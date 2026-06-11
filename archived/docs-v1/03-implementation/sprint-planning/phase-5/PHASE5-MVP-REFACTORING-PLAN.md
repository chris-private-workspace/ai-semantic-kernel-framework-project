# Phase 5 MVP 核心重構計劃

**創建日期**: 2025-12-07
**目標**: 把所有 Phase 1 (MVP) 中自行實現的功能內容，都完整地連接回到官方 Agent Framework 的架構中
**總 Story Points**: 180 點
**Sprint 範圍**: Sprint 26-30

---

## 1. 問題分析

### 1.1 審計發現摘要

根據 Sprint 25 完成後的 6-Agent 並行審計結果：

| 審計範圍 | 符合性 | 說明 |
|----------|--------|------|
| Phase 4 Adapters | 100% | 5/5 核心 Builder 正確使用官方 API |
| Phase 2 Features | 95% | 已完全遷移到 Adapter |
| Legacy Code | 100% | SK/AutoGen 完全清除，~8,691 行已刪除 |
| **Phase 1 MVP Core** | **0%** | 完全自行實現，未使用官方 API |
| API Routes | 60% | 部分使用 Adapter，部分直接用 domain |

### 1.2 具體問題清單

#### 🔴 高優先級 (必須修正)

| # | 問題 | 檔案位置 | 影響 |
|---|------|----------|------|
| 1 | `WorkflowDefinition` 自行實現 | `domain/workflows/models.py:163-326` | 工作流圖結構未使用官方 API |
| 2 | `WorkflowNode` 自行實現 | `domain/workflows/models.py:67-123` | 應使用 `Executor` |
| 3 | `WorkflowEdge` 自行實現 | `domain/workflows/models.py:126-160` | 應使用 `Edge` |
| 4 | `WorkflowExecutionService._execute_sequential` | `domain/workflows/service.py:235-314` | 應使用 `SequentialOrchestration` |
| 5 | `CheckpointService` 人工審批 | `domain/checkpoints/service.py` | 應使用 `RequestResponseExecutor` |
| 6 | `handoff/routes.py` 純 mock | `api/v1/handoff/routes.py` | 無 HandoffBuilderAdapter 整合 |

#### 🟡 中優先級 (應該修正)

| # | 問題 | 檔案位置 | 影響 |
|---|------|----------|------|
| 7 | API Routes 直接用 domain | `api/v1/agents/`, `workflows/`, `executions/` | 應通過 Adapter 封裝 |
| 8 | `ExecutionStateMachine` 自行實現 | `domain/executions/state_machine.py` | 可考慮使用 `WorkflowStatusEvent` |
| 9 | `WorkflowContext` 自行實現 | `domain/workflows/models.py:329-376` | 可考慮使用官方 context |

---

## 2. 遷移策略

### 2.1 Adapter 模式延續

Phase 5 延續 Phase 3-4 的 Adapter 模式策略：

```
┌─────────────────────────────────────────────────────────────────┐
│                    API Routes Layer                              │
│   (api/v1/agents, workflows, executions, checkpoints, ...)      │
├─────────────────────────────────────────────────────────────────┤
│                         ↓                                        │
│    ┌──────────────────────────────────────────────────────────┐ │
│    │              Adapter Layer (Phase 5 新增)                 │ │
│    │         integrations/agent_framework/core/                │ │
│    │                                                            │ │
│    │  ┌─────────────────┐  ┌─────────────────┐                │ │
│    │  │ WorkflowNode    │  │ Workflow        │                │ │
│    │  │ Adapter         │  │ Definition      │                │ │
│    │  │                 │  │ Adapter         │                │ │
│    │  └─────────────────┘  └─────────────────┘                │ │
│    │                                                            │ │
│    │  ┌─────────────────┐  ┌─────────────────┐                │ │
│    │  │ Execution       │  │ HumanApproval   │                │ │
│    │  │ Adapter         │  │ Executor        │                │ │
│    │  └─────────────────┘  └─────────────────┘                │ │
│    └──────────────────────────────────────────────────────────┘ │
│                         ↓                                        │
│    ┌──────────────────────────────────────────────────────────┐ │
│    │              Official Agent Framework API                  │ │
│    │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │ │
│    │  │ Workflow    │ │ Executor    │ │ RequestResponse     │ │ │
│    │  │             │ │             │ │ Executor            │ │ │
│    │  └─────────────┘ └─────────────┘ └─────────────────────┘ │ │
│    │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │ │
│    │  │ Edge        │ │ Sequential  │ │ WorkflowStatus      │ │ │
│    │  │             │ │ Orchestr.   │ │ Event               │ │ │
│    │  └─────────────┘ └─────────────┘ └─────────────────────┘ │ │
│    └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 向後兼容策略

為確保現有功能不中斷，採用以下策略：

1. **新 Adapter 封裝官方 API**：創建新的 Adapter 類
2. **Domain 層添加 deprecation 警告**：標記將被替換的類
3. **漸進式遷移**：逐步將 API routes 切換到 Adapter
4. **完整測試覆蓋**：確保遷移前後行為一致

---

## 3. Sprint 詳細規劃

### Sprint 26: Workflow 模型遷移 (36 點)

**週期**: 2 週
**目標**: 將 WorkflowDefinition/Node/Edge 遷移到官方 Workflow/Executor/Edge

#### 架構變更

```python
# 目前 (WRONG)
@dataclass
class WorkflowNode:
    id: str
    type: NodeType
    agent_id: Optional[UUID] = None
    config: Dict[str, Any] = field(default_factory=dict)

# 目標 (CORRECT)
from agent_framework.workflows import Executor

@Executor.register
class WorkflowNodeExecutor(Executor[NodeInput, NodeOutput]):
    async def execute(self, input: NodeInput, context) -> NodeOutput:
        # 執行邏輯
        return NodeOutput(...)
```

#### User Stories

| Story | 點數 | 描述 | 驗收標準 |
|-------|------|------|----------|
| S26-1 | 8 | WorkflowNodeAdapter | 可將 WorkflowNode 轉換為 Executor |
| S26-2 | 8 | WorkflowEdgeAdapter | 可將 WorkflowEdge 轉換為 Edge |
| S26-3 | 10 | WorkflowDefinitionAdapter | 可構建完整 Workflow |
| S26-4 | 5 | WorkflowContext 適配 | 整合官方 context |
| S26-5 | 5 | 單元測試 | 覆蓋率 >= 80% |

---

### Sprint 27: 執行引擎遷移 (38 點)

**週期**: 2 週
**目標**: 將 WorkflowExecutionService 遷移到 SequentialOrchestration

#### 架構變更

```python
# 目前 (WRONG)
class WorkflowExecutionService:
    async def _execute_sequential(self, nodes: List[WorkflowNode]) -> ExecutionResult:
        for node in nodes:
            result = await self._execute_node(node)
        return result

# 目標 (CORRECT)
from agent_framework.workflows.orchestrations import SequentialOrchestration

class ExecutionAdapter:
    def __init__(self):
        self._orchestration = SequentialOrchestration(
            agents=[...],
            name="workflow-execution"
        )

    async def execute(self, workflow: Workflow) -> WorkflowRunResult:
        return await self._orchestration.run(input_data)
```

#### User Stories

| Story | 點數 | 描述 | 驗收標準 |
|-------|------|------|----------|
| S27-1 | 10 | SequentialOrchestrationAdapter | 可執行順序工作流 |
| S27-2 | 8 | WorkflowStatusEventAdapter | 可處理狀態事件流 |
| S27-3 | 8 | ExecutionStateMachine 重構 | 整合官方事件系統 |
| S27-4 | 7 | ExecutionService 遷移 | 使用新適配器 |
| S27-5 | 5 | 整合測試 | E2E 測試通過 |

---

### Sprint 28: 人工審批遷移 (34 點)

**週期**: 2 週
**目標**: 將 CheckpointService 遷移到 RequestResponseExecutor

#### 架構變更

```python
# 目前 (WRONG) - 混合了存儲和審批
class CheckpointService:
    async def create_checkpoint(self, execution_id, node_id, payload):
        # 創建檢查點 (存儲概念)
        pass

    async def approve_checkpoint(self, checkpoint_id, user_id):
        # 審批檢查點 (人工審批概念)
        pass

# 目標 (CORRECT) - 分離關注點
from agent_framework.workflows import RequestResponseExecutor

# 1. 人工審批 - 使用 RequestResponseExecutor
class ApprovalRequest(BaseModel):
    action: str
    risk_level: str
    details: str

class ApprovalResponse(BaseModel):
    approved: bool
    reason: str
    approver: str

@Executor.register
class HumanApprovalExecutor(RequestResponseExecutor[ApprovalRequest, ApprovalResponse]):
    """工作流在此暫停等待人工回應"""
    pass

# 2. 狀態存儲 - 使用 CheckpointStorage
from agent_framework.workflows.checkpoints import InMemoryCheckpointStore
checkpoint_store = InMemoryCheckpointStore()
```

#### User Stories

| Story | 點數 | 描述 | 驗收標準 |
|-------|------|------|----------|
| S28-1 | 10 | HumanApprovalExecutor | 基於 RequestResponseExecutor |
| S28-2 | 8 | ApprovalRequest/Response 模型 | 符合官方模式 |
| S28-3 | 8 | CheckpointService 重構 | 分離存儲與審批 |
| S28-4 | 5 | 審批工作流整合 | 可暫停/恢復工作流 |
| S28-5 | 3 | 單元測試 | 覆蓋率 >= 80% |

---

### Sprint 29: API Routes 遷移 (38 點)

**週期**: 2 週
**目標**: 將 API routes 從直接使用 domain 遷移到使用 Adapter

#### 變更範圍

| Route 模組 | 目前狀態 | 目標狀態 |
|-----------|----------|----------|
| `/handoff` | 純 mock | HandoffBuilderAdapter |
| `/workflows` | 直接用 domain | WorkflowDefinitionAdapter |
| `/executions` | 直接用 domain | ExecutionAdapter |
| `/checkpoints` | 直接用 domain | HumanApprovalExecutor |
| `/agents` | 部分用 domain | AgentAdapter (可選) |

#### User Stories

| Story | 點數 | 描述 | 驗收標準 |
|-------|------|------|----------|
| S29-1 | 8 | handoff/routes.py 遷移 | 使用 HandoffBuilderAdapter |
| S29-2 | 8 | workflows/routes.py 遷移 | 使用 WorkflowDefinitionAdapter |
| S29-3 | 8 | executions/routes.py 遷移 | 使用執行適配器 |
| S29-4 | 8 | checkpoints/routes.py 遷移 | 使用審批適配器 |
| S29-5 | 6 | API 整合測試 | 所有 API 端點測試通過 |

---

### Sprint 30: 整合與驗收 (34 點)

**週期**: 2 週
**目標**: 完整整合測試、文檔更新和最終驗收

#### User Stories

| Story | 點數 | 描述 | 驗收標準 |
|-------|------|------|----------|
| S30-1 | 8 | E2E 整合測試 | 完整工作流測試通過 |
| S30-2 | 8 | 效能測試 | 無效能退化 |
| S30-3 | 6 | 文檔更新 | API 文檔完整 |
| S30-4 | 6 | 棄用代碼清理 | 無遺留自行實現代碼 |
| S30-5 | 6 | 最終審計 | 符合性 >= 95% |

---

## 4. 檔案結構規劃

### 4.1 新增 Adapter 目錄

```
backend/src/integrations/agent_framework/
├── builders/              # 現有 (Phase 4)
│   ├── concurrent.py
│   ├── groupchat.py
│   ├── handoff.py
│   ├── magentic.py
│   └── ...
│
├── core/                  # 新增 (Phase 5)
│   ├── __init__.py
│   ├── workflow.py        # WorkflowDefinitionAdapter
│   ├── executor.py        # WorkflowNodeExecutor
│   ├── edge.py            # WorkflowEdgeAdapter
│   ├── execution.py       # ExecutionAdapter
│   └── approval.py        # HumanApprovalExecutor
│
├── multiturn/             # 現有
└── memory/                # 現有
```

### 4.2 Sprint 執行目錄

```
docs/03-implementation/sprint-execution/
├── sprint-26/
│   ├── progress.md
│   ├── decisions.md
│   └── README.md
├── sprint-27/
├── sprint-28/
├── sprint-29/
└── sprint-30/
```

---

## 5. 風險管理

### 5.1 技術風險

| 風險 | 機率 | 影響 | 緩解措施 |
|------|------|------|----------|
| API 不兼容 | 中 | 高 | 查閱官方源碼，必要時調整 |
| 效能退化 | 低 | 高 | 效能測試，漸進式遷移 |
| 向後兼容破壞 | 中 | 中 | 完整測試覆蓋，deprecation 警告 |
| 複雜度超預估 | 中 | 中 | 每個 Sprint 中期檢查 |

### 5.2 緩解策略

1. **每個 Story 完成後立即驗證**
2. **Sprint 中期進行對齊檢查**
3. **保持現有 domain 代碼直到完全遷移**
4. **使用 feature flag 控制新舊實現切換**

---

## 6. 驗收標準

### 6.1 Phase 5 完成標準

| 標準 | 描述 | 驗證方法 |
|------|------|----------|
| API 符合性 | >= 95% 使用官方 API | verify_official_api_usage.py |
| 測試覆蓋率 | >= 80% | pytest --cov |
| 效能無退化 | 回應時間 <= 現有實現 | 效能測試 |
| E2E 測試 | 所有工作流場景通過 | 整合測試套件 |
| 文檔完整 | API 文檔、架構圖更新 | 人工審查 |

### 6.2 每個 Sprint 的完成標準

1. ✅ 所有 User Stories 完成
2. ✅ 單元測試通過
3. ✅ Checklist 100% 完成
4. ✅ progress.md 更新
5. ✅ decisions.md 記錄

---

## 7. 相關參考

### 7.1 官方 API 文檔
- [Workflows API Reference](../../../../.claude/skills/microsoft-agent-framework/references/workflows-api.md)
- [Builders API Reference](../../../../.claude/skills/microsoft-agent-framework/references/builders-api.md)

### 7.2 項目文檔
- [Sprint 25 最終審計報告](../../sprint-execution/sprint-25/FINAL-COMPREHENSIVE-AUDIT.md)
- [Phase 3 重構計劃](../phase-3/PHASE3-REFACTOR-PLAN.md)
- [Sprint 工作流程檢查點](../phase-3/SPRINT-WORKFLOW-CHECKLIST.md)

### 7.3 源碼參考
- `reference/agent-framework/python/packages/core/agent_framework/workflows/`
- `reference/agent-framework/python/packages/core/agent_framework/`

---

**規劃人**: Claude Code
**規劃日期**: 2025-12-07
**狀態**: 待執行
