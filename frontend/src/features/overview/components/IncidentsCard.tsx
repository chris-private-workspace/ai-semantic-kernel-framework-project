/**
 * File: frontend/src/features/overview/components/IncidentsCard.tsx
 * Purpose: /overview recent incidents card — 4 incident rows with RiskBadge + status Badge.
 * Category: Frontend / features / overview / components
 * Scope: Phase 57 / Sprint 57.27 Day 2 / US-C2
 *
 * Description:
 *   1:1 mockup port of `reference/design-mockups/page-overview.jsx:204-225`.
 *   Wraps mockup-ui <Card> (bodyClass="flush" — no padding); body renders one
 *   incident row per RECENT_INCIDENTS fixture entry. Each row: RiskBadge
 *   (sev), mono id, title flex-1, status Badge, since mono right-aligned.
 *
 *   The incidents list API is not yet wired; a visible <BackendGapBanner>
 *   declares fixture data per AP-2 honesty.
 *
 * Key Components:
 *   - IncidentsCard: card + 4 incident rows + backend-gap banner
 *
 * Created: 2026-05-21 (Sprint 57.27 Day 2 / US-B3)
 * Last Modified: 2026-05-22
 *
 * Modification History (newest-first):
 *   - 2026-05-22: Sprint 57.29 US-C2 — verbatim re-point to mockup .row + mockup-ui RiskBadge/Badge
 *   - 2026-05-21: Initial creation (Sprint 57.27 Day 2 / US-C2) — extract from OverviewPage inline
 *
 * Related:
 *   - reference/design-mockups/page-overview.jsx:204-225 (IncidentsCard canonical)
 *   - frontend/src/features/overview/__fixtures__/incidents.ts (fixture data)
 *   - frontend/src/components/mockup-ui.tsx (Card / Button / Badge / RiskBadge primitives)
 *   - frontend/src/components/ui/BackendGapBanner.tsx (shared)
 */

/* eslint-disable no-restricted-syntax -- verbatim re-point: inline styles are mockup page-overview.jsx visual-layer literals copied byte-for-byte; re-expressing as Tailwind IS the drift bug this epic kills (STYLE.md §1 escape hatch + frontend-mockup-fidelity.md) */

import type { CSSProperties, FC } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { BackendGapBanner } from "@/components/ui/BackendGapBanner";
import { Badge, Button, Card, RiskBadge } from "@/components/mockup-ui";
import type { RiskLevel } from "@/components/mockup-ui";

import { RECENT_INCIDENTS } from "../__fixtures__/incidents";

export const IncidentsCard: FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const openCount = RECENT_INCIDENTS.filter((i) => i.status !== "resolved").length;

  return (
    <Card
      title={t("overview.incidents.title")}
      subtitle={`${openCount} ${t("overview.incidents.subtitle")}`}
      actions={
        <Button
          variant="ghost"
          size="sm"
          iconRight="arrow_right"
          onClick={() => navigate("/incidents")}
        >
          {t("overview.incidents.allIncidents")}
        </Button>
      }
      bodyClass="flush"
    >
      {/* verbatim from page-overview.jsx:211-224 */}
      <div>
        {RECENT_INCIDENTS.map((inc, i) => (
          <div
            key={inc.id}
            className="row"
            style={{
              gap: 10,
              padding: "10px 14px",
              borderBottom: i < RECENT_INCIDENTS.length - 1 ? "1px solid var(--border)" : "none",
              fontSize: 12.5,
              cursor: "pointer",
            } satisfies CSSProperties}
            onClick={() => navigate("/incidents")}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") navigate("/incidents"); }}
          >
            <RiskBadge level={inc.sev as RiskLevel} />
            <span className="mono" style={{ fontSize: 11.5, width: 64 } satisfies CSSProperties}>{inc.id}</span>
            <span style={{ flex: 1 } satisfies CSSProperties}>{inc.title}</span>
            <Badge tone={inc.status === "resolved" ? "success" : inc.status === "open" ? "warning" : ""}>
              {inc.status}
            </Badge>
            <span className="mono subtle" style={{ fontSize: 11, width: 40, textAlign: "right" } satisfies CSSProperties}>{inc.since}</span>
          </div>
        ))}
      </div>
      <BackendGapBanner reason={t("overview.incidents.backendGap")} />
    </Card>
  );
};
