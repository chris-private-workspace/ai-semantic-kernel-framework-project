---
title: 61-memory-recall-precision-ab design note
purpose: Spike-extract design note from Sprint 57.158; the memory recall-strategy A/B harness + the semantic-wins verdict
category: V2 extension docs (post-22-sprint era)
created: 2026-07-06 (Sprint 57.158 Day 4 closeout)
sprint_source: 57.158
verified_ratio: ≥ 95% (per 8-Point Quality Gate)
status: Active
---

# 61-memory-recall-precision-ab Design Note (Sprint 57.158 extract)

## 0. Spike Summary

- **Scope (user stories)**: US-1 3-arm recall benchmark · US-2 discriminating many-fact corpus · US-3 recall@k/precision@k/MRR oracle + two-sided verdict · US-4 real-Azure run · US-5 closeout.
- **Gap closed**: `AD-Memory-Vector-Recall-Precision-AB` — 57.155 proved the semantic-axis machinery LIVE but not that cosine recall BEATS `profile()` at scale.
- **Verified period**: 2026-07-06.
- **Calibration**: NEW class `memory-vector-recall-precision-ab-spike` 0.60; parent-direct (`agent_factor` 1.0); bottom-up ~6 hr → committed ~3.6 hr; actual ~1.0-1.05 IN band (Day-0 0-drift + a smooth single real-Azure run + no re-drive; the DeterministicEmbeddingClient + `_FakeMemStore` + the importlib idiom were all pre-existing patterns).
- **Verification**: pytest +17 offline; a real-Azure `text-embedding-3-large` + real-Qdrant run.
- **Verdict**: **semantic-wins** — semantic recall@k **100%** vs profile **20%** vs keyword **10%** (semantic − profile **+80pp**, MRR 1.0).

## 1. Decision Matrix — how to isolate the semantic advantage

| Approach | Isolates ranking strategy? | DB required? | Offline-runnable? | Decision |
|----------|----------------------------|--------------|-------------------|----------|
| **3 ranking arms over the case's `MemoryRow` list** (chosen) | ✅ yes — only the rank function differs | ❌ no (`search(rows=…)` takes rows as a param) | ✅ yes (fake store + deterministic embedder) | ✅ **chosen** |
| Drive the full `UserLayer.read` per arm (real DB) | ✅ yes | ✅ yes — seed `memory_user` | ❌ no (needs Postgres + RLS) | ❌ rejected — un-runnable offline, heavier |
| Compare live chat-v2 turns | ❌ no — `profile()` + semantic + knowledge_search all merge | ✅ yes | ❌ no | ❌ rejected — the exact confound 57.155 hit |

**Chosen reason**: `MemoryVectorIndex.search(*, rows, query, top_k)` takes `rows` as a PARAMETER (`vector_index.py:169`) — the layer fetches them from DB then passes them in — so the semantic arm needs only an EmbeddingClient + a vector store, no DB. profile/keyword are then 2-line ranking rules over the same rows. **Rejected-full-read reason**: seeding a real DB per case makes the harness un-runnable in CI and adds RLS/session complexity for no measurement gain (the ranking is the variable, not persistence). **Rejected-live-turn reason**: it re-creates the very `profile()`+`knowledge_search` confound 57.155's drive-through hit.

## 2. Verified Invariants

### 2.1 The three arms rank the same fact set; only `semantic` is a real code path (US-1)
- **Implementation**: `rank_profile` / `rank_keyword` / `rank_semantic` at `backend/scripts/benchmark_memory_recall_precision.py`. `rank_profile` = `sorted(facts, key=confidence, reverse=True)[:k]` (faithful to `UserLayer.read(query="")` `ORDER BY confidence.desc().limit(k)`, `user_layer.py:141`); `rank_keyword` = substring filter + confidence-desc (faithful to `content.ilike(f"%{query}%")`, `user_layer.py:133,141`); `rank_semantic` = `await index.search(rows=..., query=..., top_k=k)` (the REAL 57.155 producer).
- **Behavior**: profile is query-agnostic (confidence only); keyword needs a substring; semantic is cosine-ranked (query-relevant). `dedup_key` carries the fact id so hits map straight to gold ids.
- **Verification**: `cd backend && pytest tests/unit/scripts/test_benchmark_memory_recall_precision.py -k "rank_" -q`.
- **Test fixture**: hand-built `FactSpec` lists (test asserts `rank_profile == ["hi","mid","lo"]`, `rank_keyword("postgresql") == ["c","a"]`, a question-query → `[]`).

### 2.2 The corpus discriminates (US-2)
- **Implementation**: `backend/tests/fixtures/memory/memory_recall_precision_cases.yaml` — 10 cases; a case discriminates when its gold fact is OUTSIDE the top-5-by-confidence AND the query is a non-substring of the gold content.
- **Behavior**: 8/10 cases discriminate (gold low-confidence + question-query); profile & keyword structurally miss those, only semantic can catch them. 2 easy controls (high-confidence gold; one keyword-substring) anchor the low end.
- **Verification**: `pytest tests/unit/scripts/test_benchmark_memory_recall_precision.py::test_corpus_is_discriminating -q` (asserts ≥50% via `rank_profile`); measured **8/10 = 80%**.

### 2.3 The oracle is recall@k/precision@k/MRR (US-3)
- **Implementation**: `recall_at_k` / `precision_at_k` / `mrr` (pure) + `build_report` two-sided verdict (`MATERIALITY_DELTA=0.10`).
- **Behavior**: recall@k = gold-in-top-k / |gold| (primary); precision@k = gold-in-top-k / k; MRR = 1/rank of first gold. Verdict: semantic − profile recall@k `≥ +Δ` → semantic-wins, `≤ −Δ` → profile-sufficient, else tie.
- **Verification**: `pytest tests/unit/scripts/test_benchmark_memory_recall_precision.py -k "recall_at_k or precision_at_k or mrr or build_report" -q`.
- **Test fixture**: hand-checked lists + synthetic `ArmScore`s asserting each verdict branch.

### 2.4 Real-Azure verdict = semantic-wins (US-4)
- **Behavior**: real `text-embedding-3-large` (3072-dim) + real Qdrant, 10 cases → semantic recall@k **100%** (MRR 1.0 = gold always first) vs profile **20%** vs keyword **10%**; semantic − profile **+80pp** ≫ materiality.
- **Verification (reproduce)**: `PYTHONPATH=backend/src python backend/scripts/benchmark_memory_recall_precision.py` (from project root so `env_file=".env"` reads the root `.env`; needs `AZURE_OPENAI_DEPLOYMENT_EMBEDDING` + a reachable Qdrant). Deterministic (embedding cosine is stable per text) → no re-run needed.
- **Evidence**: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-158/artifacts/memory_recall_precision_report.{md,json}`.

## 3. Cross-Category Contracts

**None.** ZERO `src/` change / no new ABC / no wire event (stays 26) / no migration. The harness reuses:
- `MemoryVectorIndex.search` (Cat 3, Sprint 57.155).
- `EmbeddingClient` ABC + `QdrantVectorStore` (Sprint 57.146).
- `DeterministicEmbeddingClient` (`adapters/_testing/embedding.py`, Sprint 57.146) for the offline arm.

No 17.md edit required.

## 4. Open Invariants (deferred; new carryover AD)

- [ ] `AD-Memory-Vector-Recall-Adversarial-Corpus` — the corpus is discriminating but NON-adversarial (one clear single-topic gold per case, no semantic distractors, no ambiguous multi-topic queries). A harder corpus (near-duplicate distractors + ambiguous queries) would stress precision@k and separate "recall the buried fact" from "rank it above look-alikes". The recall@k win is robust; precision@k under adversarial load is the open question.
- [ ] The deferred 57.155 semantic-axis slices (`AD-Memory-Semantic-Axis-System-Tenant-Layers`, `AD-Memory-Vector-Incremental-Write`, `AD-Memory-Semantic-NearDup-Dedup`, `AD-Memory-Session-Summary-Semantic-Rank`) are now EVIDENCE-BACKED to build on (this A/B was their gate).
- [ ] Making the semantic axis default-ON (`MEMORY_VECTOR_ENABLED`) — a product decision this A/B now supports but does not itself flip.

## 5. Rollback / Fallback

- **Nothing to roll back**: ZERO `src/` change — the harness is inert eval tooling. Deleting the 3 new files removes it with no runtime effect.
- **If the verdict is later disputed**: re-run the harness (deterministic) or extend the corpus per `AD-Memory-Vector-Recall-Adversarial-Corpus`; the offline test guards the oracle + arm + discrimination invariants against regression.
- **Sentinel**: the semantic axis itself remains `MEMORY_VECTOR_ENABLED` default OFF (57.155) — this A/B informs, but does not change, that default.

## 6. References

- Sprint plan: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-158-plan.md`
- Progress + retrospective: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-158/`
- Change record: `claudedocs/4-changes/feature-changes/CHANGE-125-memory-recall-precision-ab.md`
- Measured axis: Sprint 57.155 (`memory/project_phase57_155_memory_vector_recall.md`) + design note `58-memory-vector-recall-design.md`
- Mirrored scaffold: `backend/scripts/benchmark_combined_formation_quality.py` (Sprint 57.154) + design note 57
- Calibration: `.claude/rules/sprint-workflow.md` §Scope-class multiplier matrix (`memory-vector-recall-precision-ab-spike` 0.60)

## Modification History
- 2026-07-06: Initial extract from Sprint 57.158 closeout (Day 4)
