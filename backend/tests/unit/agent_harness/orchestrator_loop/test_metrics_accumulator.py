"""
File: backend/tests/unit/agent_harness/orchestrator_loop/test_metrics_accumulator.py
Purpose: Unit tests for LoopMetricsAccumulator (57.2 closes AD-Cat10-Cat11-LoopMetricsAccumulator).
Category: Tests
Created: 2026-05-07 (Sprint 57.2 Day 3)
"""

from __future__ import annotations

from agent_harness._contracts.events import (
    LLMResponded,
    SubagentSpawned,
    ToolCallExecuted,
    VerificationFailed,
    VerificationPassed,
)
from agent_harness._contracts.observability import TraceContext
from agent_harness.orchestrator_loop._metrics import LoopMetricsAccumulator


def _ctx() -> TraceContext:
    return TraceContext()


def test_accumulator_initial_state_is_zero() -> None:
    """Fresh accumulator has all counters at 0 and provider/model empty."""
    acc = LoopMetricsAccumulator()
    assert acc.total_turns == 0
    assert acc.cumulative_input_tokens == 0
    assert acc.cumulative_output_tokens == 0
    assert acc.verification_iterations == 0
    assert acc.subagent_dispatched == 0
    assert acc.last_provider == ""
    assert acc.last_model == ""
    assert acc.total_tokens == 0  # property == sum


def test_accumulator_llm_responded_accumulates_split_and_attribution() -> None:
    """LLMResponded events accumulate input/output and capture provider/model."""
    acc = LoopMetricsAccumulator()
    acc.on_event(
        LLMResponded(
            content="hi",
            provider="azure_openai",
            model="gpt-5.4",
            input_tokens=100,
            output_tokens=50,
            trace_context=_ctx(),
        )
    )
    acc.on_event(
        LLMResponded(
            content="more",
            provider="azure_openai",
            model="gpt-5.4",
            input_tokens=200,
            output_tokens=80,
            trace_context=_ctx(),
        )
    )
    assert acc.total_turns == 2
    assert acc.cumulative_input_tokens == 300
    assert acc.cumulative_output_tokens == 130
    assert acc.total_tokens == 430
    assert acc.last_provider == "azure_openai"
    assert acc.last_model == "gpt-5.4"


def test_accumulator_provider_model_most_recent_wins() -> None:
    """Multi-model loop reports last LLM call's provider/model (dominant)."""
    acc = LoopMetricsAccumulator()
    acc.on_event(
        LLMResponded(
            content="a",
            provider="azure_openai",
            model="gpt-5.4",
            input_tokens=10,
            output_tokens=5,
            trace_context=_ctx(),
        )
    )
    acc.on_event(
        LLMResponded(
            content="b",
            provider="anthropic",
            model="claude-3.7-sonnet",
            input_tokens=20,
            output_tokens=10,
            trace_context=_ctx(),
        )
    )
    assert acc.last_provider == "anthropic"
    assert acc.last_model == "claude-3.7-sonnet"
    # Cumulative still sums across providers
    assert acc.cumulative_input_tokens == 30
    assert acc.cumulative_output_tokens == 15


def test_accumulator_verification_pass_and_fail_count_iterations() -> None:
    """Both VerificationPassed and VerificationFailed increment iterations."""
    acc = LoopMetricsAccumulator()
    acc.on_event(VerificationPassed(verifier="rules", trace_context=_ctx()))
    acc.on_event(VerificationFailed(verifier="judge", reason="bad", trace_context=_ctx()))
    acc.on_event(VerificationPassed(verifier="rules", trace_context=_ctx()))
    assert acc.verification_iterations == 3


def test_accumulator_subagent_spawned_increments_count() -> None:
    """SubagentSpawned events count toward subagent_dispatched."""
    acc = LoopMetricsAccumulator()
    from uuid import uuid4

    pid = uuid4()
    acc.on_event(
        SubagentSpawned(
            subagent_id=uuid4(), mode="fork", parent_session_id=pid, trace_context=_ctx()
        )
    )
    acc.on_event(
        SubagentSpawned(
            subagent_id=uuid4(), mode="teammate", parent_session_id=pid, trace_context=_ctx()
        )
    )
    assert acc.subagent_dispatched == 2


def test_accumulator_unrelated_events_are_noop() -> None:
    """ToolCallExecuted and similar events do not affect accumulator state."""
    acc = LoopMetricsAccumulator()
    acc.on_event(
        ToolCallExecuted(
            tool_call_id="t1",
            tool_name="search",
            duration_ms=10.0,
            result_content="ok",
            trace_context=_ctx(),
        )
    )
    assert acc.total_turns == 0
    assert acc.cumulative_input_tokens == 0


def test_accumulator_to_loop_completed_payload_returns_six_fields() -> None:
    """to_loop_completed_payload() returns dict ready for LoopCompleted unpack."""
    acc = LoopMetricsAccumulator()
    acc.on_event(
        LLMResponded(
            content="x",
            provider="azure_openai",
            model="gpt-5.4",
            input_tokens=42,
            output_tokens=8,
            trace_context=_ctx(),
        )
    )
    payload = acc.to_loop_completed_payload()
    assert payload == {
        "total_turns": 1,
        "total_tokens": 50,
        "input_tokens": 42,
        "output_tokens": 8,
        "provider": "azure_openai",
        "model": "gpt-5.4",
    }


def test_accumulator_cached_input_tokens_accumulate() -> None:
    """Sprint 57.65 A-2 Tier2: cached_input_tokens sum across LLMResponded events."""
    acc = LoopMetricsAccumulator()
    acc.on_event(
        LLMResponded(
            content="a",
            input_tokens=100,
            output_tokens=10,
            cached_input_tokens=40,
            trace_context=_ctx(),
        )
    )
    acc.on_event(
        LLMResponded(
            content="b",
            input_tokens=200,
            output_tokens=20,
            cached_input_tokens=120,
            trace_context=_ctx(),
        )
    )
    assert acc.cumulative_cached_input_tokens == 160
    assert acc.cumulative_input_tokens == 300


def test_accumulator_cache_hit_rate_computed_and_div0_guarded() -> None:
    """Sprint 57.65 A-2 Tier2: cache_hit_rate = cached / input; 0.0 when no input."""
    empty = LoopMetricsAccumulator()
    assert empty.cache_hit_rate == 0.0  # div-by-0 guarded (no input tokens yet)

    acc = LoopMetricsAccumulator()
    acc.on_event(
        LLMResponded(
            content="x",
            input_tokens=100,
            output_tokens=5,
            cached_input_tokens=75,
            trace_context=_ctx(),
        )
    )
    assert acc.cache_hit_rate == 0.75


def test_accumulator_empty_provider_model_does_not_overwrite() -> None:
    """LLMResponded with empty provider/model doesn't clear previously-captured values."""
    acc = LoopMetricsAccumulator()
    acc.on_event(
        LLMResponded(
            content="a",
            provider="azure_openai",
            model="gpt-5.4",
            input_tokens=10,
            output_tokens=5,
            trace_context=_ctx(),
        )
    )
    # Subsequent event with empty provider/model (e.g. early-stub case).
    acc.on_event(
        LLMResponded(
            content="b",
            provider="",
            model="",
            input_tokens=5,
            output_tokens=2,
            trace_context=_ctx(),
        )
    )
    # Cumulative still grows; provider/model preserved from earlier event.
    assert acc.last_provider == "azure_openai"
    assert acc.last_model == "gpt-5.4"
    assert acc.cumulative_input_tokens == 15
    assert acc.cumulative_output_tokens == 7
