---
title: 60-scheduler-cross-burst design note
purpose: Spike-extract design note from Sprint 57.157; verified runtime invariants for the chat cross-burst auto-continue scheduler
category: V2 extension docs (post-22-sprint era)
created: 2026-07-06 (Sprint 57.157 Day 4 closeout)
sprint_source: 57.157
verified_ratio: ≥ 95% (per 8-Point Quality Gate)
status: Active
---

# 60-scheduler-cross-burst Design Note (Sprint 57.157 extract)

## 0. Spike Summary

- **Scope (user stories)**: US-1 `should_continue_plan` predicate + router outer-loop auto-continue · US-2 `max_bursts` bound + per-burst caps preserved · US-3 default-OFF settings · US-4 drive-through PASS · US-5 closeout.
- **Gap closed**: `AD-TaskPrimitive-Scheduler-Phase58` — a `write_todos` plan (57.140) that needs >8 turns stalled at the per-send `max_turns=8` ceiling and forced the user to type "continue". The scheduler bridges bursts within one SSE stream.
- **Verified period**: 2026-07-06 (Day 0 三-prong → Day 3 drive-through).
- **Calibration**: NEW class `scheduler-cross-burst-spike` 0.60; parent-direct (`agent_factor` 1.0, 3-segment); bottom-up ~6 hr → committed ~3.6 hr; actual ~1.15-1.3 near/slightly-over band top (drive-through env-resolution detective work — first-session DB/env discovery — was the variance driver, not the code or a re-drive). KEEP 0.60 single-data-point; if a 2nd `scheduler-*-spike` lands >1.20, re-point 0.70 (pre-registered plan §7).
- **Verification**: pytest +18 (12 predicate + 6 router); 850 regression byte-identical when OFF; real-Azure drive-through both legs.
- **Design principle**: **guidance not enforcement** — the scheduler continues a plan the agent left unfinished; it never blocks the agent, and stops on any non-`max_turns` terminal (mirrors the 57.140/57.156 nudge-not-force pattern).

## 1. Decision Matrix — where does the outer-loop live?

| Approach | Continuation stays on the open SSE stream? | Orphan risk | Per-burst closeout control | Decision |
|----------|-------------------------------------------|-------------|----------------------------|----------|
| **Inline outer-`while` in the SSE generator** (chosen) | ✅ yes — same `_stream_loop_events` connection | none | full (guards in the existing body) | ✅ **chosen** |
| Background job (`main.py`-style poller re-driving the session) | ❌ no — a new task, disconnected from the client stream | high (Risk Class E spawn-worker orphan; 57.97 precedent) | must re-plumb closeout | ❌ rejected — orphans the open stream |
| `loop.py`-level max_turns bump / unbounded run | n/a | n/a | breaks the `max_turns=8` governance ceiling | ❌ rejected — violates bounded-burst server-side design |

**Chosen reason**: the SSE connection is already open streaming this session's events; keeping continuation on the same stream means the client renders one continuous terminal frame (no reconnect, no new wire event). **Rejected-background reason**: a poller would run detached from the request's DB session + trace context and orphan on client disconnect. **Rejected-loop-bump reason**: `max_turns=8` (`handler.py:771`) is an intentional per-burst governance boundary — the fix is to chain bounded bursts, not to remove the bound.

## 2. Verified Invariants

### 2.1 Continue-predicate is a pure 4-condition AND (US-1)
- **Implementation**: `should_continue_plan(*, enabled, stop_reason, todos, bursts_used, max_bursts)` at `backend/src/agent_harness/orchestrator_loop/scheduler.py` — returns `enabled and stop_reason == TerminationReason.MAX_TURNS.value and bursts_used < max_bursts and any(t.status != "completed" for t in todos)`.
- **Behavior**: only a `max_turns` burst with an unfinished plan and remaining budget continues. `end_turn` / `token_budget` / `handoff` / `awaiting_approval`, an all-`completed` plan, an empty plan (agent never called `write_todos`), and a reached `max_bursts` all return False. Pure — no I/O.
- **Verification**: `cd backend && pytest tests/unit/agent_harness/orchestrator_loop/test_scheduler.py -q` → 12 passed (every AND false-branch).
- **Test fixture**: inline `Todo(id, title, status)` builders (`_pending()` / `_completed()`), no DB.

### 2.2 Router outer-loop chains bursts on one stream via a `(event, swallow)` generator (US-1)
- **Implementation**: `_scheduled_loop_events(loop, *, session_id, user_input, trace_context, db, tenant_id)` at `backend/src/api/v1/chat/router.py:756-810`; consumed by the existing `async for event, _swallow in _scheduled_loop_events(...)` at `router.py:884`.
- **Behavior**: an outer `while True` runs `loop.run()`; for each `LoopCompleted` it loads the tenant-scoped todo store (`make_chat_todo_store(db, session_id, tenant_id)`, `router.py:793`) and calls the predicate. `swallow=True` on an intermediate `max_turns`+unfinished frame → the caller skips persist+yield and the closeout, and the generator restarts the loop with `current_input = CONTINUATION_NUDGE` (`router.py:810`). A single `loop.run()` caps at `max_turns=8` (`handler.py:771`) so a rendered burst count > 8 is proof of continuation. `loop.py` is UNTOUCHED — continuation rides the FREE cross-turn rehydration (57.127 message ledger + 57.156 `## Active Plan`).
- **Verification**: `cd backend && pytest tests/unit/api/v1/chat/test_scheduler_router.py -q` → 6 passed (drives the REAL generator with a scripted fake loop + fake todo store + patched settings: OFF byte-identical / continue + one-terminal / complete-stops / end_turn-stops / max_bursts bound / empty-plan stops).
- **Test fixture**: `_FakeLoop` (per-burst scripted async gen), `_FakeTodoStore`, `_patch()` monkeypatches `chat_router.get_settings` + `make_chat_todo_store` (module imported via `importlib.import_module("api.v1.chat.router")` — `from api.v1.chat import router` yields the `__init__`-re-exported APIRouter, not the module).

### 2.3 Per-burst billing vs final-only closeout split (US-2; Day-0 drift D-router-loopcompleted-shape)
- **Implementation**: `router.py` body — billing enqueue runs every burst; the `if not _swallow` guards gate the terminal persist+yield, quota reconcile / SLA record / audit (`router.py:934/959/967/998/1148`) and the `break→continue` (`router.py:1238`). Compaction accumulator resets per burst.
- **Behavior**: each burst really burns tokens → billing every burst (no `materialized` under-count = no C-11/C-15 漏帳 regress); quota reconcile reuses the SAME reservation → running it per burst would over-release, so it + SLA + audit + handoff run on the final burst only.
- **Verification (real, drive-through)**: ON = billing outbox `materialized=15` for a 2-burst / 15-turn run (one row per real turn, no per-burst closeout double-run); OFF = `materialized=8` for the 8-turn single burst. Reproduce: set `CHAT_SCHEDULER_AUTO_CONTINUE=true`, drive a >8-turn `write_todos` plan in chat-v2, grep the backend log `billing outbox drain — materialized=N`.

### 2.4 Default OFF is byte-identical (US-3)
- **Implementation**: `chat_scheduler_auto_continue: bool = False` + `chat_scheduler_max_bursts: int = 3` at `backend/src/core/config/__init__.py` (after `chat_memory_combined_formation`); read per-request via `get_settings()` in `_scheduled_loop_events` (`router.py:779`). When OFF, `swallow` is always False → exactly one `loop.run()`.
- **Behavior**: OFF → the generator degenerates to the pre-57.157 single burst; `max_bursts` (continuations) ⇒ total bursts ≤ `max_bursts + 1` ⇒ ≤ 32 turns/send when ON at default 3.
- **Verification**: `cd backend && pytest tests/unit -k "chat" -q` → 850 regression passed (default-OFF byte-identical; quota/SLA/audit/billing/handoff intact). Real: `get_settings()` probe printed `chat_scheduler_auto_continue=False`; drive-through OFF ran a single 8-turn burst that stopped at `max_turns` with the plan 7/12 unfinished.

### 2.5 Drive-through — continuation is real, not inferred (US-4)
- **Behavior**: ON, one `POST /api/v1/chat/` → 15 gpt-5.2 completions under one trace + LOOP (14 turns) rendered as one stream; the `messages` ledger shows the scheduler-injected `CONTINUATION_NUDGE` as a `user` turn at `13:38:33` between burst 1 and burst 2; Todos panel reached 12/12 `completed` with no manual "continue"; Verification passed (llm_judge 0.98). OFF, same prompt → 8 completions, `stop_reason=max_turns`, plan 7/12, DB nudge count stays 1 (leg-1 only).
- **Verification (reproduce)**: real chat-v2 (`:3007`) + real Azure gpt-5.2, `real_llm` mode; prompt a 12-step sequential DAG `write_todos` plan executed one step at a time. Airtight burst-boundary check: `docker exec ipa_v2_postgres psql -U ipa_v2 -d ipa_v2 -t -c "SELECT count(*) FROM messages WHERE content::text LIKE '%Continue executing the plan%';"` → 1 (ON injected exactly one nudge; OFF injected none).
- **Test fixture / evidence**: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-157/artifacts/leg1-env-on-multiburst.png` + `leg2-env-off-single-burst.png`; progress.md Day 3.

## 3. Cross-Category Contracts

**None.** No new ABC / contract / wire event (wire schema stays 26). The scheduler reuses:
- Cat 3 message rehydration — `DBMessageStore` (Sprint 57.127, `17-cross-category-interfaces.md` message-ledger).
- Cat 3/7 todo store — `make_chat_todo_store` / `DBTodoStore.load()` (Sprint 57.140).
- Cat 1 `LoopCompleted` + `TerminationReason.MAX_TURNS` (unchanged).

No 17.md edit required — nothing new to register.

## 4. Open Invariants (deferred; new carryover ADs)

- [ ] `AD-Scheduler-Burst-Stats-Aggregate-Phase58` — the final `loop_end` frame reflects only the last burst's turn/token counters, not the cross-burst total.
- [ ] `AD-Scheduler-Burst-Boundary-Wire-Phase58` — no wire event marks a burst boundary; a FE burst counter would need one.
- [ ] `AD-Scheduler-PerTenant-Phase58` — `auto_continue` / `max_bursts` are global env, not per-tenant policy (deliberate anti-AP-6; promote only on real demand).
- [ ] `AD-Scheduler-TokenBudget-Continue-Phase58` — only `max_turns` continues; `token_budget` conservatively stops (a token-aware continuation is a separate decision).
- [ ] `AD-TaskPrimitive-DAG-Enforce-Phase58` — the DAG (57.156) + scheduler both remain guidance; enforcing dependency order is deferred.

## 5. Rollback / Fallback

- **Fallback already in place**: `CHAT_SCHEDULER_AUTO_CONTINUE` default OFF → the feature is dormant until a tenant/env opts in. No rollback needed to disable — unset the env.
- **If the design proves wrong**: revert `router.py` to iterate `loop.run()` directly (drop `_scheduled_loop_events` + the 3 `if not _swallow` guards) and delete `scheduler.py` + the 2 settings. Estimated effort ~1-2 hr (single file + a pure module; `loop.py` / DB / wire untouched, so no migration/rollback there).
- **Sentinel**: the OFF-path 850-test byte-identical proof is the regression guard — any accidental behavior change when OFF fails those tests.

## 6. References

- Sprint plan: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-157-plan.md`
- Sprint checklist: `.../sprint-57-157-checklist.md`
- Progress + retrospective: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-157/`
- Change record: `claudedocs/4-changes/feature-changes/CHANGE-124-scheduler-cross-burst-auto-continue.md`
- Reality audit motivation: `claudedocs/5-status/v2-reality-audit-engine-vs-grounding-20260626.md` §9 (long-lived agent 5% ceiling)
- Prerequisites: Sprint 57.127 (message rehydration) · 57.140 (task primitive) · 57.156 (DAG)
- Calibration: `.claude/rules/sprint-workflow.md` §Scope-class multiplier matrix (`scheduler-cross-burst-spike` 0.60)

## Modification History
- 2026-07-06: Initial extract from Sprint 57.157 closeout (Day 4)
