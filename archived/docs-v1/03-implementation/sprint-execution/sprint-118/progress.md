# Sprint 118 Progress: RAG Pipeline

## 狀態概覽

| 項目 | 狀態 |
|------|------|
| **開始日期** | 2026-03-19 |
| **預計結束** | 2026-03-19 |
| **總點數** | 10 點 |
| **完成點數** | 10 點 |
| **進度** | 100% |
| **Phase** | Phase 38 — E2E Assembly C |
| **Branch** | `feature/phase-38-e2e-c` |

## Sprint 目標

1. ✅ DocumentParser（PDF/Word/HTML/Markdown/Text 多格式解析）
2. ✅ DocumentChunker（recursive + semantic + fixed-size 三種策略）
3. ✅ EmbeddingManager（Azure OpenAI text-embedding-3-large 整合）
4. ✅ VectorStoreManager（Qdrant collection 管理 + in-memory fallback）
5. ✅ KnowledgeRetriever（hybrid search + keyword boost + reranking）
6. ✅ RAGPipeline（端到端 ingest + retrieve + search_knowledge handler）

## User Stories 進度

| Story | 名稱 | 點數 | 狀態 | 完成度 |
|-------|------|------|------|--------|
| S118-1 | DocumentParser | 2 | ✅ 完成 | 100% |
| S118-2 | DocumentChunker | 2 | ✅ 完成 | 100% |
| S118-3 | EmbeddingManager | 1 | ✅ 完成 | 100% |
| S118-4 | VectorStoreManager | 2 | ✅ 完成 | 100% |
| S118-5 | KnowledgeRetriever | 2 | ✅ 完成 | 100% |
| S118-6 | RAGPipeline + search_knowledge handler | 1 | ✅ 完成 | 100% |

## 完成項目詳情

### S118-1: DocumentParser (2 SP)
- **新增**: `backend/src/integrations/knowledge/document_parser.py`
  - 支援 PDF (PyPDF2)、DOCX (python-docx)、HTML (stdlib)、Markdown、Text
  - `parse(file_path)` / `parse_text(text)` → `ParsedDocument`
  - 格式自動偵測（副檔名映射 12 種格式）
  - Graceful fallback: 無相依套件時降級為 raw text

### S118-2: DocumentChunker (2 SP)
- **新增**: `backend/src/integrations/knowledge/chunker.py`
  - 3 種策略: RECURSIVE（heading→paragraph→sentence）/ FIXED_SIZE / SEMANTIC
  - Recursive: 先按 markdown heading 分割 → 段落 → 固定窗口
  - Fixed-size: 字元窗口 + overlap + 句子邊界對齊
  - `TextChunk` dataclass with metadata (split_level, position)

### S118-3: EmbeddingManager (1 SP)
- **新增**: `backend/src/integrations/knowledge/embedder.py`
  - 委託 `integrations/memory/EmbeddingService` 做實際向量化
  - 支援 `embed_text()` / `embed_batch()`
  - Fallback: hash-based pseudo-embedding（開發環境無 API key 時）

### S118-4: VectorStoreManager (2 SP)
- **新增**: `backend/src/integrations/knowledge/vector_store.py`
  - Qdrant client 管理（local path 模式）
  - `index_documents()` — 批次索引 + upsert
  - `search()` — cosine similarity search
  - `delete_collection()` / `get_collection_info()`
  - In-memory fallback store（無 Qdrant 時）

### S118-5: KnowledgeRetriever (2 SP)
- **新增**: `backend/src/integrations/knowledge/retriever.py`
  - Hybrid search: vector similarity + keyword boost (70/30 blend)
  - Reciprocal Rank Fusion scoring
  - Simple reranking (query-document overlap coverage)
  - `RetrievalResult` dataclass with content, score, source, metadata

### S118-6: RAGPipeline (1 SP)
- **新增**: `backend/src/integrations/knowledge/rag_pipeline.py`
  - `ingest_file()` — Parse → Chunk → Embed → Index
  - `ingest_text()` — Direct text ingestion
  - `retrieve()` / `retrieve_and_format()` — Search + format for LLM
  - `handle_search_knowledge()` — Orchestrator tool handler

## 檔案變更清單

| 操作 | 檔案路徑 |
|------|---------|
| 新增 | `backend/src/integrations/knowledge/__init__.py` |
| 新增 | `backend/src/integrations/knowledge/document_parser.py` |
| 新增 | `backend/src/integrations/knowledge/chunker.py` |
| 新增 | `backend/src/integrations/knowledge/embedder.py` |
| 新增 | `backend/src/integrations/knowledge/vector_store.py` |
| 新增 | `backend/src/integrations/knowledge/retriever.py` |
| 新增 | `backend/src/integrations/knowledge/rag_pipeline.py` |

## 架構決策

| 決策 | 理由 |
|------|------|
| Recursive chunking 為預設 | 按文件結構分割品質最佳 |
| Hybrid search (70% vector + 30% keyword) | 平衡語義相似和精確匹配 |
| In-memory fallback for Qdrant | 開發環境不強制安裝 Qdrant |
| Hash-based pseudo-embedding fallback | 無 API key 時仍可開發測試 |
| 獨立 knowledge/ 模組 | 與 memory/ 分離，知識 ≠ 記憶 |

## 相關文檔

- [Phase 38 計劃](../../sprint-planning/phase-38/README.md)
- [Sprint 117 Progress](../sprint-117/progress.md)
