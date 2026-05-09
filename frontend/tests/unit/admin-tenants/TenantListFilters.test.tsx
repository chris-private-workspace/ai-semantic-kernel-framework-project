/**
 * File: frontend/tests/unit/admin-tenants/TenantListFilters.test.tsx
 * Purpose: Unit test for TenantListFilters — Apply triggers setFilter (TanStack auto-refetches via key change).
 * Category: Frontend / tests / unit / admin-tenants
 * Scope: Phase 57 / Sprint 57.4 US-3 → Sprint 57.9 US-6 Day 4 (drop loadData spy)
 *
 * Created: 2026-05-07 (Sprint 57.4 Day 3)
 * Last Modified: 2026-05-09
 *
 * Modification History:
 *   - 2026-05-09: Sprint 57.9 US-6 Day 4 — drop listTenants spy (filter no longer calls service directly; TanStack auto-refetches)
 *   - 2026-05-07: Initial creation (Sprint 57.4 Day 3)
 */

import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { TenantListFilters } from "../../../src/features/admin-tenants/components/TenantListFilters";
import { useAdminTenantsStore } from "../../../src/features/admin-tenants/store/adminTenantsStore";
import { TenantState } from "../../../src/features/admin-tenants/types";

describe("TenantListFilters (post-57.9 US-6 — TanStack-driven)", () => {
  afterEach(() => {
    useAdminTenantsStore.getState().reset();
  });

  it("Apply with state=ACTIVE selected updates store query (no QueryClient needed — component reads store + UI events only)", () => {
    render(<TenantListFilters />);

    const stateSelect = screen.getAllByRole("combobox")[0];
    fireEvent.change(stateSelect, { target: { value: TenantState.ACTIVE } });

    fireEvent.click(screen.getByText("Apply"));

    // Post-57.9 US-6: TenantListFilters no longer calls listTenants directly;
    // the assertion is on store state, which the TanStack hook will read in
    // production wiring (queryKey includes store.query → auto-refetch).
    expect(useAdminTenantsStore.getState().query.state).toBe(TenantState.ACTIVE);
    expect(useAdminTenantsStore.getState().query.offset).toBe(0); // setFilter resets offset
  });
});
