# Sprint 57.92 Plan — Between-Turns Guardrail ESCALATE Pause Point (地基 A Slice 3, leg 2)

**Purpose**: 地基 A Slice 3 builds GENERALIZED pause points on the shared re-enterable loop (`_run_turns`, Slice 1+2) using the `_emit_deferred_pause` primitive (Slice 3 leg 1 / Sprint 57.91). Leg 1 shipped the FIRST new pause point — input-guardrail ESCALATE (pauses BEFORE the first LLM call). This sprint = **Slice 3 leg 2**: the SECOND new pause point — **between-turns guardrail ESCALATE**: a NEW Cat 9 guardrail runs at the TOP of each loop iteration after the first completed turn (`turn_count > 0`, BEFORE the next turn's LLM call) on the just-completed turn's accumulated output; when it returns `ESCALATE` (with deferred HITL wiring) the loop pauses BETWEEN turns, awaiting human approval to continue, and `resume()` continues to the next turn's LLM call (NO pending tool, NO re-generation — the next turn hadn't run). This reuses `_emit_deferred_pause` (leg 1's primitive) byte-for-byte; it adds a new `GuardrailType.BETWEEN_TURNS` + `check_between_turns` so it does NOT double-fire with the existing per-LLM-response `_cat9_output_check` (which runs the OUTPUT chain). The pause checkpoint carries `pending_approval.kind = "between_turns"`; `resume()` learns the between-turns kind (mirror of leg 1's input kind, differing only in a `skip_between_turns_once` flag passed to the shared `_run_turns` drive so the same boundary doesn't re-escalate on re-entry). **This is a feature add** (a new user-visible pause point) on 主流量 Cat 1 — so the 57.88-91 pause-resume tests are kept UNCHANGED (the input + tool paths are untouched) and a NEW between-turns-pause / between-turns-resume unit test + a **drive-through** (real UI + real backend + real Azure LLM: a multi-turn loop whose just-completed turn output trips the between-turns guardrail → pause → approve → answer) are the acceptance. **Record = CHANGE-059**; no new design note (continuation of the 57.88 pause-resume domain — update `19-pause-resume-design.md §5`: the "Generalized pause points" deferred line splits further into shipped (input + between-turns) + still-deferred (mid-thinking)).

**Category / Scope**: Cat 1 (Orchestrator Loop — `_cat9_between_turns_check` + `_cat9_between_turns_hitl_pause`; a new gate at the `_run_turns` loop top; `resume()` between-turns kind-branch + `skip_between_turns_once` flag) + Cat 9 (Guardrails — a new `GuardrailType.BETWEEN_TURNS` + `GuardrailEngine.check_between_turns` + a real `BetweenTurnsKeywordGuardrail` that ESCALATEs on a configured trigger; engine wiring) + Cat 7 (the checkpoint `pending_approval.kind = "between_turns"` — JSONB, no migration) + Cat 12 (the between-turns pause emits the same LOOP-span / `awaiting_approval` terminator + `ApprovalRequested`). Phase 57.92

**Created**: 2026-06-08
**Status**: Draft (scope below; code execution gated on Day-0 GO)
**Source**: Sprint 57.91 carryover (`next-phase-candidates.md` — Slice 3 leg 2 between-turns pause) + `19-pause-resume-design.md §5` Open Invariant "Generalized pause points" + AskUserQuestion 2026-06-08 (trigger = **between-turns guardrail ESCALATE**, scope = **leg 2 only**; mid-thinking deferred to leg 3, subagent child-loop a separate sprint).

> **Modification History**
> - 2026-06-08: Initial creation — between-turns guardrail ESCALATE pause point on the `_emit_deferred_pause` primitive (leg 1); new `GuardrailType.BETWEEN_TURNS` + loop-top gate + resume between-turns kind + skip-once

---

## 0. Background

Slice 1+2 (57.89/57.90) made `run()` and `resume()` share ONE re-enterable per-turn loop (`_run_turns`, `loop.py:1261`). Slice 3 leg 1 (57.91) extracted the generalized durable-pause tail `_emit_deferred_pause(...)` (`loop.py:1037`) — checkpoint `pending_approval` + audit + `LoopCompleted(awaiting_approval)` — and built the FIRST new pause point on it: input-guardrail ESCALATE (`_cat9_input_check` ESCALATE → `_cat9_input_hitl_pause` → `pending_approval.kind = "input"`; `resume()` learned the no-pending-tool path). "Generalized pause points" still has TWO deferred legs: **between-turns** (this sprint) and **mid-thinking** (leg 3). This sprint delivers the between-turns pause point — the SECOND concrete pause point, reusing leg 1's primitive + resume machinery with the smallest possible delta.

### Ground truth re-confirmed (Day-0 head-start — this plan's Day-0 verify)

Re-confirmed at this plan's Day 0 (Prong 1 path + Prong 2 content greps on `loop.py` / `engine.py` / `_abc.py` / `handler.py`):

- **The `_emit_deferred_pause` primitive (leg 1) is kind-agnostic** (`loop.py:1037-1086`): it takes `pending_approval` (any `kind`) + `messages` + `turn_count` + `session_id` + audit fields, persists the checkpoint via `_emit_state_checkpoint`, audits, and terminates `awaiting_approval`. A between-turns pause reuses it verbatim with a `between_turns`-kind `pending_approval`.
- **The per-turn loop body** (`_run_turns`, `loop.py:1282` `while True`): top runs the pre-LLM termination checks (`max_turns` / `tokens` / `cancellation`) then the Cat 4 compaction check, then the TURN span opens for the LLM call. `_cat9_output_check` (`loop.py:1668`) runs once PER LLM response (mid-turn, on `parsed.text`, BEFORE the stop_reason terminator) via the OUTPUT chain. `turn_count += 1` is the LAST statement of the while-body (`loop.py:2050`) — so at the TOP of an iteration `turn_count = K` is the turn ABOUT to run, and `turn_count > 0` means ≥1 turn already completed (its output fully appended to `messages`). **The loop top (after termination checks, before the LLM call) is the clean between-turns seam**: the prior turn's output is complete in `messages`, the about-to-run turn's LLM has NOT been called → a resume continues by making that call (no re-generation / re-escalation of an already-produced output, which a mid-`_cat9_output_check` pause WOULD suffer).
- **`GuardrailType`** (`_abc.py:31-34`) has exactly INPUT / OUTPUT / TOOL; `GuardrailEngine._chains` is `{gt: [] for gt in GuardrailType}` (`engine.py:80-82`) so a NEW enum value auto-creates its chain; `check_input/output/tool_call` each call `_run_chain(<type>, …)` (`engine.py:117-142`). A new `BETWEEN_TURNS` value + a `check_between_turns` mirror is the no-double-fire path (the existing per-response output check stays on the OUTPUT chain; the between-turns gate runs only the BETWEEN_TURNS chain).
- **`resume()`** (`loop.py:2053-2292`) reads `pending_approval`, reads the decision (non-blocking `get_decision`), yields `ApprovalReceived`, then branches on `pending_approval["kind"]` (leg 1): `"input"` → no tool, fall through; else (`"tool"`) → build + exec the pending tool. BOTH kinds then drive the SHARED `_run_turns` inside a fresh `metrics_acc` + LOOP span (`loop.py:2259-2292`). A between-turns kind is the input kind PLUS a `skip_between_turns_once=True` passed to the shared drive.
- **`_run_turns` takes raw per-run locals** (`session_id` / `messages` / `turn_count` / `tokens_used` / `metrics_acc` / `ctx` / `root_ctx`) — adding a keyword `skip_between_turns_once: bool = False` is additive; the `run()` call site passes the default, the `resume()` between-turns drive passes `True`.
- **The chat handler** (`handler.py`) wires `echo_tool` as a TOOL-ESCALATE (`CHAT_HITL_ESCALATE_TOOLS = {"echo_tool"}`, `handler.py:121`) + (leg 1) `KeywordEscalationGuardrail` on `CHAT_HITL_ESCALATE_INPUT_PHRASES = {"approval required"}` (`handler.py:131`). `echo_tool` is the ONLY deterministic demo tool (DEMO_SYSTEM_PROMPT drives it). **`echo_tool` CANNOT reach a between-turns boundary**: it tool-escalates at turn 0's tool check (tool-kind pause), and a tool-kind resume execs the pre-approved tool OUTSIDE the loop then re-enters `_run_turns` at `turn_count=0` → the re-entered turn 0 produces the final answer → `turn_count` never reaches 1 → the between-turns gate (`turn_count > 0`) never fires. **A non-escalate deterministic demo tool is required** so turn 0 runs end-to-end INSIDE `_run_turns`, `turn_count` increments to 1, and the gate fires at the top of turn 1.

---

## 1. Sprint Goal

Ship the between-turns guardrail ESCALATE pause point on the `_emit_deferred_pause` primitive: (1) add a new `GuardrailType.BETWEEN_TURNS` + `GuardrailEngine.check_between_turns` (mirror of `check_output`); (2) add `_cat9_between_turns_check` (runs `check_between_turns` on the just-completed turn's output; ESCALATE + deferred wiring → `_cat9_between_turns_hitl_pause`; ESCALATE-without-HITL → fail closed BLOCK; BLOCK → terminate; PASS → continue) + a NEW gate at the TOP of the `_run_turns` while-loop (gated `turn_count > 0 and not skip_between_turns_once`); (3) `_cat9_between_turns_hitl_pause` builds a between-turns `ApprovalRequest` + emits `ApprovalRequested` + calls `_emit_deferred_pause` with `pending_approval.kind = "between_turns"` (no `tool_call`); (4) `resume()` gains a between-turns kind-branch (mirror of input kind: APPROVED → no tool, audit, fall through; REJECTED → block) and drives the shared `_run_turns` with `skip_between_turns_once=True` so the same boundary doesn't re-escalate on re-entry; (5) wire a REAL `BetweenTurnsKeywordGuardrail` (`GuardrailType.BETWEEN_TURNS`, ESCALATE on a configured phrase) into the chat handler + a deterministic non-escalate demo tool (`note_tool`) + a DEMO_SYSTEM_PROMPT line so the pause point is reachable on 主流量. **This is a deliberate feature add** on 主流量 Cat 1: the 57.88-91 input/tool pause-resume tests stay UNCHANGED + NEW between-turns-pause + between-turns-resume (APPROVED/REJECTED) + ESCALATE-no-HITL-BLOCK + `BetweenTurnsKeywordGuardrail` unit tests, and a **drive-through** (real UI + real backend + real Azure gpt-5.2) walks a multi-turn loop whose completed-turn output trips the between-turns guardrail → pause (HITL card) → approve → answer. Out of scope: Slice 3 leg 3 (mid-thinking pause); subagent child-loop (Cat 11); output-guardrail ESCALATE pause; the 57.88 carryover ADs.

---

## 2. User Stories

- **US-1 (between-turns gate on the primitive)** — As the loop maintainer, I want a between-turns pause to reuse the leg-1 `_emit_deferred_pause` primitive (one durable-pause tail, no second copy) so the pause mechanism stays single-source. → `_cat9_between_turns_hitl_pause` builds the kind-specific `ApprovalRequest` + `ApprovalRequested`, then calls `_emit_deferred_pause` with a `between_turns`-kind `pending_approval`.
- **US-2 (between-turns ESCALATE pause)** — As an approver, I want the loop to PAUSE between turns when a guardrail flags the just-completed turn's output ESCALATE, so I can approve/reject CONTINUING the loop before the next LLM turn — not have it silently proceed. → a new gate at the `_run_turns` loop top (`turn_count > 0`) runs `_cat9_between_turns_check`; ESCALATE + deferred wiring → pause (checkpoint `pending_approval{kind:"between_turns"}` + `ApprovalRequested` + `awaiting_approval`).
- **US-3 (between-turns resume, no re-generation)** — As the resumed loop, I want a between-turns pause to resume by continuing to the next turn's LLM call (NOT re-running the prior turn, NOT executing a tool), so the approved continuation proceeds exactly as it would have un-paused. → `resume()` between-turns kind: APPROVED → drive the shared `_run_turns` with `skip_between_turns_once=True` (the gate skips the just-approved boundary once); REJECTED → `GuardrailTriggered(between_turns, block)` + `GUARDRAIL_BLOCKED`. Input + tool kinds unchanged.
- **US-4 (fail-closed without HITL)** — As the loop, I want a between-turns ESCALATE WITHOUT the deferred HITL wiring to fail closed to BLOCK (terminate, not silent-proceed), so a missing approval surface never lets a flagged continuation through. → `_cat9_between_turns_check`: `ESCALATE && deferred wiring → pause; elif action != PASS (incl. ESCALATE-without-HITL, BLOCK) → terminate GUARDRAIL_BLOCKED`.
- **US-5 (no double-fire + reachable on 主流量)** — As the user, I want the between-turns check to be its own guardrail type (not re-fire the existing per-response output check) AND reachable through the real chat path with a REAL guardrail + a real multi-turn flow (not a Potemkin). → a new `GuardrailType.BETWEEN_TURNS` + `check_between_turns`; a `BetweenTurnsKeywordGuardrail` registered in the chat handler; a deterministic non-escalate demo tool (`note_tool`) + a DEMO_SYSTEM_PROMPT line so the real LLM produces a completed-turn whose output trips the between-turns guardrail.
- **US-6 (drive-through acceptance)** — As the user, I want the between-turns pause to actually work end-to-end through the real chat UI + backend + LLM. → drive-through: a `note`-style request → turn 0 runs `note_tool` (executes, no tool-escalate) → top of turn 1 between-turns guardrail ESCALATEs on the note output → pause (HITL card, no answer yet) → approve → resume → the LLM answers; screenshot + observed-vs-intended diff in progress.md; fix any frontend gap that blocks the between-turns HITL card / its Approve.

---

## 3. Technical Specifications

### 3.0 Architecture (the second pause point)

```
_run_turns while-body (Slice 2)                _run_turns while-body (Slice 3 leg 2)
  while True:                                    while True:
    termination checks (turns/tokens/cancel)       termination checks (turns/tokens/cancel)
    (no between-turns gate)                         NEW between-turns gate:
                                                       if turn_count > 0 and not skip_once:
                                                         async for ev in _cat9_between_turns_check(
                                                             messages, ctx, turn_count, session_id):
                                                           yield ev; LoopCompleted → return
                                                       skip_once = False   # consume after 1st iter
    compaction check                                compaction check
    TURN span → LLM call → parse → output check     TURN span → LLM call → parse → output check
    stop_reason / classify / tool dispatch          stop_reason / classify / tool dispatch
    turn_count += 1                                 turn_count += 1

_cat9_between_turns_check (NEW, mirror of _cat9_input_check):
   content = last assistant/tool message text (just-completed turn output)
   g = check_between_turns(content)
   ESCALATE + hitl_manager + hitl_deferred + checkpointer + reducer
        → _cat9_between_turns_hitl_pause → _emit_deferred_pause(kind="between_turns")
   action != PASS (BLOCK / ESCALATE-no-HITL / …) → GUARDRAIL_BLOCKED terminate

resume(): kind = pending["kind"]                  (leg 1 had: "input" | "tool")
   "between_turns": (not appr) block / (appr) no tool → skip_between_turns_once = True
   "input":         (unchanged)
   "tool":          (unchanged)
   → SHARED drive _run_turns(skip_between_turns_once=<flag>)
```

The `_run_turns` drive (fresh `metrics_acc` + LOOP span, Slice 2) is SHARED by all kinds; only the per-kind prep + the `skip_between_turns_once` flag differ. The input/tool branches + the `_cat9_output_check` per-response check stay byte-identical.

### 3.1 New `GuardrailType.BETWEEN_TURNS` + `check_between_turns` (US-5)
- `_abc.py`: add `BETWEEN_TURNS = "between_turns"` to `GuardrailType` (4th value). `_chains` default factory auto-includes it; no exhaustiveness `match` exists on `GuardrailType` (Day-0 grep confirms — else fix).
- `engine.py`: add `async def check_between_turns(self, content, *, trace_context=None) -> GuardrailResult: return await self._run_chain(GuardrailType.BETWEEN_TURNS, content, trace_context=trace_context)` (mirror `check_output`). Default PASS when chain empty (backward-compat no-op).

### 3.2 `_cat9_between_turns_check` + loop-top gate (US-2/US-4)
- New `async def _cat9_between_turns_check(self, *, messages: list[Message], ctx: TraceContext, turn_count: int, session_id: UUID) -> AsyncIterator[LoopEvent]`:
  - `content = self._latest_output_text(messages)` — the content of the last assistant/tool message (the just-completed turn's output); `""` fallback when none.
  - `if self._guardrail_engine is not None:` → `g = await check_between_turns(content, trace_context=ctx)`.
    - `if g.action == ESCALATE and self._hitl_manager and self._hitl_deferred and self._checkpointer and self._reducer:` → `async for ev in self._cat9_between_turns_hitl_pause(output_excerpt=content, reason=g.reason or "escalated", ctx=ctx, session_id=session_id, messages=messages, turn_count=turn_count): yield ev` → `return` (terminal — the pause yields `LoopCompleted`).
    - `elif g.action != PASS:` → audit `guardrail.between_turns.block` + `GuardrailTriggered(between_turns, action=g.action.value/"block")` + `LoopCompleted(GUARDRAIL_BLOCKED)` + `return` (covers BLOCK + ESCALATE-without-HITL = fail closed, US-4).
  - Tripwire: out of scope here (the between-turns check is escalation-focused; tripwire stays on input/output).
- New gate in `_run_turns` while-loop top, immediately AFTER the cancellation termination check (`loop.py:~1307`) and BEFORE the compaction check:
  ```
  if turn_count > 0 and not skip_between_turns_once:
      between_turns_terminated = False
      async for ev in self._cat9_between_turns_check(
          messages=messages, ctx=ctx, turn_count=turn_count, session_id=session_id):
          yield ev
          if isinstance(ev, LoopCompleted):
              between_turns_terminated = True
      if between_turns_terminated:
          return
  skip_between_turns_once = False
  ```
  `skip_between_turns_once = False` runs every iteration (consumes the skip after the FIRST re-entered iteration; a fresh `run()` enters with it already False).
- New helper `_latest_output_text(messages) -> str`: return the `content` of the last message whose role is `assistant` or `tool` and whose content is truthy, else `""`. (Module-level pure function OR a small static method — Day-1 pick the simplest; no state.)

### 3.3 `_cat9_between_turns_hitl_pause` (US-1/US-2)
- New `async def _cat9_between_turns_hitl_pause(self, *, output_excerpt: str, reason: str, ctx, session_id, messages, turn_count) -> AsyncIterator[LoopEvent]` — a near-verbatim mirror of `_cat9_input_hitl_pause` (`loop.py:631-749`):
  - `if self._hitl_manager is None: return` (defensive; caller gated).
  - identity: `tenant_id = self._tenant_id or ctx.tenant_id`; `session_id_eff = ctx.session_id or session_id`; either None → audit `guardrail.between_turns.escalate.no_identity` + `GuardrailTriggered(between_turns, block)` + `LoopCompleted(GUARDRAIL_BLOCKED)` + return (fail closed).
  - `request_id = uuid4()`; `risk_level = RiskLevel.HIGH`; `sla_deadline = now + hitl_timeout_s`; `ApprovalRequest(request_id, tenant_id, session_id_eff, requester="guardrails", risk_level, payload={"kind":"between_turns","output_excerpt":output_excerpt[:200],"reason":reason,"summary":"approve continuation"}, sla_deadline, context_snapshot={"trace_id": ctx.trace_id})`.
  - `request_approval(...)` in try/except (persist-fail → audit `guardrail.between_turns.escalate.persist_failed` + block + GUARDRAIL_BLOCKED + return).
  - audit `guardrail.between_turns.escalate.requested` + `yield ApprovalRequested(request_id, risk_level.value, ctx)`.
  - `pending_approval = {"kind":"between_turns","approval_request_id":str(request_id),"turn":turn_count}` (no `tool_call`).
  - `async for ev in self._emit_deferred_pause(request_id=request_id, pending_approval=pending_approval, messages=messages, turn_count=turn_count, session_id=session_id_eff, audit_event_type="guardrail.between_turns.escalate.deferred", audit_content={"request_id":str(request_id),"turn":turn_count}, ctx=ctx): yield ev`.

### 3.4 `resume()` between-turns kind-branch + `_run_turns` skip flag (US-3)
- `_run_turns` signature: add `skip_between_turns_once: bool = False` (keyword). `run()` call site (`loop.py:~1245`, after `_cat9_input_check`) passes nothing (default False). The gate (§3.2) reads + consumes it.
- `resume()` (after `yield ApprovalReceived`, `loop.py:2147+`): add a branch parallel to the input branch (keep input + tool branches byte-identical):
  - `elif kind == "between_turns":` — if `decision.decision != APPROVED` → audit `resume.between_turns.{decision}` + `GuardrailTriggered(between_turns, block)` + `LoopCompleted(GUARDRAIL_BLOCKED)` + return; else (APPROVED) → audit `resume.between_turns.approved`; NO tool exec; set `skip_between_turns_once = True`.
  - Initialize `skip_between_turns_once = False` before the kind-branch; the shared drive passes it: `self._run_turns(..., skip_between_turns_once=skip_between_turns_once)`.
  - Default `kind="tool"` + the input branch + the tool branch are unchanged; only the new `elif` + the one extra kwarg on the drive call.

### 3.5 Real between-turns guardrail trigger + non-escalate demo tool (US-5)
- New `backend/src/agent_harness/guardrails/between_turns/keyword_detector.py` — `class BetweenTurnsKeywordGuardrail(Guardrail)`, `guardrail_type = GuardrailType.BETWEEN_TURNS`, ctor takes `frozenset[str]` of trigger phrases (case-insensitive substring); `check(content, ...)` → `GuardrailResult(action=ESCALATE, reason="output matched between-turns escalation phrase", risk_level="HIGH")` when matched, else PASS. REAL detection; single responsibility; `_extract_text` mirrors `KeywordEscalationGuardrail` (str | Message | ToolCall → text). New `between_turns/__init__.py` exporting it.
- New deterministic non-escalate demo tool `note_tool` (mirror echo_tool registration; NOT in `CHAT_HITL_ESCALATE_TOOLS`) — takes `text`, returns `text` (so its result is deterministic + matchable). Registered into the same tool registry/executor the chat handler builds. Day-0: locate echo_tool's real registration site (`make_default_executor` chain) + register `note_tool` beside it.
- Handler wiring (`handler.py`): `CHAT_HITL_ESCALATE_BETWEEN_TURNS_PHRASES = frozenset({"checkpoint"})` (deterministic, MUST NOT contain the input-escalate phrase `"approval required"` so the input gate doesn't pre-empt it); when `hitl_manager is not None`, `engine.register(BetweenTurnsKeywordGuardrail(CHAT_HITL_ESCALATE_BETWEEN_TURNS_PHRASES))`. Extend `DEMO_SYSTEM_PROMPT`: "When asked to 'note' some text, you MUST call the `note_tool` function with that text." So `note the word checkpoint, then confirm` → turn 0 `note_tool("checkpoint")` (executes) → top of turn 1 between-turns gate matches "checkpoint" → pause.

### 3.6 What is explicitly NOT done (Slice 3 leg 3 / separate)
- No mid-thinking pause (streaming-LLM interruption — leg 3). No output-guardrail ESCALATE pause (the per-response `_cat9_output_check` ESCALATE stays "continue" — out of scope; the between-turns gate is the distinct new surface). No subagent child-loop (Cat 11). No checkpoint-bloat fix / per-tenant capability policy / reject-path reaper (57.88 carryover ADs). The between-turns guardrail checks ONLY the last assistant/tool message (not a full-transcript accumulation or a turn-delta tracker) — a deliberate thin-spike simplification.

### 3.7 Lint / neutrality / doc single-source
- `check_llm_sdk_leak` 0 (no adapter/SDK touched). `check_ap1_pipeline_disguise` green (no new loop; the gate is a guardrail check at the existing `while True` top, the helper is a tail emitter). `check_promptbuilder_usage` (AP-8) green (PromptBuilder untouched). `category-boundaries` — the new guardrail lives in Cat 9 `guardrails/between_turns/`; no backwards import. `19-pause-resume-design.md §5` updated: "Generalized pause points" deferred line splits into shipped (input + between-turns) + still-deferred (mid-thinking). CHANGE-059 records it. **17.md**: `GuardrailType` is single-sourced in §2.1 — add `BETWEEN_TURNS` there (a new contract enum value) + a 1-line note that `awaiting_approval` now also originates from a between-turns guardrail ESCALATE (same terminal, new origin). This is the one genuine contract-surface touch (a new enum value) — minimal, additive.

### 3.8 Validation (US-1..US-6)
- **mypy `src/ --strict` 0**; `run_all` 10/10; `black`/`isort`/`flake8` clean.
- **pytest**: the 57.88-91 input/tool pause-resume tests assert UNCHANGED (input/tool paths byte-identical; the new `skip_between_turns_once` defaults False so existing drives are unaffected). NEW unit tests: (a) between-turns ESCALATE → pause (a 2-turn loop via a non-escalate tool; checkpoint `pending_approval{kind:"between_turns"}` + `LoopCompleted(awaiting_approval)` at the top of turn 1; the turn-1 LLM was NOT called); (b) between-turns resume APPROVED → drives `_run_turns` to `end_turn`, gate skipped (no re-escalate), NO extra pause; (c) between-turns resume REJECTED → `GUARDRAIL_BLOCKED`; (d) between-turns ESCALATE-without-HITL → terminate GUARDRAIL_BLOCKED (fail closed, US-4). NEW `BetweenTurnsKeywordGuardrail` unit test (type/match/case/no-match/empty/Message-extract). Full backend suite green (NET delta documented — expect +9-11 from the new tests).
- **Drive-through** (US-6): real UI + real backend + real Azure — `note`-request → turn 0 `note_tool` executes → top of turn 1 between-turns ESCALATE → pause (HITL card, no answer) → approve → resume → answer; screenshot + observed-vs-intended diff in progress.md. (Per CLAUDE.md §Drive-Through Acceptance — the between-turns pause is user-facing.)

---

## 4. File Change List

| File | Change |
|------|--------|
| `backend/src/agent_harness/guardrails/_abc.py` | **EDIT** — add `BETWEEN_TURNS = "between_turns"` to `GuardrailType` (US-5). MHist 1-line. |
| `backend/src/agent_harness/guardrails/engine.py` | **EDIT** — add `check_between_turns()` mirror of `check_output` (US-5). MHist 1-line. |
| `backend/src/agent_harness/guardrails/between_turns/keyword_detector.py` | **NEW** — `BetweenTurnsKeywordGuardrail(Guardrail)`, `GuardrailType.BETWEEN_TURNS`, ESCALATE on a configured phrase (US-5). File header. |
| `backend/src/agent_harness/guardrails/between_turns/__init__.py` | **NEW** — export `BetweenTurnsKeywordGuardrail`. |
| `backend/src/agent_harness/orchestrator_loop/loop.py` | **EDIT** — (US-1/US-2) NEW `_cat9_between_turns_check` + `_cat9_between_turns_hitl_pause` + `_latest_output_text`; NEW gate at the `_run_turns` loop top (`turn_count > 0 and not skip_between_turns_once`). (US-3) `_run_turns` gains `skip_between_turns_once: bool = False`; `resume()` gains a `between_turns` kind-branch + passes the flag to the shared drive; `run()` call site unchanged (default). Update file-header MHist (1-line, E501-safe). |
| `backend/src/api/v1/chat/handler.py` | **EDIT** — `CHAT_HITL_ESCALATE_BETWEEN_TURNS_PHRASES` + register `BetweenTurnsKeywordGuardrail`; extend `DEMO_SYSTEM_PROMPT` with the `note_tool` instruction (US-5). `note_tool` needs NO handler registration (auto via `make_default_executor`; auto-PASS since not in `CHAT_HITL_ESCALATE_TOOLS`). MHist 1-line. |
| `backend/src/agent_harness/tools/note_tool.py` | **NEW** — `NOTE_TOOL_SPEC` + `note_handler` (deterministic `text`→`text`; mirror `echo_tool.py`). Day-0 resolved (D-DAY0-1). |
| `backend/src/business_domain/_register_all.py` | **EDIT** — register `NOTE_TOOL_SPEC` + `handlers["note_tool"] = note_handler` beside echo (`:237-238`). |
| `backend/tests/unit/agent_harness/orchestrator_loop/test_loop_pause_resume.py` | **EDIT** — ADD between-turns pause + between-turns resume (APPROVED/REJECTED) + ESCALATE-no-HITL-BLOCK unit tests (US-2/US-3/US-4); keep the 57.88-91 input/tool assertions unchanged. |
| `backend/tests/unit/agent_harness/guardrails/test_between_turns_keyword_detector.py` | **NEW** — `BetweenTurnsKeywordGuardrail` unit test (match → ESCALATE / no-match → PASS). |
| `backend/tests/integration/api/test_chat_pause_resume_e2e.py` | **EDIT (if feasible)** — add a between-turns-pause integration assertion at the coroutine layer (mirror the tool/input pause e2e). |
| frontend (`HITLTurn` / `useLoopEventStream` / `chatStore`, IF the drive-through finds a gap) | **EDIT (conditional)** — only if the between-turns HITL card / its Approve does not surface for a no-tool pause. Likely none (events are tool-agnostic; proven leg 1). |
| `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-92-plan.md` + `-checklist.md` | **NEW** — this plan + checklist |
| `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-92/progress.md` + `retrospective.md` | **NEW** — Day 0-N progress + retro |
| `claudedocs/4-changes/feature-changes/CHANGE-059-between-turns-pause.md` | **NEW** — the change record (between-turns pause point + new GuardrailType + non-escalate demo tool + drive-through) |
| `docs/03-implementation/agent-harness-planning/19-pause-resume-design.md` | **EDIT** — §5 split "Generalized pause points" into shipped (input + between-turns) + still-deferred (mid-thinking); add the between-turns gate + `pending_approval.kind="between_turns"` to §1/§3. |
| `docs/03-implementation/agent-harness-planning/17-cross-category-interfaces.md` | **EDIT** — §2.1 add `GuardrailType.BETWEEN_TURNS`; §4.1/§5.3 note `awaiting_approval` now also originates from a between-turns guardrail ESCALATE (new contract enum value + new origin). |

No new DB table / no migration / no new Azure-adapter change / no ResumeService change / no `/resume` endpoint change (the between-turns pause flows through the existing tool-agnostic resume path; ResumeService loads the latest checkpoint regardless of kind).

---

## 5. Acceptance Criteria

- A new `GuardrailType.BETWEEN_TURNS` + `GuardrailEngine.check_between_turns` exist; the between-turns gate runs ONLY the BETWEEN_TURNS chain (no double-fire with the per-response `_cat9_output_check` OUTPUT chain) (US-5).
- A 2-turn loop whose just-completed turn output trips the between-turns guardrail PAUSES at the TOP of the next turn (before its LLM call): checkpoint `pending_approval{kind:"between_turns"}` + `ApprovalRequested` + `LoopCompleted(awaiting_approval)`, SSE released; the next turn's LLM was NOT called (US-2).
- A between-turns ESCALATE WITHOUT deferred HITL wiring fails closed to BLOCK (`GUARDRAIL_BLOCKED`), not silent-proceed (US-4).
- `resume()` of a between-turns pause: APPROVED → drives `_run_turns` to `end_turn` with the gate skipped once (no re-escalate, no second pause on the same boundary, NO tool exec); REJECTED → `GuardrailTriggered(between_turns, block)` + `GUARDRAIL_BLOCKED` (US-3). Input + tool resume unchanged.
- A REAL `BetweenTurnsKeywordGuardrail` + a non-escalate `note_tool` + a DEMO_SYSTEM_PROMPT line make the pause point reachable on 主流量 (not a Potemkin) (US-5).
- `mypy --strict src/` 0; `run_all` 10/10 (LLM SDK leak 0; AP-1; AP-8); `black`/`isort`/`flake8` clean; full backend pytest green (NET delta documented). `19-pause-resume-design.md §5` + 17.md §2.1 updated; CHANGE-059 written.
- **Drive-through PASS**: real UI + real backend + real Azure — `note`-request → turn 0 `note_tool` → between-turns pause (HITL card) → approve → answer; screenshot + observed-vs-intended diff recorded. (No "gate-only" claimed as drive-through.)

---

## 6. Deliverables

- [ ] `GuardrailType.BETWEEN_TURNS` + `check_between_turns` (US-5)
- [ ] `_cat9_between_turns_check` + `_cat9_between_turns_hitl_pause` + `_latest_output_text` + the `_run_turns` loop-top gate (US-1/US-2/US-4)
- [ ] `_run_turns` `skip_between_turns_once` flag + `resume()` between-turns kind-branch; input/tool kinds unchanged (US-3)
- [ ] `BetweenTurnsKeywordGuardrail` + `note_tool` + handler wiring + DEMO_SYSTEM_PROMPT line (US-5)
- [ ] NEW unit tests: between-turns pause / resume APPROVED+REJECTED / ESCALATE-no-HITL BLOCK / BetweenTurnsKeywordGuardrail; input/tool-path tests unchanged; full backend pytest green (US-2/US-3/US-4/validation)
- [ ] mypy 0 + run_all 10/10 + format chain (validation)
- [ ] **drive-through PASS** (real UI + real backend + real Azure; screenshot + diff) (US-6)
- [ ] CHANGE-059 + `19-pause-resume-design.md §5` + 17.md §2.1 note + progress.md + retrospective.md
- [ ] commit (Day 0-N) — push + PR user-authorized

---

## 7. Workload Calibration

Scope class: **`backend-core-loop-refactor` (0.55) — 4th data point, CAVEATED (FEATURE-ADD shape, same as 57.91 leg 1; different from Slice 1 pure-extraction + Slice 2 behavior-rewire)**. This sprint ADDS a second pause point + a new GuardrailType + a new engine method + a new guardrail + a non-escalate demo tool + handler wiring — a feature on 主流量 Cat 1, leveraging leg 1's primitive + resume machinery. The work splits: ~new GuardrailType + check_between_turns (mechanical, ~0.5 hr) / `_cat9_between_turns_check` + `_cat9_between_turns_hitl_pause` + `_latest_output_text` + loop-top gate (~1.5 hr; mirror of leg-1 input) / `resume()` between-turns kind + skip flag (~0.75 hr) / `BetweenTurnsKeywordGuardrail` + `note_tool` + handler wiring + demo prompt (~1.5 hr) / tests (~2.5 hr) / drive-through (~1.5 hr; the non-escalate-tool multi-turn flow is slightly less deterministic than leg-1's input phrase) / docs (~1 hr). Dominant costs = tests + drive-through, not the core gate. Reuse the Slice-1/2/leg-1 class for continuity but flag the shape a FOURTH time (feature-add). **Per 57.91 retro Q2**: this is the 4th `backend-core-loop-refactor` data point and the 2nd consecutive feature-add shape; if it ALSO lands < 0.7 (3rd feature-add < 0.7 would be 57.91 + this; the matrix lower-trigger is 3 consecutive same-shape < 0.7), propose a `loop-pause-point-feature` class split in retro. **Agent-delegated: no** (parent-direct) — 主流量 loop surgery (a new loop-top gate + resume kind-branch) touching the most-tested file + a behavior-visible feature + a drive-through is too high-blast-radius to delegate; `agent_factor = 1.0`. Does NOT extend the `AD-Calibration-AgentDelegated-WallClock-Measure` streak (parent-direct, same as 57.88/89/90/91).

> Bottom-up est ~9.75 hr → class-calibrated commit ~5.4 hr (mult 0.55). **Agent-delegated: no.**

If Day-1 shows the between-turns gate ripples wider than the loop-top + resume + new guardrail type (e.g. the `note_tool` registration needs executor surgery, or the new GuardrailType breaks an exhaustiveness check, or the frontend needs real work), STOP and re-scope (split the demo-tool / drive-through into a follow-up) rather than rush.

---

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| **Between-turns boundary unreachable in the drive-through** (echo_tool tool-escalates → never reaches turn 1) | Day-0 verified: echo_tool tool-escalates + a tool resume execs outside the loop → no turn-1 boundary. Add a non-escalate `note_tool` + a DEMO_SYSTEM_PROMPT line so turn 0 runs end-to-end INSIDE `_run_turns`, `turn_count`→1, gate fires at top of turn 1. The between-turns phrase (`checkpoint`) MUST NOT contain the input phrase (`approval required`) so the input gate doesn't pre-empt. |
| **Resume re-escalates the same boundary** (infinite pause) | `skip_between_turns_once=True` passed by the between-turns resume → the gate skips the just-approved boundary for the FIRST re-entered iteration, then the flag is consumed (`skip_between_turns_once = False` each iteration). Unit test (b) asserts NO second pause on resume APPROVED. |
| **Mid-`_cat9_output_check` pause would re-generate the LLM output** (why the gate is at the loop top, not the output check) | The gate is at the loop TOP (before the next turn's LLM call) so resume continues by making that call (never run) — no re-generation. The per-response `_cat9_output_check` ESCALATE stays "continue" (untouched). |
| **New `GuardrailType` value breaks an exhaustiveness check / `len(GuardrailType)` assertion** | Day-0 grep all `GuardrailType` usages (`match`, `len(`, dict-literal-over-types, frontend mirror). `_chains` factory auto-includes it. Fix any exhaustive site; expect none (engine is the only structural consumer). |
| **Double-fire with the per-response output check** | The between-turns gate runs `check_between_turns` (BETWEEN_TURNS chain) ONLY; the per-response check runs `check_output` (OUTPUT chain). Distinct chains → no double-fire. The new guardrail registers as BETWEEN_TURNS type. |
| **`resume()` mis-branches** (between-turns regresses input/tool) | Add a NEW `elif kind == "between_turns":` (input + tool branches byte-identical); default `kind="tool"` preserves 57.88-era checkpoints. Unit tests cover all 3 kinds APPROVED+REJECTED; the unchanged input/tool tests guard regression. |
| **Over-abstraction** | Mirror leg-1's input pattern (check + hitl_pause helper + reuse `_emit_deferred_pause`); ~per-kind ~30-line build, no parameterized mega-helper (Karpathy §2/§3). `_latest_output_text` is a tiny pure helper. |
| **Drive-through non-determinism (real LLM + a tool call)** | The pause is BEFORE turn 1's LLM call (deterministic on the note phrase in turn 0's tool result), so the PAUSE is deterministic once the LLM calls `note_tool`. The DEMO_SYSTEM_PROMPT drives `note_tool` like it drives echo_tool (57.88/91 confirmed real-LLM tool-calling works). Fall back: ALSO a scripted real-backend drive (2-turn state → gate → /resume) + attempt the UI drive; record exactly what was driven. |
| **Risk Class E (stale `--reload` backend)** | Clean restart before the drive-through (kill stale uvicorn reloader+worker procs; verify :8000 OWNER is the fresh PID via `Get-NetTCPConnection -LocalPort 8000`) — the new guardrail + `note_tool` + demo prompt are startup-wired; a stale process runs old `handler.py`. |
| **Risk Class C (test isolation on the most-tested file)** | Run the full suite; module-level singleton reset fixtures already in place (`agent_harness/conftest.py`). The new guardrail + `note_tool` are stateless. |
| **LLM-neutrality** | No adapter/SDK touched; `check_llm_sdk_leak` gates. |
| **Smuggling unrelated change** | The `loop.py` change is exactly the new gate + 2 new methods + `_latest_output_text` + the resume `elif` + the one `_run_turns` kwarg; the input/tool branches + the `_run_turns` drive + `_cat9_output_check` stay byte-identical (diff to those blocks = 0 lines). |

---

## 9. Out of Scope (this sprint; → Slice 3 leg 3 / separate ADs)

- **Slice 3 leg 3 — mid-thinking pause** (interrupt an in-flight streaming LLM call). Hardest; separate sprint.
- **Output-guardrail ESCALATE pause** (the per-response `_cat9_output_check` ESCALATE → pause) — distinct from the between-turns gate; the per-response ESCALATE stays "continue". Possible future leg.
- **Subagent child-loop (Cat 11)** — consumes the lifecycle skeleton; distinct larger sprint.
- **Full-transcript / turn-delta between-turns content** — this sprint checks ONLY the last assistant/tool message (thin-spike simplification); a richer accumulation/delta tracker is a future refinement.
- **`AD-Resume-Checkpoint-Bloat`** (`resume_messages` → `messages` table + checkpoint TTL) — the between-turns pause adds another `resume_messages` writer; same open AD.
- **`AD-Resume-Tenant-Capability-Policy`** (per-tenant escalation config — now also per-tenant between-turns phrases) — separate AD.
- **`AD-Resume-Reject-Path`** (reject-then-resume / checkpoint reaper) — separate AD; a between-turns reject leaves a dangling checkpoint the same way.
