# Sprint 48: Core SDK Integration - Claude Agent SDK 核心整合

**Sprint 目標**: 實現 Claude Agent SDK 核心功能，包含 ClaudeSDKClient、query() API 和 Session 管理
**週期**: Week 1-2 (2 週)
**Story Points**: 35 點
**MVP 功能**: F12 - Claude Agent SDK 基礎整合

---

## Sprint 概覽

### 目標

1. **ClaudeSDKClient 封裝** - 封裝 Anthropic Claude SDK，提供統一的客戶端介面
2. **One-shot Query API** - 實現單次查詢功能，支援工具選擇和工作目錄設定
3. **Session 管理** - 多輪對話 Session 建立、維護和關閉
4. **配置管理** - API Key、模型選擇、Token 限制等配置

### 成功標準

- [ ] ClaudeSDKClient 可正常初始化並連接 Anthropic API
- [ ] query() 函數可執行單次任務並返回結果
- [ ] Session 可維持多輪對話上下文
- [ ] 單元測試覆蓋率 ≥ 85%
- [ ] 與現有 SessionService 整合驗證通過

---

## 架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                   Claude SDK Integration                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              ClaudeSDKClient                         │    │
│  │                                                      │    │
│  │  ┌──────────────┐  ┌──────────────┐                 │    │
│  │  │   query()    │  │ Session Mgmt │                 │    │
│  │  │              │  │              │                 │    │
│  │  │ - prompt     │  │ - create     │                 │    │
│  │  │ - tools      │  │ - query      │                 │    │
│  │  │ - timeout    │  │ - history    │                 │    │
│  │  │ - hooks      │  │ - fork       │                 │    │
│  │  └──────────────┘  └──────────────┘                 │    │
│  │                                                      │    │
│  │  ┌──────────────────────────────────────────────┐   │    │
│  │  │              Configuration                    │   │    │
│  │  │                                              │   │    │
│  │  │  - api_key        - max_tokens               │   │    │
│  │  │  - model          - timeout                  │   │    │
│  │  │  - base_url       - system_prompt            │   │    │
│  │  └──────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────┘    │
│                            │                                 │
│                            ▼                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Anthropic API Client                    │    │
│  │                                                      │    │
│  │  - Messages API                                      │    │
│  │  - Tool Use API                                      │    │
│  │  - Streaming Support                                 │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## User Stories

### S48-1: ClaudeSDKClient 核心封裝 (10 點)

**描述**: 建立 ClaudeSDKClient 類別，封裝 Anthropic Python SDK，提供統一的初始化和配置介面。

**驗收標準**:
- [ ] ClaudeSDKClient 可透過 API Key 初始化
- [ ] 支援模型選擇 (claude-sonnet-4, claude-opus-4, etc.)
- [ ] 支援自訂 system_prompt
- [ ] 支援 max_tokens 和 timeout 配置
- [ ] 配置可從環境變數或配置檔案讀取
- [ ] 錯誤處理完善 (AuthenticationError, RateLimitError, etc.)

**技術任務**:

1. **建立 ClaudeSDKClient 類別 (`backend/src/integrations/claude_sdk/client.py`)**

```python
"""Claude Agent SDK Client wrapper."""

import os
from typing import Optional, List, Any, Dict
from dataclasses import dataclass, field

import anthropic
from anthropic import Anthropic, AsyncAnthropic

from .config import ClaudeSDKConfig
from .exceptions import (
    ClaudeSDKError,
    AuthenticationError,
    RateLimitError,
    TimeoutError,
)


@dataclass
class ClaudeSDKConfig:
    """Configuration for Claude SDK Client."""

    api_key: Optional[str] = None
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096
    timeout: int = 300
    system_prompt: Optional[str] = None
    base_url: Optional[str] = None

    def __post_init__(self):
        if self.api_key is None:
            self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise AuthenticationError("ANTHROPIC_API_KEY not configured")


class ClaudeSDKClient:
    """
    Claude Agent SDK Client for autonomous AI agent operations.

    Provides both one-shot query() and multi-turn session management.

    Example:
        # One-shot query
        result = await client.query("Analyze this code", tools=["Read", "Grep"])

        # Multi-turn session
        session = await client.create_session()
        await session.query("Read the auth module")
        await session.query("What issues do you see?")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 4096,
        timeout: int = 300,
        system_prompt: Optional[str] = None,
        tools: Optional[List[str]] = None,
        hooks: Optional[List["Hook"]] = None,
        mcp_servers: Optional[List["MCPServer"]] = None,
    ):
        """
        Initialize Claude SDK Client.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Model to use (default: claude-sonnet-4-20250514)
            max_tokens: Maximum tokens per response
            timeout: Request timeout in seconds
            system_prompt: System prompt for all queries
            tools: List of built-in tools to enable
            hooks: List of Hook instances for behavior interception
            mcp_servers: List of MCP servers to connect
        """
        self.config = ClaudeSDKConfig(
            api_key=api_key,
            model=model,
            max_tokens=max_tokens,
            timeout=timeout,
            system_prompt=system_prompt,
        )

        self._client = AsyncAnthropic(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            timeout=self.config.timeout,
        )

        self.tools = tools or []
        self.hooks = hooks or []
        self.mcp_servers = mcp_servers or []
        self._sessions: Dict[str, "Session"] = {}

    async def query(
        self,
        prompt: str,
        tools: Optional[List[str]] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None,
        working_directory: Optional[str] = None,
    ) -> "QueryResult":
        """
        Execute a one-shot autonomous task.

        Args:
            prompt: Task description
            tools: Override default tools for this query
            max_tokens: Override default max_tokens
            timeout: Override default timeout
            working_directory: Set working directory for file operations

        Returns:
            QueryResult with content, tool_calls, and metadata
        """
        from .query import execute_query

        return await execute_query(
            client=self._client,
            config=self.config,
            prompt=prompt,
            tools=tools or self.tools,
            max_tokens=max_tokens or self.config.max_tokens,
            timeout=timeout or self.config.timeout,
            working_directory=working_directory,
            hooks=self.hooks,
            mcp_servers=self.mcp_servers,
        )

    async def create_session(
        self,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        history: Optional[List["Message"]] = None,
    ) -> "Session":
        """
        Create a new multi-turn conversation session.

        Args:
            session_id: Custom session identifier
            context: Initial context variables
            history: Pre-load conversation history

        Returns:
            Session instance for multi-turn interactions
        """
        from .session import Session
        import uuid

        sid = session_id or str(uuid.uuid4())
        session = Session(
            session_id=sid,
            client=self._client,
            config=self.config,
            tools=self.tools,
            hooks=self.hooks,
            mcp_servers=self.mcp_servers,
            context=context,
            history=history,
        )

        self._sessions[sid] = session

        # Trigger session start hooks
        for hook in self.hooks:
            await hook.on_session_start(sid)

        return session

    async def resume_session(self, session_id: str) -> "Session":
        """Resume an existing session by ID."""
        if session_id not in self._sessions:
            raise ClaudeSDKError(f"Session {session_id} not found")
        return self._sessions[session_id]

    async def close(self):
        """Close client and all sessions."""
        for session in self._sessions.values():
            await session.close()
        self._sessions.clear()
        await self._client.close()
```

2. **建立配置模組 (`backend/src/integrations/claude_sdk/config.py`)**

```python
"""Claude SDK configuration management."""

import os
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import yaml


@dataclass
class ClaudeSDKConfig:
    """Configuration for Claude SDK."""

    # API Configuration
    api_key: Optional[str] = None
    base_url: Optional[str] = None

    # Model Configuration
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096
    timeout: int = 300

    # Agent Configuration
    system_prompt: Optional[str] = None
    tools: List[str] = field(default_factory=list)

    # Bash Security
    allowed_commands: List[str] = field(default_factory=list)
    denied_commands: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate and apply defaults."""
        if self.api_key is None:
            self.api_key = os.getenv("ANTHROPIC_API_KEY")

        # Default denied commands for security
        if not self.denied_commands:
            self.denied_commands = [
                "rm -rf /",
                "sudo rm",
                ":(){ :|:& };:",  # Fork bomb
                "curl | bash",
                "wget | sh",
            ]

    @classmethod
    def from_env(cls) -> "ClaudeSDKConfig":
        """Create config from environment variables."""
        return cls(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model=os.getenv("CLAUDE_SDK_MODEL", "claude-sonnet-4-20250514"),
            max_tokens=int(os.getenv("CLAUDE_SDK_MAX_TOKENS", "4096")),
            timeout=int(os.getenv("CLAUDE_SDK_TIMEOUT", "300")),
        )

    @classmethod
    def from_yaml(cls, path: str) -> "ClaudeSDKConfig":
        """Create config from YAML file."""
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
            "system_prompt": self.system_prompt,
            "tools": self.tools,
        }
```

3. **建立異常類別 (`backend/src/integrations/claude_sdk/exceptions.py`)**

```python
"""Claude SDK exception classes."""

from typing import Optional, Dict, Any


class ClaudeSDKError(Exception):
    """Base exception for Claude SDK."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class AuthenticationError(ClaudeSDKError):
    """Raised when API authentication fails."""
    pass


class RateLimitError(ClaudeSDKError):
    """Raised when API rate limit is exceeded."""

    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


class TimeoutError(ClaudeSDKError):
    """Raised when operation times out."""
    pass


class ToolError(ClaudeSDKError):
    """Raised when a tool execution fails."""

    def __init__(
        self,
        message: str,
        tool_name: str,
        args: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.tool_name = tool_name
        self.args = args or {}


class HookRejectionError(ClaudeSDKError):
    """Raised when a hook rejects an operation."""

    def __init__(self, message: str, hook_name: str):
        super().__init__(message)
        self.hook_name = hook_name


class MCPError(ClaudeSDKError):
    """Base exception for MCP operations."""
    pass


class MCPConnectionError(MCPError):
    """Raised when MCP server connection fails."""

    def __init__(self, message: str, server_name: str, command: Optional[str] = None):
        super().__init__(message)
        self.server_name = server_name
        self.command = command


class MCPToolError(MCPError):
    """Raised when an MCP tool execution fails."""

    def __init__(self, message: str, server_name: str, tool_name: str):
        super().__init__(message)
        self.server_name = server_name
        self.tool_name = tool_name
```

---

### S48-2: Query API 實現 (8 點)

**描述**: 實現 query() 函數，支援單次任務執行、工具選擇和結果返回。

**驗收標準**:
- [ ] query() 可接受 prompt 並返回結果
- [ ] 支援 tools 參數指定可用工具
- [ ] 支援 working_directory 設定
- [ ] 返回 QueryResult 包含 content、tool_calls、tokens_used
- [ ] 支援 timeout 設定
- [ ] 錯誤處理完善

**技術任務**:

1. **建立 Query 執行器 (`backend/src/integrations/claude_sdk/query.py`)**

```python
"""One-shot query execution for Claude SDK."""

import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from anthropic import AsyncAnthropic

from .config import ClaudeSDKConfig
from .types import QueryResult, ToolCall
from .tools import get_tool_definitions, execute_tool
from .exceptions import TimeoutError, ToolError


@dataclass
class QueryResult:
    """Result of a one-shot query."""

    content: str
    tool_calls: List[ToolCall]
    tokens_used: int
    duration: float
    status: str  # 'success', 'error', 'timeout'
    error: Optional[str] = None

    @property
    def successful(self) -> bool:
        return self.status == "success"


async def execute_query(
    client: AsyncAnthropic,
    config: ClaudeSDKConfig,
    prompt: str,
    tools: List[str],
    max_tokens: int,
    timeout: int,
    working_directory: Optional[str],
    hooks: List["Hook"],
    mcp_servers: List["MCPServer"],
) -> QueryResult:
    """
    Execute a one-shot autonomous query.

    Args:
        client: Anthropic client instance
        config: SDK configuration
        prompt: Task description
        tools: List of enabled tool names
        max_tokens: Maximum response tokens
        timeout: Timeout in seconds
        working_directory: Working directory for file operations
        hooks: List of hooks for interception
        mcp_servers: List of MCP servers

    Returns:
        QueryResult with response and metadata
    """
    start_time = time.time()
    tool_calls: List[ToolCall] = []
    total_tokens = 0

    try:
        # Get tool definitions for enabled tools
        tool_definitions = get_tool_definitions(tools, mcp_servers)

        # Build messages
        messages = [{"role": "user", "content": prompt}]

        # Agentic loop - continue until task complete
        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise TimeoutError(f"Query exceeded timeout of {timeout}s")

            # Call Claude API
            response = await client.messages.create(
                model=config.model,
                max_tokens=max_tokens,
                system=config.system_prompt or "",
                messages=messages,
                tools=tool_definitions if tool_definitions else None,
            )

            total_tokens += response.usage.input_tokens + response.usage.output_tokens

            # Check for tool use
            has_tool_use = any(
                block.type == "tool_use" for block in response.content
            )

            if not has_tool_use:
                # No tool use - extract final response
                final_content = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        final_content += block.text

                return QueryResult(
                    content=final_content,
                    tool_calls=tool_calls,
                    tokens_used=total_tokens,
                    duration=time.time() - start_time,
                    status="success",
                )

            # Process tool calls
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tool_call = ToolCall(
                        id=block.id,
                        name=block.name,
                        args=block.input,
                    )
                    tool_calls.append(tool_call)

                    # Execute hook checks
                    for hook in hooks:
                        hook_result = await hook.on_tool_call(
                            ToolCallContext(
                                tool_name=block.name,
                                args=block.input,
                                session_id=None,
                            )
                        )
                        if hook_result.is_rejected:
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": f"Rejected: {hook_result.reason}",
                                "is_error": True,
                            })
                            continue

                    # Execute tool
                    try:
                        result = await execute_tool(
                            tool_name=block.name,
                            args=block.input,
                            working_directory=working_directory,
                            mcp_servers=mcp_servers,
                        )
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })

                        # Trigger tool result hooks
                        for hook in hooks:
                            await hook.on_tool_result(
                                ToolResultContext(
                                    tool_name=block.name,
                                    result=result,
                                    success=True,
                                )
                            )

                    except Exception as e:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": f"Error: {str(e)}",
                            "is_error": True,
                        })

            # Add assistant response and tool results to messages
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

    except TimeoutError:
        return QueryResult(
            content="",
            tool_calls=tool_calls,
            tokens_used=total_tokens,
            duration=time.time() - start_time,
            status="timeout",
            error="Query timed out",
        )

    except Exception as e:
        return QueryResult(
            content="",
            tool_calls=tool_calls,
            tokens_used=total_tokens,
            duration=time.time() - start_time,
            status="error",
            error=str(e),
        )
```

2. **建立型別定義 (`backend/src/integrations/claude_sdk/types.py`)**

```python
"""Type definitions for Claude SDK."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


@dataclass
class ToolCall:
    """Represents a single tool invocation."""

    id: str
    name: str
    args: Dict[str, Any]
    result: Optional[str] = None
    success: bool = True
    duration: Optional[float] = None


@dataclass
class Message:
    """Represents a conversation message."""

    role: str  # 'user', 'assistant'
    content: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    timestamp: Optional[float] = None


@dataclass
class ToolCallContext:
    """Context passed to hooks for tool call interception."""

    tool_name: str
    args: Dict[str, Any]
    session_id: Optional[str] = None
    tool_source: str = "builtin"  # 'builtin' or 'mcp'
    mcp_server: Optional[str] = None


@dataclass
class ToolResultContext:
    """Context passed to hooks after tool execution."""

    tool_name: str
    result: str
    success: bool
    session_id: Optional[str] = None
    duration: Optional[float] = None


@dataclass
class QueryContext:
    """Context passed to hooks for query interception."""

    prompt: str
    session_id: Optional[str] = None
    tools: List[str] = field(default_factory=list)


class HookResult:
    """Result from a hook execution."""

    ALLOW = None  # Will be set in __init__

    def __init__(self, allowed: bool = True, reason: Optional[str] = None, modified_args: Optional[Dict] = None):
        self.allowed = allowed
        self.reason = reason
        self.modified_args = modified_args

    @property
    def is_rejected(self) -> bool:
        return not self.allowed

    @classmethod
    def reject(cls, reason: str) -> "HookResult":
        return cls(allowed=False, reason=reason)

    @classmethod
    def modify(cls, modified_args: Dict[str, Any]) -> "HookResult":
        return cls(allowed=True, modified_args=modified_args)


# Set class-level ALLOW
HookResult.ALLOW = HookResult(allowed=True)
```

---

### S48-3: Session 管理實現 (10 點)

**描述**: 實現 Session 類別，支援多輪對話、上下文維護和歷史管理。

**驗收標準**:
- [ ] Session 可維持對話歷史
- [ ] session.query() 可執行查詢並累積歷史
- [ ] 支援 get_history() 取得完整對話記錄
- [ ] 支援 add_context() 添加上下文變數
- [ ] 支援 fork() 建立分支 Session
- [ ] 支援 close() 清理資源

**技術任務**:

1. **建立 Session 類別 (`backend/src/integrations/claude_sdk/session.py`)**

```python
"""Multi-turn conversation session for Claude SDK."""

import uuid
import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

from anthropic import AsyncAnthropic

from .config import ClaudeSDKConfig
from .types import Message, ToolCall, QueryContext, ToolCallContext, ToolResultContext, HookResult
from .query import QueryResult
from .tools import get_tool_definitions, execute_tool


@dataclass
class SessionResponse:
    """Response from a session query."""

    content: str
    tool_calls: List[ToolCall]
    tokens_used: int
    message_index: int  # Position in conversation history


class Session:
    """
    Multi-turn conversation session.

    Maintains conversation history and context across multiple queries.

    Example:
        session = await client.create_session()
        try:
            await session.query("Read the auth module")
            await session.query("What security issues do you see?")
            recommendations = await session.query("Provide recommendations")
        finally:
            await session.close()
    """

    def __init__(
        self,
        session_id: str,
        client: AsyncAnthropic,
        config: ClaudeSDKConfig,
        tools: List[str],
        hooks: List["Hook"],
        mcp_servers: List["MCPServer"],
        context: Optional[Dict[str, Any]] = None,
        history: Optional[List[Message]] = None,
    ):
        self.session_id = session_id
        self._client = client
        self._config = config
        self._tools = tools
        self._hooks = hooks
        self._mcp_servers = mcp_servers
        self._context: Dict[str, Any] = context or {}
        self._history: List[Message] = history or []
        self._closed = False
        self._total_tokens = 0

    @property
    def is_closed(self) -> bool:
        return self._closed

    def get_history(self) -> List[Message]:
        """Get conversation history."""
        return self._history.copy()

    def get_context(self) -> Dict[str, Any]:
        """Get current context variables."""
        return self._context.copy()

    def add_context(self, key: str, value: Any) -> None:
        """Add a context variable."""
        self._context[key] = value

    async def query(
        self,
        prompt: str,
        tools: Optional[List[str]] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ) -> SessionResponse:
        """
        Send a query within the session.

        Args:
            prompt: Query text
            tools: Override session tools for this query
            max_tokens: Override max tokens
            stream: Enable streaming response

        Returns:
            SessionResponse with content and tool calls
        """
        if self._closed:
            raise RuntimeError("Session is closed")

        # Trigger query start hooks
        for hook in self._hooks:
            result = await hook.on_query_start(
                QueryContext(prompt=prompt, session_id=self.session_id)
            )
            if result and result.is_rejected:
                raise RuntimeError(f"Query rejected: {result.reason}")

        start_time = time.time()
        active_tools = tools or self._tools
        tool_definitions = get_tool_definitions(active_tools, self._mcp_servers)
        tool_calls: List[ToolCall] = []

        # Build messages from history
        messages = self._build_messages()
        messages.append({"role": "user", "content": prompt})

        # Add user message to history
        self._history.append(Message(role="user", content=prompt, timestamp=time.time()))

        # Agentic loop
        while True:
            response = await self._client.messages.create(
                model=self._config.model,
                max_tokens=max_tokens or self._config.max_tokens,
                system=self._build_system_prompt(),
                messages=messages,
                tools=tool_definitions if tool_definitions else None,
            )

            self._total_tokens += response.usage.input_tokens + response.usage.output_tokens

            # Check for tool use
            has_tool_use = any(block.type == "tool_use" for block in response.content)

            if not has_tool_use:
                # Extract final response
                final_content = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        final_content += block.text

                # Add assistant response to history
                self._history.append(
                    Message(
                        role="assistant",
                        content=final_content,
                        tool_calls=tool_calls,
                        timestamp=time.time(),
                    )
                )

                # Trigger query end hooks
                for hook in self._hooks:
                    await hook.on_query_end(
                        QueryContext(prompt=prompt, session_id=self.session_id),
                        final_content,
                    )

                return SessionResponse(
                    content=final_content,
                    tool_calls=tool_calls,
                    tokens_used=self._total_tokens,
                    message_index=len(self._history) - 1,
                )

            # Process tool calls
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tool_call = ToolCall(id=block.id, name=block.name, args=block.input)
                    tool_calls.append(tool_call)

                    # Check hooks
                    approved = True
                    for hook in self._hooks:
                        hook_result = await hook.on_tool_call(
                            ToolCallContext(
                                tool_name=block.name,
                                args=block.input,
                                session_id=self.session_id,
                            )
                        )
                        if hook_result and hook_result.is_rejected:
                            approved = False
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": f"Rejected: {hook_result.reason}",
                                "is_error": True,
                            })
                            break

                    if not approved:
                        continue

                    # Execute tool
                    try:
                        result = await execute_tool(
                            tool_name=block.name,
                            args=block.input,
                            mcp_servers=self._mcp_servers,
                        )
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })

                        for hook in self._hooks:
                            await hook.on_tool_result(
                                ToolResultContext(
                                    tool_name=block.name,
                                    result=result,
                                    success=True,
                                    session_id=self.session_id,
                                )
                            )

                    except Exception as e:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": f"Error: {str(e)}",
                            "is_error": True,
                        })

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

    async def fork(self, branch_name: Optional[str] = None) -> "Session":
        """
        Create a branched session for exploration.

        Args:
            branch_name: Optional name for the branch

        Returns:
            New Session with copied history and context
        """
        branch_id = f"{self.session_id}:{branch_name or uuid.uuid4().hex[:8]}"

        return Session(
            session_id=branch_id,
            client=self._client,
            config=self._config,
            tools=self._tools.copy(),
            hooks=self._hooks,
            mcp_servers=self._mcp_servers,
            context=self._context.copy(),
            history=self._history.copy(),
        )

    async def close(self) -> None:
        """Close the session and cleanup resources."""
        if not self._closed:
            for hook in self._hooks:
                await hook.on_session_end(self.session_id)
            self._closed = True

    def _build_messages(self) -> List[Dict[str, Any]]:
        """Build API messages from history."""
        messages = []
        for msg in self._history:
            messages.append({"role": msg.role, "content": msg.content})
        return messages

    def _build_system_prompt(self) -> str:
        """Build system prompt with context."""
        base = self._config.system_prompt or ""

        if self._context:
            context_str = "\n".join(f"{k}: {v}" for k, v in self._context.items())
            base = f"{base}\n\nContext:\n{context_str}"

        return base
```

---

### S48-4: API 端點整合 (7 點)

**描述**: 建立 FastAPI 端點，將 Claude SDK 功能暴露給前端和外部系統。

**驗收標準**:
- [ ] POST /api/v1/claude-sdk/query 端點可執行單次查詢
- [ ] POST /api/v1/claude-sdk/sessions 可建立 Session
- [ ] POST /api/v1/claude-sdk/sessions/{id}/query 可執行 Session 查詢
- [ ] DELETE /api/v1/claude-sdk/sessions/{id} 可關閉 Session
- [ ] 與現有認證系統整合

**技術任務**:

1. **建立 API 路由 (`backend/src/api/v1/claude_sdk/routes.py`)**

```python
"""Claude SDK API routes."""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from src.integrations.claude_sdk.client import ClaudeSDKClient
from src.integrations.claude_sdk.exceptions import ClaudeSDKError
from src.api.deps import get_current_user


router = APIRouter(prefix="/claude-sdk", tags=["Claude SDK"])

# Global client instance (should be properly managed in production)
_client: Optional[ClaudeSDKClient] = None


def get_client() -> ClaudeSDKClient:
    global _client
    if _client is None:
        _client = ClaudeSDKClient()
    return _client


# --- Request/Response Models ---

class QueryRequest(BaseModel):
    prompt: str = Field(..., description="Task description")
    tools: Optional[List[str]] = Field(None, description="Tools to enable")
    max_tokens: Optional[int] = Field(None, description="Max response tokens")
    timeout: Optional[int] = Field(None, description="Timeout in seconds")
    working_directory: Optional[str] = Field(None, description="Working directory")


class QueryResponse(BaseModel):
    content: str
    tool_calls: List[dict]
    tokens_used: int
    duration: float
    status: str


class CreateSessionRequest(BaseModel):
    session_id: Optional[str] = None
    system_prompt: Optional[str] = None
    tools: Optional[List[str]] = None
    context: Optional[dict] = None


class SessionQueryRequest(BaseModel):
    prompt: str
    tools: Optional[List[str]] = None
    max_tokens: Optional[int] = None


class SessionResponse(BaseModel):
    session_id: str
    status: str = "active"


class SessionQueryResponse(BaseModel):
    content: str
    tool_calls: List[dict]
    tokens_used: int
    message_index: int


# --- Endpoints ---

@router.post("/query", response_model=QueryResponse)
async def execute_query(
    request: QueryRequest,
    client: ClaudeSDKClient = Depends(get_client),
    current_user: dict = Depends(get_current_user),
):
    """Execute a one-shot autonomous query."""
    try:
        result = await client.query(
            prompt=request.prompt,
            tools=request.tools,
            max_tokens=request.max_tokens,
            timeout=request.timeout,
            working_directory=request.working_directory,
        )

        return QueryResponse(
            content=result.content,
            tool_calls=[
                {"id": tc.id, "name": tc.name, "args": tc.args}
                for tc in result.tool_calls
            ],
            tokens_used=result.tokens_used,
            duration=result.duration,
            status=result.status,
        )

    except ClaudeSDKError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    request: CreateSessionRequest,
    client: ClaudeSDKClient = Depends(get_client),
    current_user: dict = Depends(get_current_user),
):
    """Create a new conversation session."""
    try:
        session = await client.create_session(
            session_id=request.session_id,
            context=request.context,
        )

        return SessionResponse(session_id=session.session_id)

    except ClaudeSDKError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/query", response_model=SessionQueryResponse)
async def session_query(
    session_id: str,
    request: SessionQueryRequest,
    client: ClaudeSDKClient = Depends(get_client),
    current_user: dict = Depends(get_current_user),
):
    """Execute a query within an existing session."""
    try:
        session = await client.resume_session(session_id)
        result = await session.query(
            prompt=request.prompt,
            tools=request.tools,
            max_tokens=request.max_tokens,
        )

        return SessionQueryResponse(
            content=result.content,
            tool_calls=[
                {"id": tc.id, "name": tc.name, "args": tc.args}
                for tc in result.tool_calls
            ],
            tokens_used=result.tokens_used,
            message_index=result.message_index,
        )

    except ClaudeSDKError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/sessions/{session_id}")
async def close_session(
    session_id: str,
    client: ClaudeSDKClient = Depends(get_client),
    current_user: dict = Depends(get_current_user),
):
    """Close a session and cleanup resources."""
    try:
        session = await client.resume_session(session_id)
        await session.close()
        return {"status": "closed", "session_id": session_id}

    except ClaudeSDKError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/sessions/{session_id}/history")
async def get_session_history(
    session_id: str,
    client: ClaudeSDKClient = Depends(get_client),
    current_user: dict = Depends(get_current_user),
):
    """Get conversation history for a session."""
    try:
        session = await client.resume_session(session_id)
        history = session.get_history()

        return {
            "session_id": session_id,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp,
                }
                for msg in history
            ],
        }

    except ClaudeSDKError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

---

## 時間規劃

| 任務 | 預估時間 | 負責人 |
|------|----------|--------|
| S48-1: ClaudeSDKClient 核心封裝 | 3 天 | Backend |
| S48-2: Query API 實現 | 2 天 | Backend |
| S48-3: Session 管理實現 | 3 天 | Backend |
| S48-4: API 端點整合 | 2 天 | Backend |
| 整合測試 | 1 天 | QA |
| 文檔更新 | 1 天 | Tech Writer |

---

## 測試要求

### 單元測試

```python
# tests/unit/integrations/claude_sdk/test_client.py

import pytest
from unittest.mock import AsyncMock, patch

from src.integrations.claude_sdk.client import ClaudeSDKClient
from src.integrations.claude_sdk.exceptions import AuthenticationError


class TestClaudeSDKClient:
    """Tests for ClaudeSDKClient."""

    def test_init_with_api_key(self):
        """Test client initialization with API key."""
        client = ClaudeSDKClient(api_key="test-key")
        assert client.config.api_key == "test-key"

    def test_init_without_api_key_raises_error(self, monkeypatch):
        """Test that missing API key raises AuthenticationError."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(AuthenticationError):
            ClaudeSDKClient()

    @pytest.mark.asyncio
    async def test_query_returns_result(self):
        """Test one-shot query execution."""
        with patch("src.integrations.claude_sdk.query.execute_query") as mock:
            mock.return_value = AsyncMock(
                content="Test response",
                tool_calls=[],
                tokens_used=100,
                duration=1.0,
                status="success",
            )

            client = ClaudeSDKClient(api_key="test-key")
            result = await client.query("Test prompt")

            assert result.content == "Test response"
            assert result.status == "success"

    @pytest.mark.asyncio
    async def test_create_session(self):
        """Test session creation."""
        client = ClaudeSDKClient(api_key="test-key")
        session = await client.create_session()

        assert session.session_id is not None
        assert not session.is_closed
```

### 整合測試

```python
# tests/integration/claude_sdk/test_api.py

import pytest
from httpx import AsyncClient

from main import app


@pytest.mark.asyncio
async def test_query_endpoint():
    """Test /claude-sdk/query endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/claude-sdk/query",
            json={"prompt": "What is 2+2?"},
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "status" in data


@pytest.mark.asyncio
async def test_session_lifecycle():
    """Test session create, query, close lifecycle."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create session
        create_response = await client.post(
            "/api/v1/claude-sdk/sessions",
            json={},
            headers={"Authorization": "Bearer test-token"},
        )
        assert create_response.status_code == 200
        session_id = create_response.json()["session_id"]

        # Query session
        query_response = await client.post(
            f"/api/v1/claude-sdk/sessions/{session_id}/query",
            json={"prompt": "Hello"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert query_response.status_code == 200

        # Close session
        close_response = await client.delete(
            f"/api/v1/claude-sdk/sessions/{session_id}",
            headers={"Authorization": "Bearer test-token"},
        )
        assert close_response.status_code == 200
```

---

## 風險與緩解

| 風險 | 影響 | 機率 | 緩解措施 |
|------|------|------|----------|
| Anthropic API 變更 | 高 | 低 | 封裝 API 調用，抽象化介面 |
| Rate Limit 限制 | 中 | 中 | 實現重試機制和限流 |
| Token 成本過高 | 中 | 中 | 實現 Token 使用監控和預算控制 |
| Session 狀態同步問題 | 中 | 中 | 使用 Redis 作為 Session 存儲 |

---

## 完成定義

- [ ] 所有 User Stories 完成並通過驗收
- [ ] 單元測試覆蓋率 ≥ 85%
- [ ] 整合測試通過
- [ ] API 文檔更新
- [ ] Code Review 完成
- [ ] 無 Critical/High 級別 Bug

---

## 依賴

- **Phase 11**: Agent-Session Integration (必須完成)
- **外部依賴**: anthropic Python SDK
- **基礎設施**: Redis (Session 狀態存儲)
