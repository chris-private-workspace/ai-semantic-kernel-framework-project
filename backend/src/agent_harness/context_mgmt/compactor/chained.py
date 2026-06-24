"""
File: backend/src/agent_harness/context_mgmt/compactor/chained.py
Purpose: ChainedCompactor — run an ordered list of compactors in sequence, threading compacted state.  # noqa: E501
Category: 範疇 4 (Context Management)
Scope: Phase 57 / Sprint 57.139

Description:
    ChainedCompactor composes multiple Compactor strategies into a single
    Compactor so the loop's one `self._compactor.compact_if_needed` call site
    (loop.py:2221) stays untouched. Each child runs on the PREVIOUS child's
    compacted output (state threaded forward), so a cheap early layer (the
    PreClearCompactor) can reduce tokens FIRST and a later layer (the
    HybridCompactor) then sees the reduced count via should_compact and may
    skip its expensive semantic stage entirely — the ACON "tool-result clearing
    first defers semantic" mechanism.

    Result merge: messages_compacted accumulates across triggered children;
    tokens_after = the final threaded state's token_usage_so_far; strategy_used
    = the last triggered child's strategy; the LLM-usage attribution fields
    (input/output_tokens, model — Sprint 57.109 C2) carry the last child that
    reported a real summarize call, so the ledger `_compaction` sub_type
    attribution survives the chain.

Key Components:
    - ChainedCompactor: Compactor; sequential composition (preclear -> hybrid).

LLM neutrality: composes Compactor ABCs only; no provider SDK import.

Owner: 01-eleven-categories-spec.md §範疇 4
Single-source: 17-cross-category-interfaces.md §2.1 (Compactor row)

Related:
    - compactor/_abc.py (Compactor ABC)
    - compactor/preclear.py (the early stage)
    - compactor/hybrid.py (the structural->semantic stage)
    - _category_factories.py make_chat_compactor (wires [preclear, hybrid] when enabled)

Created: 2026-06-24 (Sprint 57.139)

Modification History:
    - 2026-06-24: Initial creation (Sprint 57.139) — sequential compactor composition
"""

from __future__ import annotations

import time

from agent_harness._contracts import (
    CompactionResult,
    CompactionStrategy,
    LoopState,
    TraceContext,
)
from agent_harness.context_mgmt.compactor._abc import Compactor


class ChainedCompactor(Compactor):
    """Run an ordered list of compactors in sequence, threading compacted state."""

    def __init__(self, *, compactors: list[Compactor]) -> None:
        if not compactors:
            raise ValueError("ChainedCompactor requires at least one compactor")
        self.compactors = list(compactors)

    def should_compact(self, state: LoopState) -> bool:
        """Trigger if ANY child would trigger (a later child may trigger only
        after an earlier one reduced — but should_compact is a cheap pre-gate;
        the per-child compact_if_needed re-checks on the threaded state)."""
        return any(c.should_compact(state) for c in self.compactors)

    async def compact_if_needed(
        self,
        state: LoopState,
        *,
        trace_context: TraceContext | None = None,
    ) -> CompactionResult:
        start = time.perf_counter()
        tokens_before = state.transient.token_usage_so_far

        current_state = state
        any_triggered = False
        total_compacted = 0
        last_strategy: CompactionStrategy | None = None
        # Carry the latest non-zero LLM summarize attribution (Sprint 57.109 C2).
        input_tokens = 0
        output_tokens = 0
        model = ""

        for compactor in self.compactors:
            result = await compactor.compact_if_needed(current_state, trace_context=trace_context)
            if result.triggered and result.compacted_state is not None:
                any_triggered = True
                current_state = result.compacted_state
                total_compacted += result.messages_compacted
                last_strategy = result.strategy_used
                if result.input_tokens or result.output_tokens or result.model:
                    input_tokens = result.input_tokens
                    output_tokens = result.output_tokens
                    model = result.model

        if not any_triggered:
            return CompactionResult(
                triggered=False,
                strategy_used=None,
                tokens_before=tokens_before,
                tokens_after=tokens_before,
                messages_compacted=0,
                duration_ms=(time.perf_counter() - start) * 1000.0,
                compacted_state=None,
            )

        return CompactionResult(
            triggered=True,
            strategy_used=last_strategy,
            tokens_before=tokens_before,
            tokens_after=current_state.transient.token_usage_so_far,
            messages_compacted=total_compacted,
            duration_ms=(time.perf_counter() - start) * 1000.0,
            compacted_state=current_state,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=model,
        )
