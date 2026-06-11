# 監控最佳實踐

## 概述

本文檔提供 IPA Platform Phase 2 的監控配置和最佳實踐。

---

## 效能監控設置

### 1. 啟用效能分析器

```python
from src.core.performance import PerformanceProfiler

# 全局分析器實例
profiler = PerformanceProfiler()

# 應用啟動時初始化
@app.on_event("startup")
async def setup_profiler():
    profiler.start_session("application_monitoring")
```

### 2. 自動指標收集

```python
from src.core.performance import MetricCollector

collector = MetricCollector()

# 啟動自動收集
await collector.start(
    collection_interval_seconds=30,
    metrics=["cpu", "memory", "disk", "network"]
)
```

### 3. 設置閾值警報

```python
# CPU 警報
collector.set_threshold("cpu_percent", max_value=80)

# 記憶體警報
collector.set_threshold("memory_percent", max_value=85)

# 延遲警報
collector.set_threshold("avg_latency_ms", max_value=500)

# 錯誤率警報
collector.set_threshold("error_rate", max_value=0.05)
```

---

## Phase 2 功能監控

### 並行執行監控

```python
# 監控並行執行
profiler.record_metric(
    name="concurrent_tasks",
    metric_type=MetricType.CONCURRENCY,
    value=current_concurrent_count
)

# 監控吞吐量
profiler.record_metric(
    name="fork_join_throughput",
    metric_type=MetricType.THROUGHPUT,
    value=tasks_per_second
)
```

### Agent 交接監控

```python
# 交接成功率
handoff_success_rate = completed_handoffs / total_handoffs
profiler.record_metric(
    name="handoff_success_rate",
    metric_type=MetricType.ERROR_RATE,
    value=1 - handoff_success_rate
)

# 交接延遲
profiler.record_metric(
    name="handoff_latency",
    metric_type=MetricType.LATENCY,
    value=handoff_duration_ms,
    unit="ms"
)
```

### 群組對話監控

```python
# 活躍會話數
profiler.record_metric(
    name="active_groupchats",
    metric_type=MetricType.CONCURRENCY,
    value=active_sessions_count
)

# 訊息延遲
profiler.record_metric(
    name="message_latency",
    metric_type=MetricType.LATENCY,
    value=message_processing_time_ms
)
```

---

## 儀表板配置

### Grafana 儀表板

```json
{
  "dashboard": {
    "title": "IPA Platform - Phase 2 Monitoring",
    "panels": [
      {
        "title": "System Resources",
        "type": "timeseries",
        "targets": [
          {"expr": "ipa_cpu_percent"},
          {"expr": "ipa_memory_percent"}
        ]
      },
      {
        "title": "Concurrent Executions",
        "type": "gauge",
        "targets": [
          {"expr": "ipa_concurrent_executions"}
        ]
      },
      {
        "title": "API Latency",
        "type": "histogram",
        "targets": [
          {"expr": "histogram_quantile(0.95, ipa_api_latency)"}
        ]
      }
    ]
  }
}
```

### 關鍵指標面板

| 面板 | 指標 | 警報閾值 |
|------|------|----------|
| CPU 使用率 | `cpu_percent` | > 80% |
| 記憶體使用率 | `memory_percent` | > 85% |
| API 延遲 P95 | `api_latency_p95` | > 500ms |
| 錯誤率 | `error_rate` | > 5% |
| 並發執行數 | `concurrent_executions` | > 50 |
| 交接成功率 | `handoff_success_rate` | < 95% |

---

## 日誌監控

### 結構化日誌

```python
import structlog

logger = structlog.get_logger()

# 記錄執行開始
logger.info("execution_started",
    execution_id=execution.id,
    workflow_id=workflow.id,
    user_id=user.id
)

# 記錄效能指標
logger.info("performance_metric",
    metric_name="api_latency",
    value=latency_ms,
    tags={"endpoint": endpoint, "method": method}
)
```

### 日誌級別配置

```python
LOGGING_CONFIG = {
    "version": 1,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO"
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": "logs/ipa.log",
            "level": "DEBUG"
        }
    },
    "loggers": {
        "src.core.concurrent": {"level": "INFO"},
        "src.core.handoff": {"level": "INFO"},
        "src.core.groupchat": {"level": "INFO"},
        "src.core.performance": {"level": "DEBUG"}
    }
}
```

---

## 健康檢查

### 端點配置

```python
@app.get("/health")
async def health_check():
    checks = {
        "database": await check_database(),
        "redis": await check_redis(),
        "rabbitmq": await check_rabbitmq(),
        "performance": await check_performance_module()
    }

    all_healthy = all(c["status"] == "healthy" for c in checks.values())

    return {
        "status": "healthy" if all_healthy else "unhealthy",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }
```

### Kubernetes Probes

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

---

## 警報配置

### 警報規則

```yaml
alerts:
  - name: HighCPUUsage
    condition: cpu_percent > 80
    duration: 5m
    severity: warning
    notification:
      - teams
      - email

  - name: HighMemoryUsage
    condition: memory_percent > 85
    duration: 5m
    severity: critical
    notification:
      - teams
      - pagerduty

  - name: HighErrorRate
    condition: error_rate > 0.05
    duration: 2m
    severity: critical
    notification:
      - teams
      - slack

  - name: SlowAPIResponse
    condition: api_latency_p95 > 500
    duration: 5m
    severity: warning
    notification:
      - email
```

### 通知整合

```python
from src.infrastructure.notifications import NotificationService

notification_service = NotificationService()

# 發送警報
await notification_service.send_alert(
    title="High CPU Usage Alert",
    message=f"CPU usage is {cpu_percent}%",
    severity="warning",
    channels=["teams", "email"]
)
```

---

## 監控檢查清單

- [ ] 效能分析器已啟用
- [ ] 指標收集已配置
- [ ] 閾值警報已設置
- [ ] 儀表板已建立
- [ ] 日誌記錄已配置
- [ ] 健康檢查端點可用
- [ ] 警報通知已整合
- [ ] 定期審查監控數據
