"""rate_limit_alerts — durable 80%-threshold usage alert log (Sprint 57.62).

Revision ID: 0021_rate_limit_alerts
Revises: 0020_clear_rate_limits_meta_data
Create Date: 2026-05-29

File: backend/src/infrastructure/db/migrations/versions/0021_rate_limit_alerts.py
Purpose: Create the rate_limit_alerts table (per-(tenant, resource, window,
    window_start) 80%-threshold breach alert log) + RLS policies. No data
    migration — the table is populated at runtime by rate_limit_counter
    ._write_through when usage crosses the threshold.
Category: Infrastructure / Migration (Phase 58.x RateLimits usage alerting)
Scope: Sprint 57.62 Track A / US-1 (RateLimits 80% usage alerting)

Tables:
    rate_limit_alerts
       - Per (tenant, resource_type, window_type, window_start) durable alert.
       - UNIQUE(tenant_id, resource_type, window_type, window_start) — idempotent
         per-window upsert (peak actual_pct kept; first-crossing time preserved).
       - CHECK severity IN ('warning', 'critical') — mirrors SLAViolation lowercase.
       - FK tenant_id → tenants(id) ON DELETE CASCADE (TenantScopedMixin).
       - Index (tenant_id, triggered_at) for the recent-alerts GET ordering.
       - RLS: BOTH tenant_isolation_* (USING) + tenant_insert_* (WITH CHECK),
         mirroring the 0019 two-policy pattern (the check_rls_policies V2 lint
         expects this; current_setting('app.tenant_id', true) missing_ok arg).

No data migration: unlike 0019 (which seeded config from meta_data), this table
    starts empty; the enforcement point writes rows lazily on threshold crossings.

downgrade():
    Drops both policies + the table.

Modification History:
    - 2026-05-29: Initial creation (Sprint 57.62 Track A / US-1 — RateLimits 80%
      usage alerting)

Related:
    - 0019_rate_limit_configs.py — sibling two-policy RLS + create_table pattern
    - 0009_rls_policies.py — two-policy RLS pattern (USING + WITH CHECK)
    - 0020_clear_rate_limits_meta_data.py — prior head (down_revision)
    - infrastructure/db/models/api_keys.py:RateLimitAlert — ORM (same sprint)
    - infrastructure/db/models/sla.py:SLAViolation — alert-log + lowercase-CHECK precedent
    - platform_layer/tenant/rate_limit_alert_store.py — the store that writes/reads it
    - sprint-57-62-plan.md §Track A
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0021_rate_limit_alerts"
down_revision: Union[str, None] = "0020_clear_rate_limits_meta_data"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create rate_limit_alerts + RLS (no data migration — runtime-populated)."""

    # ----- rate_limit_alerts table -------------------------------------
    op.create_table(
        "rate_limit_alerts",
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
        sa.Column("resource_type", sa.String(64), nullable=False),
        sa.Column("window_type", sa.String(16), nullable=False),
        sa.Column("threshold_pct", sa.Integer, nullable=False),
        sa.Column("actual_pct", sa.Integer, nullable=False),
        sa.Column("used", sa.Integer, nullable=False),
        sa.Column("quota", sa.Integer, nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "triggered_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "resource_type",
            "window_type",
            "window_start",
            name="uq_rate_limit_alerts_window",
        ),
        sa.CheckConstraint(
            "severity IN ('warning', 'critical')",
            name="ck_rate_limit_alerts_severity",
        ),
    )
    op.create_index(
        "ix_rate_limit_alerts_tenant_recent",
        "rate_limit_alerts",
        ["tenant_id", "triggered_at"],
    )

    # ----- RLS (two policies — 0019 pattern; check_rls_policies lint) ---
    op.execute("ALTER TABLE rate_limit_alerts ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE rate_limit_alerts FORCE ROW LEVEL SECURITY")
    # USING — applies to SELECT / UPDATE / DELETE
    op.execute("""
        CREATE POLICY tenant_isolation_rate_limit_alerts ON rate_limit_alerts
            USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
        """)
    # WITH CHECK — applies to INSERT / UPDATE row-target
    op.execute("""
        CREATE POLICY tenant_insert_rate_limit_alerts ON rate_limit_alerts
            FOR INSERT
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid)
        """)


def downgrade() -> None:
    """Drop RLS policies + table."""
    op.execute("DROP POLICY IF EXISTS tenant_insert_rate_limit_alerts ON rate_limit_alerts")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_rate_limit_alerts ON rate_limit_alerts")
    op.drop_index("ix_rate_limit_alerts_tenant_recent", table_name="rate_limit_alerts")
    op.drop_table("rate_limit_alerts")
