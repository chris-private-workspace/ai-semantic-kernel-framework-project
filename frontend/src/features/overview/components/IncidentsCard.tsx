/**
 * File: frontend/src/features/overview/components/IncidentsCard.tsx
 * Purpose: /overview recent incidents card — 4 incident rows with RiskBadge + status Badge.
 * Category: Frontend / features / overview / components
 * Scope: Phase 57 / Sprint 57.27 Day 2 / US-C2
 *
 * Description:
 *   1:1 mockup port of `reference/design-mockups/page-overview.jsx:204-225`.
 *   Wraps the shared <CardShell> (flush body — no padding); body renders one
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
 *
 * Modification History (newest-first):
 *   - 2026-05-21: Initial creation (Sprint 57.27 Day 2 / US-C2) — extract from OverviewPage inline
 *
 * Related:
 *   - reference/design-mockups/page-overview.jsx:204-225 (IncidentsCard canonical)
 *   - frontend/src/features/overview/__fixtures__/incidents.ts (fixture data)
 *   - frontend/src/components/ui/CardShell.tsx + BackendGapBanner.tsx (shared)
 *   - frontend/src/features/overview/components/_primitives.tsx (Badge + RiskBadge)
 */

import { ArrowRight } from "lucide-react";
import type { FC } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { BackendGapBanner } from "@/components/ui/BackendGapBanner";
import { CardShell } from "@/components/ui/CardShell";

import { RECENT_INCIDENTS } from "../__fixtures__/incidents";
import { Badge, RiskBadge } from "./_primitives";

export const IncidentsCard: FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const openCount = RECENT_INCIDENTS.filter((i) => i.status !== "resolved").length;

  return (
    <CardShell
      title={t("overview.incidents.title")}
      subtitle={`${openCount} ${t("overview.incidents.subtitle")}`}
      actions={
        <button
          type="button"
          onClick={() => navigate("/incidents")}
          className="flex items-center gap-1 text-[11px] text-fg-muted hover:text-foreground"
        >
          {t("overview.incidents.allIncidents")} <ArrowRight className="h-3 w-3" />
        </button>
      }
      bodyClass=""
    >
      <div>
        {RECENT_INCIDENTS.map((inc, i) => (
          <button
            key={inc.id}
            type="button"
            onClick={() => navigate("/incidents")}
            className={`flex w-full cursor-pointer items-center gap-[10px] px-[14px] py-[10px] text-left text-[12.5px] hover:bg-bg-hover ${
              i < RECENT_INCIDENTS.length - 1 ? "border-b border-border" : ""
            }`}
          >
            <RiskBadge level={inc.sev} />
            <span className="w-[64px] font-mono text-[11.5px]">{inc.id}</span>
            <span className="flex-1">{inc.title}</span>
            <Badge
              tone={
                inc.status === "resolved"
                  ? "success"
                  : inc.status === "open"
                    ? "warning"
                    : "muted"
              }
            >
              {inc.status}
            </Badge>
            <span className="w-[40px] text-right font-mono text-[11px] text-fg-muted">
              {inc.since}
            </span>
          </button>
        ))}
      </div>
      <BackendGapBanner reason={t("overview.incidents.backendGap")} />
    </CardShell>
  );
};
