# Sprint 141: Chat → Orchestrator Pipeline 接通

## Sprint 目標

1. UnifiedChat 消除雙路徑，統一走 `/orchestrator/chat`
2. PipelineResponse 數據驅動 Chat 顯示（意圖、風險、模式、session_id）
3. IntentStatusChip 嵌入 Chat 訊息流（用戶訊息下方）
4. LLM 回應以打字效果串流顯示
5. 組件匯出完善

## Sprint 週期

| 項目 | 值 |
|------|-----|
| **Phase** | Phase 41 — Chat Pipeline Integration |
| **Sprint** | 141 |
| **Story Points** | 10 點 |
| **狀態** | 📋 計劃中 |

## User Stories

### S141-1: UnifiedChat 統一走 Orchestrator Pipeline (4 SP)

**作為** 前端使用者
**我希望** Chat 發送訊息後經過完整的 Orchestrator 管線處理
**以便** 我的請求能被正確分類、風險評估、並由 Agent 決策最佳處理方式

**技術規格**:

**改動 1: `pages/UnifiedChat.tsx` — 消除雙路徑**
- 修改 `handleSend()` 函數（現有 line 633-677）
- 移除 orchestration ON/OFF 分支邏輯
- 統一流程：
  1. 添加用戶訊息到 chat
  2. POST `/orchestrator/chat` （PipelineRequest 格式：`{content, source: 'user', session_id}`）
  3. 解析 PipelineResponse → 提取 intent_category, risk_level, routing_layer, framework_used, session_id, task_id
  4. 將 orchestration metadata 附加到 assistant message
  5. 添加 assistant 回應到 chat
- 保留 `isOrchestrationEnabled` flag 作為 fallback（漸進式遷移）
- 新增 `orchestratorSessionId` state 追蹤當前 pipeline session

**改動 2: `hooks/useOrchestratorChat.ts` — 增強為主要 Chat hook**
- 修改 `sendMessage()` 內部邏輯：
  - 非 SSE 模式（預設）：POST `/orchestrator/chat` → PipelineResponse
  - 從 PipelineResponse 提取 metadata 並存入 `latestMetadata` state
  - 如果 response 含 `task_id`，存入新的 `activeTasks` state
- 新增 `activeTasks: string[]` state — 追蹤活躍任務 ID
- 新增 `orchestrationEvents: OrchestrationEvent[]` state — 記錄管線事件

**改動 3: `api/endpoints/orchestrator.ts` — Response 類型對齊**
- 更新 `SendOrchestratorMessageResponse` 匹配 PipelineResponse 欄位：
  - content, intent_category, confidence, risk_level, routing_layer
  - framework_used, session_id, task_id, processing_time_ms, is_complete

### S141-2: IntentStatusChip 嵌入 Chat 訊息流 (3 SP)

**作為** 前端使用者
**我希望** 在 Chat 中看到每條訊息的意圖分類和風險評估結果
**以便** 我能了解系統如何理解我的請求

**技術規格**:

**改動 1: `components/unified-chat/MessageList.tsx` — 擴展 timeline**
- 現有 timeline 支援 `message` + `approval` 兩種 item type
- 新增 `intentStatus` item type
- 每條 assistant message 如果有 orchestration metadata，在其上方渲染 IntentStatusChip
- IntentStatusChip 數據從 message.metadata 讀取（intent, riskLevel, executionMode）

**改動 2: 擴展 Message 類型**
- 在現有 message type 中新增 optional `orchestrationMetadata` 欄位：
  ```typescript
  interface ChatMessage {
    // ...existing fields
    orchestrationMetadata?: {
      intent?: string;
      riskLevel?: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
      executionMode?: string;
      routingLayer?: string;
      confidence?: number;
      processingTimeMs?: number;
    };
  }
  ```

**改動 3: IntentStatusChip 樣式微調**
- 確保在 MessageList timeline 中的顯示效果（間距、寬度）
- 展開時顯示 routing_layer + confidence + processing_time

### S141-3: LLM 回應串流顯示 (2 SP)

**作為** 前端使用者
**我希望** AI 回應以打字效果逐字出現
**以便** 我能即時看到 AI 正在思考和回應，而非等待數十秒後一次性出現

**技術規格**:
- 現有 `useUnifiedChat.ts` 的 SSE 路徑已有打字效果（ReadableStream 解析）
- 新增 **模擬打字效果** 到 orchestrator 同步路徑：
  - 收到 PipelineResponse.content 後
  - 以 20ms/字元 的速度逐字渲染到 MessageList
  - 使用 `requestAnimationFrame` 避免 UI 卡頓
- 新增 `useTypewriterEffect(content, speed)` hook

### S141-4: 組件匯出 + 清理 (1 SP)

**作為** 開發者
**我希望** Phase 40 建立的組件正確匯出並可被引用
**以便** Sprint 142 能直接使用這些組件

**技術規格**:
- 修改 `components/unified-chat/index.ts`：
  - 匯出 IntentStatusChip
  - 匯出 TaskProgressCard
  - 匯出 MemoryHint
- 確保所有 import paths 正確
- TypeScript 編譯零錯誤

## 驗收標準

- [ ] 用戶發送訊息 → 經 `/orchestrator/chat` 處理 → 收到回應
- [ ] 每條 assistant 回應上方顯示 IntentStatusChip（意圖 + 風險 + 模式）
- [ ] IntentStatusChip 可展開顯示詳細資訊（routing layer, confidence, processing time）
- [ ] AI 回應以打字效果出現（非一次性）
- [ ] Session ID 在多輪對話中保持一致
- [ ] 舊的 orchestration flow 仍可作為 fallback 使用
- [ ] IntentStatusChip, TaskProgressCard, MemoryHint 正確匯出
- [ ] TypeScript 零錯誤、npm run build 通過

## 相關連結

- [Phase 41 計劃](./README.md)
- [Sprint 142 Plan](./sprint-142-plan.md)

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 10
