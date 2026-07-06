# Sprint 57.157 Retrospective — Scheduler: cross-burst auto-continue

**Closed**: 2026-07-06
**Branch**: `feature/sprint-57-157-scheduler-cross-burst` (from `main` `aa0dcf13`)
**Closes**: `AD-TaskPrimitive-Scheduler-Phase58`

## Q1 — What shipped?

A **guidance-not-enforcement cross-burst scheduler**, default OFF. When a chat `real_llm` burst ends at `max_turns=8` with an unfinished `write_todos` plan, the SSE generator auto-continues the loop for the next bounded burst (driven by a `CONTINUATION_NUDGE` user turn) instead of forcing the user to type "continue" — the direct fix for the reality-audit §9 "long-lived agent 5% / per-session `max_turns=8`" ceiling.

- NEW `agent_harness/orchestrator_loop/scheduler.py` — pure `should_continue_plan()` 4-condition AND predicate + `CONTINUATION_NUDGE`.
- `api/v1/chat/router.py` — a `_scheduled_loop_events` chaining generator yielding `(event, swallow)`; the existing `async for` gains 3 `if not _swallow` guards. Billing every burst; quota/SLA/audit/handoff final burst only (Day-0 drift split).
- `core/config/__init__.py` — `chat_scheduler_auto_continue: bool = False` + `chat_scheduler_max_bursts: int = 3`.
- NO migration / wire (stays 26) / codegen / frontend / `loop.py` change.

## Q2 — Calibration (estimate accuracy)

- Class **NEW `scheduler-cross-burst-spike` 0.60**; **agent-delegated: no** (parent-direct, `agent_factor` 1.0, 3-segment).
- Bottom-up ~6 hr → class-calibrated commit **~3.6 hr** (×0.60).
- Actual ~4.2-4.7 hr-equivalent → **ratio ~1.15-1.3, near/slightly-over band top**. The code + tests were on-budget (chaining-generator design AVOIDED indenting the ~400-line main-flow body; 18 tests; no re-drive, no re-architecture — UNLIKE 57.149). The variance driver was the **drive-through env-resolution detective work** (a first-session cost: discovering the app's real DSN is `…/ipa_v2` not the `.env` `DB_NAME=ipa_platform`; the container role is `ipa_v2` not `postgres`; a trace-id grep-order bug in the first poll) — not the feature.
- **Verdict**: KEEP 0.60 as the 1st data point. Per plan §7 (pre-registered): if a 2nd `scheduler-*-spike` lands >1.20 (drive-through-dominated), re-point 0.70. Single over-ish point → single-data-point caution, no re-point yet.

## Q3 — What went well?

- **Day-0 三-prong caught the MAJOR drift** `D-router-loopcompleted-shape` (the `loop_end` yields at `router.py:878` BEFORE the heavy closeout at `:888`; a naive outer-loop would re-run quota reconcile every burst → over-release). Catching it Day 0 shaped the billing-every-burst / closeout-final-only split before any code.
- **Chaining-generator design** kept the high-risk main-flow edit small: yielding `(event, swallow)` meant the ~400-line body barely changed (3 guards), instead of wrapping it in an outer indent.
- **Drive-through was airtight**: not just "14 > 8 therefore multi-burst" — the messages ledger directly shows the injected `CONTINUATION_NUDGE` user turn between bursts (ON) vs its absence (OFF), and billing `materialized=15` vs `8` proves the closeout split.
- **850-test OFF byte-identical** gave high confidence the default path is untouched.

## Q4 — What to improve?

- The env/DB resolution overhead (root `.env` vs `backend/.env`, computed DSN → `ipa_v2` db, container role) cost ~30-45 min. **Lesson recorded**: when starting a backend for a drive-through from a fresh session, probe the app's ACTUAL `get_settings().database_url` first (not the `.env` `DB_NAME`) before any DB query — the `.env` `DB_NAME`/`DB_USER` are not what the app connects with here.
- The first log-poll grep had the trace-id regex-order reversed (`$TID.*chat/completions` vs the actual `…chat/completions…,"trace_id":…` line order) → counted 0. **Lesson**: don't assume JSON field order in a log line; grep the trace-id and the URL independently.

## Q5 — Anti-pattern self-check

- **AP-1** (pipeline-as-loop): N/A — the outer-loop IS a real `while` that re-invokes `loop.run()` on a runtime condition, not a fixed step count.
- **AP-2** (side-track): ✅ reachable from `api/v1/chat` main flow; default-OFF but wired, drive-through proven.
- **AP-3** (scattering): ✅ predicate in Cat 1 `orchestrator_loop/`; router wiring in the chat router.
- **AP-4** (Potemkin): ✅ drive-through proved real multi-burst behavior + real ledger nudge + real billing rows.
- **AP-6** (future-proofing): ✅ global env, per-tenant deferred as an AD (not pre-built).
- **AP-8/AP-11**: N/A / ✅ no version suffixes.
- v2 lints: `python scripts/lint/run_all.py` → 11/11.

## Q6 — Carryover ADs (registered in next-phase-candidates.md)

- `AD-Scheduler-Burst-Stats-Aggregate-Phase58` · `AD-Scheduler-Burst-Boundary-Wire-Phase58` · `AD-Scheduler-PerTenant-Phase58` · `AD-Scheduler-TokenBudget-Continue-Phase58` · `AD-TaskPrimitive-DAG-Enforce-Phase58`.

## Q7 — Verification summary

- Unit +18 (12 predicate + 6 router) · mypy `src` 400 Success · run_all 11/11 · 850 chat regression passed (OFF byte-identical) · black/isort/flake8 clean · LLM-SDK-leak clean.
- Drive-through (real chat-v2 + Azure gpt-5.2): ON = 15 turns / 2 bursts / 1 send, ledger nudge injected, Todos 12/12, Verification 0.98, billing materialized=15; OFF = 8 turns / 1 burst, stop_reason=max_turns, plan 7/12, no nudge, billing materialized=8. Artifacts: `artifacts/leg{1,2}-*.png`.
