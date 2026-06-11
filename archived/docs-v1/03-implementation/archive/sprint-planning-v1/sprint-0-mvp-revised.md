# Sprint 0: Infrastructure & Foundation - MVP 調整版

> ⚠️ **重要提示**: 本文檔為 **Phase 2 (雲端部署)** 參考文檔  
> 📄 **開發階段請使用**: [Sprint 0 本地開發版](./sprint-0-local-development.md)  
> 🔄 **適用時機**: Sprint 4+ 集成測試/生產環境部署

**版本**: 1.1 (MVP 調整版 - Phase 2 Reference)  
**創建日期**: 2025-11-20  
**Sprint 期間**: 2025-11-25 至 2025-12-06 (2週)  
**團隊規模**: 8人 (3後端, 2前端, 1 DevOps, 1 QA, 1 PO)

---

## 🎯 調整說明

基於 MVP 快速上線的策略，Sprint 0 進行以下調整：

### 主要變更

#### Phase 1: 本地開發（Sprint 0-3）✅ 當前階段
1. **開發環境**: Docker Compose（完全本地）
2. **消息隊列**: **RabbitMQ** (本地 Docker 容器)
3. **認證方式**: **Mock Authentication** (無需 Azure AD)
4. **日誌方案**: **Console Logging** (標準輸出)
5. **成本**: **$0 Azure 費用** (僅 OpenAI API ~$20/月)

#### Phase 2: 雲端部署（Sprint 4+ 集成測試/生產）
1. **部署平台**: Kubernetes (AKS) → **Azure App Service**
2. **消息隊列**: RabbitMQ → **Azure Service Bus**
3. **認證方式**: Mock → **Azure AD OAuth 2.0**
4. **監控方案**: Console → **Application Insights + Azure Monitor**
5. **成本**: ~$123-143/月

### 調整理由
- ✅ **零 Azure 成本**: 開發階段完全本地，省下 3 個月 $114 訂閱費
- ✅ **快速迭代**: 無網絡延遲，本地調試方便
- ✅ **降低複雜度**: 無需學習 Kubernetes，專注業務邏輯
- ✅ **離線開發**: 不依賴網絡連接，適合任何環境
- ✅ **平滑遷移**: 代碼無需修改，僅切換環境變量

### 後期擴展路徑
當 MVP 驗證成功，業務需要更高彈性時，可遷移到 Kubernetes：
- 更細粒度的服務拆分
- 獨立擴展每個微服務
- 藍綠部署/金絲雀發布
- 跨區域高可用

---

## 📊 調整後的 Story Points

**總計劃點數**: 33 (調整前: 42 → 38 → 33)  
**減少原因**: 
- 完全本地開發，無需 Azure 資源配置
- 使用 RabbitMQ 替代 Service Bus（更簡單）
- Mock 認證替代 Azure AD（開發階段）
- Console 日誌替代 Application Insights

**按優先級分配**:
- P0 (Critical): 28 點 (85%)
- P1 (High): 5 點 (15%)

**按團隊分配**:
- DevOps: 13 點 (39%)
- Backend: 20 點 (61%)

---

## 🎯 調整後的 Sprint Backlog

### S0-1: Development Environment Setup ✅ (無變更)
**Story Points**: 5  
**優先級**: P0 - Critical  
**負責人**: DevOps  
**依賴**: 無

#### 描述
配置**完全本地**開發環境，使用 Docker Compose 編排所有服務，無需任何 Azure 資源。

#### 驗收標準
- [x] Docker Compose 配置完成，包含: ✅ **已完成**
  - PostgreSQL 16 (本地容器)
  - Redis 7 (本地容器)
  - **RabbitMQ 3.12** (本地容器，替代 Azure Service Bus)
  - Backend API (Python FastAPI)
- [x] README 包含本地環境設置指南 (< 15 分鐘完成) ✅ **已完成**
- [x] 環境變量模板 (.env.example) ✅ **已完成**
- [x] 本地開發指南 (local-development-guide.md) ✅ **已完成**
- [ ] RabbitMQ Management UI 可訪問 (http://localhost:15672)

#### 技術實現
```yaml
# docker-compose.yml
version: '3.8'
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: ipa_platform
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
  
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3
  
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/ipa_platform
      REDIS_URL: redis://redis:6379/0
      AZURE_SERVICE_BUS_CONNECTION_STRING: ${SERVICE_BUS_CONN_STR}
    depends_on:
      - postgres
      - redis
    volumes:
      - ./backend:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

volumes:
  postgres_data:
  redis_data:
```

---

### S0-2: Azure App Service Setup 🆕 (替代 Kubernetes)
**Story Points**: 5 (原 8 點，降低複雜度)  
**優先級**: P0 - Critical  
**負責人**: DevOps  
**依賴**: 無

#### 描述
在 Azure 創建 App Service Plan 和 App Service，配置 Staging 和 Production 環境。

#### 驗收標準
- [ ] Azure App Service Plan 創建完成
  - Plan: Standard S1 (1 vCore, 1.75GB RAM, $75/月)
- [ ] 2 個 App Service 實例
  - **ipa-backend-staging**: 測試環境
  - **ipa-backend-prod**: 生產環境
- [ ] 配置 Deployment Slots (staging → production swap)
- [ ] 啟用 Application Insights
- [ ] 配置自動擴展規則 (CPU > 70% 時擴展)
- [ ] 設置健康檢查端點 (/health)

#### 技術實現
```bash
# Azure CLI 命令
az group create --name rg-ipa-platform --location eastus

# 創建 App Service Plan
az appservice plan create \
  --name plan-ipa-platform \
  --resource-group rg-ipa-platform \
  --sku S1 \
  --is-linux

# 創建 Backend App Service (Staging)
az webapp create \
  --name ipa-backend-staging \
  --resource-group rg-ipa-platform \
  --plan plan-ipa-platform \
  --runtime "PYTHON:3.11"

# 創建 Backend App Service (Production)
az webapp create \
  --name ipa-backend-prod \
  --resource-group rg-ipa-platform \
  --plan plan-ipa-platform \
  --runtime "PYTHON:3.11"

# 配置 Application Insights
az monitor app-insights component create \
  --app ipa-platform-insights \
  --location eastus \
  --resource-group rg-ipa-platform \
  --application-type web

# 啟用自動擴展
az monitor autoscale create \
  --resource ipa-backend-prod \
  --resource-group rg-ipa-platform \
  --resource-type Microsoft.Web/serverfarms \
  --name autoscale-ipa \
  --min-count 1 \
  --max-count 5 \
  --count 1

az monitor autoscale rule create \
  --resource ipa-backend-prod \
  --resource-group rg-ipa-platform \
  --autoscale-name autoscale-ipa \
  --condition "Percentage CPU > 70 avg 5m" \
  --scale out 1
```

#### 子任務
1. [ ] 創建 Azure Resource Group
2. [ ] 創建 App Service Plan
3. [ ] 創建 Staging 和 Production App Service
4. [ ] 配置 Deployment Slots
5. [ ] 啟用 Application Insights
6. [ ] 配置自動擴展規則
7. [ ] 設置環境變量 (App Settings)
8. [ ] 測試部署流程

---

### S0-3: CI/CD Pipeline for App Service 🔄 (調整)
**Story Points**: 5 (原 8 點，App Service 部署更簡單)  
**優先級**: P0 - Critical  
**負責人**: DevOps  
**依賴**: S0-2

#### 描述
創建 GitHub Actions 流水線，實現自動構建、測試、部署到 Azure App Service。

#### 驗收標準
- [ ] GitHub Actions workflow 配置完成
  - `.github/workflows/ci-cd.yml`
- [ ] Pipeline 階段:
  1. Build: Docker image 構建
  2. Test: pytest 單元測試 (coverage > 80%)
  3. Security Scan: Trivy, Bandit, Safety
  4. Deploy to Staging: 自動部署
  5. Smoke Test: 基本健康檢查
  6. Deploy to Production: 手動批准
- [ ] Azure Service Principal 配置完成 (用於 CI/CD 認證)
- [ ] Secrets 配置在 GitHub Secrets

#### 技術實現
```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  AZURE_WEBAPP_NAME: ipa-backend-staging
  PYTHON_VERSION: '3.11'

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov bandit safety
      
      - name: Run tests
        run: |
          pytest --cov=. --cov-report=xml --cov-report=term
      
      - name: Security scan - Bandit
        run: bandit -r . -f json -o bandit-report.json
      
      - name: Security scan - Safety
        run: safety check --json
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
  
  deploy-staging:
    needs: build-and-test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    steps:
      - uses: actions/checkout@v4
      
      - name: Login to Azure
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}
      
      - name: Deploy to App Service (Staging)
        uses: azure/webapps-deploy@v2
        with:
          app-name: ${{ env.AZURE_WEBAPP_NAME }}
          package: .
      
      - name: Run smoke tests
        run: |
          curl -f https://ipa-backend-staging.azurewebsites.net/health || exit 1
  
  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment:
      name: production
      url: https://ipa-backend-prod.azurewebsites.net
    steps:
      - uses: actions/checkout@v4
      
      - name: Login to Azure
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}
      
      - name: Deploy to App Service (Production)
        uses: azure/webapps-deploy@v2
        with:
          app-name: ipa-backend-prod
          package: .
      
      - name: Run smoke tests
        run: |
          curl -f https://ipa-backend-prod.azurewebsites.net/health || exit 1
```

#### 子任務
1. [ ] 創建 Azure Service Principal
2. [ ] 配置 GitHub Secrets (AZURE_CREDENTIALS)
3. [ ] 編寫 CI/CD workflow 文件
4. [ ] 配置測試階段 (pytest, coverage)
5. [ ] 配置安全掃描 (Trivy, Bandit, Safety)
6. [ ] 配置 Staging 部署
7. [ ] 配置 Production 部署 (需手動批准)
8. [ ] 測試完整 CI/CD 流程

---

### S0-4: Database Infrastructure ✅ (無變更)
**Story Points**: 5  
**優先級**: P0 - Critical  
**負責人**: Backend  
**依賴**: 無

#### 描述
設置 Azure Database for PostgreSQL Flexible Server，初始化 schema，配置 Alembic 遷移框架。

#### 驗收標準
- [ ] Azure PostgreSQL Flexible Server 創建完成
  - SKU: Burstable B1ms (1 vCore, 2GB RAM, $12/月)
  - PostgreSQL 版本: 16
  - 備份保留: 7 天
- [ ] Database 初始化
  - Database name: `ipa_platform`
  - User: `ipa_admin`
- [ ] Alembic 遷移框架配置
  - `alembic.ini` 配置
  - `migrations/` 目錄結構
  - 初始遷移腳本 (create tables)
- [ ] 連接池配置 (SQLAlchemy)
- [ ] SSL 連接強制啟用

#### 技術實現
```bash
# 創建 PostgreSQL Server
az postgres flexible-server create \
  --name ipa-postgres-server \
  --resource-group rg-ipa-platform \
  --location eastus \
  --admin-user ipa_admin \
  --admin-password <STRONG_PASSWORD> \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --version 16 \
  --storage-size 32 \
  --backup-retention 7 \
  --public-access 0.0.0.0-255.255.255.255

# 創建數據庫
az postgres flexible-server db create \
  --resource-group rg-ipa-platform \
  --server-name ipa-postgres-server \
  --database-name ipa_platform
```

```python
# backend/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # 檢查連接健康
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

```python
# backend/models/workflow.py
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON
from sqlalchemy.sql import func
from database import Base

class Workflow(Base):
    __tablename__ = "workflows"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    config = Column(JSON, nullable=False)
    version = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(255))
    status = Column(String(50), default='draft')
```

#### 子任務
1. [ ] 創建 Azure PostgreSQL Server
2. [ ] 創建數據庫和用戶
3. [ ] 配置防火牆規則 (允許 Azure services)
4. [ ] 安裝 Alembic (`pip install alembic`)
5. [ ] 初始化 Alembic (`alembic init migrations`)
6. [ ] 配置 SQLAlchemy 連接池
7. [ ] 創建基礎 model (Workflow, Execution, Agent)
8. [ ] 生成初始遷移腳本
9. [ ] 測試數據庫連接和遷移

---

### S0-5: Redis Cache Setup ✅ (無變更)
**Story Points**: 3  
**優先級**: P0 - Critical  
**負責人**: Backend  
**依賴**: 無

#### 描述
設置 Azure Cache for Redis，配置連接池和緩存策略。

#### 驗收標準
- [ ] Azure Cache for Redis 創建完成
  - SKU: Basic C0 (250MB, $16/月)
- [ ] Redis 客戶端配置 (redis-py)
- [ ] 緩存策略實現:
  - Workflow 配置緩存 (TTL: 5 分鐘)
  - Execution 狀態緩存 (TTL: 1 分鐘)
  - Session 存儲 (TTL: 30 分鐘)

#### 技術實現
```bash
# 創建 Redis Cache
az redis create \
  --name ipa-redis-cache \
  --resource-group rg-ipa-platform \
  --location eastus \
  --sku Basic \
  --vm-size c0
```

```python
# backend/cache.py
import redis
import os
import json
from typing import Optional

REDIS_URL = os.getenv("REDIS_URL")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

class Cache:
    @staticmethod
    def get(key: str) -> Optional[dict]:
        value = redis_client.get(key)
        return json.loads(value) if value else None
    
    @staticmethod
    def set(key: str, value: dict, ttl: int = 300):
        redis_client.setex(key, ttl, json.dumps(value))
    
    @staticmethod
    def delete(key: str):
        redis_client.delete(key)
    
    @staticmethod
    def invalidate_pattern(pattern: str):
        for key in redis_client.scan_iter(pattern):
            redis_client.delete(key)

# 使用示例
def get_workflow(workflow_id: str):
    cache_key = f"workflow:{workflow_id}"
    cached = Cache.get(cache_key)
    if cached:
        return cached
    
    workflow = db.query(Workflow).filter_by(id=workflow_id).first()
    Cache.set(cache_key, workflow.to_dict(), ttl=300)
    return workflow
```

---

### S0-6: Azure Service Bus Setup 🆕 (替代 RabbitMQ)
**Story Points**: 3  
**優先級**: P0 - Critical  
**負責人**: Backend  
**依賴**: 無

#### 描述
設置 Azure Service Bus，創建 Queues 和 Topics，配置 Python SDK。

#### 驗收標準
- [ ] Azure Service Bus Namespace 創建
  - SKU: Basic ($10/月)
- [ ] Queues 創建:
  - `execution-queue`: 執行任務隊列
  - `notification-queue`: 通知隊列
  - `dlq-execution`: Dead Letter Queue for execution failures
- [ ] Python SDK 配置 (azure-servicebus)
- [ ] 重試機制實現 (指數退避)
- [ ] Dead Letter Queue 處理邏輯

#### 技術實現
```bash
# 創建 Service Bus Namespace
az servicebus namespace create \
  --name ipa-servicebus \
  --resource-group rg-ipa-platform \
  --location eastus \
  --sku Basic

# 創建 Queues
az servicebus queue create \
  --name execution-queue \
  --namespace-name ipa-servicebus \
  --resource-group rg-ipa-platform \
  --max-delivery-count 5 \
  --lock-duration PT5M

az servicebus queue create \
  --name notification-queue \
  --namespace-name ipa-servicebus \
  --resource-group rg-ipa-platform
```

```python
# backend/message_queue.py
from azure.servicebus import ServiceBusClient, ServiceBusMessage
import os
import json

SERVICE_BUS_CONN_STR = os.getenv("AZURE_SERVICE_BUS_CONNECTION_STRING")
servicebus_client = ServiceBusClient.from_connection_string(SERVICE_BUS_CONN_STR)

class MessageQueue:
    @staticmethod
    def send_message(queue_name: str, message: dict):
        with servicebus_client:
            sender = servicebus_client.get_queue_sender(queue_name=queue_name)
            with sender:
                msg = ServiceBusMessage(json.dumps(message))
                sender.send_messages(msg)
    
    @staticmethod
    def receive_messages(queue_name: str, max_messages: int = 10):
        with servicebus_client:
            receiver = servicebus_client.get_queue_receiver(queue_name=queue_name)
            with receiver:
                messages = receiver.receive_messages(
                    max_message_count=max_messages,
                    max_wait_time=5
                )
                for msg in messages:
                    try:
                        body = json.loads(str(msg))
                        yield body
                        receiver.complete_message(msg)
                    except Exception as e:
                        print(f"Error processing message: {e}")
                        receiver.abandon_message(msg)

# 使用示例
def trigger_execution(workflow_id: str, params: dict):
    message = {
        "workflow_id": workflow_id,
        "params": params,
        "timestamp": datetime.utcnow().isoformat()
    }
    MessageQueue.send_message("execution-queue", message)
```

#### 子任務
1. [ ] 創建 Service Bus Namespace
2. [ ] 創建 Queues (execution, notification)
3. [ ] 配置 Dead Letter Queue
4. [ ] 安裝 Python SDK (`pip install azure-servicebus`)
5. [ ] 實現消息發送邏輯
6. [ ] 實現消息接收邏輯
7. [ ] 配置重試機制
8. [ ] 測試消息流

---

### S0-7: Authentication Framework ✅ (無變更)
**Story Points**: 8  
**優先級**: P0 - Critical  
**負責人**: Backend  
**依賴**: S0-4

#### 描述
實現 OAuth 2.0 + JWT 身份驗證，集成 Azure AD。

#### 驗收標準
- [ ] OAuth 2.0 授權流程實現
- [ ] JWT Token 生成和驗證
- [ ] Azure AD 集成 (使用 MSAL)
- [ ] RBAC 角色定義 (Admin, User, Viewer)
- [ ] API 端點保護 (require_auth decorator)
- [ ] Token 刷新機制

#### 技術實現
```python
# backend/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
import os

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return username

def require_role(allowed_roles: list):
    def decorator(func):
        async def wrapper(*args, current_user = Depends(get_current_user), **kwargs):
            if current_user.role not in allowed_roles:
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# 使用示例
@app.post("/workflows")
@require_role(["admin", "user"])
async def create_workflow(workflow: WorkflowCreate, current_user = Depends(get_current_user)):
    # ...
```

---

### S0-8: Monitoring Setup (Hybrid) 🔄 (調整)
**Story Points**: 5  
**優先級**: P1 - High  
**負責人**: DevOps  
**依賴**: S0-2

#### 描述
配置混合監控方案：Azure Monitor (基礎) + Prometheus (自定義業務指標)。

#### 驗收標準
- [ ] Application Insights 配置完成
  - 自動收集 HTTP 請求/響應
  - 異常追蹤
  - 依賴追蹤 (DB, Redis, Service Bus)
  - 自定義事件記錄
- [ ] Azure Monitor 告警規則
  - CPU > 80% for 5 mins
  - Memory > 85% for 5 mins
  - HTTP 5xx errors > 10 in 5 mins
- [ ] Prometheus + Grafana 部署 (可選，用於自定義指標)
  - 部署在 Azure Container Instance
  - Grafana Dashboard 配置
  - 業務指標採集 (Workflow success rate, LLM API cost)

#### 技術實現
```python
# backend/main.py - Application Insights 集成
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace import config_integration
import logging

# 配置 Application Insights
config_integration.trace_integrations(['requests', 'sqlalchemy', 'redis'])

logger = logging.getLogger(__name__)
logger.addHandler(AzureLogHandler(
    connection_string=os.getenv('APPLICATIONINSIGHTS_CONNECTION_STRING')
))

# 自定義事件記錄
from opencensus.ext.azure import metrics_exporter
from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import measure as measure_module
from opencensus.stats import stats as stats_module
from opencensus.stats import view as view_module

# 定義自定義指標
workflow_execution_measure = measure_module.MeasureInt(
    "workflow_executions",
    "Number of workflow executions",
    "executions"
)

# 記錄自定義指標
def record_workflow_execution(workflow_id: str, success: bool):
    mmap = stats_module.stats.stats_recorder.new_measurement_map()
    mmap.measure_int_put(workflow_execution_measure, 1)
    mmap.record()
    
    logger.info(f"Workflow executed: {workflow_id}, success: {success}", extra={
        'custom_dimensions': {
            'workflow_id': workflow_id,
            'success': success
        }
    })
```

```bash
# 可選: 部署 Prometheus + Grafana (自定義指標)
az container create \
  --name prometheus \
  --resource-group rg-ipa-platform \
  --image prom/prometheus:latest \
  --cpu 1 \
  --memory 1 \
  --ports 9090 \
  --environment-variables PROM_CONFIG_URL=https://...

az container create \
  --name grafana \
  --resource-group rg-ipa-platform \
  --image grafana/grafana:latest \
  --cpu 1 \
  --memory 1 \
  --ports 3000
```

---

### S0-9: Application Insights Logging 🆕 (替代 ELK)
**Story Points**: 3 (原 5 點，內建集成更簡單)  
**優先級**: P1 - High  
**負責人**: DevOps  
**依賴**: S0-2

#### 描述
配置 Application Insights 作為集中式日誌系統，無需部署額外基礎設施。

#### 驗收標準
- [ ] Application Insights 完整配置
- [ ] 結構化日誌記錄 (JSON format)
- [ ] 日誌級別配置 (DEBUG/INFO/WARNING/ERROR)
- [ ] Correlation ID 追蹤 (跨服務請求)
- [ ] Log Analytics 查詢示例文檔
- [ ] 日誌保留策略 (90 天，可延長到 730 天)

#### 技術實現
```python
# backend/logging_config.py
import logging
import json
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.tracer import Tracer
from opencensus.trace.samplers import ProbabilitySampler

# 配置日誌格式
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        if hasattr(record, 'custom_dimensions'):
            log_data['custom_dimensions'] = record.custom_dimensions
        return json.dumps(log_data)

# 配置 Application Insights
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = AzureLogHandler(
    connection_string=os.getenv('APPLICATIONINSIGHTS_CONNECTION_STRING')
)
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)

# 配置分布式追蹤
tracer = Tracer(
    exporter=AzureExporter(
        connection_string=os.getenv('APPLICATIONINSIGHTS_CONNECTION_STRING')
    ),
    sampler=ProbabilitySampler(1.0)  # MVP 階段 100% 採樣
)

# 使用示例
logger.info("Workflow execution started", extra={
    'custom_dimensions': {
        'workflow_id': workflow_id,
        'user_id': user_id,
        'execution_id': execution_id
    }
})
```

**Log Analytics 查詢示例 (KQL)**:
```kusto
// 查詢最近 1 小時的錯誤日誌
traces
| where timestamp > ago(1h)
| where severityLevel >= 3  // ERROR and above
| project timestamp, message, customDimensions
| order by timestamp desc

// 查詢特定 Workflow 的執行日誌
traces
| where customDimensions.workflow_id == "workflow-123"
| order by timestamp asc

// 分析 HTTP 請求性能
requests
| where timestamp > ago(1d)
| summarize avg(duration), percentile(duration, 95), count() by name
| order by avg_duration desc
```

---

## 📅 Sprint 0 時間線

```
Week 1 (11/25-11/29):
  Day 1-2: S0-1 (Docker Compose), S0-2 (App Service), S0-4 (Database)
  Day 3-4: S0-5 (Redis), S0-6 (Service Bus), S0-7 (Auth)
  Day 5: S0-3 (CI/CD), S0-8 (Monitoring)

Week 2 (12/02-12/06):
  Day 1-2: S0-3 (CI/CD 完善), S0-9 (Logging)
  Day 3-4: 集成測試，修復問題
  Day 5: Sprint Review, Retrospective, Sprint 1 Planning
```

---

## 🎯 Definition of Done (DoD)

### Sprint 0 整體 DoD
- [ ] 所有 P0 任務完成並驗證
- [ ] 所有開發人員可以在本地運行完整應用棧
- [ ] CI/CD 流水線可以自動部署到 Staging
- [ ] Staging 環境健康檢查通過
- [ ] 基礎監控儀表板可用 (App Insights)
- [ ] 文檔更新 (README, Setup Guide)

### 個別任務 DoD
- [ ] 代碼提交到 `main` 分支
- [ ] 單元測試通過 (if applicable)
- [ ] 代碼審查通過 (1 approver)
- [ ] 文檔更新
- [ ] Demo 給 PO 確認

---

## 🚨 風險與緩解策略

| 風險 | 嚴重性 | 緩解策略 |
|------|--------|---------|
| **Azure 資源配額不足** | High | 提前申請資源配額，準備備用訂閱 |
| **Service Principal 權限問題** | Medium | 使用 Owner 角色測試，後期降級為 Contributor |
| **Application Insights 學習曲線** | Medium | 提供 KQL 查詢示例文檔，安排培訓 |
| **Service Bus 與 RabbitMQ 差異** | Low | 編寫抽象層，便於後期切換 |

---

## 📊 成本估算 (MVP 階段)

| 服務 | SKU | 月成本 |
|------|-----|--------|
| App Service Plan | Standard S1 | $75 |
| PostgreSQL | Burstable B1ms | $12 |
| Redis Cache | Basic C0 | $16 |
| Service Bus | Basic | $10 |
| Application Insights | Pay-as-you-go | $10-30 (estimated) |
| **總計** | | **$123-143** |

對比 Kubernetes 方案 (~$300+/月)，節省 **~55%** 成本。

---

## 📝 備註

1. **後期遷移路徑**: 當 MVP 驗證成功，需要更高彈性時，可以逐步遷移到 Kubernetes，已有的代碼無需大改。
2. **技術債務**: Service Bus 抽象層需要保持與 RabbitMQ 兼容的接口，便於未來切換。
3. **監控擴展**: MVP 階段先用 App Insights，後期可以添加 Prometheus 採集自定義業務指標。
4. **學習資源**: 
   - [Azure App Service 文檔](https://docs.microsoft.com/azure/app-service/)
   - [Application Insights 快速入門](https://docs.microsoft.com/azure/azure-monitor/app/app-insights-overview)
   - [Azure Service Bus Python SDK](https://docs.microsoft.com/azure/service-bus-messaging/service-bus-python-how-to-use-queues)

---

**文檔狀態**: ✅ MVP 調整版完成 (2025-11-20)  
**下一步**: 開始執行 Sprint 0 任務 (2025-11-25)
