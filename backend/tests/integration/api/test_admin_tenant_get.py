"""
File: backend/tests/integration/api/test_admin_tenant_get.py
Purpose: Integration tests — GET /admin/tenants/{tenant_id} endpoint (Sprint 57.3 US-1).
Category: Tests / Integration / API (Phase 57+ SaaS Frontend 2/N)
Scope: Sprint 57.3 / Day 1 / US-1 (closes D1 RED finding)

Description:
    Verifies the GET /admin/tenants/{tenant_id} endpoint:
    - 401 when no JWT context (no X-Test-User header)
    - 403 when role is not admin/platform_admin
    - 404 when tenant_id not found in DB
    - 200 happy path with full TenantResponse 10-field shape
    - 200 round-trip preserves nested meta_data JSONB content
    - 200 response field types match Pydantic schema (UUID / enum / datetime)

    Mirrors test_admin_tenants_rbac.py + test_admin_sla_reports.py patterns
    (FastAPI test app with X-Test-User / X-Test-Roles middleware + optional
    dependency_overrides for db_session + require_admin_platform_role).

Created: 2026-05-07 (Sprint 57.3 Day 1)
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
from infrastructure.db.models.identity import TenantPlan, TenantState
from infrastructure.db.session import get_db_session
from platform_layer.identity.auth import require_tenant_match_or_platform_admin
from tests.conftest import seed_tenant

pytestmark = pytest.mark.asyncio


def _build_app(db_session: AsyncSession | None = None) -> FastAPI:
    """Build app with admin tenants router + role middleware + optional DB override."""
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
        app.dependency_overrides[require_tenant_match_or_platform_admin] = _override_admin

    return app


async def test_get_tenant_401_without_auth() -> None:
    """No X-Test-User header → require_admin_platform_role 401."""
    app = _build_app()
    tenant_id = uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant_id}")
    assert resp.status_code == 401


async def test_get_tenant_403_cross_tenant() -> None:
    """Non-platform-admin → a different tenant via the URL → 403 (Sprint 57.13 US-A3)."""
    app = _build_app()
    user_id = uuid4()
    path_tenant_id = uuid4()
    caller_tenant_id = uuid4()  # different → cross-tenant
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(
            f"/api/v1/admin/tenants/{path_tenant_id}",
            headers={
                "X-Test-User": str(user_id),
                "X-Test-Roles": json.dumps(["tenant_admin"]),
                "X-Test-Tenant": str(caller_tenant_id),
            },
        )
    assert resp.status_code == 403
    assert "cross-tenant" in resp.json()["detail"]


async def test_get_tenant_404_not_found(db_session: AsyncSession) -> None:
    """Admin auth + random UUID not in DB → 404."""
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    random_tenant_id = uuid4()
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{random_tenant_id}")
    assert resp.status_code == 404
    assert str(random_tenant_id) in resp.json()["detail"]


async def test_get_tenant_happy_path(db_session: AsyncSession) -> None:
    """Admin auth + seeded tenant → 200 + all 10 fields populated."""
    t = await seed_tenant(db_session, code="GET_HAPPY", display_name="Happy Path")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{t.id}")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["id"] == str(t.id)
    assert body["code"] == "GET_HAPPY"
    assert body["display_name"] == "Happy Path"
    # state defaults to REQUESTED per ORM model (D10 — was PROVISIONING in plan)
    assert body["state"] == TenantState.REQUESTED.value
    # plan defaults to ENTERPRISE per ORM model
    assert body["plan"] == TenantPlan.ENTERPRISE.value
    assert body["provisioning_progress"] == {}
    assert body["onboarding_progress"] == {}
    assert body["meta_data"] == {}
    assert "created_at" in body
    assert "updated_at" in body


async def test_get_tenant_response_shape(db_session: AsyncSession) -> None:
    """Response keys match TenantResponse 15-field schema exactly.

    Sprint 57.46 extended TenantResponse from 10 → 15 fields by adding 5
    SaaS settings columns (region/locale/retention_days/sso_enabled/seats).
    """
    t = await seed_tenant(db_session, code="SHAPE_TEST")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{t.id}")
    assert resp.status_code == 200
    body = resp.json()
    expected_keys = {
        "id",
        "code",
        "display_name",
        "state",
        "plan",
        "provisioning_progress",
        "onboarding_progress",
        "meta_data",
        # Sprint 57.46 — 5 SaaS settings columns
        "region",
        "locale",
        "retention_days",
        "sso_enabled",
        "seats",
        "created_at",
        "updated_at",
    }
    assert set(body.keys()) == expected_keys


async def test_get_tenant_meta_data_jsonb_round_trip(db_session: AsyncSession) -> None:
    """Nested meta_data dict round-trips through JSONB column."""
    nested = {
        "admin_email": "round@trip.com",
        "tags": ["a", "b", "c"],
        "config": {"flag": True, "limit": 42},
    }
    from infrastructure.db.models.identity import Tenant

    t = Tenant(code="META_RT", display_name="Meta Round-Trip", meta_data=nested)
    db_session.add(t)
    await db_session.flush()
    await db_session.refresh(t)

    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{t.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta_data"] == nested
