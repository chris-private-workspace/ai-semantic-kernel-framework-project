# Sprint 107: Azure AI Search 資源建立 + 索引設計

## 概述

Sprint 107 專注於建立 Azure AI Search 資源和設計語義路由索引，這是整個 Phase 30 的基礎設施準備。

## 目標

1. 建立 Azure AI Search 資源
2. 設計並建立 semantic-routes 索引
3. 配置環境變量
4. 驗證 Azure 連接

## Story Points: 15 點

## 前置條件

- ✅ Azure 訂閱可用
- ✅ Azure OpenAI 已配置
- ✅ Phase 28 完成
- ✅ Phase 29 完成

## 任務分解

### Story 107-1: 建立 Azure AI Search 資源 (2h, P0)

**目標**: 在 Azure Portal 建立 Azure AI Search 服務

**交付物**:
- Azure AI Search 服務實例
- 服務端點 URL
- 管理 API Key

**步驟**:
1. 登入 Azure Portal
2. 建立資源 → "Azure AI Search"
3. 設定:
   - 名稱: `ipa-semantic-search`
   - 區域: East US 2 (與 OpenAI 同區)
   - 定價層: Basic (~$75/月)
4. 取得 Endpoint 和 API Key

**驗收標準**:
- [ ] Azure AI Search 服務建立成功
- [ ] 可以存取管理 API

### Story 107-2: 設計索引 Schema (2h, P0)

**目標**: 設計 semantic-routes 索引結構

**交付物**:
- `backend/src/integrations/orchestration/intent_router/semantic_router/index_schema.json`

**索引設計**:
```json
{
  "name": "semantic-routes",
  "fields": [
    {"name": "id", "type": "Edm.String", "key": true},
    {"name": "route_name", "type": "Edm.String", "filterable": true, "sortable": true},
    {"name": "category", "type": "Edm.String", "filterable": true, "facetable": true},
    {"name": "sub_intent", "type": "Edm.String", "filterable": true},
    {"name": "utterance", "type": "Edm.String", "searchable": true, "analyzer": "zh-Hans.microsoft"},
    {"name": "utterance_vector", "type": "Collection(Edm.Single)", "dimensions": 1536, "vectorSearchProfile": "vector-profile"},
    {"name": "workflow_type", "type": "Edm.String", "filterable": true},
    {"name": "risk_level", "type": "Edm.String", "filterable": true},
    {"name": "description", "type": "Edm.String", "searchable": true},
    {"name": "enabled", "type": "Edm.Boolean", "filterable": true},
    {"name": "created_at", "type": "Edm.DateTimeOffset", "sortable": true},
    {"name": "updated_at", "type": "Edm.DateTimeOffset", "sortable": true}
  ],
  "vectorSearch": {
    "algorithms": [
      {
        "name": "hnsw-algorithm",
        "kind": "hnsw",
        "hnswParameters": {
          "m": 4,
          "efConstruction": 400,
          "efSearch": 500,
          "metric": "cosine"
        }
      }
    ],
    "profiles": [
      {
        "name": "vector-profile",
        "algorithm": "hnsw-algorithm"
      }
    ]
  }
}
```

**驗收標準**:
- [ ] Schema 定義完整
- [ ] 向量搜索配置正確
- [ ] 中文分析器配置

### Story 107-3: 建立索引 (2h, P0)

**目標**: 在 Azure AI Search 中建立索引

**交付物**:
- `backend/scripts/create_search_index.py`

**腳本功能**:
```python
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
)

def create_index():
    """建立 semantic-routes 索引"""
    index_client = SearchIndexClient(
        endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
        credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_API_KEY")),
    )

    # 從 schema.json 載入並建立索引
    ...
```

**驗收標準**:
- [ ] 索引建立成功
- [ ] 可以在 Azure Portal 查看索引結構
- [ ] 向量搜索配置正確

### Story 107-4: 配置環境變量 (1h, P0)

**目標**: 更新環境變量配置

**交付物**:
- 更新 `backend/.env.example`
- 更新 `backend/.env`

**新增變量**:
```bash
# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://ipa-semantic-search.search.windows.net
AZURE_SEARCH_API_KEY=<your-api-key>
AZURE_SEARCH_INDEX_NAME=semantic-routes

# Semantic Router Configuration
USE_AZURE_SEARCH=true
SEMANTIC_SIMILARITY_THRESHOLD=0.85
SEMANTIC_TOP_K=3
```

**驗收標準**:
- [ ] .env.example 更新完成
- [ ] 本地 .env 配置正確
- [ ] 敏感資訊不被 commit

### Story 107-5: 驗證連接 (1h, P1)

**目標**: 驗證 Azure AI Search 連接

**交付物**:
- `backend/scripts/verify_search_connection.py`

**測試內容**:
1. 連接到 Azure AI Search
2. 列出索引
3. 取得索引統計
4. 執行簡單搜索測試

**驗收標準**:
- [ ] 連接測試通過
- [ ] 索引存在
- [ ] 搜索 API 可用

## 技術設計

### Azure AI Search 配置選項

| 設定 | 值 | 說明 |
|------|-----|------|
| 定價層 | Basic | 15 GB 存儲, 3 replica |
| 區域 | East US 2 | 與 Azure OpenAI 同區減少延遲 |
| 複本數 | 1 | 開發環境，生產可增加 |
| 分區數 | 1 | 資料量小，1 個分區足夠 |

### 向量搜索參數

| 參數 | 值 | 說明 |
|------|-----|------|
| Algorithm | HNSW | 高效近似最近鄰搜索 |
| Metric | cosine | 餘弦相似度 |
| m | 4 | 每層連接數 |
| efConstruction | 400 | 建索引時搜索範圍 |
| efSearch | 500 | 搜索時搜索範圍 |

## 依賴

```
azure-search-documents>=11.4.0
azure-identity>=1.14.0
```

## 風險

| 風險 | 緩解措施 |
|------|---------|
| Azure 資源建立失敗 | 確認訂閱權限和配額 |
| 區域不可用 | 備選 East US 或 West US 2 |
| API Key 外洩 | 使用環境變量，不 commit |

## 完成標準

- [ ] Azure AI Search 資源建立
- [ ] 索引 Schema 設計完成
- [ ] 索引建立成功
- [ ] 環境變量配置完成
- [ ] 連接驗證通過

---

**Sprint 開始**: TBD
**Sprint 結束**: TBD + 3 days
**Story Points**: 15
