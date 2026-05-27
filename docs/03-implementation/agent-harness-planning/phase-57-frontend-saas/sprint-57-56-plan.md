# Sprint 57.56 — Quotas Admin Write Endpoint + Frontend Edit Mode (Phase 58.x WRITE side 3/4)

**Phase**: 57+ Frontend SaaS / Phase 58.x portfolio (Quotas WRITE-side ship; backend admin upsert + frontend edit mode)
**Goal**: Ship the Phase 58.x WRITE side for Quotas — close the existing BackendGapBanner copy ("Live usage tracking (current_usage): backend extension Phase 58+ — limits shown are tenant-effective from PlanQuota") by adding `PUT /admin/tenants/{tenant_id}/quotas` overrides upsert endpoint + `tenants.meta_data["quota_overrides"]` JSONB write + Pydantic write schema + frontend QuotasTab edit mode (Usage quotas Card ONLY — RateLimits Card unchanged per Sprint 57.57 scope) + `useQuotasSave` mutation hook. This is the **1st validation data point** for tier-4 sub-class `mechanical-greenfield-design-decisions` 0.65 (NEW Sprint 57.55 retro Q4 ACTIVATION; closes Sprint 57.55 carryover `AD-AgentFactor-Tier-4-Validation-Sprint-57.56`; single NEW component-pair = 1 endpoint + 1 mutation hook + 1 tab edit mode following Sprint 57.54+57.55 template).
**Branch**: `feature/sprint-57-56-quotas-write-endpoint`
**Class**: `medium-backend` 0.80 (8-data-point baseline post Sprint 57.55: 55.5=1.14 + 55.6=0.92 + 57.47=0.16 + 57.48=0.11 + 57.50=0.27 + 57.53=0.83 + 57.54≈1.0 + 57.55=0.79; 8-pt mean 0.65; last-3 mean 0.87 IN band lower-middle; KEEP per Sprint 57.55 retro Q4 — class baseline calibrates human-pace, agent residual captured at tier-4 sub-class layer)
**Sub-class** (agent_factor): `mechanical-greenfield-design-decisions` 0.65 (**tier-4 1st validation** under NEW table effective Sprint 57.56+ per Sprint 57.55 retro Q4 tier-4 SPLIT ACTIVATION; closes Sprint 57.55 carryover `AD-AgentFactor-Tier-4-Validation-Sprint-57.56`)
**Agent-delegated**: **yes — backend + frontend via code-implementer agent delegation** (≥ 80% of Day 1 work; required to generate 1st validation data point under `mechanical-greenfield-design-decisions` 0.65)
**Date**: 2026-05-27 (Sprint 57.55 closeout same-day continuation; main `2514197a` post PR #205 merge; Sprint 57.56 branch from main HEAD)
**Prior sprint reference**: Sprint 57.55 (closeout 2026-05-27; PR #205 merged main `2514197a`) generated `mechanical-greenfield` 0.50 tier-3 2nd validation data point with ratio ~1.57 ABOVE band by 0.37 → 2 consec > 1.20 ROLLBACK RULE MET → **tier-4 SPLIT ACTIVATED**: `mechanical-greenfield-port-style` 0.45 RESERVED + `mechanical-greenfield-design-decisions` 0.65 NEW. Sprint 57.54+57.55 retroactive mapping = `-design-decisions` (equivalent ratios under 0.65 = 1.05-1.55 / 1.21 = top band edge / IN band). Sprint 57.56 = **1st validation under tier-4 `-design-decisions` 0.65** → if lands IN band [0.85, 1.20] → tier-4 SPLIT validated cleanly; if > 1.20 → 1st > 1.20 data point single-data-point caution KEEP; if < 0.7 → 1st < 0.7 data point single-data-point caution KEEP; rollback rule "2 sprints > 1.20 → lift 0.65 → 0.80" pending Sprint 57.57+ 2nd data point.

---

## 1. Sprint Goal

```
AS the project maintainer of the Phase 58.x SaaS portfolio (HITLPolicies
   shipped Sprint 57.54 / FeatureFlags shipped Sprint 57.55 / Quotas /
   RateLimits / Identity persistence ADs) AND the V2 calibration matrix
   maintainer with `mechanical-greenfield-design-decisions` 0.65 tier-4
   sub-class table NEW from Sprint 57.55 retro Q4 ACTIVATION but ZERO
   validation data points so far (needs 1st data point for tier-4 SPLIT
   sanity check + rollback rule baseline)
I WANT the Quotas WRITE-side gap closed (PUT overrides upsert endpoint +
   tenants.meta_data["quota_overrides"] JSONB write + Pydantic write
   schema with numeric resource-keyed map + frontend QuotasTab Usage
   quotas Card edit mode + useQuotasSave mutation hook + service func) —
   selected from Phase 58.x portfolio per user direction 2026-05-27
   Option B "ship one WRITE-side AD per sprint" continuation — executed
   via code-implementer agent delegation (backend track + frontend track
   sequential) such that the sprint generates the FIRST validation data
   point for `mechanical-greenfield-design-decisions` 0.65 tier-4 baseline
SO THAT (a) Sprint 57.55 carryover `AD-AgentFactor-Tier-4-Validation-
   Sprint-57.56` is closed with a clean 1st validation data point under
   agent-delegated mode; (b) Sprint 57.56 retro Q4 either confirms tier-4
   SPLIT cleanly validated (IN band [0.85, 1.20]) OR generates 1st
   above/below-band data point for Sprint 57.57+ 2nd validation rollback
   rule baseline; (c) the existing BackendGapBanner copy in QuotasTab
   ("Live usage tracking (current_usage): backend extension Phase 58+")
   is softened to admit only deeper Phase 58+ gaps remain (live usage
   tracking via Redis counter exposure); (d) Sprint 57.48 frontend tab
   (read-only) is extended into full read+write parity matching the
   Sprint 57.54+57.55 edit-mode pattern for tenant-settings admin UX
   consistency; (e) `medium-backend` 0.80 class gets its 9th data point
   continuing post-confound-resolution tracking (per Sprint 57.55 retro
   Q4 discipline); (f) `medium-frontend` 0.65 class gets its 6th data
   point (Sprint 57.13=0.95-1.0 / 57.49=0.064 / 57.54≈0.32 / 57.55=0.53
   / Sprint 57.56 = TBD); confound resolved at tier-4 sub-class layer
   per Sprint 57.55 discipline; (g) Phase 58.x portfolio progresses from
   2/4 (HITLPolicies + FeatureFlags shipped) to 3/4 (Quotas WRITE side
   closed; RateLimits remains Sprint 57.57 candidate)
```

## 2. Background & Context

### 2.1 Quotas baseline state (verified Sprint 57.56 Day 0 Prong 2 content verify — D-DAY0-A 🔴 RED resolved via user Option B + 4 🆕 NOTABLE)

**Sprint 57.56 Day 0 critical correction (D-DAY0-A 🔴 RED → resolved via user Option B Recommended)**: Plan v0 framing assumed Quotas follows Sprint 57.54+57.55 canonical-service-+-override-storage architecture. **Reality**: Quotas has **NO** per-tenant override storage — `PlanQuota` is per-Plan template (immutable per-tenant via PlanLoader YAML). User selected Option B at Day 0: use `tenant.meta_data["quota_overrides"]` JSONB pattern (mirrors Sprint 57.48 RateLimits Track D + Sprint 57.50 Identity).

**Corrected baseline**:

- ✅ `backend/src/infrastructure/db/models/identity.py::Tenant.meta_data` JSONB column exists (default `{}`; per Sprint 57.50 D-DAY0-2 lesson Tenant ORM lives in `identity.py` not `tenant.py`)
- ✅ `backend/src/api/v1/admin/tenants.py` L1098-1173 (Sprint 57.48 Track C) implements `GET /admin/tenants/{tenant_id}/quotas` — projects 4 PlanQuota fields via `_project_plan_quota_to_items(plan_quota)` helper at L1126-1141
- ✅ `backend/src/platform_layer/tenant/plans.py::PlanQuota` per-Plan template (4 fields: `tokens_per_day: int` / `cost_usd_per_day: float` / `sessions_per_user_concurrent: int` / `api_keys_max: int`) — source of truth for default
- ✅ `backend/src/platform_layer/tenant/quota.py::QuotaEnforcer` Redis-backed runtime enforcement (per-tenant cap resolved from `PlanLoader.get_plan(tenant.plan).quota.tokens_per_day`); **does NOT need modification** in Sprint 57.56 (runtime continues reading from plan template)
- ✅ `frontend/src/features/tenant-settings/hooks/useQuotas.ts` (Sprint 57.49) read hook with `QUOTAS_QUERY_KEY_BASE = ["tenant-settings", "quotas"]`
- ✅ `frontend/src/features/tenant-settings/components/tabs/QuotasTab.tsx` (Sprint 57.49) reads + displays via the hook + ALSO renders RateLimits Card combined + `BackendGapBanner` copy: "Live usage tracking (current_usage): backend extension Phase 58+ — limits shown are tenant-effective from PlanQuota"
- ❌ NO per-tenant override layer (D-DAY0-A → Option B selected)
- ❌ NO canonical service like Sprint 57.54 (`DBHITLPolicyStore.put()`) or Sprint 57.55 (`FeatureFlagsService.set_tenant_override`); Sprint 57.56 uses **direct ORM UPDATE** on tenants.meta_data with manual audit_log_append (mirrors Sprint 57.48 RateLimits direct meta_data write + Sprint 57.3 PATCH tenant audit chain pattern)
- ❌ NO `PUT /admin/tenants/{tenant_id}/quotas` endpoint (write side gap)
- ❌ NO `useQuotasSave` mutation hook on frontend
- ❌ NO `saveQuotaOverrides` service func

**Actual Sprint 57.56 scope** = the WRITE side referenced explicitly in the existing BackendGapBanner copy + Option B `tenants.meta_data["quota_overrides"]` JSONB pattern:

### 2.2 True Phase 58.x gap for Quotas (post Day 0 D-DAY0-A Option B resolution)

**Backend gaps** (Sprint 57.56 closes):
1. ❌ `tenant.meta_data["quota_overrides"]` JSONB write path (direct ORM UPDATE; namespace key `"quota_overrides"` parallel to Sprint 57.48 `"rate_limits"` + Sprint 57.50 `"identity"`)
2. ❌ `PUT /admin/tenants/{tenant_id}/quotas` admin endpoint (composite-replace semantics; mirrors Sprint 57.54+57.55 pattern)
3. ❌ `QuotaOverridesUpsertRequest` Pydantic write schema (composite `overrides: dict[str, float]`; resource-keyed; float-uniform for cost_usd_per_day + int-coerced for token/session/keys)
4. ❌ `_project_plan_quota_to_items` GET helper extension to merge `tenant.meta_data["quota_overrides"]` overlay over plan default
5. ❌ Pytest tests covering upsert/multi-tenant isolation/unknown resource rejection (422)/composite-replace clear behavior/audit chain emit verification/idempotency

**Frontend gaps** (Sprint 57.56 closes):
1. ❌ `saveQuotaOverrides(tenantId, payload)` service func
2. ❌ `useQuotasSave(tenantId)` TanStack mutation hook (with invalidation of `QUOTAS_QUERY_KEY_BASE`)
3. ❌ `QuotasTab` edit-mode toggle on **Usage quotas Card ONLY** (Edit/Cancel/Save buttons + per-row numeric input + "clear override" button to revert to plan default; RateLimits Card unchanged → Sprint 57.57 candidate)
4. ❌ Vitest tests (mutation hook + tab edit mode)
5. ❌ BackendGapBanner copy soften (remove "tenant-effective from PlanQuota" framing — only live usage tracking via Redis counter exposure remains Phase 58+)

**Deferred (REMAINS Phase 58+)**:
- ❌ Live usage tracking (`current_usage` real Redis counter exposure at admin layer; QuotaEnforcer Redis counters per-day, not admin-readable) — Phase 58+ scope
- ❌ Quota usage history / trend chart — Phase 58+ extension
- ❌ Per-resource alerting thresholds — Phase 58+ extension
- ❌ Quota request increase workflow (existing "Request increase" button is alert stub; backend gap) — Phase 58+
- ❌ Plan upgrade auto-rollover (override map invalidation on plan change) — Phase 58+
- ❌ Optimistic concurrency / If-Match (Sprint 57.50 Identity Phase 58.x precedent — also deferred)

### 2.3 Why `mechanical-greenfield-design-decisions` 0.65 tier-4 1st validation (NOT port-style 0.45)

Per Sprint 57.55 retro Q4 tier-4 SPLIT ACTIVATION decision + `sprint-workflow.md §Active Agent Delegation Factor Modifier` tier-4 sub-class table effective Sprint 57.56+:

| Sub-class | Trigger | Sprint 57.56 fit? |
|-----------|---------|--------------------|
| `mechanical-pattern-reuse-heavy` 0.30 | ≥ 4 mechanical repetitions of same template in 1 sprint | ❌ Sprint 57.56 = 1 NEW endpoint pair + 1 NEW mutation hook + 1 tab edit mode (counts as 1 component-pair, not 4) |
| `mechanical-greenfield-port-style` 0.45 RESERVED | Single NEW component-pair via mirror-port; **NO** NEW Pydantic schema design / NO NEW UX state design | ❌ Sprint 57.56 has NEW Pydantic numeric union design + NEW edit-mode UX state design (composite-replace + per-resource clear UI) |
| **`mechanical-greenfield-design-decisions` 0.65 NEW** | Single NEW component-pair WITH NEW Pydantic + UX state design | ✅ MATCH — mirrors Sprint 57.54+57.55 retroactive `-design-decisions` mapping exactly |
| `mixed-multidomain-bundle-mechanical` 0.65 | 3+ independent tracks WITH mechanical pattern reuse | ❌ Sprint 57.56 = single Quotas domain |
| `mixed-multidomain-bundle-non-mechanical` 1.0 | 3+ independent tracks; pure audit/docs/rules | ❌ |

**1st validation prediction**:
- Sprint 57.54+57.55 retroactive `-design-decisions` mapping under 0.65: equivalent ratios 1.05-1.55 / 1.21 = top band edge / IN band middle
- Sprint 57.56 = same shape (single new endpoint + hook + tab edit mode) but **architecturally simpler** than 57.55 (no canonical service extension; direct ORM UPDATE; mirrors Sprint 57.48 RateLimits pattern internalized)
- Predicted actual ratio under tier-4 0.65: **~1.0-1.4 IN/ABOVE band top edge** (greenfield design decisions still apply: Pydantic numeric union + per-resource clear semantics + Card-scoped edit mode; pattern-reuse acceleration vs Sprint 57.55 internalized)
- **Decision matrix at Sprint 57.56 retro Q4**:
  - If lands IN band [0.85, 1.20] → tier-4 SPLIT 1st validation confirmed cleanly; KEEP 0.65; flag Sprint 57.57+ 2nd validation for rollback rule baseline
  - If lands > 1.20 → 1st > 1.20 data point single-data-point caution KEEP; flag Sprint 57.57+ 2nd validation; if Sprint 57.57 also > 1.20 → 2 consec rollback rule MET → propose 0.65 → 0.80 lift
  - If lands < 0.7 → 1st < 0.7 data point single-data-point caution KEEP; flag Sprint 57.57+ 2nd validation; if Sprint 57.57 also < 0.7 → 2 consec rollback rule MET → propose 0.65 → 0.45 tighten (matching `-port-style` baseline)

### 2.4 Pattern-reuse capture (Sprint 57.54 HITLPolicies + Sprint 57.55 FeatureFlags WRITE precedents)

Sprint 57.54+57.55 established the WRITE-side template:
- `PUT /admin/tenants/{tenant_id}/<resource>` upsert endpoint with composite-replace semantics
- Pydantic `<Resource>UpsertRequest` with `extra="forbid"` + `field_validator`
- Pydantic `<Resource>UpsertResponse` echoing saved composite + projected items
- `useResourceSave` TanStack mutation hook (mirror `useTenantSettingsSave` Sprint 57.9)
- Tab edit mode: editing state + draft state + Edit/Cancel/Save buttons + per-row form + reverse-projection items→composite draft seed + BackendGapBanner copy soften
- conftest.py `<RESOURCE>_PUT_%` LIKE sweep extension (mirrors Sprint 57.12 + 57.53 §Committed-Row Cleanup Pattern)

**Sprint 57.56 architectural simplification vs 57.55** (D-DAY0-D 🆕 NOTABLE):
- ❌ NO canonical service extension (FF/HITL had `set_tenant_override`/`put()`)
- ✅ Direct ORM UPDATE on `Tenant.meta_data` (mirrors Sprint 57.48 RateLimits + Sprint 57.50 Identity precedent)
- ✅ Manual `audit_log_append(operation="tenant_quota_overrides_upsert", ...)` (Sprint 57.3 PATCH tenant precedent)
- ✅ GET helper extension reads merged plan default + override overlay (existing `_project_plan_quota_to_items` minimal extension)

### 2.5 Sprint 57.55 carryover chain (`AD-AgentFactor-Tier-4-Validation-Sprint-57.56`)

- Sprint 57.52 retro Q4 (2026-05-26): tier-3 SPLIT ACTIVATED — `mixed-multidomain-bundle-mechanical` 0.65 + `mixed-multidomain-bundle-non-mechanical` 1.0
- Sprint 57.53 was first sprint under new tier-3 sub-class table effective Sprint 57.53+ — parent-assistant-direct execution (`agent_factor = 1.0`); 1st validation NOT generated → carryover renamed Sprint 57.54
- Sprint 57.54 generated `mechanical-greenfield` 0.50 tier-3 1st validation: ratio ~1.37-2.0 ABOVE band by 0.17-0.8 → KEEP single-data-point caution; flag Sprint 57.55+ for 2nd validation
- Sprint 57.55 generated `mechanical-greenfield` 0.50 tier-3 2nd validation: ratio ~1.57 ABOVE band by 0.37 → 2 consec > 1.20 ROLLBACK RULE MET → **tier-4 SPLIT ACTIVATED**: `mechanical-greenfield-port-style` 0.45 RESERVED + `mechanical-greenfield-design-decisions` 0.65 NEW
- Sprint 57.56 = mandated agent-delegated mode to deliver the 1st validation data point under tier-4 `-design-decisions` 0.65 (closes `AD-AgentFactor-Tier-4-Validation-Sprint-57.56`)

### 2.6 Class baseline tracking continuation

- `medium-backend` 0.80: Sprint 57.55 was 8th data point (ratio 0.79; 8-pt mean 0.65; last-3 mean 0.87 IN band lower-middle; KEEP per Sprint 57.55 retro Q4). Sprint 57.56 = 9th data point continuing post-confound-resolution tracking.
- `medium-frontend` 0.65: Sprint 57.55 was 5th data point (ratio 0.53 frontend sub-portion; 5-pt mean ~0.55; last 3 = 3/3 < 0.7 lower-trigger criteria MET BUT KEEP per Sprint 57.50 retro confound-resolved-at-sub-class-layer discipline — frontend confound resolved at tier-4 sub-class layer; class baseline 0.65 confirmed well-calibrated for human-pace). Sprint 57.56 frontend portion = 6th data point. AD-medium-frontend-Baseline-Recalibration continues — need consistent human-factor data point to recalibrate.

---

## 3. User Stories

### US-1: Backend WRITE side — PUT overrides endpoint + tenants.meta_data write

```
AS the V2 backend developer extending the existing Sprint 57.48 Track C
   Quotas admin API surface (read-only) to support per-tenant Quotas
   override write
I WANT the WRITE side for `tenants.meta_data["quota_overrides"]` JSONB +
   `PUT /admin/tenants/{tenant_id}/quotas` upsert endpoint + Pydantic
   `QuotaOverridesUpsertRequest` write schema implemented + GET helper
   extension to merge plan default with override overlay + integration
   tests covering all critical paths (auth/404/upsert-create/upsert-
   update/multi-tenant isolation/unknown resource rejection/empty
   overrides/idempotency/persistence-via-GET)
SO THAT admin operators can configure per-tenant Quotas overrides
   programmatically + the frontend QuotasTab can ship edit mode in
   US-2 without backend gap.
```

**Acceptance**:
- WRITE path uses direct SQLAlchemy `ORMQuery.update(meta_data=...)` OR `jsonb_set` UPDATE on existing tenants row; composite override map written atomically; tenants.updated_at rotates server-side via existing `onupdate=func.now()` invariant
- `QuotaOverridesUpsertRequest` Pydantic model with composite shape (single field `overrides: dict[str, float]`); `extra="forbid"`; resource names validated against PlanQuota field whitelist (4 known: `tokens_per_day` / `cost_usd_per_day` / `sessions_per_user_concurrent` / `api_keys_max`)
- `PUT /admin/tenants/{tenant_id}/quotas` endpoint returns 200 OK with `QuotaOverridesUpsertResponse` (echoes saved composite + projected `items` list matching GET shape with override overlay applied)
- Endpoint uses `Depends(require_admin_platform_role)` (matches existing GET endpoint per Sprint 57.48 Track C)
- Endpoint uses `_load_tenant_or_404` for 404 path consistency
- Unknown resource names rejected with 422 (4-name whitelist enforced via `field_validator` or post-coercion check)
- GET endpoint refactored to merge `tenant.meta_data["quota_overrides"]` overlay over plan default per resource (extension to `_project_plan_quota_to_items` accepting optional `overrides: dict[str, float]` parameter)
- Audit chain entry emitted via direct `audit_log_append(...)` call (mirrors Sprint 57.3 PATCH tenant precedent; operation=`tenant_quota_overrides_upsert`)
- Pytest 10-12 NEW tests added in `backend/tests/integration/api/test_admin_tenant_quotas.py` (extend existing Sprint 57.48 file):
  - `test_put_requires_admin_role` (401/403)
  - `test_put_tenant_not_found` (404)
  - `test_put_creates_new_overrides` (200; no prior overrides in meta_data)
  - `test_put_updates_existing_overrides` (200; prior overrides, new map replaces)
  - `test_put_response_projects_items_matching_get` (response.items echoes GET shape with override applied)
  - `test_put_unknown_resource_rejected` (422; resource name not in PlanQuota whitelist)
  - `test_put_extra_field_rejected` (422; payload with non-`overrides` field)
  - `test_put_multi_tenant_isolation` (tenant_b PUT does NOT affect tenant_a meta_data)
  - `test_put_empty_overrides_clears_all` (200; PUT with `{}` clears all overrides → GET returns plan defaults)
  - `test_put_idempotent_same_payload_twice` (PUT twice same payload → consistent state; updated_at rotates)
  - `test_put_persists_to_db_via_subsequent_get` (post-PUT GET reflects new resolved_value across all 4 quota items)
  - `test_put_audit_chain_emitted` (operation=`tenant_quota_overrides_upsert` row appears in audit_log)
- Pytest count delta: +10 to +12 (current 1784 PASS → 1794-1796 PASS); 0 fail; 0 skip change

### US-2: Frontend WRITE side — useQuotasSave + QuotasTab Usage quotas Card edit mode

```
AS the V2 frontend developer extending the Sprint 57.49 QuotasTab
   (read-only display of Usage quotas + Rate limits combined) to support
   inline edit mode on Usage quotas Card matching the Sprint 57.54+57.55
   edit-mode pattern for tenant-settings admin UX consistency
I WANT a NEW `useQuotasSave(tenantId)` TanStack mutation hook +
   `saveQuotaOverrides` service func + edit-mode UI on QuotasTab Usage
   quotas Card ONLY (Edit/Cancel/Save buttons + per-row numeric input +
   "clear" button to remove explicit override + reverse-projection
   items→composite draft seed; RateLimits Card unchanged — Sprint 57.57
   candidate per scope guard) + Vitest tests covering mutation success/
   error/cache invalidation
SO THAT the BackendGapBanner copy can be softened (only live usage
   tracking via Redis counter exposure remains Phase 58+, override
   edit API now real-backed).
```

**Acceptance**:
- `frontend/src/features/tenant-settings/services/tenantSettingsService.ts` — NEW `saveQuotaOverrides(tenantId, payload)` async func using `fetchWithAuth` PUT; matches existing `fetchQuotas` / `saveHITLPolicies` / `saveFeatureFlagOverrides` patterns
- `frontend/src/features/tenant-settings/types.ts` — NEW types `QuotaOverridesUpsertRequest` + `QuotaOverridesUpsertResponse` (type module-level per Sprint 57.54 D-DAY1-2 precedent; NOT inline in service)
- `frontend/src/features/tenant-settings/hooks/useQuotasSave.ts` — NEW TanStack `useMutation` hook with `onSuccess` invalidation of `QUOTAS_QUERY_KEY_BASE` (re-fetches GET); error propagation via existing pattern (mirror `useHITLPoliciesSave` Sprint 57.54 + `useFeatureFlagsSave` Sprint 57.55 verbatim)
- `frontend/src/features/tenant-settings/components/tabs/QuotasTab.tsx` — edit mode on Usage quotas Card ONLY:
  - State: `editing: boolean` + `draft: Record<string, number>` (composite shape mirroring write schema; seeded by reverse-projection from items where override differs from plan default)
  - Edit button: top-right of Usage quotas Card, toggles `editing`
  - Edit form: per-row numeric `<input type="number">` + "clear" button to remove explicit override (sets that resource to undefined in draft → omitted from payload)
  - Save / Cancel buttons: Save calls mutation, Cancel reverts draft + exits edit mode
  - Success → exits edit mode + invalidates QUOTAS_QUERY_KEY_BASE
  - Error → keeps form open + shows error message
  - **Scope guard**: RateLimits Card unchanged (Sprint 57.57 candidate)
  - **Mockup-fidelity discipline**: 0 NEW hex/oklch literals (reuse existing `--info`/`--warning`/`--success`/`--danger` tokens via existing buttons via `--btn-primary` pattern from existing tabs and Sprint 57.54+57.55 edit modes)
- BackendGapBanner copy update: from "Live usage tracking (current_usage): backend extension Phase 58+ — limits shown are tenant-effective from PlanQuota" → "Live usage tracking (current_usage Redis counter exposure): backend extension Phase 58+ — limits shown are tenant-effective + editable via Edit button"
- Vitest 5-8 NEW tests added across:
  - `frontend/tests/unit/tenant-settings/useQuotasSave.test.tsx` (NEW file; mutation success → invalidates QUERY_KEY / mutation error → propagates error / payload shape)
  - `frontend/tests/unit/tenant-settings/tabs/QuotasTab.test.tsx` (extend OR create if missing; new edit-mode tests + banner copy assertion update)
  - `frontend/tests/unit/tenant-settings/tenantSettingsService.test.ts` (extend; saveQuotaOverrides PUT shape + URL + body)
- Vitest count delta: +5 to +8 (current 630 PASS → 635-638 PASS); 0 fail; 0 skip change

### US-3: AD-Plan-Workload-AgentDelegation-Explicit-Field-Codification (CONDITIONAL on Sprint 57.56 validation success)

Sprint 57.53 retro Q5 carried `AD-Plan-Workload-AgentDelegation-Explicit-Field` (codify sprint plan §6 pre-commit "agent-delegated: yes/no/partial/TBD-Day-1-decision" field). Sprint 57.54+57.55 plans both explicitly filled this field. Sprint 57.56 plan continues — **3rd consecutive data point** under the proposed mandatory rule.

**This sprint validates the codification value for the 3rd time** (Plan-time agent-delegation explicit field, 3 data points). If Sprint 57.56 1st validation succeeds (cleanly delivers tier-4 1st data point regardless of direction), Sprint 57.56 retro Q5 SHOULD promote the rule edit to `sprint-workflow.md §Workload Calibration §Four-segment form when agent_factor applies` as MANDATORY field (3-data-point evidence sufficient per AD-Plan-2/3/4/5 promotion precedent).

**Acceptance** (this sprint):
- Plan §Workload 4-segment form contains explicit "Agent-delegated: yes" line ✅
- Day 1 retrospective Q2 records actual delegation mode (confirm `yes` vs reclassify `partial` if any track diverges)
- IF Sprint 57.56 1st validation cleanly lands → Sprint 57.56 retro Q5 propose codification edit (promote to MANDATORY in `sprint-workflow.md`)

---

## 4. Technical Specification

### 4.1 Backend Track — Direct ORM UPDATE on tenants.meta_data (D-DAY0-D simpler path)

**Pivot rationale** (D-DAY0-D 🆕 NOTABLE): per-tenant Quotas overrides have **NO** canonical service like Sprint 57.54+57.55 (FF/HITL); Sprint 57.56 uses **direct ORM UPDATE on `Tenant.meta_data["quota_overrides"]`** (mirrors Sprint 57.48 RateLimits + Sprint 57.50 Identity precedent). Audit chain emitted via direct `audit_log_append` call (Sprint 57.3 PATCH tenant precedent). Architecturally simpler than 57.54+57.55 — no NEW method on service class.

**File 1**: `backend/src/api/v1/admin/tenants.py` (extend; ~120 lines added)

```python
# === Sprint 57.56 — Quotas admin PUT (closes AD-Quotas-Backend-Write Phase 58.x) ===
# Option B per user direction 2026-05-27: tenant.meta_data["quota_overrides"]
# JSONB direct ORM write (mirrors Sprint 57.48 RateLimits Track D + Sprint 57.50
# Identity precedent); audit chain via direct audit_log_append (Sprint 57.3 PATCH
# tenant precedent). No canonical service like Sprint 57.54+57.55 (FF/HITL).

_PLAN_QUOTA_RESOURCE_WHITELIST: frozenset[str] = frozenset({
    "tokens_per_day",
    "cost_usd_per_day",
    "sessions_per_user_concurrent",
    "api_keys_max",
})


class QuotaOverridesUpsertRequest(BaseModel):
    """Composite Quota overrides upsert payload (composite-replace semantics)."""

    model_config = ConfigDict(extra="forbid")
    overrides: dict[str, float] = Field(
        default_factory=dict,
        description=(
            "Map of resource name → override limit (float; int-coerced for "
            "tokens/sessions/keys). Composite-replace semantics: resources NOT "
            "in payload but currently overridden for this tenant are cleared "
            "(reverts to plan default)."
        ),
    )

    @field_validator("overrides")
    @classmethod
    def _check_resource_names(cls, v: dict[str, float]) -> dict[str, float]:
        unknown = set(v.keys()) - _PLAN_QUOTA_RESOURCE_WHITELIST
        if unknown:
            raise ValueError(
                f"Unknown quota resource(s): {sorted(unknown)}; "
                f"allowed: {sorted(_PLAN_QUOTA_RESOURCE_WHITELIST)}"
            )
        return v


class QuotaOverridesUpsertResponse(BaseModel):
    """Echoes saved composite + projects items list for cache hydration."""

    saved_overrides: dict[str, float]
    items: list[QuotaItem]


def _project_plan_quota_to_items(
    plan_quota: Any,
    overrides: dict[str, float] | None = None,
) -> list[QuotaItem]:
    """Project PlanQuota fields to QuotaItem list; merge per-tenant override
    overlay when provided.

    Sprint 57.56 extension: accepts optional `overrides` map (resource → value)
    from `tenant.meta_data["quota_overrides"]`; applied as overlay over plan
    default per resource. Existing Sprint 57.48 GET behavior preserved when
    overrides=None.
    """
    overrides = overrides or {}
    items: list[QuotaItem] = []
    for attr, unit, period in _QUOTA_RESOURCE_META:
        raw = overrides.get(attr, getattr(plan_quota, attr, None))
        if raw is None:
            continue
        items.append(
            QuotaItem(
                resource=attr,
                limit=float(raw),
                unit=unit,
                period=period,
                current_usage=None,
            )
        )
    return items


@router.put(
    "/{tenant_id}/quotas",
    response_model=QuotaOverridesUpsertResponse,
    dependencies=[Depends(require_admin_platform_role)],
)
async def upsert_tenant_quota_overrides(
    tenant_id: UUID,
    payload: QuotaOverridesUpsertRequest,
    db: AsyncSession = Depends(get_db_session),
    actor_user_id: UUID = Depends(require_admin_platform_role),
) -> QuotaOverridesUpsertResponse:
    """Upsert per-tenant Quotas overrides into tenant.meta_data["quota_overrides"].

    Composite-replace semantics: payload.overrides represents the COMPLETE desired
    override state for this tenant. Any resource with a current tenant override that
    is NOT in payload.overrides will be CLEARED (reverts to plan default).

    - 401/403 via require_admin_platform_role
    - 404 via _load_tenant_or_404
    - 422 via QuotaOverridesUpsertRequest field_validator (unknown resource)
    - 200 with response.saved_overrides + response.items (projected for cache hydration)
    - Audit chain entry emitted via direct audit_log_append (Sprint 57.3 precedent)
    """
    tenant = await _load_tenant_or_404(db, tenant_id)

    # Write override map into meta_data["quota_overrides"]
    new_meta = dict(tenant.meta_data or {})
    new_meta["quota_overrides"] = dict(payload.overrides)
    tenant.meta_data = new_meta

    # Audit chain (Sprint 57.3 PATCH tenant precedent)
    await audit_log_append(
        db,
        tenant_id=tenant_id,
        user_id=actor_user_id,
        operation="tenant_quota_overrides_upsert",
        resource_type="tenant",
        resource_id=str(tenant_id),
        operation_data={
            "tenant_id": str(tenant_id),
            "overrides": dict(payload.overrides),
        },
        operation_result="success",
    )

    await db.commit()
    await db.refresh(tenant)

    # Project items (cache hydration consistency with GET)
    loader: PlanLoader = get_plan_loader()
    try:
        plan = loader.get_plan(tenant.plan.value)
        items = _project_plan_quota_to_items(plan.quota, overrides=payload.overrides)
    except Exception:
        items = []

    return QuotaOverridesUpsertResponse(
        saved_overrides=payload.overrides,
        items=items,
    )
```

**GET refactor**: Sprint 57.48 Track C `list_tenant_quotas` extends to read `tenant.meta_data.get("quota_overrides") or {}` and pass to `_project_plan_quota_to_items(plan.quota, overrides=...)`. Existing GET tests pass unmodified (overrides default to empty → behavior preserved).

**Total backend code**: ~120 lines net (NEW Pydantic 2 + endpoint 1 + GET refactor + helper extension).

### 4.2 Backend Track — Pytest tests

**File**: `backend/tests/integration/api/test_admin_tenant_quotas.py` (extend existing Sprint 57.48 file)

Add 10-12 NEW tests after the existing GET tests (which already establish auth/404/multi-tenant patterns; reuse fixtures verbatim). Helpers: `_unique_code()` uuid4-suffix builder (mirror Sprint 57.55 pattern).

**File**: `backend/tests/integration/api/conftest.py` (extend `_clear_committed_test_tenants` LIKE sweep)

Add `QUOTA_PUT_%` LIKE prefix to the existing `_clear_committed_test_tenants()` cleanup sweep (mirrors Sprint 57.54 `HITL_PUT_%` + Sprint 57.55 `FF_PUT_%` extensions; parallels Sprint 57.12 + 57.53 §Committed-Row Cleanup Pattern).

### 4.3 Frontend Track — Types module

**File**: `frontend/src/features/tenant-settings/types.ts` (extend)

```typescript
export interface QuotaOverridesUpsertRequest {
  overrides: Record<string, number>;
}

export interface QuotaOverridesUpsertResponse {
  saved_overrides: Record<string, number>;
  items: QuotaItem[];
}
```

### 4.4 Frontend Track — Service func

**File**: `frontend/src/features/tenant-settings/services/tenantSettingsService.ts` (extend)

```typescript
export async function saveQuotaOverrides(
  tenantId: string,
  payload: QuotaOverridesUpsertRequest,
  signal?: AbortSignal
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
```

### 4.5 Frontend Track — Mutation hook

**File**: `frontend/src/features/tenant-settings/hooks/useQuotasSave.ts` (NEW; mirror `useFeatureFlagsSave.ts` Sprint 57.55 verbatim)

```typescript
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { saveQuotaOverrides } from "../services/tenantSettingsService";
import type {
  QuotaOverridesUpsertRequest,
  QuotaOverridesUpsertResponse,
} from "../types";
import { QUOTAS_QUERY_KEY_BASE } from "./useQuotas";

export function useQuotasSave(tenantId: string) {
  const queryClient = useQueryClient();
  return useMutation<
    QuotaOverridesUpsertResponse,
    Error,
    QuotaOverridesUpsertRequest
  >({
    mutationFn: (payload) => saveQuotaOverrides(tenantId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...QUOTAS_QUERY_KEY_BASE, tenantId],
      });
    },
  });
}
```

### 4.6 Frontend Track — QuotasTab edit mode (Usage quotas Card ONLY)

**File**: `frontend/src/features/tenant-settings/components/tabs/QuotasTab.tsx` (edit)

Edit mode adds to Usage quotas Card ONLY:
- State: `const [editing, setEditing] = useState(false); const [draft, setDraft] = useState<Record<string, number>>(seedFromItems);`
- useEffect on tenantId change → reset both editing + draft
- Edit toggle button (top-right of Usage quotas Card header area)
- Form: per-row numeric `<input type="number">` + "clear override" button (sets that resource to undefined in draft → omitted from payload)
- Save → call useQuotasSave mutation; Cancel → reset draft + exit
- BackendGapBanner copy soften
- **RateLimits Card unchanged** (Sprint 57.57 scope guard)

### 4.7 Verification

- `cd backend && pytest tests/integration/api/test_admin_tenant_quotas.py -v` → all PASS (existing + 10-12 NEW)
- `cd backend && pytest --tb=short -q` → 1794-1796 PASS + 0 fail
- `cd backend && mypy --strict src/` → 0 errors
- `python scripts/lint/run_all.py` → 9/9 GREEN
- `cd frontend && npm run lint && npm run build` → exit 0 / 0 ESLint / 0 tsc errors (NOT `--silent` per AD-Pre-Push-Lint-Silent-Suppression-Anti-Pattern)
- `cd frontend && npm run test` → 635-638 PASS
- LLM SDK leak scan → 0

---

## 5. File Change List

### Backend (EDIT only — no NEW files; architecturally simpler than 57.54+57.55)
- **EDIT**: `backend/src/api/v1/admin/tenants.py` — add `QuotaOverridesUpsertRequest` + `QuotaOverridesUpsertResponse` Pydantic + `_PLAN_QUOTA_RESOURCE_WHITELIST` frozenset + `_project_plan_quota_to_items` overrides parameter extension + GET refactor to pass override overlay + `upsert_tenant_quota_overrides` endpoint (~120 lines net)
- **EDIT**: `backend/tests/integration/api/test_admin_tenant_quotas.py` — add 10-12 NEW PUT tests (~260 lines)
- **EDIT**: `backend/tests/integration/api/conftest.py` — add `QUOTA_PUT_%` LIKE sweep (~1 line addition to existing `_clear_committed_test_tenants`)

### Frontend (NEW + EDIT)
- **EDIT**: `frontend/src/features/tenant-settings/types.ts` — add `QuotaOverridesUpsertRequest` + `QuotaOverridesUpsertResponse` types (~10 lines)
- **EDIT**: `frontend/src/features/tenant-settings/services/tenantSettingsService.ts` — add `saveQuotaOverrides` service func (~19 lines incl. import)
- **NEW**: `frontend/src/features/tenant-settings/hooks/useQuotasSave.ts` — mutation hook (~45 lines incl. full header)
- **EDIT**: `frontend/src/features/tenant-settings/components/tabs/QuotasTab.tsx` — add Usage quotas Card edit mode (~150 lines added; soften BackendGapBanner copy; RateLimits Card unchanged)
- **NEW**: `frontend/tests/unit/tenant-settings/useQuotasSave.test.tsx` — mutation hook Vitest tests (~110 lines)
- **EDIT/NEW**: `frontend/tests/unit/tenant-settings/tabs/QuotasTab.test.tsx` — extend with edit-mode tests + banner copy assertion update (if file exists; else NEW; ~120 lines added)
- **EDIT**: `frontend/tests/unit/tenant-settings/tenantSettingsService.test.ts` — extend with saveQuotaOverrides test (~45 lines)

### Sprint artifacts (Day 0 + Day 2)
- `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-56-plan.md` (this file)
- `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-56-checklist.md`
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-56/progress.md`
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-56/retrospective.md`
- `memory/project_phase57_56_quotas_write_endpoint.md`
- `memory/MEMORY.md` (pointer entry)
- `claudedocs/1-planning/next-phase-candidates.md` (Sprint 57.56 closeout note)
- `CLAUDE.md` (Current Sprint row + Last Updated footer)
- `.claude/rules/sprint-workflow.md` (matrix +1 row data point for `mechanical-greenfield-design-decisions` 0.65 1st validation + `medium-backend` 0.80 9th + `medium-frontend` 0.65 6th + §Active block 1st validation entry under tier-4 sub-class table)
- `claudedocs/4-changes/feature-changes/CHANGE-026-quotas-write-endpoint.md` (NEW — per CLAUDE.md `4-changes/` convention)

---

## 6. Workload

**Bottom-up est**: ~3.3 hr
- Day 0 三-prong (Prong 1 path verify on admin/tenants.py + frontend tab/hook/service paths; Prong 2 content verify on baseline ALREADY DONE in this plan §2.1; Prong 3 schema verify on tenants.meta_data JSONB column + PlanQuota whitelist): ~0.3 hr (DONE pre-plan)
- Day 1 Backend track (PUT endpoint + Pydantic + helper extension + ~10-12 pytest tests, agent-delegated via code-implementer; ~15-20% faster than Sprint 57.55 due to no canonical service extension + pattern fully internalized): ~1.2 hr human-equivalent
- Day 1 Frontend track (types + service func + mutation hook + Usage quotas Card edit mode + ~5-8 Vitest tests + BackendGapBanner copy soften, agent-delegated via code-implementer; ~15-20% faster than Sprint 57.55 due to template internalization): ~1.2 hr human-equivalent
- Day 2 closeout (progress + retro + memory + sprint-workflow.md matrix + CLAUDE.md + next-phase-candidates + CHANGE-026 + commit + PR): ~0.6 hr (slightly heavier than Sprint 57.55 because tier-4 1st validation Q4 narrative requires rollback rule baseline framing)

**Class-calibrated commit** (`medium-backend` 0.80):
- 3.3 × 0.80 = **~2.64 hr committed (~158 min)**

**Agent-adjusted commit** (`agent_factor = 0.65` tier-4 `mechanical-greenfield-design-decisions` — **1st validation**):
- 2.64 × 0.65 = **~1.72 hr agent-adjusted (~103 min)**

**4-segment form**:
> Bottom-up est ~3.3 hr → class-calibrated commit ~2.64 hr (mult 0.80) → agent-adjusted commit ~1.72 hr (agent_factor 0.65 tier-4 `mechanical-greenfield-design-decisions` — **1st validation under tier-4 table** effective Sprint 57.56+)
> **Agent-delegated**: **yes** — backend + frontend via code-implementer agent delegation (sequential: backend first, then frontend with backend types confirmed; mirror Sprint 57.54+57.55 sequence; 18th + 19th consecutive code-implementer)

**1st validation prediction (tier-4 `mechanical-greenfield-design-decisions` 0.65)**:
- Single component-pair (1 backend endpoint + 1 frontend mutation hook + 1 tab edit-mode) cleanly scoped; agent-delegated pattern from Sprint 57.49-57.55 internalized (18th-19th consecutive frontend agent)
- **Pattern-reuse acceleration vs Sprint 57.55**: Sprint 57.55 had FF canonical service path (D-DAY0-T pivot ~15-line clear_tenant_override extension); Sprint 57.56 has simpler direct ORM UPDATE (no canonical service; mirrors Sprint 57.48 RateLimits + Sprint 57.50 Identity verbatim); expect ~15-20% faster than Sprint 57.55 baseline
- Expected actual ~50-65 min wall-clock total (backend ~10-15 min agent + frontend ~25 min agent + supervisory ~5-10 min + Day 0 ~15 min DONE + Day 2 closeout ~20-25 min)
- Predicted ratio actual/committed-with-agent-factor: **~1.0-1.4 IN/ABOVE band top edge** (greenfield design decisions still apply: Pydantic numeric union + per-resource clear semantics + Card-scoped edit mode)
- **Decision matrix at Sprint 57.56 retro Q4**:
  - If lands IN band [0.85, 1.20] → tier-4 SPLIT 1st validation confirmed cleanly; KEEP 0.65; flag Sprint 57.57+ 2nd validation
  - If lands > 1.20 → 1st > 1.20 data point single-data-point caution KEEP; flag Sprint 57.57+ 2nd validation; if 2 consec > 1.20 → propose 0.65 → 0.80 lift
  - If lands < 0.7 → 1st < 0.7 data point single-data-point caution KEEP; flag Sprint 57.57+ 2nd validation; if 2 consec < 0.7 → propose 0.65 → 0.45 tighten (matching `-port-style` baseline; would suggest the SPLIT was wrong direction)

---

## 7. Acceptance Criteria

| # | Criterion | Verify |
|---|---|---|
| AC-1 | `upsert_tenant_quota_overrides` endpoint declared with `@router.put("/{tenant_id}/quotas", ...)` | grep `@router.put.*quotas` in admin/tenants.py |
| AC-2 | Pydantic `QuotaOverridesUpsertRequest` + `QuotaOverridesUpsertResponse` declared + `extra="forbid"` set + `field_validator` on resource names | grep models in admin/tenants.py |
| AC-3 | Unknown resource names rejected with 422 (4-name whitelist enforced) | pytest `test_put_unknown_resource_rejected` |
| AC-4 | Multi-tenant isolation guarded (tenant_b PUT does not affect tenant_a meta_data) | pytest `test_put_multi_tenant_isolation` |
| AC-5 | Empty overrides clears all override map (GET returns plan defaults) | pytest `test_put_empty_overrides_clears_all` |
| AC-6 | `_project_plan_quota_to_items` extended with optional `overrides` parameter; GET refactored to pass override overlay; PUT reuses for response.items | grep helper signatures + invocations in admin/tenants.py |
| AC-7 | Audit chain entry emitted (operation=`tenant_quota_overrides_upsert`; resource_type=`tenant`) | pytest `test_put_audit_chain_emitted` |
| AC-8 | Pytest count delta +10 to +12 | `pytest --tb=short -q` count = 1794-1796 |
| AC-9 | Full backend pytest baseline ALL-GREEN | `pytest --tb=short -q` 0 fail |
| AC-10 | mypy --strict 0 errors | `mypy --strict src/` |
| AC-11 | 9 V2 lints preserved | `python scripts/lint/run_all.py` exit 0 |
| AC-12 | LLM SDK leak 0 | covered by `run_all.py` |
| AC-13 | NEW `saveQuotaOverrides` service func + `useQuotasSave` mutation hook implemented | grep files |
| AC-14 | QuotasTab Usage quotas Card edit-mode UI (Edit/Cancel/Save + per-row numeric input + clear button) functional | manual smoke + Vitest tab tests |
| AC-15 | QuotasTab RateLimits Card UNCHANGED (scope guard; Sprint 57.57 candidate) | grep + visual check |
| AC-16 | BackendGapBanner copy softened (remove "tenant-effective from PlanQuota" framing; only live usage tracking remains Phase 58+) | grep BackendGapBanner text |
| AC-17 | Vitest count delta +5 to +8 | `npm run test` count = 635-638 |
| AC-18 | Vite build clean | `npm run build` exit 0 |
| AC-19 | tsc strict 0 errors | covered by `npm run build` |
| AC-20 | ESLint 0 errors | `npm run lint` (NOT `--silent`) |
| AC-21 | File MHist updated on edited files (≤100 char budget per AD-Lint-MHist-Verbosity) | grep MHist lines |
| AC-22 | Day 0 三-prong report logged with drift findings | Read progress.md Day 0 |
| AC-23 | retrospective.md Q1-Q6 with **1st validation `mechanical-greenfield-design-decisions` 0.65 ratio + tier-4 SPLIT sanity check** in Q4 + agent-delegation confirmed in Q2 | grep Q2 + Q4 |
| AC-24 | sprint-workflow.md MHist + matrix `medium-backend` 0.80 9th data point + `medium-frontend` 0.65 6th data point + §Active block `mechanical-greenfield-design-decisions` 0.65 1st validation entry | grep |
| AC-25 | CHANGE-026-quotas-write-endpoint.md created | Read claudedocs/4-changes/feature-changes/ |
| AC-26 | conftest.py `QUOTA_PUT_%` LIKE sweep added (mirrors Sprint 57.54 `HITL_PUT_%` + 57.55 `FF_PUT_%`) | grep conftest.py |
| AC-27 | Mockup-fidelity DUAL CLEAN 22/22 PARITY preserved (12 consecutive sprints 57.45-57.56); HEX_OKLCH baseline 47 unchanged | check-mockup-fidelity.mjs PASS + grep oklch count |

---

## 8. Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| **`mechanical-greenfield-design-decisions` 0.65 tier-4 1st validation lands > 1.20** | Medium (Sprint 57.54+57.55 retroactive mapping was 1.21 at top band edge; pattern-reuse-acceleration may push slightly higher) | Sprint 57.56 retro Q4 single-data-point caution KEEP 0.65; flag Sprint 57.57+ 2nd validation; if 2 consec > 1.20 → propose 0.65 → 0.80 lift |
| **`mechanical-greenfield-design-decisions` 0.65 tier-4 1st validation lands in band [0.85, 1.20]** | High (Sprint 57.54+57.55 retroactive validates this range; pattern internalization should land here) | KEEP 0.65 baseline; tier-4 SPLIT 1st validation confirmed cleanly; flag Sprint 57.57+ continuing tracking |
| **`mechanical-greenfield-design-decisions` 0.65 tier-4 1st validation lands < 0.7** | Low (architectural simplification + pattern-reuse acceleration would need to push ratio below 0.7; possible if Sprint 57.56 turns out closer to `-port-style` than `-design-decisions` despite NEW Pydantic design) | 1st < 0.7 data point single-data-point caution KEEP; flag Sprint 57.57+ 2nd validation; if 2 consec < 0.7 → SPLIT was wrong direction → propose 0.65 → 0.45 tighten (would suggest reclassifying Sprint 57.56 as `-port-style` retroactively) |
| Unknown resource name validation cost (4-name whitelist hardcoded vs PlanQuota field introspection) | Low | Hardcoded frozenset acceptable (PlanQuota fields are stable); alternatives: dynamic introspection deferred Phase 58+ if PlanQuota schema expands |
| Composite-replace semantics vs per-resource PATCH | Medium (UX implication: user must include all explicit overrides in payload) | Documented in plan §4.1 + AC; frontend draft state seeded by reverse-projection (overridden-only items); user clears via "clear override" UI removing from draft; matches Sprint 57.54+57.55 composite-replace pattern |
| `tenants.meta_data` JSONB structure conflicts with other Phase 58.x portfolio items (RateLimits + Identity already use meta_data keys) | Low (verified §2.1 Prong 2: Sprint 57.50 Identity in meta_data["identity"]; Sprint 57.48 RateLimits in meta_data["rate_limits"]; FF target key `tenant_overrides` is distinct; Sprint 57.56 target key `quota_overrides` is distinct) | Use namespaced key `quota_overrides` (Sprint 57.48 D-DAY0-3 established convention); separate from other meta_data keys; mutate via dict-copy not in-place |
| Frontend edit-mode form draft state divergence on tenant switch | Medium | Use `[editing, draft]` state-pair; reset both on `tenantId` change via `useEffect` (Sprint 57.54+57.55 precedent) |
| Frontend reverse-projection from items→Record may lose information | Low | Items contain `limit` (resolved with override applied); reverse-projection seeds from `tenant.meta_data["quota_overrides"]` via PUT response OR from items where override differs from plan default; precise seed strategy: track explicit overrides separately or store via mutation response |
| RLS policy on tenants table (Sprint 57.50 Phase 58.x precedent) | Low | tenants table is global no-RLS (per Sprint 57.48 D-DAY0-3 + 53.7 §Risk Class C); UPDATE works via require_admin_platform_role auth |
| Pydantic Field validator pattern for `overrides` dict | Low | `field_validator` on `overrides` checks resource name whitelist; numeric coercion handled by `dict[str, float]` type |
| Vitest mutation test setup requires QueryClient wrapper | Low | Existing precedent in repo Sprint 57.54+57.55 verbatim mirror; reuse helper pattern |
| Agent delegation 2 sequential agents (backend then frontend) overhead vs 1 single | Low | Standard pattern (Sprint 57.49-57.55 precedent); type contract handoff between tracks: backend Pydantic shape → frontend TypeScript shape duplicated once, then frontend agent reads backend types from spec |
| BackendGapBanner copy change may break Vitest snapshot tests | Low | Grep existing snapshot tests for QuotasTab copy assertions Day 0 Prong 2; update if any |
| `medium-backend` 0.80 9th data point | Low | Per Sprint 57.55 retro Q4: 9th data point continues tracking; no class adjustment unless 3-sprint window pattern emerges |
| `medium-frontend` 0.65 6th data point — if also < 0.7 → 4+ consecutive < 0.7 lower-trigger persistent | Low | Confound resolved at tier-4 sub-class layer per Sprint 57.55 discipline; class baseline holds; AD-medium-frontend-Baseline-Recalibration continues (need consistent human-factor data) |
| QuotasTab RateLimits Card accidentally modified (scope creep) | Medium (QuotasTab renders both Cards combined) | Explicit scope guard in US-2 + AC-15; code-implementer agent prompt MUST scope edit to Usage quotas Card ONLY; verify via diff review post-Day-1 |
| `tenant.meta_data` write triggers existing GET test regression | Low | Refactor preserves Sprint 57.48 Track C behavior when overrides=None; existing 7 GET tests cover behavior; if test fails → revert helper extension signature, inline override merge in PUT instead |
| Audit chain ordering between commit + audit_log_append | Low | Sprint 57.3 PATCH tenant precedent established pattern; audit_log_append accepts AsyncSession + commits in same transaction as tenant update |

---

## 9. Carryover ADs (for Sprint 57.57+ pickup)

- **`AD-AgentFactor-Tier-4-Validation-Sprint-57.57`** (NEW CONDITIONAL — needed for 2nd validation under `mechanical-greenfield-design-decisions` 0.65; pending direction-of-drift from Sprint 57.56 1st data point)
- **`AD-AgentFactor-Tier-4-Structural-Action`** (CONDITIONAL NEW — IF Sprint 57.56+57.57 hits 2 consec > 1.20 → propose 0.65 → 0.80 lift; IF 2 consec < 0.7 → SPLIT was wrong direction → propose 0.65 → 0.45 tighten + reclassify Sprint 57.54+57.55 retroactively as `-port-style`)
- **`AD-Plan-Workload-AgentDelegation-Explicit-Field-Codification`** (Sprint 57.53+57.54+57.55 carryover — Sprint 57.56 = **3rd data point** under proposed mandatory rule; if Sprint 57.56 1st validation cleanly lands → promote to MANDATORY in `sprint-workflow.md §Workload Calibration §Four-segment form when agent_factor applies` per AD-Plan-2/3/4/5 promotion precedent)
- **`AD-Quotas-LiveUsageTracking-Phase58`** (NEW — Phase 58+ deeper extension; expose QuotaEnforcer Redis counters at admin layer for `current_usage` real value; out of Sprint 57.56 scope)
- **`AD-Quotas-UsageHistory-Phase58`** (NEW — Phase 58+ extension; per-resource usage history / trend chart UI; backend cron + storage)
- **`AD-Quotas-Alerting-Phase58`** (NEW — Phase 58+ extension; per-resource alerting thresholds + notification webhook)
- **`AD-Quotas-RequestIncrease-Workflow-Phase58`** (NEW — Phase 58+ extension; existing "Request increase" button is alert stub; backend endpoint + approval workflow)
- **`AD-Quotas-PlanUpgrade-AutoRollover-Phase58`** (NEW — Phase 58+ extension; override map invalidation logic on tenant plan change)
- **`AD-Quotas-OptimisticConcurrency`** (CONDITIONAL — if Day 1 surfaces concurrent edit race conditions; Phase 58+ If-Match header pattern)
- **`AD-TenantSettings-RateLimits-Write-Endpoint`** (Phase 58.x portfolio remaining; **last** WRITE-side AD; same mechanical-greenfield-design-decisions pattern as Sprint 57.54+57.55+57.56; Sprint 57.57 candidate following Option B "1 WRITE-side AD per sprint" cadence)
- **`AD-TenantSettings-Identity-Persistence-Phase58`** (Sprint 57.50 carryover continues; full SSO admin schema; broader scope than mechanical-greenfield)
- **`AD-Test-Cleanup-Pattern-Shared-Helper`** (Sprint 57.53+57.54+57.55 carryover continues; Phase 58.x — extract `_clear_committed_test_tenants` LIKE patterns to shared helper)
- **`AD-MediumBackend-AICadence-Recalibration`** (Sprint 57.53+57.54+57.55 carryover continues; Phase 58+ — revisit `medium-backend` 0.80 if next 2-3 human-factor sprints continue at 0.70-0.85)
- **`AD-Day0-Prong1-Test-Glob-Multi-Pattern`** (Sprint 57.54+57.55 carryover continues — codify multi-pattern test file glob in §Step 2.5 Prong 1 to avoid D-DAY0-1 `__tests__/` Glob false-negative repeat)
- **`AD-Phase58-Persistence-WriteSide-Pattern-Template`** (Sprint 57.54+57.55 carryover continues — pattern template reusable for RateLimits; if Sprint 57.57+ batches multiple → `mechanical-pattern-reuse-heavy` 0.30 candidate)
- **`AD-Day0-Prong2-Phase58-WriteSide-Resource-Storage-Grep`** (Sprint 57.55 carryover — Lesson 1 codification; Sprint 57.56 D-DAY0-A validates rule value)
- **`AD-Day0-Prong2-CanonicalService-Grep`** (Sprint 57.55 carryover — Lesson 2 codification; Sprint 57.56 D-DAY0-D **inverse** validates rule value — discovered NO canonical service exists, simpler direct ORM path)
- Potential NEW from Sprint 57.56 Day 0 三-prong findings

---

**Modification History**:
- 2026-05-27: Sprint 57.56 Day 0.2 — D-DAY0-A 🔴 RED resolved via user Option B (Recommended) Day 0 selection: tenant.meta_data["quota_overrides"] JSONB direct ORM write pattern (mirrors Sprint 57.48 RateLimits + Sprint 57.50 Identity precedent); architecturally simpler than 57.54+57.55 (NO canonical service extension); scope (workload / class / Sprint goal) UNCHANGED — see progress.md §Day 0 Option B decision
- 2026-05-27: Sprint 57.56 Day 0.1 — Initial draft (Quotas WRITE side Phase 58.x ship; mirror Sprint 57.55 structure verbatim; agent-delegated yes plan-time explicit field per Sprint 57.53+57.54+57.55 carryover AD; `mechanical-greenfield-design-decisions` 0.65 tier-4 1st validation under tier-4 sub-class table NEW Sprint 57.55 retro Q4 ACTIVATION; closes Sprint 57.55 carryover AD-AgentFactor-Tier-4-Validation-Sprint-57.56; Phase 58.x portfolio 3/4 item; tier-4 SPLIT 1st validation rollback rule baseline pending Sprint 57.57+ 2nd data point)
