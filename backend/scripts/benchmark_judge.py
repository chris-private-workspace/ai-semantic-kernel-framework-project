"""
File: backend/scripts/benchmark_judge.py
Purpose: Permanent, re-runnable cheap-judge accuracy benchmark (Sprint 57.111 A3).
Category: 範疇 10 (Verification Loops) — eval tooling
Scope: Phase 57 / Sprint 57.111 (A3)

Description:
    Measures how accurately the CHEAP-tier LLM judge (Sprint 57.97) verifies output
    versus the STRONG tier and versus hand-labeled ground truth — settling design note
    24's open invariant ("a cheaper judge MAY be less reliable; NOT formally measured")
    with a real number + a human go/no-go verdict (keep cheap vs move judge to strong).

    The reusable logic lives here (importable as `scripts.benchmark_judge`):
      - load_cases(path)            — parse + schema-validate the golden YAML fixture
      - run_judge(judge, cases, ...) — run a Verifier over the cases (trace-aware optional)
      - build_report(...)           — pure accuracy / agreement / trace-delta computation
      - main()                      — CLI: build the Azure profile, run both tiers, write a report
    The pytest wrapper `tests/benchmark/test_judge_accuracy.py` (@pytest.mark.benchmark,
    skipif RUN_AZURE_INTEGRATION) drives a real Azure run; `tests/unit/scripts/
    test_benchmark_judge.py` covers load_cases / build_report / run_judge CI-safe (MockChatClient).

    Run on demand:
      RUN_AZURE_INTEGRATION=1 AZURE_OPENAI_*=... python scripts/benchmark_judge.py

LLM Provider Neutrality: the core (load/run/score) operates on the Verifier ABC; only
main() builds the Azure ModelProfile (the concrete on-demand entry, like the existing
real-Azure integration test).

Created: 2026-06-13 (Sprint 57.111 A3)

Modification History (newest-first):
    - 2026-06-13: Initial creation (Sprint 57.111 A3) — cheap-judge accuracy benchmark

Related:
    - backend/tests/fixtures/verification/judge_benchmark.yaml (the golden dataset)
    - backend/src/agent_harness/verification/llm_judge.py (the judge under test)
    - 24-multi-model-profile-design.md §4 (the open invariant being settled)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from statistics import mean
from uuid import uuid4

import yaml

from agent_harness._contracts.chat import Message
from agent_harness._contracts.state import (
    DurableState,
    LoopState,
    StateVersion,
    TransientState,
)
from agent_harness.verification import LLMJudgeVerifier, Verifier

# The tracked accuracy floor (A3 defines it; design note 24 had no number). A cheap judge
# below this on the unambiguous categories (clear_* + trace_dependent) is "visibly
# mis-verifying" → the human verdict is to keep the judge on the strong tier. Borderline
# cases are reported but NOT in the floor (their ground truth is genuinely soft).
CHEAP_ACCURACY_FLOOR = 0.70

_UNAMBIGUOUS = ("clear_pass", "clear_fail", "trace_dependent")
_VALID_CATEGORIES = ("clear_pass", "clear_fail", "trace_dependent", "borderline")


@dataclass(frozen=True)
class BenchCase:
    """One labeled benchmark case."""

    id: str
    output: str
    expected_passed: bool
    category: str
    trace: list[Message] = field(default_factory=list)


@dataclass(frozen=True)
class JudgeRun:
    """The result of running one judge over the cases (aligned to the case order)."""

    verdicts: list[bool]
    input_tokens: int
    output_tokens: int


@dataclass(frozen=True)
class BenchReport:
    """Computed benchmark metrics."""

    total: int
    cheap_accuracy: float
    strong_accuracy: float
    cheap_vs_strong_agreement: float
    per_category: dict[str, dict[str, float]]
    trace_delta: float | None  # cheap WITH trace − cheap WITHOUT trace, on trace_dependent
    cheap_tokens: int
    strong_tokens: int
    floor: float
    cheap_passes_floor: bool


def load_cases(path: str | Path) -> list[BenchCase]:
    """Parse + schema-validate the golden YAML fixture into BenchCase objects."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "cases" not in data:
        raise ValueError("benchmark fixture must be a mapping with a top-level 'cases' list")
    raw_cases = data["cases"]
    if not isinstance(raw_cases, list) or not raw_cases:
        raise ValueError("'cases' must be a non-empty list")

    cases: list[BenchCase] = []
    seen_ids: set[str] = set()
    for i, rc in enumerate(raw_cases):
        if not isinstance(rc, dict):
            raise ValueError(f"case #{i} is not a mapping")
        for key in ("id", "output", "expected_passed", "category"):
            if key not in rc:
                raise ValueError(f"case #{i} missing required key '{key}'")
        cid = str(rc["id"])
        if cid in seen_ids:
            raise ValueError(f"duplicate case id '{cid}'")
        seen_ids.add(cid)
        category = str(rc["category"])
        if category not in _VALID_CATEGORIES:
            raise ValueError(f"case '{cid}' has invalid category '{category}'")
        if not isinstance(rc["expected_passed"], bool):
            raise ValueError(f"case '{cid}' expected_passed must be a bool")
        trace: list[Message] = []
        for j, tm in enumerate(rc.get("trace", []) or []):
            if not isinstance(tm, dict) or "role" not in tm or "content" not in tm:
                raise ValueError(f"case '{cid}' trace entry #{j} needs 'role' + 'content'")
            role = str(tm["role"])
            content = str(tm["content"])
            trace.append(Message(role=role, content=content))  # type: ignore[arg-type]
        cases.append(
            BenchCase(
                id=cid,
                output=str(rc["output"]),
                expected_passed=bool(rc["expected_passed"]),
                category=category,
                trace=trace,
            )
        )
    return cases


def _state_from_trace(trace: list[Message]) -> LoopState | None:
    """Wrap a case's trace as a minimal LoopState the trace-aware judge reads (None if empty)."""
    if not trace:
        return None
    sid = uuid4()
    return LoopState(
        transient=TransientState(messages=list(trace)),
        durable=DurableState(session_id=sid, tenant_id=sid),
        version=StateVersion(
            version=0,
            parent_version=None,
            created_at=datetime.now(),
            created_by_category="benchmark",
        ),
    )


async def run_judge(judge: Verifier, cases: list[BenchCase], *, with_trace: bool) -> JudgeRun:
    """Run `judge` over every case; return its pass/fail verdicts + token totals.

    with_trace=True passes each case's trace as a LoopState (so trace_dependent cases
    exercise the A3 trace-aware path); with_trace=False passes state=None (the pre-A3
    final-string-only behavior — used for the trace-delta comparison).
    """
    verdicts: list[bool] = []
    in_tok = 0
    out_tok = 0
    for case in cases:
        state = _state_from_trace(case.trace) if with_trace else None
        result = await judge.verify(output=case.output, state=state)
        verdicts.append(result.passed)
        in_tok += result.input_tokens
        out_tok += result.output_tokens
    return JudgeRun(verdicts=verdicts, input_tokens=in_tok, output_tokens=out_tok)


def _accuracy(cases: list[BenchCase], verdicts: list[bool]) -> float:
    if not cases:
        return 0.0
    return mean(1.0 if v == c.expected_passed else 0.0 for c, v in zip(cases, verdicts))


def _agreement(a: list[bool], b: list[bool]) -> float:
    if not a:
        return 0.0
    return mean(1.0 if x == y else 0.0 for x, y in zip(a, b))


def build_report(
    cases: list[BenchCase],
    cheap: JudgeRun,
    strong: JudgeRun,
    *,
    cheap_no_trace: JudgeRun | None = None,
    floor: float = CHEAP_ACCURACY_FLOOR,
) -> BenchReport:
    """Pure metric computation: accuracy vs label, cheap-vs-strong agreement, trace delta."""
    per_category: dict[str, dict[str, float]] = {}
    for cat in _VALID_CATEGORIES:
        idx = [i for i, c in enumerate(cases) if c.category == cat]
        if not idx:
            continue
        sub = [cases[i] for i in idx]
        per_category[cat] = {
            "n": float(len(idx)),
            "cheap_accuracy": _accuracy(sub, [cheap.verdicts[i] for i in idx]),
            "strong_accuracy": _accuracy(sub, [strong.verdicts[i] for i in idx]),
        }

    # The floor is judged on the unambiguous categories only (borderline excluded).
    unamb_idx = [i for i, c in enumerate(cases) if c.category in _UNAMBIGUOUS]
    unamb_cases = [cases[i] for i in unamb_idx]
    cheap_acc_unamb = _accuracy(unamb_cases, [cheap.verdicts[i] for i in unamb_idx])

    trace_delta: float | None = None
    if cheap_no_trace is not None:
        td_idx = [i for i, c in enumerate(cases) if c.category == "trace_dependent"]
        if td_idx:
            td_cases = [cases[i] for i in td_idx]
            with_t = _accuracy(td_cases, [cheap.verdicts[i] for i in td_idx])
            without_t = _accuracy(td_cases, [cheap_no_trace.verdicts[i] for i in td_idx])
            trace_delta = with_t - without_t

    return BenchReport(
        total=len(cases),
        cheap_accuracy=_accuracy(cases, cheap.verdicts),
        strong_accuracy=_accuracy(cases, strong.verdicts),
        cheap_vs_strong_agreement=_agreement(cheap.verdicts, strong.verdicts),
        per_category=per_category,
        trace_delta=trace_delta,
        cheap_tokens=cheap.input_tokens + cheap.output_tokens,
        strong_tokens=strong.input_tokens + strong.output_tokens,
        floor=floor,
        cheap_passes_floor=cheap_acc_unamb >= floor,
    )


def report_to_markdown(report: BenchReport, *, stamp: str) -> str:
    """Render a human-readable benchmark report (for the design-note verdict)."""
    lines = [
        f"# Cheap-Judge Accuracy Benchmark — {stamp}",
        "",
        f"- cases: **{report.total}**",
        f"- cheap accuracy (all): **{report.cheap_accuracy:.2%}**",
        f"- strong accuracy (all): **{report.strong_accuracy:.2%}**",
        f"- cheap-vs-strong agreement: **{report.cheap_vs_strong_agreement:.2%}**",
        f"- trace delta (cheap, trace_dependent: with−without): "
        f"**{'n/a' if report.trace_delta is None else format(report.trace_delta, '+.2%')}**",
        f"- cheap tokens: {report.cheap_tokens} · strong tokens: {report.strong_tokens}",
        f"- floor (unambiguous categories): {report.floor:.0%} → "
        f"**{'PASS' if report.cheap_passes_floor else 'FAIL'}**",
        "",
        "## Per category",
        "",
        "| category | n | cheap acc | strong acc |",
        "|----------|---|-----------|------------|",
    ]
    for cat, m in report.per_category.items():
        lines.append(
            f"| {cat} | {int(m['n'])} | {m['cheap_accuracy']:.2%} | {m['strong_accuracy']:.2%} |"
        )
    return "\n".join(lines) + "\n"


async def _amain(fixture: Path, out_dir: Path, judge_template: str) -> int:
    # Imported lazily so a CI-safe import of this module's pure helpers does not require
    # the Azure adapter env.
    from adapters.azure_openai.profile import build_azure_model_profile

    cases = load_cases(fixture)
    profile = build_azure_model_profile()
    cheap_judge = LLMJudgeVerifier(
        chat_client=profile.cheap, judge_template=judge_template, temperature=0.0
    )
    strong_judge = LLMJudgeVerifier(
        chat_client=profile.action, judge_template=judge_template, temperature=0.0
    )

    cheap = await run_judge(cheap_judge, cases, with_trace=True)
    strong = await run_judge(strong_judge, cases, with_trace=True)
    cheap_no_trace = await run_judge(cheap_judge, cases, with_trace=False)
    report = build_report(cases, cheap, strong, cheap_no_trace=cheap_no_trace)

    out_dir.mkdir(parents=True, exist_ok=True)
    md = report_to_markdown(report, stamp=datetime.now().isoformat(timespec="seconds"))
    (out_dir / "judge_benchmark_report.md").write_text(md, encoding="utf-8")
    (out_dir / "judge_benchmark_report.json").write_text(
        json.dumps(
            {
                "total": report.total,
                "cheap_accuracy": report.cheap_accuracy,
                "strong_accuracy": report.strong_accuracy,
                "cheap_vs_strong_agreement": report.cheap_vs_strong_agreement,
                "trace_delta": report.trace_delta,
                "per_category": report.per_category,
                "cheap_tokens": report.cheap_tokens,
                "strong_tokens": report.strong_tokens,
                "floor": report.floor,
                "cheap_passes_floor": report.cheap_passes_floor,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(md)
    return 0 if report.cheap_passes_floor else 1


def main() -> int:
    # The report markdown carries non-ASCII typography (− · → —); a Windows cp950 console
    # can't encode it. Force the stdout text layer to UTF-8 so the print never crashes.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except Exception:  # noqa: BLE001 — best-effort; redirected/odd streams keep their codec
        pass
    parser = argparse.ArgumentParser(description="Cheap-judge accuracy benchmark (A3).")
    parser.add_argument(
        "--fixture",
        default=str(
            Path(__file__).resolve().parent.parent
            / "tests"
            / "fixtures"
            / "verification"
            / "judge_benchmark.yaml"
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
