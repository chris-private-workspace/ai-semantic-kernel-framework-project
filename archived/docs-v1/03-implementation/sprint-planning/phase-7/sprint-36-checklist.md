# Sprint 36 Checklist: 驗證與優化

**Sprint 目標**: 完整測試 AI 自主決策能力，優化性能，準備 UAT
**總點數**: 15 Story Points
**狀態**: ⏳ 待開始
**前置條件**: Sprint 34, 35 完成

---

## Story Checklist

### S36-1: 端到端 AI 決策測試 (5 pts)

**狀態**: ⏳ 待開始

#### 準備工作
- [ ] 確認 Azure OpenAI 配置有效
- [ ] 確認 Sprint 34, 35 完成

#### 實現任務
- [ ] 創建測試目錄 `tests/e2e/`
- [ ] 創建 `conftest.py`
  - [ ] 添加 e2e marker
  - [ ] 添加 real_llm_service fixture
- [ ] 創建 `test_ai_autonomous_decision.py`
  - [ ] test_intelligent_task_decomposition
  - [ ] test_intelligent_decision_making
  - [ ] test_intelligent_error_learning
  - [ ] test_full_planning_workflow
- [ ] 創建 `test_llm_integration.py`
  - [ ] test_llm_generate
  - [ ] test_llm_generate_structured

#### 驗證
- [ ] 所有 E2E 測試通過
- [ ] 測試使用真實 LLM（非 Mock）
- [ ] 測試結果符合預期

---

### S36-2: 性能基準測試與優化 (5 pts)

**狀態**: ⏳ 待開始

#### 準備工作
- [ ] 確認性能測試環境

#### 實現任務
- [ ] 創建 `tests/performance/`
- [ ] 創建 `test_llm_performance.py`
  - [ ] test_single_request_latency
  - [ ] test_concurrent_requests
  - [ ] test_cache_effectiveness
  - [ ] test_timeout_handling
- [ ] 建立性能基準表
- [ ] 識別優化點
- [ ] 實施優化措施
  - [ ] 緩存預熱（如需要）
  - [ ] 連接池優化（如需要）
  - [ ] 超時配置調整（如需要）

#### 驗證
- [ ] P95 延遲 < 5 秒
- [ ] 並發成功率 > 80%
- [ ] 緩存延遲 < 100ms
- [ ] 性能報告生成

---

### S36-3: 文檔更新和 UAT 準備 (3 pts)

**狀態**: ⏳ 待開始

#### 實現任務
- [ ] 更新技術架構文檔
  - [ ] `docs/02-architecture/technical-architecture.md`
  - [ ] 添加 LLM 服務層說明
  - [ ] 更新架構圖
- [ ] 創建 LLM 服務 README
  - [ ] `backend/src/integrations/llm/README.md`
  - [ ] 使用指南
  - [ ] 配置說明
- [ ] 更新 UAT 測試計劃
  - [ ] 添加 AI 自主決策場景
  - [ ] 更新 FEATURE-INDEX.md
- [ ] 更新主 CLAUDE.md
  - [ ] 添加 LLM 配置
  - [ ] 更新開發命令
- [ ] 創建 Phase 7 完成報告
  - [ ] `docs/03-implementation/sprint-execution/phase-7-summary.md`

#### 驗證
- [ ] 所有文檔更新完成
- [ ] 文檔內容準確
- [ ] UAT 計劃可執行

---

### S36-4: LLM 回退策略驗證 (2 pts)

**狀態**: ⏳ 待開始

#### 實現任務
- [ ] 創建 `tests/unit/test_llm_fallback.py`
  - [ ] test_decomposer_fallback_on_llm_error
  - [ ] test_decomposer_fallback_on_timeout
  - [ ] test_decision_engine_fallback
  - [ ] test_trial_error_fallback
  - [ ] test_no_llm_uses_rule_based

#### 驗證
- [ ] 所有回退測試通過
- [ ] 降級邏輯正確
- [ ] 功能完整性不受影響

---

## 驗證命令

```bash
# 1. E2E 測試 (需要真實 API)
cd backend
pytest tests/e2e/ -v -m e2e --tb=short
# 預期: 全部通過

# 2. 性能測試
pytest tests/performance/ -v -m performance
# 預期: 全部通過，P95 < 5s

# 3. 回退策略測試
pytest tests/unit/test_llm_fallback.py -v
# 預期: 全部通過

# 4. 完整測試（排除 E2E）
pytest tests/ -v --ignore=tests/e2e --cov=src
# 預期: 全部通過，覆蓋率 > 85%

# 5. 文檔檢查
ls docs/03-implementation/sprint-execution/phase-7-summary.md
ls backend/src/integrations/llm/README.md
# 預期: 文件存在
```

---

## 完成定義

- [ ] 所有 S36 Story 完成
- [ ] E2E 測試套件創建並通過
- [ ] 性能基準測試通過
  - [ ] P95 延遲 < 5 秒
  - [ ] 並發成功率 > 80%
  - [ ] 緩存有效工作
- [ ] 文檔更新完成
  - [ ] 技術架構文檔
  - [ ] LLM 服務 README
  - [ ] UAT 測試計劃
  - [ ] Phase 7 完成報告
- [ ] 回退策略驗證通過
- [ ] 代碼審查完成
- [ ] Phase 7 正式結束

---

## 輸出產物

| 文件 | 類型 | 說明 |
|------|------|------|
| `tests/e2e/test_ai_autonomous_decision.py` | 新增 | E2E 測試 |
| `tests/e2e/test_llm_integration.py` | 新增 | LLM 整合測試 |
| `tests/performance/test_llm_performance.py` | 新增 | 性能測試 |
| `tests/unit/test_llm_fallback.py` | 新增 | 回退策略測試 |
| `docs/02-architecture/technical-architecture.md` | 修改 | 添加 LLM 層 |
| `backend/src/integrations/llm/README.md` | 新增 | LLM 服務文檔 |
| `docs/03-implementation/sprint-execution/phase-7-summary.md` | 新增 | Phase 7 報告 |
| `claudedocs/uat/FEATURE-INDEX.md` | 修改 | 更新功能狀態 |

---

## Phase 7 最終驗收

| 驗收項目 | 標準 | 狀態 |
|----------|------|------|
| LLM 服務基礎設施 | AzureOpenAILLMService 可用 | ⏳ |
| Phase 2 擴展 LLM 整合 | 100% 組件注入 LLM | ⏳ |
| AI 自主決策功能 | E2E 測試通過 | ⏳ |
| 性能達標 | P95 < 5s | ⏳ |
| 降級策略 | 回退測試通過 | ⏳ |
| 文檔完整 | 所有文檔更新 | ⏳ |
| 測試覆蓋 | > 85% | ⏳ |

---

## 風險緩解檢查

- [ ] Azure OpenAI 配額充足
- [ ] 緩存策略正確配置
- [ ] 超時設置合理
- [ ] 降級策略可靠
- [ ] 監控和日誌完善

---

**創建日期**: 2025-12-21
