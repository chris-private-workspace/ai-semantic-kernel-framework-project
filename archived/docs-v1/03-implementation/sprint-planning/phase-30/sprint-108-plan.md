# Sprint 108: AzureSemanticRouter 實現

## 概述

Sprint 108 專注於實現基於 Azure AI Search 的語義路由器，替代現有的內存實現，提供持久化和動態管理能力。

## 目標

1. 實現 AzureSemanticRouter 類
2. 整合 Azure OpenAI Embedding
3. 實現向量搜索功能
4. 與 BusinessIntentRouter 整合
5. 實現 fallback 機制

## Story Points: 25 點

## 前置條件

- ✅ Sprint 107 完成 (Azure AI Search 資源)
- ✅ Azure AI Search 索引就緒
- ✅ Azure OpenAI Embedding 可用

## 任務分解

### Story 108-1: AzureSearchClient 封裝 (4h, P0)

**目標**: 封裝 Azure AI Search SDK 操作

**交付物**:
- `backend/src/integrations/orchestration/intent_router/semantic_router/azure_search_client.py`

**核心實現**:
```python
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential

class AzureSearchClient:
    """Azure AI Search 客戶端封裝"""

    def __init__(
        self,
        endpoint: str,
        index_name: str,
        api_key: str,
    ):
        self._client = SearchClient(
            endpoint=endpoint,
            index_name=index_name,
            credential=AzureKeyCredential(api_key),
        )

    async def vector_search(
        self,
        vector: List[float],
        top_k: int = 3,
        filters: Optional[str] = None,
    ) -> List[SearchResult]:
        """執行向量搜索"""
        vector_query = VectorizedQuery(
            vector=vector,
            k_nearest_neighbors=top_k,
            fields="utterance_vector",
        )

        results = self._client.search(
            search_text=None,
            vector_queries=[vector_query],
            filter=filters,
            select=["id", "route_name", "category", "sub_intent", "utterance", "workflow_type", "risk_level"],
        )

        return [self._to_search_result(r) for r in results]

    async def hybrid_search(
        self,
        query: str,
        vector: List[float],
        top_k: int = 3,
    ) -> List[SearchResult]:
        """執行混合搜索 (文字 + 向量)"""
        ...

    async def upsert_route(self, route: SemanticRoute) -> bool:
        """新增或更新路由"""
        ...

    async def delete_route(self, route_id: str) -> bool:
        """刪除路由"""
        ...
```

**驗收標準**:
- [ ] 向量搜索功能正常
- [ ] 混合搜索功能正常
- [ ] CRUD 操作正常
- [ ] 錯誤處理完整

### Story 108-2: EmbeddingService 整合 (3h, P0)

**目標**: 整合 Azure OpenAI Embedding 服務

**交付物**:
- `backend/src/integrations/orchestration/intent_router/semantic_router/embedding_service.py`

**核心實現**:
```python
from openai import AzureOpenAI

class EmbeddingService:
    """Azure OpenAI Embedding 服務"""

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        deployment_name: str = "text-embedding-ada-002",
    ):
        self._client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version="2024-02-15-preview",
        )
        self._deployment = deployment_name
        self._cache: Dict[str, List[float]] = {}

    async def get_embedding(self, text: str) -> List[float]:
        """獲取文字的 embedding 向量"""
        # 檢查快取
        cache_key = hashlib.md5(text.encode()).hexdigest()
        if cache_key in self._cache:
            return self._cache[cache_key]

        response = self._client.embeddings.create(
            model=self._deployment,
            input=text,
        )

        embedding = response.data[0].embedding
        self._cache[cache_key] = embedding
        return embedding

    async def get_embeddings_batch(
        self,
        texts: List[str],
    ) -> List[List[float]]:
        """批量獲取 embeddings"""
        ...
```

**驗收標準**:
- [ ] Embedding 生成正確
- [ ] 快取機制工作
- [ ] 批量處理支援
- [ ] 錯誤處理完整

### Story 108-3: AzureSemanticRouter 實現 (6h, P0)

**目標**: 實現基於 Azure AI Search 的語義路由器

**交付物**:
- `backend/src/integrations/orchestration/intent_router/semantic_router/azure_router.py`

**核心實現**:
```python
class AzureSemanticRouter:
    """基於 Azure AI Search 的語義路由器"""

    def __init__(
        self,
        search_client: AzureSearchClient,
        embedding_service: EmbeddingService,
        threshold: float = 0.85,
        top_k: int = 3,
    ):
        self._search_client = search_client
        self._embedding_service = embedding_service
        self._threshold = threshold
        self._top_k = top_k

    async def route(self, query: str) -> SemanticRouteResult:
        """執行語義路由"""
        # 1. 生成查詢向量
        query_vector = await self._embedding_service.get_embedding(query)

        # 2. 執行向量搜索
        results = await self._search_client.vector_search(
            vector=query_vector,
            top_k=self._top_k,
            filters="enabled eq true",
        )

        # 3. 檢查相似度閾值
        if not results or results[0].score < self._threshold:
            return SemanticRouteResult(matched=False)

        # 4. 返回最佳匹配
        best_match = results[0]
        return SemanticRouteResult(
            matched=True,
            route_name=best_match.route_name,
            intent_category=ITIntentCategory(best_match.category),
            sub_intent=best_match.sub_intent,
            similarity=best_match.score,
            workflow_type=WorkflowType(best_match.workflow_type),
            risk_level=RiskLevel(best_match.risk_level),
        )

    @property
    def routes(self) -> List[SemanticRoute]:
        """獲取所有路由 (延遲載入)"""
        ...
```

**驗收標準**:
- [ ] 語義路由功能正常
- [ ] 閾值過濾正確
- [ ] 結果格式正確
- [ ] 與現有介面相容

### Story 108-4: 整合 BusinessIntentRouter (4h, P0)

**目標**: 將 AzureSemanticRouter 整合到現有路由系統

**交付物**:
- 修改 `backend/src/integrations/orchestration/intent_router/router.py`
- 修改 `backend/src/api/v1/orchestration/intent_routes.py`

**整合方式**:
```python
def create_router(
    pattern_rules_path: Optional[str] = None,
    semantic_routes: Optional[List[SemanticRoute]] = None,
    llm_api_key: Optional[str] = None,
    config: Optional[RouterConfig] = None,
    use_azure_search: bool = False,  # 新增參數
) -> BusinessIntentRouter:
    """創建路由器實例"""

    # 根據配置選擇語義路由器
    if use_azure_search:
        semantic_router = AzureSemanticRouter(
            search_client=AzureSearchClient(...),
            embedding_service=EmbeddingService(...),
        )
    else:
        semantic_router = SemanticRouter(routes=semantic_routes)

    return BusinessIntentRouter(
        pattern_matcher=pattern_matcher,
        semantic_router=semantic_router,
        llm_classifier=llm_classifier,
        config=config,
    )
```

**驗收標準**:
- [ ] 無縫切換 Azure/內存路由器
- [ ] 三層路由系統正常工作
- [ ] 環境變量控制切換
- [ ] 向後相容

### Story 108-5: Fallback 機制 (4h, P1)

**目標**: 實現 Azure Search 失敗時的 fallback

**交付物**:
- `backend/src/integrations/orchestration/intent_router/semantic_router/fallback_router.py`

**Fallback 策略**:
1. Azure Search 超時 → 跳過語義層，使用 LLM
2. Azure Search 錯誤 → 記錄錯誤，跳過語義層
3. 連接失敗 → 切換到內存路由器 (如有快取)

**驗收標準**:
- [ ] 超時處理正確
- [ ] 錯誤降級正常
- [ ] 日誌記錄完整
- [ ] 不影響用戶體驗

### Story 108-6: 單元測試 (4h, P0)

**目標**: 為所有組件編寫測試

**交付物**:
- `backend/tests/unit/orchestration/semantic_router/test_azure_search_client.py`
- `backend/tests/unit/orchestration/semantic_router/test_embedding_service.py`
- `backend/tests/unit/orchestration/semantic_router/test_azure_router.py`

**驗收標準**:
- [ ] 測試覆蓋率 > 85%
- [ ] 所有測試通過
- [ ] Mock Azure 服務

## 技術設計

### 類圖

```
┌─────────────────────┐
│ BusinessIntentRouter│
├─────────────────────┤
│ - pattern_matcher   │
│ - semantic_router   │◄───────┐
│ - llm_classifier    │        │
└─────────────────────┘        │
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
┌───────────────┐    ┌──────────────────┐    ┌────────────────┐
│SemanticRouter │    │AzureSemanticRouter│    │FallbackRouter  │
│ (內存實現)     │    │ (Azure 實現)      │    │ (降級實現)      │
├───────────────┤    ├──────────────────┤    ├────────────────┤
│ - routes      │    │ - search_client  │    │ - primary      │
│ - encoder     │    │ - embedding_svc  │    │ - fallback     │
└───────────────┘    └──────────────────┘    └────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
    ┌──────────────────┐            ┌──────────────────┐
    │AzureSearchClient │            │EmbeddingService  │
    ├──────────────────┤            ├──────────────────┤
    │ - vector_search  │            │ - get_embedding  │
    │ - hybrid_search  │            │ - cache          │
    │ - upsert_route   │            └──────────────────┘
    └──────────────────┘
```

## 依賴

```
azure-search-documents>=11.4.0
openai>=1.10.0
```

## 風險

| 風險 | 緩解措施 |
|------|---------|
| Azure Search 延遲高 | 設定合理 timeout，實現 fallback |
| Embedding 成本 | 實現快取機制 |
| 介面不相容 | 保持與現有 SemanticRouter 相同介面 |

## 完成標準

- [ ] AzureSearchClient 實現完成
- [ ] EmbeddingService 實現完成
- [ ] AzureSemanticRouter 實現完成
- [ ] BusinessIntentRouter 整合完成
- [ ] Fallback 機制實現
- [ ] 測試覆蓋率 > 85%

---

**Sprint 開始**: TBD
**Sprint 結束**: TBD + 5 days
**Story Points**: 25
