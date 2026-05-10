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
    LLMRequested,
    LLMResponded,
    LoopCompleted,
    LoopStarted,
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

    def test_tool_call_failed(self) -> None:
        ev = ToolCallFailed(
            tool_call_id="c1",
            tool_name="broken_tool",
            error="timeout",
        )
        out = serialize_loop_event(ev)
        assert out is not None
        assert out["type"] == "tool_call_result"
        assert out["data"]["is_error"] is True
        assert out["data"]["result"] == "timeout"

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

    def test_loop_completed(self) -> None:
        ev = LoopCompleted(stop_reason="end_turn", total_turns=2)
        out = serialize_loop_event(ev)
        assert out["type"] == "loop_end"
        assert out["data"]["stop_reason"] == "end_turn"
        assert out["data"]["total_turns"] == 2

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

    def test_unsupported_event_raises_with_sprint_pointer(self) -> None:
        # Sprint 54.1 US-3: VerificationPassed/Failed are now wired.
        # Sprint 57.12 US-1: SubagentSpawned/SubagentCompleted are now wired.
        # Use TripwireTriggered (Cat 9; still unwired in 50.2 scope) as a
        # canonical "deferred event type" — kept in sync as future sprints
        # add owner branches.
        ev = TripwireTriggered(violation_type="pii_leak", detail="ssn detected")
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
