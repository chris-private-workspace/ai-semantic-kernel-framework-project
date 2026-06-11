# Sprint 29: API Routes 遷移

**Sprint 目標**: 將 API routes 從直接使用 domain 遷移到使用 Adapter
**週期**: 2 週
**Story Points**: 38 點
**Phase 5 功能**: P5-F4 (API Routes 遷移)

---

## Sprint 概覽

### 目標
1. 遷移 handoff/routes.py (純 mock → HandoffBuilderAdapter)
2. 遷移 workflows/routes.py (使用 WorkflowDefinitionAdapter)
3. 遷移 executions/routes.py (使用 ExecutionAdapter)
4. 遷移 checkpoints/routes.py (使用 HumanApprovalExecutor)
5. 完整 API 整合測試

### 成功標準
- [ ] 所有 API routes 使用適配器層
- [ ] 無直接 domain 層 import (Phase 2-5 功能)
- [ ] API 行為無變化
- [ ] 所有現有測試通過

---

## 問題分析

### 目前狀態

根據審計報告，API routes 的使用狀況：

| Route 模組 | 目前狀態 | 問題 |
|-----------|----------|------|
| `/groupchat` | ✅ 使用 Adapter | 還有 deprecated domain imports |
| `/nested` | ✅ 使用 Adapter | 還有 deprecated domain imports |
| `/planning` | ✅ 使用 Adapter | Lines 18-61 用 deprecated classes |
| `/concurrent` | ⚠️ 部分 | 混合使用 adapter + domain |
| `/handoff` | 🔴 純 mock | **完全沒有用 HandoffBuilderAdapter** |
| `/agents` | ❌ 直接用 domain | 需要 AgentAdapter 封裝 |
| `/workflows` | ❌ 直接用 domain | 需要 WorkflowDefinitionAdapter |
| `/executions` | ❌ 直接用 domain | 需要 ExecutionAdapter |
| `/checkpoints` | ❌ 直接用 domain | 需要 HumanApprovalExecutor |

### 優先順序

1. **高優先級**: handoff/routes.py (完全是 mock)
2. **高優先級**: workflows/routes.py (核心功能)
3. **高優先級**: executions/routes.py (核心功能)
4. **中優先級**: checkpoints/routes.py (審批功能)
5. **低優先級**: 清理 deprecated imports

---

## User Stories

### S29-1: handoff/routes.py 遷移 (8 點)

**描述**: 將 handoff API 從純 mock 遷移到使用 HandoffBuilderAdapter。

**目前問題**:

```python
# api/v1/handoff/routes.py - 完全是 in-memory mock
_handoffs: Dict[UUID, Dict[str, Any]] = {}
_agent_capabilities: Dict[UUID, List[Dict[str, Any]]] = {}
_agent_availability: Dict[UUID, Dict[str, Any]] = {}

@router.post("/initiate")
async def initiate_handoff(...):
    # 純 mock 實現，沒有使用 HandoffBuilderAdapter
    handoff_id = uuid4()
    _handoffs[handoff_id] = {...}
    return {"handoff_id": handoff_id}
```

**目標實現**:

```python
# api/v1/handoff/routes.py - 使用 HandoffBuilderAdapter
from src.integrations.agent_framework.builders import HandoffBuilderAdapter

@router.post("/initiate")
async def initiate_handoff(
    request: HandoffInitiateRequest,
    adapter: HandoffBuilderAdapter = Depends(get_handoff_adapter)
):
    """啟動 Agent 交接"""
    handoff = await adapter.initiate_handoff(
        source_agent_id=request.source_agent_id,
        target_agent_id=request.target_agent_id,
        context=request.context
    )
    return HandoffResponse(
        handoff_id=handoff.id,
        status=handoff.status,
        message="Handoff initiated"
    )
```

**驗收標準**:
- [ ] 移除所有 in-memory mock
- [ ] 使用 HandoffBuilderAdapter
- [ ] 所有端點功能正常
- [ ] API 行為不變

**檔案**:
- `backend/src/api/v1/handoff/routes.py` (重寫)
- `backend/tests/integration/test_handoff_api.py`

---

### S29-2: workflows/routes.py 遷移 (8 點)

**描述**: 將 workflows API 遷移到使用 WorkflowDefinitionAdapter。

**目前問題**:

```python
# api/v1/workflows/routes.py - 直接使用 domain
from src.domain.workflows.service import WorkflowService
from src.domain.workflows.models import WorkflowDefinition, WorkflowNode

@router.post("/")
async def create_workflow(
    workflow: WorkflowCreateRequest,
    service: WorkflowService = Depends(get_workflow_service)
):
    # 直接使用 domain service
    result = await service.create(workflow.dict())
    return result
```

**目標實現**:

```python
# api/v1/workflows/routes.py - 使用 WorkflowDefinitionAdapter
from src.integrations.agent_framework.core import WorkflowDefinitionAdapter

@router.post("/")
async def create_workflow(
    workflow: WorkflowCreateRequest,
    adapter: WorkflowDefinitionAdapter = Depends(get_workflow_adapter)
):
    """創建工作流"""
    # 使用適配器創建
    result = await adapter.create_from_request(workflow)
    return WorkflowResponse(
        id=result.id,
        name=result.name,
        status="created"
    )

@router.post("/{workflow_id}/run")
async def run_workflow(
    workflow_id: UUID,
    input_data: WorkflowRunRequest,
    adapter: WorkflowDefinitionAdapter = Depends(get_workflow_adapter)
):
    """執行工作流"""
    result = await adapter.run(workflow_id, input_data.dict())
    return WorkflowRunResponse(
        execution_id=result.execution_id,
        status=result.status
    )
```

**驗收標準**:
- [ ] 使用 WorkflowDefinitionAdapter
- [ ] 創建、查詢、執行功能正常
- [ ] API 行為不變

**檔案**:
- `backend/src/api/v1/workflows/routes.py` (修改)
- `backend/tests/integration/test_workflows_api.py`

---

### S29-3: executions/routes.py 遷移 (8 點)

**描述**: 將 executions API 遷移到使用 ExecutionAdapter。

**目前問題**:

```python
# api/v1/executions/routes.py - 直接使用 domain
from src.domain.executions.service import ExecutionService
from src.domain.executions.state_machine import ExecutionStateMachine

@router.get("/{execution_id}")
async def get_execution(
    execution_id: UUID,
    service: ExecutionService = Depends(get_execution_service)
):
    # 直接使用 domain service
    execution = await service.get(execution_id)
    return execution
```

**目標實現**:

```python
# api/v1/executions/routes.py - 使用 ExecutionAdapter
from src.integrations.agent_framework.core import ExecutionAdapter

@router.get("/{execution_id}")
async def get_execution(
    execution_id: UUID,
    adapter: ExecutionAdapter = Depends(get_execution_adapter)
):
    """獲取執行狀態"""
    execution = await adapter.get_execution(execution_id)
    return ExecutionResponse(
        id=execution.id,
        status=execution.status,
        result=execution.result
    )

@router.get("/{execution_id}/events")
async def get_execution_events(
    execution_id: UUID,
    adapter: ExecutionAdapter = Depends(get_execution_adapter)
):
    """獲取執行事件流"""
    events = await adapter.get_events(execution_id)
    return ExecutionEventsResponse(events=events)
```

**驗收標準**:
- [ ] 使用 ExecutionAdapter
- [ ] 狀態查詢、事件獲取功能正常
- [ ] API 行為不變

**檔案**:
- `backend/src/api/v1/executions/routes.py` (修改)
- `backend/tests/integration/test_executions_api.py`

---

### S29-4: checkpoints/routes.py 遷移 (8 點)

**描述**: 將 checkpoints API 遷移到使用審批適配器。

**目標實現**:

```python
# api/v1/checkpoints/routes.py - 使用 HumanApprovalExecutor
from src.integrations.agent_framework.core import (
    HumanApprovalExecutor,
    ApprovalRequest,
    ApprovalResponse
)

@router.get("/pending")
async def get_pending_approvals(
    user_id: str = Depends(get_current_user_id),
    adapter: ApprovalAdapter = Depends(get_approval_adapter)
):
    """獲取待審批列表"""
    pending = await adapter.get_pending_approvals(user_id)
    return PendingApprovalsResponse(approvals=pending)

@router.post("/{request_id}/approve")
async def approve_request(
    request_id: str,
    approval: ApprovalInput,
    user_id: str = Depends(get_current_user_id),
    workflow_manager: WorkflowManager = Depends(get_workflow_manager)
):
    """審批請求"""
    response = ApprovalResponse(
        request_id=request_id,
        approved=True,
        reason=approval.reason,
        approver=user_id,
        approved_at=datetime.utcnow()
    )

    # 恢復工作流
    await workflow_manager.respond(
        executor_name="human-approval",
        response=response
    )

    return {"status": "approved", "request_id": request_id}
```

**驗收標準**:
- [ ] 使用 HumanApprovalExecutor 模式
- [ ] 待審批列表、審批/拒絕功能正常
- [ ] 與工作流正確整合

**檔案**:
- `backend/src/api/v1/checkpoints/routes.py` (修改)
- `backend/tests/integration/test_checkpoints_api.py`

---

### S29-5: API 整合測試 (6 點)

**描述**: 完成所有 API 端點的整合測試。

**驗收標準**:
- [ ] handoff API 所有端點測試通過
- [ ] workflows API 所有端點測試通過
- [ ] executions API 所有端點測試通過
- [ ] checkpoints API 所有端點測試通過
- [ ] 無 domain 層直接 import (Phase 2-5 功能)

**測試範例**:

```python
# tests/integration/test_handoff_api.py
import pytest
from fastapi.testclient import TestClient
from uuid import uuid4


class TestHandoffAPI:

    @pytest.fixture
    def client(self, app):
        return TestClient(app)

    def test_initiate_handoff(self, client, sample_agents):
        """測試啟動交接"""
        response = client.post(
            "/api/v1/handoff/initiate",
            json={
                "source_agent_id": str(sample_agents[0].id),
                "target_agent_id": str(sample_agents[1].id),
                "context": {"task": "customer-support"}
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "handoff_id" in data
        assert data["status"] == "initiated"

    def test_complete_handoff(self, client, active_handoff):
        """測試完成交接"""
        response = client.post(
            f"/api/v1/handoff/{active_handoff.id}/complete"
        )

        assert response.status_code == 200
        assert response.json()["status"] == "completed"

    def test_get_handoff_status(self, client, active_handoff):
        """測試獲取交接狀態"""
        response = client.get(
            f"/api/v1/handoff/{active_handoff.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(active_handoff.id)
```

---

## 完成定義 (Definition of Done)

1. **功能完成**
   - [ ] handoff/routes.py 遷移完成
   - [ ] workflows/routes.py 遷移完成
   - [ ] executions/routes.py 遷移完成
   - [ ] checkpoints/routes.py 遷移完成

2. **測試完成**
   - [ ] 所有 API 端點測試通過
   - [ ] 整合測試通過
   - [ ] 無回歸問題

3. **代碼品質**
   - [ ] 無直接 domain import (Phase 2-5 功能)
   - [ ] 所有 deprecated imports 清理
   - [ ] 代碼審查完成

---

## 相關文檔

- [Sprint 28 Plan](./sprint-28-plan.md) - 人工審批遷移
- [Sprint 30 Plan](./sprint-30-plan.md) - 整合與驗收
- [Phase 5 Overview](./README.md)
