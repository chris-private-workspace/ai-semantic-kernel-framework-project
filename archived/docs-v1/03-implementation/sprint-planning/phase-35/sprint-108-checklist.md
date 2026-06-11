# Sprint 108 Checklist: 最短路徑端到端接通

**Sprint 目標**: 建立完整端到端流程，從 Chat API 到 LLM 回應的最短路徑接通
**總點數**: 7 點
**狀態**: ✅ 已完成

## S108-1: 跨模組合約介面 (1 點) ✅
- [x] 新增 `backend/src/integrations/contracts/__init__.py`
- [x] 新增 `backend/src/integrations/contracts/pipeline.py`
  - [x] `PipelineRequest` Pydantic model
  - [x] `PipelineResponse` Pydantic model
  - [x] `PipelineSource` enum (USER, SERVICENOW, PROMETHEUS, API)
- [x] 解耦 orchestration/ 和 hybrid/ 模組的直接依賴

## S108-2: Orchestrator Chat API endpoint (2 點) ✅
- [x] 新增 `backend/src/api/v1/orchestrator/__init__.py`
- [x] 新增 `backend/src/api/v1/orchestrator/routes.py`
  - [x] `POST /api/v1/orchestrator/chat` — 完整 E2E pipeline
  - [x] `GET /api/v1/orchestrator/test-intent` — 意圖路由測試
  - [x] `GET /api/v1/orchestrator/health` — 健康檢查
- [x] 流程接通：LLMServiceFactory → BusinessIntentRouter → AgentHandler → OrchestratorMediator → 回應
- [x] Lazy imports 避免啟動失敗
- [x] 完整的 error handling 和 processing time 追蹤

## S108-3: API 路由註冊 (1 點) ✅
- [x] 修改 `backend/src/api/v1/__init__.py`
  - [x] 新增 `orchestrator_chat_router` import
  - [x] 註冊到 `protected_router`
- [x] 遵循項目集中式路由註冊模式

## S108-4: C-07 SQL Injection 修復 (1 點) ✅
- [x] 修改 `backend/src/integrations/agent_framework/memory/postgres_storage.py`
  - [x] 新增 `_validate_table_name()` — 白名單驗證（僅允許字母/數字/底線）
  - [x] 新增 `_validate_jsonb_path_part()` — 驗證 JSONB 路徑段
  - [x] `TABLE_NAME` 在 `__init__` 時驗證（攔截子類別覆蓋）
- [x] 確認其他 SQL 已使用參數化查詢（$1, $2 等）

## S108-5: RoutingDecision 注入 + AgentHandler 修改 (2 點) ✅
- [x] 修改 `backend/src/integrations/hybrid/orchestrator/agent_handler.py`
  - [x] 從 `context.get("routing_decision")` 查找
  - [x] 從 `request.metadata.get("routing_decision")` 雙重查找
- [x] Endpoint 將 RoutingDecision 序列化為 dict 放入 `OrchestratorRequest.metadata`

## 驗證標準
- [x] 完整端到端流程：Chat API → InputGateway → Mediator → AgentHandler → LLM → 回應
- [x] 跨模組合約介面使用 Pydantic 型別定義
- [x] C-07 SQL Injection 漏洞已修復（白名單驗證）
- [x] API 路由正確註冊並可存取
- [x] RoutingDecision 能正確傳遞到 AgentHandler

## Phase 35 驗收確認
- [x] Sprint 107 + Sprint 108 全部完成 (15 Story Points)
- [x] AgentHandler LLM 決策引擎就緒
- [x] 端到端 pipeline 代碼接通
- [x] C-07 安全漏洞修復
- [x] 零 Mock 架構設計（LLMServiceFactory 自動偵測真實 API）

## 相關連結
- [Sprint 108 Plan](./sprint-108-plan.md)
- [Sprint 107 Checklist](./sprint-107-checklist.md)
- [Phase 35 Overview](./README.md)

---

**Sprint 狀態**: ✅ 已完成
**Story Points**: 7
**完成日期**: 2026-03-19
