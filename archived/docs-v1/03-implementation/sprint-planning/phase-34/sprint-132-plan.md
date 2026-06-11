# Sprint 132: HybridOrchestratorV2 重構（Mediator Pattern）

## 概述

Sprint 132 對 HybridOrchestratorV2 進行架構重構，將 God Object（1,254 LOC、11 個依賴）重構為 Mediator Pattern，消除最大的架構瓶頸。

## 目標

1. 將 HybridOrchestratorV2 拆分為 Mediator + 獨立 Handler
2. 消除 God Object（1,254 LOC → 每個 Handler < 200 LOC）
3. 解耦 11 個依賴為鬆耦合的事件驅動
4. 保持所有現有 API 向後相容

## Story Points: 30 點

## 前置條件

- ⬜ Sprint 128-131 完成
- ⬜ 80% 測試覆蓋率（確保重構安全網）

## 任務分解

### Story 132-1: Mediator 架構設計 (1 天, P3)

**現狀分析**:
```
HybridOrchestratorV2 (1,254 LOC)
  ├── 知曉 BusinessIntentRouter
  ├── 知曉 GuidedDialogEngine
  ├── 知曉 HITLController
  ├── 知曉 RiskAssessor
  ├── 知曉 MAF Builders (9 個)
  ├── 知曉 Claude SDK
  ├── 知曉 Swarm
  ├── 知曉 ContextSynchronizer
  ├── 知曉 InputGateway
  ├── 知曉 Metrics
  └── 知曉 Audit Logger
```

**目標架構**:
```
OrchestratorMediator (<300 LOC)
  ├── RoutingHandler      — 路由協調
  ├── DialogHandler       — 對話管理
  ├── ApprovalHandler     — HITL 審批
  ├── ExecutionHandler    — 框架執行（MAF/Claude/Swarm）
  ├── ContextHandler      — 上下文同步
  └── ObservabilityHandler — 指標/審計
```

### Story 132-2: Mediator 實現 (3 天, P3)

**交付物**:
```
src/integrations/hybrid/orchestrator/
├── __init__.py
├── mediator.py           # OrchestratorMediator（事件分發）
├── handlers/
│   ├── __init__.py
│   ├── routing.py        # RoutingHandler
│   ├── dialog.py         # DialogHandler
│   ├── approval.py       # ApprovalHandler
│   ├── execution.py      # ExecutionHandler
│   ├── context.py        # ContextHandler
│   └── observability.py  # ObservabilityHandler
├── events.py             # 內部事件定義
└── contracts.py          # Handler 介面
```

**Mediator 核心邏輯**:
```python
class OrchestratorMediator:
    def __init__(self, handlers: dict[str, Handler]):
        self._handlers = handlers

    async def execute(self, request: OrchestratorRequest) -> OrchestratorResponse:
        # 1. Routing
        routing = await self._handlers["routing"].handle(request)
        # 2. Dialog (if needed)
        if routing.needs_dialog:
            dialog = await self._handlers["dialog"].handle(request, routing)
        # 3. Approval (if needed)
        if routing.needs_approval:
            approval = await self._handlers["approval"].handle(request, routing)
        # 4. Execution
        result = await self._handlers["execution"].handle(request, routing)
        # 5. Observability
        await self._handlers["observability"].record(request, result)
        return result
```

### Story 132-3: 遷移 + 向後相容 (2 天, P3)

**遷移策略**:
1. 新建 Mediator 架構（不修改現有代碼）
2. HybridOrchestratorV2 委託到 Mediator
3. 所有測試通過後，逐步替換調用點
4. 標記 HybridOrchestratorV2 為 deprecated

### Story 132-4: 測試 (1 天, P3)

**測試範圍**:

| 測試 | 範圍 |
|------|------|
| `test_mediator.py` | Mediator 事件分發 |
| `test_routing_handler.py` | 路由處理 |
| `test_execution_handler.py` | 框架執行 |
| `test_backward_compat.py` | 向後相容性 |

## 風險

| 風險 | 影響 | 緩解 |
|------|------|------|
| 重構引入 regression | 現有功能中斷 | 80% 測試覆蓋率作為安全網 |
| Handler 間耦合 | 未完全解耦 | 嚴格的事件驅動設計 |
| 效能下降 | 額外間接層開銷 | 基準測試比對 |

## 依賴

- 改善提案 Phase D P3: HybridOrchestratorV2 重構
- Sprint 131 測試覆蓋率 80%（重構安全網）
