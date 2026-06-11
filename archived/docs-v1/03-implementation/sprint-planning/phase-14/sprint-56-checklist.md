# Sprint 56 Checklist: Mode Switcher & HITL

## Pre-Sprint Setup

- [x] 確認 Sprint 55 (Risk Assessment) 已完成
- [x] 確認 Context Bridge 可用
- [x] 建立 `backend/src/integrations/hybrid/switching/` 目錄結構

---

## S56-1: Mode Switcher 核心實現 (13 pts)

### 檔案建立
- [x] `backend/src/integrations/hybrid/switching/__init__.py`
- [x] `backend/src/integrations/hybrid/switching/models.py`
  - [x] `SwitchTrigger` 資料類別
  - [x] `SwitchResult` 資料類別
  - [x] `ModeTransition` 資料類別
  - [x] `MigratedState` 資料類別
- [x] `backend/src/integrations/hybrid/switching/switcher.py`
  - [x] `ModeSwitcher` 主類別
  - [x] `should_switch()` 方法
  - [x] `execute_switch()` 方法
  - [x] `rollback_switch()` 方法
  - [x] `_create_switch_checkpoint()` 方法
  - [x] `_initialize_target_mode()` 方法
  - [x] `_validate_switch()` 方法

### 測試
- [x] `backend/tests/unit/integrations/hybrid/switching/test_models.py`
- [x] `backend/tests/unit/integrations/hybrid/switching/test_switcher.py`
- [x] 測試覆蓋率 > 90%

### 驗證
- [x] 模式切換成功執行
- [x] 回滾機制正常運作
- [x] 狀態正確保存和遷移

---

## S56-2: Trigger Detectors (8 pts)

### 檔案建立
- [x] `backend/src/integrations/hybrid/switching/triggers/__init__.py`
- [x] `backend/src/integrations/hybrid/switching/triggers/base.py`
  - [x] `TriggerDetector` 抽象類
- [x] `backend/src/integrations/hybrid/switching/triggers/complexity.py`
  - [x] `ComplexityTriggerDetector` 類別
- [x] `backend/src/integrations/hybrid/switching/triggers/user.py`
  - [x] `UserRequestTriggerDetector` 類別
- [x] `backend/src/integrations/hybrid/switching/triggers/failure.py`
  - [x] `FailureTriggerDetector` 類別
- [x] `backend/src/integrations/hybrid/switching/triggers/resource.py`
  - [x] `ResourceTriggerDetector` 類別

### 測試
- [x] `backend/tests/unit/integrations/hybrid/switching/triggers/test_complexity.py`
- [x] `backend/tests/unit/integrations/hybrid/switching/triggers/test_failure.py`
- [x] 各種觸發場景測試

### 驗證
- [x] 複雜度變化正確觸發切換
- [x] 失敗後正確觸發診斷模式
- [x] 用戶請求正確識別

---

## S56-3: State Migration (7 pts)

### 檔案建立
- [x] `backend/src/integrations/hybrid/switching/migration/__init__.py`
- [x] `backend/src/integrations/hybrid/switching/migration/state_migrator.py`
  - [x] `StateMigrator` 類別
  - [x] `migrate()` 方法
  - [x] `_workflow_to_chat()` 方法
  - [x] `_chat_to_workflow()` 方法
  - [x] `_hybrid_migration()` 方法

### 測試
- [x] `backend/tests/unit/integrations/hybrid/switching/migration/test_state_migrator.py`
- [x] Workflow → Chat 遷移測試
- [x] Chat → Workflow 遷移測試
- [x] 資料完整性測試

### 驗證
- [x] 遷移後狀態完整
- [x] 對話歷史正確轉換
- [x] Tool 調用記錄保留

---

## S56-4: Enhanced HITL & API (7 pts)

### 檔案建立/修改
- [x] `backend/src/api/v1/hybrid/switch_routes.py`
  - [x] `POST /api/v1/hybrid/switch`
  - [x] `GET /api/v1/hybrid/switch/status/{switch_id}`
  - [x] `POST /api/v1/hybrid/switch/rollback`
- [x] `backend/src/api/v1/hybrid/schemas.py` 更新
  - [x] `SwitchRequest`
  - [x] `SwitchResponse`
  - [x] `SwitchStatusResponse`
  - [x] `RollbackRequest`

### 整合
- [x] 風險型審批流程整合
- [x] WebSocket 切換事件通知 (可選)

### 測試
- [x] `backend/tests/unit/api/v1/hybrid/test_switch_routes.py`
- [x] API 端對端測試

### 驗證
- [x] API 端點可訪問
- [x] 手動切換成功
- [x] 回滾 API 正常運作

---

## Quality Gates

### 代碼品質
- [x] `black .` 格式化通過
- [x] `isort .` 導入排序通過
- [x] `flake8 .` 無錯誤
- [x] `mypy .` 類型檢查通過

### 測試品質
- [x] 單元測試全部通過
- [x] 整合測試全部通過
- [x] 模式切換成功率 > 99%

---

## Notes

```
Sprint 56 開始日期: 2026-01-02
Sprint 56 結束日期: 2026-01-03
實際完成點數: 35 / 35 pts ✅
```
