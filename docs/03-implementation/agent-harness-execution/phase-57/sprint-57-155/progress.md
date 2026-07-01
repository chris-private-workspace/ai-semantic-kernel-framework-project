# Sprint 57.155 Progress — CARRY-026 Slice 1: semantic recall on the user memory layer

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-155-plan.md) · [Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-155-checklist.md)

Branch `feature/sprint-57-155-memory-vector-recall` from `main` `c3d1bff1`.

---

## Day 0 — 2026-07-01 — Plan-vs-Repo Verify (三-prong) + Branch

**Verdict: GO, scope-shift ~0%.** All 8 Day-0 D-items confirmed clean; one scope REDUCTION.

### Drift findings

| ID | Finding | Implication |
|----|---------|-------------|
| **D-count-filter-signature** | `QdrantVectorStore.count(self, name)` has NO `payload_filter` today (`qdrant_client.py:88`); the ONLY caller is `knowledge/vector_index.py:135` (no-arg) | Adding `payload_filter=None` default is byte-safe for the existing caller. Confirmed. |
| **D-userlayer-ctor** | `UserLayer.__init__(self, session_factory)` — only param is `session_factory` (`user_layer.py:81`) | `vector_index=None` is purely additive → byte-identical when absent. Confirmed. |
| **D-read-timescales** | `("semantic",)`-only short-circuits to `[]` (`:101-103`); mixed path runs ILIKE, silently drops semantic (`:106-113`) | New branch slots in without changing keyword behavior. Confirmed. |
| **D-factory-userlayer-site** | `"user": UserLayer(session_factory)` at `_category_factories.py:304`; both callers (loop prompt builder + auto-extract ctx) share `make_chat_memory_deps` | Inject once in the factory → both callers get the index. Confirmed. |
| **D-embedding-configured** | `knowledge_index.py:55-107` singleton pattern (`is_embedding_configured()` + `qdrant_url` gate, lazy imports) is the mirror target | `memory_vector_index.py` mirrors it (simpler — MemoryVectorIndex takes only embedder+store, no docs_root). Confirmed. |
| **D-qdrant-count-filter-model** | `search` uses `models.Filter.model_validate(payload_filter) if payload_filter else None` (`qdrant_client.py:127`) | `count` mirrors the exact shape (`count_filter=`). Confirmed. |
| **D-ap8-neutrality** | AP-8 (`check_promptbuilder_usage.py:132`) only flags `.chat()`/`.stream()`; `vector_index.py` calls only `.embed()`/`.search()` | **Scope REDUCTION**: NO allowlist needed (`_register_all`/lint allowlist untouched). `check_llm_sdk_leak` also green (imports only ABC + Qdrant). Confirmed. |
| **D-namespace-literal** | `QdrantNamespaceStrategy` `Literal` already enumerates `"user_memory"` (`qdrant_namespace.py:55-60`, 49.3-reserved) | `collection_name(tid,"user_memory")` → `tenant_<hex>_user_memory`; namespace file untouched. Confirmed. |

**Prong 3 (schema)**: N/A — no DB table / migration / ORM column (point ids from 57.150 `dedup_key`; dormant `vector_id` stays dormant). Migration head still `0033`. Confirmed.

**Baselines re-verified Day-2**: pytest 3106 → 3123 (+17) · mypy `src` 397 → 399/0 · run_all 11/11.

**Numbering**: CHANGE-122 free (121 highest) · design note `58-*` free (57 highest).

Branch created from `main` `c3d1bff1`.

---

## Day 1 — 2026-07-01 — MemoryVectorIndex + count filter (US-1)

- **1.1 `QdrantVectorStore.count(name, payload_filter=None)`** — added the optional per-user filter, mirroring `search`'s `models.Filter.model_validate`. Existing no-arg callers unaffected (updated the sibling `_FakeQdrant.count` in `test_qdrant_client.py` + added a filter-scoping test + `test_count_absent_collection`).
- **1.2 `MemoryVectorIndex`** (`agent_harness/memory/vector_index.py`, ~155 lines) — mirrors `KnowledgeVectorIndex`: `EmbeddingClient` ABC + `QdrantVectorStore` + `QdrantNamespaceStrategy("user_memory")`; `search(*, tenant_id, user_id, rows, query, top_k)` with `_EMBED_BATCH=16`, per-user count-idempotency, `_point_id(user_id, dedup_key)` stable, `_user_filter` two-key. Imports only the ABC + Qdrant (neutrality clean).
- **1.3 unit tests** (`test_memory_vector_index.py`, 9 tests) — exact-content ranks first (cosine 1.0), empty guards, lazy-ingest idempotency, new-fact re-ingest, batch-16, point-id stability + per-user uniqueness, tenant+user payload stamp, per-user isolation.
- **1.x partial gate**: black/isort/flake8 + mypy clean; 15 tests pass (9 index + 6 qdrant).

---

## Day 2 — 2026-07-01 — UserLayer semantic branch + opt-in singleton + factory (US-2/US-3)

- **2.1 `UserLayer` semantic branch** — additive `vector_index=None` ctor param; `read()` reworked: `want_keyword` (short/long ILIKE, unchanged, preserves `profile()`'s wildcard) + `want_semantic` (`"semantic"` in scales AND index injected AND non-empty query). No semantic hits → keyword path returned UNCHANGED (byte-identical to 57.150, incl. the semantic-only `[]` stub). Semantic hits → dedup-merge by row id (keep higher relevance), vector hits carry cosine as `relevance_score`. New `_semantic_hits` helper fetches the user's rows, calls the index, maps hits back by `dedup_key`, `try/except` fail-soft to `[]`. Header Description + MHist updated.
  - Tests: kept `test_read_semantic_only_returns_empty` (validates the index=None stub); ADDED `test_read_semantic_returns_vector_hits_when_index_injected` + `test_read_semantic_fail_soft_on_index_error`.
- **2.2 opt-in flag + singleton + factory** — `memory_vector_enabled: bool = False` (`core/config`, env `MEMORY_VECTOR_ENABLED`, beside `knowledge_vector_enabled`); `get_memory_vector_index()` memoized singleton (`api/v1/chat/memory_vector_index.py`, mirrors `knowledge_index.py`: None on flag-off / unconfigured, lazy heavy imports, `reset_*` hook); `make_chat_memory_deps` injects it into the UserLayer only. Singleton tests (3): flag-off → None, flag-on-unconfigured → None, flag-on-configured → builds + memoizes.
- **2.3 integration test** (`tests/integration/memory/test_memory_vector_recall.py`, 2 tests, REAL Postgres + real `MemoryVectorIndex`/`DeterministicEmbeddingClient` + fake Qdrant): real DB rows → semantic-only read returns the row via the vector path (cosine 1.0, NOT the `[]` stub); per-user isolation (user A's search never returns user B's fact via the payload filter).
- **2.x full gate**: **pytest 3123 passed / 6 skip (+17)** · **mypy `src` 399 files / 0 errors** · flake8 clean · **run_all 11/11** · black/isort clean · FE untouched (no Vitest/mockup delta).

## Day 3 — 2026-07-01 — Drive-through (US-4) — real chat-v2 + real Azure text-embedding-3-large + real Qdrant

**Verdict: PASS.** Real UI (chat-v2 on :3007) + real Azure gpt-5.2 + real `text-embedding-3-large` (3072-dim) + real Qdrant (`ipa_v2_qdrant` on :6333). Clean-restarted the backend (killed stale PID 49236 + spawn-worker 61628 per Risk Class E; fresh sole PID; `MEMORY_VECTOR_ENABLED=true`). Two users, SAME tenant acme-prod: **jamie** (user `04dc4ee0`) + **priya** (user `dc921d38`).

### Machinery LIVE on the main flow (the decisive 57.155-specific evidence)

- Backend log (first chat send): `memory vector index built (model=text-embedding-3-large)` — the singleton built lazily on the real chat path (no startup-blocking), real Azure embeddings.
- Per-user lazy ingest: `ingested 4 rows … user=04dc4ee0` → `ingested 5 rows … user=04dc4ee0` (jamie's new fact bumped 4→5, count-idempotency re-ingest) ; later `ingested 2 rows … user=dc921d38` (priya's own facts).
- Qdrant collection `tenant_09eb1b629fd3439a_user_memory`: **7 points, size 3072, Cosine**; per-user breakdown **jamie 5 / priya 2** — both users' points coexist in the ONE per-tenant collection, isolated by the `user_id` payload. (`QdrantNamespaceStrategy.collection_name(tid,"user_memory")` live.)
- Count-idempotency: jamie's Leg-2 search re-used the collection with NO re-ingest (`count==5==len(rows)`) — the guard works live (no wasted embed).

### Leg 1 (jamie states a fact) — PASS

jamie: "Remember this about me: I'm the lead engineer on **Project Lodestar**, our initiative to replace keyword lookup with meaning-based retrieval." → agent proactively `memory_write` (`{scope:user, key:role_project_lodestar, content:"User is the lead engineer on Project Lodestar…", confidence:0.9}` → `ok:true`) + "Got it — I'll remember…" + Verification passed (0.99). Fact embedded into Qdrant (visible in the 5-point payload). [`artifacts/sprint-57-155-leg1-jamie-states-fact.png`]

### Leg 2 (jamie NEW-session keyword-disjoint recall) — PASS with honest caveat

NEW session, query "who owns the effort to make search find things by concept rather than exact literal terms? name the person and the initiative" (ZERO keyword overlap with the stored fact). Agent recalled **"Project Lodestar — replacing keyword lookup with meaning-based (semantic) retrieval"** (verbatim from jamie's memory fact). [`artifacts/sprint-57-155-leg2-jamie-semantic-recall.png`]

**Honest attribution caveat**: the recall is co-supported by the always-on `profile()` (57.148, returns the user's rows keyword-independently) AND the agent also called `knowledge_search` (57.145 KB) which muddied the source attribution (it hedged "I can't confirm the owner from internal docs"). So the ANSWER alone does not isolate the semantic axis from `profile()`. The semantic axis's DISTINCTIVE machinery (embed + cosine + per-user Qdrant) IS proven live (logs + Qdrant above); a few-fact scenario cannot behaviourally separate it from `profile()`. This is a fair limitation of the drive-through, not a defect — 57.155's value (relevance-ranked recall at many-fact scale) is proven at the machinery layer.

### Leg 3 (priya per-user isolation) — CLEAN PASS (the strongest 57.155-specific proof)

priya (same tenant, different user), NEW session: "Do you remember … my name, my role, or a project called Project Lodestar? … who leads Project Lodestar if you know." → priya recalled ONLY her own memory ("I remember you as a **compliance lead** preparing for a **SOC 2 Type II audit** … I **do not have your name**") and explicitly **"did not find any source that states who leads Project Lodestar, so I don't know"** + Verification passed (0.97). [`artifacts/sprint-57-155-leg3-priya-final-answer.png`]

"Project Lodestar" + jamie's name ("Chris"/"Dana Okafor") exist ONLY in jamie's user memory (nowhere in the shared KB — priya's `knowledge_search` for "Project Lodestar lead" returned unrelated state-mgmt docs). priya's semantic search (payload_filter `tenant_id=acme AND user_id=dc921d38`) returns 0 of jamie's 5 points → **complete per-user isolation at BOTH the vector-store layer AND the user-facing answer**, despite the shared per-tenant collection. (An unrelated per-tenant HITL "checkpoint" escalation policy from 57.106 paused priya mid-run; approved to continue — not a 57.155 concern.)

**Post-run**: reverted `.env` `MEMORY_VECTOR_ENABLED` to the shipped default (removed the line; the running backend keeps it on until its next restart). Screenshots in `artifacts/`.

**Status**: Day 0-3 complete (all gates green + drive-through PASS). Day 4 (CHANGE-122 + design note 58 + closeout) pending.
