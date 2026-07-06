"""
File: tests/unit/api/v1/chat/test_scheduler_router.py
Purpose: Cross-burst auto-continue outer-loop (_scheduled_loop_events) — Sprint 57.157.
Category: tests
Scope: Phase 57.157 / Sprint 57.157
Created: 2026-07-06 (Sprint 57.157)
Modified: 2026-07-06

Drives the REAL _scheduled_loop_events generator with a scripted fake loop + fake
todo store + patched settings (no real LLM / DB). Asserts the burst-chaining +
swallow decisions (AC-2..AC-6): OFF = one burst byte-identical; ON + max_turns +
unfinished = auto-continue; complete / end_turn = stop; max_bursts bounds it.
"""

from __future__ import annotations

import importlib
from collections.abc import AsyncIterator
from uuid import UUID

import pytest

from agent_harness._contracts import LoopCompleted, TraceContext
from agent_harness._contracts.todo import Todo

# `from api.v1.chat import router` yields the __init__-re-exported APIRouter instance
# (a package attribute that shadows the submodule); import the real module so
# monkeypatch.setattr targets its get_settings / make_chat_todo_store names.
chat_router = importlib.import_module("api.v1.chat.router")

_TENANT = UUID("11111111-1111-1111-1111-111111111111")
_SESSION = UUID("33333333-3333-3333-3333-333333333333")


class _Marker:
    """A non-LoopCompleted event — helper yields it verbatim with swallow=False."""

    def __init__(self, tag: str) -> None:
        self.tag = tag


class _FakeLoop:
    """loop.run() returns a fresh async gen per call, scripted per burst."""

    def __init__(self, burst_scripts: list[list[object]]) -> None:
        self._scripts = burst_scripts
        self.calls: list[str] = []  # user_input recorded per burst

    def run(
        self, *, session_id: UUID, user_input: str, trace_context: TraceContext
    ) -> AsyncIterator[object]:
        idx = len(self.calls)
        self.calls.append(user_input)
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


def _patch(
    monkeypatch: pytest.MonkeyPatch,
    *,
    enabled: bool,
    max_bursts: int,
    todos: list[Todo],
) -> None:
    class _Settings:
        chat_scheduler_auto_continue = enabled
        chat_scheduler_max_bursts = max_bursts

    monkeypatch.setattr(chat_router, "get_settings", lambda: _Settings())
    monkeypatch.setattr(
        chat_router,
        "make_chat_todo_store",
        lambda db, session_id, tenant_id: _FakeTodoStore(todos),
    )


async def _collect(loop: _FakeLoop) -> list[tuple[object, bool]]:
    out: list[tuple[object, bool]] = []
    async for item in chat_router._scheduled_loop_events(
        loop,
        session_id=_SESSION,
        user_input="go",
        trace_context=TraceContext(),
        db=object(),  # non-None → the todo-store branch runs
        tenant_id=_TENANT,
    ):
        out.append(item)
    return out


def _pending() -> Todo:
    return Todo(id="1", title="step 1", status="pending")


def _completed() -> Todo:
    return Todo(id="1", title="step 1", status="completed")


@pytest.mark.asyncio
async def test_disabled_single_burst_byte_identical(monkeypatch: pytest.MonkeyPatch) -> None:
    # AC-2: scheduler OFF → exactly one burst, swallow always False.
    _patch(monkeypatch, enabled=False, max_bursts=3, todos=[_pending()])
    loop = _FakeLoop([[_Marker("a"), LoopCompleted(stop_reason="max_turns")]])
    out = await _collect(loop)
    assert loop.calls == ["go"]
    assert [sw for (_, sw) in out] == [False, False]


@pytest.mark.asyncio
async def test_on_max_turns_unfinished_continues(monkeypatch: pytest.MonkeyPatch) -> None:
    # AC-3 + AC-7: ON + max_turns + unfinished → 2 bursts; the intermediate
    # max_turns LoopCompleted is swallowed (True); the final end_turn is not.
    _patch(monkeypatch, enabled=True, max_bursts=3, todos=[_pending()])
    loop = _FakeLoop(
        [
            [_Marker("a"), LoopCompleted(stop_reason="max_turns")],
            [_Marker("b"), LoopCompleted(stop_reason="end_turn")],
        ]
    )
    out = await _collect(loop)
    assert len(loop.calls) == 2
    assert loop.calls[1] == chat_router.CONTINUATION_NUDGE
    # marker(F), max_turns(T=swallowed), marker(F), end_turn(F)
    assert [sw for (_, sw) in out] == [False, True, False, False]
    # AC-7: exactly one non-swallowed LoopCompleted reaches the caller.
    finals = [ev for (ev, sw) in out if isinstance(ev, LoopCompleted) and not sw]
    assert len(finals) == 1 and finals[0].stop_reason == "end_turn"


@pytest.mark.asyncio
async def test_on_plan_complete_stops(monkeypatch: pytest.MonkeyPatch) -> None:
    # AC-4: ON + max_turns but plan all completed → does not continue.
    _patch(monkeypatch, enabled=True, max_bursts=3, todos=[_completed()])
    loop = _FakeLoop([[LoopCompleted(stop_reason="max_turns")]])
    out = await _collect(loop)
    assert loop.calls == ["go"]
    assert [sw for (_, sw) in out] == [False]


@pytest.mark.asyncio
async def test_on_end_turn_stops(monkeypatch: pytest.MonkeyPatch) -> None:
    # AC-5: ON + end_turn terminal → single burst.
    _patch(monkeypatch, enabled=True, max_bursts=3, todos=[_pending()])
    loop = _FakeLoop([[LoopCompleted(stop_reason="end_turn")]])
    out = await _collect(loop)
    assert loop.calls == ["go"]
    assert [sw for (_, sw) in out] == [False]


@pytest.mark.asyncio
async def test_max_bursts_bound(monkeypatch: pytest.MonkeyPatch) -> None:
    # AC-6: max_bursts=2 + always max_turns/unfinished → 3 loop.run calls
    # (burst 0,1 swallowed; burst 2 stops as bursts_used==max_bursts).
    _patch(monkeypatch, enabled=True, max_bursts=2, todos=[_pending()])
    loop = _FakeLoop([[LoopCompleted(stop_reason="max_turns")]])  # same script each burst
    out = await _collect(loop)
    assert len(loop.calls) == 3  # 1 initial + 2 continuations
    assert loop.calls == [
        "go",
        chat_router.CONTINUATION_NUDGE,
        chat_router.CONTINUATION_NUDGE,
    ]
    assert [sw for (_, sw) in out] == [True, True, False]


@pytest.mark.asyncio
async def test_empty_plan_stops(monkeypatch: pytest.MonkeyPatch) -> None:
    # ON + max_turns but no todos (agent never called write_todos) → nothing to continue.
    _patch(monkeypatch, enabled=True, max_bursts=3, todos=[])
    loop = _FakeLoop([[LoopCompleted(stop_reason="max_turns")]])
    out = await _collect(loop)
    assert loop.calls == ["go"]
    assert [sw for (_, sw) in out] == [False]
