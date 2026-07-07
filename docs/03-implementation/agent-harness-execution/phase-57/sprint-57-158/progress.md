# Sprint 57.158 Progress — memory vector-recall precision A/B

**Plan**: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-158-plan.md`
**Base**: `main` HEAD `65157788` (57.157 merged; chore #371 status-flip docs-only pending)

---

## Day 0 — Plan-vs-Repo Verify (三-prong) — 2026-07-06

### Prong 1 — path verify ✅
- NEW free (Glob 0): `scripts/benchmark_memory_recall_precision.py`, `tests/fixtures/memory/memory_recall_precision_cases.yaml`, `tests/unit/scripts/test_benchmark_memory_recall_precision.py`.
- `CHANGE-125` free (highest 124), design note `61` free (highest 60).
- `backend/scripts/__init__.py` present + `pyproject.toml` `pythonpath=["."]` (`:57`) — importlib-shadow prereqs OK.

### Prong 2 — content verify (drift findings)

| D | Finding | Implication |
|---|---------|-------------|
| **D-fake-store-reuse** ✅ | `_FakeMemStore` is inlined in TWO test files (`tests/integration/memory/test_memory_vector_recall.py:52` + `tests/unit/agent_harness/memory/test_memory_vector_index.py:40`), NOT a shared importable helper. | Re-inline a minimal `_FakeMemStore` in the new offline test (matches the existing convention; avoids creating an AP-3 shared helper). |
| **D-profile-nonempty-query** ✅ | `profile()` passes `query=""` + `time_scales=("long_term",)` + `max_hints=top_k` (default 5); docstring: "wildcard empty query relies on UserLayer.read's ILIKE '%%'" (`retrieval.py:161-197`). | The `profile` arm is genuinely query-agnostic, confidence-ranked, never touches the vector index — a clean A/B baseline. |
| **D-search-ingest-idempotency** ✅ | `MemoryVectorIndex._ingest` per-user count guard: `if count(payload_filter=user_filter) == expected: return` (idempotent no-op, `vector_index.py:135`). | `search` ingests-on-search → the harness needn't pre-ingest; the offline `_FakeMemStore` must honor the two-key count filter (it does, per recon). |
| **D-corpus-discriminates** ✅ | keyword arm = `content.ilike(f"%{query}%")` + `confidence.desc().nulls_last()` (`user_layer.py:133,141`); `_row_to_hint` relevance = `0.8 if query.lower() in content.lower() else 0.4` (`user_layer.py:385`). | To make the A/B discriminate, gold facts MUST be low-confidence (miss profile top-5) AND non-substring of the query (miss keyword). This is a real corpus-design constraint → §Risks row confirmed. |
| **D-importlib-shadow** ✅ | prereqs confirmed (scripts/__init__.py + pythonpath); the register-before-exec idiom lives in `test_benchmark_combined_formation_quality.py:44-65`. | Copy the idiom verbatim in the new offline test. |

### Prong 3 — schema verify
- **N/A** — ZERO DB change. The harness measures existing `memory_user` rows + the existing Qdrant `tenant_*_user_memory` collections; no new table/migration/column.

### D-baselines (re-verified at branch `65157788`)
- mypy `src` **400/0** · pytest collect **3163** · run_all **11/11** · wire **26** · Vitest 925 / mockup 51 (N/A — no FE).

### Go/no-go
- **PROCEED.** Measurement spike, ZERO `src/` change, surface confined to 3 new files; all 5 D-items confirmed the plan's assumptions against real code (0 drift, 0 scope shift). The only design-critical item (D-corpus-discriminates) is a corpus-authoring constraint already captured in plan §3.2 + §Risks.

---

## Day 1 — Harness scaffold + oracle (US-1/US-3) — 2026-07-06

**Done**:
- `scripts/benchmark_memory_recall_precision.py` (NEW) — mirrors the 57.154 scaffold: `MATERIALITY_DELTA=0.10` + `DEFAULT_K=5` + 3 arm consts + `FactSpec`/`RecallCase`/`ArmScore`/`RecallReport` dataclasses + `load_cases` (yaml + required-key + dup-id + gold-in-facts validation) + `recall_at_k`/`precision_at_k`/`mrr` oracle + `rank_profile`/`rank_keyword` (faithful confidence/substring reproductions of `UserLayer` SQL, anchored) + `rank_semantic` (REAL `MemoryVectorIndex.search`, rows-as-param → no DB) + `run_arm` + `build_report` (two-sided verdict) + `report_to_markdown` + `_amain`/`main` (lazy Azure embedder + real Qdrant).
- **Key design**: `MemoryVectorIndex.search(*, rows, query, top_k)` takes `rows` as a PARAMETER → all 3 arms rank the case's `MemoryRow` list, so the harness is DB-free (offline + real both need only embedder+store). profile/keyword replicate a 2-line SQL ORDER BY (AP-10-acceptable vs a DB dependency).

**Partial gate**: black/isort/flake8 clean (removed unused `re`; fixed 3 E501). mypy gate is `mypy src/` (CI `backend-ci.yml:152`) — scripts/ is intentionally OUT of it (the sibling 57.154 script shows the same standalone import-untyped; a non-issue).

## Day 2 — Corpus + arms + CI-safe test (US-1/US-2/US-3) — 2026-07-06

**Done**:
- `tests/fixtures/memory/memory_recall_precision_cases.yaml` (NEW) — 10 cases, single-user 8-12 facts each. **8/10 discriminating** (gold fact deliberately low-confidence → outside profile top-5, AND query is a question → non-substring so keyword misses) + 2 easy controls (high-conf gold; case 9 also keyword-substring). Verified discrimination count = **8/10 = 80%** (≥50%).
- `tests/unit/scripts/test_benchmark_memory_recall_precision.py` (NEW, 17 tests) — importlib-shadow idiom; re-inlined `_FakeMemStore` (per D-fake-store-reuse); asserts oracle math (recall/precision/MRR + cutoff) + arm reproductions + corpus discrimination (≥50% via `rank_profile`) + `load_cases` validation (missing-key / gold-not-in-facts / dup-id) + `run_arm` drives the REAL `MemoryVectorIndex.search` offline (DeterministicEmbeddingClient — machinery only, NOT the semantic win) + `build_report` two-sided verdict (semantic-wins / profile-sufficient / tie).

**Full gate**: pytest **17 passed** · mypy `src` **400/0** (no src change) · run_all **11/11** · black/isort/flake8 clean · LLM-SDK-leak clean (ABC-only). Vitest/mockup/build N/A (no FE).

**Note (offline limitation, by design)**: the hash-based DeterministicEmbeddingClient has no semantic structure → the offline semantic arm is near-random; it CANNOT show the semantic advantage. That is the Day-3 real-Azure run's job (real `text-embedding-3-large` gives synonym-aware cosine).

**Next (Day 3)**: real-Azure A/B run (`RUN_AZURE_INTEGRATION=1`) — the substantive verification; record the verdict honestly either way.

## Day 3 — Real-Azure A/B run (US-4) — measurement-spike verification — 2026-07-06

**Setup**: run from project root (`PYTHONPATH=backend/src` so `env_file=".env"` reads the root `.env`; verified `is_embedding_configured()=True`, `deployment_embedding=text-embedding-3-large`, `qdrant_url=http://localhost:6333`). Qdrant reachable (HTTP 200, "all shards are ready"; the container's "unhealthy" flag is a stale healthcheck). Real `text-embedding-3-large` (3072-dim) + real Qdrant (fresh tenant+user per case → per-case collection). NO chat-v2 UI — this is a measurement spike; the real-Azure run IS the substantive verification (per plan §3.x, exempt from chat-v2 drive-through).

### Verdict: **semantic-wins** (decisive)

| arm | recall@k | precision@k | MRR |
|-----|----------|-------------|-----|
| profile (confidence, query-agnostic) | 20.00% | 4.00% | 0.150 |
| keyword (substring) | 10.00% | 2.00% | 0.100 |
| **semantic (cosine, query-relevant)** | **100.00%** | 22.00% | **1.000** |

- semantic − profile recall@k: **+80.00pp** (≫ 10% materiality) · semantic − keyword: **+90.00pp**
- Artifacts: `artifacts/memory_recall_precision_report.{md,json}`.

**What it means**: with real embeddings, semantic recall surfaced the gold fact in ALL 10 cases (MRR 1.0 = gold always ranked first), while confidence-ranked `profile()` caught it only 20% (the 2 high-confidence control cases) and keyword 10% (the 1 substring case). This **validates the 57.155 semantic axis** — at many-fact scale with discriminating queries, cosine recall massively out-recalls confidence-ranking, exactly the distinctive value 57.155's drive-through could not isolate (it was co-supported by `profile()` + `knowledge_search`). `AD-Memory-Vector-Recall-Precision-AB` is answered.

### Observed vs intended + honesty caveats
- Intended: measure semantic-vs-profile recall at scale, honest either way. **Observed**: a decisive semantic win — NOT a forced result (the corpus was built to discriminate, but 8/10 cases having gold OUTSIDE profile top-5 is a realistic "buried relevant fact" scenario, not a tuned-for-semantic one).
- **No re-run needed** (unlike 57.154's stochastic LLM-judge): embedding cosine is deterministic (text-embedding-3-large returns a stable vector per text), so the +80pp gap is far beyond any run-to-run variance.
- **Honest limitation**: the corpus has ONE clearly-relevant, single-topic gold fact per case (semantically close but lexically different + low-confidence). It is NOT adversarial — no near-duplicate semantic distractors, no ambiguous multi-topic queries. So the 100%/22% reflects the CLEAN discriminating case; a harder corpus (distractors + ambiguous queries) would stress precision@k harder → registered as a follow-on AD (`AD-Memory-Vector-Recall-Adversarial-Corpus`). The recall@k win, however, is robust and the point of the AD.

## Day 4 — <pending>
