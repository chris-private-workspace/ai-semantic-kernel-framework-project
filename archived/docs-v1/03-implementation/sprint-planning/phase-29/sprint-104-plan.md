# Sprint 104: ExtendedThinking + 工具調用展示優化

## 概述

Sprint 104 專注於實現 Claude Extended Thinking（擴展思考）的可視化展示，以及工具調用的增強展示功能。這是 Agent Swarm 可視化的核心差異化功能。

## 目標

1. 實現 ExtendedThinkingPanel 擴展思考面板
2. 實現 ThinkingBlock 單個思考塊組件
3. 實現 ThinkingTimeline 思考時間線
4. 增強 ToolCallItem 支援實時更新
5. 實現 WorkerActionList 操作列表組件
6. 後端支援 Extended Thinking 事件

## Story Points: 28 點

## 前置條件

- ✅ Sprint 103 完成 (WorkerDetailDrawer)
- ✅ Claude SDK Extended Thinking 支援
- ✅ SSE 事件系統就緒

## 任務分解

### Story 104-1: 後端 Extended Thinking 支援 (5h, P0)

**目標**: 在後端整合 Claude Extended Thinking 內容捕獲

**交付物**:
- 修改 `backend/src/integrations/claude_sdk/client.py`
- 修改 `backend/src/integrations/swarm/tracker.py`

**核心實現**:

```python
# 在 ClaudeSDKClient 中捕獲 thinking 內容
class ClaudeSDKClient:
    async def execute_with_thinking(
        self,
        messages: List[Dict],
        tools: List[Dict],
        thinking_callback: Optional[Callable[[str, int], Awaitable[None]]] = None,
    ) -> AsyncGenerator[Dict, None]:
        """
        執行 Claude API 調用，捕獲 Extended Thinking 內容

        thinking_callback: async (thinking_content: str, token_count: int) -> None
        """
        async with self.client.messages.stream(
            model=self.model,
            messages=messages,
            tools=tools,
            max_tokens=4096,
            # 啟用 Extended Thinking (如果 API 支援)
            extra_headers={"anthropic-beta": "extended-thinking-2024-10"},
        ) as stream:
            current_thinking = ""

            async for event in stream:
                if event.type == "content_block_start":
                    if hasattr(event.content_block, 'type'):
                        if event.content_block.type == "thinking":
                            current_thinking = ""

                elif event.type == "content_block_delta":
                    if hasattr(event.delta, 'thinking'):
                        current_thinking += event.delta.thinking
                        if thinking_callback:
                            await thinking_callback(
                                current_thinking,
                                len(current_thinking.split())  # 簡單的 token 估算
                            )

                elif event.type == "content_block_stop":
                    # 思考塊結束
                    pass

                # 繼續處理其他事件類型...
                yield event
```

**驗收標準**:
- [ ] Extended Thinking 內容正確捕獲
- [ ] Thinking 事件正確發送
- [ ] Token 計數正確
- [ ] 不影響現有功能

### Story 104-2: ExtendedThinkingPanel 主面板 (5h, P0)

**目標**: 實現擴展思考的主展示面板

**交付物**:
- `frontend/src/components/unified-chat/agent-swarm/ExtendedThinkingPanel.tsx`

**設計規格**:

```
┌─────────────────────────────────────────────────────────────┐
│ 💭 思考過程 (Extended Thinking)                     [展開] │
│ ─────────────────────────────────────────────────────────  │
│ 我需要分析這個 ETL 失敗問題。根據用戶提供的信息：         │
│                                                             │
│ 1. 錯誤是 "Connection timeout to source database"          │
│ 2. 連續三天失敗                                            │
│ 3. 影響 APAC Finance Daily Report                         │
│                                                             │
│ 這表明問題可能是：                                         │
│ - 網路配置變更                                             │
│ - 防火牆規則調整                                           │
│ - 源數據庫負載過高                                         │
│ - 連接池配置問題                                           │
│                                                             │
│ 我應該先查詢 ADF 的詳細日誌來確認具體的錯誤模式...        │
│                                                             │
│ ─────────────────────────────────────────────────────────  │
│ Token: 245 | 更新: 10:35:22                                │
└─────────────────────────────────────────────────────────────┘
```

**組件實現**:

```tsx
// ExtendedThinkingPanel.tsx
import { FC, useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Brain, ChevronDown, ChevronUp, Clock, Hash } from 'lucide-react';
import { cn } from '@/lib/utils';
import { ThinkingContent } from './types';

interface ExtendedThinkingPanelProps {
  thinkingHistory: ThinkingContent[];
  maxHeight?: number;
  defaultExpanded?: boolean;
  autoScroll?: boolean;
}

export const ExtendedThinkingPanel: FC<ExtendedThinkingPanelProps> = ({
  thinkingHistory,
  maxHeight = 300,
  defaultExpanded = true,
  autoScroll = true,
}) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const scrollRef = useRef<HTMLDivElement>(null);

  // 自動滾動到底部
  useEffect(() => {
    if (autoScroll && scrollRef.current && isExpanded) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [thinkingHistory, autoScroll, isExpanded]);

  if (thinkingHistory.length === 0) {
    return null;
  }

  // 獲取最新的思考內容
  const latestThinking = thinkingHistory[thinkingHistory.length - 1];
  const totalTokens = thinkingHistory.reduce(
    (sum, t) => sum + (t.tokenCount || 0),
    0
  );

  const formatTime = (isoString: string) => {
    return new Date(isoString).toLocaleTimeString();
  };

  return (
    <Card>
      <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
        <CardHeader className="pb-2">
          <CollapsibleTrigger asChild>
            <Button
              variant="ghost"
              className="w-full justify-between p-0 h-auto hover:bg-transparent"
            >
              <div className="flex items-center gap-2">
                <Brain className="h-4 w-4 text-purple-500" />
                <CardTitle className="text-sm font-medium">
                  思考過程 (Extended Thinking)
                </CardTitle>
                <Badge variant="secondary" className="text-xs">
                  {thinkingHistory.length} blocks
                </Badge>
              </div>
              {isExpanded ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </Button>
          </CollapsibleTrigger>
        </CardHeader>

        <CollapsibleContent>
          <CardContent className="pt-0">
            <ScrollArea
              ref={scrollRef}
              className={cn('pr-4')}
              style={{ maxHeight }}
            >
              <div className="space-y-3">
                {thinkingHistory.map((thinking, index) => (
                  <ThinkingBlock
                    key={index}
                    thinking={thinking}
                    index={index}
                    isLatest={index === thinkingHistory.length - 1}
                  />
                ))}
              </div>
            </ScrollArea>

            {/* 統計信息 */}
            <div className="flex items-center justify-between mt-3 pt-3 border-t text-xs text-muted-foreground">
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-1">
                  <Hash className="h-3 w-3" />
                  <span>Token: {totalTokens}</span>
                </div>
                <div className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  <span>更新: {formatTime(latestThinking.timestamp)}</span>
                </div>
              </div>
            </div>
          </CardContent>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  );
};

// ThinkingBlock 子組件
interface ThinkingBlockProps {
  thinking: ThinkingContent;
  index: number;
  isLatest: boolean;
}

const ThinkingBlock: FC<ThinkingBlockProps> = ({
  thinking,
  index,
  isLatest,
}) => {
  return (
    <div
      className={cn(
        'p-3 rounded-lg bg-purple-50 dark:bg-purple-950/20 border border-purple-100 dark:border-purple-900',
        isLatest && 'animate-pulse-subtle',
      )}
    >
      <div className="flex items-center justify-between mb-2">
        <Badge variant="outline" className="text-xs">
          Block {index + 1}
        </Badge>
        {thinking.tokenCount && (
          <span className="text-xs text-muted-foreground">
            {thinking.tokenCount} tokens
          </span>
        )}
      </div>
      <div className="text-sm whitespace-pre-wrap leading-relaxed">
        {thinking.content}
      </div>
    </div>
  );
};
```

**驗收標準**:
- [ ] 正確顯示思考內容
- [ ] 支援展開/收起
- [ ] 自動滾動到最新
- [ ] Token 統計正確
- [ ] 動畫效果正常

### Story 104-3: 實時思考更新 (4h, P0)

**目標**: 實現思考內容的實時流式更新

**交付物**:
- 修改 `frontend/src/components/unified-chat/agent-swarm/hooks/useSwarmEvents.ts`

**核心實現**:

```typescript
// 在 useSwarmEvents 中處理 thinking 事件
export function useSwarmEvents(
  eventSource: EventSource | null,
  handlers: SwarmEventHandlers,
) {
  // ... 現有代碼

  // 處理 worker_thinking 事件
  // 這是增量更新，需要合併到現有狀態
  const handleWorkerThinking = useCallback((payload: WorkerThinkingPayload) => {
    // 通知父組件更新 Worker 的 thinking 狀態
    handlers.onWorkerThinking?.(payload);
  }, [handlers]);

  // ...
}

// 在使用端，合併 thinking 內容
const updateWorkerThinking = (payload: WorkerThinkingPayload) => {
  setSwarmStatus(prev => {
    if (!prev) return prev;

    return {
      ...prev,
      workers: prev.workers.map(w => {
        if (w.workerId !== payload.workerId) return w;

        // 更新或追加 thinking
        const existingHistory = w.thinkingHistory || [];
        const lastThinking = existingHistory[existingHistory.length - 1];

        if (lastThinking && payload.thinkingContent.startsWith(lastThinking.content)) {
          // 增量更新：替換最後一個
          return {
            ...w,
            thinkingHistory: [
              ...existingHistory.slice(0, -1),
              {
                content: payload.thinkingContent,
                timestamp: payload.timestamp,
                tokenCount: payload.tokenCount,
              },
            ],
          };
        } else {
          // 新的 thinking block
          return {
            ...w,
            thinkingHistory: [
              ...existingHistory,
              {
                content: payload.thinkingContent,
                timestamp: payload.timestamp,
                tokenCount: payload.tokenCount,
              },
            ],
          };
        }
      }),
    };
  });
};
```

**驗收標準**:
- [ ] 思考內容實時更新
- [ ] 增量合併正確
- [ ] 無閃爍問題
- [ ] 性能良好

### Story 104-4: WorkerActionList 組件 (5h, P0)

**目標**: 實現類似 Kimi AI 的操作列表組件

**交付物**:
- `frontend/src/components/unified-chat/agent-swarm/WorkerActionList.tsx`

**設計規格**:

```
┌─────────────────────────────────────────────────────────────┐
│ • 多代理上下文窗口限制處理方案                         >   │
│ • Read Todo                                             >   │
│ • Think                                                 >   │
│ • Write Todo                                            >   │
│ • 方案 監控 計數 壓縮 多代理                                │
│                                                             │
│ 讓我開始編寫詳細的技術實現方案。首先，我需要研究 Claude   │
│ 的 token 計算機制和相關 API。                              │
│                                                             │
│ • Search | Claude API token counting...           39 results│
│ • Claude Token 限制監控實現方案                             │
└─────────────────────────────────────────────────────────────┘
```

**組件實現**:

```tsx
// WorkerActionList.tsx
import { FC } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { ChevronRight, Search, FileText, Brain, Edit, Code, Database } from 'lucide-react';
import { cn } from '@/lib/utils';

export type ActionType =
  | 'read_todo'
  | 'think'
  | 'write_todo'
  | 'search'
  | 'file_created'
  | 'code'
  | 'database'
  | 'custom';

interface WorkerAction {
  id: string;
  type: ActionType;
  title: string;
  description?: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
  expandable?: boolean;
}

interface WorkerActionListProps {
  actions: WorkerAction[];
  onActionClick?: (action: WorkerAction) => void;
}

const ACTION_ICONS: Record<ActionType, typeof Search> = {
  read_todo: FileText,
  think: Brain,
  write_todo: Edit,
  search: Search,
  file_created: FileText,
  code: Code,
  database: Database,
  custom: ChevronRight,
};

const ACTION_COLORS: Record<ActionType, string> = {
  read_todo: 'text-blue-500',
  think: 'text-purple-500',
  write_todo: 'text-green-500',
  search: 'text-orange-500',
  file_created: 'text-teal-500',
  code: 'text-pink-500',
  database: 'text-cyan-500',
  custom: 'text-gray-500',
};

export const WorkerActionList: FC<WorkerActionListProps> = ({
  actions,
  onActionClick,
}) => {
  return (
    <div className="space-y-1">
      {actions.map((action) => {
        const Icon = ACTION_ICONS[action.type] || ACTION_ICONS.custom;
        const color = ACTION_COLORS[action.type] || ACTION_COLORS.custom;

        return (
          <div
            key={action.id}
            className={cn(
              'flex items-center justify-between p-2 rounded-md',
              'hover:bg-accent cursor-pointer transition-colors',
              action.expandable && 'group',
            )}
            onClick={() => onActionClick?.(action)}
          >
            <div className="flex items-center gap-2 min-w-0">
              <Icon className={cn('h-4 w-4 flex-shrink-0', color)} />
              <span className="text-sm truncate">{action.title}</span>
              {action.description && (
                <span className="text-xs text-muted-foreground truncate hidden sm:inline">
                  {action.description}
                </span>
              )}
            </div>
            {action.expandable && (
              <ChevronRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
            )}
            {action.metadata?.resultCount && (
              <span className="text-xs text-muted-foreground">
                {action.metadata.resultCount} results
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
};
```

**驗收標準**:
- [ ] 正確顯示操作列表
- [ ] 操作圖標和顏色正確
- [ ] 點擊事件正常
- [ ] 響應式設計

### Story 104-5: 增強工具調用展示 (4h, P1)

**目標**: 增強 ToolCallItem 支援實時狀態更新

**交付物**:
- 修改 `frontend/src/components/unified-chat/agent-swarm/ToolCallItem.tsx`

**增強功能**:
- 實時狀態更新動畫
- 執行時間實時計時
- 輸出結果流式顯示

**驗收標準**:
- [ ] 狀態轉換動畫
- [ ] 實時計時器
- [ ] 流式輸出支援

### Story 104-6: 單元測試 (5h, P0)

**目標**: 為所有組件編寫完整測試

**交付物**:
- `frontend/src/components/unified-chat/agent-swarm/__tests__/ExtendedThinkingPanel.test.tsx`
- `frontend/src/components/unified-chat/agent-swarm/__tests__/WorkerActionList.test.tsx`
- `backend/tests/unit/swarm/test_thinking_events.py`

**驗收標準**:
- [ ] 測試覆蓋率 > 85%
- [ ] 所有測試通過
- [ ] 後端 thinking 事件測試

## 技術設計

### Extended Thinking 數據流

```
Claude API
    │
    │ thinking event
    ▼
ClaudeSDKClient
    │
    │ thinking_callback
    ▼
SwarmIntegration.on_thinking()
    │
    ▼
SwarmTracker.add_worker_thinking()
    │
    ▼
SwarmEventEmitter.emit_worker_thinking()
    │
    │ SSE
    ▼
useSwarmEvents (frontend)
    │
    ▼
ExtendedThinkingPanel
```

### 性能優化

- Thinking 內容增量更新
- 使用 `useMemo` 避免不必要的重渲染
- 滾動區域虛擬化 (如需要)

## 依賴

- Claude API Extended Thinking (anthropic-beta)
- Framer Motion (動畫)

## 風險

| 風險 | 緩解措施 |
|------|---------|
| Thinking 內容過長 | 分頁/虛擬化 |
| 更新頻繁 | 節流處理 |
| API 不支援 | 降級處理 |

## 完成標準

- [ ] 所有 Story 完成
- [ ] 測試覆蓋率 > 85%
- [ ] 實時更新正常
- [ ] 代碼審查通過

---

**Sprint 開始**: 2026-02-27
**Sprint 結束**: 2026-03-06
**Story Points**: 28
