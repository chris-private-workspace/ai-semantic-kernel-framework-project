/**
 * File: frontend/src/features/overview/__fixtures__/incidents.ts
 * Purpose: Fixture recent-incident rows for IncidentsCard.
 * Category: Frontend / features / overview / __fixtures__
 * Scope: Phase 57 / Sprint 57.27 Day 2 / US-B3
 *
 * Description:
 *   Lifted 1:1 from mockup `reference/design-mockups/page-overview.jsx:54-59`
 *   (RECENT_INCIDENTS const). The incidents list API is not yet wired, so
 *   IncidentsCard ships this fixture + a visible <BackendGapBanner> per AP-2
 *   honesty; the backend wire folds into AD-Overview-Backend-Extensions-Phase58.
 *
 * Created: 2026-05-21 (Sprint 57.27 Day 2 / US-B3)
 *
 * Modification History (newest-first):
 *   - 2026-05-21: Initial creation (Sprint 57.27 Day 2) — lift inline RECENT_INCIDENTS const to fixture
 *
 * Related:
 *   - reference/design-mockups/page-overview.jsx:54-59 (RECENT_INCIDENTS canonical)
 *   - frontend/src/features/overview/components/IncidentsCard.tsx (consumer)
 */

export interface Incident {
  id: string;
  title: string;
  sev: "low" | "medium" | "high" | "critical";
  status: "open" | "investigating" | "resolved";
  since: string;
}

export const RECENT_INCIDENTS: Incident[] = [
  {
    id: "INC-2451",
    title: "p95 latency breach · gpt-4.1 provider",
    sev: "high",
    status: "open",
    since: "12m",
  },
  {
    id: "INC-2447",
    title: "redaction rule false-positive · acme-prod",
    sev: "low",
    status: "investigating",
    since: "1h",
  },
  {
    id: "INC-2440",
    title: "subagent budget exceeded x4 · globex-eu",
    sev: "medium",
    status: "open",
    since: "2h",
  },
  {
    id: "INC-2438",
    title: "kb_search vector index rebuild",
    sev: "low",
    status: "resolved",
    since: "3h",
  },
];
