# Sprint 57.27 Retrospective — AD-Mockup-Fidelity-Rebuild-Overview

**Sprint**: 57.27 — `/overview` full mockup-strict rebuild
**Class**: `frontend-mockup-strict-rebuild` 0.60 (4th application)
**Closed**: 2026-05-21
**Branch**: `feature/sprint-57-27-overview-rebuild` (7 commits from main `fb27df73`)
**Outcome**: ✅ 9/9 widgets rebuilt 1:1 from `reference/design-mockups/page-overview.jsx`; DRIFT-REPORT verdict **PARITY**

---

## Q1 — What was delivered

Full mockup-fidelity rebuild of `/overview` (operator dashboard): the 728-line all-in-one `OverviewPage.tsx` → ~215-line clean assembly of **9 feature widget components**:

| Group | Widgets | Day |
|-------|---------|-----|
| B | ActiveLoopsCard · HITLQueueCard | 1 |
| C | CostBurnChart · ErrorTrendChart · ProvidersCard · IncidentsCard · QuickActionsStrip | 2 |
| D | page-head + KPI row + grid assembly | 3 |

- New `frontend/src/features/overview/` directory: 7 widget components + `_primitives.tsx` (Badge/RiskBadge) + 5 `__fixtures__/*.ts` + 7 Vitest specs.
- Shared primitive reuse: `CardShell`, `PageHead`, `StatCard`, `Spark`, `BackendGapBanner` (from Sprint 57.24/57.25 dashboard epic).
- **R9 (user decision)**: `CardShell` card-title `text-sm` → `text-[12.5px]` — closes D8 across `/overview` + `/cost-dashboard` + `/sla-dashboard`.
- 16 drift IDs (D1-D16) from Day 0 + D17 logged during build; D1-D14 + D16 closed, D17 accepted addition, D15 carryover.
- Vitest 430 → **457** (+27); lint + build clean; 0 backend changes; 0 LLM SDK leak.

## Q2 — Calibration (4th `frontend-mockup-strict-rebuild` data point)

- **Plan §Workload**: bottom-up ~6.5 hr → calibrated commit ~3.9 hr (multiplier 0.60).
- **Actual**: ≈ 3.7 hr-equivalent (estimated — agent-assisted compressed session, not rigorously per-day hour-tracked; same caveat as Sprint 57.13 matrix row).
- **Ratio actual/committed ≈ 0.95** — ✅ in `[0.85, 1.20]` band.
- **Ratio actual/bottom-up ≈ 0.57** — bottom-up ~1.7× generous; the 0.60 multiplier landed close.
- **4-data-point series**: 57.23=0.59 / 57.24=1.19 / 57.25=0.88 / **57.27≈0.95** → 4-pt mean **0.90**, in-band lower-middle.

### Q2.1 — #41 rich-dashboard sub-class DECISION

Sprint 57.24 v2 retro hypothesised a `frontend-mockup-strict-rebuild` rich-dashboard sub-class running higher; 57.25 retro DEFERRED pending a 4th data point (`AD-Sprint-Plan-rich-dashboard-sub-class-DEFER` #41).

`/overview` is a rich operator dashboard (2 charts + 4-stat KPI row + 4 cards) — the same shape as cost/sla-dashboard. Rich-dashboard sub-set ratios: 57.24=1.19 / 57.25=0.88 / 57.27≈0.95 → **3-pt mean ≈ 1.01**, squarely in-band middle.

**DECISION: DROP the rich-dashboard sub-class proposal (#41 RESOLVED — no split).** Three rich data points average ~1.0 in-band; there is no distinct rich-dashboard cost signal to justify a separate multiplier. KEEP the single `frontend-mockup-strict-rebuild` 0.60 baseline for the whole class.

## Q3 — What went well

- **Primitive reuse paid off** — `CardShell`/`_primitives`/`BackendGapBanner` + the Day-1-established widget pattern meant Day-2's 5 widgets and Day-3 assembly were largely mechanical ports. No primitive extraction cost.
- **AP-3 reversal completed cleanly** — 728-line all-in-one → ~215-line assembly; 0 inline Card/Badge/Stat/RiskBadge definitions remain. Orphan inline primitives removed (Karpathy §3).
- **Day-0 三-prong caught real drift early** — D-PRE-2 (no `/overview` in visual-regression) removed a risk; D-PRE-6 (Loop type gaps) + D-PRE-8 (AUDIT-REPORT Unit 7 wrong page-title claim) shaped the build correctly.
- **Honest pair-verify** — found the ActiveLoopsCard live-data 404; recorded it truthfully rather than papering over with a screenshot of the empty state.

## Q4 — What to improve

- **Agent `Scope` header errors** — both code-implementer delegations wrote wrong `US-` tags in file headers (Day-2 widgets `US-B3`; OverviewPage `US-C1`). Caught in review pre-commit, but the delegation prompt should state the exact US number per file next time.
- **Agent hardcoded `acme-prod · operator`** in the page-head meta — the mockup hardcodes it, but production should read auth context (ActiveLoopsCard Day 1 already set the `useAuthStore` precedent). Caught in review. Delegation prompts for mockup ports should explicitly say "mockup literal X → real data source Y".
- **ActiveLoopsCard is not actually a real-data widget in practice** — its `GET /api/v1/loops` endpoint 404s, so it always renders the error state. It was treated as "the ONE real-data widget" (no BackendGapBanner) but the backing endpoint does not exist. → Q6 carryover.

## Q5 — Discipline check (V2 紀律 9 項)

1. Server-Side First ✅ frontend-only · 2. LLM Neutrality ✅ N/A · 3. CC Reference ✅ mockup-direct · 4. 17.md single-source ✅ no new contract · 5. 11+1 範疇 ✅ frontend · 6. anti-patterns ✅ (AP-3 reversal completed; AP-2 honesty via BackendGapBanner) · 7. Sprint workflow ✅ plan→checklist→三-prong→code→progress→retro · 8. File header ✅ (Scope errors caught + fixed) · 9. Multi-tenant ✅ N/A.

Rolling-planning ✅ — no future sprint plan pre-written; no unchecked `[ ]` deleted (deferred items marked 🚧); retrospective contains no concrete future-sprint tasks.

## Q6 — Carryover

- **D15** — Active Loops `maxTurns` hardcoded 50; `Session` ORM gap → existing `AD-Loop-Session-Enrich-Phase58`.
- **ActiveLoopsCard live-data 404** (NEW) — `GET /api/v1/loops` endpoint absent; widget always shows error state. Phase 58: build the endpoint OR fixture-back the widget. → `AD-Overview-Backend-Extensions-Phase58`.
- **AD-Overview-Backend-Extensions-Phase58** (NEW) — 8 fixture-backed `/overview` widgets + the absent loops endpoint need real backend APIs.
- **R9 side-effect re-verify** — `/cost-dashboard` + `/sla-dashboard` consume the changed `CardShell`; a light pair-verify pass to confirm the 12.5px title → next dashboard-touching sprint.
- **`/overview` visual-regression coverage** — D-PRE-2: `/overview` is not in `visual-regression.spec.ts`; optionally add it (deferred — Ops Dashboards sprint candidate).

## Q7 — Commits

| Commit | Scope |
|--------|-------|
| `43eedcee` | Day 0 — plan + checklist + 三-prong + DRIFT skeleton |
| `9c4fd7f6` | Day 1 — ActiveLoopsCard + HITLQueueCard |
| `0305c739` | Day 1 — doc backfill |
| `2bd7c776` | Day 2 — 5 Group-C widgets |
| `179ca17b` | Day 2 — doc backfill |
| `dd405c6b` | Day 3 — OverviewPage final assembly + R9 CardShell |
| `5cbfe7b7` | Day 3 — assembly doc backfill |
| _(pending)_ | Day 3 closeout — DRIFT verdict + retro + memory + calibration |
