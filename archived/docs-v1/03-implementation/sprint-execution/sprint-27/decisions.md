# Sprint 27 Decisions: 執行引擎遷移

**Sprint 目標**: 將 WorkflowExecutionService 遷移到官方 SequentialOrchestration

---

## 決策記錄

### D27-001: SequentialOrchestration 封裝策略

**日期**: 2025-12-07
**狀態**: ✅ 已決定
**背景**:
需要將 Sprint 26 的 WorkflowNodeExecutor 封裝為 ChatAgent 介面，以便使用官方 SequentialOrchestration。

**選項**:
1. 直接實現 ChatAgent 介面 - 完全符合官方 API
2. 使用適配器包裝 - 保留現有執行邏輯
3. 混合方式 - 核心用官方，擴展用適配器

**決定**: 選項 2 - 使用 ExecutorAgentWrapper 適配器
**理由**:
- 保留 WorkflowNodeExecutor 的完整功能
- ExecutorAgentWrapper 實現 ChatAgent 介面
- 支持 run() 和 run_streaming() 方法
- 可以處理多種輸入格式 (dict, string, NodeInput)
- 與官方 SequentialOrchestration 完全兼容

---

### D27-002: 事件系統設計

**日期**: 2025-12-07
**狀態**: ✅ 已決定
**背景**:
官方 WorkflowStatusEvent 需要轉換為內部事件格式。

**選項**:
1. 完全採用官方事件格式
2. 保留內部事件格式，添加適配層
3. 統一到新的混合格式

**決定**: 選項 2 - 使用 WorkflowStatusEventAdapter 適配層
**理由**:
- 保留現有內部事件格式 (InternalExecutionEvent)
- 適配器將官方 WorkflowStatusEvent 轉換為內部格式
- 支持事件歷史追蹤和狀態查詢
- EventFilter 提供靈活的事件過濾功能
- 向後兼容現有事件處理邏輯

---

### D27-003: 狀態機整合方式

**日期**: 2025-12-07
**狀態**: ✅ 已決定
**背景**:
現有 ExecutionStateMachine 需要與官方 orchestration 整合。

**選項**:
1. 重構為官方狀態管理
2. 保留現有狀態機，添加橋接層
3. 雙軌運行，逐步遷移

**決定**: 選項 2 - 使用 EnhancedExecutionStateMachine 橋接層
**理由**:
- 保留現有 ExecutionStateMachine 的所有功能和 API
- EnhancedExecutionStateMachine 封裝 DomainStateMachine
- 整合 WorkflowStatusEventAdapter 接收官方事件
- 自動將官方事件轉換為狀態轉換
- StateMachineManager 提供集中化管理
- 狀態映射字典 (EVENT_TO_DOMAIN_STATUS) 確保正確轉換

---

### D27-004: ExecutionService 遷移策略

**日期**: 2025-12-07
**狀態**: ✅ 已決定並實現
**背景**:
WorkflowExecutionService 需要使用新的 ExecutionAdapter 和 SequentialOrchestrationAdapter。

**選項**:
1. 完全替換現有服務
2. 添加適配器層，保留原有介面
3. 創建新服務並逐步遷移

**決定**: 選項 2 - 添加適配器層 (雙軌模式)
**理由**:
- 保留 WorkflowExecutionService 公開 API 不變
- 添加 `use_official_api` 參數啟用官方 API 模式
- `_execute_workflow_official()` 使用 SequentialOrchestrationAdapter
- `_execute_workflow_legacy()` 保留原有執行邏輯
- 支持 EnhancedExecutionStateMachine 進行狀態追蹤
- 完全向後兼容現有調用代碼

---

## 技術約束

1. **必須使用官方 API**:
   - `from agent_framework.workflows.orchestrations import SequentialOrchestration`
   - `from agent_framework import WorkflowStatusEvent`

2. **與 Sprint 26 整合**:
   - 依賴 `WorkflowNodeExecutor` (executor.py)
   - 依賴 `WorkflowEdgeAdapter` (edge.py)
   - 依賴 `WorkflowContextAdapter` (context.py)

3. **向後兼容**:
   - 現有 ExecutionService API 保持不變
   - 內部實現切換到官方 API

---

## 參考資料

- [官方 Workflows API](../../../../.claude/skills/microsoft-agent-framework/references/workflows-api.md)
- [Sprint 26 Decisions](../sprint-26/decisions.md)
- [技術架構文檔](../../02-architecture/technical-architecture.md)
