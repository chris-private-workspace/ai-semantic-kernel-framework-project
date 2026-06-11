# Sprint 134 Progress: OrchestratorBootstrap 全管線組裝

## 狀態概覽

| 項目 | 狀態 |
|------|------|
| **開始日期** | 2026-03-19 |
| **預計結束** | 2026-03-19 |
| **總點數** | 12 點 |
| **完成點數** | 12 點 |
| **進度** | 100% |
| **Phase** | Phase 39 — E2E Assembly D |
| **Branch** | `feature/phase-39-e2e-d` |

## Sprint 目標

1. ✅ OrchestratorBootstrap 工廠類（組裝 7 個 handler 的啟動入口）
2. ✅ InputGateway + RoutingHandler 接線（含 FrameworkSelector + SwarmModeHandler）
3. ✅ RiskAssessor + ApprovalHandler 接線（含 HITLController）
4. ✅ ExecutionHandler 接線（MAF executor + Claude executor + SwarmHandler）
5. ✅ MCP 工具動態註冊到 OrchestratorToolRegistry（MCPToolBridge）

## User Stories 進度

| Story | 名稱 | 點數 | 狀態 | 完成度 |
|-------|------|------|------|--------|
| S134-1 | OrchestratorBootstrap 類 | 3 | ✅ 完成 | 100% |
| S134-2 | InputGateway + RoutingHandler 接線 | 2 | ✅ 完成 | 100% |
| S134-3 | RiskAssessor + ApprovalHandler 接線 | 2 | ✅ 完成 | 100% |
| S134-4 | ExecutionHandler 接線 | 3 | ✅ 完成 | 100% |
| S134-5 | MCP 工具動態註冊 | 2 | ✅ 完成 | 100% |

## 完成項目詳情

### S134-1: OrchestratorBootstrap 類 (3 SP)
- **新增**: `backend/src/integrations/hybrid/orchestrator/bootstrap.py`
  - `OrchestratorBootstrap` class with `build()` factory method
  - 7 個 `_wire_*_handler()` 方法，每個都用 graceful degradation
  - `health_check()` — 驗證所有 handler 接線狀態
  - 依賴注入：接受 `llm_service` 參數，自動建立如未提供
  - `_create_tool_registry()` — 建立 ToolRegistry + DispatchHandlers + ResultSynthesiser
  - `_create_llm_service()` — 透過 LLMServiceFactory 建立

### S134-2: InputGateway + RoutingHandler 接線 (2 SP)
- `_wire_routing_handler()` 接線 4 個組件：
  - InputGateway (from orchestration/input_gateway)
  - BusinessIntentRouter (via create_router_with_llm())
  - FrameworkSelector (from hybrid/intent/router)
  - SwarmModeHandler (from hybrid/swarm_mode)

### S134-3: RiskAssessor + ApprovalHandler 接線 (2 SP)
- `_wire_approval_handler()` 接線 2 個組件：
  - RiskAssessor (from orchestration/risk_assessor)
  - HITLController (from orchestration/hitl/controller)

### S134-4: ExecutionHandler 接線 (3 SP)
- `_wire_execution_handler()` 接線 3 個執行引擎：
  - Claude executor: ClaudeCoordinator.coordinate_agents
  - MAF executor: WorkflowExecutorAdapter.execute
  - Swarm handler: SwarmModeHandler

### S134-5: MCP 工具動態註冊 (2 SP)
- **新增**: `backend/src/integrations/hybrid/orchestrator/mcp_tool_bridge.py`
  - `MCPToolBridge` class: MCP ServerRegistry → OrchestratorToolRegistry 轉換
  - `discover_and_register()` — 掃描 MCP 伺服器工具並批量註冊
  - `_create_lazy_handler()` — 首次調用才建立 MCP 連線
  - `_get_or_create_client()` — lazy-load MCPClient
- **修改**: `backend/src/api/v1/orchestrator/routes.py`
  - 新增 `_get_bootstrap()` singleton — 觸發完整管線組裝
  - `_get_tool_registry()` 現在從 Bootstrap 取得（fallback standalone）
  - `_get_session_factory()` 從 Bootstrap 取得 LLM service

## 檔案變更清單

| 操作 | 檔案路徑 |
|------|---------|
| 新增 | `backend/src/integrations/hybrid/orchestrator/bootstrap.py` |
| 新增 | `backend/src/integrations/hybrid/orchestrator/mcp_tool_bridge.py` |
| 修改 | `backend/src/api/v1/orchestrator/routes.py` |
| 修改 | `backend/src/integrations/hybrid/orchestrator/__init__.py` |

## 架構決策

| 決策 | 理由 |
|------|------|
| Graceful degradation 每個 handler | 任一依賴不可用不阻止整體啟動 |
| Lazy-loading MCP 工具 | 避免啟動時建立所有 MCP 連線 |
| Bootstrap singleton 在 routes.py | 第一次請求時觸發組裝，非啟動時 |
| Claude executor 用 coordinate_agents | 這是 ClaudeCoordinator 的主要入口 |

## 相關文檔

- [Sprint 134 Plan](../../sprint-planning/phase-39/sprint-134-plan.md)
- [Sprint 134 Checklist](../../sprint-planning/phase-39/sprint-134-checklist.md)
- [Phase 39 計劃](../../sprint-planning/phase-39/README.md)
