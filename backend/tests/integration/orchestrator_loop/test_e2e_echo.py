"""
File: backend/tests/integration/orchestrator_loop/test_e2e_echo.py
Purpose: Sprint 50.1 acceptance e2e — "user asks echo X → loop replies X".
Category: Integration tests / Sprint 50.1 acceptance gate
Scope: Phase 50 / Sprint 50.1 (Day 4.1)

Description:
    The Sprint 50.1 acceptance criterion (per sprint-50-1-plan.md §Story 50.1-6):
        user message → AgentLoop.run() → MockChatClient yields tool_call →
        echo_tool execute → MockChatClient yields END_TURN → final answer.

    THIS test asserts deep semantics that complement Day 3 integration test:
        a) Full event sequence with ordering AND counts.
        b) ChatRequest progression — each chat() round receives the right
           messages list (user, assistant w/ tool_calls, tool result, ...).
        c) Final assistant content carries the echo result back to user.
        d) Loop terminates with END_TURN reason at expected turn count.

    Day 4.2 (test_observability_coverage) further verifies tracer / metric
    emission against this same scenario.

Created: 2026-04-30 (Sprint 50.1 Day 4.1)
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from adapters._testing.mock_clients import MockChatClient
from agent_harness._contracts import (
    ChatResponse,
    LoopCompleted,
    LoopEvent,
    LoopStarted,
    MemoryAccessed,
    SpanEnded,
    SpanStarted,
    StopReason,
    Thinking,
    ToolCall,
    ToolCallRequested,
)
from agent_harness.orchestrator_loop import AgentLoopImpl, TerminationReason
from agent_harness.output_parser import OutputParserImpl
from agent_harness.tools import make_echo_executor

# Sprint 57.75 (A-5c): the loop now interleaves diagnostic SpanStarted/SpanEnded
# + MemoryAccessed events into the stream. These acceptance tests assert the
# PUBLIC event sequence, so filter the diagnostic events out first (their emit
# order + nesting are covered in test_observability_coverage.py).
_DIAGNOSTIC_EVENTS = (SpanStarted, SpanEnded, MemoryAccessed)


def _public(events: list[LoopEvent]) -> list[LoopEvent]:
    return [e for e in events if not isinstance(e, _DIAGNOSTIC_EVENTS)]


@pytest.mark.asyncio
async def test_e2e_echo_acceptance() -> None:
    """Sprint 50.1 acceptance e2e: 'echo hello' goes through TAO loop and
    surfaces back as 'echo returned: hello' in the final assistant turn."""
    registry, executor = make_echo_executor()
    chat = MockChatClient(
        responses=[
            # Turn 1: assistant decides to call echo_tool
            ChatResponse(
                model="m",
                content="I'll call the echo tool.",
                tool_calls=[
                    ToolCall(
                        id="call_1",
                        name="echo_tool",
                        arguments={"text": "hello"},
                    )
                ],
                stop_reason=StopReason.TOOL_USE,
            ),
            # Turn 2: assistant uses tool result and ends
            ChatResponse(
                model="m",
                content="Echo returned: hello",
                stop_reason=StopReason.END_TURN,
            ),
        ]
    )
    loop = AgentLoopImpl(
        chat_client=chat,
        output_parser=OutputParserImpl(),
        tool_executor=executor,
        tool_registry=registry,
        system_prompt="You are an echo assistant.",
        max_turns=5,
        token_budget=10_000,
    )

    sid = uuid4()
    events = [ev async for ev in loop.run(session_id=sid, user_input="please echo hello")]

    # === Assertion (a): full event sequence ===================================
    type_seq = [type(e).__name__ for e in _public(events)]
    # Sprint 50.2 Day 2.4: per-turn events expanded with TurnStarted /
    # LLMRequested / LLMResponded; ToolCallExecuted yielded after success.
    assert type_seq == [
        "LoopStarted",
        # --- turn 1 ---
        "TurnStarted",
        "LLMRequested",
        "LLMResponded",  # canonical SSE llm_response (50.2)
        "Thinking",  # backward compat (50.1 tests still rely)
        "ToolCallRequested",
        "ToolCallExecuted",
        # --- turn 2 ---
        "TurnStarted",
        "LLMRequested",
        "LLMResponded",
        "Thinking",
        "LoopCompleted",
    ]

    # LoopStarted carries session_id
    started = _public(events)[0]
    assert isinstance(started, LoopStarted)
    assert started.session_id == sid

    # ToolCallRequested carries the right tool_call_id + arguments
    tcr = next(e for e in events if isinstance(e, ToolCallRequested))
    assert tcr.tool_call_id == "call_1"
    assert tcr.tool_name == "echo_tool"
    assert tcr.arguments == {"text": "hello"}

    # Two Thinking events with distinct text
    thinking_events = [e for e in events if isinstance(e, Thinking)]
    assert len(thinking_events) == 2
    assert thinking_events[0].text == "I'll call the echo tool."
    assert thinking_events[1].text == "Echo returned: hello"

    # LoopCompleted: END_TURN, total_turns = 1 (one TOOL_USE turn before END_TURN)
    completed = _public(events)[-1]
    assert isinstance(completed, LoopCompleted)
    assert completed.stop_reason == TerminationReason.END_TURN.value
    assert completed.total_turns == 1

    # === Assertion (b): ChatRequest progression ==============================
    # MockChatClient was called twice; last_request is turn 2's input.
    assert chat.chat_call_count == 2
    final_messages = chat.last_request.messages  # type: ignore[union-attr]

    # Expected progression on turn 2 input:
    #   [system, user, assistant(tool_calls=[call_1]), tool(call_1, "hello")]
    assert [m.role for m in final_messages] == [
        "system",
        "user",
        "assistant",
        "tool",
    ]

    sys_msg, user_msg, asst_msg, tool_msg = final_messages
    assert sys_msg.content == "You are an echo assistant."
    assert user_msg.content == "please echo hello"
    assert asst_msg.tool_calls is not None and len(asst_msg.tool_calls) == 1
    assert asst_msg.tool_calls[0].id == "call_1"
    assert tool_msg.tool_call_id == "call_1"
    assert tool_msg.content == "hello"  # echo_tool returned "hello"

    # === Assertion (c): tool was actually executed once =====================
    # (Indirectly: turn 2 saw the tool message; if executor failed, content
    # would not equal "hello".)


@pytest.mark.asyncio
async def test_e2e_zero_turn_immediate_final() -> None:
    """If the very first ChatResponse is END_TURN with no tool_calls, loop
    completes in 0 tool turns. Validates the FINAL fast-path."""
    registry, executor = make_echo_executor()
    loop = AgentLoopImpl(
        chat_client=MockChatClient(
            responses=[
                ChatResponse(
                    model="m",
                    content="Hello, world.",
                    stop_reason=StopReason.END_TURN,
                ),
            ]
        ),
        output_parser=OutputParserImpl(),
        tool_executor=executor,
        tool_registry=registry,
    )
    events = [ev async for ev in loop.run(session_id=uuid4(), user_input="hi")]
    # Sprint 50.2 Day 2.4: per-turn events expanded.
    assert [type(e).__name__ for e in _public(events)] == [
        "LoopStarted",
        "TurnStarted",
        "LLMRequested",
        "LLMResponded",
        "Thinking",
        "LoopCompleted",
    ]
    completed = _public(events)[-1]
    assert isinstance(completed, LoopCompleted)
    assert completed.total_turns == 0
    assert completed.stop_reason == TerminationReason.END_TURN.value
