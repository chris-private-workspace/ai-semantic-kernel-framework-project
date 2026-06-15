"""
File: backend/tests/integration/api/test_auth_me.py
Purpose: Integration tests — GET /api/v1/auth/me (Sprint 57.13 US-A1).
Category: Tests / Integration / API (Phase 57+ Frontend Foundation)
Scope: Sprint 57.13 / Day 1 / US-A1

Description:
    Verifies GET /api/v1/auth/me:
    - 401 when no JWT (neither Bearer header nor v2_jwt cookie)
    - 401 when the JWT is expired
    - 200 with a valid v2_jwt *cookie* → {user, tenant, roles} payload
    - 200 with a valid Authorization: Bearer header → same payload
    - 401 when the JWT is valid but the referenced user row is gone

    Mirrors test_jwt_auth.py (custom FastAPI app + TenantContextMiddleware
    with a test JWTManager) + test_admin_tenant_get.py (dependency_overrides
    for the DB session) patterns.

Created: 2026-05-10 (Sprint 57.13 Day 1)
Last Modified: 2026-06-15 (Sprint 57.123 — assert tenant.plan + tenant.region carry real DB values)
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.auth import router as auth_router
from platform_layer.identity.jwt import JWTManager
from platform_layer.middleware import TenantContextMiddleware
from platform_layer.middleware.tenant_context import get_db_session_with_tenant
from tests.conftest import seed_tenant, seed_user

pytestmark = pytest.mark.asyncio

_SECRET = "auth-me-integ-secret"


def _mgr(*, expires_minutes: int = 60) -> JWTManager:
    return JWTManager(secret=_SECRET, algorithm="HS256", expires_minutes=expires_minutes)


def _build_app(
    db_session: AsyncSession | None = None,
    *,
    jwt_manager: JWTManager | None = None,
) -> FastAPI:
    app = FastAPI()
    app.add_middleware(TenantContextMiddleware, jwt_manager=jwt_manager or _mgr())
    app.include_router(auth_router, prefix="/api/v1")
    if db_session is not None:

        async def _override_session() -> AsyncIterator[AsyncSession]:
            yield db_session

        app.dependency_overrides[get_db_session_with_tenant] = _override_session
    return app


async def test_me_401_without_jwt() -> None:
    """No Bearer header AND no v2_jwt cookie → middleware 401 before the handler."""
    app = _build_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/auth/me")
    assert resp.status_code == 401


async def test_me_401_expired_jwt() -> None:
    """Expired (but well-formed, correctly-signed) JWT → 401."""
    mgr = _mgr(expires_minutes=-1)
    token = mgr.encode(sub=str(uuid4()), tenant_id=uuid4())
    app = _build_app(jwt_manager=mgr)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


async def test_me_200_with_cookie(db_session: AsyncSession) -> None:
    """Valid v2_jwt cookie → 200 with full {user, tenant, roles} payload."""
    tenant = await seed_tenant(db_session, code="AUTHME_T", display_name="AuthMe Tenant")
    user = await seed_user(db_session, tenant, email="me@authme.test", display_name="Me User")
    token = _mgr().encode(sub=str(user.id), tenant_id=tenant.id, roles=["user", "admin"])
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies={"v2_jwt": token}
    ) as ac:
        resp = await ac.get("/api/v1/auth/me")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["user"]["id"] == str(user.id)
    assert body["user"]["email"] == "me@authme.test"
    assert body["user"]["display_name"] == "Me User"
    assert body["tenant"]["id"] == str(tenant.id)
    assert body["tenant"]["name"] == "AuthMe Tenant"
    assert body["tenant"]["code"] == "AUTHME_T"
    # Sprint 57.123: real Tenant display fields present (server defaults here).
    assert body["tenant"]["plan"] == "enterprise"
    assert body["tenant"]["region"] == "global"
    assert body["roles"] == ["user", "admin"]


async def test_me_200_with_bearer(db_session: AsyncSession) -> None:
    """Valid Authorization: Bearer header → 200 (same handler path as the cookie)."""
    tenant = await seed_tenant(db_session, code="AUTHME_B", display_name="AuthMe B")
    user = await seed_user(db_session, tenant, email="b@authme.test")
    token = _mgr().encode(sub=str(user.id), tenant_id=tenant.id, roles=["user"])
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["user"]["id"] == str(user.id)
    assert resp.json()["roles"] == ["user"]


async def test_me_tenant_plan_and_region_are_real(db_session: AsyncSession) -> None:
    """tenant.plan + tenant.region flow from the real Tenant columns, not a fixture.

    Sprint 57.123: proves the chrome's plan badge + region row read live DB
    values — seed a tenant, override region to a distinctive value, and assert
    /auth/me returns it (a hardcoded "global" would fail this).
    """
    tenant = await seed_tenant(db_session, code="AUTHME_REGION", display_name="Region Tenant")
    tenant.region = "ap-southeast-7"  # non-default → proves it's read from the DB
    await db_session.flush()
    user = await seed_user(db_session, tenant, email="r@authme.test")
    token = _mgr().encode(sub=str(user.id), tenant_id=tenant.id, roles=["user"])
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200, resp.text
    tenant_body = resp.json()["tenant"]
    assert tenant_body["plan"] == "enterprise"
    assert tenant_body["region"] == "ap-southeast-7"


async def test_me_401_when_user_row_missing(db_session: AsyncSession) -> None:
    """Signature valid + tenant exists, but the user_id has no row → 401."""
    tenant = await seed_tenant(db_session, code="AUTHME_GHOST", display_name="Ghost")
    token = _mgr().encode(sub=str(uuid4()), tenant_id=tenant.id, roles=["user"])
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
    assert "no longer exists" in resp.json()["detail"]
