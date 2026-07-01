"""
File: backend/tests/unit/agent_harness/tools/test_todo_tools.py
Purpose: Unit tests for the write_todos ToolSpec + handler (Sprint 57.140).
Category: Tests / 範疇 2
Scope: Phase 57 / Sprint 57.140

Description:
    DB-free unit tests for the task primitive's write side (a fake TodoStore):
    - WRITE_TODOS_SPEC is auto-pass (risk=LOW + destructive=False)
    - handler parses the list + calls store.replace + returns a count confirmation
    - replace-whole-list (a 2nd call overwrites, not appends)
    - tolerant of malformed entries (dropped) / rejects a non-list payload

Created: 2026-06-24 (Sprint 57.140)
"""

from __future__ import annotations

import pytest

from agent_harness._contracts import ExecutionContext, RiskLevel, ToolCall
from agent_harness._contracts.todo import Todo
from agent_harness.state_mgmt import TodoStore
from agent_harness.tools.todo_tools import WRITE_TODOS_SPEC, make_write_todos_handler


class _FakeTodoStore(TodoStore):
    """In-memory TodoStore for handler unit tests."""

    def __init__(self) -> None:
        self.todos: list[Todo] = []
        self.replace_calls = 0

    async def load(self) -> list[Todo]:
        return list(self.todos)

    async def replace(self, todos: list[Todo]) -> None:
        self.replace_calls += 1
        self.todos = list(todos)


def _call(todos: object) -> ToolCall:
    return ToolCall(id="tc1", name="write_todos", arguments={"todos": todos})


def test_spec_is_auto_pass() -> None:
    """write_todos must be LOW-risk + non-destructive → auto-pass (no HITL prompt)."""
    assert WRITE_TODOS_SPEC.name == "write_todos"
    assert WRITE_TODOS_SPEC.risk_level == RiskLevel.LOW
    assert WRITE_TODOS_SPEC.annotations.destructive is False
    # schema forbids extra (scope) fields → forged tenant args are schema-invalid
    assert WRITE_TODOS_SPEC.input_schema["additionalProperties"] is False


@pytest.mark.asyncio
async def test_handler_writes_list() -> None:
    """The handler parses the list, calls store.replace, returns a count summary."""
    store = _FakeTodoStore()
    handler = make_write_todos_handler(store)
    result = await handler(
        _call(
            [
                {"id": "1", "title": "research", "status": "in_progress"},
                {"id": "2", "title": "write", "status": "pending"},
                {"id": "3", "title": "review", "status": "pending"},
            ]
        ),
        ExecutionContext(),
    )
    assert store.replace_calls == 1
    assert [t.id for t in store.todos] == ["1", "2", "3"]
    assert store.todos[0].status == "in_progress"
    assert "3 todos" in result


@pytest.mark.asyncio
async def test_handler_replace_whole_list() -> None:
    """A 2nd call OVERWRITES the prior list (CC replace-whole-list)."""
    store = _FakeTodoStore()
    handler = make_write_todos_handler(store)
    await handler(_call([{"id": "1", "title": "a", "status": "pending"}]), ExecutionContext())
    await handler(
        _call(
            [
                {"id": "1", "title": "a", "status": "completed"},
                {"id": "2", "title": "b", "status": "in_progress"},
            ]
        ),
        ExecutionContext(),
    )
    assert store.replace_calls == 2
    assert [(t.id, t.status) for t in store.todos] == [("1", "completed"), ("2", "in_progress")]


@pytest.mark.asyncio
async def test_handler_drops_malformed_entries() -> None:
    """Malformed entries (no id/title, non-dict) are dropped; the rest persist."""
    store = _FakeTodoStore()
    handler = make_write_todos_handler(store)
    await handler(
        _call(
            [
                {"id": "1", "title": "keep"},
                {"id": "", "title": "drop"},
                "not a dict",
            ]
        ),
        ExecutionContext(),
    )
    assert [t.id for t in store.todos] == ["1"]


@pytest.mark.asyncio
async def test_handler_rejects_non_list() -> None:
    """A non-list 'todos' payload returns an error and writes nothing."""
    store = _FakeTodoStore()
    handler = make_write_todos_handler(store)
    result = await handler(_call("not a list"), ExecutionContext())
    assert "Error" in result
    assert store.replace_calls == 0


@pytest.mark.asyncio
async def test_handler_parses_depends_on() -> None:
    """The handler threads per-todo depends_on through to the store (Sprint 57.156 DAG)."""
    store = _FakeTodoStore()
    handler = make_write_todos_handler(store)
    await handler(
        _call(
            [
                {"id": "a", "title": "design", "status": "completed"},
                {"id": "b", "title": "build", "depends_on": ["a"]},
                {"id": "c", "title": "test", "depends_on": ["a", "b", "b"]},  # dedup
            ]
        ),
        ExecutionContext(),
    )
    by_id = {t.id: t for t in store.todos}
    assert by_id["a"].depends_on == ()
    assert by_id["b"].depends_on == ("a",)
    assert by_id["c"].depends_on == ("a", "b")


def test_spec_schema_allows_depends_on() -> None:
    """The write_todos item schema exposes depends_on (array of strings)."""
    item_props = WRITE_TODOS_SPEC.input_schema["properties"]["todos"]["items"]["properties"]
    assert item_props["depends_on"]["type"] == "array"
    assert item_props["depends_on"]["items"]["type"] == "string"
