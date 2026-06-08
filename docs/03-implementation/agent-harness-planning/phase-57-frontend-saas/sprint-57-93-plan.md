# Sprint 57.93 Plan — Output-Guardrail ESCALATE Pause Point (地基 A Slice 3, output-guardrail leg)

**Purpose**: 地基 A Slice 3 builds GENERALIZED pause points on the shared re-enterable loop (`_run_turns`, Slice 1+2) using the `_emit_deferred_pause` primitive (Slice 3 leg 1 / Sprint 57.91). Leg 1 shipped the input-guardrail ESCALATE pause (before the first LLM call); leg 2 (Sprint 57.92) shipped the between-turns guardrail ESCALATE pause (at the loop top between turns). This sprint = the **output-guardrail ESCALATE pause point** — the THIRD concrete pause point: when an OUTPUT guardrail flags a FINAL answer ESCALATE, the loop pauses **BEFORE delivering it** (before `LLMResponded` renders the answer in the UI), awaiting human approval; on APPROVE the held answer is re-emitted (no LLM re-call) and the turn ends; on REJECT the answer is **never rendered** (`GUARDRAIL_BLOCKED`). This reuses `_emit_deferred_pause` (leg 1's primitive) and the EXISTING `GuardrailType.OUTPUT` + `GuardrailEngine.check_output` (NO new guardrail type — unlike leg 2). The decisive design choice is **pre-delivery gating**: the frontend renders the answer from the `llm_response` SSE event (`chatStore.ts:365`), which fires at `loop.py:1859` — BEFORE the existing per-response `_cat9_output_check` at `loop.py:1893`. A pause AT the existing check point would be a Potemkin (the answer is already on screen). So the new pause is a CONDITIONAL pre-gate inserted BEFORE `LLMResponded` for final answers (`_cat9_output_escalate_pause`), gated on `is_final_answer AND the full deferred-HITL wiring` so non-HITL paths are byte-unchanged. `resume()` of an output-kind pause is the SIMPLEST kind — it does NOT drive `_run_turns` (the turn already produced its terminal answer); APPROVED re-emits the held `LLMResponded` + `LoopCompleted(END_TURN)`, REJECTED emits `GuardrailTriggered(output, block)` + `LoopCompleted(GUARDRAIL_BLOCKED)`. **This is a feature add** (a new user-visible pause point) on 主流量 Cat 1 — so the 57.88-92 input/between-turns/tool pause-resume tests are kept UNCHANGED (those paths are untouched) and a NEW output-pause / output-resume unit test + a **drive-through** (real UI + real backend + real Azure LLM: a final answer whose content trips the output guardrail → pause → approve → answer renders / reject → answer withheld) are the acceptance. **Record = CHANGE-060**; no new design note (continuation of the 57.88 pause-resume domain — update `19-pause-resume-design.md §5`: the "Generalized pause points" line now lists shipped input + between-turns + output, still-deferred mid-thinking).

**Category / Scope**: Cat 1 (Orchestrator Loop — `_cat9_output_escalate_pause` conditional pre-gate before `LLMResponded`; `resume()` output kind-branch + `_replay_approved_output` helper) + Cat 9 (Guardrails — a real `OutputKeywordEscalationGuardrail` on the EXISTING `GuardrailType.OUTPUT` chain; engine wiring; NO new type/method) + Cat 7 (the checkpoint `pending_approval.kind = "output"` carrying the held answer snapshot — JSONB, no migration) + Cat 12 (the output pause emits the same LOOP-span / `awaiting_approval` terminator + `ApprovalRequested`). Phase 57.93

**Created**: 2026-06-08
**Status**: Draft (scope below; code execution gated on Day-0 GO)
**Source**: Sprint 57.92 §9 Out of Scope ("Output-guardrail ESCALATE pause … Possible future leg") + `next-phase-candidates.md` (Sprint 57.92 carryover) + `19-pause-resume-design.md §5` Open Invariant "Generalized pause points" + AskUserQuestion 2026-06-08 (feature = **output-guardrail ESCALATE pause**; semantics = **pre-delivery gate** — the flagged answer is withheld until approved).

> **Modification History**
> - 2026-06-08: Initial creation — output-guardrail ESCALATE pause point on the `_emit_deferred_pause` primitive; pre-delivery gate (pause before LLMResponded for final answers); reuse GuardrailType.OUTPUT; resume output-kind re-emits the held answer (no _run_turns drive)

---

## 0. Background

Slice 1+2 (57.89/57.90) made `run()` and `resume()` share ONE re-enterable per-turn loop (`_run_turns`, `loop.py:1460`). Slice 3 leg 1 (57.91) extracted the generalized durable-pause tail `_emit_deferred_pause(...)` (`loop.py:1038`) — checkpoint `pending_approval` + audit + `LoopCompleted(awaiting_approval)` — and built the FIRST new pause point (input-guardrail ESCALATE; `pending_approval.kind = "input"`). Leg 2 (57.92) added the SECOND (between-turns guardrail ESCALATE at the loop top; `kind = "between_turns"`; a NEW `GuardrailType.BETWEEN_TURNS`). "Generalized pause points" still lists deferred legs; this sprint delivers the **output-guardrail ESCALATE pause point** — the THIRD concrete pause point. Unlike legs 1/2 it reuses the EXISTING `GuardrailType.OUTPUT` + `check_output` (the output guardrail chain already exists; it just never paused). The novel problem this leg solves — absent in legs 1/2 — is the **mid-turn re-generation / pre-delivery gotcha** that leg 2's plan flagged repeatedly: the output is produced mid-turn, the frontend renders it from `llm_response`, and a naïve pause after the fact is a Potemkin. The pre-delivery design below resolves it without re-running the LLM.

### Ground truth re-confirmed (Day-0 head-start — this plan's Day-0 verify)

Re-confirmed at this plan's Day 0 (Prong 1 path + Prong 2 content greps on `loop.py` / `engine.py` / `_abc.py` / `handler.py` / `chatStore.ts`):

- **The frontend renders the answer from `llm_response`, not `loop_end`** (`frontend/src/features/chat_v2/store/chatStore.ts:351-366`): `case "llm_response"` pushes an `AnswerBlock` `if (ev.data.content)`. So the answer is on screen the instant `LLMResponded` fires — `loop.py:1859`, which is BEFORE the existing per-response output check `_cat9_output_check` at `loop.py:1893`. **A pause at the existing output-check point cannot gate delivery** (the answer already rendered = AP-4 Potemkin). Pre-delivery gating REQUIRES the pause BEFORE `LLMResponded`.
- **`GuardrailType.OUTPUT` + `check_output` already exist** (`_abc.py:35` `GuardrailType` has INPUT/OUTPUT/BETWEEN_TURNS/TOOL; `engine.py:135` `check_output` runs the OUTPUT chain). **No new GuardrailType, no new engine method** (unlike leg 2). A real `OutputKeywordEscalationGuardrail(GuardrailType.OUTPUT)` registers on the existing chain.
- **The chat path's OUTPUT chain is NON-empty** (Day-0 D-DAY0-1 correction): `handler.py:325` builds `build_default_guardrail_engine()` (`_factory.py:54-68`) which registers `ToxicityDetector` (OUTPUT, priority 10) + `SensitiveInfoDetector` (OUTPUT, priority 20) — plus the input PII/Jailbreak. So adding an `OutputKeywordEscalationGuardrail` joins a non-empty chain. `_run_chain` (`engine.py:102-117`) is **fail-fast-first-non-PASS in ascending priority order**, so registering the new guardrail at **priority=5** (mirror the input keyword guardrail's priority=5) makes it run FIRST → its ESCALATE on the demo phrase wins deterministically, and a non-matching answer PASSes through to Toxicity (p10) + SensitiveInfo (p20) unchanged. `SensitiveInfoDetector` only matches system-prompt-leak patterns (`You are a/an X agent`, `<system>`, `Your role is to`) + cross-tenant UUIDs — the demo phrase `confidential` matches NONE → no BLOCK collision. (ToxicityDetector match logic to re-confirm Day-1 against the real demo answer; priority=5 makes mine fire first regardless.)
- **The per-response `_cat9_output_check`** (`loop.py:1089-1160`) runs once per LLM response on `parsed.text` at `loop.py:1893`, BEFORE the stop_reason terminator: BLOCK → terminate; SANITIZE/REROLL/**ESCALATE** → `GuardrailTriggered` + **continue**; tripwire → terminate. The ESCALATE-continue branch stays UNTOUCHED — the new pre-gate handles ESCALATE-pause for final answers BEFORE `LLMResponded`; non-paused paths still pass through 1893 unchanged.
- **The final-answer emission points** (`loop.py:1903` `should_terminate_by_stop_reason(response)` → `END_TURN`; `loop.py:1921` `classify_output(response) == OutputType.FINAL` → `END_TURN`) both yield `LoopCompleted(END_TURN, …metrics…)` then `return`. `is_final_answer = should_terminate_by_stop_reason(response) or classify_output(response) == OutputType.FINAL` is computable right after `parsed = parse(response)` (`loop.py:1851`); both helpers + `OutputType` are already imported (used at 1903/1921). The per-call token locals (`_input_tokens` / `_output_tokens` / `_cached_input_tokens` / `_provider`, assigned ~1841-1847) and `response.model` / `metrics_acc.cache_hit_rate` are in scope at the parse point → the held-answer snapshot can capture them.
- **`resume()`** (`loop.py:2278-2552`) reads `pending_approval`, reads the decision (non-blocking `get_decision`), yields `ApprovalReceived`, then branches on `pending_approval["kind"]`: `"input"`/`"between_turns"` (no tool, fall through) and the default `"tool"` (exec the pending tool, fall through); ALL kinds then drive the SHARED `_run_turns` inside a fresh `metrics_acc` + LOOP span (`loop.py:2502-2552`). The output kind is DIFFERENT: it does NOT drive `_run_turns` (the turn already produced its terminal answer) — it re-emits the held `LLMResponded` + `LoopCompleted(END_TURN)` (APPROVED) or `GuardrailTriggered`+`GUARDRAIL_BLOCKED` (REJECTED) and RETURNS before the shared drive.
- **`HITLTurn` / `useLoopEventStream` / `chatStore` are tool-agnostic** for the pause (proven legs 1/2: a no-tool pause surfaces an approval card; the SSE events `ApprovalRequested` / `loop_end(awaiting_approval)` / `ApprovalReceived` / `loop_end` carry no kind). Expected frontend change: NONE — but the drive-through must confirm the answer is genuinely WITHHELD before approval (the new, leg-specific UX assertion) and rendered after.

---

## 1. Sprint Goal

Ship the output-guardrail ESCALATE pause point on the `_emit_deferred_pause` primitive: (1) add `_cat9_output_escalate_pause` — a conditional pre-gate inserted BEFORE `LLMResponded` (right after `parsed = parse(...)`), gated at the call site on `is_final_answer AND hitl_manager AND hitl_deferred AND checkpointer AND reducer`; it runs `check_output(parsed.text)`; on `ESCALATE` it builds an output `ApprovalRequest` + emits `ApprovalRequested` + calls `_emit_deferred_pause` with `pending_approval.kind = "output"` carrying the held-answer snapshot (`answer_text` + the per-call token/provider fields); any non-ESCALATE result → return (no-op, fall through to the unchanged `LLMResponded` + `_cat9_output_check`); (2) `resume()` gains an `output` kind-branch (mirror of input's APPROVED/REJECTED gate, but TERMINAL — no `_run_turns` drive): APPROVED → `_replay_approved_output` re-emits `LLMResponded(answer_text)` + `Thinking` + appends the assistant message + `LoopCompleted(END_TURN, …snapshot metrics…)` + return; REJECTED → `GuardrailTriggered(output, block)` + `LoopCompleted(GUARDRAIL_BLOCKED)` + return; (3) wire a REAL `OutputKeywordEscalationGuardrail` (`GuardrailType.OUTPUT`, ESCALATE on a configured phrase) into the chat handler + a DEMO_SYSTEM_PROMPT line so the real LLM produces a FINAL answer containing the phrase. **This is a deliberate feature add** on 主流量 Cat 1: the 57.88-92 input/between-turns/tool pause-resume tests stay UNCHANGED + NEW output-pause + output-resume (APPROVED/REJECTED) + ESCALATE-pre-gate-only-when-final + `OutputKeywordEscalationGuardrail` unit tests, and a **drive-through** (real UI + real backend + real Azure gpt-5.2) walks a final answer whose content trips the output guardrail → pause (HITL card, **answer NOT yet shown**) → approve → answer renders / reject → answer withheld. Out of scope: Slice 3 leg 3 (mid-thinking pause); subagent child-loop (Cat 11); pausing on non-final (TOOL_USE) output (the tool guardrail already pauses before tool exec); the 57.88 carryover ADs.

---

## 2. User Stories

- **US-1 (output gate on the primitive)** — As the loop maintainer, I want an output pause to reuse the leg-1 `_emit_deferred_pause` primitive (one durable-pause tail, no second copy) and the EXISTING `GuardrailType.OUTPUT` chain (no new type) so the pause mechanism + guardrail surface stay single-source. → `_cat9_output_escalate_pause` builds the kind-specific `ApprovalRequest` + `ApprovalRequested`, then calls `_emit_deferred_pause` with an `output`-kind `pending_approval`.
- **US-2 (pre-delivery pause)** — As an approver, I want the loop to PAUSE a FINAL answer flagged ESCALATE **before it is delivered** (before `LLMResponded` renders it), so I can approve/reject BEFORE the user sees the flagged content — not approve it after it is already on screen. → the pre-gate runs BEFORE `LLMResponded`; ESCALATE + deferred wiring → pause (checkpoint `pending_approval{kind:"output", answer_text}` + `ApprovalRequested` + `awaiting_approval`); `LLMResponded` is NOT emitted for the held answer.
- **US-3 (output resume, no re-generation, no re-drive)** — As the resumed loop, I want an output pause to resume by DELIVERING (or withholding) the already-produced answer — NOT re-running the LLM, NOT driving more turns. → `resume()` output kind: APPROVED → `_replay_approved_output` re-emits the held `LLMResponded` + `Thinking` + `LoopCompleted(END_TURN)` (no LLM call); REJECTED → `GuardrailTriggered(output, block)` + `GUARDRAIL_BLOCKED`; either way `return` before the shared `_run_turns` drive. Input + between-turns + tool kinds unchanged.
- **US-4 (additive — non-HITL & non-final byte-unchanged)** — As the loop maintainer, I want the pre-gate to change NOTHING when the deferred-HITL wiring is absent OR the response is not a final answer, so existing output-guardrail behavior + the 57.88-92 tests are untouched. → the pre-gate is gated at the call site on `is_final_answer AND hitl_manager AND hitl_deferred AND checkpointer AND reducer`; otherwise it is never entered. The per-response `_cat9_output_check` at 1893 (BLOCK/sanitize/reroll/escalate-continue/tripwire) stays byte-identical.
- **US-5 (reachable on 主流量, not a Potemkin)** — As the user, I want the output pause reachable through the real chat path with a REAL guardrail + a real final-answer flow. → a real `OutputKeywordEscalationGuardrail` registered in the chat handler (when `hitl_manager`) on a configured phrase (NOT colliding with the input `approval required` / between-turns `checkpoint` phrases) + a DEMO_SYSTEM_PROMPT line so the LLM emits a final answer containing the phrase.
- **US-6 (drive-through acceptance — withhold-then-deliver)** — As the user, I want the output pause to actually work end-to-end through the real chat UI + backend + LLM, and crucially I want the flagged answer to be WITHHELD until I approve. → drive-through: a request that makes the LLM emit a flagged final answer → pause (HITL card, **AnswerBlock NOT present**) → approve → answer renders; (and a reject path → answer never renders, `GUARDRAIL_BLOCKED`). screenshot + observed-vs-intended diff in progress.md; fix any frontend gap that lets the answer leak before approval.

---

## 3. Technical Specifications

### 3.0 Architecture (the third pause point — pre-delivery gate)

```
per-turn body (Slice 2/leg 2)                  per-turn body (Slice 3 output leg)
  parsed = parse(response)                       parsed = parse(response)
                                                 NEW pre-delivery gate (final answers only):
                                                   is_final = stop_reason || classify==FINAL
                                                   if is_final and <full HITL wiring>:
                                                     async for ev in _cat9_output_escalate_pause(
                                                         output_text=parsed.text, response_snapshot,
                                                         ctx, turn_count, session_id, messages):
                                                       yield ev; LoopCompleted → return
  yield LLMResponded(content=parsed.text)        yield LLMResponded(content=parsed.text)   # held back if paused above
  yield Thinking; post-LLM checkpoint            yield Thinking; post-LLM checkpoint
  _cat9_output_check (BLOCK/.../escalate-cont.)  _cat9_output_check (UNCHANGED)
  stop_reason / classify / dispatch              stop_reason / classify / dispatch

_cat9_output_escalate_pause (NEW; mirror of _cat9_between_turns_check's escalate path):
   g = check_output(output_text)                       # EXISTING OUTPUT chain
   action == ESCALATE → _cat9_output_hitl_pause → _emit_deferred_pause(kind="output", answer snapshot)
   action != ESCALATE → return  (no-op; caller falls through to LLMResponded + 1893)

resume(): kind = pending["kind"]                  (legs had: "input" | "between_turns" | "tool")
   "output": APPROVED → _replay_approved_output (LLMResponded + Thinking + END_TURN); return   # NO drive
             REJECTED → GuardrailTriggered(output,block) + GUARDRAIL_BLOCKED; return            # NO drive
   "input" / "between_turns" / "tool":  (unchanged) → SHARED drive _run_turns
```

The output kind is the ONLY kind that does NOT drive `_run_turns` — its turn already produced a terminal answer, so resume re-emits it (no re-generation) rather than continuing the loop. The input/between-turns/tool branches + the `_run_turns` drive + `_cat9_output_check` + `LLMResponded` (for non-paused turns) stay byte-identical.

### 3.1 `_cat9_output_escalate_pause` pre-gate + call site (US-2/US-4)
- New `async def _cat9_output_escalate_pause(self, *, output_text: str, response_snapshot: dict[str, Any], ctx: TraceContext, turn_count: int, session_id: UUID, messages: list[Message]) -> AsyncIterator[LoopEvent]`:
  - `if self._guardrail_engine is None: return` (defensive; caller gated).
  - `g_result = await self._guardrail_engine.check_output(output_text, trace_context=ctx)`.
  - `if g_result.action == GuardrailAction.ESCALATE:` → `async for ev in self._cat9_output_hitl_pause(answer_text=output_text, response_snapshot=response_snapshot, reason=g_result.reason or "escalated", ctx=ctx, session_id=session_id, messages=messages, turn_count=turn_count): yield ev` → `return` (terminal — the pause yields `LoopCompleted`).
  - else → `return` (no-op; the caller falls through to the unchanged `LLMResponded` + `_cat9_output_check`, which handles BLOCK/sanitize/reroll/escalate-continue/tripwire). **The pre-gate ONLY pauses on ESCALATE; it does not emit `GuardrailTriggered` and does not handle BLOCK** (that stays at 1893, byte-identical). This keeps the double `check_output` call (pre-gate + 1893) inert for every non-ESCALATE final answer — a documented, accepted spike cost; the demo uses a keyword detector so the second call is negligible.
- New call site in `_run_turns`, IMMEDIATELY after `parsed = await self._output_parser.parse(...)` (`loop.py:1851`) and BEFORE `yield LLMResponded(...)` (`loop.py:1859`):
  ```
  is_final_answer = should_terminate_by_stop_reason(response) or (
      classify_output(response) == OutputType.FINAL
  )
  if (
      is_final_answer
      and self._guardrail_engine is not None
      and self._hitl_manager is not None
      and self._hitl_deferred
      and self._checkpointer is not None
      and self._reducer is not None
  ):
      output_pause_terminated = False
      response_snapshot = {
          "answer_text": parsed.text,
          "input_tokens": _input_tokens,
          "output_tokens": _output_tokens,
          "cached_input_tokens": _cached_input_tokens,
          "provider": _provider,
          "model": response.model,
          "cache_hit_rate": metrics_acc.cache_hit_rate,
      }
      async for ev in self._cat9_output_escalate_pause(
          output_text=parsed.text, response_snapshot=response_snapshot,
          ctx=ctx, turn_count=turn_count, session_id=session_id, messages=messages):
          yield ev
          if isinstance(ev, LoopCompleted):
              output_pause_terminated = True
      if output_pause_terminated:
          return
  ```
  The gate is gated on the SAME full deferred-HITL wiring the pause needs, so when that wiring is absent (most unit tests / non-HITL deployments) the gate is never entered → zero behavior change, zero extra `check_output` call. `is_final_answer` is computed locally (the pure helpers are re-called at 1903/1921 — negligible).

### 3.2 `_cat9_output_hitl_pause` (US-1/US-2)
- New `async def _cat9_output_hitl_pause(self, *, answer_text: str, response_snapshot: dict[str, Any], reason: str, ctx, session_id, messages, turn_count) -> AsyncIterator[LoopEvent]` — a near-verbatim mirror of `_cat9_between_turns_hitl_pause` (`loop.py:1240-1358`):
  - `if self._hitl_manager is None: return` (defensive; caller gated).
  - identity: `tenant_id = self._tenant_id or ctx.tenant_id`; `session_id_eff = ctx.session_id or session_id`; either None → audit `guardrail.output.escalate.no_identity` + `GuardrailTriggered(output, block)` + `LoopCompleted(GUARDRAIL_BLOCKED)` + return (fail closed).
  - `request_id = uuid4()`; `risk_level = RiskLevel.HIGH`; `sla_deadline = now + hitl_timeout_s`; `ApprovalRequest(request_id, tenant_id, session_id_eff, requester="guardrails", risk_level, payload={"kind":"output","output_excerpt":answer_text[:200],"reason":reason,"summary":"approve delivery"}, sla_deadline, context_snapshot={"trace_id": ctx.trace_id})`.
  - `request_approval(...)` in try/except (persist-fail → audit `guardrail.output.escalate.persist_failed` + block + GUARDRAIL_BLOCKED + return).
  - audit `guardrail.output.escalate.requested` + `yield ApprovalRequested(request_id, risk_level.value, ctx)`.
  - `pending_approval = {"kind":"output","approval_request_id":str(request_id),"turn":turn_count,"response_snapshot":response_snapshot}` (no `tool_call`; carries the held answer so resume can re-emit without the LLM).
  - `async for ev in self._emit_deferred_pause(request_id=request_id, pending_approval=pending_approval, messages=messages, turn_count=turn_count, session_id=session_id_eff, audit_event_type="guardrail.output.escalate.deferred", audit_content={"request_id":str(request_id),"turn":turn_count}, ctx=ctx): yield ev`.

### 3.3 `resume()` output kind-branch + `_replay_approved_output` (US-3)
- `resume()` (after `yield ApprovalReceived`, in the kind if/elif chain, `loop.py:2376+`): add a branch parallel to input/between-turns (keep those + tool byte-identical), but TERMINAL (returns; does NOT fall through to the shared drive):
  - `elif kind == "output":` — read `snap = pending.get("response_snapshot", {})`; `answer_text = str(snap.get("answer_text", ""))`.
    - if `decision.decision != APPROVED` → audit `resume.output.{decision}` + `GuardrailTriggered(output, block, reason=...)` + `LoopCompleted(GUARDRAIL_BLOCKED, total_turns=turn_count)` + `return`.
    - else (APPROVED) → audit `resume.output.approved`; `async for ev in self._replay_approved_output(answer_text=answer_text, snap=snap, turn_count=turn_count, ctx=ctx): yield ev`; `return`.
- New `async def _replay_approved_output(self, *, answer_text: str, snap: dict[str, Any], turn_count: int, ctx: TraceContext) -> AsyncIterator[LoopEvent]` — re-emits the held terminal answer (the single place that reconstructs the withheld `LLMResponded` + `END_TURN` from the snapshot, so the field set lives in one helper, not duplicated inline):
  - `yield LLMResponded(content=answer_text, tool_calls=(), thinking=None, provider=snap.get("provider"), model=snap.get("model"), input_tokens=snap.get("input_tokens"), output_tokens=snap.get("output_tokens"), cached_input_tokens=snap.get("cached_input_tokens"), trace_context=ctx)`
  - `yield Thinking(text=answer_text, trace_context=ctx)`
  - `yield LoopCompleted(stop_reason=END_TURN.value, total_turns=turn_count, input_tokens=snap.get("input_tokens"), output_tokens=snap.get("output_tokens"), provider=snap.get("provider"), model=snap.get("model"), cached_input_tokens=snap.get("cached_input_tokens"), cache_hit_rate=snap.get("cache_hit_rate"), trace_context=ctx)`
  - (No `_run_turns` drive, no new LOOP span — no turns run; the resume re-emits a single terminal answer. Documented spike simplification: the resumed END_TURN is not nested under a fresh LOOP span; trace fidelity for the re-emit is out of scope.)
- `resume()` does NOT init/forward `skip_between_turns_once` for the output kind (it returns before the shared drive); the between-turns/input/tool drive path is unchanged.

### 3.4 What is explicitly NOT done (Slice 3 leg 3 / separate)
- No mid-thinking pause (streaming-LLM interruption — leg 3). No pausing on NON-final (TOOL_USE / HANDOFF) output ESCALATE (the per-response `_cat9_output_check` ESCALATE stays "continue"; the tool guardrail already pauses before tool exec). No subagent child-loop (Cat 11). No checkpoint-bloat fix / per-tenant capability policy / reject-path reaper (57.88 carryover ADs). The output pause carries the answer in the checkpoint snapshot (a `resume_messages`-adjacent writer — same `AD-Resume-Checkpoint-Bloat`). The pre-gate runs `check_output` a second time at 1893 on non-ESCALATE final answers (inert; accepted spike cost — not optimized via result-sharing this sprint).

### 3.5 Real output guardrail trigger + demo prompt (US-5)
- New `backend/src/agent_harness/guardrails/output/escalation_keyword_detector.py` — `class OutputKeywordEscalationGuardrail(Guardrail)`, `guardrail_type = GuardrailType.OUTPUT`, ctor takes `frozenset[str]` of trigger phrases (case-insensitive substring); `check(content, ...)` → `GuardrailResult(action=ESCALATE, reason="output matched escalation phrase", risk_level="HIGH")` when matched, else PASS. REAL detection; single responsibility; `_extract_text` mirrors `KeywordEscalationGuardrail` (str | Message | ToolCall → text). Export from `guardrails/output/__init__.py` (Day-0: confirm the package `__init__` export pattern matches `between_turns/__init__.py`).
- Handler wiring (`handler.py`): `CHAT_HITL_ESCALATE_OUTPUT_PHRASES = frozenset({"confidential"})` (deterministic; MUST NOT contain the input phrase `"approval required"` or the between-turns phrase `"checkpoint"` so those gates do not pre-empt); when `hitl_manager is not None`, `engine.register(OutputKeywordEscalationGuardrail(CHAT_HITL_ESCALATE_OUTPUT_PHRASES), priority=5)`. **The `priority=5` is load-bearing** (D-DAY0-1): the default engine already has `ToxicityDetector` (OUTPUT p10) + `SensitiveInfoDetector` (OUTPUT p20); `_run_chain` is fail-fast-first-non-PASS in ascending priority, so p5 runs the new guardrail FIRST → its ESCALATE on `confidential` wins; a non-matching answer PASSes through to the p10/p20 defaults unchanged. Extend `DEMO_SYSTEM_PROMPT`: "When asked to share something confidential, your final answer MUST contain the word 'confidential'." So `tell me something confidential` → final answer contains "confidential" → pre-gate ESCALATE → pause before `LLMResponded` → approve → answer renders.

### 3.6 Lint / neutrality / doc single-source
- `check_llm_sdk_leak` 0 (no adapter/SDK touched). `check_ap1_pipeline_disguise` green (no new loop; the pre-gate is a guardrail check before an existing emission; the helpers are tail emitters). `check_promptbuilder_usage` (AP-8) green (PromptBuilder untouched). `category-boundaries` — the new guardrail lives in Cat 9 `guardrails/output/`; no backwards import. `19-pause-resume-design.md §5` updated: "Generalized pause points" now lists shipped (input + between-turns + output) + still-deferred (mid-thinking). CHANGE-060 records it. **17.md**: `GuardrailType.OUTPUT` already single-sourced in §2.1 (no new enum value); add a 1-line note that `awaiting_approval` now ALSO originates from an output guardrail ESCALATE on a final answer (same terminal, new origin — the 3rd origin after tool + input/between-turns). No new contract enum value this sprint.

### 3.7 Validation (US-1..US-6)
- **mypy `src/ --strict` 0**; `run_all` 10/10; `black`/`isort`/`flake8` clean (run the CI-equivalent scope `flake8 src/ tests/`, NOT a path subset — Sprint 57.92 lesson).
- **pytest**: the 57.88-92 input/between-turns/tool pause-resume tests assert UNCHANGED (those paths byte-identical; the pre-gate defaults inert when the HITL wiring is absent so existing drives are unaffected). NEW unit tests: (a) output ESCALATE on a FINAL answer → pause (a single-turn loop whose final answer trips the output guardrail; checkpoint `pending_approval{kind:"output", response_snapshot.answer_text}` + `LoopCompleted(awaiting_approval)`; `LLMResponded` was NOT yielded for the held answer); (b) output resume APPROVED → re-emits `LLMResponded(answer_text)` + `LoopCompleted(END_TURN)`, NO `_run_turns` drive / NO LLM call; (c) output resume REJECTED → `GUARDRAIL_BLOCKED`, NO `LLMResponded`; (d) pre-gate does NOT fire on a NON-final response (TOOL_USE) even if its text matches (gated on `is_final_answer`); (e) pre-gate does NOT fire without the full HITL wiring (the answer renders normally + 1893 escalate-continue). NEW `OutputKeywordEscalationGuardrail` unit test (type/match/case/no-match/empty/Message-extract). Full backend suite green (NET delta documented — expect +10-12 from the new tests).
- **Drive-through** (US-6): real UI + real backend + real Azure — a `confidential`-eliciting request → final answer trips the output guardrail → pause (HITL card, **AnswerBlock absent**) → approve → answer renders; ALSO drive a reject → answer never renders + `GUARDRAIL_BLOCKED`; screenshot + observed-vs-intended diff in progress.md. (Per CLAUDE.md §Drive-Through Acceptance — the output pause is user-facing; the withhold-before-approval behavior is the leg-specific assertion that distinguishes it from a Potemkin.)

---

## 4. File Change List

| File | Change |
|------|--------|
| `backend/src/agent_harness/guardrails/output/escalation_keyword_detector.py` | **NEW** — `OutputKeywordEscalationGuardrail(Guardrail)`, `GuardrailType.OUTPUT`, ESCALATE on a configured phrase (US-5). File header. |
| `backend/src/agent_harness/guardrails/output/__init__.py` | **EDIT** — export `OutputKeywordEscalationGuardrail` (Day-0: confirm existing export style). |
| `backend/src/agent_harness/orchestrator_loop/loop.py` | **EDIT** — (US-1/US-2) NEW `_cat9_output_escalate_pause` + `_cat9_output_hitl_pause`; NEW conditional pre-gate before `LLMResponded` (gated `is_final_answer AND full deferred-HITL wiring`). (US-3) `resume()` gains a TERMINAL `output` kind-branch + `_replay_approved_output` helper; input/between-turns/tool branches + the shared `_run_turns` drive unchanged. Update file-header MHist (1-line, E501-safe ≤100). |
| `backend/src/api/v1/chat/handler.py` | **EDIT** — `CHAT_HITL_ESCALATE_OUTPUT_PHRASES` + register `OutputKeywordEscalationGuardrail` (when `hitl_manager`); extend `DEMO_SYSTEM_PROMPT` with the confidential instruction (US-5). MHist 1-line. |
| `backend/tests/unit/agent_harness/orchestrator_loop/test_loop_pause_resume.py` | **EDIT** — ADD output pause + output resume (APPROVED/REJECTED) + non-final-no-fire + no-wiring-no-fire unit tests (US-2/US-3/US-4); keep the 57.88-92 input/between-turns/tool assertions unchanged. |
| `backend/tests/unit/agent_harness/guardrails/test_output_escalation_keyword_detector.py` | **NEW** — `OutputKeywordEscalationGuardrail` unit test (match → ESCALATE / no-match → PASS / type / empty / Message-extract). |
| `backend/tests/integration/api/test_chat_pause_resume_e2e.py` | **EDIT (if feasible)** — add an output-pause integration assertion at the coroutine layer (mirror the tool/input/between-turns pause e2e). |
| frontend (`HITLTurn` / `useLoopEventStream` / `chatStore`, IF the drive-through finds a leak) | **EDIT (conditional)** — only if the AnswerBlock leaks before approval, OR the output HITL card / its Approve does not surface for a no-tool pause. Likely none (events are tool-agnostic; the answer is held back at the source = never emitted in `llm_response`). |
| `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-93-plan.md` + `-checklist.md` | **NEW** — this plan + checklist |
| `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-93/progress.md` + `retrospective.md` | **NEW** — Day 0-N progress + retro |
| `claudedocs/4-changes/feature-changes/CHANGE-060-output-guardrail-pause.md` | **NEW** — the change record (output pause point + pre-delivery gate + real output guardrail + drive-through) |
| `docs/03-implementation/agent-harness-planning/19-pause-resume-design.md` | **EDIT** — §5 list "Generalized pause points" shipped (input + between-turns + output) + still-deferred (mid-thinking); add the output pre-gate + `pending_approval.kind="output"` (held-answer snapshot) to §1/§3. |
| `docs/03-implementation/agent-harness-planning/17-cross-category-interfaces.md` | **EDIT** — §4.1/§5.3 note `awaiting_approval` now ALSO originates from an output guardrail ESCALATE on a final answer (3rd origin); NO new enum value (OUTPUT already present). |

No new DB table / no migration / no new Azure-adapter change / no ResumeService change / no `/resume` endpoint change (the output pause flows through the existing tool-agnostic resume path; ResumeService loads the latest checkpoint regardless of kind; the held answer rides in the checkpoint's `pending_approval.response_snapshot`).

---

## 5. Acceptance Criteria

- The output pause reuses the EXISTING `GuardrailType.OUTPUT` + `check_output` (NO new type/method) and the leg-1 `_emit_deferred_pause` primitive (US-1).
- A single-turn loop whose FINAL answer trips the output guardrail PAUSES **before `LLMResponded`**: checkpoint `pending_approval{kind:"output", response_snapshot.answer_text}` + `ApprovalRequested` + `LoopCompleted(awaiting_approval)`, SSE released; the held answer's `LLMResponded` was NOT yielded (US-2).
- `resume()` of an output pause: APPROVED → `_replay_approved_output` re-emits `LLMResponded(answer_text)` + `Thinking` + `LoopCompleted(END_TURN)` with NO `_run_turns` drive / NO LLM call; REJECTED → `GuardrailTriggered(output, block)` + `GUARDRAIL_BLOCKED` with NO `LLMResponded` (US-3). Input + between-turns + tool resume unchanged.
- The pre-gate is byte-inert when the deferred-HITL wiring is absent OR the response is non-final: the per-response `_cat9_output_check` (1893) + `LLMResponded` (1859) stay byte-identical; the 57.88-92 tests pass unchanged (US-4).
- A REAL `OutputKeywordEscalationGuardrail` + a DEMO_SYSTEM_PROMPT line make the pause point reachable on 主流量 (not a Potemkin) (US-5).
- `mypy --strict src/` 0; `run_all` 10/10 (LLM SDK leak 0; AP-1; AP-8); `black`/`isort`/`flake8 src/ tests/` clean; full backend pytest green (NET delta documented). `19-pause-resume-design.md §5` + 17.md §4.1/§5.3 updated; CHANGE-060 written.
- **Drive-through PASS**: real UI + real backend + real Azure — a flagged final answer → pause (HITL card, **AnswerBlock absent before approval**) → approve → answer renders; reject → answer never renders + `GUARDRAIL_BLOCKED`; screenshot + observed-vs-intended diff recorded. (No "gate-only" claimed as drive-through.)

---

## 6. Deliverables

- [ ] `OutputKeywordEscalationGuardrail` (GuardrailType.OUTPUT) + `guardrails/output/__init__.py` export (US-5)
- [ ] `_cat9_output_escalate_pause` + `_cat9_output_hitl_pause` + the conditional pre-gate before `LLMResponded` (US-1/US-2)
- [ ] `resume()` TERMINAL `output` kind-branch + `_replay_approved_output`; input/between-turns/tool kinds + shared drive unchanged (US-3)
- [ ] handler wiring (`CHAT_HITL_ESCALATE_OUTPUT_PHRASES` + register + DEMO_SYSTEM_PROMPT line) (US-5)
- [ ] NEW unit tests: output pause / resume APPROVED+REJECTED / non-final-no-fire / no-wiring-no-fire / `OutputKeywordEscalationGuardrail`; input/between-turns/tool tests unchanged; full backend pytest green (US-2/US-3/US-4/validation)
- [ ] mypy 0 + run_all 10/10 + format chain `flake8 src/ tests/` (validation)
- [ ] **drive-through PASS** (real UI + real backend + real Azure; withhold-then-deliver + reject-never-renders; screenshot + diff) (US-6)
- [ ] CHANGE-060 + `19-pause-resume-design.md §5` + 17.md §4.1/§5.3 note + progress.md + retrospective.md
- [ ] commit (Day 0-N) — push + PR user-authorized

---

## 7. Workload Calibration

Scope class: **`backend-core-loop-refactor` (0.55) — 5th data point, CAVEATED (FEATURE-ADD shape, 3rd consecutive after 57.91 input + 57.92 between-turns)**. This sprint ADDS a third pause point on 主流量 Cat 1, reusing leg-1's primitive + the EXISTING OUTPUT guardrail (no new type/method, unlike leg 2), but introduces the genuinely-new pre-delivery gating (a conditional pre-gate before `LLMResponded` + a TERMINAL resume kind that re-emits the held answer rather than driving `_run_turns`). The work splits: ~`OutputKeywordEscalationGuardrail` + export (mechanical, mirror input keyword detector, ~0.5 hr) / `_cat9_output_escalate_pause` + `_cat9_output_hitl_pause` + the pre-gate call site (~1.75 hr; mirror leg-2's hitl_pause but the call-site reorder/finality gating is new) / `resume()` output kind + `_replay_approved_output` (~1.25 hr; terminal branch, snapshot re-emit) / handler wiring + demo prompt (~0.5 hr) / tests (~2.75 hr; the withhold-before-LLMResponded + non-final-no-fire assertions are new shapes) / drive-through (~1.75 hr; withhold-then-deliver + reject, plus verifying the AnswerBlock is genuinely absent) / docs (~1 hr). Dominant costs = tests + drive-through, not the core gate. Reuse the Slice-1/2/leg-1/leg-2 class for continuity but flag the shape a FIFTH time (feature-add). **Per 57.92 retro Q2**: this is the 3rd consecutive feature-add `backend-core-loop-refactor` data point; if it ALSO lands < 0.7, that is the 3rd same-shape < 0.7 (57.91 + 57.92 + this) — propose a `loop-pause-point-feature` class split (~0.40) in this sprint's retro. **Agent-delegated: no** (parent-direct) — 主流量 loop surgery (a pre-gate that reorders delivery + a terminal resume kind) on the most-tested file + a behavior-visible feature + a drive-through is too high-blast-radius to delegate; `agent_factor = 1.0`. Does NOT extend the `AD-Calibration-AgentDelegated-WallClock-Measure` streak (parent-direct, same as 57.88/89/90/91/92).

> Bottom-up est ~9.5 hr → class-calibrated commit ~5.25 hr (mult 0.55). **Agent-delegated: no.**

If Day-1 shows the pre-delivery gate ripples wider than the pre-gate + resume kind + new output guardrail (e.g. the `LLMResponded` reorder breaks an event-ordering assertion in the Cat 9 output-guardrail tests, or the frontend leaks the answer and needs real masking work, or `classify_output` at the pre-gate point has a side effect), STOP and re-scope (split the reject-path / drive-through into a follow-up) rather than rush.

---

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| **Pause is a Potemkin — answer already rendered** (the whole point of this leg) | Day-0 confirmed the frontend renders the AnswerBlock from `llm_response` (`chatStore.ts:365`), which fires BEFORE the existing output check. The pre-gate runs BEFORE `LLMResponded` so the held answer's `llm_response` is NEVER emitted until approval → genuinely withheld. The drive-through's US-6 assertion is specifically "AnswerBlock ABSENT before approval". |
| **Resume re-runs the LLM (re-generation)** | The output kind is TERMINAL in `resume()` — it re-emits the held answer from the checkpoint snapshot and `return`s BEFORE the shared `_run_turns` drive. No `_run_turns`, no LLM call. Unit test (b) asserts NO `_run_turns` drive + NO LLM call on resume APPROVED. |
| **Pre-gate changes existing output-guardrail behavior / ordering** | The pre-gate is gated at the call site on `is_final_answer AND full deferred-HITL wiring`; when absent it is NEVER entered → `LLMResponded` (1859) + `_cat9_output_check` (1893) byte-identical. Day-0 grep the Cat 9 output-guardrail tests (53.3) + the loop tests for `llm_response`-vs-output-guardrail ordering assertions; expect none affected (the pre-gate only fires under full HITL wiring, which those tests don't set). |
| **Double `check_output` call on HITL-wired final answers** | The pre-gate calls `check_output`; on non-ESCALATE it returns and 1893 calls it again. Accepted spike cost (the demo + tests use a keyword detector → negligible; LLM-judge output detectors are not on the chat path). Documented in §3.4; result-sharing optimization deferred. The pre-gate emits NO `GuardrailTriggered` (only the pause's `ApprovalRequested`), so no double-emit. |
| **Phrase collision pre-empts the output gate** | `CHAT_HITL_ESCALATE_OUTPUT_PHRASES = {"confidential"}` MUST NOT contain the input phrase (`approval required`) or the between-turns phrase (`checkpoint`); the user prompt elicits a final answer (not an input/between-turns trigger) so the input + between-turns gates pass and the final answer's output gate fires. The demo prompt instructs the LLM to put `confidential` in the FINAL answer (not a tool call). |
| **D-DAY0-1: OUTPUT chain already has Toxicity/SensitiveInfo (BLOCK detectors)** | Register the new `OutputKeywordEscalationGuardrail` at `priority=5` (before Toxicity p10 / SensitiveInfo p20). `_run_chain` is fail-fast-first-non-PASS in ascending priority → p5 ESCALATE on `confidential` wins; `SensitiveInfoDetector` only matches system-prompt-leak patterns so `confidential` does not trip its BLOCK. Non-matching outputs still reach the p10/p20 defaults (behavior preserved). |
| **`resume()` mis-branches** (output regresses input/between-turns/tool) | Add a NEW TERMINAL `elif kind == "output":` (input + between-turns + tool branches byte-identical); default `kind="tool"` preserves 57.88-era checkpoints. Unit tests cover all 4 kinds; the unchanged input/between-turns/tool tests guard regression. |
| **Snapshot metrics fidelity** (END_TURN re-emit) | The held-answer snapshot carries input/output/cached tokens + provider/model + cache_hit_rate so the resumed `END_TURN` + `LLMResponded` carry the original per-call cost (the cost ledger is written at resume, since the paused run never emitted `LLMResponded`/`END_TURN`). Thin-spike: the snapshot is the minimal metric set; richer trace nesting (LOOP span over the re-emit) deferred. |
| **Over-abstraction** | Mirror leg-2's between-turns pattern (escalate-pre-gate + hitl_pause helper + reuse `_emit_deferred_pause`) + one new terminal-resume helper `_replay_approved_output`; ~per-kind ~30-line build, no parameterized mega-helper (Karpathy §2/§3). |
| **Drive-through non-determinism (real LLM final answer)** | The pause is BEFORE the final answer's `LLMResponded` (deterministic once the LLM puts `confidential` in the final answer). DEMO_SYSTEM_PROMPT drives the phrase like it drives echo/note tools (57.88/91/92 confirmed real-LLM instruction-following). Fall back: ALSO a scripted real-backend drive (final answer → gate → /resume) + the UI drive; record exactly what was driven. |
| **Risk Class E (stale `--reload` backend)** | Clean restart before the drive-through (kill stale uvicorn reloader+worker procs; verify :8000 OWNER is the fresh PID via `Get-NetTCPConnection -LocalPort 8000`) — the new guardrail + demo prompt are startup-wired; a stale process runs old `handler.py`. The same stale-PID footgun bit 57.91 + 57.92. |
| **Risk Class C (test isolation on the most-tested file)** | Run the full suite; module-level singleton reset fixtures already in place (`agent_harness/conftest.py`). The new guardrail is stateless. |
| **LLM-neutrality** | No adapter/SDK touched; `check_llm_sdk_leak` gates. |
| **Smuggling unrelated change** | The `loop.py` change is exactly the pre-gate + 2 new methods + `_replay_approved_output` + the resume `elif`; the input/between-turns/tool branches + the `_run_turns` drive + `_cat9_output_check` + `LLMResponded` (non-paused) stay byte-identical (diff to those blocks = 0 lines). |

---

## 9. Out of Scope (this sprint; → Slice 3 leg 3 / separate ADs)

- **Slice 3 leg 3 — mid-thinking pause** (interrupt an in-flight streaming LLM call). Hardest; separate sprint.
- **Output ESCALATE pause on NON-final responses** (TOOL_USE / HANDOFF turns whose text escalates) — the per-response `_cat9_output_check` ESCALATE stays "continue"; the tool guardrail already pauses before tool exec. A future refinement.
- **Subagent child-loop (Cat 11)** — consumes the lifecycle skeleton; distinct larger sprint.
- **Result-sharing `check_output` (avoid the pre-gate double-call)** — deferred micro-optimization; inert + negligible for keyword detectors.
- **LOOP-span trace nesting over the resume re-emit** — the output resume re-emits a single terminal answer without a fresh LOOP span; trace-tab fidelity for the re-emit is deferred.
- **`AD-Resume-Checkpoint-Bloat`** (`resume_messages` + the new `response_snapshot` → `messages` table + checkpoint TTL) — the output pause adds another checkpoint-payload writer; same open AD.
- **`AD-Resume-Tenant-Capability-Policy`** (per-tenant escalation config — now also per-tenant output phrases) — separate AD.
- **`AD-Resume-Reject-Path`** (reject-then-resume / checkpoint reaper) — separate AD; an output reject leaves a dangling checkpoint the same way.
