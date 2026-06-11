# PROMPT-04: DEVELOPMENT EXECUTION
# 開發任務執行

> **用途**: 執行開發任務的完整開發流程
> **變數**: `{TASK_ID}` 或任務描述
> **預估時間**: 15-30 分鐘 (根據任務複雜度)
> **版本**: v3.0.0

---

## 🔤 變數定義

```yaml
{TASK_ID}:
  描述: 任務標識符或任務描述
  格式: 自由格式
  範例:
    - "add-user-profile-api"
    - "fix-login-redirect"
    - "implement-workflow-versioning"
```

---

## 🎯 執行步驟

### Step 1: 確認準備就緒

```yaml
檢查項:
  - [ ] 已執行 PROMPT-02 準備任務
  - [ ] 已理解需求和驗收標準
  - [ ] 本地開發環境正常 (docker-compose up -d)
  - [ ] 後端 API 運行中 (localhost:8000)
  - [ ] 前端開發服務器運行中 (localhost:3000)

如果未準備好:
  → 建議先執行 @PROMPT-02-NEW-SPRINT-PREP.md {TASK_ID}
```

### Step 2: 創建 Feature Branch

```bash
# Branch 命名規範
格式: feature/{task-id}-{description}
範例:
  - feature/add-user-profile-api
  - feature/fix-login-redirect
  - bugfix/fix-workflow-validation

命令:
git checkout -b feature/{task-id}-{description}
```

### Step 3: 實施開發

```yaml
開發流程:
  1. 閱讀相關代碼
  2. 設計實現方案
  3. 編寫代碼
  4. 編寫單元測試
  5. 本地驗證
  6. 代碼自檢

代碼實施建議:
  - 遵循專案代碼規範
  - 編寫清晰的註釋
  - 保持函數簡潔
  - 避免過度設計
  - 考慮錯誤處理
  - 注意安全性

專案代碼規範:
  Python:
    - 格式化: Black (line-length: 100)
    - 導入排序: isort (profile: black)
    - Lint: flake8
    - 類型檢查: mypy

  TypeScript:
    - 格式化: Prettier
    - Lint: ESLint
    - 類型檢查: tsc
```

### Step 4: 編寫測試

```yaml
測試類型:
  1. 單元測試:
     - 覆蓋核心業務邏輯
     - 測試邊界條件
     - 測試錯誤處理

  2. 集成測試:
     - 測試組件間交互
     - 測試 API 接口

  3. E2E 測試 (如需要):
     - 測試完整用戶場景

測試覆蓋率目標: >= 80%

測試命令:
  # Python
  pytest backend/tests/ -v --cov=backend/src

  # TypeScript
  npm test -- --coverage
```

### Step 5: 本地驗證

```yaml
驗證檢查清單:
  - [ ] 代碼可以編譯/運行
  - [ ] 所有測試通過
  - [ ] 功能符合驗收標準
  - [ ] 無明顯 Bug
  - [ ] 代碼質量檢查通過
  - [ ] 文檔已更新 (如需要)
```

### Step 6: 代碼自檢

```yaml
檢查項:
  - [ ] 代碼遵循 SOLID 原則
  - [ ] 無重複代碼 (DRY)
  - [ ] 函數和變數命名清晰
  - [ ] 錯誤處理完善
  - [ ] 無安全漏洞
  - [ ] 性能考慮合理
  - [ ] 日誌記錄適當
```

---

## 📤 輸出格式

```markdown
# 開發任務報告: {TASK_ID}

**生成時間**: {TIMESTAMP}
**生成者**: AI Assistant (PROMPT-04)

---

## 📊 任務信息

| 項目 | 內容 |
|------|------|
| **任務 ID** | {TASK_ID} |
| **任務類型** | {TASK_TYPE} |
| **複雜度** | {COMPLEXITY} |
| **完成狀態** | {STATUS} |

---

## ✅ 完成的功能

### 功能 1: {FEATURE_NAME_1}
**描述**: {FEATURE_DESCRIPTION}
**實現**: {IMPLEMENTATION_DETAILS}
**文件**: `{FILE_PATH}`

### 功能 2: {FEATURE_NAME_2}
...

---

## 💻 實現細節

### 新增文件
```
{NEW_FILE_1}
{NEW_FILE_2}
```

### 修改文件
```
{MODIFIED_FILE_1}
{MODIFIED_FILE_2}
```

### 關鍵代碼片段
```{LANGUAGE}
// {FILE_PATH}:{LINE}
{CODE_SNIPPET}
```

---

## 🧪 測試覆蓋

### 單元測試
- ✅ {TEST_CASE_1}
- ✅ {TEST_CASE_2}
- ✅ {TEST_CASE_3}

### 集成測試
- ✅ {INTEGRATION_TEST_1}
- ✅ {INTEGRATION_TEST_2}

**測試覆蓋率**: {COVERAGE}%

---

## ✅ 驗收標準檢查

- [x] {ACCEPTANCE_CRITERIA_1}
- [x] {ACCEPTANCE_CRITERIA_2}
- [x] {ACCEPTANCE_CRITERIA_3}

**全部通過**: ✅

---

## 🔍 代碼質量檢查

- [x] 代碼規範檢查 (Lint)
- [x] 類型檢查 (TypeScript/MyPy)
- [x] 安全掃描
- [x] 性能檢查
- [x] 單元測試通過
- [x] 集成測試通過

---

## 📝 技術決策記錄

### 決策 1: {DECISION_TITLE}
**背景**: {CONTEXT}
**決策**: {DECISION}
**原因**: {RATIONALE}
**影響**: {CONSEQUENCES}

---

## ⚠️ 已知問題/限制

### 問題 1: {ISSUE_TITLE}
**描述**: {ISSUE_DESCRIPTION}
**影響**: {IMPACT}
**計劃**: {MITIGATION_PLAN}

---

## 🚀 下一步行動

1. ✅ 開發完成
2. ⏭️ 執行 `@PROMPT-05-TESTING-PHASE.md {TASK_ID}` (可選,深度測試)
3. 📋 執行 `@PROMPT-06-PROGRESS-SAVE.md {TASK_ID}` (保存進度)
4. 🔍 (可選) 執行 `@PROMPT-08-CODE-REVIEW.md {FILE_PATH}` (代碼審查)

---

**生成工具**: PROMPT-04
**版本**: v3.0.0
```

---

## 💡 使用範例

```bash
# 開發新功能
用戶: "@PROMPT-04-SPRINT-DEVELOPMENT.md add-user-profile-api"

AI 執行:
1. 確認準備就緒
2. 創建 feature branch
3. 指導實施開發
4. 提醒編寫測試
5. 執行本地驗證
6. 代碼質量檢查
7. 生成開發報告

輸出:
---
✅ 任務開發完成

任務: add-user-profile-api
類型: Feature

功能實現:
- 用戶個人資料 CRUD API
- 頭像上傳支持
- 資料驗證邏輯

測試覆蓋: 85%
質量檢查: ✅ 全部通過

下一步:
1. 可選深度測試: @PROMPT-05
2. 保存進度: @PROMPT-06 add-user-profile-api
---
```

---

## 🔗 相關文檔

- [AI Assistant Instructions](../AI-ASSISTANT-INSTRUCTIONS.md)
- [PROMPT-02: Task Prep](./PROMPT-02-NEW-SPRINT-PREP.md)
- [PROMPT-05: Testing Phase](./PROMPT-05-TESTING-PHASE.md)
- [PROMPT-06: Progress Save](./PROMPT-06-PROGRESS-SAVE.md)

---

**版本**: v3.0.0
**更新日期**: 2025-12-01
