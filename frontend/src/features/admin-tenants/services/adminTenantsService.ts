/**
 * File: frontend/src/features/admin-tenants/services/adminTenantsService.ts
 * Purpose: REST client for 57.4 admin tenant list endpoint.
 * Category: Frontend / admin-tenants / services
 * Scope: Phase 57 / Sprint 57.4 US-2 → Sprint 57.9 US-6 Day 4 (fetchWithAuth swap)
 *
 * Description:
 *   Wraps GET /api/v1/admin/tenants list endpoint. Builds URLSearchParams
 *   from TenantListQuery (only setting params that are non-undefined).
 *
 *   Sprint 57.9 US-6 Day 4: raw `fetch` swapped to `fetchWithAuth` (Sprint 57.7
 *   IAM JWT) + signal forwarded for TanStack auto-cancellation.
 *
 * Created: 2026-05-07 (Sprint 57.4 Day 2)
 * Last Modified: 2026-05-09
 *
 * Modification History (newest-first):
 *   - 2026-05-09: Sprint 57.9 US-6 Day 4 — swap raw fetch to fetchWithAuth + signal param
 *   - 2026-05-07: Initial creation (Sprint 57.4 Day 2)
 *
 * Related:
 *   - backend/src/api/v1/admin/tenants.py (GET "" list endpoint)
 *   - ../types.ts (TenantListQuery + TenantListResponse)
 *   - ../hooks/useAdminTenants.ts (TanStack consumer)
 */

import { fetchWithAuth } from "../../auth/services/authService";
import type { TenantListQuery, TenantListResponse } from "../types";

const API_BASE = "/api/v1/admin";

async function _handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      // ignore JSON parse failure; use status only
    }
    throw new Error(detail);
  }
  return (await response.json()) as T;
}

/**
 * Build a URLSearchParams instance from a TenantListQuery, omitting
 * undefined optional filters (state / plan / search).
 */
export function buildListSearchParams(query: TenantListQuery): URLSearchParams {
  const params = new URLSearchParams();
  if (query.state !== undefined) params.set("state", query.state);
  if (query.plan !== undefined) params.set("plan", query.plan);
  if (query.search !== undefined && query.search !== "") {
    params.set("search", query.search);
  }
  params.set("limit", String(query.limit));
  params.set("offset", String(query.offset));
  return params;
}

export async function listTenants(
  query: TenantListQuery,
  signal?: AbortSignal,
): Promise<TenantListResponse> {
  const params = buildListSearchParams(query);
  const response = await fetchWithAuth(`${API_BASE}/tenants?${params.toString()}`, {
    method: "GET",
    signal,
  });
  return _handleResponse<TenantListResponse>(response);
}
