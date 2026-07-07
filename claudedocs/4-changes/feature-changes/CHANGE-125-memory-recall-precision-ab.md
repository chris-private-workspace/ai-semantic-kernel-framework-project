# CHANGE-125: memory vector-recall precision A/B

**Date**: 2026-07-06
**Sprint**: 57.158
**Scope**: 範疇 3 (Memory) — eval tooling
**Closes**: `AD-Memory-Vector-Recall-Precision-AB`

## Problem

Sprint 57.155 wired the Cat 3 memory semantic axis (L4 user-layer vector recall) and its drive-through proved the machinery (per-user Qdrant ingest + isolation) is LIVE. But 57.155's own retro flagged an honest caveat: the recall was co-supported by the always-on `profile()` (57.148) + `knowledge_search`, so the semantic axis's DISTINCTIVE value — relevance-ranked recall at many-fact scale — was proven at the machinery layer, NOT behaviourally. No measurement existed isolating "does cosine-ranked semantic recall actually beat confidence-ranked `profile()` at scale?". Building MORE on the axis (system/tenant layers, incremental write, semantic dedup) before proving it helps risks a wired-but-valueless Potemkin.

## Root Cause

`profile()` recall is query-independent (query=`""` → `ILIKE '%%'` → `confidence.desc()` top-5, `retrieval.py:161-197` + `user_layer.py:141`) — it surfaces the highest-confidence facts regardless of the query. At many-fact scale a genuinely-relevant fact that happens to be low-confidence is buried below the top-5 and never surfaces, even when the user's query is about exactly that fact. The semantic axis (`MemoryVectorIndex.search`, cosine, query-relevant, `vector_index.py:169-205`) should catch it — but nothing measured whether it does.

## Solution

An **evidence-first A/B benchmark spike, ZERO `src/` change** (measures existing producers; mirrors the 57.154 combined-formation-quality A/B).

- **NEW `scripts/benchmark_memory_recall_precision.py`** — 3 recall arms rank the same per-case fact set for a query, top-k: `profile` (confidence-desc, query-agnostic — a faithful reproduction of the `UserLayer.read(query="")` SQL ORDER BY), `keyword` (substring — reproduces `content.ilike(%q%)`), `semantic` (the REAL 57.155 `MemoryVectorIndex.search`; `rows` are a parameter → no DB). Oracle: `recall@k` (primary) / `precision@k` / `mrr` over each case's `gold_fact_ids`. Two-sided verdict on recall@k (semantic − profile): `≥ +0.10` semantic-wins / `≤ −0.10` profile-sufficient / else tie.
- **NEW `tests/fixtures/memory/memory_recall_precision_cases.yaml`** — 10 single-user cases (8-12 facts each); **8/10 discriminating** (gold fact deliberately low-confidence → outside profile top-5, AND query is a question → non-substring, so both baselines miss) + 2 easy controls.
- **NEW `tests/unit/scripts/test_benchmark_memory_recall_precision.py`** (17 tests) — CI-safe offline (importlib-shadow idiom + re-inlined `_FakeMemStore` + `DeterministicEmbeddingClient`): oracle math + arm reproductions + corpus discrimination (≥50%) + `load_cases` validation + `run_arm` drives the REAL `MemoryVectorIndex.search` offline (machinery, NOT the semantic win) + `build_report` two-sided verdict.

ZERO change to `UserLayer` / `MemoryVectorIndex` / `profile()` / wire / migration / frontend.

## Verification

- **Gate**: pytest +17 (new offline test) · mypy `src` 400/0 (no src change) · run_all 11/11 · black/isort/flake8 clean · LLM-SDK-leak clean (ABC-only). Vitest/mockup/build N/A.
- **Real-Azure A/B (the measurement-spike verification; NOT gate-only)** — real `text-embedding-3-large` (3072-dim) + real Qdrant over the 10-case corpus:

  | arm | recall@k | precision@k | MRR |
  |-----|----------|-------------|-----|
  | profile (confidence) | 20% | 4% | 0.150 |
  | keyword (substring) | 10% | 2% | 0.100 |
  | **semantic (cosine)** | **100%** | 22% | **1.000** |

  **Verdict `semantic-wins`**: semantic − profile recall@k **+80pp** (≫ 10% materiality). Semantic surfaced the gold fact in ALL 10 cases (MRR 1.0 = always ranked first); profile caught it only 20% (the 2 high-confidence controls). Deterministic (embedding cosine) → no re-run needed. Report: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-158/artifacts/memory_recall_precision_report.{md,json}`.

## Impact

Eval tooling only (범주 3), ZERO runtime change. Closes `AD-Memory-Vector-Recall-Precision-AB` with a decisive, honest verdict: the 57.155 semantic axis materially out-recalls confidence-ranked `profile()` at many-fact scale — the axis's distinctive value is now proven behaviourally, so the deferred semantic-axis slices (system/tenant layers, incremental write, semantic dedup) are worth building on it. Honest limitation: the corpus is discriminating but non-adversarial (single clear gold per case, no semantic distractors) → a harder-corpus follow-on (`AD-Memory-Vector-Recall-Adversarial-Corpus`) would stress precision@k; the recall@k win is robust.
