# 代碼整合補救計劃

**日期**: 2025-11-29
**狀態**: 🔴 需要立即行動

---

## 📋 問題摘要

### 發現

1. **遺失的代碼存在於 `feature/s1-9-test-framework` 分支**
   - 20 個提交未合併到 main
   - 包含 Sprint 0-1 的完整實現
   - 274 個文件，+34,777 行代碼

2. **直接合併有 11 個衝突文件**
   - 兩個分支已各自發展
   - 需要仔細解決衝突

3. **SCAMPER 文件可從 archive 恢復**
   - 原始內容在 `02-scamper-method-original.md` (2998 行)

---

## 🎯 需要整合的核心代碼

### 優先級 P0 - Agent Service (F1 核心功能)

| 提交 | 內容 | 文件 |
|------|------|------|
| `e1b9874` | S1-6: Agent Framework Integration | 20 個文件 |
| `59812ab` | S1-7: Tool Factory | 新增文件 |

**關鍵文件列表**:
```
backend/src/core/ai/
├── __init__.py
├── agent_framework_service.py          ← Agent Framework 核心
├── plugins/
│   ├── __init__.py
│   ├── base.py                         ← Plugin 基類
│   └── builtin/
│       ├── __init__.py
│       ├── math_plugin.py              ← 數學工具
│       └── time_plugin.py              ← 時間工具

backend/src/domain/agents/
├── prompt_schemas.py                   ← Prompt 模板 schemas

backend/src/infrastructure/database/models/
├── llm_usage_log.py                    ← LLM 使用追蹤
├── prompt_template.py                  ← Prompt 模板

backend/src/infrastructure/database/repositories/
├── llm_usage_repository.py             ← LLM 使用記錄
├── prompt_template_repository.py       ← Prompt 模板 CRUD

backend/migrations/versions/
├── ae6e12213d42_add_llm_usage_logs_table_for_s1_6.py
├── aede787db286_add_prompt_templates_table_for_s1_6.py
```

### 優先級 P1 - Execution Service (執行引擎)

| 提交 | 內容 |
|------|------|
| `c222efe` | S1-3: 狀態機實現 |
| `21a6b01` | S1-4: 步驟編排 |
| `515e779` | S1-5: 錯誤處理 |

---

## 🔧 推薦整合策略

### 策略 A: Cherry-Pick 關鍵提交 (推薦)

```bash
# 1. 創建新的整合分支
git checkout -b feature/integrate-agent-service

# 2. Cherry-pick Agent Service 代碼
git cherry-pick e1b9874  # S1-6: Agent Framework
git cherry-pick 59812ab  # S1-7: Tool Factory

# 3. 解決衝突後測試
pytest backend/tests/

# 4. 合併回主分支
git checkout feature/sprint-3-security
git merge feature/integrate-agent-service
```

**優點**:
- ✅ 只引入需要的代碼
- ✅ 衝突較少
- ✅ 可以逐步驗證

**缺點**:
- ⚠️ 可能遺漏依賴

### 策略 B: 手動複製文件

```bash
# 1. 從 feature 分支提取特定文件
git show feature/s1-9-test-framework:backend/src/core/ai/agent_framework_service.py > backend/src/core/ai/agent_framework_service.py

# 2. 逐一複製所需文件
# 3. 手動調整 imports 和依賴
# 4. 測試
```

**優點**:
- ✅ 完全控制
- ✅ 可以按需調整

**缺點**:
- ⚠️ 工作量大
- ⚠️ 容易遺漏文件

### 策略 C: 重寫 Agent Service (最安全但耗時)

基於 archive 中的原始設計重新實現 Agent Service。

**優點**:
- ✅ 代碼完全符合當前架構
- ✅ 無合併衝突

**缺點**:
- ⚠️ 需要 2-3 週時間
- ⚠️ 重複工作

---

## 📅 執行計劃

### Phase 1: 準備 (Day 1)

1. [ ] 創建整合分支
2. [ ] 確認 feature/s1-9-test-framework 分支完整性
3. [ ] 識別所有需要的文件

### Phase 2: 整合 Agent Service (Day 2-3)

1. [ ] Cherry-pick S1-6 (Agent Framework)
2. [ ] 解決衝突
3. [ ] Cherry-pick S1-7 (Tool Factory)
4. [ ] 解決衝突
5. [ ] 更新 requirements.txt
6. [ ] 驗證 imports

### Phase 3: 整合 Execution Service (Day 4-5)

1. [ ] Cherry-pick S1-3, S1-4, S1-5
2. [ ] 解決衝突
3. [ ] 驗證狀態機功能

### Phase 4: 測試和驗證 (Day 6-7)

1. [ ] 運行所有單元測試
2. [ ] 運行整合測試
3. [ ] 驗證 API 端點
4. [ ] 確認 Agent Framework 連接 Azure OpenAI

### Phase 5: 文檔更新 (Day 8)

1. [ ] 更新 sprint-status.yaml
2. [ ] 更新 gap-analysis-report.md
3. [ ] 創建整合完成報告

---

## ⚠️ 風險評估

| 風險 | 影響 | 機率 | 緩解措施 |
|------|------|------|----------|
| 衝突解決錯誤 | 高 | 中 | 逐步測試，保留備份 |
| 缺少依賴 | 中 | 高 | 完整複製 AI 模組 |
| 測試失敗 | 中 | 中 | 修復後再合併 |
| Azure OpenAI 配置 | 低 | 低 | 確認 .env 配置 |

---

## 📝 SCAMPER 文件恢復

原始 SCAMPER 分析在 archive 中保存完好：

```
來源: docs/00-discovery/brainstorming/archive/02-scamper-method-original.md

內容:
- S - Substitute: 行 89-478 (6 個決策)
- C - Combine: 行 479-1360 (7 個創新點)
- A - Adapt: 行 1361-2912 (17 個借鑒點)
```

**恢復步驟**:
1. 此 archive 文件包含完整原始分析
2. 損壞的分割文件 (A-adapt.md, C-combine.md, S-substitute.md) 可保留，因為 Overview 有決策摘要
3. 如需詳細內容，參考 archive 原始文件

---

## 🎯 建議下一步

1. **立即**: 執行策略 A (Cherry-Pick)，優先整合 S1-6 Agent Framework Service
2. **然後**: 更新 sprint-status.yaml 以反映真實狀態
3. **最後**: 完成 MVP 驗收前的功能補齊

---

*Generated: 2025-11-29*
