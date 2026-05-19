/**
 * File: frontend/src/features/cost-dashboard/components/ProviderMixCard.tsx
 * Purpose: Admin-scope 4-provider mix card per mockup page-admin.jsx:295-317.
 * Category: Frontend / cost-dashboard / components
 * Scope: Phase 57 / Sprint 57.24 Day 2 US-C3
 *
 * Description:
 *   Renders the mockup "Provider mix" admin-scope card: 4 rows (provider-A/
 *   B/C/self-hosted alias) × dot + label + $cost · tokens + BarTrack +
 *   LLM-neutrality redaction notice at bottom.
 *
 *   Admin scope gate: this component is ADMIN-AGNOSTIC; parent CostOverview
 *   checks isPlatformAdmin and conditionally mounts (same pattern as
 *   TenantTopTable US-C2).
 *
 *   Data source: fully-fixture (PROVIDER_MIX_FIXTURE). Cross-provider
 *   aggregation backend API pending Phase 58+ AD-Cost-Dashboard-Backend-
 *   Extensions. BackendGapBanner marks fixture state per AP-2.
 *
 *   The LLM-neutrality notice explains WHY provider identity is redacted
 *   (V2 §約束 3 architectural rationale); this is mockup-faithful copy
 *   distinct from the AP-2 fixture-state BackendGapBanner.
 *
 * Created: 2026-05-19 (Sprint 57.24 Day 2 US-C3)
 *
 * Modification History:
 *   - 2026-05-19: Initial creation (Sprint 57.24 Day 2 US-C3)
 */

import { Shield } from "lucide-react";
import type { FC } from "react";
import { useTranslation } from "react-i18next";

import { BarTrack } from "../../../components/charts/BarTrack";
import { BackendGapBanner } from "../../../components/ui/BackendGapBanner";
import { CardShell } from "../../../components/ui/CardShell";
import { PROVIDER_MIX_FIXTURE } from "../__fixtures__/providerMix";

export const ProviderMixCard: FC = () => {
  const { t } = useTranslation("common");
  return (
    <CardShell
      title={t("cost.provider.title")}
      subtitle={
        <span className="inline-flex items-center gap-1.5">
          <Shield size={11} aria-hidden />
          {t("cost.provider.subtitle")}
        </span>
      }
    >
      <div className="flex flex-col gap-2.5" data-testid="provider-mix-card">
        {PROVIDER_MIX_FIXTURE.map((row) => (
          <div key={row.label}>
            <div className="mb-1 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <span
                  aria-hidden
                  className={`inline-block h-2 w-2 rounded-sm ${row.toneClass}`}
                />
                <span className="font-mono text-xs">{row.label}</span>
              </span>
              <span className="font-mono text-[11.5px] tabular-nums">
                ${row.cost}
                <span className="text-fg-muted"> · {row.tokens}</span>
              </span>
            </div>
            <BarTrack pct={row.pct} tone={row.toneColor} />
          </div>
        ))}
      </div>
      <div className="mt-3 border-t border-border pt-3" />
      <p
        data-testid="provider-llm-neutrality-notice"
        className="text-[11px] text-fg-muted"
      >
        {t("cost.provider.llmNeutralityNotice")}
      </p>
      <BackendGapBanner reason={t("cost.banner.crossProvider")} />
    </CardShell>
  );
};
