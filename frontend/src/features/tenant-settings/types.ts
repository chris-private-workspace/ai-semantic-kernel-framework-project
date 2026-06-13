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
 *   - 2026-06-13: Sprint 57.114 — +Skill CRUD schemas (per-tenant skills catalog tab)
 *   - 2026-06-12: Sprint 57.107 B3 — HarnessPolicy +handoffEnabled +handoffTargetAllowlist (Cat 11 handoff governance)
 *   - 2026-06-12: Sprint 57.106 C3 — +HarnessPolicy read/write schemas (harness-policy tab)
 *   - 2026-06-11: Sprint 57.104 C1 — +ModelPolicy read/write schemas (model-policy tab)
 *   - 2026-05-29: Sprint 57.62 US-3 — +RateLimitAlert{Item,Response} alerts read schemas
 *   - 2026-05-28: Sprint 57.58 Track D — +RateLimitsUsage{Item,Response} live usage read schemas
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

/* === Sprint 57.58 Track D — RateLimits live usage read schemas ===
 *
 * Mirrors backend Pydantic RateLimitsUsageItem / RateLimitsUsageResponse at
 * backend/src/api/v1/admin/tenants.py (GET /{tenant_id}/rate-limits/usage).
 * Distinct from RateLimitItem ({label, value} display string): the usage view
 * is the LIVE Redis sliding-window counter parsed into numeric fields.
 *   - window:   window length in SECONDS (int)
 *   - reset_at: UNIX epoch SECONDS when the oldest entry ages out (0 = empty)
 */

export interface RateLimitsUsageItem {
  resource: string;
  window: number; // window length in seconds
  limit: number;
  current: number; // entries currently inside the window
  reset_at: number; // UNIX epoch seconds when oldest entry ages out (0 = empty)
}

export interface RateLimitsUsageResponse {
  items: RateLimitsUsageItem[];
}

/* === Sprint 57.62 US-3 — RateLimits alerts read schemas ===
 *
 * Mirrors backend Pydantic RateLimitAlertItem / RateLimitAlertsResponse at
 * backend/src/api/v1/admin/tenants.py (GET /{tenant_id}/rate-limits/alerts).
 * One persisted 80%-threshold usage alert per (resource, window, window_start),
 * peak-tracked; newest-first. Distinct from RateLimitsUsageItem (live counter):
 * this is the durable, deduplicated breach record.
 *   - threshold_pct: the crossing threshold that fired (currently 80)
 *   - actual_pct:    observed usage pct, per-window peak
 *   - severity:      "warning" (80-99%) | "critical" (>=100%, throttled)
 *   - window_start / triggered_at: ISO-8601 datetime strings
 */

export interface RateLimitAlertItem {
  resource: string;
  window: string; // window_type label (e.g. "min")
  threshold_pct: number; // crossing threshold (currently 80)
  actual_pct: number; // observed usage pct (per-window peak)
  used: number;
  quota: number;
  severity: string; // "warning" | "critical"
  window_start: string; // ISO-8601 datetime
  triggered_at: string; // ISO-8601 datetime
}

export interface RateLimitAlertsResponse {
  items: RateLimitAlertItem[];
}

/* === Sprint 57.104 C1 — Model policy read/write schemas ===
 *
 * Mirrors backend GET/PUT /admin/tenants/{id}/model-policy. The tenant's model
 * policy selects which deployment/model the agent loop's "action" (primary) and
 * "cheap" (e.g. verifier/judge) tiers use. The policy is SPARSE: any unset field
 * is null on read; on write, an omitted/empty field is CLEARED (reverts to the
 * system default). PUT is composite-replace: the body is the COMPLETE desired
 * policy. 422 (with `detail` string) when a model is unknown/unpriced or an
 * unknown field is sent (backend extra=forbid).
 *
 * FE convention: camelCase in the UI; the service maps to/from the snake_case
 * API shape (see tenantSettingsService.ts get/putModelPolicy).
 */

/** Camelcase UI shape — sparse (null = system default). */
export interface ModelPolicy {
  actionDeployment: string | null;
  actionModel: string | null;
  cheapDeployment: string | null;
  cheapModel: string | null;
}

/** Snake_case API read shape (GET response). */
export interface ModelPolicyApiResponse {
  action_deployment: string | null;
  action_model: string | null;
  cheap_deployment: string | null;
  cheap_model: string | null;
}

/** Snake_case API write shape (PUT body) — all optional (omitted = cleared). */
export interface ModelPolicyApiUpsertRequest {
  action_deployment?: string;
  action_model?: string;
  cheap_deployment?: string;
  cheap_model?: string;
}

/* === Sprint 57.106 C3 — Harness policy (GET + PUT) ===
 *
 * Mirrors backend GET/PUT /admin/tenants/{id}/harness-policy. The tenant's
 * harness policy governs the agent loop's guardrail-escalation phrase/tool sets
 * (input / between-turns / output / tools), the in-loop verification gate
 * (mode + judge template + escalate-on-max), and the risky-action detector
 * (enabled + extra regex patterns). The policy is SPARSE: any unset field is
 * null on read; on write, PUT is COMPOSITE-REPLACE — the body is the COMPLETE
 * desired policy, so an omitted/null field is CLEARED (reverts to the system
 * default). 422 (with `detail` string) when a judge-template name is unknown, a
 * regex is bad/oversize, a list exceeds 20 patterns, or verification_mode is
 * invalid (backend extra=forbid).
 *
 * FE convention: the value object is a single SPARSE shape shared by the UI and
 * (after case-mapping) the API. The service maps to/from the snake_case API
 * shape (see tenantSettingsService.ts get/putHarnessPolicy).
 */

/** Verification gate mode (null = system default). */
export type HarnessVerificationMode = "enabled" | "disabled";

/** The 5 shipped judge templates (null = system default). */
export type HarnessJudgeTemplate =
  | "factual_consistency"
  | "format_compliance"
  | "output_quality"
  | "pii_leak_check"
  | "safety_review";

/** Camelcase UI shape — sparse (null = system default for every field). */
export interface HarnessPolicy {
  escalateInputPhrases: string[] | null;
  escalateBetweenTurnsPhrases: string[] | null;
  escalateOutputPhrases: string[] | null;
  escalateTools: string[] | null;
  verificationMode: HarnessVerificationMode | null;
  verificationJudgeTemplate: HarnessJudgeTemplate | null;
  verificationEscalateOnMax: boolean | null;
  riskyActionEnabled: boolean | null;
  riskyActionExtraPatterns: string[] | null;
  // Sprint 57.107 B3: Cat 11 handoff governance.
  // handoffEnabled tri-state (null = system default ON); handoffTargetAllowlist
  // null = no restriction (any target). The backend rejects an empty list with a
  // 422 ("use handoff_enabled=false").
  handoffEnabled: boolean | null;
  handoffTargetAllowlist: string[] | null;
}

/** Snake_case API read shape (GET response) — sparse (null = system default). */
export interface HarnessPolicyApiResponse {
  escalate_input_phrases: string[] | null;
  escalate_between_turns_phrases: string[] | null;
  escalate_output_phrases: string[] | null;
  escalate_tools: string[] | null;
  verification_mode: HarnessVerificationMode | null;
  verification_judge_template: HarnessJudgeTemplate | null;
  verification_escalate_on_max: boolean | null;
  risky_action_enabled: boolean | null;
  risky_action_extra_patterns: string[] | null;
  // Sprint 57.107 B3
  handoff_enabled: boolean | null;
  handoff_target_allowlist: string[] | null;
}

/** Snake_case API write shape (PUT body) — composite-replace (null = cleared). */
export interface HarnessPolicyApiUpsertRequest {
  escalate_input_phrases?: string[] | null;
  escalate_between_turns_phrases?: string[] | null;
  escalate_output_phrases?: string[] | null;
  escalate_tools?: string[] | null;
  verification_mode?: HarnessVerificationMode | null;
  verification_judge_template?: HarnessJudgeTemplate | null;
  verification_escalate_on_max?: boolean | null;
  risky_action_enabled?: boolean | null;
  risky_action_extra_patterns?: string[] | null;
  // Sprint 57.107 B3
  handoff_enabled?: boolean | null;
  handoff_target_allowlist?: string[] | null;
}

/* === Sprint 57.114 — Per-tenant Skills catalog (CRUD) ===
 *
 * Mirrors backend GET/POST/PUT/DELETE /admin/tenants/{id}/skills at
 * backend/src/api/v1/admin/tenants.py. A tenant's custom skills overlay the
 * bundled set per chat request (a same-name tenant skill shadows a bundled one).
 * snake_case direct (mirrors TenantMemberItem / QuotaItem — a simple list
 * resource, not a sparse policy value-object, so no camelCase mapper).
 *   - name:         kebab-case slug (^[a-z0-9][a-z0-9-]*$), max 128
 *   - description:  one-line summary, max 512
 *   - instructions: the full skill body (read_skill returns it verbatim)
 * Create requires all 3; update is sparse (only provided fields change).
 */

export interface Skill {
  id: string;
  name: string;
  description: string;
  instructions: string;
  created_at: string; // ISO 8601 datetime
  updated_at: string;
}

export interface SkillListResponse {
  skills: Skill[];
}

export interface SkillCreateRequest {
  name: string;
  description: string;
  instructions: string;
}

export interface SkillUpdateRequest {
  name?: string;
  description?: string;
  instructions?: string;
}
