# Sprint 57.57 — RateLimits Admin Write Endpoint + Frontend Edit Mode (Phase 58.x WRITE side 4/4 FINAL)

**Phase**: 57+ Frontend SaaS / Phase 58.x portfolio (RateLimits WRITE-side ship; backend admin upsert + frontend edit mode — **FINAL portfolio item closing the 4-AD WRITE-side wave**)
**Goal**: Ship the Phase 58.x WRITE side for RateLimits — close the existing BackendGapBanner copy in QuotasTab RateLimits Card by adding `PUT /admin/tenants/{tenant_id}/rate-limits` overrides upsert endpoint + `tenants.meta_data["rate_limits"]` JSONB write (list-of-`{label, value}` composite-replace semantics; mirrors Sprint 57.48 Track D read shape verbatim) + Pydantic write schema + frontend QuotasTab RateLimits Card edit mode (Usage quotas Card UNCHANGED per scope guard — **reverse of Sprint 57.56**) + `useRateLimitsSave` mutation hook with variable-length-list UX (add row + remove row + empty list allowed). This is the **2nd validation data point** for tier-4 sub-class `mechanical-greenfield-design-decisions` 0.65 (NEW Sprint 57.55 retro Q4 ACTIVATION; closes Sprint 57.56 carryover `AD-AgentFactor-Tier-4-Validation-Sprint-57.57`; single NEW component-pair = 1 endpoint + 1 mutation hook + 1 Card edit mode following Sprint 57.54+57.55+57.56 template). **Sprint 57.57 = Phase 58.x portfolio FINAL ship 4/4 — closes WRITE-side wave; remaining Phase 58+ work moves to deeper extensions (live usage tracking / rate limit syntax validation / etc).** Day 2 closeout bundles **3 PROMOTION ADs** (per user 2026-05-27 selection): AD-Plan-Workload-AgentDelegation-Explicit-Field-Codification (3-data-point evidence reached) + AD-Day0-Prong2-Phase58-WriteSide-Resource-Storage-Grep (3-data-point reached) + AD-Day0-Prong2-CanonicalService-Grep (2-data-point both directions actionable) → all 3 promoted to `sprint-workflow.md` rule additions.
**Branch**: `feature/sprint-57-57-rate-limits-write-endpoint`
**Class**: `medium-backend` 0.80 (9-data-point baseline post Sprint 57.56: 55.5=1.14 + 55.6=0.92 + 57.47=0.16 + 57.48=0.11 + 57.50=0.27 + 57.53=0.83 + 57.54≈1.0 + 57.55=0.79 + 57.56≈0.66; 9-pt mean ~0.65; last-3 mean ~0.82 IN band lower-middle; KEEP per Sprint 57.56 retro Q4 — confound-resolved-at-sub-class-layer discipline holds)
**Sub-class** (agent_factor): `mechanical-greenfield-design-decisions` 0.65 (**tier-4 2nd validation** under NEW table effective Sprint 57.56+ per Sprint 57.55 retro Q4 tier-4 SPLIT ACTIVATION; closes Sprint 57.56 carryover `AD-AgentFactor-Tier-4-Validation-Sprint-57.57`; Sprint 57.56 = 1st validation IN BAND middle ratio ~1.02 CONFIRMED CLEANLY)
**Agent-delegated**: **yes — backend + frontend via code-implementer agent delegation** (≥ 80% of Day 1 work; required to generate 2nd validation data point under `mechanical-greenfield-design-decisions` 0.65; sequential: backend → frontend; 20th + 21st consecutive code-implementer chain extended)
**Date**: 2026-05-27 (Sprint 57.56 closeout same-day continuation; main `7daaa66f` post PR #206 merge; Sprint 57.57 branch from main HEAD)
**Prior sprint reference**: Sprint 57.56 (closeout 2026-05-27; PR #206 merged main `7daaa66f`) generated `mechanical-greenfield-design-decisions` 0.65 tier-4 **1st validation** data point with ratio ~1.02 ✅ IN BAND middle [0.85, 1.20] → **tier-4 SPLIT 1st validation CONFIRMED CLEANLY**; KEEP 0.65 baseline; Sprint 57.54+57.55 retroactive `-design-decisions` mapping VINDICATED. Sprint 57.57 = **2nd validation under tier-4 `-design-decisions` 0.65** → if lands IN band [0.85, 1.20] → tier-4 SPLIT fully validated (2 consec IN band; rollback rule baseline established); if > 1.20 → 1st > 1.20 data point single-data-point caution KEEP (1-of-2 in band still); if < 0.7 → 1st < 0.7 data point single-data-point caution KEEP; rollback rule "2 sprints > 1.20 OR < 0.7 → trigger structural action" requires ANOTHER below/above-band sprint to fire.

---

## 1. Sprint Goal

```
AS the project maintainer of the Phase 58.x SaaS portfolio (HITLPolicies
   shipped Sprint 57.54 / FeatureFlags shipped Sprint 57.55 / Quotas
   shipped Sprint 57.56 / RateLimits = THIS sprint = FINAL 4/4) AND the
   V2 calibration matrix maintainer with `mechanical-greenfield-design-
   decisions` 0.65 tier-4 sub-class table now with 1 data point IN BAND
   middle (Sprint 57.56 ~1.02 CONFIRMED CLEANLY) but needs a 2nd data
   point to fully validate tier-4 SPLIT + establish rollback rule
   baseline (per Sprint 57.56 retro Q4 flag)
I WANT the RateLimits WRITE-side gap closed (PUT items upsert endpoint +
   tenants.meta_data["rate_limits"] JSONB write with list-of-{label,
   value} composite-replace semantics + Pydantic write schema + frontend
   QuotasTab RateLimits Card edit mode with variable-length-list UX (add
   row + remove row + empty list allowed = fallback to DEFAULT_RATE_LIMITS)
   + useRateLimitsSave mutation hook + service func) — selected from
   Phase 58.x portfolio per user direction 2026-05-27 as the FINAL 4/4
   item — executed via code-implementer agent delegation (backend track
   + frontend track sequential; 20th + 21st consecutive) such that the
   sprint generates the SECOND validation data point for `mechanical-
   greenfield-design-decisions` 0.65 tier-4 baseline + bundles 3
   PROMOTION ADs into Day 2 docs track
SO THAT (a) Sprint 57.56 carryover `AD-AgentFactor-Tier-4-Validation-
   Sprint-57.57` is closed with a clean 2nd validation data point under
   agent-delegated mode; (b) Sprint 57.57 retro Q4 either confirms tier-4
   SPLIT fully validated cleanly (2 consec IN band) OR generates 1st
   above/below-band data point for Sprint 57.58+ rollback rule baseline;
   (c) the existing BackendGapBanner copy in QuotasTab RateLimits Card
   ("Rate limits read-only; backend admin endpoint Phase 58+") is
   softened to admit only deeper Phase 58+ gaps remain (rate limit
   syntax validation / per-rule live usage tracking); (d) Sprint 57.48
   Track D RateLimits read-only frontend tab is extended into full read+
   write parity matching the Sprint 57.54+57.55+57.56 edit-mode pattern
   for tenant-settings admin UX consistency; (e) `medium-backend` 0.80
   class gets its 10th data point continuing post-confound-resolution
   tracking (per Sprint 57.56 retro Q4 discipline); (f) `medium-frontend`
   0.65 class gets its 7th data point (Sprint 57.13=0.95-1.0 / 57.49=
   0.064 / 57.54≈0.32 / 57.55=0.53 / 57.56≈0.50 / Sprint 57.57 = TBD);
   confound resolved at tier-4 sub-class layer per Sprint 57.56
   discipline; (g) Phase 58.x portfolio progresses from 3/4 (Quotas
   shipped) to **4/4 FINAL ✅ CLOSURE** (RateLimits WRITE side closed;
   wave complete; Phase 58+ moves to deeper extensions); (h) Day 2
   closeout bundles 3 PROMOTION ADs into `sprint-workflow.md` rule
   updates (AD-Plan-Workload-AgentDelegation-Explicit-Field-Codification
   + AD-Day0-Prong2-Phase58-WriteSide-Resource-Storage-Grep + AD-Day0-
   Prong2-CanonicalService-Grep)
```

## 2. Background & Context

### 2.1 RateLimits baseline state (verified Sprint 57.57 Day 0 Prong 2 content verify — all GREEN per pre-plan grep)

**Sprint 57.57 Day 0 pre-plan content verify** (Prong 2 done before plan draft per Sprint 57.55 D-DAY0-B RED lesson — avoid plan-write rework):

- ✅ `backend/src/api/v1/admin/tenants.py` L1319-1384 (Sprint 57.48 Track D) implements `GET /admin/tenants/{tenant_id}/rate-limits` — projects `tenant.meta_data["rate_limits"]` list of `{label, value}` (string both) via paginated `RateLimitListResponse`
- ✅ `RateLimitItem` Pydantic at L1327-1331 = `{label: str, value: str}`; both display strings (e.g. value = "100 / min")
- ✅ `RateLimitListResponse` at L1334-1338 = `{items, total, limit, offset}` (paginated read shape)
- ✅ `DEFAULT_RATE_LIMITS` at L1341-1345 = hardcoded 3-item list fallback when `tenant.meta_data["rate_limits"]` is empty/missing (mirrors `_fixtures.ts` RATE_LIMITS shape verbatim)
- ✅ `backend/src/infrastructure/db/models/identity.py::Tenant.meta_data` JSONB column exists (Sprint 57.50 D-DAY0-2 lesson Tenant ORM lives in `identity.py` not `tenant.py`); namespace key `"rate_limits"` already established by Sprint 57.48 Track D (no migration needed)
- ✅ `backend/tests/integration/api/test_admin_tenant_rate_limits.py` exists (Sprint 57.48 Day 1; 7-9 GET tests; will extend with PUT tests)
- ✅ `backend/tests/integration/api/conftest.py` exists with `_clear_committed_test_tenants()` (extended Sprint 57.54 HITL_PUT_% + Sprint 57.55 FF_PUT_% + Sprint 57.56 QUOTA_PUT_% sweeps; pattern: prefix LIKE sweep)
- ✅ `frontend/src/features/tenant-settings/types.ts` — `RateLimitItem` + `RateLimitListResponse` declared
- ✅ `frontend/src/features/tenant-settings/services/tenantSettingsService.ts` — `fetchRateLimits` + Sprint 57.56 `saveQuotaOverrides` precedent to mirror
- ✅ `frontend/src/features/tenant-settings/hooks/useRateLimits.ts` exists with `RATE_LIMITS_QUERY_KEY_BASE` (Sprint 57.49)
- ✅ `frontend/src/features/tenant-settings/components/tabs/QuotasTab.tsx` renders BOTH Usage quotas Card + RateLimits Card combined (Sprint 57.49); Sprint 57.56 added edit mode to Usage quotas Card ONLY (scope guard); Sprint 57.57 = **reverse scope guard** = add edit mode to RateLimits Card + Usage quotas Card UNCHANGED

**No D-DAY0-A 🔴 RED in Sprint 57.57** — unlike Sprint 57.56 (which discovered NO override storage on Day 0 → user Option B pivot), Sprint 57.57's storage path `tenant.meta_data["rate_limits"]` has been established + active since Sprint 57.48 Track D. The WRITE side simply extends the existing read into write-back with composite-replace semantics.

### 2.2 True Phase 58.x gap for RateLimits

**Backend gaps** (Sprint 57.57 closes):
1. ❌ `tenant.meta_data["rate_limits"]` JSONB write path (direct ORM UPDATE; namespace key `"rate_limits"` already in use by Sprint 57.48 Track D read; write extends in place)
2. ❌ `PUT /admin/tenants/{tenant_id}/rate-limits` admin endpoint (composite-replace semantics; mirrors Sprint 57.56 `PUT /quotas` pattern — same direct ORM UPDATE + manual `append_audit`)
3. ❌ `RateLimitsUpsertRequest` Pydantic write schema (composite `items: list[RateLimitItem]`; variable-length list; **NO whitelist** unlike Sprint 57.56 Quotas — RateLimits has free-form labels per spec)
4. ❌ Pytest tests covering upsert/multi-tenant isolation/composite-replace clear behavior/empty list/audit chain emit verification/idempotency/persistence-via-subsequent-GET

**Frontend gaps** (Sprint 57.57 closes):
1. ❌ `saveRateLimits(tenantId, payload)` service func
2. ❌ `useRateLimitsSave(tenantId)` TanStack mutation hook (with invalidation of `RATE_LIMITS_QUERY_KEY_BASE`)
3. ❌ `QuotasTab` edit-mode toggle on **RateLimits Card ONLY** (Edit/Cancel/Save buttons + per-row `<input>` for label + value text + Add row button + per-row Remove (×) button + variable-length list state + empty list save allowed (= clear all overrides → backend falls back to DEFAULT_RATE_LIMITS); Usage quotas Card UNCHANGED → Sprint 57.56 scope guard preserved reverse)
4. ❌ Vitest tests (mutation hook + tab edit mode incl. add row / remove row / empty list save / Usage quotas Card UNCHANGED scope guard assertion)
5. ❌ BackendGapBanner copy soften for RateLimits Card (existing read-only banner removed; only deeper Phase 58+ extensions remain)

**Deferred (REMAINS Phase 58+)**:
- ❌ Rate limit syntax validation (parse "100 / min" into structured `{limit: int, unit: "request", period: "minute"}` — currently raw display string) — Phase 58+ scope
- ❌ Per-rule live usage tracking (similar to Quotas live usage gap) — Phase 58+ extension
- ❌ Rate limit enforcement at runtime (currently `tenant.meta_data["rate_limits"]` is admin display only; no runtime enforcement using these values) — Phase 58+ extension
- ❌ Per-rule alerting thresholds — Phase 58+ extension
- ❌ Optimistic concurrency / If-Match (Sprint 57.50 Identity Phase 58.x precedent — also deferred)
- ❌ Dedicated `tenant_rate_limits` table (Sprint 57.48 D-DAY0-5 noted as Phase 58+ option if persistence requirements grow)

### 2.3 Why `mechanical-greenfield-design-decisions` 0.65 tier-4 2nd validation (NOT port-style 0.45)

Per Sprint 57.55 retro Q4 tier-4 SPLIT ACTIVATION decision + Sprint 57.56 retro Q4 1st validation CONFIRMED CLEANLY + `sprint-workflow.md §Active Agent Delegation Factor Modifier` tier-4 sub-class table:

| Sub-class | Trigger | Sprint 57.57 fit? |
|-----------|---------|--------------------|
| `mechanical-pattern-reuse-heavy` 0.30 | ≥ 4 mechanical repetitions of same template in 1 sprint | ❌ Sprint 57.57 = 1 NEW endpoint pair + 1 NEW mutation hook + 1 Card edit mode (counts as 1 component-pair, not 4) |
| `mechanical-greenfield-port-style` 0.45 RESERVED | Single NEW component-pair via mirror-port; **NO** NEW Pydantic schema design / NO NEW UX state design | ❌ Sprint 57.57 has NEW Pydantic list-composite design (variable-length list semantics; NOT mirror-port of 57.56 dict shape) + NEW UX state design (add/remove row + empty list state machine — distinct from Sprint 57.56 per-resource numeric input) |
| **`mechanical-greenfield-design-decisions` 0.65 NEW** | Single NEW component-pair WITH NEW Pydantic + UX state design | ✅ MATCH — variable-length list UX + composite-replace list semantics + Pydantic items list shape all NEW design vs Sprint 57.56 |
| `mixed-multidomain-bundle-mechanical` 0.65 | 3+ independent tracks WITH mechanical pattern reuse | ❌ Sprint 57.57 = single RateLimits domain |
| `mixed-multidomain-bundle-non-mechanical` 1.0 | 3+ independent tracks; pure audit/docs/rules | ❌ |

**Note on Day 2 docs track**: Day 2 bundles 3 PROMOTION docs edits (~20-30 min total) — does NOT trigger reclassification because (a) <80% Day 1 work (Day 1 is the agent-delegated track); (b) Day 2 closeout 已是常規 sprint closeout 一部分 (memory + retro + CLAUDE.md + next-phase-candidates + CHANGE-027); (c) the 3 PROMOTIONs are codification-only (no source code change). 仍歸 single-domain `mechanical-greenfield-design-decisions` 0.65.

**2nd validation prediction**:
- Sprint 57.56 1st validation under tier-4 0.65 = ratio ~1.02 IN BAND middle CONFIRMED CLEANLY (single new endpoint + hook + Card edit mode w/ NEW Pydantic + NEW UX state)
- Sprint 57.57 same shape (single new endpoint + hook + Card edit mode w/ NEW Pydantic + NEW UX state) but with **variable-length-list UX slightly more complex than fixed-4-resource numeric input** of Sprint 57.56
- Predicted actual ratio under tier-4 0.65: **~0.95-1.30 IN/ABOVE band middle to top edge** (slightly higher variance than Sprint 57.56 due to add/remove row state machine + reverse scope guard verification)
- **Decision matrix at Sprint 57.57 retro Q4**:
  - If lands IN band [0.85, 1.20] → tier-4 SPLIT 2nd validation CONFIRMED CLEANLY; **tier-4 SPLIT fully validated with 2 consec IN band**; KEEP 0.65; rollback rule baseline established (need 3 consec OOB-same-direction to fire)
  - If lands > 1.20 → 1st > 1.20 single-data-point caution KEEP (1 IN band + 1 > band; mixed signal, NOT 2 consec); flag Sprint 57.58+ for 3rd validation
  - If lands < 0.7 → 1st < 0.7 single-data-point caution KEEP (1 IN band + 1 < band; mixed signal); flag Sprint 57.58+ for 3rd validation

### 2.4 Pattern-reuse capture (Sprint 57.54-57.56 WRITE-side wave precedents)

Sprint 57.54+57.55+57.56 established the WRITE-side template (now 4-data-point base after Sprint 57.57):
- `PUT /admin/tenants/{tenant_id}/<resource>` upsert endpoint with composite-replace semantics
- Pydantic `<Resource>UpsertRequest` with `extra="forbid"` + optional `field_validator` (whitelist for Sprint 57.56 Quotas; type/empty-check for Sprint 57.57 RateLimits)
- Pydantic `<Resource>UpsertResponse` echoing saved composite + projected items
- `use<Resource>Save` TanStack mutation hook (mirror `useTenantSettingsSave` Sprint 57.9; verbatim follow Sprint 57.54+57.55+57.56)
- Tab edit mode: editing state + draft state + Edit/Cancel/Save buttons + per-row form + reverse-projection items→composite draft seed + BackendGapBanner copy soften
- conftest.py `<RESOURCE>_PUT_%` LIKE sweep extension (mirrors Sprint 57.12 + 57.53 §Committed-Row Cleanup Pattern; Sprint 57.57 adds `RATE_PUT_%`)

**Sprint 57.57 architectural pattern** (mirrors Sprint 57.56 direct ORM simplification):
- ❌ NO canonical service extension (RateLimits has no service like FF/HITL)
- ✅ Direct ORM UPDATE on `Tenant.meta_data["rate_limits"]` (Sprint 57.48 read precedent + Sprint 57.56 write precedent verbatim mirror)
- ✅ Manual `append_audit(operation="tenant_rate_limits_upsert", ...)` (Sprint 57.3 PATCH precedent; D-DAY1-1 helper name `append_audit` NOT `audit_log_append` per Sprint 57.56 fix-forward — already corrected in plan §4.1)
- ✅ GET endpoint already reads from `tenant.meta_data["rate_limits"]` (Sprint 57.48); PUT writes; **no GET refactor needed** (unlike Sprint 57.56 which needed `_project_plan_quota_to_items` overrides parameter extension because of plan template merge — RateLimits has no plan template)

**Sprint 57.57 UX deltas vs Sprint 57.54-57.56**:
- **Variable-length list** (Sprint 57.57 NEW) vs fixed schema (57.54 reviewer/SLA per risk × 3 / 57.55 flag on/off per registered flag / 57.56 4 fixed quota resources)
- **Add row button + per-row Remove (×)** UI primitive (Sprint 57.57 NEW; no precedent in 57.54-57.56 tabs)
- **Empty list save allowed** = clear all overrides → backend falls back to `DEFAULT_RATE_LIMITS` (Sprint 57.57 NEW; Sprint 57.56 had analogous "empty dict clears all" but with fixed-resource semantics)
- **Two text inputs per row** (label + value as display strings) vs single numeric input per row (Sprint 57.56)

### 2.5 Sprint 57.56 carryover chain (`AD-AgentFactor-Tier-4-Validation-Sprint-57.57`)

- Sprint 57.55 retro Q4 (2026-05-27): tier-4 SPLIT ACTIVATED — `mechanical-greenfield-port-style` 0.45 RESERVED + `mechanical-greenfield-design-decisions` 0.65 NEW; Sprint 57.54+57.55 retroactive `-design-decisions` mapping (equivalent ratios 1.05-1.55 / 1.21 → band top edge / IN band)
- Sprint 57.56 = mandated agent-delegated mode to deliver tier-4 1st validation data point under `-design-decisions` 0.65; ratio actual/agent-adjusted ~1.02 ✅ IN BAND middle CONFIRMED CLEANLY (closes `AD-AgentFactor-Tier-4-Validation-Sprint-57.56`)
- Sprint 57.57 = mandated agent-delegated mode to deliver tier-4 **2nd validation** data point under `-design-decisions` 0.65 (closes `AD-AgentFactor-Tier-4-Validation-Sprint-57.57`)
- Sprint 57.57 also = **Phase 58.x portfolio FINAL ship 4/4** (HITLPolicies + FeatureFlags + Quotas + RateLimits all closed; wave complete)

### 2.6 Class baseline tracking continuation

- `medium-backend` 0.80: Sprint 57.56 was 9th data point (ratio ~0.66; 9-pt mean ~0.65; last-3 mean ~0.82 IN band lower-middle; KEEP per Sprint 57.56 retro Q4). Sprint 57.57 = 10th data point continuing post-confound-resolution tracking — **10-pt mean is meaningful sample size threshold** per `When to adjust the multiplier` rule.
- `medium-frontend` 0.65: Sprint 57.56 was 6th data point (ratio ~0.50; 6-pt mean ~0.54; 3-of-last-3 < 0.7 lower-trigger MET BUT KEEP per Sprint 57.50+57.55+57.56 confound-resolved-at-sub-class-layer discipline — frontend confound resolved at tier-4 sub-class layer; class baseline holds for human-pace; AD-medium-frontend-Baseline-Recalibration continues — need consistent human-factor data point to recalibrate). Sprint 57.57 frontend portion = 7th data point.

### 2.7 Day 2 docs track — 3 PROMOTION ADs (per user 2026-05-27 bundle decision)

Per user selection of "Bundle 3 PROMOTION ADs into closeout docs track" option, Sprint 57.57 Day 2 closeout adds the following codification edits to `.claude/rules/sprint-workflow.md`:

**PROMOTION 1: `AD-Plan-Workload-AgentDelegation-Explicit-Field-Codification`** (Sprint 57.53+57.54+57.55+57.56 carryover — 4-data-point evidence reached):
- Add MANDATORY rule to `§Workload Calibration §Four-segment form when agent_factor applies`: plan §Workload **must** include explicit "Agent-delegated: yes / no / partial" field at plan-time
- Update §Tracking discipline to add "explicit `agent-delegated: yes / no / partial` tag at plan-time (NOT just retrospective Q2)"
- Per AD-Plan-2/3/4/5 promotion precedent: 3-data-point evidence sufficient (Sprint 57.57 = 5th consecutive data point under proposed rule)

**PROMOTION 2: `AD-Day0-Prong2-Phase58-WriteSide-Resource-Storage-Grep`** (Sprint 57.55+57.56 carryover — 3-data-point evidence reached):
- Add NEW Drift Class row to `§Step 2.5 Prong 2 Drift Class table`: **Claimed-but-missing-storage-path** (e.g. plan assumes `<resource>` has dedicated override table; reality = `tenant.meta_data["<key>"]` JSONB direct write OR vice versa). Grep template: `grep -rn "meta_data\[.<key>.\]\|<Resource>Service\|class .*<Resource>.*Store" backend/src/` to discover actual storage architecture before plan §4.1 commits
- Codifies Sprint 57.55 D-DAY0-B + Sprint 57.56 D-DAY0-A + Sprint 57.57 (no D-DAY0 RED on this dim — storage was already explicit since Sprint 57.48; Sprint 57.57 validates rule by absence)

**PROMOTION 3: `AD-Day0-Prong2-CanonicalService-Grep`** (Sprint 57.55+57.56 carryover — 2-data-point both directions actionable):
- Add NEW Drift Class row to `§Step 2.5 Prong 2 Drift Class table`: **Claimed-but-missing-canonical-service** (e.g. plan assumes a canonical service method like `Service.set_override` exists; reality = no canonical service, direct ORM path required OR vice versa). Grep template: `grep -rn "class .*<Resource>Service\|def set_\|def put_\|def update_" backend/src/` to discover canonical service availability before plan §4.1 endpoint design
- Codifies Sprint 57.55 D-DAY0-T (positive — found canonical setter, simplified plan) + Sprint 57.56 D-DAY0-D (inverse — found NO canonical service, simplified to direct ORM); both directions produce actionable plan pivots

---

## 3. User Stories

### US-1: Backend WRITE side — PUT items endpoint + tenants.meta_data write

```
AS the V2 backend developer extending the existing Sprint 57.48 Track D
   RateLimits admin API surface (read-only) to support per-tenant
   RateLimits override write
I WANT the WRITE side for `tenants.meta_data["rate_limits"]` JSONB +
   `PUT /admin/tenants/{tenant_id}/rate-limits` upsert endpoint +
   Pydantic `RateLimitsUpsertRequest` write schema (composite `items:
   list[RateLimitItem]`) + integration tests covering all critical paths
   (auth/404/upsert-create/upsert-update/multi-tenant isolation/empty
   list-allowed/idempotency/persistence-via-GET/audit chain emit)
SO THAT admin operators can configure per-tenant RateLimits overrides
   programmatically + the frontend QuotasTab RateLimits Card can ship
   edit mode in US-2 without backend gap.
```

**Acceptance**:
- WRITE path uses direct SQLAlchemy ORM update on `tenant.meta_data["rate_limits"]` via dict-identity-swap pattern (mirror Sprint 57.56 Quotas exactly: `new_meta = dict(...); new_meta["rate_limits"] = list(...); tenant.meta_data = new_meta`); `tenants.updated_at` rotates server-side via existing `onupdate=func.now()` invariant
- `RateLimitsUpsertRequest` Pydantic model with composite shape (single field `items: list[RateLimitItem]`); `extra="forbid"`; reuse existing `RateLimitItem` Pydantic from Sprint 57.48 Track D (`{label: str, value: str}` with `model_config = ConfigDict(from_attributes=True)`)
- `PUT /admin/tenants/{tenant_id}/rate-limits` endpoint returns 200 OK with `RateLimitsUpsertResponse` (echoes saved items + projected pagination shape matching GET response `{items, total, limit, offset}` — total=len(saved items); limit=50 default; offset=0)
- Endpoint uses `Depends(require_admin_platform_role)` (matches existing GET endpoint per Sprint 57.48 Track D)
- Endpoint uses `_load_tenant_or_404` for 404 path consistency
- Empty `items: []` payload accepted → clears all RateLimits overrides (subsequent GET returns DEFAULT_RATE_LIMITS fallback per Sprint 57.48 Track D existing behavior)
- Composite-replace semantics: `payload.items` represents COMPLETE desired override state; any prior overrides not in payload are removed
- Insertion order preserved (Python list semantics + JSONB list serialization preserves order)
- Audit chain entry emitted via direct `append_audit(...)` call (mirrors Sprint 57.56 fix-forward + Sprint 57.3 PATCH precedent; operation=`tenant_rate_limits_upsert`)
- Pytest 8-10 NEW tests added in `backend/tests/integration/api/test_admin_tenant_rate_limits.py` (extend existing Sprint 57.48 file):
  - `test_put_requires_admin_role` (401/403)
  - `test_put_tenant_not_found` (404)
  - `test_put_creates_new_items` (200; no prior overrides)
  - `test_put_replaces_existing_items` (200; prior overrides, new list replaces)
  - `test_put_response_projects_items_matching_get` (response shape matches GET pagination envelope)
  - `test_put_extra_field_rejected` (422; payload with non-`items` field)
  - `test_put_multi_tenant_isolation` (tenant_b PUT does NOT affect tenant_a meta_data)
  - `test_put_empty_items_clears_all` (200; PUT with `[]` clears all → subsequent GET returns DEFAULT_RATE_LIMITS)
  - `test_put_idempotent_same_payload_twice` (PUT twice same payload → consistent state; updated_at rotates)
  - `test_put_audit_chain_emitted` (operation=`tenant_rate_limits_upsert` row appears in audit_log)
- Pytest count delta: +8 to +10 (current 1796 PASS → 1804-1806 PASS); 0 fail; 0 skip change

### US-2: Frontend WRITE side — useRateLimitsSave + QuotasTab RateLimits Card edit mode

```
AS the V2 frontend developer extending the Sprint 57.49 QuotasTab
   (read-only display of Usage quotas + Rate limits combined; Sprint
   57.56 added edit mode to Usage quotas Card ONLY) to support inline
   edit mode on RateLimits Card matching the Sprint 57.54+57.55+57.56
   edit-mode pattern for tenant-settings admin UX consistency
I WANT a NEW `useRateLimitsSave(tenantId)` TanStack mutation hook +
   `saveRateLimits` service func + edit-mode UI on QuotasTab RateLimits
   Card ONLY (Edit/Cancel/Save buttons + Add row button + per-row label
   + value text inputs + per-row Remove (×) button + variable-length
   list state + empty list save allowed; Usage quotas Card UNCHANGED —
   Sprint 57.56 scope guard preserved reverse) + Vitest tests covering
   mutation success/error/cache invalidation/add row/remove row/empty
   list save/Usage quotas Card UNCHANGED scope guard assertion
SO THAT the BackendGapBanner copy can be softened (only rate limit
   syntax validation + per-rule live usage tracking remain Phase 58+;
   override edit API now real-backed).
```

**Acceptance**:
- `frontend/src/features/tenant-settings/services/tenantSettingsService.ts` — NEW `saveRateLimits(tenantId, payload)` async func using `fetchWithAuth` PUT; matches existing `fetchRateLimits` / `saveQuotaOverrides` (Sprint 57.56) / `saveFeatureFlagOverrides` (Sprint 57.55) patterns
- `frontend/src/features/tenant-settings/types.ts` — NEW types `RateLimitsUpsertRequest` + `RateLimitsUpsertResponse` (type module-level per Sprint 57.54+57.55+57.56 precedent; NOT inline in service)
- `frontend/src/features/tenant-settings/hooks/useRateLimitsSave.ts` — NEW TanStack `useMutation` hook with `onSuccess` invalidation of `RATE_LIMITS_QUERY_KEY_BASE` (re-fetches GET); error propagation via existing pattern (mirror `useQuotasSave` Sprint 57.56 + `useFeatureFlagsSave` Sprint 57.55 + `useHITLPoliciesSave` Sprint 57.54 verbatim)
- `frontend/src/features/tenant-settings/components/tabs/QuotasTab.tsx` — edit mode on RateLimits Card ONLY:
  - State: `editing: boolean` + `draft: RateLimitItem[]` (list shape mirroring write schema; seeded by reverse-projection from current items)
  - Edit button: top-right of RateLimits Card, toggles `editing`
  - Edit form: per-row two text `<input type="text">` (label + value) controlled inputs + per-row Remove (×) button removing that index from draft
  - **Add row button** at bottom of edit form (appends `{label: "", value: ""}` to draft)
  - Save / Cancel buttons: Save calls mutation, Cancel reverts draft + exits edit mode
  - Empty list (0 rows) save allowed → PUT body `items: []` → backend falls back to DEFAULT_RATE_LIMITS on subsequent GET
  - Success → exits edit mode + invalidates RATE_LIMITS_QUERY_KEY_BASE
  - Error → keeps form open + shows error message
  - **Scope guard**: Usage quotas Card UNCHANGED (Sprint 57.56 edit mode preserved; reverse of Sprint 57.56 scope guard which protected RateLimits Card)
  - **Mockup-fidelity discipline**: 0 NEW hex/oklch literals (reuse existing `--info`/`--warning`/`--success`/`--danger` tokens via existing buttons via `--btn-primary` pattern from existing tabs and Sprint 57.54-57.56 edit modes)
- BackendGapBanner copy update for RateLimits Card section: soften to "Rate limit syntax validation + per-rule live usage tracking: backend extension Phase 58+ — rule list editable via Edit button" (or similar; preserve V2 §Frontend Mockup-Fidelity Hard Constraint discipline by reusing existing BackendGapBanner component verbatim — only the message string changes)
- Vitest 8-13 NEW tests added across:
  - `frontend/tests/unit/tenant-settings/useRateLimitsSave.test.tsx` (NEW file; mutation success → invalidates QUERY_KEY / mutation error → propagates error / payload shape — 3 tests)
  - `frontend/tests/unit/tenant-settings/tabs/QuotasTab.test.tsx` (extend; 8-10 NEW edit-mode tests covering RateLimits Card: Edit visible / draft seed / label input change / value input change / Add row appends to draft / Remove row deletes from draft / Save→mutation+exit / Cancel→reset+exit / Empty list save allowed / Usage quotas Card UNCHANGED scope guard assertion + banner copy update + Save disabled while pending)
  - `frontend/tests/unit/tenant-settings/tenantSettingsService.test.ts` (extend; saveRateLimits PUT shape + URL + body — 1-2 tests)
- Vitest count delta: +8 to +13 (current 645 PASS → 653-658 PASS); 0 fail; 0 skip change

### US-3: 3 PROMOTION ADs codification (per user 2026-05-27 bundle decision)

```
AS the V2 calibration matrix maintainer + sprint workflow rule
   maintainer with 3 carryover ADs reaching promotion criteria (3+
   data-point evidence per AD-Plan-2/3/4/5 promotion precedent)
I WANT 3 docs-only edits to `.claude/rules/sprint-workflow.md` bundled
   into Sprint 57.57 Day 2 closeout (parallel track to RateLimits ship;
   no source code change; ~20-30 min total docs work):
   1. AD-Plan-Workload-AgentDelegation-Explicit-Field-Codification →
      §Workload Calibration §Four-segment form MANDATORY field
   2. AD-Day0-Prong2-Phase58-WriteSide-Resource-Storage-Grep → §Step
      2.5 Prong 2 NEW Drift Class row (Claimed-but-missing-storage-path)
   3. AD-Day0-Prong2-CanonicalService-Grep → §Step 2.5 Prong 2 NEW
      Drift Class row (Claimed-but-missing-canonical-service)
SO THAT Phase 58.x WRITE-side wave closeout (Sprint 57.54-57.57) leaves
   no codification debt; future Phase 58+ sprints inherit clearer Day 0
   三-prong + plan §Workload discipline.
```

**Acceptance**:
- `.claude/rules/sprint-workflow.md` §Workload Calibration §Four-segment form when agent_factor applies — MANDATORY field added to 4-segment form template; tracking discipline §3 updated to "explicit `agent-delegated: yes / no / partial` tag at plan-time (NOT just retrospective Q2)"
- `.claude/rules/sprint-workflow.md` §Step 2.5 Prong 2 Drift Class table — 2 NEW rows added (Claimed-but-missing-storage-path + Claimed-but-missing-canonical-service) with grep template + ROI evidence cross-reference
- File MHist 1-line entry on `.claude/rules/sprint-workflow.md` for Sprint 57.57 PROMOTION bundle (≤100 chars per AD-Lint-MHist-Verbosity)
- 3 carryover ADs marked CLOSED in `claudedocs/1-planning/next-phase-candidates.md` Sprint 57.57 closeout section
- This US is a Day 2 closeout track (Day 1 = RateLimits ship; Day 2 = closeout + 3 PROMOTIONS)

---

## 4. Technical Specification

### 4.1 Backend Track — Direct ORM UPDATE on tenants.meta_data["rate_limits"]

Mirror Sprint 57.56 Quotas WRITE-side exactly with simplifications:
- NO whitelist (RateLimits has free-form labels)
- NO plan-default merge (RateLimits has no plan template — fallback to DEFAULT_RATE_LIMITS handled in existing GET at L1368-1370)
- NO GET refactor needed (Sprint 57.48 Track D GET reads `tenant.meta_data["rate_limits"]` directly; PUT writes to same key)
- List composite-replace semantics (vs Quotas dict composite-replace)
- Empty list allowed (vs Quotas empty dict allowed — semantically equivalent: clear all overrides)

**File 1**: `backend/src/api/v1/admin/tenants.py` (extend; ~100 lines added)

```python
# === Sprint 57.57 — RateLimits admin PUT (closes AD-TenantSettings-RateLimits-Write-Endpoint Phase 58.x portfolio FINAL 4/4) ===
# Composite-replace semantics on tenant.meta_data["rate_limits"] JSONB list-of-{label, value};
# mirrors Sprint 57.56 Quotas direct ORM UPDATE + manual append_audit pattern verbatim;
# variable-length list (empty list allowed = clear all overrides → DEFAULT_RATE_LIMITS fallback
# via existing Sprint 57.48 Track D GET behavior preserved).

class RateLimitsUpsertRequest(BaseModel):
    """Composite RateLimits upsert payload (composite-replace semantics; variable-length list)."""

    model_config = ConfigDict(extra="forbid")
    items: list[RateLimitItem] = Field(
        default_factory=list,
        description=(
            "List of {label, value} rate limit entries. Composite-replace "
            "semantics: payload.items represents COMPLETE desired override state. "
            "Empty list ([]) clears all overrides → backend falls back to "
            "DEFAULT_RATE_LIMITS on subsequent GET. Insertion order preserved."
        ),
    )


class RateLimitsUpsertResponse(BaseModel):
    """Echoes saved items + projects pagination envelope matching GET shape for cache hydration."""

    items: list[RateLimitItem]
    total: int
    limit: int
    offset: int


@router.put(
    "/{tenant_id}/rate-limits",
    response_model=RateLimitsUpsertResponse,
    dependencies=[Depends(require_admin_platform_role)],
)
async def upsert_tenant_rate_limits(
    tenant_id: UUID,
    payload: RateLimitsUpsertRequest,
    db: AsyncSession = Depends(get_db_session),
    actor_user_id: UUID = Depends(require_admin_platform_role),
) -> RateLimitsUpsertResponse:
    """Upsert per-tenant RateLimits overrides into tenant.meta_data["rate_limits"].

    Composite-replace semantics: payload.items represents the COMPLETE desired
    override state for this tenant. Empty items list ([]) clears all overrides
    (subsequent GET returns DEFAULT_RATE_LIMITS fallback via Sprint 57.48 Track D
    existing behavior).

    - 401/403 via require_admin_platform_role
    - 404 via _load_tenant_or_404
    - 422 via RateLimitsUpsertRequest extra="forbid"
    - 200 with response.items + pagination envelope (projected for cache hydration consistency with GET)
    - Audit chain entry emitted via direct append_audit (Sprint 57.3 PATCH + Sprint 57.56 precedent)
    """
    tenant = await _load_tenant_or_404(db, tenant_id)

    # Write items list into meta_data["rate_limits"] via dict-identity-swap for SQLAlchemy JSONB change detection
    new_meta = dict(tenant.meta_data or {})
    new_meta["rate_limits"] = [
        {"label": item.label, "value": item.value} for item in payload.items
    ]
    tenant.meta_data = new_meta

    # Audit chain (Sprint 57.3 PATCH + Sprint 57.56 precedent; helper name `append_audit` per Sprint 57.56 D-DAY1-1 fix-forward)
    await append_audit(
        db,
        tenant_id=tenant_id,
        user_id=actor_user_id,
        operation="tenant_rate_limits_upsert",
        resource_type="tenant",
        resource_id=str(tenant_id),
        operation_data={
            "tenant_id": str(tenant_id),
            "items_count": len(payload.items),
            "items": [{"label": i.label, "value": i.value} for i in payload.items],
        },
        operation_result="success",
    )

    await db.commit()
    await db.refresh(tenant)

    # Project pagination envelope (cache hydration consistency with GET — Sprint 57.48 Track D shape)
    saved_items = [RateLimitItem(label=i.label, value=i.value) for i in payload.items]
    return RateLimitsUpsertResponse(
        items=saved_items,
        total=len(saved_items),
        limit=50,
        offset=0,
    )
```

**No GET refactor needed**: Sprint 57.48 Track D `list_tenant_rate_limits` already reads `tenant.meta_data["rate_limits"]` and falls back to DEFAULT_RATE_LIMITS when empty/missing. Sprint 57.57 PUT writes to the same key; subsequent GET reads the new list naturally.

**Total backend code**: ~100 lines net (NEW Pydantic 2 + endpoint 1; no helper extension; no GET refactor — architecturally simpler than Sprint 57.56 which had `_project_plan_quota_to_items` overrides param extension).

### 4.2 Backend Track — Pytest tests

**File**: `backend/tests/integration/api/test_admin_tenant_rate_limits.py` (extend existing Sprint 57.48 file)

Add 8-10 NEW tests after the existing GET tests (which already establish auth/404/multi-tenant patterns; reuse fixtures verbatim). Helpers: `_unique_code()` uuid4-suffix builder (mirror Sprint 57.55+57.56 pattern).

**File**: `backend/tests/integration/api/conftest.py` (extend `_clear_committed_test_tenants` LIKE sweep)

Add `RATE_PUT_%` LIKE prefix to the existing `_clear_committed_test_tenants()` cleanup sweep (mirrors Sprint 57.54 `HITL_PUT_%` + Sprint 57.55 `FF_PUT_%` + Sprint 57.56 `QUOTA_PUT_%` extensions; parallels Sprint 57.12 + 57.53 §Committed-Row Cleanup Pattern).

### 4.3 Frontend Track — Types module

**File**: `frontend/src/features/tenant-settings/types.ts` (extend)

```typescript
export interface RateLimitsUpsertRequest {
  items: RateLimitItem[];
}

export interface RateLimitsUpsertResponse {
  items: RateLimitItem[];
  total: number;
  limit: number;
  offset: number;
}
```

(Reuses existing `RateLimitItem` type from Sprint 57.48; no new RateLimitItem shape change.)

### 4.4 Frontend Track — Service func

**File**: `frontend/src/features/tenant-settings/services/tenantSettingsService.ts` (extend)

```typescript
export async function saveRateLimits(
  tenantId: string,
  payload: RateLimitsUpsertRequest,
  signal?: AbortSignal
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
```

### 4.5 Frontend Track — Mutation hook

**File**: `frontend/src/features/tenant-settings/hooks/useRateLimitsSave.ts` (NEW; mirror `useQuotasSave.ts` Sprint 57.56 verbatim)

```typescript
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { saveRateLimits } from "../services/tenantSettingsService";
import type {
  RateLimitsUpsertRequest,
  RateLimitsUpsertResponse,
} from "../types";
import { RATE_LIMITS_QUERY_KEY_BASE } from "./useRateLimits";

export function useRateLimitsSave(tenantId: string) {
  const queryClient = useQueryClient();
  return useMutation<
    RateLimitsUpsertResponse,
    Error,
    RateLimitsUpsertRequest
  >({
    mutationFn: (payload) => saveRateLimits(tenantId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...RATE_LIMITS_QUERY_KEY_BASE, tenantId],
      });
    },
  });
}
```

### 4.6 Frontend Track — QuotasTab edit mode (RateLimits Card ONLY)

**File**: `frontend/src/features/tenant-settings/components/tabs/QuotasTab.tsx` (edit)

Edit mode adds to RateLimits Card ONLY:
- State: `const [rlEditing, setRlEditing] = useState(false); const [rlDraft, setRlDraft] = useState<RateLimitItem[]>(seedFromItems);`
- useEffect on `tenantId` change → reset both rlEditing + rlDraft
- Edit toggle button (top-right of RateLimits Card header area; **NOT** affecting Usage quotas Card Edit button which Sprint 57.56 added)
- Form:
  - Per-row two `<input type="text">` (label + value as display strings)
  - Per-row Remove (×) button (filters draft removing that index)
  - **Add row button** at bottom of edit form (appends `{label: "", value: ""}` to draft)
- Save → call useRateLimitsSave mutation; Cancel → reset draft + exit
- Empty list save (0 rows in draft) → PUT body `items: []` → backend clears all overrides
- BackendGapBanner copy soften for RateLimits Card section
- **Usage quotas Card UNCHANGED** (Sprint 57.56 scope guard preserved reverse; Sprint 57.56 added edit mode to Usage quotas Card — that Edit/Cancel/Save UI remains intact)

### 4.7 Verification

- `cd backend && pytest tests/integration/api/test_admin_tenant_rate_limits.py -v` → all PASS (existing + 8-10 NEW)
- `cd backend && pytest --tb=short -q` → 1804-1806 PASS + 0 fail
- `cd backend && mypy --strict src/` → 0 errors
- `python scripts/lint/run_all.py` → 9/9 GREEN
- `cd frontend && npm run lint && npm run build` → exit 0 / 0 ESLint / 0 tsc errors (NOT `--silent` per AD-Pre-Push-Lint-Silent-Suppression-Anti-Pattern)
- `cd frontend && npm run test` → 653-658 PASS
- LLM SDK leak scan → 0
- HEX_OKLCH baseline 47 unchanged (13 consecutive sprints 57.45-57.57 DUAL CLEAN target)

---

## 5. File Change List

### Backend (EDIT only — no NEW files; architecturally simpler than 57.54+57.55 + same simplification as 57.56)
- **EDIT**: `backend/src/api/v1/admin/tenants.py` — add `RateLimitsUpsertRequest` + `RateLimitsUpsertResponse` Pydantic + `upsert_tenant_rate_limits` endpoint (~100 lines net)
- **EDIT**: `backend/tests/integration/api/test_admin_tenant_rate_limits.py` — add 8-10 NEW PUT tests (~200-260 lines)
- **EDIT**: `backend/tests/integration/api/conftest.py` — add `RATE_PUT_%` LIKE sweep (~1 line addition to existing `_clear_committed_test_tenants`)

### Frontend (NEW + EDIT)
- **EDIT**: `frontend/src/features/tenant-settings/types.ts` — add `RateLimitsUpsertRequest` + `RateLimitsUpsertResponse` types (~10 lines)
- **EDIT**: `frontend/src/features/tenant-settings/services/tenantSettingsService.ts` — add `saveRateLimits` service func (~19 lines incl. import)
- **NEW**: `frontend/src/features/tenant-settings/hooks/useRateLimitsSave.ts` — mutation hook (~45 lines incl. full header per file-header-convention.md)
- **EDIT**: `frontend/src/features/tenant-settings/components/tabs/QuotasTab.tsx` — add RateLimits Card edit mode (~150 lines added; soften BackendGapBanner copy; Usage quotas Card unchanged)
- **NEW**: `frontend/tests/unit/tenant-settings/useRateLimitsSave.test.tsx` — mutation hook Vitest tests (~110 lines)
- **EDIT**: `frontend/tests/unit/tenant-settings/tabs/QuotasTab.test.tsx` — extend with RateLimits Card edit-mode tests + Usage quotas Card UNCHANGED scope guard assertion (~140 lines added)
- **EDIT**: `frontend/tests/unit/tenant-settings/tenantSettingsService.test.ts` — extend with saveRateLimits test (~45 lines)

### Day 2 docs track (3 PROMOTIONS — per user 2026-05-27 bundle decision)
- **EDIT**: `.claude/rules/sprint-workflow.md` — 3 PROMOTION edits (~80-120 lines added across 2 sections + 1 MHist entry):
  - §Workload Calibration §Four-segment form when agent_factor applies — MANDATORY field codification (PROMOTION 1)
  - §Step 2.5 Prong 2 Drift Class table — 2 NEW rows (PROMOTION 2 + PROMOTION 3)
  - §Tracking discipline — explicit plan-time agent-delegated tag MANDATORY (PROMOTION 1 sub-rule)

### Sprint artifacts (Day 0 + Day 2)
- `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-57-plan.md` (this file)
- `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-57-checklist.md`
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-57/progress.md`
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-57/retrospective.md`
- `memory/project_phase57_57_rate_limits_write_endpoint.md`
- `memory/MEMORY.md` (pointer entry)
- `claudedocs/1-planning/next-phase-candidates.md` (Sprint 57.57 closeout note + Phase 58.x portfolio 4/4 FINAL CLOSURE 🎉)
- `CLAUDE.md` (Current Sprint row + Last Updated footer)
- `.claude/rules/sprint-workflow.md` (matrix +1 row data point for `mechanical-greenfield-design-decisions` 0.65 2nd validation + `medium-backend` 0.80 10th + `medium-frontend` 0.65 7th + §Active block 2nd validation entry under tier-4 sub-class table; ALSO the 3 PROMOTION rule additions per US-3)
- `claudedocs/4-changes/feature-changes/CHANGE-027-rate-limits-write-endpoint.md` (NEW — per CLAUDE.md `4-changes/` convention)

---

## 6. Workload

**Bottom-up est**: ~3.5 hr
- Day 0 三-prong (Prong 1 path verify on admin/tenants.py + frontend tab/hook/service paths; Prong 2 content verify on baseline ALREADY DONE in this plan §2.1; Prong 3 schema verify on tenants.meta_data JSONB column + namespace key `"rate_limits"` already established Sprint 57.48): ~0.3 hr (DONE pre-plan)
- Day 1 Backend track (PUT endpoint + Pydantic + ~8-10 pytest tests, agent-delegated via code-implementer; ~10-15% faster than Sprint 57.56 due to no helper extension + no GET refactor + pattern fully internalized 4-data-point base): ~1.1 hr human-equivalent
- Day 1 Frontend track (types + service func + mutation hook + RateLimits Card edit mode with variable-length-list UX + ~8-13 Vitest tests + BackendGapBanner copy soften + Usage quotas Card scope guard verification, agent-delegated via code-implementer; ~5-10% slower than Sprint 57.56 due to variable-length list UX complexity + reverse scope guard): ~1.3 hr human-equivalent
- Day 2 closeout (progress + retro + memory + sprint-workflow.md matrix + CLAUDE.md + next-phase-candidates + CHANGE-027 + commit + PR): ~0.5 hr standard closeout
- Day 2 docs track (3 PROMOTION edits to `.claude/rules/sprint-workflow.md`): ~0.3 hr (per user bundle decision)

**Class-calibrated commit** (`medium-backend` 0.80):
- 3.5 × 0.80 = **~2.8 hr committed (~168 min)**

**Agent-adjusted commit** (`agent_factor = 0.65` tier-4 `mechanical-greenfield-design-decisions` — **2nd validation**):
- 2.8 × 0.65 = **~1.82 hr agent-adjusted (~109 min)**

**4-segment form**:
> Bottom-up est ~3.5 hr → class-calibrated commit ~2.8 hr (mult 0.80) → agent-adjusted commit ~1.82 hr (agent_factor 0.65 tier-4 `mechanical-greenfield-design-decisions` — **2nd validation under tier-4 table** effective Sprint 57.56+)
> **Agent-delegated**: **yes** — backend + frontend via code-implementer agent delegation (sequential: backend first, then frontend with backend types confirmed; mirror Sprint 57.54+57.55+57.56 sequence; 20th + 21st consecutive code-implementer)

**2nd validation prediction (tier-4 `mechanical-greenfield-design-decisions` 0.65)**:
- Single component-pair (1 backend endpoint + 1 frontend mutation hook + 1 Card edit mode) cleanly scoped; agent-delegated pattern from Sprint 57.49-57.56 internalized (20th-21st consecutive frontend agent)
- **Pattern-reuse acceleration vs Sprint 57.56**: Sprint 57.56 had ratio 1.02 (1st validation IN BAND middle CONFIRMED CLEANLY); Sprint 57.57 has same architecture (direct ORM + manual append_audit) + 4-data-point pattern-reuse base (Sprint 57.54-57.56); BUT variable-length-list UX slightly more complex than Sprint 57.56 fixed-resource numeric input
- Expected actual ~55-75 min wall-clock total (backend ~10-15 min agent + frontend ~25-30 min agent + supervisory ~5-10 min + Day 0 ~15 min DONE + Day 2 closeout ~25-30 min incl. 3 PROMOTION edits)
- Predicted ratio actual/committed-with-agent-factor: **~0.95-1.30 IN/ABOVE band middle to top edge** (greenfield design decisions still apply: list composite-replace semantics + add/remove row UX + reverse scope guard verification)
- **Decision matrix at Sprint 57.57 retro Q4**:
  - If lands IN band [0.85, 1.20] → tier-4 SPLIT 2nd validation CONFIRMED CLEANLY; **tier-4 SPLIT fully validated with 2 consec IN band**; KEEP 0.65; rollback rule baseline established (need 3 consec OOB-same-direction to fire structural action)
  - If lands > 1.20 → 1st > 1.20 data point single-data-point caution KEEP (mixed signal: 1 IN band + 1 > band; NOT 2 consec same direction); flag Sprint 57.58+ for 3rd validation
  - If lands < 0.7 → 1st < 0.7 data point single-data-point caution KEEP (mixed signal: 1 IN band + 1 < band); flag Sprint 57.58+ for 3rd validation; if Sprint 57.58 also < 0.7 → 2 consec < 0.7 → propose 0.65 → 0.45 tighten (matching `-port-style` baseline; would suggest reclassifying Sprint 57.57 retroactively as `-port-style`)

---

## 7. Acceptance Criteria

| # | Criterion | Verify |
|---|---|---|
| AC-1 | `upsert_tenant_rate_limits` endpoint declared with `@router.put("/{tenant_id}/rate-limits", ...)` | grep `@router.put.*rate-limits` in admin/tenants.py |
| AC-2 | Pydantic `RateLimitsUpsertRequest` + `RateLimitsUpsertResponse` declared + `extra="forbid"` set | grep models in admin/tenants.py |
| AC-3 | Extra field rejected with 422 (via `extra="forbid"`) | pytest `test_put_extra_field_rejected` |
| AC-4 | Multi-tenant isolation guarded (tenant_b PUT does not affect tenant_a meta_data) | pytest `test_put_multi_tenant_isolation` |
| AC-5 | Empty items list clears all override list (subsequent GET returns DEFAULT_RATE_LIMITS) | pytest `test_put_empty_items_clears_all` |
| AC-6 | Reuse `RateLimitItem` Pydantic from Sprint 57.48 Track D (no schema change) | grep RateLimitItem in admin/tenants.py |
| AC-7 | Audit chain entry emitted (operation=`tenant_rate_limits_upsert`; resource_type=`tenant`) via `append_audit` (NOT `audit_log_append` per Sprint 57.56 D-DAY1-1 fix-forward) | pytest `test_put_audit_chain_emitted` |
| AC-8 | Pytest count delta +8 to +10 | `pytest --tb=short -q` count = 1804-1806 |
| AC-9 | Full backend pytest baseline ALL-GREEN | `pytest --tb=short -q` 0 fail |
| AC-10 | mypy --strict 0 errors | `mypy --strict src/` |
| AC-11 | 9 V2 lints preserved | `python scripts/lint/run_all.py` exit 0 |
| AC-12 | LLM SDK leak 0 | covered by `run_all.py` |
| AC-13 | NEW `saveRateLimits` service func + `useRateLimitsSave` mutation hook implemented | grep files |
| AC-14 | QuotasTab RateLimits Card edit-mode UI (Edit/Cancel/Save + per-row label+value text inputs + Add row + per-row Remove button) functional | manual smoke + Vitest tab tests |
| AC-15 | QuotasTab Usage quotas Card UNCHANGED (scope guard reverse of Sprint 57.56; Sprint 57.56 edit mode preserved intact) | grep + Vitest scope guard assertion test |
| AC-16 | Empty items list save allowed → backend falls back to DEFAULT_RATE_LIMITS | pytest `test_put_empty_items_clears_all` + Vitest empty list save test |
| AC-17 | BackendGapBanner copy softened for RateLimits Card section | grep BackendGapBanner text |
| AC-18 | Vitest count delta +8 to +13 | `npm run test` count = 653-658 |
| AC-19 | Vite build clean | `npm run build` exit 0 |
| AC-20 | tsc strict 0 errors | covered by `npm run build` |
| AC-21 | ESLint 0 errors | `npm run lint` (NOT `--silent`) |
| AC-22 | File MHist updated on edited files (≤100 char budget per AD-Lint-MHist-Verbosity) | grep MHist lines |
| AC-23 | Day 0 三-prong report logged with drift findings | Read progress.md Day 0 |
| AC-24 | retrospective.md Q1-Q6 with **2nd validation `mechanical-greenfield-design-decisions` 0.65 ratio + tier-4 SPLIT 2-data-point assessment** in Q4 + agent-delegation confirmed in Q2 | grep Q2 + Q4 |
| AC-25 | sprint-workflow.md MHist + matrix `medium-backend` 0.80 10th data point + `medium-frontend` 0.65 7th data point + §Active block `mechanical-greenfield-design-decisions` 0.65 2nd validation entry | grep |
| AC-26 | CHANGE-027-rate-limits-write-endpoint.md created | Read claudedocs/4-changes/feature-changes/ |
| AC-27 | conftest.py `RATE_PUT_%` LIKE sweep added (mirrors Sprint 57.54 HITL + 57.55 FF + 57.56 QUOTA) | grep conftest.py |
| AC-28 | Mockup-fidelity DUAL CLEAN 22/22 PARITY preserved (13 consecutive sprints 57.45-57.57); HEX_OKLCH baseline 47 unchanged | check-mockup-fidelity.mjs PASS + grep oklch count |
| AC-29 | 3 PROMOTION ADs codified into `.claude/rules/sprint-workflow.md` (per US-3): §Workload Calibration §Four-segment form MANDATORY agent-delegated field + §Step 2.5 Prong 2 NEW Drift Class rows (Claimed-but-missing-storage-path + Claimed-but-missing-canonical-service) | grep §Workload §Step 2.5 in sprint-workflow.md |
| AC-30 | 3 carryover ADs marked CLOSED in next-phase-candidates.md Sprint 57.57 closeout section | grep CLOSED in next-phase-candidates.md |

---

## 8. Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| **`mechanical-greenfield-design-decisions` 0.65 tier-4 2nd validation lands > 1.20** | Medium (Sprint 57.56 1st validation 1.02 IN band; variable-length list UX slightly more complex; could push slightly higher) | Sprint 57.57 retro Q4 single-data-point caution KEEP 0.65 (mixed signal not 2 consec same direction); flag Sprint 57.58+ for 3rd validation |
| **`mechanical-greenfield-design-decisions` 0.65 tier-4 2nd validation lands in band [0.85, 1.20]** | High (Sprint 57.56 1st validation 1.02 IN band cleanly; same architecture + simpler GET path + 4-data-point pattern-reuse base) | KEEP 0.65 baseline; tier-4 SPLIT 2nd validation CONFIRMED CLEANLY; rollback rule baseline established (need 3 consec OOB-same-direction to fire) |
| **`mechanical-greenfield-design-decisions` 0.65 tier-4 2nd validation lands < 0.7** | Low (architectural simplification + 4-data-point pattern-reuse base would need to push ratio below 0.7; possible if Sprint 57.57 turns out closer to `-port-style` than `-design-decisions` despite NEW Pydantic + UX state design) | 1st < 0.7 data point single-data-point caution KEEP (mixed signal not 2 consec same direction); flag Sprint 57.58+ for 3rd validation |
| Variable-length list UX state machine complexity (add row / remove row / empty list save) | Medium | Test coverage explicit per US-2 (add row appends / remove row deletes / empty list save / Save while pending disabled); Vitest count +8-13 absorbs UX coverage; agent prompt scope explicit |
| Reverse scope guard verification (Usage quotas Card unchanged) | Medium (QuotasTab renders both Cards combined; Sprint 57.56 already added edit mode to Usage Card; Sprint 57.57 must NOT touch that edit mode) | Explicit scope guard in US-2 + AC-15; code-implementer agent prompt MUST scope edit to RateLimits Card ONLY; verify via diff review post-Day-1 + Vitest scope guard assertion test (Usage quotas Card Edit/Cancel/Save buttons + numeric inputs unchanged) |
| Composite-replace semantics vs per-row PATCH | Medium (UX implication: user must include all rules in payload) | Documented in plan §4.1 + AC; frontend draft state seeded by current items; user adds via Add row button / removes via × button; same composite-replace pattern as Sprint 57.54-57.56 |
| `tenant.meta_data["rate_limits"]` JSONB list serialization order | Low (Python list + Postgres JSONB list both preserve order; FastAPI default JSON encoder also preserves order) | Verified Day 0; pytest `test_put_response_projects_items_matching_get` covers order preservation across PUT→GET cycle |
| Pydantic `extra="forbid"` on RateLimitsUpsertRequest (no whitelist on RateLimitItem content) | Low | `extra="forbid"` on outer Request blocks unknown top-level fields; RateLimitItem reused unchanged (allows arbitrary label + value strings per spec) |
| Day 2 docs track (3 PROMOTIONs) cost overshoot | Low | Each promotion = ~10 min docs edit; total ~30 min budgeted; if any blocks, fall back to Phase 58+ standalone docs sprint |
| AD-Plan-Workload-AgentDelegation-Explicit-Field-Codification MANDATORY field affects future plans | Low (Sprint 57.54-57.56 already use explicit field; Sprint 57.57 = 5th consecutive; codification merely codifies existing practice) | Plan template stub will be reviewed for fit-purpose |
| Vitest mutation test setup requires QueryClient wrapper | Low | Existing precedent in repo Sprint 57.54-57.56 verbatim mirror; reuse helper pattern |
| Agent delegation 2 sequential agents (backend then frontend) overhead | Low | Standard pattern (Sprint 57.49-57.56 precedent); type contract handoff via shared types.ts module |
| BackendGapBanner copy change may break Vitest snapshot tests | Low | Grep existing snapshot tests for QuotasTab copy assertions Day 0 Prong 2; update if any |
| `medium-backend` 0.80 10th data point | Low | Per Sprint 57.56 retro Q4: 10th data point continues tracking + reaches meaningful sample threshold; no class adjustment unless 3-sprint window pattern emerges |
| `medium-frontend` 0.65 7th data point — if also < 0.7 → 5 consecutive < 0.7 lower-trigger persistent | Low | Confound resolved at tier-4 sub-class layer per Sprint 57.55+57.56 discipline; class baseline holds; AD-medium-frontend-Baseline-Recalibration continues (need consistent human-factor data) |
| QuotasTab combined Cards: Usage quotas Card edit state vs RateLimits Card edit state isolation | Medium | Separate state pairs: `(qEditing, qDraft)` from Sprint 57.56 vs `(rlEditing, rlDraft)` Sprint 57.57; both useEffect on tenantId reset; both Cards' Edit buttons independent |
| Frontend reverse-projection from current items to draft (seed) | Low | Items already in correct shape `RateLimitItem[]`; draft seed = direct copy on entering edit mode; no transform needed |
| Phase 58.x portfolio 4/4 FINAL CLOSURE — premature celebration if Sprint 57.57 fails CI | Low | Standard 5-CI-check gate before merge; Sprint 57.57 announces 4/4 ONLY after PR #207 merge |

---

## 9. Carryover ADs (for Sprint 57.58+ pickup)

- **`AD-AgentFactor-Tier-4-Validation-Sprint-57.58`** (NEW CONDITIONAL — needed for 3rd validation under `mechanical-greenfield-design-decisions` 0.65 IF Sprint 57.57 lands mixed-signal (1 IN + 1 OOB); pending direction-of-drift from Sprint 57.57 2nd data point. If Sprint 57.57 lands IN band → tier-4 SPLIT fully validated; only further OOB triggers need future tracking — carryover may close without successor)
- **`AD-AgentFactor-Tier-4-Structural-Action`** (CONDITIONAL CONTINUE — IF Sprint 57.57+57.58 hits 2 consec > 1.20 OR 2 consec < 0.7 → propose structural action; otherwise REMAINS LATENT)
- **`AD-Quotas-LiveUsageTracking-Phase58`** (Sprint 57.56 carryover continues — Phase 58+ deeper extension; expose QuotaEnforcer Redis counters at admin layer)
- **`AD-Quotas-UsageHistory-Phase58`** (Sprint 57.56 carryover continues)
- **`AD-Quotas-Alerting-Phase58`** (Sprint 57.56 carryover continues)
- **`AD-Quotas-RequestIncrease-Workflow-Phase58`** (Sprint 57.56 carryover continues)
- **`AD-Quotas-PlanUpgrade-AutoRollover-Phase58`** (Sprint 57.56 carryover continues)
- **`AD-Quotas-OptimisticConcurrency`** (Sprint 57.56 CONDITIONAL continues)
- **`AD-RateLimits-SyntaxValidation-Phase58`** (NEW — Phase 58+ extension; parse "100 / min" into structured `{limit: int, unit: "request", period: "minute"}`; currently raw display strings)
- **`AD-RateLimits-RuntimeEnforcement-Phase58`** (NEW — Phase 58+ extension; currently `tenant.meta_data["rate_limits"]` is admin display only; no runtime enforcement)
- **`AD-RateLimits-LiveUsageTracking-Phase58`** (NEW — Phase 58+ extension; analogous to Quotas live usage)
- **`AD-RateLimits-Alerting-Phase58`** (NEW — Phase 58+ extension)
- **`AD-RateLimits-DedicatedTable-Phase58`** (NEW CONDITIONAL — Sprint 57.48 D-DAY0-5 noted; Phase 58+ option if persistence requirements grow beyond JSONB; today: deferred)
- **`AD-RateLimits-OptimisticConcurrency`** (NEW CONDITIONAL — if Day 1 surfaces concurrent edit race conditions; Phase 58+ If-Match header pattern)
- **`AD-TenantSettings-Identity-Persistence-Phase58`** (Sprint 57.50 carryover continues; full SSO admin schema; broader scope than mechanical-greenfield)
- **`AD-Test-Cleanup-Pattern-Shared-Helper`** (Sprint 57.53-57.56 carryover continues; Phase 58.x — extract `_clear_committed_test_tenants` LIKE patterns to shared helper)
- **`AD-MediumBackend-AICadence-Recalibration`** (Sprint 57.53-57.56 carryover continues; Phase 58+)
- **`AD-medium-frontend-Baseline-Recalibration`** (Sprint 57.49-57.56 carryover continues; need consistent human-factor data point)
- **`AD-Day0-Prong1-Test-Glob-Multi-Pattern`** (Sprint 57.54-57.56 carryover continues — codify multi-pattern test file glob)
- **`AD-Phase58-Persistence-WriteSide-Pattern-Template`** (Sprint 57.54-57.56 carryover — pattern template now 4-data-point base after Sprint 57.57; can be used as reference template for Phase 58+ similar work)
- **CLOSED via Sprint 57.57 US-3 Day 2 PROMOTION bundle**: `AD-Plan-Workload-AgentDelegation-Explicit-Field-Codification` + `AD-Day0-Prong2-Phase58-WriteSide-Resource-Storage-Grep` + `AD-Day0-Prong2-CanonicalService-Grep`
- **CLOSED via Sprint 57.57 ship**: `AD-TenantSettings-RateLimits-Write-Endpoint` (Phase 58.x portfolio FINAL 4/4 — wave complete)
- Potential NEW from Sprint 57.57 Day 0/1 三-prong findings

---

**Modification History**:
- 2026-05-27: Sprint 57.57 Day 0.1 — Initial draft (RateLimits WRITE side Phase 58.x ship FINAL 4/4; mirror Sprint 57.56 structure verbatim with simplifications — no whitelist + no plan merge + no GET refactor; agent-delegated yes plan-time explicit field per Sprint 57.53+57.54+57.55+57.56 carryover AD; `mechanical-greenfield-design-decisions` 0.65 tier-4 2nd validation under tier-4 sub-class table NEW Sprint 57.55 retro Q4 ACTIVATION + Sprint 57.56 retro Q4 1st validation CONFIRMED CLEANLY; closes Sprint 57.56 carryover AD-AgentFactor-Tier-4-Validation-Sprint-57.57; Phase 58.x portfolio item 4/4 FINAL CLOSURE 🎉; tier-4 SPLIT 2nd validation rollback rule baseline pending; Day 2 docs track bundles 3 PROMOTION ADs per user 2026-05-27 selection)
