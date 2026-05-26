"""
File: backend/src/core/feature_flags.py
Purpose: FeatureFlagsService — central read+write API for feature_flags table.
Category: Core (cross-cutting service)
Scope: Sprint 56.1 / Day 3 / US-4 Feature Flags

Description:
    Resolves "is feature X enabled for tenant T?" queries with the lookup
    precedence:
        1. tenant_overrides[str(tenant_id)] when set
        2. default_enabled fallback

    Writes via `set_tenant_override` always emit an audit chain entry via
    `infrastructure.db.audit_helper.append_audit` so the actor + before/after
    transition is traceable.

    Default flags (seeded once on first call to `seed_defaults`):
        - thinking_enabled        (default True)
        - verification_enabled    (default True)
        - llm_caching_enabled     (default True)
        - pii_masking             (default True)

    Cache: in-memory `_resolved_cache[(flag_name, tenant_id_or_none)] -> bool`.
    Invalidated on every `set_tenant_override`. Cache is per-instance — module
    singleton lifecycle managed via `get_feature_flags_service` /
    `reset_feature_flags_service` (per `.claude/rules/testing.md`
    §Module-level Singleton Reset Pattern).

    Cross-category note: `core/` is permitted to depend on `infrastructure/`
    + `platform_layer/` (per category-boundaries.md §Cross-layer rules); the
    audit chain caller obeys multi-tenant-data.md (always passes tenant_id).

Modification History (newest-first):
    - 2026-05-26: Sprint 57.55 — add clear_tenant_override (D-DAY0-T pivot)
    - 2026-05-06: Initial creation (Sprint 56.1 Day 3 / US-4)

Related:
    - infrastructure/db/models/feature_flag.py — ORM
    - infrastructure/db/audit_helper.py — append_audit chain helper
    - sprint-56-1-plan.md §US-4 + checklist 3.5/3.6
"""

from __future__ import annotations

from typing import Iterable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.audit_helper import append_audit
from infrastructure.db.models.feature_flag import FeatureFlag

DEFAULT_FLAGS: dict[str, tuple[bool, str]] = {
    "thinking_enabled": (True, "Cat 6 Thinking emission gate (per-tenant)"),
    "verification_enabled": (True, "Cat 10 verification loop gate (per-tenant)"),
    "llm_caching_enabled": (True, "Cat 4 prompt-caching breakpoint emission gate"),
    "pii_masking": (True, "Cat 9 PII redaction in audit log + tracer attrs"),
}


class FeatureFlagNotFoundError(KeyError):
    """Raised when a flag name is not in the registry (and not seeded)."""


class FeatureFlagsService:
    """Stateless service over the `feature_flags` table with read cache."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        # Cache: {(flag_name, tenant_id_str_or_none): bool}
        self._resolved_cache: dict[tuple[str, str | None], bool] = {}

    # ---- Read ------------------------------------------------------

    async def is_enabled(
        self,
        flag_name: str,
        tenant_id: UUID | None = None,
        user_id: UUID | None = None,  # noqa: ARG002 — reserved for Phase 56.x per-user
    ) -> bool:
        """Resolve flag for tenant; check tenant override first then default."""
        cache_key = (flag_name, str(tenant_id) if tenant_id else None)
        if cache_key in self._resolved_cache:
            return self._resolved_cache[cache_key]

        flag = await self._load(flag_name)
        if flag is None:
            raise FeatureFlagNotFoundError(
                f"flag '{flag_name}' not in registry; seed_defaults() may be required"
            )

        if tenant_id is not None:
            override = flag.tenant_overrides.get(str(tenant_id))
            if override is not None:
                resolved = bool(override)
                self._resolved_cache[cache_key] = resolved
                return resolved

        resolved = bool(flag.default_enabled)
        self._resolved_cache[cache_key] = resolved
        return resolved

    async def _load(self, flag_name: str) -> FeatureFlag | None:
        stmt = select(FeatureFlag).where(FeatureFlag.name == flag_name)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    # ---- Write -----------------------------------------------------

    async def set_tenant_override(
        self,
        flag_name: str,
        tenant_id: UUID,
        enabled: bool,
        actor_user_id: UUID | None = None,
    ) -> None:
        """Set per-tenant override + emit audit chain entry."""
        flag = await self._load(flag_name)
        if flag is None:
            raise FeatureFlagNotFoundError(
                f"flag '{flag_name}' not in registry; cannot override unknown flag"
            )
        previous = flag.tenant_overrides.get(str(tenant_id))
        new_overrides = dict(flag.tenant_overrides)
        new_overrides[str(tenant_id)] = enabled
        flag.tenant_overrides = new_overrides

        await append_audit(
            self._session,
            tenant_id=tenant_id,
            user_id=actor_user_id,
            operation="feature_flag_override_set",
            resource_type="feature_flag",
            resource_id=flag_name,
            operation_data={
                "flag_name": flag_name,
                "tenant_id": str(tenant_id),
                "previous_override": previous,
                "new_value": enabled,
            },
            operation_result="success",
        )

        await self._session.flush()
        # Invalidate cached lookups for this flag (any tenant).
        keys_to_drop = [k for k in self._resolved_cache if k[0] == flag_name]
        for k in keys_to_drop:
            self._resolved_cache.pop(k, None)

    async def clear_tenant_override(
        self,
        flag_name: str,
        tenant_id: UUID,
        actor_user_id: UUID | None = None,
    ) -> None:
        """Remove per-tenant override (revert to default_enabled) + emit audit entry.

        Sprint 57.55 — D-DAY0-T pivot: supports composite-replace clear semantics
        for PUT /admin/tenants/{tenant_id}/feature-flags endpoint. Idempotent:
        no-op when no override exists for the given tenant (no audit entry emitted).
        """
        flag = await self._load(flag_name)
        if flag is None:
            raise FeatureFlagNotFoundError(
                f"flag '{flag_name}' not in registry; cannot clear unknown flag"
            )
        if str(tenant_id) not in flag.tenant_overrides:
            return  # idempotent no-op
        previous = flag.tenant_overrides[str(tenant_id)]
        new_overrides = dict(flag.tenant_overrides)
        del new_overrides[str(tenant_id)]
        flag.tenant_overrides = new_overrides

        await append_audit(
            self._session,
            tenant_id=tenant_id,
            user_id=actor_user_id,
            operation="feature_flag_override_cleared",
            resource_type="feature_flag",
            resource_id=flag_name,
            operation_data={
                "flag_name": flag_name,
                "tenant_id": str(tenant_id),
                "previous_override": previous,
            },
            operation_result="success",
        )

        await self._session.flush()
        # Invalidate cached lookups for this flag (any tenant).
        keys_to_drop = [k for k in self._resolved_cache if k[0] == flag_name]
        for k in keys_to_drop:
            self._resolved_cache.pop(k, None)

    # ---- Seed ------------------------------------------------------

    async def seed_defaults(self, names: Iterable[str] | None = None) -> int:
        """Idempotent: insert any missing default flag rows. Returns insert count."""
        target = names or DEFAULT_FLAGS.keys()
        existing_stmt = select(FeatureFlag.name).where(FeatureFlag.name.in_(list(target)))
        existing_rows = await self._session.execute(existing_stmt)
        existing = set(existing_rows.scalars().all())
        to_insert = [name for name in target if name not in existing]

        for name in to_insert:
            default, description = DEFAULT_FLAGS[name]
            row = FeatureFlag(
                name=name,
                default_enabled=default,
                tenant_overrides={},
                description=description,
            )
            self._session.add(row)
        if to_insert:
            await self._session.flush()
        return len(to_insert)


# Module-level singleton — reset hook per testing.md §Module-level Singleton Reset Pattern.
_service: FeatureFlagsService | None = None


def get_feature_flags_service(session: AsyncSession) -> FeatureFlagsService:
    """Per-request service factory (sessions are per-request → no caching)."""
    return FeatureFlagsService(session)


def reset_feature_flags_service() -> None:
    """Test isolation hook (singleton not used; reserved for future caching layer)."""
    global _service
    _service = None
