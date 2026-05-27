# CHANGE-026: Quotas Admin WRITE-side ship (Phase 58.x portfolio item 3/4)

**Date**: 2026-05-27
**Sprint**: 57.56
**Scope**: Backend (admin Quotas WRITE endpoint via `tenant.meta_data["quota_overrides"]` JSONB direct ORM write + manual `append_audit`) + Frontend (tenant-settings QuotasTab Usage quotas Card edit mode + mutation hook)
**PR**: TBD (pending Day 2 push + open)
**Commit (Day 0+1)**: `45735484`

## Problem

Sprint 57.48 Track C shipped `GET /admin/tenants/{tenant_id}/quotas` (read-only) projecting 4 PlanQuota fields from `PlanLoader.get_plan(tenant.plan).quota`. Sprint 57.49 shipped read-only QuotasTab + `useQuotas` hook + RateLimits Card combined. But the WRITE side was deferred to Phase 58+ with `BackendGapBanner` copy: "Live usage tracking (current_usage): backend extension Phase 58+ — limits shown are tenant-effective from PlanQuota". Admin operators had NO way to configure per-tenant Quotas overrides programmatically — only via Plan upgrade (cross-tenant blast radius) or direct DB manipulation.

## Root Cause

Sprint 57.48 split read-vs-write deliberately (read-only admin UI first; write API + frontend edit mode deferred). The write API was the next natural portfolio item in the Phase 58.x sequence (after Sprint 57.54 HITLPolicies + Sprint 57.55 FeatureFlags shipped 1+2 of 4).

Sprint 57.56 Day 0 三-prong revealed plan v0 misframing:
- **D-DAY0-A 🔴 RED** (resolved via user Option B Recommended BEFORE plan v1 drafting): plan v0 assumed Quotas follows Sprint 57.54+57.55 canonical-service-+-override-storage architecture. **Reality**: PlanQuota is per-Plan template immutable (PlanLoader YAML); NO existing override storage; NO canonical service exists. User selected Option B at AskUserQuestion: `tenant.meta_data["quota_overrides"]` JSONB direct ORM write (mirrors Sprint 57.48 RateLimits + Sprint 57.50 Identity precedent); direct ORM UPDATE + manual `append_audit` (Sprint 57.3 PATCH precedent).
- **D-DAY0-D 🆕 NOTABLE**: NO canonical service like Sprint 57.54 (`DBHITLPolicyStore.put()`) or Sprint 57.55 (`FeatureFlagsService.set_tenant_override`); **inversely validates** Sprint 57.55 carryover `AD-Day0-Prong2-CanonicalService-Grep` rule (the rule produces actionable outcomes in BOTH directions).
- **D-DAY0-E 🆕 NOTABLE**: QuotasTab renders Quotas + RateLimits Cards combined; scope guard required: edit mode on Usage quotas Card ONLY (RateLimits Card UNCHANGED = Sprint 57.57 candidate).

Day 0 decision applied BEFORE plan v1 drafting (zero rework cycle; scope/class/workload UNCHANGED).

## Solution

### Backend changes (3 files EDIT only — architecturally simpler than Sprint 57.54+57.55; NO NEW source files)

1. **`backend/src/api/v1/admin/tenants.py`** (+120 / -3):
   - NEW `_PLAN_QUOTA_RESOURCE_WHITELIST` frozenset (4 known resource names; computed from `_QUOTA_RESOURCE_META` DRY refactor — single source for resource names)
   - NEW Pydantic `QuotaOverridesUpsertRequest` (`extra="forbid"` + `field_validator` checking 4-name whitelist; raises ValueError → 422 on unknown resource)
   - NEW Pydantic `QuotaOverridesUpsertResponse` (saved_overrides + items echoing GET shape with override overlay applied)
   - REFACTOR `_project_plan_quota_to_items` to accept optional `overrides: dict[str, float] | None` parameter; applies override overlay over plan default per resource (uses dict.get fallback to PlanQuota attr)
   - REFACTOR existing GET endpoint `list_tenant_quotas` to read `tenant.meta_data.get("quota_overrides") or {}` and pass to helper; existing 7 GET tests pass unmodified
   - NEW `PUT /admin/tenants/{tenant_id}/quotas` endpoint `upsert_tenant_quota_overrides`:
     - 401/403 via `require_admin_platform_role`
     - 404 via `_load_tenant_or_404`
     - 422 via field_validator (unknown resource) OR `extra="forbid"` (extra field)
     - Direct ORM UPDATE via **dict-identity-swap pattern** (`new_meta = dict(tenant.meta_data or {}); new_meta["quota_overrides"] = dict(payload.overrides); tenant.meta_data = new_meta`) for SQLAlchemy JSONB change detection (without identity swap, SQLAlchemy can't detect mutation of in-place dict)
     - Direct `append_audit` call (operation=`tenant_quota_overrides_upsert`; resource_type=`tenant`; mirrors Sprint 57.3 PATCH tenant precedent; **D-DAY1-1 fix-forward**: actual helper name is `append_audit` not `audit_log_append` as plan §4.1 referenced)
     - `await db.commit()` + `await db.refresh(tenant)`; response.items via helper with override overlay for cache hydration consistency

2. **`backend/tests/integration/api/test_admin_tenant_quotas.py`** (+263 / -5): 12 NEW pytest tests after existing GET tests. Helpers: `_unique_code()` uuid4-suffix builder (mirror Sprint 57.55 pattern).
   - `test_put_requires_admin_role` (401)
   - `test_put_tenant_not_found` (404)
   - `test_put_creates_new_overrides` (200; verify tenant.meta_data["quota_overrides"] populated)
   - `test_put_updates_existing_overrides` (PUT twice; 2nd replaces 1st)
   - `test_put_response_projects_items_matching_get` (response.items[i].limit reflects override; subsequent GET returns same)
   - `test_put_unknown_resource_rejected` (422 via field_validator)
   - `test_put_extra_field_rejected` (422 via `extra="forbid"`)
   - `test_put_multi_tenant_isolation` (tenant_b PUT does NOT affect tenant_a meta_data)
   - `test_put_empty_overrides_clears_all` (PUT `{}` → subsequent GET returns plan defaults)
   - `test_put_idempotent_same_payload_twice` (PUT twice same payload → consistent final state)
   - `test_put_persists_to_db_via_subsequent_get` (post-PUT GET reflects new resolved values across all 4 quota items)
   - `test_put_audit_chain_emitted` (mirrors `test_admin_tenant_patch.py` pattern: 1 row with `operation == "tenant_quota_overrides_upsert"`)

3. **`backend/tests/integration/api/conftest.py`** (+3 / -1): extended `_clear_committed_test_tenants()` with `QUOTA_PUT_%` LIKE sweep (mirrors Sprint 57.54 `HITL_PUT_%` + Sprint 57.55 `FF_PUT_%` extensions; parallels Sprint 57.12 + 57.53 §Committed-Row Cleanup Pattern).

### Frontend changes (7 files: 5 EDIT + 2 NEW)

1. **`frontend/src/features/tenant-settings/types.ts`** (+11 lines): NEW `QuotaOverridesUpsertRequest` + `QuotaOverridesUpsertResponse` types module-level (per Sprint 57.54 D-DAY1-2 precedent; NOT inline in service).

2. **`frontend/src/features/tenant-settings/services/tenantSettingsService.ts`** (+22 lines incl. import): NEW `saveQuotaOverrides(tenantId, payload, signal?)` PUT service func — **verbatim mirror** Sprint 57.55 `saveFeatureFlagOverrides` pattern.

3. **`frontend/src/features/tenant-settings/hooks/useQuotasSave.ts`** (NEW; ~45 lines incl. full header): TanStack `useMutation<Response, Error, Args>` hook with `onSuccess` invalidation of `[...QUOTAS_QUERY_KEY_BASE, tenantId]`. **Verbatim mirror** of Sprint 57.55 `useFeatureFlagsSave.ts`.

4. **`frontend/src/features/tenant-settings/components/tabs/QuotasTab.tsx`** (128 → ~262 lines; +134 net):
   - editing state + draft state + useEffect on tenantId change reset
   - Edit/Cancel/Save buttons (top-right of Usage quotas Card header)
   - per-row numeric `<input type="number">` controlled input
   - "Clear override" mini-button per row (removes from draft → omitted from payload)
   - reverse-projection draft seed (uses current limit; user modifies or clears)
   - auto-exit on success + tenant-switch reset + inline error rendering
   - `pct` calculation uses `effectiveLimit` (draft override if present) for real-time preview during edit
   - BackendGapBanner copy softened: from "Live usage tracking (current_usage): backend extension Phase 58+ — limits shown are tenant-effective from PlanQuota" → "Live usage tracking (current_usage Redis counter exposure): backend extension Phase 58+ — limits shown are tenant-effective + editable via Edit button"
   - **CRITICAL SCOPE GUARD**: RateLimits Card UNCHANGED (Sprint 57.57 candidate; verified via 11th assertion test in QuotasTab.test.tsx)
   - **Mockup-fidelity discipline**: HEX_OKLCH baseline 47 preserved (0 NEW oklch literals); all new inline `style={{...}}` has `eslint-disable-next-line no-restricted-syntax` comment

5. **`frontend/tests/unit/tenant-settings/useQuotasSave.test.tsx`** (NEW; ~120 lines / 3 tests): mutationFn payload + onSuccess invalidate (targeted query key) + Error propagation.

6. **`frontend/tests/unit/tenant-settings/tabs/QuotasTab.test.tsx`** (rewrite +124 lines net; 6 → 16 tests / 10 NEW edit-mode tests): Edit button visible / draft seed / input change / Clear override / Save→mutation+exit / Cancel→reset+exit / Save disabled while pending / Banner copy update / RateLimits Card scope guard assertion / handleRequestIncrease + Request increase Button preserved.

7. **`frontend/tests/unit/tenant-settings/tenantSettingsService.test.ts`** (+47 lines / 2 tests + NEW MHist block): saveQuotaOverrides PUT URL/body + 422 throw.

## Verification

### Backend
- `pytest test_admin_tenant_quotas.py -v` — **20 PASS** (8 existing GET + 12 NEW PUT)
- Full `pytest --tb=short -q` — **1796 PASS / 4 skip / 0 fail** (1784 baseline + 12 NEW = exact upper target hit)
- `mypy --strict src/` — 0 errors / 310 source files
- `black + isort + flake8` — all clean

### Frontend
- `npm run lint` — 0 ESLint errors (3 pre-existing jsx-ast-utils warnings unrelated; NOT `--silent` per AD-Pre-Push-Lint-Silent-Suppression-Anti-Pattern)
- `npm run build` — clean / Vite 3.32s / tsc strict 0 errors
- `npm run test` — **645 PASS / 0 fail** / 121 test files (630 baseline + 15 NEW)

### V2 lints
- `python scripts/lint/run_all.py` — **9/9 V2 lints GREEN** (1.03s; incl. check_ap4_frontend_placeholder.py)
- LLM SDK leak scan — 0 leaks

### Mockup-fidelity discipline
- HEX_OKLCH baseline 47 preserved (0 NEW hex/oklch literals)
- All inline `style={{...}}` have `eslint-disable-next-line no-restricted-syntax` comment (Sprint 57.40 FIX-015 lesson honored)
- Mockup-fidelity DUAL CLEAN 22/22 PARITY preserved **12 consecutive sprints 57.45-57.56** ⭐ — strongest streak of Phase 57+ epic

## Impact

### File count delta
- **13 files** (8 EDIT + 5 untracked NEW including sprint artifacts):
  - Backend: 3 EDIT
  - Frontend: 5 EDIT + 2 NEW
  - Sprint artifacts: 3 NEW (plan + checklist + progress + execution dir)

### Line delta
- Day 0+1 combined commit `45735484`: **+2002 / -43** = net +1959 lines

### Test count delta
- pytest: 1784 → **1796** (+12 exact upper target hit)
- Vitest: 630 → **645** (+15 over plan +5-8 by 88% upper bound; acceptable per Sprint 57.55 precedent +13)

### Calibration delta — TIER-4 1ST VALIDATION ✅ CLEAN

**`mechanical-greenfield-design-decisions` 0.65 — 1st validation IN BAND middle**:
- Bottom-up est ~3.3 hr → class-calibrated ~2.64 hr (mult 0.80 medium-backend) → agent-adjusted ~1.72 hr (agent_factor 0.65 tier-4)
- Actual wall-clock ~1.67-1.83 hr → ratio actual/agent-adjusted **~1.02** ✅ IN BAND middle [0.85, 1.20]
- **tier-4 SPLIT 1st validation CONFIRMED CLEANLY**; KEEP 0.65 baseline
- Sprint 57.54+57.55 retroactive `-design-decisions` mapping VINDICATED (equivalent ratios 1.05-1.55 / 1.21 → Sprint 57.56 ~1.02 bullseye)
- Flag Sprint 57.57+ 2nd validation under same sub-class for rollback rule baseline

**Class baseline tracking**:
- `medium-backend` 0.80 9th data point ratio ~0.66 (BELOW band; 9-pt mean ~0.65; last 3 = 2/3 < 0.7; lower-trigger NOT MET; KEEP per confound-resolved-at-sub-class-layer discipline)
- `medium-frontend` 0.65 6th data point ratio ~0.50 (4th consecutive < 0.7; KEEP per discipline)

### Phase 58.x portfolio progress
- 1/4 (Sprint 57.54 HITLPolicies) → 2/4 (Sprint 57.55 FeatureFlags) → **3/4 (Sprint 57.56 Quotas)** ✅
- Remaining: RateLimits (Sprint 57.57 candidate; final 4/4)

### Code-implementer agent chain
- 18th + 19th consecutive code-implementer delegation post Sprint 57.53 break
- Direct ORM path (no canonical service) variant validated as ~equivalent speed to canonical service path (Sprint 57.54+57.55 ~50 min agent; Sprint 57.56 ~50-55 min agent — Pydantic + audit code volume comparable)

## Lessons Captured (3 codification candidates — 3-data-point evidence reached)

1. **Lesson 1 — Phase 58.x WRITE-side architectural heterogeneity** (3 of 3 sprints had Day 0 plan-pivot OR Day 0 architecture-clarification): codify in `sprint-workflow.md §Step 2.5 Prong 2 Drift Class table` as NEW row "Phase 58.x WRITE-side resource storage architecture mismatch". AD candidate: `AD-Day0-Prong2-Phase58-WriteSide-Resource-Storage-Grep` PROMOTION (Sprint 57.55 carryover — 3-data-point evidence reached).

2. **Lesson 2 — Canonical service path NOT universal** (3 sprints = 3 patterns: dedicated table / JSONB on registry / NO service): the rule "search for canonical service" produces actionable outcomes in BOTH directions (exists → use it; doesn't exist → direct ORM simplification). AD candidate: `AD-Day0-Prong2-CanonicalService-Grep` PROMOTION (Sprint 57.55 carryover — 2-data-point evidence, both directions validated).

3. **Lesson 3 — Plan-time explicit "Agent-delegated: yes" 4-segment Workload form** (Sprint 57.54 + 57.55 + 57.56 all explicit; 3-data-point evidence reached per AD-Plan-2/3/4/5 promotion precedent): promote to MANDATORY field in `sprint-workflow.md §Workload Calibration §Four-segment form when agent_factor applies`. AD candidate: `AD-Plan-Workload-AgentDelegation-Explicit-Field-Codification` PROMOTION.

## Cross-references

- Sprint 57.55 FeatureFlags WRITE (CHANGE-025) — 2nd Phase 58.x portfolio item; canonical service path precedent
- Sprint 57.54 HITLPolicies WRITE (CHANGE-024) — 1st portfolio item; dedicated table + RLS pattern
- Sprint 57.48 RateLimits Track D — `tenant.meta_data["rate_limits"]` JSONB direct ORM precedent for Sprint 57.56 Option B pattern
- Sprint 57.50 Identity GET — `tenant.meta_data["identity"]` precedent
- Sprint 57.3 PATCH tenant — `append_audit` direct call precedent
- `memory/project_phase57_56_quotas_write_endpoint.md` — detailed sprint summary
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-56/retrospective.md` — Q1-Q6 retro (Q7 N/A SKIP 6th consecutive)
- `.claude/rules/sprint-workflow.md §Active Agent Delegation Factor Modifier` — tier-4 sub-class table activation history
