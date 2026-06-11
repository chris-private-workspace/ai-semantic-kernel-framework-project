# Sprint 57.35 — Checklist

**Plan**: [`sprint-57-35-plan.md`](./sprint-57-35-plan.md)
**Sprint Goal**: 6th Phase-2 per-page verbatim-CSS re-point — AuthShell + 7 `/auth/*` routes. **2nd non-rich-dashboard shape** in epic; **3rd validation data point** for `frontend-verbatim-css-repoint` 0.50 lifted baseline + **2nd bimodal-by-shape data point**. Closes Sprint 57.23 vintage HSL-translation epic gap.

---

## Day 0 — Plan + Checklist + 三-prong + Before-baseline

### 0.1 Plan + Checklist drafted

- [x] **`sprint-57-35-plan.md` exists** — mirrors Sprint 57.34 format
- [x] **`sprint-57-35-checklist.md` exists** — this file

### 0.2 三-prong verify

- [x] **Prong 1 path-verify** — 8 production + 2 mockup files confirmed
- [x] **Prong 2 content-verify** — per-route mockup line ranges confirmed + `/auth/login` 0 mockup classes across 18 className occurrences (Sprint 57.23 vintage HSL translation drift confirmed)
- [x] **Prong 3 schema-verify** — N/A
- [x] **Drift findings catalog** — D1 logged in progress.md Day 0

### 0.3 Before-baseline 22-route sweep

- [x] **Run `route-sweep.mjs before`** — 22 PNGs captured to `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-35/artifacts/auth-repoint/screenshots/before/`
- [x] **Sample auth routes before** — user-reported drift (SSO unstyled / Continue no fill / dev-login orange missing) confirmed in screenshot baseline

### 0.4 Day 0 commit

- [x] **Commit Day 0** — earlier this session (plan + checklist + 三-prong + before-baseline + route-sweep MHist)

---

## Day 1 — AuthShell + Login + Dev (Group B)

### 1.1 US-B1 — AuthShell re-point

- [x] **Edit `AuthShell.tsx`** — verbatim per `page-extras.jsx:5-15` (`.auth-shell`/`.auth-card`/`.auth-foot` mockup CSS)
  - DoD: shared shell verbatim; preserve children + footer prop API

### 1.2 US-B2 — Login re-point

- [x] **Edit `/auth/login/index.tsx`** — verbatim per `page-extras.jsx:28-56`
  - 3 SSO Buttons with proper `.btn-outline` styling (SAML / Microsoft / Google)
  - `.or-divider`
  - `.input` Work email
  - `.btn-primary` Continue (with arrow icon)
  - `.mono` `dev-login` orange link verbatim per mockup `style={{ color: var(--warning) }}`
  - `.kbar`-style footer (`SAML 2.0 / OIDC · MFA required by tenant policy`)
  - DoD: visual diff ≤ 2 px; all 3 SSO buttons styled correctly; dev-login orange visible

### 1.3 US-B3 — Dev re-point

- [x] **Edit `/auth/dev/index.tsx`** — verbatim per `page-extras.jsx:110-151`
  - DEV_LOGIN warning hint
  - Form fields verbatim
  - DoD: visual diff ≤ 2 px

### 1.4 Day 1 5-gate quick-check + commit

- [x] **tsc + ESLint + Vitest pass** — `cd frontend; npm run lint; npm run test -- --run auth`
- [x] **Commit Day 1** — `929d4b9a`

---

## Day 2 — Callback + Register (Group C)

### 2.1 US-C1 — Callback re-point

- [x] **Edit `/auth/callback/index.tsx`** — verbatim per `page-extras.jsx:73-105`
  - Spinner Card + "Completing sign-in…" + provider context
  - DoD: visual diff ≤ 2 px

### 2.2 US-C2 — Register re-point

- [x] **Edit `/auth/register/index.tsx`** — verbatim per `page-auth-extras.jsx:42-186`
  - Signup form with tenant/role fields
  - "Already have account" link with `.mono` accent
  - DoD: visual diff ≤ 2 px; all Field labels verbatim

### 2.3 Day 2 5-gate quick-check + commit

- [x] **tsc + ESLint + Vitest pass**
- [x] **Commit Day 2** — `a317be18`

---

## Day 3 — Invite + MFA + Expired (Group D)

### 3.1 US-D1 — Invite re-point

- [x] **Edit `/auth/invite/index.tsx`** — verbatim per `page-auth-extras.jsx:192+`
  - DoD: visual diff ≤ 2 px

### 3.2 US-D2 — MFA re-point

- [x] **Edit `/auth/mfa/index.tsx`** — verbatim per mockup MFA section
  - 6-digit TOTP input grid (preserve existing roll-own UI per Sprint 57.23 Q3 decision)
  - WebAuthn fallback UI
  - DoD: visual diff ≤ 2 px

### 3.3 US-D3 — Expired re-point

- [x] **Edit `/auth/expired/index.tsx`** — verbatim per mockup Expired section
  - DoD: visual diff ≤ 2 px

### 3.4 Day 3 5-gate quick-check + commit

- [x] **Full Vitest run** — 456/456 baseline maintained
- [x] **Commit Day 3** — `5c70f7d3`

---

## Day 4 — Regression sweep + closeout (Group E)

### 4.1 US-E1 — 22-route sweep after

- [x] **Run `route-sweep.mjs after`** — 22 PNGs captured
- [x] **Sweep delta analysis** — 7 auth routes ✅ PARITY flip; 0 regressions
- [x] **Sample 7 auth screenshots from `after/`** — /auth/login sampled; matches mockup truth

### 4.2 US-E3 — Final 5-gate verification

- [x] **tsc + Vite build** — `built in 3.19s`
- [x] **ESLint** — exit 0 (only 3 pre-existing `TSSatisfiesExpression` parser warnings)
- [x] **Vitest** — 456/456 baseline preserved (4 spec files updated)
- [x] **check:mockup-fidelity** — diff empty + grep clean

### 4.3 US-E4 — Docs sync

- [x] **REPOINT-REPORT.md** — written
- [x] **progress.md Day 0-4** — entries written
- [x] **retrospective.md Q1-Q7** — written; bimodal-by-shape WEAKENED + scale-overhead AD
- [x] **`sprint-workflow.md §Matrix`** — `frontend-verbatim-css-repoint` 6th data point cell update + MHist
- [x] **memory subfile** — written
- [x] **`MEMORY.md` pointer** — Sprint 57.35 entry added above Sprint 57.34 entry
- [x] **`CLAUDE.md` Current Sprint row + footer** — minimal touch (2 line edits)
- [x] **`next-phase-candidates.md`** — Sprint 57.35 Carryover + scale-overhead AD + bimodal-watch AD update + Sprint 57.23 epic-gap RESOLVED

### 4.4 US-E5 — Commit + PR + merge

- [ ] **Day 4 commit** on `feature/sprint-57-35-auth-repoint`
- [ ] **PR open** — `gh pr create`
- [ ] **CI green → squash-merge**

### 4.5 Sprint closeout self-check

- [x] Sacred Rule check — 0 unchecked items deleted
- [x] Acceptance Criteria — 5/6 pass; #6 PR+merge pending Day 4.5
- [ ] Working tree clean post-merge — on main
- [ ] Branch deleted — `feature/sprint-57-35-auth-repoint` deleted local + remote

