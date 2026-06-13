"""
File: backend/tests/integration/api/test_mfa_endpoints.py
Purpose: POST /api/v1/mfa/{enroll,enroll/confirm,verify} + password-login MFA-gate
         integration tests (Sprint 57.112 / US-2).
Category: Tests / Integration / API (C-12 IAM Block C MFA)
Created: 2026-06-13 (Sprint 57.112 Day 2)

Verifies the endpoints end-to-end over a real Postgres test session:
  - full flow: enroll → confirm → password-login (mfa_required) → verify → session
  - password-login with mfa_enabled → {mfa_required:true} + v2_mfa_challenge cookie,
    NO v2_jwt (no session until the second factor)
  - password-login without MFA unchanged → v2_jwt, no challenge (regression)
  - verify is challenge-gated: missing / non-mfa_pending challenge → 401
  - verify wrong code → generic 401; webauthn → honest 400
  - enroll already-enabled → 409
  - EXEMPT contract: /mfa/verify exempt (pre-session); /mfa/enroll NOT

Both get_db_session (raw, for verify + password-login) and get_db_session_with_tenant
(enroll/confirm) are overridden to the injected test db_session (no commit → rolls
back at teardown). TOTPService is stateless (no reset fixture needed; mirrors the
CredentialsService pattern).
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Awaitable, Callable
from uuid import UUID

import pyotp
from fastapi import FastAPI, Request, Response
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.auth import router as auth_router
from api.v1.mfa import router as mfa_router
from infrastructure.db.session import get_db_session
from platform_layer.identity.credentials import CredentialsService
from platform_layer.identity.jwt import JWTManager
from platform_layer.middleware.tenant_context import (
    TenantContextMiddleware,
    get_db_session_with_tenant,
)
from tests.conftest import seed_tenant, seed_user

_CHALLENGE_COOKIE = "v2_mfa_challenge"


def _build_app(db_session: AsyncSession) -> FastAPI:
    app = FastAPI()
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(mfa_router, prefix="/api/v1")

    @app.middleware("http")
    async def _populate_test_state(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        user_header = request.headers.get("X-Test-User")
        tenant_header = request.headers.get("X-Test-Tenant")
        roles_header = request.headers.get("X-Test-Roles")
        request.state.user_id = UUID(user_header) if user_header else None
        request.state.tenant_id = UUID(tenant_header) if tenant_header else None
        request.state.roles = json.loads(roles_header) if roles_header else None
        return await call_next(request)

    async def _override_session() -> AsyncIterator[AsyncSession]:
        yield db_session  # no commit — rolls back at fixture teardown

    # enroll/confirm use the tenant dep (which normally opens its OWN session +
    # SET LOCAL + commit); override to the test session (the service sets RLS itself).
    app.dependency_overrides[get_db_session] = _override_session
    app.dependency_overrides[get_db_session_with_tenant] = _override_session
    return app


def _client(app: FastAPI) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _ctx(db: AsyncSession, tenant_id: object) -> None:
    await db.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(tenant_id)})


async def _seed_user_with_password(
    db: AsyncSession, *, code: str, email: str, password: str
) -> tuple[object, object]:
    tenant = await seed_tenant(db, code=code)
    await _ctx(db, tenant.id)
    user = await seed_user(db, tenant, email=email)
    await CredentialsService().set_password(user=user, raw=password)
    await db.flush()
    return tenant, user


async def _seed_enrolled_user(
    db: AsyncSession, *, code: str, email: str, password: str
) -> tuple[object, object, str]:
    """Seed a user with a password + an already-enabled TOTP secret (direct ORM)."""
    tenant, user = await _seed_user_with_password(db, code=code, email=email, password=password)
    secret = pyotp.random_base32()
    user.totp_secret = secret  # type: ignore[attr-defined]
    user.mfa_enabled = True  # type: ignore[attr-defined]
    await db.flush()
    return tenant, user, secret


def _challenge_cookie(user_id: object, tenant_id: object, *, mfa_pending: bool = True) -> str:
    extra = {"mfa_pending": True} if mfa_pending else {"foo": "bar"}
    return JWTManager().encode(sub=str(user_id), tenant_id=tenant_id, roles=[], extra=extra)


# ----- full flow -----------------------------------------------------------


async def test_full_flow_enroll_confirm_login_verify(db_session: AsyncSession) -> None:
    """US-2 e2e — enroll → confirm → password-login(mfa_required) → verify → session."""
    tenant, user = await _seed_user_with_password(
        db_session, code="MFAE_FLOW", email="flow@mfae.test", password="rightpw123"
    )
    hdrs = {"X-Test-User": str(user.id), "X-Test-Tenant": str(tenant.id)}
    app = _build_app(db_session)
    async with _client(app) as ac:
        enroll = await ac.post("/api/v1/mfa/enroll", headers=hdrs)
        assert enroll.status_code == 200, enroll.text
        secret = enroll.json()["secret"]
        assert enroll.json()["otpauth_uri"].startswith("otpauth://totp/")

        confirm = await ac.post(
            "/api/v1/mfa/enroll/confirm",
            headers=hdrs,
            json={"code": pyotp.TOTP(secret).now()},
        )
        assert confirm.status_code == 200, confirm.text
        assert confirm.json()["mfa_enabled"] is True

        login = await ac.post(
            "/api/v1/auth/password-login",
            json={"tenant_code": "MFAE_FLOW", "email": "flow@mfae.test", "password": "rightpw123"},
        )
        assert login.status_code == 200, login.text
        assert login.json() == {"mfa_required": True}
        assert login.cookies.get(_CHALLENGE_COOKIE)
        assert login.cookies.get("v2_jwt") is None  # NO session yet

        verify = await ac.post(
            "/api/v1/mfa/verify",
            json={"method": "totp", "code": pyotp.TOTP(secret).now()},
        )
    assert verify.status_code == 200, verify.text
    assert verify.json()["user"]["email"] == "flow@mfae.test"
    assert verify.json()["roles"] == ["user"]
    assert verify.cookies.get("v2_jwt")  # full session granted
    assert JWTManager().verify(verify.cookies["v2_jwt"]) is True


# ----- password-login MFA-gate ---------------------------------------------


async def test_password_login_mfa_enabled_returns_challenge(db_session: AsyncSession) -> None:
    tenant, user, _secret = await _seed_enrolled_user(
        db_session, code="MFAE_GATE", email="gate@mfae.test", password="rightpw123"
    )
    app = _build_app(db_session)
    async with _client(app) as ac:
        resp = await ac.post(
            "/api/v1/auth/password-login",
            json={"tenant_code": "MFAE_GATE", "email": "gate@mfae.test", "password": "rightpw123"},
        )
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"mfa_required": True}
    assert resp.cookies.get(_CHALLENGE_COOKIE)
    assert resp.cookies.get("v2_jwt") is None


async def test_password_login_no_mfa_unchanged(db_session: AsyncSession) -> None:
    """Regression — a user WITHOUT MFA still gets a session directly (no challenge)."""
    await _seed_user_with_password(
        db_session, code="MFAE_NOMFA", email="no@mfae.test", password="rightpw123"
    )
    app = _build_app(db_session)
    async with _client(app) as ac:
        resp = await ac.post(
            "/api/v1/auth/password-login",
            json={"tenant_code": "MFAE_NOMFA", "email": "no@mfae.test", "password": "rightpw123"},
        )
    assert resp.status_code == 200, resp.text
    assert resp.cookies.get("v2_jwt")
    assert resp.cookies.get(_CHALLENGE_COOKIE) is None
    assert resp.json()["user"]["email"] == "no@mfae.test"


# ----- verify challenge-gating ---------------------------------------------


async def test_verify_without_challenge_401(db_session: AsyncSession) -> None:
    app = _build_app(db_session)
    async with _client(app) as ac:
        resp = await ac.post("/api/v1/mfa/verify", json={"method": "totp", "code": "123456"})
    assert resp.status_code == 401, resp.text


async def test_verify_non_pending_challenge_401(db_session: AsyncSession) -> None:
    """A token without mfa_pending (e.g. a stray session JWT) is not a valid challenge."""
    tenant, user, _secret = await _seed_enrolled_user(
        db_session, code="MFAE_NP", email="np@mfae.test", password="rightpw123"
    )
    cookie = _challenge_cookie(user.id, tenant.id, mfa_pending=False)
    app = _build_app(db_session)
    async with _client(app) as ac:
        ac.cookies.set(_CHALLENGE_COOKIE, cookie)
        resp = await ac.post("/api/v1/mfa/verify", json={"method": "totp", "code": "123456"})
    assert resp.status_code == 401, resp.text


async def test_verify_wrong_code_401(db_session: AsyncSession) -> None:
    tenant, user, secret = await _seed_enrolled_user(
        db_session, code="MFAE_WRONG", email="wrong@mfae.test", password="rightpw123"
    )
    valid = {pyotp.TOTP(secret).now()}
    wrong = next(f"{n:06d}" for n in range(1000000) if f"{n:06d}" not in valid)
    app = _build_app(db_session)
    async with _client(app) as ac:
        ac.cookies.set(_CHALLENGE_COOKIE, _challenge_cookie(user.id, tenant.id))
        resp = await ac.post("/api/v1/mfa/verify", json={"method": "totp", "code": wrong})
    assert resp.status_code == 401, resp.text


async def test_verify_webauthn_400(db_session: AsyncSession) -> None:
    """WebAuthn is not supported this release → honest 400 (not a faked success)."""
    tenant, user, _secret = await _seed_enrolled_user(
        db_session, code="MFAE_WA", email="wa@mfae.test", password="rightpw123"
    )
    app = _build_app(db_session)
    async with _client(app) as ac:
        ac.cookies.set(_CHALLENGE_COOKIE, _challenge_cookie(user.id, tenant.id))
        resp = await ac.post("/api/v1/mfa/verify", json={"method": "webauthn", "simulated": True})
    assert resp.status_code == 400, resp.text
    assert "WebAuthn" in resp.json()["detail"]


# ----- enroll guard --------------------------------------------------------


async def test_enroll_already_enabled_409(db_session: AsyncSession) -> None:
    tenant, user, _secret = await _seed_enrolled_user(
        db_session, code="MFAE_409", email="dup@mfae.test", password="rightpw123"
    )
    hdrs = {"X-Test-User": str(user.id), "X-Test-Tenant": str(tenant.id)}
    app = _build_app(db_session)
    async with _client(app) as ac:
        resp = await ac.post("/api/v1/mfa/enroll", headers=hdrs)
    assert resp.status_code == 409, resp.text


# ----- exempt contract -----------------------------------------------------


def test_mfa_exempt_contract() -> None:
    """/api/v1/mfa/verify is exempt (challenge-gated, pre-session); /mfa/enroll is NOT."""
    exempt = TenantContextMiddleware.EXEMPT_PATH_PREFIXES
    assert "/api/v1/mfa/verify" in exempt
    assert not any("/api/v1/mfa/enroll".startswith(p) for p in exempt)
