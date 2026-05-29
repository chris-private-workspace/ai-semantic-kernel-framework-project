"""clear_rate_limits_meta_data — retire transitional RateLimits JSONB (Sprint 57.60).

Revision ID: 0020_clear_rate_limits_meta_data
Revises: 0019_rate_limit_configs
Create Date: 2026-05-29

File: backend/src/infrastructure/db/migrations/versions/0020_clear_rate_limits_meta_data.py
Purpose: Data-only cleanup migration that strips the now-redundant
    tenant.meta_data["rate_limits"] JSONB key from every tenant. Sprint 57.59
    (0019) migrated this config into the rate_limit_configs table and made it the
    source of truth; Sprint 57.60 removed the transitional meta_data read-fallback
    + PUT dual-write, so the stored blob is dead weight. This strips it.
Category: Infrastructure / Migration (Phase 58.x RateLimits MetaData cleanup)
Scope: Sprint 57.60 Day 1 / US-2 (closes AD-RateLimits-MetaData-Cleanup-Phase58)

Tables:
    (none created/dropped) — data-only UPDATE on tenants.meta_data. No DDL, no new
    table, no RLS policy change (check_rls_policies 20 tables unchanged).

upgrade() — strip the key (additive cleanup, idempotent):
    UPDATE tenants SET "metadata" = "metadata" - 'rate_limits'
        WHERE "metadata" ? 'rate_limits'
    Only touches tenants carrying the key (idempotent — re-running is a no-op).
    rate_limit_configs is untouched (already authoritative since 0019).

downgrade() — reverse-populate from the config table (reversibility):
    Reads each tenant's rate_limit_configs rows, INLINE-projects them back to the
    {label, value} display shape, and writes meta_data["rate_limits"]. This keeps
    the migration symmetric so a downgrade past 0020 then 0019 still resolves the
    0019 retained-meta_data fallback. The reverse projection is the inverse of
    0019's inline parse: it is LOSSY for custom labels (canonical resource_type
    slug -> humanised display string, not the operator's original string) — but
    enforcement semantics (quota / window) round-trip exactly. Acceptable: a
    downgrade is a dev-only operation.

Dep-light (Sprint 57.59 D-DAY0-N rule): the projection is INLINE here, NOT
    importing platform_layer.tenant.rate_limit_config_store (which pulls Redis +
    ORM types). Alembic migrations are frozen point-in-time snapshots. The inline
    _inline_project mirrors RateLimitConfigStore.project_config_to_item +
    _resource_to_label.

Physical column (Sprint 57.59 D-DAY1-1 / D-DAY0-M = AD-Day0-Prong3-Physical-
    Column-Read): the tenants JSONB column is named "metadata" at the DB level —
    the ORM exposes it as the `meta_data` attribute via mapped_column("metadata",
    ...) in identity.py:Tenant. 0019 raw SQL already uses "metadata"; this
    migration must too.

Modification History:
    - 2026-05-29: Initial creation (Sprint 57.60 Day 1 / US-2 — retire transitional
      meta_data["rate_limits"] fallback blob)

Related:
    - 0019_rate_limit_configs.py — created the table + additive seed (this reverses
      the meta_data leg; its _parse_item is the forward inverse of _inline_project)
    - platform_layer/tenant/rate_limit_config_store.py:project_config_to_item /
      _resource_to_label — the live projection this inline logic mirrors
    - api/v1/admin/tenants.py / middleware/rate_limit.py / tool_rate_limit_gate.py
      — the 4 read sites + PUT whose meta_data fallback was removed this sprint
    - sprint-57-60-plan.md §4.3
"""

from __future__ import annotations

import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0020_clear_rate_limits_meta_data"
down_revision: Union[str, None] = "0019_rate_limit_configs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# === Inline reverse projection (config row -> {label, value}) ==========
# Why inline (not import): rate_limit_config_store.py pulls Redis + ORM types at
# module level; Alembic migrations must stay dep-light + frozen-in-time. This is
# the inverse of 0019's _parse_item and mirrors
# RateLimitConfigStore.project_config_to_item / _resource_to_label so a
# downgrade reproduces the {label, value} display shape the GET path expects.
# LOSSY for custom labels (canonical slug -> humanise), lossless for the 3 known
# resources + enforcement semantics (quota / window).
_RESOURCE_TO_LABEL: dict[str, str] = {
    "api_requests": "API requests",
    "tool_calls": "Tool calls",
    "sse_connections": "SSE connections",
}


def _resource_to_label(resource_type: str) -> str:
    """Display label for a canonical resource key (humanise slug for custom)."""
    if resource_type in _RESOURCE_TO_LABEL:
        return _RESOURCE_TO_LABEL[resource_type]
    return resource_type.replace("_", " ").strip().capitalize() or resource_type


def _inline_project(resource_type: str, window_type: str, quota: int) -> dict[str, str]:
    """Project (resource_type, window_type, quota) back to {label, value}.

    Quota is rendered with a thousands separator (mirrors
    project_config_to_item so "1000 / min" -> "1,000 / min").
    """
    return {
        "label": _resource_to_label(resource_type),
        "value": f"{quota:,} / {window_type}",
    }


def upgrade() -> None:
    """Strip the now-redundant rate_limits key from every tenant's meta_data."""
    # JSONB minus-key operator; only touches tenants that carry the key
    # (idempotent — re-running is a no-op). The config lives in rate_limit_configs
    # since 0019, so nothing is lost. Physical column is "metadata" (see header).
    conn = op.get_bind()
    conn.execute(
        sa.text(
            'UPDATE tenants SET "metadata" = "metadata" - \'rate_limits\' '
            "WHERE \"metadata\" ? 'rate_limits'"
        )
    )


def downgrade() -> None:
    """Reverse-populate meta_data["rate_limits"] from rate_limit_configs rows.

    Reversibility (dev-only; lossy for custom labels — see header). Reads the
    config rows, inline-projects them back to {label, value}, groups by tenant,
    and writes the list into meta_data["rate_limits"] via jsonb_set.
    """
    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            "SELECT tenant_id, resource_type, window_type, quota "
            "FROM rate_limit_configs ORDER BY tenant_id, resource_type, window_type"
        )
    ).fetchall()

    by_tenant: dict[object, list[dict[str, str]]] = {}
    for row in rows:
        tenant_id, resource_type, window_type, quota = row[0], row[1], row[2], int(row[3])
        item = _inline_project(resource_type, window_type, quota)
        by_tenant.setdefault(tenant_id, []).append(item)

    # NOTE: CAST(:items AS jsonb) — NOT :items::jsonb. The `::` cast shorthand
    # collides with named-param parsing under the asyncpg driver (the test path);
    # CAST(...) is equivalent SQL that parses cleanly under both psycopg (Alembic)
    # and asyncpg.
    update_sql = sa.text(
        'UPDATE tenants SET "metadata" = jsonb_set('
        "COALESCE(\"metadata\", '{}'::jsonb), '{rate_limits}', CAST(:items AS jsonb)) "
        "WHERE id = :tid"
    )
    for tenant_id, items in by_tenant.items():
        conn.execute(update_sql, {"items": json.dumps(items), "tid": tenant_id})
