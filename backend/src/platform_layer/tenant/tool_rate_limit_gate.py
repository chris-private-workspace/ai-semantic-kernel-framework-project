"""
File: backend/src/platform_layer/tenant/tool_rate_limit_gate.py
Purpose: RedisToolRateLimitGate — Cat 2 tool-call budget adapter (Track B wiring seam).
Category: Phase 58.x SaaS / platform_layer.tenant
Scope: Sprint 57.58 (Track B) — RateLimits RuntimeEnforcement (Phase 58.x portfolio #1)

Description:
    Concrete adapter satisfying the Cat 2 tool layer's `RateLimitGate` protocol
    (declared structurally in agent_harness/tools/executor.py so the tool layer
    stays LLM-neutral + free of any platform/Redis import). This adapter lives
    in platform_layer because it is the only side that may touch the DB +
    RedisRateLimitCounter.

    Per tool call it enforces TWO resource keys against the tenant's configured
    rate limits (parsed from the {label, value} list):
      - `tool_calls.<tool_name>` — per-tool granularity (only if the tenant
        configured a limit for that specific tool).
      - `tool_calls` — the aggregate tool-call budget.

    Fail-open: any DB / Redis / parse error returns None (the call proceeds).
    Tool execution must NEVER be blocked by rate-limit infrastructure failure.

Key Components:
    - RedisToolRateLimitGate: RateLimitGate adapter (check returns Error | None)

Created: 2026-05-28 (Sprint 57.58)
Last Modified: 2026-05-28

Modification History (newest-first):
    - 2026-05-29: Sprint 57.60 — _load_tool_limits drops transitional meta_data fallback
    - 2026-05-28: Sprint 57.59 US-3 — _load_tool_limits reads config table (fallback meta_data)
    - 2026-05-28: Sprint 57.58 Track B — initial creation (tool-call rate gate)

Related:
    - agent_harness/tools/executor.py — RateLimitGate protocol + pre-call hook
    - platform_layer/tenant/rate_limit_config_store.py — config source of truth
    - platform_layer/tenant/rate_limit_counter.py — counter + {label,value} parser
    - platform_layer/middleware/rate_limit.py — HTTP-edge sibling (api_requests)
    - sprint-57-58-plan.md §4.2 (Cat 2 tool layer)
"""

from __future__ import annotations

import logging
from uuid import UUID

from agent_harness._contracts.errors import RateLimitExceededError
from infrastructure.db.engine import get_session_factory
from platform_layer.tenant._rate_limit_contracts import RateLimitCounter
from platform_layer.tenant.rate_limit_config_store import (
    RateLimitConfigStore,
    project_config_to_item,
)
from platform_layer.tenant.rate_limit_counter import parse_rate_limit_item

# RateLimitCounter ABC + parser are siblings under platform_layer/tenant/.

logger = logging.getLogger(__name__)

# Resource keys for the tool layer. Aggregate budget + per-tool granularity.
TOOL_CALLS_AGGREGATE = "tool_calls"
TOOL_CALLS_PREFIX = "tool_calls."


class RedisToolRateLimitGate:
    """Tool-call budget gate backed by RedisRateLimitCounter (fail-open)."""

    def __init__(self, counter: RateLimitCounter) -> None:
        self._counter = counter

    async def check(
        self,
        tenant_id: UUID,
        tool_name: str,
    ) -> RateLimitExceededError | None:
        """Return a RateLimitExceededError if over budget, else None (proceed)."""
        try:
            limits = await self._load_tool_limits(tenant_id)
        except Exception:  # noqa: BLE001 — fail-open: never block tools on infra error
            logger.warning(
                "tool_rate_limit_gate: limit load failed; failing open",
                exc_info=True,
            )
            return None

        # Resource keys this call consumes: the aggregate + this tool's specific
        # key (if the tenant configured one). Check the specific key first so an
        # over-limit per-tool budget surfaces the precise resource.
        candidates = [f"{TOOL_CALLS_PREFIX}{tool_name}", TOOL_CALLS_AGGREGATE]
        for resource in candidates:
            spec = limits.get(resource)
            if spec is None:
                continue
            limit, window_seconds = spec
            try:
                decision = await self._counter.check_and_increment(
                    tenant_id, resource, window_seconds, limit
                )
            except Exception:  # noqa: BLE001 — fail-open on counter error
                logger.warning(
                    "tool_rate_limit_gate: counter error; failing open",
                    exc_info=True,
                )
                return None
            if not decision.allowed:
                return RateLimitExceededError(
                    resource=resource,
                    limit=limit,
                    retry_after=decision.retry_after,
                )
        return None

    async def _load_tool_limits(self, tenant_id: UUID) -> dict[str, tuple[int, int]]:
        """Map resource -> (limit, window_seconds) for tool_calls* resources.

        Source of truth (Sprint 57.59): the `rate_limit_configs` table, projected
        back to the {label, value} shape, then parsed. When the table has no config
        rows for this tenant, no limits load (empty map) — enforcement never applies
        phantom defaults.

        Keeps only parsed items whose resource is the aggregate `tool_calls` or a
        per-tool `tool_calls.<name>` key. The config-store query filters by
        tenant_id (鐵律 2).
        """
        factory = get_session_factory()
        async with factory() as session:
            store = RateLimitConfigStore()
            configs = await store.list_configs(session, tenant_id)
            raw: list[object] = [project_config_to_item(c) for c in configs]
        out: dict[str, tuple[int, int]] = {}
        for item in raw:
            parsed = parse_rate_limit_item(item)
            if parsed is None:
                continue
            if parsed.resource == TOOL_CALLS_AGGREGATE or parsed.resource.startswith(
                TOOL_CALLS_PREFIX
            ):
                out[parsed.resource] = (parsed.limit, parsed.window_seconds)
        return out
