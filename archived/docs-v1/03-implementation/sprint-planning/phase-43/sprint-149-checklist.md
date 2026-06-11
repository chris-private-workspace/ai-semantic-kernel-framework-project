# Sprint 149 Checklist: Worker Detail Visualization — 即時細節展示

**Sprint**: 149 | **Phase**: 43 | **Story Points**: 12
**Plan**: [sprint-149-plan.md](./sprint-149-plan.md)

---

## S149-1: SSE Worker 事件消費 + swarmStore 統一 (4 SP)

### useSSEChat 擴充
- [ ] 新增 SWARM_STARTED handler
- [ ] 新增 SWARM_WORKER_THINKING handler
- [ ] 新增 SWARM_WORKER_TOOL_CALL handler
- [ ] 新增 SWARM_WORKER_MESSAGE handler
- [ ] 新增 SWARM_WORKER_COMPLETED handler
- [ ] 新增 SWARM_WORKER_FAILED handler
- [ ] 新增 SWARM_AGGREGATING handler
- [ ] 新增 SWARM_COMPLETED handler

### UnifiedChat SSE → swarmStore
- [ ] SWARM_STARTED → swarmStore.setSwarmStatus()
- [ ] SWARM_WORKER_START → swarmStore.addWorker()
- [ ] SWARM_WORKER_THINKING → swarmStore.updateWorkerThinking()
- [ ] SWARM_WORKER_TOOL_CALL → swarmStore.updateWorkerToolCall()
- [ ] SWARM_WORKER_PROGRESS → swarmStore.updateWorkerProgress()
- [ ] SWARM_WORKER_COMPLETED → swarmStore.completeWorker()
- [ ] SWARM_COMPLETED → swarmStore.completeSwarm()

### swarmStore 擴充
- [ ] 為每個 Worker 維護 WorkerDetail（thinking_steps, tool_calls, messages）
- [ ] setWorkerDetail() action 自動從事件累積
- [ ] 從事件數據自動建構 WorkerDetail

## S149-2: WorkerDetailDrawer 嵌入 Chat (4 SP)

### UnifiedChat 嵌入
- [ ] 在 AgentSwarmPanel 旁渲染 WorkerDetailDrawer
- [ ] 點擊 WorkerCard → swarmStore.selectWorker() → openDrawer()
- [ ] Drawer 讀取 swarmStore.selectedWorkerDetail

### Drawer 內容面板
- [ ] Tab 1: Overview — 任務描述、狀態、進度、持續時間
- [ ] Tab 2: Extended Thinking — 逐步 LLM 推理過程
- [ ] Tab 3: Tool Calls — 工具名、參數、結果、耗時
- [ ] Tab 4: Messages — Worker 完整 message 歷史

### 即時更新
- [ ] 新事件自動更新 Drawer 內容
- [ ] Thinking 面板自動滾動到最新

## S149-3: Extended Thinking + Tool Calls 真實數據 (4 SP)

### ExtendedThinkingPanel
- [ ] 接收真實 thinking_steps（從 swarmStore WorkerDetail）
- [ ] 每步：時間戳 + 內容 + 耗時
- [ ] Markdown 渲染支援
- [ ] 執行中 typing indicator

### ToolCallsPanel
- [ ] 接收真實 tool_calls 數據
- [ ] 每調用：工具名 + 參數 JSON + 結果 + 耗時 + 狀態
- [ ] 執行中 spinner
- [ ] 失敗顯示錯誤

### Worker Progress Timeline
- [ ] 執行時間線：START → THINKING → TOOL_CALL → COMPLETED
- [ ] 每個節點可點擊
- [ ] 時間線即時更新

## 驗收測試

- [ ] SSE Worker 事件正確填充 swarmStore
- [ ] swarmStore 統一管理 Swarm 狀態
- [ ] WorkerDetailDrawer 可在 Chat 中打開
- [ ] Extended Thinking 顯示真實 LLM 推理
- [ ] Tool Calls 顯示真實工具調用
- [ ] Message History 顯示完整對話
- [ ] 即時更新（新事件自動刷新）
- [ ] Markdown 渲染正常
- [ ] TypeScript 零錯誤

---

**狀態**: 📋 計劃中
