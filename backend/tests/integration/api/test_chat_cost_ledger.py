"""
File: backend/tests/integration/api/test_chat_cost_ledger.py
Purpose: Integration — chat router LoopCompleted + ToolCallExecuted → billing_outbox enqueue.
Category: Tests / Integration / API (Phase 56 SaaS Stage 1 / Sprint 57.84 C-15)
Scope: Sprint 56.3 / Day 3 (US-4) → Sprint 57.84 (C-15 billing-Outbox flip).

Description:
    Drives _stream_loop_events with stub loops and asserts the chat observer
    ENQUEUES durable billing events into billing_outbox (the Sprint 57.84 flip:
    the observer no longer writes cost_ledger directly — a background drainer
    materializes cost_ledger from the outbox; see test_billing_outbox_drain.py
    for the drain → cost_ledger parity). The quota-reconcile test is unchanged
    (the flip did not touch the quota path).

Created: 2026-05-06 (Sprint 56.3 Day 3)
Last Modified: 2026-06-05 (Sprint 57.84 — flip cost-write → billing_outbox enqueue)
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from agent_harness._contracts import LoopCompleted, TraceContext
from agent_harness._contracts.events import ToolCallExecuted
from api.v1.chat.router import _stream_loop_events
from api.v1.chat.session_registry import SessionRegistry
from infrastructure.db.models.billing_outbox import BillingOutboxEvent
from platform_layer.billing.billing_outbox import BillingOutboxService
from tests.conftest import seed_tenant

pytestmark = pytest.mark.asyncio


class _StubLoop:
    """Yields ToolCallExecuted + LoopCompleted (1 of each) for chat router observer."""

    def __init__(
        self,
        input_tokens: int = 0,
        output_tokens: int = 0,
        tool_name: str = "salesforce_query",
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
            tool_call_id="tc-1",
            tool_name=self._tool_name,
            duration_ms=12.0,
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


async def _set_tenant(db: AsyncSession, tid: UUID) -> None:
    # billing_outbox has FORCE RLS — set the tenant context so the enqueue's
    # INSERT WITH CHECK passes (harmless if the test role bypasses RLS).
    await db.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(tid)})


async def test_chat_request_enqueues_billing_outbox_end_to_end(
    db_session: AsyncSession,
) -> None:
    """Sprint 57.84 (US-1/US-5) — a full chat run enqueues an llm_call + a
    tool_call billing event into billing_outbox (the producer side of the flip)."""
    t = await seed_tenant(db_session, code="OBX_E2E_1")
    await _set_tenant(db_session, t.id)
    session_id = uuid4()
    registry = SessionRegistry()
    await registry.register(t.id, session_id)

    stub_loop = _StubLoop(input_tokens=1_200, output_tokens=800, tool_name="salesforce_query")
    trace_ctx = TraceContext(tenant_id=t.id, session_id=session_id)

    await _consume(
        _stream_loop_events(
            stub_loop,
            t.id,
            session_id,
            registry,
            user_input="hello",
            trace_context=trace_ctx,
            billing_outbox=BillingOutboxService(),
            db=db_session,
        )
    )

    rows = (
        (
            await db_session.execute(
                select(BillingOutboxEvent).where(BillingOutboxEvent.tenant_id == t.id)
            )
        )
        .scalars()
        .all()
    )
    event_types = {r.event_type for r in rows}
    assert event_types == {"llm_call", "tool_call"}
    assert len(rows) == 2
    assert all(r.status == "pending" for r in rows)
    assert all(r.session_id == session_id for r in rows)

    llm_row = next(r for r in rows if r.event_type == "llm_call")
    assert llm_row.payload["input_tokens"] == 1_200
    assert llm_row.payload["output_tokens"] == 800
    assert llm_row.payload["model"] == "gpt-5.4"
    assert llm_row.idempotency_key == f"{session_id}:llm:loop"

    tool_row = next(r for r in rows if r.event_type == "tool_call")
    assert tool_row.payload["tool_name"] == "salesforce_query"
    assert tool_row.idempotency_key == f"{session_id}:tool:salesforce_query:0"


# === Sprint 57.82 (B-8 leg-1) verification cost — flipped to outbox in 57.84 ===


class _VerificationStubLoop:
    """Yields a single LoopCompleted carrying BOTH loop + verification (judge) token
    split (as the correction-loop wrapper would stamp). verifier_registry defaults to
    None in _stream_loop_events → wrapper passthrough → this event reaches the router
    observer unchanged."""

    def __init__(
        self,
        *,
        input_tokens: int,
        output_tokens: int,
        verification_input_tokens: int,
        verification_output_tokens: int,
        provider: str = "azure_openai",
        model: str = "gpt-5.4",
        verification_model: str = "gpt-5.4",
    ) -> None:
        self._in = input_tokens
        self._out = output_tokens
        self._vin = verification_input_tokens
        self._vout = verification_output_tokens
        self._provider = provider
        self._model = model
        self._vmodel = verification_model

    async def run(
        self,
        *,
        session_id: UUID,
        user_input: str,
        trace_context: TraceContext,
    ) -> AsyncIterator[object]:
        yield LoopCompleted(
            stop_reason="end_turn",
            total_turns=1,
            total_tokens=self._in + self._out,
            input_tokens=self._in,
            output_tokens=self._out,
            provider=self._provider,
            model=self._model,
            verification_input_tokens=self._vin,
            verification_output_tokens=self._vout,
            verification_model=self._vmodel,
            trace_context=trace_context,
        )


class _SpyQuota:
    """Records the actual_tokens passed to record_usage (duck-typed QuotaEnforcer)."""

    def __init__(self) -> None:
        self.recorded_actual: int | None = None

    async def record_usage(
        self, *, tenant_id: UUID, actual_tokens: int, reserved_tokens: int
    ) -> int:
        self.recorded_actual = actual_tokens
        return actual_tokens


async def test_chat_verification_judge_enqueues_distinct_billing_outbox_event(
    db_session: AsyncSession,
) -> None:
    """Sprint 57.84 (was 57.82): a LoopCompleted carrying judge tokens enqueues a
    DISTINCT `_verification` llm_call billing event, separate from the loop event."""
    t = await seed_tenant(db_session, code="OBX_VERIF_1")
    await _set_tenant(db_session, t.id)
    session_id = uuid4()
    registry = SessionRegistry()
    await registry.register(t.id, session_id)

    stub_loop = _VerificationStubLoop(
        input_tokens=1_000,
        output_tokens=500,
        verification_input_tokens=120,
        verification_output_tokens=8,
    )
    trace_ctx = TraceContext(tenant_id=t.id, session_id=session_id)

    await _consume(
        _stream_loop_events(
            stub_loop,
            t.id,
            session_id,
            registry,
            user_input="hi",
            trace_context=trace_ctx,
            billing_outbox=BillingOutboxService(),
            db=db_session,
        )
    )

    rows = (
        (
            await db_session.execute(
                select(BillingOutboxEvent).where(BillingOutboxEvent.tenant_id == t.id)
            )
        )
        .scalars()
        .all()
    )
    # Two llm_call events: the loop event + the distinct verification event.
    assert len(rows) == 2
    assert all(r.event_type == "llm_call" for r in rows)
    keys = {r.idempotency_key for r in rows}
    assert keys == {f"{session_id}:llm:loop", f"{session_id}:llm:_verification"}

    by_key = {r.idempotency_key: r for r in rows}
    loop_row = by_key[f"{session_id}:llm:loop"]
    verif_row = by_key[f"{session_id}:llm:_verification"]
    assert loop_row.payload["input_tokens"] == 1_000
    assert loop_row.payload["sub_type_suffix"] == ""
    assert verif_row.payload["input_tokens"] == 120
    assert verif_row.payload["output_tokens"] == 8
    assert verif_row.payload["sub_type_suffix"] == "_verification"


async def test_chat_verification_tokens_counted_against_quota(
    db_session: AsyncSession,
) -> None:
    """Sprint 57.82: judge tokens are added to the quota reconcile actual_tokens.

    (Unchanged by the 57.84 flip — the quota-reconcile path is independent of the
    cost-write → billing_outbox flip.)"""
    t = await seed_tenant(db_session, code="OBX_VERIF_Q")
    session_id = uuid4()
    registry = SessionRegistry()
    await registry.register(t.id, session_id)

    spy = _SpyQuota()
    stub_loop = _VerificationStubLoop(
        input_tokens=1_000,
        output_tokens=500,
        verification_input_tokens=120,
        verification_output_tokens=8,
    )
    trace_ctx = TraceContext(tenant_id=t.id, session_id=session_id)

    await _consume(
        _stream_loop_events(
            stub_loop,
            t.id,
            session_id,
            registry,
            user_input="hi",
            trace_context=trace_ctx,
            quota_enforcer=spy,  # type: ignore[arg-type]  # duck-typed spy
            estimated_tokens=2_000,
        )
    )

    # total_tokens (1000+500) + judge (120+8) = 1628
    assert spy.recorded_actual == 1_628
