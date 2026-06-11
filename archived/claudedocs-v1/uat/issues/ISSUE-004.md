# ISSUE-004: API 回應序列化錯誤

> **建立日期**: 2025-12-10 04:30
> **模組**: api
> **嚴重程度**: High
> **狀態**: 已修復
> **發現者**: User
> **會話 ID**: SESSION-2025-12-10-01

---

## 問題描述

Workflow 執行 API 的回應模型 `WorkflowExecutionResponse.result` 欄位預期為 `str` 類型，但工作流執行結果返回的是事件列表 `List[ExecutorInvokedEvent | ExecutorCompletedEvent]`。導致 Pydantic 驗證失敗。

---

## 重現步驟

1. 進入 Workflows 頁面
2. 選擇一個已啟用的工作流
3. 點擊「執行」按鈕
4. 觀察 API 錯誤回應

---

## 預期結果

API 應該返回成功的執行結果，包含正確序列化的 result 欄位

---

## 實際結果

API 返回 500 錯誤，Pydantic 驗證失敗：
```
1 validation error for WorkflowExecutionResponse
result
  Input should be a valid string [type=string_type, input_value=[ExecutorInvokedEvent(...)], input_type=list]
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
fastapi.exceptions.ResponseValidationError: 1 validation error for WorkflowExecutionResponse
result
  Input should be a valid string [type=string_type, input_value=[ExecutorInvokedEvent(executor_id='start', timestamp=datetime.datetime(2025, 12, 10, 4, 25, 47, 123456)), ExecutorCompletedEvent(executor_id='start', ...)], input_type=list]
```

---

## 相關資訊

- **相關頁面**: http://localhost:3005/workflows/{id}
- **相關 API**: POST /api/v1/workflows/{id}/execute
- **相關代碼**:
  - backend/src/api/v1/workflows/routes.py:430-458
  - backend/src/domain/workflows/schemas.py (WorkflowExecutionResponse)

---

## 狀態歷史

| 日期 | 狀態變更 | 備註 |
|------|----------|------|
| 2025-12-10 04:30 | 建立 | 初始記錄 |
| 2025-12-10 04:30 | 已修復 | 添加 JSON 序列化邏輯 |

---

## 修復記錄

**修復 ID**: FIX-004
**修復日期**: 2025-12-10
**修復者**: AI Assistant
**驗證狀態**: 已驗證

### 修復內容

在 routes.py 添加 `import json` 並在回應建構前添加結果序列化邏輯：

```python
import json  # 新增 import

# ... 在 execute_workflow 函數中 ...

# Convert result to JSON string for API response
result_str = None
if result.result is not None:
    try:
        if isinstance(result.result, str):
            result_str = result.result
        elif isinstance(result.result, (dict, list)):
            result_str = json.dumps(result.result, default=str)
        else:
            result_str = str(result.result)
    except Exception:
        result_str = str(result.result)

return WorkflowExecutionResponse(
    execution_id=execution_id,
    workflow_id=workflow_id,
    status="completed" if result.success else "failed",
    result=result_str,  # 使用序列化後的字串
    # ... 其他欄位 ...
)
```

### 根本原因

官方 Agent Framework 的 `Workflow.run()` 方法返回一個事件列表（包含 `ExecutorInvokedEvent`、`ExecutorCompletedEvent` 等），而非直接的執行結果。我們的 API 回應模型 `WorkflowExecutionResponse.result` 定義為 `Optional[str]`，需要將事件列表序列化為 JSON 字串才能正確返回。

### 驗證結果

修復後執行測試：
```json
{
    "execution_id": "6924b830-5e77-43d0-98a3-9388c5e9b1ac",
    "workflow_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "result": "[\"ExecutorInvokedEvent...\", \"ExecutorCompletedEvent...\"]",
    "stats": {
        "duration_seconds": 0.058745
    }
}
```

