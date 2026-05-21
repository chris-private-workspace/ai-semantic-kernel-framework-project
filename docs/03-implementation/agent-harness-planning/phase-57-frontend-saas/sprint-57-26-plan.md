---
sprint: 57.26
phase: Phase 57+ Frontend SaaS 22/N (pending close)
title: AD-Foundation-Fidelity-Token-Correction — Global Token Baseline Alignment + 22-Route Regression Sweep
class: frontend-foundation-token-correction 0.55 (NEW class; 1st application; HYBRID weighted blend — css-token-edit ×0.60 ~25% + 22-route regression sweep ×0.50 ~50% + shell-component edit ×0.50 ~15% + closeout ×0.80 ~10% ≈ 0.55)
duration_days: 4 (Day 0 setup + 三-prong + baseline capture / Day 1 token correction + shell alignment / Day 2 22-route regression sweep / Day 3 closeout)
related:
  - Sprint 57.25 plan + retrospective (frontend-mockup-strict-rebuild 0.60 class 3rd app; sla-dashboard rebuild)
  - Sprint 57.20 plan (Option W frontend-leads / backend-follows; mockup token tree `--bg/--bg-1/...` first added)
  - Sprint 57.18 plan (mockup-integration-foundation; semantic + risk tokens; first token wiring — incomplete font-size baseline)
  - Sprint 57.17 plan (frontend-css-engine-hotfix; Tailwind v4 directive hotfix — closest prior class)
  - Sprint 57.22 AUDIT-REPORT-COMPREHENSIVE.md (41-route mockup-fidelity audit; foundation drift NOT separately scoped — this sprint fills that gap)
  - CLAUDE.md §Frontend Mockup-Fidelity Hard Constraint (2026-05-17)
  - reference/design-mockups/styles.css:1-210 (canonical foundation tokens — :root + .app + body)
  - .claude/rules/sprint-workflow.md §Scope-class multiplier matrix
  - .claude/rules/sprint-workflow.md §Step 2.5 (Day-0 verify three-prong)
  - claudedocs/4-changes/sprint-57-25-sla-dashboard-rebuild/compare-overview-{prod,mockup}.png (drift evidence captured 2026-05-20)
---

# Sprint 57.26 — AD-Foundation-Fidelity-Token-Correction

## Sprint Goal

Align the **global foundation tokens** (root font-size baseline, shell layout dimensions, shell background tokens, rem-based design tokens) of the production frontend to mockup `reference/design-mockups/styles.css` so that **every one of the ~22 already-shipped routes** inherits a mockup-faithful visual **baseline** (font scale / sidebar width / main padding / background hue) — then **sweep all routes with a before/after + vs-mockup regression check** to confirm no breakage. This sprint corrects the **foundation layer only**; per-route content rebuild remains the scope of the `frontend-mockup-strict-rebuild` epic (Sprint 57.23+).

**Two-line philosophy**:

1. **Fix the foundation, not the pages** — the drift the user reported on 2026-05-20 (font too large, main content mis-positioned, background hue off) is NOT a per-page bug; it is a **shared foundation gap** left by Sprint 57.18 (`mockup-integration-foundation` wired the token *tree* but never set the `13px` body baseline) + Sprint 57.20 (shell rewrite kept shadcn `bg-background` + `240px` sidebar + `p-6` main). One foundation correction fixes the baseline for all 22 routes at once.
2. **Sweep to prove no regression** — changing `html` font-size has a 22-route blast radius. Every route gets a 1440×900 screenshot before vs after the correction, plus an after vs mockup-equivalent comparison; cosmetic regressions are iterated in-sprint, structural ones become carryover ADs (NOT silently shipped).

## Background

### Why Sprint 57.26 (this sprint)

After Sprint 57.25 (`/sla-dashboard` rebuild) merged (PR #158 → main `08f762fa`), the user compared production routes against the `:8080` mockup server and reported visual drift on `/overview` and `/auth/login`: font type/size/colour mismatch + main-content positioning mismatch. A standalone Playwright probe (`claudedocs/4-changes/sprint-57-25-sla-dashboard-rebuild/compare-overview-{prod,mockup}.png`) confirmed the "not centered / not full-screen" report was browser-cache staleness (production code correct) — but **objectively measured 4 real foundation drifts**:

| # | Foundation token | Production (current) | Mockup `styles.css` | Visual consequence |
|---|------------------|----------------------|---------------------|--------------------|
| 1 | body / root font-size baseline | `16px` (browser default — `index.css` body block never sets `font-size`) | `13px` (`styles.css:184`) | All text ~23% larger; every Tailwind rem-based utility (`text-*` / `p-*` / `gap-*`) inflated → loose, oversized layout across all 22 routes |
| 2 | shell `<main>` padding | `p-6` = `24px` (`AppShellV2.tsx:115`) | `.main` padding `0` (`styles.css:208`; inner page wrapper owns padding) | Right-side main content offset inward vs mockup |
| 3 | sidebar grid column width | `240px` (`AppShellV2.tsx:102` `grid-cols-[240px_1fr]`) | `232px` (`styles.css:200` `.app` grid `232px 1fr`) | Left rail 8px too wide on every authed route |
| 4 | shell background tokens | `bg-background` / `text-foreground` (shadcn token — dark `hsl(222 84% 4.9%)` blue-black) | `--bg` token tree (mockup `--bg` neutral-grey) | Whole-page base hue too blue / too dark |
| 5 | `--radius` base token | `0.5rem` (`index.css:51` — rem-based; will be scaled by the font-size fix) | `8px` (`styles.css:29` — px-based) | After fix #1, `0.5rem` resolves to 6.5px not 8px → radius drifts smaller; rem-based tokens must convert to px |

Mockup good news already in place: density tokens `--row-h:36px / --pad:14px / --gap:10px` (Sprint 57.20) **already match** mockup `styles.css:26-28`; the mockup `--bg`/`--bg-1`/... token tree exists (Sprint 57.20) — it is just **not consumed by the shell root**.

**Σ bottom-up**: ~6.4 hr (mid) before calibration
**Calibrated commit**: ~6.4 hr × 0.55 ≈ ~3.5 hr (NEW class baseline)

### Why a foundation sprint (not folded into the rebuild epic)

The Sprint 57.23+ `frontend-mockup-strict-rebuild` epic rebuilds routes **one at a time**. If the font-size / shell baseline is wrong, every rebuild sprint builds on a wrong base and must locally compensate — drift compounds. Correcting the foundation **once, before** the bulk of the epic runs, means every subsequent rebuild starts from a mockup-faithful base. Three routes (57.23 auth / 57.24 cost-dashboard / 57.25 sla-dashboard) are already rebuilt; they are re-verified in the Day 2 sweep (R1).

### Class baseline — NEW class `frontend-foundation-token-correction` 0.55

No prior class fits cleanly:
- `frontend-css-engine-hotfix` 0.60 (Sprint 57.17) — closest, but that was a 1-line hotfix; this sprint also carries a 22-route regression sweep.
- `frontend-e2e-sweep` 0.50 (Sprint 57.14) — the sweep portion is mechanical like e2e-sweep, but this also edits global CSS + shell components.
- `frontend-refactor-mechanical` 0.50/0.80 — partial fit for the shell edits only.

→ NEW class `frontend-foundation-token-correction` 0.55, HYBRID weighted blend: css-token-edit ×0.60 (~25%) + 22-route regression sweep ×0.50 (~50%) + shell-component edit ×0.50 (~15%) + closeout ×0.80 (~10%) ≈ 0.55. 1st application; Day 3 retrospective Q2 records the actual/committed ratio as the 1st data point.

### What is preserved (NOT changed)

| Layer | Specific | Reason |
|-------|----------|--------|
| Token *values* | mockup `--bg`/`--bg-1`/`--fg`/... HSL approximations in `index.css` (Sprint 57.20) | Already wired; this sprint only changes which tokens the *shell consumes*, not the values |
| Density tokens | `--row-h:36px / --pad:14px / --gap:10px` | Already match mockup `styles.css:26-28` |
| Semantic + risk tokens | `--success`/`--warning`/`--danger`/`--thinking`/`--tool`/`--memory`/`--info` + 4 risk levels | Already wired (Sprint 57.18); colour values out of scope |
| Per-route content | Every route's body markup | Foundation-only sprint; content rebuild = `frontend-mockup-strict-rebuild` epic |
| Routing / auth | `App.tsx` routes, `RequireAuth`, `authStore` | Untouched |
| Backend | `backend/**` | 0 backend changes |
| 3 rebuilt routes' structure | `/auth/*` (57.23) / `/cost-dashboard` (57.24) / `/sla-dashboard` (57.25) component trees | Untouched; only re-verified in the Day 2 sweep |

### What gets changed (this sprint scope)

| Layer | File | Approach |
|-------|------|----------|
| Root font-size baseline | `frontend/src/index.css` `@layer base` | Add `html { font-size: 13px }` (rem-scaling) so all Tailwind rem-based utilities scale to the mockup 13px base; `body` keeps `font-size` unset (inherits) or set explicit `13px`; Day 1 spike confirms `13px` vs `81.25%` (see §Technical Specifications) |
| rem→px design tokens | `frontend/src/index.css` `:root` + `.dark` | Convert `--radius` from `0.5rem` to `8px` (+ derived radii) so they survive the font-size rescale unchanged, matching mockup px tokens |
| Shell background tokens | `frontend/src/components/AppShellV2.tsx` | Root `<div>` `bg-background text-foreground` → `bg-bg text-fg` (mockup token tree) |
| Shell sidebar width | `frontend/src/components/AppShellV2.tsx` | `grid-cols-[240px_1fr]` → `grid-cols-[232px_1fr]` |
| Shell main padding | `frontend/src/components/AppShellV2.tsx` | `<main>` `p-6` → mockup-faithful inset (Day 1 decision: drop to mockup `.main` 0 + push padding into per-page wrappers, OR keep a smaller mockup-faithful inset — see §Technical Specifications R2 decision) |
| AuthShell background | `frontend/src/components/AuthShell.tsx` | Verify radial-gradient uses `--bg` not shadcn `--background`; align if drifted |
| index.css body block | `frontend/src/index.css` `@layer base body` | Align `font-family` to `var(--font-sans)` token form + confirm `line-height` matches mockup `1.45` |
| Vitest layout specs | `frontend/tests/unit/**` shell/layout specs | Adapt selector/dimension assertions if any assert `240px` / `p-6` literally |

## User Stories

### Group A — Day 0 setup + 三-prong + baseline capture (PRE-WORK)

**US-A1**: As a Sprint 57.26 owner, I want plan + checklist landed + feature branch from main `08f762fa` + Day 0 三-prong (Prong 1 path verify on `index.css` / `AppShellV2.tsx` / `AuthShell.tsx` / `tailwind.config.ts` + Prong 2 content verify on the 5 foundation drifts vs mockup `styles.css` + Prong 4 test selector verify on shell/layout Vitest specs that may assert literal `240px` / `p-6` / `bg-background`) + a baseline 1440×900 screenshot of all ~22 routes (the standalone Playwright sweep harness) + FOUNDATION-DRIFT-REPORT skeleton, so that Day 1+ has a verified baseline and the before/after sweep has a fixed reference set.

### Group B — Foundation token correction + shell alignment (Day 1)

**US-B1**: As a frontend operator, I want the production root font-size baseline aligned to the mockup `13px` base (rem-scaling via `html { font-size }` in `index.css`) + rem-based design tokens (`--radius`) converted to px so they survive the rescale, so that all Tailwind `text-*` / `p-*` / `gap-*` utilities resolve to mockup-faithful sizes across all 22 routes. Day 1 opens with a short approach spike (capture `/overview` + 2 other routes at candidate `13px` and `81.25%` settings; pick the one matching mockup proportion) before committing.

**US-B2**: As a frontend operator, I want `AppShellV2` shell aligned to mockup `.app`: sidebar grid column `240px → 232px` + root background `bg-background/text-foreground → bg-bg/text-fg` (mockup token tree) + `<main>` padding corrected to a mockup-faithful inset, so that every authed route's shell chrome (left rail width, base hue, content inset) matches mockup `styles.css:198-208` at 1440×900.

**US-B3**: As a frontend operator, I want `AuthShell` + `index.css` body block verified/aligned (radial-gradient backdrop sources `--bg` not shadcn `--background`; body `font-family` in token form; `line-height` matches mockup `1.45`), so that the `/auth/*` route family inherits the same corrected foundation as authed routes.

### Group C — 22-route regression sweep (Day 2)

**US-C1**: As a Sprint 57.26 owner, I want all ~22 routes re-screenshotted at 1440×900 *after* the foundation correction and diffed against the Day 0 *before* baseline, so that every visual change is catalogued as intended-improvement vs unintended-regression in the FOUNDATION-DRIFT-REPORT.

**US-C2**: As a Sprint 57.26 owner, I want all ~22 routes' after-correction screenshots compared against their mockup-equivalent page (`:8080/#<route>`), so that the FOUNDATION-DRIFT-REPORT records which drift dimensions the foundation correction resolved and which residual per-route content drift remains for the `frontend-mockup-strict-rebuild` epic.

**US-C3**: As a Sprint 57.26 owner, I want cosmetic regressions found in US-C1 iterated to parity within this sprint (Tailwind class tweaks) and structural regressions logged as carryover ADs (NOT silently shipped), so that the foundation correction lands without breaking any already-shipped route.

### Group D — Vitest + closeout (Day 3)

**US-D1**: As a Sprint 57.26 owner, I want the Vitest baseline (430/430 from Sprint 57.25) preserved — adapting any shell/layout spec that asserted literal `240px` / `p-6` / `bg-background` — plus `npm run lint` exit 0 + `npm run build` green + bundle KB delta recorded, so that the foundation correction ships without test or build regression.

**US-D2**: As a Sprint 57.26 owner, I want the FOUNDATION-DRIFT-REPORT finalised with a per-route verdict (FOUNDATION-PARITY = baseline aligned, residual content drift noted) + an explicit list of which routes still need `frontend-mockup-strict-rebuild` epic treatment, so that the epic's remaining-route backlog is accurate.

**US-D3**: As a Sprint 57.26 owner, I want commits + retrospective Q1-Q7 with the 1st-data-point calibration ratio for the NEW `frontend-foundation-token-correction` class + memory snapshot `memory/project_phase57_26_foundation_fidelity.md` + MEMORY.md +1 quality pointer + `.claude/rules/sprint-workflow.md` calibration matrix +1 NEW class row + CLAUDE.md Current Sprint row + Last Updated footer + `next-phase-candidates.md` update, so that Sprint 57.26 = COMPLETE and Phase 57+ Frontend 23/N opens cleanly.

## Technical Specifications

### US-B1 — root font-size rem-scaling approach

The production frontend uses Tailwind v4 utility classes (`text-sm`, `p-4`, `gap-3`, …) which are **rem-based**; `rem` resolves against `<html>` font-size. The browser default is `16px`; the mockup body baseline is `13px`. Two candidate approaches:

| Approach | Mechanism | Trade-off |
|----------|-----------|-----------|
| **A (primary)** — `html { font-size: 13px }` | Explicit px on the root element | Simplest, most explicit; every rem utility scales by 13/16 = 0.8125; `text-base`(1rem)→13px, `text-sm`(0.875rem)→11.4px, `text-xs`(0.75rem)→9.75px — close to mockup's 10-13px text range |
| **B (fallback)** — `html { font-size: 81.25% }` | Percentage of browser default | Same numeric result but respects a user who raised their browser default font-size (accessibility); slightly less explicit |

**Day 1 spike**: capture `/overview` + `/cost-dashboard` + `/auth/login` at both settings via the sweep harness; pick whichever matches mockup proportion. **Default to A** unless the spike shows an accessibility reason to prefer B. Record the decision in progress.md Day 1.

**rem→px token correction** (required regardless of A/B): `index.css` `:root` + `.dark` `--radius: 0.5rem` → `--radius: 8px` (mockup `styles.css:29`). `tailwind.config.ts` `borderRadius` derives `md`/`sm` via `calc(var(--radius) - Npx)` — already px-arithmetic-safe once `--radius` is px. Audit any other rem-valued custom property in `index.css` during Day 0 Prong 2.

**Out of scope**: rewriting per-route Tailwind classes. The rem-scaling fix deliberately shifts the *whole* scale so per-route markup is untouched.

### US-B2 — AppShellV2 shell alignment

```tsx
// AppShellV2.tsx root div — BEFORE
<div data-testid="app-shell"
  className="grid h-screen w-screen grid-cols-[240px_1fr] overflow-hidden bg-background text-foreground">

// AFTER
<div data-testid="app-shell"
  className="grid h-screen w-screen grid-cols-[232px_1fr] overflow-hidden bg-bg text-fg">
```

`<main>` padding decision (R2): mockup `.main` has padding `0` and each page's inner wrapper owns its padding. Production pages currently rely on `AppShellV2`'s `p-6`. Two options:
- **Option A** — drop `<main>` to `p-0` and add the inset to each page wrapper: correct per mockup but touches ~19 page files (scope creep).
- **Option B (default)** — keep a single mockup-faithful inset on `<main>` but corrected from `p-6` (24px) to the mockup page-padding value (Day 1 measure mockup `#overview` inner wrapper padding — likely `--pad` 14px or a `20-24px` page gutter). This keeps the change shell-local.

Default **Option B**: change `p-6` to the measured mockup page-gutter class; document the measured value in progress.md. `fullBleed` prop path (Sprint 57.21 chat-v2) unchanged.

### US-B3 — AuthShell + index.css body

`AuthShell.tsx:48-51` radial-gradient currently uses `hsl(var(--primary) / 0.12)` + `hsl(var(--background))`. Verify `--background` (shadcn) vs `--bg` (mockup) — align the backdrop base to `--bg` for hue consistency with authed routes. `index.css` `@layer base body`: confirm `font-family` matches `var(--font-sans)` chain + add `line-height: 1.45` if absent (mockup `styles.css:185`).

### Affected route inventory (Day 0 Prong 1 confirms exact list)

~22 routes across 2 shells:
- **AuthShell** (7): `/auth/login` `/auth/callback` `/auth/register` `/auth/invite/:token` `/auth/mfa` `/auth/expired` `/auth/dev`
- **AppShellV2** (~15): `/overview` `/chat-v2` `/orchestrator` `/subagents` `/loop-debug` `/state-inspector` `/memory` `/verification` `/governance` `/cost-dashboard` `/sla-dashboard` `/admin/tenants` `/admin/tenants/settings` + PROP/coming-soon stub routes

## File Change List

### MODIFIED files (~4-6)

1. `frontend/src/index.css` — add `html { font-size }` baseline (`@layer base`); `--radius` `0.5rem`→`8px` in `:root` + `.dark`; body block `font-family` token form + `line-height: 1.45`
2. `frontend/src/components/AppShellV2.tsx` — `grid-cols-[240px_1fr]`→`[232px_1fr]`; `bg-background text-foreground`→`bg-bg text-fg`; `<main>` `p-6`→mockup-faithful inset
3. `frontend/src/components/AuthShell.tsx` — radial-gradient backdrop `--background`→`--bg` if drifted
4. `frontend/tailwind.config.ts` — only if Day 0 Prong 2 finds a rem-based theme value needing px conversion (likely none — `borderRadius` already `calc()`-safe)
5. Shell/layout Vitest spec(s) — adapt any literal `240px` / `p-6` / `bg-background` assertion (exact files from Day 0 Prong 4)

### NEW files (~2-3)

1. `frontend/scripts/route-sweep.mjs` — standalone Playwright 1440×900 sweep harness (mocked auth) screenshotting all ~22 routes; reused Day 0 (before) + Day 2 (after); placed in `frontend/scripts/` per V2 file-organization (NOT repo root); supersedes the temporary `frontend/diagnose-render.mjs` which is deleted
2. `claudedocs/4-changes/sprint-57-26-foundation-fidelity/FOUNDATION-DRIFT-REPORT.md` — Day 0 skeleton → Day 2 before/after + vs-mockup matrix → Day 3 final verdict
3. `claudedocs/4-changes/sprint-57-26-foundation-fidelity/screenshots/` — before/ + after/ + mockup/ route captures

### DELETED files (1)

1. `frontend/diagnose-render.mjs` — temporary 2026-05-20 diagnostic probe; superseded by `frontend/scripts/route-sweep.mjs`; workspace hygiene (Karpathy §3 orphan delete — its only purpose was the now-complete drift investigation)

### PRESERVED (not touched)

- All ~22 route page files (foundation-only sprint)
- `backend/**` — 0 backend changes
- `App.tsx` / `RequireAuth` / `authStore` — routing + auth untouched
- Token *values* in `index.css` `--bg`/`--fg`/semantic/risk — unchanged (only shell *consumption* changes)
- `i18n/` — 0 i18n keys (no copy changes)

## Acceptance Criteria

1. ✅ Production root font-size baseline aligned to mockup `13px` base (rem-scaling); `/overview` body computed `font-size` + Tailwind `text-*` utilities resolve to mockup-faithful sizes
2. ✅ `--radius` (+ derived) converted `0.5rem`→`8px`; radius survives the font-size rescale at mockup `8px`
3. ✅ `AppShellV2` sidebar grid column = `232px`; root background = `bg-bg/text-fg`; `<main>` padding = mockup-faithful inset (measured value documented)
4. ✅ `AuthShell` backdrop + `index.css` body block sourced from mockup token tree; `/auth/*` family inherits corrected foundation
5. ✅ All ~22 routes screenshotted before (Day 0) + after (Day 2) at 1440×900; before/after diff catalogued in FOUNDATION-DRIFT-REPORT
6. ✅ All ~22 routes compared after-correction vs mockup-equivalent; residual per-route content drift catalogued (= `frontend-mockup-strict-rebuild` epic backlog)
7. ✅ 0 structural regression shipped — cosmetic regressions iterated to parity in-sprint; any structural regression logged as carryover AD (NOT shipped silently)
8. ✅ Vitest 430/430 preserved (shell/layout specs adapted for new dimensions, NOT deleted); `npm run lint` exit 0; `npm run build` green
9. ✅ Bundle KB delta ≈ 0 (CSS + shell-only change; no new dependency)
10. ✅ `frontend/diagnose-render.mjs` deleted; replaced by `frontend/scripts/route-sweep.mjs` (proper location)
11. ✅ FOUNDATION-DRIFT-REPORT final verdict = FOUNDATION-PARITY per route + accurate epic-backlog list
12. ✅ Commits + retrospective Q1-Q7 with 1st-data-point calibration ratio for NEW `frontend-foundation-token-correction` class + memory snapshot + MEMORY.md +1 + sprint-workflow.md calibration matrix +1 NEW class row + CLAUDE.md minimal touch + next-phase-candidates.md update + PR landed

## Deliverables

- [ ] Plan + checklist drafted (this sprint Day 0)
- [ ] `frontend/scripts/route-sweep.mjs` standalone sweep harness
- [ ] FOUNDATION-DRIFT-REPORT skeleton + Day 0 before-baseline screenshots (~22 routes)
- [ ] `index.css` font-size baseline + rem→px token correction
- [ ] `AppShellV2` sidebar width + background token + main padding correction
- [ ] `AuthShell` + `index.css` body block alignment
- [ ] Day 2 after-correction sweep (~22 routes) + before/after + vs-mockup matrix
- [ ] Cosmetic regressions iterated to parity; structural ones logged as carryover
- [ ] Vitest 430/430 preserved; shell/layout specs adapted; lint + build green
- [ ] `frontend/diagnose-render.mjs` deleted
- [ ] Retrospective Q1-Q7 + 1st-data-point calibration + memory snapshot + MEMORY.md +1 + calibration matrix NEW class row + CLAUDE.md minimal touch + next-phase-candidates.md update
- [ ] PR opened + CI green + merge + post-merge cleanup

## Dependencies & Risks

### Dependencies

- Mockup `:8080` http server reachable (Day 0 + Day 2 vs-mockup comparison) — `python -m http.server 8080` in `reference/design-mockups/`
- Production dev server `:3007` running (verified this session)
- Mockup token tree (`--bg`/`--fg`/...) present in `index.css` (Sprint 57.20 — verified Day 0 Prong 1)
- Standalone Playwright pattern (Sprint 57.25 fallback for AD #37 MCP blocker) — reused as the sweep harness

### Risks

| ID | Risk | Severity | Mitigation |
|----|------|----------|------------|
| **R1** | Font-size rescale shifts the 3 already-rebuilt routes (57.23 auth / 57.24 cost / 57.25 sla) off the fidelity they reached at 16px base | HIGH | Day 0 Prong 2 checks whether the 3 routes use rem utilities or px arbitrary values; Day 2 sweep audits all 3 explicitly; if a route used px arbitrary values it is *unaffected* and may now over/under-shoot — if structural regression, log carryover `AD-Rebuilt-Route-Refidelity` (do NOT silently ship); cosmetic → iterate in-sprint |
| **R2** | `<main>` padding decision (Option A 19-file vs Option B shell-local) under-scoped | MEDIUM | Default Option B (shell-local, single inset value); Day 1 measure mockup `#overview` inner page-gutter; if mockup pages have *no* uniform gutter (each page differs) → keep Option B with the most-common value + note per-page deviations as epic backlog |
| **R3** | 22-route sweep finds many cosmetic regressions → Day 2 over-runs | MEDIUM | Sweep harness batch-screenshots all routes in one run (~2-3 min); triage by severity; cosmetic-only iterate; cap in-sprint fixes — structural regressions are carryover not Day 2 work |
| **R4** | rem-scaling breaks a fixed-px element that *should* have scaled (or vice versa) | MEDIUM | Day 1 spike captures 3 representative routes at candidate settings before committing; Tailwind arbitrary px values (`w-[240px]` etc.) do NOT scale — Day 0 Prong 2 greps for arbitrary-px usage in shell + high-traffic components |
| **R5** | A shell/layout Vitest spec asserts literal `240px`/`p-6`/`bg-background` and breaks | LOW | Day 0 Prong 4 greps test files for these literals; adapt assertions (NOT delete) |
| **R6** | Browser-cache staleness masks the fix during verification (the original 2026-05-20 false alarm) | LOW | Sweep harness uses fresh Playwright contexts (no cache); user-facing verification note in PR body: hard-refresh / new tab |

### Common Risk Classes (per sprint-workflow.md §Common Risk Classes)

- **Risk Class A** (paths-filter vs `required_status_checks`): POSSIBLE — if the only changes are `frontend/**` + `claudedocs/**` the backend-ci paths-filter skips; PR body notes it, or touch `.github/workflows/backend-ci.yml` header per the documented workaround
- **Risk Class B** (cross-platform mypy unused-ignore): N/A — frontend-only
- **Risk Class C** (module-level singleton across test event loops): N/A — frontend Vitest

## Workload

| Group | Bottom-up est | Class haircut 0.55 | Day allocation |
|-------|---------------|--------------------|----------------|
| Group A (Day 0 setup + 三-prong + baseline capture) | ~0.6 hr | ~0.3 hr | Day 0 |
| Group B (token correction + shell alignment) | ~2.5 hr | ~1.4 hr | Day 1 |
| Group C (22-route regression sweep) | ~2.5 hr | ~1.4 hr | Day 2 |
| Group D (Vitest + closeout) | ~0.8 hr | ~0.4 hr | Day 3 |
| **Σ Bottom-up** | **~6.4 hr** | **~3.5 hr** | **4 working days (Day 0-3)** |

**Bottom-up est ~6.4 hr → calibrated commit ~3.5 hr (multiplier 0.55 — NEW class baseline)**

Day 3 retrospective Q2: record actual / committed ratio as the **1st data point** for the NEW `frontend-foundation-token-correction` class. Expected band [0.85, 1.20]; KEEP 0.55 baseline regardless (1 data point insufficient to adjust per `When to adjust` 3-sprint window rule).

## Sequencing / Day plan

### Day 0 — Plan + Checklist + 三-prong + baseline capture

- [ ] Plan + checklist drafted (mirror Sprint 57.25 structure)
- [ ] Branch creation from main `08f762fa`
- [ ] Day 0 三-prong (Prong 1 path verify on `index.css` / `AppShellV2.tsx` / `AuthShell.tsx` / `tailwind.config.ts` + Prong 2 content verify on the 5 foundation drifts + arbitrary-px usage grep in shell + Prong 4 test selector verify for literal `240px`/`p-6`/`bg-background` in Vitest specs)
- [ ] `frontend/scripts/route-sweep.mjs` harness authored
- [ ] Day 0 before-baseline sweep — all ~22 routes at 1440×900
- [ ] FOUNDATION-DRIFT-REPORT skeleton + D-PRE findings catalogued in progress.md Day 0
- [ ] Day 0 commit

### Day 1 — Group B (token correction + shell alignment)

- [ ] US-B1 font-size approach spike (capture 3 routes at `13px` vs `81.25%`; pick + document)
- [ ] US-B1 `index.css` font-size baseline + `--radius` rem→px correction
- [ ] US-B2 `AppShellV2` sidebar `232px` + `bg-bg/text-fg` + `<main>` padding (Option B; measure mockup gutter)
- [ ] US-B3 `AuthShell` backdrop + `index.css` body block alignment
- [ ] Day 1 spot-check sweep (`/overview` + `/auth/login` + `/cost-dashboard`) + commit

### Day 2 — Group C (22-route regression sweep)

- [ ] US-C1 after-correction sweep — all ~22 routes; before/after diff catalogued
- [ ] US-C2 after-correction vs mockup-equivalent comparison; residual content drift catalogued
- [ ] US-C3 cosmetic regressions iterated to parity; structural → carryover AD
- [ ] FOUNDATION-DRIFT-REPORT before/after + vs-mockup matrix populated
- [ ] Day 2 commit

### Day 3 — Group D + closeout

- [ ] US-D1 Vitest 430/430 (adapt shell/layout specs) + lint + build + bundle delta
- [ ] US-D2 FOUNDATION-DRIFT-REPORT final verdict + epic-backlog list
- [ ] `frontend/diagnose-render.mjs` deleted
- [ ] US-D3 retrospective.md Q1-Q7 + Q2 1st-data-point calibration ratio
- [ ] memory snapshot `memory/project_phase57_26_foundation_fidelity.md` + MEMORY.md +1 quality pointer
- [ ] `.claude/rules/sprint-workflow.md` calibration matrix +1 NEW class row (`frontend-foundation-token-correction` 0.55) + MHist
- [ ] `claudedocs/1-planning/next-phase-candidates.md` update (foundation-fidelity closed; epic-backlog routes referenced)
- [ ] CLAUDE.md Current Sprint row + Last Updated footer (REFACTOR-001 §Sprint Closeout minimal touch)
- [ ] PR open + CI green + merge + post-merge cleanup

---

**Plan drafted**: 2026-05-20 Day 0
**Sprint duration target**: 4 working days from Day 0 plan/checklist commit to PR merged
**Class**: `frontend-foundation-token-correction` 0.55 (NEW class; 1st application; HYBRID weighted blend)
