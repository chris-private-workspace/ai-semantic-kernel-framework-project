"""memory_user.dedup_key — write-side upsert dedup (Sprint 57.150).

Revision ID: 0032_memory_user_dedup_key
Revises: 0031_session_todos
Create Date: 2026-06-30

File: backend/src/infrastructure/db/migrations/versions/0032_memory_user_dedup_key.py
Purpose: Add the write-side dedup conflict key to memory_user so UserLayer.write
    becomes an idempotent upsert. Closes AD-Memory-User-Upsert-By-Key: 57.149 wired
    an auto-extractor that runs after EVERY send, so the same durable fact piled up
    duplicate rows and diluted the 57.148 profile() top-k. The new dedup_key =
    md5(normalize(content)) + a (tenant_id, user_id, dedup_key) unique constraint let
    write() ON CONFLICT DO UPDATE one row instead of inserting a second.
Category: Infrastructure / Migration (Sprint 57.150 — Cat 3 Memory dedup)
Scope: Sprint 57.150 / US-2

upgrade():
    1. Add memory_user.dedup_key VARCHAR(32) NULL (additive).
    2. Backfill dedup_key = md5(lower(btrim(regexp_replace(content,'\\s+',' ','g')))) —
       MUST match user_layer._dedup_key's Python normalization byte-for-byte (collapse
       all whitespace runs → single space, trim edges, lowercase) so live writes hit
       the backfilled keys.
    3. Delete pre-existing duplicate rows, keeping the best per
       (tenant_id, user_id, dedup_key): highest confidence, newest created_at tiebreak.
       MUST run BEFORE the unique constraint (existing dups would violate it).
    4. Add uq_memory_user_dedup UNIQUE (tenant_id, user_id, dedup_key).

    No RLS change (memory_user RLS lands in 0009). No partition change.

downgrade():
    Drop the unique constraint, then the column.

Modification History:
    - 2026-06-30: Initial creation (Sprint 57.150 / US-2)

Related:
    - 0031_session_todos.py — recent migration (mirror)
    - infrastructure/db/models/memory.py:MemoryUser — ORM (dedup_key + UniqueConstraint)
    - agent_harness/memory/layers/user_layer.py:_dedup_key — the matching Python normalization
    - sprint-57-150-plan.md §3.2
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0032_memory_user_dedup_key"
down_revision: Union[str, None] = "0031_session_todos"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Normalization MUST match user_layer._dedup_key (collapse → trim → lower → md5).
_BACKFILL_SQL = """
    UPDATE memory_user
       SET dedup_key = md5(lower(btrim(regexp_replace(content, '\\s+', ' ', 'g'))))
"""

# Keep the best row per (tenant_id, user_id, dedup_key): highest confidence,
# newest created_at as tiebreak; delete the rest. Must run before the unique
# constraint (existing dups would otherwise reject it).
_DEDUP_EXISTING_SQL = """
    DELETE FROM memory_user
     WHERE id IN (
        SELECT id FROM (
            SELECT id,
                   row_number() OVER (
                       PARTITION BY tenant_id, user_id, dedup_key
                       ORDER BY confidence DESC NULLS LAST, created_at DESC
                   ) AS rn
              FROM memory_user
             WHERE dedup_key IS NOT NULL
        ) ranked
         WHERE ranked.rn > 1
     )
"""


def upgrade() -> None:
    """Add dedup_key + backfill + dedup existing rows + unique constraint."""
    op.add_column(
        "memory_user",
        sa.Column("dedup_key", sa.String(length=32), nullable=True),
    )
    op.execute(_BACKFILL_SQL)
    op.execute(_DEDUP_EXISTING_SQL)
    op.create_unique_constraint(
        "uq_memory_user_dedup",
        "memory_user",
        ["tenant_id", "user_id", "dedup_key"],
    )


def downgrade() -> None:
    """Drop the unique constraint, then the column."""
    op.drop_constraint("uq_memory_user_dedup", "memory_user", type_="unique")
    op.drop_column("memory_user", "dedup_key")
