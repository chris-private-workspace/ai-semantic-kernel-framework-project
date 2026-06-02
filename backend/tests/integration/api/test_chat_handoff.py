"""
File: backend/tests/integration/api/test_chat_handoff.py
Purpose: Integration tests proving Sprint 57.68 A-3b HANDOFF control-transfer on
    the chat path — a loop that ends with stop_reason="handoff" drives the router
    post-loop hook to boot a child session (HandoffService) and emit an
    agent_handoff SSE frame, with full multi-tenant isolation.
Category: Tests / integration / api
Scope: Phase 57 / Sprint 57.68 A-3b (Stage 2)

Description:
    Deterministic + Azure-call-free: a fake AgentLoop yields a single
    LoopCompleted(stop_reason="handoff", handoff_target=..., handoff_reason=...).
    The test drives the REAL router generator `_stream_loop_events` (the same
    serialize + post-loop hook the production POST /chat uses; verifier_registry
    is None → run_with_verification delegates straight to loop.run()), against a
    REAL db_session. It asserts the full backend handover:
      (a) the parent LoopCompleted carries stop_reason == "handoff";
      (b) a child session row is persisted (tenant == parent, handoff_parent_id
          == parent.id, meta_data["agent_role"] == target);
      (c) the parent session status == "handed_off";
      (d) a "session.handoff" audit row exists;
      (e) an `agent_handoff` SSE frame carries new_session_id.

    Multi-tenant 鐵律: the child inherits the parent's tenant_id; a handoff with
    a foreign-tenant parent raises HandoffError inside the hook → fail-soft (no
    child booted, no parent mutation, no agent_handoff frame, stream not crashed).

    Also hosts the 3 router-hook logic tests (emit / fail-soft / skip) with a
    monkeypatched HandoffService. They live here (not the unit file) because
    _stream_loop_events opens a real DB connection for its LoopCompleted
    observers; depending on the managed `db_session` fixture lets conftest's
    dispose_engine() teardown run so the connection does not leak onto a closed
    event loop (Risk Class C).

Created: 2026-06-02 (Sprint 57.68 A-3b Stage 2)
Last Modified: 2026-06-02 (Sprint 57.69 A-3b — add parent-context carry integration test)
"""

from __future__ import annotations

import json
import sys
from collections.abc import AsyncIterator
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agent_harness._contracts import LoopCompleted, LoopEvent, TraceContext
from agent_harness._contracts.chat import Message
from api.v1.chat.handler import resolve_session_persona
from api.v1.chat.router import _stream_loop_events
from api.v1.chat.session_registry import get_default_registry
from infrastructure.db.models import Session as SessionModel
from infrastructure.db.models.audit import AuditLog
from platform_layer.handoff import DEFAULT_MAX_CARRY_MESSAGES, HandoffError, HandoffResult
from platform_layer.handoff.context_carry import _CARRIED_CONTEXT_HEADER
from tests.conftest import seed_tenant, seed_user

# The `api.v1.chat` package re-exports `router` (the APIRouter instance), which
# shadows the `router` submodule for attribute access — so monkeypatch the real
# module object fetched from sys.modules (NOT `api.v1.chat.router` attr-path).
_ROUTER_MODULE = sys.modules["api.v1.chat.router"]


class _HandoffLoop:
    """Fake AgentLoop whose run() yields one HANDOFF LoopCompleted.

    Mirrors the AgentLoopImpl.run(session_id, user_input, trace_context) async
    generator signature consumed by run_with_verification (passthrough mode).
    """

    def __init__(
        self,
        *,
        target_agent: str,
        reason: str,
        context: list[Message] | None = None,
    ) -> None:
        self._target = target_agent
        self._reason = reason
        self._context = context

    async def run(
        self,
        *,
        session_id: UUID,
        user_input: str,
        trace_context: TraceContext | None = None,
    ) -> AsyncIterator[LoopEvent]:
        yield LoopCompleted(
            stop_reason="handoff",
            total_turns=1,
            handoff_target=self._target,
            handoff_reason=self._reason,
            handoff_context=self._context,
            trace_context=trace_context,
        )


async def _seed_parent_session(db: AsyncSession, *, tenant_id: UUID, user_id: UUID) -> SessionModel:
    """Persist a parent Session row (status active) for a handoff to link to."""
    row = SessionModel(
        id=uuid4(),
        tenant_id=tenant_id,
        user_id=user_id,
        title="parent",
        status="active",
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return row


def _collect_frames(raw: list[bytes]) -> list[tuple[str, dict]]:
    """Parse SSE byte frames into (event_type, data_dict) tuples."""
    frames: list[tuple[str, dict]] = []
    for chunk in raw:
        text = chunk.decode("utf-8")
        event_type = ""
        data_json = ""
        for line in text.splitlines():
            if line.startswith("event: "):
                event_type = line[len("event: ") :]
            elif line.startswith("data: "):
                data_json = line[len("data: ") :]
        if event_type and data_json:
            frames.append((event_type, json.loads(data_json)))
    return frames


@pytest.mark.asyncio
async def test_chat_handoff_boots_child_and_emits_frame(db_session: AsyncSession) -> None:
    """A handoff loop boots a child session + emits an agent_handoff SSE frame."""
    tenant = await seed_tenant(db_session, code="HANDOFF_T")
    user = await seed_user(db_session, tenant, email="handoff@test.com")
    parent = await _seed_parent_session(db_session, tenant_id=tenant.id, user_id=user.id)

    trace_ctx = TraceContext(tenant_id=tenant.id, session_id=parent.id, user_id=user.id)
    loop = _HandoffLoop(target_agent="researcher", reason="needs deep research")
    registry = get_default_registry()
    await registry.register(tenant.id, parent.id)

    raw = [
        frame
        async for frame in _stream_loop_events(
            loop,
            tenant.id,
            parent.id,
            registry,
            user_input="hand this off",
            trace_context=trace_ctx,
            db=db_session,
        )
    ]
    frames = _collect_frames(raw)

    # (a) parent LoopCompleted serialized to loop_end carrying stop_reason=handoff.
    loop_end = [d for t, d in frames if t == "loop_end"]
    assert len(loop_end) == 1
    assert loop_end[0]["stop_reason"] == "handoff"

    # (e) an agent_handoff frame carrying a new_session_id.
    handoff_frames = [d for t, d in frames if t == "agent_handoff"]
    assert len(handoff_frames) == 1
    hf = handoff_frames[0]
    assert hf["target_agent"] == "researcher"
    assert hf["parent_session_id"] == str(parent.id)
    new_session_id = UUID(hf["new_session_id"])

    # (b) child session row persisted, tenant-inherited + linked + persona role.
    child = (
        await db_session.execute(select(SessionModel).where(SessionModel.id == new_session_id))
    ).scalar_one()
    assert child.tenant_id == tenant.id
    assert child.handoff_parent_id == parent.id
    assert child.meta_data["agent_role"] == "researcher"

    # (c) parent marked handed_off.
    refreshed_parent = (
        await db_session.execute(select(SessionModel).where(SessionModel.id == parent.id))
    ).scalar_one()
    assert refreshed_parent.status == "handed_off"

    # (d) a session.handoff audit row exists for the parent.
    audit_rows = (
        (
            await db_session.execute(
                select(AuditLog).where(
                    (AuditLog.tenant_id == tenant.id) & (AuditLog.operation == "session.handoff")
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(audit_rows) == 1
    assert audit_rows[0].operation_data["target_agent"] == "researcher"
    assert audit_rows[0].operation_data["new_session_id"] == str(new_session_id)


@pytest.mark.asyncio
async def test_chat_handoff_carries_parent_context(db_session: AsyncSession) -> None:
    """Sprint 57.69 A-3b slice 2: the parent conversation is carried to the child.

    A handoff loop whose LoopCompleted carries a non-trivial handoff_context
    drives the router hook to boot a child whose meta_data["carried_context"] is
    populated (capped + tenant-scoped); the carried snapshot stays SERVER-SIDE
    (NOT in the loop_end SSE frame); and resolving the child's persona returns a
    prompt STRING that embeds the carried-context block.
    """
    tenant = await seed_tenant(db_session, code="HANDOFF_CARRY")
    user = await seed_user(db_session, tenant, email="carry@test.com")
    parent = await _seed_parent_session(db_session, tenant_id=tenant.id, user_id=user.id)

    # Build more than the cap so we also prove the last-N cap (drop oldest).
    over = DEFAULT_MAX_CARRY_MESSAGES + 4
    convo = [
        Message(role="user" if i % 2 == 0 else "assistant", content=f"turn-{i}")
        for i in range(over)
    ]

    trace_ctx = TraceContext(tenant_id=tenant.id, session_id=parent.id, user_id=user.id)
    loop = _HandoffLoop(target_agent="researcher", reason="carry it", context=convo)
    registry = get_default_registry()
    await registry.register(tenant.id, parent.id)

    raw = [
        frame
        async for frame in _stream_loop_events(
            loop,
            tenant.id,
            parent.id,
            registry,
            user_input="hand this off with context",
            trace_context=trace_ctx,
            db=db_session,
        )
    ]
    frames = _collect_frames(raw)

    # The carried snapshot must stay server-side — NOT on the loop_end frame.
    loop_end = [d for t, d in frames if t == "loop_end"]
    assert len(loop_end) == 1
    assert "handoff_context" not in loop_end[0]

    handoff_frames = [d for t, d in frames if t == "agent_handoff"]
    assert len(handoff_frames) == 1
    new_session_id = UUID(handoff_frames[0]["new_session_id"])

    # Child carries the capped carried_context, tenant-scoped to the parent.
    child = (
        await db_session.execute(select(SessionModel).where(SessionModel.id == new_session_id))
    ).scalar_one()
    assert child.tenant_id == tenant.id
    carried = child.meta_data["carried_context"]
    assert len(carried) == DEFAULT_MAX_CARRY_MESSAGES
    assert carried[-1] == {"role": "assistant", "content": f"turn-{over - 1}"}

    # Resolving the child persona returns a STRING embedding the carried block.
    prompt = await resolve_session_persona(db_session, new_session_id, tenant.id)
    assert isinstance(prompt, str)
    assert _CARRIED_CONTEXT_HEADER in prompt
    assert f"turn-{over - 1}" in prompt


@pytest.mark.asyncio
async def test_chat_handoff_foreign_parent_fails_soft(db_session: AsyncSession) -> None:
    """A handoff whose tenant does not own the parent boots NO child + no frame.

    Multi-tenant 鐵律: the hook calls HandoffService with the caller's tenant_id;
    a parent in another tenant is not found → HandoffError → fail-soft (no child,
    no parent mutation, no agent_handoff frame, stream not crashed).
    """
    parent_tenant = await seed_tenant(db_session, code="HANDOFF_PT")
    parent_user = await seed_user(db_session, parent_tenant, email="pt@test.com")
    parent = await _seed_parent_session(
        db_session, tenant_id=parent_tenant.id, user_id=parent_user.id
    )

    # A DIFFERENT tenant attempts the handoff (its own tenant_id in the context).
    other_tenant = await seed_tenant(db_session, code="HANDOFF_OT")
    other_user = await seed_user(db_session, other_tenant, email="ot@test.com")

    trace_ctx = TraceContext(tenant_id=other_tenant.id, session_id=parent.id, user_id=other_user.id)
    loop = _HandoffLoop(target_agent="researcher", reason="x")
    registry = get_default_registry()
    await registry.register(other_tenant.id, parent.id)

    raw = [
        frame
        async for frame in _stream_loop_events(
            loop,
            other_tenant.id,
            parent.id,
            registry,
            user_input="hand off cross-tenant",
            trace_context=trace_ctx,
            db=db_session,
        )
    ]
    frames = _collect_frames(raw)

    # Stream did not crash; loop_end still emitted.
    assert any(t == "loop_end" for t, _ in frames)
    # No agent_handoff frame (HandoffError swallowed by the fail-soft hook).
    assert not any(t == "agent_handoff" for t, _ in frames)

    # No child session was booted under the foreign tenant.
    foreign_children = (
        (
            await db_session.execute(
                select(SessionModel).where(SessionModel.tenant_id == other_tenant.id)
            )
        )
        .scalars()
        .all()
    )
    assert foreign_children == []

    # Parent (in its own tenant) was NOT mutated.
    refreshed_parent = (
        await db_session.execute(select(SessionModel).where(SessionModel.id == parent.id))
    ).scalar_one()
    assert refreshed_parent.status == "active"


# ============================================================
# Router post-loop hook unit-of-logic (mocked HandoffService)
# ============================================================
# These exercise ONLY the router hook's branching (emit / fail-soft / skip)
# with HandoffService monkeypatched, so the real boot_handoff is not under test
# here. They live in the integration file (not the unit file) because
# _stream_loop_events opens a real DB connection for its LoopCompleted
# observers; depending on the managed `db_session` fixture ensures conftest's
# dispose_engine() teardown runs and the connection does not leak onto a closed
# event loop (Risk Class C — module-level engine across test event loops).


@pytest.mark.asyncio
async def test_router_hook_emits_agent_handoff(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """On success the hook boots a child + emits an agent_handoff frame."""
    tenant = await seed_tenant(db_session, code="HANDOFF_HOOK1")
    user = await seed_user(db_session, tenant, email="hook1@test.com")
    parent = await _seed_parent_session(db_session, tenant_id=tenant.id, user_id=user.id)
    new_session_id = uuid4()

    class _FakeService:
        async def boot_handoff(self, **kwargs: Any) -> HandoffResult:
            assert kwargs["parent_session_id"] == parent.id
            assert kwargs["target_agent"] == "researcher"
            assert kwargs["tenant_id"] == tenant.id
            assert kwargs["user_id"] == user.id
            return HandoffResult(
                new_session_id=new_session_id,
                parent_session_id=parent.id,
                target_agent="researcher",
            )

    monkeypatch.setattr(_ROUTER_MODULE, "HandoffService", _FakeService)

    trace_ctx = TraceContext(tenant_id=tenant.id, session_id=parent.id, user_id=user.id)
    registry = get_default_registry()
    await registry.register(tenant.id, parent.id)

    raw = [
        frame
        async for frame in _stream_loop_events(
            _HandoffLoop(target_agent="researcher", reason="r"),
            tenant.id,
            parent.id,
            registry,
            user_input="x",
            trace_context=trace_ctx,
            db=db_session,
        )
    ]
    frames = _collect_frames(raw)
    handoff = [d for t, d in frames if t == "agent_handoff"]
    assert len(handoff) == 1
    assert handoff[0]["new_session_id"] == str(new_session_id)
    assert handoff[0]["parent_session_id"] == str(parent.id)
    assert handoff[0]["target_agent"] == "researcher"


@pytest.mark.asyncio
async def test_router_hook_failsoft_on_handoff_error(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A HandoffError is swallowed — no agent_handoff frame, stream not crashed."""
    tenant = await seed_tenant(db_session, code="HANDOFF_HOOK2")
    user = await seed_user(db_session, tenant, email="hook2@test.com")
    parent = await _seed_parent_session(db_session, tenant_id=tenant.id, user_id=user.id)

    class _RaisingService:
        async def boot_handoff(self, **kwargs: Any) -> HandoffResult:
            raise HandoffError("foreign parent")

    monkeypatch.setattr(_ROUTER_MODULE, "HandoffService", _RaisingService)

    trace_ctx = TraceContext(tenant_id=tenant.id, session_id=parent.id, user_id=user.id)
    registry = get_default_registry()
    await registry.register(tenant.id, parent.id)

    raw = [
        frame
        async for frame in _stream_loop_events(
            _HandoffLoop(target_agent="researcher", reason="r"),
            tenant.id,
            parent.id,
            registry,
            user_input="x",
            trace_context=trace_ctx,
            db=db_session,
        )
    ]
    frames = _collect_frames(raw)
    # Stream completed (loop_end present) but no agent_handoff frame.
    assert any(t == "loop_end" for t, _ in frames)
    assert not any(t == "agent_handoff" for t, _ in frames)


@pytest.mark.asyncio
async def test_router_hook_skips_when_no_target(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Empty handoff_target → HandoffService is never called (no frame)."""
    tenant = await seed_tenant(db_session, code="HANDOFF_HOOK3")
    user = await seed_user(db_session, tenant, email="hook3@test.com")
    parent = await _seed_parent_session(db_session, tenant_id=tenant.id, user_id=user.id)
    called = {"n": 0}

    class _CountingService:
        async def boot_handoff(self, **kwargs: Any) -> HandoffResult:
            called["n"] += 1
            return HandoffResult(uuid4(), uuid4(), "x")

    monkeypatch.setattr(_ROUTER_MODULE, "HandoffService", _CountingService)

    trace_ctx = TraceContext(tenant_id=tenant.id, session_id=parent.id, user_id=user.id)
    registry = get_default_registry()
    await registry.register(tenant.id, parent.id)

    raw = [
        frame
        async for frame in _stream_loop_events(
            _HandoffLoop(target_agent="", reason="r"),  # empty target
            tenant.id,
            parent.id,
            registry,
            user_input="x",
            trace_context=trace_ctx,
            db=db_session,
        )
    ]
    frames = _collect_frames(raw)
    assert called["n"] == 0
    assert not any(t == "agent_handoff" for t, _ in frames)
