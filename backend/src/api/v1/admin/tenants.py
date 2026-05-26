"""
File: backend/src/api/v1/admin/tenants.py
Purpose: System-admin tenant lifecycle + settings CRUD endpoints.
Category: API Layer / Admin (Sprint 56.1 + Sprint 57.3)
Scope: Sprint 56.1 Day 1+3 (provisioning + onboarding) + Sprint 57.3 Day 1+2 (GET + PATCH)
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
Last Modified: 2026-05-10

Modification History:
    - 2026-05-26: Sprint 57.47 Day 1 — LIST 7→12 + region filter + members GET (AD-AdminT-Ext)
    - 2026-05-26: Sprint 57.46 Day 1 — +5 SaaS settings fields (closes AD-TenantSettings-Schema-Ext)
    - 2026-05-10: Sprint 57.13 US-A3 — /{tenant_id} dep → require_tenant_match_or_platform_admin
    - 2026-05-07: Sprint 57.4 — add GET "" list endpoint (US-1 closes D1)
    - 2026-05-07: Sprint 57.3 Day 2 — add PATCH /{id} + TenantUpdateRequest + audit chain (US-2)
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

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.audit_helper import append_audit
from infrastructure.db.models.identity import Tenant, TenantPlan, TenantState, User
from infrastructure.db.session import get_db_session
from platform_layer.identity.auth import (
    require_admin_platform_role,
    require_tenant_match_or_platform_admin,
)
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
# Sprint 57.4 (US-1): List endpoint with filter + pagination
# ---------------------------------------------------------------------


class TenantListItem(BaseModel):
    """Lightweight subset of Tenant ORM for paginated list responses.

    Excludes provisioning_progress / onboarding_progress / meta_data
    JSONB fields to keep list payload small; clients fetch full detail
    via GET /{tenant_id} (Sprint 57.3).
    """

    id: UUID
    code: str
    display_name: str
    state: TenantState
    plan: TenantPlan
    region: str
    locale: str
    retention_days: int
    sso_enabled: bool
    seats: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TenantListResponse(BaseModel):
    """Paginated list response wrapper (Sprint 57.4 US-1)."""

    items: list[TenantListItem]
    total: int
    limit: int
    offset: int


@router.get(
    "",
    response_model=TenantListResponse,
    dependencies=[Depends(require_admin_platform_role)],
)
async def list_tenants(
    state: TenantState | None = Query(None),
    plan: TenantPlan | None = Query(None),
    region: str | None = Query(None, max_length=32),
    search: str | None = Query(None, max_length=128),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session),
) -> TenantListResponse:
    """List tenants with optional filter by state / plan + ILIKE search.

    Sprint 57.4 (US-1) — closes plan-time D1 RED finding (backend was
    missing a list endpoint at the entity prefix). Powers the Admin
    Tenants Console frontend page (US-2..US-5).

    Auth: super-admin only via require_admin_platform_role.
    Order: created_at DESC (newest first).
    """
    base_stmt = select(Tenant)
    if state is not None:
        base_stmt = base_stmt.where(Tenant.state == state)
    if plan is not None:
        base_stmt = base_stmt.where(Tenant.plan == plan)
    if region is not None:
        base_stmt = base_stmt.where(Tenant.region == region)
    if search is not None:
        like = f"%{search}%"
        base_stmt = base_stmt.where(or_(Tenant.code.ilike(like), Tenant.display_name.ilike(like)))

    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total_raw = (await db.execute(count_stmt)).scalar()
    total = int(total_raw or 0)

    page_stmt = (
        base_stmt.order_by(Tenant.created_at.desc(), Tenant.id.desc()).limit(limit).offset(offset)
    )
    rows = (await db.execute(page_stmt)).scalars().all()

    return TenantListResponse(
        items=[TenantListItem.model_validate(t) for t in rows],
        total=total,
        limit=limit,
        offset=offset,
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

    Mirrors all 15 ORM fields of the Tenant model (10 baseline + 5 SaaS settings
    added Sprint 57.46). Used as response_model for both GET (US-1) and PATCH
    (US-2 — caller sees post-update state).
    """

    id: UUID
    code: str
    display_name: str
    state: TenantState
    plan: TenantPlan
    provisioning_progress: dict[str, Any]
    onboarding_progress: dict[str, Any]
    meta_data: dict[str, Any]
    # Sprint 57.46 Day 1 — SaaS settings extension
    region: str
    locale: str
    retention_days: int
    sso_enabled: bool
    seats: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


@router.get(
    "/{tenant_id}",
    response_model=TenantResponse,
    dependencies=[Depends(require_tenant_match_or_platform_admin)],
)
async def get_tenant(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> TenantResponse:
    """Return full tenant entity (10 fields) given tenant_id.

    Auth: require_tenant_match_or_platform_admin (Sprint 57.13 US-A3) —
    platform admins read any tenant; a regular user reads only their own
    (the tenant-settings page derives tenant_id from the session). 404 if
    tenant not found via _load_tenant_or_404.
    """
    tenant = await _load_tenant_or_404(db, tenant_id)
    return TenantResponse.model_validate(tenant)


_REGION_VALUES = ("apac", "emea", "americas", "global")
# BCP-47 locale code regex: 2-3 alpha lang + optional 2-3 alpha/digit region
# (e.g. "en", "en-US", "zh-Hant", "zh-CN"). Conservative — covers the cases
# we serve; broader BCP-47 tags can be added if real usage demands them.
_LOCALE_PATTERN = r"^[A-Za-z]{2,3}(-[A-Za-z0-9]{2,4})?$"


class TenantUpdateRequest(BaseModel):
    """Partial update request for PATCH /admin/tenants/{tenant_id}.

    Editable fields (Sprint 57.46 extends 2 → 7):
        - display_name (Sprint 57.3 baseline)
        - meta_data (Sprint 57.3 baseline)
        - region (Sprint 57.46 — apac / emea / americas / global)
        - locale (Sprint 57.46 — BCP-47 conservative regex)
        - retention_days (Sprint 57.46 — 1-3650 / 10 years max)
        - sso_enabled (Sprint 57.46 — bool)
        - seats (Sprint 57.46 — ≥1)

    Pydantic extra='forbid' still rejects any other field with 422 (per US-2
    immutable field guard for id / code / state / plan / created_at /
    updated_at / progress fields).

    State transitions go through TenantLifecycle.transition (per
    VALID_TRANSITIONS lifecycle.py:63); plan upgrades go through
    PlanLoader workflow (56.1) — neither belongs here.
    """

    display_name: str | None = Field(None, min_length=1, max_length=256)
    meta_data: dict[str, Any] | None = None
    region: str | None = Field(None, max_length=32)
    locale: str | None = Field(None, max_length=16, pattern=_LOCALE_PATTERN)
    retention_days: int | None = Field(None, ge=1, le=3650)
    sso_enabled: bool | None = None
    seats: int | None = Field(None, ge=1)

    model_config = ConfigDict(extra="forbid")

    @field_validator("region")
    @classmethod
    def _validate_region(cls, v: str | None) -> str | None:
        """Restrict region to a small whitelist.

        Pydantic Literal would also work, but staying with str|None keeps the
        OpenAPI schema looking like a free-text field (we may extend the set
        in Phase 58+ for APAC sub-regions). Runtime check is sufficient.
        """
        if v is not None and v not in _REGION_VALUES:
            raise ValueError(f"region must be one of {_REGION_VALUES}, got {v!r}")
        return v


@router.patch("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: UUID,
    request: TenantUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
    admin_user_id: UUID = Depends(require_admin_platform_role),
) -> TenantResponse:
    """Partial update for tenant settings (display_name + meta_data only).

    On actual change, writes audit chain entry with operation=
    "tenant_settings_updated" + operation_data containing changed_fields +
    old_values + new_values for full audit trail.

    No-op (no fields changed) short-circuits without audit entry.

    Auth: require_admin_platform_role; admin_user_id captured for audit
    chain user_id field.
    """
    tenant = await _load_tenant_or_404(db, tenant_id)

    changed_fields: list[str] = []
    old_values: dict[str, Any] = {}
    new_values: dict[str, Any] = {}

    if request.display_name is not None and request.display_name != tenant.display_name:
        old_values["display_name"] = tenant.display_name
        new_values["display_name"] = request.display_name
        tenant.display_name = request.display_name
        changed_fields.append("display_name")

    if request.meta_data is not None and request.meta_data != tenant.meta_data:
        old_values["meta_data"] = tenant.meta_data
        new_values["meta_data"] = request.meta_data
        tenant.meta_data = request.meta_data
        changed_fields.append("meta_data")

    # Sprint 57.46 Day 1 — 5 SaaS settings fields (closes
    # AD-TenantSettings-Backend-Schema-Extension)
    if request.region is not None and request.region != tenant.region:
        old_values["region"] = tenant.region
        new_values["region"] = request.region
        tenant.region = request.region
        changed_fields.append("region")

    if request.locale is not None and request.locale != tenant.locale:
        old_values["locale"] = tenant.locale
        new_values["locale"] = request.locale
        tenant.locale = request.locale
        changed_fields.append("locale")

    if request.retention_days is not None and request.retention_days != tenant.retention_days:
        old_values["retention_days"] = tenant.retention_days
        new_values["retention_days"] = request.retention_days
        tenant.retention_days = request.retention_days
        changed_fields.append("retention_days")

    if request.sso_enabled is not None and request.sso_enabled != tenant.sso_enabled:
        old_values["sso_enabled"] = tenant.sso_enabled
        new_values["sso_enabled"] = request.sso_enabled
        tenant.sso_enabled = request.sso_enabled
        changed_fields.append("sso_enabled")

    if request.seats is not None and request.seats != tenant.seats:
        old_values["seats"] = tenant.seats
        new_values["seats"] = request.seats
        tenant.seats = request.seats
        changed_fields.append("seats")

    if not changed_fields:
        # No-op — return current state without writing audit entry.
        return TenantResponse.model_validate(tenant)

    await db.flush()  # Bump updated_at via SQLAlchemy onupdate.

    # D11 (Day 2): append_audit signature uses operation/operation_data/user_id
    # (not action/details/actor_user_id as plan-time assumed).
    await append_audit(
        db,
        tenant_id=tenant_id,
        operation="tenant_settings_updated",
        resource_type="tenant",
        resource_id=str(tenant_id),
        operation_data={
            "changed_fields": changed_fields,
            "old_values": old_values,
            "new_values": new_values,
        },
        user_id=admin_user_id,
        operation_result="success",
    )
    await db.commit()

    return TenantResponse.model_validate(tenant)


# =====================================================================
# Sprint 57.47 Track B (US-3 cheapest fixture-only tab) — MEMBERS GET
# =====================================================================
class TenantMemberItem(BaseModel):
    """Tenant member row projected from User ORM for /tenant-settings Members tab.

    Sprint 57.47 Track B — closes cheapest fixture-only TenantSettings tab
    (~1.5-2 hr; User ORM already has all needed fields via TenantScopedMixin).
    Fixture shape in `frontend/src/features/tenant-settings/_fixtures.ts` Member:
    `{ n: display_name, e: email, r: role, a: last_active_relative, c: capacity_pct }`.
    For backend we expose the raw User fields; frontend maps to its shape.
    Role + last-active + capacity are NOT in the current User ORM — exposed as
    `null` here for Phase 58+ to wire when role/activity tracking lands.
    """

    id: UUID
    email: str
    display_name: str | None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TenantMemberListResponse(BaseModel):
    """Paginated response for tenant member list."""

    items: list[TenantMemberItem]
    total: int
    limit: int
    offset: int


@router.get(
    "/{tenant_id}/members",
    response_model=TenantMemberListResponse,
    dependencies=[Depends(require_tenant_match_or_platform_admin)],
)
async def list_tenant_members(
    tenant_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session),
) -> TenantMemberListResponse:
    """List Users in this tenant (Sprint 57.47 Track B Day 1 stretch).

    Auth: require_tenant_match_or_platform_admin (mirrors GET /{tenant_id}
    pattern Sprint 57.13 US-A3) — platform admins read any tenant; a regular
    user reads only their own tenant's members.

    Order: created_at DESC (newest first).

    Returns 5 fields per User (id/email/display_name/status/created_at).
    role/last_active/capacity_pct columns in mockup fixture are NOT in the
    current User ORM; frontend will display placeholders or hide those
    columns until Phase 58+ adds role/activity tracking.
    """
    # Confirm tenant exists (404 else, consistent with GET /{tenant_id} pattern)
    await _load_tenant_or_404(db, tenant_id)

    base_stmt = select(User).where(User.tenant_id == tenant_id)
    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total_raw = (await db.execute(count_stmt)).scalar()
    total = int(total_raw or 0)

    page_stmt = (
        base_stmt.order_by(User.created_at.desc(), User.id.desc()).limit(limit).offset(offset)
    )
    rows = (await db.execute(page_stmt)).scalars().all()

    return TenantMemberListResponse(
        items=[TenantMemberItem.model_validate(u) for u in rows],
        total=total,
        limit=limit,
        offset=offset,
    )
