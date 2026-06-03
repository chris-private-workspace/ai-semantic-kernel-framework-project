/**
 * File: frontend/src/features/memory/services/memoryService.ts
 * Purpose: REST client for /api/v1/memory/{recent,scope,by-time} — auditor-RBAC + JWT tenant scoped.
 * Category: Frontend / memory / services
 * Scope: Phase 57 / Sprint 57.12 Day 2 / US-3
 *
 * Description:
 *   Wraps three backend memory endpoints (Sprint 57.12 US-2):
 *
 *   - GET /api/v1/memory/recent?layer=X&limit=&offset=
 *       Paginated recent entries within a single layer. tenant + user + system
 *       supported; role + session return 501.
 *
 *   - GET /api/v1/memory/scope/{layer}/{scope_id}?limit=&offset=
 *       Entries scoped to a specific scope_id. tenant scope_id mismatch → 404.
 *
 *   - GET /api/v1/memory/by-time/{layer}/{time_scale}?limit=&offset=
 *       Time-scale filter on expires_at. Only layer=user supported (others 400).
 *
 *   Mirrors verificationService.ts (Sprint 57.11) style: fetchWithAuth from
 *   authService.ts (D-PRE-3 — NOT separate fetchWithAuth.ts), JSON error
 *   surface (Error with detail).
 *
 *   403 = auditor RBAC denial; 501 = layer not yet wired (Phase 58+);
 *   400 = invalid layer/time_scale combination — UI surfaces detail message.
 *
 * Created: 2026-05-10 (Sprint 57.12 Day 2 / US-3)
 *
 * Modification History (newest-first):
 *   - 2026-06-03: Sprint 57.73 Track C — add fetchMatrix (GET /matrix layer×time_scale count aggregate)
 *   - 2026-05-10: Initial creation (Sprint 57.12 Day 2 / US-3)
 *
 * Related:
 *   - backend/src/api/v1/memory.py (Pydantic DTOs)
 *   - ../types.ts (MemoryEntryPage / MemoryRecentFilter / MemoryLayer / MemoryTimeScale / MemoryMatrixResponse)
 *   - ../../auth/services/authService.ts (fetchWithAuth helper)
 *   - ../../verification/services/verificationService.ts (sibling pattern reference)
 */

import { fetchWithAuth } from "../../auth/services/authService";
import type {
  MemoryEntryPage,
  MemoryLayer,
  MemoryMatrixResponse,
  MemoryRecentFilter,
  MemoryTimeScale,
} from "../types";

const API_BASE = "/api/v1/memory";

function _buildPageParams(limit: number, offset: number): URLSearchParams {
  const params = new URLSearchParams();
  params.set("limit", String(limit));
  params.set("offset", String(offset));
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

export const memoryService = {
  /** Paginated recent entries from a single layer. */
  async fetchRecent(filter: MemoryRecentFilter, signal?: AbortSignal): Promise<MemoryEntryPage> {
    const params = _buildPageParams(filter.limit, filter.offset);
    params.set("layer", filter.layer);
    const url = `${API_BASE}/recent?${params.toString()}`;
    const response = await fetchWithAuth(url, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
      signal,
    });
    return _handleResponse<MemoryEntryPage>(response);
  },

  /** Entries scoped to a specific scope_id within a layer. */
  async fetchByScope(
    layer: MemoryLayer,
    scopeId: string,
    limit: number,
    offset: number,
    signal?: AbortSignal,
  ): Promise<MemoryEntryPage> {
    const params = _buildPageParams(limit, offset);
    const url = `${API_BASE}/scope/${layer}/${encodeURIComponent(scopeId)}?${params.toString()}`;
    const response = await fetchWithAuth(url, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
      signal,
    });
    return _handleResponse<MemoryEntryPage>(response);
  },

  /** Time-scale filter on expires_at (layer=user only). */
  async fetchByTime(
    layer: MemoryLayer,
    timeScale: MemoryTimeScale,
    limit: number,
    offset: number,
    signal?: AbortSignal,
  ): Promise<MemoryEntryPage> {
    const params = _buildPageParams(limit, offset);
    const url = `${API_BASE}/by-time/${layer}/${timeScale}?${params.toString()}`;
    const response = await fetchWithAuth(url, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
      signal,
    });
    return _handleResponse<MemoryEntryPage>(response);
  },

  /** Aggregate (layer × time_scale) counts for the 5×3 matrix widget. */
  async fetchMatrix(signal?: AbortSignal): Promise<MemoryMatrixResponse> {
    const url = `${API_BASE}/matrix`;
    const response = await fetchWithAuth(url, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
      signal,
    });
    return _handleResponse<MemoryMatrixResponse>(response);
  },
};

// Exported for unit tests so the URLSearchParams build contract has direct
// coverage without going through the full fetch round-trip.
export const _testing = { _buildPageParams };
