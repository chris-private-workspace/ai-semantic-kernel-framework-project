/**
 * File: frontend/tests/unit/admin-tenants/adminTenantsStore.test.ts
 * Purpose: Unit test for adminTenantsStore (UI-only post-Sprint 57.9 US-6 migration).
 * Category: Frontend / tests / unit / admin-tenants
 * Scope: Phase 57 / Sprint 57.4 US-2 → Sprint 57.9 US-6 Day 4 (rewrite for UI-only API)
 *
 * Created: 2026-05-07 (Sprint 57.4 Day 2)
 * Last Modified: 2026-05-09
 *
 * Modification History:
 *   - 2026-05-09: Sprint 57.9 US-6 Day 4 — rewrite for UI-only store API (drop loadData/items/total)
 *   - 2026-05-07: Initial creation (Sprint 57.4 Day 2)
 */

import { beforeEach, describe, expect, it } from "vitest";

import { useAdminTenantsStore } from "../../../src/features/admin-tenants/store/adminTenantsStore";
import { TenantState } from "../../../src/features/admin-tenants/types";

describe("adminTenantsStore (UI-only post-57.9 US-6)", () => {
  beforeEach(() => {
    useAdminTenantsStore.getState().reset();
  });

  it("setFilter resets offset to 0 even when offset was advanced", () => {
    useAdminTenantsStore.getState().setPagination({ offset: 50 });
    expect(useAdminTenantsStore.getState().query.offset).toBe(50);
    useAdminTenantsStore.getState().setFilter({ state: TenantState.ACTIVE });
    const state = useAdminTenantsStore.getState();
    expect(state.query.state).toBe(TenantState.ACTIVE);
    expect(state.query.offset).toBe(0);
  });

  it("setPagination updates limit/offset without touching filters", () => {
    useAdminTenantsStore.getState().setFilter({ state: TenantState.ACTIVE });
    useAdminTenantsStore.getState().setPagination({ offset: 100, limit: 25 });
    const { query } = useAdminTenantsStore.getState();
    expect(query.state).toBe(TenantState.ACTIVE);
    expect(query.offset).toBe(100);
    expect(query.limit).toBe(25);
  });

  it("reset returns query to default", () => {
    useAdminTenantsStore.getState().setFilter({ state: TenantState.SUSPENDED });
    useAdminTenantsStore.getState().setPagination({ offset: 100 });
    useAdminTenantsStore.getState().reset();
    const { query } = useAdminTenantsStore.getState();
    expect(query.state).toBeUndefined();
    expect(query.plan).toBeUndefined();
    expect(query.search).toBeUndefined();
    expect(query.offset).toBe(0);
    expect(query.limit).toBe(50);
  });

  it("store API surface is UI-only (no items/total/loading/error/loadData)", () => {
    const state = useAdminTenantsStore.getState();
    expect(state).not.toHaveProperty("items");
    expect(state).not.toHaveProperty("total");
    expect(state).not.toHaveProperty("loading");
    expect(state).not.toHaveProperty("error");
    expect(state).not.toHaveProperty("loadData");
  });
});
