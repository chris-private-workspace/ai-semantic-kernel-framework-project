# Phase 28: 三層意圖路由架構文檔

**版本**: 1.0
**創建日期**: 2026-01-16
**最後更新**: 2026-01-16
**Phase**: 28 (Sprint 91-99)
**Story Points**: 235 pts

---

## 概述

Phase 28 實現了完整的 **三層意圖路由系統**，用於智能處理 IT 服務請求。系統採用漸進式分類策略：
- **Layer 1**: Pattern Matcher (規則基礎，高速)
- **Layer 2**: Semantic Router (向量相似度)
- **Layer 3**: LLM Classifier (語義理解，兜底)

配合 **GuidedDialogEngine** 進行多輪對話收集資訊，**InputGateway** 處理多來源輸入，以及 **HITLController** 管理人機協作審批流程。

---

## 架構圖

```
┌───────────────────────────────────────────────────────────────────────────┐
│                           Input Sources                                    │
├───────────────┬───────────────────┬───────────────────────────────────────┤
│  User Input   │  ServiceNow       │  Prometheus                           │
│  (Chat/API)   │  (Webhook)        │  (AlertManager)                       │
└───────┬───────┴─────────┬─────────┴────────────────┬──────────────────────┘
        │                 │                          │
        └─────────────────┼──────────────────────────┘
                          ▼
              ┌───────────────────────┐
              │    InputGateway       │
              │  (Source Detection)   │
              └───────────┬───────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ ServiceNow    │ │ Prometheus    │ │ User Input    │
│ Handler       │ │ Handler       │ │ Handler       │
│ (Simplified)  │ │ (Simplified)  │ │ (Full Routing)│
└───────┬───────┘ └───────┬───────┘ └───────┬───────┘
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ▼
              ┌───────────────────────┐
              │ BusinessIntentRouter  │
              │  (Three-Layer)        │
              └───────────┬───────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ Layer 1:      │ │ Layer 2:      │ │ Layer 3:      │
│ Pattern       │ │ Semantic      │ │ LLM           │
│ Matcher       │ │ Router        │ │ Classifier    │
│ (< 10ms)      │ │ (< 100ms)     │ │ (< 2000ms)    │
└───────┬───────┘ └───────┬───────┘ └───────┬───────┘
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ▼
              ┌───────────────────────┐
              │ CompletenessChecker   │
              │ (Information Gap)     │
              └───────────┬───────────┘
                          │
            ┌─────────────┴─────────────┐
            │                           │
            ▼                           ▼
    [completeness >= 0.8]       [completeness < 0.8]
            │                           │
            ▼                           ▼
┌───────────────────────┐   ┌───────────────────────┐
│ RiskAssessor          │   │ GuidedDialogEngine    │
│ (Risk Evaluation)     │   │ (Multi-turn Dialog)   │
└───────────┬───────────┘   └───────────┬───────────┘
            │                           │
            │                   ┌───────┴───────┐
            │                   │               │
            ▼                   ▼               ▼
┌───────────────────────┐ ┌─────────────┐ ┌─────────────┐
│ HITLController        │ │ Question    │ │ Context     │
│ (Approval Workflow)   │ │ Generator   │ │ Manager     │
└───────────┬───────────┘ └─────────────┘ └─────────────┘
            │
┌───────────┴───────────┐
│ Approval Required?    │
├───────────────────────┤
│  Yes → Teams/Email    │
│  No  → Direct Execute │
└───────────────────────┘
```

---

## 核心組件

### 1. InputGateway (Sprint 95)

**職責**: 統一入口，識別來源並路由到對應處理器

**位置**: `backend/src/integrations/orchestration/input_gateway/`

```python
from orchestration import InputGateway, IncomingRequest, SourceType

# 創建 Gateway
gateway = InputGateway(
    source_handlers={
        "servicenow": ServiceNowHandler(),
        "prometheus": PrometheusHandler(),
    },
    business_router=BusinessIntentRouter(...),
)

# 處理請求
request = IncomingRequest(
    content="ETL Pipeline 失敗了",
    source_type="user",
)
decision = await gateway.process(request)
```

**Source Handlers**:
| Handler | 來源 | 處理方式 | 目標延遲 |
|---------|------|----------|----------|
| ServiceNowHandler | ServiceNow Webhook | 直接映射 | < 10ms |
| PrometheusHandler | Prometheus AlertManager | 規則映射 | < 10ms |
| UserInputHandler | 用戶輸入 | 三層路由 | < 500ms |

### 2. BusinessIntentRouter (Sprint 93)

**職責**: 三層漸進式意圖分類

**位置**: `backend/src/integrations/orchestration/intent_router/`

```python
from orchestration import BusinessIntentRouter, RouterConfig

router = BusinessIntentRouter(
    pattern_matcher=PatternMatcher(rules_path="rules.yaml"),
    semantic_router=SemanticRouter(routes=semantic_routes),
    llm_classifier=LLMClassifier(api_key="..."),
    config=RouterConfig(
        pattern_threshold=0.90,
        semantic_threshold=0.85,
        enable_llm_fallback=True,
    ),
)

decision = await router.route("ETL 今天跑失敗了")
print(decision.intent_category)  # ITIntentCategory.INCIDENT
print(decision.routing_layer)    # "pattern"
print(decision.confidence)       # 0.95
```

**三層架構**:

| Layer | 組件 | 技術 | 目標 P95 | 準確率 |
|-------|------|------|----------|--------|
| Layer 1 | PatternMatcher | 正則表達式 | < 10ms | > 95% |
| Layer 2 | SemanticRouter | 向量相似度 | < 100ms | > 90% |
| Layer 3 | LLMClassifier | Claude Haiku | < 2000ms | > 85% |

### 3. GuidedDialogEngine (Sprint 94)

**職責**: 多輪對話引導，增量式資訊收集

**位置**: `backend/src/integrations/orchestration/guided_dialog/`

```python
from orchestration import GuidedDialogEngine, create_mock_dialog_engine

engine = GuidedDialogEngine(
    router=business_router,
    context_manager=context_manager,
    question_generator=question_generator,
    max_turns=5,
)

# 開始對話
response = await engine.start_dialog("ETL 有問題")
print(response.questions)  # [請問是哪個系統？, ...]

# 處理回應 (增量更新，不重新 LLM 分類)
response = await engine.process_response("是 DataWarehouse 的 ETL")
print(response.state.routing_decision.sub_intent)  # "etl_failure"
```

**核心特性**:
- **增量更新**: 用戶回應不觸發 LLM 重新分類，僅更新 context
- **規則細化**: RefinementRules 根據關鍵字細化 sub_intent
- **範本問題**: QuestionGenerator 根據 intent 生成問題
- **最大輪數**: 超過 max_turns 自動 Handoff

### 4. RiskAssessor (Sprint 96)

**職責**: 評估操作風險等級，決定是否需要 HITL 審批

**位置**: `backend/src/integrations/orchestration/risk_assessor/`

```python
from orchestration import RiskAssessor, AssessmentContext

assessor = RiskAssessor()

context = AssessmentContext(
    routing_decision=decision,
    user_input="系統完全當機了",
)
assessment = assessor.assess(context)

print(assessment.overall_risk)      # RiskLevel.CRITICAL
print(assessment.requires_approval) # True
print(assessment.approval_type)     # "multi"
```

**風險等級**:
| Risk Level | 條件 | 審批類型 |
|------------|------|----------|
| CRITICAL | 系統停機、業務中斷 | 多人審批 |
| HIGH | 生產環境變更、資料庫操作 | 單人審批 |
| MEDIUM | 一般事件處理 | 無需審批 |
| LOW | 查詢、簡單請求 | 無需審批 |

### 5. HITLController (Sprint 97)

**職責**: 人機協作審批流程管理

**位置**: `backend/src/integrations/orchestration/hitl/`

```python
from orchestration import (
    HITLController,
    InMemoryApprovalStorage,
    TeamsNotificationService,
)

controller = HITLController(
    storage=InMemoryApprovalStorage(),
    notification_service=TeamsNotificationService(webhook_url),
    default_timeout_minutes=30,
)

# 創建審批請求
request = await controller.request_approval(
    routing_decision=decision,
    risk_assessment=assessment,
    requester="user@example.com",
)

# 處理審批
approved_request = await controller.process_approval(
    request_id=request.request_id,
    approved=True,
    approver="admin@example.com",
)
```

**審批狀態**:
```
PENDING → APPROVED
        → REJECTED
        → EXPIRED (timeout)
        → CANCELLED (by requester)
```

---

## 數據模型

### ITIntentCategory

```python
class ITIntentCategory(Enum):
    INCIDENT = "incident"   # 事件報告
    REQUEST = "request"     # 服務請求
    CHANGE = "change"       # 變更請求
    QUERY = "query"         # 一般查詢
    UNKNOWN = "unknown"     # 無法分類
```

### RoutingDecision

```python
@dataclass
class RoutingDecision:
    intent_category: ITIntentCategory
    sub_intent: Optional[str]       # e.g., "etl_failure"
    confidence: float               # 0.0 - 1.0
    workflow_type: WorkflowType     # SIMPLE/SEQUENTIAL/MAGENTIC
    risk_level: RiskLevel           # LOW/MEDIUM/HIGH/CRITICAL
    completeness: CompletenessInfo
    routing_layer: str              # pattern/semantic/llm
    reasoning: str
    processing_time_ms: float
```

### CompletenessInfo

```python
@dataclass
class CompletenessInfo:
    is_complete: bool               # 資訊是否完整
    missing_fields: List[str]       # ["system_name", "error_message"]
    completeness_score: float       # 0.0 - 1.0
    suggestions: List[str]          # 建議問題
```

---

## 配置指南

### Pattern Rules YAML

```yaml
# rules.yaml
rules:
  - id: incident_etl_failure
    category: incident
    sub_intent: etl_failure
    patterns:
      - "ETL.*失敗"
      - "ETL.*錯誤"
      - "資料處理.*異常"
    priority: 100
    workflow_type: sequential
    risk_level: high
    enabled: true

  - id: request_access
    category: request
    sub_intent: access_request
    patterns:
      - "申請.*權限"
      - "需要.*存取"
    priority: 80
    workflow_type: simple
    risk_level: low
    enabled: true
```

### Semantic Routes

```python
routes = [
    SemanticRoute(
        name="database_issue",
        category=ITIntentCategory.INCIDENT,
        sub_intent="database_issue",
        utterances=[
            "資料庫連線有問題",
            "DB 連不上",
            "查詢很慢",
        ],
        workflow_type=WorkflowType.SEQUENTIAL,
        risk_level=RiskLevel.HIGH,
    ),
]
```

### 環境變數

```bash
# Pattern Matcher
PATTERN_CONFIDENCE_THRESHOLD=0.90
PATTERN_RULES_PATH=/app/config/rules.yaml

# Semantic Router
SEMANTIC_SIMILARITY_THRESHOLD=0.85
EMBEDDING_MODEL=text-embedding-ada-002

# LLM Classifier
ENABLE_LLM_FALLBACK=true
LLM_TIMEOUT_SECONDS=2.0
ANTHROPIC_API_KEY=xxx

# Completeness
COMPLETENESS_THRESHOLD=0.80
MAX_DIALOG_TURNS=5

# HITL
HITL_TIMEOUT_MINUTES=30
TEAMS_WEBHOOK_URL=https://xxx
```

---

## 性能指標

### 延遲目標

| 組件 | P95 目標 | P99 目標 |
|------|----------|----------|
| Pattern Matcher | < 10ms | < 20ms |
| Semantic Router | < 100ms | < 200ms |
| LLM Classifier | < 2000ms | < 3000ms |
| Overall (no LLM) | < 500ms | < 800ms |
| System Source | < 10ms | < 20ms |

### 準確率目標

| 指標 | 目標值 |
|------|--------|
| Pattern 匹配覆蓋率 | > 70% |
| 三層路由整體準確率 | > 95% |
| GuidedDialog 平均輪數 | < 3 |
| 完整度評估準確率 | > 90% |

---

## 故障排除

### 常見問題

**1. Pattern 沒有匹配**

```python
# 檢查規則是否載入
print(pattern_matcher.get_rules())

# 測試單一規則
result = pattern_matcher.test_pattern("ETL 失敗", "incident_etl_failure")
print(result.matched, result.confidence)
```

**2. 完整度一直很低**

```python
# 檢查完整度規則
print(completeness_checker.get_rules(ITIntentCategory.INCIDENT))

# 手動測試
result = completeness_checker.check(
    intent_category=ITIntentCategory.INCIDENT,
    user_input="ETL 失敗了",
)
print(result.missing_fields)
```

**3. HITL 審批超時**

```python
# 檢查待審批請求
pending = await controller.list_pending_requests()
for req in pending:
    print(f"{req.request_id}: {req.expires_at}")

# 調整超時時間
controller.default_timeout_minutes = 60
```

**4. Semantic Router 準確率低**

```python
# 檢查 routes 是否載入
print(semantic_router.get_routes())

# 測試相似度
result = await semantic_router.route("資料庫有問題")
print(f"similarity: {result.similarity}, route: {result.route_name}")

# 調整閾值
config.semantic_threshold = 0.80
```

---

## 監控和指標

### OpenTelemetry 指標

```python
from orchestration.metrics import get_metrics_collector

collector = get_metrics_collector()

# 記錄路由請求
collector.record_routing_request(
    intent_category="incident",
    layer_used="pattern",
    latency_seconds=0.005,
    confidence=0.95,
)

# 獲取指標
metrics = collector.get_metrics()
```

### 關鍵指標

| 指標名稱 | 類型 | 說明 |
|----------|------|------|
| orchestration_routing_requests_total | Counter | 路由請求總數 |
| orchestration_routing_latency_seconds | Histogram | 路由延遲 |
| orchestration_dialog_rounds_total | Counter | 對話輪數 |
| orchestration_hitl_requests_total | Counter | HITL 請求數 |
| orchestration_hitl_approval_time_seconds | Histogram | 審批時間 |

---

## 相關文檔

| 文檔 | 位置 |
|------|------|
| Sprint 91-99 計劃 | `docs/03-implementation/sprint-planning/phase-28/` |
| API 參考 | `docs/api/orchestration-api-reference.md` |
| 單元測試 | `backend/tests/unit/orchestration/` |
| 整合測試 | `backend/tests/integration/orchestration/` |
| 性能測試 | `backend/tests/performance/` |

---

**Phase 28 完成日期**: 2026-01-16
**總 Story Points**: 235 pts
**Sprint 數量**: 9 (Sprint 91-99)
