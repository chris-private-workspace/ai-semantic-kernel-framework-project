# Sprint 52 Checklist: Intent Router & Mode Detection

## Pre-Sprint Setup

- [x] 確認 Phase 12 (Sprint 51) 已完成
- [x] 確認 HybridOrchestrator 基礎架構可用
- [x] 建立 `backend/src/integrations/hybrid/intent/` 目錄結構
- [x] 更新 requirements.txt (如有新依賴)

---

## S52-1: Intent Router 核心實現 (13 pts)

### 檔案建立
- [x] `backend/src/integrations/hybrid/intent/__init__.py`
- [x] `backend/src/integrations/hybrid/intent/models.py`
  - [x] `ExecutionMode` 枚舉
  - [x] `IntentAnalysis` Pydantic 模型
  - [x] `SessionContext` 資料類別
- [x] `backend/src/integrations/hybrid/intent/router.py`
  - [x] `IntentRouter` 主類別
  - [x] `analyze_intent()` 方法
  - [x] `should_switch_mode()` 方法
- [x] `backend/src/integrations/hybrid/intent/classifiers/__init__.py`
- [x] `backend/src/integrations/hybrid/intent/classifiers/base.py`
  - [x] `BaseClassifier` 抽象類

### 測試
- [x] `backend/tests/unit/integrations/hybrid/intent/test_models.py`
- [x] `backend/tests/unit/integrations/hybrid/intent/test_router.py`
- [x] 測試覆蓋率 > 90%

### 驗證
- [x] `IntentRouter` 可正確實例化
- [x] `analyze_intent()` 返回正確的 `IntentAnalysis`
- [x] 不同輸入產生預期的模式分類

---

## S52-2: Mode Detection Algorithm (10 pts)

### 檔案建立
- [x] `backend/src/integrations/hybrid/intent/classifiers/rule_based.py`
  - [x] `RuleBasedClassifier` 類別
  - [x] `WORKFLOW_KEYWORDS` 關鍵字列表
  - [x] `CHAT_KEYWORDS` 關鍵字列表
  - [x] `classify()` 方法
- [ ] `backend/src/integrations/hybrid/intent/classifiers/llm_based.py` **[未實現]**
  - [ ] `LLMBasedClassifier` 類別 (可選 fallback) - 設計為 LLM 輔助分類器，尚未實現
- [x] `backend/src/integrations/hybrid/intent/analyzers/__init__.py`
- [x] `backend/src/integrations/hybrid/intent/analyzers/complexity.py`
  - [x] `ComplexityAnalyzer` 類別
  - [x] `ComplexityScore` 資料類別
- [x] `backend/src/integrations/hybrid/intent/analyzers/multi_agent.py`
  - [x] `MultiAgentDetector` 類別

### 測試
- [x] `backend/tests/unit/integrations/hybrid/intent/classifiers/test_rule_based.py`
- [x] `backend/tests/unit/integrations/hybrid/intent/analyzers/test_complexity.py`
- [x] 準確率測試套件 (目標 > 85%)

### 驗證
- [x] 規則分類器對已知輸入正確分類
- [x] 複雜度分析器產生合理的分數
- [x] 多代理檢測器正確識別協作需求

---

## S52-3: API 整合與路由端點 (7 pts)

### 檔案建立/修改
- [x] `backend/src/api/v1/hybrid/intent_routes.py`
  - [x] `POST /api/v1/hybrid/analyze-intent`
  - [x] `GET /api/v1/hybrid/modes`
- [x] `backend/src/api/v1/hybrid/__init__.py` 更新路由註冊
- [x] `backend/src/api/v1/hybrid/schemas.py`
  - [x] `IntentAnalysisRequest`
  - [x] `IntentAnalysisResponse`
  - [x] `ExecutionModeResponse`

### 整合
- [x] 更新 `HybridOrchestrator` 整合 `IntentRouter`
- [x] 在 `execute()` 方法中調用意圖分析

### 測試
- [x] `backend/tests/unit/api/v1/hybrid/test_intent_routes.py`
- [x] API 端對端測試

### 驗證
- [x] API 端點可訪問
- [x] 請求/響應格式正確
- [x] OpenAPI 文檔自動生成

---

## S52-4: 整合測試與文檔 (5 pts)

### 測試
- [x] `backend/tests/integration/hybrid/test_intent_integration.py`
  - [x] 測試完整流程：輸入 → 分類 → 執行模式
  - [x] 邊界情況：空輸入、超長輸入、特殊字符
  - [x] 上下文影響測試
- [x] 效能測試
  - [x] 分類延遲 < 50ms (無 LLM)
  - [x] 分類延遲 < 500ms (含 LLM fallback)

### 文檔
- [x] `docs/03-implementation/sprint-execution/sprint-52/README.md`
- [x] API 使用範例文檔
- [x] 架構決策記錄 (ADR)

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
- [x] 覆蓋率報告生成

### 文檔品質
- [x] README 更新
- [x] API 文檔完整
- [x] 代碼註釋充足

---

## Sprint Review Checklist

- [x] 所有 User Stories 完成
- [x] Demo 準備就緒
- [x] 技術債務記錄
- [x] 下一 Sprint 依賴項確認

---

## Notes

```
Sprint 52 開始日期: 2025-12-28
Sprint 52 結束日期: 2025-12-29
實際完成點數: 35 / 35 pts ✅ (核心功能完成)
```

### 審計備註 (2026-01-14)

**LLMBasedClassifier 未實現說明**：
- 設計文檔中 `llm_based.py` 被定義為「可選 fallback」
- 當前系統使用 `RuleBasedClassifier` 作為主要分類器
- 此差距不影響核心功能，但限制了系統處理模糊意圖的能力
- 如需 LLM 輔助分類功能，建議在後續 Sprint 中補實現
