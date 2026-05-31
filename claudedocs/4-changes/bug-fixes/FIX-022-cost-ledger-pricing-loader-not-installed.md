# FIX-022: cost_ledger never written — PricingLoader not installed at app startup

**Date**: 2026-05-31
**Sprint**: between-sprints (post Sprint 57.62)
**Scope**: Phase 56 SaaS Stage 1 billing (Cat 12 cross-cutting) — API startup wiring + chat router pricing fallback
**Source**: `claudedocs/5-status/runtime-verification-20260530.md` §5.1 (P1) + §6.2
**Branch**: `fix/cost-ledger-pricing-loader`

## Problem

A real, billable Azure OpenAI chat call (runtime-verification 2026-05-30, Run #2)
persisted a `sessions` row (+1) and a `tool_calls` row (+1) but wrote **zero**
`cost_ledger` rows. No billing record exists for real LLM spend on the success path.

## Root Cause

Confirmed by code inspection (real grep/read outputs, not hypothesis) — this is
H1 of the two §5.1 hypotheses; H2 was NOT the blocker:

1. The chat router builds a per-request `CostLedgerService` **only** when a pricing
   loader is present — `router.py:253` `if pricing_loader is not None:` else
   `cost_ledger_service = None`.
2. The ledger write is further gated at `router.py:393`
   `if cost_ledger is not None and (event.input_tokens > 0 or event.output_tokens > 0)`.
3. `maybe_get_pricing_loader()` (`pricing.py:142`) returns the module-level
   `_loader`, `None` until `set_pricing_loader()` is called.
4. **`set_pricing_loader(` has ZERO call sites in `backend/src`** (grep: only the
   definition + a docstring mention). The production lifespan `api/main.py:_lifespan()`
   loaded `.env` + logging + OTel + rate-limit counter, but **never installed the
   PricingLoader**.

→ `_loader` was always `None` → `cost_ledger_service` always `None` → the
`record_llm_call` write was always skipped. Since Sprint 56.3 US-4 wired the
**router consumer** but never the **startup producer** — a classic AP-4
(wired-but-never-activated) gap. It is a real production bug, not a probe artifact
(the inline runtime probe had no lifespan, but production has the same gap because
the lifespan never wires the loader either).

`record_llm_call` itself is correct: given a non-None loader + tokens > 0 it writes
two rows (input + output split); unknown (provider, model) records at zero cost
(`cost_ledger.py:129`).

## Solution

Surgical, fail-soft, mirroring the existing `_wire_rate_limit_counter()` idiom.

1. **`backend/src/api/main.py`** — add `_wire_pricing_loader()` (loads
   `backend/config/llm_pricing.yml` into a `PricingLoader`, calls
   `set_pricing_loader()`; on any error logs a warning and leaves the loader
   `None` so cost-ledger writes degrade to a no-op rather than blocking startup).
   Call it in `_lifespan()` right after `_wire_rate_limit_counter()`.

2. **`backend/tests/unit/api/test_main_lifespan.py`** — add
   `test_lifespan_wires_pricing_loader_from_yaml`: asserts the loader is `None`
   before startup and non-None (with the yaml parsed) after the lifespan runs.
   The precise regression guard for this bug; a mock-path test, distinct from the
   `real_llm` regression test recommended in §5.2 (still open).

### §6.2 model-identity clarification (no pricing data invented — deferred)

Per user decision (2026-05-31): fix H1 + **document** the model-identity mismatch;
do **not** invent USD pricing figures. Documented + consolidated only:

- The identities are mismatched **4 ways**:
  - `.env` `AZURE_OPENAI_DEPLOYMENT_NAME=gpt-5.2` (the deployment actually called)
  - `config.py` `model_name` default `gpt-4o` (and `ChatResponse.model` falls back
    to it — `adapter.py:448`)
  - chat router / cost-ledger fallback string `gpt-5.4`
  - `llm_pricing.yml` `azure_openai` keys = `{gpt-4o-mini, gpt-5.4}` only
- **Consequence**: only `gpt-5.4` resolves to real pricing. `gpt-4o` and `gpt-5.2`
  return `get_llm_pricing → None` → rows written at **$0** (observable anomaly).
  After this fix cost rows **appear**, but a call billed as gpt-4o/gpt-5.2 is
  priced at $0 until the real model + USD pricing is aligned in `llm_pricing.yml`.
- **Code tidy (behavior-preserving)**: the bare `"gpt-5.4"` literal in `router.py`
  is consolidated into `_FALLBACK_PRICING_MODEL` with a comment documenting the
  4-way mismatch; the stale "uses default azure_openai/gpt-5.4" attribution
  docstring in `cost_ledger.py` (contradicted by the truthful 57.2 `record_llm_call`
  docstring) is corrected.

### Deferred follow-up (NOT in this fix)

- Add the real production model + its USD per-million pricing to `llm_pricing.yml`
  and align `AZURE_OPENAI_MODEL_NAME` so cost rows carry non-zero cost
  (needs real pricing data the assistant must not invent).
- Confirm token flow on the real path: H2 — whether streaming Azure responses
  populate `usage` so `LoopCompleted.input_tokens/output_tokens > 0` (the second
  AND clause of the `router.py:393` gate). Verifiable only via a `real_llm` run
  (runtime-verification §5.2 — still open).

## Verification

All from real tool output on branch `fix/cost-ledger-pricing-loader`:

- `pytest tests/unit/api/test_main_lifespan.py tests/integration/api/test_chat_cost_ledger.py
  tests/integration/api/test_chat_e2e.py tests/integration/api/test_admin_cost_summary.py
  tests/unit/platform_layer/billing/` → **25 passed** (incl. the new
  `test_lifespan_wires_pricing_loader_from_yaml`). The integration `conftest.py`
  autouse `reset_pricing_loader()` keeps per-test isolation, so installing the
  loader at startup does not regress tests that expect no cost rows.
- `flake8` (4 changed files) → exit 0.
- `black --check` (4 changed files) → 4 files unchanged.
- `isort --check-only` (4 changed files) → exit 0.
- `mypy src/api/main.py src/api/v1/chat/router.py src/platform_layer/billing/cost_ledger.py`
  → **Success: no issues found in 3 source files**.
- `python scripts/lint/run_all.py` (repo root) → **exit 0; 9/9 V2 lints PASS**
  (AP-1 / LLM SDK Leak / PromptBuilder / Cross-Category Import / Duplicate
  Dataclass / Sole Mutator / Sync Callback / RLS Policies / AP-4 Frontend
  Placeholder). This fix closes an AP-4 instance rather than adding one.

**Not yet verified**: that a real Azure call now produces non-zero `cost_ledger`
rows end-to-end. This fix removes the H1 blocker (loader installed → service
constructed → write reached); whether the row carries non-zero cost depends on the
deferred §6.2 pricing alignment + H2 token-flow confirmation (a real_llm run).

## Impact

- Backend only. Production behavior change: at startup the app now installs the
  PricingLoader, so the chat router constructs `CostLedgerService` and reaches the
  `record_llm_call` write on every chat completion with tokens > 0.
- Fail-soft: if `llm_pricing.yml` is missing/malformed the loader stays `None` and
  cost-ledger writes degrade to a no-op (prior behavior) — startup never blocks.
- No DB schema change, no migration, no frontend change.

## Files Changed

| File | Change |
|------|--------|
| `backend/src/api/main.py` | + `_wire_pricing_loader()` helper; called in `_lifespan()` (H1 fix) |
| `backend/src/api/v1/chat/router.py` | consolidate `"gpt-5.4"` fallback → `_FALLBACK_PRICING_MODEL` + §6.2 comment |
| `backend/src/platform_layer/billing/cost_ledger.py` | correct stale attribution docstring + §6.2 pricing caveat |
| `backend/tests/unit/api/test_main_lifespan.py` | + `test_lifespan_wires_pricing_loader_from_yaml` regression test |
