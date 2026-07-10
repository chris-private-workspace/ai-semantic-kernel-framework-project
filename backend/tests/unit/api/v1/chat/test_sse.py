"""
File: backend/tests/unit/api/v1/chat/test_sse.py
Purpose: Unit tests for SSE serializer (LoopEvent → wire format).
Category: tests
Scope: Phase 50 / Sprint 50.2 (Day 1.3)

Created: 2026-04-30
"""

from __future__ import annotations

import json
from uuid import uuid4

import pytest

from agent_harness._contracts import (
    ContextCompacted,
    ErrorRetried,
    LLMRequested,
    LLMResponded,
    LoopCompleted,
    LoopStarted,
    PromptBuilt,
    StateCheckpointed,
    Thinking,
    ToolCall,
    ToolCallExecuted,
    ToolCallFailed,
    ToolCallRequested,
    TripwireTriggered,
    TurnStarted,
)
from api.v1.chat.sse import format_sse_message, serialize_loop_event


class TestSerializeLoopEvent:
    def test_loop_started(self) -> None:
        sid = uuid4()
        ev = LoopStarted(session_id=sid)
        out = serialize_loop_event(ev)
        assert out["type"] == "loop_start"
        assert out["data"]["session_id"] == str(sid)
        assert "request_id" in out["data"]

    def test_loop_started_no_session(self) -> None:
        ev = LoopStarted()
        out = serialize_loop_event(ev)
        assert out["data"]["session_id"] is None

    def test_thinking_returns_none_skipped_in_day_2(self) -> None:
        """Day 2: Thinking → None; LLMResponded carries canonical llm_response."""
        ev = Thinking(text="hello world")
        out = serialize_loop_event(ev)
        assert out is None

    def test_turn_started(self) -> None:
        ev = TurnStarted(turn_num=2)
        out = serialize_loop_event(ev)
        assert out is not None
        assert out["type"] == "turn_start"
        assert out["data"]["turn_num"] == 2

    def test_llm_requested(self) -> None:
        ev = LLMRequested(model="gpt-4o", tokens_in=500)
        out = serialize_loop_event(ev)
        assert out is not None
        assert out["type"] == "llm_request"
        assert out["data"]["model"] == "gpt-4o"
        assert out["data"]["tokens_in"] == 500

    def test_llm_responded_with_tool_calls(self) -> None:
        tc = ToolCall(id="c1", name="echo_tool", arguments={"text": "X"})
        ev = LLMResponded(
            content="calling tool",
            tool_calls=(tc,),
            thinking="reasoning here",
        )
        out = serialize_loop_event(ev)
        assert out is not None
        assert out["type"] == "llm_response"
        assert out["data"]["content"] == "calling tool"
        assert out["data"]["thinking"] == "reasoning here"
        assert out["data"]["tool_calls"] == [
            {"id": "c1", "name": "echo_tool", "arguments": {"text": "X"}}
        ]
        # Sprint 57.66: cache field present, defaults to 0 when unset.
        assert out["data"]["cached_input_tokens"] == 0

    def test_llm_responded_cached_input_tokens(self) -> None:
        """Sprint 57.66 (A-5a+): llm_response carries 57.65 cached_input_tokens."""
        ev = LLMResponded(content="hi", cached_input_tokens=321)
        out = serialize_loop_event(ev)
        assert out is not None
        assert out["type"] == "llm_response"
        assert out["data"]["cached_input_tokens"] == 321
        # Sprint 57.108: per-call token actuals present, default to 0 when unset.
        assert out["data"]["input_tokens"] == 0
        assert out["data"]["output_tokens"] == 0

    def test_llm_responded_token_actuals(self) -> None:
        """Sprint 57.108: llm_response carries per-call input/output token actuals."""
        ev = LLMResponded(content="hi", input_tokens=1200, output_tokens=345)
        out = serialize_loop_event(ev)
        assert out is not None
        assert out["data"]["input_tokens"] == 1200
        assert out["data"]["output_tokens"] == 345

    def test_tool_call_failed(self) -> None:
        ev = ToolCallFailed(
            tool_call_id="c1",
            tool_name="broken_tool",
            error="timeout",
            error_taxonomy="failed_api",  # Sprint 57.164
        )
        out = serialize_loop_event(ev)
        assert out is not None
        assert out["type"] == "tool_call_result"
        assert out["data"]["is_error"] is True
        assert out["data"]["result"] == "timeout"
        # Sprint 57.164: the typed taxonomy flows to the wire on a failure.
        assert out["data"]["error_taxonomy"] == "failed_api"

    def test_tool_call_requested(self) -> None:
        ev = ToolCallRequested(
            tool_call_id="call_123",
            tool_name="echo_tool",
            arguments={"text": "X"},
        )
        out = serialize_loop_event(ev)
        assert out["type"] == "tool_call_request"
        assert out["data"]["tool_call_id"] == "call_123"
        assert out["data"]["tool_name"] == "echo_tool"
        assert out["data"]["args"] == {"text": "X"}

    def test_tool_call_executed(self) -> None:
        ev = ToolCallExecuted(
            tool_call_id="call_123",
            tool_name="echo_tool",
            duration_ms=1.25,
            result_content="X",
        )
        out = serialize_loop_event(ev)
        assert out is not None
        assert out["type"] == "tool_call_result"
        assert out["data"]["duration_ms"] == 1.25
        assert out["data"]["is_error"] is False
        assert out["data"]["result"] == "X"
        # Sprint 57.164: success has no taxonomy — always null (parity with the fail branch).
        assert out["data"]["error_taxonomy"] is None

    def test_loop_completed(self) -> None:
        ev = LoopCompleted(stop_reason="end_turn", total_turns=2)
        out = serialize_loop_event(ev)
        assert out["type"] == "loop_end"
        assert out["data"]["stop_reason"] == "end_turn"
        assert out["data"]["total_turns"] == 2
        # Sprint 57.66: cache fields present, default to 0 / 0.0 when unset.
        assert out["data"]["cached_input_tokens"] == 0
        assert out["data"]["cache_hit_rate"] == 0.0

    def test_loop_completed_cache_fields(self) -> None:
        """Sprint 57.66 (A-5a+): loop_end carries 57.65 cache fields when set."""
        ev = LoopCompleted(
            stop_reason="end_turn",
            total_turns=3,
            cached_input_tokens=512,
            cache_hit_rate=0.42,
        )
        out = serialize_loop_event(ev)
        assert out["type"] == "loop_end"
        assert out["data"]["cached_input_tokens"] == 512
        assert out["data"]["cache_hit_rate"] == 0.42

    def test_approval_requested(self) -> None:
        """Sprint 53.5 US-2: Cat 9 ESCALATE → ApprovalRequested → SSE."""
        from agent_harness._contracts import ApprovalRequested

        rid = uuid4()
        ev = ApprovalRequested(approval_request_id=rid, risk_level="HIGH")
        out = serialize_loop_event(ev)
        assert out is not None
        assert out["type"] == "approval_requested"
        assert out["data"]["approval_request_id"] == str(rid)
        assert out["data"]["risk_level"] == "HIGH"
        assert out["data"]["kind"] == ""  # Sprint 57.100: default kind on the wire
        # Sprint 57.108: tool context defaults on the wire (old-frame compatible).
        assert out["data"]["tool_name"] is None
        assert out["data"]["reason"] == ""

    def test_approval_requested_carries_kind(self) -> None:
        """Sprint 57.100: the pause kind rides the approval_requested wire."""
        from agent_harness._contracts import ApprovalRequested

        ev = ApprovalRequested(approval_request_id=uuid4(), risk_level="HIGH", kind="verification")
        out = serialize_loop_event(ev)
        assert out is not None
        assert out["data"]["kind"] == "verification"

    def test_approval_requested_carries_tool_context(self) -> None:
        """Sprint 57.108: the tool-escalate approval carries tool_name + reason."""
        from agent_harness._contracts import ApprovalRequested

        ev = ApprovalRequested(
            approval_request_id=uuid4(),
            risk_level="HIGH",
            kind="tool",
            tool_name="wire_transfer",
            reason="matched risky-action pattern",
        )
        out = serialize_loop_event(ev)
        assert out is not None
        assert out["data"]["tool_name"] == "wire_transfer"
        assert out["data"]["reason"] == "matched risky-action pattern"

    def test_message_injected(self) -> None:
        """Sprint 57.101 B1: MessageInjected → message_injected wire frame."""
        from agent_harness._contracts import MessageInjected

        ev = MessageInjected(text="also check the db pool")
        out = serialize_loop_event(ev)
        assert out is not None
        assert out["type"] == "message_injected"
        assert out["data"]["text"] == "also check the db pool"

    def test_approval_received_approved(self) -> None:
        """Sprint 53.5 US-2: wait_for_decision returns → ApprovalReceived → SSE."""
        from agent_harness._contracts import ApprovalReceived

        rid = uuid4()
        ev = ApprovalReceived(approval_request_id=rid, decision="APPROVED")
        out = serialize_loop_event(ev)
        assert out is not None
        assert out["type"] == "approval_received"
        assert out["data"]["approval_request_id"] == str(rid)
        assert out["data"]["decision"] == "APPROVED"

    def test_approval_received_rejected(self) -> None:
        from agent_harness._contracts import ApprovalReceived

        ev = ApprovalReceived(approval_request_id=uuid4(), decision="REJECTED")
        out = serialize_loop_event(ev)
        assert out is not None
        assert out["data"]["decision"] == "REJECTED"

    def test_guardrail_triggered_input_block(self) -> None:
        """Sprint 53.6 D2: Cat 9 Stage 1 input PII detection → GuardrailTriggered → SSE."""
        from agent_harness._contracts import GuardrailTriggered

        ev = GuardrailTriggered(
            guardrail_type="input",
            action="block",
            reason="PII detected: email pattern",
        )
        out = serialize_loop_event(ev)
        assert out is not None
        assert out["type"] == "guardrail_triggered"
        assert out["data"]["guardrail_type"] == "input"
        assert out["data"]["action"] == "block"
        assert out["data"]["reason"] == "PII detected: email pattern"

    def test_guardrail_triggered_output_sanitize(self) -> None:
        """Sprint 53.6 D2: Cat 9 Stage 2 output detection → GuardrailTriggered → SSE."""
        from agent_harness._contracts import GuardrailTriggered

        ev = GuardrailTriggered(
            guardrail_type="output",
            action="sanitize",
            reason="Jailbreak attempt: prompt injection",
        )
        out = serialize_loop_event(ev)
        assert out is not None
        assert out["type"] == "guardrail_triggered"
        assert out["data"]["guardrail_type"] == "output"
        assert out["data"]["action"] == "sanitize"

    def test_guardrail_triggered_tool_escalate_block(self) -> None:
        """Sprint 53.6 D2: Stage 3 reject/escalate/timeout → GuardrailTriggered(block)."""
        from agent_harness._contracts import GuardrailTriggered

        ev = GuardrailTriggered(
            guardrail_type="tool",
            action="block",
            reason="HITL rejected by reviewer",
        )
        out = serialize_loop_event(ev)
        assert out is not None
        assert out["type"] == "guardrail_triggered"
        assert out["data"]["guardrail_type"] == "tool"
        assert out["data"]["action"] == "block"
        assert "reviewer" in out["data"]["reason"]

    def test_subagent_spawned_serializes_to_subagent_spawned_frame(self) -> None:
        """Sprint 57.12 US-1: SubagentSpawned → 'subagent_spawned' SSE frame.

        Closes AD-Cat11-SSEEvents (54.2 carryover). Frontend SubagentTree (US-6)
        consumes via chatStore.mergeEvent (CONVENTION.md §7 3-edit checklist).
        """
        from agent_harness._contracts import SubagentSpawned

        sid = uuid4()
        parent = uuid4()
        ev = SubagentSpawned(
            subagent_id=sid,
            mode="fork",
            parent_session_id=parent,
        )
        out = serialize_loop_event(ev)
        assert out is not None
        assert out["type"] == "subagent_spawned"
        assert out["data"]["subagent_id"] == str(sid)
        assert out["data"]["mode"] == "fork"
        assert out["data"]["parent_session_id"] == str(parent)

    def test_subagent_completed_serializes_to_subagent_completed_frame(self) -> None:
        """Sprint 57.12 US-1: SubagentCompleted → 'subagent_completed' SSE frame.

        Per D1-005: uses 17.md §4 single-source fields only (subagent_id /
        summary / tokens_used). Status (running/success/error) is implicit
        for SubagentTree UI: Spawned event = running; Completed event = terminal.
        """
        from agent_harness._contracts import SubagentCompleted

        sid = uuid4()
        ev = SubagentCompleted(
            subagent_id=sid,
            summary="Subagent finished task X with result Y.",
            tokens_used=147,
        )
        out = serialize_loop_event(ev)
        assert out is not None
        assert out["type"] == "subagent_completed"
        assert out["data"]["subagent_id"] == str(sid)
        assert out["data"]["summary"] == "Subagent finished task X with result Y."
        assert out["data"]["tokens_used"] == 147

    def test_context_compacted(self) -> None:
        """Sprint 57.66 (A-5a+): Cat 4 ContextCompacted → 'context_compacted'."""
        ev = ContextCompacted(
            tokens_before=8000,
            tokens_after=3000,
            compaction_strategy="summarize",
            messages_compacted=12,
            duration_ms=4.5,
        )
        out = serialize_loop_event(ev)
        assert out is not None
        assert out["type"] == "context_compacted"
        assert out["data"]["tokens_before"] == 8000
        assert out["data"]["tokens_after"] == 3000
        assert out["data"]["compaction_strategy"] == "summarize"
        assert out["data"]["messages_compacted"] == 12
        assert out["data"]["duration_ms"] == 4.5

    def test_prompt_built(self) -> None:
        """Sprint 57.66 (A-5a+): Cat 5 PromptBuilt → 'prompt_built'.

        memory_layers_used must serialize as a JSON list of scope-key names
        (NOT memory content). Asserts no raw-content key leaks into the payload.
        """
        ev = PromptBuilt(
            messages_count=6,
            estimated_input_tokens=1200,
            cache_breakpoints_count=2,
            memory_layers_used=("session", "tenant"),
            position_strategy_used="lost_in_middle",
            duration_ms=2.3,
        )
        out = serialize_loop_event(ev)
        assert out is not None
        assert out["type"] == "prompt_built"
        assert out["data"]["messages_count"] == 6
        assert out["data"]["estimated_input_tokens"] == 1200
        assert out["data"]["cache_breakpoints_count"] == 2
        assert out["data"]["position_strategy_used"] == "lost_in_middle"
        assert out["data"]["duration_ms"] == 2.3
        # tuple → JSON list of scope-key strings (not memory content).
        assert out["data"]["memory_layers_used"] == ["session", "tenant"]
        assert isinstance(out["data"]["memory_layers_used"], list)
        # No raw memory-content key leaks — only the scope-name list is exposed.
        assert set(out["data"].keys()) == {
            "messages_count",
            "estimated_input_tokens",
            "cache_breakpoints_count",
            "memory_layers_used",
            "position_strategy_used",
            "duration_ms",
            "trace_id",
        }

    def test_state_checkpointed(self) -> None:
        """Sprint 57.66 (A-5a+): Cat 7 StateCheckpointed → 'state_checkpointed'."""
        ev = StateCheckpointed(version=7)
        out = serialize_loop_event(ev)
        assert out is not None
        assert out["type"] == "state_checkpointed"
        assert out["data"]["version"] == 7

    def test_tripwire_triggered(self) -> None:
        """Sprint 57.66 (A-5a+): Cat 9 TripwireTriggered → 'tripwire_triggered'."""
        ev = TripwireTriggered(violation_type="pii_leak", detail="ssn detected")
        out = serialize_loop_event(ev)
        assert out is not None
        assert out["type"] == "tripwire_triggered"
        assert out["data"]["violation_type"] == "pii_leak"
        assert out["data"]["detail"] == "ssn detected"

    def test_unsupported_event_raises_with_sprint_pointer(self) -> None:
        # Sprint 54.1 US-3: VerificationPassed/Failed are now wired.
        # Sprint 57.12 US-1: SubagentSpawned/SubagentCompleted are now wired.
        # Sprint 57.66 (A-5a+): ContextCompacted / PromptBuilt / StateCheckpointed
        # / TripwireTriggered are now wired.
        # Use ErrorRetried (Cat 8; still unwired) as a canonical "deferred event
        # type" — kept in sync as future sprints add owner branches.
        ev = ErrorRetried(attempt=1, error_class="TimeoutError", backoff_ms=250.0)
        with pytest.raises(NotImplementedError, match="Sprint 50.2"):
            serialize_loop_event(ev)


class TestFormatSseMessage:
    def test_basic_frame(self) -> None:
        frame = format_sse_message("loop_start", {"a": 1})
        assert frame.startswith(b"event: loop_start\n")
        assert b'data: {"a":1}\n\n' in frame

    def test_unicode_preserved(self) -> None:
        frame = format_sse_message("llm_response", {"content": "你好"})
        assert "你好".encode("utf-8") in frame

    def test_uuid_serializable(self) -> None:
        sid = uuid4()
        frame = format_sse_message("loop_start", {"session_id": sid})
        # UUID coerced to string by _jsonable
        body = frame.decode("utf-8")
        assert str(sid) in body
        # Verify it parses as JSON
        data_line = [line for line in body.split("\n") if line.startswith("data: ")][0]
        parsed = json.loads(data_line[len("data: ") :])
        assert parsed["session_id"] == str(sid)

    def test_prompt_built_round_trip_wire_frame(self) -> None:
        """Sprint 57.66 (A-5a+): a new diagnostic event round-trips to a wire frame."""
        ev = PromptBuilt(
            messages_count=4,
            estimated_input_tokens=900,
            memory_layers_used=("user", "session"),
            position_strategy_used="lost_in_middle",
        )
        payload = serialize_loop_event(ev)
        assert payload is not None
        frame = format_sse_message(payload["type"], payload["data"])
        body = frame.decode("utf-8")
        assert body.startswith("event: prompt_built\n")
        data_line = [line for line in body.split("\n") if line.startswith("data: ")][0]
        parsed = json.loads(data_line[len("data: ") :])
        assert parsed["messages_count"] == 4
        assert parsed["memory_layers_used"] == ["user", "session"]
        assert body.endswith("\n\n")

    def test_float_wire_fields_serialize_as_json_numbers(self) -> None:
        """FIX-025: float payload fields (cache_hit_rate / duration_ms) must wire
        as JSON numbers, not strings. Regression guard for the `_jsonable`
        UUID-fallback bug where `float.hex` existing made 0.5 serialize as "0.5".
        """
        ev = LoopCompleted(
            stop_reason="end_turn",
            total_turns=1,
            cached_input_tokens=256,
            cache_hit_rate=0.5,
        )
        payload = serialize_loop_event(ev)
        assert payload is not None
        frame = format_sse_message(payload["type"], payload["data"])
        data_line = [
            line for line in frame.decode("utf-8").split("\n") if line.startswith("data: ")
        ][0]
        parsed = json.loads(data_line[len("data: ") :])
        # JSON number, not the string "0.5".
        assert parsed["cache_hit_rate"] == 0.5
        assert isinstance(parsed["cache_hit_rate"], float)
        assert parsed["cached_input_tokens"] == 256
