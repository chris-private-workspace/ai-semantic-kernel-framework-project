/**
 * File: frontend/tests/unit/cost-dashboard/costStore.test.ts
 * Purpose: Unit test for costStore (UI-only post-Sprint 57.9 US-6 migration).
 * Category: Frontend / tests / unit / cost-dashboard
 * Scope: Phase 57 / Sprint 57.1 US-2 → Sprint 57.9 US-6 Day 4 (rewrite for UI-only API)
 *
 * Created: 2026-05-06 (Sprint 57.1 Day 1)
 * Last Modified: 2026-05-09
 *
 * Modification History:
 *   - 2026-05-09: Sprint 57.9 US-6 Day 4 — rewrite for UI-only store API (drop loadData)
 *   - 2026-05-06: Initial creation (Sprint 57.1 Day 1)
 */

import { beforeEach, describe, expect, it } from "vitest";

import { useCostStore } from "../../../src/features/cost-dashboard/store/costStore";

describe("costStore (UI-only post-57.9 US-6)", () => {
  beforeEach(() => {
    useCostStore.getState().reset();
  });

  it("setMonth updates currentMonth", () => {
    useCostStore.getState().setMonth("2026-04");
    expect(useCostStore.getState().currentMonth).toBe("2026-04");
  });

  it("reset returns currentMonth to default (current YYYY-MM)", () => {
    useCostStore.getState().setMonth("2024-01");
    useCostStore.getState().reset();
    const expected = new Date().toISOString().substring(0, 7);
    expect(useCostStore.getState().currentMonth).toBe(expected);
  });

  it("store API surface is UI-only (no data/loading/error/loadData)", () => {
    const state = useCostStore.getState();
    // These keys MUST be absent post-57.9 US-6 — server cache lives in TanStack
    // hook (useCostSummary) and not in Zustand. If these reappear, the
    // migration regressed.
    expect(state).not.toHaveProperty("data");
    expect(state).not.toHaveProperty("loading");
    expect(state).not.toHaveProperty("error");
    expect(state).not.toHaveProperty("loadData");
  });
});
