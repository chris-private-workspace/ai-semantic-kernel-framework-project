/**
 * File: frontend/src/features/overview/__fixtures__/hitlQueue.ts
 * Purpose: Fixture HITL-queue pending-approval rows for the /overview HITLQueueCard.
 * Category: Frontend / features / overview / __fixtures__
 * Scope: Phase 57 / Sprint 57.27 Day 1 / US-B2
 *
 * Description:
 *   Lifted 1:1 from mockup `reference/design-mockups/page-overview.jsx:48-52`
 *   (HITL_QUEUE) and the prior inline OverviewPage.tsx const. The governance
 *   pending-approvals aggregation API is not yet wired, so HITLQueueCard ships
 *   this fixture + a visible <BackendGapBanner> per AP-2 honesty; the backend
 *   wire folds into AD-Overview-Backend-Extensions-Phase58.
 *
 * Created: 2026-05-21 (Sprint 57.27 Day 1 / US-B2)
 *
 * Modification History (newest-first):
 *   - 2026-05-21: Initial creation (Sprint 57.27 Day 1) — lift inline HITL_QUEUE const to fixture
 *
 * Related:
 *   - reference/design-mockups/page-overview.jsx:48-52 (HITL_QUEUE canonical)
 *   - frontend/src/features/overview/components/HITLQueueCard.tsx (consumer)
 */

export interface HitlQueueItem {
  id: string;
  title: string;
  risk: "low" | "medium" | "high" | "critical";
  requester: string;
  sla: string;
}

export const HITL_QUEUE: HitlQueueItem[] = [
  {
    id: "appr_91",
    title: "salesforce_update — refund $4,820",
    risk: "high",
    requester: "sess_7c11d",
    sla: "3h 12m",
  },
  {
    id: "appr_92",
    title: "email_send — refund confirmation to 14 customers",
    risk: "medium",
    requester: "sess_7c11d",
    sla: "3h 14m",
  },
  {
    id: "appr_88",
    title: "servicenow_create_ticket — P1 incident escalation",
    risk: "critical",
    requester: "sess_4f88c",
    sla: "23m",
  },
];
