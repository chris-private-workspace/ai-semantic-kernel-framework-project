# Phase 12: Claude Agent SDK 整合

## 概述

Phase 12 專注於將 Claude Agent SDK 整合至 IPA Platform，建立 **Hybrid Agent Architecture**，結合 Microsoft Agent Framework 與 Anthropic Claude Agent SDK 的優勢。

## 目標

1. **Claude Agent SDK 核心整合** - 實現 ClaudeSDKClient、Session 管理、query() API
2. **工具與 Hooks 系統** - 整合 Built-in Tools、實現 Hook 攔截機制
3. **MCP 與混合架構** - MCP Server 整合、雙框架協調器

## Sprint 規劃

| Sprint | 名稱 | Story Points | 狀態 |
|--------|------|--------------|------|
| [Sprint 48](./sprint-48-plan.md) | Core SDK Integration | 35 點 | 📋 計劃中 |
| [Sprint 49](./sprint-49-plan.md) | Tools & Hooks System | 32 點 | 📋 計劃中 |
| [Sprint 50](./sprint-50-plan.md) | MCP & Hybrid Architecture | 38 點 | 📋 計劃中 |

**總計**: 105 Story Points

## 架構概覽

```
┌─────────────────────────────────────────────────────────────────┐
│                     IPA Platform (Hybrid)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────┐     ┌─────────────────────┐           │
│  │ Microsoft Agent     │     │ Claude Agent SDK    │           │
│  │ Framework           │     │                     │           │
│  │                     │     │ ┌─────────────────┐ │           │
│  │ - GroupChatBuilder  │     │ │ ClaudeSDKClient │ │           │
│  │ - HandoffBuilder    │     │ │ - query()       │ │           │
│  │ - ConcurrentBuilder │     │ │ - session       │ │           │
│  │ - PlanningAdapter   │     │ └─────────────────┘ │           │
│  │                     │     │                     │           │
│  └──────────┬──────────┘     │ ┌─────────────────┐ │           │
│             │                │ │ Tools           │ │           │
│             │                │ │ - Read/Write    │ │           │
│             │                │ │ - Bash/Grep     │ │           │
│             │                │ │ - WebSearch     │ │           │
│             ▼                │ └─────────────────┘ │           │
│  ┌──────────────────────┐    │                     │           │
│  │ Hybrid Orchestrator  │◄───┤ ┌─────────────────┐ │           │
│  │                      │    │ │ Hooks           │ │           │
│  │ - Task Router        │    │ │ - Approval      │ │           │
│  │ - Context Sync       │    │ │ - Audit         │ │           │
│  │ - Capability Match   │    │ │ - Sandbox       │ │           │
│  └──────────────────────┘    │ └─────────────────┘ │           │
│             │                │                     │           │
│             ▼                │ ┌─────────────────┐ │           │
│  ┌──────────────────────┐    │ │ MCP Servers     │ │           │
│  │ Unified Agent API    │    │ │ - Postgres      │ │           │
│  │                      │    │ │ - GitHub        │ │           │
│  │ /api/v1/agents/      │    │ │ - Custom        │ │           │
│  │ /api/v1/hybrid/      │    │ └─────────────────┘ │           │
│  └──────────────────────┘    └─────────────────────┘           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 核心組件

### 1. ClaudeSDKClient (Sprint 48)

```python
from claude_sdk import ClaudeSDKClient, query

# One-shot query
result = await query(
    prompt="Analyze this code for security issues",
    tools=["Read", "Grep", "Glob"],
    working_directory="/path/to/project"
)

# Multi-turn session
client = ClaudeSDKClient(
    model="claude-sonnet-4-20250514",
    system_prompt="You are a code reviewer.",
    tools=["Read", "Write", "Edit", "Bash"]
)

session = await client.create_session()
await session.query("Read the authentication module")
await session.query("What security issues do you see?")
```

### 2. Hooks System (Sprint 49)

```python
from claude_sdk import Hook, HookResult

class ApprovalHook(Hook):
    """Require approval for write operations."""

    WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "Bash"}

    async def on_tool_call(self, context: ToolCallContext) -> HookResult:
        if context.tool_name in self.WRITE_TOOLS:
            approved = await self.request_approval(context)
            return HookResult.ALLOW if approved else HookResult.reject("Not approved")
        return HookResult.ALLOW
```

### 3. MCP Integration (Sprint 50)

```python
from claude_sdk.mcp import MCPStdioServer

postgres_mcp = MCPStdioServer(
    name="postgres",
    command="uvx",
    args=["mcp-server-postgres"],
    env={"DATABASE_URL": os.getenv("DATABASE_URL")}
)

client = ClaudeSDKClient(mcp_servers=[postgres_mcp])
```

## 與現有系統整合

| 現有組件 | Claude SDK 整合方式 |
|----------|---------------------|
| SessionService | 共享 Session 狀態，同步對話歷史 |
| AgentExecutor | 路由至 Claude SDK 或 Agent Framework |
| ToolCallHandler | 統一工具調用介面 |
| EventPublisher | 整合 Claude SDK 事件至現有事件系統 |

## 前置條件

- ✅ Phase 11 完成 (Agent-Session Integration)
- ✅ Claude Agent SDK skill 文件建立
- 🔲 Anthropic API Key 配置
- 🔲 Claude SDK Python 套件安裝

## 技術棧

| 技術 | 版本 | 用途 |
|------|------|------|
| claude-sdk | 1.x | Claude Agent SDK Python 套件 |
| @anthropic/claude-sdk | 1.x | Claude Agent SDK TypeScript 套件 |
| mcp | 1.x | Model Context Protocol |
| FastAPI | 0.100+ | API 整合 |
| Redis | 7.x | Session 狀態同步 |

## 文件索引

| 文件 | 說明 |
|------|------|
| [sprint-48-plan.md](./sprint-48-plan.md) | Sprint 48 計劃 - Core SDK Integration |
| [sprint-48-checklist.md](./sprint-48-checklist.md) | Sprint 48 Checklist |
| [sprint-49-plan.md](./sprint-49-plan.md) | Sprint 49 計劃 - Tools & Hooks |
| [sprint-49-checklist.md](./sprint-49-checklist.md) | Sprint 49 Checklist |
| [sprint-50-plan.md](./sprint-50-plan.md) | Sprint 50 計劃 - MCP & Hybrid |
| [sprint-50-checklist.md](./sprint-50-checklist.md) | Sprint 50 Checklist |

---

**Phase 12 開始時間**: 待定
**預估完成時間**: 3 週 (3 Sprints)
