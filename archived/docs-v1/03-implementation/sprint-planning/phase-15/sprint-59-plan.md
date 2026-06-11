# Sprint 59: AG-UI Basic Features (1-4)

## Sprint 概述

**Sprint 目標**: 實現 AG-UI 前 4 個核心功能：Agentic Chat、Backend Tool Rendering、Human-in-the-Loop、Agentic Generative UI

**Story Points**: 28 點
**預估工期**: 1 週

## User Stories

### S59-1: Agentic Chat (7 pts)

**As a** 前端開發者
**I want** 完整的 Agentic Chat 對話組件
**So that** 用戶可以與 Agent 進行即時串流對話

**Acceptance Criteria**:
- [ ] 後端 `AgenticChatHandler` 整合 HybridOrchestratorV2
- [ ] 前端 `AgentChat` 主組件實現
- [ ] 前端 `Message` 訊息氣泡組件
- [ ] 前端 `ChatInput` 輸入組件
- [ ] 前端 `useAGUI` Hook 實現
- [ ] 支持文字訊息串流顯示
- [ ] 支持工具調用內嵌顯示
- [ ] 單元測試覆蓋率 > 90%

**Technical Tasks**:
```
backend/src/integrations/ag_ui/features/
├── __init__.py
└── agentic_chat.py          # AgenticChatHandler

frontend/src/
├── components/ag-ui/
│   ├── AgentChat.tsx        # 主對話介面
│   ├── Message.tsx          # 訊息氣泡
│   ├── ChatInput.tsx        # 輸入框
│   └── index.ts             # Barrel export
├── hooks/
│   └── useAGUI.ts           # AG-UI Hook
└── providers/
    └── AGUIProvider.tsx     # Context Provider
```

**Implementation Details**:
```python
# backend/src/integrations/ag_ui/features/agentic_chat.py
from typing import AsyncIterator
from src.integrations.hybrid import HybridOrchestratorV2
from src.integrations.ag_ui import HybridEventBridge
from src.integrations.ag_ui.events import AGUIEvent

class AgenticChatHandler:
    """Agentic Chat 功能處理器"""

    def __init__(
        self,
        orchestrator: HybridOrchestratorV2,
        event_bridge: HybridEventBridge,
    ):
        self.orchestrator = orchestrator
        self.event_bridge = event_bridge

    async def handle_chat(
        self,
        run_input: RunAgentInput,
    ) -> AsyncIterator[AGUIEvent]:
        """處理對話請求"""
        # 1. 分析意圖 (使用現有 IntentRouter)
        intent = await self.orchestrator.intent_router.analyze_intent(
            user_input=run_input.messages[-1].content,
            session_context=run_input.state,
        )

        # 2. 執行並串流事件
        async for event in self.orchestrator.stream_execute(
            messages=run_input.messages,
            mode=intent.mode,
        ):
            yield self.event_bridge.convert(event)
```

```tsx
// frontend/src/components/ag-ui/AgentChat.tsx
import { useAGUI } from '@/hooks/useAGUI';
import { Message } from './Message';
import { ChatInput } from './ChatInput';

export function AgentChat() {
  const { messages, sendMessage, isLoading } = useAGUI();

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (
          <Message key={msg.id} message={msg} />
        ))}
        {isLoading && <TypingIndicator />}
      </div>
      <ChatInput onSend={sendMessage} disabled={isLoading} />
    </div>
  );
}
```

---

### S59-2: Backend Tool Rendering (7 pts)

**As a** 後端開發者
**I want** 工具執行結果的標準化渲染系統
**So that** 前端能正確顯示各種類型的工具執行結果

**Acceptance Criteria**:
- [ ] 後端 `ToolRenderingHandler` 整合 UnifiedToolExecutor
- [ ] 支持結果類型自動檢測 (text, json, table, image)
- [ ] 前端 `ToolResultRenderer` 組件
- [ ] 前端 `ToolExecutingIndicator` 狀態組件
- [ ] 前端 `ToolErrorDisplay` 錯誤組件
- [ ] 支持工具執行狀態顯示 (pending, running, success, error)
- [ ] 單元測試覆蓋率 > 90%

**Technical Tasks**:
```
backend/src/integrations/ag_ui/features/
└── tool_rendering.py        # ToolRenderingHandler

frontend/src/components/ag-ui/
├── ToolResultRenderer.tsx   # 結果渲染器
├── ToolExecutingIndicator.tsx  # 執行中指示器
└── ToolErrorDisplay.tsx     # 錯誤顯示
```

**Implementation Details**:
```python
# backend/src/integrations/ag_ui/features/tool_rendering.py
from typing import Any
from src.integrations.hybrid.execution import UnifiedToolExecutor
from src.integrations.ag_ui.events import ToolCallEndEvent, AGUIEventType

class ToolRenderingHandler:
    """後端工具渲染處理器"""

    def __init__(self, unified_executor: UnifiedToolExecutor):
        self.executor = unified_executor

    async def execute_and_format(
        self,
        tool_call: ToolCall,
        context: HybridContext,
    ) -> ToolCallEndEvent:
        """執行工具並格式化結果"""
        result = await self.executor.execute_tool(
            tool_name=tool_call.name,
            arguments=tool_call.args,
            source="ag_ui",
            context=context,
        )

        return ToolCallEndEvent(
            type=AGUIEventType.TOOL_CALL_END,
            tool_call_id=tool_call.id,
            tool_call_name=tool_call.name,
            result=self._format_result(result),
            result_type=self._detect_result_type(result),
        )

    def _detect_result_type(self, result: Any) -> str:
        """檢測結果類型"""
        if isinstance(result, dict):
            if "image_url" in result:
                return "image"
            if "table" in result or "rows" in result:
                return "table"
            return "json"
        return "text"

    def _format_result(self, result: Any) -> dict:
        """格式化結果為前端可渲染格式"""
        return {
            "data": result,
            "formatted": True,
        }
```

```tsx
// frontend/src/components/ag-ui/ToolResultRenderer.tsx
interface ToolResultRendererProps {
  result: any;
  resultType: 'text' | 'json' | 'table' | 'image';
  status: 'pending' | 'running' | 'success' | 'error';
}

export function ToolResultRenderer({
  result,
  resultType,
  status,
}: ToolResultRendererProps) {
  if (status === 'running') {
    return <ToolExecutingIndicator />;
  }

  if (status === 'error') {
    return <ToolErrorDisplay error={result} />;
  }

  switch (resultType) {
    case 'text':
      return <p className="whitespace-pre-wrap">{result}</p>;
    case 'json':
      return (
        <pre className="bg-muted p-2 rounded text-sm overflow-x-auto">
          {JSON.stringify(result, null, 2)}
        </pre>
      );
    case 'table':
      return <DataTable data={result.rows} columns={result.columns} />;
    case 'image':
      return <img src={result.image_url} alt="Tool result" className="max-w-full rounded" />;
    default:
      return <p>{String(result)}</p>;
  }
}
```

---

### S59-3: Human-in-the-Loop (8 pts)

**As a** 系統管理員
**I want** 函數審批請求功能
**So that** 高風險操作能被人工審核後才執行

**Acceptance Criteria**:
- [ ] 後端 `HITLHandler` 整合 RiskAssessmentEngine
- [ ] 後端生成 `approval_required` 自定義事件
- [ ] 後端 `ApprovalStorage` 審批狀態管理
- [ ] `POST /api/v1/ag-ui/approvals/{id}/approve` 端點
- [ ] `POST /api/v1/ag-ui/approvals/{id}/reject` 端點
- [ ] `GET /api/v1/ag-ui/approvals/pending` 端點
- [ ] 前端 `ApprovalDialog` 組件
- [ ] 支持審批/拒絕操作
- [ ] 支持審批超時處理 (預設 5 分鐘)
- [ ] 顯示風險等級和原因
- [ ] 單元測試覆蓋率 > 90%

**Technical Tasks**:
```
backend/src/integrations/ag_ui/features/
└── human_in_loop.py         # HITLHandler, ApprovalStorage

backend/src/api/v1/ag_ui/
└── routes.py                # 新增審批 API 端點

frontend/src/components/ag-ui/
└── ApprovalDialog.tsx       # 審批對話框
```

**Implementation Details**:
```python
# backend/src/integrations/ag_ui/features/human_in_loop.py
from src.integrations.hybrid.risk import RiskAssessmentEngine, RiskLevel
from src.integrations.ag_ui.events import CustomEvent, AGUIEventType

class HITLHandler:
    """Human-in-the-Loop 處理器"""

    def __init__(
        self,
        risk_engine: RiskAssessmentEngine,
        approval_storage: ApprovalStorage,
    ):
        self.risk_engine = risk_engine
        self.approval_storage = approval_storage

    async def check_approval_needed(
        self,
        tool_call: ToolCall,
        context: HybridContext,
    ) -> tuple[bool, RiskAssessment | None]:
        """檢查是否需要審批"""
        assessment = await self.risk_engine.assess(
            tool_name=tool_call.name,
            arguments=tool_call.args,
            context=context,
        )
        needs_approval = assessment.level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        return needs_approval, assessment

    async def create_approval_event(
        self,
        tool_call: ToolCall,
        assessment: RiskAssessment,
        run_id: str,
    ) -> CustomEvent:
        """創建審批請求事件"""
        approval_id = await self.approval_storage.create_pending(
            tool_call_id=tool_call.id,
            tool_name=tool_call.name,
            arguments=tool_call.args,
            risk_level=assessment.level,
            run_id=run_id,
        )

        return CustomEvent(
            type=AGUIEventType.CUSTOM,
            name="approval_required",
            data={
                "approval_id": approval_id,
                "tool_call_id": tool_call.id,
                "tool_name": tool_call.name,
                "arguments": tool_call.args,
                "risk_level": assessment.level.value,
                "risk_score": assessment.score,
                "reasoning": assessment.reasoning,
                "timeout_seconds": 300,
            },
        )

    async def handle_approval_response(
        self,
        approval_id: str,
        approved: bool,
        user_comment: str | None = None,
    ) -> None:
        """處理審批響應"""
        await self.approval_storage.update_status(
            approval_id=approval_id,
            approved=approved,
            user_comment=user_comment,
        )
```

**API Specification**:
```yaml
/api/v1/ag-ui/approvals/{approval_id}/approve:
  post:
    summary: 批准工具調用
    parameters:
      - name: approval_id
        in: path
        required: true
        schema:
          type: string
    responses:
      200:
        description: 批准成功
        content:
          application/json:
            schema:
              type: object
              properties:
                status:
                  type: string
                  enum: [approved]

/api/v1/ag-ui/approvals/{approval_id}/reject:
  post:
    summary: 拒絕工具調用
    parameters:
      - name: approval_id
        in: path
        required: true
        schema:
          type: string
    requestBody:
      content:
        application/json:
          schema:
            type: object
            properties:
              reason:
                type: string
    responses:
      200:
        description: 拒絕成功

/api/v1/ag-ui/approvals/pending:
  get:
    summary: 獲取待審批列表
    responses:
      200:
        description: 待審批列表
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
                properties:
                  approval_id:
                    type: string
                  tool_name:
                    type: string
                  risk_level:
                    type: string
                  created_at:
                    type: string
                    format: date-time
```

---

### S59-4: Agentic Generative UI (6 pts)

**As a** 用戶
**I want** 看到長時間操作的即時進度更新
**So that** 我能了解工作流的執行狀態

**Acceptance Criteria**:
- [ ] 後端 `GenerativeUIHandler` 整合 ModeSwitcher
- [ ] 後端生成 `workflow_progress` 自定義事件
- [ ] 後端生成 `mode_switch` 自定義事件
- [ ] 前端 `ProgressIndicator` 組件
- [ ] 前端 `ModeSwitchNotification` 組件
- [ ] 支持多步驟工作流進度
- [ ] 支持步驟狀態 (pending, running, completed, failed)
- [ ] 單元測試覆蓋率 > 90%

**Technical Tasks**:
```
backend/src/integrations/ag_ui/features/
└── generative_ui.py         # GenerativeUIHandler

frontend/src/components/ag-ui/
├── ProgressIndicator.tsx    # 進度指示器
└── ModeSwitchNotification.tsx  # 模式切換通知
```

**Implementation Details**:
```python
# backend/src/integrations/ag_ui/features/generative_ui.py
from src.integrations.ag_ui.events import CustomEvent, AGUIEventType

class GenerativeUIHandler:
    """Generative UI 處理器"""

    async def emit_progress_event(
        self,
        workflow_id: str,
        current_step: int,
        total_steps: int,
        step_name: str,
        step_status: str,
    ) -> CustomEvent:
        """發送進度事件"""
        return CustomEvent(
            type=AGUIEventType.CUSTOM,
            name="workflow_progress",
            data={
                "workflow_id": workflow_id,
                "current_step": current_step,
                "total_steps": total_steps,
                "step_name": step_name,
                "step_status": step_status,
                "progress_percent": (current_step / total_steps) * 100,
            },
        )

    async def emit_mode_switch_event(
        self,
        from_mode: str,
        to_mode: str,
        reason: str,
    ) -> CustomEvent:
        """發送模式切換事件"""
        return CustomEvent(
            type=AGUIEventType.CUSTOM,
            name="mode_switch",
            data={
                "from_mode": from_mode,
                "to_mode": to_mode,
                "reason": reason,
            },
        )
```

```tsx
// frontend/src/components/ag-ui/ProgressIndicator.tsx
import { Clock, Loader2, CheckCircle, XCircle } from 'lucide-react';

interface WorkflowProgress {
  workflowId: string;
  currentStep: number;
  totalSteps: number;
  stepName: string;
  stepStatus: 'pending' | 'running' | 'completed' | 'failed';
  progressPercent: number;
}

export function ProgressIndicator({ progress }: { progress: WorkflowProgress }) {
  const statusIcons = {
    pending: <Clock className="h-4 w-4 text-muted-foreground" />,
    running: <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />,
    completed: <CheckCircle className="h-4 w-4 text-green-500" />,
    failed: <XCircle className="h-4 w-4 text-red-500" />,
  };

  return (
    <div className="p-4 border rounded-lg bg-muted/50">
      <div className="mb-3">
        <div className="h-2 bg-muted rounded-full overflow-hidden">
          <div
            className="h-full bg-primary transition-all duration-300"
            style={{ width: `${progress.progressPercent}%` }}
          />
        </div>
      </div>
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-2">
          {statusIcons[progress.stepStatus]}
          <span>{progress.stepName}</span>
        </div>
        <span className="text-muted-foreground">
          {progress.currentStep} / {progress.totalSteps}
        </span>
      </div>
    </div>
  );
}
```

---

## Dependencies

| 依賴項 | 來源 | 狀態 |
|--------|------|------|
| HybridEventBridge | Sprint 58 | 📋 待完成 |
| Thread Manager | Sprint 58 | 📋 待完成 |
| AG-UI Event Types | Sprint 58 | 📋 待完成 |
| HybridOrchestratorV2 | Phase 13 | ✅ 已完成 |
| UnifiedToolExecutor | Phase 13 | ✅ 已完成 |
| RiskAssessmentEngine | Phase 14 | ✅ 已完成 |
| ModeSwitcher | Phase 14 | ✅ 已完成 |

## Definition of Done

- [ ] 所有 User Stories 完成
- [ ] 後端單元測試覆蓋率 > 85%
- [ ] 前端組件測試完成
- [ ] 對話流程 E2E 測試通過
- [ ] 審批流程 E2E 測試通過
- [ ] API 文檔更新
- [ ] Code Review 完成
