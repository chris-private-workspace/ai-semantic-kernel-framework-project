"""invites — DB-backed single-use expiring member invites (Sprint 57.85, C-12 IAM Block B).

Revision ID: 0026_invites
Revises: 0025_billing_outbox
Create Date: 2026-06-06

File: backend/src/infrastructure/db/migrations/versions/0026_invites.py
Purpose: Create the invites table (admin creates an invite for an email+role;
    the invitee accepts it to become an active User with the granted role).
    Invites are DB-backed (revocable / single-use / expiring / listable) + RLS.
    No data-seed (new empty table). Closes the C-12 invites-leg schema (US-1 + US-4).
Category: Infrastructure / Migration (Sprint 57.85 — C-12 IAM Block B invites)
Scope: Sprint 57.85 / US-1 + US-4

Tables:
    invites
       - tenant_id FK → tenants(id) ON DELETE CASCADE (TenantScopedMixin).
       - role_id FK → roles(id) ON DELETE CASCADE; invited_by FK → users(id)
         ON DELETE CASCADE; accepted_user_id FK → users(id) ON DELETE SET NULL.
       - UNIQUE (token_hash) — globally-unique high-entropy bearer lookup.
       - uq_invites_pending_email — partial UNIQUE (tenant_id, email) WHERE
         status='pending' (at most one live pending invite per email per tenant).
       - idx_invites_tenant (tenant_id).
       - CHECK on status enum.
       - RLS: tenant_isolation_* (USING) + tenant_insert_* (WITH CHECK) + FORCE,
         mirroring 0025_billing_outbox. The USING clause carries a system-context
         ESCAPE for the unauthenticated guest GET/accept: when app.tenant_id is the
         all-zeros sentinel, the row is visible cross-tenant so the guest endpoint
         can look up the invite by its globally-unique token_hash. The endpoint
         then sets app.tenant_id = invite.tenant_id before the accept's user-create
         (users keeps its own RLS). No request runs under the sentinel by default
         (the guest endpoint sets it explicitly only for the token lookup), so
         per-request isolation is unaffected. check_rls_policies only requires
         ENABLE RLS + a CREATE POLICY ON the table (not the USING expression).

downgrade():
    Drops both policies + indexes + the table.

Modification History:
    - 2026-06-06: Initial creation (Sprint 57.85 / US-1 + US-4)

Related:
    - 0025_billing_outbox.py — two-policy + sentinel-escape RLS pattern (mirror)
    - infrastructure/db/models/invites.py:Invite — ORM
    - platform_layer/identity/invites.py — InvitesService (same sprint)
    - sprint-57-85-plan.md §3.1
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0026_invites"
down_revision: Union[str, None] = "0025_billing_outbox"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# All-zeros sentinel tenant: the unauthenticated guest GET/accept endpoint sets
# app.tenant_id to this value ONLY to look up an invite by its globally-unique
# token_hash (the bearer secret). A real request never runs under it (missing JWT
# → 401), so per-request isolation is unaffected.
_SYSTEM_SENTINEL = "00000000-0000-0000-0000-000000000000"


def upgrade() -> None:
    """Create invites + indexes + RLS (two policies + guest-lookup escape)."""

    op.create_table(
        "invites",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("email", sa.String(256), nullable=False),
        sa.Column(
            "role_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("roles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "invited_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column(
            "status",
            sa.String(16),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "accepted_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("token_hash", name="uq_invites_token_hash"),
        sa.CheckConstraint(
            "status IN ('pending', 'accepted', 'revoked', 'expired')",
            name="ck_invites_status",
        ),
    )
    op.create_index("idx_invites_tenant", "invites", ["tenant_id"])
    # At most one live pending invite per (tenant, email).
    op.create_index(
        "uq_invites_pending_email",
        "invites",
        ["tenant_id", "email"],
        unique=True,
        postgresql_where=sa.text("status = 'pending'"),
    )

    # ----- RLS (two policies + guest-lookup system-context escape) --------
    op.execute("ALTER TABLE invites ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE invites FORCE ROW LEVEL SECURITY")
    # USING — SELECT / UPDATE / DELETE: per-tenant isolation PLUS the all-zeros
    # system sentinel escape for the unauthenticated guest token lookup.
    op.execute(f"""
        CREATE POLICY tenant_isolation_invites ON invites
            USING (
                tenant_id = current_setting('app.tenant_id', true)::uuid
                OR current_setting('app.tenant_id', true)::uuid
                   = '{_SYSTEM_SENTINEL}'::uuid
            )
        """)
    # WITH CHECK — INSERT: the admin create always runs under a real tenant
    # context, so enqueue stays strictly tenant-scoped.
    op.execute("""
        CREATE POLICY tenant_insert_invites ON invites
            FOR INSERT
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid)
        """)


def downgrade() -> None:
    """Drop RLS policies + indexes + table."""
    op.execute("DROP POLICY IF EXISTS tenant_insert_invites ON invites")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_invites ON invites")
    op.drop_index("uq_invites_pending_email", table_name="invites")
    op.drop_index("idx_invites_tenant", table_name="invites")
    op.drop_table("invites")
