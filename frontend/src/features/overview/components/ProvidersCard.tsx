/**
 * File: frontend/src/features/overview/components/ProvidersCard.tsx
 * Purpose: /overview providers traffic-light card — 4 provider rows with state dots.
 * Category: Frontend / features / overview / components
 * Scope: Phase 57 / Sprint 57.27 Day 2 / US-C2
 *
 * Description:
 *   1:1 mockup port of `reference/design-mockups/page-overview.jsx:180-199`.
 *   Wraps mockup-ui <Card> (bodyClass="dense"); body renders one provider row per
 *   PROVIDERS fixture entry. Each row: coloured traffic-dot via verbatim
 *   trafficDot() inline-style function (8px circle + oklch-glow ring),
 *   mono name, p95 label, call count right-aligned.
 *
 *   D-PRE-1 contract: data-testid="traffic-dot-${state}" is preserved on the
 *   dot span (Day-1 三-prong requirement, tested by the e2e suite).
 *
 *   The telemetry provider traffic-light API is not yet wired; a visible
 *   <BackendGapBanner> declares fixture data per AP-2 honesty.
 *
 * Key Components:
 *   - ProvidersCard: card + 4 provider rows + backend-gap banner
 *
 * Created: 2026-05-21 (Sprint 57.27 Day 2 / US-B3)
 * Last Modified: 2026-05-22
 *
 * Modification History (newest-first):
 *   - 2026-05-22: Sprint 57.29 US-C2 — verbatim re-point to mockup .row + trafficDot() inline
 *   - 2026-05-21: Initial creation (Sprint 57.27 Day 2 / US-C2) — extract from OverviewPage inline
 *
 * Related:
 *   - reference/design-mockups/page-overview.jsx:180-199 (ProvidersCard canonical)
 *   - frontend/src/features/overview/__fixtures__/providers.ts (fixture data)
 *   - frontend/src/components/mockup-ui.tsx (Card / Button primitives)
 *   - frontend/src/components/ui/BackendGapBanner.tsx (shared)
 */

/* eslint-disable no-restricted-syntax -- verbatim re-point: inline styles are mockup page-overview.jsx visual-layer literals copied byte-for-byte; re-expressing as Tailwind IS the drift bug this epic kills (STYLE.md §1 escape hatch + frontend-mockup-fidelity.md) */

import type { CSSProperties, FC } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { BackendGapBanner } from "@/components/ui/BackendGapBanner";
import { Button, Card } from "@/components/mockup-ui";

import { PROVIDERS } from "../__fixtures__/providers";

// Verbatim from page-overview.jsx:28-32 — typed TrafficState for exhaustive mapping
type TrafficState = "green" | "amber" | "red";

function trafficDot(state: TrafficState): CSSProperties {
  const colorVar =
    state === "green"
      ? "var(--success)"
      : state === "amber"
        ? "var(--warning)"
        : "var(--danger)";
  return {
    width: 8,
    height: 8,
    borderRadius: "50%",
    background: colorVar,
    boxShadow: `0 0 0 3px oklch(from ${colorVar} l c h / 0.18)`,
  };
}

export const ProvidersCard: FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  return (
    <Card
      title={t("overview.providers.title")}
      subtitle={`${PROVIDERS.length} providers · 24h`}
      actions={
        <Button
          variant="ghost"
          size="sm"
          iconRight="arrow_right"
          onClick={() => navigate("/sla-dashboard")}
        >
          {t("overview.providers.details")}
        </Button>
      }
      bodyClass="dense"
    >
      {/* verbatim from page-overview.jsx:186-198 */}
      <div className="col" style={{ gap: 0 }}>
        {PROVIDERS.map((p, i) => (
          <div
            key={p.name}
            className="row"
            style={{
              gap: 10,
              padding: "10px 4px",
              borderBottom: i < PROVIDERS.length - 1 ? "1px solid var(--border)" : "none",
            } satisfies CSSProperties}
          >
            {/* D-PRE-1: data-testid preserved — Day-0 三-prong contract */}
            <span
              data-testid={`traffic-dot-${p.state}`}
              style={trafficDot(p.state as TrafficState)}
            />
            <span className="mono" style={{ fontSize: 12, flex: 1 } satisfies CSSProperties}>{p.name}</span>
            <span className="mono subtle" style={{ fontSize: 11 } satisfies CSSProperties}>p95 {p.p95}s</span>
            <span className="mono subtle" style={{ fontSize: 11, width: 60, textAlign: "right" } satisfies CSSProperties}>{p.calls}</span>
          </div>
        ))}
      </div>
      <BackendGapBanner reason={t("overview.providers.backendGap")} />
    </Card>
  );
};
