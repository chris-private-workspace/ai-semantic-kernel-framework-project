# Sprint 142: Inline 組件嵌入 + 工具調用顯示

## Sprint 目標

1. TaskProgressCard 嵌入 Chat — 當 Agent dispatch 任務時顯示即時進度
2. ToolCallTracker 嵌入 Chat — 顯示工具調用過程
3. OrchestrationPanel 精簡 — 與 inline 組件互補不重複
4. 高風險操作 HITL 審批流程在 Chat 中可視化

## Sprint 週期

| 項目 | 值 |
|------|-----|
| **Phase** | Phase 41 — Chat Pipeline Integration |
| **Sprint** | 142 |
| **Story Points** | 10 點 |
| **狀態** | 📋 計劃中 |

## User Stories

### S142-1: TaskProgressCard 嵌入 Chat (3 SP)

**作為** 前端使用者
**我希望** 當 AI 分發任務時，Chat 中直接顯示任務進度卡片
**以便** 我不需要離開 Chat 就能追蹤任務執行狀況

**技術規格**:

**改動 1: `components/unified-chat/MessageList.tsx`**
- 新增 `taskProgress` timeline item type
- 當 assistant message 的 `orchestrationMetadata.taskId` 存在時，在 message 下方渲染 TaskProgressCard
- TaskProgressCard 內部使用 `useTask(taskId)` 自動 refetch（running 狀態每 3 秒）
- 支援同時顯示多個 TaskProgressCard（Swarm 場景）

**改動 2: `pages/UnifiedChat.tsx`**
- 從 PipelineResponse 提取 `task_id`
- 將 task_id 附加到 assistant message 的 metadata
- 維護 `activeTasks` state 追蹤所有活躍任務

**改動 3: TaskProgressCard 樣式適配**
- 確保卡片在 MessageList 內的寬度和間距合適
- 點擊 task ID 跳轉到 `/tasks/{id}` 詳情頁

### S142-2: ToolCallTracker 嵌入 Chat (3 SP)

**作為** 前端使用者
**我希望** 看到 AI 調用工具的過程（工具名稱、狀態、耗時）
**以便** 我能理解 AI 正在做什麼操作

**技術規格**:

**改動 1: 新增 `hooks/useToolCallEvents.ts`**
- 從 PipelineResponse.metadata 或 SSE 事件提取工具調用資訊
- 管理 `toolCalls: TrackedToolCall[]` state
- TrackedToolCall: `{ id, toolName, status, args, result, startTime, endTime }`

**改動 2: `components/unified-chat/MessageList.tsx`**
- 新增 `toolCalls` timeline item type
- 在 assistant message 前渲染工具調用列表（如果有）
- 使用現有 ToolCallTracker 組件（已在 unified-chat/ 中）

**改動 3: `components/unified-chat/ToolCallTracker.tsx` 適配**
- 確認接受 `toolCalls` prop 格式與 pipeline 輸出相容
- 新增 inline 模式（compact layout for chat timeline）
- 顯示：工具名稱、狀態圖標（pending/running/completed/failed）、耗時

### S142-3: HITL 審批在 Chat 中顯示 (2 SP)

**作為** 前端使用者
**我希望** 高風險操作需要審批時，Chat 中直接顯示審批卡片
**以便** 我能在 Chat 中批准或拒絕操作，不需要跳轉到審批中心

**技術規格**:
- 現有 `InlineApproval.tsx` 和 `ApprovalDialog.tsx` 已存在
- 改動 `handleSend` 流程：
  - 當 PipelineResponse 指示 `requires_approval=true` 時
  - 在 Chat 中渲染 InlineApproval 卡片
  - 用戶批准後繼續執行管線
- 連接 `GET /orchestration/approvals` 查詢審批狀態
- 連接 `POST /orchestration/approvals/{id}/decision` 提交決定

### S142-4: OrchestrationPanel 精簡 (2 SP)

**作為** 前端使用者
**我希望** 右側面板與 inline 組件不重複顯示
**以便** 介面不會有資訊冗餘

**技術規格**:
- OrchestrationPanel 預設收起（collapsed）
- 新增「顯示詳細」按鈕展開面板
- 面板專注於：Agent 工具清單、Pipeline 狀態、Debug 資訊
- 移除面板中已由 inline 組件顯示的資訊（routing decision, risk assessment）
- 保留 Swarm 視覺化面板（Agent 卡片 + 進度）

## 驗收標準

- [ ] 當 Agent dispatch 任務時，Chat 中顯示 TaskProgressCard
- [ ] TaskProgressCard 即時更新進度（running 狀態每 3 秒）
- [ ] 點擊 task ID 能跳轉到 TaskDetailPage
- [ ] 工具調用過程以 ToolCallTracker 在 Chat 中顯示
- [ ] 高風險操作在 Chat 中顯示審批卡片
- [ ] 用戶可在 Chat 中直接批准/拒絕
- [ ] OrchestrationPanel 預設收起，可手動展開
- [ ] 多個 inline 組件同時顯示時 timeline 排列正確
- [ ] TypeScript 零錯誤、npm run build 通過

## 相關連結

- [Phase 41 計劃](./README.md)
- [Sprint 141 Plan](./sprint-141-plan.md)
- [Sprint 143 Plan](./sprint-143-plan.md)

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 10
