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
Last Modified: 2026-06-10

Modification History (newest-first):
    - 2026-06-10: Sprint 57.98 A1 US-5 — drop run_with_verification wrapper; gate is in-loop now
    - 2026-06-09: Sprint 57.95 — relay subagent SSE events (buffer drained by _stream_loop_events)
    - 2026-06-08: Sprint 57.88 US-4 — NEW POST /chat/{id}/resume (durable HITL pause-resume)
    - 2026-06-05: Sprint 57.84 — C-15: chat cost-write → billing_outbox enqueue + drainer
    - 2026-06-05: Sprint 57.82 — record verification judge LLM cost + count vs quota (B-8 leg-1)
    - 2026-06-02: Sprint 57.71 — thread real tracer into build_handler (A-4 Tier 0)
    - 2026-06-02: Sprint 57.69 A-3b — pass parent_context to boot_handoff (carry parent convo)
    - 2026-06-02: Sprint 57.68 A-3b — post-loop HANDOFF hook: boot child session + emit AgentHandoff
    - 2026-06-01: Sprint 57.64 Day 2 — thread user_id into build_handler + TraceContext (Cat 3)
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

from agent_harness._contracts import (
    AgentHandoff,
    LoopCompleted,
    LoopEvent,
    LoopState,
    TraceContext,
)
from agent_harness._contracts.events import ToolCallExecuted
from agent_harness.observability._abc import Tracer
from agent_harness.orchestrator_loop import AgentLoop
from business_domain._service_factory import BusinessServiceFactory
from core.config import get_settings
from infrastructure.db.audit_helper import append_audit
from infrastructure.db.repositories import SessionRepository, ToolCallRepository
from infrastructure.db.session import get_db_session
from platform_layer.billing.billing_outbox import (
    BillingOutboxService,
    llm_idempotency_key,
    maybe_get_billing_outbox,
    tool_idempotency_key,
)
from platform_layer.governance.service_factory import (
    ServiceFactory,
    get_service_factory,
)
from platform_layer.handoff import HandoffError, HandoffService
from platform_layer.identity import get_current_tenant
from platform_layer.identity.auth import get_current_user_id
from platform_layer.observability import (
    SLAMetricRecorder,
    classify_loop_complexity,
    get_tracer,
    maybe_get_sla_recorder,
)
from platform_layer.resume import ResumeService
from platform_layer.tenant.quota import (
    QuotaEnforcer,
    QuotaExceededError,
    maybe_get_quota_enforcer,
)

from .handler import build_handler, resolve_session_persona
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

    # Sprint 57.68 A-3b (US-3): resume of a HANDOFF-booted child session must run
    # as its target persona (meta_data["agent_role"]) — resolved here so the sync
    # builders receive a ready system_prompt (DEMO_SYSTEM_PROMPT for ordinary
    # sessions / on any miss). Only meaningful when the client passed an existing
    # session_id; a fresh session has no row yet (→ demo persona).
    system_prompt = await resolve_session_persona(db, session_id, current_tenant)

    # Sprint 57.95 (Cat 11 → Cat 12 SSE relay): a router-owned buffer collects the
    # SubagentSpawned / SubagentCompleted events the dispatcher emits WHILE the loop
    # is awaiting a task_spawn tool (the loop generator is blocked then, so it cannot
    # yield them). _stream_loop_events drains the buffer into the SSE stream so the
    # Inspector "Tree" tab shows the subagent node (was headless: "no subagents").
    # The emitter append + the drain both run in _stream_loop_events's single asyncio
    # task → no lock / no queue needed.
    subagent_event_buffer: list[LoopEvent] = []

    async def _relay_subagent_event(ev: LoopEvent) -> None:
        subagent_event_buffer.append(ev)

    try:
        # Sprint 57.98 A1 (US-5): build_handler now returns the wired AgentLoopImpl
        # alone — the Cat 10 verifier registry is injected INTO the loop ctor (the
        # gate is in-loop), so the router no longer threads a registry around it.
        loop = build_handler(
            req.mode,
            req.message,
            service_factory=factory,
            business_factory_provider=(
                business_factory_provider if settings.business_domain_mode == "service" else None
            ),
            db=db,
            session_id=session_id,
            tenant_id=current_tenant,
            user_id=current_user,
            system_prompt=system_prompt,
            # Sprint 57.71 (A-4 Tier 0): thread the already-resolved real
            # OTelTracer (Depends(get_tracer)) into the loop so its root +
            # per-turn span tree run on a real tracer (was NoOp on the chat
            # path). Reuses the existing dependency — no new Depends.
            tracer=tracer,
            # Sprint 57.95: the emitter the dispatcher calls on spawn / complete.
            subagent_event_emitter=_relay_subagent_event,
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
            # Sprint 57.88 (Day-4 drive-through fix): COMMIT the sessions row before
            # the loop runs. A deferred-HITL ESCALATE (durable pause-resume) persists
            # an `approvals` row that FKs to `sessions`; that INSERT happens mid-SSE-
            # stream via the HITL manager's OWN db connection, which cannot see this
            # request session's still-open transaction. Without an early commit the
            # approval INSERT raises FK violation `approvals_session_id_fkey` →
            # the loop soft-blocks the tool instead of pausing (the gates pass because
            # integration tests pre-create the session row; only a real drive-through
            # surfaced it). Committing here makes the row visible cross-connection.
            # Tests skip this block entirely (SESSIONS_CHAT_OBSERVER=false), so their
            # rollback-based isolation is unaffected.
            await db.commit()
        except Exception:  # noqa: BLE001
            logger.exception(
                "chat session %s/%s: sessions row INSERT failed (best-effort)",
                current_tenant,
                session_id,
            )

    # P0 #12 — root TraceContext established at API boundary. The loop
    # already accepts trace_context; sse.py will copy trace_id into every
    # SSE frame's data so SSE consumers can correlate with backend traces.
    # Sprint 57.64 Day 2: include user_id so the loop's ExecutionContext
    # (loop.py:1136) attributes memory_search / memory_write to the
    # authenticated user (Cat 3 dual-axis tenant_id + user_id scoping).
    trace_ctx = TraceContext(
        tenant_id=current_tenant,
        session_id=session_id,
        user_id=current_user,
    )

    # Sprint 56.3 Day 1 (US-1 — SLA Metric Recording): chat_start_time
    # captures end-to-end loop latency at the request boundary; passed to
    # _stream_loop_events so the LoopCompleted observer can record into the
    # per-tenant Redis sliding window via SLAMetricRecorder.
    chat_start_time = time.monotonic()

    # Sprint 57.84 (C-15 billing-Outbox flip): the chat observer now ENQUEUES a
    # durable billing event into billing_outbox (atomic with the request txn)
    # instead of writing cost_ledger best-effort. A background drainer (wired in
    # api/main.py) materializes cost_ledger from the outbox idempotently — pricing
    # is resolved by the drainer (single-source), so the router no longer needs the
    # PricingLoader. maybe_get_billing_outbox() is None only if startup wiring
    # failed → enqueue is skipped (degrade, same best-effort spirit as before).
    billing_outbox = maybe_get_billing_outbox()

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
            billing_outbox=billing_outbox,
            db=db,
            subagent_event_buffer=subagent_event_buffer,
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


def _drain_subagent_frames(buffer: "list[LoopEvent] | None") -> list[bytes]:
    """Serialize + frame any buffered subagent events (SubagentSpawned/Completed).

    Cat 11 → Cat 12 SSE relay (Sprint 57.95): subagent lifecycle events are emitted
    by DefaultSubagentDispatcher while the parent loop is awaiting the task_spawn
    tool — the loop generator is blocked then and cannot yield them. The chat router
    collects them in a buffer (via the wired event_emitter); _stream_loop_events
    drains it here, applying the SAME serialize / skip handling as loop events, so the
    Inspector "Tree" tab shows the subagent node instead of "no subagents".
    """
    if not buffer:
        return []
    frames: list[bytes] = []
    while buffer:
        ev = buffer.pop(0)
        try:
            payload = serialize_loop_event(ev)
        except NotImplementedError:
            continue
        if payload is None:
            continue
        frames.append(format_sse_message(payload["type"], payload["data"]))
    return frames


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
    billing_outbox: BillingOutboxService | None = None,
    db: AsyncSession | None = None,
    subagent_event_buffer: "list[LoopEvent] | None" = None,
) -> AsyncIterator[bytes]:
    """Drive the loop generator + emit SSE bytes; finalize tenant-scoped registry.

    `user_input` is appended into the loop's messages as the first user turn.
    For ``echo_demo`` mode it is harmless (MockChatClient ignores the request);
    for ``real_llm`` it is what the model actually responds to.

    `trace_context` is the root context for this chat run — passed to
    ``loop.run`` so child spans (TurnStarted / LLMRequested / etc.) inherit
    the trace_id; sse.py extracts trace_id into each SSE event.

    Sprint 57.98 A1 (US-5): the Cat 10 verification gate now runs INSIDE the loop
    (``loop.run()`` → ``_run_turns`` → ``_cat10_verify_gate``); the verifier
    registry is injected into the loop ctor by ``build_handler``. The retired
    ``run_with_verification`` wrapper (which used to bracket ``loop.run`` here) is
    gone, so a paused-then-resumed continuation is verified for free (``resume()``
    drives the same ``_run_turns``). A non-verified run (registry None) streams a
    byte-identical event sequence to the pre-57.98 direct ``loop.run``.
    """
    natural_completion = False
    # Sprint 57.84 (C-15): per-request monotonic seq disambiguates repeated
    # same-tool billing events in the idempotency key (a replay reuses the seq).
    tool_seq = 0
    try:
        async for event in loop.run(  # type: ignore[attr-defined]
            session_id=session_id,
            user_input=user_input,
            trace_context=trace_context,
        ):
            # Sprint 57.95 (Cat 11 → Cat 12 SSE relay): flush any subagent events
            # emitted during the prior await (e.g. a task_spawn tool call) BEFORE the
            # loop event that follows them, so the Inspector Tree shows the node.
            for _frame in _drain_subagent_frames(subagent_event_buffer):
                yield _frame
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
                            # Sprint 57.82 (B-8 leg-1): judge LLM tokens (Cat 10
                            # verification) count against the cap too — real
                            # consumption. 0 when disabled / no judge ran.
                            actual_tokens=(
                                event.total_tokens
                                + event.verification_input_tokens
                                + event.verification_output_tokens
                            ),
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
                # Sprint 57.84 (C-15 billing-Outbox flip): ENQUEUE a durable
                # llm_call billing event into billing_outbox (atomic with this
                # request's txn) instead of writing cost_ledger directly. A
                # background drainer materializes cost_ledger from the outbox
                # idempotently (pricing single-source in the drainer). Provider/
                # model sourced truthfully from the LoopCompleted accumulator;
                # early-termination paths (empty tokens) skip the enqueue. The
                # enqueue is a single INSERT in the request txn → the billing event
                # commits atomically with session/audit (no more best-effort 漏扣).
                # Logged best-effort isolation kept so a rare enqueue hiccup does
                # not break the SSE stream (consistent w/ sessions/audit observers).
                if (
                    billing_outbox is not None
                    and db is not None
                    and (event.input_tokens > 0 or event.output_tokens > 0)
                ):
                    try:
                        await billing_outbox.enqueue(
                            db,
                            tenant_id=tenant_id,
                            event_type="llm_call",
                            payload={
                                "provider": event.provider or "azure_openai",
                                "model": event.model or _FALLBACK_PRICING_MODEL,
                                "input_tokens": event.input_tokens,
                                "output_tokens": event.output_tokens,
                                "cached_input_tokens": 0,
                                "sub_type_suffix": "",
                            },
                            idempotency_key=llm_idempotency_key(session_id, ""),
                            session_id=session_id,
                        )
                    except Exception:  # noqa: BLE001
                        logger.exception(
                            "chat session %s/%s: billing outbox LLM enqueue failed",
                            tenant_id,
                            session_id,
                        )
                # Sprint 57.84 (C-15): enqueue the Cat 10 verification judge LLM
                # call as a DISTINCT `_verification` billing event (B-8 leg-1 cost
                # attribution preserved — the drainer materializes the
                # `_verification` sub_type). Judge shares the loop adapter →
                # event.provider correct; model is the judge's own
                # (verification_model) falling back to the loop model. 0 tokens
                # (verification disabled / no judge ran) → skip.
                if (
                    billing_outbox is not None
                    and db is not None
                    and (
                        event.verification_input_tokens > 0 or event.verification_output_tokens > 0
                    )
                ):
                    try:
                        await billing_outbox.enqueue(
                            db,
                            tenant_id=tenant_id,
                            event_type="llm_call",
                            payload={
                                "provider": event.provider or "azure_openai",
                                "model": (
                                    event.verification_model
                                    or event.model
                                    or _FALLBACK_PRICING_MODEL
                                ),
                                "input_tokens": event.verification_input_tokens,
                                "output_tokens": event.verification_output_tokens,
                                "cached_input_tokens": 0,
                                "sub_type_suffix": "_verification",
                            },
                            idempotency_key=llm_idempotency_key(session_id, "_verification"),
                            session_id=session_id,
                        )
                    except Exception:  # noqa: BLE001
                        logger.exception(
                            "chat session %s/%s: billing outbox verification enqueue failed",
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
                # Sprint 57.68 (A-3b — Cat 11 HANDOFF control transfer):
                # when the loop terminated with stop_reason="handoff", boot a
                # persisted child session for the target agent (HandoffService —
                # server-side-first; DB/session knowledge stays out of the loop),
                # then emit an AgentHandoff SSE frame carrying the new_session_id
                # so the client can pivot. Multi-tenant 鐵律: the child inherits
                # the parent's tenant_id; a foreign/unknown target raises
                # HandoffError → fail soft (log, emit nothing) so a bad handoff
                # never crashes the stream. user_id sourced from the request
                # TraceContext (the authenticated actor).
                if event.stop_reason == "handoff" and db is not None and event.handoff_target:
                    try:
                        handoff_result = await HandoffService().boot_handoff(
                            parent_session_id=session_id,
                            target_agent=event.handoff_target,
                            reason=event.handoff_reason or "",
                            tenant_id=tenant_id,
                            user_id=trace_context.user_id or tenant_id,
                            db=db,
                            # Sprint 57.69 A-3b slice 2: carry the parent's
                            # in-memory conversation snapshot into the booted
                            # child's meta_data["carried_context"].
                            parent_context=event.handoff_context,
                        )
                        handoff_payload = serialize_loop_event(
                            AgentHandoff(
                                target_agent=event.handoff_target,
                                reason=event.handoff_reason or "",
                                parent_session_id=session_id,
                                new_session_id=handoff_result.new_session_id,
                                trace_context=trace_context,
                            )
                        )
                        if handoff_payload is not None:
                            yield format_sse_message(
                                handoff_payload["type"], handoff_payload["data"]
                            )
                    except HandoffError:
                        # Invalid handover (unknown target / foreign parent): no
                        # child booted, no frame emitted — the parent already
                        # ended normally. Do NOT crash the stream.
                        logger.warning(
                            "chat session %s/%s: handoff to %r failed (no child booted)",
                            tenant_id,
                            session_id,
                            event.handoff_target,
                        )
                    except Exception:  # noqa: BLE001
                        # Defensive: any other handoff failure (DB flake) must
                        # not break the SSE stream — the parent loop is done.
                        logger.exception(
                            "chat session %s/%s: handoff boot failed",
                            tenant_id,
                            session_id,
                        )
                break
            # Sprint 57.84 (C-15): enqueue one tool_call billing event per
            # ToolCallExecuted into billing_outbox (the drainer prices it from
            # config/llm_pricing.yml + materializes cost_ledger). tool_seq makes
            # repeated same-tool calls in one loop distinct while a replay reuses
            # the same key (idempotent). Best-effort isolation kept (SSE safety).
            if (
                isinstance(event, ToolCallExecuted)
                and billing_outbox is not None
                and db is not None
            ):
                try:
                    await billing_outbox.enqueue(
                        db,
                        tenant_id=tenant_id,
                        event_type="tool_call",
                        payload={"tool_name": event.tool_name},
                        idempotency_key=tool_idempotency_key(session_id, event.tool_name, tool_seq),
                        session_id=session_id,
                    )
                    tool_seq += 1
                except Exception:  # noqa: BLE001
                    logger.exception(
                        "chat session %s/%s: billing outbox tool enqueue failed (tool=%s)",
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
        # Sprint 57.95: drain any subagent events appended during the final await
        # (defensive — the per-iteration drain already flushes the common case, since
        # task_spawn precedes the LoopCompleted that breaks the loop).
        for _frame in _drain_subagent_frames(subagent_event_buffer):
            yield _frame
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


# === Sprint 57.88 (US-4): durable HITL pause-resume endpoint ================
# Why: a chat tool ESCALATE in deferred mode pauses the loop with
# stop_reason="awaiting_approval" + a resumable checkpoint, releasing the SSE
# connection (a human approval may take hours/days). After the human decides via
# the EXISTING POST /governance/approvals/{id}/decide, the client calls this NEW
# endpoint to drive AgentLoopImpl.resume() on a fresh SSE stream — executing the
# approved pending tool and continuing to end_turn (or emitting a block on
# reject). Multi-tenant 鐵律: ResumeService is tenant-scoped; a checkpoint for
# another tenant (or no paused checkpoint) → None → 404 (no info leak).


def get_resume_service() -> ResumeService:
    """ResumeService provider (default chat-builder). Tests override via DI."""
    return ResumeService()


async def _stream_resume_events(
    loop: AgentLoop,
    *,
    state: LoopState,
    trace_context: TraceContext,
) -> AsyncIterator[bytes]:
    """Drive loop.resume() + emit SSE bytes (thin mirror of _stream_loop_events).

    Resume runs the post-approval continuation only (execute the approved pending
    tool → continue to end_turn), so it skips the chat-start observers
    (sessions / cost ledger / quota) — those fired on the original RUN-1 stream.
    Framing matches _stream_loop_events: one frame per serializable event,
    Thinking → None → skipped (LLMResponded carries the canonical content).
    """
    async for event in loop.resume(state=state, trace_context=trace_context):
        try:
            payload = serialize_loop_event(event)
        except NotImplementedError:
            logger.debug("sse(resume): skip unserialized event %s", type(event).__name__)
            continue
        if payload is None:
            continue
        yield format_sse_message(payload["type"], payload["data"])


@router.post("/{session_id}/resume", status_code=status.HTTP_200_OK)
async def resume_chat(
    session_id: UUID,
    current_tenant: UUID = Depends(get_current_tenant),
    current_user: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session),
    resume_service: ResumeService = Depends(get_resume_service),
) -> StreamingResponse:
    """Resume a chat that paused on a deferred HITL approval; stream the continuation.

    Re-derives tenant_id / user_id from the JWT (standard chat auth deps).
    ResumeService loads the latest paused checkpoint for (session_id, tenant_id),
    rebuilds the LoopState (messages from the checkpoint metadata — decision B),
    and wires a fresh loop. A missing / cross-tenant paused checkpoint → 404
    (multi-tenant 鐵律: never reveal cross-tenant existence).

    The approval decision itself is checked inside `resume()` (non-blocking
    get_decision): APPROVED → run the pending tool + continue to end_turn;
    REJECTED / ESCALATED → GuardrailTriggered(block) + terminate. Both produce a
    valid SSE stream (the checkpoint existed — it was just not approved), so we do
    NOT 404 on an un-approved-yet decision; the stream reports the outcome.
    """
    result = await resume_service.resume_session(
        session_id=session_id,
        tenant_id=current_tenant,
        user_id=current_user,
        db=db,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No resumable session {session_id} found.",
        )

    trace_ctx = TraceContext(
        tenant_id=current_tenant,
        session_id=session_id,
        user_id=current_user,
    )

    return StreamingResponse(
        _stream_resume_events(
            result.loop,
            state=result.state,
            trace_context=trace_ctx,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "X-Session-Id": str(session_id),
            "X-Trace-Id": trace_ctx.trace_id,
        },
    )
