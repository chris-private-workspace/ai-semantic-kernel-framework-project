# Sprint 57.156 Progress — DAG task primitive: dependency-aware todos

Base `main` HEAD `e7b4ba73` · branch `feature/sprint-57-156-dag-task-primitive` · [plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-156-plan.md) · [checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-156-checklist.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch — 2026-07-01

**三-prong: 0 scope drift, go.** Backend delta concentrated in 2 files (`_contracts/todo.py` + `tools/todo_tools.py`) + 2 FE files; loop.py / sse.py / wire / store / migration all UNTOUCHED as predicted.

### Drift findings

| ID | Finding | Implication |
|----|---------|-------------|
| **D-todo-contract** | `Todo = {id,title,status}` frozen (`todo.py:53-59`); `_todo_{to,from}_dict` single serde chokepoint (`:70-81`) | `depends_on` additive; a serde change reaches store + wire + sse |
| **D-loop-seams-untouched** | `loop.py:2003` calls `render_active_plan` helper; `:3167-3171` emits `TodosUpdated(tuple[Todo])` | both transparent to a new field → **loop.py UNTOUCHED** |
| **D-sse-serde-driven** | `sse.py:261` serializes via `todos_to_jsonb(list(event.todos))` | serde change auto-flows → **sse.py UNTOUCHED** |
| **D-wire-generic** | `todos_updated = {todos:"Record<string,unknown>[]"}` (`event_wire_schema.py:242-244`) | **NO wire schema change (26) + NO codegen regen** |
| **D-todoitem-fe-shape** | `chatStore.ts` `TodoItem = {id,title,status}` (:136-140); `todos_updated` map (:582) + `narrowTodoStatus` | additive `depends_on?: string[]` + map parse |
| **D-inspectortodos-shape** | `InspectorTodos.tsx` `TodoRow` renders `.badge`+title via `var(--*)` | dep line + blocked badge reuse `.badge`; `styles-mockup.css` byte-identical |
| **D-existing-tests** | `test_serde_round_trip:44` asserts byte-exact `blob ==` | +`depends_on:[]` per dict → updated (additive) |
| **D-schema (Prong 3)** | `session_todos.todos` JSONB whole-list blob (`0031:80-85`) | **NO migration** — per-todo `depends_on` schema-free |

**Baselines**: pytest 3123/6skip · wire 26 · mockup 51 · mypy `src` 399/0 · run_all 11/11 · Vitest 922. **Go/no-go**: scope-shift ~0% → proceed.

Branch created from `main` `e7b4ba73`.

## Day 1 — Contract + tool — 2026-07-01

- `_contracts/todo.py`: `Todo += depends_on: tuple[str,...] = ()` + `_todo_to_dict` += `depends_on` list + `_normalize_depends_on` (non-list → (); self-ref/empty dropped; order-preserving dedup) + `_todo_from_dict` threads it + NEW `ready_todos()` (direct-dep, cycle-safe single pass, unknown-dep-ignored) + dependency-aware `render_active_plan` (byte-identical when no todo has deps; `(ready)` / `(blocked by: <titles>)` when deps exist).
- `tools/todo_tools.py`: `write_todos` items schema += `depends_on: array[string minLength 1] default []` + description nudge; handler UNCHANGED.
- Tests: NEW `test_todo_dag.py` (14: depends_on serde/tolerance + ready_todos chain/diamond/unknown/cycle/empty/non-pending + render byte-identical/annotated) + `test_serde_round_trip` byte-exact updated + `test_todo_tools` +2 (depends_on parse + schema).
- Partial gate: 28 todo tests pass · black/isort/flake8 + mypy clean.

## Day 2 — Frontend dependency render + full gate — 2026-07-01

- `chatStore.ts`: `TodoItem += depends_on?: string[]` + `todos_updated` map narrows the generic prerequisite-id list.
- `InspectorTodos.tsx`: per todo with deps a "⤷ needs: <titles>" line + a `blocked` badge (pending todo whose known deps aren't all completed — mirrors backend `ready_todos`); reuses `.badge`/`var(--*)` only.
- FE tests: +3 DAG (blocked badge + deps line; ready = deps completed → no badge; badge reuses `.badge`).
- **Full gate GREEN**: pytest **3139 passed / 6 skip (+16)** · mypy `src` **399/0** · run_all **11/11** · Vitest **925 passed / 148 files (+3)** · mockup **51 byte-identical** (`diff` empty) · `npm run lint && npm run build` clean · black/isort/flake8 + LLM-SDK-leak clean.

## Day 3 — Drive-through (real chat-v2 :3007 + real backend :8000 + real Azure gpt-5.2) — 2026-07-01

**Clean restart (Risk Class E)**: killed stale backend PID 57580 (5:05 PM start = pre-code); no orphan spawn-worker (sole python); fresh sole PID startup-complete 20:28 with DAG code; vite :3007 HMR served the FE. jamie@acme.com · operator · acme-prod.

### Leg 1 — agent authors a DAG (STRONG PASS)

Prompt: a 5-step "add invoices table" task with real prerequisites, asking to use `write_todos` with `depends_on`.

**Observed vs intended**:
- Agent called `write_todos` with each todo's `depends_on`: `1→[]`, `2→[1]`, `3→[1]`, `4→[3]`, `5→[4]` (a real DAG, not a flat list).
- The `todos_updated` wire event carried `depends_on` per todo (trace `743c72d4…`) → **proves sse.py `todos_to_jsonb` auto-flowed the field with sse.py UNCHANGED** (Day-0 prediction confirmed live).
- Agent's answer correctly identified **"Ready to start first: Step 1 (Design the schema)"** → understood the DAG semantics.
- Verification passed 0.99.
- **Todos panel render**: row 1 (root) pending + NO blocked badge + NO deps line; rows 2-5 pending + **blocked** badge + "⤷ needs: <prerequisite title>"; `blocked` badge className = `badge` (mockup class reused, no new CSS); summary "0/5 completed".
- Screenshot: `artifacts/sprint-57-156-leg1-dag-blocked.png`.

### Leg 2 — completing a step dynamically unblocks dependents (STRONG PASS)

Prompt: "I've finished step 1 — mark it completed, tell me which steps are now ready."

**Observed vs intended**:
- Agent called `write_todos` marking step 1 `completed` (deps preserved).
- Todos panel LIVE update: row 1 → **completed**; rows 2+3 (`depends_on:[1]`, now completed) → **blocked badge REMOVED** (ready); rows 4+5 → **still blocked** (their deps 3/4 not completed); summary "1/5 completed".
- Proves the readiness re-computation is dynamic + the FE mirrors the backend rule live via `todos_updated`.
- Screenshot: `artifacts/sprint-57-156-leg2-dag-unblocked.png`.

**Verdict**: Drive-through STRONG PASS both legs — the DAG is authored by the agent, carried on the wire, understood by the agent, and rendered + dynamically re-computed in the panel. Not gate-only. `.env` untouched (no flag — the feature is additive + always-on).

Note (pre-existing, NOT a 57.156 regression): the memory trace showed accumulated cross-sprint identity facts (Dana Okafor vs Chris) from 57.148-153 — the `AD-Verification-Judge-Memory-Inject-Blind` / cross-sprint identity carryovers, unrelated to DAG; the DAG answer + verification were clean.
