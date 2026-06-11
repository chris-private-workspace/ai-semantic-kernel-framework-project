# Sprint 101 Checklist: Swarm 事件系統 + SSE 整合

## 開發任務

### Story 101-1: 定義 Swarm 事件類型
- [ ] 創建 `backend/src/integrations/swarm/events/` 目錄
- [ ] 創建 `__init__.py`
- [ ] 創建 `types.py`
- [ ] 定義 `SwarmCreatedPayload`
- [ ] 定義 `SwarmStatusUpdatePayload`
- [ ] 定義 `SwarmCompletedPayload`
- [ ] 定義 `WorkerStartedPayload`
- [ ] 定義 `WorkerProgressPayload`
- [ ] 定義 `WorkerThinkingPayload`
- [ ] 定義 `WorkerToolCallPayload`
- [ ] 定義 `WorkerMessagePayload`
- [ ] 定義 `WorkerCompletedPayload`
- [ ] 定義 `SwarmEventNames` 常量類
- [ ] 添加類型註解
- [ ] 編寫單元測試

### Story 101-2: 實現 SwarmEventEmitter
- [ ] 創建 `emitter.py`
- [ ] 實現 `SwarmEventEmitter` 類
- [ ] 實現 `start()` 方法
- [ ] 實現 `stop()` 方法
- [ ] 實現 `emit_swarm_created()` 方法
- [ ] 實現 `emit_swarm_status_update()` 方法
- [ ] 實現 `emit_swarm_completed()` 方法
- [ ] 實現 `emit_worker_started()` 方法
- [ ] 實現 `emit_worker_progress()` 方法
- [ ] 實現 `emit_worker_thinking()` 方法
- [ ] 實現 `emit_worker_tool_call()` 方法
- [ ] 實現 `emit_worker_completed()` 方法
- [ ] 實現事件節流邏輯
- [ ] 實現批量發送邏輯
- [ ] 實現 `_worker_to_summary()` 輔助方法

### Story 101-3: 整合 HybridEventBridge
- [ ] 修改 `bridge.py`
- [ ] 添加 `enable_swarm_events` 參數
- [ ] 添加 `_swarm_emitter` 屬性
- [ ] 實現 `configure_swarm_emitter()` 方法
- [ ] 添加 `swarm_emitter` 屬性
- [ ] 修改 `start()` 方法啟動 Swarm emitter
- [ ] 修改 `stop()` 方法停止 Swarm emitter
- [ ] 確保向後兼容

### Story 101-4: 前端 SSE 事件處理 Hook
- [ ] 創建 `frontend/src/components/unified-chat/agent-swarm/` 目錄
- [ ] 創建 `hooks/` 子目錄
- [ ] 創建 `types/index.ts` (事件類型定義)
- [ ] 創建 `useSwarmEvents.ts`
- [ ] 定義 `SwarmEventHandlers` 接口
- [ ] 實現事件監聽邏輯
- [ ] 實現事件分發邏輯
- [ ] 添加錯誤處理
- [ ] 編寫單元測試

### Story 101-5: 單元測試與整合測試
- [ ] 創建 `backend/tests/unit/swarm/test_event_types.py`
  - [ ] Payload 序列化測試
  - [ ] 類型驗證測試
- [ ] 創建 `backend/tests/unit/swarm/test_emitter.py`
  - [ ] 各類事件發送測試
  - [ ] 節流功能測試
  - [ ] 批量發送測試
- [ ] 創建 `backend/tests/integration/swarm/test_bridge_integration.py`
  - [ ] 完整事件流測試
  - [ ] 生命週期測試
- [ ] 創建前端 Hook 測試

### Story 101-6: 性能測試與優化
- [ ] 創建 `backend/tests/performance/swarm/test_event_performance.py`
- [ ] 測試事件延遲
- [ ] 測試事件吞吐量
- [ ] 測試內存使用

## 品質檢查

### 代碼品質
- [ ] Black 格式化通過
- [ ] isort 排序通過
- [ ] flake8 檢查通過
- [ ] mypy 類型檢查通過
- [ ] ESLint 檢查通過 (前端)

### 測試
- [ ] 後端單元測試覆蓋率 > 90%
- [ ] 前端單元測試覆蓋率 > 85%
- [ ] 所有測試通過
- [ ] 性能測試通過

### 文檔
- [ ] 函數 docstrings 完整
- [ ] 類 docstrings 完整
- [ ] TypeScript JSDoc 完整

## 驗收標準

- [ ] 所有事件類型定義正確
- [ ] SwarmEventEmitter 正常運作
- [ ] HybridEventBridge 整合成功
- [ ] 前端 Hook 正確接收事件
- [ ] 事件延遲 < 100ms
- [ ] 事件吞吐量 > 50 events/sec

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 25
**開始日期**: 2026-02-06
