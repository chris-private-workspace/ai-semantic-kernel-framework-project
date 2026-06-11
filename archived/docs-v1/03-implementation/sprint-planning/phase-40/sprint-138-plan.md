# Sprint 138: Orchestrator Chat 增強 + Session 管理

## Sprint 目標

1. useOrchestratorChat hook + API endpoints — 連接 UnifiedChat 到 /orchestrator/chat
2. Session 管理頁面 — Session 列表 + 詳情頁（含狀態篩選和訊息歷史）
3. ChatHistoryPanel 改造 — 加入可恢復 Sessions 區塊 + Resume 功能
4. IntentStatusChip 內聯組件 — 在 Chat 訊息中顯示意圖/風險/執行模式
5. Sidebar + App.tsx 路由更新 — 新增 Sessions 導航入口

## Sprint 週期

| 項目 | 值 |
|------|-----|
| **Phase** | Phase 40 — Frontend Enhancement: E2E Workflow UI |
| **Sprint** | 138 |
| **Story Points** | 12 點 |
| **狀態** | 📋 計劃中 |

## Sprint 概述

Sprint 138 是 Phase 40 的第一個 Sprint，專注於建立 Orchestrator Chat 的前端連接和 Session 管理功能。包含 useOrchestratorChat hook 連接 `/orchestrator/chat` 端點、Session 管理頁面（列表 + 詳情含狀態篩選）、ChatHistoryPanel 改造（加入可恢復 Sessions 區塊和 Resume 按鈕）、IntentStatusChip 內聯組件（在聊天訊息中顯示意圖類別、風險等級、執行模式）、以及 Sidebar 和 App.tsx 路由更新。

## User Stories

### S138-1: useOrchestratorChat hook + API endpoints (3 SP)

**作為** 前端使用者
**我希望** Chat 頁面能連接到 `/orchestrator/chat` 端點
**以便** 我的訊息能經過完整的 Orchestrator 管線處理並獲得回應

**技術規格**:
- 新增 `frontend/src/api/endpoints/orchestrator.ts`
  - `sendOrchestratorMessage(sessionId, message)` — POST /orchestrator/chat
  - `getOrchestratorStatus()` — GET /orchestrator/health
  - SSE 串流支援 — 連接 /orchestrator/chat/stream
- 新增 `frontend/src/hooks/useOrchestratorChat.ts`
  - `useOrchestratorChat(sessionId)` hook
  - 管理 messages state、loading state、error state
  - 支援 SSE 串流回應（透過 EventSource）
  - 自動重連機制（斷線後 3 秒重連）
  - 回傳 `{ messages, sendMessage, isLoading, error, isConnected }`
- 修改 `frontend/src/components/unified-chat/` 相關組件
  - 連接 useOrchestratorChat hook 取代現有直接 API 呼叫
  - 保留現有 UI 結構，僅替換資料來源

### S138-2: Session 管理頁面 (3 SP)

**作為** 前端使用者
**我希望** 有一個專門的 Session 管理頁面
**以便** 我能查看所有 Sessions 的狀態、瀏覽訊息歷史、並管理 Session 生命週期

**技術規格**:
- 新增 `frontend/src/api/endpoints/sessions.ts`
  - `getSessions(filters)` — GET /sessions（支援 status 篩選）
  - `getSession(id)` — GET /sessions/{id}
  - `getSessionMessages(id)` — GET /sessions/{id}/messages
  - `getRecoverableSessions()` — GET /sessions/recoverable
  - `resumeSession(id)` — POST /sessions/{id}/resume
  - `deleteSession(id)` — DELETE /sessions/{id}
- 新增 `frontend/src/hooks/useSessions.ts`
  - `useSessions(filters)` — 列表查詢 hook（React Query）
  - `useSession(id)` — 單一 Session 查詢 hook
  - `useSessionMessages(id)` — 訊息歷史查詢 hook
  - `useResumeSession()` — Resume mutation hook
- 新增 `frontend/src/pages/sessions/SessionsPage.tsx`
  - Session 列表頁面
  - 狀態篩選器（active / completed / interrupted / recoverable）
  - 表格顯示：Session ID、建立時間、最後更新、狀態、訊息數量
  - 操作按鈕：查看詳情、Resume、刪除
  - 使用 Shadcn UI Table + Badge + Select 組件
- 新增 `frontend/src/pages/sessions/SessionDetailPage.tsx`
  - Session 詳情頁面
  - 顯示 Session metadata（ID、建立時間、狀態、Agent 資訊）
  - 訊息歷史時間軸（含角色標記：user / assistant / system）
  - 返回列表按鈕

### S138-3: ChatHistoryPanel 改造 (3 SP)

**作為** 前端使用者
**我希望** Chat 側邊欄顯示可恢復的 Sessions
**以便** 我能快速恢復之前中斷的對話，而不需要開新的 Session

**技術規格**:
- 修改 `frontend/src/components/unified-chat/ChatHistoryPanel.tsx`
  - 在現有 thread 列表上方新增「可恢復 Sessions」區塊
  - 呼叫 `GET /sessions/recoverable` 取得可恢復 Session 列表
  - 每個可恢復 Session 顯示：最後訊息摘要、中斷時間、狀態 Badge
  - Resume 按鈕 → 呼叫 `POST /sessions/{id}/resume`
  - Resume 成功後自動切換到該 Session 的對話
  - 保留現有 localStorage thread 邏輯（漸進式遷移）
  - 可恢復區塊可摺疊/展開（預設展開）
  - 使用 Shadcn UI Collapsible + Button + Badge 組件

### S138-4: IntentStatusChip 內聯組件 (2 SP)

**作為** 前端使用者
**我希望** 在 Chat 訊息中看到意圖分析結果
**以便** 我能了解系統如何理解我的請求、評估的風險等級、以及選擇的執行模式

**技術規格**:
- 新增 `frontend/src/components/unified-chat/IntentStatusChip.tsx`
  - Props: `{ intent: string; riskLevel: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'; executionMode: string; }`
  - 內聯顯示格式：「意圖：{intent} | 風險：{riskLevel} | 模式：{executionMode}」
  - 風險等級色彩：LOW=綠色、MEDIUM=黃色、HIGH=橙色、CRITICAL=紅色
  - 可展開詳細資訊（點擊展開顯示完整意圖分析）
  - 使用 Shadcn UI Badge + Tooltip + Collapsible 組件
  - 響應式設計：小螢幕只顯示圖標，hover 顯示完整資訊

### S138-5: Sidebar + App.tsx 路由更新 (1 SP)

**作為** 前端使用者
**我希望** Sidebar 導航包含 Sessions 管理入口
**以便** 我能方便地進入 Session 管理頁面

**技術規格**:
- 修改 `frontend/src/App.tsx`
  - 新增路由 `/sessions` → `SessionsPage`
  - 新增路由 `/sessions/:id` → `SessionDetailPage`
  - Lazy import 新增頁面組件
- 修改 `frontend/src/components/layout/Sidebar.tsx`
  - 在「AI 助手」下方新增「Sessions 管理」導航項目
  - 圖標：Clock 或 History icon
  - 路由指向 `/sessions`

## 檔案變更清單

### 新增檔案
| 檔案路徑 | 用途 |
|----------|------|
| `frontend/src/api/endpoints/orchestrator.ts` | Orchestrator Chat API client |
| `frontend/src/api/endpoints/sessions.ts` | Session CRUD + Recovery API client |
| `frontend/src/hooks/useOrchestratorChat.ts` | Orchestrator chat hook（SSE 串流） |
| `frontend/src/hooks/useSessions.ts` | Session 管理 React Query hooks |
| `frontend/src/pages/sessions/SessionsPage.tsx` | Session 列表頁面 |
| `frontend/src/pages/sessions/SessionDetailPage.tsx` | Session 詳情頁面 |
| `frontend/src/components/unified-chat/IntentStatusChip.tsx` | 內聯意圖/風險/模式提示組件 |

### 修改檔案
| 檔案路徑 | 修改內容 |
|----------|---------|
| `frontend/src/components/unified-chat/ChatHistoryPanel.tsx` | 新增可恢復 Sessions 區塊 + Resume 按鈕 |
| `frontend/src/App.tsx` | 新增 /sessions 路由 |
| `frontend/src/components/layout/Sidebar.tsx` | 新增 Sessions 管理導航項目 |

## 驗收標準

- [ ] useOrchestratorChat hook 能連接 `/orchestrator/chat` 並收發訊息
- [ ] SSE 串流回應正常運作（打字效果）
- [ ] Session 列表頁面能顯示所有 Sessions 並支援狀態篩選
- [ ] Session 詳情頁面能顯示完整訊息歷史
- [ ] ChatHistoryPanel 顯示可恢復 Sessions 區塊
- [ ] Resume 按鈕能成功恢復中斷的 Session
- [ ] IntentStatusChip 正確顯示意圖、風險等級、執行模式
- [ ] Sidebar 包含 Sessions 管理導航入口
- [ ] 所有新增組件使用 TypeScript + Shadcn UI
- [ ] 所有新增程式碼通過 ESLint 檢查
- [ ] npm run build 無錯誤

## 相關連結

- [Phase 40 計劃](./README.md)
- [Sprint 139 Plan](./sprint-139-plan.md)
- [E2E Workflow 基準](../../user-expected-workflow.md)

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 12
