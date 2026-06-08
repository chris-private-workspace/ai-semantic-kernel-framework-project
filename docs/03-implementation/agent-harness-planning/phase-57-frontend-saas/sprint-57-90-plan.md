# Sprint 57.90 Plan — run() Re-entrancy Refactor Slice 2: rewire resume + delete the copy + multi-pause (closes AD-Resume-Continuation-Fidelity)

**Purpose**: The 地基 A keystone debt-paydown, Slice 2 of 2 — the close of `AD-Resume-Continuation-Fidelity`. Sprint 57.89 Slice 1 extracted `run()`'s per-turn body into the re-enterable `_run_turns(...)` (`loop.py:1055`) with zero behavior change, but `resume()` (`loop.py:1847`) still continues via `_resume_continuation` (`loop.py:1998-2145`) — a SECOND, reduced copy of the loop body that omits Cat 4 compaction / Cat 7 checkpoints / Cat 8 retry / Cat 9 per-tool guardrail+deferred-pause / Cat 9 output guardrail / Cat 12 spans / HANDOFF (analysis note `claudedocs/1-planning/run-loop-reentrancy-refactor-analysis-20260608.md §3`). **This sprint = Slice 2: rewire `resume()` to drive the shared `_run_turns(...)` (after executing the pre-approved pending tool once, outside the loop), then DELETE `_resume_continuation`.** Because `_run_turns` carries the Cat 9 per-tool deferred-pause branch, a 2nd ESCALATE in the resumed continuation now checkpoints + pauses again **for free** → multi-pause-per-run falls out (the §3-#1 + #4 limitation closes simultaneously). **This is a behavior change** (resume's continuation gains the omitted machinery) — NOT zero-behavior-change like Slice 1 — so the 57.88 continuation-path test assertions are updated (Never-Delete: convert, not delete) and a NEW multi-pause test + a **drive-through** (real UI + real backend + real Azure LLM: echo → pause → approve → echo → 2nd pause → approve → answer) are the acceptance. **Record = CHANGE-057** (feature change + the `_resume_continuation` deletion); no new design note (continuation of the 57.88 pause-resume domain — `19-pause-resume-design.md §5` Open Invariant is marked CLOSED).
**Category / Scope**: Cat 1 (Orchestrator Loop — `resume()` rewire onto the shared `_run_turns`; delete `_resume_continuation`) + the integration points the continuation now gains (Cat 4 compaction / Cat 7 checkpoint / Cat 8 retry / Cat 9 guardrail+HITL deferred-pause / Cat 12 spans); Phase 57.90
**Created**: 2026-06-08
**Status**: Draft (scope below; code execution gated on Day-0 GO)
**Source**: Sprint 57.89 carryover (`next-phase-candidates.md §Sprint 57.89 Carryover` — Slice 2 is the immediate next step) + analysis note `run-loop-reentrancy-refactor-analysis-20260608.md §5/§6/§7` (target design + locked decision + slicing). The pre-approved-pending-tool-must-not-re-escalate decision is **locked** (analysis note §6.1 option (b)).

> **Modification History**
> - 2026-06-08: Initial creation — Slice 2 rewire+delete+multi-pause+drive-through; folds the analysis note's §5 target design + §6.1 locked decision + §7 slicing

---

## 0. Background

Slice 1 (Sprint 57.89) paid down half the keystone debt: `run()`'s per-turn body is now a single re-enterable `_run_turns(session_id, messages, turn_count, tokens_used, metrics_acc, ctx, root_ctx)` async generator that `run()` drives via `async for ev in self._run_turns(...)`. The reduced copy `_resume_continuation` was deliberately left in place (Slice 1 scope guard). Slice 2 completes the close: point `resume()` at `_run_turns` and delete the copy.

### Ground truth re-confirmed (Day-0 head-start — this plan's Day-0 verify)

The analysis note + the Slice-1 commit established (re-confirmed at this plan's Day 0):
- **`_run_turns` (`loop.py:1055-1846`)** is the verbatim run() body: pre-LLM terminators → Cat 4 compaction → Cat 5 PromptBuilder → LLM → parse → Cat 7 post-LLM checkpoint (`_emit_state_checkpoint`, `loop.py:1446`) → Cat 9 output guardrail → stop_reason → dispatch (incl. HANDOFF) → tool loop (`_cat9_tool_check` `loop.py:597` → `_cat9_hitl_branch` `loop.py:679` whose deferred-pause branch checkpoints at `loop.py:813` with `pending_approval=`) + Cat 8 retry (`_handle_tool_error`) → Cat 7 post-tool checkpoint (`loop.py:1825`). **Everything multi-pause needs is already inside `_run_turns`.**
- **`resume()` (`loop.py:1847-1996`)** already: builds ctx/session_id/messages/turn_count/tokens_used from `state`; yields `LoopStarted`; reads `pending_approval`; non-blocking `get_decision`; reject → `GuardrailTriggered(block)` + `LoopCompleted(GUARDRAIL_BLOCKED)`; APPROVED → execs the pending tool (raw, already-approved) + appends the observation; then calls `_resume_continuation`. **The rewire swaps that last call for an `_run_turns` drive inside a LOOP span.**
- **`_resume_continuation` (`loop.py:1998-2145`)** has exactly ONE caller — `resume()` @1990 (Day-0 grep). After the rewire it is dead → DELETE.
- **The resume-path loop instance is fully wired** — `ResumeService._default_build_loop` (`platform_layer/resume/service.py:94`) builds via `build_real_llm_handler(...)`, the SAME builder the chat path uses (zero divergence). Since the original chat loop saved the 1st pause checkpoint, the builder already wires `reducer`/`checkpointer`/`tenant_id` → the **2nd** pause checkpoint (in the resumed `_run_turns`) saves the same way → multi-pause works end-to-end through `POST /chat/{id}/resume` with NO ResumeService change.

---

## 1. Sprint Goal

Rewire `resume()` so that, after it executes the pre-approved pending tool once (outside the loop, as it does today — already HITL-APPROVED so it must NOT re-enter `_cat9_*`, the locked §6.1 decision) and appends the observation, it drives the shared `_run_turns(...)` inside a LOOP span (constructing a fresh `metrics_acc` + opening a `root_ctx` LOOP span exactly as `run()` does), instead of calling `_resume_continuation`. Then **DELETE `_resume_continuation`** (now dead). The resumed continuation thereby gains Cat 4 compaction, Cat 7 post-LLM/post-tool checkpoints, Cat 8 retry, Cat 9 per-tool deferred-pause + output guardrail, Cat 12 LOOP→TURN spans, and HANDOFF dispatch — and a **2nd ESCALATE in the continuation checkpoints + pauses again (multi-pause-per-run)** because `_run_turns` carries the same `_cat9_hitl_branch` deferred branch run() uses. **This is a deliberate behavior change** (resume's continuation event stream becomes the richer run()-grade stream): the 57.88 continuation-path test assertions are updated to the new stream (Never-Delete: convert), a NEW unit test asserts a 2nd-ESCALATE-pauses-again, and a **drive-through** (real UI + real backend + real Azure gpt-5.2) walks echo → pause → approve → echo → 2nd pause → approve → answer. Out of scope: Slice 3 generalized pause points; subagent child-loop; checkpoint-bloat / per-tenant-capability / reject-reaper carryover ADs.

---

## 2. User Stories

- **US-1 (resume drives the shared loop)** — As the loop maintainer, I want `resume()` to drive `_run_turns(...)` (after the pre-approved pending-tool exec) instead of `_resume_continuation`, so the resumed continuation runs the SAME machinery as a fresh run() (Cat 4/7/8/9/12 + HANDOFF), eliminating the reduced-copy divergence. → `resume()` builds a fresh `metrics_acc` + opens a `root_ctx` LOOP span (mirror run()'s `start_span` + `SpanStarted`/`SpanEnded`) and `async for ev in self._run_turns(...)`.
- **US-2 (delete the copy)** — As the codebase, I want `_resume_continuation` deleted once it is dead, so there is a single source of truth for the per-turn loop (no drift, Karpathy §3 — orphan from this change is mine to clean). → remove `loop.py:1998-2145`; grep proves zero callers.
- **US-3 (multi-pause-per-run)** — As an approver, I want a 2nd tool that needs approval, requested during the resumed continuation, to pause again (checkpoint + release SSE) so I can approve it too — not silently execute or fail. → falls out of US-1 (`_run_turns` carries `_cat9_hitl_branch`); proven by a NEW unit test (2nd ESCALATE → `LoopCompleted(AWAITING_APPROVAL)` + a new `hitl_pause` checkpoint) + the drive-through.
- **US-4 (pre-approved pending tool does not re-escalate)** — As the resumed loop, I want the already-APPROVED pending tool to execute exactly once without re-triggering `_cat9_hitl_branch` ESCALATE, so resume does not deadlock on its own approved tool. → keep the pending-tool exec OUTSIDE `_run_turns` (the locked §6.1 option (b)); `_run_turns`'s first iteration is a fresh LLM turn that sees the appended observation, it does not re-run the pending tool.
- **US-5 (drive-through acceptance)** — As the user, I want the multi-pause resume to actually work end-to-end through the real chat UI + backend + LLM, not just pass gates. → drive-through: echo → pause → approve → echo → 2nd pause → approve → answer; screenshot + observed-vs-intended diff in progress.md; fix any frontend gap that blocks a 2nd HITLTurn after the 1st resume.

---

## 3. Technical Specifications

### 3.0 Architecture (the rewire)

```
BEFORE (Slice 1 end)                         AFTER (Slice 2)
resume():                                    resume():
  ... build state locals + LoopStarted         ... build state locals + LoopStarted   [unchanged]
  ... read pending / get_decision              ... read pending / get_decision        [unchanged]
  ... reject → GUARDRAIL_BLOCKED                ... reject → GUARDRAIL_BLOCKED          [unchanged]
  ... APPROVED → exec pending tool + append    ... APPROVED → exec pending tool + append [unchanged]
  async for ev in self._resume_continuation(   metrics_acc = LoopMetricsAccumulator()
      messages, turn_count, tokens_used, ctx): async with start_span(LOOP) as root_ctx:
      yield ev                                     try:
                                                       yield SpanStarted(LOOP)
                                                       async for ev in self._run_turns(
                                                           session_id, messages, turn_count,
                                                           tokens_used, metrics_acc, ctx, root_ctx):
                                                           yield ev
                                                   finally:
                                                       yield SpanEnded(LOOP)
_resume_continuation():  [114-line copy]      _resume_continuation():  [DELETED]
```

The pending-tool exec + approval bridge (LoopStarted, ApprovalReceived, the pending ToolCall* events) stay **byte-identical** to 57.88 — only the continuation drive changes. The LOOP span brackets the `_run_turns` continuation (where the omitted Cat 12 TURN spans matter); the approval-bridge events stay span-less (they are not turns), which minimizes 57.88 test churn (the early-return reject/error paths are unchanged).

### 3.1 `resume()` rewire (US-1/US-4)
- Construct `metrics_acc = LoopMetricsAccumulator()` (fresh per-resume — the continuation's per-run metrics start clean; `_resume_continuation` had no accumulator, so the resumed `LoopCompleted` now ALSO carries the 57.2 token-split / 57.65 cache / 57.82 verification fields → a gain, not a loss).
- Open the LOOP span via `self._tracer.start_span(name="agent_loop.run", category=SpanCategory.ORCHESTRATOR, trace_context=ctx, attributes={"span_type": "LOOP"})` as `root_ctx`, mirror run()'s `_root_ctx_t0` + `SpanStarted(LOOP)` (in the `try`) + `SpanEnded(LOOP)` (in `finally`, loop-measured `duration_ms`).
- Drive `async for ev in self._run_turns(session_id=session_id, messages=messages, turn_count=turn_count, tokens_used=tokens_used, metrics_acc=metrics_acc, ctx=ctx, root_ctx=root_ctx): yield ev`.
- **US-4**: the pending tool is executed BEFORE this block (already-APPROVED, raw `_tool_executor.execute`, as today) and its observation appended to `messages`; `_run_turns`'s first iteration is a fresh LLM turn — it never re-runs the pending tool, so no re-escalation. (Cat 8 retry on the resumed pending-tool exec stays deferred — it is already approved; a failure surfaces as `ToolCallFailed` and the continuation's first LLM turn observes it. Note in §9.)

### 3.2 Delete `_resume_continuation` (US-2)
- After the rewire, grep confirms `_resume_continuation` has zero callers → remove the method (`loop.py:1998-2145`). Remove any now-unused imports it solely required (check `CacheBreakpoint` / `ChatRequest` / `classify_output` / `should_terminate_*` are still used by `_run_turns` — they are; verify no orphan import).

### 3.3 Multi-pause-per-run (US-3)
- No new code: `_run_turns`'s tool loop calls `_cat9_tool_check` (`loop.py:597`) → `_cat9_hitl_branch` (`loop.py:679`) whose deferred branch emits `_emit_state_checkpoint(..., pending_approval=...)` (`loop.py:813`) + `LoopCompleted(AWAITING_APPROVAL)` + `return`. Driven from resume, a 2nd ESCALATE therefore writes a NEW `hitl_pause` checkpoint (with the full continuation buffer in `resume_messages`) and releases SSE — the resume LOOP-span `finally` fires `SpanEnded(LOOP)`. The client approves + calls `/chat/{id}/resume` again; `ResumeService.resume_session` loads the LATEST `hitl_pause` snapshot (it already `ORDER BY version DESC LIMIT 1`) → the 2nd pause. **End-to-end with NO ResumeService change** (the resume-path loop is wired by `build_real_llm_handler`, zero divergence — it saved the 1st checkpoint, it saves the 2nd).
- NEW unit test (`test_loop_pause_resume.py`): resume with a continuation whose first LLM turn requests an approval-required tool → assert the stream ends `LoopCompleted(stop_reason="awaiting_approval")` AND a new pause checkpoint was emitted (`StateCheckpointed` / the deferred-branch contract) — i.e. the resumed loop can pause again.

### 3.4 Drive-through (US-5)
- Real UI (`dev.py start`) + real backend (clean restart per Risk Class E — kill stale `--reload` workers first) + real Azure gpt-5.2 (NOT echo/mock LLM; the `echo_tool` is the approval-required tool, the LLM is real). Path: prompt the agent to echo twice across turns → 1st `echo` ESCALATEs → pause (HITLTurn) → approve → resume → continuation's LLM requests `echo` again → 2nd pause (HITLTurn) → approve → resume → final answer renders.
- Walk every control: the 2nd HITLTurn must appear, its Approve must drive a 2nd `/resume`, the final answer must render. If the frontend (`useLoopEventStream` / `chatStore` / `HITLTurn`) does NOT surface a 2nd `AWAITING_APPROVAL` after the 1st resume, fix it (in scope — making the feature drivable). Screenshot + observed-vs-intended diff → progress.md.
- If a real two-echo prompt is non-deterministic with the live LLM, fall back to a scripted real-backend drive (two `/resume` round-trips via httpx against the real loop with `echo_tool`) AND still attempt the UI drive; record exactly what was driven (no "gate-only" passed off as drive-through).

### 3.5 What is explicitly NOT done (Slice 3+)
- No generalized pause points (input ESCALATE / mid-thinking / between-turns). No subagent child-loop (Cat 11). No checkpoint-bloat fix (`resume_messages` → `messages` table). No per-tenant capability policy. No reject-path reaper. (These are Slice 3 / separate carryover ADs per analysis note §7/§8.)

### 3.6 Lint / neutrality / doc single-source
- `check_llm_sdk_leak` 0 (no adapter/SDK touched). `check_ap1_pipeline_disguise` green (`resume()` now ALSO drives the `while`-loop via `_run_turns` — the Slice-1 delegation-aware detector already accepts a sibling-method-driven loop; confirm `resume` is not flagged). `check_promptbuilder_usage` (AP-8) green (PromptBuilder is inside `_run_turns`, untouched). No new contract → 17.md unchanged (the `resume()` ABC signature is unchanged). `19-pause-resume-design.md §5` Open Invariant `AD-Resume-Continuation-Fidelity` marked CLOSED. CHANGE-057 records the rewire + deletion.

### 3.7 Validation (US-1..US-5)
- **mypy `src/ --strict` 0**; `run_all` 10/10; `black`/`isort`/`flake8` clean.
- **pytest**: the 57.88 pause-resume tests (8 unit + 5 integration) — the early-return paths (pending-absent, decision-None, reject) assert UNCHANGED; the approve-then-continue paths get their continuation assertions updated to the run()-grade stream (spans/checkpoints/metrics fields) — convert, never delete. NEW multi-pause unit test (US-3). Full backend suite green (expect a small NET test-count delta from the NEW multi-pause test + any split assertion helpers — documented, not smuggled).
- **Drive-through** (US-5): real UI + real backend + real Azure — echo→pause→approve→echo→2nd pause→approve→answer; screenshot + observed-vs-intended diff in progress.md. (Per CLAUDE.md §Drive-Through Acceptance — resume is user-facing.)

---

## 4. File Change List

| File | Change |
|------|--------|
| `backend/src/agent_harness/orchestrator_loop/loop.py` | **EDIT** — `resume()` (`~1953-1996`): replace the `_resume_continuation` call with a fresh `metrics_acc` + a `root_ctx` LOOP span driving `_run_turns(...)` (US-1/US-4). **DELETE** `_resume_continuation` (`1998-2145`) (US-2). Remove any orphan imports. Update file-header MHist (1-line, E501-safe). |
| `backend/tests/unit/agent_harness/orchestrator_loop/test_loop_pause_resume.py` | **EDIT** — update the approve-then-continue assertions to the run()-grade continuation stream (spans/checkpoints/metrics); keep early-return assertions unchanged. **ADD** the multi-pause unit test (US-3). |
| `backend/tests/integration/api/test_chat_pause_resume_e2e.py` | **EDIT** — update the resumed-continuation event assertions to the richer stream (convert, not delete). Add a 2nd-pause integration assertion if feasible at the API layer. |
| frontend (`useLoopEventStream` / `chatStore` / `HITLTurn`, IF the drive-through finds a gap) | **EDIT (conditional)** — surface a 2nd `AWAITING_APPROVAL` after the 1st resume so a 2nd HITLTurn renders + its Approve drives a 2nd `/resume`. Only if the drive-through proves it's needed. |
| `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-90-plan.md` + `-checklist.md` | **NEW** — this plan + checklist |
| `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-90/progress.md` + `retrospective.md` | **NEW** — Day 0-N progress + retro |
| `claudedocs/4-changes/feature-changes/CHANGE-057-resume-drives-shared-loop-multi-pause.md` | **NEW** — the change record (rewire + delete + multi-pause + drive-through) |
| `docs/03-implementation/agent-harness-planning/19-pause-resume-design.md` | **EDIT** — §5 mark `AD-Resume-Continuation-Fidelity` CLOSED (Slice 1+2 landed) |

No new DB table / no migration / no new contract (17.md unchanged) / no Azure-adapter change / no `ResumeService` change.

---

## 5. Acceptance Criteria

- `resume()` drives `_run_turns(...)` inside a `root_ctx` LOOP span (with a fresh `metrics_acc`) after the pre-approved pending-tool exec; the pending tool executes exactly once and does NOT re-escalate (US-1/US-4).
- `_resume_continuation` is DELETED; grep proves zero callers; no orphan import remains (US-2).
- A 2nd ESCALATE in the resumed continuation checkpoints (`hitl_pause`) + emits `LoopCompleted(AWAITING_APPROVAL)` + releases SSE; a 2nd `/resume` loads it and continues — proven by the NEW unit test (US-3) AND the drive-through (US-5).
- The approval-bridge / early-return resume paths (pending-absent ERROR, decision-None ERROR, reject GUARDRAIL_BLOCKED) are byte-identical to 57.88 (their test assertions unchanged); the approve-then-continue paths assert the run()-grade continuation stream (converted, not deleted).
- `mypy --strict src/` 0; `run_all` 10/10 (LLM SDK leak 0; AP-1 accepts resume driving `_run_turns`; AP-8 PromptBuilder); `black`/`isort`/`flake8` clean; full backend pytest green (NET delta documented). `19-pause-resume-design.md §5` marks the AD CLOSED; CHANGE-057 written.
- **Drive-through PASS**: real UI + real backend + real Azure — echo→pause→approve→echo→2nd pause→approve→answer; screenshot + observed-vs-intended diff recorded. (No "gate-only" claimed as drive-through.)

---

## 6. Deliverables

- [ ] `resume()` rewired to drive `_run_turns` in a LOOP span + fresh `metrics_acc`; pending tool exec'd once, no re-escalation (US-1/US-4)
- [ ] `_resume_continuation` deleted; zero callers; no orphan import (US-2)
- [ ] multi-pause: NEW unit test (2nd ESCALATE pauses again) green (US-3)
- [ ] 57.88 tests converted to the run()-grade continuation stream (early-return paths unchanged); full backend pytest green (US-3/validation)
- [ ] mypy 0 + run_all 10/10 + format chain (validation)
- [ ] **drive-through PASS** (real UI + real backend + real Azure; screenshot + diff) (US-5)
- [ ] CHANGE-057 + `19-pause-resume-design.md §5` CLOSED + progress.md + retrospective.md
- [ ] commit (Day 0-N) — push + PR user-authorized

---

## 7. Workload Calibration

Scope class: **`backend-core-loop-refactor` (0.55) — 2nd data point, CAVEATED (different shape from Slice 1)**. Slice 1 was a pure extraction (zero-behavior-change gate). Slice 2 is a behavior-change slice on the SAME 主流量 Cat 1 surface: a small mechanical rewire (swap one call for a LOOP-span `_run_turns` drive) + a mechanical delete (114-line dead copy) + test-assertion conversion (the richer continuation stream) + a NEW multi-pause test + a real drive-through. The dominant cost is the test conversion + the drive-through (incl. a possible small frontend fix), not new code. Reuse the Slice-1 class for continuity but flag the shape difference (behavior change + drive-through vs pure extraction) — if its ratio diverges from Slice 1's, that's the shape, not the multiplier. **Agent-delegated: no** (parent-direct) — 主流量 loop surgery + a behavior change with a drive-through is too high-blast-radius to delegate cleanly; `agent_factor = 1.0`. Does NOT extend the `AD-Calibration-AgentDelegated-WallClock-Measure` streak (parent-direct, same as 57.88/57.89). Caveat: 2nd unvalidated data point in this class — record caveated, do NOT generalize.

> Bottom-up est ~10 hr → class-calibrated commit ~5.5 hr (mult 0.55).

If Day-1 shows the test-assertion conversion balloons (e.g. the continuation stream change ripples into many more tests than the pause-resume suite), STOP and re-scope (split the drive-through into its own follow-up) rather than rush the conversion.

---

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| **2nd pause checkpoint does not save** (multi-pause silently broken) | Day-0 verified: the resume-path loop is built by `build_real_llm_handler` (same as chat; zero divergence) — it saved the 1st checkpoint so it has `reducer`/`checkpointer`/`tenant_id` → the 2nd saves too. Day-1 grep `build_real_llm_handler` to re-confirm the wiring; the NEW unit test + drive-through are the proof. |
| **Pre-approved pending tool re-escalates** (resume deadlocks on its own approved tool) | Locked §6.1 option (b): exec the pending tool OUTSIDE `_run_turns` (as today), append the observation, THEN drive `_run_turns` (first iteration = fresh LLM turn, not a re-run of the pending tool). No re-escalation path exists. |
| **Test churn underestimated** (continuation-stream change ripples widely) | Scope guard: the early-return resume paths (reject/error) stay byte-identical → only the approve-then-continue assertions change. If ripple exceeds the pause-resume suite, STOP + re-scope (§7). Never delete a test to make it pass — convert it. |
| **Frontend can't surface a 2nd HITLTurn** (drive-through blocked) | In scope to fix (US-5) — making the feature drivable IS the acceptance. Likely the existing `useLoopEventStream.resume` + `HITLTurn` re-trigger on a repeated `AWAITING_APPROVAL`; verify, small fix if not. |
| **Cat 12 span tree for the continuation** | resume opens the LOOP span (mirror run()); `_run_turns` nests TURN under `root_ctx`. Verify `test_reconstructs_loop_turn_operation_tree_with_correct_nesting`-style assertions hold for the resumed path (the continuation turns now appear in the tree — expected gain). |
| **Smuggling unrelated change into the rewire** | The rewire + delete is the only `loop.py` change; the pending-tool-exec + approval bridge stay byte-identical. Commit the rewire+delete together; the test conversions in the same PR but the diff to `resume()`'s bridge = 0 lines. |
| **Drive-through non-determinism (real LLM two-echo)** | Fall back to a scripted real-backend two-`/resume` drive AND attempt the UI drive; record exactly what was driven (§3.4). No gate-only passed off as drive-through. |
| **Risk Class E (stale `--reload` backend)** | Clean restart before the drive-through (kill all stale uvicorn reloader+worker procs; confirm sole owner of :8000) — a wiring/startup behavior must be verified against a fresh process. |
| **Risk Class C (test isolation on the most-tested file)** | Run the full suite (not a subset); the module-level singleton reset fixtures are already in place (`agent_harness/conftest.py`, Sprint 57.53). |
| **LLM-neutrality** | No adapter/SDK touched; `check_llm_sdk_leak` gates. |

---

## 9. Out of Scope (this sprint; → Slice 3 / separate ADs)

- **Slice 3**: generalized pause points (input ESCALATE / mid-thinking / between-turns) now enabled by the shared `_run_turns` + checkpoint-everywhere.
- **Subagent child-loop (Cat 11)** — consumes this refactor; distinct larger sprint.
- **Cat 8 retry on the resumed pending-tool exec** — the pre-approved pending tool still executes raw (already approved); wrapping that single bridge exec in Cat 8 retry is a minor deferred enhancement (a failure already surfaces to the continuation LLM).
- **`AD-Resume-Checkpoint-Bloat`** (`resume_messages` → `messages` table + checkpoint TTL) — separate 57.88 carryover AD.
- **`AD-Resume-Tenant-Capability-Policy`** (per-tenant `capability_matrix.yaml`) — separate AD.
- **`AD-Resume-Reject-Path`** (reject-then-resume / checkpoint reaper for dangling rejects) — separate AD.
- **地基 B explicit phase machine** — separate design decision.
