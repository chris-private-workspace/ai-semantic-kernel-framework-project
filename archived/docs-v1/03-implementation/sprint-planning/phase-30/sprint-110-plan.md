# Sprint 110: 整合測試 + 監控 + 文檔

## 概述

Sprint 110 是 Phase 30 的最後一個 Sprint，專注於端到端測試、性能監控和完整文檔編寫。

## 目標

1. 編寫端到端整合測試
2. 實現搜索性能監控
3. 建立監控 Dashboard
4. 編寫完整技術文檔
5. 最終驗收測試

## Story Points: 15 點

## 前置條件

- ✅ Sprint 107-109 完成
- ✅ AzureSemanticRouter 運作正常
- ✅ 15 條路由已遷移

## 任務分解

### Story 110-1: 端到端測試 (4h, P0)

**目標**: 編寫完整的 E2E 測試套件

**交付物**:
- `backend/tests/e2e/orchestration/test_semantic_routing_e2e.py`

**測試場景**:
```python
class TestSemanticRoutingE2E:
    """語義路由端到端測試"""

    @pytest.mark.asyncio
    async def test_full_routing_flow(self, client):
        """測試完整路由流程"""
        # 1. 發送請求
        response = await client.post(
            "/api/v1/orchestration/intent/classify",
            json={"content": "ETL Pipeline 今天執行失敗了"},
        )
        assert response.status_code == 200

        # 2. 驗證結果
        result = response.json()
        assert result["routing_decision"]["intent_category"] == "INCIDENT"
        assert result["routing_decision"]["sub_intent"] == "etl_failure"
        assert result["routing_decision"]["routing_layer"] in ["pattern", "semantic"]

    @pytest.mark.asyncio
    async def test_azure_search_integration(self, client):
        """測試 Azure Search 整合"""
        # 1. 測試向量搜索
        response = await client.post(
            "/api/v1/orchestration/routes/search",
            json={"query": "我需要申請新帳號", "top_k": 3},
        )
        assert response.status_code == 200

        results = response.json()["results"]
        assert len(results) > 0
        assert results[0]["route_name"] == "account_creation_request"

    @pytest.mark.asyncio
    async def test_fallback_to_llm(self, client):
        """測試未匹配時 fallback 到 LLM"""
        response = await client.post(
            "/api/v1/orchestration/intent/classify",
            json={"content": "這是一個非常特殊的請求"},
        )
        assert response.status_code == 200

        result = response.json()
        assert result["routing_decision"]["routing_layer"] == "llm"

    @pytest.mark.asyncio
    async def test_route_management_crud(self, client):
        """測試路由管理 CRUD"""
        # 1. 創建路由
        create_response = await client.post(
            "/api/v1/orchestration/routes",
            json={
                "route_name": "test_route",
                "category": "REQUEST",
                "sub_intent": "test_intent",
                "utterance": "這是測試路由",
                "workflow_type": "STANDARD",
                "risk_level": "LOW",
            },
        )
        assert create_response.status_code == 200
        route_id = create_response.json()["id"]

        # 2. 獲取路由
        get_response = await client.get(f"/api/v1/orchestration/routes/{route_id}")
        assert get_response.status_code == 200

        # 3. 更新路由
        update_response = await client.put(
            f"/api/v1/orchestration/routes/{route_id}",
            json={"description": "Updated description"},
        )
        assert update_response.status_code == 200

        # 4. 刪除路由
        delete_response = await client.delete(f"/api/v1/orchestration/routes/{route_id}")
        assert delete_response.status_code == 200
```

**驗收標準**:
- [ ] 所有 E2E 測試通過
- [ ] 覆蓋主要使用場景
- [ ] 錯誤場景測試

### Story 110-2: 性能監控 (3h, P0)

**目標**: 實現搜索性能監控

**交付物**:
- `backend/src/integrations/orchestration/intent_router/semantic_router/metrics.py`

**監控指標**:
```python
from prometheus_client import Counter, Histogram, Gauge

# 搜索指標
SEARCH_REQUESTS = Counter(
    "semantic_router_search_total",
    "Total semantic search requests",
    ["status", "source"],
)

SEARCH_LATENCY = Histogram(
    "semantic_router_search_latency_seconds",
    "Semantic search latency",
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

SEARCH_SIMILARITY = Histogram(
    "semantic_router_search_similarity",
    "Search result similarity scores",
    buckets=[0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 1.0],
)

# Embedding 指標
EMBEDDING_LATENCY = Histogram(
    "semantic_router_embedding_latency_seconds",
    "Embedding generation latency",
)

EMBEDDING_CACHE_HITS = Counter(
    "semantic_router_embedding_cache_hits_total",
    "Embedding cache hits",
)

# 路由指標
ROUTES_COUNT = Gauge(
    "semantic_router_routes_total",
    "Total routes in Azure Search",
)

class SemanticRouterMetrics:
    """語義路由器監控"""

    @staticmethod
    def record_search(status: str, latency: float, similarity: float):
        """記錄搜索指標"""
        SEARCH_REQUESTS.labels(status=status, source="azure").inc()
        SEARCH_LATENCY.observe(latency)
        if similarity > 0:
            SEARCH_SIMILARITY.observe(similarity)

    @staticmethod
    def record_embedding(latency: float, cache_hit: bool):
        """記錄 Embedding 指標"""
        EMBEDDING_LATENCY.observe(latency)
        if cache_hit:
            EMBEDDING_CACHE_HITS.inc()
```

**驗收標準**:
- [ ] Prometheus 指標正確暴露
- [ ] 延遲指標準確
- [ ] 快取命中率追蹤

### Story 110-3: 監控 Dashboard (3h, P1)

**目標**: 建立 Grafana Dashboard

**交付物**:
- `infrastructure/grafana/dashboards/semantic-router.json`

**Dashboard 內容**:
1. 搜索請求量 (QPS)
2. 搜索延遲分佈 (P50, P95, P99)
3. 相似度分數分佈
4. Embedding 快取命中率
5. 路由匹配成功率
6. Azure Search 可用性

**驗收標準**:
- [ ] Dashboard 可視化完整
- [ ] 告警規則配置
- [ ] 文檔說明

### Story 110-4: 技術文檔 (3h, P0)

**目標**: 編寫完整技術文檔

**交付物**:
- `docs/03-implementation/phase-30-azure-search-integration.md`
- 更新 `docs/02-architecture/technical-architecture.md`

**文檔內容**:
1. 架構概述
2. 組件說明
3. 配置指南
4. 部署說明
5. 監控說明
6. 故障排除

**驗收標準**:
- [ ] 架構說明完整
- [ ] 配置文檔清晰
- [ ] 包含代碼範例

### Story 110-5: 最終驗收 (2h, P0)

**目標**: 執行最終驗收測試

**交付物**:
- `docs/03-implementation/sprint-planning/phase-30/acceptance-report.md`

**驗收清單**:

| 功能 | 驗收標準 | 通過 |
|------|---------|------|
| Azure AI Search | 資源正常運作 | [ ] |
| 索引結構 | 符合設計規格 | [ ] |
| 向量搜索 | 延遲 < 100ms (P95) | [ ] |
| 路由遷移 | 15 條路由完整 | [ ] |
| 路由管理 API | CRUD 全部通過 | [ ] |
| 整合路由 | 三層路由正常 | [ ] |
| Fallback | 錯誤降級正常 | [ ] |
| 監控 | Dashboard 可用 | [ ] |

**驗收標準**:
- [ ] 所有功能驗收通過
- [ ] 性能指標達標
- [ ] 文檔完整

## 技術設計

### 監控架構

```
┌─────────────────┐     ┌─────────────────┐
│AzureSemanticRouter│──►│ SemanticRouter  │
│                  │    │ Metrics         │
└─────────────────┘     └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │   Prometheus    │
                        │   /metrics      │
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │    Grafana      │
                        │   Dashboard     │
                        └─────────────────┘
```

### 性能目標

| 指標 | 目標值 |
|------|--------|
| 搜索延遲 P50 | < 50ms |
| 搜索延遲 P95 | < 100ms |
| 搜索延遲 P99 | < 200ms |
| Embedding 快取命中率 | > 60% |
| 路由匹配準確率 | > 95% |

## 依賴

```
prometheus-client>=0.17.0
```

## 風險

| 風險 | 緩解措施 |
|------|---------|
| 性能不達標 | 提早識別，優化搜索參數 |
| 監控遺漏 | 完整測試監控覆蓋 |
| 文檔過時 | 與代碼同步更新 |

## 完成標準

- [ ] E2E 測試全部通過
- [ ] 監控指標暴露
- [ ] Dashboard 可用
- [ ] 技術文檔完整
- [ ] 最終驗收通過

---

**Sprint 開始**: TBD
**Sprint 結束**: TBD + 3 days
**Story Points**: 15
