# Sprint 57.17 Progress

**Sprint**: 57.17 — AD-Tailwind-v4-Directive-Hotfix
**Scope**: Phase 57 / `frontend-css-engine-hotfix` 0.60 (NEW class, 1st app)
**Branch**: `feature/sprint-57-17-tailwind-v4-hotfix`
**Status**: Day 0 → Day 1 transition

---

## Day 0 — 2026-05-15

### Accomplishments

- ✅ Plan file authored (`sprint-57-17-plan.md`, 319 lines, 11 top-level §, mirrors 57.16 structure)
- ✅ Checklist file authored (`sprint-57-17-checklist.md`, 4 Day, 3 Group US, mirrors 57.16 day-structure)
- ✅ Branch `feature/sprint-57-17-tailwind-v4-hotfix` created from main `16195fb4` (Sprint 57.16 head)
- ✅ User authorized all 5 plan §Open questions (calibration class / `@config` vs `@theme` / baseline regen path / approval-card sentinel handling / triple-PR pattern)
- ✅ Day 0 三-prong verify complete (2 path corrections, 0 content drift, 0 scope shift)

### Day 0 三-prong drift findings

- **D-PRE-1 (path)** — visual-regression baselines NOT at assumed `__screenshots__/`; actual path is `frontend/tests/e2e/visual/visual-regression.spec.ts-snapshots/` (Playwright's default `*.spec.ts-snapshots/` sub-dir naming convention). All 6 PNGs (`{app-shell,auth-login,verification-recent,cost-dashboard,governance,admin-tenants}-chromium-linux.png`) ARE present. **Impact**: checklist path string update only; no scope change.
- **D-PRE-2 (path)** — `visual-baseline` is NOT a separate `.github/workflows/visual-baseline.yml` file; it is a **JOB inside `playwright-e2e.yml:114-194`** gated by `if: github.event_name == 'workflow_dispatch'`. Single workflow_dispatch trigger fires the regen job + skips the regular e2e job via `if: github.event_name != 'workflow_dispatch'` on the latter (L60). FIX-008 PR-not-push pattern confirmed at L163-188 (`chore/visual-baselines-{run_id}` branch + auto-PR open). **Impact**: checklist trigger command corrected to `gh workflow run playwright-e2e.yml`; no scope change.
- **D-PRE-3 (none)** — Schema verify N/A confirmed (this sprint touches 0 DB / migration / ORM model / API endpoint).

### Prong 2 content verify summary

- (a) `grep -n "@tailwind " frontend/src/index.css` → **3 matches at L6-8** ✅ confirms current dead-directive state
- (b) `grep -n "@import \"tailwindcss\"" frontend/src/index.css` → **0 matches** ✅ confirms target not yet applied
- (c) `grep -n "@config" frontend/src/index.css` → **0 matches** ✅ confirms target not yet applied
- (d) `grep -n "@tailwindcss/postcss" frontend/postcss.config.cjs` → **1 match** ✅ v4 plugin already wired
- (e) `frontend/tailwind.config.ts` confirmed v3-style (content[] + theme.extend.colors + darkMode:"class") — loadable via `@config`
- (f) `frontend/vite.config.ts` → **0 tailwind references** ✅ (no v3-era header comment to update; clean)
- (g) `grep "className=\"flex " frontend/src/features/chat_v2/` → **6 occurrences in 4 files** ✅ utilities ARE consumed in source; this hotfix UNBLOCKS them, doesn't introduce them

### Day 0 GO/NO-GO

**GO** for Day 1 US-A1 (1-line CSS fix) — 0 scope shift; D-PRE-1+2 are path-corrections in checklist only.

### Calibration

NEW class `frontend-css-engine-hotfix` 0.60 (1st application, baseline opens this sprint). HYBRID blend N/A (single-domain hotfix — pure CSS config + validation, no multi-class mix). Bottom-up ~10 hr → committed ~6 hr per plan §Workload.

---

## Day 1 — _pending_

### Planned

- US-A1: `frontend/src/index.css:6-8` edit (`@tailwind base/components/utilities` → `@import "tailwindcss"; @config "../tailwind.config.ts";`) + MHist +1
- US-A1 verify: `npm run build` → check `dist/assets/index-*.css` > 40 kB; `grep "@tailwind " frontend/src/**/*.css` → 0
- US-B1 start: full e2e + `approval-card.spec.ts` DevTools investigation
