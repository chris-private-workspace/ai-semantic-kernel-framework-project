# Sprint 57.140 Retrospective — explicit todo-list task primitive

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-140-plan.md) · [Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-140-checklist.md) · [Progress](./progress.md)

Closes research #1 `Explicit task primitive` (eval `task-primitive-thin-spike-eval-20260618.md`). 1st of the canonical net-new block after #6/#3/#8/#4.

---

## Q1: What was delivered?

A full vertical slice of an explicit, structured, durable task primitive (CC `TodoWrite`-like) for the chat agent loop:
- **Cat 2**: `write_todos` tool (replace-whole-list, auto-pass risk=LOW).
- **Cat 3/7**: `session_todos` table (migration 0031) + `DBTodoStore` + `Todo` contract.
- **Cat 5**: DEMO_SYSTEM_PROMPT plan-first nudge.
- **Cat 1**: run-start `## Active Plan` re-injection (loop, async) + `TodosUpdated` emit after write_todos.
- **Cat 12**: `todos_updated` wire event (25→26).
- **Frontend**: chat-v2 Inspector "Todos" tab + store slice.

~28 files. CHANGE-107 + design note 44.

## Q2: Calibration (workload accuracy)

- Scope class **`task-primitive-spike` 0.60** (NEW, 1st data point). Anchored to `skills-system-spike` (57.113, 0.60) — same greenfield-module + builtin-tool + main-flow-wiring shape — but at the upper edge (this slice ALSO has a migration + a new wire event + a panel, which 57.113 lacked).
- **Agent-delegated: no** (parent-direct, agent_factor 1.0 → 3-segment).
- Bottom-up est ~16 hr → class-calibrated commit ~9.6 hr (mult 0.60) → **actual ~9-10 hr** → ratio **~0.95-1.0 IN band**. The 0.60 held: every pipeline had a recent precedent (store↔DBMessageStore, tool↔memory_tools, wire↔loop_terminated, panel↔Inspector tabs), so the bottom-up haircut fit despite the larger surface. KEEP 0.60 pending 2-3 sprint validation; if a 2nd `task-primitive-spike` (e.g. the DAG follow-on) lands > 1.20, re-point toward 0.70.

## Q3: What went well?

- **Day-0 三-prong de-risked the whole sprint** — every layer's precedent was confirmed on current main before code (store/tool/wire/handler line refs), so Day 1-2 was mostly mechanical mirroring. Only 2 path/line drifts (codegen path, loop emit line 2873 vs stale 3075-3082), no scope shift.
- **The drive-through was a clean STRONG PASS** — the agent proactively planned (3 todos), completed them, and on a 2nd send rehydrated the existing list + added a 4th (4/4). The AP-4 "agent ignores the list" risk — the eval's single biggest worry (§6) — was FALSIFIED in one drive-through. gpt-5.2 followed the plan-first nudge without being explicitly told to call the tool.
- **Naming discipline** — avoiding `task` everywhere (`write_todos`/`Todo`/`session_todos`/`todos_updated`) cleanly sidestepped the Cat 11 `task_spawn` collision.
- **Zero CSS / mockup-fidelity stayed byte-identical** — the new Todos tab reused existing mockup `.tab`/`.badge`/`var(--*)`, so the 51 HEX_OKLCH baseline + the styles-mockup.css diff stayed clean.

## Q4: What drifted / what to improve?

- **D-loop-runstart-inject** — the plan put the `## Active Plan` injection in handler.py (Cat 5), but `build_real_llm_handler` is SYNC → the async `todo_store.load()` had to live in `loop.run()`. Lesson: when a plan asserts "injection in the handler", Day-0 should verify the handler is async-capable for the specific load (a Prong-2 check: "is the injection site sync or async?").
- **D-register-all-threading** — the tool registration belongs in `make_default_executor` (the per-request opt-in home, like skills), NOT `register_builtin_tools` as the plan FCL implied. Caught at the cross-category lint (private `_abc` import) + the wiring read. Added `_register_all.py` to scope (~6 lines).
- **D-test-basename-clash** — two `test_todo_store.py` (unit + integration) clashed (no `__init__.py` in test dirs → pytest basename collision). Renamed unit → `test_todo_serde.py`. Lesson: when adding BOTH a unit and an integration test for a new module, give them distinct basenames upfront.
- **3 count-test surfaces** — adding a wire event touched 3 count assertions (parity + active_skill + FE eventSchema), not 2 as the plan assumed (the FE eventSchema mirror was the 3rd). Reinforces the 57.130 lesson (find ALL count-test locations at Day-0).

## Q5: Anti-pattern self-check

- **AP-2** (no side-track) ✅ — the primitive is reachable from the chat 主流量 (handler → executor → loop); the drive-through drove it.
- **AP-3** (no cross-dir scatter) ✅ — Cat 2 in tools/, Cat 7 in state_mgmt/, contract in _contracts/. The cross-category import went through the package export (not private `_abc`).
- **AP-4** (no Potemkin) ✅ — the drive-through FALSIFIED the dead-control risk; the panel renders REAL agent-authored todos, the tool really persists, the run-start inject really re-focuses.
- **AP-6** (no speculative abstraction) ✅ — per-tenant config / DAG / scheduler explicitly deferred (eval §7-8); only the linear primitive shipped.
- **AP-8** (PromptBuilder) ✅ — the static nudge rides DEMO_SYSTEM_PROMPT; the dynamic inject augments the system message at run-start (no naked messages-list assembly).
- **AP-11** (no version suffix) ✅ — no `_v2` / `_old` names.
- v2 lints **10/10**.

## Q6: Carryover (→ next sprint plan §Carryover / next-phase-candidates)

- `AD-TaskPrimitive-DAG-Phase58` — the dependency-graph / DAG evolution of the linear primitive (the candidate's eventual aspiration).
- `AD-TaskPrimitive-Scheduler-Phase58` — cross-burst auto-continue (research #3; the durable spine is its prerequisite — re-evaluate now that #1 is proven).
- `AD-TaskPrimitive-Saturation-DriveThrough-Phase58` — a 5+-send long task with compaction to test status-update reliability at scale (this spike proved 2 sends).
- `AD-ChatV2-Inspector-Todos-TurnBlock-Phase58` — optionally also render the plan inline in the turn timeline (the eval §3.3 alternative not taken).

## Q7: Next

Research #1 CLOSED. Per the canonical ranked order (#6→#3→#8→#4→#1→#2→#5→#7), the next un-done item is **#2 (PassK eval harness)** — or the user may pick #3 (scheduler) now that its task-primitive prerequisite is shipped. NOT pre-written (rolling discipline).

---

## Design Note Extract (spike sprint)

**File**: `docs/03-implementation/agent-harness-planning/44-task-primitive-write-todos-design.md`
**Verified ratio (estimated)**: ≥ 95%
**8-Point Quality Gate**:
- [x] 1. Section header maps to spike user stories (US-1..6)
- [x] 2. Every technical claim has file:line / verification (Verified Invariants §2.1-2.6)
- [x] 3. Decision rationale has a comparison matrix (§1, 7 decisions × rejected alternatives)
- [x] 4. Verification command per invariant (pytest paths + drive-through evidence)
- [x] 5. Test fixture reference (unit/integration test files + drive-through screenshots)
- [x] 6. Open invariants clearly bounded (§4 — verified-this-spike vs deferred)
- [x] 7. Rollback / fallback path (§5 — all-three-or-nothing sentinel + revert steps + est)
- [x] 8. 17.md cross-ref (§3 — N/A justified: TodoStore follows the existing Cat-7 store-family pattern, no new boundary-crossing ABC contract)

**Reviewer pass**: self-review (parent-direct sprint)
