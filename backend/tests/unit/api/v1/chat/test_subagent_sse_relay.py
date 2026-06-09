"""
File: backend/tests/unit/api/v1/chat/test_subagent_sse_relay.py
Purpose: Unit tests — Cat 11 → Cat 12 subagent SSE relay (node-level).
Category: Tests / 範疇 11 (Subagent) / Cat 12 (Observability) / api chat path
Scope: Sprint 57.95

Description:
    Sprint 57.95 wires the chat subagent dispatcher's event_emitter so
    SubagentSpawned / SubagentCompleted reach the SSE stream and the Inspector
    "Tree" tab shows the subagent node (was headless: "no subagents"). Subagent
    events are emitted while the parent loop awaits the task_spawn tool (the loop
    generator is blocked then), so a router-owned buffer collects them and
    _stream_loop_events drains it. These tests cover:
      - make_chat_subagent_dispatcher threads event_emitter into the dispatcher
      - _drain_subagent_frames serializes buffered events + empties the buffer
      - _stream_loop_events relays buffered subagent events into the SSE stream
      - empty buffer → no subagent frames (no-regression on the non-spawn path)

Created: 2026-06-09 (Sprint 57.95)
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import UUID, uuid4

import pytest

from adapters._testing.mock_clients import MockChatClient
from agent_harness._contracts import (
    LoopCompleted,
    LoopEvent,
    SubagentCompleted,
    SubagentSpawned,
    TraceContext,
)
from api.v1.chat._category_factories import make_chat_subagent_dispatcher
from api.v1.chat.router import _drain_subagent_frames, _stream_loop_events
from api.v1.chat.session_registry import SessionRegistry

# === Factory threading (US-1) ===


def test_make_chat_subagent_dispatcher_threads_event_emitter() -> None:
    """The chat factory passes event_emitter through to the dispatcher (was dropped)."""

    async def _emitter(event: LoopEvent) -> None:  # pragma: no cover — identity check only
        return None

    chat = MockChatClient(responses=[])
    dispatcher = make_chat_subagent_dispatcher(chat, event_emitter=_emitter)
    assert dispatcher._event_emitter is _emitter


def test_make_chat_subagent_dispatcher_default_emitter_is_none() -> None:
    """No emitter supplied → dispatcher emission stays a no-op (pre-57.95 default)."""
    chat = MockChatClient(responses=[])
    dispatcher = make_chat_subagent_dispatcher(chat)
    assert dispatcher._event_emitter is None


# === _drain_subagent_frames pure helper (US-2/US-4) ===


def test_drain_subagent_frames_empty_or_none_returns_empty() -> None:
    assert _drain_subagent_frames(None) == []
    assert _drain_subagent_frames([]) == []


def test_drain_subagent_frames_serializes_and_empties_buffer() -> None:
    """Buffered Spawned/Completed → 2 SSE frames; the buffer is drained to empty."""
    sid = uuid4()
    buffer: list[LoopEvent] = [
        SubagentSpawned(subagent_id=sid, mode="fork", parent_session_id=uuid4()),
        SubagentCompleted(subagent_id=sid, summary="child summary", tokens_used=42),
    ]
    frames = _drain_subagent_frames(buffer)
    assert len(frames) == 2
    joined = b"".join(frames)
    assert b"subagent_spawned" in joined
    assert b"subagent_completed" in joined
    assert b"child summary" in joined
    assert buffer == []  # drained (the caller's list is emptied in place)


# === _stream_loop_events relay (US-2/US-3/US-4) ===


class _SpawningStubLoop:
    """Stub loop whose run() appends subagent events to the shared buffer BEFORE
    yielding LoopCompleted — mirrors the dispatcher emitting during a task_spawn
    tool await (the loop generator is blocked then, so the events land in the
    router buffer, not the loop's own event stream)."""

    def __init__(self, buffer: list[LoopEvent], parent_session_id: UUID) -> None:
        self._buffer = buffer
        self._parent_session_id = parent_session_id
        self.subagent_id = uuid4()

    async def run(
        self,
        *,
        session_id: UUID,
        user_input: str,
        trace_context: TraceContext,
    ) -> AsyncIterator[object]:
        self._buffer.append(
            SubagentSpawned(
                subagent_id=self.subagent_id,
                mode="fork",
                parent_session_id=self._parent_session_id,
            )
        )
        self._buffer.append(
            SubagentCompleted(
                subagent_id=self.subagent_id,
                summary="child loop summary",
                tokens_used=42,
            )
        )
        yield LoopCompleted(
            stop_reason="end_turn",
            total_turns=1,
            total_tokens=10,
            trace_context=trace_context,
        )


class _PlainStubLoop:
    """Stub loop that never spawns — yields only a LoopCompleted."""

    async def run(
        self,
        *,
        session_id: UUID,
        user_input: str,
        trace_context: TraceContext,
    ) -> AsyncIterator[object]:
        yield LoopCompleted(
            stop_reason="end_turn",
            total_turns=1,
            total_tokens=10,
            trace_context=trace_context,
        )


async def _collect(stream: AsyncIterator[bytes]) -> list[bytes]:
    return [chunk async for chunk in stream]


@pytest.mark.asyncio
async def test_stream_loop_events_relays_buffered_subagent_frames() -> None:
    """A spawn emitted during the loop is drained into the SSE stream (Tree node)."""
    tenant_id = uuid4()
    session_id = uuid4()
    registry = SessionRegistry()
    await registry.register(tenant_id, session_id)
    buffer: list[LoopEvent] = []
    stub = _SpawningStubLoop(buffer, parent_session_id=session_id)
    trace_ctx = TraceContext(tenant_id=tenant_id, session_id=session_id)

    frames = await _collect(
        _stream_loop_events(
            stub,
            tenant_id,
            session_id,
            registry,
            user_input="spawn a sub-task please",
            trace_context=trace_ctx,
            subagent_event_buffer=buffer,
        )
    )
    joined = b"".join(frames)
    assert b"subagent_spawned" in joined
    assert b"subagent_completed" in joined
    assert b"child loop summary" in joined
    # The subagent frames precede the loop_end frame (drained before the event).
    assert joined.index(b"subagent_spawned") < joined.index(b"loop_end")
    # The buffer is fully drained.
    assert buffer == []


@pytest.mark.asyncio
async def test_stream_loop_events_empty_buffer_emits_no_subagent_frames() -> None:
    """No spawn → no subagent frames (byte-level no-regression on the non-spawn path)."""
    tenant_id = uuid4()
    session_id = uuid4()
    registry = SessionRegistry()
    await registry.register(tenant_id, session_id)
    buffer: list[LoopEvent] = []
    trace_ctx = TraceContext(tenant_id=tenant_id, session_id=session_id)

    frames = await _collect(
        _stream_loop_events(
            _PlainStubLoop(),
            tenant_id,
            session_id,
            registry,
            user_input="no spawn",
            trace_context=trace_ctx,
            subagent_event_buffer=buffer,
        )
    )
    joined = b"".join(frames)
    assert b"subagent_spawned" not in joined
    assert b"subagent_completed" not in joined
