/**
 * File: frontend/src/features/admin-tenants/hooks/useAdminTenantsStats.ts
 * Purpose: TanStack Query hook for the admin-tenants fleet stats aggregate (GET /admin/tenants/stats).
 * Category: Frontend / admin-tenants / hooks
 * Scope: Phase 57 / Sprint 57.74 (A-6a carryover — stats aggregate wiring)
 *
 * Description:
 *   Wraps `fetchStats` via TanStack `useQuery`. The query key is static
 *   (`["admin-tenants", "stats"]`) — fleet-wide aggregate has no per-query
 *   parameters, so a single cache entry serves both the stats strip (fleet
 *   counts) and the table (per-tenant map). React Query dedups the two
 *   consumers into one request.
 *
 * Created: 2026-06-03 (Sprint 57.74)
 *
 * Modification History (newest-first):
 *   - 2026-06-03: Initial creation (Sprint 57.74) — fleet stats aggregate hook
 *
 * Related:
 *   - ../services/adminTenantsService.ts (fetchStats)
 *   - ./useAdminTenants.ts (sibling list hook — mirrored shape)
 *   - backend/src/api/v1/admin/tenants.py (GET /stats — TenantsStatsResponse)
 */

import { useQuery } from "@tanstack/react-query";

import { fetchStats } from "../services/adminTenantsService";
import type { TenantsStatsResponse } from "../types";

export const ADMIN_TENANTS_STATS_QUERY_KEY = ["admin-tenants", "stats"] as const;

export function useAdminTenantsStats() {
  return useQuery<TenantsStatsResponse, Error>({
    queryKey: ADMIN_TENANTS_STATS_QUERY_KEY,
    queryFn: ({ signal }) => fetchStats(signal),
  });
}
