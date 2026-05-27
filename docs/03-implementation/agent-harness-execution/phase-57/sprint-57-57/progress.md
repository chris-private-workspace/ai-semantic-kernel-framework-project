# Sprint 57.57 Progress — RateLimits Admin Write Endpoint + Frontend Edit Mode (Phase 58.x WRITE side 4/4 FINAL)

**Sprint**: 57.57
**Phase**: 57+ Frontend SaaS / Phase 58.x portfolio (FINAL 4/4 — closes WRITE-side wave)
**Branch**: `feature/sprint-57-57-rate-limits-write-endpoint` (from main `7daaa66f` post Sprint 57.56 PR #206 merge)
**Date**: 2026-05-27 (Sprint 57.56 closeout same-day continuation)
**Plan**: [sprint-57-57-plan.md](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-57-plan.md)
**Checklist**: [sprint-57-57-checklist.md](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-57-checklist.md)

---

## Day 0 — Plan + 三-Prong Verify (2026-05-27)

### 0.1 Plan + Checklist drafting ✅

- **Plan** written: `sprint-57-57-plan.md` (mirror Sprint 57.56 structure verbatim — 9 sections; sections 4.1-4.7 simplified per RateLimits architectural deltas no whitelist/no plan merge/no GET refactor; Day 2 docs track NEW US-3 for 3 PROMOTION bundle per user 2026-05-27 selection)
- **Checklist** written: `sprint-57-57-checklist.md` (mirror Sprint 57.56 Day 0-2 structure verbatim; Day 2.4 NEW PROMOTION codification section)

### 0.2 User scope decisions (AskUserQuestion 4×; all Recommended selected)

User confirmed 4 scope decisions at Day 0 BEFORE plan v1 draft (per Sprint 57.55 D-DAY0-B RED lesson — avoid rewriting plan after pivot):

1. **List semantics**: Composite-replace (whole list replacement; PUT body 帶完整 list = 新狀態; missing rows removed) — mirrors Sprint 57.54-57.56 composite-replace pattern
2. **UX**: Add Row + Remove Per Row + 允許 empty list save (= clear all overrides → backend fallback to DEFAULT_RATE_LIMITS)
3. **Bundle**: 3 PROMOTION ADs into Day 2 closeout docs track (~20-30 min extra cost; bundles AD-Plan-Workload-AgentDelegation-Explicit-Field-Codification + AD-Day0-Prong2-Phase58-WriteSide-Resource-Storage-Grep + AD-Day0-Prong2-CanonicalService-Grep)
4. **Row order**: Preserve insertion order (Python list + JSONB list both preserve order; UX expectation matches naturally)

### 0.8 Day 0 三-Prong Verify

**Prong 1 — Path Verify** (10/10 GREEN — pre-plan grep + Read-based verification):

| # | Finding | Status |
|---|---------|--------|
| Path-1 | `backend/src/infrastructure/db/models/identity.py::Tenant.meta_data` JSONB exists (Sprint 57.50+57.56 lesson) | ✅ |
| Path-2 | `backend/src/api/v1/admin/tenants.py` L1319-1384 Sprint 57.48 Track D RateLimits GET endpoint + `RateLimitItem` + `RateLimitListResponse` + `DEFAULT_RATE_LIMITS` fallback list | ✅ |
| Path-3 | `RateLimitItem` Pydantic at L1327-1331 = `{label: str, value: str}` with `ConfigDict(from_attributes=True)` — reusable verbatim for write schema items | ✅ |
| Path-4 | `DEFAULT_RATE_LIMITS` at L1341-1345 = hardcoded 3-item list mirroring `_fixtures.ts` RATE_LIMITS shape (`API requests` / `Tool calls` / `SSE connections`) | ✅ |
| Path-5 | `backend/tests/integration/api/test_admin_tenant_rate_limits.py` exists (Sprint 57.48 Day 1 GET tests; will extend with PUT tests) | ✅ |
| Path-6 | `backend/tests/integration/api/conftest.py` exists with `_clear_committed_test_tenants()` (LIKE prefix sweep extended Sprint 57.54+57.55+57.56) | ✅ |
| Path-7 | `frontend/src/features/tenant-settings/types.ts` exists — `RateLimitItem` + `RateLimitListResponse` declared (Sprint 57.49) | ✅ |
| Path-8 | `frontend/src/features/tenant-settings/services/tenantSettingsService.ts` exists with `fetchRateLimits` + Sprint 57.56 `saveQuotaOverrides` template precedent | ✅ |
| Path-9 | `frontend/src/features/tenant-settings/hooks/useRateLimits.ts` exists — `RATE_LIMITS_QUERY_KEY_BASE` declared | ✅ |
| Path-10 | `frontend/src/features/tenant-settings/components/tabs/QuotasTab.tsx` exists; Sprint 57.49 read-only + Sprint 57.56 Usage quotas Card edit mode added — Sprint 57.57 will add **RateLimits Card edit mode** (reverse scope guard) | ✅ |

**Prong 2 — Content Verify** (5 NOTABLE; 0 RED; per Sprint 57.55 D-DAY0-B RED lesson — done pre-plan to avoid post-plan rework):

- **D-DAY0-A** ✅ GREEN — Storage path `tenant.meta_data["rate_limits"]` confirmed in `admin/tenants.py` L1368-1370 (Sprint 57.48 Track D read path uses same key). WRITE side simply extends existing read into write-back. **NO storage architecture mid-plan pivot needed** — validates `AD-Day0-Prong2-Phase58-WriteSide-Resource-Storage-Grep` promotion rule (Sprint 57.57 = no D-DAY0 RED on this dimension because storage was already explicit since Sprint 57.48; 3-data-point cross-sprint evidence reached: Sprint 57.55 RED + 57.56 RED + 57.57 GREEN).

- **D-DAY0-B** ✅ GREEN — NO canonical service like Sprint 57.54 (`DBHITLPolicyStore.put()`) or Sprint 57.55 (`FeatureFlagsService.set_tenant_override`); Sprint 57.57 uses **direct ORM UPDATE** on tenants row + manual `append_audit` (Sprint 57.3 PATCH + Sprint 57.56 precedent verbatim mirror). **Inverse-validates** Sprint 57.55 `AD-Day0-Prong2-CanonicalService-Grep` promotion rule (2nd data point both directions actionable: Sprint 57.55 found canonical → simplified plan; Sprint 57.56+57.57 found NO canonical → simplified to direct ORM).

- **D-DAY0-C** 🆕 NOTABLE — RateLimits storage shape = **list of {label, value}** (free-form labels; NO whitelist like Sprint 57.56 Quotas 4-resource whitelist). Composite-replace semantics = whole list replacement. Pydantic `items: list[RateLimitItem]` reuses existing Sprint 57.48 `RateLimitItem` Pydantic verbatim — no new RateLimitItem shape change.

- **D-DAY0-D** 🆕 NOTABLE — Variable-length list UX (add row / remove row / empty list save allowed) distinct from Sprint 57.54-57.56 fixed-schema patterns. NEW UX state design qualifies for `mechanical-greenfield-design-decisions` 0.65 tier-4 sub-class (not `-port-style` 0.45 which would require **NO** new UX state design).

- **D-DAY0-E** 🆕 NOTABLE — QuotasTab also renders Usage quotas Card combined (Sprint 57.49 + Sprint 57.56 added Usage Card edit mode). Sprint 57.57 scope guard: ONLY add edit mode to **RateLimits Card** (Usage quotas Card unchanged per **Sprint 57.56 scope guard reverse**); both Edit/Cancel/Save UIs coexist independently after Sprint 57.57 (state pairs isolated: `(qEditing, qDraft)` Sprint 57.56 vs `(rlEditing, rlDraft)` Sprint 57.57).

- **D-DAY0-F** ✅ GREEN — `RATE_LIMITS_QUERY_KEY_BASE` at `useRateLimits.ts` confirmed; mutation hook will use `[...RATE_LIMITS_QUERY_KEY_BASE, tenantId]` (mirror Sprint 57.56 `useQuotasSave` invalidation pattern verbatim).

- **D-DAY0-G** ✅ GREEN — `saveQuotaOverrides` Sprint 57.56 precedent in `tenantSettingsService.ts` is direct pattern reuse for `saveRateLimits`; `useQuotasSave` Sprint 57.56 hook is direct mirror precedent for `useRateLimitsSave`.

- **D-DAY0-H** ✅ GREEN — Pydantic `BaseModel` + `ConfigDict` + `Field` already imported at `admin/tenants.py` L78 (no new imports needed for `RateLimitsUpsertRequest`/`Response`).

- **D-DAY0-I** ✅ GREEN — `append_audit` helper name (NOT `audit_log_append`) per Sprint 57.56 D-DAY1-1 fix-forward already corrected in plan §4.1.

- **D-DAY0-J** ✅ GREEN — pytest baseline 1796 PASS predicts +8 to +10 → 1804-1806 PASS; Vitest baseline 645 PASS predicts +8 to +13 → 653-658 PASS; HEX_OKLCH baseline 47 preserved target (13 consecutive sprints 57.45-57.57 DUAL CLEAN target).

**Prong 2.5 — Frontend Tree Depth Audit** (3/3 GREEN — Sprint 57.40 AD-Plan-5 fold-in):

- **D-DAY0-K** ✅ GREEN — QuotasTab depth-1 imports clean: Button/Card (mockup-ui) + BackendGapBanner (ui/) + useQuotas + useRateLimits + useQuotasSave (Sprint 57.56); no deeper feature-area imports.
- **D-DAY0-L** ✅ GREEN — Anti-pattern grep clean: 0 shadcn-utility tokens; existing inline `style={{...}}` all have `eslint-disable-next-line no-restricted-syntax`; no outer wrapper; layout-class N/A.
- **D-DAY0-M** ✅ GREEN — Edit mode UI will use existing primitives + `--btn-primary`/`--danger`/`--info` tokens (Sprint 57.54-57.56 precedent); HEX_OKLCH baseline 47 preserved target.

**Prong 3 — Schema Verify** (5/5 GREEN — AD-Plan-4 promotion):

- **D-DAY0-N** ✅ GREEN — `tenants.meta_data` JSONB column exists (default `{}`); per `09-db-schema-design.md §Group 1 Identity & Tenancy` ORM lives in `identity.py`.
- **D-DAY0-O** ✅ GREEN — Namespace key `"rate_limits"` already used by Sprint 57.48 Track D read; distinct from existing meta_data keys: `"identity"` (Sprint 57.50) + `"quota_overrides"` (Sprint 57.56); no collision.
- **D-DAY0-P** ✅ GREEN — No FK CASCADE from `tenants.meta_data` JSONB to audit_log; audit chain emitted via direct `append_audit` call (Sprint 57.3 + 57.56 precedent).
- **D-DAY0-Q** ✅ GREEN — Alembic head 0018; **no NEW migration needed** in Sprint 57.57 (tenants table + meta_data JSONB + namespace key all already exist).
- **D-DAY0-R** ✅ GREEN — tenants table is global no-RLS (per Sprint 57.48 D-DAY0-3 + 53.7 §Risk Class C); multi-tenant isolation enforced at `require_admin_platform_role` auth + path tenant_id check.

### 0.9 Drift findings catalog summary

**Total**: 18 catalogued (13 GREEN + 0 🔴 RED + 5 🆕 NOTABLE)

**Notable patterns** (3 GENERALIZED LESSONS for the 3 PROMOTION ADs to be codified Day 2):

1. **Storage-path explicit since prior sprint** (D-DAY0-A): When Phase 58.x WRITE-side ships are sequenced (Sprint 57.54+57.55+57.56+57.57), each new sprint's storage architecture should be **established by prior sprint's read endpoint** (Sprint 57.48 Track D for RateLimits) — eliminating mid-plan storage-path pivots. Codify as `AD-Day0-Prong2-Phase58-WriteSide-Resource-Storage-Grep` Drift Class row in §Step 2.5 Prong 2 table.

2. **Canonical service path both directions actionable** (D-DAY0-B): Sprint 57.55 D-DAY0-T (positive — found `FeatureFlagsService.set_tenant_override`) + Sprint 57.56 D-DAY0-D (inverse — no canonical service, direct ORM path) + Sprint 57.57 (inverse continued — no canonical service). The grep produces actionable plan pivots in BOTH directions: exists → use canonical method (simpler endpoint code); doesn't exist → direct ORM UPDATE pattern. Codify as `AD-Day0-Prong2-CanonicalService-Grep` Drift Class row.

3. **Plan-time agent-delegated explicit field 4-data-point reached** (plan-time tracking): Sprint 57.53+57.54+57.55+57.56+57.57 all include explicit "Agent-delegated: yes / no / partial" field in §Workload 4-segment form. 5-consecutive-sprint usage confirms the proposed mandatory rule produces actionable plan-time information. Codify as MANDATORY rule via `AD-Plan-Workload-AgentDelegation-Explicit-Field-Codification`.

### 0.10 Go/no-go decision

**GO** ✅ — 0 blocking RED findings; sprint scope/class/workload all consistent with Sprint 57.56 template; user 4-question scope confirmation locked Day 0 BEFORE plan v1 (zero plan-rework cycle).

### 0.11 Branch + Day 0 commit prep

- Branch: `feature/sprint-57-57-rate-limits-write-endpoint` created from main `7daaa66f` ✅
- Day 0 + Day 1 combined commit pattern (per Sprint 57.46-57.56 small-scope precedent)
- Next: User approval gate → Day 1 sequential agent delegation (Track A backend → Track B frontend)

---

## Day 1 — Implementation (2026-05-27; sequential agent delegation; 20th + 21st consecutive code-implementer)

### 1.1 Track A — Backend (code-implementer agent; ~25 min wall-clock; 20th consecutive) ✅

**Files modified** (3 backend EDIT only; NO frontend; NO new source files):
- `backend/src/api/v1/admin/tenants.py` (+110 lines): NEW `RateLimitsUpsertRequest` + `RateLimitsUpsertResponse` Pydantic + `upsert_tenant_rate_limits` PUT endpoint via dict-identity-swap pattern + manual `append_audit("tenant_rate_limits_upsert")` chain + MHist 1-line entry
- `backend/tests/integration/api/test_admin_tenant_rate_limits.py` (+209 lines): 10 NEW PUT tests + `select`/`AuditLog` imports + `_unique_code()` helper with `RATE_PUT_` prefix + MHist 1-line entry
- `backend/tests/integration/api/conftest.py` (+2 lines): `RATE_PUT_%` LIKE sweep in `_clear_committed_test_tenants()` + MHist 1-line entry

**Verification (Track A pre-handoff)**:
- `pytest test_admin_tenant_rate_limits.py -v` — **16 PASS** (6 GET + 10 NEW PUT) in 2.61s
- `pytest --tb=line -q` (full suite) — **1806 PASS / 4 skip / 0 fail** in 69s (1796 baseline + 10 new; exact target)
- `mypy --strict src/` — 0 errors / 310 source files
- `black + isort + flake8` — all clean
- `python scripts/lint/run_all.py` — 9/9 GREEN in 1.04s

**No D-DAY1 drift findings**: Pattern mirror Sprint 57.56 Quotas verbatim succeeded; helper name `append_audit` (Sprint 57.56 D-DAY1-1 fix-forward already corrected in plan §4.1); RateLimitItem reuse from Sprint 57.48 Track D successful.

### 1.2 Track B — Frontend (code-implementer agent; ~30 min wall-clock; 21st consecutive) ✅

**Files modified** (7 frontend total: 5 EDIT + 2 NEW):
- **EDIT** `frontend/src/features/tenant-settings/types.ts` (+12 lines): `RateLimitsUpsertRequest` + `RateLimitsUpsertResponse` types + MHist
- **EDIT** `frontend/src/features/tenant-settings/services/tenantSettingsService.ts` (+20 lines): `saveRateLimits` PUT func + 2 type imports + MHist
- **NEW** `frontend/src/features/tenant-settings/hooks/useRateLimitsSave.ts` (~45 lines): verbatim mirror of Sprint 57.56 `useQuotasSave.ts` + full file header
- **EDIT** `frontend/src/features/tenant-settings/components/tabs/QuotasTab.tsx` (+118 net): NEW `rlEditing`/`rlDraft` state pair + 6 handlers + read/edit branching on RateLimits Card + softened BackendGapBanner (2 banners now: Usage Card + RateLimits Card both softened) + **Usage quotas Card UNCHANGED bit-for-bit (Sprint 57.56 edit mode preserved)**; Karpathy §3 cleanup: removed obsolete `handleRequestIncrease` window.alert placeholder + its Vitest test (backend PUT now real → no placeholder needed)
- **NEW** `frontend/tests/unit/tenant-settings/useRateLimitsSave.test.tsx` (~110 lines, 3 hook tests)
- **EDIT** `frontend/tests/unit/tenant-settings/tenantSettingsService.test.ts` (+44 lines, 2 saveRateLimits tests)
- **EDIT** `frontend/tests/unit/tenant-settings/tabs/QuotasTab.test.tsx` (+180 lines): 13 NEW RateLimits edit-mode tests + Usage Card scope-guard assertion + fixed Sprint 57.56 banner test (now uses `getAllByTestId[0]` for 2-banner reality)

**Verification (Track B pre-handoff)**:
- `npm run lint` — 0 ESLint errors (only pre-existing `jsx-ast-utils` TS plugin warnings unrelated)
- `npm run build` — built in 3.56s; tsc strict 0 errors; Vite bundle clean
- `npm run test -- --run` — **663 PASS / 0 FAIL / 122 test files** in 17.77s

**Test count delta**: Vitest 645 → **663 PASS** (+18 NEW; over plan +5-8 by 10-13 acceptable per Sprint 57.56 precedent +15). Breakdown: 3 hook tests + 2 service tests + 13 tab tests = 18 total NEW.

**HEX_OKLCH baseline preserved**: 0 NEW `oklch(` literals in QuotasTab.tsx (verified via grep); all RateLimits Card colors use existing `var(--btn-primary)` / `var(--danger)` / `var(--info)` / `var(--success)` / `var(--fg)` tokens; all NEW inline `style={{...}}` blocks carry `eslint-disable-next-line no-restricted-syntax` comments per AD-Pre-Push-Lint-Silent-Suppression discipline.

**Notable observation (D-DAY1-2 NOTABLE — Karpathy §3 cleanup)**: Track B agent identified obsolete `handleRequestIncrease` function (was `window.alert` placeholder for "Request increase" button) — since backend PUT now real-backed, the placeholder is dead code. Agent removed function + JSX + corresponding Vitest test. This is the correct Karpathy §3 dead-code-cleanup outcome (no orphan code preserved). Recorded as positive observation NOT regression.

### 1.3 Day 1 Full Validation Sweep (cross-track confirm) ✅

| Check | Result |
|-------|--------|
| `pytest --tb=line -q` (full suite) | **1806 PASS / 4 skip / 0 fail** (1796 baseline + 10 NEW; exact target hit) in 69.94s |
| `python scripts/lint/run_all.py` (9 V2 lints) | **9/9 GREEN** in 1.04s |
| `git status --short` | 8 modified (3 backend + 5 frontend) + 4 untracked (sprint-57-57 execution dir + plan + checklist + useRateLimitsSave.test.tsx; NEW useRateLimitsSave.ts already tracked) |

**Usage quotas Card UNCHANGED scope guard verified**: Sprint 57.56 edit mode UI (qEditing/qDraft state + Save/Cancel/Edit buttons + per-resource numeric inputs + Sprint 57.56 BackendGapBanner copy) all preserved bit-for-bit; Vitest assertion test explicitly confirms `quotas-edit-btn` test-id remains functional even while RateLimits Card is in edit mode (independent state pairs).

**Mockup-fidelity DUAL CLEAN preserved**: HEX_OKLCH baseline 47 unchanged through Sprint 57.57; this becomes **13 consecutive sprints 57.45-57.57 DUAL CLEAN streak preserved** (per AC-28).

### 1.4 Day 1 commit (Day 0 + Day 1 combined per Sprint 57.46-57.56 small-scope precedent)

🚧 **Pending bash call** — combined Day 0 + Day 1 commit staged with all 12 files + sprint artifacts.

---

## Day 1 Sprint-aggregate metrics

| Metric | Sprint 57.56 (Quotas) | Sprint 57.57 (RateLimits) | Delta |
|--------|----------------------|---------------------------|-------|
| Pytest delta | +12 (1784→1796) | **+10** (1796→1806) | -2 (no plan-default merge tests needed) |
| Vitest delta | +15 (630→645) | **+18** (645→663) | +3 (variable-length list UX coverage) |
| Backend files | 3 EDIT (no NEW) | **3 EDIT** (no NEW) | same |
| Frontend files | 7 (5 EDIT + 2 NEW) | **7** (5 EDIT + 2 NEW) | same |
| Track A wall-clock | ~25 min | **~25 min** | same |
| Track B wall-clock | ~25-30 min | **~30 min** | similar |
| Total agent delegation | ~50-55 min | **~55 min** | similar |
| Code-implementer count | 18th + 19th | **20th + 21st** consecutive | chain extended |

### Day 1 wall-clock breakdown (estimated)

- Day 0 三-prong + plan/checklist + user scope confirmation (parent assistant): ~30 min
- Track A backend agent: ~25 min wall-clock
- Track B frontend agent: ~30 min wall-clock
- Day 1.3 validation sweep (parent assistant): ~3 min
- Day 1 progress + checklist updates (parent assistant): ~10 min
- **Day 1 total**: ~95-100 min (consistent with Sprint 57.56 ~90-100 min)

---

## Day 2 — Closeout (2026-05-27; parent assistant) ✅

Day 2 closeout work captured fully in [`retrospective.md`](./retrospective.md) Q1-Q7 6必答 format. Summary:

- **Retrospective Q1-Q7 written** (Q7 N/A SKIP 7th consecutive feature ship NOT spike per Sprint 57.52-57.56 precedent)
- **sprint-workflow.md 6 edits** ✅:
  - MHist prepend (Sprint 57.57 retro 1-line entry)
  - Matrix `medium-backend` 0.80 row → 10 data points
  - Matrix `medium-frontend` 0.65 row → 7 data points
  - §Active Activation history block 3 entries appended (Sprint 57.55 + 57.56 + 57.57 — backfilled DEFERRED backlog from prior closeouts)
  - **PROMOTION 1**: §Workload Calibration §Four-segment form MANDATORY `Agent-delegated:` plan-time field codification
  - **PROMOTION 2 + 3**: §Step 2.5 Prong 2 Drift Class table 2 NEW rows (Claimed-but-missing-storage-path + Claimed-but-missing-canonical-service)
- **Memory subfile** `project_phase57_57_rate_limits_write_endpoint.md` ✅
- **MEMORY.md pointer** prepended at TOP of §Project — Recent Sprints (~700 char + keywords block) ✅
- **CLAUDE.md** Current Sprint row + Last Updated footer updated (navigator-only per Sprint Closeout Policy) ✅
- **next-phase-candidates.md** Updated header + NEW Sprint 57.57 Carryover section + Sprint 57.56 demoted ✅
- **CHANGE-027** feature change record created ✅
- **Checklist Day 2** items marked `[x]` ✅
- **Day 2 wall-clock**: ~30-35 min (heavier than Sprint 57.56 by ~5-10 min due to 3 PROMOTION docs edits + retro Q3 5-lesson capture)

### Sprint-aggregate totals

| Metric | Value |
|--------|-------|
| Pytest delta | +10 (1796→1806; exact target hit) |
| Vitest delta | +18 (645→663; over plan +5-8 by 10-13 acceptable per Sprint 57.56 +15 precedent) |
| mypy --strict | 0 errors / 310 source files |
| 9 V2 lints | 9/9 GREEN in 1.04s |
| Vite build | 3.56s clean / tsc strict 0 errors |
| HEX_OKLCH baseline | 47 unchanged (13 consecutive sprints 57.45-57.57 DUAL CLEAN — strongest streak Phase 57+) |
| Day 0+1 commit | `08695112` (13 files +2022/-44) |
| Total wall-clock | ~125-130 min (~2.08-2.17 hr) |
| Ratio actual/agent-adjusted | ~1.15 ✅ IN BAND top edge [0.85, 1.20] |
| Tier-4 SPLIT outcome | **FULLY VALIDATED** with 2 consec IN band (57.56=1.02 + 57.57=1.15) |
| Phase 58.x portfolio | **4/4 FINAL CLOSURE 🎉** (HITLPolicies + FeatureFlags + Quotas + RateLimits all closed) |
| ADs CLOSED simultaneously | 5 (1 tier-4 validation + 1 portfolio FINAL + 3 PROMOTIONS) |
| NEW carryover ADs | 6 (5 Phase 58+ RateLimits extensions + 1 tier-4 Sprint 57.58 conditional) |

### Day 2 commit pending

🚧 Day 2 closeout commit staged for next bash call. Commit message captures tier-4 SPLIT FULLY VALIDATED + Phase 58.x portfolio FINAL CLOSURE 🎉 + DUAL CLEAN 13 consecutive + 20th+21st code-implementer chain + 3 PROMOTION docs track codified zero codification debt.

