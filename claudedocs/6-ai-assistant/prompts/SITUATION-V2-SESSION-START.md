# SITUATION V2 — Session Start Prompt（V2 重構期間每個新 session 必用）

> **用法**：在每個新 session 開始時，整份 copy 到對話框，**更新最後一節「今天的任務」一行即可**。其他段落是給 AI 助手的常駐脈絡，不必每次改。
>
> **適用範圍**：Phase 49+（V2 重構期間，預計 22 sprint / 5.5 個月）。完成 V2 後（Phase 56+）再決定是否退役此 prompt。

---

## 第一部分：你正在加入什麼專案

你好。本專案是 **IPA Platform V2**（Intelligent Process Automation Platform），目前正處於 **V2 重構期間**（Phase 49+，2026-04 啟動）。

### V2 為何存在（Why this rebirth）

V1（Phase 1-48）2025-11 至 2026-04 累積了 5 個月的開發，但 2026-04 V9 audit 發現：
- 真實對齊度只有 **27%**（11 範疇中 8 個 Level 0-2 — 不可用 / 半成品）
- Guardrails 散在 6 處、Orchestrator 散在 5 處（cross-directory scattering）
- Pipeline 偽裝成 Loop / 無 PromptBuilder / 無 Verification / Context Rot 完全忽略
- Hybrid 橋接層債務 + Potemkin Features（結構在但無內容）

→ 決策**重新出發**（不修補、不全砍）：保留 V9 分析 / CC 30-wave 研究 / V1 教訓作設計知識，從 Day 1 按 **agent harness 11+1 範疇**重新組織代碼。

### V2 不是什麼（避免常見誤解）

- ❌ **不是「Claude SDK 應用」** — V2 是 LLM Provider 中性的企業 agent 平台
- ❌ **不是「CC 移植」** — 參考 CC 架構但完全 server-side 重新設計
- ❌ **不是「本地工具升級版」** — V2 是企業 server-side，工具是企業 API/服務
- ❌ **不是「修補 V1」** — V1 已封存到 `archived/v1-phase1-48/`（READ-ONLY），不擴充
- ❌ **不是 SaaS-ready**（Phase 55 完成 ≠ SaaS-ready；SaaS Stage 1 在 Phase 56-58）

---

## 第二部分：3 大最高指導原則（不可違反）

詳見 `docs/03-implementation/agent-harness-planning/10-server-side-philosophy.md`。

### 原則 1：Server-Side First
- 部署在企業伺服器；用戶在遠端 browser；多租戶 + zero-trust
- 工具是**企業 API**（D365 / SAP / KB / SharePoint）— 不是本地檔案 read/write
- HITL 是核心，不是邊角

### 原則 2：LLM Provider Neutrality ⭐⭐⭐
- ❌ `agent_harness/**` 任何檔案禁止 `import openai` / `import anthropic` / `import agent_framework`
- ✅ 全走 `adapters/_base/ChatClient` ABC + 中性 ToolSpec / Message / StopReason
- CI 強制 lint 檢查；違反 = PR 直接 revert

### 原則 3：CC 參考但 Server-Side 轉化
- 概念複製、實作重寫
- CC `Bash tool` → 沙盒化 enterprise 命令；CC `Read/Write user files` → 企業 API；CC git checkpoint → DB state_snapshots
- 不照搬 CC 本地實作（multi-tenant 場景會出安全 / 性能問題）

---

## 第三部分：V2 11+1 範疇（架構骨架）

V2 嚴格按以下範疇組織代碼，**禁止跨範疇雜湊**：

| # | 範疇 | Phase 實作 |
|---|------|----------|
| 1 | Orchestrator Loop（TAO/ReAct）| 50.1 |
| 2 | Tool Layer | 51.1 |
| 3 | Memory（5 scope × 3 time scale）| 51.2 |
| 4 | Context Mgmt（Compaction + Prompt Caching）| 52.1 |
| 5 | Prompt Construction | 52.2 |
| 6 | Output Parsing | 50.1 |
| 7 | State Mgmt（Reducer + transient/durable）| 53.1 |
| 8 | Error Handling | 53.2 |
| 9 | Guardrails & Safety（含 Tripwire）| 53.3 + 53.4 |
| 10 | Verification Loops | 54.1 |
| 11 | Subagent Orchestration（4 模式，**無 worktree**）| 54.2 |
| **12** | **Observability / Tracing**（cross-cutting）| 49.4 起滲透所有 |

外加 `§HITL Centralization`（`agent_harness/hitl/`）— 跨範疇 2/7/8/9 的 HITL 統一管理。

完整 spec：`agent-harness-planning/01-eleven-categories-spec.md`。

---

## 第四部分：權威排序（衝突時上位者勝）

```
docs/03-implementation/agent-harness-planning/ (19 份 V2 規劃) > 根目錄 CLAUDE.md > .claude/rules/ > V1 文件
```

**任何衝突以上位者為準**。例如：V2 規劃說 `platform_layer/`，過期 V1 文件說 `platform/` → 用 V2 規劃。

---

## 第五部分：必讀文件（每次新 session 至少讀這 5 份 + 1 份 active reference）

依序讀完才能對齊上下文：

1. **本 prompt**（你正在讀）— 高層 onboarding
2. **`CLAUDE.md`**（專案根目錄，2026-04-28 V2 重寫版）— 高層導航 + V2 11+1 範疇 + 5 大核心約束 + Sprint Workflow
3. **`docs/03-implementation/agent-harness-planning/README.md`** — V2 規劃 19 份文件導覽
4. **`docs/03-implementation/agent-harness-planning/10-server-side-philosophy.md`** — 3 大最高指導原則完整論述
5. **`docs/03-implementation/agent-harness-planning/17-cross-category-interfaces.md`** — Single-source 介面權威表（24 dataclass + 19 ABC + 22 LoopEvent + 9 跨範疇工具）

### 🆕 第 6 份（active during Phase 57.7-57.9，2026-05-08+）

6. **`claudedocs/1-planning/enterprise-saas-gap-analysis-20260508.md`** — 8-sub-agent enterprise SaaS gap audit
   - §0 Executive Summary — V2 對 industry baseline 整體 ~30-40% 結論
   - §1.2 Identity / Auth / Access — 6 Tier 0 blockers（Phase 57.7 Block A scope）
   - §6 Adjusted Roadmap — Phase 57.7 / 57.8 / 57.9 spike 順序與 Day 4 design note extract 對應
   - §5 Buy-vs-Build 9 條決策矩陣（IAM 偏向 Buy，其他 8 條未決）

**何時降級**：Phase 58.0 開始 Tier 1（IaC + DR drill）後，本文件已大部分被 spike-extract design notes（20-iam / 21-compliance / 22-sre）取代，可降為「需要時再讀」（從必讀降為條件性 reference）。降級時記得編輯本 §5 移除此項。

按需要再讀：
- `04-anti-patterns.md`（V1 教訓 11 條反模式 — PR 必通檢查清單）
- `06-phase-roadmap.md`（22 sprint 路線圖）
- `.claude/rules/README.md`（13 份 V2 開發規則索引）
- `claudedocs/templates/spike-design-note-template.md`（spike sprint Day 4 closeout extract 用 template + 8-Point Quality Gate）
- 🆕 **任何 frontend sprint**：`docs/rules-on-demand/frontend-mockup-fidelity.md`（mockup CSS 逐字複製法 — 前端 mockup-fidelity 權威方法；杜絕 Sprint 57.18-57.27 CSS 翻譯 drift）

---

## 第六部分：Rolling Planning Discipline（V2 紀律核心，sprint + doc 雙層）⭐

> **這是 V2 最重要的工作節奏紀律，每次 session 都要記住**

V2 採用「**滾動式 sprint 規劃**」（per `.claude/rules/sprint-workflow.md`）：

### ✅ 正確做法

- **執行當前 sprint 期間（或結束時）**才寫**下一個** sprint 的 plan + checklist
- 每個 sprint 結束 retrospective 後，根據實作學習**微調**下一 sprint 設計
- Phase README + 06-phase-roadmap.md 提供高層綱要，**不是**完整 plan
- 完成 sprint plan + checklist 才開始 code（**禁止跳步**：Phase README → Plan → Checklist → Code → Update → Progress doc → Retrospective）
- 🆕 **起草新 plan/checklist 必先讀「最近一個 completed sprint」樣板**：章節編號 / 命名 / Day 數 / 細節水平必須一致；scope 差異透過**內容**調整（更多 stories / file / tests），**不透過結構**調整（多加章節 / 改 Day 數）。違反 = 用戶矯正成本（前車：52.1 plan/checklist v1 → v3 三輪重寫才對齊 51.2 格式）

### ❌ 禁止做法

- **不**預寫全 22 個 sprint plan + checklist（過早決定 = 將來必返工）
- **不**「為了完整」而把 49.2 / 49.3 / 49.4 plan 一次寫齊（違反 rolling）
- **不**跳過 plan 直接 code（Phase 35-38 + 42 違規前車之鑑）
- **不**刪除未勾選的 checklist 項（只能 `[ ]→[x]`，延後項加 🚧 + reason）
- 🆕 **不**因 gap analysis 結果就一次預寫多份新規劃文件（doc-level 同 sprint-level 反模式；前車：2026-05-08 enterprise SaaS gap analysis §3 一度提議 18-25 共 8 docs，被用戶當場糾正——同 V2 21 docs : 22 sprints 模式）

### 為什麼是 rolling，不是預寫

1. 實作 sprint N 會學到東西，會影響 sprint N+1 的設計
2. 一次預寫 5 個 sprint plan，第 1 個跑完通常要改後 4 個
3. ROI 偏低 + 維護成本高
4. 標準業界做法

→ **每個新 session 開始時，AI 助手必須先確認 rolling planning 紀律仍在執行，沒有突然出現 5 個未來 sprint plan 文件。**

### 🆕 第六-五節：Doc-Level Rolling 紀律（2026-05-08 加入）

V2 §6 sprint-level rolling 已運作 22 sprint。**新領域 doc 也必須 rolling，不預寫**：

#### ✅ 正確順序
識別 gap → 1 個 thin vertical spike sprint（如 IAM Block A：OIDC + RS256 + 1 login endpoint + frontend stub）→ retrospective → 從實作學習 extract 寫 1 份輕量 design note → 之後 sprint 擴充為完整 doc

#### ❌ 禁止順序
識別 gap → 一次寫 8 份新規劃文件（如 18/19/20/21/22/23/24/25）→ 22 個 implementation sprint 跟著跑 → Sprint 57.5 paper-vs-runtime drift 模式重演

#### 為什麼
- V2 dual scoring 已證明 paper 詳細不等於 runtime 落實（code 85% / runtime 40%）
- 預寫 doc 在 1st spike 跑完通常要改 → ROI 偏低 + 維護成本高
- gap analysis（如 `claudedocs/1-planning/enterprise-saas-gap-analysis-20260508.md`）作用是**識別** Top 10 gap 與 Buy-vs-Build 決策，**不是**直接觸發 doc 預寫

#### 實踐範例
2026-05-08 enterprise SaaS gap analysis §3 一度提議「新增 18-25 共 8 docs（拆 14 / 拆 15 / 新增 18-19-22-23-24-25）」，被用戶當場識別為「+50% 規模重演 V2 21 docs : 22 sprints 模式」。正確做法：保留 §3 作 reference index（識別哪些 gap 需要 doc），但 doc 撰寫**順延**至 Tier 0 thin spike 跑完。例如：
- IAM Block A spike（1 sprint）→ retrospective → Day 4 closeout extract IAM design note → 之後 sprint 視真實需要擴充

#### Quality 不是頁數，是 verified ratio
**「輕量」不等於「低品質」**。14.md 800 行 verified ratio 僅 10.6%（91 行 verified / 862 行總）= 高頁數低品質。Spike-extract design note 行數通常 200-500（outcome 非 cap），但 verified ratio ≥ 95%（每行對應實際 file:line / verification command / test fixture）= 中頁數高品質。

每個 spike-extract design note **必須通過 8-Point Quality Gate**（per `claudedocs/templates/spike-design-note-template.md`）：

1. **Section header 對應 spike user story**（不是 generic「OIDC overview」）
2. **每個技術 claim 有 file:line**（不是「we use RS256」而是 `JWTManager.encode()` at `jwt.py:42-58`）
3. **Decision rationale 含比較矩陣**（vendor / approach 三-四欄表 + 否決原因）
4. **Verification command（reproducible）**（`pytest tests/integration/auth/test_oidc_flow.py::test_real_entra_callback`）
5. **Test fixture reference**（link 到實際 test data / mock setup）
6. **Open invariant 明確分界**（「verified in this spike: A,B,C」/「deferred to Phase XX.Y: D,E,F」）
7. **Rollback / fallback 路徑**（若設計後續證明錯，怎麼撤回 + 估時）
8. **Cross-reference 17.md single-source**（任何新 contract 必須在 17.md 對應 §section 登記）

**禁止**：用「regulated 200-300 行」當品質替代品。重點是禁止 speculation 充頁數，不是壓縮 verified content。

→ **每個新 session 開始時，AI 助手必須先確認 doc-level rolling 紀律仍在執行，沒有「為了完整」一次規劃多份新 doc，且每份 design note 通過 8-Point Quality Gate。**

→ **Sprint Day 4 closeout 時，AI 助手必須對 design note 自查 8 條，並在 retrospective.md 記錄通過/未通過項。**

---

## 第七部分：當前進度（AI 自查，不需用戶手動更新）

新 session 開始時，AI 助手請用以下指令自查當前進度：

```bash
# 1. 看現在在哪個 branch
git branch --show-current

# 2. 看 main 最近的 commits（過去 sprint 痕跡）
git log main --oneline -20

# 3. 看當前 branch 的 commits（如果在 feature branch）
git log $(git branch --show-current) --oneline --not main

# 4. 看 working tree 是否乾淨
git status --short

# 5. 看 V2 sprint 規劃文件覆蓋（已寫了哪些 sprint）
ls docs/03-implementation/agent-harness-planning/phase-*

# 6. 看執行紀錄（已執行 / 收尾的 sprint）
ls docs/03-implementation/agent-harness-execution/

# 7. 讀最近收尾的 sprint retrospective（學該 sprint 的 open items + lessons）
# 路徑類似 docs/03-implementation/agent-harness-execution/phase-XX/sprint-XX-Y/retrospective.md
```

**讀完上述後**，AI 助手應該能回答：
- 目前在哪個 sprint？哪一天？
- 上一個收尾的 sprint 是哪個？有什麼 open items？
- 累計完成多少 sprint？離 Phase 55（V2 完成）還有多遠？

---

## 第八部分：常駐 Open Items / Follow-ups

> **權威單一來源** = `claudedocs/1-planning/next-phase-candidates.md`（per `.claude/rules/sprint-workflow.md` §Sprint Closeout — CLAUDE.md + MEMORY.md Update Policy）。
> 本節**只**放「最近收尾 sprint」的一句話狀態指標 + 指向權威來源；**不**再逐 sprint / 逐範疇累積 carryover dump —— 該模式 = REFACTOR-001（2026-05-18）在 CLAUDE.md / MEMORY.md 識別、並由 §Sprint Closeout 政策明令禁止的 bloat。
> 歷史 carryover 完整內容的單一來源 = git history + 各 sprint `retrospective.md` §Carryover + `memory/project_phase*.md` subfile。

### 最近收尾 sprint

- **最新狀態快查**：`git log main --oneline -10` 顯示最近 sprint merge 序列；最近 sprint detail 從 commit subject 即可辨認（feat / fix scope + sprint id）。
- **詳細 detail single-source**：`memory/MEMORY.md`（per-sprint quality pointer index）→ `memory/project_phase*.md`（per-sprint subfile，goal / scope / ratio / drift / carryover ADs 完整紀錄）→ `docs/03-implementation/agent-harness-execution/phase-XX/sprint-XX-Y/retrospective.md`（完整 Q1-Q7 retro）。
- **開放 / pending items**：`claudedocs/1-planning/next-phase-candidates.md`（權威單一來源 — REFACTOR-001 §Sprint Closeout 政策明令禁止本節重建逐 sprint carryover dump）。
- **下一步**：未預寫（rolling planning §6）；下個 sprint 候選方向見上述 `next-phase-candidates.md`。user approve direction 必先。

### AI 助手任務

每個新 sprint 開始時，讀 `next-phase-candidates.md`（權威 open-items 清單）+ 上一個收尾 sprint 的 `retrospective.md` §Carryover，向用戶確認哪些 follow-up 在本 sprint 處理、哪些繼續延後。**不要**在本節重建逐 sprint carryover dump。

---

## 第九部分：常駐 milestones（V2 累計完成 — navigator level）

> **本節單一原則**（per REFACTOR-001 + `.claude/rules/sprint-workflow.md` §Sprint Closeout Policy）：本節只放 Phase-level milestone snapshot。Per-sprint detail（ratio / drift / AD / carryover）**NEVER** 重複在此 — 一律 redirect 到 canonical sources（見下方 redirect 表）。
>
> **Dual scoring 評估** (Sprint 57.6+): Phase 57+ 採 code-level + runtime-level dual scoring，避免 V2 22/22 closure-style "isolated tests pass" 重蹈。

### Phase-level milestone

| Phase | Status | Closed / Latest | Highlight |
|-------|--------|-----------------|-----------|
| **Phase 49-55 V2 Refactor** | ✅ 22/22 (100%) | closed 2026-05-04 (Sprint 55.2) + 6 carryover bundles (53.2.5 / 53.7 / 55.3-55.6) | 11+1 範疇 全 Level 4（Cat 9 L5）+ LLM Provider 中性 (CI-enforced) + Multi-tenant 3 鐵律 |
| **Phase 56 SaaS Stage 1** | ✅ 3/3 (100%) | closed 2026-05-06 (Sprint 56.3) | tenant lifecycle (56.1) + polish bundle (56.2) + SLA Monitor + Cost Ledger (56.3) |
| **Phase 57+ Frontend Mockup-Fidelity Epic** | 🔄 ongoing | latest = Sprint 57.38 + FIX-011 (2026-05-24) | 11/17 Phase-2 routes shipped / 6 🟡 remaining; verbatim-CSS foundation switch closed 10-sprint translation drift |

### Phase 57+ sub-epic 結構（時間序，high-level only）

```
Frontend Foundation (57.13-57.17; auth flow + design-system + telemetry + i18n + a11y + Lighthouse CI)
  → Mockup-Direct-Port Foundation (57.19-57.21; shell V3 grid + chatv2 Turn Block Model)
  → Comprehensive Audit (57.22; 41 routes / 10-sprint roadmap)
  → Strict-Rebuild Epic (57.23-57.27; 5 sprint, 9 widgets reusable primitives)
  → ⭐ Verbatim-CSS Foundation Switch (57.28; closes 10-sprint translation drift ROOT CAUSE)
  → Phase-2 Per-Page Re-Point Epic (57.29-57.37; 11 routes Phase-2 shipped, agent-delegated)
  → Class-Split Decision (57.38; Option 2 applied — `-simple` 0.50 / `-with-extras` 0.65)
  → Sister-bug FIX (FIX-010 + FIX-011; layout-class production-only artifacts)
```

### Redirect 表（detail 真正的 single-source）

| 想看什麼 | 去哪裡 |
|---------|--------|
| Sprint merge SHA + PR # + date | `git log main --oneline -50` |
| Sprint goal / scope / AD / carryover | `memory/MEMORY.md`（per-sprint quality pointer index）+ `memory/project_phase*.md`（subfile）+ `docs/03-implementation/agent-harness-execution/phase-XX/sprint-XX-Y/retrospective.md`（完整 Q1-Q7 retro） |
| Calibration ratio + class trend | `.claude/rules/sprint-workflow.md` §Scope-class multiplier matrix（canonical 16 active classes 全部 per-sprint 資料點 + 3-sprint window decision rule） |
| Open items / next sprint candidates | `claudedocs/1-planning/next-phase-candidates.md`（權威單一來源） |
| Sprint plan + checklist 原始版 | `docs/03-implementation/agent-harness-planning/phase-XX-*/sprint-XX-Y-plan.md` + `-checklist.md` |
| 變更紀錄（FIX / CHANGE / REFACTOR） | `claudedocs/4-changes/{bug-fixes,feature-changes,refactoring}/` |

### Backup 歷史

> 2026-05-24 cleanup 之前的 verbose milestone table（30+ row sprint-by-sprint detail）已 archive 至 `claudedocs/7-archive/SITUATION-V2-SESSION-START-pre-cleanup-20260524.md`，如需查閱完整原始 row 內容請去該檔。本節 cleanup follows REFACTOR-001 + Sprint Closeout Policy navigator-only principle。

---

## 第十部分：行為規範（給 AI 助手）

每次回應前，AI 助手請確保：

### 必做

- [ ] 對齐 3 大最高指導原則（server-side / LLM neutrality / CC reference）
- [ ] 不引入新 LLM SDK 直接 import 進 `agent_harness/**`
- [ ] 不刪除未勾選的 checklist 項（只能 `[ ]→[x]` 或加 🚧）
- [ ] 跨範疇型別從 `agent_harness._contracts/` import（不重複定義）
- [ ] 開始 code 前確認該 sprint 已有 plan + checklist
- [ ] 🆕 **起草新 sprint plan/checklist 前先讀最近 completed sprint 的 plan/checklist 作格式樣板**（非空白白板起草；章節 / Day 數 / 細節水平必須一致；最近樣板 = `phase-53-2-error-handling/sprint-53-2-{plan,checklist}.md` 或 carryover 版 `sprint-53-2-5-{plan,checklist}.md`）
- [ ] 寫 commit message 用 Conventional Commits 格式（per `.claude/rules/git-workflow.md`）+ co-author
- [ ] 每個 commit 對應一個 checklist 項目
- [ ] 維持每天 progress.md 紀錄（estimates vs actual）
- [ ] 🆕 **sprint 結束寫 retrospective.md 用 6 必答格式**（53.2 + 53.2.5 樣板）：
  - Q1 What went well
  - Q2 What didn't go well
  - Q3 What we learned（generalizable lessons）
  - Q4 Audit Debt deferred（明確標 ID + target sprint）
  - Q5 Next steps（rolling planning 下；不寫具體未來 sprint 任務，只寫 carryover 候選）
  - Q6 Solo-dev policy validation（or 其他 sprint-specific 主題）

### 🆕 V2 紀律 9 項自檢（每 PR 前 + 每 commit 後）

per `compact 格式 §3` + `.claude/rules/anti-patterns-checklist.md`：

1. Server-Side First（tenant_id 強制 / no local file IO 假設）
2. LLM Provider Neutrality（agent_harness 零 SDK import）
3. CC Reference 不照搬（CC 概念 → V2 server-side 重寫）
4. 17.md Single-source（dataclass / ABC / 工具不重複定義）
5. 11+1 範疇歸屬（每檔案明確歸 1 範疇）
6. 04 anti-patterns（11 條全綠）
7. Sprint workflow（plan → checklist → code → progress → retro）
8. File header convention
9. Multi-tenant rule

### 🆕 Solo-Dev 政策（2026-05-03 Sprint 53.2 永久結構性變更）

- `required_approving_review_count = 0`（不是 1）
- ✅ PR 仍要開（audit trail + CI gate）
- ✅ enforce_admins=true 仍 active（admin 不能直接 push main）
- ✅ 4 active required CI checks 必須全綠
- ❌ **不需** review approval（GitHub 阻擋 author self-approve；solo dev 無第二 reviewer）
- ❌ **不用** temp-relax bootstrap（PATCH review_count: 1→0 暫降）—— 已永久 0
- 當 2nd collaborator 加入時 1-line PATCH 還原為 1（指令見 `13-deployment-and-devops.md` §gh api command）

### Paths Filter Workaround（docs-only PR）— ⚠️ RETIRED Sprint 55.6

**NO LONGER APPLIES.** Sprint 55.6 removed the `paths` filter from `.github/workflows/backend-ci.yml` (Option Z, closes AD-CI-5) → **every PR runs full backend CI + v2-lints**, including docs-only / `.gitignore`-only PRs. No paths-filter `mergeStateStatus=BLOCKED` situation; **no touch-`backend-ci.yml` workaround needed**. `backend-ci.yml` header is authoritative.

（Residual edge case, NOT paths-filter: a rare GitHub webhook miss/delay — e.g. PR #203, Sprint 57.53 — can leave checks unreported; a header touch re-triggers, but that's a webhook quirk.）

### 不做

- [ ] 不預寫多個未來 sprint plan（rolling planning！）
- [ ] 不刪除 V1 archive 內任何檔案（archived/v1-phase1-48/ 是 read-only baseline）
- [ ] 不讓 AI 助手單方面決定不可逆操作（git tag push / git mv 大量檔案）— 必須先報告
- [ ] 不執行 `--no-verify` / `--force` git 命令（除非用戶明確授權）
- [ ] 不啟動長期運行 server process（CLAUDE.md 規範：節點 process 與 claude code 衝突）
- [ ] 🆕 不寫 `--admin` merge bypass（enforce_admins=true 會擋；solo-dev policy 已用 `review_count=0` 解決） 

---

## 第十一部分：今天的任務（**唯一需要用戶填寫的部分**）

> 在每個新 session 開始時，把整份 prompt copy 後，只改下方這一節即可。

```
今天的任務：__________________

例：
- 「啟動 Sprint 49.2 — DB Schema + Async ORM」
  → AI 將先寫 `phase-49-foundation/sprint-49-2-plan.md` + `sprint-49-2-checklist.md`，等用戶 approve 才開始 code
- 「繼續 Sprint 49.2 Day 3」
  → AI 接續執行 Day 3 任務（先讀 progress.md 確認 Day 1-2 完成情況）
- 「修復 Sprint 49.1 follow-up：rename platform/ in V2 規劃文件」
  → AI 處理 Open Items 中的 `platform/` rename 同步
- 「Review Sprint 49.1 retrospective + 規劃 Sprint 49.2 plan」
  → AI 讀 retrospective.md 後與用戶討論 49.2 範圍 + 寫 plan
- 「建立第 8 個 SITUATION prompt」
  → AI 按用戶需求建立 / 修改 prompt 模板
```

---

## 附錄：本 prompt 自身的維護

### 何時更新

| 觸發 | 更新位置 |
|------|---------|
| Sprint 結束 | 第八部分 Open Items（合併 retrospective Action items）+ 第九部分 milestones（加一行）|
| 發現 V2 規劃修訂（17.md / 02 / 04 / 10 等）| 第三部分（11+1 範疇）+ 第四部分（權威排序）+ 第五部分（必讀清單）|
| Phase 切換（如 Phase 49 → 50）| 第七部分（自查指令）+ 第九部分（milestones）|

### 何時退役

V2 完成（Phase 55 後）→ 此 prompt 變歷史紀念物，改用 V3 / SaaS Stage 1 對應 prompt（如有）。

---

**Last Updated**: 2026-05-10（Sprint 57.12 closeout — **Agent Harness UI Suite + Cat 11 SSE + Cat 3 /api/v1/memory + AD-AdminTenant-Patch-Flake**; PR #127 → main `3e06c48d`; 8/8 USs: LoopVisualizer (chat-v2 inline + /loop-debug standalone — single component 2 contexts) + MemoryViewer (/memory 2-tab Recent/By-Scope over NEW `/api/v1/memory` REST read facade, role+session 501 — Direct ORM not new ABC, D1-007) + SubagentTree (chat-v2 inline, buildForest tree depth-cap 5) + Cat 11 SubagentSpawned/Completed SSE from `DefaultSubagentDispatcher.spawn` (best-effort `_emit_safely`) + AD-AdminTenant-Patch-Flake fix (WORM-trigger-toggle conftest cleanup; root cause: admin PATCH `db.commit()` persists rows past db_session rollback → uq_tenants_code collision; FK CASCADE to audit_log WORM trigger); CONVENTION.md §7 SSE 3-edit applied for subagent; routes.config.ts 11→13 entries (active 7→9); 4 NEW Playwright e2e (6 tests) + chat-v2 regression 10/10; Day 4 lint fixup (Day 1/Day 3 commits had skipped black/flake8 — re-confirms `feedback_pre_push_lint_must_run_flake8.md`); STRETCH real-backend spawn e2e DEFERRED → AD-Subagent-RealShip-E2E; Day 4 closeout ALL GREEN (pytest 1635→1654 / mypy --strict 0/305 / 9 V2 lints 9/9 / Vitest 119→168 / Playwright 31→37 / Vite build main 296.58 kB +1.44 vs 57.11 → AD-Bundle-Size-285kB-Carryover continues / ESLint silent / backend black+isort+flake8 clean / LLM SDK leak 0) + retrospective.md Q1-Q7 (Q7 N/A SKIP — feature ship NOT spike, 5th consecutive 57.8-57.12) + memory snapshot project_phase57_12_agent_harness_ui_suite.md + 3 doc syncs (sprint-workflow.md calibration `large multi-domain` +1 data point 57.12=0.75 → 5-pt mean 0.81 + plan/checklist MHist closeout + 16-frontend-design.md V2 Ship Timeline 7/N→9/N + 3 debug UIs promoted shipped); **calibration `large multi-domain` 0.55 5th application**; bottom-up ~25 hr / committed ~14 hr / actual ~9.5-11.5 hr → ratio **~0.75**; 5-pt mean 0.81 (lower edge [0.85,1.20]); KEEP 0.55 — `When to adjust` lower-trigger (3+ consecutive < 0.7) NOT met (only 57.11=0.47 of last 3); 6 NEW carryover ADs Phase 58+: AD-Subagent-RealShip-E2E + AD-Memory-ABC-ListMethods + AD-Memory-Role-Session-Phase58 + AD-Cat11-Handoff-Events-Phase58+ + AD-Cat11-Completed-ErrorFields + AD-Bundle-Size-285kB-Carryover; partial-closed AD-Cat11-Multiturn / AD-Cat11-ParentCtx (metadata only); **dual scoring** code-level ★★★★★ ~95% / runtime-level ★★★★ ~85% (real auth-gated /loop-debug + /memory + chat-v2 inline panels render+merge live SSE; role+session 501 + real-backend spawn e2e deferred prevents 100%); **V2 22/22 + Phase 56-58 SaaS Stage 1 3/3 unchanged** (Sprint 57.12 advances Phase 57+ Frontend SaaS 7/N → **9/N**); Phase 57.13+ direction per Q5 retro 5 candidates pending user instruct: (a) AD-Bundle-Size optimization ~3-5 hr / (b) Cat 11 deepening ~8-12 hr / (c) Memory read facade completion ~5-7 hr / (d) Tier 1 IaC + DR drill ~15-20 hr / (e) SOC 2 + SBOM ~12-15 hr）

**Previous**: 2026-05-09（Sprint 57.9 closeout — **Governance Real Ship + TanStack Query 4-page Migration**;PR pending squash merge from `feature/sprint-57-9-governance-ship-tquery-migration` 5 commits ahead of main `c5894e96`;6 USs all delivered (US-1 governance auth gate + AppShellV2 + 2-tab Routes / US-2 Tailwind 3 components / US-3 governance TanStack hooks APPROVALS_QUERY_KEY single-source + DecisionModal drop onSubmit prop / US-4 AuditLogViewer real impl + auditService + useAuditLog + 4-field filter form draft-vs-committed / US-5 AuditChainBadge enabled:false manual trigger 4 states / US-6 4-page TanStack migration cost+sla+admin-tenants+tenant-settings + 4 stores reduced UI-only + bonus useTenantSettingsSave mutation hook);Day 4 closeout: full validation sweep all green (pytest 1622 baseline maintained / Vitest 75 → **93** +18 target ≥+8 hit **225%** in 3.65s / Playwright **27/27** in 7.3s — 5 governance auth-gate fixed via seedAuthJwt beforeEach + 4 StrictMode mock fixed via retryClicked flag pattern / tsc strict 0 errors / 9 V2 lints 9/9 in 1.00s / Vite build 240.86 kB main + 1865 modules / Backend flake8 silent + black 300 files clean / LLM SDK leak 0) + retrospective.md Q1-Q7 (Q7 N/A SKIP — feature ship NOT spike per Sprint 57.8 precedent) + memory snapshot project_phase57_9_governance_ship.md + 4 doc syncs (sprint-workflow.md calibration matrix +1 row `frontend-feature-with-migration` 0.50 NEW class + this header + 16-frontend-design.md V2 Ship Timeline 5/N → 6/N + governance promoted to shipped + CLAUDE.md sync deferred to post-merge closeout PR per Sprint 57.7+57.8 pattern);**calibration `frontend-feature-with-migration` 0.50 HYBRID NEW class 1st app** weighted blend (governance ship × 0.55 + 4-page TanStack pattern-reuse × 0.35 + 5 hook tests × 0.65);bottom-up est ~25-30 hr / committed 10.5 hr / actual ~10.5 hr → ratio **1.00 ✅ bullseye in [0.85, 1.20] band**;KEEP 0.50 baseline 1-data-point opens per `When to adjust` 3-sprint window rule;extends AD-Sprint-Plan-10 split proposal (vs 57.8 `frontend-arch-spike` 0.50 over band by 0.30 — pattern-reuse-heavy hits target);**15-sprint cumulative window** in-band 9/15 (60%) — back to 60% threshold after 57.8 dip;16 cumulative D-findings (D-PRE-1 through D-PRE-16 across 5 days);**AD-Cost-Dashboard-UseQuery FULLY CLOSED** via Day 4 4-page batch migration + AD-Front-1 partial close (TanStack refetchInterval replaces manual setInterval);**4 NEW carryover ADs Phase 57.10+**: AD-Governance-RealShip-E2E + AD-AuditLog-Range + AD-AuditLog-OperationDropdown + AD-StrictMode-MockPattern;**dual scoring**: code-level ★★★★★ ~95% (single-source `*_QUERY_KEY_BASE` exports preserved + 17.md cross-ref unchanged + 9 V2 lints green + pytest 1622 + 18 NEW Vitest + tsc strict 0 + Playwright 27/27 + Vite build clean) / runtime-level ★★★★ ~85% (real auth gate governance + AppShellV2 6 routes + JWT consumed all 5 services + chat-v2 + governance + 4 admin pages all wired through fetchWithAuth + TanStack auto-cancellation + invalidation — 4 admin pages cost/sla/admin-tenants/tenant-settings still no auth gate AD-Frontend-AuthUX deferred Phase 58.x prevents 100% runtime score);**V2 22/22 + Phase 56-58 SaaS Stage 1 3/3 unchanged** (Sprint 57.9 advances Phase 57+ Frontend SaaS 5/N → **6/N** — governance now real ship);pattern reuse acceleration Day 2 -17% / Day 3 -33% / Day 4 -50% (governance ship + TanStack pattern internalized);0 design note (feature ship NOT spike per Sprint 57.8 precedent);Phase 57.10+ direction per Q5 retro 5 candidates pending user instruct: (a) verification real ship ~10-12 hr highest pattern-reuse ROI / (b) 5 deferred 16.md pages Phase 58.2+ / (c) SOC 2 + SBOM Block C+D EU CRA 2026 Sep deadline / (d) Status Page + APAC Compliance Block E+F TW/HK / (e) Tier 1 IaC + DR drill production launch readiness）

**Previous**: 2026-05-09（Sprint 57.8 closeout — **AppShell V2 + chat-v2 Real Ship**;PR pending squash merge from `feature/sprint-57-8-appshell-v2-chat-v2-ship` 4 commits ahead of main `51162fd5`;Day 0 Decision Z architecture-first pivot per user feedback;5 USs all delivered (US-1 AppShellV2 + Sidebar + uiStore / US-2 UserMenu auto-inject custom popover no @radix-ui / US-3 routes.config 11-entry single-source registry / US-4 4-page batch migration + Day 0 A1 page-level wrap + B1 AuthShell rename / US-5 chat-v2 page real ship: auth gate Navigate first auth-gated page + AppShellV2 wrap + ChatLayout reuse + chatService fetch→fetchWithAuth + 4 Playwright e2e);pytest 1622 baseline / Vitest 41 → 57 (+16) / Playwright 23 → 27 (+4 chat-v2-ship) / mypy 0/300 / 9 V2 lints / Vite 246.19 kB main + AppShellV2 lazy 34.88 kB;calibration `frontend-arch-spike` 0.50 HYBRID NEW 1st app ratio ~1.50 OVER band by 0.30 → AD-Sprint-Plan-10 propose split greenfield(0.45)/reuse-ship(0.35);13 D-findings;5 NEW carryover ADs (AD-Sprint-Plan-10 + AD-Frontend-h1-Convention + AD-Test-Tenant-Code-Pollution + AD-Plan-3-h1-Grep + AD-Cost-Dashboard-ChildrenTailwind);Phase 57+ Frontend SaaS 4/N → 5/N）

**Previous**: 2026-05-10（Sprint 57.7 closeout — **IAM Foundation + Frontend Foundation 1/N spike**;7 USs all delivered including US-A1 WorkOS chosen + US-A2 OIDC backend + US-A3 DB-backed RBAC + US-B1+B2+B3 frontend foundation + US-R1 sessions+tool_calls observer;design note `20-iam-deep-dive.md` 8-Point Quality Gate ≥95% verified;pytest 1602 → 1622 (+20);Vitest 35 → 41 (+6);calibration `iam-frontend-spike` HYBRID 0.60 ratio ~0.92 ✅ in band lower edge;25 cumulative D-findings;13 NEW carryover ADs Phase 57.8+/58+;V2 22/22 + Phase 56-58 SaaS Stage 1 3/3 unchanged;Phase 57+ Frontend SaaS 3/N → 4/N）
> Previous: 2026-05-08（Sprint 57.6 closeout — **Reality Gap Fix Sprint** + 5 doc updates merged per Decision 4 (b);PR #114 merged main `799ce14e`;5 USs all closed: US-1 entry-point/port drift + US-2 dotenv lifespan + US-3 audit_log observer narrow scope + US-4 16.md V2 Ship Timeline + US-5 NEW V2 lint #9 + E2E real-LLM workflow;**AD-Reality-3 split into 5 sub-ADs** (3-audit_log closed Day 2 + 3a/b/c/d deferred Phase 57.7+);pytest 1598 → 1602 (+4);**8 V2 lints → 9 V2 lints**;calibration `reality-gap-fix` 0.50 NEW class 1st app ratio 0.54 below [0.85, 1.20] band by 0.31 → AD-Sprint-Plan-8 propose pending validation;5 NEW deferred ADs Phase 57.7+ (3a/b/c/d + AD-Plan-5);**dual scoring**: code-level ★★★★★ ~95% / runtime-level ★★★★ ~75%;V2 22/22 + Phase 56-58 SaaS Stage 1 3/3 + Phase 57+ Frontend SaaS 3/N unchanged）
> Previous: 2026-05-07（Sprint 57.5 closeout — **V2 Reality Check & Smoke Test Sprint** non-feature reality verification gate (0 source code change);PR #112 merged main `c1139fcc`;first-of-kind sprint type;pivot from Feature Flags Admin UI Day 0 (renamed deferred candidate);5 USs all closed (US-1 Day 0 三-prong + Path C + US-2 Day 1 backend smoke 20 D-findings + US-3 Day 2 frontend Playwright 7-page 8 NEW D-findings = 28 cumulative + US-4 Day 3 21-doc reality audit + 315-line v2-reality-gap-report.md + US-5 Day 4 closeout retrospective + memory + sync PR);**0 source code change** (pytest 1598 / mypy 0/295 / 8 V2 lints 8/8 / Vitest 35 / Playwright 23 — all unchanged from 57.4 baseline);**dual scoring framework introduced**: code-level ★★★★ ~85% (structure + tests + lints) vs runtime-level ★★ ~40% (7 RED runtime gaps);21-doc audit: 9 strongly aligned + 8 mostly w/ drift + 4 significant gap (10/14/15/16);28 D-findings (7 RED + 13 YELLOW + 8 GREEN);**calibration `reality-check` NEW class 1st app ratio ~1.04 ✅ in band** → AD-Sprint-Plan-7 (NEW) propose 0.85 baseline;Top 5 RED (Phase 57.6+ MUST-FIX-FIRST): R1 entry-point + port drift + R2 .env autoload + R3 chat router DB persist + R4 5 placeholder pages + R5 AP-4 lint extension + E2E real-LLM gate;**10 NEW AD-Reality-N + AD-Sprint-Plan-7** (5 Phase 57.6 + 5 Phase 57.7 scopes);Phase 57.6+ direction per Option D (A+C 組合): Phase 57.6 Reality Gap Fix ~10-15hr + Phase 57.7 Re-baseline ~3-5hr + Phase 57.8+ feature work resumption;5 user decision points pending Day 4.5;**V2 22/22 + Phase 56-58 SaaS Stage 1 3/3 + Phase 57+ Frontend 3/N unchanged** (reality check verification gate, NOT main progress)
> Previous: 2026-05-07（Sprint 57.4 closeout — **Phase 57+ SaaS Frontend 3/N — Admin Tenants Console List Bundle**;PR #110 merged `ca8c43c7`;closes plan-time D1 RED (backend admin tenants.py 缺 GET `""` list endpoint) via Option A pre-emptive bundle;5 USs all closed (US-1 backend list endpoint 9 tests + US-2 admin-tenants infra 7 Vitest + US-3 Table+Filters 5 Vitest + US-4 Pagination+page layout + US-5 App.tsx route + 4 Playwright e2e);pytest 1589 → **1598** (+9 plan target +6 ⏫150%);Vitest 23 → **35** (+12 plan target +6 ⏫200%);Playwright e2e 19 → **23** (+4);Vite build 69 → **75** modules / 203.02 → **209.11** kB;calibration `mixed` 0.60 mid-band 4th app ratio **0.42** under band 0.43;4-data-point window mean **0.79 ⬇️ below band** → AD-Sprint-Plan-6 propose split mixed-greenfield 0.60 vs mixed-pattern-reuse 0.40;3 NEW carryover ADs (AD-Sprint-Plan-6 / AD-AdminTenants-URL-QuerySync / AD-AdminTenants-DebouncedSearch);8 D-findings;2 CI fix commits (D14 black + D15 flake8 E501 MHist trim);**Day 0 三-prong second fully-applied sprint** ROI ≈ 16-24×;V2 22/22 + Phase 56-58 SaaS Stage 1 3/3 unchanged + **Phase 57+ Frontend SaaS 2/N → 3/N** ↑;Phase 57.5 candidates 待 user approve per rolling planning 紀律
> Previous: 2026-05-07（Sprint 57.3 closeout — **Phase 57+ SaaS Frontend 2/N — Tenant Settings Bundle**;PR #108 merged `5c893e5b`;closes Day 0 D1 RED finding (backend admin tenants.py 缺 GET/PUT/PATCH for tenant entity → user-confirmed Option B pivot bundle backend + frontend);5 USs all closed (US-1 GET 6 tests + US-2 PATCH+audit chain 9 tests + US-3 frontend infra + US-4 View+EditForm + US-5 routing + 4 Playwright e2e);pytest 1574 → **1589** (+15 cumulative;plan target +10 ⏫150%);mypy 0/295 source files unchanged;8 V2 lints 8/8 green;LLM SDK leak 0;Vitest 15 → **23** (+8 cumulative;plan target +6 ⏫133%);Playwright e2e 11 → **15** (+4);Vite build 63 → **69** modules (+6 wire-up) / 196.55 → **203.02** kB;calibration `mixed` 0.60 mid-band **3rd application** ratio **0.57** under [0.85, 1.20] band lower edge by 0.28;3-data-point `mixed` window 53.7=1.01 + 56.2=1.17 + 57.3=0.57 = mean **0.92 ✅** in band → KEEP 0.60 mid-band per AD-Sprint-Plan-4 matrix discipline;**14-sprint cumulative window 8/14 (57%) in-band** slipped below 60% threshold for first time after 3 consecutive sprints in-band;13 D-findings cumulative (1 🔴 RED + 8 🟢 GREEN + 4 🟠 YELLOW);1 CI fix commit (Day 4 D14 flake8 E501 file header lines 3/5/49);**Day 0 三-prong first fully-applied sprint** (Path 8 checks 0 drift + Content 7 checks 1 RED + 5 GREEN + 2 YELLOW + Schema N/A);ROI ≈ 12-18× (40 min cost prevented 8-12 hr 57.1 v1-style abort rework);D1 RED finding fully closed (backend admin tenants.py R+U complete);V2 22/22 + Phase 56-58 SaaS Stage 1 3/3 unchanged + **Phase 57+ Frontend SaaS 1/N → 2/N** ↑;Phase 57.x next-sprint candidates (10 candidates per Q5 retrospective) 待 user approve per rolling planning 紀律
> Previous: 2026-05-06（Sprint 56.3 closeout — 🎉 **Phase 56-58 SaaS Stage 1 3/3 ✅ CLOSURE** — SLA Monitor + Cost Ledger 聯合 merged;5 USs closed (SLAMetricRecorder Cat 12 + SLAReportGenerator monthly + CostLedger ORM/aggregate/PricingLoader yaml + chat router LLM/tool auto-record hooks + closeout);Alembic 0016 (3 tables + 3 RLS);pytest 1530 → **1557** (+27 cumulative = 108% of plan target +25);mypy 0/293 source files;8 V2 lints 8/8 (含 check_rls_policies 0 gaps);LLM SDK leak 0;calibration `large multi-domain` 0.55 mid-band 2nd application ratio **1.04 ✅** in [0.85, 1.20] band by 0.16;`large multi-domain` 2-data-point mean **1.02** ✅ → KEEP 0.55;**11-sprint window 7/11 (64%) in-band** sustained above 60% threshold for 2nd consecutive sprint;8 Day-0 兩-prong 探勘 D-findings;**AD-Plan-4-Schema-Grep PROMOTED to validated rule** (3rd data point evidence — 56.3 D6 sessions.total_cost_usd Day-0 catch saved ~1 hr; fold-in pending as Prong 3 Schema Verify in §Step 2.5);3 NEW Phase 56.x carryover ADs (AD-Cost-Ledger-Token-Split + AD-Cost-Ledger-Provider-Attribution + AD-Cat10-Cat11-LoopMetricsAccumulator);Phase 57+ candidate scope pending user approval per rolling planning 紀律（候選:Citus PoC standalone worktree / DR + WAL streaming / Compliance partial GDPR / SLA monthly cron / Frontend Onboarding Wizard / Cost+SLA dashboards / SaaS Stage 2 Stripe + Status Page）
**Maintainer**: 用戶 + AI 助手共同維護
**File location**: `claudedocs/6-ai-assistant/prompts/SITUATION-V2-SESSION-START.md`

---

## Update history

| Date | Sprint | Updates |
|------|------|------|
| 2026-04-29 | 49.1 | 初版（V2 重構期間 onboarding prompt） |
| 2026-04-30 | 52.1 | 新增 §6 「format consistency rule」（52.1 v1→v3 incident 教訓） |
| 2026-05-03 | 53.2.5 | §8 全更新（Cat 8 + CI carryover + AI-22 + #31）；§9 milestones 補 49.1 → 53.2.5 共 16 個 sprint 行；§10 加 6 必答 retrospective 格式 + V2 紀律 9 項自檢 + Solo-dev policy + Paths filter workaround |
| 2026-05-04 | 54.1 | §8 closes AD-Cat9-1+2+3 + adds AD-Cat10-Obs-1 / AD-Cat10-Wire-1 / AD-Cat9-1-WireDetectors / AD-Test-Module-Naming as 54.1 carryover; §9 milestones row +Sprint 54.1 (V2 18/22 → 19/22 = 86%); session start time updated to 54.1 closeout |
| 2026-05-04 | 54.2 | §8 closes AD-Cat10-Obs-1 + adds AD-Cat10-Obs-Cat9Wrappers / AD-Cat11-Multiturn / AD-Cat11-SSEEvents / AD-Cat11-ParentCtx / AD-Sprint-Plan-2 / AD-Cat12-Helpers-1 / AD-Lint-3 as 54.2 carryover; §9 milestones row +Sprint 54.2 (V2 19/22 → 20/22 = 91%); Phase 54 完成 2/2; session start time updated to 54.2 closeout |
| 2026-05-04 | 55.1 | §9 milestones row +Sprint 55.1 (V2 20/22 → 21/22 = 95%); Phase 55 progresses 1/2; new AD logged: AD-Sprint-Plan-3 (multiplier 0.50→0.40 for 55.2; 4-sprint mean 0.76 BELOW band) + AD-BusinessDomainPartialSwap-1 (full register_*_tools mode swap for 4 deferred domains); session start time updated to 55.1 closeout |
| 2026-05-04 | **55.2** | **🎉 V2 22/22 (100%) CLOSURE**; §9 milestones row +Sprint 55.2; AD-BusinessDomainPartialSwap-1 closed at 3 layers (per-domain + aggregator + chat router); AD-Sprint-Plan-3 conditionally closed (0.40 first hit ratio 1.10 in band; 5-sprint mean 0.826); 2 new AD for Phase 56+ (AD-Phase56-Calibration + AD-Cat12-BusinessObs); session start time updated to 55.2 closeout |
| 2026-05-04 | **55.3** | §8 closes 6 ADs (AD-Plan-1 + AD-Lint-2 + AD-Lint-3 + AD-Cat12-Helpers-1 + AD-Cat7-1 + AD-Hitl-7) + supersedes AD-Sprint-Plan-2 + AD-Phase56-Calibration via new AD-Sprint-Plan-4 (scope-class multiplier matrix); §9 milestones row +Sprint 55.3 (V2 22/22 unchanged — audit cycle bundle); 2 new AD logged: AD-Sprint-Plan-4 (matrix) + AD-Plan-2 (Day-0 path verify); pytest +18 (1416 → 1434); 7th V2 lint check_sole_mutator added; calibration ratio 2.81 way over band evidence drives matrix proposal |
| 2026-05-05 | **55.4** | §8 closes 4 ADs (AD-Cat8-1 + AD-Cat8-3 narrow + AD-Cat9-5 + AD-Cat9-6); AD-Cat8-2 deferred to 55.5 per D6 + Selection D; §9 milestones row +Sprint 55.4 (V2 22/22 unchanged — audit cycle bundle); 3 new AD logged: AD-Sprint-Plan-5 (medium-backend mult 0.65→0.75) + AD-Plan-3 (Day-0 content grep) + AD-Test-DB-Trigger (SAVEPOINT pattern); pytest +12 (1434 → 1446); calibration ratio 1.36 over band → mult lift recommendation; 10 drifts D1-D10; AD-Plan-2 first self-application 0 path drifts (ROI validated) but D5 reveals AD-Plan-2 doesn't catch wrong-content drifts |
| 2026-05-05 | **55.5** | §8 closes 2 ADs (AD-Cat10-Wire-1 + AD-Cat10-Obs-Cat9Wrappers) + validates AD-Sprint-Plan-5 (medium-backend mult 0.80 1st refinement ratio 1.14 ✅ in band) + validates AD-Plan-3 (5 wrong-content drifts caught — D1+D2+D4+D5+D7; ROI 4-8× ~55min cost prevents ~3-4hr rework); §9 milestones row +Sprint 55.5 (V2 22/22 unchanged — audit cycle bundle); 3 new AD logged: AD-Plan-3-Promotion (integrate Day-0 content grep permanently into sprint-workflow.md §Step 2.5) + AD-Lint-MHist-Verbosity (trim default verbosity; 2 consec sprints exceeded E501) + AD-Cat10-Wire-1-Production (operational rollout, no sprint binding); pytest +8 (1446 → 1454, 33% over target +6); 9 drifts D1-D9; Option E (3-mode → 2-mode post-D4+D5) preserved 17.md §Cat 10 single-source; AST-walk sentinel pattern (D8 response) reusable for invariant tests; 7-sprint window 3/7 in-band — KEEP 0.80 for next 2-3 medium-backend sprints |
| 2026-05-05 | **55.6** | §8 closes 5 ADs in clean closure (AD-Cat8-2 Option H + AD-CI-5 Option Z + AD-CI-6 + AD-Plan-3-Promotion + AD-Lint-MHist-Verbosity); §9 milestones row +Sprint 55.6 (V2 22/22 unchanged — audit cycle bundle); **Phase 55 audit cycle COMPLETE backend/infra closure** (Groups A+B+C+D+H all closed across 55.3-55.6); AD-Plan-3 status: candidate → **validated rule** promoted (sprint-workflow.md §Step 2.5 two-prong model + 5-row drift class table + ROI evidence); pytest +9 (1454 → 1463, 12.5% over target +8); 11 drifts D1-D11 (D3 critical scope reduction Cat8-2 ~10-12 hr → ~5-6 hr; D9 backoff_ms units fix; D10 soft-failure path retry fix); 2 plan revisions via separate commits per AD-Plan-1 audit-trail (Day 1 morning Option H; Day 3 morning Option Z); calibration multiplier 0.85 medium-backend 2nd application ratio **0.92 ✅** in [0.85, 1.20] band by 0.07 → 8-sprint window 4/8 (50%) in-band; medium-backend 2-data-point mean 1.03; 0 new ADs logged; **Phase 56+ direction pending user approval** per rolling planning 紀律 |
| 2026-05-06 | **56.1** | §9 milestones row +Sprint 56.1 — **🚀 Phase 56+ SaaS Stage 1 1st of 3** ; 5 USs all closed (US-1 tenant lifecycle + US-2 plan template + US-3 onboarding API + US-4 feature flags + US-5 RLS hardening); pytest +45 (1463 → 1508, 122% of plan target +37); 8th V2 lint check_rls_policies (0 gaps; V2 baseline complete); calibration `large multi-domain` 0.55 mid-band 1st application ratio **1.00 ✅ bullseye**; 9-sprint window 5/9 in-band (first crossing 50%); 28 D-findings cumulative (D26+D27 column-level drift caught at first test run; D28 RLS audit reveals 0 gaps so §4.3 Alembic migration not needed); 3 Phase 56.x carryover ADs (AD-AdminAuth-1 RBAC stub replacement / AD-QuotaEstimation-1 Cat 4 token counter / AD-QuotaPostCall-1 LLMResponded reconciliation); 1 process AD candidate (AD-Plan-4-Schema-Grep); 2 CI fix commits during PR (isort `--profile black` order + EmailStr → regex pattern to avoid email-validator dep); V2 22/22 unchanged + **Phase 56-58 SaaS Stage 1 progress 0/3 → 1/3** ↑ ; Sprint 56.2 candidate scope pending user approval per rolling planning 紀律 |
| 2026-05-06 | **56.2** | §8 closes 4 Phase 56.x ADs from 56.1 (AD-Cat12-BusinessObs / AD-QuotaEstimation-1 / AD-QuotaPostCall-1 / AD-AdminAuth-1); §9 milestones row +Sprint 56.2 — **🚀 Phase 56+ SaaS Stage 1 2nd of 3 — Polish Bundle**; 12 D-findings cumulative (10 Day 0 + D11 pytest module-name collision + D12 record_usage already exists at 56.1 quota.py L138-159 — net scope -1.4 hr); 5 NEW test files + 1 NEW source file (tracer.py factory) + 6 MODIFIED source files; pytest +22 (1508 → 1530, 129% of plan target +17); calibration `mixed` 0.60 mid-band 2nd application ratio **1.17 ✅** in [0.85, 1.20] band by 0.03; mixed 2-data-point mean **1.09** → KEEP 0.60 mid-band per AD-Sprint-Plan-4 matrix; **10-sprint window 6/10 in-band** first crossing 60% threshold; 0 CI fix commits required (Option Z paths-filter retired stable across 8 sprints); AD-Plan-4-Schema-Grep evaluation deferred again to 56.3 retro for 3rd data point per 1-sprint evidence rule; 2 NEW Phase 56.3 carryover (Cat 4 ChatClient.count_tokens precision + helper-method LoopCompleted total_tokens propagation); V2 22/22 unchanged + **Phase 56-58 SaaS Stage 1 progress 1/3 → 2/3** ↑ ; Sprint 56.3 candidate scope pending user approval per rolling planning 紀律 (候選: SLA Monitor + Cost Ledger / Citus PoC standalone worktree / Compliance partial GDPR) |
| 2026-05-06 | **56.3** | §8 closes AD-Plan-4-Schema-Grep (PROMOTED to validated rule via 3rd data point evidence — 56.3 D6 sessions.total_cost_usd Day-0 catch saved ~1 hr; fold-in pending as Prong 3 Schema Verify in §Step 2.5); §9 milestones row +Sprint 56.3 — 🎉 **Phase 56-58 SaaS Stage 1 3/3 ✅ CLOSURE** SLA Monitor + Cost Ledger 聯合; 5 USs all closed (US-1 SLAMetricRecorder Cat 12 + US-2 SLAReportGenerator monthly + US-3 CostLedger ORM/aggregate/PricingLoader yaml + US-4 chat router LLM/tool auto-record hooks D2 single-entry simplification + D4 reuse ToolCallExecuted saves 1 hr + US-5 closeout); Alembic 0016 (3 tables + 3 RLS + 6 indexes); pytest +27 (1530 → 1557, 108% of plan target +25); mypy --strict 0/293 source files (was 284, +9 NEW); 8 V2 lints 8/8 green (含 check_rls_policies 0 gaps on 3 new tables); LLM SDK leak 0; calibration `large multi-domain` 0.55 mid-band 2nd application ratio **1.04 ✅** in [0.85, 1.20] band by 0.16; large multi-domain 2-data-point mean **1.02** ✅ → KEEP 0.55 mid-band per AD-Sprint-Plan-4 matrix; **11-sprint window 7/11 (64%) in-band** sustained above 60% threshold for 2nd consecutive sprint; 1 CI fix commit (Linux mypy `Returning Any` cross-platform — explicit `float()` cast in _get_p99); 8 Day-0 兩-prong 探勘 D-findings catalogued (D6 critical Schema-Grep 3rd-data-point ROI evidence); 9 NEW source files + 4 MODIFIED + 9 NEW test files = 25+ tests across 9 test files; **AD-Plan-4-Schema-Grep PROMOTED to validated rule** + 3 NEW Phase 56.x carryover ADs (AD-Cost-Ledger-Token-Split + AD-Cost-Ledger-Provider-Attribution + AD-Cat10-Cat11-LoopMetricsAccumulator); V2 22/22 unchanged + 🎉 **Phase 56-58 SaaS Stage 1 progress 2/3 → 3/3 ✅ CLOSURE** ; Phase 57+ candidate scope pending user approval per rolling planning 紀律 (候選: Citus PoC standalone worktree / DR + WAL streaming / Compliance partial GDPR / SLA monthly cron / Frontend Onboarding Wizard / Cost+SLA dashboards / SaaS Stage 2 Stripe + Status Page) |
| 2026-05-07 | **57.4** | §8 closes plan-time D1 RED (backend admin tenants.py 缺 GET `""` list endpoint → user-approved Option A pre-emptive bundle 2026-05-07); §9 milestones row +Sprint 57.4 — **Phase 57+ SaaS Frontend 3/N — Admin Tenants Console List Bundle**; 5 USs all closed (US-1 backend list endpoint 9 tests + US-2 admin-tenants infra 7 Vitest + US-3 Table+Filters 5 Vitest + US-4 Pagination+page layout + US-5 App.tsx route + 4 Playwright e2e); pytest +9 (1589→1598, 150% of plan target +6); mypy --strict 0/295 unchanged; 8 V2 lints 8/8 green; LLM SDK leak 0; Vitest +12 (23→35, 200% of plan target +6); Playwright e2e +4 (19→23); Vite build 69→75 modules (+6 wire-up) / 203.02→209.11 kB (+6.09 kB); calibration `mixed` 0.60 mid-band 4th app ratio **0.42** under [0.85, 1.20] band lower edge by 0.43; 4-data-point `mixed` window 53.7=1.01 + 56.2=1.17 + 57.3=0.57 + 57.4=0.42 = mean **0.79 ⬇️ below band**; 15-sprint window 8/15 (53%) further dropped below 60% threshold for second consecutive sprint after 57.3 first dip; 8 D-findings (1 🔴 RED + 5 🟢 GREEN + 2 🟠 YELLOW); 2 CI fix commits (D14 black 2 files + D15 flake8 E501 MHist trim per AD-Lint-MHist-Verbosity); **Day 0 三-prong second fully-applied sprint** Path+Content+Schema(N/A) ROI ≈ 16-24×; **3 NEW carryover ADs**: AD-Sprint-Plan-6 (split mixed into mixed-greenfield 0.60 vs mixed-pattern-reuse 0.40 per pattern reuse acceleration evidence) + AD-AdminTenants-URL-QuerySync (deferred per AP-6 to Phase 57.x or 58) + AD-AdminTenants-DebouncedSearch (deferred per AP-6 to Phase 58+ when tenant count > 500); V2 22/22 + Phase 56-58 SaaS Stage 1 3/3 unchanged + **Phase 57+ Frontend SaaS 2/N → 3/N** ↑; Phase 57.5 candidates pending user approve |
| 2026-05-07 | **57.3** | §8 closes D1 RED finding (backend admin tenants.py 缺 GET/PUT/PATCH for tenant entity → user-confirmed Option B pivot bundle backend + frontend 2026-05-07); §9 milestones row +Sprint 57.3 — **Phase 57+ SaaS Frontend 2/N — Tenant Settings Bundle**; 5 USs all closed (US-1 Backend GET 6 tests + US-2 Backend PATCH+audit chain 9 tests + US-3 Frontend infra 5 Vitest + US-4 View+EditForm 3 Vitest + US-5 routing + 4 Playwright e2e); pytest +15 (1574 → 1589, plan target +10 ⏫150%); mypy --strict 0/295 source files unchanged (modify existing tenants.py only); 8 V2 lints 8/8 green; LLM SDK leak 0; Vitest +8 (15 → 23, plan target +6 ⏫133%); Playwright e2e +4 (11 → 15); Vite build 63 → 69 modules (+6 wire-up) / 196.55 → 203.02 kB; calibration `mixed` 0.60 mid-band **3rd application** ratio **0.57** under [0.85, 1.20] band lower edge by 0.28; 3-data-point `mixed` window 53.7=1.01 + 56.2=1.17 + 57.3=0.57 = mean **0.92 ✅** in band → KEEP 0.60 mid-band per AD-Sprint-Plan-4 matrix discipline; **14-sprint cumulative window 8/14 (57%) in-band** slipped below 60% threshold for first time after 3 consecutive sprints in-band; 13 D-findings cumulative (1 🔴 RED + 8 🟢 GREEN + 4 🟠 YELLOW); 1 CI fix commit (Day 4 D14 flake8 E501 file header lines 3/5/49); **Day 0 三-prong first fully-applied sprint** (Path 8 checks 0 drift + Content 7 checks 1 RED + 5 GREEN + 2 YELLOW + Schema N/A); ROI ≈ 12-18× (40 min cost prevented 8-12 hr 57.1 v1-style abort rework); D1 RED finding fully closed (backend admin tenants.py R+U complete); V2 22/22 + Phase 56-58 SaaS Stage 1 3/3 unchanged + **Phase 57+ Frontend SaaS 1/N → 2/N** ↑; Phase 57.x next-sprint candidates (10 candidates per Q5 retrospective: Admin tenant console list view / Onboarding self-serve wizard 需 backend self-serve API / Feature flags admin UI / Audit log frontend view / DR + WAL streaming / Compliance partial GDPR / SaaS Stage 2 Stripe + 月結 + Status Page / AD-Cat10-VisualVerifier+Frontend-Panel / AD-Cat11-Multiturn+SSEEvents+ParentCtx / AD-CI-6 Phase 58) 待 user approve per rolling planning 紀律 |
| 2026-05-22 | **57.28** | §8 精簡重寫（per `.claude/rules/sprint-workflow.md` §Sprint Closeout policy）— 改為「`next-phase-candidates.md` 權威指針 + 最近收尾 sprint 一句話狀態」結構；移除停在 Sprint 57.21 的逐 sprint／逐範疇 carryover dump（~52 KB）；歷史內容單一來源 = git history + 各 sprint retrospective.md + memory subfile |
| 2026-05-29 | **57.62 f/u** | §10 §Paths Filter Workaround 標記 **RETIRED Sprint 55.6**（paths filter 已移除 → docs-only PR 跑 full CI；移除誤導性 touch-backend-ci.yml 指令；保留 webhook-miss residual edge case 註記）。同型 stale-doc cleanup 跟在 graphify 去除之後 |
