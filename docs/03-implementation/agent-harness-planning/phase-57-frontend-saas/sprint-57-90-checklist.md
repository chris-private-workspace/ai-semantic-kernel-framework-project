# Sprint 57.90 — Checklist (run() Re-entrancy Refactor Slice 2: rewire resume + delete copy + multi-pause + drive-through)

**Plan**: [`sprint-57-90-plan.md`](./sprint-57-90-plan.md)
**Created**: 2026-06-08
**Status**: Draft (code gated on Day-0 GO)

> Rule: only `[ ]` → `[x]`; never delete unchecked items; defer with `🚧 + reason`.
> CHANGE (behavior change, NOT pure refactor) → CHANGE-057 record; no new design note (update `19-pause-resume-design.md §5`). Gate = full backend pytest green (NET delta documented) + **drive-through PASS** (resume is user-facing). Locked §6.1: pre-approved pending tool exec'd OUTSIDE `_run_turns` (no re-escalation).

---

## Day 0 — Plan-vs-Repo Verify + Branch

### 0.1 Three-prong Day-0 verify
- [x] **Prong 1 (path)**: confirmed — `resume()` @1847 / `_resume_continuation` @1998 (one caller @1990) / `_run_turns` @1055 / `_emit_state_checkpoint` @2147 / `_cat9_tool_check` @597 / `_cat9_hitl_branch` @679 (deferred checkpoint @813 `pending_approval=`) / `run()` delegates @1036 with sig (session_id, messages, turn_count, tokens_used, metrics_acc, ctx, root_ctx). `platform_layer/resume/service.py` present. (progress.md Day-0 Prong 1)
- [x] **Prong 2 (content — the critical ones)**: confirmed — (a) `_run_turns` carries the tool loop → `_cat9_tool_check` → `_cat9_hitl_branch` deferred-pause checkpoint (multi-pause reachable from resume); (b) `_resume_continuation` has exactly ONE caller (`resume()` @1990) → safe to delete; (c) **resume-path loop is fully wired** — `ResumeService._default_build_loop` → `build_real_llm_handler(...)` (same builder as chat, zero divergence; saved the 1st checkpoint → saves the 2nd → multi-pause end-to-end with NO ResumeService change). (progress.md Day-0 Prong 2)
- [x] **Prong 3 (schema)**: N/A — no DB / migration / ORM change this sprint (progress.md Day-0)
- [x] **Baseline capture**: pre-sprint baseline = main `dc25dbf5` (57.89 merged): re-confirm exact pytest/mypy/run_all/Vitest numbers Day-1 before editing
- [x] Catalogue D-DAY0-1..N drift findings in progress.md; **go/no-go = GO** (Option (b) locked; LOOP-span-around-`_run_turns` (Option Y) chosen to minimize 57.88 early-return test churn)

### 0.2 Branch
- [x] Branch `feature/sprint-57-90-resume-reentrancy-slice-2` from `main` (`dc25dbf5`)
- [x] plan + checklist + progress committed (Day-0 commit `17103640`)

---

## Day 1 — Rewire resume() + delete _resume_continuation (US-1/US-2/US-4)

### 1.1 Rewire resume() to drive _run_turns
- [x] **Replace the `_resume_continuation` call with a LOOP-span `_run_turns` drive**
  - fresh `metrics_acc = LoopMetricsAccumulator()` + `start_span(LOOP) as root_ctx` (mirror run(): `_root_ctx_t0` + `SpanStarted(LOOP)` in `try` + `SpanEnded(LOOP)` in `finally`); inside: `async for ev in self._run_turns(session_id, messages, turn_count, tokens_used, metrics_acc, ctx, root_ctx): yield ev`
  - DoD met: resume drives `_run_turns`; the pending-tool exec + approval bridge above byte-identical
  - Verify: grep — only docstring mention of `_resume_continuation` remains; `_run_turns` driven from resume()
- [x] **US-4: pending tool exec stays OUTSIDE `_run_turns` (no re-escalation)**
  - DoD met: pending tool executed once (raw) + observation appended BEFORE the `_run_turns` drive; multi-pause test proves the 1st tool exec'd once + a 2nd tool pauses (no re-escalation of the 1st)
- [x] **mypy clean on the rewired resume()** — `mypy src/agent_harness/orchestrator_loop/loop.py` = Success; `mypy src/` 0/346
  - Also updated resume() docstring (stale Karpathy §3 — was "does NOT re-enter run()'s body") + file-header MHist (1-line E501-safe)

### 1.2 Delete _resume_continuation (US-2)
- [x] **DELETE `_resume_continuation`** — method removed; grep shows zero CODE references (only the explanatory docstring mention in resume() + a stale .pyc)
  - Verify: `grep -rn "_resume_continuation" src tests` → docstring line only
- [x] **No orphan imports** — `flake8 loop.py` clean (F401 none); all symbols the deleted copy used are still used by `_run_turns` (verbatim run() body)

---

## Day 2 — Tests: convert 57.88 + multi-pause (US-3)

### 2.1 Convert 57.88 continuation assertions (Never-Delete)
- [x] **`test_loop_pause_resume.py` — approve-then-continue locks in the new path**
  - Outcome: the existing 8 tests PASS UNCHANGED (they use contains-style assertions; the new spans/checkpoints are additive — verified the new path IS exercised: `_build_resume_loop` wires no checkpointer so `_emit_state_checkpoint` no-ops, but resume now drives `_run_turns`). ADDED a LOOP-span assertion to `test_resume_approved_executes_tool_and_continues` to LOCK IN that resume drives `_run_turns` (the deleted copy emitted no span). Zero tests deleted. (Karpathy §3: did not force-rewrite passing tests; added the one meaningful lock-in assertion.)
  - Verify: `pytest test_loop_pause_resume.py -q` → 9 passed
- [x] **`test_chat_pause_resume_e2e.py` (5 integration)** — pass unchanged within the full suite (contains-style; resumed path now richer but additive); converted-not-needed (no assertion broke)
  - Verify: green within full `pytest -q` (2232)

### 2.2 Multi-pause unit test (US-3)
- [x] **NEW `test_resume_continuation_can_pause_again`** — green
  - DoD met: resume → 1st pending tool (tc-1) exec'd once → continuation's 1st LLM turn requests tc-2 (approval-required) → ESCALATE → deferred pause → `LoopCompleted(awaiting_approval)` + NEW `pending_approval` checkpoint (tc-2) + `ApprovalRequested` re-emitted; tc-2 NOT executed. Proves multi-pause-per-run (impossible with the deleted copy).
  - NEW builder `_build_resume_loop_multipause` (wires EscalateGuardrail + hitl_deferred + checkpointer/reducer)
- [x] **Span-tree + event-schema guards green** — `run_all` 10/10 (incl. `check_event_schema_sync` + AP-1 accepts resume driving `_run_turns`)

---

## Day 3 — Full regression + drive-through (US-5) + CHANGE-057

### 3.1 Full gate sweep
- [x] **Full backend pytest green (NET delta documented)** — **2232 passed / 4 skipped** (57.89 baseline 2231 → +1 = the NEW multi-pause test; NET delta = +1, documented, no test deleted)
  - Verify: `python -m pytest -q` → 2232 passed
- [x] **mypy 0 + run_all 10/10 + format chain** — mypy `src/` 0/346; run_all 10/10 (AP-1 accepts resume driving `_run_turns`; LLM SDK leak 0; AP-8 green; event-schema sync); black/isort/flake8 clean on changed files

### 3.2 Drive-through (US-5 — resume is user-facing) — **PASS**
- [x] **Clean backend restart (Risk Class E)** — `dev.py restart backend` killed stale PID 19056 → fresh PID 54916 (committed code); frontend node :3007 untouched; real Azure gpt-5.2 from repo-root `.env`
- [x] **Drove multi-pause through the real UI + real backend + real Azure gpt-5.2** — PASS
  - dan@acme.com admin / acme-prod / chat-v2 real_llm mode. Prompt induced two sequential echo_tool calls. Observed: turn 2 echo `alpha` → **pause 1** (approval a3022c6a) → approve → executed → turn 4 echo `beta` → **pause 2** (NEW approval e318b15c) → approve → executed → turn 6 **end_turn** answer rendered. Loop visualizer showed real LOOP/TURN/LLM_CALL spans + state_checkpointed v1/v2. The 2nd pause checkpoint persisted + the 2nd `/resume` loaded it (ResumeService DESC) → the multi-pause the deleted copy made impossible.
  - Evidence: `artifacts/sprint-57-90-multipause-drivethrough.png` + observed-vs-intended table in progress.md Day 3.
- [x] **No frontend fix needed** — chat-v2 surfaced the 2nd HITLTurn (new approval region + its own Approve) without change; `useLoopEventStream`/`chatStore`/`HITLTurn` re-trigger on a repeated pause as-is.

### 3.3 CHANGE-057 + design-note close
- [x] `claudedocs/4-changes/feature-changes/CHANGE-057-resume-drives-shared-loop-multi-pause.md` written
- [x] `19-pause-resume-design.md §5` — `AD-Resume-Continuation-Fidelity` marked ✅ CLOSED (Slice 1+2)

---

## Day 4 — Closeout

### 4.1 Closeout
- [x] Full validation (parent re-verified): pytest **2232** (+1) / mypy 0/346 / run_all 10/10 / pause-resume 9 + multi-pause green / **drive-through PASS** (screenshot + observed-vs-intended table)
- [x] progress.md (Day 0-4) + retrospective.md (Q1-Q7)
- [x] Calibration: `backend-core-loop-refactor` 0.55 (2nd data point, caveated — behavior-change shape) + `agent_factor` 1.0 (parent-direct); recorded `calibration-log.md §3`; carryover (Slice 3 / subagent child-loop / 57.88 ADs) → next-phase-candidates.md
- [x] MEMORY.md pointer + `project_phase57_90_resume_reentrancy_slice_2.md` subfile + CLAUDE.md lean (Current Sprint row + Last Updated) + CHANGE-057 + `19-pause-resume-design.md §5` CLOSED
- [ ] commit (Day 0-N) + push + PR — closeout commit pending; **push + PR pending user authorization**
