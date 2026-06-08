# Sprint 57.92 — Checklist (Between-Turns Guardrail ESCALATE Pause Point — 地基 A Slice 3 leg 2)

**Plan**: [`sprint-57-92-plan.md`](./sprint-57-92-plan.md)
**Created**: 2026-06-08
**Status**: Draft (code gated on Day-0 GO)

> Rule: only `[ ]` → `[x]`; never delete unchecked items; defer with `🚧 + reason`.
> CHANGE (feature add — second pause point) → CHANGE-059 record; no new design note (update `19-pause-resume-design.md §5`). Gate = full backend pytest green (NET delta documented) + **drive-through PASS** (between-turns pause is user-facing). Locked scope: between-turns guardrail ESCALATE only (mid-thinking deferred to leg 3; subagent child-loop a separate sprint).

---

## Day 0 — Plan-vs-Repo Verify + Branch

### 0.1 Three-prong Day-0 verify
- [x] **Prong 1 (path)**: confirmed — `_emit_deferred_pause` `:1037` / `_cat9_input_check` `:546` + `_cat9_input_hitl_pause` `:631` (mirror template) / `_cat9_output_check` `:1088` (called `:1668`, OUTPUT chain) / `_run_turns` `:1261` (`while True` `:1282`, term checks end `~:1307`, `turn_count += 1` LAST `:2050`) / `run()` drive `:1242` / `resume()` kind-branch `:2147` + shared drive `:2275`. `engine.py` `_chains` `:80` / `check_output` `:126` / `_run_chain` `:100`. `_abc.py` `GuardrailType` `:31`. `handler.py` `:121`/`:131`/`:103`/`:306-321`/`make_default_executor` `:255`. echo_tool registered `business_domain/_register_all.py:237-238` (impl `agent_harness/tools/echo_tool.py`). (progress.md Day-0 Prong 1)
- [x] **Prong 2 (content)**: confirmed — (a) `_emit_deferred_pause` kind-agnostic; (b) `run()` drive `:1242` passes raw locals (skip flag additive); (c) `resume()` `kind=pending.get("kind","tool")` + shared drive both kinds; (d) per-response check uses OUTPUT chain (no double-fire); (e) `_cat9_input_hitl_pause` exact mirror; (f) echo_tool tool-escalates + tool-resume execs outside loop → re-enters turn 0 → never reaches turn 1 → confirms `note_tool` required. (progress.md Day-0 Prong 2)
- [x] **Prong 2.5 (GuardrailType exhaustiveness)**: SAFE — all usages are import / `guardrail_type = GuardrailType.X` / `_chains` factory / `_run_chain(GuardrailType.X)`; NO `match`/`len()`/dict-over-types; cat9_mutator+fallback pass-through only. 4th value `BETWEEN_TURNS` breaks nothing. (progress.md Day-0 Prong 2.5)
- [x] **Prong 3 (schema)**: N/A — no DB/migration/ORM change; `pending_approval.kind="between_turns"` additive JSONB. (progress.md Day-0)
- [x] **Baseline capture**: baseline = main `0ceb788d` (57.91 merged): pytest 2243 / mypy 0/347 / run_all 10/10 / Vitest 772 (re-confirm Day-1 before editing)
- [x] **Drive-through tool decision**: `note_tool` = NEW `agent_harness/tools/note_tool.py` (mirror echo) + register `_register_all.py:237-238`; auto-available + auto-PASS in chat; between-turns phrase `checkpoint` (≠ `approval required`); DEMO_SYSTEM_PROMPT line. (progress.md Day-0 D-DAY0-1)
- [x] Catalogue D-DAY0-1..4 drift findings in progress.md; **go/no-go = GO** (gate reachable via `note_tool` + between-turns gate; no exhaustiveness break; no ResumeService/endpoint/migration/frontend change; all 4 drifts anticipated by plan)

### 0.2 Branch
- [x] Branch `feature/sprint-57-92-between-turns-pause` from `main` (`0ceb788d`)
- [x] plan + checklist + progress committed (Day-0 commit `d12e68ed`)

---

## Day 1 — GuardrailType + between-turns gate + pause helper (US-1/US-2/US-4/US-5)

### 1.1 New `GuardrailType.BETWEEN_TURNS` + `check_between_turns` (US-5)
- [x] **`_abc.py`** — added `BETWEEN_TURNS = "between_turns"` to `GuardrailType`; MHist 1-line
- [x] **`engine.py`** — added `check_between_turns()` mirror of `check_output` (BETWEEN_TURNS chain, default PASS when empty); docstring "three→four cut points"; MHist 1-line
- [x] **No exhaustiveness break** (Prong 2.5 confirmed none; `_chains` factory auto-includes)
- [x] **mypy clean** — `mypy src --strict` Success (350 files)

### 1.2 `_cat9_between_turns_check` + `_cat9_between_turns_hitl_pause` + `_latest_output_text` (US-1/US-2/US-4)
- [x] **`_latest_output_text(messages) -> str`** — content of last truthy assistant/tool message, `""` fallback (static pure helper)
- [x] **`_cat9_between_turns_check`** — runs `check_between_turns(content)`; PASS→return; ESCALATE + deferred wiring → `_cat9_between_turns_hitl_pause` + return; `action != PASS` (BLOCK / ESCALATE-no-HITL) → audit + `GuardrailTriggered(between_turns)` + `LoopCompleted(GUARDRAIL_BLOCKED)` (US-4 fail-closed)
- [x] **`_cat9_between_turns_hitl_pause`** — mirror `_cat9_input_hitl_pause`: identity gate / `ApprovalRequest(payload kind=between_turns, output_excerpt, summary="approve continuation")` / `request_approval` try-except / audit `guardrail.between_turns.escalate.requested` / `ApprovalRequested` / `pending_approval={kind:"between_turns",…}` (no tool_call) / `_emit_deferred_pause(...)`
- [x] **mypy clean** on the 3 new methods

### 1.3 Loop-top gate in `_run_turns` (US-2)
- [x] **`_run_turns` signature** — added `skip_between_turns_once: bool = False` (keyword)
- [x] **NEW gate** after the cancellation termination check, before compaction: `if turn_count > 0 and not skip_between_turns_once:` → `async for ev in self._cat9_between_turns_check(...)` (yield; `LoopCompleted` → `return`); then `skip_between_turns_once = False` (consume after 1st iter)
- [x] **`run()` call site** (`:1440`) — unchanged (default False); type-checks

### 1.4 Real guardrail + non-escalate demo tool + handler wiring (US-5)
- [x] **NEW `guardrails/between_turns/keyword_detector.py`** — `BetweenTurnsKeywordGuardrail(Guardrail)`, `GuardrailType.BETWEEN_TURNS`, ESCALATE on configured phrase; `_extract_text` mirrors `KeywordEscalationGuardrail`; `between_turns/__init__.py` export; mypy clean
- [x] **`note_tool`** — NEW `agent_harness/tools/note_tool.py` (`text`→`text`) + registered unconditionally in `_register_all.py` (covers both branches); NOT in `CHAT_HITL_ESCALATE_TOOLS` → auto-PASS in chat
- [x] **Handler wiring** (`handler.py`) — `CHAT_HITL_ESCALATE_BETWEEN_TURNS_PHRASES = {"checkpoint"}` + `engine.register(BetweenTurnsKeywordGuardrail(...))` gated on `hitl_manager is not None`; extended `DEMO_SYSTEM_PROMPT` with the `note_tool` instruction

---

## Day 2 — resume() between-turns kind + tests (US-3)

### 2.1 `resume()` between-turns kind-branch (US-3)
- [x] **Init `skip_between_turns_once = False`** before the kind-branch
- [x] **NEW `elif kind == "between_turns":`** — APPROVED → audit `resume.between_turns.approved` + no tool + `skip_between_turns_once = True`; REJECTED → `GuardrailTriggered(between_turns, block)` + `GUARDRAIL_BLOCKED` + return. input + tool branches byte-identical
- [x] **Shared drive** (`:2499`) — passes `skip_between_turns_once=skip_between_turns_once` to `self._run_turns(...)`
- [x] **mypy clean** on the restructured `resume()`

### 2.2 Unit tests (US-2/US-3/US-4/US-5)
- [x] **Between-turns pause** — `test_between_turns_escalate_pauses_before_next_turn`: 2-turn loop (non-escalate tool) → ESCALATE at top of turn 1 → `ApprovalRequested` + checkpoint `pending_approval{kind:"between_turns"}` + `awaiting_approval`; turn-1 LLM NOT called (FakeChatClient 1-response budget proves it)
- [x] **Between-turns resume APPROVED** — `test_resume_between_turns_approved_continues_no_repause`: drives `_run_turns` to `end_turn`; gate skipped once (NO second pause, always-escalate guardrail wired proves skip); NO tool exec
- [x] **Between-turns resume REJECTED** — `test_resume_between_turns_rejected_blocks`: `GuardrailTriggered(between_turns, block)` + `GUARDRAIL_BLOCKED`
- [x] **ESCALATE-without-HITL → BLOCK** — `test_between_turns_escalate_without_hitl_blocks` (fail closed, US-4)
- [x] **`BetweenTurnsKeywordGuardrail` unit test** (7 cases: type/match/case/no-match/empty/blank-drop/Message-extract)
- [x] **Input/tool-path tests UNCHANGED** — 57.88-91 cases pass without edit (skip flag defaults False; input/tool branches byte-identical)
- [x] **Span-tree + event-schema guards** — `run_all` 10/10 (incl. `check_event_schema_sync` + AP-1; no new events — reuses `ApprovalRequested`/`GuardrailTriggered`/`LoopCompleted`)

---

## Day 3 — Full regression + drive-through (US-6) + CHANGE-059

### 3.1 Full gate sweep
- [x] **Full backend pytest green (NET delta documented)** — baseline 2243 → **2254 passed / 4 skipped** = +11 (4 between-turns loop unit + 7 guardrail unit); NO test deleted
- [x] **mypy 0 + run_all 10/10 + format chain** — mypy `src --strict` 0 (350 files); run_all **10/10** (LLM SDK leak 0; AP-1; AP-8; event-schema sync); black/isort/flake8 clean

### 3.2 Drive-through (US-6 — between-turns pause is user-facing) — **PASS**
- [x] **Clean backend restart (Risk Class E)** — killed stale uvicorn worker 16992 + reloader 50548 (57.91 PRE-57.92 process); verified :8000 no LISTEN owner; fresh backend PID 53688 (57.92 code); frontend :3007 (PID 6200); Azure SET
- [x] **Drove the between-turns pause through real UI + real backend + real Azure gpt-5.2** — `note the word checkpoint` → turn 0 `note_tool` exec (input `{text:checkpoint}` → output `checkpoint`, NON-escalate, `state_checkpointed v2`) → top of turn 1 `approval_requested risk=HIGH` → pause (HITL card **`tool: —`** between-turns-kind, `loop_end stop=awaiting_approval turns=1`, NO answer, turn-1 LLM not called) → Approve → `Decision: APPROVED` → resume → `stop: end_turn` answer **"checkpoint"** (gate skipped, NO re-pause). Observed-vs-intended table in progress.md Day 3.
  - Evidence: `artifacts/sprint-57-92-between-turns-1-paused.png` + `-2-resumed-answer.png`
- [x] **Frontend gap** — NONE needed; the HITL card + Approve surfaced generically for a no-tool pause (`tool: —`; events tool-agnostic, as leg 1)

### 3.3 CHANGE-059 + design-note update
- [x] `claudedocs/4-changes/feature-changes/CHANGE-059-between-turns-pause.md` written
- [x] `19-pause-resume-design.md §5` — "Generalized pause points" split into shipped (leg 1 input + leg 2 between-turns) + still-deferred (leg 3 mid-thinking); MHist 57.91+57.92 lines
- [x] `17-cross-category-interfaces.md` — `LoopCompleted` row: `awaiting_approval` 3rd origin = between-turns guardrail ESCALATE + new `GuardrailType.BETWEEN_TURNS` enum value (single-source `_abc.py`)

---

## Day 4 — Closeout

### 4.1 Closeout
- [x] Full validation (parent re-verified): pytest **2254** (+11) / mypy 0/350 / run_all 10/10 / input+tool-path tests unchanged / **drive-through PASS** (2 screenshots + observed-vs-intended table)
- [x] progress.md (Day 0-4) + retrospective.md (Q1-Q7)
- [x] Calibration: `backend-core-loop-refactor` 0.55 (4th data point, caveated — feature-add shape, 2nd consecutive < 0.7) + `agent_factor` 1.0 (parent-direct); recorded `calibration-log.md §3`; flagged `loop-pause-point-feature` ~0.40 split PROPOSAL (3rd same-shape confirms); carryover (Slice 3 leg 3 / output-guardrail ESCALATE / subagent child-loop / 57.88 ADs) → next-phase-candidates.md
- [x] MEMORY.md pointer + `project_phase57_92_between_turns_pause.md` subfile + CLAUDE.md lean (Current Sprint row + Last Updated) + CHANGE-059 + `19-pause-resume-design.md §5` + 17.md `LoopCompleted` 3rd-origin note updated
- [ ] commit (Day 0-N) + push + PR — closeout commit done; **push + PR pending user authorization**
