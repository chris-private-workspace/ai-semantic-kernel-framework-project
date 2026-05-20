# Sprint 57.26 — Checklist (AD-Foundation-Fidelity-Token-Correction)

[Link to plan](./sprint-57-26-plan.md)

**Class**: `frontend-foundation-token-correction` 0.55 (NEW class; 1st application; HYBRID weighted blend)
**Workload**: Bottom-up ~6.4 hr → calibrated commit ~3.5 hr (multiplier 0.55)
**Day count**: 4 (Day 0 setup + 三-prong + baseline / Day 1 token correction / Day 2 22-route sweep / Day 3 closeout)
**1st-data-point watch**: Day 3 retro Q2 records actual/committed ratio as the NEW class's 1st data point; KEEP 0.55 regardless (1 data point insufficient to adjust per 3-sprint window rule)

---

## Day 0 — Plan + Checklist + 三-prong + baseline capture (2026-05-20)

### 0.1 Plan + Checklist + Branch
- [x] **Plan drafted** at `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-26-plan.md`
  - DoD: 13-section structure mirror Sprint 57.25 (Sprint Goal / Background / User Stories / Technical Spec / File Change List / Acceptance Criteria / Deliverables / Risks / Workload / Day plan)
  - Verify: file exists; sections present
- [x] **Checklist drafted** at `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-26-checklist.md`
  - DoD: Day 0-3 structure; per-task DoD + Verify command; sub-bullets 3-6 per task
  - Verify: this file exists
- [x] **Branch creation** from main `08f762fa`
  - DoD: `git checkout -b feature/sprint-57-26-foundation-fidelity`
  - Verify: `git branch --show-current` → `feature/sprint-57-26-foundation-fidelity`
- [x] **FOUNDATION-DRIFT-REPORT skeleton** at `claudedocs/4-changes/sprint-57-26-foundation-fidelity/FOUNDATION-DRIFT-REPORT.md`
  - DoD: file with 5-foundation-drift table + ~22-route before/after matrix skeleton
  - Verify: file exists
- [x] **progress.md Day 0** at `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-26/progress.md`
  - DoD: Day 0 entry with 三-prong findings + baseline sweep ref
  - Verify: file exists

### 0.2 Day 0 三-prong (Prong 1 path + Prong 2 content + Prong 4 test selector)
- [x] **Prong 1 Path verify**: foundation files exist as plan assumes
  - DoD: `index.css` / `AppShellV2.tsx` / `AuthShell.tsx` / `tailwind.config.ts` all present (creates: none; edits: all 4)
  - Verify: `Glob` each path → 1 result
- [x] **Prong 2 Content verify**: 5 foundation drifts confirmed in source + arbitrary-px audit
  - DoD: confirm `index.css` body block has NO `font-size`; `--radius: 0.5rem` present; `AppShellV2` has `grid-cols-[240px_1fr]` + `bg-background text-foreground` + `<main> p-6`
  - DoD: D-PRE catalogued — grep shell + high-traffic components for Tailwind arbitrary-px (`w-[NNNpx]` / `h-[NNNpx]` / `text-[NNpx]`) that will NOT rem-scale (R4)
  - DoD: D-PRE — check the 3 rebuilt routes (auth/cost/sla) for rem-utility vs px-arbitrary usage (R1)
  - Verify: `Grep("font-size", index.css)` + `Grep("\\[\\d+px\\]", frontend/src/components)` + read 3 rebuilt-route components
- [x] **Prong 4 Test selector verify**: shell/layout Vitest specs asserting literal foundation values
  - DoD: D-PRE catalogued — which specs assert `240px` / `p-6` / `bg-background` / `grid-cols`
  - Verify: `Grep("240px|p-6|bg-background|grid-cols-\\[", frontend/tests)` + list affected specs

### 0.3 Day 0 sweep harness + before-baseline
- [x] **`frontend/scripts/route-sweep.mjs`** standalone Playwright sweep harness
  - DoD: 1440×900; mocked `/api/v1/auth/me` (admin) + empty-200 for other `/api/v1/`; screenshots all ~22 routes to a parametrised out-dir (before/ vs after/)
  - DoD: placed in `frontend/scripts/` per V2 file-organization (NOT repo root)
  - Verify: `node scripts/route-sweep.mjs before` produces ~22 PNGs in `screenshots/before/`
- [x] **Before-baseline sweep** — all ~22 routes captured
  - DoD: `claudedocs/4-changes/sprint-57-26-foundation-fidelity/screenshots/before/` has ~22 PNGs
  - Verify: directory listing count ≈ 22

### 0.4 Day 0 commit
- [ ] **Day 0 commit** with plan + checklist + Day 0 progress + DRIFT-REPORT skeleton + sweep harness + before-baseline
  - Commit message: `chore(sprint-57-26, Day 0): plan + checklist + 三-prong + route-sweep harness + before-baseline`
  - DoD: `git status` clean post-commit; commit hash recorded in progress.md
  - Verify: `git log --oneline -1`

---

## Day 1 — Group B (token correction + shell alignment) (2026-05-21)

### 1.1 US-B1 font-size approach spike + decision
- [ ] **Approach spike**: capture `/overview` + `/cost-dashboard` + `/auth/login` at `html { font-size: 13px }` vs `81.25%`
  - DoD: 6 screenshots compared vs mockup proportion; pick A (`13px`) or B (`81.25%`)
  - DoD: decision + reason recorded in progress.md Day 1
  - Verify: progress.md Day 1 §approach decision present
- [ ] **`index.css` font-size baseline applied**
  - DoD: `@layer base` gains `html { font-size: <chosen> }`; body block keeps inherit or explicit `13px`
  - Verify: `Grep("font-size", index.css)` shows the new rule

### 1.2 US-B1 rem→px design token correction
- [ ] **`--radius` rem→px** in `index.css` `:root` + `.dark`
  - DoD: `--radius: 0.5rem` → `--radius: 8px` (mockup `styles.css:29`); any other rem-valued custom prop from Prong 2 audit converted
  - Verify: `Grep("--radius", index.css)` shows `8px`; `npm run build` green
- [ ] **`tailwind.config.ts` borderRadius audit**
  - DoD: `borderRadius.md/sm` `calc(var(--radius) - Npx)` confirmed px-arithmetic-safe with px `--radius` (likely no change)
  - Verify: read `tailwind.config.ts` borderRadius block

### 1.3 US-B2 AppShellV2 shell alignment
- [ ] **Sidebar grid column** `grid-cols-[240px_1fr]` → `grid-cols-[232px_1fr]`
  - DoD: matches mockup `styles.css:200` `.app` grid
- [ ] **Root background tokens** `bg-background text-foreground` → `bg-bg text-fg`
  - DoD: shell root consumes mockup token tree (hue consistency)
- [ ] **`<main>` padding** `p-6` → mockup-faithful inset (Option B)
  - DoD: measure mockup `#overview` inner page-gutter; apply measured value; record in progress.md
  - DoD: `fullBleed` prop path (Sprint 57.21 chat-v2) unchanged
  - Verify: `/overview` main content inset matches mockup at 1440×900

### 1.4 US-B3 AuthShell + index.css body
- [ ] **`AuthShell.tsx` backdrop** radial-gradient base `--background` → `--bg` if drifted
  - DoD: `/auth/*` family backdrop hue consistent with authed routes
- [ ] **`index.css` body block** `font-family` token form + `line-height: 1.45` (mockup `styles.css:185`)
  - DoD: body block aligned to mockup

### 1.5 Day 1 spot-check + commit
- [ ] **Spot-check sweep** `/overview` + `/auth/login` + `/cost-dashboard` post-correction
  - DoD: 3 routes visually closer to mockup; no obvious breakage
- [ ] **Day 1 commit** with Group B work
  - Commit message: `feat(frontend, sprint-57-26, Day 1, Group B): font-size baseline + rem→px tokens + AppShellV2 + AuthShell foundation alignment`
  - DoD: `git status` clean post-commit

---

## Day 2 — Group C (22-route regression sweep) (2026-05-22)

### 2.1 US-C1 after-correction sweep + before/after diff
- [ ] **After-correction sweep** — all ~22 routes via `route-sweep.mjs after`
  - DoD: `screenshots/after/` has ~22 PNGs
  - Verify: directory count ≈ 22
- [ ] **Before/after diff catalogued** in FOUNDATION-DRIFT-REPORT
  - DoD: per-route row — change classified intended-improvement vs unintended-regression
  - Verify: DRIFT-REPORT before/after matrix populated for all ~22 routes

### 2.2 US-C2 after vs mockup comparison
- [ ] **Mockup-equivalent sweep** — `:8080/#<route>` for routes with a mockup counterpart
  - DoD: `screenshots/mockup/` captures; routes without a mockup counterpart noted
- [ ] **After vs mockup matrix** in FOUNDATION-DRIFT-REPORT
  - DoD: per-route — which foundation drift dimensions resolved (font / sidebar / padding / hue) + residual per-route content drift noted as epic backlog
  - Verify: DRIFT-REPORT vs-mockup matrix populated

### 2.3 US-C3 regression triage + iterate
- [ ] **Cosmetic regressions iterated** to parity (Tailwind class tweaks)
  - DoD: each cosmetic regression from US-C1 fixed in-sprint; re-screenshot confirms
- [ ] **Structural regressions logged** as carryover ADs
  - DoD: any structural regression (esp. the 3 rebuilt routes per R1) → `next-phase-candidates.md` carryover AD; NOT shipped silently
  - Verify: structural regressions list in DRIFT-REPORT + carryover ADs added

### 2.4 Day 2 commit
- [ ] **Day 2 commit** with sweep results + cosmetic fixes
  - Commit message: `feat(frontend, sprint-57-26, Day 2, Group C): 22-route regression sweep + before/after + vs-mockup matrix + cosmetic parity fixes`
  - DoD: `git status` clean post-commit

---

## Day 3 — Group D + closeout (2026-05-23)

### 3.1 US-D1 Vitest + lint + build
- [ ] **Shell/layout Vitest specs adapted** for new foundation dimensions
  - DoD: specs asserting `240px`/`p-6`/`bg-background` updated to `232px`/new-inset/`bg-bg` (adapt NOT delete)
- [ ] **Vitest 430/430 passing** (Sprint 57.25 baseline preserved; 0 regression)
  - Verify: `npm run test` exit 0
- [ ] **`npm run lint` exit 0** + **`npm run build` green** + bundle KB delta recorded
  - DoD: bundle delta ≈ 0 (CSS + shell-only); recorded in progress.md

### 3.2 US-D2 FOUNDATION-DRIFT-REPORT final
- [ ] **Final per-route verdict** = FOUNDATION-PARITY (baseline aligned; residual content drift noted)
  - DoD: all ~22 routes have a verdict
- [ ] **Epic-backlog list** — routes still needing `frontend-mockup-strict-rebuild` treatment
  - DoD: accurate remaining-route list for the epic
- [ ] **`frontend/diagnose-render.mjs` deleted** (superseded by `scripts/route-sweep.mjs`)
  - Verify: `Glob("frontend/diagnose-render.mjs")` → 0 results

### 3.3 US-D3 Retrospective + memory + closeout
- [ ] **retrospective.md Q1-Q7** at `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-26/retrospective.md`
  - DoD: Q2 records actual/committed ratio = 1st data point for NEW `frontend-foundation-token-correction` class
- [ ] **memory snapshot** `memory/project_phase57_26_foundation_fidelity.md`
  - DoD: distinguishing features + verdicts + metrics + keywords per quality-pointer principle
- [ ] **MEMORY.md +1 quality pointer line** (~300 char; topic + keywords + subfile link)
- [ ] **`.claude/rules/sprint-workflow.md` calibration matrix +1 NEW class row**
  - DoD: `frontend-foundation-token-correction` 0.55 row with 1st data point `57.26=<ratio>` + MHist entry
- [ ] **`claudedocs/1-planning/next-phase-candidates.md` update**
  - DoD: foundation-fidelity item closed; epic-backlog routes referenced; any R1 structural-regression carryover added
- [ ] **CLAUDE.md Current Sprint row + Last Updated footer** (REFACTOR-001 §Sprint Closeout minimal touch — NO history additions)
- [ ] **Day 3 commit** closeout
  - Commit message: `feat(frontend, sprint-57-26, Day 3): closeout — FOUNDATION-DRIFT-REPORT final + retrospective + calibration matrix NEW class + minimal CLAUDE.md touch`
  - DoD: `git status` clean post-commit

### 3.4 PR open + CI + merge
- [ ] **PR open** with body (Sprint 57.26 scope + 5 foundation drifts corrected + 22-route sweep result + NEW calibration class + browser-cache hard-refresh verification note)
- [ ] **CI green**: backend-ci (paths-filter — note if skipped) / frontend lint / Vitest / Playwright / a11y / visual-regression
- [ ] **Merge** (after CI green + user approval; squash per Sprint 57.23-57.25 pattern)
- [ ] **Post-merge cleanup**: local + remote branch delete

---

## Key Decisions Required During Sprint

| Decision Point | When | Default |
|----------------|------|---------|
| Font-size approach: `html { font-size: 13px }` (A) vs `81.25%` (B) | Day 1.1 spike | A (`13px`) — explicit; switch to B only if spike shows accessibility reason |
| `<main>` padding: drop to `p-0` + per-page wrappers (Option A, ~19 files) vs shell-local corrected inset (Option B) | Day 1.3 | Option B (shell-local; single measured inset value) |
| 3 rebuilt routes (auth/cost/sla) regression handling | Day 2.3 | Cosmetic → iterate in-sprint; structural → carryover `AD-Rebuilt-Route-Refidelity` (do NOT silently ship) |
| Routes without a mockup counterpart (PROP stubs) | Day 2.2 | vs-mockup comparison skipped; before/after regression check still applies |
| backend-ci paths-filter skip (frontend-only PR) | Day 3.4 | PR body note; or touch `.github/workflows/backend-ci.yml` header per documented workaround |

---

**Plan + checklist drafted**: 2026-05-20 Day 0
**Class**: `frontend-foundation-token-correction` 0.55 (NEW class; 1st application)
**Target close**: 2026-05-23 (4 working days from Day 0 commit to PR merged)
