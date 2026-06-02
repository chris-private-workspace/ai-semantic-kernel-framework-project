"""
File: backend/src/infrastructure/db/models/agent_catalog.py
Purpose: AgentCatalog ORM — per-tenant AgentSpec definitions backing Cat 11 HANDOFF personas.
Category: Infrastructure / ORM (Subagent group, per 09-db-schema-design.md Group 9 範疇 11)
Scope: Phase 57 / Sprint 57.70 (real per-tenant agent-spec catalog, Stage-1a)

Description:
    Per-tenant, durable catalog of AgentSpec definitions (the persistent
    backing for the Cat 11 Subagent Registry AND for HANDOFF persona
    resolution). Replaces the Sprint 57.68 hardcoded 3-entry persona
    stand-in (platform_layer/handoff/persona_registry.py): a tenant's
    catalog row (active) overrides the hardcoded DEFAULT_AGENTS fallback.

    Fields align to the mockup AgentSpec shape (reference/design-mockups/
    page-agents.jsx SubagentDetail tabs): key (immutable role id) / name /
    model / system_prompt / allowed_modes (subset of fork/as_tool/teammate/
    handoff) / status (live/staging) + budget{max_tokens,duration,concurrent,
    depth} + tools[] stored in the meta_data JSONB.

    Multi-tenant 鐵律: inherits TenantScopedMixin (tenant_id NOT NULL + FK +
    index); a UNIQUE(tenant_id, key) keeps role keys unique per tenant. RLS
    (2 policies + FORCE) is applied by Alembic 0023.

    The budget / tools / allowed_modes fields are STORED (JSONB) but NOT yet
    enforced in the agent loop (Sprint 57.70 §9 — enforcement deferred).

Key Components:
    - AgentCatalog: per-tenant AgentSpec definition row

Created: 2026-06-02 (Sprint 57.70 Stage-1a)
Last Modified: 2026-06-02

Modification History (newest-first):
    - 2026-06-02: Initial creation (Sprint 57.70 Stage-1a) — per-tenant agent-spec catalog

Related:
    - 09-db-schema-design.md §Group 9 Subagent (範疇 11)
    - 0023_agent_catalog.py — Alembic migration (table + RLS + data seed)
    - infrastructure/db/repositories/agent_catalog_repository.py — DAO
    - platform_layer/handoff/persona_registry.py — async resolve_persona (DB → defaults → None)
    - .claude/rules/multi-tenant-data.md 鐵律 1 (tenant_id NOT NULL on session-scoped tables)
    - sprint-57-70-plan.md §3.1
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import (
    Boolean,
    DateTime,
    Index,
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
# AgentCatalog - per-tenant AgentSpec definition (範疇 11)
# =====================================================================
class AgentCatalog(Base, TenantScopedMixin):
    """Per-tenant AgentSpec definition. Per 09-db-schema-design.md §Group 9."""

    __tablename__ = "agent_catalog"

    id: Mapped[PyUUID] = mapped_column(
        PgUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    # key = the role / immutable id (e.g. "researcher"); unique per tenant.
    key: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)

    # Subset of fork / as_tool / teammate / handoff (stored, not yet enforced).
    allowed_modes: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'live'"))

    # JSONB exposed as `meta_data` but stored under the physical column
    # "metadata" (mirrors Session/Tenant). Holds budget{max_tokens,duration,
    # concurrent,depth} + tools[]; STORED, not yet loop-enforced.
    meta_data: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("TRUE"))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "key", name="uq_agent_catalog_tenant_key"),
        Index("idx_agent_catalog_tenant", "tenant_id"),
    )


__all__ = ["AgentCatalog"]
