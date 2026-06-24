# Sprint 57.140 Plan — explicit todo-list task primitive (write_todos tool + durable store + chat-v2 panel)

**Summary**: Ships the first vertical slice of an explicit, structured, durable task primitive (CC `TodoWrite`-like) for the chat agent loop, closing research #1 (`task-primitive-thin-spike-eval-20260618.md`). Today the agent's plan is emergent free-text — no structure, no durable state, invisible to the user. This spike adds a `write_todos` builtin tool (Cat 2, replace-whole-list, auto-pass) + a dedicated `session_todos` DB store (Cat 3/7, mirrors `DBMessageStore`, survives cross-send) + run-start re-injection of the list into the system prompt (Cat 5) + a `todos_updated` wire event (Cat 12) + a chat-v2 Inspector "Todos" panel. **The drive-through is MANDATORY and is the whole point**: it is the only thing that proves the load-bearing thesis — that the agent will *proactively maintain* the list across multiple 8-turn sends, not write it once and ignore it (the AP-4 risk). Spike sprint → a design note (44) is required. Storage = dedicated table (user-confirmed eval option C); scope = single vertical slice (user-confirmed).

**Status**: Approved-to-execute (user 2026-06-24 — "從 #1 task-primitive 開始"; storage + scope forks confirmed via AskUserQuestion: dedicated `session_todos` table + single vertical slice)
**Branch**: `feature/sprint-57-140-task-primitive-spike`
**Base**: `main` HEAD `313a3e31` (Sprint 57.139 layered-compaction flip #332 merged)
**Slice**: closes research #1 `Explicit task primitive` (tracked under `5-status/task-primitive-thin-spike-eval-20260618.md`, no separate AD); standalone spike (1st of the canonical net-new block after #6/#3/#8/#4)
**Scope decisions**: (a) storage = dedicated `session_todos` table + `DBTodoStore` mirroring `DBMessageStore` (eval §3.1-C; cross-send + clean-end durable) (b) tool = `write_todos`, replace-whole-list semantics, `risk=LOW`+`destructive=False` → auto-pass under any tenant policy (c) **naming avoids `task`** (collides with Cat 11 `task_spawn`) — tool `write_todos`, store `TodoStore`, table `session_todos`, contract `Todo`, wire event `todos_updated` (this DEVIATES from the eval §3.3 literal `tasks_updated` to honour the eval §3.2 naming principle fully) (d) run-start injection lives in `handler.py` (per-request, mirrors 57.115 `## Active Skill`) → NO loop.py for injection; loop.py gets ONE bounded edit (emit `TodosUpdated` after a successful `write_todos` tool call) (e) linear list + status only — NO dependency graph / scheduler / `max_turns` change (eval §7 boundary)

---

## 0. Background

### The gap (research #1, per `task-primitive-thin-spike-eval-20260618.md`)

The chat agent loop plans, but the plan is **natural-language free text** — emergent, with no system-prompt enforcement, no structure, no durable state, and no user visibility.

CC's `TodoWrite` gives a **structured + durable + updatable + visible** todo state: the agent marks items `pending → in_progress → completed` as it works, and the list is both a mid-run re-focus anchor and a user progress window.

### Why it matters (the missing capability)

This platform's long tasks **span multiple 8-turn sends** (`max_turns=8`; continuity via Cat 3 rehydration + compaction). A free-text plan is only rehydrated back as conversation — there is **no structured, durable, updatable task state** that lets the agent know, after a new send / compaction, "what's left and what's done". The explicit task primitive is the **durable task spine** the multi-send long-running model is missing — not a decorative nice-to-have.

### Root cause (recon code read, file:line; ALL re-verified §checklist 0.1)

| Layer | Reality (on `main` HEAD `313a3e31`) | Anchor |
|-------|-------------------------------------|--------|
| System prompt | pure tool-use guidance; NO "plan-first / track steps" instruction | `api/v1/chat/handler.py:147` (DEMO_SYSTEM_PROMPT) |
| Durable state | `DurableState.metadata` is **pause-scoped** (only written on `_emit_state_checkpoint`) → insufficient for clean-end multi-send | `_contracts/state.py` metadata + `loop.py` checkpoint path |
| Cross-send durable precedent | `DBMessageStore` loads at run-start, appends at clean-end → survives multi-send | `state_mgmt/message_store.py:74-150` · ABC `state_mgmt/_abc.py:64-89` |
| Factory wiring precedent | `make_chat_message_store` all-three-or-nothing guard | `_category_factories.py:376-392` |
| Run-start rehydration | `run()` loads prior, injects system prompt, persists user prompt | `loop.py:1935-1961` (helper `_persist_to_ledger` 1920-1933) |
| Tool DB-write precedent | dual-arity `(ToolCall, ExecutionContext)` + forgery detect + DB write | `tools/memory_tools.py:270-323` (forgery 81-120) · ctx `_contracts/tools.py:102-126` |
| Auto-pass risk | `risk=LOW`+`destructive=False` → auto-approve under any tenant policy | `_contracts/hitl.py:163-190` (decide_tool_hitl) |
| Wire pipeline | 6-file; CURRENT count **25** (loop_terminated newest, 57.130) | events.py:60-479 · sse.py:135-503 · event_wire_schema.py:88-237 · codegen 87-113 · generated TS · chatStore.ts:425+ |
| Prompt-inject seam | per-request `## Active Skill` append (57.115) | `handler.py:504-512` |
| Inspector tabs | 4 tabs (Turn/Trace/Memory/Tree) | `chat_v2/components/inspector/ChatInspector.tsx:67-72` |

→ The fix must add a durable, structured todo store that survives clean-end multi-send (mirror `DBMessageStore`), a tool to write it, a run-start re-injection so the agent re-focuses, and a wire event + panel so it is visible — then PROVE the agent maintains it via drive-through.

### The design (full-stack vertical slice: tool + store + prompt + wire + panel)

```
Cat 2  write_todos tool (NEW todo_tools.py)  ──writes──▶  Cat 3/7 DBTodoStore (NEW, session_todos table 0031)
                                                                    │
Cat 5  handler.py run-start: load todos ──inject──▶ "## Active Plan" in system prompt   (per-request, no loop.py)
                                                                    │
Cat 1  loop.py (ONE edit): after write_todos exec ──re-read store──▶ yield TodosUpdated(todos)
                                                                    │
Cat 12 todos_updated wire event (6-file, 25→26) ──SSE──▶ chatStore mergeEvent ──▶ chat-v2 Inspector "Todos" tab
```

Replace-whole-list semantics (same as CC TodoWrite — every call rewrites the full list). `risk=LOW`+`destructive=False` so the agent calls it freely in-loop with no HITL prompt.

### Ground truth (recon head-start — code read on `main` HEAD `313a3e31`; ALL re-verified §checklist 0.1)

- `state_mgmt/_abc.py:64-89` — `MessageStore` ABC (`load()` / `append()`) — the shape `TodoStore` mirrors.
- `state_mgmt/message_store.py:74-150` — `DBMessageStore` bound to `(session_id, tenant_id)`, serde via `_contracts/message_serde.py`, best-effort `begin_nested()` SAVEPOINT.
- `_category_factories.py:376-392` — `make_chat_message_store` all-three-or-nothing guard (None → single-turn degrade).
- `loop.py:1935-1961` run-start; `loop.py:3075-3082` `ToolCallExecuted` emit seam (the symmetric point for `TodosUpdated`).
- `tools/memory_tools.py:270-323` — dual-arity DB-write handler + `_detect_forged_scope_args` 81-120.
- `_contracts/hitl.py:82-89` DEFAULT policy (`auto_approve_max_risk=LOW`); `163-190` `decide_tool_hitl`.
- `event_wire_schema.py:88-237` WIRE_SCHEMA (25 entries); count tests `test_event_wire_schema_parity.py:146` + `test_loop_start_active_skill.py:51`.
- migration head = `0030_tenant_skills`; messages RLS in `0009_rls_policies.py`; ORM `models/sessions.py:163-218` (no physical-name aliases).

**Baselines (57.139 closeout)**: pytest 2825+5skip · wire 25 · Vitest 915 · mockup 51 · mypy 0/376 · run_all 10/10. Re-verify Day-0.

### STALE / drift findings (Day-0; full detail → progress.md — placeholder, filled in §checklist 0.1)

- **D-wire-count** — re-grep `len(WIRE_SCHEMA)` + the 2 count tests; confirm CURRENT == 25 before bumping to 26.
- **D-migration-head** — confirm `0031` free + the `down_revision` chain head is `0030_tenant_skills`.
- **D-orm-aliases** — confirm new `SessionTodos` ORM needs no `mapped_column("physical", ...)` (messages model has none; raw SQL in migration uses physical names).
- **D-tool-arity** — confirm `write_todos` must be DUAL-arity (skills tools are single-arity; DB-write needs ExecutionContext per memory_tools).
- **D-loop-emit-seam** — confirm `loop.py:3075-3082` is the live ToolCallExecuted seam + that injecting an optional `todo_store` ctor kwarg mirrors `message_store` (loop otherwise UNTOUCHED for injection).
- **D-handler-per-request** — confirm `build_real_llm_handler` builds the loop per-request with db/session_id/tenant_id in scope (so todos load + inject lives there, not loop.py).

## 1. Sprint Goal

Deliver a working, durable, visible todo-list task primitive on the chat-v2 main flow and **PROVE it is load-bearing** via a mandatory drive-through: a real UI + real backend + real LLM multi-step task across ≥2 sends where the agent (1) proactively calls `write_todos` with ≥3 items, (2) updates item status as it progresses, (3) after a cross-send rehydration still continues from the durable list, and (4) the chat-v2 Todos panel reflects each update with real (non-fixture) labels. Gates: full backend + frontend green. Produces CHANGE-107 + spike design note 44.

## 2. User Stories

- **US-1** (Cat 2 tool): 作為 agent，我希望有一個 `write_todos` 工具能寫下整份結構化 todo list，以便把多步計畫變成可更新的狀態而非自由文字。
- **US-2** (Cat 3/7 storage): 作為平台，我希望 todo list 存進專用 `session_todos` 表並跨多次 send 存活，以便長任務在新 send / compaction 後仍知道「還剩什麼」。
- **US-3** (Cat 5 prompt): 作為 agent，我希望系統提示指示我「多步任務先列 plan、逐步更新」且每次 run 起始把當前 list 注入，以便我會 load-bearingly 維護它而非寫死一次。
- **US-4** (Cat 12 + frontend): 作為使用者，我希望在 chat-v2 看到 todo 面板隨 agent 進度更新（pending/in_progress/completed），以便進度可視、標籤真實。
- **US-5** (drive-through, MANDATORY): 作為驗收者，我希望真 UI + 真後端 + 真 LLM 跑一個跨 send 多步任務，觀察 agent 主動列出 + 逐步更新 + 跨 send 接續 + 面板同步，以便證明 load-bearing（非 AP-4 死控件）。
- **US-6** (closeout): CHANGE-107 + design note 44 + retrospective + navigators + AD closed.

## 3. Technical Specifications

### 3.0 Architecture (full-stack: Cat 2 + Cat 3/7 + Cat 5 + Cat 1 + Cat 12 + frontend; +1 migration; loop.py ONE bounded edit)

```
NEW   agent_harness/_contracts/todo.py           — Todo dataclass (id/title/status) + serde (_todo_to_dict/_from_dict)
NEW   agent_harness/state_mgmt/todo_store.py      — DBTodoStore(TodoStore): load()/replace() bound to (session_id,tenant_id)
EDIT  agent_harness/state_mgmt/_abc.py            — TodoStore ABC (mirrors MessageStore)
NEW   agent_harness/tools/todo_tools.py           — WRITE_TODOS_SPEC + make_write_todos_handler (dual-arity, forgery-detect, writes store)
EDIT  agent_harness/tools/__init__.py             — export WRITE_TODOS_SPEC + make_write_todos_handler + register in register_builtin_tools
NEW   infrastructure/db/migrations/versions/0031_session_todos.py — table + RLS (down_revision 0030_tenant_skills)
EDIT  infrastructure/db/models/sessions.py        — SessionTodos ORM (TenantScopedMixin; no partitioning)
EDIT  api/v1/chat/_category_factories.py          — make_chat_todo_store (all-three-or-nothing guard)
EDIT  api/v1/chat/handler.py                       — system-prompt nudge + run-start load todos + "## Active Plan" inject + pass todo_store to loop
EDIT  agent_harness/orchestrator_loop/loop.py     — optional todo_store ctor kwarg + emit TodosUpdated after successful write_todos exec
EDIT  agent_harness/_contracts/events.py           — TodosUpdated(LoopEvent) {todos: list[Todo]}
EDIT  api/v1/chat/sse.py                            — serializer branch → {"type":"todos_updated","data":{"todos":[...]}}
EDIT  api/v1/chat/event_wire_schema.py             — WIRE_SCHEMA 25→26 (todos_updated)
EDIT  scripts/codegen/generate_event_schemas.py    — WIRE_TYPE_TO_INTERFACE += todos_updated
REGEN frontend/src/features/chat_v2/generated/loopEvents.generated.ts — regen (DO NOT hand-edit)
EDIT  frontend/src/features/chat_v2/store/chatStore.ts — mergeEvent case "todos_updated" (capture todos)
EDIT  frontend/src/features/chat_v2/components/inspector/ChatInspector.tsx — 5th tab "Todos"
NEW   frontend/src/features/chat_v2/components/inspector/InspectorTodos.tsx — panel (status badges, real labels)
EDIT  frontend/src/features/chat_v2/.../types.ts   — Todo type (if not auto-from-generated)
NEW   backend/tests/unit/agent_harness/tools/test_todo_tools.py        — tool: writes / replace-whole-list / forgery-reject / auto-pass risk
NEW   backend/tests/unit/agent_harness/state_mgmt/test_todo_store.py   — store: load empty / replace / cross-bind isolation / tenant scope
EDIT  backend/tests/unit/api/v1/chat/test_event_wire_schema_parity.py  — count 25→26
EDIT  backend/tests/unit/api/v1/chat/test_loop_start_active_skill.py   — count 25→26
NEW   frontend Vitest for InspectorTodos                                — renders list + status badges + empty state
```

### 3.1 `write_todos` tool (US-1) — `tools/todo_tools.py`

- `WRITE_TODOS_SPEC`: name `write_todos`, neutral JSON-schema input `{todos: [{id: str, title: str, status: enum[pending,in_progress,completed]}]}` (whole list), `ToolAnnotations(read_only=False, destructive=False, idempotent=True)`, `risk_level=RiskLevel.LOW`, `hitl_policy=AUTO`, tags `("builtin","planning")`.
- `make_write_todos_handler(todo_store_factory or store)`: dual-arity `(call, context) -> str`; `_detect_forged_scope_args` (mirror memory_tools); validate/normalize the list; `await store.replace(todos)`; return a short confirmation string (e.g. `"Updated plan: 3 todos (1 completed, 1 in_progress, 1 pending)"`).
- Replace-whole-list (no per-item patch) — matches CC TodoWrite + keeps the store a single upsert.

### 3.2 `session_todos` store (US-2) — `state_mgmt/todo_store.py` + `_abc.py` + migration + ORM

- `TodoStore` ABC in `_abc.py`: `async load() -> list[Todo]` / `async replace(todos: list[Todo]) -> None`.
- `DBTodoStore` bound to `(session_id, tenant_id)`; `replace` = upsert single row (`ON CONFLICT (session_id) DO UPDATE`); best-effort `begin_nested()` SAVEPOINT (mirror DBMessageStore); serde via `_contracts/todo.py`.
- `0031_session_todos.py`: `session_todos(id PK, tenant_id NOT NULL FK, session_id NOT NULL UNIQUE FK, todos JSONB NOT NULL, updated_at)` — 1 row/session, NO partitioning (low volume); RLS `ENABLE`+`FORCE` + `tenant_isolation_session_todos` + `tenant_insert_session_todos` (mirror 0009 messages policies). Raw SQL uses physical column names.
- `SessionTodos(Base, TenantScopedMixin)` ORM in `models/sessions.py`.
- `make_chat_todo_store(db, session_id, tenant_id)` all-three-or-nothing guard (None → primitive degrades to in-session only, agent still works).

### 3.3 Prompt nudge + run-start inject (US-3) — `handler.py`

- Append to DEMO_SYSTEM_PROMPT a short nudge: "For any multi-step task, FIRST call `write_todos` to lay out a plan (≥3 items), then update each item's status as you complete it. Re-consult the plan after each step." (the load-bearing instruction).
- In `build_real_llm_handler` (per-request, where `## Active Skill` is appended 504-512): if a todo store is available, `todos = await todo_store.load()`; if non-empty, append `## Active Plan` section listing items + status → the run-start re-focus anchor (the cross-send increment vs free-text).

### 3.4 Loop emit (US-4 backend half) — `loop.py` (ONE bounded edit)

- Optional `todo_store: TodoStore | None = None` ctor kwarg (mirror `message_store`).
- After a successful tool exec where `tc.name == "write_todos"` (symmetric to the `ToolCallExecuted` seam 3075-3082): `todos = await self._todo_store.load(); yield TodosUpdated(todos=todos, trace_context=ctx)`. No other loop change.

### 3.5 Wire event + panel (US-4 frontend half) — Cat 12 6-file + Inspector

- `TodosUpdated(LoopEvent)` {todos}; sse.py branch `todos_updated`; WIRE_SCHEMA 25→26; codegen map += ; regen TS; chatStore mergeEvent `case "todos_updated"` capturing the list into store state.
- `ChatInspector.tsx` 5th tab `{ id: "todos", label: "Todos" }`; `InspectorTodos.tsx` renders the list with status badges (`.badge` pending/in_progress/completed) + empty state — real labels from the captured event, NOT fixture.

### 3.x What is explicitly NOT done

- ❌ NO `max_turns` change (stays 8) — eval §7.
- ❌ NO cross-burst auto-continue scheduler ("one send runs to completion") — separate gap, eval §8.
- ❌ NO task dependency graph / DAG / auto-scheduling — linear list + status only (despite the candidate's "DAG" label, the eval recommends the linear primitive first to measure load-bearing).
- ❌ NO human `/chat/{id}/update-plan` endpoint — eval §3.2 "optional", out of the minimal slice.
- ❌ NO per-tenant todo config / quotas.

### 3.y Validation (US-1..US-6)

Gates: mypy `src` 376+ (0) · run_all 10/10 · pytest 2825+ (+new) · Vitest 915+ (+new) · mockup 51 (`diff` empty, backend+inspector-only — no mockup CSS touched) · `npm run lint && npm run build` (NO `--silent`) · black/isort/flake8 clean · LLM-SDK-leak clean. Plus the §3.x / US-5 drive-through (MANDATORY — the load-bearing gate).

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 1 | `agent_harness/_contracts/todo.py` | NEW |
| 2 | `agent_harness/state_mgmt/todo_store.py` | NEW |
| 3 | `agent_harness/state_mgmt/_abc.py` | EDIT (TodoStore ABC) |
| 4 | `agent_harness/tools/todo_tools.py` | NEW |
| 5 | `agent_harness/tools/__init__.py` | EDIT (export + register) |
| 6 | `infrastructure/db/migrations/versions/0031_session_todos.py` | NEW |
| 7 | `infrastructure/db/models/sessions.py` | EDIT (SessionTodos ORM) |
| 8 | `api/v1/chat/_category_factories.py` | EDIT (make_chat_todo_store) |
| 9 | `api/v1/chat/handler.py` | EDIT (prompt nudge + run-start inject + pass store) |
| 10 | `agent_harness/orchestrator_loop/loop.py` | EDIT (todo_store kwarg + emit TodosUpdated) |
| 11 | `agent_harness/_contracts/events.py` | EDIT (TodosUpdated) |
| 12 | `api/v1/chat/sse.py` | EDIT (serializer) |
| 13 | `api/v1/chat/event_wire_schema.py` | EDIT (25→26) |
| 14 | `scripts/codegen/generate_event_schemas.py` | EDIT (map) |
| 15 | `frontend/.../generated/loopEvents.generated.ts` | REGEN |
| 16 | `frontend/.../store/chatStore.ts` | EDIT (mergeEvent case) |
| 17 | `frontend/.../inspector/ChatInspector.tsx` | EDIT (5th tab) |
| 18 | `frontend/.../inspector/InspectorTodos.tsx` | NEW |
| 19 | `frontend/.../chat_v2 types.ts` | EDIT (Todo type, if needed) |
| 20 | `tests/unit/agent_harness/tools/test_todo_tools.py` | NEW |
| 21 | `tests/unit/agent_harness/state_mgmt/test_todo_store.py` | NEW |
| 22 | `tests/unit/api/v1/chat/test_event_wire_schema_parity.py` | EDIT (count) |
| 23 | `tests/unit/api/v1/chat/test_loop_start_active_skill.py` | EDIT (count) |
| 24 | `frontend Vitest InspectorTodos` | NEW |
| — | `agent_harness/orchestrator_loop/loop.py` injection path | **UNTOUCHED** (injection in handler.py, NOT loop) |
| — | mockup `styles-mockup.css` | **UNTOUCHED** (Inspector uses existing classes) |

## 5. Acceptance Criteria

1. `write_todos` tool registered, dual-arity, `risk=LOW`+`destructive=False` → auto-passes (no HITL) under DEFAULT policy; forged scope args rejected; replace-whole-list writes the `session_todos` row.
2. `DBTodoStore` survives cross-send: `load()` after a fresh store bound to the same `(session_id, tenant_id)` returns the prior list; cross-tenant / cross-session bind returns empty (isolation).
3. Run-start: a non-empty stored list is injected as `## Active Plan` into the system prompt; the nudge instructs plan-first + status updates.
4. `todos_updated` wire event flows backend→frontend; WIRE_SCHEMA == 26; both count tests updated; codegen regenerates the TS interface; chat-v2 Inspector "Todos" tab renders the list with real status badges.
5. **Drive-through PASS (MANDATORY, real UI + backend + LLM)** — a multi-step task across ≥2 sends: agent proactively `write_todos` (≥3 items), updates `pending→in_progress→completed`, after cross-send rehydration continues from the durable list, Todos panel reflects each update (real labels); screenshot + observed-vs-intended in progress.md. (NOT gate-only.) If the agent does NOT reliably update / consult → honest finding: load-bearing UNPROVEN, evaluation downgraded (stronger prompt engineering or defer), recorded — NOT papered over.
6. Research #1 CLOSED (tracked under the eval); CHANGE-107; design note 44 (8-point gate); calibration recorded (`task-primitive-spike` 0.60); navigators + next-phase-candidates updated.

## 6. Deliverables

- [ ] US-1 `write_todos` tool (spec + dual-arity handler + register)
- [ ] US-2 `session_todos` store (Todo contract + TodoStore ABC + DBTodoStore + migration 0031 + ORM + factory)
- [ ] US-3 prompt nudge + run-start `## Active Plan` injection
- [ ] US-4 `todos_updated` wire event (6-file) + loop emit + chat-v2 Todos panel
- [ ] US-5 drive-through (load-bearing gate) — screenshot + observed-vs-intended
- [ ] US-6 CHANGE-107 + design note 44 + closeout

## 7. Workload Calibration

- Scope class **`task-primitive-spike` 0.60** (NEW class, 1st data point). Anchors to `skills-system-spike` (57.113, 0.60) — same greenfield-module + builtin-tool + main-flow-wiring shape — but at the UPPER edge: this slice ALSO has a migration (57.114-like) AND a new wire event (6-file, 57.101/130-like) AND a chat-v2 panel, which 57.113 lacked. The 0.60 reflects the well-trodden pipelines (store mirrors DBMessageStore, tool mirrors memory_tools, wire mirrors loop_terminated, panel mirrors Inspector tabs) — every piece has a recent precedent. Flag at Day-4 retro: if ratio > 1.20, re-point toward 0.70 (full-stack spike with migration+wire is heavier than the pure-module skills spike).
- **Agent-delegated: no** (parent-direct, agent_factor 1.0 → 3-segment form). Consistent with the recent spike cadence (57.136-139 all parent-direct); the load-bearing parts (prompt nudge wording, store semantics, the drive-through judgment) need parent judgment, and parent-direct keeps the new class's 1st calibration point clean.
- Bottom-up est ~16 hr (tool ~2 · store+migration+ORM+factory ~4 · prompt+inject ~1.5 · wire 6-file+loop emit ~3 · FE panel+tab ~2.5 · tests ~2 · drive-through+closeout ~1) → class-calibrated commit ~9.6 hr (mult 0.60). Day-4 retro Q2 verifies.

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| **AP-4 Potemkin — agent ignores the list (THE core risk, eval §6)** | The drive-through (US-5) is designed to falsify/confirm exactly this; if unreliable → honest downgrade, NOT a "verified" claim. Strengthen via system-prompt nudge + run-start re-injection. |
| **AP-6 free-text plan + tool list coexist (eval §5 MEDIUM)** | Nudge phrasing requires the agent to USE the tool AS the plan, not keep a prose plan alongside. |
| Naming collision with Cat 11 `task_spawn` | All names avoid `task` (`write_todos`/`TodoStore`/`session_todos`/`Todo`/`todos_updated`). |
| Wire-count drift (24/25/26 hardcoded in tests + codegen map) | Day-0 D-wire-count re-grep; update BOTH count tests + the codegen `WIRE_TYPE_TO_INTERFACE` map in the same commit (Sprint 57.130 lesson). |
| Migration head occupied / down_revision chain | Day-0 D-migration-head: confirm 0031 free + chain to 0030_tenant_skills. |
| **Risk Class C** — module-level singleton / DB-call test isolation (new store + new tool add DB calls) | autouse session fixture / reset; ensure `get_db_session` override covers new endpoints (Sprint 57.68 lesson). |
| **Risk Class E** — stale `--reload` / orphan spawn-worker masks store wiring at drive-through | Clean restart + `Get-CimInstance Win32_Process` PID/PPID/StartTime sweep before drive-through; kill python only, NOT node :3007 (57.97 lesson). |
| ORM physical-name alias in raw migration SQL | Day-0 D-orm-aliases: messages model has none; new SessionTodos uses direct column names. |
| Drive-through trigger non-determinism (real-LLM may not always plan) | Use an explicitly multi-step prompt that strongly invites planning; if the agent plans but doesn't UPDATE, that's the honest load-bearing finding (record it). |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- Cross-burst auto-continue scheduler ("one send runs the whole task to completion") — research #3 / eval §8; the durable spine here is its prerequisite, not the same thing.
- `max_turns` relaxation — eval §8 #2 (independent governance/cost evaluation).
- Task dependency graph / DAG / auto-scheduling — the candidate's eventual "DAG" aspiration; this spike ships the linear primitive first (eval §7).
- Human `/chat/{id}/update-plan` endpoint (mid-run plan edit by a person) — eval §3.2 optional extension.
- Per-tenant todo config / quotas / retention — Phase 58 if demanded (AP-6 speculative now).
