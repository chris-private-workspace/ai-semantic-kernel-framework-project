# Story 98-4: 整合 HITL 到現有審批流程

## 概述

| 屬性 | 值 |
|------|-----|
| **Story 編號** | S98-4 |
| **名稱** | 整合 HITL 到審批流程 |
| **點數** | 4 |
| **優先級** | P0 |
| **狀態** | ✅ 完成 |

## 目標

在 API 層整合新的 HITL 到現有審批機制，支援 Teams Webhook 回調。

## 交付物

### 新增文件

- `backend/src/api/v1/orchestration/approval_routes.py`

### API 端點

| Method | Endpoint | 描述 |
|--------|----------|------|
| GET | `/api/v1/orchestration/approvals` | 獲取待審批列表 |
| GET | `/api/v1/orchestration/approvals/{approval_id}` | 獲取審批詳情 |
| POST | `/api/v1/orchestration/approvals/{approval_id}/decision` | 提交審批決定 |
| POST | `/api/v1/orchestration/approvals/{approval_id}/callback` | Teams Webhook 回調 |

### Pydantic 模型

```python
class ApprovalSummary(BaseModel):
    approval_id: str       # 審批 ID
    status: str            # 狀態
    requester: str         # 請求者
    intent_category: Optional[str]  # IT 意圖類別
    risk_level: Optional[str]       # 風險等級
    created_at: datetime   # 創建時間
    expires_at: Optional[datetime]  # 過期時間

class ApprovalDetailResponse(BaseModel):
    approval_id: str       # 審批 ID
    status: str            # 狀態
    approval_type: str     # 審批類型
    requester: str         # 請求者
    intent_category: Optional[str]  # IT 意圖
    risk_level: Optional[str]       # 風險等級
    risk_score: Optional[float]     # 風險分數
    risk_factors: Optional[List[str]]  # 風險因素
    history: Optional[List[Dict]]   # 審批歷史

class SubmitDecisionRequest(BaseModel):
    decision: ApprovalDecision  # 審批決定
    approver: str               # 審批人
    comment: Optional[str]      # 備註

class TeamsCallbackRequest(BaseModel):
    action_type: str     # 動作類型
    approval_id: str     # 審批 ID
    user_id: str         # Teams 用戶 ID
    user_name: Optional[str]  # Teams 用戶名
    comment: Optional[str]    # 備註
```

## 使用範例

### 獲取待審批列表

```bash
GET /api/v1/orchestration/approvals?status_filter=pending
```

Response:
```json
{
  "approvals": [
    {
      "approval_id": "abc-123",
      "status": "pending",
      "requester": "user@example.com",
      "intent_category": "change_management",
      "risk_level": "high",
      "created_at": "2026-01-16T10:00:00Z",
      "expires_at": "2026-01-16T10:30:00Z"
    }
  ],
  "total": 1,
  "pending_count": 1
}
```

### 提交審批決定

```bash
POST /api/v1/orchestration/approvals/abc-123/decision
{
  "decision": "approve",
  "approver": "admin@example.com",
  "comment": "Approved for production deployment"
}
```

Response:
```json
{
  "approval_id": "abc-123",
  "decision": "approve",
  "status": "approved",
  "message": "Request approved successfully by admin@example.com"
}
```

### Teams Webhook 回調

```bash
POST /api/v1/orchestration/approvals/abc-123/callback
{
  "action_type": "approve",
  "approval_id": "abc-123",
  "user_id": "teams-user-123",
  "user_name": "John Doe",
  "comment": "Approved via Teams"
}
```

## 驗收標準

- [x] 審批 API 實現完成
- [x] 與現有 HITLController 整合
- [x] Teams 回調正常工作
- [x] 錯誤處理完善

---

**完成日期**: 2026-01-16
