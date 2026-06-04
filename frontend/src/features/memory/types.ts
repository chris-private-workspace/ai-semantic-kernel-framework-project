/**
 * File: frontend/src/features/memory/types.ts
 * Purpose: TypeScript types mirroring backend /api/v1/memory Pydantic DTOs (Sprint 57.12 US-3).
 * Category: Frontend / memory / types
 * Scope: Phase 57 / Sprint 57.12 Day 2 / US-3
 *
 * Description:
 *   Single-source TS contract for the memory feature folder consumed by:
 *     - services/memoryService.ts (REST DTOs)
 *     - hooks/useMemoryRecent.ts + useMemoryByScope.ts + useMemoryByTime.ts (TanStack Query)
 *     - components/MemoryRecentList.tsx + MemoryByScopeBrowser.tsx (US-5)
 *     - components/MemoryScopeBadge.tsx (5-layer badge)
 *
 *   Backend authority:
 *     - MemoryEntryItem  ↔ backend Pydantic MemoryEntryItem (api/v1/memory.py)
 *     - MemoryEntryPage  ↔ MemoryEntryPage (memory.py)
 *     - MemoryLayer / MemoryTimeScale enums ↔ backend Enum (memory.py)
 *
 *   Per Sprint 57.12 Day 1 D1-008: 5-layer ORM tables have non-uniform
 *   schemas, so MemoryEntryItem is a discriminated shape with nullable
 *   layer-specific fields. Frontend renders fields conditionally on `layer`.
 *   Phase 57.12 ships tenant + user + system fully; role + session → 501.
 *
 * Created: 2026-05-10 (Sprint 57.12 Day 2 / US-3)
 *
 * Modification History (newest-first):
 *   - 2026-06-04: Sprint 57.77 — add MemoryOpItem / MemoryOpsResponse (GET /ops ops-history)
 *   - 2026-06-03: Sprint 57.73 Track C — add MemoryMatrixCell / MemoryMatrixResponse (GET /matrix aggregate)
 *   - 2026-05-10: Initial creation (Sprint 57.12 Day 2 / US-3)
 *
 * Related:
 *   - backend/src/api/v1/memory.py (Pydantic DTOs)
 *   - sprint-57-12-plan.md §US-3
 */

export type MemoryLayer = "system" | "tenant" | "role" | "user" | "session";

export type MemoryTimeScale = "permanent" | "quarterly" | "daily";

export interface MemoryEntryItem {
  id: string;
  layer: MemoryLayer;
  /** tenant_id / role_id / user_id / session_id depending on layer; null for system. */
  scope_id: string | null;
  /** key string; null for layers without a key column (e.g. user). */
  key: string | null;
  /** entry content; for session layer this is the summary. */
  content: string;
  category: string | null;
  /** Unix epoch ms; only memory_user has expires_at. */
  expires_at_ms: number | null;
  /** Unix epoch ms. */
  created_at_ms: number;
  /** Unix epoch ms; role + session don't have updated_at. */
  updated_at_ms: number | null;
  /** Only tenant + user layers (via TenantScopedMixin). */
  tenant_id: string | null;
}

export interface MemoryEntryPage {
  items: MemoryEntryItem[];
  total: number;
  has_more: boolean;
  next_offset: number | null;
  page_size: number;
}

/** Filter for the /recent endpoint. layer is mandatory (single layer per request). */
export interface MemoryRecentFilter {
  layer: MemoryLayer;
  limit: number;
  offset: number;
}

/**
 * Single (layer × time_scale) count cell of the 5×3 Memory matrix.
 * Backend emits one cell per non-empty pair (zero-count cells omitted).
 * Mirrors backend MemoryMatrixCell (api/v1/memory.py).
 */
export interface MemoryMatrixCell {
  layer: MemoryLayer;
  time_scale: MemoryTimeScale;
  count: number;
}

/**
 * Aggregate response for GET /api/v1/memory/matrix.
 * - cells: non-empty (layer, time_scale) cells; absent pairs default to 0 in UI.
 * - total: sum of emitted cell counts.
 * - gapped_layers: layers with no backend query path (role + session) — rendered
 *   as a gap indicator, NEVER a fabricated number.
 * Mirrors backend MemoryMatrixResponse (api/v1/memory.py).
 */
export interface MemoryMatrixResponse {
  cells: MemoryMatrixCell[];
  total: number;
  gapped_layers: MemoryLayer[];
}

/**
 * Single memory_ops row from GET /api/v1/memory/ops (Sprint 57.76 backend).
 * Mirrors backend MemoryOpItem (api/v1/memory.py:153-166) verbatim.
 * - op: "WRITE" | "EVICT" (the only emitted operations; READ/EXPIRE not recorded).
 * - scope: "user" | "tenant" (role/session layers are not recorded — see plan §9).
 * - key/time_scale/value_snapshot/actor: null when the layer/op left them unset.
 * - created_at_ms: Unix epoch ms (also the pagination cursor unit).
 */
export interface MemoryOpItem {
  op: string;
  scope: string;
  key: string | null;
  time_scale: string | null;
  value_snapshot: string | null;
  actor: string | null;
  created_at_ms: number;
}

/**
 * Cursor-paginated response for GET /api/v1/memory/ops.
 * - ops: rows ordered created_at DESC (newest first).
 * - next_cursor: created_at_ms of the last row when the page is full; null when
 *   no more rows. Pass it back as `before` to fetch the next (older) page.
 * Mirrors backend MemoryOpsResponse (api/v1/memory.py:169-171).
 */
export interface MemoryOpsResponse {
  ops: MemoryOpItem[];
  next_cursor: number | null;
}
