# Sprint 57.136 — Checklist (verification correction context hygiene — self-conditioning spike)

[Plan](./sprint-57-136-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch

### 0.1 Three-prong Day-0 verify (against `main` HEAD `074362c4`)
- [x] **Prong 1 — path verify**: `loop.py` / `core/config/__init__.py` / `handler.py` / `scripts/benchmark_judge.py` / `tests/fixtures/verification/` exist; NEW files free (`benchmark_correction_hygiene.py`, `correction_hygiene_cases.yaml`, `test_benchmark_correction_hygiene.py`); `CHANGE-103` free; design note `40-*` free → ✅ all confirmed (benchmark at `backend/scripts/`; fixture `judge_benchmark.yaml`; max CHANGE=102; max design-note=39)
- [x] **Prong 2 — content verify** (drift → progress.md):
  - [x] **D-correction-branch** — `loop.py` `outcome=="correct"` branch still appends `assistant(parsed.text)` + `user(correction_block)` at ~2620 (single edit site) → ✅ confirmed loop.py:2617-2626
  - [x] **D-azure-role-pairing** — verify whether Azure OpenAI accepts back-to-back `user` messages (decides `summarize` drop-vs-placeholder) → check `adapters/azure_openai/` + a minimal probe if needed; shifts §3.1 + §8 → ✅ RESOLVED: adapter forwards verbatim (no merge/alternation); 57.101 injection proves consecutive-user works → `summarize` = DROP failed assistant turn (placeholder demoted to comment fallback)
  - [x] **D-config-anchor** — `verification_escalate_on_max` 3-layer wire still at `handler.py:666-696` (strategy mirrors it) → ✅ confirmed; #6 simpler (settings-only, per-tenant OUT)
  - [x] **D-benchmark-anchor** — `benchmark_judge.py` `load_cases/run_judge/build_report/main` + `judge_benchmark.yaml` fixture path (spike script mirrors it) → ✅ confirmed surface (+`report_to_markdown`/`_amain`/dataclasses); `run_arm` mirrors scaffold not fn-name; nuance: drives a correction cycle (~+5% Day 2)
  - [x] **D-build-correction-block** — `_build_correction_block` (loop.py:295-309) still carries reasons + suggested_correction (summarize arm depends on it) → ✅ confirmed; does NOT quote failed answer → summarize-drop is self-sufficient
- [x] **Prong 3 — schema verify**: N/A (no new DB table / migration / ORM column)
- [x] **D-baselines** — pytest 2747+5skip · wire 25 · Vitest 915 · mockup 51 · mypy 0/374 · run_all 10/10 → recorded (57.135 closeout; FIX-033 #319 on main may shift pytest → re-baseline Day 2 full gate)
- [x] **Catalog drift** — progress.md Day-0 table (D-IDs + implication + which §Risks row) → ✅ done (progress.md Day 0)
- [x] **Go/no-go** — scope-shift % → proceed (≤20%) / revise (20-50%) / abort (>50%); D-azure-role-pairing is the main scope lever → ✅ GREEN, net <10% shift, PROCEED

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-136-verification-correction-hygiene` (from `main` `074362c4`) → ✅ on branch

---

## Day 1 — Pluggable correction-context strategy + config wire (US-1, US-2)

### 1.1 `correction_context_strategy` in loop.py
- [x] **ctor param + branch**
  - DoD: `correction_context_strategy: str = "keep"` ctor param (`self._correction_context_strategy`); module const `_WITHHELD_PLACEHOLDER`; `outcome=="correct"` branch (~2620) branches — `keep` = current bytes, `summarize` = placeholder (or drop per D-azure-role-pairing) instead of `parsed.text`; `user(correction_block)` unchanged; `verification_attempts`/checkpoint untouched
  - Verify: `grep -n "correction_context_strategy\|_WITHHELD_PLACEHOLDER" backend/src/agent_harness/orchestrator_loop/loop.py`
  - ✅ done: ctor param (373) + `self._correction_context_strategy` (438) + branch at 2617-2632 — `if self._correction_context_strategy != "summarize": messages.append(assistant, parsed.text)`; `user(correction_block)` + counters/`continue` UNCHANGED. **Day-0 D-azure-role-pairing RESOLVED → summarize = DROP** (Azure accepts consecutive user); `_WITHHELD_PLACEHOLDER` const NOT defined (would be dead code) — demoted to an inline comment fallback note for a future role-pairing-strict provider (scope reduction, progress.md Day 0)

### 1.2 Settings + handler thread
- [x] **`chat_verification_correction_strategy` setting**
  - DoD: `Settings` field default `"keep"` (env `CHAT_VERIFICATION_CORRECTION_STRATEGY`); ∈ {keep,summarize} else fall back keep; `handler.py` resolves + passes `correction_context_strategy=` into `AgentLoopImpl(...)` (mirror `verification_escalate_on_max`)
  - Verify: `grep -n "chat_verification_correction_strategy\|correction_context_strategy=" backend/src/core/config/__init__.py backend/src/api/v1/chat/handler.py`
  - ✅ done: `chat_verification_correction_strategy: str = "keep"` (config:134) + handler resolve (settings-only, per-tenant OUT) + `not in ("keep","summarize") → "keep"` fallback + ctor pass; pydantic-settings auto-binds env `CHAT_VERIFICATION_CORRECTION_STRATEGY`

### 1.3 Unit tests (keep byte-unchanged + summarize context)
- [x] **strategy unit tests**
  - DoD: `keep` arm asserts messages byte-identical to pre-sprint (the rollback guarantee); `summarize` arm asserts the verbatim failed answer is absent AND the correction `user` message (reasons + suggested_correction) present + role-pairing legal; unknown-value→keep fallback
  - Verify: `cd backend && pytest tests/unit/orchestrator_loop/ -k correction -q`
  - ✅ done: +3 tests in `tests/unit/agent_harness/orchestrator_loop/test_loop_verification_gate.py` (`test_correction_keep_includes_failed_answer` / `_summarize_drops_failed_answer` / `_unknown_strategy_falls_back_to_keep`); the 5 pre-existing gate tests = the keep byte-identical regression guard (still green). `pytest ...test_loop_verification_gate.py -k correction` → 3 passed; full file 8 passed

### 1.x Partial gate
- [x] `cd backend && mypy src && black . && isort . && flake8 .` clean
  - ✅ done (changed-files scope): black reformatted loop.py + test (format only, re-ran tests 8 passed) · isort/flake8 clean · **mypy src 0/374** (baseline held)

---

## Day 2 — Measurement harness + real-Azure A/B (US-3)

### 2.1 `benchmark_correction_hygiene.py` + golden fixture
- [x] **mirror benchmark_judge.py**
  - DoD: `load_cases / run_arm(strategy,...) / build_report / main()`; report fields = retry_pass_rate, repeat_error_rate (retry-vs-failed similarity = self-conditioning signal), prompt_tokens mean per arm; `correction_hygiene_cases.yaml` fail-prone cases (trigger per Day-0 decision); `@pytest.mark.benchmark` skipif `RUN_AZURE_INTEGRATION`
  - Verify: `cd backend && python -c "import scripts.benchmark_correction_hygiene as b; print(b.load_cases, b.build_report)"`
  - ✅ done: full scaffold (load_cases / build_correction_messages / token_jaccard / run_arm / build_report / report_to_markdown / _amain / main + HygieneCase/ArmRun/HygieneReport dataclasses). **Design note**: harness REPRODUCES the loop's 2620 two-construction (NOT a `@pytest.mark.benchmark` wrapper — the real-Azure entry is `main()` gated by `RUN_AZURE_INTEGRATION` env, like benchmark_judge's CLI; the CI-safe pins are the unit test). 10-case `correction_hygiene_cases.yaml` (plausible-but-wrong answers)
  - Verify (actual): `python -c "import scripts.benchmark_correction_hygiene"` shadowed by `tests.unit.scripts` → validated via importlib in the unit test (15 passed)

### 2.2 CI-safe unit test
- [x] **MockChatClient load/run/report test**
  - DoD: `test_benchmark_correction_hygiene.py` covers `load_cases`/`build_report`/`run_arm` with MockChatClient (no Azure); mirrors `test_benchmark_judge.py`
  - Verify: `cd backend && pytest tests/unit/scripts/test_benchmark_correction_hygiene.py -q`
  - ✅ done: +15 tests (load schema/missing/dup · build keep/summarize/unknown · jaccard identical/disjoint/partial/empty · run_arm aggregate+construction · build_report flip-on-repeat/flip-on-pass/keep-on-noise). 15 passed

### 2.3 Real-Azure A/B run
- [x] **A/B report (keep vs summarize)**
  - DoD: `RUN_AZURE_INTEGRATION=1 AZURE_OPENAI_*=... python scripts/benchmark_correction_hygiene.py` produces a JSON report for both arms; numbers recorded in progress.md Day 2 (retry_pass_rate / repeat_error_rate / token delta)
  - Verify: report file written + numbers in progress.md
  - ✅ done: 10 cases × 2 arms (40 real Azure calls). **keep**: pass 100%, repeat 0.207, tokens 80.0 · **summarize**: pass 100%, repeat 0.165, tokens 62.8 · delta repeat **−0.043** / pass +0 / tokens −17.2. **Verdict KEEP** (effect directionally confirmed but < 5% threshold). Report → `artifacts/correction_hygiene_report.{md,json}` + numbers in progress.md Day 2

### 2.x Full gate
- [x] mypy `src` 0/374 · run_all 10/10 · backend pytest 2747+ + new · Vitest 915 (unchanged) · `npm run lint && npm run build` clean (NO `--silent`) · mockup 51 (`diff` empty) · black/isort/flake8 clean · LLM-SDK-leak clean
  - ✅ done: **pytest 2765 passed + 5 skip** (baseline 2747 + 18 new) · **v2 lints 10/10** (cwd=root; incl. check_llm_sdk_leak) · **mypy src 0/374** · black/isort/flake8 clean. Fixed 2 `test_handler.py` regressions (mock stub missing the new settings field — same pattern as 57.99 A2). Frontend (Vitest/mockup/npm) = unchanged sentinels (backend-only, untouched)

---

## Day 3 — Drive-through (US-4) — real UI + real backend + real LLM

### 3.1 Clean restart (Risk Class E)
- [x] kill stale `--reload` + orphan spawn-workers (Win32_Process PID/PPID/StartTime sweep); confirm fresh SOLE port owner + startup log; set `CHAT_VERIFICATION_CORRECTION_STRATEGY` to the strategy under test BEFORE restart (startup-resolved)
  - ✅ done: backend was NOT running (port 8000 free); started a FRESH single-process uvicorn (PID 51136, no `--reload` → no orphan risk) with strict `safety_review` judge; startup log confirmed DB/Redis/Azure/pricing wired + "startup complete". (Server stopped + port 8000 confirmed free at Day-3 close.)

### 3.2 Drive-through (MANDATORY — NOT gate-only) — "兩者結合" per user (AskUserQuestion 2026-06-23)
- [x] construct a fail-then-pass chat-v2 turn with real Azure (judge-threshold/prompt lever per Day-0)
  - ⚠️ real judge passed good answers on 2 prompts (social-eng + lock-picking) → no UI correction triggered (the 57.99-documented "real fail can't be forced cleanly"). Correction triggered DETERMINISTICALLY in the backend runtime drive-through via a controlled fail-once verifier instead.
- [x] **THE fix (real UI + backend runtime)**: correction loop + drop proven
  - ✅ **backend runtime** (real Azure + full `build_real_llm_handler` loop + controlled fail-once): `VerificationFailed → retry → VerificationPassed → LoopCompleted`; keep retry context = `[...,assistant,user]` (failed answer re-shown), summarize = `[...,user,user]` (failed answer DROPPED); wiring env→loop keep/summarize/banana→keep
  - ✅ **UI** (real chat-v2 + real Azure gpt-5.2 ×2): main flow end-to-end (send→answer render) + verification gate on main flow (Inspector "claim verified" + Loop visualizer verification_passed) + my 2620 change did NOT break the verification pass path (no-regression)
  - correction frontend RENDER (VerificationFailed→correction turn) = covered by 57.98/99 prior UI drive-throughs (frontend untouched this sprint)
- [x] Screenshot + observed-vs-intended → progress.md Day 3
  - ✅ `artifacts/dt-57136-keep-verification-passed.jpeg` + progress.md Day 3 (UI + runtime tables)

### 3.3 Decision gate (evidence → default)
- [x] **strategy verdict** — from the Day-2 A/B: flip default to `summarize` (1-line settings change) IF materially better, else keep `keep` + record negative result + mark #6 low-risk; verdict + rationale in progress.md + design note
  - ✅ **KEEP stays default** (A/B: summarize directionally better — repeat −0.043 / tokens −17.2 — but < 5% threshold; both arms retry 100% pass). `summarize` ships as a working env opt-in lever (wiring + drop runtime-verified). #6 = low-risk in the 2-turn correction case. Recorded in progress.md + design note.

---

## Day 4 — CHANGE-103 + design note 40 + closeout

### 4.1 CHANGE-103 + design note (spike)
- [x] **`CHANGE-103-verification-correction-hygiene.md`** (gap + fix + A/B numbers + drive-through PASS + AD closed) → ✅ `claudedocs/4-changes/feature-changes/CHANGE-103-verification-correction-hygiene.md`
- [x] **`40-verification-correction-hygiene-design.md`** (spike design note — 8-point gate: section per US / decision = the A/B verdict / verified invariants with file:line / open invariants / rollback = env-gate + revert / 17.md cross-ref / verification commands / fixtures) → ✅ `docs/03-implementation/agent-harness-planning/40-verification-correction-hygiene-design.md` (8/8 gate; 17.md = NO new contract, justified N/A — Cat 1 internal ctor param via existing config wire)

### 4.2 Closeout
- [x] retrospective.md Q1-Q7 + calibration (`verification-context-hygiene-spike` 0.60, 1st data point; flag if ratio out of band → re-point) → ✅ `phase-57/sprint-57-136/retrospective.md` (ratio ~1.0 IN band, KEEP 0.60)
- [x] Final gate sweep: mypy · run_all · pytest · Vitest · mockup · build · lint · LLM-SDK-leak → ✅ **pytest 2765 passed + 5 skip** · **mypy 0/374** · **v2 lints 10/10** (incl. check_llm_sdk_leak) · Vitest 915 / mockup 51 / wire 25 = unchanged sentinels (backend-only)
- [x] Navigators: CLAUDE.md Current-Sprint + Last-Updated · MEMORY.md pointer + subfile · next-phase-candidates (CLOSE `AD-Verification-Retry-Context-SelfConditioning`) · sprint-workflow matrix (`verification-context-hygiene-spike` row / 1st data point) → ✅ all 4 updated (CLAUDE.md PR-pending row + footer · MEMORY.md pointer + `project_phase57_136_*` subfile · next-phase-candidates AD CLOSED + 57.136 carryover block + per-tenant follow-on registered · matrix row added)
- [x] Anti-pattern self-check (retro Q5): AP-2/3/4/6/8/11 → violations; v2 lints 10/10 → ✅ retro Q5 (AP-2 no dead `_WITHHELD_PLACEHOLDER` · AP-4 runtime drive-through · AP-6 per-tenant OUT · all clean); v2 lints 10/10
- [ ] **Commit** → ⏳ PR push + open → CI → merge: PENDING USER CONFIRMATION (push is outward-facing per Developer Preferences) → post-merge status flip after gh-verified MERGED
