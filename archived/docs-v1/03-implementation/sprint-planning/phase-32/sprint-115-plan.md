# Sprint 115: SemanticRouter Real 實現

## 概述

Sprint 115 專注於將 SemanticRouter 從 Mock 實現遷移到 Azure AI Search 向量搜索，這是三層路由系統從「60% 可用」提升到「95% 可用」的關鍵步驟。

**重要**: 本 Sprint 整合了原 Phase 30（Azure AI Search）的 Sprint 107-110 計劃內容。詳細技術規格請參考：
- `docs/03-implementation/sprint-planning/phase-30/sprint-107-plan.md` — Azure AI Search 資源建立 + 索引設計
- `docs/03-implementation/sprint-planning/phase-30/sprint-108-plan.md` — AzureSemanticRouter 實現
- `docs/03-implementation/sprint-planning/phase-30/sprint-109-plan.md` — 路由管理 API + 資料遷移

## 目標

1. 建立 Azure AI Search 資源和 semantic-routes 索引
2. 實現 AzureSemanticRouter 替代 Mock SemanticRouter
3. 路由管理 CRUD API + 現有 15 條路由遷移到 Azure

## Story Points: 45 點

## 前置條件

- ✅ Sprint 114 完成（AD 場景基礎建設）
- ✅ Azure 訂閱可用
- ✅ Azure OpenAI 已配置（text-embedding-ada-002）
- ✅ Phase 31 Mock 分離完成（確認使用真實版本）

## 任務分解

### Story 115-1: Azure AI Search 資源建立 + semantic-routes 索引 (2 天, P0)

> **對應**: Phase 30 Sprint 107 全部內容

**目標**: 在 Azure 建立 AI Search 資源，設計並建立 HNSW 向量索引

**交付物**:
- Azure AI Search 服務實例（`ipa-semantic-search`）
- `backend/src/integrations/orchestration/intent_router/semantic_router/index_schema.json`
- `backend/src/integrations/orchestration/intent_router/semantic_router/setup_index.py`
- 修改 `backend/.env.example` 新增 Azure AI Search 環境變量

**Azure 資源配置**:

| 項目 | 設定 |
|------|------|
| 名稱 | `ipa-semantic-search` |
| 區域 | East US 2（與 Azure OpenAI 同區） |
| 定價層 | Basic (~$75/月) |
| 索引名稱 | `semantic-routes` |

**索引 Schema 重點**:

```json
{
  "name": "semantic-routes",
  "fields": [
    {"name": "id", "type": "Edm.String", "key": true},
    {"name": "route_name", "type": "Edm.String", "filterable": true},
    {"name": "category", "type": "Edm.String", "filterable": true, "facetable": true},
    {"name": "sub_intent", "type": "Edm.String", "filterable": true},
    {"name": "utterance", "type": "Edm.String", "searchable": true},
    {"name": "utterance_vector", "type": "Collection(Edm.Single)", "dimensions": 1536, "vectorSearchProfile": "vector-profile"},
    {"name": "workflow_type", "type": "Edm.String", "filterable": true},
    {"name": "risk_level", "type": "Edm.String", "filterable": true},
    {"name": "description", "type": "Edm.String", "searchable": true},
    {"name": "enabled", "type": "Edm.Boolean", "filterable": true},
    {"name": "created_at", "type": "Edm.DateTimeOffset", "sortable": true},
    {"name": "updated_at", "type": "Edm.DateTimeOffset", "sortable": true}
  ],
  "vectorSearch": {
    "algorithms": [{"name": "hnsw-algorithm", "kind": "hnsw"}],
    "profiles": [{"name": "vector-profile", "algorithmConfigurationName": "hnsw-algorithm"}]
  }
}
```

**環境變量新增**:

```bash
# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://ipa-semantic-search.search.windows.net
AZURE_SEARCH_API_KEY=<your-api-key>
AZURE_SEARCH_INDEX_NAME=semantic-routes
USE_AZURE_SEARCH=true
SEMANTIC_SIMILARITY_THRESHOLD=0.85
SEMANTIC_TOP_K=3
```

**驗收標準**:
- [ ] Azure AI Search 服務建立成功
- [ ] 可以存取管理 API
- [ ] 索引 Schema 建立成功（HNSW + hybrid search）
- [ ] setup_index.py 腳本可重複執行（冪等）
- [ ] 環境變量文檔更新
- [ ] 連接驗證測試通過

### Story 115-2: AzureSemanticRouter 實現 (3 天, P0)

> **對應**: Phase 30 Sprint 108 全部內容

**目標**: 實現基於 Azure AI Search 的語義路由器，替代 Mock SemanticRouter

**交付物**:
- `backend/src/integrations/orchestration/intent_router/semantic_router/azure_search_client.py`
- `backend/src/integrations/orchestration/intent_router/semantic_router/embedding_service.py`
- `backend/src/integrations/orchestration/intent_router/semantic_router/azure_semantic_router.py`
- `backend/tests/unit/orchestration/test_azure_semantic_router.py`
- `backend/tests/unit/orchestration/test_embedding_service.py`

**核心實現**:

```python
class AzureSearchClient:
    """Azure AI Search 客戶端封裝"""
    def __init__(self, endpoint: str, api_key: str, index_name: str): ...
    async def vector_search(self, vector: list[float], top_k: int, filters: str) -> list[dict]: ...
    async def hybrid_search(self, query: str, vector: list[float], top_k: int) -> list[dict]: ...
    async def upload_documents(self, documents: list[dict]) -> None: ...
    async def delete_documents(self, ids: list[str]) -> None: ...


class EmbeddingService:
    """Azure OpenAI Embedding 服務"""
    def __init__(self, endpoint: str, api_key: str, deployment: str): ...
    async def get_embedding(self, text: str) -> list[float]: ...
    async def get_embeddings_batch(self, texts: list[str]) -> list[list[float]]: ...


class AzureSemanticRouter:
    """基於 Azure AI Search 的語義路由器"""
    def __init__(
        self, search_client: AzureSearchClient,
        embedding_service: EmbeddingService,
        similarity_threshold: float = 0.85
    ): ...

    async def route(self, query: str) -> Optional[SemanticRouteResult]: ...
    async def route_with_scores(self, query: str, top_k: int = 3) -> list[SemanticRouteResult]: ...
```

**整合 BusinessIntentRouter**:
- 修改 `BusinessIntentRouter` 的 Layer 2 初始化邏輯
- 當 `USE_AZURE_SEARCH=true` 時使用 `AzureSemanticRouter`
- 當 `USE_AZURE_SEARCH=false` 時 fallback 到原有 Mock SemanticRouter
- 支援 text-embedding-ada-002 (1536 維向量)

**驗收標準**:
- [ ] AzureSearchClient 封裝完成（vector search + hybrid search）
- [ ] EmbeddingService 封裝完成（單筆 + 批次）
- [ ] AzureSemanticRouter 完整實現
- [ ] 與 BusinessIntentRouter 整合完成
- [ ] Fallback 機制正常（Azure 不可用時 fallback 到 Mock）
- [ ] 搜索延遲 < 100ms (P95)
- [ ] 快取機制實現（常用查詢快取 embedding）
- [ ] 單元測試覆蓋率 > 90%

### Story 115-3: 路由管理 API + 資料遷移 (2 天, P0)

> **對應**: Phase 30 Sprint 109 全部內容

**目標**: 實現路由管理 CRUD API，並將現有 15 條路由從 YAML 遷移到 Azure AI Search

**交付物**:
- `backend/src/integrations/orchestration/intent_router/semantic_router/route_manager.py`
- `backend/src/api/v1/orchestration/routes.py`（路由管理端點）
- `backend/src/integrations/orchestration/intent_router/semantic_router/migration.py`
- `backend/tests/unit/orchestration/test_route_manager.py`
- `backend/tests/integration/orchestration/test_route_api.py`

**路由管理 API**:

```
POST   /api/v1/orchestration/routes          # 新增路由
GET    /api/v1/orchestration/routes          # 列出路由
PUT    /api/v1/orchestration/routes/{id}     # 更新路由
DELETE /api/v1/orchestration/routes/{id}     # 刪除路由
POST   /api/v1/orchestration/routes/sync     # YAML → Azure 同步
POST   /api/v1/orchestration/routes/search   # 測試搜索
```

**資料遷移**:
- 讀取現有 YAML 路由定義（15 條路由，56 個 utterance）
- 批次生成 embedding 向量
- 上傳到 Azure AI Search 索引
- 驗證遷移完整性（數量、搜索結果比對）

**驗收標準**:
- [ ] 6 個路由管理端點全部實現
- [ ] CRUD 操作正確（含 embedding 自動生成）
- [ ] YAML → Azure 同步功能可用
- [ ] 15 條路由成功遷移
- [ ] 遷移後搜索結果與原 Mock 一致
- [ ] API 測試通過

## 技術設計

### 目錄結構

```
backend/src/integrations/orchestration/intent_router/semantic_router/
├── __init__.py
├── index_schema.json               # 🆕 索引 Schema
├── setup_index.py                  # 🆕 索引建立腳本
├── azure_search_client.py          # 🆕 Azure Search 封裝
├── embedding_service.py            # 🆕 Embedding 服務
├── azure_semantic_router.py        # 🆕 Azure 語義路由器
├── route_manager.py                # 🆕 路由管理器
├── migration.py                    # 🆕 遷移腳本
├── semantic_router.py              # 現有: Mock 實現 (保留作為 fallback)
└── routes.yaml                     # 現有: 路由定義
```

### 依賴新增

```
azure-search-documents>=11.4.0
azure-identity>=1.14.0
openai>=1.10.0
```

## 風險

| 風險 | 緩解措施 |
|------|----------|
| Azure AI Search 服務建立延遲 | 提前申請，平行處理其他任務 |
| Embedding 品質不足 | 調整 similarity_threshold、增加 utterance 多樣性 |
| 遷移後路由結果差異 | 比對測試、人工驗證 Top-5 路由 |
| Azure 成本超預期 | 監控 API 調用量、實現 embedding 快取 |

## 完成標準

- [ ] Azure AI Search 資源和索引建立成功
- [ ] AzureSemanticRouter 替代 Mock，正常運作
- [ ] 15 條路由成功遷移到 Azure
- [ ] 路由管理 API 全部可用
- [ ] 搜索延遲 < 100ms (P95)
- [ ] Fallback 機制測試通過

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 45
**開始日期**: TBD
