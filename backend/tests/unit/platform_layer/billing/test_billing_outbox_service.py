"""
File: backend/tests/unit/platform_layer/billing/test_billing_outbox_service.py
Purpose: BillingOutbox producer + pure-logic unit tests (Sprint 57.84 / US-1 + US-2).
Category: Tests / Unit (platform_layer.billing)
Created: 2026-06-05 (Sprint 57.84 Day 2)

Covers the producer (enqueue idempotency, db_session — rolled back) + the pure
helpers (idempotency-key builders, backoff, payload validators). The stateful
drain is integration-tested in tests/integration/billing/test_billing_outbox_drain.py
(needs committed data — the drainer uses its own session factory).
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.models.billing_outbox import BillingOutboxEvent
from platform_layer.billing.billing_outbox import (
    BillingOutboxService,
    _backoff_seconds,
    _payload_int,
    _payload_str,
    llm_idempotency_key,
    tool_idempotency_key,
)
from tests.conftest import seed_tenant

_LLM_PAYLOAD: dict[str, object] = {
    "provider": "azure_openai",
    "model": "gpt-5.4",
    "input_tokens": 100,
    "output_tokens": 50,
    "cached_input_tokens": 0,
    "sub_type_suffix": "",
}


# ----- pure helpers (no DB) -----------------------------------------------


def test_llm_idempotency_key_loop_vs_verification_distinct() -> None:
    sid = uuid4()
    assert llm_idempotency_key(sid, "") == f"{sid}:llm:loop"
    assert llm_idempotency_key(sid, "_verification") == f"{sid}:llm:_verification"
    # loop vs verification are distinct events under the same session.
    assert llm_idempotency_key(sid, "") != llm_idempotency_key(sid, "_verification")


def test_tool_idempotency_key_seq_disambiguates_same_tool() -> None:
    sid = uuid4()
    assert tool_idempotency_key(sid, "web_search", 0) != tool_idempotency_key(sid, "web_search", 1)
    # same (session, tool, seq) → stable key (a replay is a no-op enqueue).
    assert tool_idempotency_key(sid, "web_search", 0) == tool_idempotency_key(sid, "web_search", 0)


def test_backoff_seconds_exponential_and_capped() -> None:
    assert _backoff_seconds(1) == 2
    assert _backoff_seconds(2) == 4
    assert _backoff_seconds(3) == 8
    assert _backoff_seconds(100) == 3600  # capped at _MAX_BACKOFF_S


def test_payload_validators() -> None:
    assert _payload_str({"x": "ok"}, "x") == "ok"
    assert _payload_str({}, "x", "") == ""
    assert _payload_int({"x": 5}, "x") == 5
    assert _payload_int({}, "missing", 0) == 0
    with pytest.raises(ValueError):
        _payload_str({"x": 1}, "x")
    with pytest.raises(ValueError):
        _payload_int({"x": "nope"}, "x")
    with pytest.raises(ValueError):
        _payload_int({"x": True}, "x")  # bool is not a valid int payload value


# ----- enqueue (db_session — rolled back at teardown) ---------------------


@pytest.mark.asyncio
async def test_enqueue_adds_pending_row(db_session: AsyncSession) -> None:
    """US-1 — enqueue writes one pending outbox row in the caller's txn."""
    t = await seed_tenant(db_session, code="OBX_ENQ_1")
    await db_session.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(t.id)})
    sid = uuid4()

    await BillingOutboxService().enqueue(
        db_session,
        tenant_id=t.id,
        event_type="llm_call",
        payload=_LLM_PAYLOAD,
        idempotency_key=llm_idempotency_key(sid, ""),
        session_id=sid,
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
    assert len(rows) == 1
    assert rows[0].event_type == "llm_call"
    assert rows[0].status == "pending"  # server default
    assert rows[0].retry_count == 0
    assert rows[0].session_id == sid
    assert rows[0].payload["model"] == "gpt-5.4"


@pytest.mark.asyncio
async def test_enqueue_duplicate_idempotency_key_is_noop(db_session: AsyncSession) -> None:
    """US-2 — re-enqueuing the same (tenant, idempotency_key) is a no-op (ON CONFLICT)."""
    t = await seed_tenant(db_session, code="OBX_ENQ_DUP")
    await db_session.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(t.id)})
    sid = uuid4()
    key = llm_idempotency_key(sid, "")
    svc = BillingOutboxService()

    await svc.enqueue(
        db_session,
        tenant_id=t.id,
        event_type="llm_call",
        payload=_LLM_PAYLOAD,
        idempotency_key=key,
        session_id=sid,
    )
    # Redelivery of the same logical event — must NOT raise and must NOT duplicate.
    await svc.enqueue(
        db_session,
        tenant_id=t.id,
        event_type="llm_call",
        payload=_LLM_PAYLOAD,
        idempotency_key=key,
        session_id=sid,
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
    assert len(rows) == 1  # ON CONFLICT DO NOTHING — single row
