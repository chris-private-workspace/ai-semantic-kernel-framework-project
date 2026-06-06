"""
File: backend/tests/unit/platform_layer/identity/test_credentials_service.py
Purpose: CredentialsService set/authenticate unit tests (Sprint 57.86 / US-1..US-3).
Category: Tests / Unit (platform_layer.identity — C-12 IAM credentials)
Created: 2026-06-06 (Sprint 57.86 Day 2)

Covers the service against the real docker-compose Postgres (db_session, rolled
back at teardown): set_password persists a verifiable bcrypt hash; authenticate
success returns the user; and EVERY miss mode (wrong password / unknown email /
no-password SSO-only user / unknown tenant_code) raises the SAME
InvalidCredentialsError — the anti-enumeration invariant (US-3).

The HTTP layer (cookie/JWT/generic-401 + 2-tenant isolation) is covered in
tests/integration/api/test_password_login.py.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from platform_layer.identity.credentials import CredentialsService, InvalidCredentialsError
from platform_layer.identity.passwords import verify_password
from tests.conftest import seed_tenant, seed_user

# asyncio_mode=auto (pyproject) auto-detects async tests.


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


# ----- set_password -------------------------------------------------------


async def test_set_password_persists_verifiable_hash(db_session: AsyncSession) -> None:
    """US-1 — set_password stores a bcrypt hash that verifies the raw password."""
    tenant = await seed_tenant(db_session, code="CRED_SET")
    await _ctx(db_session, tenant.id)
    user = await seed_user(db_session, tenant, email="set@cred.test")
    await CredentialsService().set_password(user=user, raw="hunter2pw")
    await db_session.flush()
    assert user.password_hash is not None
    assert user.password_hash.startswith("$2b$12$")
    assert await verify_password("hunter2pw", user.password_hash) is True


# ----- authenticate -------------------------------------------------------


async def test_authenticate_success_returns_user(db_session: AsyncSession) -> None:
    """US-2 — correct tenant_code + email + password resolves the user."""
    await _seed_user_with_password(
        db_session, code="CRED_OK", email="ok@cred.test", password="rightpw123"
    )
    user = await CredentialsService().authenticate(
        db_session, tenant_code="CRED_OK", email="ok@cred.test", raw="rightpw123"
    )
    assert user.email == "ok@cred.test"


async def test_authenticate_wrong_password_raises(db_session: AsyncSession) -> None:
    await _seed_user_with_password(
        db_session, code="CRED_WRONG", email="w@cred.test", password="rightpw123"
    )
    with pytest.raises(InvalidCredentialsError):
        await CredentialsService().authenticate(
            db_session, tenant_code="CRED_WRONG", email="w@cred.test", raw="WRONGpw"
        )


async def test_authenticate_unknown_email_raises(db_session: AsyncSession) -> None:
    await _seed_user_with_password(
        db_session, code="CRED_NOEMAIL", email="real@cred.test", password="rightpw123"
    )
    with pytest.raises(InvalidCredentialsError):
        await CredentialsService().authenticate(
            db_session, tenant_code="CRED_NOEMAIL", email="ghost@cred.test", raw="rightpw123"
        )


async def test_authenticate_no_password_user_raises(db_session: AsyncSession) -> None:
    """US-3 — an SSO-only user (no password_hash) cannot password-login."""
    tenant = await seed_tenant(db_session, code="CRED_SSO")
    await _ctx(db_session, tenant.id)
    await seed_user(db_session, tenant, email="sso@cred.test")  # no set_password
    await db_session.flush()
    with pytest.raises(InvalidCredentialsError):
        await CredentialsService().authenticate(
            db_session, tenant_code="CRED_SSO", email="sso@cred.test", raw="anything"
        )


async def test_authenticate_unknown_tenant_raises(db_session: AsyncSession) -> None:
    with pytest.raises(InvalidCredentialsError):
        await CredentialsService().authenticate(
            db_session, tenant_code="NO_SUCH_TENANT", email="x@cred.test", raw="anything"
        )
