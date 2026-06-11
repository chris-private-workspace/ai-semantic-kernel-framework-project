# Sprint 0: 基礎設施建設

**Sprint 目標**: 建立完整的開發環境和 CI/CD 基礎設施
**週期**: Week 1-2 (2 週)
**Story Points**: 34 點

---

## Sprint 概覽

### 目標
1. 建立本地開發環境 (Docker Compose)
2. 配置 CI/CD Pipeline
3. 設置數據庫和緩存基礎設施
4. 建立代碼品質標準和工具
5. 準備 Azure 雲端資源

### 成功標準
- [ ] 開發者可在 30 分鐘內啟動完整開發環境
- [ ] CI Pipeline 可自動運行測試和品質檢查
- [ ] 數據庫遷移系統正常運作
- [ ] 代碼品質工具 (Black, isort, flake8, mypy) 配置完成
- [ ] Azure 資源 (App Service, PostgreSQL, Redis) 已創建

---

## 技術規格

### 開發環境架構

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Compose                        │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │ PostgreSQL  │  │    Redis    │  │   RabbitMQ      │ │
│  │   16+       │  │     7+      │  │   (Local Dev)   │ │
│  │  Port:5432  │  │  Port:6379  │  │   Port:5672     │ │
│  └─────────────┘  └─────────────┘  └─────────────────┘ │
│                                                          │
│  ┌─────────────────────────────────────────────────────┐│
│  │              FastAPI Backend                         ││
│  │              Port: 8000                              ││
│  │              Hot Reload Enabled                      ││
│  └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

### 技術棧版本要求

| 組件 | 版本 | 用途 |
|------|------|------|
| Python | 3.11+ | 後端運行時 |
| PostgreSQL | 16+ | 主數據存儲 |
| Redis | 7+ | 緩存、會話 |
| Docker | 24+ | 容器化 |
| Docker Compose | 2.20+ | 本地編排 |
| Node.js | 18+ | 前端工具鏈 |

### Agent Framework 依賴

```bash
# 核心依賴
pip install agent-framework --pre  # Microsoft Agent Framework (Preview)

# Azure 集成
pip install agent-framework[azure]  # Azure OpenAI 支持

# 開發依賴
pip install pytest pytest-asyncio pytest-cov
pip install black isort flake8 mypy
```

---

## User Stories

### S0-1: 本地開發環境 (13 點)

**描述**: 作為開發者，我需要一個完整的本地開發環境，以便快速開始開發工作。

**驗收標準**:
- [ ] Docker Compose 配置包含所有服務 (PostgreSQL, Redis, RabbitMQ)
- [ ] 環境變量模板 (.env.example) 已創建
- [ ] 健康檢查端點 (/health) 可用
- [ ] 數據持久化配置正確
- [ ] 開發者文檔包含完整啟動指南

**技術任務**:

1. **docker-compose.yml 配置**
```yaml
version: '3.8'
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
    ports:
      - "${DB_PORT}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER} -d ${DB_NAME}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    ports:
      - "${REDIS_PORT}:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  rabbitmq:
    image: rabbitmq:3-management
    environment:
      RABBITMQ_DEFAULT_USER: ${RABBITMQ_USER}
      RABBITMQ_DEFAULT_PASS: ${RABBITMQ_PASSWORD}
    ports:
      - "${RABBITMQ_PORT}:5672"
      - "15672:15672"  # Management UI
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    healthcheck:
      test: rabbitmq-diagnostics -q ping
      interval: 30s
      timeout: 30s
      retries: 3

volumes:
  postgres_data:
  redis_data:
  rabbitmq_data:
```

2. **環境變量配置 (.env.example)**
```bash
# Database
DB_NAME=ipa_platform
DB_USER=ipa_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

# RabbitMQ (Local Dev)
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest

# Azure OpenAI (Required for Agent Framework)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o

# Application
APP_ENV=development
LOG_LEVEL=DEBUG
SECRET_KEY=your_secret_key_for_jwt
```

3. **數據庫初始化腳本 (scripts/init-db.sql)**
```sql
-- 創建擴展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 基礎表結構
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    code TEXT,
    config JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'draft',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS workflows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    agent_id UUID REFERENCES agents(id),
    trigger_type VARCHAR(50),
    trigger_config JSONB DEFAULT '{}',
    graph_definition JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'draft',
    version INTEGER DEFAULT 1,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id UUID REFERENCES workflows(id) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    result JSONB,
    error TEXT,
    llm_calls INTEGER DEFAULT 0,
    llm_tokens INTEGER DEFAULT 0,
    llm_cost DECIMAL(10, 4) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS checkpoints (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    execution_id UUID REFERENCES executions(id) NOT NULL,
    step VARCHAR(255) NOT NULL,
    state JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    approved_by UUID REFERENCES users(id),
    feedback TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    execution_id UUID REFERENCES executions(id),
    action VARCHAR(255) NOT NULL,
    actor VARCHAR(255),
    actor_type VARCHAR(50),
    details JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_executions_workflow_id ON executions(workflow_id);
CREATE INDEX IF NOT EXISTS idx_executions_status ON executions(status);
CREATE INDEX IF NOT EXISTS idx_checkpoints_execution_id ON checkpoints(execution_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_execution_id ON audit_logs(execution_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
```

---

### S0-2: FastAPI 專案結構 (8 點)

**描述**: 作為開發者，我需要一個規範化的 FastAPI 專案結構，以便團隊協作開發。

**驗收標準**:
- [ ] 專案結構符合 Python 最佳實踐
- [ ] 依賴管理使用 pyproject.toml
- [ ] 配置管理支持多環境
- [ ] 日誌系統配置完成
- [ ] 錯誤處理中間件就緒

**專案結構**:
```
backend/
├── src/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py           # API 路由聚合
│   │       ├── workflows/          # 工作流 API
│   │       ├── agents/             # Agent API
│   │       ├── executions/         # 執行 API
│   │       └── checkpoints/        # 檢查點 API
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py               # 配置管理
│   │   ├── security.py             # 安全相關
│   │   └── logging.py              # 日誌配置
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── workflows/              # 工作流領域
│   │   ├── agents/                 # Agent 領域
│   │   └── executions/             # 執行領域
│   └── infrastructure/
│       ├── __init__.py
│       ├── database/               # 數據庫相關
│       ├── cache/                  # 緩存相關
│       └── messaging/              # 消息隊列
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # pytest fixtures
│   ├── unit/
│   └── integration/
├── main.py                         # 應用入口
├── pyproject.toml                  # 項目配置
└── requirements.txt                # 依賴列表
```

**技術任務**:

1. **pyproject.toml 配置**
```toml
[project]
name = "ipa-platform"
version = "0.1.0"
description = "Intelligent Process Automation Platform"
requires-python = ">=3.11"

[tool.black]
line-length = 100
target-version = ['py311']
include = '\.pyi?$'
extend-exclude = '''
/(
    \.git
    | \.venv
    | migrations
)/
'''

[tool.isort]
profile = "black"
line_length = 100
skip_gitignore = true

[tool.mypy]
python_version = "3.11"
strict = true
ignore_missing_imports = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_functions = "test_*"
asyncio_mode = "auto"
addopts = "-v --cov=src --cov-report=term-missing"

[tool.coverage.run]
source = ["src"]
omit = ["*/tests/*", "*/__pycache__/*"]

[tool.coverage.report]
fail_under = 80
```

2. **配置管理 (src/core/config.py)**
```python
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """應用配置"""

    # 環境
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = Field(default=True)

    # 數據庫
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "ipa_platform"
    db_user: str = "ipa_user"
    db_password: str = ""

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""

    @property
    def redis_url(self) -> str:
        return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}"

    # Azure OpenAI
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_deployment_name: str = "gpt-4o"

    # 安全
    secret_key: str = ""
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # 日誌
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

3. **應用入口 (main.py)**
```python
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.v1.router import api_router
from src.core.config import get_settings
from src.core.logging import setup_logging
from src.infrastructure.database.session import init_db, close_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """應用生命週期管理"""
    # 啟動
    setup_logging()
    await init_db()
    yield
    # 關閉
    await close_db()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="IPA Platform API",
        description="Intelligent Process Automation Platform",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else ["https://your-domain.com"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 路由
    app.include_router(api_router, prefix="/api/v1")

    # 健康檢查
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "version": "0.1.0"}

    return app


app = create_app()
```

---

### S0-3: CI/CD Pipeline (8 點)

**描述**: 作為開發團隊，我們需要自動化的 CI/CD Pipeline，以確保代碼品質。

**驗收標準**:
- [ ] GitHub Actions 配置完成
- [ ] PR 觸發自動測試
- [ ] 代碼品質檢查 (lint, type check) 集成
- [ ] 測試覆蓋率報告生成
- [ ] 主分支合併觸發部署 (staging)

**GitHub Actions 配置** (.github/workflows/ci.yml):
```yaml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

env:
  PYTHON_VERSION: "3.11"

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install black isort flake8 mypy

      - name: Run Black
        run: cd backend && black --check .

      - name: Run isort
        run: cd backend && isort --check-only .

      - name: Run flake8
        run: cd backend && flake8 .

      - name: Run mypy
        run: cd backend && mypy src/

  test:
    runs-on: ubuntu-latest
    needs: lint

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_password
          POSTGRES_DB: test_db
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov

      - name: Run tests
        env:
          DB_HOST: localhost
          DB_PORT: 5432
          DB_NAME: test_db
          DB_USER: test_user
          DB_PASSWORD: test_password
          REDIS_HOST: localhost
          REDIS_PORT: 6379
        run: |
          cd backend
          pytest --cov=src --cov-report=xml --cov-report=term-missing

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: backend/coverage.xml
          fail_ci_if_error: true

  build:
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v4

      - name: Build Docker image
        run: |
          docker build -t ipa-platform:${{ github.sha }} -f backend/Dockerfile backend/

      - name: Push to registry
        if: github.event_name == 'push'
        run: |
          echo "Push to Azure Container Registry"
          # az acr login --name ${{ secrets.ACR_NAME }}
          # docker push ${{ secrets.ACR_NAME }}.azurecr.io/ipa-platform:${{ github.sha }}
```

---

### S0-4: Azure 資源配置 (5 點)

**描述**: 作為 DevOps，我需要配置 Azure 雲端資源，以支持 MVP 部署。

**驗收標準**:
- [ ] Azure Resource Group 已創建
- [ ] Azure App Service Plan 已配置
- [ ] Azure Database for PostgreSQL 已創建
- [ ] Azure Cache for Redis 已創建
- [ ] Azure Key Vault 已配置

**Azure 資源清單**:

| 資源類型 | SKU | 用途 |
|---------|-----|------|
| App Service Plan | B1 (MVP) → S1 (Production) | 應用託管 |
| App Service | - | FastAPI 應用 |
| PostgreSQL Flexible Server | Burstable B1ms | 數據庫 |
| Azure Cache for Redis | Basic C0 | 緩存 |
| Azure Service Bus | Basic | 消息隊列 |
| Key Vault | Standard | 密鑰管理 |
| Application Insights | - | 監控 |

**Terraform 配置** (infrastructure/main.tf):
```hcl
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

variable "environment" {
  default = "dev"
}

variable "location" {
  default = "East Asia"
}

resource "azurerm_resource_group" "main" {
  name     = "rg-ipa-platform-${var.environment}"
  location = var.location
}

# App Service Plan
resource "azurerm_service_plan" "main" {
  name                = "asp-ipa-platform-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  os_type             = "Linux"
  sku_name            = "B1"
}

# PostgreSQL Flexible Server
resource "azurerm_postgresql_flexible_server" "main" {
  name                   = "psql-ipa-platform-${var.environment}"
  resource_group_name    = azurerm_resource_group.main.name
  location               = azurerm_resource_group.main.location
  version                = "16"
  administrator_login    = "ipaadmin"
  administrator_password = var.db_password
  zone                   = "1"
  storage_mb             = 32768
  sku_name               = "B_Standard_B1ms"
}

# Redis Cache
resource "azurerm_redis_cache" "main" {
  name                = "redis-ipa-platform-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  capacity            = 0
  family              = "C"
  sku_name            = "Basic"
  enable_non_ssl_port = false
  minimum_tls_version = "1.2"
}

# Key Vault
resource "azurerm_key_vault" "main" {
  name                = "kv-ipa-platform-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"

  purge_protection_enabled = false
}
```

---

## 時間規劃

### Week 1 (Day 1-5)

| 日期 | 任務 | 負責人 | 產出 |
|------|------|--------|------|
| Day 1-2 | S0-1: Docker Compose + 環境變量 | DevOps | docker-compose.yml, .env.example |
| Day 2-3 | S0-1: 數據庫初始化腳本 | Backend | init-db.sql |
| Day 3-4 | S0-2: FastAPI 專案結構 | Backend | 完整專案骨架 |
| Day 4-5 | S0-2: 配置管理 + 日誌 | Backend | config.py, logging.py |

### Week 2 (Day 6-10)

| 日期 | 任務 | 負責人 | 產出 |
|------|------|--------|------|
| Day 6-7 | S0-3: GitHub Actions CI | DevOps | ci.yml |
| Day 7-8 | S0-3: 測試 + 覆蓋率集成 | Backend | pytest 配置 |
| Day 8-9 | S0-4: Azure 資源配置 | DevOps | Terraform 腳本 |
| Day 9-10 | 集成測試 + 文檔完善 | 全員 | 開發者指南 |

---

## 風險與緩解

| 風險 | 可能性 | 影響 | 緩解措施 |
|------|--------|------|---------|
| Docker 環境不一致 | 中 | 高 | 統一 Docker 版本，使用 .env 模板 |
| Azure 資源配額限制 | 低 | 中 | 提前申請配額增加 |
| CI Pipeline 過慢 | 中 | 中 | 使用緩存，優化測試並行度 |
| Agent Framework 版本變更 | 高 | 高 | 鎖定版本，監控 Release Notes |

---

## 完成定義 (Definition of Done)

1. **代碼完成**
   - [ ] 所有代碼已提交並通過 PR Review
   - [ ] 代碼符合 Black, isort, flake8 標準
   - [ ] 類型檢查 (mypy) 通過

2. **測試完成**
   - [ ] 單元測試覆蓋率 >= 80%
   - [ ] 集成測試通過
   - [ ] 健康檢查端點可用

3. **文檔完成**
   - [ ] README 包含啟動指南
   - [ ] 環境變量說明完整
   - [ ] API 文檔 (Swagger) 可訪問

4. **基礎設施就緒**
   - [ ] Docker Compose 可一鍵啟動
   - [ ] CI Pipeline 正常運行
   - [ ] Azure 資源已創建

---

## 相關文檔

- [Sprint 0 Checklist](./sprint-0-checklist.md)
- [本地開發指南](../local-development-guide.md)
- [技術架構](../../02-architecture/technical-architecture.md)
- [Agent Framework 參考](../../../reference/agent-framework/)
