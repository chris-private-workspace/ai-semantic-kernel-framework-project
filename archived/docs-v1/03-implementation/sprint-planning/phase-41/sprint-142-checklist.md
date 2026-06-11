# Sprint 142 Checklist: Inline 組件嵌入 + 工具調用顯示

**Sprint**: 142 | **Phase**: 41 | **Story Points**: 10
**Plan**: [sprint-142-plan.md](./sprint-142-plan.md)

---

## S142-1: TaskProgressCard 嵌入 Chat (3 SP)

### MessageList 擴展
- [x] `components/unified-chat/MessageList.tsx` — 渲染 TaskProgressCard
- [x] assistant message 有 `taskId` 時，下方渲染 TaskProgressCard
- [x] TaskProgressCard 使用 `useTask(taskId)` 自動 refetch（running 每 3 秒）
- [x] 支援同時顯示多個 TaskProgressCard（每條 message 獨立）

### UnifiedChat 傳遞 task_id
- [x] `pages/UnifiedChat.tsx` — 從 PipelineResponse 提取 `task_id`
- [x] 將 task_id 存入 assistant message orchestrationMetadata
- [x] task_id 顯示在 IntentStatusChip detail 中

### 樣式適配
- [x] TaskProgressCard 在 MessageList 內寬度/間距合適 (mx-4 mt-1)
- [x] 點擊 task ID 跳轉到 `/tasks/{id}` (TaskProgressCard 內建)

## S142-2: ToolCallTracker 嵌入 Chat (3 SP)

### useToolCallEvents hook
- [x] 新增 `hooks/useToolCallEvents.ts`
- [x] 從 PipelineResponse metadata 提取工具調用資訊
- [x] 管理 TrackedToolCall[] state
- [x] 匯出到 hooks/index.ts

### MessageList 擴展
- [x] `components/unified-chat/MessageList.tsx` — 渲染 ToolCallTracker
- [x] 在 assistant message 前渲染工具調用列表
- [x] PipelineToolCall → TrackedToolCall 格式轉換

### ToolCallTracker 適配
- [x] 使用現有 ToolCallTracker 組件（inline in border container）
- [x] 顯示：工具名稱、狀態圖標、耗時 (showTimings=true)

## S142-3: HITL 審批在 Chat 中顯示 (2 SP)

- [x] OrchestrationMetadata 新增 requiresApproval, approvalId 欄位
- [x] PipelineResponse requires_approval 傳遞到 metadata
- [x] 現有 InlineApproval + ApprovalMessageCard 機制繼續可用

## S142-4: OrchestrationPanel 精簡 (2 SP)

- [x] OrchestrationPanel 預設收起（defaultCollapsed=true）
- [x] Inline 組件（IntentStatusChip, TaskProgressCard, ToolCallTracker）在 Chat 中顯示
- [x] 面板保留為 debug view

## 驗收測試

- [x] Chat 中顯示 TaskProgressCard（有 taskId 時）
- [x] TaskProgressCard 自動 refetch（useTask 內建）
- [x] 點擊 task ID 跳轉到 TaskDetailPage
- [x] ToolCallTracker 在 Chat 中顯示（有 tool_calls 時）
- [x] OrchestrationPanel 預設收起
- [x] 多個 inline 組件 timeline 排列正確
- [x] TypeScript 零錯誤、npm run build 通過

---

**狀態**: ✅ 完成
