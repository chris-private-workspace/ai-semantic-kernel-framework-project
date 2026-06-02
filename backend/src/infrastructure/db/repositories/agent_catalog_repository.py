"""
File: backend/src/infrastructure/db/repositories/agent_catalog_repository.py
Purpose: AgentCatalogRepository — async tenant-scoped DAO for the agent_catalog table.
Category: Infrastructure / Repositories (Sprint 57.70 Stage-1a — per-tenant agent-spec catalog)
Scope: Phase 57 / Sprint 57.70 Stage-1a

Description:
    Encapsulates AgentCatalog ORM operations (list / get / create / update /
    delete) for the per-tenant AgentSpec catalog. Backs the async
    resolve_persona() (HANDOFF persona resolution) and the Stage-1b admin
    CRUD API.

    Multi-tenant 鐵律: `tenant_id` is a REQUIRED keyword-only argument on every
    method and is applied as a filter in every WHERE clause (defence-in-depth
    alongside the table's RLS policies). The caller owns the transaction
    (flush, not commit) — mirrors SessionRepository.

Created: 2026-06-02 (Sprint 57.70 Stage-1a)
Last Modified: 2026-06-02

Modification History (newest-first):
    - 2026-06-02: Initial creation (Sprint 57.70 Stage-1a) — tenant-scoped agent catalog CRUD

Related:
    - infrastructure/db/models/agent_catalog.py (AgentCatalog ORM)
    - infrastructure/db/repositories/session_repository.py (pattern source)
    - platform_layer/handoff/persona_registry.py (resolve_persona consumer)
    - .claude/rules/multi-tenant-data.md 鐵律 (tenant-scoped queries)
    - sprint-57-70-plan.md §3.2
"""

from __future__ import annotations

import logging
from typing import Any, Sequence, cast
from uuid import UUID

from sqlalchemy import CursorResult, delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.models.agent_catalog import AgentCatalog

logger = logging.getLogger(__name__)


class AgentCatalogRepository:
    """DAO for agent_catalog — per-tenant AgentSpec definition persistence."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_by_tenant(self, *, tenant_id: UUID) -> Sequence[AgentCatalog]:
        """Return all AgentSpec rows for the tenant (newest first)."""
        stmt = (
            select(AgentCatalog)
            .where(AgentCatalog.tenant_id == tenant_id)
            .order_by(AgentCatalog.created_at.desc())
        )
        result = await self._db.execute(stmt)
        return result.scalars().all()

    async def get_by_key(self, *, tenant_id: UUID, key: str) -> AgentCatalog | None:
        """Fetch one AgentSpec by (tenant_id, key); None when absent in this tenant."""
        stmt = select(AgentCatalog).where(
            (AgentCatalog.tenant_id == tenant_id) & (AgentCatalog.key == key)
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, *, tenant_id: UUID, agent_id: UUID) -> AgentCatalog | None:
        """Fetch one AgentSpec by (tenant_id, id); None when absent / foreign."""
        stmt = select(AgentCatalog).where(
            (AgentCatalog.tenant_id == tenant_id) & (AgentCatalog.id == agent_id)
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        tenant_id: UUID,
        key: str,
        name: str,
        system_prompt: str,
        model: str | None = None,
        allowed_modes: list[str] | None = None,
        status: str = "live",
        meta_data: dict[str, Any] | None = None,
    ) -> AgentCatalog:
        """INSERT a new AgentSpec row scoped to the tenant.

        Caller owns the transaction (flush here, commit at the request scope).

        Raises:
            sqlalchemy.exc.IntegrityError: UNIQUE(tenant_id, key) violation
                (the role key already exists for this tenant) or FK violation
                (tenant_id missing in tenants).
        """
        agent = AgentCatalog(
            tenant_id=tenant_id,
            key=key,
            name=name,
            system_prompt=system_prompt,
            model=model,
            allowed_modes=allowed_modes if allowed_modes is not None else [],
            status=status,
        )
        if meta_data is not None:
            agent.meta_data = meta_data
        self._db.add(agent)
        await self._db.flush()
        logger.debug(
            "agent_catalog_repository.create ok",
            extra={"tenant_id": str(tenant_id), "key": key},
        )
        return agent

    async def update(
        self,
        *,
        tenant_id: UUID,
        agent_id: UUID,
        **fields: Any,
    ) -> AgentCatalog | None:
        """UPDATE a tenant's AgentSpec row by id; return the updated row or None.

        Only the provided `fields` are updated (tenant_id / id / key changes are
        ignored to keep the immutable identifiers stable). Tenant-scoped UPDATE
        (multi-tenant 鐵律) — a foreign / missing row is a no-op returning None.
        """
        allowed = {
            "name",
            "model",
            "system_prompt",
            "allowed_modes",
            "status",
            "meta_data",
            "is_active",
        }
        values = {k: v for k, v in fields.items() if k in allowed}
        if not values:
            # Nothing mutable supplied — just return the current row (or None).
            return await self.get_by_id(tenant_id=tenant_id, agent_id=agent_id)
        stmt = (
            update(AgentCatalog)
            .where((AgentCatalog.tenant_id == tenant_id) & (AgentCatalog.id == agent_id))
            .values(**values)
        )
        await self._db.execute(stmt)
        await self._db.flush()
        return await self.get_by_id(tenant_id=tenant_id, agent_id=agent_id)

    async def delete(self, *, tenant_id: UUID, agent_id: UUID) -> int:
        """DELETE a tenant's AgentSpec row by id; return rows deleted (0 / 1).

        Tenant-scoped DELETE (multi-tenant 鐵律) — a foreign / missing row
        affects 0 rows.
        """
        stmt = delete(AgentCatalog).where(
            (AgentCatalog.tenant_id == tenant_id) & (AgentCatalog.id == agent_id)
        )
        result = cast("CursorResult[Any]", await self._db.execute(stmt))
        await self._db.flush()
        return result.rowcount or 0


__all__ = ["AgentCatalogRepository"]
