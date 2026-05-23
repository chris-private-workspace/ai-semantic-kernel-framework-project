/**
 * File: frontend/src/features/cost-dashboard/components/ProviderMixCard.tsx
 * Purpose: Admin-scope 4-provider mix card — verbatim re-point to mockup page-admin.jsx:295-317.
 * Category: Frontend / cost-dashboard / components
 * Scope: Phase 57 / Sprint 57.24 Day 2 US-C3 → 57.31 Day 1 (verbatim re-point)
 *
 * Description:
 *   Renders the mockup "Provider mix" admin-scope card: 4 rows (provider-A/
 *   B/C/self-hosted alias) × dot + label + $cost · tokens + .bar-track +
 *   .thin-rule + LLM-neutrality redaction notice (.subtle).
 *
 *   Sprint 57.31 Day 1 verbatim re-point: consume mockup-ui <Card> + <Icon> +
 *   mockup verbatim CSS classes (.col / .spread / .row / .mono / .tnum /
 *   .subtle / .bar-track / .thin-rule); drop translated-Tailwind CardShell /
 *   BarTrack wrappers + Tailwind-bg-tone dot wrappers in favor of inline
 *   `background: var(--*)` literals copied byte-for-byte.
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
 * Last Modified: 2026-05-23
 *
 * Modification History:
 *   - 2026-05-23: Sprint 57.31 Day 1 — verbatim re-point to mockup .col/.spread/.bar-track/.thin-rule/.subtle per page-admin.jsx:295-317
 *   - 2026-05-19: Initial creation (Sprint 57.24 Day 2 US-C3)
 */

/* eslint-disable no-restricted-syntax -- verbatim re-point: inline-style literals (dot bg + .bar-track fill width%/bg) are mockup page-admin.jsx visual-layer literals copied byte-for-byte; STYLE.md §1 escape hatch + frontend-mockup-fidelity.md */

import type { CSSProperties, FC } from "react";
import { useTranslation } from "react-i18next";

import { Card, Icon } from "../../../components/mockup-ui";
import { BackendGapBanner } from "../../../components/ui/BackendGapBanner";
import { PROVIDER_MIX_FIXTURE } from "../__fixtures__/providerMix";

export const ProviderMixCard: FC = () => {
  const { t } = useTranslation("common");
  return (
    <Card
      title={t("cost.provider.title")}
      subtitle={
        <span className="row" style={{ gap: 6 } satisfies CSSProperties}>
          <Icon name="shield" size={11} />
          {t("cost.provider.subtitle")}
        </span>
      }
    >
      {/* verbatim from page-admin.jsx:296-313 — .col + spread row + .bar-track */}
      <div
        className="col"
        style={{ gap: 10 } satisfies CSSProperties}
        data-testid="provider-mix-card"
      >
        {PROVIDER_MIX_FIXTURE.map((row) => (
          <div key={row.label}>
            <div className="spread" style={{ marginBottom: 4 } satisfies CSSProperties}>
              <span className="row" style={{ gap: 6 } satisfies CSSProperties}>
                <span
                  aria-hidden
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: 2,
                    background: row.toneColor,
                  } satisfies CSSProperties}
                />
                <span
                  className="mono"
                  style={{ fontSize: 12 } satisfies CSSProperties}
                >
                  {row.label}
                </span>
              </span>
              <span
                className="mono tnum"
                style={{ fontSize: 11.5 } satisfies CSSProperties}
              >
                ${row.cost} <span className="subtle">· {row.tokens}</span>
              </span>
            </div>
            <div className="bar-track" data-testid="bar-track">
              <span
                data-testid="bar-track-fill"
                data-pct={row.pct}
                style={{
                  width: `${row.pct}%`,
                  background: row.toneColor,
                } satisfies CSSProperties}
              />
            </div>
          </div>
        ))}
        <div className="thin-rule" />
        <div
          data-testid="provider-llm-neutrality-notice"
          className="subtle"
          style={{ fontSize: 11 } satisfies CSSProperties}
        >
          {t("cost.provider.llmNeutralityNotice")}
        </div>
      </div>
      <BackendGapBanner reason={t("cost.banner.crossProvider")} />
    </Card>
  );
};
