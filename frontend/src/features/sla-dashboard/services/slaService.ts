/**
 * File: frontend/src/features/sla-dashboard/services/slaService.ts
 * Purpose: REST client for 56.3 admin sla-report endpoint.
 * Category: Frontend / sla-dashboard / services
 * Scope: Phase 57 / Sprint 57.1 US-3 → Sprint 57.9 US-6 Day 4 (fetchWithAuth swap)
 *
 * Description:
 *   Wraps GET /api/v1/admin/tenants/{tenant_id}/sla-report?month=YYYY-MM.
 *
 *   Sprint 57.9 US-6 Day 4: raw `fetch` swapped to `fetchWithAuth` (Sprint 57.7
 *   IAM JWT injection) and signal forwarded for TanStack auto-cancellation.
 *
 * Created: 2026-05-06 (Sprint 57.1 Day 2)
 * Last Modified: 2026-05-09
 *
 * Modification History (newest-first):
 *   - 2026-05-09: Sprint 57.9 US-6 Day 4 — swap raw fetch to fetchWithAuth (JWT injection) + signal param
 *   - 2026-05-06: Initial creation (Sprint 57.1 Day 2 / US-3)
 *
 * Related:
 *   - backend/src/api/v1/admin/sla_reports.py (endpoint)
 *   - ../types.ts (SLAReportResponse)
 *   - ../hooks/useSLAReport.ts (TanStack consumer)
 */

import { fetchWithAuth } from "../../auth/services/authService";
import type { SLAReportResponse } from "../types";

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

export async function fetchSLAReport(
  tenantId: string,
  month: string,
  signal?: AbortSignal,
): Promise<SLAReportResponse> {
  const response = await fetchWithAuth(
    `${API_BASE}/tenants/${tenantId}/sla-report?month=${encodeURIComponent(month)}`,
    { method: "GET", signal },
  );
  return _handleResponse<SLAReportResponse>(response);
}
