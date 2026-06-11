# Sprint 116 Checklist: 架構加固

## 開發任務

### Story 116-1: Swarm 整合到 execute_with_routing()
- [ ] 創建 `backend/src/integrations/hybrid/swarm_mode.py`
  - [ ] 定義 `ExecutionMode` enum（SINGLE_AGENT, HANDOFF, SWARM_MODE）
  - [ ] 實現 `SwarmModeHandler` 類
  - [ ] 實現 `should_use_swarm()` — 基於 intent/context 判斷
  - [ ] 實現 `execute_swarm()` — Swarm 執行邏輯
  - [ ] 實現 Worker 分配邏輯
  - [ ] 實現結果彙整邏輯
- [ ] 修改 `HybridOrchestratorV2.execute_with_routing()`
  - [ ] 在 intent 解析後判斷 ExecutionMode
  - [ ] 新增 SWARM_MODE 分支
  - [ ] 注入 `SwarmModeHandler`
  - [ ] 確保 SINGLE_AGENT 和 HANDOFF 不受影響
- [ ] 修改 `backend/src/integrations/swarm/swarm_integration.py`
  - [ ] 確保 SwarmIntegration 可被 SwarmModeHandler 使用
  - [ ] 添加必要的介面適配
- [ ] 新增 Feature Flag
  - [ ] 環境變量 `SWARM_MODE_ENABLED=false`（預設關閉）
  - [ ] 更新 `.env.example`
- [ ] 創建 `backend/tests/unit/hybrid/test_swarm_mode.py`
  - [ ] 測試 `should_use_swarm()` 各種場景
  - [ ] 測試 `execute_swarm()` 正常流程
  - [ ] 測試 `execute_swarm()` 錯誤處理
  - [ ] 測試 ExecutionMode 選擇邏輯
- [ ] 創建 `backend/tests/integration/hybrid/test_swarm_routing.py`
  - [ ] 測試 execute_with_routing() + SWARM_MODE 完整流程
  - [ ] 測試 Feature Flag 關閉時不觸發 Swarm
  - [ ] 回歸測試 SINGLE_AGENT 模式
  - [ ] 回歸測試 HANDOFF 模式

### Story 116-2: Layer 4 拆分 — L4a + L4b
- [ ] 創建共享契約
  - [ ] 創建 `backend/src/integrations/orchestration/contracts.py`
  - [ ] 定義 `InputEvent` ABC
  - [ ] 定義 `RoutingRequest` dataclass
  - [ ] 定義 `RoutingResult` dataclass
  - [ ] 定義 `InputGatewayProtocol`
  - [ ] 定義 `RouterProtocol`
- [ ] 重組 L4a: Input Processing
  - [ ] 確認 `orchestration/input/` 目錄結構正確
  - [ ] 創建 `input/contracts.py` — InputGateway 介面
  - [ ] 確認 `servicenow_webhook.py` 在正確位置（Sprint 114）
  - [ ] 確認 `ritm_intent_mapper.py` 在正確位置（Sprint 114）
  - [ ] 移動/創建 `http_input.py` — HTTP API 輸入適配器
  - [ ] 移動/創建 `sse_input.py` — SSE 輸入適配器
  - [ ] 更新 `input/__init__.py` 導出
- [ ] 重組 L4b: Decision Engine
  - [ ] 確認 `orchestration/routing/` 目錄結構正確
  - [ ] 創建 `routing/contracts.py` — Router 介面
  - [ ] 確認 PatternMatcher 在正確位置
  - [ ] 確認 BusinessIntentRouter 在正確位置
  - [ ] 確認 SemanticRouter 子模組在正確位置
  - [ ] 更新 `routing/__init__.py` 導出
- [ ] 更新 import 路徑
  - [ ] 掃描所有 `from orchestration.` import
  - [ ] 更新受影響的 import 語句
  - [ ] 保留舊 import 路徑 re-export（向後兼容過渡）
  - [ ] 標記 deprecated import 路徑
- [ ] 創建 `backend/tests/unit/orchestration/test_layer_contracts.py`
  - [ ] 測試 InputEvent → RoutingRequest 轉換
  - [ ] 測試 RoutingRequest 各欄位
  - [ ] 測試 RoutingResult 各欄位
  - [ ] 測試 Protocol 合規性
- [ ] 回歸測試
  - [ ] 執行現有 orchestration 測試套件
  - [ ] 確認無 import 錯誤
  - [ ] 確認功能正確性

### Story 116-3: L5-L6 循環依賴修復
- [ ] 創建 `backend/src/integrations/shared/` 目錄
- [ ] 創建 `backend/src/integrations/shared/__init__.py`
- [ ] 創建 `backend/src/integrations/shared/protocols.py`
  - [ ] 定義 `ToolCallbackProtocol`
    - [ ] `on_tool_call()` method
    - [ ] `on_tool_result()` method
  - [ ] 定義 `ExecutionEngineProtocol`
    - [ ] `execute()` method
  - [ ] 定義 `OrchestrationContextProtocol`（如需要）
- [ ] 修改 L5 (orchestration) 文件
  - [ ] 移除對 L6 的直接 import
  - [ ] 改為 import `shared/protocols`
  - [ ] 使用 Dependency Injection 注入執行引擎
- [ ] 修改 L6 (claude_sdk / agent_framework) 文件
  - [ ] 移除對 L5 的直接 import
  - [ ] 實現 `ToolCallbackProtocol`
  - [ ] 使用 Dependency Injection 接收回調
- [ ] 驗證循環依賴消除
  - [ ] `python -c "import orchestration"` 不報錯
  - [ ] `python -c "import claude_sdk"` 不報錯
  - [ ] 交叉 import 不報錯
- [ ] 創建 `backend/tests/unit/shared/test_protocols.py`
  - [ ] 測試 ToolCallbackProtocol 結構合規
  - [ ] 測試 ExecutionEngineProtocol 結構合規
  - [ ] 測試現有實現符合 Protocol

## 品質檢查

### 代碼品質
- [ ] 類型提示完整（Protocol 使用 typing.Protocol）
- [ ] Docstrings 完整
- [ ] 遵循專案代碼風格
- [ ] 模組導出正確
- [ ] 無循環 import（所有模組可獨立載入）

### 測試
- [ ] 單元測試創建且通過
- [ ] 整合測試創建且通過
- [ ] **回歸測試通過**（重點！架構重構必須確保不破壞現有功能）
- [ ] 測試覆蓋率 > 85%

### 架構
- [ ] 依賴方向正確（上層 → 下層，無反向）
- [ ] Protocol 介面定義清晰
- [ ] 向後兼容（舊 import 路徑有 re-export）
- [ ] Feature Flag 控制新功能

## 驗收標準

- [ ] Swarm 可通過 `execute_with_routing()` 觸發（Feature Flag 開啟時）
- [ ] 現有 SINGLE_AGENT 和 HANDOFF 模式不受影響
- [ ] Layer 4 拆分為 L4a（Input）+ L4b（Decision）
- [ ] L5-L6 循環依賴消除
- [ ] 所有現有測試通過（回歸無破壞）
- [ ] 架構文檔更新

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 45
**開始日期**: TBD
