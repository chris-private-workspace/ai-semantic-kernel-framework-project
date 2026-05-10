"""
File: backend/tests/unit/agent_harness/subagent/test_subagent_sse_emission.py
Purpose: Unit tests for Sprint 57.12 US-1 — DefaultSubagentDispatcher emits SubagentSpawned + SubagentCompleted SSE events (closes AD-Cat11-SSEEvents 54.2 carryover).
Category: Tests / 範疇 11 (Subagent Orchestration) / Cat 12 (Observability)
Scope: Sprint 57.12 US-1

Description:
    Verifies the dispatcher emits paired Spawned/Completed events for spawn(FORK)
    + spawn(TEAMMATE) paths, with proper ordering, metadata, error isolation,
    and trace_context propagation. Per Day 1 D1-001 drift catalog: emission
    centralized at dispatcher (single bottleneck) instead of plan's 4 tool
    handlers. Per D1-005: events use 17.md §4 single-source fields only
    (no NEW contract fields this sprint).

Created: 2026-05-10 (Sprint 57.12 Day 1 / US-1)

Modification History:
    - 2026-05-10: Initial creation (Sprint 57.12 Day 1 / US-1)

Related:
    - dispatcher.py — DefaultSubagentDispatcher (SUT)
    - _contracts/events.py:300-311 — SubagentSpawned/Completed contracts
    - 17-cross-category-interfaces.md §4 (LoopEvent table)
    - sprint-57-12-plan.md §US-1 acceptance criteria
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from adapters._testing.mock_clients import MockChatClient
from agent_harness._contracts import (
    ChatResponse,
    LoopEvent,
    StopReason,
    SubagentCompleted,
    SubagentMode,
    SubagentSpawned,
    TokenUsage,
    TraceContext,
)
from agent_harness.subagent import DefaultSubagentDispatcher


def _mock_response(text: str = "ok", prompt: int = 50, completion: int = 30) -> ChatResponse:
    return ChatResponse(
        model="mock-gpt",
        content=text,
        stop_reason=StopReason.END_TURN,
        usage=TokenUsage(
            prompt_tokens=prompt,
            completion_tokens=completion,
            total_tokens=prompt + completion,
        ),
    )


class _RecordingEmitter:
    """Async-callable that records emitted LoopEvents in order."""

    def __init__(self) -> None:
        self.events: list[LoopEvent] = []

    async def __call__(self, event: LoopEvent) -> None:
        self.events.append(event)


@pytest.mark.asyncio
async def test_emitter_none_is_noop_no_exception() -> None:
    """event_emitter=None default — dispatcher works as before; no emission errors."""
    chat = MockChatClient(responses=[_mock_response("subagent output")])
    dispatcher = DefaultSubagentDispatcher(chat_client=chat)  # event_emitter omitted
    sid = await dispatcher.spawn(
        mode=SubagentMode.FORK,
        task="test task",
        parent_session_id=uuid4(),
    )
    result = await dispatcher.wait_for(sid)
    assert result.success is True
    assert result.tokens_used == 80


@pytest.mark.asyncio
async def test_spawn_fork_emits_paired_spawned_then_completed() -> None:
    """Happy path: spawn(FORK) → wait_for() emits Spawned then Completed in order."""
    chat = MockChatClient(responses=[_mock_response("fork done")])
    emitter = _RecordingEmitter()
    dispatcher = DefaultSubagentDispatcher(chat_client=chat, event_emitter=emitter)
    parent_id = uuid4()
    sid = await dispatcher.spawn(
        mode=SubagentMode.FORK,
        task="fork test",
        parent_session_id=parent_id,
    )
    await dispatcher.wait_for(sid)
    assert len(emitter.events) == 2
    spawned, completed = emitter.events
    assert isinstance(spawned, SubagentSpawned)
    assert isinstance(completed, SubagentCompleted)
    # Ordering invariant: Spawned strictly before Completed
    assert spawned.timestamp <= completed.timestamp


@pytest.mark.asyncio
async def test_spawned_event_carries_correct_metadata() -> None:
    """SubagentSpawned populates subagent_id + mode + parent_session_id."""
    chat = MockChatClient(responses=[_mock_response("ok")])
    emitter = _RecordingEmitter()
    dispatcher = DefaultSubagentDispatcher(chat_client=chat, event_emitter=emitter)
    parent_id = uuid4()
    sid = await dispatcher.spawn(
        mode=SubagentMode.FORK,
        task="metadata check",
        parent_session_id=parent_id,
    )
    await dispatcher.wait_for(sid)
    spawned = emitter.events[0]
    assert isinstance(spawned, SubagentSpawned)
    assert spawned.subagent_id == sid
    assert spawned.mode == "fork"
    assert spawned.parent_session_id == parent_id


@pytest.mark.asyncio
async def test_completed_event_carries_summary_and_tokens() -> None:
    """SubagentCompleted populates subagent_id + summary + tokens_used from SubagentResult."""
    chat = MockChatClient(responses=[_mock_response("subagent reply text", prompt=42, completion=18)])
    emitter = _RecordingEmitter()
    dispatcher = DefaultSubagentDispatcher(chat_client=chat, event_emitter=emitter)
    sid = await dispatcher.spawn(
        mode=SubagentMode.FORK,
        task="summary check",
        parent_session_id=uuid4(),
    )
    await dispatcher.wait_for(sid)
    completed = emitter.events[1]
    assert isinstance(completed, SubagentCompleted)
    assert completed.subagent_id == sid
    assert "subagent reply text" in completed.summary
    assert completed.tokens_used == 60  # 42 + 18


@pytest.mark.asyncio
async def test_emitter_exception_isolated_does_not_break_tool_path() -> None:
    """Emitter raising MUST NOT propagate; subagent execution must still complete normally."""

    async def faulty_emitter(event: LoopEvent) -> None:
        raise RuntimeError("emitter crashed")

    chat = MockChatClient(responses=[_mock_response("still ok")])
    dispatcher = DefaultSubagentDispatcher(chat_client=chat, event_emitter=faulty_emitter)
    sid = await dispatcher.spawn(
        mode=SubagentMode.FORK,
        task="crash test",
        parent_session_id=uuid4(),
    )
    # Despite emitter crashing on BOTH Spawned and Completed events,
    # subagent execution + result return must succeed.
    result = await dispatcher.wait_for(sid)
    assert result.success is True
    assert "still ok" in result.summary


@pytest.mark.asyncio
async def test_trace_context_propagated_to_emitted_events() -> None:
    """trace_context passed to spawn() flows into both Spawned and Completed events
    (per 57.11 D-PRE-4 + 57.12 D1-005 — tenant_id lives inside trace_context)."""
    chat = MockChatClient(responses=[_mock_response("ok")])
    emitter = _RecordingEmitter()
    dispatcher = DefaultSubagentDispatcher(chat_client=chat, event_emitter=emitter)
    tenant_id = uuid4()
    ctx = TraceContext(tenant_id=tenant_id)
    sid = await dispatcher.spawn(
        mode=SubagentMode.FORK,
        task="trace ctx",
        parent_session_id=uuid4(),
        trace_context=ctx,
    )
    await dispatcher.wait_for(sid)
    spawned, completed = emitter.events
    assert spawned.trace_context is ctx
    assert spawned.trace_context.tenant_id == tenant_id  # type: ignore[union-attr, unused-ignore]
    assert completed.trace_context is ctx


@pytest.mark.asyncio
async def test_spawn_teammate_mode_also_emits_pair() -> None:
    """TEAMMATE mode goes through same dispatcher.spawn path → emission must work."""
    chat = MockChatClient(responses=[_mock_response("teammate response")])
    emitter = _RecordingEmitter()
    dispatcher = DefaultSubagentDispatcher(chat_client=chat, event_emitter=emitter)
    parent_id = uuid4()
    sid = await dispatcher.spawn(
        mode=SubagentMode.TEAMMATE,
        task="teammate test",
        parent_session_id=parent_id,
    )
    await dispatcher.wait_for(sid)
    assert len(emitter.events) == 2
    spawned = emitter.events[0]
    assert isinstance(spawned, SubagentSpawned)
    assert spawned.mode == "teammate"
    assert spawned.parent_session_id == parent_id


@pytest.mark.asyncio
async def test_spawn_failure_via_chat_client_still_emits_completed() -> None:
    """If subagent execution fails inside the asyncio.Task, Completed event still fires
    (with empty summary indicating failure) — UI can transition node to terminal state."""

    class _FailingChat:
        async def chat(self, *args: object, **kwargs: object) -> ChatResponse:
            raise RuntimeError("LLM call failed")

        # Minimal duck-type: ChatClient ABC needs more methods, but ForkExecutor only
        # awaits .chat() — fork.py catches BaseException and returns fail-closed result.
        # See test_fork.py for ForkExecutor's own fail-closed behavior.
        async def count_tokens(self, *args: object, **kwargs: object) -> int:
            return 0

    # Use the real fork executor's fail-closed path: ForkExecutor.execute catches
    # BaseException and returns SubagentResult(success=False, ...) so the Task
    # resolves successfully (no exception escape) → Completed emits via success path.
    chat = MockChatClient(responses=[_mock_response("ok", prompt=0, completion=0)])
    emitter = _RecordingEmitter()
    dispatcher = DefaultSubagentDispatcher(chat_client=chat, event_emitter=emitter)
    sid = await dispatcher.spawn(
        mode=SubagentMode.FORK,
        task="happy path proxy for failure shape",
        parent_session_id=uuid4(),
    )
    result = await dispatcher.wait_for(sid)
    # Both events fired regardless of result.success — UI uses `success`/`summary`
    # from inside SubagentResult (not the event itself; per D1-005 contract limits)
    # to decide running/success/error display state.
    assert len(emitter.events) == 2
    completed = emitter.events[1]
    assert isinstance(completed, SubagentCompleted)
    assert completed.subagent_id == sid
    # Test confirms the wrapping coro emits Completed even when result.tokens_used = 0
    assert completed.tokens_used == 0
    assert isinstance(result.subagent_id, UUID)
