"""
File: backend/tests/integration/api/test_admin_tenant_list.py
Purpose: Integration tests — GET /admin/tenants list endpoint (Sprint 57.4 US-1).
Category: Tests / Integration / API (Phase 57+ SaaS Frontend 3/N)
Scope: Sprint 57.4 / Day 1 / US-1 (closes plan-time D1 RED finding)

Description:
    Verifies the GET /admin/tenants list endpoint:
    - 401 when no JWT context (no X-Test-User header)
    - 403 when role is not admin/platform_admin
    - 200 happy path with default pagination (50 / 0)
    - 200 filter by state — only matching tenants returned
    - 200 filter by plan — only matching tenants returned
    - 200 search by ILIKE on code substring
    - 200 pagination limit + offset behavior
    - 200 empty result for non-matching search
    - Response shape matches TenantListResponse

    Mirrors test_admin_tenant_get.py + test_admin_tenant_patch.py
    patterns (FastAPI test app with X-Test-User / X-Test-Roles
    middleware + dependency_overrides for db_session +
    require_admin_platform_role).

Created: 2026-05-07 (Sprint 57.4 Day 1)
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
    """Build app with admin tenants router + role middleware + DB override."""
    app = FastAPI()
    app.include_router(admin_tenants_router, prefix="/api/v1")

    @app.middleware("http")
    async def _populate_test_state(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        user_header = request.headers.get("X-Test-User")
        roles_header = request.headers.get("X-Test-Roles")
        request.state.user_id = UUID(user_header) if user_header else None
        request.state.roles = json.loads(roles_header) if roles_header else None
        return await call_next(request)

    if db_session is not None:

        async def _override_session() -> AsyncIterator[AsyncSession]:
            yield db_session

        async def _override_admin() -> UUID:
            return UUID("00000000-0000-0000-0000-000000000001")

        app.dependency_overrides[get_db_session] = _override_session
        app.dependency_overrides[require_admin_platform_role] = _override_admin

    return app


async def _seed_tenant_with(
    session: AsyncSession,
    *,
    code: str,
    display_name: str | None = None,
    state: TenantState = TenantState.REQUESTED,
    plan: TenantPlan = TenantPlan.ENTERPRISE,
) -> Tenant:
    """Create + flush a Tenant with explicit state + plan for filter tests.

    Note: Phase 56+ Stage 1 only ships TenantPlan.ENTERPRISE; STANDARD lands
    in Stage 2. Plan filter test therefore exercises the filter parameter
    parsing path rather than exclusion.
    """
    t = Tenant(
        code=code,
        display_name=display_name or f"Tenant {code}",
        state=state,
        plan=plan,
    )
    session.add(t)
    await session.flush()
    await session.refresh(t)
    return t


async def test_list_tenants_401_without_auth() -> None:
    """No X-Test-User header → require_admin_platform_role 401."""
    app = _build_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/admin/tenants")
    assert resp.status_code == 401


async def test_list_tenants_403_wrong_role() -> None:
    """tenant_admin role insufficient → 403."""
    app = _build_app()
    user_id = uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(
            "/api/v1/admin/tenants",
            headers={
                "X-Test-User": str(user_id),
                "X-Test-Roles": json.dumps(["tenant_admin"]),
            },
        )
    assert resp.status_code == 403


async def test_list_tenants_happy_no_filter(db_session: AsyncSession) -> None:
    """Admin auth + seeded tenants → 200 + items + total >= 1 + correct shape."""
    await _seed_tenant_with(db_session, code="LIST_T1", display_name="Tenant One")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/admin/tenants")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "items" in body and "total" in body and "limit" in body and "offset" in body
    assert body["limit"] == 50
    assert body["offset"] == 0
    assert body["total"] >= 1
    # Each item should have the 7 TenantListItem fields (no progress/meta_data).
    sample = body["items"][0]
    expected = {"id", "code", "display_name", "state", "plan", "created_at", "updated_at"}
    assert expected.issubset(set(sample.keys()))
    assert "meta_data" not in sample
    assert "provisioning_progress" not in sample
    assert "onboarding_progress" not in sample


async def test_list_tenants_filter_by_state(db_session: AsyncSession) -> None:
    """Filter state=active returns only ACTIVE tenants (excludes REQUESTED)."""
    await _seed_tenant_with(db_session, code="STATE_ACT", state=TenantState.ACTIVE)
    await _seed_tenant_with(db_session, code="STATE_REQ", state=TenantState.REQUESTED)
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/admin/tenants?state=active")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert all(item["state"] == "active" for item in body["items"])
    assert any(item["code"] == "STATE_ACT" for item in body["items"])
    assert all(item["code"] != "STATE_REQ" for item in body["items"])


async def test_list_tenants_filter_by_plan(db_session: AsyncSession) -> None:
    """Filter plan=enterprise parses + returns matching tenants.

    Phase 56+ Stage 1 only ships TenantPlan.ENTERPRISE — exclusion test
    requires Stage 2 STANDARD to be added. This test verifies the filter
    parameter parses and the response items all have plan=enterprise.
    """
    await _seed_tenant_with(db_session, code="PLAN_ENT", plan=TenantPlan.ENTERPRISE)
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/admin/tenants?plan=enterprise")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert all(item["plan"] == "enterprise" for item in body["items"])
    assert any(item["code"] == "PLAN_ENT" for item in body["items"])


async def test_list_tenants_search_by_code(db_session: AsyncSession) -> None:
    """Search ILIKE matches code substring."""
    await _seed_tenant_with(db_session, code="ACME_CORP", display_name="Acme Corp")
    await _seed_tenant_with(db_session, code="OTHER_CO", display_name="Other Co")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/admin/tenants?search=ACME")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    codes = [item["code"] for item in body["items"]]
    assert "ACME_CORP" in codes
    assert "OTHER_CO" not in codes


async def test_list_tenants_pagination(db_session: AsyncSession) -> None:
    """limit + offset return distinct paginated slices.

    Uses ILIKE search to isolate the 3 seeded PAGE_* tenants so the test
    is independent of any other tenants seeded by sibling fixtures.
    Endpoint orders by (created_at DESC, id DESC) for deterministic
    pagination even when tenants share the same created_at timestamp.
    """
    for i in range(3):
        await _seed_tenant_with(db_session, code=f"PAGE_{i}")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        page1 = await ac.get(
            "/api/v1/admin/tenants?search=PAGE_&limit=2&offset=0"
        )
        page2 = await ac.get(
            "/api/v1/admin/tenants?search=PAGE_&limit=2&offset=2"
        )
    assert page1.status_code == 200 and page2.status_code == 200
    body1 = page1.json()
    body2 = page2.json()
    assert body1["limit"] == 2 and body1["offset"] == 0
    assert body2["limit"] == 2 and body2["offset"] == 2
    assert body1["total"] == 3 and body2["total"] == 3
    assert len(body1["items"]) == 2
    assert len(body2["items"]) == 1
    # Pages must not overlap.
    ids1 = {item["id"] for item in body1["items"]}
    ids2 = {item["id"] for item in body2["items"]}
    assert ids1.isdisjoint(ids2)


async def test_list_tenants_empty_filter(db_session: AsyncSession) -> None:
    """Search with no match → items=[] + total=0."""
    await _seed_tenant_with(db_session, code="EXISTING_CODE")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(
            "/api/v1/admin/tenants?search=NONEXISTENT_TENANT_99999"
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 0


async def test_list_tenants_invalid_query_limit(db_session: AsyncSession) -> None:
    """limit > 200 → 422 Unprocessable Entity (Pydantic Query validation)."""
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/admin/tenants?limit=500")
    assert resp.status_code == 422
