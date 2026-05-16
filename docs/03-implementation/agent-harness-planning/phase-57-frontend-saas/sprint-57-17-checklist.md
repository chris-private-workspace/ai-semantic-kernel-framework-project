---
File: docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-17-checklist.md
Purpose: Sprint 57.17 execution checklist — AD-Tailwind-v4-Directive-Hotfix (Tailwind v4 + v3 directive mismatch in `frontend/src/index.css:6-8` silently no-op'd since Sprint 57.7 US-B1 → 9 ship sprints rendered as unstyled HTML; 1-line CSS fix + full validation + visual baseline regen; Day 0-3).
Category: Frontend / build config (Tailwind PostCSS pipeline)
Scope: Phase 57 / Sprint 57.17

Created: 2026-05-15 (drafted post-plan approval)
Last Modified: 2026-05-15
Status: Open (Day 0 in progress — branch created, plan + checklist + 三-prong baseline pending commit)

Modification History (newest-first):
    - 2026-05-15: Initial creation (Sprint 57.17 — mirrors 57.16 day-structure, Day 0-3 for focused CSS-engine-hotfix scope)

Related:
    - sprint-57-17-plan.md (sibling plan — authority for this checklist)
    - sprint-57-16-checklist.md (structural template per sprint-workflow.md §Step 2 — most recent completed sprint)
---

# Sprint 57.17 — Checklist (Day 0-3)

> Branch: `feature/sprint-57-17-tailwind-v4-hotfix`
> Calibration: NEW class `frontend-css-engine-hotfix` 0.60 (1st application)
> Bottom-up ~10 hr → committed ~6 hr
> Single-line CSS config hotfix sprint with full-blast-radius validation. Restores Tailwind utility CSS emission (dead since Sprint 57.7 US-B1) — closes the foundation bug that left 9 ship sprints' worth of pages rendering as unstyled browser-default HTML while e2e + a11y + visual-regression all passed because they only inspect ARIA/DOM/text, not computed CSS. Regenerates the 6 `visual-regression.spec.ts` baselines (captured on broken state). Triple-PR pattern: hotfix → feature branch (a), baseline-regen sub-PR → feature branch (b), `chore/closeout-57-17` post-merge (c).

---

## Day 0 — Setup + Branch + Pre-flight + 三-prong + Calibration

### 0.1 Branch creation
- [x] **Branch `feature/sprint-57-17-tailwind-v4-hotfix` from main `16195fb4`** ✅
  - Verify: `git branch --show-current` → `feature/sprint-57-17-tailwind-v4-hotfix`; `git rev-parse main` → `16195fb4...` (Sprint 57.16 head)

### 0.2 Pre-flight baseline capture (post Sprint 57.16) — sanity only; mostly untouched
- [ ] pytest baseline = **1676 pass + 4 skip** — not touched this sprint (0 backend changes); sanity only
- [ ] mypy --strict baseline = **0 / 306 files** — not touched, sanity only
- [ ] 9 V2 lints baseline = **9/9 green** — not touched, sanity only
- [ ] Vitest baseline = **236 / 57 files** — sanity only (no unit-test inline-style assertions per Sprint 57.16 D-PRE-2)
- [ ] Playwright baseline = **40 pass / 7 skip / 0 fail** (local Windows; CI ubuntu 46 pass / 1 skip)
- [ ] Vite build main JS bundle baseline = **297.89 kB (gzip 95.27)** — expected ≈ unchanged post-fix (JS not affected)
- [ ] Vite build compiled CSS baseline = **~14 kB** — expected **> 40 kB post-fix** (utilities now emitted)
- [ ] LLM SDK leak baseline = **0** — not touched, sanity only
- [ ] `@tailwind` directive occurrences = **3** at `src/index.css:6-8` (current state; target post-US-A1 = 0)
- [ ] `@import "tailwindcss"` occurrences = **0** (target post-US-A1 = 1)
- [ ] Chromium browser binary check — `chromium-1217` ↔ Playwright 1.59.1 (no install needed)
- [ ] Manual screenshot baseline of `/` + `/auth/login` + `/chat-v2` (post-dev-login) via Playwright MCP — confirms current unstyled state (already captured 2026-05-15 pre-sprint: `login-page.png` + `chat-v2-page.png` at project root, will be archived to `claudedocs/3-progress/daily/2026-05-15-pre-57-17-baseline/`)

### 0.3 Day 0 三-prong verify (per AD-Plan-1+3+4 promoted rules)
- [ ] **Prong 1 Path Verify** — file existence checks:
  - `frontend/src/index.css` ✅ (current 54 lines)
  - `frontend/tailwind.config.ts` ✅ (52 lines, v3-style content[] + theme.extend.colors + darkMode:"class")
  - `frontend/postcss.config.cjs` ✅ (v4 plugin `@tailwindcss/postcss`)
  - `frontend/package.json` ✅ (`tailwindcss@^4.2.4` + `@tailwindcss/postcss@^4.2.4`)
  - `frontend/vite.config.ts` ✅ (check for v3-era comments to update)
  - `frontend/src/main.tsx` ✅ (import "./index.css" at L25)
  - 6 visual-regression baselines: `frontend/tests/e2e/visual/visual-regression.spec.ts-snapshots/{app-shell,auth-login,verification-recent,cost-dashboard,governance,admin-tenants}-chromium-linux.png` ✅ (D-PRE-1 path correction: Playwright's default `*.spec.ts-snapshots/` sub-dir naming, NOT `__screenshots__/`)
  - `visual-baseline` capability ✅ = **JOB inside `.github/workflows/playwright-e2e.yml:114-194`** (D-PRE-2 correction: NOT a separate `visual-baseline.yml`; triggered via `gh workflow run playwright-e2e.yml`; `if: github.event_name == 'workflow_dispatch'` gates the regen job; FIX-008 PR-not-push pattern at L163-188 confirmed)
  - `STYLE.md` ✅ + `CONVENTION.md` ✅ + `agent-harness-planning/16-frontend-design.md` ✅ + `sprint-workflow.md` ✅
  - DoD: D-PRE catalog in progress.md
- [ ] **Prong 2 Content Verify** — grep-based assertion checks:
  - (a) `grep -n "@tailwind " frontend/src/**/*.css` → **expect 3 matches** (`base` / `components` / `utilities` at `index.css:6-8`) — confirms current dead-directive state
  - (b) `grep -n "@import \"tailwindcss\"" frontend/src/**/*.css` → **expect 0 matches** — confirms target state not yet applied
  - (c) `grep -n "@config" frontend/src/**/*.css` → **expect 0 matches** — confirms target state not yet applied
  - (d) `cat frontend/postcss.config.cjs | grep "@tailwindcss/postcss"` → **expect 1 match** — confirms v4 plugin already wired
  - (e) `cat frontend/tailwind.config.ts | grep -E "darkMode|content|extend"` → **expect content[] + darkMode:"class" + extend:{}` present** — confirms config is v3-style (must be loadable via `@config`)
  - (f) `cat frontend/vite.config.ts | grep -i tailwind` → check for v3-era header references (if found → update in US-A1)
  - (g) Sample 5 utility class usages in real files — e.g. `grep -rn "className=\"flex " frontend/src/features/chat_v2/` → **expect many matches** (confirms utility classes ARE consumed; this hotfix unblocks them, not introduces them)
  - (h) Verify the 6 visual baselines were captured AFTER Sprint 57.7 US-B1 (i.e. on broken state) — check git log of `__screenshots__/app-shell-chromium-linux.png` → should show Sprint 57.14 (post-57.7) as the introducing commit
  - DoD: drift findings catalogued in progress.md as D-PRE-N entries (any unexpected grep result = blocking)
- [ ] **Prong 3 Schema Verify** — **N/A** (0 DB / migration / ORM model / API endpoint touched). Noted in progress.md

### 0.4 Calibration baseline confirmation
- [ ] **Documented in progress.md Day 0** — Class `frontend-css-engine-hotfix` 0.60 (NEW, 1st application — baseline opens this sprint); HYBRID blend N/A (single-domain hotfix — pure CSS config); bottom-up ~10 hr → committed ~6 hr; Day 0-3; Day 3 retro Q2 verify ratio (`actual/committed` should land in [0.85, 1.20] band ideally; if 1st-app outliers → 2-3 sprint window before adjustment per sprint-workflow.md `When to adjust` rule)

### 0.5 Day 0 smoke probe (de-risk Group A + Group B) — deferred to Day 1 start
- [ ] **Open http://localhost:3007/ in browser + DevTools** → confirm current unstyled state (no Tailwind utility rules in computed CSS) — runs at Day 1 start before US-A1 edit
- [ ] **`cd frontend && npm run build`** → record current `dist/assets/index-*.css` size (baseline ~14 kB) — Day 1 start
- [ ] **`npm run test`** (vitest) → 236 pass — Day 1 start
- [ ] **`npm run lint`** → silent — Day 1 start
- [ ] **`npx playwright test approval-card.spec.ts`** → record pre-fix pass behaviour for CRITICAL→`#b71c1c` sentinel (the key risk per plan §Risk matrix) — Day 1 start, BEFORE the fix

### 0.6 Day 0 commit
- [ ] **Day 0 commit** `chore(sprint-57-17, Day 0): plan + checklist + 三-prong baseline`

---

## Day 1 — US-A1 (Tailwind v4 directive fix) + US-B1 (start: e2e full suite + approval-card investigation)

### 1.1 US-A1: edit `frontend/src/index.css`
- [ ] **`frontend/src/index.css` L6-8** — replace `@tailwind base; @tailwind components; @tailwind utilities;` with `@import "tailwindcss"; @config "../tailwind.config.ts";`
  - Verify: `cat frontend/src/index.css | head -10` shows `@import "tailwindcss";` at L6 + `@config "../tailwind.config.ts";` at L7 (or wherever the 3 lines were)
  - Update `index.css` Description block: remove "Tailwind 4 directives" phrasing → "Tailwind v4 import + v3 config bridge"
  - MHist +1 line per `.claude/rules/file-header-convention.md` budget (≤ 100 chars effective):
    - `- 2026-05-15: Sprint 57.17 — replace dead v3 @tailwind directives with v4 @import + @config (closes AD-Tailwind-v4-Directive-Hotfix)`
- [ ] **`frontend/vite.config.ts`** — if Day 0 三-prong Prong 2-f flagged any v3-era header comment, update wording (no functional change to vite plugin chain)

### 1.2 US-A1: build verify + grep verify + lint
- [ ] **`cd frontend && npm run build`** → ✅ no warnings; `dist/assets/index-*.css` size **> 40 kB** (baseline was ~14 kB) — confirms utilities are now emitted
- [ ] **`grep -rn "@tailwind " frontend/src/**/*.css`** → 0 matches (post-edit)
- [ ] **`grep -rn "@import \"tailwindcss\"" frontend/src/**/*.css`** → 1 match (`src/index.css:6`)
- [ ] **`npm run lint`** → silent (ESLint doesn't lint CSS but stylelint may; if stylelint complains about `@config`, add `// stylelint-disable-next-line at-rule-no-unknown` comment)
- [ ] **`npm run test`** (vitest) → 236 pass (no unit test should care about CSS bundle)

### 1.3 US-B1 start: full e2e + `approval-card.spec.ts` DevTools investigation
- [ ] **Restart Vite dev server** (`python scripts/dev.py restart frontend`) → confirm hot-reload picks up new CSS
- [ ] **Manual browser verify** — open http://localhost:3007/auth/login → confirm shadcn styling visible (NOT Times-Roman serif); login via dev-login → http://localhost:3007/chat-v2 → confirm AppShellV2 sidebar visible + rounded buttons + slate base + Card surfaces
- [ ] **`approval-card.spec.ts` investigation** — open DevTools on `/governance` (or whichever route uses `ApprovalCard`); inspect a CRITICAL-risk badge; record `getComputedStyle().color` value pre-fix vs post-fix. Document in progress.md Day 1 + retro Q3.
  - Pre-fix expected: `rgb(0,0,0)` or other UA default (since `text-[#b71c1c]` arbitrary class emitted nothing)
  - Post-fix expected: `rgb(183, 28, 28)` (= `#b71c1c`)
- [ ] **`npm run e2e -- chat-v2/`** → 10/10 pass (chat-v2 regression sentinel — must stay green)
- [ ] **`npm run e2e`** (full suite) → expected: 40 pass / 7 skip / 0 fail; **EXCEPT** `visual-regression.spec.ts` is expected to **FAIL 6/6** (baselines are pre-fix). Document split: `e2e-functional 34/0 fail` + `visual-regression 6/6 fail (expected, trigger for US-B2)`
- [ ] **Day 1 commit** `feat(sprint-57-17, Day 1): US-A1 v4 directive fix + US-B1 start e2e + DevTools investigation`

---

## Day 2 — US-B1 completion (a11y + manual 11-route) + US-B2 (visual baseline regen workflow_dispatch)

### 2.1 US-B1: a11y re-run + manual 11-route Playwright MCP screenshot
- [ ] **`npm run e2e -- a11y/a11y-scan.spec.ts`** → expect **0 NEW violations vs 57.16 baseline** (which had 4 moderate/minor on `/chat-v2`: `heading-order` / `landmark-main-is-top-level` / `landmark-no-duplicate-main` / `landmark-unique` + `/auth/callback?error` `page-has-heading-one`). Observe if landmark detection IMPROVES post-fix (working AppShellV2 main grid + sidebar `<aside>` semantics could resolve duplicate-main)
- [ ] **Manual Playwright MCP screenshot 11 routes** — `/` + `/auth/login` + 9 gated routes (after dev-login) — confirm each renders shadcn-styled. Attach to `claudedocs/4-changes/feature-changes/CHANGE-001-tailwind-v4-hotfix-screenshots.md` with side-by-side pre/post comparison

### 2.2 US-B2: visual baseline regeneration via 57.14 workflow_dispatch
- [ ] **`gh workflow run playwright-e2e.yml --ref feature/sprint-57-17-tailwind-v4-hotfix`** → trigger Linux-runner-only baseline regen via the `visual-baseline` job (D-PRE-2 corrected — single workflow file with 2 jobs, manual dispatch picks `visual-baseline` only)
- [ ] **`gh run list --workflow=playwright-e2e.yml --limit 1`** → wait for completion (~3-5 min CI time)
- [ ] **`gh pr view <auto-opened-PR>`** → review the 6 regenerated PNGs; manual inspection: AppShellV2 sidebar visible / shadcn rounded buttons / Card surfaces / proper `font-sans` (not UA Times-Roman) / slate base
- [ ] **Merge baseline-regen PR into feature branch** — `gh pr merge <pr-number> --merge` (NOT into main; merges into `feature/sprint-57-17-tailwind-v4-hotfix`)
- [ ] **`git pull origin feature/sprint-57-17-tailwind-v4-hotfix`** → sync feature branch with merged baselines

### 2.3 US-B1 completion: re-run visual-regression against new baselines
- [ ] **`npm run e2e -- visual-regression.spec.ts`** → expect 6/6 pass (new baselines now match real shadcn-styled rendering)
- [ ] **`npm run e2e`** (full suite final) → 40 pass / 7 skip / 0 fail (or document any residual delta + open follow-up AD)
- [ ] **Day 2 commit** `test(sprint-57-17, Day 2): US-B1 a11y + manual screenshots + US-B2 baseline regen merged`

---

## Day 3 — US-C1: retrospective + memory + doc syncs + PR

### 3.1 US-C1: retrospective.md (Q1-Q7)
- [ ] **`docs/03-implementation/agent-harness-execution/phase-57/sprint-57-17/retrospective.md`** — Q1 (what shipped) / Q2 (calibration ratio actual/committed — first data point for `frontend-css-engine-hotfix`) / Q3 (dead-directive root cause investigation detail + `approval-card.spec.ts` pre/post-fix behaviour comparison) / Q4 (follow-up ADs: AD-Tailwind-v4-Config-Migration / AD-Style-Token-Config-Audit visibility update / AD-A11y-Structural-Nits re-evaluation / AD-Lighthouse-Visual-Hard-Gate now actionable) / Q5 (what worked well) / Q6 (what to improve next sprint) / Q7 (cross-cutting lessons — extend Sprint 57.5 reality-check methodology with computed-style spot-check)

### 3.2 US-C1: memory snapshot
- [ ] **`memory/project_phase57_17_tailwind_v4_hotfix.md`** — one-page summary (root cause / fix / blast radius / 4 follow-up ADs)
- [ ] **`memory/MEMORY.md`** — index +1 line under "Project — Recent Sprints (Phase 57+)" section (newest at top)

### 3.3 US-C1: in-sprint doc syncs
- [ ] **`agent-harness-planning/16-frontend-design.md`** — Sprint Timeline row +1 (Sprint 57.17 / AD-Tailwind-v4-Directive-Hotfix / 1-line CSS fix + full validation)
- [ ] **`.claude/rules/sprint-workflow.md`** — Calibration matrix +1 row (`frontend-css-engine-hotfix` 0.60 1st app — `57.17 = <ratio>`)
- [ ] **`agent-harness-execution/phase-57/sprint-57-13/retrospective.md`** — cross-reference note: "Frontend Foundation 1/N design-system layer (US-B3) is now actually running post-Sprint 57.17 hotfix; pre-57.17 it was paper-shipped only"
- [ ] **`STYLE.md §2`** — observation note: post-fix, the tokens IN `tailwind.config.ts` (background/foreground/primary/secondary/destructive/muted) now WORK; the documented-but-missing tokens (success/warning/danger/card/accent/thinking/tool/memory) still no-op → AD-Style-Token-Config-Audit promoted to top of Phase 57.18 候選
- [ ] **`frontend/CONVENTION.md §10`** — if not yet documented, add Tailwind v4 directive guidance (the `@import "tailwindcss"; @config "...";` pattern is the project standard)

### 3.4 US-C1: doc syncs (deferred post-merge — separate `chore/closeout-57-17` PR)
- [ ] **`CLAUDE.md`** — Phase 12/N → 14/N counter + Latest/Prev Sprint row + main HEAD + Next Phase 候選 row (promote AD-Lighthouse-Visual-Hard-Gate to top now that baselines reliable; add AD-Tailwind-v4-Config-Migration as new candidate) + footer
- [ ] **`claudedocs/6-ai-assistant/prompts/SITUATION-V2-SESSION-START.md`** — §第八部分 carryover update + NEW "session-start sanity check" warning: "open http://localhost:3007/ + DevTools in browser before claiming frontend state; e2e + a11y + visual-regression pass does NOT guarantee runtime UI"

### 3.5 Day 3 progress entry + commit
- [ ] **`docs/03-implementation/agent-harness-execution/phase-57/sprint-57-17/progress.md`** — Day 3 entry summarizing US-C1 work
- [ ] **Day 3 commit** `chore(sprint-57-17, Day 3): closeout — retro + memory + in-sprint doc syncs`

### 3.6 US-C1: PR open + CI smoke
- [ ] **`gh pr create --base main --title "Sprint 57.17 — AD-Tailwind-v4-Directive-Hotfix..."`** — body lists 5 deliverables (US-A1+B1+B2+C1 + post-merge sync deferred); attaches CHANGE-001 screenshots
- [ ] **Watch CI** — expect all 5 required checks green (backend-ci / V2-Lint / playwright-e2e / frontend-lint / frontend-build)
- [ ] **User confirms squash-merge** (per Sprint 53.2 solo-dev policy `enforce_admins=true` / `review_count=0` — user is sole approver)

### 3.7 Post-merge `chore/closeout-57-17` PR (deferred)
- [ ] After 57.17 PR merges into main → branch `chore/closeout-57-17-doc-sync` from new main; apply §3.4 deferred doc syncs (CLAUDE.md + SITUATION); open + merge

---

## 重要備註

### Rolling planning 紀律自檢（每 day 結束 + Day 3 closeout 必檢）
- [ ] Day 0 closing: confirm no future-sprint plan files pre-written (`phase-57-frontend-saas/sprint-57-18*` should NOT exist)
- [ ] Day 1 closing: confirm scope creep contained (no edits outside `frontend/src/index.css` + `vite.config.ts` header)
- [ ] Day 2 closing: confirm baseline-regen PR is sub-PR (merging into feature branch, NOT main)
- [ ] Day 3 closing: confirm retro Q6 lists at most 1-2 future sprint candidates (NOT a 5-sprint pre-plan)

### Scope 控管（single-line CSS config hotfix sprint）
- [ ] Out-of-scope changes detected during execution → log as D-DAY-N findings in progress.md, defer to post-merge AD
- [ ] If `@config` directive doesn't resolve `tailwind.config.ts` correctly → execute roll-back plan (plan §Risk matrix) + open AD-Tailwind-v4-Full-Migration as immediate replacement sprint (don't try to in-place fix in 57.17)

### V2 紀律 9 項自檢（每 commit + 每 PR — per plan §Acceptance Criteria）
- [ ] AP-4 Potemkin: this sprint CLOSES a Potemkin (design system shipped but never ran)
- [ ] AP-10 Mock-vs-Real Divergence: this sprint CLOSES a divergence (e2e mocks passed on broken-CSS; real browser revealed truth)
- [ ] Other 9 APs: N/A (frontend config change, no backend / no LLM / no DB / no naming versioning)

### Sprint 57.x cascade lessons 強制執行
- [ ] Lesson #1: e2e + a11y + visual-regression pass ≠ runtime UI works. Sprint 57.17 retro Q7 must propose a "computed-style spot-check" addition to V2 Reality Check methodology (Sprint 57.5 template, if it exists)
- [ ] Lesson #2: Design system install sprints must include a "open the page in a real browser and look at it" deliverable. Update CONVENTION.md §10 if appropriate
- [ ] Lesson #3: SITUATION-V2-SESSION-START.md §6 "doc-level rolling discipline" extends to design-system installs — don't claim US-B1 "COMPLETE" until manually verified in browser

### Open Items / Carry-forward（待填入 retrospective Q4）
- AD-Tailwind-v4-Config-Migration (NEW from this sprint) — full v4 idiomatic `@theme inline` migration; deletes `tailwind.config.ts`; ~6-8 hr standalone sprint
- AD-Style-Token-Config-Audit (57.16 carryover — now actionable post-fix; promotes to Phase 57.18 候選 top slot)
- AD-A11y-Structural-Nits (57.16 carryover — re-evaluate post-fix; landmark issues may auto-resolve)
- AD-Lighthouse-Visual-Hard-Gate (57.15+57.16 carryover — baselines now reliable, can flip to required CI check)
