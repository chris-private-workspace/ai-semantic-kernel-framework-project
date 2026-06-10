# Sprint 57.99 — Checklist (Verification-ESCALATE human-in-the-loop — A2: on max-attempts, conditionally swap the A1 `verification_failed` terminal for a human ESCALATE pause; APPROVE delivers the held answer, REJECT-with-note re-injects one bounded human-coached turn)

**Plan**: [`sprint-57-99-plan.md`](./sprint-57-99-plan.md)
**Created**: 2026-06-10
**Status**: Draft — awaiting user GO for Day-1 code (Day-0 Explore recon already run; design decisions locked via AskUserQuestion 2026-06-10)

> Rule: only `[ ]` → `[x]`; never delete unchecked items; defer with `🚧 + reason`.
> **Feature-continuation** (the 4th pause leg — input/between-turns/output/verification — built from the same 57.91-93 primitive + the A1 gate) → **NO new design note** (`sprint-workflow.md §Step 5.5`, the 57.91-93/95/96 precedent). Record = CHANGE-066 + **update `25-verification-in-loop-design.md` §4** (A2 Open Invariant → SHIPPED) + 17.md (new resume kind). Gate = full backend pytest green (NET delta) + **drive-through PASS** (a strict-judge fail → escalate pause → APPROVE delivers the held answer AND REJECT-with-note re-injects one human-coached turn). Locked decisions (AskUserQuestion 2026-06-10): APPROVE = **deliver the held failed answer (human overrides the judge)**; REJECT-with-note = **one human-coached turn, then terminal**; gating = **global settings toggle `chat_verification_escalate_on_max`, default OFF = A1 preserved**. Out: A3 trace-critique, per-tenant policy (C3), deliver-with-flag, multi-round coaching, dedicated approval UI.

---

## Day 0 — Plan-vs-Repo Verify + Branch

### 0.1 Three-prong Day-0 verify
- [x] **Prong 1 (path)**: re-confirm the Explore recon anchors (post-A1-merge line numbers) — loop `_cat10_verify_gate :1606` + `_VerifyVerdict :328-347` + `_build_correction_block :350-364` + FAIL==max integration `:2313-2360` (terminal `:2344-2346`, `VERIFICATION_FAILED_STOP_REASON :220`) · `_emit_deferred_pause :1114-1165` (kinds tool `:1053`/input `:1137`/between_turns `:1425`/output `:1588`; checkpoint `:1144`; AWAITING_APPROVAL `:1161`; output `response_snapshot :1591`) · `_cat9_output_escalate_pause :1442-1482` + `_cat9_output_hitl_pause :1484-1604` (ApprovalRequest `:1535-1549`, pending_approval `:1587-1592`) · `_replay_approved_output :3078-3129` (re-emit LLMResponded `:3106`, LoopCompleted END_TURN `:3118`, snapshot fields `:3099-3105`) · `resume() :2750-3076` (get_decision `:2826`; kinds input `:2856-2883`/between_turns `:2884-2914`/output `:2915-2957` replay `:2950`/tool else `:2958-3024`; shared `_run_turns` drive `:3057-3068`) · `__init__ :410-416` (verifier_registry param) · durable counter write `:3185-3186` + resume read (`metadata["verification_attempts"]`) · `ApprovalDecision hitl.py:68-77` (reason `:77`) + `DecisionRequestBody governance/router.py:102-106` (reason max 4096 `:106`) · events `ApprovalRequested/Received events.py:400-408` + `GuardrailTriggered :306` + `VerificationFailed :271-281` · handler verification mode `:265-270` + ctor pass `:456-459`. (progress.md Day-0 Prong 1)
- [x] **Prong 2 (content)**: confirm — (a) the FAIL==max terminal `:2344-2346` has `parsed.text` (held answer) + `verdict` (reasons) + the provider/model/token fields in scope (for the snapshot); (b) `_replay_approved_output`'s snapshot field set (`:3099-3105`) so APPROVE can reuse it; (c) `resume()` reads `decision.reason` on the get_decision path (so REJECT can read the note); (d) the durable `verification_attempts` write/read pattern (`:3185-3186` + resume) so `verification_escalated` mirrors it; (e) the `core/config` settings module location + how `chat_verification_mode` is declared (so the new toggle matches the pattern); (f) the 3 `handler.py` builders that construct `AgentLoopImpl` (so all 3 thread the toggle); (g) `_emit_deferred_pause`'s `kind` is a free string (no enum) so `"verification"` is additive. (progress.md Day-0 Prong 2)
- [x] **Prong 2.5 (drift)**: confirm — **D1**: `resume()`'s `kind` dispatch is an `if/elif` chain (so `elif kind == "verification":` is additive, no exhaustiveness consumer breaks). **D2**: the held-answer snapshot can be built at the terminal point (all `_replay_approved_output` fields in scope at `:2344`), else capture them earlier. **D3**: the REJECT continuation can drive `_run_turns` with `verification_attempts=max` + `verification_escalated=True` to bound to one turn (the FAIL==max branch reads `verification_escalated`). **D4**: `LoopCompleted` + `ApprovalRequested(HIGH)` reused (no new event — the 57.93 precedent). (progress.md Day-0 Prong 2.5)
- [x] **Prong 3 (schema)**: N/A — no DB/migration/ORM change (the durable bool rides the existing `state_snapshots` JSONB checkpoint metadata, the 57.98 precedent); no new event type (`ApprovalRequested`/`ApprovalReceived`/`GuardrailTriggered`/`VerificationFailed` already wire-serialized → `check_event_schema_sync` unaffected); no new DTO (the note rides `ApprovalDecision.reason`). Confirm no new table/column/event/DTO.
- [x] **Baseline capture**: baseline = `main` HEAD (57.99 branched from `be89d3ec`; pytest collect = **2298** (`-m "not real_llm"`); mypy `src` = **0/353**; run_all 10/10 to confirm Day-0; record NET delta after edits)
- [x] **Design-note decision**: A2 = feature-continuation → NO new design note (the 57.91-93 precedent). Confirm in progress.md + plan to UPDATE `25-verification-in-loop-design.md` §4 (A2 Open Invariant → SHIPPED) instead.
- [x] **Strict-judge drive-through setup**: identify how to force a real verification fail for the Day-3 drive-through (a strict judge template / a deliberately-hard prompt) without faking — the 57.98 carryover `strict-judge drive-through template`; Day-0 note the approach + that the cheap deployment (57.97) is set
- [x] Catalogue Day-0/Day-1 drift in progress.md; **go/no-go decision = GO** (feasibility: the recon confirmed A2 = a new pause method + one conditional terminal branch + one resume kind + a settings toggle + a durable bool; the conditional bits = the snapshot field match + the REJECT bound + the strict-judge fail)

### 0.2 Branch
- [x] Branch `feature/sprint-57-99-verification-escalate` from `main` (`be89d3ec`)
- [ ] plan + checklist + progress committed (Day-0 commit)

---

## Day 1 — Config toggle + the escalate pause (US-1/US-2)

### 1.1 The config toggle (US-1)
- [x] **`core/config` setting** — add `chat_verification_escalate_on_max: bool = False` (env `CHAT_VERIFICATION_ESCALATE_ON_MAX`); `.env.example` documents it; MHist
  - DoD: `mypy src --strict` 0; the setting reads from env with a False default
  - ✅ Added to the `chat_verification_*` cluster. **D-DAY1-2**: `.env.example` has NO sibling `CHAT_VERIFICATION_*` entries → skipped the lone entry (the `Settings` default False documents it; match the convention). MHist added.
- [x] **`orchestrator_loop/loop.py` `__init__`** — add `verification_escalate_on_max: bool = False` (store `self._verification_escalate_on_max`); MHist
  - ✅ Optional param default False; existing sites build. MHist added.
- [x] **`api/v1/chat/handler.py`** — all 3 builders read `settings.chat_verification_escalate_on_max` + pass `verification_escalate_on_max=` into `AgentLoopImpl(...)`; MHist
  - ✅ Threaded into the MAIN real_llm site (the one with verifier_registry + hitl_deferred). The echo-demo + child-loop sites are untouched (no registry → the escalate branch never runs there). MHist added.

### 1.2 The escalate pause (US-2)
- [x] **NEW `_cat10_verification_escalate_pause()`** (mirrors `_cat9_output_hitl_pause`) — build the held-answer + verifier-reasons `response_snapshot` (the `_replay_approved_output` field set), create the `ApprovalRequest` (`"kind":"verification"`, `risk_level="HIGH"`, reasons in the payload), emit `ApprovalRequested(HIGH)`, build `pending_approval` (`kind="verification"` + `response_snapshot`), call `_emit_deferred_pause(kind="verification", ...)`, persist `verification_escalated=True`; MHist
  - ✅ Snapshot carries `answer_text=parsed.text` + the metrics fields (so Day-2 resume APPROVE replays via `_replay_approved_output`). Reason from the failed-verifier `VerificationFailed` events. Fail-closed (no-identity / persist-fail) → A1 `verification_failed` terminal. Covered by `test_verify_escalate_on_max_pauses_for_human`.
- [x] **Conditional FAIL==max branch** — `if self._verification_escalate_on_max and not verification_escalated:` → `_cat10_verification_escalate_pause(...)` → `return`; `else:` → the A1 `LoopCompleted(verification_failed)` (byte-identical); MHist
  - ✅ Gated additionally on the full HITL deferred-pause wiring (`hitl_manager + hitl_deferred + checkpointer + reducer`) so it falls back to A1 when a resumable pause isn't possible. `test_verify_escalate_off_preserves_a1_terminal` proves toggle-OFF byte-identical (124 regression green).
- [x] **Durable `verification_escalated` write** — `_emit_state_checkpoint`/`_emit_deferred_pause` write `metadata["verification_escalated"]` when True (mirror `verification_attempts`); thread into `_run_turns` as a param (`verification_escalated: bool = False`); MHist
  - ✅ Threaded `_run_turns` → `_emit_deferred_pause` → `_emit_state_checkpoint`; the escalate test asserts `metadata.verification_escalated is True`.
- [x] **mypy clean** on the backend files (full `src --strict` 0)
  - ✅ mypy 0/353; black/isort/flake8 (changed src + test) clean.

---

## Day 2 — Resume APPROVE / REJECT-with-note + the durable bound (US-3/US-4/US-5)

### 2.1 Resume APPROVE → deliver the held answer (US-3)
- [x] **`resume()` `elif kind == "verification":` APPROVED** — re-emit the held failed answer via the `_replay_approved_output` shape (terminal, no LLM re-call, NOT re-verified); MHist
  - DoD: a test asserts the delivered content == the held failed answer + the verifier is NOT called (replay code-path isolation, the A1 rule) ✅ `test_verify_escalate_resume_approve_delivers_held_answer`

### 2.2 Resume REJECT-with-note → one bounded human-coached turn (US-4)
- [x] **`resume()` `kind="verification"` REJECTED** — append `Message(role="user", content="[Verification rejected by reviewer: {decision.reason or 'no reason given'}. Please revise the answer.]")` + drive `_run_turns` with `verification_attempts=self._max_correction_attempts` + `verification_escalated=True`; MHist
  - DoD: the note re-injects (reaches the next chat request) + one `_run_turns` turn runs; PASS → deliver ✅ `test_verify_escalate_resume_reject_coaches_one_turn`
- [x] **The bound (reject-then-fail terminates)** — the FAIL==max branch reads `verification_escalated` (from the metadata / the `_run_turns` param) → already-escalated → the A1 terminal (NOT a 2nd escalate)
  - DoD: a test asserts reject-then-fail → `LoopCompleted(verification_failed)` with NO 2nd `ApprovalRequested` ✅ `test_verify_escalate_reject_then_fail_binds_to_a1_terminal`

### 2.3 Durable flag survives resume + no new event (US-5)
- [x] **Durable `verification_escalated` resume read** — `resume()` reads `metadata.get("verification_escalated", False)` → passes to `_run_turns` (mirror the `verification_attempts` resume read); MHist
  - DoD: a pause→resume mid-escalation preserves the flag; a fresh run starts False ✅ (reject-then-fail test honours the rehydrated flag; toggle-OFF test = fresh-False)
- [x] **No new event** — confirm A2 reuses `ApprovalRequested`/`ApprovalReceived`/`GuardrailTriggered`/`VerificationFailed` (no new event type; `check_event_schema_sync` unaffected)
  - DoD: `grep` no new event class added; `check_event_schema_sync` green ✅ run_all 10/10 (no new event class)

---

## Day 3 — Tests + full regression + drive-through (US-6) + CHANGE-066

### 3.1 Tests (US-1..US-5)
- [x] **toggle tests** (D-DAY1-1: in `test_loop_pause_resume.py`, NOT a NEW `test_loop_verification_escalate.py` — reuses the full HITL+verifier fixtures) — toggle OFF → A1 `verification_failed` terminal byte-identical (no `ApprovalRequested`); toggle ON + FAIL==max → escalate pause (`ApprovalRequested(HIGH)` + `awaiting_approval` + held answer + verifier reason); `verification_escalated` persisted
  - DoD: the toggle-OFF byte-identical + the escalate-pause cases pass ✅ `test_verify_escalate_off_preserves_a1_terminal` + `test_verify_escalate_on_max_pauses_for_human` (Day-1)
- [x] **resume APPROVE test** — `kind="verification"` APPROVE → the held failed answer is delivered (content matches) + the verifier is NOT re-called ✅ `test_verify_escalate_resume_approve_delivers_held_answer`
- [x] **resume REJECT-with-note test** — REJECT → the note re-injects as a `user` Message (reaches the next chat request) + one `_run_turns` turn runs; PASS → deliver ✅ `test_verify_escalate_resume_reject_coaches_one_turn` (asserts the note in `chat.seen_messages`)
- [x] **reject-then-fail-terminates test** — REJECT → the human-coached turn FAILS → `LoopCompleted(verification_failed)` (NO 2nd `ApprovalRequested` — the durable bound holds) ✅ `test_verify_escalate_reject_then_fail_binds_to_a1_terminal`
- [x] **durable-flag test** — a pause→resume mid-escalation preserves `verification_escalated`; a fresh run starts False ✅ (reject-then-fail honours the rehydrated flag; toggle-OFF + `test_fresh_run_starts_counter_at_zero` = fresh-False)
- [x] **`test_chat_verification_smoke.py`** — green (toggle-OFF default preserves A1; no escalate) ✅ 3 passed

### 3.2 Full gate sweep
- [x] **Full backend pytest green (NET delta documented)** — NO test deleted; record baseline (2298 collect) → delta ✅ **2299 passed + 4 skipped = 2303** (2298 + 5: 2 Day-1 escalate + 3 Day-2 resume; zero deletion). D-DAY3-1: the sweep caught 2 Sprint-57.97 `test_handler.py` tests broken by the Day-1 `settings` read (their `SimpleNamespace` stub lacked the new attribute) → root-cause fix on the stub
- [x] **mypy 0 + run_all 10/10 + format chain** — mypy `src --strict` 0; run_all **10/10** (AP-1 green — the escalate is a conditional `return` in the while-driven `_run_turns`, the reject continuation drives `_run_turns`; `check_event_schema_sync` unaffected; LLM SDK leak 0); black/isort/flake8 **FULL `src/ tests/` scope** clean — run INDEPENDENTLY (no `&&`, no `--silent`; the 57.98 CI-black lesson — full scope, not changed-files subset) ✅ mypy `src` 0/353 · run_all 10/10 · format clean

### 3.3 Drive-through (US-6 — strict-judge fail → escalate → approve + reject-coach)
- [x] **Clean backend restart (Risk Class E)** — killed the stale uvicorn reloader (40280) + `multiprocessing.spawn` worker (6476) via `Win32_Process` + `Stop-Process -Force`; verified :8000 free + node :3007 (PID 6200) untouched; started a fresh NO-`--reload` single process (PID 35284→9344) with `CHAT_VERIFICATION_MODE=enabled` + `CHAT_VERIFICATION_ESCALATE_ON_MAX=true` + a forced-fail `CHAT_VERIFICATION_JUDGE_TEMPLATE` env (real LLM judge, deterministic fail, zero code pollution); restored the normal `--reload` backend after ✅
- [x] **Drove a verification fail → escalate → APPROVE** ✅ real UI (jamie@acme.com/acme-prod) + real backend + real Azure gpt-5.2 + a real LLM judge (forced-fail via env). 3 final-answer attempts each `verification_failed` → attempt 2==max → A2 escalate: `approval_requested risk=HIGH` + `loop_end stop=awaiting_approval` (Loop visualizer) + a kind-agnostic HITL card (severity HIGH, **tool: —** = verification-kind) → **Approve** → `resume()` → `_replay_approved_output` → turn 4 flips `awaiting_approval`→**`stop: end_turn`**, the held answer renders, card shows **Decision: APPROVED**. Screenshots: `artifacts/dt5799-A-escalate-pause.png` + `dt5799-B-approved-delivered.png`. Observed-vs-intended in progress.md Day-3 part 2
- [x] **REJECT-with-note → one human-coached turn** — backend unit-proven (`test_verify_escalate_resume_reject_coaches_one_turn` + `_reject_then_fail_binds_to_a1_terminal`); **NOT UI-drivable** — drive-through revealed a chat-v2 frontend gap: `HITLTurn.submitDecision("rejected")` deliberately does NOT `resume()` (built for tool-kind reject=terminate) + the reject button has NO note input (`decide()` sends no `reason`). A2 backend supports it fully; wiring the chat-v2 UI (verification-kind resume-on-reject + a coaching-note input) is a documented frontend follow-up (out of A2's backend file-list scope; user-confirmed Option A). Drive-through finding logged in progress.md
  - NOTE (honest gap): the forced-fail is a real LLM judge instructed to fail (deterministic) — clearly labelled DEMO; the escalate/approve/reject mechanism is unit-proven. NOT claimed "gate-only". D-DAY3-2: the first forced-fail correction text mentioned "approval" → gpt-5.2 called the `request_approval` tool (a tool-kind 57.88 pause, not A2) → re-ran with a neutral "no tools, just re-answer" correction to keep 3 final answers → clean A2 escalate

### 3.4 CHANGE-066 + 25.md §4 + 17.md
- [x] `claudedocs/4-changes/feature-changes/CHANGE-066-verification-escalate.md` written ✅
- [x] **`25-verification-in-loop-design.md` §4** — move the "A2 — verification-ESCALATE human-in-the-loop" Open Invariant from deferred → SHIPPED (with the A2 file:line); MHist ✅
- [x] **`17-cross-category-interfaces.md`** — the `LoopCompleted(verification_failed)` terminal now has a conditional human-ESCALATE alternative; `resume()` gains `kind="verification"` (APPROVE → replay held answer; REJECT → one coached turn); `ApprovalRequested/Received` contracts unchanged ✅ (`LoopCompleted` row §259 — `awaiting_approval` 5th origin)

---

## Day 4 — Closeout (feature-continuation — NO design note)

### 4.1 Closeout
- [x] Full validation (parent re-verified): pytest **2299 passed + 4 skipped = 2303** (baseline 2298 +5, zero deletion) / mypy `src` **0/353** / run_all **10/10** / **black FULL `src tests` 656 files clean** / `events.py`+`ModelProfile`+frontend+DB diff = **0** (3 backend src files only) / **drive-through PASS** (escalate → APPROVE-delivers — real UI + real Azure; REJECT-coaches half = backend unit-proven + chat-v2 frontend follow-up, NOT UI-driven; artifacts `dt5799-{A,B}.png`) ✅
- [x] progress.md (Day 0-3, parts 1+2) + retrospective.md (Q1-Q7) ✅
- [x] Calibration: `loop-pause-point-feature` 0.50 (NEW class, 1st data point ~0.93 IN band — honours the 57.92/93 proposal, set 0.50 > 0.40 for the bounded REJECT continuation) + `agent_factor` 1.0 (parent-direct); recorded `calibration-log.md §3` + `sprint-workflow.md §Scope-class matrix` row; carryover (chat-v2 reject UI / A3 trace-critique / per-tenant policy C3 / deliver-with-flag / multi-round coaching / cheap-judge accuracy) → next-phase-candidates.md ✅
- [x] MEMORY.md pointer + `project_phase57_99_verification_escalate.md` subfile + CLAUDE.md lean (Current Sprint row + Last Updated) + CHANGE-066 + 25.md §4 update + 17.md update ✅
- [ ] commit (Day 0-N) + push + PR — Day-1..Day-3 committed (`bf99ad83`/`aefafc59`/`f2682619`/`e73e3e83`); Day-4 closeout commit next; **push + PR pending user authorization**
