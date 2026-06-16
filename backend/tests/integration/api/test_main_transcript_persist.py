"""
File: backend/tests/integration/api/test_main_transcript_persist.py
Purpose: Integration tests for the main-session transcript observer (Sprint 57.125).
Category: Tests / Integration / API
Scope: Phase 57 / Sprint 57.125 / US-1+US-2 (writer)

Description:
    Drives the REAL `_stream_loop_events` with a fake loop that yields main-session
    LoopEvents (TurnStarted / Thinking / LLMRequested / LoopCompleted). Asserts:
    - the inbound user prompt → a `user_message` row FIRST (seq 1, persist-only) — Sprint 57.126
    - each serializable main event → a `message_events` row keyed by the MAIN
      session_id, with a monotonic sequence_num and the serialized payload
    - Thinking (serializer returns None) is NOT persisted (skipped)
    - the observer is env-gated (MAIN_TRANSCRIPT_OBSERVER=false → no rows)
    - main rows (session_id=main) and sidechain rows (session_id=subagent_id)
      coexist without collision in the same run
    - `main_seq` seeds from the session's MAX so seq is globally monotonic across
      the multiple sends of a multi-turn session (Sprint 57.126)
    - tenant isolation: main rows are invisible cross-tenant (鐵律)

Created: 2026-06-16 (Sprint 57.125)

Modification History (newest-first):
    - 2026-06-16: Sprint 57.126 — user_message row first + multi-turn main_seq seed
    - 2026-06-16: Initial creation (Sprint 57.125 — main transcript writer)

Related:
    - api/v1/chat/router.py (_persist_main_event + _stream_loop_events)
    - api/v1/sessions.py (GET /{id}/events reader)
    - sprint-57-125-plan.md §3.1
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agent_harness._contracts import LoopCompleted, LoopEvent, TraceContext
from agent_harness._contracts.events import (
    LLMRequested,
    SubagentChildEvent,
    SubagentSpawned,
    Thinking,
    TurnStarted,
)
from api.v1.chat.router import _stream_loop_events
from api.v1.chat.session_registry import get_default_registry
from infrastructure.db.models.sessions import MessageEvent
from infrastructure.db.models.sessions import Session as SessionModel
from tests.conftest import seed_tenant, seed_user

pytestmark = pytest.mark.asyncio


class _EmittingLoop:
    """Fake AgentLoop: yields a fixed main-session event sequence then completes.

    If a subagent buffer + id are provided, it also appends a sidechain event to
    the buffer mid-run (simulating the dispatcher emitting while the loop awaits
    task_spawn) so the main/sidechain separation can be asserted in one run.
    """

    def __init__(
        self, *, buffer: list[LoopEvent] | None = None, subagent_id: UUID | None = None
    ) -> None:
        self._buffer = buffer
        self._sid = subagent_id

    async def run(
        self,
        *,
        session_id: UUID,
        user_input: str,
        trace_context: TraceContext | None = None,
    ) -> AsyncIterator[LoopEvent]:
        yield TurnStarted(turn_num=0, trace_context=trace_context)
        # Thinking → serializer returns None → must NOT be persisted.
        yield Thinking(text="(internal reasoning)", trace_context=trace_context)
        yield LLMRequested(model="gpt-x", tokens_in=11, trace_context=trace_context)
        if self._buffer is not None and self._sid is not None:
            self._buffer.append(
                SubagentSpawned(subagent_id=self._sid, mode="fork", parent_session_id=session_id)
            )
            self._buffer.append(
                SubagentChildEvent(subagent_id=self._sid, inner=TurnStarted(turn_num=0))
            )
        yield LoopCompleted(stop_reason="end_turn", total_turns=1, trace_context=trace_context)


async def _seed_main_session(db: AsyncSession, *, tenant_id: UUID, user_id: UUID) -> UUID:
    sid = uuid4()
    db.add(SessionModel(id=sid, tenant_id=tenant_id, user_id=user_id, status="active"))
    await db.flush()
    return sid


async def _drive(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    session_id: UUID,
    user_id: UUID,
    buffer: list[LoopEvent] | None = None,
    subagent_id: UUID | None = None,
) -> None:
    loop = _EmittingLoop(buffer=buffer, subagent_id=subagent_id)
    registry = get_default_registry()
    await registry.register(tenant_id, session_id)
    trace_ctx = TraceContext(tenant_id=tenant_id, session_id=session_id, user_id=user_id)
    async for _frame in _stream_loop_events(
        loop,
        tenant_id,
        session_id,
        registry,
        user_input="hello",
        trace_context=trace_ctx,
        db=db,
        subagent_event_buffer=buffer,
    ):
        pass


async def test_main_transcript_persists_ordered_events(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MAIN_TRANSCRIPT_OBSERVER", "true")
    tenant = await seed_tenant(db_session, code="MAINTX_T")
    user = await seed_user(db_session, tenant, email="main@tx.test")
    session_id = await _seed_main_session(db_session, tenant_id=tenant.id, user_id=user.id)

    await _drive(db_session, tenant_id=tenant.id, session_id=session_id, user_id=user.id)

    events = (
        (
            await db_session.execute(
                select(MessageEvent)
                .where(MessageEvent.session_id == session_id)
                .order_by(MessageEvent.sequence_num)
            )
        )
        .scalars()
        .all()
    )
    # Sprint 57.126: user_message persisted FIRST (seq 1), then TurnStarted +
    # LLMRequested + LoopCompleted; Thinking skipped (serializer None).
    assert [e.sequence_num for e in events] == [1, 2, 3, 4]
    assert [e.event_type for e in events] == [
        "user_message",
        "turn_start",
        "llm_request",
        "loop_end",
    ]
    assert all(e.tenant_id == tenant.id for e in events)
    # The user_message row carries the inbound prompt text (persist-only; no trace_id).
    assert events[0].event_data == {"text": "hello"}
    # event_data stores the serializer's data dict (+ trace_id injection).
    assert events[1].event_data["turn_num"] == 0
    assert events[2].event_data["model"] == "gpt-x"
    assert events[3].event_data["stop_reason"] == "end_turn"
    assert "trace_id" in events[1].event_data


async def test_main_transcript_env_gated_off_writes_nothing(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MAIN_TRANSCRIPT_OBSERVER", "false")
    tenant = await seed_tenant(db_session, code="MAINTX_OFF")
    user = await seed_user(db_session, tenant, email="main@off.test")
    session_id = await _seed_main_session(db_session, tenant_id=tenant.id, user_id=user.id)

    await _drive(db_session, tenant_id=tenant.id, session_id=session_id, user_id=user.id)

    rows = (
        (
            await db_session.execute(
                select(MessageEvent).where(MessageEvent.session_id == session_id)
            )
        )
        .scalars()
        .all()
    )
    assert rows == []


async def test_main_and_sidechain_rows_separate_by_session_id(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Main rows (session_id=main) + sidechain rows (session_id=subagent_id) coexist."""
    monkeypatch.setenv("MAIN_TRANSCRIPT_OBSERVER", "true")
    monkeypatch.setenv("SUBAGENT_TRANSCRIPT_OBSERVER", "true")
    tenant = await seed_tenant(db_session, code="MAINTX_MIX")
    user = await seed_user(db_session, tenant, email="main@mix.test")
    session_id = await _seed_main_session(db_session, tenant_id=tenant.id, user_id=user.id)
    buffer: list[LoopEvent] = []
    sub_id = uuid4()

    await _drive(
        db_session,
        tenant_id=tenant.id,
        session_id=session_id,
        user_id=user.id,
        buffer=buffer,
        subagent_id=sub_id,
    )

    main_rows = (
        (
            await db_session.execute(
                select(MessageEvent).where(MessageEvent.session_id == session_id)
            )
        )
        .scalars()
        .all()
    )
    side_rows = (
        (await db_session.execute(select(MessageEvent).where(MessageEvent.session_id == sub_id)))
        .scalars()
        .all()
    )
    # Sprint 57.126: main rows now include the user_message row (seq 1).
    assert sorted(e.event_type for e in main_rows) == [
        "llm_request",
        "loop_end",
        "turn_start",
        "user_message",
    ]
    assert len(side_rows) >= 1
    assert all(e.event_type == "subagent_child" for e in side_rows)
    # No collision: main rows own a clean 1..4 sequence space of their own.
    assert {e.sequence_num for e in main_rows} == {1, 2, 3, 4}


async def test_main_transcript_invisible_cross_tenant(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Main transcript rows are tenant-scoped (multi-tenant 鐵律)."""
    monkeypatch.setenv("MAIN_TRANSCRIPT_OBSERVER", "true")
    tenant_a = await seed_tenant(db_session, code="MAINTX_XT_A")
    tenant_b = await seed_tenant(db_session, code="MAINTX_XT_B")
    user_a = await seed_user(db_session, tenant_a, email="xt_a@main.test")
    session_id = await _seed_main_session(db_session, tenant_id=tenant_a.id, user_id=user_a.id)

    await _drive(db_session, tenant_id=tenant_a.id, session_id=session_id, user_id=user_a.id)

    b_rows = (
        (
            await db_session.execute(
                select(MessageEvent)
                .where(MessageEvent.session_id == session_id)
                .where(MessageEvent.tenant_id == tenant_b.id)
            )
        )
        .scalars()
        .all()
    )
    assert b_rows == []


async def test_main_seq_continues_across_sends(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Sprint 57.126: a multi-turn session (≥2 sends) keeps a globally monotonic
    sequence_num — `main_seq` seeds from the session's MAX, so ORDER BY sequence_num
    replays send-1's events then send-2's (57.125 reset to 0 per request → scramble)."""
    monkeypatch.setenv("MAIN_TRANSCRIPT_OBSERVER", "true")
    tenant = await seed_tenant(db_session, code="MAINTX_MT")
    user = await seed_user(db_session, tenant, email="main@mt.test")
    session_id = await _seed_main_session(db_session, tenant_id=tenant.id, user_id=user.id)

    # Two sends on the SAME session (multi-turn conversation).
    await _drive(db_session, tenant_id=tenant.id, session_id=session_id, user_id=user.id)
    await _drive(db_session, tenant_id=tenant.id, session_id=session_id, user_id=user.id)

    events = (
        (
            await db_session.execute(
                select(MessageEvent)
                .where(MessageEvent.session_id == session_id)
                .order_by(MessageEvent.sequence_num)
            )
        )
        .scalars()
        .all()
    )
    # 4 rows per send (user_message + turn_start + llm_request + loop_end), seq 1..8,
    # no collision, each send's block contiguous + in order.
    assert [e.sequence_num for e in events] == [1, 2, 3, 4, 5, 6, 7, 8]
    assert [e.event_type for e in events] == [
        "user_message",
        "turn_start",
        "llm_request",
        "loop_end",
        "user_message",
        "turn_start",
        "llm_request",
        "loop_end",
    ]
