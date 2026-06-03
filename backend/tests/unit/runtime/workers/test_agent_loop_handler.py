"""
File: backend/tests/unit/runtime/workers/test_agent_loop_handler.py
Purpose: Unit tests for execute_loop_with_sse + build_agent_loop_handler (Sprint 50.2 Day 2.5).
Category: tests
Scope: Phase 50 / Sprint 50.2 (Day 2.5)

Created: 2026-04-30
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from adapters._testing.mock_clients import MockChatClient
from agent_harness._contracts import (
    ChatResponse,
    LLMResponded,
    LoopCompleted,
    LoopEvent,
    StopReason,
    ToolCall,
)
from agent_harness.orchestrator_loop import AgentLoopImpl
from agent_harness.output_parser import OutputParserImpl
from agent_harness.tools import make_echo_executor
from runtime.workers import (
    TaskEnvelope,
    build_agent_loop_handler,
    execute_loop_with_sse,
)


def _make_echo_loop(message: str) -> AgentLoopImpl:
    registry, executor = make_echo_executor()
    parser = OutputParserImpl()
    chat = MockChatClient(
        responses=[
            ChatResponse(
                model="m",
                content="",
                tool_calls=[ToolCall(id="c1", name="echo_tool", arguments={"text": message})],
                stop_reason=StopReason.TOOL_USE,
            ),
            ChatResponse(model="m", content=message, stop_reason=StopReason.END_TURN),
        ]
    )
    return AgentLoopImpl(
        chat_client=chat,
        output_parser=parser,
        tool_executor=executor,
        tool_registry=registry,
        max_turns=4,
    )


@pytest.mark.asyncio
async def test_execute_loop_with_sse_dispatches_each_event() -> None:
    collected: list[LoopEvent] = []

    async def emit(ev: LoopEvent) -> None:
        collected.append(ev)

    loop = _make_echo_loop("zebra")
    summary = await execute_loop_with_sse(
        loop=loop,
        session_id=uuid4(),
        user_input="echo zebra",
        sse_emit=emit,
    )
    # Sprint 57.75 (A-5c): the loop now interleaves diagnostic SpanStarted/
    # SpanEnded + MemoryAccessed events; assert the PUBLIC event contract.
    _DIAGNOSTIC = {"SpanStarted", "SpanEnded", "MemoryAccessed"}
    type_names = [type(e).__name__ for e in collected]
    public_names = [n for n in type_names if n not in _DIAGNOSTIC]
    assert "LoopStarted" == public_names[0]
    assert "LoopCompleted" == public_names[-1]
    assert "ToolCallExecuted" in type_names
    assert "LLMResponded" in type_names

    assert summary["status"] == "completed"
    assert summary["total_turns"] >= 1
    assert summary["final_content"] == "zebra"


@pytest.mark.asyncio
async def test_build_agent_loop_handler_runs_through_envelope() -> None:
    collected: list[LoopEvent] = []

    async def emit(ev: LoopEvent) -> None:
        collected.append(ev)

    # Wire the handler with the same components an in-process API would use.
    registry, executor = make_echo_executor()
    parser = OutputParserImpl()
    chat = MockChatClient(
        responses=[
            ChatResponse(
                model="m",
                content="",
                tool_calls=[ToolCall(id="c1", name="echo_tool", arguments={"text": "X"})],
                stop_reason=StopReason.TOOL_USE,
            ),
            ChatResponse(model="m", content="X", stop_reason=StopReason.END_TURN),
        ]
    )
    handler = build_agent_loop_handler(
        chat_client=chat,
        tool_registry=registry,
        tool_executor=executor,
        output_parser=parser,
        sse_emit=emit,
        max_turns=4,
    )

    envelope = TaskEnvelope.new(
        tenant_id="tenant-a",
        user_id="user-a",
        payload={"message": "echo X"},
        trace_id="trace-1",
    )
    summary = await handler(envelope)
    assert summary["status"] == "completed"
    assert summary["final_content"] == "X"
    # SSE callback called for the event stream
    assert any(isinstance(e, LLMResponded) for e in collected)
    assert any(isinstance(e, LoopCompleted) for e in collected)


@pytest.mark.asyncio
async def test_build_agent_loop_handler_non_uuid_task_id_falls_back() -> None:
    """task_id is a free-form string per TaskEnvelope contract; handler coerces."""
    received: list[LoopEvent] = []

    async def emit(ev: LoopEvent) -> None:
        received.append(ev)

    registry, executor = make_echo_executor()
    parser = OutputParserImpl()
    chat = MockChatClient(
        responses=[ChatResponse(model="m", content="ok", stop_reason=StopReason.END_TURN)]
    )
    handler = build_agent_loop_handler(
        chat_client=chat,
        tool_registry=registry,
        tool_executor=executor,
        output_parser=parser,
        sse_emit=emit,
        max_turns=2,
    )
    envelope = TaskEnvelope(
        task_id="not-a-uuid",  # legal per TaskEnvelope schema (str)
        tenant_id="t",
        user_id=None,
        payload={"message": "hi"},
        trace_id="trace-1",
    )
    summary = await handler(envelope)
    assert summary["status"] == "completed"
    # No exception raised → fallback UUID coercion worked.
