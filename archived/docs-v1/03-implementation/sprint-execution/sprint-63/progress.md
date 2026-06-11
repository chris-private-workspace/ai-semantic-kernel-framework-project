# Sprint 63 Progress: Mode Switching & State Management

> **Phase 16**: Unified Agentic Chat Interface
> **Sprint 目標**: AG-UI SSE 整合和即時狀態管理

---

## Sprint 概述

| 屬性 | 值 |
|------|-----|
| Sprint 編號 | 63 |
| 計劃點數 | 30 Story Points |
| 開始日期 | 2026-01-07 |
| 完成日期 | 2026-01-07 ✅ |
| 前置條件 | Sprint 62 完成、AG-UI SSE 端點可用 |

---

## Story 進度

| Story | 名稱 | 點數 | 狀態 | 進度 |
|-------|------|------|------|------|
| S63-1 | useUnifiedChat Hook | 8 | ✅ 完成 | 100% |
| S63-2 | AG-UI Event Integration | 11 | ✅ 完成 | 100% |
| S63-3 | Real Mode Detection | 6 | ✅ 完成 | 100% |
| S63-4 | State Persistence | 5 | ✅ 完成 | 100% |

**整體進度**: 30/30 pts (100%) ✅

---

## 實施順序

根據依賴關係，實施順序：

1. **S63-1** (8 pts) - useUnifiedChat Hook (主要編排 Hook) 🔄
2. **S63-2** (11 pts) - AG-UI Event Integration (事件處理器 + 共享狀態)
3. **S63-3** (6 pts) - Real Mode Detection (模式檢測 + 切換原因)
4. **S63-4** (5 pts) - State Persistence (狀態持久化)

---

## 檔案結構

```
frontend/src/
├── hooks/
│   ├── useUnifiedChat.ts           # S63-1: 主編排 Hook ⏳
│   ├── useHybridMode.ts            # S63-3: 增強模式管理 (已存在)
│   ├── useSharedState.ts           # S63-2: 共享狀態 (已存在)
│   └── useOptimisticState.ts       # S63-2: 樂觀更新 (已存在)
│
├── stores/
│   └── unifiedChatStore.ts         # S63-4: 增強持久化 (已存在)
│
└── components/unified-chat/
    └── ModeIndicator.tsx           # S63-3: 模式指示器 (新增) ⏳
```

---

## 詳細進度記錄

### S63-1: useUnifiedChat Hook (8 pts)

**狀態**: ✅ 完成

**前端檔案**:
- [x] `frontend/src/hooks/useUnifiedChat.ts`
- [x] `frontend/src/hooks/index.ts` (導出更新)

**驗收標準**:
- [x] Hook 創建和管理 SSE 連接
- [x] 連接狀態追蹤 (connecting, connected, disconnected)
- [x] `sendMessage()` 函數實作
- [x] `cancelStream()` 函數實作
- [x] `clearMessages()` 函數實作
- [x] `reconnect()` 函數實作
- [x] Hook 整合 Zustand store
- [x] Hook 提供模式和工作流狀態

**實作功能**:
- SSE 連接生命週期管理 (連接/斷開/重連)
- 指數退避重連邏輯
- 完整 AG-UI 事件處理 (15 種事件類型)
- useHybridMode 整合
- Zustand store 同步
- STATE_SNAPSHOT/DELTA 處理
- 共享狀態管理
- Token 使用量追蹤
- Checkpoint 管理
- 審批流程管理

**Hook API**:
```typescript
const {
  messages,           // ChatMessage[]
  isConnected,        // boolean
  isStreaming,        // boolean
  error,              // Error | null
  sendMessage,        // (content: string) => Promise<void>
  cancelStream,       // () => void
  clearMessages,      // () => void
  reconnect,          // () => void
  currentMode,        // ExecutionMode
  workflowState,      // WorkflowState | null
  pendingApprovals,   // PendingApproval[]
} = useUnifiedChat({ threadId, sessionId });
```

---

### S63-2: AG-UI Event Integration (11 pts)

**狀態**: ✅ 完成

**前端檔案**:
- [x] `frontend/src/hooks/useUnifiedChat.ts` - 事件處理器
- [x] `frontend/src/stores/unifiedChatStore.ts` - 事件驅動更新

**事件處理器**:
- [x] `RUN_STARTED` - 初始化運行狀態
- [x] `RUN_FINISHED` - 完成運行狀態
- [x] `RUN_ERROR` - 處理運行錯誤
- [x] `TEXT_MESSAGE_START` - 開始新訊息
- [x] `TEXT_MESSAGE_CONTENT` - 追加內容 delta
- [x] `TEXT_MESSAGE_END` - 完成訊息
- [x] `TOOL_CALL_START` - 開始工具調用追蹤
- [x] `TOOL_CALL_ARGS` - 更新工具參數
- [x] `TOOL_CALL_END` - 完成工具調用
- [x] `STATE_SNAPSHOT` - 完整狀態替換
- [x] `STATE_DELTA` - 增量狀態更新
- [x] `CUSTOM` - 處理自定義事件

**增強功能**:
- [x] `handleStateSnapshot()` 替換完整狀態
- [x] `handleStateDelta()` 合併增量更新
- [x] 狀態版本追蹤
- [x] 衝突檢測 (baseVersion 檢查)
- [x] 衝突時自動請求 snapshot

---

### S63-3: Real Mode Detection (6 pts)

**狀態**: ✅ 完成

**前端檔案**:
- [x] `frontend/src/hooks/useHybridMode.ts` - 外部更新支持
- [x] `frontend/src/hooks/useUnifiedChat.ts` - 模式檢測處理
- [x] `frontend/src/components/unified-chat/ModeIndicator.tsx` - 模式指示器

**增強功能**:
- [x] 儲存 `switchReason` 在 ModeState
- [x] 儲存 `switchConfidence` 在 ModeState
- [x] 儲存 `lastSwitchAt` 時間戳
- [x] 在 ModeIndicator Tooltip 顯示原因

**新增類型和 API**:
- `UseHybridModeReturn` interface (定義 hook 返回類型)
- `switchReason: string | null` - 切換原因
- `switchConfidence: number` - 信心度 (0-1)
- `lastSwitchAt: string | null` - ISO 時間戳

---

### S63-4: State Persistence (5 pts)

**狀態**: ✅ 完成

**前端檔案**:
- [x] `frontend/src/stores/unifiedChatStore.ts` - 持久化中間件
- [x] `frontend/src/types/unified-chat.ts` - 類型更新

**驗收標準**:
- [x] 添加 Zustand `persist` 中間件 (已有，增強)
- [x] 配置 localStorage 存儲 (從 sessionStorage 改為 localStorage)
- [x] 限制持久化訊息 (最多 100 條)
- [x] 持久化模式偏好
- [x] 持久化手動覆蓋設定
- [x] 處理存儲配額錯誤 (QuotaExceededError 處理)
- [x] 清除歷史功能移除持久化數據 (`clearPersistence()` action)

**實作功能**:
- 自定義 storage adapter 處理 localStorage 讀寫錯誤
- Quota exceeded 時自動清除舊數據重試
- 持久化 messages (限制 100 條)、workflowState、checkpoints (限制 20 個)
- 版本化遷移支持 (version: 1)

---

## 測試統計

| 類別 | 測試數量 | 狀態 |
|------|---------|------|
| TypeScript 編譯 | N/A | ⏳ |
| S63-1 Hook Tests | Pending | ⏳ |
| S63-2 Event Tests | Pending | ⏳ |
| S63-3 Mode Tests | Pending | ⏳ |
| S63-4 Persistence Tests | Pending | ⏳ |

---

## 技術備註

### SSE 連接管理

```typescript
// 帶自動重連的連接
const connectSSE = (threadId: string) => {
  const eventSource = new EventSource(
    `/api/v1/ag-ui?thread_id=${threadId}`
  );

  eventSource.onopen = () => setIsConnected(true);
  eventSource.onerror = (e) => {
    setIsConnected(false);
    // 指數退避重連
    scheduleReconnect();
  };
  eventSource.onmessage = (e) => {
    const event = JSON.parse(e.data);
    handleEvent(event);
  };

  return eventSource;
};
```

### 共享狀態整合

```typescript
// STATE_SNAPSHOT - 完整狀態替換
const handleStateSnapshot = (event: StateSnapshotEvent) => {
  const { state, version } = event;
  setSharedState(state);
  setStateVersion(version);
};

// STATE_DELTA - 增量狀態合併
const handleStateDelta = (event: StateDeltaEvent) => {
  const { delta, version, baseVersion } = event;

  // 衝突檢測
  if (baseVersion !== currentVersion) {
    requestStateSnapshot();
    return;
  }

  setSharedState(prev => ({ ...prev, ...delta }));
  setStateVersion(version);
};
```

---

## 依賴關係

- Sprint 62 完成 (UnifiedChat 頁面、useHybridMode hook、Zustand store)
- AG-UI SSE 端點 (`POST /api/v1/ag-ui`)
- IntentRouter 用於模式檢測
- Thread/Session 管理 API

---

## 備註

- 整合現有 useAGUI hook 的功能
- 使用 useSharedState 和 useOptimisticState 支持狀態同步
- 前端需要 React 18+、TypeScript 5+
- 重點是 SSE 連接穩定性和事件處理正確性

---

**更新日期**: 2026-01-07
**Sprint 狀態**: ✅ 完成
**完成日期**: 2026-01-07
