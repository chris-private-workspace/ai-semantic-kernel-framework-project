/**
 * File: frontend/src/features/overview/components/HITLQueueCard.tsx
 * Purpose: /overview HITL-queue card — 3 risk-tinted pending-approval cards (fixture).
 * Category: Frontend / features / overview / components
 * Scope: Phase 57 / Sprint 57.27 Day 1 / US-B2
 *
 * Description:
 *   1:1 mockup port of `reference/design-mockups/page-overview.jsx:143-167`.
 *   Wraps the shared <CardShell> (dense body); body renders one risk-tinted
 *   card per HITL_QUEUE fixture row. Critical-risk rows take the mockup
 *   `oklch(from var(--danger) l c h / 0.08)` tint + 0.4-alpha border.
 *
 *   The governance pending-approvals aggregation API is not yet wired, so a
 *   visible <BackendGapBanner> declares the AD-Overview-Backend-Extensions-
 *   Phase58 carryover per AP-2 honesty.
 *
 * Key Components:
 *   - HITLQueueCard: card + 3 risk-tinted approval cards + backend-gap banner
 *
 * Created: 2026-05-21 (Sprint 57.27 Day 1 / US-B2)
 *
 * Modification History (newest-first):
 *   - 2026-05-21: Initial creation (Sprint 57.27 Day 1) — extract from OverviewPage inline + banner
 *
 * Related:
 *   - reference/design-mockups/page-overview.jsx:143-167 (HITL card canonical)
 *   - frontend/src/features/overview/__fixtures__/hitlQueue.ts (fixture data)
 *   - frontend/src/components/ui/CardShell.tsx + BackendGapBanner.tsx (shared)
 */

import { ArrowRight } from "lucide-react";
import type { FC } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { BackendGapBanner } from "@/components/ui/BackendGapBanner";
import { CardShell } from "@/components/ui/CardShell";

import { HITL_QUEUE } from "../__fixtures__/hitlQueue";
import { RiskBadge } from "./_primitives";

export const HITLQueueCard: FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  return (
    <CardShell
      title={t("overview.hitlQueue.title")}
      subtitle={`${HITL_QUEUE.length} pending`}
      actions={
        <button
          type="button"
          onClick={() => navigate("/governance")}
          className="flex items-center gap-1 text-[11px] text-fg-muted hover:text-foreground"
        >
          {t("overview.hitlQueue.review")} <ArrowRight className="h-3 w-3" />
        </button>
      }
      bodyClass="p-2.5"
    >
      <div className="flex flex-col gap-[10px]">
        {HITL_QUEUE.map((req) => (
          <button
            key={req.id}
            type="button"
            onClick={() => navigate("/governance")}
            className={`flex flex-col gap-[6px] rounded-[6px] border p-[10px] text-left ${
              req.risk === "critical"
                ? "border-danger/40 bg-danger/8"
                : "border-border bg-bg-1"
            }`}
          >
            <div className="flex items-center justify-between gap-[6px]">
              <RiskBadge level={req.risk} />
              <span className="font-mono text-[10.5px] text-fg-subtle">
                SLA · {req.sla}
              </span>
            </div>
            <div className="text-[12.5px] font-medium leading-snug">{req.title}</div>
            <div className="font-mono text-[10.5px] text-fg-subtle">
              {req.id} · from {req.requester}
            </div>
          </button>
        ))}
      </div>
      <BackendGapBanner reason={t("overview.hitlQueue.backendGap")} />
    </CardShell>
  );
};
