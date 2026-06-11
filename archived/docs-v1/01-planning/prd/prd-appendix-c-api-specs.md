# PRD 附錄 C: API 規範

**版本**: 1.0  
**日期**: 2025-11-19  
**狀態**: 草稿

---

## 📑 文檔導航

- [PRD 主文檔](./prd-main.md)
- [PRD 附錄 A: Features 1-7](./prd-appendix-a-features-1-7.md)
- [PRD 附錄 B: Features 8-14](./prd-appendix-b-features-8-14.md)
- **[PRD 附錄 C: API 規範](./prd-appendix-c-api-specs.md)** ← 您在這裡

---

## 目錄

- [C1. REST API 規範](#rest-api)
  - [工作流管理 API](#workflow-api)
  - [執行管理 API](#execution-api)
  - [Agent 配置 API](#agent-api)
  - [監控與審計 API](#monitoring-api)
- [C2. GraphQL API](#graphql-api)
- [C3. Webhook 規範](#webhook-specs)
- [C4. 身份認證與授權](#authentication)
- [C5. 錯誤處理規範](#error-handling)
- [C6. 速率限制](#rate-limiting)
- [C7. API 版本控制](#versioning)

---

## 附錄 C 概述

本附錄定義平台所有 **API 接口規範**，包括 REST API、GraphQL、Webhook、身份認證等。所有 API 遵循：

- **RESTful 設計原則**
- **OpenAPI 3.0 標準**
- **OAuth 2.0 / JWT 認證**
- **統一錯誤格式**
- **完整的請求/響應示例**

---

## <a id="rest-api"></a>C1. REST API 規範

### API 基礎信息

**基礎 URL**: `https://api.ipa.example.com/v1`

**通用請求頭**:
```http
Authorization: Bearer <access_token>
Content-Type: application/json
X-Request-ID: <uuid>
```

**通用響應格式**:
```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2025-11-19T10:30:00Z"
  }
}
```

---

### <a id="workflow-api"></a>C1.1 工作流管理 API

#### 創建工作流

**端點**: `POST /workflows`

**請求體**:
```json
{
  "name": "customer_360_view",
  "display_name": "客戶 360 度視圖",
  "description": "整合多個系統的客戶數據",
  "agents": [
    {
      "agent_id": "servicenow_query_agent",
      "config": {
        "instance_url": "https://dev123.service-now.com",
        "timeout": 30
      }
    },
    {
      "agent_id": "dynamics_crm_agent",
      "config": {
        "api_url": "https://org.crm.dynamics.com"
      }
    }
  ],
  "trigger": {
    "type": "webhook",
    "config": {
      "authentication": "hmac",
      "filters": [
        {
          "json_path": "$.event_type",
          "operator": "equals",
          "value": "customer.created"
        }
      ]
    }
  },
  "retry_policy": {
    "enabled": true,
    "max_retries": 5,
    "backoff_strategy": "exponential"
  }
}
```

**響應** (201 Created):
```json
{
  "success": true,
  "data": {
    "workflow_id": "wf_abc123",
    "name": "customer_360_view",
    "status": "active",
    "webhook_url": "https://api.ipa.example.com/webhooks/wh_xyz789",
    "created_at": "2025-11-19T10:30:00Z",
    "created_by": "user_123"
  },
  "meta": {
    "request_id": "req_001"
  }
}
```

#### 列出所有工作流

**端點**: `GET /workflows`

**查詢參數**:
- `status`: 過濾狀態 (`active`, `inactive`, `draft`)
- `limit`: 每頁數量 (默認 20, 最大 100)
- `offset`: 分頁偏移量
- `sort`: 排序字段 (`created_at`, `name`, `last_executed_at`)

**請求示例**:
```http
GET /workflows?status=active&limit=10&sort=-created_at
```

**響應** (200 OK):
```json
{
  "success": true,
  "data": [
    {
      "workflow_id": "wf_abc123",
      "name": "customer_360_view",
      "display_name": "客戶 360 度視圖",
      "status": "active",
      "trigger_type": "webhook",
      "created_at": "2025-11-19T10:30:00Z",
      "last_executed_at": "2025-11-19T14:25:30Z",
      "execution_count": 42
    }
  ],
  "meta": {
    "total": 1,
    "limit": 10,
    "offset": 0,
    "has_more": false
  }
}
```

#### 獲取工作流詳情

**端點**: `GET /workflows/{workflow_id}`

**響應** (200 OK):
```json
{
  "success": true,
  "data": {
    "workflow_id": "wf_abc123",
    "name": "customer_360_view",
    "display_name": "客戶 360 度視圖",
    "description": "整合多個系統的客戶數據",
    "status": "active",
    "agents": [ ... ],
    "trigger": { ... },
    "retry_policy": { ... },
    "created_at": "2025-11-19T10:30:00Z",
    "updated_at": "2025-11-19T12:00:00Z",
    "version": 2
  }
}
```

#### 更新工作流

**端點**: `PATCH /workflows/{workflow_id}`

**請求體** (部分更新):
```json
{
  "display_name": "客戶 360 度視圖 (生產)",
  "retry_policy": {
    "max_retries": 10
  }
}
```

**響應** (200 OK):
```json
{
  "success": true,
  "data": {
    "workflow_id": "wf_abc123",
    "version": 3,
    "updated_at": "2025-11-19T15:00:00Z"
  }
}
```

#### 刪除工作流

**端點**: `DELETE /workflows/{workflow_id}`

**響應** (204 No Content)

---

### <a id="execution-api"></a>C1.2 執行管理 API

#### 手動觸發執行

**端點**: `POST /workflows/{workflow_id}/execute`

**請求體**:
```json
{
  "input_data": {
    "customer_id": "CUST-5678",
    "include_tickets": true,
    "include_crm": true
  },
  "idempotency_key": "exec_20251119_001"
}
```

**響應** (202 Accepted):
```json
{
  "success": true,
  "data": {
    "execution_id": "exec_abc123",
    "workflow_id": "wf_abc123",
    "status": "queued",
    "queued_at": "2025-11-19T15:10:00Z"
  }
}
```

#### 查詢執行狀態

**端點**: `GET /executions/{execution_id}`

**響應** (200 OK):
```json
{
  "success": true,
  "data": {
    "execution_id": "exec_abc123",
    "workflow_id": "wf_abc123",
    "status": "completed",
    "started_at": "2025-11-19T15:10:05Z",
    "completed_at": "2025-11-19T15:10:12Z",
    "duration_ms": 7200,
    "result": {
      "customer_profile": { ... },
      "open_tickets": 3,
      "crm_interactions": 15
    },
    "logs": [
      {
        "timestamp": "2025-11-19T15:10:05Z",
        "level": "info",
        "message": "Starting ServiceNow query..."
      }
    ]
  }
}
```

#### 列出執行記錄

**端點**: `GET /executions`

**查詢參數**:
- `workflow_id`: 過濾工作流
- `status`: 過濾狀態 (`queued`, `running`, `completed`, `failed`, `dlq`)
- `start_date`: 開始時間 (ISO 8601)
- `end_date`: 結束時間
- `limit`: 每頁數量
- `offset`: 分頁偏移量

**請求示例**:
```http
GET /executions?workflow_id=wf_abc123&status=failed&limit=10
```

**響應** (200 OK):
```json
{
  "success": true,
  "data": [
    {
      "execution_id": "exec_abc124",
      "workflow_id": "wf_abc123",
      "status": "failed",
      "error": {
        "type": "HTTPException",
        "message": "ServiceNow API timeout",
        "code": 503
      },
      "retry_count": 5,
      "started_at": "2025-11-19T14:00:00Z",
      "failed_at": "2025-11-19T14:01:02Z"
    }
  ],
  "meta": {
    "total": 3,
    "limit": 10,
    "offset": 0
  }
}
```

#### 取消執行

**端點**: `POST /executions/{execution_id}/cancel`

**響應** (200 OK):
```json
{
  "success": true,
  "data": {
    "execution_id": "exec_abc123",
    "status": "cancelled",
    "cancelled_at": "2025-11-19T15:15:00Z"
  }
}
```

---

### <a id="agent-api"></a>C1.3 Agent 配置 API

#### 列出所有 Agent

**端點**: `GET /agents`

**響應** (200 OK):
```json
{
  "success": true,
  "data": [
    {
      "agent_id": "servicenow_query_agent",
      "name": "ServiceNow 查詢 Agent",
      "type": "system_integration",
      "capabilities": ["query", "update", "create_incident"],
      "status": "active",
      "version": "1.2.0"
    }
  ]
}
```

#### 獲取 Agent 詳情

**端點**: `GET /agents/{agent_id}`

**響應** (200 OK):
```json
{
  "success": true,
  "data": {
    "agent_id": "servicenow_query_agent",
    "name": "ServiceNow 查詢 Agent",
    "description": "查詢 ServiceNow 工單和配置項",
    "type": "system_integration",
    "capabilities": [ ... ],
    "configuration_schema": {
      "type": "object",
      "properties": {
        "instance_url": {
          "type": "string",
          "description": "ServiceNow 實例 URL"
        },
        "timeout": {
          "type": "integer",
          "default": 30
        }
      },
      "required": ["instance_url"]
    },
    "prompt_template": "servicenow_query_v1.yaml"
  }
}
```

---

### <a id="monitoring-api"></a>C1.4 監控與審計 API

#### 獲取執行統計

**端點**: `GET /metrics/executions`

**查詢參數**:
- `workflow_id`: 過濾工作流
- `start_date`: 開始時間
- `end_date`: 結束時間
- `granularity`: 時間粒度 (`hour`, `day`, `week`)

**響應** (200 OK):
```json
{
  "success": true,
  "data": {
    "total_executions": 1523,
    "success_rate": 0.952,
    "avg_duration_ms": 3240,
    "error_rate": 0.048,
    "by_status": {
      "completed": 1450,
      "failed": 73
    },
    "timeline": [
      {
        "timestamp": "2025-11-19T00:00:00Z",
        "count": 145,
        "success_rate": 0.965
      }
    ]
  }
}
```

#### 查詢審計日誌

**端點**: `GET /audit-logs`

**查詢參數**:
- `event_type`: 事件類型 (`user_login`, `config_change`, `execution_start`)
- `user_id`: 用戶 ID
- `start_date`: 開始時間
- `end_date`: 結束時間
- `limit`: 每頁數量

**響應** (200 OK):
```json
{
  "success": true,
  "data": [
    {
      "log_id": "log_abc123",
      "event_type": "config_change",
      "user_id": "user_123",
      "user_email": "alex.chen@example.com",
      "resource_type": "workflow",
      "resource_id": "wf_abc123",
      "action": "update",
      "changes": {
        "retry_policy.max_retries": {
          "old": 5,
          "new": 10
        }
      },
      "ip_address": "10.0.1.45",
      "timestamp": "2025-11-19T15:00:00Z",
      "sha256_hash": "a1b2c3..."
    }
  ]
}
```

---

## <a id="graphql-api"></a>C2. GraphQL API

### GraphQL 端點

**URL**: `https://api.ipa.example.com/graphql`

### Schema 概覽

```graphql
type Query {
  workflow(id: ID!): Workflow
  workflows(
    status: WorkflowStatus
    limit: Int
    offset: Int
  ): WorkflowConnection!
  
  execution(id: ID!): Execution
  executions(
    workflowId: ID
    status: ExecutionStatus
    startDate: DateTime
    endDate: DateTime
    limit: Int
    offset: Int
  ): ExecutionConnection!
  
  agent(id: ID!): Agent
  agents: [Agent!]!
  
  metrics(
    workflowId: ID
    startDate: DateTime!
    endDate: DateTime!
    granularity: MetricGranularity!
  ): Metrics!
}

type Mutation {
  createWorkflow(input: CreateWorkflowInput!): Workflow!
  updateWorkflow(id: ID!, input: UpdateWorkflowInput!): Workflow!
  deleteWorkflow(id: ID!): Boolean!
  
  executeWorkflow(
    workflowId: ID!
    inputData: JSON!
    idempotencyKey: String
  ): Execution!
  
  cancelExecution(id: ID!): Execution!
  retryExecution(id: ID!): Execution!
}

type Workflow {
  id: ID!
  name: String!
  displayName: String!
  description: String
  status: WorkflowStatus!
  agents: [AgentConfig!]!
  trigger: TriggerConfig!
  retryPolicy: RetryPolicy!
  createdAt: DateTime!
  updatedAt: DateTime!
  lastExecutedAt: DateTime
  executionCount: Int!
  executions(limit: Int, offset: Int): ExecutionConnection!
}

type Execution {
  id: ID!
  workflow: Workflow!
  status: ExecutionStatus!
  inputData: JSON!
  result: JSON
  error: ExecutionError
  startedAt: DateTime
  completedAt: DateTime
  durationMs: Int
  retryCount: Int!
  logs: [LogEntry!]!
}

enum WorkflowStatus {
  ACTIVE
  INACTIVE
  DRAFT
}

enum ExecutionStatus {
  QUEUED
  RUNNING
  COMPLETED
  FAILED
  CANCELLED
  DLQ
}
```

### 查詢示例

#### 查詢工作流及其最近執行

```graphql
query GetWorkflowWithExecutions($workflowId: ID!) {
  workflow(id: $workflowId) {
    id
    name
    displayName
    status
    agents {
      agentId
      config
    }
    executionCount
    executions(limit: 10) {
      edges {
        node {
          id
          status
          startedAt
          completedAt
          durationMs
          error {
            type
            message
          }
        }
      }
      pageInfo {
        hasNextPage
        endCursor
      }
    }
  }
}
```

#### 執行工作流 Mutation

```graphql
mutation ExecuteWorkflow($workflowId: ID!, $inputData: JSON!) {
  executeWorkflow(
    workflowId: $workflowId
    inputData: $inputData
    idempotencyKey: "exec_20251119_001"
  ) {
    id
    status
    queuedAt
  }
}
```

---

## <a id="webhook-specs"></a>C3. Webhook 規範

### Webhook 接收端點

**URL 格式**: `https://api.ipa.example.com/webhooks/{webhook_id}`

### 安全驗證 (HMAC-SHA256)

**簽名計算**:
```python
import hmac
import hashlib

secret = "your_webhook_secret"
payload = json.dumps(request_body)
signature = "sha256=" + hmac.new(
    secret.encode(),
    payload.encode(),
    hashlib.sha256
).hexdigest()
```

**請求頭**:
```http
POST /webhooks/wh_xyz789 HTTP/1.1
Host: api.ipa.example.com
Content-Type: application/json
X-Webhook-Signature: sha256=a1b2c3...
X-Webhook-Event: incident.created
```

### Webhook 請求體

```json
{
  "event_type": "incident.created",
  "event_id": "evt_abc123",
  "timestamp": "2025-11-19T15:30:00Z",
  "data": {
    "incident_id": "INC0012345",
    "priority": "2",
    "description": "Server DB-01 is not responding",
    "assigned_to": "alex.chen@example.com"
  }
}
```

### Webhook 響應

**成功 (200 OK)**:
```json
{
  "status": "triggered",
  "execution_id": "exec_abc456",
  "message": "Workflow execution started"
}
```

**已處理 (200 OK)**:
```json
{
  "status": "already_processed",
  "execution_id": "exec_abc123",
  "message": "This event has already been processed"
}
```

**過濾掉 (200 OK)**:
```json
{
  "status": "filtered",
  "message": "Request did not match filter criteria"
}
```

---

## <a id="authentication"></a>C4. 身份認證與授權

### OAuth 2.0 流程

#### 1. 獲取訪問令牌

**端點**: `POST /oauth/token`

**請求體** (Client Credentials Grant):
```json
{
  "grant_type": "client_credentials",
  "client_id": "client_abc123",
  "client_secret": "secret_xyz789",
  "scope": "workflows:read workflows:write executions:read"
}
```

**響應** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "workflows:read workflows:write executions:read"
}
```

### JWT Token 格式

**Header**:
```json
{
  "alg": "RS256",
  "typ": "JWT"
}
```

**Payload**:
```json
{
  "sub": "user_123",
  "iss": "https://api.ipa.example.com",
  "aud": "ipa-api",
  "exp": 1700000000,
  "iat": 1699996400,
  "scope": "workflows:read workflows:write"
}
```

### RBAC 權限範圍

| Scope | 描述 |
|-------|------|
| `workflows:read` | 讀取工作流配置 |
| `workflows:write` | 創建/更新/刪除工作流 |
| `executions:read` | 查看執行記錄 |
| `executions:write` | 手動觸發執行 |
| `agents:read` | 查看 Agent 配置 |
| `agents:write` | 配置 Agent |
| `admin` | 完整管理權限 |

---

## <a id="error-handling"></a>C5. 錯誤處理規範

### 統一錯誤格式

```json
{
  "success": false,
  "error": {
    "code": "validation_error",
    "message": "Invalid workflow configuration",
    "details": [
      {
        "field": "agents[0].config.instance_url",
        "message": "Required field is missing"
      }
    ]
  },
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2025-11-19T15:30:00Z"
  }
}
```

### HTTP 狀態碼

| 狀態碼 | 含義 | 使用場景 |
|--------|------|----------|
| 200 OK | 成功 | GET/PATCH 成功 |
| 201 Created | 創建成功 | POST 創建資源 |
| 202 Accepted | 已接受 | 異步操作（執行觸發）|
| 204 No Content | 無內容 | DELETE 成功 |
| 400 Bad Request | 請求錯誤 | 參數驗證失敗 |
| 401 Unauthorized | 未授權 | Token 無效/過期 |
| 403 Forbidden | 禁止訪問 | 權限不足 |
| 404 Not Found | 資源不存在 | 資源 ID 錯誤 |
| 409 Conflict | 衝突 | 幂等性衝突 |
| 429 Too Many Requests | 限流 | 超過速率限制 |
| 500 Internal Server Error | 服務器錯誤 | 內部錯誤 |
| 503 Service Unavailable | 服務不可用 | 維護中 |

### 錯誤代碼

| 錯誤代碼 | 描述 |
|----------|------|
| `validation_error` | 請求參數驗證失敗 |
| `authentication_error` | 認證失敗 |
| `authorization_error` | 權限不足 |
| `not_found` | 資源不存在 |
| `conflict` | 資源衝突 |
| `rate_limit_exceeded` | 超過速率限制 |
| `internal_error` | 內部服務器錯誤 |

---

## <a id="rate-limiting"></a>C6. 速率限制

### 限流策略

| API 類別 | 速率限制 | 突發流量 |
|---------|----------|----------|
| 讀取 API (GET) | 1000 req/min | 1200 |
| 寫入 API (POST/PATCH) | 500 req/min | 600 |
| 執行觸發 | 100 req/min | 120 |
| Webhook | 500 req/min | 1000 |

### 響應頭

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 234
X-RateLimit-Reset: 1700000000
```

### 429 錯誤響應

```json
{
  "success": false,
  "error": {
    "code": "rate_limit_exceeded",
    "message": "Rate limit exceeded. Please retry after 60 seconds",
    "retry_after": 60
  }
}
```

---

## <a id="versioning"></a>C7. API 版本控制

### 版本策略

- **主版本**：URL 路徑中指定 (`/v1`, `/v2`)
- **次版本**：向後兼容的變更通過響應頭指示
- **棄用通知**：提前 6 個月通知

### 版本響應頭

```http
API-Version: 1.2.0
API-Supported-Versions: 1.0.0, 1.1.0, 1.2.0
API-Deprecated-Versions: 0.9.0
```

### 棄用警告

```http
Warning: 299 - "API version 1.0 will be deprecated on 2026-06-01"
```

---

## 總結

附錄 C 提供了平台所有 **API 接口的完整規範**：

✅ **REST API**：工作流、執行、Agent、監控  
✅ **GraphQL**：靈活的查詢語言  
✅ **Webhook**：事件驅動集成  
✅ **認證授權**：OAuth 2.0 + JWT + RBAC  
✅ **錯誤處理**：統一錯誤格式  
✅ **速率限制**：防止濫用  
✅ **版本控制**：向後兼容  

這些 API 為平台提供了**標準化、可靠、安全**的集成能力。

---

**相關文檔**:
- [OpenAPI 3.0 完整規範](./api-docs/openapi.yaml)
- [GraphQL Schema 定義](./api-docs/schema.graphql)
- [API 使用示例](./api-docs/examples.md)
- [SDK 文檔](./api-docs/sdk.md)
