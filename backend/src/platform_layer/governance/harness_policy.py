"""
File: backend/src/platform_layer/governance/harness_policy.py
Purpose: HarnessPolicy + resolve_tenant_harness_policy — per-tenant Cat 9/10 knobs (TTL-cached).
Category: Phase 57 platform_layer.governance (config tiering — C3)
Scope: Sprint 57.106 (C3 — per-tenant harness policy + risky-action detector)

Description:
    Resolves a tenant's HarnessPolicy from tenant.meta_data["harness_policy"] behind
    a short TTL cache (byte-pattern mirror of platform_layer/billing/model_policy.py,
    Sprint 57.104 C1). The policy carries the tenant's OPTIONAL overrides for the
    chat handler's governance knobs: escalate keyword phrases (3 chains), the
    escalate-tool list, verification mode / judge-template NAME / escalate-on-max,
    and the risky-action detector switch + extra patterns. Every field is sparse —
    an absent field falls back to the system default at wiring time, so a tenant
    with no policy is byte-identical to today's hardcoded-defaults path.

    Fail-open: any miss / DB flake → an empty policy (the defaults path), never an
    error. Provider-neutral; no SDK import; no agent_harness import (the detector
    receives plain values at registration — category boundaries hold).

Key Components:
    - HarnessPolicy — frozen sparse value object (from_dict / to_dict / is_empty)
    - resolve_tenant_harness_policy(db, tenant_id) -> HarnessPolicy
    - invalidate_tenant_harness_policy(tenant_id) — called by the admin PUT
    - reset_harness_policy_cache() — test isolation hook (Risk Class C)
    - _HarnessPolicyCache — TTL cache with an injectable clock

Created: 2026-06-12 (Sprint 57.106)
Last Modified: 2026-06-12

Modification History (newest-first):
    - 2026-06-12: Sprint 57.107 (B3) — add handoff_enabled + handoff_target_allowlist (9→11)
    - 2026-06-12: Initial creation (Sprint 57.106 C3) — per-tenant harness policy resolver

Related:
    - platform_layer/billing/model_policy.py — the mirrored C1 resolver pattern
    - api/v1/chat/handler.py — consumes the policy (phrases / tools / verification sourcing)
    - api/v1/admin/tenants.py — the PUT writes meta_data["harness_policy"] + invalidates
    - agent_harness/guardrails/tool/risky_action_detector.py — receives extra_patterns
    - .claude/rules/testing.md §Module-level Singleton Reset Pattern (Risk Class C)
"""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from uuid import UUID

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

# Default TTL: a policy change takes effect within ~60s even without a PUT-
# invalidate; the PUT invalidates immediately so the change is instant next request.
_DEFAULT_TTL_S = 60.0

# The meta_data["harness_policy"] JSONB schema v1 keys — single source for the
# round-trip (from_dict / to_dict) + the admin endpoint's request shape.
_LIST_FIELDS = (
    "escalate_input_phrases",
    "escalate_between_turns_phrases",
    "escalate_output_phrases",
    "escalate_tools",
    "risky_action_extra_patterns",
    "handoff_target_allowlist",
)
_STR_FIELDS = ("verification_mode", "verification_judge_template")
_BOOL_FIELDS = ("verification_escalate_on_max", "risky_action_enabled", "handoff_enabled")


def _clean_str(value: Any) -> str | None:
    """Coerce a raw JSONB value to a non-empty stripped str, else None."""
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _clean_str_list(value: Any) -> tuple[str, ...] | None:
    """Coerce a raw JSONB value to a tuple of non-empty strs; None when unusable.

    An explicit empty list survives as () — "tenant set it to nothing" is a real
    override (e.g. escalate_tools: [] turns the default escalate list OFF), distinct
    from None = "not set, use the system default".
    """
    if not isinstance(value, list):
        return None
    cleaned = tuple(s.strip() for s in value if isinstance(s, str) and s.strip())
    if not cleaned and value:
        # Non-empty raw list with zero usable strings → treat as not-set.
        return None
    return cleaned


def _clean_bool(value: Any) -> bool | None:
    """Coerce a raw JSONB value to bool, else None (not-set)."""
    return value if isinstance(value, bool) else None


@dataclass(frozen=True)
class HarnessPolicy:
    """A tenant's optional Cat 9/10 governance overrides (sparse; None = default).

    tuple fields use () vs None deliberately: () is an explicit "off" override,
    None means "not set" (system default applies). risky_action_enabled is
    tri-state for the same reason (None → the detector's default-ON).
    """

    escalate_input_phrases: tuple[str, ...] | None = None
    escalate_between_turns_phrases: tuple[str, ...] | None = None
    escalate_output_phrases: tuple[str, ...] | None = None
    escalate_tools: tuple[str, ...] | None = None
    verification_mode: str | None = None  # "enabled" | "disabled"
    verification_judge_template: str | None = None  # shipped template NAME only
    verification_escalate_on_max: bool | None = None
    risky_action_enabled: bool | None = None
    risky_action_extra_patterns: tuple[str, ...] | None = None
    # Sprint 57.107 (B3): handoff governance. handoff_enabled None/True = the
    # spec-only `handoff` tool is registered (the shipped feature defaults ON);
    # False = not registered (zero-cost off — the risky_action_enabled pattern).
    # handoff_target_allowlist None = all registered personas; values = restrict
    # (enforced at HandoffService.boot_handoff, defense in depth); the admin PUT
    # rejects an explicit [] (use handoff_enabled to disable).
    handoff_enabled: bool | None = None
    handoff_target_allowlist: tuple[str, ...] | None = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> HarnessPolicy:
        """Build from a raw meta_data["harness_policy"] mapping (None / empty → all-None)."""
        if not data:
            return cls()
        kwargs: dict[str, Any] = {}
        for name in _LIST_FIELDS:
            kwargs[name] = _clean_str_list(data.get(name))
        for name in _STR_FIELDS:
            kwargs[name] = _clean_str(data.get(name))
        for name in _BOOL_FIELDS:
            kwargs[name] = _clean_bool(data.get(name))
        return cls(**kwargs)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSONB-ready dict, dropping not-set (None) fields."""
        out: dict[str, Any] = {}
        for name in _LIST_FIELDS:
            value = getattr(self, name)
            if value is not None:
                out[name] = list(value)
        for name in (*_STR_FIELDS, *_BOOL_FIELDS):
            value = getattr(self, name)
            if value is not None:
                out[name] = value
        return out

    def is_empty(self) -> bool:
        """True when no field is set (→ the system-defaults path)."""
        return all(
            getattr(self, name) is None for name in (*_LIST_FIELDS, *_STR_FIELDS, *_BOOL_FIELDS)
        )


# === _HarnessPolicyCache: per-tenant TTL cache with an injectable clock ========
# Why: the chat hot path resolves the policy every request; a short TTL turns N
# requests/min into 1 DB read/min per tenant. Injectable clock for deterministic
# TTL tests; no lock — get/put have no await, so dict mutations are atomic on the
# event loop (mirror of _ModelPolicyCache, Sprint 57.104 D7 rationale).
class _HarnessPolicyCache:
    """A per-tenant HarnessPolicy TTL cache. Module singleton; reset in tests."""

    def __init__(
        self, ttl_s: float = _DEFAULT_TTL_S, clock: Callable[[], float] = time.monotonic
    ) -> None:
        self._ttl_s = ttl_s
        self._clock = clock
        self._entries: dict[UUID, tuple[HarnessPolicy, float]] = {}

    def get(self, tenant_id: UUID) -> HarnessPolicy | None:
        entry = self._entries.get(tenant_id)
        if entry is None:
            return None
        policy, expiry = entry
        if self._clock() >= expiry:
            self._entries.pop(tenant_id, None)
            return None
        return policy

    def put(self, tenant_id: UUID, policy: HarnessPolicy) -> None:
        self._entries[tenant_id] = (policy, self._clock() + self._ttl_s)

    def invalidate(self, tenant_id: UUID) -> None:
        self._entries.pop(tenant_id, None)

    def clear(self) -> None:
        self._entries.clear()


_cache = _HarnessPolicyCache()


async def resolve_tenant_harness_policy(
    db: AsyncSession | None, tenant_id: UUID | None
) -> HarnessPolicy:
    """Resolve a tenant's HarnessPolicy (TTL-cached). Fail-open to an empty policy.

    Returns HarnessPolicy() (the system-defaults path) when db / tenant_id is
    missing, the tenant row / meta_data["harness_policy"] is absent, or on any
    lookup error.
    """
    if db is None or tenant_id is None:
        return HarnessPolicy()
    cached = _cache.get(tenant_id)
    if cached is not None:
        return cached

    policy = HarnessPolicy()
    try:
        from sqlalchemy import select

        from infrastructure.db.models.identity import Tenant

        result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = result.scalar_one_or_none()
        if tenant is not None:
            raw = (tenant.meta_data or {}).get("harness_policy")
            if isinstance(raw, dict):
                policy = HarnessPolicy.from_dict(raw)
    except Exception:  # noqa: BLE001 — fail-open (mirrors resolve_tenant_model_policy)
        # A resolution failure must not break chat; the defaults path applies.
        return HarnessPolicy()

    _cache.put(tenant_id, policy)
    return policy


def invalidate_tenant_harness_policy(tenant_id: UUID) -> None:
    """Drop a tenant's cached policy (called by the admin PUT after a write)."""
    _cache.invalidate(tenant_id)


def reset_harness_policy_cache() -> None:
    """Test isolation hook (Risk Class C — module singleton across event loops)."""
    _cache.clear()
