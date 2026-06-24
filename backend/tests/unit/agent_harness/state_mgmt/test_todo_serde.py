"""
File: backend/tests/unit/agent_harness/state_mgmt/test_todo_serde.py
Purpose: Unit tests for the Todo serde + make_chat_todo_store None-guard (Sprint 57.140).
         (Renamed from test_todo_store.py to avoid a basename clash with the
         integration test_todo_store.py — pytest uses the basename as the module.)
Category: Tests / 範疇 7 + 範疇 3 contract
Scope: Phase 57 / Sprint 57.140

Description:
    DB-free unit tests for the task primitive's contract layer:
    - todos_to_jsonb / todos_from_jsonb round-trip
    - tolerant deserialization (malformed entries dropped; unknown status → pending)
    - _todo_from_dict requires id + title
    - summarize_todos count line
    - make_chat_todo_store all-three-or-nothing None guard
    The DB round-trip / isolation tests live in the integration suite (DBTodoStore
    needs real PG) — mirrors test_message_store.py.

Created: 2026-06-24 (Sprint 57.140)
"""

from __future__ import annotations

from uuid import uuid4

from agent_harness._contracts.todo import (
    Todo,
    _todo_from_dict,
    summarize_todos,
    todos_from_jsonb,
    todos_to_jsonb,
)
from api.v1.chat._category_factories import make_chat_todo_store


def test_serde_round_trip() -> None:
    """todos_to_jsonb then todos_from_jsonb returns the list verbatim."""
    todos = [
        Todo(id="1", title="Research the topic", status="completed"),
        Todo(id="2", title="Draft the answer", status="in_progress"),
        Todo(id="3", title="Review", status="pending"),
    ]
    blob = todos_to_jsonb(todos)
    assert blob == [
        {"id": "1", "title": "Research the topic", "status": "completed"},
        {"id": "2", "title": "Draft the answer", "status": "in_progress"},
        {"id": "3", "title": "Review", "status": "pending"},
    ]
    assert todos_from_jsonb(blob) == todos


def test_serde_drops_malformed_entries() -> None:
    """todos_from_jsonb drops non-dict / missing-id / missing-title entries."""
    raw = [
        {"id": "1", "title": "ok", "status": "pending"},
        {"id": "", "title": "no id"},  # dropped
        {"id": "3", "title": ""},  # dropped
        "not a dict",  # dropped
        {"id": "5", "title": "also ok", "status": "completed"},
    ]
    out = todos_from_jsonb(raw)
    assert [t.id for t in out] == ["1", "5"]


def test_serde_unknown_status_normalizes_to_pending() -> None:
    """An unknown / missing status coerces to 'pending' (never raises)."""
    out = todos_from_jsonb([{"id": "1", "title": "x", "status": "bogus"}])
    assert out[0].status == "pending"
    out2 = todos_from_jsonb([{"id": "2", "title": "y"}])
    assert out2[0].status == "pending"


def test_serde_non_list_returns_empty() -> None:
    """A corrupt (non-list) blob deserializes to [] (never breaks a send)."""
    assert todos_from_jsonb(None) == []
    assert todos_from_jsonb({"not": "a list"}) == []


def test_todo_from_dict_requires_id_and_title() -> None:
    """_todo_from_dict returns None when id or title is blank."""
    assert _todo_from_dict({"id": "1", "title": "ok"}) is not None
    assert _todo_from_dict({"id": "", "title": "ok"}) is None
    assert _todo_from_dict({"id": "1", "title": ""}) is None


def test_summarize_todos_counts() -> None:
    """summarize_todos reports per-status counts."""
    todos = [
        Todo(id="1", title="a", status="completed"),
        Todo(id="2", title="b", status="in_progress"),
        Todo(id="3", title="c", status="pending"),
        Todo(id="4", title="d", status="pending"),
    ]
    summary = summarize_todos(todos)
    assert "4 todos" in summary
    assert "1 completed" in summary
    assert "1 in_progress" in summary
    assert "2 pending" in summary


def test_factory_none_guard() -> None:
    """make_chat_todo_store returns None when db / session / tenant is missing."""
    sid, tid = uuid4(), uuid4()
    assert make_chat_todo_store(None, sid, tid) is None
    assert make_chat_todo_store(object(), None, tid) is None  # type: ignore[arg-type]
    assert make_chat_todo_store(object(), sid, None) is None  # type: ignore[arg-type]
