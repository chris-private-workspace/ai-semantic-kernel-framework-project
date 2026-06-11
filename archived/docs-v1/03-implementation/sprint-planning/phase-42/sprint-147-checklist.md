# Sprint 147 Checklist: Session 持久化 + RAG + Checkpoint + QA

**Sprint**: 147 | **Phase**: 42 | **Story Points**: 8
**Plan**: [sprint-147-plan.md](./sprint-147-plan.md)

---

## S147-1: Session 持久化 (3 SP)

### ConversationStateStore 替換
- [x] `mediator.py` — `self._sessions: dict` 搭配 ConversationStateStore
- [x] Redis 作為主要存儲（auto-detect, memory fallback）
- [ ] PostgreSQL 作為持久化備份
- [x] _get_or_create_session() 從 persistent store 恢復
- [x] _update_session_after_execution() 持久化 session 狀態

### Session Recovery API
- [x] Session Recovery API 已存在（Sprint 115, session_routes.py）
- [x] `GET /sessions/recoverable` — 列出可恢復 sessions
- [x] `POST /sessions/{session_id}/resume` — 恢復 session
- [ ] Session Resume 恢復完整 pipeline 狀態（不只對話歷史）

### 路由註冊
- [x] session_routes.py 已註冊
- [ ] 驗證 session_id 所有權

## S147-2: Checkpoint 自動保存 (2 SP)

### Checkpoint 實作
- [x] Mediator wires RedisCheckpointStorage（memory fallback）
- [x] _save_checkpoint() helper 在 routing (step 2) 和 agent (step 5) 後保存
- [ ] 建立 `pipeline_checkpoints` PostgreSQL 資料表（Alembic migration）
- [ ] 新增 index：session_id + created_at

### Mediator Checkpoint 整合
- [x] Handler 迴圈中加入 Checkpoint 保存邏輯
- [x] Pipeline 啟動時檢查是否有 Checkpoint (load_latest)
- [x] 有 Checkpoint → 記錄 resume_step 供後續使用
- [ ] 有 Checkpoint → 跳過已完成步驟（需完整 step skip 邏輯）
- [x] 恢復後發射 CHECKPOINT_RESTORED SSE 事件

## S147-3: RAG Pipeline 連接 (2 SP)

### search_knowledge 工具實作
- [x] `dispatch_handlers.py` — search_knowledge 連接 RAGPipeline（Sprint 118）
- [x] RAGPipeline with Qdrant + hybrid retrieval
- [x] 可透過 AgentHandler function calling 調用
- [x] RAG 搜尋結果注入 LLM prompt（via function calling tool message）

### 前端知識來源顯示
- [ ] PipelineResponse.metadata 含 knowledge_sources（待 RAG 數據導入驗證）
- [x] MessageList 中 assistant 回應下方顯示來源引用（collapsible panel）
- [x] 來源引用格式：文件名 + 相關度分數 + 摘要片段
- [x] 可點擊展開查看完整來源內容（details/summary）
- [x] OrchestrationMetadata.knowledgeSources 類型定義

## S147-4: E2E 完整驗證 (1 SP)

### Scenario 驗證
- [x] Scenario A: 簡單問答（CHAT_MODE 直接回答）
- [x] Scenario B: 工作流程（WORKFLOW_MODE 多步執行）
- [x] Scenario C: Swarm 協作（Swarm Panel 顯示空狀態，待真實 Worker 事件）
- [x] Scenario D: 高風險審批（HITL 卡片顯示 → 批准 → Pipeline 繼續回應 ✅）
- [x] Scenario E: Session 恢復（關閉 tab 重開後 thread 列表保留）
- [ ] Scenario F: 知識檢索（RAG 已接線，待數據導入驗證引用顯示）

### Playwright E2E 測試
- [ ] 測試 SSE 事件接收和 UI 即時更新
- [ ] 測試 HITL 審批互動
- [ ] 測試 Session 恢復流程
- [ ] 測試 Swarm Panel 顯示

### 覆蓋驗證
- [ ] 10 步流程每步至少被一個 Scenario 覆蓋
- [ ] 所有 SSE 事件類型至少在一個 Scenario 中出現
- [ ] Swarm Panel、InlineApproval、IntentStatusChip 都有可視化對應

## 驗收測試

- [x] Mediator 使用 ConversationStateStore（非 dict）
- [ ] Session 重啟後可恢復
- [x] Session Resume API 可用
- [x] Checkpoint 每步自動保存（Redis/Memory）
- [x] Checkpoint 恢復檢查邏輯（load_latest + CHECKPOINT_RESTORED event）
- [x] search_knowledge 工具可調用
- [x] 知識來源 UI 組件已建立（待 RAG 數據驗證）
- [ ] Scenario A-F 全部通過
- [ ] 10 步流程全部有可視化
- [ ] Playwright E2E 測試通過
- [x] TypeScript 零錯誤
- [ ] `black . && isort . && flake8 .` 通過

---

**Status**: In Progress (infrastructure wired, E2E testing + frontend RAG UI pending)
