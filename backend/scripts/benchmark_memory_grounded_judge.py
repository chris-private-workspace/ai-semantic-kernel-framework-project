"""
File: backend/scripts/benchmark_memory_grounded_judge.py
Purpose: A/B benchmark of the memory-aware in-loop judge (memory_aware vs bare) — measures the
         grounded-recall false-positive-reject rate + the genuine-fabrication catch rate (57.153).
Category: 範疇 10 (Verification Loops) — eval tooling
Scope: Phase 57 / Sprint 57.153 (AD-Verification-Judge-Memory-Inject-Blind)

Description:
    Settles the 57.153 fix with real numbers + a human go/no-go verdict: does showing the in-loop
    Cat 10 judge the memory injected into the turn's prompt (the new {memory} grounding block)
    LOWER the rate at which a memory-grounded recall is false-positive-rejected as fabrication,
    WITHOUT degrading the rate at which a genuine fabrication is correctly caught?

    It runs the REAL production judge (LLMJudgeVerifier + output_quality template) over a golden
    corpus under two arms — the ONLY variable is whether the verify state carries injected_memory:
      - memory_aware: state.transient.injected_memory = build_memory_block(case.injected_memory)
      - bare:         state.transient.injected_memory = None  (pre-57.153 memory-blind judge)
    For each case the judge produces a pass/fail verdict; the corpus labels each case as either a
    `grounded_recall` (consistent with the injected memory → the CORRECT verdict is PASS; a REJECT
    is a false positive) or a `genuine_fabrication` (asserts a fact NOT in the memory or trace →
    the CORRECT verdict is REJECT). Metrics:
      - grounded_recall_false_reject_rate — grounded cases the judge wrongly REJECTED (want DOWN
        with memory_aware)
      - fabrication_catch_rate            — fabrication cases the judge correctly REJECTED (want
        NOT degraded by memory_aware — the grounding must not make the judge too lenient)
    A materially lower false-reject rate AND a non-degraded catch rate → the human verdict is to
    KEEP memory-grounding default ON (the 57.153 ship default); else flip to opt-in (default OFF).

    The reusable logic lives here (importable as `scripts.benchmark_memory_grounded_judge`):
      - load_cases(path)              — parse + schema-validate the golden YAML
      - build_judge_state(case, grounded) — the two verify-state constructions
      - run_arm(arm, cases, judge)    — judge every case under one arm (real LLM)
      - build_report(bare, memory)    — pure A/B metric computation + verdict
      - main()                        — CLI: build Azure profile, run both arms
    CI-safe unit coverage lives in tests/unit/scripts/test_benchmark_memory_grounded_judge.py
    (a spy judge + the pure helpers, NO Azure). Real run on demand:
      RUN_AZURE_INTEGRATION=1 AZURE_OPENAI_*=... python scripts/benchmark_memory_grounded_judge.py

LLM Provider Neutrality: the core (load / build / run / score) operates on the Verifier ABC +
the neutral state/Message dataclasses; only main() builds the concrete Azure ModelProfile
(mirrors benchmark_correction_hygiene.py — the on-demand entry, like the real-Azure test).

Created: 2026-07-01 (Sprint 57.153)

Modification History (newest-first):
    - 2026-07-01: Initial creation (Sprint 57.153) — memory_aware-vs-bare grounded-recall A/B

Related:
    - backend/tests/fixtures/verification/memory_grounded_judge_cases.yaml (the golden dataset)
    - backend/src/agent_harness/verification/llm_judge.py ({memory} substitution)
    - backend/src/agent_harness/verification/_trace.py (build_memory_block)
    - backend/scripts/benchmark_correction_hygiene.py (the mirrored scaffold)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import yaml

from agent_harness._contracts.chat import Message
from agent_harness._contracts.state import DurableState, LoopState, StateVersion, TransientState
from agent_harness.verification import Verifier, build_memory_block

# A materially lower false-reject rate (or a materially degraded catch rate) must move the metric
# by at least this much (5 percentage points) to drive the verdict; below it the difference is
# noise. Mirrors benchmark_correction_hygiene.py's SELF_CONDITIONING_DELTA.
MATERIALITY_DELTA = 0.05

_GROUNDED = "grounded_recall"
_FABRICATION = "genuine_fabrication"
_VALID_EXPECTED = (_GROUNDED, _FABRICATION)


@dataclass(frozen=True)
class GroundingCase:
    """One judge case: an injected-memory set + a user question + a recall to verify + its label."""

    id: str
    injected_memory: list[str]  # the facts injected into the turn (each a memory summary line)
    user_question: str  # the conversation trace (what the user asked)
    candidate_answer: str  # the recall the judge verifies
    expected: str  # "grounded_recall" (correct verdict = PASS) | "genuine_fabrication" (= REJECT)


@dataclass(frozen=True)
class ArmRun:
    """Aggregated judge verdicts for one arm (memory_aware | bare) over the cases."""

    arm: str
    n_grounded: int
    grounded_false_rejects: int
    grounded_recall_false_reject_rate: float
    n_fabrication: int
    fabrication_catches: int
    fabrication_catch_rate: float


@dataclass(frozen=True)
class GroundingReport:
    """Computed A/B metrics + the human go/no-go verdict."""

    total: int
    bare: ArmRun
    memory_aware: ArmRun
    false_reject_delta: float  # memory − bare; NEGATIVE = memory reduces false rejects (the win)
    catch_delta: float  # memory − bare; NEGATIVE = memory degrades fabrication catch (the risk)
    memory_grounding_recommended: bool


def load_cases(path: str | Path) -> list[GroundingCase]:
    """Parse + schema-validate the golden YAML fixture into GroundingCase objects."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "cases" not in data:
        raise ValueError("grounding fixture must be a mapping with a top-level 'cases' list")
    raw_cases = data["cases"]
    if not isinstance(raw_cases, list) or not raw_cases:
        raise ValueError("'cases' must be a non-empty list")

    cases: list[GroundingCase] = []
    seen_ids: set[str] = set()
    for i, rc in enumerate(raw_cases):
        if not isinstance(rc, dict):
            raise ValueError(f"case #{i} is not a mapping")
        for key in ("id", "injected_memory", "user_question", "candidate_answer", "expected"):
            if key not in rc:
                raise ValueError(f"case #{i} missing required key '{key}'")
        cid = str(rc["id"])
        if cid in seen_ids:
            raise ValueError(f"duplicate case id '{cid}'")
        seen_ids.add(cid)
        expected = str(rc["expected"])
        if expected not in _VALID_EXPECTED:
            raise ValueError(
                f"case '{cid}' expected must be one of {_VALID_EXPECTED}, got {expected}"
            )
        mem = rc["injected_memory"]
        if not isinstance(mem, list):
            raise ValueError(f"case '{cid}' injected_memory must be a list")
        cases.append(
            GroundingCase(
                id=cid,
                injected_memory=[str(m) for m in mem],
                user_question=str(rc["user_question"]),
                candidate_answer=str(rc["candidate_answer"]),
                expected=expected,
            )
        )
    return cases


def build_judge_state(case: GroundingCase, *, grounded: bool) -> LoopState:
    """Construct the verify state for one arm.

    Both arms carry the user question as the {trace}; the memory_aware arm additionally renders the
    injected memory into transient.injected_memory (→ the judge's {memory} block). The bare arm
    leaves it None (the pre-57.153 memory-blind judge). This isolates the grounding as the only
    variable, exactly as the loop's _cat10_verify_gate threads it (flag ON vs OFF).
    """
    injected = None
    if grounded:
        accesses = [{"scope": "user", "summary": fact} for fact in case.injected_memory]
        injected = build_memory_block(accesses) or None
    sid = uuid4()
    return LoopState(
        transient=TransientState(
            messages=[Message(role="user", content=case.user_question)],
            injected_memory=injected,
        ),
        durable=DurableState(session_id=sid, tenant_id=sid),
        version=StateVersion(
            version=0,
            parent_version=None,
            created_at=datetime.now(),
            created_by_category="benchmark",
        ),
    )


async def run_arm(arm: str, cases: list[GroundingCase], *, judge: Verifier) -> ArmRun:
    """Judge every case under one arm (real LLM calls). arm ∈ {'memory_aware', 'bare'}."""
    grounded_arm = arm == "memory_aware"
    n_grounded = n_fabrication = 0
    grounded_false_rejects = fabrication_catches = 0
    for case in cases:
        state = build_judge_state(case, grounded=grounded_arm)
        verdict = await judge.verify(output=case.candidate_answer, state=state)
        if case.expected == _GROUNDED:
            n_grounded += 1
            if not verdict.passed:  # a grounded recall rejected = a false positive
                grounded_false_rejects += 1
        else:  # genuine_fabrication
            n_fabrication += 1
            if not verdict.passed:  # a fabrication rejected = a correct catch
                fabrication_catches += 1
    return ArmRun(
        arm=arm,
        n_grounded=n_grounded,
        grounded_false_rejects=grounded_false_rejects,
        grounded_recall_false_reject_rate=(
            grounded_false_rejects / n_grounded if n_grounded else 0.0
        ),
        n_fabrication=n_fabrication,
        fabrication_catches=fabrication_catches,
        fabrication_catch_rate=(fabrication_catches / n_fabrication if n_fabrication else 0.0),
    )


def build_report(bare: ArmRun, memory_aware: ArmRun) -> GroundingReport:
    """Pure A/B metric computation + the human go/no-go verdict."""
    false_reject_delta = (
        memory_aware.grounded_recall_false_reject_rate - bare.grounded_recall_false_reject_rate
    )
    catch_delta = memory_aware.fabrication_catch_rate - bare.fabrication_catch_rate
    # KEEP memory-grounding default ON iff it MATERIALLY improves on AT LEAST ONE axis — either it
    # reduces grounded-recall false rejects (false_reject_delta ≤ −Δ) OR it improves contradiction
    # catch (catch_delta ≥ +Δ) — AND it REGRESSES on NEITHER axis (false_reject_delta ≤ +Δ keeps it
    # from getting MORE trigger-happy; catch_delta ≥ −Δ keeps it from getting too lenient, the
    # design's primary guard). Two-sided OR mirrors benchmark_correction_hygiene's verdict shape:
    # a memory-blind output_quality judge is already lenient enough to PASS grounded recalls (so
    # the false-reject axis may not move on an isolated corpus), but it is BLIND to contradictions
    # of the injected memory — the catch axis is where the fix demonstrably pays off.
    improves = false_reject_delta <= -MATERIALITY_DELTA or catch_delta >= MATERIALITY_DELTA
    no_regression = false_reject_delta <= MATERIALITY_DELTA and catch_delta >= -MATERIALITY_DELTA
    memory_grounding_recommended = improves and no_regression
    return GroundingReport(
        total=bare.n_grounded + bare.n_fabrication,
        bare=bare,
        memory_aware=memory_aware,
        false_reject_delta=false_reject_delta,
        catch_delta=catch_delta,
        memory_grounding_recommended=memory_grounding_recommended,
    )


def report_to_markdown(report: GroundingReport, *, stamp: str) -> str:
    """Render a human-readable A/B report (for the design-note verdict)."""
    verdict = (
        "KEEP memory-grounding default ON"
        if report.memory_grounding_recommended
        else "FLIP to opt-in (default OFF)"
    )
    lines = [
        f"# Memory-Grounded Judge A/B — {stamp}",
        "",
        f"- cases: **{report.total}** "
        f"(grounded {report.bare.n_grounded} / fabrication {report.bare.n_fabrication})",
        "",
        "| metric | bare | memory_aware | delta (mem−bare) |",
        "|--------|------|--------------|------------------|",
        f"| grounded_recall_false_reject_rate | "
        f"{report.bare.grounded_recall_false_reject_rate:.2%} | "
        f"{report.memory_aware.grounded_recall_false_reject_rate:.2%} | "
        f"{report.false_reject_delta:+.2%} |",
        f"| fabrication_catch_rate | {report.bare.fabrication_catch_rate:.2%} | "
        f"{report.memory_aware.fabrication_catch_rate:.2%} | {report.catch_delta:+.2%} |",
        "",
        f"- materiality threshold: **{MATERIALITY_DELTA:.0%}**",
        f"- **verdict: {verdict}**",
        "",
        "> false_reject_delta NEGATIVE = memory-grounding reduces grounded-recall false rejects "
        "(the win); catch_delta must stay ≥ −threshold = memory-grounding must NOT make the judge "
        "too lenient on genuine fabrications.",
    ]
    return "\n".join(lines) + "\n"


async def _amain(fixture: Path, out_dir: Path, judge_template: str) -> int:
    # Imported lazily so a CI-safe import of this module's pure helpers does not require the Azure
    # adapter env (mirrors benchmark_correction_hygiene.py).
    from adapters.azure_openai.profile import build_azure_model_profile

    from agent_harness.verification import LLMJudgeVerifier

    cases = load_cases(fixture)
    profile = build_azure_model_profile()
    # The verdict is rendered by the cheap-tier judge (the production in-loop verifier).
    judge = LLMJudgeVerifier(
        chat_client=profile.cheap, judge_template=judge_template, temperature=0.0
    )
    bare = await run_arm("bare", cases, judge=judge)
    memory_aware = await run_arm("memory_aware", cases, judge=judge)
    report = build_report(bare, memory_aware)

    out_dir.mkdir(parents=True, exist_ok=True)
    md = report_to_markdown(report, stamp=datetime.now().isoformat(timespec="seconds"))
    (out_dir / "memory_grounded_judge_report.md").write_text(md, encoding="utf-8")
    (out_dir / "memory_grounded_judge_report.json").write_text(
        json.dumps(
            {
                "total": report.total,
                "bare": report.bare.__dict__,
                "memory_aware": report.memory_aware.__dict__,
                "false_reject_delta": report.false_reject_delta,
                "catch_delta": report.catch_delta,
                "memory_grounding_recommended": report.memory_grounding_recommended,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(md)
    return 0


def main() -> int:
    # The report markdown carries non-ASCII typography (− · ≥); a Windows cp950 console can't
    # encode it. Force the stdout text layer to UTF-8 so the print never crashes.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except Exception:  # noqa: BLE001 — best-effort; redirected/odd streams keep their codec
        pass
    parser = argparse.ArgumentParser(description="Memory-grounded judge A/B (Sprint 57.153).")
    parser.add_argument(
        "--fixture",
        default=str(
            Path(__file__).resolve().parent.parent
            / "tests"
            / "fixtures"
            / "verification"
            / "memory_grounded_judge_cases.yaml"
        ),
    )
    parser.add_argument(
        "--out", default=str(Path(__file__).resolve().parent.parent / "benchmark_reports")
    )
    parser.add_argument("--template", default="output_quality")
    args = parser.parse_args()
    return asyncio.run(_amain(Path(args.fixture), Path(args.out), args.template))


if __name__ == "__main__":
    sys.exit(main())
