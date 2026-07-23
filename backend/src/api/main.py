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
Last Modified: 2026-07-23

Modification History (newest-first):
    - 2026-07-23: Sprint 57.167 — _warn_business_domain_mock() at startup (de-Potemkin 1)
    - 2026-06-17: Sprint 57.135 — scheduled transcript-retention sweep job (billing-drainer mirror)
    - 2026-06-13: Sprint 57.112 — mount mfa router (TOTP enroll/confirm/verify; IAM Block C)
    - 2026-06-07: FIX-028 — _wire_sla_recorder() at startup (sla-report 500 fix; twin of FIX-022)
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
from api.v1.mfa import router as mfa_router
from api.v1.sessions import router as sessions_router
from api.v1.subagents import router as subagents_router
from api.v1.telemetry import router as telemetry_router
from api.v1.tenants import router as tenants_router
from api.v1.verification import router as verification_router
from infrastructure.db import dispose_engine
from platform_layer.middleware import RateLimitMiddleware, TenantContextMiddleware
from platform_layer.observability import (
    configure_json_logging,
    setup_opentelemetry,
    shutdown_opentelemetry,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

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


def _wire_sla_recorder() -> None:
    """Install the SLAMetricRecorder singleton at startup (fail-open).

    FIX-028: Sprint 56.3 built SLAMetricRecorder + SLAReportGenerator + the
    set/get/reset hooks + tests, and the chat router consumes the LENIENT
    maybe_get_sla_recorder() (silent no-op when unwired). But nothing in
    backend/src ever called set_sla_recorder() — only the 2 test files did — so
    the producer stayed unwired in production (AP-4: wired-but-never-activated,
    the twin of FIX-022's pricing loader). Consequence: the report endpoint's
    STRICT get_sla_recorder() (sla_reports.py — cache-miss generate path) raised
    RuntimeError → GET /admin/tenants/{id}/sla-report 500'd in real use while
    pytest stayed green (tests inject their own recorder).

    Creates a lazy redis.asyncio client from settings.redis_url (not connected
    here — the first ZADD/ZRANGE establishes the connection). Fail-open: on any
    error the singleton stays None and the chat router's maybe_get_sla_recorder()
    keeps no-op'ing rather than blocking startup; pure Redis, no DB / RLS needed
    (every metric key already carries tenant_id — cf. _wire_error_budget).
    """
    try:
        from redis.asyncio import Redis

        from core.config import get_settings
        from platform_layer.observability.sla_monitor import (
            SLAMetricRecorder,
            set_sla_recorder,
        )

        settings = get_settings()
        client = Redis.from_url(settings.redis_url)
        set_sla_recorder(SLAMetricRecorder(redis_client=client))
        logger.info("api.main: SLA recorder wired")
    except Exception:  # noqa: BLE001 — fail-open: never block startup on SLA recording
        logger.warning(
            "api.main: SLA recorder not wired; recording disabled (fail-open)",
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


def _warn_business_domain_mock() -> None:
    """Announce at startup whether the 18 business tools are MOCK or real.

    Sprint 57.167 (de-Potemkin 1): `business_domain_mode` defaults to "mock", so
    the default deployment answers business questions from a fabricated HTTP
    backend — and nothing anywhere said so. The reality audit (2026-06-26, re-scanned
    2026-07-15) named this the most trust-damaging Potemkin: an operator could run
    what looks like production and never learn the data is invented.

    Both branches log deliberately: silence must not be ambiguous, so "service"
    emits a positive confirmation rather than nothing. Fail-open like the sibling
    _wire_* helpers — a settings read must never block startup.
    """
    try:
        from core.config import get_settings

        mode = get_settings().business_domain_mode
        if mode == "mock":
            logger.warning(
                "api.main: BUSINESS DOMAIN IS MOCK — the 18 business tools "
                "(patrol/correlation/rootcause/audit/incident) return FABRICATED "
                "data from the mock backend, not real systems. Tool results are "
                'marked with "_mock": true. Set BUSINESS_DOMAIN_MODE=service for '
                "the DB-backed production pathway."
            )
        else:
            logger.info("api.main: business domain mode = service (DB-backed, real data)")
    except Exception:  # noqa: BLE001 — fail-open: never block startup on a settings read
        logger.warning("api.main: business domain mode not resolved (fail-open)", exc_info=True)


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


async def _transcript_retention_poll_loop(
    session_factory: "async_sessionmaker[AsyncSession]",
    interval_s: int,
    stop_event: asyncio.Event,
) -> None:
    """Run the per-tenant transcript-retention sweep every interval_s until stop_event is set.

    Fail-open: a sweep-cycle exception is logged and the loop continues (a transient DB flake
    must never kill the poller). The sweep runs ONCE at start, then every interval; the interval
    sleep is interrupted by stop_event for prompt shutdown. Mirrors _billing_outbox_poll_loop.
    """
    from platform_layer.transcripts.retention import run_transcript_retention_sweep

    while not stop_event.is_set():
        try:
            stats = await run_transcript_retention_sweep(session_factory)
            if stats.total_messages or stats.total_events or stats.tenants_failed:
                logger.info(
                    "api.main: transcript retention sweep — tenants=%d failed=%d "
                    "messages_deleted=%d events_deleted=%d",
                    stats.tenants_processed,
                    stats.tenants_failed,
                    stats.total_messages,
                    stats.total_events,
                )
        except Exception:  # noqa: BLE001 — fail-open: a flake must not kill the poller
            logger.exception("api.main: transcript retention sweep cycle failed")
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval_s)
        except (TimeoutError, asyncio.TimeoutError):
            pass  # interval elapsed → next cycle


async def _start_transcript_retention_job(app: FastAPI) -> None:
    """Start the background transcript-retention sweep poll loop (fail-open, DEFAULT OFF).

    Sprint 57.135 (57.134 follow-on #1): auto-enforces per-tenant transcript retention by
    deleting messages + message_events older than each tenant's tenants.retention_days every
    TRANSCRIPT_RETENTION_JOB_INTERVAL_S (default 86400 = daily). DESTRUCTIVE, so it is OPT-IN:
    disabled unless TRANSCRIPT_RETENTION_JOB_ENABLED=true (read as a plain env flag to dodge the
    get_settings() lru_cache timing trap, mirroring the billing drainer). The task + stop event
    are stored on app.state for shutdown cancellation.
    """
    if os.environ.get("TRANSCRIPT_RETENTION_JOB_ENABLED", "false").lower() != "true":
        logger.info("api.main: transcript retention job disabled (env; default off)")
        return
    try:
        from infrastructure.db.engine import get_session_factory

        interval_s = int(os.environ.get("TRANSCRIPT_RETENTION_JOB_INTERVAL_S", "86400"))
        stop_event = asyncio.Event()
        task = asyncio.create_task(
            _transcript_retention_poll_loop(get_session_factory(), interval_s, stop_event)
        )
        app.state.transcript_retention_stop = stop_event
        app.state.transcript_retention_task = task
        logger.info("api.main: transcript retention job started (interval=%ds)", interval_s)
    except Exception:  # noqa: BLE001 — fail-open: never block startup on the job
        logger.warning("api.main: transcript retention job not started (fail-open)", exc_info=True)


async def _warm_knowledge_index(app: FastAPI) -> None:
    """Build the process-wide knowledge vector index at startup — NO blocking ingest (fail-soft).

    Sprint 57.147 (per-tenant isolation): the index now ingests PER TENANT lazily on
    first search (each tenant → its own Qdrant collection from <root>/<tenant>/). A
    blocking all-corpus startup ingest no longer fits — there is no single tenant at
    startup, and embedding the full default corpus at boot is the separate
    AD-Knowledge-Connector-Ingest-Scale concern. We only memoize the singleton so a
    misconfiguration surfaces early; flag off / unconfigured → None → skip (zero added
    startup cost). Any Azure / Qdrant error is logged + swallowed so the agent degrades
    to the keyword path rather than blocking startup.
    """
    try:
        from api.v1.chat.knowledge_index import get_knowledge_vector_index

        index = get_knowledge_vector_index()
        if index is None:
            return
        logger.info("api.main: knowledge vector index ready (lazy per-tenant ingest)")
    except Exception:  # noqa: BLE001 — fail-soft: never block startup
        logger.warning("api.main: knowledge vector index warm skipped (fail-soft)", exc_info=True)


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
    _wire_sla_recorder()
    _wire_billing_outbox()
    _warn_business_domain_mock()
    await _start_billing_outbox_drainer(app)
    await _start_transcript_retention_job(app)
    await _warm_knowledge_index(app)
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
        # Sprint 57.135: stop the transcript-retention sweep poller (same lifecycle as
        # the billing drainer above) before OTel + engine teardown — the poller uses the DB.
        _ret_stop = getattr(app.state, "transcript_retention_stop", None)
        _ret_task = getattr(app.state, "transcript_retention_task", None)
        if _ret_stop is not None:
            _ret_stop.set()
        if _ret_task is not None:
            try:
                await asyncio.wait_for(_ret_task, timeout=10)
            except (TimeoutError, asyncio.TimeoutError, asyncio.CancelledError):
                _ret_task.cancel()
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
    app.include_router(mfa_router, prefix="/api/v1")
    app.include_router(invites_router, prefix="/api/v1")
    app.include_router(tenants_router, prefix="/api/v1")
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
