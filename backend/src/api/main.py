"""
File: backend/src/api/main.py
Purpose: FastAPI app entrypoint — mounts routers + middleware + OTel + JSON logger.
Category: api (HTTP boundary)
Scope: Phase 49 / Sprint 49.4 Day 5

Description:
    Process entrypoint for the V2 backend. Run via:

        uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

    What this wires:
    - JSON logging (configure_json_logging) — early so all subsequent log lines are structured
    - OTel SDK (setup_opentelemetry) — TracerProvider + MeterProvider +
      FastAPI/SQLAlchemy/Redis instrumentation
    - TenantContextMiddleware — extracts X-Tenant-Id → request.state.tenant_id (49.3 Day 4.4)
    - api/v1 routers (health for now; chat / governance / hitl land in 50.2+)
    - Lifespan: setup on startup, shutdown_opentelemetry + dispose_engine on shutdown

    NOT in scope this sprint:
    - JWT extraction (replaces X-Tenant-Id header in 49.5+)
    - Auth / API key middleware (Phase 53.4)
    - Rate-limit middleware (Phase 49.3 schema is in place; enforcement Phase 53.4)
    - Static / CORS config (depends on frontend deploy decision; Phase 55)

Created: 2026-04-29 (Sprint 49.4 Day 5)
Last Modified: 2026-04-29

Modification History (newest-first):
    - 2026-05-10: Sprint 57.13 US-B4 — mount telemetry router (frontend beacons; anonymous)
    - 2026-05-09: Sprint 57.7 US-A2 — mount auth router (3 OIDC PKCE endpoints; WorkOS skeleton)
    - 2026-05-08: Sprint 57.6 US-2 — _lifespan() autoload .env via dotenv (closes AD-Reality-2)
    - 2026-05-06: Sprint 56.1 — mount admin_tenants router (POST /api/v1/admin/tenants)
    - 2026-05-04: Mount governance router (Sprint 53.5 US-1) — GET /governance/approvals
        + POST /governance/approvals/{id}/decide (approver RBAC + tenant isolation).
    - 2026-05-04: Mount audit router (Sprint 53.5 US-5+US-6) — GET /audit/log
        + GET /audit/verify-chain (auditor RBAC + tenant isolation).
    - 2026-04-30: Mount chat router (Sprint 50.2 Day 1.5) — POST /chat SSE +
        sessions endpoints.
    - 2026-04-29: Initial creation (Sprint 49.4 Day 5)

Related:
    - api/v1/health.py — first router mounted
    - platform_layer/middleware/tenant_context.py
    - platform_layer/observability/setup.py
    - platform_layer/observability/logger.py
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from dotenv import load_dotenv
from fastapi import FastAPI

from api.v1.admin.cost_summary import router as admin_cost_summary_router
from api.v1.admin.sla_reports import router as admin_sla_reports_router
from api.v1.admin.tenants import router as admin_tenants_router
from api.v1.audit import router as audit_router
from api.v1.auth import router as auth_router
from api.v1.chat import router as chat_router
from api.v1.governance import router as governance_router
from api.v1.health import router as health_router
from api.v1.loops import router as loops_router
from api.v1.memory import router as memory_router
from api.v1.sessions import router as sessions_router
from api.v1.subagents import router as subagents_router
from api.v1.telemetry import router as telemetry_router
from api.v1.verification import router as verification_router
from infrastructure.db import dispose_engine
from platform_layer.middleware import RateLimitMiddleware, TenantContextMiddleware
from platform_layer.observability import (
    configure_json_logging,
    setup_opentelemetry,
    shutdown_opentelemetry,
)

logger = logging.getLogger(__name__)


def _wire_rate_limit_counter() -> None:
    """Install the RedisRateLimitCounter singleton at startup (fail-open).

    Sprint 57.58 Track A: creates a redis.asyncio client from settings.redis_url
    and registers it so RateLimitMiddleware (and the Cat 2 tool layer) can
    enforce per-tenant limits. If Redis is unavailable / misconfigured the
    counter stays None and the middleware fails open (rate limits MUST NOT break
    the service). The client is created lazily here (not connected) — the first
    Lua script call establishes the connection; connection errors there are also
    caught by the middleware's fail-open path.
    """
    try:
        from redis.asyncio import Redis

        from core.config import get_settings
        from platform_layer.tenant.rate_limit_counter import (
            RedisRateLimitCounter,
            set_rate_limit_counter,
        )

        settings = get_settings()
        client = Redis.from_url(settings.redis_url)
        set_rate_limit_counter(RedisRateLimitCounter(client))
        logger.info("api.main: rate-limit counter wired")
    except Exception:  # noqa: BLE001 — fail-open: never block startup on rate limits
        logger.warning(
            "api.main: rate-limit counter not wired; enforcement disabled (fail-open)",
            exc_info=True,
        )


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup: load .env + structured logging + OTel SDK. Shutdown: flush + dispose engine."""
    # Sprint 57.6 US-2 (R2 / 57.5 D-20): autoload .env so AZURE_OPENAI_API_KEY etc.
    # populate process env before settings / adapter initialization. No-op if .env
    # already loaded by external process manager (e.g. docker-compose env_file).
    load_dotenv()
    configure_json_logging()
    setup_opentelemetry(app)
    _wire_rate_limit_counter()
    logger.info("api.main: startup complete")
    try:
        yield
    finally:
        await shutdown_opentelemetry()
        await dispose_engine()
        logger.info("api.main: shutdown complete")


def create_app() -> FastAPI:
    """Build the FastAPI app. Factory pattern so tests can swap config easily."""
    app = FastAPI(
        title="IPA Platform V2",
        version="2.0.0-alpha",
        description="V2 11+1 category agent harness — server-side, LLM-provider-neutral.",
        lifespan=_lifespan,
    )

    # Middleware (Starlette runs them outside-in / LIFO: the LAST added runs
    # FIRST at request time). We add RateLimitMiddleware BEFORE
    # TenantContextMiddleware so that TenantContextMiddleware runs first and
    # populates request.state.{tenant_id, roles} that RateLimitMiddleware reads.
    # Net request-time order: TenantContext -> RateLimit -> routes.
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(TenantContextMiddleware)

    # Routers: api/v1.
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(telemetry_router, prefix="/api/v1")
    app.include_router(chat_router, prefix="/api/v1")
    app.include_router(audit_router, prefix="/api/v1")
    app.include_router(verification_router, prefix="/api/v1")
    app.include_router(loops_router, prefix="/api/v1")
    app.include_router(memory_router, prefix="/api/v1")
    app.include_router(sessions_router, prefix="/api/v1")
    app.include_router(subagents_router, prefix="/api/v1")
    app.include_router(governance_router, prefix="/api/v1")
    app.include_router(admin_tenants_router, prefix="/api/v1")
    app.include_router(admin_sla_reports_router, prefix="/api/v1")
    app.include_router(admin_cost_summary_router, prefix="/api/v1")

    return app


# Module-level app instance — uvicorn imports this.
app = create_app()
