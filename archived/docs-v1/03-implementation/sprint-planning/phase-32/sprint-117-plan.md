# Sprint 117: Multi-Worker + ServiceNow MCP

## 概述

Sprint 117 專注於兩個基礎設施增強：將單 Worker Uvicorn 升級為 Gunicorn Multi-Worker 配置，以及實現 ServiceNow MCP Server 提供 RITM 回寫能力。這兩項是 AD 場景端到端閉環的關鍵拼圖。

## 目標

1. Multi-Worker Uvicorn 部署（Gunicorn + environment-aware 配置）
2. ServiceNow MCP Server（6 個核心工具 — RITM/Incident 操作）

## Story Points: 40 點

## 前置條件

- ✅ Sprint 116 完成（架構加固 — Swarm 整合、Layer 4 拆分、循環依賴修復）
- ✅ Phase 31 InMemory 存儲已遷移 Redis（Multi-Worker 前提）
- ✅ ContextSynchronizer asyncio.Lock 已修復（Phase 31）
- ✅ ServiceNow 開發實例可用（Table API 存取）

## 任務分解

### Story 117-1: Multi-Worker Uvicorn (2 天, P1)

**目標**: 將單 Worker + reload=True 的開發配置替換為 environment-aware 的 Multi-Worker 配置

**交付物**:
- 新增 `backend/gunicorn.conf.py`
- 修改 `backend/main.py`（啟動邏輯）
- 新增 `backend/src/core/server_config.py`
- 新增 `backend/tests/unit/core/test_server_config.py`

**配置設計**:

```python
# server_config.py
import os
import multiprocessing
from enum import Enum


class ServerEnvironment(str, Enum):
    """伺服器環境"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class ServerConfig:
    """Environment-aware 伺服器配置"""

    def __init__(self, env: str = None):
        self.environment = ServerEnvironment(
            env or os.getenv("SERVER_ENV", "development")
        )

    @property
    def workers(self) -> int:
        if self.environment == ServerEnvironment.DEVELOPMENT:
            return 1
        return int(os.getenv(
            "UVICORN_WORKERS",
            str(min(multiprocessing.cpu_count() * 2 + 1, 8))
        ))

    @property
    def reload(self) -> bool:
        return self.environment == ServerEnvironment.DEVELOPMENT

    @property
    def host(self) -> str:
        return os.getenv("SERVER_HOST", "0.0.0.0")

    @property
    def port(self) -> int:
        return int(os.getenv("SERVER_PORT", "8000"))

    @property
    def log_level(self) -> str:
        if self.environment == ServerEnvironment.DEVELOPMENT:
            return "debug"
        return os.getenv("LOG_LEVEL", "info")

    @property
    def access_log(self) -> bool:
        return self.environment != ServerEnvironment.PRODUCTION

    @property
    def worker_class(self) -> str:
        return "uvicorn.workers.UvicornWorker"
```

```python
# gunicorn.conf.py
from src.core.server_config import ServerConfig

config = ServerConfig()

bind = f"{config.host}:{config.port}"
workers = config.workers
worker_class = config.worker_class
reload = config.reload
loglevel = config.log_level
accesslog = "-" if config.access_log else None
```

**啟動方式**:

```bash
# Development (1 worker + reload)
SERVER_ENV=development python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production (N workers via Gunicorn)
SERVER_ENV=production gunicorn main:app -c gunicorn.conf.py
```

**驗收標準**:
- [ ] `ServerConfig` 正確區分 dev/staging/prod 環境
- [ ] Development: 1 worker + reload=True
- [ ] Production: N workers（CPU*2+1, max 8）+ reload=False
- [ ] Gunicorn 配置文件正確
- [ ] 環境變量可覆蓋預設值
- [ ] Multi-Worker 啟動無 InMemory 衝突（Phase 31 已遷移 Redis）
- [ ] 單元測試覆蓋各環境配置
- [ ] 更新 `.env.example` 和啟動文檔

### Story 117-2: ServiceNow MCP Server (3-4 天, P1)

**目標**: 實現 ServiceNow MCP Server，提供 6 個核心工具讓 Agent 可以操作 ServiceNow Incident 和 RITM

**交付物**:
- 新增 `backend/src/integrations/mcp/servicenow_server.py`
- 新增 `backend/src/integrations/mcp/servicenow_client.py`
- 新增 `backend/src/integrations/mcp/servicenow_config.py`
- 新增 `backend/tests/unit/mcp/test_servicenow_server.py`
- 新增 `backend/tests/unit/mcp/test_servicenow_client.py`
- 新增 `backend/tests/integration/mcp/test_servicenow_api.py`

**ServiceNow Client 設計**:

```python
# servicenow_client.py
from typing import Optional, Dict, Any, List
import httpx


class ServiceNowConfig:
    """ServiceNow 連接配置"""
    instance_url: str  # https://company.service-now.com
    username: str
    password: str  # 或 OAuth2 token
    api_version: str = "v2"
    timeout: int = 30


class ServiceNowClient:
    """ServiceNow Table API 客戶端"""

    def __init__(self, config: ServiceNowConfig):
        self._config = config
        self._base_url = f"{config.instance_url}/api/now/{config.api_version}"
        self._client = httpx.AsyncClient(
            auth=(config.username, config.password),
            timeout=config.timeout,
        )

    # ==================== Incident 操作 ====================

    async def create_incident(
        self, short_description: str, description: str,
        category: str = "inquiry", urgency: str = "3",
        assignment_group: Optional[str] = None,
        caller_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """建立 Incident"""

    async def update_incident(
        self, sys_id: str, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新 Incident"""

    async def get_incident(
        self, number: Optional[str] = None, sys_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """查詢 Incident"""

    # ==================== RITM 操作 ====================

    async def create_ritm(
        self, cat_item: str, variables: Dict[str, Any],
        requested_for: str, short_description: str,
    ) -> Dict[str, Any]:
        """建立 RITM (Requested Item)"""

    async def get_ritm_status(
        self, number: Optional[str] = None, sys_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """查詢 RITM 狀態"""

    async def add_work_notes(
        self, table: str, sys_id: str, work_notes: str
    ) -> Dict[str, Any]:
        """添加工作備註"""

    # ==================== Attachment 操作 ====================

    async def add_attachment(
        self, table: str, sys_id: str, file_name: str, content: bytes,
        content_type: str = "text/plain"
    ) -> Dict[str, Any]:
        """添加附件"""
```

**MCP Server 6 個核心工具**:

| 工具名稱 | 操作 | Table API | 說明 |
|----------|------|-----------|------|
| `create_incident` | POST | `/table/incident` | 建立 Incident |
| `update_incident` | PATCH | `/table/incident/{sys_id}` | 更新 Incident 狀態/欄位 |
| `get_incident` | GET | `/table/incident` | 查詢 Incident |
| `create_ritm` | POST | `/table/sc_req_item` | 建立 RITM |
| `get_ritm_status` | GET | `/table/sc_req_item` | 查詢 RITM 狀態 |
| `add_attachment` | POST | `/attachment/file` | 添加附件 |

**MCP Server 設計**:

```python
# servicenow_server.py
class ServiceNowMCPServer:
    """ServiceNow MCP Server"""

    def __init__(self, client: ServiceNowClient):
        self._client = client
        self._tools = self._register_tools()

    def _register_tools(self) -> Dict[str, ToolDefinition]:
        """註冊 6 個核心工具"""
        return {
            "create_incident": ToolDefinition(
                name="create_incident",
                description="Create a new ServiceNow incident",
                input_schema={...},
                handler=self._create_incident,
            ),
            # ... 其他 5 個工具
        }

    async def _create_incident(self, params: Dict) -> Dict:
        """create_incident 工具處理"""
        return await self._client.create_incident(**params)

    # ... 其他 handler methods
```

**驗收標準**:
- [ ] ServiceNowClient 6 個核心方法實現完整
- [ ] ServiceNow MCP Server 註冊 6 個工具
- [ ] 每個工具有完整的 input_schema 和 description
- [ ] 錯誤處理完整（網路錯誤、認證失敗、權限不足、記錄不存在）
- [ ] 支援 Basic Auth 和 OAuth2 Token 認證
- [ ] 超時和重試機制
- [ ] 單元測試（Mock ServiceNow API）覆蓋率 > 85%
- [ ] 整合測試（ServiceNow 開發實例）通過
- [ ] 環境變量文檔更新

## 技術設計

### 目錄結構

```
backend/
├── gunicorn.conf.py                    # 🆕 Gunicorn 配置
├── src/
│   ├── core/
│   │   └── server_config.py            # 🆕 伺服器配置
│   └── integrations/mcp/
│       ├── servicenow_config.py        # 🆕 ServiceNow 配置
│       ├── servicenow_client.py        # 🆕 ServiceNow Client
│       └── servicenow_server.py        # 🆕 ServiceNow MCP Server
└── tests/
    ├── unit/
    │   ├── core/test_server_config.py  # 🆕
    │   └── mcp/
    │       ├── test_servicenow_server.py  # 🆕
    │       └── test_servicenow_client.py  # 🆕
    └── integration/mcp/
        └── test_servicenow_api.py      # 🆕
```

### 環境變量新增

```bash
# Server Configuration
SERVER_ENV=development    # development | staging | production
UVICORN_WORKERS=4         # 覆蓋預設 worker 數量
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# ServiceNow
SERVICENOW_INSTANCE_URL=https://company.service-now.com
SERVICENOW_USERNAME=<username>
SERVICENOW_PASSWORD=<password>
SERVICENOW_API_VERSION=v2
SERVICENOW_TIMEOUT=30
```

## 依賴新增

```
gunicorn>=21.2.0          # Multi-Worker WSGI/ASGI
httpx>=0.25.0             # Async HTTP Client (已有)
```

## 風險

| 風險 | 緩解措施 |
|------|----------|
| Multi-Worker 下 InMemory 不一致 | Phase 31 已遷移 Redis，此風險已消除 |
| ServiceNow API 限流 | 實現重試退避機制、批次操作合併 |
| ServiceNow 開發實例不穩定 | 完整 Mock 測試、整合測試標記為可選 |
| Gunicorn 在 Windows 不可用 | 開發環境仍用 Uvicorn 直接啟動 |

## 完成標準

- [ ] Multi-Worker 配置 environment-aware（dev: 1 worker, prod: N workers）
- [ ] Gunicorn 配置文件就緒
- [ ] ServiceNow MCP Server 6 個工具全部可用
- [ ] 所有測試通過
- [ ] 文檔更新完成

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 40
**開始日期**: TBD
