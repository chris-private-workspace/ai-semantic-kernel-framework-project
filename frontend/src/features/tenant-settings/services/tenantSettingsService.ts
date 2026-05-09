/**
 * File: frontend/src/features/tenant-settings/services/tenantSettingsService.ts
 * Purpose: REST client for 57.3 admin tenant GET + PATCH endpoints.
 * Category: Frontend / tenant-settings / services
 * Scope: Phase 57 / Sprint 57.3 US-3 → Sprint 57.9 US-6 Day 4 (fetchWithAuth swap)
 *
 * Description:
 *   Wraps GET + PATCH /api/v1/admin/tenants/{tenant_id}.
 *
 *   Sprint 57.9 US-6 Day 4: raw `fetch` swapped to `fetchWithAuth` (Sprint 57.7
 *   IAM JWT) + signal forwarded for TanStack auto-cancellation on the GET path.
 *
 * Created: 2026-05-07 (Sprint 57.3 Day 3)
 * Last Modified: 2026-05-09
 *
 * Modification History (newest-first):
 *   - 2026-05-09: Sprint 57.9 US-6 Day 4 — swap raw fetch to fetchWithAuth + signal param on GET
 *   - 2026-05-07: Initial creation (Sprint 57.3 Day 3)
 *
 * Related:
 *   - backend/src/api/v1/admin/tenants.py (GET + PATCH endpoints)
 *   - ../types.ts (TenantSettingsResponse + TenantUpdateRequest)
 *   - ../hooks/useTenantSettings.ts + useTenantSettingsSave.ts (TanStack consumers)
 */

import { fetchWithAuth } from "../../auth/services/authService";
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

export async function fetchTenantSettings(
  tenantId: string,
  signal?: AbortSignal,
): Promise<TenantSettingsResponse> {
  const response = await fetchWithAuth(`${API_BASE}/tenants/${tenantId}`, {
    method: "GET",
    signal,
  });
  return _handleResponse<TenantSettingsResponse>(response);
}

export async function updateTenantSettings(
  tenantId: string,
  payload: TenantUpdateRequest,
): Promise<TenantSettingsResponse> {
  const response = await fetchWithAuth(`${API_BASE}/tenants/${tenantId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return _handleResponse<TenantSettingsResponse>(response);
}
