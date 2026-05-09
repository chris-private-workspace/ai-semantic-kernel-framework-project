# `.claude/rules/` 索引

**Purpose**: V2 開發規則總覽 + on-demand 載入指南。所有規則對齐 `docs/03-implementation/agent-harness-planning/` 21 份權威文件。

**Last Updated**: 2026-05-09（Hybrid context-load 重構：4 critical always-loaded + 10 on-demand）
**Status**: Active

---

## 載入策略（Hybrid，2026-05-09 起）

為控制 session context 用量，本目錄分兩層：

| 位置 | 行為 | 用途 |
|------|------|------|
| **`.claude/rules/*.md`**（頂層 4 條 + 本 README）| ✅ Claude Code 自動載入每個 session | 高頻 critical 規則 |
| **`.claude/rules/on-demand/*.md`**（10 條）| ⏸️ 預設不載入，需 AI 主動 `Read` | 情境式規則 |

**Why Hybrid**: 全載入成本 ~50KB context；全 on-demand 風險 AI 漏掉 sprint workflow / MHist / tenant 鐵律。Hybrid 保留 4 條最高 ROI critical 規則永遠載入（~15KB），其餘 ~35KB 改 on-demand。

---

## 🔴 Always-Loaded（4 條 critical，永遠在 context）

| 檔案 | 用途 | 為何 always |
|------|------|------------|
| [`sprint-workflow.md`](./sprint-workflow.md) | Plan → Checklist → Code → Update → Progress 5 步流程 + Day 0 三-prong + calibration matrix | 每個 sprint 起始必依；流程不能 lint |
| [`file-header-convention.md`](./file-header-convention.md) | File header + Modification History（1-line max + char budget）| 53.x 連續 3 sprint MHist 超 E501 反例驗證重要性 |
| [`multi-tenant-data.md`](./multi-tenant-data.md) | DB tenant_id 三鐵律 + RLS + GDPR / PII | 每個業務 endpoint 都要對；CI lint 部分覆蓋 |
| [`anti-patterns-checklist.md`](./anti-patterns-checklist.md) | 11 條 PR 自檢清單（V1 教訓）| 每個 PR merge 前必通；CI lint 只覆蓋 AP-1+2+4 |

---

## 📋 On-Demand（10 條，需要時主動 Read）

> **AI 規則**：碰到下列「Trigger」時，**先 Read 對應規則檔再開始 code**。

### 路徑：`.claude/rules/on-demand/`

| 檔案 | Trigger（什麼時候 Read）|
|------|------------------------|
| [`category-boundaries.md`](./on-demand/category-boundaries.md) | 新建檔案 / 跨範疇 import / 不確定代碼歸哪個 11+1 範疇 |
| [`llm-provider-neutrality.md`](./on-demand/llm-provider-neutrality.md) | 碰 `agent_harness/` 任何 LLM 呼叫 / 新增 adapter / 換 model |
| [`adapters-layer.md`](./on-demand/adapters-layer.md) | 修改 `adapters/` / 新增 LLM provider（5 步 SOP） |
| [`observability-instrumentation.md`](./on-demand/observability-instrumentation.md) | 新增埋點 / 動 Cat 12 cross-cutting / TraceContext |
| [`code-quality.md`](./on-demand/code-quality.md) | 修 mypy strict 報錯 / 跨平台 mypy `unused-ignore` 問題 |
| [`testing.md`](./on-demand/testing.md) | 寫 contract test / multi-tenant test / 範疇測試規劃 |
| [`git-workflow.md`](./on-demand/git-workflow.md) | 寫 commit message / 開新 branch（scope 對應 11+1 範疇）|
| [`backend-python.md`](./on-demand/backend-python.md) | 純 Python backend 通用約定（少用，多被 code-quality 取代）|
| [`frontend-react.md`](./on-demand/frontend-react.md) | 純 React/TypeScript 通用約定 |
| [`graphify-usage.md`](./on-demand/graphify-usage.md) | 用 graphify-out/ 加速理解 codebase |

---

## 任務情境快查（哪些 rule 該配對）

### 開始一個 sprint
- ✅ Always: `sprint-workflow.md`（Day 0 三-prong + calibration）
- 📋 Read: `on-demand/category-boundaries.md`（確認代碼歸屬）

### 寫新檔案
- ✅ Always: `file-header-convention.md`（header + MHist）
- 📋 Read: `on-demand/category-boundaries.md`

### 寫新業務 endpoint
- ✅ Always: `multi-tenant-data.md`（tenant_id 鐵律）
- 📋 Read: `on-demand/observability-instrumentation.md`（埋點）+ `on-demand/testing.md`（multi-tenant test）

### 動 LLM 呼叫 / Adapter
- 📋 Read: `on-demand/llm-provider-neutrality.md` + `on-demand/adapters-layer.md`

### Code review / PR 自檢
- ✅ Always: `anti-patterns-checklist.md`（11 條）
- 📋 Read: `on-demand/git-workflow.md`（commit format）

### 修 CI lint / 跨平台 mypy
- 📋 Read: `on-demand/code-quality.md`

---

## 與 V2 規劃文件的對應關係

`.claude/rules/` 是**操作層規則**，內容必須對齐 `docs/03-implementation/agent-harness-planning/` 的**設計層規範**。

| Rule | 對應 V2 文件 |
|------|-------------|
| sprint-workflow.md | CLAUDE.md §Sprint Execution Workflow / 06-phase-roadmap.md |
| file-header-convention.md | CLAUDE.md §File Header & Modification Convention |
| multi-tenant-data.md | 09-db-schema-design.md / 14-security-deep-dive.md / 10.md §原則 1 |
| anti-patterns-checklist.md | 04-anti-patterns.md |
| on-demand/category-boundaries.md | 01-eleven-categories-spec.md / 02-architecture-design.md / 17-cross-category-interfaces.md |
| on-demand/llm-provider-neutrality.md | 10-server-side-philosophy.md §原則 2 / 17.md §Contract 2 |
| on-demand/adapters-layer.md | 07-tech-stack-decisions.md / 17.md §Contract 2 |
| on-demand/observability-instrumentation.md | 01-eleven-categories-spec.md §範疇 12 / 17.md §Contract 12 |
| on-demand/code-quality.md | 11-test-strategy.md |
| on-demand/testing.md | 11-test-strategy.md / 04-anti-patterns.md |
| on-demand/git-workflow.md | CLAUDE.md §Code Standards |
| on-demand/graphify-usage.md | CLAUDE.md §graphify（純本地工具）|

> **權威排序**：V2 規劃文件（21 份）> 本目錄規則 > 既有代碼。衝突以上位者為準。

---

## 維護

- 每次 V2 規劃文件更新（特別是 17.md / 04.md / 10.md），需檢查對應 rule 是否同步
- Rule 改動 = 開發習慣改動 → PR 標題加 `chore(rules)` 並通知所有開發者
- 新 rule 必須走 `sprint-workflow.md` 標準流程（plan + checklist）
- 舊 rule 淘汰時走 `archive` scope，不直接刪除（保留 git history）
- **Always-loaded vs on-demand 分流調整**：若發現某 on-demand rule 在 3 個連續 sprint 都被 Read，應提案 promote 到 always-loaded（反之亦然）

---

## 已淘汰的規則

| 舊 Rule | 淘汰原因 | 替代 |
|--------|--------|------|
| `agent-framework.md` | V1 MAF 已封存（Sprint 49.1） | `on-demand/adapters-layer.md` |
| `azure-openai-api.md` | 內容拆分到 ABC 設計 + Azure 細節 | `on-demand/adapters-layer.md` §Azure OpenAI 特定細節 |

---

## Modification History

- 2026-05-09: Hybrid 重構（4 critical always-loaded + 10 on-demand 移至 `on-demand/`）。Context 節省 ~35KB／session。
- 2026-04-28: V2 Phase 49+ 重寫
