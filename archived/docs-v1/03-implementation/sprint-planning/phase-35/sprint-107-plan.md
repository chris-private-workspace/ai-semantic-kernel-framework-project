# Sprint 107: Orchestrator Agent 原型

**Sprint 目標**: 建立 AgentHandler LLM 決策引擎，啟用三層意圖路由
**週期**: Phase 35 — E2E Assembly A0
**Story Points**: 8 點
**前置條件**: Phase 29 完成、MAF RC4 升級完成、E2E Blueprint 三方專家分析完成

## Sprint 概述

Sprint 107 是 Phase 35 的第一個 Sprint，專注於建立 Hybrid Orchestrator Agent 原型。核心任務包括新增 AgentHandler 類別作為 LLM 決策引擎、設計繁體中文 IT 運維助手 System Prompt、透過 LLMServiceProtocol 接入 Azure OpenAI，以及啟用三層意圖路由的 L1 PatternMatcher 和 L3 LLMClassifier。

## User Stories

### Story S107-1: AgentHandler 類別建立 (2 點)
**作為** IT 運維管理者
**我希望** 平台擁有一個 LLM 決策引擎
**以便** 能夠智慧地處理用戶的 IT 運維問題

#### 技術規格
- 新增 `backend/src/integrations/hybrid/orchestrator/agent_handler.py` (199 行)
- 繼承 `Handler` ABC，實作 `handle()` 方法
- 支持 `LLMServiceProtocol` 注入
- Graceful degradation：LLM 不可用時返回 fallback 回應
- Error handling：LLM 呼叫失敗時不崩潰，返回友善錯誤訊息

### Story S107-2: Function Tools 實作 (2 點)
**作為** IT 運維管理者
**我希望** Agent 能夠理解意圖路由結果並生成對應回應
**以便** 收到準確且有上下文的回覆

#### 技術規格
- `_build_context_prompt()` 方法將 RoutingDecision 轉為 LLM 可讀的上下文
- 支持 dataclass 和 dict 兩種輸入格式
- 包含 intent_category, sub_intent, confidence, risk_level, completeness, routing_layer

### Story S107-3: System Prompt 設計 (1 點)
**作為** IT 運維管理者
**我希望** Agent 以繁體中文回應 IT 運維問題
**以便** 台灣/香港用戶能無障礙使用

#### 技術規格
- 新增 `backend/src/integrations/hybrid/prompts/__init__.py`
- 新增 `backend/src/integrations/hybrid/prompts/orchestrator.py`
- 繁體中文 IT 運維助手角色定義
- 包含回應格式指引和注意事項

### Story S107-4: Azure OpenAI 連接配置 (1 點)
**作為** IT 運維管理者
**我希望** 平台使用真實的 LLM 服務
**以便** 獲得高品質的 AI 回應

#### 技術規格
- AgentHandler 通過 `LLMServiceProtocol` 抽象層呼叫 LLM
- `LLMServiceFactory.create()` 自動偵測 Azure OpenAI 環境變數
- 不直接綁定特定 LLM 供應商，保持靈活性（符合 AD-2 架構決策）

### Story S107-5: 三層意圖路由啟用 (2 點)
**作為** IT 運維管理者
**我希望** 系統能自動分類用戶輸入的意圖
**以便** 不同類型的問題得到正確的處理

#### 技術規格
- 修改 `backend/src/integrations/hybrid/orchestrator/contracts.py` — HandlerType 新增 AGENT
- 修改 `backend/src/integrations/hybrid/orchestrator/mediator.py` — Pipeline 新增 Step 5 (Agent)
- 修改 `backend/src/integrations/hybrid/__init__.py` — 匯出 AgentHandler
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

## 相關連結
- [Sprint 107 Checklist](./sprint-107-checklist.md)
- [Phase 35 Overview](./README.md)

---

**Sprint 開始**: 2026-03-19
**Sprint 結束**: 2026-03-19
**Story Points**: 8
**狀態**: ✅ 已完成
