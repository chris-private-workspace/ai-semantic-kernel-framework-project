"""Sprint 57.46 Day 1 — Tenant settings 5-column extension.

Revision ID: 0018_tenant_settings_extension
Revises: 0017_verification_log
Create Date: 2026-05-26

File: backend/src/infrastructure/db/migrations/versions/0018_tenant_settings_extension.py
Purpose: Extend `tenants` table with 5 SaaS settings columns required by
    /tenant-settings frontend page real-data migration (Sprint 57.44 D-DAY0-4
    fixture-first lock-in unblock; AD-TenantSettings-Backend-Schema-Extension).

Schema changes on `tenants` table (all NOT NULL with sensible defaults for
backfill on existing rows; Tenant table is global root, no RLS needed per
0009_rls_policies.py:36 — `tenants` is listed under "Tables intentionally
global (no RLS)"):

    ADD region          VARCHAR(32)  NOT NULL DEFAULT 'global'
    ADD locale          VARCHAR(16)  NOT NULL DEFAULT 'en-US'
    ADD retention_days  INTEGER      NOT NULL DEFAULT 90
    ADD sso_enabled     BOOLEAN      NOT NULL DEFAULT FALSE
    ADD seats           INTEGER      NOT NULL DEFAULT 5

Multi-tenant: Tenant table itself is the registry root (no tenant_id; per
0009_rls_policies.py:36); these columns are tenant-scope settings stored on
the root row.

Modification History:
    - 2026-05-26: Initial creation (Sprint 57.46 Day 1 / Track B — closes
      AD-TenantSettings-Backend-Schema-Extension)

Related:
    - 0014_phase56_1_saas_foundation.py — pattern reference for tenant column ALTERs
    - infrastructure/db/models/identity.py:Tenant — ORM model (extended same sprint)
    - api/v1/admin/tenants.py — TenantResponse + PATCH endpoint (extended same sprint)
    - sprint-57-44 D-DAY0-4 — origin of schema gap (Tenant ORM was missing
      region/locale/retention_days/Identity & SSO/seats per /tenant-settings
      fixture-first lock-in)
    - sprint-57-46-plan.md §4.2 — column spec source
    - .claude/rules/multi-tenant-data.md (Tenant table = global root exception)
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0018_tenant_settings_extension"
down_revision: Union[str, None] = "0017_verification_log"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add 5 SaaS settings columns to tenants table with safe defaults."""

    # 1. region — regional setting (apac / emea / americas / global)
    op.add_column(
        "tenants",
        sa.Column(
            "region",
            sa.String(32),
            nullable=False,
            server_default=sa.text("'global'"),
        ),
    )

    # 2. locale — BCP-47 locale code
    op.add_column(
        "tenants",
        sa.Column(
            "locale",
            sa.String(16),
            nullable=False,
            server_default=sa.text("'en-US'"),
        ),
    )

    # 3. retention_days — data retention policy (GDPR-relevant)
    op.add_column(
        "tenants",
        sa.Column(
            "retention_days",
            sa.Integer,
            nullable=False,
            server_default=sa.text("90"),
        ),
    )

    # 4. sso_enabled — Identity/SSO toggle
    op.add_column(
        "tenants",
        sa.Column(
            "sso_enabled",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("FALSE"),
        ),
    )

    # 5. seats — Plan seat limit
    op.add_column(
        "tenants",
        sa.Column(
            "seats",
            sa.Integer,
            nullable=False,
            server_default=sa.text("5"),
        ),
    )


def downgrade() -> None:
    """Drop 5 SaaS settings columns (reverse order)."""
    op.drop_column("tenants", "seats")
    op.drop_column("tenants", "sso_enabled")
    op.drop_column("tenants", "retention_days")
    op.drop_column("tenants", "locale")
    op.drop_column("tenants", "region")
