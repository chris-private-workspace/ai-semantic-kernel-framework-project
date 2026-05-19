/**
 * File: frontend/src/components/charts/BarTrack.tsx
 * Purpose: Reusable horizontal percentage-bar primitive for breakdown / quota / mix widgets.
 * Category: Frontend / components / charts (design-system layer)
 * Scope: Phase 57 / Sprint 57.24 Day 2 US-C1 (1st consumer: CategoryBarsCard / TenantTopTable / ProviderMixCard)
 *
 * Description:
 *   Mockup-direct port of reference/design-mockups/styles.css .bar-track rule:
 *   2px-tall track on bg-bg-2 background, single span child filled to `pct`%
 *   with caller-provided tone color.
 *
 *   `pct` is clamped to [0, 100]; > 100 callers should signal overflow visually
 *   via tone instead (e.g. tone="hsl(var(--danger))" for quota-over alerts;
 *   see TenantTopTable).
 *
 *   Inline `style` is required for dynamic `width: X%` + `backgroundColor`
 *   (Tailwind utilities cannot express runtime percentages cleanly without
 *   exploding the class table). The escape hatch is documented per STYLE.md §3.
 *
 *   Planned reuse: Sprint 57.24 Day 2 (3 widgets) + Sprint 57.25 sla-dashboard
 *   SLO budget bars + 57.26+ other dashboards' quota / mix widgets.
 *
 * Created: 2026-05-19 (Sprint 57.24 Day 2 US-C1)
 *
 * Modification History:
 *   - 2026-05-19: Initial creation (Sprint 57.24 Day 2 US-C1)
 */

import type { FC } from "react";

export interface BarTrackProps {
  pct: number;
  tone?: string;
  height?: number;
}

export const BarTrack: FC<BarTrackProps> = ({
  pct,
  tone = "hsl(var(--primary))",
  height = 4,
}) => {
  const clamped = Math.min(100, Math.max(0, pct));
  return (
    <div
      data-testid="bar-track"
      className="overflow-hidden rounded-sm bg-bg-2"
      // eslint-disable-next-line no-restricted-syntax -- dynamic track height in px; no Tailwind arbitrary value fits cleanly across heights
      style={{ height: `${height}px` }}
    >
      <span
        data-testid="bar-track-fill"
        data-pct={clamped}
        className="block h-full"
        // eslint-disable-next-line no-restricted-syntax -- dynamic width % + tone color cannot be expressed via Tailwind utility (mockup-fidelity bar fill); STYLE.md §3 escape hatch
        style={{ width: `${clamped}%`, backgroundColor: tone }}
      />
    </div>
  );
};
