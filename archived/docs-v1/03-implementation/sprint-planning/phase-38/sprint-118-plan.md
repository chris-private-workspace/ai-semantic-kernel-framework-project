# Sprint 118: RAG Pipeline

## Sprint Info

| Field | Value |
|-------|-------|
| **Sprint Number** | 118 |
| **Phase** | 38 - E2E Assembly C: 記憶與知識組裝 |
| **Duration** | 1 day |
| **Story Points** | 10 pts |
| **Status** | ✅ 完成 |
| **Branch** | `feature/phase-38-e2e-c` |

---

## Sprint 目標

實現完整的 RAG Pipeline，包括文檔解析、Chunking、Embedding、向量索引、檢索 + Reranking 管線，讓 Orchestrator Agent 具備企業知識檢索能力。

---

## Sprint 概述

Sprint 118 為 Phase 38 的第二個 Sprint，建構獨立的 `knowledge/` 模組，實現從文檔入庫到語義檢索的端到端 RAG 管線。包含 5 個核心元件（DocumentParser、DocumentChunker、EmbeddingManager、VectorStoreManager、KnowledgeRetriever）和 1 個編排器（RAGPipeline），並將 search_knowledge handler 接入 Orchestrator。

---

## 前置條件

- ✅ Sprint 117 完成（記憶寫入 + 檢索注入）
- ✅ Azure OpenAI Embedding 模型可用 (text-embedding-3-large)
- ✅ Qdrant 向量資料庫就緒
- ✅ search_knowledge tool 定義已完成

---

## User Stories

### S118-1: DocumentParser 文檔解析器 (2 pts)

**作為** 知識管理系統，
**我希望** 支援 PDF、Word、HTML、Markdown、Text 等多格式文檔解析，
**以便** 企業各類文件能統一入庫成為可檢索的知識。

**技術規格**:
- 新增 `backend/src/integrations/knowledge/document_parser.py`
- 支援 PDF (PyPDF2)、DOCX (python-docx)、HTML (stdlib)、Markdown、Text
- `parse(file_path)` / `parse_text(text)` → `ParsedDocument`
- 格式自動偵測（副檔名映射 12 種格式）
- Graceful fallback: 無相依套件時降級為 raw text

---

### S118-2: DocumentChunker 文檔分塊 (2 pts)

**作為** RAG Pipeline，
**我希望** 將解析後的文檔以 recursive、semantic、fixed-size 三種策略進行分塊，
**以便** 文件內容能以適當粒度被索引和檢索。

**技術規格**:
- 新增 `backend/src/integrations/knowledge/chunker.py`
- 3 種策略: RECURSIVE（heading→paragraph→sentence）/ FIXED_SIZE / SEMANTIC
- Recursive: 先按 markdown heading 分割 → 段落 → 固定窗口
- Fixed-size: 字元窗口 + overlap + 句子邊界對齊
- `TextChunk` dataclass with metadata (split_level, position)

---

### S118-3: EmbeddingManager 向量化 (1 pt)

**作為** RAG Pipeline，
**我希望** 將文本透過 Azure OpenAI text-embedding-3-large 模型轉換為向量，
**以便** 文本能在向量空間中進行語義相似度搜索。

**技術規格**:
- 新增 `backend/src/integrations/knowledge/embedder.py`
- 委託 `integrations/memory/EmbeddingService` 做實際向量化
- 支援 `embed_text()` / `embed_batch()`
- Fallback: hash-based pseudo-embedding（開發環境無 API key 時）

---

### S118-4: VectorStoreManager 向量索引管理 (2 pts)

**作為** 知識管理系統，
**我希望** 管理 Qdrant collection 的建立、索引、搜索和刪除，
**以便** 知識向量能被持久化存儲和高效檢索。

**技術規格**:
- 新增 `backend/src/integrations/knowledge/vector_store.py`
- Qdrant client 管理（local path 模式）
- `index_documents()` — 批次索引 + upsert
- `search()` — cosine similarity search
- `delete_collection()` / `get_collection_info()`
- In-memory fallback store（無 Qdrant 時）

---

### S118-5: KnowledgeRetriever 檢索 + Reranking (2 pts)

**作為** Orchestrator Agent，
**我希望** 透過 hybrid search (vector + keyword) 結合 reranking 取得最相關的知識片段，
**以便** 回答品質不僅依賴語義相似度，也考慮關鍵字精確匹配。

**技術規格**:
- 新增 `backend/src/integrations/knowledge/retriever.py`
- Hybrid search: vector similarity + keyword boost (70/30 blend)
- Reciprocal Rank Fusion scoring
- Simple reranking (query-document overlap coverage)
- `RetrievalResult` dataclass with content, score, source, metadata

---

### S118-6: RAGPipeline + search_knowledge handler (1 pt)

**作為** Orchestrator Agent，
**我希望** 有一個端到端的 RAG Pipeline 編排器和對應的 tool handler，
**以便** 自主決定何時、如何從知識庫中檢索資訊來回答用戶問題。

**技術規格**:
- 新增 `backend/src/integrations/knowledge/rag_pipeline.py`
- `ingest_file()` — Parse → Chunk → Embed → Index
- `ingest_text()` — Direct text ingestion
- `retrieve()` / `retrieve_and_format()` — Search + format for LLM
- `handle_search_knowledge()` — Orchestrator tool handler

---

## 架構決策

| 決策 | 理由 |
|------|------|
| Recursive chunking 為預設 | 按文件結構分割品質最佳 |
| Hybrid search (70% vector + 30% keyword) | 平衡語義相似和精確匹配 |
| In-memory fallback for Qdrant | 開發環境不強制安裝 Qdrant |
| Hash-based pseudo-embedding fallback | 無 API key 時仍可開發測試 |
| 獨立 knowledge/ 模組 | 與 memory/ 分離，知識 ≠ 記憶 |

---

## 相關連結

- [Phase 38 計劃](./README.md)
- [Sprint 118 Progress](../../sprint-execution/sprint-118/progress.md)
- [Sprint 117 Plan](./sprint-117-plan.md)
- [Sprint 119 Plan](./sprint-119-plan.md)
