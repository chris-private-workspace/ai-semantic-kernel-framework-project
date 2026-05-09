/**
 * File: frontend/src/features/cost-dashboard/services/costService.ts
 * Purpose: REST client for 56.3 admin cost-summary endpoint.
 * Category: Frontend / cost-dashboard / services
 * Scope: Phase 57 / Sprint 57.1 US-2 → Sprint 57.9 US-6 Day 4 (fetchWithAuth swap)
 *
 * Description:
 *   Wraps GET /api/v1/admin/tenants/{tenant_id}/cost-summary?month=YYYY-MM.
 *
 *   Sprint 57.9 US-6 Day 4: raw `fetch` swapped to `fetchWithAuth` so requests
 *   carry Sprint 57.7 IAM JWT (mirror chat-v2 D3 pattern from Sprint 57.8 +
 *   governanceService swap from Sprint 57.9 US-3). `credentials: "include"`
 *   is set by fetchWithAuth itself (no longer passed explicitly).
 *
 *   Errors are surfaced as `Error` with HTTP status / detail; useCostSummary
 *   hook (Sprint 57.9 US-6) forwards via TanStack Query `error` field.
 *
 * Created: 2026-05-06 (Sprint 57.1 Day 1)
 * Last Modified: 2026-05-09
 *
 * Modification History (newest-first):
 *   - 2026-05-09: Sprint 57.9 US-6 Day 4 — swap raw fetch to fetchWithAuth (JWT injection)
 *   - 2026-05-06: Initial creation (Sprint 57.1 Day 1 / US-2)
 *
 * Related:
 *   - backend/src/api/v1/admin/cost_summary.py (endpoint)
 *   - ../types.ts (CostSummaryResponse)
 *   - ../hooks/useCostSummary.ts (TanStack consumer)
 *   - ../../auth/services/authService.ts (fetchWithAuth helper)
 */

import { fetchWithAuth } from "../../auth/services/authService";
import type { CostSummaryResponse } from "../types";

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

export async function fetchCostSummary(
  tenantId: string,
  month: string,
  signal?: AbortSignal,
): Promise<CostSummaryResponse> {
  const response = await fetchWithAuth(
    `${API_BASE}/tenants/${tenantId}/cost-summary?month=${encodeURIComponent(month)}`,
    { method: "GET", signal },
  );
  return _handleResponse<CostSummaryResponse>(response);
}
