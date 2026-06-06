"""
File: backend/tests/integration/api/test_phase56_3_e2e.py
Purpose: Cross-AD e2e — Phase 56.3 SLA Monitor + billing enqueue + quota chat flow.
Category: Tests / Integration / API (Phase 56 SaaS Stage 1 / Sprint 57.84 C-15)
Scope: Sprint 56.3 / Day 4 / US-5 closeout cross-AD e2e (updated Sprint 57.84).

Description:
    Single integrated chat flow that exercises:
    - US-1 SLAMetricRecorder: record_loop_completion via the chat router
      observer; classify_loop_complexity bucket recorded in Redis; get_loop_p99
      returns the recorded latency.
    - US-3 + US-4 billing: Sprint 57.84 (C-15) flipped the chat observer from a
      direct cost_ledger write to a durable billing_outbox ENQUEUE — so the
      LoopCompleted + ToolCallExecuted observers now enqueue billing events
      (a background drainer materializes cost_ledger; the drain → cost_ledger
      parity is covered by tests/integration/billing/test_billing_outbox_drain.py).
    - US-2 + US-3 quota carryover from 56.2: pre-call estimate + post-call
      reconcile via record_usage (UNCHANGED by the flip).
    - All hooks coexist in one _stream_loop_events run without breaking SSE.

    Uses fakeredis + real db_session fixture (Postgres per conftest.py).

Created: 2026-05-06 (Sprint 56.3 Day 4 / US-5 closeout)
Last Modified: 2026-06-05 (Sprint 57.84 — cost-write flipped to billing_outbox enqueue)
"""

from __future__ import annotations

import time
from collections.abc import AsyncIterator
from uuid import UUID, uuid4

import pytest
from fakeredis import FakeAsyncRedis
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from agent_harness._contracts import LoopCompleted, TraceContext
from agent_harness._contracts.events import ToolCallExecuted
from api.v1.chat.router import _stream_loop_events
from api.v1.chat.session_registry import SessionRegistry
from infrastructure.db.models.billing_outbox import BillingOutboxEvent
from platform_layer.billing.billing_outbox import BillingOutboxService
from platform_layer.observability.sla_monitor import SLAMetricRecorder
from platform_layer.tenant.plans import PlanLoader
from platform_layer.tenant.quota import QuotaEnforcer
from tests.conftest import seed_tenant

pytestmark = pytest.mark.asyncio


class _StubLoopWithToolAndCompletion:
    """Stub agent loop emitting ToolCallExecuted + LoopCompleted in one run."""

    def __init__(
        self,
        *,
        input_tokens: int = 0,
        output_tokens: int = 0,
        tool_name: str,
        provider: str = "azure_openai",
        model: str = "gpt-5.4",
    ) -> None:
        self._input_tokens = input_tokens
        self._output_tokens = output_tokens
        self._tool_name = tool_name
        self._provider = provider
        self._model = model

    async def run(
        self,
        *,
        session_id: UUID,
        user_input: str,
        trace_context: TraceContext,
    ) -> AsyncIterator[object]:
        yield ToolCallExecuted(
            tool_call_id="tc-e2e-1",
            tool_name=self._tool_name,
            duration_ms=15.0,
            result_content="ok",
            trace_context=trace_context,
        )
        yield LoopCompleted(
            stop_reason="end_turn",
            total_turns=1,
            total_tokens=self._input_tokens + self._output_tokens,
            input_tokens=self._input_tokens,
            output_tokens=self._output_tokens,
            provider=self._provider,
            model=self._model,
            trace_context=trace_context,
        )


async def _consume(stream: AsyncIterator[bytes]) -> None:
    async for _ in stream:
        pass


async def test_phase56_3_cross_ad_full_flow(db_session: AsyncSession) -> None:
    """One chat flow exercises US-1 (SLA) + US-3+4 (billing enqueue) + 56.2 quota."""
    t = await seed_tenant(db_session, code="P563_E2E")
    tenant_id = t.id
    # billing_outbox has FORCE RLS — set the tenant context so enqueue's INSERT
    # WITH CHECK passes (harmless if the test role bypasses RLS).
    await db_session.execute(
        text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(tenant_id)}
    )
    session_id = uuid4()

    redis = FakeAsyncRedis()
    sla_recorder = SLAMetricRecorder(redis_client=redis)
    quota_enforcer = QuotaEnforcer(client=redis, plan_loader=PlanLoader())

    registry = SessionRegistry()
    await registry.register(tenant_id, session_id)

    # 56.2 carryover (US-2 + US-3): pre-call estimate + reserve.
    msg = "x" * 800
    estimated_tokens = quota_enforcer.estimate_pre_call_tokens(msg, fallback=1000)
    assert estimated_tokens == 200, f"56.2 estimate wrong: {estimated_tokens}"
    await quota_enforcer.check_and_reserve(
        tenant_id=tenant_id, plan_name="enterprise", estimated_tokens=estimated_tokens
    )
    assert await quota_enforcer.get_usage(tenant_id) == 200

    # Stub loop emits 1 ToolCallExecuted + 1 LoopCompleted.
    stub_loop = _StubLoopWithToolAndCompletion(
        input_tokens=70,
        output_tokens=50,
        tool_name="salesforce_query",
    )
    trace_ctx = TraceContext(tenant_id=tenant_id, session_id=session_id)
    chat_start_time = time.monotonic()

    await _consume(
        _stream_loop_events(
            stub_loop,
            tenant_id,
            session_id,
            registry,
            user_input=msg,
            trace_context=trace_ctx,
            quota_enforcer=quota_enforcer,
            estimated_tokens=estimated_tokens,
            sla_recorder=sla_recorder,
            chat_start_time=chat_start_time,
            billing_outbox=BillingOutboxService(),
            db=db_session,
        )
    )

    # === US-1 (SLA) assertion ===
    p99 = await sla_recorder.get_loop_p99(tenant_id, complexity_category="simple")
    assert p99 is not None, "US-1: SLA loop_completion not recorded"
    assert p99 >= 0, f"US-1: SLA latency must be >= 0, got {p99}"

    # === US-3 + US-4 (billing enqueue) assertions — Sprint 57.84 flip ===
    # The chat observer enqueues an llm_call + a tool_call billing event into
    # billing_outbox (the drainer materializes cost_ledger separately).
    rows = (
        (
            await db_session.execute(
                select(BillingOutboxEvent).where(BillingOutboxEvent.tenant_id == tenant_id)
            )
        )
        .scalars()
        .all()
    )
    event_types = {r.event_type for r in rows}
    assert event_types == {"llm_call", "tool_call"}, "billing events missing"
    assert len(rows) == 2, f"expected 2 outbox events (1 llm + 1 tool), got {len(rows)}"
    assert all(r.session_id == session_id for r in rows)

    llm_row = next(r for r in rows if r.event_type == "llm_call")
    assert llm_row.payload["input_tokens"] == 70
    assert llm_row.payload["output_tokens"] == 50
    assert llm_row.idempotency_key == f"{session_id}:llm:loop"

    tool_row = next(r for r in rows if r.event_type == "tool_call")
    assert tool_row.payload["tool_name"] == "salesforce_query"
    assert tool_row.idempotency_key == f"{session_id}:tool:salesforce_query:0"

    # === 56.2 carryover (quota US-3) assertion — UNCHANGED by the flip ===
    # Reserved 200 → actual 120 → counter reconciled to 120.
    final_usage = await quota_enforcer.get_usage(tenant_id)
    assert final_usage == 120, f"56.2 reconciliation wrong: {final_usage}"
