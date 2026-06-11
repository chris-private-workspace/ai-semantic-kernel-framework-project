# Phase 13: Hybrid Core Architecture (混合核心架構)

## 概述

Phase 13 專注於建立 MAF (Microsoft Agent Framework) 與 Claude Agent SDK 的**混合核心架構**，實現真正的框架融合而非獨立執行。

## 目標

1. **Intent Router** - 智能意圖路由，區分 Workflow Mode 與 Chat Mode
2. **Context Bridge** - 跨框架上下文同步與狀態橋接
3. **Unified Execution Layer** - 統一執行層，讓 Claude 處理所有 Tool 執行

## 前置條件

- ✅ Phase 12 完成 (Claude Agent SDK Integration)
- ✅ HybridOrchestrator 基礎架構就緒
- ✅ FrameworkSelector 5 種選擇策略已實現
- ✅ MAF Adapters (GroupChat, Handoff, Concurrent, Nested, Planning) 已就緒

## Sprint 規劃

| Sprint | 名稱 | Story Points | 狀態 |
|--------|------|--------------|------|
| [Sprint 52](./sprint-52-plan.md) | Intent Router & Mode Detection | 35 點 | ✅ 完成 |
| [Sprint 53](./sprint-53-plan.md) | Context Bridge & Sync | 35 點 | ✅ 完成 |
| [Sprint 54](./sprint-54-plan.md) | HybridOrchestrator Refactor | 35 點 | ✅ 完成 |

**總計**: 105 Story Points ✅ 已完成

## 架構概覽

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Phase 13 Architecture                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────┐       │
│  │                      Intent Router (NEW)                      │       │
│  │  ┌─────────────────┐  ┌─────────────────┐                    │       │
│  │  │ Mode Detection  │  │ Complexity      │                    │       │
│  │  │ Algorithm       │  │ Analyzer        │                    │       │
│  │  └────────┬────────┘  └────────┬────────┘                    │       │
│  │           │                    │                              │       │
│  │           ▼                    ▼                              │       │
│  │  ┌─────────────────────────────────────┐                     │       │
│  │  │ Intent Classification               │                     │       │
│  │  │ - WORKFLOW_MODE (MAF 主導)          │                     │       │
│  │  │ - CHAT_MODE (Claude 主導)           │                     │       │
│  │  │ - HYBRID_MODE (動態切換)            │                     │       │
│  │  └─────────────────────────────────────┘                     │       │
│  └──────────────────────────────────────────────────────────────┘       │
│                              │                                           │
│                              ▼                                           │
│  ┌──────────────────────────────────────────────────────────────┐       │
│  │                   Context Bridge (NEW)                        │       │
│  │                                                               │       │
│  │  MAF Context ◄──────────────────────────► Claude Context     │       │
│  │  ┌─────────────┐        Sync Layer        ┌─────────────┐    │       │
│  │  │ Workflow    │ ◄─────────────────────► │ Session     │    │       │
│  │  │ State       │                          │ History     │    │       │
│  │  │ Checkpoints │                          │ Tool Calls  │    │       │
│  │  │ Agent State │                          │ Context     │    │       │
│  │  └─────────────┘                          └─────────────┘    │       │
│  └──────────────────────────────────────────────────────────────┘       │
│                              │                                           │
│                              ▼                                           │
│  ┌──────────────────────────────────────────────────────────────┐       │
│  │              HybridOrchestrator (REFACTORED)                  │       │
│  │                                                               │       │
│  │  ┌─────────────────────────────────────────────────────┐     │       │
│  │  │          Unified Tool Execution Layer               │     │       │
│  │  │                                                     │     │       │
│  │  │  MAF Workflow ───┐                                  │     │       │
│  │  │                  │──► Claude Tool Executor          │     │       │
│  │  │  Claude Session ─┘    (All tools via Claude)        │     │       │
│  │  │                                                     │     │       │
│  │  └─────────────────────────────────────────────────────┘     │       │
│  │                                                               │       │
│  │  Tool Callback: MAF → Claude → Result → MAF                  │       │
│  └──────────────────────────────────────────────────────────────┘       │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## 核心組件

### 1. Intent Router (Sprint 52)

```python
from enum import Enum
from typing import Optional
from pydantic import BaseModel

class ExecutionMode(Enum):
    WORKFLOW_MODE = "workflow"      # MAF 主導，適合多步驟流程
    CHAT_MODE = "chat"              # Claude 主導，適合自由對話
    HYBRID_MODE = "hybrid"          # 動態切換，根據上下文決定

class IntentAnalysis(BaseModel):
    mode: ExecutionMode
    confidence: float               # 0.0 - 1.0
    reasoning: str
    suggested_framework: str        # "maf" | "claude" | "hybrid"
    complexity_score: float         # 0.0 - 1.0
    requires_multi_agent: bool
    requires_persistence: bool

class IntentRouter:
    """
    智能意圖路由器 - 決定使用 Workflow Mode 還是 Chat Mode

    決策因素:
    - 任務複雜度分析
    - 多代理需求檢測
    - 持久化需求評估
    - 用戶歷史偏好
    """

    async def analyze_intent(
        self,
        user_input: str,
        session_context: Optional[SessionContext] = None,
        history: Optional[List[Message]] = None,
    ) -> IntentAnalysis:
        """分析用戶意圖，決定執行模式"""
        ...

    async def should_switch_mode(
        self,
        current_mode: ExecutionMode,
        new_input: str,
        execution_state: ExecutionState,
    ) -> tuple[bool, Optional[ExecutionMode]]:
        """判斷是否需要切換執行模式"""
        ...
```

### 2. Context Bridge (Sprint 53)

```python
from dataclasses import dataclass
from typing import Dict, Any, List

@dataclass
class MAFContext:
    """Microsoft Agent Framework 上下文"""
    workflow_id: str
    current_step: int
    agent_states: Dict[str, Any]
    checkpoint_data: Dict[str, Any]
    pending_approvals: List[str]

@dataclass
class ClaudeContext:
    """Claude Agent SDK 上下文"""
    session_id: str
    conversation_history: List[Message]
    tool_call_history: List[ToolCall]
    current_context: Dict[str, Any]

class ContextBridge:
    """
    跨框架上下文橋接器

    職責:
    - MAF Checkpoint ↔ Claude Session 狀態同步
    - Tool 執行結果在兩框架間傳遞
    - 對話歷史統一管理
    """

    async def sync_to_claude(
        self,
        maf_context: MAFContext,
    ) -> ClaudeContext:
        """將 MAF 上下文同步到 Claude"""
        ...

    async def sync_to_maf(
        self,
        claude_context: ClaudeContext,
    ) -> MAFContext:
        """將 Claude 上下文同步回 MAF"""
        ...

    async def merge_contexts(
        self,
        maf_context: MAFContext,
        claude_context: ClaudeContext,
    ) -> HybridContext:
        """合併兩框架上下文"""
        ...
```

### 3. Unified Execution Layer (Sprint 54)

```python
class UnifiedToolExecutor:
    """
    統一 Tool 執行層 - 所有 Tool 執行通過 Claude

    無論是 MAF Workflow 還是 Claude Session，
    所有 Tool 調用都由 Claude 統一處理。
    """

    def __init__(
        self,
        claude_client: ClaudeSDKClient,
        tool_registry: ToolRegistry,
        hook_manager: HookManager,
    ):
        self.claude = claude_client
        self.registry = tool_registry
        self.hooks = hook_manager

    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        source: str,  # "maf" | "claude"
        context: HybridContext,
    ) -> ToolResult:
        """
        統一執行 Tool

        流程:
        1. Hook 前處理 (Approval, Audit, etc.)
        2. Tool 執行
        3. 結果同步回源框架
        4. Hook 後處理
        """
        ...

class HybridOrchestratorV2:
    """
    重構後的混合編排器

    改進:
    - 統一執行層取代獨立執行器
    - Intent Router 整合
    - Context Bridge 整合
    """

    def __init__(self, ...):
        self.intent_router = IntentRouter()
        self.context_bridge = ContextBridge()
        self.unified_executor = UnifiedToolExecutor(...)

    async def execute(
        self,
        request: HybridRequest,
    ) -> HybridResult:
        # 1. 分析意圖，決定模式
        intent = await self.intent_router.analyze_intent(request.input)

        # 2. 根據模式執行
        if intent.mode == ExecutionMode.WORKFLOW_MODE:
            return await self._execute_workflow_mode(request, intent)
        elif intent.mode == ExecutionMode.CHAT_MODE:
            return await self._execute_chat_mode(request, intent)
        else:
            return await self._execute_hybrid_mode(request, intent)
```

## 與現有系統整合

| 現有組件 | Phase 13 整合方式 |
|----------|-------------------|
| `HybridOrchestrator` | 重構為 V2，整合 Intent Router 和 Context Bridge |
| `FrameworkSelector` | 保留，作為 Intent Router 的輔助決策 |
| `SessionAgentBridge` | 連接 Context Bridge，實現 Session↔Workflow 狀態同步 |
| `CheckpointStorage` | 擴展結構，支持 ClaudeContext 存儲 |
| `ToolRegistry` | 整合至 UnifiedToolExecutor |

## 技術棧

| 技術 | 版本 | 用途 |
|------|------|------|
| Python | 3.11+ | 後端實現 |
| FastAPI | 0.100+ | API 整合 |
| Redis | 7.x | 上下文快取、狀態同步 |
| Pydantic | 2.x | 資料模型驗證 |

## 風險與緩解

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| Intent 分類錯誤 | 執行模式不當 | 添加 confidence 閾值，低信心度時詢問用戶 |
| 上下文同步延遲 | 狀態不一致 | 實現樂觀鎖和版本控制 |
| 執行層單點故障 | 所有 Tool 失效 | 添加 fallback 到原生執行器 |

## 成功標準

- [ ] Intent Router 分類準確率 > 90%
- [ ] Context Bridge 同步延遲 < 100ms
- [ ] 統一執行層 Tool 成功率 > 99%
- [ ] 現有功能回歸測試 100% 通過

---

**Phase 13 開始時間**: 待 Phase 12 完成
**預估完成時間**: 3 週 (3 Sprints)

---

## Hotfix 記錄

### 2026-01-07: LLM 連接修復

**問題**: API 路由層 `core_routes.py` 中的 `get_orchestrator()` 沒有傳入 `claude_executor`，導致 `HybridOrchestratorV2._claude_executor = None`，Chat Mode 返回模擬響應 `[CHAT_MODE] Processed: ...` 而非真實 LLM 響應。

**根本原因**:
- Phase 13 設計正確，但 API 路由層實現遺漏了 Claude SDK 連接
- `orchestrator_v2.py` 當 `_claude_executor = None` 時會 fallback 到模擬模式

**修復**:
- 新增 `backend/src/api/v1/hybrid/dependencies.py` - Claude 依賴注入層
  - `get_claude_client()` - ClaudeSDKClient singleton
  - `get_claude_executor()` - 可注入的 executor 函數
- 修改 `backend/src/api/v1/hybrid/core_routes.py` - 注入 `claude_executor`
  - 導入 `get_claude_executor` 並傳入 `HybridOrchestratorV2`

**影響**:
- ✅ Chat Mode 現在調用真實 Claude API
- ✅ 向後兼容：若 ANTHROPIC_API_KEY 未配置，自動 fallback 到模擬模式
- ✅ 日誌記錄執行模式 (REAL vs SIMULATION)
