# ISSUE-003: WorkflowBuilder API 方法不存在

> **建立日期**: 2025-12-10 04:05
> **模組**: workflows
> **嚴重程度**: Critical
> **狀態**: 已修復
> **發現者**: User
> **會話 ID**: SESSION-2025-12-10-01

---

## 問題描述

WorkflowDefinitionAdapter 使用 `WorkflowBuilder.register_executor()` 方法註冊執行器，但安裝的 Agent Framework 版本沒有此方法。導致工作流建構完全失敗。

---

## 重現步驟

1. 進入 Workflows 頁面
2. 選擇任意工作流
3. 點擊「執行」按鈕
4. 觀察錯誤訊息

---

## 預期結果

WorkflowBuilder 應該成功建構工作流並返回 Workflow 物件

---

## 實際結果

建構失敗，錯誤訊息：
```
AttributeError: 'WorkflowBuilder' object has no attribute 'register_executor'
```

---

## 環境信息

```yaml
瀏覽器: Chrome 120
作業系統: Windows 11
Frontend URL: http://localhost:3005
Backend URL: http://localhost:8000
Agent Framework Version: 0.1.0-preview
```

---

## 錯誤訊息

```
AttributeError: 'WorkflowBuilder' object has no attribute 'register_executor'
Traceback (most recent call last):
  File "...\workflow.py", line 210, in build
    builder.register_executor(factory, name=node.id)
AttributeError: 'WorkflowBuilder' object has no attribute 'register_executor'
```

---

## 相關資訊

- **相關頁面**: http://localhost:3005/workflows/{id}
- **相關 API**: POST /api/v1/workflows/{id}/execute
- **相關代碼**: backend/src/integrations/agent_framework/core/workflow.py:200-270

---

## 狀態歷史

| 日期 | 狀態變更 | 備註 |
|------|----------|------|
| 2025-12-10 04:05 | 建立 | 初始記錄 |
| 2025-12-10 04:05 | 已修復 | 重構 build() 方法使用 add_edge() |

---

## 修復記錄

**修復 ID**: FIX-003
**修復日期**: 2025-12-10
**修復者**: AI Assistant
**驗證狀態**: 已驗證

### 修復內容

完全重構 workflow.py 的 `build()` 方法。

從舊的實現：
```python
def build(self) -> Workflow:
    builder = WorkflowBuilder()

    # Register executors by name (NOT SUPPORTED)
    for node in self._definition.nodes:
        factory = lambda n=node: WorkflowNodeExecutor(...)
        builder.register_executor(factory, name=node.id)

    # Add edges by name
    for edge in self._definition.edges:
        builder.add_edge(edge.source, edge.target)
```

修改為新的實現：
```python
def build(self) -> Workflow:
    builder = WorkflowBuilder()

    # Create executor instances directly
    for node in self._definition.nodes:
        executor = WorkflowNodeExecutor(node=node, ...)
        self._executor_map[node.id] = executor

    # Add edges using executor objects directly
    for edge in self._definition.edges:
        source_executor = self._executor_map[edge.source]
        target_executor = self._executor_map[edge.target]
        builder.add_edge(source_executor, target_executor)

    # Set start executor
    builder.set_start_executor(start_executor)

    return builder.build()
```

### 根本原因

安裝的 Agent Framework 版本使用不同的 API 模式：
- 不使用 `register_executor()` 方法
- `add_edge()` 直接接受 Executor 物件，而非名稱字串
- 需要明確調用 `set_start_executor()` 設定起始執行器

這是 Preview 版本 API 與文檔不一致的問題，需要根據實際安裝的版本調整代碼。

