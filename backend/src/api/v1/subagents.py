"""
File: backend/src/api/v1/subagents.py
Purpose: Cat 11 Subagent Registry REST facade — agent_catalog AgentSpec registry view.
Category: api/v1
Scope: Phase 57 / Sprint 57.78 (re-point STUB → agent_catalog registry)

Description:
    GET endpoint, gated by `Depends(get_current_tenant)` + RLS session:

    - GET /api/v1/subagents
        Lists the current tenant's AgentSpec catalog (registry view), backed by
        the per-tenant `agent_catalog` table (Sprint 57.70). Each item exposes
        the durable spec fields: key / name / model / allowed_modes (subset of
        fork/as_tool/teammate/handoff) / status / system_prompt, plus
        budget + tools parsed from the meta_data JSONB.

    Sprint 57.78 re-point (per Day 0 三-prong + user AskUserQuestion decision):

    This endpoint previously returned an EMPTY "runtime invocations" list with a
    `not_implemented_reason` flag — SubagentSpawned/Completed are in-memory
    LoopEvents only and were never persisted (AD-Subagent-RealList-Phase58).
    The user chose the **Agent Catalog/Registry view** over runtime invocations:
    the tenant's AgentSpec catalog already exists in `agent_catalog`
    (tenant-scoped + RLS, Sprint 57.70), so this endpoint now serves that real
    registry data.

    Usage metrics (calls_24h / p95_latency / success_rate / avg_tokens /
    top_orchestrator) have NO runtime data source (no persisted invocation
    telemetry), so they are reported in the `gapped` list — an honest gap, not
    fabricated zeros (AP-4). The runtime-invocations persistence path is the
    heavier route deferred to AD-Subagent-Invocations-Persistence-Phase58.

    Multi-tenant: tenant-scoped via the repo `tenant_id` filter (every WHERE
    clause) PLUS RLS `SET LOCAL app.tenant_id` from `get_db_session_with_tenant`
    (defence-in-depth, mirrors the memory.py /matrix + /ops facades). This is a
    tenant-facing read (any tenant user sees their tenant's catalog) — NO
    audit-role gate (it is not audit data).

Created: 2026-05-17 (Sprint 57.19 Day 2 / US-B4)
Last Modified: 2026-06-04

Modification History (newest-first):
    - 2026-06-04: Sprint 57.78 — re-point STUB → agent_catalog registry (AD-Subagent-RealList)
    - 2026-05-17: Initial creation (Sprint 57.19 Day 2 / US-B4) — empty-list stub

Related:
    - infrastructure/db/models/agent_catalog.py (AgentCatalog ORM — registry source)
    - infrastructure/db/repositories/agent_catalog_repository.py (list_by_tenant DAO)
    - platform_layer/middleware/tenant_context.py (get_db_session_with_tenant — RLS)
    - platform_layer/identity/auth.py (get_current_tenant)
    - api/v1/admin/agents.py (AgentResponse — serialization reference)
    - api/v1/memory.py (sibling deps-trio pattern for /matrix + /ops)
    - sprint-57-78-plan.md §3.1
    - 17-cross-category-interfaces.md §11 Cat 11 (no NEW ABC method this sprint)
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.repositories.agent_catalog_repository import (
    AgentCatalogRepository,
)
from platform_layer.identity.auth import get_current_tenant
from platform_layer.middleware.tenant_context import get_db_session_with_tenant

router = APIRouter(prefix="/subagents", tags=["subagents"])

# Usage metrics with NO runtime data source (no persisted invocation telemetry).
# Reported as honest gaps rather than fabricated zeros (AP-4).
USAGE_GAPPED = [
    "calls_24h",
    "p95_latency",
    "success_rate",
    "avg_tokens",
    "top_orchestrator",
]


class SubagentSpecItem(BaseModel):
    """One AgentSpec registry row (durable spec fields from agent_catalog)."""

    key: str
    name: str
    model: str | None
    allowed_modes: list[str]  # subset of fork/as_tool/teammate/handoff
    status: str  # live / staging
    system_prompt: str
    budget: dict[str, Any] | None  # meta_data.get("budget") — None if unset
    tools: list[str]  # meta_data.get("tools", [])


class SubagentsResponse(BaseModel):
    items: list[SubagentSpecItem]
    gapped: list[str]  # usage metrics with no runtime data source


@router.get("", response_model=SubagentsResponse)
async def list_subagents(
    current_tenant: UUID = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db_session_with_tenant),
) -> SubagentsResponse:
    """List the current tenant's AgentSpec catalog (registry view).

    Tenant-scoped via the repo `tenant_id` filter + RLS session
    (defence-in-depth). Usage metrics have no runtime source and are reported
    in `gapped` (honest gap, not fabricated zeros).
    """
    rows = await AgentCatalogRepository(db).list_by_tenant(tenant_id=current_tenant)

    items: list[SubagentSpecItem] = []
    for r in rows:
        meta = r.meta_data or {}
        tools = meta.get("tools", [])
        if not isinstance(tools, list):
            tools = []
        items.append(
            SubagentSpecItem(
                key=r.key,
                name=r.name,
                model=r.model,
                allowed_modes=r.allowed_modes,
                status=r.status,
                system_prompt=r.system_prompt,
                budget=meta.get("budget"),
                tools=tools,
            )
        )

    return SubagentsResponse(items=items, gapped=USAGE_GAPPED)
