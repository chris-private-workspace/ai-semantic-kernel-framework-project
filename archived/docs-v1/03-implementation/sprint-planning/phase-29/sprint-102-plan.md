# Sprint 102: AgentSwarmPanel + WorkerCard

## 概述

Sprint 102 專注於實現 Agent Swarm 的主面板和 Worker 卡片組件，這是可視化介面的核心 UI 元素。

## 目標

1. 實現 AgentSwarmPanel 主面板組件
2. 實現 SwarmHeader 標題欄組件
3. 實現 OverallProgress 整體進度條組件
4. 實現 WorkerCard 單卡片組件
5. 實現 WorkerCardList 卡片列表組件
6. 實現 SwarmStatusBadges 底部狀態徽章

## Story Points: 30 點

## 前置條件

- ✅ Sprint 100 完成 (Swarm 數據模型 + API)
- ✅ Sprint 101 完成 (Swarm 事件系統)
- ✅ Shadcn UI 組件庫就緒
- ✅ Tailwind CSS 配置完成

## 任務分解

### Story 102-1: TypeScript 類型定義 (2h, P0)

**目標**: 定義前端所需的所有 TypeScript 類型

**交付物**:
- `frontend/src/components/unified-chat/agent-swarm/types/index.ts`

**類型定義**:

```typescript
// types/index.ts

// ==================== 基礎類型 ====================

export type WorkerType = 'claude_sdk' | 'maf' | 'hybrid';
export type WorkerStatus = 'pending' | 'running' | 'paused' | 'completed' | 'failed';
export type SwarmMode = 'sequential' | 'parallel' | 'pipeline' | 'hybrid';
export type SwarmStatus = 'initializing' | 'executing' | 'aggregating' | 'completed' | 'failed';

// ==================== 工具調用 ====================

export interface ToolCallInfo {
  toolCallId: string;
  toolName: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  inputArgs: Record<string, unknown>;
  outputResult?: Record<string, unknown>;
  error?: string;
  startedAt?: string;
  completedAt?: string;
  durationMs?: number;
}

// ==================== 思考內容 ====================

export interface ThinkingContent {
  content: string;
  timestamp: string;
  tokenCount?: number;
}

// ==================== Worker 消息 ====================

export interface WorkerMessage {
  role: 'system' | 'user' | 'assistant' | 'tool';
  content: string;
  timestamp: string;
  toolCallId?: string;
}

// ==================== Worker 摘要 (卡片顯示) ====================

export interface WorkerSummary {
  workerId: string;
  workerName: string;
  workerType: WorkerType;
  role: string;
  status: WorkerStatus;
  progress: number;
  currentAction?: string;
  toolCallsCount: number;
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
}

// ==================== Worker 詳情 (Drawer 顯示) ====================

export interface WorkerDetail extends WorkerSummary {
  taskId: string;
  taskDescription: string;
  thinkingHistory: ThinkingContent[];
  toolCalls: ToolCallInfo[];
  messages: WorkerMessage[];
  result?: Record<string, unknown>;
  error?: string;
  checkpointId?: string;
  checkpointBackend?: string;
}

// ==================== Swarm 狀態 ====================

export interface AgentSwarmStatus {
  swarmId: string;
  sessionId: string;
  mode: SwarmMode;
  status: SwarmStatus;
  totalWorkers: number;
  overallProgress: number;
  workers: WorkerSummary[];
  createdAt: string;
  startedAt?: string;
  estimatedCompletion?: string;
  completedAt?: string;
  metadata: Record<string, unknown>;
}

// ==================== 組件 Props ====================

export interface AgentSwarmPanelProps {
  swarmStatus: AgentSwarmStatus | null;
  onWorkerClick?: (worker: WorkerSummary) => void;
  isLoading?: boolean;
  className?: string;
}

export interface SwarmHeaderProps {
  mode: SwarmMode;
  status: SwarmStatus;
  totalWorkers: number;
  startedAt?: string;
}

export interface OverallProgressProps {
  progress: number;
  status: SwarmStatus;
  animated?: boolean;
}

export interface WorkerCardProps {
  worker: WorkerSummary;
  index: number;
  isSelected?: boolean;
  onClick?: () => void;
}

export interface WorkerCardListProps {
  workers: WorkerSummary[];
  selectedWorkerId?: string;
  onWorkerClick?: (worker: WorkerSummary) => void;
}

export interface SwarmStatusBadgesProps {
  workers: WorkerSummary[];
  onWorkerClick?: (worker: WorkerSummary) => void;
}
```

**驗收標準**:
- [ ] 所有類型定義完成
- [ ] 與後端 API 響應格式一致
- [ ] 導出正確

### Story 102-2: SwarmHeader 組件 (3h, P0)

**目標**: 實現 Swarm 標題欄組件

**交付物**:
- `frontend/src/components/unified-chat/agent-swarm/SwarmHeader.tsx`

**設計規格**:

```
┌─────────────────────────────────────────────────────────────┐
│ 🐝 AGENT SWARM (3 Workers)                    [Sequential]  │
│ ────────────────────────────────────────────────────────    │
│ Status: 🔄 Executing | Started: 10:30:45                    │
└─────────────────────────────────────────────────────────────┘
```

**組件實現**:

```tsx
// SwarmHeader.tsx
import { FC } from 'react';
import { Badge } from '@/components/ui/badge';
import { Bug, Clock, PlayCircle, CheckCircle, XCircle, Pause } from 'lucide-react';
import { SwarmHeaderProps, SwarmMode, SwarmStatus } from './types';

const MODE_LABELS: Record<SwarmMode, string> = {
  sequential: 'Sequential',
  parallel: 'Parallel',
  pipeline: 'Pipeline',
  hybrid: 'Hybrid',
};

const STATUS_CONFIG: Record<SwarmStatus, { icon: typeof Clock; color: string; label: string }> = {
  initializing: { icon: Clock, color: 'text-yellow-500', label: 'Initializing' },
  executing: { icon: PlayCircle, color: 'text-blue-500', label: 'Executing' },
  aggregating: { icon: Clock, color: 'text-purple-500', label: 'Aggregating' },
  completed: { icon: CheckCircle, color: 'text-green-500', label: 'Completed' },
  failed: { icon: XCircle, color: 'text-red-500', label: 'Failed' },
};

export const SwarmHeader: FC<SwarmHeaderProps> = ({
  mode,
  status,
  totalWorkers,
  startedAt,
}) => {
  const statusConfig = STATUS_CONFIG[status];
  const StatusIcon = statusConfig.icon;

  const formatTime = (isoString?: string) => {
    if (!isoString) return '--:--:--';
    return new Date(isoString).toLocaleTimeString();
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bug className="h-4 w-4 text-amber-500" />
          <span className="font-semibold text-sm">
            AGENT SWARM ({totalWorkers} Workers)
          </span>
        </div>
        <Badge variant="outline" className="text-xs">
          {MODE_LABELS[mode]}
        </Badge>
      </div>

      <div className="flex items-center gap-4 text-xs text-muted-foreground">
        <div className="flex items-center gap-1">
          <StatusIcon className={`h-3 w-3 ${statusConfig.color}`} />
          <span>{statusConfig.label}</span>
        </div>
        {startedAt && (
          <div className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            <span>Started: {formatTime(startedAt)}</span>
          </div>
        )}
      </div>
    </div>
  );
};
```

**驗收標準**:
- [ ] 組件正確顯示 Swarm 信息
- [ ] 狀態圖標和顏色正確
- [ ] 響應式設計
- [ ] 單元測試通過

### Story 102-3: OverallProgress 組件 (2h, P0)

**目標**: 實現整體進度條組件

**交付物**:
- `frontend/src/components/unified-chat/agent-swarm/OverallProgress.tsx`

**設計規格**:

```
整體進度: ████████████░░░░░░░░  65%
```

**組件實現**:

```tsx
// OverallProgress.tsx
import { FC } from 'react';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';
import { OverallProgressProps, SwarmStatus } from './types';

const STATUS_COLORS: Record<SwarmStatus, string> = {
  initializing: 'bg-yellow-500',
  executing: 'bg-blue-500',
  aggregating: 'bg-purple-500',
  completed: 'bg-green-500',
  failed: 'bg-red-500',
};

export const OverallProgress: FC<OverallProgressProps> = ({
  progress,
  status,
  animated = true,
}) => {
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <span className="text-muted-foreground">Overall Progress</span>
        <span className="font-medium">{progress}%</span>
      </div>
      <Progress
        value={progress}
        className={cn(
          'h-2',
          animated && status === 'executing' && 'animate-pulse',
        )}
        indicatorClassName={STATUS_COLORS[status]}
      />
    </div>
  );
};
```

**驗收標準**:
- [ ] 進度條正確顯示
- [ ] 動畫效果正常
- [ ] 狀態顏色正確

### Story 102-4: WorkerCard 組件 (6h, P0)

**目標**: 實現單個 Worker 的卡片組件

**交付物**:
- `frontend/src/components/unified-chat/agent-swarm/WorkerCard.tsx`

**設計規格**:

```
┌─────────────────────────────────────────────────────────────┐
│ 🔍 DiagnosticWorker                     🔄 Running     01   │
│ [🤖 Claude SDK] [Diagnostic]                                │
│ └─ 分析 ADF Pipeline 錯誤日誌...                            │
│ ████████████████░░░░  85%  [analyzing] (2/3 tools)          │
│                                                   [查看 >]  │
└─────────────────────────────────────────────────────────────┘
```

**組件實現**:

```tsx
// WorkerCard.tsx
import { FC } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import {
  Search, Wrench, CheckCircle, Clock, PlayCircle,
  XCircle, Pause, ChevronRight, Bot, Building2
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { WorkerCardProps, WorkerStatus, WorkerType } from './types';

// 角色圖標映射
const ROLE_ICONS: Record<string, typeof Search> = {
  diagnostic: Search,
  remediation: Wrench,
  verification: CheckCircle,
  default: Bot,
};

// 狀態配置
const STATUS_CONFIG: Record<WorkerStatus, { icon: typeof Clock; color: string; bgColor: string }> = {
  pending: { icon: Clock, color: 'text-gray-500', bgColor: 'bg-gray-100' },
  running: { icon: PlayCircle, color: 'text-blue-500', bgColor: 'bg-blue-50' },
  paused: { icon: Pause, color: 'text-yellow-500', bgColor: 'bg-yellow-50' },
  completed: { icon: CheckCircle, color: 'text-green-500', bgColor: 'bg-green-50' },
  failed: { icon: XCircle, color: 'text-red-500', bgColor: 'bg-red-50' },
};

// Worker 類型配置
const TYPE_CONFIG: Record<WorkerType, { icon: typeof Bot; label: string }> = {
  claude_sdk: { icon: Bot, label: 'Claude SDK' },
  maf: { icon: Building2, label: 'MAF' },
  hybrid: { icon: Bot, label: 'Hybrid' },
};

export const WorkerCard: FC<WorkerCardProps> = ({
  worker,
  index,
  isSelected = false,
  onClick,
}) => {
  const RoleIcon = ROLE_ICONS[worker.role] || ROLE_ICONS.default;
  const statusConfig = STATUS_CONFIG[worker.status];
  const StatusIcon = statusConfig.icon;
  const typeConfig = TYPE_CONFIG[worker.workerType];
  const TypeIcon = typeConfig.icon;

  const displayIndex = String(index + 1).padStart(2, '0');

  return (
    <Card
      className={cn(
        'cursor-pointer transition-all hover:shadow-md',
        isSelected && 'ring-2 ring-primary',
        statusConfig.bgColor,
      )}
      onClick={onClick}
    >
      <CardContent className="p-3 space-y-2">
        {/* 標題行 */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <RoleIcon className={cn('h-4 w-4', statusConfig.color)} />
            <span className="font-medium text-sm truncate max-w-[180px]">
              {worker.workerName}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <StatusIcon className={cn('h-4 w-4', statusConfig.color)} />
            <span className="text-xs font-mono text-muted-foreground">
              {displayIndex}
            </span>
          </div>
        </div>

        {/* 類型標籤 */}
        <div className="flex items-center gap-1">
          <Badge variant="secondary" className="text-xs h-5">
            <TypeIcon className="h-3 w-3 mr-1" />
            {typeConfig.label}
          </Badge>
          <Badge variant="outline" className="text-xs h-5 capitalize">
            {worker.role}
          </Badge>
        </div>

        {/* 當前操作 */}
        {worker.currentAction && (
          <div className="text-xs text-muted-foreground truncate">
            └─ {worker.currentAction}
          </div>
        )}

        {/* 進度條 */}
        <div className="space-y-1">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <Progress
                value={worker.progress}
                className="h-1.5 w-24"
              />
              <span className="font-mono">{worker.progress}%</span>
            </div>
            <span className="text-muted-foreground">
              ({worker.toolCallsCount} tools)
            </span>
          </div>
        </div>

        {/* 查看按鈕 */}
        <div className="flex justify-end">
          <Button
            variant="ghost"
            size="sm"
            className="h-6 text-xs"
            onClick={(e) => {
              e.stopPropagation();
              onClick?.();
            }}
          >
            查看 <ChevronRight className="h-3 w-3 ml-1" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};
```

**驗收標準**:
- [ ] 卡片正確顯示 Worker 信息
- [ ] 狀態圖標和顏色正確
- [ ] 進度條正確顯示
- [ ] 點擊事件正常
- [ ] 響應式設計
- [ ] 單元測試通過

### Story 102-5: WorkerCardList 組件 (3h, P0)

**目標**: 實現 Worker 卡片列表組件

**交付物**:
- `frontend/src/components/unified-chat/agent-swarm/WorkerCardList.tsx`

**組件實現**:

```tsx
// WorkerCardList.tsx
import { FC } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { WorkerCard } from './WorkerCard';
import { WorkerCardListProps } from './types';

export const WorkerCardList: FC<WorkerCardListProps> = ({
  workers,
  selectedWorkerId,
  onWorkerClick,
}) => {
  if (workers.length === 0) {
    return (
      <div className="text-center text-muted-foreground text-sm py-4">
        No workers assigned yet
      </div>
    );
  }

  return (
    <ScrollArea className="max-h-[400px]">
      <div className="space-y-2 pr-4">
        {workers.map((worker, index) => (
          <WorkerCard
            key={worker.workerId}
            worker={worker}
            index={index}
            isSelected={worker.workerId === selectedWorkerId}
            onClick={() => onWorkerClick?.(worker)}
          />
        ))}
      </div>
    </ScrollArea>
  );
};
```

**驗收標準**:
- [ ] 列表正確渲染
- [ ] 滾動正常
- [ ] 選中狀態正確
- [ ] 空狀態處理

### Story 102-6: AgentSwarmPanel 主面板 (6h, P0)

**目標**: 整合所有子組件，實現 Agent Swarm 主面板

**交付物**:
- `frontend/src/components/unified-chat/agent-swarm/AgentSwarmPanel.tsx`
- `frontend/src/components/unified-chat/agent-swarm/index.ts`

**組件實現**:

```tsx
// AgentSwarmPanel.tsx
import { FC } from 'react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';
import { SwarmHeader } from './SwarmHeader';
import { OverallProgress } from './OverallProgress';
import { WorkerCardList } from './WorkerCardList';
import { AgentSwarmPanelProps } from './types';

export const AgentSwarmPanel: FC<AgentSwarmPanelProps> = ({
  swarmStatus,
  onWorkerClick,
  isLoading = false,
  className,
}) => {
  // 加載狀態
  if (isLoading) {
    return (
      <Card className={cn('w-full', className)}>
        <CardHeader className="pb-2">
          <Skeleton className="h-4 w-48" />
          <Skeleton className="h-3 w-32 mt-2" />
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-2 w-full" />
          <div className="space-y-2">
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-24 w-full" />
          </div>
        </CardContent>
      </Card>
    );
  }

  // 無數據狀態
  if (!swarmStatus) {
    return (
      <Card className={cn('w-full', className)}>
        <CardContent className="py-8 text-center text-muted-foreground">
          <p className="text-sm">No active Agent Swarm</p>
          <p className="text-xs mt-1">
            A swarm will appear when multi-agent coordination starts
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn('w-full', className)}>
      <CardHeader className="pb-2">
        <SwarmHeader
          mode={swarmStatus.mode}
          status={swarmStatus.status}
          totalWorkers={swarmStatus.totalWorkers}
          startedAt={swarmStatus.startedAt}
        />
      </CardHeader>

      <CardContent className="space-y-4">
        <OverallProgress
          progress={swarmStatus.overallProgress}
          status={swarmStatus.status}
        />

        <div className="border-t pt-4">
          <WorkerCardList
            workers={swarmStatus.workers}
            onWorkerClick={onWorkerClick}
          />
        </div>
      </CardContent>
    </Card>
  );
};
```

**導出文件**:

```typescript
// index.ts
export * from './types';
export { AgentSwarmPanel } from './AgentSwarmPanel';
export { SwarmHeader } from './SwarmHeader';
export { OverallProgress } from './OverallProgress';
export { WorkerCard } from './WorkerCard';
export { WorkerCardList } from './WorkerCardList';
export { SwarmStatusBadges } from './SwarmStatusBadges';
```

**驗收標準**:
- [ ] 主面板正確組合子組件
- [ ] 加載狀態正確
- [ ] 空狀態正確
- [ ] 響應式設計
- [ ] 導出正確

### Story 102-7: SwarmStatusBadges 組件 (3h, P1)

**目標**: 實現底部狀態徽章組件

**交付物**:
- `frontend/src/components/unified-chat/agent-swarm/SwarmStatusBadges.tsx`

**設計規格**:

```
[👤01 ✅] [👤02 ✅] [👤03 🔄] [👤04 ⏳] [👤05 ⏳]
Completed  Completed  Running   Pending   Pending
```

**組件實現**:

```tsx
// SwarmStatusBadges.tsx
import { FC } from 'react';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { CheckCircle, Clock, PlayCircle, XCircle, Pause, User } from 'lucide-react';
import { cn } from '@/lib/utils';
import { SwarmStatusBadgesProps, WorkerStatus } from './types';

const STATUS_CONFIG: Record<WorkerStatus, { icon: typeof Clock; color: string }> = {
  pending: { icon: Clock, color: 'text-gray-400' },
  running: { icon: PlayCircle, color: 'text-blue-500' },
  paused: { icon: Pause, color: 'text-yellow-500' },
  completed: { icon: CheckCircle, color: 'text-green-500' },
  failed: { icon: XCircle, color: 'text-red-500' },
};

export const SwarmStatusBadges: FC<SwarmStatusBadgesProps> = ({
  workers,
  onWorkerClick,
}) => {
  return (
    <div className="flex flex-wrap gap-2 justify-center py-2">
      {workers.map((worker, index) => {
        const statusConfig = STATUS_CONFIG[worker.status];
        const StatusIcon = statusConfig.icon;
        const displayIndex = String(index + 1).padStart(2, '0');

        return (
          <Tooltip key={worker.workerId}>
            <TooltipTrigger asChild>
              <Badge
                variant="outline"
                className={cn(
                  'cursor-pointer hover:bg-accent transition-colors',
                  'flex items-center gap-1 px-2 py-1',
                )}
                onClick={() => onWorkerClick?.(worker)}
              >
                <User className="h-3 w-3" />
                <span className="font-mono text-xs">{displayIndex}</span>
                <StatusIcon className={cn('h-3 w-3', statusConfig.color)} />
              </Badge>
            </TooltipTrigger>
            <TooltipContent>
              <div className="text-xs">
                <div className="font-medium">{worker.workerName}</div>
                <div className="text-muted-foreground capitalize">
                  {worker.status} - {worker.progress}%
                </div>
              </div>
            </TooltipContent>
          </Tooltip>
        );
      })}
    </div>
  );
};
```

**驗收標準**:
- [ ] 徽章正確顯示
- [ ] Tooltip 正確顯示
- [ ] 點擊事件正常
- [ ] 響應式設計

### Story 102-8: 單元測試 (5h, P0)

**目標**: 為所有組件編寫完整測試

**交付物**:
- `frontend/src/components/unified-chat/agent-swarm/__tests__/`

**測試文件**:
- `SwarmHeader.test.tsx`
- `OverallProgress.test.tsx`
- `WorkerCard.test.tsx`
- `WorkerCardList.test.tsx`
- `AgentSwarmPanel.test.tsx`
- `SwarmStatusBadges.test.tsx`

**驗收標準**:
- [ ] 測試覆蓋率 > 85%
- [ ] 所有測試通過
- [ ] 快照測試正確

## 技術設計

### 組件層次

```
AgentSwarmPanel
├── SwarmHeader
├── OverallProgress
├── WorkerCardList
│   └── WorkerCard (多個)
└── SwarmStatusBadges (可選)
```

### 樣式規範

- 使用 Tailwind CSS
- 使用 Shadcn UI 組件
- 支援深色模式
- 響應式設計

## 依賴

- React 18
- Shadcn UI
- Tailwind CSS
- Lucide React (圖標)

## 風險

| 風險 | 緩解措施 |
|------|---------|
| 性能問題 (多卡片) | 虛擬化列表 (如需要) |
| 樣式不一致 | 統一使用 Shadcn 組件 |
| 響應式問題 | 測試多種螢幕尺寸 |

## 完成標準

- [ ] 所有 Story 完成
- [ ] 測試覆蓋率 > 85%
- [ ] 響應式設計正確
- [ ] 代碼審查通過

---

**Sprint 開始**: 2026-02-13
**Sprint 結束**: 2026-02-20
**Story Points**: 30
