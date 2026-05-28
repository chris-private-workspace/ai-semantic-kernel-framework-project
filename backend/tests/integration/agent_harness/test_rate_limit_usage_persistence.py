"""
File: backend/tests/integration/agent_harness/test_rate_limit_usage_persistence.py
Purpose: Integration tests — config-table read + usage write-through + Redis recovery (RateLimits).
Category: Tests / Integration / platform_layer.tenant (Phase 58.x RateLimits Potemkin close)
Scope: Sprint 57.59 Day 1 / US-3 (closes AD-RateLimits-Potemkin-Migration-Phase58)

Description:
    Exercises the US-3 re-point that activates the formerly-Potemkin rate_limits
    usage table (AP-4 close). Five behaviours, all against a real docker-compose
    PostgreSQL + a fakeredis-backed RedisRateLimitCounter:

    1. middleware reads config from the rate_limit_configs table (not meta_data)
    2. usage write-through creates the rate_limits row (window_start + window_end
       both populated — Day 0 D-DAY0-G) on first increment, then updates `used`
       on subsequent increments within the same window
    3. Redis-restart recovery seeds the counter from the table's `used` so the
       gate resumes from the persisted baseline instead of resetting to zero
    4. multi-tenant usage isolation: tenant A's usage row never leaks into the
       count the counter recovers for tenant B (per-tenant key + tenant_id row)

    The counter is constructed with session_factory=get_session_factory so its
    best-effort write-through / recovery commit to (and read from) the real DB.
    Tenants use UUID-suffixed RATE_USAGE_ codes so the api conftest sweep cleans
    them up (FK CASCADE from tenants drops their rate_limit_configs + rate_limits
    rows); a local fixture also clears the WORM-trigger-guarded usage rows.

Created: 2026-05-28 (Sprint 57.59 Day 1)

Modification History (newest-first):
    - 2026-05-28: Initial creation (Sprint 57.59 US-3 — usage persistence + recovery)
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
import pytest_asyncio
from fakeredis.aioredis import FakeRedis
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.engine import dispose_engine, get_session_factory
from infrastructure.db.models.api_keys import RateLimit, RateLimitConfig
from infrastructure.db.models.identity import Tenant, TenantPlan, TenantState
from platform_layer.middleware.rate_limit import RateLimitMiddleware
from platform_layer.tenant.rate_limit_counter import (
    RedisRateLimitCounter,
    reset_rate_limit_counter,
)

pytestmark = pytest.mark.asyncio


# UUID-suffixed so the api conftest `RATE_USAGE_%` sweep cleans these tenants up
# (FK CASCADE drops their rate_limit_configs + rate_limits rows). The seeded
# config + usage rows are COMMITTED so the counter's own session (write-through
# / recovery) can see them — committed rows leak past db_session rollback, hence
# the explicit cleanup.
def _code() -> str:
    return f"RATE_USAGE_{uuid.uuid4().hex[:12]}"


@pytest.fixture
def fake_redis() -> FakeRedis:
    return FakeRedis(decode_responses=False)


@pytest_asyncio.fixture(autouse=True)
async def _reset_counter() -> AsyncIterator[None]:
    reset_rate_limit_counter()
    yield
    reset_rate_limit_counter()


async def _set_tenant_ctx(session: AsyncSession, tenant_id: UUID) -> None:
    # set_config(..., is_local=true) — the bind-param form (SET LOCAL cannot take
    # $1 under asyncpg) per the correction_loop.py / RLS precedent.
    await session.execute(
        text("SELECT set_config('app.tenant_id', :tid, true)"), {"tid": str(tenant_id)}
    )


async def _commit_tenant_with_configs(
    *,
    code: str,
    configs: list[tuple[str, str, int]],
) -> UUID:
    """Create a tenant + COMMIT rate_limit_configs rows; return tenant_id.

    Configs are (resource_type, window_type, quota). Committed (not flushed) so
    the counter's own session + the middleware's own session can read them.
    """
    factory = get_session_factory()
    async with factory() as session:
        tenant = Tenant(
            code=code,
            display_name=f"Tenant {code}",
            state=TenantState.ACTIVE,
            plan=TenantPlan.ENTERPRISE,
            meta_data={},
        )
        session.add(tenant)
        await session.flush()
        tenant_id = tenant.id
        await _set_tenant_ctx(session, tenant_id)
        for resource_type, window_type, quota in configs:
            session.add(
                RateLimitConfig(
                    tenant_id=tenant_id,
                    resource_type=resource_type,
                    window_type=window_type,
                    quota=quota,
                )
            )
        await session.commit()
    await dispose_engine()
    return tenant_id


async def _read_usage_rows(tenant_id: UUID, resource: str) -> list[RateLimit]:
    factory = get_session_factory()
    async with factory() as session:
        await _set_tenant_ctx(session, tenant_id)
        result = await session.execute(
            select(RateLimit)
            .where(RateLimit.tenant_id == tenant_id, RateLimit.resource_type == resource)
            .order_by(RateLimit.window_end.desc())
        )
        rows = list(result.scalars().all())
    await dispose_engine()
    return rows


async def _seed_usage_row(
    *,
    tenant_id: UUID,
    resource: str,
    window_type: str,
    quota: int,
    used: int,
    window_seconds: int,
) -> None:
    """COMMIT a still-open rate_limits usage row (window_end in the future)."""
    now = datetime.now(tz=timezone.utc)
    start_s = (int(now.timestamp()) // window_seconds) * window_seconds
    window_start = datetime.fromtimestamp(start_s, tz=timezone.utc)
    window_end = window_start + timedelta(seconds=window_seconds)
    factory = get_session_factory()
    async with factory() as session:
        await _set_tenant_ctx(session, tenant_id)
        session.add(
            RateLimit(
                tenant_id=tenant_id,
                resource_type=resource,
                window_type=window_type,
                quota=quota,
                used=used,
                window_start=window_start,
                window_end=window_end,
            )
        )
        await session.commit()
    await dispose_engine()


# === Test 1: middleware reads config from the table ====================


async def test_middleware_loads_config_from_table() -> None:
    """_load_rate_limits returns the {label,value} projection of config rows."""
    tenant_id = await _commit_tenant_with_configs(
        code=_code(),
        configs=[("api_requests", "min", 100), ("tool_calls", "min", 1000)],
    )
    mw = RateLimitMiddleware(app=lambda *_: None)  # type: ignore[arg-type]
    items = await mw._load_rate_limits(tenant_id)
    # Projected back to {label, value}; both config rows surface.
    by_label = {i["label"]: i["value"] for i in items}  # type: ignore[index]
    assert by_label["API requests"] == "100 / min"
    assert by_label["Tool calls"] == "1,000 / min"


async def test_middleware_falls_back_to_meta_data_when_no_config_rows() -> None:
    """No config rows → fall back to tenant.meta_data['rate_limits']."""
    code = _code()
    factory = get_session_factory()
    async with factory() as session:
        tenant = Tenant(
            code=code,
            display_name=f"Tenant {code}",
            state=TenantState.ACTIVE,
            plan=TenantPlan.ENTERPRISE,
            meta_data={"rate_limits": [{"label": "API requests", "value": "7 / min"}]},
        )
        session.add(tenant)
        await session.flush()
        tenant_id = tenant.id
        await session.commit()
    await dispose_engine()

    mw = RateLimitMiddleware(app=lambda *_: None)  # type: ignore[arg-type]
    items = await mw._load_rate_limits(tenant_id)
    assert items == [{"label": "API requests", "value": "7 / min"}]


# === Test 2: usage write-through creates + updates the row =============


async def test_usage_write_through_creates_and_updates_row(fake_redis: FakeRedis) -> None:
    """check_and_increment write-throughs a rate_limits row (start+end) then updates used."""
    tenant_id = await _commit_tenant_with_configs(
        code=_code(), configs=[("api_requests", "min", 10)]
    )
    counter = RedisRateLimitCounter(fake_redis, session_factory=get_session_factory)

    # First increment → creates the usage row (used = 1).
    d1 = await counter.check_and_increment(tenant_id, "api_requests", 60, 10)
    assert d1.allowed is True
    rows = await _read_usage_rows(tenant_id, "api_requests")
    assert len(rows) == 1, "write-through must create exactly one row for the window"
    row = rows[0]
    assert row.window_type == "min"
    assert row.used == 1
    assert row.quota == 10  # denormalised config snapshot
    assert row.window_start is not None and row.window_end is not None
    # window_end = window_start + window_seconds (Day 0 D-DAY0-G).
    assert (row.window_end - row.window_start) == timedelta(seconds=60)

    # Second increment in the same window → updates the SAME row (used = 2).
    d2 = await counter.check_and_increment(tenant_id, "api_requests", 60, 10)
    assert d2.allowed is True
    rows = await _read_usage_rows(tenant_id, "api_requests")
    assert len(rows) == 1, "same-window increment must upsert, not insert a new row"
    assert rows[0].used == 2


# === Test 3: Redis-restart recovery seeds from the table ===============


async def test_redis_restart_recovery_seeds_counter_from_table(fake_redis: FakeRedis) -> None:
    """A fresh (empty) Redis recovers `used` from a still-open usage row."""
    tenant_id = await _commit_tenant_with_configs(
        code=_code(), configs=[("api_requests", "min", 10)]
    )
    # Simulate state from before a Redis restart: 4 used in the current window,
    # persisted in the table, but Redis (fakeredis) is empty.
    await _seed_usage_row(
        tenant_id=tenant_id,
        resource="api_requests",
        window_type="min",
        quota=10,
        used=4,
        window_seconds=60,
    )

    counter = RedisRateLimitCounter(fake_redis, session_factory=get_session_factory)
    # Next increment: recovery seeds 4 from the table, then this request makes 5.
    decision = await counter.check_and_increment(tenant_id, "api_requests", 60, 10)
    assert decision.allowed is True
    # remaining = limit - count = 10 - 5 = 5 (recovery baseline counted).
    assert decision.remaining == 5, "recovery must seed the persisted used baseline"


async def test_recovery_noop_when_no_open_window(fake_redis: FakeRedis) -> None:
    """No still-open usage row → recovery is a no-op; counter starts at zero."""
    tenant_id = await _commit_tenant_with_configs(
        code=_code(), configs=[("api_requests", "min", 10)]
    )
    counter = RedisRateLimitCounter(fake_redis, session_factory=get_session_factory)
    decision = await counter.check_and_increment(tenant_id, "api_requests", 60, 10)
    assert decision.allowed is True
    # No prior persisted window → this is request #1 → remaining = 9.
    assert decision.remaining == 9


# === Test 4: multi-tenant usage isolation ==============================


async def test_multi_tenant_usage_isolation(fake_redis: FakeRedis) -> None:
    """Tenant A's persisted usage never leaks into tenant B's recovered count."""
    tenant_a = await _commit_tenant_with_configs(
        code=_code(), configs=[("api_requests", "min", 10)]
    )
    tenant_b = await _commit_tenant_with_configs(
        code=_code(), configs=[("api_requests", "min", 10)]
    )
    # Tenant A: persist a near-exhausted window (used = 9).
    await _seed_usage_row(
        tenant_id=tenant_a,
        resource="api_requests",
        window_type="min",
        quota=10,
        used=9,
        window_seconds=60,
    )

    counter = RedisRateLimitCounter(fake_redis, session_factory=get_session_factory)
    # Tenant B has NO usage row → recovery seeds nothing → request #1 → remaining 9.
    decision_b = await counter.check_and_increment(tenant_b, "api_requests", 60, 10)
    assert decision_b.allowed is True
    assert decision_b.remaining == 9, "tenant B must not inherit tenant A's usage"

    # Tenant A's write-through row is scoped to tenant A only.
    a_rows = await _read_usage_rows(tenant_a, "api_requests")
    b_rows = await _read_usage_rows(tenant_b, "api_requests")
    assert all(r.tenant_id == tenant_a for r in a_rows)
    assert all(r.tenant_id == tenant_b for r in b_rows)
    # Tenant B never sees tenant A's used=9 row.
    assert all(r.used != 9 or r.tenant_id == tenant_a for r in b_rows)
