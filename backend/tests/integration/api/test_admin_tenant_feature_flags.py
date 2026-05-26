"""
File: backend/tests/integration/api/test_admin_tenant_feature_flags.py
Purpose: Integration tests — GET /admin/tenants/{tenant_id}/feature-flags (Sprint 57.48 Track B).
Category: Tests / Integration / API (Phase 58+ Backend Schema Extension wave)
Scope: Sprint 57.48 Day 1 Track B (closes AD-TenantSettings-FeatureFlags-Backend-AdminGet)

Description:
    Verifies the GET /admin/tenants/{tenant_id}/feature-flags endpoint:
    - 401 when no JWT context
    - 404 when tenant not found
    - 200 with empty list when no flags registered
    - 200 with resolved values (tenant_overrides applied over default_enabled)
    - Multi-tenant isolation (tenant A's override does NOT bleed into tenant B)
    - Response shape: items + total + limit + offset; items carry
      name/value/default_enabled/overridden/description/updated_at
    - Pagination (limit + offset) ordered by name ASC

Created: 2026-05-26 (Sprint 57.48 Day 1)

Modification History (newest-first):
    - 2026-05-26: Initial creation (Sprint 57.48 Day 1 Track B — FeatureFlags admin GET)
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
from infrastructure.db.models.feature_flag import FeatureFlag
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


async def _seed_flag(
    session: AsyncSession,
    *,
    name: str,
    default_enabled: bool = False,
    tenant_overrides: dict[str, Any] | None = None,
    description: str | None = None,
) -> FeatureFlag:
    ff = FeatureFlag(
        name=name,
        default_enabled=default_enabled,
        tenant_overrides=tenant_overrides or {},
        description=description,
    )
    session.add(ff)
    await session.flush()
    await session.refresh(ff)
    return ff


async def test_list_feature_flags_401_without_auth() -> None:
    app = _build_app()
    tenant_id = uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant_id}/feature-flags")
    assert resp.status_code == 401


async def test_list_feature_flags_404_when_tenant_not_found(db_session: AsyncSession) -> None:
    app = _build_app(db_session=db_session)
    missing_id = uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{missing_id}/feature-flags")
    assert resp.status_code == 404


async def test_list_feature_flags_empty_when_registry_empty(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code="FF_EMPTY_T1")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/feature-flags")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 0


async def test_list_feature_flags_resolves_default_when_no_override(
    db_session: AsyncSession,
) -> None:
    tenant = await _seed_tenant(db_session, code="FF_DEF_T1")
    await _seed_flag(db_session, name="ff.alpha", default_enabled=True)
    await _seed_flag(db_session, name="ff.beta", default_enabled=False)

    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/feature-flags")
    assert resp.status_code == 200, resp.text
    items = resp.json()["items"]
    by_name = {item["name"]: item for item in items}
    assert by_name["ff.alpha"]["value"] is True
    assert by_name["ff.alpha"]["overridden"] is False
    assert by_name["ff.beta"]["value"] is False
    assert by_name["ff.beta"]["overridden"] is False


async def test_list_feature_flags_applies_tenant_override(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code="FF_OVR_T1")
    await _seed_flag(
        db_session,
        name="ff.gamma",
        default_enabled=False,
        tenant_overrides={str(tenant.id): True},
    )

    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/feature-flags")
    assert resp.status_code == 200, resp.text
    item = next(i for i in resp.json()["items"] if i["name"] == "ff.gamma")
    assert item["value"] is True
    assert item["overridden"] is True
    assert item["default_enabled"] is False


async def test_list_feature_flags_response_shape(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code="FF_SHAPE_T1")
    await _seed_flag(db_session, name="ff.shape", default_enabled=True, description="desc")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/feature-flags")
    assert resp.status_code == 200, resp.text
    item = resp.json()["items"][0]
    expected = {"name", "value", "default_enabled", "overridden", "description", "updated_at"}
    assert expected.issubset(set(item.keys()))


async def test_list_feature_flags_tenant_isolation(db_session: AsyncSession) -> None:
    """Tenant A's override does not appear in tenant B's response."""
    tenant_a = await _seed_tenant(db_session, code="FF_ISO_A")
    tenant_b = await _seed_tenant(db_session, code="FF_ISO_B")
    await _seed_flag(
        db_session,
        name="ff.iso",
        default_enabled=False,
        tenant_overrides={str(tenant_a.id): True},
    )

    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp_a = await ac.get(f"/api/v1/admin/tenants/{tenant_a.id}/feature-flags")
        resp_b = await ac.get(f"/api/v1/admin/tenants/{tenant_b.id}/feature-flags")

    item_a = next(i for i in resp_a.json()["items"] if i["name"] == "ff.iso")
    item_b = next(i for i in resp_b.json()["items"] if i["name"] == "ff.iso")
    assert item_a["value"] is True and item_a["overridden"] is True
    assert item_b["value"] is False and item_b["overridden"] is False


async def test_list_feature_flags_pagination(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code="FF_PAGE_T1")
    for i in range(3):
        await _seed_flag(db_session, name=f"ff.page{i}", default_enabled=False)

    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        page1 = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/feature-flags?limit=2&offset=0")
        page2 = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/feature-flags?limit=2&offset=2")
    assert page1.status_code == 200 and page2.status_code == 200
    assert page1.json()["total"] == 3
    assert len(page1.json()["items"]) == 2
    assert len(page2.json()["items"]) == 1
