/**
 * File: frontend/src/features/admin-tenants/hooks/useAdminTenants.ts
 * Purpose: TanStack Query hook for admin tenants list (consumed by AdminTenantsPage children).
 * Category: Frontend / admin-tenants / hooks
 * Scope: Phase 57 / Sprint 57.9 US-6 Day 4
 *
 * Description:
 *   Reads `query` from `useAdminTenantsStore` (UI-only post-migration), wraps
 *   `listTenants` service via TanStack `useQuery`. Auto-refetches whenever
 *   `query` (filter + pagination) changes via stable JSON serialization in
 *   the queryKey (TanStack identity check).
 *
 *   `placeholderData: keepPreviousData` keeps prior items visible while next
 *   page / filtered set loads (smooth UX without flashing empty table).
 *
 * Created: 2026-05-09 (Sprint 57.9 Day 4 US-6)
 *
 * Modification History (newest-first):
 *   - 2026-05-09: Initial creation (Sprint 57.9 US-6)
 *
 * Related:
 *   - ../services/adminTenantsService.ts (listTenants)
 *   - ../store/adminTenantsStore.ts (UI-only query state post-migration)
 */

import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { listTenants } from "../services/adminTenantsService";
import { useAdminTenantsStore } from "../store/adminTenantsStore";
import type { TenantListResponse } from "../types";

export const ADMIN_TENANTS_QUERY_KEY_BASE = ["admin-tenants", "list"] as const;

export function useAdminTenants() {
  const query = useAdminTenantsStore((s) => s.query);
  return useQuery<TenantListResponse, Error>({
    queryKey: [...ADMIN_TENANTS_QUERY_KEY_BASE, query],
    queryFn: ({ signal }) => listTenants(query, signal),
    placeholderData: keepPreviousData,
  });
}
