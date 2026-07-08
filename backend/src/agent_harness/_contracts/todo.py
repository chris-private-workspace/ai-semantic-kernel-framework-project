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
    - Todo: frozen dataclass (id / title / status / depends_on)
    - TodoStatus: Literal["pending", "in_progress", "completed"]
    - _todo_to_dict / _todo_from_dict: single-item serde
    - todos_to_jsonb / todos_from_jsonb: list serde (DB JSONB column)
    - ready_todos: ids of pending todos whose deps are all completed (Sprint 57.156 DAG)
    - detect_cycles: ids of todos participating in a dependency cycle (Sprint 57.162)
    - plan_warnings: non-blocking advisory lines — out-of-order + cycle (Sprint 57.162)
    - render_active_plan: '## Active Plan' section, dependency+cycle-aware (Sprint 57.156/162)
    - summarize_todos: short "(N completed, M in_progress, K pending)" line

Created: 2026-06-24 (Sprint 57.140)
Last Modified: 2026-07-08

Modification History (newest-first):
    - 2026-07-08: Sprint 57.162 — detect_cycles + soft plan advisory + render cycle (DAG)
    - 2026-07-01: Sprint 57.156 — Todo.depends_on + ready_todos + dependency-aware render (DAG)
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
    depends_on: tuple[str, ...] = ()  # ids of prerequisite todos (Sprint 57.156 DAG)


def _normalize_status(raw: Any) -> TodoStatus:
    """Coerce an arbitrary value to a valid TodoStatus (unknown → 'pending')."""
    text = str(raw).strip()
    if text in _VALID_STATUSES:
        return text  # type: ignore[return-value]  # membership-checked against the Literal
    return "pending"


def _normalize_depends_on(raw: Any, *, self_id: str) -> tuple[str, ...]:
    """Coerce an arbitrary value to a clean tuple of prerequisite todo ids.

    Tolerant (Sprint 57.156 DAG): a non-list → (); each entry str()'d + stripped;
    empties dropped; a self-reference dropped (a todo cannot depend on itself);
    order-preserving dedup. A dep referencing a non-existent id is kept here (the
    readiness check ignores unknown ids) — normalization only cleans the shape.
    """
    if not isinstance(raw, list):
        return ()
    out: list[str] = []
    seen: set[str] = set()
    for entry in raw:
        dep = str(entry).strip()
        if not dep or dep == self_id or dep in seen:
            continue
        seen.add(dep)
        out.append(dep)
    return tuple(out)


def _todo_to_dict(todo: Todo) -> dict[str, Any]:
    """Serialize a Todo to a JSONB-safe dict."""
    return {
        "id": todo.id,
        "title": todo.title,
        "status": todo.status,
        "depends_on": list(todo.depends_on),
    }


def _todo_from_dict(data: dict[str, Any]) -> Todo | None:
    """Rebuild a Todo from a dict; return None for a malformed entry (no id/title)."""
    todo_id = str(data.get("id", "")).strip()
    title = str(data.get("title", "")).strip()
    if not todo_id or not title:
        return None
    return Todo(
        id=todo_id,
        title=title,
        status=_normalize_status(data.get("status")),
        depends_on=_normalize_depends_on(data.get("depends_on"), self_id=todo_id),
    )


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


def ready_todos(todos: list[Todo]) -> set[str]:
    """Return the ids of pending todos whose every KNOWN dependency is completed.

    A todo is "ready" (the agent should work it next) iff it is still pending and
    every prerequisite it lists that ALSO EXISTS in the plan is completed. An
    unknown dep id (a typo, or a dep since removed from the list) is IGNORED — it
    must not permanently deadlock the plan (guidance, not enforcement). Single pass
    over direct dependencies, so a dependency cycle simply leaves its nodes
    not-ready (the function never recurses / loops). A no-dep pending todo is
    trivially ready.
    """
    known = {t.id for t in todos}
    completed = {t.id for t in todos if t.status == "completed"}
    ready: set[str] = set()
    for todo in todos:
        if todo.status != "pending":
            continue
        unmet = [d for d in todo.depends_on if d in known and d not in completed]
        if not unmet:
            ready.add(todo.id)
    return ready


def detect_cycles(todos: list[Todo]) -> set[str]:
    """Return the ids of todos that participate in a dependency cycle.

    Considers KNOWN dependency ids only (an unknown / typo'd dep id is ignored,
    consistent with ready_todos) — so a reported cycle is a real closed loop among
    existing todos, not an artefact of a dangling id. Depth-first search with grey
    (on the current path) / black (fully explored) colouring; when a grey node is
    re-encountered every node on the path back to it is a cycle member. Bounded by
    the plan size (the agent writes a handful of todos). Empty for an acyclic plan.
    """
    known = {t.id for t in todos}
    adjacency: dict[str, tuple[str, ...]] = {}
    for todo in todos:
        # first occurrence wins if a malformed blob repeats an id (serde dedups upstream)
        adjacency.setdefault(
            todo.id,
            tuple(d for d in todo.depends_on if d in known and d != todo.id),
        )

    white, grey, black = 0, 1, 2
    color: dict[str, int] = dict.fromkeys(adjacency, white)
    cyclic: set[str] = set()
    path: list[str] = []

    def visit(node: str) -> None:
        color[node] = grey
        path.append(node)
        for dep in adjacency[node]:
            if color.get(dep, black) == grey:
                # back-edge: dep is on the current path → the whole loop is cyclic
                cyclic.update(path[path.index(dep) :])
            elif color.get(dep, black) == white:
                visit(dep)
        path.pop()
        color[node] = black

    for tid in adjacency:
        if color[tid] == white:
            visit(tid)
    return cyclic


def plan_warnings(todos: list[Todo]) -> list[str]:
    """Non-blocking advisory lines about an inconsistent plan; [] when the plan is clean.

    Two advisories, in order (Sprint 57.162, guidance-not-enforcement — the caller
    appends these to the write_todos observation; the write ALWAYS succeeds):
      1. Out-of-order: a todo marked in_progress / completed while a KNOWN prerequisite
         is not yet completed (the agent worked ahead of its own declared order).
      2. Cycle: a dependency cycle among existing todos (those steps can never become
         ready) — surfaced once with the member titles.
    An empty list means no advisory (the handler then returns the plain summary,
    byte-identical to Sprint 57.156).
    """
    title_by_id = {t.id: t.title for t in todos}
    completed = {t.id for t in todos if t.status == "completed"}
    warnings: list[str] = []

    for todo in todos:
        if todo.status not in ("in_progress", "completed"):
            continue
        for dep in todo.depends_on:
            if dep in title_by_id and dep not in completed:
                warnings.append(
                    f"'{todo.title}' is marked {todo.status} but prerequisite "
                    f"'{title_by_id[dep]}' is not completed."
                )

    cyclic = detect_cycles(todos)
    if cyclic:
        titles = [title_by_id[tid] for tid in title_by_id if tid in cyclic]
        warnings.append(
            "Dependency cycle detected among: "
            f"{', '.join(titles)} — these steps can never become ready; "
            "fix their depends_on."
        )
    return warnings


def render_active_plan(todos: list[Todo]) -> str:
    """Render the current todo list as a '## Active Plan' system-prompt section.

    Re-injected at every run start (loop.py) so the agent re-focuses on what's left
    after a new send / compaction — the durable cross-send increment a free-text
    plan lacks. The loop guards on `if todos`, so this is only called for a
    non-empty list.

    Dependency-aware (Sprint 57.156 DAG): when ANY todo declares `depends_on`, each
    pending dependent todo is annotated `(ready)` (all prerequisites completed) or
    `(blocked by: <titles>)` so the agent works unblocked steps first — a NUDGE,
    nothing enforces the order. Cycle-aware (Sprint 57.162): a pending todo that is
    part of a dependency cycle is annotated `(blocked by cycle: <titles>)` instead of
    the misleading plain `(blocked by: ...)`, so a typo'd `depends_on` surfaces as a
    fixable deadlock rather than silently staying not-ready forever. When NO todo has
    a dependency the output is byte-identical to the Sprint 57.140 flat render (same
    instruction, no annotations).
    """
    has_deps = any(t.depends_on for t in todos)
    completed = {t.id for t in todos if t.status == "completed"}
    title_by_id = {t.id: t.title for t in todos}
    # Sprint 57.162: surface a dependency cycle durably (the agent re-reads this at
    # every run start) — a cyclic node is annotated distinctly so a typo'd depends_on
    # is visible, not a silent deadlock. Only computed when the plan actually has deps.
    cyclic = detect_cycles(todos) if has_deps else set()

    if has_deps:
        instruction = (
            "You have an existing task plan from earlier in this task. Continue from "
            "it — do NOT restart. Work the steps marked (ready) first; a step marked "
            "(blocked by: ...) is waiting on a prerequisite to complete. A step marked "
            "(blocked by cycle: ...) is part of a dependency cycle — revise its "
            "depends_on so it can become ready. As you finish each step, call "
            "`write_todos` again with the WHOLE updated list to move items to "
            "in_progress / completed."
        )
    else:
        instruction = (
            "You have an existing task plan from earlier in this task. Continue from "
            "it — do NOT restart. As you finish each step, call `write_todos` again "
            "with the WHOLE updated list to move items to in_progress / completed."
        )

    lines = ["## Active Plan", instruction, ""]
    for todo in todos:
        annotation = ""
        if has_deps and todo.status == "pending" and todo.depends_on:
            if todo.id in cyclic:
                cycle_titles = [title_by_id[tid] for tid in title_by_id if tid in cyclic]
                annotation = f" (blocked by cycle: {', '.join(cycle_titles)})"
            else:
                unmet = [
                    title_by_id.get(d, d)
                    for d in todo.depends_on
                    if d in title_by_id and d not in completed
                ]
                annotation = f" (blocked by: {', '.join(unmet)})" if unmet else " (ready)"
        lines.append(f"- [{todo.status}] {todo.title}{annotation}")
    return "\n".join(lines)
