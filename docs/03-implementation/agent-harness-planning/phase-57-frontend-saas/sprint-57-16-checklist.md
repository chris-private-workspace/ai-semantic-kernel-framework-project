---
File: docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-16-checklist.md
Purpose: Sprint 57.16 execution checklist — AD-Inline-Style-Cleanup-Sweep-Round2 (5 deferred feature components' inline styles → Tailwind + remove their 5 file-level eslint-disables + flip /chat-v2 back to full color-contrast in a11y-scan.spec.ts + STYLE.md §1 cleanup; ~4 USs / Day 0-3).
Category: Frontend / a11y / DevOps (lint config)
Scope: Phase 57 / Sprint 57.16

Created: 2026-05-11 (drafted post-plan approval)
Last Modified: 2026-05-11
Status: Day 0 done (§0.1-0.4 [x]; §0.5 smoke probe deferred to Day 1 start; §0.6 commit pending in this commit)

Modification History (newest-first):
    - 2026-05-11: Day 0 — §0.1-0.4 [x]; 三-prong done (4 D-PRE; 0 scope shift; Day 1 GO); §0.5 smoke probe deferred to Day 1 start per checklist note
    - 2026-05-11: Initial creation (Sprint 57.16 — mirrors 57.15 day-structure, Day 0-3 for focused mechanical-refactor tier-2 scope)

Related:
    - sprint-57-16-plan.md (sibling plan — authority for this checklist)
    - sprint-57-15-checklist.md (structural template per sprint-workflow.md §Step 2 — most recent completed sprint)
---

# Sprint 57.16 — Checklist (Day 0-3)

> Branch: `feature/sprint-57-16-inline-style-round2`
> Calibration: `frontend-refactor-mechanical` HYBRID 0.50 (2nd application)
> Bottom-up ~5.5-8 hr → committed ~3-4 hr
> Focused mechanical-refactor tier-2 sprint (smaller than 57.15: 5 files vs 10, no new guard, no visual-baseline regen). Closes the Sprint 57.15 carryover `AD-Inline-Style-Cleanup-Sweep-Round2` + flips `/chat-v2` to full `color-contrast` (the last route still disabled) + makes the entire `frontend/src` inline-style-clean (0 `style=`, 0 file-level eslint-disable).

---

## Day 0 — Setup + Branch + Pre-flight + 三-prong + Calibration

### 0.1 Branch creation
- [x] **Branch `feature/sprint-57-16-inline-style-round2` from main `afd7917b`** ✅
  - Verify: `git branch --show-current` → `feature/sprint-57-16-inline-style-round2`; `git rev-parse main` → `afd7917b854b0ef1090b734d1d644c7d2a9ab8e8`

### 0.2 Pre-flight baseline capture (post Sprint 57.15) — sanity only; mostly untouched — DONE 2026-05-11
- [x] pytest baseline = **1676 pass + 4 skip** — not touched this sprint, sanity only (won't re-run; 0 backend changes expected)
- [x] mypy --strict baseline = **0 / 306 files** — not touched, sanity only
- [x] 9 V2 lints baseline = **9/9 green** — not touched, sanity only
- [x] Vitest baseline = **236 / 57 files** — not touched (D-PRE-2 confirmed 0 inline-style-literal assertions)
- [x] Playwright baseline = **18 spec files**; local Windows run = 40 pass / 7 skip (6 visual opt-in-on-Windows + 1 connectivity); CI ubuntu = 46 pass / 1 skip (visual runs there); a11y-scan currently = 2 pass (color-contrast on for 8/9, `/chat-v2` disabled via `allowLowContrast`)
- [x] Vite build main bundle baseline = **297.89 kB (gzip 95.27)** — expected ≈ unchanged or slightly down (removes 2 `Record<string,CSSProperties>` + 4 helper fns + inline-style object literals)
- [x] LLM SDK leak baseline = **0** — not touched, sanity only
- [x] `style=\{` occurrences baseline = **5 real positives across 5 files** (`grep -rEn "style=\{" frontend/src --include="*.tsx"` returns 7 but `SubagentTree.tsx` + `ApprovalList.tsx` are JSDoc/comment false-positives — D-PRE-1). This sprint's target → 0 real positives (each Round2 file migrated + 5 file-level disables removed)
- [x] 5 file-level `/* eslint-disable no-restricted-syntax -- AD-Inline-Style-Cleanup-Sweep-Round2 */` directives confirmed at line 1 of `ChatLayout` / `InputBar` / `SLAMetricsCard` / `TenantSettingsView` / `TenantSettingsEditForm` — this sprint removes all 5
- [x] Chromium browser binary installed — `chromium-1217` ↔ Playwright 1.59.1 (no install needed)

### 0.3 Day 0 三-prong verify (per AD-Plan-1+3+4 promoted rules) — DONE 2026-05-11; 4 D-PRE catalogued (2🟢 / 2🟡 out-of-scope); 0 scope shift; Day 1 GO
- [x] **Prong 1 Path Verify** — 5 src feature components ✅ + `eslint.config.js` ✅ (`no-restricted-syntax` guard at L59-66) + `tests/e2e/a11y/a11y-scan.spec.ts` ✅ (`allowLowContrast` param at L85 + conditional disable at L87-94 + `route === "/chat-v2"` at L122) + `tests/e2e/visual/visual-regression.spec.ts` ✅ + 6 `*-chromium-linux.png` baselines ✅ + `STYLE.md` ✅ + `CONVENTION.md` ✅ + `tailwind.config.ts` ✅ + `src/index.css` ✅ + `agent-harness-planning/16-frontend-design.md` ✅ + `sprint-workflow.md` ✅. DoD: D-PRE catalog in progress.md ✅
- [x] **Prong 2 Content Verify** — (a) `tailwind.config.ts` + `src/index.css` confirmed define ONLY {background/foreground/primary/secondary/destructive/muted/border/input/ring} + nested `-foreground` → **D-PRE-4**: STYLE.md §2 token table drifts (`success`/`warning`/`danger`/`card` etc. NOT defined); strategy adjusted (verified tokens for critical path, 57.15 vocab elsewhere); (b) `a11y-scan.spec.ts` signature + locations confirmed for US-B1 removal; (c) `eslint.config.js` `no-restricted-syntax` `JSXAttribute[name.name='style']` rule at L59-66 (NOT changed in 57.16); (d) **D-PRE-2**: 0 vitest specs across `frontend/tests/unit/` (proper test root) assert `toHaveStyle`/`getComputedStyle`/`.style`/`backgroundColor` — risk drops to ~0; (e) `SLAMetricsCard.tsx` confirmed has NO real bar width — file-level disable reason "dynamic bar widths" stale, all dynamic values are 3-way enum (`noData ? "#888" : passing ? "#1a7f37" : "#a00"`) → finite class lookup; (f) **D-PRE-3**: STYLE.md §3 "Reference component" path `governance/components/ApprovalCard.tsx` is stale (file doesn't exist; real is `governance/components/ApprovalList.tsx`) — out-of-scope doc nit; (g) 5 files' static vs enum-dynamic confirmed: ~93% static (~58 `style=`) + ~7% enum-dynamic (4 files have enum colour; 0 files have continuous values). DoD: drift findings catalogued in progress.md ✅
- [x] **Prong 3 Schema Verify** — **N/A** (0 DB / migration / ORM model / API endpoint touched). Noted in progress.md ✅

### 0.4 Calibration baseline confirmation
- [x] **Documented in progress.md Day 0** — Class `frontend-refactor-mechanical` HYBRID 0.50 (2nd app — 57.15 was 1st, ratio `actual/committed` ≈ 1.7 OVER band but `actual/bottom-up` ≈ 0.89; per §Calibration matrix 3-sprint window rule KEEP 0.50, single-sprint outliers ignored); HYBRID blend = US-A1+A2 ×0.40-0.45 ~0.70 + US-B1 ×0.55 ~0.10 + US-C1 ×0.80 ~0.20 ≈ 0.48 ≈ 0.50; bottom-up ~5.5-8 hr → committed ~3-4 hr; Day 0-3; Day 3 retro Q2 verify ratio (if 2/2 over band → Q6 proposes 0.50→0.70-0.80 for next refactor sprint per matrix note) ✅

### 0.5 Day 0 smoke probe (de-risk Group A + Group B) — deferred to Day 1 start
- [ ] **`npm run e2e -- a11y/a11y-scan.spec.ts`** (baseline — color-contrast on for 8/9, `/chat-v2` via `allowLowContrast`) → should be 2 pass (confirms e2e pipeline + the a11y spec runs in this dev session) — run at Day 1 start before any migration
- [ ] **`npm run test`** (vitest) → 236 pass (confirms unit-test baseline before any migration) — Day 1 start
- [ ] **`npm run lint`** (baseline — guard already there, 5 file-level disables active) → silent — Day 1 start
- [ ] **`npx playwright test chat/` + `npx playwright test`** (baseline — chat-v2 4 e2e + approval-card.spec.ts pass) → confirms regression-sentinel baseline before touching ChatLayout/InputBar — Day 1 start

### 0.6 Day 0 commit
- [x] **Day 0 commit** `chore(sprint-57-16, Day 0): plan + checklist + 三-prong baseline` ✅

---

## Day 1 — US-A1 (triage + migration table) + US-A2 (start: chat-v2 + sla-dashboard)

### 1.1 US-A1: per-file triage → migration table — DONE 2026-05-11
- [x] **Triage** done across the 5 files; full migration table in progress.md Day 1 (line/key/original/class/target). ~93% static / ~7% enum-dynamic (4 files have enum colour); 0 files have continuous values (SLAMetricsCard's disable reason was stale per D-PRE-2).
- [x] **Hex → token mapping confirmed** against `tailwind.config.ts` + `src/index.css` + STYLE.md §2 per D-PRE-4 strategy: critical-path tokens (`text-muted-foreground` / `bg-muted` / `bg-background` / `text-foreground` / `bg-primary`) for `/chat-v2`; 57.15 vocab (`bg-success`/`bg-warning`/`bg-danger`/`bg-muted-foreground`/`border-success`/`border-danger`/`bg-success/10`/`bg-danger/10`) for elsewhere — visual continuity with 57.15-migrated TenantListTable / ApprovalCard.

### 1.2 US-A2: migrate — chat-v2 (2 files; `/chat-v2` color-contrast prerequisite) + sla-dashboard (1 file) — DONE 2026-05-11
- [x] **`features/chat_v2/components/ChatLayout.tsx`** ✅ — `styles` Record(6) → Tailwind: page `grid h-[calc(100vh_-_6.5rem)] grid-cols-[240px_1fr_280px]` (drop `gridTemplateAreas` — 3 children in order via grid auto-placement; underscore→space for the calc()); sidebar `overflow-y-auto border-r border-border bg-muted p-4 text-sm text-foreground`; inspector mirror with `border-l` + `text-[13px]`; main `flex flex-col overflow-hidden`; placeholder `text-[13px] leading-relaxed text-muted-foreground` (**`#7c8696` → AA token — `/chat-v2` color-contrast prerequisite**); h3 `mt-0 text-[13px] text-muted-foreground`; dropped `import type { CSSProperties }`; **removed line-1 disable**; Description updated to remove "Phase 58+ Tailwind migration pending" note + add 57.16 note; MHist +1 (`- 2026-05-11: Sprint 57.16 — inline styles → Tailwind utility classes (AD-Inline-Style-Cleanup-Sweep-Round2)`)
- [x] **`features/chat_v2/components/InputBar.tsx`** ✅ — `styles` Record(7) + `statusStyle`/`modeButton`/`sendBtn` helper fn + `statusPill` → Tailwind: container `flex flex-col gap-2 border-t border-border bg-background px-6 py-3` (`#fff`→`bg-background` verified token); topRow `flex items-center gap-2.5 text-xs text-muted-foreground` (**`#7c8696` → AA token — `/chat-v2` prerequisite**); modeToggle `ml-auto flex items-center gap-1`; inputRow `flex items-end gap-2.5`; textarea `max-h-40 min-h-11 flex-1 resize-none rounded-md border border-border px-3 py-2.5 text-sm leading-relaxed outline-none` (dropped `fontFamily:"inherit"` — already inherits); errorBanner `rounded border border-danger/40 bg-danger/10 px-2.5 py-1.5 text-xs text-danger`; `statusPill` → `STATUS_PILL` const Record + `getPill()` fallback `{label:"○ idle", cls:"text-muted-foreground"}`; status span inline `cn("inline-flex items-center gap-1 font-medium", pill.cls)`; mode button inline `cn(..., active ? "bg-primary text-white" : "bg-background text-muted-foreground")`; send button inline `cn(..., sendDisabled ? "cursor-not-allowed bg-muted-foreground" : "cursor-pointer bg-primary")`; stop button `cursor-pointer rounded-md border-none bg-danger px-4 py-2.5 text-sm font-medium text-white`; dropped `import type { CSSProperties }`; **removed line-1 disable**; MHist +1
  - Verify: ✅ `npm run lint` silent (incl `--report-unused-disable-directives` — the 3 removed disables are gone, the 2 remaining for TenantSettings{View,EditForm} stay used) / ✅ `npm run test -- --run` → **57 files / 236 pass — unchanged** (full vitest; the `AuthShell.test.tsx:94 'kaboom'` stack trace is the intentional error-boundary test) / ✅ `npx playwright test chat/` → **10/10 pass** (4 chat-v2-ship + 4 approval-card incl `risk badge text + color reflects risk level (CRITICAL → dark red)` colour-literal regression sentinel + 1 chat-v2-loop-inline + 1 chat-v2-subagent-inline) — ChatLayout/InputBar structure didn't drift, approval-card colour assertion still green
- [x] **`features/sla-dashboard/components/SLAMetricsCard.tsx`** ✅ — 3-way enum colour/bg → `SLA_STATE` const Record `{noData/pass/fail: {text, border, bg}}` finite lookup (57.15 vocab); `const st = noData ? SLA_STATE.noData : passing ? SLA_STATE.pass : SLA_STATE.fail`; card `cn("min-w-[200px] rounded-lg border-2 p-4", st.border, st.bg)` + `data-testid` unchanged; label `<p>` `m-0 text-[0.85rem] text-muted-foreground` (`#444` → token); value `<p>` `cn("my-2 text-2xl font-bold", st.text)`; status `<p>` `cn("m-0 text-xs", st.text)`; removed `color`/`bg` hex vars; **removed line-1 disable** (stale "dynamic bar widths" reason removed with it — D-PRE confirmed never had bar widths); MHist +1
  - Verify: ✅ vitest pass (sla-dashboard suite unchanged in full run) / lint silent
- [x] **Day 1 progress entry** + migration notes + drift catalog ✅
- [x] **Day 1 commit** `refactor(sprint-57-16, Day 1): US-A1 triage + US-A2 chat-v2 + sla-dashboard inline styles → Tailwind` ✅

---

## Day 2 — US-A2 (tenant-settings 2 files) + US-B1 (a11y-scan `/chat-v2` flip + STYLE.md cleanup)

### 2.1 US-A2: migrate — tenant-settings (2 files) — DONE 2026-05-11
- [x] **`features/tenant-settings/components/TenantSettingsView.tsx`** ✅ — `stateBadgeColor`→`stateBadgeClass`: ACTIVE→`"bg-success"` / PROV|REQ→`"bg-warning"` / SUSP|ARCH|default→`"bg-muted-foreground"`; `planBadgeColor`→`planBadgeClass`: ENTERPRISE→`"bg-primary"` / else→`"bg-muted-foreground"`; container `p-8 font-sans`; description `<p>` `text-sm text-muted-foreground` (`#666`→AA token); "No tenant" `<p>` `text-danger` (`#a00`); loading `<p>` `italic`; error `<div>` `mt-4 border border-danger p-4 text-danger`; `<dl>` `mt-6 grid grid-cols-[max-content_1fr] gap-x-4 gap-y-2`; `<dt>` `font-semibold`; `<dd>` `m-0` (+ `font-mono` for id/code); badge `<span>` `cn(BADGE_CLASS, stateBadgeClass(data.state))` where `BADGE_CLASS = "rounded-sm px-2 py-0.5 text-[0.85rem] text-white"`; `<details>` `mt-4`; `<summary>` `cursor-pointer`; `<pre>` `bg-muted p-3 text-[0.85rem]` (`#f0f0f0`→`bg-muted`; STYLE.md §4 simplified to fit existing visual); Edit `<button>` `mt-6 px-4 py-2`; `import { cn }`; **removed line-1 disable**; MHist +1
- [x] **`features/tenant-settings/components/TenantSettingsEditForm.tsx`** ✅ — container `mt-6 border border-border p-6` (`#ccc`→`border-border`); each field group `mt-4`; `<label>` `block font-semibold`; `<input>`/`<textarea>` `mt-1 w-full px-2 py-1.5` (+ `font-mono text-[0.85rem]` for textarea per STYLE.md §4); validation `<p>` `mt-1 text-[0.85rem] text-danger` (`#a00`); save-error `<p>` `mt-4 text-danger`; button row `<div>` `mt-6 flex gap-3`; buttons `px-4 py-2`; **removed line-1 disable**; MHist +1
  - Verify: ✅ `npm run lint --report-unused-disable-directives` → silent (all 5 file-level disables now removed across the sprint); ✅ `grep -rEn "style=\{" frontend/src --include="*.tsx"` → only 2 JSDoc/comment matches (SubagentTree:43 comment + ApprovalList:11 JSDoc history — **0 real inline `style=` in `frontend/src`**); ✅ `npm run test -- --run` → 57 files / 236 pass — unchanged; ✅ `git diff` only `frontend/src/features/**` (+ Day 2 a11y-scan.spec.ts + STYLE.md + docs); no `tailwind.config.ts` change; no component-logic change

### 2.2 US-B1: a11y-scan `/chat-v2` flip + STYLE.md §1 cleanup — DONE 2026-05-11
- [x] **`frontend/tests/e2e/a11y/a11y-scan.spec.ts`** ✅ — `scan(page, label, allowLowContrast = false)` → `scan(page, label)` (3rd param dropped; conditional `disableRules(["color-contrast"])` block + its 6-line comment replaced by a single Sprint-57.16 explanation note); loop `await scan(page, route, route === "/chat-v2")` → `await scan(page, route)` (loop comment updated to "all 9 gated routes (incl /chat-v2) run the full axe rule set"); MHist +1 at top of newest-first list (`- 2026-05-11: Sprint 57.16 — /chat-v2 color-contrast re-enabled (ChatLayout + InputBar migrated to AA tokens); all 9 gated routes + auth pages now full axe rule set (AD-Inline-Style-Cleanup-Sweep-Round2)`)
- [x] **`frontend/STYLE.md`** ✅ — §1 "Inline-style escape hatches" final paragraph: "(see `features/chat_v2/components/ChatLayout.tsx` et al. — pending `AD-Inline-Style-Cleanup-Sweep-Round2`)" replaced with "(No live examples remain after Sprint 57.16 — the entire `frontend/src` is inline-style-clean — but the pattern stays documented for future bulk migrations.)"; MHist += 57.16 entry at top; `Last Modified` already 2026-05-11; `CONVENTION.md` checked — no §1 inline-style cross-ref needs editing
  - Verify: ✅ `npm run lint` 0 error; ✅ `npx playwright test a11y/a11y-scan.spec.ts` → **2 / 2 pass** (`/chat-v2` now scanned with full axe rule set including color-contrast; 4 moderate/minor reported on `/chat-v2` are `heading-order` / `landmark-main-is-top-level` / `landmark-no-duplicate-main` / `landmark-unique` — structural a11y nits, pre-existing, NOT color-contrast — logged for retrospective Q4 as separate future a11y-hardening sprint); ✅ `npx playwright test` (full) → **40 pass / 7 skip / 0 fail** (chat-v2 + approval-card + verification + governance + admin-tenants + a11y-scan all green; visual-regression 6 opt-in skip on Windows)
- [x] **Day 2 progress entry** + verify notes ✅
- [x] **Day 2 commit** `feat(sprint-57-16, Day 2): US-A2 tenant-settings + US-B1 /chat-v2 color-contrast re-enabled (all 5 file-level disables removed)` ✅

---

## Day 3 — US-C1: validation sweep + visual baseline sanity + retrospective + memory + doc syncs + PR

### 3.1 US-C1: full validation sweep
- [ ] **Frontend**: `npm run lint` 0 error (incl `no-restricted-syntax` guard + `--report-unused-disable-directives` — 0 file-level disables remain; codebase 0 `style=`) / `npm run build` main bundle `index-*.js` byte size recorded (≈ unchanged or slightly down) / `npm run test` (vitest) 236 pass — unchanged (or adjusted count if a layout assertion was changed — record in progress.md) / `npx playwright test` (full) 40+ pass / 7 skip / 0 fail
- [ ] **Backend sanity** — `git diff --stat main..HEAD` = 0 `backend/` changes (only `frontend/**` + `docs/**`) → backend baselines guaranteed unchanged (pytest 1676 pass+4 skip / mypy 0/306 / 9-9 V2 lints / 0 LLM SDK leak); not re-run (rationale in retrospective Q1)

### 3.2 US-C1: visual baseline sanity — DONE pending (expected 0 changes — no workflow run needed)
- [ ] **`git diff --stat main..HEAD`** confirms 0 files touched that render in the 6 `visual-regression.spec.ts` snapshot routes (app-shell / auth-login / verification-recent / cost-dashboard / governance / admin-tenants): the 5 migrated files are chat-v2 (`ChatLayout`/`InputBar`) / sla-dashboard (`SLAMetricsCard`) / tenant-settings (`TenantSettings{View,EditForm}`) — none in the 6 routes; `pages/` not touched → visual baselines expected unchanged → **no `gh workflow run` this sprint** (the differentiator vs Sprint 57.15 which had 7 files in 3 snapshot routes). Note in progress.md.
- [ ] **Fallback (only if `git diff` unexpectedly touches a snapshotted-route file)** — `gh workflow run "Playwright E2E" --ref feature/sprint-57-16-inline-style-round2` → download artifact → compare/commit per Sprint 57.14 PR #135 path + retrospective Q4 `AD-Visual-Baseline-Refresh-57.16`. **Expected: not needed.**
  - Verify: feature branch CI `visual-regression.spec.ts` will pass (baselines unchanged); `a11y-scan.spec.ts` will pass (9/9 full color-contrast)

### 3.3 US-C1: routes / docs cross-check
- [ ] `routes.config.ts` — no change (no routing change)
- [ ] `eslint.config.js` — no change (guard is 57.15's; only the 5 file-level disables removed from the source files)
- [ ] 17.md — no change (0 NEW agent-harness contract/ABC/LoopEvent/migration/API)

### 3.4 US-C1: retrospective.md (Q1-Q7)
- [ ] **NEW `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-16/retrospective.md`** — Q1 (US-A1/A2/B1/C1 ✅; 5 files migrated; `frontend/src` 0 `style=` / 0 file-level disable; `/chat-v2` full color-contrast — all 9 gated routes + auth pages now full axe rule set) / Q2 (`actual/bottom-up` ratio + `actual/committed` ratio — vs 57.15's 0.89 / 1.7; 2nd `frontend-refactor-mechanical` data point) / Q3 (Day 0 drift findings: SLAMetricsCard stale "dynamic bar widths" reason / STYLE.md §3 reference component naming / approx-value list pin / + any vitest layout-assertion adjustments) / Q4 (carryover AD: `AD-Lighthouse-Visual-Hard-Gate` still open — baselines stable; 57.13 carryover untouched: AD-Bundle-Size optional / AD-i18n-Feature-Namespaces / AD-WorkOS-Prod-Redirect-Flow / AD-Frontend-RUM-SessionReplay / D-DAY4-2; doc nits — CONVENTION.md §8 wrong import path / auth-fixtures.ts stale header NOTE) / Q5 (Phase 57.17+ candidate names only — see CLAUDE.md Next Phase 候選) / Q6 (calibration verdict — KEEP 0.50 if `actual/committed` ≈ 0.85-1.2; if 2/2 over band → propose 0.50→0.70-0.80 for next refactor sprint per matrix note) / Q7 (N/A — not a spike) + 8-point sprint-workflow self-check all ✅ + rolling-planning self-check ✅

### 3.5 US-C1: memory snapshot
- [ ] **NEW `memory/project_phase57_16_inline_style_round2.md`** + **`MEMORY.md` index +1 row** (Recent Sprints top)

### 3.6 US-C1: doc syncs (in-sprint)
- [ ] `16-frontend-design.md` — V2 Ship Timeline +1 entry (13/N counter — Round2 5/5 → all 15 feature components Tailwind-clean + `/chat-v2` color-contrast re-enabled → 9/9 gated routes + auth pages full axe rule + `no-restricted-syntax` guard now covers entire codebase with 0 file-level disables)
- [ ] `.claude/rules/sprint-workflow.md` — calibration matrix `frontend-refactor-mechanical` row updated (+1 data point 57.16=<ratio>; 2-data-point mean; verdict KEEP 0.50 per 3-sprint window rule OR if 2/2 over band note the propose-lift trigger) + matrix MHist
- [ ] `STYLE.md` — §1 "Inline-style escape hatches" cleanup + MHist (done in US-B1)
- [ ] checklist [x] + plan/checklist header MHist closeout (Status: Draft → Closed)
- [ ] **Deferred post-merge** (not in this PR): `CLAUDE.md` (main HEAD + Latest Sprint row + Next Phase 候選 — remove `AD-Inline-Style-Cleanup-Sweep-Round2`; note a11y color-contrast now 9/9; carryover update) + `claudedocs/6-ai-assistant/prompts/SITUATION-V2-SESSION-START.md` §第八部分

### 3.7 US-C1: PR open + closeout sync
- [ ] **`git push -u origin feature/sprint-57-16-inline-style-round2`** + **`gh pr create`** — title `Sprint 57.16 — AD-Inline-Style-Cleanup-Sweep-Round2 (5 deferred components' inline styles → Tailwind + /chat-v2 color-contrast re-enabled — frontend/src now inline-style-clean)`; body has summary + V2 紀律 9 項 self-check + test plan + post-merge follow-ups (CLAUDE.md/SITUATION sync) + carryover (`AD-Lighthouse-Visual-Hard-Gate`)
- [ ] **Verify 5 active CI checks** — pending CI run (`Frontend E2E` = this sprint's main check — a11y-scan `/chat-v2` full color-contrast green + visual-regression baselines unchanged green + chat-v2 4 e2e green; `visual-baseline` job correctly `skipping` on PR events)
- [ ] **Squash merge** — 🚧 NOT done in-session: per executing-actions-with-care, squash-merge to `main` is surfaced to the user for confirmation (PR open + CI status communicated → user decides)

### 3.8 Day 3 progress entry + commit
- [ ] **Day 3 progress entry** (validation sweep + visual-baseline-sanity-0-changes + closeout)
- [ ] **Day 3 commit** `chore(sprint-57-16, Day 3): retrospective + doc syncs + closeout`

---

## 重要備註

### Rolling planning 紀律自檢（每 day 結束 + Day 3 closeout 必檢）
- ☐ 沒預寫 57.17 sprint plan（Phase 57.17+ candidates 只列候選名於 retrospective Q5）
- ☐ 沒跳過 plan/checklist 直接 code（Day 0 plan + checklist 完整；Day 1 起 code）
- ☐ 沒刪除未勾選 [ ] 項（用 [x] 完成 / 🚧 阻塞 + reason）
- ☐ 沒在 retrospective 寫具體未來 sprint task（Q5 只列候選）

### Scope 控管（focused 機械重構 tier-2 sprint）
- 5 檔 ~62 `style=` attr——比 57.15（10 檔 ~70 attr）小；不切分。若意外發現某檔還有 component 本身的問題（非單純樣式）→ 標 🚧 + reason，**不刪 / 不留半套**；不夠時間就 carryover 並 file-level eslint-disable 保留（但**先試一次做完**——預期可以）
- 若 `/chat-v2` 全開後 color-contrast 紅且無法本 sprint 修色（ChatLayout 有 component 本身的 a11y 問題，非色問題）→ revert a11y-scan flip commit、保留 `allowLowContrast` 特例但 comment 改新 AD + retrospective Q4（**不**假裝沒看到）
- visual baseline **預期不需重產**（5 檔不在 6 snapshot route）；只 `git diff --stat` 確認；若意外碰到 → fallback 走 57.14 workflow + retrospective Q4

### V2 紀律 9 項自檢（每 commit + 每 PR — per plan §Acceptance Criteria）
1. ✅ Server-Side First — N/A（不動 backend）；前端樣式重構
2. ✅ LLM Provider Neutrality — N/A（不碰 agent_harness）；Tailwind / @axe-core 非 LLM SDK
3. ✅ CC Reference 不照搬 — N/A
4. ✅ 17.md Single-source — N/A（0 NEW agent-harness contract/ABC/LoopEvent/migration/API）
5. ✅ 11+1 範疇 — N/A（純前端 component + e2e spec；無範疇雜湊）
6. ✅ AP-2/4/6 — no orphan（移除 5 file-level disable → guard 對它們也 enable 真會 fail / `/chat-v2` color-contrast 全開真會 scan）/ no Potemkin（migration 後 sub-AA 色真消失 / `/chat-v2` 不再有特例）/ YAGNI（不順手設計系統全替換 / 不加沒被要求的 token / 不重構沒壞的 component 邏輯 / 不為沒有真連續值的 case 強上 CSS-var）
7. ✅ Sprint workflow — plan→checklist→三-prong→code→progress→retro，無跳步
8. ✅ File header MHist — plan/checklist/progress/retrospective header + 每改的 component 檔更新 MHist（≤ E501 1-line）
9. ✅ Multi-tenant — N/A（不動 backend / DB / API）

### Sprint 57.x cascade lessons 強制執行
- ✅ Day-0 三-prong（path + content；schema N/A）必跑
- ✅ Day-0 smoke probe（a11y-scan + vitest + lint + chat-v2 e2e baseline）確認管線通 + regression sentinel baseline
- ✅ 修色 / 改 component 不改 spec 來「跑綠」（除非斷言對象本來就該改 — 如 `toHaveStyle({color:hex})` → `toHaveClass`）
- ✅ 不 disable / skip / `test.only` 來「跑綠」（per CLAUDE.md sacred rule）— `/chat-v2` 全開若必須 revert 必標 NEW AD + comment（**不**假裝）
- ✅ 每改一檔（或一組相關檔）跑該 feature vitest；改完跑全套 vitest；最後 e2e 全套（含 chat-v2 regression sentinel）
- ✅ Tailwind class 必須與原 inline 值 *等價*（`p-4`=`1rem`、`gap-2`=`0.5rem`、`px-6 py-3`=`1.5rem 0.75rem`…）— layout 不該飄；近似值（`gap-2.5`≈`0.6rem`）僅用於不在 visual snapshot 的 case
- ✅ chat-v2 的 4 個 57.8 e2e + approval-card.spec.ts 是 regression sentinel — 改 ChatLayout/InputBar 後必跑

### Open Items / Carry-forward（待填入 retrospective Q4）
- **AD-Lighthouse-Visual-Hard-Gate** — `frontend-lighthouse.yml` continue-on-error → required CI check；`visual-regression.spec.ts` 從「跑」轉「gating」（baselines 57.15 已確認穩定 — 0 diff）；+companion `waitForLoadState("networkidle")` in visual specs to cover populated states
- **AD-Color-Contrast-Round2**（NEW，若本 sprint `/chat-v2` 全開出現無法修的色問題 → 列剩餘違規 + 檔/組件）— 預期不需要
- **AD-Visual-Baseline-Refresh-57.16**（NEW，若 `git diff` 意外碰到 snapshotted-route 檔且 workflow path 走不通 → 走 fallback）— 預期不需要
- 57.13 carryover 未動：AD-WorkOS-Prod-Redirect-Flow / AD-i18n-Feature-Namespaces / AD-Frontend-RUM-SessionReplay / AD-Bundle-Size(optional) / D-DAY4-2
- Pre-existing doc nits（**未修 — out of scope**）：`CONVENTION.md` §8 e2e 範例 import `seedAuthJwt` from 錯路徑 `"../helpers/auth"`（實際 `tests/e2e/fixtures/auth-fixtures.ts`）；`auth-fixtures.ts` header NOTE 說 "Full e2e sweep: Sprint 57.13 US-C1"（stale — 57.14 才是那個 sweep）
