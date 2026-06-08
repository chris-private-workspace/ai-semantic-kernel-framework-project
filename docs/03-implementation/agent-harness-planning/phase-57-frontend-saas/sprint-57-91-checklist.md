# Sprint 57.91 — Checklist (Generalized Pause Primitive + Input-ESCALATE Pause Point — 地基 A Slice 3 leg 1)

**Plan**: [`sprint-57-91-plan.md`](./sprint-57-91-plan.md)
**Created**: 2026-06-08
**Status**: Draft (code gated on Day-0 GO)

> Rule: only `[ ]` → `[x]`; never delete unchecked items; defer with `🚧 + reason`.
> CHANGE (feature add — new pause point) → CHANGE-058 record; no new design note (update `19-pause-resume-design.md §5`). Gate = full backend pytest green (NET delta documented) + **drive-through PASS** (input pause is user-facing). Locked scope: generalized primitive + input-ESCALATE only (between-turns / mid-thinking deferred to legs 2/3).

---

## Day 0 — Plan-vs-Repo Verify + Branch

### 0.1 Three-prong Day-0 verify
- [x] **Prong 1 (path)**: confirmed — `run()` input-check `loop.py:1032` (inside LOOP span) / `_cat9_input_check` `:545` (no ESCALATE, no session_id/messages) / `_cat9_hitl_branch` deferred tail `:799-839` / `resume()` `:1848` (`pending_tc` build `:1907`) / shared `_run_turns` drive `:2009-2042` / `_emit_state_checkpoint` `:2044`. Guardrails: `GuardrailAction.ESCALATE` `_abc.py:43`, `Guardrail` ABC `:57` (`check(*, content, trace_context)`), `GuardrailResult.risk_level` Literal `:54`, `GuardrailType.INPUT` `:32`, `engine.register/check_input` `engine.py:84/117`, input guardrails `input/pii_detector.py`+`jailbreak_detector.py`. Handler `CHAT_HITL_ESCALATE_TOOLS` `:119` + `build_default_guardrail_engine` `:294` + `ToolGuardrail` reg `:299` + `hitl_deferred` `:331`; same builder used by ResumeService. (progress.md Day-0 Prong 1)
- [x] **Prong 2 (content)**: confirmed — (a) `check_input`→`_run_chain(INPUT)` carries ESCALATE (not tool-gated); (b) `resume()` builds `pending_tc` unconditionally `:1907` → move into tool-kind branch; (c) ResumeService tool-agnostic (no change); (d) `_emit_state_checkpoint` stores `resume_messages` only when `pending_approval` set (input pause inherits no-bloat); (e) frontend HITL card renders from `ApprovalRequested`+`awaiting_approval` (eyeball input card copy in drive-through, not trusting Explore). (progress.md Day-0 Prong 2)
- [x] **Prong 3 (schema)**: N/A — no DB/migration/ORM change; `pending_approval.kind` additive JSONB. (progress.md Day-0)
- [x] **Baseline capture**: baseline = main `1cf0ceb4` (57.90 merged): expected pytest 2232 / mypy 0/346 / run_all 10/10 / Vitest 772; re-confirm Day-1 before editing
- [x] Catalogue D-DAY0-1..4 drift findings in progress.md; **go/no-go = GO** (primitive seam + input-pause path reachable end-to-end, no ResumeService/endpoint/migration change; all 4 drifts anticipated by plan §3)

### 0.2 Branch
- [x] Branch `feature/sprint-57-91-generalized-pause-input-escalate` from `main` (`1cf0ceb4`)
- [ ] plan + checklist + progress committed (Day-0 commit)

---

## Day 1 — Generalized primitive + input ESCALATE branch (US-1/US-2/US-4/US-5)

### 1.1 `_emit_deferred_pause` primitive + tool reroute (US-1)
- [ ] **NEW `_emit_deferred_pause(...)`** — the durable-pause tail (checkpoint `pending_approval` + audit + `LoopCompleted(awaiting_approval)`); caller pre-builds the ApprovalRequest + yields ApprovalRequested
  - DoD: helper exists; signature `(*, request_id, pending_approval, messages, turn_count, session_id, audit_event_type, audit_content, ctx)`
- [ ] **Route `_cat9_hitl_branch` deferred tail through it** — `pending_approval` gains `"kind":"tool"`; behavior byte-identical
  - Verify: `pytest test_loop_pause_resume.py -q` tool-path cases pass UNCHANGED; grep the deferred tail now calls `_emit_deferred_pause`
- [ ] **mypy clean** on the helper + reroute — `mypy src/agent_harness/orchestrator_loop/loop.py` Success

### 1.2 `_cat9_input_check` ESCALATE branch (US-2/US-4)
- [ ] **Extend `_cat9_input_check` signature** (`session_id`/`messages`/`turn_count`) + update `run()` call site (`:1032`)
- [ ] **ESCALATE→input-pause branch** — build input `ApprovalRequest` + `ApprovalRequested` + `_emit_deferred_pause(input-kind)`; no-identity / persist-fail → BLOCK (mirror tool path)
  - DoD: `pending_approval = {"kind":"input", "approval_request_id":…, "turn":…}` (no `tool_call`)
- [ ] **ESCALATE-without-HITL → BLOCK** (fail closed, US-4) — `elif action != PASS` covers BLOCK/SANITIZE/REROLL + ESCALATE-no-HITL

### 1.3 `KeywordEscalationGuardrail` + handler wiring (US-5)
- [ ] **NEW `guardrails/input/escalation_keyword_detector.py`** — `KeywordEscalationGuardrail(Guardrail)`, `GuardrailType.INPUT`, ESCALATE on configured phrase; PASS otherwise; file header
  - Verify: `mypy` clean; export from `input/__init__.py` if package re-exports
- [ ] **Handler wiring** (`api/v1/chat/handler.py`) — `CHAT_HITL_ESCALATE_INPUT_PHRASES` + `engine.register(KeywordEscalationGuardrail(...))` when `hitl_manager` present

---

## Day 2 — resume() kind-branch + tests (US-3)

### 2.1 `resume()` kind-branch (US-3)
- [ ] **Branch on `pending_approval["kind"]`** (default `"tool"`) after `ApprovalReceived`
  - input-kind: APPROVED → audit + fall through to shared `_run_turns` drive (NO tool exec); REJECTED → `GuardrailTriggered(input, block)` + `GUARDRAIL_BLOCKED`
  - tool-kind: move `pending_tc` build here; existing exec/append (unchanged)
  - DoD: the shared `metrics_acc` + LOOP span + `_run_turns` drive reached by both kinds
- [ ] **mypy clean** on the restructured `resume()` — `mypy src/` 0/346

### 2.2 Unit tests (US-2/US-3/US-4)
- [ ] **Input pause** — input ESCALATE → `ApprovalRequested` + checkpoint `pending_approval{kind:"input"}` + `LoopCompleted(awaiting_approval)`; assert NO LLM call happened
- [ ] **Input resume APPROVED** — drives `_run_turns` to `end_turn`, NO `ToolCall*` events (no tool exec)
- [ ] **Input resume REJECTED** — `GuardrailTriggered(input, block)` + `GUARDRAIL_BLOCKED`
- [ ] **ESCALATE-without-HITL → BLOCK** (fail closed, US-4)
- [ ] **`KeywordEscalationGuardrail` unit test** (`tests/unit/agent_harness/guardrails/test_escalation_keyword_detector.py`) — match→ESCALATE / no-match→PASS
- [ ] **Tool-path tests UNCHANGED** — `pytest test_loop_pause_resume.py -q` 57.88-90 cases pass without edit (byte-identical tool deferred behavior)
- [ ] **Span-tree + event-schema guards** — `run_all` 10/10 (incl. `check_event_schema_sync` + AP-1)

---

## Day 3 — Full regression + drive-through (US-6) + CHANGE-058

### 3.1 Full gate sweep
- [ ] **Full backend pytest green (NET delta documented)** — baseline 2232 → +N (the new input + guardrail tests); NO test deleted
  - Verify: `python -m pytest -q`
- [ ] **mypy 0 + run_all 10/10 + format chain** — mypy `src/` 0; run_all 10/10 (LLM SDK leak 0; AP-1; AP-8; event-schema sync); black/isort/flake8 clean

### 3.2 Drive-through (US-6 — input pause is user-facing)
- [ ] **Clean backend restart (Risk Class E)** — `dev.py restart backend` kill stale `--reload` workers → fresh process (committed code incl. the new guardrail); real Azure gpt-5.2 from repo-root `.env`
- [ ] **Drive the input pause through real UI + real backend + real Azure** — trigger-phrase input → pause (HITL card, no answer yet) → approve → resume → LLM answers the approved input
  - Walk every control: the input HITL card appears; its Approve drives `/resume`; the answer renders. If the card / Approve does NOT surface for a no-tool pause, fix the frontend (in scope, US-6).
  - Evidence: `artifacts/sprint-57-91-input-pause-drivethrough.png` + observed-vs-intended table in progress.md Day 3.
- [ ] **Frontend gap (if any) fixed** — record whether a frontend change was needed (expected: none; events are tool-agnostic)

### 3.3 CHANGE-058 + design-note update
- [ ] `claudedocs/4-changes/feature-changes/CHANGE-058-generalized-pause-input-escalate.md` written
- [ ] `19-pause-resume-design.md §5` — "Generalized pause points" split into shipped (input-ESCALATE + `_emit_deferred_pause` primitive) + still-deferred (between-turns / mid-thinking); add `pending_approval.kind` to §1/§3
- [ ] `17-cross-category-interfaces.md` — 1-line note `awaiting_approval` now also originates from an input-guardrail ESCALATE (no new contract)

---

## Day 4 — Closeout

### 4.1 Closeout
- [ ] Full validation (parent re-verified): pytest 2232+N / mypy 0/346 / run_all 10/10 / tool-path tests unchanged / **drive-through PASS** (screenshot + observed-vs-intended table)
- [ ] progress.md (Day 0-4) + retrospective.md (Q1-Q7)
- [ ] Calibration: `backend-core-loop-refactor` 0.55 (3rd data point, caveated — feature-add shape) + `agent_factor` 1.0 (parent-direct); record `calibration-log.md §3`; carryover (Slice 3 legs 2/3 / subagent child-loop / 57.88 ADs) → next-phase-candidates.md
- [ ] MEMORY.md pointer + `project_phase57_91_*.md` subfile + CLAUDE.md lean (Current Sprint row + Last Updated) + CHANGE-058 + `19-pause-resume-design.md §5` updated
- [ ] commit (Day 0-N) + push + PR — **push + PR pending user authorization**
