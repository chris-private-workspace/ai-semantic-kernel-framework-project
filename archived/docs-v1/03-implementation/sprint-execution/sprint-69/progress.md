# Sprint 69 Progress: Claude Code UI + Dashboard Integration

> **Phase 17**: Agentic Chat Enhancement
> **Sprint 目標**: 層級進度顯示、Dashboard 整合、Guest User ID 完善

---

## Sprint 概述

| 屬性 | 值 |
|------|-----|
| Sprint 編號 | 69 |
| 計劃點數 | 21 Story Points |
| 完成點數 | 21 Story Points |
| 開始日期 | 2026-01-08 |
| 完成日期 | 2026-01-08 |
| Phase | 17 - Agentic Chat Enhancement |
| 前置條件 | Sprint 68 完成、AG-UI CUSTOM 事件運作中 |

---

## Story 進度

| Story | 名稱 | 點數 | 狀態 | 進度 |
|-------|------|------|------|------|
| S69-1 | step_progress Backend Event | 5 | ✅ 完成 | 100% |
| S69-2 | StepProgress Sub-step Component | 5 | ✅ 完成 | 100% |
| S69-3 | Progress Event Integration | 3 | ✅ 完成 | 100% |
| S69-4 | Dashboard Layout Integration | 5 | ✅ 完成 | 100% |
| S69-5 | Guest User ID Implementation | 3 | ✅ 完成 | 100% |

**整體進度**: 21/21 pts (100%) ✅

---

## 詳細進度記錄

### S69-1: step_progress Backend Event (5 pts)

**狀態**: ✅ 完成

**任務清單**:
- [x] 定義 `SubStepStatus` enum
- [x] 定義 `SubStep` dataclass
- [x] 定義 `StepProgressPayload` dataclass
- [x] 實現 `StepProgressTracker` 類
- [x] 實現 `create_step_progress_event()` 函數
- [x] 實現 `emit_step_progress()` 輔助函數
- [x] 導出至 events package `__init__.py`

**新增檔案**:
- [x] `backend/src/integrations/ag_ui/events/progress.py`

**修改檔案**:
- [x] `backend/src/integrations/ag_ui/events/__init__.py` - 導出新類型

**代碼模式**:
```python
@dataclass
class SubStep:
    id: str
    name: str
    status: SubStepStatus
    progress: Optional[int] = None
    message: Optional[str] = None

@dataclass
class StepProgressPayload:
    step_id: str
    step_name: str
    current: int
    total: int
    progress: int  # 0-100
    status: SubStepStatus
    substeps: List[SubStep]
```

---

### S69-2: StepProgress Sub-step Component (5 pts)

**狀態**: ✅ 完成

**任務清單**:
- [x] 創建 `StepProgressEnhanced.tsx`
- [x] 創建 `SubStepItem` 組件
- [x] 實現 `StatusIcon` 組件
- [x] 添加主步驟標題與進度
- [x] 添加可折疊子步驟列表
- [x] 顯示進度百分比
- [x] 添加展開/折疊動畫 (CSS transition)
- [x] 尊重 `prefers-reduced-motion` 偏好
- [x] 導出至 unified-chat index

**新增檔案**:
- [x] `frontend/src/components/unified-chat/StepProgressEnhanced.tsx`

**修改檔案**:
- [x] `frontend/src/components/unified-chat/index.ts` - 導出新組件
- [x] `frontend/src/types/unified-chat.ts` - 新類型定義

**視覺呈現**:
```
Step 2/5: Process documents (45%)  [████░░░░░░]
  ├─ ✓ Load files
  ├─ ◉ Parse content (67%)
  ├─ ○ Analyze structure
  └─ ○ Generate summary
```

---

### S69-3: Progress Event Integration (3 pts)

**狀態**: ✅ 完成

**任務清單**:
- [x] 在 useAGUI 定義 `StepProgressState` 類型
- [x] 在 useAGUI 處理 `step_progress` CUSTOM 事件
- [x] 儲存 step progress 狀態 (Map)
- [x] 提供 `currentStepProgress` getter
- [x] 運行完成時清除進度
- [x] 在返回值中導出 `stepProgress` 和 `currentStepProgress`

**修改檔案**:
- [x] `frontend/src/hooks/useAGUI.ts`

**代碼模式**:
```typescript
const [stepProgress, setStepProgress] = useState<StepProgressState>({
  steps: new Map(),
  currentStep: null,
});

// 在 CUSTOM 事件處理中
else if (eventName === 'step_progress') {
  // Parse payload and update state
  setStepProgress((prev) => {
    const newSteps = new Map(prev.steps);
    newSteps.set(progressEvent.stepId, progressEvent);
    return { steps: newSteps, currentStep: progressEvent.stepId };
  });
}
```

---

### S69-4: Dashboard Layout Integration (5 pts)

**狀態**: ✅ 完成

**任務清單**:
- [x] 將 `/chat` 路由從獨立路由移至 AppLayout 子路由
- [x] 在 Sidebar 添加 "AI 助手" 導航項 (MessageSquare 圖標)
- [x] 將 UnifiedChat 從 `h-screen` 改為 `h-full`
- [x] 更新文件標頭註釋

**修改檔案**:
- [x] `frontend/src/App.tsx` - 路由變更
- [x] `frontend/src/components/layout/Sidebar.tsx` - 添加導航項
- [x] `frontend/src/pages/UnifiedChat.tsx` - 布局適配

**路由變更**:
```tsx
// Before:
<Route path="/chat" element={<UnifiedChat />} />  // 獨立路由

// After:
<Route path="/" element={<AppLayout />}>
  <Route path="chat" element={<UnifiedChat />} />  // AppLayout 子路由
  ...
</Route>
```

---

### S69-5: Guest User ID Implementation (3 pts)

**狀態**: ✅ 完成

**任務清單**:
- [x] 驗證 `guestUser.ts` 已存在 (Sprint 68 已實現)
- [x] 在 API client 中整合 `X-Guest-Id` header
- [x] 驗證後端 `get_user_id` dependency 已存在
- [x] `migrateGuestData()` 已在 guestUser.ts 中實現

**修改檔案**:
- [x] `frontend/src/api/client.ts` - 添加 X-Guest-Id header

**代碼模式**:
```typescript
import { getGuestHeaders } from '@/utils/guestUser';

async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const guestHeaders = getGuestHeaders();  // { 'X-Guest-Id': 'guest-xxx' }

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...guestHeaders,  // S69-5: Include X-Guest-Id for sandbox isolation
    ...options?.headers,
  };
  // ...
}
```

---

## 技術備註

### Event Flow

```
Backend Workflow Execution
         │
         ▼
   emit_step_progress()
         │
         ▼
   CustomEvent(step_progress)
         │
         ▼
   SSE Stream
         │
         ▼
   Frontend useAGUI
         │
         ▼
   StepProgressEnhanced component
```

### Dashboard 整合架構

```
┌───────────────────────────────────────────────────────────┐
│                        AppLayout                           │
├──────────────┬────────────────────────────────────────────┤
│              │                                            │
│   Sidebar    │              UnifiedChat                   │
│              │   ┌────────────────────────────────────┐   │
│  - Dashboard │   │  ChatHeader (Internal Page Header) │   │
│  - AI 助手   │   ├────────────────────────────────────┤   │
│  - 效能監控  │   │  ChatArea / WorkflowSidePanel      │   │
│  - 工作流    │   │                                    │   │
│  - Agents    │   ├────────────────────────────────────┤   │
│  - ...       │   │  ChatInput                         │   │
│              │   ├────────────────────────────────────┤   │
│              │   │  StatusBar                         │   │
│              │   └────────────────────────────────────┘   │
└──────────────┴────────────────────────────────────────────┘
```

---

## 新增/修改檔案總覽

### 新增檔案
| 檔案 | 說明 |
|------|------|
| `backend/src/integrations/ag_ui/events/progress.py` | Step progress 後端事件類型和 Tracker |
| `frontend/src/components/unified-chat/StepProgressEnhanced.tsx` | 層級進度組件 |

### 修改檔案
| 檔案 | 說明 |
|------|------|
| `backend/src/integrations/ag_ui/events/__init__.py` | 導出新類型 |
| `frontend/src/components/unified-chat/index.ts` | 導出 StepProgressEnhanced |
| `frontend/src/types/unified-chat.ts` | 新增進度類型定義 |
| `frontend/src/hooks/useAGUI.ts` | step_progress 事件處理 |
| `frontend/src/App.tsx` | Chat 路由整合至 AppLayout |
| `frontend/src/components/layout/Sidebar.tsx` | 添加 AI 助手導航 |
| `frontend/src/pages/UnifiedChat.tsx` | h-screen → h-full |
| `frontend/src/api/client.ts` | X-Guest-Id header 整合 |

---

**更新日期**: 2026-01-08
**Sprint 狀態**: ✅ 完成
