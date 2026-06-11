# AI Document Extraction - 測試策略框架

> **版本**: 1.0.0
> **建立日期**: 2025-12-27
> **適用範圍**: 所有功能測試

---

## 概述

本文件定義項目的整體測試策略，包括測試類型、目錄結構、文檔規範和執行流程。此框架適用於所有新功能和變更的測試。

---

## 測試目錄結構

### 1. 自動化測試代碼 (`tests/`)

```
tests/
├── unit/                           # 單元測試
│   ├── services/                   # 服務層測試
│   │   ├── batch-processor.test.ts
│   │   ├── gpt-vision.test.ts
│   │   └── processing-router.test.ts
│   ├── utils/                      # 工具函數測試
│   └── hooks/                      # Hooks 測試
│
├── integration/                    # 整合測試
│   ├── api/                        # API 端點測試
│   │   └── documents.test.ts
│   └── services/                   # 服務間整合測試
│       └── dual-processing.test.ts
│
└── e2e/                            # 端到端測試
    ├── document-upload.spec.ts     # 文件上傳流程
    ├── batch-processing.spec.ts    # 批次處理流程
    └── review-workflow.spec.ts     # 審核工作流
```

### 2. 測試文檔 (`claudedocs/5-status/testing/`)

```
claudedocs/5-status/testing/
├── TESTING-FRAMEWORK.md            # 本文件 - 測試策略總綱
│
├── plans/                          # 測試計劃
│   ├── TEST-PLAN-001-dual-processing.md
│   ├── TEST-PLAN-002-*.md
│   └── ...
│
├── reports/                        # 測試報告
│   ├── TEST-REPORT-2025-12-27-dual-processing.md
│   └── ...
│
├── manual/                         # 手動測試腳本
│   ├── MANUAL-TEST-001-file-upload.md
│   └── ...
│
└── e2e/                            # E2E 測試文檔（已存在）
    └── ...
```

---

## 測試類型與覆蓋率目標

| 測試類型 | 目的 | 覆蓋率目標 | 執行時機 |
|---------|------|-----------|---------|
| **單元測試** | 驗證單一函數/模組 | ≥ 80% | 每次 commit |
| **整合測試** | 驗證模組間交互 | ≥ 70% | 每次 PR |
| **E2E 測試** | 驗證完整用戶流程 | 關鍵流程 | 每次 release |
| **手動測試** | 探索性測試/UI 驗證 | 新功能必須 | 功能完成時 |

---

## 測試計劃文檔規範

### 命名規則

```
TEST-PLAN-{NNN}-{description}.md

範例:
- TEST-PLAN-001-dual-processing.md
- TEST-PLAN-002-batch-upload.md
```

### 測試計劃模板

```markdown
# TEST-PLAN-{NNN}: {功能名稱}

> **狀態**: 📝 草稿 | 🔄 進行中 | ✅ 完成 | ❌ 失敗
> **建立日期**: YYYY-MM-DD
> **關聯變更**: CHANGE-XXX / Story X.X
> **測試人員**: {姓名}

---

## 測試目標

[描述此測試要驗證什麼]

## 前置條件

- [ ] 環境已準備
- [ ] 測試數據已就緒
- [ ] 相依服務已啟動

## 測試範圍

### 包含
- [要測試的功能點]

### 排除
- [不在此次測試範圍的項目]

## 測試場景

### 場景 1: {場景名稱}
| 步驟 | 操作 | 預期結果 | 實際結果 | 狀態 |
|------|------|---------|---------|------|
| 1 | | | | ⏳ |
| 2 | | | | ⏳ |

### 場景 2: {場景名稱}
...

## 測試數據

| 數據類型 | 文件名/描述 | 用途 |
|---------|------------|------|
| | | |

## 風險與緩解

| 風險 | 影響 | 緩解措施 |
|------|------|---------|
| | | |

## 測試結果摘要

| 項目 | 結果 |
|------|------|
| 總場景數 | X |
| 通過 | X |
| 失敗 | X |
| 阻塞 | X |
| 通過率 | X% |

## 發現的問題

| 問題編號 | 描述 | 嚴重度 | 狀態 |
|---------|------|--------|------|
| | | | |

## 結論與建議

[測試結論和後續建議]
```

---

## 測試報告文檔規範

### 命名規則

```
TEST-REPORT-{YYYY-MM-DD}-{description}.md

範例:
- TEST-REPORT-2025-12-27-dual-processing.md
- TEST-REPORT-2025-12-28-batch-upload.md
```

---

## 測試環境要求

### 本地開發環境

```bash
# 必要服務
- PostgreSQL (Docker)
- Node.js 20+
- npm 10+

# 環境變數
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=xxx
AZURE_DOCUMENT_INTELLIGENCE_KEY=xxx
AZURE_OPENAI_ENDPOINT=xxx
AZURE_OPENAI_API_KEY=xxx
```

### 測試數據準備

| 文件類型 | 建議數量 | 來源 |
|---------|---------|------|
| Native PDF | 5+ | 真實發票樣本 |
| Scanned PDF | 5+ | 掃描發票 |
| Image (JPG/PNG) | 3+ | 拍照發票 |

**測試數據存放位置**: `uploads/test-samples/` (不提交到 Git)

---

## 測試執行流程

### 1. 手動測試流程

```
1. 閱讀測試計劃 (TEST-PLAN-XXX.md)
       ↓
2. 準備測試環境和數據
       ↓
3. 按照場景逐步執行
       ↓
4. 記錄實際結果
       ↓
5. 更新測試報告 (TEST-REPORT-XXX.md)
       ↓
6. 如有問題，創建 Bug 記錄
```

### 2. 自動化測試執行

```bash
# 單元測試
npm run test:unit

# 整合測試
npm run test:integration

# E2E 測試
npm run test:e2e

# 全部測試 + 覆蓋率
npm run test:coverage
```

---

## 測試優先級

### P0 - 必須測試（阻塞發布）
- 核心處理流程（文件上傳 → AI 處理 → 結果輸出）
- 數據正確性（提取結果準確）
- 安全性（認證、授權）

### P1 - 應該測試（高優先級）
- 邊界條件（空文件、大文件、格式錯誤）
- 錯誤處理（服務不可用、超時）
- 性能指標（處理時間、成本）

### P2 - 可以測試（中優先級）
- UI/UX 體驗
- 兼容性（不同瀏覽器、設備）

### P3 - 有時間再測（低優先級）
- 極端邊界情況
- 壓力測試

---

## 狀態標記

| 標記 | 含義 |
|------|------|
| ⏳ | 待測試 |
| 🔄 | 測試中 |
| ✅ | 通過 |
| ❌ | 失敗 |
| ⚠️ | 部分通過/有風險 |
| 🚫 | 阻塞/無法測試 |

---

## 與其他文檔的關係

```
claudedocs/
├── 4-changes/feature-changes/CHANGE-XXX.md  ← 功能變更描述
│           ↓
├── 5-status/testing/plans/TEST-PLAN-XXX.md  ← 測試計劃
│           ↓
├── 5-status/testing/reports/TEST-REPORT-*.md ← 測試結果
│           ↓
└── 4-changes/bug-fixes/FIX-XXX.md           ← 發現的問題
```

---

## 相關文檔

- [測試規範](.claude/rules/testing.md) - 自動化測試代碼規範
- [CHANGE-001](../../../4-changes/feature-changes/CHANGE-001-native-pdf-dual-processing.md) - Native PDF 雙重處理

---

**維護者**: Development Team
**最後更新**: 2025-12-27
