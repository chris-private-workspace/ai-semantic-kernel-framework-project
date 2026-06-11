# 27 — Per-tenant Model Policy (Config Tiering, C1)

**Purpose**: Design-note extract from Sprint 57.104 (C1) — how a tenant governs its own `{action, cheap}` LLM model selection, resolved per-request into the chat `ModelProfile`, with a pricing-validated admin write-side + operator tab.
**Category / Scope**: 範疇 4 (model selection) × adapters × platform_layer (config tiering) × api/v1/admin × Frontend — Phase 57 / Sprint 57.104
**Created**: 2026-06-11
**Status**: Active (extracted from a shipped + drive-through-proven spike)
**Method**: Extracted from the real implementation (commits `2816e883` backend + `ae2aed96` FE) + a real-UI/real-Azure drive-through. All file:line on `main` HEAD post-merge.

> **Modification History**
> - 2026-06-11: Initial creation (Sprint 57.104 C1 spike extract)

---

## 1. Spike Summary — "C1: make 57.97's env-only ModelProfile tenant-governable"

Sprint 57.97 (design note 24) built `ModelProfile{action, cheap}` but model selection was **system-wide + env-only**. C1 adds a per-tenant override: an admin sets `{action_deployment, action_model, cheap_deployment, cheap_model}` (all optional); the policy persists in `tenant.meta_data["model_policy"]` (JSONB); it is resolved per-request (TTL-cached) and built into that request's profile — so a tenant's chat runs on its configured deployment, and the `cost_ledger` model sub_type reflects it.

**The keystone pattern**: model resolution is an **async DB read the router runs BEFORE the sync builders**, mirroring `resolve_session_persona` (`handler.py:654`). The resolved `ModelPolicy` threads through `build_handler` → `build_real_llm_handler` → `build_azure_model_profile`. `loop.py` is untouched.

## 2. Decision Matrix

### 2.1 Storage (where the policy lives)

| Option | Precedent | Verdict |
|--------|-----------|---------|
| **`tenant.meta_data["model_policy"]` JSONB (CHOSEN)** | `quota_overrides` (57.56), `rate_limits` (pre-0019) | ✅ Zero migration; `append_audit` reuse; cheapest spike. Schema-less acceptable for a spike; graduates to a typed table if the surface widens (the rate_limits 0019 path). |
| Dedicated `tenant_policies` table | `rate_limit_configs` (0019) | ❌ Migration + surface area; premature for a 4-field spike (YAGNI). C3-era if the policy面 widens. |
| Registry-table JSONB (per-key) | `feature_flags.tenant_overrides` | ❌ Shape mismatch — model policy is per-tenant, not per-key. |

### 2.2 How the override reaches the profile build (the sync/async boundary)

| Option | Mechanism | Verdict |
|--------|-----------|---------|
| **Resolve in the router, thread `ModelPolicy` into the sync builder, builder owns action+cheap construction (CHOSEN)** | `router.py:236` `resolve_tenant_model_policy` → `build_handler(model_policy=)` → `build_real_llm_handler` → `build_azure_model_profile(policy)` | ✅ Keeps the builders sync (no async DB import in the wiring layer); the `resolve_session_persona` precedent (`handler.py:654`); single builder (no parallel path). |
| Make `build_real_llm_handler` async | resolve inside the builder | ❌ The builder is sync (`handler.py:256` `def`, not `async def`) + called in a sync chain; converting it ripples through `build_handler` + the router. |
| Separate `build_tenant_model_profile` | parallel builder | ❌ AP-11 parallel path; the env-only builder becomes the "legacy" sibling. |

### 2.3 BaseSettings None-override trap (Day-0 D3)

`AzureOpenAIConfig` is a `pydantic-settings BaseSettings` (`adapters/azure_openai/config.py:34-43`, `env_prefix="AZURE_OPENAI_"`). Explicit kwargs WIN over env, and **passing `deployment_name=None` overrides to None** (field default `""`, `config.py:56-59`) — it does NOT fall back to env. → `_azure_config` (`profile.py`) includes a kwarg ONLY when the policy field is a concrete string; omitting it lets BaseSettings read the env default. One definition of "the default deployment" (the env).

## 3. Verified Invariants (drive-through + gate proven)

| Invariant | Evidence (file:line / artifact) |
|-----------|--------------------------------|
| `ModelPolicy` is provider-neutral (no SDK import) → both adapters + platform_layer import it | `adapters/_base/model_policy.py`; `check_llm_sdk_leak` + `check_cross_category_import` green (10/10) |
| All-None policy is byte-identical to 57.97 (env-only) | `profile.py` `build_azure_model_profile(policy or ModelPolicy())`; `test_profile.py::test_empty_policy_is_byte_identical_to_none` |
| Per-tenant action override changes the chat's action model | Drive-through: acme-prod policy `gpt-5.4-nano` → `cost_ledger` action sub_type `azure_openai_gpt-5.4-nano-2026-03-17` (vs env-default `gpt-5.2`). `progress.md` Day 3 table |
| Cache invalidation: a policy change takes effect on the next chat | Drive-through: nano → mini via the tab → next chat action sub_type `azure_openai_gpt-5.4-mini`; `invalidate_tenant_model_policy` called by the PUT (`tenants.py`); `test_model_policy.py::test_resolve_invalidate_forces_reread` |
| cost_ledger sub_type flows from `event.model` (no router wiring needed) | `router.py:569` reads `event.model`; D6 confirmed |
| Unpriced model rejected (governance invariant) | Drive-through 422 inline "Unknown/unpriced model: 'bogus-model-xyz'"; `_validate_model_policy_pricing` (`tenants.py`) reuses `get_llm_pricing("azure_openai", model)`; `test_admin_tenant_model_policy.py::test_put_unpriced_model_rejected` |
| Composite-replace (omitted fields cleared) | `test_put_composite_replace` + drive-through clear→default (`dt57104` step 6) |
| Multi-tenant isolation | `test_put_multi_tenant_isolation` (each tenant's meta_data holds only its own override) |

**Verification command**: `cd backend && python -m pytest tests/unit/adapters/_base/test_model_policy.py tests/unit/platform_layer/billing/test_model_policy.py tests/unit/adapters/azure_openai/test_profile.py tests/integration/api/test_admin_tenant_model_policy.py -q` (27 unit + 13 integration). Drive-through reproduce: dev-login `platform_admin` → tenant-settings → Model Policy tab → set `action_deployment`=a 2nd real Azure deployment → chat → query `cost_ledger.sub_type`.

**Test fixtures**: integration uses `_pricing_loaded` (loads real `backend/config/llm_pricing.yml`) + `_seed_tenant` (MODELPOL_PUT_ sweep in `tests/integration/api/conftest.py`). Resolver unit uses `_FakeSession`/`_FakeTenant` + injectable clock (no DB).

## 4. Cross-Category Contracts (→ 17.md single-source)

Registered in `17-cross-category-interfaces.md`:
- `ModelPolicy` value object (`adapters/_base/model_policy.py`) — the neutral per-tenant override that resolves to a `ModelProfile`.
- `resolve_tenant_model_policy(db, tenant_id) -> ModelPolicy` (`platform_layer/billing/model_policy.py`) — TTL-cached, fail-open; `invalidate_tenant_model_policy(tenant_id)` called by the admin PUT.
- `PUT`/`GET /api/v1/admin/tenants/{id}/model-policy` — admin-gated, pricing-validated governance write/read.

## 5. Open Invariants (NOT verified this spike — deferred)

- **`AD-RBAC-DB-To-JWT-Wiring-Phase58`** (pre-existing, shared): the admin endpoint gates on `require_admin_platform_role` reading the JWT `roles` claim; the OIDC callback hardcodes `roles=["user"]` (`auth.py:302`). Dev-login carries `platform_admin` so the drive-through is fully valid in dev; production-OIDC admin would 403. NOT a C1 regression (already affects 57.55-57.57 admin PUTs); its own slice.
- **Cheap-tier per-tenant override** in the chat hot path: wired (`cheap_deployment`/`cheap_model` resolve) + unit-tested, but the drive-through only exercised the ACTION override (the chat's verification turn ran on the env cheap tier). The cheap override path is gate-verified, not drive-through-verified.
- **C2** (compaction cheap tier) + **C3** (per-tenant verification/HITL/guardrail policy + risky-action detector) + **C4** (non-Azure profile builders) — later slices; `ModelPolicy` is provider-neutral so C4 adds builders without reshaping C1.
- **Graduate to a typed table** — meta_data JSONB is the spike storage; revisit if the policy面 widens (C3).

## 6. Rollback / Fallback

- The resolver is **fail-open**: any miss / DB flake → `ModelPolicy()` (the env-only path) — a resolution failure never breaks chat (`model_policy.py` `except Exception` → `ModelPolicy()`).
- An all-None / absent policy is byte-identical to 57.97 — disabling the feature = clearing the policy (PUT `{}`), or reverting the 2 commits (`2816e883` + `ae2aed96`); the env-only builder path is the fallback (no env / config change needed).
- Cache staleness bounded at the TTL (~60s) even without an invalidate; the PUT invalidates for instant effect.

## 7. References

- `24-multi-model-profile-design.md` — the 57.97 `ModelProfile{action,cheap}` this extends.
- `17-cross-category-interfaces.md` — `ModelPolicy` + resolver + endpoints contracts.
- `harness-deepening-proposal-20260610.md §3` — the C workflow (C1 slice).
- `CHANGE-071-per-tenant-model-policy.md` — the change record.
- `sprint-57-104/progress.md` Day 3 — the drive-through evidence + cost_ledger table.
- `.claude/rules/sprint-workflow.md §Step 5.5` — the spike design-note 8-point gate.

## 8. 8-Point Quality Gate (self-review)

1. ✅ Section headers map to the C1 spike (storage / sync-async boundary / verified invariants).
2. ✅ Technical claims carry file:line (`config.py:56-59`, `router.py:569`, `handler.py:654`, etc.).
3. ✅ Decision rationale = comparison matrices (§2.1/2.2/2.3).
4. ✅ Verification command (pytest line + drive-through reproduce).
5. ✅ Test fixtures referenced (`_pricing_loaded`, MODELPOL_PUT_ sweep, `_FakeSession`).
6. ✅ Open invariants explicitly fenced (verified vs deferred — §5).
7. ✅ Rollback path (§6 — fail-open + clear-policy + revert-commits).
8. ✅ 17.md cross-ref (§4 — no parallel contract definition).
