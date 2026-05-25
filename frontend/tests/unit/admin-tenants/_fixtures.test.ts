/**
 * File: frontend/tests/unit/admin-tenants/_fixtures.test.ts
 * Purpose: Vitest schema integrity coverage for admin-tenants fixtures (TENANTS / STATS / TABLE_SUBTITLE).
 * Category: Frontend / Tests / admin-tenants / unit
 * Scope: Phase 57 / Sprint 57.43 Day 2 (mockup-fidelity rebuild Vitest coverage)
 *
 * Description:
 *   Karpathy §2 minimal but useful — schema integrity locks:
 *   - TENANTS_FIXTURE has exactly 8 entries (mockup verbatim port)
 *   - STATS_FIXTURE has exactly 4 entries
 *   - TABLE_SUBTITLE matches verbatim mockup string
 *   - Every TENANTS_FIXTURE entry has all 9 required fields
 *   - Plan / status / deltaDir enums are within declared union types
 *
 * Created: 2026-05-25 (Sprint 57.43 Day 2)
 *
 * Modification History (newest-first):
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
  TENANTS_FIXTURE,
} from "@/features/admin-tenants/_fixtures";

describe("admin-tenants/_fixtures (Sprint 57.43)", () => {
  it("TENANTS_FIXTURE has exactly 8 entries", () => {
    expect(TENANTS_FIXTURE).toHaveLength(8);
  });

  it("STATS_FIXTURE has exactly 4 entries", () => {
    expect(STATS_FIXTURE).toHaveLength(4);
  });

  it("TABLE_SUBTITLE matches verbatim mockup string", () => {
    expect(TABLE_SUBTITLE).toBe("48 active · 3 anomalies in last 24h");
  });

  it("every TENANTS_FIXTURE entry has all 9 required fields", () => {
    const required = [
      "id",
      "name",
      "plan",
      "seats",
      "region",
      "agents",
      "runs24",
      "status",
      "created",
    ];
    for (const t of TENANTS_FIXTURE) {
      for (const field of required) {
        expect(t).toHaveProperty(field);
      }
    }
  });

  it("TENANTS_FIXTURE plan values are within union 'Starter' | 'Pro' | 'Enterprise'", () => {
    const validPlans = new Set(["Starter", "Pro", "Enterprise"]);
    for (const t of TENANTS_FIXTURE) {
      expect(validPlans.has(t.plan)).toBe(true);
    }
  });

  it("TENANTS_FIXTURE status values are within union 'active' | 'quota-warn' | 'anomaly'", () => {
    const validStatuses = new Set(["active", "quota-warn", "anomaly"]);
    for (const t of TENANTS_FIXTURE) {
      expect(validStatuses.has(t.status)).toBe(true);
    }
  });

  it("STATS_FIXTURE deltaDir values are within union 'up' | 'down'", () => {
    const validDirs = new Set(["up", "down"]);
    for (const s of STATS_FIXTURE) {
      expect(validDirs.has(s.deltaDir)).toBe(true);
    }
  });

  it("TENANTS_FIXTURE has 1 anomaly + 1 quota-warn + 6 active per mockup verbatim port", () => {
    const counts = TENANTS_FIXTURE.reduce<Record<string, number>>(
      (acc, t) => {
        acc[t.status] = (acc[t.status] ?? 0) + 1;
        return acc;
      },
      {},
    );
    expect(counts.active).toBe(6);
    expect(counts["quota-warn"]).toBe(1);
    expect(counts.anomaly).toBe(1);
  });
});
