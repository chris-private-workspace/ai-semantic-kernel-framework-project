"""
File: backend/src/api/v1/chat/router.py
Purpose: HTTP entrypoint for the V2 main agent flow — POST /chat (SSE) + GET sessions.
Category: api/v1/chat
Scope: Phase 50 / Sprint 50.2 (Day 1.5) — Sprint 52.5 Day 2 (P0 #11+#12 wiring)

Description:
    Three endpoints, all gated by `Depends(get_current_tenant)` (single
    canonical source: JWT-decoded tenant_id from request.state, populated
    by TenantContextMiddleware):

    - POST /api/v1/chat/                   → starts AgentLoopImpl.run() and
                                             streams LoopEvents as SSE.
    - GET  /api/v1/chat/sessions/{id}      → returns running/completed/cancelled
                                             status for a known session of THIS tenant.
    - POST /api/v1/chat/sessions/{id}/cancel → flips status to "cancelled" and
                                             signals cancel_event for THIS tenant.

    POST /chat orchestration (per Sprint 52.5 P0 #11+#12):
        1. JWT middleware populates request.state.tenant_id → Depends extracts.
        2. Parse ChatRequest (mode + message).
        3. Generate / accept session_id; register in SessionRegistry under tenant.
        4. Create root TraceContext(tenant_id=current_tenant, session_id=...).
        5. build_handler(mode, message) — returns wired AgentLoopImpl.
        6. Stream loop.run(trace_context=root_ctx) events through
           serialize_loop_event + format_sse_message.
        7. mark_completed on natural termination; raise propagates as 500.

    Cross-tenant attempts return 404 — never reveal whether the session
    exists under a different tenant (per multi-tenant-data.md 鐵律).

    Phase 50.2 keeps everything in-process. Phase 53.1 will fork the loop
    execution into a worker pool (Temporal / Celery) — at that point the
    POST endpoint becomes a session-creation + SSE-attach pair, and the
    actual loop run lives in the worker.

Created: 2026-04-30 (Sprint 50.2 Day 1.5)
Last Modified: 2026-05-31

Modification History (newest-first):
    - 2026-05-31: FIX-022 §6.2 — consolidate gpt-5.4 pricing fallback into named const
    - 2026-05-10: Sprint 57.7 US-R1 — sessions + tool_calls observer (AD-Reality-3a/3b)
    - 2026-05-08: Sprint 57.6 US-3 — audit_log observer at LoopCompleted (AD-Reality-3-audit_log)
    - 2026-05-06: Sprint 56.3 Day 3 — wire Cost Ledger LLM + tool hooks (US-4)
    - 2026-05-06: Sprint 56.3 Day 1 — wire SLA span observer (US-1 — Cat 12 SLA recording)
    - 2026-05-06: Sprint 56.2 Day 2 — quota pre-call estimate + post-call reconcile (US-2 + US-3)
    - 2026-05-06: Sprint 56.2 Day 1 — real Tracer wired (closes AD-Cat12-BusinessObs)
    - 2026-05-06: Sprint 56.1 Day 2 — pre-stream QuotaEnforcer.check_and_reserve gate (US-2)
    - 2026-05-05: Sprint 55.5 Day 1 — wire run_with_verification at L197 (AD-Cat10-Wire-1; Option E)
    - 2026-05-04: Sprint 55.2 — BusinessServiceFactory per-request wiring (AD-BizDomain-1)
    - 2026-05-04: Sprint 53.6 US-4 — ServiceFactory through build_handler (closes AD-Front-2)
    - 2026-05-01: Sprint 52.5 P0 #11+#12 — Depends(get_current_tenant) + root TraceContext + 404
    - 2026-04-30: Sprint 50.2 Day 1.5 — initial: POST /chat SSE + GET/cancel sessions

Related:
    - .schemas (ChatRequest / ChatSessionResponse)
    - .handler (build_handler)
    - .sse (serialize_loop_event / format_sse_message — emits trace_id)
    - .session_registry (tenant-scoped storage)
    - api/main.py (mounts this router; installs TenantContextMiddleware)
    - platform_layer/identity (Depends source)
    - claudedocs/5-status/V2-AUDIT-W3-2-PHASE50-2.md (audit source)
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from collections.abc import AsyncIterator
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from agent_harness._contracts import LoopCompleted, TraceContext
from agent_harness._contracts.events import ToolCallExecuted
from agent_harness.observability._abc import Tracer
from agent_harness.verification import VerifierRegistry, run_with_verification
from business_domain._service_factory import BusinessServiceFactory
from core.config import get_settings
from infrastructure.db.audit_helper import append_audit
from infrastructure.db.repositories import SessionRepository, ToolCallRepository
from infrastructure.db.session import get_db_session
from platform_layer.billing import (
    CostLedgerService,
    PricingLoader,
    maybe_get_pricing_loader,
)
from platform_layer.governance.service_factory import (
    ServiceFactory,
    get_service_factory,
)
from platform_layer.identity import get_current_tenant
from platform_layer.identity.auth import get_current_user_id
from platform_layer.observability import (
    SLAMetricRecorder,
    classify_loop_complexity,
    get_tracer,
    maybe_get_sla_recorder,
)
from platform_layer.tenant.quota import (
    QuotaEnforcer,
    QuotaExceededError,
    maybe_get_quota_enforcer,
)

from .handler import build_handler
from .schemas import ChatRequest, ChatSessionResponse
from .session_registry import SessionRegistry, get_default_registry
from .sse import format_sse_message, serialize_loop_event

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])

# FIX-022 §6.2 (runtime-verification 2026-05-30): fallback model identity used for
# cost-ledger pricing when a LoopCompleted event carries no model (early-termination
# paths). Consolidated here from a bare literal so the app's priced-default model
# lives in ONE place. NOTE the deployment/model/pricing identities are currently
# mismatched (4-way): .env AZURE_OPENAI_DEPLOYMENT_NAME=gpt-5.2 vs config.model_name
# default gpt-4o vs this fallback gpt-5.4 vs llm_pricing.yml keys {gpt-4o-mini,
# gpt-5.4}. Only gpt-5.4 is actually priced — gpt-4o / gpt-5.2 resolve to $0 rows
# (get_llm_pricing -> None). Aligning the real deployment model + its USD pricing in
# llm_pricing.yml is the deferred follow-up (FIX-022 §6.2 "定價數據另案").
_FALLBACK_PRICING_MODEL = "gpt-5.4"


@router.post("/", status_code=status.HTTP_200_OK)
async def chat(
    req: ChatRequest,
    current_tenant: UUID = Depends(get_current_tenant),
    current_user: UUID = Depends(get_current_user_id),
    factory: ServiceFactory = Depends(get_service_factory),
    db: AsyncSession = Depends(get_db_session),
    quota_enforcer: QuotaEnforcer | None = Depends(maybe_get_quota_enforcer),
    sla_recorder: SLAMetricRecorder | None = Depends(maybe_get_sla_recorder),
    pricing_loader: PricingLoader | None = Depends(maybe_get_pricing_loader),
    tracer: Tracer = Depends(get_tracer),
) -> StreamingResponse:
    """Run an agent loop and stream LoopEvents as SSE.

    Response is `text/event-stream` (per 02-architecture-design §SSE).
    Each frame is `event: <type>\\ndata: <json>\\n\\n`. The session_id is
    in the first `loop_start` frame's data, alongside the `trace_id` of
    the root TraceContext (frontend can correlate with Jaeger / logs).

    Sprint 53.6 US-4 — closes AD-Front-2: passes ServiceFactory through
    `build_handler` so AgentLoopImpl receives the production HITLManager.
    Cat 9 Stage 3 ESCALATE now flows through the full HITL pipeline
    (request_approval → notifier → reviewer UI → wait_for_decision → resume).
    Toggle off via env `HITL_ENABLED=false` (handler.py guards this).

    Sprint 55.2 US-3 — closes AD-BusinessDomainPartialSwap-1 at the wiring
    layer: builds a per-request BusinessServiceFactory(db, tenant_id, tracer=None)
    and passes the factory_provider lambda to build_handler. When
    settings.business_domain_mode='service', business-domain handlers route
    through DB-backed services (5 domains uniformly mode-aware). When
    'mock' (default), preserves 51.0/55.1 PoC behavior. Tracer=None per
    AD-Cat12-Helpers-1 deferred (Phase 56+).
    """
    settings = get_settings()

    # Sprint 56.1 Day 2 (US-2): pre-stream daily token quota gate.
    # Off by default; enabled via env QUOTA_ENFORCEMENT_ENABLED=true after
    # Redis client is wired at app startup (api/main.py).
    # Sprint 56.2 Day 2 (US-2 + US-3 — closes AD-QuotaEstimation-1 +
    # AD-QuotaPostCall-1): replace fixed 1000-token reservation with
    # message-length heuristic; post-call reconciliation in
    # _stream_loop_events releases over-reservation when LoopCompleted fires.
    estimated_tokens = 0
    if settings.quota_enforcement_enabled and quota_enforcer is not None:
        estimated_tokens = quota_enforcer.estimate_pre_call_tokens(
            req.message,
            fallback=settings.quota_estimated_tokens_per_call,
        )
        try:
            await quota_enforcer.check_and_reserve(
                tenant_id=current_tenant,
                plan_name="enterprise",
                estimated_tokens=estimated_tokens,
            )
        except QuotaExceededError as exc:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=str(exc),
                headers={"Retry-After": str(exc.retry_after_seconds)},
            ) from exc

    business_factory = BusinessServiceFactory(
        db=db,
        tenant_id=current_tenant,
        tracer=tracer,  # Sprint 56.2 US-1: real Tracer wired (closes AD-Cat12-BusinessObs)
    )

    def business_factory_provider() -> BusinessServiceFactory:
        return business_factory

    # Sprint 57.63 Day 1: session_id generated BEFORE build_handler so the Cat 7
    # DBCheckpointer can bind to it (was generated AFTER build_handler pre-57.63).
    session_id = req.session_id or uuid4()

    try:
        loop, verifier_registry = build_handler(
            req.mode,
            req.message,
            service_factory=factory,
            business_factory_provider=(
                business_factory_provider if settings.business_domain_mode == "service" else None
            ),
            db=db,
            session_id=session_id,
            tenant_id=current_tenant,
        )
    except (RuntimeError, ValueError) as exc:
        # Misconfiguration (env vars / unsupported mode) → 503.
        # Schema-layer errors (invalid mode literal) get caught by FastAPI
        # validation as 422 before reaching here.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    registry = get_default_registry()
    await registry.register(current_tenant, session_id)

    # Sprint 57.7 US-R1 (closes AD-Reality-3a): persist sessions row at chat
    # start with real user_id from JWT claim.sub. Best-effort failure: DB
    # flake must NOT break SSE stream — chat session is already registered
    # in-memory via SessionRegistry; DB row is for audit / analytics.
    # SAVEPOINT pattern matches Sprint 57.6 audit_log observer.
    # Default ON in production; tests/conftest.py sets to "false" via
    # SESSIONS_CHAT_OBSERVER=false for test isolation parity with audit_log.
    _sessions_observer_enabled = os.environ.get("SESSIONS_CHAT_OBSERVER", "true").lower() == "true"
    if _sessions_observer_enabled:
        try:
            async with db.begin_nested():
                await SessionRepository(db).create_session(
                    session_id=session_id,
                    user_id=current_user,
                    tenant_id=current_tenant,
                )
        except Exception:  # noqa: BLE001
            logger.exception(
                "chat session %s/%s: sessions row INSERT failed (best-effort)",
                current_tenant,
                session_id,
            )

    # P0 #12 — root TraceContext established at API boundary. The loop
    # already accepts trace_context; sse.py will copy trace_id into every
    # SSE frame's data so SSE consumers can correlate with backend traces.
    trace_ctx = TraceContext(
        tenant_id=current_tenant,
        session_id=session_id,
    )

    # Sprint 56.3 Day 1 (US-1 — SLA Metric Recording): chat_start_time
    # captures end-to-end loop latency at the request boundary; passed to
    # _stream_loop_events so the LoopCompleted observer can record into the
    # per-tenant Redis sliding window via SLAMetricRecorder.
    chat_start_time = time.monotonic()

    # Sprint 56.3 Day 3 (US-4 — Cost Ledger auto-record):
    # Construct CostLedgerService per-request when pricing_loader is wired.
    # CostLedgerService writes use the same `db` session as BusinessServiceFactory
    # (kept alive by FastAPI for the StreamingResponse iterator's lifetime).
    cost_ledger_service: CostLedgerService | None = None
    if pricing_loader is not None:
        cost_ledger_service = CostLedgerService(db=db, pricing_loader=pricing_loader)

    return StreamingResponse(
        _stream_loop_events(
            loop,
            current_tenant,
            session_id,
            registry,
            user_input=req.message,
            trace_context=trace_ctx,
            quota_enforcer=quota_enforcer,
            estimated_tokens=estimated_tokens,
            sla_recorder=sla_recorder,
            chat_start_time=chat_start_time,
            cost_ledger=cost_ledger_service,
            db=db,
            verifier_registry=verifier_registry,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # disable nginx buffering for real-time
            "X-Session-Id": str(session_id),
            "X-Trace-Id": trace_ctx.trace_id,
        },
    )


async def _stream_loop_events(
    loop: object,  # AgentLoopImpl; loose-typed to avoid circular import noise
    tenant_id: UUID,
    session_id: UUID,
    registry: SessionRegistry,
    *,
    user_input: str,
    trace_context: TraceContext,
    quota_enforcer: QuotaEnforcer | None = None,
    estimated_tokens: int = 0,
    sla_recorder: SLAMetricRecorder | None = None,
    chat_start_time: float | None = None,
    cost_ledger: CostLedgerService | None = None,
    db: AsyncSession | None = None,
    verifier_registry: VerifierRegistry | None = None,
) -> AsyncIterator[bytes]:
    """Drive the loop generator + emit SSE bytes; finalize tenant-scoped registry.

    `user_input` is appended into the loop's messages as the first user turn.
    For ``echo_demo`` mode it is harmless (MockChatClient ignores the request);
    for ``real_llm`` it is what the model actually responds to.

    `trace_context` is the root context for this chat run — passed to
    ``loop.run`` so child spans (TurnStarted / LLMRequested / etc.) inherit
    the trace_id; sse.py extracts trace_id into each SSE event.

    Sprint 55.5 (AD-Cat10-Wire-1; Option E 2-mode post-D4+D5):
    Always invokes ``run_with_verification`` wrapper. When
    ``settings.chat_verification_mode == "disabled"`` (default), passes
    ``verifier_registry=None`` → wrapper transparently delegates to
    ``loop.run()`` per correction_loop.py:99-106 (byte-for-byte event stream
    identical to direct loop.run; backwards-compat preserved). When
    ``"enabled"``, passes a populated ``VerifierRegistry`` → wrapper runs
    verifiers + self-correction loop (max 2 attempts).
    """
    # Sprint 57.63 (Cat 10, approach A): verifier_registry is now passed in from
    # build_handler — built with the loop's OWN adapter (shared ChatClient) when
    # settings.chat_verification_mode == "enabled", else None. The previous
    # in-function select_verifier_registry() call is removed.
    natural_completion = False
    try:
        async for event in run_with_verification(
            agent_loop=loop,  # type: ignore[arg-type]
            session_id=session_id,
            user_input=user_input,
            trace_context=trace_context,
            verifier_registry=verifier_registry,
            max_correction_attempts=2,
        ):
            try:
                payload = serialize_loop_event(event)
            except NotImplementedError:
                # Event types deferred to later sprints (HITL / Verification / etc.).
                logger.debug("sse: skip unserialized event %s", type(event).__name__)
                continue
            if payload is None:
                # Day 2: serializer signals "skip this event" (e.g. Thinking →
                # LLMResponded carries the canonical content).
                continue
            yield format_sse_message(payload["type"], payload["data"])
            if isinstance(event, LoopCompleted):
                natural_completion = True
                # Sprint 56.2 Day 2 (US-3 — closes AD-QuotaPostCall-1):
                # reconcile reservation with actual tokens. event.total_tokens
                # is the cumulative input+output across all LLM calls in this
                # loop run (loop.py L944 accumulator → LoopCompleted event).
                # Default 0 from early-termination paths releases full
                # reservation back; happy-path END_TURN releases over-reservation.
                if quota_enforcer is not None and estimated_tokens > 0:
                    try:
                        await quota_enforcer.record_usage(
                            tenant_id=tenant_id,
                            actual_tokens=event.total_tokens,
                            reserved_tokens=estimated_tokens,
                        )
                    except Exception:  # noqa: BLE001
                        # Reconciliation failure must not break SSE stream;
                        # over-reservation will roll off at midnight UTC TTL.
                        logger.exception(
                            "chat session %s/%s: quota reconciliation failed",
                            tenant_id,
                            session_id,
                        )
                # Sprint 56.3 Day 1 (US-1 — SLA Metric Recording):
                # Record loop end-to-end latency in the complexity bucket so
                # SLAReportGenerator (US-2) can compute per-tenant p99.
                # Failure must not break SSE stream — Redis flake should not
                # cascade into chat outage; SLA monitoring is best-effort.
                if sla_recorder is not None and chat_start_time is not None:
                    try:
                        latency_ms = int((time.monotonic() - chat_start_time) * 1000)
                        complexity = classify_loop_complexity(event)
                        await sla_recorder.record_loop_completion(
                            tenant_id=tenant_id,
                            latency_ms=latency_ms,
                            complexity_category=complexity,
                        )
                    except Exception:  # noqa: BLE001
                        logger.exception(
                            "chat session %s/%s: SLA loop completion record failed",
                            tenant_id,
                            session_id,
                        )
                # Sprint 56.3 Day 3 (US-4) → Sprint 57.2 (closes
                # AD-Cost-Ledger-Token-Split + AD-Cost-Ledger-Provider-Attribution):
                # Record TWO ledger entries (input + output split) from
                # LoopCompleted accumulator-sourced fields. Provider/model
                # now truthful (sourced from event.provider + event.model
                # populated by AgentLoop from adapter.model_info().provider +
                # ChatResponse.model). Best-effort failure: ledger write must
                # not break SSE stream. Fallback for early-termination paths
                # (provider="" or empty token counts) skips the write per
                # event.input_tokens > 0 OR event.output_tokens > 0 gate.
                if cost_ledger is not None and (event.input_tokens > 0 or event.output_tokens > 0):
                    try:
                        await cost_ledger.record_llm_call(
                            tenant_id=tenant_id,
                            provider=event.provider or "azure_openai",
                            model=event.model or _FALLBACK_PRICING_MODEL,
                            input_tokens=event.input_tokens,
                            output_tokens=event.output_tokens,
                            session_id=session_id,
                        )
                    except Exception:  # noqa: BLE001
                        logger.exception(
                            "chat session %s/%s: cost ledger LLM record failed",
                            tenant_id,
                            session_id,
                        )
                # Sprint 57.6 Day 2 US-3 (R3 / closes 57.5 D-17 + AD-Reality-3-audit_log):
                # Append a hash-chained audit_log row for chat completion. Best-effort
                # failure isolation: audit append must NOT break the SSE stream
                # (Redis / DB flake should not cascade into chat outage).
                # user_id=None per audit_helper signature (system actor; no JWT
                # user_id extraction in V2 yet — 57.6 Day 2 探勘 confirmed).
                # Sprint 57.6 Day 4 CI fix: env-flag observer for test isolation。
                # Default ON in production;tests/conftest.py sets to "false" via
                # AUDIT_LOG_CHAT_OBSERVER=false。Phase 57.7+ AD-Reality-FlakeEventLoop
                # to add proper connection-pool isolation in tests/conftest.py
                # db_session fixture (estimated ~1-2 hr;not blocking Sprint 57.6 closure)。
                # SAVEPOINT pattern still used for FK violation isolation in production。
                _audit_observer_enabled = (
                    os.environ.get("AUDIT_LOG_CHAT_OBSERVER", "true").lower() == "true"
                )
                if db is not None and _audit_observer_enabled:
                    try:
                        async with db.begin_nested():
                            await append_audit(
                                db,
                                tenant_id=tenant_id,
                                operation="conversation_completed",
                                resource_type="session",
                                resource_id=str(session_id),
                                operation_data={
                                    "total_turns": event.total_turns,
                                    "total_tokens": event.total_tokens,
                                    "input_tokens": event.input_tokens,
                                    "output_tokens": event.output_tokens,
                                    "model": event.model or "",
                                    "provider": event.provider or "",
                                    "outcome": "completed",
                                },
                                user_id=None,
                                session_id=session_id,
                                operation_result="success",
                            )
                    except Exception:  # noqa: BLE001
                        logger.exception(
                            "chat session %s/%s: audit_log append failed",
                            tenant_id,
                            session_id,
                        )
                break
            # Sprint 56.3 Day 3 (US-4 — Cost Ledger tool hook):
            # Record one cost ledger entry per ToolCallExecuted event (per
            # Day 0 D4 — event already exists at events.py:131; no new
            # event needed). Per-tenant pricing comes from
            # config/llm_pricing.yml (default_per_call + named overrides).
            if isinstance(event, ToolCallExecuted) and cost_ledger is not None:
                try:
                    await cost_ledger.record_tool_call(
                        tenant_id=tenant_id,
                        tool_name=event.tool_name,
                        session_id=session_id,
                    )
                except Exception:  # noqa: BLE001
                    logger.exception(
                        "chat session %s/%s: cost ledger tool record failed (tool=%s)",
                        tenant_id,
                        session_id,
                        event.tool_name,
                    )
            # Sprint 57.7 US-R1 (closes AD-Reality-3b): persist tool_calls
            # row per ToolCallExecuted event. Best-effort SAVEPOINT — FK
            # violation (sessions row missing) MUST NOT cascade into SSE
            # stream. Env flag TOOL_CALLS_CHAT_OBSERVER=false for tests.
            _tc_observer_enabled = (
                os.environ.get("TOOL_CALLS_CHAT_OBSERVER", "true").lower() == "true"
            )
            if isinstance(event, ToolCallExecuted) and db is not None and _tc_observer_enabled:
                try:
                    async with db.begin_nested():
                        # event.arguments is a dict at events.py:131 (D4 — Sprint 56.3)
                        await ToolCallRepository(db).create(
                            session_id=session_id,
                            tenant_id=tenant_id,
                            tool_name=event.tool_name,
                            arguments=getattr(event, "arguments", {}) or {},
                            status="completed",
                            duration_ms=getattr(event, "duration_ms", None),
                        )
                except Exception:  # noqa: BLE001
                    logger.exception(
                        "chat session %s/%s: tool_calls row INSERT failed (tool=%s)",
                        tenant_id,
                        session_id,
                        event.tool_name,
                    )
    except asyncio.CancelledError:
        logger.info(
            "chat session %s/%s: client disconnected mid-stream",
            tenant_id,
            session_id,
        )
        raise
    finally:
        if natural_completion:
            await registry.mark_completed(tenant_id, session_id)
        # else: leave status as-is (running / cancelled) — caller can poll GET.


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_session(
    session_id: UUID,
    current_tenant: UUID = Depends(get_current_tenant),
) -> ChatSessionResponse:
    """Return session status for THIS tenant; 404 on missing OR cross-tenant.

    Cross-tenant attempts deliberately return 404 (not 403) so the API does
    not reveal that the session exists under a different tenant.
    """
    registry = get_default_registry()
    entry = await registry.get(current_tenant, session_id)
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found.",
        )
    return ChatSessionResponse(
        session_id=session_id,
        status=entry.status,
        started_at=entry.started_at,
    )


@router.post("/sessions/{session_id}/cancel", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_session(
    session_id: UUID,
    current_tenant: UUID = Depends(get_current_tenant),
) -> None:
    """Cancel a running session for THIS tenant; 404 on missing OR cross-tenant.

    Same 404-on-cross-tenant rule as get_session — never reveal cross-tenant
    session existence.
    """
    registry = get_default_registry()
    found = await registry.cancel(current_tenant, session_id)
    if not found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found.",
        )
