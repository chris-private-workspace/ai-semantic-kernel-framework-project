# Sprint 57.98 — Checklist (Verification into the loop — A1: the Cat 10 verify gate becomes an in-loop pre-delivery gear; correction re-injects as a turn; resume covered; the outer wrapper retires)

**Plan**: [`sprint-57-98-plan.md`](./sprint-57-98-plan.md)
**Created**: 2026-06-10
**Status**: Draft — awaiting user GO for Day-1 code (Day-0 Explore recon already run; design decisions locked via AskUserQuestion 2026-06-10)

> Rule: only `[ ]` → `[x]`; never delete unchecked items; defer with `🚧 + reason`.
> **Spike** (new-domain: first in-loop critique gear, touches `loop.py` core) → Day-4 design-note extract MANDATORY (`sprint-workflow.md §Step 5.5` 8-pt gate) → `25-verification-in-loop-design.md`. Record = CHANGE-065 + 17.md verifier-flow update. Gate = full backend pytest green (NET delta) + **drive-through PASS** (fail-then-pass in-loop correction visible AND a resumed session's post-resume answer is verified). Locked decisions (AskUserQuestion 2026-06-10): gate order = **guardrail → verification**; attempt counter = **durable (checkpoint)**; max-after terminal = **stop_reason="verification_failed"** (A1 default; ESCALATE→A2 deferred). Out: A2 human loop, A3 trace-critique, deliver-with-flag, per-tenant policy.

---

## Day 0 — Plan-vs-Repo Verify + Branch

### 0.1 Three-prong Day-0 verify
- [ ] **Prong 1 (path)**: re-confirm the Explore recon anchors — wrapper `verification/correction_loop.py:83-91` (`run_with_verification`, max=2 `:90`) / intercept `:141-144` / `_build_correction_input` `:321-337` / terminal `:229-239` (`VERIFICATION_FAILED_STOP_REASON :80`) / verifier call `:168-171` · router `:96` import + `:432-439` wrap + `_stream_resume_events :813-835` + `loop.resume() :827` + endpoint `:838-892` + tuple unpack `:241` + `:349` plumbing · handler `build_handler` tuple `:241` + registry `:488-495` (`make_chat_verifier_registry(profile.cheap,...) :492-494`) · loop `_run_turns :1621` + parse `:2012` + output-guardrail pre-gate `:2014-2023` + `_cat9_output_check :1090-1176` + `_cat9_output_escalate_pause :1371-1399` + `_emit_deferred_pause :1039-1088` + `__init__ :311-351` + action call `:1954` + `resume() :2486-2520` (drives `_run_turns :2512`) + `_replay_approved_output :2805-2856` · state `LoopState :79-85` + `DurableState :66-76` · events `VerificationPassed :319-329` + `VerificationFailed :332-343` (`correction_attempt :343`). (progress.md Day-0 Prong 1)
- [ ] **Prong 2 (content)**: confirm — (a) the loop ctor has NO `verifier_registry` today (DRIFT 1) → add it; (b) `resume()` drives the shared `_run_turns` (DRIFT 2) → the gate covers resume for free; (c) `_replay_approved_output` re-emits directly + does NOT route through the parse→gate path (else add an explicit skip); (d) the SOLE-CONSUMER re-grep: `grep -rn "run_with_verification" backend/` → only router (`:96`/`:432`) + `verification/__init__.py` + tests; (e) the `build_handler` tuple's 2nd element (the registry) has no consumer besides the router (so it can move to the ctor); (f) the `is_final_answer` predicate the 57.93 output pre-gate uses (reuse it for the verify gate); (g) the verification_log writer the wrapper called (DRIFT 4 — migrate it in-loop). (progress.md Day-0 Prong 2)
- [ ] **Prong 2.5 (reducer / drift)**: confirm — **D1**: the Reducer action/shape for a durable-state field (mirror how `pending_approval_ids`/`last_checkpoint_version` are mutated) so `verification_attempts` increments through the reducer, not direct mutation. **D2**: WHERE a fresh `run()` should reset `verification_attempts` to 0 (run entry, NOT resume). **D3**: the correction `Message` role the wrapper used (`_build_correction_input` output role — user vs tool) so the in-loop feedback matches. **D4**: `LoopCompleted` accepts a raw `stop_reason="verification_failed"` string (no new `TerminationReason` enum) — the 57.92/93 precedent. (progress.md Day-0 Prong 2.5)
- [ ] **Prong 3 (schema)**: N/A — no DB/migration/ORM change (the durable field rides the existing `state_snapshots` JSONB checkpoint); no new event type (`VerificationPassed/Failed` already wire-serialized → `check_event_schema_sync` unaffected). Confirm no new table/column/event.
- [ ] **Baseline capture**: baseline = `main` HEAD (57.98 branched from `84389e91`; capture exact pytest / mypy / run_all numbers at branch creation; record NET delta after edits)
- [ ] **Design-note number locate**: `Glob docs/03-implementation/agent-harness-planning/2*-*.md` → confirm next free number (expect **25**; 24 = multi-model-profile). If a verification design note already exists, EXTEND it instead of creating 25 (note in progress.md).
- [ ] **Strict-judge drive-through setup**: identify how to construct a fail-then-pass verification for the Day-3 drive-through (a strict judge template / a deliberately-wrong-then-corrected prompt) without faking — Day-0 note the approach + that the cheap deployment (57.97) is set
- [ ] Catalogue Day-0/Day-1 drift in progress.md; **go/no-go decision** (feasibility: the recon confirmed the gate move is clean with one ctor-param coupling; the conditional bits = reducer shape + replay-skip + verification_log migration)

### 0.2 Branch
- [ ] Branch `feature/sprint-57-98-verification-in-loop` from `main` (`84389e91`)
- [ ] plan + checklist + progress committed (Day-0 commit)

---

## Day 1 — Loop ctor verifier + the in-loop gate (US-1/US-2)

### 1.1 Loop ctor gains the verifier (US-1)
- [ ] **`orchestrator_loop/loop.py` `__init__`** — add `verifier_registry: VerifierRegistry | None = None` (Day-0 confirm the canonical import for the registry type); store `self._verifier_registry`; MHist
  - DoD: `mypy src/ --strict` 0; existing construction sites (handler + tests) still build (optional param)

### 1.2 The `_cat10_verify_gate()` in `_run_turns` (US-2)
- [ ] **NEW `_cat10_verify_gate()`** (mirrors `_cat9_output_*`) — runs `self._verifier_registry.get_all()` → `await verifier.verify(output=..., state=..., trace_context=...)`; returns a pass/fail-with-corrections result; MHist
  - DoD: unit-tested with a mock registry (PASS / FAIL-with-corrections)
- [ ] **Integrate into `_run_turns`** — after the `_cat9_output_*` output-guardrail handling (`:2014-2023`), before `yield LLMResponded`, gated on `is_final_answer AND self._verifier_registry`:
  - PASS → `yield VerificationPassed` → fall through to deliver (`yield LLMResponded` → `LoopCompleted(end_turn)`)
  - FAIL & `attempts < max` → `yield VerificationFailed(correction_attempt=n)` + append correction `Message` (migrate `_build_correction_input` concat) + bump durable counter (1.3) + `continue` the while-loop (next turn re-answers)
  - FAIL == max → terminal (1.4)
  - DoD: a FAIL re-injects + continues as a NEW turn (turn_count++, SAME LOOP span — not a new run); `verifier_registry is None` → gate skipped (byte-identical)
- [ ] **Migrate verification_log persistence** (57.11) — the wrapper's per-attempt writer called from the gate (best-effort); MHist
  - DoD: persistence happens per attempt in-loop (covered by the converted persist test)
- [ ] **mypy clean** on the backend files (full `src --strict` 0)

---

## Day 2 — Durable counter + terminal + resume/replay + wrapper retire (US-3/US-4/US-5)

### 2.1 Durable attempt counter (US-3)
- [ ] **`_contracts/state.py` `DurableState`** — add `verification_attempts: int = 0` (checkpointed; no migration); MHist
- [ ] **Reducer** (Day-0 D1 located) — handle increment + fresh-run reset (sole mutator); MHist
  - DoD: a pause-mid-correction → resume test asserts the count continues (not reset); a fresh run starts at 0

### 2.2 Terminal + resume coverage + replay-not-reverified (US-4)
- [ ] **Terminal** — FAIL == max → `LoopCompleted(stop_reason="verification_failed")` (raw string, no new enum per Day-0 D4)
  - DoD: max → `verification_failed`
- [ ] **Resume coverage** — NO new code (resume drives `_run_turns`); a test asserts a resumed continuation's final answer is verified
- [ ] **`_replay_approved_output` skips the gate** — confirm (Day-0 Prong 2c) it re-emits directly; if it routes through parse→gate, add an explicit skip; MHist if changed
  - DoD: a test asserts an approved replay is NOT re-verified

### 2.3 Wrapper retired + flow rewired (US-5)
- [ ] **`api/v1/chat/handler.py`** — pass `verifier_registry` into `AgentLoopImpl(..., verifier_registry=registry)`; drop it from the `build_handler` return tuple if unused (Day-0 Prong 2e confirmed); MHist
  - DoD: the loop's `_verifier_registry is` the built registry; cheap judge (57.97) preserved
- [ ] **`api/v1/chat/router.py`** — delete the `run_with_verification` wrapper (`:432-439` → `async for event in loop.run(...)`); remove the import (`:96`) + unused `verifier_registry` plumbing (`:349`); resume path unchanged; MHist
  - DoD: `grep -rn "run_with_verification" backend/src` → 0
- [ ] **`verification/correction_loop.py` REMOVE** + remove the `run_with_verification` re-export from `verification/__init__.py`; MHist
  - DoD: import 0; rollback = git history

---

## Day 3 — Tests + full regression + drive-through (US-6) + CHANGE-065

### 3.1 Tests (US-1..US-5)
- [ ] **NEW `test_loop_verification_gate.py`** — gate verifies a final answer (mock registry); PASS → `VerificationPassed` + deliver; FAIL<max → `VerificationFailed(correction_attempt=1)` + NEW turn (turn_count++, same LOOP span) + correction `Message` in next turn context; FAIL==max → `LoopCompleted(verification_failed)`; `verifier_registry is None` → byte-identical
- [ ] **NEW durable-counter test** — pause mid-correction (guardrail-ESCALATE) → resume → count continues; fresh run resets to 0
- [ ] **NEW resume-coverage test** — a resumed continuation's final answer is verified
- [ ] **NEW replay-not-reverified test** — `_replay_approved_output` delivers without calling the verifier
- [ ] **CONVERT (Never-Delete)** `test_correction_loop.py` + `test_correction_loop_persist.py` → in-loop gate + in-loop persistence equivalents
- [ ] **`test_chat_verification_smoke.py` / `test_verification.py` / `test_sse_verification_serialization.py`** — green (wire unchanged); adjust only wrapper-specific multi-run assertions

### 3.2 Full gate sweep
- [ ] **Full backend pytest green (NET delta documented)** — NO test deleted (conversions net ~0 + NEW gate tests); record baseline → delta
- [ ] **mypy 0 + run_all 10/10 + format chain** — mypy `src --strict` 0; run_all **10/10** (AP-1 green — `continue` in while-driven `_run_turns`, not a pipeline; `check_event_schema_sync` unaffected; `check_cross_category_import` green for `VerifierRegistry` into `loop.py`; LLM SDK leak 0); black/isort/flake8 (changed src+tests) clean — run INDEPENDENTLY (no `&&`, no `--silent`)

### 3.3 Drive-through (US-6 — fail-then-pass in-loop + resume verified)
- [ ] **Clean backend restart (Risk Class E)** — kill stale uvicorn reloader + `multiprocessing.spawn` worker (`Get-CimInstance Win32_Process` PID/PPID/StartTime + `Stop-Process -Force`); verify the FRESH PID is the SOLE :8000 owner; frontend node untouched; verifier wiring built at startup
- [ ] **Drove a fail-then-pass request through real UI + real backend + real Azure** — Inspector shows `VerificationFailed(attempt=1)` → a correction turn → `VerificationPassed` → the answer renders; the judge ran on the cheap tier (57.97 cost_ledger). Observed-vs-intended in progress.md Day 3
  - Evidence: `artifacts/sprint-57-98-1-inloop-correction.png` + cost_ledger verification row (cheap tier)
- [ ] **Resume-coverage drive-through** — pause a session (HITL ESCALATE) → resume → the post-resume final answer is verified (before A1: un-verified). Observed-vs-intended + screenshot
  - Evidence: `artifacts/sprint-57-98-2-resume-verified.png`

### 3.4 CHANGE-065 + 17.md
- [ ] `claudedocs/4-changes/feature-changes/CHANGE-065-verification-in-loop.md` written
- [ ] **`17-cross-category-interfaces.md`** — verifier registry now loop-injected (was wrapper); `correction_loop`/`run_with_verification` retired; `VerificationPassed/Failed` contract unchanged

---

## Day 4 — Closeout (+ spike design note)

### 4.1 Design note (MANDATORY — spike)
- [ ] **`25-verification-in-loop-design.md`** (Day-0 confirmed number) — per `claudedocs/templates/spike-design-note-template.md`; 8-point quality gate verified in retrospective.md:
  - [ ] 1. Section header maps to the spike US (US-1..US-6)
  - [ ] 2. each technical claim has file:line (`loop.py` gate + `_run_turns` integration / `state.py DurableState` / `handler.py` injection / `router.py` wrapper delete / `correction_loop.py` removed)
  - [ ] 3. Decision matrix (outer-wrapper vs in-loop gate · guardrail-first vs verification-first · durable vs transient counter · stop_reason vs deliver-with-flag vs ESCALATE — ≥4 rows)
  - [ ] 4. verification command (`pytest .../test_loop_verification_gate.py` + the drive-through reproduce)
  - [ ] 5. test fixture reference (mock verifier registry + the converted persist fixtures + artifact PNGs)
  - [ ] 6. Open invariants split (§ fenced: A2 human loop, A3 trace-critique, deliver-with-flag, per-tenant policy, cheap-judge accuracy)
  - [ ] 7. rollback path (revert the commit; the `chat_verification_mode` env gate disables verification)
  - [ ] 8. 17.md cross-ref (verifier-flow update)

### 4.2 Closeout
- [ ] Full validation (parent re-verified): pytest NET delta / mypy 0 / run_all 10/10 / converted tests green / `events.py`+`ModelProfile`+frontend+DB diff = 0 / **drive-through PASS** (in-loop correction + resume verified; artifacts PNG)
- [ ] progress.md (Day 0-3) + retrospective.md (Q1-Q7) + **design-note 8-pt gate self-check recorded** (retro Q6)
- [ ] Calibration: `verification-in-loop-spike` 0.60 (1st data point) + `agent_factor` 1.0 (parent-direct); recorded `calibration-log.md §3` + `sprint-workflow.md §Scope-class matrix` row; carryover (A2 verification-ESCALATE / A3 trace-critique / deliver-with-flag / per-tenant verification policy / cheap-judge accuracy) → next-phase-candidates.md
- [ ] MEMORY.md pointer + `project_phase57_98_verification_in_loop.md` subfile + CLAUDE.md lean (Current Sprint row + Last Updated) + CHANGE-065 + design-note 25 + 17.md update
- [ ] commit (Day 0-N) + push + PR — **push + PR pending user authorization**
