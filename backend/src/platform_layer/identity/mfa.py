"""
File: backend/src/platform_layer/identity/mfa.py
Purpose: TOTPService — enroll / confirm / verify a user's TOTP second factor (C-12 IAM Block C MFA).
Category: platform_layer.identity (MFA leg)
Scope: Sprint 57.112 / US-1

Description:
    RFC 6238 TOTP second factor for the local-password login path. Three operations,
    all stateless + self-managing their RLS tenant context (like CredentialsService):
      - enroll(db, user_id, tenant_id, issuer_name): generate a base32 secret, store
        it on the user (mfa_enabled stays FALSE), and return the otpauth:// URI the
        authenticator app scans. Re-enroll is allowed only while not yet enabled.
      - confirm(db, user_id, tenant_id, code): verify the user's first code against the
        stored secret, then flip mfa_enabled=true (the enroll → activation step).
      - verify(db, user_id, tenant_id, code): validate a code at login. EVERY failure
        (no secret / not enabled / wrong code) raises the SAME generic InvalidTOTPError
        so the login path leaks nothing (the user is already identified by the signed
        challenge token, so this is defense-in-depth, not the primary enumeration gate).

    The secret is stored PLAINTEXT in users.totp_secret: a TOTP secret is a SHARED
    secret that must be readable to recompute codes (unlike a password it cannot be
    hashed). At-rest encryption is a tracked deferred AD (AD-MFA-Secret-At-Rest-
    Encryption) — no encryption utility is wired in the codebase today.

    Audit is done at the ENDPOINT layer (api/v1/mfa.py), mirroring password-login —
    this keeps TOTPService a pure, audit-free, unit-testable service like
    CredentialsService.

Key Components:
    - MFAError (base, 400) → InvalidTOTPError (401, generic) / MFANotEnrolledError (400)
      / MFAAlreadyEnabledError (409) — carry an HTTP status hint for the router
    - EnrollResult: frozen dataclass (secret, otpauth_uri)
    - TOTPService: enroll / confirm / verify
    - set_/get_/maybe_get_mfa_service: singleton (+ reset hook per testing.md)

Created: 2026-06-13 (Sprint 57.112)
Last Modified: 2026-06-13

Modification History (newest-first):
    - 2026-06-13: Initial creation (Sprint 57.112 / US-1) — TOTP enroll/confirm/verify

Related:
    - platform_layer/identity/credentials.py — CredentialsService (the mirrored pattern)
    - api/v1/mfa.py — POST /api/v1/mfa/{enroll,enroll/confirm,verify} (consumers + audit)
    - api/v1/auth.py — password-login MFA-gate (issues the mfa_pending challenge)
    - infrastructure/db/models/identity.py — User.{totp_secret,mfa_enabled}
    - .claude/rules/multi-tenant-data.md 鐵律 (tenant context per query)
    - sprint-57-112-plan.md §3.1
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

import pyotp
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.models.identity import User

# TOTP skew tolerance: accept the code from the previous + next 30s window so a
# small client/server clock drift does not reject a valid code (RFC 6238 standard).
_VALID_WINDOW = 1


# === Typed errors (carry an HTTP status hint for the router) ===
class MFAError(Exception):
    """Base MFA error; subclasses set `status_code` + a safe `detail`."""

    status_code: int = 400
    detail: str = "mfa error"

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(detail or self.detail)
        if detail:
            self.detail = detail


class InvalidTOTPError(MFAError):
    # 401 + a SINGLE generic message for every login-verify failure (no leak of
    # "not enrolled" vs "wrong code").
    status_code = 401
    detail = "Invalid verification code"


class MFANotEnrolledError(MFAError):
    # 400 — confirm() called before enroll() set a secret.
    status_code = 400
    detail = "MFA is not enrolled"


class MFAAlreadyEnabledError(MFAError):
    # 409 — enroll() called when MFA is already active (re-enroll must reset first).
    status_code = 409
    detail = "MFA is already enabled"


@dataclass(frozen=True)
class EnrollResult:
    """The secret + provisioning URI returned by enroll().

    secret: the base32 TOTP shared secret (the user keys it into their authenticator,
        or scans the QR rendered from otpauth_uri).
    otpauth_uri: the otpauth://totp/... URI an authenticator app scans.
    """

    secret: str
    otpauth_uri: str


# === TOTPService: TOTP enroll + confirm + verify ===
# Why: C-12 IAM Block C needs an app-level second factor on the local-password login
# path. DB-backed on users (two columns: totp_secret + mfa_enabled — lean monolithic
# identity, no separate MFA table). Stateless; db passed per call; self-manages RLS.
# Mirrors CredentialsService (generic-error verify + module-level _set_tenant +
# singleton). pyotp implements RFC 6238 (stdlib hmac, no native deps).
class TOTPService:
    """TOTP lifecycle; each method manages its own RLS tenant context."""

    async def enroll(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        tenant_id: UUID,
        issuer_name: str,
    ) -> EnrollResult:
        """Generate + store a base32 secret (mfa_enabled stays false); return the URI.

        Raises MFAAlreadyEnabledError if MFA is already active (re-enroll would
        silently rotate the secret of a working second factor).
        """
        user = await self._load_user(db, user_id=user_id, tenant_id=tenant_id)
        if user is None:
            raise MFAError("user not found")
        if user.mfa_enabled:
            raise MFAAlreadyEnabledError()

        secret = pyotp.random_base32()
        user.totp_secret = secret
        otpauth_uri = pyotp.TOTP(secret).provisioning_uri(name=user.email, issuer_name=issuer_name)
        return EnrollResult(secret=secret, otpauth_uri=otpauth_uri)

    async def confirm(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        tenant_id: UUID,
        code: str,
    ) -> None:
        """Verify the first code against the stored secret, then flip mfa_enabled=true.

        Raises MFANotEnrolledError if enroll() has not run, InvalidTOTPError on a
        wrong code.
        """
        user = await self._load_user(db, user_id=user_id, tenant_id=tenant_id)
        if user is None or user.totp_secret is None:
            raise MFANotEnrolledError()
        if not pyotp.TOTP(user.totp_secret).verify(code.strip(), valid_window=_VALID_WINDOW):
            raise InvalidTOTPError()
        user.mfa_enabled = True

    async def verify(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        tenant_id: UUID,
        code: str,
    ) -> User:
        """Validate a login code → the User, or raise InvalidTOTPError.

        EVERY miss (user gone / not enabled / no secret / wrong code) raises the
        SAME generic InvalidTOTPError — the login path leaks nothing.
        """
        user = await self._load_user(db, user_id=user_id, tenant_id=tenant_id)
        if user is None or not user.mfa_enabled or user.totp_secret is None:
            raise InvalidTOTPError()
        if not pyotp.TOTP(user.totp_secret).verify(code.strip(), valid_window=_VALID_WINDOW):
            raise InvalidTOTPError()
        return user

    async def _load_user(self, db: AsyncSession, *, user_id: UUID, tenant_id: UUID) -> User | None:
        """Set the RLS tenant context, then load the user scoped by (id, tenant_id)."""
        await _set_tenant(db, str(tenant_id))
        return (
            await db.execute(select(User).where(User.id == user_id, User.tenant_id == tenant_id))
        ).scalar_one_or_none()


async def _set_tenant(db: AsyncSession, tenant_id: str) -> None:
    """SET LOCAL app.tenant_id for the current txn (RLS context).

    set_config(...) is the bind-param-compatible form of SET LOCAL (asyncpg
    rejects params on the SET utility); is_local=true → txn-scoped. Mirrors
    credentials.py / invites.py.
    """
    await db.execute(text("SELECT set_config('app.tenant_id', :tid, true)"), {"tid": tenant_id})


# Module-level singleton (stateless; db passed per call). Reset hook per
# testing.md §Module-level Singleton Reset Pattern.
_service: TOTPService | None = None


def get_mfa_service() -> TOTPService:
    """FastAPI Depends accessor (strict — raises if uninitialised)."""
    if _service is None:
        raise RuntimeError(
            "TOTPService not initialised; call set_mfa_service() at app startup "
            "or in a test fixture"
        )
    return _service


def maybe_get_mfa_service() -> TOTPService | None:
    """Lenient accessor — returns None if uninitialised."""
    return _service


def set_mfa_service(service: TOTPService | None) -> None:
    """Install singleton (app startup or tests fixture)."""
    global _service
    _service = service


__all__ = [
    "EnrollResult",
    "InvalidTOTPError",
    "MFAAlreadyEnabledError",
    "MFAError",
    "MFANotEnrolledError",
    "TOTPService",
    "get_mfa_service",
    "maybe_get_mfa_service",
    "set_mfa_service",
]
