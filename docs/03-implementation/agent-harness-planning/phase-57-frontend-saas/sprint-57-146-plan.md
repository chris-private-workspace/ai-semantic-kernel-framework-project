# Sprint 57.146 Plan — knowledge Slice 2: section-aware snippets + embedding/Qdrant vector search

**Summary**: Second slice of the knowledge-connector arc (`AD-Knowledge-Connector-First-Real-Source`). Upgrades the 57.145 keyword `LocalDocsConnector` from a Potemkin-risk first-match-line snippet to **section-aware retrieval** powered by **real Azure embeddings + Qdrant vector search**. Two coupled deliverables: (1) **section-aware chunking** — split each `.md` into `##`-heading sections so a hit returns the whole section body, directly closing the 57.145 R2 drive-through finding (the agent over-searched into `max_turns` because a snippet was one line, not enough to answer enumerate-style questions); (2) a **provider-neutral embedding path** — a new `EmbeddingClient` ABC (約束 3 forbids `import openai` in `business_domain/`) + an Azure `text-embedding-3-*` adapter + a Qdrant vector-store wrapper + an idempotent ingest, so `knowledge_search` retrieves by semantic similarity (finds the right section even when keywords don't match verbatim). Keyword stays as the runtime fallback (opt-in `KNOWLEDGE_VECTOR_ENABLED`; OFF → 57.145 byte-identical). **Drive-through MANDATORY**: prove, on real chat-v2 + real Azure embeddings + real Qdrant, that a semantic query keyword would miss returns the right section AND the agent answers in ONE search (no over-search). Spike sprint (new domain: first embedding/vector path) → design note required. NO DB migration, NO per-tenant KB isolation (single shared collection — RBAC is Slice 3).

**Status**: Approved-to-execute (user 2026-06-27 — direction "AD-Knowledge-Connector-First-Real-Source Slice 2/3" confirmed; scope "snippet 深度 + embedding/Qdrant" picked via AskUserQuestion; embedding provider = **Azure embedding** picked via AskUserQuestion)
**Branch**: `feature/sprint-57-146-knowledge-embedding-vector`
**Base**: `main` HEAD `03f2b79d` (Sprint 57.145 flip #345 merged — first real knowledge connector)
**Slice**: arc Slice 2 of 3 (1=first real connector ✅ 57.145 / **2=embedding+Qdrant semantic + section snippets ← this** / 3=RBAC + per-tenant isolation + citation). Closes the Slice-2 half of `AD-Knowledge-Connector-First-Real-Source`.
**Scope decisions**: (a) **embedding provider = Azure** (`text-embedding-3-small` via the existing `openai` SDK in `adapters/azure_openai/` — no new LLM dep; env `AZURE_OPENAI_DEPLOYMENT_EMBEDDING`) (b) **new `EmbeddingClient` ABC** in `adapters/_base/` (provider-neutral; `business_domain/` sees only the ABC — llm_sdk_leak-safe) + a deterministic test double (no Azure in CI) (c) **Qdrant client wrapper** in `infrastructure/vector/` (consumes the existing `qdrant-client` container; `qdrant-client` SDK added to requirements) — single shared `knowledge_local_docs` collection, NOT per-tenant (Slice 3) (d) **section-aware chunking** (`##`-heading split) shared by BOTH the keyword path (richer snippet, fixes R2) AND the embedding path (chunk = embed unit) (e) **vector = opt-in primary, keyword = fallback**: `KNOWLEDGE_VECTOR_ENABLED` (default False → 57.145 byte-identical); when True + embedding deployment + Qdrant reachable → vector search; runtime embedding/Qdrant error → fail-soft to keyword (f) **idempotent startup ingest** gated by the flag (mirror the `_get_shared_sandbox` process-wide singleton + lifespan pattern); fail-soft if Azure/Qdrant unreachable at startup (degrades to keyword) (g) **NO DB migration / NO new wire event / frontend UNTOUCHED** (existing tool-call rendering surfaces the search; the answer is the streamed report).

---

## 0. Background

### The gap (`AD-Knowledge-Connector-First-Real-Source` Slice 2)

57.145 shipped the first real connector (keyword search over real `.md`). Its drive-through PASSed but surfaced two real quality gaps the keyword path can't fix:

- **R2 over-search** — the snippet is the matched line ± 1 context line (`_SNIPPET_CONTEXT_LINES = 1`). For a "list everything about X" question the agent gets a heading + one line, not the section body, so it re-searches repeatedly and burns `max_turns=8` without a clean answer.
- **Keyword brittleness** — a real LLM sends semantic phrases; if the doc uses different words than the query, OR-token keyword match misses the relevant section entirely (it can only find what shares a literal token).

### Why it matters (the missing capability)

A knowledge-research golden path needs retrieval that (a) returns enough context to answer in one shot and (b) finds the right passage by meaning, not literal token overlap. Slice 2 is the quality upgrade that makes the connector usable for real research questions, not just keyword lookups. It is also the platform's **first real embedding + vector path** — the `EmbeddingClient` ABC + Qdrant wrapper unblock the long-stubbed Cat 3 memory semantic axis later (CARRY-026), though this sprint scopes only the knowledge KB.

### Root cause (recon code read, file:line; ALL re-verified §checklist 0.1)

| Layer | Reality (on `main` HEAD `03f2b79d`) | Anchor |
|-------|-------------------------------------|--------|
| Snippet depth | matched line ± 1 line, max 400 chars — no section body | `business_domain/knowledge/connector.py:42,160-169` |
| Retrieval | whitespace-token OR keyword match only; no semantic | `connector.py:96-123,125-158` |
| Embedding ABC | NONE — `adapters/_base/` has only `ChatClient` | `adapters/_base/__init__.py:60` (exports ChatClient/ModelInfo/PricingInfo/StreamEvent) |
| Azure SDK reuse | `AsyncAzureOpenAI` already wired for chat; `.embeddings.create` available on same client | `adapters/azure_openai/adapter.py:52,152-159` |
| Qdrant container | running in dev (port 6333, healthcheck), env vars declared, but NO client code | `docker-compose.dev.yml:74-86` · `.env.example:49-53` |
| Qdrant namespace | `QdrantNamespaceStrategy.collection_name/payload_filter`, `"kb"` layer exists | `infrastructure/vector/qdrant_namespace.py:55-60,76-107` |
| Qdrant client wrapper | stub only (CARRY-026); README specs `upsert/search/delete_by_tenant` | `infrastructure/vector/__init__.py:6-8` |
| `qdrant-client` dep | NOT in requirements (sentence-transformers/qdrant deferred) | `backend/requirements.txt:9` |
| Opt-in wiring | `make_default_executor(knowledge_root=...)` → `register_knowledge_tools` | `_register_all.py:232,371-375` |
| Tool handler | single-arity `(ToolCall)->str`, returns `{hits:[{source,snippet,score}],count}` | `business_domain/knowledge/tools.py:83-107,110-124` |
| llm_sdk_leak scope | scans `backend/src` (incl. business_domain); exempts `adapters/<provider>/` | `scripts/lint/check_llm_sdk_leak.py:38-43,106` |

→ The fix must add (1) section-aware chunking shared by keyword + embedding paths, (2) a provider-neutral `EmbeddingClient` ABC + Azure impl + test double, (3) a Qdrant vector-store wrapper, (4) a `KnowledgeVectorIndex` that ingests (embed sections → upsert) + searches (embed query → Qdrant search), (5) opt-in flag + fail-soft keyword fallback + idempotent startup ingest, then PROVE semantic retrieval + one-shot answering via drive-through.

### The design (backend: 1 ABC + 1 Azure adapter + 1 Qdrant wrapper + chunking + index + opt-in wiring; NO migration / wire / FE)

```
adapters/_base/embedding_client.py        EmbeddingClient ABC: async embed(texts)->list[list[float]] + model_name
adapters/azure_openai/embeddings.py       AzureOpenAIEmbeddingClient(cfg): client.embeddings.create(model=deployment, input=texts)
adapters/_testing/embedding.py            DeterministicEmbeddingClient(dim): hash->fixed-dim unit vector (CI; no Azure)
infrastructure/vector/qdrant_client.py    QdrantVectorStore(url): ensure_collection(name,dim) / upsert / search(top_k,filter=None)
business_domain/knowledge/chunking.py     split_sections(text)->list[Section(heading_path, body)]  (## split; preamble = doc intro)
business_domain/knowledge/vector_index.py KnowledgeVectorIndex(embed, store, connector): ingest()  + search(query, top_k)->list[KnowledgeHit]
business_domain/knowledge/connector.py    section-aware snippet (reuse chunking) for the keyword path too (fixes R2 when vector OFF)
business_domain/knowledge/tools.py        register_knowledge_tools(..., vector_index=None): handler vector-primary + keyword fallback
business_domain/_register_all.py          make_default_executor(..., knowledge_vector_index=None): thread to register_knowledge_tools
api/v1/chat/handler.py                    process-wide KnowledgeVectorIndex singleton (when KNOWLEDGE_VECTOR_ENABLED) + thread in
api/main.py (lifespan)                    idempotent startup ingest when flag on (fail-soft); mirror _get_shared_sandbox singleton
core/config/__init__.py                   knowledge_vector_enabled / azure_openai_embedding_deployment / qdrant_url
backend/requirements.txt                  + qdrant-client
(frontend UNTOUCHED — existing tool-call rendering surfaces hits; answer = streamed report)
(NO migration / NO new wire event / NO codegen / NO new panel)
```

WHY a new `EmbeddingClient` ABC over importing openai in the connector: 約束 3 forbids `import openai` outside `adapters/<provider>/`; `check_llm_sdk_leak.py` fails CI if the connector touches the SDK. The ABC is mandated by neutrality, not speculative (AP-6-safe: ONE concrete Azure impl + a test double, no other providers). WHY section-aware chunking shared by both paths: it's the single change that fixes R2 (richer keyword snippet) AND defines the embedding unit — one abstraction, two consumers. WHY keyword stays as fallback: preserves the 57.145 drive-through-verified path and degrades gracefully when Azure/Qdrant are down (anti-Potemkin: the tool never goes dark).

### Ground truth (recon head-start — code read on `main` HEAD `03f2b79d`; ALL re-verified §checklist 0.1)

- `connector.py:80-94` — `list_files()` (rglob `.md`/`.txt`, root-confined) — reused as the ingest file source.
- `connector.py:125-169` — `_score_and_snippet` + `_build_snippet` — the keyword path that gains section-aware snippets.
- `tools.py:49-80,110-124` — `KNOWLEDGE_SEARCH_SPEC` (unchanged) + `register_knowledge_tools` (gains a `vector_index` kwarg).
- `_register_all.py:371-375` — the 57.145 `knowledge_root` opt-in branch (gains the vector index thread-through).
- `adapters/azure_openai/adapter.py:121-159` — `AzureOpenAIConfig` + lazy `AsyncAzureOpenAI` construction (the embedding adapter mirrors this; shares endpoint/key/api_version, separate `embedding_deployment`).
- `adapters/_base/__init__.py:60` — `__all__` (gains `EmbeddingClient`).
- `infrastructure/vector/qdrant_namespace.py:67-108` — `QdrantNamespaceStrategy` (reused for the collection-name constant now; per-tenant `"kb"` namespacing is Slice 3).
- `_register_all.py:104-122` — `_get_shared_sandbox` process-wide singleton + `get_settings()` pattern (mirror for the vector-index singleton + startup ingest).

**Baselines (57.145 closeout)**: pytest 2947+6skip · wire 26 · Vitest 922 · mockup 51 · mypy 0/385 · run_all 11/11. Re-verify Day-0.

### STALE / drift findings (Day-0; full detail → progress.md — placeholder, filled in §checklist 0.1)

- **D-config-shape** — read `core/config/__init__.py` Settings + `adapters/azure_openai/config.py` `AzureOpenAIConfig`; confirm where to add `knowledge_vector_enabled` / `azure_openai_embedding_deployment` / `qdrant_url` (env names) + whether the embedding config is a sibling `AzureOpenAIEmbeddingConfig` or a field add.
- **D-embedding-test-double-home** — confirm `adapters/_testing/` vs `adapters/_mock/` is the right home for `DeterministicEmbeddingClient` (grep existing test doubles); confirm the unit tests for the Azure adapter mock `client.embeddings.create` (not a live call).
- **D-qdrant-dep** — confirm `qdrant-client` absent from requirements + pick a pinned range (`qdrant-client>=1.7,<2.0`); confirm `infrastructure/vector/qdrant_client.py` free; decide SDK vs httpx (lean SDK per README plan).
- **D-ingest-trigger** — read `api/main.py` lifespan + confirm where an idempotent startup ingest hook lands (after settings load, fail-soft); confirm the flag-OFF path adds ZERO startup cost.
- **D-handler-thread** — read `api/v1/chat/handler.py` `build_real_llm_handler`; confirm the singleton vector-index construction point + that it threads `knowledge_vector_index` into `make_default_executor` only when the flag is on.
- **D-collection-name** — confirm a fixed shared collection name (`knowledge_local_docs`) does not collide; note per-tenant `"kb"` namespacing deferred to Slice 3 (single shared root model continues from 57.145).
- **D-toolcall-render** — re-confirm (57.145 D-fe-toolcall-render) chat-v2 renders the tool result so source paths + section snippets are visible WITHOUT a new wire event.
- **D-baselines** — re-confirm pytest 2947+6skip · wire 26 (UNCHANGED) · Vitest 922 (UNCHANGED — FE untouched) · mockup 51 · mypy 0/385 · run_all 11/11.
- **D-change-num** — confirm `CHANGE-113` free (highest after 112) + design note `50-*` free (highest after 49).

## 1. Sprint Goal

Deliver real semantic retrieval on the knowledge connector and **PROVE it via a mandatory drive-through**: a real chat-v2 + real Azure embeddings + real Qdrant session where a semantic question (one keyword search would miss) makes the agent call `knowledge_search`, the tool embeds the query, Qdrant returns the right `##`-section by similarity, the section-aware snippet carries enough body that the agent answers in ONE search (no over-search into `max_turns` — the R2 fix), and the answer cites the real source path — rendered in chat-v2 with no DEMO label (real data). Gates: full backend green (FE untouched) + `KNOWLEDGE_VECTOR_ENABLED=False` keeps 57.145 byte-identical. Produces CHANGE-113 + a spike design note. Closes the Slice-2 half of `AD-Knowledge-Connector-First-Real-Source`.

## 2. User Stories

- **US-1** (Cat 2 chunking + snippet): 作為平台，我希望有一個 section-aware chunker 把 `.md` 依 `##` heading 切段，並讓 keyword 路徑回傳整個 section body（而非單行），以便修正 57.145 R2 over-search（agent 一次搜尋就拿到足夠內容）。
- **US-2** (provider-neutral embedding): 作為平台，我希望有一個 `EmbeddingClient` ABC + Azure `text-embedding-3-small` 實作（+ 測試用 deterministic double），以便在不違反 provider-neutrality 的前提下取得真實向量。
- **US-3** (Qdrant vector store): 作為平台，我希望有一個 `QdrantVectorStore` wrapper（ensure_collection / upsert / search）消費既有 Qdrant 容器，以便儲存 + 相似度檢索文件 section 向量。
- **US-4** (vector index + opt-in wiring): 作為 agent，我希望 `knowledge_search` 在 `KNOWLEDGE_VECTOR_ENABLED` 開啟時走語意檢索（embed query → Qdrant），關閉或外部錯誤時 fail-soft 回 keyword，以便我能依語意找到正確 section、且服務永不熄燈。
- **US-5** (drive-through, MANDATORY): 作為驗收者，我希望真 UI + 真 Azure embedding + 真 Qdrant 跑一個「keyword 會錯過」的語意問題，觀察 agent 呼叫 `knowledge_search` → Qdrant 回正確 section → 一次搜尋即答（無 over-search）→ 引用真實來源，且 chat-v2 真實渲染（無 DEMO），以便證明這是真語意檢索而非 Potemkin。
- **US-6** (closeout): CHANGE-113 + spike design note (8-point gate) + retrospective + navigators + `AD-Knowledge-Connector-First-Real-Source` Slice-2 CLOSED + Slice-3 carryover。

## 3. Technical Specifications

### 3.0 Architecture (backend: ABC + Azure adapter + Qdrant wrapper + chunking + index + opt-in wiring; NO migration / NO wire event / NO frontend)

```
NEW   adapters/_base/embedding_client.py            — EmbeddingClient ABC (async embed + model_name)
NEW   adapters/azure_openai/embeddings.py           — AzureOpenAIEmbeddingClient (openai SDK; embeddings.create)
NEW   adapters/azure_openai/embedding_config.py     — AzureOpenAIEmbeddingConfig (shares endpoint/key/api_version; +embedding_deployment) [shape Day-0 D-config-shape]
NEW   adapters/_testing/embedding.py                — DeterministicEmbeddingClient (hash→unit vector; CI test double)
NEW   infrastructure/vector/qdrant_client.py        — QdrantVectorStore (ensure_collection/upsert/search)
NEW   business_domain/knowledge/chunking.py         — split_sections(text)->list[Section]
NEW   business_domain/knowledge/vector_index.py     — KnowledgeVectorIndex(embed, store, connector): ingest()/search()
EDIT  adapters/_base/__init__.py                     — export EmbeddingClient
EDIT  business_domain/knowledge/connector.py        — section-aware snippet (reuse chunking) for keyword path
EDIT  business_domain/knowledge/tools.py            — register_knowledge_tools(..., vector_index=None); handler vector-primary + keyword fallback
EDIT  business_domain/knowledge/__init__.py         — export chunking / vector_index symbols
EDIT  business_domain/_register_all.py              — make_default_executor(..., knowledge_vector_index=None) thread-through
EDIT  api/v1/chat/handler.py                         — process-wide KnowledgeVectorIndex singleton (flag-gated) + thread in
EDIT  api/main.py                                    — idempotent startup ingest (flag-gated, fail-soft)
EDIT  core/config/__init__.py                        — knowledge_vector_enabled / azure_openai_embedding_deployment / qdrant_url
EDIT  backend/requirements.txt                       — + qdrant-client>=1.7,<2.0
NEW   backend/tests/unit/adapters/azure_openai/test_embeddings.py        — mock embeddings.create; batch shape; config gate
NEW   backend/tests/unit/adapters/_testing/test_deterministic_embedding.py — determinism; dim; unit-norm
NEW   backend/tests/unit/infrastructure/vector/test_qdrant_client.py     — mock QdrantClient; ensure/upsert/search shape (+ payload_filter passthrough)
NEW   backend/tests/unit/business_domain/knowledge/test_chunking.py      — ## split; preamble; heading path; empty/no-heading docs
NEW   backend/tests/unit/business_domain/knowledge/test_vector_index.py  — ingest count; search ranks by cosine; fail-soft to keyword
EDIT  backend/tests/unit/business_domain/knowledge/test_knowledge_connector.py — section-aware snippet returns body not 1 line
EDIT  backend/tests/unit/business_domain/knowledge/test_knowledge_tools.py     — vector_index path vs keyword fallback
EDIT  backend/tests/unit/.../test_make_default_executor*.py              — knowledge_vector_index opt-in (if present)
(frontend: UNTOUCHED)
```

### 3.1 Section-aware chunking + snippet (US-1) — `chunking.py` + `connector.py`

- `split_sections(text: str) -> list[Section]`: split markdown on `##`+ headings; each `Section(heading_path: str, body: str, start_line: int)`. Content before the first `##` = a preamble section (heading_path = the H1 / filename). A doc with no `##` = one whole-doc section. Trim each section body to a sane max (e.g. `_MAX_SECTION_CHARS ≈ 1200`) so the snippet is a usable paragraph, not the whole file.
- `connector.py`: the keyword snippet builder reuses `split_sections` — when a token matches inside a section, return the SECTION body (heading + paragraph) instead of the matched line ± 1. This is the R2 fix on the keyword path; `_SNIPPET_CONTEXT_LINES` retained only as the within-section trim. `KnowledgeHit` shape unchanged (source/snippet/score) — snippet is now richer.

### 3.2 EmbeddingClient ABC + Azure adapter + test double (US-2) — `adapters/`

- `EmbeddingClient(ABC)`: `async def embed(self, texts: list[str]) -> list[list[float]]` (batch; order-preserving) + `def model_name(self) -> str`. Minimal (KISS); dimension is derived at ingest from `len(vectors[0])` (no hardcoded dim). Exported from `adapters/_base/__init__.py`.
- `AzureOpenAIEmbeddingClient(config)`: lazy `AsyncAzureOpenAI` (mirror `adapter.py:_get_client`), `await client.embeddings.create(model=deployment, input=texts)`, returns `[d.embedding for d in resp.data]`. `openai` SDK import is allowed here. Config: `AzureOpenAIEmbeddingConfig` reusing endpoint/key/api_version + `embedding_deployment` (env `AZURE_OPENAI_DEPLOYMENT_EMBEDDING`); `is_configured()` gate. Error maps via the existing `AzureOpenAIErrorMapper`.
- `DeterministicEmbeddingClient(dim=64)` (`adapters/_testing/`): `embed` hashes each text → a fixed-dim unit vector (deterministic, no network). Lets unit tests exercise the index end-to-end without Azure. NOT used in production wiring.

### 3.3 Qdrant vector store wrapper (US-3) — `infrastructure/vector/qdrant_client.py`

- `QdrantVectorStore(url: str)`: lazy `qdrant_client.QdrantClient(url=...)` (or AsyncQdrantClient — pick at Day-1 by what the SDK offers cleanly; the wrapper exposes async methods via `to_thread` if sync-only).
- `ensure_collection(name, dim)`: create the collection (cosine distance) if absent; idempotent.
- `upsert(name, points)`: `points = list[(id, vector, payload)]`; payload carries `{source, heading_path, snippet}`.
- `search(name, query_vector, top_k, payload_filter=None) -> list[VectorHit(payload, score)]`: cosine top-k; `payload_filter` passthrough (reuse `QdrantNamespaceStrategy.payload_filter` shape — used by Slice 3, default None here).
- Lives in `infrastructure/vector/` (infra layer; `qdrant-client` import is NOT an LLM SDK → llm_sdk_leak N/A; category-boundaries: infra wrapper consumed by business_domain).

### 3.4 KnowledgeVectorIndex + opt-in wiring (US-4) — `vector_index.py` + `tools.py` + `_register_all.py` + `handler.py` + `main.py` + `config`

- `KnowledgeVectorIndex(embed: EmbeddingClient, store: QdrantVectorStore, connector: LocalDocsConnector, collection="knowledge_local_docs")`:
  - `async def ingest()`: for each file (`connector.list_files()`) → `split_sections` → embed all section bodies (batched) → `ensure_collection(dim)` → `upsert`. Idempotent: skip if the collection already holds the expected count (a cheap count check) — re-ingest only when empty/missing.
  - `async def search(query, top_k=5) -> list[KnowledgeHit]`: embed query → `store.search` → map payloads to `KnowledgeHit(source, snippet=heading_path+body, score=cosine)`.
- `register_knowledge_tools(registry, handlers, *, docs_root, vector_index=None)`: when `vector_index` present, the handler does vector search first; on embedding/Qdrant error → fail-soft to `connector.search` (keyword). When None → 57.145 keyword behavior byte-identical.
- `make_default_executor(..., knowledge_vector_index: KnowledgeVectorIndex | None = None)`: thread into the existing `if knowledge_root:` branch (pass `vector_index=knowledge_vector_index`). None → byte-identical.
- `handler.py`: a process-wide `KnowledgeVectorIndex` singleton built once (mirror `_get_shared_sandbox`) ONLY when `get_settings().knowledge_vector_enabled` AND the embedding config `is_configured()` AND Qdrant URL set; threaded into `make_default_executor`. Flag off → singleton None → keyword (57.145).
- `api/main.py` lifespan: when the flag is on, call `index.ingest()` once at startup (fail-soft: log + continue to keyword on any Azure/Qdrant error). Flag off → zero added startup work.
- `core/config`: `knowledge_vector_enabled: bool` (env `KNOWLEDGE_VECTOR_ENABLED`, default False), `azure_openai_embedding_deployment: str` (env `AZURE_OPENAI_DEPLOYMENT_EMBEDDING`, default ""), `qdrant_url: str` (env `QDRANT_URL`, default `http://localhost:6333`).

### 3.x What is explicitly NOT done

- Per-tenant KB collection isolation via `QdrantNamespaceStrategy` + RBAC per-doc filtering (Slice 3 — single shared `knowledge_local_docs` collection here).
- Wiring the Cat 3 memory semantic axis (CARRY-026) — this sprint scopes only the knowledge KB; the new ABC/wrapper unblock it but do not wire it.
- Re-ranking / hybrid score fusion (keyword ∪ vector merge) — vector-primary with keyword fail-soft fallback, not a fused score.
- PDF/Office parsing, external sources (SharePoint/Confluence) — later slices/ADs.
- Incremental re-ingest on file change / a manage-collection admin endpoint — startup idempotent ingest only.
- Multiple embedding providers — Azure only (the test double is not a provider).

### 3.y Validation (US-1..US-5)

Gates: mypy `src` 0/385+ · run_all 11/11 · pytest 2947+ (+ new) · Vitest 922 (UNCHANGED — FE untouched) · wire 26 (UNCHANGED) · mockup 51 (`diff` empty) · `npm run lint && npm run build` (NO `--silent`) · black/isort/flake8 clean · LLM-SDK-leak clean (embedding SDK confined to `adapters/azure_openai/`; connector sees only the ABC). Plus the §3 drive-through (MANDATORY — US-5) AND a flag-OFF byte-identical check (57.145 keyword path unchanged).

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 1 | `adapters/_base/embedding_client.py` | NEW |
| 2 | `adapters/azure_openai/embeddings.py` | NEW |
| 3 | `adapters/azure_openai/embedding_config.py` | NEW (shape per Day-0 D-config-shape) |
| 4 | `adapters/_testing/embedding.py` | NEW |
| 5 | `infrastructure/vector/qdrant_client.py` | NEW |
| 6 | `business_domain/knowledge/chunking.py` | NEW |
| 7 | `business_domain/knowledge/vector_index.py` | NEW |
| 8 | `adapters/_base/__init__.py` | EDIT (export EmbeddingClient) |
| 9 | `business_domain/knowledge/connector.py` | EDIT (section-aware snippet) |
| 10 | `business_domain/knowledge/tools.py` | EDIT (vector_index kwarg + fallback) |
| 11 | `business_domain/knowledge/__init__.py` | EDIT (exports) |
| 12 | `business_domain/_register_all.py` | EDIT (knowledge_vector_index thread-through) |
| 13 | `api/v1/chat/handler.py` | EDIT (singleton + thread + flag gate) |
| 14 | `api/main.py` | EDIT (startup idempotent ingest, flag-gated, fail-soft) |
| 15 | `core/config/__init__.py` | EDIT (3 settings) |
| 16 | `backend/requirements.txt` | EDIT (+ qdrant-client) |
| 17 | `backend/tests/unit/adapters/azure_openai/test_embeddings.py` | NEW |
| 18 | `backend/tests/unit/adapters/_testing/test_deterministic_embedding.py` | NEW |
| 19 | `backend/tests/unit/infrastructure/vector/test_qdrant_client.py` | NEW |
| 20 | `backend/tests/unit/business_domain/knowledge/test_chunking.py` | NEW |
| 21 | `backend/tests/unit/business_domain/knowledge/test_vector_index.py` | NEW |
| 22 | `backend/tests/unit/business_domain/knowledge/test_knowledge_connector.py` | EDIT (section snippet) |
| 23 | `backend/tests/unit/business_domain/knowledge/test_knowledge_tools.py` | EDIT (vector vs keyword) |
| 24 | `backend/tests/unit/.../test_make_default_executor*.py` | EDIT (if present — opt-in) |
| — | `agent_harness/orchestrator_loop/loop.py` | **UNTOUCHED** (tool flows through existing executor) |
| — | `api/v1/chat/sse.py` / `event_wire_schema.py` / codegen | **UNTOUCHED** (no new wire event) |
| — | `frontend/**` | **UNTOUCHED** (existing tool-call rendering) |
| — | `infrastructure/db/**` | **UNTOUCHED** (no migration — Qdrant holds vectors) |

## 5. Acceptance Criteria

1. `split_sections` chunks `.md` by `##` heading; the keyword path returns a section body (not a single line) — 57.145 R2 over-search structurally fixed (unit-tested).
2. `EmbeddingClient` ABC + `AzureOpenAIEmbeddingClient` (openai SDK confined to `adapters/azure_openai/`) + `DeterministicEmbeddingClient` test double; llm_sdk_leak clean (unit-tested with the SDK mocked — no live Azure in CI).
3. `QdrantVectorStore` ensure/upsert/search over the running Qdrant container; `KnowledgeVectorIndex.ingest()` idempotent; `search()` ranks by cosine (unit-tested with the deterministic double + mocked Qdrant).
4. `knowledge_search` is vector-primary when `KNOWLEDGE_VECTOR_ENABLED` + embedding configured + Qdrant reachable; fail-soft to keyword on error; flag OFF → executor byte-identical to 57.145 (unit-tested).
5. **Drive-through PASS (MANDATORY, real UI + Azure embedding + Qdrant)** — a semantic query keyword would miss returns the right `##`-section by similarity, the agent answers in ONE `knowledge_search` (no over-search into `max_turns`), and cites the real source path; rendered with NO DEMO label. Screenshot + observed-vs-intended in progress.md. (NOT gate-only.)
6. `AD-Knowledge-Connector-First-Real-Source` Slice-2 CLOSED; CHANGE-113 + spike design note (8-point gate); calibration recorded; navigators + next-phase-candidates updated (Slice-3 carryover); reality-audit pillar 1 note (connector quality: keyword → semantic).

## 6. Deliverables

- [ ] US-1 section-aware chunking + richer keyword snippet (R2 fix)
- [ ] US-2 `EmbeddingClient` ABC + Azure adapter + deterministic test double
- [ ] US-3 `QdrantVectorStore` wrapper
- [ ] US-4 `KnowledgeVectorIndex` + opt-in wiring + fail-soft fallback + startup ingest
- [ ] US-5 drive-through PASS (semantic retrieval + one-shot answer, real Azure + Qdrant, no DEMO)
- [ ] US-6 CHANGE-113 + design note + retro + navigators + Slice-2 CLOSED

## 7. Workload Calibration

- Scope class **`knowledge-embedding-vector-spike` 0.60** (NEW class, 1st data point). Rationale: a greenfield embedding+vector path — a new cross-category ABC (`EmbeddingClient`) + a real Azure adapter + a Qdrant infra wrapper + chunking + an ingest/search index + opt-in wiring + a drive-through with TWO external deps (Azure embedding + Qdrant). Heavier than 57.145's `knowledge-connector-real-source-spike` 0.55 (which was keyword-only, no new ABC/infra) — the new ABC + infra wrapper are real design-decision content, so 0.60 (≈ `skills-system-spike` 0.60 / `task-primitive-spike` 0.60 greenfield-module shape, but with the offsetting external-dep drive-through risk). Cite `.claude/rules/sprint-workflow.md` §Scope-class multiplier matrix; flag for re-point if 1st-pt ratio lands out of [0.7, 1.2] (the external-dep drive-through is the variance risk — same family as 57.130's wire-surface over-edge).
- **Agent-delegated: no** (parent-direct; consistent with the 57.136-145 spike run). `agent_factor` 1.0 → 3-segment form. Rationale: a cross-category ABC design decision + a real new external-infra risk surface + a mandatory drive-through with two external deps — parent-direct keeps the judgment in-loop. (Test-writing may be opportunistically delegated mid-sprint without changing the classification, per §Before Commit item 7 — parent re-runs ALL gates.)
- Bottom-up est ~20.5 hr (chunking + snippet ~1.5 · EmbeddingClient ABC + Azure adapter + config + test double ~3.5 · Qdrant wrapper ~2.5 · vector index + ingest ~2 · tool/connector hybrid wiring ~1.5 · config + handler + register + startup ingest ~2 · unit tests all ~3 · drive-through ~2 · closeout incl. design note ~2.5) → class-calibrated commit ~12.3 hr (mult 0.60). Day-4 retro Q2 verifies. **Note**: this is a LARGE spike (~2.5× a normal 57.13x spike) — the user explicitly chose the snippet+embedding+Qdrant bundle informed it exceeds thin-spike; structured for safety (keyword fallback + opt-in flag preserve the 57.145 path).

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| **Azure embedding deployment missing** (drive-through blocker — needs `text-embedding-3-*` deployed on the user's Azure resource) | env `AZURE_OPENAI_DEPLOYMENT_EMBEDDING`; confirm the deployment name with the user at Day 3 start; if absent, the drive-through cannot run with real embeddings → either deploy one OR (last resort) the flag-OFF keyword path still ships the R2 snippet fix (US-1) drive-through-able without Azure. The vector half (US-2/3/4) would then be gate-only — explicitly labelled, NOT "verified". |
| **provider-neutrality leak** (embedding SDK in business_domain) | `EmbeddingClient` ABC in `adapters/_base/`; openai SDK confined to `adapters/azure_openai/embeddings.py`; `check_llm_sdk_leak.py` (run_all) gates it; connector imports only the ABC. |
| **Qdrant unreachable at runtime / startup** | Fail-soft everywhere: startup ingest logs + continues to keyword; the tool handler catches embedding/Qdrant errors → keyword fallback. The tool never goes dark (anti-Potemkin). |
| **Stale `--reload` masks the new flag/singleton/ingest** (Risk Class E) | Clean restart before drive-through: kill stale uvicorn reloader + orphan spawn-workers (Win32_Process PID/PPID/StartTime sweep per 57.97), set `KNOWLEDGE_VECTOR_ENABLED=1` + `AZURE_OPENAI_DEPLOYMENT_EMBEDDING` + the root `.env` Azure vars in the SAME start shell (57.145 env-mechanism lesson — config reads OS env, not `backend/.env`), confirm the startup ingest log line + fresh sole port owner, THEN drive-through. |
| **Ingest cost / latency at startup** (~21 docs × N sections = one embedding batch) | Idempotent: skip if the collection already holds the expected count; batch all sections in one `embeddings.create` call; fail-soft so a slow/failed ingest never blocks startup (degrades to keyword). |
| **`qdrant-client` new dependency** | Pin `qdrant-client>=1.7,<2.0` (the documented Phase-51.2 plan); infra-layer only; CI installs it; the deterministic test double + mocked QdrantClient keep unit tests offline. |
| **Embedding dimension mismatch on re-ingest** (model change → different dim vs existing collection) | `ensure_collection` derives dim from the live embedding output; on dim mismatch with an existing collection, recreate (drop+create) — logged; acceptable for a single shared system KB (no tenant data at risk). |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- Per-tenant KB collection isolation (`QdrantNamespaceStrategy` `"kb"` layer) + RBAC per-doc filtering + structured citation report → `AD-Knowledge-Connector-RBAC-Citation-Slice3`.
- External-platform sources (SharePoint/Confluence/Notion read API) → `AD-Knowledge-Connector-External-Source`.
- PDF/Office parsing → `AD-Knowledge-Connector-DocTypes`.
- Wiring the Cat 3 memory semantic axis on the new ABC/wrapper (CARRY-026) → separate Cat 3 sprint.
- Hybrid keyword∪vector score fusion / re-ranking → `AD-Knowledge-Connector-Hybrid-Rerank`.
- Incremental re-ingest on file change + a manage-collection admin endpoint → `AD-Knowledge-Connector-Ingest-Mgmt`.
