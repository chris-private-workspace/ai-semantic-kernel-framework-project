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

---

## Day 2 — 2026-06-11 — FE Model Policy tab (US-6)

### Approach
- The mechanical FE mirror (tab + 2 hooks + service + tab registration + Vitest) was delegated to a code-implementer agent with a precise contract; **the parent independently reviewed the code + re-ran every gate** (Before-Commit item 7 — delegated FE must be parent-re-verified). → `agent-delegated: partial` (US-6 only; the backend Day 1 was parent-direct).

### Shipped (commit `ae2aed96`)
- `ModelPolicyTab.tsx` (NEW) — VIEW (4 fields; null → "System default") + EDIT (4 inputs + Save/Cancel) + inline 422 banner (`saveMutation.error.message`); no dead controls; mockup-ui `Card` + QuotasTab classes (`row`/`col`/`spread`/`mono`/`subtle`/`btn-*`).
- `useModelPolicy.ts` + `useModelPolicySave.ts` (NEW) — mirror `useQuotas`/`useQuotasSave` (TanStack; invalidate on save).
- `tenantSettingsService.ts` — `getModelPolicy`/`putModelPolicy` (snake↔camel `_modelPolicyFromApi`/`_modelPolicyToApi`; composite-replace drops blank fields; `_handleResponse` surfaces 422 `detail` → Error.message → inline banner).
- `TenantSettingsView.tsx` — register "Model Policy" tab after Quotas (6 → 7).
- `types.ts` — `ModelPolicy` (camelCase) + `ModelPolicyApiResponse`/`ModelPolicyApiUpsertRequest` (snake).
- English copy (operator-tab convention; no i18n layer — inline literals, matches QuotasTab). Mockup-fidelity: operator tabs follow the in-repo QuotasTab style authority (not the customer oklch baseline); `check:mockup-fidelity` 53 unchanged.

### Parent-re-verified gate (Day 2)
- lint **exit 0** (the `TSSatisfiesExpression` lines are jsx-ast-utils library console noise, NOT eslint errors) · build **exit 0** (3.18s) · Vitest **809 passed / 136 files** (+22 net) · `check:mockup-fidelity` **passed** (byte-identical CSS; hex/oklch 53 unchanged).
- Code review confirmed: the 422 path is correct end-to-end (backend 422 `{detail}` → `_handleResponse` throw Error(detail) → `saveMutation.error.message` → "Save failed: …" inline); no dead controls; English copy; URL `/api/v1/admin/tenants/{id}/model-policy` matches backend.

### 🚧 Remaining (Day 3)
- **Drive-through (US-7)** — the hard-constraint final gear: clean backend restart (Risk Class E) + real Azure + tenant A policy (set via the new tab) vs tenant B unset → `cost_ledger` model sub_type differentiation + 422 in the tab. NOT yet driven → C1 is **gate-verified, drive-through pending** (per the Drive-Through Acceptance Hard Constraint, not "done" until driven).
- Day 4 closeout: CHANGE-071 + NEW design note (config-tiering spike, §Step 5.5) + 17.md + retrospective + CLAUDE/MEMORY + calibration row.

---

## Day 3 — 2026-06-11 — Full gate re-verify + DRIVE-THROUGH (US-7) ✅ PASS

### Clean restart (Risk Class E)
- Killed the stale dev backend PID 16496 (the prior-session B2b code, NO C1) — single no-reload process, no spawn-workers; `:8000` confirmed FREE + `python.exe count 0`; did NOT touch the frontend node (:3007 PID 22000).
- Started a fresh no-reload backend (PID 35340); startup log confirmed **"pricing loader wired"** (→ the 422 validator is live) + **"billing outbox drainer started"** (→ the cost_ledger pipeline) + the C1 code loaded.

### Drive-through (real UI :3007 + real backend + real Azure, Playwright; dev-login `platform_admin`)
The full user-facing chain — including cache invalidation — proven on `acme-prod` (one tenant, policy changed via the tab):

1. **Tab registered + GET works**: the "Model Policy" tab appears 7th (after Quotas); on load all 4 fields render "System default" (sparse GET → empty). (`dt57104-1`)
2. **Set policy → persist → GET reflects**: Edit → action_deployment/model = `gpt-5.4-nano` → Save → exits edit, view shows `gpt-5.4-nano`; persists across a full page reload (re-GET). (`dt57104-2`)
3. **Policy resolves into the chat → cost_ledger differentiates**: a real_llm chat ("capital of France?" → "Paris") with the nano policy → `cost_ledger` action turn sub_type = **`azure_openai_gpt-5.4-nano-2026-03-17_input/output`** (vs the pre-C1 baseline chat at 08:32 on the env-default **`azure_openai_gpt-5.2`**). The verification turn ran on the env cheap tier `gpt-5.4-mini` (policy didn't override cheap). (`dt57104-3`)
4. **422 unpriced model surfaced inline (governance gear)**: Edit → action_model = `bogus-model-xyz` → Save → inline banner **"Save failed: Unknown/unpriced model: 'bogus-model-xyz' (not in config/llm_pricing.yml)"**, stays in edit mode, policy unchanged. (`dt57104-4`)
5. **Cache invalidation**: changed the policy to `gpt-5.4-mini` via the tab → Save → ran a 2nd real_llm chat ("color of the sky?" → "Blue") → `cost_ledger` action turn = **`azure_openai_gpt-5.4-mini-2026-03-17_input/output`**. The policy CHANGE took effect on the very next chat ⇒ the PUT's `invalidate_tenant_model_policy` cleared the resolver TTL cache.
6. **Clear → revert to default**: Edit → cleared both action fields → Save → all 4 back to "System default" (composite-replace clear); `acme-prod` left clean (no policy → env default).

**cost_ledger evidence (acme-prod action turn, same tenant, policy set via the tab):**
| recorded_at | action turn model sub_type | tab policy |
|-------------|----------------------------|-----------|
| 08:32 (pre-C1 baseline) | `azure_openai_gpt-5.2-2025-12-11` | none (env default) |
| 11:59 (C1) | `azure_openai_gpt-5.4-nano-2026-03-17` | action=gpt-5.4-nano |
| 12:04 (C1) | `azure_openai_gpt-5.4-mini-2026-03-17` | action=gpt-5.4-mini |

**Drive-through verdict: PASS.** Every DoD met — tab persist/reflect, policy→chat model resolution, per-tenant model sub_type differentiation, cache invalidation on policy change, inline 422 governance, clear-to-default, no dead controls. Screenshots: `artifacts/dt57104-{1,2,3,4}.png` (the `gpt-5.4-mini` chat + clear states proven via cost_ledger query above, not separately screenshotted). The US-7 wiring assertion the Day-1 plan deferred is now end-to-end-proven (the nano/mini chats show `build_real_llm_handler(model_policy)` → the tenant's action deployment reaches the loop + cost ledger).

### Day 3 gate (re-verified)
- Backend: mypy `src` 0/357 · flake8 clean · run_all 10/10 · unit 27 · integration 13 (Day 1, unchanged).
- Frontend: lint 0 · build 0 · Vitest 809/136 · check:mockup-fidelity 53 (Day 2, parent-re-verified).
- `loop.py` / DB / migration / wire-schema diff = 0.
