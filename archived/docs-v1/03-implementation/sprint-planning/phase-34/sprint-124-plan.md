# Sprint 124: n8n 整合 — Mode 1 + Mode 2

## 概述

Sprint 124 啟動 Phase 34 的 P1 功能擴展，實現 n8n 與 IPA Platform 的前兩種協作模式。Mode 1 讓 IPA Agent 能觸發 n8n 工作流，Mode 2 讓 n8n 工作流能呼叫 IPA API 進行 AI 推理。

## 目標

1. 實現 n8n MCP Server（Mode 1: IPA → n8n）
2. 實現 n8n Webhook 入口（Mode 2: n8n → IPA）
3. 建立 n8n 連線管理與健康檢查
4. 編寫單元測試與整合測試

## Story Points: 25 點

## 前置條件

- ✅ Phase 33 完成（生產化就緒、60% 覆蓋率）
- ⬜ n8n Docker 容器可用（docker-compose 已包含）
- ⬜ n8n API Token 配置就緒

## 任務分解

### Story 124-1: n8n MCP Server — IPA 觸發 n8n (3 天, P1)

**目標**: 建立 n8n MCP Server，讓 IPA Agent 能觸發 n8n 工作流

**交付物**:
- `backend/src/integrations/mcp/servers/n8n/` 模組
- n8n MCP Server 6 個 tools

**技術方案**:
```
用戶請求 → IPA Agent 分析 → 呼叫 n8n MCP Tool → n8n 執行工作流 → 返回結果
```

**MCP Tools**:

| Tool | 說明 | n8n API |
|------|------|---------|
| `list_workflows` | 列出所有 n8n 工作流 | GET /workflows |
| `get_workflow` | 取得工作流詳情 | GET /workflows/{id} |
| `execute_workflow` | 觸發工作流執行 | POST /workflows/{id}/execute |
| `get_execution` | 查詢執行狀態 | GET /executions/{id} |
| `list_executions` | 列出執行歷史 | GET /executions |
| `activate_workflow` | 啟用/停用工作流 | PATCH /workflows/{id} |

**檔案結構**:
```
src/integrations/mcp/servers/n8n/
├── __init__.py
├── __main__.py          # MCP Server 入口
├── server.py            # N8nMCPServer
├── client.py            # N8nApiClient（n8n REST API 封裝）
└── tools/
    ├── __init__.py
    ├── workflow.py       # 工作流管理 tools
    └── execution.py      # 執行管理 tools
```

### Story 124-2: n8n Webhook 入口 — n8n 觸發 IPA (2 天, P1)

**目標**: 建立 Webhook 端點，讓 n8n 工作流能呼叫 IPA 進行 AI 推理

**交付物**:
- `backend/src/api/v1/n8n/` API 路由
- Webhook 認證與驗證機制

**API 端點**:

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/v1/n8n/webhook` | POST | n8n Webhook 入口 |
| `/api/v1/n8n/webhook/{workflow_id}` | POST | 指定工作流的 Webhook |
| `/api/v1/n8n/status` | GET | 連線狀態檢查 |
| `/api/v1/n8n/config` | GET | 取得 n8n 配置 |
| `/api/v1/n8n/config` | PUT | 更新 n8n 配置 |

**Webhook Payload 格式**:
```python
class N8nWebhookPayload(BaseModel):
    workflow_id: str
    execution_id: str
    action: str              # "analyze", "classify", "execute"
    data: dict               # 業務資料
    callback_url: str | None # 異步回調 URL
```

### Story 124-3: 連線管理與測試 (2 天, P1)

**目標**: n8n 連線配置管理、健康檢查、測試

**交付物**:
- 連線配置管理（URL, API Key, 超時設定）
- 健康檢查機制
- 單元測試 + 整合測試

**測試範圍**:

| 測試檔案 | 測試數量 | 範圍 |
|----------|---------|------|
| `test_n8n_client.py` | ~15 | API client CRUD |
| `test_n8n_server.py` | ~10 | MCP Server tools |
| `test_n8n_webhook.py` | ~10 | Webhook 端點 |
| `test_n8n_integration.py` | ~5 | 端到端流程 |

## 風險

| 風險 | 影響 | 緩解 |
|------|------|------|
| n8n API 版本差異 | Tool 不相容 | 支援 n8n v1.x API |
| n8n Docker 網路隔離 | 連線失敗 | 使用 Docker network |
| Webhook 安全 | 未授權觸發 | HMAC 簽名驗證 |

## 依賴

- 改善提案 Phase D P1: n8n 整合（3 種協作模式）
- n8n Docker Compose 服務
