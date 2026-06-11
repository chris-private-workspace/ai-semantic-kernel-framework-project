# 03-implementation 文檔索引

**最後更新**: 2025-11-20
**維護者**: DevOps Team

本目錄包含項目實現階段的所有技術文檔,包括架構設計、Sprint 規劃和實現總結。

---

## 📂 目錄結構

```
03-implementation/
├── README.md (本文檔)
├── sprint-status.yaml (Sprint 追蹤主文件)
│
├── sprint-planning/ (Sprint 規劃文檔)
│   ├── sprint-0-mvp-revised.md
│   ├── sprint-1-core-services.md
│   ├── sprint-2-integrations.md
│   ├── sprint-3-security-observability.md
│   ├── sprint-4-ui-frontend.md
│   └── sprint-5-testing-launch.md
│
├── architecture-designs/ (架構設計文檔)
│   ├── azure-architecture-design.md
│   ├── database-schema-design.md
│   ├── project-structure-design.md
│   ├── authentication-design.md
│   ├── redis-cache-design.md
│   ├── message-queue-design.md
│   └── monitoring-design.md
│
├── implementation-guides/ (實現指南)
│   ├── local-development-guide.md
│   ├── deployment-guide.md
│   ├── azure-service-principal-setup.md
│   └── redis-usage-examples.md
│
├── sprint-summaries/ (Sprint 實現總結)
│   ├── S0-7-authentication-summary.md
│   ├── S0-8-monitoring-summary.md
│   └── S0-9-logging-summary.md
│
└── legacy/ (歷史文檔)
    ├── mvp-implementation-plan.md
    └── LOCAL-FIRST-UPDATE-SUMMARY.md
```

---

## 📋 文檔分類說明

### 1. Sprint 規劃文檔 (sprint-planning/)

**用途**: Sprint 執行的主要依據,定義每個 Sprint 的目標、Stories 和 Tasks

| 文件 | 狀態 | 說明 |
|------|------|------|
| `sprint-0-mvp-revised.md` | ✅ 已完成 | Sprint 0 基礎設施建設 (當前版本) |
| `sprint-1-core-services.md` | ⏳ 待執行 | Sprint 1 核心服務開發 |
| `sprint-2-integrations.md` | ⏳ 待執行 | Sprint 2 整合與擴展 |
| `sprint-3-security-observability.md` | ⏳ 待執行 | Sprint 3 安全與可觀測性 |
| `sprint-4-ui-frontend.md` | ⏳ 待執行 | Sprint 4 前端開發 |
| `sprint-5-testing-launch.md` | ⏳ 待執行 | Sprint 5 測試與上線 |

**重要性**: 🔴 **Critical** - 這是 Sprint 執行的主要依據

**使用時機**:
- Sprint Planning 會議
- 日常開發任務分配
- Sprint Review 檢查進度

---

### 2. 架構設計文檔 (architecture-designs/)

**用途**: 詳細的技術架構設計,開發時的參考文檔

| 文件 | 類別 | 說明 |
|------|------|------|
| `azure-architecture-design.md` | 雲端架構 | Azure 資源架構設計 |
| `database-schema-design.md` | 數據庫 | 完整的數據庫 Schema |
| `project-structure-design.md` | 代碼結構 | 項目目錄結構設計 |
| `authentication-design.md` | 認證系統 | JWT 認證架構設計 |
| `redis-cache-design.md` | 快取系統 | Redis 快取策略設計 |
| `message-queue-design.md` | 消息隊列 | 隊列系統架構設計 |
| `monitoring-design.md` | 監控系統 | OpenTelemetry + App Insights |

**重要性**: 🟡 **High** - 開發時需要參考

**使用時機**:
- 開始開發某個模組前
- Code Review 時檢查是否符合設計
- 技術討論和決策時

---

### 3. 實現指南 (implementation-guides/)

**用途**: 實際操作的 How-To 指南

| 文件 | 用途 | 說明 |
|------|------|------|
| `local-development-guide.md` | 本地開發 | Docker Compose 環境設置 |
| `deployment-guide.md` | 部署 | Azure 部署步驟 |
| `azure-service-principal-setup.md` | Azure 配置 | Service Principal 創建 |
| `redis-usage-examples.md` | 使用範例 | Redis 使用案例 |

**重要性**: 🟡 **High** - 實際操作時需要

**使用時機**:
- 新成員 onboarding
- 部署到新環境
- 遇到配置問題時

---

### 4. Sprint 實現總結 (sprint-summaries/)

**用途**: 記錄每個 Story 的實現細節和完成情況

| 文件 | Story | 說明 |
|------|-------|------|
| `S0-7-authentication-summary.md` | S0-7 | 認證框架實現總結 |
| `S0-8-monitoring-summary.md` | S0-8 | 監控系統實現總結 |
| `S0-9-logging-summary.md` | S0-9 | 日誌系統實現總結 |

**重要性**: 🟢 **Medium** - 參考和回顧用

**使用時機**:
- Sprint Retrospective
- 技術文檔編寫
- 新功能參考已完成的實現

**命名規範**: `S{Sprint}-{Story}-{模組名}-summary.md`

---

### 5. 歷史文檔 (legacy/)

**用途**: 已被取代但保留的歷史文檔

| 文件 | 說明 |
|------|------|
| `mvp-implementation-plan.md` | 早期 MVP 計劃 (已被 Sprint 規劃取代) |
| `LOCAL-FIRST-UPDATE-SUMMARY.md` | 本地優先開發總結 (已完成) |

**重要性**: 🔵 **Low** - 僅供參考

---

## 🔄 文檔生命週期

### Sprint 規劃階段
1. **讀取**: `sprint-planning/sprint-{N}-*.md`
2. **參考**: 相關的 `architecture-designs/` 文檔
3. **更新**: `sprint-status.yaml` (標記 Story 為 in-progress)

### Sprint 開發階段
1. **跟隨**: Sprint 規劃文檔
2. **參考**: 架構設計和實現指南
3. **更新**: `sprint-status.yaml` (更新進度)

### Sprint 完成階段
1. **創建**: `S{Sprint}-{Story}-summary.md` 實現總結
2. **更新**: `sprint-status.yaml` (標記 Story 為 completed)
3. **生成**: Sprint 完成報告 (在 `claudedocs/sprint-reports/`)

---

## 📊 當前狀態 (2025-11-20)

### Sprint 0 ✅ 已完成

**完成的 Stories**: 9/9 (100%)
**完成點數**: 42/38 (110.5%)

**生成的文檔**:
- ✅ 7 個架構設計文檔
- ✅ 4 個實現指南
- ✅ 3 個 Story 實現總結 (S0-7, S0-8, S0-9)
- ✅ Sprint 0 完成報告
- ✅ 架構 Code Review 報告

### Sprint 1 ⏳ 待開始

**主要任務**: 核心服務開發
**規劃文檔**: `sprint-planning/sprint-1-core-services.md`
**預計開始**: 2025-12-09

---

## 🎯 如何使用這些文檔?

### 情境 1: 開始新的 Sprint

```bash
# 1. 讀取 Sprint 規劃
open archived/docs-v1/03-implementation/sprint-planning/sprint-1-core-services.md

# 2. 檢查 Sprint Status
open docs/03-implementation/sprint-status.yaml

# 3. 參考相關架構設計
open archived/docs-v1/03-implementation/architecture-designs/
```

### 情境 2: 開發特定功能

```bash
# 1. 找到對應的 Story (從 sprint-status.yaml)
# 2. 讀取相關的架構設計文檔
# 3. 參考實現指南
# 4. 開始開發
```

### 情境 3: 完成 Story 後

```bash
# 1. 創建 Story 實現總結
touch docs/03-implementation/S1-{N}-{name}-summary.md

# 2. 更新 sprint-status.yaml
# 3. 生成 Sprint 報告 (使用 PROMPT-06)
```

### 情境 4: 新成員 Onboarding

**建議閱讀順序**:
1. `README.md` (本文檔)
2. `sprint-status.yaml` (了解當前進度)
3. `architecture-designs/azure-architecture-design.md` (整體架構)
4. `implementation-guides/local-development-guide.md` (環境設置)
5. 當前 Sprint 的規劃文檔

---

## 🔧 文檔維護規範

### 命名規範

**架構設計**: `{模組名}-design.md`
- 範例: `authentication-design.md`

**實現指南**: `{用途}-guide.md`
- 範例: `local-development-guide.md`

**Sprint 總結**: `S{Sprint}-{Story}-{模組名}-summary.md`
- 範例: `S0-7-authentication-summary.md`

**Sprint 規劃**: `sprint-{N}-{主題}.md`
- 範例: `sprint-1-core-services.md`

### 更新頻率

| 文檔類型 | 更新頻率 | 負責人 |
|---------|---------|--------|
| Sprint 規劃 | Sprint 開始前 | Product Owner |
| 架構設計 | 需求變更時 | Tech Lead |
| 實現指南 | 流程變更時 | DevOps |
| Sprint 總結 | Story 完成時 | 開發者 |
| sprint-status.yaml | 每日 | Scrum Master |

### 文檔審查

- **架構設計文檔**: 需要 Tech Lead 審查
- **實現指南**: 需要團隊 Review
- **Sprint 總結**: 自動生成,可選擇性審查

---

## 📚 相關文檔

### 其他重要文檔位置

```
docs/
├── 01-planning/          # PRD, 產品規劃
├── 02-architecture/      # 技術架構 (高階)
├── 03-implementation/    # 實現文檔 (本目錄)
├── 04-usage/            # 使用指南和最佳實踐
└── 05-operations/       # 運維文檔

claudedocs/
├── sprint-reports/      # Sprint 完成報告
├── session-logs/        # 工作 Session 記錄
└── code-review/         # Code Review 報告
```

### 文檔層次關係

```
01-planning (戰略層)
    ↓
02-architecture (架構層)
    ↓
03-implementation (實現層) ← 你在這裡
    ↓
04-usage (使用層)
    ↓
05-operations (運維層)
```

---

## 🤔 常見問題

### Q1: Sprint 規劃文檔和 sprint-status.yaml 哪個是主要依據?

**A**:
- **Sprint 規劃文檔**: 詳細的 Story 描述、Tasks、技術方案
- **sprint-status.yaml**: 進度追蹤、狀態管理

**使用策略**:
1. Sprint 開始前讀取規劃文檔了解詳情
2. 日常開發參考 sprint-status.yaml 追蹤進度
3. 兩者互補使用

### Q2: 為什麼有這麼多架構設計文檔?

**A**: 每個文檔對應一個主要模組:
- 方便專注閱讀某個模組
- 避免單一文檔過長
- 便於並行編輯和維護

### Q3: Story 實現總結是必須的嗎?

**A**:
- **S0-1 到 S0-6**: 較簡單,沒有單獨總結
- **S0-7 到 S0-9**: 較複雜,有詳細總結
- **建議**: 複雜 Story (>5 points) 應該有總結

### Q4: 歷史文檔可以刪除嗎?

**A**:
- **不建議刪除**: 保留作為歷史參考
- **建議**: 移動到 `legacy/` 目錄
- **標記**: 在文件開頭註明 "已過期" 或 "已被取代"

---

## ✅ 待辦事項

### 文檔整理任務

- [x] 創建 README.md 索引文件
- [ ] 創建子目錄結構
  - [ ] `architecture-designs/`
  - [ ] `implementation-guides/`
  - [ ] `sprint-summaries/`
  - [ ] `legacy/`
- [ ] 移動文件到對應目錄
- [ ] 更新文檔內部鏈接
- [ ] 創建 S0-1 到 S0-6 的簡化總結

### Sprint 1 準備

- [ ] 細化 Sprint 1 規劃文檔
- [ ] 創建 Sprint 1 技術設計文檔
- [ ] 準備開發環境
- [ ] 分配任務

---

**維護者**: DevOps Team
**版本**: v1.0.0
**最後更新**: 2025-11-20
