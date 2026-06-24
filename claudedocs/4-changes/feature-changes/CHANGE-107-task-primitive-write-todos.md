# CHANGE-107: Explicit todo-list task primitive (write_todos + durable store + chat-v2 panel)

**Date**: 2026-06-24
**Sprint**: 57.140
**Scope**: Cat 2 (Tool) + Cat 3/7 (durable store) + Cat 5 (prompt) + Cat 1 (loop emit/inject) + Cat 12 (wire) + frontend

## Problem

The chat agent loop plans, but the plan is **natural-language free text** — emergent, with no structure, no durable state, and no user visibility. Long tasks span multiple 8-turn sends (`max_turns=8`); a free-text plan is only rehydrated back as conversation, so the agent has no structured, durable, updatable task state telling it "what's left / what's done" after a new send / compaction. (Research #1, `task-primitive-thin-spike-eval-20260618.md`.)

## Root Cause

`DurableState.metadata` is pause-scoped (only written on `_emit_state_checkpoint`) → insufficient for clean-end multi-send. No `tasks:[{id,status}]` / checklist / step tracker existed anywhere (3-agent grep). The durable cross-send precedent is `DBMessageStore` (57.127): load at run-start, append at clean-end.

## Solution

A full vertical slice (mirroring each layer's recent precedent):

- **Cat 2 tool** — `write_todos` (`tools/todo_tools.py`): replace-whole-list semantics (CC TodoWrite), `risk=LOW`+`destructive=False` → auto-passes (no HITL prompt) under any tenant policy, `additionalProperties:False` (forged scope args schema-invalid). Dual-arity handler persists via a bound store. Opt-in registered in `make_default_executor` (mirrors skills 57.113).
- **Cat 3/7 store** — `DBTodoStore` (`state_mgmt/todo_store.py`, `TodoStore` ABC) over a NEW `session_todos` table (migration 0031, 1 row/session, JSONB, tenant-scoped RLS mirroring 0030). `replace` = upsert on `session_id`, best-effort SAVEPOINT. `Todo` contract + tolerant serde in `_contracts/todo.py`. Wired via `make_chat_todo_store` (all-three-or-nothing).
- **Cat 5 prompt** — DEMO_SYSTEM_PROMPT plan-first nudge (static, build-time).
- **Cat 1 loop** — run-start `## Active Plan` re-injection (`loop.run()`, async — `build_real_llm_handler` is sync so the dynamic load lives here) + emit `TodosUpdated` after a successful `write_todos` call (re-reads the store). 2 bounded loop.py edits; injection NOT in handler (sync constraint).
- **Cat 12 wire** — `todos_updated` event (6-file pipeline, WIRE_SCHEMA 25→26, `todos: Record<string,unknown>[]`).
- **Frontend** — `chatStore` `TodoItem` + `todos` slice + `mergeEvent` narrow; NEW 5th Inspector "Todos" tab (`InspectorTodos.tsx`, existing mockup `.badge`/`.tab` classes — styles-mockup.css UNTOUCHED).

Naming avoids `task` (collides with Cat 11 `task_spawn`): `write_todos`/`Todo`/`session_todos`/`todos_updated`.

PR: feature/sprint-57-140-task-primitive-spike. ~28 files.

## Verification

- **Gates**: mypy `src` 0/380 · v2 lints 10/10 (incl. check_llm_sdk_leak — neutrality preserved) · backend pytest 2843 +5skip · Vitest 920 · `npm run build` pass · mockup-fidelity 51 byte-identical · black/isort/flake8 clean.
- **Tests**: serde+factory unit (7) · tool handler unit (5) · DBTodoStore integration (5, real PG) · wire parity (TodosUpdated instance) · 3 count tests 25→26 · 4 InspectorTodos Vitest.
- **Drive-through (STRONG PASS, real Azure gpt-5.2)**: send 1 → agent proactively `write_todos` 3 items → panel 3/3 completed; send 2 (cross-send) → rehydrated the 3 + added a 4th → panel 4/4 completed. The agent continued FROM the durable structured list across sends (the key increment vs free-text). AP-4 "agent ignores the list" risk FALSIFIED. Screenshots in `sprint-57-140/artifacts/`.

## Impact

Full-stack (backend + 1 migration + frontend). Default path UNCHANGED for sessions without the store (all-three-or-nothing → no panel, agent still works). Closes research #1 (the linear durable task primitive); DAG / scheduler / `max_turns` relaxation remain out of scope (eval §7-8). Design note 44.
