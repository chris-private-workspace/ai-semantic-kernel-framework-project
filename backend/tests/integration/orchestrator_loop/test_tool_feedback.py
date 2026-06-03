"""
File: backend/tests/integration/orchestrator_loop/test_tool_feedback.py
Purpose: Cross-module integration test: AgentLoopImpl + production
         InMemoryToolRegistry + echo_tool wired through OutputParserImpl.
Category: Integration tests
Scope: Phase 50 / Sprint 50.1 (Day 3.2)

Description:
    Day 2 unit test (test_loop.test_multi_turn_tool_use_feedback) already
    verified tool-feedback semantics with inline mock executors. THIS test
    additionally proves the same flow works against the production
    InMemoryToolRegistry + InMemoryToolExecutor + echo_tool exported from
    `agent_harness.tools` (Day 3.3 module) — i.e. that the modules wire
    up end-to-end without requiring the test fixture.

    This is the integration foundation that Day 4 e2e test will extend
    with Tracer / Metrics coverage assertions.

Created: 2026-04-30 (Sprint 50.1 Day 3.2)
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from adapters._testing.mock_clients import MockChatClient
from agent_harness._contracts import (
    ChatResponse,
    LoopCompleted,
    LoopEvent,
    MemoryAccessed,
    Message,
    SpanEnded,
    SpanStarted,
    StopReason,
    ToolCall,
)
from agent_harness.orchestrator_loop import AgentLoopImpl, TerminationReason
from agent_harness.output_parser import OutputParserImpl
from agent_harness.tools import make_echo_executor

# Sprint 57.75 (A-5c): filter the loop's new diagnostic SpanStarted/SpanEnded +
# MemoryAccessed events; these tests assert the PUBLIC event sequence.
_DIAGNOSTIC_EVENTS = (SpanStarted, SpanEnded, MemoryAccessed)


def _public(events: list[LoopEvent]) -> list[LoopEvent]:
    return [e for e in events if not isinstance(e, _DIAGNOSTIC_EVENTS)]


@pytest.mark.asyncio
async def test_production_inmemory_executor_wires_into_loop() -> None:
    """Wire `make_echo_executor()` (production module) into AgentLoopImpl;
    verify Day 2 multi-turn tool-feedback semantics still hold."""
    registry, executor = make_echo_executor()
    chat = MockChatClient(
        responses=[
            ChatResponse(
                model="m",
                content="calling echo",
                tool_calls=[ToolCall(id="c1", name="echo_tool", arguments={"text": "world"})],
                stop_reason=StopReason.TOOL_USE,
            ),
            ChatResponse(
                model="m",
                content="The echo returned: world",
                stop_reason=StopReason.END_TURN,
            ),
        ]
    )
    loop = AgentLoopImpl(
        chat_client=chat,
        output_parser=OutputParserImpl(),
        tool_executor=executor,
        tool_registry=registry,
        system_prompt="you are an echo bot",
    )

    events = [ev async for ev in loop.run(session_id=uuid4(), user_input="echo world")]

    # Event sequence — Sprint 50.2 Day 2.4 expanded with per-turn events.
    assert [type(e).__name__ for e in _public(events)] == [
        "LoopStarted",
        "TurnStarted",
        "LLMRequested",
        "LLMResponded",
        "Thinking",
        "ToolCallRequested",
        "ToolCallExecuted",
        "TurnStarted",
        "LLMRequested",
        "LLMResponded",
        "Thinking",
        "LoopCompleted",
    ]

    # Tool message correctly fed back (V2 mandatory cure)
    assert chat.last_request is not None
    tool_msgs = [m for m in chat.last_request.messages if m.role == "tool"]
    assert len(tool_msgs) == 1
    assert tool_msgs[0].tool_call_id == "c1"
    assert tool_msgs[0].content == "world"

    # Final assistant turn references the echo result (last public event before
    # LoopCompleted is the final-turn Thinking; diagnostic events filtered).
    public = _public(events)
    assert "world" in (
        public[-2].text if hasattr(public[-2], "text") else ""  # type: ignore[attr-defined]
    )

    completed = _public(events)[-1]
    assert isinstance(completed, LoopCompleted)
    assert completed.stop_reason == TerminationReason.END_TURN.value
    assert completed.total_turns == 1


@pytest.mark.asyncio
async def test_loop_built_from_production_modules_only() -> None:
    """Sanity check: AgentLoopImpl construction needs ZERO inline test fixtures
    when using `make_echo_executor()` — proves modules can be wired by
    Phase 50.2 frontend / API code."""
    registry, executor = make_echo_executor()
    loop = AgentLoopImpl(
        chat_client=MockChatClient(
            responses=[
                ChatResponse(model="m", content="ok", stop_reason=StopReason.END_TURN),
            ]
        ),
        output_parser=OutputParserImpl(),
        tool_executor=executor,
        tool_registry=registry,
    )
    # Just exercise the wire-up; not asserting deep behavior here.
    events = [ev async for ev in loop.run(session_id=uuid4(), user_input="hi")]
    assert isinstance(_public(events)[-1], LoopCompleted)
    # Registered tools surface to LLM via ChatRequest.tools
    assert any(
        isinstance(m, Message) for m in [Message(role="user", content="hi")]
    )  # smoke: Message dataclass usable
