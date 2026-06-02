"""agent_catalog — per-tenant AgentSpec definition catalog (Sprint 57.70).

Revision ID: 0023_agent_catalog
Revises: 0022_session_handoff_linkage
Create Date: 2026-06-02

File: backend/src/infrastructure/db/migrations/versions/0023_agent_catalog.py
Purpose: Create the agent_catalog table (per-tenant AgentSpec definitions
    backing Cat 11 HANDOFF persona resolution + the Subagent Registry) + RLS
    policies + a data migration that materializes the 3 default agents
    (researcher / reviewer / planner) per existing tenant.
Category: Infrastructure / Migration (Sprint 57.70 — real per-tenant agent-spec catalog)
Scope: Sprint 57.70 Stage-1a / US-1 + US-2

Tables:
    agent_catalog
       - Per-tenant AgentSpec definition (key/name/model/system_prompt/
         allowed_modes/status + budget+tools in the metadata JSONB).
       - UNIQUE(tenant_id, key) — role keys unique per tenant.
       - FK tenant_id → tenants(id) ON DELETE CASCADE (TenantScopedMixin).
       - RLS: BOTH tenant_isolation_* (USING) + tenant_insert_* (WITH CHECK)
         + FORCE, mirroring the 0019_rate_limit_configs.py two-policy pattern
         (the check_rls_policies V2 lint expects this).

Data migration (ADDITIVE):
    Seeds the 3 default agents per EXISTING tenant (SELECT id FROM tenants) so
    those tenants get editable rows. New / empty-catalog tenants are covered at
    runtime by the hardcoded DEFAULT_AGENTS fallback in
    platform_layer/handoff/persona_registry.py (no lazy-write in any read path).
    The default prompts are INLINED here (kept identical to DEFAULT_AGENTS) so
    the migration stays a dep-light frozen-in-time snapshot — same discipline as
    0019 inlining parse_rate_limit_item.

    NOTE: the agent_catalog JSONB column is named "metadata" at the DB level
    (the ORM exposes it as `meta_data` via mapped_column("metadata", ...)). Raw
    SQL here must quote the real physical column name "metadata".

downgrade():
    Drops both policies + the table.

Modification History:
    - 2026-06-02: Initial creation (Sprint 57.70 Stage-1a / US-1 + US-2)

Related:
    - 0019_rate_limit_configs.py — two-policy RLS + per-tenant seed pattern
    - 0022_session_handoff_linkage.py — prior head (down_revision)
    - infrastructure/db/models/agent_catalog.py:AgentCatalog — ORM (same sprint)
    - platform_layer/handoff/persona_registry.py:DEFAULT_AGENTS — fallback + seed source
    - sprint-57-70-plan.md §3.1 / §3.2
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0023_agent_catalog"
down_revision: Union[str, None] = "0022_session_handoff_linkage"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# === Default agents (INLINED snapshot of DEFAULT_AGENTS) ===================
# Why inline (not import): Alembic migrations must stay dep-light + frozen in
# time; persona_registry.py is live application code that may evolve. Kept
# identical to DEFAULT_AGENTS so the seeded rows match the hardcoded fallback.
# (key, name, system_prompt) — model NULL, allowed_modes ["handoff"], status
# "live", metadata {} for every seeded default.
_DEFAULT_AGENTS: list[tuple[str, str, str]] = [
    (
        "researcher",
        "Researcher",
        (
            "You are a research specialist agent. Investigate the user's question "
            "thoroughly, gather supporting evidence, cite sources where possible, "
            "and produce a structured, well-organized findings summary."
        ),
    ),
    (
        "reviewer",
        "Reviewer",
        (
            "You are a critical review specialist agent. Carefully assess the work "
            "handed to you for correctness, completeness, and risks. Point out "
            "concrete issues and concrete improvements; be specific and honest."
        ),
    ),
    (
        "planner",
        "Planner",
        (
            "You are a planning specialist agent. Break the user's goal into a "
            "clear, ordered set of verifiable steps, identify dependencies and "
            "risks, and state the success criteria for each step."
        ),
    ),
]


def upgrade() -> None:
    """Create agent_catalog + RLS + seed the 3 defaults per existing tenant."""

    # ----- agent_catalog table -----------------------------------------
    op.create_table(
        "agent_catalog",
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
        sa.Column("key", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("model", sa.String(128), nullable=True),
        sa.Column("system_prompt", sa.Text, nullable=False),
        sa.Column(
            "allowed_modes",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "status",
            sa.String(32),
            nullable=False,
            server_default=sa.text("'live'"),
        ),
        sa.Column(
            "metadata",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "is_active",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("TRUE"),
        ),
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
        sa.UniqueConstraint("tenant_id", "key", name="uq_agent_catalog_tenant_key"),
    )
    op.create_index("idx_agent_catalog_tenant", "agent_catalog", ["tenant_id"])

    # ----- RLS (two policies — 0019 pattern; check_rls_policies lint) ---
    op.execute("ALTER TABLE agent_catalog ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE agent_catalog FORCE ROW LEVEL SECURITY")
    # USING — applies to SELECT / UPDATE / DELETE
    op.execute("""
        CREATE POLICY tenant_isolation_agent_catalog ON agent_catalog
            USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
        """)
    # WITH CHECK — applies to INSERT / UPDATE row-target
    op.execute("""
        CREATE POLICY tenant_insert_agent_catalog ON agent_catalog
            FOR INSERT
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid)
        """)

    # ----- ADDITIVE data migration: seed defaults per existing tenant --
    # The migration runs as the schema owner; RLS does not FORCE on the owner,
    # so the INSERT proceeds without SET LOCAL. New tenants rely on the runtime
    # hardcoded DEFAULT_AGENTS fallback (no lazy-write). The JSONB column is the
    # physical "metadata"; allowed_modes seeded as ["handoff"].
    conn = op.get_bind()
    tenant_rows = conn.execute(sa.text("SELECT id FROM tenants")).fetchall()

    insert_sql = sa.text(
        "INSERT INTO agent_catalog "
        '(id, tenant_id, key, name, model, system_prompt, allowed_modes, status, "metadata", is_active) '
        "VALUES (gen_random_uuid(), :tenant_id, :key, :name, NULL, :system_prompt, "
        "'[\"handoff\"]'::jsonb, 'live', '{}'::jsonb, TRUE)"
    )

    for row in tenant_rows:
        tenant_id = row[0]
        for key, name, system_prompt in _DEFAULT_AGENTS:
            conn.execute(
                insert_sql,
                {
                    "tenant_id": tenant_id,
                    "key": key,
                    "name": name,
                    "system_prompt": system_prompt,
                },
            )


def downgrade() -> None:
    """Drop RLS policies + table."""
    op.execute("DROP POLICY IF EXISTS tenant_insert_agent_catalog ON agent_catalog")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_agent_catalog ON agent_catalog")
    op.drop_index("idx_agent_catalog_tenant", table_name="agent_catalog")
    op.drop_table("agent_catalog")
