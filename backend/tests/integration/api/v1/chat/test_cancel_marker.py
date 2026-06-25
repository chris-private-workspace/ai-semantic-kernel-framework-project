"""
File: backend/tests/integration/api/v1/chat/test_cancel_marker.py
Purpose: Integration tests — cancel_session persists the interrupt marker (Sprint 57.143).
Category: Tests / Integration / API (chat)
Scope: Sprint 57.143 (AD-UserStop-Resume-Context — user Stop→continue durable resume)

Description:
    Verifies the US-2 backend: POST /sessions/{id}/cancel records a
    `[Request interrupted by user]` marker in the Cat-3 messages ledger via
    DBMessageStore's own committed tenant-scoped session, so a follow-up "continue"
    send rehydrates a coherent transcript. Calls the handler function directly
    (the Depends-injected current_tenant is passed as a kwarg) against the real
    default SessionRegistry + real PG:
    - cancel a running session → marker persisted (assistant role, marker text)
    - cross-tenant cancel → 404, NO marker written for the real tenant
    - marker-persist failure path is best-effort (covered by the unit suite's
      no-DB cancel tests — the 204/404 contract is unchanged).

    Seed is COMMITTED (the store opens its own session → needs the session FK
    visible); cleanup deletes the tenant (FK CASCADE drops user/session/messages),
    mirroring tests/integration/api/conftest.py's committed-test sweep.

Pre-requisite (per tests/conftest.py):
    docker compose -f docker-compose.dev.yml up -d postgres
    cd backend && alembic upgrade head

Created: 2026-06-25 (Sprint 57.143)
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from agent_harness.state_mgmt import DBMessageStore
from api.v1.chat.router import INTERRUPT_MARKER, cancel_session
from api.v1.chat.session_registry import get_default_registry
from infrastructure.db import get_session_factory
from infrastructure.db.models import Session as SessionModel
from tests.conftest import seed_tenant, seed_user

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def committed_session(db_session: AsyncSession) -> AsyncIterator[tuple[object, object]]:
    """Seed tenant/user/session COMMITTED; yield (sid, tid); cleanup via tenant CASCADE."""
    tenant = await seed_tenant(db_session, code=f"CANCELMARK_{uuid4().hex[:8]}")
    user = await seed_user(db_session, tenant, email=f"{uuid4().hex[:8]}@test.com")
    session_row = SessionModel(tenant_id=tenant.id, user_id=user.id)
    db_session.add(session_row)
    await db_session.flush()
    await db_session.refresh(session_row)
    sid, tid = session_row.id, tenant.id
    await db_session.commit()
    try:
        yield sid, tid
    finally:
        factory = get_session_factory()
        async with factory() as s:
            await s.execute(text("DELETE FROM tenants WHERE id = :tid"), {"tid": str(tid)})
            await s.commit()


async def test_cancel_persists_interrupt_marker(committed_session: tuple[object, object]) -> None:
    """cancel_session records the [Request interrupted by user] marker in the ledger."""
    sid, tid = committed_session
    reg = get_default_registry()
    await reg.register(tid, sid)  # type: ignore[arg-type]
    try:
        await cancel_session(session_id=sid, current_tenant=tid)  # type: ignore[arg-type]

        store = DBMessageStore(get_session_factory(), session_id=sid, tenant_id=tid)
        loaded = await store.load()
        assert [(m.role, m.content) for m in loaded] == [("assistant", INTERRUPT_MARKER)]
    finally:
        await reg.cleanup(tid, sid)  # type: ignore[arg-type]


async def test_cancel_cross_tenant_404_no_marker(committed_session: tuple[object, object]) -> None:
    """A cross-tenant cancel → 404 and writes NO marker for the real tenant (鐵律)."""
    sid, tid = committed_session
    reg = get_default_registry()
    await reg.register(tid, sid)  # type: ignore[arg-type]
    try:
        with pytest.raises(HTTPException) as exc:
            await cancel_session(session_id=sid, current_tenant=uuid4())
        assert exc.value.status_code == 404

        # the real tenant's ledger stays empty — the 404 short-circuits before the marker
        store = DBMessageStore(get_session_factory(), session_id=sid, tenant_id=tid)
        assert await store.load() == []
    finally:
        await reg.cleanup(tid, sid)  # type: ignore[arg-type]
