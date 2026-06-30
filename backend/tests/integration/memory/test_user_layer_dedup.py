"""
File: backend/tests/integration/memory/test_user_layer_dedup.py
Purpose: Real-DB tests for UserLayer.write write-side dedup (Sprint 57.150).
Category: Tests / Integration / 範疇 3
Scope: Phase 57 / Sprint 57.150 (US-1, US-3)

Description:
    Requires a live PostgreSQL with `alembic upgrade head` (per conftest db_session)
    so the uq_memory_user_dedup constraint exists. Verifies that a repeated normalized
    fact UPDATEs one row (the upsert) instead of inserting a duplicate, that the
    conflict resolution takes the greatest confidence + latest content while keeping
    the first writer's provenance, that distinct facts stay separate, and that the
    dedup key is per (tenant, user) so it never collapses across tenants. Also holds
    the long_term/short_term expiry coverage relocated from the unit test (the
    inserted row is observable here).

    Uses the commit→flush shared-session trick (mirrors
    test_memory_ops_rls.py::test_user_layer_write_op_same_txn_rollback) so the writes
    live in the test transaction and roll back at teardown; ON CONFLICT still sees the
    flushed first row within the same transaction.

Created: 2026-06-30 (Sprint 57.150)
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import AsyncIterator, Callable

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from agent_harness.memory.layers.user_layer import UserLayer
from infrastructure.db.models.memory import MemoryOp, MemoryUser
from tests.conftest import seed_tenant, seed_user

pytestmark = pytest.mark.asyncio


def _shared_factory(db_session: AsyncSession) -> Callable[[], object]:
    """Yield the test session; treat commit as flush so the test txn rolls back."""

    @asynccontextmanager
    async def _factory() -> AsyncIterator[AsyncSession]:
        orig_commit = db_session.commit
        db_session.commit = db_session.flush  # type: ignore[method-assign]
        try:
            yield db_session
        finally:
            db_session.commit = orig_commit  # type: ignore[method-assign]

    return _factory


async def _user_count(db_session: AsyncSession, tenant_id: object) -> int:
    return (
        await db_session.execute(
            select(func.count()).select_from(MemoryUser).where(MemoryUser.tenant_id == tenant_id)
        )
    ).scalar_one()


async def test_same_fact_twice_dedups_to_one_row(db_session: AsyncSession) -> None:
    """A repeat of the same normalized fact UPDATEs one row (greatest confidence,
    latest content) instead of inserting a duplicate; the op log keeps both writes."""
    t = await seed_tenant(db_session, code="DEDUP_SAME")
    u = await seed_user(db_session, t, email="same@dedup.test")
    await db_session.flush()

    layer = UserLayer(_shared_factory(db_session))  # type: ignore[arg-type]
    id1 = await layer.write(
        content="User likes dark mode.", tenant_id=t.id, user_id=u.id, confidence=0.7
    )
    # case + double-whitespace variant → SAME normalized dedup_key → upsert.
    id2 = await layer.write(
        content="user likes  DARK mode.", tenant_id=t.id, user_id=u.id, confidence=0.9
    )

    assert id1 == id2  # upsert returned the existing row id
    assert await _user_count(db_session, t.id) == 1  # one fact row, not two

    row = (
        await db_session.execute(select(MemoryUser).where(MemoryUser.tenant_id == t.id))
    ).scalar_one()
    assert float(row.confidence) == 0.9  # greatest(0.7, 0.9)
    assert row.content == "user likes  DARK mode."  # latest raw content
    assert row.dedup_key is not None

    # The append-only op log records BOTH writes (history is not deduped).
    op_count = (
        await db_session.execute(
            select(func.count()).select_from(MemoryOp).where(MemoryOp.tenant_id == t.id)
        )
    ).scalar_one()
    assert op_count == 2


async def test_lower_confidence_repeat_keeps_greatest(db_session: AsyncSession) -> None:
    """greatest() is symmetric: a lower-confidence repeat does not lower the row."""
    t = await seed_tenant(db_session, code="DEDUP_CONF")
    u = await seed_user(db_session, t, email="conf@dedup.test")
    await db_session.flush()

    layer = UserLayer(_shared_factory(db_session))  # type: ignore[arg-type]
    await layer.write(content="fact x", tenant_id=t.id, user_id=u.id, confidence=0.9)
    await layer.write(content="fact x", tenant_id=t.id, user_id=u.id, confidence=0.4)

    assert await _user_count(db_session, t.id) == 1
    row = (
        await db_session.execute(select(MemoryUser).where(MemoryUser.tenant_id == t.id))
    ).scalar_one()
    assert float(row.confidence) == 0.9  # not lowered to 0.4


async def test_distinct_facts_kept_separate(db_session: AsyncSession) -> None:
    """Two genuinely different facts → two rows (dedup is exact-normalized, not
    over-collapsing; semantic near-dup is CARRY-026, out of scope)."""
    t = await seed_tenant(db_session, code="DEDUP_DIFF")
    u = await seed_user(db_session, t, email="diff@dedup.test")
    await db_session.flush()

    layer = UserLayer(_shared_factory(db_session))  # type: ignore[arg-type]
    id1 = await layer.write(content="Chris works on Aurora", tenant_id=t.id, user_id=u.id)
    id2 = await layer.write(content="Chris prefers tables", tenant_id=t.id, user_id=u.id)

    assert id1 != id2
    assert await _user_count(db_session, t.id) == 2


async def test_dedup_key_is_per_tenant(db_session: AsyncSession) -> None:
    """The same content for two different tenants → one row each (the unique key is
    (tenant_id, user_id, dedup_key) — never collapses across tenants)."""
    t_a = await seed_tenant(db_session, code="DEDUP_T_A")
    t_b = await seed_tenant(db_session, code="DEDUP_T_B")
    u_a = await seed_user(db_session, t_a, email="a@dedup.test")
    u_b = await seed_user(db_session, t_b, email="b@dedup.test")
    await db_session.flush()

    layer = UserLayer(_shared_factory(db_session))  # type: ignore[arg-type]
    await layer.write(content="shared phrasing", tenant_id=t_a.id, user_id=u_a.id)
    await layer.write(content="shared phrasing", tenant_id=t_b.id, user_id=u_b.id)

    assert await _user_count(db_session, t_a.id) == 1
    assert await _user_count(db_session, t_b.id) == 1


async def test_long_term_no_expiry(db_session: AsyncSession) -> None:
    """Relocated from the unit test: long_term writes leave expires_at NULL."""
    t = await seed_tenant(db_session, code="DEDUP_LT")
    u = await seed_user(db_session, t, email="lt@dedup.test")
    await db_session.flush()

    layer = UserLayer(_shared_factory(db_session))  # type: ignore[arg-type]
    await layer.write(content="durable fact", tenant_id=t.id, user_id=u.id, time_scale="long_term")
    row = (
        await db_session.execute(select(MemoryUser).where(MemoryUser.tenant_id == t.id))
    ).scalar_one()
    assert row.expires_at is None


async def test_short_term_sets_24h_expiry(db_session: AsyncSession) -> None:
    """Relocated from the unit test: short_term writes set expires_at ≈ now + 24h."""
    t = await seed_tenant(db_session, code="DEDUP_ST")
    u = await seed_user(db_session, t, email="st@dedup.test")
    await db_session.flush()

    before = datetime.now(timezone.utc)
    layer = UserLayer(_shared_factory(db_session))  # type: ignore[arg-type]
    await layer.write(content="working note", tenant_id=t.id, user_id=u.id, time_scale="short_term")
    row = (
        await db_session.execute(select(MemoryUser).where(MemoryUser.tenant_id == t.id))
    ).scalar_one()
    assert row.expires_at is not None
    delta = row.expires_at - before
    assert timedelta(hours=23, minutes=55) < delta < timedelta(hours=24, minutes=5)
