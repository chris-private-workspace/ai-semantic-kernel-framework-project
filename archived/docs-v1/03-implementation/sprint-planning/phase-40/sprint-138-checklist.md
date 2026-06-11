# Sprint 138 Checklist: Orchestrator Chat 增強 + Session 管理

## Sprint 目標

| 項目 | 值 |
|------|-----|
| **總點數** | 12 點 |
| **狀態** | ✅ 已完成 |

---

## 開發任務

### S138-1: useOrchestratorChat hook + API endpoints (3 SP)
- [x] 新增 `frontend/src/api/endpoints/orchestrator.ts`
- [x] 實作 `sendOrchestratorMessage(sessionId, message)` — POST /orchestrator/chat
- [x] 實作 `getOrchestratorStatus()` — GET /orchestrator/health
- [x] 實作 SSE 串流支援 — 連接 /orchestrator/chat/stream
- [x] 新增 `frontend/src/hooks/useOrchestratorChat.ts`
- [x] 實作 `useOrchestratorChat(sessionId)` hook
- [x] 管理 messages / loading / error state
- [x] 實作 SSE 串流回應（透過 EventSource）
- [x] 實作自動重連機制（斷線後 3 秒重連）
- [x] 回傳 `{ messages, sendMessage, isLoading, error, isConnected }`
- [x] 修改 UnifiedChat 相關組件連接 useOrchestratorChat hook
- [x] 保留現有 UI 結構，僅替換資料來源

### S138-2: Session 管理頁面 (3 SP)
- [x] 新增 `frontend/src/api/endpoints/sessions.ts`
- [x] 實作 `getSessions(filters)` — GET /sessions（支援 status 篩選）
- [x] 實作 `getSession(id)` — GET /sessions/{id}
- [x] 實作 `getSessionMessages(id)` — GET /sessions/{id}/messages
- [x] 實作 `getRecoverableSessions()` — GET /sessions/recoverable
- [x] 實作 `resumeSession(id)` — POST /sessions/{id}/resume
- [x] 實作 `deleteSession(id)` — DELETE /sessions/{id}
- [x] 新增 `frontend/src/hooks/useSessions.ts`
- [x] 實作 `useSessions(filters)` — 列表查詢 hook（React Query）
- [x] 實作 `useSession(id)` — 單一 Session 查詢 hook
- [x] 實作 `useSessionMessages(id)` — 訊息歷史查詢 hook
- [x] 實作 `useResumeSession()` — Resume mutation hook
- [x] 新增 `frontend/src/pages/sessions/SessionsPage.tsx`
- [x] 實作狀態篩選器（active / completed / interrupted / recoverable）
- [x] 實作表格顯示：Session ID、建立時間、最後更新、狀態、訊息數量
- [x] 實作操作按鈕：查看詳情、Resume、刪除
- [x] 使用 Shadcn UI Table + Badge + Select 組件
- [x] 新增 `frontend/src/pages/sessions/SessionDetailPage.tsx`
- [x] 實作 Session metadata 顯示（ID、建立時間、狀態、Agent 資訊）
- [x] 實作訊息歷史時間軸（含角色標記：user / assistant / system）
- [x] 實作返回列表按鈕

### S138-3: ChatHistoryPanel 改造 (3 SP)
- [x] 修改 `frontend/src/components/unified-chat/ChatHistoryPanel.tsx`
- [x] 在現有 thread 列表上方新增「可恢復 Sessions」區塊
- [x] 呼叫 `GET /sessions/recoverable` 取得可恢復 Session 列表
- [x] 每個可恢復 Session 顯示：最後訊息摘要、中斷時間、狀態 Badge
- [x] 實作 Resume 按鈕 → 呼叫 `POST /sessions/{id}/resume`
- [x] Resume 成功後自動切換到該 Session 的對話
- [x] 保留現有 localStorage thread 邏輯（漸進式遷移）
- [x] 可恢復區塊可摺疊/展開（預設展開）
- [x] 使用 Shadcn UI Collapsible + Button + Badge 組件

### S138-4: IntentStatusChip 內聯組件 (2 SP)
- [x] 新增 `frontend/src/components/unified-chat/IntentStatusChip.tsx`
- [x] 實作 Props interface: `{ intent, riskLevel, executionMode }`
- [x] 實作內聯顯示格式：「意圖：{intent} | 風險：{riskLevel} | 模式：{executionMode}」
- [x] 實作風險等級色彩：LOW=綠色、MEDIUM=黃色、HIGH=橙色、CRITICAL=紅色
- [x] 實作可展開詳細資訊（點擊展開顯示完整意圖分析）
- [x] 使用 Shadcn UI Badge + Tooltip + Collapsible 組件
- [x] 實作響應式設計：小螢幕只顯示圖標，hover 顯示完整資訊

### S138-5: Sidebar + App.tsx 路由更新 (1 SP)
- [x] 修改 `frontend/src/App.tsx` — 新增路由 `/sessions` → SessionsPage
- [x] 修改 `frontend/src/App.tsx` — 新增路由 `/sessions/:id` → SessionDetailPage
- [x] Lazy import 新增頁面組件
- [x] 修改 `frontend/src/components/layout/Sidebar.tsx` — 新增「Sessions 管理」導航項目
- [x] 設定導航圖標（Clock 或 History icon）
- [x] 路由指向 `/sessions`

## 驗證標準

- [x] useOrchestratorChat hook 能連接 `/orchestrator/chat` 並收發訊息
- [x] SSE 串流回應正常運作（打字效果）
- [x] Session 列表頁面能顯示所有 Sessions 並支援狀態篩選
- [x] Session 詳情頁面能顯示完整訊息歷史
- [x] ChatHistoryPanel 顯示可恢復 Sessions 區塊
- [x] Resume 按鈕能成功恢復中斷的 Session
- [x] IntentStatusChip 正確顯示意圖、風險等級、執行模式
- [x] Sidebar 包含 Sessions 管理導航入口
- [x] 所有新增組件使用 TypeScript + Shadcn UI
- [x] 所有新增程式碼通過 ESLint 檢查
- [x] npm run build 無錯誤

## 相關連結

- [Phase 40 計劃](./README.md)
- [Sprint 138 Plan](./sprint-138-plan.md)
- [Sprint 139 Plan](./sprint-139-plan.md)

---

**Sprint 狀態**: ✅ 已完成
**Story Points**: 12
