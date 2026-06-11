# Story 98-3: 整合 GuidedDialogEngine 到 API 層

## 概述

| 屬性 | 值 |
|------|-----|
| **Story 編號** | S98-3 |
| **名稱** | 整合 GuidedDialogEngine 到 API 層 |
| **點數** | 4 |
| **優先級** | P0 |
| **狀態** | ✅ 完成 |

## 目標

在 API 層支援引導式對話，提供 REST API 端點管理多輪對話會話。

## 交付物

### 新增文件

- `backend/src/api/v1/orchestration/dialog_routes.py`

### API 端點

| Method | Endpoint | 描述 |
|--------|----------|------|
| POST | `/api/v1/orchestration/dialog/start` | 啟動對話，返回第一輪問題 |
| POST | `/api/v1/orchestration/dialog/{dialog_id}/respond` | 提交用戶回答，返回下一輪問題或完成 |
| GET | `/api/v1/orchestration/dialog/{dialog_id}/status` | 獲取對話狀態 |
| DELETE | `/api/v1/orchestration/dialog/{dialog_id}` | 取消對話 |

### Pydantic 模型

```python
class StartDialogRequest(BaseModel):
    content: str               # 用戶初始消息
    user_id: Optional[str]     # 用戶 ID
    session_id: Optional[str]  # 會話 ID
    initial_context: Optional[Dict[str, Any]]  # 初始上下文

class DialogQuestionItem(BaseModel):
    question_id: str           # 問題 ID
    question: str              # 問題文字
    field_name: str            # 欄位名稱
    options: Optional[List[str]]  # 選項
    required: bool             # 是否必填

class DialogStatusResponse(BaseModel):
    dialog_id: str             # 對話 ID
    status: str                # 狀態
    needs_more_info: bool      # 是否需要更多資訊
    message: Optional[str]     # 訊息
    questions: Optional[List[DialogQuestionItem]]  # 問題列表
    current_intent: Optional[str]  # 當前意圖
    completeness_score: float  # 完整度分數
    turn_count: int            # 對話輪數

class RespondToDialogRequest(BaseModel):
    responses: Dict[str, Any]  # 回答
    additional_message: Optional[str]  # 額外訊息
```

## 使用範例

### 啟動對話

```bash
POST /api/v1/orchestration/dialog/start
{
  "content": "我想申請一台新的虛擬機",
  "user_id": "user@example.com"
}
```

Response:
```json
{
  "dialog_id": "abc-123",
  "status": "active",
  "needs_more_info": true,
  "message": "我需要更多資訊來處理您的請求。",
  "questions": [
    {
      "question_id": "q1",
      "question": "請問您需要什麼規格的虛擬機？",
      "field_name": "vm_spec",
      "options": ["Small (2 vCPU, 4GB)", "Medium (4 vCPU, 8GB)", "Large (8 vCPU, 16GB)"],
      "required": true
    }
  ],
  "completeness_score": 0.3,
  "turn_count": 1
}
```

### 提交回答

```bash
POST /api/v1/orchestration/dialog/abc-123/respond
{
  "responses": {
    "vm_spec": "Medium (4 vCPU, 8GB)"
  }
}
```

## 驗收標準

- [x] API 路由實現完成
- [x] 多輪對話正常工作
- [x] 狀態管理正確
- [x] 錯誤處理完善

---

**完成日期**: 2026-01-16
