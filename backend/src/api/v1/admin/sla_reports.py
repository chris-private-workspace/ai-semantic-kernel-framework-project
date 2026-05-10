"""
File: backend/src/api/v1/admin/sla_reports.py
Purpose: GET /api/v1/admin/tenants/{tenant_id}/sla-report?month=YYYY-MM endpoint.
Category: API / Admin (Phase 56 SaaS Stage 1)
Scope: Sprint 56.3 / Day 2 / US-2 SLA Monthly Report.

Description:
    Returns per-tenant per-month SLAReport JSON with 4 SLA metric category
    breakdown + violation count. Cache-first read: if SLAReport row exists
    for (tenant_id, month) → return cached. Else generate via
    SLAReportGenerator + persist + return.

    Auth: `require_tenant_match_or_platform_admin` (Sprint 57.13 US-A3) —
    platform admins see any tenant; a regular user sees only their own.

Created: 2026-05-06 (Sprint 56.3 Day 2)
Last Modified: 2026-05-10

Modification History (newest-first):
    - 2026-05-10: Sprint 57.13 US-A3 — auth dep → require_tenant_match_or_platform_admin
    - 2026-05-06: Initial creation (Sprint 56.3 Day 2 / US-2)

Related:
    - sprint-56-3-plan.md §US-2
    - platform_layer/observability/sla_monitor.py (SLAReportGenerator)
    - infrastructure/db/models/sla.py (SLAReport ORM)
    - api/v1/admin/tenants.py (auth + router pattern reference)
"""

from __future__ import annotations

import re
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.models.identity import Tenant
from infrastructure.db.models.sla import SLAReport
from infrastructure.db.session import get_db_session
from platform_layer.identity.auth import require_tenant_match_or_platform_admin
from platform_layer.observability.sla_monitor import (
    SLAReportGenerator,
    get_sla_recorder,
)

router = APIRouter(prefix="/admin/tenants", tags=["admin", "sla"])

_MONTH_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


class SLAReportResponse(BaseModel):
    tenant_id: UUID
    month: str
    availability_pct: float
    api_p99_ms: int | None
    loop_simple_p99_ms: int | None
    loop_medium_p99_ms: int | None
    loop_complex_p99_ms: int | None
    hitl_queue_notif_p99_ms: int | None
    violations_count: int


@router.get(
    "/{tenant_id}/sla-report",
    response_model=SLAReportResponse,
    dependencies=[Depends(require_tenant_match_or_platform_admin)],
)
async def get_sla_report(
    tenant_id: UUID,
    month: str = Query(..., description="YYYY-MM format"),
    db: AsyncSession = Depends(get_db_session),
) -> SLAReportResponse:
    """Return SLA report for tenant + month (cached or generated on demand)."""
    if not _MONTH_PATTERN.match(month):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="month must be YYYY-MM",
        )

    # 1. Cache lookup — existing (tenant_id, month) row?
    stmt = select(SLAReport).where((SLAReport.tenant_id == tenant_id) & (SLAReport.month == month))
    cached = (await db.execute(stmt)).scalar_one_or_none()
    if cached is not None:
        return _to_response(cached)

    # 2. On-demand generate — load tenant for plan tier.
    tenant_row = (
        await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    ).scalar_one_or_none()
    if tenant_row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"tenant {tenant_id} not found",
        )

    recorder = get_sla_recorder()
    generator = SLAReportGenerator(recorder=recorder, db_session=db)
    plan_value = (
        tenant_row.plan.value if hasattr(tenant_row.plan, "value") else str(tenant_row.plan)
    )
    report = await generator.generate_monthly_report(
        tenant_id=tenant_id,
        month=month,
        plan=plan_value,
    )
    return _to_response(report)


def _to_response(report: SLAReport) -> SLAReportResponse:
    return SLAReportResponse(
        tenant_id=report.tenant_id,
        month=report.month,
        availability_pct=float(report.availability_pct),
        api_p99_ms=report.api_p99_ms,
        loop_simple_p99_ms=report.loop_simple_p99_ms,
        loop_medium_p99_ms=report.loop_medium_p99_ms,
        loop_complex_p99_ms=report.loop_complex_p99_ms,
        hitl_queue_notif_p99_ms=report.hitl_queue_notif_p99_ms,
        violations_count=report.violations_count,
    )
