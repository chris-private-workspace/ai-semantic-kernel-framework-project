# REFACTOR-005: sprint-workflow.md Calibration-History Extraction

**Date**: 2026-05-31
**Type**: Refactoring (docs/rules hygiene)
**Scope**: `.claude/rules/sprint-workflow.md`（always-loaded critical rule 之一）
**Status**: ✅ Completed (2026-05-31; executed after user approval)
**Related**: REFACTOR-001（CLAUDE.md/MEMORY.md bloat audit — 同一反模式，不同宿主檔）

---

## Problem

`sprint-workflow.md` = 1045 行 / **89.9k tokens**（~86 tokens/行，正常 markdown 的 6-8 倍），是 always-loaded 4 條 critical rule 之一，**每個 session 開場強制載入**，單檔吃掉約 9% context window、佔 memory files 的 55%。

根因：57+ sprint 的**逐 sprint 校準歷史敘述**累積在三個區塊。與 REFACTOR-001 在 CLAUDE.md 修過的 bloat 是同一個病——§Sprint Closeout 政策把校準 ratio 導流進此檔，卻沒設每 data point 字數上限。

## Root Cause

校準歷史**本來就 single-source 重複**在各 sprint 的 `retrospective.md` + `memory/project_phase*.md`。把它累積進 always-loaded 規則檔 = single-source 違規 + context 浪費。修正方向：**規則 + active 決策表留在規則檔；逐 sprint 審計敘述搬到非 always-loaded log**。

---

## Line Map（要搬 / 留 / 重寫）

| 行段 | 內容 | 動作 |
|------|------|------|
| L1-10 | File header | **KEEP** |
| **L11-39** | 頂部 Modification History blockquote（~29 條 per-sprint retro 巨型條目）| **MOVE → log §3**；留 initial creation + ≤4 條結構性里程碑 + pointer |
| L43-73 | Overview + Step 1 | **KEEP** |
| L74-97 | §Workload Calibration（3-segment + When-to-adjust 規則）| **KEEP** |
| L98-118 | §Four-segment form（agent_factor 規則 + mandatory field）| **KEEP** |
| L119-122 | §Scope-class matrix intro | **KEEP** |
| **L123-152** | matrix 表格（每 class 一行，Status cell 內逐 data-point 巨型敘述）| **REWRITE LEAN** — 每 class 留 1 行：`class \| multiplier \| 3-sprint mean \| 1-line KEEP/adjust status`；data-point 敘述搬 log §1 |
| **L153-197** | matrix 內嵌 Modification History 清單（~42 條 sprint 條目）| **MOVE → log §1** |
| L198-202 | §Active Agent Delegation header + Status + Hypothesis | **KEEP**（Hypothesis 壓成 1 行）|
| **L204-215** | Activation evidence 5-data-point 表 | **MOVE → log §2** |
| L216-234 | **Formula**（agent_factor tier-4 sub-class 表）| **KEEP 表格 + baselines**；每個 sub-class 內嵌的逐 sprint evidence 壓成 1-phrase rationale，evidence 搬 log §2 |
| L235 | When agent-delegated applies | **KEEP** |
| **L237-247** | Equivalent ratios + deprecated 0.55 history | **MOVE → log §2** |
| L248-268 | Rollback rule + Escalation + Tracking discipline（active 規則）| **KEEP** |
| L269 | First validation sprint | **MOVE → log §2** |
| **L271-308** | **Activation history**（Sprint 57.42→57.62 逐 sprint 巨型段落）| **MOVE → log §2** |
| L309-311 | Why this matters + Note on baseline lift | **CONDENSE** 1-2 行 KEEP，detail 搬 log §2 |
| L312-1045 | Step 2 / 2.5 / 3-5 / Sprint Closeout / Risk Classes / Change Records | **KEEP**（規則本身）|

**核心搬移目標**（tokens 最大、最乾淨）：L11-39 + L123-197 + L204-215 + L237-247 + L269-311。
**留在規則檔的決策資訊不缺**：active multiplier 表 + agent_factor tier-4 表 + when-to-adjust / rollback / tracking 規則 → 下個 sprint plan §Workload 照樣查得到。

**OUT of scope（本次不動）**：Step 2.5 §ROI evidence（L473+）內的 per-sprint promotion 證據表——較小且兼具規則範例價值，列為可選 phase 2，保持本次改動 surgical。

---

## New File Structure

`docs/03-implementation/agent-harness-execution/calibration-log.md`（非 `.claude/` 樹下 → Claude Code 不 auto-load）

```
# Calibration Log（sprint-workflow.md 校準歷史 single-source）
Header: Purpose / Category / Created / Status
> Active 決策表權威來源仍是 .claude/rules/sprint-workflow.md §Scope-class matrix + §agent_factor 表；
> 本檔只放「逐 sprint 審計敘述」（回溯用），不放 active 規則。

## §1 Scope-class Multiplier — per-class data-point history
   （從 matrix Status cell + 內嵌 MHist 搬入；每 class 完整 data point 序列 + 決策理由）

## §2 Agent_factor — activation/validation history
   （5-data-point evidence 表 + tier-4 split 演進 + Sprint 57.42→57.62 逐 sprint 段落 + deprecated baselines）

## §3 sprint-workflow.md change log
   （頂部 MHist 搬入的 per-sprint 條目）
```

---

## Doc-Sync Touchpoints（single-source 一致性）

1. **sprint-workflow.md**：matrix 段 + agent-delegation 段各加 1 行 pointer「Full per-sprint history → `calibration-log.md`」；新增 1 條 MHist（本 refactor）
2. **sprint-workflow.md §Sprint Closeout redirect 表**（L694-806 內）：`Calibration ratio` 列改為「active table → sprint-workflow.md §matrix；full history → calibration-log.md」
3. **`claudedocs/6-ai-assistant/prompts/SITUATION-V2-SESSION-START.md` §9 redirect 表**：同上 calibration 列更新
4. **`.claude/rules/README.md`**：V2 文件對應表加 calibration-log.md 一列（optional，低優先）

---

## Validation

- 重量測：`wc -l` + /context 估算 → 目標 sprint-workflow.md **89.9k → ~22-25k tokens**
- 無規則文字遺失：diff KEEP 區段（Step 1-5 / 2.5 / Closeout / Risk / Change Records 逐字不變）
- 無資料遺失：log 檔涵蓋全部搬出條目（grep 抽樣比對 sprint id 數量）
- Lint：9 條 V2 lint 只掃 backend code，**不掃 .md**（N/A）；無 markdown CI gate
- git history：move = 內容可溯（原檔 git blame 保留）

## Rollback

單一 `chore(rules)` PR；內容為「搬移 + 瘦身」非銷毀 → `git revert` 即還原。風險低。

## Calibration（本 chore 自身）

- Scope class：`audit-cycle / docs / template` 0.40（純 markdown hygiene，無 code）
- Agent-delegated：**no**（內容搬移屬精細手術，parent-assistant-direct）→ agent_factor 1.0（3-segment form）
- 非 sprint，屬 chore（同 graphify / paths-filter cleanup 模式）；不需 full plan/checklist/retrospective，本 REFACTOR-005 即記錄

---

## Execution Steps（approval 後）

1. 新建 `calibration-log.md`，把 L11-39 + L123-197 + L204-215 + L237-247 + L269-311 的搬移內容寫入 §1/§2/§3
2. 編輯 sprint-workflow.md：rewrite-lean matrix 表 + agent-delegation 段；插 pointer 行；更新 redirect 表；新增 MHist
3. 更新 SITUATION §9 redirect 表（+ README 可選）
4. 重量測 + diff 驗證 KEEP 區段無損
5. `git checkout -b chore/extract-sprint-workflow-calibration-log` → commit → push → PR（solo-dev review_count=0）

---

## Result (2026-05-31)

**Method**: log built via `sed -n` verbatim extraction (lossless, no transcription); source trimmed via pattern-anchored `sed` deletes (4 history blocks + verbose matrix table) + 6 targeted `Edit`s (lean matrix table, trimmed MHist + REFACTOR-005 entry + §3 pointer, agent-deleg §2 pointer, Last Modified, dangling-ref fix).

**sprint-workflow.md**: 1045 → **925 lines**, 74478 chars (was 89.9k tokens per /context). diff = 39 insertions / 159 deletions (net −120 lines, all the densest per-sprint narration). Est. token drop ~90k → ~21-25k (≈6% of session window reclaimed at every start).

**New file**: `docs/03-implementation/agent-harness-execution/calibration-log.md` (249 lines, 130584 chars) — §1 scope-class history + §2 agent_factor history + §3 sprint-workflow change log, all verbatim.

**Functionality preserved (verified)**:
- Rule anchors intact (1 each): Formula tier-4 table (all 7 baselines), Rollback rule, Escalation, Tracking discipline, When-applies, §Workload Calibration §When-to-adjust.
- Downstream sections intact (1 each): Step 2 / 2.5 / 3 / 4 / 5, Sprint Closeout, Common Risk Classes, Change Record Conventions.
- Lean active matrix = 25 class rows (multiplier + 3-sprint mean + 1-line status).
- agent-deleg section reads coherently header → pointer → Status → Hypothesis → Formula → When → Rollback → Escalation → Tracking → Step 2.

**Doc-sync**: 3 pointers in sprint-workflow.md (matrix §1 / agent-deleg §2 / MHist §3) + SITUATION §9 redirect row. README intentionally NOT touched (always-loaded; discoverability already covered by the 4 pointers).

**Lint**: N/A — 9 V2 lints scan backend code only, not `.md`; no markdown CI gate.

**Files**: M `.claude/rules/sprint-workflow.md` / M `SITUATION-V2-SESSION-START.md` / A `calibration-log.md` / A this record.
