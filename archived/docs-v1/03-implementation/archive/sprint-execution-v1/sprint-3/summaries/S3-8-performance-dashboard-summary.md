# S3-8: Performance Dashboard - 實現摘要

**Story ID**: S3-8
**標題**: Performance Monitoring Dashboard
**Story Points**: 3
**狀態**: ✅ 已完成
**完成日期**: 2025-11-25

---

## 📋 驗收標準達成情況

| 驗收標準 | 狀態 | 說明 |
|---------|------|------|
| P95/P99 延遲顯示 | ✅ | 百分位計算 |
| RPS 顯示 | ✅ | 每秒請求數 |
| 錯誤率顯示 | ✅ | 5xx 錯誤百分比 |
| 資源使用率 | ✅ | CPU/Memory 監控 |

---

## 🔧 技術實現

### PerformanceCollector

```python
# backend/src/api/v1/performance/routes.py

@dataclass
class RequestMetric:
    method: str
    path: str
    status_code: int
    duration_ms: float
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class PercentileStats:
    p50: float
    p75: float
    p90: float
    p95: float
    p99: float
    count: int

class PerformanceCollector:
    """性能數據收集器"""
    _instance = None
    _lock = threading.Lock()

    def record_request(self, method: str, path: str, status_code: int, duration_ms: float):
        """記錄請求"""
        metric = RequestMetric(method, path, status_code, duration_ms)
        self._metrics.append(metric)

    def get_percentile_stats(self, window_minutes: int = 5) -> PercentileStats:
        """計算百分位統計"""
        latencies = self._get_recent_latencies(window_minutes)
        if not latencies:
            return PercentileStats(0, 0, 0, 0, 0, 0)

        sorted_latencies = sorted(latencies)
        n = len(sorted_latencies)

        return PercentileStats(
            p50=sorted_latencies[int(n * 0.50)],
            p75=sorted_latencies[int(n * 0.75)],
            p90=sorted_latencies[int(n * 0.90)],
            p95=sorted_latencies[int(n * 0.95)],
            p99=sorted_latencies[int(n * 0.99)] if n >= 100 else sorted_latencies[-1],
            count=n
        )

    def get_rps(self, window_seconds: int = 60) -> float:
        """計算每秒請求數"""

    def get_error_rate(self, window_minutes: int = 5) -> float:
        """計算錯誤率 (5xx)"""
```

### Grafana Dashboard

```json
{
  "title": "Performance Dashboard",
  "panels": [
    {
      "title": "API Latency Stats",
      "type": "stat",
      "gridPos": {"h": 4, "w": 12}
    },
    {
      "title": "Requests Per Second",
      "type": "gauge",
      "gridPos": {"h": 4, "w": 6}
    },
    {
      "title": "Error Rate",
      "type": "gauge",
      "gridPos": {"h": 4, "w": 6}
    },
    {
      "title": "Latency Distribution",
      "type": "histogram",
      "gridPos": {"h": 8, "w": 12}
    },
    {
      "title": "CPU Usage",
      "type": "gauge"
    },
    {
      "title": "Memory Usage",
      "type": "gauge"
    }
  ]
}
```

### 性能告警規則

```yaml
# monitoring/prometheus/rules/performance-alerts.yml
groups:
  - name: performance-alerts
    rules:
      - alert: HighApiLatency
        expr: histogram_quantile(0.95, http_request_duration_seconds) > 0.5
        labels:
          severity: warning

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.01
        labels:
          severity: critical
```

### API 端點

| 端點 | 說明 |
|------|------|
| GET /performance/latency | 延遲統計 |
| GET /performance/throughput | 吞吐量 |
| GET /performance/error-rate | 錯誤率 |
| GET /performance/resources | 資源使用 |
| GET /performance/summary | 綜合摘要 |

---

## 📁 代碼位置

```
backend/src/api/v1/performance/
├── __init__.py
└── routes.py                  # 性能收集器和 API

monitoring/grafana/provisioning/dashboards/
└── performance-dashboard.json # Dashboard 定義

monitoring/prometheus/rules/
└── performance-alerts.yml     # 告警規則

backend/tests/unit/
└── test_performance_monitoring.py  # 27 個測試
```

---

## 🧪 測試覆蓋

- PerformanceCollector 單例測試
- 請求記錄測試
- 百分位計算測試
- RPS 計算測試
- 錯誤率計算測試
- 線程安全測試

**測試結果**: 27/27 通過 ✅

---

## 📝 備註

- 使用滑動窗口計算指標
- 支援資源監控 (psutil)
- Dashboard 自動刷新

---

**生成日期**: 2025-11-26
