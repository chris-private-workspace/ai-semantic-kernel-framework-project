/**
 * File: frontend/tests/unit/sla-dashboard/slaStore.test.ts
 * Purpose: Unit test for slaStore (UI-only post-Sprint 57.9 US-6 migration).
 * Category: Frontend / tests / unit / sla-dashboard
 * Scope: Phase 57 / Sprint 57.1 US-3 → Sprint 57.9 US-6 Day 4 (rewrite for UI-only API)
 *
 * Created: 2026-05-06 (Sprint 57.1 Day 2)
 * Last Modified: 2026-05-09
 *
 * Modification History:
 *   - 2026-05-09: Sprint 57.9 US-6 Day 4 — rewrite for UI-only store API (drop loadData)
 *   - 2026-05-06: Initial creation (Sprint 57.1 Day 2)
 */

import { beforeEach, describe, expect, it } from "vitest";

import { useSLAStore } from "../../../src/features/sla-dashboard/store/slaStore";

describe("slaStore (UI-only post-57.9 US-6)", () => {
  beforeEach(() => {
    useSLAStore.getState().reset();
  });

  it("setMonth updates currentMonth", () => {
    useSLAStore.getState().setMonth("2026-05");
    expect(useSLAStore.getState().currentMonth).toBe("2026-05");
  });

  it("reset returns currentMonth to default (current YYYY-MM)", () => {
    useSLAStore.getState().setMonth("2024-01");
    useSLAStore.getState().reset();
    const expected = new Date().toISOString().substring(0, 7);
    expect(useSLAStore.getState().currentMonth).toBe(expected);
  });

  it("store API surface is UI-only (no data/loading/error/loadData)", () => {
    const state = useSLAStore.getState();
    expect(state).not.toHaveProperty("data");
    expect(state).not.toHaveProperty("loading");
    expect(state).not.toHaveProperty("error");
    expect(state).not.toHaveProperty("loadData");
  });
});
