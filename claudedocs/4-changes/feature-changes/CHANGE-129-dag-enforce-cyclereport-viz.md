# CHANGE-129: DAG task primitive — soft-enforce advisory + cycle report + Inspector Viz

**Date**: 2026-07-08
**Sprint**: 57.162
**Scope**: 範疇 2 (Tool Layer handler) + 範疇 3-adjacent (`_contracts/todo.py`) + Frontend (chat_v2 Inspector). Backend 2 files + FE 1 file. NO migration / wire (26) / codegen / sse.py / loop.py-signature / store change.

## Problem

Sprint 57.156 shipped the DAG data model (`Todo.depends_on` + `ready_todos` + dependency-aware render + FE `⤷ needs`/`blocked` badge) but left 3 carryovers open:
- **DAG-Enforce** — nothing signals the agent when it works out of dependency order (marks a dependent `in_progress`/`completed` before its prerequisite is done).
- **CycleReport** — `ready_todos` is "cycle-safe by construction" but a cycle is NEVER surfaced: cyclic todos silently stay not-ready forever and a pending cyclic node even rendered the misleading `(blocked by: <titles>)` as if it were a normal, resolvable block.
- **Viz** — the Inspector Todos tab is a flat list with a textual `⤷ needs` line; the DAG structure (parallelizable layers, downstream chains) isn't visible.

## Root Cause

The 57.156 primitive is deliberately **guidance-not-enforcement**, and the three gaps are the missing "surfacing" half of that guidance: the handler returned only a plain summary (`tools/todo_tools.py:142`); `ready_todos`/`render_active_plan` never distinguished a cycle from a normal block (`_contracts/todo.py`); the FE only rendered a flat list.

## Solution

**Enforce semantics = SOFT** (user AskUserQuestion pick, preserving guidance-not-enforcement):

- `_contracts/todo.py`:
  - `detect_cycles(todos) -> set[str]` — DFS grey/black over known-deps-only adjacency (unknown/self deps ignored, consistent with `ready_todos`); returns cyclic ids.
  - `plan_warnings(todos) -> list[str]` — out-of-order lines (a non-pending todo with an unmet KNOWN prereq) + one cycle line; `[]` when clean.
  - `render_active_plan` — a cyclic pending node renders `(blocked by cycle: <titles>)` instead of the misleading plain `(blocked by: …)`; no-dep plans stay byte-identical to Sprint 57.140.
- `tools/todo_tools.py` — the `write_todos` handler appends the `plan_warnings` output as a `⚠️ Plan advisory (not blocking):` block to its observation. **The write ALWAYS succeeds** (a NUDGE); a clean plan appends nothing (byte-identical to 57.156).
- `InspectorTodos.tsx` — a NEW inline `TodoDagGraph`: longest-path (cycle-guarded) topological levels; fixed-size circular nodes coloured by status/blocked/cycle via existing `var(--*)` tokens (`--success`/`--info`/`--warning`/`--danger`/`--border-strong`), numbered 1..N with the full title in `aria-label` (keeps `getByText` unique to the flat list); SVG edges in `var(--border)` (cycle edge dashed `var(--danger)`). Rendered only when the plan has a dependency; the flat list is retained below as the a11y/textual fallback. No new CSS / no oklch literal → `styles-mockup.css` byte-identical.

Rides the 57.140/156 machinery serde-transparently: the wire already carries `depends_on` since 57.156 (`sse.py:261` `todos_to_jsonb`), so Viz needs zero backend/wire change.

## Verification

- Gates: mypy `src` **400/0** · run_all **11/11** · backend pytest **3223 passed / 6 skipped** (+17: `test_todo_dag.py` +14, `test_todo_tools.py` +3) · Vitest **930 passed** (149 files, +3) · `npm run lint` + `npm run build` rc=0 · mockup **51 byte-identical** (no new hex/oklch) · black/isort/flake8 + LLM-SDK-leak clean.
- **Drive-through STRONG PASS** — real chat-v2 :3007 + fresh backend (57.162 code) + real Azure gpt-5.2 (session `344890a3…`, `stop: end_turn`, Verification 0.99). Agent `write_todos` a 4-item DAG (`b` in_progress before prereq `a`; `c↔d` cycle):
  - Advisory in the REAL observation: `Recorded plan: 4 todos…` + `⚠️ Plan advisory (not blocking):` + the out-of-order line (Write migration) + the cycle line (Deploy service, Run smoke tests) → **write succeeded, not rejected = soft enforce confirmed live**.
  - Viz in the REAL Inspector Todos tab: `todo-dag-graph` 238×94px, 4 nodes labelled 1-4, edges `a→b` solid + `c↔d` dashed cycle, cycle-node markers c/d, cyclic node border computed `2px dashed oklch(0.65 0.21 25)` (`var(--danger)` resolves), flat list retained.
  - Screenshot: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-162/artifacts/sprint-57-162-drivethrough-dag-viz-advisory.png`.
- Honest scope: the durable `render_active_plan` cycle annotation (cross-send system-prompt injection, not directly UI-visible) is unit-tested (`test_render_cycle_annotates_distinctly`); it shares `detect_cycles` with the drive-through-proven immediate advisory.

## Impact

Backend-only handler/contract + FE-only Viz. Closes `AD-TaskPrimitive-DAG-Enforce-Phase58` (soft) + `AD-TaskPrimitive-DAG-CycleReport-Phase58` + `AD-TaskPrimitive-DAG-Viz-Phase58` — the DAG arc's final slice. Guidance-not-enforcement preserved (no hard reject; `token_counter`-style opt-in not needed — the advisory is additive and self-limiting). **No new carryover AD** (per user directive 完成即暫停, 不要產生其他工作). No design note (bounded feature slice, not a research-eval spike).
