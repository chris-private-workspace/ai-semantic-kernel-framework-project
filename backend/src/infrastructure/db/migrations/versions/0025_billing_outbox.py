"""billing_outbox — transactional outbox for durable idempotent cost events (Sprint 57.84).

Revision ID: 0025_billing_outbox
Revises: 0024_memory_ops
Create Date: 2026-06-05

File: backend/src/infrastructure/db/migrations/versions/0025_billing_outbox.py
Purpose: Create the billing_outbox table (transactional outbox: chat request
    enqueues a chargeable LLM/tool event atomically with its own txn; a
    background drainer materializes cost_ledger idempotently) + RLS policies.
    No data-seed (new empty outbox). Closes the C-15 billing-write-atomicity
    leg's schema (US-1 + US-2).
Category: Infrastructure / Migration (Sprint 57.84 — C-15 billing Outbox)
Scope: Sprint 57.84 / US-1 + US-2

Tables:
    billing_outbox
       - tenant_id FK → tenants(id) ON DELETE CASCADE (TenantScopedMixin).
       - UNIQUE (tenant_id, idempotency_key) — idempotent enqueue (US-2).
       - idx_billing_outbox_due (next_retry_at) WHERE status IN
         ('pending','failed') — the drainer claim path.
       - idx_billing_outbox_tenant (tenant_id).
       - CHECK on status + event_type enums.
       - RLS: tenant_isolation_* (USING) + tenant_insert_* (WITH CHECK) +
         FORCE, mirroring 0024_memory_ops. The USING clause carries a
         system-context ESCAPE for the background drainer: when
         app.tenant_id is the all-zeros sentinel, the row is visible
         cross-tenant so the poller can claim/update due rows across
         tenants. Per row the drainer sets app.tenant_id = row.tenant_id
         before the cost_ledger materialize (cost_ledger keeps its own RLS).
         No request ever runs under the sentinel (missing JWT → 401), so the
         escape does not weaken per-request isolation. check_rls_policies
         only requires ENABLE RLS + a CREATE POLICY ON the table (it does not
         constrain the USING expression).

downgrade():
    Drops both policies + indexes + the table.

Modification History:
    - 2026-06-05: Initial creation (Sprint 57.84 / US-1 + US-2)

Related:
    - 0024_memory_ops.py — two-policy RLS pattern (mirror + escape extension)
    - infrastructure/db/models/billing_outbox.py:BillingOutboxEvent — ORM
    - platform_layer/billing/billing_outbox.py — service + drainer (same sprint)
    - sprint-57-84-plan.md §3.1
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0025_billing_outbox"
down_revision: Union[str, None] = "0024_memory_ops"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# All-zeros sentinel tenant: the background drainer sets app.tenant_id to this
# value to claim/update due rows across tenants. A real request never runs
# under it (missing JWT → 401), so per-request isolation is unaffected.
_SYSTEM_SENTINEL = "00000000-0000-0000-0000-000000000000"


def upgrade() -> None:
    """Create billing_outbox + indexes + RLS (two policies + drainer escape)."""

    op.create_table(
        "billing_outbox",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("payload", postgresql.JSONB, nullable=False),
        sa.Column("idempotency_key", sa.String(256), nullable=False),
        sa.Column(
            "status",
            sa.String(16),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column(
            "retry_count",
            sa.Integer,
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text, nullable=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "idempotency_key", name="uq_billing_outbox_idem"),
        sa.CheckConstraint(
            "status IN ('pending', 'processing', 'done', 'failed')",
            name="ck_billing_outbox_status",
        ),
        sa.CheckConstraint(
            "event_type IN ('llm_call', 'tool_call')",
            name="ck_billing_outbox_event_type",
        ),
    )
    op.create_index(
        "idx_billing_outbox_due",
        "billing_outbox",
        ["next_retry_at"],
        postgresql_where=sa.text("status IN ('pending', 'failed')"),
    )
    op.create_index("idx_billing_outbox_tenant", "billing_outbox", ["tenant_id"])

    # ----- RLS (two policies + drainer system-context escape) ----------
    op.execute("ALTER TABLE billing_outbox ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE billing_outbox FORCE ROW LEVEL SECURITY")
    # USING — SELECT / UPDATE / DELETE: per-tenant isolation PLUS the
    # all-zeros system sentinel escape for the cross-tenant drainer claim.
    op.execute(f"""
        CREATE POLICY tenant_isolation_billing_outbox ON billing_outbox
            USING (
                tenant_id = current_setting('app.tenant_id', true)::uuid
                OR current_setting('app.tenant_id', true)::uuid
                   = '{_SYSTEM_SENTINEL}'::uuid
            )
        """)
    # WITH CHECK — INSERT: the producer (chat request) always runs under a
    # real tenant context, so enqueue stays strictly tenant-scoped.
    op.execute("""
        CREATE POLICY tenant_insert_billing_outbox ON billing_outbox
            FOR INSERT
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid)
        """)


def downgrade() -> None:
    """Drop RLS policies + indexes + table."""
    op.execute("DROP POLICY IF EXISTS tenant_insert_billing_outbox ON billing_outbox")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_billing_outbox ON billing_outbox")
    op.drop_index("idx_billing_outbox_tenant", table_name="billing_outbox")
    op.drop_index("idx_billing_outbox_due", table_name="billing_outbox")
    op.drop_table("billing_outbox")
