/**
 * File: frontend/src/components/charts/AreaChart.tsx
 * Purpose: Inline SVG area chart primitive — pure SVG, gradient fill + line stroke.
 * Category: Frontend / components / charts (design-system layer)
 * Scope: Phase 57 / Sprint 57.24 Day 1 US-B3 (1st consumer: /cost-dashboard 30d Spend over time card)
 *
 * Description:
 *   Mockup-direct port of reference/design-mockups/page-admin.jsx:5-29
 *   (AreaChart helper). Renders a 760×h SVG with viewBox preserveAspectRatio
 *   "none" (scales to container), 3 horizontal grid lines (25/50/75% positions),
 *   gradient-filled area path + stroke line path.
 *
 *   `data` is the value series; max normalized to (peak × 1.15) for headroom.
 *   `tone` accepts raw CSS color string (e.g. "var(--memory)"); gradient
 *   ID derives from sanitized tone string (uniqueness across multiple instances).
 *
 *   Planned reuse: Sprint 57.25 /sla-dashboard latency chart base (3-series
 *   extension via composition) + 57.26+ other dashboards.
 *
 * Created: 2026-05-19 (Sprint 57.24 Day 1 US-B3)
 * Last Modified: 2026-05-19
 *
 * Modification History (newest-first):
 *   - 2026-05-19: Initial creation (Sprint 57.24 Day 1 US-B3) — 1st consumer cost-dashboard
 *
 * Related:
 *   - reference/design-mockups/page-admin.jsx:5-29 (AreaChart canonical mockup)
 *   - frontend/src/components/ui/CardShell.tsx (typical wrapping card)
 */

import type { FC } from "react";

export interface AreaChartProps {
  data: number[];
  tone?: string;
  height?: number;
}

const VIEW_WIDTH = 760;
const PADDING = 24;

export const AreaChart: FC<AreaChartProps> = ({
  data,
  tone = "var(--primary)",
  height = 180,
}) => {
  if (data.length === 0) return null;
  const max = Math.max(...data) * 1.15;
  const step = data.length > 1 ? (VIEW_WIDTH - PADDING * 2) / (data.length - 1) : 0;
  const points = data.map(
    (v, i): [number, number] => [
      PADDING + i * step,
      height - PADDING - (v / max) * (height - PADDING * 2),
    ],
  );
  const line = points
    .map((p, i) => `${i === 0 ? "M" : "L"}${p[0].toFixed(1)},${p[1].toFixed(1)}`)
    .join(" ");
  const lastX = points[points.length - 1][0];
  const area = `${line} L${lastX.toFixed(1)},${height - PADDING} L${PADDING},${height - PADDING} Z`;
  const gradientId = `area-gradient-${tone.replace(/[^a-zA-Z]/g, "")}`;
  return (
    <svg
      viewBox={`0 0 ${VIEW_WIDTH} ${height}`}
      preserveAspectRatio="none"
      className="w-full"
      height={height}
      data-testid="area-chart"
    >
      <defs>
        <linearGradient id={gradientId} x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor={tone} stopOpacity="0.32" />
          <stop offset="100%" stopColor={tone} stopOpacity="0" />
        </linearGradient>
      </defs>
      <g aria-hidden>
        {[0.25, 0.5, 0.75].map((t) => (
          <line
            key={t}
            x1={PADDING}
            x2={VIEW_WIDTH - PADDING}
            y1={PADDING + (height - PADDING * 2) * t}
            y2={PADDING + (height - PADDING * 2) * t}
            stroke="var(--border)"
            strokeWidth="0.5"
            opacity="0.6"
          />
        ))}
      </g>
      <path d={area} fill={`url(#${gradientId})`} data-testid="area-fill" />
      <path
        d={line}
        fill="none"
        stroke={tone}
        strokeWidth="1.5"
        data-testid="area-line"
      />
    </svg>
  );
};
