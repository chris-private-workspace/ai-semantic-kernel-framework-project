# ISSUE-001: WorkflowNodeExecutor Handler 類型註解錯誤

> **建立日期**: 2025-12-10 04:05
> **模組**: workflows
> **嚴重程度**: High
> **狀態**: 已修復
> **發現者**: User
> **會話 ID**: SESSION-2025-12-10-01

---

## 問題描述

WorkflowNodeExecutor 的 `@handler` 裝飾器方法類型註解錯誤。handler 預期接收 `Dict[str, Any]` 類型，但工作流引擎傳入的是 `NodeInput` Pydantic 模型。導致 `@handler` 裝飾器無法匹配正確的 handler。

---

## 重現步驟

1. 進入 Workflows 頁面
2. 選擇一個工作流
3. 點擊「執行」按鈕
4. 觀察錯誤訊息

---

## 預期結果

工作流應該成功執行並返回結果

---

## 實際結果

執行失敗，錯誤訊息：
```
RuntimeError: Executor WorkflowNodeExecutor cannot handle message of type <class 'src.integrations.agent_framework.core.executor.NodeInput'>.
```

---

## 環境信息

```yaml
瀏覽器: Chrome 120
作業系統: Windows 11
Frontend URL: http://localhost:3005
Backend URL: http://localhost:8000
```

---

## 錯誤訊息

```
RuntimeError: Executor WorkflowNodeExecutor cannot handle message of type <class 'src.integrations.agent_framework.core.executor.NodeInput'>.
Traceback (most recent call last):
  File "...\agent_framework\_workflows\_executor.py", line 468, in _find_handler
    raise RuntimeError(f"Executor {self.__class__.__name__} cannot handle message of type {type(message)}.")
```

---

## 相關資訊

- **相關頁面**: http://localhost:3005/workflows/{id}
- **相關 API**: POST /api/v1/workflows/{id}/execute
- **相關代碼**: backend/src/integrations/agent_framework/core/executor.py:159-163

---

## 狀態歷史

| 日期 | 狀態變更 | 備註 |
|------|----------|------|
| 2025-12-10 04:05 | 建立 | 初始記錄 |
| 2025-12-10 04:05 | 已修復 | 修改 handler 類型註解為 NodeInput |

---

## 修復記錄

**修復 ID**: FIX-001
**修復日期**: 2025-12-10
**修復者**: AI Assistant
**驗證狀態**: 已驗證

### 修復內容

將 executor.py 第 159-163 行的 handler 類型註解從：
```python
async def handle_node_input(
    self,
    input_data: Dict[str, Any],
    ctx: WorkflowContext
) -> None:
```

修改為：
```python
async def handle_node_input(
    self,
    input_data: NodeInput,
    ctx: WorkflowContext
) -> None:
```
