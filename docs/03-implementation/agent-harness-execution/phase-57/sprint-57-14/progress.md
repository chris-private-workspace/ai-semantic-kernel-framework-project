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
- `38f826b9` `chore(sprint-57-14, Day 0): plan + checklist + 三-prong baseline` ✅

---

## Day 1 — 2026-05-10 — US-A1 (run suite + triage) + US-A2 (fix)

### US-A1: full Playwright e2e suite run + triage
- `npx playwright test --reporter=list` → **39 passed / 1 failed / 7 skipped** (47 tests across 18 spec files; 7 skipped = 1 `connectivity.spec.ts` `test.skip(!RUN_CONNECTIVITY)` + 6 `visual-regression.spec.ts` `test.skip(!RUN_VISUAL)` — the expected opt-in skips).
- **Triage** — only ONE failing test (the carryover note over-estimated the regression; the PR #130 CI-round fixes (`4667dd94` auth-fixtures `**/` JSDoc + 5-spec `seedAuthJwt` beforeEach; `c80e49cc` a11y color-contrast disable + cost/sla error-path "Failed to load data") had already synced the rest):

  | Spec / test | Failure | Classification | Root cause |
  |-------------|---------|----------------|------------|
  | `a11y/a11y-scan.spec.ts:70` "gated pages … 0 critical/serious a11y violations" | isolation: `getByTestId('app-shell')` not found → "navigated to /auth/login" (deterministic, 4/4 repeats); full-suite: `frame.evaluate: Execution context was destroyed, most likely because of a navigation` (axe ran, then the page navigated under it) | **(d-ish) hermeticity bug, not a stale assertion** | The test mocked `**/api/v1/auth/me` (browser-side, 200) but NOT the pages' data endpoints. A Python backend **is running on :8000** (process 3552 — `Get-NetTCPConnection -LocalPort 8000`); so the gated pages' data fetches (`/api/v1/governance/approvals`, `/api/v1/admin/tenants`, …) went through the Vite proxy → real backend → no valid JWT (the mock was browser-side only; the real `fetch(..., {credentials:'include'})` carries no cookie/Bearer) → **401** → `fetchWithAuth`'s `handleAuthExpired()` → `window.location.href='/auth/login'` → shell unmounts / context destroyed. In CI (no backend on :8000) the data endpoints fail differently (Vite proxy → ECONNREFUSED → 500/socket-close → `<ErrorRetry>`, no redirect) so it would pass there — but the test was fragile (depended on the *absence* of a backend). |

### US-A2: fix
- **`tests/e2e/a11y/a11y-scan.spec.ts`** — root-cause fix (per RULES failure-investigation — fix the test's hermeticity, not the implementation): NEW `mockApi(page, authMe)` helper registers a catch-all `**/api/v1/**` → 503 FIRST, then `**/api/v1/auth/me` → 200/401 (more-specific last-registered handler wins for `/auth/me`; catch-all covers all other API calls → deterministic 503 → page renders `<ErrorRetry>` which axe still scans (the "error UIs need a11y too" intent preserved) and crucially never a 401 → no redirect). Both tests (gated-pages + auth-pages) use it. Also added `await page.waitForLoadState("networkidle")` after each `page.goto` and before `scan(...)` so client-side redirects (e.g. `/verification` → `/verification/recent` if it has an index `<Navigate>`) + mocked data fetches settle before axe injects/evaluates. File-header MHist + Description updated.
- **`tests/e2e/fixtures/auth-fixtures.ts`** — NOT touched (D-PRE-2: already authStore-based + `seedAuthJwt` already had the fixes from PR #130; the stale "Full e2e sweep: Sprint 57.13 US-C1 (Day 9)" header NOTE left as-is since the file is untouched — Trivial-tier change not warranted; will update if a later sprint touches it).
- No `src/` change; no implementation change; no new unit test (no real bug — the bug was in the *test's* hermeticity).

### Verify
- `npx playwright test a11y/a11y-scan.spec.ts --reporter=line` → **2 passed (12.8s)** (moderate/minor a11y warnings logged: `/chat-v2` 4 — heading-order/landmark-*; `/auth/callback?error` 1 — page-has-heading-one; these are baseline-scope `console.warn`, not failures)
- `npx playwright test --reporter=line` (full suite) → **40 passed / 7 skipped / 0 failed** — re-run ×2 more → identical (no flake)
- `git diff` shows only `tests/e2e/a11y/a11y-scan.spec.ts` (+ progress.md / checklist) — no `src/`, no `playwright.config.ts`

### Drift findings (D-DAY1)
- D-DAY1-1 (🟢 scope-reducing): the e2e regression was 1 test, not the broad "Days 4-8 churn" the carryover note implied → US-A1/A2 done in ~1 hr; sprint will come in well under the ~4-6.5 hr commit (ratio ~0.4-0.5). Surplus noted for retrospective Q2.
- D-DAY1-2: a real backend running on :8000 (process 3552) — this is *why* the test was red locally but would be green in CI. The fix makes the test hermetic regardless. (Not stopping the backend per CLAUDE.md "Do not stop any node.js process" — though this is a python process; left running anyway, not relevant.)

### Day 1 commit
- `4d50dd2f` `fix(sprint-57-14, Day 1): US-A1 e2e triage + US-A2 a11y-scan hermeticity` ✅

---

## Day 2 — 2026-05-10 — US-B1: visual-regression CI mechanism + skip-guard rewrite

### US-B1 changes
- **`.github/workflows/playwright-e2e.yml`** —
  - `on:` += `workflow_dispatch` (manual trigger to regenerate visual baselines)
  - `e2e` job += `if: github.event_name != 'workflow_dispatch'` (so the manual trigger only runs the visual job, not the regular suite against the pre-commit checkout)
  - NEW `visual-baseline` job: `if: github.event_name == 'workflow_dispatch'`; `runs-on: ubuntu-latest`; `permissions: contents: write`; checkout (`ref: github.ref`, `token: GITHUB_TOKEN`) → setup-node 20 + `npm ci` → cache + `npx playwright install --with-deps chromium` → `npm run build` → `RUN_VISUAL=1 npx playwright test visual --update-snapshots` → `git add tests/e2e/visual/**/*-snapshots/` + (if changed) commit `chore(e2e): regenerate visual-regression baselines [skip ci]` + `git push origin HEAD:${{ github.ref_name }}` → upload `visual-baselines` artifact (always).
- **`frontend/package.json`** — NEW script `"e2e:visual:update": "RUN_VISUAL=1 playwright test visual --update-snapshots"` (Linux/WSL only — Windows `npm run` uses cmd.exe where the inline env-var syntax fails; CI uses `env:` not the script).
- **`frontend/tests/e2e/visual/visual-regression.spec.ts`** — skip-guard rewrite: `import {existsSync} 'node:fs'` + `dirname/join` `node:path` + `fileURLToPath` `node:url`; `SNAPSHOTS_DIR = join(dirname(fileURLToPath(import.meta.url)), "visual-regression.spec.ts-snapshots")`; `HAS_BASELINES = existsSync(SNAPSHOTS_DIR)`; `RUN_VISUAL = HAS_BASELINES || Boolean(process.env.RUN_VISUAL)` → spec **auto-un-skips once the `-snapshots/` dir is committed** (so push/PR e2e isn't red on a missing baseline; once it lands the spec runs on every push/PR). Skip message points to the `visual-baseline` workflow. File-header Description + MHist updated.
- **`frontend/CONVENTION.md`** — §8: NEW "### Hermetic API mocking" sub-section (mock catch-all `**/api/v1/**` first + specific routes after; the a11y-scan-was-red-locally lesson; `waitForLoadState("networkidle")` before axe/screenshot) + NEW "### Visual regression baselines (Sprint 57.14)" sub-section (Linux-only generation / auto-skip-until-committed guard / `visual-baseline` workflow trigger / `npm run e2e:visual:update` for WSL / `.gitattributes *.png binary` / never commit Windows-generated). MHist += 57.14 entry + a backfill 57.13 §10-13 entry; `Last Modified` → 2026-05-10.

### Verify
- `python -c "yaml.safe_load(open(...,encoding='utf-8'))"` → YAML OK; jobs `[e2e, visual-baseline]`; on `[push, pull_request, workflow_dispatch]` ✅
- `npx playwright test visual --list` → 6 tests listed (spec parses with the new imports) ✅
- `npx playwright test visual --reporter=line` → **6 skipped** (skip guard works — no `-snapshots/` dir + no `RUN_VISUAL` → skip; message points to the workflow) ✅
- `npx playwright test --reporter=line` (full suite) → **40 passed / 7 skipped / 0 failed** (visual changes didn't break the rest) ✅
- Actual baseline PNG commit: **NOT done in this dev session** (Windows-generated would cross-OS-mismatch in CI). The `visual-baseline` workflow produces them; trigger it once post-merge → `AD-Visual-Baseline-Generation` then converges from "carryover" to "done" (or to "run the workflow once" if the user prefers to defer the trigger).

### One-shot trigger note (post-merge)
```
# After this sprint's PR merges, generate the Linux baselines once:
gh workflow run "Playwright E2E" --ref main
# (or GitHub UI → Actions → "Playwright E2E" → Run workflow → branch: main)
# → runs the visual-baseline job → commits tests/e2e/visual/visual-regression.spec.ts-snapshots/*.png back to main
# From then on visual-regression.spec.ts runs as part of every push/PR e2e job.
```

### Day 2 commit
- (pending) `feat(sprint-57-14, Day 2): US-B1 visual-regression CI baseline mechanism + auto-un-skip guard`

---
