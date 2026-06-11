# IPA Platform - Complete Feature Catalog

> **Purpose**: 完整的功能目錄，詳細說明每個功能的描述、依賴關係和相互關聯
> **Last Updated**: 2025-12-29
> **Total Features**: 65+ 功能模塊

---

## Table of Contents

1. [Feature Overview](#1-feature-overview)
2. [Core Engine Features](#2-core-engine-features)
3. [Orchestration Features](#3-orchestration-features)
4. [AI Enhancement Features](#4-ai-enhancement-features)
5. [Session & Claude SDK Features](#5-session--claude-sdk-features)
6. [MCP Protocol & Servers](#6-mcp-protocol--servers)
7. [Human-in-the-Loop Features](#7-human-in-the-loop-features)
8. [Platform Services](#8-platform-services)
9. [External Connectors](#9-external-connectors)
10. [Configuration & Management](#10-configuration--management)
11. [Feature Dependency Matrix](#11-feature-dependency-matrix)
12. [Feature Relationship Diagram](#12-feature-relationship-diagram)

---

## 1. Feature Overview

### 1.1 Feature Statistics

| Category | Count | Status |
|----------|-------|--------|
| Core Engine | 9 | ✅ Complete |
| Orchestration | 18 | ✅ Complete |
| AI Enhancement | 8 | ✅ Complete |
| Session & Claude SDK | 20 | ✅ Complete |
| MCP Protocol & Servers | 12 | ✅ Complete |
| Human-in-the-Loop | 6 | ✅ Complete |
| Platform Services | 7 | ✅ Complete |
| External Connectors | 4 | ✅ Complete |
| Configuration & Management | 6 | ✅ Complete |
| **Total** | **65+** | **Production Ready** |

### 1.2 Feature Category Map

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           IPA PLATFORM COMPLETE FEATURE MAP                          │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─ CORE ENGINE (9) ────────────────────────────────────────────────────────────┐   │
│  │  [Agent Management]      [Workflow Engine]       [Execution Control]         │   │
│  │  [Tool Registry]         [Capability Registry]   [State Machine]             │   │
│  │  [Step Execution]        [Error Handling]        [History Management]        │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  ┌─ ORCHESTRATION (18) ─────────────────────────────────────────────────────────┐   │
│  │  [GroupChat]             [Handoff]               [Concurrent]                │   │
│  │  [Nested Workflow]       [Dynamic Planning]      [MultiTurn]                 │   │
│  │  [Turn Management]       [Voting System]         [Parallel Gateway]          │   │
│  │  [Context Propagation]   [Task Decomposition]    [Memory Persistence]        │   │
│  │  [Capability Matching]   [Handoff Policies]      [Trial & Error]             │   │
│  │  [Recursive Handler]     [Composition Builder]   [Deadlock Detection]        │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  ┌─ AI ENHANCEMENT (8) ─────────────────────────────────────────────────────────┐   │
│  │  [Decision Engine]       [Code Interpreter]      [LLM Integration]           │   │
│  │  [Confidence Scoring]    [Sandbox Execution]     [Response Caching]          │   │
│  │  [Visualization Gen]     [Token Tracking]                                    │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  ┌─ SESSION & CLAUDE SDK (20) ──────────────────────────────────────────────────┐   │
│  │  [Session Management]    [Agent-Session Bridge]  [ClaudeSDKClient]           │   │
│  │  [ToolRegistry]          [HookManager]           [HybridOrchestrator]        │   │
│  │  [File Analysis]         [File Generation]       [History Manager]           │   │
│  │  [Bookmarks]             [Search]                [Tags]                      │   │
│  │  [Statistics]            [Templates]             [Event Publishing]          │   │
│  │  [StreamingHandler]      [WebSocket Handler]     [Tool Approval Manager]     │   │
│  │  [Hook Pipeline]         [Capability Selector]                               │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  ┌─ MCP PROTOCOL & SERVERS (12) ────────────────────────────────────────────────┐   │
│  │  [MCP Core]              [Server Registry]       [Transport Layer]           │   │
│  │  [Shell Server]          [Filesystem Server]     [SSH Server]                │   │
│  │  [LDAP Server]           [Azure Server]          [Permission System]         │   │
│  │  [Audit Logger]          [Config Loader]         [Tool Discovery]            │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  ┌─ HUMAN-IN-THE-LOOP (6) ──────────────────────────────────────────────────────┐   │
│  │  [Checkpoint System]     [Approval Workflow]     [Tool Approval]             │   │
│  │  [Timeout Handling]      [Escalation Logic]      [Resume Service]            │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  ┌─ PLATFORM SERVICES (7) ──────────────────────────────────────────────────────┐   │
│  │  [Audit Logging]         [Cache Management]      [DevTools/Tracer]           │   │
│  │  [Learning Service]      [Notifications]         [Performance Monitor]       │   │
│  │  [Dashboard API]                                                             │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  ┌─ EXTERNAL CONNECTORS (4) ────────────────────────────────────────────────────┐   │
│  │  [ServiceNow]            [Dynamics 365]          [SharePoint]                │   │
│  │  [Connector Registry]                                                        │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  ┌─ CONFIGURATION & MANAGEMENT (6) ─────────────────────────────────────────────┐   │
│  │  [Prompt Templates]      [Workflow Templates]    [Webhook Triggers]          │   │
│  │  [Version Control]       [Scenario Routing]      [Dashboard Config]          │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Engine Features

### 2.1 Agent Management

| Feature | Description | Dependencies | API Endpoint |
|---------|-------------|--------------|--------------|
| **Agent CRUD** | 建立、讀取、更新、刪除 Agent 配置 | Database, Pydantic | `POST/GET/PUT/DELETE /api/v1/agents` |
| **Agent Configuration** | JSON 配置管理，包括 LLM 設定、工具綁定 | Config Service | `PUT /api/v1/agents/{id}/config` |
| **Capability Registry** | Agent 能力註冊和查詢系統 | Redis Cache | `GET /api/v1/agents/{id}/capabilities` |

**Related Files**:
```
backend/src/domain/agents/
├── service.py          # Agent 業務邏輯
├── schemas.py          # Pydantic 模型
└── tools/
    ├── registry.py     # 工具註冊表
    ├── builtin.py      # 內建工具
    └── base.py         # 工具基類
```

**Relationships**:
- **Depends On**: Database, Redis, LLM Integration
- **Used By**: Workflow Engine, Orchestration, Session Management

---

### 2.2 Workflow Engine

| Feature | Description | Dependencies | API Endpoint |
|---------|-------------|--------------|--------------|
| **Workflow CRUD** | 工作流定義管理 | Database | `POST/GET/PUT/DELETE /api/v1/workflows` |
| **State Machine** | 工作流執行狀態轉換 (pending → running → waiting → completed/failed) | Redis | Internal |
| **Step Execution** | 單步驟執行邏輯 | Agent Service | Internal |
| **Error Handling** | 錯誤捕獲、重試邏輯、失敗恢復 | Audit Logger | Internal |

**Related Files**:
```
backend/src/domain/workflows/
├── service.py          # Workflow 業務邏輯
├── models.py           # 數據模型
├── resume_service.py   # 恢復服務
└── executors/
    ├── approval.py     # 審批執行器
    ├── concurrent.py   # 並行執行器
    └── parallel_gateway.py  # 並行網關
```

**State Machine Diagram**:
```
┌─────────┐     execute()    ┌─────────┐
│ PENDING │─────────────────▶│ RUNNING │
└─────────┘                  └────┬────┘
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
              ┌──────────┐ ┌───────────┐ ┌────────────┐
              │COMPLETED │ │  FAILED   │ │  WAITING   │
              └──────────┘ └───────────┘ │ _APPROVAL  │
                                         └─────┬──────┘
                                               │ approve()
                                               ▼
                                         ┌──────────┐
                                         │ RUNNING  │
                                         └──────────┘
```

**Relationships**:
- **Depends On**: Agent Management, State Machine, Checkpoint System
- **Used By**: Execution Control, Orchestration Modules

---

### 2.3 Execution Control

| Feature | Description | Dependencies | API Endpoint |
|---------|-------------|--------------|--------------|
| **Execution Tracking** | 執行實例追蹤和管理 | Database, Redis | `GET /api/v1/executions` |
| **History Management** | 執行歷史記錄和查詢 | PostgreSQL | `GET /api/v1/executions/{id}/history` |
| **Real-time Updates** | WebSocket 實時狀態推送 | WebSocket | `WS /api/v1/executions/{id}/ws` |
| **Metrics Collection** | 執行指標收集 (duration, token usage) | Performance Monitor | Internal |

**Related Files**:
```
backend/src/domain/executions/
├── state_machine.py    # 執行狀態機
└── __init__.py

backend/src/api/v1/executions/
├── routes.py           # API 路由
└── schemas.py          # 請求/響應模型
```

**Relationships**:
- **Depends On**: Workflow Engine, State Machine
- **Used By**: Dashboard, Audit Logging, Performance Monitor

---

## 3. Orchestration Features

### 3.1 GroupChat (多 Agent 對話)

| Feature | Description | Dependencies | API Endpoint |
|---------|-------------|--------------|--------------|
| **Multi-Agent Chat** | 多個 Agent 協同對話 | GroupChatBuilder | `POST /api/v1/groupchat` |
| **Turn Management** | 輪次管理 (round-robin, priority) | Turn Tracker | Internal |
| **History Tracking** | 對話歷史記錄 | Redis, PostgreSQL | `GET /api/v1/groupchat/{id}/history` |
| **Voting System** | 群體投票決策機制 | Voting Adapter | `POST /api/v1/groupchat/{id}/vote` |

**Related Files**:
```
backend/src/integrations/agent_framework/builders/
├── groupchat.py              # GroupChatBuilderAdapter
├── groupchat_orchestrator.py # 協調器
├── groupchat_voting.py       # 投票系統
└── groupchat_migration.py    # 遷移適配

backend/src/api/v1/groupchat/
├── routes.py                 # API 路由
├── multiturn_service.py      # 多輪服務
└── schemas.py                # 模型定義
```

**Relationships**:
- **Depends On**: Agent Management, Turn Tracker, Memory Persistence
- **Used By**: Customer Service Scenarios, Research Assistant

---

### 3.2 Handoff (Agent 交接)

| Feature | Description | Dependencies | API Endpoint |
|---------|-------------|--------------|--------------|
| **Handoff Controller** | 交接執行控制 | HandoffBuilder | `POST /api/v1/handoff` |
| **3 Handoff Policies** | IMMEDIATE, GRACEFUL, CONDITIONAL | Policy Engine | Config |
| **6 Trigger Types** | CONDITION, EVENT, TIMEOUT, ERROR, CAPABILITY, EXPLICIT | Trigger Parser | Config |
| **Capability Matching** | 智能 Agent 能力匹配 | Capability Registry | Internal |
| **Context Transfer** | 上下文傳遞 | Context Manager | Internal |

**Related Files**:
```
backend/src/integrations/agent_framework/builders/
├── handoff.py              # HandoffBuilderAdapter
├── handoff_policy.py       # 交接策略
├── handoff_capability.py   # 能力匹配
├── handoff_context.py      # 上下文管理
├── handoff_service.py      # 交接服務
└── handoff_hitl.py         # 人機交互支持

backend/src/api/v1/handoff/
├── routes.py               # API 路由
└── schemas.py              # 模型定義
```

**Handoff Policy Diagram**:
```
┌─────────────┐        ┌─────────────┐        ┌─────────────┐
│  IMMEDIATE  │        │  GRACEFUL   │        │ CONDITIONAL │
│             │        │             │        │             │
│ 立即交接    │        │ 等待完成   │        │ 條件滿足   │
│ 無等待     │        │ 再交接     │        │ 才交接     │
└─────────────┘        └─────────────┘        └─────────────┘
```

**Relationships**:
- **Depends On**: Agent Management, Capability Registry, Trigger System
- **Used By**: Customer Service Routing, Specialized Task Delegation

---

### 3.3 Concurrent (並行執行)

| Feature | Description | Dependencies | API Endpoint |
|---------|-------------|--------------|--------------|
| **Parallel Execution** | 多任務並行執行 | ConcurrentBuilder | `POST /api/v1/concurrent` |
| **Resource Pooling** | 執行資源池管理 | Thread Pool | Internal |
| **Error Isolation** | 錯誤隔離，單任務失敗不影響其他 | Error Handler | Internal |
| **State Management** | 並行執行狀態追蹤 | Concurrent State | `GET /api/v1/concurrent/{id}/status` |
| **Deadlock Detection** | 死鎖檢測和預防 | Deadlock Detector | Internal |
| **WebSocket Updates** | 實時進度推送 | WebSocket | `WS /api/v1/concurrent/{id}/ws` |

**Related Files**:
```
backend/src/integrations/agent_framework/builders/
├── concurrent.py               # ConcurrentBuilderAdapter
└── concurrent_migration.py     # 遷移支持

backend/src/domain/workflows/executors/
├── concurrent.py               # 並行執行器
├── concurrent_state.py         # 狀態管理
└── parallel_gateway.py         # 並行網關

backend/src/domain/workflows/
└── deadlock_detector.py        # 死鎖檢測
```

**Relationships**:
- **Depends On**: Workflow Engine, Thread Pool, State Machine
- **Used By**: Document Processing, Batch Operations

---

### 3.4 Nested Workflow (嵌套工作流)

| Feature | Description | Dependencies | API Endpoint |
|---------|-------------|--------------|--------------|
| **Sub-workflow Invocation** | 工作流中調用子工作流 | NestedWorkflowAdapter | `POST /api/v1/nested` |
| **Context Propagation** | 父子工作流上下文傳遞 | Context Propagation | Internal |
| **Nested Error Handling** | 嵌套層級錯誤處理 | Error Handler | Internal |
| **Recursive Handler** | 遞歸工作流支持 | Recursive Handler | Internal |
| **Composition Builder** | 工作流組合構建 | Composition Builder | Internal |

**Related Files**:
```
backend/src/integrations/agent_framework/builders/
└── nested_workflow.py          # NestedWorkflowAdapter

backend/src/domain/orchestration/nested/
├── workflow_manager.py         # 工作流管理器
├── sub_executor.py             # 子執行器
├── recursive_handler.py        # 遞歸處理
├── composition_builder.py      # 組合構建
└── context_propagation.py      # 上下文傳遞
```

**Nested Workflow Structure**:
```
┌─ Parent Workflow ────────────────────────────┐
│                                              │
│  [Step 1] ──▶ [Step 2] ──▶ [Sub-Workflow] ─┐│
│                              │              ││
│              ┌───────────────▼──────────┐  ││
│              │ ┌─ Child Workflow ─────┐ │  ││
│              │ │ [A] ──▶ [B] ──▶ [C]  │ │  ││
│              │ └──────────────────────┘ │  ││
│              └──────────────────────────┘  ││
│                              │              ││
│  [Step 4] ◀────────────────[Result]◀───────┘│
│                                              │
└──────────────────────────────────────────────┘
```

**Relationships**:
- **Depends On**: Workflow Engine, Context Manager, Error Handler
- **Used By**: Complex Document Processing, Multi-stage Pipelines

---

### 3.5 Dynamic Planning (動態規劃)

| Feature | Description | Dependencies | API Endpoint |
|---------|-------------|--------------|--------------|
| **Task Decomposition** | 任務自動分解 | Task Decomposer | `POST /api/v1/planning/decompose` |
| **Plan Adaptation** | 執行時計劃調整 | Dynamic Planner | Internal |
| **Autonomous Decision** | 自主決策能力 | Decision Engine | Internal |
| **Trial & Error** | 試錯學習機制 | Trial Error Handler | Internal |

**Related Files**:
```
backend/src/integrations/agent_framework/builders/
├── planning.py                 # PlanningAdapter
└── magentic.py                # MagenticBuilderAdapter

backend/src/domain/orchestration/planning/
├── task_decomposer.py          # 任務分解器
├── dynamic_planner.py          # 動態規劃器
├── decision_engine.py          # 決策引擎
└── trial_error.py              # 試錯處理
```

**Decision Engine Flow**:
```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Analyze    │────▶│   Evaluate   │────▶│   Decide     │
│   Context    │     │   Options    │     │   Action     │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
                     ┌────────────────────────────┴───────────────┐
                     ▼                            ▼               ▼
              ┌──────────┐                 ┌──────────┐    ┌──────────┐
              │ Execute  │                 │ Delegate │    │ Escalate │
              │ Self     │                 │ to Agent │    │ to Human │
              └──────────┘                 └──────────┘    └──────────┘
```

**Relationships**:
- **Depends On**: LLM Integration, Agent Management, Decision Engine
- **Used By**: Autonomous Agents, Research Assistants

---

### 3.6 MultiTurn (多輪對話)

| Feature | Description | Dependencies | API Endpoint |
|---------|-------------|--------------|--------------|
| **Conversation State** | 對話狀態維護 | Session Manager | Internal |
| **Memory Persistence** | 記憶持久化 (Redis/PostgreSQL) | Memory Store | Internal |
| **Checkpoint Storage** | 對話檢查點 | Checkpoint Storage | Internal |
| **Turn Tracking** | 輪次追蹤 | Turn Tracker | Internal |
| **Context Management** | 上下文窗口管理 | Context Manager | Internal |

**Related Files**:
```
backend/src/integrations/agent_framework/multiturn/
├── adapter.py                  # MultiTurnAdapter
└── checkpoint_storage.py       # 檢查點存儲

backend/src/domain/orchestration/multiturn/
├── session_manager.py          # Session 管理
├── turn_tracker.py             # 輪次追蹤
└── context_manager.py          # 上下文管理

backend/src/domain/orchestration/memory/
├── base.py                     # 記憶基類
├── in_memory.py                # 內存存儲
├── redis_store.py              # Redis 存儲
└── postgres_store.py           # PostgreSQL 存儲
```

**Relationships**:
- **Depends On**: Redis, PostgreSQL, Checkpoint System
- **Used By**: GroupChat, Session Management, Research Assistant

---

## 4. AI Enhancement Features

### 4.1 Decision Engine

| Feature | Description | Dependencies | API Endpoint |
|---------|-------------|--------------|--------------|
| **Confidence Scoring** | 決策信心度評分 | LLM Integration | Internal |
| **Multi-factor Analysis** | 多因素決策分析 | Scoring Models | Internal |
| **Audit Trail** | 決策審計追蹤 | Audit Logger | Internal |
| **Threshold Configuration** | 信心度閾值配置 | Config Service | Admin |

**Related Files**:
```
backend/src/domain/orchestration/planning/
└── decision_engine.py          # 決策引擎核心
```

**Confidence Scoring Model**:
```
┌─────────────────────────────────────────────────────────────┐
│                    Confidence Scoring                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Score = Σ (Factor_i × Weight_i)                            │
│                                                              │
│  Factors:                                                    │
│  ├─ LLM Confidence (0.3)     ─ 模型自身信心度               │
│  ├─ Context Relevance (0.25) ─ 上下文相關性                 │
│  ├─ Historical Success (0.2) ─ 歷史成功率                   │
│  ├─ Input Quality (0.15)     ─ 輸入品質                     │
│  └─ Agent Capability (0.1)   ─ Agent 能力匹配度             │
│                                                              │
│  Thresholds:                                                 │
│  ├─ High Confidence: ≥ 0.8   → Auto Execute                 │
│  ├─ Medium: 0.5 - 0.8        → Human Review                 │
│  └─ Low: < 0.5               → Reject / Escalate            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Relationships**:
- **Depends On**: LLM Integration, Historical Data
- **Used By**: Dynamic Planning, Human-in-the-Loop

---

### 4.2 Code Interpreter

| Feature | Description | Dependencies | API Endpoint |
|---------|-------------|--------------|--------------|
| **Sandbox Execution** | 安全沙箱代碼執行 | Docker/Isolated Runtime | `POST /api/v1/code-interpreter/execute` |
| **File Upload/Download** | 文件上傳下載支持 | File Storage | `POST /api/v1/code-interpreter/files` |
| **Visualization Generation** | 圖表/視覺化生成 | Matplotlib, Plotly | `GET /api/v1/code-interpreter/visualizations` |
| **Multi-language Support** | 多語言支持 (Python, JS) | Language Runtimes | Config |

**Related Files**:
```
backend/src/integrations/agent_framework/tools/
├── code_interpreter_tool.py    # Code Interpreter 工具
└── base.py                     # 工具基類

backend/src/integrations/agent_framework/assistant/
├── manager.py                  # Assistant 管理器
├── files.py                    # 文件處理
└── models.py                   # 數據模型

backend/src/api/v1/code_interpreter/
├── routes.py                   # API 路由
├── visualization.py            # 視覺化處理
└── schemas.py                  # 模型定義
```

**Relationships**:
- **Depends On**: Docker Runtime, File Storage
- **Used By**: Data Analysis, Report Generation, Document Processing

---

### 4.3 LLM Integration

| Feature | Description | Dependencies | API Endpoint |
|---------|-------------|--------------|--------------|
| **Azure OpenAI Client** | Azure OpenAI API 封裝 | Azure SDK | Internal |
| **Response Caching** | LLM 響應緩存 | Redis | Internal |
| **Token Tracking** | Token 使用追蹤 | Metrics Collector | `GET /api/v1/performance/tokens` |
| **Multi-model Support** | 多模型支持 (GPT-4, GPT-4o) | Model Factory | Config |
| **Rate Limiting** | API 調用限流 | Rate Limiter | Internal |

**Related Files**:
```
backend/src/integrations/llm/
├── protocol.py                 # LLM 協議介面
├── factory.py                  # 模型工廠
├── cached.py                   # 緩存 LLM 客戶端
└── mock.py                     # 測試用 Mock 客戶端
```

**Relationships**:
- **Depends On**: Azure OpenAI, Redis Cache
- **Used By**: All Agent Operations, Decision Engine

---

## 5. Session & Claude SDK Features

### 5.1 Session Management

| Feature | Description | Dependencies | API Endpoint |
|---------|-------------|--------------|--------------|
| **Session State** | Session 狀態機管理 | State Machine | `GET /api/v1/sessions/{id}` |
| **Message Tracking** | 消息記錄和追蹤 | Database, Cache | `GET /api/v1/sessions/{id}/messages` |
| **Event Publishing** | 15+ 事件類型發布 | Event Bus | Internal |
| **Dual Storage** | PostgreSQL + Redis 雙存儲 | DB, Cache | Internal |

**Related Files**:
```
backend/src/domain/sessions/
├── models.py                   # Session, Message, ToolCall 模型
├── service.py                  # SessionService
├── cache.py                    # Redis 緩存
├── repository.py               # 數據訪問層
└── events.py                   # SessionEventPublisher
```

**Session State Machine**:
```
┌──────────┐     activate()    ┌──────────┐
│ CREATED  │──────────────────▶│  ACTIVE  │◀─────────┐
└──────────┘                   └────┬─────┘          │
                                    │                │
                       ┌────────────┼────────────┐   │
                       ▼            ▼            ▼   │
                 ┌──────────┐ ┌──────────┐ ┌──────────┐
                 │SUSPENDED │ │ TIMEOUT  │ │  ENDED   │
                 └────┬─────┘ └──────────┘ └──────────┘
                      │ resume()     │
                      └──────────────┘
```

**Relationships**:
- **Depends On**: Database, Redis, Event Bus
- **Used By**: Agent-Session Bridge, Chat API

---

### 5.2 Agent-Session Bridge

| Feature | Description | Dependencies | API Endpoint |
|---------|-------------|--------------|--------------|
| **AgentExecutor** | LLM 交互核心 | LLM Integration | Internal |
| **StreamingHandler** | SSE 串流響應 | HTTP Streaming | `GET /api/v1/sessions/{id}/chat/stream` |
| **ToolCallHandler** | 工具調用處理 | Tool Registry | Internal |
| **WebSocket Handler** | 雙向實時通訊 | WebSocket | `WS /api/v1/sessions/{id}/ws` |
| **ToolApprovalManager** | 工具審批管理 | Redis, HITL | `POST /api/v1/sessions/{id}/approvals` |

**Related Files**:
```
backend/src/domain/sessions/
├── executor.py                 # AgentExecutor
├── streaming.py                # StreamingHandler
├── tool_handler.py             # ToolCallHandler
├── approval.py                 # ToolApprovalManager
└── bridge.py                   # SessionAgentBridge

backend/src/api/v1/sessions/
├── chat.py                     # Chat API
├── websocket.py                # WebSocket Handler
├── routes.py                   # REST Routes
└── schemas.py                  # Pydantic Schemas
```

**Relationships**:
- **Depends On**: Session Management, LLM Integration, Tool Registry
- **Used By**: Chat Applications, Interactive Agents

---

### 5.3 File Processing

| Feature | Description | Dependencies | API Endpoint |
|---------|-------------|--------------|--------------|
| **Document Analyzer** | 文檔內容分析 | LLM, OCR | Internal |
| **Image Analyzer** | 圖像內容分析 | Multimodal LLM | Internal |
| **Code Analyzer** | 代碼分析 | Code Interpreter | Internal |
| **Data Analyzer** | 數據集分析 | Pandas, Analysis Tools | Internal |
| **Code Generator** | 代碼生成 | LLM | Internal |
| **Report Generator** | 報告生成 (MD, HTML) | Template Engine | Internal |
| **Data Exporter** | 數據導出 (CSV, JSON, Excel) | Export Libraries | Internal |

**Related Files**:
```
backend/src/domain/sessions/files/
├── analyzer.py                 # FileAnalyzer 路由器
├── document_analyzer.py        # 文檔分析
├── image_analyzer.py           # 圖像分析
├── code_analyzer.py            # 代碼分析
├── data_analyzer.py            # 數據分析
├── generator.py                # FileGenerator 路由器
├── code_generator.py           # 代碼生成
├── report_generator.py         # 報告生成
└── data_exporter.py            # 數據導出
```

**Relationships**:
- **Depends On**: LLM Integration, Code Interpreter
- **Used By**: Document Processing Pipeline, Data Analysis

---

### 5.4 Claude SDK Integration

| Feature | Description | Dependencies | API Endpoint |
|---------|-------------|--------------|--------------|
| **ClaudeSDKClient** | Claude SDK 核心封裝 | Claude API | `POST /api/v1/claude-sdk/query` |
| **ToolRegistry** | 工具註冊和管理 | Tool Schema | `GET /api/v1/claude-sdk/tools` |
| **HookManager** | Hook 生命週期管理 | Hook Pipeline | `GET /api/v1/claude-sdk/hooks` |
| **HybridOrchestrator** | 混合編排 (Agent + Claude) | Orchestration | `POST /api/v1/claude-sdk/hybrid` |
| **MCP Integration** | MCP 協議整合 | MCP Servers | `GET /api/v1/claude-sdk/mcp/servers` |

**Related Files**:
```
backend/src/integrations/claude_sdk/
├── client.py                   # ClaudeSDKClient
├── query.py                    # Query API
├── session.py                  # Session 管理
├── config.py                   # 配置
├── types.py                    # 類型定義
└── exceptions.py               # 異常處理

├── tools/
│   ├── registry.py             # ToolRegistry
│   ├── file_tools.py           # 文件工具
│   ├── command_tools.py        # 命令工具
│   └── web_tools.py            # Web 工具

├── hooks/
│   ├── base.py                 # HookManager
│   ├── approval.py             # 審批 Hook
│   ├── audit.py                # 審計 Hook
│   ├── rate_limit.py           # 限流 Hook
│   └── sandbox.py              # 沙箱 Hook

├── mcp/
│   ├── manager.py              # MCP Manager
│   ├── stdio.py                # STDIO 傳輸
│   ├── http.py                 # HTTP 傳輸
│   └── discovery.py            # 服務發現

└── hybrid/
    ├── orchestrator.py         # HybridOrchestrator
    ├── capability.py           # 能力分析
    ├── selector.py             # Agent 選擇器
    └── synchronizer.py         # 狀態同步
```

**Relationships**:
- **Depends On**: Claude API, MCP Protocol
- **Used By**: Hybrid Orchestration, Advanced AI Tasks

---

## 6. MCP Protocol & Servers

### 6.1 MCP Core

| Feature | Description | Dependencies | API Endpoint |
|---------|-------------|--------------|--------------|
| **MCP Client** | MCP 協議客戶端 | Transport Layer | Internal |
| **Transport Layer** | STDIO/HTTP 傳輸 | Network | Internal |
| **Server Registry** | MCP Server 註冊表 | Redis | `GET /api/v1/mcp/servers` |
| **Config Loader** | 配置加載器 | File System | Internal |
| **Permission System** | 權限控制 | RBAC | Internal |
| **Audit Logger** | 操作審計 | Audit Service | Internal |

**Related Files**:
```
backend/src/integrations/mcp/
├── core/
│   ├── client.py               # MCP 客戶端
│   ├── transport.py            # 傳輸層
│   └── types.py                # 類型定義

├── registry/
│   ├── server_registry.py      # Server 註冊表
│   └── config_loader.py        # 配置加載

└── security/
    ├── permissions.py          # 權限系統
    └── audit.py                # 審計日誌
```

---

### 6.2 MCP Servers

| Server | Description | Tools Count | Security |
|--------|-------------|-------------|----------|
| **Shell Server** | 命令行執行 | 5 | Whitelist/Blacklist, Dangerous Pattern Blocking |
| **Filesystem Server** | 文件系統操作 | 6 | Sandbox, Blocked Patterns, Size Limits |
| **SSH Server** | SSH 遠程連接 | 6 | Connection Pool, Key Auth, Host Whitelist |
| **LDAP Server** | 目錄服務查詢 | 4 | TLS Support, Read-only Mode |
| **Azure Server** | Azure 資源管理 | 15+ | Azure RBAC Integration |

**Server Details**:

#### Shell Server
```
backend/src/integrations/mcp/servers/shell/
├── executor.py                 # ShellExecutor (安全控制)
├── tools.py                    # 工具定義
└── server.py                   # MCP Server 入口

Tools:
├── execute_command             # 執行命令
├── run_script                  # 執行腳本
├── get_environment             # 獲取環境變量
├── check_command_exists        # 檢查命令存在
└── get_working_directory       # 獲取工作目錄

Security:
├── Command Whitelist           # 允許的命令列表
├── Command Blacklist           # 禁止的命令列表
├── Dangerous Patterns          # 危險模式攔截 (rm -rf, fork bombs, wget|sh)
├── Timeout Limits              # 執行超時限制
└── Output Size Limits          # 輸出大小限制
```

#### Filesystem Server
```
backend/src/integrations/mcp/servers/filesystem/
├── sandbox.py                  # FilesystemSandbox (路徑驗證)
├── tools.py                    # 工具定義
└── server.py                   # MCP Server 入口

Tools:
├── read_file                   # 讀取文件
├── write_file                  # 寫入文件
├── list_directory              # 列出目錄
├── search_files                # 搜索文件
├── get_file_info               # 獲取文件信息
└── delete_file                 # 刪除文件

Security:
├── Path Validation             # 路徑驗證 (防止目錄穿越)
├── Blocked Patterns            # 敏感文件攔截 (.env, *.pem, *.key)
├── File Size Limits            # 文件大小限制
└── Permission Flags            # 寫入/刪除權限開關
```

#### SSH Server
```
backend/src/integrations/mcp/servers/ssh/
├── client.py                   # SSHClient (連接池)
├── tools.py                    # 工具定義
└── server.py                   # MCP Server 入口

Tools:
├── connect                     # 建立連接
├── execute_remote              # 遠程執行命令
├── upload_file                 # SFTP 上傳
├── download_file               # SFTP 下載
├── list_remote_directory       # 列出遠程目錄
└── disconnect                  # 斷開連接

Security:
├── Connection Pooling          # 連接池管理
├── Key Authentication          # 密鑰認證優先
├── Password Authentication     # 密碼認證 (可選)
├── Host Whitelist              # 主機白名單
└── Host Blacklist              # 主機黑名單
```

#### LDAP Server
```
backend/src/integrations/mcp/servers/ldap/
├── client.py                   # LDAPClient (連接池)
├── tools.py                    # 工具定義
└── server.py                   # MCP Server 入口

Tools:
├── search_users                # 搜索用戶
├── search_groups               # 搜索群組
├── get_user_details            # 獲取用戶詳情
└── get_group_members           # 獲取群組成員

Security:
├── TLS/SSL Support             # 安全連接
├── Connection Pooling          # 連接池管理
└── Read-only Mode              # 只讀模式 (默認)
```

#### Azure Server
```
backend/src/integrations/mcp/servers/azure/
├── client.py                   # Azure Client
├── server.py                   # MCP Server 入口
└── tools/
    ├── vm.py                   # VM 管理工具
    ├── resource.py             # 資源管理工具
    ├── monitor.py              # 監控工具
    ├── network.py              # 網絡工具
    └── storage.py              # 存儲工具

Tool Categories:
├── VM Tools (5)                # 啟動/停止/重啟/列表/狀態
├── Resource Tools (4)          # 列表/標籤/刪除/移動
├── Monitor Tools (3)           # 指標/日誌/警報
├── Network Tools (2)           # NSG/VNet
└── Storage Tools (3)           # Blob/Container/Account
```

**Relationships**:
- **Depends On**: MCP Core, Permission System
- **Used By**: Claude SDK, Tool Execution Pipeline

---

## 7. Human-in-the-Loop Features

### 7.1 Checkpoint System

| Feature | Description | Dependencies | API Endpoint |
|---------|-------------|--------------|--------------|
| **Checkpoint Creation** | 創建執行檢查點 | Database | `POST /api/v1/checkpoints` |
| **Checkpoint Storage** | 檢查點存儲管理 | PostgreSQL, Redis | Internal |
| **State Snapshot** | 執行狀態快照 | Serialization | Internal |
| **Checkpoint Restoration** | 檢查點恢復 | State Machine | `POST /api/v1/checkpoints/{id}/restore` |

**Related Files**:
```
backend/src/domain/checkpoints/
├── storage.py                  # CheckpointStorage
└── service.py                  # CheckpointService

backend/src/integrations/agent_framework/
├── checkpoint.py               # 框架層檢查點
└── multiturn/
    └── checkpoint_storage.py   # 多輪對話檢查點
```

---

### 7.2 Approval Workflow

| Feature | Description | Dependencies | API Endpoint |
|---------|-------------|--------------|--------------|
| **Approval Request** | 發起審批請求 | Notification | `POST /api/v1/checkpoints/{id}/request-approval` |
| **Approve/Reject** | 審批/拒絕操作 | State Machine | `POST /api/v1/checkpoints/{id}/approve` |
| **Timeout Handling** | 審批超時處理 | Scheduler | Config |
| **Escalation Logic** | 升級邏輯 | Notification | Config |
| **Audit Trail** | 審批審計追蹤 | Audit Logger | Internal |

**Related Files**:
```
backend/src/integrations/agent_framework/core/
├── approval.py                 # 審批邏輯
└── approval_workflow.py        # 審批工作流

backend/src/domain/workflows/executors/
└── approval.py                 # 審批執行器

backend/src/domain/workflows/
└── resume_service.py           # 恢復服務
```

**Approval Flow**:
```
┌──────────────────────────────────────────────────────────────────────┐
│                        Approval Workflow                              │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────┐     ┌──────────────┐     ┌──────────┐     ┌──────────┐ │
│  │Execution│────▶│ Checkpoint   │────▶│ Approval │────▶│  Result  │ │
│  │ Pause   │     │ Created      │     │ Pending  │     │ Resume   │ │
│  └─────────┘     └──────────────┘     └────┬─────┘     └──────────┘ │
│                                             │                        │
│                        ┌────────────────────┼────────────────────┐   │
│                        ▼                    ▼                    ▼   │
│                  ┌──────────┐         ┌──────────┐         ┌────────┐│
│                  │ Approved │         │ Rejected │         │Timeout ││
│                  │ (Resume) │         │ (Cancel) │         │(Escal.)││
│                  └──────────┘         └──────────┘         └────────┘│
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

**Relationships**:
- **Depends On**: Checkpoint System, Notification Service, State Machine
- **Used By**: High-risk Operations, Sensitive Data Access

---

## 8. Platform Services

### 8.1 Audit Logging

| Feature | Description | Dependencies | API Endpoint |
|---------|-------------|--------------|--------------|
| **Operation Logging** | 操作日誌記錄 | Database | Internal |
| **Query Interface** | 審計日誌查詢 | Elasticsearch (opt.) | `GET /api/v1/audit/logs` |
| **Retention Policy** | 日誌保留策略 | Scheduler | Config |
| **Export** | 日誌導出 | File System | `GET /api/v1/audit/export` |

**Related Files**:
```
backend/src/domain/audit/
└── logger.py                   # AuditLogger

backend/src/api/v1/audit/
├── routes.py                   # API 路由
└── schemas.py                  # 模型定義
```

---

### 8.2 Cache Management

| Feature | Description | Dependencies | API Endpoint |
|---------|-------------|--------------|--------------|
| **LLM Response Cache** | LLM 響應緩存 | Redis | Internal |
| **Session Cache** | Session 數據緩存 | Redis | Internal |
| **Cache Invalidation** | 緩存失效管理 | Redis | `DELETE /api/v1/cache/{key}` |
| **Cache Statistics** | 緩存統計 | Redis | `GET /api/v1/cache/stats` |

**Related Files**:
```
backend/src/api/v1/cache/
├── routes.py                   # API 路由
└── schemas.py                  # 模型定義

backend/src/integrations/llm/
└── cached.py                   # CachedLLMClient
```

---

### 8.3 DevTools & Tracing

| Feature | Description | Dependencies | API Endpoint |
|---------|-------------|--------------|--------------|
| **Execution Tracing** | 執行追蹤 | Tracer | `GET /api/v1/devtools/trace/{id}` |
| **Debug Mode** | 調試模式 | Config | Config |
| **Performance Profiling** | 性能分析 | Profiler | `GET /api/v1/devtools/profile/{id}` |

**Related Files**:
```
backend/src/domain/devtools/
└── tracer.py                   # ExecutionTracer

backend/src/api/v1/devtools/
├── routes.py                   # API 路由
└── schemas.py                  # 模型定義
```

---

### 8.4 Learning Service

| Feature | Description | Dependencies | API Endpoint |
|---------|-------------|--------------|--------------|
| **Pattern Learning** | 從執行歷史學習模式 | ML Models | Internal |
| **Feedback Integration** | 整合用戶反饋 | Feedback Store | `POST /api/v1/learning/feedback` |
| **Model Update** | 模型更新 | ML Pipeline | Admin |

**Related Files**:
```
backend/src/domain/learning/
└── service.py                  # LearningService

backend/src/api/v1/learning/
├── routes.py                   # API 路由
└── schemas.py                  # 模型定義
```

---

### 8.5 Notifications

| Feature | Description | Dependencies | API Endpoint |
|---------|-------------|--------------|--------------|
| **Teams Integration** | Microsoft Teams 通知 | Teams API | Internal |
| **Approval Notifications** | 審批通知 | Teams, Email | Internal |
| **Alert Notifications** | 警報通知 | Teams, Email | Internal |

**Related Files**:
```
backend/src/domain/notifications/
└── teams.py                    # TeamsNotifier

backend/src/api/v1/notifications/
├── routes.py                   # API 路由
└── schemas.py                  # 模型定義
```

---

### 8.6 Performance Monitor

| Feature | Description | Dependencies | API Endpoint |
|---------|-------------|--------------|--------------|
| **Metrics Collection** | 指標收集 | Prometheus (opt.) | Internal |
| **Token Usage Tracking** | Token 使用追蹤 | Counter | `GET /api/v1/performance/tokens` |
| **Latency Tracking** | 延遲追蹤 | Histogram | `GET /api/v1/performance/latency` |
| **Dashboard Data** | 儀表板數據 | Aggregation | `GET /api/v1/performance/dashboard` |

**Related Files**:
```
backend/src/api/v1/performance/
└── routes.py                   # API 路由
```

---

### 8.7 Dashboard API

| Feature | Description | Dependencies | API Endpoint |
|---------|-------------|--------------|--------------|
| **Overview Stats** | 概覽統計 | Aggregation | `GET /api/v1/dashboard/overview` |
| **Recent Activity** | 近期活動 | Database | `GET /api/v1/dashboard/activity` |
| **System Health** | 系統健康狀態 | Health Checks | `GET /api/v1/dashboard/health` |

**Related Files**:
```
backend/src/api/v1/dashboard/
└── routes.py                   # API 路由
```

---

## 9. External Connectors

### 9.1 Connector Registry

| Feature | Description | Dependencies | API Endpoint |
|---------|-------------|--------------|--------------|
| **Connector Registration** | 連接器註冊 | Database | `POST /api/v1/connectors` |
| **Connector Discovery** | 連接器發現 | Registry | `GET /api/v1/connectors` |
| **Credential Management** | 憑證管理 | Vault | Admin |

**Related Files**:
```
backend/src/domain/connectors/
├── base.py                     # BaseConnector
└── registry.py                 # ConnectorRegistry
```

---

### 9.2 ServiceNow Connector

| Feature | Description | Dependencies | API Endpoint |
|---------|-------------|--------------|--------------|
| **Incident Management** | 事件管理 | ServiceNow API | Internal |
| **Change Management** | 變更管理 | ServiceNow API | Internal |
| **CMDB Query** | CMDB 查詢 | ServiceNow API | Internal |

**Related Files**:
```
backend/src/domain/connectors/
└── servicenow.py               # ServiceNowConnector
```

---

### 9.3 Dynamics 365 Connector

| Feature | Description | Dependencies | API Endpoint |
|---------|-------------|--------------|--------------|
| **CRM Operations** | CRM 操作 | Dynamics API | Internal |
| **Entity CRUD** | 實體 CRUD | Dynamics API | Internal |
| **Workflow Trigger** | 工作流觸發 | Dynamics API | Internal |

**Related Files**:
```
backend/src/domain/connectors/
└── dynamics365.py              # Dynamics365Connector
```

---

### 9.4 SharePoint Connector

| Feature | Description | Dependencies | API Endpoint |
|---------|-------------|--------------|--------------|
| **Document Operations** | 文檔操作 | SharePoint API | Internal |
| **List Operations** | 列表操作 | SharePoint API | Internal |
| **Site Operations** | 站點操作 | SharePoint API | Internal |

**Related Files**:
```
backend/src/domain/connectors/
└── sharepoint.py               # SharePointConnector
```

---

## 10. Configuration & Management

### 10.1 Prompt Templates

| Feature | Description | Dependencies | API Endpoint |
|---------|-------------|--------------|--------------|
| **Template CRUD** | 模板管理 | Database | `POST/GET/PUT/DELETE /api/v1/prompts` |
| **Variable Substitution** | 變量替換 | Template Engine | Internal |
| **Version Control** | 模板版本控制 | Versioning | Internal |

**Related Files**:
```
backend/src/domain/prompts/
└── template.py                 # PromptTemplate

backend/src/api/v1/prompts/
├── routes.py                   # API 路由
└── schemas.py                  # 模型定義
```

---

### 10.2 Workflow Templates

| Feature | Description | Dependencies | API Endpoint |
|---------|-------------|--------------|--------------|
| **Template Library** | 模板庫 | Database | `GET /api/v1/templates` |
| **Template Instantiation** | 模板實例化 | Workflow Engine | `POST /api/v1/templates/{id}/instantiate` |
| **Custom Templates** | 自定義模板 | Template Service | `POST /api/v1/templates` |

**Related Files**:
```
backend/src/domain/templates/
├── models.py                   # 模板模型
└── service.py                  # TemplateService

backend/src/api/v1/templates/
├── routes.py                   # API 路由
└── schemas.py                  # 模型定義
```

---

### 10.3 Webhook Triggers

| Feature | Description | Dependencies | API Endpoint |
|---------|-------------|--------------|--------------|
| **Webhook Registration** | Webhook 註冊 | Database | `POST /api/v1/triggers/webhooks` |
| **Event Dispatch** | 事件分發 | Event Bus | Internal |
| **Signature Verification** | 簽名驗證 | Crypto | Internal |

**Related Files**:
```
backend/src/domain/triggers/
└── webhook.py                  # WebhookTrigger

backend/src/api/v1/triggers/
├── routes.py                   # API 路由
└── schemas.py                  # 模型定義
```

---

### 10.4 Version Control

| Feature | Description | Dependencies | API Endpoint |
|---------|-------------|--------------|--------------|
| **Workflow Versioning** | 工作流版本控制 | Database | `GET /api/v1/versioning/{entity}/{id}` |
| **Rollback** | 版本回滾 | Version Store | `POST /api/v1/versioning/{id}/rollback` |
| **Diff View** | 版本差異 | Diff Engine | `GET /api/v1/versioning/{id}/diff` |

**Related Files**:
```
backend/src/domain/versioning/
└── service.py                  # VersioningService

backend/src/api/v1/versioning/
├── routes.py                   # API 路由
└── schemas.py                  # 模型定義
```

---

### 10.5 Scenario Routing

| Feature | Description | Dependencies | API Endpoint |
|---------|-------------|--------------|--------------|
| **Intent Classification** | 意圖分類 | LLM | Internal |
| **Workflow Selection** | 工作流選擇 | Router | `POST /api/v1/routing/route` |
| **Fallback Handling** | 降級處理 | Config | Internal |

**Related Files**:
```
backend/src/domain/routing/
└── scenario_router.py          # ScenarioRouter

backend/src/api/v1/routing/
├── routes.py                   # API 路由
└── schemas.py                  # 模型定義
```

---

## 11. Feature Dependency Matrix

### 11.1 Core Dependencies

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           FEATURE DEPENDENCY MATRIX                                  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  Infrastructure Layer (基礎設施)                                                     │
│  ══════════════════════════════                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                              │
│  │  PostgreSQL  │  │    Redis     │  │   RabbitMQ   │                              │
│  │  (Persist)   │  │   (Cache)    │  │  (Messaging) │                              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                              │
│         │                 │                 │                                        │
│         └────────────┬────┴─────────────────┘                                       │
│                      ▼                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                        Core Services (核心服務)                              │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │   │
│  │  │    Agent     │  │   Workflow   │  │  Execution   │  │   Session    │     │   │
│  │  │   Service    │  │   Service    │  │   Service    │  │   Service    │     │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │   │
│  └─────────┼─────────────────┼─────────────────┼─────────────────┼─────────────┘   │
│            │                 │                 │                 │                  │
│            └────────────┬────┴────────────┬────┴────────────┬────┘                  │
│                         ▼                 ▼                 ▼                       │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                      Orchestration (編排層)                                  │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │   │
│  │  │GroupChat │ │ Handoff  │ │Concurrent│ │  Nested  │ │ Planning │          │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘          │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                     │                                               │
│                                     ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                       AI & Tools (AI 與工具)                                 │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │   │
│  │  │     LLM      │  │   Decision   │  │    Code      │  │   Claude     │     │   │
│  │  │ Integration  │  │    Engine    │  │ Interpreter  │  │     SDK      │     │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘     │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                     │                                               │
│                                     ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                       MCP Protocol (MCP 協議)                                │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐           │   │
│  │  │  Shell  │  │Filesys. │  │   SSH   │  │  LDAP   │  │  Azure  │           │   │
│  │  │ Server  │  │ Server  │  │ Server  │  │ Server  │  │ Server  │           │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘           │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 11.2 Cross-Feature Dependencies

| Feature | Depends On | Used By |
|---------|------------|---------|
| **Agent Management** | Database, Redis | All Orchestration, Session |
| **Workflow Engine** | Agent, State Machine, Checkpoint | Execution, Orchestration |
| **GroupChat** | Agent, Turn Tracker, Memory | Customer Service, Research |
| **Handoff** | Agent, Capability Registry, Trigger | Task Routing, Escalation |
| **Session Management** | Database, Redis, Event Bus | Chat API, Bridge |
| **Decision Engine** | LLM, Historical Data | Planning, HITL |
| **MCP Servers** | MCP Core, Permission | Claude SDK, Tool Execution |
| **Claude SDK** | Claude API, MCP | Hybrid Orchestration |

---

## 12. Feature Relationship Diagram

### 12.1 Complete Feature Interaction

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              IPA PLATFORM FEATURE RELATIONSHIPS                          │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│                                    ┌───────────────┐                                     │
│                                    │   Frontend    │                                     │
│                                    │  (React 18)   │                                     │
│                                    └───────┬───────┘                                     │
│                                            │                                             │
│                                    ┌───────▼───────┐                                     │
│                                    │   API Layer   │                                     │
│                                    │  (FastAPI)    │                                     │
│                                    └───────┬───────┘                                     │
│            ┌───────────────────────────────┼───────────────────────────────┐             │
│            │                               │                               │             │
│    ┌───────▼───────┐               ┌───────▼───────┐               ┌───────▼───────┐    │
│    │    Agent      │◀─────────────▶│   Workflow    │◀─────────────▶│   Session     │    │
│    │  Management   │               │    Engine     │               │  Management   │    │
│    └───────┬───────┘               └───────┬───────┘               └───────┬───────┘    │
│            │                               │                               │             │
│            │          ┌────────────────────┼────────────────────┐          │             │
│            │          │                    │                    │          │             │
│    ┌───────▼──────────▼───┐    ┌───────────▼───────────┐    ┌───▼──────────▼───────┐    │
│    │     GroupChat        │    │       Handoff         │    │    Concurrent        │    │
│    │  ┌─────────────────┐ │    │  ┌─────────────────┐  │    │  ┌─────────────────┐ │    │
│    │  │ Turn Management │ │    │  │ 3 Policies      │  │    │  │ Parallel Exec   │ │    │
│    │  │ Voting System   │ │    │  │ 6 Triggers      │  │    │  │ Resource Pool   │ │    │
│    │  │ History         │ │    │  │ Capability Match│  │    │  │ Error Isolation │ │    │
│    │  └─────────────────┘ │    │  └─────────────────┘  │    │  └─────────────────┘ │    │
│    └──────────────────────┘    └───────────────────────┘    └──────────────────────┘    │
│                                            │                                             │
│    ┌──────────────────────┐    ┌───────────▼───────────┐    ┌──────────────────────┐    │
│    │   Nested Workflow    │    │   Dynamic Planning    │    │     MultiTurn        │    │
│    │  ┌─────────────────┐ │    │  ┌─────────────────┐  │    │  ┌─────────────────┐ │    │
│    │  │ Sub-workflow    │ │    │  │ Task Decompose  │  │    │  │ Conv. State     │ │    │
│    │  │ Context Prop.   │ │◀───│  │ Plan Adaptation │  │───▶│  │ Memory Persist  │ │    │
│    │  │ Recursive       │ │    │  │ Decision Engine │  │    │  │ Checkpoint      │ │    │
│    │  └─────────────────┘ │    │  └─────────────────┘  │    │  └─────────────────┘ │    │
│    └──────────────────────┘    └───────────────────────┘    └──────────────────────┘    │
│                                            │                                             │
│            ┌───────────────────────────────┼───────────────────────────────┐             │
│            │                               │                               │             │
│    ┌───────▼───────┐               ┌───────▼───────┐               ┌───────▼───────┐    │
│    │     LLM       │◀─────────────▶│   Decision    │◀─────────────▶│    Code       │    │
│    │ Integration   │               │    Engine     │               │  Interpreter  │    │
│    └───────┬───────┘               └───────┬───────┘               └───────┬───────┘    │
│            │                               │                               │             │
│            │          ┌────────────────────┼────────────────────┐          │             │
│            │          │                    │                    │          │             │
│    ┌───────▼──────────▼───┐    ┌───────────▼───────────┐    ┌───▼──────────▼───────┐    │
│    │   Claude SDK         │    │      MCP Protocol     │    │     Tool Registry    │    │
│    │  ┌─────────────────┐ │    │  ┌─────────────────┐  │    │  ┌─────────────────┐ │    │
│    │  │ ClaudeSDKClient │ │    │  │ Server Registry │  │    │  │ Tool Discovery  │ │    │
│    │  │ HybridOrchest.  │◀├────│  │ Permission Sys  │  │───▶│  │ Schema Valid.   │ │    │
│    │  │ Hook Manager    │ │    │  │ Audit Logger    │  │    │  │ Execution Pipe  │ │    │
│    │  └─────────────────┘ │    │  └─────────────────┘  │    │  └─────────────────┘ │    │
│    └──────────────────────┘    └───────────────────────┘    └──────────────────────┘    │
│                                            │                                             │
│            ┌───────────────────────────────┼───────────────────────────────┐             │
│            │                               │                               │             │
│    ┌───────▼───────┐               ┌───────▼───────┐               ┌───────▼───────┐    │
│    │   Checkpoint  │◀─────────────▶│   Approval    │◀─────────────▶│    HITL       │    │
│    │    System     │               │   Workflow    │               │   Controls    │    │
│    └───────────────┘               └───────────────┘               └───────────────┘    │
│                                                                                          │
│    ┌─────────────────────────────────────────────────────────────────────────────┐      │
│    │                           Platform Services                                  │      │
│    │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐    │      │
│    │  │  Audit  │ │  Cache  │ │DevTools │ │Learning │ │ Notify  │ │ Perf.   │    │      │
│    │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘    │      │
│    └─────────────────────────────────────────────────────────────────────────────┘      │
│                                                                                          │
│    ┌─────────────────────────────────────────────────────────────────────────────┐      │
│    │                          External Connectors                                 │      │
│    │  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                    │      │
│    │  │ ServiceNow  │     │Dynamics 365 │     │ SharePoint  │                    │      │
│    │  └─────────────┘     └─────────────┘     └─────────────┘                    │      │
│    └─────────────────────────────────────────────────────────────────────────────┘      │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘

Legend:
──────▶  Direct dependency
◀─────▶  Bidirectional interaction
│        Hierarchical relationship
```

---

## Appendix: Quick Reference

### A. Feature Count by Category

| Category | Count | Key Components |
|----------|-------|----------------|
| Core Engine | 9 | Agent, Workflow, Execution, Tool Registry, State Machine |
| Orchestration | 18 | GroupChat, Handoff, Concurrent, Nested, Planning, MultiTurn |
| AI Enhancement | 8 | Decision Engine, Code Interpreter, LLM Integration |
| Session & Claude SDK | 20 | Session, Bridge, Claude SDK, File Processing, Hooks |
| MCP Protocol & Servers | 12 | Core, 5 Servers, Security |
| Human-in-the-Loop | 6 | Checkpoint, Approval, Tool Approval |
| Platform Services | 7 | Audit, Cache, DevTools, Learning, Notifications, Performance |
| External Connectors | 4 | ServiceNow, Dynamics 365, SharePoint, Registry |
| Configuration | 6 | Prompts, Templates, Triggers, Versioning, Routing |
| **TOTAL** | **65+** | |

### B. API Endpoint Summary

| Category | Endpoint Prefix | Route Count |
|----------|-----------------|-------------|
| Agents | `/api/v1/agents` | 8 |
| Workflows | `/api/v1/workflows` | 10 |
| Executions | `/api/v1/executions` | 6 |
| Sessions | `/api/v1/sessions` | 13 |
| GroupChat | `/api/v1/groupchat` | 5 |
| Handoff | `/api/v1/handoff` | 5 |
| Concurrent | `/api/v1/concurrent` | 5 |
| Nested | `/api/v1/nested` | 4 |
| Planning | `/api/v1/planning` | 4 |
| Claude SDK | `/api/v1/claude-sdk` | 15 |
| MCP | `/api/v1/mcp` | 8 |
| Checkpoints | `/api/v1/checkpoints` | 6 |
| Platform Services | Various | 20+ |
| **TOTAL** | | **100+** |

### C. MCP Server Tool Count

| Server | Tools | Description |
|--------|-------|-------------|
| Shell | 5 | Command execution, scripts |
| Filesystem | 6 | File operations |
| SSH | 6 | Remote operations |
| LDAP | 4 | Directory queries |
| Azure | 15+ | Cloud resource management |
| **TOTAL** | **36+** | |

---

*Document Version: 1.0*
*Last Updated: 2025-12-29*
*Generated for IPA Platform Phase 1-12*
