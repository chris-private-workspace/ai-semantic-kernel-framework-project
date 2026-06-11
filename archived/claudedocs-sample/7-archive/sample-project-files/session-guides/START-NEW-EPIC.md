# 🚀 Session Guide: 開始新 Epic 開發

> **使用時機**: 準備開始新的 Epic 開發 (例如: Epic 9, Epic 10)
> **目標**: 完整理解 Epic 需求、設定環境、建立開發計劃
> **預計時間**: 30-60 分鐘

---

## 📋 開發人員檢查清單

在開始新 Epic 前，請確認以下項目:

### 🎯 規劃文檔準備
- [ ] Epic 概覽文檔存在 (`claudedocs/1-planning/epics/epic-X/epic-X-overview.md`)
- [ ] Epic 需求文檔存在 (`claudedocs/1-planning/epics/epic-X/epic-X-requirements.md`)
- [ ] Epic 技術架構文檔存在 (`claudedocs/1-planning/epics/epic-X/epic-X-architecture.md`)
- [ ] Epic 風險分析文檔存在 (`claudedocs/1-planning/epics/epic-X/epic-X-risks.md`)
- [ ] 使用者故事已撰寫 (`docs/stories/epic-X/`)

### 🛠️ 開發環境準備
- [ ] 已閱讀 `DEVELOPMENT-SETUP.md` 並完成環境設定
- [ ] 已執行 `pnpm check:env` 確認環境正常
- [ ] 已執行 `pnpm dev` 確認系統可啟動
- [ ] Git 狀態乾淨 (`git status` 無未提交變更)
- [ ] 已更新到最新 main 分支 (`git pull origin main`)

### 📚 技術研究準備
- [ ] 已研究新技術棧 (如 Azure OpenAI, Azure AI Search)
- [ ] 已閱讀相關 SDK 文檔
- [ ] 已完成 PoC (Proof of Concept) 驗證可行性
- [ ] 已評估技術風險和緩解措施

---

## 🤖 AI 助手執行流程

當你準備開始新 Epic 時，使用以下 Prompt:

### Prompt 模板

```markdown
我準備開始 Epic X 的開發工作。

Epic 資訊:
- **Epic 名稱**: [Epic 9: AI Assistant Integration]
- **預計時間**: [8-12 週]
- **主要目標**: [將 AI 能力整合到專案管理平台]

請幫我:

1. 全面理解 Epic
   - 閱讀 `claudedocs/1-planning/epics/epic-X/` 所有文檔
   - 閱讀 `docs/stories/epic-X/` 所有使用者故事
   - 總結 Epic 目標、範圍、技術挑戰、風險

2. 驗證環境準備
   - 檢查 Git 狀態 (`git status`, `git branch`)
   - 確認開發環境正常 (`pnpm check:env`)
   - 確認最新程式碼 (`git log -1`)

3. 建立 Sprint 計劃
   - 根據 Epic 規劃創建 Sprint 1 計劃
   - 創建 `claudedocs/2-sprints/epic-X/sprint-1/` 文檔
   - 包含: Sprint 目標、任務清單、驗收標準

4. 建立開發分支
   - 創建 Feature Branch: `feature/epic-X-sprint-1`
   - 確保從最新 main 分支創建

5. 創建 TodoWrite 任務清單
   - 根據 Sprint 1 計劃創建詳細任務
   - 標記優先級和依賴關係

6. 生成開始摘要
   - 總結 Epic 關鍵資訊
   - 列出 Sprint 1 主要任務
   - 標註需要注意的風險和挑戰

請用中文完成所有步驟。
```

---

## 🔄 AI 助手執行步驟

### Step 1: 理解 Epic (10 分鐘)

```bash
# 1. 讀取 Epic 規劃文檔
Read: claudedocs/1-planning/epics/epic-X/epic-X-overview.md
Read: claudedocs/1-planning/epics/epic-X/epic-X-requirements.md
Read: claudedocs/1-planning/epics/epic-X/epic-X-architecture.md
Read: claudedocs/1-planning/epics/epic-X/epic-X-risks.md

# 2. 讀取使用者故事
Read: docs/stories/epic-X/story-X.1-*.md
Read: docs/stories/epic-X/story-X.2-*.md
# ... 所有故事

# 3. 讀取主路線圖
Read: claudedocs/1-planning/roadmap/MASTER-ROADMAP.md
```

**輸出**: AI 助手應生成 Epic 摘要:
```markdown
## Epic X 摘要

### 目標
[Epic 主要目標]

### 範圍
- Story X.1: [描述]
- Story X.2: [描述]
- ...

### 技術架構
- 新增套件: packages/X
- 主要技術: [技術棧]
- 外部依賴: [Azure 服務等]

### 關鍵風險
1. [風險 1] - 緩解措施: [...]
2. [風險 2] - 緩解措施: [...]

### 成功指標
- [KPI 1]: 目標值
- [KPI 2]: 目標值
```

---

### Step 2: 驗證環境 (5 分鐘)

```bash
# 1. 檢查 Git 狀態
Bash: git status
Bash: git branch
Bash: git log --oneline -5

# 2. 確認環境正常
Bash: pnpm check:env

# 3. 確認依賴最新
Bash: pnpm install

# 4. 確認 Prisma Client 已生成
Bash: pnpm db:generate
```

**驗證清單**:
- ✅ Git 狀態乾淨 (無未提交變更)
- ✅ 在 main 分支且為最新
- ✅ `pnpm check:env` 通過
- ✅ 依賴已安裝
- ✅ Prisma Client 已生成

---

### Step 3: 建立 Sprint 1 計劃 (15 分鐘)

```bash
# 1. 創建 Sprint 1 目錄
# (目錄應已存在，如不存在則創建)
Bash: mkdir -p claudedocs/2-sprints/epic-X/sprint-1

# 2. 創建 Sprint 計劃文檔
Write: claudedocs/2-sprints/epic-X/sprint-1/sprint-plan.md
```

**Sprint 計劃模板**:
```markdown
# Epic X Sprint 1: [Sprint 主題]

> **時間**: Week 1-2 (2025-11-XX ~ 2025-11-XX)
> **目標**: [Sprint 主要目標]
> **Story**: Story X.1 [故事名稱]

## 🎯 Sprint 目標

- [ ] [主要交付物 1]
- [ ] [主要交付物 2]
- [ ] [主要交付物 3]

## 📋 任務清單

### Backend 任務
1. [ ] 創建 Prisma Schema 擴展
2. [ ] 創建 tRPC Router
3. [ ] 單元測試

### Frontend 任務
1. [ ] 創建 UI 組件
2. [ ] 創建頁面
3. [ ] 整合 tRPC API

### 基礎設施任務
1. [ ] 設定 Azure 服務
2. [ ] 配置環境變數
3. [ ] 更新 CI/CD

## ✅ 驗收標準

- [ ] 所有單元測試通過
- [ ] E2E 測試涵蓋關鍵流程
- [ ] TypeScript 無錯誤
- [ ] ESLint 通過
- [ ] 文檔已更新

## ⚠️ 風險

1. [風險 1] - 緩解: [...]
2. [風險 2] - 緩解: [...]

## 📅 時間線

- **Day 1-2**: [任務]
- **Day 3-5**: [任務]
- **Day 6-8**: [任務]
- **Day 9-10**: [測試 & 文檔]
```

---

### Step 4: 建立開發分支 (2 分鐘)

```bash
# 1. 確保在 main 分支且為最新
Bash: git checkout main
Bash: git pull origin main

# 2. 創建 Feature Branch
Bash: git checkout -b feature/epic-X-sprint-1

# 3. 確認分支創建成功
Bash: git branch
```

**分支命名規範**:
- `feature/epic-X-sprint-Y` - Sprint 開發分支
- `feature/epic-X-story-X.Y` - Story 開發分支
- `fix/epic-X-issue-description` - Bug 修復分支

---

### Step 5: 創建 TodoWrite 任務清單 (5 分鐘)

```bash
# 使用 TodoWrite 工具創建任務清單
TodoWrite: [根據 Sprint 計劃創建詳細任務]
```

**任務範例**:
```json
[
  {
    "content": "閱讀 Epic X 規劃文檔",
    "status": "completed",
    "activeForm": "已完成閱讀 Epic X 規劃文檔"
  },
  {
    "content": "創建 Sprint 1 計劃文檔",
    "status": "completed",
    "activeForm": "已完成創建 Sprint 1 計劃文檔"
  },
  {
    "content": "設定 Azure OpenAI 服務",
    "status": "in_progress",
    "activeForm": "正在設定 Azure OpenAI 服務"
  },
  {
    "content": "創建 packages/ai 套件基礎架構",
    "status": "pending",
    "activeForm": "正在創建 packages/ai 套件"
  },
  {
    "content": "實作 BudgetAI Service",
    "status": "pending",
    "activeForm": "正在實作 BudgetAI Service"
  }
]
```

---

### Step 6: 生成開始摘要 (3 分鐘)

**輸出範例**:

```markdown
# 🚀 Epic X Sprint 1 開始摘要

## 時間
- **日期**: 2025-11-08
- **Sprint**: Sprint 1 (Week 1-2)

## Epic 概覽
- **名稱**: Epic 9: AI Assistant Integration
- **目標**: 將 AI 能力整合到專案管理平台
- **範圍**: 4 個 Story, 5 個 Sprint, 8-12 週
- **預算**: $35/month (Azure OpenAI)

## Sprint 1 目標
- ✅ 設定 AI 服務基礎設施
- ✅ 完成 Azure OpenAI 整合
- ✅ 創建 packages/ai 套件
- ✅ 實作第一個 AI 功能 (預算建議 PoC)

## 主要任務 (本週)
1. [進行中] 設定 Azure OpenAI 服務
2. [待開始] 創建 packages/ai 套件基礎架構
3. [待開始] 實作 BudgetAI Service
4. [待開始] 創建 tRPC Router (aiSuggestion)
5. [待開始] 實作前端 AI 建議組件

## 關鍵風險
⚠️ **風險 1**: AI 建議準確度不足
- 緩解: Beta 測試、信心度閾值、A/B 測試

⚠️ **風險 2**: Azure OpenAI 成本超支
- 緩解: 成本控制、快取策略、Rate Limiting

## 技術架構
- **新增套件**: packages/ai (BudgetAI, ExpenseAI, RiskAI, ReportAI)
- **主要技術**: Azure OpenAI, Azure AI Search, Redis
- **API 設計**: tRPC routers (aiSuggestion, aiAnalysis, aiReport)
- **資料模型**: AIUsageLog, AIFeedback, ProjectRisk

## 下一步行動
1. 完成 Azure OpenAI 服務設定
2. 創建 packages/ai 套件目錄結構
3. 實作 BudgetAI Service 核心邏輯
4. 撰寫單元測試

## 參考文檔
- [Epic 9 概覽](claudedocs/1-planning/epics/epic-9/epic-9-overview.md)
- [Epic 9 架構](claudedocs/1-planning/epics/epic-9/epic-9-architecture.md)
- [Sprint 1 計劃](claudedocs/2-sprints/epic-9/sprint-1/sprint-plan.md)

## Git 狀態
- **Branch**: feature/epic-9-sprint-1
- **Base**: main (最新)
- **Commits**: 0 (新分支)

---

**準備完成！開始 Epic 9 Sprint 1 開發** 🚀
```

---

## ✅ 驗收標準

開始新 Epic 前，應確認:

### 文檔完整性
- [ ] Epic 概覽、需求、架構、風險文檔都存在
- [ ] Sprint 1 計劃文檔已創建
- [ ] TodoWrite 任務清單已建立

### 環境準備
- [ ] Git 狀態乾淨
- [ ] 已創建 Feature Branch
- [ ] `pnpm check:env` 通過
- [ ] 依賴已安裝

### 理解程度
- [ ] 理解 Epic 目標和範圍
- [ ] 理解技術架構和主要技術
- [ ] 理解關鍵風險和緩解措施
- [ ] 理解 Sprint 1 目標和任務

### 計劃完整性
- [ ] Sprint 1 任務清單完整
- [ ] 任務優先級和依賴關係明確
- [ ] 驗收標準清楚定義
- [ ] 時間估算合理

---

## 🔗 相關文檔

- [SITUATION-1: 專案入門](../prompts/SITUATION-1-PROJECT-ONBOARDING.md)
- [SITUATION-2: 開發前準備](../prompts/SITUATION-2-FEATURE-DEV-PREP.md)
- [CONTINUE-DEVELOPMENT Session Guide](./CONTINUE-DEVELOPMENT.md)
- [MASTER-ROADMAP](../../1-planning/roadmap/MASTER-ROADMAP.md)

---

## 📝 備註

### 常見問題

**Q: 如果 Epic 規劃文檔不完整怎麼辦?**
A: 暫停開發，先完成規劃文檔。參考 Epic 9 文檔範例。

**Q: 如果技術研究還不充分怎麼辦?**
A: Sprint 1 應包含技術研究和 PoC 驗證，不要急於實作。

**Q: 如果 Sprint 1 任務太多怎麼辦?**
A: 重新評估範圍，優先 P0 任務，將 P1-P3 任務移至後續 Sprint。

### 成功模式

1. **充分準備**: 花 30-60 分鐘理解 Epic，勝過盲目開發 1 週
2. **明確計劃**: Sprint 計劃越詳細，執行越順暢
3. **風險優先**: 先解決高風險項目 (PoC, 技術驗證)
4. **小步迭代**: Sprint 1 應交付可驗證的 MVP，不求完美

---

**維護者**: AI 助手團隊
**最後更新**: 2025-11-08
**版本**: 1.0
