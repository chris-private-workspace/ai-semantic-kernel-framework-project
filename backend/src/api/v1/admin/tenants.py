"""
File: backend/src/api/v1/admin/tenants.py
Purpose: System-admin tenant lifecycle + settings CRUD endpoints — provisioning + onboarding + read/update API surface.
Category: API Layer / Admin (Sprint 56.1 SaaS Stage 1 + Sprint 57.3 Tenant Settings)
Scope: Sprint 56.1 Day 1 (US-1) + Day 3 (US-3 part 2 onboarding) + Sprint 57.3 Day 1+2 (US-1 GET + US-2 PATCH)
Owner: api/v1/admin owner

Description:
    Sprint 56.1 Day 1 (US-1):
        POST /api/v1/admin/tenants — create new tenant + run ProvisioningWorkflow.

    Sprint 56.1 Day 3 (US-3 part 2):
        GET  /api/v1/admin/tenants/{id}/onboarding-status — snapshot
        POST /api/v1/admin/tenants/{id}/onboarding/{step} — advance step
            with auto-transition to ACTIVE when all 6 steps complete + health
            check passes.

    Sprint 56.2 Day 1 (US-4 — closes AD-AdminAuth-1): the 56.1 stub
    `require_admin_token` (X-Admin-Token header against env var) is replaced
    by `require_admin_platform_role` (JWT-claim-based RBAC, mirrors 53.5
    require_audit_role / require_approver_role pattern). All 3 admin
    endpoints now check that the caller's JWT 'roles' claim includes "admin"
    or "platform_admin". `tenant_admin` role is intentionally excluded —
    tenant-scoped admins cannot create / suspend / archive other tenants.

    Sprint 57.3 Day 1+2 (US-1 + US-2 — closes Day 0 D1 RED finding via
    Option B pivot user-confirmed 2026-05-07):
        GET   /api/v1/admin/tenants/{tenant_id} — read full tenant entity
            (10-field TenantResponse mirroring ORM fields).
        PATCH /api/v1/admin/tenants/{tenant_id} — partial update for
            display_name + meta_data only (extra='forbid' rejects other
            fields); writes audit chain entry on actual change.

    D11 (carryover): no Cat 12 obs span — structured logging only (consistent
    with provisioning.py D11 / chat router L121 D4).

Key Components:
    - TenantCreateRequest / TenantCreateResponse Pydantic schemas
    - OnboardingStatusResponse / OnboardingAdvanceRequest schemas (Day 3)
    - TenantResponse / TenantUpdateRequest schemas (Sprint 57.3)
    - router: APIRouter prefix /admin/tenants
    - create_tenant / get_onboarding_status / advance_onboarding_step
    - get_tenant / update_tenant (Sprint 57.3)

Created: 2026-05-06 (Sprint 56.1 Day 1)
Last Modified: 2026-05-07

Modification History:
    - 2026-05-07: Sprint 57.3 Day 1 — add GET /{tenant_id} + TenantResponse (US-1 closes D1)
    - 2026-05-06: Sprint 56.2 Day 1 — RBAC dep replaces token stub (closes AD-AdminAuth-1)
    - 2026-05-06: Sprint 56.1 Day 4 CI — replace EmailStr with regex (avoid email-validator dep)
    - 2026-05-06: Sprint 56.1 Day 3 — onboarding-status GET + onboarding/{step} POST (US-3 part 2)
    - 2026-05-06: Initial creation (Sprint 56.1 Day 1 / US-1)

Related:
    - platform_layer/tenant/provisioning.py — ProvisioningWorkflow
    - platform_layer/tenant/lifecycle.py — TenantLifecycle
    - platform_layer/tenant/onboarding.py — OnboardingTracker (Day 2)
    - platform_layer/tenant/health_check.py — TenantHealthChecker (Day 3)
    - infrastructure/db/models/identity.py — Tenant ORM
    - sprint-56-1-plan.md §US-1 + §US-3 + §Architecture
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.models.identity import Tenant, TenantPlan, TenantState
from infrastructure.db.session import get_db_session
from platform_layer.identity.auth import require_admin_platform_role
from platform_layer.tenant.health_check import TenantHealthChecker
from platform_layer.tenant.lifecycle import IllegalTransitionError, TenantLifecycle
from platform_layer.tenant.onboarding import (
    VALID_STEPS,
    InvalidOnboardingStepError,
    OnboardingTracker,
)
from platform_layer.tenant.provisioning import ProvisioningError, ProvisioningWorkflow

router = APIRouter(prefix="/admin/tenants", tags=["admin", "tenants"])

# Cheap email regex (RFC 5322-lite). We avoid pydantic's `EmailStr` so we
# don't need the optional `email-validator` extra in CI / lean prod images.
_EMAIL_PATTERN = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"


class TenantCreateRequest(BaseModel):
    code: str = Field(min_length=2, max_length=64, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    display_name: str = Field(min_length=1, max_length=256)
    plan: TenantPlan = TenantPlan.ENTERPRISE
    admin_email: str = Field(pattern=_EMAIL_PATTERN, max_length=320)


class TenantCreateResponse(BaseModel):
    tenant_id: UUID
    code: str
    state: TenantState
    estimated_ready_in_seconds: int


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=TenantCreateResponse,
    dependencies=[Depends(require_admin_platform_role)],
)
async def create_tenant(
    payload: TenantCreateRequest,
    db: AsyncSession = Depends(get_db_session),
) -> TenantCreateResponse:
    """Create new tenant + run ProvisioningWorkflow synchronously.

    Returns 201 with tenant_id once all 7 stub steps complete (state=PROVISIONING).
    Tenant transitions to ACTIVE only after onboarding 6-step + health check
    (Sprint 56.1 US-3 endpoints; Day 3 additions).
    """
    # admin_email is captured into metadata for the create_first_admin_user
    # step (deferred to Phase 56.x per D12).
    tenant = Tenant(
        code=payload.code,
        display_name=payload.display_name,
        plan=payload.plan,
        meta_data={"admin_email": str(payload.admin_email)},
    )
    db.add(tenant)
    await db.flush()

    workflow = ProvisioningWorkflow(db)
    try:
        await workflow.run(tenant.id)
    except ProvisioningError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"provisioning failed at step {exc.step}: {exc.original}",
        ) from exc

    return TenantCreateResponse(
        tenant_id=tenant.id,
        code=tenant.code,
        state=tenant.state,
        estimated_ready_in_seconds=60,
    )


# ---------------------------------------------------------------------
# Day 3 (US-3 part 2): Onboarding endpoints
# ---------------------------------------------------------------------


class OnboardingStatusResponse(BaseModel):
    tenant_id: UUID
    state: TenantState
    completed_steps: list[str]
    pending_steps: list[str]
    step_records: dict[str, Any]
    is_complete: bool


class OnboardingAdvanceRequest(BaseModel):
    payload: dict[str, Any] = Field(default_factory=dict)


class OnboardingAdvanceResponse(BaseModel):
    tenant_id: UUID
    step: str
    state: TenantState
    is_complete: bool
    health_check: dict[str, Any] | None = None
    transitioned_to_active: bool = False


async def _load_tenant_or_404(db: AsyncSession, tenant_id: UUID) -> Tenant:
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"tenant {tenant_id} not found"
        )
    return tenant


@router.get(
    "/{tenant_id}/onboarding-status",
    response_model=OnboardingStatusResponse,
    dependencies=[Depends(require_admin_platform_role)],
)
async def get_onboarding_status(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> OnboardingStatusResponse:
    """Snapshot of completed + pending steps + tenant state."""
    tenant = await _load_tenant_or_404(db, tenant_id)
    tracker = OnboardingTracker(db)
    snapshot = await tracker.get_progress(tenant_id)
    is_complete = await tracker.is_complete(tenant_id)
    return OnboardingStatusResponse(
        tenant_id=tenant_id,
        state=tenant.state,
        completed_steps=snapshot["completed_steps"],
        pending_steps=snapshot["pending_steps"],
        step_records=snapshot["step_records"],
        is_complete=is_complete,
    )


@router.post(
    "/{tenant_id}/onboarding/{step}",
    response_model=OnboardingAdvanceResponse,
    dependencies=[Depends(require_admin_platform_role)],
)
async def advance_onboarding_step(
    tenant_id: UUID,
    step: str,
    body: OnboardingAdvanceRequest,
    db: AsyncSession = Depends(get_db_session),
) -> OnboardingAdvanceResponse:
    """Advance a single onboarding step.

    When the final step (`health_check`) completes AND the
    `TenantHealthChecker` 6-point probe passes, auto-transitions the tenant
    from PROVISIONING → ACTIVE via `TenantLifecycle.transition`. Other steps
    just record progress + return current state.

    Step name in path is validated against `VALID_STEPS`; unknown steps
    return 400 (not 422 — keeps the FastAPI validation surface for body).
    """
    if step not in VALID_STEPS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"unknown onboarding step '{step}'; valid: {list(VALID_STEPS)}",
        )

    tenant = await _load_tenant_or_404(db, tenant_id)
    tracker = OnboardingTracker(db)

    try:
        await tracker.advance(tenant_id, step, payload=body.payload)
    except InvalidOnboardingStepError as exc:
        # Defensive — should already have been caught by the path-level
        # check above; re-map for safety.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    is_complete = await tracker.is_complete(tenant_id)

    health_report_dict: dict[str, Any] | None = None
    transitioned = False

    if is_complete:
        # Run the 6-point health probe; auto-transition only when all green.
        # D24: chat_call / redis_client injection deferred to production
        # wiring (Phase 56.x); test paths inject mocks directly.
        checker = TenantHealthChecker(db)
        report = await checker.run(tenant_id)
        health_report_dict = report.as_dict()
        if report.all_passed and tenant.state == TenantState.PROVISIONING:
            lifecycle = TenantLifecycle(db)
            try:
                await lifecycle.transition(tenant_id, TenantState.ACTIVE)
                transitioned = True
                # Refresh state for response.
                await db.refresh(tenant)
            except IllegalTransitionError:
                # Already moved on — leave state as-is.
                transitioned = False

    return OnboardingAdvanceResponse(
        tenant_id=tenant_id,
        step=step,
        state=tenant.state,
        is_complete=is_complete,
        health_check=health_report_dict,
        transitioned_to_active=transitioned,
    )


# ---------------------------------------------------------------------
# Sprint 57.3 Day 1+2 (US-1 + US-2): Tenant settings read + partial update
# Closes Day 0 D1 RED finding via Option B pivot user-confirmed 2026-05-07.
# ---------------------------------------------------------------------


class TenantResponse(BaseModel):
    """Read-only response for GET /admin/tenants/{tenant_id}.

    Mirrors all 10 ORM fields of the Tenant model. Used as response_model
    for both GET (US-1) and PATCH (US-2 — caller sees post-update state).
    """

    id: UUID
    code: str
    display_name: str
    state: TenantState
    plan: TenantPlan
    provisioning_progress: dict[str, Any]
    onboarding_progress: dict[str, Any]
    meta_data: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


@router.get(
    "/{tenant_id}",
    response_model=TenantResponse,
    dependencies=[Depends(require_admin_platform_role)],
)
async def get_tenant(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> TenantResponse:
    """Return full tenant entity (10 fields) given tenant_id.

    Auth: require_admin_platform_role (super-admin only). 404 if tenant
    not found via _load_tenant_or_404.
    """
    tenant = await _load_tenant_or_404(db, tenant_id)
    return TenantResponse.model_validate(tenant)
