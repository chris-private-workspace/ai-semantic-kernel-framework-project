"""rate_limit_configs — durable RateLimits config table (Sprint 57.59).

Revision ID: 0019_rate_limit_configs
Revises: 0018_tenant_settings_extension
Create Date: 2026-05-28

File: backend/src/infrastructure/db/migrations/versions/0019_rate_limit_configs.py
Purpose: Create the rate_limit_configs table (per-tenant per-(resource,window)
    quota config) + RLS policies + an ADDITIVE data migration that seeds it from
    each tenant's existing tenant.meta_data["rate_limits"] JSONB list.
Category: Infrastructure / Migration (Phase 58.x RateLimits Potemkin close)
Scope: Sprint 57.59 Day 1 / US-1 (closes AD-RateLimits-Potemkin-Migration-Phase58)

Tables:
    rate_limit_configs
       - Per (tenant, resource_type, window_type) durable quota config.
       - UNIQUE(tenant_id, resource_type, window_type)
       - FK tenant_id → tenants(id) ON DELETE CASCADE
       - RLS: BOTH tenant_isolation_* (USING) + tenant_insert_* (WITH CHECK),
         mirroring the 0009_rls_policies.py two-policy pattern (the
         check_rls_policies V2 lint expects this).

Data migration (ADDITIVE — Day 0 D-DAY0-N + R1):
    Reads `SELECT id, meta_data FROM tenants WHERE meta_data ? 'rate_limits'`
    and parses each {label, value} item INLINE (NOT importing
    platform_layer.tenant.rate_limit_counter — that module imports Redis types at
    module level; Alembic migrations must be dep-light historical snapshots). The
    inline parse mirrors parse_rate_limit_item() exactly:
        label "API requests" -> resource_type "api_requests" (slug fallback)
        value "100 / min"     -> (quota=100, window_type="min")
    Unparseable items (e.g. "50 concurrent", malformed, non-positive) are SKIPPED
    gracefully (fail-open — a bad admin config never blocks the migration), and
    duplicate (resource_type, window_type) within one tenant are de-duped
    (last-wins) before INSERT so the unique constraint never trips.

    meta_data is NOT modified/deleted here — it stays as a transitional read
    fallback (cleanup deferred to AD-RateLimits-MetaData-Cleanup-Phase58).

downgrade():
    Drops both policies + the table. Config then falls back to the retained
    meta_data["rate_limits"] — no data loss.

Modification History:
    - 2026-05-28: Initial creation (Sprint 57.59 Day 1 / US-1 — RateLimits config
      two-table split; AP-4 Potemkin close)

Related:
    - 0006_api_keys_rate_limits.py — sibling rate_limits (usage) table pattern
    - 0009_rls_policies.py — two-policy RLS pattern (USING + WITH CHECK)
    - 0018_tenant_settings_extension.py — prior head (down_revision)
    - infrastructure/db/models/api_keys.py:RateLimitConfig — ORM (same sprint)
    - platform_layer/tenant/rate_limit_counter.py:parse_rate_limit_item — the
      live parser this inline logic mirrors
    - sprint-57-59-plan.md §4.2
"""

from __future__ import annotations

import re
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0019_rate_limit_configs"
down_revision: Union[str, None] = "0018_tenant_settings_extension"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# === Inline {label, value} parser ======================================
# Why inline (not import): rate_limit_counter.py imports redis.asyncio types at
# module level; Alembic migrations must stay dep-light + frozen-in-time. This is
# an intentional, acceptable duplication of parse_rate_limit_item() — the live
# service keeps its own copy; this is the point-in-time snapshot used once.
# Mapping kept identical to parse_rate_limit_item / label_to_resource so the
# seeded rows match what the live store would produce.
_LABEL_TO_RESOURCE: dict[str, str] = {
    "api requests": "api_requests",
    "tool calls": "tool_calls",
    "sse connections": "sse_connections",
}

# Canonical display window units the config table stores in window_type.
# parse_rate_limit_value accepts aliases (second/minute/hr/...); we normalise to
# the canonical short form so the reverse projection round-trips deterministically.
_WINDOW_ALIASES: dict[str, str] = {
    "sec": "sec",
    "second": "sec",
    "min": "min",
    "minute": "min",
    "hour": "hour",
    "hr": "hour",
    "day": "day",
}

# e.g. "100 / min", "1,000 / minute". "50 concurrent" does NOT match (skipped).
_VALUE_RE = re.compile(r"^\s*([\d,]+)\s*/\s*([a-zA-Z]+)\s*$")


def _label_to_resource(label: str) -> str:
    """Canonical resource key for a display label (slug fallback for custom)."""
    key = label.strip().lower()
    if key in _LABEL_TO_RESOURCE:
        return _LABEL_TO_RESOURCE[key]
    slug = re.sub(r"[^a-z0-9]+", "_", key).strip("_")
    return slug or "unknown"


def _parse_item(item: object) -> tuple[str, str, int] | None:
    """Parse a stored {label, value} dict into (resource_type, window_type, quota).

    Returns None for non-dict, missing label, non-rate value (e.g. "50
    concurrent"), unknown window alias, or non-positive quota — callers skip
    these (fail-open: a bad config never blocks the migration).
    """
    if not isinstance(item, dict):
        return None
    label = str(item.get("label", ""))
    value = str(item.get("value", ""))
    if not label:
        return None
    m = _VALUE_RE.match(value)
    if m is None:
        return None
    raw_quota, raw_window = m.group(1), m.group(2).lower()
    window_type = _WINDOW_ALIASES.get(raw_window)
    if window_type is None:
        return None
    try:
        quota = int(raw_quota.replace(",", ""))
    except ValueError:
        return None
    if quota <= 0:
        return None
    return _label_to_resource(label), window_type, quota


def upgrade() -> None:
    """Create rate_limit_configs + RLS + additive data migration from meta_data."""

    # ----- rate_limit_configs table ------------------------------------
    op.create_table(
        "rate_limit_configs",
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
        sa.Column("window_type", sa.String(32), nullable=False),
        sa.Column("quota", sa.Integer, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "resource_type",
            "window_type",
            name="uq_rate_limit_configs_tenant_resource_window",
        ),
    )
    op.create_index("ix_rate_limit_configs_tenant_id", "rate_limit_configs", ["tenant_id"])

    # ----- RLS (two policies — 0009 pattern; check_rls_policies lint) ---
    op.execute("ALTER TABLE rate_limit_configs ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE rate_limit_configs FORCE ROW LEVEL SECURITY")
    # USING — applies to SELECT / UPDATE / DELETE
    op.execute("""
        CREATE POLICY tenant_isolation_rate_limit_configs ON rate_limit_configs
            USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
        """)
    # WITH CHECK — applies to INSERT / UPDATE row-target
    op.execute("""
        CREATE POLICY tenant_insert_rate_limit_configs ON rate_limit_configs
            FOR INSERT
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid)
        """)

    # ----- ADDITIVE data migration from tenant.meta_data["rate_limits"] -
    # Read each tenant carrying a rate_limits JSONB list, inline-parse the items,
    # de-dup (resource_type, window_type) last-wins, and INSERT config rows.
    # meta_data is left untouched (transitional fallback). Best-effort: rows that
    # don't parse are skipped (fail-open). The migration runs as the schema owner;
    # RLS does not FORCE on the owner, so the INSERT proceeds without SET LOCAL.
    # NOTE: the tenants JSONB column is named "metadata" at the DB level (the
    # ORM exposes it as the `meta_data` attribute via mapped_column("metadata", ...)
    # in identity.py:Tenant). Raw SQL here must use the real column name.
    conn = op.get_bind()
    rows = conn.execute(
        sa.text('SELECT id, "metadata" FROM tenants WHERE "metadata" ? \'rate_limits\'')
    ).fetchall()

    insert_sql = sa.text(
        "INSERT INTO rate_limit_configs "
        "(id, tenant_id, resource_type, window_type, quota) "
        "VALUES (gen_random_uuid(), :tenant_id, :resource_type, :window_type, :quota)"
    )

    for row in rows:
        tenant_id = row[0]
        meta = row[1] or {}
        raw = meta.get("rate_limits") if isinstance(meta, dict) else None
        if not isinstance(raw, list):
            continue
        # De-dup within one tenant on (resource_type, window_type), last item wins
        # (the unique constraint forbids duplicates; display lists may collide
        # after label→resource slugging).
        deduped: dict[tuple[str, str], int] = {}
        for item in raw:
            parsed = _parse_item(item)
            if parsed is None:
                continue
            resource_type, window_type, quota = parsed
            deduped[(resource_type, window_type)] = quota
        for (resource_type, window_type), quota in deduped.items():
            conn.execute(
                insert_sql,
                {
                    "tenant_id": tenant_id,
                    "resource_type": resource_type,
                    "window_type": window_type,
                    "quota": quota,
                },
            )


def downgrade() -> None:
    """Drop RLS policies + table (config falls back to retained meta_data)."""
    op.execute("DROP POLICY IF EXISTS tenant_insert_rate_limit_configs ON rate_limit_configs")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_rate_limit_configs ON rate_limit_configs")
    op.drop_index("ix_rate_limit_configs_tenant_id", table_name="rate_limit_configs")
    op.drop_table("rate_limit_configs")
