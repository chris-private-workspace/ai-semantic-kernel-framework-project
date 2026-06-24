"""session_todos — per-session durable todo list (Sprint 57.140, task primitive).

Revision ID: 0031_session_todos
Revises: 0030_tenant_skills
Create Date: 2026-06-24

File: backend/src/infrastructure/db/migrations/versions/0031_session_todos.py
Purpose: Create the session_todos table — the durable backing for the explicit
    task primitive (CC `TodoWrite`-like). The agent writes a whole structured plan
    via the Cat-2 `write_todos` tool; DBTodoStore upserts it here so a follow-up
    send rehydrates "what's left / what's done" across multiple 8-turn sends.
    One row per session (UNIQUE session_id, the upsert conflict target), the whole
    list as JSONB. NOT partitioned (1 row/session, low volume) + tenant-scoped RLS.
    No data-seed (new empty table). Closes the schema half of research #1.
Category: Infrastructure / Migration (Sprint 57.140 — explicit task primitive)
Scope: Sprint 57.140 / US-2

Tables:
    session_todos
       - tenant_id FK → tenants(id) ON DELETE CASCADE (TenantScopedMixin).
       - session_id FK → sessions(id) ON DELETE CASCADE; UNIQUE (the conflict target).
       - todos JSONB NOT NULL default '[]' — the whole list [{id,title,status},...].
       - created_at / updated_at.
       - idx_session_todos_tenant_session (tenant_id, session_id).
       - RLS: tenant_isolation_* (USING) + tenant_insert_* (WITH CHECK) + FORCE,
         mirroring 0030_tenant_skills (strict per-tenant, no sentinel escape — the
         chat loop + tool always run under a real tenant context via _set_tenant).

downgrade():
    Drops both policies + the index + the table.

Modification History:
    - 2026-06-24: Initial creation (Sprint 57.140 / US-2)

Related:
    - 0030_tenant_skills.py — two-policy RLS pattern (mirror)
    - infrastructure/db/models/sessions.py:SessionTodos — ORM
    - agent_harness/state_mgmt/todo_store.py:DBTodoStore — the store
    - sprint-57-140-plan.md §3.2
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0031_session_todos"
down_revision: Union[str, None] = "0030_tenant_skills"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create session_todos + index + RLS (two policies, strict per-tenant, no escape)."""

    op.create_table(
        "session_todos",
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
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "todos",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
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
        sa.UniqueConstraint("session_id", name="uq_session_todos_session"),
    )
    op.create_index(
        "idx_session_todos_tenant_session",
        "session_todos",
        ["tenant_id", "session_id"],
    )

    # ----- RLS (two policies, strict per-tenant — no sentinel escape) ------
    op.execute("ALTER TABLE session_todos ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE session_todos FORCE ROW LEVEL SECURITY")
    # USING — SELECT / UPDATE / DELETE: strict per-tenant isolation.
    op.execute("""
        CREATE POLICY tenant_isolation_session_todos ON session_todos
            USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
        """)
    # WITH CHECK — INSERT: rows are always written under a real tenant context.
    op.execute("""
        CREATE POLICY tenant_insert_session_todos ON session_todos
            FOR INSERT
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid)
        """)


def downgrade() -> None:
    """Drop RLS policies + index + table."""
    op.execute("DROP POLICY IF EXISTS tenant_insert_session_todos ON session_todos")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_session_todos ON session_todos")
    op.drop_index("idx_session_todos_tenant_session", table_name="session_todos")
    op.drop_table("session_todos")
