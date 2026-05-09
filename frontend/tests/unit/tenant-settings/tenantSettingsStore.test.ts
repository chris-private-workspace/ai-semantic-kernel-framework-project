/**
 * File: frontend/tests/unit/tenant-settings/tenantSettingsStore.test.ts
 * Purpose: Unit test for tenantSettingsStore (UI-only post-Sprint 57.9 US-6 migration).
 * Category: Frontend / tests / unit / tenant-settings
 * Scope: Phase 57 / Sprint 57.3 US-3 → Sprint 57.9 US-6 Day 4 (rewrite for UI-only API)
 *
 * Created: 2026-05-07 (Sprint 57.3 Day 3)
 * Last Modified: 2026-05-09
 *
 * Modification History:
 *   - 2026-05-09: Sprint 57.9 US-6 Day 4 — rewrite for UI-only store API (drop loadData/save)
 *   - 2026-05-07: Initial creation (Sprint 57.3 Day 3)
 */

import { beforeEach, describe, expect, it } from "vitest";

import { useTenantSettingsStore } from "../../../src/features/tenant-settings/store/tenantSettingsStore";

describe("tenantSettingsStore (UI-only post-57.9 US-6)", () => {
  beforeEach(() => {
    useTenantSettingsStore.getState().reset();
  });

  it("setTenantId updates tenantId field", () => {
    useTenantSettingsStore.getState().setTenantId("tenant-uuid");
    expect(useTenantSettingsStore.getState().tenantId).toBe("tenant-uuid");
  });

  it("reset clears tenantId back to null", () => {
    useTenantSettingsStore.getState().setTenantId("tenant-uuid");
    useTenantSettingsStore.getState().reset();
    expect(useTenantSettingsStore.getState().tenantId).toBeNull();
  });

  it("store API surface is UI-only (no data/loading/error/save/saving/saveError/loadData)", () => {
    const state = useTenantSettingsStore.getState();
    expect(state).not.toHaveProperty("data");
    expect(state).not.toHaveProperty("loading");
    expect(state).not.toHaveProperty("error");
    expect(state).not.toHaveProperty("save");
    expect(state).not.toHaveProperty("saving");
    expect(state).not.toHaveProperty("saveError");
    expect(state).not.toHaveProperty("loadData");
  });
});
