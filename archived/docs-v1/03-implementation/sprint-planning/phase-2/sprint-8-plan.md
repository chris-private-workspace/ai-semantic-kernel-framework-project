# Sprint 8: 智能交接機制 - Agent Handoff

**Sprint 目標**: 實現 Agent 之間的動態責任轉移和協作協議
**週期**: Week 17-18 (2 週)
**Story Points**: 31 點
**Phase 2 功能**: P2-F3 (Agent Handoff 交接機制), P2-F4 (Collaboration Protocol 協作協議)

---

## Sprint 概覽

### 目標
1. 實現 Agent 之間的動態 Handoff 機制
2. 建立協作協議 (Collaboration Protocol)
3. 支援條件式和事件驅動的交接
4. 實現交接狀態追蹤和審計
5. 建立交接失敗的回滾機制

### 成功標準
- [ ] Agent 可根據條件自動將任務交接給其他 Agent
- [ ] 交接過程中上下文完整傳遞
- [ ] 支援雙向交接 (A↔B)
- [ ] 交接失敗可自動回滾或升級
- [ ] 所有交接有完整審計記錄

---

## 核心概念

### Handoff 架構

```
┌─────────────────────────────────────────────────────────────────┐
│                        Agent Handoff Flow                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────┐                      ┌─────────────┐           │
│  │   Agent A   │                      │   Agent B   │           │
│  │  (Source)   │                      │  (Target)   │           │
│  └──────┬──────┘                      └──────▲──────┘           │
│         │                                    │                   │
│         │  1. Trigger Handoff                │                   │
│         ▼                                    │                   │
│  ┌──────────────────────────────────────────┴────────┐          │
│  │                 Handoff Controller                 │          │
│  │  ┌────────────────────────────────────────────┐   │          │
│  │  │ 2. Evaluate Conditions                      │   │          │
│  │  │    - Capability Match                       │   │          │
│  │  │    - Availability Check                     │   │          │
│  │  │    - Permission Validation                  │   │          │
│  │  └────────────────────────────────────────────┘   │          │
│  │  ┌────────────────────────────────────────────┐   │          │
│  │  │ 3. Prepare Context Transfer                 │   │          │
│  │  │    - Task State                             │   │          │
│  │  │    - Conversation History                   │   │          │
│  │  │    - Relevant Data                          │   │          │
│  │  └────────────────────────────────────────────┘   │          │
│  │  ┌────────────────────────────────────────────┐   │          │
│  │  │ 4. Execute Transfer                         │   │          │
│  │  │    - Lock Source Agent                      │   │          │
│  │  │    - Initialize Target Agent                │   │          │
│  │  │    - Confirm Handoff                        │   │          │
│  │  └────────────────────────────────────────────┘   │          │
│  └───────────────────────────────────────────────────┘          │
│                                                                   │
│  ┌───────────────────────────────────────────────────┐          │
│  │                    Audit Trail                     │          │
│  │  [Handoff Initiated] → [Validated] → [Completed]   │          │
│  └───────────────────────────────────────────────────┘          │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Microsoft Agent Framework Handoff API

```python
# Agent Framework 交接相關 API (概念)
from agent_framework import (
    HandoffExecutor,
    TransferContext,
    HandoffPolicy,
)

# 交接策略
class HandoffPolicy:
    IMMEDIATE = "immediate"      # 立即交接
    GRACEFUL = "graceful"        # 優雅交接 (等待當前任務完成)
    CONDITIONAL = "conditional"  # 條件式交接
```

---

## User Stories

### S8-1: Agent Handoff 核心機制 (13 點)

**描述**: 作為開發者，我需要讓 Agent 能夠將任務交接給更適合的 Agent 處理。

**驗收標準**:
- [ ] 支援基於條件的自動交接
- [ ] 交接時完整傳遞任務上下文
- [ ] 支援優雅交接 (不中斷當前操作)
- [ ] 交接成功後源 Agent 正確釋放資源

**技術任務**:

1. **Handoff 控制器 (src/domain/workflows/handoff/controller.py)**
```python
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum
import asyncio

from src.domain.agents.service import AgentService


class HandoffStatus(str, Enum):
    """交接狀態"""
    INITIATED = "initiated"
    VALIDATING = "validating"
    TRANSFERRING = "transferring"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class HandoffPolicy(str, Enum):
    """交接策略"""
    IMMEDIATE = "immediate"      # 立即交接
    GRACEFUL = "graceful"        # 優雅交接
    CONDITIONAL = "conditional"  # 條件式交接


@dataclass
class HandoffContext:
    """交接上下文"""
    task_id: str
    task_state: Dict[str, Any]
    conversation_history: List[Dict[str, Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    timeout: int = 300  # 秒


@dataclass
class HandoffRequest:
    """交接請求"""
    id: UUID = field(default_factory=uuid4)
    source_agent_id: UUID = None
    target_agent_id: UUID = None
    context: HandoffContext = None
    policy: HandoffPolicy = HandoffPolicy.GRACEFUL
    reason: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class HandoffResult:
    """交接結果"""
    request_id: UUID
    status: HandoffStatus
    source_agent_id: UUID
    target_agent_id: UUID
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    rollback_performed: bool = False


class HandoffController:
    """
    交接控制器

    管理 Agent 之間的任務交接
    """

    def __init__(
        self,
        agent_service: AgentService,
        audit_logger,
    ):
        self._agent_service = agent_service
        self._audit = audit_logger
        self._active_handoffs: Dict[UUID, HandoffRequest] = {}

    async def initiate_handoff(
        self,
        source_agent_id: UUID,
        target_agent_id: UUID,
        context: HandoffContext,
        policy: HandoffPolicy = HandoffPolicy.GRACEFUL,
        reason: str = "",
    ) -> HandoffRequest:
        """發起交接請求"""
        request = HandoffRequest(
            source_agent_id=source_agent_id,
            target_agent_id=target_agent_id,
            context=context,
            policy=policy,
            reason=reason,
        )

        self._active_handoffs[request.id] = request

        # 記錄審計
        await self._audit.log(
            action="handoff.initiated",
            actor="system",
            actor_type="system",
            details={
                "handoff_id": str(request.id),
                "source_agent": str(source_agent_id),
                "target_agent": str(target_agent_id),
                "reason": reason,
            },
        )

        return request

    async def execute_handoff(
        self,
        request: HandoffRequest,
    ) -> HandoffResult:
        """執行交接"""
        try:
            # 1. 驗證交接條件
            await self._validate_handoff(request)

            # 2. 根據策略執行
            if request.policy == HandoffPolicy.IMMEDIATE:
                result = await self._immediate_handoff(request)
            elif request.policy == HandoffPolicy.GRACEFUL:
                result = await self._graceful_handoff(request)
            else:
                result = await self._conditional_handoff(request)

            # 3. 清理
            del self._active_handoffs[request.id]

            return result

        except Exception as e:
            # 交接失敗，嘗試回滾
            await self._rollback_handoff(request)

            return HandoffResult(
                request_id=request.id,
                status=HandoffStatus.FAILED,
                source_agent_id=request.source_agent_id,
                target_agent_id=request.target_agent_id,
                error=str(e),
                rollback_performed=True,
            )

    async def _validate_handoff(self, request: HandoffRequest) -> None:
        """驗證交接條件"""
        # 檢查源 Agent 是否存在且可用
        source_agent = await self._agent_service.get_agent(request.source_agent_id)
        if not source_agent:
            raise ValueError(f"Source agent {request.source_agent_id} not found")

        # 檢查目標 Agent 是否存在且可用
        target_agent = await self._agent_service.get_agent(request.target_agent_id)
        if not target_agent:
            raise ValueError(f"Target agent {request.target_agent_id} not found")

        # 檢查目標 Agent 是否有處理能力
        if not await self._check_capability(target_agent, request.context):
            raise ValueError(f"Target agent lacks required capability")

    async def _check_capability(
        self,
        agent,
        context: HandoffContext,
    ) -> bool:
        """檢查 Agent 能力"""
        # TODO: 實現能力匹配邏輯
        return True

    async def _immediate_handoff(
        self,
        request: HandoffRequest,
    ) -> HandoffResult:
        """立即交接"""
        # 1. 暫停源 Agent
        await self._agent_service.pause_agent(request.source_agent_id)

        # 2. 傳輸上下文
        await self._transfer_context(request)

        # 3. 激活目標 Agent
        await self._agent_service.activate_agent(
            request.target_agent_id,
            context=request.context.task_state,
        )

        # 4. 釋放源 Agent
        await self._agent_service.release_agent(request.source_agent_id)

        return HandoffResult(
            request_id=request.id,
            status=HandoffStatus.COMPLETED,
            source_agent_id=request.source_agent_id,
            target_agent_id=request.target_agent_id,
            completed_at=datetime.utcnow(),
        )

    async def _graceful_handoff(
        self,
        request: HandoffRequest,
    ) -> HandoffResult:
        """優雅交接 - 等待當前任務完成"""
        # 1. 標記源 Agent 為交接中
        await self._agent_service.mark_handoff_pending(request.source_agent_id)

        # 2. 等待當前任務完成
        await self._wait_for_completion(
            request.source_agent_id,
            timeout=request.context.timeout,
        )

        # 3. 執行實際交接
        return await self._immediate_handoff(request)

    async def _conditional_handoff(
        self,
        request: HandoffRequest,
    ) -> HandoffResult:
        """條件式交接"""
        # 評估條件後決定是否交接
        should_handoff = await self._evaluate_conditions(request)

        if should_handoff:
            return await self._graceful_handoff(request)
        else:
            return HandoffResult(
                request_id=request.id,
                status=HandoffStatus.FAILED,
                source_agent_id=request.source_agent_id,
                target_agent_id=request.target_agent_id,
                error="Handoff conditions not met",
            )

    async def _transfer_context(self, request: HandoffRequest) -> None:
        """傳輸上下文到目標 Agent"""
        context_data = {
            "task_id": request.context.task_id,
            "task_state": request.context.task_state,
            "conversation_history": request.context.conversation_history,
            "metadata": request.context.metadata,
            "handoff_reason": request.reason,
            "source_agent_id": str(request.source_agent_id),
        }

        await self._agent_service.inject_context(
            request.target_agent_id,
            context_data,
        )

    async def _wait_for_completion(
        self,
        agent_id: UUID,
        timeout: int,
    ) -> None:
        """等待 Agent 完成當前任務"""
        start_time = datetime.utcnow()

        while True:
            status = await self._agent_service.get_agent_status(agent_id)

            if status in ["idle", "ready"]:
                return

            elapsed = (datetime.utcnow() - start_time).total_seconds()
            if elapsed > timeout:
                raise TimeoutError(f"Agent {agent_id} did not complete within timeout")

            await asyncio.sleep(1)

    async def _evaluate_conditions(self, request: HandoffRequest) -> bool:
        """評估交接條件"""
        # TODO: 實現條件評估邏輯
        return True

    async def _rollback_handoff(self, request: HandoffRequest) -> None:
        """回滾交接"""
        try:
            # 恢復源 Agent
            await self._agent_service.restore_agent(request.source_agent_id)

            # 記錄回滾
            await self._audit.log(
                action="handoff.rolled_back",
                actor="system",
                actor_type="system",
                details={
                    "handoff_id": str(request.id),
                    "source_agent": str(request.source_agent_id),
                    "target_agent": str(request.target_agent_id),
                },
            )
        except Exception as e:
            # 回滾也失敗，記錄錯誤
            await self._audit.log(
                action="handoff.rollback_failed",
                actor="system",
                actor_type="system",
                details={
                    "handoff_id": str(request.id),
                    "error": str(e),
                },
            )
```

2. **Handoff 觸發器 (src/domain/workflows/handoff/triggers.py)**
```python
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from uuid import UUID


class HandoffTriggerType(str, Enum):
    """交接觸發類型"""
    CONDITION = "condition"      # 條件觸發
    EVENT = "event"              # 事件觸發
    EXPLICIT = "explicit"        # 明確指令觸發
    TIMEOUT = "timeout"          # 超時觸發
    ERROR = "error"              # 錯誤觸發
    CAPABILITY = "capability"    # 能力不足觸發


@dataclass
class HandoffTriggerCondition:
    """交接觸發條件"""
    trigger_type: HandoffTriggerType
    condition_expression: Optional[str] = None  # 條件表達式
    event_name: Optional[str] = None
    timeout_seconds: Optional[int] = None
    error_types: Optional[List[str]] = None
    capability_requirements: Optional[List[str]] = None


class HandoffTriggerEvaluator:
    """
    交接觸發評估器

    評估是否應該觸發交接
    """

    def __init__(self):
        self._evaluators: Dict[HandoffTriggerType, Callable] = {
            HandoffTriggerType.CONDITION: self._evaluate_condition,
            HandoffTriggerType.EVENT: self._evaluate_event,
            HandoffTriggerType.TIMEOUT: self._evaluate_timeout,
            HandoffTriggerType.ERROR: self._evaluate_error,
            HandoffTriggerType.CAPABILITY: self._evaluate_capability,
        }

    async def should_trigger(
        self,
        condition: HandoffTriggerCondition,
        context: Dict[str, Any],
    ) -> bool:
        """評估是否應該觸發交接"""
        evaluator = self._evaluators.get(condition.trigger_type)
        if evaluator:
            return await evaluator(condition, context)
        return False

    async def _evaluate_condition(
        self,
        condition: HandoffTriggerCondition,
        context: Dict[str, Any],
    ) -> bool:
        """評估條件表達式"""
        if not condition.condition_expression:
            return False

        # 安全評估表達式
        try:
            # 使用簡單的條件解析
            return self._parse_condition(
                condition.condition_expression,
                context,
            )
        except Exception:
            return False

    def _parse_condition(
        self,
        expression: str,
        context: Dict[str, Any],
    ) -> bool:
        """解析條件表達式"""
        # 支援簡單的比較表達式
        # 例如: "confidence < 0.5" 或 "error_count > 3"
        import re

        # 解析表達式
        match = re.match(r'(\w+)\s*(==|!=|<|>|<=|>=)\s*(.+)', expression.strip())
        if not match:
            return False

        field, operator, value = match.groups()
        field_value = context.get(field)

        if field_value is None:
            return False

        # 轉換值類型
        try:
            if value.replace('.', '').isdigit():
                value = float(value)
            elif value.lower() in ('true', 'false'):
                value = value.lower() == 'true'
        except ValueError:
            pass

        # 比較
        ops = {
            '==': lambda a, b: a == b,
            '!=': lambda a, b: a != b,
            '<': lambda a, b: a < b,
            '>': lambda a, b: a > b,
            '<=': lambda a, b: a <= b,
            '>=': lambda a, b: a >= b,
        }

        return ops.get(operator, lambda a, b: False)(field_value, value)

    async def _evaluate_event(
        self,
        condition: HandoffTriggerCondition,
        context: Dict[str, Any],
    ) -> bool:
        """評估事件觸發"""
        if not condition.event_name:
            return False

        triggered_events = context.get("triggered_events", [])
        return condition.event_name in triggered_events

    async def _evaluate_timeout(
        self,
        condition: HandoffTriggerCondition,
        context: Dict[str, Any],
    ) -> bool:
        """評估超時觸發"""
        if not condition.timeout_seconds:
            return False

        elapsed = context.get("elapsed_seconds", 0)
        return elapsed >= condition.timeout_seconds

    async def _evaluate_error(
        self,
        condition: HandoffTriggerCondition,
        context: Dict[str, Any],
    ) -> bool:
        """評估錯誤觸發"""
        error_type = context.get("error_type")
        if not error_type:
            return False

        if condition.error_types:
            return error_type in condition.error_types
        return True  # 任何錯誤都觸發

    async def _evaluate_capability(
        self,
        condition: HandoffTriggerCondition,
        context: Dict[str, Any],
    ) -> bool:
        """評估能力觸發"""
        if not condition.capability_requirements:
            return False

        agent_capabilities = set(context.get("agent_capabilities", []))
        required = set(condition.capability_requirements)

        # 如果缺少任何必要能力，則觸發交接
        return not required.issubset(agent_capabilities)
```

---

### S8-2: 協作協議實現 (13 點)

**描述**: 作為開發者，我需要建立 Agent 間的協作協議，確保交接過程標準化。

**驗收標準**:
- [ ] 定義標準的協作消息格式
- [ ] 支援請求-回應模式
- [ ] 支援廣播模式
- [ ] 支援協商模式

**技術任務**:

1. **協作協議定義 (src/domain/workflows/handoff/protocol.py)**
```python
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum


class MessageType(str, Enum):
    """協作消息類型"""
    REQUEST = "request"          # 請求
    RESPONSE = "response"        # 回應
    BROADCAST = "broadcast"      # 廣播
    NEGOTIATE = "negotiate"      # 協商
    ACKNOWLEDGE = "acknowledge"  # 確認
    REJECT = "reject"            # 拒絕
    CANCEL = "cancel"            # 取消


class CollaborationPhase(str, Enum):
    """協作階段"""
    DISCOVERY = "discovery"      # 發現可用 Agent
    NEGOTIATION = "negotiation"  # 協商
    AGREEMENT = "agreement"      # 達成協議
    EXECUTION = "execution"      # 執行
    COMPLETION = "completion"    # 完成


@dataclass
class CollaborationMessage:
    """協作消息"""
    id: UUID = field(default_factory=uuid4)
    type: MessageType = MessageType.REQUEST
    sender_id: UUID = None
    receiver_id: Optional[UUID] = None  # None 表示廣播
    correlation_id: Optional[UUID] = None  # 關聯的原始消息
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    ttl: int = 60  # 消息存活時間(秒)


@dataclass
class CollaborationSession:
    """協作會話"""
    id: UUID = field(default_factory=uuid4)
    initiator_id: UUID = None
    participants: List[UUID] = field(default_factory=list)
    phase: CollaborationPhase = CollaborationPhase.DISCOVERY
    messages: List[CollaborationMessage] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class CollaborationProtocol:
    """
    協作協議

    定義 Agent 間協作的標準流程
    """

    def __init__(self):
        self._sessions: Dict[UUID, CollaborationSession] = {}
        self._message_handlers: Dict[MessageType, List[callable]] = {}

    def create_session(
        self,
        initiator_id: UUID,
        participants: List[UUID] = None,
        context: Dict[str, Any] = None,
    ) -> CollaborationSession:
        """創建協作會話"""
        session = CollaborationSession(
            initiator_id=initiator_id,
            participants=participants or [],
            context=context or {},
        )
        self._sessions[session.id] = session
        return session

    def get_session(self, session_id: UUID) -> Optional[CollaborationSession]:
        """獲取會話"""
        return self._sessions.get(session_id)

    async def send_message(
        self,
        session_id: UUID,
        message: CollaborationMessage,
    ) -> None:
        """發送協作消息"""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # 記錄消息
        session.messages.append(message)

        # 觸發處理器
        handlers = self._message_handlers.get(message.type, [])
        for handler in handlers:
            await handler(session, message)

    def register_handler(
        self,
        message_type: MessageType,
        handler: callable,
    ) -> None:
        """註冊消息處理器"""
        if message_type not in self._message_handlers:
            self._message_handlers[message_type] = []
        self._message_handlers[message_type].append(handler)

    async def request_handoff(
        self,
        session: CollaborationSession,
        target_id: UUID,
        task_description: str,
        requirements: List[str] = None,
    ) -> CollaborationMessage:
        """請求交接"""
        message = CollaborationMessage(
            type=MessageType.REQUEST,
            sender_id=session.initiator_id,
            receiver_id=target_id,
            payload={
                "action": "handoff_request",
                "task_description": task_description,
                "requirements": requirements or [],
                "session_id": str(session.id),
            },
        )

        await self.send_message(session.id, message)
        session.phase = CollaborationPhase.NEGOTIATION

        return message

    async def respond_to_request(
        self,
        session: CollaborationSession,
        original_message_id: UUID,
        accepted: bool,
        reason: str = "",
        counter_proposal: Dict[str, Any] = None,
    ) -> CollaborationMessage:
        """回應請求"""
        message_type = MessageType.ACKNOWLEDGE if accepted else MessageType.REJECT

        message = CollaborationMessage(
            type=message_type,
            sender_id=session.initiator_id,  # 會被實際發送者覆蓋
            correlation_id=original_message_id,
            payload={
                "accepted": accepted,
                "reason": reason,
                "counter_proposal": counter_proposal,
            },
        )

        await self.send_message(session.id, message)

        if accepted:
            session.phase = CollaborationPhase.AGREEMENT
        elif counter_proposal:
            session.phase = CollaborationPhase.NEGOTIATION

        return message

    async def broadcast_capability_query(
        self,
        session: CollaborationSession,
        required_capabilities: List[str],
    ) -> CollaborationMessage:
        """廣播能力查詢"""
        message = CollaborationMessage(
            type=MessageType.BROADCAST,
            sender_id=session.initiator_id,
            receiver_id=None,  # 廣播
            payload={
                "action": "capability_query",
                "required_capabilities": required_capabilities,
            },
        )

        await self.send_message(session.id, message)
        return message

    async def negotiate_terms(
        self,
        session: CollaborationSession,
        target_id: UUID,
        proposed_terms: Dict[str, Any],
    ) -> CollaborationMessage:
        """協商條款"""
        message = CollaborationMessage(
            type=MessageType.NEGOTIATE,
            sender_id=session.initiator_id,
            receiver_id=target_id,
            payload={
                "action": "negotiate_terms",
                "proposed_terms": proposed_terms,
            },
        )

        await self.send_message(session.id, message)
        return message

    async def finalize_session(
        self,
        session: CollaborationSession,
        outcome: str,
        result: Dict[str, Any] = None,
    ) -> None:
        """完成協作會話"""
        session.phase = CollaborationPhase.COMPLETION
        session.completed_at = datetime.utcnow()
        session.context["outcome"] = outcome
        session.context["result"] = result

    def cleanup_expired_sessions(self, max_age_hours: int = 24) -> int:
        """清理過期會話"""
        from datetime import timedelta

        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        expired_ids = [
            sid for sid, session in self._sessions.items()
            if session.created_at < cutoff
        ]

        for sid in expired_ids:
            del self._sessions[sid]

        return len(expired_ids)
```

2. **能力匹配服務 (src/domain/workflows/handoff/capability_matcher.py)**
```python
from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from uuid import UUID


@dataclass
class AgentCapability:
    """Agent 能力定義"""
    name: str
    description: str
    proficiency: float = 1.0  # 0.0 - 1.0
    tags: List[str] = None


@dataclass
class CapabilityMatch:
    """能力匹配結果"""
    agent_id: UUID
    agent_name: str
    match_score: float  # 0.0 - 1.0
    matched_capabilities: List[str]
    missing_capabilities: List[str]


class CapabilityMatcher:
    """
    能力匹配服務

    根據所需能力找到最合適的 Agent
    """

    def __init__(self):
        self._agent_capabilities: Dict[UUID, List[AgentCapability]] = {}

    def register_agent_capabilities(
        self,
        agent_id: UUID,
        capabilities: List[AgentCapability],
    ) -> None:
        """註冊 Agent 能力"""
        self._agent_capabilities[agent_id] = capabilities

    def unregister_agent(self, agent_id: UUID) -> None:
        """取消註冊"""
        if agent_id in self._agent_capabilities:
            del self._agent_capabilities[agent_id]

    def find_matching_agents(
        self,
        required_capabilities: List[str],
        exclude_agents: List[UUID] = None,
        min_score: float = 0.5,
    ) -> List[CapabilityMatch]:
        """查找匹配的 Agent"""
        matches = []
        exclude_set = set(exclude_agents or [])

        for agent_id, capabilities in self._agent_capabilities.items():
            if agent_id in exclude_set:
                continue

            match = self._calculate_match(
                agent_id,
                capabilities,
                required_capabilities,
            )

            if match.match_score >= min_score:
                matches.append(match)

        # 按匹配分數排序
        return sorted(matches, key=lambda m: m.match_score, reverse=True)

    def _calculate_match(
        self,
        agent_id: UUID,
        capabilities: List[AgentCapability],
        required: List[str],
    ) -> CapabilityMatch:
        """計算匹配分數"""
        capability_names = {c.name: c for c in capabilities}
        required_set = set(required)

        matched = []
        missing = []

        weighted_score = 0.0
        max_score = len(required_set)

        for req in required_set:
            if req in capability_names:
                matched.append(req)
                # 考慮熟練度
                weighted_score += capability_names[req].proficiency
            else:
                missing.append(req)

        match_score = weighted_score / max_score if max_score > 0 else 0.0

        return CapabilityMatch(
            agent_id=agent_id,
            agent_name="",  # 需要從外部獲取
            match_score=match_score,
            matched_capabilities=matched,
            missing_capabilities=missing,
        )

    def get_best_agent(
        self,
        required_capabilities: List[str],
        exclude_agents: List[UUID] = None,
    ) -> Optional[CapabilityMatch]:
        """獲取最佳匹配的 Agent"""
        matches = self.find_matching_agents(
            required_capabilities,
            exclude_agents,
        )
        return matches[0] if matches else None
```

---

### S8-3: Handoff API 和審計 (5 點)

**描述**: 作為系統管理員，我需要 API 來管理交接並查看審計記錄。

**驗收標準**:
- [ ] 提供交接管理 API
- [ ] 所有交接操作有審計記錄
- [ ] 支援查詢交接歷史

**技術任務**:

1. **Handoff API (src/api/v1/handoff/routes.py)**
```python
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from uuid import UUID

from src.domain.workflows.handoff.controller import (
    HandoffController,
    HandoffContext,
    HandoffPolicy,
    HandoffStatus,
)


router = APIRouter(prefix="/handoff", tags=["handoff"])


class HandoffRequest(BaseModel):
    source_agent_id: UUID
    target_agent_id: UUID
    task_id: str
    task_state: Dict[str, Any]
    conversation_history: List[Dict[str, Any]] = []
    policy: str = "graceful"
    reason: str = ""


class HandoffResponse(BaseModel):
    handoff_id: UUID
    status: str
    source_agent_id: UUID
    target_agent_id: UUID
    error: Optional[str] = None


@router.post("/initiate", response_model=HandoffResponse)
async def initiate_handoff(
    request: HandoffRequest,
    controller: HandoffController = Depends(),
):
    """發起 Agent 交接"""
    context = HandoffContext(
        task_id=request.task_id,
        task_state=request.task_state,
        conversation_history=request.conversation_history,
    )

    try:
        handoff_request = await controller.initiate_handoff(
            source_agent_id=request.source_agent_id,
            target_agent_id=request.target_agent_id,
            context=context,
            policy=HandoffPolicy(request.policy),
            reason=request.reason,
        )

        result = await controller.execute_handoff(handoff_request)

        return HandoffResponse(
            handoff_id=result.request_id,
            status=result.status.value,
            source_agent_id=result.source_agent_id,
            target_agent_id=result.target_agent_id,
            error=result.error,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{agent_id}")
async def get_handoff_history(
    agent_id: UUID,
    limit: int = 50,
    controller: HandoffController = Depends(),
):
    """獲取 Agent 的交接歷史"""
    # TODO: 實現歷史查詢
    return {"agent_id": str(agent_id), "history": []}


@router.get("/capability-match")
async def find_capable_agents(
    capabilities: str,  # 逗號分隔的能力列表
    exclude: Optional[str] = None,
    controller: HandoffController = Depends(),
):
    """查找具有特定能力的 Agent"""
    required = [c.strip() for c in capabilities.split(",")]
    exclude_list = [UUID(e.strip()) for e in exclude.split(",")] if exclude else []

    # TODO: 調用 CapabilityMatcher
    return {"required": required, "matches": []}
```

---

## 時間規劃

### Week 17 (Day 1-5)

| 日期 | 任務 | 負責人 | 產出 |
|------|------|--------|------|
| Day 1-2 | S8-1: HandoffController 核心 | Backend | controller.py |
| Day 2-3 | S8-1: HandoffTrigger 評估器 | Backend | triggers.py |
| Day 3-4 | S8-2: CollaborationProtocol | Backend | protocol.py |
| Day 4-5 | S8-2: 消息處理和會話管理 | Backend | protocol.py |

### Week 18 (Day 6-10)

| 日期 | 任務 | 負責人 | 產出 |
|------|------|--------|------|
| Day 6-7 | S8-2: CapabilityMatcher | Backend | capability_matcher.py |
| Day 7-8 | S8-3: Handoff API | Backend | routes.py |
| Day 8-9 | S8-3: 審計集成 | Backend | audit integration |
| Day 9-10 | 單元測試 + 集成測試 | 全員 | 測試用例 |

---

## 完成定義 (Definition of Done)

1. **功能完成**
   - [ ] Handoff 支援三種策略
   - [ ] 協作協議支援四種消息類型
   - [ ] 能力匹配正常運作
   - [ ] API 完整可用

2. **測試完成**
   - [ ] 單元測試覆蓋率 >= 80%
   - [ ] 交接集成測試通過
   - [ ] 回滾場景測試通過

3. **文檔完成**
   - [ ] Handoff API 文檔
   - [ ] 協作協議規範
   - [ ] 能力配置指南

---

## 相關文檔

- [Phase 2 Overview](./README.md)
- [Sprint 7 Plan](./sprint-7-plan.md) - 前置 Sprint
- [Sprint 9 Plan](./sprint-9-plan.md) - 後續 Sprint
