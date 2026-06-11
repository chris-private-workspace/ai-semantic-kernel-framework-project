# Sprint 3: 集成 & 可靠性

**Sprint 目標**: 實現外部觸發、通知系統和完整審計追蹤
**週期**: Week 7-8 (2 週)
**Story Points**: 40 點
**MVP 功能**: F4 (跨場景協作), F8 (n8n 觸發), F9 (Prompt 管理), F10 (審計追蹤), F11 (Teams 通知)

---

## Sprint 概覽

### 目標
1. 實現 n8n 觸發和錯誤處理機制
2. 建立 Prompt 模板管理系統
3. 實現 Append-only 審計日誌
4. 集成 Microsoft Teams 通知
5. 支持跨場景 (CS↔IT) 協作

### 成功標準
- [ ] n8n 可觸發工作流執行
- [ ] Prompt 模板可通過 YAML 管理
- [ ] 所有關鍵操作有審計記錄
- [ ] Teams 通知可正確推送
- [ ] 跨場景路由正常運作

---

## 系統架構

### 集成架構圖

```
┌─────────────────────────────────────────────────────────────────┐
│                        外部觸發源                                │
├───────────────┬───────────────────────┬─────────────────────────┤
│               │                       │                         │
│  ┌──────────┐ │    ┌──────────────┐   │   ┌───────────────┐     │
│  │   n8n    │ │    │   Webhook    │   │   │   Schedule    │     │
│  │ Workflow │ │    │   Endpoint   │   │   │   (APScheduler│     │
│  └────┬─────┘ │    └──────┬───────┘   │   └───────┬───────┘     │
│       │       │           │           │           │             │
└───────┼───────┴───────────┼───────────┴───────────┼─────────────┘
        │                   │                       │
        └───────────────────┼───────────────────────┘
                            │
                    ┌───────▼───────┐
                    │  IPA Platform │
                    │   Trigger     │
                    │   Service     │
                    └───────┬───────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼───────┐   ┌───────▼───────┐   ┌───────▼───────┐
│   Workflow    │   │   Prompt      │   │   Audit       │
│   Execution   │   │   Manager     │   │   Logger      │
└───────┬───────┘   └───────────────┘   └───────────────┘
        │
        │ 完成/錯誤
        │
┌───────▼───────────────────────────────────────────────┐
│                  Notification Service                  │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐  │
│  │   Teams     │   │   Email     │   │   Webhook   │  │
│  │   Adaptive  │   │   (Future)  │   │   Callback  │  │
│  │   Card      │   │             │   │             │  │
│  └─────────────┘   └─────────────┘   └─────────────┘  │
└───────────────────────────────────────────────────────┘
```

---

## User Stories

### S3-1: n8n 觸發與錯誤處理 (10 點)

**描述**: 作為開發者，我需要讓 n8n 可以觸發 IPA 工作流，並正確處理錯誤。

**驗收標準**:
- [ ] n8n 可通過 Webhook 觸發工作流
- [ ] 觸發支持帶參數
- [ ] 錯誤可回調 n8n
- [ ] 支持重試機制

**技術任務**:

1. **Webhook 觸發服務 (src/domain/triggers/webhook.py)**
```python
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from dataclasses import dataclass
import hmac
import hashlib

from src.domain.workflows.execution_service import WorkflowExecutionService
from src.domain.audit.logger import AuditLogger


@dataclass
class WebhookTriggerConfig:
    """Webhook 觸發配置"""
    workflow_id: UUID
    secret: str  # 用於驗證請求
    enabled: bool = True
    retry_count: int = 3
    retry_delay: int = 60  # seconds


class WebhookTriggerService:
    """Webhook 觸發服務"""

    def __init__(
        self,
        execution_service: WorkflowExecutionService,
        audit_logger: AuditLogger,
    ):
        self._execution_service = execution_service
        self._audit = audit_logger

    def verify_signature(self, payload: bytes, signature: str, secret: str) -> bool:
        """驗證 Webhook 簽名"""
        expected = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    async def trigger(
        self,
        config: WebhookTriggerConfig,
        payload: Dict[str, Any],
        source: str = "n8n",
    ) -> UUID:
        """觸發工作流執行"""
        # 記錄審計日誌
        await self._audit.log(
            action="workflow.triggered",
            actor=source,
            actor_type="system",
            details={
                "workflow_id": str(config.workflow_id),
                "source": source,
                "payload_keys": list(payload.keys()),
            },
        )

        # 執行工作流
        execution_id = await self._execution_service.execute_workflow(
            workflow_id=config.workflow_id,
            input_data=payload,
        )

        return execution_id

    async def handle_error(
        self,
        execution_id: UUID,
        error: Exception,
        callback_url: Optional[str] = None,
    ) -> None:
        """處理執行錯誤"""
        await self._audit.log(
            action="workflow.error",
            actor="system",
            actor_type="system",
            details={
                "execution_id": str(execution_id),
                "error": str(error),
                "error_type": type(error).__name__,
            },
        )

        # 回調 n8n
        if callback_url:
            import httpx
            async with httpx.AsyncClient() as client:
                await client.post(
                    callback_url,
                    json={
                        "execution_id": str(execution_id),
                        "status": "failed",
                        "error": str(error),
                    },
                )
```

2. **Webhook API (src/api/v1/triggers/routes.py)**
```python
from fastapi import APIRouter, HTTPException, Request, Depends, Header
from pydantic import BaseModel
from typing import Optional, Dict, Any
from uuid import UUID

from src.domain.triggers.webhook import WebhookTriggerService, WebhookTriggerConfig


router = APIRouter(prefix="/triggers", tags=["triggers"])


class WebhookPayload(BaseModel):
    data: Dict[str, Any]
    callback_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TriggerResponse(BaseModel):
    execution_id: UUID
    status: str


@router.post("/webhook/{workflow_id}", response_model=TriggerResponse)
async def trigger_workflow(
    workflow_id: UUID,
    payload: WebhookPayload,
    request: Request,
    x_webhook_signature: Optional[str] = Header(None),
    trigger_service: WebhookTriggerService = Depends(),
):
    """
    Webhook 觸發工作流

    用於 n8n 或其他外部系統觸發 IPA 工作流。
    支持可選的 HMAC 簽名驗證。
    """
    # 獲取工作流配置
    config = await get_webhook_config(workflow_id)
    if not config:
        raise HTTPException(status_code=404, detail="Workflow not found or webhook not enabled")

    # 驗證簽名 (如果提供)
    if x_webhook_signature:
        body = await request.body()
        if not trigger_service.verify_signature(body, x_webhook_signature, config.secret):
            raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        execution_id = await trigger_service.trigger(
            config=config,
            payload=payload.data,
            source="webhook",
        )
        return TriggerResponse(execution_id=execution_id, status="started")

    except Exception as e:
        if payload.callback_url:
            await trigger_service.handle_error(
                execution_id=None,
                error=e,
                callback_url=payload.callback_url,
            )
        raise HTTPException(status_code=500, detail=str(e))
```

---

### S3-2: Prompt 模板管理 (8 點)

**描述**: 作為開發者，我需要通過 YAML 管理 Agent Prompt 模板。

**驗收標準**:
- [ ] Prompt 可通過 YAML 定義
- [ ] 支持變量替換
- [ ] 支持版本管理
- [ ] API 可獲取和更新模板

**技術任務**:

1. **Prompt 模板引擎 (src/domain/prompts/template.py)**
```python
from typing import Dict, Any, Optional, List
from pathlib import Path
import yaml
from dataclasses import dataclass
from string import Template


@dataclass
class PromptTemplate:
    """Prompt 模板"""
    id: str
    name: str
    description: str
    template: str
    variables: List[str]
    version: int = 1
    category: str = "general"


class PromptTemplateManager:
    """Prompt 模板管理器"""

    def __init__(self, templates_dir: Path):
        self._templates_dir = templates_dir
        self._cache: Dict[str, PromptTemplate] = {}

    def load_templates(self) -> None:
        """從 YAML 文件加載模板"""
        for yaml_file in self._templates_dir.glob("*.yaml"):
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                for template_data in data.get("templates", []):
                    template = PromptTemplate(
                        id=template_data["id"],
                        name=template_data["name"],
                        description=template_data.get("description", ""),
                        template=template_data["template"],
                        variables=template_data.get("variables", []),
                        version=template_data.get("version", 1),
                        category=template_data.get("category", "general"),
                    )
                    self._cache[template.id] = template

    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """獲取模板"""
        return self._cache.get(template_id)

    def render(self, template_id: str, variables: Dict[str, Any]) -> str:
        """渲染模板"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

        # 檢查必要變量
        missing = set(template.variables) - set(variables.keys())
        if missing:
            raise ValueError(f"Missing variables: {missing}")

        # 使用 Template 進行替換
        t = Template(template.template)
        return t.safe_substitute(variables)

    def list_templates(self, category: Optional[str] = None) -> List[PromptTemplate]:
        """列出模板"""
        templates = list(self._cache.values())
        if category:
            templates = [t for t in templates if t.category == category]
        return templates
```

2. **Prompt 模板示例 (prompts/it_operations.yaml)**
```yaml
templates:
  - id: incident_triage
    name: 工單分類 Prompt
    description: 用於自動分類 IT 工單的優先級和類型
    category: it_operations
    version: 1
    variables:
      - ticket_title
      - ticket_description
      - affected_systems
    template: |
      你是一個 IT 運維專家。請分析以下工單並進行分類：

      標題: $ticket_title
      描述: $ticket_description
      受影響系統: $affected_systems

      請提供：
      1. 優先級 (P1-P4)
      2. 類型 (硬體/軟體/網路/安全/其他)
      3. 建議處理團隊
      4. 預估解決時間

      以 JSON 格式回覆。

  - id: incident_resolution
    name: 工單解決建議
    description: 基於歷史數據提供解決建議
    category: it_operations
    version: 1
    variables:
      - ticket_info
      - similar_tickets
    template: |
      基於以下工單信息和歷史相似工單，提供解決建議：

      當前工單:
      $ticket_info

      相似歷史工單:
      $similar_tickets

      請提供：
      1. 根本原因分析
      2. 建議解決步驟
      3. 預防措施
```

3. **Prompt API (src/api/v1/prompts/routes.py)**
```python
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from src.domain.prompts.template import PromptTemplateManager, PromptTemplate


router = APIRouter(prefix="/prompts", tags=["prompts"])


class PromptTemplateResponse(BaseModel):
    id: str
    name: str
    description: str
    variables: List[str]
    version: int
    category: str


class RenderRequest(BaseModel):
    variables: Dict[str, Any]


class RenderResponse(BaseModel):
    rendered: str


@router.get("/templates", response_model=List[PromptTemplateResponse])
async def list_templates(
    category: Optional[str] = None,
    manager: PromptTemplateManager = Depends(),
):
    """列出 Prompt 模板"""
    templates = manager.list_templates(category)
    return [
        PromptTemplateResponse(
            id=t.id,
            name=t.name,
            description=t.description,
            variables=t.variables,
            version=t.version,
            category=t.category,
        )
        for t in templates
    ]


@router.get("/templates/{template_id}", response_model=PromptTemplateResponse)
async def get_template(
    template_id: str,
    manager: PromptTemplateManager = Depends(),
):
    """獲取特定模板"""
    template = manager.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return PromptTemplateResponse(
        id=template.id,
        name=template.name,
        description=template.description,
        variables=template.variables,
        version=template.version,
        category=template.category,
    )


@router.post("/templates/{template_id}/render", response_model=RenderResponse)
async def render_template(
    template_id: str,
    request: RenderRequest,
    manager: PromptTemplateManager = Depends(),
):
    """渲染模板"""
    try:
        rendered = manager.render(template_id, request.variables)
        return RenderResponse(rendered=rendered)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

### S3-3: 審計日誌系統 (10 點)

**描述**: 作為合規人員，我需要完整的操作審計記錄。

**驗收標準**:
- [ ] 所有關鍵操作記錄審計日誌
- [ ] 審計日誌不可修改 (Append-only)
- [ ] 支持按條件查詢
- [ ] 支持導出審計報告

**技術任務**:

1. **審計日誌服務 (src/domain/audit/logger.py)**
```python
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession


class AuditAction(str, Enum):
    """審計動作類型"""
    # 工作流相關
    WORKFLOW_CREATED = "workflow.created"
    WORKFLOW_UPDATED = "workflow.updated"
    WORKFLOW_DELETED = "workflow.deleted"
    WORKFLOW_TRIGGERED = "workflow.triggered"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_ERROR = "workflow.error"

    # Agent 相關
    AGENT_CREATED = "agent.created"
    AGENT_EXECUTED = "agent.executed"
    AGENT_ERROR = "agent.error"

    # 檢查點相關
    CHECKPOINT_CREATED = "checkpoint.created"
    CHECKPOINT_APPROVED = "checkpoint.approved"
    CHECKPOINT_REJECTED = "checkpoint.rejected"

    # 用戶相關
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_PERMISSION_CHANGED = "user.permission_changed"


@dataclass
class AuditEntry:
    """審計條目"""
    id: UUID
    timestamp: datetime
    action: str
    actor: str
    actor_type: str  # "user", "system", "agent"
    execution_id: Optional[UUID]
    details: Dict[str, Any]


class AuditLogger:
    """審計日誌記錄器 - Append-only"""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def log(
        self,
        action: str,
        actor: str,
        actor_type: str = "user",
        execution_id: Optional[UUID] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> UUID:
        """記錄審計日誌"""
        from src.infrastructure.database.models import AuditLogModel

        entry = AuditLogModel(
            id=uuid4(),
            action=action,
            actor=actor,
            actor_type=actor_type,
            execution_id=execution_id,
            details=details or {},
            timestamp=datetime.utcnow(),
        )

        self._session.add(entry)
        await self._session.commit()

        return entry.id

    async def query(
        self,
        action: Optional[str] = None,
        actor: Optional[str] = None,
        execution_id: Optional[UUID] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditEntry]:
        """查詢審計日誌"""
        from sqlalchemy import select
        from src.infrastructure.database.models import AuditLogModel

        query = select(AuditLogModel).order_by(AuditLogModel.timestamp.desc())

        if action:
            query = query.where(AuditLogModel.action == action)
        if actor:
            query = query.where(AuditLogModel.actor == actor)
        if execution_id:
            query = query.where(AuditLogModel.execution_id == execution_id)
        if start_time:
            query = query.where(AuditLogModel.timestamp >= start_time)
        if end_time:
            query = query.where(AuditLogModel.timestamp <= end_time)

        query = query.limit(limit).offset(offset)
        result = await self._session.execute(query)

        return [
            AuditEntry(
                id=row.id,
                timestamp=row.timestamp,
                action=row.action,
                actor=row.actor,
                actor_type=row.actor_type,
                execution_id=row.execution_id,
                details=row.details,
            )
            for row in result.scalars()
        ]

    async def get_execution_trail(self, execution_id: UUID) -> List[AuditEntry]:
        """獲取執行的完整審計軌跡"""
        return await self.query(execution_id=execution_id, limit=1000)
```

2. **審計 API (src/api/v1/audit/routes.py)**
```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from src.domain.audit.logger import AuditLogger


router = APIRouter(prefix="/audit", tags=["audit"])


class AuditEntryResponse(BaseModel):
    id: UUID
    timestamp: datetime
    action: str
    actor: str
    actor_type: str
    execution_id: Optional[UUID]
    details: dict


class AuditQueryParams(BaseModel):
    action: Optional[str] = None
    actor: Optional[str] = None
    execution_id: Optional[UUID] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = 100
    offset: int = 0


@router.get("/logs", response_model=List[AuditEntryResponse])
async def query_audit_logs(
    params: AuditQueryParams = Depends(),
    logger: AuditLogger = Depends(),
):
    """查詢審計日誌"""
    entries = await logger.query(
        action=params.action,
        actor=params.actor,
        execution_id=params.execution_id,
        start_time=params.start_time,
        end_time=params.end_time,
        limit=params.limit,
        offset=params.offset,
    )
    return [
        AuditEntryResponse(
            id=e.id,
            timestamp=e.timestamp,
            action=e.action,
            actor=e.actor,
            actor_type=e.actor_type,
            execution_id=e.execution_id,
            details=e.details,
        )
        for e in entries
    ]


@router.get("/executions/{execution_id}/trail", response_model=List[AuditEntryResponse])
async def get_execution_trail(
    execution_id: UUID,
    logger: AuditLogger = Depends(),
):
    """獲取執行的審計軌跡"""
    entries = await logger.get_execution_trail(execution_id)
    return [
        AuditEntryResponse(
            id=e.id,
            timestamp=e.timestamp,
            action=e.action,
            actor=e.actor,
            actor_type=e.actor_type,
            execution_id=e.execution_id,
            details=e.details,
        )
        for e in entries
    ]
```

---

### S3-4: Teams 通知集成 (8 點)

**描述**: 作為業務用戶，我需要在 Teams 中收到審批請求和執行通知。

**驗收標準**:
- [ ] 審批請求可推送到 Teams
- [ ] 執行完成可發送通知
- [ ] 支持 Adaptive Card 格式
- [ ] 支持配置通知渠道

**技術任務**:

1. **Teams 通知服務 (src/domain/notifications/teams.py)**
```python
from typing import Dict, Any, Optional
from dataclasses import dataclass
import httpx


@dataclass
class TeamsNotificationConfig:
    """Teams 通知配置"""
    webhook_url: str
    enabled: bool = True


class TeamsNotificationService:
    """Teams 通知服務"""

    def __init__(self, config: TeamsNotificationConfig):
        self._config = config

    async def send_approval_request(
        self,
        checkpoint_id: str,
        workflow_name: str,
        content: str,
        approver: Optional[str] = None,
    ) -> bool:
        """發送審批請求通知"""
        card = self._build_approval_card(
            checkpoint_id=checkpoint_id,
            workflow_name=workflow_name,
            content=content,
        )
        return await self._send_card(card)

    async def send_execution_completed(
        self,
        execution_id: str,
        workflow_name: str,
        status: str,
        result_summary: str,
    ) -> bool:
        """發送執行完成通知"""
        card = self._build_completion_card(
            execution_id=execution_id,
            workflow_name=workflow_name,
            status=status,
            result_summary=result_summary,
        )
        return await self._send_card(card)

    async def send_error_alert(
        self,
        execution_id: str,
        workflow_name: str,
        error_message: str,
    ) -> bool:
        """發送錯誤告警"""
        card = self._build_error_card(
            execution_id=execution_id,
            workflow_name=workflow_name,
            error_message=error_message,
        )
        return await self._send_card(card)

    def _build_approval_card(
        self,
        checkpoint_id: str,
        workflow_name: str,
        content: str,
    ) -> Dict[str, Any]:
        """構建審批請求 Adaptive Card"""
        return {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.4",
                        "body": [
                            {
                                "type": "TextBlock",
                                "text": "🔔 審批請求",
                                "weight": "bolder",
                                "size": "large",
                            },
                            {
                                "type": "TextBlock",
                                "text": f"工作流: {workflow_name}",
                                "wrap": True,
                            },
                            {
                                "type": "TextBlock",
                                "text": "待審批內容:",
                                "weight": "bolder",
                            },
                            {
                                "type": "TextBlock",
                                "text": content[:500],  # 限制長度
                                "wrap": True,
                            },
                        ],
                        "actions": [
                            {
                                "type": "Action.OpenUrl",
                                "title": "查看詳情並審批",
                                "url": f"https://app.ipa-platform.com/checkpoints/{checkpoint_id}",
                            },
                        ],
                    },
                }
            ],
        }

    def _build_completion_card(
        self,
        execution_id: str,
        workflow_name: str,
        status: str,
        result_summary: str,
    ) -> Dict[str, Any]:
        """構建完成通知 Adaptive Card"""
        status_emoji = "✅" if status == "completed" else "⚠️"
        return {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.4",
                        "body": [
                            {
                                "type": "TextBlock",
                                "text": f"{status_emoji} 工作流執行完成",
                                "weight": "bolder",
                                "size": "large",
                            },
                            {
                                "type": "FactSet",
                                "facts": [
                                    {"title": "工作流", "value": workflow_name},
                                    {"title": "狀態", "value": status},
                                    {"title": "執行 ID", "value": execution_id[:8]},
                                ],
                            },
                            {
                                "type": "TextBlock",
                                "text": result_summary[:300],
                                "wrap": True,
                            },
                        ],
                    },
                }
            ],
        }

    def _build_error_card(
        self,
        execution_id: str,
        workflow_name: str,
        error_message: str,
    ) -> Dict[str, Any]:
        """構建錯誤告警 Adaptive Card"""
        return {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.4",
                        "body": [
                            {
                                "type": "TextBlock",
                                "text": "🚨 執行錯誤",
                                "weight": "bolder",
                                "size": "large",
                                "color": "attention",
                            },
                            {
                                "type": "TextBlock",
                                "text": f"工作流: {workflow_name}",
                            },
                            {
                                "type": "TextBlock",
                                "text": f"錯誤: {error_message[:200]}",
                                "wrap": True,
                                "color": "attention",
                            },
                        ],
                        "actions": [
                            {
                                "type": "Action.OpenUrl",
                                "title": "查看詳情",
                                "url": f"https://app.ipa-platform.com/executions/{execution_id}",
                            },
                        ],
                    },
                }
            ],
        }

    async def _send_card(self, card: Dict[str, Any]) -> bool:
        """發送 Adaptive Card"""
        if not self._config.enabled:
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self._config.webhook_url,
                    json=card,
                    timeout=10,
                )
                return response.status_code == 200
        except Exception:
            return False
```

---

### S3-5: 跨場景協作 (4 點)

**描述**: 作為業務用戶，我需要 IT 和 CS 工作流可以互相觸發。

**驗收標準**:
- [ ] CS 工單可觸發 IT 工作流
- [ ] IT 工單可查詢相關 CS 記錄
- [ ] 關聯關係正確維護

**技術任務**:

1. **場景路由服務 (src/domain/routing/scenario_router.py)**
```python
from typing import Dict, Any, Optional
from uuid import UUID
from enum import Enum


class Scenario(str, Enum):
    IT_OPERATIONS = "it_operations"
    CUSTOMER_SERVICE = "customer_service"


class ScenarioRouter:
    """跨場景路由服務"""

    def __init__(self, execution_service, audit_logger):
        self._execution_service = execution_service
        self._audit = audit_logger

    async def route_to_scenario(
        self,
        source_scenario: Scenario,
        target_scenario: Scenario,
        source_execution_id: UUID,
        data: Dict[str, Any],
    ) -> UUID:
        """路由到目標場景"""
        # 獲取目標場景的默認工作流
        target_workflow_id = await self._get_default_workflow(target_scenario)

        # 記錄跨場景路由
        await self._audit.log(
            action="scenario.routed",
            actor="system",
            actor_type="system",
            execution_id=source_execution_id,
            details={
                "source_scenario": source_scenario.value,
                "target_scenario": target_scenario.value,
                "target_workflow_id": str(target_workflow_id),
            },
        )

        # 觸發目標工作流
        new_execution_id = await self._execution_service.execute_workflow(
            workflow_id=target_workflow_id,
            input_data={
                **data,
                "_source_scenario": source_scenario.value,
                "_source_execution_id": str(source_execution_id),
            },
        )

        return new_execution_id

    async def _get_default_workflow(self, scenario: Scenario) -> UUID:
        """獲取場景默認工作流"""
        # TODO: 從配置或數據庫獲取
        workflow_mapping = {
            Scenario.IT_OPERATIONS: "...",
            Scenario.CUSTOMER_SERVICE: "...",
        }
        return UUID(workflow_mapping.get(scenario, ""))
```

---

## 時間規劃

### Week 7 (Day 1-5)

| 日期 | 任務 | 負責人 | 產出 |
|------|------|--------|------|
| Day 1-2 | S3-1: Webhook 觸發服務 | Backend | webhook.py |
| Day 2-3 | S3-1: 觸發 API + 錯誤處理 | Backend | triggers/routes.py |
| Day 3-4 | S3-2: Prompt 模板引擎 | Backend | template.py |
| Day 4-5 | S3-2: Prompt API | Backend | prompts/routes.py |

### Week 8 (Day 6-10)

| 日期 | 任務 | 負責人 | 產出 |
|------|------|--------|------|
| Day 6-7 | S3-3: 審計日誌服務 | Backend | logger.py |
| Day 7-8 | S3-3: 審計 API | Backend | audit/routes.py |
| Day 8-9 | S3-4: Teams 通知 | Backend | teams.py |
| Day 9-10 | S3-5: 跨場景路由 + 集成測試 | 全員 | 測試用例 |

---

## 完成定義 (Definition of Done)

1. **功能完成**
   - [ ] n8n 可觸發工作流
   - [ ] Prompt 模板 YAML 可用
   - [ ] 審計日誌完整
   - [ ] Teams 通知可發送

2. **測試完成**
   - [ ] 單元測試覆蓋率 >= 80%
   - [ ] n8n 集成測試通過
   - [ ] Teams 通知測試通過

3. **文檔完成**
   - [ ] n8n 集成指南
   - [ ] Prompt 模板開發指南
   - [ ] 審計日誌查詢指南

---

## 相關文檔

- [Sprint 3 Checklist](./sprint-3-checklist.md)
- [Sprint 2 Plan](./sprint-2-plan.md) - 前置 Sprint
- [Sprint 4 Plan](./sprint-4-plan.md) - 後續 Sprint
