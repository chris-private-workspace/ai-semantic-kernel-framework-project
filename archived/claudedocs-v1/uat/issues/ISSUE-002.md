# ISSUE-002: WorkflowEdgeAdapter 參數名稱錯誤

> **建立日期**: 2025-12-10 04:05
> **模組**: workflows
> **嚴重程度**: High
> **狀態**: 已修復
> **發現者**: User
> **會話 ID**: SESSION-2025-12-10-01

---

## 問題描述

WorkflowEdgeAdapter 使用 `source` 和 `target` 作為 Edge 建構參數，但官方 Agent Framework API 要求使用 `source_id` 和 `target_id`。導致 Edge 物件建立失敗。

---

## 重現步驟

1. 進入 Workflows 頁面
2. 選擇一個包含多節點的工作流
3. 點擊「執行」按鈕
4. 觀察錯誤訊息

---

## 預期結果

Edge 物件應該正確建立，工作流圖能夠正常構建

---

## 實際結果

Edge 建構失敗，錯誤訊息指出參數名稱不正確

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
TypeError: Edge.__init__() got unexpected keyword argument 'source'
Expected: source_id, target_id
Received: source, target
```

---

## 相關資訊

- **相關頁面**: http://localhost:3005/workflows/{id}
- **相關 API**: POST /api/v1/workflows/{id}/execute
- **相關代碼**: backend/src/integrations/agent_framework/core/edge.py:345-354

---

## 狀態歷史

| 日期 | 狀態變更 | 備註 |
|------|----------|------|
| 2025-12-10 04:05 | 建立 | 初始記錄 |
| 2025-12-10 04:05 | 已修復 | 修改 Edge 參數名稱 |

---

## 修復記錄

**修復 ID**: FIX-002
**修復日期**: 2025-12-10
**修復者**: AI Assistant
**驗證狀態**: 已驗證

### 修復內容

將 edge.py 第 345-354 行的 Edge 建構從：
```python
return Edge(
    source=self._edge.source,
    target=self._edge.target,
    condition=self._evaluator.evaluate,
)
```

修改為：
```python
return Edge(
    source_id=self._edge.source,
    target_id=self._edge.target,
    condition=self._evaluator.evaluate,
)
```

### 根本原因

官方 Agent Framework 的 Edge 類別使用 `source_id` 和 `target_id` 作為參數名稱，這是為了與內部 ID 追蹤系統保持一致。我們的代碼錯誤地使用了 `source` 和 `target`。

