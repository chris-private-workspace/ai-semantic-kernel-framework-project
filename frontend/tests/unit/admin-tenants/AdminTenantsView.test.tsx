/**
 * File: frontend/tests/unit/admin-tenants/AdminTenantsView.test.tsx
 * Purpose: Vitest coverage for AdminTenantsView — integration data-flow across 3 subcomponents.
 * Category: Frontend / Tests / admin-tenants / unit
 * Scope: Phase 57 / Sprint 57.43 Day 2 → Sprint 57.73 (real-data wiring)
 *
 * Description:
 *   - Mounts TenantsPageHeader (title "Tenants" present)
 *   - Mounts TenantsStatsStrip ("Active tenants" / "Total seats" labels + AP-2 banner)
 *   - Mounts TenantsTable ("All tenants" Card title + REAL tenant rows from the
 *     mocked useAdminTenants hook — Sprint 57.73 wired the table to live data)
 *   - Row click → TenantMembersDrawer drill-down (Sprint 57.49)
 *   useAdminTenants is mocked so the view can render without a real fetch; the
 *   view is wrapped in QueryClientProvider because it now mounts a TanStack hook.
 *
 * Created: 2026-05-25 (Sprint 57.43 Day 2)
 *
 * Modification History (newest-first):
 *   - 2026-06-03: Sprint 57.73 — wrap in QueryClientProvider + mock useAdminTenants + assert real rows (A-6a)
 *   - 2026-05-26: Sprint 57.49 — add row click → drawer integration tests + mock useTenantMembers
 *   - 2026-05-25: Initial creation (Sprint 57.43 Day 2) — admin-tenants mockup-fidelity rebuild Vitest coverage
 *
 * Related:
 *   - frontend/src/features/admin-tenants/components/AdminTenantsView.tsx
 *   - sprint-57-73-plan.md
 */

import "@testing-library/jest-dom/vitest";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";

import {
  TenantPlan,
  TenantState,
  type TenantListResponse,
} from "@/features/admin-tenants/types";

// Sprint 57.49 — AdminTenantsView mounts TenantMembersDrawer which uses useTenantMembers
vi.mock("@/features/tenant-settings/hooks/useTenantMembers", () => ({
  useTenantMembers: vi.fn().mockReturnValue({
    data: { items: [], total: 0, limit: 50, offset: 0 },
    isLoading: false,
    error: null,
  }),
  TENANT_MEMBERS_QUERY_KEY_BASE: ["tenant-settings", "members"],
}));

// Sprint 57.73 — AdminTenantsView mounts useAdminTenants; return controlled real data.
const MOCK_RESPONSE: TenantListResponse = {
  items: [
    {
      id: "00000000-0000-0000-0000-000000000001",
      code: "ACME",
      display_name: "Acme Corp",
      state: TenantState.ACTIVE,
      plan: TenantPlan.ENTERPRISE,
      created_at: "2026-01-15T08:30:00Z",
      updated_at: "2026-05-07T00:00:00Z",
    },
    {
      id: "00000000-0000-0000-0000-000000000002",
      code: "GLOBEX",
      display_name: "Globex EU",
      state: TenantState.SUSPENDED,
      plan: TenantPlan.STANDARD,
      created_at: "2025-09-12T12:00:00Z",
      updated_at: "2026-05-07T00:00:00Z",
    },
  ],
  total: 2,
  limit: 50,
  offset: 0,
};

vi.mock("@/features/admin-tenants/hooks/useAdminTenants", () => ({
  useAdminTenants: () => ({
    data: MOCK_RESPONSE,
    isLoading: false,
    isError: false,
    refetch: vi.fn(),
  }),
  ADMIN_TENANTS_QUERY_KEY_BASE: ["admin-tenants", "list"],
}));

import { AdminTenantsView } from "@/features/admin-tenants/components/AdminTenantsView";

function renderView() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <AdminTenantsView />
    </QueryClientProvider>,
  );
}

describe("AdminTenantsView (Sprint 57.43 / 57.73)", () => {
  it("renders TenantsPageHeader with title 'Tenants'", () => {
    renderView();
    const matches = screen.getAllByText("Tenants");
    expect(matches.length).toBeGreaterThanOrEqual(1);
  });

  it("renders TenantsPageHeader sub line + route-pill", () => {
    renderView();
    expect(
      screen.getByText(
        /Multi-tenant lifecycle · RLS-isolated · feature flags \+ quotas per tenant/i,
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("/admin/tenants")).toBeInTheDocument();
  });

  it("renders TenantsStatsStrip with all 4 KPI labels", () => {
    renderView();
    expect(screen.getByText("Active tenants")).toBeInTheDocument();
    expect(screen.getByText("Total seats")).toBeInTheDocument();
    expect(screen.getByText("Agents deployed")).toBeInTheDocument();
    expect(screen.getByText("Anomalies")).toBeInTheDocument();
  });

  it("renders TenantsTable with Card title 'All tenants'", () => {
    renderView();
    expect(screen.getByText("All tenants")).toBeInTheDocument();
  });

  it("renders real tenant rows from useAdminTenants (mapped name + code)", () => {
    renderView();
    expect(screen.getByText("Acme Corp")).toBeInTheDocument();
    expect(screen.getByText("ACME")).toBeInTheDocument();
    expect(screen.getByText("Globex EU")).toBeInTheDocument();
    expect(screen.getByText("GLOBEX")).toBeInTheDocument();
  });

  it("renders 2 AP-2 BackendGapBanners (stats strip + table gaps)", () => {
    renderView();
    const banners = screen.getAllByTestId("backend-gap-banner");
    expect(banners.length).toBe(2);
  });

  it("Sprint 57.49: drawer is closed by default (no dialog visible)", () => {
    renderView();
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(screen.queryByTestId("tenant-members-drawer")).toBeNull();
  });

  it("Sprint 57.49: clicking a tenant row opens TenantMembersDrawer", async () => {
    const user = userEvent.setup();
    renderView();
    const row = screen.getByTestId("tenant-row-ACME");
    await user.click(row);
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByTestId("tenant-members-drawer")).toBeInTheDocument();
  });

  it("Sprint 57.49: Close button hides drawer (selectedTenantId → null)", async () => {
    const user = userEvent.setup();
    renderView();
    const row = screen.getByTestId("tenant-row-ACME");
    await user.click(row);
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /close/i }));
    expect(screen.queryByRole("dialog")).toBeNull();
  });
});
