# Sprint 18 決策記錄

**Sprint**: 18 - WorkflowExecutor 和整合
**開始日期**: 2025-12-05

---

## DEC-18-001: 架構策略選擇

**日期**: 2025-12-05
**狀態**: 已決定

### 背景
需要決定如何將現有 NestedWorkflowManager 遷移至 Agent Framework WorkflowExecutor。

### 選項

1. **完全替換**: 直接使用 WorkflowExecutor 替換 NestedWorkflowManager
2. **並行架構**: 保留原有實現 + 新增適配器層
3. **漸進遷移**: 逐步將功能遷移到新 API

### 決定
選擇 **並行架構** (選項 2)

### 理由
1. 與 Sprint 13-17 保持一致的遷移策略
2. 提供向後兼容性
3. 允許漸進式測試和驗證
4. 降低遷移風險
5. WorkflowExecutor 涉及複雜的 Request/Response 協調

### 影響
- 需要維護適配器層
- 代碼量增加但風險降低
- 用戶可選擇使用新舊 API

---

## DEC-18-002: 並發執行策略

**日期**: 2025-12-05
**狀態**: 已決定

### 背景
Agent Framework WorkflowExecutor 支持多個併發子工作流執行，需要決定如何在適配器中處理。

### 決定
- 使用 `ExecutionContext` 追蹤每個執行
- 使用 `execution_id` (UUID) 識別每個執行
- 使用 `request_to_execution` 映射請求到執行
- 在 `on_checkpoint_save` / `on_checkpoint_restore` 中處理狀態持久化

### 實現策略
```python
# 追蹤並發執行
self._execution_contexts: dict[str, ExecutionContext] = {}
self._request_to_execution: dict[str, str] = {}
```

---

## DEC-18-003: SubWorkflow 消息處理

**日期**: 2025-12-05
**狀態**: 已決定

### 背景
WorkflowExecutor 使用 `SubWorkflowRequestMessage` 和 `SubWorkflowResponseMessage` 進行父子工作流通信。

### 決定
- 保留 Agent Framework 的消息格式
- 創建轉換函數支持我們的 NestedWorkflowManager 格式
- `create_response()` 方法驗證響應類型

### 映射表

| Agent Framework | 我們的實現 |
|-----------------|-----------|
| SubWorkflowRequestMessage | NestedWorkflowRequest |
| SubWorkflowResponseMessage | NestedWorkflowResponse |
| ExecutionContext | NestedExecutionContext |

---

## DEC-18-004: 整合測試策略

**日期**: 2025-12-05
**狀態**: 已決定

### 背景
Sprint 18 需要測試所有 Phase 3 功能的整合。

### 決定
- 分層測試：單元測試 → 整合測試 → E2E 測試
- 測試組合：
  1. ConcurrentBuilder + GroupChatBuilder
  2. HandoffBuilder + MagenticBuilder
  3. WorkflowExecutor + Checkpoint
  4. 全功能整合 E2E

### 優先級
1. WorkflowExecutor 基本功能
2. 嵌套工作流執行
3. 並發執行隔離
4. Phase 3 整合

---

## 已完成決策

### RESOLVED-001: 舊代碼清理範圍
**問題**: 確定哪些舊代碼需要標記為 deprecated 或刪除？
**狀態**: ✅ 已決定
**決定**:
- Phase 2 代碼保留，不刪除
- 遷移層使用 `Legacy` 後綴標記舊類型
- 提供雙向轉換函數支持向後兼容
- 文檔說明遷移路徑

---

## Sprint 18 決策摘要

| 決策 ID | 主題 | 狀態 |
|---------|------|------|
| DEC-18-001 | 並行架構策略 | ✅ 已決定 |
| DEC-18-002 | 並發執行策略 | ✅ 已決定 |
| DEC-18-003 | SubWorkflow 消息處理 | ✅ 已決定 |
| DEC-18-004 | 整合測試策略 | ✅ 已決定 |
| RESOLVED-001 | 舊代碼清理範圍 | ✅ 已決定 |
