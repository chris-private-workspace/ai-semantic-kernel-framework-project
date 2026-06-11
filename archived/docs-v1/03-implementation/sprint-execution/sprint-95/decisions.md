# Sprint 95: 技術決策記錄

## 決策 1: InputGateway 來源識別策略

### 背景
需要根據請求來源決定走簡化路徑還是完整三層路由。

### 決策
採用多重識別策略，優先級如下：
1. **Header 識別**: 檢查特定 webhook header (如 `x-servicenow-webhook`, `x-prometheus-alertmanager`)
2. **Source Type 顯式指定**: 請求中的 `source_type` 欄位
3. **預設為用戶來源**: 無法識別時走完整路由

### 理由
- Header 識別最可靠，webhook 通常會帶特定 header
- 允許 API 調用者顯式指定來源類型
- 預設走完整路由確保安全 (不會遺漏重要處理)

---

## 決策 2: ServiceNow 映射表設計

### 背景
ServiceNow webhook 提供 category/subcategory，需要映射到 IT Intent。

### 決策
採用 `{category}/{subcategory}` 組合鍵的映射表：
```python
CATEGORY_MAPPING = {
    "incident/hardware": ("incident", "hardware_failure"),
    "incident/software": ("incident", "software_issue"),
    ...
}
```

### 理由
- 組合鍵提供精確匹配
- 當 subcategory 不存在或不匹配時，回退到 PatternMatcher
- 易於擴展和維護

---

## 決策 3: Prometheus 告警模式匹配

### 背景
Prometheus alertname 沒有標準格式，需要靈活匹配。

### 決策
採用模式列表 + 優先級匹配：
```python
ALERT_PATTERNS = [
    (r".*high_cpu.*", "incident", "performance_issue"),
    (r".*_down.*|.*unavailable.*", "incident", "service_down"),
    ...
]
```

### 理由
- 正則表達式提供靈活性
- 順序處理確保優先級
- 易於添加新的告警模式

---

## 決策 4: SchemaValidator 驗證策略

### 背景
需要驗證不同來源的數據結構。

### 決策
採用聲明式 Schema 定義 + 統一驗證接口：
```python
SCHEMAS = {
    "servicenow": {
        "required": ["number", "category", "short_description"],
        "optional": ["subcategory", "priority", "assignment_group"],
    },
    "prometheus": {
        "required": ["alerts"],
        "nested": {"alerts": ["alertname", "status"]},
    },
}
```

### 理由
- 聲明式配置易於維護
- 支援必填/可選欄位驗證
- 支援嵌套結構驗證
- 提供清晰的錯誤訊息

---

## 決策 5: RoutingDecision 來源標記

### 背景
需要區分由不同處理器產生的 RoutingDecision。

### 決策
使用 `layer_used` 欄位標記來源：
- `servicenow_mapping`: ServiceNow 映射表
- `prometheus_mapping`: Prometheus 告警映射
- `user_input_router`: 用戶輸入三層路由
- `pattern`, `semantic`, `llm`: 三層路由各層

### 理由
- 便於調試和審計
- 支援性能分析
- 便於追蹤決策來源

---

## 決策 6: 系統來源 Completeness 處理

### 背景
系統來源 (ServiceNow, Prometheus) 的資訊通常是完整的。

### 決策
系統來源預設 completeness 為 100%：
```python
completeness=CompletenessInfo(
    score=1.0,
    threshold=0.6,
    missing_fields=[],
    is_sufficient=True,
)
```

### 理由
- 系統來源資料結構固定，已通過 Schema 驗證
- 避免不必要的 completeness 檢查
- 簡化處理流程

---

## 架構圖

```
┌─────────────────────────────────────────────────────────────────┐
│                        InputGateway                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  _identify_source()                      │   │
│  │  Headers → source_type → default                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            │                                     │
│              ┌─────────────┼─────────────┐                      │
│              │             │             │                       │
│              ▼             ▼             ▼                       │
│  ┌───────────────┐ ┌─────────────┐ ┌───────────────┐           │
│  │ ServiceNow    │ │ Prometheus  │ │ User Input    │           │
│  │ Handler       │ │ Handler     │ │ Handler       │           │
│  │               │ │             │ │               │           │
│  │ ┌───────────┐ │ │ ┌─────────┐ │ │ ┌───────────┐ │           │
│  │ │ Mapping   │ │ │ │ Pattern │ │ │ │ Business  │ │           │
│  │ │ Table     │ │ │ │ Match   │ │ │ │ Intent    │ │           │
│  │ └───────────┘ │ │ └─────────┘ │ │ │ Router    │ │           │
│  │       │       │ │      │      │ │ │ (3-layer) │ │           │
│  │       ▼       │ │      ▼      │ │ └───────────┘ │           │
│  │ ┌───────────┐ │ │             │ │               │           │
│  │ │ Pattern   │ │ │             │ │               │           │
│  │ │ Matcher   │ │ │             │ │               │           │
│  │ │ (fallback)│ │ │             │ │               │           │
│  │ └───────────┘ │ │             │ │               │           │
│  └───────────────┘ └─────────────┘ └───────────────┘           │
│              │             │             │                       │
│              └─────────────┼─────────────┘                      │
│                            ▼                                     │
│                   RoutingDecision                                │
└─────────────────────────────────────────────────────────────────┘
```

---

**記錄日期**: 2026-01-15
