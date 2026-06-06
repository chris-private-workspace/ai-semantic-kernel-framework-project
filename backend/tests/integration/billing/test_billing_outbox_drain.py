"""
File: backend/tests/integration/billing/test_billing_outbox_drain.py
Purpose: BillingOutboxDrainer integration (Sprint 57.84 / US-3 + US-4) — real Postgres.
Category: Tests / Integration (platform_layer.billing)
Created: 2026-06-05 (Sprint 57.84 Day 2)

Why integration (not unit): the drainer uses its OWN session factory (one
independent transaction per row, with commits + FOR UPDATE SKIP LOCKED), so it
can only see COMMITTED outbox rows. These tests therefore commit seed data via
_get_factory() and clean up by deleting the test tenant's rows in a
finally / fixture teardown (db_session's rollback can't reach committed data).
Proves the drainer end-to-end BEFORE Day-3 wires it into the lifespan.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from core.config import get_settings
from infrastructure.db.models import Tenant
from infrastructure.db.models.billing_outbox import BillingOutboxEvent
from infrastructure.db.models.cost_ledger import CostLedger
from platform_layer.billing.billing_outbox import (
    SYSTEM_SENTINEL_TENANT,
    BillingOutboxDrainer,
    BillingOutboxService,
    llm_idempotency_key,
)
from platform_layer.billing.pricing import PricingLoader

pytestmark = pytest.mark.asyncio

# Sprint 57.84: a dedicated NullPool engine isolates this module's heavy direct-
# session churn (the drainer opens a session per row + the helpers commit seed
# data) from the global pooled engine. NullPool closes each connection on session
# return → nothing lingers to be GC'd on a closed event loop, which would raise
# asyncpg's "_cancel never awaited / Event loop is closed" unraisable and fail an
# unrelated test. Disposed in the fixture / test finally.
_engine: AsyncEngine | None = None


def _get_factory() -> async_sessionmaker[AsyncSession]:
    global _engine
    if _engine is None:
        _engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
    return async_sessionmaker(_engine, expire_on_commit=False)


async def _dispose() -> None:
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None


_PRICING_YAML = Path(__file__).resolve().parents[3] / "config" / "llm_pricing.yml"

_LLM_PAYLOAD: dict[str, object] = {
    "provider": "azure_openai",
    "model": "gpt-5.4",
    "input_tokens": 600,
    "output_tokens": 400,
    "cached_input_tokens": 0,
    "sub_type_suffix": "",
}


def _loader() -> PricingLoader:
    pl = PricingLoader()
    pl.load_from_yaml(_PRICING_YAML)
    return pl


async def _commit_tenant(code: str) -> UUID:
    factory = _get_factory()
    async with factory() as s:
        t = Tenant(code=code, display_name=code)
        s.add(t)
        await s.flush()
        tid = t.id
        await s.commit()
    return tid


async def _delete_tenant(tid: UUID) -> None:
    """Delete a tenant's committed billing_outbox + cost_ledger + tenant rows.

    Sets the tenant context so the deletes pass RLS whether or not the test
    role bypasses it (first USING branch matches tenant_id)."""
    factory = _get_factory()
    async with factory() as s:
        await s.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(tid)})
        await s.execute(delete(CostLedger).where(CostLedger.tenant_id == tid))
        await s.execute(delete(BillingOutboxEvent).where(BillingOutboxEvent.tenant_id == tid))
        await s.execute(delete(Tenant).where(Tenant.id == tid))
        await s.commit()


async def _enqueue_committed(
    tid: UUID,
    *,
    event_type: str,
    payload: dict[str, object],
    idempotency_key: str,
    session_id: UUID,
) -> None:
    factory = _get_factory()
    async with factory() as s:
        await s.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(tid)})
        await BillingOutboxService().enqueue(
            s,
            tenant_id=tid,
            event_type=event_type,
            payload=payload,
            idempotency_key=idempotency_key,
            session_id=session_id,
        )
        await s.commit()


async def _cost_rows(tid: UUID) -> list[CostLedger]:
    factory = _get_factory()
    async with factory() as s:
        await s.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(tid)})
        return list(
            (await s.execute(select(CostLedger).where(CostLedger.tenant_id == tid))).scalars().all()
        )


async def _outbox_rows(tid: UUID) -> list[BillingOutboxEvent]:
    factory = _get_factory()
    async with factory() as s:
        # sentinel context: the drainer-escape lets us read the row cross-tenant
        # (also the first USING branch would match tid — either works).
        await s.execute(
            text("SELECT set_config('app.tenant_id', :t, true)"),
            {"t": SYSTEM_SENTINEL_TENANT},
        )
        return list(
            (await s.execute(select(BillingOutboxEvent).where(BillingOutboxEvent.tenant_id == tid)))
            .scalars()
            .all()
        )


@pytest_asyncio.fixture
async def committed_tenant() -> AsyncIterator[UUID]:
    tid = await _commit_tenant(f"OBX_DR_{uuid4().hex[:8]}")
    try:
        yield tid
    finally:
        await _delete_tenant(tid)
        await _dispose()


async def test_drain_materializes_cost_ledger_parity(committed_tenant: UUID) -> None:
    """US-3 — drain materializes the SAME 2 cost_ledger rows a direct
    record_llm_call would, and marks the outbox row done."""
    tid = committed_tenant
    sid = uuid4()
    await _enqueue_committed(
        tid,
        event_type="llm_call",
        payload=_LLM_PAYLOAD,
        idempotency_key=llm_idempotency_key(sid, ""),
        session_id=sid,
    )

    stats = await BillingOutboxDrainer(_get_factory(), _loader()).drain_once()
    assert stats.claimed == 1
    assert stats.materialized == 1

    cost = await _cost_rows(tid)
    assert len(cost) == 2  # input + output split (parity with direct path)
    assert {r.sub_type for r in cost} == {
        "azure_openai_gpt-5.4_input",
        "azure_openai_gpt-5.4_output",
    }
    assert all(r.session_id == sid for r in cost)

    obx = await _outbox_rows(tid)
    assert len(obx) == 1
    assert obx[0].status == "done"
    assert obx[0].processed_at is not None


async def test_drain_is_idempotent_across_two_cycles(committed_tenant: UUID) -> None:
    """US-3 — running drain twice materializes exactly once (no 雙扣)."""
    tid = committed_tenant
    sid = uuid4()
    await _enqueue_committed(
        tid,
        event_type="llm_call",
        payload=_LLM_PAYLOAD,
        idempotency_key=llm_idempotency_key(sid, ""),
        session_id=sid,
    )
    drainer = BillingOutboxDrainer(_get_factory(), _loader())

    first = await drainer.drain_once()
    assert first.materialized == 1
    # Second cycle: the row is now `done` → not due → claims nothing.
    second = await drainer.drain_once()
    assert second.claimed == 0
    assert second.materialized == 0

    cost = await _cost_rows(tid)
    assert len(cost) == 2  # still 2, not 4 — exactly-once materialization


async def test_drain_reschedules_then_dead_letters_on_bad_payload(
    committed_tenant: UUID,
) -> None:
    """US-3 — a materialize failure (malformed payload) rolls back the cost
    write, bumps retry/backoff, and dead-letters after max_retry."""
    tid = committed_tenant
    sid = uuid4()
    # Missing "provider" → _payload_str raises → materialize fails → rollback.
    bad_payload: dict[str, object] = {"model": "gpt-5.4", "input_tokens": 1, "output_tokens": 1}
    await _enqueue_committed(
        tid,
        event_type="llm_call",
        payload=bad_payload,
        idempotency_key=llm_idempotency_key(sid, ""),
        session_id=sid,
    )

    # max_retry=1 → the first failure immediately dead-letters.
    stats = await BillingOutboxDrainer(_get_factory(), _loader(), max_retry=1).drain_once()
    assert stats.claimed == 1
    assert stats.dead_lettered == 1
    assert stats.materialized == 0

    obx = await _outbox_rows(tid)
    assert len(obx) == 1
    assert obx[0].status == "failed"
    assert obx[0].retry_count == 1
    assert obx[0].next_retry_at is None  # dead-letter → not re-claimed
    assert obx[0].last_error is not None

    # The failed materialize wrote NO cost rows (rolled back).
    assert await _cost_rows(tid) == []


async def test_drain_reschedules_with_backoff_when_retries_remain(
    committed_tenant: UUID,
) -> None:
    """US-3 — below max_retry, a failure reschedules (next_retry_at set, future)."""
    tid = committed_tenant
    sid = uuid4()
    bad_payload: dict[str, object] = {"model": "gpt-5.4"}
    await _enqueue_committed(
        tid,
        event_type="llm_call",
        payload=bad_payload,
        idempotency_key=llm_idempotency_key(sid, ""),
        session_id=sid,
    )

    stats = await BillingOutboxDrainer(_get_factory(), _loader(), max_retry=8).drain_once()
    assert stats.failed == 1
    assert stats.dead_lettered == 0

    obx = await _outbox_rows(tid)
    assert obx[0].status == "failed"
    assert obx[0].retry_count == 1
    assert obx[0].next_retry_at is not None  # rescheduled (not dead-lettered)


async def test_drain_two_tenants_scopes_cost_rows() -> None:
    """US-4 — the drainer materializes each row under its OWN tenant; no cross-leak."""
    tid_a = await _commit_tenant(f"OBX_DR_A_{uuid4().hex[:8]}")
    tid_b = await _commit_tenant(f"OBX_DR_B_{uuid4().hex[:8]}")
    try:
        sid_a, sid_b = uuid4(), uuid4()
        await _enqueue_committed(
            tid_a,
            event_type="llm_call",
            payload=_LLM_PAYLOAD,
            idempotency_key=llm_idempotency_key(sid_a, ""),
            session_id=sid_a,
        )
        await _enqueue_committed(
            tid_b,
            event_type="tool_call",
            payload={"tool_name": "salesforce_query"},
            idempotency_key=f"{sid_b}:tool:salesforce_query:0",
            session_id=sid_b,
        )

        stats = await BillingOutboxDrainer(_get_factory(), _loader()).drain_once()
        assert stats.materialized == 2

        cost_a = await _cost_rows(tid_a)
        cost_b = await _cost_rows(tid_b)
        # Tenant A got its 2 LLM rows; tenant B got its 1 tool row — no cross-leak.
        assert {r.cost_type for r in cost_a} == {"llm"}
        assert len(cost_a) == 2
        assert {r.cost_type for r in cost_b} == {"tool"}
        assert len(cost_b) == 1
        assert all(r.tenant_id == tid_a for r in cost_a)
        assert all(r.tenant_id == tid_b for r in cost_b)
    finally:
        await _delete_tenant(tid_a)
        await _delete_tenant(tid_b)
        await _dispose()
