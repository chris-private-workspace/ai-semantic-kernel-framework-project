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
Last Modified: 2026-06-05

Modification History (newest-first):
    - 2026-06-05: Sprint 57.81 — _wire_error_budget() at startup (B-7 RedisBudgetStore wiring)
    - 2026-06-02: Sprint 57.70 Stage-1b — mount admin_agents router (agent_catalog CRUD)
    - 2026-05-31: FIX-022 — _wire_pricing_loader() at startup (cost_ledger §5.1 H1)
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

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, AsyncIterator

from dotenv import load_dotenv
from fastapi import FastAPI

from api.v1.admin.agents import router as admin_agents_router
from api.v1.admin.cost_summary import router as admin_cost_summary_router
from api.v1.admin.sla_reports import router as admin_sla_reports_router
from api.v1.admin.tenants import router as admin_tenants_router
from api.v1.audit import router as audit_router
from api.v1.auth import router as auth_router
from api.v1.chat import router as chat_router
from api.v1.governance import router as governance_router
from api.v1.health import router as health_router
from api.v1.invites import router as invites_router
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

if TYPE_CHECKING:
    from platform_layer.billing.billing_outbox import BillingOutboxDrainer

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
        from infrastructure.db.engine import get_session_factory
        from platform_layer.tenant.rate_limit_counter import (
            RedisRateLimitCounter,
            set_rate_limit_counter,
        )

        settings = get_settings()
        client = Redis.from_url(settings.redis_url)
        # Sprint 57.59: inject the DB session factory so the counter write-throughs
        # each window's live count to the durable rate_limits usage table (AP-4
        # close) + recovers from it on a Redis restart. Persistence is best-effort
        # + fail-open inside the counter; the Redis hot-path is unaffected.
        set_rate_limit_counter(RedisRateLimitCounter(client, session_factory=get_session_factory))
        logger.info("api.main: rate-limit counter wired")
    except Exception:  # noqa: BLE001 — fail-open: never block startup on rate limits
        logger.warning(
            "api.main: rate-limit counter not wired; enforcement disabled (fail-open)",
            exc_info=True,
        )


def _wire_pricing_loader() -> None:
    """Install the PricingLoader singleton at startup (fail-soft).

    FIX-022 (runtime-verification 2026-05-30 §5.1 H1): the chat router builds a
    per-request CostLedgerService ONLY when maybe_get_pricing_loader() is non-None
    (router.py — `if pricing_loader is not None`). Until this wiring, nothing in
    the app ever called set_pricing_loader(), so the loader stayed None, the
    CostLedgerService was never constructed, and the cost_ledger write was always
    skipped — a real billable LLM call persisted sessions + tool_calls but zero
    cost rows. Sprint 56.3 US-4 wired the router consumer but never the startup
    producer (AP-4: wired-but-never-activated).

    Loads config/llm_pricing.yml into a process-wide PricingLoader. Fail-soft: if
    the yaml is missing / malformed the loader stays None and cost-ledger writes
    degrade to a no-op (best-effort, same philosophy as the router's try/except
    around record_llm_call) rather than blocking startup.
    """
    try:
        from pathlib import Path

        from platform_layer.billing.pricing import PricingLoader, set_pricing_loader

        # main.py = backend/src/api/main.py → parents[2] = backend → backend/config/.
        pricing_yaml = Path(__file__).resolve().parents[2] / "config" / "llm_pricing.yml"
        loader = PricingLoader()
        loader.load_from_yaml(pricing_yaml)
        set_pricing_loader(loader)
        logger.info("api.main: pricing loader wired (%s)", pricing_yaml)
    except Exception:  # noqa: BLE001 — fail-soft: never block startup on pricing config
        logger.warning(
            "api.main: pricing loader not wired; cost ledger writes disabled (fail-soft)",
            exc_info=True,
        )


def _wire_error_budget() -> None:
    """Install the RedisBudgetStore singleton at startup (fail-open).

    Sprint 57.81 (B-7): the chat factory (make_chat_error_deps) builds the Cat 8
    TenantErrorBudget per request; without a shared store it used a fresh
    InMemoryBudgetStore each time → counters reset every request (budget
    effectively non-functional) and never shared across instances. This wires a
    process-wide RedisBudgetStore from settings.redis_url so the per-tenant
    error-budget counters accumulate (and are cross-instance correct). The
    TenantErrorBudget wrapper is stateless — all state lives in this store.

    Fail-open: if Redis is unavailable / misconfigured the store stays None and
    the factory falls back to InMemoryBudgetStore (budget degrades to per-request
    rather than blocking startup). Pure Redis — no DB session / RLS needed (the
    budget keys already carry tenant_id; cf. rate-limit counter's DB write-through
    which this deliberately does NOT copy).
    """
    try:
        from redis.asyncio import Redis

        from agent_harness.error_handling import RedisBudgetStore
        from core.config import get_settings
        from platform_layer.governance.error_budget_provider import set_budget_store

        settings = get_settings()
        client = Redis.from_url(settings.redis_url)
        set_budget_store(RedisBudgetStore(client))
        logger.info("api.main: error budget store wired")
    except Exception:  # noqa: BLE001 — fail-open: never block startup on error budget
        logger.warning(
            "api.main: error budget store not wired; budget per-request (fail-open)",
            exc_info=True,
        )


def _wire_billing_outbox() -> None:
    """Install the BillingOutboxService enqueue singleton at startup (fail-soft).

    Sprint 57.84 (C-15): the chat observer enqueues durable billing events via
    maybe_get_billing_outbox() (atomic with the request txn — replaces the
    best-effort direct cost_ledger write). The service is stateless (db passed
    per call) so this just registers a process-wide instance. Fail-soft: if
    registration fails, the chat observer's enqueue is skipped (degrade, like
    the pricing loader).
    """
    try:
        from platform_layer.billing.billing_outbox import (
            BillingOutboxService,
            set_billing_outbox,
        )

        set_billing_outbox(BillingOutboxService())
        logger.info("api.main: billing outbox enqueue service wired")
    except Exception:  # noqa: BLE001 — fail-soft: never block startup on the outbox
        logger.warning(
            "api.main: billing outbox enqueue service not wired (fail-soft)",
            exc_info=True,
        )


async def _billing_outbox_poll_loop(
    drainer: BillingOutboxDrainer,
    interval_s: int,
    stop_event: asyncio.Event,
) -> None:
    """Drain the billing outbox every interval_s until stop_event is set.

    Fail-open: a drain-cycle exception is logged and the loop continues (a
    transient DB flake must never kill the poller). Shutdown is prompt — the
    interval sleep is interrupted by stop_event.
    """
    while not stop_event.is_set():
        try:
            stats = await drainer.drain_once()
            if stats.materialized or stats.failed or stats.dead_lettered:
                logger.info(
                    "api.main: billing outbox drain — materialized=%d failed=%d dead=%d",
                    stats.materialized,
                    stats.failed,
                    stats.dead_lettered,
                )
        except Exception:  # noqa: BLE001 — fail-open: a flake must not kill the poller
            logger.exception("api.main: billing outbox drain cycle failed")
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval_s)
        except (TimeoutError, asyncio.TimeoutError):
            pass  # interval elapsed → next cycle


async def _start_billing_outbox_drainer(app: FastAPI) -> None:
    """Start the background billing-outbox drainer poll loop (fail-open).

    Sprint 57.84 (C-15): drains billing_outbox → cost_ledger every
    settings.billing_outbox_poll_interval_s. Disabled via env
    BILLING_OUTBOX_DRAINER_ENABLED=false (tests + ops kill switch; read as a
    plain env flag to dodge the get_settings() lru_cache timing trap). Needs the
    pricing loader (wired above); if absent the drainer is not started. The task
    + stop event are stored on app.state for shutdown cancellation.
    """
    if os.environ.get("BILLING_OUTBOX_DRAINER_ENABLED", "true").lower() != "true":
        logger.info("api.main: billing outbox drainer disabled (env)")
        return
    try:
        from core.config import get_settings
        from infrastructure.db.engine import get_session_factory
        from platform_layer.billing.billing_outbox import BillingOutboxDrainer
        from platform_layer.billing.pricing import maybe_get_pricing_loader

        pricing = maybe_get_pricing_loader()
        if pricing is None:
            logger.warning(
                "api.main: billing outbox drainer not started; pricing loader unavailable"
            )
            return
        settings = get_settings()
        drainer = BillingOutboxDrainer(
            get_session_factory(),
            pricing,
            batch=settings.billing_outbox_batch,
            max_retry=settings.billing_outbox_max_retry,
        )
        stop_event = asyncio.Event()
        task = asyncio.create_task(
            _billing_outbox_poll_loop(drainer, settings.billing_outbox_poll_interval_s, stop_event)
        )
        app.state.billing_outbox_stop = stop_event
        app.state.billing_outbox_task = task
        logger.info("api.main: billing outbox drainer started")
    except Exception:  # noqa: BLE001 — fail-open: never block startup on the drainer
        logger.warning("api.main: billing outbox drainer not started (fail-open)", exc_info=True)


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
    _wire_pricing_loader()
    _wire_error_budget()
    _wire_billing_outbox()
    await _start_billing_outbox_drainer(app)
    logger.info("api.main: startup complete")
    try:
        yield
    finally:
        # Sprint 57.84 (C-15): stop the billing-outbox drainer BEFORE OTel +
        # engine teardown (the poller uses the DB engine).
        _stop_event = getattr(app.state, "billing_outbox_stop", None)
        _drainer_task = getattr(app.state, "billing_outbox_task", None)
        if _stop_event is not None:
            _stop_event.set()
        if _drainer_task is not None:
            try:
                await asyncio.wait_for(_drainer_task, timeout=10)
            except (TimeoutError, asyncio.TimeoutError, asyncio.CancelledError):
                _drainer_task.cancel()
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
    app.include_router(invites_router, prefix="/api/v1")
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
    app.include_router(admin_agents_router, prefix="/api/v1")

    return app


# Module-level app instance — uvicorn imports this.
app = create_app()
