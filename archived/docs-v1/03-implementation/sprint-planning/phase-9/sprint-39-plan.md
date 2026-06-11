# Sprint 39: MCP Core Framework

**Sprint 目標**: 建立 MCP (Model Context Protocol) 核心架構，為所有執行工具提供統一的基礎設施
**總點數**: 40 Story Points
**優先級**: 🔴 CRITICAL
**前置條件**: Phase 8 完成

---

## 背景

MCP (Model Context Protocol) 是由 Anthropic 提出的標準化協議，用於 AI Agent 與外部工具的交互。Microsoft Agent Framework 原生支援 MCP，這使得我們可以：

1. 使用標準化接口連接各種執行工具
2. 利用現有的 MCP Server 生態系統
3. 建立統一的權限和審計機制

### MCP 核心概念

```
┌─────────────────────────────────────────────────────────────────┐
│                     MCP Architecture                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌───────────────┐         ┌───────────────┐                    │
│  │  MCP Client   │◄───────►│  MCP Server   │                    │
│  │  (AI Agent)   │  JSON   │  (Tool Host)  │                    │
│  └───────────────┘  RPC    └───────────────┘                    │
│                                                                  │
│  Client 功能:                Server 功能:                        │
│  • 發現 Tools               • 定義 Tools                        │
│  • 調用 Tools               • 執行 Tools                        │
│  • 處理 Resources           • 提供 Resources                    │
│  • 使用 Prompts             • 定義 Prompts                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 本 Sprint 產出架構

```
backend/src/integrations/mcp/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── client.py           # MCPClient - 核心客戶端
│   ├── protocol.py         # MCP 協議實現
│   ├── transport.py        # 傳輸層 (stdio, sse, websocket)
│   └── types.py            # MCP 類型定義
│
├── registry/
│   ├── __init__.py
│   ├── server_registry.py  # MCP Server 註冊表
│   ├── tool_registry.py    # Tool 註冊表
│   └── discovery.py        # 工具發現機制
│
├── security/
│   ├── __init__.py
│   ├── permissions.py      # 權限系統
│   ├── audit.py            # 審計日誌
│   └── policies.py         # 安全策略
│
└── api/
    ├── __init__.py
    └── routes.py           # MCP 管理 API
```

---

## Story 清單

### S39-1: MCP 核心協議實現 (10 pts)

**優先級**: 🔴 P0 - CRITICAL
**類型**: 新增
**影響範圍**: `backend/src/integrations/mcp/core/`

#### 設計

```python
# 文件: backend/src/integrations/mcp/core/types.py

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from enum import Enum


class ToolInputType(str, Enum):
    """工具參數類型。"""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"


@dataclass
class ToolParameter:
    """工具參數定義。"""
    name: str
    type: ToolInputType
    description: str
    required: bool = True
    default: Any = None
    enum: Optional[List[str]] = None


@dataclass
class ToolSchema:
    """MCP 工具 Schema。

    符合 MCP 規範的工具定義格式。
    """
    name: str
    description: str
    parameters: List[ToolParameter] = field(default_factory=list)
    returns: Optional[str] = None

    def to_mcp_format(self) -> Dict[str, Any]:
        """轉換為 MCP 標準格式。"""
        properties = {}
        required = []

        for param in self.parameters:
            properties[param.name] = {
                "type": param.type.value,
                "description": param.description,
            }
            if param.enum:
                properties[param.name]["enum"] = param.enum
            if param.required:
                required.append(param.name)

        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": properties,
                "required": required,
            }
        }


@dataclass
class ToolResult:
    """工具執行結果。"""
    success: bool
    content: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_mcp_format(self) -> Dict[str, Any]:
        """轉換為 MCP 標準格式。"""
        if self.success:
            return {
                "content": [
                    {"type": "text", "text": str(self.content)}
                ]
            }
        else:
            return {
                "isError": True,
                "content": [
                    {"type": "text", "text": self.error or "Unknown error"}
                ]
            }


@dataclass
class MCPRequest:
    """MCP 請求。"""
    jsonrpc: str = "2.0"
    id: Union[str, int] = ""
    method: str = ""
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPResponse:
    """MCP 響應。"""
    jsonrpc: str = "2.0"
    id: Union[str, int] = ""
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
```

```python
# 文件: backend/src/integrations/mcp/core/protocol.py

from typing import Any, Callable, Dict, List, Optional
import json
import logging
from .types import MCPRequest, MCPResponse, ToolSchema, ToolResult

logger = logging.getLogger(__name__)


class MCPProtocol:
    """MCP 協議處理器。

    實現 MCP JSON-RPC 2.0 協議的核心邏輯。

    Supported Methods:
        - initialize: 初始化連接
        - tools/list: 列出可用工具
        - tools/call: 調用工具
        - resources/list: 列出資源
        - resources/read: 讀取資源
        - prompts/list: 列出提示模板
        - prompts/get: 獲取提示模板
    """

    MCP_VERSION = "2024-11-05"

    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._tool_schemas: Dict[str, ToolSchema] = {}
        self._initialized = False
        self._request_id = 0

    def register_tool(
        self,
        name: str,
        handler: Callable,
        schema: ToolSchema,
    ) -> None:
        """註冊工具。

        Args:
            name: 工具名稱
            handler: 工具處理函數
            schema: 工具 Schema
        """
        self._tools[name] = handler
        self._tool_schemas[name] = schema
        logger.info(f"Registered MCP tool: {name}")

    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """處理 MCP 請求。

        Args:
            request: MCP 請求

        Returns:
            MCP 響應
        """
        method = request.method
        params = request.params

        try:
            if method == "initialize":
                result = await self._handle_initialize(params)
            elif method == "tools/list":
                result = await self._handle_tools_list()
            elif method == "tools/call":
                result = await self._handle_tools_call(params)
            elif method == "ping":
                result = {}
            else:
                return MCPResponse(
                    id=request.id,
                    error={
                        "code": -32601,
                        "message": f"Method not found: {method}",
                    }
                )

            return MCPResponse(id=request.id, result=result)

        except Exception as e:
            logger.error(f"MCP request error: {e}", exc_info=True)
            return MCPResponse(
                id=request.id,
                error={
                    "code": -32603,
                    "message": str(e),
                }
            )

    async def _handle_initialize(self, params: Dict) -> Dict:
        """處理初始化請求。"""
        self._initialized = True
        return {
            "protocolVersion": self.MCP_VERSION,
            "capabilities": {
                "tools": {},
                "resources": {},
                "prompts": {},
            },
            "serverInfo": {
                "name": "ipa-platform-mcp",
                "version": "1.0.0",
            }
        }

    async def _handle_tools_list(self) -> Dict:
        """處理工具列表請求。"""
        tools = []
        for name, schema in self._tool_schemas.items():
            tools.append(schema.to_mcp_format())
        return {"tools": tools}

    async def _handle_tools_call(self, params: Dict) -> Dict:
        """處理工具調用請求。"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name not in self._tools:
            return {
                "isError": True,
                "content": [
                    {"type": "text", "text": f"Tool not found: {tool_name}"}
                ]
            }

        handler = self._tools[tool_name]
        result = await handler(**arguments)

        if isinstance(result, ToolResult):
            return result.to_mcp_format()
        else:
            return {
                "content": [
                    {"type": "text", "text": str(result)}
                ]
            }

    def create_request(
        self,
        method: str,
        params: Optional[Dict] = None,
    ) -> MCPRequest:
        """創建 MCP 請求。"""
        self._request_id += 1
        return MCPRequest(
            id=self._request_id,
            method=method,
            params=params or {},
        )
```

#### 任務清單

1. **創建 MCP 類型定義** (`types.py`)
   - ToolParameter, ToolSchema
   - ToolResult
   - MCPRequest, MCPResponse
   - 符合 MCP 規範格式

2. **實現 MCP 協議處理器** (`protocol.py`)
   - initialize 方法
   - tools/list 方法
   - tools/call 方法
   - 錯誤處理

3. **實現傳輸層** (`transport.py`)
   - StdioTransport (子進程通訊)
   - 基本的請求/響應處理

#### 驗收標準
- [ ] 類型定義符合 MCP 規範
- [ ] 協議處理器正確實現核心方法
- [ ] 單元測試覆蓋所有公開方法
- [ ] 錯誤處理完整

---

### S39-2: MCP Client 實現 (10 pts)

**優先級**: 🔴 P0 - CRITICAL
**類型**: 新增
**影響範圍**: `backend/src/integrations/mcp/core/client.py`

#### 設計

```python
# 文件: backend/src/integrations/mcp/core/client.py

from typing import Any, Dict, List, Optional, Type
import asyncio
import logging
from dataclasses import dataclass

from .protocol import MCPProtocol
from .transport import StdioTransport, BaseTransport
from .types import ToolSchema, ToolResult

logger = logging.getLogger(__name__)


@dataclass
class ServerConfig:
    """MCP Server 配置。"""
    name: str
    command: str
    args: List[str] = None
    env: Dict[str, str] = None
    transport: str = "stdio"  # stdio, sse, websocket


class MCPClient:
    """MCP 客戶端。

    管理與 MCP Server 的連接和工具調用。

    Example:
        ```python
        client = MCPClient()

        # 連接到 MCP Server
        await client.connect(ServerConfig(
            name="azure-mcp",
            command="python",
            args=["-m", "mcp_servers.azure"],
        ))

        # 列出可用工具
        tools = await client.list_tools("azure-mcp")

        # 調用工具
        result = await client.call_tool(
            server="azure-mcp",
            tool="list_vms",
            arguments={"resource_group": "prod-rg"},
        )

        # 斷開連接
        await client.disconnect("azure-mcp")
        ```
    """

    def __init__(self):
        """初始化 MCP 客戶端。"""
        self._servers: Dict[str, BaseTransport] = {}
        self._protocols: Dict[str, MCPProtocol] = {}
        self._tools: Dict[str, Dict[str, ToolSchema]] = {}

    async def connect(self, config: ServerConfig) -> bool:
        """連接到 MCP Server。

        Args:
            config: Server 配置

        Returns:
            是否連接成功
        """
        if config.name in self._servers:
            logger.warning(f"Server already connected: {config.name}")
            return True

        try:
            # 創建傳輸層
            transport = StdioTransport(
                command=config.command,
                args=config.args or [],
                env=config.env,
            )

            # 啟動 Server
            await transport.start()

            # 發送初始化請求
            protocol = MCPProtocol()
            init_request = protocol.create_request("initialize", {
                "protocolVersion": MCPProtocol.MCP_VERSION,
                "capabilities": {},
                "clientInfo": {
                    "name": "ipa-platform",
                    "version": "1.0.0",
                }
            })

            response = await transport.send(init_request)

            if response.error:
                logger.error(f"Initialize failed: {response.error}")
                await transport.stop()
                return False

            # 獲取工具列表
            tools_request = protocol.create_request("tools/list")
            tools_response = await transport.send(tools_request)

            if tools_response.result:
                self._tools[config.name] = {}
                for tool in tools_response.result.get("tools", []):
                    schema = self._parse_tool_schema(tool)
                    self._tools[config.name][schema.name] = schema

            self._servers[config.name] = transport
            self._protocols[config.name] = protocol

            logger.info(
                f"Connected to MCP Server: {config.name} "
                f"({len(self._tools.get(config.name, {}))} tools)"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to connect to {config.name}: {e}")
            return False

    async def disconnect(self, server_name: str) -> bool:
        """斷開 MCP Server 連接。

        Args:
            server_name: Server 名稱

        Returns:
            是否斷開成功
        """
        if server_name not in self._servers:
            return True

        try:
            transport = self._servers[server_name]
            await transport.stop()

            del self._servers[server_name]
            del self._protocols[server_name]
            if server_name in self._tools:
                del self._tools[server_name]

            logger.info(f"Disconnected from MCP Server: {server_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to disconnect from {server_name}: {e}")
            return False

    async def list_tools(
        self,
        server_name: Optional[str] = None,
    ) -> Dict[str, List[ToolSchema]]:
        """列出可用工具。

        Args:
            server_name: 可選的 Server 名稱過濾

        Returns:
            Server 名稱到工具列表的映射
        """
        if server_name:
            if server_name in self._tools:
                return {server_name: list(self._tools[server_name].values())}
            return {}

        return {
            name: list(tools.values())
            for name, tools in self._tools.items()
        }

    async def call_tool(
        self,
        server: str,
        tool: str,
        arguments: Dict[str, Any] = None,
    ) -> ToolResult:
        """調用工具。

        Args:
            server: Server 名稱
            tool: 工具名稱
            arguments: 工具參數

        Returns:
            工具執行結果
        """
        if server not in self._servers:
            return ToolResult(
                success=False,
                content=None,
                error=f"Server not connected: {server}",
            )

        if server not in self._tools or tool not in self._tools[server]:
            return ToolResult(
                success=False,
                content=None,
                error=f"Tool not found: {server}/{tool}",
            )

        try:
            transport = self._servers[server]
            protocol = self._protocols[server]

            request = protocol.create_request("tools/call", {
                "name": tool,
                "arguments": arguments or {},
            })

            response = await transport.send(request)

            if response.error:
                return ToolResult(
                    success=False,
                    content=None,
                    error=response.error.get("message", "Unknown error"),
                )

            result = response.result
            if result.get("isError"):
                content = result.get("content", [])
                error_text = content[0].get("text", "Unknown error") if content else "Unknown error"
                return ToolResult(
                    success=False,
                    content=None,
                    error=error_text,
                )

            content = result.get("content", [])
            text_content = content[0].get("text", "") if content else ""

            return ToolResult(
                success=True,
                content=text_content,
                metadata={"server": server, "tool": tool},
            )

        except Exception as e:
            logger.error(f"Tool call failed: {server}/{tool}: {e}")
            return ToolResult(
                success=False,
                content=None,
                error=str(e),
            )

    def _parse_tool_schema(self, tool_data: Dict) -> ToolSchema:
        """解析工具 Schema。"""
        from .types import ToolParameter, ToolInputType

        parameters = []
        input_schema = tool_data.get("inputSchema", {})
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])

        for name, prop in properties.items():
            param_type = prop.get("type", "string")
            try:
                type_enum = ToolInputType(param_type)
            except ValueError:
                type_enum = ToolInputType.STRING

            parameters.append(ToolParameter(
                name=name,
                type=type_enum,
                description=prop.get("description", ""),
                required=name in required,
                enum=prop.get("enum"),
            ))

        return ToolSchema(
            name=tool_data.get("name", ""),
            description=tool_data.get("description", ""),
            parameters=parameters,
        )

    @property
    def connected_servers(self) -> List[str]:
        """獲取已連接的 Server 列表。"""
        return list(self._servers.keys())

    async def close(self) -> None:
        """關閉所有連接。"""
        for server_name in list(self._servers.keys()):
            await self.disconnect(server_name)
```

#### 任務清單

1. **實現 ServerConfig**
   - 配置 Server 連接參數
   - 支援 stdio/sse/websocket 傳輸

2. **實現 MCPClient**
   - connect() - 連接到 Server
   - disconnect() - 斷開連接
   - list_tools() - 列出工具
   - call_tool() - 調用工具
   - 連接管理和錯誤處理

3. **實現傳輸層** (`transport.py`)
   - StdioTransport 基本實現
   - 異步請求/響應

#### 驗收標準
- [ ] MCPClient 可以連接到 MCP Server
- [ ] 工具列表正確獲取
- [ ] 工具調用正常工作
- [ ] 錯誤處理完整

---

### S39-3: MCP Server 註冊表 (8 pts)

**優先級**: 🟡 P1
**類型**: 新增
**影響範圍**: `backend/src/integrations/mcp/registry/`

#### 設計

```python
# 文件: backend/src/integrations/mcp/registry/server_registry.py

from typing import Dict, List, Optional
from dataclasses import dataclass, field
import logging
import yaml
from pathlib import Path

from ..core.client import ServerConfig, MCPClient

logger = logging.getLogger(__name__)


@dataclass
class ServerMetadata:
    """MCP Server 元數據。"""
    name: str
    description: str
    version: str
    category: str  # azure, shell, filesystem, database, etc.
    risk_level: int = 1  # 1=低, 2=中, 3=高
    enabled: bool = True
    config: ServerConfig = None


class MCPServerRegistry:
    """MCP Server 註冊表。

    管理所有可用的 MCP Server 配置和狀態。

    Example:
        ```python
        registry = MCPServerRegistry()

        # 載入配置
        registry.load_from_yaml("config/mcp-servers.yaml")

        # 獲取 Server 列表
        servers = registry.list_servers()

        # 獲取特定類別的 Server
        azure_servers = registry.get_servers_by_category("azure")

        # 啟用/禁用 Server
        registry.set_enabled("azure-mcp", True)
        ```
    """

    def __init__(self):
        """初始化註冊表。"""
        self._servers: Dict[str, ServerMetadata] = {}
        self._client: Optional[MCPClient] = None

    def register(self, metadata: ServerMetadata) -> None:
        """註冊 MCP Server。

        Args:
            metadata: Server 元數據
        """
        self._servers[metadata.name] = metadata
        logger.info(f"Registered MCP Server: {metadata.name}")

    def unregister(self, name: str) -> bool:
        """取消註冊 MCP Server。

        Args:
            name: Server 名稱

        Returns:
            是否成功取消
        """
        if name in self._servers:
            del self._servers[name]
            logger.info(f"Unregistered MCP Server: {name}")
            return True
        return False

    def get(self, name: str) -> Optional[ServerMetadata]:
        """獲取 Server 元數據。

        Args:
            name: Server 名稱

        Returns:
            Server 元數據或 None
        """
        return self._servers.get(name)

    def list_servers(
        self,
        enabled_only: bool = True,
    ) -> List[ServerMetadata]:
        """列出所有 Server。

        Args:
            enabled_only: 是否只返回啟用的 Server

        Returns:
            Server 列表
        """
        servers = list(self._servers.values())
        if enabled_only:
            servers = [s for s in servers if s.enabled]
        return servers

    def get_servers_by_category(
        self,
        category: str,
        enabled_only: bool = True,
    ) -> List[ServerMetadata]:
        """按類別獲取 Server。

        Args:
            category: 類別名稱
            enabled_only: 是否只返回啟用的 Server

        Returns:
            符合條件的 Server 列表
        """
        servers = self.list_servers(enabled_only)
        return [s for s in servers if s.category == category]

    def get_servers_by_risk_level(
        self,
        max_level: int = 3,
        enabled_only: bool = True,
    ) -> List[ServerMetadata]:
        """按風險等級獲取 Server。

        Args:
            max_level: 最大風險等級
            enabled_only: 是否只返回啟用的 Server

        Returns:
            符合條件的 Server 列表
        """
        servers = self.list_servers(enabled_only)
        return [s for s in servers if s.risk_level <= max_level]

    def set_enabled(self, name: str, enabled: bool) -> bool:
        """設置 Server 啟用狀態。

        Args:
            name: Server 名稱
            enabled: 是否啟用

        Returns:
            是否成功設置
        """
        if name in self._servers:
            self._servers[name].enabled = enabled
            return True
        return False

    def load_from_yaml(self, path: str) -> int:
        """從 YAML 文件載入配置。

        Args:
            path: YAML 文件路徑

        Returns:
            載入的 Server 數量
        """
        config_path = Path(path)
        if not config_path.exists():
            logger.warning(f"Config file not found: {path}")
            return 0

        with open(config_path) as f:
            config = yaml.safe_load(f)

        count = 0
        for server_config in config.get("servers", []):
            try:
                metadata = ServerMetadata(
                    name=server_config["name"],
                    description=server_config.get("description", ""),
                    version=server_config.get("version", "1.0.0"),
                    category=server_config.get("category", "general"),
                    risk_level=server_config.get("risk_level", 1),
                    enabled=server_config.get("enabled", True),
                    config=ServerConfig(
                        name=server_config["name"],
                        command=server_config["command"],
                        args=server_config.get("args", []),
                        env=server_config.get("env", {}),
                        transport=server_config.get("transport", "stdio"),
                    ),
                )
                self.register(metadata)
                count += 1
            except Exception as e:
                logger.error(f"Failed to load server config: {e}")

        return count

    def save_to_yaml(self, path: str) -> bool:
        """保存配置到 YAML 文件。

        Args:
            path: YAML 文件路徑

        Returns:
            是否成功保存
        """
        servers = []
        for metadata in self._servers.values():
            server_dict = {
                "name": metadata.name,
                "description": metadata.description,
                "version": metadata.version,
                "category": metadata.category,
                "risk_level": metadata.risk_level,
                "enabled": metadata.enabled,
            }
            if metadata.config:
                server_dict["command"] = metadata.config.command
                server_dict["args"] = metadata.config.args
                server_dict["env"] = metadata.config.env
                server_dict["transport"] = metadata.config.transport
            servers.append(server_dict)

        config = {"servers": servers}

        with open(path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)

        return True
```

#### 配置文件示例

```yaml
# config/mcp-servers.yaml
servers:
  - name: azure-mcp
    description: Azure 資源管理工具
    version: 1.0.0
    category: azure
    risk_level: 2
    enabled: true
    command: python
    args: ["-m", "mcp_servers.azure"]
    env:
      AZURE_SUBSCRIPTION_ID: "${AZURE_SUBSCRIPTION_ID}"
    transport: stdio

  - name: shell-mcp
    description: Shell 命令執行工具
    version: 1.0.0
    category: shell
    risk_level: 3
    enabled: true
    command: python
    args: ["-m", "mcp_servers.shell"]
    transport: stdio

  - name: filesystem-mcp
    description: 文件系統操作工具
    version: 1.0.0
    category: filesystem
    risk_level: 2
    enabled: true
    command: python
    args: ["-m", "mcp_servers.filesystem"]
    transport: stdio
```

#### 任務清單

1. **實現 ServerMetadata**
   - Server 描述信息
   - 風險等級
   - 啟用狀態

2. **實現 MCPServerRegistry**
   - register() / unregister()
   - list_servers()
   - get_servers_by_category()
   - get_servers_by_risk_level()

3. **YAML 配置支援**
   - load_from_yaml()
   - save_to_yaml()

4. **創建預設配置**
   - `config/mcp-servers.yaml`

#### 驗收標準
- [ ] Server 註冊和查詢正常工作
- [ ] YAML 配置載入成功
- [ ] 風險等級過濾正確

---

### S39-4: 權限與審計系統 (8 pts)

**優先級**: 🟡 P1
**類型**: 新增
**影響範圍**: `backend/src/integrations/mcp/security/`

#### 設計

```python
# 文件: backend/src/integrations/mcp/security/permissions.py

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RiskLevel(int, Enum):
    """風險等級。"""
    LOW = 1       # 只讀操作
    MEDIUM = 2    # 低風險寫操作
    HIGH = 3      # 高風險操作


class ApprovalRequirement(str, Enum):
    """審批需求。"""
    NONE = "none"           # 自動執行
    AGENT = "agent"         # Agent 確認
    HUMAN = "human"         # 人工審批


@dataclass
class ToolPermission:
    """工具權限定義。"""
    server: str
    tool: str
    risk_level: RiskLevel = RiskLevel.LOW
    approval_required: ApprovalRequirement = ApprovalRequirement.NONE
    allowed_roles: Set[str] = field(default_factory=set)
    denied_roles: Set[str] = field(default_factory=set)
    conditions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PermissionCheckResult:
    """權限檢查結果。"""
    allowed: bool
    approval_required: ApprovalRequirement
    reason: Optional[str] = None


class MCPPermissionManager:
    """MCP 權限管理器。

    管理工具調用的權限和審批流程。

    Example:
        ```python
        manager = MCPPermissionManager()

        # 設置工具權限
        manager.set_permission(ToolPermission(
            server="shell-mcp",
            tool="execute_command",
            risk_level=RiskLevel.HIGH,
            approval_required=ApprovalRequirement.HUMAN,
        ))

        # 檢查權限
        result = manager.check_permission(
            server="shell-mcp",
            tool="execute_command",
            user_roles={"admin"},
            context={"command": "rm -rf"},
        )

        if not result.allowed:
            print(f"Permission denied: {result.reason}")
        elif result.approval_required == ApprovalRequirement.HUMAN:
            print("Human approval required")
        ```
    """

    def __init__(self):
        """初始化權限管理器。"""
        self._permissions: Dict[str, ToolPermission] = {}
        self._default_policies: Dict[RiskLevel, ApprovalRequirement] = {
            RiskLevel.LOW: ApprovalRequirement.NONE,
            RiskLevel.MEDIUM: ApprovalRequirement.AGENT,
            RiskLevel.HIGH: ApprovalRequirement.HUMAN,
        }

    def set_permission(self, permission: ToolPermission) -> None:
        """設置工具權限。

        Args:
            permission: 權限定義
        """
        key = f"{permission.server}/{permission.tool}"
        self._permissions[key] = permission
        logger.info(f"Set permission for {key}: {permission.approval_required}")

    def get_permission(
        self,
        server: str,
        tool: str,
    ) -> Optional[ToolPermission]:
        """獲取工具權限。

        Args:
            server: Server 名稱
            tool: 工具名稱

        Returns:
            權限定義或 None
        """
        key = f"{server}/{tool}"
        return self._permissions.get(key)

    def check_permission(
        self,
        server: str,
        tool: str,
        user_roles: Set[str] = None,
        context: Dict[str, Any] = None,
    ) -> PermissionCheckResult:
        """檢查權限。

        Args:
            server: Server 名稱
            tool: 工具名稱
            user_roles: 用戶角色
            context: 調用上下文

        Returns:
            權限檢查結果
        """
        user_roles = user_roles or set()
        context = context or {}

        permission = self.get_permission(server, tool)

        if permission is None:
            # 沒有特定權限設置，使用預設策略
            return PermissionCheckResult(
                allowed=True,
                approval_required=ApprovalRequirement.AGENT,
                reason="No specific permission, using default policy",
            )

        # 檢查角色
        if permission.denied_roles & user_roles:
            return PermissionCheckResult(
                allowed=False,
                approval_required=ApprovalRequirement.NONE,
                reason="Role is denied",
            )

        if permission.allowed_roles and not (permission.allowed_roles & user_roles):
            return PermissionCheckResult(
                allowed=False,
                approval_required=ApprovalRequirement.NONE,
                reason="Role not in allowed list",
            )

        # 檢查條件
        for condition_key, condition_value in permission.conditions.items():
            if condition_key in context:
                if not self._check_condition(
                    context[condition_key],
                    condition_value,
                ):
                    return PermissionCheckResult(
                        allowed=False,
                        approval_required=ApprovalRequirement.NONE,
                        reason=f"Condition not met: {condition_key}",
                    )

        return PermissionCheckResult(
            allowed=True,
            approval_required=permission.approval_required,
        )

    def _check_condition(self, value: Any, condition: Any) -> bool:
        """檢查條件。"""
        if isinstance(condition, dict):
            if "not_contains" in condition:
                return condition["not_contains"] not in str(value)
            if "contains" in condition:
                return condition["contains"] in str(value)
            if "max_length" in condition:
                return len(str(value)) <= condition["max_length"]
        return True

    def set_default_policy(
        self,
        risk_level: RiskLevel,
        approval: ApprovalRequirement,
    ) -> None:
        """設置預設策略。

        Args:
            risk_level: 風險等級
            approval: 審批需求
        """
        self._default_policies[risk_level] = approval
```

```python
# 文件: backend/src/integrations/mcp/security/audit.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import json
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class AuditEventType(str, Enum):
    """審計事件類型。"""
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    PERMISSION_CHECK = "permission_check"
    APPROVAL_REQUEST = "approval_request"
    APPROVAL_RESPONSE = "approval_response"
    ERROR = "error"


@dataclass
class AuditEvent:
    """審計事件。"""
    id: str
    timestamp: datetime
    event_type: AuditEventType
    server: str
    tool: str
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    workflow_id: Optional[str] = None
    arguments: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Any] = None
    success: bool = True
    error: Optional[str] = None
    risk_level: int = 1
    approval_status: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class MCPAuditLogger:
    """MCP 審計日誌記錄器。

    記錄所有 MCP 工具調用和結果，用於審計和問題追蹤。

    Example:
        ```python
        audit = MCPAuditLogger()

        # 記錄工具調用
        event = audit.log_tool_call(
            server="azure-mcp",
            tool="list_vms",
            arguments={"resource_group": "prod-rg"},
            user_id="user-123",
            agent_id="agent-456",
        )

        # 記錄結果
        audit.log_tool_result(
            event_id=event.id,
            success=True,
            result={"vms": [...]},
        )

        # 查詢審計記錄
        events = audit.query(
            server="azure-mcp",
            start_time=datetime.now() - timedelta(hours=24),
        )
        ```
    """

    def __init__(self, storage_backend: str = "memory"):
        """初始化審計記錄器。

        Args:
            storage_backend: 存儲後端 (memory, database, file)
        """
        self._events: List[AuditEvent] = []
        self._event_counter = 0
        self._storage_backend = storage_backend

    def log_tool_call(
        self,
        server: str,
        tool: str,
        arguments: Dict[str, Any],
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        risk_level: int = 1,
    ) -> AuditEvent:
        """記錄工具調用。

        Args:
            server: Server 名稱
            tool: 工具名稱
            arguments: 調用參數
            user_id: 用戶 ID
            agent_id: Agent ID
            workflow_id: 工作流 ID
            risk_level: 風險等級

        Returns:
            審計事件
        """
        self._event_counter += 1
        event = AuditEvent(
            id=f"audit-{self._event_counter}",
            timestamp=datetime.utcnow(),
            event_type=AuditEventType.TOOL_CALL,
            server=server,
            tool=tool,
            user_id=user_id,
            agent_id=agent_id,
            workflow_id=workflow_id,
            arguments=self._sanitize_arguments(arguments),
            risk_level=risk_level,
        )

        self._events.append(event)
        logger.info(
            f"AUDIT: {event.event_type.value} - "
            f"{server}/{tool} by {user_id or agent_id}"
        )

        return event

    def log_tool_result(
        self,
        event_id: str,
        success: bool,
        result: Any = None,
        error: Optional[str] = None,
    ) -> Optional[AuditEvent]:
        """記錄工具結果。

        Args:
            event_id: 對應的調用事件 ID
            success: 是否成功
            result: 執行結果
            error: 錯誤信息

        Returns:
            更新後的審計事件
        """
        for event in self._events:
            if event.id == event_id:
                event.success = success
                event.result = result
                event.error = error

                # 創建結果事件
                self._event_counter += 1
                result_event = AuditEvent(
                    id=f"audit-{self._event_counter}",
                    timestamp=datetime.utcnow(),
                    event_type=AuditEventType.TOOL_RESULT,
                    server=event.server,
                    tool=event.tool,
                    user_id=event.user_id,
                    agent_id=event.agent_id,
                    workflow_id=event.workflow_id,
                    success=success,
                    result=result,
                    error=error,
                    metadata={"original_event_id": event_id},
                )
                self._events.append(result_event)

                return result_event

        return None

    def log_permission_check(
        self,
        server: str,
        tool: str,
        allowed: bool,
        reason: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> AuditEvent:
        """記錄權限檢查。"""
        self._event_counter += 1
        event = AuditEvent(
            id=f"audit-{self._event_counter}",
            timestamp=datetime.utcnow(),
            event_type=AuditEventType.PERMISSION_CHECK,
            server=server,
            tool=tool,
            user_id=user_id,
            success=allowed,
            error=reason if not allowed else None,
        )
        self._events.append(event)
        return event

    def query(
        self,
        server: Optional[str] = None,
        tool: Optional[str] = None,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[AuditEvent]:
        """查詢審計記錄。

        Args:
            各種過濾條件
            limit: 最大返回數量

        Returns:
            符合條件的審計事件列表
        """
        results = []

        for event in reversed(self._events):
            if len(results) >= limit:
                break

            if server and event.server != server:
                continue
            if tool and event.tool != tool:
                continue
            if user_id and event.user_id != user_id:
                continue
            if agent_id and event.agent_id != agent_id:
                continue
            if workflow_id and event.workflow_id != workflow_id:
                continue
            if event_type and event.event_type != event_type:
                continue
            if start_time and event.timestamp < start_time:
                continue
            if end_time and event.timestamp > end_time:
                continue

            results.append(event)

        return results

    def _sanitize_arguments(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """清理敏感參數。"""
        sanitized = {}
        sensitive_keys = {"password", "secret", "token", "key", "credential"}

        for key, value in arguments.items():
            if any(s in key.lower() for s in sensitive_keys):
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = value

        return sanitized
```

#### 任務清單

1. **實現權限系統** (`permissions.py`)
   - RiskLevel 枚舉
   - ApprovalRequirement 枚舉
   - ToolPermission 數據類
   - MCPPermissionManager

2. **實現審計日誌** (`audit.py`)
   - AuditEvent 數據類
   - MCPAuditLogger
   - 敏感信息過濾

3. **整合到 MCPClient**
   - 調用前權限檢查
   - 調用後審計記錄

#### 驗收標準
- [ ] 權限檢查正確執行
- [ ] 審計日誌完整記錄
- [ ] 敏感信息被過濾

---

### S39-5: MCP 管理 API (4 pts)

**優先級**: 🟢 P2
**類型**: 新增
**影響範圍**: `backend/src/api/v1/mcp/`

#### 設計

```python
# 文件: backend/src/api/v1/mcp/routes.py

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/mcp", tags=["MCP"])


class ServerStatusResponse(BaseModel):
    """Server 狀態響應。"""
    name: str
    connected: bool
    tools_count: int
    category: str
    risk_level: int


class ToolListResponse(BaseModel):
    """工具列表響應。"""
    server: str
    tools: List[dict]


@router.get("/servers", response_model=List[ServerStatusResponse])
async def list_servers():
    """列出所有 MCP Server。"""
    registry = get_registry()
    client = get_client()

    servers = []
    for metadata in registry.list_servers():
        servers.append(ServerStatusResponse(
            name=metadata.name,
            connected=metadata.name in client.connected_servers,
            tools_count=len(client._tools.get(metadata.name, {})),
            category=metadata.category,
            risk_level=metadata.risk_level,
        ))

    return servers


@router.post("/servers/{name}/connect")
async def connect_server(name: str):
    """連接 MCP Server。"""
    registry = get_registry()
    client = get_client()

    metadata = registry.get(name)
    if not metadata:
        raise HTTPException(404, f"Server not found: {name}")

    success = await client.connect(metadata.config)
    if not success:
        raise HTTPException(500, f"Failed to connect to {name}")

    return {"message": f"Connected to {name}"}


@router.post("/servers/{name}/disconnect")
async def disconnect_server(name: str):
    """斷開 MCP Server。"""
    client = get_client()

    success = await client.disconnect(name)
    if not success:
        raise HTTPException(500, f"Failed to disconnect from {name}")

    return {"message": f"Disconnected from {name}"}


@router.get("/servers/{name}/tools", response_model=ToolListResponse)
async def list_tools(name: str):
    """列出 Server 的工具。"""
    client = get_client()

    if name not in client.connected_servers:
        raise HTTPException(400, f"Server not connected: {name}")

    tools = await client.list_tools(name)

    return ToolListResponse(
        server=name,
        tools=[t.to_mcp_format() for t in tools.get(name, [])],
    )


@router.get("/audit")
async def query_audit(
    server: Optional[str] = None,
    tool: Optional[str] = None,
    limit: int = 100,
):
    """查詢審計日誌。"""
    audit = get_audit_logger()

    events = audit.query(
        server=server,
        tool=tool,
        limit=limit,
    )

    return {
        "events": [
            {
                "id": e.id,
                "timestamp": e.timestamp.isoformat(),
                "event_type": e.event_type.value,
                "server": e.server,
                "tool": e.tool,
                "success": e.success,
            }
            for e in events
        ]
    }
```

#### 任務清單

1. **實現 MCP 管理 API**
   - `GET /mcp/servers` - 列出 Server
   - `POST /mcp/servers/{name}/connect` - 連接
   - `POST /mcp/servers/{name}/disconnect` - 斷開
   - `GET /mcp/servers/{name}/tools` - 列出工具
   - `GET /mcp/audit` - 查詢審計日誌

2. **添加到路由**
   - 更新 `api/v1/__init__.py`

#### 驗收標準
- [ ] API 端點正常工作
- [ ] 返回格式符合規範

---

## 驗證命令

```bash
# 1. 語法檢查
cd backend
python -m py_compile src/integrations/mcp/core/types.py
python -m py_compile src/integrations/mcp/core/protocol.py
python -m py_compile src/integrations/mcp/core/client.py
python -m py_compile src/integrations/mcp/registry/server_registry.py
python -m py_compile src/integrations/mcp/security/permissions.py
python -m py_compile src/integrations/mcp/security/audit.py

# 2. 運行測試
pytest tests/unit/integrations/mcp/ -v --cov

# 3. API 測試
# 列出 Server
curl http://localhost:8000/api/v1/mcp/servers

# 連接 Server
curl -X POST http://localhost:8000/api/v1/mcp/servers/azure-mcp/connect

# 列出工具
curl http://localhost:8000/api/v1/mcp/servers/azure-mcp/tools

# 4. 類型檢查
mypy src/integrations/mcp/
```

---

## 完成定義

- [ ] 所有 S39 Story 完成
- [ ] MCP 核心協議實現完成
- [ ] MCPClient 可以連接和調用工具
- [ ] Server 註冊表功能完整
- [ ] 權限和審計系統運作正常
- [ ] 管理 API 可用
- [ ] 測試覆蓋率 > 85%

---

**創建日期**: 2025-12-22
