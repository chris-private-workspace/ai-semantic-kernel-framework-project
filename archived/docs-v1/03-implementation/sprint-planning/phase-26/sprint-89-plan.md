# Sprint 89: 統計和進階功能

## Sprint Info

| Field | Value |
|-------|-------|
| **Sprint Number** | 89 |
| **Phase** | 26 - DevUI 前端實現 |
| **Duration** | 5-7 days |
| **Story Points** | 12 pts |
| **Status** | ✅ 完成 |
| **Priority** | 🟡 P1 高優先 |

---

## Sprint Goal

實現統計儀表板和進階功能，包括實時追蹤更新和事件過濾搜索。

---

## Prerequisites

- Sprint 88 完成（時間線可視化）

---

## User Stories

### S89-1: 統計儀表板 (5 pts)

**Description**: 實現執行統計儀表板，展示關鍵指標

**Acceptance Criteria**:
- [ ] LLM 調用統計卡片：
  - 調用次數
  - 總耗時
  - 平均耗時
- [ ] 工具調用統計卡片：
  - 調用次數
  - 總耗時
  - 成功率
- [ ] 事件統計卡片：
  - 總事件數
  - 按類型分佈（餅圖）
- [ ] 錯誤和警告：
  - 錯誤計數
  - 警告計數
  - 錯誤列表
- [ ] 檢查點統計：
  - 創建數量
  - 批准/拒絕/超時

**API Endpoints**:
```
GET /api/v1/devtools/traces/{execution_id}/statistics
```

**Files to Create**:
- `frontend/src/components/DevUI/Statistics.tsx`
- `frontend/src/components/DevUI/StatCard.tsx`
- `frontend/src/components/DevUI/EventPieChart.tsx`

---

### S89-2: 實時追蹤功能 (5 pts)

**Description**: 實現實時追蹤更新功能，支持正在執行的工作流

**Acceptance Criteria**:
- [ ] SSE 連接建立
- [ ] 實時事件接收和顯示
- [ ] 自動滾動到最新事件
- [ ] 連接狀態指示器
- [ ] 斷線重連機制
- [ ] 暫停/繼續自動更新

**技術實現**:
```typescript
// 使用 EventSource 接收 SSE
const eventSource = new EventSource(
  `/api/v1/devtools/traces/${executionId}/stream`
);

eventSource.onmessage = (event) => {
  const traceEvent = JSON.parse(event.data);
  addEvent(traceEvent);
};
```

**Files to Create**:
- `frontend/src/hooks/useDevToolsStream.ts`
- `frontend/src/components/DevUI/LiveIndicator.tsx`

---

### S89-3: 事件過濾和搜索 (2 pts)

**Description**: 實現事件的進階過濾和搜索功能

**Acceptance Criteria**:
- [ ] 按事件類型過濾（多選）
- [ ] 按嚴重性過濾
- [ ] 按執行器 ID 過濾
- [ ] 文本搜索（事件數據）
- [ ] 過濾器組合
- [ ] 清除過濾器

**Files to Create**:
- `frontend/src/components/DevUI/EventFilter.tsx`
- `frontend/src/hooks/useEventFilter.ts`

---

## UI 設計

### 統計儀表板布局

```
┌─────────────────────────────────────────────────────────────┐
│                     執行統計                                 │
├───────────────┬───────────────┬───────────────┬────────────┤
│  LLM 調用     │  工具調用     │  事件總數     │  錯誤/警告  │
│  5 次         │  12 次        │  45           │  2 / 3     │
│  ████ 3.2s    │  ████ 1.5s    │               │            │
├───────────────┴───────────────┴───────────────┴────────────┤
│                    事件類型分佈                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  [餅圖: LLM 25%, Tool 35%, Workflow 20%, Other 20%] │    │
│  └────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────┤
│  檢查點: 創建 3 | 批准 2 | 拒絕 0 | 超時 1                 │
└─────────────────────────────────────────────────────────────┘
```

### 實時追蹤指示器

```
┌─────────────────────────────────────────────────────┐
│  🟢 實時追蹤中 | 最後更新: 10:30:45 | [暫停] [斷開] │
└─────────────────────────────────────────────────────┘
```

---

## 技術實現

### 統計數據類型

```typescript
interface TraceStatistics {
  execution_id: string;
  total_events: number;
  events_by_type: Record<string, number>;
  total_duration_ms?: number;
  llm_calls: number;
  llm_total_ms: number;
  tool_calls: number;
  tool_total_ms: number;
  errors: number;
  warnings: number;
  checkpoints: number;
}
```

### 實時追蹤 Hook

```typescript
// frontend/src/hooks/useDevToolsStream.ts
export function useDevToolsStream(executionId: string) {
  const [events, setEvents] = useState<TraceEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isPaused, setIsPaused] = useState(false);

  useEffect(() => {
    if (isPaused) return;

    const eventSource = new EventSource(
      `${API_BASE}/devtools/traces/${executionId}/stream`
    );

    eventSource.onopen = () => setIsConnected(true);
    eventSource.onerror = () => setIsConnected(false);
    eventSource.onmessage = (e) => {
      const event = JSON.parse(e.data);
      setEvents(prev => [...prev, event]);
    };

    return () => eventSource.close();
  }, [executionId, isPaused]);

  return { events, isConnected, isPaused, setIsPaused };
}
```

---

## Definition of Done

- [ ] 所有 Stories 完成
- [ ] 統計數據正確顯示
- [ ] SSE 實時更新正常
- [ ] 過濾和搜索功能正常
- [ ] 單元測試覆蓋率 > 80%

---

## Success Metrics

| Metric | Target |
|--------|--------|
| 統計載入時間 | < 500ms |
| 實時更新延遲 | < 1s |
| 過濾響應時間 | < 200ms |

---

**Created**: 2026-01-13
**Story Points**: 12 pts
