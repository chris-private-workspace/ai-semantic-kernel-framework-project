/**
 * File: frontend/tests/unit/admin-tenants/useAdminTenants.test.tsx
 * Purpose: Vitest tests for useAdminTenants TanStack Query hook (Sprint 57.9 US-6).
 * Category: Frontend / tests / unit / admin-tenants
 * Scope: Phase 57 / Sprint 57.9 US-6 Day 4
 *
 * Created: 2026-05-09 (Sprint 57.9 Day 4 US-6)
 *
 * Modification History:
 *   - 2026-05-09: Initial creation (Sprint 57.9 US-6)
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, test, vi } from "vitest";

import * as svc from "@/features/admin-tenants/services/adminTenantsService";
import {
  ADMIN_TENANTS_QUERY_KEY_BASE,
  useAdminTenants,
} from "@/features/admin-tenants/hooks/useAdminTenants";
import { useAdminTenantsStore } from "@/features/admin-tenants/store/adminTenantsStore";
import {
  TenantPlan,
  TenantState,
  type TenantListResponse,
} from "@/features/admin-tenants/types";

function makeWrapper() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
}

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

describe("useAdminTenants (Sprint 57.9 US-6)", () => {
  beforeEach(() => {
    useAdminTenantsStore.getState().reset();
  });

  test("ADMIN_TENANTS_QUERY_KEY_BASE is single-source ['admin-tenants', 'list']", () => {
    expect(ADMIN_TENANTS_QUERY_KEY_BASE).toEqual(["admin-tenants", "list"]);
  });

  test("initial fetch returns list response on success", async () => {
    const spy = vi.spyOn(svc, "listTenants").mockResolvedValueOnce(MOCK);

    const { result } = renderHook(() => useAdminTenants(), {
      wrapper: makeWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(spy).toHaveBeenCalledTimes(1);
    expect(result.current.data).toEqual(MOCK);
  });

  test("error state surfaces (HTTP 403 admin RBAC simulation)", async () => {
    vi.spyOn(svc, "listTenants").mockRejectedValueOnce(
      new Error("HTTP 403: admin role required"),
    );

    const { result } = renderHook(() => useAdminTenants(), {
      wrapper: makeWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toBe("HTTP 403: admin role required");
  });
});
