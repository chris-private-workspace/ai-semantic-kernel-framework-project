"""
File: backend/src/platform_layer/middleware/rate_limit.py
Purpose: RateLimitMiddleware — per-request runtime enforcement of tenant rate limits.
Category: Platform layer / Middleware (cross-cutting; ranges 9 governance + multi-tenancy)
Scope: Sprint 57.58 (Track A) — RateLimits RuntimeEnforcement (Phase 58.x portfolio #1)

Description:
    Transforms the tenant's `rate_limit_configs` rows (the Sprint 57.59 source of
    truth; admin-display-only before runtime enforcement) into runtime governance.
    For every authenticated request:

      1. Bypass when there is no tenant scope (internal calls) OR the JWT
         carries an `admin` / `service` role (operators are not throttled).
      2. Bypass exempt path prefixes (health probes, the auth gateway itself,
         the rate-limit usage endpoint — polling it must not consume capacity).
      3. Load the tenant's {label, value} rate-limit list (per-request DB read),
         parse the HTTP-relevant `api_requests` items into numeric limits.
      4. For each matching item, atomic sliding-window check via the shared
         RedisRateLimitCounter (DRY with Track B tool layer).
      5. Over-limit -> 429 with {error, resource, limit, window,
         retry_after_seconds} + Retry-After / X-RateLimit-* headers.

    Fail-open by design: if Redis / the Lua script / the DB read errors, the
    middleware logs a warning and ALLOWS the request. Rate limiting must NEVER
    take the service down (R1 in the sprint plan).

    Ordering: registered immediately AFTER TenantContextMiddleware in
    api/main.py — it depends on request.state.{tenant_id, roles} that the
    tenant-context middleware sets from the JWT.

Key Components:
    - RateLimitMiddleware: BaseHTTPMiddleware enforcing per-tenant HTTP limits
    - HTTP_RESOURCE: "api_requests" (the resource key for edge HTTP requests)

Created: 2026-05-28 (Sprint 57.58)
Last Modified: 2026-05-28

Modification History (newest-first):
    - 2026-05-29: Sprint 57.60 — _load_rate_limits drops transitional meta_data fallback
    - 2026-05-28: Sprint 57.59 US-3 — _load_rate_limits reads config table (fallback meta_data)
    - 2026-05-28: Sprint 57.58 Track A — initial creation (RateLimits RuntimeEnforcement)

Related:
    - platform_layer/middleware/tenant_context.py — sets request.state (runs first)
    - platform_layer/tenant/rate_limit_config_store.py — config source of truth
    - platform_layer/tenant/rate_limit_counter.py — RedisRateLimitCounter + parser
    - platform_layer/tenant/_rate_limit_contracts.py — RateLimitDecision
    - api/main.py — registration order (after TenantContextMiddleware)
    - sprint-57-58-plan.md §4.1 / §4.5 (bypass logic)
"""

from __future__ import annotations

import logging
from uuid import UUID

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from infrastructure.db.engine import get_session_factory
from platform_layer.tenant.rate_limit_config_store import (
    RateLimitConfigStore,
    project_config_to_item,
)
from platform_layer.tenant.rate_limit_counter import (
    maybe_get_rate_limit_counter,
    parse_rate_limit_item,
)

logger = logging.getLogger(__name__)

# Resource key for edge HTTP requests. Tool calls (Track B) use tool_calls.*.
HTTP_RESOURCE = "api_requests"

# Roles that skip enforcement entirely (operators / internal service callers).
_BYPASS_ROLES: frozenset[str] = frozenset({"admin", "service"})


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-tenant HTTP rate-limit enforcement (sliding window, fail-open)."""

    # Paths that never count against a tenant's rate limit:
    #   - /api/v1/health         : k8s probes
    #   - /api/v1/auth/*         : the auth gateway establishes the session
    #   - /api/v1/telemetry      : anonymous beacons (no tenant scope)
    # The usage endpoint is excluded via _is_usage_path (suffix match) so admin
    # polling of live usage does not itself consume capacity.
    EXEMPT_PATH_PREFIXES: tuple[str, ...] = (
        "/api/v1/health",
        "/api/v1/auth/login",
        "/api/v1/auth/callback",
        "/api/v1/auth/dev-login",
        "/api/v1/auth/logout",
        "/api/v1/telemetry",
    )

    @staticmethod
    def _is_exempt_path(path: str) -> bool:
        for prefix in RateLimitMiddleware.EXEMPT_PATH_PREFIXES:
            if path == prefix or path.startswith(prefix + "/"):
                return True
        # The live-usage GET endpoint is read-only admin display — polling it
        # must not perturb the enforcement counter.
        return path.endswith("/rate-limits/usage")

    async def dispatch(self, request, call_next):  # type: ignore[no-untyped-def]
        # --- 1. Bypass: exempt path ---
        if self._is_exempt_path(request.url.path):
            return await call_next(request)

        # --- 2. Bypass: no tenant scope (internal call) ---
        tenant_id = getattr(request.state, "tenant_id", None)
        if not isinstance(tenant_id, UUID):
            return await call_next(request)

        # --- 3. Bypass: admin / service role ---
        roles = getattr(request.state, "roles", None) or []
        if _BYPASS_ROLES & set(roles):
            return await call_next(request)

        # --- 4. Counter not wired (dev / pre-startup) -> fail-open ---
        counter = maybe_get_rate_limit_counter()
        if counter is None:
            return await call_next(request)

        # --- 5. Enforce. Any failure here is fail-open (log + allow). ---
        try:
            items = await self._load_rate_limits(tenant_id)
            for raw_item in items:
                parsed = parse_rate_limit_item(raw_item)
                # Only HTTP-edge resource applies at the middleware layer; tool
                # call limits are enforced in the Cat 2 tool layer (Track B).
                if parsed is None or parsed.resource != HTTP_RESOURCE:
                    continue
                decision = await counter.check_and_increment(
                    tenant_id,
                    parsed.resource,
                    parsed.window_seconds,
                    parsed.limit,
                )
                if not decision.allowed:
                    return JSONResponse(
                        status_code=429,
                        content={
                            "error": "rate_limit_exceeded",
                            "resource": parsed.resource,
                            "limit": parsed.limit,
                            "window": parsed.window_seconds,
                            "retry_after_seconds": decision.retry_after,
                        },
                        headers={
                            "Retry-After": str(decision.retry_after),
                            "X-RateLimit-Limit": str(parsed.limit),
                            "X-RateLimit-Remaining": str(decision.remaining),
                            "X-RateLimit-Reset": str(decision.reset_at),
                        },
                    )
        except Exception:  # noqa: BLE001 — fail-open: rate limits MUST NOT break service
            logger.warning(
                "rate_limit_middleware: enforcement error; failing open",
                exc_info=True,
            )

        return await call_next(request)

    async def _load_rate_limits(self, tenant_id: UUID) -> list[object]:
        """Load this tenant's {label, value} rate-limit list (empty on miss).

        Source of truth (Sprint 57.59): the `rate_limit_configs` table, projected
        back to the {label, value} shape parse_rate_limit_item expects. When the
        table has no config rows for this tenant, enforcement loads nothing (empty
        list) — enforcement never applies phantom defaults.

        Per-request DB read is acceptable for v1 (single tenant-scoped lookup;
        volume bounded by the request rate we are limiting). The config-store query
        filters by tenant_id (鐵律 2) — no SET LOCAL needed for this read.
        """
        factory = get_session_factory()
        async with factory() as session:
            store = RateLimitConfigStore()
            configs = await store.list_configs(session, tenant_id)
            if configs:
                return [project_config_to_item(c) for c in configs]
        return []
