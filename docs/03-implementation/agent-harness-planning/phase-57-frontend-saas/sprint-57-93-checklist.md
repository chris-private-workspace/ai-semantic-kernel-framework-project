# Sprint 57.93 — Checklist (Output-Guardrail ESCALATE Pause Point — 地基 A Slice 3 output-guardrail leg)

**Plan**: [`sprint-57-93-plan.md`](./sprint-57-93-plan.md)
**Created**: 2026-06-08
**Status**: Draft (code gated on Day-0 GO)

> Rule: only `[ ]` → `[x]`; never delete unchecked items; defer with `🚧 + reason`.
> CHANGE (feature add — third pause point) → CHANGE-060 record; no new design note (update `19-pause-resume-design.md §5`). Gate = full backend pytest green (NET delta documented) + **drive-through PASS** (output pause is user-facing; the leg-specific assertion is the answer is WITHHELD before approval). Locked scope: output-guardrail ESCALATE on a FINAL answer only (non-final / mid-thinking deferred; subagent child-loop a separate sprint).

---

## Day 0 — Plan-vs-Repo Verify + Branch

### 0.1 Three-prong Day-0 verify
- [x] **Prong 1 (path)**: confirmed — `_emit_deferred_pause` `:1038` / `_cat9_output_check` `:1089` (called `:1893`, OUTPUT chain) / `_cat9_between_turns_hitl_pause` `:1240` (mirror template for the new hitl_pause) / `_run_turns` `:1460` (`while True` `:1482`; LLM call+token locals `:1832-1848`; parse `:1851`; `LLMResponded` `:1859`; output check call `:1893`; stop_reason `:1903`; classify `:1921`) / `run()` `:1360` / `resume()` kind-branch `:2372` + shared drive `:2502-2552`. `engine.py` `check_output` `:135` / `_run_chain` `:102` (fail-fast-first-non-PASS). `_abc.py` `GuardrailType` `:35` (OUTPUT already present — NO new type). `handler.py` guardrail build `:325` (`build_default_guardrail_engine`) + wiring `:330-348` / `CHAT_HITL_ESCALATE_*` `:129/:139/:150` / `DEMO_SYSTEM_PROMPT` `:110`. `_factory.py:54-68` default engine (PII p10 + Jailbreak p20 input; Toxicity p10 + SensitiveInfo p20 output). Mirror templates: `guardrails/input/escalation_keyword_detector.py` `KeywordEscalationGuardrail` (new output keyword detector) + `_cat9_between_turns_hitl_pause` (new hitl_pause). (progress.md Day-0 Prong 1)
- [x] **Prong 2 (content)**: confirmed — (a) frontend renders AnswerBlock from `llm_response` `chatStore.ts:365` (BEFORE the output check → pre-delivery gate must precede `LLMResponded`); (b) `_input_tokens`/`_output_tokens`/`_cached_input_tokens`/`_provider` (`:1832-1838`) + `response.model` + `metrics_acc.cache_hit_rate` in scope at parse `:1851` (snapshot capture); (c) `should_terminate_by_stop_reason` + `classify_output` + `OutputType` used at `:1903`/`:1921` → imported + pure (re-callable at the pre-gate); (d) **DRIFT D-DAY0-1**: chat OUTPUT chain is **NON-empty** — `build_default_guardrail_engine()` (`_factory.py:67-68`) registers `ToxicityDetector` (p10) + `SensitiveInfoDetector` (p20); RESOLVED by registering the new guardrail at `priority=5` (fail-fast-first-non-PASS → ESCALATE on `confidential` wins; SensitiveInfo only matches system-prompt-leak so no BLOCK collision); (e) `_cat9_output_check` ESCALATE branch = `GuardrailTriggered`+continue (stays untouched); (f) `resume()` kind-branch shape + `_run_turns` shared drive (output kind must RETURN before it). (progress.md Day-0 Prong 2 + D-DAY0-1)
- [x] **Prong 2.5 (event-ordering / test assertions)**: SAFE — the existing `test_loop_pause_resume.py` fake ESCALATE guardrails are `GuardrailType.TOOL` (`:178`) + `GuardrailType.BETWEEN_TURNS` (`:912`); NONE is OUTPUT. Their test loops build minimal engines (single fake guardrail), so the OUTPUT chain is empty → `check_output` → PASS → the new pre-gate no-ops even under full HITL wiring. No `llm_response`-vs-output-guardrail ordering assertion is touched (the pre-gate fires only when an OUTPUT-chain guardrail ESCALATEs on a FINAL answer under full HITL wiring — a combination no existing test sets). (progress.md Day-0 Prong 2.5)
- [x] **Prong 3 (schema)**: N/A — no DB/migration/ORM change; `pending_approval.kind="output"` + `response_snapshot` additive JSONB. (progress.md Day-0)
- [ ] **Baseline capture**: baseline = main `9b4bed54` (57.92 merged): pytest 2254 / mypy 0/350 / run_all 10/10 / Vitest 772 (re-confirm Day-1 before editing)
- [x] **Demo trigger decision**: output guardrail = NEW `OutputKeywordEscalationGuardrail` (mirror input keyword detector) on phrase `confidential` (≠ `approval required` / `checkpoint`), registered at **priority=5** (D-DAY0-1: runs before Toxicity p10 / SensitiveInfo p20 → ESCALATE wins, no BLOCK collision); NO tool needed (the final answer carries the phrase); DEMO_SYSTEM_PROMPT line drives it. (progress.md Day-0 D-DAY0-1)
- [x] Catalogued D-DAY0-1 (OUTPUT chain non-empty → priority=5) drift finding in progress.md; **go/no-go = GO** (gate reachable via output guardrail on a final answer; pre-gate purely additive under HITL wiring; no exhaustiveness/ordering break; no new GuardrailType; no ResumeService/endpoint/migration change; frontend likely none; the one drift resolved by priority=5 — 0% scope change)

### 0.2 Branch
- [x] Branch `feature/sprint-57-93-output-guardrail-pause` from `main` (`9b4bed54`)
- [ ] plan + checklist + progress committed (Day-0 commit)

---

## Day 1 — Output guardrail + pre-delivery gate + pause helper (US-1/US-2/US-4/US-5)

### 1.1 New `OutputKeywordEscalationGuardrail` (US-5)
- [ ] **NEW `guardrails/output/escalation_keyword_detector.py`** — `OutputKeywordEscalationGuardrail(Guardrail)`, `guardrail_type = GuardrailType.OUTPUT`, ESCALATE on a configured case-insensitive phrase; `_extract_text` mirrors `KeywordEscalationGuardrail`; file header
- [ ] **`guardrails/output/__init__.py`** — export `OutputKeywordEscalationGuardrail` (match existing export style)
- [ ] **mypy clean** — `mypy src --strict` on the new file

### 1.2 `_cat9_output_escalate_pause` + `_cat9_output_hitl_pause` (US-1/US-2)
- [ ] **`_cat9_output_escalate_pause`** — runs `check_output(output_text)`; ESCALATE → `_cat9_output_hitl_pause(...)` + return; else → return (no-op, no `GuardrailTriggered`); defensive `engine is None → return`
- [ ] **`_cat9_output_hitl_pause`** — mirror `_cat9_between_turns_hitl_pause`: identity gate (no-identity → fail-closed BLOCK) / `ApprovalRequest(payload kind=output, output_excerpt, summary="approve delivery")` / `request_approval` try-except (persist-fail → BLOCK) / audit `guardrail.output.escalate.requested` / `ApprovalRequested` / `pending_approval={kind:"output",turn,response_snapshot}` (no tool_call) / `_emit_deferred_pause(...)`
- [ ] **mypy clean** on the 2 new methods

### 1.3 Conditional pre-gate before `LLMResponded` in `_run_turns` (US-2/US-4)
- [ ] **Pre-gate call site** — after `parsed = parse(...)` (`:1851`), before `yield LLMResponded` (`:1859`): compute `is_final_answer = should_terminate_by_stop_reason(response) or classify_output(response) == OutputType.FINAL`; `if is_final_answer and guardrail_engine and hitl_manager and hitl_deferred and checkpointer and reducer:` → build `response_snapshot` (answer_text + token/provider/model/cache_hit_rate) → `async for ev in _cat9_output_escalate_pause(...)` (yield; `LoopCompleted` → `return`)
- [ ] **`LLMResponded` (`:1859`) + `_cat9_output_check` (`:1893`) byte-identical** — pre-gate is purely additive (gated on full HITL wiring); non-paused turns unchanged
- [ ] **mypy clean** on the restructured `_run_turns` parse block

### 1.4 Handler wiring + demo prompt (US-5)
- [ ] **Handler wiring** (`handler.py`) — `CHAT_HITL_ESCALATE_OUTPUT_PHRASES = {"confidential"}` + `engine.register(OutputKeywordEscalationGuardrail(...), priority=5)` (D-DAY0-1: before Toxicity p10 / SensitiveInfo p20) gated on `hitl_manager is not None`; extended `DEMO_SYSTEM_PROMPT` with the confidential instruction; MHist 1-line
- [ ] **No phrase collision** — `confidential` ∉ `{approval required}` (input) ∪ `{checkpoint}` (between-turns)

---

## Day 2 — resume() output kind + tests (US-3)

### 2.1 `resume()` output kind-branch + `_replay_approved_output` (US-3)
- [ ] **NEW TERMINAL `elif kind == "output":`** — read `snap = pending.get("response_snapshot",{})`; REJECTED → audit `resume.output.{decision}` + `GuardrailTriggered(output, block)` + `GUARDRAIL_BLOCKED` + `return`; APPROVED → audit `resume.output.approved` + `async for ev in _replay_approved_output(...)` + `return` (NO shared `_run_turns` drive). input + between-turns + tool branches byte-identical
- [ ] **`_replay_approved_output`** — re-emits `LLMResponded(content=answer_text, tokens/provider/model from snap)` + `Thinking` + `LoopCompleted(END_TURN, snapshot metrics)`; no `_run_turns`, no LLM call
- [ ] **mypy clean** on the restructured `resume()`

### 2.2 Unit tests (US-2/US-3/US-4/US-5)
- [ ] **Output pause** — `test_output_escalate_pauses_before_delivery`: single-turn loop whose FINAL answer trips the output guardrail → `ApprovalRequested` + checkpoint `pending_approval{kind:"output", response_snapshot.answer_text}` + `awaiting_approval`; `LLMResponded` for the held answer NOT yielded (assert no `LLMResponded` with the answer content before the pause)
- [ ] **Output resume APPROVED** — `test_resume_output_approved_replays_answer`: re-emits `LLMResponded(answer_text)` + `LoopCompleted(END_TURN)`; NO `_run_turns` drive / NO LLM call (FakeChatClient 0-additional-response budget proves it)
- [ ] **Output resume REJECTED** — `test_resume_output_rejected_blocks`: `GuardrailTriggered(output, block)` + `GUARDRAIL_BLOCKED`; NO `LLMResponded`
- [ ] **Pre-gate non-final no-fire** — `test_output_pre_gate_skips_non_final`: a TOOL_USE response whose text matches does NOT pre-gate (gated on `is_final_answer`); the loop proceeds to tool dispatch
- [ ] **Pre-gate no-wiring no-fire** — `test_output_pre_gate_inert_without_hitl`: without the full HITL wiring the final answer renders normally (LLMResponded yielded) + 1893 escalate-continue path
- [ ] **`OutputKeywordEscalationGuardrail` unit test** (type / match → ESCALATE / case-insensitive / no-match → PASS / empty / Message-extract)
- [ ] **Input/between-turns/tool-path tests UNCHANGED** — 57.88-92 cases pass without edit (pre-gate inert without HITL wiring; resume input/between-turns/tool branches byte-identical)
- [ ] **Span-tree + event-schema guards** — `run_all` 10/10 (incl. `check_event_schema_sync` + AP-1; no new events — reuses `ApprovalRequested`/`GuardrailTriggered`/`LLMResponded`/`LoopCompleted`)

---

## Day 3 — Full regression + drive-through (US-6) + CHANGE-060

### 3.1 Full gate sweep
- [ ] **Full backend pytest green (NET delta documented)** — baseline 2254 → expect +10-12 (output pause/resume/non-final/no-wiring loop unit + output guardrail unit); NO test deleted
- [ ] **mypy 0 + run_all 10/10 + format chain** — mypy `src --strict` 0; run_all **10/10** (LLM SDK leak 0; AP-1; AP-8; event-schema sync); `black`/`isort`/`flake8 src/ tests/` clean (CI-equivalent scope, NOT a path subset — 57.92 lesson)

### 3.2 Drive-through (US-6 — output pause is user-facing; withhold-then-deliver) — **PASS required**
- [ ] **Clean backend restart (Risk Class E)** — kill ALL stale uvicorn reloader+worker procs; verify :8000 OWNER is the fresh PID (`Get-NetTCPConnection -LocalPort 8000`); the new guardrail + demo prompt are startup-wired; Azure SET; note frontend port (57.92 was :3007)
- [ ] **Drive the output pause through real UI + real backend + real Azure gpt-5.2** — a `confidential`-eliciting request → final answer trips the output guardrail → pause (HITL card, **AnswerBlock ABSENT before approval**, `loop_end stop=awaiting_approval`) → Approve → answer renders ("...confidential..."); ALSO drive a Reject → answer never renders + `GUARDRAIL_BLOCKED`. Observed-vs-intended table in progress.md Day 3
  - Evidence: `artifacts/sprint-57-93-output-{1-paused,2-approved-answer,3-rejected}.png`
- [ ] **Frontend gap** — confirm NONE needed (answer held at source = never emitted before approval); if the AnswerBlock leaks, fix the frontend gap (record FIX)

### 3.3 CHANGE-060 + design-note update
- [ ] `claudedocs/4-changes/feature-changes/CHANGE-060-output-guardrail-pause.md` written
- [ ] `19-pause-resume-design.md §5` — "Generalized pause points" lists shipped (input + between-turns + output) + still-deferred (mid-thinking); MHist 57.93 line
- [ ] `17-cross-category-interfaces.md` — `LoopCompleted` row: `awaiting_approval` 3rd origin = output guardrail ESCALATE on a final answer; NO new enum value (OUTPUT already present)

---

## Day 4 — Closeout

### 4.1 Closeout
- [ ] Full validation (parent re-verified): pytest baseline+delta / mypy 0 / run_all 10/10 / input+between-turns+tool-path tests unchanged / **drive-through PASS** (screenshots + observed-vs-intended table, incl. withhold-before-approval)
- [ ] progress.md (Day 0-4) + retrospective.md (Q1-Q7)
- [ ] Calibration: `backend-core-loop-refactor` 0.55 (5th data point, caveated — feature-add shape, 3rd consecutive) + `agent_factor` 1.0 (parent-direct); record `calibration-log.md §3`; if < 0.7 → 3rd same-shape → ACTIVATE `loop-pause-point-feature` ~0.40 split proposal; carryover (Slice 3 leg 3 / subagent child-loop / 57.88 ADs) → next-phase-candidates.md
- [ ] MEMORY.md pointer + `project_phase57_93_output_guardrail_pause.md` subfile + CLAUDE.md lean (Current Sprint row + Last Updated) + CHANGE-060 + `19-pause-resume-design.md §5` + 17.md `LoopCompleted` 3rd-origin note updated
- [ ] commit (Day 0-N) + push + PR — **push + PR pending user authorization**
