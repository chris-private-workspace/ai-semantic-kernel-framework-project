# Sprint 96: RiskAssessor + Policies

## 概述

Sprint 96 專注於建立 **RiskAssessor** 風險評估器和 **Policies** 風險策略，實現 IT 意圖到風險等級的映射。

## 目標

1. 實現 RiskAssessor 核心
2. 定義風險評估策略
3. 整合 ITIntent → 風險等級映射
4. API 路由實現 (intent/classify)

## Story Points: 25 點

## 前置條件

- ✅ Sprint 95 完成 (InputGateway)
- ✅ BusinessIntentRouter 就緒
- ✅ RoutingDecision 模型定義完成

## 任務分解

### Story 96-1: 實現 RiskAssessor 核心 (4h, P0)

**目標**: 建立風險評估器核心邏輯

**交付物**:
- `backend/src/integrations/orchestration/risk_assessor/assessor.py`
- `backend/src/integrations/orchestration/risk_assessor/__init__.py`

**驗收標準**:
- [ ] RiskAssessor 類實現完成
- [ ] assess() 方法返回 RiskAssessment
- [ ] 支援多維度風險評估
- [ ] 風險等級: low/medium/high/critical

### Story 96-2: 定義風險評估策略 (4h, P0)

**目標**: 定義 IT 服務管理場景的風險策略

**交付物**:
- `backend/src/integrations/orchestration/risk_assessor/policies.py`

**風險策略矩陣**:

| Intent Category | Sub Intent | 預設風險等級 | 需要審批 |
|----------------|------------|-------------|---------|
| incident | system_down | critical | ✅ |
| incident | etl_failure | high | ✅ |
| incident | performance_issue | medium | ❌ |
| request | account_request | medium | ❌ |
| request | access_request | high | ✅ |
| change | emergency_change | critical | ✅ |
| change | standard_change | medium | ❌ |
| query | * | low | ❌ |

**驗收標準**:
- [ ] RiskPolicy dataclass 定義完成
- [ ] 策略矩陣定義完成
- [ ] 支援動態策略載入
- [ ] 支援策略覆蓋

### Story 96-3: 整合 ITIntent → 風險等級映射 (3h, P0)

**目標**: 實現 ITIntent 到風險等級的映射邏輯

**交付物**:
- 更新 `assessor.py`

**映射規則**:

```python
def _calculate_risk_level(
    self,
    intent_category: ITIntentCategory,
    sub_intent: str,
    context: Optional[Dict] = None,
) -> RiskLevel:
    """計算風險等級"""
    # 1. 查找策略
    policy = self.policies.get_policy(intent_category, sub_intent)

    # 2. 基礎風險
    base_risk = policy.default_risk_level

    # 3. 上下文調整
    if context:
        if context.get("is_production"):
            base_risk = self._elevate_risk(base_risk)
        if context.get("is_weekend"):
            base_risk = self._elevate_risk(base_risk)

    return base_risk
```

**驗收標準**:
- [ ] 映射邏輯正確
- [ ] 上下文調整正確
- [ ] 支援風險等級提升/降低

### Story 96-4: 風險評估單元測試 (4h, P0)

**目標**: 為風險評估編寫完整測試

**交付物**:
- `backend/tests/unit/orchestration/test_risk_assessor.py`

**測試案例**:
- [ ] 各意圖類型風險評估
- [ ] 上下文調整測試
- [ ] 策略覆蓋測試
- [ ] 邊界條件測試

### Story 96-5: API 路由實現 (3h, P0)

**目標**: 實現 orchestration API 路由

**交付物**:
- `backend/src/api/v1/orchestration/__init__.py`
- `backend/src/api/v1/orchestration/routes.py`
- `backend/src/api/v1/orchestration/intent_routes.py`

**API 端點**:

```
POST /api/v1/orchestration/intent/classify
- 輸入: { "content": "用戶輸入", "source": "user" }
- 輸出: RoutingDecision

POST /api/v1/orchestration/intent/test
- 輸入: { "content": "測試輸入" }
- 輸出: 各層分類結果 (用於調試)
```

**驗收標準**:
- [ ] API 路由實現完成
- [ ] Pydantic 模型定義
- [ ] 錯誤處理完善
- [ ] OpenAPI 文檔生成

## 技術設計

### RiskAssessor 類設計

```python
from enum import Enum
from dataclasses import dataclass

class RiskLevel(Enum):
    LOW = "low"           # 自動執行
    MEDIUM = "medium"     # 記錄審計
    HIGH = "high"         # 需要審批
    CRITICAL = "critical" # 多重審批

@dataclass
class RiskAssessment:
    level: RiskLevel
    score: float              # 0.0 - 1.0
    requires_approval: bool
    approval_type: str        # "single" | "multi" | "none"
    factors: List[RiskFactor]
    reasoning: str

class RiskAssessor:
    """
    風險評估器

    評估維度:
    1. 意圖類別 (incident > change > request > query)
    2. 子意圖 (system_down > etl_failure > general)
    3. 上下文因素 (生產環境, 週末, 緊急)
    """

    def __init__(self, policies: RiskPolicies):
        self.policies = policies

    def assess(
        self,
        routing_decision: RoutingDecision,
        context: Optional[AssessmentContext] = None,
    ) -> RiskAssessment:
        """評估風險"""
        # 1. 獲取基礎風險
        policy = self.policies.get_policy(
            routing_decision.intent_category,
            routing_decision.sub_intent,
        )
        base_level = policy.default_risk_level

        # 2. 計算風險分數
        score = self._calculate_score(routing_decision, context)

        # 3. 上下文調整
        final_level = self._adjust_for_context(base_level, context)

        # 4. 確定審批要求
        requires_approval = final_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        approval_type = self._get_approval_type(final_level)

        return RiskAssessment(
            level=final_level,
            score=score,
            requires_approval=requires_approval,
            approval_type=approval_type,
            factors=self._get_factors(routing_decision, context),
            reasoning=self._generate_reasoning(routing_decision, final_level),
        )
```

### 風險策略定義

```python
@dataclass
class RiskPolicy:
    """風險策略"""
    intent_category: ITIntentCategory
    sub_intent: str
    default_risk_level: RiskLevel
    requires_approval: bool
    approval_type: str
    factors: List[str]

class RiskPolicies:
    """風險策略集合"""

    POLICIES = [
        # Incident 策略
        RiskPolicy(
            intent_category=ITIntentCategory.INCIDENT,
            sub_intent="system_down",
            default_risk_level=RiskLevel.CRITICAL,
            requires_approval=True,
            approval_type="multi",
            factors=["system_criticality", "business_impact"],
        ),
        RiskPolicy(
            intent_category=ITIntentCategory.INCIDENT,
            sub_intent="etl_failure",
            default_risk_level=RiskLevel.HIGH,
            requires_approval=True,
            approval_type="single",
            factors=["data_impact", "downstream_systems"],
        ),
        # ... 更多策略
    ]

    def get_policy(
        self,
        intent_category: ITIntentCategory,
        sub_intent: str,
    ) -> RiskPolicy:
        """獲取策略"""
        # 精確匹配
        for policy in self.POLICIES:
            if (policy.intent_category == intent_category and
                policy.sub_intent == sub_intent):
                return policy

        # 類別默認
        for policy in self.POLICIES:
            if (policy.intent_category == intent_category and
                policy.sub_intent == "*"):
                return policy

        # 全局默認
        return self._get_default_policy()
```

## 完成標準

- [ ] 所有 Story 完成
- [ ] 風險評估邏輯正確
- [ ] API 路由正常工作
- [ ] 單元測試覆蓋率 > 90%
- [ ] 代碼審查通過

---

**Sprint 開始**: 2026-02-13
**Sprint 結束**: 2026-02-20
**Story Points**: 25
