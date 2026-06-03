/**
 * File: frontend/src/features/admin-tenants/types.ts
 * Purpose: TypeScript interfaces mirroring 57.4 backend TenantListItem + TenantListResponse.
 * Category: Frontend / admin-tenants / types
 * Scope: Phase 57 / Sprint 57.4 US-2
 *
 * Description:
 *   Mirrors backend Pydantic schemas at backend/src/api/v1/admin/tenants.py
 *   (Sprint 57.4 US-1 list endpoint; extended Sprint 57.47 to 12 fields).
 *   TenantState + TenantPlan enums are re-exported from ../tenant-settings/types
 *   to avoid duplicate definitions (per 17.md single-source spirit + AP-11 命名一致).
 *
 * Created: 2026-05-07 (Sprint 57.4 Day 2)
 * Last Modified: 2026-06-03
 *
 * Modification History (newest-first):
 *   - 2026-06-03: Sprint 57.73 — sync TenantListItem with backend 57.47 LIST 7→12 (region/locale/retention_days/sso_enabled/seats) for real-data table wiring
 *   - 2026-05-07: Initial creation (Sprint 57.4 Day 2)
 *
 * Related:
 *   - backend/src/api/v1/admin/tenants.py (TenantListItem + TenantListResponse)
 *   - ../tenant-settings/types (TenantState + TenantPlan source of truth)
 *   - ./services/adminTenantsService.ts (consumer)
 *   - ./store/adminTenantsStore.ts (consumer)
 */

import type { TenantPlan, TenantState } from "../tenant-settings/types";

export { TenantPlan, TenantState } from "../tenant-settings/types";

/**
 * Lightweight subset of Tenant ORM returned by GET /admin/tenants list.
 * Excludes JSONB progress + meta_data (clients fetch via GET /{id}).
 * SaaS settings fields (region/locale/retention_days/sso_enabled/seats) were
 * added to the list response in Sprint 57.47 (LIST 7→12).
 */
export interface TenantListItem {
  id: string;
  code: string;
  display_name: string;
  state: TenantState;
  plan: TenantPlan;
  region: string;
  locale: string;
  retention_days: number;
  sso_enabled: boolean;
  seats: number;
  created_at: string; // ISO 8601 datetime
  updated_at: string;
}

/**
 * Paginated list response wrapper.
 */
export interface TenantListResponse {
  items: TenantListItem[];
  total: number;
  limit: number;
  offset: number;
}

/**
 * Query params for GET /admin/tenants list endpoint.
 *
 * - state / plan: exact filter (undefined = no filter)
 * - search: ILIKE on code+display_name (max 128 chars; undefined = no search)
 * - limit: pagination size (default 50; range 1..200)
 * - offset: pagination start (default 0)
 */
export interface TenantListQuery {
  state?: TenantState;
  plan?: TenantPlan;
  search?: string;
  limit: number;
  offset: number;
}
