# Sprint 57.14 Retrospective — AD-Frontend-E2E-Sweep

> Branch: `feature/sprint-57-14-frontend-e2e-sweep` (from main `2766dc90`)
> Plan: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-14-plan.md`
> Days: 0-3 (focused maintenance sprint). Calibration class: `frontend-e2e-sweep` HYBRID 0.50 (1st application).

---

## Q1 — What shipped?

**Goal**: close the Sprint 57.13 carryover `AD-Frontend-E2E-Sweep` (run the Playwright e2e suite green + sync stale assertions) + land the `AD-Visual-Baseline-Generation` mechanism.

| US | Status | Detail |
|----|--------|--------|
| US-A1 — run full e2e + triage | ✅ | `npx playwright test` → **39 passed / 1 failed / 7 skipped** (47 tests / 18 spec files; 7 skipped = 1 `connectivity` + 6 `visual-regression` opt-in skips). Triage: the *only* failure was `a11y/a11y-scan.spec.ts:70` "gated pages" — and it was a **hermeticity bug, not a stale assertion** (see Q3). The PR #130 CI-round fixes (`4667dd94` auth-fixtures `**/` JSDoc + 5-spec `seedAuthJwt` beforeEach; `c80e49cc` a11y color-contrast disable + cost/sla error-path "Failed to load data") had already synced everything else — the carryover note over-estimated the regression. |
| US-A2 — fix stale assertions | ✅ | `tests/e2e/a11y/a11y-scan.spec.ts` — root-cause fix (per RULES failure-investigation — fixed the *test's* hermeticity, not the implementation): NEW `mockApi(page, authMe)` registers catch-all `**/api/v1/**` → 503 FIRST + `**/api/v1/auth/me` → 200/401 SECOND (last-registered-matching wins for `/auth/me`; catch-all 503 covers all other API → page renders `<ErrorRetry>` which axe still scans (the "error UIs need a11y" intent preserved) and never a 401 → no `handleAuthExpired` redirect → hermetic regardless of a running backend). Added `await page.waitForLoadState("networkidle")` after each `goto` before `scan(...)` (settle client redirects + mocked fetches before axe injects/evaluates). File-header MHist + Description updated. **No `src/` change; no implementation change; no new unit test** (the bug was in the test). Result: full suite **40 passed / 7 skipped / 0 failed**, ×3 runs, no flake. |
| US-B1 — visual-regression CI mechanism | ✅ | `.github/workflows/playwright-e2e.yml`: `on:` += `workflow_dispatch`; `e2e` job += `if: github.event_name != 'workflow_dispatch'`; NEW `visual-baseline` job (`if: workflow_dispatch`; ubuntu-latest; `permissions: contents: write`; `RUN_VISUAL=1 playwright test visual --update-snapshots` → commit `-snapshots/` back + `[skip ci]` + push; upload artifact). `package.json`: `e2e:visual:update` script (Linux/WSL). `visual-regression.spec.ts`: skip guard now `existsSync("<spec>-snapshots/") || RUN_VISUAL` → **auto-un-skips once baselines are committed** (push/PR e2e never red on a missing baseline; spec runs on every push/PR once the dir lands). `CONVENTION.md` §8: NEW "Hermetic API mocking" + "Visual regression baselines" sub-sections + MHist. **Actual baseline PNGs not generated in this dev session** (Windows → cross-OS mismatch in CI); the `visual-baseline` workflow produces them — one-shot post-merge trigger documented in progress.md → `AD-Visual-Baseline-Generation` converges from "carryover" to "run the workflow once". |
| US-C1 — closeout | ✅ | validation sweep (lint silent / build main 297.89 kB unchanged / vitest 236 pass unchanged / e2e 40 pass+7 skip; backend untouched — `git diff --stat main..HEAD` confirms 0 `backend/` changes → baselines guaranteed unchanged, full backend suite not re-run) + this retrospective + memory snapshot + 3 in-sprint doc syncs (16-frontend-design.md / sprint-workflow.md calibration / CONVENTION.md — done in US-B1) + PR. CLAUDE.md + SITUATION deferred post-merge. |

**Commits**: `38f826b9` (Day 0 plan+checklist+三-prong) / `4d50dd2f` (Day 1 US-A1+A2) / `9b1e047a` (Day 2 US-B1) / Day 3 closeout (pending).

---

## Q2 — Estimate accuracy

| | Bottom-up | Committed (×0.50) | Actual (est.) | Ratio (actual ÷ committed) |
|--|-----------|-------------------|---------------|----------------------------|
| Day 0 (plan + checklist + 三-prong + smoke probe) | — (in C1) | — | ~1.5 hr | |
| US-A1 + US-A2 | 5-8 hr | — | ~1 hr | **way under** — the regression was 1 test, not the broad churn the carryover note implied |
| US-B1 | 2-3 hr | — | ~1.5 hr | ~on estimate |
| US-C1 (closeout) | 1-2 hr | — | ~1.5 hr | ~on estimate |
| **Total** | **~8-13 hr** | **~4-6.5 hr** | **~5.5 hr** | **~1.05** ✅ in [0.85, 1.20] band |

`actual / bottom-up` ≈ 5.5 / 10.5 ≈ **0.52** — the 0.50 multiplier was bang-on at the *aggregate* level even though US-A1/A2 over-estimated badly: the doc/closeout overhead (Day 0 plan-drafting + Day 3 closeout, ~3 hr) is fixed cost that the per-US bottom-up under-counts, so it offsets the A1/A2 over-estimate. `frontend-e2e-sweep` 0.50 → **KEEP** (1-data-point; pending 2-3 future e2e-sweep sprints — `AD-Frontend-E2E-Sweep` is a recurring shape whenever a large feature sprint outpaces its e2e specs).

---

## Q3 — Surprises / discoveries

- **D-DAY1-1 (🟢 scope-reducing)**: the carryover note ("Days 4-8 changed implementation but e2e specs weren't synced — merge 前 CI 可能仍有殘留 stale assertion") over-estimated the damage. The PR #130 CI-round fixes had already synced auth-fixtures, the 5 tenant-page specs' `seedAuthJwt` beforeEach, and the cost/sla error-path matcher. The *only* residual failure was 1 a11y test, and it wasn't even a stale assertion.
- **D-DAY1-2 — the a11y test was red *locally* but would have been green *in CI***: `a11y-scan.spec.ts` "gated pages" mocked `**/api/v1/auth/me` (browser-side) but NOT the pages' data endpoints. A Python backend **is running on :8000** in this dev environment (`Get-NetTCPConnection -LocalPort 8000` → PID 3552). So the gated pages' data fetches (`/api/v1/governance/approvals`, `/api/v1/admin/tenants`, …) went through the Vite proxy → that real backend → no valid JWT (the mock was browser-side only; the real `fetch(..., {credentials:'include'})` carries no cookie/Bearer) → **401** → `fetchWithAuth`'s `handleAuthExpired()` → `window.location.href='/auth/login'` → the shell never rendered (isolation) / "Execution context destroyed mid-axe" (full suite). In CI (no backend on :8000) the data fetches fail differently (Vite proxy → ECONNREFUSED → 500/socket-close → `<ErrorRetry>`, no redirect) so the test would have been green there. The fix (hermetic mocking of *all* `/api/v1/**`) makes it correct regardless — and it's now codified in CONVENTION.md §8 so the next "mocked only some endpoints" spec gets caught at review.
- **Build/bundle/test baselines all unchanged** — no `src/` change, so main bundle stayed 297.89 kB, vitest stayed 236, backend untouched.
- **No new unit test added** — correctly, per RULES failure-investigation: the bug was in the *test's* setup, not the application; adding an app-level unit test would have been Potemkin.

---

## Q4 — Carryover / open items (→ Phase 57.15+)

- **AD-Visual-Baseline-Generation (converged)** — this sprint landed the mechanism (the `visual-baseline` `workflow_dispatch` job + the auto-un-skip guard + `e2e:visual:update` script + CONVENTION.md §8). The remaining step is a one-shot: after this sprint's PR merges, run `gh workflow run "Playwright E2E" --ref main` (or GitHub UI → Actions → "Playwright E2E" → Run workflow) → the `visual-baseline` job generates the Linux baselines, commits them to `main` ([skip ci]), and from then on `visual-regression.spec.ts` runs on every push/PR (its guard auto-detects the committed `-snapshots/` dir). So this AD is no longer a "carryover sprint" — it's "run the workflow once". (Could be done by whoever merges the PR, or noted as a tiny follow-up.)
- **AD-Inline-Style-Cleanup-Sweep (still open, separate)** — ~15 files with `style={{}}` → Tailwind (`SubagentTree` / `TenantSettingsView` / `TenantList{Pagination,Table,Filters}` / `ChatLayout` / `SLAMetricsCard` / `MonthPicker` / `CostBreakdownTable` / `MessageList` / `ApprovalCard` / `ToolCallCard` + admin-tenants index). Doing it lets the a11y scan re-enable the `color-contrast` rule (chat-v2 inline panels currently fail WCAG AA). Not this sprint (untouched).
- **AD-Lighthouse-Visual-Hard-Gate** — once the visual baselines are stable (a few CI cycles after the one-shot generation), flip `visual-regression.spec.ts` from "runs but the e2e job is already required" to also gating, and flip `frontend-lighthouse.yml` from `continue-on-error` to required.
- **57.13 carryover, untouched this sprint** — `AD-WorkOS-Prod-Redirect-Flow` (staging-verify real OIDC redirect chain) / `AD-i18n-Feature-Namespaces` (per-page string extraction beyond the 2 demos) / `AD-Frontend-RUM-SessionReplay` (heavier obs) / `AD-Bundle-Size` (optional — main is ~flat) / `D-DAY4-2` (verification/memory/AuditLogViewer full `<ErrorRetry>`/`<EmptyState>` adoption — needs `data-testid?`/`pending?` props).
- **No `AD-Frontend-E2E-Sweep-Round2`** — not needed; the suite is green with no `test.fixme`/`test.skip` left beyond the 2 intentional opt-in skips.
- **Pre-existing doc nit (not fixed — out of scope)**: `CONVENTION.md` §8 "Playwright e2e tests" example imports `seedAuthJwt` from `"../helpers/auth"` but the fixture actually lives at `tests/e2e/fixtures/auth-fixtures.ts`; and `auth-fixtures.ts`'s file-header NOTE still says "Full e2e sweep: Sprint 57.13 US-C1 (Day 9)". Trivial-tier; left for whoever next touches those files.

---

## Q5 — Next-phase candidates (names only — rolling planning; no plan written)

(a) **AD-Inline-Style-Cleanup-Sweep** ~5-8 hr — ~15 files `style={{}}` → Tailwind + re-enable a11y `color-contrast` rule + no-inline-style guard.
(b) **AD-Lighthouse-Visual-Hard-Gate** — visual + Lighthouse from baseline/continue-on-error → required CI checks (after baseline stability).
(c) **IAM Block B spike** ~12-18 hr — WorkOS SCIM/SAML/org-level (gap-analysis §1.2; spike → Day-4 design-note extract).
(d) **Tier 1 IaC + DR drill** ~15-20 hr.
(e) **SOC 2 + SBOM** ~12-15 hr.
(f) **AD-i18n-Feature-Namespaces** — per-page string extraction beyond the 2 demos.

(User picks one explicitly → then draft the plan.)

---

## Q6 — Calibration verdict

`frontend-e2e-sweep` HYBRID 0.50 (1st application) → actual/committed ≈ **1.05** ✅ in [0.85, 1.20] band → **KEEP 0.50** (1-data-point baseline opens; pending 2-3 future e2e-sweep sprints to validate — recurring shape). Logged as a new row in `.claude/rules/sprint-workflow.md` calibration matrix.

---

## Q7 — Design-note extract

**N/A** — this is a focused maintenance sprint, not a spike sprint (no new domain explored). No 8-Point Quality Gate to run.

---

## Sprint-workflow 8-point self-check

| Step | Done? |
|------|-------|
| Phase README (sub-sumed under phase-57-frontend-saas) | ✅ |
| Sprint Plan (`sprint-57-14-plan.md`, mirrors 57.13 structure) | ✅ |
| Sprint Checklist (`sprint-57-14-checklist.md`, mirrors 57.13, condensed Day 0-3) | ✅ |
| Day 0 三-prong (Prong 1+2; Prong 3 N/A — no DB) + Day-0 smoke probe | ✅ |
| Code (Day 1-2) against checklist | ✅ |
| Update checklist daily (`[ ]` → `[x]`, no deletions) | ✅ |
| progress.md daily entries (Day 0-3) | ✅ |
| retrospective.md (this file) Q1-Q7 | ✅ |
| PR opened | ✅ (Day 3) |

## Rolling-planning self-check
- ☑ No future-sprint plan pre-written (Phase 57.15+ candidates = names only, Q5)
- ☑ No plan/checklist skipped (Day 0 plan + checklist before any code)
- ☑ No unchecked `[ ]` deleted; no `test.skip`/`test.fixme`/`test.only` added to "go green" (the 2 opt-in skips are intentional and pre-existing)
- ☑ No specific future-sprint task written in this retrospective
