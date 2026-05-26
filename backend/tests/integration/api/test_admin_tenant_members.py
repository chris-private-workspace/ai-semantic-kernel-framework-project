"""
File: backend/tests/integration/api/test_admin_tenant_members.py
Purpose: Integration tests — GET /admin/tenants/{tenant_id}/members (Sprint 57.47 Track B).
Category: Tests / Integration / API (Phase 58+ Backend Schema Extension wave)
Scope: Sprint 57.47 Day 1 Track B (cheapest fixture-only TenantSettings tab — MEMBERS)

Description:
    Verifies the GET /admin/tenants/{tenant_id}/members read-only endpoint:
    - 401 when no JWT context
    - 200 happy path returns User rows scoped to the path tenant_id
    - Multi-tenant isolation — tenant A's request never returns tenant B users
    - Response shape matches TenantMemberListResponse (items + total + limit + offset)
    - Each item exposes the 5 fields (id/email/display_name/status/created_at)
    - 404 when tenant_id does not exist
    - Pagination (limit + offset) works correctly

    Pattern mirrors test_admin_tenant_get.py — same dependency_overrides for
    require_tenant_match_or_platform_admin + get_db_session.

Created: 2026-05-26 (Sprint 57.47 Day 1)

Modification History (newest-first):
    - 2026-05-26: Initial creation (Sprint 57.47 Day 1 Track B — cheapest MEMBERS tab)
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
from infrastructure.db.models.identity import Tenant, TenantPlan, TenantState, User
from infrastructure.db.session import get_db_session
from platform_layer.identity.auth import require_tenant_match_or_platform_admin

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


async def _seed_user(
    session: AsyncSession,
    *,
    tenant: Tenant,
    email: str,
    display_name: str | None = None,
    status: str = "active",
) -> User:
    u = User(
        tenant_id=tenant.id,
        email=email,
        display_name=display_name,
        status=status,
    )
    session.add(u)
    await session.flush()
    await session.refresh(u)
    return u


# =====================================================================
# Auth + 404 tests
# =====================================================================
async def test_list_members_401_without_auth() -> None:
    """No X-Test-User header → 401."""
    app = _build_app()
    tenant_id = uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant_id}/members")
    assert resp.status_code == 401


async def test_list_members_404_when_tenant_not_found(db_session: AsyncSession) -> None:
    """Admin auth + non-existent tenant_id → 404 (mirrors GET /{tenant_id})."""
    app = _build_app(db_session=db_session)
    missing_id = uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{missing_id}/members")
    assert resp.status_code == 404


# =====================================================================
# Happy path + shape
# =====================================================================
async def test_list_members_happy_path_returns_users_for_tenant(
    db_session: AsyncSession,
) -> None:
    """Admin auth + seeded users → 200 with items + total."""
    tenant = await _seed_tenant(db_session, code="MEM_HAPPY_T1")
    await _seed_user(db_session, tenant=tenant, email="alice@example.com", display_name="Alice")
    await _seed_user(db_session, tenant=tenant, email="bob@example.com")

    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/members")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert {"items", "total", "limit", "offset"}.issubset(set(body.keys()))
    assert body["total"] == 2
    assert len(body["items"]) == 2
    emails = {item["email"] for item in body["items"]}
    assert emails == {"alice@example.com", "bob@example.com"}


async def test_list_members_response_shape_has_5_fields(db_session: AsyncSession) -> None:
    """Each TenantMemberItem exposes id/email/display_name/status/created_at."""
    tenant = await _seed_tenant(db_session, code="MEM_SHAPE_T1")
    await _seed_user(db_session, tenant=tenant, email="shape@example.com", display_name="Shape")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/members")
    assert resp.status_code == 200, resp.text
    item = resp.json()["items"][0]
    expected = {"id", "email", "display_name", "status", "created_at"}
    assert expected.issubset(set(item.keys()))


# =====================================================================
# Multi-tenant isolation — CRITICAL (per .claude/rules/multi-tenant-data.md)
# =====================================================================
async def test_list_members_tenant_isolation(db_session: AsyncSession) -> None:
    """Users from tenant B must NOT appear in tenant A's response."""
    tenant_a = await _seed_tenant(db_session, code="MEM_ISO_A")
    tenant_b = await _seed_tenant(db_session, code="MEM_ISO_B")
    await _seed_user(db_session, tenant=tenant_a, email="userA@example.com")
    await _seed_user(db_session, tenant=tenant_b, email="userB@example.com")

    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp_a = await ac.get(f"/api/v1/admin/tenants/{tenant_a.id}/members")
        resp_b = await ac.get(f"/api/v1/admin/tenants/{tenant_b.id}/members")

    assert resp_a.status_code == 200 and resp_b.status_code == 200
    emails_a = {item["email"] for item in resp_a.json()["items"]}
    emails_b = {item["email"] for item in resp_b.json()["items"]}
    assert emails_a == {"userA@example.com"}
    assert emails_b == {"userB@example.com"}


# =====================================================================
# Pagination
# =====================================================================
async def test_list_members_pagination(db_session: AsyncSession) -> None:
    """limit + offset return distinct slices ordered by created_at DESC."""
    tenant = await _seed_tenant(db_session, code="MEM_PAGE_T1")
    for i in range(3):
        await _seed_user(db_session, tenant=tenant, email=f"u{i}@example.com")

    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        page1 = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/members?limit=2&offset=0")
        page2 = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/members?limit=2&offset=2")
    assert page1.status_code == 200 and page2.status_code == 200
    body1 = page1.json()
    body2 = page2.json()
    assert body1["total"] == 3 and body2["total"] == 3
    assert len(body1["items"]) == 2
    assert len(body2["items"]) == 1
    ids1 = {item["id"] for item in body1["items"]}
    ids2 = {item["id"] for item in body2["items"]}
    assert ids1.isdisjoint(ids2)


async def test_list_members_empty_when_no_users(db_session: AsyncSession) -> None:
    """Tenant with 0 users → items=[] + total=0 (not 404)."""
    tenant = await _seed_tenant(db_session, code="MEM_EMPTY_T1")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/members")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 0


async def test_list_members_invalid_query_limit(db_session: AsyncSession) -> None:
    """limit > 200 → 422 (Pydantic Query validation; mirrors LIST endpoint)."""
    tenant = await _seed_tenant(db_session, code="MEM_LIM_T1")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/members?limit=500")
    assert resp.status_code == 422
