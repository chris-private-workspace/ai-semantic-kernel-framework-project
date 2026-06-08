# Sprint 57.91 Progress — Generalized Pause Primitive + Input-ESCALATE Pause Point (地基 A Slice 3 leg 1)

**Plan**: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-91-plan.md`
**Checklist**: `../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-91-checklist.md`
**Branch**: `feature/sprint-57-91-generalized-pause-input-escalate` (from `main` `1cf0ceb4`)
**Type**: CHANGE (Cat 1 + Cat 9 feature add — new durable pause point) → CHANGE-058

---

## Day 0 — Plan-vs-Repo Verify + Branch (2026-06-08)

### Three-prong Day-0 verify

**Prong 1 (path)** — all confirmed (Read + Grep):
- `run()` input-check call site `loop.py:1032` (`async for ev in self._cat9_input_check(user_input=user_input, ctx=ctx)` + `if isinstance(ev, LoopCompleted): return`, INSIDE the LOOP span opened at `:1004`/SpanStarted `:1017`/SpanEnded `:1048`).
- `_cat9_input_check` `loop.py:545-596` (signature `(*, user_input, ctx)` — only PASS/BLOCK + tripwire; **no ESCALATE branch, no session_id/messages threaded**).
- `_cat9_hitl_branch` deferred tail `loop.py:799-839` (checkpoint `pending_approval{tool_call}` + audit `guardrail.tool.escalate.deferred` + `LoopCompleted(awaiting_approval)` — the factorable tail).
- `resume()` `loop.py:1848`; `pending_tc` build `loop.py:1907-1912` (unconditional today); shared `_run_turns` drive `loop.py:2009-2042`.
- `_emit_state_checkpoint` `loop.py:2044` (`pending_approval` → `metadata["pending_approval"]` + `resume_messages` only when set; JSONB, no migration).
- Guardrails: `GuardrailAction.ESCALATE` `_abc.py:43`; `Guardrail` ABC `_abc.py:57` (`guardrail_type` class attr + `async def check(*, content, trace_context=None) -> GuardrailResult`); `GuardrailResult.risk_level` is `Literal["LOW".."CRITICAL"]="LOW"` `_abc.py:54`; `GuardrailType.INPUT` `_abc.py:32`; `engine.register(g, *, priority=100)` `engine.py:84`; `engine.check_input` `engine.py:117` (runs INPUT chain fail-fast). Existing INPUT guardrails `input/pii_detector.py` + `input/jailbreak_detector.py` (BLOCK/SANITIZE — NOT repurposed).
- Handler `api/v1/chat/handler.py`: `CHAT_HITL_ESCALATE_TOOLS` `:119`; `build_real_llm_handler` builds `guardrail_engine = build_default_guardrail_engine()` `:294` (already has PII+Jailbreak INPUT) → registers `ToolGuardrail` priority 10 `:299`; `hitl_deferred=(hitl_manager is not None)` `:331`. **Same builder is used by ResumeService `_default_build_loop`** → wiring the input guardrail here reaches both run + resume (harmless on resume — resume drives `_run_turns`, not `run()`/input-check).

**Prong 2 (content)** — all confirmed:
- (a) `engine.check_input` → `_run_chain(INPUT)` returns whatever a guardrail yields incl. ESCALATE (not tool-gated; `engine.py:108-115`). ✅ input ESCALATE is reachable.
- (b) `resume()` reads `pending.get("tool_call", {})` + builds a `ToolCall` UNCONDITIONALLY (`:1907-1912`) → must move into a tool-kind branch (input-kind must NOT build a ToolCall). ✅
- (c) ResumeService (`platform_layer/resume/service.py`) passes only `session_id` + tenant; reads `pending_approval` generically (Explore sweep) → **no change needed** for input-kind. ✅
- (d) `_emit_state_checkpoint` stores `resume_messages` ONLY when `pending_approval` set (`:2086-2088`) → input pause inherits the no-bloat property (ordinary checkpoints stay empty). ✅
- (e) frontend HITL card renders from `ApprovalRequested` + `stopReason==="awaiting_approval"` (events, Explore sweep `HITLTurn.tsx`/`useLoopEventStream.ts`/`chatStore`) → **expected tool-agnostic**; the card copy for an input pause (`ApprovalRequest.payload.summary="approve user input"`) is the one thing to EYEBALL in the drive-through (NOT trusting the Explore "no frontend change" claim — drive-through confirms).

**Prong 3 (schema)** — **N/A**: no DB table / migration / ORM change. `pending_approval` is JSONB checkpoint metadata; the `kind` key is additive (round-trips via the existing `_serialize/_deserialize_state_for_db`). No RLS / FK touched.

**Baseline capture** (main `1cf0ceb4`, 57.90 merged): expected pytest 2232 / mypy 0/346 / run_all 10/10 / Vitest 772. Re-confirm exact numbers Day-1 before editing.

### Drift findings

- **D-DAY0-1** — `_cat9_input_check` is NOT threaded `session_id`/`messages`/`turn_count` (only `user_input`/`ctx`). Implication: the signature + the `run():1032` call site must change to pass them (plan §3.2 anticipated; not a scope shift).
- **D-DAY0-2** — `resume()` builds `pending_tc` unconditionally (`:1907`). Implication: move the build INTO the tool-kind branch so input-kind never constructs an empty `ToolCall` (plan §3.3 anticipated).
- **D-DAY0-3** — the chat handler wires NO input guardrail today (`build_default_guardrail_engine` adds PII+Jailbreak but the trigger for a drive-through must ESCALATE, which those don't). Implication: a new `KeywordEscalationGuardrail` + handler registration is required for the pause point to be reachable on 主流量 (plan §3.4 anticipated; this is the US-5 work, not a surprise).
- **D-DAY0-4** — `GuardrailResult.risk_level` is a STRING literal (`"HIGH"`), distinct from the loop's `RiskLevel.HIGH` enum used for the `ApprovalRequest`. Implication: the new guardrail returns `risk_level="HIGH"` (string); the `_cat9_input_check` ApprovalRequest still uses `RiskLevel.HIGH` (enum, mirror the tool branch). No conflict — noted to avoid a type mix-up Day-1.

### Go/No-Go

**GO** — the generalized-primitive seam (`_emit_deferred_pause`) + the input-pause path (input ESCALATE → checkpoint → `awaiting_approval` → resume drives `_run_turns` with no tool) are confirmed reachable end-to-end with NO ResumeService / endpoint / migration change. The only new artifact is a thin real guardrail (US-5). Scope unchanged from plan (drift findings all anticipated by §3, no §Acceptance shift).

### Day 0 actions
- [x] Branch `feature/sprint-57-91-generalized-pause-input-escalate` from `main` `1cf0ceb4`
- [x] Three-prong verify (Prong 1 path + Prong 2 content + Prong 3 N/A) + 4 drift findings catalogued + GO
- [ ] plan + checklist + progress committed (Day-0 commit) — next
