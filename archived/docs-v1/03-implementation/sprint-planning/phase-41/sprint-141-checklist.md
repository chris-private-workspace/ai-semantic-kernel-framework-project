# Sprint 141 Checklist: Chat → Orchestrator Pipeline 接通

**Sprint**: 141 | **Phase**: 41 | **Story Points**: 10
**Plan**: [sprint-141-plan.md](./sprint-141-plan.md)

---

## S141-1: UnifiedChat 統一走 Orchestrator Pipeline (4 SP)

### 消除雙路徑
- [x] `pages/UnifiedChat.tsx` — `handleSend()` 統一走 `/orchestrator/chat`
- [x] 移除 orchestration ON/OFF 分支邏輯（保留 fallback）
- [x] POST `/orchestrator/chat` 使用 PipelineRequest 格式 (`{content, source, session_id}`)
- [x] 解析 PipelineResponse → 提取 intent_category, risk_level, routing_layer, session_id, task_id
- [x] 新增 `orchestratorSessionId` state 追蹤 pipeline session
- [x] 保留 `isOrchestrationEnabled` flag 作為 fallback

### useOrchestratorChat 增強
- [x] 直接在 UnifiedChat 中使用 `orchestratorApi.sendMessage()` (更簡潔)
- [x] 從 PipelineResponse 提取 metadata 存入 assistant message
- [x] task_id 從 response 提取並存入 orchestrationMetadata

### API Response 類型對齊
- [x] `api/endpoints/orchestrator.ts` — 更新 Response 類型匹配 PipelineResponse

## S141-2: IntentStatusChip 嵌入 Chat 訊息流 (3 SP)

### MessageList 擴展
- [x] `components/unified-chat/MessageList.tsx` — assistant message 上方渲染 IntentStatusChip
- [x] assistant message 有 orchestration metadata 時，渲染 IntentStatusChip
- [x] IntentStatusChip 數據從 message.orchestrationMetadata 讀取

### Message 類型擴展
- [x] ChatMessage interface 新增 `orchestrationMetadata?` 欄位
- [x] 含 intent, riskLevel, executionMode, routingLayer, confidence, processingTimeMs, detail

### IntentStatusChip 樣式
- [x] 在 MessageList timeline 中間距/寬度適當 (mx-4 mb-1)
- [x] 展開時顯示 routing_layer + confidence + processing_time (detail string)

## S141-3: LLM 回應串流顯示 (2 SP)

- [x] 新增 `useTypewriterEffect(content, speed)` hook
- [x] orchestrator 同步路徑：收到 PipelineResponse.content 後模擬打字效果
- [x] 使用 `requestAnimationFrame` 避免 UI 卡頓
- [x] 15ms/字元速度 (略快於原計劃的 20ms)

## S141-4: 組件匯出 + 清理 (1 SP)

- [x] `components/unified-chat/index.ts` — 匯出 IntentStatusChip
- [x] `components/unified-chat/index.ts` — 匯出 TaskProgressCard
- [x] `components/unified-chat/index.ts` — 匯出 MemoryHint
- [x] `hooks/index.ts` — 匯出 useTypewriterEffect
- [x] 所有 import paths 正確
- [x] TypeScript 編譯零錯誤

## 驗收測試

- [x] 用戶發送訊息 → 經 `/orchestrator/chat` 處理 → 收到回應
- [x] 每條 assistant 回應上方顯示 IntentStatusChip
- [x] IntentStatusChip 可展開顯示詳細資訊
- [x] AI 回應以打字效果出現
- [x] Session ID 多輪對話保持一致 (orchestratorSessionId)
- [x] 舊 orchestration flow 仍可作為 fallback
- [x] 組件正確匯出
- [x] TypeScript 零錯誤、npm run build 通過

---

**狀態**: ✅ 完成
