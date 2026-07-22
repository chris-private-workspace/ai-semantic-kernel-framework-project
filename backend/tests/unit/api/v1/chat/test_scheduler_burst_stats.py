"""
File: backend/tests/unit/api/v1/chat/test_scheduler_burst_stats.py
Purpose: Sprint 57.166 — the final loop_end reports the CROSS-BURST aggregate
    turn/token totals (FE payload + audit), while per-burst billing stays per-burst.
Category: tests / api/v1/chat
Scope: Phase 57 / Sprint 57.166 (AD-Scheduler-Burst-Stats-Aggregate)

Description:
    Drives the REAL _stream_loop_events with a scheduler-ON 2-burst fake loop
    (burst1 max_turns 8 turns / burst2 end_turn 7 turns) + a pending todo store, and
    asserts the aggregate lands where it should and NOT where it must not:
      - T1 audit   — append_audit operation_data == the cross-burst SUM (15 / 170 / …)
      - T2 wire    — the single final loop_end SSE payload total_turns == 15
      - T3 OFF     — scheduler OFF single burst → audit == the one burst (byte-identical)
      - T4 billing — billing_outbox.enqueue receives EACH burst's OWN tokens (no sum)

    MAIN_TRANSCRIPT_OBSERVER is forced false so _max_main_seq (int(await
    db.execute().scalar_one())) is skipped — the pre-existing pitfall that fails the 2
    _make_mock_db-based tests in test_audit_log_observer.py (Day-0 D-audit-observer-
    pre-existing-fails); unrelated to this sprint.

Created: 2026-07-16 (Sprint 57.166)
"""

from __future__ import annotations

import importlib
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from agent_harness._contracts import LoopCompleted, TraceContext
from agent_harness._contracts.todo import Todo

# api.v1.chat.__init__ re-exports `router` (the APIRouter), shadowing the submodule;
# import the real module so monkeypatch targets its get_settings / make_chat_todo_store.
chat_router = importlib.import_module("api.v1.chat.router")


@pytest.fixture(autouse=True)
def _no_main_transcript(monkeypatch: pytest.MonkeyPatch) -> None:
    # Skip _max_main_seq (int(await db.execute().scalar_one())) — it needs a real DB;
    # a mock db returns a coroutine → TypeError (the pre-existing audit-observer trap).
    monkeypatch.setenv("MAIN_TRANSCRIPT_OBSERVER", "false")


class _FakeLoop:
    """loop.run() returns a fresh async gen per call, scripted per burst."""

    def __init__(self, burst_scripts: list[list[object]]) -> None:
        self._scripts = burst_scripts
        self.calls = 0

    def run(self, **_kwargs: Any) -> AsyncIterator[object]:  # noqa: ANN401
        idx = self.calls
        self.calls += 1
        script = self._scripts[idx] if idx < len(self._scripts) else self._scripts[-1]

        async def _gen() -> AsyncIterator[object]:
            for ev in script:
                yield ev

        return _gen()


class _FakeTodoStore:
    def __init__(self, todos: list[Todo]) -> None:
        self._todos = todos

    async def load(self) -> list[Todo]:
        return self._todos


def _make_mock_db() -> Any:
    """AsyncMock db whose begin_nested() is a proper (sync) async-context-manager."""
    db = AsyncMock()
    nested = AsyncMock()
    nested.__aenter__ = AsyncMock(return_value=None)
    nested.__aexit__ = AsyncMock(return_value=None)
    db.begin_nested = MagicMock(return_value=nested)
    return db


def _patch_scheduler(monkeypatch: pytest.MonkeyPatch, *, enabled: bool, todos: list[Todo]) -> None:
    class _Settings:
        chat_scheduler_auto_continue = enabled
        chat_scheduler_max_bursts = 3

    monkeypatch.setattr(chat_router, "get_settings", lambda: _Settings())
    monkeypatch.setattr(
        chat_router,
        "make_chat_todo_store",
        lambda db, session_id, tenant_id: _FakeTodoStore(todos),
    )


def _lc(stop: str, turns: int, total: int, tin: int, tout: int) -> LoopCompleted:
    return LoopCompleted(
        stop_reason=stop,
        total_turns=turns,
        total_tokens=total,
        input_tokens=tin,
        output_tokens=tout,
        model="gpt-5.4",
        provider="azure_openai",
    )


# burst1 hits the ceiling (swallowed → continue); burst2 ends naturally (final).
_TWO_BURST = [
    [_lc("max_turns", 8, 100, 80, 20)],
    [_lc("end_turn", 7, 70, 55, 15)],
]


async def _drive(
    *,
    db: Any,
    billing_outbox: Any = None,
    tenant_id: UUID,
    session_id: UUID,
    scripts: list[list[object]],
) -> None:
    registry = MagicMock()
    registry.mark_completed = AsyncMock()
    gen = chat_router._stream_loop_events(
        loop=_FakeLoop(scripts),
        tenant_id=tenant_id,
        session_id=session_id,
        registry=registry,
        user_input="go",
        trace_context=TraceContext(tenant_id=tenant_id, session_id=session_id),
        db=db,
        billing_outbox=billing_outbox,
    )
    async for _chunk in gen:
        pass


@pytest.mark.asyncio
async def test_audit_operation_data_is_cross_burst_aggregate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """T1: the ONE conversation_completed audit row sums both bursts' counters."""
    monkeypatch.setenv("AUDIT_LOG_CHAT_OBSERVER", "true")
    _patch_scheduler(monkeypatch, enabled=True, todos=[Todo(id="1", title="s", status="pending")])
    tenant_id, session_id = uuid4(), uuid4()
    db = _make_mock_db()

    with (
        patch.object(
            chat_router, "serialize_loop_event", return_value={"type": "loop_end", "data": {}}
        ),
        patch.object(chat_router, "format_sse_message", return_value=b"x"),
        patch.object(chat_router, "append_audit", new=AsyncMock()) as mock_append,
    ):
        await _drive(db=db, tenant_id=tenant_id, session_id=session_id, scripts=_TWO_BURST)

    # Final-burst only → exactly one audit row, carrying the SUM of both bursts.
    assert mock_append.call_count == 1
    op = mock_append.call_args.kwargs["operation_data"]
    assert op["total_turns"] == 15  # 8 + 7
    assert op["total_tokens"] == 170  # 100 + 70
    assert op["input_tokens"] == 135  # 80 + 55
    assert op["output_tokens"] == 35  # 20 + 15


@pytest.mark.asyncio
async def test_final_loop_end_payload_total_turns_is_aggregate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """T2: the single yielded loop_end SSE payload carries the aggregate turn count."""
    monkeypatch.setenv("AUDIT_LOG_CHAT_OBSERVER", "false")
    _patch_scheduler(monkeypatch, enabled=True, todos=[Todo(id="1", title="s", status="pending")])
    tenant_id, session_id = uuid4(), uuid4()

    captured: list[tuple[str, dict[str, Any]]] = []

    def _capture(msg_type: str, data: dict[str, Any]) -> bytes:
        captured.append((msg_type, data))
        return b"x"

    # REAL serialize_loop_event so the payload is the true loop_end dict the router patches.
    with patch.object(chat_router, "format_sse_message", side_effect=_capture):
        await _drive(db=object(), tenant_id=tenant_id, session_id=session_id, scripts=_TWO_BURST)

    loop_ends = [data for (mtype, data) in captured if mtype == "loop_end"]
    # The swallowed intermediate loop_end is NOT yielded → exactly one final frame.
    assert len(loop_ends) == 1
    assert loop_ends[0]["total_turns"] == 15


@pytest.mark.asyncio
async def test_scheduler_off_single_burst_is_byte_identical(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """T3: scheduler OFF → one burst → audit reflects that burst (agg == the one burst)."""
    monkeypatch.setenv("AUDIT_LOG_CHAT_OBSERVER", "true")
    _patch_scheduler(monkeypatch, enabled=False, todos=[Todo(id="1", title="s", status="pending")])
    tenant_id, session_id = uuid4(), uuid4()
    db = _make_mock_db()

    with (
        patch.object(
            chat_router, "serialize_loop_event", return_value={"type": "loop_end", "data": {}}
        ),
        patch.object(chat_router, "format_sse_message", return_value=b"x"),
        patch.object(chat_router, "append_audit", new=AsyncMock()) as mock_append,
    ):
        await _drive(
            db=db,
            tenant_id=tenant_id,
            session_id=session_id,
            scripts=[[_lc("end_turn", 8, 100, 80, 20)]],
        )

    assert mock_append.call_count == 1
    op = mock_append.call_args.kwargs["operation_data"]
    assert op["total_turns"] == 8  # the one burst — no double count
    assert op["total_tokens"] == 100


@pytest.mark.asyncio
async def test_billing_stays_per_burst_no_double_charge(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """T4: each burst's billing enqueue carries its OWN tokens, never the aggregate."""
    monkeypatch.setenv("AUDIT_LOG_CHAT_OBSERVER", "false")
    _patch_scheduler(monkeypatch, enabled=True, todos=[Todo(id="1", title="s", status="pending")])
    tenant_id, session_id = uuid4(), uuid4()
    billing = MagicMock()
    billing.enqueue = AsyncMock()

    with (
        patch.object(
            chat_router, "serialize_loop_event", return_value={"type": "loop_end", "data": {}}
        ),
        patch.object(chat_router, "format_sse_message", return_value=b"x"),
    ):
        await _drive(
            db=object(),
            billing_outbox=billing,
            tenant_id=tenant_id,
            session_id=session_id,
            scripts=_TWO_BURST,
        )

    # Both bursts bill (enqueue is NOT gated on _swallow) — each with its OWN tokens.
    llm_payloads = [
        c.kwargs["payload"]
        for c in billing.enqueue.call_args_list
        if c.kwargs["payload"].get("sub_type_suffix", "") == ""
    ]
    assert len(llm_payloads) == 2
    assert (llm_payloads[0]["input_tokens"], llm_payloads[0]["output_tokens"]) == (80, 20)
    assert (llm_payloads[1]["input_tokens"], llm_payloads[1]["output_tokens"]) == (55, 15)
