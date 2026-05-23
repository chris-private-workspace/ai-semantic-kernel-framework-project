/**
 * File: frontend/src/features/sla-dashboard/components/TimeRangeTabs.tsx
 * Purpose: 4-button time-range tab group for SLA Dashboard page-actions (Sprint 57.25 Day 1 US-B1; Sprint 57.32 Day 1 US-B1 verbatim re-point).
 * Category: Frontend / sla-dashboard / components
 * Scope: Phase 57 / Sprint 57.32 Day 1 US-B1 (verbatim re-point)
 *
 * Description:
 *   Mockup-direct verbatim port of `reference/design-mockups/page-admin.jsx:43-48`
 *   `.btn-group` with 4 range buttons (1h ghost / 24h outline-active /
 *   7d ghost / 30d ghost). Per user Q2 alignment (2026-05-19), this
 *   sprint ships visual-only with local React useState active tab; clicks
 *   change active highlight but do NOT refetch data (backend time-range
 *   aggregation endpoint pending Phase 58+
 *   AD-SLA-Dashboard-Backend-Extensions-Phase58).
 *
 *   Sprint 57.32 Day 1 US-B1: Phase-2 verbatim CSS re-point. The
 *   container Tailwind class `inline-flex items-center rounded-md border
 *   border-border bg-bg-1 p-0.5` is replaced with mockup `.btn-group`
 *   (styles-mockup.css:461-465). The per-button Tailwind classes are
 *   replaced with mockup-ui `<Button>` primitive (variant ghost/outline,
 *   size sm). role="tablist" + aria-selected + data-testid preserved.
 *
 *   AP-2 honesty: the broader LatencyChart 24h widget below carries the
 *   BackendGapBanner declaring time-range aggregation pending; this
 *   component itself stays minimal (4-button group with role="tablist").
 *
 * Created: 2026-05-19 (Sprint 57.25 Day 1 US-B1)
 * Last Modified: 2026-05-23
 *
 * Modification History:
 *   - 2026-05-23: Sprint 57.32 Day 1 US-B1 — verbatim re-point: .btn-group + mockup-ui Button (closes phase-2 translated-Tailwind drift)
 *   - 2026-05-19: Initial creation (Sprint 57.25 Day 1 US-B1)
 *
 * Related:
 *   - reference/design-mockups/page-admin.jsx:43-48 (canonical mockup)
 *   - frontend/src/styles-mockup.css:461-465 (.btn-group foundation)
 *   - frontend/src/components/mockup-ui.tsx (Button primitive)
 *   - sprint-57-32-plan.md §US-B1
 */

import { useState } from "react";
import { useTranslation } from "react-i18next";

import { Button } from "../../../components/mockup-ui";

type Range = "1h" | "24h" | "7d" | "30d";
const RANGES: Range[] = ["1h", "24h", "7d", "30d"];

export function TimeRangeTabs() {
  const { t } = useTranslation("common");
  const [active, setActive] = useState<Range>("24h");
  return (
    <div
      role="tablist"
      aria-label={t("sla.range.label")}
      data-testid="sla-range-tabs"
      className="btn-group"
    >
      {RANGES.map((r) => {
        const isActive = active === r;
        return (
          <Button
            key={r}
            variant={isActive ? "outline" : "ghost"}
            size="sm"
            role="tab"
            aria-selected={isActive}
            onClick={() => setActive(r)}
            data-testid={`sla-range-tab-${r}`}
          >
            {t(`sla.range.${r}`)}
          </Button>
        );
      })}
    </div>
  );
}
