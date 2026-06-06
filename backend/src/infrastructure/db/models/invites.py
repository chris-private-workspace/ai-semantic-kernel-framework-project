"""
File: backend/src/infrastructure/db/models/invites.py
Purpose: Invite ORM — DB-backed, single-use, expiring member-invite tokens (IAM Block B).
Category: Infrastructure / ORM (platform_layer.identity — C-12 IAM Block B invites leg)
Scope: Sprint 57.85 / US-1 + US-4

Description:
    A tenant admin creates an Invite for an (email, role); the invitee accepts it
    to become an active User with the granted role. The invite is DB-backed (not a
    stateless JWT) so it is revocable, single-use, expiring, and listable.

    Token security: the raw token (`secrets.token_urlsafe(32)`) is returned ONCE by
    the create endpoint and NEVER persisted — only its `sha256` hex (`token_hash`,
    64 chars) is stored. The guest GET/accept endpoints look up by `token_hash`
    (globally UNIQUE → bearer secret). Because the guest is unauthenticated (no
    `app.tenant_id`), the RLS USING clause carries a system-sentinel escape (mirror
    billing_outbox, Sprint 57.84) so the token lookup can read cross-tenant; the
    accept's user-creation then runs under `SET LOCAL app.tenant_id = invite.tenant_id`.

    Status state machine: pending → accepted (single-use, rowcount-guarded) /
    pending → revoked (admin) / pending → expired (lazy, on read past expires_at).

Key Components:
    - InviteStatus: enum mirror of the CHECK constraint
    - Invite: ORM (TenantScopedMixin)

Created: 2026-06-06 (Sprint 57.85)

Modification History:
    - 2026-06-06: Initial creation (Sprint 57.85 / US-1 + US-4)

Related:
    - migrations/versions/0026_invites.py
    - platform_layer/identity/invites.py (InvitesService)
    - infrastructure/db/models/identity.py (Tenant / User / Role / UserRole)
    - infrastructure/db/models/billing_outbox.py (sentinel-escape RLS precedent)
    - .claude/rules/multi-tenant-data.md 鐵律 1 (tenant_id NN + RLS)
    - c12-iam-block-bc-analysis-20260601.md §5 (invites = minimal self-contained slice)
"""

from __future__ import annotations

import enum
from datetime import datetime
from uuid import UUID as PyUUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.db.base import Base, TenantScopedMixin


class InviteStatus(str, enum.Enum):
    """invites.status — matches CHECK constraint."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    REVOKED = "revoked"
    EXPIRED = "expired"


class Invite(Base, TenantScopedMixin):
    """A single-use, expiring member invite (admin-created, guest-accepted)."""

    __tablename__ = "invites"

    id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    email: Mapped[str] = mapped_column(String(256), nullable=False)
    role_id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
    )
    invited_by: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'pending'")
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    accepted_user_id: Mapped[PyUUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        # Globally-unique bearer lookup (sentinel-scoped guest GET/accept).
        UniqueConstraint("token_hash", name="uq_invites_token_hash"),
        CheckConstraint(
            "status IN ('pending', 'accepted', 'revoked', 'expired')",
            name="ck_invites_status",
        ),
        Index("idx_invites_tenant", "tenant_id"),
        # At most one live pending invite per (tenant, email).
        Index(
            "uq_invites_pending_email",
            "tenant_id",
            "email",
            unique=True,
            postgresql_where=text("status = 'pending'"),
        ),
    )


__all__ = [
    "Invite",
    "InviteStatus",
]
