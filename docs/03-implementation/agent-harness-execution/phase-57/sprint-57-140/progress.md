# Sprint 57.140 Progress — explicit todo-list task primitive (write_todos tool + durable store + chat-v2 panel)

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-140-plan.md) · [Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-140-checklist.md)

Closes research #1 `Explicit task primitive` (tracked under `claudedocs/5-status/task-primitive-thin-spike-eval-20260618.md`; no separate AD). 1st of the canonical net-new block after #6/#3/#8/#4.

---

## Day 0 (2026-06-24) — Plan-vs-Repo Verify (三-prong) + Branch

Branch `feature/sprint-57-140-task-primitive-spike` from `main` `313a3e31` (57.139 layered-compaction flip #332 merged).

### Prong 1 — path verify ✅
- 7 NEW files all FREE: `_contracts/todo.py` · `state_mgmt/todo_store.py` · `tools/todo_tools.py` · `migrations/0031_session_todos.py` · `inspector/InspectorTodos.tsx` · `tests/.../tools/test_todo_tools.py` · `tests/.../state_mgmt/test_todo_store.py`.
- All EDIT targets present EXCEPT the codegen path (see D-codegen-path).
- CHANGE max 106 → use **CHANGE-107**. Design-note max 43 → use **44**. Migration head `0030_tenant_skills` → use **0031**.

### Prong 2 — content verify (drift table)

| ID | Finding | Implication |
|----|---------|-------------|
| **D-wire-count** ✅ | `event_wire_schema.py:3,30,81` all say "25"; count tests `test_event_wire_schema_parity.py:146` + `test_loop_start_active_skill.py:51` both `== 25`. | CURRENT == 25 confirmed; bump to **26** + update BOTH count tests + codegen map in same commit. |
| **D-tool-arity** ✅ | `memory_tools.py:278` `async def handler(call: ToolCall, context: ExecutionContext) -> str` + `_detect_forged_scope_args:81`; skills tools are single-arity. | `write_todos` MUST be DUAL-arity (DB write needs ExecutionContext). Mirror memory_write forgery-detect. |
| **D-loop-emit-seam** ✅ (line drift) | `message_store` ctor kwarg `loop.py:331` + `self._message_store:424` + `_persist_to_ledger:1932-1933` + run-start load `:1952`. `yield ToolCallExecuted` is at **`loop.py:2873`** (recon head-start said 3075-3082 — STALE by ~200 lines; the seam exists at 2873). | Mirror `message_store` → add optional `todo_store` ctor kwarg; emit `TodosUpdated` symmetric to the 2873 seam. Plan §3.4 line ref corrected 3075-3082 → **2873**. |
| **D-handler-per-request** ✅ | `build_real_llm_handler:274`; `## Active Skill` deterministic injection `:500-508`; `make_chat_message_store:544`. | todos load + `## Active Plan` inject lives in `handler.py` per-request (near 508/544), NOT loop.py. Confirms plan §3.3 / decision (d). |
| **D-hitl-autopass** ✅ | DEFAULT `auto_approve_max_risk=RiskLevel.LOW` (`hitl.py:86`) + `require_approval_min_risk=MEDIUM` (`:87`). | `risk=LOW`+`destructive=False` auto-passes under DEFAULT (and any) policy → agent calls `write_todos` freely in-loop, no HITL prompt. |
| **D-codegen-path** ⚠️ (path drift) | codegen lives at repo-root **`scripts/codegen/generate_event_schemas.py`**, NOT `backend/scripts/codegen/...`. | Plan §3.0 / FCL #14 wrote `scripts/codegen/...` (correct); checklist Prong 1 listed `backend/scripts/...` (wrong). Use repo-root `scripts/codegen/`. No scope change. |

### Prong 3 — schema verify ✅
- Migration `0031` free; `0030_tenant_skills` `revision="0030_tenant_skills"` + `down_revision="0029_user_mfa_totp"` → 0030 is head → 0031 `down_revision="0030_tenant_skills"`.
- RLS in `0009_rls_policies.py` applies `ENABLE`+`FORCE`+per-table policies via a **table-list loop** that ALREADY RAN → `session_todos` (created in 0031) must self-contain its own `ENABLE`+`FORCE ROW LEVEL SECURITY` + `tenant_isolation_session_todos` + `tenant_insert_session_todos` policies INSIDE 0031 (mirror the 0009 pattern; cannot retro-add to 0009).
- `models/sessions.py` Message ORM has NO `mapped_column("physical",...)` aliases → `SessionTodos` uses direct column names; raw SQL in 0031 uses physical names directly (no alias hazard).

### D-baselines (re-verify at Day-1 partial gate)
Recorded from 57.139 closeout: pytest 2825+5skip · wire 25 · Vitest 915 · mockup 51 · mypy 0/376 · run_all 10/10.

### Go/no-go ✅ PROCEED
All 3 prongs GREEN. 2 drifts are path/line corrections only (D-codegen-path: repo-root scripts/; D-loop-emit-seam: 2873 not 3075-3082) — neither shifts scope. Scope-shift < 20% → PROCEED to Day 1. Every pipeline has a recent precedent (store↔DBMessageStore, tool↔memory_tools, wire↔loop_terminated, panel↔Inspector tabs).

---

## Day 1 (2026-06-24) — Cat 2 tool + Cat 3/7 durable store (US-1, US-2)

**Shipped (9 src/contract + 3 tests)**:
- `_contracts/todo.py` (NEW) — `Todo` frozen dataclass (id/title/status `Literal`) + JSONB-safe serde (tolerant: malformed dropped, unknown status → "pending") + `summarize_todos`. Mirrors `message_serde.py`.
- `state_mgmt/_abc.py` (EDIT) — `TodoStore` ABC (`load()` / `replace()`), mirrors `MessageStore`.
- `state_mgmt/todo_store.py` (NEW) — `DBTodoStore` bound to (session_id, tenant_id); `replace` = `pg_insert(...).on_conflict_do_update(constraint="uq_session_todos_session")` (replace-whole-list upsert); best-effort `begin_nested()` SAVEPOINT.
- `state_mgmt/__init__.py` (EDIT) — re-export `TodoStore` + `DBTodoStore`.
- `infrastructure/db/models/sessions.py` (EDIT) — `SessionTodos(Base, TenantScopedMixin)`: id PK / session_id FK UNIQUE / todos JSONB; NOT partitioned (1 row/session); `uq_session_todos_session` (upsert target) + `idx_session_todos_tenant_session`.
- `infrastructure/db/migrations/versions/0031_session_todos.py` (NEW) — table + 2-policy RLS, mirrors 0030_tenant_skills; `down_revision="0030_tenant_skills"`.
- `tools/todo_tools.py` (NEW) — `WRITE_TODOS_SPEC` (risk=LOW + destructive=False → auto-pass; `additionalProperties:False` → forged scope args schema-invalid) + `make_write_todos_handler(store)` (dual-arity, replace-whole-list, count confirmation).
- `tools/__init__.py` (EDIT) — export the spec + handler factory.
- `business_domain/_register_all.py` (EDIT) — **D-register-all-threading** (drift below): `make_default_executor` `todo_store` kwarg + opt-in block (mirrors skills 341-345).
- `api/v1/chat/_category_factories.py` (EDIT) — `make_chat_todo_store(db, session_id, tenant_id)` all-three-or-nothing guard.
- Tests: unit `test_todo_store.py` (7 serde+factory) + unit `test_todo_tools.py` (5 handler) + integration `test_todo_store.py` (5 DB round-trip/overwrite/isolation/empty; mirrors test_message_store.py, needs PG + 0031).

**Day-1 drift (→ §Risks)**:
- **D-register-all-threading** — tool registers in `make_default_executor` (`_register_all.py`) as a `todo_store` opt-in (mirrors skills 341-345), NOT `register_builtin_tools` as plan FCL #5 implied. `_register_all.py` ADDED to scope (~6-line threading + import + MHist). <20% shift; store bound per-request, threaded by handler.py (Day 2).
- **D-cross-category-import** — first `todo_tools.py` imported `state_mgmt._abc` → `check_cross_category_import` FAIL (private cross-category). FIX: import `TodoStore` from the package `agent_harness.state_mgmt` (re-exported), mirroring `memory_tools` → `agent_harness.memory`. No cycle.
- **D-test-isolation (pre-existing, NOT my regression)** — `test_audit_log_observer.py` (2 tests) FAIL in isolation (`router.py:626 int() ... not coroutine`); CONFIRMED identical fail on clean main (git-stash verify) → Risk Class C test-ordering flake (passes in full 2825 suite). Verify at Day-2 full gate.

**Partial gate**: mypy `src` **0/380** (+4 files) · v2 lints **10/10** (incl. check_llm_sdk_leak — neutrality preserved) · black/isort/flake8 clean · **new unit tests 12 pass**. Integration test (DBTodoStore) deferred to CI/PG + Day-3 drive-through DB.

---

## Day 2 (2026-06-24) — Cat 5 prompt + Cat 12 wire event + loop emit + chat-v2 panel (US-3, US-4)

**Shipped (backend wire + prompt + loop + frontend panel)**:
- **Cat 5 prompt** (`handler.py`): DEMO_SYSTEM_PROMPT plan-first nudge (multi-step → `write_todos` ≥3 + status updates, single source of truth) + build `todo_store` once + pass to `make_default_executor(todo_store=)` + `AgentLoopImpl(todo_store=)`.
- **Cat 1 run-start inject** (`loop.py` — **D-loop-runstart-inject** drift below): build_real_llm_handler is SYNC → the dynamic `## Active Plan` re-injection moved to `loop.run()` (async): load todos, if non-empty append `render_active_plan(todos)` to the system message content. New `render_active_plan` helper in `_contracts/todo.py`.
- **Cat 1 loop emit** (`loop.py`): optional `todo_store` ctor kwarg + after a successful `write_todos` tool call (symmetric to the `ToolCallExecuted` seam at loop.py:3076) `yield TodosUpdated(todos=tuple(await todo_store.load()))`. `loop.py` 2 bounded edits (inject + emit); injection NOT in handler (sync).
- **Cat 12 wire event** (`TodosUpdated` 6-file): `events.py` `TodosUpdated(LoopEvent){todos: tuple[Todo,...]}` + `_contracts/__init__` re-export + `sse.py` serializer (`todos_updated` → `todos_to_jsonb`) + `event_wire_schema.py` WIRE_SCHEMA **25→26** (`todos: Record<string, unknown>[]`, added to recognized types) + codegen `WIRE_TYPE_TO_INTERFACE += todos_updated` + regen `loopEvents.generated.ts` (`TodosUpdatedEvent`) + 3 count tests (parity 25→26 + active_skill 25→26 + FE eventSchema 25→26 + new recognition tests).
- **Frontend panel**: `chatStore.ts` `TodoItem` type + `todos` state slice (3 init/reset + Pick) + `narrowTodoStatus` helper + `mergeEvent` `todos_updated` case (narrow `Record<string,unknown>[]` → `TodoItem[]`, replace-whole-list) + `ChatInspector.tsx` 5th "Todos" tab + NEW `InspectorTodos.tsx` (status `.badge` success/info/base + completed count + honest empty state, mirrors InspectorMemory) + Vitest (4).

**Day-2 drift (→ §Risks)**:
- **D-loop-runstart-inject** — plan §3.3/decision(d) said the `## Active Plan` injection lives in handler.py (Cat 5). But `build_real_llm_handler` is a SYNC `def` (returns AgentLoopImpl) → cannot `await todo_store.load()`. The DYNAMIC re-injection MUST be in `loop.run()` (async, per-send freshness). STATIC nudge stays in DEMO_SYSTEM_PROMPT (Cat 5, sync). loop.py becomes 2 edits (emit + inject) vs plan's "ONE". Bounded; no scope shift.
- **D-mockup-5th-tab** — the reference mockup (page-chat.jsx) has NO todos surface (predates the feature). Added a NEW 5th Inspector "Todos" tab using ONLY existing mockup classes (`.tab`/`.badge`/`var(--*)`) → `styles-mockup.css` UNTOUCHED, mockup-fidelity diff stays empty (51 baseline). Justified new-feature surface (eval §3.3); labeled honestly in InspectorTodos docstring.
- **D-test-basename-clash** — `tests/unit/.../test_todo_store.py` + `tests/integration/.../test_todo_store.py` same basename → pytest "import file mismatch" (no `__init__.py` in test dirs). FIX: renamed unit → `test_todo_serde.py` (accurate — it tests serde + factory, not the DB store).
- **D-test-isolation RESOLVED** — `test_audit_log_observer` PASSED in the full 2841-item suite (confirmed Risk Class C isolation flake, not a regression).

**Full gate**: mypy `src` **0/380** · v2 lints **10/10** (check_event_schema_sync confirms codegen synced) · backend pytest **2843 pass** +5skip (3 integration DBTodoStore failed on first run = test DB lacked 0031 → `alembic upgrade head` applied → 5/5 pass) · `npm run lint` clean (NO --silent) · `npm run build` (tsc) pass (added `todos` to the `_initial` Pick) · Vitest **920 pass** (+5: 4 InspectorTodos + 1 todos_updated recognition) · mockup-fidelity **51 baseline byte-identical**. Migration 0031 applied to local DB.

---

## Day 3 (2026-06-24) — Drive-through (US-5) — chat-v2, real Azure gpt-5.2 — **the load-bearing gate**

Clean restart (Risk Class E): NO python pre-start (`Get-CimInstance Win32_Process` empty), :8000 free, :3007 node (frontend vite dev, PID 31616) UNTOUCHED. Backend started single-process (no --reload) with root `.env` Azure creds → startup complete + all services wired. Frontend HMR served the Day-2 components (the Todos tab was live). dev-login jamie@acme.com·operator·acme-prod.

**The walk (real UI + real backend + real Azure gpt-5.2)**:
- **Before**: clicked the NEW Inspector "Todos" tab → honest empty state "Plan · this session / no plan yet — the agent writes one for multi-step tasks" (NOT a fixture).
- **Send 1** ("plan a 3-step TCP vs UDP outline … first lay out your plan as todos, then work through each step, marking each in_progress then completed"): the agent **PROACTIVELY** called `write_todos` with **3 items**, worked through them across the 8-turn loop, and the Todos panel rendered **3/3 completed** with the agent-authored titles + `completed` `.badge.success` per row (`[data-testid="inspector-todos"]` snapshot confirms: "Define scope and key comparison criteria…", "Draft a 3-step outline…", "Review and refine the outline…"). `tool_call_result write_todos` visible in the event stream; verification passed. Screenshot `dt-57140-progress.jpeg`.
- **Send 2 — cross-send rehydration** ("Add a 4th step … keep the 3 you already finished as completed, add the new one, then do it"): the agent **rehydrated the 3 existing todos** (preserved verbatim with their completed status — proof the durable list survived the send boundary), added the 4th, and the panel updated to **4/4 completed** with the new row "Write a one-sentence summary of the guide." [completed]. This is THE load-bearing proof — the agent continued FROM the durable structured list (replace-whole-list: 3 preserved + 1 new), not a free-text restart. Screenshot `dt-57140-crosssend-4todos.jpeg`.

**Verdict: STRONG PASS** — all 4 §6 drive-through criteria met: (1) proactive `write_todos` ≥3 ✅ (2) status updates pending→in_progress→completed ✅ (3) cross-send rehydration + continuation ✅ (4) panel updates with real labels + correct count ✅. The AP-4 "dead control / agent ignores the list" risk is **falsified** — the agent reliably maintained the structured durable plan across 2 sends. Real-LLM evidence: gpt-5.2 ×N action turns + gpt-5.4-mini cheap-tier verification (57.109 split) + `POST /api/v1/chat/ 200 OK`.

**Note**: a `sessions_pkey` duplicate-key on send 2 is the PRE-EXISTING best-effort `create_session` INSERT race (`router.py:368`, caught, chat unaffected — both sends completed + panels updated) — unrelated to the task primitive (same observation as the 57.139 drive-through).

Artifacts: `artifacts/dt-57140-progress.jpeg` (3/3) + `artifacts/dt-57140-crosssend-4todos.jpeg` (4/4 cross-send).

---
