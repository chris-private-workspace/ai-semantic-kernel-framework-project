# Sprint 57.141 — Checklist (pass^k reliability eval harness, research #2)

[Plan](./sprint-57-141-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch

### 0.1 Three-prong Day-0 verify (against `main` HEAD `196d8892`)
- [x] **Prong 1 — path verify**: NEW targets free (`scripts/benchmark_pass_k.py` / `tests/fixtures/observability/pass_k_cases.yaml` / `tests/unit/scripts/test_benchmark_pass_k.py`); `tests/fixtures/observability/` = NEW dir; next = **CHANGE-108** + **design note 45** ✓
- [x] **Prong 2 — content verify** (drift → progress.md):
  - [x] **D-chatclient-abc** — `ChatClient(ABC)` `chat_client.py:63` has 5 abstract (chat/stream/count_tokens/get_pricing/supports_feature) → wrapper delegates all + injects on chat
  - [x] **D-handler-factory-shape** — factory takes NO client param → direct-construct `AgentLoopImpl` with `_FaultInjectingChatClient(profile.action)` for λ
  - [x] **D-verifier-ctor** — `LLMJudgeVerifier(*, chat_client, judge_template, temperature=1.0).verify→.passed`; rules oracle = inline exact/contains (NOT RulesBasedVerifier) → scope ↓
  - [x] **D-loop-run-noDB** ✅ GREEN — `AgentLoopImpl.__init__:318` deps `message_store`/`checkpointer`/`tenant_id` ALL `\|None=None`; `run():1959` `message_store is None→[]` → DB-less drivable
  - [x] **D-benchmark-marker** — `benchmark` marker registered `pyproject.toml:68` (RUN_AZURE_INTEGRATION=1)
  - [x] **D-faultclient-leak** — subclass `adapters._base.ChatClient` (no native import) → LLM-SDK-leak clean
- [x] **Prong 3 — schema verify**: N/A (no DB table / migration / ORM column — offline harness)
- [x] **D-baselines** — pytest 2843+5skip · wire 26 · Vitest 920 · mockup 51 · mypy 0/380 · run_all 10/10 (FE/mockup untouched; full re-verify Day-2 gate)
- [x] **Catalog drift** — progress.md Day-0 table (6 D-rows, all GREEN)
- [x] **Go/no-go** — **GO**; scope NOT shifted (slightly ↓: rules oracle plain compare, loop DB-less)

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-141-passk-reliability-harness` (from `main` `196d8892`)

---

## Day 1 — Harness core + hybrid oracle (US-1/2/5)

### 1.1 `PassKCase` + `load_cases`
- [x] **`PassKCase` frozen dataclass + `load_cases(YAML)` with schema validation**
  - DoD: required keys / unique id / category enum / oracle_type enum validated; judge cases carry `expected` criterion; mirrors `benchmark_judge.load_cases:109-151` ✓
  - Verify: `test_load_cases_*` (4 tests: real corpus + dup-id + bad-category + bad-oracle) green ✓

### 1.2 `run_case` (k-run driver) + hybrid oracle
- [x] **`run_case(case, *, k, action_client, judge_client, arm, variant, user_input, fault_rate, rng)` driving `loop.run()` k times + capturing answer/tool_seq/tokens/stop_reason**
  - DoD: per-run pass via `evaluate()` (rules inline exact/contains | LLMJudge open-ended via per-case criterion raw template); returns `CaseRuns` ✓
  - Verify: `test_run_case_drives_loop_offline` (spy ChatClient + real AgentLoopImpl, no Azure) + `test_evaluate_*` (5) green ✓

### 1.3 `build_report` (4-axis metrics) + MD/JSON
- [x] **`build_report` computing pass@1 / pass^k / divergence / answer+tool-seq consistency / λ / ε / per-category + MD+JSON writer**
  - DoD: pure function; metrics correct on synthetic CaseRuns; MD table + JSON to `benchmark_reports/` ✓
  - Verify: `test_build_report_*` (5: pass_k/consistency/lambda/epsilon/markdown) green ✓

### 1.x partial gate
- [x] black/isort/flake8 clean + mypy `src` 380/0 (harness type-resolves clean vs src; scripts/ not CI-mypy-gated, same as `benchmark_judge.py`)

---

## Day 2 — Fault (λ) + Perturbation (ε) axes + corpus + CI tests (US-3/4)

### 2.1 `_FaultInjectingChatClient` + λ axis
- [x] **`_FaultInjectingChatClient(ChatClient)` (rng-injectable transient raise) + λ degradation in report**
  - DoD: wraps inner; `rng.random()<fault_rate`→`InjectedFault` else delegate; all 6 ABC methods delegate; report `lambda_degradation = pass^k(0)−pass^k(λ)` ✓ (decision: inject at chat client, loop uses DEFAULT error handling; baseline/fault differ only by wrapper — measures real-loop resilience as-is; escaped fault → failed run)
  - Verify: `test_fault_client_*` (3: raises-at-high-rate / passthrough-at-zero / seeded-deterministic) green; LLM-SDK-leak lint 3/3 ✓

### 2.2 ε perturbation axis
- [x] **per-case `perturbations` runs + `epsilon_instability` (pass^k spread across paraphrases)**
  - DoD: original + variants each get a pass^k; aggregate mean spread + per-case in report ✓
  - Verify: `test_build_report_epsilon_instability` green ✓

### 2.3 Corpus `pass_k_cases.yaml`
- [x] **12 cases: easy (rules) / multistep (where pass^k<pass@1 may show) + 2 judge; 2 with `perturbations`**
  - DoD: difficulty gradient (5 easy + 7 multistep; 10 rules + 2 judge); rules cases deterministic `expected`; judge cases criterion; schema-valid ✓ (note: `tool_use` schema-supported but deferred from shipped corpus — DB-free robustness; design note 45 §Open)
  - Verify: `test_load_cases_parses_real_corpus` green (≥10 cases, multistep + judge + perturbation present) ✓

### 2.4 `main()` argparse + CI-safe test file
- [x] **`main()` (`--fixture --out --k --fault-rate --epsilon` + UTF-8 stdout) + `test_benchmark_pass_k.py` (importlib + spy ChatClient + seeded rng, NO Azure)**
  - DoD: importlib idiom mirrors `test_benchmark_judge.py`; all 17 unit tests green without Azure ✓ (real-Azure path = `_amain` lazy Azure import, run on demand)
  - Verify: `pytest tests/unit/scripts/test_benchmark_pass_k.py` → 17 passed ✓

### 2.x Full gate
- [x] mypy `src` 380/0 ✓ · v2 lint tests 21 pass (incl. llm_sdk_leak 3) ✓ · black/isort/flake8 clean ✓ · LLM-SDK-leak clean ✓ · Vitest/mockup/build UNTOUCHED (FE not touched this sprint)
- [x] backend pytest **2859 passed + 5 skip** (2843 baseline + 17 new = 2860; the 1 "fail" = pre-existing `AD-Billing-Outbox-Drain-Test-Flake` Risk Class C — **passes in isolation** (re-ran 1 passed); zero src edit this sprint so not caused here)
  - Note (Day-0 drift): CLAUDE.md/`sprint-workflow.md` reference `scripts/lint/run_all.py` which does NOT exist — v2 lints migrated to `tests/unit/scripts/lint/` pytest tests (stale-doc carryover, NOT this sprint's fix)

---

## Day 3 — Drive-through (US-6) — real Azure harness run (offline; NOT chat-v2 UI)
_(Pure-offline measurement harness → the real-Azure run IS the drive-through, #135/#137/#138 "CATCH = the harness" pattern. NOT gate-only.)_

### 3.1 Clean env (Risk Class E)
- [x] Fresh `python` harness invocation (no long-running server); `.env` Azure creds loaded (`set -a && source ../.env && set +a`); `build_azure_model_profile` built a real gpt-5.2 client ✓ (k=1 smoke first → wiring proven, 14 calls)

### 3.2 Drive-through (MANDATORY — real Azure, cost-bounded k)
- [x] Ran `benchmark_pass_k.py --k 3 --fault-rate 0.2 --epsilon` on real Azure (gpt-5.2) — ALL 4 axes exercised: 12 cases · k=3 · **90 runs · 94,373 tokens** ✓
- [x] **THE verdict**: pass@1 100% / pass^k 100% (divergence 0% — honest: corpus too easy to stress divergence, valid verdict) · **answer-consistency 75% (KEY signal)** · **λ degradation 50% (KEY signal)** · ε instability 0% ✓
- [x] Report MD+JSON → `artifacts/passk-drivethrough-verdict.{md,json}` (tracked; `benchmark_reports/` is gitignored); verdict table + reading + AP-4 check → progress.md Day 3 ✓

---

## Day 4 — CHANGE-NNN + design note + closeout

### 4.1 CHANGE-NNN + design note
- [x] **`CHANGE-108-passk-reliability-harness.md`** (gap + 4-axis harness + drive-through verdict + AD closed) ✓
- [x] **Spike design note** `45-passk-reliability-eval-design.md` (8/8-point gate; §3 cross-category N/A — reuses ChatClient/Verifier/AgentLoop ABCs, no new contract) ✓

### 4.2 Closeout
- [x] retrospective.md Q1-Q7 + calibration (`passk-reliability-spike` 0.60, 1st data point ~1.0 IN band → KEEP) ✓
- [x] Final gate sweep: mypy src 380/0 · pytest 2859+5skip · v2 lints 21 · black --check unchanged · flake8 clean · LLM-SDK-leak clean · Vitest/mockup/build UNTOUCHED ✓
- [x] Navigators: CLAUDE.md Current-Sprint + Last-Updated · MEMORY.md pointer + subfile · next-phase-candidates (CLOSED research #2; next #5) · sprint-workflow matrix (`passk-reliability-spike` row) ✓
- [x] Anti-pattern self-check (retro Q5): AP-2/3/4/6/8/11 no violations; v2 lint tests 21 pass ✓
- [x] **Commit** local `ad813fa4` (15 files, +2048; explicit-staged sprint files only — README.md w/ user's concurrent user-interrupt edit LEFT for the user; pre-existing untracked + AGENTS.md deletion untouched) → ⏳ PR push + open → CI → merge: **PENDING USER CONFIRMATION** (push is outward-facing) → post-merge status flip after gh-verified MERGED
