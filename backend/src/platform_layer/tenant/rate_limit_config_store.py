"""
File: backend/src/platform_layer/tenant/rate_limit_config_store.py
Purpose: RateLimitConfigStore — CRUD + {label,value} projection over rate_limit_configs.
Category: Phase 58.x SaaS / platform_layer.tenant
Scope: Sprint 57.59 (US-2) — RateLimits config two-table split (AP-4 Potemkin close)

Description:
    Durable config store backing the admin GET/PUT /rate-limits endpoints. Replaces
    the Sprint 57.48-57.58 tenant.meta_data["rate_limits"] JSONB path as the source
    of truth, projecting config rows back to the unchanged admin API {label, value}
    shape so the frontend is untouched.

    The store owns the parse/project mapping between the API display shape
    ({"label": "API requests", "value": "100 / min"}) and the normalised columns
    (resource_type / window_type / quota). The mapping is kept consistent with
    platform_layer.tenant.rate_limit_counter.parse_rate_limit_item so the migration-
    seeded rows and live-written rows agree.

    Composite-replace semantics (mirrors Sprint 57.57 PUT): replace_configs takes
    the COMPLETE desired override list — it deletes the tenant's existing config
    rows and inserts the parsed payload, so an empty list clears all overrides.
    Unparseable items (e.g. "50 concurrent", malformed) are skipped (fail-open).

    Session injection: methods take the caller's AsyncSession directly (the admin
    endpoint passes its request session) so the store participates in the endpoint's
    transaction + audit chain without owning connection lifecycle.

Key Components:
    - RateLimitConfigStore: list_configs / replace_configs over rate_limit_configs
    - parse_config_item: {label, value} dict -> (resource_type, window_type, quota)
    - project_config_to_item: RateLimitConfig row -> {label, value} dict

Created: 2026-05-28 (Sprint 57.59 US-2)
Last Modified: 2026-05-28

Modification History (newest-first):
    - 2026-05-29: Sprint 57.61 — add is_recognized_rate_limit_value PUT-time validator predicate
    - 2026-05-28: Sprint 57.59 US-2 — initial creation (config store + projection)

Related:
    - infrastructure/db/models/api_keys.py:RateLimitConfig — ORM model
    - 0019_rate_limit_configs.py — migration (inline parse mirrors this store)
    - platform_layer/tenant/rate_limit_counter.py:parse_rate_limit_item — sibling parser
    - api/v1/admin/tenants.py — GET/PUT /rate-limits consumers
    - .claude/rules/multi-tenant-data.md 鐵律 2 (all queries filter by tenant_id)
"""

from __future__ import annotations

import re
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.models.api_keys import RateLimitConfig

# === {label, value} <-> columns mapping ================================
# Kept identical to rate_limit_counter.parse_rate_limit_item /  label_to_resource
# so config rows written here, seeded by the migration, and parsed by the runtime
# counter all agree. The reverse map yields canonical labels for the three known
# resources so a PUT -> GET round-trip on them is byte-identical; custom labels
# round-trip through a slug + humanise (title-case) which is stable but normalised.
_LABEL_TO_RESOURCE: dict[str, str] = {
    "api requests": "api_requests",
    "tool calls": "tool_calls",
    "sse connections": "sse_connections",
}
_RESOURCE_TO_LABEL: dict[str, str] = {
    "api_requests": "API requests",
    "tool_calls": "Tool calls",
    "sse_connections": "SSE connections",
}

# Canonical display window units stored in window_type.
_WINDOW_ALIASES: dict[str, str] = {
    "sec": "sec",
    "second": "sec",
    "min": "min",
    "minute": "min",
    "hour": "hour",
    "hr": "hour",
    "day": "day",
}

# e.g. "100 / min", "1,000 / minute". "50 concurrent" does NOT match (skipped).
_VALUE_RE = re.compile(r"^\s*([\d,]+)\s*/\s*([a-zA-Z]+)\s*$")

# Display-only concurrency pattern (e.g. "50 concurrent") — recognized + accepted
# by the admin validator but NOT enforceable (no time window), so the runtime
# parsers skip it. Kept here next to parse_config_item so the {label,value} domain
# logic stays in one module (no 4th regex copy beyond this one new pattern).
_CONCURRENCY_RE = re.compile(r"^\s*[\d,]+\s+concurrent\s*$", re.IGNORECASE)


def is_recognized_rate_limit_value(value: str) -> tuple[bool, str | None]:
    """Validate an admin-supplied rate-limit display value.

    Accepts: enforceable rate 'N / <sec|min|hour|day>' OR display-only 'N concurrent'.
    Rejects everything else with a human reason. Broader than parse_config_item
    (which only recognizes the enforceable rate) because the admin UI legitimately
    carries the non-enforceable 'N concurrent' default (DEFAULT_RATE_LIMITS SSE row).

    Public so the RateLimitsUpsertRequest validator (tenants.py) + tests reuse it;
    used at PUT-time so a malformed value returns a clear 422 instead of being
    silently skipped by replace_configs (which keeps its fail-open skip).
    """
    v = (value or "").strip()
    if not v:
        return False, "value is empty"
    m = _VALUE_RE.match(v)
    if m:
        raw_quota, raw_window = m.group(1), m.group(2).lower()
        if raw_window not in _WINDOW_ALIASES:
            return False, f"unsupported window '{m.group(2)}' (supported: sec, min, hour, day)"
        try:
            quota = int(raw_quota.replace(",", ""))
        except ValueError:
            return False, "quota is not a number"
        if quota <= 0:
            return False, "quota must be a positive number"
        return True, None
    if _CONCURRENCY_RE.match(v):
        return True, None  # display-only; not time-windowed, not enforced
    return False, "value must be 'N / <sec|min|hour|day>' or 'N concurrent'"


def _label_to_resource(label: str) -> str:
    """Canonical resource key for a display label (slug fallback for custom)."""
    key = label.strip().lower()
    if key in _LABEL_TO_RESOURCE:
        return _LABEL_TO_RESOURCE[key]
    slug = re.sub(r"[^a-z0-9]+", "_", key).strip("_")
    return slug or "unknown"


def _resource_to_label(resource_type: str) -> str:
    """Display label for a canonical resource key (humanise slug for custom)."""
    if resource_type in _RESOURCE_TO_LABEL:
        return _RESOURCE_TO_LABEL[resource_type]
    return resource_type.replace("_", " ").strip().capitalize() or resource_type


def parse_config_item(item: object) -> tuple[str, str, int] | None:
    """Parse a {label, value} dict into (resource_type, window_type, quota).

    Returns None for non-dict, missing label, non-rate value (e.g. "50
    concurrent"), unknown window alias, or non-positive quota — callers skip
    these (fail-open; a malformed admin config never blocks).
    """
    if not isinstance(item, dict):
        return None
    label = str(item.get("label", ""))
    value = str(item.get("value", ""))
    if not label:
        return None
    m = _VALUE_RE.match(value)
    if m is None:
        return None
    raw_quota, raw_window = m.group(1), m.group(2).lower()
    window_type = _WINDOW_ALIASES.get(raw_window)
    if window_type is None:
        return None
    try:
        quota = int(raw_quota.replace(",", ""))
    except ValueError:
        return None
    if quota <= 0:
        return None
    return _label_to_resource(label), window_type, quota


def project_config_to_item(config: RateLimitConfig) -> dict[str, str]:
    """Project a config row back to the admin API {label, value} display shape.

    Quota is rendered with a thousands separator (e.g. 8888 -> "8,888") so the
    round-trip matches the admin UI display convention (DEFAULT_RATE_LIMITS uses
    "1,000 / min") and the {label, value} strings the frontend originally sent.
    """
    return {
        "label": _resource_to_label(config.resource_type),
        "value": f"{config.quota:,} / {config.window_type}",
    }


class RateLimitConfigStore:
    """Durable per-tenant RateLimits config over the rate_limit_configs table."""

    async def list_configs(self, session: AsyncSession, tenant_id: UUID) -> list[RateLimitConfig]:
        """Return this tenant's config rows ordered by (resource_type, window_type).

        Multi-tenant rule (鐵律 2): every query filters by tenant_id.
        """
        result = await session.execute(
            select(RateLimitConfig)
            .where(RateLimitConfig.tenant_id == tenant_id)
            .order_by(RateLimitConfig.resource_type, RateLimitConfig.window_type)
        )
        return list(result.scalars().all())

    async def replace_configs(
        self,
        session: AsyncSession,
        tenant_id: UUID,
        items: list[dict[str, str]],
    ) -> list[RateLimitConfig]:
        """Composite-replace this tenant's config with the parsed payload items.

        Deletes the tenant's existing config rows then inserts the parsed payload
        (mirrors Sprint 57.57 PUT composite-replace). An empty list clears all.
        Unparseable items are skipped; duplicate (resource_type, window_type) within
        the payload is de-duped last-wins so the unique constraint never trips.
        Flushes (does NOT commit) so the caller controls the transaction + audit.
        Returns the freshly-listed config rows (post-flush) for response projection.
        """
        # Delete-all for this tenant (multi-tenant rule: scoped by tenant_id).
        await session.execute(delete(RateLimitConfig).where(RateLimitConfig.tenant_id == tenant_id))
        await session.flush()

        deduped: dict[tuple[str, str], int] = {}
        for item in items:
            parsed = parse_config_item(item)
            if parsed is None:
                continue
            resource_type, window_type, quota = parsed
            deduped[(resource_type, window_type)] = quota

        for (resource_type, window_type), quota in deduped.items():
            session.add(
                RateLimitConfig(
                    tenant_id=tenant_id,
                    resource_type=resource_type,
                    window_type=window_type,
                    quota=quota,
                )
            )
        await session.flush()

        return await self.list_configs(session, tenant_id)
