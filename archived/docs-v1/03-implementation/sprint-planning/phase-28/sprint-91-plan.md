# Sprint 91: Pattern Matcher + 規則定義

## 概述

Sprint 91 專注於建立三層路由的第一層 **Pattern Matcher** 和核心數據模型，這是整個 BusinessIntentRouter 的基礎。

## 目標

1. 定義核心數據模型 (ITIntent, RoutingDecision, CompletenessInfo)
2. 實現 PatternMatcher 核心邏輯
3. 建立 30+ 預定義規則 (涵蓋 incident/request/change/query)
4. 建立基礎審計日誌結構

## Story Points: 25 點

## 前置條件

- ✅ Phase 27 完成
- ✅ 專案結構就緒
- ✅ 開發環境配置完成

## 任務分解

### Story 91-1: 定義核心數據模型 (3h, P0)

**目標**: 建立 ITIntent、RoutingDecision、CompletenessInfo 等核心數據模型

**交付物**:
- `backend/src/integrations/orchestration/intent_router/models.py`

**驗收標準**:
- [ ] ITIntentCategory enum 定義完成 (incident/request/change/query/unknown)
- [ ] CompletenessInfo dataclass 定義完成
- [ ] RoutingDecision dataclass 定義完成
- [ ] 類型註解完整
- [ ] 單元測試通過

### Story 91-2: 實現 PatternMatcher 核心邏輯 (4h, P0)

**目標**: 實現基於正則表達式的模式匹配器

**交付物**:
- `backend/src/integrations/orchestration/intent_router/pattern_matcher/matcher.py`
- `backend/src/integrations/orchestration/intent_router/pattern_matcher/__init__.py`

**驗收標準**:
- [ ] PatternMatcher 類實現完成
- [ ] 支援 YAML 規則載入
- [ ] match() 方法返回 PatternMatchResult
- [ ] 置信度計算邏輯正確
- [ ] 延遲 < 10ms (1000 次調用平均)

### Story 91-3: 建立 30+ 預定義規則 (6h, P0)

**目標**: 定義涵蓋 IT 服務管理場景的匹配規則

**交付物**:
- `backend/src/integrations/orchestration/intent_router/pattern_matcher/rules.yaml`

**規則分類**:

| 類別 | 規則數量 | 範例 |
|------|---------|------|
| Incident | 10+ | ETL失敗, 系統當機, 效能問題 |
| Request | 8+ | 帳號申請, 權限變更, 軟體安裝 |
| Change | 6+ | 系統升級, 配置變更, 部署請求 |
| Query | 6+ | 狀態查詢, 報表查詢, 資訊查詢 |

**驗收標準**:
- [ ] 至少 30 條規則
- [ ] 每個類別至少 6 條規則
- [ ] 規則支援中文和英文
- [ ] 規則有優先級設定
- [ ] 測試覆蓋率 > 90%

### Story 91-4: Pattern Matcher 單元測試 (3h, P0)

**目標**: 為 Pattern Matcher 編寫完整單元測試

**交付物**:
- `backend/tests/unit/orchestration/test_pattern_matcher.py`

**測試案例**:
- [ ] 正常匹配測試 (各類別)
- [ ] 置信度計算測試
- [ ] 無匹配情況測試
- [ ] 多規則衝突測試
- [ ] 效能基準測試

### Story 91-5: 基礎審計日誌結構 (2h, P1)

**目標**: 建立結構化審計日誌基礎

**交付物**:
- `backend/src/integrations/orchestration/audit/__init__.py`
- `backend/src/integrations/orchestration/audit/logger.py`

**驗收標準**:
- [ ] AuditLogger 類實現
- [ ] log_routing_decision() 方法
- [ ] 支援結構化日誌格式
- [ ] 整合現有 logging 框架

## 技術設計

### Pattern Matcher 架構

```python
# rules.yaml 格式
rules:
  - id: incident_etl_failure
    category: incident
    sub_intent: etl_failure
    patterns:
      - "ETL.*失敗"
      - "ETL.*報錯"
      - "ETL.*error"
      - "pipeline.*failure"
    priority: 100
    workflow_type: magentic
    risk_level: high

  - id: incident_system_down
    category: incident
    sub_intent: system_down
    patterns:
      - "系統.*當機"
      - "系統.*掛掉"
      - "service.*down"
      - "system.*unavailable"
    priority: 100
    workflow_type: magentic
    risk_level: critical
```

### PatternMatcher 類設計

```python
@dataclass
class PatternMatchResult:
    matched: bool
    intent_category: Optional[ITIntentCategory]
    sub_intent: Optional[str]
    confidence: float
    rule_id: Optional[str]
    workflow_type: Optional[str]
    risk_level: Optional[str]

class PatternMatcher:
    def __init__(self, rules_path: str):
        self.rules = self._load_rules(rules_path)
        self._compile_patterns()

    def match(self, user_input: str) -> PatternMatchResult:
        """匹配用戶輸入"""
        for rule in sorted(self.rules, key=lambda r: r.priority, reverse=True):
            for pattern in rule.compiled_patterns:
                if pattern.search(user_input):
                    return PatternMatchResult(
                        matched=True,
                        intent_category=rule.category,
                        sub_intent=rule.sub_intent,
                        confidence=0.95,  # Pattern 匹配高置信度
                        rule_id=rule.id,
                        workflow_type=rule.workflow_type,
                        risk_level=rule.risk_level,
                    )

        return PatternMatchResult(matched=False, confidence=0.0)
```

## 依賴

- PyYAML >= 6.0 (規則載入)
- re (正則表達式)

## 風險

| 風險 | 緩解措施 |
|------|---------|
| 規則覆蓋不足 | 持續收集實際案例，迭代優化 |
| 正則效能問題 | 預編譯正則，優化匹配順序 |
| 中文匹配複雜 | 測試各種表達方式 |

## 完成標準

- [ ] 所有 Story 完成
- [ ] 單元測試覆蓋率 > 90%
- [ ] Pattern Matcher 延遲 < 10ms
- [ ] 代碼審查通過
- [ ] 文檔更新

---

**Sprint 開始**: 2026-01-15
**Sprint 結束**: 2026-01-22
**Story Points**: 25
