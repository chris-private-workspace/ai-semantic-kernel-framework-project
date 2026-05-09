/**
 * File: frontend/tests/unit/admin-tenants/TenantListTable.test.tsx
 * Purpose: Unit test for TenantListTable — render rows + empty state (TanStack hook driven).
 * Category: Frontend / tests / unit / admin-tenants
 * Scope: Phase 57 / Sprint 57.4 US-3 → Sprint 57.9 US-6 Day 4 (TanStack hook source)
 *
 * Created: 2026-05-07 (Sprint 57.4 Day 3)
 * Last Modified: 2026-05-09
 *
 * Modification History:
 *   - 2026-05-09: Sprint 57.9 US-6 Day 4 — wrap with QueryClientProvider; items now sourced from useAdminTenants hook
 *   - 2026-05-07: Initial creation (Sprint 57.4 Day 3)
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { TenantListTable } from "../../../src/features/admin-tenants/components/TenantListTable";
import * as svc from "../../../src/features/admin-tenants/services/adminTenantsService";
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

function renderInWrappers(): void {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const Wrap = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  );
  render(
    <Wrap>
      <TenantListTable />
    </Wrap>,
  );
}

describe("TenantListTable (post-57.9 US-6 — TanStack-driven)", () => {
  beforeEach(() => {
    useAdminTenantsStore.getState().reset();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders rows with code + display_name + state/plan badges", async () => {
    vi.spyOn(svc, "listTenants").mockResolvedValue({
      items: SAMPLE,
      total: SAMPLE.length,
      limit: 50,
      offset: 0,
    });
    renderInWrappers();
    await waitFor(() => expect(screen.getByText("ACME")).toBeInTheDocument());
    expect(screen.getByText("OTHER")).toBeInTheDocument();
    expect(screen.getByText("Acme Corp")).toBeInTheDocument();
    expect(screen.getAllByText("active")).toHaveLength(1);
    expect(screen.getAllByText("requested")).toHaveLength(1);
    expect(screen.getAllByText("enterprise")).toHaveLength(2);
    expect(screen.getAllByText("View")).toHaveLength(2);
  });

  it("renders empty state with Reset Filters button when items=[]", async () => {
    vi.spyOn(svc, "listTenants").mockResolvedValue({
      items: [],
      total: 0,
      limit: 50,
      offset: 0,
    });
    renderInWrappers();
    await waitFor(() => expect(screen.getByText(/No tenants match/)).toBeInTheDocument());
    expect(screen.getByText("Reset Filters")).toBeInTheDocument();
  });
});
