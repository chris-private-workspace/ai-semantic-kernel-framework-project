"""
File: backend/tests/integration/api/test_admin_tenant_rate_limits_alerts.py
Purpose: Integration tests — GET /admin/tenants/{tenant_id}/rate-limits/alerts (Sprint 57.62).
Category: Tests / Integration / API (Phase 58.x RateLimits usage alerting)
Scope: Sprint 57.62 Track A / US-1 (RateLimits 80% usage alerting)

Description:
    Verifies the recent-alerts GET endpoint (source: the rate_limit_alerts table):
    - 404 when tenant not found
    - 200 empty list when the tenant has no alerts
    - 200 newest-first ordering
    - limit cap (le=100) — out-of-range limit → 422
    - multi-tenant isolation via the endpoint (tenant A's alert not in B's response)

    Mirrors test_admin_tenant_rate_limits.py's _build_app helper (test-state
    middleware + dependency overrides for the db session + admin role).

Created: 2026-05-29 (Sprint 57.62 Track A)

Modification History (newest-first):
    - 2026-05-29: Initial creation (Sprint 57.62 Track A / US-1)
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI, Request, Response
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.admin.tenants import router as admin_tenants_router
from infrastructure.db.models.api_keys import RateLimitAlert
from infrastructure.db.models.identity import Tenant, TenantPlan, TenantState
from infrastructure.db.session import get_db_session
from platform_layer.identity.auth import require_admin_platform_role

pytestmark = pytest.mark.asyncio


def _build_app(db_session: AsyncSession | None = None) -> FastAPI:
    app = FastAPI()
    app.include_router(admin_tenants_router, prefix="/api/v1")

    @app.middleware("http")
    async def _populate_test_state(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        user_header = request.headers.get("X-Test-User")
        roles_header = request.headers.get("X-Test-Roles")
        tenant_header = request.headers.get("X-Test-Tenant")
        request.state.user_id = UUID(user_header) if user_header else None
        request.state.roles = json.loads(roles_header) if roles_header else None
        request.state.tenant_id = UUID(tenant_header) if tenant_header else None
        return await call_next(request)

    if db_session is not None:

        async def _override_session() -> AsyncIterator[AsyncSession]:
            yield db_session

        async def _override_admin() -> UUID:
            return UUID("00000000-0000-0000-0000-000000000001")

        app.dependency_overrides[get_db_session] = _override_session
        app.dependency_overrides[require_admin_platform_role] = _override_admin

    return app


async def _seed_tenant(session: AsyncSession, *, code: str) -> Tenant:
    t = Tenant(
        code=code,
        display_name=f"Tenant {code}",
        state=TenantState.ACTIVE,
        plan=TenantPlan.ENTERPRISE,
        meta_data={},
    )
    session.add(t)
    await session.flush()
    await session.refresh(t)
    return t


async def _seed_alert(
    session: AsyncSession,
    tenant_id: UUID,
    *,
    resource_type: str,
    window_start: datetime,
    triggered_at: datetime,
    actual_pct: int = 85,
    severity: str = "warning",
) -> None:
    session.add(
        RateLimitAlert(
            tenant_id=tenant_id,
            resource_type=resource_type,
            window_type="min",
            threshold_pct=80,
            actual_pct=actual_pct,
            used=actual_pct,
            quota=100,
            severity=severity,
            window_start=window_start,
            triggered_at=triggered_at,
        )
    )
    await session.flush()


async def test_alerts_404_when_tenant_not_found(db_session: AsyncSession) -> None:
    app = _build_app(db_session=db_session)
    missing_id = uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{missing_id}/rate-limits/alerts")
    assert resp.status_code == 404


async def test_alerts_empty_when_none(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code="RLA_EP_EMPTY")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/rate-limits/alerts")
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"items": []}


async def test_alerts_newest_first(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code="RLA_EP_ORDER")
    base = datetime(2026, 5, 1, 0, 0, 0, tzinfo=timezone.utc)
    await _seed_alert(
        db_session,
        tenant.id,
        resource_type="oldest",
        window_start=base,
        triggered_at=base,
    )
    await _seed_alert(
        db_session,
        tenant.id,
        resource_type="newest",
        window_start=base + timedelta(minutes=5),
        triggered_at=base + timedelta(minutes=5),
        actual_pct=100,
        severity="critical",
    )
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/rate-limits/alerts")
    assert resp.status_code == 200, resp.text
    items = resp.json()["items"]
    assert [i["resource"] for i in items] == ["newest", "oldest"]
    assert items[0]["severity"] == "critical"
    assert items[0]["actual_pct"] == 100
    assert items[0]["threshold_pct"] == 80
    assert items[0]["window"] == "min"


async def test_alerts_limit_cap_rejects_over_100(db_session: AsyncSession) -> None:
    """limit > 100 violates Query(le=100) → 422 (does not reach the DB)."""
    tenant = await _seed_tenant(db_session, code="RLA_EP_CAP")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/rate-limits/alerts?limit=101")
    assert resp.status_code == 422


async def test_alerts_limit_caps_returned_rows(db_session: AsyncSession) -> None:
    """A valid small limit caps the returned rows."""
    tenant = await _seed_tenant(db_session, code="RLA_EP_LIMIT")
    base = datetime(2026, 5, 1, 0, 0, 0, tzinfo=timezone.utc)
    for i in range(4):
        await _seed_alert(
            db_session,
            tenant.id,
            resource_type=f"res_{i}",
            window_start=base + timedelta(minutes=i),
            triggered_at=base + timedelta(minutes=i),
        )
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/rate-limits/alerts?limit=2")
    assert resp.status_code == 200, resp.text
    items = resp.json()["items"]
    assert len(items) == 2
    # Newest two: res_3, res_2.
    assert [i["resource"] for i in items] == ["res_3", "res_2"]


async def test_alerts_multi_tenant_isolation(db_session: AsyncSession) -> None:
    """Tenant A's alerts MUST NOT appear in tenant B's response (table-scoped)."""
    tenant_a = await _seed_tenant(db_session, code="RLA_EP_ISO_A")
    tenant_b = await _seed_tenant(db_session, code="RLA_EP_ISO_B")
    base = datetime(2026, 5, 1, 0, 0, 0, tzinfo=timezone.utc)
    await _seed_alert(
        db_session,
        tenant_a.id,
        resource_type="only_a",
        window_start=base,
        triggered_at=base,
    )
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp_a = await ac.get(f"/api/v1/admin/tenants/{tenant_a.id}/rate-limits/alerts")
        resp_b = await ac.get(f"/api/v1/admin/tenants/{tenant_b.id}/rate-limits/alerts")
    assert resp_a.status_code == 200 and resp_b.status_code == 200
    assert {i["resource"] for i in resp_a.json()["items"]} == {"only_a"}
    assert resp_b.json()["items"] == []
