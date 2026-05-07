/**
 * File: frontend/tests/unit/admin-tenants/TenantListFilters.test.tsx
 * Purpose: Unit test for TenantListFilters — Apply triggers setFilter+loadData.
 * Category: Frontend / tests / unit / admin-tenants
 * Scope: Phase 57 / Sprint 57.4 US-3
 *
 * Created: 2026-05-07 (Sprint 57.4 Day 3)
 */

import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { TenantListFilters } from "../../../src/features/admin-tenants/components/TenantListFilters";
import * as svc from "../../../src/features/admin-tenants/services/adminTenantsService";
import { useAdminTenantsStore } from "../../../src/features/admin-tenants/store/adminTenantsStore";
import { TenantState } from "../../../src/features/admin-tenants/types";

describe("TenantListFilters", () => {
  afterEach(() => {
    useAdminTenantsStore.getState().reset();
    vi.restoreAllMocks();
  });

  it("Apply with state=ACTIVE selected triggers setFilter + loadData", async () => {
    const listSpy = vi
      .spyOn(svc, "listTenants")
      .mockResolvedValue({ items: [], total: 0, limit: 50, offset: 0 });
    render(<TenantListFilters />);

    // First select is State dropdown.
    const stateSelect = screen.getAllByRole("combobox")[0];
    fireEvent.change(stateSelect, { target: { value: TenantState.ACTIVE } });

    fireEvent.click(screen.getByText("Apply"));

    await vi.waitFor(() => expect(listSpy).toHaveBeenCalled());
    expect(useAdminTenantsStore.getState().query.state).toBe(TenantState.ACTIVE);
  });
});
