# Sprint 93 Checklist: BusinessIntentRouter 整合 + 完整度

## 開發任務

### Story 93-1: 實現 BusinessIntentRouter 協調器
- [x] 創建 `router.py`
- [x] 實現 `BusinessIntentRouter` 類
- [x] 整合 PatternMatcher
- [x] 整合 SemanticRouter
- [x] 整合 LLMClassifier
- [x] 實現三層路由邏輯
- [x] 實現置信度/相似度閾值判斷
- [x] 實現 `_build_decision()` 方法
- [x] 實現延遲追蹤

### Story 93-2: 實現 CompletenessChecker
- [x] 創建 `completeness/` 目錄
- [x] 創建 `__init__.py`
- [x] 創建 `checker.py`
- [x] 實現 `CompletenessChecker` 類
- [x] 實現 `check()` 方法
- [x] 實現欄位提取邏輯
- [x] 實現完整度分數計算

### Story 93-3: 定義完整度規則
- [x] 創建 `rules.py`
- [x] 定義 `CompletenessRule` dataclass
- [x] 定義 incident 規則 (閾值 60%)
  - [x] affected_system
  - [x] symptom_type
  - [x] urgency
- [x] 定義 request 規則 (閾值 60%)
  - [x] request_type
  - [x] requester
  - [x] justification
- [x] 定義 change 規則 (閾值 70%)
  - [x] change_type
  - [x] target_system
  - [x] schedule
- [x] 定義 query 規則 (閾值 50%)
  - [x] query_type

### Story 93-4: 整合測試
- [x] 創建 `test_business_intent_router.py`
- [x] 編寫 Pattern 直接匹配測試
- [x] 編寫降級到 Semantic 測試
- [x] 編寫降級到 LLM 測試
- [x] 編寫完整度計算測試
- [x] 編寫缺失欄位識別測試
- [x] 編寫延遲統計測試

### Story 93-5: 性能基準測試
- [x] 創建 `test_router_performance.py`
- [x] 測試 Pattern 層 P95 延遲
- [x] 測試 Semantic 層 P95 延遲
- [x] 測試 LLM 層 P95 延遲
- [x] 測試整體 P95 延遲 (無 LLM)

## 品質檢查

### 代碼品質
- [x] Black 格式化通過
- [x] isort 排序通過
- [x] flake8 檢查通過
- [x] mypy 類型檢查通過

### 測試
- [x] 單元測試覆蓋率 > 90%
- [x] 整合測試通過 (40/40)
- [x] 性能基準測試通過 (11/11)

### 文檔
- [x] BusinessIntentRouter docstrings 完整
- [x] CompletenessChecker docstrings 完整
- [x] 完整度規則註釋完整

## 驗收標準

- [x] 三層路由正確運作
- [x] 完整度檢查正確
- [x] 缺失欄位識別正確
- [x] Pattern 層延遲 < 10ms
- [x] Semantic 層延遲 < 100ms
- [x] LLM 層延遲 < 2000ms
- [x] 整體 P95 延遲 < 500ms (無 LLM)

---

**Sprint 狀態**: ✅ 完成
**Story Points**: 25
**完成日期**: 2026-01-15
