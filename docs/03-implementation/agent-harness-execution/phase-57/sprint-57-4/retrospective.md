# Sprint 57.4 Retrospective — Phase 57+ SaaS Frontend 3/N: Admin Tenants Console list bundle

> **Sprint Plan**: [sprint-57-4-plan.md](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-4-plan.md)
> **Sprint Checklist**: [sprint-57-4-checklist.md](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-4-checklist.md)
> **Branch**: `feature/sprint-57-4-admin-tenants-list-bundle`
> **Date**: 2026-05-07

---

## Q1 — What went well

- **Plan-time Prong 2 catch saved ~8-12 hr Day 1 rework** — the missing GET `""` list endpoint was identified at plan-time before any frontend code started. Option A pre-emptive bundle delivered in the same calibrated commit envelope (~8 hr) that a frontend-only naive plan would have spent rebuilding.
- **57.3 pattern reuse acceleration** — types/service/store/page architecture mirrored 57.3 tenant-settings 1:1, including inline-style badge palette, `_handleResponse<T>` helper, Zustand store with reset action, and React Router / page wrapper conventions. Estimated 60-70% velocity boost vs greenfield 57.1 v2.
- **5 Vitest unit tests + 4 Playwright e2e all green on first integrated run** (after 2 minor selector fixes from strict-mode violations). Pytest 9 new integration tests passed first run with only one pagination-stability fix (deterministic ORDER BY).
- **D1 RED finding closed cleanly** — backend tenants.py R surface now includes both `GET /{id}` (57.3) AND `GET ""` (57.4 list); CRUD R complete for admin tenant entity.
- **Day 0 三-prong second fully-applied sprint** — Path + Content + Schema all attempted; ROI ≈ 16-24× confirms 57.3 first application was not a fluke. Cumulative AD-Plan-3 evidence: 4 sprints (55.5/55.6/57.3/57.4) all caught D1-class drift before Day 1 code.

## Q2 — What didn't go well + Calibration verdict

### Calibration (AD-Sprint-Plan-4 `mixed` 0.60 mid-band 4th application)

| Sprint | Multiplier | Bottom-up | Committed | Actual | Ratio |
|--------|-----------|-----------|-----------|--------|-------|
| 53.7 (1st app) | 0.55 | 13.5 hr | 7.4 hr | 7.5 hr | 1.01 ✅ |
| 56.2 (2nd app) | 0.60 | 22 hr | 13.2 hr | 15.4 hr | 1.17 ✅ |
| 57.3 (3rd app) | 0.60 | 17 hr | 10 hr | ~5.7 hr | 0.57 ⬇️ |
| **57.4 (4th app)** | **0.60** | **14 hr** | **8.4 hr** | **~3.5 hr** | **0.42 ⬇️** |
| **4-data-point mean** | | | | | **0.79 ⬇️** |

**Verdict**: 4-data-point window mean 0.79 dropped below band lower edge [0.85, 1.20] by 0.06. The two recent low ratios (57.3 0.57 + 57.4 0.42) reflect a real *pattern reuse* effect — adding pages that mirror an established frontend feature folder (cost-dashboard / sla-dashboard / tenant-settings) compounds velocity beyond the multiplier's expected ratio.

**Action**: Log **AD-Sprint-Plan-6** to consider scope-class refinement: split `mixed` into `mixed-greenfield` (0.60 retained) and `mixed-pattern-reuse` (proposed 0.40 starting baseline) for sprints that primarily extend an established frontend feature folder. Keep 0.60 for Sprint 57.5 if scope is novel; lower if it's clearly pattern-reuse continuation.

### Other

- **Playwright strict-mode selector fixes (D14)** — `getByText("active")` matched 2 elements (badge span + dropdown option text) on first run; fixed via `.locator("td span").filter({ hasText })` and `getByRole("heading")`. Cost ~5 min mid-Day-4. AD-Plan-3 process did not catch this because Playwright accessibility snapshots were not in scope for content-verify.
- **Pagination test stability (D9)** — three tenants seeded in same flush share `created_at`; LIMIT/OFFSET ordering was non-deterministic. Fixed via secondary sort key `(created_at DESC, id DESC)` on the endpoint + ILIKE-search isolation in the test. Endpoint fix is a real correctness improvement (paginated APIs need deterministic ordering); test fix is hygiene.

## Q3 — What we learned + Day 0 三-prong observations

- **Pattern reuse compounds calibration drift faster than expected**. Sprint 57.3 already showed 0.57; Sprint 57.4 deepened to 0.42. Two consecutive sprints in the same lineage (tenant-settings → admin-tenants console) reveal that the multiplier matrix needs sub-classes for greenfield vs reuse, not just for scope size.
- **AD-Plan-3 wrong-content drift catch is now a 4-sprint pattern**. ROI evidence consolidated: ~30 min Day-0 cost prevents 8-12 hr Day-1+ rework consistently. Recommend promoting Day-0 三-prong to a non-skippable rule line in `sprint-workflow.md` §Step 2.5 (already there as "Required" but de-facto enforcement evidence is now strong enough to remove the "first fully-applied sprint" framing — it's standard practice now).
- **Schema-Grep (Prong 3) N/A is a valid verdict**, not a "skip". This sprint had no DB schema/migration scope and the Tenant ORM was reused as-is. Prong 3 attempt = re-confirming `class Tenant` field list + checking migrations head — under 5 min cost. Worth keeping the attempt habit even when verdict is N/A; it's free insurance against accidentally missing a schema dependency.
- **Frontend bundle delta first-time observed** — Vite tree-shakes new feature folders aggressively until a route consumer imports them; build size only grew on Day 4 when App.tsx imported `AdminTenantsPage`. Result: 203.02 kB (Day 0-3) → **209.11 kB** (Day 4 wired). Future planning can rely on this: bundle-size impact is deferred until route wire-up.

## Q4 — Audit Debt deferred (明確標 ID + target sprint)

| AD ID | Description | Target |
|-------|-------------|--------|
| ⏸ **AD-Sprint-Plan-6** (NEW) | Split `mixed` multiplier into `mixed-greenfield` (0.60) vs `mixed-pattern-reuse` (~0.40). Evidence: 57.3 (0.57) + 57.4 (0.42) consecutive pattern-reuse sprints. Apply at next sprint plan §Workload header. | Sprint 57.5+ |
| ⏸ **AD-AdminTenants-URL-QuerySync** (NEW) | Implement URL query string sync for filters/pagination (deferred this sprint per AP-6 — no real shareability need yet). When admin team raises actual share-URL request → next admin frontend sprint. | Phase 57.x or 58 |
| ⏸ **AD-AdminTenants-DebouncedSearch** (NEW) | Add 300ms debounce to TenantListFilters search input (deferred this sprint per AP-6 — explicit Apply button is enough for current scale). When tenants count > ~500 in production search frequency tuning becomes real. | Phase 58+ |
| ⏸ **AD-Cat10-VisualVerifier+Frontend-Panel** (carry from 55.5) | Phase 57.x Group F. | Phase 57.x |
| ⏸ **AD-Cat11-Multiturn / SSEEvents / ParentCtx** (carry from 54.2) | Phase 56+ Cat 11 bundle. | Phase 56+ |
| ⏸ **AD-CI-6** (carry from 55.6) | Production launch — needs Azure provisioning. | Phase 58 |
| ⏸ **AD-Cat12-BusinessObs (real tracer)** (carry from 55.2) | Thread real tracer through chat router. | Phase 56.x |
| ⏸ **AD-Cost-Ledger-Token-Split / Provider-Attribution / LoopMetricsAccumulator** (carry from 56.3) | Operational rollout / refactoring track. | Phase 56.x |

## Q5 — Next steps (rolling planning)

Sprint 57.5 candidates pending user approval (per `.claude/rules/sprint-workflow.md` rolling planning 紀律):

1. **Onboarding self-serve wizard** — needs backend self-serve API design first; non-trivial ~12-15 hr × `large multi-domain` 0.55 = ~7-8 hr commit
2. **Feature flags admin UI** (small-frontend ~5-6 hr × proposed `mixed-pattern-reuse` 0.40 = ~2-3 hr commit) — backend 56.1 ships full service + endpoint
3. **Audit log frontend view** (small-frontend ~6-7 hr × `mixed-pattern-reuse` 0.40 = ~3 hr commit) — backend 53.5/53.6 ships full audit/log + verify-chain
4. **Compliance partial GDPR** (medium-backend ~10-13 hr × 0.80 = ~8-10 hr commit)
5. **DR + WAL streaming** (large multi-domain ~14-18 hr)
6. **SaaS Stage 2 Stripe + 月結 + Status Page** (large multi-domain ~12-15 hr)
7. **AD-Cat10-VisualVerifier + Frontend-Panel** (Phase 57.x Group F deferred)
8. **AD-Cat11-Multiturn + SSEEvents + ParentCtx** (54.2 deferred bundle)
9. **AD-CI-6** Phase 58 production launch (needs Azure provisioning)

**Recommend**: continue frontend pattern-reuse momentum with **#2 Feature flags UI** or **#3 Audit log view** for fast ROI; OR pivot to **#1 Onboarding self-serve** for Stage 1 SaaS UX completeness (requires backend API design upfront).

User approval required per rolling planning 紀律. Do not draft Sprint 57.5 plan/checklist before user picks direction.

## Q6 — Solo-dev policy validation

- ✅ `enforce_admins=true` permanent (PR cannot bypass CI via admin merge)
- ✅ `required_approving_review_count = 0` permanent (solo dev unable to self-approve)
- ✅ All 5 active CI checks expected green on PR (paths-filter retired since 55.6 — backend-ci.yml + playwright-e2e.yml always trigger)
- ✅ No `--no-verify` / `--force` git operations used this sprint
- ✅ Scope respected: backend list endpoint touched only `tenants.py`; frontend admin-tenants is new isolated folder; no cross-cutting ripple to V2 範疇 1-12

---

## Sprint Stats Summary

| Metric | Baseline (Sprint 57.3 close) | After Sprint 57.4 | Delta | vs Plan |
|--------|-------------------------------|-------------------|-------|---------|
| Backend pytest | 1589 | **1598** | **+9** | 150% of +6 |
| Backend mypy --strict | 0/295 source files | 0/295 (unchanged) | 0 | ✅ |
| 8 V2 lints | 8/8 green | 8/8 green | 0 | ✅ |
| LLM SDK leak | 0 (5 docstring mentions only) | 0 | 0 | ✅ |
| Frontend Vitest | 23 / 8 files | **35 / 13 files** | **+12** | 200% of +6 |
| Playwright e2e | 19 (chromium) | **23** (chromium) | **+4** | ✅ |
| Vite build modules | 69 | **75** | +6 | wire-up |
| Vite build size (kB) | 203.02 | **209.11** | +6.09 | wire-up |

**Calibration**: `mixed` 0.60 4th app ratio **0.42** ⬇️ below band by 0.43; 4-data-point window mean **0.79** dropped below 60% in-band sustain. AD-Sprint-Plan-6 logged.
