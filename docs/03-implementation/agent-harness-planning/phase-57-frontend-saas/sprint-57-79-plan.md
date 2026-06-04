# Sprint 57.79 Plan — C-11 billing-correctness 收尾 (pricing key normalize + adapter max_tokens param) (closes AD-Cost-Ledger-Model-Pricing-Key-Mismatch + AD-Adapter-MaxTokens-NewModel-Param)

**Branch**: `feature/sprint-57-79-c11-billing-gaps` (from `main` `3c3e85df`)
**Closes**: `AD-Cost-Ledger-Model-Pricing-Key-Mismatch` + `AD-Adapter-MaxTokens-NewModel-Param` — the 2 billing gaps surfaced by the C-11 real-LLM smoke (#237).
**Scope**: Backend (2 billing-correctness fixes) + actual real-LLM Azure verification (user `.env` has live key). NOT frontend; NOT B-7/B-8 core logic.

---

## 0. Background

C-11 real-LLM e2e is **already LIVE + verified** (HTTP 200 + SSE `loop_end` + Azure real reply + audit_log Δ=1; PricingLoader startup wiring FIX-022 `main.py:167`; e2e-real-llm-smoke CI gate FIX-023; cost_ledger row-count Δ≥2 confirmed post-restart, process-state not code bug). The smoke run (#237) surfaced **2 residual billing gaps** that make cost recording silently wrong on the gpt-5.x deployment. This sprint closes both + re-verifies against real Azure.

**User decision (AskUserQuestion, 2026-06-04)**: do the 2 code fixes AND run real Azure verification this sprint (user `.env` has a live `AZURE_OPENAI_*` key; cost ~$0.005/run).

### Day-0 ground-truth (parent grep + 1 researcher pass, main `3c3e85df`)
- **D-DAY0-1 (pricing key flow)**: `response.model` is returned verbatim by the adapter (`adapter.py:448` `model=getattr(response, "model", self.config.model_name)`) → `event.model` (`loop.py:1198-1199`) → `metrics_acc.last_model` (`loop.py:1264`) → `router.py:440` `record_llm_call(model=event.model or _FALLBACK_PRICING_MODEL)` → `cost_ledger.py:137` → `get_llm_pricing("azure_openai", model)`.
- **D-DAY0-2 (exact lookup, no normalize)**: `pricing.py:119-121` `get_llm_pricing` = `self._llm.get(provider, {}).get(model)` — pure exact dict lookup, **no normalize**. A date-suffixed model id (e.g. `gpt-5.2-2025-12-11`) never matches a base yaml key → returns `None` → cost row written with `unit_cost=0` (silent billing gap).
- **D-DAY0-3 (yaml gap)**: `config/llm_pricing.yml:10-18` `azure_openai` has only `gpt-4o-mini` + `gpt-5.4`. **No `gpt-5.2`** of any form.
- **D-DAY0-4 (max_tokens hard-wired ×2)**: `adapter.py:210-211` (chat) + `:282-283` (stream) both do `if request.max_tokens is not None: kwargs["max_tokens"] = request.max_tokens`. gpt-5.x rejects `max_tokens` (400: "use `max_completion_tokens`"). Loop main-flow doesn't set a token cap so doesn't hit it, but the e2e smoke cost-guard (`e2e-real-llm-smoke.yml:173` `MAX_TOKENS_PER_CALL`) + any future verification sub-call / compaction would 400 on gpt-5.x.
- **D-DAY0-5 (config fields available)**: `azure_openai/config.py` `AzureOpenAIConfig` has `api_version` (`:52`, default `2024-02-15-preview`), `model_name` (`:63`), `model_family` (`:67` Literal["gpt","gpt-mini","gpt-nano"]), `deployment_name` (`:56`). **No existing gpt-5 / capability helper** — must add. `model_family` is too coarse (gpt-5.x is still "gpt").
- **D-DAY0-6 (config staleness trap)**: per #237, `config.model_name` may be stale (`gpt-4o`) while the live deployment returns `gpt-5.2-2025-12-11`. If Gap-2's param branch keys off `model_name` while `model_name` is stale, it mis-branches → still 400. **The judging field must reflect the real deployment model.**
- **D-DAY0-7 (test gaps)**: `test_pricing_loader.py` tests get_llm_pricing happy values but **no None / normalize branch**; `test_integration.py:84,108,153` uses `max_tokens=` but **no kwargs-composition assertion**. Both need new unit coverage.

---

## 1. Sprint Goal

Close the 2 C-11 billing gaps — make `get_llm_pricing` robust to date-suffixed Azure model ids (+ add the gpt-5.2 base price), and make the adapter emit `max_completion_tokens` for gpt-5.x instead of `max_tokens` — then re-verify against real Azure (cost_ledger `unit_cost>0` + no 400 on a token-capped call).

---

## 2. User Stories

- **US-1** — 作為 billing 維護者，我希望 real_llm 聊天的 cost_ledger 記錄真實 `unit_cost`（非 $0），以便計費準確（不再 silent 漏記）。
- **US-2** — 作為平台維護者，我希望 gpt-5.x deployment 不因 `max_tokens` param 報 400，以便 token cap（e2e 護欄 / 未來 verification sub-call / compaction）能運作。
- **US-3** — 作為 QA，我希望 pricing lookup 對 date-suffixed model 名 robust，以便 deployment 版本更新（`gpt-5.2-2026-XX-XX`）不會 silent 回 $0。
- **US-4** — 作為開發者，我希望 unit test 覆蓋 `get_llm_pricing` normalize/None 分支 + adapter `max_tokens` param 分支，以便回歸保護。
- **US-5** — 作為 release owner，我希望實際 real-LLM Azure smoke 驗證 `cost_ledger.unit_cost>0` + token-capped 呼叫不 400，以便確認 end-to-end 真的修好（非僅 mock）。

---

## 3. Technical Specifications

### 3.0 Architecture
Two independent backend fixes + a real-LLM verification leg. Gap 1 lives in the billing layer (`pricing.py` + yaml); Gap 2 lives in the adapters layer (`azure_openai/adapter.py` — provider-specific param naming, correctly absorbed at the adapter boundary per LLM-neutrality). Neither touches `loop.py` / `agent_harness`.

### 3.1 Gap 1 — pricing key date-suffix normalize + gpt-5.2 base price (US-1/US-3) — `pricing.py` + `llm_pricing.yml`
- `get_llm_pricing(provider, model)` (`pricing.py:119-121`): keep exact lookup first; on miss, strip a trailing Azure version suffix `-YYYY-MM-DD` (regex `r"-\d{4}-\d{2}-\d{2}$"`) and retry the base key. Return `None` only if both miss.
  ```python
  def get_llm_pricing(self, provider: str, model: str) -> LLMPricing | None:
      models = self._llm.get(provider, {})
      hit = models.get(model)
      if hit is not None:
          return hit
      base = _strip_version_suffix(model)   # drop trailing -YYYY-MM-DD
      return models.get(base) if base != model else None
  ```
  - Module helper `_strip_version_suffix(model: str) -> str` (single `re.sub`); add `import re`.
  - **Design rationale**: keeps the cost_ledger row's `model` field at the full `gpt-5.2-2025-12-11` (audit fidelity) while pricing matches the base `gpt-5.2`. Robust to future date bumps — yaml maintains base keys only. Alternative (yaml full date key) rejected: brittle (every deployment version bump → silent $0 again).
- `config/llm_pricing.yml`: add `azure_openai.gpt-5.2` with `input_per_million` / `output_per_million` / `cached_input_per_million` + bump `last_updated`. **Pricing values: user-provided (see §8 Dependency D1).**

### 3.2 Gap 2 — adapter max_completion_tokens for gpt-5.x (US-2) — `azure_openai/adapter.py`
- New helper `_max_tokens_param_name(model_name: str) -> str`: returns `"max_completion_tokens"` if `model_name.startswith("gpt-5")` else `"max_tokens"`. Place as a module function (testable in isolation) + call from both sites.
- `adapter.py:210-211` (chat) + `:282-283` (stream): replace the hard-wired `kwargs["max_tokens"]` with `kwargs[self._max_tokens_param_name()] = request.max_tokens` (instance wrapper reads `self.config.model_name`).
- **Judging field**: use `config.model_name` (NOT deployment_name — deployment is a user-chosen string with no model-generation guarantee). Requires `config.model_name` to reflect the real deployment generation — see §3.4 + §8 Risk.

### 3.3 e2e workflow max-tokens param alignment (US-2) — `.github/workflows/e2e-real-llm-smoke.yml`
- The smoke's `MAX_TOKENS_PER_CALL` cost-guard (`:173`) flows into the chat request `max_tokens`. With 3.2 in place, the adapter auto-translates per model — **no workflow change needed** if the cap goes through `ChatRequest.max_tokens`. Confirm the smoke driver sets `ChatRequest.max_tokens` (not a raw Azure kwarg). If it bypasses the adapter, align it. (Verify in Day 3; likely no-op.)

### 3.4 config.model_name alignment (US-2 prerequisite) — env/config
- If the live deployment returns `gpt-5.2-...` but `config.model_name` is stale (`gpt-4o`), 3.2 mis-branches. Day 3 real-LLM probe will print `response.model`; align `config.model_name` (env `AZURE_OPENAI_MODEL_NAME` or config default) to the real generation so the param branch is correct. This is an env/config alignment, not code — documented as a verification step, not a code deliverable.

### 3.5 Tests (US-4) — `test_pricing_loader.py` + adapter unit test
- `test_pricing_loader.py` (extend): (a) exact hit unchanged; (b) `get_llm_pricing("azure_openai","gpt-5.2-2025-12-11")` → returns the `gpt-5.2` base price (normalize branch); (c) unknown model with no base → `None`; (d) a non-date-suffixed unknown → `None` (no false normalize).
- adapter unit test (extend `test_integration.py` or NEW `test_max_tokens_param.py`): `_max_tokens_param_name("gpt-5.2")` → `max_completion_tokens`; `("gpt-4o")` → `max_tokens`; `("gpt-5.4")` → `max_completion_tokens`. (Pure function; no live call.) If feasible with the existing mock client, assert the kwargs key emitted for a gpt-5 vs gpt-4 config.
- cost_ledger None-branch (extend `test_cost_ledger_us4.py` if cheap): confirm a model that resolves via normalize records `unit_cost>0` (uses a mock PricingLoader with a base key).

### 3.6 real-LLM verification (US-5) — manual, user `.env`
- Clean restart backend (Risk Class E — kill stale `--reload` workers first; confirm startup log `pricing loader wired` `main.py:167`).
- Run the real-LLM smoke (local `.env`, NOT GitHub secrets): one chat turn → capture `response.model` (confirms real deployment id) → query `cost_ledger` newest rows → assert `unit_cost_usd > 0` (Δ≥2 input+output rows, both priced).
- Run a token-capped call (set `ChatRequest.max_tokens`) → assert no 400 (max_completion_tokens accepted).
- Record actual `response.model` string + cost rows in progress.md Day 3 (evidence).

### 3.7 Lint / validation
`mypy src/` + `pytest` (new + regression) + `python scripts/lint/run_all.py` (10/10 — no schema change, no LLM-SDK leak: `re` + yaml only, adapter param naming is provider-internal). NO frontend changes.

---

## 4. File Change List

**NEW (0-1)**
- `backend/tests/unit/adapters/azure_openai/test_max_tokens_param.py` (if not extending `test_integration.py`)

**EDIT (4-5)**
- `backend/src/platform_layer/billing/pricing.py` (date-suffix normalize in `get_llm_pricing` + `_strip_version_suffix` helper + `import re`)
- `backend/config/llm_pricing.yml` (add `azure_openai.gpt-5.2` price + bump `last_updated`)
- `backend/src/adapters/azure_openai/adapter.py` (`_max_tokens_param_name` helper + 2 call-site swaps :210-211 / :282-283)
- `backend/tests/unit/billing/test_pricing_loader.py` (normalize/None branch tests)
- `backend/tests/integration/adapters/.../test_integration.py` (kwargs param assertion — if extending instead of NEW file)

**NO frontend / migration / wire-schema / ORM change.**

---

## 5. Acceptance Criteria

- `get_llm_pricing("azure_openai", "gpt-5.2-2025-12-11")` returns the `gpt-5.2` base price (not None); unknown models still return None; cost row records `unit_cost>0` for gpt-5.2.
- adapter emits `max_completion_tokens` for `model_name.startswith("gpt-5")`, `max_tokens` otherwise — both chat + stream paths; verified by unit test.
- real-LLM smoke (user `.env`): startup log `pricing loader wired`; `response.model` captured; cost_ledger newest rows `unit_cost_usd > 0`; a token-capped call returns no 400.
- Gates: backend mypy 0 + pytest (new + regression) green + run_all 10/10. No frontend.

---

## 6. Deliverables

- [ ] Gap 1: `get_llm_pricing` date-suffix normalize + `gpt-5.2` yaml price (user-provided values)
- [ ] Gap 2: adapter `_max_tokens_param_name` + 2 call-site swaps (chat + stream)
- [ ] Unit tests: pricing normalize/None branch + adapter param branch (+ cost_ledger None-branch if cheap)
- [ ] real-LLM Azure verification (startup log + response.model + cost_ledger unit_cost>0 + no-400 token cap) — evidence in progress.md
- [ ] All gates green; closeout (CHANGE-047 + progress + retro + MEMORY + CLAUDE lean; both ADs CLOSED → C-11 billing-correctness DONE)

---

## 7. Workload Calibration

Scope class `medium-backend` (0.80 — 2 small backend fixes + real-LLM verification leg). **Agent-delegated: no** (parent-direct — billing correctness needs care + real-LLM verification is a parent/user collaboration that can't be delegated). `agent_factor` = 1.0 → 3-segment form.

Bottom-up est ~7.5 hr (Gap1 ~2 + Gap2 ~2 + tests ~1.5 + real-LLM verify ~1 + closeout ~1) → class-calibrated commit ~6 hr (mult 0.80).

---

## 8. Dependencies & Risks

- **Dependency D1 (gpt-5.2 USD pricing — user-provided)**: `gpt-5.2` is the project's internal model id; its real per-million USD price must come from the user / Azure pricing reference. Plan §3.1 leaves the yaml values as a Day-1 fill-in. **Cannot fabricate** (a wrong price is just a different billing inaccuracy). Block Day-1 yaml edit until confirmed; the normalize code + tests can proceed with a fixture price.
- **Dependency D2 (live Azure `.env`)**: real-LLM verification (§3.6) needs the user's local `.env` with a working `AZURE_OPENAI_*` key. User confirmed available.
- **Risk: config.model_name staleness (D-DAY0-6)**: Gap-2 branches off `config.model_name`; if it's stale (`gpt-4o`) while deployment is `gpt-5.2`, it mis-branches → still 400. Mitigation: Day-3 probe prints `response.model`; align `config.model_name` before asserting; unit tests pin the helper logic independent of env.
- **Risk Class E (stale `--reload` masks wiring)**: real-LLM verify must clean-restart backend (kill stale reloader+worker on :8000, confirm `pricing loader wired` startup log) — else a stale process gives a false negative. Per `sprint-workflow.md §Common Risk Classes E`.
- **Risk: normalize over-matches**: `_strip_version_suffix` must only strip a trailing `-YYYY-MM-DD` (anchored `$`), not arbitrary trailing digits — unit test (d) guards a non-date unknown returns None (no false base match).
- **Risk: max_completion_tokens unsupported on old api_version**: gpt-5.x deployments use a newer api_version that accepts the param. If the e2e gate's api_version is old, alignment may also be needed — verify in Day 3 (likely fine; api_version is per-deployment).
- **Dependency**: PricingLoader startup wiring (FIX-022) + cost_ledger record path (56.3) live. No new infra.

---

## 9. Out of Scope (this sprint; carryover)

- **B-7 ErrorBudget Redis wiring** — `RedisBudgetStore` not wired + `handler.py:218` per-request rebuild; the billing bundle's budget half. Separate sprint.
- **B-8 Verification default-enable** — deliberately deferred (3 launch-blockers); judge-token cost_ledger accounting is its concern, not this sprint's.
- **C-15 DevOps/data-platform billing** — the bundle's third leg.
- **Auto-sync pricing from provider API** — `llm_pricing.yml:3` notes a future Phase 56.x audit-cycle idea; stays manual yaml this sprint.
- **GitHub Secrets + scheduled e2e gate** (`AD-CI-6`) — real-LLM CI stays manual workflow_dispatch + local `.env`; production-launch concern.
