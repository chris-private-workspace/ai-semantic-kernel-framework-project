# Sprint 105: OrchestrationPanel 整合 + 狀態管理

## 概述

Sprint 105 專注於將 Agent Swarm 可視化組件整合到現有的 OrchestrationPanel 中，並建立完整的狀態管理架構。

## 目標

1. 擴展 OrchestrationPanel 支援 AgentSwarmPanel
2. 實現 useSwarmStatus Zustand Store
3. 實現完整的事件處理流程
4. 優化組件間狀態同步
5. 實現 Swarm 和 Worker 的交互邏輯

## Story Points: 25 點

## 前置條件

- ✅ Sprint 102 完成 (AgentSwarmPanel + WorkerCard)
- ✅ Sprint 103 完成 (WorkerDetailDrawer)
- ✅ Sprint 104 完成 (ExtendedThinking)
- ✅ 現有 OrchestrationPanel 就緒
- ✅ Zustand 狀態管理就緒

## 任務分解

### Story 105-1: Swarm Zustand Store (5h, P0)

**目標**: 實現 Agent Swarm 的 Zustand 狀態管理

**交付物**:
- `frontend/src/stores/swarmStore.ts`

**核心實現**:

```typescript
// swarmStore.ts
import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import { devtools } from 'zustand/middleware';
import {
  AgentSwarmStatus,
  WorkerSummary,
  WorkerDetail,
  WorkerProgressPayload,
  WorkerThinkingPayload,
  WorkerToolCallPayload,
} from '@/components/unified-chat/agent-swarm/types';

interface SwarmState {
  // 狀態
  swarmStatus: AgentSwarmStatus | null;
  selectedWorkerId: string | null;
  selectedWorkerDetail: WorkerDetail | null;
  isDrawerOpen: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  setSwarmStatus: (status: AgentSwarmStatus | null) => void;
  updateWorkerProgress: (payload: WorkerProgressPayload) => void;
  updateWorkerThinking: (payload: WorkerThinkingPayload) => void;
  updateWorkerToolCall: (payload: WorkerToolCallPayload) => void;
  completeWorker: (workerId: string, status: 'completed' | 'failed', result?: unknown) => void;

  selectWorker: (worker: WorkerSummary | null) => void;
  setWorkerDetail: (detail: WorkerDetail | null) => void;
  openDrawer: () => void;
  closeDrawer: () => void;

  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

const initialState = {
  swarmStatus: null,
  selectedWorkerId: null,
  selectedWorkerDetail: null,
  isDrawerOpen: false,
  isLoading: false,
  error: null,
};

export const useSwarmStore = create<SwarmState>()(
  devtools(
    immer((set, get) => ({
      ...initialState,

      setSwarmStatus: (status) =>
        set((state) => {
          state.swarmStatus = status;
        }),

      updateWorkerProgress: (payload) =>
        set((state) => {
          if (!state.swarmStatus) return;

          const workerIndex = state.swarmStatus.workers.findIndex(
            (w) => w.workerId === payload.workerId
          );
          if (workerIndex === -1) return;

          state.swarmStatus.workers[workerIndex] = {
            ...state.swarmStatus.workers[workerIndex],
            progress: payload.progress,
            currentAction: payload.currentAction,
            status: payload.status as any,
          };

          // 重新計算整體進度
          state.swarmStatus.overallProgress = Math.round(
            state.swarmStatus.workers.reduce((sum, w) => sum + w.progress, 0) /
              state.swarmStatus.workers.length
          );
        }),

      updateWorkerThinking: (payload) =>
        set((state) => {
          // 如果選中的 Worker 正在更新，同時更新 detail
          if (
            state.selectedWorkerDetail &&
            state.selectedWorkerDetail.workerId === payload.workerId
          ) {
            const lastThinking =
              state.selectedWorkerDetail.thinkingHistory[
                state.selectedWorkerDetail.thinkingHistory.length - 1
              ];

            if (
              lastThinking &&
              payload.thinkingContent.startsWith(lastThinking.content)
            ) {
              // 增量更新
              state.selectedWorkerDetail.thinkingHistory[
                state.selectedWorkerDetail.thinkingHistory.length - 1
              ] = {
                content: payload.thinkingContent,
                timestamp: payload.timestamp,
                tokenCount: payload.tokenCount,
              };
            } else {
              // 新的 thinking block
              state.selectedWorkerDetail.thinkingHistory.push({
                content: payload.thinkingContent,
                timestamp: payload.timestamp,
                tokenCount: payload.tokenCount,
              });
            }
          }
        }),

      updateWorkerToolCall: (payload) =>
        set((state) => {
          if (!state.swarmStatus) return;

          const workerIndex = state.swarmStatus.workers.findIndex(
            (w) => w.workerId === payload.workerId
          );
          if (workerIndex !== -1) {
            state.swarmStatus.workers[workerIndex].toolCallsCount += 1;
          }

          // 更新 detail
          if (
            state.selectedWorkerDetail &&
            state.selectedWorkerDetail.workerId === payload.workerId
          ) {
            const existingIndex = state.selectedWorkerDetail.toolCalls.findIndex(
              (t) => t.toolCallId === payload.toolCallId
            );

            if (existingIndex !== -1) {
              // 更新現有的
              state.selectedWorkerDetail.toolCalls[existingIndex] = {
                ...state.selectedWorkerDetail.toolCalls[existingIndex],
                status: payload.status as any,
                outputResult: payload.outputResult,
                error: payload.error,
                durationMs: payload.durationMs,
              };
            } else {
              // 添加新的
              state.selectedWorkerDetail.toolCalls.push({
                toolCallId: payload.toolCallId,
                toolName: payload.toolName,
                status: payload.status as any,
                inputArgs: payload.inputArgs,
                outputResult: payload.outputResult,
                error: payload.error,
                durationMs: payload.durationMs,
              });
            }
          }
        }),

      completeWorker: (workerId, status, result) =>
        set((state) => {
          if (!state.swarmStatus) return;

          const workerIndex = state.swarmStatus.workers.findIndex(
            (w) => w.workerId === workerId
          );
          if (workerIndex !== -1) {
            state.swarmStatus.workers[workerIndex].status = status;
            state.swarmStatus.workers[workerIndex].progress = 100;
          }
        }),

      selectWorker: (worker) =>
        set((state) => {
          state.selectedWorkerId = worker?.workerId || null;
          state.selectedWorkerDetail = null; // 清除舊的 detail
        }),

      setWorkerDetail: (detail) =>
        set((state) => {
          state.selectedWorkerDetail = detail;
        }),

      openDrawer: () =>
        set((state) => {
          state.isDrawerOpen = true;
        }),

      closeDrawer: () =>
        set((state) => {
          state.isDrawerOpen = false;
          state.selectedWorkerId = null;
          state.selectedWorkerDetail = null;
        }),

      setLoading: (loading) =>
        set((state) => {
          state.isLoading = loading;
        }),

      setError: (error) =>
        set((state) => {
          state.error = error;
        }),

      reset: () => set(initialState),
    })),
    { name: 'swarm-store' }
  )
);
```

**驗收標準**:
- [ ] Store 正確定義
- [ ] 所有 actions 正常工作
- [ ] immer 不可變更新正確
- [ ] DevTools 支援

### Story 105-2: 擴展 OrchestrationPanel (6h, P0)

**目標**: 將 AgentSwarmPanel 整合到現有的 OrchestrationPanel

**交付物**:
- 修改 `frontend/src/components/unified-chat/OrchestrationPanel.tsx`

**整合實現**:

```tsx
// OrchestrationPanel.tsx (擴展)
import { FC, useCallback } from 'react';
import { AgentSwarmPanel, WorkerDetailDrawer, WorkerSummary } from './agent-swarm';
import { useSwarmStore } from '@/stores/swarmStore';
// ... 其他 imports

interface OrchestrationPanelProps {
  // ... 現有 props
  showSwarmPanel?: boolean;
}

export const OrchestrationPanel: FC<OrchestrationPanelProps> = ({
  // ... 現有 props
  showSwarmPanel = true,
}) => {
  // Swarm Store
  const {
    swarmStatus,
    selectedWorkerId,
    isDrawerOpen,
    selectWorker,
    openDrawer,
    closeDrawer,
  } = useSwarmStore();

  // Worker 點擊處理
  const handleWorkerClick = useCallback((worker: WorkerSummary) => {
    selectWorker(worker);
    openDrawer();
  }, [selectWorker, openDrawer]);

  // 關閉 Drawer
  const handleDrawerClose = useCallback(() => {
    closeDrawer();
  }, [closeDrawer]);

  return (
    <div className="space-y-4">
      {/* 現有組件 */}
      {/* Workflow Progress */}
      {/* Routing Decision */}
      {/* Risk Assessment */}

      {/* 🆕 Agent Swarm Panel */}
      {showSwarmPanel && swarmStatus && (
        <AgentSwarmPanel
          swarmStatus={swarmStatus}
          onWorkerClick={handleWorkerClick}
        />
      )}

      {/* 🆕 Worker Detail Drawer */}
      <WorkerDetailDrawer
        open={isDrawerOpen}
        onClose={handleDrawerClose}
        swarmId={swarmStatus?.swarmId || ''}
        worker={
          swarmStatus?.workers.find((w) => w.workerId === selectedWorkerId) ||
          null
        }
      />

      {/* Tool Calls */}
      {/* Checkpoints */}
    </div>
  );
};
```

**驗收標準**:
- [ ] AgentSwarmPanel 正確顯示
- [ ] Worker 點擊正確打開 Drawer
- [ ] 與現有組件和諧共存
- [ ] 響應式佈局正確

### Story 105-3: SSE 事件處理整合 (5h, P0)

**目標**: 將 Swarm SSE 事件與 Store 連接

**交付物**:
- 修改 `frontend/src/components/unified-chat/hooks/useAgentExecution.ts` (或類似)

**整合實現**:

```tsx
// useAgentExecution.ts (擴展)
import { useEffect } from 'react';
import { useSwarmStore } from '@/stores/swarmStore';
import { useSwarmEvents } from '../agent-swarm/hooks/useSwarmEvents';

export function useAgentExecution(sessionId: string) {
  const eventSource = useEventSource(`/api/v1/ag-ui?session_id=${sessionId}`);

  // Swarm Store actions
  const {
    setSwarmStatus,
    updateWorkerProgress,
    updateWorkerThinking,
    updateWorkerToolCall,
    completeWorker,
  } = useSwarmStore();

  // 處理 Swarm 事件
  useSwarmEvents(eventSource, {
    onSwarmCreated: (payload) => {
      setSwarmStatus({
        swarmId: payload.swarmId,
        sessionId: payload.sessionId,
        mode: payload.mode as any,
        status: 'initializing',
        totalWorkers: payload.workers.length,
        workers: payload.workers.map((w: any, i: number) => ({
          ...w,
          status: 'pending',
          progress: 0,
          toolCallsCount: 0,
          createdAt: new Date().toISOString(),
        })),
        overallProgress: 0,
        createdAt: payload.createdAt,
        metadata: {},
      });
    },

    onSwarmStatusUpdate: (payload) => {
      setSwarmStatus(payload);
    },

    onSwarmCompleted: (payload) => {
      setSwarmStatus((prev) =>
        prev
          ? {
              ...prev,
              status: payload.status as any,
              completedAt: payload.completedAt,
            }
          : null
      );
    },

    onWorkerStarted: (payload) => {
      // Worker 開始，更新狀態
    },

    onWorkerProgress: (payload) => {
      updateWorkerProgress(payload);
    },

    onWorkerThinking: (payload) => {
      updateWorkerThinking(payload);
    },

    onWorkerToolCall: (payload) => {
      updateWorkerToolCall(payload);
    },

    onWorkerCompleted: (payload) => {
      completeWorker(payload.workerId, payload.status as any, payload.result);
    },
  });

  // ... 其他邏輯
}
```

**驗收標準**:
- [ ] 所有 Swarm 事件正確處理
- [ ] Store 狀態正確更新
- [ ] 無記憶體洩漏
- [ ] 重連處理正確

### Story 105-4: useSwarmStatus Hook (3h, P0)

**目標**: 封裝 Swarm 狀態訪問和操作

**交付物**:
- `frontend/src/components/unified-chat/agent-swarm/hooks/useSwarmStatus.ts`

**實現**:

```typescript
// useSwarmStatus.ts
import { useCallback, useMemo } from 'react';
import { useSwarmStore } from '@/stores/swarmStore';
import { WorkerSummary } from '../types';

export function useSwarmStatus() {
  const store = useSwarmStore();

  // 計算屬性
  const isSwarmActive = useMemo(() => {
    return store.swarmStatus?.status === 'executing';
  }, [store.swarmStatus?.status]);

  const completedWorkers = useMemo(() => {
    return store.swarmStatus?.workers.filter((w) => w.status === 'completed') || [];
  }, [store.swarmStatus?.workers]);

  const runningWorkers = useMemo(() => {
    return store.swarmStatus?.workers.filter((w) => w.status === 'running') || [];
  }, [store.swarmStatus?.workers]);

  const failedWorkers = useMemo(() => {
    return store.swarmStatus?.workers.filter((w) => w.status === 'failed') || [];
  }, [store.swarmStatus?.workers]);

  // Actions
  const handleWorkerSelect = useCallback(
    (worker: WorkerSummary) => {
      store.selectWorker(worker);
      store.openDrawer();
    },
    [store]
  );

  const handleDrawerClose = useCallback(() => {
    store.closeDrawer();
  }, [store]);

  return {
    // 狀態
    swarmStatus: store.swarmStatus,
    selectedWorkerId: store.selectedWorkerId,
    selectedWorkerDetail: store.selectedWorkerDetail,
    isDrawerOpen: store.isDrawerOpen,
    isLoading: store.isLoading,
    error: store.error,

    // 計算屬性
    isSwarmActive,
    completedWorkers,
    runningWorkers,
    failedWorkers,

    // Actions
    handleWorkerSelect,
    handleDrawerClose,
    setWorkerDetail: store.setWorkerDetail,
    reset: store.reset,
  };
}
```

**驗收標準**:
- [ ] Hook 正確封裝 Store
- [ ] 計算屬性正確
- [ ] 類型安全

### Story 105-5: 組件通信優化 (4h, P1)

**目標**: 優化組件間的通信和狀態同步

**交付物**:
- 優化相關組件

**優化內容**:
- 使用 `useMemo` 避免不必要的重渲染
- 使用 `useCallback` 穩定事件處理函數
- 批量狀態更新
- 選擇性訂閱 (selector)

**驗收標準**:
- [ ] 無不必要的重渲染
- [ ] React DevTools 無警告
- [ ] 性能良好

### Story 105-6: 單元測試與整合測試 (2h, P0)

**目標**: 為整合部分編寫測試

**交付物**:
- `frontend/src/stores/__tests__/swarmStore.test.ts`
- `frontend/src/components/unified-chat/__tests__/OrchestrationPanel.integration.test.tsx`

**驗收標準**:
- [ ] Store 測試完整
- [ ] 整合測試通過

## 技術設計

### 狀態流

```
SSE Events
    │
    ▼
useSwarmEvents (hook)
    │
    ▼
SwarmStore (Zustand)
    │
    ├─► OrchestrationPanel
    │       │
    │       ▼
    │   AgentSwarmPanel
    │
    └─► WorkerDetailDrawer
            │
            ▼
        useWorkerDetail
```

### Store 結構

```
SwarmStore
├── swarmStatus: AgentSwarmStatus | null
├── selectedWorkerId: string | null
├── selectedWorkerDetail: WorkerDetail | null
├── isDrawerOpen: boolean
├── isLoading: boolean
└── error: string | null
```

## 依賴

- Zustand
- zustand/middleware/immer
- zustand/middleware/devtools

## 風險

| 風險 | 緩解措施 |
|------|---------|
| 狀態同步問題 | 單一狀態源，immer 不可變更新 |
| 重渲染過多 | 選擇性訂閱，useMemo |
| 記憶體洩漏 | 清理訂閱，reset 函數 |

## 完成標準

- [ ] 所有 Story 完成
- [ ] Store 正確工作
- [ ] 整合測試通過
- [ ] 無性能問題

---

**Sprint 開始**: 2026-03-06
**Sprint 結束**: 2026-03-13
**Story Points**: 25
