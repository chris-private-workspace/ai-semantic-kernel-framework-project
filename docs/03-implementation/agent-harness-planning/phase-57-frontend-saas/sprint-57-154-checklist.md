# Sprint 57.154 — Checklist (A/B-measure combined-formation quality vs two focused calls)

[Plan](./sprint-57-154-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch

### 0.1 Three-prong Day-0 verify (against `main` HEAD `a0cf503a`)
- [x] **Prong 1 — path verify**: 3 NEW targets free; `core/config/__init__.py` present (contingent EDIT); `CHANGE-121` + design note `57-*` free (120 / 56 highest)
- [x] **Prong 2 — content verify** (drift → progress.md):
  - [x] **D-fixture-dir** — fixtures by-category (`guardrails/verification/context_mgmt/observability/tools/`); NO `memory/` → create NEW `tests/fixtures/memory/` (anticipated; no scope shift)
  - [x] **D-capture-signatures** — `UserLayer.write(*, content, tenant_id, user_id, time_scale, confidence, source, trace_context) -> UUID` + `upsert_summary(*, session_id, summary, key_decisions, unresolved_issues) -> UUID` — keyword-only, doubles match
  - [x] **D-ap8-scope** — AP-8 = repo-root `scripts/lint/check_promptbuilder_usage.py` root `backend/src/agent_harness`; `backend/scripts/` OUTSIDE → no allowlist
  - [x] **D-cheap-profile** — `build_azure_model_profile()->{action,cheap}` confirmed (`profile.py:57`); siblings use `profile.cheap`
  - [x] **D-test-scripts-dir** — `backend/tests/unit/scripts/` (__init__ + 9 sibling tests); importlib-shadow guard `parents[3]` + `sys.modules` pre-register (mirror `test_benchmark_memory_grounded_judge.py:30-42`)
  - [x] **D-form-signature** — `form(*, messages, session_id, tenant_id, user_id, known_facts, trace_context)`; `_form_combined` needs non-None user_id for facts (formation.py:115/161)
- [x] **Prong 3 — schema verify**: N/A (no DB table / migration / ORM column change)
- [x] **D-baselines** — pytest 3082 · wire 26 · Vitest 922 · mockup 51 · mypy 0/397 · run_all 11/11 (re-verify Day 2)
- [x] **Catalog drift** — progress.md Day-0 table
- [x] **Go/no-go** — scope-shift ~0% → proceed

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-154-combined-formation-quality-ab` (from `main` `a0cf503a`)

---

## Day 1 — harness core + capturing doubles (US-1)

### 1.1 Dataclasses + load_cases
- [x] **`FormationCase` / `ArmScore` / `FormationReport` dataclasses + `load_cases(path)`** (mirror `benchmark_memory_grounded_judge.py`)
  - DoD: schema-validate (dup-id / missing-key / bad-conversation raise `ValueError`); `expected_facts` = `list[list[str]]`, `expected_summary_points` = `list[str]`, `expects_facts` = bool ✅
  - Verify: 24 unit tests pass (incl. 5 load_cases tests) ✅

### 1.2 Capturing doubles + run_arm
- [x] **`_CapturingUserLayer.write` + `_CapturingSummaryStore.upsert_summary`** — signatures match the real seams (Day-0 D-capture-signatures); record facts `(content, confidence)` + summary dict; `write` returns `uuid4()`
- [x] **`run_arm(arm, cases, *, chat_client, judge)`** — per case builds the REAL `MemoryFormationWorker(...combined=(arm=="combined"))` via `_build_worker` + capturing sinks; `await worker.form(...known_facts=None)`; reads captured facts + summary → `ArmScore`
  - DoD: drives the real worker; no DB; unit test proves combined=1 chat() / separate=2 chat() per case ✅

### 1.x partial gate
- [x] black + isort + flake8 clean on the new script (mypy CI-gated on `src/` only — harness in `scripts/` is not; src untouched → 0/397)

---

## Day 2 — Hybrid oracle + corpus + two-sided verdict + tests (US-2/US-3)

### 2.1 Hybrid oracle
- [x] **`score_facts(emitted, expected_keyword_groups) -> (coverage, spurious_count)`** — deterministic normalized keyword-group coverage + spurious count ✅
- [x] **`score_summary(judge, conversation, summary_obj, expected_points) -> float`** — self-contained rubric via ChatClient ABC (cheap tier); tolerant numeric parse (0.0 on unparseable); provider-neutral; summary None → 0.0 (no judge call)
  - DoD: spy tests: None short-circuits (0 judge calls) + scripted score returned ✅

### 2.2 Golden corpus
- [x] **`memory_formation_quality_cases.yaml`** — 10 difficulty-graded cases (2 clear multi-fact / subtle-implicit / 2 zero-fact spurious-test / decisions-heavy / long multi-turn / identity / constraints / troubleshooting / prefs-stack)
  - DoD: `load_cases` parses all 10; each has conversation + expected_facts + expected_summary_points + expects_facts ✅

### 2.3 Two-sided verdict + tests
- [x] **`build_report` + `report_to_markdown` + `_amain` + `main`** — `combined_recommended` = no material regression on facts_coverage AND summary_score (≥ −Δ) AND `spurious_delta ≤ SPURIOUS_DELTA`; `MATERIALITY_DELTA = 0.05`; UTF-8 stdout; JSON+MD to `benchmark_reports/`
- [x] **`test_benchmark_combined_formation_quality.py`** (24 CI-safe) — load_cases happy/not-mapping/missing/dup/bad-turn; score_facts full/partial/spurious×2; _parse_score json/prose/clamp/bare/unparseable; score_summary none/spy; run_arm combined=1/separate=2/captured-facts; build_report keep/keep-within-Δ/flip-facts/flip-summary/flip-spurious
  - Verify: `pytest tests/unit/scripts/test_benchmark_combined_formation_quality.py -q` → **24 passed** ✅

### 2.x Full gate
- [x] run_all 11/11 · black/isort/flake8 clean · LLM-SDK-leak clean · 24 new tests pass (full pytest 3082+24 + mypy `src` 0/397 re-verified at closeout — src untouched)

---

## Day 3 — Real-Azure A/B run (US-4) — real LLM + real production formation path
_(Pure-backend measurement spike: NO user-facing surface → the real-Azure A/B IS the real-LLM verification, NOT a UI drive-through. Explicitly stated so it is not implied as usability. If the verdict FLIPS the default → add a chat-v2 drive-through of the separate path.)_

### 3.1 Environment (Risk Class E — LOW)
- [x] Harness is a standalone script building its own Azure profile (no running-backend dependency); root `.env` loaded via python-dotenv + runpy; fresh `python scripts/…` invocation (no `--reload` process)

### 3.2 Real-Azure A/B (real LLM — NOT gate-only)
- [x] Ran both arms over the real production formation path (real cheap-tier `chat()`), 3× to settle the borderline first run
- [x] **THE verdict**: facts_coverage {95,100,100}% vs {100,100,100}% (Run-1 −5pp = single-case single-keyword-group noise, did NOT reproduce); summary tied-to-better (mean Δ +0.009); spurious tied-to-better (0.30–0.40 vs 0.40) → **majority KEEP** → **KEEP `chat_memory_combined_formation` default ON** (NO config change; combined ≈ separate within LLM noise)
- [x] Report + observed-vs-intended → progress.md Day 3 + `artifacts/combined-formation-quality-ab-3runs.md`. Verdict KEEP → NO chat-v2 drive-through needed (default unchanged, no user-facing behavior change)

---

## Day 4 — CHANGE-121 + design note 57 + closeout

### 4.1 CHANGE-121 + design note 57
- [x] **`CHANGE-121-combined-formation-quality-ab.md`** (gap + harness + A/B verdict + real-LLM run + AD closed) ✅
- [x] **`57-memory-combined-formation-quality-ab-design.md`** (8-point gate all ✅: §2 decision matrices + file:line per claim + verification commands + fixtures + §5 open-invariant split + §6 1-line rollback + §4 17.md cross-ref)

### 4.2 Closeout
- [x] retrospective.md Q1-Q7 + calibration (`memory-formation-combine-ab-spike` 0.60, 1st data point ~0.95-1.03 IN band → KEEP) ✅
- [x] Final gate sweep: mypy `src --strict` **0/397** · run_all **11/11** · pytest **3106 passed / 6 skip** (3082 +24) · black/isort/flake8 clean · LLM-SDK-leak clean · FE untouched (no Vitest/mockup delta) ✅
- [x] Navigators: CLAUDE.md Current-Sprint + Last-Updated · MEMORY.md pointer + subfile · next-phase-candidates (CLOSE the AD + carryovers) · sprint-workflow matrix (`memory-formation-combine-ab-spike` 0.60 row) ✅
- [x] Anti-pattern self-check (retro Q5): AP-2/3/4/6/8/10/11 → 0 violations; v2 lints 11/11 ✅
- [x] **Commit `0fa81705`** → PR #362 pushed + opened → CI all-green (5 required) → squash-merged (gh-verified MERGED, main `64732999`, mergedAt 2026-07-01T05:50:09Z) → status flip done (chore branch)
