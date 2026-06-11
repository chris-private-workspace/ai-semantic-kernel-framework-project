# Sprint 109: 路由管理 API + 資料遷移

## 概述

Sprint 109 專注於實現路由管理 API 和將現有 15 條語義路由遷移到 Azure AI Search。

## 目標

1. 實現路由管理 CRUD API
2. 實現 YAML → Azure 同步功能
3. 遷移現有 15 條路由
4. 實現路由搜索測試 API
5. 驗證遷移完整性

## Story Points: 20 點

## 前置條件

- ✅ Sprint 108 完成 (AzureSemanticRouter)
- ✅ Azure AI Search 索引就緒
- ✅ EmbeddingService 可用

## 任務分解

### Story 109-1: 路由管理 Service (4h, P0)

**目標**: 實現路由管理的業務邏輯

**交付物**:
- `backend/src/integrations/orchestration/intent_router/semantic_router/route_manager.py`

**核心實現**:
```python
class RouteManager:
    """語義路由管理器"""

    def __init__(
        self,
        search_client: AzureSearchClient,
        embedding_service: EmbeddingService,
    ):
        self._search_client = search_client
        self._embedding_service = embedding_service

    async def create_route(self, route: SemanticRouteCreate) -> SemanticRoute:
        """創建新路由"""
        # 1. 生成 utterance embedding
        embedding = await self._embedding_service.get_embedding(route.utterance)

        # 2. 創建路由文檔
        doc = {
            "id": str(uuid.uuid4()),
            "route_name": route.route_name,
            "category": route.category.value,
            "sub_intent": route.sub_intent,
            "utterance": route.utterance,
            "utterance_vector": embedding,
            "workflow_type": route.workflow_type.value,
            "risk_level": route.risk_level.value,
            "description": route.description,
            "enabled": True,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        # 3. 上傳到 Azure Search
        await self._search_client.upsert_route(doc)

        return SemanticRoute(**doc)

    async def update_route(
        self,
        route_id: str,
        updates: SemanticRouteUpdate,
    ) -> SemanticRoute:
        """更新路由"""
        ...

    async def delete_route(self, route_id: str) -> bool:
        """刪除路由"""
        ...

    async def list_routes(
        self,
        category: Optional[str] = None,
        enabled: Optional[bool] = None,
    ) -> List[SemanticRoute]:
        """列出路由"""
        ...

    async def sync_from_yaml(self, yaml_path: str) -> SyncResult:
        """從 YAML 文件同步路由"""
        ...
```

**驗收標準**:
- [ ] CRUD 操作正常
- [ ] Embedding 自動生成
- [ ] 同步功能正常
- [ ] 錯誤處理完整

### Story 109-2: 路由管理 API (4h, P0)

**目標**: 實現 RESTful API 端點

**交付物**:
- `backend/src/api/v1/orchestration/route_routes.py`
- `backend/src/api/v1/orchestration/route_schemas.py`

**API 端點**:
```python
route_router = APIRouter(prefix="/orchestration/routes", tags=["Route Management"])

@route_router.post("", response_model=SemanticRouteResponse)
async def create_route(route: SemanticRouteCreate) -> SemanticRouteResponse:
    """新增語義路由"""
    ...

@route_router.get("", response_model=List[SemanticRouteResponse])
async def list_routes(
    category: Optional[str] = None,
    enabled: Optional[bool] = None,
) -> List[SemanticRouteResponse]:
    """列出語義路由"""
    ...

@route_router.get("/{route_id}", response_model=SemanticRouteResponse)
async def get_route(route_id: str) -> SemanticRouteResponse:
    """獲取單個路由"""
    ...

@route_router.put("/{route_id}", response_model=SemanticRouteResponse)
async def update_route(
    route_id: str,
    updates: SemanticRouteUpdate,
) -> SemanticRouteResponse:
    """更新路由"""
    ...

@route_router.delete("/{route_id}")
async def delete_route(route_id: str) -> dict:
    """刪除路由"""
    ...

@route_router.post("/sync", response_model=SyncResultResponse)
async def sync_routes() -> SyncResultResponse:
    """從 YAML 同步路由到 Azure"""
    ...

@route_router.post("/search", response_model=SearchResultResponse)
async def test_search(query: str, top_k: int = 3) -> SearchResultResponse:
    """測試語義搜索"""
    ...
```

**驗收標準**:
- [ ] 所有 API 端點正常
- [ ] 請求驗證正確
- [ ] 響應格式正確
- [ ] OpenAPI 文檔完整

### Story 109-3: 資料遷移腳本 (3h, P0)

**目標**: 將現有 15 條路由遷移到 Azure

**交付物**:
- `backend/scripts/migrate_routes_to_azure.py`

**遷移步驟**:
```python
async def migrate_routes():
    """遷移語義路由到 Azure AI Search"""

    # 1. 讀取現有路由
    from src.integrations.orchestration.intent_router.semantic_router.routes import (
        get_default_routes,
    )
    routes = get_default_routes()
    logger.info(f"Found {len(routes)} routes to migrate")

    # 2. 初始化服務
    route_manager = RouteManager(...)

    # 3. 批量遷移
    success_count = 0
    for route in routes:
        try:
            await route_manager.create_route(route)
            success_count += 1
            logger.info(f"Migrated: {route.name}")
        except Exception as e:
            logger.error(f"Failed to migrate {route.name}: {e}")

    # 4. 驗證遷移
    migrated = await route_manager.list_routes()
    logger.info(f"Migration complete: {success_count}/{len(routes)} routes")

    return success_count
```

**驗收標準**:
- [ ] 15 條路由全部遷移
- [ ] Embedding 正確生成
- [ ] 可在 Azure Portal 查看
- [ ] 遷移日誌完整

### Story 109-4: 驗證遷移 (2h, P0)

**目標**: 驗證遷移後的路由功能正常

**交付物**:
- `backend/scripts/verify_migration.py`

**驗證內容**:
1. 路由數量正確 (15 條)
2. 每條路由的欄位完整
3. 向量搜索功能正常
4. 與原路由結果一致

**測試用例**:
```python
TEST_QUERIES = [
    ("ETL Pipeline 今天跑失敗了", "etl_failure", "INCIDENT"),
    ("我需要申請一個新帳號", "account_creation", "REQUEST"),
    ("系統很慢，效能問題", "performance_issue", "INCIDENT"),
]
```

**驗收標準**:
- [ ] 所有驗證通過
- [ ] 結果與原實現一致
- [ ] 驗證報告完整

### Story 109-5: API 整合測試 (3h, P0)

**目標**: 為路由管理 API 編寫整合測試

**交付物**:
- `backend/tests/integration/orchestration/test_route_api.py`

**驗收標準**:
- [ ] 所有 API 測試通過
- [ ] 錯誤場景覆蓋
- [ ] 測試覆蓋率 > 85%

### Story 109-6: 文檔更新 (4h, P1)

**目標**: 更新相關文檔

**交付物**:
- 更新 `docs/api/orchestration-api-reference.md`
- 創建 `docs/06-user-guide/route-management.md`

**驗收標準**:
- [ ] API 參考文檔完整
- [ ] 使用指南清晰
- [ ] 包含範例

## 技術設計

### 資料模型

```python
class SemanticRouteCreate(BaseModel):
    """創建路由請求"""
    route_name: str
    category: ITIntentCategory
    sub_intent: str
    utterance: str
    workflow_type: WorkflowType
    risk_level: RiskLevel
    description: Optional[str] = None

class SemanticRouteUpdate(BaseModel):
    """更新路由請求"""
    utterance: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    risk_level: Optional[RiskLevel] = None

class SemanticRouteResponse(BaseModel):
    """路由響應"""
    id: str
    route_name: str
    category: str
    sub_intent: str
    utterance: str
    workflow_type: str
    risk_level: str
    description: Optional[str]
    enabled: bool
    created_at: datetime
    updated_at: datetime
```

### 遷移流程

```
┌─────────────────┐
│  routes.py      │
│  (15 條路由)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ migrate_routes  │
│ _to_azure.py    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ EmbeddingService│────►│ Azure OpenAI    │
│ (生成向量)       │     │ (Embedding API) │
└────────┬────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ RouteManager    │────►│ Azure AI Search │
│ (上傳文檔)       │     │ (semantic-routes)│
└─────────────────┘     └─────────────────┘
```

## 依賴

```
pydantic>=2.0.0
```

## 風險

| 風險 | 緩解措施 |
|------|---------|
| 遷移中斷 | 支援增量遷移，記錄已完成項目 |
| Embedding 不一致 | 使用相同的 embedding 模型 |
| API 權限問題 | 確認 Azure 權限設定 |

## 完成標準

- [ ] 路由管理 API 全部實現
- [ ] 15 條路由成功遷移
- [ ] 遷移驗證通過
- [ ] 整合測試通過
- [ ] 文檔更新完成

---

**Sprint 開始**: TBD
**Sprint 結束**: TBD + 4 days
**Story Points**: 20
