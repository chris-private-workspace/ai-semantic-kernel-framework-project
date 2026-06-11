# 效能監控 API 參考

## 概述

效能監控 API 提供系統效能監控、分析會話管理、優化建議等功能。

**Base URL**: `/api/v1/performance`

---

## 端點列表

| 方法 | 端點 | 說明 |
|------|------|------|
| GET | `/metrics` | 獲取效能指標 |
| POST | `/profile/start` | 開始分析會話 |
| POST | `/profile/stop` | 結束分析會話 |
| POST | `/profile/metric` | 記錄指標 |
| GET | `/profile/sessions` | 列出分析會話 |
| GET | `/profile/summary/{id}` | 獲取會話摘要 |
| POST | `/optimize` | 執行優化分析 |
| GET | `/collector/summary` | 收集器摘要 |
| GET | `/collector/alerts` | 獲取警告 |
| POST | `/collector/threshold` | 設置閾值 |
| GET | `/health` | 健康檢查 |

---

## GET /performance/metrics

獲取完整的效能指標。

### 查詢參數

| 參數 | 類型 | 說明 |
|------|------|------|
| `range` | string | 時間範圍 (1h/24h/7d)，預設 24h |

### 響應

**成功 (200)**:

```json
{
  "system_metrics": {
    "cpu_percent": 45.2,
    "memory_percent": 62.5,
    "disk_percent": 38.0,
    "network_bytes_sent": 1234567890,
    "network_bytes_recv": 9876543210
  },
  "phase2_stats": {
    "concurrent_executions": 12,
    "handoff_success_rate": 97.5,
    "groupchat_sessions": 8,
    "planning_accuracy": 89.3,
    "nested_workflow_depth": 4,
    "avg_latency_ms": 145.0,
    "throughput_improvement": 3.2
  },
  "recommendations": [
    {
      "id": "1",
      "type": "optimization",
      "title": "Enable connection pooling",
      "description": "Connection pooling can reduce latency by 25%",
      "impact": "high"
    }
  ],
  "history": [
    {
      "timestamp": "00:00",
      "cpu": 42.0,
      "memory": 60.0,
      "latency": 140.0
    }
  ]
}
```

---

## POST /performance/profile/start

開始效能分析會話。

### 請求

```json
{
  "name": "api_performance_test",
  "metadata": {
    "environment": "production",
    "test_type": "load_test"
  }
}
```

### 響應

**成功 (200)**:

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "api_performance_test",
  "status": "active",
  "started_at": "2025-12-05T10:00:00Z",
  "metrics_count": 0
}
```

---

## POST /performance/profile/stop

結束當前分析會話。

### 響應

**成功 (200)**:

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "api_performance_test",
  "status": "completed",
  "started_at": "2025-12-05T10:00:00Z",
  "ended_at": "2025-12-05T10:30:00Z",
  "metrics_count": 1500
}
```

**錯誤 (404)**:

```json
{
  "error": "no_active_session",
  "message": "No active profiling session"
}
```

---

## POST /performance/profile/metric

記錄效能指標。

### 請求

```json
{
  "name": "api_response_time",
  "metric_type": "latency",
  "value": 125.5,
  "unit": "ms",
  "tags": {
    "endpoint": "/api/v1/agents",
    "method": "GET"
  }
}
```

### 參數說明

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `name` | string | 是 | 指標名稱 |
| `metric_type` | string | 是 | 指標類型 (latency/throughput/memory/cpu/concurrency/error_rate) |
| `value` | float | 是 | 指標值 |
| `unit` | string | 否 | 單位 |
| `tags` | object | 否 | 標籤 |

### 響應

**成功 (200)**:

```json
{
  "status": "recorded",
  "metric": "api_response_time"
}
```

---

## GET /performance/profile/sessions

列出所有分析會話。

### 查詢參數

| 參數 | 類型 | 說明 |
|------|------|------|
| `limit` | integer | 返回數量限制，預設 10，最大 100 |

### 響應

**成功 (200)**:

```json
{
  "sessions": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "api_performance_test",
      "started_at": "2025-12-05T10:00:00Z",
      "ended_at": "2025-12-05T10:30:00Z",
      "metrics_count": 1500,
      "status": "completed"
    }
  ],
  "total": 1
}
```

---

## GET /performance/profile/summary/{session_id}

獲取分析會話摘要。

### 路徑參數

| 參數 | 類型 | 說明 |
|------|------|------|
| `session_id` | UUID | 會話 ID |

### 響應

**成功 (200)**:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "api_performance_test",
  "started_at": "2025-12-05T10:00:00Z",
  "ended_at": "2025-12-05T10:30:00Z",
  "summary": {
    "duration_seconds": 1800,
    "total_metrics": 1500,
    "metrics_by_type": {
      "latency": {
        "count": 500,
        "min": 50.0,
        "max": 500.0,
        "avg": 125.5,
        "median": 120.0,
        "p95": 200.0,
        "p99": 350.0
      },
      "throughput": {
        "count": 500,
        "min": 100.0,
        "max": 1000.0,
        "avg": 500.0,
        "median": 480.0,
        "p95": 850.0,
        "p99": 950.0
      }
    }
  },
  "metrics_count": 1500
}
```

---

## POST /performance/optimize

執行效能優化分析。

### 請求

```json
{
  "target": "api",
  "strategies": ["caching", "connection_pooling"]
}
```

### 參數說明

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `target` | string | 是 | 優化目標 (api/db/cache) |
| `strategies` | array | 否 | 指定優化策略 |

### 響應

**成功 (200)**:

```json
{
  "target": "api",
  "success": true,
  "before_metrics": {
    "avg_latency_ms": 200.0,
    "throughput": 500.0,
    "error_rate": 0.02
  },
  "after_metrics": {
    "avg_latency_ms": 150.0,
    "throughput": 650.0,
    "error_rate": 0.01
  },
  "improvement_percent": 25.0,
  "strategies_applied": ["caching", "connection_pooling"],
  "recommendations": [
    "Consider query optimization for further improvement"
  ]
}
```

---

## GET /performance/collector/alerts

獲取效能警告。

### 查詢參數

| 參數 | 類型 | 說明 |
|------|------|------|
| `clear` | boolean | 是否清除警告，預設 false |

### 響應

**成功 (200)**:

```json
{
  "alerts": [
    {
      "id": "1",
      "metric_name": "cpu_percent",
      "value": 95.0,
      "threshold": 80.0,
      "severity": "high",
      "message": "CPU usage exceeded threshold",
      "timestamp": "2025-12-05T10:00:00Z"
    }
  ],
  "total": 1
}
```

---

## POST /performance/collector/threshold

設置指標閾值。

### 查詢參數

| 參數 | 類型 | 說明 |
|------|------|------|
| `metric_name` | string | 指標名稱 |
| `min_value` | float | 最小閾值 (可選) |
| `max_value` | float | 最大閾值 (可選) |

### 響應

**成功 (200)**:

```json
{
  "status": "set",
  "metric": "cpu_percent",
  "min": null,
  "max": 80.0
}
```

---

## GET /performance/health

檢查效能模組健康狀態。

### 響應

**成功 (200)**:

```json
{
  "status": "healthy",
  "cpu_percent": 45.0,
  "memory_percent": 62.0,
  "timestamp": "2025-12-05T10:00:00Z"
}
```

---

## 錯誤碼

| 錯誤碼 | HTTP 狀態 | 說明 |
|--------|----------|------|
| `validation_error` | 400 | 請求參數驗證失敗 |
| `invalid_metric_type` | 400 | 無效的指標類型 |
| `session_not_found` | 404 | 會話不存在 |
| `no_active_session` | 404 | 無活躍會話 |
| `internal_error` | 500 | 內部錯誤 |
