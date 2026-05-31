# Claude Workflow Kit — 製作與移植教學

**Purpose**: 把本項目（ai-semantic-kernel-framework）驗證過的「sprint 紀律 + CI gate + 規則載入 + 變更紀錄」流程，抽成可移植到**任何新項目**的通用模版。
**Created**: 自動帶入（見 init 腳本）
**Status**: Active

---

## 0. 這個 kit 是什麼

`templates/claude-workflow-kit/` 是一個**自包含模版**，分三部分：

| 部分 | 路徑 | 用途 |
|------|------|------|
| **可注入內容** | `kit/` | 會被複製到目標項目的所有檔案（規則、CI、PR 模版、lint 框架、claudedocs 骨架） |
| **bootstrap 腳本** | `init-workflow.ps1` | 互動式問答 → 變數替換 → 注入到目標 repo |
| **本教學** | `TEMPLATE-GUIDE.md` | 你現在讀的這份 |

設計原則：**只帶方法論層，丟掉內容層**（見下方 §2 分類表）。

---

## 1. 快速開始（3 步）

```powershell
# 1. 進到 kit 目錄
cd C:\Users\Chris\Downloads\ai-semantic-kernel-framework-project\templates\claude-workflow-kit

# 2. 跑 bootstrap（互動式；缺的參數會問你）
.\init-workflow.ps1 -TargetPath "C:\path\to\new-project"

# 3. 進新項目，commit 初始流程骨架
cd C:\path\to\new-project
git add .claude .github scripts claudedocs CLAUDE.md docs
git commit -m "chore(workflow): bootstrap sprint workflow kit"
```

完成後新項目立即擁有：5 步 sprint 流程、CI gate、PR 自檢模版、Hybrid 規則載入、FIX/CHANGE/REFACTOR 變更紀錄、claudedocs 骨架。

---

## 2. 核心觀念：兩層切開（移植成敗關鍵）

本項目流程之所以耐用，是「方法論層」疊在「內容層」上。模版化 = **帶走骨架、丟掉血肉**。

| 分類 | 代表檔案 | 處理方式 |
|------|---------|---------|
| **A. 直接攜帶**（通用方法論） | `sprint-workflow.md` 5 步骨架、`file-header-convention.md`、`rules/README.md` Hybrid 載入、`PULL_REQUEST_TEMPLATE.md`、`run_all.py` lint wrapper、`claudedocs/` 變更慣例、`settings.json` SessionStart hook | kit 已通用化，照用 |
| **B. 參數化**（保留結構、換內容） | `CLAUDE.md`、`ci.yml` 的實際命令、`anti-patterns-checklist.md` 的條目 | bootstrap 用 placeholder 自動換；條目自己補 |
| **C. 丟棄**（原項目專屬） | 11+1 範疇、LLM provider neutrality、multi-tenant 三鐵律、calibration agent_factor 矩陣、`check_llm_sdk_leak` / `check_rls_policies` | **不放進 kit**；需要時才針對新項目自寫 |

> 為什麼要丟 C：原項目的 calibration 比率矩陣是「該團隊累積 50+ sprint 的歷史數據」，搬到新項目是錯的基準。新項目應從 `multiplier 0.6` 預設重新累積。

---

## 3. Placeholder 對照表

bootstrap 腳本會把下列 token 全文替換。手動客製時也照這張表：

| Token | 意義 | 範例值 |
|-------|------|--------|
| `{{PROJECT_NAME}}` | 項目名稱 | `my-saas-app` |
| `{{PROJECT_DESC}}` | 一句話描述 | `A multi-tenant billing platform` |
| `{{PRIMARY_LANGUAGE}}` | 主語言 | `TypeScript` / `Python` / `Go` |
| `{{FORMAT_CMD}}` | 格式化命令 | `prettier --write .` / `black .` |
| `{{LINT_CMD}}` | lint 命令 | `npm run lint` / `flake8 src` |
| `{{TYPECHECK_CMD}}` | 型別檢查 | `tsc --noEmit` / `mypy src --strict` |
| `{{TEST_CMD}}` | 測試命令 | `npm test` / `pytest` |
| `{{DEFAULT_BRANCH}}` | 主分支 | `main` |
| `{{DATE}}` | 注入日期 | `2026-05-31` |

---

## 4. 注入後你要做的客製（10 分鐘）

1. **`CLAUDE.md`** — 填 Mission / 技術棧 / 核心約束（取代原項目的 11+1 範疇）。
2. **`anti-patterns-checklist.md`** — `§Project-Specific` 區塊補新項目自己的教訓（一開始可留空，每次踩坑加一條）。
3. **`docs/rules-on-demand/`** — 把新項目真正需要的情境式規則放這（資料庫慣例、API 風格…）；通用 4 條已在 `.claude/rules/`。
4. **`.github/workflows/ci.yml`** — 確認 toolchain 命令對；若無前端可刪 frontend job。
5. **`scripts/lint/run_all.py`** — 預設只有框架；要加新項目專屬 AST 檢查時，照 `_example_detector` 模式寫。
6. **分支保護** — 到 GitHub Settings → Branches，把 CI job 名加進 required status checks（本項目經驗：solo dev 設 `review_count=0` + `enforce_admins=true`）。

---

## 5. 回流同步紀律（重要）

模版會持續演進。維持**單向同步**：

- ✅ 通用改進（5 步流程優化、新增通用 lint 框架）→ 改在 `templates/claude-workflow-kit/kit/`，再 re-inject 到各項目。
- ❌ 各項目的專屬內容（calibration、domain 規則）**不回流**到 kit。
- 每次 re-inject 前先 `git diff`，避免覆蓋目標項目已客製的 `CLAUDE.md` / `anti-patterns` 條目（bootstrap 對既有檔預設**不覆蓋**，需 `-Force`）。

---

## 6. 進階：升級成 GitHub template repo

若要 `gh repo create new --template`：

```powershell
# 把 kit/ 內容推到一個新 repo（注意：保留 placeholder 不替換）
gh repo create my-org/claude-workflow-template --private
# 在該 repo Settings → 勾 "Template repository"
# 新項目： gh repo create new-proj --template my-org/claude-workflow-template
#         然後仍需跑一次 placeholder 替換（可把 init-workflow.ps1 也放進 template repo）
```

starter-kit（本方案）vs template repo 取捨：starter-kit 適合「我在本機跨多項目注入」；template repo 適合「團隊/組織共用、雲端一鍵」。兩者可並存。

---

## 附錄：kit 檔案清單

```
kit/
├── CLAUDE.md                          # 參數化項目導航
├── .claude/
│   ├── settings.json                  # SessionStart hook + plugins 佔位
│   └── rules/
│       ├── README.md                  # Hybrid 載入策略（通用化）
│       ├── sprint-workflow.md         # 5 步流程（通用精簡版）
│       ├── file-header-convention.md  # 檔頭 + MHist 規範
│       └── anti-patterns-checklist.md # PR 自檢骨架 + 6 條通用反模式
├── .github/
│   ├── PULL_REQUEST_TEMPLATE.md       # PR 自檢模版（參數化）
│   └── workflows/
│       └── ci.yml                     # CI gate 結構（參數化）
├── scripts/lint/
│   ├── run_all.py                     # 一站式 lint wrapper 框架
│   └── _example_detector.py           # 自寫 AST 檢查範本
├── docs/rules-on-demand/
│   └── README.md                      # on-demand 規則放置說明
└── claudedocs/
    ├── README.md
    ├── 1-planning/.gitkeep
    ├── 4-changes/{bug-fixes,feature-changes,refactoring}/.gitkeep
    └── templates/
        ├── sprint-plan-template.md
        ├── sprint-checklist-template.md
        ├── FIX-template.md
        ├── CHANGE-template.md
        └── REFACTOR-template.md
```
