# Sprint 99: 技術決策

## 概述

本文檔記錄 Sprint 99 (E2E 測試 + 性能優化 + 文檔) 的關鍵技術決策。

---

## 決策 99-1: E2E 測試架構

### 問題

如何設計 E2E 測試以覆蓋完整的三層路由流程？

### 決策

採用 **場景驅動測試** 架構：

```python
# 測試場景定義
test_scenarios = [
    {
        "name": "pattern_direct_match",
        "input": "ETL Pipeline 失敗了",
        "expected_intent": "incident",
        "expected_sub_intent": "etl_failure",
        "expected_layer": "pattern",
        "max_latency_ms": 50
    },
    {
        "name": "semantic_match",
        "input": "資料庫連線好像有問題",
        "expected_intent": "incident",
        "expected_sub_intent": "database_issue",
        "expected_layer": "semantic"
    },
    # ...
]
```

### 理由

1. **可讀性**: 場景定義清晰，易於理解測試目的
2. **可維護性**: 新增場景只需添加數據，不需修改測試代碼
3. **可追蹤性**: 每個場景對應 sprint-99-plan.md 中的測試場景

---

## 決策 99-2: 性能測試策略

### 問題

如何有效測量各層的 P95 延遲？

### 決策

採用 **統計抽樣 + 百分位數計算**：

```python
import statistics
import numpy as np

class PerformanceMetrics:
    def __init__(self, measurements: List[float]):
        self.measurements = sorted(measurements)
        self.p50 = np.percentile(measurements, 50)
        self.p95 = np.percentile(measurements, 95)
        self.p99 = np.percentile(measurements, 99)
        self.mean = statistics.mean(measurements)
        self.std = statistics.stdev(measurements)
```

### 測試配置

| 組件 | 調用次數 | 目標 P95 |
|------|---------|---------|
| Pattern Matcher | 1000 | < 10ms |
| Semantic Router | 500 | < 100ms |
| LLM Classifier | 100 | < 2000ms |
| 整體 (無 LLM) | 500 | < 500ms |

### 理由

1. **統計有效性**: 足夠的樣本量確保結果可靠
2. **實際負載**: 模擬真實使用場景的調用頻率
3. **分層測量**: 每層獨立測量，便於識別瓶頸

---

## 決策 99-3: 監控指標設計

### 問題

應該收集哪些監控指標？如何整合 OpenTelemetry？

### 決策

採用 **四大指標類別** 設計：

```python
# 1. 路由指標
routing_requests_total = Counter(
    "orchestration_routing_requests_total",
    "Total routing requests",
    ["intent_category", "layer_used"]
)

routing_latency_seconds = Histogram(
    "orchestration_routing_latency_seconds",
    "Routing latency",
    ["layer_used"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
)

# 2. 對話指標
dialog_rounds_total = Counter(
    "orchestration_dialog_rounds_total",
    "Total dialog rounds"
)

dialog_completion_rate = Gauge(
    "orchestration_dialog_completion_rate",
    "Dialog completion rate"
)

# 3. HITL 指標
hitl_requests_total = Counter(
    "orchestration_hitl_requests_total",
    "Total HITL requests",
    ["risk_level", "status"]
)

hitl_approval_time_seconds = Histogram(
    "orchestration_hitl_approval_time_seconds",
    "HITL approval time",
    buckets=[60, 300, 600, 1800, 3600]
)

# 4. 系統指標
system_source_requests_total = Counter(
    "orchestration_system_source_requests_total",
    "Total system source requests",
    ["source_type"]
)
```

### 理由

1. **可觀測性**: 符合 RED (Rate, Errors, Duration) 方法論
2. **告警支援**: 指標設計支援基於閾值的告警
3. **儀表板友好**: 便於 Grafana 視覺化

---

## 決策 99-4: 文檔結構

### 問題

如何組織 Phase 28 的文檔以便於維護和查閱？

### 決策

採用 **三層文檔結構**：

```
docs/
├── 03-implementation/sprint-planning/
│   ├── README.md                    # 總覽 (更新)
│   └── phase-28/
│       ├── ARCHITECTURE.md          # 架構說明 (新增)
│       ├── sprint-91-plan.md        # Sprint 計劃
│       └── ...
│
├── api/
│   └── orchestration-api-reference.md  # API 參考 (新增)
│
└── backend/
    └── CLAUDE.md                    # 開發指南 (更新)
```

### 文檔內容規範

1. **ARCHITECTURE.md**: 高層架構、組件關係、數據流
2. **API Reference**: OpenAPI 格式、範例請求/回應
3. **CLAUDE.md**: 開發者快速上手指南

### 理由

1. **職責分離**: 不同文檔服務不同受眾
2. **易於導航**: 層次結構清晰
3. **版本控制友好**: 變更可追蹤

---

## 決策 99-5: 測試 Mock 策略

### 問題

E2E 測試中如何處理外部依賴 (LLM API、Redis、Webhook)?

### 決策

採用 **分層 Mock** 策略：

```python
# Level 1: 完全 Mock (單元測試級別)
@pytest.fixture
def mock_router():
    return MockBusinessIntentRouter()

# Level 2: 外部服務 Mock (E2E 測試級別)
@pytest.fixture
def e2e_router():
    return BusinessIntentRouter(
        pattern_matcher=PatternMatcher(rules_dict=REAL_RULES),
        semantic_router=SemanticRouter(routes=REAL_ROUTES),
        llm_classifier=MockLLMClassifier(),  # Mock LLM
    )

# Level 3: 完全真實 (集成測試/需要環境變量)
@pytest.fixture
def real_router():
    return create_router(
        pattern_rules_path="rules.yaml",
        llm_api_key=os.environ["ANTHROPIC_API_KEY"],
    )
```

### E2E 測試策略

| 組件 | Mock | 原因 |
|------|------|------|
| Pattern Matcher | 真實 | 無外部依賴 |
| Semantic Router | Mock | 避免向量計算開銷 |
| LLM Classifier | Mock | 避免 API 調用成本 |
| HITL Storage | InMemory | 避免 Redis 依賴 |
| Notification | Mock | 避免 Webhook 調用 |

### 理由

1. **測試速度**: E2E 測試應該快速運行
2. **成本控制**: 避免不必要的 LLM API 調用
3. **環境獨立**: 測試不依賴外部服務

---

## 決策總結

| 決策 | 選項 | 理由 |
|------|------|------|
| E2E 測試架構 | 場景驅動 | 可讀性、可維護性 |
| 性能測試 | 統計抽樣 | 統計有效性 |
| 監控指標 | 四類指標 | 可觀測性 |
| 文檔結構 | 三層結構 | 職責分離 |
| Mock 策略 | 分層 Mock | 測試速度、成本控制 |

---

**記錄日期**: 2026-01-16
**記錄人**: Claude Code
