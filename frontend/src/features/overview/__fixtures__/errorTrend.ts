/**
 * File: frontend/src/features/overview/__fixtures__/errorTrend.ts
 * Purpose: Fixture 24-hour error-count array for ErrorTrendChart.
 * Category: Frontend / features / overview / __fixtures__
 * Scope: Phase 57 / Sprint 57.27 Day 2 / US-B3
 *
 * Description:
 *   Lifted 1:1 from mockup `reference/design-mockups/page-overview.jsx:68`
 *   (ERROR_24H const). The telemetry hourly-bucket API is not yet wired, so
 *   ErrorTrendChart ships this fixture + a visible <BackendGapBanner> per AP-2
 *   honesty; the backend wire folds into AD-Overview-Backend-Extensions-Phase58.
 *
 * Created: 2026-05-21 (Sprint 57.27 Day 2 / US-B3)
 *
 * Modification History (newest-first):
 *   - 2026-05-21: Initial creation (Sprint 57.27 Day 2) — lift inline ERROR_24H const to fixture
 *
 * Related:
 *   - reference/design-mockups/page-overview.jsx:68 (ERROR_24H canonical)
 *   - frontend/src/features/overview/components/ErrorTrendChart.tsx (consumer)
 */

/** 24 hourly error counts verbatim from mockup page-overview.jsx:68. */
export const ERROR_24H: number[] = [
  3, 2, 4, 1, 0, 2, 1, 0, 0, 1, 3, 5, 8, 12, 9, 6, 4, 3, 5, 7, 4, 2, 1, 2,
];
