/**
 * File: frontend/tests/unit/admin-tenants/TenantListTable.test.tsx
 * Purpose: Unit test for TenantListTable — render rows + empty state.
 * Category: Frontend / tests / unit / admin-tenants
 * Scope: Phase 57 / Sprint 57.4 US-3
 *
 * Created: 2026-05-07 (Sprint 57.4 Day 3)
 */

import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it } from "vitest";

import { TenantListTable } from "../../../src/features/admin-tenants/components/TenantListTable";
import { useAdminTenantsStore } from "../../../src/features/admin-tenants/store/adminTenantsStore";
import {
  TenantPlan,
  TenantState,
  type TenantListItem,
} from "../../../src/features/admin-tenants/types";

const SAMPLE: TenantListItem[] = [
  {
    id: "00000000-0000-0000-0000-000000000001",
    code: "ACME",
    display_name: "Acme Corp",
    state: TenantState.ACTIVE,
    plan: TenantPlan.ENTERPRISE,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-05-07T00:00:00Z",
  },
  {
    id: "00000000-0000-0000-0000-000000000002",
    code: "OTHER",
    display_name: "Other Co",
    state: TenantState.REQUESTED,
    plan: TenantPlan.ENTERPRISE,
    created_at: "2026-02-01T00:00:00Z",
    updated_at: "2026-05-01T00:00:00Z",
  },
];

describe("TenantListTable", () => {
  afterEach(() => {
    useAdminTenantsStore.getState().reset();
  });

  it("renders rows with code + display_name + state/plan badges", () => {
    useAdminTenantsStore.setState({ items: SAMPLE, total: SAMPLE.length, loading: false });
    render(
      <MemoryRouter>
        <TenantListTable />
      </MemoryRouter>,
    );
    expect(screen.getByText("ACME")).toBeInTheDocument();
    expect(screen.getByText("OTHER")).toBeInTheDocument();
    expect(screen.getByText("Acme Corp")).toBeInTheDocument();
    // Each badge text appears once per row.
    expect(screen.getAllByText("active")).toHaveLength(1);
    expect(screen.getAllByText("requested")).toHaveLength(1);
    expect(screen.getAllByText("enterprise")).toHaveLength(2);
    // View buttons one per row.
    expect(screen.getAllByText("View")).toHaveLength(2);
  });

  it("renders empty state with Reset Filters button when items=[]", () => {
    useAdminTenantsStore.setState({ items: [], total: 0, loading: false });
    render(
      <MemoryRouter>
        <TenantListTable />
      </MemoryRouter>,
    );
    expect(screen.getByText(/No tenants match/)).toBeInTheDocument();
    expect(screen.getByText("Reset Filters")).toBeInTheDocument();
  });
});
