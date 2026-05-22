/**
 * File: frontend/src/features/overview/__fixtures__/kpiSparklines.ts
 * Purpose: KPI sparkline point arrays for the /overview 4-stat row Cost MTD + SLA p95 cards.
 * Category: Frontend / features / overview / __fixtures__
 * Scope: Phase 57 / Sprint 57.27 Day 3 / US-C1
 *
 * Description:
 *   Lifted 1:1 from mockup `reference/design-mockups/page-overview.jsx:93-94`
 *   (Stat spark arrays). Consumed by OverviewPage KPI row StatCard spark prop
 *   via <Spark points={...} />.
 *
 *   COST_MTD_SPARK  → 12-point cumulative cost trend
 *   SLA_P95_SPARK   → 7-point p95 latency trend (most-recent = rightmost)
 *
 * Created: 2026-05-21 (Sprint 57.27 Day 3 / US-C1)
 *
 * Modification History (newest-first):
 *   - 2026-05-21: Initial creation (Sprint 57.27 Day 3) — KPI spark arrays from mockup :93-94
 *
 * Related:
 *   - reference/design-mockups/page-overview.jsx:93-94 (canonical spark values)
 *   - frontend/src/pages/overview/OverviewPage.tsx (consumer)
 *   - frontend/src/components/charts/Spark.tsx (renderer)
 */

/** 12-point cumulative cost trend for Cost MTD stat card (mockup :93). */
export const COST_MTD_SPARK: number[] = [2, 4, 5, 6, 8, 10, 12, 14, 16, 18, 20, 22];

/** 7-point p95 latency trend for SLA p95 stat card (mockup :94). */
export const SLA_P95_SPARK: number[] = [2.0, 2.1, 2.0, 1.9, 1.95, 1.88, 1.84];
