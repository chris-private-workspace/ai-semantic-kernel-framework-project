# Phase 40: Frontend Enhancement — E2E Workflow UI

## 概述

Phase 40 專注於 **前端改善**，建立缺少的 UI 頁面和組件，讓 E2E 工作流程能在前端完整測試和操作。

基於 Agent Team 討論結論（前端架構師 + UX 設計師 + 後端顧問），後端 API 已 95% 就緒，前端需要 5 個新頁面/改造才能支持完整的 10 步 E2E 流程。

> **Status**: ✅ 已完成 — 3 Sprints (138-140), 30 SP

## 核心問題

1. **UnifiedChat 未連接新 Pipeline** — 現有 Chat 頁面不使用 `/orchestrator/chat` 端點
2. **Session 管理缺失** — ChatHistoryPanel 用 localStorage，未對接後端 Session API
3. **任務追蹤無 UI** — dispatch 出去的任務無法在前端查看進度
4. **知識庫/記憶無管理介面** — Step 10 的知識和記憶系統無前端入口

## 設計原則（UX 設計師建議）

1. **Chat-Centric** — 核心流程不離開 Chat 頁面，用內聯卡片取代頁面跳轉
2. **漸進式揭露** — 簡單問答不顯示複雜 UI，Workflow/Swarm 時才展開
3. **最少頁面切換** — 輔助功能通過 Sidebar 進入，核心操作在 Chat 完成

## 前置條件

- ✅ Phase 39 (E2E Assembly D) 完成 — 後端 Pipeline 組裝完畢
- ✅ 後端 API 95% 就緒（~50+ endpoints）
- ✅ `user-expected-workflow.md` baseline 文件建立
- ✅ React 18 + TypeScript + Shadcn UI + Zustand + React Query 技術棧就緒

## Sprint 規劃

| Sprint | 名稱 | Story Points | 狀態 |
|--------|------|--------------|------|
| [Sprint 138](./sprint-138-plan.md) | Orchestrator Chat 增強 + Session 管理 | 12 點 | ✅ 已完成 |
| [Sprint 139](./sprint-139-plan.md) | Task Dashboard + 內聯進度組件 | 10 點 | ✅ 已完成 |
| [Sprint 140](./sprint-140-plan.md) | Knowledge 管理 + Memory 檢視 + 導航更新 | 8 點 | ✅ 已完成 |

**總計**: ~30 Story Points (3 Sprints)

## 架構概覽

### 頁面導航結構

```
Login → Dashboard（概覽）→ Chat（核心操作）
                              ├── 左側：Session 列表（含 Recoverable Sessions）
                              ├── 中間：對話 + 內聯狀態卡片
                              │         ├── IntentStatusChip（意圖/風險）
                              │         ├── TaskProgressCard（任務進度）
                              │         └── MemoryHint（記憶提示）
                              └── 右側：OrchestrationPanel（自適應）
         ↓
Sidebar 導航：
  ├── Dashboard          （已有）
  ├── AI 助手 / Chat     （增強：連接 /orchestrator/chat）
  ├── Sessions 管理      （新增：Session CRUD + Resume）
  ├── 任務中心           （新增：Task Dashboard）
  ├── 知識庫             （新增：Knowledge 管理）
  ├── 記憶系統           （新增：Memory 檢視）
  ├── 工作流             （已有）
  ├── Agents             （已有）
  ├── 審批中心           （已有）
  ├── 審計日誌           （已有）
  └── DevUI              （已有）
```

### E2E 步驟 → UI 映射

| Step | 用戶看到什麼 | UI 元素 | 位置 |
|------|------------|---------|------|
| 1. 登入 | Login 頁面 | LoginPage（已有） | 獨立頁面 |
| 2. Session | 左側 Session 列表（進行中 + 可恢復） | 改造 ChatHistoryPanel | Chat 左側 |
| 3. 意圖+風險 | 內聯狀態提示：「意圖：XXX｜風險：LOW」 | IntentStatusChip（新增） | Chat 中間 |
| 4. 決策 | 狀態提示更新：「模式：Workflow」 | IntentStatusChip 擴展 | Chat 中間 |
| 5. 任務分發 | 任務卡片：task_id + 進度條 | TaskProgressCard（新增） | Chat 中間 |
| 6. 工具調用 | 卡片內展開工具步驟 | ToolCallTracker（已有） | Chat 中間 |
| 7. SSE 串流 | 打字效果 + 進度動畫 | ChatArea（已有） | Chat 中間 |
| 8. 統一回應 | 最終回覆 | MessageList（已有） | Chat 中間 |
| 9. Resume | 「可恢復 Sessions」區塊 + 恢復按鈕 | 改造 ChatHistoryPanel | Chat 左側 |
| 10. 記憶+知識 | 記憶提示 + Sidebar 知識庫入口 | MemoryHint + KnowledgePage | Chat + 獨立頁面 |

## 新增檔案清單

### Sprint 138（P0 核心）
```
frontend/src/
├── api/endpoints/
│   ├── orchestrator.ts          # Orchestrator Chat API
│   └── sessions.ts              # Session CRUD + Recovery API
├── hooks/
│   ├── useOrchestratorChat.ts   # Orchestrator chat hook
│   └── useSessions.ts           # Session management hooks
├── pages/sessions/
│   ├── SessionsPage.tsx         # Session 列表頁
│   └── SessionDetailPage.tsx    # Session 詳情頁
└── components/unified-chat/
    └── IntentStatusChip.tsx      # 內聯意圖/風險提示
```

### Sprint 139（P0 任務）
```
frontend/src/
├── api/endpoints/
│   └── tasks.ts                 # Task CRUD API
├── hooks/
│   └── useTasks.ts              # Task management hooks
├── pages/tasks/
│   ├── TaskDashboardPage.tsx    # 任務中心
│   └── TaskDetailPage.tsx       # 任務詳情
└── components/unified-chat/
    └── TaskProgressCard.tsx      # 內聯任務進度卡片
```

### Sprint 140（P1 知識+記憶）
```
frontend/src/
├── api/endpoints/
│   ├── knowledge.ts             # Knowledge API
│   └── memory.ts                # Memory API
├── hooks/
│   ├── useKnowledge.ts          # Knowledge hooks
│   └── useMemory.ts             # Memory hooks
├── pages/
│   ├── knowledge/KnowledgePage.tsx  # 知識庫管理
│   └── memory/MemoryPage.tsx        # 記憶檢視
└── components/unified-chat/
    └── MemoryHint.tsx            # 記憶提示條
```

## 風險與緩解

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| ChatHistoryPanel localStorage → 後端遷移是破壞性變更 | 高 | 漸進式：先加「可恢復」區塊，保留現有 thread 邏輯 |
| UnifiedChat 改造可能影響現有功能 | 中 | 新增 useOrchestratorChat hook，不修改現有 hooks |
| 知識庫頁面依賴 Qdrant 服務 | 低 | 頁面檢測服務狀態，不可用時顯示提示 |

## 成功標準

- [ ] 用戶可通過 Chat 頁面發送請求到 `/orchestrator/chat` 並收到回應
- [ ] 用戶可在 Session 列表看到所有 Sessions 並 Resume 中斷的 Session
- [ ] 用戶可在 Task Dashboard 追蹤 dispatch 出去的任務進度
- [ ] 用戶可在知識庫頁面上傳文檔和搜索
- [ ] 用戶可在記憶頁面查看和搜索歷史記憶
- [ ] Sidebar 導航包含所有新頁面入口
- [ ] 所有新頁面使用 Shadcn UI + TypeScript + React Query

---

**Phase 40 前置**: Phase 39 (E2E Assembly D) 完成
**總 Story Points**: ~30 pts
**Sprint 範圍**: Sprint 138-140
**技術棧**: React 18 + TypeScript + Shadcn UI + Zustand + React Query
