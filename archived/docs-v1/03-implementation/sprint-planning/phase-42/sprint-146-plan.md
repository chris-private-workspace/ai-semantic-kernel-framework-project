# Sprint 146: Swarm UI 整合 + HITL 審批

## Sprint 目標

1. AgentSwarmPanel 嵌入 UnifiedChat，Swarm 事件透過 SSE 填充 swarmStore
2. HITL 審批流程：高風險操作暫停 Pipeline，SSE 推送 APPROVAL_REQUIRED，用戶在 Chat 中批准/拒絕
3. 修復 DialogHandler（GuidedDialogEngine 缺 router）+ HITLController（缺 storage）初始化問題

## Sprint 週期

| 項目 | 值 |
|------|-----|
| **Phase** | Phase 42 — E2E Pipeline Deep Integration |
| **Sprint** | 146 |
| **Story Points** | 10 點 |
| **狀態** | 📋 計劃中 |

## User Stories

### S146-1: AgentSwarmPanel 嵌入 Chat (4 SP)

**作為** Chat 使用者
**我希望** 當系統啟動 Swarm 多 Agent 協作時，在 Chat 中即時看到各 Worker 的執行狀態
**以便** 了解哪些 Agent 正在處理什麼任務，整體進度如何

**技術規格**:

**改動 1: `frontend/src/pages/UnifiedChat.tsx` — 嵌入 AgentSwarmPanel**
- 當 SSE 接收到 `SWARM_WORKER_START` 事件時，顯示 AgentSwarmPanel
- AgentSwarmPanel 位置：Chat 區域右側或訊息流下方（根據螢幕寬度決定）
- 大螢幕（≥1280px）：右側面板（寬度 360px）
- 小螢幕（<1280px）：訊息流下方折疊面板

**改動 2: `frontend/src/hooks/useSSEChat.ts` — Swarm 事件處理**
- 新增 Swarm 相關事件 handler：
  ```typescript
  SWARM_WORKER_START: (data) => swarmStore.addWorker(data),
  SWARM_PROGRESS: (data) => swarmStore.updateWorkerProgress(data),
  SWARM_WORKER_COMPLETE: (data) => swarmStore.completeWorker(data),
  SWARM_COMPLETE: (data) => swarmStore.completeSwarm(data),
  ```
- Swarm 事件自動填充 `useSwarmStore` Zustand store

**改動 3: `frontend/src/components/unified-chat/agent-swarm/` — WorkerCard 即時更新**
- 確保 WorkerCard 組件從 swarmStore 讀取即時數據
- 進度條依據 SWARM_PROGRESS 事件更新
- Worker 完成時顯示結果摘要
- Swarm 完成後面板顯示總結

### S146-2: HITL 審批流程 (3 SP)

**作為** Chat 使用者
**我希望** 系統在執行高風險操作前暫停並詢問我的批准
**以便** 我能在關鍵操作前審核並決定是否繼續

**技術規格**:

**改動 1: `backend/src/integrations/orchestration/mediator.py` — 暫停機制**
- 在 Pipeline 的風險評估步驟後，檢查 `risk_level`
- 如果 `risk_level >= HIGH`：
  1. 發射 `APPROVAL_REQUIRED` SSE 事件：
     ```json
     {
       "approval_id": "uuid",
       "action": "dispatch_workflow",
       "risk_level": "HIGH",
       "description": "即將執行多步驟工作流程，影響 3 個系統",
       "details": {"systems": ["CRM", "ERP", "Email"], "estimated_time": "5m"}
     }
     ```
  2. 使用 `asyncio.Event` 暫停 Pipeline 等待審批
  3. 等待前端回傳審批結果（approve / reject）
  4. 審批通過 → 繼續執行；拒絕 → 回傳取消訊息

**改動 2: `backend/src/api/v1/orchestration.py` — 審批回傳端點**
- 新增 `POST /orchestrator/approval/{approval_id}` 端點
- 接受 `{"action": "approve" | "reject", "reason": "optional"}`
- 通知對應 Pipeline 的 `asyncio.Event` 繼續或取消

**改動 3: `frontend/src/components/unified-chat/InlineApproval.tsx` — 審批 UI**
- SSE 接收 APPROVAL_REQUIRED 時，在 Chat 訊息流中渲染 InlineApproval 卡片
- 顯示：操作描述、風險等級、影響系統、預估時間
- 兩個按鈕：✅ 批准 / ❌ 拒絕（可附加理由）
- 點擊後 POST `/orchestrator/approval/{approval_id}`
- 審批後卡片變為只讀狀態（顯示結果）

### S146-3: DialogHandler + HITLController 修復 (3 SP)

**作為** Pipeline 的開發維護者
**我希望** GuidedDialogEngine 和 HITLController 能正確初始化
**以便** 對話引導和人機協作流程在 Pipeline 中正常運作

**技術規格**:

**改動 1: `backend/src/integrations/orchestration/handlers/dialog_handler.py` — 修復初始化**
- GuidedDialogEngine 初始化缺少 `router` 參數
- 從 Bootstrap context 取得 IntentRouter instance 傳入
- 確保 DialogHandler 在 Pipeline 中被正確觸發（多輪對話場景）

**改動 2: `backend/src/integrations/orchestration/handlers/hitl_handler.py` — 修復初始化**
- HITLController 初始化缺少 `storage` 參數
- 從 Bootstrap context 取得 approval storage（Redis 或 PostgreSQL）
- HITLController 管理待審批項目的狀態（pending → approved/rejected）

**改動 3: `backend/src/integrations/orchestration/bootstrap.py` — 傳入依賴**
- Bootstrap 建立 IntentRouter instance 並傳入 DialogHandler
- Bootstrap 建立 approval storage 並傳入 HITLController
- 確保所有 Handler 依賴在 Bootstrap 階段完整注入

**改動 4: 對話引導可視化**
- 前端 Chat 中顯示對話引導步驟（DialogHandler 輸出）
- 使用 SSE 事件 `DIALOG_STEP` 推送引導資訊
- 顯示引導進度和下一步提示

## 驗收標準

- [ ] Swarm 執行時 AgentSwarmPanel 在 Chat 中顯示
- [ ] WorkerCard 即時反映各 Worker 狀態（啟動、進度、完成）
- [ ] swarmStore 透過 SSE 事件正確填充
- [ ] 高風險操作觸發 APPROVAL_REQUIRED 事件
- [ ] InlineApproval 卡片在 Chat 中渲染（操作描述 + 批准/拒絕）
- [ ] 用戶批准後 Pipeline 繼續執行
- [ ] 用戶拒絕後 Pipeline 取消並回傳訊息
- [ ] GuidedDialogEngine 正確初始化（含 router 參數）
- [ ] HITLController 正確初始化（含 storage 參數）
- [ ] 對話引導流程在 Chat 中可視化
- [ ] TypeScript 零錯誤、npm run build 通過
- [ ] `black . && isort . && flake8 .` 通過

## 相關連結

- [Phase 42 計劃](./README.md)
- [Sprint 145 Plan](./sprint-145-plan.md)
- [Sprint 147 Plan](./sprint-147-plan.md)

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 10
