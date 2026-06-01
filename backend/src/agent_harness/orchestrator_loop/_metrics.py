"""
File: backend/src/agent_harness/orchestrator_loop/_metrics.py
Purpose: LoopMetricsAccumulator — sum-across-loop metrics replacing last-event proxy.
Category: 範疇 1 (Orchestrator Loop) — supports Cat 10/11/12 metrics
Scope: Phase 57+ Sprint 57.2 (Audit Cycle Lvl 2 — closes AD-Cat10-Cat11-LoopMetricsAccumulator)

Description:
    Accumulator over LoopEvent stream. Sum input/output tokens + verification
    iterations + subagent dispatched count + retain dominant provider/model.

    Replaces SLAMonitor.classify_loop_complexity()'s reliance on last-event
    proxy (LoopCompleted.total_tokens / total_turns alone) per AD-Cat10-Cat11
    -LoopMetricsAccumulator (56.3 carryover; deferred to Phase 56.x → closed
    Sprint 57.2). Also enables AD-Cost-Ledger-Token-Split (input/output split)
    + AD-Cost-Ledger-Provider-Attribution (real provider/model attribution
    from per-call LLMResponded events instead of chat router hardcoded
    azure_openai/gpt-5.4 default).

Key Components:
    - LoopMetricsAccumulator: dataclass with cumulative state + on_event() hook
    - on_event(event): consume LoopEvent and update state in-place
    - to_loop_completed_payload(): return tuple of accumulator-sourced
      LoopCompleted fields for AgentLoop final emit

Created: 2026-05-07 (Sprint 57.2 Day 1)
Last Modified: 2026-05-07

Modification History (newest-first):
    - 2026-06-01: Sprint 57.65 A-2 — accumulate cached_input_tokens + cache_hit_rate prop
    - 2026-05-07: Sprint 57.2 Day 1 — initial (closes AD-Cat10-Cat11-LoopMetricsAccumulator)

Related:
    - 17-cross-category-interfaces.md §Cat 12 metrics
    - sla_monitor.py L92-94 — Day 0 D2 documented this deferred accumulator need
    - LoopCompleted event (events.py L106) — input/output/provider/model fields (57.2 Day 1)
    - cost_ledger.py record_llm_call() — consumes split via chat router observer
"""

from __future__ import annotations

from dataclasses import dataclass

from .._contracts.events import (
    LLMResponded,
    LoopEvent,
    SubagentSpawned,
    VerificationFailed,
    VerificationPassed,
)

__all__ = ["LoopMetricsAccumulator"]


@dataclass
class LoopMetricsAccumulator:
    """Sum-across-loop metrics replacing last-event proxy.

    State accumulates from LLMResponded / VerificationCompleted /
    SubagentDispatched events. Provider/model use most-recent-wins
    (dominant attribution for multi-model loops; single-model loops
    report unambiguously).
    """

    total_turns: int = 0
    cumulative_input_tokens: int = 0
    cumulative_output_tokens: int = 0
    # Sprint 57.65 A-2 Tier2: cumulative cached-input tokens (prompt-cache
    # observability). Sourced from the neutral TokenUsage.cached_input_tokens
    # via LLMResponded.cached_input_tokens; dropped before 57.65 (flowed only
    # to billing). Feeds LoopCompleted.cache_hit_rate.
    cumulative_cached_input_tokens: int = 0
    verification_iterations: int = 0
    subagent_dispatched: int = 0
    last_provider: str = ""
    last_model: str = ""

    def on_event(self, event: LoopEvent) -> None:
        """Consume one LoopEvent and update accumulator state.

        - LLMResponded: accumulate input/output tokens; update last provider/model
        - VerificationPassed | VerificationFailed: increment verification_iterations
        - SubagentSpawned: increment subagent_dispatched
        - Other events: no-op

        Note: D14 finding (Sprint 57.2 Day 1) — verification events are named
        VerificationPassed + VerificationFailed (no Completed); subagent event
        is SubagentSpawned (no Dispatched). Both Pass/Fail count as iterations.
        """
        if isinstance(event, LLMResponded):
            self.total_turns += 1
            self.cumulative_input_tokens += event.input_tokens
            self.cumulative_output_tokens += event.output_tokens
            self.cumulative_cached_input_tokens += event.cached_input_tokens
            if event.provider:
                self.last_provider = event.provider
            if event.model:
                self.last_model = event.model
        elif isinstance(event, (VerificationPassed, VerificationFailed)):
            self.verification_iterations += 1
        elif isinstance(event, SubagentSpawned):
            self.subagent_dispatched += 1

    @property
    def total_tokens(self) -> int:
        """Cumulative input + output (invariant: == LoopCompleted.total_tokens)."""
        return self.cumulative_input_tokens + self.cumulative_output_tokens

    @property
    def cache_hit_rate(self) -> float:
        """Prompt-cache hit rate = cached_input / input (div-by-0 guarded → 0.0).

        Sprint 57.65 A-2 Tier2: single DRY source for the rate consumed by both
        LoopCompleted emission sites. Returns 0.0 when no input tokens have been
        accumulated (early-termination before any LLM call).
        """
        if self.cumulative_input_tokens <= 0:
            return 0.0
        return self.cumulative_cached_input_tokens / self.cumulative_input_tokens

    def to_loop_completed_payload(self) -> dict[str, int | str]:
        """Return accumulator-sourced LoopCompleted field values.

        Used by AgentLoop final emit to populate LoopCompleted with
        cumulative split + dominant provider/model. Caller adds
        stop_reason + trace fields separately.
        """
        return {
            "total_turns": self.total_turns,
            "total_tokens": self.total_tokens,
            "input_tokens": self.cumulative_input_tokens,
            "output_tokens": self.cumulative_output_tokens,
            "provider": self.last_provider,
            "model": self.last_model,
        }
