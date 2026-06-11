# Sprint 45: Agent Executor Core

> **Phase 11**: Agent-Session Integration
> **Sprint 目標**: 建立統一的 Agent 執行器，整合 LLM 調用與串流支援

---

## Sprint 概述

| 屬性 | 值 |
|------|-----|
| Sprint 編號 | 45 |
| 計劃點數 | 35 Story Points |
| 預計工期 | 5 工作日 |
| 前置條件 | Phase 10 Session Mode 完成 |

### Sprint 目標

1. 建立 AgentExecutor 統一執行介面
2. 整合 Azure OpenAI LLM 調用
3. 實現串流回應生成
4. 支援工具調用基礎架構

---

## User Stories

### S45-1: AgentExecutor 核心類別 (13 pts)

**As a** 系統開發者
**I want** 統一的 Agent 執行介面
**So that** Workflow 和 Session 模式可共享執行邏輯

**驗收標準**:
- [ ] AgentExecutor 類別實現
- [ ] 支援 Agent 配置載入
- [ ] 訊息構建邏輯 (system + history + user)
- [ ] 執行事件定義 (ExecutionEvent)
- [ ] 同步與非同步執行模式

**技術設計**:

```python
# backend/src/domain/sessions/executor.py

from typing import AsyncIterator, List, Optional
from dataclasses import dataclass
from enum import Enum

class ExecutionEventType(Enum):
    """執行事件類型"""
    CONTENT = "content"           # 文字內容
    TOOL_CALL = "tool_call"       # 工具調用
    TOOL_RESULT = "tool_result"   # 工具結果
    ERROR = "error"               # 錯誤
    DONE = "done"                 # 完成

@dataclass
class ExecutionEvent:
    """執行事件"""
    type: ExecutionEventType
    data: Any
    metadata: Optional[Dict[str, Any]] = None

class AgentExecutor:
    """Agent 執行器 - 統一執行介面"""

    def __init__(
        self,
        llm_service: LLMService,
        tool_registry: Optional[ToolRegistry] = None,
        mcp_client: Optional[MCPClient] = None
    ):
        self._llm = llm_service
        self._tools = tool_registry
        self._mcp = mcp_client

    async def execute(
        self,
        agent: Agent,
        messages: List[Message],
        stream: bool = True
    ) -> AsyncIterator[ExecutionEvent]:
        """
        執行 Agent 對話

        Args:
            agent: Agent 配置
            messages: 對話歷史
            stream: 是否串流回應

        Yields:
            ExecutionEvent: 執行事件
        """
        # 1. 構建 LLM 請求
        llm_messages = self._build_messages(agent, messages)
        available_tools = self._get_available_tools(agent)

        # 2. 調用 LLM
        if stream:
            async for chunk in self._stream_completion(
                llm_messages,
                tools=available_tools
            ):
                yield chunk
        else:
            result = await self._complete(llm_messages, tools=available_tools)
            yield result

    def _build_messages(
        self,
        agent: Agent,
        messages: List[Message]
    ) -> List[Dict]:
        """構建 LLM 訊息格式"""
        llm_messages = []

        # System prompt from agent config
        if agent.system_prompt:
            llm_messages.append({
                "role": "system",
                "content": agent.system_prompt
            })

        # Conversation history
        for msg in messages:
            llm_messages.append({
                "role": msg.role.value,
                "content": msg.content
            })

        return llm_messages

    def _get_available_tools(self, agent: Agent) -> List[Dict]:
        """獲取 Agent 可用工具"""
        if not self._tools or not agent.tool_ids:
            return []

        tools = []
        for tool_id in agent.tool_ids:
            tool = self._tools.get(tool_id)
            if tool:
                tools.append(tool.to_openai_format())
        return tools
```

**依賴**:
- LLMService (Phase 3)
- Agent domain model
- ToolRegistry (Phase 9 MCP)

---

### S45-2: LLM 串流整合 (10 pts)

**As a** 系統開發者
**I want** 串流式 LLM 回應
**So that** 用戶可即時看到 Agent 回應

**驗收標準**:
- [ ] Azure OpenAI 串流調用
- [ ] SSE (Server-Sent Events) 格式處理
- [ ] Token 計數追蹤
- [ ] 超時與重試機制
- [ ] 錯誤處理與恢復

**技術設計**:

```python
# backend/src/domain/sessions/streaming.py

from typing import AsyncIterator
import asyncio

class StreamingLLMHandler:
    """串流 LLM 處理器"""

    def __init__(
        self,
        client: AsyncAzureOpenAI,
        deployment: str,
        timeout: float = 60.0,
        max_retries: int = 3
    ):
        self._client = client
        self._deployment = deployment
        self._timeout = timeout
        self._max_retries = max_retries

    async def stream_completion(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> AsyncIterator[ExecutionEvent]:
        """
        串流生成回應

        Yields:
            ExecutionEvent: content/tool_call/done 事件
        """
        request_params = {
            "model": self._deployment,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True
        }

        if tools:
            request_params["tools"] = tools
            request_params["tool_choice"] = "auto"

        try:
            response = await asyncio.wait_for(
                self._client.chat.completions.create(**request_params),
                timeout=self._timeout
            )

            accumulated_content = ""
            tool_calls = []

            async for chunk in response:
                delta = chunk.choices[0].delta

                # Content chunk
                if delta.content:
                    accumulated_content += delta.content
                    yield ExecutionEvent(
                        type=ExecutionEventType.CONTENT,
                        data=delta.content,
                        metadata={"accumulated": len(accumulated_content)}
                    )

                # Tool call chunk
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        tool_calls = self._accumulate_tool_call(tool_calls, tc)

            # Emit tool calls if any
            for tool_call in tool_calls:
                yield ExecutionEvent(
                    type=ExecutionEventType.TOOL_CALL,
                    data=tool_call
                )

            # Done event
            yield ExecutionEvent(
                type=ExecutionEventType.DONE,
                data={
                    "content": accumulated_content,
                    "tool_calls": tool_calls,
                    "usage": self._estimate_usage(messages, accumulated_content)
                }
            )

        except asyncio.TimeoutError:
            yield ExecutionEvent(
                type=ExecutionEventType.ERROR,
                data={"error": "timeout", "message": "LLM response timeout"}
            )
        except Exception as e:
            yield ExecutionEvent(
                type=ExecutionEventType.ERROR,
                data={"error": "llm_error", "message": str(e)}
            )

    def _accumulate_tool_call(
        self,
        tool_calls: List,
        delta_tc
    ) -> List:
        """累積工具調用 delta"""
        # 實現工具調用的增量累積
        ...
        return tool_calls

    def _estimate_usage(
        self,
        messages: List[Dict],
        response: str
    ) -> Dict:
        """估算 token 使用量"""
        # 使用 tiktoken 估算
        ...
```

**依賴**:
- openai (AsyncAzureOpenAI)
- tiktoken (token 計數)

---

### S45-3: 工具調用框架 (8 pts)

**As a** 系統開發者
**I want** 工具調用處理框架
**So that** Agent 可執行 MCP 工具

**驗收標準**:
- [ ] 工具調用解析
- [ ] MCP 工具執行整合
- [ ] 工具結果回傳 LLM
- [ ] 多輪工具調用支援
- [ ] 工具權限檢查

**技術設計**:

```python
# backend/src/domain/sessions/tool_handler.py

class ToolCallHandler:
    """工具調用處理器"""

    def __init__(
        self,
        mcp_client: MCPClient,
        permission_checker: Optional[PermissionChecker] = None
    ):
        self._mcp = mcp_client
        self._permissions = permission_checker

    async def handle_tool_calls(
        self,
        tool_calls: List[ToolCall],
        session_context: SessionContext
    ) -> AsyncIterator[ExecutionEvent]:
        """
        處理工具調用

        Args:
            tool_calls: LLM 返回的工具調用列表
            session_context: Session 上下文

        Yields:
            ExecutionEvent: tool_result 或 approval_required 事件
        """
        for tool_call in tool_calls:
            # 權限檢查
            if self._permissions:
                requires_approval = await self._permissions.check(
                    tool_call.function.name,
                    session_context
                )

                if requires_approval:
                    yield ExecutionEvent(
                        type=ExecutionEventType.TOOL_CALL,
                        data={
                            "status": "approval_required",
                            "tool_call": tool_call,
                            "approval_id": str(uuid4())
                        }
                    )
                    continue

            # 執行工具
            try:
                result = await self._mcp.execute_tool(
                    tool_call.function.name,
                    json.loads(tool_call.function.arguments)
                )

                yield ExecutionEvent(
                    type=ExecutionEventType.TOOL_RESULT,
                    data={
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "result": result
                    }
                )
            except Exception as e:
                yield ExecutionEvent(
                    type=ExecutionEventType.TOOL_RESULT,
                    data={
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "error": str(e)
                    }
                )

class ToolCall:
    """工具調用數據結構"""
    id: str
    function: ToolFunction

class ToolFunction:
    """工具函數"""
    name: str
    arguments: str  # JSON string
```

**依賴**:
- MCPClient (Phase 9)
- PermissionChecker (可選)

---

### S45-4: 執行事件系統 (4 pts)

**As a** 系統開發者
**I want** 統一的執行事件系統
**So that** 可追蹤和處理執行過程

**驗收標準**:
- [ ] 事件類型定義完整
- [ ] 事件序列化支援
- [ ] WebSocket 事件格式
- [ ] 事件日誌記錄

**技術設計**:

```python
# backend/src/domain/sessions/events.py

from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional
from enum import Enum
from datetime import datetime
import json

class ExecutionEventType(Enum):
    """執行事件類型"""
    # 內容事件
    CONTENT = "content"
    CONTENT_DELTA = "content_delta"

    # 工具事件
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    APPROVAL_REQUIRED = "approval_required"
    APPROVAL_RESPONSE = "approval_response"

    # 狀態事件
    STARTED = "started"
    DONE = "done"
    ERROR = "error"

    # 系統事件
    HEARTBEAT = "heartbeat"

@dataclass
class ExecutionEvent:
    """執行事件"""
    type: ExecutionEventType
    data: Any
    timestamp: datetime = None
    event_id: str = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.event_id is None:
            self.event_id = str(uuid4())

    def to_dict(self) -> Dict:
        """轉換為字典"""
        return {
            "event_id": self.event_id,
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }

    def to_json(self) -> str:
        """轉換為 JSON"""
        return json.dumps(self.to_dict())

    def to_sse(self) -> str:
        """轉換為 SSE 格式"""
        return f"event: {self.type.value}\ndata: {json.dumps(self.data)}\n\n"

    def to_websocket(self) -> Dict:
        """轉換為 WebSocket 格式"""
        return {
            "type": "execution_event",
            "payload": self.to_dict()
        }
```

**依賴**:
- 無外部依賴

---

## 技術架構

### 組件關係

```
┌─────────────────────────────────────────────────────────────┐
│                     AgentExecutor                            │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                  execute()                           │    │
│  │  1. _build_messages() - 構建 LLM 訊息               │    │
│  │  2. _get_available_tools() - 獲取可用工具            │    │
│  │  3. StreamingLLMHandler.stream_completion()         │    │
│  │  4. ToolCallHandler.handle_tool_calls()             │    │
│  └─────────────────────────────────────────────────────┘    │
└───────────────────────────┬─────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
    ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
    │ LLMService    │ │ ToolRegistry  │ │ MCPClient     │
    │ (Phase 3)     │ │ (Phase 9)     │ │ (Phase 9)     │
    └───────────────┘ └───────────────┘ └───────────────┘
```

### 檔案結構

```
backend/src/domain/sessions/
├── __init__.py
├── executor.py          # AgentExecutor (S45-1)
├── streaming.py         # StreamingLLMHandler (S45-2)
├── tool_handler.py      # ToolCallHandler (S45-3)
└── events.py            # ExecutionEvent system (S45-4)
```

---

## 依賴關係

### 內部依賴
| 組件 | Phase | 用途 |
|------|-------|------|
| LLMService | Phase 3 | Azure OpenAI 調用 |
| Agent model | Phase 3 | Agent 配置 |
| MCPClient | Phase 9 | MCP 工具調用 |
| ToolRegistry | Phase 9 | 工具註冊表 |
| SessionService | Phase 10 | Session 狀態 |

### 外部依賴
| 套件 | 版本 | 用途 |
|------|------|------|
| openai | >= 1.0 | AsyncAzureOpenAI |
| tiktoken | >= 0.5 | Token 計數 |

---

## 測試計劃

### 單元測試

```python
# tests/unit/domain/sessions/test_executor.py

class TestAgentExecutor:
    """AgentExecutor 單元測試"""

    @pytest.fixture
    def mock_llm_service(self):
        return MagicMock(spec=LLMService)

    @pytest.fixture
    def executor(self, mock_llm_service):
        return AgentExecutor(llm_service=mock_llm_service)

    async def test_build_messages_with_system_prompt(self, executor):
        """測試系統提示詞構建"""
        agent = Agent(system_prompt="You are a helpful assistant")
        messages = [Message(role=MessageRole.USER, content="Hello")]

        llm_messages = executor._build_messages(agent, messages)

        assert llm_messages[0]["role"] == "system"
        assert llm_messages[0]["content"] == "You are a helpful assistant"
        assert llm_messages[1]["role"] == "user"

    async def test_execute_streams_content(self, executor, mock_llm_service):
        """測試串流執行"""
        # Setup mock
        mock_llm_service.stream.return_value = async_generator(["Hello", " World"])

        agent = Agent(name="test")
        messages = [Message(role=MessageRole.USER, content="Hi")]

        events = []
        async for event in executor.execute(agent, messages, stream=True):
            events.append(event)

        assert len(events) >= 2
        assert events[0].type == ExecutionEventType.CONTENT
```

### 整合測試

```python
# tests/integration/test_agent_execution.py

class TestAgentExecution:
    """Agent 執行整合測試"""

    @pytest.mark.integration
    async def test_full_execution_flow(self, test_client, test_agent):
        """測試完整執行流程"""
        # Create session
        session = await create_test_session(test_agent.id)

        # Execute with streaming
        events = []
        async for event in execute_agent(session.id, "Hello"):
            events.append(event)

        # Verify
        assert any(e.type == ExecutionEventType.CONTENT for e in events)
        assert events[-1].type == ExecutionEventType.DONE
```

---

## 風險與緩解

| 風險 | 可能性 | 影響 | 緩解措施 |
|------|--------|------|----------|
| LLM 回應延遲 | 中 | 中 | 超時設定、串流優化 |
| Token 超出限制 | 中 | 中 | Token 計數、歷史截斷 |
| 工具執行失敗 | 中 | 低 | 錯誤處理、重試機制 |
| 串流中斷 | 低 | 中 | 心跳檢測、重連機制 |

---

## 完成標準

- [ ] 所有 Story 完成並通過驗收
- [ ] 單元測試覆蓋率 > 85%
- [ ] 整合測試通過
- [ ] 代碼審查完成
- [ ] 文檔更新完成

---

**創建日期**: 2025-12-23
**預計完成**: Sprint 45 結束
