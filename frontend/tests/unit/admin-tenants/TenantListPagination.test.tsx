/**
 * File: frontend/tests/unit/admin-tenants/TenantListPagination.test.tsx
 * Purpose: Unit test for TenantListPagination — Next click advances offset + triggers loadData.
 * Category: Frontend / tests / unit / admin-tenants
 * Scope: Phase 57 / Sprint 57.4 US-4
 *
 * Created: 2026-05-07 (Sprint 57.4 Day 3)
 */

import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { TenantListPagination } from "../../../src/features/admin-tenants/components/TenantListPagination";
import * as svc from "../../../src/features/admin-tenants/services/adminTenantsService";
import { useAdminTenantsStore } from "../../../src/features/admin-tenants/store/adminTenantsStore";

describe("TenantListPagination", () => {
  afterEach(() => {
    useAdminTenantsStore.getState().reset();
    vi.restoreAllMocks();
  });

  it("Next click advances offset by limit and triggers loadData", async () => {
    const listSpy = vi
      .spyOn(svc, "listTenants")
      .mockResolvedValue({ items: [], total: 100, limit: 50, offset: 50 });
    useAdminTenantsStore.setState({
      query: { limit: 50, offset: 0, state: undefined, plan: undefined, search: undefined },
      total: 100,
    });

    render(<TenantListPagination />);
    fireEvent.click(screen.getByText("Next →"));

    await vi.waitFor(() => expect(listSpy).toHaveBeenCalled());
    expect(useAdminTenantsStore.getState().query.offset).toBe(50);
  });

  it("Prev disabled at offset=0 + Next disabled when offset+limit >= total", () => {
    useAdminTenantsStore.setState({
      query: { limit: 50, offset: 0, state: undefined, plan: undefined, search: undefined },
      total: 30,
    });
    render(<TenantListPagination />);
    expect(screen.getByText("← Prev")).toBeDisabled();
    expect(screen.getByText("Next →")).toBeDisabled();
    expect(screen.getByText(/1-30 of 30/)).toBeInTheDocument();
  });
});
