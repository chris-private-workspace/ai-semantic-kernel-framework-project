# Sprint 103: WorkerDetailDrawer 詳情面板

## 概述

Sprint 103 專注於實現 Worker 詳情的 Drawer 滑出面板，這是查看單個 Worker 完整執行詳情的核心介面。

## 目標

1. 實現 WorkerDetailDrawer 主組件
2. 實現 WorkerHeader 標題欄
3. 實現 CurrentTask 任務描述組件
4. 實現 ToolCallsPanel 工具調用面板
5. 實現 ToolCallItem 單個工具調用組件
6. 實現 MessageHistory 對話歷史組件
7. 實現 CheckpointPanel 檢查點面板

## Story Points: 32 點

## 前置條件

- ✅ Sprint 102 完成 (AgentSwarmPanel + WorkerCard)
- ✅ Shadcn UI Drawer 組件就緒
- ✅ 類型定義完成

## 任務分解

### Story 103-1: useWorkerDetail Hook (4h, P0)

**目標**: 實現獲取 Worker 詳情的 React Hook

**交付物**:
- `frontend/src/components/unified-chat/agent-swarm/hooks/useWorkerDetail.ts`

**核心實現**:

```typescript
// useWorkerDetail.ts
import { useState, useEffect, useCallback } from 'react';
import { WorkerDetail } from '../types';

interface UseWorkerDetailOptions {
  swarmId: string;
  workerId: string;
  enabled?: boolean;
  pollInterval?: number; // 輪詢間隔 (ms)
}

interface UseWorkerDetailResult {
  worker: WorkerDetail | null;
  isLoading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

export function useWorkerDetail({
  swarmId,
  workerId,
  enabled = true,
  pollInterval,
}: UseWorkerDetailOptions): UseWorkerDetailResult {
  const [worker, setWorker] = useState<WorkerDetail | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchWorkerDetail = useCallback(async () => {
    if (!enabled || !swarmId || !workerId) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `/api/v1/swarm/${swarmId}/workers/${workerId}?include_thinking=true&include_messages=true`
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch worker detail: ${response.statusText}`);
      }

      const data = await response.json();
      setWorker(data);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setIsLoading(false);
    }
  }, [swarmId, workerId, enabled]);

  // 初始加載
  useEffect(() => {
    fetchWorkerDetail();
  }, [fetchWorkerDetail]);

  // 輪詢更新 (可選)
  useEffect(() => {
    if (!pollInterval || !enabled) return;

    const intervalId = setInterval(fetchWorkerDetail, pollInterval);
    return () => clearInterval(intervalId);
  }, [pollInterval, enabled, fetchWorkerDetail]);

  return {
    worker,
    isLoading,
    error,
    refetch: fetchWorkerDetail,
  };
}
```

**驗收標準**:
- [ ] Hook 正確獲取 Worker 詳情
- [ ] 支援輪詢更新
- [ ] 錯誤處理正確
- [ ] TypeScript 類型完整

### Story 103-2: WorkerHeader 組件 (3h, P0)

**目標**: 實現 Drawer 標題欄組件

**交付物**:
- `frontend/src/components/unified-chat/agent-swarm/WorkerHeader.tsx`

**設計規格**:

```
┌─────────────────────────────────────────────────────────────┐
│ ← 返回                              🔍 DiagnosticWorker     │
│                                                             │
│ 狀態: 🔄 Running | 進度: ████████░░ 85%                     │
│ 類型: 🤖 Claude SDK | 角色: Diagnostic                      │
└─────────────────────────────────────────────────────────────┘
```

**驗收標準**:
- [ ] 顯示 Worker 名稱和角色圖標
- [ ] 顯示狀態和進度
- [ ] 顯示類型標籤
- [ ] 返回按鈕正常工作

### Story 103-3: CurrentTask 組件 (2h, P0)

**目標**: 實現當前任務描述組件

**交付物**:
- `frontend/src/components/unified-chat/agent-swarm/CurrentTask.tsx`

**設計規格**:

```
┌─────────────────────────────────────────────────────────────┐
│ 📋 當前任務                                                 │
│ ─────────────────────────────────────────────────────────  │
│ 分析 APAC Glider ETL Pipeline 連續三天失敗的根因，        │
│ 重點檢查 Connection timeout 錯誤的來源。                   │
└─────────────────────────────────────────────────────────────┘
```

**驗收標準**:
- [ ] 正確顯示任務描述
- [ ] 支援長文本截斷/展開
- [ ] 樣式符合設計規範

### Story 103-4: ToolCallItem 組件 (4h, P0)

**目標**: 實現單個工具調用的展示組件

**交付物**:
- `frontend/src/components/unified-chat/agent-swarm/ToolCallItem.tsx`

**設計規格**:

```
┌─────────────────────────────────────────────────────────────┐
│ ☁️ azure MCP │ query_adf_logs               ✅ 1,245ms      │
│ ─────────────────────────────────────────────────────────  │
│ Input: {pipeline: "APAC_Glider_ETL", range: "72h"}        │
│ Output: {error_count: 47, primary: "timeout"...}          │
└─────────────────────────────────────────────────────────────┘
```

**組件實現**:

```tsx
// ToolCallItem.tsx
import { FC, useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Cloud, Terminal, CheckCircle, Clock, XCircle, ChevronDown, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';
import { ToolCallInfo } from './types';

interface ToolCallItemProps {
  toolCall: ToolCallInfo;
  defaultExpanded?: boolean;
}

const STATUS_CONFIG = {
  pending: { icon: Clock, color: 'text-gray-500', label: 'Pending' },
  running: { icon: Clock, color: 'text-blue-500', label: 'Running' },
  completed: { icon: CheckCircle, color: 'text-green-500', label: 'Completed' },
  failed: { icon: XCircle, color: 'text-red-500', label: 'Failed' },
};

export const ToolCallItem: FC<ToolCallItemProps> = ({
  toolCall,
  defaultExpanded = false,
}) => {
  const [isOpen, setIsOpen] = useState(defaultExpanded);
  const statusConfig = STATUS_CONFIG[toolCall.status];
  const StatusIcon = statusConfig.icon;

  // 判斷是否為 MCP 工具
  const isMCP = toolCall.toolName.includes(':') || toolCall.toolName.startsWith('mcp_');
  const ToolIcon = isMCP ? Cloud : Terminal;

  const formatDuration = (ms?: number) => {
    if (!ms) return '--';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const formatJson = (obj: Record<string, unknown>) => {
    try {
      return JSON.stringify(obj, null, 2);
    } catch {
      return String(obj);
    }
  };

  return (
    <Card className="overflow-hidden">
      <Collapsible open={isOpen} onOpenChange={setIsOpen}>
        <CollapsibleTrigger asChild>
          <Button
            variant="ghost"
            className="w-full justify-between p-3 h-auto hover:bg-accent"
          >
            <div className="flex items-center gap-2">
              <ToolIcon className="h-4 w-4 text-muted-foreground" />
              <span className="font-mono text-sm">{toolCall.toolName}</span>
            </div>
            <div className="flex items-center gap-2">
              <StatusIcon className={cn('h-4 w-4', statusConfig.color)} />
              {toolCall.durationMs && (
                <span className="text-xs text-muted-foreground">
                  {formatDuration(toolCall.durationMs)}
                </span>
              )}
              {isOpen ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
            </div>
          </Button>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <CardContent className="p-3 pt-0 space-y-3">
            {/* Input */}
            <div>
              <div className="text-xs font-medium text-muted-foreground mb-1">
                Input:
              </div>
              <pre className="text-xs bg-muted p-2 rounded-md overflow-x-auto">
                {formatJson(toolCall.inputArgs)}
              </pre>
            </div>

            {/* Output */}
            {toolCall.outputResult && (
              <div>
                <div className="text-xs font-medium text-muted-foreground mb-1">
                  Output:
                </div>
                <pre className="text-xs bg-muted p-2 rounded-md overflow-x-auto max-h-40">
                  {formatJson(toolCall.outputResult)}
                </pre>
              </div>
            )}

            {/* Error */}
            {toolCall.error && (
              <div>
                <div className="text-xs font-medium text-red-500 mb-1">
                  Error:
                </div>
                <pre className="text-xs bg-red-50 dark:bg-red-950 p-2 rounded-md text-red-600 dark:text-red-400">
                  {toolCall.error}
                </pre>
              </div>
            )}
          </CardContent>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  );
};
```

**驗收標準**:
- [ ] 正確顯示工具調用信息
- [ ] 支援展開/收起
- [ ] 輸入/輸出格式化正確
- [ ] 錯誤狀態正確顯示

### Story 103-5: ToolCallsPanel 組件 (3h, P0)

**目標**: 實現工具調用面板

**交付物**:
- `frontend/src/components/unified-chat/agent-swarm/ToolCallsPanel.tsx`

**設計規格**:

```
┌─────────────────────────────────────────────────────────────┐
│ 🔧 工具調用 (3)                                             │
│ ─────────────────────────────────────────────────────────  │
│                                                             │
│ [ToolCallItem 1]                                            │
│ [ToolCallItem 2]                                            │
│ [ToolCallItem 3]                                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**驗收標準**:
- [ ] 正確顯示工具調用數量
- [ ] 列表滾動正常
- [ ] 空狀態處理

### Story 103-6: MessageHistory 組件 (4h, P0)

**目標**: 實現對話歷史組件

**交付物**:
- `frontend/src/components/unified-chat/agent-swarm/MessageHistory.tsx`

**設計規格**:

```
┌─────────────────────────────────────────────────────────────┐
│ 💬 對話歷史                                          [展開] │
│ ─────────────────────────────────────────────────────────  │
│ [System] 你是一個專業的 ETL 故障診斷專家...               │
│ [User] 請分析 APAC Glider ETL Pipeline 的問題...          │
│ [Assistant] 好的，我來分析這個問題。首先...               │
│ [Tool] query_adf_logs → {error_count: 47...}              │
│ [Assistant] 根據日誌分析，主要錯誤是...                   │
└─────────────────────────────────────────────────────────────┘
```

**驗收標準**:
- [ ] 正確顯示各角色消息
- [ ] 支援展開/收起
- [ ] 消息時間戳顯示
- [ ] 長文本截斷

### Story 103-7: CheckpointPanel 組件 (2h, P1)

**目標**: 實現檢查點面板

**交付物**:
- `frontend/src/components/unified-chat/agent-swarm/CheckpointPanel.tsx`

**設計規格**:

```
┌─────────────────────────────────────────────────────────────┐
│ 💾 Checkpoint                                               │
│ ID: chk_abc123 | Backend: Redis | 可恢復: ✅               │
│ [恢復到此狀態]                                              │
└─────────────────────────────────────────────────────────────┘
```

**驗收標準**:
- [ ] 顯示 Checkpoint ID
- [ ] 顯示 Backend 類型
- [ ] 恢復按鈕正常

### Story 103-8: WorkerDetailDrawer 主組件 (6h, P0)

**目標**: 整合所有子組件，實現 Worker 詳情 Drawer

**交付物**:
- `frontend/src/components/unified-chat/agent-swarm/WorkerDetailDrawer.tsx`

**組件實現**:

```tsx
// WorkerDetailDrawer.tsx
import { FC } from 'react';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import { Separator } from '@/components/ui/separator';
import { WorkerHeader } from './WorkerHeader';
import { CurrentTask } from './CurrentTask';
import { ExtendedThinkingPanel } from './ExtendedThinkingPanel';
import { ToolCallsPanel } from './ToolCallsPanel';
import { MessageHistory } from './MessageHistory';
import { CheckpointPanel } from './CheckpointPanel';
import { useWorkerDetail } from './hooks/useWorkerDetail';
import { WorkerSummary } from './types';

interface WorkerDetailDrawerProps {
  open: boolean;
  onClose: () => void;
  swarmId: string;
  worker: WorkerSummary | null;
}

export const WorkerDetailDrawer: FC<WorkerDetailDrawerProps> = ({
  open,
  onClose,
  swarmId,
  worker,
}) => {
  const { worker: workerDetail, isLoading, error } = useWorkerDetail({
    swarmId,
    workerId: worker?.workerId || '',
    enabled: open && !!worker,
    pollInterval: worker?.status === 'running' ? 2000 : undefined,
  });

  return (
    <Sheet open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <SheetContent
        side="right"
        className="w-full sm:w-[540px] sm:max-w-[90vw] p-0"
      >
        <SheetHeader className="p-4 pb-0">
          <SheetTitle className="sr-only">Worker Details</SheetTitle>
        </SheetHeader>

        <ScrollArea className="h-[calc(100vh-60px)]">
          <div className="p-4 space-y-4">
            {/* 加載狀態 */}
            {isLoading && !workerDetail && (
              <div className="space-y-4">
                <Skeleton className="h-20 w-full" />
                <Skeleton className="h-16 w-full" />
                <Skeleton className="h-32 w-full" />
                <Skeleton className="h-48 w-full" />
              </div>
            )}

            {/* 錯誤狀態 */}
            {error && (
              <div className="text-center text-red-500 py-8">
                <p>Failed to load worker details</p>
                <p className="text-sm text-muted-foreground">{error.message}</p>
              </div>
            )}

            {/* 內容 */}
            {workerDetail && (
              <>
                {/* Worker 標題 */}
                <WorkerHeader
                  worker={workerDetail}
                  onBack={onClose}
                />

                <Separator />

                {/* 當前任務 */}
                <CurrentTask
                  taskDescription={workerDetail.taskDescription}
                />

                <Separator />

                {/* 思考過程 (Sprint 104) */}
                {workerDetail.thinkingHistory.length > 0 && (
                  <>
                    <ExtendedThinkingPanel
                      thinkingHistory={workerDetail.thinkingHistory}
                    />
                    <Separator />
                  </>
                )}

                {/* 工具調用 */}
                <ToolCallsPanel
                  toolCalls={workerDetail.toolCalls}
                />

                <Separator />

                {/* 對話歷史 */}
                <MessageHistory
                  messages={workerDetail.messages}
                />

                {/* Checkpoint */}
                {workerDetail.checkpointId && (
                  <>
                    <Separator />
                    <CheckpointPanel
                      checkpointId={workerDetail.checkpointId}
                      backend={workerDetail.checkpointBackend}
                    />
                  </>
                )}
              </>
            )}
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
};
```

**驗收標準**:
- [ ] Drawer 正確打開/關閉
- [ ] 所有子組件正確渲染
- [ ] 加載狀態正確
- [ ] 錯誤處理正確
- [ ] 滾動正常
- [ ] 動畫流暢

### Story 103-9: 單元測試與整合測試 (4h, P0)

**目標**: 為所有組件編寫完整測試

**交付物**:
- `frontend/src/components/unified-chat/agent-swarm/__tests__/WorkerDetailDrawer.test.tsx`
- 其他組件測試文件

**驗收標準**:
- [ ] 測試覆蓋率 > 85%
- [ ] 所有測試通過
- [ ] Mock API 正確

## 技術設計

### Drawer 層次

```
WorkerDetailDrawer
├── WorkerHeader
├── CurrentTask
├── ExtendedThinkingPanel (Sprint 104)
├── ToolCallsPanel
│   └── ToolCallItem (多個)
├── MessageHistory
└── CheckpointPanel
```

### 數據流

```
WorkerCard (click)
        │
        ▼
AgentSwarmPanel.onWorkerClick
        │
        ▼
State: selectedWorker
        │
        ▼
WorkerDetailDrawer (open)
        │
        ▼
useWorkerDetail (fetch)
        │
        ▼
Render sub-components
```

## 依賴

- Shadcn UI Sheet
- Shadcn UI Collapsible
- ScrollArea

## 風險

| 風險 | 緩解措施 |
|------|---------|
| Drawer 動畫卡頓 | 使用 CSS transform |
| 數據過大 | 分頁/虛擬化 |
| 輪詢效能 | 條件輪詢，只在 running 時 |

## 完成標準

- [ ] 所有 Story 完成
- [ ] 測試覆蓋率 > 85%
- [ ] 動畫流暢
- [ ] 代碼審查通過

---

**Sprint 開始**: 2026-02-20
**Sprint 結束**: 2026-02-27
**Story Points**: 32
