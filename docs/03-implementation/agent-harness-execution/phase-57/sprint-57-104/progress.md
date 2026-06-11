# Sprint 57.104 Progress — per-tenant model policy (C1)

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-104-plan.md) · [Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-104-checklist.md)

---

## Day 0 — 2026-06-11 — Plan-vs-Repo Verify + Branch

### Branch
- `feature/sprint-57-104-per-tenant-model-policy` from `main` HEAD `680bcd58` ✅

### Three-prong Day-0 verify (against HEAD `680bcd58`)

**Backend scope shift = 0%** — all File Change List anchors confirmed; no signature mismatch. Notable refinements + one scope decision below.

#### Drift / confirm findings

- **D1 (confirm)** — `adapters/_base/model_profile.py` exists; `model_policy.py` absent; `platform_layer/config/` does NOT exist → resolver home = `platform_layer/billing/model_policy.py` (co-located with `pricing.py` + `cost_ledger.py`). ModelPolicy value object → `adapters/_base/` (neutral, next to ModelProfile).
- **D2 (confirm)** — `build_azure_model_profile` has exactly **2 callers**: `handler.py:320` (prod) + `tests/unit/adapters/azure_openai/test_profile.py`. Signature reshape (Option A: `(strong_client)` → `(policy)`) is low-impact; convert both (Never-Delete).
- **D3 (drift → §8 Risks)** — `AzureOpenAIConfig` is a BaseSettings (`env_prefix="AZURE_OPENAI_"`); explicit kwargs OVERRIDE env, and **passing `deployment_name=None` overrides to None (no env fallback)**. Field defaults: `deployment_name=""`, `model_name="gpt-4o"`. **Implication**: the builder must pass a concrete override string OR OMIT the kwarg entirely (so BaseSettings reads the env default). The resolver/builder must never pass None. (Refines §3.2.)
- **D4 (confirm)** — pricing: `get_pricing_loader()` (strict) / `maybe_get_pricing_loader()` (lenient); `get_llm_pricing(provider, model) -> LLMPricing | None`. Provider key = `azure_openai`. Models in `config/llm_pricing.yml`: gpt-4o-mini / gpt-5.2 / gpt-5.4 / gpt-5.4-mini / gpt-5.4-nano (+ anthropic claude-3.7-sonnet). `_strip_version_suffix` regex `r"-\d{4}-\d{2}-\d{2}$"` auto-strips Azure date suffix. → validator: `get_pricing_loader().get_llm_pricing("azure_openai", model)` is None → 422.
- **D5 (confirm)** — `_load_tenant_or_404(db, tenant_id)` local (`tenants.py:430-437`); `append_audit` from `infrastructure.db.audit_helper` (`:94`); `require_admin_platform_role` from `platform_layer.identity.auth` (`:103`); router `APIRouter(prefix="/admin/tenants")` (`:127`). PUT /quotas meta_data-write + append_audit + commit pattern confirmed (`:1419-1444`). GET handlers do NOT audit (read-only precedent) → C1 GET no audit.
- **D6 (drift → SIMPLER, refines §3.3)** — the cost_ledger model sub_type is sourced from **`event.model`** (the loop's `LoopCompleted` accumulator from `ChatResponse.model` + `adapter.model_info().provider`), NOT a hardcoded env read in the router (`router.py:569` reads `event.model`). **Implication**: a per-tenant deployment is automatically reflected in the cost_ledger sub_type as long as the adapter is built on the tenant's deployment/model — NO router wiring needed. Caveat: `event.model` reflects what Azure returns (the underlying model), so the drive-through needs two deployments whose underlying models differ (or a different `model_name` alias) — already in §8 Risks.
- **D7 (drift → refines §3.1)** — NO monkeypatchable clock helper exists (SessionRegistry uses bare `datetime.now(UTC)`). → the TTL cache uses a small class with an **injectable clock callable** (default `time.monotonic`) so tests are deterministic, rather than relying on a global time provider.
- **D8 (confirm)** — `handler.py:312` `chat_client = AzureOpenAIAdapter(AzureOpenAIConfig())`; `:320` `profile = build_azure_model_profile(chat_client)`; `:513` verifier `profile.cheap`; `tenant_id` + `db` are function params (in scope). The resolve plugs in at :312-320.
- **D9 (drift → SCOPE DECISION, see below)** — a tenant-settings operator page **already exists**: `frontend/src/features/tenant-settings/components/TenantSettingsView.tsx` is a 6-tab IA (General / Flags / Quotas / HITL / Members / Danger); `QuotasTab.tsx` + `FeatureFlagsTab.tsx` have edit modes (57.56-57.57). model-policy FE references = 0. **Implication**: my plan §9 FE-deferral justification ("no operator home exists") is INACCURATE — a home exists, and a model-policy tab mirroring QuotasTab is low-cost. This converts FE-deferral from "technically blocked (no mockup home)" to "a scope choice" → surfaced to the user before Day-1.
- **D10 (confirm)** — zero existing `model_policy` / `model-policy` residue in backend + frontend → clean greenfield, no collision.

#### Go/no-go
- Backend scope shift 0% → backend portion GO (proceed once FE-scope decision lands).
- D9 opens a real FE-scope fork (backend-only vs +model-policy tab); **resolved 2026-06-11 by user → include the model-policy tab** (US-6; plan §3.6 + §9 updated, calibration → full-stack). The plan §3.1/§3.2/§3.3 refined by D3/D6/D7 (folded into §3, not silently rewritten — D-findings preserved here per AP-2).

---

## Day 1 — 2026-06-11 — Backend: ModelPolicy + resolver + builder + wiring + admin API (US-1..US-5)

### Shipped
- **US-1** `ModelPolicy` frozen value object (`adapters/_base/model_policy.py`, neutral, from_dict/to_dict/is_empty) + `resolve_tenant_model_policy` + `_ModelPolicyCache` (injectable clock, ~60s TTL) + `invalidate_tenant_model_policy` + `reset_model_policy_cache` (`platform_layer/billing/model_policy.py`). Mirrors `resolve_session_persona` (async-resolve-before-build, fail-open). Risk Class C autouse reset.
- **US-2** `build_azure_model_profile(policy=None)` reshape (`adapters/azure_openai/profile.py`): builds action + cheap from policy ∪ env; `_azure_config` conditional-kwargs helper (D3 — never pass None to BaseSettings); all-None byte-identical to 57.97.
- **US-3** wiring: router `resolve_tenant_model_policy(db, current_tenant)` BEFORE `build_handler` (mirrors `resolve_session_persona`, `router.py:230+`) → `model_policy` threads through `build_handler` → `build_real_llm_handler` → `build_azure_model_profile`; `chat_client = profile.action`. D6: cost_ledger sub_type flows from `event.model` (no router wiring). `loop.py` diff 0.
- **US-4** `PUT /admin/tenants/{id}/model-policy` (`api/v1/admin/tenants.py`): `extra="forbid"` + pricing-validated (`maybe_get_pricing_loader().get_llm_pricing("azure_openai", model)` → 422) + meta_data JSONB identity-swap + `append_audit(tenant_model_policy_upsert)` + `db.commit()` + `invalidate_tenant_model_policy` + composite-replace (empty → clear).
- **US-5** `GET /admin/tenants/{id}/model-policy` (sparse stored overrides; no audit — GET precedent).

### Tests (backend)
- `tests/unit/adapters/_base/test_model_policy.py` (8) — value object round-trip / strip / drop-None.
- `tests/unit/platform_layer/billing/test_model_policy.py` (11) — cache TTL (injected clock) / resolve parse / cache-hit-no-db / invalidate-reread / fail-open.
- `tests/unit/adapters/azure_openai/test_profile.py` (8, CONVERTED to the policy signature) — env fallback + policy overrides + D3-omit.
- `tests/integration/api/test_admin_tenant_model_policy.py` (13, NEW) — PUT auth/404/persist/composite-replace/clear/extra-forbid/422-unpriced/200-priced/isolation/audit + GET 404/empty/reflects-PUT. + conftest `MODELPOL_PUT_%` sweep.
- **Wiring unit test**: deferred to Day-3 drive-through (build_real_llm_handler is heavy to mock; the 2-line param threading is mypy-checked + the pieces (builder + resolver) are unit-tested + drive-through proves end-to-end).

### Gate (Day 1)
- mypy `src` **0 / 357** (+2 new source files) · flake8 (`src tests`) clean · `run_all` **10/10** (event count UNCHANGED; `check_llm_sdk_leak` 0; `check_cross_category_import` green) · unit **27 passed** · integration **13 passed**. `loop.py` / DB / migration / wire-schema diff **0**.
- Note: PUT 422 uses `HTTP_422_UNPROCESSABLE_ENTITY` (a starlette DeprecationWarning) — KEPT for consistency with the 2 pre-existing usages in `tenants.py`; the rename is a cross-file concern, not C1 scope.

### Next (Day 2)
- FE Model Policy tab (`ModelPolicyTab.tsx` mirroring `QuotasTab` + `TenantSettingsView` registration + admin service `getModelPolicy`/`putModelPolicy` + i18n) + Vitest. Then Day 3 full gate + drive-through (US-7).
