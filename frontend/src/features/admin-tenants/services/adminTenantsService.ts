/**
 * File: frontend/src/features/admin-tenants/services/adminTenantsService.ts
 * Purpose: REST client for 57.4 admin tenant list endpoint.
 * Category: Frontend / admin-tenants / services
 * Scope: Phase 57 / Sprint 57.4 US-2
 *
 * Description:
 *   Wraps GET /api/v1/admin/tenants list endpoint. Builds URLSearchParams
 *   from TenantListQuery (only setting params that are non-undefined).
 *   Mirrors plain-fetch + _handleResponse<T> pattern from 57.3
 *   tenantSettingsService.ts.
 *
 * Created: 2026-05-07 (Sprint 57.4 Day 2)
 *
 * Related:
 *   - backend/src/api/v1/admin/tenants.py (GET "" list endpoint)
 *   - ../types.ts (TenantListQuery + TenantListResponse)
 *   - ../../tenant-settings/services/tenantSettingsService.ts (pattern reference)
 */

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
): Promise<TenantListResponse> {
  const params = buildListSearchParams(query);
  const response = await fetch(
    `${API_BASE}/tenants?${params.toString()}`,
    { credentials: "include" },
  );
  return _handleResponse<TenantListResponse>(response);
}
