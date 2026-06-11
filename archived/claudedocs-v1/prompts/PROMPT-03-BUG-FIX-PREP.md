# PROMPT-03: BUG FIX PREPARATION
# Bug 修復準備

> **用途**: 準備修復 Bug,分析問題和影響範圍
> **變數**: `{BUG_ID}`
> **預估時間**: 3-5 分鐘
> **版本**: v3.0.0

---

## 🔤 變數定義

```yaml
{BUG_ID}:
  描述: Bug 標識符
  格式: "BUG-{N}" 或 "BUG-{YYYY-MM-DD}-{N}"
  範例: "BUG-001", "BUG-2025-11-20-001"
```

---

## 🎯 執行步驟

### Step 1: 讀取 Bug 報告

```yaml
可能的位置:
  - GitHub Issues
  - docs/bugs/bug-{ID}.md
  - claudedocs/bug-reports/bug-{ID}.md

提取信息:
  - Bug ID
  - 標題
  - 描述
  - 重現步驟
  - 預期行為 vs 實際行為
  - 嚴重程度
  - 優先級
  - 報告人
  - 報告日期
  - 影響版本
```

### Step 2: 分析問題

```yaml
分析內容:
  1. 問題根本原因分析
  2. 影響範圍評估
  3. 相關代碼位置識別
  4. 測試用例覆蓋情況
  5. 修復風險評估
```

### Step 3: 搜索相關代碼

```yaml
搜索策略:
  - 使用 Grep 搜索錯誤消息
  - 查找相關函數/類
  - 識別可能受影響的模塊
  - 檢查測試文件
```

---

## 📤 輸出格式

```markdown
# Bug 修復準備報告: {BUG_ID}

**生成時間**: {TIMESTAMP}
**生成者**: AI Assistant (PROMPT-03)

---

## 🐛 Bug 基本信息

| 項目 | 內容 |
|------|------|
| **Bug ID** | {BUG_ID} |
| **標題** | {BUG_TITLE} |
| **嚴重程度** | {SEVERITY} (Critical/High/Medium/Low) |
| **優先級** | {PRIORITY} (P0/P1/P2/P3) |
| **報告人** | {REPORTER} |
| **報告日期** | {REPORT_DATE} |
| **影響版本** | {AFFECTED_VERSION} |
| **當前狀態** | {STATUS} |

---

## 📝 問題描述

### 問題摘要
{BUG_DESCRIPTION}

### 重現步驟
1. {REPRODUCTION_STEP_1}
2. {REPRODUCTION_STEP_2}
3. {REPRODUCTION_STEP_3}

### 預期行為
{EXPECTED_BEHAVIOR}

### 實際行為
{ACTUAL_BEHAVIOR}

### 錯誤消息/截圖
```
{ERROR_MESSAGE}
```

---

## 🔍 根本原因分析

### 初步分析
{ROOT_CAUSE_ANALYSIS}

### 可能的原因
1. {POSSIBLE_CAUSE_1}
2. {POSSIBLE_CAUSE_2}
3. {POSSIBLE_CAUSE_3}

### 需要驗證的假設
- [ ] {HYPOTHESIS_1}
- [ ] {HYPOTHESIS_2}

---

## 📍 影響範圍評估

### 受影響的組件
- **組件**: {AFFECTED_COMPONENT_1}
  - 影響程度: {IMPACT_LEVEL}
  - 用戶影響: {USER_IMPACT}

### 受影響的功能
- {AFFECTED_FEATURE_1}
- {AFFECTED_FEATURE_2}

### 受影響的用戶場景
- {AFFECTED_SCENARIO_1}

---

## 💻 相關代碼位置

### 可能的問題代碼
```
{FILE_PATH_1}:{LINE_NUMBER}
{FILE_PATH_2}:{LINE_NUMBER}
```

### 相關測試文件
```
{TEST_FILE_1}
{TEST_FILE_2}
```

---

## ⚠️ 修復風險評估

### 風險等級: {RISK_LEVEL}

### 風險因素
1. **{RISK_FACTOR_1}**
   - 風險: {RISK_DESCRIPTION}
   - 緩解措施: {MITIGATION}

2. **{RISK_FACTOR_2}**
   - ...

### 建議修復策略
{FIX_STRATEGY}

---

## ✅ 修復準備檢查清單

問題理解:
- [ ] 已理解 Bug 根本原因
- [ ] 已確認重現步驟
- [ ] 已評估影響範圍

代碼分析:
- [ ] 已識別問題代碼位置
- [ ] 已查看相關測試用例
- [ ] 已評估修復風險

環境準備:
- [ ] 本地環境可重現 Bug
- [ ] 創建 bugfix branch
- [ ] 準備測試方案

---

## 🚀 下一步行動

1. ✅ Bug 分析完成
2. ⏭️ 開始編寫修復代碼
3. 🧪 編寫/更新測試用例
4. ✅ 驗證修復效果
5. 📋 使用 PROMPT-06 保存進度

---

## 📚 相關資源

- Bug 報告: {BUG_REPORT_LINK}
- 相關文檔: {RELATED_DOCS}
- 測試指南: {TEST_GUIDE}

---

**生成工具**: PROMPT-03
**版本**: v2.0.0
```

---

## 💡 使用範例

```bash
# 準備修復 Bug
用戶: "@PROMPT-03-BUG-FIX-PREP.md BUG-001"

AI 執行:
1. 讀取 Bug 報告
2. 分析問題根本原因
3. 搜索相關代碼
4. 評估影響範圍和修復風險
5. 生成修復準備報告

輸出:
---
🐛 Bug 修復準備完成

Bug: BUG-001 - Docker 容器網絡連接失敗
嚴重程度: High
優先級: P1

根本原因:
Docker Compose 網絡配置錯誤,backend 無法訪問 PostgreSQL

影響範圍:
- 本地開發環境
- 所有開發者

修復風險: Low
修復策略: 更新 docker-compose.yml 網絡配置

準備就緒: ✅
下一步: 開始修復代碼
---
```

---

## 🔗 相關文檔

- [AI Assistant Instructions](../AI-ASSISTANT-INSTRUCTIONS.md)
- [PROMPT-06: Progress Save](./PROMPT-06-PROGRESS-SAVE.md)

---

**版本**: v3.0.0
**更新日期**: 2025-12-01
