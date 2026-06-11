# S1-1: Workflow Service - Core CRUD 實現總結

**Story ID**: S1-1
**Story Points**: 8
**優先級**: P0 - Critical
**負責人**: Backend Engineer 1
**狀態**: Not Started
**開始日期**: 2025-11-21
**完成日期**: TBD

---

## 📋 Story 概述

### 目標
實現工作流的創建、讀取、更新、刪除基本操作,為用戶提供管理工作流的核心功能。

### 依賴項
- ✅ S0-4: Database Infrastructure (已完成)
- ✅ S0-7: Authentication Framework (已完成)

### 驗收標準

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

---

## 🏗️ 技術架構

### 架構層次
```
FastAPI Router (API Layer)
    ↓
Pydantic Schemas (Validation Layer)
    ↓
SQLAlchemy Models (Data Layer)
    ↓
PostgreSQL Database
```

### 核心組件

#### 1. Database Model
**文件**: `backend/src/app/models/workflow.py`

```python
from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import uuid
from datetime import datetime

class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    trigger_type = Column(String(50), nullable=False)  # manual, cron, webhook
    trigger_config = Column(JSON)
    status = Column(String(50), default="active", index=True)  # active, inactive, deleted
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    # 關聯
    # agent = relationship("Agent", back_populates="workflows")
    # creator = relationship("User", back_populates="workflows")
```

#### 2. Pydantic Schemas
**文件**: `backend/src/app/schemas/workflow.py`

```python
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

#### 3. FastAPI Router
**文件**: `backend/src/app/api/v1/workflows.py`

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models import Workflow, User
from app.schemas import WorkflowCreate, WorkflowUpdate, WorkflowResponse
from app.dependencies import get_db, get_current_user

router = APIRouter(prefix="/api/v1/workflows", tags=["workflows"])

@router.post("/", response_model=WorkflowResponse, status_code=201)
async def create_workflow(
    workflow: WorkflowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """創建新的工作流"""
    # 實現細節
    pass

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
    """列出所有工作流 (支持過濾、排序、分頁)"""
    # 實現細節
    pass

# ... 其他端點
```

---

## 📝 實現細節

### 任務分解

#### Task 1: 創建 Database Model 和 Migration
- [ ] 創建 `workflow.py` model 文件
- [ ] 定義 Workflow 表結構
- [ ] 創建 Alembic migration
- [ ] 運行 migration 到本地數據庫

#### Task 2: 創建 Pydantic Schemas
- [ ] 創建 `schemas/workflow.py`
- [ ] 定義 `WorkflowCreate` schema
- [ ] 定義 `WorkflowUpdate` schema
- [ ] 定義 `WorkflowResponse` schema
- [ ] 添加自定義驗證器

#### Task 3: 實現 CREATE Endpoint
- [ ] 實現 `POST /api/v1/workflows`
- [ ] 驗證 agent_id 存在
- [ ] 驗證 trigger_config 格式
- [ ] 插入數據庫
- [ ] 返回創建的工作流

#### Task 4: 實現 READ Endpoints
- [ ] 實現 `GET /api/v1/workflows` (列表)
  - [ ] 分頁參數 (skip, limit)
  - [ ] 過濾參數 (status, category)
  - [ ] 排序參數 (sort_by, order)
- [ ] 實現 `GET /api/v1/workflows/{id}` (詳情)
  - [ ] 檢查工作流存在
  - [ ] 檢查用戶權限

#### Task 5: 實現 UPDATE Endpoint
- [ ] 實現 `PUT /api/v1/workflows/{id}`
- [ ] 部分更新支持 (exclude_unset)
- [ ] 更新 updated_at 時間戳
- [ ] 返回更新後的工作流

#### Task 6: 實現 DELETE Endpoint
- [ ] 實現 `DELETE /api/v1/workflows/{id}`
- [ ] 軟刪除實現 (status = "deleted")
- [ ] 設置 deleted_at 時間戳
- [ ] 返回 204 No Content

#### Task 7: 添加錯誤處理
- [ ] 404 錯誤 (工作流不存在)
- [ ] 403 錯誤 (權限不足)
- [ ] 400 錯誤 (驗證失敗)
- [ ] 500 錯誤 (服務器錯誤)

#### Task 8: 編寫單元測試
- [ ] 測試創建工作流 (成功和失敗案例)
- [ ] 測試列出工作流 (過濾、排序、分頁)
- [ ] 測試獲取工作流詳情
- [ ] 測試更新工作流
- [ ] 測試刪除工作流
- [ ] 測試權限檢查

#### Task 9: 編寫集成測試
- [ ] 完整的 CRUD 流程測試
- [ ] 多用戶隔離測試
- [ ] 邊界條件測試

#### Task 10: 更新 API 文檔
- [ ] OpenAPI schema 自動生成
- [ ] 添加詳細的描述和示例
- [ ] 更新 README.md

---

## 🧪 測試計劃

### 單元測試

**文件**: `backend/tests/test_workflows.py`

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestWorkflowCRUD:
    def test_create_workflow_success(self, auth_headers, test_agent):
        """測試成功創建工作流"""
        response = client.post(
            "/api/v1/workflows",
            json={
                "name": "Test Workflow",
                "description": "Test description",
                "agent_id": str(test_agent.id),
                "trigger_type": "manual",
                "trigger_config": {}
            },
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Workflow"
        assert data["trigger_type"] == "manual"

    def test_create_workflow_invalid_agent(self, auth_headers):
        """測試使用無效 agent_id 創建工作流"""
        response = client.post(
            "/api/v1/workflows",
            json={
                "name": "Test Workflow",
                "agent_id": "non-existent-id",
                "trigger_type": "manual"
            },
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_list_workflows_with_pagination(self, auth_headers, create_test_workflows):
        """測試分頁功能"""
        response = client.get(
            "/api/v1/workflows?skip=0&limit=5",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 5

    def test_list_workflows_with_filters(self, auth_headers, create_test_workflows):
        """測試過濾功能"""
        response = client.get(
            "/api/v1/workflows?status=active&sort_by=name&order=asc",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        # 驗證排序
        names = [w["name"] for w in data]
        assert names == sorted(names)

    def test_get_workflow_by_id(self, auth_headers, test_workflow):
        """測試獲取單個工作流"""
        response = client.get(
            f"/api/v1/workflows/{test_workflow.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_workflow.id)

    def test_get_workflow_not_found(self, auth_headers):
        """測試獲取不存在的工作流"""
        response = client.get(
            "/api/v1/workflows/00000000-0000-0000-0000-000000000000",
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_update_workflow(self, auth_headers, test_workflow):
        """測試更新工作流"""
        response = client.put(
            f"/api/v1/workflows/{test_workflow.id}",
            json={"name": "Updated Workflow"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Workflow"

    def test_delete_workflow(self, auth_headers, test_workflow):
        """測試刪除工作流"""
        response = client.delete(
            f"/api/v1/workflows/{test_workflow.id}",
            headers=auth_headers
        )
        assert response.status_code == 204

        # 驗證軟刪除
        workflow = db.query(Workflow).filter(Workflow.id == test_workflow.id).first()
        assert workflow.status == "deleted"
        assert workflow.deleted_at is not None
```

### 測試覆蓋率目標
- **單元測試覆蓋率**: ≥ 80%
- **集成測試**: 完整 CRUD 流程
- **邊界測試**: 輸入驗證、權限檢查

---

## 📊 實現狀態

### 完成情況

| 任務 | 狀態 | 完成日期 | 備註 |
|------|------|----------|------|
| Database Model | ⏳ Not Started | - | - |
| Pydantic Schemas | ⏳ Not Started | - | - |
| CREATE Endpoint | ⏳ Not Started | - | - |
| READ Endpoints | ⏳ Not Started | - | - |
| UPDATE Endpoint | ⏳ Not Started | - | - |
| DELETE Endpoint | ⏳ Not Started | - | - |
| 錯誤處理 | ⏳ Not Started | - | - |
| 單元測試 | ⏳ Not Started | - | - |
| 集成測試 | ⏳ Not Started | - | - |
| API 文檔 | ⏳ Not Started | - | - |

### 實際工時記錄
| 日期 | 工作內容 | 耗時 | 累計 |
|------|----------|------|------|
| 2025-11-21 | 文檔準備 | - | - |

---

## 🔍 Code Review Checklist

開發完成後,使用此 checklist 進行自我檢查:

### 功能完整性
- [ ] 所有驗收標準都滿足
- [ ] 所有 API endpoints 正常工作
- [ ] 分頁、過濾、排序功能正常

### 代碼質量
- [ ] 遵循 PEP 8 風格
- [ ] 函數和類有適當的 docstrings
- [ ] 沒有硬編碼的值
- [ ] 錯誤處理完整

### 安全性
- [ ] JWT 認證正確實施
- [ ] SQL 注入防護 (使用 ORM)
- [ ] 輸入驗證完整
- [ ] 用戶權限檢查

### 測試
- [ ] 測試覆蓋率 ≥ 80%
- [ ] 所有測試通過
- [ ] 包含邊界測試

### 文檔
- [ ] OpenAPI 文檔完整
- [ ] README 更新
- [ ] 代碼註釋清晰

---

## 🐛 已知問題和解決方案

### 問題列表
_開發過程中遇到的問題記錄在此_

| 問題 | 影響 | 解決方案 | 狀態 |
|------|------|----------|------|
| - | - | - | - |

---

## 📚 參考文檔

### 內部文檔
- [Sprint 1 Planning](../../../sprint-planning/sprint-1-core-services.md)
- [Database Schema Design](../../architecture-designs/database-schema-design.md)
- [Authentication Design](../../architecture-designs/authentication-design.md)
- [SPRINT-EXECUTION-GUIDE.md](../../SPRINT-EXECUTION-GUIDE.md)

### 外部文檔
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Validators](https://pydantic-docs.helpmanual.io/usage/validators/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/14/orm/)
- [Alembic Migrations](https://alembic.sqlalchemy.org/en/latest/)

---

## 💡 技術決策記錄

### 決策 1: 軟刪除 vs 硬刪除
**決策**: 使用軟刪除 (status = "deleted" + deleted_at timestamp)
**理由**:
- 保留歷史記錄用於審計
- 可以恢復誤刪除的工作流
- 不破壞外鍵關聯

**權衡**:
- 需要在查詢時過濾 deleted 狀態
- 數據庫會保留更多數據

### 決策 2: 分頁默認值
**決策**: 默認 20 條/頁,最大 100 條/頁
**理由**:
- 平衡性能和用戶體驗
- 防止單次查詢過多數據

---

## 🎯 下一步工作

### 當前 Story (S1-1) 完成後
1. 進行 Code Review
2. 更新 sprint-status.yaml
3. 創建 S1-1 完成報告
4. 開始 S1-2: Workflow Service - Version Management

### Sprint 1 整體進度
- S1-1: Workflow CRUD (當前)
- S1-2: Version Management (下一個)
- S1-3: Execution State Machine
- ...

---

**最後更新**: 2025-11-21
**更新人**: AI Assistant
**版本**: v1.0
