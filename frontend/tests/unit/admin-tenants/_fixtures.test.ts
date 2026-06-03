/**
 * File: frontend/tests/unit/admin-tenants/_fixtures.test.ts
 * Purpose: Vitest schema integrity coverage for admin-tenants table subtitle.
 * Category: Frontend / Tests / admin-tenants / unit
 * Scope: Phase 57 / Sprint 57.43 Day 2 → Sprint 57.74 (real-data wiring)
 *
 * Description:
 *   Karpathy §2 minimal but useful — schema integrity lock for the only
 *   remaining fixture-backed value after the real-data wiring sprints:
 *   - TABLE_SUBTITLE matches verbatim mockup string
 *   STATS_FIXTURE removed Sprint 57.74 (strip now real GET /admin/tenants/stats);
 *   TENANTS_FIXTURE removed Sprint 57.73 (table real GET /admin/tenants).
 *
 * Created: 2026-05-25 (Sprint 57.43 Day 2)
 *
 * Modification History (newest-first):
 *   - 2026-06-03: Sprint 57.74 — drop STATS_FIXTURE assertions (fixture removed; strip real-data) (A-6a)
 *   - 2026-06-03: Sprint 57.73 — drop TENANTS_FIXTURE assertions (fixture removed; table real-data) (A-6a)
 *   - 2026-05-25: Initial creation (Sprint 57.43 Day 2) — admin-tenants mockup-fidelity rebuild Vitest coverage
 *
 * Related:
 *   - frontend/src/features/admin-tenants/_fixtures.ts
 *   - sprint-57-74-plan.md
 */

import { describe, expect, it } from "vitest";

import { TABLE_SUBTITLE } from "@/features/admin-tenants/_fixtures";

describe("admin-tenants/_fixtures (Sprint 57.43 / 57.74)", () => {
  it("TABLE_SUBTITLE matches verbatim mockup string", () => {
    expect(TABLE_SUBTITLE).toBe("48 active · 3 anomalies in last 24h");
  });
});
