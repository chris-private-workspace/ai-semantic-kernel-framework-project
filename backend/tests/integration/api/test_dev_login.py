"""
File: backend/tests/integration/api/test_dev_login.py
Purpose: Integration tests — POST /api/v1/auth/dev-login (Sprint 57.13 US-A4).
Category: Tests / Integration / API (Phase 57+ Frontend Foundation)
Scope: Sprint 57.13 / Day 2 / US-A4

Description:
    Verifies the dev-only fake-login endpoint:
    - dev env → 200 with {user, tenant, roles} payload + v2_jwt cookie;
      the dev tenant + user are created; the JWT decodes with valid claims
    - idempotent: a second call reuses the same tenant + user (no dup rows)
    - production (Settings.env in {production, prod}) → 404 (route invisible)

    Pattern mirrors test_auth_me.py (custom app + TenantContextMiddleware +
    dependency_overrides[get_db_session]).

Created: 2026-05-10 (Sprint 57.13 Day 2)
Last Modified: 2026-05-10
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.auth import router as auth_router
from core.config import get_settings
from infrastructure.db.models.identity import Tenant, User
from infrastructure.db.session import get_db_session
from platform_layer.identity.jwt import JWTManager
from platform_layer.middleware import TenantContextMiddleware

pytestmark = pytest.mark.asyncio


def _build_app(db_session: AsyncSession) -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        TenantContextMiddleware,
        jwt_manager=JWTManager(secret="dev-login-secret", algorithm="HS256", expires_minutes=60),
    )
    app.include_router(auth_router, prefix="/api/v1")

    async def _override_session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db_session] = _override_session
    return app


async def test_dev_login_dev_env_returns_payload_and_cookie(db_session: AsyncSession) -> None:
    app = _build_app(db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/v1/auth/dev-login",
            params={"tenant_code": "DEVLOGIN_T", "email": "alice@dev.local"},
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["tenant"]["code"] == "DEVLOGIN_T"
    assert body["tenant"]["name"] == "Dev Tenant (DEVLOGIN_T)"
    assert body["user"]["email"] == "alice@dev.local"
    assert "platform_admin" in body["roles"]
    assert "v2_jwt" in resp.cookies

    tenant = (
        await db_session.execute(select(Tenant).where(Tenant.code == "DEVLOGIN_T"))
    ).scalar_one()
    user = (
        await db_session.execute(select(User).where(User.external_id == "dev:alice@dev.local"))
    ).scalar_one()
    assert user.tenant_id == tenant.id
    assert str(user.id) == body["user"]["id"]

    # The issued JWT decodes (same default secret) with the expected claims.
    claims = JWTManager().decode(resp.cookies["v2_jwt"])
    assert claims.tenant_id == tenant.id
    assert "platform_admin" in claims.roles
    assert claims.sub == str(user.id)


async def test_dev_login_idempotent_reuses_tenant_and_user(db_session: AsyncSession) -> None:
    app = _build_app(db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r1 = await ac.post(
            "/api/v1/auth/dev-login",
            params={"tenant_code": "DEVLOGIN_RT", "email": "bob@dev.local"},
        )
        r2 = await ac.post(
            "/api/v1/auth/dev-login",
            params={"tenant_code": "DEVLOGIN_RT", "email": "bob@dev.local"},
        )
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json()["user"]["id"] == r2.json()["user"]["id"]
    assert r1.json()["tenant"]["id"] == r2.json()["tenant"]["id"]

    tenants = (
        (await db_session.execute(select(Tenant).where(Tenant.code == "DEVLOGIN_RT")))
        .scalars()
        .all()
    )
    users = (
        (await db_session.execute(select(User).where(User.external_id == "dev:bob@dev.local")))
        .scalars()
        .all()
    )
    assert len(tenants) == 1
    assert len(users) == 1


async def test_dev_login_404_in_production(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ENV", "production")
    get_settings.cache_clear()
    try:
        app = _build_app(db_session)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                "/api/v1/auth/dev-login",
                params={"tenant_code": "dev", "email": "x@y.z"},
            )
        assert resp.status_code == 404
    finally:
        get_settings.cache_clear()
