"""
File: backend/tests/unit/agent_harness/subagent/test_subagent_child_turnstream.py
Purpose: Unit tests — ForkExecutor forwards the child loop's TAO subset wrapped in
    SubagentChildEvent (Sprint 57.96 Cat 11 Scope B), tagged with subagent_id;
    non-TAO events are NOT forwarded; final-answer/token extraction is preserved.
    Plus the wrapper SSE serialize round-trip (flatten + skip cases).
Category: Tests / 範疇 11 (Subagent Orchestration) / Cat 12 (Observability)
Scope: Sprint 57.96

Created: 2026-06-09 (Sprint 57.96)

Related:
    - subagent/modes/fork.py — ForkExecutor (SUT; forwards TAO subset)
    - _contracts/events.py — SubagentChildEvent wrapper
    - api/v1/chat/sse.py — serialize_loop_event subagent_child branch
"""

from __future__ import annotations

from typing import AsyncIterator, Callable
from uuid import uuid4

import pytest

from agent_harness._contracts import (
    LLMRequested,
    LLMResponded,
    LoopCompleted,
    LoopEvent,
    SubagentBudget,
    SubagentChildEvent,
    Thinking,
    ToolCallExecuted,
    ToolCallRequested,
    TurnStarted,
)
from agent_harness.subagent.modes.fork import ForkExecutor
from api.v1.chat.sse import serialize_loop_event


class _ScriptedChildLoop:
    """A fake child AgentLoop that yields a fixed event sequence (no real LLM)."""

    def __init__(self, events: list[LoopEvent]) -> None:
        self._events = events

    async def run(  # noqa: D401 — async generator mirroring AgentLoop.run
        self,
        *,
        session_id: object = None,
        user_input: str = "",
        trace_context: object = None,
    ) -> AsyncIterator[LoopEvent]:
        for ev in self._events:
            yield ev


class _RecordingEmitter:
    def __init__(self) -> None:
        self.events: list[LoopEvent] = []

    async def __call__(self, event: LoopEvent) -> None:
        self.events.append(event)


def _factory_yielding(events: list[LoopEvent]) -> Callable[[SubagentBudget], _ScriptedChildLoop]:
    def factory(budget: SubagentBudget) -> _ScriptedChildLoop:
        return _ScriptedChildLoop(events)

    return factory


@pytest.mark.asyncio
async def test_forwards_tao_subset_tagged_with_subagent_id() -> None:
    """ForkExecutor forwards ONLY the TAO subset, each wrapped + tagged with subagent_id."""
    sid = uuid4()
    child_events: list[LoopEvent] = [
        TurnStarted(turn_num=1),
        LLMRequested(model="m", tokens_in=5),  # NOT in TAO subset → dropped
        LLMResponded(content="child says hi"),
        ToolCallRequested(tool_call_id="c1", tool_name="echo", arguments={"text": "x"}),
        ToolCallExecuted(tool_call_id="c1", tool_name="echo", duration_ms=1.0, result_content="x"),
        LoopCompleted(stop_reason="end_turn", total_turns=1, total_tokens=42),  # NOT forwarded
    ]
    emitter = _RecordingEmitter()
    executor = ForkExecutor(
        child_loop_factory=_factory_yielding(child_events),  # type: ignore[arg-type]
        event_emitter=emitter,
    )
    result = await executor.execute(subagent_id=sid, task="t", budget=SubagentBudget())

    # Final-answer + token extraction preserved (unchanged 57.94 behavior).
    assert result.success is True
    assert "child says hi" in result.summary
    assert result.tokens_used == 42

    # Only the TAO subset forwarded; each is a SubagentChildEvent tagged with sid.
    forwarded = emitter.events
    assert all(isinstance(e, SubagentChildEvent) for e in forwarded)
    assert all(isinstance(e, SubagentChildEvent) and e.subagent_id == sid for e in forwarded)
    inner_types = [type(e.inner).__name__ for e in forwarded if isinstance(e, SubagentChildEvent)]
    # LLMRequested + LoopCompleted excluded by the filter.
    assert inner_types == ["TurnStarted", "LLMResponded", "ToolCallRequested", "ToolCallExecuted"]


@pytest.mark.asyncio
async def test_no_emitter_no_forwarding_byte_identical_result() -> None:
    """Without an emitter (non-chat paths / 57.94 baseline) there is no forwarding."""
    sid = uuid4()
    child_events: list[LoopEvent] = [
        TurnStarted(turn_num=1),
        LLMResponded(content="hi"),
        LoopCompleted(total_tokens=7),
    ]
    executor = ForkExecutor(
        child_loop_factory=_factory_yielding(child_events),  # type: ignore[arg-type]
    )
    result = await executor.execute(subagent_id=sid, task="t", budget=SubagentBudget())
    # Behaviour identical to 57.94: success + summary + tokens, no forwarding side-channel.
    assert result.success is True
    assert "hi" in result.summary
    assert result.tokens_used == 7


def test_wrapper_serialize_round_trip() -> None:
    """serialize_loop_event(SubagentChildEvent) → flattened {subagent_id, inner_type, inner}."""
    sid = uuid4()
    wrapped = SubagentChildEvent(subagent_id=sid, inner=LLMResponded(content="hi", thinking="t"))
    payload = serialize_loop_event(wrapped)
    assert payload is not None
    assert payload["type"] == "subagent_child"
    assert payload["data"]["subagent_id"] == str(sid)
    assert payload["data"]["inner_type"] == "llm_response"
    assert payload["data"]["inner"]["content"] == "hi"
    # The inner does NOT carry its own trace_id; only the outer frame does.
    assert "trace_id" not in payload["data"]["inner"]
    assert "trace_id" in payload["data"]


def test_wrapper_with_thinking_inner_skips() -> None:
    """A Thinking inner serializes to None → the wrapper skips (defensive; never forwarded)."""
    wrapped = SubagentChildEvent(subagent_id=uuid4(), inner=Thinking(text="x"))
    assert serialize_loop_event(wrapped) is None


def test_wrapper_with_none_inner_skips() -> None:
    """A None inner (dataclass default) serializes to None (skip)."""
    assert serialize_loop_event(SubagentChildEvent(subagent_id=uuid4(), inner=None)) is None
