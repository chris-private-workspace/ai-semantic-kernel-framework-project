# REFACTOR-006: run() Re-entrancy — Slice 1 (extract `_run_turns`)

**Date**: 2026-06-08
**Sprint**: 57.89
**Scope**: Cat 1 (Orchestrator Loop) — `loop.py` `run()` body extraction + AP-1 lint detector
**Closes**: `AD-Resume-Continuation-Fidelity` Slice 1/2

## Problem

Sprint 57.88 shipped durable pause-resume, but `resume()` continues a paused conversation via `_resume_continuation` (`loop.py`) — a SECOND, reduced copy of `run()`'s per-turn body that omits Cat 4 compaction / Cat 7 checkpoints / Cat 8 retry / Cat 9 output+per-tool guardrail / Cat 12 spans (analysis note `run-loop-reentrancy-refactor-analysis-20260608.md §3`). Consequences: a resumed conversation cannot pause again (one-approval-per-run), the copy drifts from run(), and the subagent child-loop would inherit the debt.

## Root Cause

`run()`'s per-turn body was a deeply-nested inline block inside the outer `while True` (`loop.py:1035`), never extracted into a callable unit — so `resume()` had nothing to share and got a hand-written reduced copy.

## Solution

**Pure extraction, zero behavior change.** Moved run()'s outer-`while True` body (797 lines, 1035-1831) verbatim into a NEW re-enterable `_run_turns(self, *, session_id, messages, turn_count, tokens_used, metrics_acc, ctx, root_ctx) -> AsyncIterator[LoopEvent]` async generator (programmatic move + uniform dedent-by-8, the Sprint 57.71 pattern). `run()` keeps its pre-loop input guardrail + the LOOP-span `try/finally` (SpanEnded fires on every exit) and drives the loop via `async for ev in self._run_turns(...): yield ev`. A `return` inside `_run_turns` ends the generator → run()'s `async for` completes → run()'s `finally` still fires SpanEnded(LOOP) → behavior-identical.

- **Raw-locals signature** (not a `LoopState` carrier — D-DAY0-1, documented deviation from plan §3.1): lower-risk pure extraction AND still reusable by resume() in Slice 2 (resume unpacks its `LoopState` into these args).
- **AP-1 lint made delegation-aware** (`scripts/lint/check_ap1_pipeline_disguise.py`): the detector required the `while` lexically inside `run()`; the extraction moved it to `_run_turns`, a false positive. Fix: `run_drives_while_loop()` accepts run() driving the loop via a sibling method it calls (one delegation hop). Intent preserved — a real for-pipeline behind a no-while helper still fails. +2 detector tests (delegated-while passes / delegated-no-while fails).

**NOT done** (Slice 2): rewire `resume()` onto `_run_turns`, delete `_resume_continuation`, multi-pause, drive-through. `resume()` / `_resume_continuation` are byte-unchanged this sprint.

## Verification

- Full backend `pytest`: **2231 passed / 4 skipped** = 2229 (loop extraction UNCHANGED — the zero-behavior-change proof) + 2 (new AP-1 detector tests).
- `mypy src/` 0/346 (confirms `_run_turns` has no undefined names → param list complete); `run_all` 10/10 (AP-1 delegation-aware green); black + isort + flake8 clean.
- `test_reconstructs_loop_turn_operation_tree_with_correct_nesting` + the 8 pause-resume unit + 5 integration green (run()'s span tree + pause path intact).
- Scope-guard: `git diff main -- loop.py` shows 0 +/- lines touching `resume()` / `_resume_continuation`.

## Impact

Backend-only, Cat 1 core. No DB / migration / frontend / API change. No `LoopEvent` field change (`check_event_schema_sync` green). The 主流量 chat loop behaves identically. Unblocks Slice 2 (resume() rewire + delete the reduced copy + multi-pause) and downstream the subagent child-loop (Cat 11).
