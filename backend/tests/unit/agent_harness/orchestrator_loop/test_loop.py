"""
File: backend/tests/unit/agent_harness/orchestrator_loop/test_loop.py
Purpose: Unit tests for AgentLoopImpl — the TAO/ReAct main loop.
Category: Tests / 範疇 1
Scope: Phase 50 / Sprint 50.1 (Day 2.2)

Description:
    Validates Sprint 50.1 acceptance criteria:
    - while-true main loop driven by StopReason / 4 terminators (AP-1 cure)
    - tool results fed back as Message(role="tool", tool_call_id=...)
    - cancellation safety (asyncio.CancelledError → LoopCompleted(cancelled))
    - HANDOFF path stub for Cat 11 (Phase 54.2)

Created: 2026-04-30
"""

from __future__ import annotations

import asyncio
from typing import AsyncIterator
from uuid import uuid4

import pytest

from adapters._testing.mock_clients import MockChatClient
from agent_harness._contracts import (
    ChatResponse,
    ExecutionContext,
    LoopCompleted,
    LoopEvent,
    LoopStarted,
    MemoryAccessed,
    SpanEnded,
    SpanStarted,
    StopReason,
    TokenUsage,
    ToolCall,
    ToolCallRequested,
    ToolResult,
    ToolSpec,
    TraceContext,
)
from agent_harness.orchestrator_loop import AgentLoopImpl, TerminationReason
from agent_harness.output_parser import OutputParserImpl
from agent_harness.tools._abc import ToolExecutor, ToolRegistry

# Sprint 57.75 (A-5c): the loop now also yields diagnostic SpanStarted/SpanEnded
# + MemoryAccessed events interleaved with the public event stream. These
# sequence assertions test the PUBLIC contract, so filter the diagnostic events
# out first (their own emit order + nesting are covered in
# test_observability_coverage.py + test_loop_with_prompt_builder.py).
_DIAGNOSTIC_EVENTS = (SpanStarted, SpanEnded, MemoryAccessed)


def _public(events: list[LoopEvent]) -> list[LoopEvent]:
    """Drop Sprint 57.75 diagnostic span/memory events from a yielded stream."""
    return [e for e in events if not isinstance(e, _DIAGNOSTIC_EVENTS)]


# === Test fixtures ===========================================================


class _StubRegistry(ToolRegistry):
    """Empty in-memory registry — list() returns []."""

    def __init__(self, specs: list[ToolSpec] | None = None) -> None:
        self._specs = list(specs or [])

    def register(self, spec: ToolSpec) -> None:
        self._specs.append(spec)

    def get(self, name: str) -> ToolSpec | None:
        for s in self._specs:
            if s.name == name:
                return s
        return None

    def list(self) -> list[ToolSpec]:
        return list(self._specs)


class _EchoExecutor(ToolExecutor):
    """Synchronous tool executor: echoes tc.arguments['text']."""

    def __init__(self) -> None:
        self.executed: list[ToolCall] = []
        # Sprint 52.5 P0 #18: capture last context for test assertions.
        self.last_context: ExecutionContext | None = None

    async def execute(
        self,
        call: ToolCall,
        *,
        trace_context: TraceContext | None = None,
        context: ExecutionContext | None = None,
    ) -> ToolResult:
        self.executed.append(call)
        self.last_context = context
        text = str(call.arguments.get("text", ""))
        return ToolResult(
            tool_call_id=call.id,
            tool_name=call.name,
            success=True,
            content=text,
        )

    async def execute_batch(
        self,
        calls: list[ToolCall],
        *,
        trace_context: TraceContext | None = None,
        context: ExecutionContext | None = None,
    ) -> list[ToolResult]:
        return [await self.execute(c, trace_context=trace_context, context=context) for c in calls]


class _SlowExecutor(ToolExecutor):
    """Tool executor that sleeps — used for cancellation tests."""

    async def execute(
        self,
        call: ToolCall,
        *,
        trace_context: TraceContext | None = None,
        context: ExecutionContext | None = None,
    ) -> ToolResult:
        await asyncio.sleep(10)
        return ToolResult(tool_call_id=call.id, tool_name=call.name, success=True, content="")

    async def execute_batch(
        self,
        calls: list[ToolCall],
        *,
        trace_context: TraceContext | None = None,
        context: ExecutionContext | None = None,
    ) -> list[ToolResult]:
        return [await self.execute(c, trace_context=trace_context, context=context) for c in calls]


def _make_loop(
    *,
    chat_responses: list[ChatResponse],
    executor: ToolExecutor | None = None,
    max_turns: int = 50,
    token_budget: int = 100_000,
) -> AgentLoopImpl:
    return AgentLoopImpl(
        chat_client=MockChatClient(responses=chat_responses),
        output_parser=OutputParserImpl(),
        tool_executor=executor or _EchoExecutor(),
        tool_registry=_StubRegistry(),
        system_prompt="you are a test agent",
        max_turns=max_turns,
        token_budget=token_budget,
    )


async def _collect(it: AsyncIterator) -> list:
    return [ev async for ev in it]


# === Tests ===================================================================


@pytest.mark.asyncio
async def test_single_turn_final_end_turn() -> None:
    """No tool_calls + END_TURN → LoopStarted, Thinking, LoopCompleted(end_turn)."""
    loop = _make_loop(
        chat_responses=[
            ChatResponse(model="m", content="Hello!", stop_reason=StopReason.END_TURN),
        ],
    )
    events = await _collect(loop.run(session_id=uuid4(), user_input="hi"))
    types = [type(e).__name__ for e in _public(events)]
    # Sprint 50.2 Day 2.4: per-turn events expanded with TurnStarted /
    # LLMRequested / LLMResponded. Thinking event preserved for backward compat.
    assert types == [
        "LoopStarted",
        "TurnStarted",
        "LLMRequested",
        "LLMResponded",
        "Thinking",
        "LoopCompleted",
    ]
    completed = _public(events)[-1]
    assert isinstance(completed, LoopCompleted)
    assert completed.stop_reason == TerminationReason.END_TURN.value
    assert completed.total_turns == 0


@pytest.mark.asyncio
async def test_multi_turn_tool_use_feedback() -> None:
    """Turn 1 emits tool_call, Loop appends Message(role='tool'),
    Turn 2 receives that message and answers FINAL.

    Validates AP-1 cure: tool result IS fed back as a Message before next chat()."""
    tc = ToolCall(id="c1", name="echo_tool", arguments={"text": "world"})
    executor = _EchoExecutor()
    chat = MockChatClient(
        responses=[
            ChatResponse(
                model="m",
                content="calling tool",
                tool_calls=[tc],
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
        tool_registry=_StubRegistry(),
        system_prompt="you echo",
    )
    events = await _collect(loop.run(session_id=uuid4(), user_input="echo world"))
    types = [type(e).__name__ for e in _public(events)]
    # Sprint 50.2 Day 2.4: per-turn events expanded; ToolCallExecuted yielded
    # by Loop after tool_executor.execute() success (Cat 2-owned event).
    assert types == [
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
    assert executor.executed == [tc]
    # Turn 2 must have seen the tool message in its input
    assert chat.last_request is not None
    last_msgs = chat.last_request.messages
    tool_msgs = [m for m in last_msgs if m.role == "tool"]
    assert len(tool_msgs) == 1
    assert tool_msgs[0].tool_call_id == "c1"
    assert tool_msgs[0].content == "world"
    completed = _public(events)[-1]
    assert isinstance(completed, LoopCompleted)
    assert completed.stop_reason == TerminationReason.END_TURN.value
    assert completed.total_turns == 1  # 1 tool turn before END_TURN


@pytest.mark.asyncio
async def test_max_turns_terminates() -> None:
    """If LLM keeps emitting tool_use forever, max_turns=2 stops the loop."""
    tc = ToolCall(id="c1", name="echo_tool", arguments={"text": "x"})

    def _tool_use_resp() -> ChatResponse:
        return ChatResponse(
            model="m",
            content="more tools",
            tool_calls=[tc],
            stop_reason=StopReason.TOOL_USE,
        )

    loop = _make_loop(
        chat_responses=[_tool_use_resp() for _ in range(5)],
        max_turns=2,
    )
    events = await _collect(loop.run(session_id=uuid4(), user_input="loop"))
    completed = _public(events)[-1]
    assert isinstance(completed, LoopCompleted)
    assert completed.stop_reason == TerminationReason.MAX_TURNS.value
    assert completed.total_turns == 2


@pytest.mark.asyncio
async def test_token_budget_terminates() -> None:
    """Once tokens_used >= budget, loop exits with token_budget reason."""
    resp = ChatResponse(
        model="m",
        content="thinking",
        tool_calls=[ToolCall(id="c1", name="echo_tool", arguments={})],
        stop_reason=StopReason.TOOL_USE,
        usage=TokenUsage(prompt_tokens=10, completion_tokens=10, total_tokens=20),
    )
    loop = _make_loop(
        chat_responses=[resp, resp, resp],
        token_budget=15,  # 1st turn uses 20 tokens → exceeds
    )
    events = await _collect(loop.run(session_id=uuid4(), user_input="x"))
    completed = _public(events)[-1]
    assert isinstance(completed, LoopCompleted)
    assert completed.stop_reason == TerminationReason.TOKEN_BUDGET.value


@pytest.mark.asyncio
async def test_cancellation_during_tool_yields_cancelled() -> None:
    """Cancel mid-tool → LoopCompleted(cancelled) + CancelledError propagates."""
    tc = ToolCall(id="c1", name="slow", arguments={})
    loop = AgentLoopImpl(
        chat_client=MockChatClient(
            responses=[
                ChatResponse(
                    model="m",
                    content="calling slow",
                    tool_calls=[tc],
                    stop_reason=StopReason.TOOL_USE,
                ),
            ]
        ),
        output_parser=OutputParserImpl(),
        tool_executor=_SlowExecutor(),
        tool_registry=_StubRegistry(),
    )

    async def consume() -> list:
        return await _collect(loop.run(session_id=uuid4(), user_input="go"))

    task = asyncio.create_task(consume())
    await asyncio.sleep(0.05)  # let the loop reach the slow execute
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


@pytest.mark.asyncio
async def test_handoff_path_yields_handoff_stop_reason() -> None:
    """HANDOFF detected → LoopCompleted(handoff) carrying target_agent + reason.

    Sprint 57.68 A-3b: the loop swaps the old HANDOFF_NOT_IMPLEMENTED dead-end
    for a real `handoff` stop_reason carrying the parsed control-transfer intent
    (the platform layer boots the child session post-loop).
    """
    handoff_call = ToolCall(
        id="h1",
        name="handoff",
        arguments={"target_agent": "specialist", "reason": "needs expert"},
    )
    loop = _make_loop(
        chat_responses=[
            ChatResponse(
                model="m",
                content="handing off",
                tool_calls=[handoff_call],
                stop_reason=StopReason.TOOL_USE,
            ),
        ],
    )
    events = await _collect(loop.run(session_id=uuid4(), user_input="x"))
    completed = _public(events)[-1]
    assert isinstance(completed, LoopCompleted)
    assert completed.stop_reason == TerminationReason.HANDOFF.value
    assert completed.stop_reason == "handoff"
    assert completed.handoff_target == "specialist"
    assert completed.handoff_reason == "needs expert"
    # Verify NO ToolCallRequested was emitted (HANDOFF short-circuits before
    # the tool_call dispatch loop).
    assert not any(isinstance(e, ToolCallRequested) for e in events)


@pytest.mark.asyncio
async def test_first_event_is_loop_started() -> None:
    """Loop ALWAYS starts with LoopStarted carrying session_id."""
    sid = uuid4()
    loop = _make_loop(
        chat_responses=[
            ChatResponse(model="m", content="ok", stop_reason=StopReason.END_TURN),
        ],
    )
    events = await _collect(loop.run(session_id=sid, user_input="hi"))
    first = events[0]
    assert isinstance(first, LoopStarted)
    assert first.session_id == sid
