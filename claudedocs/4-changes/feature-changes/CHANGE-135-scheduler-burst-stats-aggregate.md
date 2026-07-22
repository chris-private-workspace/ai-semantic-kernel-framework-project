# CHANGE-135: The final `loop_end` reports the CROSS-BURST turn/token totals (scheduler)

**Date**: 2026-07-22
**Sprint**: 57.166
**Scope**: 範疇 1 (Orchestrator Loop) via `api/v1/chat/router.py` — backend only (NO migration / NO new wire field / NO frontend change)

## Problem

Sprint 57.157 shipped the cross-burst scheduler (`CHAT_SCHEDULER_AUTO_CONTINUE`): when a `write_todos` plan is still unfinished at the `max_turns` ceiling, the router auto-continues the loop into another burst. Each burst emits its **own** `LoopCompleted` carrying only **that burst's** counters; the intermediate ones are swallowed so the FE sees a single terminal `loop_end`.

Consequence: the one frame that survives — the terminal `loop_end` — reported only the **last** burst. A run that actually took 7 turns across 3 bursts told the human "2 turns", and the `conversation_completed` audit row recorded the same understatement (turns + total/input/output tokens). Closes the task-primitive-range carryover **`AD-Scheduler-Burst-Stats-Aggregate-Phase58`** (57.157).

## Root Cause

`_stream_loop_events` (`router.py`) read the per-burst event directly at its two summary read-sites — the FE payload patch and the `conversation_completed` audit `operation_data` — with no notion of "this is burst N of M". Nothing accumulated across the `async for`, so whichever `LoopCompleted` happened to be final won.

## Solution

Four surgical edits in `_stream_loop_events`, all inside the existing generator (no signature / event / wire change):

1. **4 accumulators** (`agg_turns` / `agg_total_tokens` / `agg_input_tokens` / `agg_output_tokens`) initialised before the `async for`.
2. **Accumulate every `LoopCompleted`** — swallowed *and* final — before serialize.
3. **Patch only the final frame**: `payload["data"]["total_turns"] = agg_turns` under `isinstance(event, LoopCompleted) and not _swallow`. (`sse.py`'s `loop_end` carries `total_turns` but not `total_tokens` — Day-0 `D-loopend-payload-fields` — so the token aggregate lands in the audit row only.)
4. **Audit `operation_data`** 4 counters → `agg_*`.

**Deliberately NOT changed — the billing enqueue still reads `event.*`.** Day-0 `D-billing-per-burst-ungated` confirmed `router.py:1024`'s enqueue is a standalone `if`, NOT gated on `_swallow`, so it fires once per burst; feeding it the running aggregate would bill burst 1 again inside burst 2's row (double-charge). Keeping the aggregate in separate locals — rather than mutating the event — is what makes both read-sites correct simultaneously.

Scheduler OFF / single burst → `agg_* == event.*` → byte-identical to the pre-change behaviour.

## Verification

- **Gate**: mypy `src` 400/0 · `python scripts/lint/run_all.py` **12/12** · black / isort / flake8 clean · LLM-SDK-leak clean. Backend pytest: scheduler suite (18) + `test_router` + the 4 new = **48 passed**; chat integration (e2e / cost_ledger / quota_reconcile / main_transcript_persist) **27 passed** → scheduler-OFF main path unchanged. The 2 `test_audit_log_observer` failures are pre-existing on `main` (Day-0 `D-audit-observer-pre-existing-fails`, `_max_main_seq` vs `AsyncMock`), unchanged by this PR.
- **New tests** — `backend/tests/unit/api/v1/chat/test_scheduler_burst_stats.py` (4), driving the REAL `_stream_loop_events` with a scripted 2-burst fake loop: T1 audit `operation_data` == 15 / 170 / 135 / 35 (8+7 turns, 100+70 tokens); T2 the single REAL-serialized `loop_end` frame == 15 turns; T3 scheduler OFF → 8 (no double count); T4 `billing_outbox.enqueue` receives 80/20 then 55/15 — **each burst's own tokens, never the sum**.
- **Drive-through PASS** (real chat-v2 UI + real backend + real Azure `gpt-5.2`; scheduler ON, `max_bursts=3`): 3 bursts (3 × `loop_start` + 3 `agent_loop.run` spans), exactly **ONE** terminal `loop_end` = `stop=end_turn turns=7`; ChatHeader badge **"· 7 turns"**; `conversation_completed` audit `total_turns` **7**. With the per-burst ceiling in force, 7 is arithmetically impossible for a single burst → the badge is the aggregate. Pre-fix both surfaces would have read ≤ the last burst. Screenshot: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-166/artifacts/sprint-57-166-drivethrough-aggregate-7-turns.png`.
  - The run needed a **temporary, user-approved test lever** to make the ceiling hit deterministic (`handler.py` `max_turns` 8 → 2) plus `HITL_ENABLED=false` (env only, so burst 2+ weren't frozen at the `python_sandbox` approval gate). Both reverted — `git diff backend/src/api/v1/chat/handler.py` is empty and the backend was restarted with no test flags. Two earlier legs (HITL gate / the model declining to self-loop on a `write_todos`-only prompt) are recorded as inconclusive in progress.md Day 3, not as passes.

## Impact

- Backend only; 1 production file (`router.py`) + 1 new test file. No migration, no new/changed wire field, no frontend change, no `agent_harness/` change.
- Behaviour changes **only** when the scheduler actually continues (default OFF). Billing/cost-ledger rows are untouched by design.
- Not aggregated (deliberate): `cached_input_tokens` and `cache_hit_rate` on the `loop_end` payload — the latter is a *rate*, so summing is meaningless and a weighted re-derivation is its own slice → carryover `AD-Scheduler-Burst-CacheRate-Aggregate`.
