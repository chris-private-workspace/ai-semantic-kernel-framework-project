# Sprint 57.104 Plan — per-tenant model policy: a tenant governs its own action/cheap LLM deployment via an admin-gated write-side, resolved per-request into the chat ModelProfile (C1: harness-deepening Workflow C slice C1 — the config-tiering spike that makes model selection tenant-governable, building on 57.97's env-only ModelProfile)

**Category / Scope**: 範疇 4 (Context Mgmt — model selection) × adapters (`build_azure_model_profile` extension) × platform_layer (tenant policy resolver + TTL cache) × api/v1/admin (governance write-side) — Phase 57 / Sprint 57.104
**Created**: 2026-06-11
**Status**: Draft
**Plan authority**: mirrors the most-recent completed sprint plan (`sprint-57-103-plan.md`, 9 sections 0-9). Scope differences expressed through content, not structure.

> **Modification History**
> - 2026-06-11: Initial draft (C1 — per-tenant model policy: meta_data["model_policy"] JSONB + resolver + TTL cache + admin PUT/GET + pricing-validated governance + per-request profile resolution)

---

## 0. Background

Sprint 57.97 (the multi-model profile spike) built `ModelProfile{action, cheap}` (`adapters/_base/model_profile.py:46-58`) and `build_azure_model_profile(strong_client)` (`adapters/azure_openai/profile.py:54-82`), which pairs the strong action-tier client with a cheap tier (the verification / llm_judge call routes to `profile.cheap`, `handler.py:~513`). But the model selection is **system-wide and env-only** (`AZURE_OPENAI_*` / `AZURE_OPENAI_CHEAP_*`): every tenant runs the same deployment. There is no governance seam for a tenant to run a different model.

C1 makes model selection **tenant-governable**: an admin sets a per-tenant `{action, cheap}` deployment/model policy; the policy is resolved per-request inside `build_real_llm_handler(tenant_id)` and built into that request's `ModelProfile`. This is the proposal's "config 分層 spike" (`harness-deepening-proposal-20260610.md §3.1-3.5`, slice C1) — the first config-tiering vertical, and the template the later C3 (verification/HITL/guardrail per-tenant policy) follows.

### Storage decision (proposal §3.2 — `meta_data["model_policy"]` JSONB)

Per the proposal's storage matrix, C1 stores the policy in `tenant.meta_data["model_policy"]` JSONB — the cheapest spike with zero migration, mirroring the `quota_overrides` (57.56) + `rate_limits` (pre-0019) precedents. Schema-less is acceptable for a spike; if the policy surface matures (C3 widens it) it graduates to a typed table, exactly as `rate_limits` did (meta_data → `rate_limit_configs` 0019-0021). `Policy shape v1` (model fields only): `{"action_deployment", "action_model", "cheap_deployment", "cheap_model"}` — every field optional (absent → env default). **On write, the policy is validated against `llm_pricing.yml`** (an unknown model is rejected 422) so the cost ledger never meets an unpriced model (a governance invariant: a tenant cannot route to a model billing can't price).

### RBAC soft-prereq resolution (decided Day-0; user-confirmed 2026-06-11)

C1's `PUT /api/v1/admin/tenants/{id}/model-policy` is gated by `require_admin_platform_role` (`platform_layer/identity/auth.py:142-154`), which (Path 1) reads the JWT `roles` claim. The proposal §3.4 flagged that the OIDC callback bakes `roles=["user"]` (`auth.py:302`) so a real-OIDC admin's JWT would 403 — an AP-4 Potemkin risk. **Day-0 evidence resolves this in C1's favour**: `_DEV_LOGIN_ROLES = ("user", "admin", "platform_admin")` (`auth.py:378`) — the dev-login JWT carries `platform_admin`, so the drive-through (dev-login → admin PUT → chat) walks end-to-end in dev, exactly the path that drive-through-verified the sibling admin PUTs (quotas/rate-limits/feature-flags, 57.55-57.57). The OIDC-callback hardcode is a **pre-existing, shared, production-OIDC-only** gap already affecting those 3 shipped endpoints; C1 neither introduces nor worsens it. It stays tracked as `AD-RBAC-DB-To-JWT-Wiring-Phase58` and is noted in §8 Risks — **NOT in C1 scope** (folding it in would expand C1 into IAM-test territory; per scope discipline it is its own slice). User confirmed "直接做 C1" (proceed; do not bundle RBAC-JWT wiring) on 2026-06-11.

### FE scope decision (admin model-policy tab IN SCOPE — user Day-0 decision 2026-06-11)

C1 is a config-tiering spike whose primary mass is backend (resolver + cache + builder + admin API). The plan's initial draft deferred the admin FE on a "no FE home / no mockup" assumption — **Day-0 D9 corrected this**: a tenant-settings operator IA already exists (`TenantSettingsView`, 6 tabs: General/Flags/Quotas/HITL/Members/Danger) with `QuotasTab` + `FeatureFlagsTab` carrying view/edit modes (57.56-57.57). Adding a 7th "Model Policy" tab mirroring `QuotasTab` is low-cost and makes the admin write **UI-drivable**, so the drive-through is UI-complete (set policy in the tab → run chats → cost_ledger differentiates) rather than API-set. The user chose to include the tab (Day-0 D9 decision). These operator tabs follow the operator-portal style authority (lower than the customer `reference/design-mockups/`), so mirroring the in-repo `QuotasTab` pattern — not inventing a mockup — is correct (§3.6). The drive-through still ultimately proves the **user-facing behavior C1 delivers**: a tenant's *chat* runs on the tenant's configured model (real chat UI + real Azure), with the differentiation visible in `cost_ledger` model sub_type.

### Ground truth (Day-0 head-start — 2 Explore recon agents + direct grep, file:line anchors on `main` HEAD `680bcd58` post-57.103-merge)

- **`ModelProfile`** — `adapters/_base/model_profile.py:46-58`: `frozen` dataclass `{action: ChatClient, cheap: ChatClient}`; when no cheap deployment configured `cheap is action` (same instance → byte-identical cost/behavior).
- **`build_azure_model_profile(strong_client)`** — `adapters/azure_openai/profile.py:54-82`: reads `AZURE_OPENAI_CHEAP_DEPLOYMENT_NAME` / `AZURE_OPENAI_CHEAP_MODEL_NAME` env; unset → `ModelProfile(action=strong_client, cheap=strong_client)`; set → builds a 2nd `AzureOpenAIAdapter(AzureOpenAIConfig(deployment_name=cheap_deployment, model_name=...))`.
- **`build_real_llm_handler`** — `handler.py:256-320`: called per-request by the router; already receives `tenant_id` + `db` params; builds `chat_client = AzureOpenAIAdapter(AzureOpenAIConfig())` (env default) then `profile = build_azure_model_profile(chat_client)` (~`:320`); `chat_client` IS `profile.action` and is used by loop / compactor / prompt builder / subagents; only the verifier registry uses `profile.cheap` (`make_chat_verifier_registry(profile.cheap, ...)`, ~`:513`). **This is where the per-tenant resolve plugs in** (tenant_id is in scope, profile is built here).
- **`AzureOpenAIConfig`** — env-default fields; `AzureOpenAIConfig()` reads env; `AzureOpenAIConfig(deployment_name=X, model_name=Y)` overrides. (Confirm in Day-0: does passing `deployment_name=None` fall back to env, or override-with-None? The resolver will pass concrete strings or omit, never None — pinned in §0.1 Prong 2.)
- **PUT /quotas skeleton (the cleanest borrowable骨架)** — `api/v1/admin/tenants.py:1394-1457`: Pydantic `QuotaOverridesUpsertRequest(model_config=ConfigDict(extra="forbid"))` + `field_validator` whitelist; handler `Depends(require_admin_platform_role)` + `_load_tenant_or_404`; **meta_data JSONB write** = `new_meta = dict(tenant.meta_data or {}); new_meta["quota_overrides"] = ...; tenant.meta_data = new_meta` (identity-swap, not in-place mutate, for ORM JSONB change detection); `await db.flush()`; **direct `append_audit(db, tenant_id=..., operation="tenant_quota_overrides_upsert", resource_type="tenant", resource_id=..., operation_data={...}, user_id=admin_user_id, operation_result="success")`**; `await db.commit()`; response projection.
- **pricing validation** — `platform_layer/billing/pricing.py:76-148`: `PricingLoader.get_llm_pricing(provider, model) -> LLMPricing | None` (None = unknown; handles Azure version suffix via `_strip_version_suffix`). The module accessor name (recon cited `get_pricing_loader()`) + the canonical `llm_pricing.yml` keys (`gpt-4o-mini / gpt-5.2 / gpt-5.4 / gpt-5.4-mini / gpt-5.4-nano / claude-3.7-sonnet`) → pin in Day-0.
- **cost_ledger model sub_type** — `cost_ledger.py:71-91` `sub_type: str`; `router.py:549-579` enqueues `sub_type=f"azure_openai_{model_name}"` for the action turn + `f"azure_openai_{model_name}_verification"` (idempotency suffix `_verification`) for the cheap verify turn. `model_name` comes from the adapter's response → **a tenant on a different action deployment yields a different `sub_type`** (the drive-through differentiation signal).
- **`Tenant.meta_data` ORM alias** — `identity.py:139-144`: `meta_data: Mapped[...] = mapped_column("metadata", JSONB, ...)` — Python attr `meta_data`, physical column `metadata`. ORM writes use `tenant.meta_data = ...`; any raw SQL must quote `"metadata"`. (C1 uses ORM only — no raw SQL — but pinned per Risk Class D.)
- **admin gate** — `require_admin_platform_role` (`platform_layer/identity/auth.py:142-154`) → `_require_role(request, {"admin","platform_admin"})`; Path 1 JWT-claim (dev-login carries both); Path 2 DB fallback gated by `Settings.rbac_db_backed_fallback` (default False, `core/config/__init__.py:71`).

### STALE / drift anchors to re-confirm in the formal Day-0 三-prong (§ checklist 0.1)

- The exact module + accessor for the pricing singleton (`get_pricing_loader()` vs a `Depends`-injected loader) + how the chat router currently obtains pricing — confirm before wiring the 422 validation.
- `build_azure_model_profile` caller set (handler + tests) — confirm count before reshaping the signature (Option A); pin the test files that construct profiles.
- `AzureOpenAIConfig` None-handling for `deployment_name` / `model_name` (env-fallback vs override-with-None) — the resolver must produce concrete strings or omit.
- The new resolver/cache module home (`platform_layer/<config|billing>/model_policy.py` vs a new `platform_layer/model_policy/`) + whether a `platform_layer/config/` package exists — pin the path (Prong 1).
- `_load_tenant_or_404` + `append_audit` + `require_admin_platform_role` import sites in `tenants.py` — confirm the exact symbols to reuse for the new endpoints.
- Whether an admin/operator tenant-detail FE page exists for the siblings (quotas/rate-limits/feature-flags) — confirms the §9 FE-deferral framing (Prong 2.5; if a trivially-extendable home with established styling exists, re-evaluate scope before Day-1).
- The router's per-request `model_name` source for the cost-ledger sub_type — confirm the action `model_name` flows from the resolved profile (not a hardcoded env read) so the differentiation actually shows.

---

## 1. Sprint Goal

A platform admin sets a per-tenant `{action, cheap}` model policy (deployment + model) via an admin-gated, pricing-validated write-side; the policy persists in `tenant.meta_data["model_policy"]`, is resolved per-request (TTL-cached, PUT-invalidated) inside `build_real_llm_handler`, and is built into that request's `ModelProfile` — so two tenants running the same prompt route to different Azure deployments and the `cost_ledger` model sub_type differs; an unknown (unpriced) model is rejected 422 with an audit row. `loop.py` untouched; no new wire event; no DB migration.

## 2. User Stories

- **US-1 (ModelPolicy value object + resolver + TTL cache)** — As the platform, I want a neutral `ModelPolicy` value object and a `resolve_tenant_model_policy(db, tenant_id)` that reads `tenant.meta_data["model_policy"]` behind a ~60s TTL cache (invalidated on write), so that per-request model resolution is cheap (one DB read per tenant per TTL window) and an absent policy resolves to "all defaults" (byte-identical to today's env-only path).
- **US-2 (Azure profile builder honors the policy)** — As the platform, I want `build_azure_model_profile` extended to build the action + cheap `ChatClient`s from a resolved `ModelPolicy` ∪ env defaults, so that a tenant's `action_deployment` / `cheap_deployment` overrides actually change which Azure deployment the loop + verifier call — and an all-None policy yields byte-identical behavior + cost to 57.97.
- **US-3 (per-request resolution wiring)** — As the platform, I want `build_real_llm_handler(tenant_id, db)` to resolve the tenant policy and build the per-tenant `ModelProfile`, so that the main loop / compactor / subagents run on the tenant's action model and the verifier on the tenant's cheap model, with the resolved `model_name` flowing into the `cost_ledger` sub_type.
- **US-4 (admin write-side — pricing-validated governance)** — As a platform admin, I want `PUT /api/v1/admin/tenants/{tenant_id}/model-policy` to upsert the policy into `tenant.meta_data["model_policy"]` with `append_audit`, rejecting an unknown/unpriced model 422 (validated against `llm_pricing.yml`), 404 for a missing/cross-tenant tenant, and `extra="forbid"` on the body, so that model governance is auditable and can never route a tenant to a model billing can't price.
- **US-5 (admin read-side)** — As a platform admin, I want `GET /api/v1/admin/tenants/{tenant_id}/model-policy` to return the tenant's current effective policy (stored overrides + resolved defaults), so that an operator can read-before-write and the drive-through can independently confirm persistence.
- **US-6 (admin FE model-policy tab)** — As a platform admin, I want a "Model Policy" tab in the existing tenant-settings IA (mirroring the `QuotasTab` view/edit pattern) so that I can read + edit a tenant's `{action, cheap}` deployment/model from the operator UI, with an unknown-model 422 surfaced inline (no dead control; gated by the existing admin route).
- **US-7 (drive-through)** — As the developer, I want a real UI + real Azure run where tenant A has a model policy (a 2nd real deployment) set via the new tab and tenant B does not, both running the same prompt, so that I observe two different `cost_ledger` model sub_types (proven driven, not gate-only), plus a 422 on an unknown model surfaced in the tab.

## 3. Technical Specifications

### 3.0 Architecture (resolve per-request → build the tenant ModelProfile; the admin write-side is a PUT /quotas sibling; `loop.py` untouched)

The resolution chain (proposal §3.3):

```
system defaults (AZURE_OPENAI_* env)
  → tenant override (tenant.meta_data["model_policy"], TTL-cached ~60s, PUT-invalidated)
  → build_real_llm_handler(tenant_id, db) resolves ModelPolicy
  → build_azure_model_profile(policy) builds {action, cheap} ChatClients (policy ∪ env)
  → ModelProfile threaded exactly as 57.97 (loop/compactor/subagents = action; verifier = cheap)
```

**Key design decision — how the tenant override reaches the profile build:**

| Option | Mechanism | Verdict |
|--------|-----------|---------|
| **A. Extend `build_azure_model_profile` to take a `ModelPolicy` and own BOTH action + cheap construction (CHOSEN)** | Signature `build_azure_model_profile(policy: ModelPolicy \| None = None) -> ModelProfile`. Builds action `AzureOpenAIAdapter(AzureOpenAIConfig(deployment_name=policy.action_deployment or <env default>, model_name=...))` + cheap from `policy.cheap_*` ∪ `AZURE_OPENAI_CHEAP_*` env ∪ (cheap is action). The handler resolves the policy, calls the builder, reads `chat_client = profile.action`. | ✅ Single source for all model-config resolution (action + cheap in one place). `policy is None` / all-None → byte-identical to 57.97 (env-only). Convert the ~2 callers (handler + tests; Never-Delete → convert). The builder already owns cheap construction → extending it to also own action construction is the natural shape, not a parallel path. |
| B. Handler builds the action client from policy; builder keeps `(strong_client, cheap_policy=…)` | Handler does `AzureOpenAIConfig(deployment_name=policy.action_deployment …)`; builder gets an extra cheap-override param | ❌ Splits model-config resolution across handler (action) + builder (cheap) — two places must agree on the env-fallback rule. A centralizes it. |
| C. New `build_tenant_model_profile` parallel function | Separate builder for the tenant path | ❌ AP-11 parallel path / two builders that drift; the env-only path becomes the "legacy" sibling. |
| D. Thread `ModelProfile` into the loop for per-turn model choice | Resolve at each turn | ❌ Explicitly out of scope (proposal §3.3 + §5): construction-time DI covers every real need; per-phase model choice is speculative (AP-6 / YAGNI). |

`loop.py` diff = 0; no new event TYPE; no codegen; no DB / migration (JSONB on the existing `tenants.metadata` column).

### 3.1 ModelPolicy value object + resolver + TTL cache (US-1)

- `backend/src/adapters/_base/model_profile.py` (or a sibling `model_policy.py`) — NEW `@dataclass(frozen=True) ModelPolicy` with `action_deployment: str | None`, `action_model: str | None`, `cheap_deployment: str | None`, `cheap_model: str | None` (all default None). A neutral value object (no provider import) co-located with `ModelProfile` so both adapters + platform_layer can import it from the neutral base. A `from_dict` / `to_dict` for the JSONB round-trip + an `is_empty` helper (all-None → the env-default path).
- `backend/src/platform_layer/billing/model_policy.py` (Day-0 D1: no `platform_layer/config/` exists → co-locate with `pricing.py` + `cost_ledger.py`) — NEW: `resolve_tenant_model_policy(db, tenant_id) -> ModelPolicy` reads `tenant.meta_data.get("model_policy", {})` → `ModelPolicy.from_dict(...)`; a small TTL-cache class holding `dict[UUID, tuple[ModelPolicy, float_expiry]]` (~60s) with an **injectable clock callable** (default `time.monotonic`) — Day-0 D7 found no module-wide clock helper exists (SessionRegistry uses bare `datetime.now(UTC)`), so the cache owns its clock for deterministic tests; `invalidate_tenant_model_policy(tenant_id)` drops the cache entry (called by the PUT). **Risk Class C**: a module singleton across test event loops → ship an autouse reset fixture (the `SessionRegistry` / `InjectionRegistry` precedent).
- Tenant scoping: the resolver is keyed by `tenant_id`; the DB read filters by `tenant_id` (multi-tenant 鐵律) via the existing `_load_tenant` path.

### 3.2 Azure profile builder honors the policy (US-2)

- `backend/src/adapters/azure_openai/profile.py` — extend `build_azure_model_profile` per Option A: accept `policy: ModelPolicy | None = None`; build the action client from `policy.action_*` ∪ env default, the cheap client from `policy.cheap_*` ∪ `AZURE_OPENAI_CHEAP_*` env ∪ (cheap is action). Preserve the 57.97 invariant: `policy is None or policy.is_empty()` → byte-identical to today (same `cheap is action` collapse when no cheap configured).
- **Day-0 D3 (load-bearing)**: `AzureOpenAIConfig` is a `BaseSettings` (`env_prefix="AZURE_OPENAI_"`); passing `deployment_name=None` OVERRIDES to None (no env fallback; field default is `""`). So the builder must build the config with **conditional kwargs**: include `deployment_name=` / `model_name=` ONLY when the policy field is a concrete string; OMIT the kwarg when None so `BaseSettings` reads the env default. This keeps exactly one definition of "the default deployment" (the env) without a parallel default string in the builder.

### 3.3 Per-request resolution wiring (US-3)

- `backend/src/api/v1/chat/handler.py` — in `build_real_llm_handler` (it has `tenant_id` + `db`): `policy = await resolve_tenant_model_policy(db, tenant_id) if tenant_id else None`; `profile = build_azure_model_profile(policy)`; `chat_client = profile.action` (replaces the direct `AzureOpenAIAdapter(AzureOpenAIConfig())` build). The verifier keeps using `profile.cheap`. Everything downstream is unchanged (chat_client threading identical).
- **Day-0 D6 (confirmed — simpler than assumed)**: the `cost_ledger` model sub_type is sourced from `event.model` (the loop's `LoopCompleted` accumulator from `ChatResponse.model` + `adapter.model_info().provider`), NOT a hardcoded env read (`router.py:569` reads `event.model`). So the per-tenant deployment is reflected automatically once the adapter is built on the tenant's deployment/model — NO router wiring needed. (Caveat for the drive-through: `event.model` is what Azure returns = the underlying model; two deployments must differ in underlying model or `model_name` alias to show distinct sub_types — §8 Risks.)

### 3.4 Admin write-side — pricing-validated governance (US-4)

- `backend/src/api/v1/admin/tenants.py` — NEW `PUT /{tenant_id}/model-policy` mirroring `upsert_tenant_quota_overrides`:
  - `class ModelPolicyUpsertRequest(BaseModel)` `model_config=ConfigDict(extra="forbid")`, fields `action_deployment / action_model / cheap_deployment / cheap_model: str | None` (all optional). A `field_validator` (or handler-level check) calls the pricing loader: every non-None `*_model` must be `get_llm_pricing(provider, model) is not None` → else 422 (`detail=f"unknown/unpriced model: {model}"`). Provider is `azure_openai` (the deployment provider) — pin the exact provider key in Day-0 against `llm_pricing.yml`.
  - Handler `Depends(require_admin_platform_role)` + `_load_tenant_or_404`; meta_data identity-swap write `new_meta = dict(tenant.meta_data or {}); new_meta["model_policy"] = payload_dict_without_none; tenant.meta_data = new_meta`; `await db.flush()`.
  - `append_audit(db, tenant_id=tenant_id, operation="tenant_model_policy_upsert", resource_type="tenant", resource_id=str(tenant_id), operation_data={"tenant_id": str(tenant_id), "policy": saved}, user_id=admin_user_id, operation_result="success")` (the 57.56/57.57 no-canonical-service direct-ORM + manual-audit pattern).
  - `await db.commit()`; **`invalidate_tenant_model_policy(tenant_id)`** (so the next request resolves fresh); `await db.refresh(tenant)`; return the saved policy.
  - `class ModelPolicyResponse(BaseModel)` echoes the saved overrides (+ optionally the resolved effective defaults for hydration).

### 3.5 Admin read-side (US-5)

- `backend/src/api/v1/admin/tenants.py` — NEW `GET /{tenant_id}/model-policy` → `Depends(require_admin_platform_role)` + `_load_tenant_or_404` → `resolve_tenant_model_policy(db, tenant_id)` (or a direct read) → `ModelPolicyResponse` with the stored overrides + the env defaults that fill the gaps (so an operator sees the effective policy). Read-only; no audit (reads are not audited per the sibling pattern — confirm in Day-0).

### 3.6 FE model-policy tab (US-6)

Day-0 D9 found an existing operator home: `frontend/src/features/tenant-settings/components/TenantSettingsView.tsx` is a 6-tab IA (General / Flags / Quotas / HITL / Members / Danger) with `QuotasTab.tsx` + `FeatureFlagsTab.tsx` already carrying view/edit modes (57.56-57.57). C1 adds a 7th tab mirroring the established `QuotasTab` pattern — no novel UI invention.

- `frontend/src/features/tenant-settings/components/tabs/ModelPolicyTab.tsx` — NEW: mirror `QuotasTab`'s view/edit shape. View mode renders the effective policy (action/cheap deployment + model) from `GET`; edit mode exposes the 4 optional fields (`action_deployment / action_model / cheap_deployment / cheap_model`) + Save → `PUT`; an unknown-model 422 surfaces inline as an error banner (the sibling-tab error pattern). No dead control — `TenantSettingsView` is already admin-route-gated.
- `frontend/src/features/tenant-settings/components/TenantSettingsView.tsx` — EDIT: register the "Model Policy" tab in the IA (6 → 7 tabs; after Quotas).
- `frontend/src/features/tenant-settings/services/*.ts` (the tenant-settings admin service) — EDIT/NEW: `getModelPolicy(tenantId)` + `putModelPolicy(tenantId, policy)` → `GET`/`PUT /api/v1/admin/tenants/{id}/model-policy` (mirror the quotas service methods; pin the exact file/symbols in the FE Day-0).
- i18n: add the tab label + field labels following the established tenant-settings copy convention (English state strings per codebase convention — pin the i18n file in the FE Day-0).
- **Mockup-fidelity**: the tenant-settings operator tabs follow the operator-portal style authority (lower than the customer `reference/design-mockups/`); there is NO customer mockup for a model-policy editor, so the in-repo `QuotasTab` IS the pattern authority for this tab — mirror it, do not invent styling. `check:mockup-fidelity` baselines the customer mockup pages (oklch byte-identical), not these operator tabs — confirm the FE gate impact (HEX_OKLCH / AP-N counts) in the FE Day-0.

### 3.7 What is explicitly NOT done + Lint / neutrality / 17.md / docs

- NO new event TYPE / codegen / event-count bump. NO DB / migration (JSONB on `tenants.metadata`). `loop.py` diff = 0. NO per-phase / per-turn model choice (proposal §5). The FE tab is the ONLY new user-facing surface (mirrors an existing tab; no new page/route).
- LLM provider neutrality: the `ModelPolicy` value object is in the neutral `adapters/_base`; the resolver (platform_layer) imports only that value object; `agent_harness/**` is untouched (model selection is an api/adapters/platform concern). `check_llm_sdk_leak` + `check_cross_category_import` stay green.
- 17.md: register the `ModelPolicy` value object + `resolve_tenant_model_policy` contract + the model-policy endpoints in the relevant section (single-source).
- Docs: **NEW design note (config tiering + per-tenant model policy)** per `sprint-workflow.md §Step 5.5` — C1 is a NEW-domain spike (config-tiering vertical), so a design-note extract is required (8-point quality gate); pin the doc number in Day-0 by globbing the existing `agent-harness-planning/` design-note series. + CHANGE-071 + 17.md.

### 3.8 Validation (US-1..US-7)

- Backend unit (resolver): absent policy → `ModelPolicy.is_empty()`; present policy → fields parsed; TTL cache hit within window (one DB read) + miss after expiry; `invalidate` forces a re-read; autouse reset fixture isolates the singleton.
- Backend unit (builder): all-None policy → byte-identical to 57.97 (`cheap is action` when no cheap env); action override → action adapter built on the tenant deployment; cheap override → distinct cheap adapter.
- Backend unit (endpoint): PUT 200 + persists + audits + invalidates cache; 422 unknown model; 404 missing/cross-tenant; `extra="forbid"` → 422 on unknown field; GET returns stored ∪ defaults; admin gate (403 without role — using a non-admin JWT fixture).
- Backend unit (wiring): `build_real_llm_handler(tenant_id with policy)` builds a profile whose action deployment == the tenant's (a focused assertion, mocking the adapter ctor or asserting the config).
- Frontend Vitest (US-6): `ModelPolicyTab` renders the effective policy (view), enters edit, Saves → calls `putModelPolicy`, surfaces a 422 unknown-model inline; `TenantSettingsView` registers the new tab.
- Drive-through (US-7): real UI + real Azure → in the new Model Policy tab, set tenant A `action_deployment` = a 2nd real Azure deployment (e.g. the cheap-tier deployment); tenant B unset → same prompt each via the chat UI → `cost_ledger` shows two different `azure_openai_{model}` sub_types; set an unknown model in the tab → 422 surfaced inline + audit row. Screenshots (tab edit + chat runs + cost ledger rows + 422) + observed-vs-intended into progress.md.

## 4. File Change List

**Backend (src) — ~5 files**
- `adapters/_base/model_profile.py` (or NEW `adapters/_base/model_policy.py`) — EDIT/NEW: `ModelPolicy` frozen value object + `from_dict`/`to_dict`/`is_empty` (US-1)
- `platform_layer/billing/model_policy.py` — NEW: `resolve_tenant_model_policy` + TTL-cache class (injectable clock) + `invalidate_tenant_model_policy` (US-1; Day-0 D1 pinned path)
- `adapters/azure_openai/profile.py` — EDIT: `build_azure_model_profile(policy=…)` builds action + cheap from policy ∪ env (US-2)
- `api/v1/chat/handler.py` — EDIT: resolve per-tenant policy → build profile → `chat_client = profile.action` (US-3)
- `api/v1/admin/tenants.py` — EDIT: `PUT` + `GET /{tenant_id}/model-policy` + request/response models + pricing validation + audit + cache invalidate (US-4/US-5)

**Frontend (src) — ~3 files + i18n**
- `features/tenant-settings/components/tabs/ModelPolicyTab.tsx` — NEW: view/edit tab mirroring `QuotasTab` (US-6)
- `features/tenant-settings/components/TenantSettingsView.tsx` — EDIT: register the Model Policy tab (6 → 7 tabs) (US-6)
- `features/tenant-settings/services/*.ts` — EDIT/NEW: `getModelPolicy` + `putModelPolicy` (US-6; pin exact file in FE Day-0)
- i18n — EDIT: tab + field labels (pin file in FE Day-0)

**Tests — ~5 files (convert + extend; 0 deletions)**
- `backend/tests/unit/.../test_model_policy_resolver.py` — NEW: resolver + TTL cache + invalidate + autouse reset
- `backend/tests/unit/adapters/azure_openai/test_profile.py` (the 57.97 profile test, Day-0 D2) — EXTEND: policy-honoring builder + all-None byte-identical; CONVERT the `build_azure_model_profile(strong_client)` caller to the new signature
- `backend/tests/unit/api/v1/admin/test_tenants*.py` — EXTEND: `TestModelPolicyEndpoints` (PUT 200/422/404/forbid + GET + admin gate 403)
- `backend/tests/unit/api/v1/chat/test_handler*.py` (if a handler test exists) — EXTEND: per-tenant profile wiring assertion (else add a focused new test)
- `frontend/src/features/tenant-settings/**/*.test.tsx` — NEW/EXTEND: `ModelPolicyTab` view/edit/422 + tab registration (US-6)

**Docs**
- `claudedocs/4-changes/feature-changes/CHANGE-071-per-tenant-model-policy.md` — NEW
- `docs/03-implementation/agent-harness-planning/<NN>-config-tiering-model-policy.md` — NEW design note (§Step 5.5 spike requirement; number pinned in Day-0)
- `docs/03-implementation/agent-harness-planning/17-cross-category-interfaces.md` — EDIT (`ModelPolicy` + resolver + model-policy endpoints)
- progress.md / retrospective.md / checklist / CLAUDE.md (Current Sprint + Last Updated) / MEMORY.md pointer + subfile / next-phase-candidates (C1 → done; remaining C2/C3/C4) / sprint-workflow.md calibration row

## 5. Acceptance Criteria

1. `ModelPolicy` value object + `resolve_tenant_model_policy` with TTL cache + `invalidate`; absent policy → `is_empty()` → env-default path. (US-1)
2. `build_azure_model_profile(policy)` builds action + cheap from policy ∪ env; all-None → byte-identical to 57.97. (US-2)
3. `build_real_llm_handler` resolves the per-tenant policy and the resolved action `model_name` flows into the `cost_ledger` sub_type. (US-3)
4. `PUT /admin/tenants/{id}/model-policy`: 200 + persists to `meta_data["model_policy"]` + audits + invalidates cache; 422 unknown/unpriced model; 404 missing/cross-tenant; `extra="forbid"`; admin-gated. (US-4)
5. `GET /admin/tenants/{id}/model-policy` returns stored ∪ defaults. (US-5)
6. A Model Policy tab in the tenant-settings IA reads + edits the policy (mirroring QuotasTab); an unknown-model 422 surfaces inline; no dead control. (US-6)
7. Gates: mypy `src` 0 · flake8 clean (`src tests`) · `run_all` 10/10 (event count UNCHANGED) · full pytest green (+N, 0 deletions) · `check_llm_sdk_leak` 0 · `check_cross_category_import` green · frontend build + lint (no `--silent`) + Vitest green · `check:mockup-fidelity` unchanged.
8. `loop.py` / DB / migration / generated wire schema diff = 0.
9. Drive-through PASS: set tenant A policy via the tab → two tenants run the same prompt → two `cost_ledger` model sub_types; an unknown model in the tab → 422 surfaced inline (real UI + real Azure; screenshot + observed-vs-intended). (US-7)

## 6. Deliverables

- [ ] US-1 `ModelPolicy` + resolver + TTL cache + invalidate (+ autouse reset)
- [ ] US-2 `build_azure_model_profile(policy)` (action + cheap from policy ∪ env; all-None byte-identical)
- [ ] US-3 per-request resolution wired into `build_real_llm_handler` (model_name → cost_ledger)
- [ ] US-4 `PUT /admin/tenants/{id}/model-policy` (pricing-validated, audited, cache-invalidating)
- [ ] US-5 `GET /admin/tenants/{id}/model-policy`
- [ ] US-6 Model Policy FE tab (view/edit, inline 422, mirrors QuotasTab) + tab registration
- [ ] US-7 drive-through PASS (set policy via tab → two-tenant sub_type differentiation + 422; screenshot)
- [ ] Backend unit tests (resolver/cache + builder + endpoints + wiring) + FE Vitest (tab view/edit/422)
- [ ] Full gate sweep green (event count unchanged; loop.py/DB diff 0; frontend build/lint/Vitest)
- [ ] CHANGE-071 + NEW design note (config tiering) + 17.md
- [ ] Closeout (progress / retrospective + 8-point design-note gate / CLAUDE.md lean / MEMORY pointer + subfile / next-phase-candidates / calibration row)

## 7. Workload Calibration

- Scope class **`config-tiering-model-policy-spike` (NEW, 0.60, 1st data point)** — a full-stack new-domain config-tiering vertical: a neutral value object + a TTL-cached DB resolver (Risk Class C) + an Azure builder signature reshape + per-request handler wiring + a pricing-validated admin write/read pair (PUT/GET) borrowing the 57.55-57.57 meta_data-JSONB + direct-audit骨架 + a tenant-settings FE tab mirroring the established `QuotasTab` view/edit pattern (D9 — an existing operator home, low-cost extension, not a novel page). No loop.py, no DB migration, no new event. Sized in the band of the recent backend spikes (subagent spikes 0.55-0.60), held at 0.60 for the new resolver/cache domain + the builder-signature reshape on the per-request hot path; the FE tab is a low-variance mirror of an existing tab so it does not push the band up. The proposal hinted "Phase-58 write-side 0.65" — that 0.65 is the agent-delegated `agent_factor`; this sprint is parent-direct, so the scope-class multiplier 0.60 stands alone.
- **Agent-delegated: no** (parent-direct; `agent_factor = 1.0`) — consistent with the 57.98-57.103 streak; the cross-layer resolve seam (neutrality boundary + cache + builder reshape) needs careful hands.
- Bottom-up est ~19 hr (backend ~15 + FE tab ~4) → class-calibrated commit ~11.5 hr (mult 0.60). Day 4 retro Q2 verifies the ratio.

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|-----------|
| **Drive-through needs 2 real Azure deployments** — proving differentiation needs tenant A on a deployment that ALSO exists in Azure (a non-existent deployment 500s at call time, not a useful test). | Use the configured cheap-tier deployment (`AZURE_OPENAI_CHEAP_DEPLOYMENT_NAME`, a real 2nd deployment) as tenant A's `action_deployment`; tenant B unset → default. If only one real deployment exists, fall back to proving the `sub_type` differs via the model-NAME field (a policy that sets `action_model` to a different priced alias on the same deployment) — confirm available deployments in Day-0/Day-3. |
| **RBAC-JWT prod-OIDC gap (`AD-RBAC-DB-To-JWT-Wiring-Phase58`)** — a real-OIDC admin's JWT carries `roles=["user"]` → 403 on the admin PUT in production. | OUT OF SCOPE (decided Day-0, user-confirmed). Pre-existing + shared (already affects quotas/rate-limits/feature-flags); dev-login carries `platform_admin` so the drive-through walks end-to-end in dev. Tracked AD; C1 follows the established sibling pattern, adds no new debt. Note in CHANGE-071 + design note Open Invariants. |
| **`build_azure_model_profile` signature reshape** — Option A changes the builder contract (caller(s) + tests). | Day-0 Prong 2 pins the caller set (recon: handler + tests, small); convert (Never-Delete); the all-None byte-identical test + mypy catch regressions. |
| **Risk Class C (module-singleton TTL cache across test loops)** — the resolver cache + the per-tenant entries persist across tests. | Autouse reset fixture clearing the cache (SessionRegistry / InjectionRegistry precedent); inject a monkeypatchable clock for deterministic TTL tests. |
| **Risk Class E (stale `--reload` worker)** — drive-through verifies startup-wired resolution + the cache; an orphaned spawn-worker serves old code. | Clean restart: kill stale uvicorn reloader + spawn-worker (`Get-CimInstance Win32_Process` PID/PPID/StartTime), confirm a fresh PID is the sole :8000 owner; do not touch frontend node. |
| **Risk Class D (ORM alias)** — `Tenant.meta_data` physical column is `metadata`. | C1 uses ORM (`tenant.meta_data = …`) only — no raw SQL; pinned per the rule. |
| **Cache staleness window** — a PUT invalidates, but an in-flight request resolved just before the PUT keeps the old policy for that request. | Acceptable for a config spike (~60s TTL; PUT invalidates for the next request). Document the eventual-consistency window in the design note. |
| **Unpriced-model invariant scope** — validating `*_model` against pricing assumes the model alias maps cleanly. | Day-0 pins the `llm_pricing.yml` keys + provider key + the version-suffix strip behavior; the validator reuses `get_llm_pricing` (the exact billing helper that prices the ledger) so write-validation == ledger-pricing (no drift). |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- **A standalone model-policy page / route** (beyond the in-IA tab) — the tab (US-6) is the operator surface; a dedicated page is unwarranted (the tenant-settings IA is the home). (NOTE: the admin model-policy *tab* is now IN SCOPE as US-6 per the user's Day-0 D9 decision 2026-06-11 — the plan's earlier FE-deferral was based on an inaccurate "no FE home" assumption; D9 found the existing 6-tab tenant-settings IA.)
- **Graduate `model_policy` to a typed table** — meta_data JSONB is the spike storage (quota_overrides precedent); typed table + RLS + index is a C3-era step if the policy surface widens (the rate_limits 0019 precedent).
- **Per-tenant verification mode / HITL escalate list / guardrail policy + risky-action detector** — C3.
- **Compaction cheap tier + memory-extraction tier** — C2.
- **Non-Azure profile builders (Anthropic / OpenAI)** — C4 (the `ModelPolicy` value object is provider-neutral, so C4 adds builders without reshaping C1).
- **Per-phase / per-turn model choice (thread ModelProfile into loop)** — proposal §5 (AP-6 / YAGNI; construction-time DI suffices).
- **RBAC-JWT prod-OIDC wiring (`AD-RBAC-DB-To-JWT-Wiring-Phase58`)** — its own slice (unlocks all admin endpoints, not just C1; touches IAM tests).
- **B3/C2/C3/B4/A3** — later slices in the 10-slice order.
