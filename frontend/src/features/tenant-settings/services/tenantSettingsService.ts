/**
 * File: frontend/src/features/tenant-settings/services/tenantSettingsService.ts
 * Purpose: REST client for /admin/tenants/{id} GET + PATCH + 5 sub-resource list endpoints.
 * Category: Frontend / tenant-settings / services
 * Scope: Phase 57 / Sprint 57.3 US-3 → Sprint 57.9 US-6 → Sprint 57.49 US-1 (5 sub-resources)
 *
 * Description:
 *   Wraps GET + PATCH /api/v1/admin/tenants/{tenant_id} (Sprint 57.3) plus 5
 *   sub-resource list endpoints shipped Sprint 57.47/48:
 *     - GET /{tenant_id}/members (Sprint 57.47 Track B)
 *     - GET /{tenant_id}/hitl-policies (Sprint 57.48 Track A)
 *     - GET /{tenant_id}/feature-flags (Sprint 57.48 Track B)
 *     - GET /{tenant_id}/quotas (Sprint 57.48 Track C)
 *     - GET /{tenant_id}/rate-limits (Sprint 57.48 Track D)
 *
 *   All use shared `fetchWithAuth` (Sprint 57.7 IAM JWT) + AbortSignal forwarding
 *   for TanStack auto-cancellation. Pagination params (limit/offset) optional;
 *   defaults to server-side limit=50 / offset=0.
 *
 * Created: 2026-05-07 (Sprint 57.3 Day 3)
 * Last Modified: 2026-05-26
 *
 * Modification History (newest-first):
 *   - 2026-06-13: Sprint 57.114 — +fetch/create/update/deleteTenantSkill (per-tenant skills tab)
 *   - 2026-06-12: Sprint 57.107 B3 — harness-policy mappers +handoff_enabled +handoff_target_allowlist
 *   - 2026-06-12: Sprint 57.106 C3 — +getHarnessPolicy/putHarnessPolicy (harness-policy tab)
 *   - 2026-06-11: Sprint 57.104 C1 — +getModelPolicy/putModelPolicy (model-policy tab)
 *   - 2026-05-29: Sprint 57.62 US-3 — +fetchRateLimitsAlerts GET recent alerts service func
 *   - 2026-05-28: Sprint 57.58 Track D — +fetchRateLimitsUsage GET live usage service func
 *   - 2026-05-27: Sprint 57.57 Track B — +saveRateLimits PUT service func
 *   - 2026-05-27: Sprint 57.56 Track B — +saveQuotaOverrides PUT service func
 *   - 2026-05-27: Sprint 57.55 Track B — +saveFeatureFlagOverrides PUT service func
 *   - 2026-05-26: Sprint 57.54 Track B — add saveHITLPolicies PUT (HITLPolicies edit mode)
 *   - 2026-05-26: Sprint 57.50 — add fetchTenantIdentity (Identity fixture cleanup)
 *   - 2026-05-26: Sprint 57.49 Day 1 — +5 sub-resource list service funcs
 *   - 2026-05-09: Sprint 57.9 US-6 Day 4 — swap raw fetch to fetchWithAuth + signal param on GET
 *   - 2026-05-07: Initial creation (Sprint 57.3 Day 3)
 *
 * Related:
 *   - backend/src/api/v1/admin/tenants.py (GET + PATCH + 5 sub-resource endpoints)
 *   - ../types.ts (response interfaces incl. Sprint 57.49 additions)
 *   - ../hooks/use*.ts (TanStack consumers)
 */

import { fetchWithAuth } from "../../auth/services/authService";
import type {
  FeatureFlagListResponse,
  FeatureFlagOverridesUpsertRequest,
  FeatureFlagOverridesUpsertResponse,
  HarnessPolicy,
  HarnessPolicyApiResponse,
  HarnessPolicyApiUpsertRequest,
  HITLPolicyListResponse,
  HITLPolicyUpsertRequest,
  HITLPolicyUpsertResponse,
  ModelPolicy,
  ModelPolicyApiResponse,
  ModelPolicyApiUpsertRequest,
  QuotaListResponse,
  QuotaOverridesUpsertRequest,
  QuotaOverridesUpsertResponse,
  RateLimitAlertsResponse,
  RateLimitListResponse,
  RateLimitsUpsertRequest,
  RateLimitsUpsertResponse,
  RateLimitsUsageResponse,
  Skill,
  SkillCreateRequest,
  SkillListResponse,
  SkillUpdateRequest,
  TenantIdentity,
  TenantMemberListResponse,
  TenantSettingsResponse,
  TenantUpdateRequest,
} from "../types";

const API_BASE = "/api/v1/admin";

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

export async function fetchTenantSettings(
  tenantId: string,
  signal?: AbortSignal,
): Promise<TenantSettingsResponse> {
  const response = await fetchWithAuth(`${API_BASE}/tenants/${tenantId}`, {
    method: "GET",
    signal,
  });
  return _handleResponse<TenantSettingsResponse>(response);
}

export async function updateTenantSettings(
  tenantId: string,
  payload: TenantUpdateRequest,
): Promise<TenantSettingsResponse> {
  const response = await fetchWithAuth(`${API_BASE}/tenants/${tenantId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return _handleResponse<TenantSettingsResponse>(response);
}

/* === Sprint 57.49 — 5 sub-resource list endpoints === */

function _buildPageParams(limit?: number, offset?: number): string {
  const params = new URLSearchParams();
  if (limit !== undefined) params.set("limit", String(limit));
  if (offset !== undefined) params.set("offset", String(offset));
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

export async function fetchTenantMembers(
  tenantId: string,
  limit?: number,
  offset?: number,
  signal?: AbortSignal,
): Promise<TenantMemberListResponse> {
  const response = await fetchWithAuth(
    `${API_BASE}/tenants/${tenantId}/members${_buildPageParams(limit, offset)}`,
    { method: "GET", signal },
  );
  return _handleResponse<TenantMemberListResponse>(response);
}

export async function fetchHITLPolicies(
  tenantId: string,
  limit?: number,
  offset?: number,
  signal?: AbortSignal,
): Promise<HITLPolicyListResponse> {
  const response = await fetchWithAuth(
    `${API_BASE}/tenants/${tenantId}/hitl-policies${_buildPageParams(limit, offset)}`,
    { method: "GET", signal },
  );
  return _handleResponse<HITLPolicyListResponse>(response);
}

export async function fetchFeatureFlags(
  tenantId: string,
  limit?: number,
  offset?: number,
  signal?: AbortSignal,
): Promise<FeatureFlagListResponse> {
  const response = await fetchWithAuth(
    `${API_BASE}/tenants/${tenantId}/feature-flags${_buildPageParams(limit, offset)}`,
    { method: "GET", signal },
  );
  return _handleResponse<FeatureFlagListResponse>(response);
}

export async function fetchQuotas(
  tenantId: string,
  limit?: number,
  offset?: number,
  signal?: AbortSignal,
): Promise<QuotaListResponse> {
  const response = await fetchWithAuth(
    `${API_BASE}/tenants/${tenantId}/quotas${_buildPageParams(limit, offset)}`,
    { method: "GET", signal },
  );
  return _handleResponse<QuotaListResponse>(response);
}

export async function fetchRateLimits(
  tenantId: string,
  limit?: number,
  offset?: number,
  signal?: AbortSignal,
): Promise<RateLimitListResponse> {
  const response = await fetchWithAuth(
    `${API_BASE}/tenants/${tenantId}/rate-limits${_buildPageParams(limit, offset)}`,
    { method: "GET", signal },
  );
  return _handleResponse<RateLimitListResponse>(response);
}

/* === Sprint 57.54 Track B — HITLPolicies upsert (PUT) === */

export async function saveHITLPolicies(
  tenantId: string,
  payload: HITLPolicyUpsertRequest,
  signal?: AbortSignal,
): Promise<HITLPolicyUpsertResponse> {
  const response = await fetchWithAuth(
    `${API_BASE}/tenants/${tenantId}/hitl-policies`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal,
    },
  );
  return _handleResponse<HITLPolicyUpsertResponse>(response);
}

/* === Sprint 57.55 Track B — FeatureFlag overrides upsert (PUT) === */

export async function saveFeatureFlagOverrides(
  tenantId: string,
  payload: FeatureFlagOverridesUpsertRequest,
  signal?: AbortSignal,
): Promise<FeatureFlagOverridesUpsertResponse> {
  const response = await fetchWithAuth(
    `${API_BASE}/tenants/${tenantId}/feature-flags`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal,
    },
  );
  return _handleResponse<FeatureFlagOverridesUpsertResponse>(response);
}

/* === Sprint 57.56 Track B — Quota overrides upsert (PUT) === */

export async function saveQuotaOverrides(
  tenantId: string,
  payload: QuotaOverridesUpsertRequest,
  signal?: AbortSignal,
): Promise<QuotaOverridesUpsertResponse> {
  const response = await fetchWithAuth(
    `${API_BASE}/tenants/${tenantId}/quotas`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal,
    },
  );
  return _handleResponse<QuotaOverridesUpsertResponse>(response);
}

/* === Sprint 57.57 Track B — RateLimits upsert (PUT) === */

export async function saveRateLimits(
  tenantId: string,
  payload: RateLimitsUpsertRequest,
  signal?: AbortSignal,
): Promise<RateLimitsUpsertResponse> {
  const response = await fetchWithAuth(
    `${API_BASE}/tenants/${tenantId}/rate-limits`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal,
    },
  );
  return _handleResponse<RateLimitsUpsertResponse>(response);
}

/* === Sprint 57.58 Track D — RateLimits live usage (GET) ===
 *
 * Read-only poll of the live Redis sliding-window counter for each configured
 * rate-limit resource. Polled every 5s by useRateLimitsUsage; MUST NOT consume
 * capacity (backend uses RateLimitCounter.peek). No pagination envelope —
 * response is {items: RateLimitsUsageItem[]} verbatim.
 */

export async function fetchRateLimitsUsage(
  tenantId: string,
  signal?: AbortSignal,
): Promise<RateLimitsUsageResponse> {
  const response = await fetchWithAuth(
    `${API_BASE}/tenants/${tenantId}/rate-limits/usage`,
    { method: "GET", signal },
  );
  return _handleResponse<RateLimitsUsageResponse>(response);
}

/* === Sprint 57.62 US-3 — RateLimits recent alerts (GET) ===
 *
 * Mirrors backend GET /{tenant_id}/rate-limits/alerts?limit=N (default 20,
 * 1..100). Returns recent 80%-threshold breach records newest-first. `limit`
 * omitted → backend default 20.
 */
export async function fetchRateLimitsAlerts(
  tenantId: string,
  limit?: number,
  signal?: AbortSignal,
): Promise<RateLimitAlertsResponse> {
  const query = limit !== undefined ? `?limit=${limit}` : "";
  const response = await fetchWithAuth(
    `${API_BASE}/tenants/${tenantId}/rate-limits/alerts${query}`,
    { method: "GET", signal },
  );
  return _handleResponse<RateLimitAlertsResponse>(response);
}

/* === Sprint 57.104 C1 — Model policy (GET + PUT) ===
 *
 * GET returns a sparse snake_case policy (unset fields null). PUT is
 * composite-replace: the body is the COMPLETE desired policy — an omitted/empty
 * field is cleared (reverts to system default). The service maps the FE
 * camelCase `ModelPolicy` to/from the snake_case API shape; on write, blank
 * fields are dropped from the body (so the backend clears them). Errors surface
 * via _handleResponse (422 `detail` string for unknown/unpriced model or unknown
 * field).
 */

function _modelPolicyFromApi(api: ModelPolicyApiResponse): ModelPolicy {
  return {
    actionDeployment: api.action_deployment,
    actionModel: api.action_model,
    cheapDeployment: api.cheap_deployment,
    cheapModel: api.cheap_model,
  };
}

function _modelPolicyToApi(policy: ModelPolicy): ModelPolicyApiUpsertRequest {
  // Composite-replace: only include non-blank fields; omitted fields are cleared
  // (revert to system default) by the backend.
  const body: ModelPolicyApiUpsertRequest = {};
  const action = policy.actionDeployment?.trim();
  const actionModel = policy.actionModel?.trim();
  const cheap = policy.cheapDeployment?.trim();
  const cheapModel = policy.cheapModel?.trim();
  if (action) body.action_deployment = action;
  if (actionModel) body.action_model = actionModel;
  if (cheap) body.cheap_deployment = cheap;
  if (cheapModel) body.cheap_model = cheapModel;
  return body;
}

export async function getModelPolicy(
  tenantId: string,
  signal?: AbortSignal,
): Promise<ModelPolicy> {
  const response = await fetchWithAuth(
    `${API_BASE}/tenants/${tenantId}/model-policy`,
    { method: "GET", signal },
  );
  const api = await _handleResponse<ModelPolicyApiResponse>(response);
  return _modelPolicyFromApi(api);
}

export async function putModelPolicy(
  tenantId: string,
  policy: ModelPolicy,
  signal?: AbortSignal,
): Promise<ModelPolicy> {
  const response = await fetchWithAuth(
    `${API_BASE}/tenants/${tenantId}/model-policy`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(_modelPolicyToApi(policy)),
      signal,
    },
  );
  const api = await _handleResponse<ModelPolicyApiResponse>(response);
  return _modelPolicyFromApi(api);
}

/* === Sprint 57.106 C3 — Harness policy (GET + PUT) ===
 *
 * GET returns a sparse snake_case policy (unset fields null). PUT is
 * composite-replace: the body is the COMPLETE desired policy — a null field is
 * cleared (reverts to system default). The service maps the FE camelCase
 * `HarnessPolicy` to/from the snake_case API shape. The UI keeps a sparse value
 * object (null = "System default"); on write, the FULL desired state is sent
 * (every field present; "System default" selections → null). Errors surface via
 * _handleResponse (422 `detail` string for unknown judge template, bad/oversize
 * regex, >20 patterns, or invalid verification_mode).
 */

function _harnessPolicyFromApi(api: HarnessPolicyApiResponse): HarnessPolicy {
  return {
    escalateInputPhrases: api.escalate_input_phrases,
    escalateBetweenTurnsPhrases: api.escalate_between_turns_phrases,
    escalateOutputPhrases: api.escalate_output_phrases,
    escalateTools: api.escalate_tools,
    verificationMode: api.verification_mode,
    verificationJudgeTemplate: api.verification_judge_template,
    verificationEscalateOnMax: api.verification_escalate_on_max,
    riskyActionEnabled: api.risky_action_enabled,
    riskyActionExtraPatterns: api.risky_action_extra_patterns,
    // Sprint 57.107 B3
    handoffEnabled: api.handoff_enabled,
    handoffTargetAllowlist: api.handoff_target_allowlist,
  };
}

function _harnessPolicyToApi(policy: HarnessPolicy): HarnessPolicyApiUpsertRequest {
  // Composite-replace: send the COMPLETE desired policy. Every field is present;
  // a null field is cleared server-side (reverts to system default).
  return {
    escalate_input_phrases: policy.escalateInputPhrases,
    escalate_between_turns_phrases: policy.escalateBetweenTurnsPhrases,
    escalate_output_phrases: policy.escalateOutputPhrases,
    escalate_tools: policy.escalateTools,
    verification_mode: policy.verificationMode,
    verification_judge_template: policy.verificationJudgeTemplate,
    verification_escalate_on_max: policy.verificationEscalateOnMax,
    risky_action_enabled: policy.riskyActionEnabled,
    risky_action_extra_patterns: policy.riskyActionExtraPatterns,
    // Sprint 57.107 B3
    handoff_enabled: policy.handoffEnabled,
    handoff_target_allowlist: policy.handoffTargetAllowlist,
  };
}

export async function getHarnessPolicy(
  tenantId: string,
  signal?: AbortSignal,
): Promise<HarnessPolicy> {
  const response = await fetchWithAuth(
    `${API_BASE}/tenants/${tenantId}/harness-policy`,
    { method: "GET", signal },
  );
  const api = await _handleResponse<HarnessPolicyApiResponse>(response);
  return _harnessPolicyFromApi(api);
}

export async function putHarnessPolicy(
  tenantId: string,
  policy: HarnessPolicy,
  signal?: AbortSignal,
): Promise<HarnessPolicy> {
  const response = await fetchWithAuth(
    `${API_BASE}/tenants/${tenantId}/harness-policy`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(_harnessPolicyToApi(policy)),
      signal,
    },
  );
  const api = await _handleResponse<HarnessPolicyApiResponse>(response);
  return _harnessPolicyFromApi(api);
}

/* === Sprint 57.114 — Per-tenant Skills catalog (CRUD) ===
 *
 * GET lists a tenant's custom skills ({skills: Skill[]} — no pagination envelope).
 * POST creates (201 → the new Skill); PUT is a sparse update (only the provided
 * fields change); DELETE → 204 (no body). Each mutation invalidates the resolver
 * TTL cache server-side, so the next chat request reflects the change. Errors
 * surface via _handleResponse (409 duplicate name / 404 missing skill or tenant /
 * 422 non-kebab name or unknown field).
 */

export async function fetchTenantSkills(
  tenantId: string,
  signal?: AbortSignal,
): Promise<SkillListResponse> {
  const response = await fetchWithAuth(`${API_BASE}/tenants/${tenantId}/skills`, {
    method: "GET",
    signal,
  });
  return _handleResponse<SkillListResponse>(response);
}

export async function createTenantSkill(
  tenantId: string,
  payload: SkillCreateRequest,
  signal?: AbortSignal,
): Promise<Skill> {
  const response = await fetchWithAuth(`${API_BASE}/tenants/${tenantId}/skills`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal,
  });
  return _handleResponse<Skill>(response);
}

export async function updateTenantSkill(
  tenantId: string,
  skillId: string,
  payload: SkillUpdateRequest,
  signal?: AbortSignal,
): Promise<Skill> {
  const response = await fetchWithAuth(
    `${API_BASE}/tenants/${tenantId}/skills/${skillId}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal,
    },
  );
  return _handleResponse<Skill>(response);
}

export async function deleteTenantSkill(
  tenantId: string,
  skillId: string,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetchWithAuth(
    `${API_BASE}/tenants/${tenantId}/skills/${skillId}`,
    { method: "DELETE", signal },
  );
  // 204 has no body; replicate _handleResponse's error-detail extraction for non-2xx.
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
}

/* === Sprint 57.50 — Identity single-record endpoint === */

export async function fetchTenantIdentity(
  tenantId: string,
  signal?: AbortSignal,
): Promise<TenantIdentity> {
  const response = await fetchWithAuth(`${API_BASE}/tenants/${tenantId}/identity`, {
    method: "GET",
    signal,
  });
  return _handleResponse<TenantIdentity>(response);
}
