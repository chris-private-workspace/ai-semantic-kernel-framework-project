/**
 * File: frontend/src/features/governance/services/governanceService.ts
 * Purpose: REST client for HITL approval endpoints (list + decide).
 * Category: Frontend / governance / services
 * Scope: Phase 53 / Sprint 53.5 US-1 → Sprint 57.9 US-3 Day 2 (fetchWithAuth swap)
 *
 * Description:
 *   Wraps GET /api/v1/governance/approvals + POST /api/v1/governance/approvals/{id}/decide.
 *
 *   Sprint 57.9 US-3 Day 2: raw `fetch` swapped to `fetchWithAuth` so requests
 *   carry Sprint 57.7 IAM JWT (Authorization: Bearer <token>) when the user
 *   is authenticated (mirror chat-v2 D3 pattern from Sprint 57.8). Anonymous
 *   requests still work for backward compat while other pages lack auth gates
 *   (per AD-Frontend-AuthUX Phase 58.x). `credentials: "include"` is set by
 *   `fetchWithAuth` itself.
 *
 *   Errors are surfaced as `Error` with the HTTP status / detail; callers
 *   should display in their own UI (Sprint 57.9 hooks: useApprovals + useApprovalDecide
 *   forward errors via TanStack Query `error` field).
 *
 * Created: 2026-05-04 (Sprint 53.5 Day 3)
 * Last Modified: 2026-05-09
 *
 * Modification History (newest-first):
 *   - 2026-05-09: Sprint 57.9 US-3 Day 2 — swap raw fetch to fetchWithAuth (JWT injection)
 *   - 2026-05-04: Initial creation (Sprint 53.5 Day 3)
 *
 * Related:
 *   - backend/src/api/v1/governance/router.py
 *   - ../types.ts (ApprovalSummary / DecisionLabel)
 *   - ../../auth/services/authService.ts (fetchWithAuth helper)
 */

import { fetchWithAuth } from "../../auth/services/authService";
import type {
  ApprovalSummary,
  DecisionLabel,
  DecisionResponse,
  PendingListResponse,
} from "../types";

const API_BASE = "/api/v1/governance";

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

export const governanceService = {
  /** List pending approvals for the current JWT tenant. */
  async listPending(signal?: AbortSignal): Promise<ApprovalSummary[]> {
    const response = await fetchWithAuth(`${API_BASE}/approvals`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
      signal,
    });
    const body = await _handleResponse<PendingListResponse>(response);
    return body.items;
  },

  /** Apply a reviewer decision. */
  async decide(
    requestId: string,
    decision: DecisionLabel,
    reason?: string,
    signal?: AbortSignal,
  ): Promise<DecisionResponse> {
    const response = await fetchWithAuth(`${API_BASE}/approvals/${requestId}/decide`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decision, reason: reason ?? null }),
      signal,
    });
    return _handleResponse<DecisionResponse>(response);
  },
};
