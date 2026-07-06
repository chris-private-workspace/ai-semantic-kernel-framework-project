# CHANGE-124: Scheduler — cross-burst auto-continue

**Date**: 2026-07-06
**Sprint**: 57.157
**Scope**: 範疇 1 (Orchestrator Loop) + api/v1/chat wiring
**Closes**: `AD-TaskPrimitive-Scheduler-Phase58`

## Problem

A chat `real_llm` send runs a single `loop.run()` burst capped at `max_turns=8` (`handler.py:771`). When the agent authors a multi-step plan via `write_todos` (Sprint 57.140/57.156) that genuinely needs more than 8 turns, the burst ends at the `max_turns` ceiling with the plan **unfinished** — and the run stops. The user must manually type "continue" to get the next burst. Long-running task execution was therefore not autonomous within one send: it required a human to re-drive after every ceiling hit.

## Root Cause

`max_turns=8` is an intentional server-side governance boundary (bounded bursts, not a CC-style unbounded run). Nothing bridged one burst to the next: the SSE generator (`router.py` `_stream_loop_events`) iterated exactly one `loop.run()` and emitted its terminal `loop_end` frame regardless of whether the durable plan was complete.

## Solution

A **guidance-not-enforcement** cross-burst scheduler, default OFF (byte-identical when off).

- **NEW `agent_harness/orchestrator_loop/scheduler.py`** — pure predicate `should_continue_plan(*, enabled, stop_reason, todos, bursts_used, max_bursts) -> bool` (4-condition AND: `enabled` · `stop_reason == max_turns` · `bursts_used < max_bursts` · any todo not `completed`) + `CONTINUATION_NUDGE` constant. Conservative: only `max_turns` continues — `end_turn` / `token_budget` / `handoff` / `awaiting_approval` all stop.
- **NEW settings** (`core/config/__init__.py`): `chat_scheduler_auto_continue: bool = False` + `chat_scheduler_max_bursts: int = 3` (max_bursts = number of *continuations*; total bursts ≤ max_bursts + 1 → ≤ 32 turns).
- **`api/v1/chat/router.py`** — a chaining generator `_scheduled_loop_events(loop, …) -> AsyncIterator[(LoopEvent, swallow)]` wraps `loop.run()` in a `while` outer-loop: on an intermediate `max_turns` `LoopCompleted` with an unfinished tenant-scoped todo store, it **swallows** the terminal frame and auto-starts the next burst driven by `CONTINUATION_NUDGE` (a real user turn — `loop.run()` self-rehydrates the Cat-3 message ledger (57.127) + the `## Active Plan` (57.156) each burst, so no checkpoint/new state is needed). The existing `async for` unpacks `_swallow` and applies 3 `if not _swallow` guards. **Billing enqueue stays every burst** (each burst really burns tokens); **quota reconcile / SLA record / audit / handoff run on the final burst only** (per Day-0 drift `D-router-loopcompleted-shape` — repeated quota reconcile of the same reservation would over-release). Compaction accumulator resets per burst.

No new DB table / migration / wire event (stays 26) / codegen / frontend / `loop.py` change — the scheduler is confined to the router outer-loop + the pure predicate.

## Verification

- **Unit** (18 new): `test_scheduler.py` (12 — every AND false-branch: disabled / end_turn / token_budget / handoff / max_bursts reached+exceeded / all-completed / empty / in_progress) + `test_scheduler_router.py` (6 — drive the REAL `_scheduled_loop_events`: OFF byte-identical / continue + one-terminal / complete-stops / end_turn-stops / max_bursts bound / empty-plan stops).
- **Gate**: mypy `src` 400 Success · run_all 11/11 · 850 regression passed (chat unit+integration+orchestrator_loop → default-OFF byte-identical confirmed; quota/SLA/audit/billing/handoff intact) · black/isort/flake8 clean · LLM-SDK-leak clean.
- **Drive-through (real chat-v2 + Azure gpt-5.2)** — a 12-step DAG `write_todos` plan:
  - **ON**: 1 POST → 15 gpt-5.2 turns / 2 bursts under one trace (LOOP 14 turns, one continuous stream); the messages ledger shows the scheduler-injected `CONTINUATION_NUDGE` user turn between bursts (`13:38:33`); Todos 12/12 completed, no manual continue; Verification passed 0.98; billing `materialized=15`.
  - **OFF (control)**: same prompt → single burst, 8 completions, `stop_reason=max_turns`, plan 7/12 (unfinished), no nudge injected (DB count stays 1); billing `materialized=8`.
  - Screenshots: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-157/artifacts/leg{1,2}-*.png`.

## Impact

Backend-only (범주 1 + chat router). Default OFF → zero behavior change unless a tenant/env opts in. When on, a plan-bearing send autonomously completes across bounded bursts within one SSE stream, preserving the `max_turns` governance ceiling per burst. Guidance not enforcement: the scheduler never blocks the agent — it continues a plan the agent left unfinished, and stops on any non-`max_turns` terminal (including HITL pause). Final-burst-only closeout keeps quota/audit correct; per-burst billing keeps token accounting honest.
