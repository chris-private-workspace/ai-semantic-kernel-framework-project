# Sprint 57.91 Plan — Generalized Pause Primitive + Input-ESCALATE Pause Point (地基 A Slice 3, leg 1)

**Purpose**: 地基 A Slice 3 builds GENERALIZED pause points on top of the shared re-enterable loop that Slice 1+2 (Sprint 57.89/57.90) delivered. Today the ONLY durable pause point is a tool-call ESCALATE (`_cat9_hitl_branch` deferred branch, `loop.py:799-839`): a pause requires a pending `ToolCall`, and `resume()` (`loop.py:1848`) assumes the checkpoint's `pending_approval` carries a `tool_call` it must re-execute. This sprint = **Slice 3 leg 1**: (1) extract a **generalized pause primitive** `_emit_deferred_pause(...)` — the durable-pause tail (checkpoint `pending_approval` + audit + `LoopCompleted(awaiting_approval)`) decoupled from "a tool call", so ANY call site can pause + resume; (2) wire the FIRST new concrete pause point on top of it — **input-guardrail ESCALATE**: when the loop-start input guardrail returns `ESCALATE` (not just BLOCK), the loop pauses BEFORE the first LLM call, awaiting human approval of the user input, and `resume()` continues to the first LLM turn (NO pending tool to execute). This generalizes `pending_approval` with a `kind` discriminator (`"tool"` vs `"input"`) and teaches `resume()` the no-pending-tool path. **This is a feature add** (a new user-visible pause point) on 主流量 Cat 1 — so the 57.88-90 pause-resume tests are converted (Never-Delete) and a NEW input-pause/input-resume unit test + a **drive-through** (real UI + real backend + real Azure LLM: ESCALATE-flagged input → pause → approve → answer) are the acceptance. **Record = CHANGE-058**; no new design note (continuation of the 57.88 pause-resume domain — update `19-pause-resume-design.md §5` to record the generalized primitive + input pause point; the "Generalized pause points" deferred line splits into shipped (input) + still-deferred (between-turns / mid-thinking)).
**Category / Scope**: Cat 1 (Orchestrator Loop — `_emit_deferred_pause` primitive; `_cat9_input_check` ESCALATE branch; `resume()` kind-branch) + Cat 9 (Guardrails — a real input guardrail that ESCALATEs on a configured trigger; engine wiring) + Cat 7 (the checkpoint `pending_approval` gains a `kind` + input payload — JSONB, no migration) + Cat 12 (the input pause emits the same LOOP-span / `awaiting_approval` terminator). Phase 57.91
**Created**: 2026-06-08
**Status**: Draft (scope below; code execution gated on Day-0 GO)
**Source**: Sprint 57.90 carryover (`next-phase-candidates.md` — Slice 3 generalized pause points, now enabled by the shared `_run_turns` + checkpoint-everywhere) + `19-pause-resume-design.md §5` Open Invariant "Generalized pause points" + AskUserQuestion 2026-06-08 (scope locked to **generalized primitive + input-ESCALATE** as the thinnest drive-through-able leg; between-turns + mid-thinking explicitly deferred to Slice 3 legs 2/3).

> **Modification History**
> - 2026-06-08: Initial creation — generalized pause primitive + input-ESCALATE pause point; folds the Day-0 head-start grounding (input check site, pending_approval coupling, ResumeService tool-agnosticism)

---

## 0. Background

Slice 1+2 (57.89/57.90) made `run()` and `resume()` share ONE re-enterable per-turn loop (`_run_turns`, `loop.py:1056`) and gave multi-pause-per-run. But the pause MECHANISM is still tool-shaped: the only thing that can pause durably is a `_cat9_tool_check → _cat9_hitl_branch` ESCALATE on a `ToolCall`, and `resume()` hard-reads `pending_approval["tool_call"]` (`loop.py:1907-1912`) and always executes a pending tool before continuing. "Generalized pause points" means a pause can happen at OTHER points (input guardrail, between-turns, mid-thinking) with NO pending tool. This sprint delivers the generalized PRIMITIVE + the first concrete new pause point (input), the thinnest leg.

### Ground truth re-confirmed (Day-0 head-start — this plan's Day-0 verify)

Re-confirmed at this plan's Day 0 (Prong 1 path + Prong 2 content greps + an Explore read-only sweep):
- **Input guardrail check site** — `run()` (`loop.py:1032-1035`) calls `_cat9_input_check(user_input, ctx)` ONCE at loop start, BEFORE `_run_turns`. `_cat9_input_check` (`loop.py:545-596`) currently handles only non-PASS → BLOCK (`GuardrailTriggered` + `LoopCompleted(GUARDRAIL_BLOCKED)`) and tripwire. **It has NO ESCALATE branch and is NOT threaded `session_id`/`messages`** (needed to build a resumable checkpoint). The user `messages` ([system?, user]) and `turn_count=0` exist in `run()` at the call site.
- **`GuardrailAction.ESCALATE` exists** (`guardrails/_abc.py:43`); the engine's `check_input` (`guardrails/engine.py:117-124`) runs the INPUT chain and CAN return any action incl. ESCALATE — ESCALATE is generic, not tool-specific. Existing INPUT guardrails: `PIIDetector` / `JailbreakDetector` (BLOCK/SANITIZE semantics — NOT to be repurposed). No input guardrail is wired into the chat handler today.
- **The durable-pause tail is factorable** — `_cat9_hitl_branch` deferred branch (`loop.py:799-839`): build `pending_approval` (tool payload) → `_emit_state_checkpoint(pending_approval=...)` (`loop.py:2044`, stores it + `resume_messages` in `state_snapshots` JSONB, no migration) → audit → `LoopCompleted(awaiting_approval)`. The checkpoint + audit + terminator is identical regardless of WHAT is being approved → this is the generalized primitive seam.
- **`resume()` (`loop.py:1848-2042`)** reads `pending_approval`, reads the decision (non-blocking `get_decision`), yields `ApprovalReceived`, then (tool-only today) builds `pending_tc`, execs it, appends the observation, and drives `_run_turns` inside a fresh `metrics_acc` + LOOP span (Slice 2). The decision-read + `ApprovalReceived` + the `_run_turns` drive are kind-agnostic; only the middle (exec pending tool) is tool-specific.
- **ResumeService / `/resume` endpoint / frontend are tool-agnostic** — `platform_layer/resume/service.py` loads the latest `hitl_pause` checkpoint, rehydrates messages from `resume_messages`, rebuilds the loop via `build_real_llm_handler` (zero divergence), and drives `loop.resume()`; it passes only `session_id` + tenant, never anything tool-specific. `POST /chat/{id}/resume` (`router.py:780`) passes only `session_id`. The chat-v2 frontend renders a HITL card on `ApprovalRequested` + pauses on `stopReason==="awaiting_approval"` + resumes on Approve — driven by events, not a tool struct. **Expected: no ResumeService / endpoint / frontend change** (drive-through confirms; the frontend HITL-card copy for an input pause is the one thing to eyeball).

---

## 1. Sprint Goal

Ship the generalized pause primitive + the input-ESCALATE pause point: (1) extract `_emit_deferred_pause(*, request_id, pending_approval, messages, turn_count, session_id, audit_event_type, audit_content, ctx)` — the durable-pause tail (checkpoint + audit + `awaiting_approval`) — and route the existing tool path's deferred branch through it (`pending_approval` gains `"kind": "tool"`, behavior byte-identical); (2) add an ESCALATE branch to `_cat9_input_check` (threaded `session_id`/`messages`/`turn_count`): when the input guardrail returns `ESCALATE` and the deferred wiring (`hitl_manager` + `checkpointer` + `reducer` + identity) is present, build an input `ApprovalRequest` + emit `ApprovalRequested` + call `_emit_deferred_pause` with an **input-kind** `pending_approval` (no `tool_call`); without the deferred wiring, ESCALATE fails closed to BLOCK; (3) teach `resume()` to branch on `pending_approval["kind"]` — input-kind APPROVED drives `_run_turns` directly (NO tool exec; the approved input proceeds to the first LLM turn), input-kind REJECTED blocks; tool-kind is unchanged. (4) Wire a REAL input guardrail (a thin keyword-trigger guardrail, analogous to 57.88's `echo_tool` ESCALATE) into the chat handler so the pause point is reachable on 主流量. **This is a deliberate feature add** on 主流量 Cat 1: the 57.88-90 pause-resume test assertions stay (tool path unchanged) + a NEW input-pause + input-resume unit test, and a **drive-through** (real UI + real backend + real Azure gpt-5.2) walks an ESCALATE-flagged input → pause (HITL card) → approve → answer. Out of scope: Slice 3 legs 2/3 (between-turns / mid-thinking); subagent child-loop; the 57.88 carryover ADs (checkpoint-bloat / per-tenant-capability / reject-reaper).

---

## 2. User Stories

- **US-1 (generalized pause primitive)** — As the loop maintainer, I want the durable-pause tail (checkpoint `pending_approval` + audit + `awaiting_approval`) extracted into `_emit_deferred_pause(...)` so ANY pause point reuses one source of truth (no second copy drifts). → new helper; the tool deferred branch routes through it with byte-identical behavior; `pending_approval` gains a `"kind"`.
- **US-2 (input-ESCALATE pause)** — As an approver, I want a user input flagged ESCALATE by the loop-start input guardrail to PAUSE the loop (checkpoint + release SSE) before any LLM call, so I can approve/reject the input itself — not have it silently blocked or silently proceed. → `_cat9_input_check` ESCALATE branch builds an input `ApprovalRequest` + `_emit_deferred_pause(input-kind)`; threads `session_id`/`messages`/`turn_count`.
- **US-3 (input resume, no pending tool)** — As the resumed loop, I want an input-kind pause to resume by continuing to the first LLM turn (NOT executing a tool), so an approved input proceeds exactly as it would have without the pause. → `resume()` branches on `pending_approval["kind"]`: input-kind APPROVED → drive `_run_turns` directly; REJECTED → `GuardrailTriggered(input, block)` + `GUARDRAIL_BLOCKED`. Tool-kind path unchanged.
- **US-4 (fail-closed without HITL)** — As the loop, I want an input ESCALATE WITHOUT the deferred HITL wiring to fail closed to BLOCK (not silently proceed), so a missing approval surface never lets a flagged input through. → `_cat9_input_check`: `ESCALATE && deferred wiring → pause; elif action != PASS (incl. ESCALATE-without-HITL) → BLOCK`.
- **US-5 (reachable on 主流量 — real trigger)** — As the user, I want the input pause reachable through the real chat path with a REAL guardrail (not a Potemkin), so the feature is driven, not just unit-tested. → a thin keyword-trigger input guardrail (`GuardrailType.INPUT`, returns `ESCALATE` on a configured phrase, risk HIGH) registered in the chat handler analogous to `CHAT_HITL_ESCALATE_TOOLS`.
- **US-6 (drive-through acceptance)** — As the user, I want the input-pause to actually work end-to-end through the real chat UI + backend + LLM. → drive-through: a trigger-phrase input → pause (HITL card, no answer yet) → approve → resume → the LLM answers the approved input; screenshot + observed-vs-intended diff in progress.md; fix any frontend gap that blocks the input HITL card / its Approve.

---

## 3. Technical Specifications

### 3.0 Architecture (the generalization)

```
BEFORE (Slice 2 end)                          AFTER (Slice 3 leg 1)
run(): _cat9_input_check(user_input, ctx)      run(): _cat9_input_check(user_input, ctx,
   PASS → continue / non-PASS → BLOCK             session_id, messages, turn_count)
                                                   PASS → continue
                                                   ESCALATE + deferred wiring → input PAUSE
                                                   other non-PASS (incl. ESCALATE-no-HITL) → BLOCK

_cat9_hitl_branch deferred tail (inline):      _cat9_hitl_branch deferred tail:
   checkpoint(pending_approval{tool_call})        pending_approval = {kind:"tool", tool_call:…}
   + audit + LoopCompleted(awaiting_approval)     async for ev in _emit_deferred_pause(…): yield ev

(no input pause)                                NEW _cat9_input_check ESCALATE branch:
                                                   build input ApprovalRequest + ApprovalRequested
                                                   pending_approval = {kind:"input", input:…}
                                                   async for ev in _emit_deferred_pause(…): yield ev

resume(): read pending → build pending_tc      resume(): read pending → kind = pending["kind"]
   → (not approved) block / (approved) exec        input-kind: (not appr) block / (appr) — no tool
   tool + append → drive _run_turns                tool-kind: build pending_tc; (not appr) block /
                                                                (appr) exec + append  [unchanged]
                                                   → SHARED drive _run_turns (both kinds)
```

The `_run_turns` drive (fresh `metrics_acc` + LOOP span, Slice 2) is SHARED by both kinds — only the prep before it differs (tool-kind execs the pending tool; input-kind does nothing). The tool path's `ApprovalRequest` build + `ApprovalRequested` (`loop.py:742-792`) stays byte-identical; only its deferred TAIL routes through the new helper.

### 3.1 `_emit_deferred_pause` primitive (US-1)
- New `async def _emit_deferred_pause(self, *, request_id: UUID, pending_approval: dict[str, Any], messages: list[Message], turn_count: int, session_id: UUID, audit_event_type: str, audit_content: dict[str, Any], ctx: TraceContext) -> AsyncIterator[LoopEvent]`.
- Body = the current deferred tail (`loop.py:814-838`): `_emit_state_checkpoint(session_id, messages, turn_count, tokens_used=0, source_category="orchestrator_loop:hitl_pause", ctx, pending_approval)` → if event yield it → `_audit_log_safe(audit_event_type, audit_content, ctx)` → `LoopCompleted(stop_reason=AWAITING_APPROVAL.value, total_turns=turn_count, trace_context=ctx)`. Caller has ALREADY created the `ApprovalRequest` + yielded `ApprovalRequested` (kind-specific) before calling this.
- Tool deferred branch refactor: keep the `if self._hitl_deferred and checkpointer and reducer and session_id` gate; inside, build `pending_approval = {"kind": "tool", "tool_call": {...}, "approval_request_id": str(request_id), "turn": turn_count}` then `async for ev in self._emit_deferred_pause(request_id=request_id, pending_approval=pending_approval, messages=messages if messages is not None else [], turn_count=turn_count, session_id=session_id, audit_event_type="guardrail.tool.escalate.deferred", audit_content={"tool": tc.name, "request_id": str(request_id), "turn": turn_count}, ctx=ctx): yield ev` then `return`. **Behavior byte-identical** (the `"kind": "tool"` key is additive; `resume()` defaults missing `kind` → `"tool"`).

### 3.2 `_cat9_input_check` ESCALATE branch (US-2/US-4)
- Extend the signature to `(*, user_input: str, ctx: TraceContext, session_id: UUID, messages: list[Message], turn_count: int = 0)` and update the `run()` call site (`loop.py:1032`) to pass them.
- After `g_result = await check_input(...)`, restructure the non-PASS handling:
  - `if g_result.action == GuardrailAction.ESCALATE and self._hitl_manager is not None and self._hitl_deferred and self._checkpointer is not None and self._reducer is not None:` → **input pause**:
    - identity: `tenant_id = self._tenant_id or ctx.tenant_id`; `session_id_eff = ctx.session_id or session_id`; if either None → fall through to BLOCK (fail closed; mirror `_cat9_hitl_branch:725-740` no-identity).
    - `request_id = uuid4()`; `risk_level = RiskLevel.HIGH`; `sla_deadline = now + hitl_timeout_s`; `ApprovalRequest(request_id, tenant_id, session_id, requester="guardrails", risk_level, payload={"kind": "input", "input_excerpt": user_input[:200], "reason": g_result.reason or "escalated", "summary": "approve user input"}, sla_deadline, context_snapshot={"trace_id": ctx.trace_id})`.
    - `request_approval(...)` in try/except (persist-fail → audit + BLOCK, mirror tool path).
    - audit `guardrail.input.escalate.requested` + `yield ApprovalRequested(approval_request_id=request_id, risk_level=risk_level.value, trace_context=ctx)`.
    - `pending_approval = {"kind": "input", "approval_request_id": str(request_id), "turn": turn_count}` (NO `tool_call`).
    - `async for ev in self._emit_deferred_pause(request_id=request_id, pending_approval=pending_approval, messages=messages, turn_count=turn_count, session_id=session_id_eff, audit_event_type="guardrail.input.escalate.deferred", audit_content={"request_id": str(request_id), "turn": turn_count}, ctx=ctx): yield ev` → `return`.
  - `elif g_result.action != GuardrailAction.PASS:` → existing BLOCK path (covers BLOCK/SANITIZE/REROLL **and** ESCALATE-without-HITL = fail closed, US-4).
- Tripwire branch unchanged.
- NOTE: `messages` at input-check time = the `run()` buffer ([system?, user]); the input pause checkpoint stores it as `resume_messages` so resume rehydrates the same buffer + `turn_count=0` → drives `_run_turns` from turn 0.

### 3.3 `resume()` kind-branch (US-3)
- After `yield ApprovalReceived(...)` (`loop.py:1931-1935`), branch:
  - `kind = str(pending.get("kind", "tool"))`.
  - **input-kind** (`kind == "input"`): if `decision.decision != APPROVED` → audit `resume.input.{decision}` + `GuardrailTriggered(guardrail_type="input", action="block", reason=...)` + `LoopCompleted(GUARDRAIL_BLOCKED)` + `return`. Else (APPROVED) → audit `resume.input.approved`; NO tool exec; fall through to the shared `_run_turns` drive (the approved input → first LLM turn).
  - **tool-kind** (else): build `pending_tc` from `pending["tool_call"]` (move the current `loop.py:1907-1912` build INTO this branch); if not APPROVED → existing `GuardrailTriggered(tool, block)` + `GUARDRAIL_BLOCKED`; if APPROVED → existing `ToolCallRequested` + exec + `ToolCallExecuted/Failed` + append tool message.
- The shared `metrics_acc` + LOOP span + `_run_turns` drive (`loop.py:2009-2042`) is reached by BOTH kinds (input-kind after the audit; tool-kind after the append). No change to the drive itself.

### 3.4 Real input guardrail trigger (US-5)
- New thin guardrail `backend/src/agent_harness/guardrails/input/escalation_keyword_detector.py` — `class KeywordEscalationGuardrail(Guardrail)`, `guardrail_type = GuardrailType.INPUT`, ctor takes a `frozenset[str]` of trigger phrases (case-insensitive substring); `check(content, ...)` → `GuardrailResult(action=ESCALATE, reason=f"input matched escalation phrase", risk_level="high")` when matched, else `GuardrailResult(action=PASS)`. REAL detection (not Potemkin); single responsibility; does NOT touch `PIIDetector`/`JailbreakDetector`.
- Handler wiring (`api/v1/chat/handler.py`): add `CHAT_HITL_ESCALATE_INPUT_PHRASES = frozenset({"approval required"})` (or similar deterministic phrase) near `CHAT_HITL_ESCALATE_TOOLS`; when `hitl_manager is not None`, construct + `engine.register(KeywordEscalationGuardrail(CHAT_HITL_ESCALATE_INPUT_PHRASES))` into the same `GuardrailEngine` that gets the `ToolGuardrail`. The `hitl_deferred=(hitl_manager is not None)` flag (`handler.py:331`) already gates the deferred branch.

### 3.5 What is explicitly NOT done (Slice 3 legs 2/3)
- No between-turns pause point (a policy gate inside `_run_turns` — budget/turn/periodic check-in; needs a trigger-policy design). No mid-thinking pause (streaming-LLM interruption). No subagent child-loop (Cat 11). No checkpoint-bloat fix / per-tenant capability policy / reject-path reaper (57.88 carryover ADs). No output-guardrail ESCALATE pause (a possible future leg; out of scope).

### 3.6 Lint / neutrality / doc single-source
- `check_llm_sdk_leak` 0 (no adapter/SDK touched). `check_ap1_pipeline_disguise` green (no new loop; the helper is a tail emitter, the input branch is a guardrail gate). `check_promptbuilder_usage` (AP-8) green (PromptBuilder untouched, inside `_run_turns`). `category-boundaries` — the new guardrail lives in Cat 9 `guardrails/input/`; no backwards import. No new cross-category contract (the `resume()` ABC signature is unchanged; `pending_approval` is an internal checkpoint payload, not a registered contract) → 17.md unchanged EXCEPT a 1-line note in §4.1/§5.3 that `awaiting_approval` now also originates from an input-guardrail ESCALATE (same terminal, new origin). `19-pause-resume-design.md §5` updated: the "Generalized pause points" deferred line splits into shipped (input-ESCALATE primitive) + still-deferred (between-turns / mid-thinking). CHANGE-058 records it.

### 3.7 Validation (US-1..US-6)
- **mypy `src/ --strict` 0**; `run_all` 10/10; `black`/`isort`/`flake8` clean.
- **pytest**: the 57.88-90 pause-resume tests (tool path) assert UNCHANGED (the tool deferred branch is byte-identical behavior; `"kind":"tool"` is additive). NEW unit tests: (a) input ESCALATE → pause (checkpoint `pending_approval{kind:"input"}` + `LoopCompleted(awaiting_approval)`, no LLM call); (b) input-pause resume APPROVED → drives `_run_turns` to `end_turn` with NO tool exec; (c) input-pause resume REJECTED → `GUARDRAIL_BLOCKED`; (d) ESCALATE-without-HITL → BLOCK (fail closed, US-4). NEW `KeywordEscalationGuardrail` unit test. Full backend suite green (NET delta documented — expect +4-6 from the new tests).
- **Drive-through** (US-6): real UI + real backend + real Azure — trigger-phrase input → pause (HITL card, no answer) → approve → resume → answer; screenshot + observed-vs-intended diff in progress.md. (Per CLAUDE.md §Drive-Through Acceptance — the input pause is user-facing.)

---

## 4. File Change List

| File | Change |
|------|--------|
| `backend/src/agent_harness/orchestrator_loop/loop.py` | **EDIT** — (US-1) NEW `_emit_deferred_pause(...)` helper; route `_cat9_hitl_branch` deferred tail through it (`pending_approval` gains `"kind":"tool"`, byte-identical). (US-2/US-4) `_cat9_input_check` — extend signature (`session_id`/`messages`/`turn_count`) + add ESCALATE→input-pause branch + ESCALATE-no-HITL→BLOCK; update the `run()` call site (`:1032`). (US-3) `resume()` — branch on `pending_approval["kind"]`; move `pending_tc` build into the tool-kind branch; input-kind APPROVED → shared `_run_turns` drive (no tool exec). Update file-header MHist (1-line, E501-safe). |
| `backend/src/agent_harness/guardrails/input/escalation_keyword_detector.py` | **NEW** — `KeywordEscalationGuardrail(Guardrail)`, `GuardrailType.INPUT`, ESCALATE on a configured trigger phrase (US-5). File header. |
| `backend/src/agent_harness/guardrails/input/__init__.py` | **EDIT (if it re-exports)** — export `KeywordEscalationGuardrail` if the package re-exports input guardrails (verify Day-0). |
| `backend/src/api/v1/chat/handler.py` | **EDIT** — `CHAT_HITL_ESCALATE_INPUT_PHRASES` + register `KeywordEscalationGuardrail` into the chat `GuardrailEngine` when `hitl_manager` present (US-5). |
| `backend/tests/unit/agent_harness/orchestrator_loop/test_loop_pause_resume.py` | **EDIT** — ADD input-ESCALATE pause + input-resume (APPROVED/REJECTED) + ESCALATE-no-HITL-BLOCK unit tests (US-2/US-3/US-4); keep the 57.88-90 tool-path assertions unchanged. |
| `backend/tests/unit/agent_harness/guardrails/test_escalation_keyword_detector.py` | **NEW** — `KeywordEscalationGuardrail` unit test (match → ESCALATE / no-match → PASS). |
| `backend/tests/integration/api/test_chat_pause_resume_e2e.py` | **EDIT (if feasible)** — add an input-pause integration assertion at the coroutine layer (mirror the tool-pause e2e). |
| frontend (`HITLTurn` / `useLoopEventStream` / `chatStore`, IF the drive-through finds a gap) | **EDIT (conditional)** — only if the input HITL card / its Approve does not surface for a no-tool pause. Likely none (events are tool-agnostic). |
| `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-91-plan.md` + `-checklist.md` | **NEW** — this plan + checklist |
| `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-91/progress.md` + `retrospective.md` | **NEW** — Day 0-N progress + retro |
| `claudedocs/4-changes/feature-changes/CHANGE-058-generalized-pause-input-escalate.md` | **NEW** — the change record (primitive + input pause point + drive-through) |
| `docs/03-implementation/agent-harness-planning/19-pause-resume-design.md` | **EDIT** — §5 split "Generalized pause points" into shipped (input-ESCALATE) + still-deferred (between-turns / mid-thinking); add the `_emit_deferred_pause` primitive + `pending_approval.kind` to §1/§3. |
| `docs/03-implementation/agent-harness-planning/17-cross-category-interfaces.md` | **EDIT (1-line)** — §4.1/§5.3 note `awaiting_approval` now also originates from an input-guardrail ESCALATE (same terminal, new origin); no new contract. |

No new DB table / no migration / no new Azure-adapter change / no ResumeService change / no `/resume` endpoint change (the input pause flows through the existing tool-agnostic resume path).

---

## 5. Acceptance Criteria

- `_emit_deferred_pause(...)` exists and is the SINGLE durable-pause tail; the tool deferred branch routes through it with byte-identical behavior (tool-path pause-resume tests unchanged); `pending_approval` carries a `"kind"` (US-1).
- An input that the loop-start guardrail flags `ESCALATE` (with deferred HITL wiring) PAUSES before any LLM call: checkpoint `pending_approval{kind:"input"}` + `ApprovalRequested` + `LoopCompleted(awaiting_approval)`, SSE released; no LLM call happened (US-2).
- An input ESCALATE WITHOUT deferred HITL wiring fails closed to BLOCK (`GUARDRAIL_BLOCKED`), not silent-proceed (US-4).
- `resume()` of an input-kind pause: APPROVED → drives `_run_turns` to `end_turn` with NO tool exec (the approved input → first LLM turn); REJECTED → `GuardrailTriggered(input, block)` + `GUARDRAIL_BLOCKED` (US-3). Tool-kind resume unchanged.
- A REAL input guardrail (`KeywordEscalationGuardrail`) is wired into the chat handler so the pause point is reachable on 主流量 (not a Potemkin) (US-5).
- `mypy --strict src/` 0; `run_all` 10/10 (LLM SDK leak 0; AP-1; AP-8); `black`/`isort`/`flake8` clean; full backend pytest green (NET delta documented). `19-pause-resume-design.md §5` updated; CHANGE-058 written.
- **Drive-through PASS**: real UI + real backend + real Azure — trigger-phrase input → pause (HITL card) → approve → answer; screenshot + observed-vs-intended diff recorded. (No "gate-only" claimed as drive-through.)

---

## 6. Deliverables

- [ ] `_emit_deferred_pause` primitive; tool deferred branch routed through it (byte-identical); `pending_approval.kind` (US-1)
- [ ] `_cat9_input_check` ESCALATE→input-pause branch + ESCALATE-no-HITL→BLOCK; `run()` call site threads `session_id`/`messages`/`turn_count` (US-2/US-4)
- [ ] `resume()` kind-branch; input-kind APPROVED drives `_run_turns` (no tool exec); tool-kind unchanged (US-3)
- [ ] `KeywordEscalationGuardrail` + chat-handler wiring (US-5)
- [ ] NEW unit tests: input pause / input resume APPROVED+REJECTED / ESCALATE-no-HITL BLOCK / KeywordEscalationGuardrail; tool-path tests unchanged; full backend pytest green (US-2/US-3/US-4/validation)
- [ ] mypy 0 + run_all 10/10 + format chain (validation)
- [ ] **drive-through PASS** (real UI + real backend + real Azure; screenshot + diff) (US-6)
- [ ] CHANGE-058 + `19-pause-resume-design.md §5` updated + 17.md 1-line note + progress.md + retrospective.md
- [ ] commit (Day 0-N) — push + PR user-authorized

---

## 7. Workload Calibration

Scope class: **`backend-core-loop-refactor` (0.55) — 3rd data point, CAVEATED (FEATURE-ADD shape, different again from Slice 1 pure-extraction + Slice 2 behavior-change-rewire)**. This sprint ADDS a new pause point + a generalized primitive + a new guardrail + handler wiring — a feature on the 主流量 Cat 1 surface, not a refactor. The work splits: ~`_emit_deferred_pause` extract + tool reroute (mechanical, ~0.5 hr) / input ESCALATE branch + signature thread (~1.5 hr) / `resume()` kind-branch (~1 hr) / `KeywordEscalationGuardrail` + handler wiring (~1.5 hr) / tests (~2.5 hr) / drive-through (~1.5 hr) / docs (~1 hr). The dominant costs are the tests + the drive-through (incl. a possible small frontend fix), not the core rewire. Reuse the Slice-1/2 class for continuity but flag the shape difference a THIRD time (feature-add vs refactor) — if its ratio diverges, that's the shape; if 3 data points keep landing < 0.7, consider a `loop-pause-point-feature` class split in retro. **Agent-delegated: no** (parent-direct) — 主流量 loop surgery (input check + resume restructure) touching the most-tested file + a behavior-visible feature + a drive-through is too high-blast-radius to delegate; `agent_factor = 1.0`. Does NOT extend the `AD-Calibration-AgentDelegated-WallClock-Measure` streak (parent-direct, same as 57.88/89/90).

> Bottom-up est ~10 hr → class-calibrated commit ~5.5 hr (mult 0.55). **Agent-delegated: no.**

If Day-1 shows the input branch ripples wider than the input check + resume (e.g. the guardrail engine needs surgery to surface ESCALATE through `check_input`, or the frontend needs real work), STOP and re-scope (split the real-guardrail wiring / drive-through into a follow-up) rather than rush.

---

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| **Input ESCALATE never reaches the loop** (guardrail engine swallows it / `check_input` can't return ESCALATE) | Day-0 verified: `GuardrailAction.ESCALATE` exists (`_abc.py:43`); `check_input` runs the INPUT chain and returns whatever the guardrail yields (`engine.py:117-124`) — ESCALATE is not tool-gated. Day-1: the `KeywordEscalationGuardrail` unit test proves it returns ESCALATE; the input-pause unit test proves `_cat9_input_check` routes it to a pause. |
| **Input pause checkpoint doesn't save / can't resume** (multi-kind silently broken) | The input pause reuses the SAME `_emit_state_checkpoint` + `resume_messages` + ResumeService path the tool pause uses (Day-0 verified tool-agnostic). The input-resume unit test + the drive-through are the proof. `turn_count=0` at input-check time is a valid StateVersion (`_emit_state_checkpoint` builds `parent_version=None` for turn 0). |
| **`resume()` mis-branches** (input-kind tries to exec an empty tool, or tool-kind regresses) | The `pending_tc` build moves INTO the tool-kind branch; input-kind never constructs a `ToolCall`. Default `kind="tool"` preserves any in-flight tool checkpoints. Unit tests cover BOTH kinds APPROVED+REJECTED; the unchanged tool-path tests guard the regression. |
| **Over-abstraction** (a generator-returning-request-id mega-helper) | Factor ONLY the shared tail (`_emit_deferred_pause`); each kind builds its own `ApprovalRequest` (payloads genuinely differ). ~30 lines of focused per-kind build is clearer than a parameterized request-builder generator (Karpathy §2/§3). |
| **Repurposing a security guardrail** | Do NOT make `PIIDetector`/`JailbreakDetector` ESCALATE; add a thin single-responsibility `KeywordEscalationGuardrail`. The drive-through trigger is a deterministic phrase (analogous to `echo_tool`). |
| **Frontend can't surface a no-tool HITL card** (drive-through blocked) | In scope to fix (US-6). Day-0: the card renders from `ApprovalRequested` + `awaiting_approval` (events, not a tool struct); likely renders as-is. Eyeball the card copy for an input pause (the `ApprovalRequest.payload.summary="approve user input"` is what a generic card would show); small fix only if the card hard-assumes a tool name. |
| **Drive-through non-determinism (real LLM)** | The pause is BEFORE the LLM call (deterministic on the trigger phrase), so the PAUSE is fully deterministic; only the post-approve answer is LLM-worded. Fall back to a scripted real-backend drive (trigger input → `/resume`) AND attempt the UI drive; record exactly what was driven. |
| **Risk Class E (stale `--reload` backend)** | Clean restart before the drive-through (kill stale uvicorn reloader+worker procs; confirm sole owner of :8000) — the new guardrail + the input branch are startup-wired (handler builds the engine at request time, but a stale process runs old `handler.py`). |
| **Risk Class C (test isolation on the most-tested file)** | Run the full suite; module-level singleton reset fixtures already in place (`agent_harness/conftest.py`). The new guardrail is stateless (no singleton). |
| **LLM-neutrality** | No adapter/SDK touched; `check_llm_sdk_leak` gates. |
| **Smuggling unrelated change** | The `loop.py` change is exactly the 3 edits (primitive + input branch + resume branch); the tool ApprovalRequest build + the `_run_turns` drive stay byte-identical (diff to those blocks = 0 lines beyond the tail reroute). |

---

## 9. Out of Scope (this sprint; → Slice 3 legs 2/3 / separate ADs)

- **Slice 3 leg 2 — between-turns pause** (a policy gate inside `_run_turns`: budget/turn-count/periodic check-in → pause). Needs a trigger-policy design; the primitive (`_emit_deferred_pause`) shipped here is its foundation.
- **Slice 3 leg 3 — mid-thinking pause** (interrupt an in-flight streaming LLM call). Hardest; separate.
- **Output-guardrail ESCALATE pause** — a possible future leg (the primitive supports it); not done.
- **Subagent child-loop (Cat 11)** — consumes the lifecycle skeleton; distinct larger sprint.
- **`AD-Resume-Checkpoint-Bloat`** (`resume_messages` → `messages` table + checkpoint TTL) — the input pause adds another `resume_messages` writer; same open AD.
- **`AD-Resume-Tenant-Capability-Policy`** (per-tenant `capability_matrix.yaml` — now also per-tenant input-escalation phrases) — separate AD.
- **`AD-Resume-Reject-Path`** (reject-then-resume / checkpoint reaper) — separate AD; an input-kind reject leaves a dangling checkpoint the same way.
