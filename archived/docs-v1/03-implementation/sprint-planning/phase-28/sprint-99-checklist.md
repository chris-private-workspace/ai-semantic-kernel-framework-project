# Sprint 99 Checklist: E2E 測試 + 性能優化 + 文檔

## 開發任務

### Story 99-1: E2E 整合測試
- [ ] 創建 `test_e2e_routing.py`
  - [ ] Pattern 直接匹配測試
  - [ ] Semantic 匹配測試
  - [ ] LLM 分類測試
- [ ] 創建 `test_e2e_dialog.py`
  - [ ] 完整度不足測試
  - [ ] 增量更新測試
  - [ ] 多輪對話測試
- [ ] 創建 `test_e2e_hitl.py`
  - [ ] 高風險審批測試
  - [ ] 審批超時測試
- [ ] 測試系統來源
  - [ ] ServiceNow Webhook 測試
  - [ ] Prometheus 告警測試
- [ ] 確認所有測試通過

### Story 99-2: 性能測試和調優
- [ ] 創建 `test_routing_performance.py`
- [ ] 測試 Pattern 層 P95 延遲 (< 10ms)
- [ ] 測試 Semantic 層 P95 延遲 (< 100ms)
- [ ] 測試 LLM 層 P95 延遲 (< 2000ms)
- [ ] 測試整體 P95 延遲 (無 LLM) (< 500ms)
- [ ] 優化項目
  - [ ] Pattern 規則預編譯
  - [ ] Semantic 向量快取
  - [ ] LLM 回應快取
  - [ ] 連接池優化
- [ ] 生成性能報告

### Story 99-3: 監控指標整合
- [ ] 創建 `metrics.py`
- [ ] 定義路由指標
  - [ ] routing_requests_total
  - [ ] routing_latency_seconds
- [ ] 定義對話指標
  - [ ] dialog_rounds_total
  - [ ] dialog_completion_rate
- [ ] 定義 HITL 指標
  - [ ] hitl_requests_total
  - [ ] hitl_approval_time_seconds
- [ ] 整合 OpenTelemetry
- [ ] 驗證指標收集正確

### Story 99-4: 文檔更新
- [ ] 更新 `sprint-planning/README.md`
  - [ ] 添加 Phase 28 到總覽
  - [ ] 更新總 Story Points
- [ ] 更新 `backend/CLAUDE.md`
  - [ ] 添加 orchestration 模組說明
- [ ] 創建 `ARCHITECTURE.md`
  - [ ] Phase 28 架構說明
  - [ ] 組件使用指南
  - [ ] 配置說明
  - [ ] 故障排除

### Story 99-5: API 文檔
- [ ] 更新 API docstrings
- [ ] 創建 `orchestration-api-reference.md`
- [ ] 驗證 Swagger UI
- [ ] 添加範例請求/回應

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

## Phase 28 完成確認

- [ ] 所有 9 個 Sprint 完成
- [ ] 總 235 Story Points 完成
- [ ] E2E 測試通過
- [ ] 性能指標達標
- [ ] 文檔更新完成
- [ ] 代碼審查通過
- [ ] Phase 28 Retrospective 完成

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 20

**Phase 28 完成日期**: 預計 2026-03-10
