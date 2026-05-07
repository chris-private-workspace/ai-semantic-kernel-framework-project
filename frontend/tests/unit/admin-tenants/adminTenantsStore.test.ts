/**
 * File: frontend/tests/unit/admin-tenants/adminTenantsStore.test.ts
 * Purpose: Unit test for adminTenantsStore — loadData populates items + total + setFilter resets offset.
 * Category: Frontend / tests / unit / admin-tenants
 * Scope: Phase 57 / Sprint 57.4 US-2
 *
 * Created: 2026-05-07 (Sprint 57.4 Day 2)
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import * as svc from "../../../src/features/admin-tenants/services/adminTenantsService";
import { useAdminTenantsStore } from "../../../src/features/admin-tenants/store/adminTenantsStore";
import {
  TenantPlan,
  TenantState,
  type TenantListResponse,
} from "../../../src/features/admin-tenants/types";

const MOCK: TenantListResponse = {
  items: [
    {
      id: "00000000-0000-0000-0000-000000000001",
      code: "ACME",
      display_name: "Acme Corp",
      state: TenantState.ACTIVE,
      plan: TenantPlan.ENTERPRISE,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-05-07T00:00:00Z",
    },
  ],
  total: 1,
  limit: 50,
  offset: 0,
};

describe("adminTenantsStore", () => {
  beforeEach(() => {
    useAdminTenantsStore.getState().reset();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("loadData success populates items + total + clears loading", async () => {
    vi.spyOn(svc, "listTenants").mockResolvedValueOnce(MOCK);
    await useAdminTenantsStore.getState().loadData();
    const state = useAdminTenantsStore.getState();
    expect(state.loading).toBe(false);
    expect(state.error).toBeNull();
    expect(state.items).toHaveLength(1);
    expect(state.total).toBe(1);
  });

  it("setFilter resets offset to 0 even when offset was advanced", () => {
    useAdminTenantsStore.getState().setPagination({ offset: 50 });
    expect(useAdminTenantsStore.getState().query.offset).toBe(50);
    useAdminTenantsStore.getState().setFilter({ state: TenantState.ACTIVE });
    const state = useAdminTenantsStore.getState();
    expect(state.query.state).toBe(TenantState.ACTIVE);
    expect(state.query.offset).toBe(0);
  });

  it("loadData failure sets error + clears items", async () => {
    vi.spyOn(svc, "listTenants").mockRejectedValueOnce(new Error("HTTP 500"));
    await useAdminTenantsStore.getState().loadData();
    const state = useAdminTenantsStore.getState();
    expect(state.loading).toBe(false);
    expect(state.error).toBe("HTTP 500");
    expect(state.items).toEqual([]);
    expect(state.total).toBe(0);
  });
});
