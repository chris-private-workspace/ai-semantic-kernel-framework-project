"""
File: backend/src/agent_harness/context_mgmt/compactor/structural.py
Purpose: Rule-based Compactor; preserves system + recent N turns + HITL decisions, drops redundant tool retries.  # noqa: E501
Category: 範疇 4 (Context Management)
Scope: Phase 52 / Sprint 52.1 Day 2

Description:
    StructuralCompactor is the fast-path compaction strategy. It applies
    deterministic rules without invoking the LLM:

      1. Always keep `role="system"` messages.
      2. Always keep messages tagged `metadata["hitl"]=True` (approval flow).
      3. Keep the most recent `keep_recent_turns` user/assistant turns.
      4. Within the kept window, drop redundant tool retries: if the same
         (tool_name, sha256(args)) appears N times consecutively, only the
         latest call + result pair is kept.
      5. (Day 3.3) Old tool results outside keep_recent are masked via
         injected ObservationMasker. Day 2 ships an inline tombstone path so
         the strategy is functional before Day 3 wires the masker.
      6. (Sprint 57.161) When a TokenCounter is injected, tokens_after is a
         REAL post-mask re-count (mirroring PreClearCompactor) so in-place
         tombstoning surfaces its reduction. Without a counter it falls back to
         a message-count ratio (blind to tombstoning; byte-identical pre-57.161).

Why this exists:
    V1 ignored context rot (AP-7). Long conversations blew context windows
    and degraded reasoning quality. Structural compaction is the cheap first
    line of defence (target p95 < 100ms). HybridCompactor falls through to
    SemanticCompactor only when structural cannot reach the budget.

Owner: 01-eleven-categories-spec.md §範疇 4
Single-source: 17-cross-category-interfaces.md §2.1 (Compactor row)

Related:
    - compactor/_abc.py (Compactor ABC)
    - 04-anti-patterns.md AP-7 (Context Rot Ignored — root motivation)
    - sprint-52-1-plan.md §1 Story 2 (3 strategies switchable)

Created: 2026-05-01 (Sprint 52.1 Day 2.1)

Modification History:
    - 2026-07-07: Sprint 57.161 — real tokens_after re-count when token_counter injected
    - 2026-05-01: Initial creation (Sprint 52.1 Day 2.1) — rule-based compaction
"""

from __future__ import annotations

import hashlib
import json
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


def _tool_call_signature(msg: Message) -> str | None:
    """Return a (tool_name, args_hash) signature for deduplication, or None."""
    if not msg.tool_calls:
        return None
    parts: list[str] = []
    for tc in msg.tool_calls:
        try:
            args_hash = hashlib.sha256(
                json.dumps(tc.arguments, sort_keys=True, default=str).encode("utf-8")
            ).hexdigest()[:16]
        except (TypeError, ValueError):
            args_hash = "unhashable"
        parts.append(f"{tc.name}:{args_hash}")
    return "|".join(parts)


def _drop_redundant_tool_retries(messages: list[Message]) -> tuple[list[Message], int]:
    """Collapse consecutive duplicate tool calls; keep only the most recent pair.

    Two assistant messages with the same (tool_name, args_hash) are considered
    a retry pair; only the latest pair (assistant call + matching tool result)
    survives. Returns (filtered_messages, dropped_count).
    """
    keep_indices: set[int] = set(range(len(messages)))
    seen_signatures: dict[str, int] = {}

    for i, msg in enumerate(messages):
        if msg.role != "assistant":
            continue
        sig = _tool_call_signature(msg)
        if sig is None:
            continue
        prior_idx = seen_signatures.get(sig)
        if prior_idx is not None and prior_idx in keep_indices:
            keep_indices.discard(prior_idx)
            if prior_idx + 1 < len(messages) and messages[prior_idx + 1].role == "tool":
                keep_indices.discard(prior_idx + 1)
        seen_signatures[sig] = i

    filtered = [m for i, m in enumerate(messages) if i in keep_indices]
    dropped = len(messages) - len(filtered)
    return filtered, dropped


class StructuralCompactor(Compactor):
    """Rule-based context compaction. Target p95 < 100ms (per Sprint 52.1 §1)."""

    def __init__(
        self,
        *,
        keep_recent_turns: int = 5,
        preserve_hitl: bool = True,
        token_budget: int = 100_000,
        token_threshold_ratio: float = 0.75,
        turn_threshold: int = 30,
        masker: ObservationMasker | None = None,
        token_counter: TokenCounter | None = None,
    ) -> None:
        self.keep_recent_turns = keep_recent_turns
        self.preserve_hitl = preserve_hitl
        self.token_budget = token_budget
        self.token_threshold_ratio = token_threshold_ratio
        self.turn_threshold = turn_threshold
        # Day 3.3: dependency-injected masker. Default = DefaultObservationMasker.
        # Replaces the Day 2 inline _redact_old_tool_results helper.
        self.masker: ObservationMasker = masker or DefaultObservationMasker()
        # Sprint 57.161: when injected, tokens_after is a REAL post-mask re-count
        # (mirrors PreClearCompactor) instead of the message-count ratio that is
        # blind to in-place tombstoning. None → legacy ratio (byte-identical).
        self.token_counter = token_counter

    def should_compact(self, state: LoopState) -> bool:
        """Override ABC default with concrete state path access."""
        if state.transient.token_usage_so_far > self.token_budget * self.token_threshold_ratio:
            return True
        if state.transient.current_turn > self.turn_threshold:
            return True
        return False

    async def compact_if_needed(
        self,
        state: LoopState,
        *,
        trace_context: TraceContext | None = None,
    ) -> CompactionResult:
        start = time.perf_counter()
        tokens_before = state.transient.token_usage_so_far
        original_count = len(state.transient.messages)

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

        # Step 1: separate the always-keep set (system + HITL) from the rest
        always_keep_indices: set[int] = set()
        for i, msg in enumerate(messages):
            if msg.role == "system":
                always_keep_indices.add(i)
            elif self.preserve_hitl and msg.metadata.get("hitl") is True:
                always_keep_indices.add(i)

        # Step 2: drop redundant tool retries (excluding always-keep messages)
        rest_messages = [m for i, m in enumerate(messages) if i not in always_keep_indices]
        rest_filtered, _dropped = _drop_redundant_tool_retries(rest_messages)

        # Step 3: redact old tool results via injected ObservationMasker (Day 3.3)
        rest_redacted = self.masker.mask_old_results(
            rest_filtered, keep_recent=self.keep_recent_turns
        )

        # Step 4: re-merge — preserve order: always_keep messages stay where they were
        kept_messages: list[Message] = []
        rest_iter = iter(rest_redacted)
        rest_buffer: list[Message] = list(rest_iter)
        rest_pointer = 0
        for i, msg in enumerate(messages):
            if i in always_keep_indices:
                kept_messages.append(msg)
            else:
                # consume one from rest_buffer (skipping ones that were filtered out)
                if rest_pointer < len(rest_buffer):
                    kept_messages.append(rest_buffer[rest_pointer])
                    rest_pointer += 1

        # Step 5: build new state with the same durable + transient swapped in.
        # tokens_after feeds BOTH the chat-v2 compaction marker AND the loop's
        # ongoing budget — loop.py:2282 sets `tokens_used = result.tokens_after`
        # and does NOT re-count (the earlier "Loop.run() will re-count" claim was
        # stale). So this value must reflect the REAL reduction.
        if self.token_counter is not None:
            # Real token re-count (mirror PreClearCompactor preclear.py:178-181):
            # a message-count ratio is BLIND to in-place tombstoning (the masker
            # shrinks tool bodies without dropping messages → len unchanged →
            # ratio 1.0 → a no-op tokens_after). Apply the true reduction ratio
            # to the loop-scale tokens_before so the marker + budget both move.
            tokens_original = self.token_counter.count(messages=messages)
            tokens_masked = self.token_counter.count(messages=kept_messages)
            reduction_ratio = (tokens_masked / tokens_original) if tokens_original > 0 else 1.0
            new_token_usage = int(tokens_before * reduction_ratio)
        else:
            # Legacy message-count ratio (byte-identical pre-57.161; used when no
            # counter is injected, e.g. unit tests constructing StructuralCompactor()).
            new_token_usage = int(tokens_before * len(kept_messages) / max(original_count, 1))
        new_transient = replace(
            state.transient,
            messages=kept_messages,
            token_usage_so_far=new_token_usage,
        )
        new_state = replace(state, transient=new_transient)
        tokens_after = new_transient.token_usage_so_far
        messages_compacted = original_count - len(kept_messages)

        return CompactionResult(
            triggered=True,
            strategy_used=CompactionStrategy.STRUCTURAL,
            tokens_before=tokens_before,
            tokens_after=tokens_after,
            messages_compacted=messages_compacted,
            duration_ms=(time.perf_counter() - start) * 1000.0,
            compacted_state=new_state,
        )
