# Sprint 51: API Routes Completion for Tools, Hooks, MCP & Hybrid

## Sprint Overview

| Item | Details |
|------|---------|
| **Sprint Goal** | 為 Sprint 49-50 已實現的功能補齊 REST API 路由 |
| **Sprint Period** | Phase 12 - Claude Agent SDK Integration |
| **Story Points** | 25 points |
| **MVP Feature** | 完整的 Claude SDK REST API 端點暴露 |
| **Prerequisites** | Sprint 48-50 已完成 (Integration Layer) |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Sprint 51: API Routes Layer                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    REST API Endpoints                          │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌────────────┐ ┌───────────┐ │  │
│  │  │ /tools/*    │ │ /hooks/*    │ │ /mcp/*     │ │ /hybrid/* │ │  │
│  │  │ (S51-1)     │ │ (S51-2)     │ │ (S51-3)    │ │ (S51-4)   │ │  │
│  │  └──────┬──────┘ └──────┬──────┘ └─────┬──────┘ └─────┬─────┘ │  │
│  └─────────┼───────────────┼───────────────┼─────────────┼───────┘  │
│            │               │               │             │           │
│            ▼               ▼               ▼             ▼           │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              Integration Layer (Sprint 49-50 已實現)           │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌────────────┐ ┌───────────┐ │  │
│  │  │   tools/    │ │   hooks/    │ │   mcp/     │ │  hybrid/  │ │  │
│  │  │ file_tools  │ │ approval    │ │ manager    │ │orchestrate│ │  │
│  │  │ cmd_tools   │ │ audit       │ │ discovery  │ │ selector  │ │  │
│  │  │ web_tools   │ │ rate_limit  │ │ stdio      │ │capability │ │  │
│  │  │ registry    │ │ sandbox     │ │ http       │ │ sync      │ │  │
│  │  └─────────────┘ └─────────────┘ └────────────┘ └───────────┘ │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## User Stories

### S51-1: Tools API Routes (8 points)

**Description**: 為 Claude SDK 工具系統建立 REST API 端點

**Acceptance Criteria**:
- [ ] POST `/claude-sdk/tools/execute` - 執行工具
- [ ] GET `/claude-sdk/tools` - 列出所有可用工具
- [ ] GET `/claude-sdk/tools/{name}` - 獲取工具詳情
- [ ] POST `/claude-sdk/tools/validate` - 驗證工具參數
- [ ] Pydantic schemas for request/response validation
- [ ] 整合現有 tools/ 模組 (file_tools, command_tools, web_tools, registry)

**API Endpoints**:

```python
# backend/src/api/v1/claude_sdk/tools_routes.py

from fastapi import APIRouter, HTTPException, status
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

router = APIRouter(prefix="/tools", tags=["Claude SDK - Tools"])


# ============= Schemas =============

class ToolParameter(BaseModel):
    """工具參數定義"""
    name: str
    type: str
    description: str
    required: bool = True
    default: Optional[Any] = None


class ToolInfo(BaseModel):
    """工具資訊"""
    name: str
    description: str
    category: str  # file, command, web, custom
    parameters: List[ToolParameter]
    requires_approval: bool = False


class ToolExecuteRequest(BaseModel):
    """工具執行請求"""
    tool_name: str = Field(..., description="工具名稱")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="工具參數")
    session_id: Optional[str] = Field(None, description="關聯的會話 ID")
    timeout: int = Field(30, ge=1, le=300, description="執行超時秒數")


class ToolExecuteResponse(BaseModel):
    """工具執行回應"""
    success: bool
    tool_name: str
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: float
    requires_approval: bool = False
    approval_id: Optional[str] = None


class ToolValidateRequest(BaseModel):
    """工具參數驗證請求"""
    tool_name: str
    parameters: Dict[str, Any]


class ToolValidateResponse(BaseModel):
    """工具參數驗證回應"""
    valid: bool
    errors: List[str] = Field(default_factory=list)


# ============= Endpoints =============

@router.get("/", response_model=List[ToolInfo])
async def list_tools(
    category: Optional[str] = None,
    include_disabled: bool = False
):
    """
    列出所有可用工具

    Args:
        category: 過濾工具類別 (file, command, web, custom)
        include_disabled: 是否包含已停用工具
    """
    from src.integrations.claude_sdk.tools.registry import ToolRegistry

    registry = ToolRegistry()
    tools = registry.list_tools(category=category, include_disabled=include_disabled)
    return tools


@router.get("/{name}", response_model=ToolInfo)
async def get_tool(name: str):
    """
    獲取特定工具詳情

    Args:
        name: 工具名稱
    """
    from src.integrations.claude_sdk.tools.registry import ToolRegistry

    registry = ToolRegistry()
    tool = registry.get_tool(name)

    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{name}' not found"
        )

    return tool


@router.post("/execute", response_model=ToolExecuteResponse)
async def execute_tool(request: ToolExecuteRequest):
    """
    執行工具

    Args:
        request: 工具執行請求
    """
    from src.integrations.claude_sdk.tools.registry import ToolRegistry
    import time

    registry = ToolRegistry()
    start_time = time.time()

    try:
        # 檢查工具是否存在
        tool = registry.get_tool(request.tool_name)
        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool '{request.tool_name}' not found"
            )

        # 檢查是否需要審批
        if tool.requires_approval:
            approval_id = await registry.request_approval(
                tool_name=request.tool_name,
                parameters=request.parameters,
                session_id=request.session_id
            )
            return ToolExecuteResponse(
                success=False,
                tool_name=request.tool_name,
                requires_approval=True,
                approval_id=approval_id,
                execution_time_ms=(time.time() - start_time) * 1000
            )

        # 執行工具
        result = await registry.execute(
            tool_name=request.tool_name,
            parameters=request.parameters,
            timeout=request.timeout
        )

        return ToolExecuteResponse(
            success=True,
            tool_name=request.tool_name,
            result=result,
            execution_time_ms=(time.time() - start_time) * 1000
        )

    except Exception as e:
        return ToolExecuteResponse(
            success=False,
            tool_name=request.tool_name,
            error=str(e),
            execution_time_ms=(time.time() - start_time) * 1000
        )


@router.post("/validate", response_model=ToolValidateResponse)
async def validate_tool_parameters(request: ToolValidateRequest):
    """
    驗證工具參數

    Args:
        request: 驗證請求
    """
    from src.integrations.claude_sdk.tools.registry import ToolRegistry

    registry = ToolRegistry()

    # 檢查工具是否存在
    tool = registry.get_tool(request.tool_name)
    if not tool:
        return ToolValidateResponse(
            valid=False,
            errors=[f"Tool '{request.tool_name}' not found"]
        )

    # 驗證參數
    errors = registry.validate_parameters(
        tool_name=request.tool_name,
        parameters=request.parameters
    )

    return ToolValidateResponse(
        valid=len(errors) == 0,
        errors=errors
    )
```

**File Structure**:
```
backend/src/api/v1/claude_sdk/
├── __init__.py           # Update to include tools_routes
├── routes.py             # Existing Sprint 48 routes
├── schemas.py            # Existing schemas
└── tools_routes.py       # 🆕 S51-1: Tools API routes
```

---

### S51-2: Hooks API Routes (5 points)

**Description**: 為 Claude SDK Hooks 系統建立 REST API 端點

**Acceptance Criteria**:
- [ ] POST `/claude-sdk/hooks/register` - 註冊新 Hook
- [ ] GET `/claude-sdk/hooks` - 列出所有 Hooks
- [ ] GET `/claude-sdk/hooks/{id}` - 獲取 Hook 詳情
- [ ] DELETE `/claude-sdk/hooks/{id}` - 移除 Hook
- [ ] PUT `/claude-sdk/hooks/{id}/enable` - 啟用 Hook
- [ ] PUT `/claude-sdk/hooks/{id}/disable` - 停用 Hook
- [ ] 整合現有 hooks/ 模組 (approval, audit, rate_limit, sandbox)

**API Endpoints**:

```python
# backend/src/api/v1/claude_sdk/hooks_routes.py

from fastapi import APIRouter, HTTPException, status
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

router = APIRouter(prefix="/hooks", tags=["Claude SDK - Hooks"])


# ============= Schemas =============

class HookType(str, Enum):
    """Hook 類型"""
    APPROVAL = "approval"
    AUDIT = "audit"
    RATE_LIMIT = "rate_limit"
    SANDBOX = "sandbox"
    CUSTOM = "custom"


class HookPriority(int, Enum):
    """Hook 優先級"""
    LOW = 10
    NORMAL = 50
    HIGH = 90
    CRITICAL = 100


class HookConfig(BaseModel):
    """Hook 配置"""
    type: HookType
    priority: HookPriority = HookPriority.NORMAL
    enabled: bool = True
    config: Dict[str, Any] = Field(default_factory=dict)


class HookInfo(BaseModel):
    """Hook 資訊"""
    id: str
    type: HookType
    priority: HookPriority
    enabled: bool
    config: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class HookRegisterRequest(BaseModel):
    """Hook 註冊請求"""
    type: HookType
    priority: HookPriority = HookPriority.NORMAL
    config: Dict[str, Any] = Field(default_factory=dict)


class HookRegisterResponse(BaseModel):
    """Hook 註冊回應"""
    id: str
    type: HookType
    message: str


# ============= Endpoints =============

@router.get("/", response_model=List[HookInfo])
async def list_hooks(
    type: Optional[HookType] = None,
    enabled_only: bool = False
):
    """
    列出所有 Hooks

    Args:
        type: 過濾 Hook 類型
        enabled_only: 只顯示啟用的 Hooks
    """
    from src.integrations.claude_sdk.hooks import HookManager

    manager = HookManager()
    hooks = manager.list_hooks(hook_type=type, enabled_only=enabled_only)
    return hooks


@router.get("/{hook_id}", response_model=HookInfo)
async def get_hook(hook_id: str):
    """
    獲取特定 Hook 詳情

    Args:
        hook_id: Hook ID
    """
    from src.integrations.claude_sdk.hooks import HookManager

    manager = HookManager()
    hook = manager.get_hook(hook_id)

    if not hook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hook '{hook_id}' not found"
        )

    return hook


@router.post("/register", response_model=HookRegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_hook(request: HookRegisterRequest):
    """
    註冊新 Hook

    Args:
        request: Hook 註冊請求
    """
    from src.integrations.claude_sdk.hooks import HookManager

    manager = HookManager()

    try:
        hook_id = await manager.register_hook(
            hook_type=request.type,
            priority=request.priority,
            config=request.config
        )

        return HookRegisterResponse(
            id=hook_id,
            type=request.type,
            message=f"Hook registered successfully"
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{hook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_hook(hook_id: str):
    """
    移除 Hook

    Args:
        hook_id: Hook ID
    """
    from src.integrations.claude_sdk.hooks import HookManager

    manager = HookManager()
    success = await manager.remove_hook(hook_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hook '{hook_id}' not found"
        )


@router.put("/{hook_id}/enable", response_model=HookInfo)
async def enable_hook(hook_id: str):
    """
    啟用 Hook

    Args:
        hook_id: Hook ID
    """
    from src.integrations.claude_sdk.hooks import HookManager

    manager = HookManager()
    hook = await manager.enable_hook(hook_id)

    if not hook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hook '{hook_id}' not found"
        )

    return hook


@router.put("/{hook_id}/disable", response_model=HookInfo)
async def disable_hook(hook_id: str):
    """
    停用 Hook

    Args:
        hook_id: Hook ID
    """
    from src.integrations.claude_sdk.hooks import HookManager

    manager = HookManager()
    hook = await manager.disable_hook(hook_id)

    if not hook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hook '{hook_id}' not found"
        )

    return hook
```

**File Structure**:
```
backend/src/api/v1/claude_sdk/
├── __init__.py           # Update to include hooks_routes
├── routes.py             # Existing Sprint 48 routes
├── schemas.py            # Existing schemas
├── tools_routes.py       # S51-1: Tools API routes
└── hooks_routes.py       # 🆕 S51-2: Hooks API routes
```

---

### S51-3: MCP API Routes (7 points)

**Description**: 為 Claude SDK MCP (Model Context Protocol) 管理建立 REST API 端點

**Acceptance Criteria**:
- [ ] GET `/claude-sdk/mcp/servers` - 列出 MCP 伺服器
- [ ] POST `/claude-sdk/mcp/servers/connect` - 連接 MCP 伺服器
- [ ] POST `/claude-sdk/mcp/servers/{id}/disconnect` - 斷開連接
- [ ] GET `/claude-sdk/mcp/servers/{id}/health` - 健康檢查
- [ ] GET `/claude-sdk/mcp/tools` - 列出 MCP 工具
- [ ] POST `/claude-sdk/mcp/tools/execute` - 執行 MCP 工具
- [ ] 整合現有 mcp/ 模組 (manager, discovery, stdio, http)

**API Endpoints**:

```python
# backend/src/api/v1/claude_sdk/mcp_routes.py

from fastapi import APIRouter, HTTPException, status
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

router = APIRouter(prefix="/mcp", tags=["Claude SDK - MCP"])


# ============= Schemas =============

class MCPTransport(str, Enum):
    """MCP 傳輸協議"""
    STDIO = "stdio"
    HTTP = "http"
    WEBSOCKET = "websocket"


class MCPServerStatus(str, Enum):
    """MCP 伺服器狀態"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    ERROR = "error"


class MCPServerInfo(BaseModel):
    """MCP 伺服器資訊"""
    id: str
    name: str
    transport: MCPTransport
    status: MCPServerStatus
    endpoint: str
    tools_count: int
    connected_at: Optional[datetime] = None
    last_health_check: Optional[datetime] = None


class MCPToolInfo(BaseModel):
    """MCP 工具資訊"""
    name: str
    description: str
    server_id: str
    server_name: str
    input_schema: Dict[str, Any]


class MCPConnectRequest(BaseModel):
    """MCP 連接請求"""
    name: str = Field(..., description="伺服器名稱")
    transport: MCPTransport = Field(..., description="傳輸協議")
    endpoint: str = Field(..., description="連接端點")
    config: Dict[str, Any] = Field(default_factory=dict, description="額外配置")


class MCPConnectResponse(BaseModel):
    """MCP 連接回應"""
    id: str
    name: str
    status: MCPServerStatus
    tools_discovered: int
    message: str


class MCPExecuteRequest(BaseModel):
    """MCP 工具執行請求"""
    server_id: str = Field(..., description="MCP 伺服器 ID")
    tool_name: str = Field(..., description="工具名稱")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="工具參數")
    timeout: int = Field(30, ge=1, le=300, description="執行超時秒數")


class MCPExecuteResponse(BaseModel):
    """MCP 工具執行回應"""
    success: bool
    server_id: str
    tool_name: str
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: float


class MCPHealthResponse(BaseModel):
    """MCP 健康檢查回應"""
    server_id: str
    status: MCPServerStatus
    latency_ms: float
    tools_available: int
    last_error: Optional[str] = None


# ============= Endpoints =============

@router.get("/servers", response_model=List[MCPServerInfo])
async def list_mcp_servers(
    status: Optional[MCPServerStatus] = None,
    transport: Optional[MCPTransport] = None
):
    """
    列出所有 MCP 伺服器

    Args:
        status: 過濾狀態
        transport: 過濾傳輸協議
    """
    from src.integrations.claude_sdk.mcp.manager import MCPManager

    manager = MCPManager()
    servers = await manager.list_servers(status=status, transport=transport)
    return servers


@router.post("/servers/connect", response_model=MCPConnectResponse, status_code=status.HTTP_201_CREATED)
async def connect_mcp_server(request: MCPConnectRequest):
    """
    連接 MCP 伺服器

    Args:
        request: 連接請求
    """
    from src.integrations.claude_sdk.mcp.manager import MCPManager

    manager = MCPManager()

    try:
        result = await manager.connect(
            name=request.name,
            transport=request.transport,
            endpoint=request.endpoint,
            config=request.config
        )

        return MCPConnectResponse(
            id=result.id,
            name=result.name,
            status=result.status,
            tools_discovered=result.tools_count,
            message=f"Successfully connected to {request.name}"
        )

    except ConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to connect: {str(e)}"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/servers/{server_id}/disconnect", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_mcp_server(server_id: str):
    """
    斷開 MCP 伺服器連接

    Args:
        server_id: 伺服器 ID
    """
    from src.integrations.claude_sdk.mcp.manager import MCPManager

    manager = MCPManager()
    success = await manager.disconnect(server_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server '{server_id}' not found"
        )


@router.get("/servers/{server_id}/health", response_model=MCPHealthResponse)
async def check_mcp_health(server_id: str):
    """
    檢查 MCP 伺服器健康狀態

    Args:
        server_id: 伺服器 ID
    """
    from src.integrations.claude_sdk.mcp.manager import MCPManager
    import time

    manager = MCPManager()
    start_time = time.time()

    health = await manager.health_check(server_id)

    if health is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server '{server_id}' not found"
        )

    return MCPHealthResponse(
        server_id=server_id,
        status=health.status,
        latency_ms=(time.time() - start_time) * 1000,
        tools_available=health.tools_count,
        last_error=health.last_error
    )


@router.get("/tools", response_model=List[MCPToolInfo])
async def list_mcp_tools(server_id: Optional[str] = None):
    """
    列出所有 MCP 工具

    Args:
        server_id: 過濾特定伺服器的工具
    """
    from src.integrations.claude_sdk.mcp.manager import MCPManager

    manager = MCPManager()
    tools = await manager.list_tools(server_id=server_id)
    return tools


@router.post("/tools/execute", response_model=MCPExecuteResponse)
async def execute_mcp_tool(request: MCPExecuteRequest):
    """
    執行 MCP 工具

    Args:
        request: 執行請求
    """
    from src.integrations.claude_sdk.mcp.manager import MCPManager
    import time

    manager = MCPManager()
    start_time = time.time()

    try:
        result = await manager.execute_tool(
            server_id=request.server_id,
            tool_name=request.tool_name,
            arguments=request.arguments,
            timeout=request.timeout
        )

        return MCPExecuteResponse(
            success=True,
            server_id=request.server_id,
            tool_name=request.tool_name,
            result=result,
            execution_time_ms=(time.time() - start_time) * 1000
        )

    except Exception as e:
        return MCPExecuteResponse(
            success=False,
            server_id=request.server_id,
            tool_name=request.tool_name,
            error=str(e),
            execution_time_ms=(time.time() - start_time) * 1000
        )
```

**File Structure**:
```
backend/src/api/v1/claude_sdk/
├── __init__.py           # Update to include mcp_routes
├── routes.py             # Existing Sprint 48 routes
├── schemas.py            # Existing schemas
├── tools_routes.py       # S51-1: Tools API routes
├── hooks_routes.py       # S51-2: Hooks API routes
└── mcp_routes.py         # 🆕 S51-3: MCP API routes
```

---

### S51-4: Hybrid Orchestration API Routes (5 points)

**Description**: 為 Claude SDK Hybrid 協調系統建立 REST API 端點

**Acceptance Criteria**:
- [ ] POST `/claude-sdk/hybrid/execute` - 執行混合請求
- [ ] POST `/claude-sdk/hybrid/analyze` - 分析能力選擇
- [ ] GET `/claude-sdk/hybrid/metrics` - 獲取協調指標
- [ ] POST `/claude-sdk/hybrid/context/sync` - 同步上下文
- [ ] GET `/claude-sdk/hybrid/capabilities` - 獲取可用能力
- [ ] 整合現有 hybrid/ 模組 (orchestrator, selector, capability, synchronizer)

**API Endpoints**:

```python
# backend/src/api/v1/claude_sdk/hybrid_routes.py

from fastapi import APIRouter, HTTPException, status
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

router = APIRouter(prefix="/hybrid", tags=["Claude SDK - Hybrid"])


# ============= Schemas =============

class ExecutionPreference(str, Enum):
    """執行偏好"""
    CLAUDE_PREFERRED = "claude_preferred"
    AGENT_FRAMEWORK_PREFERRED = "agent_framework_preferred"
    AUTO_SELECT = "auto_select"
    COST_OPTIMIZED = "cost_optimized"
    LATENCY_OPTIMIZED = "latency_optimized"


class CapabilityType(str, Enum):
    """能力類型"""
    CODE_GENERATION = "code_generation"
    CODE_ANALYSIS = "code_analysis"
    CONVERSATION = "conversation"
    TOOL_USE = "tool_use"
    MULTI_AGENT = "multi_agent"
    WORKFLOW = "workflow"


class CapabilityInfo(BaseModel):
    """能力資訊"""
    type: CapabilityType
    source: str  # claude_sdk, agent_framework, hybrid
    confidence: float = Field(ge=0.0, le=1.0)
    latency_estimate_ms: float
    cost_estimate: float


class HybridExecuteRequest(BaseModel):
    """混合執行請求"""
    task: str = Field(..., description="任務描述")
    preference: ExecutionPreference = ExecutionPreference.AUTO_SELECT
    context: Dict[str, Any] = Field(default_factory=dict, description="執行上下文")
    session_id: Optional[str] = Field(None, description="會話 ID")
    timeout: int = Field(60, ge=1, le=600, description="超時秒數")


class HybridExecuteResponse(BaseModel):
    """混合執行回應"""
    success: bool
    selected_executor: str  # claude_sdk, agent_framework
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: float
    capability_used: CapabilityType
    decision_reason: str


class HybridAnalyzeRequest(BaseModel):
    """混合分析請求"""
    task: str = Field(..., description="任務描述")
    preference: ExecutionPreference = ExecutionPreference.AUTO_SELECT
    include_cost_analysis: bool = False
    include_latency_analysis: bool = False


class HybridAnalyzeResponse(BaseModel):
    """混合分析回應"""
    recommended_executor: str
    confidence: float
    capabilities_matched: List[CapabilityInfo]
    alternatives: List[Dict[str, Any]]
    analysis_reason: str


class HybridMetrics(BaseModel):
    """混合協調指標"""
    total_executions: int
    claude_sdk_count: int
    agent_framework_count: int
    average_latency_ms: float
    success_rate: float
    cost_total: float
    capability_distribution: Dict[str, int]
    period_start: datetime
    period_end: datetime


class ContextSyncRequest(BaseModel):
    """上下文同步請求"""
    session_id: str = Field(..., description="會話 ID")
    source: str = Field(..., description="來源 (claude_sdk / agent_framework)")
    context: Dict[str, Any] = Field(..., description="要同步的上下文")


class ContextSyncResponse(BaseModel):
    """上下文同步回應"""
    success: bool
    session_id: str
    synced_keys: List[str]
    conflicts: List[str] = Field(default_factory=list)


# ============= Endpoints =============

@router.post("/execute", response_model=HybridExecuteResponse)
async def hybrid_execute(request: HybridExecuteRequest):
    """
    執行混合請求 - 自動選擇最佳執行器

    Args:
        request: 執行請求
    """
    from src.integrations.claude_sdk.hybrid.orchestrator import HybridOrchestrator
    import time

    orchestrator = HybridOrchestrator()
    start_time = time.time()

    try:
        result = await orchestrator.execute(
            task=request.task,
            preference=request.preference,
            context=request.context,
            session_id=request.session_id,
            timeout=request.timeout
        )

        return HybridExecuteResponse(
            success=True,
            selected_executor=result.executor,
            result=result.output,
            execution_time_ms=(time.time() - start_time) * 1000,
            capability_used=result.capability,
            decision_reason=result.reason
        )

    except Exception as e:
        return HybridExecuteResponse(
            success=False,
            selected_executor="unknown",
            error=str(e),
            execution_time_ms=(time.time() - start_time) * 1000,
            capability_used=CapabilityType.CONVERSATION,
            decision_reason="Execution failed"
        )


@router.post("/analyze", response_model=HybridAnalyzeResponse)
async def hybrid_analyze(request: HybridAnalyzeRequest):
    """
    分析任務並推薦最佳執行器

    Args:
        request: 分析請求
    """
    from src.integrations.claude_sdk.hybrid.selector import CapabilitySelector

    selector = CapabilitySelector()

    analysis = await selector.analyze(
        task=request.task,
        preference=request.preference,
        include_cost=request.include_cost_analysis,
        include_latency=request.include_latency_analysis
    )

    return HybridAnalyzeResponse(
        recommended_executor=analysis.recommended,
        confidence=analysis.confidence,
        capabilities_matched=analysis.capabilities,
        alternatives=analysis.alternatives,
        analysis_reason=analysis.reason
    )


@router.get("/metrics", response_model=HybridMetrics)
async def get_hybrid_metrics(
    period_days: int = 7
):
    """
    獲取混合協調指標

    Args:
        period_days: 統計周期天數
    """
    from src.integrations.claude_sdk.hybrid.orchestrator import HybridOrchestrator
    from datetime import timedelta

    orchestrator = HybridOrchestrator()

    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=period_days)

    metrics = await orchestrator.get_metrics(
        start_time=start_time,
        end_time=end_time
    )

    return HybridMetrics(
        total_executions=metrics.total,
        claude_sdk_count=metrics.claude_count,
        agent_framework_count=metrics.agent_count,
        average_latency_ms=metrics.avg_latency,
        success_rate=metrics.success_rate,
        cost_total=metrics.cost_total,
        capability_distribution=metrics.capability_dist,
        period_start=start_time,
        period_end=end_time
    )


@router.post("/context/sync", response_model=ContextSyncResponse)
async def sync_context(request: ContextSyncRequest):
    """
    同步會話上下文

    Args:
        request: 同步請求
    """
    from src.integrations.claude_sdk.hybrid.synchronizer import ContextSynchronizer

    synchronizer = ContextSynchronizer()

    result = await synchronizer.sync(
        session_id=request.session_id,
        source=request.source,
        context=request.context
    )

    return ContextSyncResponse(
        success=result.success,
        session_id=request.session_id,
        synced_keys=result.synced_keys,
        conflicts=result.conflicts
    )


@router.get("/capabilities", response_model=List[CapabilityInfo])
async def list_capabilities():
    """
    列出所有可用能力
    """
    from src.integrations.claude_sdk.hybrid.capability import CapabilityRegistry

    registry = CapabilityRegistry()
    capabilities = registry.list_all()

    return capabilities
```

**File Structure**:
```
backend/src/api/v1/claude_sdk/
├── __init__.py           # Update to include hybrid_routes
├── routes.py             # Existing Sprint 48 routes
├── schemas.py            # Existing schemas
├── tools_routes.py       # S51-1: Tools API routes
├── hooks_routes.py       # S51-2: Hooks API routes
├── mcp_routes.py         # S51-3: MCP API routes
└── hybrid_routes.py      # 🆕 S51-4: Hybrid API routes
```

---

## Time Planning

| Story | Points | Estimated Hours | Dependencies |
|-------|--------|-----------------|--------------|
| S51-1: Tools API Routes | 8 | 6-8 hrs | Sprint 49 tools/ |
| S51-2: Hooks API Routes | 5 | 4-5 hrs | Sprint 49 hooks/ |
| S51-3: MCP API Routes | 7 | 5-7 hrs | Sprint 50 mcp/ |
| S51-4: Hybrid API Routes | 5 | 4-5 hrs | Sprint 50 hybrid/ |
| **Total** | **25** | **19-25 hrs** | |

---

## Test Requirements

### Unit Tests

```python
# tests/unit/api/v1/claude_sdk/test_tools_routes.py

import pytest
from httpx import AsyncClient
from fastapi import status


class TestToolsRoutes:
    """Tools API Routes Unit Tests"""

    @pytest.mark.asyncio
    async def test_list_tools_returns_all_tools(self, client: AsyncClient):
        """測試列出所有工具"""
        response = await client.get("/api/v1/claude-sdk/tools")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_list_tools_filter_by_category(self, client: AsyncClient):
        """測試按類別過濾工具"""
        response = await client.get("/api/v1/claude-sdk/tools?category=file")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for tool in data:
            assert tool["category"] == "file"

    @pytest.mark.asyncio
    async def test_get_tool_returns_tool_info(self, client: AsyncClient):
        """測試獲取工具詳情"""
        response = await client.get("/api/v1/claude-sdk/tools/read_file")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "read_file"

    @pytest.mark.asyncio
    async def test_get_tool_not_found(self, client: AsyncClient):
        """測試工具不存在"""
        response = await client.get("/api/v1/claude-sdk/tools/nonexistent")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_execute_tool_success(self, client: AsyncClient):
        """測試執行工具成功"""
        response = await client.post(
            "/api/v1/claude-sdk/tools/execute",
            json={
                "tool_name": "read_file",
                "parameters": {"path": "/tmp/test.txt"},
                "timeout": 10
            }
        )
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_validate_tool_parameters(self, client: AsyncClient):
        """測試驗證工具參數"""
        response = await client.post(
            "/api/v1/claude-sdk/tools/validate",
            json={
                "tool_name": "read_file",
                "parameters": {"path": "/tmp/test.txt"}
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "valid" in data


# tests/unit/api/v1/claude_sdk/test_hooks_routes.py

class TestHooksRoutes:
    """Hooks API Routes Unit Tests"""

    @pytest.mark.asyncio
    async def test_list_hooks_returns_all(self, client: AsyncClient):
        """測試列出所有 Hooks"""
        response = await client.get("/api/v1/claude-sdk/hooks")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_register_hook_success(self, client: AsyncClient):
        """測試註冊 Hook"""
        response = await client.post(
            "/api/v1/claude-sdk/hooks/register",
            json={
                "type": "audit",
                "priority": 50,
                "config": {"log_level": "info"}
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "id" in data

    @pytest.mark.asyncio
    async def test_enable_disable_hook(self, client: AsyncClient):
        """測試啟用/停用 Hook"""
        # First register a hook
        register_resp = await client.post(
            "/api/v1/claude-sdk/hooks/register",
            json={"type": "audit", "priority": 50, "config": {}}
        )
        hook_id = register_resp.json()["id"]

        # Disable
        response = await client.put(f"/api/v1/claude-sdk/hooks/{hook_id}/disable")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["enabled"] is False

        # Enable
        response = await client.put(f"/api/v1/claude-sdk/hooks/{hook_id}/enable")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["enabled"] is True


# tests/unit/api/v1/claude_sdk/test_mcp_routes.py

class TestMCPRoutes:
    """MCP API Routes Unit Tests"""

    @pytest.mark.asyncio
    async def test_list_mcp_servers(self, client: AsyncClient):
        """測試列出 MCP 伺服器"""
        response = await client.get("/api/v1/claude-sdk/mcp/servers")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_connect_mcp_server(self, client: AsyncClient):
        """測試連接 MCP 伺服器"""
        response = await client.post(
            "/api/v1/claude-sdk/mcp/servers/connect",
            json={
                "name": "test-server",
                "transport": "stdio",
                "endpoint": "python -m test_server",
                "config": {}
            }
        )
        # May fail if server not available, but should return proper error
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_503_SERVICE_UNAVAILABLE
        ]

    @pytest.mark.asyncio
    async def test_list_mcp_tools(self, client: AsyncClient):
        """測試列出 MCP 工具"""
        response = await client.get("/api/v1/claude-sdk/mcp/tools")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)


# tests/unit/api/v1/claude_sdk/test_hybrid_routes.py

class TestHybridRoutes:
    """Hybrid API Routes Unit Tests"""

    @pytest.mark.asyncio
    async def test_hybrid_execute(self, client: AsyncClient):
        """測試混合執行"""
        response = await client.post(
            "/api/v1/claude-sdk/hybrid/execute",
            json={
                "task": "Generate a simple Python function",
                "preference": "auto_select",
                "context": {}
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "selected_executor" in data

    @pytest.mark.asyncio
    async def test_hybrid_analyze(self, client: AsyncClient):
        """測試混合分析"""
        response = await client.post(
            "/api/v1/claude-sdk/hybrid/analyze",
            json={
                "task": "Analyze this code for bugs",
                "preference": "auto_select"
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "recommended_executor" in data

    @pytest.mark.asyncio
    async def test_get_hybrid_metrics(self, client: AsyncClient):
        """測試獲取混合指標"""
        response = await client.get("/api/v1/claude-sdk/hybrid/metrics")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_executions" in data

    @pytest.mark.asyncio
    async def test_list_capabilities(self, client: AsyncClient):
        """測試列出能力"""
        response = await client.get("/api/v1/claude-sdk/hybrid/capabilities")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
```

### Test Coverage Targets

| Module | Target Coverage |
|--------|-----------------|
| tools_routes.py | >= 85% |
| hooks_routes.py | >= 85% |
| mcp_routes.py | >= 80% |
| hybrid_routes.py | >= 80% |

---

## Risk and Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Integration Layer API 變更 | High | Low | 使用 Adapter 模式隔離變更 |
| MCP 伺服器連接失敗 | Medium | Medium | 實現優雅降級和錯誤處理 |
| 性能瓶頸 | Medium | Low | 使用 async/await，實現快取 |
| Schema 驗證錯誤 | Low | Medium | 完整的 Pydantic validation |

---

## Completion Definition

### Sprint 完成標準

- [ ] 所有 4 個 Stories 實現完成
- [ ] 所有 API 端點可正常呼叫
- [ ] 單元測試覆蓋率 >= 80%
- [ ] API 文檔 (OpenAPI) 更新
- [ ] Phase 12 UAT 測試可無 simulation fallback 執行

### API Endpoints Summary

| Category | Endpoint Count |
|----------|---------------|
| Tools | 4 endpoints |
| Hooks | 6 endpoints |
| MCP | 6 endpoints |
| Hybrid | 5 endpoints |
| **Total** | **21 endpoints** |

---

## Dependencies

### 依賴的已完成 Sprint

- **Sprint 48**: Core SDK Integration (client, session, query)
- **Sprint 49**: Tools & Hooks System (tools/, hooks/)
- **Sprint 50**: MCP & Hybrid Orchestration (mcp/, hybrid/)

### 依賴的模組

```
backend/src/integrations/claude_sdk/
├── tools/           # Sprint 49
│   ├── file_tools.py
│   ├── command_tools.py
│   ├── web_tools.py
│   └── registry.py
├── hooks/           # Sprint 49
│   ├── approval.py
│   ├── audit.py
│   ├── rate_limit.py
│   └── sandbox.py
├── mcp/             # Sprint 50
│   ├── manager.py
│   ├── discovery.py
│   ├── stdio.py
│   └── http.py
└── hybrid/          # Sprint 50
    ├── orchestrator.py
    ├── selector.py
    ├── capability.py
    └── synchronizer.py
```

---

## Router Integration

更新 `__init__.py` 以包含所有新路由:

```python
# backend/src/api/v1/claude_sdk/__init__.py

from fastapi import APIRouter

from .routes import router as core_router
from .tools_routes import router as tools_router
from .hooks_routes import router as hooks_router
from .mcp_routes import router as mcp_router
from .hybrid_routes import router as hybrid_router

# Main Claude SDK router
router = APIRouter(prefix="/claude-sdk", tags=["Claude SDK"])

# Include all sub-routers
router.include_router(core_router)    # Sprint 48: /query, /sessions
router.include_router(tools_router)   # Sprint 51: /tools
router.include_router(hooks_router)   # Sprint 51: /hooks
router.include_router(mcp_router)     # Sprint 51: /mcp
router.include_router(hybrid_router)  # Sprint 51: /hybrid
```

---

**Created**: 2025-12-26
**Phase**: 12 - Claude Agent SDK Integration
**Sprint**: 51
**Status**: Planning
