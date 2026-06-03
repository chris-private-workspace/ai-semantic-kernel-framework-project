/**
 * File: frontend/tests/unit/admin-tenants/_fixtures.test.ts
 * Purpose: Vitest schema integrity coverage for admin-tenants stats fixture + table subtitle.
 * Category: Frontend / Tests / admin-tenants / unit
 * Scope: Phase 57 / Sprint 57.43 Day 2 → Sprint 57.73 (real-data wiring)
 *
 * Description:
 *   Karpathy §2 minimal but useful — schema integrity locks for what remains
 *   fixture-backed after Sprint 57.73 wired the tenants TABLE to real data:
 *   - STATS_FIXTURE has exactly 4 entries (no aggregate-stats endpoint)
 *   - TABLE_SUBTITLE matches verbatim mockup string
 *   - STATS_FIXTURE deltaDir within declared union
 *   TENANTS_FIXTURE removed Sprint 57.73 (table now real GET /admin/tenants).
 *
 * Created: 2026-05-25 (Sprint 57.43 Day 2)
 *
 * Modification History (newest-first):
 *   - 2026-06-03: Sprint 57.73 — drop TENANTS_FIXTURE assertions (fixture removed; table real-data) (A-6a)
 *   - 2026-05-25: Initial creation (Sprint 57.43 Day 2) — admin-tenants mockup-fidelity rebuild Vitest coverage
 *
 * Related:
 *   - frontend/src/features/admin-tenants/_fixtures.ts
 *   - sprint-57-43-plan.md §AC3
 */

import { describe, expect, it } from "vitest";

import {
  STATS_FIXTURE,
  TABLE_SUBTITLE,
} from "@/features/admin-tenants/_fixtures";

describe("admin-tenants/_fixtures (Sprint 57.43 / 57.73)", () => {
  it("STATS_FIXTURE has exactly 4 entries", () => {
    expect(STATS_FIXTURE).toHaveLength(4);
  });

  it("TABLE_SUBTITLE matches verbatim mockup string", () => {
    expect(TABLE_SUBTITLE).toBe("48 active · 3 anomalies in last 24h");
  });

  it("STATS_FIXTURE deltaDir values are within union 'up' | 'down'", () => {
    const validDirs = new Set(["up", "down"]);
    for (const s of STATS_FIXTURE) {
      expect(validDirs.has(s.deltaDir)).toBe(true);
    }
  });
});
