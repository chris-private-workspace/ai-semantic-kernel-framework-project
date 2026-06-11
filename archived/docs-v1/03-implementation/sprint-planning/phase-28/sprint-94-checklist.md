# Sprint 94 Checklist: GuidedDialogEngine + 增量更新

## 開發任務

### Story 94-1: 實現 GuidedDialogEngine 核心
- [ ] 創建 `guided_dialog/` 目錄
- [ ] 創建 `__init__.py`
- [ ] 創建 `engine.py`
- [ ] 實現 `GuidedDialogEngine` 類
- [ ] 實現 `generate_questions()` 方法
- [ ] 實現 `process_response()` 方法
- [ ] 整合 BusinessIntentRouter

### Story 94-2: 實現 ConversationContextManager
- [ ] 創建 `context_manager.py`
- [ ] 實現 `ConversationContextManager` 類
- [ ] 實現 `initialize()` 方法
- [ ] 實現 `update_with_user_response()` 方法
- [ ] 實現對話歷史管理

### Story 94-3: 實現增量更新邏輯
- [ ] 實現 `_extract_fields()` 方法
  - [ ] 系統名稱識別
  - [ ] 症狀識別
  - [ ] 緊急程度識別
- [ ] 實現 `_refine_sub_intent()` 方法
  - [ ] ETL 相關細化規則
  - [ ] 網路相關細化規則
  - [ ] 帳號相關細化規則
- [ ] 實現 `_calculate_completeness()` 方法
- [ ] 確保不調用 LLM 重新分類

### Story 94-4: 實現基礎 QuestionGenerator
- [ ] 創建 `generator.py`
- [ ] 實現 `QuestionGenerator` 類
- [ ] 定義問題模板
  - [ ] affected_system 問題
  - [ ] symptom_type 問題
  - [ ] urgency 問題
  - [ ] requester 問題
- [ ] 實現 `generate()` 方法

### Story 94-5: 對話流程單元測試
- [ ] 創建 `test_guided_dialog.py`
- [ ] 編寫問題生成測試
- [ ] 編寫增量更新測試
  - [ ] sub_intent 細化測試
  - [ ] 完整度重新計算測試
- [ ] 編寫多輪對話測試
- [ ] 編寫邊界條件測試
- [ ] 確認不調用 LLM 重新分類

## 品質檢查

### 代碼品質
- [ ] Black 格式化通過
- [ ] isort 排序通過
- [ ] flake8 檢查通過
- [ ] mypy 類型檢查通過

### 測試
- [ ] 單元測試覆蓋率 > 90%
- [ ] 所有測試通過
- [ ] 增量更新邏輯正確

### 文檔
- [ ] GuidedDialogEngine docstrings 完整
- [ ] ConversationContextManager docstrings 完整
- [ ] 增量更新邏輯註釋完整

## 驗收標準

- [ ] GuidedDialogEngine 正常運作
- [ ] 增量更新正確 (不重新分類)
- [ ] sub_intent 正確細化
- [ ] 完整度正確重新計算
- [ ] 測試覆蓋率 > 90%

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 30
