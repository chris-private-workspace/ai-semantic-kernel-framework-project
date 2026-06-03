/**
 * File: frontend/src/features/admin-tenants/_fixtures.ts
 * Purpose: Table subtitle ported from mockup `page-admin.jsx` L357.
 * Category: Frontend / admin-tenants / fixtures
 * Scope: Phase 57 / Sprint 57.43 Day 1 (mockup-fidelity rebuild) → Sprint 57.74 (real-data wiring)
 *
 * Description:
 *   Sprint 57.73 (A-6a) wired the tenants TABLE to real GET /api/v1/admin/tenants
 *   (TENANTS_FIXTURE removed). Sprint 57.74 wired the stats STRIP to the real
 *   GET /api/v1/admin/tenants/stats aggregate, so the former STATS_FIXTURE was
 *   likewise removed (orphan per Karpathy §3). Only the static TABLE_SUBTITLE
 *   verbatim port remains.
 *
 * Key Components:
 *   - TABLE_SUBTITLE: card sub line (L357)
 *
 * Created: 2026-05-25 (Sprint 57.43 Day 1)
 * Last Modified: 2026-06-03
 *
 * Modification History (newest-first):
 *   - 2026-06-03: Sprint 57.74 — remove orphan STATS_FIXTURE + StatFixture (strip now real-data)
 *   - 2026-06-03: Sprint 57.73 — remove orphan TENANTS_FIXTURE (table now real-data) + keep STATS_FIXTURE (no stats endpoint)
 *   - 2026-05-25: Initial creation (Sprint 57.43 Day 1) — admin-tenants full mockup-fidelity rebuild
 *
 * Related:
 *   - reference/design-mockups/page-admin.jsx L357
 *   - docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-43-plan.md
 */

export const TABLE_SUBTITLE = "48 active · 3 anomalies in last 24h";
