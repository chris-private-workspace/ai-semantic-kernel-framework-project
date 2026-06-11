# Sprint 30 Checklist: 整合與驗收

**Sprint 目標**: 完整整合測試、文檔更新和最終驗收
**週期**: 2 週
**總點數**: 34 點
**Phase 5 功能**: P5-F5 整合與驗收
**狀態**: 待執行

---

## 快速驗證命令

```bash
# 運行 E2E 測試
cd backend && pytest tests/e2e/ -v --tb=short

# 運行效能測試
cd backend && pytest tests/performance/ -v --benchmark

# 運行完整測試套件
cd backend && pytest --cov=src --cov-report=html

# 驗證腳本
cd backend && python scripts/verify_official_api_usage.py

# 最終審計
cd backend && python scripts/final_audit.py
```

---

## S30-1: E2E 整合測試 (8 點) - 待執行

### 測試場景覆蓋
- [ ] 簡單順序工作流測試
- [ ] 帶人工審批的工作流測試
- [ ] 並行執行工作流測試
- [ ] Agent 交接工作流測試
- [ ] GroupChat 工作流測試
- [ ] 錯誤恢復工作流測試

### 測試檔案創建
- [ ] `tests/e2e/__init__.py`
- [ ] `tests/e2e/test_complete_workflow.py`
- [ ] `tests/e2e/test_approval_workflow.py`
- [ ] `tests/e2e/test_concurrent_workflow.py`
- [ ] `tests/e2e/test_handoff_workflow.py`
- [ ] `tests/e2e/test_groupchat_workflow.py`
- [ ] `tests/e2e/test_error_recovery.py`

### 驗證
- [ ] 所有 E2E 測試通過
- [ ] 無功能回歸
- [ ] 測試可重複執行

---

## S30-2: 效能測試 (8 點) - 待執行

### 效能指標
- [ ] 簡單工作流執行時間 < 500ms
- [ ] 複雜工作流執行時間 < 2000ms
- [ ] GET 端點回應時間 < 100ms
- [ ] POST 端點回應時間 < 500ms
- [ ] 10 並行執行 < 5000ms
- [ ] 50 並行執行 < 15000ms
- [ ] 基準記憶體 < 512MB

### 測試檔案創建
- [ ] `tests/performance/__init__.py`
- [ ] `tests/performance/test_workflow_performance.py`
- [ ] `tests/performance/test_api_performance.py`
- [ ] `tests/performance/test_concurrent_performance.py`
- [ ] `tests/performance/test_memory_usage.py`

### 效能報告
- [ ] 生成效能報告
- [ ] 與遷移前比較
- [ ] 無效能退化確認

---

## S30-3: 文檔更新 (6 點) - 待執行

### API 文檔
- [ ] 更新 OpenAPI/Swagger 描述
- [ ] 更新端點說明
- [ ] 添加新模型文檔
- [ ] 更新請求/回應範例

### 架構文檔
- [ ] 更新 technical-architecture.md
- [ ] 添加 Phase 5 架構變更
- [ ] 更新組件圖
- [ ] 更新數據流圖

### 開發指南
- [ ] 更新 CLAUDE.md
- [ ] 更新適配器使用指南
- [ ] 添加遷移後的最佳實踐
- [ ] 更新貢獻指南

---

## S30-4: 棄用代碼清理 (6 點) - 待執行

### 代碼審查
- [ ] 識別可刪除的代碼
- [ ] 識別需保留的代碼
- [ ] 識別需標記棄用的代碼

### 清理執行
- [ ] 刪除確定不再使用的代碼
- [ ] 添加 `@deprecated` 裝飾器
- [ ] 添加棄用警告
- [ ] 更新 `__init__.py` 導出

### 驗證
- [ ] 無破壞性刪除
- [ ] 所有測試仍通過
- [ ] 無意外依賴

### 記錄
- [ ] 記錄刪除內容
- [ ] 記錄棄用項目
- [ ] 更新遷移指南

---

## S30-5: 最終審計和驗收 (6 點) - 待執行

### 審計項目
- [ ] 官方 API 使用驗證
  - [ ] `verify_official_api_usage.py` 通過
  - [ ] 所有適配器使用官方 API
- [ ] 遺留代碼檢查
  - [ ] 無 SK/AutoGen import
  - [ ] 無直接 domain 使用 (Phase 2-5 功能)
- [ ] 測試覆蓋率
  - [ ] 單元測試 >= 80%
  - [ ] 整合測試 >= 70%
- [ ] 效能基準
  - [ ] 無效能退化
- [ ] 文檔完整性
  - [ ] API 文檔完整
  - [ ] 架構圖更新

### 審計報告
- [ ] 生成 `PHASE5-FINAL-AUDIT-REPORT.md`
- [ ] 符合性評分
- [ ] 問題清單 (如有)
- [ ] 改進建議

### Phase 5 驗收
- [ ] 所有 Sprint 完成確認
- [ ] 總 Story Points 達成
- [ ] 目標達成確認
- [ ] 簽署驗收報告

---

## Sprint 30 完成標準

### 必須完成 (Must Have)
- [ ] E2E 測試全部通過
- [ ] 效能測試全部達標
- [ ] 最終審計符合性 >= 95%
- [ ] 棄用代碼清理完成

### 應該完成 (Should Have)
- [ ] 文檔完整更新
- [ ] 效能報告生成
- [ ] 遷移指南更新

### 可以延後 (Could Have)
- [ ] 進階效能優化
- [ ] 額外測試場景

---

## Phase 5 完成確認

### 總體檢查
- [ ] Sprint 26 完成 (36 點)
- [ ] Sprint 27 完成 (38 點)
- [ ] Sprint 28 完成 (34 點)
- [ ] Sprint 29 完成 (38 點)
- [ ] Sprint 30 完成 (34 點)
- [ ] **總計: 180 點**

### 目標達成
- [ ] 所有 Phase 1 MVP 核心功能使用官方 API
- [ ] 驗證腳本通過率 100%
- [ ] 整體 API 符合性 >= 95%
- [ ] 測試覆蓋率 >= 80%
- [ ] 無效能退化

### 文檔簽署
- [ ] Phase 5 完成報告
- [ ] 驗收確認
- [ ] 後續建議

---

## 依賴確認

### 前置條件
- [ ] Sprint 26-29 全部完成
  - [ ] 所有適配器可用
  - [ ] 所有 API routes 遷移完成
- [ ] 測試環境準備
  - [ ] E2E 測試環境
  - [ ] 效能測試環境

### 外部依賴
- [ ] 測試數據準備
- [ ] 效能基準數據

---

## 相關連結

- [Sprint 30 Plan](./sprint-30-plan.md) - 詳細計劃
- [Phase 5 Overview](./README.md) - Phase 5 概述
- [Phase 5 完整計劃](./PHASE5-MVP-REFACTORING-PLAN.md) - 完整計劃
- [Sprint 25 審計報告](../../sprint-execution/sprint-25/FINAL-COMPREHENSIVE-AUDIT.md) - 初始審計
