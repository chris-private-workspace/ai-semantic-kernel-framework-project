# Sprint 57.90 Progress — run() Re-entrancy Refactor Slice 2 (rewire resume + delete copy + multi-pause + drive-through)

**Sprint**: 57.90 / **Branch**: `feature/sprint-57-90-resume-reentrancy-slice-2` (from `main` `dc25dbf5`)
**Plan**: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-90-plan.md`
**Type**: CHANGE (Cat 1 behavior change — resume drives shared `_run_turns`) → CHANGE-057; closes `AD-Resume-Continuation-Fidelity` (Slice 1+2).

---

## Day 0 — Plan-vs-Repo Verify + Branch (2026-06-08)

### Branch
- `feature/sprint-57-90-resume-reentrancy-slice-2` cut from `main` `dc25dbf5` (57.89 Slice 1 merged, PR #262).

### Three-prong verify

**Prong 1 (path)** — method map confirmed in `backend/src/agent_harness/orchestrator_loop/loop.py`:
- `_handle_tool_error` @396 · `_should_retry_tool_error` @459 · `_audit_log_safe` @512 · `_cat9_input_check` @544 · `_cat9_tool_check` @597 · `_cat9_hitl_branch` @679 · `_cat9_output_check` @888 · `run` @961 · `_run_turns` @1055 · `resume` @1847 · `_resume_continuation` @1998 · `_emit_state_checkpoint` @2147 · `_tool_result_to_text` @2226.
- `run()` delegates @1036: `async for ev in self._run_turns(session_id, messages, turn_count, tokens_used, metrics_acc, ctx, root_ctx)` inside the LOOP span `as root_ctx` (@1003) with `SpanStarted`/`SpanEnded` bracket.
- `resume()` (1847-1996) currently: build state locals + `LoopStarted` → read `pending_approval` (absent → ERROR) → `get_decision` (None → ERROR) → `ApprovalReceived` → reject → `GuardrailTriggered(block)` + `LoopCompleted(GUARDRAIL_BLOCKED)` → APPROVED → exec pending tool (raw) + append observation → `_resume_continuation(messages, turn_count, tokens_used, ctx)` (@1990).
- `platform_layer/resume/service.py` present (`_default_build_loop` @94, `resume_session` @144).

**Prong 2 (content — the critical ones)**:
- **(a) multi-pause reachable from resume** ✅ — `_run_turns`'s tool loop calls `_cat9_tool_check` (@597) → `_cat9_hitl_branch` (@679), whose deferred branch emits `_emit_state_checkpoint(..., pending_approval=...)` (@813-820) + `LoopCompleted(AWAITING_APPROVAL)` + `return`. The post-LLM (@1446) + post-tool (@1825) checkpoints are inside `_run_turns`, confirming the full tool loop + checkpoint machinery moved with the body in Slice 1. So once `resume()` drives `_run_turns`, a 2nd ESCALATE pauses again — no new code.
- **(b) `_resume_continuation` has exactly ONE caller** ✅ — grep `_resume_continuation` in `backend/src` → only `resume()` call @1990 + the def @1998. Safe to delete after the rewire.
- **(c) resume-path loop is fully wired (the key multi-pause risk) — RESOLVED** ✅ — `ResumeService._default_build_loop` (`service.py:94`) builds via `build_real_llm_handler(db, session_id, tenant_id, user_id, hitl_manager)` — the SAME builder the chat path uses (the docstring states "byte-for-byte the same wiring as the original chat loop — no divergence"). Since the ORIGINAL chat loop saved the 1st `hitl_pause` checkpoint, `build_real_llm_handler` already wires `reducer`/`checkpointer`/`tenant_id` → the resumed `_run_turns`'s 2nd pause checkpoint saves the same way. `ResumeService.resume_session` already loads the LATEST snapshot (`ORDER BY version DESC LIMIT 1`), so a 2nd `/resume` picks up the 2nd pause. **Multi-pause works end-to-end through `POST /chat/{id}/resume` with NO ResumeService change.** (Day-1 re-grep `build_real_llm_handler` to re-confirm the checkpointer/reducer/tenant_id wiring; the NEW unit test + drive-through are the proof.)

**Prong 3 (schema)**: N/A — no DB table / migration / ORM change this sprint.

### Drift findings
- **D-DAY0-1** — Finding: the deferred-pause checkpoint lives in `_cat9_hitl_branch` (@813), reached via `_cat9_tool_check` (@597) from `_run_turns`'s tool loop — NOT directly in `_run_turns`'s lexical body. Implication: multi-pause is reachable as long as resume drives `_run_turns` (which calls the per-tool path); no extra wiring. No scope change.
- **D-DAY0-2** — Finding: `resume()` opens NO LOOP span today (yields `LoopStarted` then events on `ctx`); `_run_turns` REQUIRES `root_ctx` (a LOOP span ctx) for TURN-span nesting + `metrics_acc`. Implication: the rewire must construct a fresh `metrics_acc` + open a `root_ctx` LOOP span in resume (mirror run()'s `start_span`/`SpanStarted`/`SpanEnded`). Decision: **Option Y** — bracket only the `_run_turns` drive in the LOOP span (after the pending-tool exec), leaving the approval-bridge + early-return paths byte-identical → minimizes 57.88 test churn (only approve-then-continue assertions change). Recorded in plan §3.0/§3.1.
- **D-DAY0-3** — Finding: `_resume_continuation` constructs its own `build_state = LoopState(...)` for the PromptBuilder path + uses `should_terminate_*` / `classify_output` / `ChatRequest` / `CacheBreakpoint`. Implication: after deleting it, re-check those imports are still used by `_run_turns` (they are — `_run_turns` is the verbatim run() body that also uses them) → no orphan import expected, but flake8 F401 confirms on Day-1.

### Go/No-Go
**GO** — locked decisions: §6.1 option (b) (pending tool exec'd outside `_run_turns`, no re-escalation) + Option Y (LOOP span around the `_run_turns` continuation only). The key multi-pause risk (2nd checkpoint not saving) is resolved at Day-0: the resume-path loop shares the chat builder, which already checkpoints. No scope shift; behavior-change slice with the 57.88 test conversion + a NEW multi-pause test + a drive-through as acceptance.

### Calibration intent
- Scope class `backend-core-loop-refactor` 0.55 (2nd data point, CAVEATED — behavior change + drive-through, distinct shape from Slice 1's pure extraction). `agent_factor` 1.0 (parent-direct — 主流量 loop surgery). Bottom-up ~10 hr → ~5.5 hr commit (mult 0.55). Does NOT extend the AgentDelegated-WallClock streak.

---

## Day 1-2 — Rewire + delete + tests (2026-06-08)

### Code (`loop.py`)
- **resume() rewire** — replaced the `_resume_continuation(...)` call with a fresh `metrics_acc = LoopMetricsAccumulator()` + a `root_ctx` LOOP span (`start_span(name="agent_loop.run", category=ORCHESTRATOR, attributes={"span_type":"LOOP"})` + `SpanStarted(LOOP)` in `try` + `SpanEnded(LOOP)` loop-measured `duration_ms` in `finally`) driving `async for ev in self._run_turns(session_id, messages, turn_count, tokens_used, metrics_acc, ctx, root_ctx)`. The pending-tool exec + approval bridge ABOVE are byte-identical (the pre-approved tool is still exec'd once outside `_run_turns` → no re-escalation, locked §6.1 (b)).
- **DELETE `_resume_continuation`** — the 148-line reduced copy removed; grep shows zero code callers (only the explanatory mention in resume()'s docstring).
- **Stale docstring fix (Karpathy §3)** — resume()'s docstring previously said the continuation "intentionally does NOT re-enter run()'s body"; rewritten to describe the Slice-2 shared-`_run_turns` drive + the multi-pause gain + the deleted copy.
- **File-header MHist** — 1-line E501-safe entry (`Sprint 57.90 Slice 2 — resume() drives shared _run_turns; delete the reduced copy`).

### Tests (`test_loop_pause_resume.py`)
- **+1 NEW `test_resume_continuation_can_pause_again`** (multi-pause) + NEW builder `_build_resume_loop_multipause` (wires EscalateGuardrail + hitl_deferred + checkpointer/reducer). Proves: 1st pending tool (tc-1) exec'd once → continuation requests tc-2 (approval-required) → ESCALATE → deferred pause → `LoopCompleted(awaiting_approval)` + NEW `pending_approval` checkpoint (tc-2) + `ApprovalRequested` re-emitted; tc-2 NOT executed. Impossible with the deleted reduced copy → the core Slice-2 close.
- **+1 lock-in assertion** in `test_resume_approved_executes_tool_and_continues`: a `SpanStarted(span_type="LOOP")` is present → proves resume drives `_run_turns` (the deleted copy emitted no span). The other 7 pause-resume tests pass UNCHANGED (contains-style assertions; the new spans/checkpoints are additive; the new path IS exercised — `_build_resume_loop` wires no checkpointer so `_emit_state_checkpoint` no-ops, but `_run_turns` still runs). Karpathy §3: did not force-rewrite passing tests.

### Gate (Day 1-2)
- pytest **2232 passed / 4 skipped** (57.89 baseline 2231 → **+1** = the new multi-pause test; NET delta documented, no test deleted).
- mypy `src/ --strict` **0/346** (CI gate; tests not mypy-gated — the new `# type: ignore[arg-type]` mirrors the existing `_build_loop` pattern, Risk Class B cross-context unused-ignore in isolation only).
- run_all **10/10** (`check_ap1_pipeline_disguise` OK = resume driving `_run_turns` not flagged; `check_event_schema_sync` OK; `check_llm_sdk_leak` OK; AP-8 OK).
- black/isort/flake8 clean on `loop.py` + `test_loop_pause_resume.py`.

### Drift / decisions confirmed in code
- **D-DAY0-2 (Option Y) applied** — LOOP span brackets only the `_run_turns` continuation; the approval-bridge + early-return paths byte-identical → the 7 unchanged 57.88 tests confirm zero churn on those paths.
- **D-DAY0-3 (orphan import) resolved** — flake8 F401 clean; the deleted copy's symbols are all still used by `_run_turns`.
- Multi-pause checkpoint wiring (the key Day-0 risk) **proven by the new test** + Day-0's `build_real_llm_handler` analysis (`handler.py:274` `reducer, checkpointer = make_chat_state_deps(db, session_id, tenant_id)` — the resume path shares this builder).

### Remaining (Day 3+)
- Drive-through (US-5, user-facing) — real UI + real backend + real Azure: echo→pause→approve→echo→2nd pause→approve→answer (+ any frontend fix for a 2nd HITLTurn).
- CHANGE-057 + `19-pause-resume-design.md §5` CLOSE + retrospective + calibration + MEMORY + CLAUDE lean.
