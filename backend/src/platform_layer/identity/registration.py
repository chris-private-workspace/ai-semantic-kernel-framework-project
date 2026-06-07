"""
File: backend/src/platform_layer/identity/registration.py
Purpose: RegistrationService — self-service tenant registration (creates tenant + first admin).
Category: platform_layer.identity (C-12 IAM Block B registration leg)
Scope: Sprint 57.87 / US-1 + US-2 + US-3

Description:
    A prospective customer registers a brand-new workspace: register() creates a
    Tenant (state ACTIVE immediately — self-serve trial, skipping the all-stub
    ProvisioningWorkflow), seeds a real "admin" Role in that tenant + grants the
    founding User the admin UserRole, and writes a tenant_registered WORM audit
    row. Returns (tenant, user); the caller issues no session — the shipped
    register wizard redirects to the OIDC /auth/callback to log in.

    RLS context: `tenants` is the RLS-free root, so the slug-unique check + the
    Tenant INSERT need no context; the User / Role / UserRole INSERTs run under
    `_set_tenant(db, new_tenant.id)` (mirrors invites.py + the billing_outbox
    drainer — set_config app.tenant_id per write).

    Honest boundary (Sprint 57.87): the seeded admin UserRole is DB-real but NOT
    yet authz-effective — gating reads the JWT 'roles' claim and the OIDC callback
    bakes roles=["user"]; making the DB role grant the JWT admin is a separate
    DB-RBAC→JWT wiring slice (AD-RBAC-DB-To-JWT-Wiring-Phase58). This service is
    the codebase's FIRST real Role(...) creation (seed_default_roles is a stub).

Key Components:
    - RegistrationError + TenantSlugTakenError (carry an HTTP status hint)
    - RegistrationService.register: create tenant + admin role + user + userrole + audit
    - set_/get_/maybe_get_registration_service: lenient singleton (no lifespan wiring)

Created: 2026-06-06 (Sprint 57.87)
Last Modified: 2026-06-07

Modification History:
    - 2026-06-07: FIX-030 — IntegrityError(code) → TenantSlugTakenError 409 (slug race)
    - 2026-06-06: Initial creation (Sprint 57.87 / US-1..US-3) — self-service registration

Related:
    - infrastructure/db/models/identity.py — Tenant / Role / User / UserRole (reused; no migration)
    - platform_layer/identity/invites.py — User+UserRole+audit + _set_tenant pattern (mirror)
    - infrastructure/db/audit_helper.py:append_audit — WORM audit chain
    - api/v1/tenants.py — public POST /tenants/register (the HTTP surface)
    - .claude/rules/multi-tenant-data.md 鐵律 (tenant context per write)
    - c12-iam-block-bc-analysis-20260601.md §5 (Block B legs)
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.audit_helper import append_audit
from infrastructure.db.models.identity import (
    Role,
    Tenant,
    TenantPlan,
    TenantState,
    User,
    UserRole,
)

# The role code granted to the founding user. "admin" matches the JWT-claim
# gating convention (_ADMIN_PLATFORM_ROLES in platform_layer/identity/auth.py).
FOUNDING_ADMIN_ROLE_CODE = "admin"


# === Typed errors (carry an HTTP status hint for the router) ===
class RegistrationError(Exception):
    """Base registration error; subclasses set `status_code` + a safe `detail`."""

    status_code: int = 400
    detail: str = "registration error"

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(detail or self.detail)
        if detail:
            self.detail = detail


class TenantSlugTakenError(RegistrationError):
    status_code = 409
    detail = "that workspace URL is already taken"


@dataclass
class RegistrationResult:
    """The created tenant + founding user (returned by register())."""

    tenant: Tenant
    user: User


# === RegistrationService: self-service tenant onboarding ===
# Why: IAM Block B needs a self-service path for a brand-new org to register
# (the only existing tenant-create paths are dev-login (dev-only) + admin-create
# (require_admin_platform_role)). Mirrors invites.accept's User+UserRole+audit
# write pattern + adds Tenant-creation and the first real Role seed.
class RegistrationService:
    """Self-service registration; manages its own RLS tenant context per write."""

    async def register(
        self,
        db: AsyncSession,
        *,
        email: str,
        full_name: str,
        company_name: str,
        tenant_slug: str,
        region: str,
        requested_plan: str,
        company_size: str | None = None,
    ) -> RegistrationResult:
        """Create a new tenant + founding admin user; return (tenant, user).

        The tenant is ACTIVE immediately (skips the all-stub ProvisioningWorkflow).
        A real "admin" Role is seeded in the tenant and granted to the user (the
        codebase's first real Role-creation). All non-tenant writes run under the
        new tenant's RLS context. Raises TenantSlugTakenError (409) on a duplicate
        slug. `requested_plan` / `company_size` are stored in tenant.meta_data
        (the TenantPlan enum only has ENTERPRISE today — plan tiers are Stage 2).
        """
        # 1. Slug-unique check (tenants is RLS-free → no context needed). A
        #    generic 409 (no "exists in tenant X" detail) so it can't enumerate.
        existing = (
            await db.execute(select(Tenant.id).where(Tenant.code == tenant_slug))
        ).scalar_one_or_none()
        if existing is not None:
            raise TenantSlugTakenError()

        # 2. Create the tenant (ACTIVE now; plan tiers not real yet → meta_data).
        tenant = Tenant(
            code=tenant_slug,
            display_name=company_name,
            state=TenantState.ACTIVE,
            plan=TenantPlan.ENTERPRISE,
            region=region or "global",
            meta_data={"requested_plan": requested_plan, "company_size": company_size},
        )
        db.add(tenant)
        try:
            await db.flush()  # obtain tenant.id; unique(tenants.code) enforced here
        except IntegrityError as exc:
            # Concurrent same-slug signup: step 1's pre-check and this INSERT are
            # NOT atomic, so two racing registrations can both pass step 1 and then
            # collide on the unique `tenants.code` constraint here. The DB correctly
            # prevents the duplicate (only one row is created); surface the same clean
            # 409 the pre-check returns instead of a raw 500 (FIX-030 —
            # AD-Register-Concurrent-Slug-Race from the 2026-06-06 drive-through audit).
            raise TenantSlugTakenError() from exc

        # 3. Switch to the new tenant's RLS context for the user/role writes
        #    (users + roles are tenant-scoped; tenants is the RLS-free root).
        await _set_tenant(db, str(tenant.id))

        # 4. Seed the founding "admin" role (first real Role-creation in the codebase;
        #    seed_default_roles in provisioning.py is still a stub).
        role = Role(
            tenant_id=tenant.id,
            code=FOUNDING_ADMIN_ROLE_CODE,
            display_name="Admin",
            description="Founding tenant administrator (seeded at registration).",
        )
        db.add(role)
        await db.flush()  # obtain role.id

        # 5. Create the founding user (no password — OIDC-first; no external_id yet).
        user = User(
            tenant_id=tenant.id,
            email=email,
            display_name=full_name,
            status="active",
        )
        db.add(user)
        await db.flush()  # obtain user.id

        # 6. Grant the admin role to the founding user (self-grant).
        db.add(UserRole(user_id=user.id, role_id=role.id, granted_by=user.id))

        # 7. Audit the registration (WORM chain, under the tenant context).
        await append_audit(
            db,
            tenant_id=tenant.id,
            operation="tenant_registered",
            resource_type="tenant",
            resource_id=str(tenant.id),
            operation_data={
                "tenant_code": tenant_slug,
                "email": email,
                "requested_plan": requested_plan,
            },
            user_id=user.id,
            operation_result="success",
        )
        await db.flush()
        return RegistrationResult(tenant=tenant, user=user)


async def _set_tenant(db: AsyncSession, tenant_id: str) -> None:
    """SET LOCAL app.tenant_id for the current transaction (RLS context).

    set_config(...) is the bind-param-compatible function form of SET LOCAL
    (asyncpg rejects params on the SET utility statement); is_local=true →
    txn-scoped. Mirrors invites.py + middleware/tenant_context.py.
    """
    await db.execute(text("SELECT set_config('app.tenant_id', :tid, true)"), {"tid": tenant_id})


# Module-level singleton (stateless; db passed per call). Lenient — no lifespan
# wiring required (mirrors 57.85 invites / 57.86 credentials; avoids the 57.84
# Day-3 module-singleton test-leak class).
_service: RegistrationService | None = None


def get_registration_service() -> RegistrationService:
    """FastAPI Depends accessor (strict — raises if uninitialised)."""
    if _service is None:
        raise RuntimeError(
            "RegistrationService not initialised; call set_registration_service() "
            "at app startup or in a test fixture"
        )
    return _service


def maybe_get_registration_service() -> RegistrationService | None:
    """Lenient accessor — returns None if uninitialised (endpoint falls back)."""
    return _service


def set_registration_service(service: RegistrationService | None) -> None:
    """Install singleton (app startup or tests fixture)."""
    global _service
    _service = service


__all__ = [
    "RegistrationService",
    "RegistrationResult",
    "RegistrationError",
    "TenantSlugTakenError",
    "FOUNDING_ADMIN_ROLE_CODE",
    "get_registration_service",
    "maybe_get_registration_service",
    "set_registration_service",
]
