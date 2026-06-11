# Sprint 134: OrchestratorBootstrap 全管線組裝

## Sprint 目標

1. OrchestratorBootstrap 工廠類 — 組裝 7 個 handler 的啟動入口
2. InputGateway + RoutingHandler 接線（含 FrameworkSelector）
3. RiskAssessor + ApprovalHandler 接線
4. ExecutionHandler 接線（MAF executor + Claude executor + SwarmHandler）
5. MCP 工具動態註冊到 OrchestratorToolRegistry

## Sprint 週期

| 項目 | 值 |
|------|-----|
| **Phase** | Phase 39 — E2E Assembly D |
| **Sprint** | 134 |
| **Story Points** | 12 點 |
| **狀態** | 📋 計劃中 |

## Sprint 概述

Sprint 134 是 Phase 39 的第一個 Sprint，專注於建立 OrchestratorBootstrap 啟動組裝模組，將 Phase 35-38 已建立但各自獨立的 7 個 handler 一次性接線到 OrchestratorMediator。包含 OrchestratorBootstrap 工廠類（含依賴注入容器和健康檢查）、InputGateway + RoutingHandler 接線（整合 FrameworkSelector 路由策略）、RiskAssessor + ApprovalHandler 接線（含 HITL 審批流程）、ExecutionHandler 接線（MAF / Claude / Swarm 三引擎）、以及 MCP 工具動態註冊到 OrchestratorToolRegistry（lazy loading + 快取）。

## User Stories

### S134-1: OrchestratorBootstrap 類 (3 SP)

**作為** 後端開發者
**我希望** 有一個統一的啟動組裝入口
**以便** 一次性將所有 handler 接線到 OrchestratorMediator，取代目前全部 default None 的狀態

**技術規格**:
- 新增 `backend/src/integrations/hybrid/orchestrator/bootstrap.py`
  - `OrchestratorBootstrap` class: 工廠方法 `build()` 回傳完整接線的 `OrchestratorMediator`
  - 依賴注入容器: 接受 Settings / DB Session / Redis 等外部依賴
  - `_wire_routing_handler()` — 組裝 RoutingHandler
  - `_wire_approval_handler()` — 組裝 ApprovalHandler
  - `_wire_execution_handler()` — 組裝 ExecutionHandler
  - `_wire_context_handler()` — 組裝 ContextHandler
  - `_wire_dialog_handler()` — 組裝 DialogHandler
  - `_wire_observability_handler()` — 組裝 ObservabilityHandler
  - `_wire_agent_handler()` — 組裝 AgentHandler
  - `health_check()` — 驗證所有 handler 已正確接線
- 修改 `backend/src/integrations/hybrid/orchestrator/__init__.py`
  - 匯出 `OrchestratorBootstrap`
- 新增 `backend/tests/unit/integrations/hybrid/orchestrator/test_bootstrap.py`
  - 測試 `build()` 回傳完整接線的 Mediator
  - 測試 `health_check()` 成功/失敗場景
  - 測試缺少依賴時的 graceful degradation

### S134-2: InputGateway + RoutingHandler 接線 (2 SP)

**作為** Orchestrator 系統
**我希望** InputGateway 和 RoutingHandler 被正確接線
**以便** 使用者輸入能經過標準化處理後路由到正確的執行引擎

**技術規格**:
- 修改 `backend/src/integrations/hybrid/orchestrator/bootstrap.py`
  - `_wire_routing_handler()` 實作:
    - 建立 `InputGateway` (from `backend/src/integrations/orchestration/input_gateway/gateway.py`)
    - 建立 `IntentRouter` (from `backend/src/integrations/orchestration/intent_router/router.py`)
    - 建立 `FrameworkSelector` (from `backend/src/integrations/hybrid/switching/`)
    - 將三者注入 `RoutingHandler` (from `backend/src/integrations/hybrid/orchestrator/handlers/routing.py`)
- 修改 `backend/src/integrations/hybrid/orchestrator/handlers/routing.py`
  - 確保 `RoutingHandler.__init__()` 接受 `input_gateway`, `intent_router`, `framework_selector` 參數
  - `handle()` 方法串接: InputGateway.process() → IntentRouter.route() → FrameworkSelector.select()
- 新增 `backend/tests/unit/integrations/hybrid/orchestrator/test_routing_wiring.py`
  - 測試 InputGateway → RoutingHandler 完整流程

### S134-3: RiskAssessor + ApprovalHandler 接線 (2 SP)

**作為** Orchestrator 系統
**我希望** RiskAssessor 和 ApprovalHandler 被正確接線
**以便** 高風險操作能自動觸發 HITL 審批流程

**技術規格**:
- 修改 `backend/src/integrations/hybrid/orchestrator/bootstrap.py`
  - `_wire_approval_handler()` 實作:
    - 建立 `RiskAssessor` (from `backend/src/integrations/orchestration/risk_assessor/assessor.py`)
    - 建立 `HITLController` (from `backend/src/integrations/orchestration/hitl/controller.py`)
    - 將兩者注入 `ApprovalHandler` (from `backend/src/integrations/hybrid/orchestrator/handlers/approval.py`)
- 修改 `backend/src/integrations/hybrid/orchestrator/handlers/approval.py`
  - 確保 `ApprovalHandler.__init__()` 接受 `risk_assessor`, `hitl_controller` 參數
  - `handle()` 方法串接: RiskAssessor.assess() → 若 HIGH/CRITICAL → HITLController.request_approval()
- 新增 `backend/tests/unit/integrations/hybrid/orchestrator/test_approval_wiring.py`
  - 測試低風險直接放行
  - 測試高風險觸發 HITL 審批

### S134-4: ExecutionHandler 接線 (3 SP)

**作為** Orchestrator 系統
**我希望** ExecutionHandler 被正確接線到三個執行引擎
**以便** 任務能根據路由結果分派到 MAF Workflow / Claude Worker / Swarm

**技術規格**:
- 修改 `backend/src/integrations/hybrid/orchestrator/bootstrap.py`
  - `_wire_execution_handler()` 實作:
    - 建立 MAF executor (from `backend/src/integrations/agent_framework/`)
    - 建立 Claude executor (from `backend/src/integrations/claude_sdk/`)
    - 建立 SwarmHandler (from `backend/src/integrations/swarm/`)
    - 將三者注入 `ExecutionHandler` (from `backend/src/integrations/hybrid/orchestrator/handlers/execution.py`)
- 修改 `backend/src/integrations/hybrid/orchestrator/handlers/execution.py`
  - 確保 `ExecutionHandler.__init__()` 接受 `maf_executor`, `claude_executor`, `swarm_handler` 參數
  - `handle()` 方法根據 routing_result.framework 分派到對應 executor
  - 統一 `TaskResult` 格式回傳 (from `backend/src/integrations/hybrid/orchestrator/task_result_protocol.py`)
- 新增 `backend/tests/unit/integrations/hybrid/orchestrator/test_execution_wiring.py`
  - 測試 MAF 路由分派
  - 測試 Claude 路由分派
  - 測試 Swarm 路由分派
  - 測試 executor 不可用時的 fallback

### S134-5: MCP 工具動態註冊 (2 SP)

**作為** Orchestrator 系統
**我希望** MCP 工具能被動態註冊到 OrchestratorToolRegistry
**以便** Orchestrator Agent 能動態發現和調用 MCP 工具

**技術規格**:
- 新增 `backend/src/integrations/hybrid/orchestrator/mcp_tool_bridge.py`
  - `MCPToolBridge` class: 將 MCP ServerRegistry 中的工具轉換為 OrchestratorToolRegistry 格式
  - `discover_tools()` — 從 `MCPServerRegistry` (from `backend/src/integrations/mcp/registry/server_registry.py`) 掃描可用工具
  - `register_to_orchestrator()` — 將發現的工具批量註冊到 `OrchestratorToolRegistry` (from `backend/src/integrations/hybrid/orchestrator/tools.py`)
  - Lazy loading: 僅在工具首次被調用時建立 MCP 連線
  - 快取機制: 避免重複掃描已註冊的工具
- 修改 `backend/src/integrations/hybrid/orchestrator/bootstrap.py`
  - 在 `build()` 中調用 `MCPToolBridge.register_to_orchestrator()`
- 修改 `backend/src/integrations/hybrid/orchestrator/tools.py`
  - 新增 `register_mcp_tool()` 方法支援動態工具註冊
- 新增 `backend/tests/unit/integrations/hybrid/orchestrator/test_mcp_tool_bridge.py`
  - 測試工具發現
  - 測試工具註冊
  - 測試 lazy loading 行為

## 檔案變更清單

### 新增檔案
| 檔案路徑 | 用途 |
|----------|------|
| `backend/src/integrations/hybrid/orchestrator/bootstrap.py` | OrchestratorBootstrap 工廠類 |
| `backend/src/integrations/hybrid/orchestrator/mcp_tool_bridge.py` | MCP 工具動態註冊橋接器 |
| `backend/tests/unit/integrations/hybrid/orchestrator/test_bootstrap.py` | Bootstrap 單元測試 |
| `backend/tests/unit/integrations/hybrid/orchestrator/test_routing_wiring.py` | RoutingHandler 接線測試 |
| `backend/tests/unit/integrations/hybrid/orchestrator/test_approval_wiring.py` | ApprovalHandler 接線測試 |
| `backend/tests/unit/integrations/hybrid/orchestrator/test_execution_wiring.py` | ExecutionHandler 接線測試 |
| `backend/tests/unit/integrations/hybrid/orchestrator/test_mcp_tool_bridge.py` | MCP 工具橋接測試 |

### 修改檔案
| 檔案路徑 | 修改內容 |
|----------|---------|
| `backend/src/integrations/hybrid/orchestrator/__init__.py` | 匯出 OrchestratorBootstrap, MCPToolBridge |
| `backend/src/integrations/hybrid/orchestrator/handlers/routing.py` | 接受 InputGateway + IntentRouter + FrameworkSelector 注入 |
| `backend/src/integrations/hybrid/orchestrator/handlers/approval.py` | 接受 RiskAssessor + HITLController 注入 |
| `backend/src/integrations/hybrid/orchestrator/handlers/execution.py` | 接受 MAF/Claude/Swarm executor 注入 |
| `backend/src/integrations/hybrid/orchestrator/tools.py` | 新增 register_mcp_tool() 方法 |

## 驗收標準

- [ ] `OrchestratorBootstrap.build()` 回傳完整接線的 `OrchestratorMediator`（7 個 handler 全部非 None）
- [ ] `health_check()` 能驗證所有 handler 已正確接線
- [ ] InputGateway → RoutingHandler → FrameworkSelector 端到端可運行
- [ ] RiskAssessor → ApprovalHandler → HITLController 端到端可運行
- [ ] ExecutionHandler 能根據 framework 類型分派到 MAF / Claude / Swarm
- [ ] MCP 工具能被動態發現並註冊到 OrchestratorToolRegistry
- [ ] MCP 工具 lazy loading 正常運作（首次調用才建立連線）
- [ ] 所有新增程式碼通過 black / isort / flake8 / mypy 檢查
- [ ] 單元測試覆蓋率 >= 80%

## 相關連結

- [Phase 39 計劃](./README.md)
- [Sprint 135 Plan](./sprint-135-plan.md)
- [OrchestratorMediator](../../../../backend/src/integrations/hybrid/orchestrator/mediator.py)
- [Handler 模組](../../../../backend/src/integrations/hybrid/orchestrator/handlers/)

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 12
