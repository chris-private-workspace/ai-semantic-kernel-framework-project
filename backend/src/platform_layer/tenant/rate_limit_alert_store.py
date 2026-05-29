"""
File: backend/src/platform_layer/tenant/rate_limit_alert_store.py
Purpose: RateLimitAlertStore — idempotent 80%-threshold usage-alert log writer/reader.
Category: Phase 58.x SaaS / platform_layer.tenant
Scope: Sprint 57.62 (Track A) — RateLimits 80% usage alerting

Description:
    Durable alert store backing the runtime threshold detector + the admin recent-
    alerts GET endpoint. The runtime counter (rate_limit_counter._write_through)
    calls maybe_record at the enforcement point so a tenant crossing 80% of its
    configured quota for a (resource, window) is captured even when no admin is
    watching the live-usage endpoint.

    STATELESS (no constructor DI): the caller passes the AsyncSession already in
    scope (the counter's own write-through session, which has the tenant context
    set for the rate_limits RLS policies — the same session services the alert
    INSERT under the rate_limit_alerts RLS policies). The store owns no connection
    lifecycle; the caller controls commit (the counter commits its write-through
    transaction, persisting the alert too).

    Idempotent per window instance: maybe_record upserts on the unique
    (tenant_id, resource_type, window_type, window_start) key. Repeated crossings
    within the same window keep the PEAK actual_pct (func.greatest) + escalate
    severity warning -> critical when the peak reaches 100%, but NEVER bump
    triggered_at (the first-crossing time is the alert's birth time). Below 80%
    (or quota <= 0) is a no-op — no row, no ZeroDivision.

Key Components:
    - ALERT_THRESHOLD_PCT: the crossing threshold (80)
    - _severity(pct): 'critical' if >= 100 else 'warning' (lowercase, SLAViolation parity)
    - RateLimitAlertStore.maybe_record: idempotent threshold-crossing upsert
    - RateLimitAlertStore.list_recent: newest-first recent alerts (tenant-scoped)

Created: 2026-05-29 (Sprint 57.62 Track A)
Last Modified: 2026-05-29

Modification History (newest-first):
    - 2026-05-29: Sprint 57.62 Track A — initial creation (80%-threshold alert store)

Related:
    - infrastructure/db/models/api_keys.py:RateLimitAlert — ORM model
    - infrastructure/db/models/sla.py:SLAViolation — alert-log + lowercase severity precedent
    - platform_layer/tenant/rate_limit_counter.py:_write_through — the runtime hook caller
    - platform_layer/tenant/rate_limit_config_store.py — sibling stateless store style
    - 0021_rate_limit_alerts.py — migration (table + RLS)
    - api/v1/admin/tenants.py — GET /rate-limits/alerts consumer
    - .claude/rules/multi-tenant-data.md 鐵律 2 (all queries filter by tenant_id)
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.models.api_keys import RateLimitAlert

# The single crossing threshold this subsystem records (Sprint 57.62). A row is
# written the first time usage reaches >= 80% of the configured quota.
ALERT_THRESHOLD_PCT = 80


def _severity(pct: int) -> str:
    """Lowercase severity for an observed usage pct (mirrors SLAViolation casing).

    >= 100% is 'critical' (the tenant is at/over the hard limit — 429 territory);
    80-99% is 'warning' (approaching the limit). Lowercase + the CHECK constraint
    on rate_limit_alerts.severity intentionally match SLAViolation.
    """
    return "critical" if pct >= 100 else "warning"


class RateLimitAlertStore:
    """Stateless writer/reader over the rate_limit_alerts table (Sprint 57.62)."""

    async def maybe_record(
        self,
        session: AsyncSession,
        tenant_id: UUID,
        resource_type: str,
        window_type: str,
        *,
        used: int,
        quota: int,
        window_start: datetime,
    ) -> None:
        """Record an alert iff usage crossed the 80% threshold (idempotent upsert).

        No-op when quota <= 0 (un-enforceable config — also dodges ZeroDivision)
        or when pct < ALERT_THRESHOLD_PCT. Otherwise upserts on the unique
        (tenant_id, resource_type, window_type, window_start) key:
            - actual_pct = peak (GREATEST of existing + this crossing)
            - used / quota = the latest denormalised snapshot
            - severity escalates to 'critical' once the peak reaches 100%
            - triggered_at is NOT updated (first-crossing birth time preserved)
        The caller's session already carries the tenant context (set for the
        rate_limits RLS policies in _write_through), which the rate_limit_alerts
        RLS INSERT/UPDATE policies also read — so the upsert passes WITH CHECK.
        """
        if quota <= 0:
            return
        pct = int(used / quota * 100)
        if pct < ALERT_THRESHOLD_PCT:
            return

        # Peak-aware escalation: the post-conflict actual_pct is GREATEST(existing,
        # this pct); severity is derived from that SAME peak so a later 105% on an
        # already-recorded 85% window escalates warning -> critical in one upsert.
        peak = func.greatest(RateLimitAlert.actual_pct, pct)
        stmt = (
            pg_insert(RateLimitAlert)
            .values(
                tenant_id=tenant_id,
                resource_type=resource_type,
                window_type=window_type,
                threshold_pct=ALERT_THRESHOLD_PCT,
                actual_pct=pct,
                used=used,
                quota=quota,
                severity=_severity(pct),
                window_start=window_start,
            )
            .on_conflict_do_update(
                constraint="uq_rate_limit_alerts_window",
                set_={
                    "actual_pct": peak,
                    "used": used,
                    "quota": quota,
                    "severity": case((peak >= 100, "critical"), else_="warning"),
                    # triggered_at deliberately omitted — keep first-crossing time.
                },
            )
        )
        await session.execute(stmt)

    async def list_recent(
        self,
        session: AsyncSession,
        tenant_id: UUID,
        limit: int = 20,
    ) -> list[RateLimitAlert]:
        """Return this tenant's most-recent alerts (newest-first, capped at limit).

        Multi-tenant rule (鐵律 2): every query filters by tenant_id.
        """
        result = await session.execute(
            select(RateLimitAlert)
            .where(RateLimitAlert.tenant_id == tenant_id)
            .order_by(RateLimitAlert.triggered_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
