"""user_password_hash — add nullable password_hash to users (Sprint 57.86, C-12 IAM Block B/C).

Revision ID: 0027_user_password_hash
Revises: 0026_invites
Create Date: 2026-06-06

File: backend/src/infrastructure/db/migrations/versions/0027_user_password_hash.py
Purpose: Add a nullable `password_hash` column to the users table so an invited
    user can set a local password (at invite-accept) and sign back in via
    POST /auth/password-login. Nullable: OIDC/dev-login users have no local
    password. bcrypt hash string ($2b$12$…); see platform_layer/identity/
    passwords.py. Closes the C-12 local-credentials-leg schema (US-1).
Category: Infrastructure / Migration (Sprint 57.86 — C-12 IAM credentials)
Scope: Sprint 57.86 / US-1

Columns:
    users.password_hash VARCHAR(255) NULL — bcrypt hash; NULL for SSO-only users.

RLS:
    No new policy. users already has tenant_isolation RLS (migration 0001);
    the new column inherits it (RLS is row-level, not column-level). The
    accept's user-create + password-login's verify both run under the user's
    tenant context, so isolation is unchanged. check_rls_policies stays green
    (it requires ENABLE RLS + a CREATE POLICY on the table — already satisfied).

downgrade():
    Drops the column.

Modification History:
    - 2026-06-06: Initial creation (Sprint 57.86 / US-1)

Related:
    - infrastructure/db/models/identity.py:User.password_hash — ORM
    - platform_layer/identity/{passwords,credentials}.py — hash/verify + service
    - sprint-57-86-plan.md §3.1
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0027_user_password_hash"
down_revision: Union[str, None] = "0026_invites"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add nullable users.password_hash (bcrypt). No new RLS policy needed."""
    op.add_column(
        "users",
        sa.Column("password_hash", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    """Drop users.password_hash."""
    op.drop_column("users", "password_hash")
