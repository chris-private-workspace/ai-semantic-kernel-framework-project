"""
File: backend/src/agent_harness/tools/todo_tools.py
Purpose: write_todos ToolSpec + handler — the explicit task primitive's write side.
Category: 範疇 2 (Tool Layer hosting a Cat 7 backed handler)
Scope: Phase 57 / Sprint 57.140

Description:
    The Cat-2 write side of the explicit task primitive (CC `TodoWrite`-like). The
    agent calls `write_todos` with the WHOLE structured plan (replace-whole-list,
    same as CC TodoWrite); the handler persists it via a bound `TodoStore` so a
    follow-up send rehydrates "what's left / what's done" across multiple sends.

    Naming: deliberately `write_todos` / `Todo` — avoids `task` to not collide with
    the Cat-11 `task_spawn` subagent-dispatch tool (orthogonal concept).

    Risk: `risk_level=LOW` + `annotations.destructive=False` → the loop's
    `_cat9_tool_check` + DEFAULT HITLPolicy auto-approve it (no HITL prompt), so the
    agent calls it freely in-loop. The store is bound per-request to
    (session_id, tenant_id) at the factory (make_chat_todo_store), so the schema
    carries NO tenant/scope fields and sets additionalProperties=False — a forged
    scope arg makes the call schema-invalid before the handler (the bound store
    ignores LLM-supplied scope regardless).

Key Components:
    - WRITE_TODOS_SPEC: the LLM-neutral ToolSpec
    - make_write_todos_handler(store): dual-arity handler factory

Created: 2026-06-24 (Sprint 57.140)
Last Modified: 2026-06-24

Modification History (newest-first):
    - 2026-06-24: Initial creation (Sprint 57.140) — write_todos tool + handler

Related:
    - _contracts/todo.py — Todo + serde + summarize_todos
    - state_mgmt/todo_store.py — DBTodoStore (the persistence target)
    - tools/memory_tools.py — the dual-arity handler pattern this mirrors
    - business_domain/_register_all.py §make_default_executor — opt-in registration
    - sprint-57-140-plan.md §3.1
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from agent_harness._contracts import (
    ConcurrencyPolicy,
    ExecutionContext,
    RiskLevel,
    ToolAnnotations,
    ToolCall,
    ToolHITLPolicy,
    ToolSpec,
)
from agent_harness._contracts.todo import Todo, _todo_from_dict, summarize_todos
from agent_harness.state_mgmt import TodoStore

ToolHandler = Callable[[ToolCall, ExecutionContext], Awaitable[str]]


WRITE_TODOS_SPEC: ToolSpec = ToolSpec(
    name="write_todos",
    description=(
        "Record or update your structured task plan as a whole list. For any "
        "multi-step task, call this FIRST to lay out a plan (3 or more todos), then "
        "call it again to update each todo's status (pending -> in_progress -> "
        "completed) as you finish steps. Always pass the COMPLETE list — this "
        "REPLACES the previous plan. Consult the '## Active Plan' section to see "
        "what is still pending after a new message."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "todos": {
                "type": "array",
                "description": "The complete task plan (replaces the previous list).",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "minLength": 1},
                        "title": {"type": "string", "minLength": 1},
                        "status": {
                            "type": "string",
                            "enum": ["pending", "in_progress", "completed"],
                            "default": "pending",
                        },
                    },
                    "required": ["id", "title"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["todos"],
        "additionalProperties": False,
    },
    annotations=ToolAnnotations(read_only=False, destructive=False, idempotent=True),
    concurrency_policy=ConcurrencyPolicy.SEQUENTIAL,
    hitl_policy=ToolHITLPolicy.AUTO,
    risk_level=RiskLevel.LOW,
    tags=("builtin", "planning"),
)


def make_write_todos_handler(store: TodoStore) -> ToolHandler:
    """Factory: handler that persists a whole todo list via the bound TodoStore.

    The store is bound to (session_id, tenant_id) at construction
    (make_chat_todo_store), so scope is server-authoritative — the handler never
    reads tenant/session from LLM args (the schema forbids them).
    """

    async def handler(call: ToolCall, context: ExecutionContext) -> str:
        del context  # scope is bound to the store; LLM args carry no tenant/session
        args: dict[str, Any] = dict(call.arguments)
        raw = args.get("todos")
        if not isinstance(raw, list):
            return "Error: 'todos' must be a list of {id, title, status} items."

        todos: list[Todo] = []
        for entry in raw:
            if not isinstance(entry, dict):
                continue
            todo = _todo_from_dict(entry)
            if todo is not None:
                todos.append(todo)

        await store.replace(todos)
        return f"Recorded plan: {summarize_todos(todos)}."

    return handler


__all__ = ["WRITE_TODOS_SPEC", "make_write_todos_handler"]
