/**
 * File: frontend/src/features/overview/__fixtures__/costBurn.ts
 * Purpose: Fixture cost-burn data for CostBurnChart — 30-day budget formula from mockup.
 * Category: Frontend / features / overview / __fixtures__
 * Scope: Phase 57 / Sprint 57.27 Day 2 / US-B3
 *
 * Description:
 *   Lifted 1:1 from mockup `reference/design-mockups/page-overview.jsx:275-281`
 *   (CostBurnChart data formula). The cost-dashboard 30-day history API is not
 *   yet wired, so CostBurnChart ships this fixture + a visible <BackendGapBanner>
 *   per AP-2 honesty; the backend wire folds into AD-Overview-Backend-Extensions-Phase58.
 *
 * Created: 2026-05-21 (Sprint 57.27 Day 2 / US-B3)
 *
 * Modification History (newest-first):
 *   - 2026-05-21: Initial creation (Sprint 57.27 Day 2) — lift inline CostBurnChart const to fixture
 *
 * Related:
 *   - reference/design-mockups/page-overview.jsx:273-329 (CostBurnChart canonical)
 *   - frontend/src/features/overview/components/CostBurnChart.tsx (consumer)
 */

const days = 30;
const today = 18;
const budgetUsd = 4200;
const dailyBudget = budgetUsd / days; // = 140

const spent = Array.from({ length: today }, (_, i) =>
  dailyBudget * (0.6 + (i / today) * 0.9 + Math.sin(i * 0.7) * 0.15),
);

const cumulative = spent.reduce<number[]>(
  (acc, v, i) => [...acc, (acc[i - 1] ?? 0) + v],
  [],
);

export interface CostBurnFixture {
  days: number;
  today: number;
  budgetUsd: number;
  dailyBudget: number;
  cumulative: number[];
}

export const COST_BURN: CostBurnFixture = {
  days,
  today,
  budgetUsd,
  dailyBudget,
  cumulative,
};
