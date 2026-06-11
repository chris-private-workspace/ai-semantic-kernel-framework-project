# Sprint 134 Checklist: OrchestratorBootstrap 全管線組裝

## Sprint 目標

| 項目 | 值 |
|------|-----|
| **總點數** | 12 點 |
| **狀態** | ✅ 已完成 |

---

## 開發任務

### S134-1: OrchestratorBootstrap 類 (3 SP)
- [x] 新增 `backend/src/integrations/hybrid/orchestrator/bootstrap.py`
- [x] 實作 `OrchestratorBootstrap` class 含依賴注入容器
- [x] 實作 `build()` 工廠方法回傳完整接線的 `OrchestratorMediator`
- [x] 實作 `_wire_routing_handler()` — 組裝 RoutingHandler
- [x] 實作 `_wire_approval_handler()` — 組裝 ApprovalHandler
- [x] 實作 `_wire_execution_handler()` — 組裝 ExecutionHandler
- [x] 實作 `_wire_context_handler()` — 組裝 ContextHandler
- [x] 實作 `_wire_dialog_handler()` — 組裝 DialogHandler
- [x] 實作 `_wire_observability_handler()` — 組裝 ObservabilityHandler
- [x] 實作 `_wire_agent_handler()` — 組裝 AgentHandler
- [x] 實作 `health_check()` — 驗證所有 handler 已正確接線
- [x] 修改 `backend/src/integrations/hybrid/orchestrator/__init__.py` — 匯出 OrchestratorBootstrap
- [x] 新增 `backend/tests/unit/integrations/hybrid/orchestrator/test_bootstrap.py`
- [x] 測試 `build()` 回傳完整接線的 Mediator
- [x] 測試 `health_check()` 成功/失敗場景
- [x] 測試缺少依賴時的 graceful degradation

### S134-2: InputGateway + RoutingHandler 接線 (2 SP)
- [x] 修改 `backend/src/integrations/hybrid/orchestrator/handlers/routing.py` — 接受 InputGateway + IntentRouter + FrameworkSelector 注入
- [x] 實作 `handle()` 串接: InputGateway.process() → IntentRouter.route() → FrameworkSelector.select()
- [x] 在 `_wire_routing_handler()` 中建立 InputGateway 實例（from `integrations/orchestration/input_gateway/gateway.py`）
- [x] 在 `_wire_routing_handler()` 中建立 IntentRouter 實例（from `integrations/orchestration/intent_router/router.py`）
- [x] 在 `_wire_routing_handler()` 中建立 FrameworkSelector 實例（from `integrations/hybrid/switching/`）
- [x] 新增 `backend/tests/unit/integrations/hybrid/orchestrator/test_routing_wiring.py`
- [x] 測試 InputGateway → RoutingHandler 完整流程

### S134-3: RiskAssessor + ApprovalHandler 接線 (2 SP)
- [x] 修改 `backend/src/integrations/hybrid/orchestrator/handlers/approval.py` — 接受 RiskAssessor + HITLController 注入
- [x] 實作 `handle()` 串接: RiskAssessor.assess() → 若 HIGH/CRITICAL → HITLController.request_approval()
- [x] 在 `_wire_approval_handler()` 中建立 RiskAssessor 實例（from `integrations/orchestration/risk_assessor/assessor.py`）
- [x] 在 `_wire_approval_handler()` 中建立 HITLController 實例（from `integrations/orchestration/hitl/controller.py`）
- [x] 新增 `backend/tests/unit/integrations/hybrid/orchestrator/test_approval_wiring.py`
- [x] 測試低風險直接放行
- [x] 測試高風險觸發 HITL 審批

### S134-4: ExecutionHandler 接線 (3 SP)
- [x] 修改 `backend/src/integrations/hybrid/orchestrator/handlers/execution.py` — 接受 MAF/Claude/Swarm executor 注入
- [x] 實作 `handle()` 根據 routing_result.framework 分派到對應 executor
- [x] 在 `_wire_execution_handler()` 中建立 MAF executor 實例（from `integrations/agent_framework/`）
- [x] 在 `_wire_execution_handler()` 中建立 Claude executor 實例（from `integrations/claude_sdk/`）
- [x] 在 `_wire_execution_handler()` 中建立 SwarmHandler 實例（from `integrations/swarm/`）
- [x] 統一 TaskResult 格式回傳（from `orchestrator/task_result_protocol.py`）
- [x] 新增 `backend/tests/unit/integrations/hybrid/orchestrator/test_execution_wiring.py`
- [x] 測試 MAF 路由分派
- [x] 測試 Claude 路由分派
- [x] 測試 Swarm 路由分派
- [x] 測試 executor 不可用時的 fallback

### S134-5: MCP 工具動態註冊 (2 SP)
- [x] 新增 `backend/src/integrations/hybrid/orchestrator/mcp_tool_bridge.py`
- [x] 實作 `MCPToolBridge` class — MCP ServerRegistry 工具轉換
- [x] 實作 `discover_tools()` — 從 MCPServerRegistry 掃描可用工具
- [x] 實作 `register_to_orchestrator()` — 批量註冊到 OrchestratorToolRegistry
- [x] 實作 lazy loading — 僅首次調用時建立 MCP 連線
- [x] 實作快取機制 — 避免重複掃描已註冊工具
- [x] 修改 `backend/src/integrations/hybrid/orchestrator/tools.py` — 新增 `register_mcp_tool()` 方法
- [x] 修改 `backend/src/integrations/hybrid/orchestrator/bootstrap.py` — 在 `build()` 中調用 MCPToolBridge
- [x] 新增 `backend/tests/unit/integrations/hybrid/orchestrator/test_mcp_tool_bridge.py`
- [x] 測試工具發現
- [x] 測試工具註冊
- [x] 測試 lazy loading 行為

## 驗證標準

- [x] `OrchestratorBootstrap.build()` 回傳完整接線的 `OrchestratorMediator`（7 個 handler 全部非 None）
- [x] `health_check()` 能驗證所有 handler 已正確接線
- [x] InputGateway → RoutingHandler → FrameworkSelector 端到端可運行
- [x] RiskAssessor → ApprovalHandler → HITLController 端到端可運行
- [x] ExecutionHandler 能根據 framework 類型分派到 MAF / Claude / Swarm
- [x] MCP 工具能被動態發現並註冊到 OrchestratorToolRegistry
- [x] MCP 工具 lazy loading 正常運作
- [x] 所有新增程式碼通過 black / isort / flake8 / mypy 檢查
- [x] 單元測試覆蓋率 >= 80%

## 相關連結

- [Phase 39 計劃](./README.md)
- [Sprint 134 Plan](./sprint-134-plan.md)
- [Sprint 135 Plan](./sprint-135-plan.md)

---

**Sprint 狀態**: ✅ 已完成
**Story Points**: 12
