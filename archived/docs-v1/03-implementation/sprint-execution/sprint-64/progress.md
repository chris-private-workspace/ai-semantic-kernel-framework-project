# Sprint 64 Progress: Approval Flow & Risk Indicators

> **Phase 16**: Unified Agentic Chat Interface
> **Sprint 目標**: 實現完整 HITL 審批流程和風險指示系統

---

## Sprint 概述

| 屬性 | 值 |
|------|-----|
| Sprint 編號 | 64 |
| 計劃點數 | 29 Story Points |
| 開始日期 | 2026-01-07 |
| 完成日期 | 2026-01-07 ✅ |
| 前置條件 | Sprint 62-63 完成、Backend approval API |

---

## Story 進度

| Story | 名稱 | 點數 | 狀態 | 進度 |
|-------|------|------|------|------|
| S64-1 | useApprovalFlow Hook | 10 | ✅ 完成 | 100% |
| S64-2 | ApprovalDialog Component | 7 | ✅ 完成 | 100% |
| S64-3 | Risk Indicator System | 7 | ✅ 完成 | 100% |
| S64-4 | Approval API Integration | 5 | ✅ 完成 | 100% |

**整體進度**: 29/29 pts (100%) ✅

---

## 實施順序

根據依賴關係，實施順序：

1. **S64-1** (10 pts) - useApprovalFlow Hook (核心審批邏輯 + 模式切換確認) ✅
2. **S64-3** (7 pts) - Risk Indicator System (風險視覺化 + 詳情 Tooltip) ✅
3. **S64-2** (7 pts) - ApprovalDialog Component (高風險審批彈窗) ✅
4. **S64-4** (5 pts) - Approval API Integration (後端 API 整合) ✅

---

## 檔案結構

```
frontend/src/
├── hooks/
│   ├── useApprovalFlow.ts           # S64-1: 審批流程 Hook ✅
│   └── index.ts                     # 導出更新 ✅
│
├── components/unified-chat/
│   ├── ApprovalDialog.tsx           # S64-2: 審批彈窗組件 ✅
│   ├── ModeSwitchConfirmDialog.tsx  # S64-1: 模式切換確認彈窗 ✅
│   ├── RiskIndicator.tsx            # S64-3: 風險指示器 ✅
│   └── index.ts                     # 導出更新 ✅
│
├── api/
│   └── endpoints/
│       ├── ag-ui.ts                 # S64-4: 審批 API 端點 ✅
│       └── index.ts                 # 導出更新 ✅
│
└── types/
    └── unified-chat.ts              # 類型 (已有)
```

---

## 詳細進度記錄

### S64-1: useApprovalFlow Hook (10 pts)

**狀態**: ✅ 完成

**前端檔案**:
- [x] `frontend/src/hooks/useApprovalFlow.ts`
- [x] `frontend/src/components/unified-chat/ModeSwitchConfirmDialog.tsx`
- [x] `frontend/src/hooks/index.ts` (導出更新)

**驗收標準**:
- [x] Hook 追蹤 `pendingApprovals` 陣列
- [x] Hook 管理 `dialogApproval` 狀態
- [x] Hook 提供 `isProcessing` 狀態
- [x] `approve(toolCallId)` 函數實作 (含 API 呼叫)
- [x] `reject(toolCallId, reason?)` 函數實作 (含 API 呼叫)
- [x] `dismissDialog()` 函數實作
- [x] 過期審批處理 (timeout handling)
- [x] AG-UI TOOL_CALL 事件整合
- [x] 模式切換確認狀態追蹤
- [x] `modeSwitchPending` 狀態
- [x] `confirmModeSwitch()` 函數實作
- [x] `cancelModeSwitch()` 函數實作

**Hook API**:
```typescript
const {
  pendingApprovals,      // PendingApproval[]
  dialogApproval,        // PendingApproval | null
  isProcessing,          // boolean
  modeSwitchPending,     // ModeSwitchPending | null
  hasPendingApprovals,   // boolean
  highRiskCount,         // number
  criticalRiskCount,     // number
  addPendingApproval,    // (approval) => void
  approve,               // (id) => Promise<void>
  reject,                // (id, reason?) => Promise<void>
  dismissDialog,         // () => void
  showApprovalDialog,    // (approval) => void
  requestModeSwitch,     // (params) => void
  confirmModeSwitch,     // () => void
  cancelModeSwitch,      // () => void
  getApprovalById,       // (id) => PendingApproval | undefined
  clearExpiredApprovals, // () => void
} = useApprovalFlow(options);
```

---

### S64-2: ApprovalDialog Component (7 pts)

**狀態**: ✅ 完成

**前端檔案**:
- [x] `frontend/src/components/unified-chat/ApprovalDialog.tsx`

**驗收標準**:
- [x] 彈窗顯示高/危險風險審批
- [x] 顯示工具名稱和參數
- [x] 顯示風險等級徽章
- [x] 列出風險因素
- [x] 倒數計時器 (timeout)
- [x] 拒絕原因輸入框
- [x] Approve/Reject 按鈕
- [x] 鍵盤可訪問性 (Tab, Enter, Escape)

**組件 Props**:
```typescript
interface ApprovalDialogProps {
  approval: PendingApproval;
  onApprove: () => void;
  onReject: (reason?: string) => void;
  onDismiss: () => void;
  isProcessing?: boolean;
}
```

---

### S64-3: Risk Indicator System (7 pts)

**狀態**: ✅ 完成

**前端檔案**:
- [x] `frontend/src/components/unified-chat/RiskIndicator.tsx`

**驗收標準**:
- [x] 創建 RiskIndicator 組件
- [x] 四種風險等級顏色編碼 (Low/Medium/High/Critical)
- [x] 風險分數顯示 (0-100)
- [x] Tooltip 顯示風險詳情
- [x] 大小變體 (sm/md/lg)
- [x] 高風險時脈衝動畫
- [x] 顯示風險因素列表
- [x] 顯示評估理由

**組件 Props**:
```typescript
interface RiskIndicatorProps {
  level: RiskLevel;          // 'low' | 'medium' | 'high' | 'critical'
  score: number;             // 0-100
  factors?: string[];        // Risk factors list
  reasoning?: string;        // Assessment reasoning
  size?: 'sm' | 'md' | 'lg';
  showScore?: boolean;
  showTooltip?: boolean;
  onClick?: () => void;
  className?: string;
}
```

---

### S64-4: Approval API Integration (5 pts)

**狀態**: ✅ 完成

**前端檔案**:
- [x] `frontend/src/api/endpoints/ag-ui.ts`
- [x] `frontend/src/api/endpoints/index.ts`
- [x] `frontend/src/hooks/useApprovalFlow.ts` (API 整合)

**驗收標準**:
- [x] `aguiApi.approve(toolCallId)` 函數
- [x] `aguiApi.reject(toolCallId, reason)` 函數
- [x] `aguiApi.getPendingApprovals(sessionId)` 函數
- [x] API 錯誤處理
- [x] 樂觀更新實作
- [x] 失敗時回滾

**API 端點**:
```typescript
// Approve endpoint
POST /api/v1/ag-ui/tool-calls/:toolCallId/approve

// Reject endpoint
POST /api/v1/ag-ui/tool-calls/:toolCallId/reject
Body: { reason?: string }

// Get pending approvals
GET /api/v1/ag-ui/sessions/:sessionId/pending-approvals
```

---

## 技術備註

### 審批流程序列

```
1. 後端檢測高風險工具調用
2. AG-UI 發送 TOOL_CALL_START (requiresApproval: true)
3. 前端 addPendingApproval() 添加到列表
4. 若 high/critical 風險 → 自動顯示 ApprovalDialog
5. 用戶批准/拒絕
6. 前端樂觀更新 → 呼叫 API
7. API 成功 → 觸發 onApprovalProcessed callback
8. API 失敗 → 回滾狀態
```

### 風險等級顏色

```typescript
const riskColors = {
  low: 'bg-green-500',      // 綠色
  medium: 'bg-yellow-500',  // 黃色
  high: 'bg-orange-500',    // 橙色 + 脈衝動畫
  critical: 'bg-red-500',   // 紅色 + 脈衝動畫
};
```

### 模式切換確認邏輯

```typescript
// 高信心度 (>=90%) 自動接受
if (confidence >= 0.9) {
  onModeSwitchConfirm(mode);
  return;
}

// 低信心度需要用戶確認
setModeSwitchPending({
  from: currentMode,
  to: mode,
  reason,
  confidence,
});
```

---

## 依賴關係

- Sprint 62: InlineApproval 組件、StatusBar
- Sprint 63: AG-UI 事件處理、useUnifiedChat
- Backend: 審批 API 端點 (`/api/v1/ag-ui/tool-calls/{id}/approve`)

---

**更新日期**: 2026-01-07
**Sprint 狀態**: ✅ 完成
**完成日期**: 2026-01-07
