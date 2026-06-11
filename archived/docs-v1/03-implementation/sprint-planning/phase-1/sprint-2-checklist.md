# Sprint 2 Checklist: 工作流 & 檢查點 - Human-in-the-Loop

**Sprint 目標**: 實現檢查點機制和跨系統集成，支持人機協作流程
**週期**: Week 5-6
**總點數**: 45 點
**MVP 功能**: F2, F3, F14

---

## ✅ Sprint 2 完成總覽

| 項目 | 狀態 |
|------|------|
| **完成日期** | 2025-11-30 |
| **完成點數** | 45/45 (100%) |
| **測試總數** | 158 個 |
| **測試通過** | 100% |

| Story | 描述 | 點數 | 狀態 |
|-------|------|------|------|
| S2-1 | 檢查點機制實現 | 13 | ✅ 完成 |
| S2-2 | 人機協作審批流程 | 13 | ✅ 完成 |
| S2-3 | 跨系統連接器 | 10 | ✅ 完成 |
| S2-4 | Redis 緩存實現 | 9 | ✅ 完成 |

---

## 快速驗證命令

```bash
# 驗證檢查點 API
curl http://localhost:8000/api/v1/checkpoints/pending

# 驗證審批流程
curl -X POST http://localhost:8000/api/v1/checkpoints/{id}/approve

# 驗證緩存統計
curl http://localhost:8000/api/v1/cache/stats

# 運行測試
cd backend && pytest tests/unit/test_checkpoint*.py tests/unit/test_llm_cache.py -v
```

---

## S2-1: 檢查點機制實現 (13 點) ✅ 完成

### 檢查點存儲
- [x] 創建 `src/domain/checkpoints/` 目錄
- [x] 創建 `storage.py`
  - [x] DatabaseCheckpointStorage 類
    - [x] save_checkpoint() 方法
    - [x] load_checkpoint() 方法
    - [x] list_checkpoints() 方法
    - [x] _determine_status() 方法
  - [x] CheckpointService 類
    - [x] get_pending_approvals() 方法
    - [x] approve_checkpoint() 方法
    - [x] reject_checkpoint() 方法

### 數據庫模型
- [x] 更新 CheckpointModel
  - [x] 添加 state JSONB 欄位
  - [x] 添加 approved_by 外鍵
  - [x] 添加 feedback 欄位
  - [x] 添加索引

### 檢查點 API
- [x] 創建 `src/api/v1/checkpoints/routes.py`
  - [x] GET /checkpoints/pending - 待審批列表
  - [x] GET /checkpoints/{id} - 檢查點詳情
  - [x] POST /checkpoints/{id}/approve - 審批通過
  - [x] POST /checkpoints/{id}/reject - 審批拒絕
- [x] 創建請求/響應 Schema
  - [x] CheckpointResponse
  - [x] ApprovalRequest
  - [x] RejectionRequest

### 驗證標準
- [x] 檢查點保存後可從數據庫查詢
- [x] 檢查點狀態正確更新 (pending → approved/rejected)
- [x] 文件存儲與數據庫同步
- [x] API 響應格式正確

### 測試統計
- 28 個單元測試通過 (test_checkpoint_service.py)

---

## S2-2: 人機協作審批流程 (13 點) ✅ 完成

### 審批網關執行器
- [x] 創建 `src/domain/workflows/executors/approval.py`
  - [x] HumanApprovalRequest 數據類
    - [x] prompt 欄位
    - [x] content 欄位
    - [x] context 欄位
    - [x] iteration 欄位
  - [x] ApprovalGateway 類
    - [x] on_agent_response() 處理器
    - [x] on_human_feedback() 響應處理器
    - [x] on_checkpoint_save() 狀態保存
    - [x] on_checkpoint_restore() 狀態恢復

### 工作流恢復服務
- [x] 創建 `src/domain/workflows/resume_service.py`
  - [x] WorkflowResumeService 類
    - [x] resume_from_checkpoint() 方法
    - [x] resume_with_approval() 方法
- [x] 更新 WorkflowExecutionService
  - [x] get_workflow_for_execution() 方法
  - [x] update_execution_result() 方法

### 恢復 API
- [x] 添加 POST /executions/{id}/resume 端點
- [ ] 添加 WebSocket 支持 (可選) - 延後至 Sprint 4
  - [ ] 實時推送審批請求
  - [ ] 實時更新執行狀態

### 集成工作流
- [x] 更新 WorkflowBuilder 支持審批節點
- [x] 測試完整審批流程
  - [x] Agent 執行 → 暫停 → 審批 → 恢復

### 驗證標準
- [x] 工作流可在審批節點正確暫停
- [x] 審批通過後工作流正確恢復
- [x] 審批拒絕後工作流正確終止
- [x] 反饋可觸發重新處理

### 測試統計
- 24 個測試 (test_approval_gateway.py)
- 22 個測試 (test_workflow_resume_service.py)

---

## S2-3: 跨系統連接器 (10 點) ✅ 完成

### 連接器基礎架構
- [x] 創建 `src/domain/connectors/` 目錄
- [x] 創建 `base.py`
  - [x] ConnectorConfig 數據類
  - [x] ConnectorResponse 數據類
  - [x] ConnectorError 異常類
  - [x] ConnectorStatus 狀態枚舉
  - [x] AuthType 認證類型枚舉
  - [x] BaseConnector 抽象類
    - [x] name 屬性
    - [x] connect() 方法
    - [x] disconnect() 方法
    - [x] execute() 方法
    - [x] health_check() 方法

### ServiceNow 連接器
- [x] 創建 `servicenow.py`
  - [x] ServiceNowConnector 類
    - [x] _get_incident() 方法
    - [x] _list_incidents() 方法
    - [x] _create_incident() 方法
    - [x] _update_incident() 方法
    - [x] _get_change() 方法
    - [x] _list_changes() 方法
    - [x] _search_knowledge() 方法
- [x] 創建 ServiceNow 工具
  - [x] get_incident() 函數
  - [x] search_incidents() 函數

### Dynamics 365 連接器 (基礎)
- [x] 創建 `dynamics365.py`
  - [x] Dynamics365Connector 類
    - [x] OAuth2 認證
    - [x] get_customer() 方法
    - [x] search_customers() 方法
    - [x] get_cases() 方法
    - [x] create_case() 方法
    - [x] update_case() 方法

### SharePoint 連接器 (基礎)
- [x] 創建 `sharepoint.py`
  - [x] SharePointConnector 類
    - [x] list_documents() 方法
    - [x] get_document() 方法
    - [x] search_documents() 方法
    - [x] download_document() 方法
    - [x] upload_document() 方法

### 連接器管理
- [x] 創建 `registry.py`
  - [x] ConnectorRegistry 類
  - [x] 連接器配置管理
  - [x] connect_all() 方法
  - [x] health_check_all() 方法
- [x] 連接器健康檢查 API
  - [x] GET /connectors/health
  - [x] GET /connectors - 列出連接器
  - [x] GET /connectors/types - 連接器類型
  - [x] POST /connectors/{name}/execute - 執行操作

### 驗證標準
- [x] ServiceNow 工單查詢正常
- [x] 連接器錯誤正確處理並返回
- [x] Agent 可調用連接器工具
- [x] 配置變更無需重啟

### 測試統計
- 51 個單元測試通過 (test_connectors.py)

---

## S2-4: Redis 緩存實現 (9 點) ✅ 完成

### LLM 緩存服務
- [x] 創建 `src/infrastructure/cache/llm_cache.py`
  - [x] CacheEntry 數據類
  - [x] CacheStats 數據類
  - [x] LLMCacheService 類
    - [x] _generate_key() 方法 (SHA256)
    - [x] get() 方法
    - [x] set() 方法
    - [x] delete() 方法
    - [x] clear() 方法
    - [x] get_stats() 方法
    - [x] reset_stats() 方法
    - [x] warm_cache() 方法
    - [x] enable()/disable() 方法
  - [x] CachedAgentService 類
    - [x] 包裝原始 AgentService
    - [x] 自動緩存邏輯
    - [x] bypass_cache 選項

### 緩存配置
- [x] 添加環境變量
  - [x] CACHE_TTL_SECONDS (預設 3600)
  - [x] CACHE_ENABLED (預設 True)
- [ ] 更新 Settings 類 - 延後 (使用 DI 注入)

### 緩存 API
- [x] 創建 `src/api/v1/cache/routes.py`
  - [x] GET /cache/stats - 緩存統計
  - [x] GET /cache/config - 緩存配置
  - [x] POST /cache/enable - 啟用緩存
  - [x] POST /cache/disable - 停用緩存
  - [x] POST /cache/get - 取得緩存項目
  - [x] POST /cache/set - 設定緩存項目
  - [x] POST /cache/clear - 清除緩存
  - [x] POST /cache/warm - 預熱緩存
  - [x] POST /cache/reset-stats - 重置統計
- [x] 創建 Pydantic schemas
  - [x] CacheStatsResponse
  - [x] CacheEntryResponse
  - [x] CacheSetRequest
  - [x] CacheGetRequest
  - [x] CacheClearRequest/Response
  - [x] CacheWarmRequest/Response
  - [x] CacheConfigResponse

### 集成 Agent 服務
- [x] CachedAgentService 包裝器
- [x] 添加緩存繞過選項 (bypass_cache)
- [x] 記錄緩存命中日誌

### 驗證標準
- [x] 相同輸入命中緩存
- [x] 緩存 TTL 正確生效
- [x] 緩存統計準確
- [x] 命中率達到 60%+ (測試場景驗證)

### 測試統計
- 33 個單元測試通過 (test_llm_cache.py)

---

## 測試完成 ✅

### 單元測試
- [x] test_checkpoint_service.py (28 tests)
  - [x] test_save_checkpoint
  - [x] test_load_checkpoint
  - [x] test_list_checkpoints
- [x] test_approval_gateway.py (24 tests)
  - [x] test_on_agent_response
  - [x] test_on_human_feedback_approve
  - [x] test_on_human_feedback_reject
- [x] test_workflow_resume_service.py (22 tests)
  - [x] test_resume_from_checkpoint
  - [x] test_resume_with_approval
  - [x] test_cancel_paused_execution
- [x] test_connectors.py (51 tests)
  - [x] test_servicenow_get_incident
  - [x] test_servicenow_list_incidents
  - [x] test_connector_error_handling
  - [x] test_dynamics365_operations
  - [x] test_sharepoint_operations
  - [x] test_connector_registry
- [x] test_llm_cache.py (33 tests)
  - [x] test_cache_hit
  - [x] test_cache_miss
  - [x] test_cache_stats
  - [x] test_cache_clear
  - [x] test_cached_agent_service

### 集成測試
- [ ] test_human_in_the_loop.py - 延後至 Sprint 5
  - [ ] test_workflow_pause_at_approval
  - [ ] test_workflow_resume_after_approval
  - [ ] test_workflow_reject_terminates
- [ ] test_cached_agent.py - 延後至 Sprint 5
  - [ ] test_cached_response
  - [ ] test_cache_bypass

### 覆蓋率
- [x] 單元測試覆蓋率 >= 80% (模組內)
- [x] 關鍵路徑 100% 覆蓋

### 測試統計總覽
| 測試文件 | 測試數量 | 狀態 |
|---------|---------|------|
| test_checkpoint_service.py | 28 | ✅ |
| test_approval_gateway.py | 24 | ✅ |
| test_workflow_resume_service.py | 22 | ✅ |
| test_connectors.py | 51 | ✅ |
| test_llm_cache.py | 33 | ✅ |
| **Sprint 2 總計** | **158** | **100%** |

---

## 文檔完成

### API 文檔
- [ ] 檢查點 API 文檔
- [ ] 連接器配置文檔
- [ ] 緩存 API 文檔

### 開發者文檔
- [ ] 人機協作開發指南
  - [ ] 配置審批節點
  - [ ] 處理審批響應
  - [ ] 自定義審批邏輯
- [ ] 連接器開發指南
  - [ ] 創建自定義連接器
  - [ ] 認證配置
  - [ ] 錯誤處理
- [ ] 緩存調優指南
  - [ ] TTL 設置建議
  - [ ] 緩存失效策略

---

## 每日站會檢查點

### Day 1
- [ ] CheckpointService 基礎結構
- [ ] 數據庫模型更新

### Day 2
- [ ] 檢查點存儲適配器完成
- [ ] 檢查點 API 端點

### Day 3
- [ ] ApprovalGateway 實現
- [ ] 審批請求發送邏輯

### Day 4
- [ ] 審批響應處理
- [ ] WorkflowResumeService

### Day 5
- [ ] 完整審批流程測試
- [ ] 恢復 API

### Day 6
- [ ] 連接器基類
- [ ] ServiceNow 連接器

### Day 7
- [ ] Dynamics 365 連接器
- [ ] SharePoint 連接器

### Day 8
- [ ] 連接器工具集成
- [ ] LLM 緩存服務

### Day 9
- [ ] 緩存 API
- [ ] Agent 緩存集成

### Day 10
- [ ] 集成測試
- [ ] 文檔完善
- [ ] Sprint 回顧

---

## Sprint 完成標準 ✅ 全部達成

### 必須完成 (Must Have)
- [x] 檢查點保存/恢復正常
- [x] 人工審批流程完整
- [x] ServiceNow 連接器可用
- [x] Redis 緩存生效
- [x] 測試覆蓋率 >= 80% (模組內)

### 應該完成 (Should Have)
- [x] Dynamics 365 連接器
- [x] SharePoint 連接器
- [x] 緩存命中率 60%+ (測試驗證)

### 可以延後 (Could Have)
- [ ] WebSocket 實時通知 - 延後至 Sprint 4
- [ ] 連接器市場 UI - 延後至 Sprint 4

---

## 依賴確認 ✅

### 前置 Sprint
- [x] Sprint 1 完成
  - [x] Agent 執行正常
  - [x] Workflow 順序執行正常
  - [x] 工具調用正常

### 外部依賴
- [x] ServiceNow 測試實例 (Mock 模式開發)
- [x] Dynamics 365 測試租戶 (Mock 模式開發)
- [x] Redis 7+ 運行正常 (Docker Compose)

---

## 相關連結

- [Sprint 2 Plan](./sprint-2-plan.md) - 詳細計劃
- [Sprint 1 Checklist](./sprint-1-checklist.md) - 前置 Sprint
- [Sprint 3 Plan](./sprint-3-plan.md) - 後續 Sprint
- [Agent Framework Checkpoint 參考](../../../reference/agent-framework/python/samples/getting_started/workflows/checkpoint/)
