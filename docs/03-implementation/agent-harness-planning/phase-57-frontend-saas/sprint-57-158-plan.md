# Sprint 57.158 Plan — memory vector-recall precision A/B

**Summary**: An **evidence-first A/B benchmark spike** measuring whether the Sprint 57.155 semantic vector recall (`MemoryVectorIndex.search`, cosine, query-relevant) actually returns MORE relevant user facts than the Sprint 57.148 `profile()` recall (confidence-ranked, query-independent, `top_k=5`) at **many-fact scale** — the honest gap 57.155's own retro deferred (`AD-Memory-Vector-Recall-Precision-AB`). Closes that AD. Key scope decision: **ZERO `src/` change** — a permanent `scripts/benchmark_memory_recall_precision.py` + a NEW many-fact golden corpus + a CI-safe offline unit test, mirroring the 57.154 combined-formation-quality A/B pattern exactly. This is a **measurement spike, not a UI feature** → the substantive verification is a **real-Azure run** (real `text-embedding-3-large` + real Qdrant producing a real verdict), NOT a chat-v2 drive-through (exempt — no user-driven surface). A **design note (61) is required** (spike sprint). The verdict may go either way — if semantic does NOT beat profile at scale, that is an honest finding (don't over-invest in the axis); if it does, it validates 57.155.

**Status**: Approved-to-execute (user AskUserQuestion pick "Vector Recall 精度 A/B" 2026-07-06, under the engine-debt program — memory range, CARRY-026 semantic-axis continuation)
**Branch**: `feature/sprint-57-158-memory-recall-precision-ab`
**Base**: `main` HEAD `65157788` (#370 Sprint 57.157 scheduler merged; chore #371 status-flip docs-only pending, non-blocking)
**Slice**: closes `AD-Memory-Vector-Recall-Precision-AB` (CARRY-026 semantic-axis follow-on to 57.155 Slice 1; standalone measurement spike)
**Scope decisions**: (a) **3 recall arms** — `profile` (confidence, query-agnostic; `UserLayer.read(query="")`) vs `semantic` (cosine, query-relevant; `MemoryVectorIndex.search`) vs `keyword` (reference; `UserLayer.read(query=q)` ILIKE substring) — all 3 producers ALREADY exist → ZERO `src/` change; (b) oracle = **recall@k / precision@k / MRR** of a per-case gold-relevant fact subset; (c) **materiality verdict** `MATERIALITY_DELTA=0.15` on recall@k (two-sided — semantic-wins / tie / profile-sufficient); (d) permanent `scripts/benchmark_memory_recall_precision.py` + NEW `tests/fixtures/memory/memory_recall_precision_cases.yaml` (many-fact, 8-12 cases) + CI-safe `tests/unit/scripts/test_benchmark_memory_recall_precision.py` (offline `DeterministicEmbeddingClient` + `_FakeMemStore`); (e) real arm gated by `RUN_AZURE_INTEGRATION=1` + lazy Azure construction (NO `--real` flag — env-var idiom, per 57.154).

---

## 0. Background

### The gap (`AD-Memory-Vector-Recall-Precision-AB`)

- Sprint 57.155 wired the Cat 3 memory semantic axis (L4 user-layer vector recall) and its drive-through proved the **machinery** (per-user Qdrant ingest + isolation) is LIVE.
- But 57.155's own retro flagged an **honest caveat**: the Leg-2 recall was co-supported by the always-on `profile()` (57.148) + `knowledge_search`, so the semantic axis's **DISTINCTIVE value** (relevance-ranked recall at many-fact scale) was proven at the machinery/isolation layer, NOT behaviourally.
- No measurement exists that isolates "does cosine-ranked semantic recall beat confidence-ranked `profile()` at scale?".

### Why it matters (the missing capability)

Before building MORE on the semantic axis (system/tenant layers, incremental write, semantic dedup — all deferred 57.155 ADs), we must PROVE the axis actually helps — else it is a wired-but-valueless Potemkin (the reality-audit "引擎接好 ≠ 落地" trap). This A/B is the disciplined gate: measure before extending.

### Root cause (recon code read, file:line; ALL re-verified §checklist 0.1)

| Layer | Reality (on `main` HEAD `65157788`) | Anchor |
|-------|-------------------------------------|--------|
| `profile()` recall | query `""` → `want_semantic=False` → pure keyword `ILIKE '%%'` matches ALL rows → `confidence.desc()` → cap `top_k=5`. **Query-independent, confidence-ranked, never touches the vector index.** | `retrieval.py:161-197` + `user_layer.py:101-166` |
| semantic recall | `MemoryVectorIndex.search(*, tenant_id, user_id, rows, query, top_k=5)` → cosine `score` ranking; gated `want_semantic = "semantic" in time_scales and vector_index is not None and query.strip()!=""` | `vector_index.py:169-205` + `user_layer.py:122-124` |
| keyword recall | `UserLayer.read(query=q, time_scales=("long_term",))` → `content ILIKE %q%` substring, confidence-ordered | `user_layer.py:129-142` |
| naive relevance | `_row_to_hint` sets `relevance_score = 0.8 if query.lower() in content.lower() else 0.4` | `user_layer.py:385` |

→ The fix builds a harness that seeds a single user with N facts, then compares the ranked top-k of all 3 producers against a per-case gold subset — ZERO src change, all producers exist.

### The design (measurement spike: 1 script + 1 corpus + 1 offline test, ZERO src)

```
NEW scripts/benchmark_memory_recall_precision.py   — 3-arm A/B (profile/keyword/semantic), recall@k/precision@k/MRR oracle, materiality verdict
NEW tests/fixtures/memory/memory_recall_precision_cases.yaml — many-fact single-user corpus (8-12 cases; each = facts[] + query + gold_fact_ids[])
NEW tests/unit/scripts/test_benchmark_memory_recall_precision.py — CI-safe offline (DeterministicEmbeddingClient + _FakeMemStore + importlib-shadow idiom)
```

Mirrors `scripts/benchmark_combined_formation_quality.py` (57.154) scaffold: `load_cases` / dataclass arms / `run_arm` / `build_report` pure verdict / `report_to_markdown` / `_amain` / `main`. Real arm via lazy `AzureOpenAIEmbeddingClient(AzureOpenAIConfig())` + `QdrantVectorStore(settings.qdrant_url)`; CI arm via `DeterministicEmbeddingClient(dim=64)` + `_FakeMemStore` (both already used by 57.155 tests).

**Why 3 arms over 2**: the AD names semantic-vs-profile, but a naive-keyword reference column makes the finding honest — semantic's advantage over BOTH query-agnostic-confidence AND substring-keyword. All 3 are free (producers exist).

### Ground truth (recon head-start — code read on `main` HEAD `65157788`; ALL re-verified §checklist 0.1)

- `vector_index.py:169-205` — `MemoryVectorIndex.search` keyword-only args, returns `list[MemoryVectorHit]` (dedup_key/content/confidence/score).
- `retrieval.py:161-197` — `profile()` query="" confidence-ranked top_k=5.
- `scripts/benchmark_combined_formation_quality.py` — the mirror scaffold (materiality constants, dataclass arms, `load_cases`, `run_arm`, `build_report`, `_amain`, `main`).
- `tests/fixtures/memory/memory_formation_quality_cases.yaml` — the corpus template (top-level `cases:` list, per-case required-key + dup-id validation).
- `src/adapters/_testing/embedding.py:38` `DeterministicEmbeddingClient(dim=64)` (hash→L2-normalized, identical text→cosine 1.0) + `_FakeMemStore` at `tests/unit/agent_harness/memory/test_memory_vector_index.py:40-77` (honors two-key filter, cosine ranks).
- `tests/unit/scripts/test_benchmark_combined_formation_quality.py:44-65` — the importlib-shadow idiom (register in `sys.modules` BEFORE `exec_module`).
- `pyproject.toml:60-69` — `benchmark` marker (`RUN_AZURE_INTEGRATION=1`); NO `real_llm` marker; `pythonpath=["."]` + `backend/scripts/__init__.py` present.
- `src/core/config/__init__.py:236-242` `memory_vector_enabled` (env `MEMORY_VECTOR_ENABLED`); `qdrant_url:234`. Embedding field `deployment_embedding` (env `AZURE_OPENAI_DEPLOYMENT_EMBEDDING`) at `adapters/azure_openai/config.py:64-67` (NOT `embedding_deployment` — the 57.146 rename).

**Baselines (57.157 closeout)**: pytest ~3157 (3139 + 18) · wire 26 · Vitest 925 · mockup 51 · mypy `src` 400 · run_all 11/11. Re-verify Day-0.

### STALE / drift findings (Day-0; full detail → progress.md — placeholder, filled in §checklist 0.1)

- **D-fake-store-reuse** — grep whether `_FakeMemStore` is importable/shared or duplicated per test file → decide reuse vs re-inline in the new offline test (Explore report: duplicated in 2 files).
- **D-profile-nonempty-query** — verify `profile()` really passes `query=""` (not the turn query) so the profile arm is genuinely query-agnostic → confirm `retrieval.py:180`.
- **D-search-ingest-idempotency** — verify `MemoryVectorIndex.search` ingests-on-search (per-user count guard) so the harness needn't pre-ingest → confirm `vector_index.py:141-146`.
- **D-corpus-discriminates** — the corpus MUST have cases where the gold fact is NOT in the top-5-by-confidence AND NOT a keyword-substring of the query (else all 3 arms tie and the A/B proves nothing) → design cases with low-confidence-but-semantically-relevant gold facts.
- **D-pytest-baseline** — re-verify current pytest/mypy/run_all counts at branch creation.

## 1. Sprint Goal

Produce a permanent, reproducible 3-arm recall A/B that, run against real Azure `text-embedding-3-large` + real Qdrant over a discriminating many-fact corpus, yields a materiality-gated verdict on whether the 57.155 semantic axis beats `profile()` recall — closing `AD-Memory-Vector-Recall-Precision-AB` with EITHER outcome documented honestly. Proven by: gates (mypy/run_all/pytest incl. the new offline CI test) + the **real-Azure benchmark run** (the measurement-spike equivalent of a drive-through; NOT gate-only — a real embed+Qdrant verdict, screenshot/console + verdict into progress.md). Produces CHANGE-125 + design note 61.

## 2. User Stories

- **US-1** (harness): 作為平台工程師，我希望一個 3-arm recall benchmark（profile / keyword / semantic），以便在相同 many-fact 語料上量測三種召回策略的 recall@k。
- **US-2** (corpus): 作為評測設計者，我希望一份**能區分**語意與 confidence 召回的 golden 語料（gold fact 刻意低信心且非關鍵字子串），以便 A/B 不會因語料太簡單而全 tie。
- **US-3** (oracle + verdict): 作為決策者，我希望 recall@k / precision@k / MRR + materiality 判準，以便得到「語意勝 / 平手 / profile 足夠」的兩向可能結論。
- **US-4** (real-Azure verification): 作為驗證者，我希望在真 Azure embeddings + 真 Qdrant 上實跑並記錄 verdict（measurement-spike 等同 drive-through），以便結論非紙上。
- **US-5** (closeout): design note 61 + CHANGE-125 + calibration + navigators + AD closed。

## 3. Technical Specifications

### 3.0 Architecture (ZERO `src/` change — script + fixture + test only)

```
NEW scripts/benchmark_memory_recall_precision.py
    - MATERIALITY_DELTA = 0.15 ; arm names _ARM_PROFILE/_ARM_KEYWORD/_ARM_SEMANTIC
    - RecallCase / ArmScore / RecallReport dataclasses
    - load_cases(path)         mirror 57.154 (yaml.safe_load + required-key + dup-id validation)
    - recall_at_k / precision_at_k / mrr  pure oracle over gold_fact_ids
    - run_arm(arm, cases, *, profile_reader, vector_index)  drives the REAL producers
    - build_report(profile, keyword, semantic)  pure two-sided verdict
    - report_to_markdown / _amain(fixture,out_dir) / main()
NEW tests/fixtures/memory/memory_recall_precision_cases.yaml
    - cases: [ {id, facts:[{id,content,confidence}], query, gold_fact_ids:[...] } ]  (8-12 cases)
NEW tests/unit/scripts/test_benchmark_memory_recall_precision.py
    - importlib-shadow load ; DeterministicEmbeddingClient(dim=64) + _FakeMemStore
    - offline: assert oracle math + run_arm drives real MemoryVectorIndex.search + a fixed-corpus sanity verdict
UNTOUCHED  src/agent_harness/memory/** (vector_index / user_layer / retrieval)  — measured, not changed
UNTOUCHED  wire schema (26) / migration / frontend / loop.py
```

### 3.1 Harness (US-1/US-3) — `scripts/benchmark_memory_recall_precision.py`

- Mirror the 57.154 scaffold verbatim (constants → dataclasses → load_cases → oracle → run_arm → build_report → markdown → _amain → main).
- **Arm producers**: `profile` = `MemoryRetrieval.profile(tenant, user, top_k=k)` (or the equivalent `UserLayer.read(query="", ...)` over the seeded rows); `keyword` = `UserLayer.read(query=case.query, time_scales=("long_term",), max_hints=k)`; `semantic` = `MemoryVectorIndex.search(tenant, user, rows, query=case.query, top_k=k)`. Map each arm's returned facts → their `id` via `dedup_key`/content.
- Offline seeding: build `MemoryRow` list from the case facts; for profile/keyword arms use an in-memory reader mirroring `_FakeMemStore`/rows (no DB required — the harness scores RANKING, not persistence).

### 3.2 Corpus (US-2) — `tests/fixtures/memory/memory_recall_precision_cases.yaml`

- 8-12 cases, each a single user with **N=12-30 facts** of mixed topics + a query + `gold_fact_ids`.
- **Discrimination requirement (D-corpus-discriminates)**: at least half the cases place the gold fact OUTSIDE the top-5-by-confidence AND make it non-substring of the query (e.g. facts "we run our primary datastore on Aurora Postgres" conf 0.4; query "which database do we use?" — no "database" substring, low confidence → profile & keyword miss, semantic catches).

### 3.x What is explicitly NOT done

- NO change to `UserLayer` / `MemoryVectorIndex` / `profile()` (measurement only).
- NO chat-v2 drive-through (measurement spike — the real-Azure run is the verification).
- NO extension to system/tenant layers, incremental write, or semantic dedup (separate 57.155 carryover ADs).
- NO gating of the verdict in CI (the `benchmark`-marked real run is on-demand; the offline CI test asserts oracle math + a fixed deterministic verdict only).

### 3.y Validation (US-1..US-5)

Gates: mypy `src` 400 · run_all 11/11 · pytest (new offline test green + baseline unchanged) · black/isort/flake8 clean · LLM-SDK-leak clean (the script uses the `EmbeddingClient`/`QdrantVectorStore` ABCs, no direct SDK). Vitest/mockup/build N/A (no FE). Plus US-4 real-Azure run (the measurement-spike drive-through equivalent).

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 1 | `scripts/benchmark_memory_recall_precision.py` | NEW |
| 2 | `tests/fixtures/memory/memory_recall_precision_cases.yaml` | NEW |
| 3 | `tests/unit/scripts/test_benchmark_memory_recall_precision.py` | NEW |
| — | `src/agent_harness/memory/vector_index.py` · `layers/user_layer.py` · `retrieval.py` | **UNTOUCHED** |
| — | wire schema (26) · migrations · frontend · `loop.py` | **UNTOUCHED** |

## 5. Acceptance Criteria

1. `scripts/benchmark_memory_recall_precision.py` runs offline (DeterministicEmbeddingClient + _FakeMemStore) producing a 3-arm recall@k/precision@k/MRR report + a two-sided verdict.
2. The corpus has ≥ 50% discriminating cases (gold outside top-5-confidence AND non-substring) — asserted by an offline test.
3. New CI-safe unit test green (oracle math + run_arm drives the REAL `MemoryVectorIndex.search` offline); baseline pytest/mypy/run_all unchanged.
4. **Real-Azure verification (MANDATORY for this spike; the measurement equivalent of drive-through, NOT gate-only)** — run with `RUN_AZURE_INTEGRATION=1` against real `text-embedding-3-large` + real Qdrant; capture the verdict (semantic-wins / tie / profile-sufficient) + per-arm recall@k into progress.md with the console/report evidence.
5. `AD-Memory-Vector-Recall-Precision-AB` CLOSED; CHANGE-125 + design note 61; calibration recorded; navigators + next-phase-candidates updated.

## 6. Deliverables

- [ ] US-1 3-arm recall benchmark harness
- [ ] US-2 discriminating many-fact golden corpus
- [ ] US-3 recall@k/precision@k/MRR oracle + materiality two-sided verdict
- [ ] US-4 real-Azure run + verdict recorded (measurement-spike drive-through equivalent)
- [ ] US-5 design note 61 + CHANGE-125 + calibration + navigators + AD closed

## 7. Workload Calibration

- Scope class **NEW `memory-vector-recall-precision-ab-spike` 0.60** (evidence-first measurement A/B spike; anchored to `memory-formation-combine-ab-spike` 0.60 (57.154 — same real-Azure A/B harness + capturing/offline doubles + golden corpus + two-sided verdict shape) + `verification-context-hygiene-spike` 0.60 (57.136) + `verification-keycondition-spike` 0.60 (57.138). Set 0.60 not a tiny-code 0.85 because the real-code core — 3-arm harness + oracle + discriminating corpus + CI-safe offline test ≥~3.5 hr — holds the spike multiplier per the 57.137 lesson. If it lands > 1.20, re-point 0.75 (the real-Azure staging + corpus-discrimination tuning is the variance risk, per the 57.154 note).)
- **Agent-delegated: no** (parent-direct — the corpus DISCRIMINATION design + oracle/verdict logic is real evidence-design content where the result matters; the parent executes directly). `agent_factor` 1.0 → 3-segment form.
- Bottom-up est ~6 hr (harness scaffold ~2 · corpus design + discrimination ~1.5 · oracle + verdict ~1 · offline CI test ~1 · real-Azure run + verdict record ~0.5) → class-calibrated commit ~3.6 hr (mult 0.60). Day-4 retro Q2 verifies.

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| Corpus too easy → all arms tie → A/B proves nothing (D-corpus-discriminates) | Design ≥ 50% cases with gold OUTSIDE top-5-confidence AND non-substring; an offline test asserts the discrimination property |
| Real-Azure embedding cost / 429 batching (57.146 lesson) | Bounded corpus (8-12 cases × 12-30 facts); reuse the `_EMBED_BATCH=16` batching already in `MemoryVectorIndex._ingest`; gate the real run behind `RUN_AZURE_INTEGRATION=1` |
| importlib shadow (`tests.unit.scripts` shadows `backend/scripts`) | Use the register-before-exec idiom verbatim from `test_benchmark_combined_formation_quality.py:44-65` (Risk Class B-adjacent test-infra) |
| Stale `--reload` backend not relevant (no server) but real-Azure env resolution (57.157 lesson) | Probe `AzureOpenAIConfig().is_embedding_configured()` + `deployment_embedding` (env `AZURE_OPENAI_DEPLOYMENT_EMBEDDING`) BEFORE the real run; use the field name `deployment_embedding` (57.146 rename) |
| Verdict could be "profile sufficient" (semantic loses) | That is a VALID honest outcome — the AD closes either way; document it as an evidence finding (do NOT tune the corpus to force a semantic win) |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- `AD-Memory-Semantic-Axis-System-Tenant-Layers` (L1/L2 vector recall) — separate breadth slice.
- `AD-Memory-Vector-Incremental-Write` (embed-on-write + orphan cleanup) — separate correctness slice.
- `AD-Memory-Semantic-NearDup-Dedup` (semantic dedup) — separate slice; depends on this A/B's verdict.
- `AD-Memory-Session-Summary-Semantic-Rank` (57.151 recency→semantic) — separate slice.
- `AD-Memory-Vector-Inspector-Phase58` (chat-v2 Inspector surface) — frontend track, not engine.
- Making the semantic axis default-ON — a product decision gated on THIS A/B's verdict.
