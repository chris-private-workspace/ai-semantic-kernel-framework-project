# Sprint 94: GuidedDialogEngine + 增量更新

## 概述

Sprint 94 專注於建立 **GuidedDialogEngine** 引導式對話引擎，核心是實現**增量更新機制**（不重新分類）。

## 目標

1. 實現 GuidedDialogEngine 核心
2. 實現 ConversationContextManager (增量更新)
3. 實現基礎 QuestionGenerator (規則版)
4. 對話流程單元測試

## Story Points: 30 點

## 前置條件

- ✅ Sprint 93 完成 (BusinessIntentRouter)
- ✅ CompletenessChecker 就緒
- ✅ RoutingDecision 模型定義完成

## 任務分解

### Story 94-1: 實現 GuidedDialogEngine 核心 (5h, P0)

**目標**: 建立引導式對話引擎核心

**交付物**:
- `backend/src/integrations/orchestration/guided_dialog/engine.py`
- `backend/src/integrations/orchestration/guided_dialog/__init__.py`

**驗收標準**:
- [ ] GuidedDialogEngine 類實現完成
- [ ] generate_questions() 方法正常運作
- [ ] process_response() 方法正常運作
- [ ] 與 BusinessIntentRouter 整合正確
- [ ] 支援多輪對話

### Story 94-2: 實現 ConversationContextManager (4h, P0)

**目標**: 實現對話上下文管理，支援增量更新

**交付物**:
- `backend/src/integrations/orchestration/guided_dialog/context_manager.py`

**驗收標準**:
- [ ] ConversationContextManager 類實現完成
- [ ] update_with_user_response() 實現增量更新
- [ ] _refine_sub_intent() 基於規則細化
- [ ] _calculate_completeness() 重新計算完整度
- [ ] **不調用 LLM 重新分類**

### Story 94-3: 實現增量更新邏輯 (4h, P0)

**目標**: 實現增量更新核心邏輯

**交付物**:
- 更新 `context_manager.py`

**增量更新規則**:

| 原 sub_intent | 新資訊 | 更新後 sub_intent |
|--------------|--------|------------------|
| general_incident | affected_system=ETL, symptom=報錯 | etl_failure |
| general_incident | affected_system=網路, symptom=斷線 | network_failure |
| general_request | request_type=帳號 | account_request |
| general_request | request_type=權限 | access_request |

**驗收標準**:
- [ ] 增量更新規則定義完成
- [ ] 用戶回答後不重新調用 LLM
- [ ] sub_intent 正確細化
- [ ] 完整度正確重新計算

### Story 94-4: 實現基礎 QuestionGenerator (3h, P0)

**目標**: 實現基於規則的問題生成器

**交付物**:
- `backend/src/integrations/orchestration/guided_dialog/generator.py`

**問題模板**:

| 缺失欄位 | 問題模板 |
|---------|---------|
| affected_system | "請問是哪個系統有問題？" |
| symptom_type | "請描述具體的問題症狀" |
| urgency | "這個問題的緊急程度如何？" |
| requester | "請問申請人是誰？" |

**驗收標準**:
- [ ] QuestionGenerator 類實現完成
- [ ] generate() 方法根據 missing_fields 生成問題
- [ ] 問題模板涵蓋常見欄位
- [ ] 支援中文問題

### Story 94-5: 對話流程單元測試 (4h, P0)

**目標**: 為引導式對話編寫完整測試

**交付物**:
- `backend/tests/unit/orchestration/test_guided_dialog.py`

**測試案例**:
- [ ] 問題生成測試
- [ ] 增量更新測試 (sub_intent 細化)
- [ ] 完整度重新計算測試
- [ ] 多輪對話測試
- [ ] 邊界條件測試

## 技術設計

### ConversationContextManager 類設計

```python
class ConversationContextManager:
    """
    對話上下文管理器

    關鍵改進: 增量更新而非重新分類
    """

    def __init__(self, refinement_rules: RefinementRules):
        self.routing_decision: Optional[RoutingDecision] = None
        self.collected_info: Dict[str, Any] = {}
        self.dialog_history: List[Dict] = []
        self.refinement_rules = refinement_rules

    def initialize(self, routing_decision: RoutingDecision):
        """初始化上下文"""
        self.routing_decision = routing_decision
        self.collected_info = {}
        self.dialog_history = []

    def update_with_user_response(self, user_response: str) -> RoutingDecision:
        """
        增量更新，不重新分類

        步驟:
        1. 從用戶回答中提取欄位
        2. 更新已收集資訊
        3. 嘗試細化 sub_intent (基於規則)
        4. 重新計算完整度
        """
        # 1. 提取欄位
        extracted = self._extract_fields(user_response)

        # 2. 更新資訊
        self.collected_info.update(extracted)
        self.dialog_history.append({
            "role": "user",
            "content": user_response,
            "extracted": extracted,
        })

        # 3. 細化 sub_intent (基於規則，不用 LLM)
        new_sub_intent = self._refine_sub_intent(extracted)
        if new_sub_intent:
            self.routing_decision.sub_intent = new_sub_intent

        # 4. 重新計算完整度
        self.routing_decision.completeness = self._calculate_completeness()

        return self.routing_decision

    def _refine_sub_intent(self, extracted: Dict) -> Optional[str]:
        """基於規則細化 sub_intent"""
        category = self.routing_decision.intent_category
        current_sub = self.routing_decision.sub_intent

        # 查找適用的細化規則
        rule = self.refinement_rules.find_rule(
            category=category,
            current_sub_intent=current_sub,
            extracted_info=extracted,
        )

        return rule.new_sub_intent if rule else None

    def _calculate_completeness(self) -> CompletenessInfo:
        """重新計算完整度"""
        rule = self.completeness_rules.get_rule(
            self.routing_decision.intent_category
        )

        present = [f for f in rule.required_fields if f in self.collected_info]
        missing = [f for f in rule.required_fields if f not in self.collected_info]

        score = len(present) / len(rule.required_fields)

        return CompletenessInfo(
            score=score,
            threshold=rule.threshold,
            missing_fields=missing,
            is_sufficient=score >= rule.threshold,
        )

    def _extract_fields(self, user_response: str) -> Dict[str, Any]:
        """從用戶回答中提取欄位"""
        extracted = {}

        # 系統名稱識別
        system_patterns = [
            (r"ETL|etl|Pipeline|pipeline", "ETL"),
            (r"網路|network|網絡", "網路"),
            (r"ERP|erp", "ERP"),
            (r"郵件|email|mail", "郵件系統"),
        ]
        for pattern, system in system_patterns:
            if re.search(pattern, user_response, re.IGNORECASE):
                extracted["affected_system"] = system
                break

        # 症狀識別
        symptom_patterns = [
            (r"報錯|error|錯誤|失敗|fail", "報錯"),
            (r"慢|slow|延遲|lag", "效能問題"),
            (r"當機|down|掛", "系統當機"),
            (r"斷線|disconnect", "連線問題"),
        ]
        for pattern, symptom in symptom_patterns:
            if re.search(pattern, user_response, re.IGNORECASE):
                extracted["symptom_type"] = symptom
                break

        return extracted
```

### 增量更新流程圖

```
用戶: "ETL 今天報錯了"
         │
         ▼
┌─────────────────────────────────────────────────┐
│ BusinessIntentRouter.route()                     │
│                                                  │
│ 輸出:                                           │
│   intent_category: incident                     │
│   sub_intent: general_incident (資訊不足)       │
│   completeness: 15% (需要更多資訊)             │
│   missing_fields: [affected_system, symptom]   │
└───────────────────────┬─────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│ GuidedDialogEngine.generate_questions()          │
│                                                  │
│ "請問是哪個系統有問題？"                        │
│ "請描述具體的問題症狀"                          │
└───────────────────────┬─────────────────────────┘
                        │
         用戶回答: "是 ETL 系統，跑批次時報錯"
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│ ConversationContextManager.update_with_user_response()
│                                                  │
│ 1. 提取: affected_system=ETL, symptom=報錯      │
│ 2. 細化 sub_intent: general_incident → etl_failure
│ 3. 重新計算完整度: 15% → 70%                    │
│                                                  │
│ ⚠️ 不調用 LLM 重新分類                         │
└───────────────────────┬─────────────────────────┘
                        │
                        ▼
             完整度 >= 60%，繼續核心流程
```

## 完成標準

- [ ] 所有 Story 完成
- [ ] 增量更新邏輯正確
- [ ] 不重新調用 LLM 分類
- [ ] 單元測試覆蓋率 > 90%
- [ ] 代碼審查通過

---

**Sprint 開始**: 2026-02-02
**Sprint 結束**: 2026-02-09
**Story Points**: 30
