/**
 * File: frontend/src/features/sla-dashboard/components/ErrorRateByServiceCard.tsx
 * Purpose: Per-service error rate card (Sprint 57.25 Day 2 US-C3).
 * Category: Frontend / sla-dashboard / components (feature-scoped)
 * Scope: Phase 57 / Sprint 57.25 Day 2 US-C3
 *
 * Description:
 *   Mockup-direct port of reference/design-mockups/page-admin.jsx:131-152.
 *   6 rows × service + rate% + BarTrack; rate > 0.5 triggers warning tone.
 *
 *   BarTrack width = rate × 50 (mockup line 147 algorithm — scales 0-2%
 *   range to full bar width); tone warning when > 0.5, success otherwise.
 *
 *   Backend per-service error rate aggregation pending Phase 58+
 *   AD-SLA-Dashboard-Backend-Extensions; BackendGapBanner rendered below.
 *
 * Created: 2026-05-19 (Sprint 57.25 Day 2 US-C3)
 *
 * Modification History:
 *   - 2026-05-19: Initial creation (Sprint 57.25 Day 2 US-C3)
 *
 * Related:
 *   - reference/design-mockups/page-admin.jsx:131-152 (canonical mockup)
 *   - sprint-57-25-plan.md §Technical Spec §ErrorRateByServiceCard structure
 */

import { useTranslation } from "react-i18next";

import { BarTrack } from "../../../components/charts";
import { BackendGapBanner } from "../../../components/ui/BackendGapBanner";
import { CardShell } from "../../../components/ui/CardShell";
import { cn } from "../../../lib/utils";
import { ERROR_RATE_BY_SERVICE } from "../__fixtures__/errorRateByService";

const WARNING_THRESHOLD_PCT = 0.5;
const BAR_WIDTH_SCALE = 50; // mockup line 147: width = rate * 50

export function ErrorRateByServiceCard() {
  const { t } = useTranslation("common");

  return (
    <div data-testid="sla-error-rate-card-wrap">
      <CardShell
        title={t("sla.errorRate.title")}
        subtitle={t("sla.errorRate.subtitle")}
      >
        <div className="flex flex-col gap-2.5" data-testid="sla-error-rate-card">
          {ERROR_RATE_BY_SERVICE.map((row, idx) => {
            const warn = row.rate > WARNING_THRESHOLD_PCT;
            return (
              <div key={row.name} data-testid={`sla-error-rate-row-${idx}`}>
                <div className="mb-1 flex items-center justify-between">
                  <span className="font-mono text-[11.5px]">{row.name}</span>
                  <span
                    className={cn(
                      "font-mono text-[11px] tabular-nums",
                      warn ? "text-warning" : "text-fg-muted",
                    )}
                    data-testid={`sla-error-rate-pct-${idx}`}
                  >
                    {row.rate.toFixed(2)}%
                  </span>
                </div>
                <BarTrack
                  pct={Math.min(100, row.rate * BAR_WIDTH_SCALE)}
                  tone={warn ? "var(--warning)" : "var(--success)"}
                />
              </div>
            );
          })}
        </div>
      </CardShell>
      <BackendGapBanner reason={t("sla.banner.perServiceErrorRate")} />
    </div>
  );
}
