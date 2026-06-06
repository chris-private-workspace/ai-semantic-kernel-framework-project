"""
File: backend/src/api/v1/invites.py
Purpose: IAM Block B invites endpoints — admin create + guest view/accept.
Category: API / v1 (platform_layer.identity — C-12 IAM Block B invites leg)
Scope: Sprint 57.85 / US-1 + US-2 + US-3

Description:
    Three endpoints over InvitesService:
      - POST /admin/tenants/{tenant_id}/invites  (admin RBAC + own-tenant guard) —
        create a pending invite for (email, role); returns the raw token ONCE.
      - GET  /invites/{token}                    (guest, exempt path) — invite
        display metadata (tenant / inviter / role / expiresIn); 404 / 410.
      - POST /invites/{token}/accept             (guest, exempt path) — create the
        User + grant the role + consume the invite; 200 / 404 / 410 / 409.

    The guest GET/accept run EXEMPT from TenantContextMiddleware (the caller has no
    JWT); InvitesService manages the RLS tenant context internally (sentinel token
    lookup → invite's own tenant for writes). The admin create is gated by
    require_admin_platform_role (platform admins, cross-tenant by design); the
    invite is scoped to the PATH tenant_id and RLS-isolated.

    The accept request carries a `password` (the shipped frontend contract) but it
    is intentionally NOT stored this sprint — local-credential storage is a
    follow-up slice (57.86). See platform_layer/identity/invites.py docstring.

Key Components:
    - router: APIRouter (mounted at /api/v1)
    - InviteCreateRequest/Response, InviteMetadataResponse, InviteAcceptRequest/Response

Created: 2026-06-06 (Sprint 57.85)

Modification History:
    - 2026-06-06: Initial creation (Sprint 57.85 / US-1..US-3)

Related:
    - platform_layer/identity/invites.py — InvitesService + typed errors
    - platform_layer/identity/auth.py — require_admin_platform_role (platform-admin gate)
    - middleware/tenant_context.py — EXEMPT_PATH_PREFIXES (+ /api/v1/invites)
    - frontend/src/pages/auth/invite/index.tsx — InviteMetadata contract
    - sprint-57-85-plan.md §3.3
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.session import get_db_session
from platform_layer.identity.auth import require_admin_platform_role
from platform_layer.identity.invites import (
    InviteError,
    InvitesService,
    maybe_get_invites_service,
)

router = APIRouter(tags=["invites"])


# === Request / response models ===
class InviteCreateRequest(BaseModel):
    """Admin invite-create body."""

    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=256)
    role_id: UUID
    ttl_hours: int | None = Field(default=None, ge=1, le=720)


class InviteCreateResponse(BaseModel):
    """Admin invite-create response (raw token shown ONCE)."""

    invite_id: UUID
    token: str
    expires_at: datetime


class InviteMetadataResponse(BaseModel):
    """Guest invite metadata (matches frontend InviteMetadata).

    serialization_alias → JSON output uses camelCase invitedBy / expiresIn
    (FastAPI response_model_by_alias=True) while construction stays snake_case.
    """

    tenant: str
    invited_by: str = Field(serialization_alias="invitedBy")
    role: str
    expires_in: str = Field(serialization_alias="expiresIn")


class InviteAcceptRequest(BaseModel):
    """Guest accept body. `password` is accepted but NOT stored this sprint."""

    model_config = ConfigDict(extra="forbid")

    full_name: str = Field(min_length=1, max_length=256)
    password: str = Field(min_length=1)


class InviteAcceptResponse(BaseModel):
    """Guest accept response."""

    ok: bool
    user_id: UUID


def _service() -> InvitesService:
    # Lenient singleton (stateless service) — avoids a lifespan-wired singleton
    # that could leak into test event loops (Sprint 57.84 Day-3 regression).
    return maybe_get_invites_service() or InvitesService()


def _format_expires_in(expires_at: datetime) -> str:
    """Human 'expiresIn' string from an absolute expiry."""
    delta = expires_at - datetime.now(timezone.utc)
    seconds = int(delta.total_seconds())
    if seconds <= 0:
        return "expired"
    days = seconds // 86400
    if days >= 1:
        return f"{days} day" + ("s" if days != 1 else "")
    hours = seconds // 3600
    if hours >= 1:
        return f"{hours} hour" + ("s" if hours != 1 else "")
    minutes = max(1, seconds // 60)
    return f"{minutes} minute" + ("s" if minutes != 1 else "")


# === Endpoints ===
@router.post(
    "/admin/tenants/{tenant_id}/invites",
    response_model=InviteCreateResponse,
    status_code=201,
)
async def create_invite(
    tenant_id: UUID,
    body: InviteCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    admin_user_id: UUID = Depends(require_admin_platform_role),
) -> InviteCreateResponse:
    """Create a pending invite (platform-admin RBAC; invite scoped to the path tenant)."""
    # require_admin_platform_role gates to platform admins (admin / platform_admin),
    # who are cross-tenant by design (codebase RBAC model + admin/tenants.py
    # convention). The invite is scoped to the PATH tenant_id and RLS-isolated.
    try:
        invite, raw_token = await _service().create(
            db,
            tenant_id=tenant_id,
            inviter_user_id=admin_user_id,
            email=body.email,
            role_id=body.role_id,
            ttl_hours=body.ttl_hours,
        )
    except InviteError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return InviteCreateResponse(invite_id=invite.id, token=raw_token, expires_at=invite.expires_at)


@router.get("/invites/{token}", response_model=InviteMetadataResponse)
async def get_invite(
    token: str,
    db: AsyncSession = Depends(get_db_session),
) -> InviteMetadataResponse:
    """Return invite display metadata by token (guest, exempt path)."""
    try:
        meta = await _service().get_metadata(db, token)
    except InviteError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return InviteMetadataResponse(
        tenant=meta.tenant,
        invited_by=meta.invited_by,
        role=meta.role,
        expires_in=_format_expires_in(meta.expires_at),
    )


@router.post("/invites/{token}/accept", response_model=InviteAcceptResponse)
async def accept_invite(
    token: str,
    body: InviteAcceptRequest,
    db: AsyncSession = Depends(get_db_session),
) -> InviteAcceptResponse:
    """Accept an invite: create the user + grant the role (guest, exempt path)."""
    try:
        user = await _service().accept(db, token, full_name=body.full_name)
    except InviteError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return InviteAcceptResponse(ok=True, user_id=user.id)


__all__ = ["router"]
