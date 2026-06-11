# PROMPT-05: TESTING PHASE
# 測試階段執行

> **用途**: 執行完整的測試流程,確保質量
> **變數**: `{STORY_ID}`
> **預估時間**: 10-20 分鐘
> **版本**: v3.0.0

---

## 🔤 變數定義

```yaml
{STORY_ID}:
  描述: Story 標識符
  範例: "S0-1", "S0-2", "S1-3"
```

---

## 🎯 執行步驟

### Step 1: 測試環境準備

```yaml
檢查項:
  - [ ] 本地開發環境運行正常
  - [ ] 測試數據已準備
  - [ ] 測試工具已配置
  - [ ] 依賴服務已啟動
```

### Step 2: 單元測試

```yaml
執行命令:
  # Python
  pytest backend/tests/ -v --cov=backend/src

  # JavaScript/TypeScript
  npm test -- --coverage

檢查項:
  - 所有測試通過
  - 覆蓋率 >= 80%
  - 無警告或錯誤
```

### Step 3: 集成測試

```yaml
測試內容:
  - API 端點測試
  - 數據庫交互測試
  - 服務間通信測試
  - 錯誤處理測試

執行:
  pytest backend/tests/integration/ -v
```

### Step 4: E2E 測試 (如適用)

```yaml
測試工具:
  - Playwright (前端)
  - Postman/Newman (API)

測試場景:
  - 完整用戶流程
  - 關鍵業務場景
  - 錯誤場景處理
```

### Step 5: 性能測試 (可選)

```yaml
檢查項:
  - 響應時間
  - 資源使用
  - 並發處理
  - 內存洩漏
```

### Step 6: 安全測試

```yaml
檢查項:
  - SQL 注入防護
  - XSS 防護
  - CSRF 防護
  - 認證授權
  - 敏感數據處理
```

### Step 7: 生成測試報告

```yaml
報告內容:
  - 測試摘要
  - 測試覆蓋率
  - 失敗用例分析
  - 性能指標
  - 安全檢查結果
```

---

## 📤 輸出格式

```markdown
# 測試報告: {STORY_ID}

**生成時間**: {TIMESTAMP}
**生成者**: AI Assistant (PROMPT-05)

---

## 📊 測試摘要

| 項目 | 結果 |
|------|------|
| **Story ID** | {STORY_ID} |
| **測試日期** | {TEST_DATE} |
| **測試環境** | {ENVIRONMENT} |
| **總測試數** | {TOTAL_TESTS} |
| **通過數** | {PASSED_TESTS} |
| **失敗數** | {FAILED_TESTS} |
| **跳過數** | {SKIPPED_TESTS} |
| **覆蓋率** | {COVERAGE}% |
| **總體結果** | {OVERALL_RESULT} ✅/❌ |

---

## 🧪 單元測試結果

### 測試統計
- 總測試: {UNIT_TOTAL}
- 通過: {UNIT_PASSED} ✅
- 失敗: {UNIT_FAILED} ❌
- 跳過: {UNIT_SKIPPED} ⏭️

### 覆蓋率詳情
```
Module                    Coverage
------------------------  --------
{MODULE_1}                {COV_1}%
{MODULE_2}                {COV_2}%
------------------------  --------
Total                     {TOTAL_COV}%
```

### 失敗用例 (如有)
```
{FAILED_TEST_1}:
  錯誤: {ERROR_MESSAGE}
  位置: {FILE}:{LINE}
```

---

## 🔗 集成測試結果

### API 測試
- ✅ {API_TEST_1}
- ✅ {API_TEST_2}
- ❌ {API_TEST_3_FAILED}

### 數據庫測試
- ✅ {DB_TEST_1}
- ✅ {DB_TEST_2}

### 服務間通信
- ✅ {SERVICE_TEST_1}

---

## 🌐 E2E 測試結果

### 用戶場景測試
- ✅ {E2E_SCENARIO_1}
- ✅ {E2E_SCENARIO_2}

### 瀏覽器兼容性
- Chrome: ✅
- Firefox: ✅
- Safari: ✅

---

## ⚡ 性能測試結果

### 響應時間
- API 平均響應: {AVG_RESPONSE_TIME}ms
- P95 響應時間: {P95_RESPONSE_TIME}ms
- P99 響應時間: {P99_RESPONSE_TIME}ms

### 資源使用
- 內存使用: {MEMORY_USAGE}MB
- CPU 使用: {CPU_USAGE}%

---

## 🔒 安全測試結果

### 安全檢查
- ✅ SQL 注入防護
- ✅ XSS 防護
- ✅ CSRF 防護
- ✅ 認證授權檢查
- ✅ 敏感數據加密

### 漏洞掃描
{VULNERABILITY_SCAN_RESULTS}

---

## ⚠️ 發現的問題

### 問題 1: {ISSUE_TITLE}
**嚴重程度**: {SEVERITY}
**描述**: {DESCRIPTION}
**建議**: {RECOMMENDATION}

---

## ✅ 驗收標準檢查

基於 Story 驗收標準的測試結果:

- [x] {ACCEPTANCE_CRITERIA_1}
  - 測試: {TEST_NAME_1} ✅

- [x] {ACCEPTANCE_CRITERIA_2}
  - 測試: {TEST_NAME_2} ✅

- [ ] {ACCEPTANCE_CRITERIA_3}
  - 測試: {TEST_NAME_3} ❌
  - 問題: {ISSUE}

---

## 📋 測試覆蓋報告

### 已測試的功能
- ✅ {TESTED_FEATURE_1}
- ✅ {TESTED_FEATURE_2}
- ✅ {TESTED_FEATURE_3}

### 未測試的邊界情況
- ⚠️ {UNTESTED_CASE_1}
- ⚠️ {UNTESTED_CASE_2}

---

## 🚀 下一步行動

### 如果所有測試通過:
1. ✅ 測試階段完成
2. ⏭️ 執行 `@PROMPT-06-PROGRESS-SAVE.md {SPRINT_ID} {STORY_ID}`
3. 📋 準備 Code Review

### 如果有測試失敗:
1. ❌ 修復失敗的測試
2. 🔄 重新運行測試
3. ✅ 確保所有測試通過後再提交

---

## 📊 測試日誌

```
{TEST_EXECUTION_LOG}
```

---

**生成工具**: PROMPT-05
**版本**: v2.0.0
```

---

## 💡 使用範例

```bash
# 執行 Story S0-1 的完整測試
用戶: "@PROMPT-05-TESTING-PHASE.md S0-1"

AI 執行:
1. 準備測試環境
2. 運行單元測試
3. 運行集成測試
4. (可選) 運行 E2E 測試
5. 執行安全檢查
6. 生成測試報告

輸出:
---
🧪 測試完成報告

Story: S0-1
總測試: 45
通過: 44 ✅
失敗: 1 ❌
覆蓋率: 87%

問題:
- test_docker_network_connection 失敗
  原因: 網絡配置錯誤
  建議: 更新 docker-compose.yml

下一步:
1. 修復失敗的測試
2. 重新運行測試
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
