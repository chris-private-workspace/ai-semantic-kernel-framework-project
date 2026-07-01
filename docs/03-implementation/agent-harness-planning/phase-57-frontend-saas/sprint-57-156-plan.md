# Sprint 57.156 Plan — DAG task primitive: dependency-aware todos

**Summary**: Evolve the Sprint 57.140 LINEAR `write_todos` task primitive into a dependency DAG — each todo gains an optional `depends_on` (prerequisite todo ids), and the agent's re-injected `## Active Plan` marks each item **ready** (deps met) or **blocked** so it works unblocked steps first. Closes `AD-TaskPrimitive-DAG-Phase58` (the 57.140 carryover; its durable spine shipped 57.140). Key scope decision: **guidance, NOT enforcement** — the loop RENDERS ready/blocked hints; it never refuses to let the agent advance a todo (aligns with the agent-autonomy + guardrail-ESCALATE-not-block philosophy, same nudge-not-force as 57.140). The DAG rides entirely on the 57.140 machinery: JSONB blob = **NO migration**, generic `Record<>` wire = **NO wire schema change / NO codegen**, serde-transparent = **loop.py / sse.py / DBTodoStore UNTOUCHED**. Backend delta is concentrated in 2 files (`_contracts/todo.py` + `tools/todo_tools.py`) + 2 FE files. A chat-v2 **drive-through is MANDATORY** (user-facing Todos panel + agent behavior). A **design note (59)** is required (spike sprint — a new capability with real design decisions).

**Status**: Approved-to-execute (user AskUserQuestion pick 2026-07-01 — "B. DAG Task Primitive" after the memory-saturation axis-switch judgment; rolling Selection Rule satisfied).
**Branch**: `feature/sprint-57-156-dag-task-primitive`
**Base**: `main` HEAD `e7b4ba73` (chore flip #365 — Sprint 57.155 MERGED closeout)
**Slice**: closes `AD-TaskPrimitive-DAG-Phase58` (standalone; the DAG evolution of the 57.140 linear primitive — the scheduler `AD-TaskPrimitive-Scheduler-Phase58` remains a SEPARATE slice).
**Scope decisions**: (a) **guidance not enforcement** — render ready/blocked, never block the agent; (b) **direct-dependency readiness** — a todo is ready iff every listed dep is `completed` (single-pass, cycle-safe by construction, NO topological-sort recursion); (c) **unknown dep id → ignored** (treated as satisfied — a typo must not permanently deadlock the plan); (d) **serde-transparent** — reuse `todos_to_jsonb`/`todos_from_jsonb` so migration/wire/loop/sse/store stay byte-identical.

---

## 0. Background

### The gap (`AD-TaskPrimitive-DAG-Phase58`)

- Sprint 57.140 shipped the LINEAR task primitive: `write_todos` writes a flat `[{id,title,status}]` list, durably stored + re-injected as `## Active Plan` each send.
- Real multi-step work is NOT flat — steps have prerequisites ("write the migration only after the schema is designed"; "run tests after both modules land"). The linear list cannot express this, so the agent has no structured signal for **what it can work on NOW** vs **what is blocked**.
- The 57.140 eval (§7-8) explicitly deferred the DAG as `AD-TaskPrimitive-DAG-Phase58`; the durable spine it needs is already shipped.

### Why it matters (the missing capability)

Dependency-awareness lets the agent (and the human watching the Todos panel) reason about execution order across multiple 8-turn sends: work ready steps first, leave blocked ones until their prerequisites complete. It is the first structural step toward autonomous multi-step planning (the scheduler slice builds on it).

### Root cause (recon code read, file:line; ALL re-verified §checklist 0.1)

| Layer | Reality (on `main` HEAD `e7b4ba73`) | Anchor |
|-------|-------------------------------------|--------|
| Contract | `Todo = {id, title, status}` frozen dataclass; serde `todos_{to,from}_jsonb`; `render_active_plan` renders a flat `- [status] title` list | `_contracts/todo.py:53-59,70-81,114-132` |
| Tool | `write_todos` items schema = `{id, title, status}`, `additionalProperties:False`; handler rebuilds via `_todo_from_dict` (field-agnostic) | `tools/todo_tools.py:72-96,113-131` |
| Loop | run-start injects `render_active_plan(load())`; emits `TodosUpdated(todos=tuple[Todo])` after `write_todos` | `loop.py:2000-2004,3167-3171` |
| Store | `DBTodoStore` upserts `todos_to_jsonb(...)` into the `session_todos` JSONB blob | `todo_store.py:110-132` |
| Migration | `session_todos.todos` is `JSONB` (whole list per row) — schema-free per-todo fields | `0031_session_todos.py:80-85` |
| Wire | `todos_updated = {todos: "Record<string, unknown>[]"}` — generic (FE narrows) | `event_wire_schema.py:242-244` |
| SSE | `serialize_loop_event` → `todos_to_jsonb(list(event.todos))` (serde-driven) | `sse.py:258-262` |

→ Adding `Todo.depends_on` + teaching `_todo_{to,from}_dict` + `render_active_plan` about it flows the new field through serde → store/wire/sse/loop are **untouched**. The fix is 2 backend files + the readiness helper + 2 FE files.

### The design (backend: 1 contract field + serde + `ready_todos` + dependency-aware render + 1 tool schema field; FE: 1 type field + 1 render tweak)

```
# _contracts/todo.py
@dataclass(frozen=True)
class Todo:
    id: str
    title: str
    status: TodoStatus = "pending"
    depends_on: tuple[str, ...] = ()        # NEW — prerequisite todo ids

_todo_to_dict   += "depends_on": list(todo.depends_on)
_todo_from_dict += tolerant read (list[non-empty str], dedup, drop self-ref)

def ready_todos(todos) -> set[str]:          # NEW — ids of pending todos whose deps are ALL completed
    completed = {t.id for t in todos if t.status == "completed"}
    return {t.id for t in todos
            if t.status == "pending"
            and all(d in completed for d in t.depends_on if _dep_known(d, todos))}
    # unknown dep id → ignored (typo must not deadlock)

render_active_plan: per todo append "(ready)" / "(blocked by: <unmet dep titles>)"

# tools/todo_tools.py
write_todos items.properties += depends_on: array[string minLength 1]  (default [])
description += "set depends_on to ids of prerequisite todos; work ready items first"

# frontend
chatStore.ts   TodoItem += depends_on?: string[]
InspectorTodos.tsx  render a "blocked" badge / "⤷ needs: …" line per dep
```

Guidance-not-enforcement (scope decision a): `ready_todos` feeds only the RENDER (a nudge in the system prompt); nothing in the loop gates the agent's `write_todos` on it. This matches the 57.140 "nudge, don't force" pattern + V2's agent-autonomy philosophy.

### Ground truth (recon head-start — code read on `main` HEAD `e7b4ba73`; ALL re-verified §checklist 0.1)

- `_contracts/todo.py:53-59` — `Todo` frozen dataclass, 3 fields; `depends_on` appends cleanly as a defaulted 4th (frozen-safe).
- `_contracts/todo.py:70-81` — `_todo_to_dict` / `_todo_from_dict` are the single serde chokepoint; adding a field here reaches store + wire + sse.
- `tools/todo_tools.py:113-131` — handler uses `_todo_from_dict`, so it is field-agnostic (no handler change).
- `sse.py:258-262` — the wire serializer calls `todos_to_jsonb`; a serde change auto-flows to the panel.
- `loop.py:2000-2004,3167-3171` — the two 57.140 seams (`render_active_plan` call + `TodosUpdated` emit) both carry the new field transparently → loop.py UNTOUCHED.

**Baselines (57.155 closeout)**: pytest 3123 / 6 skip · wire 26 · mockup 51 byte-identical · mypy `src` 399/0 · run_all 11/11 · Vitest <re-verify Day-0>. Re-verify Day-0.

### STALE / drift findings (Day-0; full detail → progress.md — placeholder, filled in §checklist 0.1)

- **D-todoitem-fe-shape** — read `chatStore.ts` `TodoItem` current shape (confirm `{id,title,status}` → additive `depends_on?`).
- **D-inspectortodos-shape** — read `InspectorTodos.tsx` current render (confirm the mockup `.badge`/`var(--*)` classes it uses → dependency render reuses them, `styles-mockup.css` byte-identical).
- **D-todo-from-dict-additionalprops** — confirm the tool schema `additionalProperties:False` + `_todo_from_dict` ignore-unknown behavior so a client passing `depends_on` before the schema update is not rejected mid-migration (single PR → not an issue, but note).
- **D-existing-tests** — grep `test_todo_serde.py` / `test_todo_tools` current assertions so the additive field doesn't break a byte-exact serde assertion.
- **D-baselines** — re-verify the 6 gate numbers above.

## 1. Sprint Goal

Ship dependency-aware todos: `Todo.depends_on` end-to-end (contract → serde → tool schema → `## Active Plan` ready/blocked render → chat-v2 Todos panel), guidance-not-enforcement, byte-identical when no todo carries a dep. PROVEN by: the gate set (mypy/pytest/Vitest/run_all/mockup/lint/build/LLM-SDK-leak) + a **MANDATORY chat-v2 drive-through** (real Azure gpt-5.2: the agent plans a task with real prerequisites, the Active Plan marks blocked/ready, the agent works ready first, the Todos panel renders the dependency structure). Produces **CHANGE-123** + **design note 59** (spike).

## 2. User Stories

- **US-1** (contract): 作為 agent loop，我希望 todo 能宣告 `depends_on` 前置，並在 `## Active Plan` 標示 ready/blocked，以便 agent 先做未阻塞的步驟。
- **US-2** (tool): 作為 agent，我希望 `write_todos` 能接受每個 todo 的 `depends_on` id 陣列,以便把計畫表達成依賴圖。
- **US-3** (frontend): 作為看 Todos 面板的 operator，我希望看到每個 todo 的依賴 + blocked 狀態，以便理解 agent 的執行順序。
- **US-4** (drive-through, MANDATORY): 作為使用者，我希望在真 chat-v2 上,agent 對一個有真前置關係的多步任務規劃出 DAG、先做 ready 步驟、面板正確渲染依賴。
- **US-5** (closeout): CHANGE-123 + design note 59 + retro + navigators + AD closed.

## 3. Technical Specifications

### 3.0 Architecture (NO migration / NO wire schema change / NO codegen / loop.py + sse.py + store UNTOUCHED)

```
EDIT  backend/src/agent_harness/_contracts/todo.py     — Todo.depends_on + serde + ready_todos + render_active_plan deps
EDIT  backend/src/agent_harness/tools/todo_tools.py    — write_todos schema items.depends_on + description
EDIT  frontend/src/features/chat_v2/store/chatStore.ts — TodoItem += depends_on?: string[] (+ mergeEvent narrow if needed)
EDIT  frontend/src/features/chat_v2/components/inspector/InspectorTodos.tsx — render deps + blocked badge
NEW   backend/tests/unit/agent_harness/memory|contracts/test_todo_dag.py — depends_on serde + ready_todos + render (deps/ready/blocked/cycle/unknown)
EDIT  backend/tests/…/test_todo_serde.py + test_todo_tools.py — additive assertions (keep 57.140 green)
EDIT  frontend/…/InspectorTodos.test.tsx (or chatStore test) — deps render
UNTOUCHED  loop.py · sse.py · event_wire_schema.py · todo_store.py · 0031 migration · generated/events.json · loopEvents.generated.ts · styles-mockup.css
```

### 3.1 Contract — `_contracts/todo.py` (US-1)

- `Todo += depends_on: tuple[str, ...] = ()` (frozen-safe default).
- `_todo_to_dict` += `"depends_on": list(todo.depends_on)`.
- `_todo_from_dict`: read `depends_on` tolerantly — `[str(x).strip() for x in raw if …]`, drop empties, dedup preserving order, drop self-reference (`d != todo_id`); non-list → `()`.
- NEW `ready_todos(todos: list[Todo]) -> set[str]`: ids of `pending` todos whose every KNOWN dep is `completed` (unknown dep id ignored). Single pass, cycle-safe (no recursion).
- `render_active_plan`: per todo append `(ready)` when `id in ready_todos`, `(blocked by: <unmet dep titles>)` when a pending todo has unmet deps; `completed`/`in_progress` render as today. Update the instruction line to tell the agent to work ready items first.

### 3.2 Tool — `tools/todo_tools.py` (US-2)

- `write_todos` items.properties += `depends_on: {type:array, items:{type:string, minLength:1}, default:[], description:"ids of todos that must be completed first"}`. `additionalProperties:False` stays (the field is now known).
- Extend `description`: "Set `depends_on` to the ids of prerequisite todos; work items that are ready (all deps completed) before blocked ones."
- Handler UNCHANGED (`_todo_from_dict` field-agnostic).

### 3.3 Frontend (US-3) — `chatStore.ts` + `InspectorTodos.tsx`

- `TodoItem += depends_on?: string[]` (optional; older events without it render as no-dep).
- `InspectorTodos.tsx`: per todo, if `depends_on?.length`, render a small "⤷ needs: <titles>" line + a `blocked` badge when any dep is not completed (compute locally from the list — mirror the backend `ready` rule). Reuse existing mockup `.badge` / `var(--*)` classes → `styles-mockup.css` byte-identical.

### 3.x What is explicitly NOT done

- **Enforcement / topological execution ordering** — the loop does not block the agent on readiness (guidance only). If wanted later: `AD-TaskPrimitive-DAG-Enforce-Phase58`.
- **Cross-burst auto-continue scheduler** — separate `AD-TaskPrimitive-Scheduler-Phase58` (research #3).
- **Cycle rejection / auto-repair** — a cycle just renders both nodes blocked (guidance); no validation error raised.
- **Turn-block inline DAG viz** — Inspector Todos tab only (no chat-stream graph).

### 3.y Validation (US-1..US-5)

Gates: mypy `src` 399+ · run_all 11/11 · pytest 3123 + new · Vitest <baseline> + new · mockup 51 (`diff` empty) · `npm run lint && npm run build` (NO `--silent`) · black/isort/flake8 clean · LLM-SDK-leak clean. Plus the §US-4 chat-v2 drive-through (MANDATORY, user-facing).

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 1 | `backend/src/agent_harness/_contracts/todo.py` | EDIT |
| 2 | `backend/src/agent_harness/tools/todo_tools.py` | EDIT |
| 3 | `frontend/src/features/chat_v2/store/chatStore.ts` | EDIT |
| 4 | `frontend/src/features/chat_v2/components/inspector/InspectorTodos.tsx` | EDIT |
| 5 | `backend/tests/unit/agent_harness/.../test_todo_dag.py` | NEW |
| 6 | `backend/tests/.../test_todo_serde.py` + `test_todo_tools.py` | EDIT (additive) |
| 7 | `frontend/.../InspectorTodos.test.tsx` (or chatStore test) | EDIT/NEW |
| — | `loop.py` · `sse.py` · `event_wire_schema.py` · `todo_store.py` · `0031_session_todos.py` · `generated/*` · `styles-mockup.css` | **UNTOUCHED** |

## 5. Acceptance Criteria

1. `Todo.depends_on` round-trips through `todos_to_jsonb`/`todos_from_jsonb` (incl. tolerant drop of self-ref / non-list / empty).
2. `ready_todos` returns exactly the pending todos whose known deps are all completed (unit: chain, diamond, unknown-dep-ignored, cycle→both-not-ready, empty).
3. `render_active_plan` marks `(ready)` / `(blocked by: …)` correctly; a no-dep plan renders byte-identical to 57.140.
4. `write_todos` accepts `depends_on`; a call with dependent todos persists + re-injects them.
5. chat-v2 Todos panel renders deps + a blocked badge; no-dep todos unchanged.
6. **Drive-through PASS (MANDATORY, real UI + backend + LLM)** — real Azure gpt-5.2: agent plans a task with real prerequisites via `write_todos(depends_on=…)`, the Active Plan shows blocked/ready, the agent works a ready step first, the Todos panel renders the dependency structure; screenshot + observed-vs-intended in progress.md. (NOT gate-only.)
7. `AD-TaskPrimitive-DAG-Phase58` CLOSED; CHANGE-123 + design note 59 (8-point gate); calibration recorded; navigators + next-phase-candidates updated.

## 6. Deliverables

- [ ] US-1 `Todo.depends_on` + serde + `ready_todos` + dependency-aware `render_active_plan`
- [ ] US-2 `write_todos` schema `depends_on` + description
- [ ] US-3 chat-v2 Todos panel dependency render + blocked badge
- [ ] US-4 chat-v2 drive-through PASS (real Azure)
- [ ] US-5 CHANGE-123 + design note 59 + retro + navigators + AD closed

## 7. Workload Calibration

- Scope class **NEW `task-primitive-dag-spike` 0.60** (anchored to `task-primitive-spike` 0.60 (57.140, its parent) — same greenfield-capability-on-the-task-primitive shape, but LIGHTER (NO migration / new table / new event / new wire field / store change — reuses ALL 57.140 machinery) OFFSET by the real topological readiness logic + cycle/unknown-dep tolerance + the mandatory real-Azure multi-send drive-through. Per the 57.137 lesson a >~3 hr real-code core holds the 0.60, NOT a tiny-code 0.85 re-point. If the 1st data point lands > 1.20 (drive-through-dominated), re-point toward 0.70).
- **Agent-delegated: no** (parent-direct — a small, tightly-coupled 2-backend-file + 2-FE-file change; agent delegation overhead exceeds the benefit at this size). `agent_factor` 1.0 → 3-segment form.
- Bottom-up est ~10 hr (US-1 ~3 · US-2 ~1 · US-3 ~2 · US-4 drive-through ~2 · US-5 closeout ~2) → class-calibrated commit ~6 hr (mult 0.60). Day-4 retro Q2 verifies.

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| Additive `depends_on` breaks a 57.140 byte-exact serde/schema assertion | Day-0 D-existing-tests grep; keep additive; update assertions in the same PR |
| FE `InspectorTodos` render drift vs mockup fidelity | reuse existing `.badge`/`var(--*)` classes only; `diff styles-mockup.css` must stay empty; Prong 2.5 child-render grep |
| Drive-through: agent may not spontaneously use `depends_on` | the tool description + Active Plan instruction nudge it; prompt the multi-step task explicitly ("plan with prerequisites"); same nudge-worked evidence as 57.140 |
| Stale `--reload` / orphan spawn-worker masks the render change | Risk Class E — clean restart + verify sole live worker (Win32_Process PID/PPID/StartTime) before drive-through; FE = rebuild Vite |
| Cycle / self-dep in agent input | serde drops self-ref; `ready_todos` renders cyclic nodes as blocked (guidance, no crash) — covered by unit tests |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- Topological EXECUTION enforcement — `AD-TaskPrimitive-DAG-Enforce-Phase58`.
- Cross-burst auto-continue scheduler — `AD-TaskPrimitive-Scheduler-Phase58` (research #3).
- Inline turn-block DAG visualization — `AD-TaskPrimitive-DAG-Viz-Phase58`.
- Cycle validation / auto-repair surfaced to the agent — `AD-TaskPrimitive-DAG-CycleReport-Phase58`.
