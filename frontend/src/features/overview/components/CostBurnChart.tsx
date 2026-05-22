/**
 * File: frontend/src/features/overview/components/CostBurnChart.tsx
 * Purpose: /overview cost-burn bespoke SVG chart — 30-day spend vs budget diagonal.
 * Category: Frontend / features / overview / components
 * Scope: Phase 57 / Sprint 57.27 Day 2 / US-C1
 *
 * Description:
 *   1:1 mockup port of `reference/design-mockups/page-overview.jsx:273-329`.
 *   Chart-only component (NO CardShell wrapper — the OverviewPage Card wraps it).
 *   SVG viewBox 360×130, padding l:30 r:8 t:8 b:22.
 *
 *   Elements (per mockup):
 *   - y gridlines at [0,1050,2100,3150,4200] dashed + $ mono labels
 *   - budget diagonal dashed line + "budget $4,200" text label
 *   - burnGrad linearGradient (primary 0.32 → 0 transparency)
 *   - burn area fill + burn line primary 1.5px + endpoint circle r3
 *   - x-axis labels: "day 1" / "today" (primary colour) / "day 30"
 *   - legend row: $X MTD / $Y on-pace target / over-pace|under-pace
 *
 *   The cost-dashboard 30-day history API is not yet wired; a visible
 *   <BackendGapBanner> declares fixture data per AP-2 honesty.
 *
 * Key Components:
 *   - CostBurnChart: SVG chart + legend + backend-gap banner
 *
 * Created: 2026-05-21 (Sprint 57.27 Day 2 / US-B3)
 * Last Modified: 2026-05-22
 *
 * Modification History (newest-first):
 *   - 2026-05-22: Sprint 57.29 US-C2 — verbatim re-point legend to mockup .row/.mono classes
 *   - 2026-05-21: Initial creation (Sprint 57.27 Day 2 / US-C1) — extract from OverviewPage inline
 *
 * Related:
 *   - reference/design-mockups/page-overview.jsx:273-329 (CostBurnChart canonical)
 *   - frontend/src/features/overview/__fixtures__/costBurn.ts (fixture data)
 *   - frontend/src/components/ui/BackendGapBanner.tsx (shared)
 */

/* eslint-disable no-restricted-syntax -- verbatim re-point: inline styles are mockup page-overview.jsx visual-layer literals copied byte-for-byte; re-expressing as Tailwind IS the drift bug this epic kills (STYLE.md §1 escape hatch + frontend-mockup-fidelity.md) */

import type { CSSProperties, FC } from "react";
import { useTranslation } from "react-i18next";

import { BackendGapBanner } from "@/components/ui/BackendGapBanner";

import { COST_BURN } from "../__fixtures__/costBurn";

const W = 360;
const H = 130;
const PAD = { l: 30, r: 8, t: 8, b: 22 };
const INNER_W = W - PAD.l - PAD.r;
const INNER_H = H - PAD.t - PAD.b;
const MAX_Y = 4200;

const xAt = (i: number, days: number) => PAD.l + (i / (days - 1)) * INNER_W;
const yAt = (v: number) => PAD.t + INNER_H - (v / MAX_Y) * INNER_H;

export const CostBurnChart: FC = () => {
  const { t } = useTranslation();
  const { days, today, dailyBudget, cumulative } = COST_BURN;

  const budgetLine = `M ${xAt(0, days)} ${yAt(0)} L ${xAt(days - 1, days)} ${yAt(4200)}`;
  const burnPath = cumulative
    .map((v, i) => `${i === 0 ? "M" : "L"} ${xAt(i, days)} ${yAt(v)}`)
    .join(" ");
  const burnArea = `${burnPath} L ${xAt(today - 1, days)} ${yAt(0)} L ${xAt(0, days)} ${yAt(0)} Z`;

  const mtd = cumulative[today - 1] ?? 0;
  const onPace = dailyBudget * today;
  const isOverPace = mtd > onPace;

  return (
    <div className="col" style={{ gap: 8 }}>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        style={{ width: "100%", height: H }}
        aria-label={t("overview.costBurn.title")}
      >
        <defs>
          <linearGradient id="overview-costburn-grad" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="var(--primary)" stopOpacity={0.32} />
            <stop offset="100%" stopColor="var(--primary)" stopOpacity={0} />
          </linearGradient>
        </defs>
        {/* y gridlines */}
        {[0, 1050, 2100, 3150, 4200].map((v) => (
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
              ${v}
            </text>
          </g>
        ))}
        {/* budget diagonal dashed line */}
        <path
          d={budgetLine}
          stroke="var(--fg-subtle)"
          strokeDasharray="4 3"
          strokeWidth="1"
          fill="none"
        />
        <text
          x={W - PAD.r}
          y={yAt(4200) - 4}
          textAnchor="end"
          fontSize={9}
          fill="var(--fg-subtle)"
          fontFamily="var(--font-mono)"
        >
          budget $4,200
        </text>
        {/* burn area + line */}
        <path d={burnArea} fill="url(#overview-costburn-grad)" />
        <path d={burnPath} stroke="var(--primary)" strokeWidth="1.5" fill="none" />
        <circle
          cx={xAt(today - 1, days)}
          cy={yAt(mtd)}
          r="3"
          fill="var(--primary)"
        />
        {/* x axis labels */}
        <text
          x={PAD.l}
          y={H - 6}
          fontSize={9}
          fill="var(--fg-subtle)"
          fontFamily="var(--font-mono)"
        >
          day 1
        </text>
        <text
          x={xAt(today - 1, days)}
          y={H - 6}
          textAnchor="middle"
          fontSize={9}
          fill="var(--primary)"
          fontFamily="var(--font-mono)"
        >
          today
        </text>
        <text
          x={W - PAD.r}
          y={H - 6}
          textAnchor="end"
          fontSize={9}
          fill="var(--fg-subtle)"
          fontFamily="var(--font-mono)"
        >
          day 30
        </text>
      </svg>
      {/* legend row — verbatim from page-overview.jsx:319-327 */}
      <div className="row" style={{ gap: 10, fontSize: 11, color: "var(--fg-muted)" } satisfies CSSProperties}>
        <span><span className="mono" style={{ color: "var(--primary)" } satisfies CSSProperties}>${mtd.toFixed(0)}</span> {t("overview.costBurn.mtd")}</span>
        <span style={{ flex: 1 } satisfies CSSProperties} />
        <span><span className="mono">${onPace.toFixed(0)}</span> {t("overview.costBurn.onPaceTarget")}</span>
        <span style={{ color: isOverPace ? "var(--warning)" : "var(--success)" } satisfies CSSProperties}>
          {isOverPace ? t("overview.costBurn.overPace") : t("overview.costBurn.underPace")}
        </span>
      </div>
      <BackendGapBanner reason={t("overview.costBurn.backendGap")} />
    </div>
  );
};
