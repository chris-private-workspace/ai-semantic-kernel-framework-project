# Sprint 28: 人工審批遷移

**Sprint 目標**: 將 CheckpointService 遷移到 RequestResponseExecutor
**週期**: 2 週
**Story Points**: 34 點
**Phase 5 功能**: P5-F3 (人工審批遷移)

---

## Sprint 概覽

### 目標
1. 創建 HumanApprovalExecutor (基於 `RequestResponseExecutor`)
2. 設計 ApprovalRequest/Response 模型
3. 重構 CheckpointService (分離存儲與審批)
4. 整合審批工作流
5. 完整測試覆蓋

### 成功標準
- [ ] 可以使用官方 `RequestResponseExecutor` 實現人工審批
- [ ] 工作流可以在審批點暫停
- [ ] 審批回應可以恢復工作流執行
- [ ] CheckpointService 職責清晰分離

---

## 問題分析

### 目前實現的問題

現有 `CheckpointService` 混合了兩個不同的概念：

```python
# domain/checkpoints/service.py - 概念混淆
class CheckpointService:
    async def create_checkpoint(self, execution_id, node_id, payload):
        """創建檢查點 - 這是【存儲】概念"""
        pass

    async def approve_checkpoint(self, checkpoint_id, user_id):
        """審批檢查點 - 這是【人工審批】概念"""
        pass

    async def reject_checkpoint(self, checkpoint_id, user_id, reason):
        """拒絕檢查點 - 這也是【人工審批】概念"""
        pass
```

### 應該分離為

1. **狀態存儲** → 使用 `CheckpointStorage` (已在 Phase 4 實現)
2. **人工審批** → 使用 `RequestResponseExecutor` (本 Sprint 實現)

---

## 架構設計

### 目標架構 (使用官方 API)

```python
# integrations/agent_framework/core/approval.py
from agent_framework.workflows import RequestResponseExecutor, Executor
from pydantic import BaseModel

class ApprovalRequest(BaseModel):
    """審批請求模型"""
    request_id: str
    action: str
    risk_level: str  # low, medium, high, critical
    details: str
    context: Dict[str, Any] = {}
    timeout_seconds: Optional[int] = 3600  # 預設 1 小時

class ApprovalResponse(BaseModel):
    """審批回應模型"""
    request_id: str
    approved: bool
    reason: str
    approver: str
    approved_at: datetime
    metadata: Dict[str, Any] = {}

@Executor.register
class HumanApprovalExecutor(RequestResponseExecutor[ApprovalRequest, ApprovalResponse]):
    """
    人工審批執行器

    工作流在此暫停，等待人工審批回應。
    基於官方 RequestResponseExecutor 實現。
    """

    def __init__(
        self,
        id: str = "human-approval",
        notification_service: Optional['NotificationService'] = None,
        escalation_policy: Optional['EscalationPolicy'] = None
    ):
        super().__init__(id=id)
        self._notification_service = notification_service
        self._escalation_policy = escalation_policy

    async def on_request_created(self, request: ApprovalRequest, context) -> None:
        """當審批請求創建時觸發"""
        # 發送通知給審批人
        if self._notification_service:
            await self._notification_service.notify_approvers(
                request_id=request.request_id,
                action=request.action,
                risk_level=request.risk_level,
                details=request.details
            )

        # 設置超時升級
        if self._escalation_policy:
            await self._escalation_policy.schedule_escalation(
                request_id=request.request_id,
                timeout_seconds=request.timeout_seconds
            )

    async def on_response_received(
        self,
        request: ApprovalRequest,
        response: ApprovalResponse,
        context
    ) -> None:
        """當審批回應收到時觸發"""
        # 取消升級計劃
        if self._escalation_policy:
            await self._escalation_policy.cancel_escalation(request.request_id)

        # 記錄審計日誌
        await self._log_approval_decision(request, response)
```

### 工作流整合

```python
# 在工作流中使用人工審批
from agent_framework.workflows import Workflow, Edge

workflow = Workflow(
    executors=[
        analyzer,
        HumanApprovalExecutor(id="risk-approval"),
        executor_after_approval
    ],
    edges=[
        Edge(source="start", target="analyzer"),
        Edge(source="analyzer", target="risk-approval"),
        Edge(source="risk-approval", target="executor_after_approval"),
    ]
)

# 工作流會在 HumanApprovalExecutor 處暫停
# 稍後，提供審批回應
await workflow.respond(
    executor_name="risk-approval",
    response=ApprovalResponse(
        request_id="approval-123",
        approved=True,
        reason="Risk is acceptable",
        approver="admin@company.com",
        approved_at=datetime.utcnow()
    )
)
```

---

## User Stories

### S28-1: HumanApprovalExecutor (10 點)

**描述**: 創建基於官方 `RequestResponseExecutor` 的人工審批執行器。

**驗收標準**:
- [ ] 實現 `HumanApprovalExecutor` 類繼承 `RequestResponseExecutor`
- [ ] 支持通知服務整合
- [ ] 支持升級策略
- [ ] 工作流可在此暫停
- [ ] 單元測試覆蓋

**檔案**:
- `backend/src/integrations/agent_framework/core/approval.py`
- `backend/tests/unit/test_human_approval_executor.py`

**技術任務**:

```python
# backend/src/integrations/agent_framework/core/approval.py
"""
人工審批執行器 - 基於官方 RequestResponseExecutor

將現有的 CheckpointService 審批功能遷移到官方 API
"""

from typing import Any, Dict, Optional
from datetime import datetime
from pydantic import BaseModel
from uuid import UUID
import logging

from agent_framework.workflows import RequestResponseExecutor, Executor

logger = logging.getLogger(__name__)


class ApprovalRequest(BaseModel):
    """審批請求模型"""
    request_id: str
    execution_id: UUID
    node_id: str
    action: str
    risk_level: str = "medium"  # low, medium, high, critical
    details: str = ""
    payload: Dict[str, Any] = {}
    timeout_seconds: int = 3600
    required_approvers: int = 1
    current_approvers: int = 0


class ApprovalResponse(BaseModel):
    """審批回應模型"""
    request_id: str
    approved: bool
    reason: str = ""
    approver: str
    approved_at: datetime
    signature: Optional[str] = None
    metadata: Dict[str, Any] = {}


class EscalationPolicy:
    """升級策略"""

    def __init__(self, notification_service: 'NotificationService'):
        self._notification_service = notification_service
        self._pending_escalations: Dict[str, Any] = {}

    async def schedule_escalation(
        self,
        request_id: str,
        timeout_seconds: int,
        escalation_chain: List[str] = None
    ) -> None:
        """安排升級"""
        self._pending_escalations[request_id] = {
            "scheduled_at": datetime.utcnow(),
            "timeout": timeout_seconds,
            "chain": escalation_chain or []
        }

    async def cancel_escalation(self, request_id: str) -> None:
        """取消升級"""
        if request_id in self._pending_escalations:
            del self._pending_escalations[request_id]


@Executor.register
class HumanApprovalExecutor(RequestResponseExecutor[ApprovalRequest, ApprovalResponse]):
    """
    人工審批執行器

    工作流在此暫停，等待人工審批回應。
    支持：
    - 通知服務整合
    - 升級策略
    - 多人審批
    - 超時處理
    """

    def __init__(
        self,
        id: str = "human-approval",
        notification_service: Optional['NotificationService'] = None,
        escalation_policy: Optional[EscalationPolicy] = None,
        audit_logger: Optional['AuditLogger'] = None
    ):
        super().__init__(id=id)
        self._notification_service = notification_service
        self._escalation_policy = escalation_policy
        self._audit_logger = audit_logger

    async def on_request_created(
        self,
        request: ApprovalRequest,
        context
    ) -> None:
        """
        當審批請求創建時觸發

        Args:
            request: 審批請求
            context: 工作流上下文
        """
        logger.info(f"Approval request created: {request.request_id}")

        # 發送通知給審批人
        if self._notification_service:
            await self._notification_service.send_approval_notification(
                request_id=request.request_id,
                action=request.action,
                risk_level=request.risk_level,
                details=request.details,
                payload=request.payload
            )

        # 設置超時升級
        if self._escalation_policy:
            await self._escalation_policy.schedule_escalation(
                request_id=request.request_id,
                timeout_seconds=request.timeout_seconds
            )

        # 記錄審計日誌
        if self._audit_logger:
            await self._audit_logger.log_approval_request(request)

    async def on_response_received(
        self,
        request: ApprovalRequest,
        response: ApprovalResponse,
        context
    ) -> None:
        """
        當審批回應收到時觸發

        Args:
            request: 原始審批請求
            response: 審批回應
            context: 工作流上下文
        """
        logger.info(
            f"Approval response received: {response.request_id}, "
            f"approved={response.approved}"
        )

        # 取消升級計劃
        if self._escalation_policy:
            await self._escalation_policy.cancel_escalation(request.request_id)

        # 記錄審計日誌
        if self._audit_logger:
            await self._audit_logger.log_approval_decision(request, response)

        # 如果拒絕，可能需要額外處理
        if not response.approved:
            await self._handle_rejection(request, response, context)

    async def _handle_rejection(
        self,
        request: ApprovalRequest,
        response: ApprovalResponse,
        context
    ) -> None:
        """處理拒絕情況"""
        # 設置上下文狀態表示拒絕
        context.set("approval_rejected", True)
        context.set("rejection_reason", response.reason)
```

---

### S28-2: ApprovalRequest/Response 模型 (8 點)

**描述**: 設計完整的審批請求和回應模型。

**驗收標準**:
- [ ] ApprovalRequest 模型包含所有必要欄位
- [ ] ApprovalResponse 模型包含所有必要欄位
- [ ] 支持多人審批
- [ ] 支持簽名驗證
- [ ] Pydantic 驗證正確

**檔案**:
- `backend/src/integrations/agent_framework/core/approval.py` (擴展)
- `backend/tests/unit/test_approval_models.py`

---

### S28-3: CheckpointService 重構 (8 點)

**描述**: 重構 CheckpointService，分離存儲與審批職責。

**驗收標準**:
- [ ] CheckpointService 只處理狀態存儲
- [ ] 審批功能移到 HumanApprovalExecutor
- [ ] 向後兼容 (deprecation 警告)
- [ ] 現有 API 測試通過

**檔案**:
- `backend/src/domain/checkpoints/service.py` (修改)
- `backend/tests/unit/test_checkpoint_service.py` (更新)

**變更說明**:

```python
# 重構後的 CheckpointService - 只處理存儲
class CheckpointService:
    """
    檢查點服務 (重構後)

    只負責工作流狀態的存儲和恢復。
    人工審批功能已遷移到 HumanApprovalExecutor。
    """

    def __init__(self, checkpoint_store: CheckpointStorage):
        self._store = checkpoint_store

    async def save_state(
        self,
        execution_id: UUID,
        state: Dict[str, Any]
    ) -> str:
        """保存執行狀態"""
        return await self._store.save(
            checkpoint_id=str(uuid4()),
            workflow_id=str(execution_id),
            data=state
        )

    async def load_state(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """載入執行狀態"""
        checkpoint = await self._store.load(checkpoint_id)
        return checkpoint.data if checkpoint else None

    # Deprecated methods with warnings
    @deprecated("Use HumanApprovalExecutor instead")
    async def create_checkpoint(self, execution_id, node_id, payload):
        """已棄用: 請使用 HumanApprovalExecutor"""
        warnings.warn(
            "create_checkpoint is deprecated, use HumanApprovalExecutor",
            DeprecationWarning
        )
        # 暫時保留向後兼容
        ...

    @deprecated("Use HumanApprovalExecutor instead")
    async def approve_checkpoint(self, checkpoint_id, user_id):
        """已棄用: 請使用 HumanApprovalExecutor"""
        warnings.warn(
            "approve_checkpoint is deprecated, use HumanApprovalExecutor",
            DeprecationWarning
        )
        ...
```

---

### S28-4: 審批工作流整合 (5 點)

**描述**: 將 HumanApprovalExecutor 整合到工作流中。

**驗收標準**:
- [ ] 可在工作流中使用 HumanApprovalExecutor
- [ ] 工作流可正確暫停
- [ ] 可透過 `workflow.respond()` 恢復
- [ ] 整合測試通過

**檔案**:
- `backend/tests/integration/test_approval_workflow_integration.py`

---

### S28-5: 單元測試 (3 點)

**描述**: 完成所有單元測試。

**驗收標準**:
- [ ] 所有單元測試通過
- [ ] 測試覆蓋率 >= 80%
- [ ] 邊界案例覆蓋

---

## 完成定義 (Definition of Done)

1. **功能完成**
   - [ ] HumanApprovalExecutor 實現並通過測試
   - [ ] ApprovalRequest/Response 模型完成
   - [ ] CheckpointService 重構完成
   - [ ] 審批工作流整合完成

2. **測試完成**
   - [ ] 單元測試覆蓋率 >= 80%
   - [ ] 整合測試通過
   - [ ] 向後兼容測試通過

3. **驗證完成**
   - [ ] `from agent_framework.workflows import RequestResponseExecutor` 成功
   - [ ] 現有審批功能無退化
   - [ ] 代碼審查完成

---

## 相關文檔

- [Sprint 27 Plan](./sprint-27-plan.md) - 執行引擎遷移
- [Sprint 29 Plan](./sprint-29-plan.md) - API Routes 遷移
- [Workflows API Reference - Human-in-the-Loop](../../../../.claude/skills/microsoft-agent-framework/references/workflows-api.md#human-in-the-loop)
