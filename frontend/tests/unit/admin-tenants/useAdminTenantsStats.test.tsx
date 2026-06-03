/**
 * File: frontend/tests/unit/admin-tenants/useAdminTenantsStats.test.tsx
 * Purpose: Vitest tests for useAdminTenantsStats TanStack Query hook (Sprint 57.74).
 * Category: Frontend / tests / unit / admin-tenants
 * Scope: Phase 57 / Sprint 57.74 (A-6a stats aggregate wiring)
 *
 * Created: 2026-06-03 (Sprint 57.74)
 *
 * Modification History (newest-first):
 *   - 2026-06-03: Initial creation (Sprint 57.74) — fleet stats aggregate hook coverage
 *
 * Related:
 *   - frontend/src/features/admin-tenants/hooks/useAdminTenantsStats.ts
 *   - frontend/src/features/admin-tenants/services/adminTenantsService.ts (fetchStats)
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, test, vi } from "vitest";

import * as svc from "@/features/admin-tenants/services/adminTenantsService";
import {
  ADMIN_TENANTS_STATS_QUERY_KEY,
  useAdminTenantsStats,
} from "@/features/admin-tenants/hooks/useAdminTenantsStats";
import type { TenantsStatsResponse } from "@/features/admin-tenants/types";

function makeWrapper() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
}

const MOCK: TenantsStatsResponse = {
  fleet: { active_tenants: 48, total_seats: 1284, agents_deployed: 612 },
  per_tenant: [
    { tenant_id: "00000000-0000-0000-0000-000000000001", agents: 5, runs24: 1234 },
    { tenant_id: "00000000-0000-0000-0000-000000000002", agents: 2, runs24: 0 },
  ],
  gapped: ["anomalies", "deltas"],
};

describe("useAdminTenantsStats (Sprint 57.74)", () => {
  test("ADMIN_TENANTS_STATS_QUERY_KEY is single-source ['admin-tenants', 'stats']", () => {
    expect(ADMIN_TENANTS_STATS_QUERY_KEY).toEqual(["admin-tenants", "stats"]);
  });

  test("returns fleet + per_tenant + gapped on success", async () => {
    const spy = vi.spyOn(svc, "fetchStats").mockResolvedValueOnce(MOCK);

    const { result } = renderHook(() => useAdminTenantsStats(), {
      wrapper: makeWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(spy).toHaveBeenCalledTimes(1);
    expect(result.current.data).toEqual(MOCK);
    expect(result.current.data?.fleet.agents_deployed).toBe(612);
    expect(result.current.data?.per_tenant).toHaveLength(2);
    expect(result.current.data?.gapped).toEqual(["anomalies", "deltas"]);
  });

  test("error state surfaces (HTTP 403 admin RBAC simulation)", async () => {
    vi.spyOn(svc, "fetchStats").mockRejectedValueOnce(
      new Error("HTTP 403: admin role required"),
    );

    const { result } = renderHook(() => useAdminTenantsStats(), {
      wrapper: makeWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toBe("HTTP 403: admin role required");
  });
});
