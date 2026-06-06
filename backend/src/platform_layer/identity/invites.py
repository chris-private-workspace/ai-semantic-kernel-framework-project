"""
File: backend/src/platform_layer/identity/invites.py
Purpose: InvitesService — DB-backed member-invite lifecycle (create / view / accept / revoke).
Category: platform_layer.identity (C-12 IAM Block B invites leg)
Scope: Sprint 57.85 / US-1 + US-2 + US-3 + US-4

Description:
    A tenant admin creates an Invite (email + role) and gets a one-time raw token;
    an invitee views the invite metadata by token, then accepts it to become an
    active User with the granted role. Invites are DB-backed (revocable / single-use
    / expiring), reusing the Block-A User/Role/UserRole ORM + WORM audit chain.

    RLS context (mirrors the billing_outbox drainer, Sprint 57.84): the endpoints
    pass a plain `get_db_session` (no middleware tenant context); this service sets
    `app.tenant_id` via set_config per operation —
      - create: the admin's tenant (the invite is for that tenant);
      - view/accept: the all-zeros SENTINEL for the cross-tenant token lookup (the
        invites RLS USING escape), then the invite's own tenant for the user-create.
    Token security: the raw token (`secrets.token_urlsafe`) is returned ONCE by
    create and never stored — only its sha256 hex (`token_hash`) is persisted; the
    lookup is a `token_hash =` equality only (no enumeration).

    Local credentials (Sprint 57.86): accept() now bcrypt-hashes the optional
    `password` onto the new user (via CredentialsService.set_password) so the user
    can sign in via POST /auth/password-login. `password=None` keeps the OIDC-only
    path (the user authenticates via OIDC/dev-login).

Key Components:
    - InviteError + subclasses (carry an HTTP status hint for the router)
    - InvitesService: create / get_by_token / accept / revoke
    - set_/get_/maybe_get_invites_service: singleton (+ reset hook per testing.md)

Created: 2026-06-06 (Sprint 57.85)
Last Modified: 2026-06-06

Modification History:
    - 2026-06-06: Sprint 57.86 — accept() stores optional password (CredentialsService.set_password)
    - 2026-06-06: Initial creation (Sprint 57.85 / US-1..US-4)

Related:
    - infrastructure/db/models/invites.py:Invite — ORM (+ RLS sentinel escape)
    - migrations/versions/0026_invites.py — table + RLS
    - infrastructure/db/models/identity.py — User / Role / UserRole (reused)
    - platform_layer/identity/credentials.py — CredentialsService (password store; 57.86)
    - infrastructure/db/audit_helper.py:append_audit — WORM audit chain
    - platform_layer/billing/billing_outbox.py — set_config tenant-context precedent
    - .claude/rules/multi-tenant-data.md 鐵律 (tenant context per write)
    - c12-iam-block-bc-analysis-20260601.md §5 (invites = minimal slice)
"""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.audit_helper import append_audit
from infrastructure.db.models.identity import Role, Tenant, User, UserRole
from infrastructure.db.models.invites import Invite
from platform_layer.identity.credentials import CredentialsService

# The all-zeros tenant sentinel matches the invites RLS USING escape
# (0026_invites.py): under this context the guest token lookup sees rows across
# tenants. A real request never runs under it (the endpoint sets it explicitly
# only for the token lookup, then switches to the invite's own tenant).
SYSTEM_SENTINEL_TENANT = "00000000-0000-0000-0000-000000000000"

# Default invite lifetime when the caller does not specify one.
DEFAULT_TTL_HOURS = 168  # 7 days
_MAX_TTL_HOURS = 720  # 30 days
_TOKEN_BYTES = 32  # secrets.token_urlsafe(32) → ~43 url-safe chars


# === Typed errors (carry an HTTP status hint for the router) ===
class InviteError(Exception):
    """Base invite error; subclasses set `status_code` + a safe `detail`."""

    status_code: int = 400
    detail: str = "invite error"

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(detail or self.detail)
        if detail:
            self.detail = detail


class InviteNotFoundError(InviteError):
    status_code = 404
    detail = "invite not found"


class InviteExpiredError(InviteError):
    status_code = 410
    detail = "invite has expired"


class InviteConsumedError(InviteError):
    status_code = 410
    detail = "invite has already been accepted"


class InviteRevokedError(InviteError):
    status_code = 410
    detail = "invite has been revoked"


class InviteEmailExistsError(InviteError):
    status_code = 409
    detail = "a user with this email already exists in the tenant"


class InviteAlreadyPendingError(InviteError):
    status_code = 409
    detail = "a pending invite already exists for this email"


class InviteRoleNotFoundError(InviteError):
    status_code = 400
    detail = "role does not exist in this tenant"


@dataclass
class InviteMetadata:
    """Display metadata for an invite (for the guest GET endpoint)."""

    tenant: str
    invited_by: str
    role: str
    expires_at: datetime


# === InvitesService: invite lifecycle ===
# Why: IAM Block B needs an onboarding path (admin invites → member accepts) that
# is revocable / single-use / expiring. DB-backed (not a stateless JWT) so the
# state machine is auditable. Reuses Block-A User/Role/UserRole + WORM audit.
class InvitesService:
    """Invite lifecycle; each method manages its own RLS tenant context."""

    async def create(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        inviter_user_id: UUID,
        email: str,
        role_id: UUID,
        ttl_hours: int | None = None,
    ) -> tuple[Invite, str]:
        """Create a pending invite for (email, role); return (invite, raw_token).

        The raw token is shown ONCE here and never stored (only its sha256 hex).
        Raises InviteRoleNotFoundError (role not in tenant) / InviteAlreadyPendingError
        (a live pending invite already exists for the email).
        """
        await _set_tenant(db, str(tenant_id))

        role = (
            await db.execute(select(Role).where(Role.id == role_id, Role.tenant_id == tenant_id))
        ).scalar_one_or_none()
        if role is None:
            raise InviteRoleNotFoundError()

        now = _utcnow()
        # Lazy-expire stale pending invites for this email so the partial-unique
        # index (status='pending') does not block a fresh invite + they don't linger.
        await db.execute(
            update(Invite)
            .where(
                Invite.tenant_id == tenant_id,
                Invite.email == email,
                Invite.status == "pending",
                Invite.expires_at <= now,
            )
            .values(status="expired")
        )
        live_pending = (
            await db.execute(
                select(Invite).where(
                    Invite.tenant_id == tenant_id,
                    Invite.email == email,
                    Invite.status == "pending",
                )
            )
        ).first()
        if live_pending is not None:
            raise InviteAlreadyPendingError()

        ttl = _clamp_ttl(ttl_hours)
        raw_token = secrets.token_urlsafe(_TOKEN_BYTES)
        invite = Invite(
            tenant_id=tenant_id,
            email=email,
            role_id=role_id,
            invited_by=inviter_user_id,
            token_hash=hash_token(raw_token),
            status="pending",
            expires_at=now + timedelta(hours=ttl),
        )
        db.add(invite)
        await db.flush()

        await append_audit(
            db,
            tenant_id=tenant_id,
            operation="invite_created",
            resource_type="invite",
            resource_id=str(invite.id),
            operation_data={"email": email, "role_id": str(role_id)},
            user_id=inviter_user_id,
            operation_result="success",
        )
        return invite, raw_token

    async def get_metadata(self, db: AsyncSession, raw_token: str) -> InviteMetadata:
        """Resolve a live invite by its raw token and return display metadata.

        Sentinel-scoped token lookup, then switches to the invite's own tenant to
        read the tenant / inviter / role names (their tables have no sentinel
        escape). Read-only. Raises InviteNotFoundError (404) / InviteExpiredError /
        InviteConsumedError / InviteRevokedError (410).
        """
        await _set_tenant(db, SYSTEM_SENTINEL_TENANT)
        invite = await self._lookup(db, raw_token)
        self._guard_pending(invite)

        # Switch to the invite's tenant to read related names (users/roles are
        # tenant-scoped with no sentinel escape; tenants is the RLS-free root).
        await _set_tenant(db, str(invite.tenant_id))
        tenant = (
            await db.execute(select(Tenant).where(Tenant.id == invite.tenant_id))
        ).scalar_one_or_none()
        inviter = (
            await db.execute(select(User).where(User.id == invite.invited_by))
        ).scalar_one_or_none()
        role = (
            await db.execute(select(Role).where(Role.id == invite.role_id))
        ).scalar_one_or_none()

        return InviteMetadata(
            tenant=tenant.display_name if tenant is not None else "",
            invited_by=((inviter.display_name or inviter.email) if inviter is not None else ""),
            role=role.display_name if role is not None else "",
            expires_at=invite.expires_at,
        )

    async def accept(
        self,
        db: AsyncSession,
        raw_token: str,
        *,
        full_name: str,
        password: str | None = None,
    ) -> User:
        """Accept an invite: create the User + grant the role + consume the invite.

        Single-use (a rowcount-guarded UPDATE loses the race → 410). The created
        user is scoped to the invite's tenant. If `password` is provided it is
        bcrypt-hashed onto the new user (Sprint 57.86) so they can sign in via
        POST /auth/password-login; `password=None` keeps the OIDC-only path.
        Raises typed errors (404 / 410 / 409).
        """
        await _set_tenant(db, SYSTEM_SENTINEL_TENANT)
        invite = await self._lookup(db, raw_token)
        self._guard_pending(invite)

        invite_id = invite.id
        tenant_id = invite.tenant_id
        role_id = invite.role_id
        invited_by = invite.invited_by
        email = invite.email

        # Switch to the invite's own tenant for the user-create writes (the
        # lookup ran under the sentinel; users/audit keep their own tenant scope).
        await _set_tenant(db, str(tenant_id))

        existing = (
            await db.execute(select(User).where(User.tenant_id == tenant_id, User.email == email))
        ).scalar_one_or_none()
        if existing is not None:
            raise InviteEmailExistsError()

        user = User(
            tenant_id=tenant_id,
            email=email,
            display_name=full_name,
            status="active",
        )
        db.add(user)
        await db.flush()  # obtain user.id without committing

        if password is not None:
            # bcrypt-hash the local password onto the new user (Sprint 57.86); the
            # mutation flushes with the rest of this txn below.
            await CredentialsService().set_password(user=user, raw=password)

        db.add(UserRole(user_id=user.id, role_id=role_id, granted_by=invited_by))

        # Single-use consume: only the txn that flips pending → accepted wins
        # (RETURNING → no row back = lost the race).
        marked = (
            await db.execute(
                update(Invite)
                .where(Invite.id == invite_id, Invite.status == "pending")
                .values(status="accepted", accepted_at=_utcnow(), accepted_user_id=user.id)
                .returning(Invite.id)
            )
        ).scalar_one_or_none()
        if marked is None:  # another accept consumed it first
            raise InviteConsumedError()

        await append_audit(
            db,
            tenant_id=tenant_id,
            operation="invite_accepted",
            resource_type="invite",
            resource_id=str(invite_id),
            operation_data={"email": email, "role_id": str(role_id), "user_id": str(user.id)},
            user_id=user.id,
            operation_result="success",
        )
        await db.flush()
        return user

    async def revoke(self, db: AsyncSession, *, tenant_id: UUID, invite_id: UUID) -> None:
        """Revoke a pending invite (admin). Idempotent rowcount-guarded.

        Raises InviteNotFoundError if no pending invite with that id in the tenant.
        """
        await _set_tenant(db, str(tenant_id))
        revoked = (
            await db.execute(
                update(Invite)
                .where(
                    Invite.id == invite_id,
                    Invite.tenant_id == tenant_id,
                    Invite.status == "pending",
                )
                .values(status="revoked")
                .returning(Invite.id)
            )
        ).scalar_one_or_none()
        if revoked is None:
            raise InviteNotFoundError("no pending invite with that id")

    # --- internals ---------------------------------------------------------
    async def _lookup(self, db: AsyncSession, raw_token: str) -> Invite:
        invite = (
            await db.execute(select(Invite).where(Invite.token_hash == hash_token(raw_token)))
        ).scalar_one_or_none()
        if invite is None:
            raise InviteNotFoundError()
        return invite

    @staticmethod
    def _guard_pending(invite: Invite) -> None:
        """Raise the matching typed error unless the invite is live-pending."""
        if invite.status == "accepted":
            raise InviteConsumedError()
        if invite.status == "revoked":
            raise InviteRevokedError()
        if invite.status == "expired" or invite.expires_at <= _utcnow():
            raise InviteExpiredError()


def hash_token(raw_token: str) -> str:
    """sha256 hex (64 chars) of the raw token — the only form persisted."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def _clamp_ttl(ttl_hours: int | None) -> int:
    if ttl_hours is None:
        return DEFAULT_TTL_HOURS
    return max(1, min(ttl_hours, _MAX_TTL_HOURS))


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def _set_tenant(db: AsyncSession, tenant_id: str) -> None:
    """SET LOCAL app.tenant_id for the current transaction (RLS context).

    set_config(...) is the bind-param-compatible function form of SET LOCAL
    (asyncpg rejects params on the SET utility statement); is_local=true →
    txn-scoped. Mirrors middleware/tenant_context.py + the billing_outbox drainer.
    """
    await db.execute(text("SELECT set_config('app.tenant_id', :tid, true)"), {"tid": tenant_id})


# Module-level singleton (stateless; db passed per call). Reset hook per
# testing.md §Module-level Singleton Reset Pattern.
_service: InvitesService | None = None


def get_invites_service() -> InvitesService:
    """FastAPI Depends accessor (strict — raises if uninitialised)."""
    if _service is None:
        raise RuntimeError(
            "InvitesService not initialised; call set_invites_service() at app "
            "startup or in a test fixture"
        )
    return _service


def maybe_get_invites_service() -> InvitesService | None:
    """Lenient accessor — returns None if uninitialised."""
    return _service


def set_invites_service(service: InvitesService | None) -> None:
    """Install singleton (app startup or tests fixture)."""
    global _service
    _service = service


__all__ = [
    "InvitesService",
    "InviteMetadata",
    "InviteError",
    "InviteNotFoundError",
    "InviteExpiredError",
    "InviteConsumedError",
    "InviteRevokedError",
    "InviteEmailExistsError",
    "InviteAlreadyPendingError",
    "InviteRoleNotFoundError",
    "SYSTEM_SENTINEL_TENANT",
    "DEFAULT_TTL_HOURS",
    "hash_token",
    "get_invites_service",
    "maybe_get_invites_service",
    "set_invites_service",
]
