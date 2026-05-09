# V2 Frontend 設計規劃

**建立日期**：2026-04-23
**版本**：V2.0
**對應**：Phase 50.2 起

---

## 設計哲學

V2 frontend 不是 V1 的 UI 升級，是**為 11 範疇 agent harness 設計的全新介面**。

### 5 個核心理念

1. **Loop-First UI**：呈現 TAO 循環，不是線性 pipeline
2. **Transparency**：每個 thinking / tool call / verification 都可見
3. **Governance Native**：HITL / audit / approval 是核心 UX，不是邊角
4. **Real-time Streaming**：SSE 推送，毫秒級即時感
5. **DevUI for Power Users**：開發者 / admin 有強大 debug 視角

---

## Page 規劃（重新開發）

### Phase 接入時序（**2026-04-28 修訂版**）

> 對齊 [`06-phase-roadmap.md`](./06-phase-roadmap.md) 22 sprint 規劃。每頁明確 sprint 接手。

| Page | 接手 Sprint | 對應 Phase | 主要範疇 / 領域 |
|------|----------|----------|--------------|
| `chat/` | 50.2 | Phase 50 (Loop Core) | 範疇 1 + 6 主流量 |
| `governance/approvals/` | 53.4 | Phase 53 (拆分後新增) | §HITL 中央化 + 範疇 9 |
| `agents/` | 55.2 | Phase 55 業務 frontend | 業務領域 + range 11 subagent_tree |
| `workflows/` | 55.2 | Phase 55 業務 frontend | 業務領域 + tool_call_renderer |
| `incidents/` | 55.2 | Phase 55 業務 frontend | 業務領域 (incident domain) |
| `memory/` | 55.3 | Phase 55 缺漏前端（**新增**） | 範疇 3 雙軸 inspector |
| `audit/` | 55.3 | Phase 55 缺漏前端（**新增**） | 範疇 9 audit log + hash chain |
| `tools/` | 55.3 | Phase 55 缺漏前端（**新增**） | 範疇 2 ToolSpec admin |
| `admin/` | 55.3 | Phase 55 缺漏前端（**新增**） | identity / tenant / role |
| `dashboard/` | 55.3 | Phase 55 缺漏前端（**新增**） | KPI 概覽 |
| `devui/` | 55.3 | Phase 55 缺漏前端（**新增**） | 11 + 12 範疇成熟度 + trace_viewer |
| `auth/` | 49.4 | Phase 49 (Foundation) | identity 基礎 |

> **注意**：原 16-frontend-design.md 列了 9 頁，但 06-phase-roadmap.md 只排 3 頁（chat/governance/agents），其餘 6 頁排程缺漏。此次 review 修訂後 Phase 55 拆 5 sprint，55.3 專責補完前端缺漏。

### Page 結構

```
frontend/src/pages/
├── chat/                    # ⭐ 主聊天介面（核心）
├── agents/                  # Agent 管理（CRUD + test）
├── workflows/               # Workflow 編輯器（可選 phase）
├── memory/                  # Memory 瀏覽 / 編輯
├── governance/              # HITL 審批 / Risk dashboard
├── audit/                   # Audit log 瀏覽
├── tools/                   # Tool registry / test
├── devui/                   # 開發者工具
│   ├── LoopVisualizer.tsx
│   ├── CategoryDashboard.tsx
│   ├── StateTimeTravel.tsx
│   ├── PromptInspector.tsx
│   └── CostTracker.tsx
├── admin/                   # 系統管理
│   ├── tenants/
│   ├── users/
│   ├── plans/
│   └── system_settings/
├── dashboard/               # 主儀表板
└── auth/                    # Login / SSO callback
```

---

## Chat 頁面設計（最重要）

### Layout

```
┌──────────────────────────────────────────────────────────────────┐
│ Header                                                            │
│ [Tenant Logo] [Session Title]   [Settings] [User Avatar]         │
├─────────────┬────────────────────────────────────────┬──────────┤
│             │                                          │           │
│ Sessions    │   Conversation Area                      │ Inspector │
│ Sidebar     │                                          │ Sidebar   │
│             │   ┌────────────────────────────────────┐│           │
│ - Session 1 │   │ User: "..."                        ││ Loop Info │
│ - Session 2 │   │                                    ││ - Turn: 3 │
│ - Session 3 │   │ [Thinking Block ▼]                 ││ - Tokens  │
│ + New       │   │                                    ││ - Cost    │
│             │   │ Assistant: "..."                   ││           │
│             │   │                                    ││ Tools Used│
│             │   │ ┌──────────────────────────────┐  ││ - tool 1  │
│             │   │ │ 🔧 salesforce_query           │  ││ - tool 2  │
│             │   │ │ Args: {...}                   │  ││           │
│             │   │ │ Result: [...]                 │  ││ Memory    │
│             │   │ └──────────────────────────────┘  ││ Layers    │
│             │   │                                    ││ Snapshot  │
│             │   │ [HITL Required ⚠️]                 ││           │
│             │   │ [Approve] [Reject]                 ││ Verify    │
│             │   │                                    ││ Status    │
│             │   │ ✅ Verified                         ││           │
│             │   └────────────────────────────────────┘│           │
│             │                                          │           │
│             │   ┌────────────────────────────────────┐│           │
│             │   │ Input: [_____________________] [→] ││           │
│             │   └────────────────────────────────────┘│           │
└─────────────┴────────────────────────────────────────┴──────────┘
```

### 核心組件

#### MessageList
- 自動滾動到最新
- 訊息分類：user / thinking / assistant text / tool_call / tool_result / hitl / verification
- 折疊 / 展開長內容

#### ThinkingBlock
- 預設折疊
- 可展開看 agent 推理過程
- 即時 streaming（token by token）

#### ToolCallCard
- 工具名稱 + icon
- Args JSON pretty-printed
- 執行狀態（pending / running / done / error）
- Result 折疊（預設 collapsed）
- 可重新執行（debug 用）

#### HITLApprovalCard
- Risk level 標示（低 / 中 / 高 / 嚴重）
- 操作摘要
- Reasoning 展開
- 批准 / 拒絕 / 詢問詳情按鈕
- 等待時間 indicator

#### VerificationStatus
- Pass / Fail / Skipped icon
- Verifier 類型（rules / llm-judge）
- Reasoning 展開
- 若 fail 顯示 self-correction attempt 數

#### LoopProgressIndicator
- 當前 turn 計數
- Token 用量條（vs budget）
- 預估剩餘時間
- 取消按鈕

#### InspectorSidebar（右側）
- Loop info（turn / tokens / cost / latency）
- Tools used in this session
- Memory layers snapshot
- State timeline（簡略）
- Verification log
- 可選：Raw event stream（debug）

---

## Features 目錄（按 11 範疇組織）

```
frontend/src/features/
├── orchestrator_loop/      # 範疇 1
│   ├── LoopVisualizer.tsx
│   ├── TurnIndicator.tsx
│   ├── StopReasonBadge.tsx
│   └── TerminationReasonModal.tsx
├── tools/                   # 範疇 2
│   ├── ToolCallCard.tsx
│   ├── ToolPicker.tsx       # 開發者測試工具
│   ├── ToolPermissionBadge.tsx
│   └── SandboxLevelIndicator.tsx
├── memory/                  # 範疇 3
│   ├── MemoryLayerViewer.tsx
│   ├── MemorySearchPanel.tsx
│   ├── MemoryWriteForm.tsx
│   └── ClueVerificationFlow.tsx  # 線索→驗證流程
├── context_health/          # 範疇 4
│   ├── ContextUsageGauge.tsx
│   ├── CompactionEvent.tsx
│   └── TokenBudgetBar.tsx
├── prompt_inspector/        # 範疇 5
│   ├── PromptInspector.tsx  # 看 LLM 實際看到的
│   ├── HierarchyView.tsx
│   └── TokenDistribution.tsx
├── tool_call_renderer/      # 範疇 6
│   └── NativeToolCallView.tsx
├── state_timeline/          # 範疇 7
│   ├── CheckpointTimeline.tsx
│   ├── TimeTravelControls.tsx
│   └── StateDiff.tsx
├── error_panel/             # 範疇 8
│   ├── ErrorBadge.tsx
│   ├── RetryIndicator.tsx
│   └── ErrorCategoryFilter.tsx
├── guardrail_status/        # 範疇 9（**2026-04-28 拆出 HITL 後**）
│   ├── GuardrailLayerStatus.tsx  # input/output/tool 三層
│   ├── TripwireAlert.tsx
│   ├── RiskMeter.tsx
│   └── AuditLogViewer.tsx
├── hitl/                    # ⭐ §HITL 中央化（2026-04-28 從 guardrail_status 拆出）
│   ├── HITLApprovalCard.tsx       # inline chat approval card
│   ├── HITLApprovalQueue.tsx      # governance frontend pending list
│   ├── HITLDecisionModal.tsx      # reviewer 詳情 + decide 按鈕
│   ├── HITLContextSnapshot.tsx    # ApprovalRequest.context_snapshot 顯示
│   └── HITLTimeoutCountdown.tsx   # SLA deadline 倒數
├── verification_panel/      # 範疇 10
│   ├── VerificationStatus.tsx
│   ├── SelfCorrectionFlow.tsx     # 含 max_corrections 上限視覺化
│   └── JudgeReasoning.tsx
├── subagent_tree/           # 範疇 11
│   ├── SubagentTree.tsx     # 視覺化 agent 樹（基於 parent_request_id）
│   ├── HandoffArrow.tsx
│   └── MailboxView.tsx
└── observability/           # ⭐ 範疇 12（2026-04-28 新增）
    ├── TraceViewer.tsx          # 嵌入 Jaeger UI
    ├── MetricDashboard.tsx      # 三軸 metric: latency / token / cost
    ├── SpanCategoryFilter.tsx
    └── CostTracker.tsx          # per-tenant / per-session cost
```

> **架構決定（2026-04-28 review）**：HITL 從 `guardrail_status/` 拆出獨立 `hitl/`，理由：
> 1. HITL 在 V2 是中央化機制（見 01.md §HITL 中央化），不只是 guardrail 子集
> 2. 範疇 2 / 9 / 業務工具都是 caller，不應綁在範疇 9 視覺
> 3. governance frontend 頁面（pages/governance/approvals/）對應此目錄
> 4. 對齊 backend `agent_harness/hitl/` 結構

---

## Design System

### 設計工具棧

| 用途 | 工具 |
|------|------|
| Component library | **shadcn/ui**（V1 已用，保留） |
| Styling | **Tailwind CSS** |
| Icons | **Lucide React** |
| Charts | **Recharts** 或 **Tremor** |
| Animations | **Framer Motion**（節制使用） |
| Forms | **React Hook Form** + **Zod** |
| Tables | **TanStack Table** |
| Date | **date-fns** |

### Color Palette

```scss
// Tokens（透過 Tailwind 配置）
$primary: #3B82F6;     // Blue (主 actions)
$success: #10B981;     // Green (verified, approved)
$warning: #F59E0B;     // Amber (HITL, attention)
$danger: #EF4444;      // Red (errors, tripwire)
$thinking: #8B5CF6;    // Purple (thinking blocks)
$tool: #06B6D4;        // Cyan (tool calls)
$memory: #EC4899;      // Pink (memory ops)

// Severity（Risk levels）
$risk-low: $success;
$risk-medium: $warning;
$risk-high: #EA580C;   // Orange-red
$risk-critical: $danger;
```

### Typography

```scss
$font-sans: 'Inter', system-ui, sans-serif;
$font-mono: 'JetBrains Mono', monospace;  // 代碼 / JSON 用

// Sizes
text-xs: 0.75rem;   // labels, metadata
text-sm: 0.875rem;  // body
text-base: 1rem;    // default
text-lg: 1.125rem;  // section heads
text-xl: 1.25rem;   // page titles
```

---

## State Management

### Stores 結構（合併原 store + stores）

```typescript
frontend/src/stores/
├── authStore.ts          // user / tenant / token
├── chatStore.ts          // current session / messages
├── sessionListStore.ts   // session sidebar
├── settingsStore.ts      // user preferences
├── adminStore.ts         // admin views
├── governanceStore.ts    // pending approvals
└── devuiStore.ts         // dev tools state
```

### Server State（API）

使用 **TanStack Query** 處理 server state：

```typescript
// services/sessionService.ts
export const useSession = (sessionId: string) => useQuery({
  queryKey: ['session', sessionId],
  queryFn: () => api.getSession(sessionId),
})

export const useSendMessage = () => useMutation({
  mutationFn: api.sendMessage,
  onSuccess: () => queryClient.invalidateQueries(['session']),
})
```

### Client State（Zustand）

只放真正的 client state（UI state、user preferences）：

```typescript
// stores/chatStore.ts
export const useChatStore = create<ChatStore>((set) => ({
  inputDraft: '',
  isInspectorOpen: true,
  selectedTurnId: null,
  
  setInputDraft: (draft) => set({ inputDraft: draft }),
  toggleInspector: () => set((s) => ({ isInspectorOpen: !s.isInspectorOpen })),
}))
```

### SSE Stream Handling（**2026-04-28 review 修訂**：production-grade）

> **Review 發現**：原範例有 3 個關鍵缺陷：(1) 無 reconnect / lastEventId resume；(2) 全部走 onmessage 沒區分 event type；(3) 無 backpressure（高頻 token streaming 引發 re-render 風暴）。本次補強。

#### 1. 完整 hook 實作

```typescript
// hooks/useLoopEvents.ts
import { useEffect, useReducer, useRef, useSyncExternalStore } from 'react'
import { useQueryClient } from '@tanstack/react-query'

type LoopEventReducerAction =
  | { type: 'append'; events: LoopEvent[] }
  | { type: 'reset' }

function loopEventsReducer(state: LoopEvent[], action: LoopEventReducerAction): LoopEvent[] {
  if (action.type === 'reset') return []
  if (action.type === 'append') return [...state, ...action.events]
  return state
}

export const useLoopEvents = (sessionId: string) => {
  const [events, dispatch] = useReducer(loopEventsReducer, [])
  const queryClient = useQueryClient()
  const lastEventIdRef = useRef<number>(0)
  const bufferRef = useRef<LoopEvent[]>([])
  const flushScheduledRef = useRef(false)

  useEffect(() => {
    let eventSource: EventSource | null = null
    let cancelled = false

    const connect = () => {
      // 帶 last_event_id query param → 後端從該點 resume（Contract 15）
      const url = `/api/v1/chat/sessions/${sessionId}/events?last_event_id=${lastEventIdRef.current}`
      eventSource = new EventSource(url, { withCredentials: true })

      // ✅ 命名事件，對應 Contract 15 的 22 個 LoopEvent 子類
      const namedEvents = [
        'LoopStarted', 'Thinking', 'ToolCallRequested', 'ToolCallExecuted',
        'ToolCallFailed', 'MemoryAccessed', 'ContextCompacted', 'PromptBuilt',
        'StateCheckpointed', 'ErrorRetried', 'GuardrailTriggered', 'TripwireTriggered',
        'VerificationPassed', 'VerificationFailed', 'SubagentSpawned', 'SubagentCompleted',
        'ApprovalRequested', 'ApprovalReceived', 'LoopCompleted',
        'SpanStarted', 'SpanEnded', 'MetricRecorded',
      ] as const

      const handleEvent = (e: MessageEvent) => {
        const event = JSON.parse(e.data) as LoopEvent
        // SSE id 對應 Contract 15 的 streaming_seq
        if (e.lastEventId) lastEventIdRef.current = parseInt(e.lastEventId, 10)
        // ✅ Backpressure: 累積 buffer，下個 frame 才 flush
        bufferRef.current.push(event)
        if (!flushScheduledRef.current) {
          flushScheduledRef.current = true
          requestAnimationFrame(() => {
            if (cancelled) return
            const batch = bufferRef.current
            bufferRef.current = []
            flushScheduledRef.current = false
            dispatch({ type: 'append', events: batch })
            // 同步寫入 TanStack Query cache（給其他 component 訂閱）
            queryClient.setQueryData(['loop-events', sessionId], (old: LoopEvent[] = []) =>
              [...old, ...batch].slice(-1000)   // 只留最近 1000 件
            )
          })
        }
      }

      namedEvents.forEach((type) => eventSource!.addEventListener(type, handleEvent))

      // ✅ Reconnect 處理（EventSource 預設會重連，但要記錄 lastEventId）
      eventSource.onerror = () => {
        // 自動 reconnect 由瀏覽器處理，下次 connect 帶 lastEventIdRef
        console.warn(`SSE error, will reconnect from event ${lastEventIdRef.current}`)
      }
    }

    connect()
    return () => {
      cancelled = true
      eventSource?.close()
    }
  }, [sessionId, queryClient])

  return events
}
```

#### 2. Event 路由（按 type 分發給不同 component）

```typescript
// hooks/useLoopEventByType.ts
export const useLoopEventByType = <T extends LoopEvent['type']>(
  sessionId: string,
  type: T,
): Extract<LoopEvent, { type: T }>[] => {
  const events = useLoopEvents(sessionId)
  return useMemo(() => events.filter((e) => e.type === type) as any, [events, type])
}

// 使用
const thinkingEvents = useLoopEventByType(sessionId, 'Thinking')          // 給 Thinking block
const toolCalls = useLoopEventByType(sessionId, 'ToolCallRequested')       // 給 Tool list
const approvals = useLoopEventByType(sessionId, 'ApprovalRequested')      // 給 HITL card
```

#### 3. Resume 場景（page reload 後不丟事件）

當瀏覽器斷線重連，後端 SSE handler 透過 `last_event_id` query param 從該點 replay：

```python
# backend/src/api/v1/chat/events.py
@router.get("/sessions/{session_id}/events")
async def stream_events(session_id: UUID, last_event_id: int = 0):
    async for event in events_replay_from(session_id, after_seq=last_event_id):
        yield (
            f"id: {event.streaming_seq}\n"
            f"event: {event.event_type}\n"               # ⭐ named event
            f"data: {json.dumps(event.payload)}\n\n"
        )
```

#### 4. 失敗模式

| 失敗 | 處置 |
|------|------|
| EventSource 連線中斷 | 瀏覽器自動重連 + 帶 lastEventId resume |
| 後端 replay buffer 過期（事件已超過保留期） | SSE 回傳 `replay_unavailable` event → 提示用戶 reload session |
| 高頻 token storm（>1000 events/s） | requestAnimationFrame batch + cap 1000 events in cache |
| Tab 進入背景 | 自動降低 dispatch 頻率（透過 `document.visibilityState`） |

---

## TypeScript Type 系統

### 類型來源（**2026-04-28 review 修訂**：SSE event 不能手寫）

> **Review 發現**：SSE event union 不是 OpenAPI 1st-class citizen，原文件 LoopEvent 是手寫，會與後端 schema 失同步。本次補完整 codegen flow。

#### A. REST API 類型（OpenAPI codegen）

所有跨後端 REST API 類型透過 **OpenAPI codegen** 自動生成：

```bash
# 後端產生 OpenAPI spec
backend/src/main.py:app → /openapi.json

# 前端 codegen
npm run generate-types
# 用 openapi-typescript-codegen
# 產生 frontend/src/api/generated/rest/
```

#### B. SSE Event 類型（Pydantic → JSON Schema → TS codegen，**新增**）

```
agent_harness/_contracts/events.py (Pydantic)
        ↓ pydantic.schema() / 自訂 export script
backend/schemas/events.json (JSON Schema)
        ↓ json-schema-to-typescript
frontend/src/api/generated/events.ts (TypeScript)
```

```bash
# 後端 export script（CI 強制更新）
cd backend
python scripts/export_event_schemas.py
# → backend/schemas/events.json (含 22 個 LoopEvent 子類完整定義)

# 前端 codegen（npm script）
cd frontend
npm run generate-event-types
# 用 json-schema-to-typescript
# → frontend/src/api/generated/events.ts
```

```typescript
// frontend/src/api/generated/events.ts (auto-generated)
export type LoopEvent =
  | LoopStarted
  | Thinking
  | ToolCallRequested
  | ToolCallExecuted
  // ... 22 個子類

export interface LoopStarted {
  type: 'LoopStarted'
  streaming_seq: number
  trace_context: TraceContext
  timestamp: string
  payload: { session_id: string; ... }
}
// ... 21 more interfaces
```

#### C. CI 強制同步 check

```yaml
# .github/workflows/event-schema-sync.yml
on: [pull_request]
jobs:
  schema-sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: cd backend && python scripts/export_event_schemas.py
      - run: cd frontend && npm run generate-event-types
      - run: |
          # 若 generated 檔案有變動，PR 必須 commit
          git diff --exit-code backend/schemas/events.json frontend/src/api/generated/events.ts \
            || (echo "Event schemas out of sync. Re-run codegen and commit." && exit 1)
```

#### D. 替代方案：AsyncAPI（次選）

若 Pydantic export 流程變複雜，可考慮 **AsyncAPI 3.0**（事件驅動 API 標準）：
- 後端用 `asyncapi-python` 從 Pydantic 模型產生 AsyncAPI spec
- 前端用 `asyncapi-codegen` 產生 TS types
- 優點：標準化（OpenAPI 對 REST，AsyncAPI 對 SSE/WS）
- 缺點：工具鏈較不成熟

**決策**：Phase 50.2 先用 Pydantic → JSON Schema → TS（簡單）；若需要 documenting / API portal，Phase 56+ 考慮升 AsyncAPI。

### 共享類型

```typescript
// frontend/src/types/loop.ts
import type { 
  LoopEvent,        // SSE 事件 union
  Message,
  ToolCall,
  ToolResult,
  VerificationResult,
} from '@/api/generated'

// SSE 事件 discriminated union
export type LoopEvent =
  | { type: 'loop_start'; data: { request_id: string; session_id: string } }
  | { type: 'turn_start'; data: { turn_num: number } }
  | { type: 'llm_request'; data: { model: string; tokens_in: number } }
  | { type: 'llm_response'; data: { content?: string; tool_calls?: ToolCall[]; thinking?: string } }
  | { type: 'tool_call_request'; data: { tool_name: string; args: any } }
  | { type: 'tool_call_result'; data: { tool_name: string; result: any; is_error: boolean } }
  | { type: 'guardrail_check'; data: { layer: string; passed: boolean } }
  | { type: 'tripwire_fired'; data: { reason: string } }
  | { type: 'compaction_triggered'; data: { tokens_before: number; tokens_after: number } }
  | { type: 'hitl_required'; data: { approval_id: string; prompt: string } }
  | { type: 'verification_start'; data: { verifier_type: string } }
  | { type: 'verification_result'; data: { passed: boolean; reason?: string } }
  | { type: 'loop_end'; data: { result: any; total_turns: number; total_tokens: number } }
```

---

## 性能預算

### Bundle Size

| 區段 | 目標 | 上限 |
|------|------|------|
| Initial JS | < 200KB gzip | 300KB |
| Initial CSS | < 30KB gzip | 50KB |
| Total assets | < 500KB gzip | 1MB |

### Runtime Performance

| 指標 | 目標 | 上限 |
|------|------|------|
| FCP（First Contentful Paint） | < 1s | 2s |
| LCP（Largest Contentful Paint） | < 2s | 3s |
| TTI（Time to Interactive） | < 3s | 5s |
| CLS（Cumulative Layout Shift） | < 0.1 | 0.25 |
| INP（Interaction to Next Paint） | < 200ms | 500ms |

### 優化策略

- Route-based code splitting
- Lazy load DevUI（admin / power user 才載入）
- Virtualized long lists（messages / audit log）
- React.memo + useMemo 用在重點組件
- 圖片 lazy load + responsive

---

## Accessibility（WCAG 2.1 AA）

### 必須達成

- 所有互動元素 keyboard accessible
- Color contrast ≥ 4.5:1（normal text）/ 3:1（large text）
- Form labels + error messages 清楚
- ARIA labels for icon-only buttons
- Focus indicators 明顯
- Screen reader friendly（特別是 SSE stream）

### Tools

- ESLint + eslint-plugin-jsx-a11y
- axe-core 自動測試
- Manual testing with NVDA / VoiceOver

---

## Internationalization（i18n）

### 支援語言（Phase 55+）

| Locale | Status |
|--------|--------|
| en | 預設 |
| zh-TW | 必需（公司主要） |
| zh-CN | 可選 |
| ja | Phase 60+ 考慮 |

### 工具

- **react-i18next**
- 翻譯檔：`frontend/src/locales/{locale}/*.json`
- Lazy load 對應 locale

```typescript
// 使用範例
const { t } = useTranslation('chat')
<button>{t('send')}</button>
// locales/zh-TW/chat.json: { "send": "送出" }
```

---

## DevUI 規劃

### DevUI 是什麼

給開發者 / admin / power user 用的**深度 debug 介面**。

### Pages

```
/devui/
├── /loop-visualizer      # 即時 loop 流程圖
├── /category-dashboard   # 11 範疇成熟度
├── /state-time-travel    # 跨 checkpoint 比較
├── /prompt-inspector     # 看 LLM 實際 prompt
├── /cost-tracker         # 即時成本追蹤
├── /event-stream         # Raw SSE event log
├── /db-explorer          # 限定唯讀的 DB 查詢（admin only）
└── /performance-traces   # OTel traces 視覺化
```

### LoopVisualizer 範例

```
┌──────────────────────────────────────────────┐
│ Session ID: ...   [Pause] [Step] [Resume]   │
├──────────────────────────────────────────────┤
│                                              │
│  [User Input]                                │
│      ↓                                        │
│  [PromptBuilder]  ← tokens: 1.2K              │
│      ↓                                        │
│  [LLM Request: Azure OpenAI GPT-5.4]          │
│      ↓                                        │
│  [Response: tool_call=salesforce_query]       │
│      ↓                                        │
│  [Guardrail Check: ✅]                        │
│      ↓                                        │
│  [Tool Execution: ⏳ 1.5s]                    │
│      ↓                                        │
│  [Tool Result: 234 records]                   │
│      ↓                                        │
│  [Loop back to PromptBuilder]                │
│                                              │
│  Turn: 3/50                                  │
│  Tokens: 8.5K / 100K                         │
│  Cost: $0.024                                │
└──────────────────────────────────────────────┘
```

---

## 部署與 Build

### Build 流程

```bash
# Production build
npm run build
# → 產生 dist/ 含 hashed assets

# Docker
docker build -t ipa-frontend:latest .
# → multi-stage：Node build → Nginx serve
```

### Environment Variables

```typescript
// frontend/.env.example
VITE_API_BASE_URL=http://localhost:8000
VITE_SSE_BASE_URL=http://localhost:8000
VITE_TENANT_ID_OVERRIDE=  # dev only
VITE_FEATURE_DEVUI=true
VITE_FEATURE_DEBUG=false
```

### Code Splitting

```typescript
// router.tsx
const ChatPage = lazy(() => import('@/pages/chat'))
const DevUI = lazy(() => import('@/pages/devui'))
const AdminPage = lazy(() => import('@/pages/admin'))

// 普通用戶不下載 DevUI / Admin code
```

---

## Frontend Testing

### 測試金字塔

```
E2E (Playwright)
  ↑
Component (Testing Library)
  ↑
Unit (Vitest)
```

### 必測案例

```
Unit:
- 各 component 渲染
- Hooks 邏輯
- Utility functions

Component:
- ChatPage 完整互動
- HITLApprovalCard flow
- ToolCallCard 展開折疊

E2E:
- Login → Chat → Send message → Receive response
- HITL approval flow
- Session resume after pause
```

---

## Phase 對應

| Phase | Frontend deliverable |
|-------|----------------------|
| Phase 49.1 | 目錄骨架 + 基本 routing + auth login |
| Phase 50.2 | Chat 頁面 + SSE stream + LoopVisualizer 雛形 |
| Phase 51 | Memory / Tools 頁面 |
| Phase 52 | DevUI 系列（PromptInspector / CostTracker） |
| Phase 53 | Governance 頁面（HITL queue / Audit log） |
| Phase 54 | Verification panel + Subagent tree |
| Phase 55 | Admin / Tenant onboarding wizard + i18n |

---

## V2 Ship Timeline (NEW Sprint 57.6 US-4 — closes AD-Reality-4-partial / R4)

**Modification History (newest-first)**
- 2026-05-09: Sprint 57.9 Day 4 — governance promoted to **shipped** (6/N counter); 5 ship → **6 ship**; TanStack Query 4-page migration noted (closes AD-Cost-Dashboard-UseQuery via Day 4 batch); Phase 57.10 priority remaining = verification (1 priority instead of 2 since governance closed); + audit log frontend now part of governance ship (sub-tab `/governance/audit-log`)
- 2026-05-09: Sprint 57.8 Day 4 — chat-v2 promoted to **shipped** (5/N counter); 4 ship → **5 ship**; AppShell V2 architecture migration noted (architecture-first Day 0 Decision Z); Phase 57.9 priority remaining = governance + verification (2 priority instead of 3 since chat-v2 closed)
- 2026-05-08: Sprint 57.6 Day 3 US-4 — add V2 Ship Timeline section per Decision 3 (a) (closes AD-Reality-4-partial + AD-Reality-7). Honest reality framing: Phase 57+ frontend SaaS 推進 N/12 真實 ship status, NOT V3 defer.

### Reality framing

V2 重構完成（Phase 49-55,22/22 sprint）+ Phase 56-58 SaaS Stage 1 backend 3/3 已 ship。Frontend 部分按 Phase 57+ 逐個 ship。Sprint 57.5 reality check 確認 12-page claim vs 真實 ship status。Sprint 57.8 完成架構遷移 (AppShell V2 + Sidebar + UserMenu + routes.config single-source) → 後續 Phase 58.x frontend page ship 享 zero per-page architecture cost。Sprint 57.9 完成 TanStack Query 4-page batch migration → server cache 與 UI state 分離 (Zustand UI-only),pattern reuse 加速後續 page ship。**此 timeline 非 V3 defer**:Phase 57.x sprint 將逐個 ship 真實 page 至 Phase 58 production launch 前完成關鍵 priority。

### 6 已 ship pages

| Page | Sprint | Backend | Status |
|------|--------|---------|--------|
| cost-dashboard | 57.1 + 57.7 AppShell + 57.8 A1 + **57.9 TanStack** | 56.3 cost_ledger backend | ✅ Production ship + Sprint 57.9 US-6 TanStack migration (useCostSummary hook + costStore reduced UI-only); 10 Vitest + 2 Playwright e2e |
| sla-dashboard | 57.1 + 57.8 A1 + **57.9 TanStack** | 56.3 SLA monitor backend | ✅ Production ship + Sprint 57.9 US-6 TanStack migration (useSLAReport hook + slaStore reduced UI-only + Tailwind drop ALL inline styles); 8 Vitest + 2 Playwright e2e |
| tenant-settings | 57.3 + 57.8 A1 + **57.9 TanStack mutation** | 56.1 + 57.3 admin tenants.py R+U | ✅ Production ship + Sprint 57.9 US-6 TanStack query+mutation hook (useTenantSettings + useTenantSettingsSave + tenantSettingsStore reduced UI-only + EditForm NEW tenantId prop); 10 Vitest + 4 Playwright e2e |
| admin-tenants list | 57.4 + 57.8 A1 + **57.9 TanStack** | 57.4 admin tenants.py list endpoint | ✅ Production ship + Sprint 57.9 US-6 TanStack migration (useAdminTenants hook + adminTenantsStore reduced UI-only query state + 3 children consume hook); 13 Vitest + 4 Playwright e2e |
| chat-v2 | 57.8 US-5 | 50.2 + Cat 1+2+9+10+12 | ✅ Sprint 57.8 ship (auth gate via Navigate first auth-gated page + AppShellV2 wrap + ChatLayout reuse + chatService fetchWithAuth + 4 Playwright e2e) |
| **governance** | **57.9 US-1+2+3+4+5** | 53.5 (HITL backend) + 53.5 US-5+6 (audit + chain verify) | ✅ **NEW Sprint 57.9 ship**: auth gate via Navigate + AppShellV2 wrap + 2-tab nested Routes (`/governance/approvals` + `/governance/audit-log`) + Tailwind migration 3 components + TanStack hooks (useApprovals + useApprovalDecide single-source APPROVALS_QUERY_KEY) + AuditLogViewer real impl with auditService + useAuditLog + 4-field filter form draft-vs-committed + 6-col paginated table + AuditChainBadge enabled:false manual trigger 4 states; closes AD-Cost-Dashboard-UseQuery via Day 4 4-page batch; 18 Vitest (governance + audit) + 5 Playwright e2e (post-Day 4 fix authenticated via seedAuthJwt beforeEach) |

### 1 priority Phase 57.10+ ship (~10-12 hr — governance closed Sprint 57.9)

| Page | Backend ready since | Sprint candidate | Notes |
|------|---------------------|------------------|-------|
| verification panel | 54.1 + 54.2 | Phase 57.10 (TBD per user) | Replace placeholder with verifier output + correction loop visibility; AD-Cat10-Frontend-Panel scope; AppShellV2 wrap + TanStack pattern free benefit per Sprint 57.8+57.9 architecture (highest pattern-reuse ROI same as governance ship) |

### 5 deferred (Phase 57.10-57.13+ ~5-7 sprints)

| Page | Backend status | Defer rationale |
|------|----------------|-----------------|
| agents / workflows | Cat 1+11 ship 50.1 + 54.2 | Lower priority — internal admin use; user not blocking |
| incidents | business_domain/incident 51.0 + 55.1 | Mock-mode only;real-mode swap pending business onboarding |
| memory inspector | Cat 3 ship 51.2 | Power-user DevUI feature;低 priority production user |
| audit log frontend | 53.5 + 53.6 backend | Phase 57.x candidate consume `mixed-pattern-reuse` ~0.40 fast ROI per AD-Sprint-Plan-6 |
| tools / admin-extended / dashboard-extended / devui | mixed | Lower-priority DevUI / admin tooling;defer to V3 production hardening or per real demand |

### Sprint slot mapping (rolling planning;non-binding)

| Sprint | Page | Effort | Notes |
|--------|------|--------|-------|
| Phase 57.7 | IAM Foundation + Frontend Foundation 1/N spike | actual ~16.5 hr | ✅ DONE — Sprint 57.7 PR #117 merged main `51162fd5`;NOT chat-v2 (architecture pivot per Day 0 Decision Z carry-forward to 57.8) |
| Phase 57.8 | **AppShell V2 + chat-v2 real ship** | actual ~12 hr | ✅ DONE — Sprint 57.8 closeout; 5 USs (US-1+2+3+4 architecture + US-5 chat-v2 ship) |
| Phase 57.9 | **governance real ship + TanStack Query 4-page batch migration** | actual ~10.5 hr | ✅ DONE — Sprint 57.9 closeout; 6 USs (US-1+2+3 governance auth gate+Tailwind+TanStack hooks + US-4+5 AuditLogViewer+AuditChainBadge real impl + US-6 4-page TanStack migration closes AD-Cost-Dashboard-UseQuery); calibration `frontend-feature-with-migration` 0.50 1st app ratio 1.00 ✅ bullseye |
| Phase 57.10+ | verification real ship OR deferred 5 OR SOC 2 + SBOM / Status Page + APAC / Tier 1 IaC / Stage 2 SaaS | various | Per rolling planning 紀律 — user instruct each sprint scope; verification = highest pattern-reuse ROI same as governance ship |

**NOT V3 defer statement** (per Sprint 57.5 Day 4.5 Decision 3 (a)):此 frontend 推進是 Phase 57.x V2 closure scope,NOT push to V3。V3 production launch (Phase 58+) 預期 2026 Q3-Q4 已具備所有 priority 3 page + 部分 deferred 5。逐個 ship 而非 big-bang launch — 與 V2 22/22 漸進式紀律一致。

---

## 結語

V2 frontend：
- ✅ 全新開發（V1 chat / agent-swarm 封存）
- ✅ 按 11 範疇組織 features
- ✅ Loop-first UI（不是 pipeline）
- ✅ 透明度為核心（thinking / tool / verification 全可見）
- ✅ 治理 native（HITL 是核心 UX）
- ✅ DevUI 給 power users
- ✅ A11y / i18n / 性能都顧

**前端複雜度高於後端，建議 Phase 50.2 起平行多人開發**。
