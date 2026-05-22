/**
 * File: frontend/src/features/overview/components/HITLQueueCard.tsx
 * Purpose: /overview HITL-queue card — 3 risk-tinted pending-approval cards (fixture).
 * Category: Frontend / features / overview / components
 * Scope: Phase 57 / Sprint 57.27 Day 1 / US-B2
 *
 * Description:
 *   1:1 mockup port of `reference/design-mockups/page-overview.jsx:143-167`.
 *   Wraps mockup-ui <Card> (bodyClass="dense"); body renders one risk-tinted
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
 * Last Modified: 2026-05-22
 *
 * Modification History (newest-first):
 *   - 2026-05-22: Sprint 57.29 US-C2 — verbatim re-point to mockup .card dense + oklch tints
 *   - 2026-05-21: Initial creation (Sprint 57.27 Day 1) — extract from OverviewPage inline + banner
 *
 * Related:
 *   - reference/design-mockups/page-overview.jsx:143-167 (HITL card canonical)
 *   - frontend/src/features/overview/__fixtures__/hitlQueue.ts (fixture data)
 *   - frontend/src/components/mockup-ui.tsx (Card / Button / RiskBadge primitives)
 *   - frontend/src/components/ui/BackendGapBanner.tsx (shared)
 */

/* eslint-disable no-restricted-syntax -- verbatim re-point: inline styles are mockup page-overview.jsx visual-layer literals copied byte-for-byte; re-expressing as Tailwind IS the drift bug this epic kills (STYLE.md §1 escape hatch + frontend-mockup-fidelity.md) */

import type { CSSProperties, FC } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { BackendGapBanner } from "@/components/ui/BackendGapBanner";
import { Button, Card, RiskBadge } from "@/components/mockup-ui";
import type { RiskLevel } from "@/components/mockup-ui";

import { HITL_QUEUE } from "../__fixtures__/hitlQueue";

export const HITLQueueCard: FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  return (
    <Card
      title={t("overview.hitlQueue.title")}
      subtitle={`${HITL_QUEUE.length} pending`}
      actions={
        <Button
          variant="ghost"
          size="sm"
          iconRight="arrow_right"
          onClick={() => navigate("/governance")}
        >
          {t("overview.hitlQueue.review")}
        </Button>
      }
      bodyClass="dense"
    >
      {/* verbatim from page-overview.jsx:149-166 */}
      <div className="col" style={{ gap: 10 }}>
        {HITL_QUEUE.map((req) => (
          <button
            key={req.id}
            type="button"
            className="col"
            style={{
              gap: 6,
              padding: 10,
              border: `1px solid ${req.risk === "critical" ? "oklch(from var(--danger) l c h / 0.4)" : "var(--border)"}`,
              borderRadius: "var(--radius-sm)",
              cursor: "pointer",
              background: req.risk === "critical" ? "oklch(from var(--danger) l c h / 0.08)" : "var(--bg-1)",
            } satisfies CSSProperties}
            onClick={() => navigate("/governance")}
          >
            <div className="row" style={{ gap: 6, justifyContent: "space-between" } satisfies CSSProperties}>
              <RiskBadge level={req.risk as RiskLevel} />
              <span className="mono subtle" style={{ fontSize: 10.5 } satisfies CSSProperties}>SLA · {req.sla}</span>
            </div>
            <div style={{ fontSize: 12.5, fontWeight: 500, lineHeight: 1.4 } satisfies CSSProperties}>{req.title}</div>
            <div className="mono subtle" style={{ fontSize: 10.5 } satisfies CSSProperties}>{req.id} · from {req.requester}</div>
          </button>
        ))}
      </div>
      <BackendGapBanner reason={t("overview.hitlQueue.backendGap")} />
    </Card>
  );
};
