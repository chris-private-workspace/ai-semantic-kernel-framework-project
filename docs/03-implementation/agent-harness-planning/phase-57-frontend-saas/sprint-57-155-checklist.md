# Sprint 57.155 — Checklist (CARRY-026 Slice 1: semantic recall on the user memory layer)

[Plan](./sprint-57-155-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch

### 0.1 Three-prong Day-0 verify (against `main` HEAD `c3d1bff1`)
- [x] **Prong 1 — path verify**: 4 NEW targets free (`memory/vector_index.py`, `api/v1/chat/memory_vector_index.py`, 2 test files); 6 EDIT files present; `CHANGE-122` free (121 highest); design note `58-*` free (57 highest)
- [x] **Prong 2 — content verify** (drift → progress.md):
  - [x] **D-count-filter-signature** — confirmed `count(self, name)` has NO filter; only caller = knowledge `vector_index.py:135` (no-arg) → default-None byte-safe
  - [x] **D-userlayer-ctor** — confirmed `__init__(self, session_factory)` only → `vector_index=None` purely additive
  - [x] **D-read-timescales** — confirmed `("semantic",)` short-circuit `:101-103` + mixed ILIKE `:106-113` → branch slots in cleanly
  - [x] **D-factory-userlayer-site** — confirmed `"user": UserLayer(session_factory)` at `_category_factories.py:304` (both callers share the factory)
  - [x] **D-embedding-configured** — confirmed `knowledge_index.py:55-107` mirror target (is_embedding_configured + qdrant_url gate, lazy imports)
  - [x] **D-qdrant-count-filter-model** — confirmed `models.Filter.model_validate(payload_filter)` shape (`qdrant_client.py:127`) → `count` mirrors via `count_filter=`
  - [x] **D-ap8-neutrality** — confirmed AP-8 flags only `.chat()`/`.stream()` (`check_promptbuilder_usage.py:132`); embed/search-only → NO allowlist needed (scope REDUCTION); llm_sdk_leak green
  - [x] **D-namespace-literal** — confirmed `Literal` includes `"user_memory"` (`qdrant_namespace.py:55-60`) → namespace file untouched
- [x] **Prong 3 — schema verify**: N/A (no DB table / migration / ORM column; migration head still `0033`)
- [x] **D-baselines** — pytest 3106 → 3123 (+17) · mypy `src` 397 → 399/0 · run_all 11/11 (re-verified Day 2)
- [x] **Catalog drift** — progress.md Day-0 table (8 D-findings + implications)
- [x] **Go/no-go** — scope-shift ~0% → proceed

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-155-memory-vector-recall` (from `main` `c3d1bff1`)

---

## Day 1 — MemoryVectorIndex + count filter (US-1)

### 1.1 QdrantVectorStore.count payload_filter
- [x] **`count(name, payload_filter: dict | None = None) -> int`** — added; mirrors `search`'s `models.Filter.model_validate`; no-arg callers unaffected (updated `_FakeQdrant.count` + 2 new tests: filter-scoping + absent-collection)
  - DoD: both arities tested (no filter = total; filter = per-payload subset) ✅
- [x] **MemoryVectorIndex + MemoryVectorHit** (`agent_harness/memory/vector_index.py`, ~155 lines) — `EmbeddingClient` + `QdrantVectorStore` + `QdrantNamespaceStrategy("user_memory")`; `_EMBED_BATCH=16`, per-user count idempotency, `_point_id(user_id, dedup_key)` stable, `_user_filter` two-key; imports NO provider SDK
  - DoD: empty guards → `[]`; upsert once when count≠len; batch ≤16; search filtered by tenant+user ✅
- [x] **`test_memory_vector_index.py`** (9 tests, DeterministicEmbeddingClient + `_FakeMemStore`) — exact-content ranks cosine 1.0, lazy-ingest idempotency, new-fact re-ingest, batch-16, point-id stability/uniqueness, payload stamp, per-user isolation
- [x] **1.x partial gate** — black/isort/flake8 + mypy clean; 15 tests pass (9 index + 6 qdrant)

---

## Day 2 — UserLayer semantic branch + opt-in singleton + factory (US-2/US-3)

### 2.1 UserLayer semantic branch
- [x] **`UserLayer.__init__(..., vector_index=None)` + `read()` semantic branch** — no semantic hits → keyword path UNCHANGED (byte-identical stub incl. semantic-only `[]`); semantic hits → dedup-merge by row id (keep higher relevance), cosine `relevance_score`; `_semantic_hits` helper fetches rows → index → map by dedup_key, `try/except` fail-soft
  - DoD: index=None byte-identical; index present → vector hits; forced exception → fail-soft (no raise) ✅
- [x] **Update `test_user_layer.py`** — KEPT the stub test (index=None validation); ADDED `test_read_semantic_returns_vector_hits_when_index_injected` + `test_read_semantic_fail_soft_on_index_error` (extended, not weakened)
- [x] **`memory_vector_enabled: bool = False`** (`core/config`, env `MEMORY_VECTOR_ENABLED`, beside `knowledge_vector_enabled`)
- [x] **`get_memory_vector_index()`** (`api/v1/chat/memory_vector_index.py`) — memoized; `None` on flag-off / unconfigured / no qdrant_url; lazy imports; `reset_*` hook (mirror `knowledge_index.py`); 3 singleton tests (off→None / unconfigured→None / configured→builds+memoizes)
- [x] **`make_chat_memory_deps` injects the index into `UserLayer`** (`_category_factories.py`) — `get_memory_vector_index()` once → UserLayer ctor only
- [x] **`test_memory_vector_recall.py`** (2 tests, REAL Postgres + real MemoryVectorIndex/DeterministicEmbeddingClient + fake Qdrant) — real DB rows → semantic read returns row (cosine 1.0, not stub); per-user isolation A↛B
- [x] **2.x Full gate** — **pytest 3123 passed / 6 skip (+17)** · **mypy `src` 399/0** · run_all 11/11 · black/isort/flake8 clean · LLM-SDK-leak clean · FE untouched (no Vitest/mockup delta)

---

## Day 3 — Drive-through (US-4) — real chat-v2 + real backend + real Azure embeddings + real Qdrant

### 3.1 Clean restart (Risk Class E)
- [x] Set `MEMORY_VECTOR_ENABLED=true`; killed stale PID 49236 + spawn-worker 61628; fresh sole PID on :8000; real Qdrant `ipa_v2_qdrant` up + `AZURE_OPENAI_DEPLOYMENT_EMBEDDING=text-embedding-3-large` confirmed

### 3.2 Drive-through (MANDATORY — NOT gate-only) — real chat-v2 + real Azure gpt-5.2 + real text-embedding-3-large + real Qdrant
- [x] **Machinery LIVE**: log `memory vector index built (text-embedding-3-large)` + per-user ingest (jamie 4→5 / priya 2) + Qdrant `tenant_09eb…_user_memory` 7 pts (jamie 5 / priya 2) · 3072-dim · Cosine + count-idempotency (Leg-2 no re-ingest)
- [x] **Leg 1**: jamie states "Project Lodestar … replace keyword lookup with meaning-based retrieval" → agent `memory_write` conf 0.9 → embedded into Qdrant
- [x] **Leg 2 recall**: jamie NEW-session keyword-disjoint query → recalled "Project Lodestar … meaning-based retrieval" verbatim (honest caveat: co-supported by 57.148 profile() + knowledge_search muddied attribution; semantic MACHINERY proven live at the log/Qdrant layer)
- [x] **Leg 3 per-user isolation (CLEAN)**: priya (same tenant, diff user) → recalled ONLY her own SOC2/compliance memory, "did not find any source that states who leads Project Lodestar", "I do not have your name"; Qdrant user_id payload filter isolates jamie's 5 pts from priya
- [x] Screenshots (4 legs) + observed-vs-intended → progress.md Day 3 + `artifacts/`; `.env` flag reverted to shipped default

---

## Day 4 — CHANGE-122 + design note 58 + closeout

### 4.1 CHANGE-122 + design note 58
- [x] **`CHANGE-122-memory-vector-recall.md`** (gap + MemoryVectorIndex on L4 + drive-through PASS + CARRY-026 Slice-1 shipped)
- [x] **`58-memory-vector-recall-design.md`** (8-point gate all ✅: §2 decision matrices + file:line per claim + verification commands + fixtures + §5 open-invariant split (incl. honest profile() attribution caveat) + §6 1-line rollback + §4 17.md cross-ref)

### 4.2 Closeout
- [x] retrospective.md Q1-Q7 + calibration (`memory-vector-recall-spike` 0.60, 1st pt ~1.0 IN band → KEEP)
- [x] Final gate sweep: mypy `src` 399/0 · run_all 11/11 · pytest 3123/6skip · black/isort/flake8 + LLM-SDK-leak clean · FE untouched (no Vitest/mockup delta)
- [x] Navigators: CLAUDE.md Current-Sprint + Last-Updated · MEMORY.md pointer + subfile · next-phase-candidates (CARRY-026 Slice-1 done + carryovers) · sprint-workflow matrix (`memory-vector-recall-spike` 0.60 row)
- [x] Anti-pattern self-check (retro Q5): AP-2/3/4/6/8/11 → 0 violations; v2 lints 11/11
- [ ] **Commit** → ⏳ PR push + open → CI → merge: PENDING USER CONFIRMATION (push is outward-facing per Developer Preferences) → post-merge status flip after gh-verified MERGED
