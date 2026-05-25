/**
 * File: frontend/tests/unit/pages/adminTenantsRoleGate.test.tsx
 * Purpose: Unit test — AdminTenantsPage renders the data view only for platform-admin roles.
 * Category: Frontend / tests / unit / pages
 * Scope: Phase 57 / Sprint 57.13 US-A2
 *
 * Created: 2026-05-10 (Sprint 57.13 Day 2)
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import AdminTenantsPage from "../../../src/pages/admin-tenants";
import { ThemeProvider } from "../../../src/components/ThemeProvider";
import { useAuthStore } from "../../../src/features/auth/store/authStore";

// Stub the data hook so the platform-admin branch doesn't try to fetch.
vi.mock("../../../src/features/admin-tenants/hooks/useAdminTenants", () => ({
  useAdminTenants: () => ({
    data: { items: [], total: 0, limit: 50, offset: 0 },
    error: null,
    isLoading: false,
    isFetching: false,
    refetch: vi.fn(),
  }),
}));

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <ThemeProvider>
          <AdminTenantsPage />
        </ThemeProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

function setAuthed(roles: string[]): void {
  useAuthStore.setState({
    status: "authenticated",
    user: { id: "u-1", email: "a@b.test", display_name: "A" },
    tenant: { id: "t-1", name: "Acme", code: "ACME" },
    roles,
  });
}

describe("AdminTenantsPage role gate", () => {
  beforeEach(() => {
    setAuthed(["user"]);
  });

  afterEach(() => {
    useAuthStore.setState({ status: "unknown", user: null, tenant: null, roles: [] });
  });

  it("non-platform-admin → shows the 'needs permission' notice, not the table", () => {
    setAuthed(["user", "approver"]);
    renderPage();
    expect(screen.getByText(/需要平台管理員權限/)).toBeInTheDocument();
  });

  it("platform_admin role → renders the tenant data view (no permission notice)", () => {
    setAuthed(["user", "platform_admin"]);
    renderPage();
    expect(screen.queryByText(/需要平台管理員權限/)).toBeNull();
    // Sprint 57.43 mockup-fidelity rebuild — AdminTenantsView renders the
    // verbatim TenantsPageHeader (route-pill `/admin/tenants` is unique to the
    // page header; "Tenants" plain text also appears in sidebar nav).
    expect(screen.getByText("/admin/tenants")).toBeInTheDocument();
    expect(screen.getByText(/All tenants/)).toBeInTheDocument();
  });

  it("admin role also counts as platform-admin", () => {
    setAuthed(["admin"]);
    renderPage();
    expect(screen.queryByText(/需要平台管理員權限/)).toBeNull();
  });
});
