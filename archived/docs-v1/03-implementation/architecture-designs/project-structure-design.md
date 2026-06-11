# Project Structure Design
# IPA Platform - 項目文件結構設計

**版本**: 1.0
**日期**: 2025-11-20
**狀態**: 已批准
**負責人**: Architecture Team

---

## 📋 目錄

1. [設計概述](#design-overview)
2. [Backend 結構](#backend-structure)
3. [Frontend 結構](#frontend-structure)
4. [根目錄結構](#root-structure)
5. [創建步驟](#creation-steps)

---

## <a id="design-overview"></a>1. 設計概述

### 設計原則

本項目文件結構基於以下原則設計:

1. **分層架構**: 清晰的 API → Domain → Infrastructure 分層
2. **模塊化**: 每個功能領域獨立模塊
3. **可測試性**: 測試目錄與源代碼結構對應
4. **領域驅動設計 (DDD)**: Domain Layer 反映業務領域
5. **依賴倒置**: 依賴抽象接口而非具體實現

### 技術棧映射

| 層級 | 技術棧 | 目的 |
|------|--------|------|
| **Presentation** | React 18 + TypeScript | Web UI |
| **Application** | FastAPI + Pydantic | API Layer |
| **Domain** | Python Classes | 業務邏輯 |
| **Infrastructure** | SQLAlchemy, Redis, RabbitMQ | 數據持久化和外部集成 |

---

## <a id="backend-structure"></a>2. Backend 結構設計

### 完整目錄樹

```
backend/
├── src/                          # 源代碼根目錄
│   ├── __init__.py
│   ├── main.py                   # FastAPI 應用入口
│   │
│   ├── api/                      # API Layer (Application Layer)
│   │   ├── __init__.py
│   │   ├── dependencies.py       # 依賴注入
│   │   ├── middleware.py         # 中間件
│   │   │
│   │   └── v1/                   # API v1
│   │       ├── __init__.py
│   │       ├── router.py         # 主路由聚合
│   │       │
│   │       ├── workflows/        # Workflow API
│   │       │   ├── __init__.py
│   │       │   ├── router.py
│   │       │   ├── schemas.py    # Pydantic models
│   │       │   └── dependencies.py
│   │       │
│   │       ├── executions/       # Execution API
│   │       │   ├── __init__.py
│   │       │   ├── router.py
│   │       │   └── schemas.py
│   │       │
│   │       ├── agents/           # Agent API
│   │       │   ├── __init__.py
│   │       │   ├── router.py
│   │       │   └── schemas.py
│   │       │
│   │       ├── webhooks/         # Webhook receivers (n8n)
│   │       │   ├── __init__.py
│   │       │   └── router.py
│   │       │
│   │       └── auth/             # 認證 API
│   │           ├── __init__.py
│   │           ├── router.py
│   │           └── schemas.py
│   │
│   ├── core/                     # 核心配置和工具
│   │   ├── __init__.py
│   │   ├── config.py             # 配置管理 (Pydantic Settings)
│   │   ├── security.py           # 安全工具 (JWT, OAuth)
│   │   ├── logging.py            # 日誌配置
│   │   └── exceptions.py         # 自定義異常
│   │
│   ├── domain/                   # Domain Layer (DDD)
│   │   ├── __init__.py
│   │   │
│   │   ├── workflows/            # Workflow Domain
│   │   │   ├── __init__.py
│   │   │   ├── entities.py       # Workflow Entity
│   │   │   ├── value_objects.py  # Value Objects
│   │   │   ├── aggregates.py     # Aggregates
│   │   │   ├── repositories.py   # Repository 接口
│   │   │   └── services.py       # Domain Services
│   │   │
│   │   ├── executions/           # Execution Domain
│   │   │   ├── __init__.py
│   │   │   ├── entities.py
│   │   │   ├── state_machine.py  # 狀態機
│   │   │   ├── repositories.py
│   │   │   └── services.py
│   │   │
│   │   └── agents/               # Agent Domain
│   │       ├── __init__.py
│   │       ├── entities.py
│   │       ├── interfaces.py     # IAgent, ITool
│   │       └── services.py
│   │
│   ├── infrastructure/           # Infrastructure Layer
│   │   ├── __init__.py
│   │   │
│   │   ├── database/             # 數據庫
│   │   │   ├── __init__.py
│   │   │   ├── connection.py     # SQLAlchemy engine
│   │   │   ├── session.py        # Session 管理
│   │   │   └── models/           # SQLAlchemy Models
│   │   │       ├── __init__.py
│   │   │       ├── workflow.py
│   │   │       ├── execution.py
│   │   │       ├── agent.py
│   │   │       └── audit_log.py
│   │   │
│   │   ├── cache/                # Redis 緩存
│   │   │   ├── __init__.py
│   │   │   ├── client.py
│   │   │   └── strategies.py     # 緩存策略
│   │   │
│   │   ├── queue/                # RabbitMQ / Service Bus
│   │   │   ├── __init__.py
│   │   │   ├── client.py
│   │   │   ├── publisher.py
│   │   │   └── consumer.py
│   │   │
│   │   ├── repositories/         # Repository 實現
│   │   │   ├── __init__.py
│   │   │   ├── workflow_repo.py
│   │   │   ├── execution_repo.py
│   │   │   └── agent_repo.py
│   │   │
│   │   └── external/             # 外部集成
│   │       ├── __init__.py
│   │       ├── n8n_client.py
│   │       ├── teams_client.py
│   │       └── openai_client.py
│   │
│   ├── services/                 # Application Services
│   │   ├── __init__.py
│   │   ├── workflow_service.py   # Workflow 業務邏輯
│   │   ├── execution_service.py  # Execution 調度
│   │   └── agent_service.py      # Agent 執行
│   │
│   ├── agents/                   # Agent Framework Agents
│   │   ├── __init__.py
│   │   ├── base_agent.py         # 基礎 Agent 類
│   │   ├── react_agent.py        # ReAct Agent
│   │   ├── plan_execute_agent.py # Plan-Execute Agent
│   │   │
│   │   └── tools/                # Agent Tools
│   │       ├── __init__.py
│   │       ├── base_tool.py
│   │       ├── web_search_tool.py
│   │       ├── database_tool.py
│   │       └── api_call_tool.py
│   │
│   └── utils/                    # 工具函數
│       ├── __init__.py
│       ├── datetime_utils.py
│       ├── validation.py
│       └── serialization.py
│
├── tests/                        # 測試目錄
│   ├── __init__.py
│   ├── conftest.py               # pytest 配置
│   │
│   ├── unit/                     # 單元測試
│   │   ├── __init__.py
│   │   ├── domain/
│   │   │   ├── __init__.py
│   │   │   ├── test_workflow_entity.py
│   │   │   └── test_execution_state_machine.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── test_workflow_service.py
│   │   │   └── test_execution_service.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── test_datetime_utils.py
│   │
│   ├── integration/              # 集成測試
│   │   ├── __init__.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── test_workflow_api.py
│   │   │   └── test_execution_api.py
│   │   ├── database/
│   │   │   ├── __init__.py
│   │   │   └── test_workflow_repository.py
│   │   └── queue/
│   │       ├── __init__.py
│   │       └── test_rabbitmq_publisher.py
│   │
│   └── e2e/                      # 端到端測試
│       ├── __init__.py
│       └── test_workflow_execution.py
│
├── migrations/                   # Alembic 數據庫遷移
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
│
├── scripts/                      # 工具腳本
│   ├── seed_data.py              # 種子數據
│   ├── create_user.py
│   └── migrate_db.py
│
├── Dockerfile                    # Docker 構建文件
├── requirements.txt              # Python 依賴
├── requirements-dev.txt          # 開發依賴
├── pyproject.toml                # 項目配置 (Black, isort, mypy)
├── .env.example                  # 環境變量模板
└── README.md
```

### 模塊職責說明

#### API Layer (`src/api/`)
- **職責**: 處理 HTTP 請求,路由,數據驗證
- **原則**: Thin controller,業務邏輯委託給 Service Layer
- **依賴**: Domain Services, Application Services

#### Core (`src/core/`)
- **職責**: 應用配置,安全,日誌,異常處理
- **原則**: 無業務邏輯,純工具函數
- **依賴**: 無

#### Domain Layer (`src/domain/`)
- **職責**: 業務邏輯,領域規則,實體定義
- **原則**: 純業務邏輯,不依賴基礎設施
- **依賴**: 僅依賴其他 Domain 模塊

#### Infrastructure Layer (`src/infrastructure/`)
- **職責**: 數據持久化,外部集成,技術實現
- **原則**: 實現 Domain Layer 定義的接口
- **依賴**: Domain Layer 接口

#### Services (`src/services/`)
- **職責**: 協調多個 Domain 和 Infrastructure 組件
- **原則**: 應用服務,編排業務流程
- **依賴**: Domain, Infrastructure

#### Agents (`src/agents/`)
- **職責**: Agent Framework Agent 實現
- **原則**: Agent 特定邏輯,與 Domain 分離
- **依賴**: Domain, Services

---

## <a id="frontend-structure"></a>3. Frontend 結構設計

### 完整目錄樹

```
frontend/
├── src/
│   ├── main.tsx                  # 應用入口
│   ├── App.tsx                   # 根組件
│   │
│   ├── components/               # 可復用組件
│   │   ├── ui/                   # 基礎 UI 組件
│   │   │   ├── Button/
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Button.module.css
│   │   │   │   └── Button.test.tsx
│   │   │   ├── Input/
│   │   │   │   ├── Input.tsx
│   │   │   │   ├── Input.module.css
│   │   │   │   └── Input.test.tsx
│   │   │   ├── Card/
│   │   │   ├── Modal/
│   │   │   └── Table/
│   │   │
│   │   └── common/               # 業務組件
│   │       ├── Header/
│   │       ├── Sidebar/
│   │       └── Footer/
│   │
│   ├── features/                 # 功能模塊 (Feature-based)
│   │   ├── workflows/
│   │   │   ├── components/
│   │   │   │   ├── WorkflowList.tsx
│   │   │   │   ├── WorkflowEditor.tsx
│   │   │   │   └── WorkflowCard.tsx
│   │   │   ├── hooks/
│   │   │   │   ├── useWorkflows.ts
│   │   │   │   └── useWorkflowEditor.ts
│   │   │   ├── api/
│   │   │   │   └── workflowApi.ts
│   │   │   ├── types/
│   │   │   │   └── workflow.types.ts
│   │   │   └── stores/
│   │   │       └── workflowStore.ts (Zustand)
│   │   │
│   │   ├── executions/
│   │   │   ├── components/
│   │   │   │   ├── ExecutionList.tsx
│   │   │   │   ├── ExecutionDetail.tsx
│   │   │   │   └── ExecutionLogs.tsx
│   │   │   ├── hooks/
│   │   │   │   └── useExecutions.ts
│   │   │   ├── api/
│   │   │   │   └── executionApi.ts
│   │   │   └── types/
│   │   │       └── execution.types.ts
│   │   │
│   │   ├── agents/
│   │   │   ├── components/
│   │   │   │   ├── AgentList.tsx
│   │   │   │   └── AgentConfig.tsx
│   │   │   ├── hooks/
│   │   │   ├── api/
│   │   │   └── types/
│   │   │
│   │   └── auth/
│   │       ├── components/
│   │       │   └── LoginForm.tsx
│   │       ├── hooks/
│   │       │   └── useAuth.ts
│   │       └── api/
│   │           └── authApi.ts
│   │
│   ├── layouts/                  # 頁面佈局
│   │   ├── MainLayout.tsx
│   │   ├── AuthLayout.tsx
│   │   └── DashboardLayout.tsx
│   │
│   ├── pages/                    # 路由頁面
│   │   ├── Dashboard.tsx
│   │   ├── Workflows/
│   │   │   ├── WorkflowList.tsx
│   │   │   ├── WorkflowDetail.tsx
│   │   │   └── WorkflowCreate.tsx
│   │   ├── Executions/
│   │   │   ├── ExecutionList.tsx
│   │   │   └── ExecutionDetail.tsx
│   │   ├── Agents/
│   │   │   └── AgentList.tsx
│   │   └── Login.tsx
│   │
│   ├── services/                 # API 服務
│   │   ├── api.ts                # Axios 實例配置
│   │   ├── workflowService.ts
│   │   ├── executionService.ts
│   │   └── authService.ts
│   │
│   ├── stores/                   # 全局狀態管理
│   │   ├── authStore.ts
│   │   ├── themeStore.ts
│   │   └── notificationStore.ts
│   │
│   ├── hooks/                    # 自定義 Hooks
│   │   ├── useAuth.ts
│   │   ├── useWebSocket.ts
│   │   └── useDebounce.ts
│   │
│   ├── utils/                    # 工具函數
│   │   ├── formatters.ts
│   │   ├── validators.ts
│   │   └── constants.ts
│   │
│   ├── types/                    # TypeScript 類型
│   │   ├── api.types.ts
│   │   └── common.types.ts
│   │
│   ├── styles/                   # 全局樣式
│   │   ├── globals.css
│   │   └── variables.css
│   │
│   └── assets/                   # 靜態資源
│       ├── images/
│       └── icons/
│
├── public/
│   ├── index.html
│   └── favicon.ico
│
├── tests/
│   ├── unit/
│   └── e2e/
│
├── Dockerfile
├── package.json
├── tsconfig.json
├── vite.config.ts
├── .eslintrc.json
├── .prettierrc
└── README.md
```

### 模塊職責說明

#### Components (`src/components/`)
- **ui/**: 純 UI 組件,無業務邏輯
- **common/**: 業務組件,可跨 feature 複用

#### Features (`src/features/`)
- **職責**: 功能領域模塊化
- **原則**: Feature-based 組織,高內聚低耦合
- **包含**: components, hooks, api, types, stores

#### Pages (`src/pages/`)
- **職責**: 路由頁面組件
- **原則**: 組合 features 和 layouts

#### Services (`src/services/`)
- **職責**: API 調用封裝
- **原則**: 統一錯誤處理,請求攔截

---

## <a id="root-structure"></a>4. 根目錄結構

```
ai-semantic-kernel-framework-project/
├── backend/                      # 後端代碼
├── frontend/                     # 前端代碼
│
├── docs/                         # 項目文檔
│   ├── 00-discovery/
│   │   ├── brainstorming/
│   │   └── product-brief/
│   ├── 01-planning/
│   │   ├── prd/
│   │   └── ui-ux/
│   ├── 02-architecture/
│   │   ├── technical-architecture.md
│   │   ├── technical-architecture-part2.md
│   │   └── technical-architecture-part3.md
│   └── 03-implementation/
│       ├── sprint-planning/
│       ├── sprint-status.yaml
│       ├── local-development-guide.md
│       └── project-structure-design.md  # 本文檔
│
├── claudedocs/                   # AI 助手文檔
│   ├── AI-ASSISTANT-INSTRUCTIONS.md
│   ├── prompts/
│   │   ├── README.md
│   │   ├── PROMPT-01-PROJECT-ONBOARDING.md
│   │   ├── PROMPT-02-NEW-SPRINT-PREP.md
│   │   ├── PROMPT-03-BUG-FIX-PREP.md
│   │   ├── PROMPT-04-SPRINT-DEVELOPMENT.md
│   │   ├── PROMPT-05-TESTING-PHASE.md
│   │   ├── PROMPT-06-PROGRESS-SAVE.md
│   │   ├── PROMPT-07-ARCHITECTURE-REVIEW.md
│   │   ├── PROMPT-08-CODE-REVIEW.md
│   │   └── PROMPT-09-SESSION-END.md
│   └── session-logs/
│
├── scripts/                      # 跨項目腳本
│   └── setup.sh                  # 初始化腳本
│
├── docker-compose.yml            # 本地開發環境
├── .env.example                  # 環境變量模板
├── .gitignore
├── CLAUDE.md                     # AI 助手指南
├── CONTRIBUTING.md               # 貢獻指南
└── README.md                     # 項目 README
```

---

## <a id="creation-steps"></a>5. 創建步驟

### Step 1: 創建 Backend 目錄結構

```bash
# 導航到項目根目錄
cd /path/to/ai-semantic-kernel-framework-project

# 創建 Backend 主要目錄
mkdir -p backend/src/{api/v1/{workflows,executions,agents,webhooks,auth},core,domain/{workflows,executions,agents},infrastructure/{database/models,cache,queue,repositories,external},services,agents/tools,utils}

# 創建 Backend 測試目錄
mkdir -p backend/tests/{unit/{domain,services,utils},integration/{api,database,queue},e2e}

# 創建其他 Backend 目錄
mkdir -p backend/{migrations/versions,scripts}

# 創建所有 __init__.py 文件
find backend/src -type d -exec touch {}/__init__.py \;
find backend/tests -type d -exec touch {}/__init__.py \;
```

### Step 2: 創建 Frontend 目錄結構 (Sprint 4)

```bash
# 創建 Frontend 主要目錄
mkdir -p frontend/src/{components/{ui/{Button,Input,Card,Modal,Table},common/{Header,Sidebar,Footer}},features/{workflows,executions,agents,auth}/{components,hooks,api,types,stores},layouts,pages/{Workflows,Executions,Agents},services,stores,hooks,utils,types,styles,assets/{images,icons}}

# 創建 Frontend 測試目錄
mkdir -p frontend/tests/{unit,e2e}

# 創建 public 目錄
mkdir -p frontend/public
```

### Step 3: 創建根目錄文檔結構

```bash
# 已存在,無需創建
# docs/ 目錄已完整
# claudedocs/ 目錄已完整

# 創建 scripts 目錄 (如不存在)
mkdir -p scripts
```

### Step 4: 創建初始文件

```bash
# Backend 初始文件
touch backend/src/main.py
touch backend/requirements.txt
touch backend/requirements-dev.txt
touch backend/pyproject.toml
touch backend/Dockerfile
touch backend/.env.example
touch backend/README.md

# Frontend 初始文件 (Sprint 4)
touch frontend/src/main.tsx
touch frontend/src/App.tsx
touch frontend/package.json
touch frontend/tsconfig.json
touch frontend/vite.config.ts
touch frontend/.eslintrc.json
touch frontend/.prettierrc
touch frontend/Dockerfile
touch frontend/README.md

# 根目錄文件 (如不存在)
touch .gitignore
touch CONTRIBUTING.md
```

### Step 5: 驗證結構

```bash
# 查看 Backend 結構
tree backend/src -L 3

# 查看 Frontend 結構
tree frontend/src -L 3

# 查看根目錄結構
tree -L 2 -I 'node_modules|__pycache__|.git'
```

---

## 📝 實施計劃

### Phase 1: Sprint 0 (當前)
- ✅ 創建 Backend 完整目錄結構
- ✅ 創建 Backend 初始文件
- ⏳ 實現核心基礎設施 (Database, Cache, Queue)

### Phase 2: Sprint 1
- ⏳ 實現 Domain Layer (Entities, Services)
- ⏳ 實現 Infrastructure Layer (Repositories)
- ⏳ 實現 API Layer (CRUD endpoints)

### Phase 3: Sprint 2-3
- ⏳ 實現 Agent Layer
- ⏳ 實現外部集成
- ⏳ 完善測試覆蓋

### Phase 4: Sprint 4
- ⏳ 創建 Frontend 完整目錄結構
- ⏳ 實現 Frontend 功能模塊
- ⏳ 集成 Frontend 與 Backend

---

## 🎯 設計決策記錄

### 決策 1: 分層架構

**背景**: 需要清晰的職責分離和可測試性
**決策**: 採用 4 層架構 (API → Service → Domain → Infrastructure)
**原因**:
- 符合 SOLID 原則
- 易於測試和維護
- 業務邏輯與技術實現分離

**影響**:
- ✅ 代碼組織清晰
- ✅ 易於單元測試
- ⚠️ 需要更多樣板代碼

### 決策 2: Feature-based Frontend

**背景**: Frontend 功能模塊化需求
**決策**: 採用 Feature-based 組織,而非 Type-based
**原因**:
- 高內聚低耦合
- 功能模塊獨立開發和測試
- 易於團隊協作

**影響**:
- ✅ 功能邊界清晰
- ✅ 代碼複用性高
- ⚠️ 需要定義清晰的 feature 邊界

### 決策 3: Domain-Driven Design

**背景**: 複雜業務邏輯管理
**決策**: Domain Layer 採用 DDD 模式
**原因**:
- 業務邏輯與技術實現分離
- 易於理解和維護
- 符合業務領域模型

**影響**:
- ✅ 業務邏輯可測試性高
- ✅ 代碼可讀性強
- ⚠️ 需要團隊理解 DDD 概念

---

## 📚 參考資源

- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Domain-Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html)
- [Feature-Sliced Design](https://feature-sliced.design/)
- [Python Project Structure](https://docs.python-guide.org/writing/structure/)
- [React Project Structure](https://reactjs.org/docs/faq-structure.html)

---

**文檔狀態**: ✅ 完成
**維護者**: Architecture Team
**最後更新**: 2025-11-20
