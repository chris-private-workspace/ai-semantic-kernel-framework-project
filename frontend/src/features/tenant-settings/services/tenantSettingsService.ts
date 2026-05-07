/**
 * File: frontend/src/features/tenant-settings/services/tenantSettingsService.ts
 * Purpose: REST client for 57.3 admin tenant GET + PATCH endpoints.
 * Category: Frontend / tenant-settings / services
 * Scope: Phase 57 / Sprint 57.3 US-3
 *
 * Description:
 *   Wraps GET + PATCH /api/v1/admin/tenants/{tenant_id}. Mirrors plain-fetch
 *   + _handleResponse<T> pattern from 53.5 governanceService.ts + 57.1 v2
 *   costService.ts. Auth: backend enforces require_admin_platform_role;
 *   frontend lets 401/403 surface as Error and UI shows error message.
 *
 * Created: 2026-05-07 (Sprint 57.3 Day 3)
 * Last Modified: 2026-05-07
 *
 * Modification History:
 *   - 2026-05-07: Initial creation (Sprint 57.3 Day 3 / US-3 — Tenant Settings service)
 *
 * Related:
 *   - backend/src/api/v1/admin/tenants.py (GET + PATCH endpoints)
 *   - ../types.ts (TenantSettingsResponse + TenantUpdateRequest)
 *   - frontend/src/features/cost-dashboard/services/costService.ts (pattern reference)
 */

import type { TenantSettingsResponse, TenantUpdateRequest } from "../types";

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

export async function fetchTenantSettings(tenantId: string): Promise<TenantSettingsResponse> {
  const response = await fetch(
    `${API_BASE}/tenants/${tenantId}`,
    { credentials: "include" },
  );
  return _handleResponse<TenantSettingsResponse>(response);
}

export async function updateTenantSettings(
  tenantId: string,
  payload: TenantUpdateRequest,
): Promise<TenantSettingsResponse> {
  const response = await fetch(
    `${API_BASE}/tenants/${tenantId}`,
    {
      method: "PATCH",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
  );
  return _handleResponse<TenantSettingsResponse>(response);
}
