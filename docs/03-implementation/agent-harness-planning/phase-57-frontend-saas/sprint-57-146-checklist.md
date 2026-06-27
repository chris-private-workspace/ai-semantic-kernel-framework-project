# Sprint 57.146 — Checklist (knowledge Slice 2: section-aware snippets + embedding/Qdrant vector search)

[Plan](./sprint-57-146-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch

### 0.1 Three-prong Day-0 verify (against `main` HEAD `03f2b79d`)
- [x] **Prong 1 — path verify**: NEW files free ✅; EDIT files present ✅ (progress.md Day-0 Prong 1)
- [x] **Prong 2 — content verify** (drift → progress.md):
  - [x] **D-config-shape** — RESOLVED: embedding_deployment → field on EXISTING `AzureOpenAIConfig` + `is_embedding_configured()` (DROP `embedding_config.py`); core `Settings` += `knowledge_vector_enabled` + `qdrant_url`
  - [x] **D-embedding-test-double-home** — RESOLVED: `adapters/_testing/embedding.py` (sibling to `mock_clients.py`); Azure adapter test mocks `embeddings.create`
  - [x] **D-qdrant-dep** — RESOLVED: `qdrant-client` absent → add `>=1.7,<2.0`; sync `QdrantClient` + `asyncio.to_thread`
  - [x] **D-ingest-trigger** — RESOLVED: fail-soft block in `_lifespan` (`load_dotenv()` runs first); flag-OFF → zero cost
  - [x] **D-composition (was D-handler-thread)** — RESOLVED: singleton in NEW `api/v1/chat/knowledge_index.py` (api layer; keeps business_domain adapter-agnostic); +1 file nets the dropped embedding_config
  - [x] **D-collection-name** — RESOLVED: `knowledge_local_docs`, no collision; per-tenant `"kb"` deferred Slice 3
  - [x] **D-toolcall-render** — carry forward 57.145 (chat-v2 renders tool result; no new wire event)
- [x] **Prong 3 — schema verify**: N/A ✅ (NO DB table / migration / ORM column)
- [x] **D-baselines** — pytest 2947+6skip · wire 26 · Vitest 922 · mockup 51 · mypy 0/385 · run_all 11/11 (re-verify Day-2 gate)
- [x] **D-change-num** — `CHANGE-113` free; design note `50-*` free ✅
- [x] **Catalog drift** — progress.md Day-0 table ✅
- [x] **Go/no-go** — scope shift ≈ 0% (net file count unchanged) → **GO**

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-146-knowledge-embedding-vector` (from `main` `03f2b79d`) ✅ HEAD 03f2b79d

---

## Day 1 — Chunking + snippet (US-1) + EmbeddingClient ABC/adapter/double (US-2)

### 1.1 `split_sections` chunker — `business_domain/knowledge/chunking.py`
- [x] **`split_sections(text) -> list[Section]` + `Section(heading_path, body, start_line)`** ✅
  - DoD: `##` split; pre-first-`##` preamble = intro section (heading_path = H1 or `(intro)`); no-`##` doc = 1 whole-doc section; body trimmed to `_MAX_SECTION_CHARS=1500`; ### stays inside parent ##
  - Verify: `pytest tests/unit/business_domain/knowledge/test_chunking.py -q` → 8 passed

### 1.2 `test_chunking.py`
- [x] **chunker unit tests (8)** ✅ — `##` split · preamble H1/intro · ### stays inside ## · empty doc → [] · no-heading → 1 section · start_line · trim · frozen

### 1.3 Section-aware snippet on keyword path — `connector.py`
- [x] **keyword snippet returns the matched section body (reuse `split_sections`)** ✅
  - DoD: a token match returns the whole `##`-section (heading + paragraph), not matched-line ±1; `KnowledgeHit` shape unchanged; R2 over-search structurally fixed; OR-token behavior preserved; existing 57.145 tests still green
  - Verify: `pytest tests/unit/business_domain/knowledge/test_knowledge_connector.py -q` → 11 passed/1 skip (new section-snippet test)

### 1.4 `EmbeddingClient` ABC + export — `adapters/_base/embedding_client.py` + `__init__.py`
- [x] **`EmbeddingClient(ABC)`: `async embed(texts)->list[list[float]]` + `model_name()`; exported from `_base/__init__`** ✅ (minimal ABC, no SDK import, `__all__` += EmbeddingClient)

### 1.5 Azure embedding adapter + config + test double — `adapters/azure_openai/embeddings.py` + `adapters/_testing/embedding.py`
- [x] **`AzureOpenAIEmbeddingClient` + `AzureOpenAIConfig.embedding_deployment`/`is_embedding_configured()` + `DeterministicEmbeddingClient`** ✅
  - DoD: Azure impl lazy `AsyncAzureOpenAI` + `embeddings.create(model=embedding_deployment, input=texts)` re-sorted by `.index`; config field `embedding_deployment` (env auto-maps) + `is_embedding_configured()` (DROPPED separate `embedding_config.py` per D-config-shape); deterministic double = sha256→fixed-dim L2-unit vector
  - Verify: `pytest tests/unit/adapters/azure_openai/test_embeddings.py tests/unit/adapters/_testing/test_deterministic_embedding.py -q` → 5 + 6 passed (SDK mocked)

### 1.x Partial gate
- [x] mypy clean (6 src files) · `black/isort/flake8` clean (11 files; fixed 1 E501 in chunking docstring) · embedding SDK confined to `adapters/azure_openai/embeddings.py` (llm_sdk_leak full-run Day 2)

---

## Day 2 — Qdrant wrapper (US-3) + vector index + opt-in wiring (US-4) + full gate

### 2.1 `QdrantVectorStore` wrapper — `infrastructure/vector/qdrant_client.py`
- [x] **`QdrantVectorStore(url)`: `ensure_collection` / `recreate_collection` / `count` / `upsert` / `search(payload_filter=None)`** ✅
  - DoD: lazy `QdrantClient` + sync calls via `asyncio.to_thread`; cosine collection; idempotent ensure; `query_points` API (qdrant-client 1.17, `search` removed); payload `{source,snippet}`; `VectorHit(payload,score)`; payload_filter passthrough (Slice-3, default None)
  - Verify: `pytest tests/unit/infrastructure/vector/test_qdrant_client.py -q` → 5 passed (QdrantClient mocked)

### 2.2 `KnowledgeVectorIndex` — `business_domain/knowledge/vector_index.py`
- [x] **`KnowledgeVectorIndex(embed, store, connector, collection)`: `async ingest()` + `async search(query, top_k)`** ✅
  - DoD: ingest = list_files→split_sections→batch embed→`recreate_collection(dim from len(vec[0]))`→upsert; idempotent (skip if count==expected); search = embed query→store.search→`KnowledgeHit(source, snippet=body, score=cosine)`
  - Verify: `pytest tests/unit/business_domain/knowledge/test_vector_index.py -q` → 5 passed (deterministic double + fake store; exact-section → cosine 1.0 ranks first)

### 2.3 Tool vector-primary + keyword fallback — `tools.py`
- [x] **`register_knowledge_tools(..., vector_index=None)`; handler vector-first, fail-soft keyword** ✅
  - DoD: `vector_index` present → `await vector_index.search`; on embedding/Qdrant error → `connector.search` keyword; None → 57.145 byte-identical; JSON shape unchanged
  - Verify: `pytest tests/unit/business_domain/knowledge/test_knowledge_tools.py -q` → 9 passed (vector path + fail-soft fallback)

### 2.4 Opt-in wiring + config + startup ingest — `_register_all.py` + `knowledge_index.py` + `handler.py` + `api/main.py` + `core/config`
- [x] **`make_default_executor(knowledge_vector_index=None)` thread + `api/v1/chat/knowledge_index.py` singleton + flag-gated startup ingest + 3 settings** ✅
  - DoD: `_register_all` passes `vector_index`; NEW `knowledge_index.py` builds process-wide index ONLY when `knowledge_vector_enabled` + `is_embedding_configured()` + qdrant_url (lazy adapter/Qdrant import → zero cost when off); `handler.py` threads it; `main.py` `_lifespan` `_ingest_knowledge` (fail-soft); `config` += `knowledge_vector_enabled`/`qdrant_url`; `requirements.txt` += `qdrant-client>=1.12,<2.0`
  - Verify: opt-in covered by tools register tests + `get_knowledge_vector_index()` flag-off → None (keyword) by construction

### 2.x Full gate
- [x] mypy `src` **0/392** (+7 files) · run_all **11/11** · backend pytest **2979 passed / 6 skip** (+32) · Vitest 922 (UNCHANGED — FE untouched) · mockup 51 · wire 26 (`check_event_schema_sync` green) · black/isort/flake8 clean · **LLM-SDK-leak clean** (embedding SDK only in `adapters/azure_openai/embeddings.py`)

---

## Day 3 — Drive-through (US-5) — real UI + real Azure embedding + real Qdrant

### 3.1 Clean restart (Risk Class E) + ingest
- [x] User `.env` has `AZURE_OPENAI_DEPLOYMENT_EMBEDDING=text-embedding-3-large` (env-name renamed in code to match — D-env-name); killed stale uvicorn reloader 56132 + **orphan spawn-worker 48584** (57.97 trap); :8000 FREE; node untouched; relaunched single-process with `KNOWLEDGE_VECTOR_ENABLED=1` + `KNOWLEDGE_DOCS_ROOT=docs/rules-on-demand` (bounded real corpus = realistic prod pattern); Qdrant up (6333); startup log `index ready (129 sections)` + `startup complete`; `/health` 401=ready
- [x] **Day-3 bug fixes** (the drive-through's payoff): (1) env-name rename `embedding_deployment` → `deployment_embedding` (caught latent AttributeError); (2) **429 batching** — `ingest()` embeds in `_EMBED_BATCH=16` batches (all-in-one-call → 429 on real Azure TPM); default root recurses to 418 files/3818 sections → use bounded `docs/rules-on-demand` (129 sections)

### 3.2 Drive-through (MANDATORY — NOT gate-only) ✅ PASS
- [x] Real UI chat-v2 (`localhost:3007`, dev-login dan@acme.com·admin / acme-prod) + real Azure gpt-5.2 (`real_llm`) + real `text-embedding-3-large` + real Qdrant; trace_id `f5b394db…`
- [x] SEMANTIC query (no literal "adapter"/"neutrality"): "how do we keep the platform able to switch AI providers later without rewriting code? cite the source doc" → agent calls `knowledge_search`
- [x] **THE proof (real UI, per-control AP-4 walk)** — all PASS:
  - [x] agent CALLS `knowledge_search` — Trace span `agent_loop.tool.knowledge_search` TOOL_EXEC **1750ms** (real embed+Qdrant)
  - [x] vector retrieval returns RIGHT sections by similarity — `adapters-layer.md` (0.568/0.505/0.474/0.472) + `llm-provider-neutrality.md` (0.468); cross-checked real `.md` (Chinese + ASCII diagram + SOP code); keyword OR-token would have missed (no literal overlap)
  - [x] grounded answer **cites each real source path + section**: "`adapters-layer.md` (核心概念 / 新 Provider 上架 SOP Step 2)" + "`llm-provider-neutrality.md` (Multi-Provider Routing)"; each claim maps to a retrieved snippet (not fabricated)
  - [x] rendered NO DEMO label (real data); BONUS: agent planned via `write_todos` (57.140) — full research golden-path live
- [x] Screenshot `sprint-57-146-drivethrough-semantic-knowledge.png` + observed-vs-intended → progress.md Day 3
- [ ] 🚧 **Flag-OFF re-confirm deferred** — `KNOWLEDGE_VECTOR_ENABLED=0` → keyword (57.145) path is byte-identical by construction (`get_knowledge_vector_index()` returns None) + covered by unit tests; explicit UI re-confirm deferred to Day 4 final gate restart (low risk, off-path)

---

## Day 4 — CHANGE-113 + closeout (US-6)

### 4.1 CHANGE-113 + design note
- [x] **`CHANGE-113-knowledge-embedding-vector-slice2.md`** ✅ (gap + fix + drive-through PASS + Slice-2 closed + 2 Day-3 fixes)
- [x] **Spike design note** ✅ `50-knowledge-embedding-vector-design.md` — 8-point gate self-checked ~95% verified: decision matrices (embedding provider / vector store / chunk unit) + 9 verified invariants (file:line) + open-invariants table + rollback + 17.md cross-ref (EmbeddingClient = adapter-internal ABC, NO new contract row)

### 4.2 Closeout
- [x] retrospective.md Q1-Q7 + calibration (`knowledge-embedding-vector-spike` **0.60**, 1st pt ratio ~1.05-1.15 IN band upper half → KEEP)
- [x] Final gate sweep: mypy `src` **0/392** · run_all **11/11** · pytest **2980 passed / 6 skip** · black/isort/flake8 clean · LLM-SDK-leak green · Vitest 922 / wire 26 / mockup 51 (FE UNTOUCHED — not re-run, 0 FE diff)
- [x] Navigators: CLAUDE.md Current-Sprint + Last-Updated · MEMORY.md pointer + subfile `project_phase57_146_*` · next-phase-candidates (Slice-2 CLOSED + Slice-3/Ingest-Scale carryover) · sprint-workflow matrix (NEW `knowledge-embedding-vector-spike` 0.60 row)
- [x] Anti-pattern self-check (retro Q5): AP-2 (主流量-reachable, drive-through-proven) / AP-4 (NOT Potemkin — real 1750ms embed span + real Qdrant + cited answer) / AP-6 (ABC mandated by 約束 3, one provider + test double, opt-in not premature) / AP-11 (`deployment_embedding` matches `.env`); v2 lints 11/11
- [ ] **Commit** → ⏳ PR push + open → CI → merge: PENDING USER CONFIRMATION (push is outward-facing) → post-merge status flip after gh-verified MERGED
