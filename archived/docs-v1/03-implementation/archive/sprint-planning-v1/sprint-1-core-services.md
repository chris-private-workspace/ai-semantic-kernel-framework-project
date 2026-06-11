# Sprint 1: Core Services Development - 詳細規劃

> ℹ️ **開發策略**: 本 Sprint 採用**本地優先開發**  
> 🐳 **開發環境**: Docker Compose (PostgreSQL, Redis, RabbitMQ)  
> 🔐 **認證方式**: Mock Authentication (無需 Azure AD)  
> 📊 **消息隊列**: RabbitMQ (本地容器)  
> 💰 **成本**: $0 Azure 費用 + OpenAI API (~$20/月)

**版本**: 1.1 (Local-First)  
**創建日期**: 2025-11-19  
**更新日期**: 2025-11-20  
**Sprint 期間**: 2025-12-09 至 2025-12-20 (2週)  
**團隊規模**: 8人 (3後端主導, 2前端支持, 1 DevOps, 1 QA, 1 PO)

---

## 📋 Sprint 目標

Sprint 1 的核心目標是實現 IPA Platform 的三大核心服務，為整個平台奠定業務邏輯基礎。

### 核心目標
1. ✅ 實現 Workflow Service (工作流管理)
2. ✅ 實現 Execution Service (執行引擎)
3. ✅ 實現 Agent Service (Agent 編排)
4. ✅ 配置 API Gateway (Kong)
5. ✅ 建立完整的測試框架

### 成功標準
- 可以通過 API 創建、讀取、更新、刪除工作流
- 可以觸發工作流執行，狀態機正常運作
- Agent 可以順序編排執行 (A → B → C)
- Agent Framework 集成成功，支持基本 LLM 調用
- 單元測試覆蓋率 ≥ 80%
- 所有 API 有 Swagger 自動文檔

---

## 📊 Story Points 分配

**總計劃點數**: 45  
**按優先級分配**:
- P0 (Critical): 37 點 (82%)
- P1 (High): 8 點 (18%)

**按模塊分配**:
- Workflow Service: 13 點 (29%)
- Execution Service: 21 點 (47%)
- Agent Service: 13 點 (29%)
- 基礎設施: 8 點

---

## 🎯 Sprint Backlog

### S1-1: Workflow Service - Core CRUD
**Story Points**: 8  
**優先級**: P0 - Critical  
**負責人**: Backend Engineer 1  
**依賴**: S0-4 (數據庫), S0-7 (認證)

#### 描述
實現工作流的創建、讀取、更新、刪除基本操作，為用戶提供管理工作流的核心功能。

#### 驗收標準
- [ ] 實現 POST /api/workflows - 創建工作流
- [ ] 實現 GET /api/workflows - 列出所有工作流
- [ ] 實現 GET /api/workflows/{id} - 獲取單個工作流
- [ ] 實現 PUT /api/workflows/{id} - 更新工作流
- [ ] 實現 DELETE /api/workflows/{id} - 刪除工作流
- [ ] 所有端點需要 JWT 認證
- [ ] 支持分頁 (默認 20 條/頁)
- [ ] 支持按狀態、類別過濾
- [ ] 支持按名稱、創建時間排序
- [ ] 完整的輸入驗證 (Pydantic models)
- [ ] OpenAPI 3.0 文檔自動生成

#### 技術實現細節

```python
# FastAPI 路由定義
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models import Workflow, User
from app.schemas import WorkflowCreate, WorkflowUpdate, WorkflowResponse
from app.dependencies import get_db, get_current_user

router = APIRouter(prefix="/api/workflows", tags=["workflows"])

@router.post("/", response_model=WorkflowResponse, status_code=201)
async def create_workflow(
    workflow: WorkflowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    創建新的工作流
    
    - **name**: 工作流名稱 (必填, 2-200字符)
    - **description**: 工作流描述 (可選, 最多 1000字符)
    - **agent_id**: 關聯的 Agent ID (必填)
    - **trigger_type**: 觸發類型 (manual, cron, webhook)
    - **trigger_config**: 觸發配置 (JSON)
    """
    db_workflow = Workflow(
        name=workflow.name,
        description=workflow.description,
        agent_id=workflow.agent_id,
        trigger_type=workflow.trigger_type,
        trigger_config=workflow.trigger_config,
        created_by=current_user.id
    )
    db.add(db_workflow)
    db.commit()
    db.refresh(db_workflow)
    
    return db_workflow

@router.get("/", response_model=List[WorkflowResponse])
async def list_workflows(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    category: Optional[str] = None,
    sort_by: str = Query("created_at", regex="^(name|created_at|updated_at)$"),
    order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    列出所有工作流 (支持過濾、排序、分頁)
    """
    query = db.query(Workflow).filter(Workflow.created_by == current_user.id)
    
    if status:
        query = query.filter(Workflow.status == status)
    if category:
        query = query.join(Agent).filter(Agent.category == category)
    
    # 排序
    order_by = getattr(Workflow, sort_by)
    if order == "desc":
        order_by = order_by.desc()
    query = query.order_by(order_by)
    
    # 分頁
    workflows = query.offset(skip).limit(limit).all()
    return workflows

@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """獲取單個工作流詳情"""
    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.created_by == current_user.id
    ).first()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return workflow

@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: str,
    workflow_update: WorkflowUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新工作流"""
    db_workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.created_by == current_user.id
    ).first()
    
    if not db_workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # 更新字段
    for field, value in workflow_update.dict(exclude_unset=True).items():
        setattr(db_workflow, field, value)
    
    db_workflow.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_workflow)
    
    return db_workflow

@router.delete("/{workflow_id}", status_code=204)
async def delete_workflow(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """刪除工作流 (軟刪除)"""
    db_workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.created_by == current_user.id
    ).first()
    
    if not db_workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # 軟刪除
    db_workflow.status = "deleted"
    db_workflow.deleted_at = datetime.utcnow()
    db.commit()
    
    return None
```

```python
# Pydantic Schemas
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class TriggerType(str, Enum):
    MANUAL = "manual"
    CRON = "cron"
    WEBHOOK = "webhook"

class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    agent_id: str
    trigger_type: TriggerType
    trigger_config: Optional[Dict[str, Any]] = None
    
    @validator('trigger_config')
    def validate_trigger_config(cls, v, values):
        if 'trigger_type' in values:
            trigger_type = values['trigger_type']
            if trigger_type == TriggerType.CRON and not v.get('cron_expression'):
                raise ValueError('cron_expression required for cron trigger')
            if trigger_type == TriggerType.WEBHOOK and not v.get('webhook_url'):
                raise ValueError('webhook_url required for webhook trigger')
        return v

class WorkflowUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    trigger_type: Optional[TriggerType] = None
    trigger_config: Optional[Dict[str, Any]] = None
    status: Optional[str] = None

class WorkflowResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    agent_id: str
    trigger_type: TriggerType
    trigger_config: Optional[Dict[str, Any]]
    status: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True
```

#### 子任務
1. [ ] 創建 Pydantic schemas (WorkflowCreate, WorkflowUpdate, WorkflowResponse)
2. [ ] 實現 POST /api/workflows endpoint
3. [ ] 實現 GET /api/workflows endpoint (with filters)
4. [ ] 實現 GET /api/workflows/{id} endpoint
5. [ ] 實現 PUT /api/workflows/{id} endpoint
6. [ ] 實現 DELETE /api/workflows/{id} endpoint (soft delete)
7. [ ] 添加輸入驗證和錯誤處理
8. [ ] 編寫單元測試 (pytest)
9. [ ] 編寫集成測試 (TestClient)
10. [ ] 更新 OpenAPI 文檔

#### 測試計劃
```python
# 單元測試示例
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_workflow():
    response = client.post(
        "/api/workflows",
        json={
            "name": "Test Workflow",
            "description": "Test description",
            "agent_id": "test-agent-id",
            "trigger_type": "manual",
            "trigger_config": {}
        },
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Test Workflow"

def test_list_workflows_with_filters():
    response = client.get(
        "/api/workflows?status=active&limit=10&sort_by=name&order=asc",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200
    assert len(response.json()) <= 10

def test_get_workflow_not_found():
    response = client.get(
        "/api/workflows/non-existent-id",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 404
```

---

### S1-2: Workflow Service - Version Management
**Story Points**: 5  
**優先級**: P0 - Critical  
**負責人**: Backend Engineer 1  
**依賴**: S1-1

#### 描述
實現工作流版本管理，允許用戶保存工作流的多個版本並支持版本回滾。

#### 驗收標準
- [ ] 實現 POST /api/workflows/{id}/versions - 創建新版本
- [ ] 實現 GET /api/workflows/{id}/versions - 列出所有版本
- [ ] 實現 GET /api/workflows/{id}/versions/{version} - 獲取特定版本
- [ ] 實現 POST /api/workflows/{id}/rollback/{version} - 回滾到特定版本
- [ ] 每次更新工作流自動創建新版本
- [ ] 版本號自動遞增 (v1, v2, v3...)
- [ ] 保留完整的版本歷史（不可刪除）
- [ ] 支持版本比較 (diff)

#### 技術實現細節
```python
# WorkflowVersion Model
class WorkflowVersion(Base):
    __tablename__ = "workflow_versions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id"))
    version_number = Column(Integer, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"))
    trigger_config = Column(JSONB)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('workflow_id', 'version_number', name='uq_workflow_version'),
    )

@router.post("/{workflow_id}/versions", response_model=WorkflowVersionResponse)
async def create_workflow_version(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """手動創建工作流版本快照"""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # 獲取最新版本號
    latest_version = db.query(func.max(WorkflowVersion.version_number))\
        .filter(WorkflowVersion.workflow_id == workflow_id)\
        .scalar() or 0
    
    # 創建新版本
    version = WorkflowVersion(
        workflow_id=workflow.id,
        version_number=latest_version + 1,
        name=workflow.name,
        description=workflow.description,
        agent_id=workflow.agent_id,
        trigger_config=workflow.trigger_config,
        created_by=current_user.id
    )
    db.add(version)
    db.commit()
    
    return version

@router.post("/{workflow_id}/rollback/{version_number}")
async def rollback_workflow(
    workflow_id: str,
    version_number: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """回滾工作流到指定版本"""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    version = db.query(WorkflowVersion).filter(
        WorkflowVersion.workflow_id == workflow_id,
        WorkflowVersion.version_number == version_number
    ).first()
    
    if not workflow or not version:
        raise HTTPException(status_code=404, detail="Workflow or version not found")
    
    # 恢復版本數據
    workflow.name = version.name
    workflow.description = version.description
    workflow.agent_id = version.agent_id
    workflow.trigger_config = version.trigger_config
    workflow.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": f"Rolled back to version {version_number}"}
```

#### 子任務
1. [ ] 創建 WorkflowVersion 模型和遷移
2. [ ] 實現版本創建 endpoint
3. [ ] 實現版本列表 endpoint
4. [ ] 實現版本詳情 endpoint
5. [ ] 實現回滾功能
6. [ ] 添加版本比較功能 (diff)
7. [ ] 編寫單元測試
8. [ ] 更新 API 文檔

---

### S1-3: Execution Service - State Machine
**Story Points**: 8  
**優先級**: P0 - Critical  
**負責人**: Backend Engineer 2  
**依賴**: S0-4 (數據庫), S0-6 (RabbitMQ)

#### 描述
實現執行狀態機，管理工作流執行的生命週期（Pending → Running → Completed/Failed）。

#### 驗收標準
- [ ] 實現狀態機核心邏輯
- [ ] 支持以下狀態轉換:
  - Pending → Running
  - Running → Paused (checkpoint)
  - Paused → Running (resume)
  - Running → Completed
  - Running → Failed
  - Failed → Retrying → Running
- [ ] 狀態轉換記錄到審計日誌
- [ ] 支持狀態查詢 API
- [ ] 實現狀態鎖機制（防止並發衝突）
- [ ] 超時自動失敗 (默認 30 分鐘)

#### 技術實現細節
```python
# 狀態機實現 (使用 python-statemachine)
from statemachine import StateMachine, State

class ExecutionStateMachine(StateMachine):
    # 定義狀態
    pending = State('Pending', initial=True)
    running = State('Running')
    paused = State('Paused')
    completed = State('Completed', final=True)
    failed = State('Failed', final=True)
    retrying = State('Retrying')
    
    # 定義轉換
    start = pending.to(running)
    pause = running.to(paused)
    resume = paused.to(running)
    complete = running.to(completed)
    fail = running.to(failed) | paused.to(failed)
    retry = failed.to(retrying)
    retry_start = retrying.to(running)
    
    def __init__(self, execution_id: str, db: Session):
        self.execution_id = execution_id
        self.db = db
        super().__init__()
    
    def on_enter_running(self):
        """進入 running 狀態時的回調"""
        execution = self.db.query(Execution).filter(
            Execution.id == self.execution_id
        ).first()
        execution.started_at = datetime.utcnow()
        execution.status = "running"
        self.db.commit()
        
        # 發送到消息隊列開始執行
        publish_to_queue("execution.tasks", {
            "execution_id": self.execution_id,
            "action": "start"
        })
    
    def on_enter_completed(self):
        """進入 completed 狀態時的回調"""
        execution = self.db.query(Execution).filter(
            Execution.id == self.execution_id
        ).first()
        execution.completed_at = datetime.utcnow()
        execution.status = "completed"
        self.db.commit()
        
        # 發送完成通知
        send_teams_notification(execution)
    
    def on_enter_failed(self):
        """進入 failed 狀態時的回調"""
        execution = self.db.query(Execution).filter(
            Execution.id == self.execution_id
        ).first()
        execution.completed_at = datetime.utcnow()
        execution.status = "failed"
        self.db.commit()
        
        # 檢查是否需要重試
        if execution.retry_count < execution.max_retries:
            self.retry()

# Execution Service
class ExecutionService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_execution(self, workflow_id: str, triggered_by: str) -> Execution:
        """創建新的執行"""
        execution = Execution(
            workflow_id=workflow_id,
            status="pending",
            triggered_by=triggered_by,
            max_retries=3,
            retry_count=0
        )
        self.db.add(execution)
        self.db.commit()
        
        # 創建狀態機並啟動
        state_machine = ExecutionStateMachine(execution.id, self.db)
        state_machine.start()
        
        return execution
    
    def get_execution(self, execution_id: str) -> Execution:
        """獲取執行詳情"""
        return self.db.query(Execution).filter(
            Execution.id == execution_id
        ).first()
    
    def pause_execution(self, execution_id: str):
        """暫停執行 (checkpoint)"""
        state_machine = ExecutionStateMachine(execution_id, self.db)
        state_machine.pause()
    
    def resume_execution(self, execution_id: str):
        """恢復執行"""
        state_machine = ExecutionStateMachine(execution_id, self.db)
        state_machine.resume()
    
    def complete_execution(self, execution_id: str, result: dict):
        """完成執行"""
        execution = self.get_execution(execution_id)
        execution.result = result
        self.db.commit()
        
        state_machine = ExecutionStateMachine(execution_id, self.db)
        state_machine.complete()
    
    def fail_execution(self, execution_id: str, error: str):
        """執行失敗"""
        execution = self.get_execution(execution_id)
        execution.error = error
        self.db.commit()
        
        state_machine = ExecutionStateMachine(execution_id, self.db)
        state_machine.fail()

# API Endpoints
@router.post("/api/workflows/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """觸發工作流執行"""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    service = ExecutionService(db)
    execution = service.create_execution(workflow_id, current_user.id)
    
    return {"execution_id": execution.id, "status": execution.status}

@router.get("/api/executions/{execution_id}")
async def get_execution(
    execution_id: str,
    db: Session = Depends(get_db)
):
    """獲取執行狀態"""
    service = ExecutionService(db)
    execution = service.get_execution(execution_id)
    
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    return execution
```

#### 子任務
1. [ ] 設計狀態機 (狀態和轉換)
2. [ ] 實現 ExecutionStateMachine 類
3. [ ] 實現 ExecutionService 類
4. [ ] 創建執行 API endpoints
5. [ ] 實現狀態鎖機制 (PostgreSQL advisory locks)
6. [ ] 實現超時自動失敗機制
7. [ ] 編寫狀態轉換單元測試
8. [ ] 編寫並發場景集成測試

#### 測試計劃
- 測試所有狀態轉換路徑
- 測試並發狀態更新（鎖機制）
- 測試超時自動失敗
- 測試重試機制

---

### S1-4: Execution Service - Step Orchestration
**Story Points**: 8  
**優先級**: P0 - Critical  
**負責人**: Backend Engineer 2  
**依賴**: S1-3

#### 描述
實現步驟編排引擎，支持順序執行多個 Agent，並使用 Hangfire 進行後台任務調度。

#### 驗收標準
- [ ] 支持 Agent 順序執行 (A → B → C)
- [ ] 每個步驟的輸出作為下一步的輸入
- [ ] Hangfire 集成用於後台任務
- [ ] 步驟執行狀態實時更新
- [ ] 支持步驟級別的錯誤處理
- [ ] 記錄每個步驟的執行時間和 LLM 調用

#### 技術實現細節
```python
# 步驟編排引擎
from typing import List, Dict, Any
import asyncio

class Step:
    def __init__(self, agent_id: str, config: dict):
        self.agent_id = agent_id
        self.config = config
        self.result = None
        self.error = None
        self.duration_ms = 0

class StepOrchestrator:
    def __init__(self, execution_id: str, db: Session):
        self.execution_id = execution_id
        self.db = db
        self.steps: List[Step] = []
    
    def add_step(self, agent_id: str, config: dict):
        """添加執行步驟"""
        step = Step(agent_id, config)
        self.steps.append(step)
        return step
    
    async def execute_steps(self):
        """順序執行所有步驟"""
        execution = self.db.query(Execution).filter(
            Execution.id == self.execution_id
        ).first()
        
        previous_output = None
        
        for idx, step in enumerate(self.steps):
            try:
                # 更新執行步驟狀態
                execution_step = ExecutionStep(
                    execution_id=self.execution_id,
                    step_number=idx + 1,
                    agent_id=step.agent_id,
                    status="running",
                    started_at=datetime.utcnow()
                )
                self.db.add(execution_step)
                self.db.commit()
                
                # 執行 Agent
                start_time = time.time()
                agent_service = AgentService(self.db)
                result = await agent_service.execute_agent(
                    step.agent_id,
                    input_data=previous_output,
                    config=step.config
                )
                duration_ms = int((time.time() - start_time) * 1000)
                
                # 更新步驟結果
                execution_step.status = "completed"
                execution_step.completed_at = datetime.utcnow()
                execution_step.result = result
                execution_step.duration_ms = duration_ms
                self.db.commit()
                
                # 傳遞輸出到下一步
                previous_output = result
                step.result = result
                step.duration_ms = duration_ms
                
            except Exception as e:
                # 步驟執行失敗
                execution_step.status = "failed"
                execution_step.error = str(e)
                execution_step.completed_at = datetime.utcnow()
                self.db.commit()
                
                # 整個執行失敗
                execution_service = ExecutionService(self.db)
                execution_service.fail_execution(self.execution_id, str(e))
                raise
        
        # 所有步驟完成
        execution_service = ExecutionService(self.db)
        execution_service.complete_execution(
            self.execution_id,
            {"final_output": previous_output, "steps": len(self.steps)}
        )
        
        return previous_output

# Hangfire 後台任務
from hangfire import BackgroundJob

@BackgroundJob.enqueue
async def execute_workflow_background(execution_id: str, workflow_id: str):
    """後台執行工作流"""
    db = SessionLocal()
    
    try:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        agent = db.query(Agent).filter(Agent.id == workflow.agent_id).first()
        
        # 創建編排器
        orchestrator = StepOrchestrator(execution_id, db)
        
        # 添加步驟 (這裡簡化為單 Agent，實際可以配置多 Agent)
        orchestrator.add_step(agent.id, workflow.trigger_config or {})
        
        # 執行
        result = await orchestrator.execute_steps()
        
        logger.info(f"Execution {execution_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Execution {execution_id} failed: {str(e)}")
    finally:
        db.close()

# 修改執行 API 使用 Hangfire
@router.post("/api/workflows/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """觸發工作流執行 (異步)"""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # 創建執行
    service = ExecutionService(db)
    execution = service.create_execution(workflow_id, current_user.id)
    
    # 放入後台隊列
    background_tasks.add_task(execute_workflow_background, execution.id, workflow_id)
    
    return {
        "execution_id": execution.id,
        "status": "pending",
        "message": "Execution started in background"
    }
```

#### 子任務
1. [ ] 設計 ExecutionStep 模型
2. [ ] 實現 StepOrchestrator 類
3. [ ] 集成 Hangfire for background jobs
4. [ ] 實現步驟級別錯誤處理
5. [ ] 實現步驟結果傳遞邏輯
6. [ ] 記錄 LLM 調用統計
7. [ ] 編寫編排邏輯單元測試
8. [ ] 編寫多步驟集成測試

---

### S1-5: Execution Service - Error Handling & Retry
**Story Points**: 5  
**優先級**: P0 - Critical  
**負責人**: Backend Engineer 2  
**依賴**: S1-4

#### 描述
實現健壯的錯誤處理和重試機制，包含指數退避策略。

#### 驗收標準
- [ ] 支持自動重試（默認 3 次）
- [ ] 指數退避策略（1s, 2s, 4s）
- [ ] 區分可重試和不可重試錯誤
- [ ] 記錄所有錯誤到審計日誌
- [ ] 錯誤時發送 Teams 通知
- [ ] 支持手動重試

#### 技術實現細節
```python
# 錯誤類型定義
class RetryableError(Exception):
    """可重試的錯誤"""
    pass

class NonRetryableError(Exception):
    """不可重試的錯誤"""
    pass

# 重試裝飾器
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

@retry(
    retry=retry_if_exception_type(RetryableError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True
)
async def execute_with_retry(func, *args, **kwargs):
    """帶重試的執行函數"""
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        # 判斷錯誤類型
        if is_retryable_error(e):
            raise RetryableError(str(e))
        else:
            raise NonRetryableError(str(e))

def is_retryable_error(error: Exception) -> bool:
    """判斷錯誤是否可重試"""
    retryable_errors = [
        "timeout",
        "connection",
        "rate_limit",
        "service_unavailable"
    ]
    error_str = str(error).lower()
    return any(keyword in error_str for keyword in retryable_errors)

# 手動重試 API
@router.post("/api/executions/{execution_id}/retry")
async def retry_execution(
    execution_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """手動重試失敗的執行"""
    execution = db.query(Execution).filter(
        Execution.id == execution_id
    ).first()
    
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    if execution.status != "failed":
        raise HTTPException(
            status_code=400,
            detail="Can only retry failed executions"
        )
    
    # 重置狀態
    execution.status = "pending"
    execution.retry_count += 1
    execution.error = None
    db.commit()
    
    # 重新執行
    background_tasks.add_task(
        execute_workflow_background,
        execution.id,
        execution.workflow_id
    )
    
    return {"message": "Execution retry started"}
```

#### 子任務
1. [ ] 定義錯誤類型 (RetryableError, NonRetryableError)
2. [ ] 實現重試裝飾器
3. [ ] 實現錯誤分類邏輯
4. [ ] 實現指數退避策略
5. [ ] 實現手動重試 API
6. [ ] 集成錯誤通知 (Teams)
7. [ ] 編寫錯誤處理單元測試
8. [ ] 編寫重試機制集成測試

---

由於回應長度限制，我將在下一個回應中繼續創建 S1-6 到 S1-9 的詳細內容以及其他 Sprint 文檔。

---

### S1-6: Agent Service - Agent Framework Integration
**Story Points**: 8
**優先級**: P0 - Critical
**負責人**: Backend Engineer 3
**依賴**: S0-4 (數據庫)

#### 描述
集成 Microsoft Agent Framework SDK，實現 Agent 的 LLM 推理能力和插件架構。

#### 驗收標準
- [ ] Agent Framework SDK 集成成功
- [ ] Azure OpenAI 連接配置
- [ ] 實現基本的 LLM 調用功能
- [ ] 支持插件 (Plugins) 架構
- [ ] 實現 Prompt 模板管理
- [ ] LLM 調用追蹤和成本計算
- [ ] 錯誤處理和重試機制

#### 技術實現細節
```python
# Agent Framework 配置
from agent_framework import Kernel
from agent_framework.connectors.ai.open_ai import AzureChatCompletion
from agent_framework.prompt_template import PromptTemplate

class AgentFrameworkService:
    def __init__(self, config: dict):
        self.kernel = Kernel()
        
        # 配置 Azure OpenAI
        self.kernel.add_chat_service(
            "chat-gpt",
            AzureChatCompletion(
                deployment_name=config["azure_openai_deployment"],
                endpoint=config["azure_openai_endpoint"],
                api_key=config["azure_openai_key"]
            )
        )
        
        self.config = config
    
    async def execute_prompt(
        self,
        prompt_template: str,
        variables: dict,
        max_tokens: int = 500,
        temperature: float = 0.7
    ) -> dict:
        """執行 Prompt 並返回結果"""
        start_time = time.time()
        
        try:
            # 創建 Prompt
            prompt = PromptTemplate(
                template=prompt_template,
                input_variables=list(variables.keys())
            )
            
            # 渲染 Prompt
            rendered_prompt = prompt.format(**variables)
            
            # 調用 LLM
            result = await self.kernel.run_async(
                rendered_prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # 計算成本和時長
            duration_ms = int((time.time() - start_time) * 1000)
            tokens_used = result.metadata.get("usage", {}).get("total_tokens", 0)
            cost = self._calculate_cost(tokens_used)
            
            return {
                "output": result.result,
                "tokens_used": tokens_used,
                "cost": cost,
                "duration_ms": duration_ms,
                "model": self.config["azure_openai_deployment"]
            }
            
        except Exception as e:
            logger.error(f"LLM call failed: {str(e)}")
            raise RetryableError(f"LLM call failed: {str(e)}")
    
    def _calculate_cost(self, tokens: int) -> float:
        """計算 LLM 成本 (GPT-4o pricing)"""
        # Input: $2.50 / 1M tokens, Output: $10.00 / 1M tokens
        # 簡化計算，假設 input:output = 1:1
        cost_per_million = 6.25  # Average
        return (tokens / 1_000_000) * cost_per_million
    
    async def execute_with_plugin(
        self,
        plugin_name: str,
        function_name: str,
        **kwargs
    ):
        """執行插件函數"""
        plugin = self.kernel.get_plugin(plugin_name)
        function = plugin[function_name]
        
        result = await self.kernel.run_async(function, **kwargs)
        return result

# Agent Service
class AgentService:
    def __init__(self, db: Session):
        self.db = db
        self.af_service = AgentFrameworkService({
            "azure_openai_deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            "azure_openai_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
            "azure_openai_key": os.getenv("AZURE_OPENAI_KEY")
        })
    
    async def execute_agent(
        self,
        agent_id: str,
        input_data: dict,
        config: dict
    ) -> dict:
        """執行 Agent"""
        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        
        # 獲取 Agent 的 Prompt 模板
        prompt_template = agent.config.get("prompt_template")
        if not prompt_template:
            raise ValueError(f"Agent {agent_id} has no prompt template")
        
        # 準備變量
        variables = {
            "input": input_data,
            "config": config,
            **agent.config.get("default_variables", {})
        }
        
        # 執行 LLM 調用
        result = await self.af_service.execute_prompt(
            prompt_template=prompt_template,
            variables=variables,
            max_tokens=agent.config.get("max_tokens", 500),
            temperature=agent.config.get("temperature", 0.7)
        )
        
        # 記錄 LLM 調用
        self._log_llm_call(agent_id, result)
        
        return result
    
    def _log_llm_call(self, agent_id: str, result: dict):
        """記錄 LLM 調用統計"""
        # 這裡可以記錄到數據庫或發送到監控系統
        logger.info(
            f"LLM call for agent {agent_id}: "
            f"tokens={result['tokens_used']}, "
            f"cost=${result['cost']:.4f}, "
            f"duration={result['duration_ms']}ms"
        )
```

#### 子任務
1. [ ] 安裝 Agent Framework SDK
2. [ ] 配置 Azure OpenAI 連接
3. [ ] 實現 AgentFrameworkService 類
4. [ ] 實現 AgentService 類
5. [ ] 實現 Prompt 模板渲染
6. [ ] 實現 LLM 成本計算
7. [ ] 實現插件架構基礎
8. [ ] 編寫單元測試
9. [ ] 編寫集成測試 (使用 mock LLM)

---

### S1-7: Agent Service - Tool Factory
**Story Points**: 5  
**優先級**: P1 - High  
**負責人**: Backend Engineer 3  
**依賴**: S1-6

#### 描述
實現 Tool Factory 模式，允許動態註冊和調用各種工具（API calls, database queries, etc.）。

#### 驗收標準
- [ ] 實現 ITool 接口
- [ ] 實現 ToolFactory 類
- [ ] 提供至少 3 個內置 Tool:
  - HttpTool (HTTP API 調用)
  - DatabaseTool (數據庫查詢)
  - EmailTool (發送郵件)
- [ ] 支持工具註冊和發現
- [ ] 工具執行結果追蹤

#### 技術實現細節
```python
# Tool 接口
from abc import ABC, abstractmethod

class ITool(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool 名稱"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Tool 描述"""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> dict:
        """執行 Tool"""
        pass

# HTTP Tool
import httpx

class HttpTool(ITool):
    @property
    def name(self) -> str:
        return "http"
    
    @property
    def description(self) -> str:
        return "Make HTTP requests to external APIs"
    
    async def execute(
        self,
        method: str,
        url: str,
        headers: dict = None,
        body: dict = None,
        **kwargs
    ) -> dict:
        """執行 HTTP 請求"""
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                json=body,
                timeout=30.0
            )
            
            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
            }

# Database Tool
class DatabaseTool(ITool):
    def __init__(self, db: Session):
        self.db = db
    
    @property
    def name(self) -> str:
        return "database"
    
    @property
    def description(self) -> str:
        return "Execute database queries"
    
    async def execute(self, query: str, params: dict = None, **kwargs) -> dict:
        """執行數據庫查詢"""
        try:
            result = self.db.execute(text(query), params or {})
            rows = result.fetchall()
            
            return {
                "rows": [dict(row) for row in rows],
                "count": len(rows)
            }
        except Exception as e:
            return {
                "error": str(e),
                "rows": [],
                "count": 0
            }

# Tool Factory
class ToolFactory:
    def __init__(self):
        self._tools: Dict[str, ITool] = {}
    
    def register(self, tool: ITool):
        """註冊 Tool"""
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    def get_tool(self, name: str) -> ITool:
        """獲取 Tool"""
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' not found")
        return self._tools[name]
    
    def list_tools(self) -> List[dict]:
        """列出所有 Tool"""
        return [
            {
                "name": tool.name,
                "description": tool.description
            }
            for tool in self._tools.values()
        ]
    
    async def execute_tool(self, name: str, **kwargs) -> dict:
        """執行 Tool"""
        tool = self.get_tool(name)
        return await tool.execute(**kwargs)

# 全局 Tool Factory 實例
tool_factory = ToolFactory()

# 註冊內置 Tools
tool_factory.register(HttpTool())
tool_factory.register(DatabaseTool(SessionLocal()))

# API Endpoints
@router.get("/api/tools")
async def list_tools():
    """列出所有可用的 Tools"""
    return tool_factory.list_tools()

@router.post("/api/tools/{tool_name}/execute")
async def execute_tool(
    tool_name: str,
    params: dict,
    current_user: User = Depends(get_current_user)
):
    """執行指定的 Tool"""
    try:
        result = await tool_factory.execute_tool(tool_name, **params)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

#### 子任務
1. [ ] 定義 ITool 接口
2. [ ] 實現 ToolFactory 類
3. [ ] 實現 HttpTool
4. [ ] 實現 DatabaseTool
5. [ ] 實現 EmailTool
6. [ ] 實現 Tool 註冊機制
7. [ ] 創建 Tool 執行 API
8. [ ] 編寫單元測試
9. [ ] 編寫集成測試

---

### S1-8: API Gateway Setup
**Story Points**: 5  
**優先級**: P1 - High  
**負責人**: DevOps + Backend  
**依賴**: S1-1, S1-3, S1-6

#### 描述
配置 Kong API Gateway，實現統一的 API 入口、速率限制和認證。

#### 驗收標準
- [ ] Kong 部署到 Kubernetes
- [ ] 配置所有後端服務路由
- [ ] 實現 JWT 認證插件
- [ ] 配置速率限制 (100 req/min per user)
- [ ] 配置 CORS
- [ ] 配置 API 日誌記錄
- [ ] 健康檢查端點

#### 技術實現細節
```yaml
# Kong Kubernetes 配置
apiVersion: v1
kind: Service
metadata:
  name: kong-proxy
  namespace: ipa-platform-core
spec:
  type: LoadBalancer
  ports:
  - name: proxy
    port: 80
    targetPort: 8000
  - name: proxy-ssl
    port: 443
    targetPort: 8443
  selector:
    app: kong

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kong
  namespace: ipa-platform-core
spec:
  replicas: 2
  selector:
    matchLabels:
      app: kong
  template:
    metadata:
      labels:
        app: kong
    spec:
      containers:
      - name: kong
        image: kong:3.4
        env:
        - name: KONG_DATABASE
          value: "postgres"
        - name: KONG_PG_HOST
          value: "postgresql"
        - name: KONG_PG_DATABASE
          value: "kong"
        - name: KONG_PROXY_ACCESS_LOG
          value: "/dev/stdout"
        - name: KONG_ADMIN_ACCESS_LOG
          value: "/dev/stdout"
        - name: KONG_PROXY_ERROR_LOG
          value: "/dev/stderr"
        - name: KONG_ADMIN_ERROR_LOG
          value: "/dev/stderr"
        ports:
        - containerPort: 8000
          name: proxy
        - containerPort: 8443
          name: proxy-ssl
        - containerPort: 8001
          name: admin

---
# Kong 服務配置 (使用 deck)
_format_version: "3.0"

services:
  - name: workflow-service
    url: http://workflow-service:8000
    routes:
      - name: workflow-routes
        paths:
          - /api/workflows
          - /api/executions
        methods:
          - GET
          - POST
          - PUT
          - DELETE
    plugins:
      - name: jwt
        config:
          key_claim_name: kid
          secret_is_base64: false
      - name: rate-limiting
        config:
          minute: 100
          policy: local
      - name: cors
        config:
          origins:
            - "*"
          methods:
            - GET
            - POST
            - PUT
            - DELETE
          headers:
            - Authorization
            - Content-Type
          credentials: true
          max_age: 3600

  - name: agent-service
    url: http://agent-service:8000
    routes:
      - name: agent-routes
        paths:
          - /api/agents
          - /api/tools
        methods:
          - GET
          - POST
          - PUT
          - DELETE
    plugins:
      - name: jwt
      - name: rate-limiting
        config:
          minute: 50
      - name: cors
```

#### 子任務
1. [ ] 部署 Kong 到 Kubernetes
2. [ ] 配置 PostgreSQL for Kong
3. [ ] 配置服務路由 (workflow, agent services)
4. [ ] 配置 JWT 認證插件
5. [ ] 配置速率限制
6. [ ] 配置 CORS
7. [ ] 配置日誌記錄
8. [ ] 測試所有路由
9. [ ] 創建 Kong 管理文檔

---

### S1-9: Test Framework Setup
**Story Points**: 3  
**優先級**: P1 - High  
**負責人**: QA Engineer  
**依賴**: S1-1

#### 描述
建立完整的測試框架，包含單元測試、集成測試和測試數據管理。

#### 驗收標準
- [ ] pytest 測試框架配置
- [ ] TestClient for FastAPI 集成測試
- [ ] 測試數據庫配置 (isolated)
- [ ] Mock LLM 服務 (避免實際調用)
- [ ] 測試覆蓋率報告 (pytest-cov)
- [ ] CI/CD 集成測試自動化
- [ ] 測試文檔和最佳實踐

#### 技術實現細節
```python
# conftest.py - pytest 配置
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base
from app.dependencies import get_db

# 測試數據庫
SQLALCHEMY_TEST_DATABASE_URL = "postgresql://test:test@localhost:5432/test_ipa"
test_engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="function")
def db():
    """創建測試數據庫會話"""
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="function")
def client(db):
    """創建測試客戶端"""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as c:
        yield c

@pytest.fixture
def test_user(db):
    """創建測試用戶"""
    user = User(
        email="test@example.com",
        name="Test User",
        role="admin",
        password_hash=bcrypt.hashpw("password".encode(), bcrypt.gensalt())
    )
    db.add(user)
    db.commit()
    return user

@pytest.fixture
def auth_headers(test_user):
    """生成認證 headers"""
    token = create_access_token({"sub": test_user.email})
    return {"Authorization": f"Bearer {token}"}

# Mock LLM Service
from unittest.mock import Mock, AsyncMock

@pytest.fixture
def mock_llm_service(monkeypatch):
    """Mock Agent Framework LLM 調用"""
    mock_service = AsyncMock()
    mock_service.execute_prompt.return_value = {
        "output": "Mocked LLM response",
        "tokens_used": 100,
        "cost": 0.001,
        "duration_ms": 500,
        "model": "gpt-4o-mock"
    }
    
    monkeypatch.setattr("app.services.agent_service.AgentFrameworkService", lambda x: mock_service)
    return mock_service

# 單元測試示例
def test_create_workflow(client, auth_headers):
    response = client.post(
        "/api/workflows",
        json={
            "name": "Test Workflow",
            "description": "Test description",
            "agent_id": "test-agent-id",
            "trigger_type": "manual"
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Test Workflow"

# 集成測試示例
@pytest.mark.asyncio
async def test_execute_workflow_integration(client, auth_headers, db, mock_llm_service):
    # 創建 Agent
    agent = Agent(
        name="Test Agent",
        category="IT",
        code="test code",
        config={"prompt_template": "Test: {{input}}"}
    )
    db.add(agent)
    db.commit()
    
    # 創建 Workflow
    workflow_response = client.post(
        "/api/workflows",
        json={
            "name": "Integration Test Workflow",
            "agent_id": str(agent.id),
            "trigger_type": "manual"
        },
        headers=auth_headers
    )
    workflow_id = workflow_response.json()["id"]
    
    # 執行 Workflow
    exec_response = client.post(
        f"/api/workflows/{workflow_id}/execute",
        headers=auth_headers
    )
    assert exec_response.status_code == 200
    execution_id = exec_response.json()["execution_id"]
    
    # 驗證執行狀態
    status_response = client.get(
        f"/api/executions/{execution_id}",
        headers=auth_headers
    )
    assert status_response.status_code == 200
```

```yaml
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
```

#### 子任務
1. [ ] 配置 pytest 和 pytest-cov
2. [ ] 創建測試數據庫配置
3. [ ] 實現 pytest fixtures (db, client, auth)
4. [ ] 實現 Mock LLM 服務
5. [ ] 編寫單元測試模板
6. [ ] 編寫集成測試模板
7. [ ] 配置 CI/CD 測試自動化
8. [ ] 創建測試文檔

---

## 📈 Sprint Metrics

### 燃盡圖目標
- 第 1 天: 45 點
- 第 5 天: 27 點 (完成 40%)
- 第 10 天: 0 點 (完成 100%)

### 每日站會重點
- Backend Team: 核心服務開發進度
- DevOps: API Gateway 配置進度
- QA: 測試框架和測試用例進度

---

## 🚨 風險和緩解策略

### 高風險項目

#### 風險 1: Agent Framework 學習曲線陡峭
- **嚴重性**: 🔴 高
- **概率**: 🟡 中
- **緩解**:
  - Sprint 第一週安排 2 天專門學習
  - 創建內部 Agent Framework 使用文檔
  - 準備備用方案（純 Python LLM 調用）

#### 風險 2: 狀態機複雜度超出預期
- **嚴重性**: 🟡 中
- **概率**: 🟡 中
- **緩解**:
  - 使用 python-statemachine 庫簡化實現
  - 先實現基本狀態，高級功能延後

---

## ✅ Definition of Done

- [ ] 所有 API endpoints 實現並測試
- [ ] 單元測試覆蓋率 ≥ 80%
- [ ] 集成測試通過
- [ ] OpenAPI 文檔自動生成
- [ ] 代碼 review 完成
- [ ] 部署到 Staging 成功
- [ ] 性能測試通過 (P95 < 5s)

---

**狀態**: Not Started  
**上次更新**: 2025-11-19  
**更新人**: GitHub Copilot