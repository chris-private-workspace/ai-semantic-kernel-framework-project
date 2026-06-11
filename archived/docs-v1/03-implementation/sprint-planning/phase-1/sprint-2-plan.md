# Sprint 2: 工作流 & 檢查點 - Human-in-the-Loop

**Sprint 目標**: 實現檢查點機制和跨系統集成，支持人機協作流程
**週期**: Week 5-6 (2 週)
**Story Points**: 45 點
**MVP 功能**: F2 (人機協作檢查點), F3 (跨系統關聯), F14 (Redis 緩存)

---

## Sprint 概覽

### 目標
1. 實現 Agent Framework 檢查點 (Checkpoint) 機制
2. 建立人機協作 (Human-in-the-loop) 審批流程
3. 集成跨系統連接器 (ServiceNow, Dynamics 365, SharePoint)
4. 實現 Redis 緩存提升 LLM 響應效率
5. 建立工作流暫停/恢復能力

### 成功標準
- [ ] 工作流可在指定步驟暫停等待人工審批
- [ ] 人工審批後工作流可正確恢復執行
- [ ] 跨系統連接器可獲取和推送數據
- [ ] Redis 緩存命中率達到 60%+
- [ ] 檢查點狀態可持久化和恢復

---

## 核心概念

### 檢查點架構

```
┌─────────────────────────────────────────────────────────────┐
│                    Workflow Execution                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐             │
│  │  Step 1  │ ──▶ │  Step 2  │ ──▶ │  Step 3  │             │
│  │  Agent   │     │ Checkpoint│     │  Agent   │             │
│  └──────────┘     └────┬─────┘     └──────────┘             │
│                        │                                      │
│                        ▼                                      │
│               ┌────────────────┐                             │
│               │  Human Review  │                             │
│               │  ┌──────────┐  │                             │
│               │  │ Approve  │  │                             │
│               │  │ Reject   │  │                             │
│               │  │ Feedback │  │                             │
│               │  └──────────┘  │                             │
│               └────────────────┘                             │
│                        │                                      │
│                        ▼                                      │
│               ┌────────────────┐                             │
│               │ FileCheckpoint │                             │
│               │    Storage     │                             │
│               └────────────────┘                             │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Agent Framework 檢查點 API

```python
from agent_framework import (
    WorkflowBuilder,
    FileCheckpointStorage,
    WorkflowCheckpoint,
    RequestInfoEvent,
    WorkflowContext,
    handler,
    response_handler,
    get_checkpoint_summary,
)

# 創建檢查點存儲
checkpoint_storage = FileCheckpointStorage(storage_path="/path/to/checkpoints")

# 構建帶檢查點的工作流
workflow = (
    WorkflowBuilder(max_iterations=10)
    .set_start_executor(prepare_executor)
    .add_edge(prepare_executor, agent_executor)
    .add_edge(agent_executor, review_gateway)  # 審批網關
    .with_checkpointing(checkpoint_storage=checkpoint_storage)
    .build()
)

# 人機協作請求
@dataclass
class ApprovalRequest:
    prompt: str
    draft: str
    iteration: int

class ReviewGateway(Executor):
    @handler
    async def on_agent_response(self, response, ctx: WorkflowContext):
        # 發送審批請求
        await ctx.request_info(
            request_data=ApprovalRequest(
                prompt="Please review and approve",
                draft=response.text,
                iteration=1,
            ),
            response_type=str,
        )

    @response_handler
    async def on_human_feedback(self, original_request, feedback, ctx):
        if feedback.lower() == "approve":
            await ctx.yield_output(original_request.draft)
        else:
            # 重新處理
            await ctx.send_message(...)
```

---

## User Stories

### S2-1: 檢查點機制實現 (13 點)

**描述**: 作為開發者，我需要實現檢查點機制，以支持工作流狀態持久化和恢復。

**驗收標準**:
- [ ] 檢查點可在工作流執行過程中自動保存
- [ ] 工作流可從檢查點恢復執行
- [ ] 檢查點包含完整的執行狀態
- [ ] 支持列出和管理檢查點

**技術任務**:

1. **檢查點存儲適配器 (src/domain/checkpoints/storage.py)**
```python
from typing import List, Optional
from uuid import UUID
from datetime import datetime
import json

from agent_framework import FileCheckpointStorage, WorkflowCheckpoint
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models import CheckpointModel


class DatabaseCheckpointStorage:
    """數據庫檢查點存儲 - 適配 Agent Framework"""

    def __init__(self, session: AsyncSession, execution_id: UUID):
        self._session = session
        self._execution_id = execution_id
        # 同時使用文件存儲作為主存儲
        self._file_storage = FileCheckpointStorage(
            storage_path=f"/tmp/checkpoints/{execution_id}"
        )

    async def save_checkpoint(self, checkpoint: WorkflowCheckpoint) -> str:
        """保存檢查點到數據庫和文件"""
        # 保存到文件 (Agent Framework 原生)
        checkpoint_id = await self._file_storage.save_checkpoint(checkpoint)

        # 同時保存元數據到數據庫
        db_checkpoint = CheckpointModel(
            id=UUID(checkpoint_id),
            execution_id=self._execution_id,
            step=checkpoint.iteration_count,
            state=checkpoint.to_dict(),
            status=self._determine_status(checkpoint),
            created_at=datetime.utcnow(),
        )
        self._session.add(db_checkpoint)
        await self._session.commit()

        return checkpoint_id

    async def load_checkpoint(self, checkpoint_id: str) -> Optional[WorkflowCheckpoint]:
        """從存儲加載檢查點"""
        return await self._file_storage.load_checkpoint(checkpoint_id)

    async def list_checkpoints(self) -> List[WorkflowCheckpoint]:
        """列出所有檢查點"""
        return await self._file_storage.list_checkpoints()

    def _determine_status(self, checkpoint: WorkflowCheckpoint) -> str:
        """確定檢查點狀態"""
        from agent_framework import get_checkpoint_summary
        summary = get_checkpoint_summary(checkpoint)
        return summary.status or "in_progress"


class CheckpointService:
    """檢查點服務"""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_pending_approvals(self, user_id: UUID) -> List[dict]:
        """獲取待審批的檢查點"""
        query = """
            SELECT c.id, c.execution_id, c.step, c.state, c.created_at,
                   e.workflow_id, w.name as workflow_name
            FROM checkpoints c
            JOIN executions e ON c.execution_id = e.id
            JOIN workflows w ON e.workflow_id = w.id
            WHERE c.status = 'pending'
            ORDER BY c.created_at DESC
        """
        result = await self._session.execute(query)
        return [dict(row) for row in result]

    async def approve_checkpoint(
        self,
        checkpoint_id: UUID,
        user_id: UUID,
        feedback: Optional[str] = None,
    ) -> None:
        """審批檢查點"""
        from src.infrastructure.database.models import CheckpointModel

        checkpoint = await self._session.get(CheckpointModel, checkpoint_id)
        if not checkpoint:
            raise ValueError(f"Checkpoint {checkpoint_id} not found")

        checkpoint.status = "approved"
        checkpoint.approved_by = user_id
        checkpoint.feedback = feedback
        checkpoint.updated_at = datetime.utcnow()

        await self._session.commit()

    async def reject_checkpoint(
        self,
        checkpoint_id: UUID,
        user_id: UUID,
        reason: str,
    ) -> None:
        """拒絕檢查點"""
        from src.infrastructure.database.models import CheckpointModel

        checkpoint = await self._session.get(CheckpointModel, checkpoint_id)
        if not checkpoint:
            raise ValueError(f"Checkpoint {checkpoint_id} not found")

        checkpoint.status = "rejected"
        checkpoint.approved_by = user_id
        checkpoint.feedback = reason
        checkpoint.updated_at = datetime.utcnow()

        await self._session.commit()
```

2. **檢查點 API (src/api/v1/checkpoints/routes.py)**
```python
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

from src.domain.checkpoints.storage import CheckpointService


router = APIRouter(prefix="/checkpoints", tags=["checkpoints"])


class CheckpointResponse(BaseModel):
    id: UUID
    execution_id: UUID
    step: int
    status: str
    workflow_name: str
    created_at: str


class ApprovalRequest(BaseModel):
    feedback: Optional[str] = None


class RejectionRequest(BaseModel):
    reason: str


@router.get("/pending", response_model=List[CheckpointResponse])
async def list_pending_checkpoints(
    checkpoint_service: CheckpointService = Depends(),
    # current_user = Depends(get_current_user),
):
    """獲取待審批的檢查點列表"""
    checkpoints = await checkpoint_service.get_pending_approvals(user_id=None)
    return [
        CheckpointResponse(
            id=cp["id"],
            execution_id=cp["execution_id"],
            step=cp["step"],
            status="pending",
            workflow_name=cp["workflow_name"],
            created_at=cp["created_at"].isoformat(),
        )
        for cp in checkpoints
    ]


@router.post("/{checkpoint_id}/approve")
async def approve_checkpoint(
    checkpoint_id: UUID,
    request: ApprovalRequest,
    checkpoint_service: CheckpointService = Depends(),
):
    """審批通過檢查點"""
    await checkpoint_service.approve_checkpoint(
        checkpoint_id=checkpoint_id,
        user_id=None,  # TODO: 從 current_user 獲取
        feedback=request.feedback,
    )
    return {"status": "approved"}


@router.post("/{checkpoint_id}/reject")
async def reject_checkpoint(
    checkpoint_id: UUID,
    request: RejectionRequest,
    checkpoint_service: CheckpointService = Depends(),
):
    """拒絕檢查點"""
    await checkpoint_service.reject_checkpoint(
        checkpoint_id=checkpoint_id,
        user_id=None,
        reason=request.reason,
    )
    return {"status": "rejected"}
```

---

### S2-2: 人機協作審批流程 (13 點)

**描述**: 作為業務用戶，我需要在關鍵決策點審批 Agent 的執行結果。

**驗收標準**:
- [ ] 工作流可配置審批節點
- [ ] 審批請求可通過 API 獲取
- [ ] 審批後工作流自動恢復
- [ ] 拒絕可觸發重新處理或終止

**技術任務**:

1. **審批網關執行器 (src/domain/workflows/executors/approval.py)**
```python
from typing import Any, override
from dataclasses import dataclass

from agent_framework import (
    Executor,
    WorkflowContext,
    AgentExecutorResponse,
    handler,
    response_handler,
)


@dataclass
class HumanApprovalRequest:
    """人工審批請求數據"""
    prompt: str
    content: str
    context: dict
    iteration: int = 0


class ApprovalGateway(Executor):
    """審批網關 - 暫停工作流等待人工審批"""

    def __init__(
        self,
        id: str,
        next_executor_id: str,
        approval_prompt: str = "Please review and approve the following:",
    ):
        super().__init__(id=id)
        self._next_executor_id = next_executor_id
        self._approval_prompt = approval_prompt
        self._iteration = 0

    @handler
    async def on_agent_response(
        self,
        response: AgentExecutorResponse,
        ctx: WorkflowContext,
    ) -> None:
        """接收 Agent 響應，發送審批請求"""
        self._iteration += 1

        # 發送審批請求
        await ctx.request_info(
            request_data=HumanApprovalRequest(
                prompt=self._approval_prompt,
                content=response.agent_run_response.text,
                context={
                    "agent_id": response.agent_id,
                    "messages": [m.text for m in response.messages[-3:]],
                },
                iteration=self._iteration,
            ),
            response_type=str,
        )

    @response_handler
    async def on_human_feedback(
        self,
        original_request: HumanApprovalRequest,
        feedback: str,
        ctx: WorkflowContext,
    ) -> None:
        """處理人工反饋"""
        feedback_lower = feedback.strip().lower()

        if feedback_lower in ["approve", "approved", "yes", "ok"]:
            # 審批通過，輸出結果
            await ctx.yield_output({
                "status": "approved",
                "content": original_request.content,
                "approved_at": "now",
            })
        elif feedback_lower in ["reject", "rejected", "no"]:
            # 審批拒絕，終止工作流
            await ctx.yield_output({
                "status": "rejected",
                "content": original_request.content,
                "reason": "Human rejected the result",
            })
        else:
            # 其他反饋視為修改建議，重新處理
            await ctx.send_message(
                {
                    "type": "revision_request",
                    "original_content": original_request.content,
                    "feedback": feedback,
                },
                target_id=self._next_executor_id,
            )

    @override
    async def on_checkpoint_save(self) -> dict[str, Any]:
        """保存檢查點狀態"""
        return {"iteration": self._iteration}

    @override
    async def on_checkpoint_restore(self, state: dict[str, Any]) -> None:
        """恢復檢查點狀態"""
        self._iteration = state.get("iteration", 0)
```

2. **工作流恢復服務 (src/domain/workflows/resume_service.py)**
```python
from typing import Optional
from uuid import UUID

from agent_framework import Workflow, WorkflowCheckpoint

from src.domain.checkpoints.storage import CheckpointService, DatabaseCheckpointStorage
from src.domain.workflows.execution_service import WorkflowExecutionService


class WorkflowResumeService:
    """工作流恢復服務"""

    def __init__(
        self,
        execution_service: WorkflowExecutionService,
        checkpoint_service: CheckpointService,
    ):
        self._execution_service = execution_service
        self._checkpoint_service = checkpoint_service

    async def resume_from_checkpoint(
        self,
        execution_id: UUID,
        checkpoint_id: str,
        response: str,
    ) -> None:
        """從檢查點恢復工作流執行"""
        # 獲取工作流實例
        workflow = await self._execution_service.get_workflow_for_execution(execution_id)

        # 發送響應並繼續執行
        async for event in workflow.send_responses_streaming({checkpoint_id: response}):
            # 處理事件流
            if hasattr(event, 'data'):
                # 更新執行結果
                await self._execution_service.update_execution_result(
                    execution_id, event.data
                )

    async def resume_with_approval(
        self,
        execution_id: UUID,
        checkpoint_id: UUID,
        approved: bool,
        feedback: Optional[str] = None,
    ) -> None:
        """通過審批恢復工作流"""
        if approved:
            response = "approve"
        else:
            response = feedback or "reject"

        await self.resume_from_checkpoint(
            execution_id=execution_id,
            checkpoint_id=str(checkpoint_id),
            response=response,
        )
```

---

### S2-3: 跨系統連接器 (10 點)

**描述**: 作為開發者，我需要集成企業系統連接器，讓 Agent 可以訪問外部數據。

**驗收標準**:
- [ ] ServiceNow 連接器可查詢工單
- [ ] Dynamics 365 連接器可查詢客戶數據
- [ ] SharePoint 連接器可讀取文檔
- [ ] 連接器錯誤正確處理

**技術任務**:

1. **連接器基類 (src/domain/connectors/base.py)**
```python
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass


@dataclass
class ConnectorConfig:
    """連接器配置"""
    endpoint: str
    auth_type: str  # "oauth2", "api_key", "basic"
    credentials: Dict[str, str]
    timeout: int = 30


@dataclass
class ConnectorResponse:
    """連接器響應"""
    success: bool
    data: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = None


class BaseConnector(ABC):
    """連接器基類"""

    def __init__(self, config: ConnectorConfig):
        self._config = config

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    async def connect(self) -> bool:
        """建立連接"""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """斷開連接"""
        pass

    @abstractmethod
    async def execute(self, operation: str, params: Dict[str, Any]) -> ConnectorResponse:
        """執行操作"""
        pass
```

2. **ServiceNow 連接器 (src/domain/connectors/servicenow.py)**
```python
from typing import Dict, Any, List
import httpx

from .base import BaseConnector, ConnectorConfig, ConnectorResponse


class ServiceNowConnector(BaseConnector):
    """ServiceNow 連接器"""

    @property
    def name(self) -> str:
        return "servicenow"

    async def connect(self) -> bool:
        """驗證連接"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self._config.endpoint}/api/now/table/sys_user?sysparm_limit=1",
                    auth=(
                        self._config.credentials["username"],
                        self._config.credentials["password"],
                    ),
                    timeout=self._config.timeout,
                )
                return response.status_code == 200
        except Exception:
            return False

    async def disconnect(self) -> None:
        pass  # HTTP 無狀態

    async def execute(self, operation: str, params: Dict[str, Any]) -> ConnectorResponse:
        """執行 ServiceNow 操作"""
        operations = {
            "get_incident": self._get_incident,
            "list_incidents": self._list_incidents,
            "create_incident": self._create_incident,
            "update_incident": self._update_incident,
        }

        handler = operations.get(operation)
        if not handler:
            return ConnectorResponse(
                success=False,
                data=None,
                error=f"Unknown operation: {operation}",
            )

        try:
            data = await handler(params)
            return ConnectorResponse(success=True, data=data)
        except Exception as e:
            return ConnectorResponse(success=False, data=None, error=str(e))

    async def _get_incident(self, params: Dict[str, Any]) -> Dict:
        """獲取單個工單"""
        incident_id = params["incident_id"]
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._config.endpoint}/api/now/table/incident/{incident_id}",
                auth=(
                    self._config.credentials["username"],
                    self._config.credentials["password"],
                ),
            )
            response.raise_for_status()
            return response.json()["result"]

    async def _list_incidents(self, params: Dict[str, Any]) -> List[Dict]:
        """列出工單"""
        query = params.get("query", "")
        limit = params.get("limit", 10)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._config.endpoint}/api/now/table/incident",
                params={
                    "sysparm_query": query,
                    "sysparm_limit": limit,
                },
                auth=(
                    self._config.credentials["username"],
                    self._config.credentials["password"],
                ),
            )
            response.raise_for_status()
            return response.json()["result"]

    async def _create_incident(self, params: Dict[str, Any]) -> Dict:
        """創建工單"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._config.endpoint}/api/now/table/incident",
                json=params,
                auth=(
                    self._config.credentials["username"],
                    self._config.credentials["password"],
                ),
            )
            response.raise_for_status()
            return response.json()["result"]

    async def _update_incident(self, params: Dict[str, Any]) -> Dict:
        """更新工單"""
        incident_id = params.pop("incident_id")
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{self._config.endpoint}/api/now/table/incident/{incident_id}",
                json=params,
                auth=(
                    self._config.credentials["username"],
                    self._config.credentials["password"],
                ),
            )
            response.raise_for_status()
            return response.json()["result"]
```

3. **連接器作為 Agent 工具 (src/domain/agents/tools/connector_tools.py)**
```python
from typing import Annotated

from src.domain.connectors.base import ConnectorConfig
from src.domain.connectors.servicenow import ServiceNowConnector


def create_servicenow_tools(config: ConnectorConfig):
    """創建 ServiceNow 工具集"""
    connector = ServiceNowConnector(config)

    async def get_incident(
        incident_id: Annotated[str, "The ServiceNow incident ID (e.g., INC0010001)"],
    ) -> str:
        """Get details of a ServiceNow incident by ID."""
        result = await connector.execute("get_incident", {"incident_id": incident_id})
        if result.success:
            incident = result.data
            return f"Incident {incident_id}: {incident.get('short_description', 'N/A')} - Status: {incident.get('state', 'N/A')}"
        return f"Error: {result.error}"

    async def search_incidents(
        query: Annotated[str, "Search query for incidents (e.g., 'priority=1^state=2')"],
        limit: Annotated[int, "Maximum number of results"] = 5,
    ) -> str:
        """Search ServiceNow incidents with a query."""
        result = await connector.execute("list_incidents", {"query": query, "limit": limit})
        if result.success:
            incidents = result.data
            return "\n".join([
                f"- {inc['number']}: {inc.get('short_description', 'N/A')}"
                for inc in incidents
            ])
        return f"Error: {result.error}"

    return [get_incident, search_incidents]
```

---

### S2-4: Redis 緩存實現 (9 點)

**描述**: 作為開發者，我需要實現 Redis 緩存以提升 LLM 響應效率。

**驗收標準**:
- [ ] 相同輸入可命中緩存
- [ ] 緩存命中率達到 60%+
- [ ] 緩存有合理的 TTL
- [ ] 緩存統計可查詢

**技術任務**:

1. **LLM 緩存服務 (src/infrastructure/cache/llm_cache.py)**
```python
import hashlib
import json
from typing import Optional
from datetime import timedelta

import redis.asyncio as redis


class LLMCacheService:
    """LLM 響應緩存服務"""

    def __init__(self, redis_url: str, default_ttl: int = 3600):
        self._redis = redis.from_url(redis_url)
        self._default_ttl = default_ttl
        self._stats_key = "llm_cache:stats"

    def _generate_key(self, prompt: str, model: str, **kwargs) -> str:
        """生成緩存鍵"""
        # 包含影響輸出的參數
        key_data = {
            "prompt": prompt,
            "model": model,
            "temperature": kwargs.get("temperature", 0),
            "max_tokens": kwargs.get("max_tokens"),
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return f"llm_cache:{hashlib.sha256(key_str.encode()).hexdigest()}"

    async def get(
        self,
        prompt: str,
        model: str,
        **kwargs,
    ) -> Optional[str]:
        """獲取緩存的響應"""
        key = self._generate_key(prompt, model, **kwargs)
        cached = await self._redis.get(key)

        if cached:
            # 更新統計
            await self._redis.hincrby(self._stats_key, "hits", 1)
            return cached.decode()
        else:
            await self._redis.hincrby(self._stats_key, "misses", 1)
            return None

    async def set(
        self,
        prompt: str,
        model: str,
        response: str,
        ttl: Optional[int] = None,
        **kwargs,
    ) -> None:
        """緩存響應"""
        key = self._generate_key(prompt, model, **kwargs)
        await self._redis.setex(
            key,
            ttl or self._default_ttl,
            response,
        )

    async def get_stats(self) -> dict:
        """獲取緩存統計"""
        stats = await self._redis.hgetall(self._stats_key)
        hits = int(stats.get(b"hits", 0))
        misses = int(stats.get(b"misses", 0))
        total = hits + misses

        return {
            "hits": hits,
            "misses": misses,
            "total": total,
            "hit_rate": hits / total if total > 0 else 0,
        }

    async def clear(self) -> int:
        """清除所有緩存"""
        keys = await self._redis.keys("llm_cache:*")
        if keys:
            return await self._redis.delete(*keys)
        return 0


class CachedAgentService:
    """帶緩存的 Agent 服務"""

    def __init__(self, agent_service, cache_service: LLMCacheService):
        self._agent_service = agent_service
        self._cache = cache_service

    async def run_agent(self, agent_executor, message: str) -> tuple[str, dict]:
        """運行 Agent，優先使用緩存"""
        # 嘗試從緩存獲取
        model = self._agent_service._settings.azure_openai_deployment_name
        cached_response = await self._cache.get(message, model)

        if cached_response:
            return cached_response, {"llm_calls": 0, "llm_tokens": 0, "llm_cost": 0, "cached": True}

        # 調用實際 Agent
        response, stats = await self._agent_service.run_agent(agent_executor, message)

        # 緩存響應 (只緩存成功響應)
        await self._cache.set(message, model, response)

        stats["cached"] = False
        return response, stats
```

2. **緩存 API (src/api/v1/cache/routes.py)**
```python
from fastapi import APIRouter, Depends

from src.infrastructure.cache.llm_cache import LLMCacheService


router = APIRouter(prefix="/cache", tags=["cache"])


@router.get("/stats")
async def get_cache_stats(
    cache_service: LLMCacheService = Depends(),
):
    """獲取緩存統計"""
    stats = await cache_service.get_stats()
    return {
        "hits": stats["hits"],
        "misses": stats["misses"],
        "total_requests": stats["total"],
        "hit_rate": f"{stats['hit_rate']:.2%}",
    }


@router.post("/clear")
async def clear_cache(
    cache_service: LLMCacheService = Depends(),
):
    """清除緩存"""
    deleted = await cache_service.clear()
    return {"deleted_keys": deleted}
```

---

## 時間規劃

### Week 5 (Day 1-5)

| 日期 | 任務 | 負責人 | 產出 |
|------|------|--------|------|
| Day 1-2 | S2-1: 檢查點存儲適配器 | Backend | storage.py |
| Day 2-3 | S2-1: 檢查點 API | Backend | checkpoints/routes.py |
| Day 3-4 | S2-2: 審批網關執行器 | Backend | approval.py |
| Day 4-5 | S2-2: 工作流恢復服務 | Backend | resume_service.py |

### Week 6 (Day 6-10)

| 日期 | 任務 | 負責人 | 產出 |
|------|------|--------|------|
| Day 6-7 | S2-3: 連接器基類 + ServiceNow | Backend | connectors/*.py |
| Day 7-8 | S2-3: Dynamics 365 + SharePoint | Backend | connectors/*.py |
| Day 8-9 | S2-4: Redis LLM 緩存 | Backend | llm_cache.py |
| Day 9-10 | 集成測試 + 文檔 | 全員 | 測試用例 |

---

## 測試要求

### 單元測試

```python
# tests/unit/test_checkpoint.py
import pytest

from src.domain.checkpoints.storage import CheckpointService


class TestCheckpointService:

    @pytest.mark.asyncio
    async def test_get_pending_approvals(self, db_session):
        service = CheckpointService(db_session)
        approvals = await service.get_pending_approvals(user_id=None)
        assert isinstance(approvals, list)

    @pytest.mark.asyncio
    async def test_approve_checkpoint(self, db_session, checkpoint_id):
        service = CheckpointService(db_session)
        await service.approve_checkpoint(checkpoint_id, user_id=None)
        # 驗證狀態已更新


# tests/unit/test_llm_cache.py
import pytest

from src.infrastructure.cache.llm_cache import LLMCacheService


class TestLLMCache:

    @pytest.fixture
    async def cache_service(self, redis_url):
        return LLMCacheService(redis_url)

    @pytest.mark.asyncio
    async def test_cache_hit(self, cache_service):
        # 設置緩存
        await cache_service.set("test prompt", "gpt-4o", "test response")

        # 驗證命中
        cached = await cache_service.get("test prompt", "gpt-4o")
        assert cached == "test response"

    @pytest.mark.asyncio
    async def test_cache_miss(self, cache_service):
        cached = await cache_service.get("unknown prompt", "gpt-4o")
        assert cached is None
```

---

## 完成定義 (Definition of Done)

1. **功能完成**
   - [ ] 檢查點可正確保存和恢復
   - [ ] 人工審批流程完整
   - [ ] 連接器可訪問外部系統
   - [ ] 緩存命中率達標

2. **測試完成**
   - [ ] 單元測試覆蓋率 >= 80%
   - [ ] 人機協作端到端測試通過
   - [ ] 連接器集成測試通過

3. **文檔完成**
   - [ ] 檢查點 API 文檔
   - [ ] 連接器配置指南
   - [ ] 緩存調優指南

---

## 相關文檔

- [Sprint 2 Checklist](./sprint-2-checklist.md)
- [Sprint 1 Plan](./sprint-1-plan.md) - 前置 Sprint
- [Agent Framework Checkpoint 參考](../../../reference/agent-framework/python/samples/getting_started/workflows/checkpoint/)
