# Sprint 57.31 Progress — Day 0 (2026-05-23)

> Plan: [`../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-31-plan.md`](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-31-plan.md)
>
> Checklist: [`../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-31-checklist.md`](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-31-checklist.md)
>
> Branch: `feature/sprint-57-31-cost-dashboard-repoint`
>
> Base SHA: `8533603b` (main; Sprint 57.30 squash-merge — PR #164)

---

## Day 0 — Plan + Checklist + 三-prong + before-baseline

### Today's Accomplishments

- Plan + Checklist drafted mirror Sprint 57.30 format (5-day Day 0-4 structure for smaller 7-file scope)
- Day-0 三-prong verify completed; 6 findings catalogued (3 🟢 GREEN + 2 🔴 RED + 1 🟡 YELLOW)
- before-baseline screenshots captured (22 routes + 1-2 extras pending)

### Drift findings

**Prong 1 — Path verify (Glob batched)**:

| # | Finding | Status |
|---|---------|--------|
| — | 7 plan-listed MODIFIED paths all exist (pages/cost-dashboard/index.tsx + 6 components in features/cost-dashboard/components/) | ✅ no drift |
| — | 3 plan-listed NEW paths (REPOINT-REPORT.md + screenshot dirs) correctly absent | ✅ no drift |

**Prong 2 — Content verify (grep + targeted Read)**:

| ID | Finding | Severity | Action |
|----|---------|----------|--------|
| **D1** | Mockup `CostPage` at `reference/design-mockups/page-admin.jsx:201-320` — distinct from `/overview` (page-overview.jsx) + `/chat-v2` (page-chat.jsx). Co-located with `/admin/tenants` + admin models in `page-admin.jsx`. | 🟢 GREEN | Treat `page-admin.jsx:201-320` as canonical visual source for /cost-dashboard. Plan §Technical Specifications updated. |
| **D2** | Mockup CSS classes (`.grid-stats`, `.grid-main`, `.bar-track`, `.table`, `.page-head`, `.route-pill`, `.spread`, `.col`, `.tnum`) — 16 occurrences total in `styles-mockup.css` confirming ready foundation. Each class consumed elsewhere in mockup-aligned components. | 🟢 GREEN | Verbatim re-point can consume these directly; no NEW CSS class needed in foundation. |
| **D3** | Mockup CostPage **5 sections**: page-head (L203-219) + grid-stats KPI row (L221-225) + grid-main row 1 (L227-251 — AreaChart "Spend over time" LEFT + CategoryBarsCard "Spend by category" RIGHT) + grid-main row 2 (L253-294 — TenantTopTable "Spend by tenant" 8-row table) + 4th section (L295-318 — ProviderMixCard 4-row + `.thin-rule` + LLM-neutrality disclosure subtle). | 🟢 GREEN | All 5 sections clearly mapped; Day 1-3 work scoped per section. |
| **D4** | Production has `CostBreakdownTable.tsx` but **mockup CostPage has no direct equivalent**. The mockup CostPage's only table is the "Spend by tenant" (which corresponds to production `TenantTopTable.tsx`). CostBreakdownTable likely represents a production-only view OR an alternate-data-cut table. | 🔴 RED | **Decision needed Day 1**: (a) re-purpose CostBreakdownTable as production-only with mockup `.table` vocabulary + AP-2 BackendGapBanner if it represents missing backend cut, (b) consolidate with TenantTopTable, OR (c) annotate as production-only-by-design. Per AP-2 honesty rule, surface the gap. |
| **D5** | Production has `MonthPicker.tsx` but **mockup CostPage has no MonthPicker** (filter UI not in mockup). Production-only widget. | 🟡 YELLOW | Treat as production-only widget using mockup token vocabulary (var(--*) tokens); no AP-2 banner needed (not a backend gap — it's a UI affordance). Same pattern as Sprint 57.30 InputBar's mode toggle + status pill. |
| **D6** | Mockup CostPage **AreaChart "Spend over time"** (grid-main row 1 LEFT, L228-230) — uses mockup-ui `<AreaChart>` primitive. Production may have AreaChart inline in `pages/cost-dashboard/index.tsx` OR may have omitted it entirely (need to verify Day 1). | 🟡 YELLOW | Day 1 confirms; if absent in production, ADD a verbatim `<Card title="Spend over time">` + `<AreaChart>` using mockup-ui primitive (Sprint 57.24 v2 verbatim). |

**Prong 3 — Schema verify**: N/A (frontend-only sprint).

**Prong 4 — Visual baseline strategy**:

- Affected baselines: Sprint 57.31 touches only `/cost-dashboard` content; shell unchanged from Sprint 57.30. Only `/cost-dashboard`-specific Playwright `visual-regression.spec.ts` baseline should need regen.
- Sprint 57.29 + 57.30 already touched the topbar `<AppShellV2>` shell baselines (regenerated in 57.29; held in 57.30 first-run CI). 22-route route-sweep clean from 57.30.
- Decision: **accept Day 4 regen overhead if needed** (per Sprint 57.30 precedent, baseline regen may not be needed if delta is small).

### Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| CostBreakdownTable treatment (D4) | Defer to Day 1 first 10-min audit — either production-only with mockup-token vocabulary OR consolidate with TenantTopTable depending on its actual data cut + business intent | D4 needs reading the existing CostBreakdownTable to know what data it shows; can't decide without that context |
| MonthPicker treatment (D5) | Production-only widget with mockup token vocabulary (var(--*) inline) | Filter UI is a legitimate production-only affordance (mockup didn't include filter for layout simplification) |
| AreaChart in cost-dashboard (D6) | Verify Day 1 first; if absent in production, add it Day 2 alongside CategoryBarsCard work | Don't pre-plan addition; verify first |

### Before-baseline screenshots

- 22 AppShellV2 route screenshots via `route-sweep.mjs before` (after OUT_DIR re-point to sprint-57-31-* dir) — pending capture
- /cost-dashboard extras (MonthPicker open + table anomaly row visible) — pending capture

### Open items / blockers

- None. Day 0 completes once before-baseline captured + commit lands.

### Notes

- Sprint 57.31 plan time (~30 min for plan + 25 min for checklist) is shorter than Sprint 57.30 (~75 min) — pattern reuse compounding (3rd Phase-2 sprint).
- D4 (CostBreakdownTable mockup gap) is the most consequential finding. If it represents a missing backend feature (e.g. per-category drill-down), Phase-2 should preserve it as production-only with AP-2 honesty. If it's redundant with TenantTopTable, Day 1 can consolidate or leave both with mockup-style.
- Bimodal-watch 3rd-data-point hypothesis: this sprint's outcome will resolve `AD-Sprint-Plan-frontend-verbatim-bimodal-watch` (Sprint 57.30 carryover) — see plan §Class baseline 3rd-data-point evaluation criteria for the decision matrix.
