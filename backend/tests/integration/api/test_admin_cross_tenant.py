"""
File: backend/tests/integration/api/test_admin_cross_tenant.py
Purpose: Integration tests — require_tenant_match_or_platform_admin dependency (Sprint 57.13 US-A3).
Category: Tests / Integration / API (Phase 57+ Frontend Foundation)
Scope: Sprint 57.13 / Day 2 / US-A3

Description:
    Exercises the cross-tenant authorization dep used by the
    /api/v1/admin/tenants/{tenant_id}/... read endpoints (GET tenant /
    cost-summary / sla-report) via a tiny probe endpoint:

    - platform admin ("platform_admin" or "admin" role) → any tenant → 200
    - regular role + path tenant == caller's tenant → 200 (own-tenant read)
    - regular role + path tenant != caller's tenant → 403 (the closed hole)
    - no JWT context (no user_id) → 401
    - roles claim missing / not a list → 500 (middleware contract violation)

    Pattern mirrors test_admin_tenant_get.py (X-Test-User / X-Test-Roles /
    X-Test-Tenant headers populate request.state).

Created: 2026-05-10 (Sprint 57.13 Day 2)
Last Modified: 2026-05-10
"""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from uuid import UUID, uuid4

import pytest
from fastapi import Depends, FastAPI, Request, Response
from httpx import ASGITransport, AsyncClient

from platform_layer.identity.auth import require_tenant_match_or_platform_admin

pytestmark = pytest.mark.asyncio


def _build_app() -> FastAPI:
    app = FastAPI()

    @app.middleware("http")
    async def _populate_state(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        u = request.headers.get("X-Test-User")
        r = request.headers.get("X-Test-Roles")
        t = request.headers.get("X-Test-Tenant")
        request.state.user_id = UUID(u) if u else None
        request.state.roles = json.loads(r) if r else None
        request.state.tenant_id = UUID(t) if t else None
        return await call_next(request)

    @app.get("/api/v1/admin/tenants/{tenant_id}/probe")
    async def probe(
        tenant_id: UUID,
        user_id: UUID = Depends(require_tenant_match_or_platform_admin),
    ) -> dict[str, str]:
        return {"user_id": str(user_id), "tenant_id": str(tenant_id)}

    return app


async def _probe(
    *,
    path_tenant: UUID,
    user: UUID | None = None,
    roles: list[str] | None = None,
    caller_tenant: UUID | None = None,
) -> Response:
    headers: dict[str, str] = {}
    if user is not None:
        headers["X-Test-User"] = str(user)
    if roles is not None:
        headers["X-Test-Roles"] = json.dumps(roles)
    if caller_tenant is not None:
        headers["X-Test-Tenant"] = str(caller_tenant)
    transport = ASGITransport(app=_build_app())
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        return await ac.get(f"/api/v1/admin/tenants/{path_tenant}/probe", headers=headers)


async def test_platform_admin_any_tenant_200() -> None:
    user, path_t, caller_t = uuid4(), uuid4(), uuid4()  # caller != path
    resp = await _probe(
        path_tenant=path_t, user=user, roles=["platform_admin"], caller_tenant=caller_t
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["user_id"] == str(user)


async def test_admin_role_also_any_tenant_200() -> None:
    user, path_t, caller_t = uuid4(), uuid4(), uuid4()
    resp = await _probe(path_tenant=path_t, user=user, roles=["admin"], caller_tenant=caller_t)
    assert resp.status_code == 200, resp.text


async def test_regular_user_own_tenant_200() -> None:
    user, tenant = uuid4(), uuid4()
    resp = await _probe(path_tenant=tenant, user=user, roles=["user"], caller_tenant=tenant)
    assert resp.status_code == 200, resp.text
    assert resp.json()["user_id"] == str(user)


async def test_regular_user_other_tenant_403() -> None:
    user, path_t, caller_t = uuid4(), uuid4(), uuid4()  # different
    resp = await _probe(
        path_tenant=path_t, user=user, roles=["tenant_admin"], caller_tenant=caller_t
    )
    assert resp.status_code == 403
    assert "cross-tenant" in resp.json()["detail"]


async def test_no_user_id_401() -> None:
    resp = await _probe(path_tenant=uuid4(), roles=["user"], caller_tenant=uuid4())  # no user
    assert resp.status_code == 401


async def test_roles_missing_500() -> None:
    resp = await _probe(path_tenant=uuid4(), user=uuid4())  # user set, roles None
    assert resp.status_code == 500
    assert "roles middleware contract" in resp.json()["detail"]
