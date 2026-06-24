---
title: 44-task-primitive-write-todos design note
purpose: Spike-extract design note from Sprint 57.140; documents verified runtime invariants for the explicit todo-list task primitive (write_todos + durable store + chat-v2 panel)
category: V2 extension docs (post-22-sprint era)
created: 2026-06-24 (Sprint 57.140 Day 4 closeout)
sprint_source: 57.140
verified_ratio: ≥ 95% (per 8-Point Quality Gate)
status: Active
---

# 44-task-primitive-write-todos Design Note (Sprint 57.140 extract)

## 0. Spike Summary

- **Sprint scope** (closes research #1 `Explicit task primitive`, tracked under `task-primitive-thin-spike-eval-20260618.md`; Cat 2/3/7/5/1/12 + frontend): US-1 `write_todos` tool · US-2 `session_todos` durable store · US-3 prompt nudge + run-start re-injection · US-4 `todos_updated` wire event + chat-v2 Todos panel · US-5 drive-through · US-6 closeout.
- **Verified period**: 2026-06-24.
- **Calibration**: bottom-up ~16 hr → committed ~9.6 hr (NEW class `task-primitive-spike` 0.60) → actual ~9-10 hr → ratio ~0.95-1.0 IN band (parent-direct, agent_factor 1.0).
- **Verification**: pytest +22 (7 serde + 5 tool + 5 integration + wire parity instance + count tests) · 4 Vitest · real-Azure chat-v2 drive-through (2 sends).
- **The load-bearing thesis (the spike's whole point)**: CC's `TodoWrite` works because the model is trained/prompted to consult + update it. On THIS platform the proof is whether the agent (a) proactively writes a plan and (b) maintains it across multiple 8-turn sends. The drive-through (§2.6) FALSIFIED the AP-4 "agent ignores the list" risk — both confirmed.

## 1. Decision Matrix

| Decision | Option chosen | Alternatives rejected (reason) |
|----------|---------------|-------------------------------|
| Storage | **Dedicated `session_todos` table + `DBTodoStore`** (mirror DBMessageStore) | `DurableState.metadata` (pause-scoped → no clean-end multi-send persist, eval §3.1-A); reuse a memory layer (memory = "facts" semantics, not "current task state" — muddies the spine). User-confirmed eval option C. |
| Tool registration | **`make_default_executor` opt-in** (`todo_store` kwarg, mirrors skills 341-345) | `register_builtin_tools` (that's the always-on 6-tool registrar; per-request store deps belong in make_default_executor — D-register-all-threading) |
| Run-start `## Active Plan` injection | **`loop.run()` (async)** | `handler.py` (plan §3.3 intent) — but `build_real_llm_handler` is a SYNC `def` returning AgentLoopImpl → cannot `await todo_store.load()`; the dynamic per-send load MUST be async (D-loop-runstart-inject) |
| Loop emit of `TodosUpdated` | **Loop re-reads the store after a `write_todos` tool success** (name-coupled) | Tool result protocol carrying the list (richer protocol, scope creep for a spike); SSE-layer synthesis (SSE only serializes events the loop yields — can't synthesize) |
| Wire `todos` type | **`Record<string, unknown>[]`** (FE narrows to a hand-written `TodoItem`) | a 2nd named codegen element type like `LLMToolCall` (codegen emits exactly ONE named element — adding a 2nd is a real codegen change, unjustified for a spike) |
| chat-v2 surface | **NEW 5th Inspector "Todos" tab, existing mockup classes** | the mockup has NO todos surface (predates the feature); a turn-block render (eval §3.3 alternative) — the tab is the cleaner home + reuses `.tab`/`.badge`/`var(--*)` so styles-mockup.css stays byte-identical (D-mockup-5th-tab) |
| Naming | **`write_todos` / `Todo` / `session_todos` / `todos_updated`** | anything with `task` (collides with Cat 11 `task_spawn` subagent dispatch — eval §3.2) |

## 2. Verified Invariants

### 2.1 write_todos persists the whole list, auto-passes HITL
- **Implementation**: `tools/todo_tools.py` — `WRITE_TODOS_SPEC` (`risk_level=LOW`, `annotations.destructive=False`, `additionalProperties:False`) + `make_write_todos_handler(store)` dual-arity handler (replace-whole-list → `store.replace`, count confirmation).
- **Behavior**: `risk=LOW`+`destructive=False` → `decide_tool_hitl` (`hitl.py:163-190`) auto-approves under DEFAULT policy (`auto_approve_max_risk=LOW`) → the agent calls it freely in-loop, no pause.
- **Verification**: `pytest tests/unit/agent_harness/tools/test_todo_tools.py` (5 passed).

### 2.2 DBTodoStore survives cross-send (upsert on session_id)
- **Implementation**: `state_mgmt/todo_store.py` — bound to `(session_id, tenant_id)`; `replace` = `pg_insert(...).on_conflict_do_update(constraint="uq_session_todos_session", ...)` inside `begin_nested()` (best-effort); `load` returns `todos_from_jsonb(row.todos)` or [].
- **Behavior**: 1 row/session, the whole list as JSONB; a fresh store bound to the same `(session_id, tenant_id)` loads the prior list; cross-tenant / cross-session bind → [] (RLS + WHERE scope).
- **Verification**: `pytest tests/integration/agent_harness/state_mgmt/test_todo_store.py` (5 passed, real PG with migration 0031).

### 2.3 Run-start re-injection re-focuses the agent across sends
- **Implementation**: `orchestrator_loop/loop.py` `run()` — after building `messages`, if `self._todo_store` and the loaded list is non-empty, append `render_active_plan(todos)` (`_contracts/todo.py`) to the system message content.
- **Behavior**: every new send re-injects the CURRENT durable list as a `## Active Plan` section → the agent sees "what's left / what's done" after a new send / compaction (the cross-send increment vs a free-text plan). Empty list / absent store → no section (byte-identical baseline).
- **Verification**: drive-through send 2 (§2.6) — the agent rehydrated the 3 existing todos and continued.

### 2.4 Loop emits TodosUpdated after a write_todos success
- **Implementation**: `loop.py` — optional `todo_store` ctor kwarg; after the success `yield ToolCallExecuted` (loop.py:3076), `if tc.name == "write_todos" and self._todo_store is not None: yield TodosUpdated(todos=tuple(await self._todo_store.load()))`.
- **Verification**: `test_event_wire_schema_parity.py` covers a `TodosUpdated` instance → `todos_updated` frame; drive-through panel updated in real time.

### 2.5 Wire pipeline (todos_updated, 25→26)
- **Implementation**: `events.py` `TodosUpdated(LoopEvent){todos: tuple[Todo,...]}` → `sse.py` (`todos_updated` → `todos_to_jsonb`) → `event_wire_schema.py` (WIRE_SCHEMA 26, `Record<string,unknown>[]`) → codegen `WIRE_TYPE_TO_INTERFACE` → `loopEvents.generated.ts` (`TodosUpdatedEvent`) → `chatStore.ts` `mergeEvent` (narrow to `TodoItem[]`).
- **Verification**: `check_event_schema_sync` 10/10 (codegen synced) + 3 count tests 25→26 (parity + active_skill + FE eventSchema) + the FE `todos_updated` recognition test.

### 2.6 Drive-through (chat-v2, real Azure gpt-5.2) — STRONG PASS
- **Behavior**: send 1 ("plan a 3-step TCP vs UDP outline … lay out as todos, then work through marking each") → the agent **proactively** called `write_todos` with **3 items** + worked through them → panel **3/3 completed** (`[data-testid="inspector-todos"]` snapshot: the 3 agent-authored titles + `completed` `.badge.success`). Send 2 ("add a 4th step, keep the 3 finished") → the agent **rehydrated the 3 existing** (preserved verbatim) + added the 4th → panel **4/4 completed**. The agent continued FROM the durable structured list (replace-whole-list), NOT a free-text restart → AP-4 risk FALSIFIED.
- **Verification**: screenshots `sprint-57-140/artifacts/dt-57140-progress.jpeg` (3/3) + `dt-57140-crosssend-4todos.jpeg` (4/4); `tool_call_result write_todos` in the event stream; `POST /api/v1/chat/ 200 OK` + gpt-5.2 ×N + gpt-5.4-mini cheap-tier verify (57.109).

## 3. Cross-Category Contracts

**No new cross-category contract requiring 17.md registration.** `TodoStore` is a NEW Cat-7 ABC (sibling to `MessageStore` 57.127) — internal to Cat 7, consumed by Cat 2 (`write_todos`) + Cat 1 (loop) via the `agent_harness.state_mgmt` package export (NOT a private `_abc` import — D-cross-category-import). `write_todos` is a Cat-2 builtin tool (uses the existing neutral `ToolSpec`/`ExecutionContext`). `TodosUpdated` is a new `LoopEvent` subclass (the existing event-tree pattern; registered in the wire schema, the established 6-file mechanism — not a new ABC). The 17.md §2.1 MessageStore/Compactor/Checkpointer row already documents the Cat-7 store family pattern; `TodoStore` follows it. N/A justified (no new ABC method signature crosses a category boundary as a contract; the tool + event use existing single-source contracts).

## 4. Open Invariants (deferred)

- [ ] **Task dependency graph / DAG** — the candidate's eventual "DAG" aspiration; this spike ships the LINEAR primitive first (eval §7) to measure load-bearing. NOT verified.
- [ ] **Cross-burst auto-continue scheduler** ("one send runs to completion") — research #3 / eval §8; the durable spine here is its prerequisite, not the same thing. NOT in scope.
- [ ] **`max_turns` relaxation** — eval §8 #2 (independent governance/cost evaluation). UNCHANGED at 8.
- [ ] **Human mid-run plan edit** (`/chat/{id}/update-plan`) — eval §3.2 optional extension. NOT built.
- [ ] **Per-tenant todo config / quotas / retention** — Phase 58 if demanded (AP-6 speculative now).
- [ ] **Status-update reliability across MANY sends** — drive-through proved 2 sends; a long task spanning 5+ sends with compaction is plausible but NOT exhaustively driven (the 2-send proof is representative, not a saturation claim).

## 5. Rollback / Fallback

- **If the primitive proves wrong**: the default path is already a no-op for sessions without the store (`make_chat_todo_store` all-three-or-nothing → None → the loop emits no TodosUpdated, no `## Active Plan`). To fully revert: drop the `todo_store` opt-in in `make_default_executor` + the 2 loop.py edits + the `todos_updated` wire entry (+ regen) + the Inspector tab; delete `todo_tools.py` / `todo_store.py` / `_contracts/todo.py` / migration 0031 (downgrade drops the table). Est ~1.5 hr. `loop.py`'s other paths + the other compactors/stores were untouched.
- **Sentinel already in place**: yes — the all-three-or-nothing factory guard + the `if self._todo_store is not None` loop guards mean the primitive only activates when explicitly wired (the production chat path); subagent child loops + legacy/test callers are byte-identical baseline.

## 6. References

- Spike eval (the design source): `claudedocs/5-status/task-primitive-thin-spike-eval-20260618.md`
- Sprint plan: `phase-57-frontend-saas/sprint-57-140-plan.md`
- Sprint retrospective: `agent-harness-execution/phase-57/sprint-57-140/retrospective.md`
- CHANGE: `claudedocs/4-changes/feature-changes/CHANGE-107-task-primitive-write-todos.md`
- Related: `17-cross-category-interfaces.md` §2.1 (Cat-7 store family) · `04-anti-patterns.md` AP-4 (Potemkin — the drive-through guard) / AP-6 · `09-db-schema-design.md` Group 2 (sessions) · predecessor `DBMessageStore` 57.127

## Modification History
- 2026-06-24: Initial extract from Sprint 57.140 closeout (Day 4)
