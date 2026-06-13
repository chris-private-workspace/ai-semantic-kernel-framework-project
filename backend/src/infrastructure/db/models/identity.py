"""
File: backend/src/infrastructure/db/models/identity.py
Purpose: Identity / Tenancy ORM models — Tenant, User, Role, UserRole, RolePermission.
Category: Infrastructure / ORM (Identity & Tenancy group, per 09-db-schema-design.md Group 1)
Scope: Sprint 49.2 (initial Identity ORM)
Owner: infrastructure/db owner

Description:
    Multi-tenant identity foundation for V2. Maps to migration 0001_initial_identity.

    Hierarchy (per 09-db-schema-design.md L114-191):
        tenants (root, no tenant_id)
        ├── users (TenantScopedMixin)
        ├── roles (TenantScopedMixin)
        ├── user_roles (junction; NO tenant_id; tenant inferred via FK chain)
        └── role_permissions (NO tenant_id; tenant inferred via role)

    All session-scoped tables in subsequent migrations (sessions, tools,
    state, etc.) FK back to `tenants.id` directly via TenantScopedMixin.

Key Components:
    - Tenant: top-level multi-tenant root
    - User: per-tenant user identity (Entra ID / LDAP friendly via external_id)
    - Role: per-tenant RBAC role (e.g., "finance_manager")
    - UserRole: many-to-many user ↔ role mapping
    - RolePermission: per-role action permissions (resource_type / pattern / action)

Created: 2026-04-29 (Sprint 49.2 Day 1.5)
Last Modified: 2026-06-06

Modification History:
    - 2026-06-06: Sprint 57.86 — User +password_hash col (closes AD-Auth-Credentials-PasswordLogin)
    - 2026-05-26: Sprint 57.46 — Tenant +5 SaaS cols (closes AD-TenantSettings-Schema-Ext)
    - 2026-05-05: Sprint 56.1 Day 1 — Tenant ENHANCE: state/plan Enum + progress JSONB (D1)
    - 2026-04-29: Initial creation (Sprint 49.2 Day 1.5)

Related:
    - 09-db-schema-design.md §Group 1 Identity & Tenancy (L114-191)
    - .claude/rules/multi-tenant-data.md 鐵律 1
    - infrastructure/db/base.py (Base, TenantScopedMixin)
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import (
    Boolean,
    DateTime,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import (
    ForeignKey,
    Index,
    Integer,
    PrimaryKeyConstraint,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.db.base import Base, TenantScopedMixin


# =====================================================================
# TenantState — Phase 56.1 SaaS Stage 1 lifecycle state machine (per
# 15-saas-readiness.md §Tenant State Machine + sprint-56-1-plan.md §US-1)
# =====================================================================
class TenantState(str, Enum):
    """Tenant lifecycle states. Valid transitions enforced by TenantLifecycle."""

    REQUESTED = "requested"
    PROVISIONING = "provisioning"
    PROVISION_FAILED = "provision_failed"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


# =====================================================================
# TenantPlan — Phase 56.1 SaaS Stage 1 enterprise tier only (per
# user decision 2026-05-05; basic/standard deferred to Stage 2)
# =====================================================================
class TenantPlan(str, Enum):
    """Tenant subscription plan. Stage 1 = enterprise only."""

    ENTERPRISE = "enterprise"
    # Phase 56+ Stage 2 commercial SaaS will add: BASIC = "basic" / STANDARD = "standard"


# =====================================================================
# Tenant — root of the multi-tenant hierarchy (no tenant_id itself)
# =====================================================================
class Tenant(Base):
    """Top-level tenant. Per 09-db-schema-design.md L114-127.

    Sprint 56.1 enhancement: status (String) renamed to state (TenantState Enum)
    for SaaS Stage 1 lifecycle state machine. plan / provisioning_progress /
    onboarding_progress added per 15-saas-readiness.md §Tenant Lifecycle.
    """

    __tablename__ = "tenants"

    id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(256), nullable=False)
    state: Mapped[TenantState] = mapped_column(
        SQLEnum(TenantState, name="tenant_state", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        server_default=TenantState.REQUESTED.value,
    )
    plan: Mapped[TenantPlan] = mapped_column(
        SQLEnum(TenantPlan, name="tenant_plan", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        server_default=TenantPlan.ENTERPRISE.value,
    )
    provisioning_progress: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )
    onboarding_progress: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )
    meta_data: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )
    # Sprint 57.46 — +5 SaaS settings cols (closes AD-TenantSettings-Schema-Ext)
    region: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default=text("'global'"),
    )
    locale: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        server_default=text("'en-US'"),
    )
    retention_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("90"),
    )
    sso_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("FALSE"),
    )
    seats: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("5"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (Index("idx_tenants_state", "state"),)


# =====================================================================
# User — per-tenant user identity
# =====================================================================
class User(Base, TenantScopedMixin):
    """Per-tenant user. Per 09-db-schema-design.md L130-147."""

    __tablename__ = "users"

    id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    email: Mapped[str] = mapped_column(String(256), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(256))
    external_id: Mapped[str | None] = mapped_column(String(256))
    # Local-password credential (Sprint 57.86). Nullable: OIDC/dev-login users
    # have none; set at invite-accept, verified by POST /auth/password-login.
    # bcrypt hash string ($2b$12$…); see platform_layer/identity/passwords.py.
    password_hash: Mapped[str | None] = mapped_column(String(255))
    # TOTP second factor (Sprint 57.112, C-12 IAM Block C MFA). totp_secret is the
    # base32 shared secret (pyotp.random_base32, ≤32 chars); NULL until enrolled.
    # Stored PLAINTEXT — a TOTP secret must be readable to recompute codes (unlike
    # a password it cannot be hashed). At-rest encryption is deferred
    # (AD-MFA-Secret-At-Rest-Encryption — no encryption utility is wired today).
    # mfa_enabled flips true on the first confirmed code; password-login then
    # challenges for a TOTP before issuing a session. See identity/mfa.py.
    totp_secret: Mapped[str | None] = mapped_column(String(64))
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    preferences: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
        # idx_users_tenant is auto-created by TenantScopedMixin (index=True)
        Index(
            "idx_users_external",
            "external_id",
            postgresql_where=text("external_id IS NOT NULL"),
        ),
    )


# =====================================================================
# Role — per-tenant RBAC role
# =====================================================================
class Role(Base, TenantScopedMixin):
    """Per-tenant RBAC role. Per 09-db-schema-design.md L150-162."""

    __tablename__ = "roles"

    id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    display_name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    meta_data: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_roles_tenant_code"),)


# =====================================================================
# UserRole — junction table (no tenant_id; tenant inferred via FK chain)
# =====================================================================
class UserRole(Base):
    """User ↔ Role many-to-many junction. Per 09-db-schema-design.md L165-173."""

    __tablename__ = "user_roles"

    user_id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role_id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
    )
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    granted_by: Mapped[PyUUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )

    __table_args__ = (PrimaryKeyConstraint("user_id", "role_id", name="pk_user_roles"),)


# =====================================================================
# RolePermission — per-role action permissions (no tenant_id; via role)
# =====================================================================
class RolePermission(Base):
    """Per-role permission entry. Per 09-db-schema-design.md L176-189."""

    __tablename__ = "role_permissions"

    id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    role_id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
    )
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_pattern: Mapped[str] = mapped_column(String(256), nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    constraints: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )

    __table_args__ = (
        UniqueConstraint(
            "role_id",
            "resource_type",
            "resource_pattern",
            "action",
            name="uq_role_perms_full",
        ),
        Index("idx_role_perms_role", "role_id"),
    )


__all__ = ["Tenant", "User", "Role", "UserRole", "RolePermission"]
