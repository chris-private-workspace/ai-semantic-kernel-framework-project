/**
 * File: frontend/src/features/tenant-settings/types.ts
 * Purpose: TypeScript interfaces mirroring 57.3 backend TenantResponse + TenantUpdateRequest.
 * Category: Frontend / tenant-settings / types
 * Scope: Phase 57 / Sprint 57.3 US-3
 *
 * Description:
 *   Mirrors backend Pydantic schemas at backend/src/api/v1/admin/tenants.py
 *   (Sprint 57.3 US-1 + US-2). TenantState + TenantPlan enums match identity.py
 *   ORM enum values exactly (Day 1 D10: state default is REQUESTED not PROVISIONING).
 *
 * Created: 2026-05-07 (Sprint 57.3 Day 3)
 * Last Modified: 2026-05-07
 *
 * Modification History:
 *   - 2026-05-07: Initial creation (Sprint 57.3 Day 3 / US-3 — Tenant Settings types)
 *
 * Related:
 *   - backend/src/api/v1/admin/tenants.py (TenantResponse + TenantUpdateRequest)
 *   - backend/src/infrastructure/db/models/identity.py (TenantState + TenantPlan)
 *   - ./services/tenantSettingsService.ts (consumer)
 *   - ./store/tenantSettingsStore.ts (consumer)
 */

export enum TenantState {
  REQUESTED = "requested",
  PROVISIONING = "provisioning",
  ACTIVE = "active",
  SUSPENDED = "suspended",
  ARCHIVED = "archived",
}

export enum TenantPlan {
  STANDARD = "standard",
  ENTERPRISE = "enterprise",
}

export interface TenantSettingsResponse {
  id: string;
  code: string;
  display_name: string;
  state: TenantState;
  plan: TenantPlan;
  provisioning_progress: Record<string, unknown>;
  onboarding_progress: Record<string, unknown>;
  meta_data: Record<string, unknown>;
  created_at: string; // ISO 8601 datetime
  updated_at: string;
}

export interface TenantUpdateRequest {
  display_name?: string;
  meta_data?: Record<string, unknown>;
}
