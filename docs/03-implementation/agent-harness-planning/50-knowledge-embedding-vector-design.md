# Knowledge Connector Slice 2 — Embedding + Qdrant Vector Search (Design Note)

**Purpose**: Extract the verified design of the Slice-2 semantic-retrieval path from the Sprint 57.146 implementation — the platform's first real embedding + vector-store path.
**Category / Scope**: Cat 2 (Tools) + Adapters (EmbeddingClient ABC) + Infrastructure (Qdrant) / Phase 57 / Sprint 57.146
**Created**: 2026-06-27
**Status**: Active (verified ratio ~95%)
**Author**: self (solo-dev)

> **Modification History**
> - 2026-06-27: Initial extract from Sprint 57.146 (AD-Knowledge-Connector-First-Real-Source Slice 2)

---

## 1. Spike Summary (US → what shipped)

Second slice of the knowledge-connector arc. Upgrades the 57.145 keyword connector with section-aware snippets + real Azure-embedding semantic retrieval over Qdrant.

- **US-1** section-aware chunking + richer keyword snippet (fixes 57.145 R2 over-search).
- **US-2** provider-neutral `EmbeddingClient` ABC + Azure `text-embedding-3-large` adapter + deterministic test double.
- **US-3** `QdrantVectorStore` wrapper (ensure/upsert/search) over the existing dev Qdrant container.
- **US-4** `KnowledgeVectorIndex` (batched ingest + cosine search) + opt-in wiring + fail-soft keyword fallback + idempotent startup ingest.
- **US-5** drive-through PASS (real chat-v2 + Azure embedding + Qdrant). **US-6** closeout.

## 2. Decision Matrix

### Embedding provider (約束 3 mandates an abstraction; `business_domain/` cannot import a provider SDK)

| Option | Provider neutrality | Drive-through real? | Dep cost | Decision |
|--------|---------------------|---------------------|----------|----------|
| **Azure `text-embedding-3-large` via EmbeddingClient ABC** | ✅ ABC; SDK in `adapters/azure_openai/` | ✅ real Azure | reuses existing `openai` SDK (no new LLM dep) | **CHOSEN** (user pick; Azure-centric platform) |
| Local model (fastembed / sentence-transformers) | ✅ (non-LLM) | ✅ offline | +heavy dep (excluded since 49.1) | rejected (heavier; Azure preferred) |
| Import openai in the connector | ❌ fails `check_llm_sdk_leak` | — | — | rejected (約束 3 violation) |

### Vector store

| Option | Status in repo | Decision |
|--------|----------------|----------|
| **Qdrant** | container running (`docker-compose.dev.yml:74-86`); namespace strategy exists (`infrastructure/vector/qdrant_namespace.py`); client = CARRY-026 stub | **CHOSEN** (infra present; build the wrapper) |
| pgvector | not provisioned | rejected (no infra) |
| in-memory | non-persistent | rejected (real path wanted) |

### Chunk unit

`##`-heading section (shared by keyword snippet + embedding unit) — one abstraction, two consumers. Fixes R2 (richer snippet) AND defines a coherent embedding chunk.

## 3. Verified Invariants (file:line + verification)

1. **Section-aware chunking** — `split_sections` splits at level-2 `##`; preamble = H1 or `(intro)`; `###` stays inside parent; body trimmed to `_MAX_SECTION_CHARS=1500`. `business_domain/knowledge/chunking.py:60-110`. Verify: `pytest tests/unit/business_domain/knowledge/test_chunking.py -q` (8).
2. **Keyword snippet returns the section body** (R2 fix) — `connector.py:_section_snippet` reuses `split_sections`. `business_domain/knowledge/connector.py:125-145`. Verify: `test_knowledge_connector.py::test_snippet_returns_whole_section_not_one_line`.
3. **EmbeddingClient ABC** — `async embed(texts)->list[list[float]]` + `model_name()`; no SDK import. `adapters/_base/embedding_client.py:42-60`. Exported `adapters/_base/__init__.py:15`.
4. **Azure adapter SDK-confined** — `embeddings.create(model=deployment_embedding, input=texts)`, re-sorted by `.index`. `adapters/azure_openai/embeddings.py:55-75`. `check_llm_sdk_leak` green (run_all 11/11). Verify: `pytest tests/unit/adapters/azure_openai/test_embeddings.py -q` (5, SDK mocked).
5. **Qdrant wrapper** — `query_points` API (qdrant-client 1.17 removed `search`); cosine; idempotent ensure; sync calls via `asyncio.to_thread`. `infrastructure/vector/qdrant_client.py:60-150`. Verify: `pytest tests/unit/infrastructure/vector/test_qdrant_client.py -q` (5, client mocked).
6. **Batched idempotent ingest** — `_EMBED_BATCH=16` (one all-sections call → HTTP 429); skip when `count==expected`. `business_domain/knowledge/vector_index.py:51-94`. Verify: `test_vector_index.py::test_ingest_batches_embedding_calls` (asserts `batch_sizes == [16, 4]`).
7. **Opt-in + fail-soft** — `register_knowledge_tools(..., vector_index=None)`: vector-primary, keyword fallback on error. `business_domain/knowledge/tools.py:83-130`. Verify: `test_knowledge_tools.py::test_handler_fails_soft_to_keyword_on_vector_error`.
8. **Zero-cost-when-off composition** — `get_knowledge_vector_index()` returns None (no adapter/Qdrant import) unless `knowledge_vector_enabled` + `is_embedding_configured()` + qdrant_url. `api/v1/chat/knowledge_index.py:54-95`. Startup ingest fail-soft (`api/main.py::_ingest_knowledge`).
9. **Drive-through** (real, NOT gate-only) — `KNOWLEDGE_VECTOR_ENABLED=1`, `KNOWLEDGE_DOCS_ROOT=docs/rules-on-demand`; Qdrant `knowledge_local_docs` green / 129 points / dim 3072; a no-literal-keyword semantic query retrieved `adapters-layer.md` + `llm-provider-neutrality.md` by similarity, answer cited each source path. Reproduce: progress.md Day 3.

## 4. Cross-Category Contracts

- **`EmbeddingClient` ABC** (`adapters/_base/`) — a NEW provider-neutral interface, sibling to `ChatClient`. Treated as adapter-internal (like `ChatClient`'s concrete adapters); not a new 17.md cross-category contract row (it is consumed by Cat 2 / future Cat 3 via the ABC, no new event/state shape). If Cat 3 wires the memory semantic axis on it later, register it in 17.md §2.x then.
- **No new 17.md contract / wire event / DB migration** — reuses the Cat 2 `ToolSpec` (`knowledge_search`, unchanged from 57.145), the existing tool-call rendering, and Qdrant (no Postgres schema). `QdrantNamespaceStrategy` (`"kb"` layer) is reused only for the collection-name concept; per-tenant namespacing is Slice 3.

## 5. Open Invariants (deferred — NOT verified this sprint)

| Item | Status | Where |
|------|--------|-------|
| Per-tenant KB collection isolation (`QdrantNamespaceStrategy` `"kb"`) + RBAC per-doc filter | deferred | Slice 3 (`AD-Knowledge-Connector-RBAC-Citation-Slice3`) |
| Cat 3 memory semantic axis wired on the new ABC/wrapper (CARRY-026) | unblocked, NOT wired | separate Cat 3 sprint |
| Full-corpus ingest at scale (3818 sections) | NOT verified — drive-through used a bounded 129-section corpus | needs a background/offline ingest job (not blocking startup) |
| Hybrid keyword∪vector score fusion / re-ranking | deferred | `AD-Knowledge-Connector-Hybrid-Rerank` |
| Incremental re-ingest on file change | deferred | `AD-Knowledge-Connector-Ingest-Mgmt` |
| PDF/Office parsing | deferred | `.md`/`.txt` only |

**Boundary statement**: verified = semantic retrieval + section snippets + fail-soft + opt-in + batched ingest on a bounded real corpus, end-to-end on the real main flow. NOT verified = multi-tenant isolation, large-corpus startup ingest, hybrid fusion.

## 6. Rollback

- Disable via env: `KNOWLEDGE_VECTOR_ENABLED=0` → `get_knowledge_vector_index()` returns None → keyword path (57.145), byte-identical, zero cost. No data to clean (Qdrant collection is derived from the `.md` source-of-truth; drop `knowledge_local_docs` to reset).
- Full revert: remove the 7 new files + the opt-in kwarg + the 2 settings + the requirements line. < 1 hr; no migration, no sentinel, no DB state. 57.145 keyword connector is untouched underneath.

## 7. References

- `business_domain/knowledge/{chunking,connector,vector_index,tools}.py` · `adapters/_base/embedding_client.py` · `adapters/azure_openai/embeddings.py` · `infrastructure/vector/qdrant_client.py` · `api/v1/chat/knowledge_index.py`
- `49-knowledge-connector-first-real-source-design.md` (Slice 1)
- `10-server-side-philosophy.md` §原則 2 (LLM Provider Neutrality) · `.claude/rules/llm-provider-neutrality.md`
- `infrastructure/vector/qdrant_namespace.py` (Slice-3 per-tenant reuse) · CARRY-026
- Sprint 57.146 plan / checklist / progress / retrospective

## 8. Modification History

- 2026-06-27: Initial creation (Sprint 57.146) — Slice-2 embedding/vector design extract.
