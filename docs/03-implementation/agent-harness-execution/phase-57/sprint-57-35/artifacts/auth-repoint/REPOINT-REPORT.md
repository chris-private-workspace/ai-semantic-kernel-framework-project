# Sprint 57.35 — AuthShell + 7 Auth Routes Verbatim Re-Point Report

**Sprint**: 57.35 — AD-Auth-Shell-And-Pages-Verbatim-Repoint
**Date**: 2026-05-24
**Branch**: `feature/sprint-57-35-auth-repoint`
**Class**: `frontend-verbatim-css-repoint` 0.50 (6th application; 3rd validation of lifted baseline; **2nd bimodal-by-shape data point**)

---

## Outcome

🎉 **AuthShell + 7 `/auth/*` routes flipped from Sprint 57.23 vintage Tailwind-translation → mockup verbatim PARITY.** User-reported drift (2026-05-24: SSO buttons unstyled / Continue no fill / `dev-login` orange missing) **fully RESOLVED**. 22-route sweep: 0 regressions on other 14 routes.

**Closes Sprint 57.23 vintage HSL-translation epic gap on auth routes** (per CLAUDE.md §Frontend Mockup-Fidelity Hard Constraint).

---

## Visual Delta (before → after — `/auth/login` representative)

| Element | Before (Sprint 57.23 vintage Tailwind) | After (Sprint 57.35 mockup verbatim) |
|---------|----------------------------------------|--------------------------------------|
| Brand logo | Purple/blue mix Tailwind | Blue square outline verbatim |
| 3 SSO buttons | NO border/styling — plain text rows with grey icons | Proper `.btn-outline` styling with border + icons |
| Continue button | NO styling/borders text-only | Solid blue fill `.btn-primary .btn-block` with arrow icon |
| `dev-login` link | Text-only no highlight | **Orange `.mono` `dev-login`** via `style={{ color: var(--warning) }}` |
| Footer | Plain text | `.kbar` SAML 2.0/OIDC + MFA required by tenant policy |
| AuthShell width | 420px (Sprint 57.23 drift) | **400px verbatim per mockup `page-extras.jsx:13`** (D-DAY1-1) |

Screenshots: `screenshots/before/auth-*.png` vs `screenshots/after/auth-*.png` (7 routes × 2 modes = 14 auth screenshots; plus 8 other public + AppShellV2 routes unchanged baseline)

---

## 22-route Sweep Delta

| # | Route | Before | After |
|---|-------|--------|-------|
| 1 | `/auth/login` | Sprint 57.23 vintage Tailwind drift | ✅ **PARITY** |
| 2 | `/auth/callback` | same | ✅ **PARITY** |
| 3 | `/auth/dev` | same | ✅ **PARITY** |
| 4 | `/auth/register` | same | ✅ **PARITY** |
| 5 | `/auth/invite` | same | ✅ **PARITY** |
| 6 | `/auth/mfa` | same | ✅ **PARITY** (6-digit TOTP grid + WebAuthn UI roll-own preserved per Sprint 57.23 Q3) |
| 7 | `/auth/expired` | same | ✅ **PARITY** |
| 8 | AuthShell (shared) | 420px width drift | ✅ **PARITY** (400px verbatim) |
| 9-22 | 15 other routes | Pre-existing baseline | Unchanged (no regression) |

---

## Code Changes (8 production files + 4 Vitest specs / 3 commits)

| # | File | Lines delta | Change |
|---|------|-------------|--------|
| 1 | `AuthShell.tsx` | +67 / -178 | Verbatim per mockup `page-extras.jsx:5-15` (`.auth-shell`/`.auth-card`/`.auth-foot`); width 420 → 400 per mockup |
| 2 | `pages/auth/login/index.tsx` | +174 (re-pointed) | Verbatim per `page-extras.jsx:28-56` |
| 3 | `pages/auth/dev/index.tsx` | +198 (re-pointed) | Verbatim per `page-extras.jsx:110-151` |
| 4 | `pages/auth/callback/index.tsx` | +167 (re-pointed) | Verbatim per `page-extras.jsx:73-105` |
| 5 | `pages/auth/register/index.tsx` | +620 (re-pointed) | Verbatim per `page-auth-extras.jsx:42-186` |
| 6 | `pages/auth/invite/index.tsx` | +268 (re-pointed) | Verbatim per `page-auth-extras.jsx` invite section |
| 7 | `pages/auth/mfa/index.tsx` | +413 (re-pointed) | Verbatim per `page-auth-extras.jsx` MFA section; 6-digit TOTP grid + WebAuthn UI roll-own preserved |
| 8 | `pages/auth/expired/index.tsx` | +176 (re-pointed) | Verbatim per `page-auth-extras.jsx` expired section |
| 9-12 | 4 Vitest specs | +75 / mostly | Updated to track mockup-ui Field DOM (`getByLabelText` → `getByText` + id selectors); behavioral test intent preserved |

**Production subtotal**: ~+2,083 lines (mostly full file replacements).
**Net cumulative**: +1,290 / -871 = **net +419 lines** across 12 files.

`styles-mockup.css` **NOT touched** — Sprint 57.28 verbatim-CSS foundation intact. `check:mockup-fidelity` diff + grep guards still pass.

---

## Commits

| Day | SHA | Scope |
|-----|-----|-------|
| Day 0 | (earlier) | plan + checklist + 三-prong + before-baseline sweep |
| Day 1 | `929d4b9a` | AuthShell + /auth/login + /auth/dev (US-B1+B2+B3) |
| Day 2 | `a317be18` | /auth/callback + /auth/register (US-C1+C2) |
| Day 3 | `5c70f7d3` | /auth/invite + /auth/mfa + /auth/expired (US-D1+D2+D3) |
| Day 4 | (pending) | closeout |

Day 1-3 was agent-assisted via `code-implementer` agent.

---

## 5-Gate Verification

| Gate | Result |
|------|--------|
| TypeScript build | ✅ `built in 3.19s` |
| ESLint | ✅ exit 0 (only 3 pre-existing `TSSatisfiesExpression` library noise) |
| Vitest | ✅ **456/456** baseline preserved (4 spec files updated to track mockup-ui Field DOM) |
| check:mockup-fidelity | ✅ diff byte-identical + grep clean (CSS untouched) |
| Vite build | ✅ (subsumed in #1) |

---

## Drift Catalog (Day 1-3)

- **D-DAY1-1 (AuthShell column width)**: Sprint 57.23 production was 420px; mockup `page-extras.jsx:13` truth = 400px. Corrected to mockup value. Sibling `page-auth-extras.jsx:13` AuthShellX uses 420 (minor mockup-internal drift); chose `page-extras.jsx` (canonical AuthShell source) as authority.
- **D-DAY2-1 (register plan label a11y)**: `jsx-a11y/label-has-associated-control` failed on plan radio cards after verbatim rewrite (mockup wraps `<input>` + `<div>` inside `<label>`). Re-added `aria-label` (Sprint 57.23 pattern; not invasive).
- **D-DAY2-2 (register demo banner shape)**: Sprint 57.23 used plain Tailwind warning banner; re-cast as `.hitl-card[data-severity="risk-medium"]` to match the visual language used by other auth pages (AP-2 honesty principle).
- **D-DAY3-1 (expired Badge tone)**: Sprint 57.23 used generic Badge; mockup `page-auth-extras.jsx:401` uses `Badge tone="warning"` for reason. Corrected to verbatim mockup.

**Vitest spec updates (4 files / 7 tests)**: All same root cause — mockup-ui `Field` emits `<div className="field-label">` (not `<label htmlFor>`), so `getByLabelText` no longer resolves. Updates preserved behavioral test intent (`getByText` + id selectors for input control firing).

---

## Calibration Snapshot (6th app; 3rd validation; 2nd bimodal data point)

| Phase | Bottom-up est | Actual |
|-------|---------------|--------|
| Day 0 (plan + prong + sweep) | 90 min | ~63 min (-30%) |
| Day 1-3 (agent-assisted; 8 production + 4 Vitest spec updates + 4 drifts) | 360 min (~6 hr) | ~20 min agent wall-clock; **~5-6 hr human-equivalent** (8 files + 4 Vitest updates + drift handling = larger effort than Sprint 57.34 1-file orchestrator) |
| Day 4 (sweep + closeout) | 60 min | ~50 min |
| **Total (planned)** | **~8.5 hr (~510 min)** | **agent-assisted; effective ~7-7.5 hr human-equivalent** |

**Calibration caveat** (per Sprint 57.13/57.27/57.28/57.29/57.34 convention): Day 1-3 was agent-assisted (code-implementer), not rigorously per-day human time tracking.

- Approximate `actual / committed` ratio: **~1.65-1.75** (calibrated 4.25 hr vs actual ~7-7.5 hr) — **ABOVE [0.85, 1.20] band by ~0.45-0.55**
- Approximate `actual / bottom-up` ratio: **~0.85-0.90** (bottom-up estimate accurate this sprint; 0.50 multiplier too aggressive for 8-file scope vs 1-file orchestrator)

### Bimodal-by-Shape Evaluation (2nd non-rich data point)

| Sprint | Shape | Sub-shape | Ratio | Band? |
|--------|-------|-----------|-------|-------|
| 57.29-32 (rich-dashboard) | rich | dashboard | 3-pt mean ≈ 0.40 | ❌ below |
| 57.34 | non-rich | config/tabbed-forms (1 file) | ≈ 0.95-1.05 | ✅ in band |
| **57.35** | **non-rich** | **auth-flow (8 files)** | **~1.65-1.75** | **❌ ABOVE band** |

**Bimodal-by-shape signal weakened — file-count scale matters too**:
- 57.34 was 1-file orchestrator (single page, 6 inline tabs)
- 57.35 was 8-file auth epic (1 shared shell + 7 routes + 4 Vitest spec updates)
- Different scale → different ratios despite both being "non-rich-dashboard"

**Revised hypothesis**: The bimodal signal may actually be a **file-count + spec-update overhead** signal rather than pure shape-driven:
- 1-file Phase-2 re-point (57.34) ≈ in-band middle
- 8-file Phase-2 re-point (57.35) ≈ above band (1-file estimate × 8 ≠ 8× linear; coordination overhead)
- Rich-dashboard 1-page apps (57.30-32) ≈ below band (efficient single-page; shadcn primitive removal saves time)

**Action**:
- KEEP 0.50 baseline per `When to adjust` 3-sprint window rule (3 data points still inconclusive — 1 in-band + 1 below band + 1 above band)
- **Update AD-Sprint-Plan-frontend-verbatim-css-repoint-shape-bimodal-watch** → broaden to **scale-and-shape-bimodal-watch**: shape + file-count both factors
- If Sprint 57.36 (likely another single non-rich shape, e.g. `/loop-debug` or `/state-inspector`) → 4th data point will discriminate file-count vs shape signal

---

## ADs Update

**NEW (Sprint 57.35 carryover)**:
- ✅ **RESOLVED: Sprint 57.23 vintage HSL-translation epic gap on auth routes** — closed by this sprint
- 🆕 `AD-Sprint-Plan-frontend-verbatim-css-repoint-scale-overhead-watch` — file-count + Vitest-spec-update overhead may be additional variance driver; if 57.36+ multi-file sprints again > 1.20 band → propose **file-count surcharge** in calibration multiplier (e.g. 0.50 + 0.05/extra-file beyond 3)

**Updated**:
- `AD-Sprint-Plan-frontend-verbatim-css-repoint-shape-bimodal-watch` (Sprint 57.34 NEW) — bimodal hypothesis **WEAKENED but not REJECTED**. 2 non-rich data points produce vastly different ratios (1.0 vs 1.7), suggesting shape is not the dominant variance driver; file-count may be. Continue to track but don't propose class split yet.
- `AD-Sprint-Plan-frontend-verbatim-css-repoint-baseline-lift` (Sprint 57.31 NEW) — 3rd validation data point logged. Baseline still 0.50; calibration discipline OK for typical 1-file re-points.

**Unchanged**:
- `AD-IAM-Block-B-RBAC` (Phase 58+)
- `AD-WebAuthn-Roll-Own-UI` (Phase 58+; mfa page fixture-driven this sprint per Sprint 57.23 Q3)

---

## Files Changed (final)

```
NEW:
  docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/
    sprint-57-35-plan.md
    sprint-57-35-checklist.md
  docs/03-implementation/agent-harness-execution/phase-57/sprint-57-35/
    progress.md
    retrospective.md
  docs/03-implementation/agent-harness-execution/phase-57/sprint-57-35/artifacts/auth-repoint/
    REPOINT-REPORT.md
    screenshots/{before,after}/*.png  (44 PNGs)
  memory/project_phase57_35_auth_repoint.md

MODIFIED (production):
  frontend/src/components/AuthShell.tsx
  frontend/src/pages/auth/{login,callback,dev,register,invite,mfa,expired}/index.tsx (7 files)

MODIFIED (test):
  frontend/tests/unit/pages/auth/{callback,dev,invite,register}.test.tsx (4 files)

MODIFIED (infra):
  frontend/scripts/route-sweep.mjs

MODIFIED (docs):
  .claude/rules/sprint-workflow.md
  CLAUDE.md
  memory/MEMORY.md
  claudedocs/1-planning/next-phase-candidates.md
```
