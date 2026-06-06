"""
File: backend/src/platform_layer/identity/credentials.py
Purpose: CredentialsService — set/verify a user's local password (C-12 IAM Block B/C).
Category: platform_layer.identity (local-credentials leg)
Scope: Sprint 57.86 / US-1 + US-2 + US-3

Description:
    Local-password authentication for invited users (the OIDC/dev-login path is
    untouched). Two operations:
      - set_password(user, raw): bcrypt-hash + store on the User (invite-accept).
      - authenticate(db, tenant_code, email, raw): resolve the tenant by `code`
        (the RLS-free root), the user by (tenant_id, email) under the tenant's RLS
        context, then bcrypt-verify. Returns the User on success.

    Anti-enumeration (US-3): EVERY failure mode — unknown tenant_code, unknown
    email, a user with no local password (SSO-only), or a wrong password — raises
    the SAME InvalidCredentialsError (the router maps it to one generic 401). On the
    user-absent / no-hash path it still runs one bcrypt verify against passwords.
    DUMMY_HASH so response latency does not distinguish "no such user" from "wrong
    password" (timing-based enumeration guard).

    No rate-limit / lockout here (an explicit 57.86 carryover —
    AD-Auth-PasswordLogin-Lockout-Phase58); bcrypt cost=12 raises the per-guess cost.

Key Components:
    - CredentialsError + InvalidCredentialsError (generic 401 hint for the router)
    - CredentialsService: set_password / authenticate
    - set_/get_/maybe_get_credentials_service: singleton (+ reset hook per testing.md)

Created: 2026-06-06 (Sprint 57.86)
Last Modified: 2026-06-06

Modification History (newest-first):
    - 2026-06-06: Initial creation (Sprint 57.86 / US-1..US-3)

Related:
    - platform_layer/identity/passwords.py — hash_password / verify_password / DUMMY_HASH
    - platform_layer/identity/invites.py — InvitesService.accept (set_password consumer)
    - api/v1/auth.py — POST /password-login (authenticate consumer)
    - infrastructure/db/models/identity.py — Tenant / User (reused)
    - .claude/rules/multi-tenant-data.md 鐵律 (tenant context per query)
    - sprint-57-86-plan.md §3.2
"""

from __future__ import annotations

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.models.identity import Tenant, User
from platform_layer.identity.passwords import DUMMY_HASH, hash_password, verify_password


# === Typed errors (carry an HTTP status hint for the router) ===
class CredentialsError(Exception):
    """Base credentials error; subclasses set `status_code` + a safe `detail`."""

    status_code: int = 400
    detail: str = "credentials error"

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(detail or self.detail)
        if detail:
            self.detail = detail


class InvalidCredentialsError(CredentialsError):
    # 401 + a SINGLE generic message for every failure mode (no enumeration).
    status_code = 401
    detail = "Invalid credentials"


# === CredentialsService: local-password set + verify ===
# Why: IAM Block B/C needs an invited user to set a local password (invite-accept)
# and sign back in without SSO (POST /auth/password-login). DB-backed on users
# (no separate credential table — lean monolithic identity). Stateless; db passed
# per call. The generic-error + constant-time-miss design is the anti-enumeration
# gate (see module docstring / 04-anti-patterns.md is N/A — this is a security
# invariant, tested in test_credentials_service.py + test_password_login.py).
class CredentialsService:
    """Local-password lifecycle; authenticate manages its own RLS tenant context."""

    async def set_password(self, *, user: User, raw: str) -> None:
        """bcrypt-hash ``raw`` onto ``user.password_hash`` (caller's txn flushes)."""
        user.password_hash = await hash_password(raw)

    async def authenticate(
        self,
        db: AsyncSession,
        *,
        tenant_code: str,
        email: str,
        raw: str,
    ) -> User:
        """Authenticate (tenant_code, email, password) → the User, or raise.

        EVERY miss (unknown tenant / unknown email / no local password / wrong
        password) raises InvalidCredentialsError; the absent paths still run one
        bcrypt verify (DUMMY_HASH) to flatten timing. Anti-enumeration (US-3).
        """
        tenant = (
            await db.execute(select(Tenant).where(Tenant.code == tenant_code))
        ).scalar_one_or_none()
        if tenant is None:
            await verify_password(raw, DUMMY_HASH)  # constant-time miss
            raise InvalidCredentialsError()

        await _set_tenant(db, str(tenant.id))
        user = (
            await db.execute(select(User).where(User.tenant_id == tenant.id, User.email == email))
        ).scalar_one_or_none()
        if user is None or user.password_hash is None:
            await verify_password(raw, DUMMY_HASH)  # constant-time miss
            raise InvalidCredentialsError()

        if not await verify_password(raw, user.password_hash):
            raise InvalidCredentialsError()
        return user


async def _set_tenant(db: AsyncSession, tenant_id: str) -> None:
    """SET LOCAL app.tenant_id for the current txn (RLS context).

    set_config(...) is the bind-param-compatible form of SET LOCAL (asyncpg
    rejects params on the SET utility); is_local=true → txn-scoped. Mirrors
    invites.py / the billing_outbox drainer.
    """
    await db.execute(text("SELECT set_config('app.tenant_id', :tid, true)"), {"tid": tenant_id})


# Module-level singleton (stateless; db passed per call). Reset hook per
# testing.md §Module-level Singleton Reset Pattern.
_service: CredentialsService | None = None


def get_credentials_service() -> CredentialsService:
    """FastAPI Depends accessor (strict — raises if uninitialised)."""
    if _service is None:
        raise RuntimeError(
            "CredentialsService not initialised; call set_credentials_service() at "
            "app startup or in a test fixture"
        )
    return _service


def maybe_get_credentials_service() -> CredentialsService | None:
    """Lenient accessor — returns None if uninitialised."""
    return _service


def set_credentials_service(service: CredentialsService | None) -> None:
    """Install singleton (app startup or tests fixture)."""
    global _service
    _service = service


__all__ = [
    "CredentialsService",
    "CredentialsError",
    "InvalidCredentialsError",
    "get_credentials_service",
    "maybe_get_credentials_service",
    "set_credentials_service",
]
