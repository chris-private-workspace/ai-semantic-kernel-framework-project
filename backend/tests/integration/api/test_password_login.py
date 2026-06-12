"""
File: backend/tests/integration/api/test_password_login.py
Purpose: POST /auth/password-login integration tests (Sprint 57.86 / US-2..US-5;
         Sprint 57.105 DB-sourced roles claim chain).
Category: Tests / Integration / API (C-12 IAM credentials)
Created: 2026-06-06 (Sprint 57.86 Day 3)
Modified: 2026-06-12 (Sprint 57.105 — DB-sourced claim: grant/cross-tenant/founding-admin chain)

Verifies the endpoint end-to-end over a real Postgres test session:
  - success → 200 + v2_jwt cookie + AuthMeResponse shape (US-2)
  - generic 401 (identical status + body) for wrong password / SSO-only user /
    unknown tenant / unknown email — no enumeration (US-3)
  - 2-tenant isolation: same email in two tenants logs in only with its own
    tenant_code + password (US-5)
  - full-stack: admin invite-create → guest accept(password) → password-login
    succeeds (proves the invite-accept-stored bcrypt hash round-trips; US-5)
  - audit row written on success
  - exempt-path contract (password-login exempt; /auth/me NOT)

The route session is the injected test db_session (override does NOT commit) so
all writes roll back at teardown — the services never commit internally.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Awaitable, Callable
from uuid import UUID

from fastapi import FastAPI, Request, Response
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.auth import router as auth_router
from api.v1.invites import router as invites_router
from api.v1.tenants import router as tenants_router
from infrastructure.db.models.audit import AuditLog
from infrastructure.db.models.identity import Role, User, UserRole
from infrastructure.db.session import get_db_session
from platform_layer.identity.auth import require_admin_platform_role
from platform_layer.identity.credentials import CredentialsService
from platform_layer.identity.jwt import JWTManager
from platform_layer.middleware.tenant_context import TenantContextMiddleware
from tests.conftest import seed_tenant, seed_user

_GENERIC_401_DETAIL = "Invalid credentials"


def _build_app(db_session: AsyncSession, admin_user_id: UUID | None = None) -> FastAPI:
    app = FastAPI()
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(invites_router, prefix="/api/v1")

    @app.middleware("http")
    async def _populate_test_state(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        user_header = request.headers.get("X-Test-User")
        roles_header = request.headers.get("X-Test-Roles")
        request.state.user_id = UUID(user_header) if user_header else None
        request.state.roles = json.loads(roles_header) if roles_header else None
        request.state.tenant_id = None
        return await call_next(request)

    async def _override_session() -> AsyncIterator[AsyncSession]:
        yield db_session  # no commit — rolls back at fixture teardown

    async def _override_admin() -> UUID:
        return admin_user_id or UUID("00000000-0000-0000-0000-000000000001")

    app.dependency_overrides[get_db_session] = _override_session
    app.dependency_overrides[require_admin_platform_role] = _override_admin
    return app


def _client(app: FastAPI) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _ctx(db: AsyncSession, tenant_id: object) -> None:
    await db.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(tenant_id)})


async def _seed_user_with_password(
    db: AsyncSession, *, code: str, email: str, password: str
) -> object:
    tenant = await seed_tenant(db, code=code)
    await _ctx(db, tenant.id)
    user = await seed_user(db, tenant, email=email)
    await CredentialsService().set_password(user=user, raw=password)
    await db.flush()
    return tenant


def _assert_generic_401(resp: Response) -> None:
    assert resp.status_code == 401, resp.text
    assert resp.json()["detail"] == _GENERIC_401_DETAIL


# ----- success -------------------------------------------------------------


async def test_password_login_success(db_session: AsyncSession) -> None:
    """US-2 — correct creds → 200 + v2_jwt cookie + AuthMeResponse."""
    tenant = await _seed_user_with_password(
        db_session, code="PWL_OK", email="ok@pwl.test", password="rightpw123"
    )
    app = _build_app(db_session)
    async with _client(app) as ac:
        resp = await ac.post(
            "/api/v1/auth/password-login",
            json={"tenant_code": "PWL_OK", "email": "ok@pwl.test", "password": "rightpw123"},
        )
    assert resp.status_code == 200, resp.text
    cookie = resp.cookies.get("v2_jwt")
    assert cookie and JWTManager().verify(cookie) is True
    body = resp.json()
    assert body["user"]["email"] == "ok@pwl.test"
    assert body["tenant"]["code"] == "PWL_OK"
    assert body["tenant"]["id"] == str(tenant.id)
    assert body["roles"] == ["user"]


# ----- generic 401 (anti-enumeration) --------------------------------------


async def test_wrong_password_generic_401(db_session: AsyncSession) -> None:
    await _seed_user_with_password(
        db_session, code="PWL_WRONG", email="w@pwl.test", password="rightpw123"
    )
    app = _build_app(db_session)
    async with _client(app) as ac:
        resp = await ac.post(
            "/api/v1/auth/password-login",
            json={"tenant_code": "PWL_WRONG", "email": "w@pwl.test", "password": "WRONGpw"},
        )
    _assert_generic_401(resp)


async def test_sso_only_user_generic_401(db_session: AsyncSession) -> None:
    """US-3 — a user with no local password (SSO-only) cannot password-login."""
    tenant = await seed_tenant(db_session, code="PWL_SSO")
    await _ctx(db_session, tenant.id)
    await seed_user(db_session, tenant, email="sso@pwl.test")  # no set_password
    await db_session.flush()
    app = _build_app(db_session)
    async with _client(app) as ac:
        resp = await ac.post(
            "/api/v1/auth/password-login",
            json={"tenant_code": "PWL_SSO", "email": "sso@pwl.test", "password": "anything"},
        )
    _assert_generic_401(resp)


async def test_unknown_tenant_generic_401(db_session: AsyncSession) -> None:
    app = _build_app(db_session)
    async with _client(app) as ac:
        resp = await ac.post(
            "/api/v1/auth/password-login",
            json={"tenant_code": "NO_SUCH", "email": "x@pwl.test", "password": "anything"},
        )
    _assert_generic_401(resp)


async def test_unknown_email_generic_401(db_session: AsyncSession) -> None:
    await _seed_user_with_password(
        db_session, code="PWL_NOEMAIL", email="real@pwl.test", password="rightpw123"
    )
    app = _build_app(db_session)
    async with _client(app) as ac:
        resp = await ac.post(
            "/api/v1/auth/password-login",
            json={
                "tenant_code": "PWL_NOEMAIL",
                "email": "ghost@pwl.test",
                "password": "rightpw123",
            },
        )
    _assert_generic_401(resp)


# ----- isolation -----------------------------------------------------------


async def test_two_tenant_isolation(db_session: AsyncSession) -> None:
    """US-5 — same email in two tenants logs in only with its own tenant + password."""
    await _seed_user_with_password(
        db_session, code="PWL_ISO_A", email="dup@iso.test", password="pwAAAA1"
    )
    await _seed_user_with_password(
        db_session, code="PWL_ISO_B", email="dup@iso.test", password="pwBBBB2"
    )
    app = _build_app(db_session)
    async with _client(app) as ac:
        ok_a = await ac.post(
            "/api/v1/auth/password-login",
            json={"tenant_code": "PWL_ISO_A", "email": "dup@iso.test", "password": "pwAAAA1"},
        )
        # tenant A's user cannot be unlocked with tenant B's password
        cross = await ac.post(
            "/api/v1/auth/password-login",
            json={"tenant_code": "PWL_ISO_A", "email": "dup@iso.test", "password": "pwBBBB2"},
        )
        ok_b = await ac.post(
            "/api/v1/auth/password-login",
            json={"tenant_code": "PWL_ISO_B", "email": "dup@iso.test", "password": "pwBBBB2"},
        )
    assert ok_a.status_code == 200, ok_a.text
    assert ok_a.json()["tenant"]["code"] == "PWL_ISO_A"
    _assert_generic_401(cross)
    assert ok_b.status_code == 200, ok_b.text
    assert ok_b.json()["tenant"]["code"] == "PWL_ISO_B"


# ----- full-stack: invite-accept(password) → password-login ----------------


async def test_invite_accept_then_password_login(db_session: AsyncSession) -> None:
    """US-5 — the password set at invite-accept logs in via password-login (e2e)."""
    tenant = await seed_tenant(db_session, code="PWL_INV")
    await _ctx(db_session, tenant.id)
    role = Role(tenant_id=tenant.id, code="member", display_name="Member")
    db_session.add(role)
    await db_session.flush()
    inviter = await seed_user(db_session, tenant, email="admin@pwlinv.test")
    app = _build_app(db_session, admin_user_id=inviter.id)

    async with _client(app) as ac:
        create = await ac.post(
            f"/api/v1/admin/tenants/{tenant.id}/invites",
            json={"email": "joiner@pwlinv.test", "role_id": str(role.id)},
            headers={
                "X-Test-User": str(inviter.id),
                "X-Test-Roles": json.dumps(["platform_admin"]),
            },
        )
        assert create.status_code == 201, create.text
        token = create.json()["token"]
        accept = await ac.post(
            f"/api/v1/invites/{token}/accept",
            json={"full_name": "Joiner One", "password": "setatinvite9"},
        )
        assert accept.status_code == 200, accept.text
        # now sign in with the password set at invite-accept
        login = await ac.post(
            "/api/v1/auth/password-login",
            json={
                "tenant_code": "PWL_INV",
                "email": "joiner@pwlinv.test",
                "password": "setatinvite9",
            },
        )
    assert login.status_code == 200, login.text
    assert login.json()["user"]["email"] == "joiner@pwlinv.test"
    assert login.cookies.get("v2_jwt")
    # Sprint 57.105: the invited role is claim-effective at first real login
    assert login.json()["roles"] == ["member", "user"]


# ----- DB-sourced roles claim (Sprint 57.105) -------------------------------


async def test_login_claim_carries_db_role_grants(db_session: AsyncSession) -> None:
    """US-3/US-4 — a Role(code='admin') grant → claim + body roles == ['admin', 'user']."""
    tenant = await _seed_user_with_password(
        db_session, code="PWL_RBAC", email="boss@pwl.test", password="rightpw123"
    )
    user = (
        await db_session.execute(select(User).where(User.email == "boss@pwl.test"))
    ).scalar_one()
    role = Role(tenant_id=tenant.id, code="admin", display_name="Admin")
    db_session.add(role)
    await db_session.flush()
    db_session.add(UserRole(user_id=user.id, role_id=role.id))
    await db_session.flush()

    app = _build_app(db_session)
    async with _client(app) as ac:
        resp = await ac.post(
            "/api/v1/auth/password-login",
            json={"tenant_code": "PWL_RBAC", "email": "boss@pwl.test", "password": "rightpw123"},
        )
    assert resp.status_code == 200, resp.text
    assert resp.json()["roles"] == ["admin", "user"]
    claims = JWTManager().decode(resp.cookies["v2_jwt"])
    assert claims.roles == ["admin", "user"]


async def test_login_claim_ignores_other_tenant_grants(db_session: AsyncSession) -> None:
    """multi-tenant 鐵律 — a grant under ANOTHER tenant never leaks into the claim."""
    tenant = await _seed_user_with_password(
        db_session, code="PWL_XT_A", email="xt@pwl.test", password="rightpw123"
    )
    assert tenant is not None
    user = (await db_session.execute(select(User).where(User.email == "xt@pwl.test"))).scalar_one()
    other = await seed_tenant(db_session, code="PWL_XT_B")
    await _ctx(db_session, other.id)
    foreign_role = Role(tenant_id=other.id, code="admin", display_name="Admin B")
    db_session.add(foreign_role)
    await db_session.flush()
    db_session.add(UserRole(user_id=user.id, role_id=foreign_role.id))
    await db_session.flush()

    app = _build_app(db_session)
    async with _client(app) as ac:
        resp = await ac.post(
            "/api/v1/auth/password-login",
            json={"tenant_code": "PWL_XT_A", "email": "xt@pwl.test", "password": "rightpw123"},
        )
    assert resp.status_code == 200, resp.text
    assert resp.json()["roles"] == ["user"]  # the foreign-tenant grant is invisible
    assert JWTManager().decode(resp.cookies["v2_jwt"]).roles == ["user"]


async def test_register_then_password_login_claim_is_admin(db_session: AsyncSession) -> None:
    """US-4 founding-admin chain — the 57.87 register-seeded admin grant becomes
    claim-effective at the first real login. Register collects NO password (D11),
    so the password is set via CredentialsService (the 57.86-proven primitive)."""
    app = _build_app(db_session)
    app.include_router(tenants_router, prefix="/api/v1")
    async with _client(app) as ac:
        reg = await ac.post(
            "/api/v1/tenants/register",
            json={
                "email": "founder@pwl105.test",
                "full_name": "Founder 105",
                "company_name": "Co 105",
                "tenant_slug": "pwl105",
                "region": "global",
                "plan": "pro",
                "size": "11-50",
            },
        )
        assert reg.status_code == 201, reg.text
        user_id = UUID(reg.json()["user"]["id"])
        tenant_id = reg.json()["tenant"]["id"]
        founder = (await db_session.execute(select(User).where(User.id == user_id))).scalar_one()
        await _ctx(db_session, tenant_id)
        await CredentialsService().set_password(user=founder, raw="founderpw1")
        await db_session.flush()

        login = await ac.post(
            "/api/v1/auth/password-login",
            json={
                "tenant_code": "pwl105",
                "email": "founder@pwl105.test",
                "password": "founderpw1",
            },
        )
    assert login.status_code == 200, login.text
    assert login.json()["roles"] == ["admin", "user"]
    claims = JWTManager().decode(login.cookies["v2_jwt"])
    assert claims.roles == ["admin", "user"]


# ----- audit ---------------------------------------------------------------


async def test_audit_row_on_success(db_session: AsyncSession) -> None:
    tenant = await _seed_user_with_password(
        db_session, code="PWL_AUDIT", email="a@pwl.test", password="rightpw123"
    )
    app = _build_app(db_session)
    async with _client(app) as ac:
        resp = await ac.post(
            "/api/v1/auth/password-login",
            json={"tenant_code": "PWL_AUDIT", "email": "a@pwl.test", "password": "rightpw123"},
        )
    assert resp.status_code == 200, resp.text
    user_id = UUID(resp.json()["user"]["id"])
    await _ctx(db_session, tenant.id)
    rows = (
        (await db_session.execute(select(AuditLog).where(AuditLog.resource_id == str(user_id))))
        .scalars()
        .all()
    )
    assert any(r.operation == "password_login" for r in rows)


# ----- exempt-path contract ------------------------------------------------


def test_exempt_path_contract() -> None:
    """password-login is exempt (pre-JWT); /auth/me is NOT."""
    exempt = TenantContextMiddleware.EXEMPT_PATH_PREFIXES
    assert "/api/v1/auth/password-login" in exempt
    assert not any("/api/v1/auth/me".startswith(p) for p in exempt)
