"""
File: backend/tests/integration/api/test_admin_tenant_quotas.py
Purpose: Integration tests — GET /admin/tenants/{tenant_id}/quotas (Sprint 57.48 Track C).
Category: Tests / Integration / API (Phase 58+ Backend Schema Extension wave)
Scope: Sprint 57.48 Day 1 Track C (closes AD-TenantSettings-Quotas-Backend)

Description:
    Verifies the GET /admin/tenants/{tenant_id}/quotas endpoint:
    - 401 when no JWT context
    - 404 when tenant not found
    - 200 happy path returns 4 PlanQuota fields projected as items
    - Response shape: items + total + limit + offset; each item carries
      resource/limit/unit/period/current_usage
    - Pagination (limit + offset)
    - Multi-tenant isolation: different tenants on same plan see same quota
      structure but each request is scoped to its tenant_id (verified via 404 path)
    - limit > 200 → 422

Created: 2026-05-26 (Sprint 57.48 Day 1)

Modification History (newest-first):
    - 2026-05-26: Initial creation (Sprint 57.48 Day 1 Track C — Quotas admin GET)
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Awaitable, Callable
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


async def _seed_tenant(session: AsyncSession, *, code: str) -> Tenant:
    t = Tenant(
        code=code,
        display_name=f"Tenant {code}",
        state=TenantState.ACTIVE,
        plan=TenantPlan.ENTERPRISE,
    )
    session.add(t)
    await session.flush()
    await session.refresh(t)
    return t


async def test_list_quotas_401_without_auth() -> None:
    app = _build_app()
    tenant_id = uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant_id}/quotas")
    assert resp.status_code == 401


async def test_list_quotas_404_when_tenant_not_found(db_session: AsyncSession) -> None:
    app = _build_app(db_session=db_session)
    missing_id = uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{missing_id}/quotas")
    assert resp.status_code == 404


async def test_list_quotas_happy_path_returns_4_quota_fields(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code="QUOTA_HAPPY_T1")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/quotas")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 4
    assert len(body["items"]) == 4
    resources = {item["resource"] for item in body["items"]}
    assert resources == {
        "tokens_per_day",
        "cost_usd_per_day",
        "sessions_per_user_concurrent",
        "api_keys_max",
    }


async def test_list_quotas_response_shape(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code="QUOTA_SHAPE_T1")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/quotas")
    assert resp.status_code == 200, resp.text
    item = resp.json()["items"][0]
    expected = {"resource", "limit", "unit", "period", "current_usage"}
    assert expected.issubset(set(item.keys()))
    assert item["current_usage"] is None  # always null at admin layer this sprint


async def test_list_quotas_tokens_field_has_correct_unit(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code="QUOTA_UNIT_T1")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/quotas")
    body = resp.json()
    tokens = next(item for item in body["items"] if item["resource"] == "tokens_per_day")
    assert tokens["unit"] == "tokens"
    assert tokens["period"] == "day"
    assert tokens["limit"] > 0


async def test_list_quotas_pagination(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code="QUOTA_PAGE_T1")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        page1 = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/quotas?limit=2&offset=0")
        page2 = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/quotas?limit=2&offset=2")
    assert page1.status_code == 200 and page2.status_code == 200
    assert page1.json()["total"] == 4
    assert len(page1.json()["items"]) == 2
    assert len(page2.json()["items"]) == 2


async def test_list_quotas_tenant_isolation(db_session: AsyncSession) -> None:
    """Different tenants must each see a quota response scoped to their own ID
    (no cross-tenant leak via path)."""
    tenant_a = await _seed_tenant(db_session, code="QUOTA_ISO_A")
    tenant_b = await _seed_tenant(db_session, code="QUOTA_ISO_B")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp_a = await ac.get(f"/api/v1/admin/tenants/{tenant_a.id}/quotas")
        resp_b = await ac.get(f"/api/v1/admin/tenants/{tenant_b.id}/quotas")
    assert resp_a.status_code == 200 and resp_b.status_code == 200
    # Same plan (ENTERPRISE) so structure matches, but both must succeed via
    # their respective tenant paths (404 path proven separately above).
    assert resp_a.json()["total"] == 4
    assert resp_b.json()["total"] == 4


async def test_list_quotas_invalid_query_limit(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code="QUOTA_LIM_T1")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/quotas?limit=500")
    assert resp.status_code == 422
