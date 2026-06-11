# Sprint 99: E2E 測試 + 性能優化 + 文檔

## 概述

Sprint 99 是 Phase 28 的最後一個 Sprint，專注於 **E2E 整合測試**、**性能優化** 和 **文檔更新**。

## 目標

1. E2E 整合測試
2. 性能測試和調優
3. 監控指標整合 (OpenTelemetry)
4. 文檔更新
5. API 文檔 (OpenAPI)

## Story Points: 20 點

## 前置條件

- ✅ Sprint 98 完成 (整合)
- ✅ 所有組件整合完成
- ✅ 基本功能測試通過

## 任務分解

### Story 99-1: E2E 整合測試 (5h, P0)

**目標**: 編寫完整的端到端整合測試

**交付物**:
- `backend/tests/integration/orchestration/test_e2e_routing.py`
- `backend/tests/integration/orchestration/test_e2e_dialog.py`
- `backend/tests/integration/orchestration/test_e2e_hitl.py`

**測試場景**:

| 場景 | 描述 | 預期結果 |
|------|------|---------|
| Pattern 直接匹配 | "ETL Pipeline 失敗了" | incident/etl_failure, < 50ms |
| Semantic 匹配 | "資料庫連線好像有問題" | incident/database_issue |
| LLM 分類 | "系統最近跑得不太順" | incident/performance_issue |
| 完整度不足 | "系統有問題" | 啟動 GuidedDialog |
| 增量更新 | 用戶回答 "ETL, 報錯" | sub_intent 細化為 etl_failure |
| 高風險審批 | incident/system_down | 啟動 HITL |
| 系統來源 | ServiceNow Webhook | < 10ms, 直接映射 |

**驗收標準**:
- [ ] 所有測試場景覆蓋
- [ ] 測試通過率 100%
- [ ] 無 flaky tests

### Story 99-2: 性能測試和調優 (4h, P1)

**目標**: 進行性能測試並優化瓶頸

**交付物**:
- `backend/tests/performance/test_routing_performance.py`
- 性能報告

**性能指標**:

| 組件 | 目標 P95 | 測試方法 |
|------|---------|---------|
| Pattern Matcher | < 10ms | 1000 次調用 |
| Semantic Router | < 100ms | 500 次調用 |
| LLM Classifier | < 2000ms | 100 次調用 |
| 整體 (無 LLM) | < 500ms | 500 次調用 |
| GuidedDialog 輪次 | < 3 輪 | 50 次對話 |

**優化項目**:
- [ ] Pattern 規則預編譯
- [ ] Semantic 向量快取
- [ ] LLM 回應快取
- [ ] 連接池優化

**驗收標準**:
- [ ] 所有指標達標
- [ ] 無明顯瓶頸
- [ ] 性能報告完成

### Story 99-3: 監控指標整合 (3h, P1)

**目標**: 整合 OpenTelemetry 監控

**交付物**:
- `backend/src/integrations/orchestration/metrics.py`

**監控指標**:

```python
# 路由指標
routing_requests_total = Counter(
    "orchestration_routing_requests_total",
    "Total routing requests",
    ["intent_category", "layer_used"]
)

routing_latency_seconds = Histogram(
    "orchestration_routing_latency_seconds",
    "Routing latency",
    ["layer_used"]
)

# 對話指標
dialog_rounds_total = Counter(
    "orchestration_dialog_rounds_total",
    "Total dialog rounds"
)

dialog_completion_rate = Gauge(
    "orchestration_dialog_completion_rate",
    "Dialog completion rate"
)

# HITL 指標
hitl_requests_total = Counter(
    "orchestration_hitl_requests_total",
    "Total HITL requests",
    ["risk_level", "status"]
)

hitl_approval_time_seconds = Histogram(
    "orchestration_hitl_approval_time_seconds",
    "HITL approval time"
)
```

**驗收標準**:
- [ ] 指標定義完成
- [ ] 指標收集正確
- [ ] Grafana Dashboard (可選)

### Story 99-4: 文檔更新 (3h, P1)

**目標**: 更新相關文檔

**交付物**:
- 更新 `docs/03-implementation/sprint-planning/README.md`
- 更新 `backend/CLAUDE.md`
- 新增 `docs/03-implementation/sprint-planning/phase-28/ARCHITECTURE.md`

**文檔內容**:
- [ ] Phase 28 架構說明
- [ ] 組件使用指南
- [ ] 配置說明
- [ ] 故障排除

**驗收標準**:
- [ ] 文檔完整
- [ ] 範例清晰
- [ ] 無過時資訊

### Story 99-5: API 文檔 (2h, P1)

**目標**: 完善 OpenAPI 文檔

**交付物**:
- 更新 API 路由的 docstrings
- `docs/api/orchestration-api-reference.md`

**API 文檔**:

```yaml
/api/v1/orchestration/intent/classify:
  post:
    summary: 意圖分類
    description: 使用三層路由對用戶輸入進行意圖分類
    requestBody:
      content:
        application/json:
          schema:
            type: object
            properties:
              content:
                type: string
                description: 用戶輸入
              source:
                type: string
                enum: [user, servicenow, prometheus]
    responses:
      200:
        description: 分類結果
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/RoutingDecision'
```

**驗收標準**:
- [ ] API 文檔完整
- [ ] 範例正確
- [ ] Swagger UI 可用

## 驗收檢查清單

### 功能驗收

- [ ] Pattern Matcher 覆蓋率 > 70%
- [ ] 三層路由整體準確率 > 95%
- [ ] 完整度閾值正確執行
- [ ] Guided Dialog 平均輪數 < 3
- [ ] 增量更新正確運作
- [ ] 系統來源簡化路徑正確
- [ ] HITL 審批流程端到端通過

### 性能驗收

- [ ] Pattern 層 P95 延遲 < 10ms
- [ ] Semantic 層 P95 延遲 < 100ms
- [ ] LLM 層 P95 延遲 < 2000ms
- [ ] 整體 P95 延遲 < 500ms (無 LLM)

### 整合驗收

- [ ] 與現有 HybridOrchestratorV2 整合成功
- [ ] FrameworkSelector 重命名無影響
- [ ] API 路由正常工作
- [ ] 審計日誌正確記錄
- [ ] 監控指標正確收集

## Phase 28 完成總結

### 交付物

| 組件 | 檔案數 | 測試覆蓋率 |
|------|--------|-----------|
| intent_router/ | 12 | > 90% |
| guided_dialog/ | 4 | > 90% |
| input_gateway/ | 7 | > 85% |
| risk_assessor/ | 3 | > 90% |
| hitl/ | 3 | > 85% |
| audit/ | 2 | > 80% |
| API routes | 4 | > 85% |
| **總計** | **35** | **> 87%** |

### Sprint 統計

| Sprint | Story Points | 狀態 |
|--------|--------------|------|
| Sprint 91 | 25 | ✅ |
| Sprint 92 | 30 | ✅ |
| Sprint 93 | 25 | ✅ |
| Sprint 94 | 30 | ✅ |
| Sprint 95 | 25 | ✅ |
| Sprint 96 | 25 | ✅ |
| Sprint 97 | 30 | ✅ |
| Sprint 98 | 25 | ✅ |
| Sprint 99 | 20 | ✅ |
| **總計** | **235** | **100%** |

## 完成標準

- [ ] 所有 Story 完成
- [ ] E2E 測試通過
- [ ] 性能指標達標
- [ ] 文檔更新完成
- [ ] 代碼審查通過
- [ ] Phase 28 Retrospective 完成

---

**Sprint 開始**: 2026-03-06
**Sprint 結束**: 2026-03-10
**Story Points**: 20

**Phase 28 完成日期**: 2026-03-10
**Phase 28 總 Story Points**: 235
