"""
File: backend/tests/integration/api/test_rate_limit_alert_store.py
Purpose: Tests for RateLimitAlertStore — 80%-threshold detection + idempotent upsert + list.
Category: Tests / Integration / API (Phase 58.x RateLimits usage alerting)
Scope: Sprint 57.62 Track A / US-1 (RateLimits 80% usage alerting)

Description:
    Exercises RateLimitAlertStore.maybe_record + list_recent against the real test
    DB (rate_limit_alerts table). Covers the threshold boundary (>=80 records,
    <80 skips), severity mapping (warning / critical at 100), the no-op guards
    (quota <= 0 — no row, no ZeroDivision), the idempotent per-window upsert
    (dedup + peak actual_pct + escalation + triggered_at preserved), list ordering
    + limit cap, and store-level multi-tenant isolation.

    The test DB role bypasses RLS (superuser), so — like the sibling config-store
    tests — no per-session tenant context is set; isolation is asserted at the
    application query level (list_recent scoped by tenant_id). db_session rolls
    back at teardown so uncommitted rows never leak across tests.

Created: 2026-05-29 (Sprint 57.62 Track A)

Modification History (newest-first):
    - 2026-05-29: Initial creation (Sprint 57.62 Track A / US-1)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.models.api_keys import RateLimitAlert
from infrastructure.db.models.identity import Tenant, TenantPlan, TenantState
from platform_layer.tenant.rate_limit_alert_store import (
    ALERT_THRESHOLD_PCT,
    RateLimitAlertStore,
    _severity,
)

# NB: no module-level pytestmark — this file mixes a pure-sync severity test with
# async DB tests. asyncio_mode=AUTO (pyproject) auto-marks the async ones; a
# global asyncio mark would wrongly flag the sync test (mirrors the sibling
# test_rate_limit_config_migration.py convention).


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


def _window(offset_seconds: int = 0) -> datetime:
    """A deterministic timezone-aware window_start anchored away from 'now'."""
    base = datetime(2026, 5, 29, 12, 0, 0, tzinfo=timezone.utc)
    return base + timedelta(seconds=offset_seconds)


async def _alerts_for(session: AsyncSession, tenant_id: UUID) -> list[RateLimitAlert]:
    result = await session.execute(
        select(RateLimitAlert).where(RateLimitAlert.tenant_id == tenant_id)
    )
    return list(result.scalars().all())


# =====================================================================
# Pure severity / threshold helper
# =====================================================================


def test_severity_mapping() -> None:
    """_severity: >=100 critical, 80-99 warning (lowercase, SLAViolation parity)."""
    assert _severity(80) == "warning"
    assert _severity(99) == "warning"
    assert _severity(100) == "critical"
    assert _severity(105) == "critical"
    assert ALERT_THRESHOLD_PCT == 80


# =====================================================================
# maybe_record — threshold boundary + severity
# =====================================================================


async def test_record_at_80_creates_warning(db_session: AsyncSession) -> None:
    """Exactly 80% crosses the threshold → 1 row, severity 'warning'."""
    tenant = await _seed_tenant(db_session, code="RLA_80_T1")
    store = RateLimitAlertStore()
    await store.maybe_record(
        db_session,
        tenant.id,
        "api_requests",
        "min",
        used=80,
        quota=100,
        window_start=_window(),
    )
    await db_session.flush()
    rows = await _alerts_for(db_session, tenant.id)
    assert len(rows) == 1
    assert rows[0].actual_pct == 80
    assert rows[0].threshold_pct == 80
    assert rows[0].severity == "warning"
    assert rows[0].used == 80
    assert rows[0].quota == 100


async def test_record_at_90_warning(db_session: AsyncSession) -> None:
    """90% → severity 'warning' (still below 100)."""
    tenant = await _seed_tenant(db_session, code="RLA_90_T1")
    store = RateLimitAlertStore()
    await store.maybe_record(
        db_session, tenant.id, "tool_calls", "hour", used=90, quota=100, window_start=_window()
    )
    await db_session.flush()
    rows = await _alerts_for(db_session, tenant.id)
    assert len(rows) == 1
    assert rows[0].actual_pct == 90
    assert rows[0].severity == "warning"


async def test_record_at_100_critical(db_session: AsyncSession) -> None:
    """100% → severity 'critical'."""
    tenant = await _seed_tenant(db_session, code="RLA_100_T1")
    store = RateLimitAlertStore()
    await store.maybe_record(
        db_session, tenant.id, "api_requests", "min", used=100, quota=100, window_start=_window()
    )
    await db_session.flush()
    rows = await _alerts_for(db_session, tenant.id)
    assert len(rows) == 1
    assert rows[0].actual_pct == 100
    assert rows[0].severity == "critical"


async def test_record_below_threshold_no_row(db_session: AsyncSession) -> None:
    """79% is below 80% → no row written."""
    tenant = await _seed_tenant(db_session, code="RLA_79_T1")
    store = RateLimitAlertStore()
    await store.maybe_record(
        db_session, tenant.id, "api_requests", "min", used=79, quota=100, window_start=_window()
    )
    await db_session.flush()
    assert await _alerts_for(db_session, tenant.id) == []


async def test_record_quota_zero_no_row_no_zerodivision(db_session: AsyncSession) -> None:
    """quota=0 → no row + no ZeroDivisionError (guard before the pct compute)."""
    tenant = await _seed_tenant(db_session, code="RLA_Q0_T1")
    store = RateLimitAlertStore()
    # Must not raise.
    await store.maybe_record(
        db_session, tenant.id, "api_requests", "min", used=10, quota=0, window_start=_window()
    )
    await db_session.flush()
    assert await _alerts_for(db_session, tenant.id) == []


# =====================================================================
# maybe_record — idempotent per-window upsert (dedup / peak / escalation / time)
# =====================================================================


async def test_record_dedup_same_window_keeps_peak(db_session: AsyncSession) -> None:
    """85% then 95% in the SAME window → 1 row, actual_pct=95 (peak), used updated."""
    tenant = await _seed_tenant(db_session, code="RLA_DEDUP_T1")
    store = RateLimitAlertStore()
    win = _window()
    await store.maybe_record(
        db_session, tenant.id, "api_requests", "min", used=85, quota=100, window_start=win
    )
    await db_session.flush()
    await store.maybe_record(
        db_session, tenant.id, "api_requests", "min", used=95, quota=100, window_start=win
    )
    await db_session.flush()
    rows = await _alerts_for(db_session, tenant.id)
    assert len(rows) == 1  # same window → upserted, not duplicated
    assert rows[0].actual_pct == 95  # peak
    assert rows[0].used == 95  # latest snapshot
    assert rows[0].severity == "warning"


async def test_record_peak_preserved_when_usage_drops(db_session: AsyncSession) -> None:
    """95% then 85% same window → actual_pct stays 95 (GREATEST peak, not last-write)."""
    tenant = await _seed_tenant(db_session, code="RLA_PEAK_T1")
    store = RateLimitAlertStore()
    win = _window()
    await store.maybe_record(
        db_session, tenant.id, "api_requests", "min", used=95, quota=100, window_start=win
    )
    await db_session.flush()
    await store.maybe_record(
        db_session, tenant.id, "api_requests", "min", used=85, quota=100, window_start=win
    )
    await db_session.flush()
    rows = await _alerts_for(db_session, tenant.id)
    assert len(rows) == 1
    assert rows[0].actual_pct == 95  # peak preserved


async def test_record_escalation_to_critical(db_session: AsyncSession) -> None:
    """85% then 105% same window → severity escalates to 'critical', actual_pct=105."""
    tenant = await _seed_tenant(db_session, code="RLA_ESC_T1")
    store = RateLimitAlertStore()
    win = _window()
    await store.maybe_record(
        db_session, tenant.id, "api_requests", "min", used=85, quota=100, window_start=win
    )
    await db_session.flush()
    await store.maybe_record(
        db_session, tenant.id, "api_requests", "min", used=105, quota=100, window_start=win
    )
    await db_session.flush()
    rows = await _alerts_for(db_session, tenant.id)
    assert len(rows) == 1
    assert rows[0].actual_pct == 105
    assert rows[0].severity == "critical"


async def test_record_triggered_at_unchanged_on_conflict(db_session: AsyncSession) -> None:
    """A second crossing in the same window does NOT bump triggered_at (birth time kept)."""
    tenant = await _seed_tenant(db_session, code="RLA_TIME_T1")
    store = RateLimitAlertStore()
    win = _window()
    await store.maybe_record(
        db_session, tenant.id, "api_requests", "min", used=82, quota=100, window_start=win
    )
    await db_session.flush()
    first = (await _alerts_for(db_session, tenant.id))[0]
    first_triggered = first.triggered_at

    await store.maybe_record(
        db_session, tenant.id, "api_requests", "min", used=99, quota=100, window_start=win
    )
    await db_session.flush()
    await db_session.refresh(first)
    assert first.triggered_at == first_triggered  # unchanged


# =====================================================================
# list_recent — ordering + limit + isolation
# =====================================================================


async def test_list_recent_newest_first_and_limit(db_session: AsyncSession) -> None:
    """list_recent returns newest-first (by triggered_at) and respects the limit cap."""
    tenant = await _seed_tenant(db_session, code="RLA_LIST_T1")
    store = RateLimitAlertStore()
    base = datetime(2026, 5, 1, 0, 0, 0, tzinfo=timezone.utc)
    # Seed 5 distinct-window alerts with explicit ascending triggered_at.
    for i in range(5):
        db_session.add(
            RateLimitAlert(
                tenant_id=tenant.id,
                resource_type=f"res_{i}",
                window_type="min",
                threshold_pct=80,
                actual_pct=80 + i,
                used=80 + i,
                quota=100,
                severity="warning",
                window_start=base + timedelta(minutes=i),
                triggered_at=base + timedelta(minutes=i),
            )
        )
    await db_session.flush()

    rows = await store.list_recent(db_session, tenant.id, limit=3)
    assert len(rows) == 3  # limit cap
    # Newest-first: res_4 (latest triggered_at) leads.
    assert [r.resource_type for r in rows] == ["res_4", "res_3", "res_2"]


async def test_list_recent_multi_tenant_isolation(db_session: AsyncSession) -> None:
    """Tenant A's alert is NOT visible in tenant B's list_recent (scoped by tenant_id)."""
    tenant_a = await _seed_tenant(db_session, code="RLA_ISO_A")
    tenant_b = await _seed_tenant(db_session, code="RLA_ISO_B")
    store = RateLimitAlertStore()
    await store.maybe_record(
        db_session, tenant_a.id, "api_requests", "min", used=88, quota=100, window_start=_window()
    )
    await db_session.flush()

    rows_a = await store.list_recent(db_session, tenant_a.id)
    rows_b = await store.list_recent(db_session, tenant_b.id)
    assert {r.resource_type for r in rows_a} == {"api_requests"}
    assert rows_b == []
