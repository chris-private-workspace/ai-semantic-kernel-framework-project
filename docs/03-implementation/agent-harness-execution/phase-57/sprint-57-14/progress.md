# Sprint 57.14 Progress — AD-Frontend-E2E-Sweep

> Branch: `feature/sprint-57-14-frontend-e2e-sweep` (from main `2766dc90`)
> Plan: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-14-plan.md`
> Checklist: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-14-checklist.md`
> Calibration: `frontend-e2e-sweep` HYBRID 0.50 (1st application) — bottom-up ~8-13 hr → committed ~4-6.5 hr; Day 0-3

---

## Day 0 — 2026-05-10 — Setup + Branch + Pre-flight + 三-prong + Calibration + smoke probe

### Branch
- `feature/sprint-57-14-frontend-e2e-sweep` from main `2766dc90` ✅

### Pre-flight baseline (post Sprint 57.13)
| Metric | Baseline | Notes |
|--------|----------|-------|
| pytest | 1676 pass + 4 skip (1680 collected) | not touched this sprint — sanity only |
| mypy --strict | 0 / 306 files | not touched |
| 9 V2 lints | 9/9 green | not touched |
| Vitest | 236 / 57 files | not touched (unless real-bug fix) |
| Playwright | 18 spec files (incl. 2 opt-in skips: connectivity / visual-regression) | **never run green** — this sprint's target |
| Vite build main bundle | 297.89 kB (gzip 95.27) | not touched |
| LLM SDK leak | 0 | not touched |
| Chromium browser | installed (`chromium-1217` ↔ Playwright 1.59.1) | ✅ |

### Day 0 三-prong verify

**Prong 1 — Path Verify** ✅
- 18 e2e spec files exist under `tests/e2e/**` (a11y / admin_tenants / chat ×4 / connectivity / cost-dashboard / governance / i18n / loop-debug / memory / sla-dashboard / smoke / tenant-settings ×2 / verification / visual)
- `tests/e2e/fixtures/auth-fixtures.ts` exists (+ `approval-fixtures.ts`)
- `frontend/playwright.config.ts` exists; `.github/workflows/playwright-e2e.yml` exists
- `tests/e2e/visual/` contains only `visual-regression.spec.ts` — **no `visual-regression.spec.ts-snapshots/` dir** (NEW, as expected — baselines never generated)
- `frontend/package.json` / `frontend/CONVENTION.md` / `16-frontend-design.md` / `.claude/rules/sprint-workflow.md` exist

**Prong 2 — Content Verify** ✅
- `playwright.config.ts` — `webServer`: local `npm run dev -- --port 5173 --strictPort` (`reuseExistingServer: true`), CI `npm run preview -- --port 5173 --strictPort`; baseURL `http://localhost:5173`; `expect.toHaveScreenshot { animations:"disabled", maxDiffPixelRatio:0.02 }`; chromium-only project; retries CI 2 / local 0
- `playwright-e2e.yml` — `on:` = `push` (main + `feature/**` + `fix/**` + `refactor/**`) + `pull_request`. **No `workflow_dispatch`** → US-B1 must ADD it. Paths filter removed (Sprint 55.6 / AD-CI-5). One job `e2e` (ubuntu-latest, 20 min): checkout → setup-node 20 + `npm ci` → cache `~/.cache/ms-playwright` → `npx playwright install --with-deps chromium` → `npm run build` → `npx playwright test --reporter=list` (env `CI: "1"`) → upload report on failure.
- `auth-fixtures.ts` — `seedAuthJwt(page, {tenantId?, tenantCode?, roles?})` mocks `**/api/v1/auth/me` → 200 `{user, tenant:{id,name,code}, roles}` (default tenant `00000000-0000-0000-0000-0000000000e1`, roles `["user","admin","platform_admin"]`); `clearAuthJwt(page)` → 401. Already authStore-based (Sprint 57.13 US-A1/A2). `**/api/v1/auth/me` JSDoc bug already fixed in PR #130 (`4667dd94`). ⚠️ File header NOTE still says "Full e2e sweep: Sprint 57.13 US-C1 (Day 9)" — stale; this sprint IS that sweep → update header MHist when touched.
- `visual-regression.spec.ts` — current guard `test.skip(!RUN_VISUAL, …)` inside `test.describe`; 6 `toHaveScreenshot` tests (app-shell via `/loop-debug` + `getByTestId("app-shell")` / `/auth/login` `getByRole("heading",{level:1})` / `/cost-dashboard` / `/governance` / `/verification/recent` / `/admin-tenants` — all `page.route()`-mocked; uses `mockAuthMe` with tenant `00000000-0000-4000-8000-000000000099`). US-B1 rewrites the guard to `existsSync(<spec>-snapshots/) || RUN_VISUAL`.
- Browser binary: `chromium-1217` present in `/c/Users/Chris/AppData/Local/ms-playwright/` ✅

**Prong 3 — Schema Verify** — **N/A** (this sprint touches 0 DB / migration / ORM model / API endpoint — purely frontend e2e specs + 1 CI workflow)

**Drift findings (D-PRE)**:
| ID | Finding | Implication |
|----|---------|-------------|
| D-PRE-1 | `playwright-e2e.yml` `on:` lacks `workflow_dispatch` | US-B1 adds it (not just the new job) |
| D-PRE-2 | `auth-fixtures.ts` already authStore-based + `seedAuthJwt` signature stable; the `**/` JSDoc SyntaxError + 5 tenant-page `seedAuthJwt` beforeEach were already fixed in PR #130 CI rounds (`4667dd94` + `c80e49cc`) | US-A2's "auth-fixtures fix" is likely already done; main risk is the *other* spec assertions (governance Radix / verification i18n / memory design-system / login-callback rewrite) — focus there |
| D-PRE-3 | `auth-fixtures.ts` file-header NOTE says "Full e2e sweep: Sprint 57.13 US-C1 (Day 9)" — stale | update header MHist when the file is touched (or even if not — but only-if-touched per file-header rule's Trivial tier; leave if untouched) |
| D-PRE-4 (🟢) | smoke probe (`npm run e2e -- smoke.spec.ts`) → **2 passed** — Playwright runs fine in this dev session (webServer auto-starts `npm run dev` :5173, chromium launches) | US-A1/A2 proceed on the real-run path (NOT the degraded static-audit fallback) |

**Go/no-go**: Findings shift scope < 20% (D-PRE-2 actually *reduces* US-A2 scope — auth-fixtures already synced). **Continue to Day 1** with the real-run path confirmed by D-PRE-4.

### Calibration
- Class `frontend-e2e-sweep` HYBRID 0.50 (1st application, 1-data-point opens). Weighted blend: US-A1+A2 (test-maintenance-mechanical ×0.45, ~0.65 weight) + US-B1 (ci-infra-new ×0.55, ~0.20) + US-C1 (closeout ×0.80, ~0.15) ≈ 0.50 mid-band.
- Bottom-up ~8-13 hr → committed ~4-6.5 hr; Day 0-3 (4 days). Day 3 retrospective Q2 verifies ratio.

### Smoke probe (de-risk US-A1/A2)
- `npx playwright install chromium` — already installed (no-op; `chromium-1217`) ✅
- `npm run e2e -- smoke.spec.ts` → **2 passed (5.5s)** — pipeline works ✅

### Day 0 commit
- (pending) `chore(sprint-57-14, Day 0): plan + checklist + 三-prong baseline`

---
