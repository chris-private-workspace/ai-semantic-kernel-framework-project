# Sprint 57.158 — Checklist (memory vector-recall precision A/B)

[Plan](./sprint-57-158-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch

### 0.1 Three-prong Day-0 verify (against `main` HEAD `65157788`)
- [x] **Prong 1 — path verify**: 3 NEW free (Glob 0); ZERO EDIT; `CHANGE-125` free (highest 124) · design note `61` free (highest 60); `scripts/__init__.py` + `pythonpath=["."]` OK ✅
- [x] **Prong 2 — content verify** (all 5 confirmed vs real code → progress.md Day-0 table):
  - [x] **D-fake-store-reuse** — `_FakeMemStore` inlined in 2 test files (not shared) → re-inline in the new offline test ✅
  - [x] **D-profile-nonempty-query** — `profile()` passes `query=""` (`retrieval.py:161-197`, docstring confirms ILIKE '%%') → query-agnostic baseline ✅
  - [x] **D-search-ingest-idempotency** — `_ingest` per-user count guard `if count==expected: return` (`vector_index.py:135`) → harness needn't pre-ingest ✅
  - [x] **D-corpus-discriminates** — keyword `ilike(%q%)` + `confidence.desc` (`user_layer.py:133,141`) + `_row_to_hint` 0.8/0.4 (`:385`) → gold must be low-conf + non-substring; §Risks confirmed ✅
  - [x] **D-importlib-shadow** — prereqs + idiom (`test_benchmark_combined_formation_quality.py:44-65`) confirmed ✅
- [x] **Prong 3 — schema verify**: **N/A** (ZERO DB change) ✅
- [x] **D-baselines** — mypy `src` 400/0 · pytest collect 3163 · run_all 11/11 · wire 26 (Vitest 925 / mockup 51 N/A) ✅
- [x] **Catalog drift** — progress.md Day-0 table written (5 D-* + implication) ✅
- [x] **Go/no-go** — 0 drift, 0 scope shift → **PROCEED** ✅

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-158-memory-recall-precision-ab` (from `main` `65157788`) ✅

---

## Day 1 — Harness scaffold + oracle (US-1, US-3)

### 1.1 Benchmark script scaffold
- [x] **`scripts/benchmark_memory_recall_precision.py` (NEW)** — 57.154 scaffold: `MATERIALITY_DELTA=0.10` + `DEFAULT_K=5` + 3 arm consts + `FactSpec`/`RecallCase`/`ArmScore`/`RecallReport` + `load_cases` (yaml + required-key + dup-id + gold-in-facts) ✅
  - DoD: module loads clean; `load_cases` validates ✅

### 1.2 Oracle + verdict
- [x] **recall@k / precision@k / MRR + `build_report` two-sided verdict** ✅
  - DoD: pure over `gold_fact_ids`; verdict semantic-wins / profile-sufficient / tie by `MATERIALITY_DELTA` on recall@k ✅

### 1.x Partial gate
- [x] black/isort/flake8 clean (removed unused `re`, fixed E501); mypy gate = `mypy src/` (scripts/ intentionally out; sibling 57.154 same) ✅

---

## Day 2 — Corpus + arm producers + CI-safe test (US-1, US-2, US-3)

### 2.1 Discriminating golden corpus
- [x] **`tests/fixtures/memory/memory_recall_precision_cases.yaml` (NEW)** — 10 cases (8-12 facts each); **8/10 discriminating** (gold low-conf outside profile top-5 + question-query non-substring) + 2 easy controls ✅
  - DoD: offline test asserts ≥50% discriminate; measured **8/10 = 80%** ✅

### 2.2 Arm producers + run_arm
- [x] **`run_arm` drives the 3 producers** — profile (confidence-desc), keyword (substring), semantic (REAL `MemoryVectorIndex.search`); rows-as-param → DB-free ✅
  - DoD: each arm → fact-id list; offline via `DeterministicEmbeddingClient(dim=48)` + re-inlined `_FakeMemStore` ✅

### 2.3 CI-safe offline test
- [x] **`tests/unit/scripts/test_benchmark_memory_recall_precision.py` (NEW, 17 tests)** — importlib-shadow; oracle math + arm reproductions + discrimination + `load_cases` validation + `run_arm` drives REAL index offline (machinery, NOT semantic win) + `build_report` verdict ✅
  - DoD: **17 passed** offline (no Azure/Qdrant) ✅

### 2.x Full gate
- [x] mypy `src` **400/0** · run_all **11/11** · pytest **17 passed** · black/isort/flake8 clean · LLM-SDK-leak clean (ABC-only). Vitest/mockup/build N/A ✅

---

## Day 3 — Real-Azure verification (US-4) — measurement-spike equivalent of drive-through
_(This is a pure-measurement spike — NOT a chat-v2 UI feature. The substantive verification is a REAL embed+Qdrant run producing a real verdict; NOT gate-only. No chat-v2 drive-through.)_

### 3.1 Real-Azure env probe (Risk Class E-adjacent: env resolution, 57.157 lesson)
- [x] Ran from root (`PYTHONPATH=backend/src` → root `.env`); `is_embedding_configured()=True` · `deployment_embedding=text-embedding-3-large` · `qdrant_url=:6333`; Qdrant HTTP 200 "all shards ready" ✅

### 3.2 Real-Azure A/B run (MANDATORY — NOT gate-only)
- [x] Ran the harness against real `text-embedding-3-large` (3072-dim) + real Qdrant over the 10-case corpus ✅
- [x] **Verdict = `semantic-wins`** — semantic recall@k **100%** vs profile **20%** vs keyword **10%** (semantic − profile **+80pp**, MRR 1.0); honest decisive win, corpus NOT tuned-for-semantic ✅
- [x] Report `.md`+`.json` → `artifacts/`; verdict + observed-vs-intended + honesty caveats (deterministic → no re-run; non-adversarial corpus → follow-on AD) → progress.md Day 3 ✅

---

## Day 4 — CHANGE-125 + closeout

### 4.1 CHANGE-125 + design note 61
- [x] **`CHANGE-125-memory-recall-precision-ab.md`** (gap + harness + real-Azure verdict + AD closed) ✅
- [x] **`61-memory-recall-precision-ab-design.md`** (spike — 8-point gate; 3-arm rationale + corpus-discrimination + verdict + evidence-backs the deferred axis slices) ✅

### 4.2 Closeout
- [x] retrospective.md Q1-Q7 + calibration (`memory-vector-recall-precision-ab-spike` 0.60, 1st pt ~1.0-1.05 IN band; re-point 0.75 if 2nd >1.20) ✅
- [x] Final gate sweep: mypy `src` 400/0 · run_all 11/11 · pytest 17 · black/isort/flake8 clean · LLM-SDK-leak clean (Vitest/mockup/build N/A) ✅
- [x] Navigators: CLAUDE.md Current-Sprint + Last-Updated · MEMORY.md pointer + subfile · next-phase-candidates (CLOSED `AD-Memory-Vector-Recall-Precision-AB` + registered `AD-Memory-Vector-Recall-Adversarial-Corpus`) · sprint-workflow matrix (`memory-vector-recall-precision-ab-spike` 0.60 row) ✅
- [x] Anti-pattern self-check (retro Q5): AP-2/3/4/6/8/10/11 → 0 violations; v2 lints 11/11 ✅
- [ ] **Commit** → ⏳ PR push + open → CI → merge: PENDING USER CONFIRMATION (push is outward-facing) → post-merge status flip after gh-verified MERGED
