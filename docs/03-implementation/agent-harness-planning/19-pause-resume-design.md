# 19 — Durable HITL Pause-Resume (Spike Design Note)

**Purpose**: Extract the verified invariants of the durable HITL pause-resume slice (Sprint 57.88) — the 地基 A keystone: a chat-path tool ESCALATE checkpoints the loop, releases the SSE connection, and resumes hours/days later via a NEW `resume()` after a human approves.
**Category / Scope**: Cat 1 (Orchestrator Loop — deferred ESCALATE branch + `resume()`) + Cat 7 (State Mgmt — checkpoint `pending_approval` enrichment) + Cat 9 (HITL — deferred mode + `get_decision`) + Cat 12 (`awaiting_approval` stop_reason) + platform_layer.resume + chat router/SSE + chat-v2 frontend / Phase 57.88
**Created**: 2026-06-08
**Status**: Active (extracted from shipped + tested + drive-through-verified implementation)
**Closes**: 地基 A keystone slice (durable pause-resume vertical line)

> **Modification History**
> - 2026-06-09: Sprint 57.93 — §5 output-guardrail ESCALATE pre-delivery pause shipped (CHANGE-060)
> - 2026-06-08: Sprint 57.92 — §5 between-turns guardrail ESCALATE pause shipped (leg 2, CHANGE-059)
> - 2026-06-08: Sprint 57.91 — §5 input-guardrail ESCALATE pause + `_emit_deferred_pause` shipped (leg 1, CHANGE-058)
> - 2026-06-08: Initial creation — extracted from Sprint 57.88 shipped impl (8-point gate self-check in retrospective)

---

## 1. Spike Summary (what shipped, as wired)

The blocking `wait_for_decision` (which held the SSE connection open until a human decided — unusable when approval takes hours/days) is replaced, **on the chat path only**, by a durable pause-resume.

- **US-1 (deferred pause)**: a chat-path tool ESCALATE in `hitl_deferred` mode checkpoints the loop + emits `ApprovalRequested` + terminates with `stop_reason="awaiting_approval"` (NO blocking wait) → the SSE connection is released. `loop.py` `_cat9_hitl_branch` deferred branch (`loop.py:798-833`); `TerminationReason.AWAITING_APPROVAL` (`termination.py:63`).
- **US-2 (resumable checkpoint)**: the pause checkpoint self-contains `pending_approval` (pending tool call + approval_request_id + turn) AND `resume_messages` (the conversation buffer) in the existing `state_snapshots` JSONB metadata — **no migration**. `_emit_state_checkpoint` (`loop.py:2141-2185`).
- **US-3 (`resume()`)**: the pure-abstract `resume()` stub is implemented — read `pending_approval` → non-blocking `HITLManager.get_decision` → APPROVED: execute the pending tool + continue to `end_turn`; REJECTED: block; undecided: fail-closed ERROR. `AgentLoopImpl.resume` (`loop.py:1841-1990`).
- **US-4 (resume endpoint)**: NEW `POST /api/v1/chat/{session_id}/resume` drives `resume()` on a fresh SSE stream via a thin `ResumeService` (load checkpoint + tenant guard + rebuild loop). `router.py:780` + `platform_layer/resume/service.py`.
- **US-5 (drive-through)**: proven on chat-v2 UI with real backend + real Azure gpt-5.2 — `echo hello world` → pause (HITL card, answer NOT rendered) → Approve → resume → answer rendered. Screenshots in `sprint-57-88/artifacts/`.

The existing governance decide endpoint (`POST /governance/approvals/{id}/decide`), `ApprovalRequested`/`ApprovalReceived` events, and frontend `ApprovalCard`/`HITLTurn` are reused as-is.

> **Sprint 57.91 (Slice 3 leg 1, CHANGE-058)** generalized the above: the durable-pause tail (US-1/US-2) was extracted into `_emit_deferred_pause(...)` decoupled from a tool call, and `pending_approval` gained a `"kind"` discriminator (`"tool"` carries a tool_call; `"input"` carries none). The first non-tool pause point — an input-guardrail ESCALATE — pauses before any LLM call (input-kind) and `resume()` continues to the first LLM turn with no tool exec. The 57.88 events / endpoint / frontend are reused unchanged (the HITL card renders generically — an input pause shows `tool: —`). See §5 + CHANGE-058.

---

## 2. Decision Matrix

| # | Decision | Options considered | Chosen | Why (rejected the rest) |
|---|----------|--------------------|--------|--------------------------|
| D1 | Pause mechanism | (a) deferred checkpoint + terminate / (b) keep blocking `wait_for_decision` / (c) background task polling | **(a)** (`loop.py:798-833`) | (b) holds the SSE connection for the hours/days the user's real approval takes (the core conflict, plan §0 D2); (c) keeps a server task alive per pending approval (unbounded). (a) releases all resources, re-derives on resume. The blocking path is RETAINED additively for synchronous callers. |
| D2 | Resume trigger | (a) NEW `POST /chat/{id}/resume` / (b) extend the governance decide endpoint to auto-resume / (c) server-side auto-resume on decision | **(a)** (`router.py:780`) | (b) couples governance (a generic approval surface) to chat-loop resumption; (c) needs a server-side decision watcher (the thing (a)+deferred avoids). (a) keeps the client as the orchestrator: decide, then resume — mirrors chat auth deps exactly. |
| D3 | Checkpoint payload home | (a) enrich existing `state_snapshots` JSONB / (b) new migration `0028` column / (c) new `paused_loops` table | **(a)** (`loop.py:2183-2185`) | Day-0 Prong-3 confirmed `state_snapshots.state_data` is JSONB and round-trips via `_serialize/_deserialize_state_for_db` → (b)/(c) add schema for data the JSONB already holds. No migration. |
| D4 | Messages at resume | (a) self-contain in checkpoint `resume_messages` / (b) read from a `messages` DB table / (c) re-derive from event log | **(a)** (`loop.py:2185` + `service.py:189`) | **No `messages` table exists in this codebase** (Day-2 grounding). (a) is the pragmatic spike path; written ONLY on the pause checkpoint (normal post-llm/post-tool checkpoints stay empty → no bloat). Production should use a messages table / bounded summary (§5 open question). |
| D5 | ESCALATE trigger for the drive-through | (a) real `ToolGuardrail` + registry-derived `CapabilityMatrix` / (b) env-gated fake escalation rule / (c) defer the drive-through | **(a)** (`handler.py:286-300`) | User chose the real security layer over a fake (AskUserQuestion). (b) is a Potemkin trigger; (c) skips the hard-constraint gate. (a) derives the matrix from `registry.list()` (every exposed tool → PASS rule, `echo_tool` → `requires_approval`) — avoids `ToolGuardrail`'s unknown-tool→BLOCK default that a static echo-only matrix would hit. |
| D6 | `resume()` re-entry body | (a) reduced `_resume_continuation` copy / (b) refactor `run()` into a shared re-enterable loop / (c) recursion | **(a)** (`loop.py:1992`) — **caveated** | (b) is the correct production shape but a large refactor (out of spike scope); (c) is hard to checkpoint. (a) is a real while-true (passes AP-1) through PromptBuilder (passes AP-8) honoring max_turns/token_budget, but deliberately omits run()'s Cat 8 retry / Cat 9 guardrail / Cat 4 compaction (§5 open question — the honest boundary). |

---

## 3. Verified Invariants (file:line + test)

| Invariant | Evidence | Verified by |
|-----------|----------|-------------|
| Deferred ESCALATE → `stop_reason="awaiting_approval"`, no blocking wait | `loop.py:798` (deferred gate) + `:833` (`TerminationReason.AWAITING_APPROVAL.value`) | `test_loop_pause_resume.py` (deferred-pause case) + drive-through `loop_end stop=awaiting_approval` |
| Blocking path preserved when not deferred | `loop.py:690` (two-mode branch); gated on `hitl_deferred + checkpointer + reducer + session_id` else falls back | `test_loop_pause_resume.py` (blocking regression) + `approval-card.spec.ts` green |
| Checkpoint carries `pending_approval` + `resume_messages` in JSONB, no migration | `loop.py:2183-2185` (`_emit_state_checkpoint`); round-trips via `_serialize/_deserialize_state_for_db` | `test_loop_pause_resume.py` (enrich/restore) + `test_chat_pause_resume_e2e.py` (checkpoint asserted) |
| Non-blocking `get_decision` reads decided `ApprovalDecision` (None if pending) | `hitl/_abc.py` + `manager.py` `get_decision` (shared `_read_decision_if_decided`; `wait_for_decision` refactored onto it, 0 behavior change) | `test_loop_pause_resume.py` (get_decision pending↔decided) |
| `resume()` APPROVED → exec pending tool → end_turn | `loop.py:1841` (resume) + `:1884` (read pending) + `:1984` (`_resume_continuation`) | `test_loop_pause_resume.py` (resume approved) + `test_chat_pause_resume_e2e.py` (tool exec + end_turn) + drive-through |
| `resume()` REJECTED → block, no tool exec; undecided → fail-closed ERROR | `loop.py:1884+` (decision branch) | `test_loop_pause_resume.py` (rejected + undecided) + `test_chat_pause_resume_e2e.py` (reject case) |
| Resume is tenant-scoped; cross-tenant / no-paused → 404 (no leak) | `service.py:168-181` (query filters `tenant_id`; None → 404) | `test_chat_pause_resume_e2e.py` (cross-tenant 404 + no-paused 404) |
| Resume loop = same wiring as chat loop (zero divergence) | `service.py:94-129` `_default_build_loop` → `build_real_llm_handler` (+ `get_service_factory().get_hitl_manager()`) | drive-through (resume read the decision the pause recorded) |
| Chat path opts into deferred + ESCALATE matrix | `handler.py:331` (`hitl_deferred=(hitl_manager is not None)`) + `:286-300` (registry-derived `ToolGuardrail`) | `test_chat_*_wiring` 44 passed + drive-through (echo_tool ESCALATE HIGH) |
| Frontend: approve → decide → resume, guarded on `stopReason==="awaiting_approval"` | `HITLTurn.tsx` (resume trigger + guard) + `chatService.ts` `resumeChat` + `useLoopEventStream.ts` `resume()` | `HITLTurn.resume.test.tsx` (3) + `chatStore.pauseResume.test.ts` (3) + drive-through |
| FK: chat session row committed before HITL approval INSERT | `router.py:279` (`await db.commit()` after `create_session`) | drive-through (the FK-violation defect this fixed) |

**Verification command** (backend): `cd backend && python -m pytest tests/unit/agent_harness/orchestrator_loop/test_loop_pause_resume.py tests/integration/api/test_chat_pause_resume_e2e.py -q` (8 unit + 5 integration). Full sweep: `python -m pytest` → 2229 passed / 4 skipped; `mypy src/` 0/346; `python scripts/lint/run_all.py` 10/10.
**Verification command** (frontend): `cd frontend && npx vitest run tests/unit/chat_v2/chatStore.pauseResume.test.ts tests/unit/chat_v2/HITLTurn.resume.test.tsx` (6). Full: `npx vitest run` → 772 passed / 134 files; `npm run lint` (no `--silent`) + `npm run build` + `npm run check:mockup-fidelity` (oklch baseline 53 unchanged).
**Drive-through** (the hard constraint): `python scripts/dev.py start` + a clean no-`--reload` uvicorn + chat-v2 (`:3007`) + real Azure gpt-5.2 (`mode=real_llm`, NOT echo/mock) → send `echo hello world` → pause → Approve → resume. Screenshots `sprint-57-88/artifacts/sprint-57-88-drivethrough-{1-paused,2-resumed-answer}.png`. Observed == intended (progress.md Day-4 part 2).

**Test fixtures**: `backend/tests/conftest.py` (`db_session` real docker Postgres, rolled back). `test_chat_pause_resume_e2e.py` drives the endpoint **coroutines directly** (not via TestClient HTTP) — shared asyncpg `db_session` is bound to the test loop; TestClient's portal loop → "Future attached to a different loop" (Risk Class C). It still exercises the REAL `resume_chat` + `decide_approval` + ResumeService + `loop.resume()` + SSE serializer; only the HTTP transport is bypassed (covered by the chat-v2 drive-through). The `Depends()` auth wiring was parent-read-verified. ESCALATE trigger needs no fixture (DEMO_SYSTEM_PROMPT forces `echo_tool` on "echo X").

---

## 4. Cross-Category Contracts

Registered in `17-cross-category-interfaces.md` (single-source):

- **§4.1 LoopEvent table** — `LoopCompleted` row notes the NEW `stop_reason="awaiting_approval"` terminal (parallel to Sprint 57.68 `handoff`); owner Cat 1.
- **§5.2 HITL interface** — `HITLManager.get_decision(request_id) -> ApprovalDecision | None` added to the ABC (non-blocking read; owner HITL Centralization §5).
- **§5.3 HITL rules** — deferred mode = checkpoint-`pending_approval` + `resume()` re-entry (additive to the blocking path); resume is the Reducer's "merge `ApprovalDecision` + resume" rule made durable across runs.

No NEW dataclass duplicated — `ApprovalRequest`/`ApprovalDecision`/`ApprovalRequested`/`ApprovalReceived`/`LoopCompleted` all reused. `ResumeService` is a platform_layer orchestrator (not an 11+1 category ABC); its contract lives in this note + the service docstring + CHANGE-056.

---

## 5. Open Invariants (Deferred — NOT verified this spike)

- **`AD-Resume-Continuation-Fidelity`** ✅ **CLOSED (Sprint 57.89 Slice 1 + 57.90 Slice 2)** — was: `_resume_continuation` is a SECOND, reduced copy of run()'s loop body that omits Cat 4/7/8/9/12 + cannot pause again (one-approval-per-run). Slice 1 (57.89) extracted run()'s per-turn body into the re-enterable `_run_turns(...)`; Slice 2 (57.90) pointed `resume()` at it and DELETED `_resume_continuation`. The resumed continuation now runs the SAME machinery as `run()` (Cat 4/7/8/9/12 + HANDOFF) and **multi-pause-per-run** works — proven by `test_resume_continuation_can_pause_again` + a real-UI drive-through (echo `alpha` → pause → approve → echo `beta` → 2nd pause → approve → end_turn). See CHANGE-057 + `run-loop-reentrancy-refactor-analysis-20260608.md`.
- **`AD-Resume-Checkpoint-Bloat`** (NEW) — `resume_messages` self-contains the full conversation buffer in the pause checkpoint JSONB (no `messages` table). Long conversations → large rows; long-horizon retention (days) assumes messages persist. Production: a `messages` table / bounded summary + checkpoint TTL.
- **`AD-Resume-Tenant-Capability-Policy`** (NEW) — the ESCALATE matrix is derived from the live `registry.list()` (every tool PASS except `echo_tool`). Production per-tenant `capability_matrix.yaml` policy (which tools require approval per tenant/role) is deferred.
- **`AD-Resume-Reject-Path`** (NEW) — reject is recorded via the governance decide endpoint but the client does NOT call `/resume` on reject (the checkpoint is left dangling, not GC'd). A reject-then-resume (to emit the block + clean the checkpoint) or a checkpoint reaper is deferred.
- **Generalized pause points** — PARTIALLY SHIPPED (Slice 3 legs 1+2 + output-guardrail leg):
  - **leg 1 — input-guardrail ESCALATE** (Sprint 57.91, CHANGE-058): the durable-pause tail was extracted into the generalized `_emit_deferred_pause(...)` primitive (decoupled from a tool call; `pending_approval` gains a `"kind"` discriminator — `"tool"` carries a tool_call resume() re-executes, `"input"`/`"between_turns"` carry none), and the FIRST new pause point — input-guardrail ESCALATE — was built on it: an input flagged ESCALATE pauses BEFORE any LLM call (input-kind, no tool), and `resume()` continues to the first LLM turn with no tool exec. Proven by 4 unit tests + a real-UI drive-through (`approval required: …` → pause `awaiting_approval` no LLM call → approve → "Paris").
  - **leg 2 — between-turns guardrail ESCALATE** (Sprint 57.92, CHANGE-059): a NEW `GuardrailType.BETWEEN_TURNS` + `check_between_turns`; a gate at the `_run_turns` loop TOP (after ≥1 completed turn, before the next LLM call) runs `_cat9_between_turns_check` on the just-completed turn's output → ESCALATE durably pauses BETWEEN turns (between_turns-kind, no tool_call) via `_cat9_between_turns_hitl_pause` + `_emit_deferred_pause`. `resume()` drives the shared `_run_turns` with `skip_between_turns_once=True` so the just-approved boundary does not re-escalate; the loop-top seam means resume continues by making the next turn's LLM call (never run) — no re-generation. Reachable via a real `BetweenTurnsKeywordGuardrail` + a non-escalate `note_tool` (echo_tool tool-escalates and can't reach a between-turns boundary). Proven by 4 unit tests + a real-UI drive-through (`note the word checkpoint` → turn 0 `note_tool` → pause `awaiting_approval` `tool: —` → approve → `end_turn` "checkpoint").
  - **output-guardrail leg — output-guardrail ESCALATE pre-delivery pause** (Sprint 57.93, CHANGE-060): reuses the EXISTING `GuardrailType.OUTPUT` + `check_output` (no new type). A conditional **pre-gate** (`_cat9_output_escalate_pause` + `_cat9_output_hitl_pause`) runs the OUTPUT chain in `_run_turns` right after `parse(...)`, BEFORE `yield LLMResponded` — gated on `is_final_answer` + the full deferred-HITL wiring so non-HITL / non-final turns are byte-unchanged (the per-response `_cat9_output_check` at the original site stays intact). On ESCALATE it pauses (output-kind, no tool_call) carrying the **held-answer snapshot** (`pending_approval.response_snapshot`: answer_text + tokens/provider/model). This is **pre-delivery gating** — the frontend renders the answer from the `llm_response` SSE event, so the pause MUST precede it; a pause at the per-response check (after `LLMResponded`) would be a Potemkin. `resume()`'s output kind is TERMINAL (it does NOT drive `_run_turns`): APPROVED → `_replay_approved_output` re-emits the held `LLMResponded` + `LoopCompleted(END_TURN)` from the snapshot (no LLM re-call); REJECTED → `GuardrailTriggered(output, block)` + `GUARDRAIL_BLOCKED`. Reachable via a real `OutputKeywordEscalationGuardrail` (priority=5, before the default Toxicity/SensitiveInfo) + a DEMO_SYSTEM_PROMPT line. Proven by 5 unit tests + a real-UI drive-through (withhold-then-deliver on approve / withhold-permanently on reject; the answer never renders before approval).
  - STILL DEFERRED (leg 3): **mid-thinking pause** (interrupt an in-flight streaming LLM call). The only remaining generalized-pause-point leg — the input / between-turns / output / tool surfaces are all shipped.
- **地基 B cognition phases / subagent child-loop / session-list paused badge + cross-device resume / approval notification (email/webhook)** — all deferred (plan §9); 地基 A's lifecycle骨架 feeds the subagent build (a distinct larger sprint).

---

## 6. Rollback

Additive + behind a discriminator. To revert: (1) `handler.py` set `hitl_deferred=False` (or drop the `ToolGuardrail` registration `:299-301`) → the chat path returns to the blocking `wait_for_decision`; (2) remove the `POST /chat/{id}/resume` endpoint + `get_resume_service` (`router.py:739-825`) + `platform_layer/resume/`; (3) `loop.py` `resume()` reverts to the abstract stub + drop the deferred branch in `_cat9_hitl_branch` + `_resume_continuation` + `_emit_state_checkpoint` `pending_approval` path + `messages_from_metadata` + `TerminationReason.AWAITING_APPROVAL`; (4) revert the frontend 4-file wiring (`chatService`/`useLoopEventStream`/`HITLTurn`/`chatStore`). **No migration / no schema change → no DB rollback.** The `router.py:279` `db.commit()` is an independent correctness fix (keep it). Est. < 1 hr. Sentinel/fallback already in place: the blocking path is untouched, so reverting the discriminator is the whole rollback.

---

## 7. References

- `sprint-57-88-plan.md` / `sprint-57-88-checklist.md` — sprint contract
- `agent-harness-execution/phase-57/sprint-57-88/progress.md` (Day 0-4) + `retrospective.md` — execution truth
- `18-handoff-design.md` — prior Cat 11/1 lifecycle spike (the `handoff` stop_reason precedent this `awaiting_approval` mirrors)
- `01-eleven-categories-spec.md §HITL Centralization` — HITLManager single-source
- `17-cross-category-interfaces.md` §4.1 (LoopEvent) / §5.2-5.3 (HITL) — contract registration
- `.claude/rules/multi-tenant-data.md` 鐵律 — resume tenant guard (cross-tenant 404)
- `.claude/rules/sprint-workflow.md §Common Risk Classes` E (stale `--reload` worker) + C (singleton/test-loop isolation) — both hit this sprint
- `claudedocs/4-changes/feature-changes/CHANGE-056-durable-pause-resume.md`
