/**
 * File: frontend/src/features/sla-dashboard/components/LatencyChart.tsx
 * Purpose: 24h LatencyChart 3-series multi-line SVG (Sprint 57.25 Day 1 US-B3).
 * Category: Frontend / sla-dashboard / components (feature-scoped; NOT extracted to components/charts/)
 * Scope: Phase 57 / Sprint 57.25 Day 1 US-B3
 *
 * Description:
 *   Mockup-direct port of `reference/design-mockups/page-admin.jsx:157-198`
 *   LatencyChart helper. 3-series multi-line SVG (p50 / p95 / p99) over 48
 *   time points (24h sliding window @ 30min intervals). Axis labels: x at
 *   i=0,12,24,36,47 (-23h / -17h / -11h / -5h / -0h); y at 4 ticks
 *   normalized to max.
 *
 *   Per Karpathy §2 "extract on 2nd consumer" — this component is KEPT
 *   inline in features/sla-dashboard/ (only 1 consumer this sprint).
 *   Sprint 57.26+ may extract to components/charts/ if 2nd consumer
 *   arises (current carryover: AD-LatencyChart-Extraction-Phase58).
 *
 *   Color tones (mockup-faithful):
 *   - p50 → var(--primary) stroke 1.8 (most prominent)
 *   - p95 → var(--info)   stroke 1.4
 *   - p99 → var(--warning) stroke 1.4 opacity 0.9
 *
 *   Backend 24h time-series aggregation pending Phase 58+
 *   AD-SLA-Dashboard-Backend-Extensions-Phase58; AP-2 banner rendered by
 *   parent CardShell wrapper.
 *
 * Created: 2026-05-19 (Sprint 57.25 Day 1 US-B3)
 * Last Modified: 2026-05-19
 *
 * Modification History:
 *   - 2026-05-19: Initial creation (Sprint 57.25 Day 1 US-B3)
 *
 * Related:
 *   - reference/design-mockups/page-admin.jsx:157-198 (canonical mockup)
 *   - frontend/src/features/sla-dashboard/__fixtures__/latencyChart24h.ts (fixture)
 */

import { LATENCY_24H, type LatencyDataPoint } from "../__fixtures__/latencyChart24h";

const WIDTH = 760;
const HEIGHT = 220;
const PAD = 30;
const SERIES: Array<{ key: keyof LatencyDataPoint; stroke: string; width: number; opacity: number }> = [
  { key: "p50", stroke: "var(--primary)", width: 1.8, opacity: 1 },
  { key: "p95", stroke: "var(--info)", width: 1.4, opacity: 1 },
  { key: "p99", stroke: "var(--warning)", width: 1.4, opacity: 0.9 },
];

export function LatencyChart() {
  if (LATENCY_24H.length === 0) return null;
  const max = Math.max(...LATENCY_24H.map((d) => d.p99)) * 1.1;
  const step = (WIDTH - PAD * 2) / (LATENCY_24H.length - 1);

  return (
    <svg
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      preserveAspectRatio="none"
      height={HEIGHT}
      className="w-full"
      data-testid="sla-latency-chart"
      aria-label="24h latency distribution chart"
    >
      {/* horizontal grid lines at 25/50/75% */}
      <g stroke="var(--border)" strokeWidth={1} opacity={0.4}>
        {[0.25, 0.5, 0.75].map((t) => {
          const y = PAD + (HEIGHT - PAD * 2) * t;
          return <line key={t} x1={PAD} x2={WIDTH - PAD} y1={y} y2={y} />;
        })}
      </g>

      {/* axis labels */}
      <g fill="var(--fg-muted)" fontSize={9} fontFamily="ui-monospace">
        {[0, 12, 24, 36, 47].map((i) => (
          <text
            key={`x-${i}`}
            x={PAD + i * step}
            y={HEIGHT - 8}
            textAnchor="middle"
            data-testid={`sla-latency-chart-x-tick-${i}`}
          >
            -{Math.round((47 - i) / 2)}h
          </text>
        ))}
        {[0, 0.25, 0.5, 0.75].map((t) => (
          <text
            key={`y-${t}`}
            x={PAD - 6}
            y={PAD + (HEIGHT - PAD * 2) * t + 3}
            textAnchor="end"
            data-testid={`sla-latency-chart-y-tick-${t}`}
          >
            {Math.round(max * (1 - t))}ms
          </text>
        ))}
      </g>

      {/* 3 series multi-line paths */}
      {SERIES.map(({ key, stroke, width, opacity }) => {
        const d = LATENCY_24H.map((dp, i) => {
          const x = PAD + i * step;
          const y = HEIGHT - PAD - (dp[key] / max) * (HEIGHT - PAD * 2);
          return `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
        }).join(" ");
        return (
          <path
            key={key}
            d={d}
            fill="none"
            stroke={stroke}
            strokeWidth={width}
            opacity={opacity}
            data-testid={`sla-latency-chart-series-${key}`}
          />
        );
      })}
    </svg>
  );
}
