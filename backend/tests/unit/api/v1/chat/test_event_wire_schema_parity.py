"""
File: backend/tests/unit/api/v1/chat/test_event_wire_schema_parity.py
Purpose: Drift guard — assert WIRE_SCHEMA field sets match the live serializer output.
Category: tests
Scope: Phase 57 / Sprint 57.67 (A-5b — event schema codegen)

Description:
    The declarative WIRE_SCHEMA (event_wire_schema.py) is the single source of
    truth that the frontend events.json + loopEvents.generated.ts are generated
    from. This test locks non-drift between WIRE_SCHEMA and the actual
    `serialize_loop_event` output: for each of the 17 wired event classes it
    builds one representative instance, serializes it, and asserts the payload's
    `data` key set (minus the universal `trace_id`) equals the registry entry.
    Drift in EITHER direction (serializer adds/removes a field, or registry
    drifts) fails this test. Also asserts the 6 unwired classes still raise
    NotImplementedError, that Thinking still serializes to None, and that the
    registry has exactly 18 entries.

Created: 2026-06-02 (Sprint 57.67)
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from agent_harness._contracts import (
    ApprovalReceived,
    ApprovalRequested,
    ContextCompacted,
    ErrorRetried,
    GuardrailTriggered,
    LLMRequested,
    LLMResponded,
    LoopCompleted,
    LoopEvent,
    LoopStarted,
    LoopTerminated,
    MemoryAccessed,
    MetricRecorded,
    PromptBuilt,
    SpanEnded,
    SpanStarted,
    StateCheckpointed,
    SubagentCompleted,
    SubagentSpawned,
    Thinking,
    ToolCall,
    ToolCallExecuted,
    ToolCallFailed,
    ToolCallRequested,
    TripwireTriggered,
    TurnStarted,
    VerificationFailed,
    VerificationPassed,
)
from api.v1.chat.event_wire_schema import BASE_FIELDS, WIRE_SCHEMA
from api.v1.chat.sse import serialize_loop_event

# One representative instance per wired event class. ToolCallExecuted +
# ToolCallFailed both map to the same 'tool_call_result' wire type (verified
# below). Constructed with kwargs (frozen dataclasses).
WIRED_EVENT_INSTANCES: list[LoopEvent] = [
    LoopStarted(session_id=uuid4()),
    TurnStarted(turn_num=1),
    LLMRequested(model="gpt-4o", tokens_in=42),
    LLMResponded(
        content="hi",
        tool_calls=(ToolCall(id="c1", name="echo", arguments={"text": "X"}),),
        thinking="reasoning",
        cached_input_tokens=10,
    ),
    ToolCallRequested(tool_call_id="c1", tool_name="echo", arguments={"text": "X"}),
    ToolCallExecuted(tool_call_id="c1", tool_name="echo", duration_ms=1.5, result_content="X"),
    ToolCallFailed(tool_call_id="c1", tool_name="echo", error="timeout"),
    LoopCompleted(stop_reason="end_turn", total_turns=2, cached_input_tokens=5, cache_hit_rate=0.5),
    ApprovalRequested(approval_request_id=uuid4(), risk_level="HIGH"),
    ApprovalReceived(approval_request_id=uuid4(), decision="APPROVED"),
    GuardrailTriggered(guardrail_type="input", action="block", reason="PII"),
    TripwireTriggered(violation_type="pii_leak", detail="ssn detected"),
    VerificationPassed(verifier="rules", verifier_type="rules_based", score=0.9),
    VerificationFailed(
        verifier="judge",
        verifier_type="llm_judge",
        reason="off-topic",
        suggested_correction="retry",
    ),
    SubagentSpawned(subagent_id=uuid4(), mode="fork", parent_session_id=uuid4()),
    SubagentCompleted(subagent_id=uuid4(), summary="done", tokens_used=12),
    ContextCompacted(
        tokens_before=8000,
        tokens_after=3000,
        compaction_strategy="summarize",
        messages_compacted=10,
        duration_ms=4.0,
    ),
    PromptBuilt(
        messages_count=6,
        estimated_input_tokens=1200,
        cache_breakpoints_count=2,
        memory_layers_used=("session", "tenant"),
        position_strategy_used="lost_in_middle",
        duration_ms=2.3,
    ),
    StateCheckpointed(version=7),
]

# Cat 8/3/1/12 events with no serializer branch (must raise NotImplementedError).
UNWIRED_EVENT_INSTANCES: list[LoopEvent] = [
    MemoryAccessed(layer="session", operation="read", key="k"),
    ErrorRetried(attempt=1, error_class="TimeoutError", backoff_ms=250.0),
    LoopTerminated(reason="budget_exceeded"),
    SpanStarted(span_name="loop", span_id="s1"),
    SpanEnded(span_name="loop", span_id="s1", duration_ms=3.0),
    MetricRecorded(metric_name="latency", value=1.0, labels={"k": "v"}),
]


class TestWireSchemaParity:
    def test_wire_schema_has_18_entries(self) -> None:
        assert len(WIRE_SCHEMA) == 18

    def test_base_fields_only_trace_id(self) -> None:
        # trace_id is the universal field injected by serialize_loop_event;
        # it must NOT appear inside any per-event WIRE_SCHEMA entry.
        assert set(BASE_FIELDS) == {"trace_id"}
        for wire_type, fields in WIRE_SCHEMA.items():
            assert "trace_id" not in fields, f"{wire_type} must not declare trace_id"

    @pytest.mark.parametrize(
        "event",
        WIRED_EVENT_INSTANCES,
        ids=[type(ev).__name__ for ev in WIRED_EVENT_INSTANCES],
    )
    def test_serializer_field_set_matches_registry(self, event: LoopEvent) -> None:
        payload = serialize_loop_event(event)
        assert payload is not None, f"{type(event).__name__} unexpectedly serialized to None"
        wire_type = payload["type"]
        assert wire_type in WIRE_SCHEMA, f"{wire_type} not in WIRE_SCHEMA"
        serializer_fields = set(payload["data"].keys()) - {"trace_id"}
        registry_fields = set(WIRE_SCHEMA[wire_type].keys())
        assert serializer_fields == registry_fields, (
            f"{type(event).__name__} → {wire_type}: serializer fields "
            f"{serializer_fields} != registry fields {registry_fields}"
        )

    def test_tool_call_executed_and_failed_share_wire_type(self) -> None:
        # Both Cat-2 events map to the single 'tool_call_result' frame.
        executed = serialize_loop_event(
            ToolCallExecuted(tool_call_id="c1", tool_name="t", duration_ms=1.0, result_content="ok")
        )
        failed = serialize_loop_event(
            ToolCallFailed(tool_call_id="c1", tool_name="t", error="boom")
        )
        assert executed is not None and failed is not None
        assert executed["type"] == "tool_call_result"
        assert failed["type"] == "tool_call_result"
        assert set(executed["data"]) == set(failed["data"])

    def test_all_wired_classes_cover_all_18_wire_types(self) -> None:
        # The representative instances must collectively hit every WIRE_SCHEMA
        # key (proves no registry entry lacks a serializer branch).
        produced = set()
        for event in WIRED_EVENT_INSTANCES:
            payload = serialize_loop_event(event)
            assert payload is not None
            produced.add(payload["type"])
        assert produced == set(WIRE_SCHEMA.keys())

    @pytest.mark.parametrize(
        "event",
        UNWIRED_EVENT_INSTANCES,
        ids=[type(ev).__name__ for ev in UNWIRED_EVENT_INSTANCES],
    )
    def test_unwired_events_raise_not_implemented(self, event: LoopEvent) -> None:
        with pytest.raises(NotImplementedError):
            serialize_loop_event(event)

    def test_thinking_serializes_to_none(self) -> None:
        # Thinking is intentionally skipped (LLMResponded carries the content).
        assert serialize_loop_event(Thinking(text="hello")) is None
