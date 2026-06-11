# Sprint 147: Session 持久化 + RAG + Checkpoint + QA

## Sprint 目標

1. Session/Checkpoint 從 Python dict 遷移到 PostgreSQL/Redis 持久化
2. Checkpoint 每步自動保存，服務重啟後可恢復
3. RAG Pipeline 連接：search_knowledge 工具在 function calling 中可調用
4. E2E 完整驗證：6 個 Scenario、10 步流程全通過

## Sprint 週期

| 項目 | 值 |
|------|-----|
| **Phase** | Phase 42 — E2E Pipeline Deep Integration |
| **Sprint** | 147 |
| **Story Points** | 8 點 |
| **狀態** | 📋 計劃中 |

## User Stories

### S147-1: Session 持久化 (3 SP)

**作為** 系統使用者
**我希望** 我的對話 session 在服務重啟後仍然保留
**以便** 不需要重新開始對話，系統能恢復到之前的狀態

**技術規格**:

**改動 1: `backend/src/integrations/orchestration/mediator.py` — 替換 dict**
- 將 Mediator 中的 `self._sessions: dict = {}` (line ~89) 替換為 `ConversationStateStore`
- `ConversationStateStore` 使用 Redis 作為主要存儲（快速讀寫）
- PostgreSQL 作為持久化備份（Redis 清除後仍可恢復）
- Session 資料結構：
  ```python
  class SessionState:
      session_id: str
      user_id: str
      messages: list[dict]
      pipeline_state: dict  # 路由結果、風險評估、當前 handler
      metadata: dict
      created_at: datetime
      updated_at: datetime
  ```

**改動 2: `backend/src/integrations/orchestration/session_recovery.py` — API 暴露**
- SessionRecoveryManager 新增 REST API 端點：
  - `GET /orchestrator/sessions/{session_id}` — 取得 session 狀態
  - `POST /orchestrator/sessions/{session_id}/resume` — 恢復 session
  - `DELETE /orchestrator/sessions/{session_id}` — 刪除 session
- Session Resume 恢復完整 pipeline 狀態（不只是對話歷史）

**改動 3: `backend/src/api/v1/orchestration.py` — 註冊路由**
- 新增 session 管理路由
- 驗證 session_id 所有權（確保用戶只能存取自己的 session）

### S147-2: Checkpoint PostgreSQL Backend (2 SP)

**作為** Pipeline 的執行引擎
**我希望** 每個 Pipeline 步驟自動保存 Checkpoint
**以便** Pipeline 中斷時能從上次 Checkpoint 恢復，而非重新開始

**技術規格**:

**改動 1: `backend/src/infrastructure/checkpoint/` — PostgreSQL 實作**
- 切換 `CheckpointStorage` 介面實作到 `PostgresCheckpointStorage`
- Checkpoint 資料表結構：
  ```sql
  CREATE TABLE pipeline_checkpoints (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      session_id VARCHAR(64) NOT NULL,
      step_name VARCHAR(128) NOT NULL,
      step_index INTEGER NOT NULL,
      state JSONB NOT NULL,
      created_at TIMESTAMP DEFAULT NOW(),
      UNIQUE(session_id, step_name)
  );
  ```
- 每個 Handler 執行完畢後自動保存 Checkpoint

**改動 2: `backend/src/integrations/orchestration/mediator.py` — Checkpoint 整合**
- Mediator 的 Handler 迴圈中加入 Checkpoint 保存邏輯
- Pipeline 啟動時檢查是否有 Checkpoint：
  - 有 → 從 Checkpoint 恢復，跳過已完成步驟
  - 無 → 正常從頭開始
- Checkpoint 恢復後發射 `CHECKPOINT_RESTORED` SSE 事件

**改動 3: Alembic Migration**
- 新增 migration 建立 `pipeline_checkpoints` 資料表
- 新增 index：`session_id` + `created_at`

### S147-3: RAG Pipeline 連接 (2 SP)

**作為** Chat 使用者
**我希望** 系統能搜尋知識庫來回答我的問題
**以便** 得到基於組織內部知識的準確回答，而非純 LLM 猜測

**技術規格**:

**改動 1: `backend/src/integrations/orchestration/handlers/tool_registry.py` — search_knowledge 實作**
- `search_knowledge` 工具連接到 RAG Pipeline：
  ```python
  async def search_knowledge(params: dict) -> dict:
      query = params["query"]
      top_k = params.get("top_k", 5)
      results = await rag_pipeline.search(query, top_k=top_k)
      return {"sources": results, "count": len(results)}
  ```
- RAG 搜尋結果注入 LLM prompt（作為 context）

**改動 2: 前端知識來源顯示**
- PipelineResponse.metadata 中包含 `knowledge_sources`
- MessageList 中 assistant 回應下方顯示知識來源引用
- 來源引用格式：文件名 + 相關度分數 + 摘要片段
- 可點擊展開查看完整來源內容

**改動 3: Function Calling 整合**
- `search_knowledge` 在 AgentHandler tool schemas 中已註冊（Sprint 144）
- 確保 LLM 在需要時自動調用 search_knowledge
- 搜尋結果正確注入後續 LLM 生成的 context

### S147-4: E2E 完整驗證 (1 SP)

**作為** 開發團隊
**我希望** Phase 42 的所有功能在 6 個場景中端到端驗證通過
**以便** 確認 10 步 E2E 流程全部可運作

**技術規格**:

**驗證場景**:

| Scenario | 描述 | 覆蓋步驟 |
|----------|------|---------|
| A: 簡單問答 | 用戶問「什麼是 CI/CD？」→ CHAT_MODE → 直接回答 | ①②③④⑧⑩ |
| B: 工作流程 | 用戶說「部署 staging 環境」→ WORKFLOW_MODE → 多步執行 | ①②③④⑤⑥⑦⑧ |
| C: Swarm 協作 | 用戶說「全面排查系統故障」→ SWARM_MODE → 多 Worker | ①②③④⑤⑦⑧ |
| D: 高風險審批 | 用戶說「刪除生產資料庫」→ HITL 審批 → 批准/拒絕 | ①②③④⑤⑦⑧ |
| E: Session 恢復 | 對話中途重啟 → 恢復 session → 繼續 | ②⑨ |
| F: 知識檢索 | 用戶問內部文件問題 → RAG 搜尋 → 引用回答 | ①②③⑧⑩ |

**Playwright 自動化測試**:
- 每個 Scenario 撰寫 Playwright E2E 測試
- 測試 SSE 事件接收和 UI 即時更新
- 測試 HITL 審批互動
- 測試 Session 恢復流程

**驗證清單**:
- 10 步流程每步至少被一個 Scenario 覆蓋
- 所有 SSE 事件類型至少在一個 Scenario 中出現
- Swarm Panel、InlineApproval、IntentStatusChip 都有可視化對應

## 驗收標準

- [ ] Mediator 使用 ConversationStateStore（非 Python dict）
- [ ] Session 在服務重啟後可恢復
- [ ] Session Resume API 端點可用
- [ ] Pipeline 每步自動保存 Checkpoint 到 PostgreSQL
- [ ] Pipeline 中斷後可從 Checkpoint 恢復
- [ ] search_knowledge 工具在 function calling 中可調用
- [ ] 知識檢索結果注入 LLM prompt
- [ ] 前端顯示知識來源引用
- [ ] Scenario A-F 全部端到端驗證通過
- [ ] 10 步流程全部有可視化對應
- [ ] Playwright E2E 測試通過
- [ ] TypeScript 零錯誤、npm run build 通過
- [ ] `black . && isort . && flake8 .` 通過

## 相關連結

- [Phase 42 計劃](./README.md)
- [Sprint 146 Plan](./sprint-146-plan.md)

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 8
