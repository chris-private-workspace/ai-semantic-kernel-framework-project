# Sprint 93: BusinessIntentRouter 整合 + 完整度

## 概述

Sprint 93 專注於整合三層路由組件為統一的 **BusinessIntentRouter**，並實現 **CompletenessChecker** 完整度檢查模組。

## 目標

1. 實現 BusinessIntentRouter 協調器
2. 實現 CompletenessChecker (整合版)
3. 定義完整度規則 (按意圖類型)
4. 整合測試 (三層路由 E2E)

## Story Points: 25 點

## 前置條件

- ✅ Sprint 91 完成 (PatternMatcher)
- ✅ Sprint 92 完成 (SemanticRouter, LLMClassifier)

## 任務分解

### Story 93-1: 實現 BusinessIntentRouter 協調器 (4h, P0)

**目標**: 整合三層路由為統一的協調器

**交付物**:
- `backend/src/integrations/orchestration/intent_router/router.py`
- `backend/src/integrations/orchestration/intent_router/__init__.py`

**驗收標準**:
- [ ] BusinessIntentRouter 類實現完成
- [ ] 三層路由邏輯正確 (Pattern → Semantic → LLM)
- [ ] 置信度/相似度閾值可配置
- [ ] route() 方法返回統一 RoutingDecision
- [ ] 延遲追蹤正確

### Story 93-2: 實現 CompletenessChecker (3h, P0)

**目標**: 實現資訊完整度檢查器

**交付物**:
- `backend/src/integrations/orchestration/intent_router/completeness/checker.py`
- `backend/src/integrations/orchestration/intent_router/completeness/__init__.py`

**驗收標準**:
- [ ] CompletenessChecker 類實現完成
- [ ] check() 方法返回 CompletenessInfo
- [ ] 支援不同意圖類型的規則
- [ ] 缺失欄位識別正確

### Story 93-3: 定義完整度規則 (3h, P0)

**目標**: 定義各意圖類型的完整度檢查規則

**交付物**:
- `backend/src/integrations/orchestration/intent_router/completeness/rules.py`

**規則定義**:

| 意圖類型 | 必要欄位 | 閾值 |
|---------|---------|------|
| incident | affected_system, symptom_type, urgency | 60% |
| request | request_type, requester, justification | 60% |
| change | change_type, target_system, schedule | 70% |
| query | query_type | 50% |

**驗收標準**:
- [ ] 各意圖類型規則定義完成
- [ ] 閾值可配置
- [ ] 支援動態規則載入
- [ ] 測試覆蓋率 > 90%

### Story 93-4: 整合測試 (4h, P0)

**目標**: 編寫三層路由 E2E 整合測試

**交付物**:
- `backend/tests/integration/orchestration/test_business_intent_router.py`

**測試案例**:
- [ ] Pattern Matcher 直接匹配 (高置信度)
- [ ] 降級到 Semantic Router
- [ ] 降級到 LLM Classifier
- [ ] 完整度計算正確
- [ ] 缺失欄位識別正確
- [ ] 延遲統計正確

### Story 93-5: 性能基準測試 (2h, P1)

**目標**: 建立性能基準測試

**交付物**:
- `backend/tests/performance/test_router_performance.py`

**測試指標**:
- [ ] Pattern 層 P95 延遲 < 10ms
- [ ] Semantic 層 P95 延遲 < 100ms
- [ ] LLM 層 P95 延遲 < 2000ms
- [ ] 整體 P95 延遲 < 500ms (無 LLM)

## 技術設計

### BusinessIntentRouter 類設計

```python
class BusinessIntentRouter:
    """
    三層意圖路由器 + 完整度檢查

    路由策略:
    1. Pattern Matcher: 正則規則，高效能 (< 10ms)
    2. Semantic Router: 向量相似度 (< 100ms)
    3. LLM Classifier: Claude Haiku (< 2000ms)
    """

    def __init__(
        self,
        pattern_matcher: PatternMatcher,
        semantic_router: SemanticRouter,
        llm_classifier: LLMClassifier,
        completeness_checker: CompletenessChecker,
        pattern_threshold: float = 0.9,
        semantic_threshold: float = 0.85,
    ):
        self.pattern_matcher = pattern_matcher
        self.semantic_router = semantic_router
        self.llm_classifier = llm_classifier
        self.completeness_checker = completeness_checker
        self.pattern_threshold = pattern_threshold
        self.semantic_threshold = semantic_threshold

    async def route(self, user_input: str) -> RoutingDecision:
        """
        三層路由 + 完整度評估
        """
        start_time = time.time()

        # Layer 1: Pattern Matcher
        pattern_result = self.pattern_matcher.match(user_input)
        if pattern_result.matched and pattern_result.confidence >= self.pattern_threshold:
            return self._build_decision(
                pattern_result, user_input, "pattern", start_time
            )

        # Layer 2: Semantic Router
        semantic_result = await self.semantic_router.route(user_input)
        if semantic_result.matched and semantic_result.similarity >= self.semantic_threshold:
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
            collected_info=getattr(result, "extracted_info", {}),
        )

        return RoutingDecision(
            intent_category=result.intent_category,
            sub_intent=result.sub_intent,
            intent_confidence=result.confidence,
            completeness=completeness,
            workflow_type=self._get_workflow_type(result),
            risk_level=self._get_risk_level(result),
            requires_approval=self._requires_approval(result),
            layer_used=layer_used,
            latency_ms=(time.time() - start_time) * 1000,
        )
```

### CompletenessChecker 類設計

```python
class CompletenessChecker:
    """完整度檢查器"""

    def __init__(self, rules: CompletenessRules):
        self.rules = rules

    def check(
        self,
        intent_category: ITIntentCategory,
        user_input: str,
        collected_info: Dict[str, Any] = None,
    ) -> CompletenessInfo:
        """檢查完整度"""
        rule = self.rules.get_rule(intent_category)

        # 合併已收集資訊
        info = collected_info or {}
        extracted = self._extract_from_input(user_input, rule.fields)
        info.update(extracted)

        # 計算完整度
        present_fields = [f for f in rule.required_fields if f in info and info[f]]
        score = len(present_fields) / len(rule.required_fields)

        # 識別缺失欄位
        missing = [f for f in rule.required_fields if f not in info or not info[f]]

        return CompletenessInfo(
            score=score,
            threshold=rule.threshold,
            missing_fields=missing,
            is_sufficient=score >= rule.threshold,
        )
```

## 里程碑

完成 Sprint 93 後：
- ✅ 三層路由核心完成
- ✅ 可獨立運行和測試
- ✅ 為 GuidedDialogEngine 提供基礎

## 完成標準

- [ ] 所有 Story 完成
- [ ] 整合測試通過
- [ ] 性能基準測試通過
- [ ] 測試覆蓋率 > 90%
- [ ] 代碼審查通過

---

**Sprint 開始**: 2026-01-29
**Sprint 結束**: 2026-02-02
**Story Points**: 25
