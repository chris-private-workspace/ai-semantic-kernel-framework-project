# Phase 28: 三層意圖路由 + Input Gateway (Business Intent Router)

## 概述

Phase 28 專注於建立**三層意圖路由架構**（BusinessIntentRouter）和**輸入閘道系統**（InputGateway），實現 IT 服務管理場景的智能意圖分類、資訊完整度檢查和引導式對話。

本 Phase 採用 **方案 B+**：
- 將完整度檢查整合到 Three-Tier Router 內部
- 使用增量更新機制（不重新分類）
- 系統來源使用簡化路徑（映射表 + Pattern）

## 目標

1. **BusinessIntentRouter** - 三層意圖路由（Pattern → Semantic → LLM）+ 完整度評估
2. **GuidedDialogEngine** - 引導式對話 + 增量更新機制
3. **InputGateway** - 來源識別 + 格式標準化 + 系統來源簡化處理
4. **RiskAssessor** - IT 意圖 → 風險等級映射
5. **HITLController** - 人機協作審批流程

## 前置條件

- ✅ Phase 13 完成 (Hybrid Core Architecture)
- ✅ Phase 14 完成 (Advanced Hybrid Features)
- ✅ Phase 15 完成 (AG-UI Protocol Integration)
- ✅ HybridOrchestratorV2 就緒
- ✅ IntentRouter (FrameworkSelector)、ContextBridge、UnifiedExecutor 就緒
- ✅ RiskAssessment、ModeSwitcher、UnifiedCheckpoint 就緒

## Sprint 規劃

| Sprint | 名稱 | Story Points | 狀態 |
|--------|------|--------------|------|
| [Sprint 91](./sprint-91-plan.md) | Pattern Matcher + 規則定義 | 25 點 | 📋 計劃中 |
| [Sprint 92](./sprint-92-plan.md) | Semantic Router + LLM Classifier | 30 點 | 📋 計劃中 |
| [Sprint 93](./sprint-93-plan.md) | BusinessIntentRouter 整合 + 完整度 | 25 點 | 📋 計劃中 |
| [Sprint 94](./sprint-94-plan.md) | GuidedDialogEngine + 增量更新 | 30 點 | 📋 計劃中 |
| [Sprint 95](./sprint-95-plan.md) | InputGateway + SourceHandlers | 25 點 | 📋 計劃中 |
| [Sprint 96](./sprint-96-plan.md) | RiskAssessor + Policies | 25 點 | 📋 計劃中 |
| [Sprint 97](./sprint-97-plan.md) | HITLController + ApprovalHandler | 30 點 | 📋 計劃中 |
| [Sprint 98](./sprint-98-plan.md) | HybridOrchestratorV2 整合 | 25 點 | 📋 計劃中 |
| [Sprint 99](./sprint-99-plan.md) | E2E 測試 + 性能優化 + 文檔 | 20 點 | 📋 計劃中 |

**總計**: 235 Story Points (9 Sprints)
**預估時程**: 8.5 週 + 1 週緩衝 = 9.5 週

## 架構概覽

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        Phase 28: 方案 B+ 架構                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  用戶輸入: "系統好像有點問題"                                                   │
│      │                                                                           │
│      ▼                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ InputGateway (NEW)                                                       │    │
│  │   • 來源識別 (系統 vs 用戶)                                             │    │
│  │   • 系統來源 → SourceHandler → 映射表 + Pattern (簡化路徑)              │    │
│  │   • 用戶來源 → 格式標準化 → 完整流程                                    │    │
│  └───────────────────────────────┬─────────────────────────────────────────┘    │
│                                  │                                               │
│                                  ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ BusinessIntentRouter + CompletenessChecker (NEW)                         │    │
│  │                                                                          │    │
│  │   Layer 1: Pattern Matcher (規則匹配)                                    │    │
│  │     ├─ 高置信度 (>0.9) → 直接輸出                                       │    │
│  │     └─ 低置信度 → 繼續 Layer 2                                          │    │
│  │                                                                          │    │
│  │   Layer 2: Semantic Router (Aurelio)                                     │    │
│  │     ├─ 高相似度 (>0.85) → 輸出                                          │    │
│  │     └─ 低相似度 → 繼續 Layer 3                                          │    │
│  │                                                                          │    │
│  │   Layer 3: LLM Classifier (Claude Haiku)                                 │    │
│  │     └─ 同時輸出: 分類 + 完整度 + 缺失欄位                               │    │
│  │                                                                          │    │
│  │   輸出 RoutingDecision:                                                  │    │
│  │   ├─ intent_category: incident                                           │    │
│  │   ├─ sub_intent: general_incident                                        │    │
│  │   ├─ intent_confidence: 0.85                                             │    │
│  │   ├─ completeness: {score: 0.15, threshold: 0.60, is_sufficient: false} │    │
│  │   └─ missing_fields: [affected_system, symptom_type]                    │    │
│  └───────────────────────────────┬─────────────────────────────────────────┘    │
│                                  │                                               │
│              ┌───────────────────┴───────────────────┐                          │
│              │ completeness.is_sufficient?           │                          │
│              └───────────────────┬───────────────────┘                          │
│                      │                       │                                   │
│                     Yes                      No                                  │
│                      │                       │                                   │
│                      ▼                       ▼                                   │
│  ┌────────────────────────────┐  ┌─────────────────────────────────────┐       │
│  │ RiskAssessor (NEW)         │  │ GuidedDialogEngine (NEW)             │       │
│  │   • ITIntent → 風險等級    │  │   • 基於 missing_fields 生成問題    │       │
│  │   • incident/high → HITL   │  │   • 收集用戶回答                    │       │
│  └─────────────┬──────────────┘  │   • 增量更新 (不重新分類)           │       │
│                │                 └───────────────────┬─────────────────┘       │
│                ▼                                     │                          │
│  ┌────────────────────────────┐                      │ 完整度 >= 閾值後        │
│  │ HITLController (NEW)       │                      ▼                          │
│  │   • 審批請求               │◄─────────────────────┘                          │
│  │   • Teams/Slack Webhook    │                                                  │
│  └─────────────┬──────────────┘                                                  │
│                │                                                                 │
│                ▼                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ Existing HybridOrchestratorV2                                            │    │
│  │   ├─ FrameworkSelector (原 IntentRouter) → WORKFLOW/CHAT 模式           │    │
│  │   ├─ ContextBridge → 上下文同步                                         │    │
│  │   └─ UnifiedToolExecutor → Tool 執行                                    │    │
│  │                                                                          │    │
│  │   根據 ITIntent.workflow_type 選擇:                                      │    │
│  │   • sequential → Claude SDK                                              │    │
│  │   • magentic → MAF                                                       │    │
│  │   • group_chat → MAF GroupChat                                           │    │
│  │   • handoff → MAF Handoff                                                │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 核心組件

### 1. BusinessIntentRouter (Sprint 91-93)

```python
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional

class ITIntentCategory(Enum):
    INCIDENT = "incident"      # 事件處理
    REQUEST = "request"        # 服務請求
    CHANGE = "change"          # 變更管理
    QUERY = "query"            # 資訊查詢
    UNKNOWN = "unknown"

@dataclass
class CompletenessInfo:
    """完整度資訊"""
    score: float                  # 0.0-1.0
    threshold: float              # 該意圖類型的閾值
    missing_fields: List[str]     # 缺失欄位
    is_sufficient: bool           # = score >= threshold

@dataclass
class RoutingDecision:
    """統一路由決策 (整合分類 + 完整度)"""
    # 意圖分類
    intent_category: ITIntentCategory
    sub_intent: str               # etl_failure, password_reset, etc.
    intent_confidence: float      # 分類置信度 (0.0-1.0)

    # 完整度 (整合到 Router 輸出)
    completeness: CompletenessInfo

    # 工作流
    workflow_type: str            # sequential, magentic, handoff, group_chat
    risk_level: str               # low, medium, high, critical
    requires_approval: bool

    # 審計
    layer_used: str               # pattern, semantic, llm
    latency_ms: float

class BusinessIntentRouter:
    """
    三層意圖路由器 + 完整度檢查

    路由策略:
    1. Pattern Matcher: 正則規則，高效能
    2. Semantic Router: 向量相似度，語義理解
    3. LLM Classifier: Claude Haiku，複雜場景
    """

    def __init__(
        self,
        pattern_matcher: PatternMatcher,
        semantic_router: SemanticRouter,
        llm_classifier: LLMClassifier,
        completeness_checker: CompletenessChecker,
    ):
        self.pattern_matcher = pattern_matcher
        self.semantic_router = semantic_router
        self.llm_classifier = llm_classifier
        self.completeness_checker = completeness_checker

    async def route(self, user_input: str) -> RoutingDecision:
        """
        三層路由 + 完整度評估

        流程:
        1. Pattern Matcher 嘗試匹配 (< 10ms)
        2. 如果 confidence < 0.9，Semantic Router (< 100ms)
        3. 如果 similarity < 0.85，LLM Classifier (< 2000ms)
        4. 計算完整度
        5. 返回統一 RoutingDecision
        """
        start_time = time.time()

        # Layer 1: Pattern Matcher
        pattern_result = self.pattern_matcher.match(user_input)
        if pattern_result.confidence >= 0.9:
            return self._build_decision(
                pattern_result, user_input, "pattern", start_time
            )

        # Layer 2: Semantic Router
        semantic_result = await self.semantic_router.route(user_input)
        if semantic_result.similarity >= 0.85:
            return self._build_decision(
                semantic_result, user_input, "semantic", start_time
            )

        # Layer 3: LLM Classifier
        llm_result = await self.llm_classifier.classify(user_input)
        return self._build_decision(
            llm_result, user_input, "llm", start_time
        )

    def _build_decision(
        self,
        result: ClassificationResult,
        user_input: str,
        layer_used: str,
        start_time: float,
    ) -> RoutingDecision:
        """構建統一路由決策"""
        # 計算完整度
        completeness = self.completeness_checker.check(
            intent_category=result.intent_category,
            user_input=user_input,
        )

        return RoutingDecision(
            intent_category=result.intent_category,
            sub_intent=result.sub_intent,
            intent_confidence=result.confidence,
            completeness=completeness,
            workflow_type=self._get_workflow_type(result),
            risk_level=self._get_risk_level(result),
            requires_approval=result.risk_level in ["high", "critical"],
            layer_used=layer_used,
            latency_ms=(time.time() - start_time) * 1000,
        )
```

### 2. GuidedDialogEngine + 增量更新 (Sprint 94)

```python
class ConversationContextManager:
    """
    對話上下文管理器

    關鍵改進: 增量更新而非重新分類
    """

    def __init__(self):
        self.routing_decision: Optional[RoutingDecision] = None
        self.collected_info: Dict[str, Any] = {}
        self.dialog_history: List[Dict] = []

    def update_with_user_response(self, user_response: str) -> RoutingDecision:
        """增量更新，不重新分類"""
        # 1. 從用戶回答中提取欄位
        extracted = self._extract_fields(user_response)

        # 2. 更新已收集資訊
        self.collected_info.update(extracted)

        # 3. 嘗試細化 sub_intent (基於規則，不用 LLM)
        if self.routing_decision.intent_category == ITIntentCategory.INCIDENT:
            new_sub_intent = self._refine_sub_intent(extracted)
            if new_sub_intent:
                self.routing_decision.sub_intent = new_sub_intent

        # 4. 重新計算完整度
        self.routing_decision.completeness = self._calculate_completeness()

        return self.routing_decision

    def _refine_sub_intent(self, extracted: Dict) -> Optional[str]:
        """基於規則細化 sub_intent"""
        system = extracted.get("affected_system", "").lower()
        symptom = extracted.get("symptom_type", "").lower()

        if "etl" in system:
            if "報錯" in symptom or "失敗" in symptom:
                return "etl_failure"
            if "慢" in symptom or "延遲" in symptom:
                return "etl_performance"

        return None

class GuidedDialogEngine:
    """
    引導式對話引擎

    功能:
    1. 基於 missing_fields 生成問題
    2. 收集用戶回答
    3. 增量更新上下文
    """

    def __init__(
        self,
        question_generator: QuestionGenerator,
        context_manager: ConversationContextManager,
    ):
        self.question_generator = question_generator
        self.context_manager = context_manager

    async def generate_questions(
        self,
        routing_decision: RoutingDecision,
    ) -> List[Question]:
        """基於缺失欄位生成問題"""
        return await self.question_generator.generate(
            intent_category=routing_decision.intent_category,
            missing_fields=routing_decision.completeness.missing_fields,
        )

    async def process_response(
        self,
        user_response: str,
    ) -> RoutingDecision:
        """處理用戶回答，增量更新"""
        return self.context_manager.update_with_user_response(user_response)
```

### 3. InputGateway + SourceHandlers (Sprint 95)

```python
class InputGateway:
    """
    輸入閘道

    功能:
    1. 來源識別 (系統 vs 用戶)
    2. 系統來源 → 簡化路徑 (映射表 + Pattern)
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

class ServiceNowHandler(BaseSourceHandler):
    """
    ServiceNow 專用處理器

    簡化路徑:
    1. Schema Validator
    2. 映射表 (category → IT Intent)
    3. Pattern Matcher (如果需要)
    4. 跳過 Semantic Router 和 LLM Classifier
    """

    def __init__(
        self,
        schema_validator: SchemaValidator,
        category_mapping: Dict[str, ITIntentCategory],
        pattern_matcher: PatternMatcher,
    ):
        self.schema_validator = schema_validator
        self.category_mapping = category_mapping
        self.pattern_matcher = pattern_matcher

    async def process(self, request: IncomingRequest) -> RoutingDecision:
        """處理 ServiceNow Webhook"""
        # 1. 驗證 Schema
        validated = self.schema_validator.validate(request.data)

        # 2. 映射 category → IT Intent
        snow_category = validated.get("category")
        intent_category = self.category_mapping.get(
            snow_category, ITIntentCategory.UNKNOWN
        )

        # 3. 如果 subcategory 不足，使用 Pattern Matcher
        sub_intent = validated.get("subcategory")
        if not sub_intent:
            pattern_result = self.pattern_matcher.match(
                validated.get("short_description", "")
            )
            sub_intent = pattern_result.sub_intent

        return RoutingDecision(
            intent_category=intent_category,
            sub_intent=sub_intent,
            intent_confidence=1.0,  # 系統來源，置信度高
            completeness=CompletenessInfo(
                score=1.0, threshold=0.6, missing_fields=[], is_sufficient=True
            ),
            workflow_type=self._get_workflow_type(sub_intent),
            risk_level=self._get_risk_level(intent_category),
            requires_approval=False,
            layer_used="servicenow_mapping",
            latency_ms=0,
        )
```

## 與現有系統整合

| 現有組件 | Phase 28 整合方式 |
|----------|-------------------|
| `IntentRouter` | 重命名為 `FrameworkSelector`，保持技術框架選擇功能 |
| `HybridOrchestratorV2` | 在入口處整合 `InputGateway` 和 `BusinessIntentRouter` |
| `RiskAssessmentEngine` | 擴展支援 ITIntent → 風險等級映射 |
| `ApprovalHook` | 整合 `HITLController` 的審批請求 |
| `ContextBridge` | 與 `ConversationContextManager` 協調狀態同步 |

## 新增模組目錄結構

```
backend/src/integrations/orchestration/    # 🆕 新增
├── __init__.py
│
├── intent_router/                         # 三層意圖路由
│   ├── __init__.py
│   ├── router.py                          # BusinessIntentRouter
│   ├── models.py                          # RoutingDecision, ITIntent
│   │
│   ├── pattern_matcher/                   # Layer 1
│   │   ├── __init__.py
│   │   ├── matcher.py
│   │   └── rules.yaml                     # 30+ 規則
│   │
│   ├── semantic_router/                   # Layer 2
│   │   ├── __init__.py
│   │   ├── router.py                      # Aurelio
│   │   └── routes.py                      # 10+ 路由
│   │
│   ├── llm_classifier/                    # Layer 3
│   │   ├── __init__.py
│   │   ├── classifier.py                  # Claude Haiku
│   │   └── prompts.py
│   │
│   └── completeness/                      # 完整度檢查
│       ├── __init__.py
│       ├── checker.py
│       └── rules.py
│
├── guided_dialog/                         # 引導式對話
│   ├── __init__.py
│   ├── engine.py
│   ├── generator.py
│   └── context_manager.py                 # 增量更新
│
├── input_gateway/                         # 輸入閘道
│   ├── __init__.py
│   ├── gateway.py
│   ├── schema_validator.py
│   ├── source_normalizer.py
│   └── source_handlers/
│       ├── __init__.py
│       ├── base_handler.py
│       ├── servicenow_handler.py
│       ├── prometheus_handler.py
│       └── user_input_handler.py
│
├── risk_assessor/                         # 風險評估
│   ├── __init__.py
│   ├── assessor.py
│   └── policies.py
│
├── hitl/                                  # 人機協作
│   ├── __init__.py
│   ├── controller.py
│   └── approval_handler.py
│
└── audit/                                 # 審計日誌
    ├── __init__.py
    └── logger.py
```

## 技術棧

| 技術 | 版本 | 用途 |
|------|------|------|
| Python | 3.11+ | 後端實現 |
| FastAPI | 0.100+ | API 整合 |
| Aurelio | Latest | Semantic Router |
| Claude | Haiku | LLM Classifier |
| Redis | 7.x | 對話上下文快取 |
| PostgreSQL | 16.x | 路由規則持久化 |
| Pydantic | 2.x | 資料模型驗證 |

## 風險與緩解

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| Pattern 規則覆蓋不足 | 分類不準確 | 持續收集實際案例，迭代優化規則 |
| Semantic Router 準確度 | 語義理解偏差 | 調整相似度閾值，增加語義路由 |
| LLM 多任務 Prompt 複雜 | 輸出不穩定 | 分步測試，逐步增加任務 |
| 增量更新邏輯錯誤 | 狀態不一致 | 完整測試案例，邊界條件覆蓋 |
| 系統來源映射不完整 | 分類失敗 | 預留擴展點，支援自定義映射 |

## 成功標準

- [ ] Pattern Matcher 覆蓋率 > 70%
- [ ] 三層路由整體準確率 > 95%
- [ ] 完整度閾值正確執行
- [ ] Guided Dialog 平均輪數 < 3
- [ ] 增量更新正確運作 (不重新分類)
- [ ] 系統來源簡化路徑正確 (< 10ms)
- [ ] HITL 審批流程端到端通過
- [ ] Pattern 層延遲 < 10ms
- [ ] Semantic 層延遲 < 100ms
- [ ] LLM 層延遲 < 2000ms
- [ ] 整體 P95 延遲 < 500ms (無 LLM)

---

**Phase 28 開始時間**: 2026-01-15
**預估完成時間**: 9.5 週 (8.5 週 + 1 週緩衝)
**總 Story Points**: 235 pts
