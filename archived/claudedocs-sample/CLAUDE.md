# ClaudeDocs - AI 助手文檔目錄

> **相關規則**: 請參閱 `.claude/rules/documentation.md` 獲取文檔撰寫的完整規範

## 📋 目錄用途

此目錄是 AI 助手（Claude）與開發團隊協作產出的項目文檔中心，採用結構化的 7 層分類方式組織，涵蓋從規劃、開發到維運的完整生命週期文檔。這些文檔用於：

- **項目規劃**: Epic 架構設計、功能規劃、路線圖
- **進度追蹤**: 每日/每週進度報告、Sprint 計劃
- **變更管理**: Bug 修復記錄、功能變更追蹤
- **AI 協作**: 情境提示詞、工作流程指南、分析報告
- **知識傳承**: 開發經驗、故障排查、部署指南

---

## 🎯 項目概覽 - AI Document Extraction

### 核心目標
- **年處理量**: 450,000-500,000 張發票（APAC 地區）
- **自動化率**: 90-95%
- **準確率**: 90-95%
- **節省人時**: 35,000-40,000 人時/年

### 核心架構 - 三層映射系統

```
┌─────────────────────────────────────────────────────────────────┐
│ TIER 1: Universal Mapping（通用層）                              │
│ • 覆蓋 70-80% 常見術語，所有 Forwarder 通用                      │
├─────────────────────────────────────────────────────────────────┤
│ TIER 2: Forwarder-Specific Override（特定覆蓋層）                │
│ • 只記錄該 Forwarder 與通用規則「不同」的映射                    │
├─────────────────────────────────────────────────────────────────┤
│ TIER 3: LLM Classification（AI 智能分類）                        │
│ • 當以上都無法匹配時，使用 GPT-4o 智能分類                       │
└─────────────────────────────────────────────────────────────────┘
```

### 信心度路由機制

| 信心度範圍 | 處理方式 | 說明 |
|-----------|---------|------|
| ≥ 90% | AUTO_APPROVE | 自動通過，無需人工介入 |
| 70-89% | QUICK_REVIEW | 快速人工確認 |
| < 70% | FULL_REVIEW | 完整人工審核 |

---

## 🏗️ 目錄結構詳解

```
claudedocs/
├── 1-planning/                  # 規劃文檔
│   ├── architecture/            # 架構設計文檔
│   │   ├── THREE-TIER-MAPPING-SYSTEM.md   # 三層映射系統設計
│   │   └── CONFIDENCE-ROUTING.md          # 信心度路由機制
│   ├── epics/                   # Epic 規劃 (Epic 0-15)
│   │   ├── epic-0/              # 歷史數據初始化
│   │   ├── epic-1/              # 用戶認證與存取控制
│   │   └── ... (epic-2 ~ epic-12)
│   ├── features/                # Feature 規劃
│   └── roadmap/                 # 產品路線圖
│
├── 2-sprints/                   # Sprint 文檔
│   └── sprint-planning/         # Sprint 計劃記錄
│
├── 3-progress/                  # 進度追蹤
│   ├── daily/                   # 每日進度
│   └── weekly/                  # 每週進度報告
│
├── 4-changes/                   # 變更記錄
│   ├── bug-fixes/               # Bug 修復記錄
│   └── feature-changes/         # 功能變更記錄
│
├── 5-status/                    # 狀態報告
│   └── testing/                 # 測試文檔
│       ├── plans/               # 測試計劃 (TEST-PLAN-*)
│       ├── reports/             # 測試報告 (TEST-REPORT-*)
│       ├── e2e/                 # E2E 測試文檔
│       ├── manual/              # 手動測試文檔
│       └── TESTING-FRAMEWORK.md # 測試框架說明
│
├── 6-ai-assistant/              # AI 助手相關
│   ├── analysis/                # 分析報告
│   ├── prompts/                 # 情境提示詞 (SITUATION-*)
│   │   ├── SITUATION-1-PROJECT-ONBOARDING.md   # 項目入門
│   │   ├── SITUATION-2-FEATURE-DEV-PREP.md     # 功能開發準備
│   │   ├── SITUATION-3-FEATURE-ENHANCEMENT.md  # 功能增強
│   │   ├── SITUATION-4-NEW-FEATURE-DEV.md      # 新功能開發
│   │   └── SITUATION-5-SAVE-PROGRESS.md        # 保存進度
│   └── session-guides/          # 會話指南
│
├── 7-archive/                   # 歸檔文檔
│   └── templates/               # 文檔範本
│
└── CLAUDE.md                    # 本文件 - 目錄索引
```

---

## 📊 項目進度追蹤

### Epic 完成狀態 (2026-01-20)

| Epic | 名稱 | 狀態 | 完成日期 |
|------|------|------|----------|
| Epic 0 | 歷史數據初始化 | ✅ 已完成 | 2025-12-26 |
| Epic 1 | 用戶認證與存取控制 | ✅ 已完成 | 2025-12-18 |
| Epic 2 | 手動發票上傳與 AI 處理 | ✅ 已完成 | 2025-12-18 |
| Epic 3 | 發票審核與修正工作流 | ✅ 已完成 | 2025-12-19 |
| Epic 4 | 映射規則管理與自動學習 | ✅ 已完成 | 2025-12-19 |
| Epic 5 | Forwarder 配置管理 | ✅ 已完成 | 2025-12-19 |
| Epic 6 | 多城市數據隔離 | ✅ 已完成 | 2025-12-19 |
| Epic 7 | 報表儀表板與成本追蹤 | ✅ 已完成 | 2025-12-20 |
| Epic 8 | 審計追溯與合規 | ✅ 已完成 | 2025-12-20 |
| Epic 9 | 自動化文件獲取 | ✅ 已完成 | 2025-12-20 |
| Epic 10 | n8n 工作流整合 | ✅ 已完成 | 2025-12-21 |
| Epic 11 | 對外 API 服務 | ✅ 已完成 | 2025-12-21 |
| Epic 12 | 系統管理與監控 | ✅ 已完成 | 2025-12-21 |
| Epic 13 | 文件預覽與欄位映射 | ✅ 已完成 | 2026-01-03 |
| Epic 14 | Prompt 配置與動態生成 | ✅ 已完成 | 2026-01-03 |
| Epic 15 | 統一 3 層機制到日常處理流程 | ✅ 已完成 | 2026-01-03 |
| Epic 16 | 文件格式管理 | ✅ 已完成 | 2026-01-14 |
| Epic 17 | 國際化 (i18n) | ✅ 已完成 | 2026-01-17 |
| Epic 18 | 本地帳號認證系統 | ✅ 已完成 | 2026-01-19 |

### Epic 0 詳細進度 (歷史數據初始化)

| Story | 名稱 | 狀態 |
|-------|------|------|
| 0-1 | 批次文件上傳與元數據偵測 | ✅ 已完成 |
| 0-2 | 智能處理路由 | ✅ 已完成 |
| 0-3 | Just-in-Time 公司配置 | ✅ 已完成 |
| 0-4 | 批次處理進度追蹤 | ✅ 已完成 |
| 0-5 | 術語聚合與初始規則 | ✅ 已完成 |
| 0-6 | 批次公司識別整合 | ✅ 已完成 |
| 0-7 | 批次術語聚合整合 | ✅ 已完成 |
| 0-8 | 文件發行者識別 | ✅ 已完成 |
| 0-9 | 文件格式術語重組 | ✅ 已完成 |
| 0-10 | AI 術語驗證服務 | ✅ 已完成 |
| 0-11 | GPT Vision Prompt 優化 | ✅ 已完成 |

### 進行中的功能變更

| 編號 | 名稱 | 狀態 | 描述 |
|------|------|------|------|
| CHANGE-001 | Native PDF 雙重處理架構增強 | ⏳ 待實作 | 為 Native PDF 新增 GPT Vision (分類) + Azure DI (數據) 雙重處理 |

---

## 📝 文檔命名約定

### Epic 規劃
```
claudedocs/1-planning/epics/
├── epic-{N}/
│   ├── overview.md              # Epic 概述
│   ├── architecture.md          # 技術架構
│   ├── stories.md               # User Stories 列表
│   └── progress.md              # 進度追蹤
```

**Epic 編號**: 0-15 (共 16 個 Epic)

### 功能變更 (CHANGE-*)
```
claudedocs/4-changes/feature-changes/
└── CHANGE-{NNN}-{description}.md
```

**標準 CHANGE 文檔內容結構**:
```markdown
# CHANGE-{NNN}: {Change Title}

> **建立日期**: YYYY-MM-DD
> **完成日期**: YYYY-MM-DD
> **狀態**: ✅ 已完成 | 🚧 進行中
> **優先級**: High | Medium | Low

## 1. 變更概述
## 2. 功能需求
## 3. 技術設計
## 4. 影響範圍
## 5. 驗收標準
```

### Bug 修復 (FIX-*)
```
claudedocs/4-changes/bug-fixes/
└── FIX-{NNN}-{description}.md
```

**標準 FIX 文檔內容結構**:
```markdown
# FIX-{NNN}: {Bug Description}

## 問題描述
## 重現步驟
## 根本原因
## 解決方案
## 修改的檔案
## 測試驗證
```

### 進度報告
```
claudedocs/3-progress/
├── daily/{YYYY}-{MM}/{YYYY}-{MM}-{DD}.md       # 日報
└── weekly/{YYYY}-W{WW}.md                       # 週報
```

### 測試文檔 (TEST-PLAN-* / TEST-REPORT-*)
```
claudedocs/5-status/testing/
├── plans/
│   └── TEST-PLAN-{NNN}-{description}.md     # 測試計劃
├── reports/
│   └── TEST-REPORT-{NNN}-{description}.md   # 測試報告
├── e2e/                                      # E2E 測試文檔
├── manual/                                   # 手動測試文檔
└── TESTING-FRAMEWORK.md                      # 框架說明
```

**標準 TEST-PLAN 文檔結構**:
```markdown
# TEST-PLAN-{NNN}: {Title}

> **建立日期**: YYYY-MM-DD
> **關聯 Epic/Story**: Epic X / Story X.X
> **狀態**: ✅ 已完成 | 🚧 進行中

## 1. 測試範圍
## 2. 測試案例
## 3. 測試環境
## 4. 執行結果
```

### 情境提示詞 (SITUATION-*)
```
claudedocs/6-ai-assistant/prompts/
└── SITUATION-{N}-{DESCRIPTION}.md
```

**SITUATION 編號**: 連續數字 (SITUATION-1 ~ SITUATION-5)

**SITUATION 文檔結構**:
```markdown
# SITUATION-{N}: {Title}

**用途**: {觸發條件和使用情境}
**觸發情境**:
  - {情境 1}
  - {情境 2}

## 📋 快速開始檢查清單
## 🚀 執行流程
## ⚠️ 關鍵提醒
## 📁 相關檔案參考
## ✅ 完成檢查清單
```

---

## 🛠️ 技術棧

### 核心框架
- **前端**: Next.js 15 (App Router) + TypeScript
- **樣式**: Tailwind CSS + shadcn/ui
- **資料庫**: PostgreSQL + Prisma ORM
- **狀態管理**: Zustand (UI) + React Query (Server State)
- **表單**: React Hook Form + Zod 驗證
- **國際化**: next-intl（支援 en, zh-TW, zh-CN）

### 外部服務
- **OCR**: Azure Document Intelligence
- **AI**: Azure OpenAI GPT-5.2 (含 GPT Vision)
- **認證**: Azure AD (Entra ID) SSO
- **工作流**: n8n
- **文件來源**: SharePoint / Outlook / Azure Blob Storage

---

## 🔍 重要文檔索引

### AI 助手工作流程

| 文檔路徑 | 用途 |
|----------|------|
| `6-ai-assistant/prompts/SITUATION-1-PROJECT-ONBOARDING.md` | 項目入門、新會話啟動 |
| `6-ai-assistant/prompts/SITUATION-2-FEATURE-DEV-PREP.md` | 功能開發準備、任務分析 |
| `6-ai-assistant/prompts/SITUATION-3-FEATURE-ENHANCEMENT.md` | 功能增強、代碼優化 |
| `6-ai-assistant/prompts/SITUATION-4-NEW-FEATURE-DEV.md` | 新功能開發、實作執行 |
| `6-ai-assistant/prompts/SITUATION-5-SAVE-PROGRESS.md` | 保存進度、會話結束 |

### 分析報告

| 文檔路徑 | 用途 |
|----------|------|
| `6-ai-assistant/analysis/ANALYSIS-001-HISTORICAL-DATA-FLOW.md` | Epic 0 歷史數據初始化 7 階段流程架構分析 |

### 測試計劃

| 文檔路徑 | 用途 |
|----------|------|
| `5-status/testing/plans/TEST-PLAN-001-dual-processing.md` | CHANGE-001 雙重處理專用測試 |
| `5-status/testing/plans/TEST-PLAN-002-EPIC-0-COMPLETE.md` | Epic 0 Stories 0-1~0-9 測試（舊版） |
| `5-status/testing/plans/TEST-PLAN-003-EPIC-0-FULL-FEATURE.md` | Epic 0 完整功能測試（含 Stories 0-10, 0-11） |

### 核心文檔

| 文檔路徑 | 用途 |
|----------|------|
| `CLAUDE.md` (根目錄) | 專案總指南 |
| `docs/01-planning/prd/` | 產品需求文檔 |
| `docs/02-architecture/` | 系統架構設計 |
| `docs/03-stories/` | User Stories |
| `docs/04-implementation/sprint-status.yaml` | Sprint 狀態追蹤 |

---

## 🛠️ 使用指南

### 查找文檔

| 需求 | 路徑 |
|------|------|
| Epic 規劃 | `1-planning/epics/epic-{N}/` |
| 功能變更 | `4-changes/feature-changes/CHANGE-{NNN}-*` |
| Bug 修復 | `4-changes/bug-fixes/FIX-{NNN}-*` |
| 測試計劃 | `5-status/testing/plans/TEST-PLAN-{NNN}-*` |
| 測試報告 | `5-status/testing/reports/TEST-REPORT-{NNN}-*` |
| 週報 | `3-progress/weekly/` |
| AI 工作流程 | `6-ai-assistant/prompts/` |
| 範本 | `7-archive/templates/` |

### 創建新文檔

1. **確定文檔類型和目錄**
   - 新 Epic → `1-planning/epics/epic-{N}/`
   - 功能變更 → `4-changes/feature-changes/`
   - Bug 修復 → `4-changes/bug-fixes/`
   - 測試計劃 → `5-status/testing/plans/`
   - 測試報告 → `5-status/testing/reports/`
   - 進度報告 → `3-progress/`

2. **使用正確的命名約定**
   - Epic: `epic-{N}` (0-12)
   - CHANGE: `CHANGE-{NNN}-{description}.md`
   - FIX: `FIX-{NNN}-{description}.md`
   - TEST-PLAN: `TEST-PLAN-{NNN}-{description}.md`
   - TEST-REPORT: `TEST-REPORT-{NNN}-{description}.md`

3. **遵循格式範本**
   - 參考 `7-archive/templates/` 下的範本
   - 包含必要的 frontmatter
   - 使用一致的章節標題

---

## ⚠️ 重要約定

1. **命名一致性**
   - 使用 UPPERCASE-WITH-DASHES 格式
   - 編號使用三位數 (001, 002, ...)
   - 描述使用簡短英文 kebab-case

2. **語言規範**
   - 文檔內容: 繁體中文為主
   - 代碼片段: 英文
   - 日期格式: YYYY-MM-DD

3. **狀態標記**
   - ✅ 已完成
   - 🚧 進行中
   - ⏸️ 暫停/待開發
   - ❌ 已取消
   - ⚠️ 有風險/需注意

4. **禁止事項**
   - ❌ 在錯誤目錄創建文檔
   - ❌ 使用不一致的命名格式
   - ❌ 遺漏必要的 frontmatter
   - ❌ 留下未更新的過時內容

---

## 📚 相關文件

### 項目級文檔
- `CLAUDE.md` - 根目錄專案總指南
- `docs/04-implementation/sprint-status.yaml` - Sprint 狀態追蹤

### 規則文件
- `.claude/rules/general.md` - 通用開發規範
- `.claude/rules/components.md` - 組件開發規範
- `.claude/rules/typescript.md` - TypeScript 規範
- `.claude/rules/i18n.md` - 國際化開發規範
- `.claude/rules/api-design.md` - API 設計規範
- `.claude/rules/services.md` - 服務層規範
- `.claude/rules/database.md` - 資料庫規範
- `.claude/rules/testing.md` - 測試規範
- `.claude/rules/technical-obstacles.md` - 技術障礙處理

---

**維護者**: AI 助手 + 開發團隊
**最後更新**: 2026-01-18
**文檔版本**: 1.6.0
