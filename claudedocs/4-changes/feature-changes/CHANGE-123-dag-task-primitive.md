# CHANGE-123: DAG task primitive — dependency-aware todos

**Date**: 2026-07-01
**Sprint**: 57.156
**Scope**: 範疇 3 (task primitive) + 範疇 2 (tool) + frontend (chat-v2 Inspector); backend-only + FE, NO migration / wire / codegen

## Problem

The Sprint 57.140 task primitive (`write_todos` + `session_todos` + `## Active Plan` re-injection) modeled a plan as a **flat** `[{id,title,status}]` list. Real multi-step work has prerequisites ("write the migration only after the schema is designed"), which a flat list cannot express — so the agent had no structured signal for what it could work on NOW vs what was blocked. Deferred at 57.140 as `AD-TaskPrimitive-DAG-Phase58`.

## Root Cause

`Todo` carried only `id/title/status`; `render_active_plan` emitted a flat `- [status] title` list with no dependency information; the `write_todos` schema had no way for the agent to declare prerequisites.

## Solution

Evolve the primitive into a dependency DAG, riding entirely on the 57.140 machinery (serde-transparent → JSONB blob = no migration, generic `Record<>` wire = no schema change / no codegen, `render_active_plan` helper + `TodosUpdated` emit carry the field → loop.py / sse.py / DBTodoStore UNTOUCHED):

- **`_contracts/todo.py`**: `Todo += depends_on: tuple[str,...] = ()`; `_normalize_depends_on` (tolerant — non-list → (); self-ref/empty dropped; order-preserving dedup); `_todo_{to,from}_dict` thread it; NEW `ready_todos()` (a pending todo is ready iff every KNOWN dep is completed — direct-dependency, single-pass cycle-safe, unknown-dep-ignored so a typo never deadlocks); dependency-aware `render_active_plan` (`(ready)` / `(blocked by: <titles>)` annotations when any todo has a dep; **byte-identical to 57.140 when none do**).
- **`tools/todo_tools.py`**: `write_todos` items schema += `depends_on: array[string]`; description nudge ("work (ready) items before (blocked by: …)"). Handler UNCHANGED (`_todo_from_dict` field-agnostic).
- **`chatStore.ts`**: `TodoItem += depends_on?: string[]` + `todos_updated` map narrows the list.
- **`InspectorTodos.tsx`**: per-todo "⤷ needs: <titles>" line + a `blocked` badge (mirrors the backend ready rule locally), reusing `.badge` / `var(--*)` only (styles-mockup.css byte-identical).

**Scope decision**: guidance, NOT enforcement — the loop RENDERS ready/blocked hints; it never blocks the agent from advancing a todo (aligns with the agent-autonomy + guardrail-ESCALATE-not-block philosophy, same nudge-not-force as 57.140).

Files (6 + 3 tests): `_contracts/todo.py` · `tools/todo_tools.py` · `chatStore.ts` · `InspectorTodos.tsx` · NEW `test_todo_dag.py` · `test_todo_serde.py` (+1) · `test_todo_tools.py` (+2) · `InspectorTodos.test.tsx` (+3). UNTOUCHED: loop.py · sse.py · event_wire_schema.py · todo_store.py · 0031 migration · generated/*.

## Verification

- **Gates**: pytest **3139 passed / 6 skip** (+16) · mypy `src` **399/0** · run_all **11/11** · Vitest **925 passed / 148 files** (+3) · mockup **51 byte-identical** · `npm run lint && npm run build` clean · black/isort/flake8 + LLM-SDK-leak clean.
- **Drive-through STRONG PASS** (real chat-v2 :3007 + real backend + real Azure gpt-5.2; jamie@acme.com, trace `743c72d4…`):
  - **Leg 1**: a 5-step "add invoices table" task → agent `write_todos` with `depends_on` (`1→[]`, `2→[1]`, `3→[1]`, `4→[3]`, `5→[4]`); the `todos_updated` wire event carried `depends_on` (sse.py UNCHANGED); agent identified "Ready first: Step 1"; panel rendered blocked badges + "⤷ needs" lines (root ready, dependents blocked); verification 0.99.
  - **Leg 2**: marking step 1 completed → panel LIVE unblocked steps 2+3 (blocked badge removed), kept 4+5 blocked; "1/5 completed".
  - Screenshots: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-156/artifacts/sprint-57-156-leg{1,2}-*.png`.

## Impact

Backend (範疇 2/3) + frontend (chat-v2 Inspector). NO migration / wire schema change / codegen / loop.py / sse.py / store change. Additive + always-on (no env flag); a plan with no `depends_on` is byte-identical to 57.140. Closes `AD-TaskPrimitive-DAG-Phase58`. Design note `59-dag-task-primitive-design.md`.
