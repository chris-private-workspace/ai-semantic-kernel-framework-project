/**
 * File: frontend/src/features/overview/components/ErrorTrendChart.tsx
 * Purpose: /overview error-trend bespoke SVG bar chart — 24h hourly error buckets.
 * Category: Frontend / features / overview / components
 * Scope: Phase 57 / Sprint 57.27 Day 2 / US-C1
 *
 * Description:
 *   1:1 mockup port of `reference/design-mockups/page-overview.jsx:331-379`.
 *   Chart-only component (NO CardShell wrapper — the OverviewPage Card wraps it).
 *   SVG viewBox 360×130, padding l:30 r:8 t:8 b:22.
 *
 *   Elements (per mockup):
 *   - y gridlines at [0,4,8,12] dashed + numeric labels
 *   - 24 bars, tone by value (≥10 → danger, ≥6 → warning, else → info)
 *   - fillOpacity 0.85, rx 1 per mockup
 *   - x-axis labels: "-24h" / "-12h" / "now"
 *   - legend row: X errors · 24h / Y peak / hour / rising|stable
 *
 *   The telemetry hourly-bucket API is not yet wired; a visible
 *   <BackendGapBanner> declares fixture data per AP-2 honesty.
 *
 * Key Components:
 *   - ErrorTrendChart: SVG bar chart + legend + backend-gap banner
 *
 * Created: 2026-05-21 (Sprint 57.27 Day 2 / US-B3)
 *
 * Modification History (newest-first):
 *   - 2026-05-21: Initial creation (Sprint 57.27 Day 2 / US-C1) — extract from OverviewPage inline
 *
 * Related:
 *   - reference/design-mockups/page-overview.jsx:331-379 (ErrorTrendChart canonical)
 *   - frontend/src/features/overview/__fixtures__/errorTrend.ts (fixture data)
 *   - frontend/src/components/ui/BackendGapBanner.tsx (shared)
 */

import type { FC } from "react";
import { useTranslation } from "react-i18next";

import { BackendGapBanner } from "@/components/ui/BackendGapBanner";

import { ERROR_24H } from "../__fixtures__/errorTrend";

const W = 360;
const H = 130;
const PAD = { l: 30, r: 8, t: 8, b: 22 };
const INNER_W = W - PAD.l - PAD.r;
const INNER_H = H - PAD.t - PAD.b;

export const ErrorTrendChart: FC = () => {
  const { t } = useTranslation();

  const maxY = Math.max(...ERROR_24H, 10);
  const xAt = (i: number) => PAD.l + (i / (ERROR_24H.length - 1)) * INNER_W;
  const yAt = (v: number) => PAD.t + INNER_H - (v / maxY) * INNER_H;
  const bw = (INNER_W / ERROR_24H.length) * 0.7;

  const total = ERROR_24H.reduce((a, b) => a + b, 0);
  const peak = Math.max(...ERROR_24H);
  const last3Sum = ERROR_24H.slice(-3).reduce((a, b) => a + b, 0);
  const isRising = last3Sum > 10;

  return (
    <div className="flex flex-col gap-2">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="w-full"
        height={H}
        aria-label={t("overview.errors.title")}
      >
        {/* y gridlines */}
        {[0, 4, 8, 12].map((v) => (
          <g key={v}>
            <line
              x1={PAD.l}
              x2={W - PAD.r}
              y1={yAt(v)}
              y2={yAt(v)}
              stroke="var(--border)"
              strokeDasharray="2 2"
            />
            <text
              x={PAD.l - 4}
              y={yAt(v) + 3}
              textAnchor="end"
              fontSize={9}
              fill="var(--fg-subtle)"
              fontFamily="var(--font-mono)"
            >
              {v}
            </text>
          </g>
        ))}
        {/* 24 bars */}
        {ERROR_24H.map((v, i) => {
          const fill =
            v >= 10
              ? "var(--danger)"
              : v >= 6
                ? "var(--warning)"
                : "var(--info)";
          return (
            <rect
              key={i}
              x={xAt(i) - bw / 2}
              y={yAt(v)}
              width={bw}
              height={INNER_H - (yAt(v) - PAD.t)}
              fill={fill}
              fillOpacity={0.85}
              rx={1}
            />
          );
        })}
        {/* x axis labels */}
        <text
          x={PAD.l}
          y={H - 6}
          fontSize={9}
          fill="var(--fg-subtle)"
          fontFamily="var(--font-mono)"
        >
          -24h
        </text>
        <text
          x={W / 2}
          y={H - 6}
          textAnchor="middle"
          fontSize={9}
          fill="var(--fg-subtle)"
          fontFamily="var(--font-mono)"
        >
          -12h
        </text>
        <text
          x={W - PAD.r}
          y={H - 6}
          textAnchor="end"
          fontSize={9}
          fill="var(--fg-subtle)"
          fontFamily="var(--font-mono)"
        >
          now
        </text>
      </svg>
      {/* legend row */}
      <div className="flex items-center gap-[10px] text-[11px] text-fg-muted">
        <span>
          <span className="font-mono text-danger">{total}</span>{" "}
          {t("overview.errors.errorsLabel")}
        </span>
        <span className="flex-1" />
        <span>
          <span className="font-mono">{peak}</span>{" "}
          {t("overview.errors.peakLabel")}
        </span>
        {/* eslint-disable-next-line no-restricted-syntax -- dynamic per-trend colour (STYLE.md §1 escape hatch; no static Tailwind class for conditional CSS var) */}
        <span style={{ color: isRising ? "var(--warning)" : "var(--success)" }}>
          {isRising ? t("overview.errors.rising") : t("overview.errors.stable")}
        </span>
      </div>
      <BackendGapBanner reason={t("overview.errors.backendGap")} />
    </div>
  );
};
