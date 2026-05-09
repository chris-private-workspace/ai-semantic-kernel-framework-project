/**
 * File: frontend/src/features/governance/services/auditService.ts
 * Purpose: REST client for /api/v1/audit/{log,verify-chain} — auditor-RBAC + JWT tenant scoped.
 * Category: Frontend / governance / services
 * Scope: Phase 57 / Sprint 57.9 US-4 + US-5 Day 3
 *
 * Description:
 *   Wraps two backend audit endpoints (Sprint 53.5 US-5 + US-6):
 *
 *   - GET /api/v1/audit/log
 *       Paginated audit_log read scoped to the JWT tenant. Filters: operation,
 *       resource_type, user_id, from_ts_ms, to_ts_ms. Cursor pagination via
 *       offset + page_size; response carries has_more + next_offset.
 *
 *   - GET /api/v1/audit/verify-chain
 *       Walks the tenant's audit chain and recomputes hashes. Heavy operation;
 *       UI surfaces it via AuditChainBadge (US-5) — caller responsibility to
 *       avoid spamming.
 *
 *   Mirrors `governanceService.ts` style: fetchWithAuth (JWT injection per
 *   Sprint 57.7 IAM), URLSearchParams omit-undefined helper (mirror
 *   admin-tenants Sprint 57.4 buildListSearchParams pattern), JSON error
 *   surface.
 *
 *   Errors are surfaced as `Error` with HTTP status / detail; callers
 *   (useAuditLog hook + AuditChainBadge) display via TanStack Query `error`
 *   field. 403 forbidden is the auditor RBAC denial — UI must show a clear
 *   "auditor role required" message rather than the raw HTTP 403.
 *
 * Created: 2026-05-09 (Sprint 57.9 Day 3 US-4 + US-5)
 *
 * Modification History (newest-first):
 *   - 2026-05-09: Initial creation (Sprint 57.9 US-4 + US-5)
 *
 * Related:
 *   - backend/src/api/v1/audit.py (AuditLogPage / ChainVerifyResult DTOs)
 *   - ../types.ts (AuditLogPage / AuditLogFilter / ChainVerifyResult)
 *   - ../../auth/services/authService.ts (fetchWithAuth helper)
 *   - ./governanceService.ts (sibling service — mirror style)
 */

import { fetchWithAuth } from "../../auth/services/authService";
import type { AuditLogFilter, AuditLogPage, ChainVerifyResult } from "../types";

const API_BASE = "/api/v1/audit";

/**
 * Build URLSearchParams from filter, omitting undefined / empty-string keys.
 * Mirrors Sprint 57.4 admin-tenants buildListSearchParams pattern so a future
 * AD-Auditor-URLQuerySync (Phase 58+) can reuse identical helper logic.
 */
function _buildAuditLogSearchParams(filter: AuditLogFilter): URLSearchParams {
  const params = new URLSearchParams();
  if (filter.operation && filter.operation.trim() !== "") {
    params.set("operation", filter.operation.trim());
  }
  if (filter.resource_type && filter.resource_type.trim() !== "") {
    params.set("resource_type", filter.resource_type.trim());
  }
  if (filter.user_id && filter.user_id.trim() !== "") {
    params.set("user_id", filter.user_id.trim());
  }
  if (filter.from_ts_ms !== undefined) {
    params.set("from_ts_ms", String(filter.from_ts_ms));
  }
  if (filter.to_ts_ms !== undefined) {
    params.set("to_ts_ms", String(filter.to_ts_ms));
  }
  if (filter.offset !== undefined) {
    params.set("offset", String(filter.offset));
  }
  if (filter.page_size !== undefined) {
    params.set("page_size", String(filter.page_size));
  }
  return params;
}

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

export const auditService = {
  /** Paginated audit_log read scoped to the JWT tenant. */
  async fetchAuditLog(filter: AuditLogFilter, signal?: AbortSignal): Promise<AuditLogPage> {
    const params = _buildAuditLogSearchParams(filter);
    const qs = params.toString();
    const url = qs ? `${API_BASE}/log?${qs}` : `${API_BASE}/log`;
    const response = await fetchWithAuth(url, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
      signal,
    });
    return _handleResponse<AuditLogPage>(response);
  },

  /** Walk the tenant's audit chain and recompute hashes (heavy). */
  async verifyChain(signal?: AbortSignal): Promise<ChainVerifyResult> {
    const response = await fetchWithAuth(`${API_BASE}/verify-chain`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
      signal,
    });
    return _handleResponse<ChainVerifyResult>(response);
  },
};

// Exported for unit tests so the URLSearchParams omit-undefined contract has
// direct coverage without going through the full fetch round-trip.
export const _testing = { _buildAuditLogSearchParams };
