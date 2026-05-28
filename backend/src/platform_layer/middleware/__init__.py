"""
platform_layer.middleware — request-scoped middleware + dependencies.

Sprint 49.3 Day 4.4 introduces:
    - TenantContextMiddleware: extracts X-Tenant-Id header → request.state
    - get_db_session_with_tenant: FastAPI dependency that SET LOCAL
      app.tenant_id per-request (works with RLS policies in 0009)

Per .claude/rules/multi-tenant-data.md 鐵律 3, every business endpoint
must depend on get_db_session_with_tenant (not the raw get_db_session)
so RLS policies actually receive a tenant_id at query time.

Future Sprint 49.4+ will replace the X-Tenant-Id header path with JWT
extraction; the middleware contract (request.state.tenant_id) stays
the same so endpoint dependencies don't change.
"""

from __future__ import annotations

from platform_layer.middleware.rate_limit import RateLimitMiddleware
from platform_layer.middleware.tenant_context import (
    TenantContextMiddleware,
    get_db_session_with_tenant,
)

__all__ = [
    "RateLimitMiddleware",
    "TenantContextMiddleware",
    "get_db_session_with_tenant",
]
