"""
File: backend/src/platform_layer/handoff/persona_registry.py
Purpose: Per-tenant persona resolution (DB catalog → hardcoded defaults → None) for Cat 11 HANDOFF.
Category: platform_layer (Cat 11 HANDOFF support — session-boot persona)
Scope: Phase 57 / Sprint 57.70 (real per-tenant agent-spec catalog, Stage-1a)

Description:
    Resolves a target agent key → system prompt for Cat 11 HANDOFF (and the
    chat handler's per-session persona). Sprint 57.68 used a hardcoded 3-entry
    dict; Sprint 57.70 makes resolution per-tenant DB-backed:

        1. the tenant's agent_catalog row (active) → its system_prompt
        2. else the hardcoded DEFAULT_AGENTS fallback (always present, so an
           empty / new-tenant catalog still resolves the 3 defaults)
        3. else None (reject — unknown agent)

    The DB lookup is wrapped in a fail-safe try/except: any DB error falls
    through to DEFAULT_AGENTS so a known key always resolves and a DB flake
    never crashes the handoff / handler path.

    DEFAULT_AGENTS doubles as the seed source for the 0023 data migration
    (which materializes editable rows per existing tenant) and the no-DB test
    path (resolve_default_persona).

    Pure stdlib + the catalog repository; LLM-provider-neutral (no SDK import).

Key Components:
    - DEFAULT_AGENTS: dict[str, str] — hardcoded fallback + seed source
    - resolve_persona(db, tenant_id, key): async — DB catalog → defaults → None
    - resolve_default_persona(key): sync — DEFAULT_AGENTS lookup only (no DB)

Created: 2026-06-02 (Sprint 57.68 A-3b)
Last Modified: 2026-06-02

Modification History (newest-first):
    - 2026-06-02: Sprint 57.70 Stage-1a — DB-backed per-tenant resolution; rename to DEFAULT_AGENTS
    - 2026-06-02: Initial creation (Sprint 57.68 A-3b) — minimal handoff persona stand-in

Related:
    - infrastructure/db/models/agent_catalog.py — AgentCatalog ORM (DB source)
    - infrastructure/db/repositories/agent_catalog_repository.py — get_by_key
    - platform_layer/handoff/service.py — consumer (HandoffService.boot_handoff)
    - api/v1/chat/handler.py — consumer (resolve_session_persona)
    - 01-eleven-categories-spec.md §範疇 11 — HANDOFF control transfer
    - sprint-57-70-plan.md §3.3 — async tenant-scoped persona resolution (US-3)
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# === Default agents (hardcoded fallback + seed source) =====================
# Why: a HANDOFF must resolve target_agent → a real system prompt so the booted
# child session runs as the target (not the demo persona = Potemkin). The
# per-tenant DB catalog (agent_catalog) is the primary source; this dict is the
# always-present fallback so an empty / new-tenant catalog still resolves the
# canonical roles, AND the seed source the 0023 data migration materializes as
# editable rows for existing tenants. Names mirror the canonical example roles
# used across Cat 11 fixtures ("researcher" / "reviewer" / "planner").
DEFAULT_AGENTS: dict[str, str] = {
    "researcher": (
        "You are a research specialist agent. Investigate the user's question "
        "thoroughly, gather supporting evidence, cite sources where possible, "
        "and produce a structured, well-organized findings summary."
    ),
    "reviewer": (
        "You are a critical review specialist agent. Carefully assess the work "
        "handed to you for correctness, completeness, and risks. Point out "
        "concrete issues and concrete improvements; be specific and honest."
    ),
    "planner": (
        "You are a planning specialist agent. Break the user's goal into a "
        "clear, ordered set of verifiable steps, identify dependencies and "
        "risks, and state the success criteria for each step."
    ),
}


def resolve_default_persona(key: str) -> str | None:
    """Resolve a key against the hardcoded DEFAULT_AGENTS only (no DB).

    Args:
        key: the target agent identifier (whitespace-trimmed before lookup).

    Returns:
        The default system prompt, or None when key is empty / whitespace /
        not a known default. For tests + no-DB code paths.
    """
    trimmed = (key or "").strip()
    if not trimmed:
        return None
    return DEFAULT_AGENTS.get(trimmed)


async def resolve_persona(db: AsyncSession, tenant_id: UUID, key: str) -> str | None:
    """Resolve a target agent key → system prompt (per-tenant, DB-backed).

    Resolution order:
        1. the tenant's agent_catalog row (when present AND active) →
           its system_prompt;
        2. else the hardcoded DEFAULT_AGENTS fallback;
        3. else None.

    The DB lookup is fail-safe: any error falls through to the DEFAULT_AGENTS
    fallback so a known key always resolves and a DB flake never crashes the
    handoff / handler path. An empty / whitespace key short-circuits to None.

    Args:
        db: AsyncSession used for the tenant-scoped catalog read.
        tenant_id: the tenant whose catalog is consulted (multi-tenant 鐵律).
        key: the target agent identifier (whitespace-trimmed before lookup).

    Returns:
        The resolved system prompt, or None when key is empty / whitespace /
        not in the tenant catalog NOR the defaults. Callers MUST treat None as
        an invalid handoff (no session booted) / fall back to DEMO.
    """
    trimmed = (key or "").strip()
    if not trimmed:
        return None

    # 1. Per-tenant DB catalog (active row wins). Fail-safe: any DB error falls
    #    through to the always-present hardcoded defaults below.
    try:
        # Imported here (not at module level) to keep this module dep-light and
        # avoid an import cycle (the repo imports the ORM models package).
        from infrastructure.db.repositories.agent_catalog_repository import (
            AgentCatalogRepository,
        )

        row = await AgentCatalogRepository(db).get_by_key(tenant_id=tenant_id, key=trimmed)
        if row is not None and row.is_active:
            return row.system_prompt
    except Exception:  # noqa: BLE001 — fail-safe to the hardcoded fallback.
        logger.warning(
            "resolve_persona DB lookup failed; falling back to DEFAULT_AGENTS",
            extra={"tenant_id": str(tenant_id), "key": trimmed},
            exc_info=True,
        )

    # 2. Hardcoded default (covers empty / new-tenant catalogs); else 3. None.
    return DEFAULT_AGENTS.get(trimmed)


__all__ = ["DEFAULT_AGENTS", "resolve_persona", "resolve_default_persona"]
