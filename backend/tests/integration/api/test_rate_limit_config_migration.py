"""
File: backend/tests/integration/api/test_rate_limit_config_migration.py
Purpose: Tests for the 0019 data migration parse logic + RateLimitConfig ORM CRUD/RLS.
Category: Tests / Integration / API (Phase 58.x RateLimits Potemkin close)
Scope: Sprint 57.59 Day 1 / US-1 (closes AD-RateLimits-Potemkin-Migration-Phase58)

Description:
    Two test groups:
    1. Migration inline-parse correctness — the 0019 migration's `_parse_item`
       mirrors parse_rate_limit_item; verify {label, value} -> (resource_type,
       window_type, quota) and that unparseable items are skipped (None).
    2. RateLimitConfig ORM — CRUD via the table, unique constraint on
       (tenant_id, resource_type, window_type), and store-level multi-tenant
       isolation (list_configs scoped by tenant_id never leaks another tenant's
       rows — the application-level isolation pattern used across these tests).

    Data-migration correctness is exercised by replaying the migration's parse +
    insert path (seed meta_data shape -> parse -> insert config rows -> verify),
    matching the migration's de-dup-last-wins + skip-unparseable behaviour.

Created: 2026-05-28 (Sprint 57.59 Day 1)

Modification History (newest-first):
    - 2026-05-28: Initial creation (Sprint 57.59 Day 1 / US-1)
"""

from __future__ import annotations

import importlib
from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.models.api_keys import RateLimitConfig
from infrastructure.db.models.identity import Tenant, TenantPlan, TenantState
from platform_layer.tenant.rate_limit_config_store import RateLimitConfigStore

# NB: no module-level pytestmark — this file mixes pure-sync parse tests with
# async DB tests. asyncio_mode=AUTO (pyproject) auto-marks the async ones; a
# global asyncio mark would wrongly flag the sync parse tests.

# Import the migration module by its file revision name so we can exercise the
# inline parse helper directly (pure function — no DB needed).
_migration = importlib.import_module(
    "infrastructure.db.migrations.versions.0019_rate_limit_configs"
)


async def _seed_tenant(
    session: AsyncSession,
    *,
    code: str,
    meta_data: dict[str, Any] | None = None,
) -> Tenant:
    t = Tenant(
        code=code,
        display_name=f"Tenant {code}",
        state=TenantState.ACTIVE,
        plan=TenantPlan.ENTERPRISE,
        meta_data=meta_data or {},
    )
    session.add(t)
    await session.flush()
    await session.refresh(t)
    return t


# =====================================================================
# Group 1 — migration inline-parse correctness
# =====================================================================


def test_migration_parse_known_resources() -> None:
    """Known labels map to canonical resource_type + canonical window_type + quota."""
    assert _migration._parse_item({"label": "API requests", "value": "100 / min"}) == (
        "api_requests",
        "min",
        100,
    )
    assert _migration._parse_item({"label": "Tool calls", "value": "1,000 / minute"}) == (
        "tool_calls",
        "min",
        1000,
    )
    assert _migration._parse_item({"label": "Custom limit", "value": "42 / hour"}) == (
        "custom_limit",
        "hour",
        42,
    )


def test_migration_parse_skips_unparseable() -> None:
    """Non-rate / malformed / non-positive / non-dict items return None (skipped)."""
    assert _migration._parse_item({"label": "SSE connections", "value": "50 concurrent"}) is None
    assert _migration._parse_item({"label": "", "value": "10 / min"}) is None
    assert _migration._parse_item({"label": "X", "value": "0 / min"}) is None
    assert _migration._parse_item({"label": "X", "value": "garbage"}) is None
    assert _migration._parse_item("not a dict") is None
    assert _migration._parse_item({"label": "X", "value": "10 / fortnight"}) is None


# =====================================================================
# Group 2 — RateLimitConfig ORM CRUD / unique / isolation + data migration replay
# =====================================================================


async def test_config_table_crud(db_session: AsyncSession) -> None:
    """Insert + read back a config row via the store (table is wired, not Potemkin)."""
    tenant = await _seed_tenant(db_session, code="RLC_CRUD_T1")
    db_session.add(
        RateLimitConfig(
            tenant_id=tenant.id,
            resource_type="api_requests",
            window_type="min",
            quota=100,
        )
    )
    await db_session.flush()

    store = RateLimitConfigStore()
    rows = await store.list_configs(db_session, tenant.id)
    assert len(rows) == 1
    assert rows[0].resource_type == "api_requests"
    assert rows[0].window_type == "min"
    assert rows[0].quota == 100


async def test_config_table_unique_constraint(db_session: AsyncSession) -> None:
    """Duplicate (tenant_id, resource_type, window_type) violates the unique constraint."""
    tenant = await _seed_tenant(db_session, code="RLC_UNIQ_T1")
    db_session.add(
        RateLimitConfig(
            tenant_id=tenant.id, resource_type="api_requests", window_type="min", quota=100
        )
    )
    await db_session.flush()
    db_session.add(
        RateLimitConfig(
            tenant_id=tenant.id, resource_type="api_requests", window_type="min", quota=999
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_config_store_tenant_isolation(db_session: AsyncSession) -> None:
    """list_configs is scoped by tenant_id — tenant_b never sees tenant_a's rows."""
    tenant_a = await _seed_tenant(db_session, code="RLC_ISO_A")
    tenant_b = await _seed_tenant(db_session, code="RLC_ISO_B")
    db_session.add(
        RateLimitConfig(
            tenant_id=tenant_a.id, resource_type="api_requests", window_type="min", quota=100
        )
    )
    db_session.add(
        RateLimitConfig(
            tenant_id=tenant_b.id, resource_type="tool_calls", window_type="hour", quota=7
        )
    )
    await db_session.flush()

    store = RateLimitConfigStore()
    rows_a = await store.list_configs(db_session, tenant_a.id)
    rows_b = await store.list_configs(db_session, tenant_b.id)
    assert {r.resource_type for r in rows_a} == {"api_requests"}
    assert {r.resource_type for r in rows_b} == {"tool_calls"}


async def test_data_migration_replay_seeds_config_rows(db_session: AsyncSession) -> None:
    """Replay the migration parse+insert path: meta_data items -> config rows.

    Mirrors 0019 upgrade()'s additive seed (parse each item, de-dup last-wins,
    insert), and asserts unparseable items are skipped and meta_data is retained.
    """
    items = [
        {"label": "API requests", "value": "100 / min"},
        {"label": "Tool calls", "value": "1,000 / min"},
        {"label": "SSE connections", "value": "50 concurrent"},  # unparseable -> skip
    ]
    tenant = await _seed_tenant(db_session, code="RLC_MIG_T1", meta_data={"rate_limits": items})

    # Replay the migration's parse + de-dup + insert (same logic as 0019 upgrade()).
    deduped: dict[tuple[str, str], int] = {}
    for item in items:
        parsed = _migration._parse_item(item)
        if parsed is None:
            continue
        rt, wt, q = parsed
        deduped[(rt, wt)] = q
    for (rt, wt), q in deduped.items():
        db_session.add(
            RateLimitConfig(tenant_id=tenant.id, resource_type=rt, window_type=wt, quota=q)
        )
    await db_session.flush()

    rows = (
        (
            await db_session.execute(
                select(RateLimitConfig).where(RateLimitConfig.tenant_id == tenant.id)
            )
        )
        .scalars()
        .all()
    )
    # 2 parseable items seeded; "50 concurrent" skipped.
    assert {(r.resource_type, r.window_type, r.quota) for r in rows} == {
        ("api_requests", "min", 100),
        ("tool_calls", "min", 1000),
    }
    # meta_data retained (additive migration — no delete).
    row = (await db_session.execute(select(Tenant).where(Tenant.id == tenant.id))).scalar_one()
    assert row.meta_data["rate_limits"] == items
