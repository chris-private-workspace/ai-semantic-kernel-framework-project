# CHANGE-122: Cat 3 memory semantic axis — user-layer vector recall (CARRY-026 Slice 1)

**Date**: 2026-07-01
**Sprint**: 57.155
**Scope**: 範疇 3 (Memory) — semantic axis (backend-only)

## Problem

Cat 3 Memory had **zero semantic/vector retrieval**. All 5 layers read by Postgres `ILIKE` substring; the 3rd time-scale axis `"semantic"` was a hardcoded `[]` stub (`user_layer.py:101-103`) — logged as `CARRY-026` in Sprint 51.2 ("Qdrant semantic 軸實作 L1/L2/L4"). The infra was unblocked by 57.146 (`EmbeddingClient` ABC + `QdrantVectorStore`) + 57.147 (per-tenant collection + `payload_filter` pattern) — the KB half of CARRY-026 closed — but the **memory half stayed open**. A stored fact "I lead the vector-search rewrite" was invisible to the query "who works on embeddings?" (no substring overlap → ILIKE misses it), and 57.150's dedup was "exact-normalized, NOT semantic (→ CARRY-026)".

## Root Cause

The `"semantic"` axis was never wired to any embedding/vector backend (51.2 simplified design). `UserLayer.read` returned `[]` for a semantic-only request and silently dropped the semantic portion of a mixed request. The `QdrantNamespaceStrategy` `Literal` had reserved `"user_memory"` since 49.3, and `memory_user.vector_id` was a dormant column — the slots existed but nothing consumed them.

## Solution

Slice 1 (L4 user layer only) mirroring the proven knowledge vector pattern, backend-only, opt-in:

- **NEW `agent_harness/memory/vector_index.py`** — `MemoryVectorIndex` (mirrors `KnowledgeVectorIndex`): composes the `EmbeddingClient` ABC + `QdrantVectorStore` + `QdrantNamespaceStrategy("user_memory")`. `search(*, tenant_id, user_id, rows, query, top_k)` lazily ingests the user's rows (idempotent via a **per-user count guard**, `_EMBED_BATCH=16`) then cosine-searches. Point ids from `_point_id(user_id, dedup_key)` (stable, per-user-unique); `_user_filter` stamps + filters `tenant_id`+`user_id` (per-user isolation in the shared per-tenant collection). Imports only the ABC + Qdrant (LLM-neutral / AP-8-clean — embed/search, not chat).
- **EDIT `memory/layers/user_layer.py`** — additive `vector_index=None` ctor param; `read()` gains a semantic branch: no semantic hits → keyword path UNCHANGED (byte-identical to 57.150, incl. the semantic-only `[]` stub); semantic hits → dedup-merge by row id (keep higher relevance), vector hits carry the cosine score as `relevance_score`. `_semantic_hits` helper fetches the user's rows → index → maps hits back by `dedup_key`, `try/except` **fail-soft** to `[]`.
- **EDIT `infrastructure/vector/qdrant_client.py`** — `count(name, payload_filter=None)` (per-user count; mirrors `search`'s filter; no-arg callers unaffected).
- **EDIT `core/config/__init__.py`** — `memory_vector_enabled: bool = False` (env `MEMORY_VECTOR_ENABLED`; reuses the knowledge `qdrant_url` + embedding config).
- **NEW `api/v1/chat/memory_vector_index.py`** — `get_memory_vector_index()` memoized singleton (mirrors `knowledge_index.py`: None on flag-off / unconfigured, lazy heavy imports, `reset_*` hook).
- **EDIT `api/v1/chat/_category_factories.py`** — `make_chat_memory_deps` injects the index into the UserLayer only.

NO migration (point ids from the 57.150 `dedup_key`; dormant `vector_id` stays dormant), NO wire event, NO frontend. Flag OFF → byte-identical to 57.154.

## Verification

- **Gates**: pytest **3123 / 6 skip (+17)** — 9 `test_memory_vector_index` + 3 qdrant `count` + 2 UserLayer semantic (+ kept stub) + 3 singleton + 2 real-DB integration · mypy `src` **399 / 0** · run_all **11/11** (AP-8 / llm_sdk_leak / cross_category clean) · black/isort/flake8 clean · FE untouched.
- **Drive-through PASS** (real chat-v2 + real Azure gpt-5.2 + real `text-embedding-3-large` 3072-dim + real Qdrant): `memory vector index built` on the main flow + per-user Qdrant ingest (jamie 5 / priya 2 pts in `tenant_09eb…_user_memory`, Cosine) + count-idempotency (Leg-2 no re-ingest) + Leg-1 fact written + Leg-2 keyword-disjoint recall (honest caveat: co-supported by 57.148 `profile()` + `knowledge_search`; the semantic MACHINERY is proven at the log/Qdrant layer) + **Leg-3 CLEAN per-user isolation** (priya cannot retrieve jamie's memory-only "Project Lodestar" fact nor his name, despite the shared per-tenant collection — the `user_id` payload filter isolates). Detail + screenshots: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-155/progress.md` Day 3 + `artifacts/`.

## Impact

Backend-only, 範疇 3 Memory (L4 user). Opt-in (`MEMORY_VECTOR_ENABLED`, default OFF) → zero impact when off. Closes CARRY-026 Slice 1; L1 system / L2 tenant / session-summary ranking + semantic write-dedup remain (CARRY-026 remaining slices, `AD-Memory-Semantic-*`). Design note: `58-memory-vector-recall-design.md`.
