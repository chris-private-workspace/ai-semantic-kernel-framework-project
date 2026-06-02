"""
File: backend/src/api/v1/admin/agents.py
Purpose: Admin CRUD API for per-tenant AgentSpec definitions (the agent_catalog table).
Category: API Layer / Admin (Sprint 57.70 Stage-1b — per-tenant agent-spec catalog)
Scope: Phase 57 / Sprint 57.70 Stage-1b

Description:
    Platform-admin CRUD over a tenant's AgentSpec definitions (the rows backing
    Cat 11 HANDOFF persona resolution + the Subagent Registry concept). A
    sub-resource of a tenant, mirroring api/v1/admin/tenants.py conventions:

        GET    /api/v1/admin/tenants/{tenant_id}/agents             — list
        POST   /api/v1/admin/tenants/{tenant_id}/agents             — create (201)
        PUT    /api/v1/admin/tenants/{tenant_id}/agents/{agent_id}  — partial update
        DELETE /api/v1/admin/tenants/{tenant_id}/agents/{agent_id}  — delete (204)

    Auth: require_admin_platform_role (any tenant) on the collection +
    require_tenant_match_or_platform_admin on the {tenant_id} path (a regular
    user reaches only their own tenant). All persistence goes through
    AgentCatalogRepository (tenant_id-scoped — multi-tenant 鐵律). Mutations
    write an audit chain entry (operation=agent_catalog.{create,update,delete})
    and commit at the request scope.

    Distinct from /api/v1/subagents (the runtime-invocations STUB,
    AD-Subagent-RealList-Phase58) — this endpoint manages AgentSpec
    *definitions*, a different concept; that STUB is untouched.

Key Components:
    - AgentCreateRequest / AgentUpdateRequest / AgentResponse Pydantic schemas
    - router: APIRouter prefix /admin/tenants
    - list_tenant_agents / create_tenant_agent / update_tenant_agent /
      delete_tenant_agent

Created: 2026-06-02 (Sprint 57.70 Stage-1b)
Last Modified: 2026-06-02

Modification History (newest-first):
    - 2026-06-02: Initial creation (Sprint 57.70 Stage-1b) — agent-catalog admin CRUD

Related:
    - infrastructure/db/models/agent_catalog.py — AgentCatalog ORM
    - infrastructure/db/repositories/agent_catalog_repository.py — DAO
    - api/v1/admin/tenants.py — auth + audit + sub-resource router pattern
    - .claude/rules/multi-tenant-data.md 鐵律 (tenant-scoped queries + RLS)
    - sprint-57-70-plan.md §3.4
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.audit_helper import append_audit
from infrastructure.db.models.identity import Tenant
from infrastructure.db.repositories.agent_catalog_repository import AgentCatalogRepository
from infrastructure.db.session import get_db_session
from platform_layer.identity.auth import (
    require_admin_platform_role,
    require_tenant_match_or_platform_admin,
)

router = APIRouter(prefix="/admin/tenants", tags=["admin", "agents"])


# ---------------------------------------------------------------------
# Pydantic schemas — AgentSpec definition shape (per mockup page-agents.jsx)
# ---------------------------------------------------------------------


class AgentResponse(BaseModel):
    """Full AgentSpec definition row (response for list / create / update)."""

    id: UUID
    tenant_id: UUID
    key: str
    name: str
    model: str | None
    system_prompt: str
    allowed_modes: list[str]
    status: str
    meta_data: dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentCreateRequest(BaseModel):
    """Create payload for a tenant's AgentSpec definition."""

    model_config = ConfigDict(extra="forbid")
    key: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=128)
    system_prompt: str = Field(min_length=1)
    model: str | None = Field(None, max_length=128)
    allowed_modes: list[str] | None = None
    status: str = Field("live", max_length=32)
    meta_data: dict[str, Any] | None = None


class AgentUpdateRequest(BaseModel):
    """Partial update payload (all fields optional; key/id/tenant immutable)."""

    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(None, min_length=1, max_length=128)
    system_prompt: str | None = Field(None, min_length=1)
    model: str | None = Field(None, max_length=128)
    allowed_modes: list[str] | None = None
    status: str | None = Field(None, max_length=32)
    meta_data: dict[str, Any] | None = None
    is_active: bool | None = None


async def _load_tenant_or_404(db: AsyncSession, tenant_id: UUID) -> Tenant:
    """Confirm the tenant exists (404 else); mirrors admin/tenants.py helper."""
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"tenant {tenant_id} not found"
        )
    return tenant


# ---------------------------------------------------------------------
# GET — list a tenant's AgentSpec definitions
# ---------------------------------------------------------------------


@router.get(
    "/{tenant_id}/agents",
    response_model=list[AgentResponse],
    dependencies=[Depends(require_tenant_match_or_platform_admin)],
)
async def list_tenant_agents(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> list[AgentResponse]:
    """List the tenant's AgentSpec definitions (newest first).

    Auth: require_tenant_match_or_platform_admin — platform admins read any
    tenant; a regular user reads only their own. Tenant-scoped via the repo
    (multi-tenant 鐵律) — never returns another tenant's rows.
    """
    await _load_tenant_or_404(db, tenant_id)
    repo = AgentCatalogRepository(db)
    rows = await repo.list_by_tenant(tenant_id=tenant_id)
    return [AgentResponse.model_validate(r) for r in rows]


# ---------------------------------------------------------------------
# POST — create an AgentSpec definition
# ---------------------------------------------------------------------


@router.post(
    "/{tenant_id}/agents",
    status_code=status.HTTP_201_CREATED,
    response_model=AgentResponse,
)
async def create_tenant_agent(
    tenant_id: UUID,
    payload: AgentCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    admin_user_id: UUID = Depends(require_admin_platform_role),
) -> AgentResponse:
    """Create a new AgentSpec definition for the tenant.

    - 401/403 via require_admin_platform_role
    - 404 via _load_tenant_or_404
    - 409 on UNIQUE(tenant_id, key) violation (the role key already exists)
    - 201 with the persisted row; audit chain entry written
      (operation=agent_catalog.create).
    """
    await _load_tenant_or_404(db, tenant_id)
    repo = AgentCatalogRepository(db)
    try:
        agent = await repo.create(
            tenant_id=tenant_id,
            key=payload.key,
            name=payload.name,
            system_prompt=payload.system_prompt,
            model=payload.model,
            allowed_modes=payload.allowed_modes,
            status=payload.status,
            meta_data=payload.meta_data,
        )
    except IntegrityError as exc:
        # UNIQUE(tenant_id, key) → the role key already exists for this tenant.
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"agent key '{payload.key}' already exists for this tenant",
        ) from exc

    await append_audit(
        db,
        tenant_id=tenant_id,
        operation="agent_catalog.create",
        resource_type="agent_catalog",
        resource_id=str(agent.id),
        operation_data={"key": agent.key, "name": agent.name, "status": agent.status},
        user_id=admin_user_id,
        operation_result="success",
    )
    await db.commit()
    await db.refresh(agent)
    return AgentResponse.model_validate(agent)


# ---------------------------------------------------------------------
# PUT — partial update of an AgentSpec definition
# ---------------------------------------------------------------------


@router.put(
    "/{tenant_id}/agents/{agent_id}",
    response_model=AgentResponse,
)
async def update_tenant_agent(
    tenant_id: UUID,
    agent_id: UUID,
    payload: AgentUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
    admin_user_id: UUID = Depends(require_admin_platform_role),
) -> AgentResponse:
    """Partial update of a tenant's AgentSpec definition.

    Only the provided fields change (key / id / tenant_id stay immutable). A
    foreign / missing row (wrong tenant or unknown id) → 404 (the repo UPDATE
    is tenant-scoped, so a cross-tenant id never matches).

    - 401/403 via require_admin_platform_role
    - 404 when the agent is absent in this tenant
    - 200 with the updated row; audit chain entry written
      (operation=agent_catalog.update).
    """
    await _load_tenant_or_404(db, tenant_id)
    repo = AgentCatalogRepository(db)

    # Only forward fields the caller actually supplied (exclude_unset) so an
    # omitted field is left untouched rather than overwritten with its default.
    fields = payload.model_dump(exclude_unset=True)
    if not fields:
        # No fields supplied — return current row (or 404 if absent).
        existing = await repo.get_by_id(tenant_id=tenant_id, agent_id=agent_id)
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"agent {agent_id} not found in tenant",
            )
        return AgentResponse.model_validate(existing)

    agent = await repo.update(tenant_id=tenant_id, agent_id=agent_id, **fields)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"agent {agent_id} not found in tenant",
        )

    await append_audit(
        db,
        tenant_id=tenant_id,
        operation="agent_catalog.update",
        resource_type="agent_catalog",
        resource_id=str(agent_id),
        operation_data={"changed_fields": sorted(fields.keys())},
        user_id=admin_user_id,
        operation_result="success",
    )
    await db.commit()
    await db.refresh(agent)
    return AgentResponse.model_validate(agent)


# ---------------------------------------------------------------------
# DELETE — remove an AgentSpec definition
# ---------------------------------------------------------------------


@router.delete(
    "/{tenant_id}/agents/{agent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_tenant_agent(
    tenant_id: UUID,
    agent_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    admin_user_id: UUID = Depends(require_admin_platform_role),
) -> Response:
    """Delete a tenant's AgentSpec definition.

    - 401/403 via require_admin_platform_role
    - 404 when the agent is absent in this tenant (tenant-scoped DELETE never
      touches another tenant's row)
    - 204 on success; audit chain entry written
      (operation=agent_catalog.delete).
    """
    await _load_tenant_or_404(db, tenant_id)
    repo = AgentCatalogRepository(db)
    deleted = await repo.delete(tenant_id=tenant_id, agent_id=agent_id)
    if deleted == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"agent {agent_id} not found in tenant",
        )

    await append_audit(
        db,
        tenant_id=tenant_id,
        operation="agent_catalog.delete",
        resource_type="agent_catalog",
        resource_id=str(agent_id),
        operation_data={"agent_id": str(agent_id)},
        user_id=admin_user_id,
        operation_result="success",
    )
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


__all__ = ["router"]
