/**
 * File: frontend/src/features/subagents/services/subagentsService.ts
 * Purpose: REST client for Cat 11 GET /api/v1/subagents (agent_catalog registry).
 * Category: Frontend / subagents / services
 * Scope: Phase 57 / Sprint 57.78 (re-point STUB → agent_catalog registry)
 *
 * Created: 2026-05-17 (Sprint 57.19 Day 4 / US-C3)
 *
 * Modification History (newest-first):
 *   - 2026-06-04: Sprint 57.78 — fetchSubagents → SubagentsResponse registry; drop mode/cursor/limit params (AD-Subagent-RealList)
 *   - 2026-05-17: Initial creation (Sprint 57.19 Day 4 / US-C3)
 *
 * Related:
 *   - backend/src/api/v1/subagents.py
 *   - ../types.ts (SubagentsResponse)
 *   - ../../auth/services/authService.ts (fetchWithAuth)
 */

import { fetchWithAuth } from "../../auth/services/authService";
import type { SubagentsResponse } from "../types";

const API_BASE = "/api/v1";

async function _handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      // ignore
    }
    throw new Error(detail);
  }
  return (await response.json()) as T;
}

export async function fetchSubagents(signal?: AbortSignal): Promise<SubagentsResponse> {
  const response = await fetchWithAuth(`${API_BASE}/subagents`, {
    method: "GET",
    signal,
  });
  return _handleResponse<SubagentsResponse>(response);
}
