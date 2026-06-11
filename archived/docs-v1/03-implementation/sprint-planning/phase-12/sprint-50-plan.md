# Sprint 50: MCP & Hybrid Architecture - MCP 與混合架構

**Sprint 目標**: 實現 MCP Server 整合與雙框架混合架構
**週期**: Week 5-6
**總點數**: 38 點

---

## Story 列表

| Story ID | 名稱 | 點數 | 優先級 |
|----------|------|------|--------|
| S50-1 | MCP Server 基礎 | 10 | P0 |
| S50-2 | MCP Manager 與工具發現 | 8 | P0 |
| S50-3 | Hybrid Orchestrator | 12 | P0 |
| S50-4 | Context Synchronizer | 8 | P1 |

---

## S50-1: MCP Server 基礎 (10 點)

### 目標
實現 MCP Server 連接機制，支援 Stdio 和 HTTP 兩種協定。

### 技術規格

#### 檔案結構
```
backend/src/integrations/claude_sdk/mcp/
├── __init__.py
├── base.py           # MCPServer 基礎類別
├── stdio.py          # MCPStdioServer
├── http.py           # MCPHTTPServer
├── types.py          # MCP 型別定義
└── exceptions.py     # MCP 例外類別
```

#### MCPServer 基礎類別
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import asyncio

@dataclass
class MCPTool:
    """MCP 工具定義"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    server: str

@dataclass
class MCPToolResult:
    """MCP 工具執行結果"""
    content: str
    success: bool = True
    error: Optional[str] = None

class MCPServer(ABC):
    """MCP Server 基礎類別"""

    def __init__(self, name: str, timeout: int = 30):
        self.name = name
        self.timeout = timeout
        self._connected = False
        self._tools: List[MCPTool] = []

    @property
    def is_connected(self) -> bool:
        return self._connected

    @abstractmethod
    async def connect(self) -> None:
        """建立連接"""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """斷開連接"""
        pass

    @abstractmethod
    async def list_tools(self) -> List[MCPTool]:
        """列出可用工具"""
        pass

    @abstractmethod
    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> MCPToolResult:
        """執行工具"""
        pass

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
```

#### MCPStdioServer 實現
```python
import subprocess
import json
from typing import List, Dict, Any, Optional

class MCPStdioServer(MCPServer):
    """基於 Stdio 的 MCP Server (本地進程)"""

    def __init__(
        self,
        name: str,
        command: str,
        args: List[str] = None,
        env: Dict[str, str] = None,
        cwd: str = None,
        timeout: int = 30
    ):
        super().__init__(name, timeout)
        self.command = command
        self.args = args or []
        self.env = env or {}
        self.cwd = cwd
        self._process: Optional[subprocess.Popen] = None

    async def connect(self) -> None:
        """啟動 MCP Server 進程"""
        import os

        # 合併環境變數
        full_env = {**os.environ, **self.env}

        # 啟動進程
        self._process = subprocess.Popen(
            [self.command] + self.args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=full_env,
            cwd=self.cwd
        )

        # 初始化連接
        await self._initialize()
        self._connected = True

    async def _initialize(self) -> None:
        """發送初始化請求"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "claude-sdk-client",
                    "version": "1.0.0"
                }
            }
        }
        await self._send_request(request)

    async def _send_request(self, request: Dict) -> Dict:
        """發送 JSON-RPC 請求"""
        if not self._process:
            raise MCPConnectionError(self.name, "Process not started")

        # 寫入請求
        request_str = json.dumps(request) + "\n"
        self._process.stdin.write(request_str.encode())
        self._process.stdin.flush()

        # 讀取回應
        response_str = self._process.stdout.readline().decode()
        return json.loads(response_str)

    async def disconnect(self) -> None:
        """停止 MCP Server 進程"""
        if self._process:
            self._process.terminate()
            self._process.wait(timeout=5)
            self._process = None
        self._connected = False

    async def list_tools(self) -> List[MCPTool]:
        """列出 MCP Server 提供的工具"""
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }

        response = await self._send_request(request)
        tools = []

        for tool_data in response.get("result", {}).get("tools", []):
            tools.append(MCPTool(
                name=tool_data["name"],
                description=tool_data.get("description", ""),
                input_schema=tool_data.get("inputSchema", {}),
                server=self.name
            ))

        self._tools = tools
        return tools

    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> MCPToolResult:
        """執行 MCP 工具"""
        request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }

        try:
            response = await self._send_request(request)
            result = response.get("result", {})

            # 提取內容
            content_list = result.get("content", [])
            content = ""
            for item in content_list:
                if item.get("type") == "text":
                    content += item.get("text", "")

            return MCPToolResult(content=content, success=True)

        except Exception as e:
            return MCPToolResult(
                content="",
                success=False,
                error=str(e)
            )
```

#### MCPHTTPServer 實現
```python
import aiohttp
from typing import List, Dict, Any, Optional

class MCPHTTPServer(MCPServer):
    """基於 HTTP 的 MCP Server (遠端服務)"""

    def __init__(
        self,
        name: str,
        url: str,
        api_key: str = None,
        headers: Dict[str, str] = None,
        timeout: int = 30
    ):
        super().__init__(name, timeout)
        self.url = url.rstrip("/")
        self.api_key = api_key
        self.headers = headers or {}
        self._session: Optional[aiohttp.ClientSession] = None

    def _get_headers(self) -> Dict[str, str]:
        """組合請求標頭"""
        headers = {
            "Content-Type": "application/json",
            **self.headers
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def connect(self) -> None:
        """建立 HTTP Session"""
        self._session = aiohttp.ClientSession(
            headers=self._get_headers(),
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )

        # 測試連接
        async with self._session.get(f"{self.url}/health") as response:
            if response.status != 200:
                raise MCPConnectionError(
                    self.name,
                    f"Health check failed: {response.status}"
                )

        self._connected = True

    async def disconnect(self) -> None:
        """關閉 HTTP Session"""
        if self._session:
            await self._session.close()
            self._session = None
        self._connected = False

    async def list_tools(self) -> List[MCPTool]:
        """列出遠端 MCP Server 的工具"""
        async with self._session.get(f"{self.url}/tools") as response:
            data = await response.json()

            tools = []
            for tool_data in data.get("tools", []):
                tools.append(MCPTool(
                    name=tool_data["name"],
                    description=tool_data.get("description", ""),
                    input_schema=tool_data.get("inputSchema", {}),
                    server=self.name
                ))

            self._tools = tools
            return tools

    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> MCPToolResult:
        """執行遠端 MCP 工具"""
        payload = {
            "name": tool_name,
            "arguments": arguments
        }

        try:
            async with self._session.post(
                f"{self.url}/tools/call",
                json=payload
            ) as response:
                data = await response.json()

                if response.status != 200:
                    return MCPToolResult(
                        content="",
                        success=False,
                        error=data.get("error", "Unknown error")
                    )

                return MCPToolResult(
                    content=data.get("content", ""),
                    success=True
                )

        except Exception as e:
            return MCPToolResult(
                content="",
                success=False,
                error=str(e)
            )
```

### 驗收標準
- [ ] MCPServer 基礎類別定義完成
- [ ] MCPStdioServer 可啟動本地 MCP 進程
- [ ] MCPHTTPServer 可連接遠端 MCP 服務
- [ ] 工具列表查詢正常運作
- [ ] 工具執行正常運作
- [ ] 錯誤處理完整

---

## S50-2: MCP Manager 與工具發現 (8 點)

### 目標
實現 MCP Server 管理器，支援多 Server 協調與工具發現。

### 技術規格

#### 檔案結構
```
backend/src/integrations/claude_sdk/mcp/
├── manager.py        # MCPManager
└── discovery.py      # 工具發現機制
```

#### MCPManager 實現
```python
from typing import List, Dict, Any, Optional
import asyncio

class MCPManager:
    """MCP Server 管理器"""

    def __init__(self):
        self._servers: Dict[str, MCPServer] = {}
        self._tools: Dict[str, MCPTool] = {}  # tool_name -> MCPTool

    def add_server(self, server: MCPServer) -> None:
        """添加 MCP Server"""
        self._servers[server.name] = server

    def remove_server(self, name: str) -> None:
        """移除 MCP Server"""
        if name in self._servers:
            del self._servers[name]

    async def connect_all(self) -> Dict[str, bool]:
        """連接所有 Server"""
        results = {}

        async def connect_server(name: str, server: MCPServer):
            try:
                await server.connect()
                results[name] = True
            except Exception as e:
                results[name] = False

        # 並行連接
        await asyncio.gather(*[
            connect_server(name, server)
            for name, server in self._servers.items()
        ])

        return results

    async def disconnect_all(self) -> None:
        """斷開所有 Server"""
        await asyncio.gather(*[
            server.disconnect()
            for server in self._servers.values()
        ])

    async def discover_tools(self) -> List[MCPTool]:
        """發現所有可用工具"""
        all_tools = []

        for server in self._servers.values():
            if server.is_connected:
                tools = await server.list_tools()
                all_tools.extend(tools)

                # 建立工具索引
                for tool in tools:
                    key = f"{server.name}:{tool.name}"
                    self._tools[key] = tool

        return all_tools

    async def execute_tool(
        self,
        tool_ref: str,  # "server_name:tool_name"
        arguments: Dict[str, Any]
    ) -> MCPToolResult:
        """執行指定工具"""
        if ":" in tool_ref:
            server_name, tool_name = tool_ref.split(":", 1)
        else:
            # 搜尋工具
            tool_name = tool_ref
            server_name = self._find_tool_server(tool_name)

        if server_name not in self._servers:
            return MCPToolResult(
                content="",
                success=False,
                error=f"Server not found: {server_name}"
            )

        server = self._servers[server_name]
        return await server.execute_tool(tool_name, arguments)

    def _find_tool_server(self, tool_name: str) -> Optional[str]:
        """查找工具所屬的 Server"""
        for key, tool in self._tools.items():
            if tool.name == tool_name:
                return key.split(":")[0]
        return None

    def list_servers(self) -> List[Dict[str, Any]]:
        """列出所有 Server 狀態"""
        return [
            {
                "name": name,
                "connected": server.is_connected,
                "tools_count": len([
                    t for t in self._tools.values()
                    if t.server == name
                ])
            }
            for name, server in self._servers.items()
        ]

    async def health_check(self) -> Dict[str, bool]:
        """健康檢查所有 Server"""
        results = {}

        for name, server in self._servers.items():
            try:
                if server.is_connected:
                    await server.list_tools()
                    results[name] = True
                else:
                    results[name] = False
            except Exception:
                results[name] = False

        return results

    async def __aenter__(self):
        await self.connect_all()
        await self.discover_tools()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect_all()
```

#### 使用範例
```python
# 建立 Manager
manager = MCPManager()

# 添加 MCP Servers
manager.add_server(MCPStdioServer(
    name="postgres",
    command="uvx",
    args=["mcp-server-postgres"],
    env={"DATABASE_URL": "postgresql://..."}
))

manager.add_server(MCPHTTPServer(
    name="enterprise",
    url="https://mcp.company.com",
    api_key="xxx"
))

# 使用 Context Manager
async with manager:
    # 列出所有工具
    tools = await manager.discover_tools()
    print(f"Available tools: {[t.name for t in tools]}")

    # 執行工具
    result = await manager.execute_tool(
        "postgres:query",
        {"sql": "SELECT * FROM users LIMIT 10"}
    )
```

### 驗收標準
- [ ] MCPManager 可管理多個 Server
- [ ] 並行連接所有 Server
- [ ] 工具發現機制正常運作
- [ ] 工具執行可透過 tool_ref 指定
- [ ] 健康檢查機制實現
- [ ] Context Manager 支援

---

## S50-3: Hybrid Orchestrator (12 點)

### 目標
實現雙框架協調器，根據任務特性智能路由至 Microsoft Agent Framework 或 Claude Agent SDK。

### 技術規格

#### 檔案結構
```
backend/src/integrations/claude_sdk/hybrid/
├── __init__.py
├── orchestrator.py   # HybridOrchestrator
├── capability.py     # CapabilityMatcher
├── selector.py       # FrameworkSelector
└── types.py          # 型別定義
```

#### CapabilityMatcher 實現
```python
from dataclasses import dataclass
from enum import Enum
from typing import List, Set

class TaskCapability(Enum):
    """任務所需能力"""
    MULTI_AGENT = "multi_agent"           # 多代理協作
    HANDOFF = "handoff"                   # 代理交接
    FILE_OPERATIONS = "file_operations"   # 檔案操作
    CODE_EXECUTION = "code_execution"     # 程式碼執行
    WEB_SEARCH = "web_search"             # 網頁搜尋
    DATABASE_ACCESS = "database_access"   # 資料庫存取
    PLANNING = "planning"                 # 任務規劃
    CONVERSATION = "conversation"         # 對話管理

@dataclass
class TaskAnalysis:
    """任務分析結果"""
    capabilities: Set[TaskCapability]
    complexity: float  # 0.0 - 1.0
    recommended_framework: str
    confidence: float

class CapabilityMatcher:
    """分析任務所需能力"""

    # 關鍵字到能力的映射
    CAPABILITY_KEYWORDS = {
        TaskCapability.MULTI_AGENT: [
            "collaborate", "team", "agents", "together", "group"
        ],
        TaskCapability.HANDOFF: [
            "handoff", "transfer", "delegate", "specialist"
        ],
        TaskCapability.FILE_OPERATIONS: [
            "read", "write", "edit", "file", "create", "modify"
        ],
        TaskCapability.CODE_EXECUTION: [
            "run", "execute", "code", "script", "compile"
        ],
        TaskCapability.WEB_SEARCH: [
            "search", "find", "lookup", "web", "internet"
        ],
        TaskCapability.DATABASE_ACCESS: [
            "query", "database", "sql", "table", "records"
        ],
        TaskCapability.PLANNING: [
            "plan", "schedule", "organize", "workflow"
        ],
        TaskCapability.CONVERSATION: [
            "chat", "discuss", "conversation", "history"
        ]
    }

    # 框架能力映射
    FRAMEWORK_CAPABILITIES = {
        "microsoft_agent_framework": {
            TaskCapability.MULTI_AGENT,
            TaskCapability.HANDOFF,
            TaskCapability.PLANNING,
        },
        "claude_sdk": {
            TaskCapability.FILE_OPERATIONS,
            TaskCapability.CODE_EXECUTION,
            TaskCapability.WEB_SEARCH,
            TaskCapability.CONVERSATION,
        }
    }

    def analyze(self, prompt: str) -> TaskAnalysis:
        """分析任務提示"""
        prompt_lower = prompt.lower()

        # 識別所需能力
        capabilities = set()
        for capability, keywords in self.CAPABILITY_KEYWORDS.items():
            if any(kw in prompt_lower for kw in keywords):
                capabilities.add(capability)

        # 計算複雜度
        complexity = min(len(capabilities) / 4, 1.0)

        # 選擇框架
        framework, confidence = self._select_framework(capabilities)

        return TaskAnalysis(
            capabilities=capabilities,
            complexity=complexity,
            recommended_framework=framework,
            confidence=confidence
        )

    def _select_framework(
        self,
        capabilities: Set[TaskCapability]
    ) -> tuple[str, float]:
        """根據能力選擇框架"""
        ms_score = len(
            capabilities & self.FRAMEWORK_CAPABILITIES["microsoft_agent_framework"]
        )
        claude_score = len(
            capabilities & self.FRAMEWORK_CAPABILITIES["claude_sdk"]
        )

        total = ms_score + claude_score
        if total == 0:
            return "claude_sdk", 0.5  # 預設使用 Claude SDK

        if ms_score > claude_score:
            return "microsoft_agent_framework", ms_score / total
        else:
            return "claude_sdk", claude_score / total
```

#### HybridOrchestrator 實現
```python
from typing import Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class HybridResult:
    """混合執行結果"""
    content: str
    framework_used: str
    tool_calls: List[Dict[str, Any]]
    tokens_used: int
    duration: float

class HybridOrchestrator:
    """雙框架協調器"""

    def __init__(
        self,
        claude_client: "ClaudeSDKClient",
        ms_agent_service: "AgentService",
        capability_matcher: CapabilityMatcher = None
    ):
        self.claude_client = claude_client
        self.ms_agent_service = ms_agent_service
        self.capability_matcher = capability_matcher or CapabilityMatcher()
        self._context_sync = ContextSynchronizer()

    async def execute(
        self,
        prompt: str,
        force_framework: str = None,
        session_id: str = None,
        **kwargs
    ) -> HybridResult:
        """執行混合任務"""
        import time
        start_time = time.time()

        # 分析任務
        analysis = self.capability_matcher.analyze(prompt)

        # 決定使用的框架
        framework = force_framework or analysis.recommended_framework

        # 同步上下文
        if session_id:
            await self._context_sync.sync_to(framework, session_id)

        # 執行任務
        if framework == "claude_sdk":
            result = await self._execute_claude(prompt, session_id, **kwargs)
        else:
            result = await self._execute_ms_agent(prompt, session_id, **kwargs)

        # 同步結果
        if session_id:
            await self._context_sync.sync_result(session_id, result)

        return HybridResult(
            content=result.content,
            framework_used=framework,
            tool_calls=result.tool_calls,
            tokens_used=result.tokens_used,
            duration=time.time() - start_time
        )

    async def _execute_claude(
        self,
        prompt: str,
        session_id: str = None,
        **kwargs
    ):
        """使用 Claude SDK 執行"""
        if session_id:
            session = await self.claude_client.resume_session(session_id)
        else:
            session = await self.claude_client.create_session()

        return await session.query(prompt, **kwargs)

    async def _execute_ms_agent(
        self,
        prompt: str,
        session_id: str = None,
        **kwargs
    ):
        """使用 Microsoft Agent Framework 執行"""
        # 透過 AgentService 執行
        execution = await self.ms_agent_service.execute(
            prompt=prompt,
            session_id=session_id,
            **kwargs
        )

        return execution

    async def create_hybrid_session(
        self,
        primary_framework: str = "claude_sdk"
    ) -> "HybridSession":
        """建立混合 Session"""
        return HybridSession(
            orchestrator=self,
            primary_framework=primary_framework
        )
```

#### FrameworkSelector 實現
```python
class FrameworkSelector:
    """智能框架選擇器"""

    # 任務類型到框架的映射
    TASK_FRAMEWORK_MAP = {
        # Claude SDK 擅長
        "code_review": "claude_sdk",
        "file_editing": "claude_sdk",
        "debugging": "claude_sdk",
        "documentation": "claude_sdk",
        "analysis": "claude_sdk",

        # Microsoft Agent Framework 擅長
        "multi_agent_workflow": "microsoft_agent_framework",
        "agent_handoff": "microsoft_agent_framework",
        "complex_planning": "microsoft_agent_framework",
        "enterprise_integration": "microsoft_agent_framework"
    }

    def select(
        self,
        task_type: str = None,
        capabilities: Set[TaskCapability] = None,
        user_preference: str = None
    ) -> str:
        """選擇最適合的框架"""
        # 用戶偏好優先
        if user_preference:
            return user_preference

        # 任務類型映射
        if task_type and task_type in self.TASK_FRAMEWORK_MAP:
            return self.TASK_FRAMEWORK_MAP[task_type]

        # 基於能力分析
        if capabilities:
            ms_caps = {
                TaskCapability.MULTI_AGENT,
                TaskCapability.HANDOFF,
                TaskCapability.PLANNING
            }
            if capabilities & ms_caps:
                return "microsoft_agent_framework"

        # 預設使用 Claude SDK
        return "claude_sdk"
```

### 驗收標準
- [ ] CapabilityMatcher 可分析任務能力需求
- [ ] HybridOrchestrator 可路由至正確框架
- [ ] FrameworkSelector 支援多種選擇策略
- [ ] 上下文在框架間正確同步
- [ ] 混合 Session 支援跨框架對話

---

## S50-4: Context Synchronizer (8 點)

### 目標
實現跨框架的上下文同步機制，確保對話歷史和狀態一致。

### 技術規格

#### 檔案結構
```
backend/src/integrations/claude_sdk/hybrid/
├── sync.py           # ContextSynchronizer
└── state.py          # SharedState
```

#### ContextSynchronizer 實現
```python
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import json

@dataclass
class SharedContext:
    """共享上下文"""
    session_id: str
    messages: List[Dict[str, Any]] = field(default_factory=list)
    tool_results: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    active_framework: str = "claude_sdk"

    def to_claude_format(self) -> List[Dict[str, Any]]:
        """轉換為 Claude SDK 格式"""
        claude_messages = []
        for msg in self.messages:
            claude_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        return claude_messages

    def to_ms_format(self) -> List[Dict[str, Any]]:
        """轉換為 Microsoft Agent Framework 格式"""
        ms_messages = []
        for msg in self.messages:
            ms_messages.append({
                "role": msg["role"],
                "content": msg["content"],
                "timestamp": msg.get("timestamp"),
                "metadata": msg.get("metadata", {})
            })
        return ms_messages

class ContextSynchronizer:
    """跨框架上下文同步器"""

    def __init__(self, redis_client=None):
        self._redis = redis_client
        self._local_cache: Dict[str, SharedContext] = {}

    async def get_context(self, session_id: str) -> SharedContext:
        """獲取共享上下文"""
        # 先查本地快取
        if session_id in self._local_cache:
            return self._local_cache[session_id]

        # 查 Redis
        if self._redis:
            data = await self._redis.get(f"hybrid:context:{session_id}")
            if data:
                context_dict = json.loads(data)
                context = SharedContext(**context_dict)
                self._local_cache[session_id] = context
                return context

        # 建立新上下文
        context = SharedContext(session_id=session_id)
        self._local_cache[session_id] = context
        return context

    async def save_context(self, context: SharedContext) -> None:
        """儲存共享上下文"""
        self._local_cache[context.session_id] = context

        if self._redis:
            await self._redis.set(
                f"hybrid:context:{context.session_id}",
                json.dumps({
                    "session_id": context.session_id,
                    "messages": context.messages,
                    "tool_results": context.tool_results,
                    "metadata": context.metadata,
                    "active_framework": context.active_framework
                }),
                ex=7200  # 2 小時過期
            )

    async def sync_to(
        self,
        target_framework: str,
        session_id: str
    ) -> None:
        """同步上下文到目標框架"""
        context = await self.get_context(session_id)
        context.active_framework = target_framework
        await self.save_context(context)

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        framework: str,
        metadata: Dict[str, Any] = None
    ) -> None:
        """添加訊息到共享上下文"""
        import time

        context = await self.get_context(session_id)
        context.messages.append({
            "role": role,
            "content": content,
            "framework": framework,
            "timestamp": time.time(),
            "metadata": metadata or {}
        })
        await self.save_context(context)

    async def add_tool_result(
        self,
        session_id: str,
        tool_name: str,
        result: Any,
        framework: str
    ) -> None:
        """添加工具結果"""
        context = await self.get_context(session_id)
        context.tool_results.append({
            "tool_name": tool_name,
            "result": result,
            "framework": framework,
            "timestamp": time.time()
        })
        await self.save_context(context)

    async def sync_result(
        self,
        session_id: str,
        result: Any
    ) -> None:
        """同步執行結果"""
        context = await self.get_context(session_id)

        # 添加助理回應
        await self.add_message(
            session_id=session_id,
            role="assistant",
            content=result.content,
            framework=context.active_framework,
            metadata={"tokens_used": result.tokens_used}
        )

        # 添加工具結果
        for tool_call in result.tool_calls:
            await self.add_tool_result(
                session_id=session_id,
                tool_name=tool_call.get("name"),
                result=tool_call.get("result"),
                framework=context.active_framework
            )

    async def clear_context(self, session_id: str) -> None:
        """清除上下文"""
        if session_id in self._local_cache:
            del self._local_cache[session_id]

        if self._redis:
            await self._redis.delete(f"hybrid:context:{session_id}")
```

#### SharedState 實現
```python
@dataclass
class SharedState:
    """跨框架共享狀態"""
    session_id: str
    current_agent: Optional[str] = None
    workflow_status: str = "idle"
    pending_approvals: List[str] = field(default_factory=list)
    error_count: int = 0
    last_framework: str = "claude_sdk"

class StateManager:
    """狀態管理器"""

    def __init__(self, redis_client=None):
        self._redis = redis_client
        self._states: Dict[str, SharedState] = {}

    async def get_state(self, session_id: str) -> SharedState:
        """獲取共享狀態"""
        if session_id not in self._states:
            self._states[session_id] = SharedState(session_id=session_id)
        return self._states[session_id]

    async def update_state(
        self,
        session_id: str,
        **updates
    ) -> SharedState:
        """更新狀態"""
        state = await self.get_state(session_id)
        for key, value in updates.items():
            if hasattr(state, key):
                setattr(state, key, value)
        return state

    async def transition_framework(
        self,
        session_id: str,
        to_framework: str
    ) -> None:
        """記錄框架切換"""
        state = await self.get_state(session_id)
        state.last_framework = to_framework
```

### 驗收標準
- [ ] SharedContext 支援雙向格式轉換
- [ ] ContextSynchronizer 正確同步訊息歷史
- [ ] 工具結果正確記錄
- [ ] Redis 持久化正常運作
- [ ] StateManager 追蹤跨框架狀態
- [ ] 框架切換時上下文完整保留

---

## 依賴關係

```
S50-1 (MCP Server 基礎)
    ↓
S50-2 (MCP Manager) ──────┐
                          ├──→ S50-3 (Hybrid Orchestrator)
Sprint 48-49 ─────────────┘          ↓
                               S50-4 (Context Synchronizer)
```

---

## 測試計劃

### 單元測試
- `tests/unit/integrations/claude_sdk/mcp/test_stdio.py`
- `tests/unit/integrations/claude_sdk/mcp/test_http.py`
- `tests/unit/integrations/claude_sdk/mcp/test_manager.py`
- `tests/unit/integrations/claude_sdk/hybrid/test_orchestrator.py`
- `tests/unit/integrations/claude_sdk/hybrid/test_capability.py`
- `tests/unit/integrations/claude_sdk/hybrid/test_sync.py`

### 整合測試
- `tests/integration/claude_sdk/test_mcp_integration.py`
- `tests/integration/claude_sdk/test_hybrid_workflow.py`

---

## 風險與緩解

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| MCP Server 連接不穩定 | 高 | 重試機制、健康檢查 |
| 框架切換上下文丟失 | 高 | 完整的同步機制、Redis 持久化 |
| 能力分析不準確 | 中 | 可配置映射、用戶覆寫選項 |
| 效能瓶頸 | 中 | 並行連接、快取機制 |

---

## 完成定義

- [ ] 所有 Story 程式碼完成
- [ ] 單元測試覆蓋率 ≥ 85%
- [ ] 整合測試通過
- [ ] API 文檔更新
- [ ] Code Review 完成
- [ ] 無 Critical/High Bug
