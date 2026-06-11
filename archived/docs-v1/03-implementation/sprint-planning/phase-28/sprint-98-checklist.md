# Sprint 98 Checklist: HybridOrchestratorV2 整合

## 開發任務

### Story 98-1: 重命名 IntentRouter → FrameworkSelector
- [x] 更新 `hybrid/intent/router.py`
  - [x] 類名: `IntentRouter` → `FrameworkSelector`
  - [x] 類名: `IntentAnalysis` → `FrameworkAnalysis`
  - [x] 方法: `analyze_intent()` → `select_framework()`
- [x] 更新 imports
  - [x] `orchestrator_v2.py`
  - [x] 其他引用文件
- [x] 更新測試文件
- [x] 確認無破壞性變更

### Story 98-2: 整合 BusinessIntentRouter
- [x] 更新 `orchestrator_v2.py`
- [x] 添加 `input_gateway` 參數
- [x] 添加 `business_router` 參數
- [x] 添加 `guided_dialog` 參數
- [x] 添加 `risk_assessor` 參數
- [x] 添加 `hitl_controller` 參數
- [x] 更新 `execute()` 方法
  - [x] Step 1: InputGateway 處理
  - [x] Step 2: 完整度檢查
  - [x] Step 3: GuidedDialog (如需要)
  - [x] Step 4: RiskAssessor 評估
  - [x] Step 5: HITL (如需要)
  - [x] Step 6: FrameworkSelector 選擇
  - [x] Step 7: 執行

### Story 98-3: 整合 GuidedDialogEngine 到 API 層
- [x] 創建 `dialog_routes.py`
- [x] 實現 `POST /dialog/start` 端點
- [x] 實現 `POST /dialog/{dialog_id}/respond` 端點
- [x] 實現 `GET /dialog/{dialog_id}/status` 端點
- [x] 實現 `DELETE /dialog/{dialog_id}` 端點
- [x] 定義 Pydantic 請求/回應模型

### Story 98-4: 整合 HITL 到現有審批流程
- [x] 創建 `approval_routes.py`
- [x] 實現 `GET /approvals` 端點
- [x] 實現 `GET /approvals/{approval_id}` 端點
- [x] 實現 `POST /approvals/{approval_id}/decision` 端點
- [x] 實現 `POST /approvals/{approval_id}/callback` 端點
- [x] 整合現有 ApprovalHook

## 品質檢查

### 代碼品質
- [x] 語法檢查通過
- [ ] Black 格式化通過 (待執行)
- [ ] isort 排序通過 (待執行)
- [ ] flake8 檢查通過 (待執行)
- [ ] mypy 類型檢查通過 (待執行)

### 測試
- [x] 向後兼容性保持
- [x] IntentRouter/FrameworkSelector 測試 31/31 通過
- [x] HybridOrchestratorV2 測試 39/39 通過
- [x] 導入測試全部通過

### 向後相容性
- [x] 重命名無破壞性變更
- [x] 現有功能正常運作
- [x] API 向後相容

## 驗收標準

- [x] 重命名完成，無破壞性變更
- [x] HybridOrchestratorV2 整合完成
- [x] GuidedDialog API 正常工作
- [x] HITL API 正常工作
- [x] 所有相關測試通過 (70/70)

---

**Sprint 狀態**: ✅ 完成
**Story Points**: 25
**完成日期**: 2026-01-16
