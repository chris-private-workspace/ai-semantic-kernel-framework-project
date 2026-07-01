# Sprint 57.153 — Checklist (make the in-loop verification judge memory-aware)

[Plan](./sprint-57-153-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch

### 0.1 Three-prong Day-0 verify (against `main` HEAD `5bbf1a77`)
- [x] **Prong 1 — path verify**: all 8 EDIT targets present; 3 NEW free; `CHANGE-120` + design note `56` free (55/119 highest)
- [x] **Prong 2 — content verify** (drift → progress.md):
  - [x] **D-memory-accesses-shape** — `builder.py:397-406` entries `{scope,time_scale,key,summary}`; summary PII-safe capped
  - [x] **D-trace-state-fresh** — `loop.py:1737` trace_state is throwaway → no Reducer needed
  - [x] **D-loop-ctor-kwarg** — `handler.py:744-753` + `loop.py:396,467` correction_context_strategy precedent confirmed
  - [x] **D-judge-template-only-2** — only `output_quality.txt:16` + `key_condition.txt:35` have `{trace}`; rest no-op
  - [x] **D-ap8-harness** — lint rooted `backend/src/agent_harness/`; `backend/scripts/` outside → no allowlist; `llm_judge.py` already allowlisted (L80)
  - [x] **D-judge-prompt-test** — `test_llm_judge.py:174-176` uses `in` substring asserts → won't break
- [x] **Prong 3 — schema verify**: N/A (no DB table / migration / ORM column change)
- [x] **D-baselines** — pytest 3053 · wire 26 · Vitest 922 · mockup 51 · mypy 0/397 · run_all 11/11
- [x] **Catalog drift** — progress.md Day-0 table (+ bonus D-lint-path)
- [x] **Go/no-go** — scope-shift ~0% → proceed

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-153-verification-memory-grounding` (from `main` `5bbf1a77`)

---

## Day 1 — state field + memory block + judge {memory} (US-1/US-2)

### 1.1 TransientState field
- [x] **`TransientState.injected_memory: str | None = None`** (state.py) — additive after `token_usage_so_far`; docstring + MHist updated; mypy clean
### 1.2 build_memory_block helper
- [x] **`build_memory_block(accesses, *, char_budget=None)`** (`_trace.py`) — `[memory:{scope}] {summary}` capped; empty/budget-0 → `""`; defensive non-dict; keep-head drop-tail; env `CHAT_VERIFICATION_MEMORY_CHAR_BUDGET`; 9 unit tests
### 1.3 LLMJudgeVerifier {memory} substitution + templates
- [x] **`_build_prompt` substitutes `{memory}`** from `state.transient.injected_memory` (guard `state is None`/`None` → `""`); template-without-{memory} byte-identical; 4 unit tests
- [x] **`output_quality.txt` + `key_condition.txt`** — RETRIEVED MEMORY `{memory}` section + grounding instruction + "MAY BE EMPTY"

### 1.x partial gate
- [x] `black . && isort . && flake8 . && mypy src` clean (E501 ×2 fixed) · 32 affected tests pass

---

## Day 2 — loop wiring + config flag + handler (US-3)

### 2.1 loop.py capture + thread + ctor kwarg
- [x] **Capture per-turn `memory_accesses`** — `turn_injected_memory: list[Any] = []` before the PromptBuilder branch; set from `artifact.layer_metadata["memory_accesses"]` (~2406); echo/naked path `[]`
- [x] **Thread to gate** — `_cat10_verify_gate(*, ..., injected_accesses=None)` builds `build_memory_block(...) if self._verification_memory_grounding else ""` + sets `injected_memory=memory_block or None` on the trace_state `TransientState`
- [x] **New ctor kwarg** `verification_memory_grounding: bool = True` → `self._verification_memory_grounding`; MHist updated. `=False` → `injected_memory=None` → judge byte-identical

### 2.2 config flag + handler wire
- [x] **`chat_verification_memory_grounding: bool = True`** (config; env `CHAT_VERIFICATION_MEMORY_GROUNDING`; docstring mirrors `correction_context_strategy`)
- [x] **handler** passes `verification_memory_grounding=settings.chat_verification_memory_grounding` (same site as `verifier_registry=`); fake-settings stub in test_handler.py +field (stub-drift caught + fixed)

### 2.3 gate-threading + state-field tests
- [x] **test_loop_verification_gate** — 3 tests: `_CapturingVerifier` asserts `trace_state.transient.injected_memory` = rendered block (ON) / None (OFF) / None (no accesses)
- [x] **build_memory_block + {memory} substitution tests** — done Day 1 (9 block + 4 substitution)

### 2.4 cross-category-import fix
- [x] **Re-export `build_memory_block`+`build_trace_block` from `verification/__init__.py`**; loop imports via package (check_cross_category_import FAIL → fixed; 11/11)

### 2.x Full gate
- [x] mypy `src` 0/397 · run_all 11/11 · black/isort/flake8 clean · LLM-SDK-leak clean · 188 affected tests pass (verification+loop+handler); FE untouched (full pytest/Vitest at closeout)

---

## Day 3 — A/B harness + Drive-through (US-4/US-5) — real UI + real backend + real LLM

### 3.0 A/B harness (US-4)
- [x] **`scripts/benchmark_memory_grounded_judge.py`** + **`tests/fixtures/verification/memory_grounded_judge_cases.yaml`** (5 grounded-recall + 5 contradiction) + **`tests/unit/scripts/test_benchmark_memory_grounded_judge.py`** (13 CI-safe, spy judge) — importable core; two arms; metrics false_reject + catch
- [x] **Real-Azure A/B verdict** — bare 0%→memory 0% false-reject, bare 0%→memory **100%** catch (+100pp) → **KEEP default ON**. Verdict logic corrected to two-sided OR (ship if false-reject↓ OR catch↑ materially, neither regresses). `benchmark_reports/` + artifacts.

### 3.1 Clean restart (Risk Class E)
- [x] Killed stale 57.152 PID 47908 (Win32_Process sweep, 0 spawn-worker orphans) → port 8000 free → fresh backend PID 49236 sole owner (new code, memory-grounding default ON); frontend :3007 untouched

### 3.2 Drive-through (MANDATORY — NOT gate-only) — STRONG PASS
- [x] Real chat-v2 + real Azure gpt-5.2: Leg 1 jamie states "Dana Okafor / Verification Loops" → memory_write ×2 + verify 0.99; Leg 2 NEW session 0-keyword "你知道我是誰?我負責哪個範疇?"
- [x] **THE fix**: Leg-2 Loop trace shows the user-layer memory injected (Dana facts + accumulated 57.148 Chris facts = a CONTRADICTION); agent recalled both grounded facts + flagged the conflict; in-loop **VerificationPassed score 0.98** (memory-aware judge passed the grounded recall) — vs the pre-fix BLIND judge (57.152 Leg-2) that rejected→no-recall
- [x] Screenshots `artifacts/sprint-57-153-leg{1,2}-*.png` + observed-vs-intended → progress.md Day 3

---

## Day 4 — CHANGE-120 + design note 56 + closeout

### 4.1 CHANGE-120 + design note 56
- [x] **`CHANGE-120-verification-memory-grounding.md`** (gap + fix + A/B verdict + drive-through PASS + AD closed)
- [x] **`56-verification-memory-grounding-design.md`** (8-point gate: §1 decision matrix TransientState-field-vs-ABC-kwarg / file:line per claim / verification commands / fixtures / open-invariant split / rollback = env flip / 17.md §1.1+§2.1 cross-ref)

### 4.2 Closeout
- [x] retrospective.md Q1-Q7 + calibration (NEW `verification-memory-grounding-spike` 0.60, 1st pt ~1.0 IN band, KEEP)
- [x] Final gate sweep: mypy `src` 0/397 · run_all 11/11 · pytest **3082 (+29)** · black/isort/flake8 clean · LLM-SDK-leak clean (FE untouched — no Vitest/mockup delta)
- [x] Navigators: CLAUDE.md Current-Sprint + Last-Updated · MEMORY.md pointer + subfile · next-phase-candidates (CLOSE `AD-Verification-Judge-Memory-Inject-Blind` + Phase58 carryovers) · sprint-workflow matrix
- [x] Anti-pattern self-check (retro Q5): AP-2/3/4/6/8/11 → 0 violations; v2 lints 11/11
- [x] **Commit → PR #360 push + open → CI all-green (5 required) → squash-merged** (gh-verified MERGED, main `0ce4d1fa`, mergedAt 2026-07-01T03:46:23Z) → post-merge status flip done (chore branch)
