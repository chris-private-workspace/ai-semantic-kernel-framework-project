# Sprint 57.88 — Checklist (ESCALATE → Checkpoint → Resume — durable HITL pause-resume; 地基 A keystone spike)

**Plan**: [`sprint-57-88-plan.md`](./sprint-57-88-plan.md)
**Created**: 2026-06-08
**Status**: Draft (scope pending user approval; code gated on approval + Day-0 GO)

> Rule: only `[ ]` → `[x]`; never delete unchecked items; defer with `🚧 + reason`.
> SPIKE → Day-4 design-note extract + 8-point gate (`19-pause-resume-design.md`). Scope: ONE deterministic tool-ESCALATE → checkpoint → release → approve → resume → continue, driven through chat-v2 UI (real backend + real LLM).

---

## Day 0 — Plan-vs-Repo Verify + Branch

### 0.1 Three-prong Day-0 verify
- [x] **Prong 1 (path)**: all anchors confirmed — `_cat9_hitl_branch` loop.py:552-697; `_abc.py:63-71` resume; `checkpointer.py:118-181`; events.py:382/388; hitl.py:55/69; HITLManager; `manager.py` DefaultHITLManager; governance decide; chat router:138 + `_stream_loop_events`; `state.py:75` StateSnapshot
- [x] **Prong 2 (content)**: shapes captured (progress.md Day-0) — `_cat9_hitl_branch(*, tc, ctx, guardrail_reason)`; ApprovalRequested{approval_request_id, risk_level}; ApprovalReceived{approval_request_id, decision}; **NO non-blocking get_decision** (D-DAY0-1, must add); stream ends on `LoopCompleted` (D-DAY0-3 → awaiting_approval closes cleanly); decisions in `approvals` table (status!=PENDING)
- [x] **Prong 3 (schema)**: `state_snapshots.state_data` JSONB holds `pending_approval` → **免 migration** (D-DAY0-2); tenant_id+RLS ✓; head `0027`
- [x] **Doc-location**: 17.md contract section; `19-pause-resume-design.md` free (18-handoff→20-iam; 19 skipped)
- [x] Catalogued D-DAY0-1..8 in progress.md; **go/no-go = GO**

### 0.2 Branch + decisions
- [x] Branch `feature/sprint-57-88-pause-resume` from `41f1ed05`; plan+checklist (`65ab34fc`); Day-0 progress
- [x] Locked: deferred = chat path only (blocking retained); resume trigger = NEW `POST /chat/{id}/resume`; checkpoint enrich in JSONB (**no migration** per D-DAY0-2); reuse `request_approval`; enum in `termination.py` not events.py (D-DAY0-7); **Agent-delegated: yes**

---

## Day 1 — Backend core (Stage 1)

### 1.1 Deferred-approval pause (US-1)
- [x] `TerminationReason.AWAITING_APPROVAL="awaiting_approval"` — in `termination.py:63` (D-DAY0-7: NOT events.py; parallel to 57.68 HANDOFF)
- [x] `loop.py` `_cat9_hitl_branch` deferred branch: `request_approval`+`ApprovalRequested` (reused) → `_emit_state_checkpoint(pending_approval)` → `LoopCompleted("awaiting_approval")`; NO `wait_for_decision` in deferred; blocking path untouched; main loop `cat9_terminated→return` (loop.py:1366) skips tool
- [x] discriminator = `hitl_deferred: bool = False` ctor flag (gated on +checkpointer+reducer+session_id, else fall back blocking)

### 1.2 Resumable checkpoint (US-2)
- [x] pending_approval `{tool_call{name,arguments,tool_call_id}, approval_request_id, turn}` in `DurableState.metadata` (D-DAY0-2)
- [x] round-trips via existing `_serialize/_deserialize_state_for_db` JSONB — **NO migration**
- [x] unit: checkpoint enrich/restore covered in `test_loop_pause_resume.py`

### 1.3 `resume()` implementation (US-3)
- [x] `AgentLoopImpl.resume(*, state, trace_context)`: read pending_approval → `get_decision` (non-blocking, NEW) → APPROVED: exec pending tool + append observation + `_resume_continuation`→end_turn; REJECTED→block+LoopCompleted; undecided→fail-closed. ⚠️ `_resume_continuation` = reduced loop copy (no Cat 8/9/4) — design-note open question (§9)
- [x] `HITLManager.get_decision` (ABC + DefaultHITLManager, shared `_read_decision_if_decided`; wait_for_decision refactored, 0 behavior change)
- [x] unit: `resume()` approved + rejected + undecided paths

### 1.4 Backend green (Stage 1) — parent re-verified (gates run by parent, not trusted from agent report)
- [x] `mypy src/` 0/344; `run_all` 10/10 (incl. llm_sdk_leak, AP-1, AP-8); 56 passed (8 new pause-resume + loop regression + escalation e2e); zero regression

---

## Day 2 — Resume endpoint + platform service + integration tests (Stage 2)

### 2.1 Resume orchestration (US-4)
- [x] `platform_layer/resume/service.py` `ResumeService.resume_session(...)`: latest `hitl_pause` snapshot for (session,tenant) → cross-tenant/no-row → None → 404; `DBCheckpointer.load` + messages from metadata; build loop via injected `build_loop` (default real chat builder, zero divergence). Decision B: messages self-contained in checkpoint (no messages table)
- [x] `POST /chat/{session_id}/resume` — `Depends(get_current_tenant/get_current_user_id/get_db_session/get_resume_service)` mirror chat auth; None→404; `StreamingResponse(_stream_resume_events)` reuses `serialize_loop_event`. Decision A: `hitl_deferred=(hitl_manager is not None)` wired in handler.py

### 2.2 Integration tests (US-5)
- [x] `test_chat_pause_resume_e2e.py` (5, real Postgres): pause→`awaiting_approval`+checkpoint(pending_approval+resume_messages); governance decide→APPROVED→resume→tool exec+end_turn; REJECTED→block+no exec
- [x] **multi-tenant**: cross-tenant resume → 404 (no leak, tool not run); no-paused → 404
- [x] (ResumeService paths covered by the 5 e2e tests; rejection/404 paths asserted there rather than separate unit file)

### 2.3 Backend sweep — parent re-verified
- [x] mypy 0/346; run_all 10/10; 71 passed (pause-resume e2e + chat_e2e + escalation + loop unit); Risk Class C handled (shared db_session, commit→flush, endpoint get_db_session = test session). Endpoint `Depends` wiring parent-read-verified (coroutine test bypasses HTTP transport)

---

## Day 3 — Frontend pause/resume wiring (Stage 3)

### 3.1 Paused state (US-5)
- [x] chat-v2 store/components handle `LoopCompleted.stop_reason=="awaiting_approval"` → render "Awaiting approval (paused)" + `ApprovalCard`/`HITLTurn`; mark stream closed
  - Done: `loop_end(awaiting_approval)` already sets agent turn `waiting=true` ("awaiting approval" indicator) + `stopReason`; `approval_requested` already pushes `HITLTurn`; `status="completed"` reflects the genuinely-closed SSE stream. `loop_start` now clears the stale `waiting` indicator on resume (Drive-Through honesty). No new `paused` status (YAGNI).
### 3.2 Approve → resume (US-5)
- [x] ApprovalCard approve → `POST /governance/approvals/{request_id}/decide` → `POST /chat/{session_id}/resume` → consume new SSE stream → render continuation + final answer (reuse `chatStore` SSE consumer)
  - Done: `chatService.resumeChat` (POST `/chat/{id}/resume`, shared `consumeSSEStream`); `useLoopEventStream.resume()`; `HITLTurn` Approve → `decide()` → optimistic merge → `resume()` **guarded on `stopReason==="awaiting_approval"`** (scopes to deferred-pause flow; protects legacy blocking-HITL e2e). Continuation `tool_call_result` updates the pending escalated ToolBlock by id → no mergeEvent change.
### 3.3 Frontend green
- [x] `npm run lint && npm run build` (NO `--silent`); `tsc` 0; Vitest green (+ new tests); `check:mockup-fidelity` ✓ (oklch baseline unchanged)
  - Parent re-verified: lint exit 0 / tsc exit 0 / build exit 0 / Vitest **772 passed (134 files)** incl. 2 new test files (6 tests) / mockup-fidelity ✓ (oklch baseline 53 unchanged)

---

## Day 4 — Drive-through + Design note (8-point gate) + Closeout

### 4.1 Drive-through (US-5 — hard constraint)
- [x] `dev.py start` (real backend) + `real_llm` + chat-v2 in browser (Playwright MCP or manual): message → paused state + stream closed → approve → continuation + final answer rendered
  - PASSED after a deterministic ESCALATE trigger (Day-4 part 1) + 2 FK/wiring fixes (Day-4 part 2). Drive-through caught 3 defects gates were green on (Risk Class E stale worker + router session-commit FK + ResumeService hitl_manager). "echo hello world" → ESCALATE → pause (HITL card, answer NOT rendered, loop_end awaiting_approval) → Approve → decide → resume → echo_tool pending→success → answer "hello world" rendered → end_turn.
- [x] Walk every control (approve button real? resume fires? continuation renders? labels real?) — no Potemkin
  - Approve fires decide+resume; continuation renders; HITL "Decision: APPROVED"; labels real; observed == intended.
- [x] Screenshots + "observed vs intended" diff → progress.md / CHANGE-056
  - `artifacts/sprint-57-88-drivethrough-1-paused.png` + `-2-resumed-answer.png`; full observed-vs-intended in progress.md Day-4 part 2.

### 4.2 Design note extract (US-5)
- [ ] `19-pause-resume-design.md` (NEW) — 8-point gate ALL (1 headers↔stories / 2 file:line / 3 decision matrix [deferred vs blocking; resume-endpoint vs governance-inline; JSONB-enrich vs migration] / 4 verify command / 5 fixture ref / 6 verified-vs-deferred / 7 rollback / 8 17.md cross-ref); verified-ratio ≥95%
- [ ] retrospective.md §Design Note Extract (8-point self-check)

### 4.3 Closeout
- [ ] Full validation (parent re-verified): pytest green / mypy src 0 / run_all 10/10 / Vitest / migration up+down (if any) / drive-through PASS
- [ ] 17.md `resume()`+checkpoint+`AWAITING_APPROVAL`; `CHANGE-056`
- [ ] progress.md (Day 0-4) + retrospective.md (Q1-Q7)
- [ ] Calibration: `loop-lifecycle-spike` 0.55 (NEW, 1 pt, caveated) + `agent_factor` 0.65; record `calibration-log.md §3`; carryover (generalized pause points / 地基 B / subagent / session-list paused badge) → next-phase-candidates.md
- [ ] MEMORY.md pointer + `project_phase57_88_pause_resume.md` subfile + CLAUDE.md lean
- [ ] commit (Day 0-4) + push + PR — user-authorized
