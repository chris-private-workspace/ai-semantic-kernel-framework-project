/**
 * File: frontend/src/components/charts/index.ts
 * Purpose: Barrel for shared chart primitives (Sprint 57.24 introduction).
 * Category: Frontend / components / charts
 * Scope: Phase 57 / Sprint 57.24 Day 1 US-B2/B3 + Day 2 US-C1
 *
 * Modification History:
 *   - 2026-05-19: Sprint 57.24 Day 2 US-C1 — add BarTrack export
 *   - 2026-05-19: Sprint 57.24 Day 1 US-B3 — add AreaChart export
 *   - 2026-05-19: Initial creation — Spark + StatCard exports (Sprint 57.24 Day 1 US-B2)
 */

export { AreaChart, type AreaChartProps } from "./AreaChart";
export { BarTrack, type BarTrackProps } from "./BarTrack";
export { Spark, type SparkProps } from "./Spark";
export { StatCard, type StatCardProps } from "./StatCard";
