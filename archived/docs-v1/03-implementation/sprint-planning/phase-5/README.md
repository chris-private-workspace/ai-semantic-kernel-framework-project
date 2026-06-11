# Phase 5: MVP Core 官方 API 遷移

**Phase 目標**: 把所有 Phase 1 (MVP) 中自行實現的功能內容，都完整地連接回到官方 Agent Framework 的架構中

**創建日期**: 2025-12-07
**預計週期**: 5 個 Sprint (Sprint 26-30)
**總 Story Points**: 約 180 點

---

## Phase 5 背景

### 為什麼需要 Phase 5?

根據 Sprint 25 完成後的完整審計報告 (FINAL-COMPREHENSIVE-AUDIT.md)，發現：

| 審計範圍 | 狀態 | 符合性 |
|----------|------|--------|
| Phase 4 Adapters (integrations/) | ✅ 完全通過 | 100% |
| Phase 2 Features (Sprint 7-12) | ✅ 完全遷移 | 95%+ |
| 遺留代碼 (SK/AutoGen) | ✅ 完全清除 | 100% |
| **Phase 1 MVP Core (domain/)** | 🔴 **嚴重問題** | 0% |
| API Routes Integration | ⚠️ 部分問題 | 60% |

**關鍵問題**: Phase 1 MVP 的核心功能 (Workflow, Checkpoint, Execution) 完全是自行實現的，沒有使用官方 Agent Framework API。

---

## 遷移目標

### 需要遷移的核心組件

| 自行實現 | 檔案位置 | 應使用的官方 API | Sprint |
|----------|----------|------------------|--------|
| `WorkflowDefinition` | `domain/workflows/models.py:163-326` | `agent_framework.workflows.Workflow` | 26 |
| `WorkflowNode` | `domain/workflows/models.py:67-123` | `agent_framework.workflows.Executor` | 26 |
| `WorkflowEdge` | `domain/workflows/models.py:127-160` | `agent_framework.workflows.Edge` | 26 |
| `WorkflowExecutionService` | `domain/workflows/service.py:131-454` | `SequentialOrchestration` | 27 |
| `CheckpointService` (人工審批) | `domain/checkpoints/service.py` | `RequestResponseExecutor` | 28 |
| `ExecutionStateMachine` | `domain/executions/state_machine.py` | `WorkflowStatusEvent` stream | 27 |
| `handoff/routes.py` mock | `api/v1/handoff/routes.py` | `HandoffBuilderAdapter` | 29 |
| API Routes (直接用 domain) | `api/v1/agents/`, `workflows/`, etc. | Adapter 封裝 | 29-30 |

---

## Sprint 規劃概覽

### Sprint 26: Workflow 模型遷移 (36 點)
**目標**: 將 WorkflowDefinition/Node/Edge 遷移到官方 Workflow/Executor/Edge

| Story | 點數 | 描述 |
|-------|------|------|
| S26-1 | 8 | WorkflowNodeAdapter - 實現基於 Executor 的節點適配器 |
| S26-2 | 8 | WorkflowEdgeAdapter - 實現官方 Edge 介面適配器 |
| S26-3 | 10 | WorkflowDefinitionAdapter - 整合 Workflow 建構 |
| S26-4 | 5 | WorkflowContext 適配 - 整合官方 WorkflowContext |
| S26-5 | 5 | 單元測試和驗證 |

### Sprint 27: 執行引擎遷移 (38 點)
**目標**: 將 WorkflowExecutionService 遷移到 SequentialOrchestration

| Story | 點數 | 描述 |
|-------|------|------|
| S27-1 | 10 | SequentialOrchestrationAdapter - 順序執行適配器 |
| S27-2 | 8 | WorkflowStatusEventAdapter - 狀態事件流適配器 |
| S27-3 | 8 | ExecutionStateMachine 重構 - 整合官方事件系統 |
| S27-4 | 7 | ExecutionService 遷移 - 使用新適配器 |
| S27-5 | 5 | 整合測試 |

### Sprint 28: 人工審批遷移 (34 點)
**目標**: 將 CheckpointService 遷移到 RequestResponseExecutor

| Story | 點數 | 描述 |
|-------|------|------|
| S28-1 | 10 | HumanApprovalExecutor - 基於 RequestResponseExecutor |
| S28-2 | 8 | ApprovalRequest/Response 模型 |
| S28-3 | 8 | CheckpointService 重構 - 分離存儲與審批 |
| S28-4 | 5 | 審批工作流整合 |
| S28-5 | 3 | 單元測試 |

### Sprint 29: API Routes 遷移 (38 點)
**目標**: 將 API routes 從直接使用 domain 遷移到使用 Adapter

| Story | 點數 | 描述 |
|-------|------|------|
| S29-1 | 8 | handoff/routes.py 遷移 - 使用 HandoffBuilderAdapter |
| S29-2 | 8 | workflows/routes.py 遷移 - 使用 WorkflowDefinitionAdapter |
| S29-3 | 8 | executions/routes.py 遷移 - 使用執行適配器 |
| S29-4 | 8 | checkpoints/routes.py 遷移 - 使用審批適配器 |
| S29-5 | 6 | API 整合測試 |

### Sprint 30: 整合與驗收 (34 點)
**目標**: 完整整合測試、文檔更新和最終驗收

| Story | 點數 | 描述 |
|-------|------|------|
| S30-1 | 8 | E2E 整合測試 - 完整工作流測試 |
| S30-2 | 8 | 效能測試 - 確保遷移後效能無退化 |
| S30-3 | 6 | 文檔更新 - API 文檔、架構圖更新 |
| S30-4 | 6 | 棄用代碼清理 - 移除不再需要的 domain 代碼 |
| S30-5 | 6 | 最終審計和驗收 |

---

## 總 Story Points

| Sprint | 點數 | 主題 | 狀態 |
|--------|------|------|------|
| Sprint 26 | 36 | Workflow 模型遷移 | ✅ 完成 |
| Sprint 27 | 38 | 執行引擎遷移 | ✅ 完成 |
| Sprint 28 | 40 | 人工審批遷移 | ✅ 完成 |
| Sprint 29 | 35 | API Routes 遷移 | ✅ 完成 |
| Sprint 30 | 34 | 整合與驗收 | ✅ 完成 |
| **總計** | **183** | | **✅ 100%** |

> **Phase 5 已全部完成**: Sprint 26-30 共 183 點，完整 MVP 整合與驗收。

---

## 官方 API 參考

### 核心 Workflows API

```python
from agent_framework.workflows import (
    Workflow,           # 圖結構
    Executor,           # 執行單元基類
    AgentExecutor,      # Agent 執行器
    FunctionExecutor,   # 函數執行器
    Edge,               # 連接邊
    RequestResponseExecutor,  # 人工審批
)

from agent_framework.workflows.orchestrations import (
    SequentialOrchestration,  # 順序編排
    ConcurrentOrchestration,  # 並行編排
    HandoffOrchestration,     # 路由編排
    MagenticOrchestration,    # 複雜編排
)

from agent_framework.workflows.checkpoints import (
    InMemoryCheckpointStore,  # 記憶體檢查點
    CosmosCheckpointStore,    # Cosmos DB 檢查點
)
```

### 關鍵模式參考

**Executor 實現**:
```python
@Executor.register
class MyExecutor(Executor[InputModel, OutputModel]):
    async def execute(self, input: InputModel, context) -> OutputModel:
        # 業務邏輯
        return OutputModel(...)
```

**Human-in-the-Loop**:
```python
@Executor.register
class HumanApproval(RequestResponseExecutor[ApprovalRequest, ApprovalResponse]):
    pass

# 工作流暫停等待人工回應
await workflow.respond(
    executor_name="HumanApproval",
    response=ApprovalResponse(approved=True, ...)
)
```

---

## 成功標準

### 必須達成
1. ✅ 所有 Phase 1 MVP 核心功能都使用官方 API
2. ✅ 驗證腳本 `verify_official_api_usage.py` 通過率 100%
3. ✅ 整體 API 符合性 >= 95%
4. ✅ 測試覆蓋率 >= 80%
5. ✅ 無效能退化 (效能測試通過)

### 應該達成
- 文檔完整更新
- 棄用代碼完全清理
- E2E 測試覆蓋完整工作流

---

## 相關文檔

- [Sprint 25 最終審計報告](../../sprint-execution/sprint-25/FINAL-COMPREHENSIVE-AUDIT.md)
- [Phase 5 完整重構計劃](./PHASE5-MVP-REFACTORING-PLAN.md)
- [Workflows API 參考](../../../../.claude/skills/microsoft-agent-framework/references/workflows-api.md)
- [Sprint 工作流程檢查點](../phase-3/SPRINT-WORKFLOW-CHECKLIST.md)

---

**Phase 5 規劃人**: Claude Code
**規劃日期**: 2025-12-07
**完成日期**: 2025-12-07
**上次更新**: 2025-12-08
