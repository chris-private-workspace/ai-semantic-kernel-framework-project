# Sprint 0: 本地開發環境搭建 - Local-First 版本

> ℹ️ **重要**: 本文檔為 Sprint 0-3 的**本地開發版本**，完全不依賴 Azure 服務。
> 📄 **雲端部署版**: 請參考 [sprint-0-mvp-revised.md](./sprint-0-mvp-revised.md) (用於 Sprint 4+ 集成測試/生產部署)

**版本**: 2.0 (Local-First)  
**創建日期**: 2025-11-20  
**適用階段**: Sprint 0-3 (本地開發階段)  
**Sprint 期間**: 2025-11-25 至 2025-12-06 (2週)  
**團隊規模**: 8人 (3後端, 2前端, 1 DevOps, 1 QA, 1 PO)

---

## 🎯 本地開發策略

### 核心理念
- ✅ **零 Azure 成本**: 開發階段完全本地，省下 3 個月 $114 訂閱費
- ✅ **快速迭代**: 無網絡延遲，本地調試方便
- ✅ **離線開發**: 不依賴網絡連接
- ✅ **平滑遷移**: 代碼無需修改，僅切換環境變量

### 本地服務架構

```
┌─────────────────────────────────────────────────────┐
│            Docker Compose 本地環境                    │
├─────────────────────────────────────────────────────┤
│                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │ PostgreSQL   │  │    Redis     │  │ RabbitMQ  │ │
│  │   16-alpine  │  │   7-alpine   │  │  3.12-mgmt│ │
│  │              │  │              │  │           │ │
│  │ Port: 5432   │  │ Port: 6379   │  │ Port:5672 │ │
│  └──────────────┘  └──────────────┘  │ UI:  15672│ │
│                                        └───────────┘ │
│                                                       │
│  ┌──────────────────────────────────────────────┐   │
│  │         Backend (FastAPI + Uvicorn)          │   │
│  │                                              │   │
│  │  - Mock Authentication (無需 Azure AD)       │   │
│  │  - Console Logging (無需 App Insights)       │   │
│  │  - OpenAI API (可選，用於 AI 功能)           │   │
│  │                                              │   │
│  │  Port: 8000                                  │   │
│  │  Swagger: http://localhost:8000/docs        │   │
│  └──────────────────────────────────────────────┘   │
│                                                       │
└─────────────────────────────────────────────────────┘
```

---

## 📊 Story Points (本地開發版)

**總計劃點數**: 18 點  
**預計完成時間**: 5 天 (比原計劃快 5 天)

**任務分配**:
| 任務 | 負責人 | 點數 | 狀態 |
|------|--------|------|------|
| S0-1: Docker Compose 環境 | DevOps | 5 | ✅ 已完成 |
| S0-2: 數據庫 Models & Migrations | Backend | 5 | 待開始 |
| S0-3: Mock Authentication | Backend | 3 | 待開始 |
| S0-4: RabbitMQ 消息隊列集成 | Backend | 3 | 待開始 |
| S0-5: 基礎 API Endpoints | Backend | 2 | 待開始 |

---

## 🎯 Sprint Backlog (本地開發)

### S0-1: Docker Compose 環境搭建 ✅
**Story Points**: 5  
**優先級**: P0 - Critical  
**負責人**: DevOps  
**依賴**: 無  
**狀態**: ✅ **已完成 (2025-11-20)**

#### 完成內容
- [x] `docker-compose.yml` 配置完成
  - PostgreSQL 16 (ipa-postgres)
  - Redis 7 (ipa-redis)
  - RabbitMQ 3.12 (ipa-rabbitmq)
  - Backend FastAPI (ipa-backend)
- [x] `.env.example` 環境變量模板
- [x] `scripts/init-db.sql` 數據庫初始化腳本
- [x] `backend/` 基礎項目結構
- [x] `CONTRIBUTING.md` 開發規範
- [x] `docs/03-implementation/local-development-guide.md` 完整指南

#### 驗證方式
```bash
# 啟動所有服務
docker-compose up -d

# 驗證服務健康
docker-compose ps

# 測試 API
curl http://localhost:8000/health
# 應返回: {"status":"healthy","version":"0.1.0"}

# 訪問管理界面
# API 文檔: http://localhost:8000/docs
# RabbitMQ UI: http://localhost:15672 (guest/guest)
```

---

### S0-2: 數據庫 Models & Migrations
**Story Points**: 5  
**優先級**: P0 - Critical  
**負責人**: Backend  
**依賴**: S0-1  
**預計時間**: 2-3 天

#### 描述
創建 SQLAlchemy Models 和 Alembic 遷移，建立數據庫架構。

#### 驗收標準
- [ ] 安裝依賴:
  ```bash
  pip install sqlalchemy alembic psycopg2-binary asyncpg
  ```
- [ ] 創建 Models:
  - `models/user.py`: User 模型
  - `models/workflow.py`: Workflow 模型
  - `models/execution.py`: Execution 模型
  - `models/agent.py`: Agent 模型
- [ ] 初始化 Alembic:
  ```bash
  alembic init migrations
  ```
- [ ] 生成初始遷移:
  ```bash
  alembic revision --autogenerate -m "Initial schema"
  ```
- [ ] 執行遷移:
  ```bash
  alembic upgrade head
  ```
- [ ] 驗證表創建成功

#### 技術實現

**backend/src/core/database.py**:
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://ipa_user:ipa_password@localhost:5432/ipa_platform"
)

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

**backend/src/models/workflow.py**:
```python
from sqlalchemy import Column, String, Text, JSON, Integer, DateTime, Boolean
from sqlalchemy.sql import func
from src.core.database import Base
import uuid

class Workflow(Base):
    __tablename__ = "workflows"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    config = Column(JSON, nullable=False)
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(255))
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "config": self.config,
            "version": self.version,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
```

#### 子任務
1. [ ] 創建 database.py (連接配置)
2. [ ] 創建 User model
3. [ ] 創建 Workflow model
4. [ ] 創建 Execution model
5. [ ] 創建 Agent model
6. [ ] 配置 Alembic (alembic.ini, env.py)
7. [ ] 生成並執行初始遷移
8. [ ] 編寫數據庫 seeder (測試數據)
9. [ ] 測試 CRUD 操作

---

### S0-3: Mock Authentication
**Story Points**: 3  
**優先級**: P0 - Critical  
**負責人**: Backend  
**依賴**: S0-2  
**預計時間**: 1 天

#### 描述
實現 Mock 認證系統，用於本地開發，無需 Azure AD。

#### 驗收標準
- [ ] Mock 用戶系統實現
- [ ] 認證 middleware 配置
- [ ] 支持不同用戶角色 (admin, user, viewer)
- [ ] 登入 endpoint 返回 mock token
- [ ] 受保護的 endpoint 驗證 token

#### 技術實現

**backend/src/auth/mock_auth.py**:
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import os

security = HTTPBearer()

class MockUser:
    def __init__(self, email: str, name: str, roles: list[str]):
        self.id = "mock-user-id"
        self.email = email
        self.name = name
        self.roles = roles
        self.is_authenticated = True

async def get_current_user_mock(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> MockUser:
    """Mock authentication - 始終返回測試用戶"""
    
    # 允許無 token 訪問（開發模式）
    if not credentials and os.getenv("AUTH_MODE") == "mock":
        return MockUser(
            email=os.getenv("MOCK_USER_EMAIL", "developer@example.com"),
            name=os.getenv("MOCK_USER_NAME", "Local Developer"),
            roles=os.getenv("MOCK_USER_ROLES", "admin,user").split(",")
        )
    
    # 簡單的 token 驗證（開發用）
    if credentials and credentials.credentials == "mock-token":
        return MockUser(
            email="developer@example.com",
            name="Local Developer",
            roles=["admin", "user"]
        )
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
    )

def require_role(required_role: str):
    """角色驗證裝飾器"""
    async def role_checker(user: MockUser = Depends(get_current_user_mock)):
        if required_role not in user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {required_role}"
            )
        return user
    return role_checker
```

**backend/src/auth/router.py**:
```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Mock 登入 - 始終成功"""
    return {
        "access_token": "mock-token",
        "token_type": "bearer",
        "user": {
            "email": request.email,
            "name": "Local Developer",
            "roles": ["admin", "user"]
        }
    }

@router.post("/logout")
async def logout():
    """Mock 登出"""
    return {"message": "Logged out successfully"}
```

#### 子任務
1. [ ] 創建 mock_auth.py
2. [ ] 實現 MockUser 類
3. [ ] 實現 get_current_user_mock
4. [ ] 創建 auth router (登入/登出)
5. [ ] 在 main.py 中註冊 auth router
6. [ ] 測試認證流程

---

### S0-4: RabbitMQ 消息隊列集成
**Story Points**: 3  
**優先級**: P0 - Critical  
**負責人**: Backend  
**依賴**: S0-2  
**預計時間**: 1-2 天

#### 描述
集成 RabbitMQ，實現消息發布和消費機制。

#### 驗收標準
- [ ] 安裝依賴:
  ```bash
  pip install pika
  ```
- [ ] 消息發布者實現
- [ ] 消息消費者基類實現
- [ ] 創建測試隊列和 exchange
- [ ] 重試機制實現
- [ ] 消息序列化/反序列化

#### 技術實現

**backend/src/messaging/rabbitmq.py**:
```python
import pika
import json
import os
from typing import Callable
from abc import ABC, abstractmethod

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")

class MessagePublisher:
    def __init__(self):
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        self.parameters = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            credentials=credentials
        )
    
    def publish(self, queue_name: str, message: dict):
        """發布消息到隊列"""
        connection = pika.BlockingConnection(self.parameters)
        channel = connection.channel()
        
        # 確保隊列存在
        channel.queue_declare(queue=queue_name, durable=True)
        
        # 發布消息
        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # 持久化消息
            )
        )
        
        connection.close()
        print(f"✅ Message published to {queue_name}")

class MessageConsumer(ABC):
    def __init__(self, queue_name: str):
        self.queue_name = queue_name
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        self.parameters = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            credentials=credentials
        )
    
    @abstractmethod
    async def handle_message(self, message: dict):
        """子類實現此方法來處理消息"""
        pass
    
    def start(self):
        """開始消費消息"""
        connection = pika.BlockingConnection(self.parameters)
        channel = connection.channel()
        
        channel.queue_declare(queue=self.queue_name, durable=True)
        channel.basic_qos(prefetch_count=1)
        
        def callback(ch, method, properties, body):
            try:
                message = json.loads(body)
                print(f"📩 Received message from {self.queue_name}: {message}")
                
                # 處理消息 (同步調用異步方法)
                import asyncio
                asyncio.run(self.handle_message(message))
                
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                print(f"❌ Error processing message: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        
        channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=callback
        )
        
        print(f"🎧 Listening for messages on {self.queue_name}...")
        channel.start_consuming()
```

#### 使用示例

**發布消息**:
```python
from src.messaging.rabbitmq import MessagePublisher

publisher = MessagePublisher()
publisher.publish("execution-queue", {
    "workflow_id": "wf-123",
    "execution_id": "exec-456",
    "action": "start"
})
```

**消費消息**:
```python
from src.messaging.rabbitmq import MessageConsumer

class ExecutionConsumer(MessageConsumer):
    def __init__(self):
        super().__init__("execution-queue")
    
    async def handle_message(self, message: dict):
        print(f"Processing execution: {message['execution_id']}")
        # 實際的執行邏輯...

# 啟動消費者
consumer = ExecutionConsumer()
consumer.start()
```

#### 子任務
1. [ ] 創建 rabbitmq.py
2. [ ] 實現 MessagePublisher
3. [ ] 實現 MessageConsumer 基類
4. [ ] 創建測試消費者
5. [ ] 測試消息發布和消費
6. [ ] 測試重試機制

---

### S0-5: 基礎 API Endpoints
**Story Points**: 2  
**優先級**: P0 - Critical  
**負責人**: Backend  
**依賴**: S0-2, S0-3  
**預計時間**: 1 天

#### 描述
實現基礎的 CRUD API endpoints，用於測試。

#### 驗收標準
- [ ] Workflow CRUD endpoints
  - GET /api/v1/workflows (列表)
  - POST /api/v1/workflows (創建)
  - GET /api/v1/workflows/{id} (詳情)
  - PUT /api/v1/workflows/{id} (更新)
  - DELETE /api/v1/workflows/{id} (刪除)
- [ ] Swagger 文檔自動生成
- [ ] 請求驗證 (Pydantic schemas)
- [ ] 錯誤處理 middleware
- [ ] 所有 endpoints 需要認證

#### 技術實現

**backend/src/workflow/schemas.py**:
```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    config: dict = Field(...)

class WorkflowUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    config: Optional[dict] = None
    is_active: Optional[bool] = None

class WorkflowResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    config: dict
    version: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True
```

**backend/src/workflow/router.py**:
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from src.core.database import get_db
from src.models.workflow import Workflow
from src.workflow.schemas import WorkflowCreate, WorkflowUpdate, WorkflowResponse
from src.auth.mock_auth import get_current_user_mock, MockUser

router = APIRouter(prefix="/api/v1/workflows", tags=["workflows"])

@router.get("/", response_model=List[WorkflowResponse])
async def list_workflows(
    db: AsyncSession = Depends(get_db),
    current_user: MockUser = Depends(get_current_user_mock)
):
    """獲取所有工作流"""
    result = await db.execute(select(Workflow))
    workflows = result.scalars().all()
    return workflows

@router.post("/", response_model=WorkflowResponse, status_code=201)
async def create_workflow(
    workflow: WorkflowCreate,
    db: AsyncSession = Depends(get_db),
    current_user: MockUser = Depends(get_current_user_mock)
):
    """創建新工作流"""
    db_workflow = Workflow(
        **workflow.dict(),
        created_by=current_user.email
    )
    db.add(db_workflow)
    await db.commit()
    await db.refresh(db_workflow)
    return db_workflow

@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: MockUser = Depends(get_current_user_mock)
):
    """獲取工作流詳情"""
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id)
    )
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return workflow

@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: str,
    workflow: WorkflowUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: MockUser = Depends(get_current_user_mock)
):
    """更新工作流"""
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id)
    )
    db_workflow = result.scalar_one_or_none()
    
    if not db_workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    for key, value in workflow.dict(exclude_unset=True).items():
        setattr(db_workflow, key, value)
    
    await db.commit()
    await db.refresh(db_workflow)
    return db_workflow

@router.delete("/{workflow_id}", status_code=204)
async def delete_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: MockUser = Depends(get_current_user_mock)
):
    """刪除工作流"""
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id)
    )
    db_workflow = result.scalar_one_or_none()
    
    if not db_workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    await db.delete(db_workflow)
    await db.commit()
```

**backend/main.py** (更新):
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.workflow.router import router as workflow_router
from src.auth.router import router as auth_router

app = FastAPI(
    title="IPA Platform API",
    description="Intelligent Process Automation Platform (Local Development)",
    version="0.1.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router)
app.include_router(workflow_router)

@app.get("/")
async def root():
    return {
        "service": "IPA Platform API",
        "version": "0.1.0",
        "mode": "local-development",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}
```

#### 子任務
1. [ ] 創建 workflow schemas
2. [ ] 創建 workflow router (CRUD)
3. [ ] 在 main.py 註冊 router
4. [ ] 測試所有 endpoints
5. [ ] 驗證 Swagger UI 顯示正確

---

## 📈 Sprint 進度追蹤

### Daily Standup
- **時間**: 每天上午 10:00
- **時長**: 15 分鐘

### 燃盡圖目標
| 天數 | 剩餘點數 | 完成率 |
|------|---------|--------|
| Day 1 | 18 | 0% |
| Day 2 | 13 | 28% (S0-1 完成) |
| Day 3 | 8 | 56% (S0-2 完成) |
| Day 4 | 5 | 72% (S0-3 完成) |
| Day 5 | 0 | 100% (全部完成) |

---

## ✅ Definition of Done

### Code Quality
- [ ] 代碼通過 black, isort, flake8 檢查
- [ ] 類型提示完整 (mypy)
- [ ] 無安全漏洞

### Functionality
- [ ] 所有驗收標準達成
- [ ] 本地環境測試通過
- [ ] Swagger 文檔可訪問
- [ ] Health check 正常

### Documentation
- [ ] README 更新
- [ ] API 文檔完整
- [ ] 代碼註釋清晰

### Testing
- [ ] 單元測試覆蓋率 > 80%
- [ ] 手動測試通過
- [ ] Postman collection 創建

---

## 🚨 風險緩解

### 風險 1: Docker 環境問題
- **緩解**: 提供詳細的故障排除文檔
- **備案**: 使用本地 Python 虛擬環境

### 風險 2: RabbitMQ 集成複雜度
- **緩解**: 先實現基礎功能，高級特性後續迭代
- **備案**: 暫時使用內存隊列

---

## 📚 參考資源

- [本地開發指南](../local-development-guide.md)
- [Docker Compose 文件](../../../docker-compose.yml)
- [Backend README](../../../backend/README.md)
- [CONTRIBUTING.md](../../../CONTRIBUTING.md)

---

**狀態**: In Progress  
**上次更新**: 2025-11-20  
**更新人**: GitHub Copilot
