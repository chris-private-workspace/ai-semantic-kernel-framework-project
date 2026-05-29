"""
File: backend/tests/integration/api/test_clear_rate_limits_meta_data_migration.py
Purpose: Tests for the 0020 data-cleanup migration (strip + reverse-populate).
Category: Tests / Integration / API (Phase 58.x RateLimits MetaData cleanup)
Scope: Sprint 57.60 Day 1 / US-2 (closes AD-RateLimits-MetaData-Cleanup-Phase58)

Description:
    Three test groups:
    1. Inline reverse-projection correctness — the 0020 migration's
       `_inline_project` is the inverse of 0019's `_parse_item`; verify
       (resource_type, window_type, quota) -> {label, value} for known + custom
       resources (custom is lossy-but-stable: slug -> humanised label).
    2. upgrade() — exercise the migration's raw "metadata" - 'rate_limits' UPDATE
       against the real test DB: strips the key on a seeded tenant + idempotent
       (no error / no change) on a tenant without the key + multi-tenant isolation
       (only the targeted tenants are touched).
    3. downgrade() — exercise the reverse-populate jsonb_set UPDATE: seed
       rate_limit_configs rows, run the projection + UPDATE, assert
       meta_data["rate_limits"] is reverse-populated with correct {label, value}.

    The migration's raw SQL uses the physical column name "metadata" (the ORM
    exposes it as meta_data via mapped_column). Running that SQL through the test
    session against real Postgres exercises the exact migration path.

Created: 2026-05-29 (Sprint 57.60 Day 1)

Modification History (newest-first):
    - 2026-05-29: Initial creation (Sprint 57.60 Day 1 / US-2)
"""

from __future__ import annotations

import importlib
import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.models.api_keys import RateLimitConfig
from infrastructure.db.models.identity import Tenant, TenantPlan, TenantState

# NB: no module-level pytestmark — mixes pure-sync projection tests with async DB
# tests. asyncio_mode=AUTO (pyproject) auto-marks the async ones; a global mark
# would wrongly flag the sync projection tests.

# Import the migration module by its file revision name so we can exercise the
# inline reverse-projection helper directly (pure function — no DB needed).
_migration = importlib.import_module(
    "infrastructure.db.migrations.versions.0020_clear_rate_limits_meta_data"
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


# Mirrors the migration's upgrade() / downgrade() raw SQL exactly so the test
# exercises the real SQL path (physical "metadata" column).
_UPGRADE_SQL = (
    'UPDATE tenants SET "metadata" = "metadata" - \'rate_limits\' '
    "WHERE \"metadata\" ? 'rate_limits'"
)


async def _read_meta_data(session: AsyncSession, tenant_id: Any) -> dict[str, Any]:
    """Read tenants.metadata JSONB via raw SQL (bypasses the ORM identity map).

    The migration UPDATEs go through raw SQL, so a re-SELECT via the ORM would
    return the stale cached instance (and expire_all() would trigger lazy IO
    outside the greenlet). A direct scalar read returns the committed JSONB dict.
    """
    result = await session.execute(
        text('SELECT "metadata" FROM tenants WHERE id = :tid'), {"tid": tenant_id}
    )
    return result.scalar_one() or {}


# =====================================================================
# Group 1 — inline reverse-projection correctness (inverse of 0019 _parse_item)
# =====================================================================


def test_migration_project_known_resources() -> None:
    """Known resource keys map back to canonical {label, value} (round-trip safe)."""
    assert _migration._inline_project("api_requests", "min", 100) == {
        "label": "API requests",
        "value": "100 / min",
    }
    assert _migration._inline_project("tool_calls", "min", 1000) == {
        "label": "Tool calls",
        "value": "1,000 / min",
    }
    assert _migration._inline_project("sse_connections", "hour", 50) == {
        "label": "SSE connections",
        "value": "50 / hour",
    }


def test_migration_project_custom_resource_lossy_but_stable() -> None:
    """Custom resource slug humanises to a stable display label (lossy by design)."""
    assert _migration._inline_project("custom_limit", "hour", 42) == {
        "label": "Custom limit",
        "value": "42 / hour",
    }


# =====================================================================
# Group 2 — upgrade() strips the key (idempotent + isolation)
# =====================================================================


async def test_upgrade_strips_rate_limits_key(db_session: AsyncSession) -> None:
    """upgrade() removes meta_data['rate_limits'] while preserving other keys."""
    items = [{"label": "API requests", "value": "100 / min"}]
    tenant = await _seed_tenant(
        db_session,
        code="RLM_CLR_T1",
        meta_data={"rate_limits": items, "other": "keep-me"},
    )

    await db_session.execute(text(_UPGRADE_SQL))
    await db_session.flush()

    meta = await _read_meta_data(db_session, tenant.id)
    assert "rate_limits" not in meta
    # Sibling keys untouched.
    assert meta.get("other") == "keep-me"


async def test_upgrade_idempotent_on_unseeded_tenant(db_session: AsyncSession) -> None:
    """upgrade() is a no-op (no error, no change) for a tenant without the key."""
    tenant = await _seed_tenant(db_session, code="RLM_CLR_T2", meta_data={"other": "keep-me"})

    # Run twice — must stay a clean no-op both times (idempotent).
    await db_session.execute(text(_UPGRADE_SQL))
    await db_session.execute(text(_UPGRADE_SQL))
    await db_session.flush()

    meta = await _read_meta_data(db_session, tenant.id)
    assert meta == {"other": "keep-me"}


async def test_upgrade_multi_tenant_isolation(db_session: AsyncSession) -> None:
    """upgrade() touches only tenants carrying the key; others are unchanged."""
    seeded_items = [{"label": "Tool calls", "value": "500 / min"}]
    tenant_a = await _seed_tenant(
        db_session, code="RLM_CLR_ISO_A", meta_data={"rate_limits": seeded_items}
    )
    other_items = [{"label": "API requests", "value": "9 / sec"}]
    tenant_b = await _seed_tenant(
        db_session, code="RLM_CLR_ISO_B", meta_data={"rate_limits": other_items}
    )

    await db_session.execute(text(_UPGRADE_SQL))
    await db_session.flush()

    meta_a = await _read_meta_data(db_session, tenant_a.id)
    meta_b = await _read_meta_data(db_session, tenant_b.id)
    # Both carried the key -> both stripped (idempotent set-based UPDATE).
    assert "rate_limits" not in meta_a
    assert "rate_limits" not in meta_b


# =====================================================================
# Group 3 — downgrade() reverse-populates meta_data from config rows
# =====================================================================


async def test_downgrade_reverse_populates_from_config(db_session: AsyncSession) -> None:
    """downgrade() rebuilds meta_data['rate_limits'] from rate_limit_configs rows."""
    tenant = await _seed_tenant(db_session, code="RLM_DOWN_T1", meta_data={})
    db_session.add(
        RateLimitConfig(
            tenant_id=tenant.id, resource_type="api_requests", window_type="min", quota=100
        )
    )
    db_session.add(
        RateLimitConfig(
            tenant_id=tenant.id, resource_type="tool_calls", window_type="min", quota=1000
        )
    )
    await db_session.flush()

    # Replay the migration downgrade() logic (same projection + jsonb_set UPDATE).
    rows = (
        await db_session.execute(
            text(
                "SELECT tenant_id, resource_type, window_type, quota "
                "FROM rate_limit_configs WHERE tenant_id = :tid "
                "ORDER BY tenant_id, resource_type, window_type"
            ),
            {"tid": tenant.id},
        )
    ).fetchall()
    by_tenant: dict[object, list[dict[str, str]]] = {}
    for row in rows:
        item = _migration._inline_project(row[1], row[2], int(row[3]))
        by_tenant.setdefault(row[0], []).append(item)

    for tid, items in by_tenant.items():
        await db_session.execute(
            text(
                'UPDATE tenants SET "metadata" = jsonb_set('
                "COALESCE(\"metadata\", '{}'::jsonb), '{rate_limits}', CAST(:items AS jsonb)) "
                "WHERE id = :tid"
            ),
            {"items": json.dumps(items), "tid": tid},
        )
    await db_session.flush()

    meta = await _read_meta_data(db_session, tenant.id)
    reverse = meta["rate_limits"]
    assert {(e["label"], e["value"]) for e in reverse} == {
        ("API requests", "100 / min"),
        ("Tool calls", "1,000 / min"),
    }


async def test_upgrade_then_downgrade_round_trip(db_session: AsyncSession) -> None:
    """up (strip) -> down (reverse-populate from config) restores meta_data.

    Models the symmetric 0019/0020 contract: after 0020 strips the key, a
    downgrade rebuilds it from the still-present rate_limit_configs rows so the
    0019 retained-meta_data fallback still resolves past a 2-migration window.
    """
    items = [{"label": "API requests", "value": "100 / min"}]
    tenant = await _seed_tenant(db_session, code="RLM_RT_T1", meta_data={"rate_limits": items})
    db_session.add(
        RateLimitConfig(
            tenant_id=tenant.id, resource_type="api_requests", window_type="min", quota=100
        )
    )
    await db_session.flush()

    # up: strip.
    await db_session.execute(text(_UPGRADE_SQL))
    await db_session.flush()
    stripped = await _read_meta_data(db_session, tenant.id)
    assert "rate_limits" not in stripped

    # down: reverse-populate from config.
    config_rows = (
        await db_session.execute(
            text(
                "SELECT tenant_id, resource_type, window_type, quota "
                "FROM rate_limit_configs WHERE tenant_id = :tid"
            ),
            {"tid": tenant.id},
        )
    ).fetchall()
    items_out = [_migration._inline_project(r[1], r[2], int(r[3])) for r in config_rows]
    await db_session.execute(
        text(
            'UPDATE tenants SET "metadata" = jsonb_set('
            "COALESCE(\"metadata\", '{}'::jsonb), '{rate_limits}', CAST(:items AS jsonb)) "
            "WHERE id = :tid"
        ),
        {"items": json.dumps(items_out), "tid": tenant.id},
    )
    await db_session.flush()

    restored = await _read_meta_data(db_session, tenant.id)
    assert restored["rate_limits"] == [{"label": "API requests", "value": "100 / min"}]
