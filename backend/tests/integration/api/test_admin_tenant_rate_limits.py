"""
File: backend/tests/integration/api/test_admin_tenant_rate_limits.py
Purpose: Integration tests — GET /admin/tenants/{tenant_id}/rate-limits (Sprint 57.48 Track D).
Category: Tests / Integration / API (Phase 58+ Backend Schema Extension wave)
Scope: Sprint 57.48 Day 1 Track D Option A (closes AD-TenantSettings-RateLimits-Backend)

Description:
    Verifies the GET /admin/tenants/{tenant_id}/rate-limits endpoint
    (Day 0.8 Option A — fixture-projection from tenant.meta_data["rate_limits"]):
    - 401 when no JWT context
    - 404 when tenant not found
    - 200 returns DEFAULT_RATE_LIMITS (3 items) when meta_data has no
      "rate_limits" key
    - 200 returns tenant-overridden list when meta_data["rate_limits"] is set
    - Response shape: items + total + limit + offset; items carry label + value
    - Multi-tenant isolation (tenant A's override does NOT show in tenant B)

Created: 2026-05-26 (Sprint 57.48 Day 1)

Modification History (newest-first):
    - 2026-05-26: Initial creation (Sprint 57.48 Day 1 Track D — RateLimits admin GET Option A)
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI, Request, Response
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.admin.tenants import router as admin_tenants_router
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


async def test_list_rate_limits_401_without_auth() -> None:
    app = _build_app()
    tenant_id = uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant_id}/rate-limits")
    assert resp.status_code == 401


async def test_list_rate_limits_404_when_tenant_not_found(db_session: AsyncSession) -> None:
    app = _build_app(db_session=db_session)
    missing_id = uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{missing_id}/rate-limits")
    assert resp.status_code == 404


async def test_list_rate_limits_returns_defaults_when_no_override(
    db_session: AsyncSession,
) -> None:
    """meta_data lacks rate_limits → DEFAULT_RATE_LIMITS (3 items)."""
    tenant = await _seed_tenant(db_session, code="RL_DEF_T1")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/rate-limits")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 3
    labels = {item["label"] for item in body["items"]}
    assert labels == {"API requests", "Tool calls", "SSE connections"}


async def test_list_rate_limits_applies_tenant_override(db_session: AsyncSession) -> None:
    """meta_data['rate_limits'] is honoured when present."""
    custom = [
        {"label": "API requests", "value": "500 / min"},
        {"label": "Tool calls", "value": "5,000 / min"},
    ]
    tenant = await _seed_tenant(
        db_session,
        code="RL_OVR_T1",
        meta_data={"rate_limits": custom},
    )
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/rate-limits")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 2
    api = next(item for item in body["items"] if item["label"] == "API requests")
    assert api["value"] == "500 / min"


async def test_list_rate_limits_response_shape(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code="RL_SHAPE_T1")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/rate-limits")
    item = resp.json()["items"][0]
    assert {"label", "value"}.issubset(set(item.keys()))


async def test_list_rate_limits_tenant_isolation(db_session: AsyncSession) -> None:
    tenant_a = await _seed_tenant(
        db_session,
        code="RL_ISO_A",
        meta_data={"rate_limits": [{"label": "Custom A", "value": "9 / min"}]},
    )
    tenant_b = await _seed_tenant(db_session, code="RL_ISO_B")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp_a = await ac.get(f"/api/v1/admin/tenants/{tenant_a.id}/rate-limits")
        resp_b = await ac.get(f"/api/v1/admin/tenants/{tenant_b.id}/rate-limits")
    assert resp_a.status_code == 200 and resp_b.status_code == 200
    labels_a = {item["label"] for item in resp_a.json()["items"]}
    labels_b = {item["label"] for item in resp_b.json()["items"]}
    assert labels_a == {"Custom A"}
    assert labels_b == {"API requests", "Tool calls", "SSE connections"}
