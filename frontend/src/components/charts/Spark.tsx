/**
 * File: frontend/src/components/charts/Spark.tsx
 * Purpose: Inline SVG sparkline polyline primitive — pure SVG, no chart lib.
 * Category: Frontend / components / charts (design-system layer)
 * Scope: Phase 57 / Sprint 57.24 Day 1 US-B2 (1st consumer: /cost-dashboard 4-stat grid)
 *
 * Description:
 *   Mockup-direct port of reference/design-mockups/ui.jsx:115-121 (Spark helper).
 *   Renders normalized polyline from `points` over the full width/height,
 *   no fill, no axes. Caller passes raw CSS color string to `tone`
 *   (e.g. "var(--memory)" / "var(--warning)" / hex / rgb).
 *
 *   Planned reuse: Sprint 57.25 /sla-dashboard 4-stat sparklines (Availability /
 *   API p99 / Loop p99 / Error budget) + 57.26-57.28 other dashboards.
 *
 * Created: 2026-05-19 (Sprint 57.24 Day 1 US-B2)
 * Last Modified: 2026-05-19
 *
 * Modification History (newest-first):
 *   - 2026-05-19: Initial creation (Sprint 57.24 Day 1 US-B2) — 1st consumer cost-dashboard
 *
 * Related:
 *   - reference/design-mockups/ui.jsx:115-121 (Spark canonical mockup)
 *   - frontend/src/components/charts/StatCard.tsx (typical consumer)
 */

import type { FC } from "react";

export interface SparkProps {
  points: number[];
  width?: number;
  height?: number;
  tone?: string;
}

export const Spark: FC<SparkProps> = ({
  points,
  width = 90,
  height = 26,
  tone = "var(--primary)",
}) => {
  if (points.length === 0) return null;
  const max = Math.max(...points);
  const min = Math.min(...points);
  const range = max - min || 1;
  const step = points.length > 1 ? width / (points.length - 1) : 0;
  const d = points
    .map(
      (v, i) =>
        `${i === 0 ? "M" : "L"}${(i * step).toFixed(1)},${(height - ((v - min) / range) * height).toFixed(1)}`,
    )
    .join(" ");
  return (
    <svg width={width} height={height} aria-hidden data-testid="spark">
      <path d={d} fill="none" stroke={tone} strokeWidth={1.5} strokeLinecap="round" />
    </svg>
  );
};
