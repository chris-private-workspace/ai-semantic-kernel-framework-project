/**
 * File: frontend/src/features/cost-dashboard/__fixtures__/spendOverTime30d.ts
 * Purpose: 30-day Spend over time fixture for /cost-dashboard AreaChart (Sprint 57.24 US-B3).
 * Category: Frontend / cost-dashboard / fixtures
 * Scope: Phase 57 / Sprint 57.24 Day 1 US-B3
 *
 * Description:
 *   Mirrors mockup reference/design-mockups/page-admin.jsx:227 inline data
 *   array (30 daily spend values, climbing from $80 to $284, matching
 *   mockup "Spend MTD = $2,847" final stat). Used as AreaChart fixture
 *   until backend 30-day daily history endpoint lands (tracked in Phase 58+
 *   AD-Cost-Dashboard-Backend-Extensions).
 *
 * Created: 2026-05-19 (Sprint 57.24 Day 1 US-B3)
 *
 * Modification History:
 *   - 2026-05-19: Initial creation (Sprint 57.24 Day 1 US-B3)
 */

export const SPEND_OVER_TIME_30D: number[] = [
  80, 90, 85, 95, 110, 105, 120, 115, 130, 140, 128, 150, 145, 160, 170, 165,
  180, 175, 190, 200, 195, 210, 220, 230, 225, 240, 255, 250, 265, 284,
];
