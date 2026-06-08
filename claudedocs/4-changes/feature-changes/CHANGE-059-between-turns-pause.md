# CHANGE-059: Between-Turns Guardrail ESCALATE Pause Point (地基 A Slice 3 leg 2)

**Date**: 2026-06-08
**Sprint**: 57.92
**Scope**: Cat 1 (Orchestrator Loop) + Cat 9 (Guardrails) + Cat 7 (checkpoint payload) + Cat 12 (terminator/spans)
**Type**: Feature add (second generalized pause point) — CHANGE
**Record**: CHANGE-059

## Problem / Motivation

Slice 3 leg 1 (Sprint 57.91) extracted the generalized durable-pause tail `_emit_deferred_pause(...)` and shipped the FIRST new pause point on it — input-guardrail ESCALATE (pauses BEFORE the first LLM call). "Generalized pause points" still had two deferred legs: **between-turns** and **mid-thinking**. This change delivers the between-turns pause point — a pause BETWEEN completed turns (after ≥1 turn, before the next LLM call), so a human can approve/reject CONTINUING the loop based on the just-completed turn's output, rather than only at input or at a tool call.

## Solution

A NEW `GuardrailType.BETWEEN_TURNS` + `GuardrailEngine.check_between_turns` (mirror of `check_output`) — a distinct chain so the between-turns gate does NOT double-fire with the existing per-LLM-response output check (which runs the OUTPUT chain).

In `loop.py` (`_run_turns`), a NEW gate at the loop TOP (after the termination checks, before the next turn's LLM call), guarded by `turn_count > 0 and not skip_between_turns_once`:
- `_cat9_between_turns_check` runs `check_between_turns` on the just-completed turn's output (`_latest_output_text` = the last truthy assistant/tool message). PASS → continue; ESCALATE + deferred HITL wiring → `_cat9_between_turns_hitl_pause` (build a between-turns `ApprovalRequest`, emit `ApprovalRequested`, pause via `_emit_deferred_pause` with `pending_approval.kind = "between_turns"`, no `tool_call`); any other non-PASS (BLOCK, or ESCALATE-without-HITL) → fail closed to `GUARDRAIL_BLOCKED`.
- `_run_turns` gained `skip_between_turns_once: bool = False` (consumed after the first iteration).
- `resume()` gained an `elif kind == "between_turns"` branch (APPROVED → no tool exec + `skip_between_turns_once=True`; REJECTED → `GuardrailTriggered(between_turns, block)` + `GUARDRAIL_BLOCKED`) and passes the flag to the shared `_run_turns` drive so the just-approved boundary does not re-escalate on re-entry.

The seam is the loop TOP (not the mid-turn `_cat9_output_check`) so a resume continues by making the next turn's LLM call — which has NOT run — with NO re-generation (a mid-output-check pause would re-call the LLM on resume and re-generate, breaking fidelity).

Reachable on 主流量: a real `BetweenTurnsKeywordGuardrail` (Cat 9 `guardrails/between_turns/`) + a non-escalate `note_tool` (`agent_harness/tools/note_tool.py`, registered in `_register_all.py`) + a `DEMO_SYSTEM_PROMPT` line. `echo_tool` cannot reach a between-turns boundary (it tool-escalates at turn 0, and a tool resume execs the pending tool OUTSIDE the loop → `turn_count` never reaches 1); `note_tool` executes end-to-end INSIDE the loop so the gate fires at the top of turn 1.

The input/tool pause branches + the `_run_turns` drive + `_cat9_output_check` are byte-unchanged.

## Files

- `backend/src/agent_harness/guardrails/_abc.py` — `GuardrailType.BETWEEN_TURNS`
- `backend/src/agent_harness/guardrails/engine.py` — `check_between_turns`
- `backend/src/agent_harness/guardrails/between_turns/{__init__,keyword_detector}.py` — NEW `BetweenTurnsKeywordGuardrail`
- `backend/src/agent_harness/tools/note_tool.py` — NEW non-escalate demo tool
- `backend/src/business_domain/_register_all.py` — register `note_tool`
- `backend/src/agent_harness/orchestrator_loop/loop.py` — `_latest_output_text` + `_cat9_between_turns_check` + `_cat9_between_turns_hitl_pause` + loop-top gate + `_run_turns` skip flag + `resume()` between-turns kind
- `backend/src/api/v1/chat/handler.py` — `CHAT_HITL_ESCALATE_BETWEEN_TURNS_PHRASES` + register the guardrail + `DEMO_SYSTEM_PROMPT` note_tool line
- `backend/tests/unit/agent_harness/orchestrator_loop/test_loop_pause_resume.py` (+4) + `backend/tests/unit/agent_harness/guardrails/test_between_turns_keyword_detector.py` (NEW, 7)
- `docs/.../19-pause-resume-design.md §5` + `17-cross-category-interfaces.md §2.1`

## Verification

- pytest **2254 passed / 4 skipped** (baseline 2243 → +11: 4 between-turns loop pause/resume/skip/block + 7 guardrail); 57.88-91 input/tool cases unchanged.
- mypy `src --strict` **0** (350 files); run_all **10/10** (LLM SDK leak 0; AP-1; AP-8; event-schema sync — no new events); black/isort/flake8 clean.
- **Drive-through PASS** (real chat-v2 UI + real backend + real Azure gpt-5.2): `note the word checkpoint` → turn 0 `note_tool` exec (output `checkpoint`) → top-of-turn-1 `approval_requested risk=HIGH` → pause (HITL card `tool: —`, `loop_end stop=awaiting_approval turns=1`, no answer) → Approve (`Decision: APPROVED`) → resume → `end_turn` answer "checkpoint" (no re-pause). Screenshots in `sprint-57-92/artifacts/`.

## Impact

Backend (Cat 1 + Cat 9 + Cat 7 checkpoint payload). No DB table / no migration / no ResumeService change / no `/resume` endpoint change / NO frontend change (the between-turns pause flows through the existing tool-agnostic resume + HITL-card path). One contract-surface touch: a new `GuardrailType.BETWEEN_TURNS` enum value (17.md §2.1, additive). Mid-thinking pause (leg 3), output-guardrail ESCALATE pause, and subagent child-loop remain out of scope.
