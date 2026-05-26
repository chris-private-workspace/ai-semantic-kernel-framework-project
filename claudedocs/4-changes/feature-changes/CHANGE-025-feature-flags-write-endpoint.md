# CHANGE-025: FeatureFlags Admin WRITE-side ship (Phase 58.x portfolio item 2/4)

**Date**: 2026-05-27
**Sprint**: 57.55
**Scope**: Backend (Cat 9 Guardrails / FeatureFlagsService canonical setter + admin tenants WRITE endpoint) + Frontend (tenant-settings FeatureFlagsTab edit mode + mutation hook)
**PR**: TBD (pending Day 2 commit + push)
**Commit (Day 0+1 combined)**: `aff39394`

## Problem

Sprint 57.48 Track B shipped `GET /admin/tenants/{tenant_id}/feature-flags` (read-only) joining global registry `feature_flags` × `tenant_overrides` JSONB per-tenant resolution. Sprint 57.49 shipped read-only FeatureFlagsTab + `useFeatureFlags` hook. But the WRITE side was deferred to Phase 58+ with `BackendGapBanner` copy: "Numeric flag overrides + per-tenant override write API: backend extension Phase 58+". Admin operators had NO way to configure per-tenant FeatureFlag overrides programmatically through the API — only via direct DB manipulation or the legacy `set_tenant_override` programmatic path.

## Root Cause

Sprint 57.48 split read-vs-write deliberately (read-only admin UI first; write API + frontend edit mode deferred to Phase 58+). The write API was the natural next portfolio item in the Phase 58.x sequence (after Sprint 57.54 HITLPolicies WRITE shipped 1st of 4).

Sprint 57.55 Day 0 三-prong revealed plan v1 misframing:
- **D-DAY0-B 🔴 RED**: plan §4.1 assumed `tenants.meta_data["tenant_overrides"]` JSONB storage. **Reality**: per-tenant overrides live on `feature_flags.tenant_overrides[str(tenant_id)]` JSONB ON the global registry table itself (Sprint 56.1 US-4 architecture).
- **D-DAY0-T 🆕 NOTABLE**: `core/feature_flags.py::FeatureFlagsService.set_tenant_override` (Sprint 56.1) IS the canonical setter — auto-emits audit chain via `append_audit` helper. Sprint 57.55 backend should use this canonical service rather than raw SQL — cleaner V2 architecture + audit chain auto-emit positive side-effect.

Pivot decision applied at Day 0 (scope/class/workload UNCHANGED; cleaner architecture; REMOVED `AD-FeatureFlags-PerFlag-AuditLog-Phase58` carryover).

## Solution

### Backend changes (4 files)

1. **`backend/src/core/feature_flags.py`** — Added NEW `clear_tenant_override(flag_name, tenant_id, actor_user_id)` async method to `FeatureFlagsService` (~50 lines incl. docstring). Mirrors existing `set_tenant_override` audit-emit pattern: load flag → del `str(tenant_id)` key from `tenant_overrides` JSONB → emit audit chain (`operation="feature_flag_override_cleared"`) → flush + invalidate cache. Idempotent no-op if override not present.

2. **`backend/src/api/v1/admin/tenants.py`** — (+~165 lines net):
   - Extracted `_project_feature_flags_for_tenant(db, tenant_id, limit, offset) → (items, total)` helper from Sprint 57.48 Track B GET endpoint body (DRY refactor); existing GET endpoint refactored to call helper (existing 8 GET tests pass unmodified)
   - Added Pydantic `FeatureFlagOverridesUpsertRequest` (`extra="forbid"` + `overrides: dict[str, bool]` with composite-replace semantics docstring) + `FeatureFlagOverridesUpsertResponse` (saved_overrides + items echoing GET shape)
   - Added `upsert_tenant_feature_flag_overrides` endpoint at `PUT /admin/tenants/{tenant_id}/feature-flags`:
     - 401/403 via `require_admin_platform_role`
     - 404 via `_load_tenant_or_404`
     - 422 if any override key not in global FeatureFlag registry (single SELECT pre-validation; defense-in-depth catches `FeatureFlagNotFoundError` mid-loop)
     - Composite-replace semantics: SET loop via `service.set_tenant_override(...)` for each payload entry + CLEAR loop via `service.clear_tenant_override(...)` for omitted prior overrides
     - `await db.commit()` after both loops; response.items via helper for cache hydration consistency with GET

3. **`backend/tests/integration/api/test_admin_tenant_feature_flags.py`** — (+~280 lines): 12 NEW pytest tests after existing GET tests. Helpers: `_unique_code()` + `_unique_flag()` uuid4-suffix builders.
   - test_put_requires_admin_role (401/403)
   - test_put_tenant_not_found (404)
   - test_put_creates_new_overrides
   - test_put_updates_existing_overrides
   - test_put_response_projects_items_matching_get
   - test_put_unknown_flag_rejected (422)
   - test_put_extra_field_rejected (422 via `extra="forbid"`)
   - test_put_multi_tenant_isolation
   - test_put_empty_overrides_clears_all
   - test_put_composite_replace_clears_omitted
   - test_put_idempotent_same_payload_twice
   - test_put_persists_to_db_via_subsequent_get

4. **`backend/tests/integration/api/conftest.py`** — (+6 lines): extended `_clear_committed_test_tenants()` with `FF_PUT_%` LIKE sweep (mirror Sprint 57.54 `HITL_PUT_%`) + 2nd sweep line `DELETE FROM feature_flags WHERE name LIKE 'ff.%'` (D-DAY1-1 mid-Track-A drift: global no-RLS registry rows leak between tests after PUT path commits).

### Frontend changes (6 files: 4 modified + 2 NEW)

1. **`frontend/src/features/tenant-settings/types.ts`** (+10 lines): NEW `FeatureFlagOverridesUpsertRequest` + `FeatureFlagOverridesUpsertResponse` types module-level (per Sprint 57.54 D-DAY1-2 precedent; NOT inline in service).

2. **`frontend/src/features/tenant-settings/services/tenantSettingsService.ts`** (+19 lines incl. import): NEW `saveFeatureFlagOverrides(tenantId, payload, signal?)` PUT service func mirroring Sprint 57.54 `saveHITLPolicies` pattern verbatim.

3. **`frontend/src/features/tenant-settings/hooks/useFeatureFlagsSave.ts`** (NEW; 45 lines incl. full header): TanStack `useMutation<Response, Error, Args>` hook with `onSuccess` invalidation of `[...FEATURE_FLAGS_QUERY_KEY_BASE, tenantId]`. Verbatim mirror of Sprint 57.54 `useHITLPoliciesSave.ts`.

4. **`frontend/src/features/tenant-settings/components/tabs/FeatureFlagsTab.tsx`** (rewrite +105 net; preserves read-only path): editing state + draft state + useEffect on tenantId change + Edit/Cancel/Save buttons + per-row controlled Switch + "Clear override" mini-button + reverse-projection draft seed (`items.filter(i => i.overridden).reduce(...)`) + auto-exit on success + inline error rendering. BackendGapBanner copy softened per D-DAY0-D: from "Numeric flag overrides + per-tenant override write API: backend extension Phase 58+" to "Numeric flag overrides + per-flag audit log filtering + registry CRUD: backend extension Phase 58+ — booleans shown are tenant-effective + editable via Edit button".

5. **`frontend/tests/unit/tenant-settings/useFeatureFlagsSave.test.tsx`** (NEW; 110 lines / 3 tests): mutationFn payload + onSuccess invalidate + Error propagation + targeted query key.

6. **`frontend/tests/unit/tenant-settings/tabs/FeatureFlagsTab.test.tsx`** (+106 lines / 8 NEW edit-mode tests + 1 banner update): Edit button visible / draft seed / Switch toggle / Clear override / Save→mutation+exit / Cancel→reset+exit / Save disabled while pending / Banner copy update.

7. **`frontend/tests/unit/tenant-settings/tenantSettingsService.test.ts`** (+45 lines / 2 tests): saveFeatureFlagOverrides PUT URL/body + 422 throw.

## Verification

### Backend
- `pytest test_admin_tenant_feature_flags.py -v` — **20 PASS** (8 existing + 12 NEW)
- Full `pytest --tb=short -q` — **1784 PASS / 4 skip / 0 fail** (1772 baseline + 12 NEW = exact target)
- `mypy --strict src/` — 0 errors / 310 source files
- `black + isort + flake8` — all clean

### Frontend
- `npm run lint` — 0 ESLint errors (3 pre-existing jsx-ast-utils warnings unrelated; --max-warnings 0 enforced)
- `npm run build` — clean / Vite 3.23s / tsc strict 0 errors
- `npm run test` — **630 PASS / 0 fail** / 120 test files / 16.57s (617 baseline + 13 NEW)

### V2 lints
- `python scripts/lint/run_all.py` — **9/9 V2 lints GREEN** (0.99s; incl. check_ap4_frontend_placeholder.py)
- LLM SDK leak scan — 0 leaks

### Mockup-fidelity discipline
- HEX_OKLCH baseline 47 preserved (0 NEW hex/oklch literals)
- All inline `style={{...}}` have `eslint-disable-next-line no-restricted-syntax` comment (Sprint 57.40 FIX-015 lesson honored)
- Mockup-fidelity DUAL CLEAN 22/22 PARITY preserved **11 consecutive sprints 57.45-57.55**

## Impact

### File count delta
- **14 files** (9 modified + 5 NEW):
  - Backend: 4 modified
  - Frontend: 4 modified + 2 NEW
  - Sprint artifacts: 3 NEW (plan + checklist + progress)

### Line delta
- Day 0+1 combined commit `aff39394`: **+2173 / -47** = net +2126 lines

### Test count delta
- pytest: 1772 → **1784** (+12 exact target hit)
- Vitest: 617 → **630** (+13 over target +5-8)

### Calibration delta — TIER-4 SPLIT ACTIVATED

**`mechanical-greenfield` 0.50 — 2nd validation ABOVE band by 0.37 → 2 consec > 1.20 ROLLBACK RULE MET → tier-4 SPLIT ACTIVATED**:
- `mechanical-greenfield-port-style` **0.45** RESERVED (single NEW component-pair via mirror-port; NO NEW design)
- `mechanical-greenfield-design-decisions` **0.65** NEW (single NEW component-pair WITH NEW Pydantic + UX state design)

Sprint 57.54 + 57.55 retroactive `-design-decisions` mapping; equivalent ratios under 0.65 = 1.05-1.55 / 1.21 IN band top edge ✅.

### Phase 58.x portfolio progress
- 1/4 (Sprint 57.54 HITLPolicies) → **2/4 (Sprint 57.55 FeatureFlags)**
- Remaining: Quotas (Sprint 57.56) + RateLimits (Sprint 57.57)

## Lessons Captured (3 codification candidates)

1. **Lesson 1**: Per-resource Phase 58.x WRITE-side plan-drafting needs forward-looking Prong 2 content verify — each portfolio resource has different storage architecture; plan from predecessor template misses divergences. AD candidate: `AD-Day0-Prong2-Phase58-WriteSide-Resource-Storage-Grep` (NEW carryover).

2. **Lesson 2**: Canonical service path > raw SQL for Phase 58.x WRITE-side — grep `core/*` + `platform_layer/*` for existing canonical setter BEFORE plan §4 drafting. AD candidate: `AD-Day0-Prong2-CanonicalService-Grep` (NEW carryover).

3. **Lesson 3**: Tier-4 sub-class refinement is the natural next step when 2 consec > 1.20 under tier-N baseline (parallel Sprint 57.50 tier-2 + 57.52 tier-3 precedents). Tier-4 ACTIVATED this sprint.

## Cross-references

- Sprint 57.54 HITLPolicies WRITE (CHANGE-024) — 1st Phase 58.x portfolio item; predecessor template for Sprint 57.55
- Sprint 56.1 US-4 (Feature Flags) — established `FeatureFlagsService` canonical setter + audit invariant
- Sprint 57.48 Track B (FeatureFlags GET) — established `FeatureFlagItem` projection shape Sprint 57.55 helper extract
- `memory/project_phase57_55_feature_flags_write_endpoint.md` — detailed sprint summary
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-55/retrospective.md` — Q1-Q7 retro
- `.claude/rules/sprint-workflow.md §Active Agent Delegation Factor Modifier` — tier-4 split table
