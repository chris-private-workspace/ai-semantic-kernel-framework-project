"""
File: backend/scripts/benchmark_layered_compaction.py
Purpose: Layered-compaction yield harness — per-layer token reduction to settle research #4
         (AD-Context-Layered-Compaction-ACON: tool-result clearing first, ACON 26-54% band).
Category: 範疇 4 (Context Management) — eval tooling
Scope: Phase 57 / Sprint 57.139

Description:
    Quantifies how much context the CHEAP, LLM-free tool-result clearing layer
    reclaims ON ITS OWN (the ACON 26-54% target band) and how often that defers
    the EXPENSIVE semantic summary layer. The "different axis from C2 (57.109)":
    C2 made the semantic summarizer cheap; #4 measures running the free layer
    FIRST to avoid the LLM call at all.

    Over a corpus of tool-heavy transcript SPECS (layered_compaction_cases.yaml,
    built into real Message lists), measure with a REAL TokenCounter (the chat
    flow's TiktokenCounter — NOT the compactor's internal message-count ratio
    approximation at structural.py:192-193):
      - L0 = raw token count
      - L1 = after tool-result clearing ONLY (PreClearCompactor)            [LLM-free]
      - L2 = after structural (dedup + keep-recent + masking)               [LLM-free]
      - L3 = after hybrid (structural -> semantic summarize)                [Azure-gated]
    Report:
      - tool_clear_reduction_pct = (L0-L1)/L0 — per-case + mean; in_acon_band ∈ [0.26, 0.54]
      - structural_reduction_pct = (L0-L2)/L0 — what dedup adds beyond tool-clear
      - semantic_reduction_pct   = (L0-L3)/L0 — what the EXPENSIVE LLM layer adds (Azure only)
      - semantic_deferred_rate   = fraction of cases where tool-clear alone reaches DEFER_THRESHOLD
                                   (0.333 ≈ 1.5x-over-budget) — proxy for "the cheap layer alone
                                   stays under budget, no LLM call".

    KNOWN LIMITATION surfaced by this harness (Sprint 57.139 D-masker-user-anchored): the masker
    anchors on USER message count, so single-user-turn transcripts NO-OP (tool_clear_reduction 0).
    The corpus therefore models multi-user-turn (rehydrated / injected) sessions where the layer
    is reachable; a single-turn case is included to demonstrate the NO-OP. A tool-anchored clear
    (by tool_use_id) to cover single-send is AD-Compaction-ToolAnchored-Preclear-Phase58.

    The reusable logic lives here (importable as `scripts.benchmark_layered_compaction`):
      - load_cases(path)       — parse + schema-validate the corpus specs
      - build_transcript(case) — spec -> real Message list (user/assistant tool_call/tool result)
      - measure_case(...)      — run the layers, count tokens
      - build_report(results)  — pure metric computation (band / deferral / means)
      - main()                 — CLI: L0/L1/L2 always; L3 iff RUN_AZURE_INTEGRATION
    CI-safe unit coverage lives in tests/unit/scripts/test_benchmark_layered_compaction.py
    (real TiktokenCounter + fixture, NO Azure). Real full run on demand:
      RUN_AZURE_INTEGRATION=1 AZURE_OPENAI_*=... python scripts/benchmark_layered_compaction.py

LLM Provider Neutrality: the L0/L1/L2 core is pure (TiktokenCounter is a tokenizer, no provider
SDK); the L3 semantic arm uses the ChatClient ABC via build_azure_model_profile().cheap.

Created: 2026-06-24 (Sprint 57.139)

Modification History (newest-first):
    - 2026-06-24: Initial creation (Sprint 57.139) — per-layer compaction yield + ACON-band

Related:
    - backend/tests/fixtures/context_mgmt/layered_compaction_cases.yaml (the corpus specs)
    - backend/src/agent_harness/context_mgmt/compactor/preclear.py (L1 layer under test)
    - backend/src/agent_harness/context_mgmt/compactor/{structural,hybrid,semantic}.py (L2/L3)
    - backend/scripts/benchmark_sandbox_escape.py (the mirrored scaffold)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import yaml

from agent_harness._contracts import (
    DurableState,
    LoopState,
    Message,
    StateVersion,
    ToolCall,
    TransientState,
)
from agent_harness.context_mgmt.compactor._abc import Compactor
from agent_harness.context_mgmt.compactor.preclear import PreClearCompactor
from agent_harness.context_mgmt.compactor.structural import StructuralCompactor
from agent_harness.context_mgmt.token_counter._abc import TokenCounter
from agent_harness.context_mgmt.token_counter.tiktoken_counter import TiktokenCounter

# ACON target band for the cheap tool-result clearing layer (research #4).
ACON_BAND: tuple[float, float] = (0.26, 0.54)
# Reduction the tool-clear layer must reach to defer the semantic stage when a
# conversation sits ~1.5x over the semantic trigger (1 - 1/1.5 ≈ 0.333). Documented assumption.
DEFER_THRESHOLD: float = 0.333
# A case is recommended-for-preclear if the mean lands in-band AND tool-clear alone
# defers semantic in at least half the cases.
DEFER_RATE_FLOOR: float = 0.50


@dataclass(frozen=True)
class CompactionCase:
    """A tool-heavy transcript SPEC (built into real Messages by build_transcript)."""

    id: str
    n_user_turns: int
    tool_result_chars: int
    user_text_chars: int
    assistant_text_chars: int
    keep_recent: int
    note: str


@dataclass(frozen=True)
class LayerResult:
    """Per-case token counts at each layer + derived reductions."""

    id: str
    l0_tokens: int
    l1_tool_clear: int
    l2_structural: int
    l3_semantic: int | None  # None when the Azure arm did not run
    tool_clear_reduction: float
    structural_reduction: float
    semantic_reduction: float | None
    semantic_deferred: bool  # tool-clear alone reached DEFER_THRESHOLD


@dataclass(frozen=True)
class CompactionReport:
    """Aggregate yield report (the design-note verdict source)."""

    total: int
    mean_tool_clear_reduction: float
    mean_structural_reduction: float
    mean_semantic_reduction: float | None
    in_acon_band: bool
    semantic_deferred_rate: float
    semantic_ran: bool
    preclear_recommended: bool
    results: list[LayerResult] = field(default_factory=list)


def load_cases(path: str | Path) -> list[CompactionCase]:
    """Parse + schema-validate the corpus specs into CompactionCase objects."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "cases" not in data:
        raise ValueError("corpus must be a mapping with a top-level 'cases' list")
    raw_cases = data["cases"]
    if not isinstance(raw_cases, list) or not raw_cases:
        raise ValueError("'cases' must be a non-empty list")

    cases: list[CompactionCase] = []
    seen_ids: set[str] = set()
    for i, rc in enumerate(raw_cases):
        if not isinstance(rc, dict):
            raise ValueError(f"case #{i} is not a mapping")
        for key in ("id", "n_user_turns", "tool_result_chars"):
            if key not in rc:
                raise ValueError(f"case #{i} missing required key '{key}'")
        cid = str(rc["id"])
        if cid in seen_ids:
            raise ValueError(f"duplicate case id '{cid}'")
        seen_ids.add(cid)
        cases.append(
            CompactionCase(
                id=cid,
                n_user_turns=int(rc["n_user_turns"]),
                tool_result_chars=int(rc["tool_result_chars"]),
                user_text_chars=int(rc.get("user_text_chars", 40)),
                assistant_text_chars=int(rc.get("assistant_text_chars", 0)),
                keep_recent=int(rc.get("keep_recent", 5)),
                note=str(rc.get("note", "")),
            )
        )
    return cases


def build_transcript(case: CompactionCase) -> list[Message]:
    """Spec -> real Message list: per user turn → user, assistant(tool_call), tool(result)."""
    msgs: list[Message] = []
    for i in range(case.n_user_turns):
        msgs.append(Message(role="user", content="u" + ("x" * max(case.user_text_chars - 1, 0))))
        msgs.append(
            Message(
                role="assistant",
                content="a" * case.assistant_text_chars,
                tool_calls=[ToolCall(id=f"c{i}", name="search", arguments={"i": i})],
            )
        )
        msgs.append(
            Message(
                role="tool",
                content="R" * case.tool_result_chars,
                tool_call_id=f"c{i}",
                name="search",
            )
        )
    return msgs


def _state(messages: list[Message], *, token_used: int) -> LoopState:
    return LoopState(
        transient=TransientState(
            messages=messages, current_turn=len(messages), token_usage_so_far=token_used
        ),
        durable=DurableState(session_id=uuid4(), tenant_id=uuid4()),
        version=StateVersion(
            version=1,
            parent_version=None,
            created_at=datetime(2026, 1, 1),
            created_by_category="benchmark",
        ),
    )


async def _run_and_count(
    compactor: Compactor, messages: list[Message], counter: TokenCounter
) -> int:
    """Run a compactor on `messages`; return the REAL token count of its output
    (counted by `counter`, not the compactor's internal approximation)."""
    state = _state(messages, token_used=counter.count(messages=messages))
    result = await compactor.compact_if_needed(state)
    out = (
        result.compacted_state.transient.messages
        if result.triggered and result.compacted_state is not None
        else messages
    )
    return counter.count(messages=out)


def _make_structural(keep_recent: int) -> StructuralCompactor:
    # token_budget=1, turn_threshold=0 → always triggers (force the layer to run).
    return StructuralCompactor(keep_recent_turns=keep_recent, token_budget=1, turn_threshold=0)


async def measure_case(
    case: CompactionCase,
    counter: TokenCounter,
    *,
    hybrid_factory: Callable[[int], Compactor] | None = None,
) -> LayerResult:
    """Measure L0/L1/L2 (always) + L3 (when a hybrid_factory is supplied)."""
    messages = build_transcript(case)
    l0 = counter.count(messages=messages)

    # L1: tool-result clearing ONLY (preclear_ratio tiny → always triggers).
    l1 = await _run_and_count(
        PreClearCompactor(
            token_counter=counter,
            preclear_ratio=0.001,
            keep_recent_turns=case.keep_recent,
            token_budget=1,
        ),
        messages,
        counter,
    )
    # L2: structural (dedup + keep-recent + masking).
    l2 = await _run_and_count(_make_structural(case.keep_recent), messages, counter)

    # L3: hybrid (structural -> semantic summarize) — Azure-gated.
    l3: int | None = None
    if hybrid_factory is not None:
        hybrid = hybrid_factory(case.keep_recent)
        l3 = await _run_and_count(hybrid, messages, counter)

    tool_clear_reduction = (l0 - l1) / l0 if l0 else 0.0
    structural_reduction = (l0 - l2) / l0 if l0 else 0.0
    semantic_reduction = ((l0 - l3) / l0 if l0 else 0.0) if l3 is not None else None
    return LayerResult(
        id=case.id,
        l0_tokens=l0,
        l1_tool_clear=l1,
        l2_structural=l2,
        l3_semantic=l3,
        tool_clear_reduction=tool_clear_reduction,
        structural_reduction=structural_reduction,
        semantic_reduction=semantic_reduction,
        semantic_deferred=tool_clear_reduction >= DEFER_THRESHOLD,
    )


def build_report(results: list[LayerResult]) -> CompactionReport:
    """Pure metric computation: means + ACON band + semantic-deferral rate."""
    total = len(results)
    if total == 0:
        raise ValueError("no results to report")
    mean_tc = sum(r.tool_clear_reduction for r in results) / total
    mean_st = sum(r.structural_reduction for r in results) / total
    sem_results = [r.semantic_reduction for r in results if r.semantic_reduction is not None]
    semantic_ran = len(sem_results) > 0
    mean_sem = (sum(sem_results) / len(sem_results)) if semantic_ran else None
    deferred_rate = sum(1 for r in results if r.semantic_deferred) / total
    in_band = ACON_BAND[0] <= mean_tc <= ACON_BAND[1]
    return CompactionReport(
        total=total,
        mean_tool_clear_reduction=mean_tc,
        mean_structural_reduction=mean_st,
        mean_semantic_reduction=mean_sem,
        in_acon_band=in_band,
        semantic_deferred_rate=deferred_rate,
        semantic_ran=semantic_ran,
        preclear_recommended=(in_band and deferred_rate >= DEFER_RATE_FLOOR),
        results=results,
    )


def report_to_markdown(report: CompactionReport, *, stamp: str) -> str:
    """Render a human-readable per-layer yield report (for the design-note verdict)."""
    sem = (
        f"{report.mean_semantic_reduction:.2%}"
        if report.mean_semantic_reduction is not None
        else "n/a (Azure arm skipped — RUN_AZURE_INTEGRATION unset)"
    )
    lines = [
        f"# Layered Compaction Yield — {stamp}",
        "",
        f"- cases: **{report.total}** (tool-heavy transcript specs)",
        f"- ACON band: [{ACON_BAND[0]:.0%}, {ACON_BAND[1]:.0%}] · defer threshold: "
        f"{DEFER_THRESHOLD:.0%} (~1.5x over budget)",
        "",
        "| metric | value |",
        "|--------|-------|",
        f"| mean tool_clear_reduction | **{report.mean_tool_clear_reduction:.2%}** |",
        f"| in_acon_band | **{report.in_acon_band}** |",
        f"| mean structural_reduction | {report.mean_structural_reduction:.2%} |",
        f"| mean semantic_reduction | {sem} |",
        f"| semantic_deferred_rate | **{report.semantic_deferred_rate:.2%}** |",
        f"| **preclear_recommended** | **{report.preclear_recommended}** |",
        "",
        "| case | L0 | L1 tool-clear | L2 structural | L3 semantic | tool-clear% | deferred |",
        "|------|----|--------------:|--------------:|------------:|------------:|:--------:|",
    ]
    for r in report.results:
        l3 = "—" if r.l3_semantic is None else str(r.l3_semantic)
        lines.append(
            f"| {r.id} | {r.l0_tokens} | {r.l1_tool_clear} | {r.l2_structural} | "
            f"{l3} | {r.tool_clear_reduction:.2%} | {'yes' if r.semantic_deferred else 'no'} |"
        )
    lines += [
        "",
        "> tool_clear_reduction = fraction reclaimed by the LLM-free tool-result clear ALONE. "
        "in_acon_band confirms research #4's 26-54% claim. semantic_deferred_rate = how often the "
        "cheap layer alone drops below the semantic trigger (~1.5x-over assumption) — i.e. the "
        "expensive LLM summarize is avoided. NO-OP cases (single-user-turn) reflect the "
        "user-anchored masker limitation (→ AD-Compaction-ToolAnchored-Preclear-Phase58).",
    ]
    return "\n".join(lines) + "\n"


async def _amain(corpus: Path, out_dir: Path) -> int:
    counter = TiktokenCounter(model="gpt-4o")
    cases = load_cases(corpus)

    hybrid_factory: Callable[[int], Compactor] | None = None
    if os.environ.get("RUN_AZURE_INTEGRATION"):
        # Lazy import so the CI-safe core needs no Azure adapter env (mirrors the other harnesses).
        from adapters.azure_openai.profile import build_azure_model_profile
        from agent_harness.context_mgmt.compactor.hybrid import HybridCompactor
        from agent_harness.context_mgmt.compactor.semantic import SemanticCompactor

        profile = build_azure_model_profile()

        def _make_hybrid(keep_recent: int) -> Compactor:
            return HybridCompactor(
                structural=_make_structural(keep_recent),
                semantic=SemanticCompactor(
                    chat_client=profile.cheap,
                    keep_recent_turns=keep_recent,
                    token_budget=1,
                    token_threshold_ratio=0.75,
                ),
                token_budget=1,
                token_threshold_ratio=0.75,
            )

        hybrid_factory = _make_hybrid
    else:
        print(
            "WARNING: RUN_AZURE_INTEGRATION unset — measuring the LLM-free layers (L0/L1/L2) "
            "only; the semantic arm (L3) is skipped (gate-only, NOT a semantic-yield claim).",
            file=sys.stderr,
        )

    results: list[LayerResult] = []
    for case in cases:
        results.append(await measure_case(case, counter, hybrid_factory=hybrid_factory))

    report = build_report(results)
    out_dir.mkdir(parents=True, exist_ok=True)
    md = report_to_markdown(report, stamp=datetime(2026, 1, 1).isoformat(timespec="seconds"))
    (out_dir / "layered_compaction_report.md").write_text(md, encoding="utf-8")
    (out_dir / "layered_compaction_report.json").write_text(
        json.dumps(
            {
                "total": report.total,
                "mean_tool_clear_reduction": report.mean_tool_clear_reduction,
                "mean_structural_reduction": report.mean_structural_reduction,
                "mean_semantic_reduction": report.mean_semantic_reduction,
                "in_acon_band": report.in_acon_band,
                "semantic_deferred_rate": report.semantic_deferred_rate,
                "semantic_ran": report.semantic_ran,
                "preclear_recommended": report.preclear_recommended,
                "results": [r.__dict__ for r in report.results],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(md)
    return 0


def main() -> int:
    # The report markdown carries non-ASCII typography (— · ~); a Windows cp950 console
    # can't encode it. Force the stdout text layer to UTF-8 so the print never crashes.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except Exception:  # noqa: BLE001 — best-effort; redirected/odd streams keep their codec
        pass
    parser = argparse.ArgumentParser(description="Layered compaction yield (Sprint 57.139).")
    parser.add_argument(
        "--corpus",
        default=str(
            Path(__file__).resolve().parent.parent
            / "tests"
            / "fixtures"
            / "context_mgmt"
            / "layered_compaction_cases.yaml"
        ),
    )
    parser.add_argument(
        "--out", default=str(Path(__file__).resolve().parent.parent / "benchmark_reports")
    )
    args = parser.parse_args()
    return asyncio.run(_amain(Path(args.corpus), Path(args.out)))


if __name__ == "__main__":
    sys.exit(main())
