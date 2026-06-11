# Sprint 143 Checklist: Memory 整合 + Session Resume UI + 完善

**Sprint**: 143 | **Phase**: 41 | **Story Points**: 8
**Plan**: [sprint-143-plan.md](./sprint-143-plan.md)

---

## S143-1: MemoryHint 嵌入 Chat (2 SP)

### 記憶顯示
- [x] `pages/UnifiedChat.tsx` — ChatInput 上方渲染 MemoryHint
- [x] 新增 `relatedMemories` state + `showMemoryHint` state
- [x] 從 PipelineResponse metadata.memory_context 或 `/memory/search` 取得記憶
- [x] 用戶可關閉 MemoryHint（dismiss）

### 新對話自動搜索記憶
- [x] 用戶發送第一條訊息後背景呼叫 `memoryApi.searchMemories()`
- [x] 找到 ≥1 條記憶時顯示 MemoryHint
- [x] 記憶以摘要形式顯示（前 100 字，MemoryHint 內建）

## S143-2: Session Resume 在 Chat 中完整運作 (3 SP)

### Resume 流程
- [x] `handleResumeSession` callback 傳遞到 ChatHistoryPanel
- [x] Resume 後呼叫 `sessionsApi.getSessionMessages()` 載入歷史
- [x] 歷史訊息渲染到 MessageList
- [x] 更新 `orchestratorSessionId` 到恢復的 session

### 對話歷史還原
- [x] 歷史訊息保留 orchestrationMetadata（從 msg.metadata.orchestration）
- [x] Resume 後的歷史訊息也顯示 IntentStatusChip
- [x] 歷史/新訊息視覺一致性

## S143-3: 跨 Session 記憶場景 (1 SP)

- [x] PipelineResponse 含 memory_context 時在 MemoryHint 中顯示
- [x] Scenario F 邏輯實現：Session 1 記憶寫入 → Session 2 引用
- [x] MemoryHint 顯示「找到 N 條相關記憶」

## S143-4: 整體 QA + 10 步驗證 (2 SP)

### 10 步流程驗證
- [x] Step 1: 登入 → Chat 頁面
- [x] Step 2: Session 管理 → ChatHistoryPanel + Resume
- [x] Step 3: 意圖+風險 → IntentStatusChip
- [x] Step 4: Agent 決策 → IntentStatusChip executionMode
- [x] Step 5: 任務分發 → TaskProgressCard
- [x] Step 6: 工具調用 → ToolCallTracker
- [x] Step 7: SSE 串流 → 打字效果 (typewriter)
- [x] Step 8: 結果回應 → MessageList
- [x] Step 9: Session Resume → 歷史還原
- [x] Step 10: 記憶+知識 → MemoryHint

## 驗收測試

- [x] MemoryHint 在 ChatInput 上方顯示
- [x] MemoryHint 可展開/關閉
- [x] Session Resume 後載入對話歷史
- [x] 新對話自動搜索歷史記憶
- [x] 跨 Session 記憶可顯示
- [x] TypeScript 零錯誤、npm run build 通過

---

**狀態**: ✅ 完成
