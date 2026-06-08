# CHANGE-060: Output-Guardrail ESCALATE Pre-Delivery Pause Point (地基 A Slice 3)

**Date**: 2026-06-09
**Sprint**: 57.93
**Scope**: Cat 1 (Orchestrator Loop) + Cat 9 (Guardrails) + Cat 7 (State checkpoint) — cross-cutting Cat 12 events

## Problem / Goal

The durable HITL pause-resume foundation (地基 A) had pause points for tool calls (57.88), loop-start input (57.91 leg 1), and between-turns (57.92 leg 2) — but a guardrail flagging the **final answer itself** could not pause; the output guardrail's ESCALATE action just emitted `GuardrailTriggered` and continued. This sprint adds the **output-guardrail ESCALATE pause point**: when an OUTPUT guardrail flags a FINAL answer ESCALATE, the loop pauses for human approval BEFORE delivering it.

The hard part — absent in legs 1/2 — is **pre-delivery gating**. The frontend renders the answer from the `llm_response` SSE event (`chatStore.ts:365`), which fires at `loop.py:1859`, BEFORE the existing per-response output check at `loop.py:1893`. A pause at the existing check point would be a Potemkin (the answer is already on screen). The pause must precede `LLMResponded`.

## Root Cause / Design

Reuses the EXISTING `GuardrailType.OUTPUT` + `GuardrailEngine.check_output` (NO new type/method, unlike leg 2's `BETWEEN_TURNS`) and the leg-1 `_emit_deferred_pause` primitive.

- **Pre-gate** (`_cat9_output_escalate_pause` + `_cat9_output_hitl_pause`): inserted in `_run_turns` right after `parse(...)`, BEFORE `yield LLMResponded`. Gated at the call site on `is_final_answer AND guardrail_engine AND hitl_manager AND hitl_deferred AND checkpointer AND reducer` — so non-HITL / non-final paths are byte-unchanged (the per-response `_cat9_output_check` at 1893 stays intact for BLOCK/sanitize/reroll/escalate-continue/tripwire). On ESCALATE it builds an output `ApprovalRequest` + `ApprovalRequested` + `_emit_deferred_pause(kind="output")` carrying the **held-answer snapshot** (`response_snapshot`: answer_text + per-call tokens/provider/model/cache_hit_rate/total_tokens). The `LoopCompleted(awaiting_approval)` makes the caller `return` — the held answer's `LLMResponded` is never reached.
- **resume() output kind** (TERMINAL): unlike input/between-turns/tool (which drive the shared `_run_turns`), the output kind re-emits the held answer and returns BEFORE the drive — APPROVED → `_replay_approved_output` re-emits `LLMResponded(answer_text)` + `Thinking` + `LoopCompleted(END_TURN)` from the snapshot (no LLM re-call); REJECTED → `GuardrailTriggered(output, block)` + `GUARDRAIL_BLOCKED`.
- **Trigger** (Cat 9): a real `OutputKeywordEscalationGuardrail(GuardrailType.OUTPUT)` (mirror of the input keyword guardrail) registered in the chat handler at **priority=5** (D-DAY0-1: the chat OUTPUT chain already has Toxicity p10 + SensitiveInfo p20 via `build_default_guardrail_engine`; `_run_chain` is fail-fast-first-non-PASS, so p5 wins; `confidential` does not trip SensitiveInfo's system-prompt-leak patterns → no BLOCK collision). `DEMO_SYSTEM_PROMPT` extended so the LLM puts "confidential" in a final answer when asked.

## Solution (files)

| File | Change |
|------|--------|
| `agent_harness/guardrails/output/escalation_keyword_detector.py` | NEW — `OutputKeywordEscalationGuardrail` (OUTPUT, ESCALATE on phrase) |
| `agent_harness/guardrails/output/__init__.py` | export it |
| `agent_harness/orchestrator_loop/loop.py` | `_cat9_output_escalate_pause` + `_cat9_output_hitl_pause` + pre-gate before `LLMResponded` + `resume()` output kind-branch + `_replay_approved_output` |
| `api/v1/chat/handler.py` | `CHAT_HITL_ESCALATE_OUTPUT_PHRASES={"confidential"}` + register at priority=5 + DEMO_SYSTEM_PROMPT line |
| `tests/unit/.../test_loop_pause_resume.py` | +5 output pause/resume/non-final/no-wiring tests |
| `tests/unit/.../test_output_escalation_keyword_detector.py` | NEW — 7 detector tests |

No DB table / migration / ResumeService / `/resume` endpoint change (the output pause rides the existing tool-agnostic resume path; the held answer rides in the checkpoint `pending_approval.response_snapshot`).

## Verification

- **Unit**: pytest **2266 passed / 4 skipped** (baseline 2254 + 12). Key: `test_output_escalate_pauses_before_delivery` (NO `LLMResponded` before the pause) · `test_resume_output_approved_replays_answer` (re-emit, no `_run_turns` drive, no LLM call) · `test_resume_output_rejected_blocks` · `test_output_pre_gate_skips_non_final` · `test_output_pre_gate_inert_without_hitl`. The 57.88-92 input/between-turns/tool tests UNCHANGED.
- **Gates**: mypy `src --strict` 0/351 · `run_all` 10/10 (AP-1 / AP-8 / LLM SDK leak 0 / event-schema sync) · `black`/`isort` clean · `flake8 src tests` clean.
- **Drive-through PASS** (real UI + real backend + real Azure gpt-5.2, dan@acme.com / acme-prod, chat-v2 real_llm): "tell me something confidential" → pause (HITL card `tool: —`, Inspector "no blocks yet" = **answer withheld**, no `llm_response` in trace) → Approve (`/decide`+`/resume`) → held answer re-emitted + renders + `end_turn` → ; Reject (`/decide` REJECTED, no `/resume`) → answer never renders. Screenshots in `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-93/artifacts/`. Zero frontend change.

## Impact

Backend-only (Cat 1 + Cat 9 + Cat 7). The pre-gate is purely additive — inert without the full deferred-HITL wiring or on a non-final response. `awaiting_approval` now has a 3rd guardrail origin (after tool + input/between-turns). Known limitations (plan §9, 57.88 carryover): reject leaves a dangling checkpoint (`AD-Resume-Reject-Path`); the snapshot rides in the checkpoint (`AD-Resume-Checkpoint-Bloat`); per-tenant output phrases (`AD-Resume-Tenant-Capability-Policy`).
