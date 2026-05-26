# Sprint 57.55 — FeatureFlags Admin Write Endpoint + Frontend Edit Mode (Phase 58.x WRITE side)

**Phase**: 57+ Frontend SaaS / Phase 58.x portfolio (FeatureFlags WRITE-side ship; backend admin upsert + frontend edit mode)
**Goal**: Ship the Phase 58.x WRITE side for FeatureFlags — close the existing BackendGapBanner copy ("feature flag overrides edit API: backend extension Phase 58+") by adding `PUT /admin/tenants/{tenant_id}/feature-flags` overrides upsert endpoint + tenants.meta_data tenant_overrides JSONB write + frontend FeatureFlagsTab edit mode + useFeatureFlagsSave mutation hook. This is the **2nd validation data point** for tier-3 sub-class `mechanical-greenfield` 0.50 (closes Sprint 57.54 carryover `AD-AgentFactor-Tier-3-Validation-Sprint-57.55`; single NEW component-pair = 1 endpoint + 1 mutation hook + 1 tab edit mode following Sprint 57.54 HITLPolicies template).
**Branch**: `feature/sprint-57-55-feature-flags-write-endpoint`
**Class**: `medium-backend` 0.80 (7-data-point baseline post Sprint 57.54: 55.5=1.14 + 55.6=0.92 + 57.47=0.16 + 57.48=0.11 + 57.50=0.27 + 57.53=0.83 + 57.54≈1.0; 7-pt mean 0.63; KEEP per Sprint 57.50/57.53/57.54 retro `confound-resolved-by-sub-class-split` discipline — class baseline calibrates human-pace, agent residual captured at sub-class layer)
**Sub-class** (agent_factor): `mechanical-greenfield` 0.50 (**tier-3 2nd validation** under NEW table effective Sprint 57.53+ per Sprint 57.52 retro Q4 tier-3 SPLIT ACTIVATION; closes Sprint 57.54 carryover `AD-AgentFactor-Tier-3-Validation-Sprint-57.55`)
**Agent-delegated** (per AD-Plan-Workload-AgentDelegation-Explicit-Field NEW from Sprint 57.53; codification candidate per AD-Plan-Workload-AgentDelegation-Explicit-Field-Codification Sprint 57.54 carryover): **yes — backend + frontend via code-implementer agent delegation** (≥ 80% of Day 1 work; required to generate 2nd validation data point under `mechanical-greenfield` 0.50)
**Date**: 2026-05-26 (Sprint 57.54 closeout same-day continuation; main `1adba116` post PR #204 merge; Sprint 57.55 branch from main HEAD)
**Prior sprint reference**: Sprint 57.54 (closeout 2026-05-26; PR #204 merged main `1adba116`) generated `mechanical-greenfield` 0.50 1st validation data point with ratio ~1.37-2.0 ABOVE band by 0.17-0.8 → KEEP single-data-point caution. Sprint 57.55 = 2nd validation under same baseline → if also > 1.20 → **rollback rule MET (2 consec > 1.20)** → Sprint 57.55 retro Q4 propose 0.50 → 0.65 lift OR tier-4 sub-class split (`mechanical-greenfield-port-style` 0.45 vs `mechanical-greenfield-design-decisions` 0.65 per Sprint 57.54 retro CONDITIONAL `AD-Sub-Class-Greenfield-Port-vs-Design-Refinement`). If lands < 1.20 → reject rollback; if < 0.7 → 1st < 0.7 data point under 0.50 (single-data-point caution KEEP).

---

## 1. Sprint Goal

```
AS the project maintainer of the Phase 58.x SaaS portfolio (HITLPolicies
   shipped Sprint 57.54 / FeatureFlags / Quotas / RateLimits / Identity
   persistence ADs) AND the V2 calibration matrix maintainer with
   `mechanical-greenfield` 0.50 tier-3 sub-class table effective Sprint
   57.53+ but only ONE validation data point so far (Sprint 57.54 ratio
   ~1.37-2.0 ABOVE band; needs 2nd data point for rollback/keep decision)
I WANT the FeatureFlags WRITE-side gap closed (PUT overrides upsert
   endpoint + tenants.meta_data tenant_overrides JSONB write + Pydantic
   write schema + frontend edit mode + mutation hook + service func) —
   selected from Phase 58.x portfolio per user direction 2026-05-26
   Option B "ship one WRITE-side AD per sprint" — executed via code-
   implementer agent delegation (backend track + frontend track sequential)
   such that the sprint generates the SECOND validation data point for
   `mechanical-greenfield` 0.50 sub-class baseline
SO THAT (a) Sprint 57.54 carryover `AD-AgentFactor-Tier-3-Validation-
   Sprint-57.55` is closed with a clean 2nd validation data point under
   agent-delegated mode; (b) Sprint 57.55 retro Q4 either confirms keep
   0.50 (1 above + 1 below/in-band) OR triggers rollback rule (2 consec
   > 1.20 → propose 0.50 → 0.65 lift OR tier-4 sub-class split per
   Sprint 57.54 carryover CONDITIONAL `AD-Sub-Class-Greenfield-Port-vs-
   Design-Refinement`); (c) the existing BackendGapBanner copy in
   FeatureFlagsTab ("feature flag overrides edit API: backend extension
   Phase 58+") is softened to admit only deeper Phase 58+ gaps remain
   (registry CRUD / per-flag audit log); (d) Sprint 57.48 frontend tab
   migration (read-only) is extended into full read+write parity matching
   the Sprint 57.54 HITLPoliciesTab edit-mode pattern for tenant-settings
   admin UX consistency; (e) `medium-backend` 0.80 class gets its 8th
   data point continuing post-confound-resolution tracking (per Sprint
   57.50/57.53/57.54 retro discipline); (f) `medium-frontend` 0.65
   class gets its 4th data point (Sprint 57.13=0.95-1.0 / Sprint
   57.49=0.064 / Sprint 57.54≈0.32 frontend sub-portion / Sprint 57.55
   = TBD); if 4th < 0.7 → AD-medium-frontend-Baseline-Recalibration
   3-consec-below trigger condition tested; (g) Phase 58.x portfolio
   progresses from 3 open ADs (FeatureFlags/Quotas/RateLimits-Backend-
   Write) to 2 open (FeatureFlags WRITE side closed; Quotas + RateLimits
   remain as deferred ADs for Sprint 57.56+57.57)
```

## 2. Background & Context

### 2.1 FeatureFlags baseline state (verified Sprint 57.55 Day 0 Prong 2 content verify — 🔴 D-DAY0-B critical correction applied at Day 0)

**Sprint 57.55 Day 0 critical correction (D-DAY0-B 🔴 RED → resolved via D-DAY0-T pivot)**: Plan v1 incorrectly assumed per-tenant FeatureFlag overrides are stored in `tenants.meta_data["tenant_overrides"]` JSONB. **Reality**: per-tenant overrides live on `feature_flags.tenant_overrides[str(tenant_id)]` JSONB ON the global registry table itself (Sprint 56.1 US-4 architecture). See progress.md §Day 0 §Prong 2 D-DAY0-B for full evidence.

**Corrected baseline**:

- ✅ `backend/src/infrastructure/db/models/feature_flag.py::FeatureFlag` ORM model exists — global registry table (name VARCHAR(128) PK + default_enabled BOOLEAN NN + **tenant_overrides JSONB NN default={}** + description TEXT nullable + created_at/updated_at TIMESTAMPTZ with `onupdate=func.now()` auto-rotate)
- ✅ `feature_flags` table is **global no-RLS registry** (NOT per-tenant); per-tenant resolution via `feature_flags.tenant_overrides[str(tenant_id)]` JSONB key (NOT `tenants.meta_data`)
- ✅ `backend/src/api/v1/admin/tenants.py` L880-958 (Sprint 57.48 Track B) implements `GET /admin/tenants/{tenant_id}/feature-flags` — iterates global registry + reads `ff.tenant_overrides.get(tid_key)` per-flag → projects `FeatureFlagItem` (name / value / default_enabled / **overridden** [not "overridden_flag"] / description / updated_at) list
- ✅ **`backend/src/core/feature_flags.py::FeatureFlagsService` (Sprint 56.1 / US-4) IS the canonical setter** — `set_tenant_override(flag_name, tenant_id, enabled, actor_user_id)` auto-emits audit chain via `append_audit` helper (operation="feature_flag_override_set"); raises `FeatureFlagNotFoundError` if flag not in registry → maps cleanly to 422 unknown-flag (D-DAY0-T 🆕 NOTABLE)
- ✅ `frontend/src/features/tenant-settings/hooks/useFeatureFlags.ts` (Sprint 57.49) read hook with `FEATURE_FLAGS_QUERY_KEY_BASE = ["tenant-settings", "feature-flags"]`
- ✅ `frontend/src/features/tenant-settings/components/tabs/FeatureFlagsTab.tsx` (Sprint 57.49) reads + displays via the hook + `BackendGapBanner` copy: "Numeric flag overrides + per-tenant override write API: backend extension Phase 58+ — booleans shown are tenant-effective"
- ❌ NO `clear_tenant_override` method on FeatureFlagsService (Sprint 57.55 ADDS ~15-line method to support composite-replace clear semantics)
- ❌ NO `PUT /admin/tenants/{tenant_id}/feature-flags` endpoint (write side gap)
- ❌ NO `useFeatureFlagsSave` mutation hook on frontend

**Actual Sprint 57.55 scope** = the WRITE side referenced explicitly in the existing BackendGapBanner copy + clear_tenant_override service extension:

### 2.2 True Phase 58.x gap for FeatureFlags (post Day 0 D-DAY0-B + D-DAY0-T correction)

**Backend gaps** (Sprint 57.55 closes):
1. ❌ NEW `FeatureFlagsService.clear_tenant_override(flag_name, tenant_id, actor_user_id)` method (~15 lines; mirrors existing `set_tenant_override` audit-emit pattern; supports composite-replace clear semantics)
2. ❌ `PUT /admin/tenants/{tenant_id}/feature-flags` admin endpoint (loops payload.overrides + invokes `FeatureFlagsService.set_tenant_override` per entry; clears any prior tenant override NOT in payload via new `clear_tenant_override`)
3. ❌ `FeatureFlagOverridesUpsertRequest` Pydantic write schema (composite `overrides: dict[str, bool]`)
4. ❌ Pytest tests covering upsert/multi-tenant isolation/unknown flag rejection (422 via FeatureFlagNotFoundError)/composite-replace clear behavior/audit chain emit verification/idempotency

**Frontend gaps** (Sprint 57.55 closes):
1. ❌ `saveFeatureFlagOverrides(tenantId, payload)` service func
2. ❌ `useFeatureFlagsSave(tenantId)` TanStack mutation hook (with invalidation of `FEATURE_FLAGS_QUERY_KEY_BASE`)
3. ❌ `FeatureFlagsTab` edit-mode toggle (Edit/Cancel/Save buttons + per-row Switch override + "clear override" button to revert to default)
4. ❌ Vitest tests (mutation hook + tab edit mode)
5. ❌ BackendGapBanner copy soften (remove "edit API" — only registry CRUD + per-flag audit log remain Phase 58+)

**Deferred (REMAINS Phase 58+)**:
- ❌ Registry CRUD (create/delete feature flag definitions) — separate broader scope; NOT in this sprint
- ✅ Per-flag audit log entry on override change — **ALREADY IMPLEMENTED** via `FeatureFlagsService.set_tenant_override` + `append_audit` helper (Sprint 56.1); D-DAY0-T finding makes this a positive scope side-effect (REMOVED from carryover as `AD-FeatureFlags-PerFlag-AuditLog-Phase58` no longer needed)
- ❌ Numeric flag overrides (mockup fixture supports `ctl: "num"` but registry only has boolean) — Phase 58+ extension
- ❌ Per-flag audit log filtering UI (entries are persisted; filtering by flag_name in `/audit-log` page is separate scope) — Phase 58+
- ❌ Per-flag rollout schedule / canary policy — Phase 58+ extension
- ❌ Optimistic concurrency / If-Match (Sprint 57.50 Identity Phase 58.x precedent — also deferred)

### 2.3 Why `mechanical-greenfield` 0.50 2nd validation (NOT pattern-reuse-heavy 0.30)

Per Sprint 57.50 retro Q4 ESCALATION decision + `sprint-workflow.md §Active Agent Delegation Factor Modifier` tier-2 sub-class table + Sprint 57.52 retro Q4 tier-3 SPLIT:

| Sub-class | Trigger | Sprint 57.55 fit? |
|-----------|---------|--------------------|
| `mechanical-pattern-reuse-heavy` 0.30 | ≥ 4 mechanical repetitions of same template in 1 sprint | ❌ Sprint 57.55 = 1 NEW endpoint pair + 1 NEW mutation hook + 1 tab edit mode (counts as 1 component-pair, not 4) |
| **`mechanical-greenfield` 0.50** | Single NEW component-pair; < 4 mechanical repetitions | ✅ MATCH — mirrors Sprint 57.54 shape exactly |
| `mixed-multidomain-bundle-mechanical` 0.65 | 3+ independent tracks WITH mechanical pattern reuse | ❌ Sprint 57.55 = single FeatureFlags domain |
| `mixed-multidomain-bundle-non-mechanical` 1.0 | 3+ independent tracks; pure audit/docs/rules | ❌ |

**2nd validation prediction**:
- Sprint 57.54 1st data point = ratio ~1.37-2.0 ABOVE band by 0.17-0.8 (greenfield design decisions ~2× speedup vs port ~5×)
- Sprint 57.55 = same shape (single new endpoint + hook + tab edit mode) BUT pattern-reuse from Sprint 57.54 internalized → predicted faster (~3× speedup vs Sprint 57.54's ~2×)
- Predicted actual ratio: **~1.0-1.5 IN/ABOVE band lower-middle** (pattern-reuse acceleration applies; Sprint 57.54 template internalized)
- **Decision matrix at Sprint 57.55 retro Q4**:
  - If lands > 1.20 → **2 consec > 1.20 = rollback rule MET** → propose 0.50 → 0.65 lift (matches Sprint 57.54 root cause hypothesis: greenfield design >> port) OR tier-4 sub-class split per Sprint 57.54 CONDITIONAL `AD-Sub-Class-Greenfield-Port-vs-Design-Refinement` (split `mechanical-greenfield-port-style` 0.45 vs `mechanical-greenfield-design-decisions` 0.65)
  - If lands 0.85-1.20 (IN band) → **rollback rule NOT met** (1 above + 1 in-band) → KEEP 0.50; flag Sprint 57.56+ 3rd data point
  - If lands < 0.7 → 1st < 0.7 data point under 0.50 (single-data-point caution KEEP); flag Sprint 57.56+ direction

### 2.4 Pattern-reuse capture (Sprint 57.54 HITLPolicies WRITE precedent)

Sprint 57.54 established the WRITE-side template:
- `PUT /admin/tenants/{tenant_id}/<resource>` upsert endpoint
- Pydantic `<Resource>UpsertRequest` with `extra="forbid"` + `field_validator`
- Pydantic `<Resource>UpsertResponse` echoing saved composite + projected items
- `DBStore.put()` upsert via `pg_insert.on_conflict_do_update` (1st usage in repo D-DAY0-13 NOTABLE)
- `useResourceSave` TanStack mutation hook (mirror `useTenantSettingsSave` Sprint 57.9)
- Tab edit mode: editing state + draft state + Edit/Cancel/Save buttons + per-row form + reverse-projection items→composite draft seed + BackendGapBanner copy soften
- conftest.py `<RESOURCE>_PUT_%` LIKE sweep extension (mirrors Sprint 57.12 + 57.53 §Committed-Row Cleanup Pattern)

Sprint 57.55 mirrors the WRITE-side template with the FeatureFlags-specific twist: instead of dedicated table+RLS+ON CONFLICT, the override map lives inside `tenants.meta_data` JSONB → simpler write path (single UPDATE on existing tenants row; no separate store class), but field validation different (per-flag name lookup against global registry).

### 2.5 Sprint 57.54 carryover chain (`AD-AgentFactor-Tier-3-Validation-Sprint-57.55`)

- Sprint 57.52 retro Q4 (2026-05-26): tier-3 SPLIT ACTIVATED — `mixed-multidomain-bundle-mechanical` 0.65 + `mixed-multidomain-bundle-non-mechanical` 1.0
- Sprint 57.53 was first sprint under new tier-3 sub-class table effective Sprint 57.53+ — parent-assistant-direct execution (`agent_factor = 1.0`); 1st validation NOT generated → carryover renamed Sprint 57.54
- Sprint 57.54 generated `mechanical-greenfield` 0.50 1st validation data point: ratio ~1.37-2.0 ABOVE band by 0.17-0.8 → KEEP single-data-point caution; flag Sprint 57.55+ for 2nd validation
- Sprint 57.55 = mandated agent-delegated mode to deliver the 2nd validation data point

### 2.6 Class baseline tracking continuation

- `medium-backend` 0.80: Sprint 57.54 was 7th data point (ratio ~1.0 IN BAND middle; 7-pt mean 0.63; last 3 only 1/3 < 0.7 lower-trigger NOT MET; KEEP per Sprint 57.54 retro Q4). Sprint 57.55 = 8th data point continuing post-confound-resolution tracking.
- `medium-frontend` 0.65: Sprint 57.54 was 3rd data point (Sprint 57.13≈0.95-1.0 / 57.49=0.064 / 57.54≈0.32 frontend sub-portion; 3-pt mean ~0.42 below band edge; 3-sprint window evaluation in progress per Sprint 57.54 retro Q4 — last 3 only 2 of 3 < 0.7 lower-trigger NOT yet MET). Sprint 57.55 frontend portion = 4th data point. If 4th continues < 0.7 → **3+ consecutive < 0.7** = lower-trigger MET → propose 0.65 → 0.50 lift in Sprint 57.55 retro Q4 (parallel Sprint 57.48 Option B activation).

---

## 3. User Stories

### US-1: Backend WRITE side — PUT overrides endpoint + tenants.meta_data write

```
AS the V2 backend developer extending the existing Sprint 57.48 FeatureFlags
   admin API surface (read-only) to support per-tenant feature-flag override
   write
I WANT the WRITE side for `tenants.meta_data["tenant_overrides"]` JSONB +
   `PUT /admin/tenants/{tenant_id}/feature-flags` upsert endpoint +
   Pydantic `FeatureFlagOverridesUpsertRequest` write schema implemented +
   integration tests covering all critical paths (auth/404/upsert-create/
   upsert-update/multi-tenant isolation/unknown flag rejection/empty
   overrides/idempotency)
SO THAT admin operators can configure per-tenant FeatureFlag overrides
   programmatically + the frontend FeatureFlagsTab can ship edit mode in
   US-2 without backend gap.
```

**Acceptance**:
- WRITE path uses direct `UPDATE tenants SET meta_data = jsonb_set(...)` OR equivalent SQLAlchemy `ORMQuery.update(meta_data=...)` — composite override map written atomically; rotates `tenants.updated_at` server-side
- `FeatureFlagOverridesUpsertRequest` Pydantic model with composite shape (single field `overrides: dict[str, bool]`)
- `PUT /admin/tenants/{tenant_id}/feature-flags` endpoint returns 200 OK with `FeatureFlagOverridesUpsertResponse` (echoes saved composite + projected `items` list matching GET shape)
- Endpoint uses `Depends(require_admin_platform_role)` (matches existing GET endpoint per `tenants.py:919`)
- Endpoint uses `_load_tenant_or_404` for 404 path consistency
- Unknown flag names rejected with 422 (cross-check against global `FeatureFlag` registry; OR per-validator-time enum-style check IF acceptable cost; OR document acceptance behavior — decision point Day 1)
- Pytest 10-12 NEW tests added in `backend/tests/integration/api/test_admin_tenant_feature_flags.py` (extend existing Sprint 57.48 file):
  - `test_put_requires_admin_role` (401/403)
  - `test_put_tenant_not_found` (404)
  - `test_put_creates_new_overrides` (200; no prior overrides in meta_data)
  - `test_put_updates_existing_overrides` (200; prior overrides, new map replaces)
  - `test_put_response_projects_items_matching_get` (response.items echoes GET shape)
  - `test_put_unknown_flag_rejected` (422; flag name not in global registry)
  - `test_put_extra_field_rejected` (422; payload with non-`overrides` field)
  - `test_put_multi_tenant_isolation` (tenant_b PUT does NOT affect tenant_a row)
  - `test_put_empty_overrides_clears_all` (200; PUT with `{}` clears all per-tenant overrides → resolved_value reverts to default_enabled)
  - `test_put_idempotent_same_payload_twice` (PUT twice same payload → consistent state; updated_at rotates as expected)
  - `test_put_persists_to_db_via_subsequent_get` (post-PUT GET reflects new resolved_value across all flag rows)
- Pytest count delta: +10 to +12 (current 1772 PASS → 1782-1784 PASS); 0 fail; 0 skip change

### US-2: Frontend WRITE side — useFeatureFlagsSave + FeatureFlagsTab edit mode

```
AS the V2 frontend developer extending the Sprint 57.49 FeatureFlagsTab
   (read-only display) to support inline edit mode matching the Sprint 57.54
   HITLPoliciesTab edit-mode pattern for tenant-settings admin UX
   consistency
I WANT a NEW `useFeatureFlagsSave(tenantId)` TanStack mutation hook +
   `saveFeatureFlagOverrides` service func + edit-mode UI on FeatureFlagsTab
   (Edit/Cancel/Save buttons + per-row Switch override + "clear" button to
   remove explicit override + reverse-projection items→composite draft seed)
   + Vitest tests covering mutation success/error/cache invalidation
SO THAT the BackendGapBanner copy can be softened (only registry CRUD +
   per-flag audit log remain Phase 58+, edit API now real-backed).
```

**Acceptance**:
- `frontend/src/features/tenant-settings/services/tenantSettingsService.ts` — NEW `saveFeatureFlagOverrides(tenantId, payload)` async func using `fetchWithAuth` PUT; matches existing `fetchFeatureFlags` / `saveHITLPolicies` patterns
- `frontend/src/features/tenant-settings/types.ts` — NEW types `FeatureFlagOverridesUpsertRequest` + `FeatureFlagOverridesUpsertResponse` (type module-level per Sprint 57.54 D-DAY1-2 precedent; NOT inline in service)
- `frontend/src/features/tenant-settings/hooks/useFeatureFlagsSave.ts` — NEW TanStack `useMutation` hook with `onSuccess` invalidation of `FEATURE_FLAGS_QUERY_KEY_BASE` (re-fetches GET); error propagation via existing pattern (mirror `useHITLPoliciesSave` Sprint 57.54)
- `frontend/src/features/tenant-settings/components/tabs/FeatureFlagsTab.tsx` — edit mode:
  - State: `editing: boolean` + `draft: Record<string, bool>` (composite shape mirroring write schema; seeded by reverse-projection from items where `overridden_flag === true`)
  - Edit button: top-right of Card, toggles `editing`
  - Edit form: per-row Switch override + "clear" button to remove explicit override (sets that flag to undefined in draft → omitted from payload)
  - Save / Cancel buttons: Save calls mutation, Cancel reverts draft + exits edit mode
  - Success → exits edit mode + invalidates FEATURE_FLAGS_QUERY_KEY_BASE
  - Error → keeps form open + shows error message
  - **Mockup-fidelity discipline**: 0 NEW hex/oklch literals (reuse existing `--info`/`--warning`/`--success`/`--danger` tokens via `Badge` + buttons via `--btn-primary` pattern from existing tabs and Sprint 57.54 HITLPoliciesTab)
- BackendGapBanner copy update: from "Feature flag overrides edit API: backend extension Phase 58+ — flags shown are tenant-effective resolved values" → "Feature flag registry CRUD + per-flag audit log: backend extension Phase 58+ — flags shown are tenant-effective + editable via Edit button"
- Vitest 5-8 NEW tests added across:
  - `frontend/tests/unit/tenant-settings/useFeatureFlagsSave.test.tsx` (NEW file; mutation success → invalidates QUERY_KEY / mutation error → propagates error / payload shape)
  - `frontend/tests/unit/tenant-settings/tabs/FeatureFlagsTab.test.tsx` (extend; new edit-mode tests + banner copy assertion update)
  - `frontend/tests/unit/tenant-settings/tenantSettingsService.test.ts` (extend; saveFeatureFlagOverrides PUT shape + URL + body)
- Vitest count delta: +5 to +8 (current 617 PASS → 622-625 PASS); 0 fail; 0 skip change

### US-3: AD-Plan-Workload-AgentDelegation-Explicit-Field-Codification (CONDITIONAL on Sprint 57.55 validation success)

Sprint 57.53 retro Q5 carried `AD-Plan-Workload-AgentDelegation-Explicit-Field` (codify sprint plan §6 pre-commit "agent-delegated: yes/no/partial/TBD-Day-1-decision" field). Sprint 57.54 plan + this Sprint 57.55 plan both explicitly fill this field.

**This sprint validates the codification value for the 2nd time** (Plan-time agent-delegation explicit field, 2 data points). If Sprint 57.55 1st validation succeeds (2nd data point cleanly landed regardless of direction), Sprint 57.55 retro Q5 can promote the rule edit to `sprint-workflow.md §Workload Calibration §Four-segment form when agent_factor applies` as MANDATORY field.

**Acceptance** (this sprint):
- Plan §Workload 4-segment form contains explicit "Agent-delegated: yes" line
- Day 1 retrospective Q2 records actual delegation mode (confirm `yes` vs reclassify `partial` if any track diverges)
- IF Sprint 57.55 1st validation cleanly lands → propose Sprint 57.56+ codification edit (defer the edit itself; allow 1 more sprint to confirm)

---

## 4. Technical Specification

### 4.1 Backend Track — FeatureFlagsService.set/clear_tenant_override loop (D-DAY0-T pivot path)

**Pivot rationale** (D-DAY0-B 🔴 RED + D-DAY0-T 🆕 NOTABLE): per-tenant FeatureFlag overrides live on `feature_flags.tenant_overrides[str(tenant_id)]` JSONB (NOT `tenants.meta_data`); `core/feature_flags.py::FeatureFlagsService.set_tenant_override` (Sprint 56.1 / US-4) is the canonical setter and auto-emits audit chain via `append_audit`. Sprint 57.55 backend uses this canonical service rather than raw SQL — cleaner V2 architecture + audit chain auto-emit is positive scope side-effect.

**File 1**: `backend/src/core/feature_flags.py` (extend; NEW `clear_tenant_override` method ~15 lines mirroring existing `set_tenant_override` audit-emit pattern)

```python
async def clear_tenant_override(
    self,
    flag_name: str,
    tenant_id: UUID,
    actor_user_id: UUID | None = None,
) -> None:
    """Remove per-tenant override (revert to default_enabled) + emit audit entry."""
    flag = await self._load(flag_name)
    if flag is None:
        raise FeatureFlagNotFoundError(
            f"flag '{flag_name}' not in registry; cannot clear unknown flag"
        )
    if str(tenant_id) not in flag.tenant_overrides:
        return  # idempotent no-op
    previous = flag.tenant_overrides[str(tenant_id)]
    new_overrides = dict(flag.tenant_overrides)
    del new_overrides[str(tenant_id)]
    flag.tenant_overrides = new_overrides

    await append_audit(
        self._session,
        tenant_id=tenant_id,
        user_id=actor_user_id,
        operation="feature_flag_override_cleared",
        resource_type="feature_flag",
        resource_id=flag_name,
        operation_data={
            "flag_name": flag_name,
            "tenant_id": str(tenant_id),
            "previous_override": previous,
        },
        operation_result="success",
    )

    await self._session.flush()
    keys_to_drop = [k for k in self._resolved_cache if k[0] == flag_name]
    for k in keys_to_drop:
        self._resolved_cache.pop(k, None)
```

**File 2**: `backend/src/api/v1/admin/tenants.py` (extend; ~80 lines added after Sprint 57.48 Track B GET endpoint at L958)

```python
class FeatureFlagOverridesUpsertRequest(BaseModel):
    """Composite FeatureFlag overrides upsert payload (composite-replace semantics)."""

    model_config = ConfigDict(extra="forbid")
    overrides: dict[str, bool] = Field(
        default_factory=dict,
        description=(
            "Map of flag name → override value (bool). "
            "Composite-replace semantics: flags NOT in payload but currently overridden "
            "for this tenant are cleared (reverts to default_enabled)."
        ),
    )


class FeatureFlagOverridesUpsertResponse(BaseModel):
    """Echoes saved composite + projects items list for cache hydration."""

    saved_overrides: dict[str, bool]
    items: list[FeatureFlagItem]


@router.put(
    "/{tenant_id}/feature-flags",
    response_model=FeatureFlagOverridesUpsertResponse,
    dependencies=[Depends(require_admin_platform_role)],
)
async def upsert_tenant_feature_flag_overrides(
    tenant_id: UUID,
    payload: FeatureFlagOverridesUpsertRequest,
    db: AsyncSession = Depends(get_db_session),
) -> FeatureFlagOverridesUpsertResponse:
    """Upsert per-tenant FeatureFlag overrides into feature_flags.tenant_overrides JSONB.

    Composite-replace semantics: payload.overrides represents the COMPLETE desired
    override state for this tenant. Any flag with a current tenant override that is
    NOT in payload.overrides will be CLEARED (reverts to default_enabled).

    - 401/403 via require_admin_platform_role
    - 404 via _load_tenant_or_404
    - 422 if any override key not in global FeatureFlag registry
    - 200 with response.saved_overrides + response.items (projected for cache hydration)
    - Audit chain entries auto-emitted by FeatureFlagsService.set_tenant_override
      and FeatureFlagsService.clear_tenant_override (Sprint 56.1 / US-4 invariant)
    """
    await _load_tenant_or_404(db, tenant_id)

    # Pre-validate all payload keys against global registry (single SELECT)
    all_flags_stmt = select(FeatureFlag)
    all_flags = (await db.execute(all_flags_stmt)).scalars().all()
    known = {ff.name for ff in all_flags}
    unknown = set(payload.overrides.keys()) - known
    if unknown:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown feature flag(s): {sorted(unknown)}",
        )

    service = get_feature_flags_service(db)
    tid_str = str(tenant_id)

    # SET: each flag in payload → set_tenant_override (audit emit handled)
    for flag_name, value in payload.overrides.items():
        await service.set_tenant_override(
            flag_name, tenant_id, value, actor_user_id=None
        )

    # CLEAR: each flag NOT in payload with a current tenant override → clear
    for ff in all_flags:
        if ff.name not in payload.overrides and tid_str in (ff.tenant_overrides or {}):
            await service.clear_tenant_override(
                ff.name, tenant_id, actor_user_id=None
            )

    await db.commit()

    # Re-fetch + project items (cache hydration consistency with GET)
    items = await _project_feature_flags_for_tenant(db, tenant_id)
    return FeatureFlagOverridesUpsertResponse(
        saved_overrides=payload.overrides,
        items=items,
    )
```

**Helper extraction** (NEW): `_project_feature_flags_for_tenant(db, tenant_id) -> list[FeatureFlagItem]` extracted from Sprint 57.48 Track B GET endpoint body (DRY refactor — refactor existing GET to call helper, reuse in PUT response). Helper takes `tenant_id: UUID` (not `tenant` ORM row) so post-commit re-fetch path works cleanly. Acceptable scope expansion: ~30 lines net refactor + ~80 lines NEW WRITE side = ~110 line edit on admin/tenants.py + ~15 lines on core/feature_flags.py = **~125 lines total backend code**.

### 4.2 Backend Track — Pytest tests

**File**: `backend/tests/integration/api/test_admin_tenant_feature_flags.py` (extend existing Sprint 57.48 file)

Add 10-12 NEW tests after the existing GET tests (which already establish auth/404/multi-tenant patterns; reuse fixtures verbatim).

**File**: `backend/tests/integration/api/conftest.py` (extend `_clear_committed_test_tenants` LIKE sweep)

Add `FF_PUT_%` LIKE prefix to the existing `_clear_committed_test_tenants()` cleanup sweep (mirrors Sprint 57.54 `HITL_PUT_%` extension; parallels Sprint 57.12 + 57.53 §Committed-Row Cleanup Pattern).

### 4.3 Frontend Track — Types module

**File**: `frontend/src/features/tenant-settings/types.ts` (extend)

```typescript
export interface FeatureFlagOverridesUpsertRequest {
  overrides: Record<string, boolean>;
}

export interface FeatureFlagOverridesUpsertResponse {
  saved_overrides: Record<string, boolean>;
  items: FeatureFlagItem[];
}
```

### 4.4 Frontend Track — Service func

**File**: `frontend/src/features/tenant-settings/services/tenantSettingsService.ts` (extend)

```typescript
export async function saveFeatureFlagOverrides(
  tenantId: string,
  payload: FeatureFlagOverridesUpsertRequest,
  signal?: AbortSignal
): Promise<FeatureFlagOverridesUpsertResponse> {
  return fetchWithAuth<FeatureFlagOverridesUpsertResponse>(
    `/api/v1/admin/tenants/${tenantId}/feature-flags`,
    { method: "PUT", body: JSON.stringify(payload), signal }
  );
}
```

### 4.5 Frontend Track — Mutation hook

**File**: `frontend/src/features/tenant-settings/hooks/useFeatureFlagsSave.ts` (NEW; mirror `useHITLPoliciesSave.ts` Sprint 57.54 verbatim)

```typescript
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { saveFeatureFlagOverrides } from "../services/tenantSettingsService";
import type {
  FeatureFlagOverridesUpsertRequest,
  FeatureFlagOverridesUpsertResponse,
} from "../types";
import { FEATURE_FLAGS_QUERY_KEY_BASE } from "./useFeatureFlags";

export function useFeatureFlagsSave(tenantId: string) {
  const queryClient = useQueryClient();
  return useMutation<
    FeatureFlagOverridesUpsertResponse,
    Error,
    FeatureFlagOverridesUpsertRequest
  >({
    mutationFn: (payload) => saveFeatureFlagOverrides(tenantId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: [...FEATURE_FLAGS_QUERY_KEY_BASE, tenantId],
      });
    },
  });
}
```

### 4.6 Frontend Track — FeatureFlagsTab edit mode

**File**: `frontend/src/features/tenant-settings/components/tabs/FeatureFlagsTab.tsx` (edit)

Edit mode adds:
- State: `const [editing, setEditing] = useState(false); const [draft, setDraft] = useState<Record<string, boolean>>(seedFromItems);`
- Edit toggle button (top-right of Card header area)
- Form: per-row Switch override + "clear override" button (sets that flag to undefined in draft → omitted from payload)
- Save → call mutation; Cancel → reset draft + exit
- BackendGapBanner copy soften

### 4.7 Verification

- `cd backend && pytest tests/integration/api/test_admin_tenant_feature_flags.py -v` → all PASS (existing + 10-12 NEW)
- `cd backend && pytest --tb=short -q` → 1782-1784 PASS + 0 fail
- `cd backend && mypy --strict src/` → 0 errors
- `python scripts/lint/run_all.py` → 9/9 GREEN
- `cd frontend && npm run lint && npm run build` → exit 0 / 0 ESLint / 0 tsc errors (NOT `--silent` per AD-Pre-Push-Lint-Silent-Suppression-Anti-Pattern)
- `cd frontend && npm run test` → 622-625 PASS
- LLM SDK leak scan → 0

---

## 5. File Change List

### Backend (NEW + EDIT)
- **EDIT**: `backend/src/core/feature_flags.py` — add `clear_tenant_override` method to FeatureFlagsService (~15 lines; mirrors existing `set_tenant_override` audit-emit pattern; D-DAY0-T pivot)
- **EDIT**: `backend/src/api/v1/admin/tenants.py` — add `FeatureFlagOverridesUpsertRequest` + `FeatureFlagOverridesUpsertResponse` + `upsert_tenant_feature_flag_overrides` endpoint + extract `_project_feature_flags_for_tenant(db, tenant_id)` helper (DRY refactor of Sprint 57.48 GET body) (~110 lines net)
- **EDIT**: `backend/tests/integration/api/test_admin_tenant_feature_flags.py` — add 10-12 NEW PUT tests (~250 lines)
- **EDIT**: `backend/tests/integration/api/conftest.py` — add `FF_PUT_%` LIKE sweep (~1 line addition to existing `_clear_committed_test_tenants`)

### Frontend (NEW + EDIT)
- **EDIT**: `frontend/src/features/tenant-settings/types.ts` — add `FeatureFlagOverridesUpsertRequest` + `FeatureFlagOverridesUpsertResponse` types (~10 lines)
- **EDIT**: `frontend/src/features/tenant-settings/services/tenantSettingsService.ts` — add `saveFeatureFlagOverrides` service func (~15 lines)
- **NEW**: `frontend/src/features/tenant-settings/hooks/useFeatureFlagsSave.ts` — mutation hook (~40 lines incl. full header)
- **EDIT**: `frontend/src/features/tenant-settings/components/tabs/FeatureFlagsTab.tsx` — add edit mode (~150 lines added; soften BackendGapBanner copy)
- **NEW**: `frontend/tests/unit/tenant-settings/useFeatureFlagsSave.test.tsx` — mutation hook Vitest tests (~75 lines)
- **EDIT**: `frontend/tests/unit/tenant-settings/tabs/FeatureFlagsTab.test.tsx` — extend with edit-mode tests + banner copy assertion update (~120 lines added if file exists, else NEW)
- **EDIT**: `frontend/tests/unit/tenant-settings/tenantSettingsService.test.ts` — extend with saveFeatureFlagOverrides test (~35 lines)

### Sprint artifacts (Day 0 + Day 2)
- `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-55-plan.md` (this file)
- `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-55-checklist.md`
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-55/progress.md`
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-55/retrospective.md`
- `memory/project_phase57_55_feature_flags_write_endpoint.md`
- `memory/MEMORY.md` (pointer entry)
- `claudedocs/1-planning/next-phase-candidates.md` (Sprint 57.55 closeout note)
- `CLAUDE.md` (Current Sprint row + Last Updated footer)
- `.claude/rules/sprint-workflow.md` (matrix +1 row data point for `mechanical-greenfield` 0.50 2nd validation + `medium-backend` 0.80 8th + `medium-frontend` 0.65 4th + §Active block 2nd validation entry; tier-4 sub-class refinement CONDITIONAL on rollback rule outcome)
- `claudedocs/4-changes/feature-changes/CHANGE-025-feature-flags-write-endpoint.md` (NEW — per CLAUDE.md `4-changes/` convention)

---

## 6. Workload

**Bottom-up est**: ~3.5 hr
- Day 0 三-prong (Prong 1 path verify on admin/tenants.py + frontend tab/hook/service paths; Prong 2 content verify on baseline ALREADY DONE in this plan §2.1; Prong 3 schema verify on feature_flags registry + tenants.meta_data JSONB shape): ~0.3 hr
- Day 1 Backend track (PUT endpoint + Pydantic + helper extract + ~10-12 pytest tests, agent-delegated via code-implementer; faster than Sprint 57.54 by ~15-20% due to template internalization): ~1.3 hr human-equivalent
- Day 1 Frontend track (types + service func + mutation hook + tab edit mode + ~5-8 Vitest tests + BackendGapBanner copy soften, agent-delegated via code-implementer; faster than Sprint 57.54 by ~15-20% due to template internalization): ~1.2 hr human-equivalent
- Day 2 closeout (progress + retro + memory + sprint-workflow.md matrix + CLAUDE.md + next-phase-candidates + CHANGE-025 + commit + PR): ~0.4 hr (lighter than Sprint 57.54 since rollback rule decision Q4 work is structural-action-conditional)

**Class-calibrated commit** (`medium-backend` 0.80):
- 3.5 × 0.80 = **~2.8 hr committed (~168 min)**

**Agent-adjusted commit** (`agent_factor = 0.50` tier-3 `mechanical-greenfield` — **2nd validation**):
- 2.8 × 0.50 = **~1.4 hr agent-adjusted (~84 min)**

**4-segment form**:
> Bottom-up est ~3.5 hr → class-calibrated commit ~2.8 hr (mult 0.80) → agent-adjusted commit ~1.4 hr (agent_factor 0.50 tier-3 `mechanical-greenfield` — **2nd validation under tier-3 table** effective Sprint 57.53+)
> **Agent-delegated**: **yes** — backend + frontend via code-implementer agent delegation (sequential: backend first, then frontend with backend types confirmed; mirror Sprint 57.54 sequence)

**2nd validation prediction (tier-3 `mechanical-greenfield` 0.50)**:
- Single component-pair (1 backend endpoint + 1 frontend mutation hook + 1 tab edit-mode) cleanly scoped; agent-delegated pattern from Sprint 57.49-57.54 internalized (16th-17th consecutive frontend agent)
- **Pattern-reuse acceleration vs Sprint 57.54**: Sprint 57.54 had `pg_insert.on_conflict_do_update` 1st usage learning curve (D-DAY0-13); Sprint 57.55 has simpler JSONB merge (no NEW SQLAlchemy pattern); expect ~15-20% faster than Sprint 57.54 baseline
- Expected actual ~45-60 min wall-clock total (backend ~5-8 min agent + frontend ~5-8 min agent + supervisory ~10 min + Day 0 ~15 min + Day 2 closeout ~15-20 min)
- Predicted ratio actual/committed-with-agent-factor: **~1.0-1.5** (likely ABOVE band lower-middle due to greenfield design decisions pattern; Sprint 57.54 was 1.37-2.0 above)
- **Decision matrix at Sprint 57.55 retro Q4**:
  - If lands > 1.20 → **2 consec > 1.20 = rollback rule MET** → propose 0.50 → 0.65 lift (matches Sprint 57.54 root cause: greenfield design >> port) OR tier-4 sub-class split per Sprint 57.54 CONDITIONAL `AD-Sub-Class-Greenfield-Port-vs-Design-Refinement`
  - If lands 0.85-1.20 (IN band) → **rollback rule NOT met** (1 above + 1 in-band; 1 + 1 different directions) → KEEP 0.50; flag Sprint 57.56+ 3rd data point
  - If lands < 0.7 → 1st < 0.7 data point under 0.50 (single-data-point caution KEEP); flag Sprint 57.56+ direction tracking

---

## 7. Acceptance Criteria

| # | Criterion | Verify |
|---|---|---|
| AC-1 | `upsert_tenant_feature_flag_overrides` endpoint declared with `@router.put("/{tenant_id}/feature-flags", ...)` | grep `@router.put.*feature-flags` in admin/tenants.py |
| AC-2 | Pydantic `FeatureFlagOverridesUpsertRequest` + `FeatureFlagOverridesUpsertResponse` declared + `extra="forbid"` set | grep models in admin/tenants.py |
| AC-3 | Unknown flag names rejected with 422 (cross-check against global FeatureFlag registry) | pytest `test_put_unknown_flag_rejected` |
| AC-4 | Multi-tenant isolation guarded (tenant_b PUT does not affect tenant_a) | pytest `test_put_multi_tenant_isolation` |
| AC-5 | Empty overrides clears all per-tenant overrides | pytest `test_put_empty_overrides_clears_all` |
| AC-6 | `_project_feature_flags_for_tenant` helper extracted; GET refactored to use it; PUT reuses it for response.items | grep helper invocations in admin/tenants.py |
| AC-7 | Pytest count delta +10 to +12 | `pytest --tb=short -q` count = 1782-1784 |
| AC-8 | Full backend pytest baseline ALL-GREEN | `pytest --tb=short -q` 0 fail |
| AC-9 | mypy --strict 0 errors | `mypy --strict src/` |
| AC-10 | 9 V2 lints preserved | `python scripts/lint/run_all.py` exit 0 |
| AC-11 | LLM SDK leak 0 | covered by `run_all.py` |
| AC-12 | NEW `saveFeatureFlagOverrides` service func + `useFeatureFlagsSave` mutation hook implemented | grep files |
| AC-13 | FeatureFlagsTab edit-mode UI (Edit/Cancel/Save + per-row Switch + clear button) functional | manual smoke + Vitest tab tests |
| AC-14 | BackendGapBanner copy softened (remove "edit API"; only registry CRUD + per-flag audit log remain Phase 58+) | grep BackendGapBanner text |
| AC-15 | Vitest count delta +5 to +8 | `npm run test` count = 622-625 |
| AC-16 | Vite build clean | `npm run build` exit 0 |
| AC-17 | tsc strict 0 errors | covered by `npm run build` |
| AC-18 | ESLint 0 errors | `npm run lint` (NOT `--silent`) |
| AC-19 | File MHist updated on edited files (≤100 char budget per AD-Lint-MHist-Verbosity) | grep MHist lines |
| AC-20 | Day 0 三-prong report logged with drift findings | Read progress.md Day 0 |
| AC-21 | retrospective.md Q1-Q6 with **2nd validation `mechanical-greenfield` 0.50 ratio + rollback rule decision** in Q4 + agent-delegation confirmed in Q2 | grep Q2 + Q4 |
| AC-22 | sprint-workflow.md MHist + matrix `medium-backend` 0.80 8th data point + `medium-frontend` 0.65 4th data point + §Active block `mechanical-greenfield` 0.50 2nd validation entry with rollback rule outcome | grep |
| AC-23 | CHANGE-025-feature-flags-write-endpoint.md created | Read claudedocs/4-changes/feature-changes/ |
| AC-24 | conftest.py `FF_PUT_%` LIKE sweep added (mirrors Sprint 57.54 `HITL_PUT_%`) | grep conftest.py |

---

## 8. Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| **`mechanical-greenfield` 0.50 2nd validation also > 1.20** | High (Sprint 57.54 1st was 1.37-2.0 above; pattern-reuse-acceleration may compound) | Sprint 57.55 retro Q4 propose 0.50 → 0.65 lift (rollback rule MET: 2 consec > 1.20) OR tier-4 sub-class split per Sprint 57.54 CONDITIONAL AD; structural action MANDATORY per Sprint 57.52 retro Q4 rollback rule discipline |
| **`mechanical-greenfield` 0.50 2nd validation lands in band [0.85, 1.20]** | Medium (pattern-reuse acceleration may bring ratio back into band) | KEEP 0.50 baseline (1 above + 1 in-band = mixed directions; rollback rule NOT met); flag Sprint 57.56+ 3rd data point continuing |
| **`mechanical-greenfield` 0.50 2nd validation lands < 0.7** | Low (Sprint 57.54 evidence of greenfield design slow; pattern-reuse acceleration would need to be ~5× to drop below band) | 1st < 0.7 data point single-data-point caution KEEP; flag Sprint 57.56+ for direction tracking |
| Unknown flag name validation cost (per-PUT registry SELECT) | Low | Single SELECT statement per PUT; flag registry size small (<100 flags expected); acceptable; alternatives: enum literal pre-cache at app startup deferred Phase 58+ |
| Composite-replace semantics (PUT replaces full override map) vs per-flag PATCH | Medium (UX implication: user must include all explicit overrides in payload) | Documented in plan §4.1 + AC; frontend draft state seeded by reverse-projection (all `overridden_flag === true` items); user clears via "clear override" UI removing from draft; matches Sprint 57.54 HITLPolicies composite-replace pattern |
| `tenants.meta_data` JSONB structure conflicts with other Phase 58.x portfolio items (RateLimits/Identity also use meta_data) | Medium (verified §2.1 Prong 2: Sprint 57.50 Identity already in meta_data["identity"]; Sprint 57.48 RateLimits in meta_data["rate_limits_overrides"]; FF target key `tenant_overrides` is distinct) | Use namespaced key `tenant_overrides` (Sprint 57.48 D-DAY0-3 established convention); separate from other meta_data keys; mutate via dict-copy not in-place |
| Frontend edit-mode form draft state divergence on tenant switch | Medium | Use `[editing, draft]` state-pair; reset both on `tenantId` change via `useEffect` (Sprint 57.54 HITLPoliciesTab precedent) |
| Frontend reverse-projection from items→Record may lose information | Low | Items contain `overridden_flag: bool`; reverse-projection: `Object.fromEntries(items.filter(i => i.overridden_flag).map(i => [i.name, i.resolved_value]))` |
| RLS policy on tenants table (Sprint 57.50 Phase 58.x precedent) | Low | tenants table is global no-RLS (per Sprint 57.48 D-DAY0-3 + 53.7 §Risk Class C); UPDATE works via require_admin_platform_role auth |
| Pydantic Field validator pattern for `overrides` dict | Low | Default validation; key/value type-checked via `dict[str, bool]`; no need for custom field_validator (unknown flag check is endpoint-side post-coercion) |
| Vitest mutation test setup requires QueryClient wrapper | Low | Existing precedent in repo Sprint 57.54 `useHITLPoliciesSave` test verbatim mirror; reuse helper pattern |
| Agent delegation 2 sequential agents (backend then frontend) overhead vs 1 single | Low | Standard pattern (Sprint 57.49/57.50/57.54 precedent); type contract handoff between tracks: backend Pydantic shape → frontend TypeScript shape duplicated once, then frontend agent reads backend types from spec |
| BackendGapBanner copy change may break Vitest snapshot tests | Low | Grep existing snapshot tests for FeatureFlagsTab copy assertions Day 0 Prong 2; update if any |
| `medium-backend` 0.80 8th data point | Low | Per Sprint 57.54 retro Q4: 8th data point continues tracking; no class adjustment unless 3-sprint window pattern emerges |
| `medium-frontend` 0.65 4th data point — if also < 0.7 → 3+ consecutive < 0.7 lower-trigger MET | Medium | If 4th continues < 0.7 → Sprint 57.55 retro Q4 propose 0.65 → 0.50 lift (parallel `medium-backend` recalibration logic); confound resolved at tier-3 sub-class layer |
| `_project_feature_flags_for_tenant` helper extraction risks GET regression | Low | Refactor preserves Sprint 57.48 Track B behavior; existing GET pytest covers behavior; if test fails → revert helper extraction, inline in PUT instead |

---

## 9. Carryover ADs (for Sprint 57.56+ pickup)

- **`AD-AgentFactor-Tier-3-Validation-Sprint-57.56`** (NEW CONDITIONAL — needed IF Sprint 57.55 lands < 0.7 OR in-band; required for rollback rule discipline; pending direction-of-drift from Sprint 57.55 2nd data point)
- **`AD-AgentFactor-Tier-3-Structural-Action`** (CONDITIONAL NEW — IF Sprint 57.55 hits > 1.20 → propose 0.50 → 0.65 lift OR tier-4 sub-class split per Sprint 57.54 CONDITIONAL `AD-Sub-Class-Greenfield-Port-vs-Design-Refinement`; defer concrete proposal to Sprint 57.55 retro Q4)
- **`AD-Plan-Workload-AgentDelegation-Explicit-Field-Codification`** (Sprint 57.53+57.54 carryover continues — if Sprint 57.55 2nd validation cleanly lands → propose codification edit to `sprint-workflow.md §Workload Calibration §Four-segment form` as MANDATORY field in Sprint 57.56)
- **`AD-FeatureFlags-RegistryCRUD-Phase58`** (NEW — Phase 58+ deeper extension; create/delete/update global FeatureFlag registry entries; out of Sprint 57.55 scope)
- ~~**`AD-FeatureFlags-PerFlag-AuditLog-Phase58`**~~ — **REMOVED via D-DAY0-T pivot**: audit chain already auto-emitted by `FeatureFlagsService.set_tenant_override` + `clear_tenant_override` (NEW); no carryover needed
- **`AD-FeatureFlags-NumericOverrides-Phase58`** (NEW — mockup fixture supports `ctl: "num"` but registry only has boolean; Phase 58+ extension if user demand)
- **`AD-FeatureFlags-AuditLogFiltering-UI-Phase58`** (NEW — audit_log entries persisted; UI filtering by `resource_type="feature_flag"` is `/audit-log` page concern; out of Sprint 57.55 scope)
- **`AD-FeatureFlags-PerFlag-RolloutSchedule-Phase58`** (NEW — Phase 58+ extension; canary policy / percentage rollout per flag per tenant)
- **`AD-FeatureFlags-OptimisticConcurrency`** (CONDITIONAL — if Day 1 surfaces concurrent edit race conditions; Phase 58+ If-Match header pattern)
- **`AD-TenantSettings-{Quotas,RateLimits}-Write-Endpoint`** (Phase 58.x portfolio continues; 2 ADs remaining — same mechanical-greenfield pattern as Sprint 57.54 HITLPolicies + Sprint 57.55 FeatureFlags; Sprint 57.56+ candidates following Option B "1 WRITE-side AD per sprint" cadence)
- **`AD-TenantSettings-Identity-Persistence-Phase58`** (Sprint 57.50 carryover continues; full SSO admin schema; broader scope than mechanical-greenfield)
- **`AD-Test-Cleanup-Pattern-Shared-Helper`** (Sprint 57.53+57.54 carryover continues; Phase 58.x — extract `_clear_committed_test_tenants` LIKE patterns to shared helper)
- **`AD-MediumBackend-AICadence-Recalibration`** (Sprint 57.53+57.54 carryover continues; Phase 58+ — revisit `medium-backend` 0.80 if next 2-3 human-factor sprints continue at 0.70-0.85)
- **`AD-Day0-Prong1-Test-Glob-Multi-Pattern`** (Sprint 57.54 carryover continues — codify multi-pattern test file glob in §Step 2.5 Prong 1 to avoid D-DAY0-1 `__tests__/` Glob false-negative repeat)
- **`AD-Phase58-Persistence-WriteSide-Pattern-Template`** (Sprint 57.54 carryover continues — pattern template reusable for Quotas/RateLimits; if Sprint 57.56+ batches multiple → `mechanical-pattern-reuse-heavy` 0.30 candidate)
- Potential NEW from Sprint 57.55 Day 0 三-prong findings

---

**Modification History**:
- 2026-05-26: Sprint 57.55 Day 0.2 — D-DAY0-B 🔴 RED + D-DAY0-T 🆕 NOTABLE pivot applied (corrected baseline §2.1 + §2.2 + §4.1 from raw `tenants.meta_data` SQL to canonical `FeatureFlagsService.set/clear_tenant_override` loop; +15-line `clear_tenant_override` method scope expansion offset by removing raw SQL pattern; audit chain auto-emit removes Phase 58+ carryover positive side-effect); scope (workload / class / Sprint goal) UNCHANGED — see progress.md §Day 0 Pivot Decision
- 2026-05-26: Sprint 57.55 Day 0.1 — Initial draft (FeatureFlags WRITE side Phase 58.x ship; mirror Sprint 57.54 structure verbatim; agent-delegated yes plan-time explicit field per Sprint 57.53+57.54 carryover AD; `mechanical-greenfield` 0.50 tier-3 2nd validation under tier-3 sub-class table; closes Sprint 57.54 carryover AD-AgentFactor-Tier-3-Validation-Sprint-57.55; Phase 58.x portfolio item; rollback rule decision pending 2nd validation outcome)
