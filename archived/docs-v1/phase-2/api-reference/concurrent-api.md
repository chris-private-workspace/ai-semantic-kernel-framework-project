# 並行執行 API 參考

## 概述

並行執行 API 提供 Fork-Join 任務執行、並行閘道管理等功能。

**Base URL**: `/api/v1/concurrent`

---

## 端點列表

| 方法 | 端點 | 說明 |
|------|------|------|
| POST | `/fork-join` | 執行 Fork-Join 任務組 |
| POST | `/gateway/execute` | 執行並行閘道 |
| GET | `/executions/{id}` | 查詢執行狀態 |
| POST | `/executions/{id}/cancel` | 取消執行 |
| GET | `/stats` | 獲取並行執行統計 |

---

## POST /concurrent/fork-join

執行 Fork-Join 並行任務組。

### 請求

```json
{
  "tasks": [
    {
      "id": "task_1",
      "agent_id": "550e8400-e29b-41d4-a716-446655440001",
      "inputs": {
        "data": "input_data_1"
      },
      "priority": "normal"
    },
    {
      "id": "task_2",
      "agent_id": "550e8400-e29b-41d4-a716-446655440002",
      "inputs": {
        "data": "input_data_2"
      },
      "priority": "high"
    }
  ],
  "join_mode": "all",
  "timeout_seconds": 300,
  "error_handling": {
    "on_failure": "continue",
    "max_retries": 3,
    "retry_delay_seconds": 1.0
  },
  "preserve_order": true
}
```

### 參數說明

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `tasks` | array | 是 | 任務列表 |
| `tasks[].id` | string | 是 | 任務 ID |
| `tasks[].agent_id` | UUID | 是 | 執行 Agent ID |
| `tasks[].inputs` | object | 否 | 任務輸入 |
| `tasks[].priority` | string | 否 | 優先級 (high/normal/low) |
| `join_mode` | string | 否 | 合併模式 (all/any/majority)，預設 all |
| `timeout_seconds` | integer | 否 | 超時時間，預設 300 |
| `error_handling` | object | 否 | 錯誤處理設定 |
| `preserve_order` | boolean | 否 | 是否保持結果順序 |

### 響應

**成功 (200)**:

```json
{
  "execution_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "results": {
    "task_1": {
      "status": "success",
      "output": {"result": "data_1"}
    },
    "task_2": {
      "status": "success",
      "output": {"result": "data_2"}
    }
  },
  "errors": {},
  "metrics": {
    "total_time_ms": 1250,
    "tasks_completed": 2,
    "tasks_failed": 0,
    "average_task_time_ms": 625
  }
}
```

**錯誤 (400)**:

```json
{
  "error": "validation_error",
  "message": "tasks array cannot be empty",
  "details": []
}
```

---

## POST /concurrent/gateway/execute

執行並行閘道 (Fork 或 Join)。

### 請求

```json
{
  "execution_id": "550e8400-e29b-41d4-a716-446655440000",
  "gateway_type": "fork",
  "branches": ["branch_a", "branch_b", "branch_c"],
  "config": {
    "join_mode": "all",
    "timeout_seconds": 300
  }
}
```

### 參數說明

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `execution_id` | UUID | 是 | 執行 ID |
| `gateway_type` | string | 是 | 閘道類型 (fork/join/inclusive) |
| `branches` | array | Fork 時必填 | 分支列表 |
| `config` | object | 否 | 閘道配置 |

### 響應

**成功 (200)**:

```json
{
  "gateway_id": "550e8400-e29b-41d4-a716-446655440001",
  "execution_id": "550e8400-e29b-41d4-a716-446655440000",
  "gateway_type": "fork",
  "status": "completed",
  "branches_created": ["branch_a", "branch_b", "branch_c"],
  "timestamp": "2025-12-05T10:00:00Z"
}
```

---

## GET /concurrent/executions/{execution_id}

查詢並行執行狀態。

### 路徑參數

| 參數 | 類型 | 說明 |
|------|------|------|
| `execution_id` | UUID | 執行 ID |

### 響應

**成功 (200)**:

```json
{
  "execution_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "progress": {
    "total_tasks": 5,
    "completed_tasks": 3,
    "failed_tasks": 0,
    "pending_tasks": 2
  },
  "started_at": "2025-12-05T10:00:00Z",
  "estimated_completion": "2025-12-05T10:05:00Z",
  "task_details": [
    {
      "task_id": "task_1",
      "status": "completed",
      "duration_ms": 500
    }
  ]
}
```

---

## POST /concurrent/executions/{execution_id}/cancel

取消並行執行。

### 路徑參數

| 參數 | 類型 | 說明 |
|------|------|------|
| `execution_id` | UUID | 執行 ID |

### 請求

```json
{
  "reason": "User requested cancellation",
  "graceful": true
}
```

### 響應

**成功 (200)**:

```json
{
  "execution_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "cancelled",
  "cancelled_at": "2025-12-05T10:05:00Z",
  "tasks_cancelled": 2,
  "tasks_completed_before_cancel": 3
}
```

---

## GET /concurrent/stats

獲取並行執行統計資訊。

### 查詢參數

| 參數 | 類型 | 說明 |
|------|------|------|
| `time_range` | string | 時間範圍 (1h/24h/7d)，預設 24h |

### 響應

**成功 (200)**:

```json
{
  "time_range": "24h",
  "total_executions": 150,
  "successful_executions": 142,
  "failed_executions": 8,
  "average_execution_time_ms": 2500,
  "average_tasks_per_execution": 4.5,
  "throughput_improvement": 3.2,
  "peak_concurrent_tasks": 25
}
```

---

## 錯誤碼

| 錯誤碼 | HTTP 狀態 | 說明 |
|--------|----------|------|
| `validation_error` | 400 | 請求參數驗證失敗 |
| `execution_not_found` | 404 | 執行不存在 |
| `execution_timeout` | 408 | 執行超時 |
| `resource_exhausted` | 429 | 資源耗盡 |
| `internal_error` | 500 | 內部錯誤 |
