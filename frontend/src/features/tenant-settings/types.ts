/**
 * File: frontend/src/features/tenant-settings/types.ts
 * Purpose: TypeScript interfaces mirroring backend Pydantic schemas for /admin/tenants/{id} family.
 * Category: Frontend / tenant-settings / types
 * Scope: Phase 57 / Sprint 57.3 US-3 → Sprint 57.46 SaaS settings → Sprint 57.49 sub-resources
 *
 * Description:
 *   Mirrors backend Pydantic schemas at backend/src/api/v1/admin/tenants.py.
 *   Sprint 57.49 Day 1 adds 5 sub-resource list response shapes:
 *     - TenantMemberItem / TenantMemberListResponse (Sprint 57.47)
 *     - HITLPolicyItem / HITLPolicyListResponse (Sprint 57.48 Track A)
 *     - FeatureFlagItem / FeatureFlagListResponse (Sprint 57.48 Track B)
 *     - QuotaItem / QuotaListResponse (Sprint 57.48 Track C)
 *     - RateLimitItem / RateLimitListResponse (Sprint 57.48 Track D)
 *
 *   TenantSettingsResponse extended Sprint 57.46 with 5 SaaS settings fields
 *   (region/locale/retention_days/sso_enabled/seats); TenantUpdateRequest
 *   extended with same patch-able fields.
 *
 * Created: 2026-05-07 (Sprint 57.3 Day 3)
 * Last Modified: 2026-05-26
 *
 * Modification History (newest-first):
 *   - 2026-05-27: Sprint 57.57 Track B — +RateLimitsUpsert{Request,Response} write schemas
 *   - 2026-05-27: Sprint 57.56 Track B — +QuotaOverridesUpsert{Request,Response} types
 *   - 2026-05-27: Sprint 57.55 Track B — +FeatureFlagOverridesUpsert{Request,Response} write schemas
 *   - 2026-05-26: Sprint 57.54 Track B — +HITLPolicyUpsert{Request,Response} write schemas
 *   - 2026-05-26: Sprint 57.50 Day 1 — +TenantIdentity (Identity fixture cleanup)
 *   - 2026-05-26: Sprint 57.49 Day 1 — +5 sub-resource list shapes (Members/HITL/FF/Quotas/RateLimits)
 *   - 2026-05-26: Sprint 57.46 — TenantSettingsResponse +5 SaaS settings fields
 *   - 2026-05-07: Initial creation (Sprint 57.3 Day 3 / US-3)
 *
 * Related:
 *   - backend/src/api/v1/admin/tenants.py (Pydantic source of truth)
 *   - ./services/tenantSettingsService.ts (consumer)
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
  // Sprint 57.46 — SaaS settings extension
  region: string;
  locale: string;
  retention_days: number;
  sso_enabled: boolean;
  seats: number;
  created_at: string; // ISO 8601 datetime
  updated_at: string;
}

export interface TenantUpdateRequest {
  display_name?: string;
  meta_data?: Record<string, unknown>;
  region?: string;
  locale?: string;
  retention_days?: number;
  sso_enabled?: boolean;
  seats?: number;
}

/* === Sprint 57.49 — 5 sub-resource list response shapes === */

export interface TenantMemberItem {
  id: string;
  email: string;
  display_name: string | null;
  status: string;
  created_at: string;
}

export interface TenantMemberListResponse {
  items: TenantMemberItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface HITLPolicyItem {
  risk: string; // "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
  policy: string; // "auto" | "ask_once" | "always_ask"
  sla_seconds: number | null;
  reviewers: string;
}

export interface HITLPolicyListResponse {
  items: HITLPolicyItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface FeatureFlagItem {
  name: string;
  value: boolean;
  default_enabled: boolean;
  overridden: boolean;
  description: string | null;
  updated_at: string;
}

export interface FeatureFlagListResponse {
  items: FeatureFlagItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface QuotaItem {
  resource: string;
  limit: number;
  unit: string;
  period: string;
  current_usage: number | null;
}

export interface QuotaListResponse {
  items: QuotaItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface RateLimitItem {
  label: string;
  value: string;
}

export interface RateLimitListResponse {
  items: RateLimitItem[];
  total: number;
  limit: number;
  offset: number;
}

/* === Sprint 57.50 — Identity single-record response === */

export interface TenantIdentity {
  provider: string;
  scim_enabled: boolean;
  allowed_domains: string[];
  mfa_required: boolean;
}

/* === Sprint 57.54 Track B — HITLPolicies upsert write schemas === */

export type RiskLevelName = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface HITLPolicyUpsertRequest {
  auto_approve_max_risk: RiskLevelName;
  require_approval_min_risk: RiskLevelName;
  reviewer_groups_by_risk: Record<string, string[]>;
  sla_seconds_by_risk: Record<string, number>;
}

export interface HITLPolicyUpsertResponse {
  saved_policy: HITLPolicyUpsertRequest;
  items: HITLPolicyItem[];
}

/* === Sprint 57.55 Track B — FeatureFlag overrides upsert write schemas === */

export interface FeatureFlagOverridesUpsertRequest {
  overrides: Record<string, boolean>;
}

export interface FeatureFlagOverridesUpsertResponse {
  saved_overrides: Record<string, boolean>;
  items: FeatureFlagItem[];
}

/* === Sprint 57.56 Track B — Quota overrides upsert write schemas === */

export interface QuotaOverridesUpsertRequest {
  overrides: Record<string, number>;
}

export interface QuotaOverridesUpsertResponse {
  saved_overrides: Record<string, number>;
  items: QuotaItem[];
}

/* === Sprint 57.57 Track B — RateLimits upsert write schemas === */

export interface RateLimitsUpsertRequest {
  items: RateLimitItem[];
}

export interface RateLimitsUpsertResponse {
  items: RateLimitItem[];
  total: number;
  limit: number;
  offset: number;
}
