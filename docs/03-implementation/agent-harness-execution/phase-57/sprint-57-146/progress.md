# Sprint 57.146 Progress — knowledge Slice 2: section-aware snippets + embedding/Qdrant vector search

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-146-plan.md) · [Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-146-checklist.md)

---

## Day 0 — 2026-06-27 — Plan-vs-Repo Verify (三-prong) + Branch

### Prong 1 — path verify (against `main` HEAD `03f2b79d`)

- NEW files FREE ✅: `adapters/_base/embedding_client.py` · `adapters/azure_openai/embeddings.py` · `adapters/_testing/embedding.py` · `infrastructure/vector/qdrant_client.py` · `business_domain/knowledge/{chunking,vector_index}.py` · the 5 new test files (none exist).
- EDIT files PRESENT ✅: `adapters/_base/__init__.py` · `adapters/azure_openai/config.py` · `business_domain/knowledge/{connector,tools,__init__}.py` · `business_domain/_register_all.py` · `api/v1/chat/handler.py` · `api/main.py` · `core/config/__init__.py` · `requirements.txt`.
- **D-change-num** ✅: highest CHANGE = 112 → **CHANGE-113 free**; highest design note = `49-*` → **`50-*` free**.

### Prong 2 — content verify (drift findings)

| ID | Finding (real code) | Implication / §Risks shift |
|----|---------------------|----------------------------|
| **D-config-shape** | `AzureOpenAIConfig` (`adapters/azure_openai/config.py:34`) is a `BaseSettings` with `env_prefix="AZURE_OPENAI_"` + shared `endpoint`/`api_key`/`api_version`/`deployment_name`/`is_configured()`. core `Settings` (`core/config/__init__.py:41`) already holds `knowledge_docs_root` (57.145). | **DROP planned `embedding_config.py` (file #3)** — add `embedding_deployment: str` field (env `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` auto-maps via prefix) + `is_embedding_configured()` to the EXISTING `AzureOpenAIConfig` (reuses shared connection fields). core `Settings` gets only `knowledge_vector_enabled: bool = False` + `qdrant_url: str = "http://localhost:6333"`. Scope −1 file. |
| **D-composition** | `build_real_llm_handler` (`handler.py:284`) threads 57.145 `knowledge_root = get_settings().knowledge_docs_root or None` (`:497`) into `make_default_executor(..., knowledge_root=...)` (`:499-510`). `_get_shared_sandbox` (`_register_all.py:107`) is the module-singleton pattern. `business_domain` importing a concrete Azure adapter would couple the domain to a provider (category-boundary smell). | **ADD `api/v1/chat/knowledge_index.py` (+1 file)** — a `get_knowledge_vector_index()` module singleton in the API composition layer that builds `AzureOpenAIEmbeddingClient` + `QdrantVectorStore` + `LocalDocsConnector` + `KnowledgeVectorIndex` (returns None when flag off / unconfigured). Imported by handler.py (passes into `make_default_executor(knowledge_vector_index=...)`) + main.py (startup ingest). `business_domain` stays adapter-agnostic (sees only the `EmbeddingClient` ABC + its own `KnowledgeVectorIndex` type). Net file count vs plan: −1 (embedding_config) +1 (knowledge_index) = unchanged. |
| **D-ingest-trigger** | `api/main.py` `_lifespan` (`:403`) runs `load_dotenv()` first (`:409`) then a sequence of fail-soft `_wire_*`/`_start_*` blocks (`except Exception → log+continue`, e.g. `_wire_pricing_loader :136`). | Startup ingest = a NEW fail-soft block in `_lifespan` (after the existing wires) calling `get_knowledge_vector_index()`; if not None → `await index.ingest()` in try/except. Flag off → singleton None → skip → ZERO added startup cost. `load_dotenv()` already populates OS env before the embedding config reads it. |
| **D-embedding-test-double-home** | `adapters/_testing/mock_clients.py` holds `MockChatClient` (the ChatClient ABC test double; AP-10 shared-ABC). | `DeterministicEmbeddingClient` → NEW `adapters/_testing/embedding.py` (sibling). Azure adapter unit test mocks `client.embeddings.create` (no live call), mirroring the MockChatClient/contract pattern. |
| **D-qdrant-dep** | `qdrant-client` absent from `requirements.txt` (line 9 notes it was deferred). | Add `qdrant-client>=1.7,<2.0`; `QdrantVectorStore` uses sync `QdrantClient` wrapped in `asyncio.to_thread` (mirrors the docker-SDK `to_thread` pattern; avoids async-SDK version quirks + cleaner mypy). |
| **D-collection-name** | Only Qdrant code is the unused `QdrantNamespaceStrategy`. | Fixed shared collection `knowledge_local_docs` — no collision. Per-tenant `"kb"` namespacing deferred to Slice 3. |
| **D-toolcall-render** | 57.145 D-fe-toolcall-render already verified chat-v2 renders the tool result (name + result text). | Carry forward — section snippets + source paths visible WITHOUT a new wire event. wire stays 26. |

### Prong 3 — schema verify

- **N/A** ✅ — NO new DB table / migration / ORM column. Qdrant holds vectors; `.md` files are the source of truth; the `MemoryTenant/User.vector_id` columns are Cat 3, not knowledge.

### D-baselines (from 57.145 closeout; re-verify Day-2 full gate)

- pytest 2947 + 6 skip · wire 26 · Vitest 922 · mockup 51 · mypy 0/385 · run_all 11/11.

### Go/no-go

- All drift is scope-neutral refinement (net file count unchanged: −embedding_config +knowledge_index). Scope shift **≈ 0%** → **GO**.
- Plan §3.0 / §4 will be reflected in code as: embedding_config dropped, `api/v1/chat/knowledge_index.py` added, `make_default_executor` gains `knowledge_vector_index` param. (Findings preserved here per AP-2; plan §Risks unchanged in substance.)

### Branch

- `feature/sprint-57-146-knowledge-embedding-vector` from `main` `03f2b79d`.

---

## Day 1 — 2026-06-27 — Chunking + snippet (US-1) + EmbeddingClient ABC/adapter/double (US-2)

### Done

- **`chunking.py`** — `split_sections(text) -> list[Section]` (`##` split; preamble = H1 or `(intro)`; ### stays inside parent ##; `_MAX_SECTION_CHARS=1500` trim). `Section(heading_path, body incl. heading line, start_line)`.
- **`connector.py`** — `_section_snippet()` reuses `split_sections`: a keyword hit now returns the WHOLE `##`-section body (heading + paragraph) instead of matched-line ±1. **R2 over-search structurally fixed on the keyword path.** Falls back to the old line-window if no section covers the match. `KnowledgeHit` shape unchanged; 57.145 OR-token behavior preserved.
- **`adapters/_base/embedding_client.py`** — `EmbeddingClient` ABC (`async embed(texts) -> list[list[float]]` + `model_name()`); minimal (dim derived at ingest); exported from `_base/__init__`.
- **`adapters/azure_openai/embeddings.py`** — `AzureOpenAIEmbeddingClient` (lazy `AsyncAzureOpenAI`, `embeddings.create(model=embedding_deployment, input=texts)`, re-sort by `.index`, `AzureOpenAIErrorMapper`). `config.py` += `embedding_deployment` field + `is_embedding_configured()` (D-config-shape: DROPPED separate `embedding_config.py`).
- **`adapters/_testing/embedding.py`** — `DeterministicEmbeddingClient` (sha256 → fixed-dim L2-unit vector; offline; for unit tests).
- **Tests**: `test_chunking.py` (8) · `test_deterministic_embedding.py` (6) · `test_embeddings.py` (5, SDK mocked) · `test_knowledge_connector.py` +1 section-snippet test.

### Gate (Day 1 scope)

- `pytest` (4 files) → **30 passed / 1 skipped** (symlink test, Windows no-priv).
- `mypy` (6 src files) → **clean**.
- `black` / `isort` / `flake8` (11 files) → **clean** (fixed 1 E501 in chunking Purpose docstring).
- Embedding SDK (`openai`) confined to `adapters/azure_openai/embeddings.py` only → llm_sdk_leak full-run deferred to Day 2 full gate.

### Notes

- est ~5 hr (chunking + snippet + ABC + Azure adapter + double + tests) — actual ~on-budget.
- Azure embedding **deployment name** (`AZURE_OPENAI_EMBEDDING_DEPLOYMENT`) needed at Day 3 drive-through only — Day 1-2 use the deterministic double + mocked SDK (no live Azure).

---

## Day 2 — 2026-06-27 — Qdrant wrapper (US-3) + vector index + opt-in wiring (US-4) + full gate

### Done

- **`infrastructure/vector/qdrant_client.py`** — `QdrantVectorStore` (lazy `QdrantClient`, sync calls via `asyncio.to_thread`): `ensure_collection` / `recreate_collection` / `count` / `upsert` / `search`. Uses the `query_points` API (qdrant-client 1.17 removed `search`). `VectorHit(payload, score)`. Closes CARRY-026 for the KB use case.
- **`business_domain/knowledge/vector_index.py`** — `KnowledgeVectorIndex(embed, store, connector)`: `ingest()` (list_files → split_sections → batch embed → recreate_collection(dim) → upsert; idempotent via count==expected) + `search()` (embed query → Qdrant cosine top-k → `KnowledgeHit`).
- **`tools.py`** — `make_knowledge_search_handler(connector, vector_index=None)` + `register_knowledge_tools(..., vector_index=None)`: vector-primary, **fail-soft to keyword** on any embedding/Qdrant error. None → 57.145 byte-identical.
- **`_register_all.py`** — `make_default_executor(knowledge_vector_index=None)` threaded into the 57.145 `knowledge_root` branch.
- **`api/v1/chat/knowledge_index.py`** (NEW) — `get_knowledge_vector_index()` process-wide singleton (api composition layer; business_domain stays adapter-agnostic). Lazy adapter/Qdrant imports → **zero cost when flag off**. `reset_*()` test hook.
- **`handler.py`** — `build_real_llm_handler` threads `knowledge_vector_index=get_knowledge_vector_index()` into the main executor.
- **`api/main.py`** — `_lifespan` `_ingest_knowledge()` fail-soft startup ingest (None → skip).
- **`core/config`** — `knowledge_vector_enabled` (False) + `qdrant_url` (`http://localhost:6333`). **`requirements.txt`** += `qdrant-client>=1.12,<2.0`.
- **Tests**: `test_qdrant_client.py` (5, QdrantClient mocked) · `test_vector_index.py` (5, deterministic double + fake store; exact-section → cosine 1.0 ranks first) · `test_knowledge_tools.py` +2 (vector path + fail-soft fallback).

### Day-2 full gate (GREEN)

- mypy `src` → **Success: 392 source files** (baseline 385 + 7 new).
- `python scripts/lint/run_all.py` → **11/11 green** (incl. `check_llm_sdk_leak` — embedding SDK confined to `adapters/azure_openai/embeddings.py`).
- backend `pytest` → **2979 passed / 6 skipped** (baseline 2947 + 32 new; nothing broke).
- `black` / `isort` / `flake8` → clean (fixed 1 config MHist E501 + black wrapped 2 test long-lines).
- wire 26 (`check_event_schema_sync` green) · Vitest 922 / mockup 51 (FE UNTOUCHED — not re-run, 0 FE diff).

### D-config-shape applied

- DROPPED planned `embedding_config.py`; added `embedding_deployment` field + `is_embedding_configured()` to `AzureOpenAIConfig`. ADDED `api/v1/chat/knowledge_index.py` (net file count vs plan: unchanged).

### Notes

- est ~9.5 hr (Qdrant wrapper + index + wiring + config + startup ingest + tests) — actual ~on-budget.
- **All backend code done + gate-green. Day 3 (drive-through) is the remaining gate — it REQUIRES the Azure embedding deployment name + a running Qdrant container + a clean restart.**

---

## Day 3 — 2026-06-27 — Drive-through (US-5) — real UI + real Azure embedding + real Qdrant

### Day-3 findings (BOTH fixed — the value of the drive-through over gate-green)

- **D-env-name mismatch** — the user's root `.env` uses `AZURE_OPENAI_DEPLOYMENT_EMBEDDING` (= `text-embedding-3-large`), but the code field `embedding_deployment` mapped to `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`. The user's name actually matches the existing `AZURE_OPENAI_DEPLOYMENT_NAME` convention better → **renamed field `embedding_deployment` → `deployment_embedding`** (config + adapter + knowledge_index log + tests). Caught a latent `knowledge_index.py:93` `config.embedding_deployment` reference that would have been a runtime AttributeError. Re-verified: mypy clean + embedding tests 5 passed.
- **429 Too Many Requests on ingest** (the headline Day-3 bug) — the startup ingest embedded ALL sections in ONE Azure call → 429 (exceeds the deployment TPM), SDK stuck in 60s retries, startup blocked. Also discovered `list_files()` recurses → the DEFAULT planning-docs root pulls **418 files / 3818 sections** (~1.1M tokens) — far too much to embed upfront. **Fixes**: (1) `ingest()` now embeds in `_EMBED_BATCH=16`-section batches (resolves 429); (2) drive-through points `KNOWLEDGE_DOCS_ROOT` at a **bounded real folder** `docs/rules-on-demand` (12 docs / 129 sections) — which IS the realistic production pattern (a tenant points at a curated KB folder, not 418 nested sprint files). Both gate-green tests passed; the 429 only surfaced on the real Azure connection.

### Clean restart (Risk Class E)

- Killed stale uvicorn reloader (56132, 19:01) + **orphan spawn-worker** (48584, 15:12 — ppid pointing to a reused PID, the 57.97 trap); confirmed :8000 FREE + no residual python; node (frontend@3007 + claude code) untouched.
- Relaunched single-process (no `--reload`) uvicorn with `KNOWLEDGE_VECTOR_ENABLED=1` + `KNOWLEDGE_DOCS_ROOT=docs/rules-on-demand`; `load_dotenv()` loaded root `.env` (Azure incl. `AZURE_OPENAI_DEPLOYMENT_EMBEDDING`).
- Startup log: `knowledge vector index built (model=text-embedding-3-large)` → `knowledge vector index ready (129 sections)` (~21s, 8 batches, NO 429) → `Application startup complete`.
- Qdrant `knowledge_local_docs`: status **green, points_count 129, vector_size 3072** (= text-embedding-3-large dim → confirms real large embeddings), distance Cosine. `/health` 401 = ready.

### Pre-UI programmatic sanity (real Azure embed → live Qdrant)

- "swap AI providers without rewriting code" → top hits `adapters-layer.md` / `llm-provider-neutrality.md` (no literal "neutrality"/"adapter" in query → pure semantic).
- "where should a brand-new code file live" → top hit `category-boundaries.md`.

### THE drive-through (real chat-v2 + real Azure gpt-5.2 + real embedding + real Qdrant)

- dev-login dan@acme.com·admin / acme-prod, mode `real_llm`. trace_id `f5b394db524b4d4d89b6a2c1203a8e11`.
- Query: *"According to our internal engineering docs, how do we keep the platform able to switch AI providers later without rewriting code? Please cite the source doc."*
- **AP-4 per-control walk (all PASS)**:
  - agent CALLS `knowledge_search` (agent expanded the query to a rich semantic phrase) — Trace span `agent_loop.tool.knowledge_search` TOOL_EXEC **duration 1750ms** (real embed + Qdrant, not echo/training).
  - tool result = REAL section bodies from `adapters-layer.md` (0.568/0.505/0.474/0.472) + `llm-provider-neutrality.md` (0.468) — cross-checked against the real files (Chinese text + ASCII architecture diagram + code SOP). Query had NO literal "adapter"/"neutrality" → **semantic retrieval proven**; section-aware snippets (`## 核心概念\n...`) confirm Slice-1 chunking.
  - agent's answer is grounded + **cites each source path with section name**: "Source: `adapters-layer.md` (核心概念)" / "(新 Provider 上架 SOP Step 2)" / "Source: `llm-provider-neutrality.md` (Multi-Provider Routing)". Each claim maps to a specific retrieved snippet — not fabricated.
  - rendered with NO DEMO label (data is real).
- BONUS: agent used `write_todos` (57.140 task primitive) to plan the research ("Search internal engineering docs → Extract patterns + citations → Draft grounded answer") — the whole research golden-path is live.
- Screenshot: `sprint-57-146-drivethrough-semantic-knowledge.png` (playwright output dir; not committed — large binary, per 57.145 convention).

### Notes

- est drive-through ~1.5 hr → actual heavier (~3 hr) ∵ the 2 real-connection bugs (env-name rename + 429 batching) — the *normal* cost of a real-connection spike (the drive-through is the point; a vector path you can't drive-through is a Potemkin).

---
