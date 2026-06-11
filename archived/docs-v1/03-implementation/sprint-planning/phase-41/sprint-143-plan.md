# Sprint 143: Memory 整合 + Session Resume UI + 完善

## Sprint 目標

1. MemoryHint 嵌入 Chat — 在輸入框上方顯示相關記憶提示
2. Session Resume 在 Chat 中完整運作 — 恢復對話含 pipeline 狀態
3. 跨 Session 記憶展示 — 新對話自動顯示歷史記憶
4. 整體 QA 和收尾 — 確保 10 步流程全部可視化

## Sprint 週期

| 項目 | 值 |
|------|-----|
| **Phase** | Phase 41 — Chat Pipeline Integration |
| **Sprint** | 143 |
| **Story Points** | 8 點 |
| **狀態** | 📋 計劃中 |

## User Stories

### S143-1: MemoryHint 嵌入 Chat (2 SP)

**作為** 前端使用者
**我希望** Chat 輸入框上方顯示與當前對話相關的歷史記憶
**以便** 我知道 AI 記住了之前的互動

**技術規格**:

**改動 1: `pages/UnifiedChat.tsx`**
- 在 ChatInput 上方渲染 MemoryHint 組件
- 新增 `relatedMemories` state
- 當收到 PipelineResponse 時，檢查是否有 memory context
- 從 `/memory/search` 或 PipelineResponse.metadata.memories 取得記憶
- 用戶可關閉 MemoryHint（dismiss）

**改動 2: 新對話時自動搜索記憶**
- 用戶發送第一條訊息後
- 背景呼叫 `POST /memory/search` 搜索相關記憶
- 如果找到 ≥1 條記憶，顯示 MemoryHint
- 記憶內容以摘要形式顯示（前 100 字）

### S143-2: Session Resume 在 Chat 中完整運作 (3 SP)

**作為** 前端使用者
**我希望** 恢復中斷的 Session 後能看到之前的完整對話和 pipeline 狀態
**以便** 我能無縫繼續之前的工作

**技術規格**:

**改動 1: ChatHistoryPanel 的 Resume 流程**
- 點擊 Resume 按鈕 → POST `/sessions/{id}/resume`
- 成功後：
  1. 載入 Session 的對話歷史（GET `/sessions/{id}/messages`）
  2. 將歷史訊息渲染到 MessageList
  3. 如果有活躍任務（response.active_tasks），顯示 TaskProgressCard
  4. 更新 `orchestratorSessionId` 到恢復的 session

**改動 2: 對話歷史還原**
- 每條歷史訊息保留 orchestrationMetadata
- Resume 後的歷史訊息也顯示 IntentStatusChip
- 保持歷史訊息和新訊息的視覺一致性

**改動 3: 後台任務狀態同步**
- Resume 後檢查 active_tasks 清單
- 對每個活躍 task_id 顯示 TaskProgressCard
- 已完成的任務顯示完成狀態

### S143-3: 跨 Session 記憶場景 (1 SP)

**作為** 前端使用者
**我希望** 開始新對話時 AI 能自動引用之前 Session 的相關記憶
**以便** 體現 Step 10（記憶+知識）的端到端效果

**技術規格**:
- 用戶發送訊息後，Orchestrator 的 ContextHandler 已自動注入記憶（後端已實作）
- 前端展示：如果 PipelineResponse 含 memory_context，在 MemoryHint 中顯示
- 實現文檔中的 Scenario F 場景：
  ```
  Session 1: 用戶問 Pipeline 問題 → 記憶寫入
  Session 2: 用戶提到 "上次的問題" → Agent 引用記憶回答
  → MemoryHint 顯示：「找到 1 條相關記憶：CI/CD Pipeline timeout...」
  ```

### S143-4: 整體 QA + 10 步驗證 (2 SP)

**作為** 開發者
**我希望** 完整驗證 10 步流程在 Chat UI 中全部可視化
**以便** 確保 Phase 41 達到目標

**技術規格**:
- Playwright 自動化測試 10 步流程
- 測試 Scenario A-F（user-expected-workflow.md 定義的 6 個場景）
- 修復發現的 UI bug
- 確保以下每步在 Chat 中有可視化對應：
  1. ✅ 登入 → Chat 頁面
  2. ✅ Session 管理 → ChatHistoryPanel
  3. ✅ 意圖+風險 → IntentStatusChip
  4. ✅ Agent 決策 → IntentStatusChip executionMode
  5. ✅ 任務分發 → TaskProgressCard
  6. ✅ 工具調用 → ToolCallTracker
  7. ✅ SSE 串流 → 打字效果
  8. ✅ 結果回應 → MessageList
  9. ✅ Session Resume → ChatHistoryPanel + 歷史還原
  10. ✅ 記憶+知識 → MemoryHint

## 驗收標準

- [ ] Chat 輸入框上方顯示 MemoryHint（當有相關記憶時）
- [ ] MemoryHint 可展開查看記憶摘要、可關閉
- [ ] Session Resume 後能看到完整對話歷史
- [ ] Resume 後活躍任務的 TaskProgressCard 正確顯示
- [ ] 新對話自動搜索並顯示相關歷史記憶
- [ ] Scenario F（跨 Session 記憶）可在 UI 中演示
- [ ] Playwright 10 步流程測試全部通過
- [ ] 6 個 Scenario（A-F）全部在 Chat 中可演示
- [ ] TypeScript 零錯誤、npm run build 通過

## 相關連結

- [Phase 41 計劃](./README.md)
- [Sprint 141 Plan](./sprint-141-plan.md)
- [Sprint 142 Plan](./sprint-142-plan.md)
- [E2E Workflow Baseline](../../user-expected-workflow.md)

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 8
