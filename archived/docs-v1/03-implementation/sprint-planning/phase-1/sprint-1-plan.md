# Sprint 1: 核心引擎 - Agent Framework 集成

**Sprint 目標**: 完成 Microsoft Agent Framework 核心集成，實現基礎 Agent 編排能力
**週期**: Week 3-4 (2 週)
**Story Points**: 42 點
**MVP 功能**: F1 - 順序式 Agent 編排

---

## Sprint 概覽

### 目標
1. 集成 Microsoft Agent Framework 核心模組
2. 實現 Agent 創建和執行 API
3. 建立 Workflow 基礎結構
4. 實現工具 (Tools) 集成機制
5. 建立執行狀態管理

### 成功標準
- [ ] 可通過 API 創建 Agent
- [ ] Agent 可執行簡單任務並返回結果
- [ ] Workflow 可串聯多個 Agent 順序執行
- [ ] 工具調用正常運作
- [ ] 執行記錄完整保存

---

## Agent Framework 核心概念

### 架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                    IPA Platform API                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────┐    ┌─────────────────┐                 │
│  │  Agent Service  │    │ Workflow Service │                 │
│  └────────┬────────┘    └────────┬────────┘                 │
│           │                      │                           │
│  ┌────────▼──────────────────────▼────────┐                 │
│  │           Agent Framework Runtime       │                 │
│  │  ┌──────────────────────────────────┐  │                 │
│  │  │     WorkflowBuilder              │  │                 │
│  │  │     ├─ set_start_executor()      │  │                 │
│  │  │     ├─ add_edge()                │  │                 │
│  │  │     └─ build()                   │  │                 │
│  │  └──────────────────────────────────┘  │                 │
│  │  ┌──────────────────────────────────┐  │                 │
│  │  │     AgentExecutor                │  │                 │
│  │  │     ├─ Agent                     │  │                 │
│  │  │     └─ Tools[]                   │  │                 │
│  │  └──────────────────────────────────┘  │                 │
│  └─────────────────────────────────────────┘                 │
│                      │                                       │
│           ┌──────────┴──────────┐                           │
│           │                     │                           │
│  ┌────────▼────────┐  ┌────────▼────────┐                   │
│  │   Azure OpenAI  │  │   PostgreSQL    │                   │
│  │   (LLM 推理)    │  │   (狀態存儲)    │                   │
│  └─────────────────┘  └─────────────────┘                   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 核心類別

```python
# Agent Framework 核心導入
from agent_framework import (
    AgentExecutor,           # Agent 執行器
    AgentExecutorRequest,    # Agent 請求
    AgentExecutorResponse,   # Agent 響應
    ChatMessage,             # 消息類型
    Role,                    # 角色枚舉
    Executor,                # 自定義執行器基類
    Workflow,                # 工作流
    WorkflowBuilder,         # 工作流構建器
    WorkflowContext,         # 工作流上下文
    handler,                 # 處理器裝飾器
)
from agent_framework.azure import AzureOpenAIChatClient
```

---

## User Stories

### S1-1: Agent Framework 核心集成 (13 點)

**描述**: 作為開發者，我需要集成 Agent Framework 核心模組，以便使用其 Agent 能力。

**驗收標準**:
- [ ] AzureOpenAIChatClient 初始化成功
- [ ] 可創建基礎 Agent
- [ ] Agent 可執行簡單對話
- [ ] LLM 調用正確計費 (token 統計)

**技術任務**:

1. **Agent Framework 服務層 (src/domain/agents/service.py)**
```python
from typing import Optional
from dataclasses import dataclass

from agent_framework import AgentExecutor, ChatMessage, Role
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import DefaultAzureCredential

from src.core.config import get_settings


@dataclass
class AgentConfig:
    """Agent 配置"""
    name: str
    instructions: str
    tools: list = None
    max_iterations: int = 10


class AgentService:
    """Agent 服務 - 封裝 Agent Framework 操作"""

    def __init__(self):
        self._settings = get_settings()
        self._client: Optional[AzureOpenAIChatClient] = None

    async def initialize(self) -> None:
        """初始化 Azure OpenAI 客戶端"""
        self._client = AzureOpenAIChatClient(
            credential=DefaultAzureCredential(),
            endpoint=self._settings.azure_openai_endpoint,
            deployment_name=self._settings.azure_openai_deployment_name,
        )

    def create_agent(self, config: AgentConfig) -> AgentExecutor:
        """創建 Agent 執行器"""
        if not self._client:
            raise RuntimeError("AgentService not initialized")

        agent = self._client.create_agent(
            name=config.name,
            instructions=config.instructions,
            tools=config.tools or [],
        )

        return AgentExecutor(agent, id=config.name)

    async def run_agent(
        self,
        agent_executor: AgentExecutor,
        message: str,
    ) -> tuple[str, dict]:
        """運行 Agent 並返回結果和統計"""
        response = await agent_executor.agent.run(message)

        # 收集統計信息
        stats = {
            "llm_calls": 1,  # 基礎計數
            "llm_tokens": response.usage.total_tokens if hasattr(response, 'usage') else 0,
            "llm_cost": self._calculate_cost(response),
        }

        return response.text, stats

    def _calculate_cost(self, response) -> float:
        """計算 LLM 調用成本"""
        # GPT-4o 定價: $5/1M input, $15/1M output
        if hasattr(response, 'usage'):
            input_cost = (response.usage.prompt_tokens / 1_000_000) * 5
            output_cost = (response.usage.completion_tokens / 1_000_000) * 15
            return input_cost + output_cost
        return 0.0
```

2. **Agent API 路由 (src/api/v1/agents/routes.py)**
```python
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

from src.domain.agents.service import AgentService, AgentConfig
from src.infrastructure.database.repositories import AgentRepository


router = APIRouter(prefix="/agents", tags=["agents"])


class AgentCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    instructions: str
    category: Optional[str] = None


class AgentRunRequest(BaseModel):
    message: str


class AgentResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    status: str


class AgentRunResponse(BaseModel):
    result: str
    stats: dict


@router.post("/", response_model=AgentResponse)
async def create_agent(
    request: AgentCreateRequest,
    agent_repo: AgentRepository = Depends(),
):
    """創建新 Agent"""
    agent = await agent_repo.create(
        name=request.name,
        description=request.description,
        instructions=request.instructions,
        category=request.category,
    )
    return AgentResponse(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        status=agent.status,
    )


@router.post("/{agent_id}/run", response_model=AgentRunResponse)
async def run_agent(
    agent_id: UUID,
    request: AgentRunRequest,
    agent_service: AgentService = Depends(),
    agent_repo: AgentRepository = Depends(),
):
    """運行指定 Agent"""
    # 獲取 Agent 配置
    agent_db = await agent_repo.get(agent_id)
    if not agent_db:
        raise HTTPException(status_code=404, detail="Agent not found")

    # 創建並運行 Agent
    config = AgentConfig(
        name=agent_db.name,
        instructions=agent_db.instructions,
    )
    executor = agent_service.create_agent(config)
    result, stats = await agent_service.run_agent(executor, request.message)

    return AgentRunResponse(result=result, stats=stats)
```

---

### S1-2: Workflow 基礎結構 (13 點)

**描述**: 作為開發者，我需要建立 Workflow 基礎結構，以支持順序式 Agent 編排。

**驗收標準**:
- [ ] Workflow CRUD API 完成
- [ ] WorkflowBuilder 集成
- [ ] 支持順序執行多個 Agent
- [ ] 執行狀態可追蹤

**技術任務**:

1. **Workflow 領域模型 (src/domain/workflows/models.py)**
```python
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from uuid import UUID
from datetime import datetime


class NodeType(str, Enum):
    AGENT = "agent"
    GATEWAY = "gateway"
    START = "start"
    END = "end"


class TriggerType(str, Enum):
    MANUAL = "manual"
    SCHEDULE = "schedule"
    WEBHOOK = "webhook"
    EVENT = "event"


@dataclass
class WorkflowNode:
    """工作流節點"""
    id: str
    type: NodeType
    config: Dict[str, Any] = field(default_factory=dict)
    # Agent 節點配置
    agent_id: Optional[UUID] = None
    # Gateway 節點配置
    condition: Optional[str] = None


@dataclass
class WorkflowEdge:
    """工作流邊"""
    source: str
    target: str
    condition: Optional[str] = None


@dataclass
class WorkflowDefinition:
    """工作流定義"""
    nodes: List[WorkflowNode]
    edges: List[WorkflowEdge]

    def validate(self) -> List[str]:
        """驗證工作流定義"""
        errors = []
        node_ids = {n.id for n in self.nodes}

        # 檢查邊引用的節點是否存在
        for edge in self.edges:
            if edge.source not in node_ids:
                errors.append(f"Edge source '{edge.source}' not found in nodes")
            if edge.target not in node_ids:
                errors.append(f"Edge target '{edge.target}' not found in nodes")

        # 檢查是否有起點
        start_nodes = [n for n in self.nodes if n.type == NodeType.START]
        if len(start_nodes) != 1:
            errors.append("Workflow must have exactly one START node")

        return errors
```

2. **Workflow 執行服務 (src/domain/workflows/execution_service.py)**
```python
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime

from agent_framework import (
    WorkflowBuilder,
    Workflow,
    WorkflowContext,
    AgentExecutor,
    AgentExecutorRequest,
    ChatMessage,
    Role,
    Executor,
    handler,
)

from src.domain.workflows.models import WorkflowDefinition, NodeType
from src.domain.agents.service import AgentService
from src.infrastructure.database.repositories import (
    WorkflowRepository,
    ExecutionRepository,
    AgentRepository,
)


class WorkflowExecutionService:
    """工作流執行服務"""

    def __init__(
        self,
        agent_service: AgentService,
        workflow_repo: WorkflowRepository,
        execution_repo: ExecutionRepository,
        agent_repo: AgentRepository,
    ):
        self._agent_service = agent_service
        self._workflow_repo = workflow_repo
        self._execution_repo = execution_repo
        self._agent_repo = agent_repo

    async def execute_workflow(
        self,
        workflow_id: UUID,
        input_data: dict,
    ) -> UUID:
        """執行工作流"""
        # 獲取工作流定義
        workflow_db = await self._workflow_repo.get(workflow_id)
        if not workflow_db:
            raise ValueError(f"Workflow {workflow_id} not found")

        definition = WorkflowDefinition(**workflow_db.graph_definition)

        # 創建執行記錄
        execution_id = uuid4()
        await self._execution_repo.create(
            id=execution_id,
            workflow_id=workflow_id,
            status="running",
            started_at=datetime.utcnow(),
        )

        try:
            # 構建 Agent Framework Workflow
            workflow = await self._build_workflow(definition)

            # 執行工作流
            result = None
            async for event in workflow.run_stream(message=input_data.get("message", "")):
                # 處理事件
                if hasattr(event, 'data'):
                    result = event.data

            # 更新執行記錄
            await self._execution_repo.update(
                id=execution_id,
                status="completed",
                completed_at=datetime.utcnow(),
                result={"output": result},
            )

        except Exception as e:
            await self._execution_repo.update(
                id=execution_id,
                status="failed",
                completed_at=datetime.utcnow(),
                error=str(e),
            )
            raise

        return execution_id

    async def _build_workflow(self, definition: WorkflowDefinition) -> Workflow:
        """根據定義構建 Agent Framework Workflow"""
        executors = {}

        # 創建執行器
        for node in definition.nodes:
            if node.type == NodeType.AGENT and node.agent_id:
                agent_db = await self._agent_repo.get(node.agent_id)
                if agent_db:
                    executor = self._agent_service.create_agent(
                        AgentConfig(
                            name=agent_db.name,
                            instructions=agent_db.instructions,
                        )
                    )
                    executors[node.id] = executor

        # 構建工作流
        builder = WorkflowBuilder(max_iterations=10)

        # 找到起始節點
        start_node = next(n for n in definition.nodes if n.type == NodeType.START)
        first_edge = next(e for e in definition.edges if e.source == start_node.id)
        first_executor = executors.get(first_edge.target)

        if first_executor:
            builder.set_start_executor(first_executor)

            # 添加邊
            for edge in definition.edges:
                if edge.source in executors and edge.target in executors:
                    builder.add_edge(executors[edge.source], executors[edge.target])

        return builder.build()
```

3. **Workflow API 路由 (src/api/v1/workflows/routes.py)**
```python
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from uuid import UUID

from src.domain.workflows.models import WorkflowDefinition, WorkflowNode, WorkflowEdge
from src.domain.workflows.execution_service import WorkflowExecutionService
from src.infrastructure.database.repositories import WorkflowRepository


router = APIRouter(prefix="/workflows", tags=["workflows"])


class WorkflowCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    trigger_type: str = "manual"
    trigger_config: Dict[str, Any] = {}
    graph_definition: Dict[str, Any]


class WorkflowExecuteRequest(BaseModel):
    message: str
    parameters: Dict[str, Any] = {}


class WorkflowResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    status: str
    version: int


class ExecutionResponse(BaseModel):
    execution_id: UUID
    status: str


@router.post("/", response_model=WorkflowResponse)
async def create_workflow(
    request: WorkflowCreateRequest,
    workflow_repo: WorkflowRepository = Depends(),
):
    """創建新工作流"""
    # 驗證工作流定義
    definition = WorkflowDefinition(
        nodes=[WorkflowNode(**n) for n in request.graph_definition.get("nodes", [])],
        edges=[WorkflowEdge(**e) for e in request.graph_definition.get("edges", [])],
    )
    errors = definition.validate()
    if errors:
        raise HTTPException(status_code=400, detail={"validation_errors": errors})

    workflow = await workflow_repo.create(
        name=request.name,
        description=request.description,
        trigger_type=request.trigger_type,
        trigger_config=request.trigger_config,
        graph_definition=request.graph_definition,
    )

    return WorkflowResponse(
        id=workflow.id,
        name=workflow.name,
        description=workflow.description,
        status=workflow.status,
        version=workflow.version,
    )


@router.post("/{workflow_id}/execute", response_model=ExecutionResponse)
async def execute_workflow(
    workflow_id: UUID,
    request: WorkflowExecuteRequest,
    background_tasks: BackgroundTasks,
    execution_service: WorkflowExecutionService = Depends(),
):
    """執行工作流"""
    execution_id = await execution_service.execute_workflow(
        workflow_id=workflow_id,
        input_data={"message": request.message, **request.parameters},
    )

    return ExecutionResponse(
        execution_id=execution_id,
        status="running",
    )
```

---

### S1-3: 工具 (Tools) 集成機制 (8 點)

**描述**: 作為開發者，我需要實現工具集成機制，讓 Agent 可以調用外部功能。

**驗收標準**:
- [ ] 支持自定義工具註冊
- [ ] 工具可被 Agent 調用
- [ ] 工具執行結果正確返回
- [ ] 內建工具: HTTP 調用、日期時間

**技術任務**:

1. **工具基礎類 (src/domain/agents/tools/base.py)**
```python
from abc import ABC, abstractmethod
from typing import Annotated, Any
from dataclasses import dataclass


@dataclass
class ToolResult:
    """工具執行結果"""
    success: bool
    data: Any
    error: str = None


class BaseTool(ABC):
    """工具基類"""

    @property
    @abstractmethod
    def name(self) -> str:
        """工具名稱"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述"""
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """執行工具"""
        pass

    def as_function(self):
        """轉換為 Agent Framework 可用的函數"""
        async def wrapper(**kwargs):
            result = await self.execute(**kwargs)
            if result.success:
                return str(result.data)
            else:
                return f"Error: {result.error}"

        wrapper.__name__ = self.name
        wrapper.__doc__ = self.description
        return wrapper
```

2. **內建工具實現 (src/domain/agents/tools/builtin.py)**
```python
from typing import Annotated
from datetime import datetime
import httpx

from .base import BaseTool, ToolResult


class HttpTool(BaseTool):
    """HTTP 請求工具"""

    @property
    def name(self) -> str:
        return "http_request"

    @property
    def description(self) -> str:
        return "Make HTTP requests to external APIs"

    async def execute(
        self,
        url: Annotated[str, "The URL to request"],
        method: Annotated[str, "HTTP method (GET, POST, etc.)"] = "GET",
        headers: Annotated[dict, "Request headers"] = None,
        body: Annotated[dict, "Request body for POST/PUT"] = None,
    ) -> ToolResult:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=body,
                )
                return ToolResult(
                    success=True,
                    data={
                        "status_code": response.status_code,
                        "body": response.text[:1000],  # 限制大小
                    },
                )
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))


class DateTimeTool(BaseTool):
    """日期時間工具"""

    @property
    def name(self) -> str:
        return "get_current_datetime"

    @property
    def description(self) -> str:
        return "Get the current date and time"

    async def execute(
        self,
        format: Annotated[str, "Date format string"] = "%Y-%m-%d %H:%M:%S",
        timezone: Annotated[str, "Timezone name"] = "UTC",
    ) -> ToolResult:
        try:
            from zoneinfo import ZoneInfo
            tz = ZoneInfo(timezone)
            now = datetime.now(tz)
            return ToolResult(
                success=True,
                data=now.strftime(format),
            )
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))


# 使用 Agent Framework 原生方式定義工具
def get_weather(
    location: Annotated[str, "The location to get weather for"],
) -> str:
    """Get the current weather for a location."""
    # 模擬天氣數據 (實際應調用天氣 API)
    return f"The weather in {location} is sunny with a high of 25°C."


def search_knowledge_base(
    query: Annotated[str, "The search query"],
    max_results: Annotated[int, "Maximum number of results"] = 5,
) -> str:
    """Search the internal knowledge base for relevant information."""
    # 模擬搜索結果 (實際應連接向量數據庫)
    return f"Found {max_results} results for '{query}'"
```

3. **工具註冊管理 (src/domain/agents/tools/registry.py)**
```python
from typing import Dict, List, Callable, Any


class ToolRegistry:
    """工具註冊表"""

    _tools: Dict[str, Callable] = {}
    _builtin_loaded: bool = False

    @classmethod
    def register(cls, name: str, tool: Callable) -> None:
        """註冊工具"""
        cls._tools[name] = tool

    @classmethod
    def get(cls, name: str) -> Callable:
        """獲取工具"""
        return cls._tools.get(name)

    @classmethod
    def get_all(cls) -> List[Callable]:
        """獲取所有工具"""
        return list(cls._tools.values())

    @classmethod
    def load_builtins(cls) -> None:
        """加載內建工具"""
        if cls._builtin_loaded:
            return

        from .builtin import get_weather, search_knowledge_base, HttpTool, DateTimeTool

        # 註冊函數式工具
        cls.register("get_weather", get_weather)
        cls.register("search_knowledge_base", search_knowledge_base)

        # 註冊類式工具
        http_tool = HttpTool()
        datetime_tool = DateTimeTool()
        cls.register(http_tool.name, http_tool.as_function())
        cls.register(datetime_tool.name, datetime_tool.as_function())

        cls._builtin_loaded = True
```

---

### S1-4: 執行狀態管理 (8 點)

**描述**: 作為開發者，我需要完整的執行狀態管理，以追蹤和恢復執行。

**驗收標準**:
- [ ] 執行狀態持久化到數據庫
- [ ] 支持查詢執行歷史
- [ ] 支持獲取執行詳情
- [ ] LLM 調用統計完整

**技術任務**:

1. **執行狀態機 (src/domain/executions/state_machine.py)**
```python
from enum import Enum
from typing import Set, Dict


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"  # 等待人工介入
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionStateMachine:
    """執行狀態機"""

    # 狀態轉換規則
    TRANSITIONS: Dict[ExecutionStatus, Set[ExecutionStatus]] = {
        ExecutionStatus.PENDING: {ExecutionStatus.RUNNING, ExecutionStatus.CANCELLED},
        ExecutionStatus.RUNNING: {
            ExecutionStatus.PAUSED,
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
            ExecutionStatus.CANCELLED,
        },
        ExecutionStatus.PAUSED: {
            ExecutionStatus.RUNNING,
            ExecutionStatus.CANCELLED,
        },
        ExecutionStatus.COMPLETED: set(),  # 終態
        ExecutionStatus.FAILED: set(),  # 終態
        ExecutionStatus.CANCELLED: set(),  # 終態
    }

    @classmethod
    def can_transition(
        cls,
        from_status: ExecutionStatus,
        to_status: ExecutionStatus,
    ) -> bool:
        """檢查是否可以轉換狀態"""
        allowed = cls.TRANSITIONS.get(from_status, set())
        return to_status in allowed

    @classmethod
    def transition(
        cls,
        from_status: ExecutionStatus,
        to_status: ExecutionStatus,
    ) -> ExecutionStatus:
        """執行狀態轉換"""
        if not cls.can_transition(from_status, to_status):
            raise ValueError(
                f"Invalid transition from {from_status} to {to_status}"
            )
        return to_status

    @classmethod
    def is_terminal(cls, status: ExecutionStatus) -> bool:
        """檢查是否為終態"""
        return len(cls.TRANSITIONS.get(status, set())) == 0
```

2. **執行 API 路由 (src/api/v1/executions/routes.py)**
```python
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from src.domain.executions.state_machine import ExecutionStatus
from src.infrastructure.database.repositories import ExecutionRepository


router = APIRouter(prefix="/executions", tags=["executions"])


class ExecutionDetailResponse(BaseModel):
    id: UUID
    workflow_id: UUID
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    llm_calls: int
    llm_tokens: int
    llm_cost: float


class ExecutionListResponse(BaseModel):
    items: List[ExecutionDetailResponse]
    total: int
    page: int
    page_size: int


@router.get("/{execution_id}", response_model=ExecutionDetailResponse)
async def get_execution(
    execution_id: UUID,
    execution_repo: ExecutionRepository = Depends(),
):
    """獲取執行詳情"""
    execution = await execution_repo.get(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    return ExecutionDetailResponse(
        id=execution.id,
        workflow_id=execution.workflow_id,
        status=execution.status,
        started_at=execution.started_at,
        completed_at=execution.completed_at,
        result=execution.result,
        error=execution.error,
        llm_calls=execution.llm_calls,
        llm_tokens=execution.llm_tokens,
        llm_cost=float(execution.llm_cost),
    )


@router.get("/", response_model=ExecutionListResponse)
async def list_executions(
    workflow_id: Optional[UUID] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    execution_repo: ExecutionRepository = Depends(),
):
    """列出執行記錄"""
    executions, total = await execution_repo.list(
        workflow_id=workflow_id,
        status=status,
        page=page,
        page_size=page_size,
    )

    return ExecutionListResponse(
        items=[
            ExecutionDetailResponse(
                id=e.id,
                workflow_id=e.workflow_id,
                status=e.status,
                started_at=e.started_at,
                completed_at=e.completed_at,
                result=e.result,
                error=e.error,
                llm_calls=e.llm_calls,
                llm_tokens=e.llm_tokens,
                llm_cost=float(e.llm_cost),
            )
            for e in executions
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/{execution_id}/cancel")
async def cancel_execution(
    execution_id: UUID,
    execution_repo: ExecutionRepository = Depends(),
):
    """取消執行"""
    execution = await execution_repo.get(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    from src.domain.executions.state_machine import ExecutionStateMachine
    if not ExecutionStateMachine.can_transition(
        ExecutionStatus(execution.status),
        ExecutionStatus.CANCELLED,
    ):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel execution in {execution.status} status",
        )

    await execution_repo.update(
        id=execution_id,
        status="cancelled",
        completed_at=datetime.utcnow(),
    )

    return {"status": "cancelled"}
```

---

## 時間規劃

### Week 3 (Day 1-5)

| 日期 | 任務 | 負責人 | 產出 |
|------|------|--------|------|
| Day 1-2 | S1-1: Azure OpenAI 客戶端集成 | Backend | AgentService |
| Day 2-3 | S1-1: Agent CRUD API | Backend | agents/routes.py |
| Day 3-4 | S1-2: Workflow 領域模型 | Backend | workflows/models.py |
| Day 4-5 | S1-2: WorkflowBuilder 集成 | Backend | execution_service.py |

### Week 4 (Day 6-10)

| 日期 | 任務 | 負責人 | 產出 |
|------|------|--------|------|
| Day 6-7 | S1-2: Workflow API | Backend | workflows/routes.py |
| Day 7-8 | S1-3: 工具基礎類和內建工具 | Backend | tools/*.py |
| Day 8-9 | S1-4: 執行狀態機 | Backend | state_machine.py |
| Day 9-10 | 集成測試 + 文檔 | 全員 | 測試用例 + API 文檔 |

---

## 測試要求

### 單元測試

```python
# tests/unit/test_agent_service.py
import pytest
from unittest.mock import AsyncMock, patch

from src.domain.agents.service import AgentService, AgentConfig


class TestAgentService:

    @pytest.fixture
    def agent_service(self):
        return AgentService()

    @pytest.mark.asyncio
    async def test_create_agent(self, agent_service):
        # Mock Azure client
        with patch.object(agent_service, '_client') as mock_client:
            mock_client.create_agent.return_value = AsyncMock()

            config = AgentConfig(
                name="test-agent",
                instructions="You are a test agent",
            )
            executor = agent_service.create_agent(config)

            assert executor is not None
            mock_client.create_agent.assert_called_once()


# tests/unit/test_execution_state_machine.py
import pytest

from src.domain.executions.state_machine import (
    ExecutionStatus,
    ExecutionStateMachine,
)


class TestExecutionStateMachine:

    def test_valid_transition_pending_to_running(self):
        assert ExecutionStateMachine.can_transition(
            ExecutionStatus.PENDING,
            ExecutionStatus.RUNNING,
        )

    def test_invalid_transition_completed_to_running(self):
        assert not ExecutionStateMachine.can_transition(
            ExecutionStatus.COMPLETED,
            ExecutionStatus.RUNNING,
        )

    def test_is_terminal_completed(self):
        assert ExecutionStateMachine.is_terminal(ExecutionStatus.COMPLETED)

    def test_is_not_terminal_running(self):
        assert not ExecutionStateMachine.is_terminal(ExecutionStatus.RUNNING)
```

### 集成測試

```python
# tests/integration/test_workflow_execution.py
import pytest
from httpx import AsyncClient

from main import app


class TestWorkflowExecution:

    @pytest.fixture
    async def client(self):
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    @pytest.mark.asyncio
    async def test_create_and_execute_workflow(self, client):
        # 創建 Agent
        agent_response = await client.post("/api/v1/agents/", json={
            "name": "test-agent",
            "instructions": "You are a helpful assistant",
        })
        assert agent_response.status_code == 200
        agent_id = agent_response.json()["id"]

        # 創建 Workflow
        workflow_response = await client.post("/api/v1/workflows/", json={
            "name": "test-workflow",
            "graph_definition": {
                "nodes": [
                    {"id": "start", "type": "start"},
                    {"id": "agent1", "type": "agent", "agent_id": agent_id},
                    {"id": "end", "type": "end"},
                ],
                "edges": [
                    {"source": "start", "target": "agent1"},
                    {"source": "agent1", "target": "end"},
                ],
            },
        })
        assert workflow_response.status_code == 200
        workflow_id = workflow_response.json()["id"]

        # 執行 Workflow
        execute_response = await client.post(
            f"/api/v1/workflows/{workflow_id}/execute",
            json={"message": "Hello, world!"},
        )
        assert execute_response.status_code == 200
        assert "execution_id" in execute_response.json()
```

---

## 風險與緩解

| 風險 | 可能性 | 影響 | 緩解措施 |
|------|--------|------|---------|
| Agent Framework API 變更 | 高 | 高 | 封裝抽象層，監控 Release Notes |
| Azure OpenAI 配額限制 | 中 | 中 | 實現 Rate Limiting，使用緩存 |
| 工作流執行超時 | 中 | 高 | 設置合理超時，支持取消機制 |
| LLM 成本超預算 | 高 | 中 | Token 統計，成本監控告警 |

---

## 完成定義 (Definition of Done)

1. **功能完成**
   - [ ] Agent CRUD API 可用
   - [ ] Agent 可執行對話任務
   - [ ] Workflow 可串聯 Agent 執行
   - [ ] 工具調用正常

2. **測試完成**
   - [ ] 單元測試覆蓋率 >= 80%
   - [ ] 集成測試通過
   - [ ] Agent 執行端到端測試通過

3. **文檔完成**
   - [ ] API 文檔 (Swagger) 完整
   - [ ] Agent 開發指南
   - [ ] 工具開發指南

---

## 相關文檔

- [Sprint 1 Checklist](./sprint-1-checklist.md)
- [Sprint 0 Plan](./sprint-0-plan.md) - 前置 Sprint
- [Agent Framework 參考](../../../reference/agent-framework/)
- [技術架構](../../02-architecture/technical-architecture.md)
