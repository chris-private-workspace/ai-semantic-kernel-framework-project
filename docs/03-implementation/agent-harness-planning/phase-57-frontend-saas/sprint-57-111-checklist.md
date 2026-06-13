# Sprint 57.111 — Checklist (A3: trace-aware critique verifier — the in-loop Cat 10 judge sees recent turns + tool errors via the real `LoopState` (the load-bearing edit is `loop.py`'s `state=cast(LoopState, None)` → real state) + a permanent cheap-judge accuracy benchmark — labeled golden fixture + a `benchmark`-marked real-LLM harness + tracked metric, CI-deselected — the LAST harness-deepening slice)

[Plan](./sprint-57-111-plan.md)

---

## Day 0 — Plan-vs-Repo Verify + Branch

### 0.1 Three-prong Day-0 verify (against `main` HEAD `37e90f06`) — DONE, catalogued in progress.md D1-D11
- [x] **Prong 1 — path verify**: EDIT files Glob-1 (`loop.py` / `llm_judge.py` / `output_quality.txt` / `_abc.py` / `rules_based.py` / `verification/tools.py` / `cat9_mutator.py` / `cat9_fallback.py` / `pyproject.toml` / `25-…-design.md` exact paths); NEW files Glob-0 (`verification/_trace.py` / `templates/forced_fail_trace.txt` / `tests/fixtures/verification/judge_benchmark.yaml` / `tests/benchmark/{__init__,test_judge_accuracy}.py`); `test_judge_accuracy` basename 0 collisions; guardrails fixture precedent confirmed (`tests/fixtures/guardrails/*.yaml` ×4). **D6 drops `backend-ci.yml` from the list.**
- [x] **Prong 2 — content verify** (D1 cast-None ×4 sites / D2 no-state-in-_run_turns / D3 LoopState-build idiom + ABC-widen decision / D4 _build_prompt mechanism / D5 marker register + no real_llm / D6 CI no -m filter → skipif gate / D7 judge temp / D8 profile both tiers / D9 note-25 structure): ALL resolved — see progress.md D1-D11
- [x] **Prong 3 — schema verify**: N/A (no DB / no migration — benchmark is a YAML fixture + a test; verification_log NOT used) — recorded explicitly (D10)
- [x] **Catalog drift** findings in progress.md Day 0 (D1-D11 + implications; plan §8 cross-ref)
- [x] **Go/no-go**: GO — net scope shift <20% (D6 removes a file; D7 adds a tiny judge temp param; D3 widens the ABC, removing a type-lie); no loop.py logic rewrite forced

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-111-trace-aware-critique-benchmark` (from `main` `37e90f06`)

---

## Day 1 — Backend: trace-aware critique verifier (US-1) ✅

### 1.1 Trace builder + judge prompt
- [x] **`verification/_trace.py`** (NEW): `build_trace_block(messages, *, max_messages, char_budget) -> str` — bounded recent-msgs + tool-errors formatter (provider-neutral on `Message` list, no SDK import); module constants + env overrides (`CHAT_VERIFICATION_TRACE_MAX_MESSAGES` / `_CHAR_BUDGET`) + per-message cap; file header + WHY
- [x] **`verification/llm_judge.py`**: `_build_prompt(output, state)` builds `{trace}` via `build_trace_block(state.transient.messages)` when state non-None, substitutes; `state=None` → empty `{trace}` (back-compat); + optional `temperature` ctor param (D7 — benchmark determinism; default 1.0 = byte-identical); MHist 1-line
- [x] **`verification/templates/output_quality.txt`**: added a `{trace}` section + a 4th trace-contradiction failure bullet; "MAY BE EMPTY" wording keeps back-compat (no-state → judge output alone)
- [x] **config**: module constants + env override IN `_trace.py` (NOT `core/config` — D7: verification-internal tuning knobs, not tenant policy → keeps core/config untouched)

### 1.2 Gate threads the real state (US-1 load-bearing) + ABC widen (D1/D3)
- [x] **`loop.py`**: `_cat10_verify_gate` gains a `messages` param + builds a minimal `trace_state` (mirroring `compact_state` :2096) + forwards `state=trace_state` to `verifier.verify` (removed `cast(LoopState, None)` @ :1684 + the now-unused `cast` import); call site passes `messages=messages`; MHist 1-line — NO loop logic rewrite (data threaded in)
- [x] **ABC widen (D3)**: `Verifier.verify` `state: LoopState → LoopState | None = None` (`_abc.py`) — removes the 4-site `cast(LoopState, None)` type-lie; `rules_based.py` signature widened (ignores state by design); the 3 Cat 9 fallback judge sites (`verification/tools.py` / `cat9_mutator.py` / `cat9_fallback.py`) drop the cast → `state=None` + remove now-unused `cast`/`LoopState` imports
- [x] **Tests ADD (CI-safe) ×13**: `test_trace_block.py` ×8 (empty / system-only / renders user+assistant+tool / tool-call annotation / max_messages truncation / char_budget tail / per-msg cap / zero-bound) · `test_llm_judge_trace.py` ×5 (trace in prompt when state present / empty trace when state=None / back-compat no-`{trace}` template / temperature 0.0 passed / default temp 1.0). No `state is None` test pin needed convert (existing `_state()` helper returns `cast(LoopState, None)` → already exercises the back-compat path)
  - DoD: verification + guardrails + orchestrator suites **617 passed** (+13 new, 0 del) ✓; `loop.py` diff = arg + helper param + trace_state build (NO logic rewrite, reviewed) ✓; **mypy src 0/360** (359→360 = new `_trace.py`) ✓; black/isort/flake8 0 ✓

---

## Day 2 — Backend: permanent cheap-judge benchmark (US-2) ✅

### 2.1 Golden fixture + marker
- [x] **`tests/fixtures/verification/judge_benchmark.yaml`** (NEW): **28** labeled cases `{id, output, trace?, expected_passed, category}` — clear_pass ×8 / clear_fail ×8 / trace_dependent ×7 (5 fail-when-trace-disproves + 2 trace-consistent-pass — exercises US-1 + drives trace_delta) / borderline ×5 (excluded from the floor); mirrors the `tests/fixtures/guardrails/*.yaml` shape; hand-labeled to the `output_quality` judge contract
- [x] **`pyproject.toml`**: registered `benchmark` marker (`--strict-markers` is ON → required)
- [x] **`.github/workflows/backend-ci.yml`**: **NOT edited** (D6 — CI runs `pytest -v --tb=short` with NO `-m` filter; real-LLM tests gate via `RUN_AZURE_INTEGRATION` skipif, NOT marker deselection → the benchmark SKIPS in CI for free)
- [x] **`.gitignore`** (root): ignore `/backend/benchmark_reports/`

### 2.2 Harness + metric math (logic in `scripts/`, real-LLM wrapper in `tests/benchmark/`)
- [x] **`scripts/benchmark_judge.py`** (NEW — the reusable logic home, precedent `verify_audit_chain.py`): `BenchCase` / `JudgeRun` / `BenchReport` + `load_cases` (schema-validate) + `run_judge(judge, cases, *, with_trace)` (builds the trace LoopState per case) + `build_report` (pure accuracy / cheap-vs-strong agreement / per-category / trace_delta) + `CHEAP_ACCURACY_FLOOR=0.70` (the tracked metric; floor judged on unambiguous categories only) + `main()` CLI (build Azure profile → run both tiers → write JSON+MD report). file header + WHY
- [x] **`tests/benchmark/test_judge_accuracy.py`** (NEW, `@pytest.mark.benchmark` + `RUN_AZURE_INTEGRATION` skipif): real Azure `build_azure_model_profile()` → `profile.cheap` + `profile.action` judges at temp 0 → cheap/strong/agreement/trace_delta → assert `cheap_passes_floor`; **loads `benchmark_judge` via importlib** (D12 — the `tests.unit.scripts` package shadows `scripts/` once collected; same idiom as `test_verify_audit_chain.py`)
- [x] **Harness-math tests ADD (CI-safe, NOT benchmark-marked) ×9** (`tests/unit/scripts/test_benchmark_judge.py`, importlib-loaded): real-fixture schema (28, 4 categories, td has trace, cp has none, unique ids) · load rejects missing-key / bad-category / duplicate-id ×3 · `run_judge` builds state for trace cases + accumulates tokens + with_trace=False → state None ×2 · `build_report` perfect→floor-pass + cheap_vs_strong agreement ×1 · trace_delta positive ×1 · floor excludes borderline ×1
  - DoD: CI pytest green WITHOUT the benchmark (skipif → skipped; `-m "not benchmark"` deselects 1) ✓; **9 passed + 1 skipped** together ✓; mypy `src` 0/360 (scripts not gated but logic CI-tested) ✓; black/isort/flake8 0 ✓; loop.py / wire / codegen / DB UNTOUCHED ✓

---

## Day 3 — Full gates + drive-through (US-3) + CHANGE-078

### 3.1 Full gate sweep
- [ ] mypy strict 0/359 · black/isort/flake8 0 (all four) · run_all 10/10 from repo root (count 24; no codegen diff) · full pytest +N (0 del, benchmark-marked excluded) vs 2502 baseline · Vitest 837 holds (no FE) · mockup-fidelity 51 holds · `loop.py` diff = arg+param only (reviewed line-by-line) · wire schema diff empty

### 3.2 Drive-through (US-3 — real UI :3007 + fresh no-reload backend + real Azure; zero dev-login; Risk Class E clean restart, sole-owner verified, stale 57.110-knob backend killed)
- [ ] **Leg A (trace-aware critique end-to-end)**: construct a trace-dependent scenario (a prompt producing a tool error then a superficially-fine final answer) → trace-aware judge's `VerificationFailed.reason` visibly references the trace (tool error / prior turn) → correction turn → `VerificationPassed` → answer renders; reuse "soft forced-fail judge template" (:140) + "forced-fail steers no-tools" (:155); if non-deterministic, the `forced_fail_trace.txt` strict template makes the judge cite the trace deterministically; screenshot
- [ ] **Leg B (real benchmark run + verdict)**: `pytest -m benchmark` once against real Azure → real cheap_accuracy / strong_accuracy / agreement / trace_delta / cost numbers in the report artifact → write the human go/no-go verdict (keep cheap tier vs move judge to strong) from the measured number vs the tracked floor
- [ ] Screenshots + observed-vs-intended table in progress.md; report artifact saved under `sprint-57-111/artifacts/` (never-commit) + the verdict numbers into the design note
  - DoD: leg A trace-citing critique PASS; leg B real numbers recorded + verdict written

### 3.3 CHANGE-078
- [ ] `claudedocs/4-changes/feature-changes/CHANGE-078-trace-aware-critique-cheap-judge-benchmark.md` (1-page)

---

## Day 4 — Closeout

### 4.1 Closeout
- [ ] retrospective.md Q1-Q7 + calibration (NEW `verification-trace-and-benchmark-spike` 0.60 1st data point + ratio + agent-delegated: no) + progress.md final
- [ ] Design note 25 §5 trace-aware critique design + the benchmark verdict (design note 24 open-invariant RESOLVED with the real number + go/no-go, OR a focused benchmark design note 26 — finalized per §5.5); MHist 1-line
- [ ] Navigators: CLAUDE.md Current-Sprint row + Last-Updated; MEMORY.md quality pointer + memory subfile `project_phase57_111_trace_aware_critique_benchmark.md`; next-phase-candidates A3-DONE block + roadmap A-line (A-family 3/3 — harness-deepening 10-slice set COMPLETE); sprint-workflow matrix NEW row `verification-trace-and-benchmark-spike` 0.60; 17.md if the Verifier contract changed
- [ ] Spike design-note 8-point quality gate self-check (spike sprint → design note required per §5.5)
- [ ] PR (push + open on user authorization)
