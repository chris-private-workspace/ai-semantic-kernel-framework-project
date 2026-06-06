"""
File: backend/tests/unit/platform_layer/identity/test_invites_service.py
Purpose: InvitesService lifecycle unit tests (Sprint 57.85 / US-1..US-4).
Category: Tests / Unit (platform_layer.identity — C-12 IAM Block B invites)
Created: 2026-06-06 (Sprint 57.85 Day 2)

Covers the service against the real docker-compose Postgres (db_session, rolled
back at teardown): create (raw token + stored hash + audit), role/duplicate
guards, get_metadata resolution + lazy-expire + typed errors, accept (user +
role grant + single-use + duplicate-email), and the hash_token helper.

The HTTP layer (admin RBAC + exempt guest paths) is covered in
tests/integration/api/test_invites.py.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.models.audit import AuditLog
from infrastructure.db.models.identity import Role, User, UserRole
from infrastructure.db.models.invites import Invite
from platform_layer.identity.invites import (
    InviteAlreadyPendingError,
    InviteConsumedError,
    InviteEmailExistsError,
    InviteExpiredError,
    InviteMetadata,
    InviteNotFoundError,
    InviteRevokedError,
    InviteRoleNotFoundError,
    InvitesService,
    hash_token,
)
from tests.conftest import seed_tenant, seed_user

# asyncio_mode=auto (pyproject) auto-detects async tests — no module pytestmark
# (which would spuriously mark the one sync helper test).


async def _ctx(db: AsyncSession, tenant_id: object) -> None:
    """Set the RLS tenant context on the test session."""
    await db.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(tenant_id)})


async def _seed_role(db: AsyncSession, tenant_id: object, *, code: str = "member") -> Role:
    role = Role(tenant_id=tenant_id, code=code, display_name=code.title())
    db.add(role)
    await db.flush()
    await db.refresh(role)
    return role


async def _setup(db: AsyncSession, *, code: str) -> tuple[object, Role, User]:
    """Seed (tenant, role, inviter) under the tenant's RLS context."""
    tenant = await seed_tenant(db, code=code)
    await _ctx(db, tenant.id)
    role = await _seed_role(db, tenant.id)
    inviter = await seed_user(db, tenant, email=f"admin-{code.lower()}@inv.test")
    return tenant.id, role, inviter


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ----- pure helper --------------------------------------------------------


def test_hash_token_is_sha256_hex() -> None:
    h = hash_token("some-raw-token")
    assert len(h) == 64
    assert h == hash_token("some-raw-token")  # stable
    assert h != hash_token("different")


# ----- create -------------------------------------------------------------


async def test_create_returns_raw_token_and_stores_only_hash(db_session: AsyncSession) -> None:
    """US-1 — create returns the raw token once; only its sha256 is persisted."""
    tid, role, inviter = await _setup(db_session, code="INV_CREATE_1")
    invite, raw = await InvitesService().create(
        db_session, tenant_id=tid, inviter_user_id=inviter.id, email="new@inv.test", role_id=role.id
    )
    assert raw  # non-empty raw token
    assert invite.token_hash == hash_token(raw)
    assert invite.token_hash != raw  # raw is never the stored value
    assert invite.status == "pending"
    assert invite.invited_by == inviter.id
    assert invite.expires_at > _utcnow()
    # an audit row was written for the creation
    audit = (
        (await db_session.execute(select(AuditLog).where(AuditLog.resource_id == str(invite.id))))
        .scalars()
        .all()
    )
    assert any(a.operation == "invite_created" for a in audit)


async def test_create_unknown_role_raises(db_session: AsyncSession) -> None:
    tid, _role, inviter = await _setup(db_session, code="INV_CREATE_ROLE")
    with pytest.raises(InviteRoleNotFoundError):
        await InvitesService().create(
            db_session,
            tenant_id=tid,
            inviter_user_id=inviter.id,
            email="x@inv.test",
            role_id=uuid4(),  # not a role in this tenant
        )


async def test_create_duplicate_pending_raises(db_session: AsyncSession) -> None:
    """US-1 — a second live pending invite for the same email is rejected."""
    tid, role, inviter = await _setup(db_session, code="INV_CREATE_DUP")
    svc = InvitesService()
    await svc.create(
        db_session, tenant_id=tid, inviter_user_id=inviter.id, email="dup@inv.test", role_id=role.id
    )
    with pytest.raises(InviteAlreadyPendingError):
        await svc.create(
            db_session,
            tenant_id=tid,
            inviter_user_id=inviter.id,
            email="dup@inv.test",
            role_id=role.id,
        )


# ----- get_metadata -------------------------------------------------------


async def test_get_metadata_resolves(db_session: AsyncSession) -> None:
    """US-2 — get_metadata returns tenant / inviter / role display names."""
    tid, role, inviter = await _setup(db_session, code="INV_META")
    invite, raw = await InvitesService().create(
        db_session, tenant_id=tid, inviter_user_id=inviter.id, email="m@inv.test", role_id=role.id
    )
    meta = await InvitesService().get_metadata(db_session, raw)
    assert isinstance(meta, InviteMetadata)
    assert meta.tenant == "Tenant INV_META"
    assert meta.role == role.display_name
    assert meta.invited_by  # inviter display name or email
    assert meta.expires_at == invite.expires_at


async def test_get_metadata_invalid_token_raises(db_session: AsyncSession) -> None:
    await _setup(db_session, code="INV_META_BAD")
    with pytest.raises(InviteNotFoundError):
        await InvitesService().get_metadata(db_session, "no-such-token")


async def test_get_metadata_expired_raises(db_session: AsyncSession) -> None:
    """US-4 — a pending invite past expires_at reads as expired."""
    tid, role, inviter = await _setup(db_session, code="INV_META_EXP")
    raw = "expired-token"
    db_session.add(
        Invite(
            tenant_id=tid,
            email="e@inv.test",
            role_id=role.id,
            invited_by=inviter.id,
            token_hash=hash_token(raw),
            status="pending",
            expires_at=_utcnow() - timedelta(hours=1),
        )
    )
    await db_session.flush()
    with pytest.raises(InviteExpiredError):
        await InvitesService().get_metadata(db_session, raw)


async def test_get_metadata_revoked_raises(db_session: AsyncSession) -> None:
    tid, role, inviter = await _setup(db_session, code="INV_META_REV")
    raw = "revoked-token"
    db_session.add(
        Invite(
            tenant_id=tid,
            email="r@inv.test",
            role_id=role.id,
            invited_by=inviter.id,
            token_hash=hash_token(raw),
            status="revoked",
            expires_at=_utcnow() + timedelta(hours=1),
        )
    )
    await db_session.flush()
    with pytest.raises(InviteRevokedError):
        await InvitesService().get_metadata(db_session, raw)


# ----- accept -------------------------------------------------------------


async def test_accept_creates_user_grants_role_and_consumes(db_session: AsyncSession) -> None:
    """US-3 — accept creates the user, grants the role, consumes the invite, audits."""
    tid, role, inviter = await _setup(db_session, code="INV_ACCEPT")
    invite, raw = await InvitesService().create(
        db_session,
        tenant_id=tid,
        inviter_user_id=inviter.id,
        email="join@inv.test",
        role_id=role.id,
    )
    user = await InvitesService().accept(db_session, raw, full_name="Joiner One")

    assert user.email == "join@inv.test"
    assert user.display_name == "Joiner One"
    assert user.status == "active"
    # role granted
    granted = (
        await db_session.execute(
            select(UserRole).where(UserRole.user_id == user.id, UserRole.role_id == role.id)
        )
    ).scalar_one_or_none()
    assert granted is not None
    # invite consumed single-use
    consumed = (await db_session.execute(select(Invite).where(Invite.id == invite.id))).scalar_one()
    assert consumed.status == "accepted"
    assert consumed.accepted_user_id == user.id
    # audit row for the acceptance
    audit = (
        (await db_session.execute(select(AuditLog).where(AuditLog.resource_id == str(invite.id))))
        .scalars()
        .all()
    )
    assert any(a.operation == "invite_accepted" for a in audit)


async def test_accept_single_use(db_session: AsyncSession) -> None:
    """US-4 — a second accept of the same token is rejected (410)."""
    tid, role, inviter = await _setup(db_session, code="INV_SINGLE")
    _invite, raw = await InvitesService().create(
        db_session,
        tenant_id=tid,
        inviter_user_id=inviter.id,
        email="once@inv.test",
        role_id=role.id,
    )
    await InvitesService().accept(db_session, raw, full_name="First")
    with pytest.raises(InviteConsumedError):
        await InvitesService().accept(db_session, raw, full_name="Second")


async def test_accept_duplicate_email_raises(db_session: AsyncSession) -> None:
    """US-3 — accepting for an email that already exists in the tenant → 409."""
    tid, role, inviter = await _setup(db_session, code="INV_DUP_EMAIL")
    await seed_user(db_session, await _tenant_obj(db_session, tid), email="taken@inv.test")
    _invite, raw = await InvitesService().create(
        db_session,
        tenant_id=tid,
        inviter_user_id=inviter.id,
        email="taken@inv.test",
        role_id=role.id,
    )
    with pytest.raises(InviteEmailExistsError):
        await InvitesService().accept(db_session, raw, full_name="Dup")


async def test_accept_stores_password_hash(db_session: AsyncSession) -> None:
    """57.86 — accept(password=…) bcrypt-hashes the password onto the new user."""
    from platform_layer.identity.passwords import verify_password

    tid, role, inviter = await _setup(db_session, code="INV_PW")
    _invite, raw = await InvitesService().create(
        db_session, tenant_id=tid, inviter_user_id=inviter.id, email="pw@inv.test", role_id=role.id
    )
    user = await InvitesService().accept(
        db_session, raw, full_name="Pw User", password="invitepw123"
    )
    assert user.password_hash is not None
    assert await verify_password("invitepw123", user.password_hash) is True


async def test_accept_without_password_leaves_hash_none(db_session: AsyncSession) -> None:
    """57.86 regression — accept() without a password keeps the OIDC-only path."""
    tid, role, inviter = await _setup(db_session, code="INV_NOPW")
    _invite, raw = await InvitesService().create(
        db_session,
        tenant_id=tid,
        inviter_user_id=inviter.id,
        email="nopw@inv.test",
        role_id=role.id,
    )
    user = await InvitesService().accept(db_session, raw, full_name="No Pw")
    assert user.password_hash is None


async def _tenant_obj(db: AsyncSession, tenant_id: object) -> object:
    from infrastructure.db.models.identity import Tenant

    return (await db.execute(select(Tenant).where(Tenant.id == tenant_id))).scalar_one()
