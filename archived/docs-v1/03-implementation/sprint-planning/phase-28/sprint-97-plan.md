# Sprint 97: HITLController + ApprovalHandler

## 概述

Sprint 97 專注於建立 **HITLController** 人機協作控制器和 **ApprovalHandler** 審批處理器，以及完整版的 **LLM QuestionGenerator**。

## 目標

1. 實現 HITLController
2. 實現 ApprovalHandler (基礎版)
3. 實現審批 Webhook (Teams 簡化版)
4. 實現 LLM QuestionGenerator
5. 多輪對話狀態管理增強

## Story Points: 30 點

## 前置條件

- ✅ Sprint 96 完成 (RiskAssessor)
- ✅ GuidedDialogEngine 就緒
- ✅ API 路由就緒

## 任務分解

### Story 97-1: 實現 HITLController (4h, P0)

**目標**: 建立人機協作控制器

**交付物**:
- `backend/src/integrations/orchestration/hitl/controller.py`
- `backend/src/integrations/orchestration/hitl/__init__.py`

**驗收標準**:
- [ ] HITLController 類實現完成
- [ ] request_approval() 方法
- [ ] check_approval_status() 方法
- [ ] cancel_approval() 方法
- [ ] 支援超時處理

### Story 97-2: 實現 ApprovalHandler (4h, P0)

**目標**: 建立審批處理器

**交付物**:
- `backend/src/integrations/orchestration/hitl/approval_handler.py`

**驗收標準**:
- [ ] ApprovalHandler 類實現完成
- [ ] 支援 approve/reject 操作
- [ ] 審批狀態持久化
- [ ] 審批歷史記錄

### Story 97-3: 實現審批 Webhook (4h, P1)

**目標**: 實現 Teams 審批 Webhook (簡化版)

**交付物**:
- 更新 `approval_handler.py`

**Teams Webhook 格式**:

```json
{
  "@type": "MessageCard",
  "@context": "http://schema.org/extensions",
  "summary": "審批請求",
  "themeColor": "FF0000",
  "title": "高風險操作審批請求",
  "sections": [{
    "activityTitle": "ETL Pipeline 重啟",
    "facts": [
      { "name": "意圖類別", "value": "incident" },
      { "name": "子意圖", "value": "etl_failure" },
      { "name": "風險等級", "value": "high" }
    ]
  }],
  "potentialAction": [
    {
      "@type": "HttpPOST",
      "name": "批准",
      "target": "https://api.example.com/approve"
    },
    {
      "@type": "HttpPOST",
      "name": "拒絕",
      "target": "https://api.example.com/reject"
    }
  ]
}
```

**驗收標準**:
- [ ] Teams Webhook 發送正確
- [ ] 審批回調處理正確
- [ ] 支援審批超時

### Story 97-4: 實現 LLM QuestionGenerator (5h, P0)

**目標**: 實現基於 LLM 的問題生成器

**交付物**:
- 更新 `backend/src/integrations/orchestration/guided_dialog/generator.py`

**Prompt 設計**:

```python
QUESTION_GENERATION_PROMPT = """
你是一個 IT 服務助手。根據以下資訊，生成適當的澄清問題。

## 意圖類別
{intent_category}

## 缺失欄位
{missing_fields}

## 已知資訊
{collected_info}

## 要求
1. 生成 1-3 個問題
2. 問題要具體、易懂
3. 提供可選答案（如適用）
4. 使用繁體中文

## 輸出格式 (JSON)
{
  "questions": [
    {
      "field": "欄位名稱",
      "question": "問題內容",
      "options": ["選項1", "選項2"]  // 可選
    }
  ]
}
"""
```

**驗收標準**:
- [ ] LLM QuestionGenerator 實現完成
- [ ] 問題生成品質良好
- [ ] 支援選項生成
- [ ] 延遲 < 2000ms

### Story 97-5: 多輪對話狀態管理增強 (3h, P0)

**目標**: 增強多輪對話的狀態管理

**交付物**:
- 更新 `context_manager.py`

**增強功能**:
- [ ] 對話歷史持久化 (Redis)
- [ ] 對話超時處理
- [ ] 對話恢復功能
- [ ] 最大輪數限制

**驗收標準**:
- [ ] 狀態持久化正確
- [ ] 超時處理正確
- [ ] 恢復功能正常

## 技術設計

### HITLController 類設計

```python
from enum import Enum
from dataclasses import dataclass

class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

@dataclass
class ApprovalRequest:
    request_id: str
    routing_decision: RoutingDecision
    risk_assessment: RiskAssessment
    requester: str
    created_at: datetime
    expires_at: datetime
    status: ApprovalStatus

class HITLController:
    """
    人機協作控制器

    功能:
    1. 發起審批請求
    2. 追蹤審批狀態
    3. 處理審批結果
    """

    def __init__(
        self,
        approval_handler: ApprovalHandler,
        storage: ApprovalStorage,
        notification_service: NotificationService,
    ):
        self.approval_handler = approval_handler
        self.storage = storage
        self.notification_service = notification_service

    async def request_approval(
        self,
        routing_decision: RoutingDecision,
        risk_assessment: RiskAssessment,
        requester: str,
        timeout_minutes: int = 30,
    ) -> ApprovalRequest:
        """發起審批請求"""
        request = ApprovalRequest(
            request_id=str(uuid.uuid4()),
            routing_decision=routing_decision,
            risk_assessment=risk_assessment,
            requester=requester,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=timeout_minutes),
            status=ApprovalStatus.PENDING,
        )

        # 保存請求
        await self.storage.save(request)

        # 發送通知
        await self.notification_service.send_approval_request(request)

        return request

    async def check_status(self, request_id: str) -> ApprovalStatus:
        """檢查審批狀態"""
        request = await self.storage.get(request_id)

        if request.status == ApprovalStatus.PENDING:
            # 檢查是否超時
            if datetime.utcnow() > request.expires_at:
                request.status = ApprovalStatus.EXPIRED
                await self.storage.update(request)

        return request.status

    async def process_approval(
        self,
        request_id: str,
        approved: bool,
        approver: str,
        comment: Optional[str] = None,
    ) -> ApprovalRequest:
        """處理審批結果"""
        request = await self.storage.get(request_id)

        if request.status != ApprovalStatus.PENDING:
            raise ValueError(f"Request {request_id} is not pending")

        request.status = ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
        request.approver = approver
        request.approved_at = datetime.utcnow()
        request.comment = comment

        await self.storage.update(request)

        return request
```

### LLM QuestionGenerator 設計

```python
class LLMQuestionGenerator:
    """LLM 問題生成器"""

    def __init__(self, client: AsyncAnthropic):
        self.client = client

    async def generate(
        self,
        intent_category: ITIntentCategory,
        missing_fields: List[str],
        collected_info: Dict[str, Any] = None,
    ) -> List[Question]:
        """生成問題"""
        response = await self.client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": QUESTION_GENERATION_PROMPT.format(
                        intent_category=intent_category.value,
                        missing_fields=missing_fields,
                        collected_info=collected_info or {},
                    )
                }
            ]
        )

        result = self._parse_response(response.content[0].text)
        return [Question(**q) for q in result["questions"]]
```

## 完成標準

- [ ] 所有 Story 完成
- [ ] HITL 流程端到端通過
- [ ] Teams Webhook 正常工作
- [ ] LLM 問題生成品質良好
- [ ] 單元測試覆蓋率 > 90%
- [ ] 代碼審查通過

---

**Sprint 開始**: 2026-02-20
**Sprint 結束**: 2026-02-27
**Story Points**: 30
