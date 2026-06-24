"""
File: backend/src/agent_harness/context_mgmt/compactor/preclear.py
Purpose: PreClearCompactor — standalone, earlier-triggering, LLM-free tool-result clearing layer (ACON preclear).  # noqa: E501
Category: 範疇 4 (Context Management)
Scope: Phase 57 / Sprint 57.139

Description:
    PreClearCompactor runs ONLY observation masking (tool-result tombstoning)
    at a LOWER trigger ratio than the full structural/semantic compaction, so
    the cheap, deterministic tool-result clear can keep context under budget
    BEFORE the expensive semantic summarize (a cheap-tier LLM call, C2 57.109)
    is ever invoked. This is the ACON "layered compaction: tool-result clearing
    first" axis — distinct from C2's cheap-tier semantic routing.

    It reuses DefaultObservationMasker (no new masking logic) and mirrors
    StructuralCompactor's system + HITL preservation, but skips the dedup and
    semantic stages. Unlike StructuralCompactor — whose tokens_after is a
    message-count ratio approximation (structural.py:192-193, blind to content
    tombstoning) — PreClearCompactor counts the post-mask tokens with an
    injected TokenCounter, so the loop's `tokens_used = result.tokens_after`
    (loop.py:2234) and the ChainedCompactor's downstream hybrid see the REAL
    reduction and can defer semantic.

    KNOWN LIMITATION (Sprint 57.139 Day-0 D-masker-user-anchored): the masker
    anchors its keep-window on USER message count; the chat main flow runs one
    user message per loop run (_category_factories.py:129-134), so masking
    NO-OPs on single-send chat and fires only on rehydrated multi-turn (57.127)
    / mid-run injection (B1). A tool-anchored clear (by tool_use_id) to cover
    single-send is deferred to AD-Compaction-ToolAnchored-Preclear-Phase58.

Key Components:
    - PreClearCompactor: Compactor; should_compact at preclear_ratio*budget;
      compact_if_needed runs mask_old_results + accurate TokenCounter re-count.

LLM neutrality: imports the TokenCounter ABC only; the factory injects the
concrete TiktokenCounter (a pure tokenizer, no provider SDK). No openai /
anthropic import here or downstream.

Owner: 01-eleven-categories-spec.md §範疇 4
Single-source: 17-cross-category-interfaces.md §2.1 (Compactor row)

Related:
    - compactor/_abc.py (Compactor ABC)
    - observation_masker.py (DefaultObservationMasker — reused, not modified)
    - compactor/structural.py (system+HITL preservation pattern mirrored here)
    - compactor/chained.py (composes preclear -> hybrid)
    - 04-anti-patterns.md AP-7 (Context Rot Ignored — root motivation)

Created: 2026-06-24 (Sprint 57.139)

Modification History:
    - 2026-06-24: Initial creation (Sprint 57.139) — ACON tool-result preclear layer
"""

from __future__ import annotations

import time
from dataclasses import replace

from agent_harness._contracts import (
    CompactionResult,
    CompactionStrategy,
    LoopState,
    Message,
    TraceContext,
)
from agent_harness.context_mgmt._abc import ObservationMasker
from agent_harness.context_mgmt.compactor._abc import Compactor
from agent_harness.context_mgmt.observation_masker import DefaultObservationMasker
from agent_harness.context_mgmt.token_counter._abc import TokenCounter


class PreClearCompactor(Compactor):
    """Earlier-triggering, LLM-free tool-result clearing layer (ACON preclear).

    Reuses DefaultObservationMasker; triggers at preclear_ratio (default 0.50,
    LOWER than the 0.75 structural/semantic threshold). Reports the
    STRUCTURAL strategy (a structural-family tool clear) to avoid a new wire
    enum (Sprint 57.139 D-compaction-strategy-wire).
    """

    def __init__(
        self,
        *,
        token_counter: TokenCounter,
        preclear_ratio: float = 0.50,
        keep_recent_turns: int = 5,
        preserve_hitl: bool = True,
        token_budget: int = 100_000,
        masker: ObservationMasker | None = None,
    ) -> None:
        self.token_counter = token_counter
        self.preclear_ratio = preclear_ratio
        self.keep_recent_turns = keep_recent_turns
        self.preserve_hitl = preserve_hitl
        self.token_budget = token_budget
        self.masker: ObservationMasker = masker or DefaultObservationMasker()

    def should_compact(self, state: LoopState) -> bool:
        """Trigger when token usage exceeds the (lower) preclear ratio.

        Deliberately NOT turn-count gated: the preclear is purely a token-budget
        relief valve that should fire earlier than the full compactor.
        """
        return state.transient.token_usage_so_far > self.token_budget * self.preclear_ratio

    async def compact_if_needed(
        self,
        state: LoopState,
        *,
        trace_context: TraceContext | None = None,
    ) -> CompactionResult:
        start = time.perf_counter()
        tokens_before = state.transient.token_usage_so_far

        if not self.should_compact(state):
            return CompactionResult(
                triggered=False,
                strategy_used=None,
                tokens_before=tokens_before,
                tokens_after=tokens_before,
                messages_compacted=0,
                duration_ms=(time.perf_counter() - start) * 1000.0,
                compacted_state=None,
            )

        messages = list(state.transient.messages)

        # Preserve system + HITL messages (mirror StructuralCompactor step 1) so
        # the masker never tombstones an approval-flow tool result.
        always_keep_indices: set[int] = set()
        for i, msg in enumerate(messages):
            if msg.role == "system":
                always_keep_indices.add(i)
            elif self.preserve_hitl and msg.metadata.get("hitl") is True:
                always_keep_indices.add(i)

        rest_messages = [m for i, m in enumerate(messages) if i not in always_keep_indices]
        rest_masked = self.masker.mask_old_results(
            rest_messages, keep_recent=self.keep_recent_turns
        )

        # Count tombstoned messages (content changed in place; no message dropped).
        tombstoned = sum(
            1 for orig, new in zip(rest_messages, rest_masked) if orig.content != new.content
        )
        if tombstoned == 0:
            # Nothing to clear (e.g. <= keep_recent user turns — the user-anchored
            # NO-OP path). Honest passthrough rather than a no-op "triggered" event.
            return CompactionResult(
                triggered=False,
                strategy_used=None,
                tokens_before=tokens_before,
                tokens_after=tokens_before,
                messages_compacted=0,
                duration_ms=(time.perf_counter() - start) * 1000.0,
                compacted_state=None,
            )

        # Re-merge: always-keep messages stay in place; consume masked rest in order
        # (masking preserves length, so the buffer maps 1:1).
        kept_messages: list[Message] = []
        rest_pointer = 0
        for i, msg in enumerate(messages):
            if i in always_keep_indices:
                kept_messages.append(msg)
            else:
                kept_messages.append(rest_masked[rest_pointer])
                rest_pointer += 1

        # Real token-reduction ratio (NOT StructuralCompactor's message-count
        # ratio at structural.py:192-193, which is blind to in-place tombstoning)
        # applied to the loop-tracked tokens_before. This keeps tokens_after in
        # the loop's token scale (so the ContextCompacted delta and the chained
        # hybrid's should_compact compare apples-to-apples against token_budget)
        # WHILE reflecting the true masking reduction → the downstream hybrid can
        # defer its semantic stage. count() is keyword-only (token_counter/_abc.py:43-49).
        tokens_original = self.token_counter.count(messages=messages)
        tokens_masked = self.token_counter.count(messages=kept_messages)
        reduction_ratio = (tokens_masked / tokens_original) if tokens_original > 0 else 1.0
        tokens_after = int(tokens_before * reduction_ratio)

        new_transient = replace(
            state.transient,
            messages=kept_messages,
            token_usage_so_far=tokens_after,
        )
        new_state = replace(state, transient=new_transient)

        return CompactionResult(
            triggered=True,
            # STRUCTURAL (not a new PRECLEAR enum) — preclear is a structural-family
            # tool clear; reusing the value avoids a wire/codegen touch (D-strategy-wire).
            strategy_used=CompactionStrategy.STRUCTURAL,
            tokens_before=tokens_before,
            tokens_after=tokens_after,
            messages_compacted=tombstoned,
            duration_ms=(time.perf_counter() - start) * 1000.0,
            compacted_state=new_state,
        )
