# Sprint 61: AG-UI Frontend Integration & E2E Testing

## Sprint 概述

**Sprint 目標**: 實現 AG-UI 前端完整組件系統（Chat UI、HITL 審批）、Demo 頁面和 Playwright E2E 測試

**Story Points**: 43 點 (38 原始 + 5 S61-6)
**預估工期**: 1 週

## User Stories

### S61-1: useAGUI 主 Hook (8 pts) ✅ 已完成

**As a** 前端開發者
**I want** 統一的 AG-UI React Hook
**So that** 可以輕鬆整合 SSE 串流、消息管理、工具調用和審批功能

**Acceptance Criteria**:
- [x] SSE 連接管理 (EventSource)
- [x] 15 種事件類型處理
- [x] 消息狀態管理 (messages, addUserMessage)
- [x] 工具調用追蹤 (toolCalls, getToolCall)
- [x] 待審批管理 (pendingApprovals, approveToolCall, rejectToolCall)
- [x] 執行控制 (runAgent, cancelRun)
- [x] 與 useSharedState/useOptimisticState 整合
- [x] 自動重連機制

**Technical Tasks**:
```
frontend/src/hooks/
├── useAGUI.ts           # ✅ 主 Hook (~570 行)
└── index.ts             # ✅ 導出更新

frontend/src/types/
└── ag-ui.ts             # ✅ 類型擴展 (ChatMessage, ToolCallState, etc.)
```

---

### S61-2: Chat 組件 (8 pts)

**As a** 用戶
**I want** 完整的對話界面
**So that** 可以與 AI Agent 進行互動對話

**Acceptance Criteria**:
- [ ] `ChatContainer` 完整對話界面容器
- [ ] `MessageBubble` 消息氣泡 (user/assistant/system/tool)
- [ ] `MessageInput` 輸入框 (支持多行、發送按鈕)
- [ ] `ToolCallCard` 工具調用卡片 (顯示參數、結果、狀態)
- [ ] `StreamingIndicator` 串流指示器 (打字效果)
- [ ] 響應式設計
- [ ] 可訪問性 (ARIA labels)

**Technical Tasks**:
```
frontend/src/components/ag-ui/chat/
├── index.ts                 # Barrel export
├── ChatContainer.tsx        # 完整對話界面 (~150 行)
├── MessageBubble.tsx        # 消息氣泡 (~100 行)
├── MessageInput.tsx         # 輸入框 (~80 行)
├── ToolCallCard.tsx         # 工具調用卡片 (~120 行)
└── StreamingIndicator.tsx   # 串流指示器 (~40 行)
```

**Implementation Details**:
```tsx
// ChatContainer.tsx
interface ChatContainerProps {
  threadId: string;
  tools?: ToolDefinition[];
  mode?: 'auto' | 'workflow' | 'chat' | 'hybrid';
  onError?: (error: Error) => void;
}

export function ChatContainer({
  threadId,
  tools,
  mode = 'auto',
  onError,
}: ChatContainerProps) {
  const {
    messages,
    addUserMessage,
    toolCalls,
    pendingApprovals,
    isStreaming,
    runAgent,
    approveToolCall,
    rejectToolCall,
  } = useAGUI({ threadId, tools, mode });

  // ... 渲染消息列表、輸入框、工具調用卡片
}
```

---

### S61-3: HITL 審批組件 (5 pts)

**As a** 用戶
**I want** 清晰的工具調用審批界面
**So that** 可以在執行敏感操作前進行審批

**Acceptance Criteria**:
- [ ] `ApprovalDialog` 審批對話框 (模態框)
- [ ] `ApprovalBanner` 內嵌審批提示 (非模態)
- [ ] `RiskBadge` 風險等級標籤 (low/medium/high/critical)
- [ ] `ApprovalList` 待審批列表
- [ ] 支持批准/拒絕操作
- [ ] 顯示風險評估和理由
- [ ] 超時倒計時顯示

**Technical Tasks**:
```
frontend/src/components/ag-ui/hitl/
├── index.ts                 # Barrel export
├── ApprovalDialog.tsx       # 審批對話框 (~120 行)
├── ApprovalBanner.tsx       # 內嵌審批提示 (~80 行)
├── RiskBadge.tsx            # 風險等級標籤 (~40 行)
└── ApprovalList.tsx         # 待審批列表 (~80 行)
```

**Implementation Details**:
```tsx
// ApprovalDialog.tsx
interface ApprovalDialogProps {
  approval: PendingApproval;
  onApprove: () => void;
  onReject: () => void;
  onClose: () => void;
}

export function ApprovalDialog({
  approval,
  onApprove,
  onReject,
  onClose,
}: ApprovalDialogProps) {
  // 顯示工具名稱、參數、風險等級、理由
  // 批准/拒絕按鈕
  // 超時倒計時
}
```

---

### S61-4: AG-UI Demo 頁面 (10 pts)

**As a** 開發者
**I want** 完整的 AG-UI 功能展示頁面
**So that** 可以測試和驗證所有 7 個 AG-UI 功能

**Acceptance Criteria**:
- [ ] 主頁面 `AGUIDemoPage` 帶 Tab 切換
- [ ] Feature 1: `AgenticChatDemo` 對話展示
- [ ] Feature 2: `ToolRenderingDemo` 工具結果渲染
- [ ] Feature 3: `HITLDemo` 審批工作流
- [ ] Feature 4: `GenerativeUIDemo` 動態 UI 生成
- [ ] Feature 5: `ToolUIDemo` 工具式 UI
- [ ] Feature 6: `SharedStateDemo` 狀態同步
- [ ] Feature 7: `PredictiveDemo` 預測性更新
- [ ] `EventLogPanel` 事件日誌面板
- [ ] 響應式佈局 (左側 8 cols + 右側 4 cols)

**Technical Tasks**:
```
frontend/src/pages/ag-ui/
├── AGUIDemoPage.tsx         # 主頁面 (~200 行)
└── components/
    ├── index.ts             # Barrel export
    ├── AgenticChatDemo.tsx  # Feature 1 (~100 行)
    ├── ToolRenderingDemo.tsx # Feature 2 (~100 行)
    ├── HITLDemo.tsx         # Feature 3 (~100 行)
    ├── GenerativeUIDemo.tsx # Feature 4 (~100 行)
    ├── ToolUIDemo.tsx       # Feature 5 (~100 行)
    ├── SharedStateDemo.tsx  # Feature 6 (~100 行)
    ├── PredictiveDemo.tsx   # Feature 7 (~100 行)
    └── EventLogPanel.tsx    # 事件日誌 (~120 行)

frontend/src/App.tsx          # 添加 /ag-ui-demo 路由
```

**頁面佈局**:
```
┌─────────────────────────────────────────────────────┐
│  AG-UI Demo                                         │
├───────────────────────────────┬─────────────────────┤
│  [Tab 1] [Tab 2] ... [Tab 7]  │  Event Log Panel    │
│  ─────────────────────────────│  ─────────────────  │
│                               │  [RUN_STARTED]      │
│  Feature Demo Content         │  [TEXT_MESSAGE...]  │
│  (Chat / HITL / State...)     │  [TOOL_CALL...]     │
│                               │  [STATE_DELTA]      │
│                               │                     │
├───────────────────────────────┴─────────────────────┤
│  Status Bar: Connected | Mode: chat | Thread: xxx   │
└─────────────────────────────────────────────────────┘
```

---

### S61-5: Playwright E2E 測試 (7 pts)

**As a** QA 工程師
**I want** 完整的前端 E2E 自動化測試
**So that** 確保所有 UI 功能正確運作

**Acceptance Criteria**:
- [ ] 測試工具和 fixtures 設置
- [ ] Feature 1 測試: 發送消息、串流響應
- [ ] Feature 2 測試: 工具結果渲染 (代碼/JSON/錯誤)
- [ ] Feature 3 測試: 審批對話框、批准/拒絕
- [ ] Feature 4 測試: 進度指示器、模式切換
- [ ] Feature 5 測試: 表單驗證、圖表渲染
- [ ] Feature 6 測試: 狀態同步、衝突解決
- [ ] Feature 7 測試: 樂觀更新、回滾動畫
- [ ] 完整流程整合測試

**Technical Tasks**:
```
frontend/e2e/ag-ui/
├── fixtures.ts              # 測試工具 (~100 行)
├── agentic-chat.spec.ts     # Feature 1 測試 (~80 行)
├── tool-rendering.spec.ts   # Feature 2 測試 (~80 行)
├── hitl.spec.ts             # Feature 3 測試 (~100 行)
├── generative-ui.spec.ts    # Feature 4 測試 (~80 行)
├── tool-ui.spec.ts          # Feature 5 測試 (~100 行)
├── shared-state.spec.ts     # Feature 6 測試 (~80 行)
├── predictive-state.spec.ts # Feature 7 測試 (~80 行)
└── integration.spec.ts      # 完整流程測試 (~100 行)
```

**Implementation Details**:
```typescript
// fixtures.ts
import { test as base, expect } from '@playwright/test';

export const test = base.extend<{
  agUiPage: AGUITestPage;
}>({
  agUiPage: async ({ page }, use) => {
    await page.goto('/ag-ui-demo');
    await use(new AGUITestPage(page));
  },
});

class AGUITestPage {
  constructor(private page: Page) {}

  async sendMessage(text: string) {
    await this.page.fill('[data-testid="message-input"]', text);
    await this.page.click('[data-testid="send-button"]');
  }

  async waitForResponse() {
    await this.page.waitForSelector('[data-testid="assistant-message"]');
  }

  async approveToolCall(toolCallId: string) {
    await this.page.click(`[data-testid="approve-${toolCallId}"]`);
  }
}
```

---

### S61-6: Backend Test Endpoints for Feature 4 & 5 (5 pts) ✅ 已完成

**As a** QA 工程師
**I want** 專用的後端測試端點
**So that** 可以直接驗證 Feature 4 (Generative UI) 和 Feature 5 (Tool-based UI) 功能，無需真實 LLM

**Acceptance Criteria**:
- [x] `POST /api/v1/ag-ui/test/progress` - 測試工作流進度事件
- [x] `POST /api/v1/ag-ui/test/mode-switch` - 測試模式切換事件
- [x] `POST /api/v1/ag-ui/test/ui-component` - 測試 UI 組件生成事件

**Technical Tasks**:
```
backend/src/api/v1/ag_ui/
├── routes.py            # ✅ +3 測試端點 (~230 行)
└── schemas.py           # ✅ +6 新 schemas (~155 行)

scripts/uat/phase_tests/phase_15_ag_ui/
└── phase_15_ag_ui_test.py  # ✅ Feature 4 & 5 測試更新
```

**Implementation Details**:
```python
# Test Endpoints
POST /test/progress      # 進度事件 (Feature 4)
POST /test/mode-switch   # 模式切換 (Feature 4)
POST /test/ui-component  # UI 組件 (Feature 5)

# New Schemas
- TestWorkflowProgressRequest / Response
- TestModeSwitchRequest / Response
- TestUIComponentRequest / Response
```

---

## Dependencies

| 依賴項 | 來源 | 狀態 |
|--------|------|------|
| useSharedState Hook | Sprint 60 | ✅ 已完成 |
| useOptimisticState Hook | Sprint 60 | ✅ 已完成 |
| AG-UI Types (ag-ui.ts) | Sprint 60 | ✅ 已完成 |
| Backend AG-UI API | Sprint 58-60 | ✅ 已完成 |
| Shadcn UI Components | Frontend | ✅ 已安裝 |

## 前端依賴確認

```json
{
  "dependencies": {
    "@radix-ui/react-dialog": "已安裝",
    "@radix-ui/react-tabs": "已安裝",
    "recharts": "已安裝",
    "lucide-react": "已安裝"
  },
  "devDependencies": {
    "@playwright/test": "需確認"
  }
}
```

## Definition of Done

- [ ] S61-1 useAGUI Hook 完成 ✅
- [ ] S61-2 Chat 組件完成並可渲染
- [ ] S61-3 HITL 組件完成並可操作
- [ ] S61-4 Demo 頁面可訪問 (/ag-ui-demo)
- [ ] S61-5 E2E 測試全部通過
- [ ] TypeScript 編譯無錯誤
- [ ] ESLint 無錯誤
- [ ] 組件有 data-testid 供測試使用
- [ ] 響應式設計驗證
