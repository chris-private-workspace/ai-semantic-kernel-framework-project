# Sprint 57.28 — Checklist (AD-Mockup-Fidelity-Foundation-Switch)

[Link to plan](./sprint-57-28-plan.md)

**Class**: `frontend-verbatim-css-foundation` 0.55 (NEW class; 1st application; HYBRID weighted blend)
**Workload**: Bottom-up ~11.0 hr → calibrated commit ~6.2 hr (multiplier 0.55)
**Day count**: 5 (Day 0 setup + guidance-PR merge + 三-prong + before-baseline / Day 1 Layer 2+3 / Day 2 Layer 4 + theme / Day 3 CI guards + 22-route sweep / Day 4 Vitest + closeout)
**1st-data-point watch**: Day 4 retro Q2 records actual/committed ratio as the NEW class's 1st data point; KEEP 0.55 regardless (1 data point insufficient to adjust per 3-sprint window rule)
**Scope decision**: Option B (user-approved 2026-05-22) — foundation-only; per-page re-point = Phase 2 epic

---

## Day 0 — Plan + Checklist + guidance-PR merge + 三-prong + before-baseline (2026-05-22)

### 0.1 Plan + Checklist
- [x] **Plan drafted** at `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-28-plan.md` — 11-section structure mirror Sprint 57.26; user-approved 2026-05-22 (incl. Option B scope decision)
- [x] **Checklist drafted** at `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-28-checklist.md` — Day 0-4 structure

### 0.2 guidance-PR merge + branch
- [x] **`chore/frontend-mockup-fidelity-guidance` PR opened** — PR #161 (`19f31443`, 22 docs/rules files; 0 source code)
- [x] **guidance PR CI green + merged to main** — branch was BEHIND (PR #160 Sprint 57.27 merged in interim) → merged `origin/main` in (0 conflict) → 8/8 CI checks green → squash-merged to main `d4461141`; remote branch deleted
- [x] **Feature branch cut from updated main** — `feature/sprint-57-28-mockup-fidelity-foundation` from main `d4461141`

### 0.3 Day 0 三-prong (Prong 1 path + Prong 2 content/collision + Prong 4 test selector)
- [x] **Prong 1 Path verify** — 0 path drift; `index.css`/`main.tsx`/`tailwind.config.ts`/`ThemeProvider.tsx` present (edits); `styles-mockup.css` absent (create); `scripts/route-sweep.mjs` present (reuse); frontend CI = `.github/workflows/frontend-ci.yml`
- [x] **Prong 2 Content verify** — token-collision set enumerated (~28: 2 tricky + ~26 shared-intent — FOUNDATION-SWITCH-REPORT §2); mockup `styles.css` 0 `rem` → `html{font-size:13px}` KEEP (D-PRE-3); D-PRE-1 (mockup HAS light theme) + D-PRE-2 (bg/fg theme-scoped) catalogued
- [x] **Prong 4 Test selector verify** — 4 Vitest files reference theme/token literals: `AuthShell.test.tsx`, `AppShellV2.test.tsx`, `UserMenu.test.tsx`, `adminTenantsRoleGate.test.tsx` (D-PRE-6; Day 4 adapt)
- [x] **Read PoC reference implementation** — `investigation/mockup-fidelity-poc` `main.tsx` imports `./styles-mockup.css` (L46) after `./index.css` (L40); confirms Layer 2 wiring

### 0.4 Day 0 sweep before-baseline + report skeleton
- [x] **Before-baseline sweep** — 22 routes at 1440×900 via `route-sweep.mjs before` → `screenshots/before/` (22 PNGs; all ✓). `route-sweep.mjs` OUT_DIR re-pointed 57.26→57.28 + header MHist
- [x] **FOUNDATION-SWITCH-REPORT skeleton** at `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-28/artifacts/mockup-fidelity-foundation/FOUNDATION-SWITCH-REPORT.md` — 4-layer summary + filled token-collision table + 22-route matrix skeleton + D-PRE catalogue
- [x] **progress.md Day 0** at `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-28/progress.md` — Day 0 entry + 6 D-PRE findings + decisions

### 0.5 Day 0 commit
- [x] **Day 0 commit** — plan + checklist + Day 0 progress + FOUNDATION-SWITCH-REPORT skeleton + route-sweep.mjs re-point (screenshots/ kept local, not committed — per Sprint 57.26 pattern); hash recorded in progress.md
  - Commit message: `chore(sprint-57-28, Day 0): plan + checklist + 三-prong + before-baseline`

---

## Day 1 — Group B+C (Layer 2 + 3 + 4 + theme confirm) — atomic CSS foundation switch (2026-05-22)

> **D-DAY1-1**: Layer 2/3/4 are atomic (mid-state = `hsl(oklch())` invalid CSS app-wide) → Layer 4 (plan Day 2 §2.1) pulled into Day 1. **D-DAY1-2**: 15 files un-translated (user-approved Option X via AskUserQuestion). See progress.md Day 1.

### 1.1 US-B1 Layer 2 — verbatim copy
- [x] **`frontend/src/styles-mockup.css`** = byte-identical copy of `reference/design-mockups/styles.css` (1123 lines; `diff` empty)
- [x] **`main.tsx` import** `./styles-mockup.css` after `./index.css` + never-hand-edit comment + MHist

### 1.2 US-B2 Layer 3 — index.css slim-down
- [x] **Retired mockup-system HSL approximation tokens** from `index.css` (`--bg`/`--fg`/`--success`/.../`--risk-*`/density/`--radius`/`--shadow` — now verbatim from styles-mockup.css); shadcn-system set kept
- [x] **`html{font-size:13px}` KEPT** per D-PRE-3 (mockup `styles.css` is px-only) — transition-safe for the not-yet-re-pointed Tailwind-rem pages
- [x] **`index.css` body block removed** — styles-mockup.css's unlayered `body` fully supersedes it (verified)

### 1.3 US-C1 Layer 4 — tailwind.config bridge rework + token de-collision (pulled into Day 1 per D-DAY1-1)
- [x] **Mockup-token bridge** `hsl(var(--X))`→`var(--X)` in `tailwind.config.ts` (var holds full oklch)
- [x] **Token de-collision** — shadcn `--primary`/`--border` → `--sc-primary`/`--sc-border` (index.css defs + config bridge + `* { border-color }`); shadcn-only tokens unchanged
- [x] **index.html** `data-theme="dark"` added (D-PRE-2 — required for styles-mockup.css `[data-theme][data-variant]` bg/fg to resolve)

### 1.4 D-DAY1-2 un-translation (user-approved Option X)
- [x] **15 files / ~35 occurrences** `hsl(var(--mockup-token))` → `var(--X)` (bulk token-exact sed across charts / fixtures / dashboards / auth pages); 2 alpha cases → mockup `--primary-soft`/`--primary-soft-2`
- [x] **Verified** — sweep confirms cost-dashboard charts + auth backdrops restored; `CostBurnChart`/`ErrorTrendChart` (bare `var()`) became correct automatically

### 1.5 Day 1 verification + commit
- [x] **Spot-check** — 22-route sweep (`route-sweep.mjs after`); cost-dashboard / auth-login screenshot-confirmed; 0 catastrophic breakage
- [x] **Quality gates** — `npm run build` green (3.52s); `npm run lint` clean; Vitest **457/457** (0 regression)
- [x] **Day 1 commit** — Layer 2+3+4 + un-translation
  - Commit message: `feat(frontend, sprint-57-28, Day 1): verbatim-CSS foundation switch — Layer 2+3+4 + hsl(var()) un-translation`

---

## Day 2 — Group C (Layer 4 + theme toggle)

### 2.1 US-C1 Layer 4 — tailwind.config.ts bridge rework — ✅ DONE Day 1 §1.3 (D-DAY1-1 atomic resequencing)
- [x] **Mockup-token bridge** `hsl(var(--X))` → `var(--X)` — done Day 1 §1.3
- [x] **Token collision resolution** — `--primary`/`--border` de-collided → `--sc-primary`/`--sc-border`; build green; 0 invalid-CSS utility — done Day 1 §1.3

### 2.2 US-C2 theme toggle alignment

> **D-PRE-1 / plan §Risks R3**: mockup `styles.css` HAS a full light theme (`[data-theme="light"]` ×4 variants, L113-165). US-C2 is NOT "dark-only" — light + dark both retained (user-confirmed 2026-05-22). Task text corrected per sprint-workflow §Step 2.5; plan R3 row is the audit trail.

- [x] **`ThemeProvider` mockup `[data-theme]` alignment (light + dark both kept)**
  - DoD: `ThemeProvider` drives `<html>` `data-theme` attribute (`dark`↔`light`) — the mockup mechanism `styles-mockup.css` scopes `--bg`/`--fg`/... by `[data-theme][data-variant]`
  - DoD: `.dark` class toggle KEPT in sync during Phase 1 (the 13 not-yet-re-pointed pages still consume `index.css` shadcn `:root`/`.dark` tokens); Phase 2 drops it
  - DoD: `ThemeProvider` public API (`theme`/`toggleTheme`/`setTheme`/`useTheme`) unchanged — NOT deleted; stays as mount point for future `[data-variant]`/`[data-density]`
  - DoD: `index.html` already carries `data-theme="dark"` + `data-variant="linear"` (Day 1 §1.3) — updated only if needed
  - Verify: `/overview` + `/auth/login` render dark by default; theme toggle flips both `data-theme` + `.dark`
- [x] **Day 2 spot-check + commit**
  - DoD: `/overview` + `/cost-dashboard` + `/auth/login` render correctly post-theme-wire
  - Commit message: `feat(frontend, sprint-57-28, Day 2, Group C): theme toggle drives mockup [data-theme] attr (light+dark)`
  - Verify: `git status` clean post-commit

---

## Day 3 — Group D (CI guards + 22-route regression sweep)

### 3.1 US-D1 CI guards
- [x] **`frontend/scripts/check-mockup-fidelity.mjs`** authored
  - DoD: diff guard (`styles-mockup.css` vs `styles.css`, line-ending normalised) + grep guard (no new hardcoded hex/oklch in `features/`+`pages/`) — done; both guards pass
  - DoD: grep guard records the current pre-existing-offender baseline count (Phase-2 backlog); hard-fails only on NEW offenders — `HEX_OKLCH_BASELINE = 18`
  - Verify: `node scripts/check-mockup-fidelity.mjs` exits 0 ✓
- [x] **`package.json` script + CI step**
  - DoD: `+1` `package.json` script `check:mockup-fidelity`; `+1` step `Mockup-fidelity guard` in `.github/workflows/frontend-ci.yml` after the ESLint step
  - Verify: `npm run check:mockup-fidelity` exits 0 ✓

### 3.2 US-D2 after-switch 22-route sweep
- [x] **After-switch sweep** — all 22 routes via `route-sweep.mjs after` (fresh contexts, no cache)
  - DoD: `screenshots/after/` has 22 PNGs — 22/22 captured ✓ (0 harness `✗`)
- [x] **Before/after matrix + vs-mockup note** in FOUNDATION-SWITCH-REPORT
  - DoD: 22-route before/after matrix populated (report §3); per-route vs-`:8080`-mockup pixel comparison deferred to each Phase-2 re-point sprint (Option B — no markup re-pointed this sprint; rationale in report §3c) — corrected per sprint-workflow §Step 2.5
  - Verify: report §3 matrix populated for all 22 routes ✓

### 3.3 US-D3 regression triage
- [x] **Catastrophic breakage fixed in-sprint**
  - DoD: 0 catastrophic breakage from the switch — recorded in report §3a (no route that rendered before is broken after)
- [x] **Transition drift catalogued** as Phase-2 epic backlog
  - DoD: 19 routes 🟡 transition-drift catalogued in report §3 matrix + §3a as the Phase-2 re-point backlog (NOT fixed this sprint)
- [x] **Structural regressions → carryover AD**
  - DoD: 0 structural regression from the switch (no `AD-Foundation-Switch-Regression-*`); 3 routes (`/subagents` `/memory` `/verification`) error identically before+after → pre-existing route-sweep harness mock gap → NEW `AD-RouteSweep-Object-Mock-Gap` (report §3b)
- [x] **Day 3 commit**
  - Commit message: `feat(frontend, sprint-57-28, Day 3, Group D): CI mockup-fidelity guards + 22-route regression sweep + triage`
  - DoD: `git status` clean post-commit

---

## Day 4 — Group E + closeout

### 4.1 US-E1 Vitest + lint + build
- [x] **Token/theme Vitest specs adapted** (per Day-0 Prong 4)
  - DoD: `AuthShell.test.tsx` ThemeProvider test strengthened with `data-theme` assertions (Day 2 §2.2); the other 3 D-PRE-6 specs (`AppShellV2`/`UserMenu`/`adminTenantsRoleGate`) only wrap render in `<ThemeProvider>` — assert no retired token / light path → no change needed
- [x] **Vitest 457/457 passing** (post-Sprint-57.27 baseline preserved; 0 regression — checklist Day-0 number "430" was the plan-time figure; 57.27 added +27)
  - Verify: `npm run test` exit 0 ✓
- [x] **`npm run lint` exit 0 + `npm run build` green + bundle KB delta recorded**
  - DoD: lint silent ✓; build green ✓ (main JS 337.06 kB; CSS bundle 592 KB incl. verbatim `styles-mockup.css` ~39 KB raw — matches plan "~40 KB CSS")

### 4.2 US-E2 FOUNDATION-SWITCH-REPORT final + closeout
- [x] **FOUNDATION-SWITCH-REPORT final verdict** + Phase-2 epic backlog (report §5)
- [x] **retrospective.md Q1-Q7** at `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-28/retrospective.md`
  - DoD: Q2 records ratio actual/committed ≈1.05 = 1st data point for NEW `frontend-verbatim-css-foundation` class
- [x] **memory snapshot** `memory/project_phase57_28_mockup_fidelity_foundation.md` + **MEMORY.md +1 quality pointer**
- [x] **`.claude/rules/sprint-workflow.md` calibration matrix +1 NEW class row**
  - DoD: `frontend-verbatim-css-foundation` 0.55 row with 1st data point `57.28≈1.05` + MHist entry
- [x] **`claudedocs/1-planning/next-phase-candidates.md` update**
  - DoD: Sprint 57.28 carryover section + #45 `AD-RouteSweep-Object-Mock-Gap` + #46 `AD-Mockup-Fidelity-HexBaseline-Migration`
- [x] **CLAUDE.md Current Sprint row + Last Updated footer** (REFACTOR-001 §Sprint Closeout minimal touch — NO history additions)
- [x] **Day 4 commit** closeout
  - Commit message: `feat(frontend, sprint-57-28, Day 4): closeout — FOUNDATION-SWITCH-REPORT final + retrospective + calibration matrix NEW class + minimal CLAUDE.md touch`
  - DoD: `git status` clean post-commit

### 4.3 PR open + CI + merge
- [ ] **PR open** with body (Sprint 57.28 scope + 4-layer switch + token-collision resolution + dark-only theme + 22-route sweep result + NEW calibration class + browser-cache hard-refresh verification note)
- [ ] **CI green**: all required checks pass (backend-ci fires — PR touches `.github/workflows/**`)
- [ ] **Merge** (after CI green + user approval; squash per Sprint 57.23-57.26 pattern)
- [ ] **Post-merge cleanup**: local + remote feature branch delete

---

## Key Decisions Required During Sprint

| Decision Point | When | Default |
|----------------|------|---------|
| `html{font-size:13px}` hack: keep through Phase 1 vs retire now | Day 0 Prong 2 grep → Day 1.2 | KEEP if mockup `styles.css` is px-only (transition-safe); retire only if mockup uses `rem` |
| Token name collision: de-collide (rename shadcn var) vs let verbatim win | Day 2.1 per Day-0 enumeration | shadcn-only collision → rename shadcn var; shared-intent collision → verbatim wins |
| Theme: dark-only vs retain light mode | **Plan approval** + Day 2.2 | Dark-only (mockup has no light design; production dark-default since 57.21). If user wants light retained = explicit "build beyond mockup" scope addition — raise at plan approval |
| `styles-mockup.css` header comment vs pure byte-identical | Day 1.1 | Pure byte-identical (diff guard); never-edit notice lives in `main.tsx` import comment |
| Sweep regression: in-sprint fix vs catalogue vs carryover AD | Day 3.3 | Catastrophic → fix in-sprint; transition drift → catalogue (Phase-2 backlog); structural → carryover AD |
| guidance PR backend-ci paths-filter skip | Day 0.2 | Touch `.github/workflows/backend-ci.yml` header per documented workaround, or PR-body note |

---

**Plan + checklist drafted**: 2026-05-22 Day 0
**Class**: `frontend-verbatim-css-foundation` 0.55 (NEW class; 1st application)
**Target close**: 5 working days from Day 0 commit to PR merged
