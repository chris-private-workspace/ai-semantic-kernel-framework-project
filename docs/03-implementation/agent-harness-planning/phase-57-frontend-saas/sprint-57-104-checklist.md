# Sprint 57.104 — Checklist (per-tenant model policy: meta_data["model_policy"] JSONB + resolver + TTL cache + pricing-validated admin PUT/GET + a tenant-settings Model Policy tab + per-request profile resolution — C1: the config-tiering spike that makes 57.97's env-only ModelProfile tenant-governable)

[Plan](./sprint-57-104-plan.md)

**Status**: Day 1 complete (backend US-1..US-5 + tests green: mypy 0/357 · run_all 10/10 · unit 27 · integration 13); Day 2 (FE tab) next
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
- [ ] Pin `TenantSettingsView` tab registration shape + `QuotasTab` view/edit pattern + the tenant-settings admin service file (`getQuotas`/`putQuotas` analog) + i18n file + the operator-portal style authority (confirm no model-policy mockup; mirror QuotasTab)

### 2.2 FE service + tab (US-6)
- [ ] **`getModelPolicy` + `putModelPolicy`** (tenant-settings admin service) → `GET`/`PUT /api/v1/admin/tenants/{id}/model-policy`
- [ ] **`ModelPolicyTab.tsx`** (NEW, mirror `QuotasTab`): view effective policy; edit 4 fields; Save → PUT; unknown-model 422 inline error banner; no dead control
- [ ] **Register tab** in `TenantSettingsView.tsx` (6 → 7 tabs, after Quotas) + i18n labels (English copy convention)
  - DoD: `npm run build` ✓; `npm run lint` (no `--silent`) exit 0

### 2.3 Tests (US-1..US-6)
- [x] **Backend** resolver: absent → `is_empty`; present → parsed; TTL hit/miss (injected clock); `invalidate` re-reads; autouse reset isolates singleton (11 tests)
- [x] **Backend** builder: all-None byte-identical; action override → tenant deployment; cheap override → distinct cheap adapter; None never passed to `AzureOpenAIConfig` (8 tests; value-object 8 tests)
- [x] **Backend** model-policy endpoints (13 integration tests): PUT 200/persists/audits/invalidates · 422 unpriced model · 404 missing · `extra="forbid"` 422 · composite-replace/clear · isolation · GET stored(sparse)/404/empty · admin gate (401 no-auth) — GET returns stored overrides (not ∪defaults; UI shows "system default" for unset)
- [ ] **Backend** wiring: `build_real_llm_handler(tenant_id with policy)` → profile action deployment == tenant's — 🚧 DEFERRED to Day-3 drive-through (build_real_llm_handler heavy to mock; the 2-line router→handler→builder threading is mypy-checked + the pieces are unit-tested + drive-through proves end-to-end)
- [ ] **Frontend Vitest**: `ModelPolicyTab` view renders effective policy; edit → Save calls `putModelPolicy`; 422 surfaces inline; `TenantSettingsView` registers the tab

---

## Day 3 — Full regression + drive-through (US-7) + CHANGE-071 + design note + 17.md

### 3.1 Full gate sweep
- [ ] `black . && isort . && flake8 .` (src tests) clean
- [ ] `mypy src` 0 errors
- [ ] `python scripts/lint/run_all.py` 10/10 (event count UNCHANGED; `check_llm_sdk_leak` 0; `check_cross_category_import` green)
- [ ] full `pytest -q` green — (+N, 0 deletions)
- [ ] frontend `npm run lint` (exit 0, no `--silent`) + `npm run build` ✓ + Vitest (+N) + `check:mockup-fidelity` unchanged (operator tabs not in the customer-mockup baseline — confirm)
- [ ] `git diff` confirms `loop.py` / DB / migration / generated wire schema diff = 0

### 3.2 Drive-through (US-7 — two-tenant model differentiation, set via the tab)
- [ ] Clean restart (Risk Class E): kill stale uvicorn reloader + spawn-worker (`Get-CimInstance Win32_Process` PID/PPID/StartTime); fresh PID sole :8000 owner; frontend node untouched
- [ ] Confirm a 2nd real Azure deployment is available (cheap-tier deployment) → tenant A `action_deployment` = it; tenant B unset
- [ ] Real UI (dev-login `platform_admin`): open tenant A's Model Policy tab → set `action_deployment` → Save → GET/reload confirms persisted
- [ ] Real chat UI (real_llm) + real Azure: tenant A chat + tenant B chat, same prompt → both answer
- [ ] `cost_ledger` shows two different `azure_openai_{model}` sub_types (tenant A vs tenant B) — query + screenshot
- [ ] In the tab, set an unknown model → 422 surfaced inline + audit row
- [ ] Screenshots (tab edit + chat runs + cost ledger rows + 422) + observed-vs-intended in progress.md

### 3.3 CHANGE-071 + design note + 17.md
- [ ] `CHANGE-071-per-tenant-model-policy.md` (problem / design / verification / impact + the RBAC prod-OIDC open invariant)
- [ ] **NEW design note (config tiering + per-tenant model policy)** — §Step 5.5 spike requirement; pin the doc number (glob existing series); 8-point quality gate
- [ ] 17.md: `ModelPolicy` value object + `resolve_tenant_model_policy` + model-policy endpoints (single-source)

---

## Day 4 — Closeout (spike sprint — design note required)

### 4.1 Closeout
- [ ] progress.md Day 0-3 + drive-through complete
- [ ] retrospective.md Q1-Q7 (Q2 calibration; design-note 8-point gate record per §Step 5.5; the D9 FE-scope mid-Day-0 correction lesson)
- [ ] CLAUDE.md Current Sprint + Last Updated (lean, per §Sprint Closeout policy)
- [ ] MEMORY.md pointer + `project_phase57_104_per_tenant_model_policy.md` subfile
- [ ] next-phase-candidates.md: C1 done; remaining C2/C3/C4 + the RBAC-JWT-wiring slice
- [ ] sprint-workflow.md calibration row `config-tiering-model-policy-spike 0.60` (1st data point)
- [ ] all checklist items `[x]` or 🚧 (never deleted unchecked)
