# Phase 15: AG-UI Protocol Integration (AG-UI 協議整合)

## 概述

Phase 15 專注於整合 **AG-UI (Agent-User Interface)** 協議，這是由 CopilotKit 提出的開放、輕量級、事件驅動協議，用於實現 AI Agent 與前端介面的即時通訊。Microsoft Agent Framework 已正式支援此協議。

## 目標

1. **AG-UI Core** - 建立 SSE 端點和事件橋接器
2. **Basic Features** - 實現 Agentic Chat、Tool Rendering、HITL、Generative UI
3. **Advanced Features** - 實現 Tool-based GenUI、Shared State、Predictive State

## 前置條件

- ✅ Phase 13 完成 (Hybrid Core Architecture)
- ✅ Phase 14 完成 (Advanced Hybrid Features)
- ✅ HybridOrchestratorV2 就緒
- ✅ IntentRouter、ContextBridge、UnifiedExecutor 就緒
- ✅ RiskAssessment、ModeSwitcher、UnifiedCheckpoint 就緒

## Sprint 規劃

| Sprint | 名稱 | Story Points | 狀態 |
|--------|------|--------------|------|
| [Sprint 58](./sprint-58-plan.md) | AG-UI Core Infrastructure | 30 點 | ✅ 完成 |
| [Sprint 59](./sprint-59-plan.md) | AG-UI Basic Features (1-4) | 28 點 | ✅ 完成 |
| [Sprint 60](./sprint-60-plan.md) | AG-UI Advanced Features (5-7) & Integration | 27 點 | ✅ 完成 |
| [Sprint 61](./sprint-61-plan.md) | AG-UI Frontend Integration & E2E Testing | 38 點 | 🔄 進行中 |

**後端總計**: 85 Story Points ✅
**前端補充**: 38 Story Points (Sprint 61)
**Phase 15 總計**: 123 Story Points

## AG-UI 7 大核心功能

| # | 功能 | 描述 | 對應後端組件 | Sprint |
|---|------|------|--------------|--------|
| 1 | **Agentic Chat** | 基礎串流對話 + Tool 調用 | HybridOrchestrator | 59 |
| 2 | **Backend Tool Rendering** | 後端執行 Tool，前端渲染結果 | UnifiedToolExecutor | 59 |
| 3 | **Human-in-the-Loop** | 函數審批請求 | RiskAssessment + ApprovalHook | 59 |
| 4 | **Agentic Generative UI** | 長時間操作進度更新 | IntentRouter + ModeSwitcher | 59 |
| 5 | **Tool-based Generative UI** | 自定義 UI 組件 | ToolRegistry | 60 |
| 6 | **Shared State** | 雙向狀態同步 | ContextBridge + UnifiedCheckpoint | 60 |
| 7 | **Predictive State Updates** | 樂觀狀態更新 | ContextBridge + Redis | 60 |

## 架構概覽

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Phase 15: AG-UI Architecture                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                         Frontend (React)                                │ │
│  │                                                                         │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │ │
│  │  │                      AG-UI React Provider                        │   │ │
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐  │   │ │
│  │  │  │ AgentChat   │ │ ToolResult  │ │ Approval    │ │ Progress  │  │   │ │
│  │  │  │ Component   │ │ Renderer    │ │ Dialog      │ │ Indicator │  │   │ │
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘  │   │ │
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                │   │ │
│  │  │  │ Custom UI   │ │ State Sync  │ │ Optimistic  │                │   │ │
│  │  │  │ Generator   │ │ Manager     │ │ Updates     │                │   │ │
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘                │   │ │
│  │  └─────────────────────────────────────────────────────────────────┘   │ │
│  │                                   │                                     │ │
│  │                             SSE Connection                              │ │
│  │                                   │                                     │ │
│  └───────────────────────────────────┼─────────────────────────────────────┘ │
│                                      │                                       │
│  ════════════════════════════════════│═══════════════════════════════════════│
│                                      ▼                                       │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                        Backend (FastAPI)                                │ │
│  │                                                                         │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │ │
│  │  │                    AG-UI Endpoint (NEW)                          │   │ │
│  │  │                                                                  │   │ │
│  │  │  POST /api/v1/ag-ui                                              │   │ │
│  │  │  - SSE streaming response                                        │   │ │
│  │  │  - Thread management                                             │   │ │
│  │  │  - State synchronization                                         │   │ │
│  │  └─────────────────────────────────────────────────────────────────┘   │ │
│  │                                   │                                     │ │
│  │                                   ▼                                     │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │ │
│  │  │              HybridEventBridge (NEW)                             │   │ │
│  │  │                                                                  │   │ │
│  │  │  Phase 13-14 Events ──────────► AG-UI Events                     │   │ │
│  │  │                                                                  │   │ │
│  │  │  ┌─────────────────┐    ┌──────────────────────────────────┐    │   │ │
│  │  │  │ Hybrid Events   │    │ AG-UI Event Types               │    │   │ │
│  │  │  │ ─────────────── │ →  │ ────────────────────────────── │    │   │ │
│  │  │  │ • ExecutionStart│    │ • RunStartedEvent              │    │   │ │
│  │  │  │ • MessageChunk  │    │ • TextMessageContentEvent      │    │   │ │
│  │  │  │ • ToolCall      │    │ • ToolCallStartEvent           │    │   │ │
│  │  │  │ • ApprovalReq   │    │ • ToolCallEndEvent (approval)  │    │   │ │
│  │  │  │ • StateUpdate   │    │ • StateSnapshotEvent           │    │   │ │
│  │  │  │ • ProgressUpdate│    │ • CustomEvent (progress)       │    │   │ │
│  │  │  └─────────────────┘    └──────────────────────────────────┘    │   │ │
│  │  └─────────────────────────────────────────────────────────────────┘   │ │
│  │                                   │                                     │ │
│  │                                   ▼                                     │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │ │
│  │  │              Existing Phase 13-14 Components                     │   │ │
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐  │   │ │
│  │  │  │Intent Router│ │Context      │ │Unified Tool │ │Risk       │  │   │ │
│  │  │  │             │ │Bridge       │ │Executor     │ │Assessment │  │   │ │
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘  │   │ │
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                │   │ │
│  │  │  │Mode Switcher│ │Unified      │ │Hybrid       │                │   │ │
│  │  │  │             │ │Checkpoint   │ │Orchestrator │                │   │ │
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘                │   │ │
│  │  └─────────────────────────────────────────────────────────────────┘   │ │
│  │                                                                         │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## AG-UI 事件類型映射

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        AG-UI Event Type Mapping                           │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  Lifecycle Events                                                         │
│  ─────────────────────────────────────────────────────────────────────── │
│  RunStartedEvent      ← Hybrid: execution_started                         │
│  RunFinishedEvent     ← Hybrid: execution_completed / execution_failed    │
│                                                                           │
│  Text Message Events                                                      │
│  ─────────────────────────────────────────────────────────────────────── │
│  TextMessageStartEvent    ← Hybrid: message_start (role: assistant)       │
│  TextMessageContentEvent  ← Hybrid: message_chunk (streaming delta)       │
│  TextMessageEndEvent      ← Hybrid: message_end                           │
│                                                                           │
│  Tool Call Events                                                         │
│  ─────────────────────────────────────────────────────────────────────── │
│  ToolCallStartEvent   ← Hybrid: tool_call_start                           │
│  ToolCallArgsEvent    ← Hybrid: tool_call_args (streaming arguments)      │
│  ToolCallEndEvent     ← Hybrid: tool_call_end (includes result)           │
│                                                                           │
│  State Events                                                             │
│  ─────────────────────────────────────────────────────────────────────── │
│  StateSnapshotEvent   ← ContextBridge: full_state_sync                    │
│  StateDeltaEvent      ← ContextBridge: incremental_update                 │
│                                                                           │
│  Custom Events                                                            │
│  ─────────────────────────────────────────────────────────────────────── │
│  CustomEvent(progress)    ← Hybrid: workflow_progress, step_completed     │
│  CustomEvent(approval)    ← RiskAssessment: approval_required             │
│  CustomEvent(mode_switch) ← ModeSwitcher: mode_transition                 │
│  CustomEvent(ui_component)← ToolRegistry: custom_ui_render                │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

## 核心組件

### 1. AG-UI Endpoint (Sprint 58)

```python
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from typing import AsyncIterator

router = APIRouter(prefix="/ag-ui", tags=["AG-UI"])

@router.post("/")
async def ag_ui_endpoint(request: Request) -> StreamingResponse:
    """
    AG-UI SSE Endpoint

    接收 AG-UI RunAgentInput，返回 SSE 事件流
    """
    input_data = await request.json()

    # 解析 AG-UI 輸入
    run_input = RunAgentInput(
        thread_id=input_data.get("threadId"),
        run_id=input_data.get("runId"),
        messages=input_data.get("messages", []),
        tools=input_data.get("tools", []),
        state=input_data.get("state"),
        forwarded_props=input_data.get("forwardedProps"),
    )

    # 創建事件流
    async def event_stream() -> AsyncIterator[str]:
        async for event in hybrid_event_bridge.stream_ag_ui_events(run_input):
            yield f"data: {event.model_dump_json()}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
```

### 2. HybridEventBridge (Sprint 58)

```python
from typing import AsyncIterator, Dict, Any
from enum import Enum
from pydantic import BaseModel
from datetime import datetime
import uuid

class AGUIEventType(Enum):
    """AG-UI 事件類型"""
    RUN_STARTED = "RUN_STARTED"
    RUN_FINISHED = "RUN_FINISHED"
    TEXT_MESSAGE_START = "TEXT_MESSAGE_START"
    TEXT_MESSAGE_CONTENT = "TEXT_MESSAGE_CONTENT"
    TEXT_MESSAGE_END = "TEXT_MESSAGE_END"
    TOOL_CALL_START = "TOOL_CALL_START"
    TOOL_CALL_ARGS = "TOOL_CALL_ARGS"
    TOOL_CALL_END = "TOOL_CALL_END"
    STATE_SNAPSHOT = "STATE_SNAPSHOT"
    STATE_DELTA = "STATE_DELTA"
    CUSTOM = "CUSTOM"

class AGUIEvent(BaseModel):
    """AG-UI 事件基礎結構"""
    type: AGUIEventType
    timestamp: datetime

class HybridEventBridge:
    """
    混合事件橋接器

    將 Phase 13-14 的內部事件轉換為 AG-UI 標準事件
    """

    def __init__(
        self,
        orchestrator: HybridOrchestratorV2,
        context_bridge: ContextBridge,
        risk_engine: RiskAssessmentEngine,
    ):
        self.orchestrator = orchestrator
        self.context_bridge = context_bridge
        self.risk_engine = risk_engine

    async def stream_ag_ui_events(
        self,
        run_input: RunAgentInput,
    ) -> AsyncIterator[AGUIEvent]:
        """
        串流 AG-UI 事件

        流程:
        1. 發送 RunStartedEvent
        2. 轉發所有 Hybrid 事件為 AG-UI 格式
        3. 處理 Tool 調用和審批
        4. 同步狀態更新
        5. 發送 RunFinishedEvent
        """
        run_id = run_input.run_id or str(uuid.uuid4())
        thread_id = run_input.thread_id or str(uuid.uuid4())

        # 1. RunStartedEvent
        yield AGUIEvent(
            type=AGUIEventType.RUN_STARTED,
            timestamp=datetime.utcnow(),
            run_id=run_id,
            thread_id=thread_id,
        )

        try:
            # 2. 執行 Hybrid Orchestrator
            async for hybrid_event in self.orchestrator.stream_execute(
                input_messages=run_input.messages,
                tools=run_input.tools,
                state=run_input.state,
            ):
                # 3. 轉換為 AG-UI 事件
                ag_ui_event = self._convert_to_agui(hybrid_event, run_id)
                if ag_ui_event:
                    yield ag_ui_event

            # 4. RunFinishedEvent
            yield AGUIEvent(
                type=AGUIEventType.RUN_FINISHED,
                timestamp=datetime.utcnow(),
                run_id=run_id,
                thread_id=thread_id,
            )

        except Exception as e:
            # 錯誤處理
            yield AGUIEvent(
                type=AGUIEventType.RUN_FINISHED,
                timestamp=datetime.utcnow(),
                run_id=run_id,
                thread_id=thread_id,
                error=str(e),
            )

    def _convert_to_agui(
        self,
        hybrid_event: HybridEvent,
        run_id: str,
    ) -> AGUIEvent | None:
        """將 Hybrid 事件轉換為 AG-UI 事件"""
        match hybrid_event.type:
            case "message_start":
                return TextMessageStartEvent(
                    type=AGUIEventType.TEXT_MESSAGE_START,
                    message_id=hybrid_event.message_id,
                    role="assistant",
                )
            case "message_chunk":
                return TextMessageContentEvent(
                    type=AGUIEventType.TEXT_MESSAGE_CONTENT,
                    message_id=hybrid_event.message_id,
                    delta=hybrid_event.content,
                )
            case "tool_call_start":
                return ToolCallStartEvent(
                    type=AGUIEventType.TOOL_CALL_START,
                    tool_call_id=hybrid_event.tool_call_id,
                    tool_call_name=hybrid_event.tool_name,
                )
            # ... 更多事件轉換
```

### 3. AG-UI React Provider (Sprint 59-60)

```tsx
// frontend/src/providers/AGUIProvider.tsx
import { createContext, useContext, useState, useEffect } from 'react';

interface AGUIState {
  isConnected: boolean;
  currentRunId: string | null;
  messages: AGUIMessage[];
  toolCalls: AGUIToolCall[];
  sharedState: Record<string, any>;
  pendingApprovals: AGUIApproval[];
}

interface AGUIContextValue extends AGUIState {
  sendMessage: (content: string) => Promise<void>;
  approveToolCall: (toolCallId: string) => Promise<void>;
  rejectToolCall: (toolCallId: string) => Promise<void>;
  updateState: (key: string, value: any) => void;
}

const AGUIContext = createContext<AGUIContextValue | null>(null);

export function AGUIProvider({ children, endpoint }: {
  children: React.ReactNode;
  endpoint: string;
}) {
  const [state, setState] = useState<AGUIState>({
    isConnected: false,
    currentRunId: null,
    messages: [],
    toolCalls: [],
    sharedState: {},
    pendingApprovals: [],
  });

  // SSE 連接處理
  const connectSSE = async (input: RunAgentInput) => {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input),
    });

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    while (reader) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const events = chunk.split('\n\n').filter(Boolean);

      for (const eventStr of events) {
        if (eventStr.startsWith('data: ')) {
          const event = JSON.parse(eventStr.slice(6));
          handleAGUIEvent(event);
        }
      }
    }
  };

  // 事件處理
  const handleAGUIEvent = (event: AGUIEvent) => {
    switch (event.type) {
      case 'TEXT_MESSAGE_START':
        setState(prev => ({
          ...prev,
          messages: [...prev.messages, {
            id: event.message_id,
            role: event.role,
            content: '',
          }],
        }));
        break;

      case 'TEXT_MESSAGE_CONTENT':
        setState(prev => ({
          ...prev,
          messages: prev.messages.map(msg =>
            msg.id === event.message_id
              ? { ...msg, content: msg.content + event.delta }
              : msg
          ),
        }));
        break;

      case 'TOOL_CALL_END':
        if (event.requires_approval) {
          setState(prev => ({
            ...prev,
            pendingApprovals: [...prev.pendingApprovals, {
              toolCallId: event.tool_call_id,
              toolName: event.tool_call_name,
              args: event.args,
              riskLevel: event.risk_level,
            }],
          }));
        }
        break;

      case 'STATE_SNAPSHOT':
        setState(prev => ({
          ...prev,
          sharedState: event.state,
        }));
        break;

      case 'STATE_DELTA':
        setState(prev => ({
          ...prev,
          sharedState: {
            ...prev.sharedState,
            ...event.delta,
          },
        }));
        break;
    }
  };

  return (
    <AGUIContext.Provider value={{
      ...state,
      sendMessage: async (content) => {
        await connectSSE({
          messages: [{ role: 'user', content }],
          state: state.sharedState,
        });
      },
      approveToolCall: async (toolCallId) => {
        // 發送審批確認
      },
      rejectToolCall: async (toolCallId) => {
        // 發送審批拒絕
      },
      updateState: (key, value) => {
        setState(prev => ({
          ...prev,
          sharedState: { ...prev.sharedState, [key]: value },
        }));
      },
    }}>
      {children}
    </AGUIContext.Provider>
  );
}

export const useAGUI = () => {
  const context = useContext(AGUIContext);
  if (!context) throw new Error('useAGUI must be used within AGUIProvider');
  return context;
};
```

## 與現有系統整合

| 現有組件 | Phase 15 整合方式 |
|----------|-------------------|
| `HybridOrchestratorV2` | 添加 `stream_execute()` 方法支持事件串流 |
| `ContextBridge` | 擴展支持 StateSnapshot/StateDelta 事件生成 |
| `UnifiedToolExecutor` | 添加 AG-UI 工具結果格式化 |
| `RiskAssessmentEngine` | 整合審批請求到 AG-UI 事件流 |
| `ModeSwitcher` | 發送 CustomEvent(mode_switch) 通知前端 |
| `SessionService` | 支持 AG-UI Thread 管理 |

## 前端組件清單

| 組件 | 功能 | Sprint |
|------|------|--------|
| `AGUIProvider` | React Context Provider | 59 |
| `AgentChat` | 對話介面組件 | 59 |
| `ToolResultRenderer` | 工具結果渲染器 | 59 |
| `ApprovalDialog` | 審批對話框 | 59 |
| `ProgressIndicator` | 進度指示器 | 59 |
| `CustomUIRenderer` | 自定義 UI 渲染器 | 60 |
| `StateSyncManager` | 狀態同步管理器 | 60 |
| `OptimisticStateHook` | 樂觀更新 Hook | 60 |

## 技術棧

| 技術 | 版本 | 用途 |
|------|------|------|
| Python | 3.11+ | 後端 AG-UI Endpoint |
| FastAPI | 0.100+ | SSE Streaming |
| React | 18.x | 前端組件 |
| TypeScript | 5.x | 類型安全 |
| Zustand | 4.x | 狀態管理 |
| React Query | 5.x | 數據獲取 |

## 風險與緩解

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| SSE 連接中斷 | 事件丟失 | 自動重連 + 事件緩存 + 斷點續傳 |
| 事件順序錯亂 | UI 狀態不一致 | 事件序號驗證 + 重播機制 |
| 狀態同步延遲 | 用戶體驗差 | 樂觀更新 + 衝突解決策略 |
| 瀏覽器相容性 | SSE 不支援 | 降級為 WebSocket 或 Long Polling |

## 成功標準

- [ ] AG-UI 事件串流延遲 < 100ms
- [ ] SSE 連接穩定性 > 99.5%
- [ ] 7 大核心功能全部實現
- [ ] 前端組件單元測試覆蓋率 > 80%
- [ ] 現有功能回歸測試 100% 通過

---

**Phase 15 開始時間**: 待 Phase 14 完成
**預估完成時間**: 3 週 (3 Sprints)
