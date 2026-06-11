# PROMPT-08: CODE REVIEW
# 代碼質量審查

> **用途**: 審查代碼質量、最佳實踐和潛在問題
> **變數**: `{FILE_PATH}`
> **預估時間**: 5-10 分鐘
> **版本**: v3.0.0

---

## 🔤 變數定義

```yaml
{FILE_PATH}:
  描述: 要審查的文件或目錄路徑
  格式: 相對路徑或絕對路徑
  範例: "backend/src/agent/", "frontend/src/components/AgentList.tsx"
```

---

## 🎯 執行步驟

### Step 1: 讀取代碼文件

```yaml
讀取策略:
  - 如果是文件: 讀取該文件
  - 如果是目錄: 讀取目錄下所有代碼文件

支持的文件類型:
  - Python: *.py
  - TypeScript/JavaScript: *.ts, *.tsx, *.js, *.jsx
  - 配置文件: *.json, *.yaml, *.yml
```

### Step 2: 代碼質量審查

```yaml
審查維度:
  1. 代碼風格 (Code Style):
     - 命名規範
     - 縮進和格式
     - 註釋質量
     - 代碼組織

  2. 設計原則 (Design):
     - SOLID 原則
     - DRY (Don't Repeat Yourself)
     - KISS (Keep It Simple, Stupid)
     - YAGNI (You Aren't Gonna Need It)

  3. 錯誤處理 (Error Handling):
     - 異常捕獲
     - 錯誤消息
     - 錯誤恢復
     - 日誌記錄

  4. 安全性 (Security):
     - 輸入驗證
     - SQL 注入防護
     - XSS 防護
     - 敏感數據處理

  5. 性能 (Performance):
     - 算法效率
     - 資源管理
     - 緩存使用
     - 數據庫查詢優化

  6. 測試性 (Testability):
     - 依賴注入
     - 模塊化設計
     - 測試覆蓋
     - Mock 友好性
```

### Step 3: 識別問題

```yaml
問題分類:
  - Critical (嚴重): 安全漏洞、數據丟失風險
  - High (高): 性能問題、邏輯錯誤
  - Medium (中): 代碼異味、設計問題
  - Low (低): 風格問題、建議改進
```

### Step 4: 提供改進建議

```yaml
建議類型:
  - 必須修復 (MUST): Critical/High 問題
  - 應該修復 (SHOULD): Medium 問題
  - 可以考慮 (COULD): Low 問題、優化建議
```

---

## 📤 輸出格式

```markdown
# 代碼審查報告: {FILE_PATH}

**審查日期**: {REVIEW_DATE}
**審查者**: AI Assistant (PROMPT-08)

---

## 📊 審查摘要

| 項目 | 數量 | 狀態 |
|------|------|------|
| **審查文件數** | {FILE_COUNT} | - |
| **Critical 問題** | {CRITICAL_COUNT} | ❌ |
| **High 問題** | {HIGH_COUNT} | ⚠️ |
| **Medium 問題** | {MEDIUM_COUNT} | ⚠️ |
| **Low 問題** | {LOW_COUNT} | 💡 |
| **總體評分** | {SCORE}/10 | {STATUS} |

---

## ❌ Critical 問題 (必須修復)

### 問題 1: {ISSUE_TITLE}
**文件**: `{FILE_PATH}:{LINE_NUMBER}`
**分類**: {CATEGORY} (Security/Performance/Logic)
**描述**: {DESCRIPTION}

**問題代碼**:
```{LANGUAGE}
{PROBLEMATIC_CODE}
```

**建議修復**:
```{LANGUAGE}
{SUGGESTED_FIX}
```

**原因**: {RATIONALE}
**影響**: {IMPACT}

---

## ⚠️ High 問題 (應該修復)

### 問題 1: {ISSUE_TITLE}
...

---

## ⚠️ Medium 問題 (建議修復)

### 問題 1: {ISSUE_TITLE}
...

---

## 💡 Low 問題 (可以考慮)

### 問題 1: {ISSUE_TITLE}
...

---

## 🔍 詳細審查

### 1. 代碼風格審查

**評分**: {SCORE}/10

**優點**:
- ✅ {STRENGTH_1}
- ✅ {STRENGTH_2}

**問題**:
- ⚠️ {ISSUE_1}
- 💡 {SUGGESTION_1}

---

### 2. 設計原則審查

**評分**: {SCORE}/10

**SOLID 原則**:
- Single Responsibility: {ASSESSMENT}
- Open/Closed: {ASSESSMENT}
- Liskov Substitution: {ASSESSMENT}
- Interface Segregation: {ASSESSMENT}
- Dependency Inversion: {ASSESSMENT}

**問題**:
- {DESIGN_ISSUE_1}

---

### 3. 錯誤處理審查

**評分**: {SCORE}/10

**異常處理**:
- 覆蓋度: {COVERAGE}
- 質量: {QUALITY}

**問題**:
- {ERROR_HANDLING_ISSUE}

---

### 4. 安全性審查

**評分**: {SCORE}/10

**安全檢查**:
- ✅ 輸入驗證
- ❌ SQL 注入防護不足
- ✅ XSS 防護
- ⚠️ 敏感數據未加密

**問題**:
- {SECURITY_ISSUE_1}

---

### 5. 性能審查

**評分**: {SCORE}/10

**性能問題**:
- {PERFORMANCE_ISSUE_1}
- {PERFORMANCE_ISSUE_2}

**優化建議**:
- {OPTIMIZATION_1}

---

### 6. 測試性審查

**評分**: {SCORE}/10

**可測試性**:
- 依賴注入: {ASSESSMENT}
- 模塊化: {ASSESSMENT}

**改進建議**:
- {TESTABILITY_IMPROVEMENT}

---

## ✅ 代碼優點

### 優點 1: {STRENGTH_TITLE}
**描述**: {DESCRIPTION}
**位置**: `{FILE}:{LINE}`

---

## 📋 改進優先級

### 必須修復 (本 Sprint)
1. [ ] {CRITICAL_ISSUE_1}
2. [ ] {CRITICAL_ISSUE_2}
3. [ ] {HIGH_ISSUE_1}

### 應該修復 (下個 Sprint)
1. [ ] {MEDIUM_ISSUE_1}
2. [ ] {MEDIUM_ISSUE_2}

### 可以考慮 (技術債務)
1. [ ] {LOW_ISSUE_1}
2. [ ] {LOW_ISSUE_2}

---

## 💡 最佳實踐建議

### Python 最佳實踐
- {PYTHON_BEST_PRACTICE_1}
- {PYTHON_BEST_PRACTICE_2}

### TypeScript 最佳實踐
- {TS_BEST_PRACTICE_1}
- {TS_BEST_PRACTICE_2}

### 通用最佳實踐
- {GENERAL_BEST_PRACTICE_1}
- {GENERAL_BEST_PRACTICE_2}

---

## 🔧 自動化工具建議

建議使用以下工具提升代碼質量:

**Python**:
- Linter: `pylint`, `flake8`
- Formatter: `black`
- Type Checker: `mypy`
- Security: `bandit`

**TypeScript/JavaScript**:
- Linter: `eslint`
- Formatter: `prettier`
- Type Checker: `tsc`
- Security: `npm audit`

---

## 📚 參考資源

- [Python Style Guide (PEP 8)](https://pep8.org/)
- [TypeScript Best Practices](https://typescript-eslint.io/)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [Clean Code](https://github.com/ryanmcdermott/clean-code-javascript)

---

**生成工具**: PROMPT-08
**版本**: v2.0.0
```

---

## 💡 使用範例

```bash
# 審查單個文件
用戶: "@PROMPT-08-CODE-REVIEW.md backend/src/agent/service.py"

# 審查整個目錄
用戶: "@PROMPT-08-CODE-REVIEW.md backend/src/agent/"

AI 執行:
1. 讀取代碼文件
2. 對 6 個維度進行審查
3. 識別問題並分類
4. 提供改進建議
5. 生成審查報告

輸出:
---
🔍 代碼審查完成

審查文件: backend/src/agent/service.py
總體評分: 7.5/10

Critical 問題: 1
- SQL 注入風險 (Line 45)

High 問題: 2
- 缺少錯誤處理 (Line 67)
- 性能問題: N+1 查詢 (Line 89)

建議:
1. 立即修復 SQL 注入問題
2. 添加異常處理
3. 優化數據庫查詢

報告已生成
---
```

---

## 🔗 相關文檔

- [AI Assistant Instructions](../AI-ASSISTANT-INSTRUCTIONS.md)
- [PROMPT-04: Sprint Development](./PROMPT-04-SPRINT-DEVELOPMENT.md)
- [PROMPT-06: Progress Save](./PROMPT-06-PROGRESS-SAVE.md)

---

**版本**: v3.0.0
**更新日期**: 2025-12-01
