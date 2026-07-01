# Sprint 57.154 Progress — A/B-measure combined-formation quality vs two focused calls

**Plan**: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-154-plan.md`
**Checklist**: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-154-checklist.md`
**Branch**: `feature/sprint-57-154-combined-formation-quality-ab` (from `main` `a0cf503a`)
**AD**: `AD-Memory-Combined-Formation-AB-Quality` (57.152 carryover)

---

## Day 0 — 2026-07-01 — Plan-vs-Repo Verify (三-prong) + Branch

### Three-prong verify (against `main` HEAD `a0cf503a`)

**Prong 1 — path verify** ✅
- `backend/scripts/benchmark_combined_formation_quality.py` — FREE (0 results)
- `backend/tests/unit/scripts/test_benchmark_combined_formation_quality.py` — FREE (not among the 9 existing sibling benchmark tests)
- `CHANGE-121` FREE (CHANGE-120 highest) · design note `57-*` FREE (56 highest)
- `backend/src/core/config/__init__.py` present (contingent EDIT target)

**Prong 2 — content verify** ✅ (all resolved pre-code)

| ID | Finding | Implication |
|----|---------|-------------|
| **D-fixture-dir** | `backend/tests/fixtures/` is organized by CATEGORY (`guardrails/` `verification/` `context_mgmt/` `observability/` `tools/`); NO `memory/` dir yet | Create NEW `backend/tests/fixtures/memory/` for the Cat-3 corpus (consistent with the per-category convention — layered_compaction→context_mgmt, pass_k/otel→observability). Anticipated in plan ("else NEW dir"). No scope shift. |
| **D-capture-signatures** | `UserLayer.write(*, content, tenant_id=None, user_id=None, time_scale="long_term", confidence=0.5, source=None, trace_context=None) -> UUID` (`user_layer.py:124`); `DBSessionSummaryStore.upsert_summary(*, session_id, summary, key_decisions, unresolved_issues) -> UUID` (`session_summary_store.py:117`) | Both keyword-only → capturing doubles match byte-for-byte. |
| **D-ap8-scope** | AP-8 lint = repo-root `scripts/lint/check_promptbuilder_usage.py`, root `backend/src/agent_harness` (run_all default); `backend/scripts/` is OUTSIDE | Self-contained summary judge (ChatRequest via ChatClient ABC in the harness) needs NO allowlist. Confirmed by precedent (9 sibling harnesses pass run_all 11/11). |
| **D-cheap-profile** | `build_azure_model_profile(policy=None) -> ModelProfile` returns `{action, cheap}` (`adapters/azure_openai/profile.py:57`) | The on-demand real run uses `profile.cheap` (the production cheap-tier ChatClient), same as siblings. |
| **D-test-scripts-dir** | `backend/tests/unit/scripts/` exists (`__init__.py` + 9 sibling tests); importlib-shadow guard confirmed (`test_benchmark_memory_grounded_judge.py:30-42`: `_ROOT = parents[3]`, register in `sys.modules` BEFORE `exec_module`) | Mirror the shadow-load idiom exactly (the `tests.unit.scripts` package shadows a plain `from scripts.… import`). |
| **D-form-signature** | `MemoryFormationWorker.form(*, messages, session_id, tenant_id, user_id, known_facts, trace_context)` (`formation.py:115`); `_form_combined` gates `want_facts = extractor is not None and user_id is not None`, `want_summary = summarizer is not None` (`formation.py:161`) | Harness must wire BOTH collaborators + pass a non-None `user_id`; `known_facts=None` for both arms (equal footing). |

**Prong 3 — schema verify** — N/A (no DB table / migration / ORM column change; capturing doubles only)

**D-baselines** (57.153 closeout; re-verify Day 2 full gate): pytest 3082 · wire 26 · Vitest 922 · mockup 51 · mypy 0/397 · run_all 11/11

**Go/no-go**: scope-shift ~0% (only a NEW `fixtures/memory/` category dir) → **PROCEED**

### Branch
- `git checkout -b feature/sprint-57-154-combined-formation-quality-ab` from `main` `a0cf503a` ✅

---

## Day 1-2 — 2026-07-01 — Harness + Hybrid oracle + corpus + tests

Interdependent, so the whole harness module + oracle + corpus + tests were written together; Day-2 corpus/tests split preserved in the checklist.

### Code (backend-only, ZERO src change)
- **NEW `backend/scripts/benchmark_combined_formation_quality.py`** (~370 lines) — mirrors `benchmark_memory_grounded_judge.py`: `FormationCase`/`ArmScore`/`FormationReport` dataclasses + `load_cases` (schema-validate) + `_CapturingUserLayer`/`_CapturingSummaryStore` (drive the REAL `MemoryFormationWorker.form()`, capture the terminal write — AP-10 safe) + `run_arm` + Hybrid oracle (`score_facts` deterministic + `score_summary` LLM-judge rubric via ChatClient ABC) + two-sided `build_report` + `report_to_markdown` + lazy-Azure `_amain` + UTF-8 `main`.
- **NEW `backend/tests/fixtures/memory/memory_formation_quality_cases.yaml`** — 10 difficulty-graded cases (2 clear multi-fact / subtle-implicit / 2 zero-fact spurious-test / decisions-heavy / long multi-turn / identity / constraints / troubleshooting / prefs-stack).
- **NEW `backend/tests/unit/scripts/test_benchmark_combined_formation_quality.py`** — 24 CI-safe tests (spy formation + judge ChatClients + capturing sinks). Key: `run_arm` drives the REAL worker offline asserting the efficiency invariant (combined = 1 chat() / separate = 2 chat() per case).

### Gates
- black + isort + flake8 clean (fixed 7 E501 in docstrings/comments + 1 F841) ✅
- **24 new tests passed** (0.30s) ✅
- **run_all 11/11 green** (llm_sdk_leak + cross_category + AP-8 all pass — harness in `backend/scripts/` outside AP-8 root, self-contained judge needs no allowlist) ✅
- mypy: CI runs `mypy src/ --strict` only (`.github/workflows/backend-ci.yml:152`); harness in `scripts/` + test in `tests/` are NOT CI-mypy-gated; src untouched → 0/397 unchanged. (The standalone `mypy <file>` "cannot subclass ChatClient (Any)" errors are config-scoping artifacts — the sibling harnesses subclass ChatClient identically and pass CI.)

---

## Day 3 — 2026-07-01 — Real-Azure A/B run (US-4) — real LLM + real production formation path

Ran the harness against real Azure cheap-tier (root `.env` loaded via python-dotenv + runpy; the harness is a standalone script building its own Azure profile — no running-backend dependency, Risk Class E LOW). Each run = 10 cases × 2 arms × (1–2 formation calls + 1 judge call) ≈ 50 real cheap-tier calls.

### The verdict — 3 runs (settled the borderline first run)

| Run | facts_coverage (C/S/Δ) | summary_score (C/S/Δ) | spurious (C/S/Δ) | verdict |
|-----|------------------------|-----------------------|------------------|---------|
| 1 | 95% / 100% / **−5.00%** | 0.994 / 0.990 / +0.004 | 0.40 / 0.40 / +0.00 | FLIP |
| 2 | 100% / 100% / +0.00% | 0.992 / 0.994 / −0.002 | 0.30 / 0.40 / −0.10 | KEEP |
| 3 | 100% / 100% / +0.00% | 0.994 / 0.970 / +0.024 | 0.30 / 0.40 / −0.10 | KEEP |

**Observed vs intended**: intended = a real-LLM run over the production formation path emitting a KEEP/FLIP verdict on the combined default. Observed = the mechanical single-run verdict flipped on Run 1 at EXACTLY the −5pp boundary (float `0.95−1.0 = −0.05000…04`), driven by ONE case dropping ONE keyword-group (the smallest measurable unit on a 10-case mean). Re-ran 2× → both clean KEEP; the −5pp did NOT reproduce → run-to-run LLM noise (temp=0 is deterministic-*ish*), NOT a stable regression. Summary tied-to-better for combined (mean Δ ≈ +0.009); spurious tied-to-better (combined 0.30–0.40 vs 0.40).

**Decision (honest finding)**: combined ≈ separate **quality-equivalent within LLM noise** → **KEEP `chat_memory_combined_formation` default ON** (57.152 validated; ~2× efficiency win holds at no material quality cost). **NO config change; NO chat-v2 drive-through** (default unchanged → no user-facing behavior change). Full 3-run evidence: `artifacts/combined-formation-quality-ab-3runs.md`.

---
