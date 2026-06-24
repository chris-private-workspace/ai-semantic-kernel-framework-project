"""
File: backend/src/agent_harness/_contracts/todo.py
Purpose: Todo dataclass + JSONB-safe serde — the explicit task-primitive contract.
Category: 範疇 3 adjacent (Cat-3 durable todo-list contract; provider-neutral)
Scope: Phase 57 / Sprint 57.140

Description:
    Defines the explicit, structured task primitive (CC `TodoWrite`-like) the
    chat agent loop maintains across multiple 8-turn sends. A `Todo` is a single
    plan item with an id, a human title, and a lifecycle status
    (pending → in_progress → completed). The list is written whole (replace-whole-
    list, same as CC TodoWrite) via the Cat-2 `write_todos` tool and persisted to
    the `session_todos` table by `DBTodoStore` (state_mgmt/todo_store.py), so a
    follow-up send rehydrates "what's left / what's done" — the durable task spine
    the multi-send long-running model was missing (free-text plans don't survive
    structured).

    Provider-neutral: no LLM / DB type appears in this contract (mirrors
    message_serde.py). The serde round-trips a list to a JSONB-safe list[dict]
    and back, tolerantly (an unknown / missing status normalizes to "pending"; a
    malformed entry is dropped) so a corrupt stored blob never breaks a send.

Key Components:
    - Todo: frozen dataclass (id / title / status)
    - TodoStatus: Literal["pending", "in_progress", "completed"]
    - _todo_to_dict / _todo_from_dict: single-item serde
    - todos_to_jsonb / todos_from_jsonb: list serde (DB JSONB column)
    - summarize_todos: short "(N completed, M in_progress, K pending)" line

Created: 2026-06-24 (Sprint 57.140)
Last Modified: 2026-06-24

Modification History (newest-first):
    - 2026-06-24: Initial creation (Sprint 57.140) — explicit task-primitive contract

Related:
    - _contracts/message_serde.py — the sibling JSONB-safe serde this mirrors
    - state_mgmt/todo_store.py — DBTodoStore (the session_todos ledger consumer)
    - tools/todo_tools.py — write_todos tool (the producer)
    - task-primitive-thin-spike-eval-20260618.md §3-4 — the spike design
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, get_args

TodoStatus = Literal["pending", "in_progress", "completed"]

_VALID_STATUSES: tuple[str, ...] = get_args(TodoStatus)


@dataclass(frozen=True)
class Todo:
    """A single structured plan item the agent maintains across sends."""

    id: str
    title: str
    status: TodoStatus = "pending"


def _normalize_status(raw: Any) -> TodoStatus:
    """Coerce an arbitrary value to a valid TodoStatus (unknown → 'pending')."""
    text = str(raw).strip()
    if text in _VALID_STATUSES:
        return text  # type: ignore[return-value]  # membership-checked against the Literal
    return "pending"


def _todo_to_dict(todo: Todo) -> dict[str, Any]:
    """Serialize a Todo to a JSONB-safe dict."""
    return {"id": todo.id, "title": todo.title, "status": todo.status}


def _todo_from_dict(data: dict[str, Any]) -> Todo | None:
    """Rebuild a Todo from a dict; return None for a malformed entry (no id/title)."""
    todo_id = str(data.get("id", "")).strip()
    title = str(data.get("title", "")).strip()
    if not todo_id or not title:
        return None
    return Todo(id=todo_id, title=title, status=_normalize_status(data.get("status")))


def todos_to_jsonb(todos: list[Todo]) -> list[dict[str, Any]]:
    """Serialize a todo list to the JSONB column value."""
    return [_todo_to_dict(t) for t in todos]


def todos_from_jsonb(data: Any) -> list[Todo]:
    """Rebuild a todo list from a JSONB value, tolerantly (drop malformed entries)."""
    if not isinstance(data, list):
        return []
    out: list[Todo] = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        todo = _todo_from_dict(entry)
        if todo is not None:
            out.append(todo)
    return out


def summarize_todos(todos: list[Todo]) -> str:
    """A short count summary for the write_todos tool's confirmation string."""
    completed = sum(1 for t in todos if t.status == "completed")
    in_progress = sum(1 for t in todos if t.status == "in_progress")
    pending = sum(1 for t in todos if t.status == "pending")
    return (
        f"{len(todos)} todos "
        f"({completed} completed, {in_progress} in_progress, {pending} pending)"
    )


def render_active_plan(todos: list[Todo]) -> str:
    """Render the current todo list as a '## Active Plan' system-prompt section.

    Re-injected at every run start (loop.py) so the agent re-focuses on what's left
    after a new send / compaction — the durable cross-send increment a free-text
    plan lacks. The loop guards on `if todos`, so this is only called for a
    non-empty list.
    """
    lines = [
        "## Active Plan",
        (
            "You have an existing task plan from earlier in this task. Continue from "
            "it — do NOT restart. As you finish each step, call `write_todos` again "
            "with the WHOLE updated list to move items to in_progress / completed."
        ),
        "",
    ]
    lines.extend(f"- [{t.status}] {t.title}" for t in todos)
    return "\n".join(lines)
