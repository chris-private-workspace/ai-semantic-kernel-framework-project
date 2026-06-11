# 📚 Claude 輔助文檔索引 (Claude Docs) - V2.0

> **目的**: AI 助手生成的分析、規劃和實施文檔，用於輔助開發過程
> **特性**: 流程導向、時間序列化、階段性文檔
> **與 docs/ 的區別**: docs/ 是正式團隊文檔，claudedocs/ 是 AI 生成的工作文檔
> **最後更新**: 2025-11-08 (完成 V2.0 流程導向重組)
> **新架構**: 數字編號體現開發流程自然順序 (規劃→執行→追蹤→變更→總結→輔助→歸檔)

---

## 📊 V2.0 文檔結構 (流程導向)

```
claudedocs/
├── 1-planning/          # 📋 總體規劃 (開始階段)
│   ├── roadmap/         # 路線圖和時間線
│   ├── epics/           # Epic 詳細規劃 (epic-9, epic-10)
│   └── architecture/    # 架構設計決策
│
├── 2-sprints/           # 🏃 Sprint 執行文檔 (執行階段)
│   ├── epic-9/          # Epic 9 Sprint 文檔
│   ├── epic-10/         # Epic 10 Sprint 文檔
│   └── templates/       # Sprint 模板
│
├── 3-progress/          # 📈 進度追蹤 (持續監控)
│   ├── weekly/          # 每週進度記錄
│   ├── daily/           # 每日開發日誌
│   └── milestones/      # 里程碑達成記錄
│
├── 4-changes/           # 🔄 變更記錄 (應對變化)
│   ├── bug-fixes/       # Bug 修復記錄 (FIX-XXX)
│   ├── feature-changes/ # 功能變更記錄
│   ├── refactoring/     # 重構記錄
│   └── i18n/            # 國際化變更記錄
│
├── 5-status/            # 📊 狀態報告 (階段總結)
│   ├── phase-reports/   # 階段完成報告
│   ├── testing/         # 測試報告 (e2e, unit, integration)
│   └── quality/         # 品質報告
│
├── 6-ai-assistant/      # 🤖 AI 助手指引 (輔助工具)
│   ├── session-guides/  # 會話指引 (如何開始/繼續開發)
│   ├── prompts/         # Prompt 模板
│   ├── analysis/        # AI 分析報告
│   └── handoff/         # 階段交接文檔
│
└── 7-archive/           # 🗄️ 歷史歸檔 (完成後)
    ├── epic-1-8/        # Epic 1-8 已完成文檔
    ├── design-system/   # 設計系統遷移歸檔
    └── mvp-phase/       # MVP 階段歸檔
```

---

## 📂 各目錄詳細說明

### 1-planning/ (總體規劃)

**用途**: 存放**高層次規劃文檔**，為開發提供方向和藍圖

**子目錄**:
- `roadmap/` - MASTER-ROADMAP.md, MILESTONE-TIMELINE.md, RELEASE-PLAN.md
- `epics/epic-9/` - Epic 9 概覽、需求、架構、風險評估
- `epics/epic-10/` - Epic 10 概覽、需求、架構、風險評估
- `architecture/` - 技術決策記錄 (ADR)、API 設計原則

**當前文件** (3 個):
- COMPLETE-IMPLEMENTATION-PLAN.md
- GIT-WORKFLOW-AND-BRANCHING-STRATEGY.md
- POC-VALIDATION-EXECUTION-PLAN.md

---

### 2-sprints/ (Sprint 執行文檔)

**用途**: 存放**Sprint 執行期間的詳細任務和計劃**

**子目錄**:
- `epic-9/sprint-X/` - SPRINT-X-PLAN.md, SPRINT-X-TASKS.md, SPRINT-X-RETRO.md, checklist.md
- `epic-10/sprint-X/` - (同上)
- `templates/` - Sprint 計劃、任務、回顧模板

**當前狀態**: 空 (Epic 9-10 尚未開始)

---

### 3-progress/ (進度追蹤)

**用途**: 持續記錄**開發進度和狀態**

**子目錄**:
- `weekly/` - 每週進度摘要 (2025-WXX.md)
- `daily/` - 每日開發日誌 (2025-MM/2025-MM-DD.md)
- `milestones/` - 里程碑達成記錄

**當前狀態**: 空 (待創建第一個每週進度報告)

**使用指引**:
- 每週五更新 `weekly/2025-WXX.md`
- 每日更新 `daily/2025-MM/2025-MM-DD.md` (可選)
- 達成里程碑時創建 `milestones/MX-xxx-complete.md`

---

### 4-changes/ (變更記錄)

**用途**: 記錄**所有變更、修正和重構**

**子目錄與文件數**:
- `bug-fixes/` - 29 個 Bug 修復文件 (FIX-009 ~ FIX-067)
- `feature-changes/` - 功能變更記錄 (待創建)
- `refactoring/` - 重構記錄 (待創建)
- `i18n/` - 14 個國際化文件 (I18N-*.md, DASHBOARD-I18N-DIAGNOSIS.md)

**Bug 修復總覽**:
- FIX-009: NextAuth v5 升級系列 (4 個文件)
- FIX-010 ~ FIX-058: 各類 Bug 修復總結 (11 個文件)
- FIX-059 ~ FIX-067: I18N 相關修復 (9 個文件)
- FIX-081 ~ FIX-087: 搜尋/過濾/語言切換系統性修復

---

### 5-status/ (狀態報告)

**用途**: 階段性的**狀態總結和品質報告**

**子目錄與文件數**:
- `phase-reports/` - 階段完成報告 (待創建)
- `testing/e2e/` - 12 個 E2E 測試文件
- `testing/unit/` - 單元測試報告 (待創建)
- `testing/integration/` - 整合測試報告 (待創建)
- `quality/` - 品質報告 (待創建)

**E2E 測試總覽**:
- E2E-TESTING-SETUP-GUIDE.md
- E2E-TESTING-ENHANCEMENT-PLAN.md
- E2E-TESTING-FINAL-REPORT.md (7/7 測試通過)
- E2E-WORKFLOW-TESTING-PROGRESS.md (Stage 1-4 完成)
- E2E-BUDGET-PROPOSAL-WORKFLOW-SUCCESS.md
- E2E-LOGIN-FIX-SUCCESS-SUMMARY.md
- 等 12 個文件

---

### 6-ai-assistant/ (AI 助手指引)

**用途**: 幫助 AI 助手**快速理解專案狀態和繼續工作**

**子目錄與文件數**:
- `session-guides/` - 會話指引 (待創建)
- `prompts/` - Prompt 模板 (待創建)
- `analysis/` - 5 個 AI 分析報告
- `handoff/` - 1 個交接文檔

**分析報告**:
- CLAUDE-MD-ANALYSIS-REPORT.md
- FILE-ORGANIZATION-PLAN.md
- MD-FILES-ORGANIZATION-REPORT.md
- REQUIREMENT-GAP-ANALYSIS.md
- UI-SCHEMA-GAP-ANALYSIS.md

**交接文檔**:
- PHASE-A-HANDOFF.md (MVP 完成後的項目交接)

---

### 7-archive/ (歷史歸檔)

**用途**: 存放**已完成階段的文檔**，保持活躍目錄的整潔

**子目錄與文件數**:
- `epic-1-8/` - 7 個已完成的 Epic 1-8 規劃文檔
- `design-system/` - 11 個設計系統遷移文檔
- `mvp-phase/` - 2 個 MVP 階段進度文檔

**Epic 1-8 歸檔**:
- mvp-development-plan.md
- mvp-implementation-checklist.md
- EPIC-5-MISSING-FEATURES.md (✅ 已完成)
- EPIC-6-TESTING-CHECKLIST.md (✅ 已完成)
- EPIC-7-IMPLEMENTATION-PLAN.md (✅ 已完成)
- STAGE-3-4-IMPLEMENTATION-PLAN.md
- COMPLETE-IMPLEMENTATION-PROGRESS.md

**設計系統歸檔**:
- DESIGN-SYSTEM-MIGRATION-PLAN.md (✅ 遷移計劃)
- DESIGN-SYSTEM-MIGRATION-PROGRESS.md (✅ 進度追蹤)
- PHASE-1~4-DETAILED-TASKS.md (✅ 4 個階段任務)
- USER-FEEDBACK-*.md (✅ 用戶反饋實施)
- 等 11 個文件

---

## 🔄 文檔生命週期

```
1. 創建階段:
   規劃文檔: 1-planning/
   Sprint 文檔: 2-sprints/

2. 活躍維護:
   進度追蹤: 3-progress/ (每日/每週更新)
   變更記錄: 4-changes/ (持續新增)

3. 階段總結:
   狀態報告: 5-status/ (Sprint/Phase 結束時)

4. 歸檔:
   已完成文檔: 7-archive/ (Epic/Phase 完成後)
```

---

## 🎯 快速導航指南

### 我想了解...

| 需求 | 查看目錄 |
|------|---------|
| **專案總體規劃** | `1-planning/roadmap/` (待創建 MASTER-ROADMAP.md) |
| **Epic 9-10 詳細規劃** | `1-planning/epics/epic-X/` (待創建) |
| **當前 Sprint 任務** | `2-sprints/epic-X/sprint-X/` (待開始) |
| **本週開發進度** | `3-progress/weekly/2025-WXX.md` (待創建) |
| **最近的 Bug 修復** | `4-changes/bug-fixes/` (29 個文件) |
| **I18N 相關變更** | `4-changes/i18n/` (14 個文件) |
| **E2E 測試報告** | `5-status/testing/e2e/` (12 個文件) |
| **如何開始新 Epic** | `6-ai-assistant/session-guides/` (待創建) |
| **AI 分析報告** | `6-ai-assistant/analysis/` (5 個文件) |
| **已完成的 Epic 1-8** | `7-archive/epic-1-8/` (7 個文件) |
| **設計系統遷移歷史** | `7-archive/design-system/` (11 個文件) |

---

## 📋 文檔命名規範

### 通用規則
- **UPPERCASE**: 重要的總覽文檔 (MASTER-ROADMAP.md)
- **kebab-case**: 詳細文檔 (epic-9-overview.md)
- **有意義的前綴**: FIX-XXX, CHANGE-XXX, REFACTOR-XXX
- **日期格式**: ISO 格式 (2025-11-08.md, 2025-W45.md)

### 各類文檔命名範例
```bash
# 規劃文檔
1-planning/roadmap/MASTER-ROADMAP.md
1-planning/epics/epic-9/epic-9-overview.md

# Sprint 文檔
2-sprints/epic-9/sprint-1/SPRINT-1-PLAN.md
2-sprints/epic-9/sprint-1/checklist.md

# 進度追蹤
3-progress/weekly/2025-W45.md
3-progress/daily/2025-11/2025-11-08.md

# 變更記錄
4-changes/bug-fixes/FIX-081-budget-proposals.md
4-changes/i18n/I18N-ISSUES-LOG.md

# 狀態報告
5-status/phase-reports/EPIC-9-COMPLETE.md
5-status/testing/e2e/E2E-WORKFLOW-TESTING-PROGRESS.md
```

---

## 📊 與舊結構的對應關係

| 舊位置 | 新位置 | 說明 |
|-------|-------|------|
| `planning/` | `1-planning/architecture/` + `7-archive/epic-1-8/` | 分離活躍規劃和已完成規劃 |
| `progress/` | `7-archive/mvp-phase/` | MVP 階段進度已歸檔 |
| `bug-fixes/` | `4-changes/bug-fixes/` | 納入變更記錄 |
| `e2e-testing/` | `5-status/testing/e2e/` | 歸類為狀態報告 |
| `design-system/` | `7-archive/design-system/` | 已完成，歸檔 |
| `implementation/` | `7-archive/design-system/` | 已完成，歸檔 |
| `analysis/` | `6-ai-assistant/analysis/` | AI 分析報告 |
| `handoff/` | `6-ai-assistant/handoff/` | 交接文檔 |
| 根目錄 I18N 文檔 | `4-changes/i18n/` | 納入變更記錄 |
| 根目錄 FIX-05X~06X | `4-changes/bug-fixes/` | Bug 修復記錄 |

---

## 🔗 與 docs/ 的區別

| 特性 | claudedocs/ | docs/ |
|------|-------------|-------|
| **性質** | AI 生成的工作文檔 | 正式團隊文檔 |
| **目的** | 輔助開發過程、分析問題、規劃任務 | 長期保存、團隊協作、正式文檔 |
| **生命週期** | 臨時性、階段性 | 永久性、持續維護 |
| **受眾** | AI 助手、開發者（短期參考） | 全體團隊、新成員、外部協作者 |
| **維護頻率** | 任務完成後可歸檔 | 持續更新 |
| **架構** | 流程導向（1-7 數字編號） | 內容導向（prd, stories, architecture） |

---

## ✅ V2.0 重組優勢

### 1. 流程清晰
- 數字編號體現開發流程: 規劃 → 執行 → 追蹤 → 變更 → 總結 → 輔助 → 歸檔
- 新開發者和 AI 助手可以快速理解當前階段

### 2. 易於維護
- 每個階段的文檔職責明確
- 歸檔策略清晰，避免文檔膨脹

### 3. AI 友善
- `6-ai-assistant/` 集中了所有 AI 輔助文檔
- Session guides 幫助 AI 快速上手（待創建）
- Prompts 模板提高一致性（待創建）

### 4. 擴展性強
- 新增階段可以插入數字編號
- 子目錄結構靈活可調整

### 5. 時間序列化
- `3-progress/` 按時間組織，便於追蹤歷史
- 里程碑記錄清晰標記重要節點

---

## 📊 統計數據

**V2.0 重組後統計** (2025-11-08):
- **總文件數**: ~60 個
- **1-planning/**: 3 個文件
- **2-sprints/**: 0 個 (待開始)
- **3-progress/**: 0 個 (待創建)
- **4-changes/**: 43 個文件 (29 bug-fixes + 14 i18n)
- **5-status/**: 12 個文件 (12 e2e)
- **6-ai-assistant/**: 6 個文件 (5 analysis + 1 handoff)
- **7-archive/**: 20 個文件 (7 epic-1-8 + 11 design-system + 2 mvp-phase)

**重組成果**:
- ✅ 創建 7 個主目錄（流程導向）
- ✅ 創建 23 個子目錄
- ✅ 遷移 60+ 個文件到新結構
- ✅ 清理根目錄散落文件
- ✅ 建立清晰的歸檔系統

---

## 🔄 維護計劃

### 每日維護
- ✅ 更新 `3-progress/daily/2025-MM-DD.md` (開發日誌)
- ✅ 更新 `2-sprints/epic-X/sprint-X/checklist.md` (完成的任務打勾)

### 每週維護
- ✅ 更新 `3-progress/weekly/2025-WXX.md` (每週進度摘要)
- ✅ 檢查 `4-changes/` (記錄修正和變更)

### Sprint 結束維護
- ✅ 完成 `2-sprints/epic-X/sprint-X/SPRINT-X-RETRO.md` (Sprint 回顧)
- ✅ 更新 `3-progress/milestones/` (里程碑記錄)

### Phase 結束維護
- ✅ 生成 `5-status/phase-reports/EPIC-X-COMPLETE.md` (階段報告)
- ✅ 歸檔已完成文檔到 `7-archive/`

### 季度維護
- ✅ 完整審查所有文檔結構
- ✅ 歸檔已完成的 Epic 文檔
- ✅ 更新 PROJECT-INDEX.md

---

## 📝 下一步行動

### 立即創建 (優先級 P0)
1. ✅ `1-planning/roadmap/MASTER-ROADMAP.md` - 總體路線圖
2. ✅ `1-planning/epics/epic-9/epic-9-overview.md` - Epic 9 概覽
3. ✅ `3-progress/weekly/2025-W45.md` - 本週進度報告
4. ✅ `6-ai-assistant/session-guides/START-NEW-EPIC.md` - 開始新 Epic 指引

### 本週創建 (優先級 P1)
1. ⏳ `1-planning/epics/epic-9/` 下的詳細規劃文檔
2. ⏳ `2-sprints/templates/` 下的 Sprint 模板
3. ⏳ `6-ai-assistant/prompts/` 下的 Prompt 模板

### 下週創建 (優先級 P2)
1. ⏳ `1-planning/epics/epic-10/` 下的詳細規劃文檔
2. ⏳ `2-sprints/epic-9/sprint-1/` 下的 Sprint 1 文檔

---

## 📖 相關文檔

- [DOCUMENTATION-STRUCTURE-V2.md](./DOCUMENTATION-STRUCTURE-V2.md) - V2.0 完整設計文檔
- [PROJECT-REORGANIZATION-PLAN.md](./PROJECT-REORGANIZATION-PLAN.md) - 重組計劃和 Epic 9 範例
- [WINDOWS-RESTART-GUIDE.md](./WINDOWS-RESTART-GUIDE.md) - Windows 環境重啟指南
- [../PROJECT-INDEX.md](../PROJECT-INDEX.md) - 專案完整文件索引

---

**維護者**: AI 助手 + 開發團隊
**版本**: V2.0 (流程導向)
**重組完成日期**: 2025-11-08
**問題回報**: 請更新 FIXLOG.md 或 DEVELOPMENT-LOG.md
