# Phase 11: Agent-Session Integration

> **目標**: 整合 Session Mode 與 Agent Framework，實現獨立 Agent 對話能力

---

## Phase 概述

### 背景

Phase 10 建立了 Session Mode 基礎設施（對話狀態、訊息存儲），但尚未與 Agent Framework 整合。
Phase 11 將完成這個整合，讓用戶能夠透過 Session 與 Agent 進行真正的多輪對話。

### 設計原則

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         IPA Platform 能力定位                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  【主要能力】工作流編排 (Workflow Orchestration) ← 保持不變              │
│   ├── GroupChat - 多 Agent 協作                                        │
│   ├── Handoff - Agent 交接                                             │
│   ├── Concurrent - 並行執行                                            │
│   ├── Nested - 嵌套工作流                                              │
│   └── Planning - 動態規劃                                              │
│                                                                         │
│  【附加能力】獨立 Agent 對話 (Session-based) ← Phase 11 新增            │
│   └── 透過 Session 與單一 Agent 多輪對話                                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**關鍵原則**:
1. **工作流優先**: 工作流編排是平台核心，Session 對話是附加功能
2. **共享基礎設施**: Session 使用與 Workflow 相同的 Agent 和 LLM 整合
3. **清晰分離**: 兩種模式有各自的入口，但共享底層能力

---

## 架構設計

### 雙入口架構

```
                    ┌─────────────────────────────────┐
                    │           API Gateway            │
                    └─────────────────┬───────────────┘
                                      │
              ┌───────────────────────┴───────────────────────┐
              │                                               │
              ▼                                               ▼
    ┌─────────────────────┐                     ┌─────────────────────┐
    │   Workflow Mode     │                     │    Session Mode     │
    │   (Phase 1-8)       │                     │    (Phase 10-11)    │
    │                     │                     │                     │
    │  POST /workflows    │                     │  POST /sessions     │
    │  POST /executions   │                     │  WS /sessions/{id}  │
    │                     │                     │                     │
    │  • 後台自動化        │                     │  • 即時對話         │
    │  • 定時觸發          │                     │  • 串流回應         │
    │  • 批量處理          │                     │  • 文件交互         │
    │  • 審批流程          │                     │  • 工具調用         │
    └─────────┬───────────┘                     └─────────┬───────────┘
              │                                           │
              └──────────────────┬────────────────────────┘
                                 │
                                 ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                    Shared Infrastructure                         │
    │  ┌─────────────────────────────────────────────────────────┐    │
    │  │              Agent Execution Layer (Phase 11)            │    │
    │  │  • AgentExecutor - 統一的 Agent 執行介面                  │    │
    │  │  • LLM Integration - Azure OpenAI 調用                   │    │
    │  │  • Streaming Support - 串流回應生成                      │    │
    │  └─────────────────────────────────────────────────────────┘    │
    │                                                                  │
    │  ┌─────────────────────────────────────────────────────────┐    │
    │  │                 Existing Infrastructure                  │    │
    │  │  • Agent Framework Adapters (Phase 4-6)                 │    │
    │  │  • MCP Tool Layer (Phase 9)                             │    │
    │  │  • Code Interpreter (Phase 8)                           │    │
    │  │  • Memory & Storage                                     │    │
    │  └─────────────────────────────────────────────────────────┘    │
    └─────────────────────────────────────────────────────────────────┘
```

### 整合流程

```
用戶發送訊息 (Session API)
         │
         ▼
┌─────────────────────────────────────────┐
│  Session Service                         │
│  1. 驗證 Session 狀態                    │
│  2. 存儲用戶訊息                         │
│  3. 獲取對話歷史                         │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│  Agent Executor (NEW - Phase 11)         │
│  1. 載入 Agent 配置                      │
│  2. 構建 LLM 請求 (messages + tools)     │
│  3. 調用 Azure OpenAI                    │
│  4. 處理工具調用 (如有)                  │
│  5. 串流回傳回應                         │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│  Session Service                         │
│  1. 存儲 Assistant 訊息                  │
│  2. 更新 Session 狀態                    │
│  3. 串流回應給客戶端                     │
└─────────────────────────────────────────┘
```

---

## Sprint 規劃

| Sprint | 名稱 | 點數 | 主要內容 |
|--------|------|------|---------|
| Sprint 45 | Agent Executor Core | 35 pts | Agent 執行器、LLM 整合、串流支援 |
| Sprint 46 | Session-Agent Bridge | 30 pts | Session 與 Agent 橋接、訊息處理、工具調用 |
| Sprint 47 | Integration & Polish | 25 pts | 整合測試、錯誤處理、文檔完善 |

**Phase 11 總計**: 90 Story Points

---

## 技術設計

### 核心組件

#### 1. AgentExecutor (新增)

統一的 Agent 執行介面，同時支援 Workflow 和 Session 模式：

```python
class AgentExecutor:
    """Agent 執行器 - 統一執行介面"""

    def __init__(
        self,
        llm_service: LLMService,
        tool_registry: ToolRegistry,
        mcp_client: MCPClient
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
            ExecutionEvent: 執行事件 (content, tool_call, error)
        """
        # 1. 構建 LLM 請求
        llm_messages = self._build_messages(agent, messages)
        available_tools = self._get_available_tools(agent)

        # 2. 調用 LLM
        if stream:
            async for chunk in self._llm.stream(llm_messages, tools=available_tools):
                yield ExecutionEvent(type="content", data=chunk)
        else:
            response = await self._llm.complete(llm_messages, tools=available_tools)
            yield ExecutionEvent(type="content", data=response)

        # 3. 處理工具調用
        # ...
```

#### 2. SessionAgentBridge (新增)

連接 Session Service 和 Agent Executor：

```python
class SessionAgentBridge:
    """Session-Agent 橋接層"""

    def __init__(
        self,
        session_service: SessionService,
        agent_executor: AgentExecutor,
        agent_repository: AgentRepository
    ):
        self._sessions = session_service
        self._executor = agent_executor
        self._agents = agent_repository

    async def process_message(
        self,
        session_id: str,
        content: str,
        attachments: List[Attachment] = None
    ) -> AsyncIterator[str]:
        """
        處理用戶訊息並生成回應

        1. 存儲用戶訊息
        2. 獲取對話歷史
        3. 調用 Agent 生成回應
        4. 存儲 Assistant 訊息
        5. 串流回應
        """
        # 獲取 Session 和 Agent
        session = await self._sessions.get_session(session_id)
        agent = await self._agents.get(session.agent_id)

        # 存儲用戶訊息
        user_message = Message(role=MessageRole.USER, content=content)
        await self._sessions.add_message(session_id, user_message)

        # 獲取對話歷史
        history = await self._sessions.get_messages(session_id)

        # 調用 Agent 執行
        assistant_content = ""
        async for event in self._executor.execute(agent, history, stream=True):
            if event.type == "content":
                assistant_content += event.data
                yield event.data

        # 存儲 Assistant 訊息
        assistant_message = Message(
            role=MessageRole.ASSISTANT,
            content=assistant_content
        )
        await self._sessions.add_message(session_id, assistant_message)
```

### 與現有系統的關係

| 組件 | Phase | 角色 |
|------|-------|------|
| Agent Service | Phase 3 | 提供 Agent 配置 |
| LLM Integration | Phase 3 | Azure OpenAI 調用 |
| Agent Framework Adapters | Phase 4-6 | Workflow 編排 (不變) |
| MCP Tool Layer | Phase 9 | 工具調用 |
| Session Service | Phase 10 | 對話狀態管理 |
| **AgentExecutor** | **Phase 11** | **統一執行介面** |
| **SessionAgentBridge** | **Phase 11** | **Session-Agent 橋接** |

---

## 關鍵設計決策

### 1. 執行模式分離

| 模式 | 入口 | 執行路徑 | 用途 |
|------|------|---------|------|
| Workflow | `/executions` | WorkflowExecutor → Adapters | 自動化流程 |
| Session | `/sessions/{id}/messages` | SessionAgentBridge → AgentExecutor | 即時對話 |

### 2. 訊息角色處理

```python
# Session 模式的訊息角色
class MessageRole(Enum):
    USER = "user"           # 用戶輸入 (由 API 接收)
    ASSISTANT = "assistant" # Agent 回應 (由 LLM 生成)
    SYSTEM = "system"       # 系統提示 (Agent 配置)
    TOOL = "tool"           # 工具結果 (MCP 執行)
```

### 3. 串流回應

```
Client ──WebSocket──> Session API ──> SessionAgentBridge ──> AgentExecutor
                                                                   │
   ◄─────────── stream_delta ◄─────────── yield ◄─────────── LLM stream
```

### 4. 工具調用流程

```
AgentExecutor
    │
    ├─ LLM 決定調用工具
    │       │
    │       ▼
    ├─ 檢查工具權限 (需要審批?)
    │       │
    │       ├─ 不需要 → 直接執行
    │       │
    │       └─ 需要 → 發送審批請求
    │                    │
    │                    ▼
    │              等待用戶審批
    │                    │
    │       ┌────────────┴────────────┐
    │       ▼                         ▼
    │   批准 → 執行              拒絕 → 返回拒絕訊息
    │
    └─ 將工具結果返回 LLM 繼續對話
```

---

## 依賴關係

### 前置條件
- Phase 10 完成 (Session Mode 基礎設施)
- Phase 3 LLM Integration 可用
- Phase 9 MCP Tool Layer 可用

### 技術依賴
- 現有: `azure-openai`, `semantic-kernel`, `redis`
- 無新增套件依賴

---

## 交付物

### 代碼產物

```
backend/src/
├── domain/
│   └── sessions/
│       ├── executor.py      # AgentExecutor (NEW)
│       ├── bridge.py        # SessionAgentBridge (NEW)
│       └── events.py        # 執行事件定義 (UPDATE)
│
├── api/v1/sessions/
│   ├── routes.py           # 更新訊息端點 (UPDATE)
│   └── websocket.py        # WebSocket 處理 (UPDATE)
│
└── integrations/
    └── llm/
        └── streaming.py    # 串流支援 (UPDATE)
```

### 文檔產物
- Agent-Session Integration 設計文檔
- API 更新說明
- 整合測試報告

---

## 風險評估

| 風險 | 可能性 | 影響 | 緩解措施 |
|------|--------|------|---------|
| LLM 回應延遲 | 中 | 中 | 串流回應、超時處理 |
| 工具調用失敗 | 中 | 中 | 錯誤處理、重試機制 |
| 對話歷史過長 | 低 | 中 | Token 限制、歷史截斷 |
| 並發 Session 過多 | 低 | 高 | 連接限制、資源管理 |

---

## 成功指標

1. **功能完整性**: Session 可完成完整多輪對話
2. **回應延遲**: 首個 token < 2秒
3. **串流穩定性**: 無中斷串流
4. **測試覆蓋率**: > 85%
5. **API 相容性**: 不破壞現有 Workflow API

---

**創建日期**: 2025-12-23
**上次更新**: 2025-12-23
