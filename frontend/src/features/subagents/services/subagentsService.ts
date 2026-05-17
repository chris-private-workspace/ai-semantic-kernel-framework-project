/**
 * File: frontend/src/features/subagents/services/subagentsService.ts
 * Purpose: REST client for Cat 11 GET /api/v1/subagents (Sprint 57.19 US-B4).
 * Category: Frontend / subagents / services
 * Scope: Phase 57 / Sprint 57.19 Day 4 / US-C3
 *
 * Created: 2026-05-17 (Sprint 57.19 Day 4 / US-C3)
 *
 * Modification History (newest-first):
 *   - 2026-05-17: Initial creation (Sprint 57.19 Day 4 / US-C3)
 *
 * Related:
 *   - backend/src/api/v1/subagents.py
 *   - ../types.ts (SubagentsPage)
 *   - ../../auth/services/authService.ts (fetchWithAuth)
 */

import { fetchWithAuth } from "../../auth/services/authService";
import type { SubagentMode, SubagentsPage } from "../types";

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

export interface FetchSubagentsParams {
  mode?: SubagentMode;
  cursor?: string | null;
  limit?: number;
}

export async function fetchSubagents(
  params: FetchSubagentsParams = {},
  signal?: AbortSignal,
): Promise<SubagentsPage> {
  const q = new URLSearchParams();
  if (params.mode) q.set("mode", params.mode);
  if (params.cursor) q.set("cursor", params.cursor);
  if (params.limit) q.set("limit", String(params.limit));
  const qs = q.toString();
  const response = await fetchWithAuth(
    `${API_BASE}/subagents${qs ? `?${qs}` : ""}`,
    { method: "GET", signal },
  );
  return _handleResponse<SubagentsPage>(response);
}
