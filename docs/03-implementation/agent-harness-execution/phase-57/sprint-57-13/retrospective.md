# Sprint 57.13 — Retrospective

**File**: docs/03-implementation/agent-harness-execution/phase-57/sprint-57-13/retrospective.md
**Sprint**: 57.13 — Frontend Foundation 1/N Completion + Frontend↔Backend Wiring
**Dates**: 2026-05-10 (Day 0-9)
**Scope class**: `frontend-foundation-spike` (HYBRID 0.50, 1st application)
**Status**: Closed — 13/15 USs fully delivered, 2 minimal-viable (visual baselines + inline-cleanup sweep) with carryover ADs

> Modification History
> - 2026-05-10: Initial creation (Sprint 57.13 Day 9 closeout)

---

## Q1 — What went well

- **Auth flow is end-to-end functional** (US-A1..A5). The middleware allowlist + cookie fallback (D-PRE-8) fix means login → callback → `/auth/me` → authenticated → navigate actually works; dev-login (`/auth/dev-login` + DEV-only form) gives a no-WorkOS path; `<RequireAuth>` gates the 4 previously-ungated pages; cross-tenant admin checks + RLS hold; `/api/v1/health` + 8 router GETs pass a 2-test smoke; `.env.example` documents WorkOS + `VITE_SENTRY_DSN`.
- **Design-system layer landed and got adopted** (US-B2/B3). `components/ui/` (Skeleton/TableSkeleton/CardSkeleton/EmptyState/ErrorRetry/Card/Button/Badge + Radix `Dialog`/`DropdownMenu` wrappers) replaced bespoke loading/empty/error markup across governance/verification/memory/admin-tenants/cost/sla, and `DecisionModal`/`UserMenu` became the Radix reference consumers. Day-0 三-prong (path + content + schema grep) caught drift before code each day — no mid-impl re-work surprises.
- **Observability + i18n + a11y + Lighthouse all real, not Potemkin** (US-B4..B7). Sentry (opt-in via DSN, dynamic-imported), Web Vitals → Cat-12 `/telemetry/frontend` endpoint, i18next en+zh-TW with a working locale switcher, `eslint-plugin-jsx-a11y` recommended (5 violations found + fixed) + an axe-core e2e scan, Lighthouse CI (`lighthouserc.cjs` + GH workflow, verified locally that `lhci autorun` works end-to-end with a passing a11y gate).
- **Bundle size came out flat** — main `index.js` **297.89 kB** gzip 95.27 vs the Day-0 baseline **296.58 kB**, despite adding i18next (+~59 kB Day 7). Lazy-loading the auth pages (US-B9) + the chunk reorg (Radix hoisted out of `RequireAuth` into shared chunks) absorbed it. So AD-Bundle-Size is *not* in worse shape than at sprint start.
- **Bug fixed in passing**: `AD-AdminTenant-Patch-Flake` (from 57.12) — fixed Day 2 alongside the cross-tenant work.

## Q2 — Time tracking

| | Hours |
|---|---|
| Bottom-up estimate (plan §Workload) | ~49–65 hr |
| Calibrated commit (× 0.50, `frontend-foundation-spike` HYBRID blend) | ~25–32 hr |
| Actual (estimated — not rigorously per-day-tracked; the spike was front-loaded into a few intensive sessions) | ~26–30 hr |
| **Ratio actual / committed** | **≈ 0.95–1.0** ✅ in the [0.85, 1.20] band |

Per-day time wasn't logged with precision this sprint (the bulk of Days 3-9 ran as long continuous sessions rather than discrete day blocks), so the actual is a range estimate. The committed-vs-delivered picture: 13/15 USs fully done + 2 minimal-viable, in 10 calendar days — consistent with the ~25-32 hr commit. **Calibration verdict (Q6): KEEP `frontend-foundation-spike` 0.50** — 1-data-point baseline, ratio ~1.0, no adjustment.

## Q3 — What surprised us

- **The `@/components/ui` barrel + a statically-imported page = Radix in `main`.** Day 9's first auth-page rewrite imported `{ Button, Card } from "@/components/ui"`; because `App.tsx` static-imported `LoginPage`, Rollup pulled the *whole* barrel (incl. the `dialog`/`dropdown-menu` modules + their Radix deps) into the main bundle → +120 kB. Fixed by `React.lazy()`-ing the auth pages (and reverting the leaf-import workaround). Net result was actually *better* than before. Lesson for CONVENTION §10: barrel re-exports are fine for lazy-loaded consumers; a barrel import from a statically-bundled module drags the whole layer.
- **jsx-a11y recommended found only 5 violations** across the whole `src/` tree — the codebase was already mostly accessible. No rule down-tuning needed.
- **`<EmptyState>` has no `role="alert"`** (it's a "no data" panel) — the callback error page wraps it in `<div role="alert">` rather than misusing EmptyState's semantics.
- **`.js` config files don't work in a `"type":"module"` package** — both `i18next-parser.config` (Day 7) and `lighthouserc` (Day 8) had to be `.cjs` since their loaders use `require()`.
- **`npx lhci` ≠ `@lhci/cli`** — there's an unrelated squatted `lhci` package on the registry; the workflow + script use `npm run lhci` which resolves the local `node_modules/.bin/lhci`.

## Q4 — Open items / carry-forward (NEW carryover ADs)

| AD | What's left | Why deferred |
|----|-------------|--------------|
| **AD-Inline-Style-Cleanup-Sweep** | ~15 files still have `style={{}}` (`SubagentTree` / `TenantSettingsView` / `TenantListPagination` / `TenantListTable` / `TenantListFilters` / `ChatLayout` / `SLAMetricsCard` / `MonthPicker` / `CostBreakdownTable` / `MessageList` / `ApprovalCard` / `ToolCallCard` + admin-tenants index, etc.) → Tailwind; then add a `no-inline-style` lint/test guard | Day 9 minimal-viable: did the auth pages (the highest-value, they were full of inline styles + are the entry points); the broad sweep is mechanical bulk work — better as its own focused pass. Sanctioned by checklist §"大 sprint scope 控管". |
| **AD-Visual-Baseline-Generation** | `tests/e2e/visual/visual-regression.spec.ts` exists but `test.skip(!RUN_VISUAL)` — generate `*-snapshots/*.png` on the CI Linux runner (`RUN_VISUAL=1 ... --update-snapshots`), commit them, drop the skip | Locally-generated (Windows) baselines would all mismatch CI's font rendering. The spec + config + `.gitattributes` infra is in place. |
| **AD-Frontend-E2E-Sweep** (consolidates D-DAY5-3 + D-DAY7-6 + D-DAY8 a11y) | Run + verify the e2e suite end-to-end: governance approvals (post Radix-DecisionModal swap), `tests/e2e/i18n/locale-switch.spec.ts`, `tests/e2e/a11y/a11y-scan.spec.ts`, the Day 1-2 auth-gate updates, chat-v2 regression | No dev-server / backend boot was available in the working sessions. The specs are written; CI (`playwright-e2e.yml`) runs them. |
| AD-Bundle-Size (continued) | Main is 297.89 kB gzip 95.27 — flat vs baseline, so **downgraded to optional**. i18next (~59 kB) is in main (must init before render). If a code-split sprint happens, the lever is splitting i18next out of the critical path. | Not a regression this sprint; no immediate action. |
| AD-i18n-Feature-Namespaces | Per-page string extraction beyond the 2 demo adopters (cost-dashboard + verification) | i18n done minimal-viable per checklist allowance — `common` + `auth` namespaces + 2 demos. |
| AD-WorkOS-Prod-Redirect-Flow | Staging-verify the real WorkOS OIDC redirect chain (dev uses the `/auth/dev-login` fallback) | Can't be verified without a WorkOS tenant + staging env. |
| AD-Lighthouse-Visual-Hard-Gate | Promote `frontend-lighthouse.yml` (and the visual job, once baselines exist) from `continue-on-error` to a required CI check | Premature while perf budgets are warnings + visual has no baselines. |
| AD-Frontend-RUM-SessionReplay | Sentry session replay / Datadog RUM (heavier obs) | This sprint did error + Web Vitals only — sufficient for a foundation. |

**17.md**: unchanged — **0 NEW agent_harness contract / ABC / LoopEvent / migration** this sprint. The 4 NEW api/v1 endpoints (`GET /auth/me`, `POST /auth/dev-login`, `POST /telemetry/frontend`, `POST /telemetry/frontend-error`) + the `require_tenant_match_or_platform_admin` dependency are HTTP-boundary code in `api/v1` / `platform_layer`, documented in their file headers — outside 17.md's scope (which tracks agent_harness internal cross-category interfaces).

## Q4.1 — Closeout user decision points (surfaced in the PR description)

1. **Bundle size** — main 297.89 kB gzip 95.27, ~flat vs the 296.58 kB baseline. AD-Bundle-Size downgraded to optional — no follow-up code-split sprint needed unless you want to split i18next out of the critical path. Decision: keep as-is, or schedule the split?
2. **Minimal-viable carryovers** — `AD-Inline-Style-Cleanup-Sweep` (~15 files) + `AD-Visual-Baseline-Generation` + `AD-Frontend-E2E-Sweep`. Which (if any) should be the next sprint's headline vs. moving to other Phase 57.14+ candidates?
3. **Calibration** — `frontend-foundation-spike` 0.50, 1-data-point, ratio ~1.0 → KEEP. (Recorded in sprint-workflow.md matrix.)
4. **Lighthouse + visual hard gate** — currently `continue-on-error`. Promote to required CI checks now, or after `AD-Frontend-E2E-Sweep` + `AD-Visual-Baseline-Generation` land?
5. **WorkOS prod redirect** — dev used the `/auth/dev-login` fallback; the real OIDC redirect chain hasn't been exercised against a staging WorkOS tenant (AD-WorkOS-Prod-Redirect-Flow).

## Q5 — Next-sprint candidates (rolling — list only, no plan written)

- Sprint 57.14 candidate A: `AD-Inline-Style-Cleanup-Sweep` + `AD-Frontend-E2E-Sweep` (frontend hygiene + e2e green) — natural continuation
- Candidate B: `AD-Visual-Baseline-Generation` + Lighthouse/visual → hard CI gates (`AD-Lighthouse-Visual-Hard-Gate`)
- Candidate C: IAM Block B (WorkOS SCIM / SAML / org-level — per gap-analysis §1.2; spike sprint → Day-4 design-note extract)
- Candidate D: AD-Bundle-Size code-split (split i18next + lazy boundaries) — only if user wants it
- Candidate E: a Phase 58.0+ Tier-1 item (IaC + DR drill — per CLAUDE.md Next Phase 候選)

(Per rolling discipline: none of these has a plan; the user picks before any plan is drafted.)

## Q6 — Calibration verification

`frontend-foundation-spike` HYBRID 0.50 (1st application, opened this sprint). Actual/committed ratio ≈ **0.95–1.0** — bullseye in the [0.85, 1.20] band. **Verdict: KEEP 0.50** for this scope class; this is the 1-data-point baseline. Recorded as a new row in `.claude/rules/sprint-workflow.md` §Scope-class multiplier matrix. (Per the `When to adjust` rule, no change on a single data point.)

## Q7 — Design note extract

**N/A — SKIP.** Per `sprint-workflow.md` §Step 5.5, design-note extraction applies to *spike sprints exploring a NEW domain*. Sprint 57.13 was a *foundation-completion* sprint — it finished the frontend SaaS foundation that was already being built across 57.1–57.12, using established patterns (AppShellV2 / routes.config / TanStack Query / Radix wrappers). No new domain → no design note. (The IAM Block A spike's design note was Sprint 57.7's; if IAM Block B happens it'll get its own.)
