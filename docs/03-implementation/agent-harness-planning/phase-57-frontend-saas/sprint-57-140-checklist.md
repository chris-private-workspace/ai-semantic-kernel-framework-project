# Sprint 57.140 — Checklist (explicit todo-list task primitive: write_todos tool + durable store + chat-v2 panel)

[Plan](./sprint-57-140-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch

### 0.1 Three-prong Day-0 verify (against `main` HEAD `313a3e31`)
- [x] **Prong 1 — path verify**: ✅ 7 NEW files free; EDIT targets present; codegen at repo-root `scripts/codegen/generate_event_schemas.py` (NOT `backend/scripts/` — D-codegen-path); CHANGE-107 + design note 44 + migration 0031 free
- [x] **Prong 2 — content verify** (drift → progress.md):
  - [x] **D-wire-count** ✅ — CURRENT == 25 (`event_wire_schema.py:3,30,81` + count tests `:146`/`:51`) → bump 26
  - [x] **D-tool-arity** ✅ — `memory_tools.py:278` dual-arity + forgery `:81` → `write_todos` MUST be dual-arity
  - [x] **D-loop-emit-seam** ✅ (line drift) — `message_store` ctor kwarg `loop.py:331` + `yield ToolCallExecuted` at **`loop.py:2873`** (recon 3075-3082 STALE) → mirror for `todo_store`
  - [x] **D-handler-per-request** ✅ — `build_real_llm_handler:274` + `## Active Skill` `:500-508` + `make_chat_message_store:544` → todos load+inject in handler.py
  - [x] **D-hitl-autopass** ✅ — DEFAULT `auto_approve_max_risk=LOW` (`hitl.py:86`) → `risk=LOW`+`destructive=False` auto-passes any policy
- [x] **Prong 3 — schema verify**: ✅ `0031` free + `down_revision="0030_tenant_skills"` (rev id confirmed); 0009 RLS via table-list loop (already ran) → **0031 self-contains** `ENABLE`+`FORCE`+`tenant_isolation_session_todos`+`tenant_insert_session_todos`; Message ORM NO physical aliases → SessionTodos direct names; 1 row/session, NO partitioning
- [x] **D-baselines** — pytest 2825+5skip · wire 25 · Vitest 915 · mockup 51 · mypy 0/376 · run_all 10/10 (re-verify at gate)
- [x] **Catalog drift** — ✅ progress.md Day-0 table (6 D-rows)
- [x] **Go/no-go** — ✅ all 3 prongs GREEN; 2 path/line drifts only (no scope shift); scope-shift < 20% → PROCEED

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-140-task-primitive-spike` (from `main` `313a3e31`)

---

## Day 1 — Cat 2 tool + Cat 3/7 durable store (US-1, US-2)

### 1.1 `Todo` contract + serde (`_contracts/todo.py`)
- [x] **`Todo` dataclass (id/title/status `Literal`) + tolerant serde + summarize_todos** ✅
  - round-trip / drop-malformed / unknown→pending / non-list→[]
  - Verify: `pytest tests/unit/agent_harness/state_mgmt/test_todo_store.py -k serde` → green

### 1.2 `TodoStore` ABC + `DBTodoStore` (`_abc.py` EDIT + `todo_store.py` NEW)
- [x] **ABC `load()`/`replace()` mirrors MessageStore; DBTodoStore upsert single row, best-effort SAVEPOINT** ✅
  - DB tests (round-trip / overwrite-whole-list / cross-tenant + cross-session isolation / load-empty) → **integration** `test_todo_store.py` (mirrors test_message_store.py; needs PG + 0031, CI/Day-3 DB)
  - Verify (DB): `pytest tests/integration/agent_harness/state_mgmt/test_todo_store.py` (CI/PG)

### 1.3 Migration 0031 + SessionTodos ORM (`0031_session_todos.py` NEW + `models/sessions.py` EDIT)
- [x] **`session_todos` table + RLS + ORM** ✅
  - `down_revision="0030_tenant_skills"`; RLS `ENABLE`+`FORCE`+`tenant_isolation_session_todos`+`tenant_insert_session_todos`; NO partitioning; `SessionTodos(Base, TenantScopedMixin)`; physical names
  - Verify: ORM imports clean (mypy 0/380); `alembic upgrade head` at Day-3 DB

### 1.4 `write_todos` tool (`todo_tools.py` NEW + `tools/__init__.py` + `_register_all.py` EDIT)
- [x] **WRITE_TODOS_SPEC (risk=LOW, destructive=False, additionalProperties:False) + dual-arity handler + opt-in register** ✅
  - schema forbids scope fields (forged args schema-invalid); replace-whole-list + count confirmation; registered in `make_default_executor` opt-in (**D-register-all-threading** — mirrors skills, NOT register_builtin_tools)
  - Verify: `pytest tests/unit/agent_harness/tools/test_todo_tools.py` → 5 green

### 1.5 Factory wiring (`_category_factories.py` EDIT)
- [x] **`make_chat_todo_store(db, session_id, tenant_id)` all-three-or-nothing guard** ✅
  - None when any arg None; else `DBTodoStore`
  - Verify: `pytest ...test_todo_store.py::test_factory_none_guard` → green

### 1.x Partial gate
- [x] ✅ mypy `src` **0/380** · black/isort/flake8 clean · run_all **10/10** (incl. check_llm_sdk_leak) · new unit tests **12 pass**. (Pre-existing Risk Class C flake `test_audit_log_observer` confirmed on clean main — verify at Day-2 full gate.)

---

## Day 2 — Cat 5 prompt + Cat 12 wire event + loop emit + chat-v2 panel (US-3, US-4)

### 2.1 Prompt nudge + run-start inject (`handler.py` + `loop.py` EDIT — D-loop-runstart-inject)
- [x] **DEMO_SYSTEM_PROMPT plan-first nudge (Cat 5, sync) + run-start `## Active Plan` inject in `loop.run()` (Cat 1, async) + pass todo_store to executor + loop** ✅
  - **D-loop-runstart-inject**: `build_real_llm_handler` is SYNC → dynamic load must be in async `loop.run()` (not handler); static nudge in DEMO_SYSTEM_PROMPT; new `render_active_plan` helper; empty list → no section
  - Verify: mypy 0/380 + handler/loop imports clean + drive-through Day 3

### 2.2 `TodosUpdated` event + loop emit (`events.py` + `loop.py` EDIT)
- [x] **TodosUpdated(LoopEvent){todos: tuple[Todo,...]} + `_contracts` re-export + optional todo_store ctor kwarg + emit after successful write_todos exec** ✅
  - loop emits `TodosUpdated` after the success `ToolCallExecuted` (loop.py:3076) only when `tc.name=="write_todos"`; re-reads store
  - Verify: parity test covers TodosUpdated instance → green

### 2.3 Wire pipeline 6-file (sse.py + event_wire_schema.py + codegen + regen + chatStore.ts)
- [x] **todos_updated wire type 25→26 + codegen map + regen TS + mergeEvent case** ✅
  - sse.py branch (`todos_to_jsonb`); WIRE_SCHEMA == 26 (`Record<string,unknown>[]`); `WIRE_TYPE_TO_INTERFACE += todos_updated`; regen `loopEvents.generated.ts` (`TodosUpdatedEvent`); chatStore `case "todos_updated"` narrows to TodoItem[]; **3 count tests 25→26** (parity + active_skill + FE eventSchema) + new recognition tests
  - Verify: `pytest test_event_wire_schema_parity.py test_loop_start_active_skill.py` 38 green + check_event_schema_sync 10/10

### 2.4 chat-v2 Todos panel (`ChatInspector.tsx` EDIT + `InspectorTodos.tsx` NEW — D-mockup-5th-tab)
- [x] **5th Inspector tab "Todos" + panel (status badges success/info/base + count + empty state)** ✅
  - **D-mockup-5th-tab**: mockup has no todos surface → NEW tab uses ONLY existing mockup classes (`.tab`/`.badge`/`var(--*)`) → styles-mockup.css UNTOUCHED; reads `chatStore.todos`; NO fixture
  - Verify: `npx vitest run InspectorTodos` 4 green + `npm run build` pass + mockup-fidelity 51 byte-identical

### 2.x Full gate
- [x] ✅ mypy `src` **0/380** · run_all **10/10** · backend pytest **2843 pass** +5skip (0031 applied to local DB; integration 5/5) · Vitest **920 pass** (+5) · `npm run lint && npm run build` clean (NO `--silent`) · mockup **51 byte-identical** · black/isort/flake8 clean · LLM-SDK-leak clean. (D-test-basename-clash: renamed unit → test_todo_serde.py; D-test-isolation: audit_observer passes in full suite.)

---

## Day 3 — Drive-through (US-5) — real UI + real backend + real LLM (THE load-bearing gate)

### 3.1 Clean restart (Risk Class E)
- [x] ✅ NO python pre-start (`Get-CimInstance` empty) · :8000 free · :3007 node (vite dev PID 31616) UNTOUCHED · backend single-process (no --reload) + root .env Azure creds → startup complete; frontend HMR served Day-2 Todos tab

### 3.2 Drive-through (MANDATORY — NOT gate-only) — **STRONG PASS**
- [x] **multi-step task across 2 sends** — ✅ real Azure gpt-5.2 via chat-v2 (jamie@acme.com·operator·acme-prod)
- [x] **THE load-bearing walk (real UI)**:
  - [x] ✅ agent **proactively** called `write_todos` with **3 items** (send 1; `tool_call_result write_todos` in event stream)
  - [x] ✅ status pending→in_progress→completed across the 8-turn loop → panel **3/3 completed**
  - [x] ✅ **cross-send rehydration**: send 2 preserved the 3 completed todos + added a 4th → panel **4/4 completed** (continued FROM the durable list, NOT a free-text restart — THE key increment)
  - [x] ✅ Todos panel real labels (agent-authored titles) + `.badge.success` per status + correct count (non-fixture; `[data-testid="inspector-todos"]` snapshot)
- [x] **Honest verdict**: ✅ STRONG PASS — AP-4 "agent ignores the list" risk FALSIFIED; the agent reliably maintained the structured durable plan across 2 sends
- [x] ✅ Screenshots `dt-57140-progress.jpeg` (3/3) + `dt-57140-crosssend-4todos.jpeg` (4/4) → artifacts/ + progress.md Day 3

---

## Day 4 — CHANGE-107 + design note 44 + closeout

### 4.1 CHANGE-107 + design note (spike)
- [x] ✅ **`CHANGE-107-task-primitive-write-todos.md`** (gap + fix + drive-through STRONG PASS + research #1 closed)
- [x] ✅ **`44-task-primitive-write-todos-design.md`** (8/8 gate; §3 N/A justified — TodoStore follows the Cat-7 store family, no new boundary-crossing ABC contract)

### 4.2 Closeout
- [x] ✅ retrospective.md Q1-Q7 + calibration (`task-primitive-spike` 0.60, 1st data point, ratio ~0.95-1.0 IN band → KEEP)
- [x] ✅ Final gate sweep: mypy **0/380** · run_all **10/10** · pytest **2843** +5skip · Vitest **920** · mockup **51 byte-identical** · build pass · lint clean · LLM-SDK-leak clean
- [x] ✅ Navigators: CLAUDE.md Current-Sprint + Last-Updated · MEMORY.md pointer + subfile (auto-memory) · next-phase-candidates (CLOSED research #1; advance → #2 PassK next) · sprint-workflow matrix (`task-primitive-spike` 0.60 row)
- [x] ✅ Anti-pattern self-check (retro Q5): AP-2/3/4/6/8/11 → no violations; v2 lints 10/10
- [ ] **Commit** → ⏳ PR push + open → CI → merge: **PENDING USER CONFIRMATION** (push is outward-facing per Developer Preferences) → post-merge status flip after gh-verified MERGED
