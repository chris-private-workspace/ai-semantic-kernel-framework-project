# Sprint 107 Progress: Orchestrator Agent 原型

## 狀態概覽

| 項目 | 狀態 |
|------|------|
| **開始日期** | 2026-03-19 |
| **預計結束** | 2026-03-19 |
| **總點數** | 8 點 |
| **完成點數** | 8 點 |
| **進度** | 100% |
| **Phase** | Phase 35 — E2E Assembly A0 |
| **Branch** | `feature/phase-35-e2e-a0` |

## Sprint 目標

1. ✅ 建立 AgentHandler 類別（LLM 決策引擎）
2. ✅ 實作 Function Tools（route_intent context + respond_to_user）
3. ✅ System Prompt 設計（繁體中文 IT 運維助手）
4. ✅ 配置 Azure OpenAI 連接（透過 LLMServiceProtocol）
5. ✅ 三層意圖路由啟用（L1 PatternMatcher + L3 LLMClassifier）

## User Stories 進度

| Story | 名稱 | 點數 | 狀態 | 完成度 |
|-------|------|------|------|--------|
| S107-1 | AgentHandler 類別建立 | 2 | ✅ 完成 | 100% |
| S107-2 | Function Tools 實作 | 2 | ✅ 完成 | 100% |
| S107-3 | System Prompt 設計 | 1 | ✅ 完成 | 100% |
| S107-4 | Azure OpenAI 連接配置 | 1 | ✅ 完成 | 100% |
| S107-5 | 三層意圖路由啟用 | 2 | ✅ 完成 | 100% |

## 完成項目詳情

### S107-1: AgentHandler 類別 (2 SP)
- **新增**: `backend/src/integrations/hybrid/orchestrator/agent_handler.py` (199 行)
- 繼承 `Handler` ABC，實作 `handle()` 方法
- 支持 `LLMServiceProtocol` 注入
- Graceful degradation：LLM 不可用時返回 fallback 回應
- Error handling：LLM 呼叫失敗時不崩潰，返回友善錯誤訊息

### S107-2: Function Tools Context (2 SP)
- `_build_context_prompt()` 方法將 RoutingDecision 轉為 LLM 可讀的上下文
- 支持 dataclass 和 dict 兩種輸入格式
- 包含 intent_category, sub_intent, confidence, risk_level, completeness, routing_layer

### S107-3: System Prompt 設計 (1 SP)
- **新增**: `backend/src/integrations/hybrid/prompts/__init__.py`
- **新增**: `backend/src/integrations/hybrid/prompts/orchestrator.py`
- 繁體中文 IT 運維助手角色定義
- 包含回應格式指引和注意事項

### S107-4: Azure OpenAI 連接 (1 SP)
- AgentHandler 通過 `LLMServiceProtocol` 抽象層呼叫 LLM
- `LLMServiceFactory.create()` 自動偵測 Azure OpenAI 環境變數
- 不直接綁定特定 LLM 供應商，保持靈活性

### S107-5: 三層意圖路由啟用 (2 SP)
- **修改**: `backend/src/integrations/hybrid/orchestrator/contracts.py` — HandlerType 新增 AGENT
- **修改**: `backend/src/integrations/hybrid/orchestrator/mediator.py` — Pipeline 新增 Step 5 (Agent)
- **修改**: `backend/src/integrations/hybrid/__init__.py` — 匯出 AgentHandler
- Pipeline 順序：Context → Routing → Dialog → Approval → **Agent** → Execution → Observability
- Agent short-circuit 機制：簡單問題直接回應，不需進入 Execution

## 架構決策

| 決策 | 理由 |
|------|------|
| AgentHandler 預設 `should_short_circuit=True` | Sprint 107 目標是直接回應，後續 Phase 可改為 False 以進入 Execution dispatch |
| 使用 `LLMServiceProtocol` 而非直接呼叫 Azure OpenAI | 保持供應商靈活性，符合 AD-2 架構決策 |
| Agent handler 在 APPROVAL 後、EXECUTION 前 | 確定性邏輯（路由/風險/審批）先執行，LLM 只處理需要推理的部分 |

## 檔案變更清單

| 操作 | 檔案路徑 |
|------|---------|
| 新增 | `backend/src/integrations/hybrid/orchestrator/agent_handler.py` |
| 新增 | `backend/src/integrations/hybrid/prompts/__init__.py` |
| 新增 | `backend/src/integrations/hybrid/prompts/orchestrator.py` |
| 修改 | `backend/src/integrations/hybrid/orchestrator/contracts.py` |
| 修改 | `backend/src/integrations/hybrid/orchestrator/mediator.py` |
| 修改 | `backend/src/integrations/hybrid/__init__.py` |

## 相關文檔

- [Phase 35 計劃](../../sprint-planning/phase-35/README.md)
- [E2E Blueprint 架構審查](../../../../claudedocs/6-ai-assistant/analysis/IPA-E2E-Blueprint-Architecture-Review.md)
