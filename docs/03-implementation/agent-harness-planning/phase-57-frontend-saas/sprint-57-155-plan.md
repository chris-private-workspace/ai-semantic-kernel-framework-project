# Sprint 57.155 Plan — CARRY-026 Slice 1: semantic recall on the user memory layer

**Summary**: Wire the long-stubbed Cat 3 memory **semantic axis** onto the L4 user layer — the first vertical slice of `CARRY-026` (logged Sprint 51.2, infra unblocked by 57.146/57.147, still not wired). A NEW `MemoryVectorIndex` mirrors the proven `KnowledgeVectorIndex` (reuse `EmbeddingClient` ABC + `QdrantVectorStore` + `QdrantNamespaceStrategy` `"user_memory"` collection, both pre-existing) to give per-tenant+per-user semantic recall, replacing the `"semantic"`-time-scale `[]` stub in `UserLayer.read`. Opt-in `MEMORY_VECTOR_ENABLED` (default OFF → byte-identical); fail-soft to the existing keyword/stub path on any embedding/Qdrant error. Backend-only: NO migration (point ids derived from the 57.150 `dedup_key`; dormant `vector_id` column stays dormant), NO wire event, NO frontend. A drive-through is **MANDATORY** (user-facing recall on chat-v2: a semantically-related query with NO keyword overlap must retrieve the right user fact by meaning — the thing ILIKE cannot do). Spike sprint → a design note is required.

**Status**: Approved-to-execute (user selected the Memory track 2026-07-01, then picked "CARRY-026 語意記憶軸 (Recommended)" via AskUserQuestion over MultiRun / per-tenant-override / async-queue).
**Branch**: `feature/sprint-57-155-memory-vector-recall`
**Base**: `main` HEAD `c3d1bff1` (Sprint 57.154 flip commit — combined-formation A/B MERGED)
**Slice**: CARRY-026 Slice 1 (of the L1 system / L2 tenant / L4 user semantic axis originally scoped in Sprint 51.2). This slice = L4 user only; L1/L2 + session ranking = CARRY-026 remaining slices.
**Scope decisions**: (a) L4 user layer ONLY — mirrors the knowledge arc's slice-by-slice cadence (57.145 connector → 57.146 embedding → 57.147 per-tenant); (b) **lazy ingest-on-search** (mirrors `KnowledgeVectorIndex`, does NOT touch the 57.150 write-path upsert) with a per-user count-idempotency guard + `dedup_key`-derived stable point ids; (c) per-tenant collection from day 1 via `QdrantNamespaceStrategy.collection_name(tid, "user_memory")` + per-user `payload_filter` (reuse the 57.147 pattern, no non-tenant-first retrofit); (d) opt-in `MEMORY_VECTOR_ENABLED` default OFF, fail-soft to the current `[]` stub; (e) NO migration / NO wire event / NO frontend — backend-only like the knowledge slices.

---

## 0. Background

### The gap (CARRY-026 — the Cat 3 memory semantic axis)

Cat 3 Memory has **zero semantic/vector retrieval today**. Every one of the 5 layers reads by Postgres `ILIKE` substring (or in-memory substring for the session layer). The 3rd time-scale axis — `"semantic"` — is a hardcoded empty-list stub throughout: a semantic-only request returns `[]`, and a mixed request silently drops the semantic portion and keeps only the keyword hits.

- Logged Sprint 51.2 as `CARRY-026`: "Qdrant semantic 軸實作 (L1/L2/L4 vector store) → Phase 53.x" (`sprint-51-2-plan.md:283`); the whole semantic column of the 5×3 matrix was stubbed.
- The infra was **unblocked** by 57.146 (`EmbeddingClient` ABC + `QdrantVectorStore`) + 57.147 (per-tenant collection + `payload_filter` pattern). Every design note since carries it as "unblocked, NOT wired" (`50-...-design.md:68`, `51-...-design.md:73`, `52-...-design.md:67`, `53-...-design.md:73`, `54-...-design.md:53`). The **KB half is closed** (`qdrant_client.py:24` "closes CARRY-026 for KB"); the **memory half stays open**.

### Why it matters (the missing capability)

Recall is keyword-gated: a stored fact "Chris leads the vector-search rewrite" is invisible to the query "who works on embeddings?" — no substring overlap → ILIKE misses it. Sprint 57.150's dedup is likewise "exact-normalized (case/whitespace), NOT semantic (→ CARRY-026)" (`project_phase57_150...:14`), and 57.151's session recall is recency-ordered only. Semantic recall is the capability that lets the agent surface memory by **meaning**, not literal word match — the core of a genuinely knowledge-aware, long-lived personal agent (reality-audit §9 pillar).

### Root cause (recon code read, file:line; ALL re-verified §checklist 0.1)

| Layer | Reality (on `main` HEAD `c3d1bff1`) | Anchor |
|-------|-------------------------------------|--------|
| UserLayer semantic-only | short-circuits to `[]` (the stub) | `memory/layers/user_layer.py:101-102` |
| UserLayer mixed read | ILIKE `content`/`category` only; semantic axis silently dropped | `user_layer.py:106-113` (ILIKE at `:110`) |
| MemoryRetrieval.search | requests `("short_term","long_term","semantic")`, merges by `relevance*confidence` where relevance = substring 0.4/0.8 | `memory/retrieval.py:98-159` (relevance `:295` in user_layer) |
| memory_search tool | schema advertises a `"semantic"` enum the backend never fulfills | `tools/memory_tools.py:147-155` |
| Reusable infra (exists, unconsumed) | `QdrantNamespaceStrategy` `Literal` already enumerates `"user_memory"` (49.3); `QdrantVectorStore` docstring says memory can reuse it | `infrastructure/vector/qdrant_namespace.py:55-60`, `qdrant_client.py:10-13` |
| Dormant column | `memory_user.vector_id VARCHAR(128)` never written/read (a Qdrant payload-ref, NOT pgvector) | `models/memory.py:229`, `0007_memory_layers.py:180` |

→ The fix must give `UserLayer.read` a real semantic branch (embed the query, cosine-search a per-tenant+user Qdrant collection built from the user's rows) that carries real cosine relevance into the existing `relevance*confidence` merge — behind an opt-in flag, fail-soft to the current stub.

### The design (backend-only: 1 new index + 1 layer read-branch + 1 opt-in singleton + 1 count-filter; NO migration/wire/frontend)

```
NEW  agent_harness/memory/vector_index.py   MemoryVectorIndex  (mirror KnowledgeVectorIndex)
       compose EmbeddingClient(ABC) + QdrantVectorStore + QdrantNamespaceStrategy("user_memory")
       search(tenant_id, user_id, rows, query, top_k):
         coll = namespace.collection_name(tid, "user_memory")          # tenant_<hex>_user_memory
         ensure_collection(coll, dim)                                   # dim = len(embed[0])
         if store.count(coll, payload_filter=user_filter) != len(rows): # per-user idempotency
             embed rows in _EMBED_BATCH(16) chunks; upsert points
               id   = int(md5(f"{user_id}:{dedup_key}")[:16], 16)       # stable, per-user unique
               payload = {tenant_id, user_id, content, confidence, dedup_key}
         qv = embed([query])[0]
         return store.search(coll, qv, top_k, payload_filter={tenant_id AND user_id})

EDIT user_layer.py   __init__(..., vector_index: MemoryVectorIndex|None=None)
       read():  semantic-only  → vector search when index present, else [] (current stub)
                mixed w/ "semantic" → keyword ILIKE (short/long) ∪ vector hits, dedup by content
                vector hits carry cosine as relevance_score → the retrieval merge ranks them
       (fail-soft: any embed/Qdrant error → drop to keyword/[] path, never break recall)

EDIT core/config/__init__.py       memory_vector_enabled: bool = False   (env MEMORY_VECTOR_ENABLED)
NEW  api/v1/chat/memory_vector_index.py   get_memory_vector_index()   memoized singleton
       (mirror knowledge_index.py: None when flag off / embedding unconfigured / no qdrant_url;
        lazy heavy Azure/Qdrant imports only when flag on)  + reset_* test hook
EDIT api/v1/chat/_category_factories.py   make_chat_memory_deps → inject index into UserLayer
EDIT infrastructure/vector/qdrant_client.py   count(name, payload_filter=None)  (per-user count)
```

*Why lazy-ingest-on-search over embed-on-write*: embed-on-write would touch the 57.150 dedup upsert (higher risk) and needs a separate backfill for pre-flag rows. Lazy-ingest-on-search mirrors `KnowledgeVectorIndex` exactly, backfills for free, and keeps the write path byte-untouched; the per-user count guard keeps steady-state embedding cost near-zero. Incremental embed-on-write is a noted follow-on optimization.

### Ground truth (recon head-start — code read on `main` HEAD `c3d1bff1`; ALL re-verified §checklist 0.1)

- `adapters/_base/embedding_client.py:44` — `async def embed(self, texts: list[str]) -> list[list[float]]` (batch, order-preserving; dim = `len(vectors[0])`, no `dim()` method).
- `infrastructure/vector/qdrant_client.py:114-140` — `search(name, query_vector, top_k, payload_filter=None)`; `:88-97` — `count(name)` (NO filter today → the one small extension needed); cosine in `ensure_collection` `:69`.
- `infrastructure/vector/qdrant_namespace.py:75-89` — `collection_name(tenant_id, layer)` → `tenant_<16hex>_<layer>`; `:91-107` — `payload_filter(tid)` (tenant-only; per-user filter built inline in the index); `Literal` includes `"user_memory"` `:55-60`.
- `business_domain/knowledge/vector_index.py:65-192` — the exact shape to mirror (`_EMBED_BATCH=16` `:62`, `count==expected` idempotency `:135-136`, `recreate_collection` on dim `:143-144`, tenant payload stamp `:147-152`, lazy `ingest`-in-`search` `:169`).
- `api/v1/chat/knowledge_index.py:55-107` — the memoized `get_*_vector_index()` singleton to mirror (None on flag-off/unconfigured, lazy imports, `reset_*` hook).
- `core/config/__init__.py:212-220` — `knowledge_vector_enabled: bool = False` (`:217`) + `qdrant_url` (`:220`) — the exact opt-in flag precedent.
- `api/v1/chat/_category_factories.py:265-314` — `make_chat_memory_deps(db)` builds the 5-layer map (`:300-306`) + `MemoryRetrieval` (`:313`); the UserLayer construction site is the injection point.
- `memory/layers/user_layer.py:63-73` — `_dedup_key(content)` = `md5(lower(strip(collapse_ws(content))))` (57.150) — the stable per-row id source for Qdrant point ids.

**Baselines (Sprint 57.154 closeout)**: pytest 3106 (incl. skips) · wire 26 · Vitest 922 · mockup 51 · mypy `src` 0/397 · run_all 11/11. Re-verify Day-0.

### STALE / drift findings (Day-0; full detail → progress.md — placeholder, filled in §checklist 0.1)

- **D-count-filter-signature** — grep `def count` in `qdrant_client.py` → confirm it takes NO `payload_filter` today (the plan adds one); confirm no other caller breaks on the added-keyword-with-default.
- **D-userlayer-ctor** — read `UserLayer.__init__` → confirm current param list so the added `vector_index=None` keyword is purely additive (byte-identical when None).
- **D-read-timescales** — re-read `user_layer.py:84-122` → confirm the exact `time_scales` tuple handling (the `("semantic",)`-only short-circuit vs the mixed path) so the new branch slots in without changing keyword behavior.
- **D-factory-userlayer-site** — grep `UserLayer(` in `_category_factories.py` → confirm the construction line to thread the index into.
- **D-embedding-configured** — confirm `is_embedding_configured()` (`adapters/azure_openai/config.py:108-110`) + `AZURE_OPENAI_DEPLOYMENT_EMBEDDING` are the same gate `knowledge_index.py` uses (reuse verbatim).
- **D-qdrant-count-filter-model** — confirm `models.Filter.model_validate(payload_filter)` is the shape `search` already uses (`qdrant_client.py:119`) so `count` mirrors it exactly.
- **D-ap8-neutrality** — confirm `vector_index.py` (in `agent_harness/`) imports ONLY the `EmbeddingClient` ABC + `QdrantVectorStore` (no `openai`/`anthropic`) so `check_llm_sdk_leak` stays green; the singleton in `api/` may import the Azure adapter (composition root, allowed — same as `knowledge_index.py`).

## 1. Sprint Goal

Ship an opt-in semantic recall axis on the L4 user memory layer so that, with `MEMORY_VECTOR_ENABLED=true`, a chat-v2 user can store a personal fact and later retrieve it via a query that shares NO keyword with it — proven by a **MANDATORY drive-through** (real chat-v2 UI + real backend + real Azure `text-embedding-3-large` + real Qdrant) plus the full gate set (mypy `src` 0/N · run_all 11/11 · pytest +new · black/isort/flake8 + llm_sdk_leak clean). With the flag OFF the platform is byte-identical to 57.154. Produces CHANGE-122 + design note `58-memory-vector-recall-design.md` (spike sprint).

## 2. User Stories

- **US-1** (semantic index): 作為平台工程師，我希望有一個 `MemoryVectorIndex` 鏡像已驗證的 `KnowledgeVectorIndex`（重用 EmbeddingClient ABC + QdrantVectorStore + `"user_memory"` namespace），以便 memory 層取得 per-tenant+per-user 的向量檢索能力，且不新增任何 ABC / infra。
- **US-2** (layer wiring): 作為 agent runtime，我希望 `UserLayer.read` 的 `"semantic"` 分支在注入 index 時回傳真實 cosine-ranked 命中（否則維持現 `[]` stub），以便 `memory_search` 工具與 PromptBuilder 的 semantic pass 首次成為真實能力。
- **US-3** (opt-in + fail-soft): 作為維運者，我希望 `MEMORY_VECTOR_ENABLED`（預設 OFF）閘控整條語意路徑、任何 embedding/Qdrant 錯誤 fail-soft 退回關鍵字/stub，以便關閉時 byte-identical、開啟時永不因外部依賴故障而中斷 recall。
- **US-4** (drive-through, MANDATORY): 作為使用者，我希望在真 chat-v2 存一個個人事實後，用一個「無關鍵字重疊」的語意問句能被喚回，以便證明語意 recall 真的能用（非 gate-only）。
- **US-5** (closeout): 作為專案，我希望 CHANGE-122 + design note 58 + 校準 + navigators + CARRY-026 Slice-1 狀態更新齊備，以便 sprint 可審計收尾。

## 3. Technical Specifications

### 3.0 Architecture (backend-only; NO migration / NO wire event / NO frontend / NO new ABC)

```
NEW    backend/src/agent_harness/memory/vector_index.py         MemoryVectorIndex + MemoryVectorHit
NEW    backend/src/api/v1/chat/memory_vector_index.py           get_memory_vector_index() singleton + reset_*
NEW    backend/tests/unit/agent_harness/memory/test_memory_vector_index.py   fake embedder + spy Qdrant
NEW    backend/tests/unit/api/v1/chat/test_memory_vector_index_singleton.py  flag-off/unconfigured None paths
EDIT   backend/src/agent_harness/memory/layers/user_layer.py    __init__ +vector_index; read() semantic branch
EDIT   backend/src/infrastructure/vector/qdrant_client.py       count(name, payload_filter=None)
EDIT   backend/src/core/config/__init__.py                      memory_vector_enabled: bool = False
EDIT   backend/src/api/v1/chat/_category_factories.py           inject index into UserLayer when flag on
EDIT   backend/tests/unit/agent_harness/memory/test_user_layer.py   semantic-stub test → parametrized (off=stub / on=vector)
EDIT   backend/scripts/lint/... (allowlist)                     only if a lint root needs vector_index.py — verify Day-0, likely NONE
UNTOUCHED  memory/layers/{system,tenant,role,session}_layer.py  (CARRY-026 remaining slices)
UNTOUCHED  memory/retrieval.py                                   (profile()/search() merge already carries relevance_score)
UNTOUCHED  memory/layers/user_layer.py write path (57.150 dedup) (lazy-ingest-on-read design → write untouched)
UNTOUCHED  infrastructure/db/migrations/                         (no column; point ids from dedup_key)
UNTOUCHED  17-cross-category-interfaces.md                       (no new contract — reuses EmbeddingClient ABC §2.1)
```

### 3.1 MemoryVectorIndex (US-1) — `agent_harness/memory/vector_index.py`

- `class MemoryVectorIndex`: ctor `(embedder: EmbeddingClient, store: QdrantVectorStore)` — no db coupling; callers pass rows in.
- `async search(*, tenant_id, user_id, rows: list[MemoryRow], query, top_k) -> list[MemoryVectorHit]`:
  - empty `rows` or empty `query.strip()` → `[]` (guard, mirrors `vector_index.py:167`).
  - `collection = QdrantNamespaceStrategy.collection_name(tenant_id, "user_memory")`.
  - lazy ingest: embed the `rows` bodies in `_EMBED_BATCH=16` chunks; `dim = len(vectors[0])`; `await store.ensure_collection(collection, dim)`; if `await store.count(collection, payload_filter=_user_filter(tenant_id, user_id)) != len(rows)` → upsert points (`id = _point_id(user_id, dedup_key)`, payload stamps `tenant_id`+`user_id`+`content`+`confidence`+`dedup_key`). Idempotent per-user.
  - `qvec = (await embedder.embed([query]))[0]`; `hits = await store.search(collection, qvec, top_k, payload_filter=_user_filter(...))`; map `VectorHit → MemoryVectorHit(content, confidence, score)`.
- `_point_id(user_id, dedup_key)` = `int(md5(f"{user_id}:{dedup_key}".encode()).hexdigest()[:16], 16)` — stable, per-user unique (two users' identical facts → distinct points).
- `_user_filter(tenant_id, user_id)` = `{"must": [{"key":"tenant_id","match":{"value":str(tenant_id)}}, {"key":"user_id","match":{"value":str(user_id)}}]}` — defense-in-depth (collection is already per-tenant; the user_id key enforces per-user isolation inside it).
- Neutrality: imports ONLY `EmbeddingClient` (ABC) + `QdrantVectorStore` + `QdrantNamespaceStrategy` — no provider SDK (AP-2/約束 3 clean; `check_llm_sdk_leak` green).

### 3.2 UserLayer semantic branch (US-2) — `memory/layers/user_layer.py`

- `__init__(..., vector_index: "MemoryVectorIndex | None" = None)` — additive keyword, default None ⇒ byte-identical when absent.
- `read()`:
  - **semantic-only** (`time_scales == ("semantic",)`): `if self._vector_index is None: return []` (current stub preserved); else fetch the user's rows (wildcard, the existing empty-query path) → `await self._vector_index.search(...)` → return hints. Fail-soft: `except Exception: return []`.
  - **mixed** (`"semantic" in time_scales` alongside short/long): run the existing ILIKE keyword query for short/long, THEN if `vector_index` present union the vector hits, dedup by `content` (keep the higher relevance), cap `max_hints`. Vector hits carry cosine as `relevance_score` so `MemoryRetrieval.search`'s `relevance*confidence` sort ranks them naturally.
  - vector path is entirely `try/except`-guarded → any embed/Qdrant failure degrades to the keyword/stub result (never raises).
- The 3 write paths (agent `memory_write` / 57.149 auto-extract / 57.148 nudge) are **untouched** — recall reads the same `memory_user` rows they already write.

### 3.3 Opt-in singleton + count filter + factory wiring (US-3) — 3 files

- `api/v1/chat/memory_vector_index.py`: `get_memory_vector_index() -> MemoryVectorIndex | None` memoized (mirror `knowledge_index.py:55-107`): `None` when `not settings.memory_vector_enabled` / `not config.is_embedding_configured()` / `not settings.qdrant_url`; lazy heavy imports (`AzureOpenAIEmbeddingClient`, `QdrantVectorStore`) only when flag on; `reset_memory_vector_index()` test hook.
- `infrastructure/vector/qdrant_client.py`: `async count(self, name, payload_filter: dict | None = None) -> int` — mirror `search`'s `models.Filter.model_validate(payload_filter) if payload_filter else None`, pass to the SDK count call; existing no-arg callers unaffected (default None).
- `core/config/__init__.py`: `memory_vector_enabled: bool = False` (env `MEMORY_VECTOR_ENABLED`) — placed beside `knowledge_vector_enabled` (`:212-220`); reuses the existing `qdrant_url` + embedding config (no new infra config).
- `api/v1/chat/_category_factories.py`: in `make_chat_memory_deps`, call `get_memory_vector_index()` once and pass it into the `UserLayer(...)` construction (only the user layer this slice).

### 3.x What is explicitly NOT done

- L1 system + L2 tenant semantic layers, and session-summary semantic ranking (57.151) → CARRY-026 remaining slices.
- Semantic near-dup **write dedup** (extend 57.150) — this slice is recall-only; the write path is untouched.
- Incremental embed-on-write — this slice lazy-ingests-on-search; embed-on-write is a follow-on optimization.
- Populating the dormant `memory_user.vector_id` column — point ids derive from `dedup_key`; the column stays dormant (no migration).
- Hybrid keyword∪vector fusion reranking beyond the simple dedup-union in `UserLayer.read`.
- A chat-v2 Inspector surface / wire event for "semantic hit this turn" → Phase-58 AD.

### 3.y Validation (US-1..US-5)

Gates: mypy `src` 0/N (new files ARE CI-mypy-gated) · run_all 11/11 · pytest 3106+new · Vitest 922 (untouched) · mockup 51 (`diff` empty, untouched) · `npm run lint && npm run build` (NO `--silent`; FE untouched → no delta) · black/isort/flake8 clean · LLM-SDK-leak clean. Plus the §3.2/US-4 drive-through (MANDATORY — real chat-v2 + real Azure embeddings + real Qdrant).

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 1 | `backend/src/agent_harness/memory/vector_index.py` | NEW |
| 2 | `backend/src/api/v1/chat/memory_vector_index.py` | NEW |
| 3 | `backend/src/agent_harness/memory/layers/user_layer.py` | EDIT (ctor param + read semantic branch) |
| 4 | `backend/src/infrastructure/vector/qdrant_client.py` | EDIT (`count` gains `payload_filter=None`) |
| 5 | `backend/src/core/config/__init__.py` | EDIT (`memory_vector_enabled` flag) |
| 6 | `backend/src/api/v1/chat/_category_factories.py` | EDIT (inject index into UserLayer) |
| 7 | `backend/tests/unit/agent_harness/memory/test_memory_vector_index.py` | NEW |
| 8 | `backend/tests/unit/api/v1/chat/test_memory_vector_index_singleton.py` | NEW |
| 9 | `backend/tests/unit/agent_harness/memory/test_user_layer.py` | EDIT (semantic stub → parametrized off/on) |
| 10 | `backend/tests/integration/memory/test_memory_vector_recall.py` | NEW (fake embedder + spy/fake Qdrant end-to-end through UserLayer.read) |
| — | `infrastructure/db/migrations/**` | **UNTOUCHED** (no column; dedup_key point ids) |
| — | `memory/retrieval.py` | **UNTOUCHED** (merge already carries relevance_score) |
| — | `memory/layers/{system,tenant,role,session}_layer.py` | **UNTOUCHED** (later slices) |
| — | `memory/layers/user_layer.py` write path (57.150) | **UNTOUCHED** (lazy-ingest-on-read) |
| — | frontend / wire schema (24→) / codegen | **UNTOUCHED** |

## 5. Acceptance Criteria

1. `MemoryVectorIndex.search` returns cosine-ranked hits for a per-tenant+user collection, idempotent per-user (count guard), stable `dedup_key`-derived point ids — proven by unit tests (fake embedder + spy Qdrant assert: embed batched at ≤16, upsert once when count≠len, search filtered by tenant+user).
2. `UserLayer.read` semantic branch: with index=None → `[]` (byte-identical stub); with index → vector hits carrying cosine `relevance_score`; mixed request unions keyword+vector deduped; any embed/Qdrant error → fail-soft to keyword/stub (unit test forces an exception).
3. `MEMORY_VECTOR_ENABLED=false` (default) → `get_memory_vector_index()` is `None`, UserLayer built without an index, zero embedding/Qdrant import cost, platform byte-identical to 57.154 (singleton unit test).
4. `QdrantVectorStore.count(name, payload_filter=…)` filters by payload; existing no-arg callers unaffected (unit test both arities).
5. **Drive-through PASS (MANDATORY, real UI + backend + real Azure embeddings + real Qdrant)** — with the flag ON, a chat-v2 user states a personal fact, then a NEW query with NO keyword overlap semantically recalls it (Inspector shows the memory injected; grounded answer); per-user isolation holds (a second user does not retrieve it). Screenshot + observed-vs-intended in progress.md. (NOT gate-only.)
6. `CARRY-026 Slice 1` marked shipped (L4 user); CHANGE-122 + design note 58 (8-point gate); calibration `memory-vector-recall-spike` 0.60 recorded; navigators + next-phase-candidates updated (CARRY-026 remaining L1/L2/session + follow-ons logged).

## 6. Deliverables

- [ ] US-1 `MemoryVectorIndex` + `MemoryVectorHit` (mirror KnowledgeVectorIndex; no new ABC/infra)
- [ ] US-2 `UserLayer.read` semantic branch (vector when injected, `[]` stub otherwise, fail-soft) + additive ctor param
- [ ] US-3 `MEMORY_VECTOR_ENABLED` flag + memoized singleton + `QdrantVectorStore.count` filter + factory injection
- [ ] US-4 drive-through PASS (real chat-v2 + real Azure embeddings + real Qdrant; semantic recall + per-user isolation)
- [ ] US-5 CHANGE-122 + design note 58 + calibration + navigators + CARRY-026 Slice-1 status

## 7. Workload Calibration

- Scope class **NEW `memory-vector-recall-spike` 0.60** (1st data point). Anchored to `knowledge-embedding-vector-spike` 0.60 (57.146 — same new-index + Qdrant + EmbeddingClient-ABC-reuse shape) and the `memory-*` siblings 0.60 (57.148/150/151/152/154). Set 0.60 not the pure-wiring 0.55 (`knowledge-per-tenant-isolation-spike` 57.147) because a NEW `MemoryVectorIndex` + the layer read-branch design + the count-filter extension are real design-decision content beyond pure wiring; set 0.60 not a tiny-code 0.85 because the real-code core (new index ~130 lines + layer branch + singleton + tests ≥~3.5 hr) holds the spike multiplier per the 57.137 lesson. If the 1st data point lands > 1.20 (the real-Azure-embeddings + real-Qdrant drive-through is the variance driver, per the 57.146 note), re-point toward 0.70.
- **Agent-delegated: no** (parent-direct, matching all memory-* siblings). `agent_factor 1.0` → 3-segment form.
- Bottom-up est ~12.5 hr (index ~2.5 · layer branch ~1.5 · singleton+config+count+factory ~2 · unit tests ~2.5 · integration ~1 · Day-0 ~0.5 · drive-through ~1.5 · docs ~1) → class-calibrated commit ~7.5 hr (mult 0.60). Day-4 retro Q2 verifies.

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| **Real Azure embeddings 429** (57.146 Day-3 finding) | Reuse the proven `_EMBED_BATCH=16` batching + the SDK's residual-429 retry; per-user row counts are small so batching rarely triggers. |
| **Risk Class E** — stale `--reload` / orphan spawn-worker serves old code so the flag/singleton looks un-wired | Clean restart before drive-through: kill ALL uvicorn reloaders + `multiprocessing.spawn` workers on :8000, confirm sole fresh PID + startup log; the singleton is built at startup from `.env` so set `MEMORY_VECTOR_ENABLED=true` BEFORE restart (per §Common Risk Classes E). |
| **Gate-green ≠ usable** (57.145 multi-word 0-hit; the drive-through catches what units miss) | US-4 drive-through is MANDATORY with a genuinely keyword-disjoint query; do NOT mark done on unit-green alone. |
| **Per-user isolation leak** in a per-tenant collection | Point id incorporates `user_id`; `payload_filter` filters both `tenant_id` AND `user_id`; drive-through verifies a 2nd user does not retrieve the 1st user's fact (mirrors 57.147 bidirectional isolation check). |
| **Count-idempotency wrong for multi-user tenant** (a plain `count(collection)` counts all users) | `count` gains a `payload_filter` so the per-user count is correct; unit test asserts re-ingest fires only when the user's own count changes. |
| **mypy on new src files** (unlike scripts/, src IS CI-gated) | Keep `MemoryVectorHit` a typed frozen dataclass; type the row/hit lists; run `mypy src --strict` in the Day-2 full gate. |
| **Fail-soft masks a real mis-wire** (silent `except` could hide a genuine bug) | The `except` logs a warning (like `knowledge_index.py`); the drive-through confirms the HAPPY path actually returns vector hits, not a silently-swallowed empty. |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- L1 system + L2 tenant semantic layers → `AD-Memory-Semantic-Axis-System-Tenant-Layers` (CARRY-026 remaining).
- Session-summary semantic ranking (57.151 recency-only) → `AD-Memory-Session-Summary-Semantic-Rank` (CARRY-026, noted in `54-...-design.md:53`).
- Semantic near-dup write dedup (extend 57.150 exact-normalized) → `AD-Memory-Semantic-NearDup-Dedup`.
- Incremental embed-on-write (avoid lazy full re-embed on count change) → `AD-Memory-Vector-Incremental-Write`.
- Per-tenant `MEMORY_VECTOR_ENABLED` override (C3 config-tiering seam) → `AD-Memory-Vector-PerTenant-Phase58`.
- chat-v2 Inspector "semantic hit this turn" surface + wire event → `AD-Memory-Vector-Inspector-Phase58`.
- async/queue formation (CARRY-027) + SessionLayer→DB (CARRY-029) — unrelated memory carryovers, not this slice.
