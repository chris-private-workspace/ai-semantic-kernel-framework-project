"""
File: backend/scripts/benchmark_combined_formation_quality.py
Purpose: A/B benchmark of combined vs separate post-send memory formation — measures whether asking
         one combined LLM call for BOTH the user facts and the session summary degrades either
         half's quality vs the two focused calls (57.152 carryover).
Category: 範疇 3 (Memory) — eval tooling
Scope: Phase 57 / Sprint 57.154 (AD-Memory-Combined-Formation-AB-Quality)

Description:
    Settles the 57.152 combined-formation trade with real numbers + a human go/no-go verdict: does
    MemoryFormationWorker's default combined single call (one chat() returning facts[] + summary)
    LOWER the quality of the extracted user facts OR the session summary vs the proven two-call
    path (57.149 MemoryExtractor + 57.151 SessionSummarizer, each its own focused call)?

    It runs the REAL production worker over a golden corpus under two arms — the ONLY variable is
    the ctor `combined` flag:
      - combined: MemoryFormationWorker(..., combined=True)  → ONE chat() (the shipped default)
      - separate: MemoryFormationWorker(..., combined=False) → TWO focused chat() (the env fallback)
    Each arm drives form() end-to-end (build prompt → chat → parse → dispatch); only the terminal DB
    write is captured (not persisted) via _CapturingUserLayer / _CapturingSummaryStore — so the
    harness is byte-faithful to production (AP-10: no divergent prompt re-implementation).

    Hybrid oracle (user-picked, AskUserQuestion 2026-07-01):
      - facts  — DETERMINISTIC keyword-group coverage + spurious count (score_facts); no LLM.
      - summary — an LLM-judge faithfulness/coverage score in [0,1] (score_summary) via the neutral
        ChatClient ABC (a self-contained rubric — NOT a production verification/templates/ file, to
        avoid an orphan production-selectable template).
    Metrics compared (combined − separate):
      - facts_coverage       — want NOT materially lower (a focused extractor must not out-recall)
      - summary_score        — want NOT materially lower (attention-split must not shallow it)
      - facts_spurious_mean  — want NOT materially higher (the combined prompt must not hallucinate)
    Two-sided verdict: KEEP combined default ON iff combined does NOT materially regress on EITHER
    quality axis AND does not inflate spurious facts — the ~2× efficiency win was already
    established Sprint 57.152, so the A/B only needs to prove no material quality loss.

    The reusable logic lives here (importable as `scripts.benchmark_combined_formation_quality`):
      - load_cases(path)                 — parse + schema-validate the golden YAML
      - score_facts(emitted, expected)   — deterministic keyword-coverage + spurious count
      - score_summary(judge, ...)        — LLM-judge summary faithfulness (real LLM)
      - run_arm(arm, cases, ...)       — drive the REAL worker per case, capture + score (real LLM)
      - build_report(combined, separate) — pure A/B metric computation + verdict
      - main()                           — CLI: build Azure profile, run both arms
    CI-safe unit coverage lives in tests/unit/scripts/test_benchmark_combined_formation_quality.py
    (a spy ChatClient + capturing doubles + the pure helpers, NO Azure). Real run on demand:
      RUN_AZURE_INTEGRATION=1 python scripts/benchmark_combined_formation_quality.py

LLM Provider Neutrality: the core operates on the ChatClient ABC + the neutral Message/ChatRequest
dataclasses; only main() builds the concrete Azure ModelProfile (mirrors
benchmark_memory_grounded_judge.py — the on-demand entry, like the real-Azure test).

Created: 2026-07-01 (Sprint 57.154)

Modification History (newest-first):
    - 2026-07-01: Initial creation (Sprint 57.154) — combined-vs-separate formation quality A/B

Related:
    - backend/tests/fixtures/memory/memory_formation_quality_cases.yaml (the golden dataset)
    - backend/src/agent_harness/memory/formation.py (MemoryFormationWorker.form — the arms)
    - backend/src/agent_harness/memory/extraction.py / session_summarizer.py (the two workers)
    - backend/scripts/benchmark_memory_grounded_judge.py (the mirrored scaffold)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

import yaml

from adapters._base.chat_client import ChatClient
from agent_harness._contracts import ChatRequest, Message
from agent_harness.memory.extraction import MemoryExtractor
from agent_harness.memory.formation import MemoryFormationWorker
from agent_harness.memory.layers.user_layer import UserLayer
from agent_harness.memory.session_summarizer import SessionSummarizer
from agent_harness.memory.session_summary_store import DBSessionSummaryStore

# A metric must move by at least this much (5 percentage points) to be material; below it the
# difference is noise. Mirrors benchmark_memory_grounded_judge.py's MATERIALITY_DELTA.
MATERIALITY_DELTA = 0.05
# Spurious-fact inflation tolerance (mean extra facts per case). One stray fact on average is
# within noise for a keyword-grouped oracle; more than that flags the combined prompt hallucinating.
SPURIOUS_DELTA = 1.0

_ARM_COMBINED = "combined"
_ARM_SEPARATE = "separate"

_FLOAT_RE = re.compile(r"\d*\.\d+|\d+")


@dataclass(frozen=True)
class FormationCase:
    """One formation case: a conversation + the facts/summary a good formation should produce."""

    id: str
    conversation: list[dict[str, str]]  # [{role, content}] fed to both arms
    expected_facts: list[list[str]]  # keyword groups; a fact "covers" a group if it contains all
    expected_summary_points: list[str]  # topics/decisions the summary should capture
    expects_facts: bool  # False = a 0-durable-fact case (tests spurious-fact rate)


@dataclass(frozen=True)
class ArmScore:
    """Aggregated quality scores for one arm (combined | separate) over the cases."""

    arm: str
    n_cases: int
    facts_coverage: float  # mean expected-group coverage
    facts_spurious_mean: float  # mean emitted-facts-matching-no-expected-group per case
    summary_score: float  # mean LLM-judge summary faithfulness/coverage


@dataclass(frozen=True)
class FormationReport:
    """Computed A/B metrics + the human go/no-go verdict."""

    total: int
    combined: ArmScore
    separate: ArmScore
    facts_coverage_delta: float  # combined − separate; NEGATIVE = combined recalls fewer facts
    summary_score_delta: float  # combined − separate; NEGATIVE = combined summary is shallower
    spurious_delta: float  # combined − separate; POSITIVE = combined hallucinates more facts
    combined_recommended: bool


def load_cases(path: str | Path) -> list[FormationCase]:
    """Parse + schema-validate the golden YAML fixture into FormationCase objects."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "cases" not in data:
        raise ValueError("formation fixture must be a mapping with a top-level 'cases' list")
    raw_cases = data["cases"]
    if not isinstance(raw_cases, list) or not raw_cases:
        raise ValueError("'cases' must be a non-empty list")

    cases: list[FormationCase] = []
    seen_ids: set[str] = set()
    for i, rc in enumerate(raw_cases):
        if not isinstance(rc, dict):
            raise ValueError(f"case #{i} is not a mapping")
        for key in ("id", "conversation", "expected_facts", "expected_summary_points"):
            if key not in rc:
                raise ValueError(f"case #{i} missing required key '{key}'")
        cid = str(rc["id"])
        if cid in seen_ids:
            raise ValueError(f"duplicate case id '{cid}'")
        seen_ids.add(cid)
        cases.append(
            FormationCase(
                id=cid,
                conversation=_coerce_conversation(cid, rc["conversation"]),
                expected_facts=_coerce_keyword_groups(cid, rc["expected_facts"]),
                expected_summary_points=[
                    str(p) for p in _as_list(cid, rc["expected_summary_points"])
                ],
                expects_facts=bool(rc.get("expects_facts", True)),
            )
        )
    return cases


def _as_list(cid: str, value: object) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"case '{cid}': expected a list, got {type(value).__name__}")
    return value


def _coerce_conversation(cid: str, value: object) -> list[dict[str, str]]:
    turns: list[dict[str, str]] = []
    for turn in _as_list(cid, value):
        if not isinstance(turn, dict) or "role" not in turn or "content" not in turn:
            raise ValueError(f"case '{cid}': each conversation turn needs 'role' + 'content'")
        turns.append({"role": str(turn["role"]), "content": str(turn["content"])})
    if not turns:
        raise ValueError(f"case '{cid}': conversation must be non-empty")
    return turns


def _coerce_keyword_groups(cid: str, value: object) -> list[list[str]]:
    groups: list[list[str]] = []
    for group in _as_list(cid, value):
        if not isinstance(group, list):
            raise ValueError(f"case '{cid}': each expected_facts item must be a keyword list")
        groups.append([str(k) for k in group])
    return groups


# === Hybrid oracle: facts (deterministic) + summary (LLM judge) ===
# Why: "quality degradation" is subjective; the deterministic half pins facts recall/spurious
# objectively (no LLM cost, CI-safe), the judge half scores summary faithfulness where a rule
# can't (a summary can be word-different yet faithful). Mirrors the 57.141 hybrid oracle.


def _normalize(text: str) -> str:
    """Lowercase + collapse whitespace for keyword-contains matching."""
    return re.sub(r"\s+", " ", text.lower()).strip()


def score_facts(emitted_contents: list[str], expected_groups: list[list[str]]) -> tuple[float, int]:
    """Deterministic facts oracle → (coverage, spurious_count).

    coverage = fraction of expected keyword-groups for which SOME emitted fact (normalized)
    contains ALL the group's keywords. spurious_count = emitted facts matching NO expected group
    (chiefly meaningful on expects_facts=False cases — the combined prompt must not hallucinate).
    An empty expected set → coverage 1.0 (vacuous) and every emitted fact is spurious.
    """
    norm_emitted = [_normalize(c) for c in emitted_contents]
    norm_groups = [[_normalize(k) for k in group] for group in expected_groups]

    if norm_groups:
        matched = sum(
            1
            for group in norm_groups
            if any(all(k in fact for k in group) for fact in norm_emitted)
        )
        coverage = matched / len(norm_groups)
    else:
        coverage = 1.0

    spurious = sum(
        1
        for fact in norm_emitted
        if not any(all(k in fact for k in group) for group in norm_groups)
    )
    return (coverage, spurious)


_SUMMARY_JUDGE_PROMPT = """You are grading a summary of a conversation. Read the conversation, \
the summary, and the points the summary is expected to cover. Score the summary on a 0.0-1.0 scale \
combining:
  - FAITHFULNESS: does the summary avoid inventing facts not in the conversation?
  - COVERAGE: does it capture the topic, decisions, open issues, and the expected points?
1.0 = fully faithful and covers everything; 0.0 = unfaithful or misses the substance.
Return ONLY a strict JSON object: {{"score": <float 0.0-1.0>}}.

Conversation:
{conversation}

Summary to grade:
{summary}

Expected points the summary should cover:
{expected_points}
"""


async def score_summary(
    judge: ChatClient,
    *,
    conversation: str,
    summary_obj: dict[str, Any] | None,
    expected_points: list[str],
) -> float:
    """LLM-judge summary faithfulness/coverage in [0,1]. No stored summary → 0.0 (worst)."""
    if summary_obj is None:
        return 0.0
    prompt = _SUMMARY_JUDGE_PROMPT.format(
        conversation=conversation,
        summary=_render_summary(summary_obj),
        expected_points="\n".join(f"- {p}" for p in expected_points) or "(none specified)",
    )
    request = ChatRequest(messages=[Message(role="user", content=prompt)], temperature=0.0)
    response = await judge.chat(request)
    return _parse_score(_content_text(response.content))


def _parse_score(raw: str) -> float:
    """Tolerant float parse of a `{"score": x}` judge reply. 0.0 on unparseable."""
    text = raw.strip()
    if not text:
        return 0.0
    for candidate in (text, _first_json_object(text)):
        if not candidate:
            continue
        try:
            obj = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and "score" in obj:
            try:
                return _clamp01(float(obj["score"]))
            except (TypeError, ValueError):
                return 0.0
    match = _FLOAT_RE.search(text)
    if match:
        try:
            return _clamp01(float(match.group()))
        except ValueError:
            return 0.0
    return 0.0


def _first_json_object(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return ""
    return text[start : end + 1]


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _render_summary(summary_obj: dict[str, Any]) -> str:
    parts = [str(summary_obj.get("summary", ""))]
    decisions = summary_obj.get("key_decisions") or []
    issues = summary_obj.get("unresolved_issues") or []
    if decisions:
        parts.append("Decisions: " + "; ".join(str(d) for d in decisions))
    if issues:
        parts.append("Open issues: " + "; ".join(str(u) for u in issues))
    return "\n".join(parts)


def _render_conversation(messages: list[Message]) -> str:
    return "\n".join(f"[{m.role}] {_content_text(m.content)}" for m in messages)


def _content_text(content: object) -> str:
    """Plain text from a Message.content that may be str or list[ContentBlock]."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            text = getattr(block, "text", None)
            if isinstance(text, str):
                parts.append(text)
        return "\n".join(parts)
    return str(content)


# === Capturing sinks: drive the REAL worker, capture (not persist) the terminal write ===
# Why: form() writes facts via UserLayer.write + the summary via
# DBSessionSummaryStore.upsert_summary. Swapping ONLY those terminal sinks for in-memory recorders
# lets the harness run the entire real production formation path (build prompt → chat → parse →
# dispatch) and score whatever the worker produced — byte-faithful to production (AP-10), zero src
# change. The signatures mirror the real seams exactly (Day-0 D-capture-signatures).
class _CapturingUserLayer:
    """Records the facts form() would write, instead of hitting memory_user."""

    def __init__(self) -> None:
        self.written: list[dict[str, Any]] = []

    async def write(
        self,
        *,
        content: str,
        tenant_id: Any = None,
        user_id: Any = None,
        time_scale: str = "long_term",
        confidence: float = 0.5,
        source: str | None = None,
        trace_context: Any = None,
    ) -> Any:
        self.written.append({"content": content, "confidence": confidence})
        return uuid4()


class _CapturingSummaryStore:
    """Records the summary form() would upsert, instead of hitting memory_session_summary."""

    def __init__(self) -> None:
        self.stored: dict[str, Any] | None = None

    async def upsert_summary(
        self,
        *,
        session_id: Any,
        summary: str,
        key_decisions: list[str],
        unresolved_issues: list[str],
    ) -> Any:
        self.stored = {
            "summary": summary,
            "key_decisions": key_decisions,
            "unresolved_issues": unresolved_issues,
        }
        return uuid4()


def _build_worker(
    chat_client: ChatClient, *, combined: bool
) -> tuple[MemoryFormationWorker, _CapturingUserLayer, _CapturingSummaryStore]:
    """Construct the REAL worker wired to fresh capturing sinks for one case."""
    cap_user = _CapturingUserLayer()
    cap_store = _CapturingSummaryStore()
    worker = MemoryFormationWorker(
        chat_client,
        extractor=MemoryExtractor(chat_client, cast(UserLayer, cap_user)),
        summarizer=SessionSummarizer(chat_client, cast(DBSessionSummaryStore, cap_store)),
        combined=combined,
    )
    return worker, cap_user, cap_store


async def run_arm(
    arm: str, cases: list[FormationCase], *, chat_client: ChatClient, judge: ChatClient
) -> ArmScore:
    """Drive the REAL worker per case under one arm (real LLM), capture + score.

    arm ∈ {'combined', 'separate'} → the ctor `combined` flag. chat_client drives formation;
    judge scores the summary half (both are profile.cheap in the real run, spies in CI).
    """
    combined = arm == _ARM_COMBINED
    coverages: list[float] = []
    spurious_counts: list[int] = []
    summary_scores: list[float] = []
    for case in cases:
        messages = [Message(role=t["role"], content=t["content"]) for t in case.conversation]
        worker, cap_user, cap_store = _build_worker(chat_client, combined=combined)
        await worker.form(
            messages=messages,
            session_id=uuid4(),
            tenant_id=uuid4(),
            user_id=uuid4(),
            known_facts=None,
        )
        emitted = [str(w["content"]) for w in cap_user.written]
        coverage, spurious = score_facts(emitted, case.expected_facts)
        coverages.append(coverage)
        spurious_counts.append(spurious)
        summary_scores.append(
            await score_summary(
                judge,
                conversation=_render_conversation(messages),
                summary_obj=cap_store.stored,
                expected_points=case.expected_summary_points,
            )
        )
    n = len(cases)
    return ArmScore(
        arm=arm,
        n_cases=n,
        facts_coverage=_mean(coverages),
        facts_spurious_mean=_mean([float(s) for s in spurious_counts]),
        summary_score=_mean(summary_scores),
    )


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def build_report(combined: ArmScore, separate: ArmScore) -> FormationReport:
    """Pure A/B metric computation + the human go/no-go verdict.

    KEEP combined default ON iff combined does NOT materially regress on EITHER quality axis
    (facts_coverage_delta ≥ −Δ AND summary_score_delta ≥ −Δ) AND does not materially inflate
    spurious facts (spurious_delta ≤ +SPURIOUS_DELTA). The ~2× efficiency win was established Sprint
    57.152; the A/B's sole job is to prove the combined prompt loses no material quality — there is
    no "improvement" axis (combined is not expected to beat two focused calls on quality, only to
    tie within the materiality band while winning on cost).
    """
    facts_coverage_delta = combined.facts_coverage - separate.facts_coverage
    summary_score_delta = combined.summary_score - separate.summary_score
    spurious_delta = combined.facts_spurious_mean - separate.facts_spurious_mean
    no_facts_regression = facts_coverage_delta >= -MATERIALITY_DELTA
    no_summary_regression = summary_score_delta >= -MATERIALITY_DELTA
    no_spurious_inflation = spurious_delta <= SPURIOUS_DELTA
    combined_recommended = no_facts_regression and no_summary_regression and no_spurious_inflation
    return FormationReport(
        total=combined.n_cases,
        combined=combined,
        separate=separate,
        facts_coverage_delta=facts_coverage_delta,
        summary_score_delta=summary_score_delta,
        spurious_delta=spurious_delta,
        combined_recommended=combined_recommended,
    )


def report_to_markdown(report: FormationReport, *, stamp: str) -> str:
    """Render a human-readable A/B report (for the design-note verdict)."""
    verdict = (
        "KEEP combined default ON"
        if report.combined_recommended
        else "FLIP to two-call default (combined=False)"
    )
    lines = [
        f"# Combined-vs-Separate Formation Quality A/B — {stamp}",
        "",
        f"- cases: **{report.total}**",
        "",
        "| metric | combined | separate | delta (comb−sep) |",
        "|--------|----------|----------|------------------|",
        f"| facts_coverage | {report.combined.facts_coverage:.2%} | "
        f"{report.separate.facts_coverage:.2%} | {report.facts_coverage_delta:+.2%} |",
        f"| summary_score | {report.combined.summary_score:.3f} | "
        f"{report.separate.summary_score:.3f} | {report.summary_score_delta:+.3f} |",
        f"| facts_spurious_mean | {report.combined.facts_spurious_mean:.2f} | "
        f"{report.separate.facts_spurious_mean:.2f} | {report.spurious_delta:+.2f} |",
        "",
        f"- materiality threshold: **{MATERIALITY_DELTA:.0%}** "
        f"(spurious tolerance {SPURIOUS_DELTA:.1f} facts/case)",
        f"- **verdict: {verdict}**",
        "",
        "> A NEGATIVE facts_coverage/summary_score delta beyond −threshold, OR a spurious_delta "
        "above the tolerance, flips the recommendation to the proven two-call path. The efficiency "
        "win (~2× fewer calls) was established Sprint 57.152 — this A/B only guards quality.",
    ]
    return "\n".join(lines) + "\n"


async def _amain(fixture: Path, out_dir: Path) -> int:
    # Imported lazily so a CI-safe import of this module's pure helpers does not require the Azure
    # adapter env (mirrors benchmark_memory_grounded_judge.py).
    from adapters.azure_openai.profile import build_azure_model_profile

    cases = load_cases(fixture)
    profile = build_azure_model_profile()
    # Both formation + the summary judge run on the cheap tier (the production formation tier).
    combined = await run_arm(_ARM_COMBINED, cases, chat_client=profile.cheap, judge=profile.cheap)
    separate = await run_arm(_ARM_SEPARATE, cases, chat_client=profile.cheap, judge=profile.cheap)
    report = build_report(combined, separate)

    out_dir.mkdir(parents=True, exist_ok=True)
    md = report_to_markdown(report, stamp=datetime.now().isoformat(timespec="seconds"))
    (out_dir / "combined_formation_quality_report.md").write_text(md, encoding="utf-8")
    (out_dir / "combined_formation_quality_report.json").write_text(
        json.dumps(
            {
                "total": report.total,
                "combined": report.combined.__dict__,
                "separate": report.separate.__dict__,
                "facts_coverage_delta": report.facts_coverage_delta,
                "summary_score_delta": report.summary_score_delta,
                "spurious_delta": report.spurious_delta,
                "combined_recommended": report.combined_recommended,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(md)
    return 0


def main() -> int:
    # The report markdown carries non-ASCII typography (− · ≥); a Windows cp950 console can't encode
    # it. Force the stdout text layer to UTF-8 so the print never crashes.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except Exception:  # noqa: BLE001 — best-effort; redirected/odd streams keep their codec
        pass
    parser = argparse.ArgumentParser(
        description="Combined-vs-separate memory-formation quality A/B (Sprint 57.154)."
    )
    parser.add_argument(
        "--fixture",
        default=str(
            Path(__file__).resolve().parent.parent
            / "tests"
            / "fixtures"
            / "memory"
            / "memory_formation_quality_cases.yaml"
        ),
    )
    parser.add_argument(
        "--out", default=str(Path(__file__).resolve().parent.parent / "benchmark_reports")
    )
    args = parser.parse_args()
    return asyncio.run(_amain(Path(args.fixture), Path(args.out)))


if __name__ == "__main__":
    sys.exit(main())
