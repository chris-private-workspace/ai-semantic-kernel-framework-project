# Sprint 65 Progress: Metrics, Checkpoints & Polish

> **Phase 16**: Unified Agentic Chat Interface
> **Sprint 目標**: 完善執行指標、Checkpoint 功能和整體體驗打磨

---

## Sprint 概述

| 屬性 | 值 |
|------|-----|
| Sprint 編號 | 65 |
| 計劃點數 | 24 Story Points |
| 開始日期 | 2026-01-07 |
| 完成日期 | 2026-01-07 |
| 前置條件 | Sprint 62-64 完成、Checkpoint API、AG-UI 事件 |

---

## Story 進度

| Story | 名稱 | 點數 | 狀態 | 進度 |
|-------|------|------|------|------|
| S65-1 | useExecutionMetrics Hook | 6 | ✅ 完成 | 100% |
| S65-2 | Checkpoint Integration | 6 | ✅ 完成 | 100% |
| S65-3 | Error Handling & Recovery | 4 | ✅ 完成 | 100% |
| S65-4 | UI Polish & Accessibility | 4 | ✅ 完成 | 100% |
| S65-5 | CustomUIRenderer Integration | 4 | ✅ 完成 | 100% |

**整體進度**: 24/24 pts (100%) ✅

---

## 實施順序

根據依賴關係，實施順序：

1. **S65-1** (6 pts) - useExecutionMetrics Hook (Token/時間/工具追蹤)
2. **S65-2** (6 pts) - Checkpoint Integration (API 整合 + 恢復流程)
3. **S65-3** (4 pts) - Error Handling & Recovery (SSE 重連 + 錯誤邊界)
4. **S65-4** (4 pts) - UI Polish & Accessibility (動畫 + 鍵盤支持)
5. **S65-5** (4 pts) - CustomUIRenderer Integration (動態 UI 組件)

---

## 檔案結構

```
frontend/src/
├── hooks/
│   ├── useExecutionMetrics.ts     # S65-1: 執行指標 Hook
│   ├── useCheckpoints.ts          # S65-2: Checkpoint Hook
│   └── index.ts                   # 導出更新
│
├── components/unified-chat/
│   ├── ErrorBoundary.tsx          # S65-3: 錯誤邊界
│   ├── ConnectionStatus.tsx       # S65-3: 連接狀態指示
│   ├── StatusBar.tsx              # S65-1: 整合指標顯示 (增強)
│   ├── CheckpointList.tsx         # S65-2: API 整合 (增強)
│   ├── MessageList.tsx            # S65-4/5: 動畫 + 動態 UI (增強)
│   ├── ChatInput.tsx              # S65-4: 鍵盤快捷鍵 (增強)
│   ├── ChatHeader.tsx             # S65-3: 連接指示器 (增強)
│   ├── WorkflowSidePanel.tsx      # S65-4: 過渡動畫 (增強)
│   └── index.ts                   # 導出更新
│
└── api/endpoints/
    └── ag-ui.ts                   # S65-2: Checkpoint 端點 (增強)
```

---

## 詳細進度記錄

### S65-1: useExecutionMetrics Hook (6 pts)

**狀態**: ⬜ 待開始

**前端檔案**:
- [ ] `frontend/src/hooks/useExecutionMetrics.ts`
- [ ] `frontend/src/components/unified-chat/StatusBar.tsx` (整合)

**驗收標準**:
- [ ] Hook 追蹤 Token 使用量 (used, limit, percentage, formatted)
- [ ] Hook 追蹤執行時間 (total, isRunning, formatted)
- [ ] Hook 追蹤工具調用統計 (total, completed, failed, pending)
- [ ] Hook 追蹤訊息統計 (total, user, assistant)
- [ ] 從 AG-UI 事件更新指標
- [ ] `resetMetrics()` 函數
- [ ] `startTimer()` / `stopTimer()` 函數
- [ ] StatusBar 整合顯示

---

### S65-2: Checkpoint Integration (6 pts)

**狀態**: ⬜ 待開始

**前端檔案**:
- [ ] `frontend/src/hooks/useCheckpoints.ts`
- [ ] `frontend/src/components/unified-chat/CheckpointList.tsx` (增強)
- [ ] `frontend/src/api/endpoints/ag-ui.ts` (增強)

**驗收標準**:
- [ ] Hook 從 AG-UI STATE 事件載入 Checkpoints
- [ ] Hook 追蹤當前 Checkpoint
- [ ] `restoreCheckpoint(id)` 呼叫 API
- [ ] 恢復前確認對話框
- [ ] 恢復成功/失敗通知
- [ ] 執行中禁用恢復按鈕
- [ ] 恢復後 UI 更新

**API 端點**:
```typescript
// Restore checkpoint
POST /api/v1/ag-ui/checkpoints/:checkpointId/restore
Response: { success: true, restoredState: {...} }
```

---

### S65-3: Error Handling & Recovery (4 pts)

**狀態**: ⬜ 待開始

**前端檔案**:
- [ ] `frontend/src/components/unified-chat/ErrorBoundary.tsx`
- [ ] `frontend/src/components/unified-chat/ConnectionStatus.tsx`
- [ ] `frontend/src/hooks/useUnifiedChat.ts` (增強)
- [ ] `frontend/src/components/unified-chat/ChatHeader.tsx` (增強)

**驗收標準**:
- [ ] SSE 重連 (指數退避)
- [ ] 最大重試次數限制
- [ ] 手動重連按鈕
- [ ] 網路錯誤檢測和顯示
- [ ] API 錯誤處理
- [ ] 錯誤邊界捕獲崩潰
- [ ] 用戶友好錯誤訊息

**錯誤類型**:
- [ ] CONNECTION_ERROR - SSE 連接失敗
- [ ] API_ERROR - 後端 API 錯誤
- [ ] PARSE_ERROR - JSON 解析錯誤
- [ ] TIMEOUT_ERROR - 請求超時

---

### S65-4: UI Polish & Accessibility (4 pts)

**狀態**: ⬜ 待開始

**前端檔案**:
- [ ] `frontend/src/components/unified-chat/MessageList.tsx` (增強)
- [ ] `frontend/src/components/unified-chat/ChatInput.tsx` (增強)
- [ ] `frontend/src/components/unified-chat/WorkflowSidePanel.tsx` (增強)

**驗收標準**:
- [ ] 訊息出現動畫 (fade + slide)
- [ ] 模式切換過渡動畫
- [ ] 側邊面板滑入/滑出
- [ ] 載入骨架屏狀態
- [ ] 尊重 prefers-reduced-motion
- [ ] Cmd/Ctrl + Enter 發送訊息
- [ ] Escape 關閉對話框
- [ ] Tab 焦點導航
- [ ] ARIA 標籤
- [ ] 螢幕閱讀器公告

---

### S65-5: CustomUIRenderer Integration (4 pts)

**狀態**: ⬜ 待開始

**前端檔案**:
- [ ] `frontend/src/components/unified-chat/MessageList.tsx` (整合)
- [ ] `frontend/src/hooks/useUnifiedChat.ts` (增強)

**驗收標準**:
- [ ] 導入 `CustomUIRenderer` 從 AG-UI 組件
- [ ] ChatMessage 類型添加 `customUI` 欄位
- [ ] 處理 `CUSTOM` 事件的 `RENDER_UI` payload
- [ ] 條件渲染 CustomUIRenderer 或 MessageBubble
- [ ] 實作 `handleFormSubmit()` 回調
- [ ] 實作 `handleUIAction()` 回調
- [ ] 動態 UI 載入和錯誤狀態

**支援的 UI 組件**:
- [ ] DynamicForm - 表單渲染和提交
- [ ] DynamicChart - 圖表視覺化
- [ ] DynamicTable - 表格數據
- [ ] Card - 內容卡片 + 動作

---

## 技術備註

### Token 追蹤邏輯

```typescript
// 從 CUSTOM 事件監聽 Token 更新
const handleCustomEvent = (event: CustomAGUIEvent) => {
  if (event.payload.type === 'TOKEN_UPDATE') {
    updateTokens({
      used: event.payload.tokensUsed,
      limit: event.payload.tokensLimit,
    });
  }
};
```

### 執行計時器

```typescript
const useExecutionTimer = () => {
  const [startTime, setStartTime] = useState<number | null>(null);
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!startTime) return;
    const interval = setInterval(() => {
      setElapsed(Date.now() - startTime);
    }, 100);
    return () => clearInterval(interval);
  }, [startTime]);

  return {
    elapsed,
    isRunning: startTime !== null,
    start: () => setStartTime(Date.now()),
    stop: () => setStartTime(null),
    reset: () => { setStartTime(null); setElapsed(0); },
  };
};
```

### Checkpoint 恢復流程

```
1. 用戶點擊 "Restore"
2. 顯示確認對話框
3. 呼叫恢復 API
4. 後端恢復狀態
5. AG-UI 發送 STATE_SNAPSHOT 事件
6. 前端更新所有狀態
7. 清除 checkpoint 後的訊息
8. 顯示成功通知
```

### SSE 重連邏輯

```typescript
const reconnectSSE = () => {
  const backoffMs = Math.min(1000 * Math.pow(2, retryCount), 30000);
  setTimeout(() => {
    retryCount++;
    connectSSE();
  }, backoffMs);
};
```

### 動畫配置

```typescript
// 尊重 prefers-reduced-motion
const prefersReducedMotion = window.matchMedia(
  '(prefers-reduced-motion: reduce)'
).matches;

const motionConfig = {
  transition: { duration: prefersReducedMotion ? 0 : 0.3 },
  initial: prefersReducedMotion ? {} : { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: prefersReducedMotion ? {} : { opacity: 0, y: -20 },
};
```

---

## 依賴關係

- Sprint 62-64: 所有組件和 Hooks
- Checkpoint API 端點
- AG-UI TOKEN_UPDATE 事件
- Phase 15: CustomUIRenderer 組件

---

**更新日期**: 2026-01-07
**Sprint 狀態**: ✅ 完成
