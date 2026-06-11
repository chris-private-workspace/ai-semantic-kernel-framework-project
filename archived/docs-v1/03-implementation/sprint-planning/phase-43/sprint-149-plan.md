# Sprint 149: Worker Detail Visualization — 即時細節展示

## Sprint 目標

1. WorkerDetailDrawer 嵌入 Chat（點擊 WorkerCard → 展開詳細面板）
2. Extended Thinking Panel 顯示真實 LLM 推理過程
3. Tool Calls Panel 顯示真實工具調用及結果
4. Message History 顯示 Worker 完整對話記錄
5. swarmStore 統一管理所有 Swarm 狀態（替代各 hook 自管）

## Sprint 週期

| 項目 | 值 |
|------|-----|
| **Phase** | Phase 43 — Agent Swarm 完整實現 |
| **Sprint** | 149 |
| **Story Points** | 12 點 |
| **狀態** | 📋 計劃中 |

## User Stories

### S149-1: SSE Worker 事件消費 + swarmStore 統一 (4 SP)

**作為** Chat 使用者
**我希望** 前端即時接收每個 Worker 的思考、工具調用、進度事件
**以便** 在 AgentSwarmPanel 中看到真實的即時數據

**技術規格**:

**改動 1: `frontend/src/hooks/useSSEChat.ts` — 擴充 Worker 事件 handler**
- 新增 SSE 事件類型：SWARM_STARTED, SWARM_WORKER_THINKING, SWARM_WORKER_TOOL_CALL, SWARM_WORKER_MESSAGE, SWARM_WORKER_COMPLETED, SWARM_WORKER_FAILED, SWARM_PROGRESS, SWARM_AGGREGATING, SWARM_COMPLETED
- 每個事件直接呼叫 swarmStore actions

**改動 2: `frontend/src/pages/UnifiedChat.tsx` — SSE handlers 改用 swarmStore**
- SWARM_STARTED → swarmStore.setSwarmStatus(...)
- SWARM_WORKER_START → swarmStore.addWorker(...)
- SWARM_WORKER_THINKING → swarmStore.updateWorkerThinking(...)
- SWARM_WORKER_TOOL_CALL → swarmStore.updateWorkerToolCall(...)
- SWARM_WORKER_PROGRESS → swarmStore.updateWorkerProgress(...)
- SWARM_WORKER_COMPLETED → swarmStore.completeWorker(...)
- SWARM_COMPLETED → swarmStore.completeSwarm(...)

**改動 3: `frontend/src/stores/swarmStore.ts` — 補充 WorkerDetail 管理**
- 為每個 Worker 維護 WorkerDetail（thinking_steps, tool_calls, messages）
- 新增 action: `setWorkerDetail(workerId, detail)` 自動從事件累積

### S149-2: WorkerDetailDrawer 嵌入 Chat (4 SP)

**作為** Chat 使用者
**我希望** 點擊 WorkerCard 能展開詳細面板，看到該 Worker 的完整執行細節
**以便** 了解每個 Agent 在做什麼、想什麼、用了什麼工具

**技術規格**:

**改動 1: `frontend/src/pages/UnifiedChat.tsx` — 嵌入 WorkerDetailDrawer**
- 在 AgentSwarmPanel 旁渲染 WorkerDetailDrawer
- 點擊 WorkerCard → swarmStore.selectWorker(worker) → openDrawer()
- Drawer 讀取 swarmStore.selectedWorkerDetail

**改動 2: WorkerDetailDrawer 內容面板**
- Tab 1: **Overview** — 任務描述、狀態、進度、持續時間
- Tab 2: **Extended Thinking** — 逐步顯示 LLM 推理過程（從 thinking_steps 讀取）
- Tab 3: **Tool Calls** — 調用列表：工具名、參數、結果、耗時
- Tab 4: **Messages** — Worker 的完整 message 歷史（system + user + assistant + tool）

**改動 3: 即時更新**
- Drawer 打開時，新事件到達自動更新內容（swarmStore subscription）
- Thinking 面板支援自動滾動到最新

### S149-3: Extended Thinking + Tool Calls 真實數據 (4 SP)

**作為** 進階使用者
**我希望** 看到每個 Worker Agent 的完整思考鏈和工具調用歷程
**以便** 理解 Agent 的決策過程、排查問題、評估結果品質

**技術規格**:

**改動 1: `frontend/src/components/unified-chat/agent-swarm/ExtendedThinkingPanel.tsx`**
- 接收真實 thinking_steps 數據（從 swarmStore WorkerDetail）
- 每一步顯示：時間戳、思考內容、耗時
- 支援 Markdown 渲染（LLM 輸出可能含格式）
- 執行中顯示 typing indicator

**改動 2: `frontend/src/components/unified-chat/agent-swarm/ToolCallsPanel.tsx`**
- 接收真實 tool_calls 數據
- 每個調用顯示：工具名、參數（可展開 JSON）、結果（可展開）、耗時、狀態
- 執行中的 tool call 顯示 spinner
- 失敗的 tool call 顯示錯誤信息

**改動 3: Worker Progress Timeline**
- 在 WorkerCard 或 Drawer 中顯示執行時間線
- 時間線節點：START → THINKING → TOOL_CALL → THINKING → COMPLETED
- 每個節點可點擊跳轉到對應的 Thinking/ToolCall 詳情

## 驗收標準

- [ ] SSE Worker 事件正確消費並填充 swarmStore
- [ ] swarmStore 統一管理所有 Swarm 狀態
- [ ] WorkerDetailDrawer 在 Chat 中可通過 WorkerCard 點擊打開
- [ ] Extended Thinking Panel 顯示真實 LLM 推理步驟
- [ ] Tool Calls Panel 顯示真實工具調用及結果
- [ ] Message History 顯示 Worker 完整對話
- [ ] 即時更新：新事件到達自動刷新 Drawer 內容
- [ ] Thinking 面板支援 Markdown 渲染
- [ ] 執行中有 typing indicator / spinner
- [ ] TypeScript 零錯誤、npm run build 通過

## 相關連結

- [Phase 43 計劃](./README.md)
- [Sprint 148 Plan](./sprint-148-plan.md)
- [Sprint 150 Plan](./sprint-150-plan.md)

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 12
