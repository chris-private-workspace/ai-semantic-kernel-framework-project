# Sprint 57.156 — Checklist (DAG task primitive: dependency-aware todos)

[Plan](./sprint-57-156-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch

### 0.1 Three-prong Day-0 verify (against `main` HEAD `e7b4ba73`)
- [x] **Prong 1 — path verify**: EDIT targets present (`_contracts/todo.py`, `tools/todo_tools.py`, `todo_store.py`, `loop.py`, `sse.py`, `event_wire_schema.py`, `0031_session_todos.py`, `chatStore.ts`, `InspectorTodos.tsx`); `CHANGE-123` free (122 highest); design note `59-*` free (58 highest); NEW `test_todo_dag.py` free
- [ ] **Prong 2 — content verify** (drift → progress.md):
  - [x] **D-todo-contract** — confirmed `Todo = {id,title,status}` frozen (`todo.py:53-59`) + `_todo_{to,from}_dict` single serde chokepoint (`:70-81`) → `depends_on` additive
  - [x] **D-loop-seams-untouched** — confirmed `loop.py:2003` calls `render_active_plan` helper + `:3167-3171` emits `TodosUpdated(tuple[Todo])` → both transparent to a new field; **loop.py UNTOUCHED**
  - [x] **D-sse-serde-driven** — confirmed `sse.py:261` uses `todos_to_jsonb(list(event.todos))` → serde change auto-flows; **sse.py UNTOUCHED**
  - [x] **D-wire-generic** — confirmed `todos_updated = {todos:"Record<string,unknown>[]"}` (`event_wire_schema.py:242-244`) → **NO wire schema change (26) + NO codegen regen**
  - [x] **D-todoitem-fe-shape** — confirmed `chatStore.ts` `TodoItem = {id,title,status}` (:136-140) + `todos_updated` map (:582) + `narrowTodoStatus` → additive `depends_on?` + map parse
  - [x] **D-inspectortodos-shape** — confirmed `InspectorTodos.tsx` `TodoRow` uses `.badge`/`var(--*)` → dep line + blocked badge reuse them; `styles-mockup.css` byte-identical
  - [x] **D-existing-tests** — `test_serde_round_trip:44` byte-exact `blob ==` → +`depends_on:[]` per dict (additive, same-PR)
- [x] **Prong 3 — schema verify**: N/A (no new table/migration — `session_todos.todos` is JSONB whole-list blob per `0031:80-85`; per-todo `depends_on` is schema-free; migration head unchanged)
- [x] **D-baselines** — pytest 3123/6skip · wire 26 · mockup 51 · mypy `src` 399/0 · run_all 11/11 · Vitest 922
- [x] **Catalog drift** — progress.md Day-0 table (8 D-findings)
- [x] **Go/no-go** — scope-shift ~0% (recon done, backend delta 2 files + 2 FE) → proceed

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-156-dag-task-primitive` (from `main` `e7b4ba73`)

---

## Day 1 — Contract + tool (US-1/US-2)

### 1.1 `Todo.depends_on` + serde
- [x] **`Todo += depends_on: tuple[str,...] = ()`** (frozen-safe) + `_todo_to_dict` += `depends_on` list + `_normalize_depends_on` (list[non-empty str], dedup order-preserving, drop self-ref, non-list → `()`) threaded into `_todo_from_dict`
  - DoD: round-trip incl. tolerant drops; no-dep Todo serde byte-identical to 57.140 ✅

### 1.2 `ready_todos` + dependency-aware `render_active_plan`
- [x] **`ready_todos(todos) -> set[str]`** — pending todos whose every KNOWN dep is completed (unknown dep ignored; single-pass cycle-safe)
- [x] **`render_active_plan` deps** — `(ready)` / `(blocked by: <unmet dep titles>)`; no-dep list byte-identical (via `has_deps` branch); instruction updated to "work ready items first"
  - DoD: chain / diamond / unknown-dep / cycle / empty all correct ✅

### 1.3 `write_todos` schema `depends_on` (US-2)
- [x] **`write_todos` items.properties += `depends_on: array[string minLength 1] default []`** + description nudge; `additionalProperties:False` kept; handler UNCHANGED
  - DoD: a `write_todos` call with dependent todos persists them (serde-driven) ✅

### 1.4 Backend tests
- [x] **NEW `test_todo_dag.py`** (14: serde depends_on + ready_todos chain/diamond/unknown/cycle/empty/non-pending + render byte-identical/annotated) + `test_serde_round_trip` byte-exact updated + `test_todo_tools` +2 (parse + schema)

### 1.x Partial gate
- [x] black/isort/flake8 + mypy `src` clean; 28 todo tests green

---

## Day 2 — Frontend dependency render + full gate (US-3)

### 2.1 chat-v2 Todos panel deps
- [x] **`chatStore.ts` `TodoItem += depends_on?: string[]`** + `todos_updated` map narrows the generic prerequisite-id list
- [x] **`InspectorTodos.tsx` render** — per todo with deps: "⤷ needs: <titles>" line + `blocked` badge (computed locally, mirrors backend rule); reuses `.badge`/`var(--*)` only
  - DoD: deps + blocked badge render; no-dep todos unchanged; `diff styles-mockup.css` empty ✅
- [x] **FE test** — +3 DAG (blocked badge + deps line; deps-completed → no badge; badge reuses `.badge`)

### 2.x Full gate
- [x] mypy `src` **399/0** · run_all **11/11** · backend pytest **3139/6skip** (+16) · Vitest **925/148 files** (+3) · `npm run lint && npm run build` clean · mockup **51** (`diff` empty) · black/isort/flake8 + LLM-SDK-leak clean

---

## Day 3 — Drive-through (US-4) — real chat-v2 + real backend + real Azure gpt-5.2

### 3.1 Clean restart (Risk Class E)
- [x] Killed stale backend PID 57580 (5:05 PM = pre-code); no orphan spawn-worker (sole python); fresh sole PID startup-complete 20:28 with DAG code; vite :3007 HMR served FE

### 3.2 Drive-through (MANDATORY — NOT gate-only) — jamie@acme.com, trace `743c72d4…`
- [x] **Leg 1**: agent `write_todos` with `depends_on` (`1→[]`,`2→[1]`,`3→[1]`,`4→[3]`,`5→[4]`); `todos_updated` wire carried depends_on (sse.py UNCHANGED); agent identified "Ready first: Step 1"; panel rendered blocked badges + "⤷ needs" lines (root ready, dependents blocked); verify 0.99
- [x] **Leg 2**: marked step 1 completed → panel LIVE unblocked steps 2+3 (blocked badge removed), 4+5 stay blocked; "1/5 completed" — dynamic re-compute proven
- [x] Screenshots (leg1-blocked + leg2-unblocked) + observed-vs-intended → progress.md Day 3 + `artifacts/`

---

## Day 4 — CHANGE-123 + design note 59 + closeout

### 4.1 CHANGE-123 + design note 59
- [x] **`CHANGE-123-dag-task-primitive.md`** (gap + Todo.depends_on end-to-end + drive-through PASS + AD closed)
- [x] **`59-dag-task-primitive-design.md`** (8-point gate: §2 3 decision matrices + file:line per claim + verify commands + §5 open-invariant split + §6 rollback + §4 no-new-contract)

### 4.2 Closeout
- [x] retrospective.md Q1-Q7 + calibration (`task-primitive-dag-spike` 0.60, 1st pt ~0.95-1.0 IN band → KEEP)
- [x] Final gate sweep: mypy 399/0 · run_all 11/11 · pytest 3139/6skip · Vitest 925 · mockup 51 · build · lint · LLM-SDK-leak clean
- [ ] Navigators: CLAUDE.md Current-Sprint + Last-Updated · MEMORY.md pointer + subfile · next-phase-candidates (CLOSE `AD-TaskPrimitive-DAG-Phase58` + new carryovers) · sprint-workflow matrix (`task-primitive-dag-spike` 0.60 row)
- [x] Anti-pattern self-check (retro Q5): AP-2/3/4/6/8/11 → 0 violations; v2 lints 11/11
- [ ] **Commit** → ⏳ PR push + open → CI → merge: PENDING USER CONFIRMATION (push is outward-facing) → post-merge status flip after gh-verified MERGED
