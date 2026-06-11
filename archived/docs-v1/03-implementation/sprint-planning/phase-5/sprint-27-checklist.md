# Sprint 27 Checklist: 執行引擎遷移

**Sprint 目標**: 將 WorkflowExecutionService 遷移到 SequentialOrchestration
**週期**: 2 週
**總點數**: 38 點
**Phase 5 功能**: P5-F2 執行引擎遷移
**狀態**: 待執行

---

## 快速驗證命令

```bash
# 驗證官方 API 可用
python -c "from agent_framework.workflows.orchestrations import SequentialOrchestration; print('OK')"

# 驗證適配器模組
python -c "from src.integrations.agent_framework.core.execution import SequentialOrchestrationAdapter; print('OK')"
python -c "from src.integrations.agent_framework.core.events import WorkflowStatusEventAdapter; print('OK')"

# 運行單元測試
cd backend && pytest tests/unit/test_sequential_orchestration_adapter.py -v
cd backend && pytest tests/unit/test_workflow_status_event_adapter.py -v

# 運行整合測試
cd backend && pytest tests/integration/test_execution_adapter_integration.py -v

# 檢查測試覆蓋率
cd backend && pytest tests/unit/test_*execution*.py tests/unit/test_*event*.py --cov=src/integrations/agent_framework/core --cov-report=term-missing
```

---

## S27-1: SequentialOrchestrationAdapter (10 點) - 待執行

### 模組結構 (src/integrations/agent_framework/core/)
- [ ] 創建/更新 `execution.py`
  - [ ] `SequentialOrchestrationAdapter` 類
    - [ ] `__init__()` 初始化
    - [ ] `_build_orchestration()` 構建編排
    - [ ] `_executor_to_agent()` 轉換方法
    - [ ] `run()` 同步執行
    - [ ] `run_stream()` 流式執行
  - [ ] `ExecutionAdapter` 類
    - [ ] `add_event_handler()` 添加處理器
    - [ ] `execute()` 執行工作流
    - [ ] `_handle_event()` 處理事件

### 功能驗證
- [ ] 可創建 SequentialOrchestrationAdapter 實例
- [ ] 可從 WorkflowNodeExecutor 列表構建編排
- [ ] `run()` 返回正確結果
- [ ] `run_stream()` 產生事件流
- [ ] 錯誤處理正確

### 單元測試
- [ ] `test_create_orchestration_adapter.py`
- [ ] `test_run_sequential.py`
- [ ] `test_run_stream.py`
- [ ] `test_error_handling.py`

---

## S27-2: WorkflowStatusEventAdapter (8 點) - 待執行

### 模組結構
- [ ] 創建 `events.py`
  - [ ] `ExecutionStatus` 枚舉
  - [ ] `InternalExecutionEvent` 數據類
  - [ ] `WorkflowStatusEventAdapter` 類
    - [ ] `add_handler()` 添加處理器
    - [ ] `remove_handler()` 移除處理器
    - [ ] `handle()` 處理事件
    - [ ] `_convert_to_internal()` 轉換方法
    - [ ] `_map_status()` 狀態映射

### 功能驗證
- [ ] 可註冊多個事件處理器
- [ ] 事件轉換正確
- [ ] 所有事件類型處理正確
- [ ] 錯誤不影響其他處理器

### 單元測試
- [ ] `test_event_handler_registration.py`
- [ ] `test_event_conversion.py`
- [ ] `test_status_mapping.py`
- [ ] `test_multiple_handlers.py`

---

## S27-3: ExecutionStateMachine 重構 (8 點) - 待執行

### 修改檔案
- [ ] 更新 `domain/executions/state_machine.py`
  - [ ] 添加事件適配器整合
  - [ ] 保持現有 API 不變
  - [ ] 添加 `handle_official_event()` 方法
  - [ ] 更新狀態轉換邏輯

### 功能驗證
- [ ] 可接收官方事件
- [ ] 狀態轉換邏輯正確
- [ ] 與 WorkflowStatusEventAdapter 整合
- [ ] 現有 API 不變

### 單元測試
- [ ] 更新 `test_execution_state_machine.py`
- [ ] 添加事件整合測試

---

## S27-4: ExecutionService 遷移 (7 點) - 待執行

### 修改檔案
- [ ] 更新 `domain/workflows/service.py`
  - [ ] 注入 ExecutionAdapter
  - [ ] 修改 `execute()` 使用適配器
  - [ ] 保持現有介面不變
  - [ ] 添加 deprecation 警告到舊方法

### 功能驗證
- [ ] ExecutionService 使用 ExecutionAdapter
- [ ] 現有功能保持不變
- [ ] 向後兼容
- [ ] 無效能退化

### 整合測試
- [ ] `test_execution_service_migration.py`
- [ ] 測試遷移前後行為一致

---

## S27-5: 整合測試 (5 點) - 待執行

### 測試覆蓋
- [ ] E2E 順序執行測試
- [ ] 事件流測試
- [ ] 狀態機轉換測試
- [ ] 錯誤恢復測試
- [ ] 效能基準測試

### 驗證通過
- [ ] 所有單元測試通過
- [ ] 整合測試通過
- [ ] 效能無退化

### 文檔更新
- [ ] 更新 progress.md
- [ ] 記錄 decisions.md
- [ ] 更新 checklist (本文件)

---

## Sprint 27 完成標準

### 必須完成 (Must Have)
- [ ] SequentialOrchestrationAdapter 實現並通過測試
- [ ] WorkflowStatusEventAdapter 實現並通過測試
- [ ] ExecutionStateMachine 重構完成
- [ ] ExecutionService 遷移完成
- [ ] 測試覆蓋率 >= 80%

### 應該完成 (Should Have)
- [ ] 整合測試全部通過
- [ ] 效能無退化
- [ ] 代碼審查完成

### 可以延後 (Could Have)
- [ ] 進階事件過濾
- [ ] 事件持久化

---

## 依賴確認

### 前置條件
- [ ] Sprint 26 完成
  - [ ] WorkflowNodeExecutor 可用
  - [ ] WorkflowDefinitionAdapter 可用
- [ ] 官方 API 可用
  - [ ] `SequentialOrchestration` 可用
  - [ ] `WorkflowStatusEvent` 可用

### 外部依賴
- [ ] agent-framework package 可用
- [ ] 現有 ExecutionStateMachine 無破壞性變更

---

## 風險和注意事項

### 風險
1. **事件格式不兼容**: 官方事件可能與預期不同
   - 緩解: 靈活的事件適配器設計

2. **效能影響**: 新架構可能影響執行效能
   - 緩解: 效能基準測試，必要時優化

3. **向後兼容**: 現有 API 調用可能受影響
   - 緩解: 保持介面不變，內部重構

---

## 相關連結

- [Sprint 27 Plan](./sprint-27-plan.md) - 詳細計劃
- [Sprint 26 Checklist](./sprint-26-checklist.md) - 前置 Sprint
- [Sprint 28 Plan](./sprint-28-plan.md) - 後續 Sprint
