# Sprint 118 Checklist: E2E 測試 + Phase B 驗收

## 開發任務

### Story 118-1: AD 場景端到端測試
- [ ] 創建 `backend/tests/e2e/orchestration/` 目錄（如不存在）
- [ ] 創建 `conftest.py`
  - [ ] mock_ldap fixture（模擬 LDAP MCP 操作）
  - [ ] mock_servicenow fixture（模擬 ServiceNow MCP 操作）
  - [ ] mock_ldap_fail fixture（模擬 LDAP 故障）
  - [ ] mock_sn_fail fixture（模擬 ServiceNow 故障）
  - [ ] test_client fixture（FastAPI TestClient）
  - [ ] webhook_auth fixture（Webhook 認證 headers）
- [ ] 創建 `test_ad_scenario_fixtures.py`
  - [ ] 帳號解鎖 RITM payload
  - [ ] 密碼重設 RITM payload
  - [ ] 群組異動 RITM payload
  - [ ] 未知 Catalog Item RITM payload
- [ ] 創建 `test_ad_scenario_e2e.py`
  - [ ] `test_account_unlock_full_flow`
    - [ ] Step 1: ServiceNow Webhook 接收 RITM
    - [ ] Step 2: RITM 映射為 ad.account.unlock intent
    - [ ] Step 3: PatternMatcher 匹配成功
    - [ ] Step 4: Agent 選擇和執行
    - [ ] Step 5: LDAP MCP unlock 調用驗證
    - [ ] Step 6: ServiceNow RITM 關閉驗證
  - [ ] `test_password_reset_full_flow`
    - [ ] 完整密碼重設流程
    - [ ] 驗證 LDAP reset 調用
  - [ ] `test_group_membership_change_full_flow`
    - [ ] 群組異動流程（含審批步驟）
    - [ ] 驗證 LDAP group modify 調用
  - [ ] `test_unknown_ritm_fallback_to_semantic_router`
    - [ ] 未知 Catalog Item 觸發 SemanticRouter
    - [ ] 驗證 fallback 行為正確
  - [ ] `test_ritm_idempotency`
    - [ ] 相同 RITM 發送兩次
    - [ ] 驗證只執行一次
  - [ ] `test_ldap_failure_error_handling`
    - [ ] LDAP 操作失敗
    - [ ] 驗證錯誤被正確回報
    - [ ] 驗證 RITM 狀態更新為失敗
  - [ ] `test_servicenow_failure_graceful_degradation`
    - [ ] ServiceNow 不可用
    - [ ] 驗證 AD 操作仍然執行
    - [ ] 驗證失敗被記錄

### Story 118-2: Azure AI Search 整合測試 + 監控驗證
- [ ] 創建 `test_semantic_routing_e2e.py`
  - [ ] `test_full_routing_flow_with_azure`
    - [ ] 自然語言 → 三層路由 → 正確 intent
  - [ ] `test_ad_scenario_routing_accuracy`
    - [ ] 10+ 個 AD 相關測試查詢
    - [ ] 驗證 Top-1 精度 > 90%
  - [ ] `test_routing_fallback_chain`
    - [ ] L1 匹配 → 直接返回
    - [ ] L1 miss → L2 匹配 → 返回
    - [ ] L1+L2 miss → L3 分類 → 返回
  - [ ] `test_azure_search_unavailable_fallback`
    - [ ] Mock Azure Search 不可用
    - [ ] 驗證 fallback 到 Mock SemanticRouter
    - [ ] 驗證服務不中斷
  - [ ] `test_route_management_crud`
    - [ ] 新增路由 → 搜索驗證
    - [ ] 更新路由 → 搜索驗證
    - [ ] 刪除路由 → 搜索驗證
- [ ] 創建 `test_routing_performance.py`
  - [ ] `test_pattern_matcher_latency`
    - [ ] 100 次測試取 P95
    - [ ] 目標: < 5ms
  - [ ] `test_semantic_router_latency`
    - [ ] 50 次測試取 P95
    - [ ] 目標: < 100ms
  - [ ] `test_full_routing_latency`
    - [ ] 50 次測試取 P95
    - [ ] 目標: < 150ms
  - [ ] `test_concurrent_routing`
    - [ ] 10 並發請求
    - [ ] 目標: > 50 req/s
  - [ ] `test_embedding_cache_effectiveness`
    - [ ] 重複查詢 20 次
    - [ ] 驗證快取命中率 > 50%

### Story 118-3: Phase 32 性能基準 + 驗收報告
- [ ] 創建 `performance-report.md`
  - [ ] 路由性能表（PatternMatcher / SemanticRouter / 完整路由）
  - [ ] AD 場景性能表（帳號解鎖 / 密碼重設 / 群組異動）
  - [ ] 路由精度表（AD 場景 / 一般 IT / 總計）
  - [ ] 並發吞吐量數據
  - [ ] Embedding 快取效率
  - [ ] 與 Phase 28 基線比較
- [ ] 創建 `acceptance-report.md`
  - [ ] 交付物清單及狀態（13 項）
  - [ ] 成功標準達成狀態
  - [ ] 業務價值驗證（月節省、ROI、路由覆蓋率）
  - [ ] 已知問題和技術債
  - [ ] Phase 33 建議和接續事項
  - [ ] Sprint 114-118 完成時間和 velocity

## 品質檢查

### 測試品質
- [ ] E2E 測試覆蓋 3 個核心 AD 場景
- [ ] E2E 測試覆蓋 4 個異常場景
- [ ] 性能測試有明確的量化指標
- [ ] 測試結果可重現
- [ ] 無 flaky tests

### 文檔品質
- [ ] 性能報告所有指標有實測數據
- [ ] 驗收報告所有交付物有明確狀態
- [ ] 業務價值有數據支撐
- [ ] 改善建議具體可行

### 回歸測試
- [ ] 執行 Phase 29 Swarm 相關測試 — 不受影響
- [ ] 執行 Phase 28 路由相關測試 — 不受影響（或有計劃的改進）
- [ ] 執行全域 pytest — 無新增失敗

## 驗收標準

- [ ] AD 帳號解鎖 E2E 測試通過
- [ ] AD 密碼重設 E2E 測試通過
- [ ] AD 群組異動 E2E 測試通過
- [ ] 異常處理測試通過（LDAP 故障、ServiceNow 故障、冪等）
- [ ] 語義路由精度 > 90%
- [ ] 路由延遲 < 150ms (P95)
- [ ] 性能基準報告完成
- [ ] 驗收報告完成
- [ ] Phase 32 所有成功標準達成（或有明確的差距說明）

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 35
**開始日期**: TBD
