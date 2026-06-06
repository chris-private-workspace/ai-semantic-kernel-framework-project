"""
File: backend/src/api/v1/tenants.py
Purpose: IAM Block B self-service tenant registration endpoint (public, exempt).
Category: API / v1 (platform_layer.identity — C-12 IAM Block B registration leg)
Scope: Sprint 57.87 / US-1 + US-3 + US-4

Description:
    One public endpoint over RegistrationService:
      - POST /tenants/register  (guest, exempt path) — create a new tenant + its
        first admin user + seeded admin role + audit; returns 201 {tenant, user}.
        409 on a duplicate slug; 422 on an invalid slug pattern.

    The route runs EXEMPT from TenantContextMiddleware (the caller has no JWT yet);
    RegistrationService manages the RLS tenant context internally (tenants is the
    RLS-free root; the user/role writes run under the new tenant's context). No
    session/cookie is issued — the shipped register wizard redirects to the OIDC
    /auth/callback to log in.

    NB this is the PUBLIC tenants router; admin tenant CRUD lives in
    api/v1/admin/tenants.py (require_admin_platform_role). Only /tenants/register
    is exposed here + exempted.

Key Components:
    - router: APIRouter(prefix="/tenants") (mounted at /api/v1)
    - TenantRegisterRequest / TenantRegisterResponse (+ nested tenant/user out)

Created: 2026-06-06 (Sprint 57.87)
Last Modified: 2026-06-06

Modification History:
    - 2026-06-06: Initial creation (Sprint 57.87 / US-1 + US-3 + US-4)

Related:
    - platform_layer/identity/registration.py — RegistrationService + typed errors
    - middleware/tenant_context.py — EXEMPT_PATH_PREFIXES (+ /api/v1/tenants/register)
    - frontend/src/pages/auth/register/index.tsx — register wizard (the consumer)
    - sprint-57-87-plan.md §3.2
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.session import get_db_session
from platform_layer.identity.registration import (
    RegistrationError,
    RegistrationService,
    maybe_get_registration_service,
)

router = APIRouter(prefix="/tenants", tags=["tenants"])


# === Request / response models ===
class TenantRegisterRequest(BaseModel):
    """Self-service registration body (matches the register wizard payload).

    extra fields are ignored (not forbidden) to stay tolerant of the shipped
    frontend contract. `tenant_slug` is the tenant `code` (pattern mirrors
    admin/tenants.py TenantCreateRequest). `plan`/`size` are the requested tier +
    company size — stored in tenant.meta_data (TenantPlan only has ENTERPRISE today).
    """

    email: str = Field(min_length=3, max_length=256)
    full_name: str = Field(min_length=1, max_length=256)
    company_name: str = Field(min_length=1, max_length=256)
    tenant_slug: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    region: str = Field(default="global", max_length=32)
    plan: str = Field(min_length=1, max_length=32)
    size: str | None = Field(default=None, max_length=32)


class _TenantOut(BaseModel):
    id: UUID
    code: str
    display_name: str
    state: str


class _UserOut(BaseModel):
    id: UUID
    email: str
    display_name: str | None  # User.display_name is nullable (register always sets it)


class TenantRegisterResponse(BaseModel):
    """Registration response — the created tenant + founding user."""

    tenant: _TenantOut
    user: _UserOut


def _service() -> RegistrationService:
    # Lenient singleton (stateless service) — avoids a lifespan-wired singleton
    # that could leak into test event loops (Sprint 57.84 Day-3 regression).
    return maybe_get_registration_service() or RegistrationService()


# === Endpoint ===
@router.post("/register", response_model=TenantRegisterResponse, status_code=201)
async def register_tenant(
    body: TenantRegisterRequest,
    db: AsyncSession = Depends(get_db_session),
) -> TenantRegisterResponse:
    """Register a new tenant + founding admin user (public, exempt path).

    409 on a duplicate slug (generic — no enumeration). No session is issued; the
    frontend redirects to the OIDC /auth/callback to log in.
    """
    try:
        result = await _service().register(
            db,
            email=body.email,
            full_name=body.full_name,
            company_name=body.company_name,
            tenant_slug=body.tenant_slug,
            region=body.region,
            requested_plan=body.plan,
            company_size=body.size,
        )
    except RegistrationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    tenant, user = result.tenant, result.user
    return TenantRegisterResponse(
        tenant=_TenantOut(
            id=tenant.id,
            code=tenant.code,
            display_name=tenant.display_name,
            state=tenant.state.value,
        ),
        user=_UserOut(id=user.id, email=user.email, display_name=user.display_name),
    )


__all__ = ["router"]
