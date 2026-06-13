"""
File: backend/tests/unit/platform_layer/identity/test_mfa_service.py
Purpose: TOTPService enroll/confirm/verify unit tests (Sprint 57.112 / US-1).
Category: Tests / Unit (platform_layer.identity — C-12 IAM Block C MFA)
Created: 2026-06-13 (Sprint 57.112 Day 1)

Covers the service against the real docker-compose Postgres (db_session, rolled
back at teardown): enroll returns a secret + otpauth URI and leaves mfa_enabled
false; confirm flips the flag on a valid code and raises on a bad/absent secret;
verify accepts a valid code and raises the SAME generic InvalidTOTPError on EVERY
login miss (wrong code / not enabled / no secret) — no leak. valid_window absorbs
±30s clock skew. Cross-tenant verify cannot read another tenant's secret.

The HTTP layer (challenge cookie / full-session issuance / EXEMPT verify) is
covered in tests/integration/api/test_mfa_endpoints.py.
"""

from __future__ import annotations

import time

import pyotp
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from platform_layer.identity.mfa import (
    EnrollResult,
    InvalidTOTPError,
    MFAAlreadyEnabledError,
    MFANotEnrolledError,
    TOTPService,
)
from tests.conftest import seed_tenant, seed_user

# asyncio_mode=auto (pyproject) auto-detects async tests.

_ISSUER = "IPA Platform"


async def _ctx(db: AsyncSession, tenant_id: object) -> None:
    await db.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(tenant_id)})


def _wrong_code(secret: str) -> str:
    """A 6-digit code guaranteed NOT to match any of the 3 valid_window windows."""
    totp = pyotp.TOTP(secret)
    now = time.time()
    valid = {totp.at(now - 30), totp.now(), totp.at(now + 30)}
    return next(f"{n:06d}" for n in range(1000000) if f"{n:06d}" not in valid)


async def _seed_user(db: AsyncSession, *, code: str, email: str) -> tuple[object, object]:
    tenant = await seed_tenant(db, code=code)
    await _ctx(db, tenant.id)
    user = await seed_user(db, tenant, email=email)
    await db.flush()
    return tenant, user


# ----- enroll -------------------------------------------------------------


async def test_enroll_returns_secret_uri_leaves_disabled(db_session: AsyncSession) -> None:
    """US-1 — enroll stores a base32 secret + otpauth URI; mfa_enabled stays false."""
    tenant, user = await _seed_user(db_session, code="MFA_ENROLL", email="e@mfa.test")
    result = await TOTPService().enroll(
        db_session, user_id=user.id, tenant_id=tenant.id, issuer_name=_ISSUER
    )
    assert isinstance(result, EnrollResult)
    assert result.secret and len(result.secret) <= 64
    assert result.otpauth_uri.startswith("otpauth://totp/")
    assert user.totp_secret == result.secret
    assert user.mfa_enabled is False


async def test_enroll_when_already_enabled_raises(db_session: AsyncSession) -> None:
    tenant, user = await _seed_user(db_session, code="MFA_REENROLL", email="re@mfa.test")
    user.mfa_enabled = True
    user.totp_secret = pyotp.random_base32()
    await db_session.flush()
    with pytest.raises(MFAAlreadyEnabledError):
        await TOTPService().enroll(
            db_session, user_id=user.id, tenant_id=tenant.id, issuer_name=_ISSUER
        )


# ----- confirm ------------------------------------------------------------


async def test_confirm_valid_code_enables(db_session: AsyncSession) -> None:
    """US-1 — a valid first code flips mfa_enabled true."""
    tenant, user = await _seed_user(db_session, code="MFA_CONFIRM", email="c@mfa.test")
    result = await TOTPService().enroll(
        db_session, user_id=user.id, tenant_id=tenant.id, issuer_name=_ISSUER
    )
    code = pyotp.TOTP(result.secret).now()
    await TOTPService().confirm(db_session, user_id=user.id, tenant_id=tenant.id, code=code)
    assert user.mfa_enabled is True


async def test_confirm_wrong_code_raises(db_session: AsyncSession) -> None:
    tenant, user = await _seed_user(db_session, code="MFA_CONFIRM_BAD", email="cb@mfa.test")
    result = await TOTPService().enroll(
        db_session, user_id=user.id, tenant_id=tenant.id, issuer_name=_ISSUER
    )
    with pytest.raises(InvalidTOTPError):
        await TOTPService().confirm(
            db_session, user_id=user.id, tenant_id=tenant.id, code=_wrong_code(result.secret)
        )
    assert user.mfa_enabled is False


async def test_confirm_without_enroll_raises(db_session: AsyncSession) -> None:
    """confirm before enroll (no secret) → MFANotEnrolledError."""
    tenant, user = await _seed_user(db_session, code="MFA_NOENROLL", email="ne@mfa.test")
    with pytest.raises(MFANotEnrolledError):
        await TOTPService().confirm(db_session, user_id=user.id, tenant_id=tenant.id, code="123456")


# ----- verify -------------------------------------------------------------


async def _enrolled_enabled_user(
    db: AsyncSession, *, code: str, email: str
) -> tuple[object, object, str]:
    tenant, user = await _seed_user(db, code=code, email=email)
    result = await TOTPService().enroll(
        db, user_id=user.id, tenant_id=tenant.id, issuer_name=_ISSUER
    )
    await TOTPService().confirm(
        db, user_id=user.id, tenant_id=tenant.id, code=pyotp.TOTP(result.secret).now()
    )
    return tenant, user, result.secret


async def test_verify_valid_code_returns_user(db_session: AsyncSession) -> None:
    """US-1 — a valid login code returns the user."""
    tenant, user, secret = await _enrolled_enabled_user(
        db_session, code="MFA_VERIFY", email="v@mfa.test"
    )
    got = await TOTPService().verify(
        db_session, user_id=user.id, tenant_id=tenant.id, code=pyotp.TOTP(secret).now()
    )
    assert got.id == user.id


async def test_verify_wrong_code_raises(db_session: AsyncSession) -> None:
    tenant, user, secret = await _enrolled_enabled_user(
        db_session, code="MFA_VERIFY_BAD", email="vb@mfa.test"
    )
    with pytest.raises(InvalidTOTPError):
        await TOTPService().verify(
            db_session, user_id=user.id, tenant_id=tenant.id, code=_wrong_code(secret)
        )


async def test_verify_not_enabled_raises(db_session: AsyncSession) -> None:
    """US-3 — enrolled-but-not-confirmed (mfa_enabled false) → generic 401 (no leak)."""
    tenant, user = await _seed_user(db_session, code="MFA_VERIFY_OFF", email="vo@mfa.test")
    result = await TOTPService().enroll(
        db_session, user_id=user.id, tenant_id=tenant.id, issuer_name=_ISSUER
    )
    with pytest.raises(InvalidTOTPError):
        await TOTPService().verify(
            db_session, user_id=user.id, tenant_id=tenant.id, code=pyotp.TOTP(result.secret).now()
        )


async def test_verify_no_secret_raises(db_session: AsyncSession) -> None:
    """A user who never enrolled → generic 401 at login (no leak)."""
    tenant, user = await _seed_user(db_session, code="MFA_VERIFY_NONE", email="vn@mfa.test")
    with pytest.raises(InvalidTOTPError):
        await TOTPService().verify(db_session, user_id=user.id, tenant_id=tenant.id, code="123456")


# ----- skew + isolation ---------------------------------------------------


async def test_verify_accepts_previous_window_code(db_session: AsyncSession) -> None:
    """valid_window=1 absorbs ±30s skew — a code from the previous window verifies."""
    tenant, user, secret = await _enrolled_enabled_user(
        db_session, code="MFA_SKEW", email="sk@mfa.test"
    )
    prev_code = pyotp.TOTP(secret).at(time.time() - 30)
    got = await TOTPService().verify(
        db_session, user_id=user.id, tenant_id=tenant.id, code=prev_code
    )
    assert got.id == user.id


async def test_verify_cross_tenant_cannot_read_secret(db_session: AsyncSession) -> None:
    """A tenant-B context cannot verify a tenant-A user's TOTP (id+tenant scope + RLS)."""
    tenant_a, user_a, secret = await _enrolled_enabled_user(
        db_session, code="MFA_ISO_A", email="a@iso.test"
    )
    tenant_b = await seed_tenant(db_session, code="MFA_ISO_B")
    await db_session.flush()
    # Same user_id but tenant_b scope → (id, tenant_id) misses → generic 401.
    with pytest.raises(InvalidTOTPError):
        await TOTPService().verify(
            db_session, user_id=user_a.id, tenant_id=tenant_b.id, code=pyotp.TOTP(secret).now()
        )
