# Sprint 57.104 — Checklist (per-tenant model policy: meta_data["model_policy"] JSONB + resolver + TTL cache + pricing-validated admin PUT/GET + a tenant-settings Model Policy tab + per-request profile resolution — C1: the config-tiering spike that makes 57.97's env-only ModelProfile tenant-governable)

[Plan](./sprint-57-104-plan.md)

**Status**: ✅ COMPLETE (Day 0-4) — drive-through PASS. Backend `2816e883` + FE `ae2aed96` committed; closeout docs done. Merge-pending (NOT pushed — awaiting authorization).
**Branch**: `feature/sprint-57-104-per-tenant-model-policy`

---

## Day 0 — Plan-vs-Repo Verify + Branch ✅

### 0.1 Three-prong Day-0 verify (against HEAD `680bcd58`) — DONE, catalogued in progress.md D1-D10
- [x] **Prong 1 — path verify**: ModelPolicy home `adapters/_base/`; resolver `platform_layer/billing/model_policy.py` (no `config/` pkg — D1); `profile.py` / `handler.py` / `admin/tenants.py` / `pricing.py` confirmed; test files pinned (D2/D5)
- [x] **Prong 2 — content verify**: `build_azure_model_profile` 2 callers (D2); `AzureOpenAIConfig` None-overrides-to-None → pass concrete/omit (D3); `get_pricing_loader().get_llm_pricing("azure_openai", model)` + yaml keys + suffix-strip (D4); `_load_tenant_or_404`/`append_audit`/`require_admin_platform_role` + PUT /quotas骨架 (D5); cost_ledger sub_type ← `event.model` not env (D6 — simpler); no clock helper → injectable clock (D7); handler :312/:320/:513 + tenant_id/db in scope (D8)
- [x] **Prong 2.5 — FE tree audit**: `TenantSettingsView` 6-tab IA + `QuotasTab`/`FeatureFlagsTab` edit modes exist; 0 model-policy FE refs (D9) → FE tab is a low-cost extension (user chose to include — US-6)
- [x] **Prong 3 — schema verify**: N/A (no DB / migration / ORM column / new wire schema — JSONB on existing `tenants.metadata`); `Tenant.meta_data` alias physical `metadata`, ORM-only writes (Risk Class D)
- [x] **Catalog drift** in progress.md Day 0 (D1-D10 + implications; D3/D6/D7 folded into plan §3; D9 → FE-scope decision)
- [x] **Go/no-go**: backend scope shift 0%; D9 FE-scope fork resolved by user (include tab) → full-stack GO

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-104-per-tenant-model-policy` (from `main` HEAD `680bcd58`)

---

## Day 1 — Backend: ModelPolicy + resolver + builder + wiring + governance API (US-1..US-5)

### 1.1 ModelPolicy value object (US-1)
- [x] **`ModelPolicy` frozen value object** (`adapters/_base/model_policy.py` — sibling, neutral)
  - `action_deployment / action_model / cheap_deployment / cheap_model: str | None = None`; `from_dict` / `to_dict` (drop None) / `is_empty`
  - DoD: neutral (no provider import); mypy green; `check_llm_sdk_leak` green

### 1.2 Resolver + TTL cache (US-1)
- [x] **`resolve_tenant_model_policy(db, tenant_id)` + TTL-cache class (injectable clock) + `invalidate_tenant_model_policy`** (`platform_layer/billing/model_policy.py`)
  - reads `tenant.meta_data.get("model_policy", {})` → `ModelPolicy.from_dict`; ~60s TTL; tenant-scoped; injectable clock (default `time.monotonic` — D7)
  - DoD: mypy green; `check_cross_category_import` green (imports only the neutral value object)
- [x] **Autouse reset fixture** (Risk Class C) — clears the cache singleton between tests

### 1.3 Azure profile builder honors the policy (US-2)
- [x] **`build_azure_model_profile(policy=…)`** (`adapters/azure_openai/profile.py`)
  - build action + cheap from `policy.*` ∪ env; **conditional kwargs** (concrete string OR omit — never None per D3); `policy is None / is_empty()` → byte-identical to 57.97 (`cheap is action` collapse)
  - CONVERT the 2 callers (handler:320 + test_profile.py) to the new signature (Never-Delete)
  - DoD: mypy green; all-None byte-identical test green

### 1.4 Per-request resolution wiring (US-3)
- [x] **`build_real_llm_handler` resolves the tenant policy** (`handler.py:312-320`) + router resolves before build_handler
  - `policy = await resolve_tenant_model_policy(db, tenant_id) if tenant_id else None`; `profile = build_azure_model_profile(policy)`; `chat_client = profile.action`; verifier keeps `profile.cheap`
  - D6: cost_ledger sub_type flows from `event.model` automatically (no router wiring)
  - DoD: mypy green; existing chat tests stay green

### 1.5 Admin write-side (US-4)
- [x] **`PUT /{tenant_id}/model-policy`** (`api/v1/admin/tenants.py`)
  - `ModelPolicyUpsertRequest(extra="forbid")`; pricing validation → 422 on unknown/unpriced `*_model` (`get_llm_pricing("azure_openai", model)` is None)
  - `Depends(require_admin_platform_role)` + `_load_tenant_or_404`; meta_data identity-swap write; `append_audit(operation="tenant_model_policy_upsert", …)`; `db.commit()`; `invalidate_tenant_model_policy(tenant_id)`; `db.refresh`; `ModelPolicyResponse`
  - DoD: mypy green; route registered

### 1.6 Admin read-side (US-5)
- [x] **`GET /{tenant_id}/model-policy`** (`api/v1/admin/tenants.py`)
  - `Depends(require_admin_platform_role)` + `_load_tenant_or_404` → stored overrides ∪ env defaults; no audit (GET read-only precedent — D5)
  - DoD: mypy green

---

## Day 2 — FE Model Policy tab + all tests (US-6 + backend/FE tests)

### 2.1 FE Day-0 (tab-specific) — pin before code
- [x] Pinned `TenantSettingsView` tab registration + `QuotasTab` view/edit pattern + service + hooks (no i18n layer — inline English literals, matches QuotasTab) + operator-portal style authority (no model-policy mockup → mirror QuotasTab)

### 2.2 FE service + tab (US-6)
- [x] **`getModelPolicy` + `putModelPolicy`** (tenant-settings admin service) → `GET`/`PUT /api/v1/admin/tenants/{id}/model-policy` (snake↔camel + composite-replace blank-drop + 422 detail surfacing)
- [x] **`ModelPolicyTab.tsx`** (NEW, mirror `QuotasTab`) + `useModelPolicy`/`useModelPolicySave` hooks: view (null→"System default"); edit 4 fields; Save → PUT; unknown-model 422 inline banner; no dead control
- [x] **Register tab** in `TenantSettingsView.tsx` (6 → 7 tabs, after Quotas) + English inline copy
  - DoD: `npm run build` ✓ (exit 0); `npm run lint` (no `--silent`) exit 0 — both parent-re-verified

### 2.3 Tests (US-1..US-6)
- [x] **Backend** resolver: absent → `is_empty`; present → parsed; TTL hit/miss (injected clock); `invalidate` re-reads; autouse reset isolates singleton (11 tests)
- [x] **Backend** builder: all-None byte-identical; action override → tenant deployment; cheap override → distinct cheap adapter; None never passed to `AzureOpenAIConfig` (8 tests; value-object 8 tests)
- [x] **Backend** model-policy endpoints (13 integration tests): PUT 200/persists/audits/invalidates · 422 unpriced model · 404 missing · `extra="forbid"` 422 · composite-replace/clear · isolation · GET stored(sparse)/404/empty · admin gate (401 no-auth) — GET returns stored overrides (not ∪defaults; UI shows "system default" for unset)
- [ ] **Backend** wiring: `build_real_llm_handler(tenant_id with policy)` → profile action deployment == tenant's — 🚧 DEFERRED to Day-3 drive-through (build_real_llm_handler heavy to mock; the 2-line router→handler→builder threading is mypy-checked + the pieces are unit-tested + drive-through proves end-to-end)
- [x] **Frontend Vitest**: `ModelPolicyTab` view/edit/Save/422 (14) + service mapping (5) + `TenantSettingsView` registration; full suite **809 passed / 136 files** (parent-re-verified)

---

## Day 3 — Full regression + drive-through (US-7) + CHANGE-071 + design note + 17.md

### 3.1 Full gate sweep
- [x] `black . && isort . && flake8 .` (src tests) clean
- [x] `mypy src` 0 errors (0/357)
- [x] `python scripts/lint/run_all.py` 10/10 (event count UNCHANGED; `check_llm_sdk_leak` 0; `check_cross_category_import` green)
- [x] full `pytest` green — unit 27 + integration 13 (0 deletions)
- [x] frontend `npm run lint` (exit 0, no `--silent`) + `npm run build` ✓ + Vitest 809/136 + `check:mockup-fidelity` 53 (operator tabs not in the customer-mockup baseline) — parent-re-verified
- [x] `git diff` confirms `loop.py` / DB / migration / generated wire schema diff = 0

### 3.2 Drive-through (US-7 — per-tenant model differentiation, set via the tab) — PASS
- [x] Clean restart (Risk Class E): killed stale PID 16496 (prior-session B2b, no C1); fresh no-reload PID 35340 sole :8000 owner ("pricing loader wired" + "billing outbox drainer started"); frontend node :3007 untouched
- [x] Confirmed 2 real Azure deployments (gpt-5.4-nano + gpt-5.4-mini, both priced) — **single-tenant two-policies** flow chosen (stronger than two static tenants: also proves cache invalidation)
- [x] Real UI (dev-login `platform_admin`): acme-prod Model Policy tab → set `action_deployment`=gpt-5.4-nano → Save → persists across reload (GET re-fetch)
- [x] Real chat UI (real_llm) + real Azure: chat ("capital of France?"→Paris) → action turn on the nano policy
- [x] `cost_ledger`: action sub_type `azure_openai_gpt-5.4-nano` (vs pre-C1 baseline `gpt-5.2`); after changing the policy to mini via the tab → 2nd chat action sub_type `azure_openai_gpt-5.4-mini` (= **cache invalidation** proven) — query in progress.md Day 3 table
- [x] In the tab, set an unknown model (`bogus-model-xyz`) → **422 surfaced inline** "Save failed: Unknown/unpriced model…", stays in edit, policy unchanged
- [x] Screenshots (`artifacts/dt57104-{1,2,3,4}.png`) + observed-vs-intended in progress.md Day 3; acme-prod cleared back to default (composite-replace clear path also driven)

### 3.3 CHANGE-071 + design note + 17.md
- [x] `CHANGE-071-per-tenant-model-policy.md` (problem / design / verification / impact + the RBAC prod-OIDC open invariant)
- [x] **NEW design note `27-per-tenant-model-policy-design.md`** — §Step 5.5 spike requirement; 8-point quality gate ✅ (~95% verified)
- [x] 17.md: `ModelPolicy` value object + `resolve_tenant_model_policy` + model-policy endpoints (single-source row added)

---

## Day 4 — Closeout (spike sprint — design note required)

### 4.1 Closeout
- [x] progress.md Day 0-3 + drive-through complete
- [x] retrospective.md Q1-Q7 (Q2 calibration; design-note 8-point gate record per §Step 5.5; the D9 FE-scope mid-Day-0 correction lesson)
- [x] CLAUDE.md Current Sprint + Last Updated (lean, per §Sprint Closeout policy)
- [x] MEMORY.md pointer + `project_phase57_104_per_tenant_model_policy.md` subfile
- [x] next-phase-candidates.md: C1 ✅ done; soft-prereq RESOLVED-for-C1 note; remaining C2/C3/C4 + the RBAC-JWT-wiring slice
- [x] sprint-workflow.md calibration row `config-tiering-model-policy-spike 0.60` (1st data point)
- [x] all checklist items `[x]` or 🚧 (the Day-1 wiring unit test was 🚧 DEFERRED → now drive-through-proven; never deleted unchecked)
