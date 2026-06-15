"""
File: backend/src/platform_layer/skills/service.py
Purpose: TenantSkillService (per-tenant skill CRUD) + resolve_tenant_skill_registry resolver.
Category: platform_layer.skills (Skills System per-tenant catalog)
Scope: Sprint 57.114 / US-2 + US-3

Description:
    The per-tenant half of the Skills System. A tenant authors custom skills (name
    + description + a full instruction body) stored in the tenant_skills table;
    TenantSkillService does RLS-scoped CRUD (mirroring InvitesService — stateless,
    AsyncSession per call, _set_tenant before each query). resolve_tenant_skill_registry
    loads the bundled SkillRegistry then overlays the tenant's rows on top (a same-
    name tenant skill shadows a bundled one — SkillRegistry.with_overlay); it is
    TTL-cached per tenant (mirroring _ModelPolicyCache) and FAILS OPEN to the
    bundled set (db None / error / no rows → byte-identical to the system-bundled
    path). The router swaps get_default_skill_registry() for this resolver so the
    "## Available Skills" block + the read_skill tool carry the per-tenant overlay.

Key Components:
    - TenantSkillError + DuplicateSkillError (409) + SkillNotFoundError (404)
    - TenantSkillService: list_skills / create / update / delete
    - resolve_tenant_skill_registry(db, tenant_id) -> SkillRegistry (fail-open, TTL-cached)
    - invalidate_tenant_skill_registry / reset_skill_registry_cache

Created: 2026-06-13 (Sprint 57.114)

Modification History:
    - 2026-06-15: Sprint 57.117 — skill quota + body-size caps + SkillQuotaExceededError
    - 2026-06-13: Initial creation (Sprint 57.114 / US-2 + US-3)

Related:
    - infrastructure/db/models/skill.py:TenantSkill — ORM
    - agent_harness/skills/registry.py — SkillRegistry.with_overlay + get_default_skill_registry
    - platform_layer/billing/model_policy.py — _ModelPolicyCache TTL pattern (mirror)
    - platform_layer/identity/invites.py — InvitesService _set_tenant CRUD pattern (mirror)
    - api/v1/admin/tenants.py — the admin CRUD endpoints (caller; audit + cache invalidation)
    - api/v1/chat/router.py — resolve_tenant_skill_registry caller (主流量, 約束 2)
    - .claude/rules/multi-tenant-data.md 鐵律 (tenant context per write)
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Callable
from uuid import UUID

from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from agent_harness.skills import Skill, SkillRegistry, get_default_skill_registry
from infrastructure.db.models.skill import TenantSkill

_DEFAULT_TTL_S = 60.0


# === Per-tenant skill guardrails (env-overridable; the 57.109 CHAT_COMPACTION_* knob precedent) ===
# Why: Sprint 57.114 shipped the per-tenant catalog with NO upper bounds — a tenant could
# create unbounded skills, each with an unbounded `instructions` body (Text, min_length=1 only).
# These two caps are the write-path guardrails (AD-Skills-Per-Tenant-Quota): the count quota is
# enforced in create() (a typed error the admin POST endpoint already maps); the body-size cap is
# the request-layer max_length (api/v1/admin/tenants.py reads SKILLS_MAX_INSTRUCTIONS_CHARS).
# Module-level env read (restart-to-change, like CHAT_COMPACTION_*). A per-tenant CONFIGURABLE
# quota (meta_data override) + a multi-worker shared cache-invalidation signal stay deferred.
def _env_int(name: str, default: int) -> int:
    """Read a positive int from the env; non-int / non-positive → the default."""
    try:
        value = int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default


SKILLS_MAX_PER_TENANT = _env_int("SKILLS_MAX_PER_TENANT", 50)
SKILLS_MAX_INSTRUCTIONS_CHARS = _env_int("SKILLS_MAX_INSTRUCTIONS_CHARS", 20_000)


# === Typed errors (carry an HTTP status hint for the admin endpoints) ===
class TenantSkillError(Exception):
    """Base tenant-skill error; subclasses set `status_code` + a safe `detail`."""

    status_code: int = 400
    detail: str = "tenant skill error"

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(detail or self.detail)
        if detail:
            self.detail = detail


class DuplicateSkillError(TenantSkillError):
    status_code = 409
    detail = "a skill with this name already exists for this tenant"


class SkillNotFoundError(TenantSkillError):
    status_code = 404
    detail = "skill not found"


class SkillQuotaExceededError(TenantSkillError):
    status_code = 409
    detail = "skill quota reached for this tenant"


# === TenantSkillService: per-tenant skill CRUD ===
# Why: a tenant's custom skills need a persistent, listable, per-tenant home so the
# resolver can overlay them on the bundled set. Mirrors InvitesService: stateless,
# AsyncSession per call, _set_tenant before each query (RLS context). A pre-INSERT
# name-existence SELECT gives a clean DuplicateSkillError (the DB UNIQUE constraint
# is the ultimate backstop). append_audit + cache invalidation live in the admin
# endpoints (the model/harness-policy config-tiering precedent).
class TenantSkillService:
    """Per-tenant skill CRUD; each method manages its own RLS tenant context."""

    async def list_skills(self, db: AsyncSession, *, tenant_id: UUID) -> list[TenantSkill]:
        """Return the tenant's skills, ordered by name (deterministic)."""
        await _set_tenant(db, str(tenant_id))
        rows = (
            (
                await db.execute(
                    select(TenantSkill)
                    .where(TenantSkill.tenant_id == tenant_id)
                    .order_by(TenantSkill.name)
                )
            )
            .scalars()
            .all()
        )
        return list(rows)

    async def create(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        name: str,
        description: str,
        instructions: str,
    ) -> TenantSkill:
        """Create a skill. Enforces the per-tenant quota + name uniqueness.

        Raises SkillQuotaExceededError when the tenant is at SKILLS_MAX_PER_TENANT;
        DuplicateSkillError if (tenant_id, name) already exists.
        """
        await _set_tenant(db, str(tenant_id))
        count = (
            await db.execute(
                select(func.count())
                .select_from(TenantSkill)
                .where(TenantSkill.tenant_id == tenant_id)
            )
        ).scalar_one()
        if count >= SKILLS_MAX_PER_TENANT:
            raise SkillQuotaExceededError()
        existing = (
            await db.execute(
                select(TenantSkill).where(
                    TenantSkill.tenant_id == tenant_id, TenantSkill.name == name
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            raise DuplicateSkillError()
        skill = TenantSkill(
            tenant_id=tenant_id,
            name=name,
            description=description,
            instructions=instructions,
        )
        db.add(skill)
        await db.flush()
        await db.refresh(skill)
        return skill

    async def update(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        skill_id: UUID,
        name: str | None = None,
        description: str | None = None,
        instructions: str | None = None,
    ) -> TenantSkill:
        """Apply provided fields. 404 → SkillNotFoundError; a name clash → DuplicateSkillError."""
        await _set_tenant(db, str(tenant_id))
        skill = (
            await db.execute(
                select(TenantSkill).where(
                    TenantSkill.id == skill_id, TenantSkill.tenant_id == tenant_id
                )
            )
        ).scalar_one_or_none()
        if skill is None:
            raise SkillNotFoundError()
        if name is not None and name != skill.name:
            clash = (
                await db.execute(
                    select(TenantSkill).where(
                        TenantSkill.tenant_id == tenant_id, TenantSkill.name == name
                    )
                )
            ).scalar_one_or_none()
            if clash is not None:
                raise DuplicateSkillError()
            skill.name = name
        if description is not None:
            skill.description = description
        if instructions is not None:
            skill.instructions = instructions
        skill.updated_at = _utcnow()
        await db.flush()
        await db.refresh(skill)
        return skill

    async def delete(self, db: AsyncSession, *, tenant_id: UUID, skill_id: UUID) -> None:
        """Delete a skill. Raises SkillNotFoundError if no such skill in the tenant."""
        await _set_tenant(db, str(tenant_id))
        deleted = (
            await db.execute(
                sa_delete(TenantSkill)
                .where(TenantSkill.id == skill_id, TenantSkill.tenant_id == tenant_id)
                .returning(TenantSkill.id)
            )
        ).scalar_one_or_none()
        if deleted is None:
            raise SkillNotFoundError()
        await db.flush()


# === Per-tenant registry cache + resolver ===
# Why: the chat router resolves a SkillRegistry every turn; a DB round-trip per
# turn is wasteful for a slowly-changing catalog → cache per tenant with a short
# TTL (mirror _ModelPolicyCache, injectable clock for tests). Admin mutations
# invalidate. FAIL OPEN to the bundled set so a DB hiccup never breaks chat
# (regression-safe: no rows / db None / error → byte-identical to the bundled path).
class _SkillRegistryCache:
    """Per-tenant resolved-SkillRegistry TTL cache. Module singleton; reset in tests."""

    def __init__(
        self, ttl_s: float = _DEFAULT_TTL_S, clock: Callable[[], float] = time.monotonic
    ) -> None:
        self._ttl_s = ttl_s
        self._clock = clock
        self._entries: dict[UUID, tuple[SkillRegistry, float]] = {}

    def get(self, tenant_id: UUID) -> SkillRegistry | None:
        entry = self._entries.get(tenant_id)
        if entry is None:
            return None
        registry, expiry = entry
        if self._clock() >= expiry:
            self._entries.pop(tenant_id, None)
            return None
        return registry

    def put(self, tenant_id: UUID, registry: SkillRegistry) -> None:
        self._entries[tenant_id] = (registry, self._clock() + self._ttl_s)

    def invalidate(self, tenant_id: UUID) -> None:
        self._entries.pop(tenant_id, None)

    def clear(self) -> None:
        self._entries.clear()


tenant_skill_service = TenantSkillService()
_cache = _SkillRegistryCache()


async def resolve_tenant_skill_registry(
    db: AsyncSession | None, tenant_id: UUID | None
) -> SkillRegistry:
    """Resolve the tenant's SkillRegistry (bundled + tenant overlay; TTL-cached; fail-open)."""
    if db is None or tenant_id is None:
        return get_default_skill_registry()
    cached = _cache.get(tenant_id)
    if cached is not None:
        return cached
    try:
        rows = await tenant_skill_service.list_skills(db, tenant_id=tenant_id)
        extra = [
            Skill(name=row.name, description=row.description, instructions=row.instructions)
            for row in rows
        ]
        registry = get_default_skill_registry().with_overlay(extra)
    except Exception:  # noqa: BLE001 — fail-open: a DB hiccup must never break chat
        return get_default_skill_registry()
    _cache.put(tenant_id, registry)
    return registry


def invalidate_tenant_skill_registry(tenant_id: UUID) -> None:
    """Drop a tenant's cached registry (called by every admin mutation)."""
    _cache.invalidate(tenant_id)


def reset_skill_registry_cache() -> None:
    """Test isolation hook (Risk Class C) — clear the per-tenant cache."""
    _cache.clear()


async def _set_tenant(db: AsyncSession, tenant_id: str) -> None:
    """SET LOCAL app.tenant_id for the current transaction (RLS context).

    set_config(...) is the bind-param-compatible function form of SET LOCAL
    (asyncpg rejects params on the SET utility statement); is_local=true →
    txn-scoped. Mirrors platform_layer/identity/invites.py:_set_tenant.
    """
    await db.execute(text("SELECT set_config('app.tenant_id', :tid, true)"), {"tid": tenant_id})


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


__all__ = [
    "TenantSkillError",
    "DuplicateSkillError",
    "SkillNotFoundError",
    "SkillQuotaExceededError",
    "SKILLS_MAX_PER_TENANT",
    "SKILLS_MAX_INSTRUCTIONS_CHARS",
    "TenantSkillService",
    "tenant_skill_service",
    "resolve_tenant_skill_registry",
    "invalidate_tenant_skill_registry",
    "reset_skill_registry_cache",
]
