# REFACTOR-001: CLAUDE.md + MEMORY.md Bloat Audit

**Date**: 2026-05-18
**Scope**: Session-start context window optimization
**Trigger**: User flagged ~19% context window consumed at session start; system warned MEMORY.md 28 KB > 24.4 KB limit
**Status**: Step 1/4 — Audit only (no execution yet)

---

## Executive Summary

| File | Current | Projected after cleanup | Reduction |
|------|---------|-------------------------|-----------|
| **CLAUDE.md** | 640 lines / **77 KB** | ~280-320 lines / ~30-35 KB | **~45 KB / ~58%** |
| **MEMORY.md** | 114 lines / **28 KB** (over limit) | ~95-100 lines / ~14-16 KB | **~13 KB / ~46%** |
| **Combined** | ~105 KB | ~45-50 KB | **~55-60 KB ≈ 9-12% session context** |

**Findings**: ~58 KB of CLAUDE.md content + ~13 KB of MEMORY.md content is **duplicate of memory subfile + retrospective.md authoritative sources**. Cleanup is safe (single-source preserved).

---

## A. CLAUDE.md Audit (640 lines / 77 KB)

### A.1 🔴 V2 Refactor Status Table (Lines 68-81, ~14 KB)

The table has 11 rows; bloat concentrated in 6 sprint-detail cells + 1 candidate-list cell.

| Row | Lines | Approx size | Type | Subfile exists? | Recommendation |
|-----|-------|-------------|------|-----------------|----------------|
| `Phase` | 70 | ~200 char | OK | n/a | Keep |
| **`Latest Sprint` (57.21)** | 71 | ~3000 char | 🔴 Verbose duplicate | ✅ `memory/project_phase57_21_*.md` + retrospective | Compress to 5-8 lines (goal + ratio + key carryover) + link |
| **`Prev Sprint` (57.20)** | 72 | ~4000 char | 🔴 Verbose duplicate | ✅ `memory/project_phase57_20_*.md` | Compress to 1-line (id + date + 1-sentence goal) + link |
| **`Prev-Prev Sprint` (57.19)** | 73 | ~3500 char | 🔴 Verbose duplicate | ✅ `memory/project_phase57_19_*.md` | Compress to 1-line + link |
| **`Prev-Prev-Prev Sprint` (57.18)** | 74 | ~3000 char | 🔴 Verbose duplicate | ✅ `memory/project_phase57_18_*.md` | Compress to 1-line + link |
| **`Prev⁴ Sprint` (57.17)** | 75 | ~2500 char | 🔴 Verbose duplicate + ⚠️ duplicate row label | ✅ `memory/project_phase57_17_*.md` | Compress to 1-line + link |
| **`Prev⁴ Sprint` (57.16)** | 76 | ~2000 char | 🔴 Verbose duplicate + ⚠️ duplicate row label | ✅ `memory/project_phase57_16_*.md` | Compress to 1-line + link |
| `Last Convention Codify Sprint` (57.10) | 77 | ~300 char | OK-ish | ✅ subfile | Keep or merge to single "older sprints" line |
| `main HEAD` | 79 | ~300 char | Mildly verbose | n/a | Trim PR/visual-baseline detail; keep SHA + date |
| **`Next Phase 候選`** | 80 | ~3500 char | 🟡 Operationally useful but bloated | n/a | Compress to 5-8 top candidates with 1-line each; archive 20-condition bullet list to `claudedocs/1-planning/next-phase-candidates.md` |
| `Roadmap` | 81 | ~500 char | OK-ish | n/a | Keep but drop per-sprint suffix list (already in §Phase row) |
| `Tech Stack` / `Architecture` / `Branch Protection` | 82-84 | ~200 char each | OK | n/a | Keep |

**Total bloat in table**: ~18 KB of duplicate sprint detail; projected after compress: ~3-4 KB.

### A.2 🔴 `Last Updated` Footer (Lines ~580-640, ~15 KB)

Multi-paragraph blocks packing 6 sprints (57.21 + 57.20 + 57.19 + 57.18 + 57.17 + 57.16) of full retro detail.

**Status**: **Pure duplicate** of A.1 table cells AND memory subfiles. Triple-source for same data.

**Sub-blocks identified**:
- **`Last Updated` paragraph**: ~5-6 KB packed sprint highlights → compress to single line `**Last Updated**: YYYY-MM-DD (Sprint XX.YY — short goal); see V2 Refactor Status table for current state.`
- **`Recent Sprints (詳情見 memory/)` block**: ~3 KB — self-aware ("詳情見 memory/") yet still has 100-300 chars per sprint → compress to pure 1-line list of last 5 sprints with memory file links; older sprints archive to `claudedocs/7-archive/sprint-history-index.md`
- **`Project Start` / `Current Phase`** block: ~6 KB containing nested `[Sprint 57.18 historical row preserved below...]` + 57.17 + 57.16 blocks → **archive entirely** to `claudedocs/7-archive/`

### A.3 🟢 Sections to KEEP (Untouched)

Important navigation / discipline / principles — high value per byte at session start:

| Lines | Section | Why keep |
|-------|---------|----------|
| 1-21 | Intro + ⚠️ 最關鍵閱讀順序 | Navigation entry point |
| 22-35 | AI Assistant Notes | Server startup commands (Windows-specific) |
| 36-67 | Core Vision & Design Philosophy | Mission + 10 design principles |
| 88-101 | V2 不是修補 / V2 完成≠SaaS-ready | Critical scope statement |
| 102-124 | V2 11+1 範疇 | Architectural backbone |
| 125-149 | V2 五大核心約束 | Hard rules |
| 150-192 | **Frontend Mockup-Fidelity Hard Constraint** | Recent (2026-05-17) critical rule |
| 194-212 | Check Existing Before Building | Anti-pattern protection |
| 213-240 | V2 規劃文件導航（21 份） | Doc navigator |
| 241-255 | V1 歷史資產 | Reference table |
| 256-345 | Development Commands / Code Standards / Env Setup | Dev workflow |
| 356-407 | ClaudeDocs sections | Workflow conventions |
| 408-431 | Developer Preferences | Behavior rules (incl. tool-result-is-not-turn-boundary) |
| 432-460 | Karpathy Coding Guidelines | LLM coding discipline |
| 461-520 | File Header & Modification Convention | MHist + 三層級 |
| 521-570 | CRITICAL: Sprint Execution Workflow | 5-step flow |
| 571+ | Important Notes / graphify / V1 Backup | Reference |

**Estimated KEEP size**: ~32-35 KB (40-45% of current 77 KB).

---

## B. MEMORY.md Audit (114 lines / 28 KB; system warned at 24.4 KB limit)

MEMORY.md opens with explicit rule: **「每行 ≤ 200 字符。詳情寫在子檔案，這裡只放 one-line hook。」** Yet entries 57.13-57.21 all violate.

### B.1 🔴 Section "Project — Recent Sprints (Phase 57+)" Violations

| Entry | Current char | x over 200 rule | Subfile? | Recommendation |
|-------|--------------|----------------|----------|----------------|
| **57.21** | ~400 | **2x** | ✅ exists | Trim to ~180-200 char (id + date + 1-sentence goal + 1 key metric) |
| **57.20** | ~450 | **2.25x** | ✅ | Trim to ~180-200 char |
| **57.19** | ~500 | **2.5x** | ✅ | Trim to ~180-200 char |
| **57.18** | ~1500 | **7.5x** 🔴 | ✅ | Trim to ~180-200 char |
| **57.17** | ~3000 | **15x** 🔴🔴 | ✅ | Trim to ~180-200 char |
| **57.16** | ~2900 | **14.5x** 🔴🔴 | ✅ | Trim to ~180-200 char |
| **57.15** | ~2700 | **13.5x** 🔴🔴 | ✅ | Trim to ~180-200 char |
| **57.14** | ~700 | **3.5x** | ✅ | Trim to ~180-200 char |
| **57.13** | ~500 | **2.5x** | ✅ | Trim to ~180-200 char |
| **57.12** | ~300 | **1.5x** | ✅ | Trim to ~180-200 char |
| **57.11** | ~250 | **1.25x** | ✅ | Minor trim |
| 57.10 and earlier | ~150-200 | compliant ✅ | ✅ | No action |

**All 12 violating entries have authoritative subfile** at `memory/project_phase57_XX_*.md` — safe to trim index without information loss.

### B.2 🟢 Sections OK (Compliant or close to compliant)

- `Project — V2 Closure & Audit (Phase 49-56)`: 23 entries, ~150 char each — compliant
- `Project — Background / Foundational`: ~18 entries, ~100-200 char each — compliant
- `Feedback`: 13 entries, mostly compliant; first 3 entries have rationale block (~200-300 char) — borderline OK
- Top headers / footers — compliant

---

## C. Cross-Reference Validation (Single-Source Already Exists)

All bloated content has authoritative source elsewhere:

| Source | Location | Authority |
|--------|----------|-----------|
| **Memory subfile** | `memory/project_phase57_XX_*.md` per sprint | Index-level summary; safe to expand |
| **Sprint retrospective** | `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-XX/retrospective.md` | 🔴 **Authoritative** — full Q1-Q7 retro |
| **Sprint plan** | `docs/03-implementation/agent-harness-planning/phase-57-*/sprint-57-XX-plan.md` | §Workload calibration + §Risks |
| **Git log + commit messages** | `git log feature/sprint-57-XX-*` | Commit-by-commit ground truth |
| **PR descriptions** | `gh pr view <number>` | Sprint-level summary |
| **`calibration matrix`** | `.claude/rules/sprint-workflow.md` §Scope-class multiplier matrix | Cross-sprint ratio tracking |

**Conclusion**: 0 information loss if we trim CLAUDE.md / MEMORY.md to navigator-only role.

---

## D. Estimated Savings

```
Before:
  CLAUDE.md      77 KB
  MEMORY.md      28 KB
  Combined     ~105 KB    (~19% session-start context window)

After cleanup:
  CLAUDE.md    ~32 KB     (-45 KB, -58%)
  MEMORY.md    ~15 KB     (-13 KB, -46%)
  Combined    ~47 KB      (~8-10% session-start context window)

Savings: ~58 KB ≈ 9-11% context window per session
```

---

## E. Archive Target (New File to Create at Step 3)

Proposed destination for content moved out of CLAUDE.md / MEMORY.md:

| New file | Content moved from |
|----------|--------------------|
| `claudedocs/7-archive/sprint-history-index.md` | CLAUDE.md `[Sprint 57.XX historical row preserved]` blocks + `Recent Sprints (詳情見 memory/)` older entries (>3 sprints back) |
| `claudedocs/1-planning/next-phase-candidates.md` | CLAUDE.md V2 Refactor Status `Next Phase 候選` 20-bullet list (currently inline) |

Both targets are pure navigators back to authoritative sources (memory subfiles / retrospective.md). No new authoritative content created.

---

## F. Step 1 Deliverable Checklist

- [x] Audited CLAUDE.md 640 lines → identified 6 verbose table cells + footer + historical blocks
- [x] Audited MEMORY.md 114 lines → identified 12 entries violating ≤200 char rule
- [x] Cross-checked all bloated content has single-source elsewhere (memory subfile / retrospective)
- [x] Estimated savings: ~55-60 KB ≈ 9-12% context window
- [x] Identified KEEP sections (40-45% of CLAUDE.md is high-value navigator content)
- [x] Identified new archive targets

---

## G. Next Steps (Pending User Approval)

| Step | Action | Touches | Estimated effort |
|------|--------|---------|------------------|
| **Step 2** | Add archive-cutoff discipline to `.claude/rules/sprint-workflow.md` | sprint-workflow.md only | ~30 min |
| **Step 3** | Change closeout SOP: trim CLAUDE.md table + MEMORY.md entries to navigator-only; move detail to archive files | CLAUDE.md / MEMORY.md / 2 new archive files | ~60-90 min |
| ~~Step 4~~ | ~~Lint enforce~~ | Deferred per user 2026-05-18 |

---

## H. Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| AI session 需要 trimmed detail 時無 immediate context | Medium-Low | Trimmed lines link to memory subfile / retrospective; Read = 1 tool call. Affects <10% sessions per pre-audit estimate. |
| 用戶 query "Sprint 57.15 做了什麼?" | Low | Same as above; 1-line summary in MEMORY.md gives high-level; subfile read gives detail |
| 失去 calibration trend visibility | Low | `.claude/rules/sprint-workflow.md` §Scope-class multiplier matrix already tracks cross-sprint ratios — that's the authoritative source |
| Carryover ADs visibility loss | Medium | Mitigation: preserve carryover AD list in compressed sprint table cells (1-line per AD with status); detail stays in subfile |

---

## I. 🆕 Philosophy Clarification (user alignment 2026-05-18)

User refined the cleanup principle — **本質不是字數，是文件角色**：

### I.1 CLAUDE.md = Navigator / Principle / Rule（不是開發記錄場所）

**只應保留**:
- Principles（Mission / Core Vision / Design Philosophy — timeless statements）
- Architectural spec（11+1 範疇 / 5 大約束 / Frontend Mockup-Fidelity Hard Constraint）
- Rules / Conventions（File Header / Sprint Workflow / Karpathy / Developer Preferences）
- Navigator（V2 規劃文件導航 21 份 / ClaudeDocs 結構 / V1 歷史資產 reference table）
- Dev workflow reference（commands / env setup / code standards pointer）

**必須移出 CLAUDE.md**（這些都是 development records / time-bound / pending items，AI 需要時才查）:
- ❌ 「最近幾個 sprint 做了什麼」detail — **開發記錄**，去 memory subfile / retrospective.md
- ❌ `main HEAD` SHA + PR # workaround note — **point-in-time record**，git status 即可
- ❌ `Next Phase 候選` 20-bullet list — **pending issues / open items**，去 planning 文件
- ❌ `Last Updated` 多段 sprint history — **development records**
- ❌ `Recent Sprints (詳情見 memory/)` block — 自打嘴巴，自己說「詳情見 memory/」卻又塞詳情
- ❌ `[Sprint XX historical row preserved]` blocks — **archived records**

### I.2 MEMORY.md = Quality Pointer Index（字數不是硬規則，內容質量才是）

**重點不是 ≤200 char 硬性限制，是「pointer 的 quality」**：
- 每 entry 應該回答：「**這個 topic 是什麼 + 關鍵字 + 子檔路徑**」
- **NOT** 回答「這個 sprint 完整做了什麼 + Q1-Q7 retro + calibration ratio + 所有 carryover」
- AI 助手 / 開發者要能 **「知道在哪 + 用什麼 keyword 找」**，detail 自然從 subfile 取

**好的 pointer 範例**:
```
- [project_phase57_21_*.md](...) — Sprint 57.21 closed 2026-05-18; Chat-v2 Turn Block Model + Inspector 4-tab; calibration bimodal pattern.
  Keywords: chatv2, mockup-fidelity Phase-1, Turn Block, Inspector tabs.
```
（~180 char，topic 清楚 + keywords 利於 retrieval + subfile 是 single-source）

**差的 pointer**（目前 57.17 entry）:
```
- [...] — Sprint 57.17 ✅ 2026-05-15: AD-Tailwind-v4-Directive-Hotfix — 1-line CSS fix (`@tailwind ...` → `@import "tailwindcss"; @config ...;`) restores Tailwind utility CSS emission dead since Sprint 57.7 US-B1 (v4 PostCSS plugin silently no-op'd v3 directives — 9 ship sprints 57.7-57.16 rendered as unstyled HTML at runtime while e2e + a11y + visual-regression all passed inspecting only ARIA/DOM/text)...（continues for ~3000 chars）
```
（這是 retro 整段 dump，duplicate 了 subfile + retrospective.md，違反 single-source）

### I.3 重新分類 — Audit Block 對應哪一邊

| CLAUDE.md Block | 角色判斷 | 行動 |
|----------------|---------|------|
| 1-21 最關鍵閱讀順序 + AI Notes | Navigator | ✅ Keep |
| 36-67 Core Vision | Principle | ✅ Keep |
| 68 表頭 + Phase row（簡化）| Principle（current milestone）| ⚠️ Simplify (drop sprint suffix list, point to memory index) |
| **71-77 Latest/Prev/Prev-Prev/Prev³/Prev⁴ Sprint rows** | **Development records** | 🔴 **Move out** → memory subfile (已是 single-source) + retrospective.md |
| 79 main HEAD | Point-in-time record | 🔴 Remove (`git log -1` 即可) |
| 80 Next Phase 候選 | Pending items / open issues | 🔴 Move out → `claudedocs/1-planning/next-phase-candidates.md` |
| 81 Roadmap (with sprint suffix list) | Mixed: high-level=principle, suffix=records | ⚠️ Simplify (keep "Phase 49-55 V2 ✅ / Phase 56-58 SaaS Stage 1 3/3 ✅ / Phase 57+ Frontend in progress" + link to memory index) |
| 82-84 Tech Stack / Architecture / Branch Protection | Principle / Rule | ✅ Keep |
| 88-149 V2 不是 / 範疇 / 約束 | Principle | ✅ Keep |
| 150-192 Mockup-Fidelity Hard Constraint | Rule | ✅ Keep |
| 194-240 Check Existing + 規劃文件導航 | Navigator | ✅ Keep |
| 241-345 V1 reference / Dev Commands / Code Standards / Env | Reference + Rule | ✅ Keep |
| 356-407 ClaudeDocs structure | Navigator | ✅ Keep |
| 408-460 Developer Preferences + Karpathy | Behavior rules | ✅ Keep |
| 461-520 File Header Convention | Rule | ✅ Keep |
| 521-578 Sprint Workflow | Rule | ✅ Keep |
| 579-end Important / graphify / V1 Backup | Reference | ✅ Keep |
| **~580+ Last Updated multi-paragraph history** | **Development records** | 🔴 **Remove** (collapse to 1-line) |
| **~600+ Recent Sprints (詳情見 memory/) block** | **Development records** | 🔴 **Remove entirely** (MEMORY.md 已是 index) |
| **~620+ [Sprint XX historical row preserved] blocks** | **Archived records** | 🔴 **Remove entirely** (memory subfile + retrospective 已存) |

| MEMORY.md Block | 角色判斷 | 行動 |
|----------------|---------|------|
| 開頭規範說明 + 「每行 ≤ 200 字」 | Rule（spirit OK, char rule 改為「quality pointer」表述）| ⚠️ Update wording per user 2026-05-18 |
| Recent Sprints (Phase 57+) 12 violating entries | Quality 差的 pointer（packed summary）| 🔴 Rewrite as quality pointer (topic + keywords + subfile path) |
| V2 Closure (Phase 49-56) section ~23 entries | Quality OK (mostly compliant) | ✅ Light touch — ensure keywords present |
| Background / Foundational section | Quality OK | ✅ Keep |
| Feedback section | Quality OK | ✅ Keep |

---

## J. Target Skeleton — What CLAUDE.md / MEMORY.md Should Look Like

### J.1 CLAUDE.md V2 Refactor Status section after cleanup（示意）

```markdown
## V2 Refactor Status（Phase 49+）

| Attribute | Value |
|-----------|-------|
| **Phase** | V2 22/22 ✅ + SaaS Stage 1 3/3 ✅ + SaaS Frontend in progress |
| **Current Sprint** | Sprint 57.22 (in progress) — see `feature/sprint-57-22-mockup-fidelity-audit` branch |
| **Sprint History** | See [`memory/MEMORY.md`](memory/MEMORY.md) §Recent Sprints + per-sprint subfile |
| **Pending / Next Phase** | See [`claudedocs/1-planning/next-phase-candidates.md`](claudedocs/1-planning/next-phase-candidates.md) |
| **Roadmap** | Phase 49-55 V2 ✅ / Phase 56-58 SaaS Stage 1 ✅ / Phase 57+ Frontend ongoing |
| **Tech Stack** | FastAPI + React 18 + PostgreSQL + Redis |
| **Architecture** | TAO/ReAct loop + 11+1 範疇 全 Level 4（Cat 9 L5）+ LLM Provider 中性 |
| **Branch Protection** | enforce_admins=true / review_count=0 / 5 required CI checks |

詳見 `docs/03-implementation/agent-harness-planning/06-phase-roadmap.md`。
```

預估 ~10-12 lines (vs 目前 14 rows × 多行 verbose ≈ ~250 lines worth content)。

### J.2 CLAUDE.md footer after cleanup（示意）

```markdown
**Last Updated**: 2026-05-18 (Sprint 57.22 — see git log + memory/ for sprint history)
**V2 Authority**: `docs/03-implementation/agent-harness-planning/` (21 docs)
**V1 Reference**: `CLAUDE.backup.md` + `docs/07-analysis/V9/00-index.md`
```

預估 3 lines (vs 目前 ~80 lines multi-paragraph history)。

### J.3 MEMORY.md Recent Sprints entry after cleanup（示意）

```markdown
- [project_phase57_21_chatv2_mockup_fidelity_phase_1.md](project_phase57_21_chatv2_mockup_fidelity_phase_1.md)
  — Sprint 57.21 closed 2026-05-18; Chat-v2 Turn Block Model + 3-col shell + Inspector 4-tab + Composer scaffolding;
  bimodal calibration pattern emerging.
  Keywords: chatv2, mockup-fidelity Phase-1, Turn Block, Inspector 4-tab, frontend-mockup-direct-port class, bimodal ratio.
```

預估每 entry ~3-4 lines / ~250-300 char（topic + 1-sentence what + keywords for retrieval）。

**Quality 重點**：
- Topic 一句話表達「這個 sprint 在做什麼大方向」
- Keywords 涵蓋 future AI/dev 可能用來 search 的詞（feature 名 / AD 名 / class 名 / 異常 pattern）
- Subfile path 顯式 link
- **絕對不 dump retro 內容 / 不寫 calibration ratio 數字 / 不寫 commit SHA / 不寫 Vitest count**（這些都在 subfile + retrospective）

---

## K. Updated Step 2 + Step 3 Scope（reflecting philosophy）

**Step 2 — Archive Cutoff Discipline 改為 Role-Based Discipline**:

寫進 `.claude/rules/sprint-workflow.md` 新章節 `§Sprint Closeout — CLAUDE.md / MEMORY.md Update Policy`：

- **CLAUDE.md update at sprint closeout**: 只動 `Current Sprint` row + `Last Updated` 那一行 + Phase / Roadmap milestone（若達成）。**禁止** 在 CLAUDE.md 加 sprint-by-sprint detail row。
- **MEMORY.md update at sprint closeout**: 新增 quality pointer entry（topic + keywords + subfile path），**禁止** packed retro summary；對應 subfile 是 detail single-source。
- **Sprint detail destinations**: memory subfile + retrospective.md + sprint plan §Workload + git log + PR description（5 個 authoritative sources already exist）。
- **Open items / Next Phase 候選 destination**: `claudedocs/1-planning/next-phase-candidates.md`（new file in Step 3）

**Step 3 — Execute Cleanup**:
- Trim CLAUDE.md per §I.3 (~250-line section → ~12 lines)
- Trim MEMORY.md 12 violating entries per §J.3 quality-pointer pattern
- Create `claudedocs/1-planning/next-phase-candidates.md` (move 20-bullet list)
- ~~Create `claudedocs/7-archive/sprint-history-index.md`~~ — NOT needed; memory subfiles + retrospective.md already serve this role
- Update MEMORY.md header 規則說明 from「每行 ≤ 200 字符」to「quality pointer principle: topic + keywords + subfile path; detail is single-source in subfile」

---

**Modification History**:
- 2026-05-18 (v2): Append §I-K reflecting user philosophy alignment — CLAUDE.md = navigator / principle / rule（NOT dev record）; MEMORY.md = quality pointer index（quality > char count）
- 2026-05-18 (v1): Initial audit (Step 1/4 of CLAUDE.md/MEMORY.md cleanup; trigger = user session-start context spike)
