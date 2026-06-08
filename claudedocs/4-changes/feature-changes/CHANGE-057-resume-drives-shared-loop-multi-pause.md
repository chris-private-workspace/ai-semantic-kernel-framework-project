# CHANGE-057: resume() drives the shared `_run_turns` + multi-pause-per-run (closes AD-Resume-Continuation-Fidelity)

**Change Date**: 2026-06-08
**Change Type**: Feature Improvement (Cat 1 Orchestrator Loop behavior change + dead-copy deletion)
**Sprint**: 57.90 (run() re-entrancy refactor Slice 2/2)
**Scope**: 範疇 1 (Orchestrator Loop) — `resume()`; integration points the continuation now gains (Cat 4 / 7 / 8 / 9 / 12)
**Status**: ✅ Completed

## Change Summary

Sprint 57.89 Slice 1 extracted `run()`'s per-turn body into the re-enterable `_run_turns(...)` (`loop.py`). This sprint (Slice 2) points `resume()` at that shared unit and DELETES the `_resume_continuation` reduced copy. After `resume()` executes the pre-approved pending tool once (outside the loop — already HITL-APPROVED, so it must not re-enter the Cat 9 path), it now builds a fresh `metrics_acc` + opens a LOOP span and drives `_run_turns`. The resumed continuation therefore gains Cat 4 compaction, Cat 7 post-LLM/post-tool checkpoints, Cat 8 retry, Cat 9 per-tool deferred-pause + output guardrail, Cat 12 LOOP→TURN spans, and HANDOFF dispatch — and **a 2nd ESCALATE in the continuation checkpoints + pauses again (multi-pause-per-run)** because `_run_turns` carries the same `_cat9_hitl_branch` deferred branch `run()` uses.

## Change Reason

`AD-Resume-Continuation-Fidelity` (the top Sprint 57.88 carryover): `_resume_continuation` was a SECOND, reduced copy of the loop body that omitted run()'s Cat 4/7/8/9/12 machinery — most critically the Cat 9 per-tool deferred-pause, so a resumed conversation **could not pause again** (one-approval-per-run). It was also a duplication that drifts from `run()`, and the subagent child-loop (Cat 11) would have inherited the debt. The fix is structural: a single re-enterable loop driven by BOTH `run()` (57.89) and `resume()` (this change).

## Detailed Changes

- **`resume()` rewire** — replaced the `_resume_continuation(...)` call with: `metrics_acc = LoopMetricsAccumulator()` + `start_span(name="agent_loop.run", category=ORCHESTRATOR, attributes={"span_type":"LOOP"}) as root_ctx` (mirror run(): `SpanStarted(LOOP)` in `try`, loop-measured `SpanEnded(LOOP)` in `finally`) + `async for ev in self._run_turns(session_id, messages, turn_count, tokens_used, metrics_acc, ctx, root_ctx): yield ev`. The pending-tool exec + approval bridge ABOVE are byte-identical (the pre-approved tool still executes once outside `_run_turns` → no re-escalation; locked analysis-note §6.1 option (b)).
- **DELETE `_resume_continuation`** — the 148-line reduced copy removed; zero code callers remain.
- **Stale docstring de-stale (Karpathy §3)** — `resume()`'s docstring previously claimed the continuation "intentionally does NOT re-enter run()'s body"; rewritten to describe the shared-`_run_turns` drive + the multi-pause gain + the deleted copy.
- **Tests** — NEW `test_resume_continuation_can_pause_again` (+ builder `_build_resume_loop_multipause`) proves multi-pause: 1st pending tool exec'd once → continuation requests a 2nd approval-required tool → ESCALATE → `LoopCompleted(awaiting_approval)` + NEW `pending_approval` checkpoint + `ApprovalRequested`; 2nd tool NOT executed. A LOOP-span assertion added to `test_resume_approved_executes_tool_and_continues` locks in that resume drives `_run_turns`. The other 7 pause-resume tests pass unchanged (contains-style; new events additive).

## Modified Files List

- `backend/src/agent_harness/orchestrator_loop/loop.py` — resume() rewire + `_resume_continuation` deleted + docstring + MHist (net −164 lines)
- `backend/tests/unit/agent_harness/orchestrator_loop/test_loop_pause_resume.py` — +1 multi-pause test + builder + LOOP-span assertion + header
- `docs/03-implementation/agent-harness-planning/19-pause-resume-design.md` — §5 `AD-Resume-Continuation-Fidelity` marked CLOSED

## Test Verification

- Unit: `pytest test_loop_pause_resume.py` → 9 passed (incl. multi-pause).
- Full backend: `pytest -q` → **2232 passed / 4 skipped** (57.89 baseline 2231 → +1 = the new multi-pause test; no test deleted).
- mypy `src/ --strict` → 0/346. `run_all` → 10/10 (AP-1 accepts resume driving `_run_turns`; event-schema sync; SDK leak 0; AP-8). black/isort/flake8 clean.
- **Drive-through (real UI + real backend + real Azure gpt-5.2)** — PASS: chat-v2 real_llm → echo `alpha` → pause 1 → approve → executed → echo `beta` → **pause 2 (NEW approval, multi-pause)** → approve → executed → end_turn answer rendered. The 2nd pause checkpoint persisted + the 2nd `/resume` loaded it. NO frontend fix needed. Evidence: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-90/artifacts/sprint-57-90-multipause-drivethrough.png` + progress.md Day 3 observed-vs-intended table.

## Impact

- Backend-only behavior change to `resume()` (frontend untouched — it already handled a repeated pause). The resumed continuation is now run()-grade (full Cat 4/7/8/9/12 + HANDOFF) and can pause arbitrarily many times per run.
- Closes `AD-Resume-Continuation-Fidelity` (Slice 1 + Slice 2). Unblocks Slice 3 (generalized pause points) + the subagent child-loop (Cat 11), which would otherwise have inherited the reduced-copy debt.
- No DB / migration / contract (17.md) change. LLM-neutral (no adapter/SDK touched).
