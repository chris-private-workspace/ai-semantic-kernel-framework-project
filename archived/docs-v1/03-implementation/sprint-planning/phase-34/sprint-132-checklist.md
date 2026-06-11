# Sprint 132 Checklist: HybridOrchestratorV2 重構（Mediator Pattern）

## 開發任務

### Story 132-1: Mediator 架構設計
- [ ] 分析 HybridOrchestratorV2 現有職責
  - [ ] 列出所有 11 個依賴
  - [ ] 識別方法群組（routing, dialog, approval, execution）
  - [ ] 繪製依賴圖
- [ ] 設計 Handler 介面
  - [ ] Handler 抽象基類
  - [ ] 事件類型定義
  - [ ] Mediator 核心介面
- [ ] 設計遷移路徑
  - [ ] 向後相容策略
  - [ ] 階段性替換計劃

### Story 132-2: Mediator 實現
- [ ] 建立 `src/integrations/hybrid/orchestrator/` 目錄
- [ ] 實現 `contracts.py` — Handler 介面
  - [ ] Handler 抽象基類
  - [ ] HandlerResult 類型
- [ ] 實現 `events.py` — 內部事件定義
  - [ ] RoutingEvent
  - [ ] DialogEvent
  - [ ] ApprovalEvent
  - [ ] ExecutionEvent
- [ ] 實現 `mediator.py` — OrchestratorMediator
  - [ ] Handler 註冊機制
  - [ ] 事件分發邏輯
  - [ ] 執行流程編排
- [ ] 實現 `handlers/routing.py`
  - [ ] BusinessIntentRouter 封裝
  - [ ] 路由結果處理
- [ ] 實現 `handlers/dialog.py`
  - [ ] GuidedDialogEngine 封裝
  - [ ] 對話狀態管理
- [ ] 實現 `handlers/approval.py`
  - [ ] HITLController 封裝
  - [ ] 審批流程處理
- [ ] 實現 `handlers/execution.py`
  - [ ] MAF/Claude/Swarm 框架選擇
  - [ ] 執行結果處理
- [ ] 實現 `handlers/context.py`
  - [ ] ContextSynchronizer 封裝
- [ ] 實現 `handlers/observability.py`
  - [ ] Metrics + Audit 封裝

### Story 132-3: 遷移 + 向後相容
- [ ] HybridOrchestratorV2 委託到 Mediator
  - [ ] `execute_with_routing()` 委託
  - [ ] 所有公開方法委託
- [ ] 標記 HybridOrchestratorV2 deprecated
  - [ ] 添加 DeprecationWarning
  - [ ] 更新文件
- [ ] 更新 API 路由調用點
  - [ ] 使用新的 Mediator 介面
  - [ ] 確認所有路由正常

### Story 132-4: 測試
- [ ] `tests/unit/integrations/hybrid/test_mediator.py`
- [ ] `tests/unit/integrations/hybrid/test_routing_handler.py`
- [ ] `tests/unit/integrations/hybrid/test_execution_handler.py`
- [ ] `tests/unit/integrations/hybrid/test_backward_compat.py`
- [ ] 回歸測試全部通過

## 驗證標準

- [ ] Mediator < 300 LOC
- [ ] 每個 Handler < 200 LOC
- [ ] HybridOrchestratorV2 API 完全向後相容
- [ ] 效能無顯著下降（< 5% overhead）
- [ ] 所有新測試通過
- [ ] 回歸測試無失敗
