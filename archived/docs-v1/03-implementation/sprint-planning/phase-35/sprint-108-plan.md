# Sprint 108: 最短路徑端到端接通

**Sprint 目標**: 建立完整端到端流程，從 Chat API 到 LLM 回應的最短路徑接通
**週期**: Phase 35 — E2E Assembly A0
**Story Points**: 7 點
**前置條件**: Sprint 107 完成 (AgentHandler 原型就緒)

## Sprint 概述

Sprint 108 是 Phase 35 的第二個 Sprint，專注於最短路徑端到端接通。核心任務包括建立跨模組合約介面解耦 orchestration/ 和 hybrid/ 模組、建立 Orchestrator Chat API endpoint 作為 E2E pipeline 入口、修復 C-07 SQL Injection 安全漏洞，以及將 RoutingDecision 正確注入 pipeline context。

## User Stories

### Story S108-1: 跨模組合約介面 (1 點)
**作為** IT 運維管理者
**我希望** 系統模組之間有清晰的介面定義
**以便** 各模組能獨立演進而不互相耦合

#### 技術規格
- 新增 `backend/src/integrations/contracts/__init__.py`
- 新增 `backend/src/integrations/contracts/pipeline.py`
- `PipelineRequest` / `PipelineResponse` Pydantic models
- `PipelineSource` enum (USER, SERVICENOW, PROMETHEUS, API)
- 解耦 orchestration/ 和 hybrid/ 模組的直接依賴

### Story S108-2: Orchestrator Chat API endpoint (2 點)
**作為** IT 運維管理者
**我希望** 有一個統一的 Chat API 端點
**以便** 能夠端到端地與 AI 助手對話

#### 技術規格
- 新增 `backend/src/api/v1/orchestrator/__init__.py`
- 新增 `backend/src/api/v1/orchestrator/routes.py`
- 3 個端點：
  - `POST /api/v1/orchestrator/chat` — 完整 E2E pipeline
  - `GET /api/v1/orchestrator/test-intent` — 意圖路由測試
  - `GET /api/v1/orchestrator/health` — 健康檢查
- 流程：LLMServiceFactory → BusinessIntentRouter → AgentHandler → OrchestratorMediator → 回應
- Lazy imports 避免啟動失敗
- 完整的 error handling 和 processing time 追蹤

### Story S108-3: API 路由註冊 (1 點)
**作為** IT 運維管理者
**我希望** 新的 API 端點能被正確註冊到系統
**以便** 前端能存取新的 Chat API

#### 技術規格
- 修改 `backend/src/api/v1/__init__.py`
- 新增 `orchestrator_chat_router` import 和 `protected_router` 註冊
- 遵循項目現有的集中式路由註冊模式

### Story S108-4: C-07 SQL Injection 修復 (1 點)
**作為** IT 運維管理者
**我希望** 系統沒有 SQL Injection 安全漏洞
**以便** 平台資料安全得到保障

#### 技術規格
- 修改 `backend/src/integrations/agent_framework/memory/postgres_storage.py`
- 新增 `_validate_table_name()` — 白名單驗證 table name（僅允許字母/數字/底線）
- 新增 `_validate_jsonb_path_part()` — 驗證 JSONB 路徑段
- `TABLE_NAME` 在 `__init__` 時驗證（攔截子類別覆蓋）
- 其他 SQL 已使用參數化查詢（$1, $2 等），無需修改

### Story S108-5: RoutingDecision 注入 + AgentHandler 修改 (2 點)
**作為** IT 運維管理者
**我希望** Agent 能取得意圖路由結果
**以便** 基於意圖分類提供準確的回應

#### 技術規格
- 修改 `backend/src/integrations/hybrid/orchestrator/agent_handler.py` (L67)
- AgentHandler 從 `context.get("routing_decision")` 和 `request.metadata.get("routing_decision")` 雙重查找
- Endpoint 將 RoutingDecision 序列化為 dict 放入 `OrchestratorRequest.metadata`

## 架構決策

| 決策 | 理由 |
|------|------|
| 建立新 endpoint 而非修改 AG-UI | 避免破壞現有功能，低風險驗證端到端 |
| 路由註冊在 `api/v1/__init__.py` | 遵循項目集中式註冊模式（非 main.py） |
| RoutingDecision 序列化到 metadata | 不需修改 OrchestratorRequest 數據結構 |
| C-07 用白名單而非 escape | 白名單更安全，table name 本不應包含特殊字元 |

## 檔案變更清單

| 操作 | 檔案路徑 |
|------|---------|
| 新增 | `backend/src/integrations/contracts/__init__.py` |
| 新增 | `backend/src/integrations/contracts/pipeline.py` |
| 新增 | `backend/src/api/v1/orchestrator/__init__.py` |
| 新增 | `backend/src/api/v1/orchestrator/routes.py` |
| 修改 | `backend/src/api/v1/__init__.py` |
| 修改 | `backend/src/integrations/agent_framework/memory/postgres_storage.py` |
| 修改 | `backend/src/integrations/hybrid/orchestrator/agent_handler.py` |

## Phase 35 驗收狀態

| 驗收標準 | 狀態 | 說明 |
|---------|------|------|
| 繁中 IT 問題 → 正確識別意圖 → 合理回應 | ✅ 代碼就緒 | 需要真實 Azure OpenAI API Key 驗證 |
| 端到端延遲 < 5 秒 | ⏳ 待驗證 | 需要啟動服務測試 |
| 零 Mock / 模擬 | ✅ 架構支持 | LLMServiceFactory 自動偵測真實 API |
| C-07 SQL Injection 修復 | ✅ 完成 | 白名單驗證 + 測試 |

## 相關連結
- [Sprint 108 Checklist](./sprint-108-checklist.md)
- [Sprint 107 Plan](./sprint-107-plan.md)
- [Phase 35 Overview](./README.md)

---

**Sprint 開始**: 2026-03-19
**Sprint 結束**: 2026-03-19
**Story Points**: 7
**狀態**: ✅ 已完成
