"""user_mfa_totp — add totp_secret + mfa_enabled to users (Sprint 57.112, IAM Block C MFA).

Revision ID: 0029_user_mfa_totp
Revises: 0028_sidechain_sessions
Create Date: 2026-06-13

File: backend/src/infrastructure/db/migrations/versions/0029_user_mfa_totp.py
Purpose: Add the two columns the TOTP second factor needs on the users table so a
    logged-in user can enroll an authenticator (POST /api/v1/mfa/enroll →
    /enroll/confirm) and the password-login path can challenge for a code
    (POST /api/v1/mfa/verify). totp_secret holds the base32 shared secret;
    mfa_enabled gates whether login requires the second factor. Closes the
    TOTP leg of C-12 Block C (US-1).
Category: Infrastructure / Migration (Sprint 57.112 — C-12 IAM MFA)
Scope: Sprint 57.112 / US-1

Columns:
    users.totp_secret VARCHAR(64) NULL — base32 TOTP shared secret (pyotp.random_base32(),
        ≤32 chars). NULL for users who have not enrolled. Stored plaintext: a TOTP
        secret is a SHARED secret that must be readable to compute codes (unlike a
        password it cannot be hashed). At-rest encryption is a tracked deferred AD
        (AD-MFA-Secret-At-Rest-Encryption) — no encryption utility is wired today.
    users.mfa_enabled BOOLEAN NOT NULL DEFAULT false — true once the user confirms
        their first code; password-login challenges for a TOTP code when true.

RLS:
    No new policy. users already has tenant_isolation RLS (migration 0001/0009);
    the new columns inherit it (RLS is row-level, not column-level). enroll/confirm/
    verify all run under the user's tenant context (_set_tenant). check_rls_policies
    stays green (ENABLE RLS + a CREATE POLICY on users already satisfied).

downgrade():
    Drops both columns.

Modification History:
    - 2026-06-13: Initial creation (Sprint 57.112 / US-1)

Related:
    - infrastructure/db/models/identity.py:User.{totp_secret,mfa_enabled} — ORM
    - platform_layer/identity/mfa.py — TOTPService (enroll/confirm/verify)
    - api/v1/mfa.py — POST /api/v1/mfa/{enroll,enroll/confirm,verify}
    - sprint-57-112-plan.md §3.1
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0029_user_mfa_totp"
down_revision: Union[str, None] = "0028_sidechain_sessions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add nullable users.totp_secret + non-null users.mfa_enabled. No new RLS policy."""
    op.add_column(
        "users",
        sa.Column("totp_secret", sa.String(64), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "mfa_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    """Drop users.mfa_enabled + users.totp_secret."""
    op.drop_column("users", "mfa_enabled")
    op.drop_column("users", "totp_secret")
