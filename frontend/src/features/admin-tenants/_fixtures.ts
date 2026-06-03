/**
 * File: frontend/src/features/admin-tenants/_fixtures.ts
 * Purpose: Stats-strip fixture + table subtitle ported from mockup `page-admin.jsx` L350-357.
 * Category: Frontend / admin-tenants / fixtures
 * Scope: Phase 57 / Sprint 57.43 Day 1 (mockup-fidelity rebuild) → Sprint 57.73 (real-data wiring)
 *
 * Description:
 *   Sprint 57.73 (A-6a) wired the tenants TABLE to real GET /api/v1/admin/tenants,
 *   so the former TENANTS_FIXTURE was removed (orphan per Karpathy §3). The 4-stat
 *   strip has NO aggregate-stats endpoint, so STATS_FIXTURE stays — the strip
 *   marks itself placeholder via AP-2 BackendGapBanner.
 *
 * Key Components:
 *   - STATS_FIXTURE: 4-stat verbatim port (L350-355) — still placeholder (no backend)
 *   - TABLE_SUBTITLE: card sub line (L357)
 *
 * Created: 2026-05-25 (Sprint 57.43 Day 1)
 * Last Modified: 2026-06-03
 *
 * Modification History (newest-first):
 *   - 2026-06-03: Sprint 57.73 — remove orphan TENANTS_FIXTURE (table now real-data) + keep STATS_FIXTURE (no stats endpoint)
 *   - 2026-05-25: Initial creation (Sprint 57.43 Day 1) — admin-tenants full mockup-fidelity rebuild
 *
 * Related:
 *   - reference/design-mockups/page-admin.jsx L350-357
 *   - docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-43-plan.md
 */

export interface StatFixture {
  label: string;
  value: string;
  delta: string;
  deltaDir: "up" | "down";
}

export const STATS_FIXTURE: StatFixture[] = [
  { label: "Active tenants", value: "48", delta: "+3", deltaDir: "up" },
  { label: "Total seats", value: "284", delta: "+18", deltaDir: "up" },
  { label: "Agents deployed", value: "612", delta: "+24", deltaDir: "up" },
  { label: "Anomalies", value: "1", delta: "+1", deltaDir: "down" },
];

export const TABLE_SUBTITLE = "48 active · 3 anomalies in last 24h";
