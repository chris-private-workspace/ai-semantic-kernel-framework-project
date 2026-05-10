---
File: docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-15-checklist.md
Purpose: Sprint 57.15 execution checklist — AD-Inline-Style-Cleanup-Sweep (14 feature components' inline styles → Tailwind + no-inline-style ESLint guard + color-contrast axe rule re-enabled + visual baseline refresh; ~4 USs / Day 0-3).
Category: Frontend / a11y / DevOps (lint config)
Scope: Phase 57 / Sprint 57.15

Created: 2026-05-11 (drafted post-plan approval)
Last Modified: 2026-05-11
Status: Draft (Day 0 done — branch + plan + checklist + 三-prong; 4 D-PRE catalogued; Day 1 GO)

Modification History (newest-first):
    - 2026-05-11: Day 0 — §0.1-0.6 [x]; 三-prong done (4 D-PRE; D-PRE-1 → guard uses `no-restricted-syntax` not `react/forbid-dom-props`); §2.2 updated accordingly
    - 2026-05-11: Initial creation (Sprint 57.15 — mirrors 57.14 day-structure, Day 0-3 for focused mechanical-refactor scope)

Related:
    - sprint-57-15-plan.md (sibling plan — authority for this checklist)
    - sprint-57-14-checklist.md (structural template per sprint-workflow.md §Step 2 — most recent completed sprint)
---

# Sprint 57.15 — Checklist (Day 0-3)

> Branch: `feature/sprint-57-15-inline-style-cleanup`
> Calibration: `frontend-refactor-mechanical` HYBRID 0.50 (1st application)
> Bottom-up ~7.5-11.5 hr → committed ~4-6 hr
> Focused mechanical-refactor sprint (smaller than normal 5-day; Day 0-3). Closes the standing carryover `AD-Inline-Style-Cleanup-Sweep` + re-enables the `color-contrast` axe rule + adds the `no-inline-style` ESLint guard + refreshes the 3 affected visual-regression baselines (first end-to-end use of the 57.14 `visual-baseline` workflow).

---

## Day 0 — Setup + Branch + Pre-flight + 三-prong + Calibration

### 0.1 Branch creation
- [x] **Branch `feature/sprint-57-15-inline-style-cleanup` from main `c9d89ff3`** ✅
  - Verify: `git branch --show-current` → `feature/sprint-57-15-inline-style-cleanup`; `git rev-parse main` → `c9d89ff3...`

### 0.2 Pre-flight baseline capture (post Sprint 57.14) — DONE 2026-05-11 (sanity only; mostly untouched)
- [x] pytest baseline = **1676 pass + 4 skip** — not touched this sprint, sanity only (won't re-run; 0 backend changes expected)
- [x] mypy --strict baseline = **0 / 306 files** — not touched, sanity only
- [x] 9 V2 lints baseline = **9/9 green** — not touched, sanity only
- [x] Vitest baseline = **236 / 57 files** — not touched (unless a test asserts inline-style literal → D-PRE-4: none found)
- [x] Playwright baseline = **18 spec files**; local Windows run = 40 pass / 7 skip (6 visual opt-in-on-Windows + 1 connectivity); CI ubuntu = 46 pass / 1 skip (visual runs there)
- [x] Vite build main bundle baseline = **297.89 kB (gzip 95.27)** — expected ≈ unchanged or slightly down (less inline-style object literal)
- [x] LLM SDK leak baseline = **0** — not touched, sanity only
- [x] `style={{` occurrences baseline = **80 across 14 files** (`grep -rn "style={{" frontend/src`) — this sprint's target (→ should drop to only `eslint-disable`-annotated dynamic escapes)
- [x] Chromium browser binary installed — `chromium-1217` ↔ Playwright 1.59.1 (no install needed)

### 0.3 Day 0 三-prong verify (per AD-Plan-1+3+4 promoted rules) — DONE 2026-05-11; 4 D-PRE catalogued in progress.md (2🟡 / 2🟢); 0 abort; Day 1 GO (< 5% scope shift)
- [x] **Prong 1 Path Verify** — 14 src feature components ✅; `eslint.config.js` ✅ + `tests/e2e/a11y/a11y-scan.spec.ts` ✅ (`.disableRules(["color-contrast"])` at L90) + `tests/e2e/visual/visual-regression.spec.ts` ✅ + `visual-regression.spec.ts-snapshots/` has all 6 `*-chromium-linux.png` ✅ (57.14 PR #135) + `STYLE.md` ✅ + `CONVENTION.md` ✅ + `tailwind.config.ts` ✅ (`.ts` not `.js`) + `agent-harness-planning/16-frontend-design.md` ✅ (top level, NOT under phase-57-frontend-saas/) + `sprint-workflow.md` ✅. **package.json has `eslint-plugin-react-hooks` + `eslint-plugin-react-refresh` + `eslint-plugin-jsx-a11y` but NOT `eslint-plugin-react` → D-PRE-1.** DoD: D-PRE table in progress.md ✅
- [x] **Prong 2 Content Verify** — (a) `tailwind.config.ts` + `components/ui/*` colour classes → to be read in US-A2 before hex→class mapping (D-PRE-3: align `ApprovalCard` riskColor with `STYLE.md §3 Risk Badge Palette`); (b) `eslint.config.js` plugins = `@typescript-eslint`/`react-hooks`/`react-refresh`/`jsx-a11y`; `no-restricted-syntax` not configured → **D-PRE-1**: guard uses `no-restricted-syntax` `JSXAttribute[name.name='style']` selector, not `react/forbid-dom-props`; (c) `a11y-scan.spec.ts` scans `GATED_ROUTES = [/chat-v2 /cost-dashboard /sla-dashboard /admin-tenants /tenant-settings /governance /verification /loop-debug /memory]` via `mockApi`-503 → **D-PRE-2**: data-driven migration targets render as `<ErrorRetry>`, color-contrast re-enable may already be ≈green; (d) `STYLE.md` has §1 Tailwind Utility-First (Rules) / §2 Color Tokens / §3 Risk Badge Palette → **D-PRE-3**: §"Inline styles" extends §1 Rules + escape-hatch sub-§ (not new top-level §); (e) **D-PRE-4** 🟢: 0 vitest asserts `toHaveStyle`/`.style` on the 14 components; (f) ~90% static / ~5-10 dynamic sampled. DoD: drift findings catalogued in progress.md ✅
- [x] **Prong 3 Schema Verify** — **N/A** (0 DB / migration / ORM model / API endpoint touched). Noted in progress.md ✅

### 0.4 Calibration baseline confirmation
- [x] **Documented in progress.md Day 0** — Class `frontend-refactor-mechanical` HYBRID 0.50 (1st app, 1-data-point opens); HYBRID blend = US-A1+A2 ×0.40-0.45 ~0.70 + US-B1 ×0.55 ~0.15 + US-C1 ×0.80 ~0.15 ≈ 0.48 ≈ 0.50; bottom-up ~7.5-11.5 hr → committed ~4-6 hr; Day 0-3; Day 3 retro Q2 verify ratio ✅

### 0.5 Day 0 smoke probe (de-risk Group A + Group B) — deferred to Day 1 start
- [ ] **`npm run e2e -- a11y/a11y-scan.spec.ts`** (baseline, color-contrast still disabled) → should be green (confirms e2e pipeline + the a11y spec runs in this dev session) — run at Day 1 start before any migration
- [ ] **`npm run test`** (vitest) → 236 pass (confirms unit-test baseline before any migration) — Day 1 start
- [ ] **`npm run lint`** (baseline, no new guard) → silent (confirms ESLint baseline) — Day 1 start

### 0.6 Day 0 commit
- [x] **Day 0 commit** `chore(sprint-57-15, Day 0): plan + checklist + 三-prong baseline` (pending — about to commit)

---

## Day 1 — US-A1 (triage + migration table) + US-A2 (start migration)

### 1.1 US-A1: per-file triage → migration table
- [ ] **For each of the 14 files**: `grep -n "style={{"` + read context → classify each occurrence **static** (literal CSS object → Tailwind utility class) vs **dynamic** (computed from props/state → escape-hatch strategy: finite class set / CSS custom property + arbitrary value / inline `eslint-disable` + reason)
- [ ] **Migration table in progress.md Day 1** — columns: file / line / original inline style / static|dynamic / target (Tailwind class or escape strategy). For hex colours: map to a ≥4.5:1 design token / Tailwind shade (`#666`→`text-gray-600`, `#333`→`text-gray-800`, `#c62828`→`text-red-700`, …) — confirm contrast against the design system's tokens found in Prong 2

### 1.2 US-A2: migrate — chat-v2 5 files first (color-contrast re-enable prerequisite)
- [ ] **`features/chat_v2/components/ApprovalCard.tsx`** (4) — static → Tailwind class; `style={{ color: riskColor, fontWeight: 700 }}` → `className={cn("font-bold", riskLevel-conditional text-red-700/amber-700/green-700)}` (remove `riskColor` var); MHist +1 line
- [ ] **`features/chat_v2/components/ToolCallCard.tsx`** (3) — static → Tailwind class; MHist +1 line
- [ ] **`features/chat_v2/components/ChatLayout.tsx`** (2) — static → Tailwind class; MHist +1 line
- [ ] **`features/chat_v2/components/MessageList.tsx`** (2) — static → Tailwind class; MHist +1 line
- [ ] **`features/subagent/components/SubagentTree.tsx`** (1) — `style={{ marginLeft: depth>0 ? \`${depth*12}px\` : undefined }}` → CSS custom property `style={{ "--st-indent": ... } as React.CSSProperties}` + `className="ml-[var(--st-indent)]"` + `// eslint-disable-next-line no-restricted-syntax -- CSS var only, dynamic tree-indent` (or finite `ml-*` class set if depth bounded — decide from depth range); MHist +1 line
  - Verify: `npm run test -- chat_v2` + `npm run test -- subagent` green (or whichever feature test dirs exist); `git diff` only those 5 files
- [ ] **Day 1 progress entry** + migration table + drift catalog
- [ ] **Day 1 commit** `refactor(sprint-57-15, Day 1): US-A1 migration table + US-A2 chat-v2/subagent inline styles → Tailwind`

---

## Day 2 — US-A2 (remaining 9 files) + US-B1 (guard + a11y re-enable)

### 2.1 US-A2: migrate — visual-snapshot files (cost-dashboard / governance / admin-tenants) + the rest
- [ ] **`features/cost-dashboard/components/CostBreakdownTable.tsx`** (14) — static table cells → `p-2 text-right border-b border-gray-200 …`; `#666` → `text-gray-600`; MHist +1
- [ ] **`features/cost-dashboard/components/MonthPicker.tsx`** (2) — static → Tailwind; MHist +1
- [ ] **`features/governance/components/ApprovalList.tsx`** (1) — static → Tailwind; MHist +1
- [ ] **`features/admin-tenants/components/TenantListTable.tsx`** (5) — static → Tailwind; MHist +1
- [ ] **`features/admin-tenants/components/TenantListPagination.tsx`** (1) — `style={{ color: "#666", fontSize: "0.9rem" }}` → `text-gray-600 text-sm`; MHist +1
- [ ] **`features/admin-tenants/components/TenantListFilters.tsx`** (1) — static → Tailwind; MHist +1
- [ ] **`features/sla-dashboard/components/SLAMetricsCard.tsx`** (4) — static → Tailwind; bar width `style={{ width: \`${pct}%\` }}` → CSS custom property `style={{ "--bar-w": ... } as React.CSSProperties}` + `className="w-[var(--bar-w)]"` + `// eslint-disable-next-line no-restricted-syntax -- CSS var only, dynamic SLA bar width`; MHist +1
- [ ] **`features/tenant-settings/components/TenantSettingsView.tsx`** (27) — static → Tailwind; MHist +1
- [ ] **`features/tenant-settings/components/TenantSettingsEditForm.tsx`** (13) — static → Tailwind; MHist +1
  - Verify: `npm run test` (full vitest) → 236 pass (or adjusted-assertion count, noted in progress.md); `grep -rn "style={{" frontend/src` → only `eslint-disable-next-line no-restricted-syntax`-annotated dynamic escapes remain (each with a reason comment); `git diff` only `frontend/src/features/**` (+ maybe `tailwind.config.*`); no component-logic change

### 2.2 US-B1: ESLint guard + color-contrast re-enable + STYLE.md
> **D-PRE-1**: `eslint-plugin-react` is not a dep → use ESLint's built-in `no-restricted-syntax` (not `react/forbid-dom-props`/`react/forbid-component-props`). One `JSXAttribute[name.name='style']` selector covers both `<div style={…}>` and `<Comp style={…}>` (both are `JSXAttribute` at AST level).
- [ ] **`frontend/eslint.config.js`** — add to `rules`: `"no-restricted-syntax": ["error", { "selector": "JSXAttribute[name.name='style']", "message": "Use Tailwind utility classes (STYLE.md §1). For genuinely-dynamic values (computed dimensions, progress %), set a CSS custom property and read it via a Tailwind arbitrary value (`pl-[var(--x)]`), or add `// eslint-disable-next-line no-restricted-syntax -- <reason>`." }]` (if `no-restricted-syntax` ever needs another selector later, it becomes an array of objects — fine)
- [ ] **`frontend/tests/e2e/a11y/a11y-scan.spec.ts`** — remove `.disableRules(["color-contrast"])` (→ `new AxeBuilder({ page }).analyze()`); update the comment block (no longer mentions chat-v2 inline panels — they're clean). If re-enabling surfaces *out-of-scope* contrast violations that can't be fixed this sprint → keep a narrowed `.disableRules([...])` with a comment naming a NEW `AD-Color-Contrast-Round2` + list the offenders + retrospective Q4 — but try full-enable first (D-PRE-2: with mockApi-503 it may already be ≈green). File-header MHist +1
- [ ] **`frontend/STYLE.md`** — extend §1 "Rules" with the `no-restricted-syntax` inline-style guard reference + add an "Inline-style escape hatches" sub-section (3 strategies for dynamic values: finite class set [cross-ref §3 Risk Badge Palette] / CSS custom property + Tailwind arbitrary value / inline `// eslint-disable-next-line no-restricted-syntax -- <reason>` — short example each). NOT a new top-level § (D-PRE-3). MHist += 57.15 entry; `Last Modified` → 2026-05-11. (If `CONVENTION.md` §10 mentions styling → add a cross-ref, no content dup.)
  - Verify: `npm run lint` → 0 error (the 14 files are clean; dynamic escapes carry `eslint-disable`); `npm run e2e -- a11y/a11y-scan.spec.ts` → green (color-contrast now enabled; if red → US-A2 missed a low-contrast colour → fix the *colour*, not the spec); `npm run build` green
- [ ] **Day 2 progress entry** + verify notes
- [ ] **Day 2 commit** `feat(sprint-57-15, Day 2): US-A2 remaining 9 files + US-B1 no-inline-style guard + color-contrast re-enabled`

---

## Day 3 — US-C1: validation sweep + visual baseline refresh + retrospective + memory + doc syncs + PR

### 3.1 US-C1: full validation sweep
- [ ] **Frontend**: `npm run lint` (0 error, incl. new guard) / `npm run build` (main bundle ≈ 297.89 kB, ± small) / `npm run test` (vitest 236 pass, or adjusted count) / `npx playwright test` (40 pass / 7 skip on Windows; visual stays skip locally)
- [ ] **Backend sanity** — `git diff --stat main..HEAD` = 0 `backend/` changes (only `frontend/**` + `docs/**`) → backend baselines guaranteed unchanged (pytest 1676 pass+4 skip / mypy 0/306 / 9-9 V2 lints / 0 LLM SDK leak); not re-run (rationale in retrospective Q1)

### 3.2 US-C1: visual baseline refresh (first end-to-end use of the 57.14 mechanism)
- [ ] **`git push -u origin feature/sprint-57-15-inline-style-cleanup`**
- [ ] **`gh workflow run "Playwright E2E" --ref feature/sprint-57-15-inline-style-cleanup`** → wait for the `visual-baseline` job (ubuntu-latest) → it (a) runs `RUN_VISUAL=1 playwright test visual --update-snapshots`, (b) if changed: pushes to `chore/visual-baselines-<run_id>` + opens a PR against the feature branch, (c) always uploads the `visual-baselines` artifact
- [ ] **`gh run download <run_id> -n visual-baselines`** → take the 6 PNGs → commit the changed ones (expect: `cost-dashboard` / `governance` / `admin-tenants` change colour; `app-shell` / `auth-login` / `verification-recent` unchanged) into the feature branch directly (same approach as 57.14 PR #135) → close the `chore/visual-baselines-<run_id>` auto-PR (not merged — committed manually)
- [ ] **Eyeball the 3 changed PNGs** — confirm only colour changed (no layout/spacing drift — Tailwind `p-2`/`mt-4`/`w-full` are byte-equivalent to the original inline values; if layout drifted → migration bug → fix the migration)
  - Verify: feature branch CI re-runs `visual-regression.spec.ts` → green. If the workflow can't run on the feature branch (perms) → fallback: note in retrospective Q4 (`AD-Visual-Baseline-Refresh-57.15`), PR description says "`visual-regression.spec.ts` CI red is intentional — baseline pending refresh post-merge via `gh workflow run --ref main`", don't block merge

### 3.3 US-C1: routes / docs cross-check
- [ ] `routes.config.ts` — no change (no routing change) ✅
- [ ] 17.md — no change (0 NEW agent-harness contract/ABC/LoopEvent/migration/API) ✅

### 3.4 US-C1: retrospective.md (Q1-Q7)
- [ ] **NEW `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-15/retrospective.md`** — Q1 (US-A1/A2/B1/C1) / Q2 (ratio vs committed ~4-6 hr; vs bottom-up; multiplier verdict) / Q3 (drift findings) / Q4 (carryover AD: `AD-Lighthouse-Visual-Hard-Gate` still open / `AD-Color-Contrast-Round2` if out-of-scope violations / `AD-Visual-Baseline-Refresh-57.15` if fallback path / 57.13 carryover untouched / pre-existing doc nits) / Q5 (Phase 57.16+ candidate names only) / Q6 (KEEP/adjust 0.50 — 1-data-point opens) / Q7 (N/A — not a spike) + 8-point self-check all ✅ + rolling-planning self-check ✅

### 3.5 US-C1: memory snapshot
- [ ] **NEW `memory/project_phase57_15_inline_style_cleanup.md`** + **`MEMORY.md` index +1 row** (Recent Sprints top)

### 3.6 US-C1: doc syncs (in-sprint)
- [ ] `16-frontend-design.md` — V2 Ship Timeline +1 entry (12/N counter — inline-style sweep + a11y color-contrast re-enabled + no-inline-style guard + 3 visual baselines refreshed)
- [ ] `.claude/rules/sprint-workflow.md` — calibration matrix +1 row (`frontend-refactor-mechanical` 0.50 1-data-point, ratio TBD KEEP) + matrix MHist
- [ ] `STYLE.md` — §Inline styles + MHist (done in US-B1)
- [ ] checklist [x] + plan/checklist header MHist closeout (Status: Draft → Closed)
- [ ] **Deferred post-merge** (not in this PR): `CLAUDE.md` (main HEAD + Latest Sprint row + Next Phase 候選 — remove `AD-Inline-Style-Cleanup-Sweep`; note a11y color-contrast now enabled; carryover update) + `claudedocs/6-ai-assistant/prompts/SITUATION-V2-SESSION-START.md` §第八部分

### 3.7 US-C1: PR open + closeout sync
- [ ] **`gh pr create`** — title `Sprint 57.15 — AD-Inline-Style-Cleanup-Sweep (14 components' inline styles → Tailwind + no-inline-style guard + color-contrast re-enabled)`; body has summary + V2 紀律 9 項 self-check + test plan + post-merge follow-ups (CLAUDE.md/SITUATION sync; visual-baseline refresh if fallback) + carryover
- [ ] **Verify 5 active CI checks** — `Frontend E2E` green if visual baselines refreshed in-branch; else red on `visual-regression.spec.ts` with PR-description note (intentional)
- [ ] **Squash merge** — 🚧 NOT done in-session: per executing-actions-with-care, squash-merge to `main` is surfaced to the user for confirmation (PR open + CI status communicated → user decides)

### 3.8 Day 3 progress entry + commit
- [ ] **Day 3 progress entry** (validation sweep results + baseline refresh outcome + closeout)
- [ ] **Day 3 commit** `chore(sprint-57-15, Day 3): retrospective + doc syncs + visual baseline refresh + closeout`

---

## 重要備註

### Rolling planning 紀律自檢（每 day 結束 + Day 3 closeout 必檢）
- ☐ 沒預寫 57.16 sprint plan（Phase 57.16+ candidates 只列候選名於 retrospective Q5）
- ☐ 沒跳過 plan/checklist 直接 code（Day 0 plan + checklist 完整；Day 1 起 code）
- ☐ 沒刪除未勾選 [ ] 項（用 [x] 完成 / 🚧 阻塞 + reason；若分批則未清的檔 file-level eslint-disable + reason + carryover AD → 不 silent 跳過）
- ☐ 沒在 retrospective 寫具體未來 sprint task（Q5 只列候選）

### Scope 控管（focused 機械重構 sprint）
- 若 14 檔一天改不完（54 個 occurrence 集中在 `TenantSettingsView` 27 + `TenantSettingsEditForm` 13 + `CostBreakdownTable` 14）→ Day 1-2 都給 Group A；仍超 → 先改 chat-v2 5 檔（`color-contrast` 重開的前提）+ visual-snapshot 的 7 檔（cost/governance/admin-tenants），剩 `TenantSettings{View,EditForm}` + `SLAMetricsCard` 標 🚧 + carryover AD `AD-Inline-Style-Cleanup-Sweep-Round2`（**不刪 / 不留半套** — 若分批則 guard 對未清的檔 `/* eslint-disable no-restricted-syntax */` file-level + reason + carryover AD；或 guard 延後到全清）
- 若重開 `color-contrast` 出現 out-of-scope 違規無法本 sprint 修 → 窄化 `.disableRules` + comment 標 NEW `AD-Color-Contrast-Round2` + retrospective Q4（**不**假裝沒看到）
- visual baseline 重產走 57.14 workflow（feature branch dispatch → 下載 artifact commit）；若跑不了 → fallback：merge 後在 main 跑（接受 `visual-regression.spec.ts` CI 紅，PR 註明 intentional）+ retrospective Q4 `AD-Visual-Baseline-Refresh-57.15`

### V2 紀律 9 項自檢（每 commit + 每 PR — per plan §Acceptance Criteria）
1. ✅ Server-Side First — N/A（不動 backend）；前端樣式重構
2. ✅ LLM Provider Neutrality — N/A（不碰 agent_harness）；Tailwind / ESLint / @axe-core 非 LLM SDK
3. ✅ CC Reference 不照搬 — N/A
4. ✅ 17.md Single-source — N/A（0 NEW agent-harness contract/ABC/LoopEvent/migration/API）
5. ✅ 11+1 範疇 — N/A（純前端 component + ESLint config + e2e spec；無範疇雜湊）
6. ✅ AP-2/4/6 — no orphan（`no-restricted-syntax` style-attr guard 真的會 lint fail / color-contrast 重開真的會 scan）/ no Potemkin（migration 後低對比色真消失）/ YAGNI（不順手設計系統全替換 / 不加沒被要求的 token / 不重構沒壞的 component 邏輯 / 不為 guard 裝 eslint-plugin-react）
7. ✅ Sprint workflow — plan→checklist→三-prong→code→progress→retro，無跳步
8. ✅ File header MHist — plan/checklist/progress/retrospective header + 每改的 component 檔更新 MHist（≤ E501 1-line）
9. ✅ Multi-tenant — N/A（不動 backend / DB / API）

### Sprint 57.x cascade lessons 強制執行
- ✅ Day-0 三-prong（path + content；schema N/A）必跑
- ✅ Day-0 smoke probe（a11y-scan + vitest + lint baseline）確認管線通
- ✅ 修色 / 改 component 不改 spec 來「跑綠」（除非斷言對象本來就該改 — 如 `toHaveStyle({color:hex})` → `toHaveClass`）
- ✅ 不 disable / skip / `test.only` 來「跑綠」（per CLAUDE.md sacred rule）— `color-contrast` 若必須窄化 disable 必標 NEW AD + comment
- ✅ 每改一檔（或一組相關檔）跑該 feature vitest；改完跑全套 vitest；最後 e2e 全套
- ✅ Tailwind class 必須與原 inline 值 *等價*（`p-2`=`0.5rem` …）— spacing/layout 不該飄，只顏色變（intentional）；重產 baseline 後 eyeball 確認
- ✅ `[skip ci]` 已在 visual-baseline auto-commit message（57.14 已處理）；本 sprint 走「下載 artifact 手動 commit」路徑（同 57.14 PR #135）

### Open Items / Carry-forward（待填入 retrospective Q4）
- **AD-Lighthouse-Visual-Hard-Gate** — `frontend-lighthouse.yml` continue-on-error → required；`visual-regression.spec.ts` 已在 CI 跑（57.14），下一步從「跑」轉「gating」（待 baseline 穩定數個 CI cycle 後）
- **AD-Color-Contrast-Round2**（NEW，若本 sprint 重開 color-contrast 出現 out-of-scope 違規無法修）— 列剩餘違規 + 檔/組件
- **AD-Visual-Baseline-Refresh-57.15**（NEW，若 feature-branch workflow dispatch 跑不了 → 走 fallback merge 後補）
- 57.13 carryover 未動：AD-WorkOS-Prod-Redirect-Flow / AD-i18n-Feature-Namespaces / AD-Frontend-RUM-SessionReplay / AD-Bundle-Size(optional) / D-DAY4-2
- Pre-existing doc nits（**未修 — out of scope**，除非本 sprint 剛好碰那兩檔）：`CONVENTION.md` §8 e2e 範例 import `seedAuthJwt` from 錯路徑 `"../helpers/auth"`（實際 `tests/e2e/fixtures/auth-fixtures.ts`）；`auth-fixtures.ts` header NOTE 說 "Full e2e sweep: Sprint 57.13 US-C1"（stale）
