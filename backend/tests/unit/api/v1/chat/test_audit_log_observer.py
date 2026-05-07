"""
File: backend/tests/unit/api/v1/chat/test_audit_log_observer.py
Purpose: Verify chat router audit_log observer (Sprint 57.6 US-3 / R3 / closes 57.5 D-17).
Category: tests / api/v1/chat
Scope: Sprint 57.6 Day 2 US-3 narrow scope (audit_log only;sessions + tool_calls
       observers split as AD-Reality-3a/3b deferred Phase 57.7+ per Day 2 探勘
       finding — both require user_id JWT extraction infra not yet built in V2).

Description:
    Sprint 57.5 Reality Check D-17 confirmed `audit_log` table has 0 row delta
    after a chat session — chat router emits SSE LoopCompleted but does not
    append to the hash-chained audit_log。Sprint 57.6 Day 2 US-3 wires an
    audit_log observer at LoopCompleted via `append_audit()` helper from
    infrastructure/db/audit_helper.py。

    Tests directly exercise `_stream_loop_events` async generator with mocked
    dependencies(`run_with_verification` patched to yield a fake LoopCompleted;
    `append_audit` patched to capture call args / simulate failure)。

Created: 2026-05-08 (Sprint 57.6 Day 2)

Modification History:
    - 2026-05-08: Sprint 57.6 Day 2 US-3 — initial creation (closes AD-Reality-3-audit_log)

Related:
    - backend/src/api/v1/chat/router.py L308+ — `_stream_loop_events` audit_log hook
    - backend/src/infrastructure/db/audit_helper.py:90 — `append_audit()` helper
    - 57.5 reality check D-17 — `audit_log 0 row delta` finding
"""

from __future__ import annotations

import importlib
import os
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from agent_harness._contracts import LoopCompleted, TraceContext

# Sprint 57.6 Day 4 — the integration tests/conftest.py disables the audit
# observer via AUDIT_LOG_CHAT_OBSERVER=false. This unit test file MUST override
# back to "true" so the observer code path actually exercises in test env;tests
# patch append_audit directly to capture call args without hitting DB。
os.environ["AUDIT_LOG_CHAT_OBSERVER"] = "true"

# `api.v1.chat.__init__` does `from .router import router` which shadows the
# submodule reference at the package namespace。Use importlib to grab the actual
# module (with `_stream_loop_events` / `append_audit` / `serialize_loop_event`)。
chat_router_module = importlib.import_module("api.v1.chat.router")


def _make_mock_db() -> Any:
    """Mock AsyncSession with `begin_nested` returning async context manager.

    Real SQLAlchemy `AsyncSession.begin_nested()` is a sync method returning an
    `AsyncSessionTransaction` context manager。AsyncMock() default makes EVERY
    method async (returns coroutine),which breaks `async with db.begin_nested():`
    with `TypeError: 'coroutine' object does not support the asynchronous context
    manager protocol`。Override begin_nested with MagicMock returning proper
    async context manager。
    """
    db = AsyncMock()
    nested_ctx = AsyncMock()
    nested_ctx.__aenter__ = AsyncMock(return_value=None)
    nested_ctx.__aexit__ = AsyncMock(return_value=None)
    db.begin_nested = MagicMock(return_value=nested_ctx)
    return db


def _make_loop_completed(
    *,
    total_turns: int = 2,
    total_tokens: int = 150,
    input_tokens: int = 100,
    output_tokens: int = 50,
    model: str = "gpt-5.4",
    provider: str = "azure_openai",
) -> LoopCompleted:
    """Construct a minimal LoopCompleted event for the observer to consume."""
    return LoopCompleted(
        total_turns=total_turns,
        total_tokens=total_tokens,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        model=model,
        provider=provider,
    )


async def _drive_stream(
    *,
    fake_event: Any,
    db: Any,
    tenant_id: UUID | None = None,
    session_id: UUID | None = None,
) -> int:
    """Drive `_stream_loop_events` to completion;return SSE frame count.

    Patches `run_with_verification` to yield exactly one fake event so the
    LoopCompleted handler runs exactly once;patches `serialize_loop_event` /
    `format_sse_message` to return trivial bytes so SSE iteration completes。
    """
    chat_router = chat_router_module

    tenant_id = tenant_id or uuid4()
    session_id = session_id or uuid4()
    trace_ctx = TraceContext(tenant_id=tenant_id, session_id=session_id)

    async def _fake_rwv(**_kwargs: Any) -> Any:  # noqa: ANN401
        yield fake_event

    fake_registry = MagicMock()
    fake_registry.mark_completed = AsyncMock()

    with (
        patch.object(chat_router, "run_with_verification", _fake_rwv),
        patch.object(
            chat_router,
            "serialize_loop_event",
            return_value={"type": "loop_completed", "data": {"x": 1}},
        ),
        patch.object(chat_router, "format_sse_message", return_value=b"data: x\n\n"),
    ):
        gen = chat_router._stream_loop_events(
            loop=MagicMock(),  # AgentLoopImpl unused — run_with_verification patched out
            tenant_id=tenant_id,
            session_id=session_id,
            registry=fake_registry,
            user_input="hello",
            trace_context=trace_ctx,
            db=db,
        )
        frames: list[bytes] = []
        async for chunk in gen:
            frames.append(chunk)
        return len(frames)


@pytest.mark.asyncio
async def test_audit_log_observer_appends_on_loop_completed() -> None:
    """LoopCompleted event must trigger `append_audit` with operation=conversation_completed."""
    chat_router = chat_router_module

    tenant_id = uuid4()
    session_id = uuid4()
    db = _make_mock_db()
    fake_event = _make_loop_completed()

    with patch.object(chat_router, "append_audit", new=AsyncMock()) as mock_append:
        frames = await _drive_stream(
            fake_event=fake_event,
            db=db,
            tenant_id=tenant_id,
            session_id=session_id,
        )

    assert frames == 1, f"Expected 1 SSE frame from fake LoopCompleted, got {frames}"
    assert (
        mock_append.call_count == 1
    ), f"Expected append_audit called exactly once, got {mock_append.call_count}"
    # Verify call args structure (audit chain integrity preserved by helper).
    call = mock_append.call_args
    assert call.kwargs["tenant_id"] == tenant_id
    assert call.kwargs["operation"] == "conversation_completed"
    assert call.kwargs["resource_type"] == "session"
    assert call.kwargs["resource_id"] == str(session_id)
    assert call.kwargs["session_id"] == session_id
    assert call.kwargs["user_id"] is None  # system actor (no JWT user_id in V2 yet)
    assert call.kwargs["operation_result"] == "success"
    # operation_data carries the loop-completion outcome metadata.
    op_data = call.kwargs["operation_data"]
    assert op_data["total_turns"] == 2
    assert op_data["total_tokens"] == 150
    assert op_data["input_tokens"] == 100
    assert op_data["output_tokens"] == 50
    assert op_data["model"] == "gpt-5.4"
    assert op_data["provider"] == "azure_openai"
    assert op_data["outcome"] == "completed"


@pytest.mark.asyncio
async def test_audit_log_observer_skipped_when_db_none() -> None:
    """When db is None (e.g. test client without DB session), append_audit must NOT be called."""
    chat_router = chat_router_module

    fake_event = _make_loop_completed()

    with patch.object(chat_router, "append_audit", new=AsyncMock()) as mock_append:
        frames = await _drive_stream(fake_event=fake_event, db=None)

    assert frames == 1
    assert mock_append.call_count == 0, "append_audit should be skipped when db=None"


@pytest.mark.asyncio
async def test_audit_log_observer_failure_does_not_break_stream() -> None:
    """append_audit raising must NOT abort the SSE stream — best-effort isolation."""
    chat_router = chat_router_module

    fake_event = _make_loop_completed()
    db = _make_mock_db()

    failing_append = AsyncMock(side_effect=RuntimeError("simulated DB write failure"))

    with patch.object(chat_router, "append_audit", new=failing_append):
        # Stream must still yield 1 frame for the LoopCompleted event;
        # the failing audit append is logged + swallowed by the observer.
        frames = await _drive_stream(fake_event=fake_event, db=db)

    assert frames == 1, (
        f"Expected SSE stream to complete despite audit_log failure, " f"got {frames} frames"
    )
    assert (
        failing_append.call_count == 1
    ), "append_audit must still have been attempted exactly once before failing"
