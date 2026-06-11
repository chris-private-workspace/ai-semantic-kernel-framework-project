# Sprint 95: InputGateway + SourceHandlers

## 概述

Sprint 95 專注於建立 **InputGateway** 輸入閘道和 **SourceHandlers** 來源處理器，實現系統來源的簡化處理路徑。

## 目標

1. 實現 InputGateway 主類
2. 實現 BaseSourceHandler 抽象基類
3. 實現 ServiceNowHandler (映射表 + Pattern)
4. 實現 PrometheusHandler
5. 實現 SchemaValidator

## Story Points: 25 點

## 前置條件

- ✅ Sprint 94 完成 (GuidedDialogEngine)
- ✅ BusinessIntentRouter 就緒
- ✅ PatternMatcher 就緒

## 任務分解

### Story 95-1: 實現 InputGateway 主類 (3h, P0)

**目標**: 建立輸入閘道，實現來源識別和分流

**交付物**:
- `backend/src/integrations/orchestration/input_gateway/gateway.py`
- `backend/src/integrations/orchestration/input_gateway/__init__.py`

**驗收標準**:
- [ ] InputGateway 類實現完成
- [ ] process() 方法根據來源分流
- [ ] 系統來源 → SourceHandler
- [ ] 用戶來源 → BusinessIntentRouter

### Story 95-2: 實現 BaseSourceHandler (2h, P0)

**目標**: 定義來源處理器抽象基類

**交付物**:
- `backend/src/integrations/orchestration/input_gateway/source_handlers/base_handler.py`
- `backend/src/integrations/orchestration/input_gateway/source_handlers/__init__.py`

**驗收標準**:
- [ ] BaseSourceHandler ABC 定義完成
- [ ] process() 抽象方法定義
- [ ] 通用輔助方法實現

### Story 95-3: 實現 ServiceNowHandler (4h, P0)

**目標**: 實現 ServiceNow 專用處理器，使用簡化路徑

**交付物**:
- `backend/src/integrations/orchestration/input_gateway/source_handlers/servicenow_handler.py`

**映射表**:

| ServiceNow Category | IT Intent | Sub Intent |
|--------------------|-----------|------------|
| incident/hardware | incident | hardware_failure |
| incident/software | incident | software_issue |
| incident/network | incident | network_failure |
| request/account | request | account_request |
| request/access | request | access_request |
| request/software | request | software_request |
| change/standard | change | standard_change |
| change/emergency | change | emergency_change |

**驗收標準**:
- [ ] ServiceNowHandler 類實現完成
- [ ] 映射表定義完成
- [ ] 當 subcategory 不足時使用 PatternMatcher
- [ ] 跳過 Semantic Router 和 LLM Classifier
- [ ] 延遲 < 10ms

### Story 95-4: 實現 PrometheusHandler (3h, P1)

**目標**: 實現 Prometheus 告警處理器

**交付物**:
- `backend/src/integrations/orchestration/input_gateway/source_handlers/prometheus_handler.py`

**告警映射**:

| Alert Name Pattern | IT Intent | Sub Intent |
|-------------------|-----------|------------|
| `*_high_cpu_*` | incident | performance_issue |
| `*_memory_*` | incident | memory_issue |
| `*_disk_*` | incident | disk_issue |
| `*_down_*` | incident | service_down |

**驗收標準**:
- [ ] PrometheusHandler 類實現完成
- [ ] 告警名稱模式匹配
- [ ] 告警標籤提取
- [ ] 延遲 < 10ms

### Story 95-5: 實現 UserInputHandler (2h, P0)

**目標**: 實現用戶輸入處理器 (走完整流程)

**交付物**:
- `backend/src/integrations/orchestration/input_gateway/source_handlers/user_input_handler.py`

**驗收標準**:
- [ ] UserInputHandler 類實現完成
- [ ] 調用完整三層路由
- [ ] 格式標準化

### Story 95-6: 實現 SchemaValidator (3h, P0)

**目標**: 實現 Schema 驗證器

**交付物**:
- `backend/src/integrations/orchestration/input_gateway/schema_validator.py`

**驗收標準**:
- [ ] SchemaValidator 類實現完成
- [ ] 支援 ServiceNow Schema
- [ ] 支援 Prometheus Schema
- [ ] 驗證錯誤有明確訊息

## 技術設計

### InputGateway 類設計

```python
class InputGateway:
    """
    輸入閘道

    功能:
    1. 來源識別 (系統 vs 用戶)
    2. 系統來源 → 簡化路徑
    3. 用戶來源 → 完整流程
    """

    def __init__(
        self,
        source_handlers: Dict[str, BaseSourceHandler],
        business_router: BusinessIntentRouter,
    ):
        self.source_handlers = source_handlers
        self.business_router = business_router

    async def process(self, request: IncomingRequest) -> RoutingDecision:
        """處理輸入請求"""
        source_type = self._identify_source(request)

        # 系統來源 → 簡化路徑
        if source_type in self.source_handlers:
            handler = self.source_handlers[source_type]
            return await handler.process(request)

        # 用戶來源 → 完整三層路由
        return await self.business_router.route(request.content)

    def _identify_source(self, request: IncomingRequest) -> str:
        """識別來源類型"""
        if "x-servicenow-webhook" in request.headers:
            return "servicenow"
        if "x-prometheus-alertmanager" in request.headers:
            return "prometheus"
        if request.source_type:
            return request.source_type
        return "user"
```

### ServiceNowHandler 類設計

```python
class ServiceNowHandler(BaseSourceHandler):
    """
    ServiceNow 專用處理器

    簡化路徑:
    1. Schema Validator
    2. 映射表 (category → IT Intent)
    3. Pattern Matcher (如果需要)
    4. 跳過 Semantic Router 和 LLM Classifier
    """

    CATEGORY_MAPPING = {
        "incident/hardware": ("incident", "hardware_failure"),
        "incident/software": ("incident", "software_issue"),
        "incident/network": ("incident", "network_failure"),
        "request/account": ("request", "account_request"),
        "request/access": ("request", "access_request"),
        "change/standard": ("change", "standard_change"),
    }

    def __init__(
        self,
        schema_validator: SchemaValidator,
        pattern_matcher: PatternMatcher,
    ):
        self.schema_validator = schema_validator
        self.pattern_matcher = pattern_matcher

    async def process(self, request: IncomingRequest) -> RoutingDecision:
        """處理 ServiceNow Webhook"""
        start_time = time.time()

        # 1. 驗證 Schema
        validated = self.schema_validator.validate(
            request.data, schema="servicenow"
        )

        # 2. 映射 category → IT Intent
        snow_category = f"{validated['category']}/{validated.get('subcategory', '')}"
        mapping = self.CATEGORY_MAPPING.get(snow_category)

        if mapping:
            intent_category, sub_intent = mapping
        else:
            # 3. 使用 Pattern Matcher 分析 short_description
            pattern_result = self.pattern_matcher.match(
                validated.get("short_description", "")
            )
            intent_category = pattern_result.intent_category or ITIntentCategory.INCIDENT
            sub_intent = pattern_result.sub_intent or "general_incident"

        return RoutingDecision(
            intent_category=ITIntentCategory(intent_category),
            sub_intent=sub_intent,
            intent_confidence=1.0,
            completeness=CompletenessInfo(
                score=1.0,
                threshold=0.6,
                missing_fields=[],
                is_sufficient=True,
            ),
            workflow_type=self._get_workflow_type(sub_intent),
            risk_level=self._get_risk_level(intent_category),
            requires_approval=False,
            layer_used="servicenow_mapping",
            latency_ms=(time.time() - start_time) * 1000,
        )
```

### 系統來源簡化路徑

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    系統來源簡化路徑                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ServiceNow Webhook                                                          │
│  {                                                                           │
│    "number": "INC0012345",                                                  │
│    "category": "incident",                                                  │
│    "subcategory": "software",                                               │
│    "short_description": "ETL Pipeline 失敗"                                │
│  }                                                                           │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 1. Schema Validator                                                  │   │
│  │    驗證: number ✓, category ✓, short_description ✓                  │   │
│  └───────────────────────────┬─────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 2. 映射表查找                                                        │   │
│  │    incident/software → (incident, software_issue)                    │   │
│  └───────────────────────────┬─────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 3. 如果 subcategory 不足，使用 Pattern Matcher                       │   │
│  │    "ETL Pipeline 失敗" → "ETL.*失敗" → etl_failure                  │   │
│  └───────────────────────────┬─────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 輸出 RoutingDecision (< 10ms)                                        │   │
│  │   intent_category: incident                                          │   │
│  │   sub_intent: etl_failure                                            │   │
│  │   completeness: 100% (系統來源資訊完整)                              │   │
│  │   layer_used: servicenow_mapping                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ⚠️ 跳過: Semantic Router, LLM Classifier                                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 完成標準

- [ ] 所有 Story 完成
- [ ] 系統來源延遲 < 10ms
- [ ] Schema 驗證正確
- [ ] 映射表覆蓋常見場景
- [ ] 單元測試覆蓋率 > 90%
- [ ] 代碼審查通過

---

**Sprint 開始**: 2026-02-09
**Sprint 結束**: 2026-02-13
**Story Points**: 25
