# CHANGE-058: Generalized Pause Primitive + Input-ESCALATE Pause Point

**Date**: 2026-06-08
**Sprint**: 57.91 (地基 A Slice 3 leg 1)
**Scope**: Cat 1 (Orchestrator Loop) + Cat 9 (Guardrails) + Cat 7 (checkpoint payload)

## Problem

After Slice 1+2 (57.89/57.90) `run()` and `resume()` share one re-enterable `_run_turns`, but the durable-pause MECHANISM was still tool-shaped: the only thing that could pause was a tool-call ESCALATE (`_cat9_hitl_branch` deferred branch), and `resume()` hard-read `pending_approval["tool_call"]` and always executed a pending tool before continuing. There was no way to pause at any other point (input / between-turns / mid-thinking) — the "Generalized pause points" open invariant in `19-pause-resume-design.md §5`.

## Root Cause

The durable-pause tail (checkpoint `pending_approval` + audit + `LoopCompleted(awaiting_approval)`) was inlined inside the tool-call branch, coupling "pause" to "a ToolCall". `resume()` assumed every pause re-executes a tool.

## Solution

Slice 3 leg 1 (scope locked via AskUserQuestion to **generalized primitive + input-ESCALATE**; between-turns / mid-thinking deferred to legs 2/3):

1. **Generalized pause primitive** — extracted `AgentLoopImpl._emit_deferred_pause(*, request_id, pending_approval, messages, turn_count, session_id, audit_event_type, audit_content, ctx)`: the durable-pause tail decoupled from what is being approved. The tool deferred branch (`_cat9_hitl_branch`) routes through it (`pending_approval` gains a `"kind":"tool"` discriminator); behavior byte-identical.
2. **Input-ESCALATE pause point** — `_cat9_input_check` (now threaded `session_id`/`messages`/`turn_count`) gained an ESCALATE branch → new `_cat9_input_hitl_pause` builds an input `ApprovalRequest` + emits `ApprovalRequested` + calls `_emit_deferred_pause` with an **input-kind** `pending_approval` (no `tool_call`). ESCALATE WITHOUT the deferred HITL wiring fails closed to BLOCK (an ESCALATE that cannot pause must not proceed).
3. **resume() kind-branch** — `resume()` branches on `pending_approval["kind"]` (default `"tool"`): input-kind APPROVED drives `_run_turns` directly (NO tool exec — the approved input proceeds to the first LLM turn); input-kind REJECTED → `GuardrailTriggered(input, block)` + `GUARDRAIL_BLOCKED`. Tool-kind path unchanged.
4. **Real trigger** — new `KeywordEscalationGuardrail` (Cat 9 `guardrails/input/`, `GuardrailType.INPUT`, ESCALATE on a configured phrase) wired into the chat handler (`CHAT_HITL_ESCALATE_INPUT_PHRASES = {"approval required"}`, registered when `hitl_manager` present) — reachable on 主流量, not a Potemkin.

**Files**: `backend/src/agent_harness/orchestrator_loop/loop.py`; `backend/src/agent_harness/guardrails/input/escalation_keyword_detector.py` (new) + `input/__init__.py`; `backend/src/api/v1/chat/handler.py`; tests `test_loop_pause_resume.py` (+4) + `test_escalation_keyword_detector.py` (new, 7). No DB / migration / contract change (`pending_approval` is internal JSONB; `kind` is additive). No ResumeService / `/resume` endpoint change.

## Verification

- Unit: `pytest tests/unit/agent_harness/orchestrator_loop/test_loop_pause_resume.py tests/unit/agent_harness/guardrails/test_escalation_keyword_detector.py` (input pause / input resume APPROVED+REJECTED / ESCALATE-no-HITL-BLOCK + 7 guardrail).
- Full backend: **2243 passed / 4 skipped** (baseline 2232 → +11, NO test deleted); mypy `src --strict` 0 (347 files); `run_all` 10/10 (AP-1 / LLM SDK leak 0 / AP-8 / event-schema sync); black/isort/flake8 clean.
- **Drive-through PASS** (real chat-v2 UI + clean backend PID 50548 + real Azure gpt-5.2): `approval required: …` → pause (HITL card `tool: —` = input-kind, `loop_end awaiting_approval turns=0`, no LLM call) → Approve → `Decision: APPROVED` → resume → "Paris" (`end_turn`). No frontend change needed. Evidence: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-91/artifacts/`. (Risk Class E: a stale pre-57.91 listener served the first attempt's old code — caught + cleanly restarted; see progress.md Day 3.)

## Impact

Backend Cat 1 + Cat 9 feature add. The generalized primitive is the foundation for Slice 3 legs 2/3 (between-turns / mid-thinking) and an output-guardrail ESCALATE pause. `19-pause-resume-design.md §5` "Generalized pause points" split into shipped (input-ESCALATE) + still-deferred (between-turns / mid-thinking). Frontend unchanged (the HITL card / Approve / resume are tool-agnostic). The 57.88 carryover ADs (checkpoint-bloat / per-tenant capability / reject-reaper) remain open (the input pause adds another `resume_messages` writer + would also want per-tenant escalation phrases).
