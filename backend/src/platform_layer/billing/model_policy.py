"""
File: backend/src/platform_layer/billing/model_policy.py
Purpose: resolve_tenant_model_policy — read a tenant's {action, cheap} model overrides (TTL-cached).
Category: Phase 57 platform_layer.billing (config tiering)
Scope: Sprint 57.104 (C1 — per-tenant model policy)

Description:
    Resolves a tenant's ModelPolicy from tenant.meta_data["model_policy"] behind a
    short TTL cache, so the per-request chat hot path pays at most one DB read per
    tenant per TTL window. The admin PUT (api/v1/admin/tenants.py) invalidates the
    cache so a policy change takes effect on the next request.

    Mirrors api/v1/chat/handler.py:resolve_session_persona — an async, tenant-scoped
    meta_data read the ROUTER runs BEFORE build_handler so the sync builders receive
    a ready value (no async DB import in the wiring layer). Fail-open: any miss / DB
    flake → an empty policy (the env-only path), never an error (a resolution failure
    must not break chat).

    Provider-neutral: returns the neutral ModelPolicy value object; no SDK import.

Key Components:
    - resolve_tenant_model_policy(db, tenant_id) -> ModelPolicy
    - invalidate_tenant_model_policy(tenant_id) — drop the cache entry (called by the PUT)
    - reset_model_policy_cache() — test isolation hook (Risk Class C)
    - _ModelPolicyCache — TTL cache with an injectable clock (no module-wide clock helper exists)

Created: 2026-06-11 (Sprint 57.104)
Last Modified: 2026-06-11

Modification History (newest-first):
    - 2026-06-11: Initial creation (Sprint 57.104 C1) — TTL-cached per-tenant model policy resolver

Related:
    - adapters/_base/model_policy.py — the ModelPolicy value object resolved here
    - api/v1/chat/handler.py:resolve_session_persona — mirrored resolve-before-build pattern
    - api/v1/admin/tenants.py — the PUT writes meta_data["model_policy"] + invalidates the cache
    - .claude/rules/testing.md §Module-level Singleton Reset Pattern (Risk Class C)
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TYPE_CHECKING
from uuid import UUID

from adapters._base.model_policy import ModelPolicy

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

# Default TTL: a policy change takes effect within ~60s even without a PUT-
# invalidate; the PUT invalidates immediately so the change is instant next request.
_DEFAULT_TTL_S = 60.0


# === _ModelPolicyCache: per-tenant TTL cache with an injectable clock ==========
# Why: the chat hot path resolves the policy every request; a short TTL turns N
# requests/min into 1 DB read/min per tenant. Day-0 D7 (Sprint 57.104) found no
# module-wide clock helper (SessionRegistry uses a bare datetime.now), so the cache
# owns an injectable clock (default time.monotonic) for deterministic TTL tests. No
# lock: get/put have no await, so the dict mutations are atomic on the event loop;
# a concurrent miss double-reads the same value (idempotent), which is harmless.
class _ModelPolicyCache:
    """A per-tenant ModelPolicy TTL cache. Module singleton; reset in tests."""

    def __init__(
        self, ttl_s: float = _DEFAULT_TTL_S, clock: Callable[[], float] = time.monotonic
    ) -> None:
        self._ttl_s = ttl_s
        self._clock = clock
        self._entries: dict[UUID, tuple[ModelPolicy, float]] = {}

    def get(self, tenant_id: UUID) -> ModelPolicy | None:
        entry = self._entries.get(tenant_id)
        if entry is None:
            return None
        policy, expiry = entry
        if self._clock() >= expiry:
            self._entries.pop(tenant_id, None)
            return None
        return policy

    def put(self, tenant_id: UUID, policy: ModelPolicy) -> None:
        self._entries[tenant_id] = (policy, self._clock() + self._ttl_s)

    def invalidate(self, tenant_id: UUID) -> None:
        self._entries.pop(tenant_id, None)

    def clear(self) -> None:
        self._entries.clear()


_cache = _ModelPolicyCache()


async def resolve_tenant_model_policy(
    db: AsyncSession | None, tenant_id: UUID | None
) -> ModelPolicy:
    """Resolve a tenant's ModelPolicy (TTL-cached). Fail-open to an empty policy.

    Returns ModelPolicy() (the env-only path) when db / tenant_id is missing, the
    tenant row / meta_data["model_policy"] is absent, or on any lookup error.
    """
    if db is None or tenant_id is None:
        return ModelPolicy()
    cached = _cache.get(tenant_id)
    if cached is not None:
        return cached

    policy = ModelPolicy()
    try:
        from sqlalchemy import select

        from infrastructure.db.models.identity import Tenant

        result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = result.scalar_one_or_none()
        if tenant is not None:
            raw = (tenant.meta_data or {}).get("model_policy")
            if isinstance(raw, dict):
                policy = ModelPolicy.from_dict(raw)
    except Exception:  # noqa: BLE001 — fail-open (mirrors resolve_session_persona)
        # A resolution failure must not break chat; the env-only path applies.
        return ModelPolicy()

    _cache.put(tenant_id, policy)
    return policy


def invalidate_tenant_model_policy(tenant_id: UUID) -> None:
    """Drop a tenant's cached policy (called by the admin PUT after a write)."""
    _cache.invalidate(tenant_id)


def reset_model_policy_cache() -> None:
    """Test isolation hook (Risk Class C — module singleton across event loops)."""
    _cache.clear()
