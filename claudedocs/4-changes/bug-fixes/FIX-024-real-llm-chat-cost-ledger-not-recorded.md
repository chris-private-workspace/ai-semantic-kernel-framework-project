# FIX-024: real_llm chat path records 0 cost_ledger rows (cost never billed)

**Date**: 2026-06-01
**Sprint**: C-11 real-LLM e2e local verification (pre-billing-bundle)
**Scope**: cross-cutting — `platform_layer/billing` + `adapters/azure_openai` + `api/v1/chat`
**Status**: 🔎 Root cause narrowed (1 runtime check pending); **NOT yet fixed** (rolling discipline — feeds billing bundle B-7/B-8/C-15)
**Severity**: High (silent revenue leakage in SaaS — every real_llm chat is un-billed)

> This record is the by-product of C-11 (`AD-Cat4-7-8-10-RealLLM-E2E`) local verification. C-11 PRIMARY purpose (real LLM e2e works on the chat path) **PASSED**; this FIX documents the secondary `cost_ledger Δ≥2` assertion that current code does NOT satisfy.

---

## Problem

Running the `e2e-real-llm-smoke.yml` verification locally against a **fresh current-code backend** (HEAD `64f29259`, restarted 2026-06-01):

- ✅ HTTP 200 (not 503), SSE `event: loop_end`, `audit_log` Δ=1 — real LLM e2e works.
- ❌ **`cost_ledger` Δ=0** — zero cost rows written for a successful billable LLM call.

The GitHub Actions gate's `cost_ledger Δ≥2` assertion has **never been validated** (the gate never ran green — Azure secrets were unprovisioned), so this latent gap went undetected. Current code does not satisfy it.

## Root Cause Analysis

The cost write lives at `backend/src/api/v1/chat/router.py:412`:
```python
if cost_ledger is not None and (event.input_tokens > 0 or event.output_tokens > 0):
    await cost_ledger.record_llm_call(...)
```
`Δ=0` (zero ROWS) means `record_llm_call` was **never called** — because `record_llm_call` writes 2 rows even for unknown pricing (`cost_ledger.py:138-140` "Unknown (provider, model) → record at zero cost"). So the `if` was False.

Investigation **ruled out** the obvious suspects:
- **Adapter streaming / missing `stream_options.include_usage`** — NO. The loop calls the **non-streaming** `chat()` (`loop.py:939`), and a direct probe proved the real Azure call returns usage: `prompt_tokens=12, completion_tokens=9, total_tokens=21` on `gpt-5.2-2025-12-11`.
- **Loop not propagating usage** — NO. Both completion branches (`loop.py:1021-1030` END_TURN-terminator + `loop.py:1037-1048` FINAL) set `input_tokens/output_tokens = metrics_acc.cumulative_*`, accumulated from `response.usage` at `loop.py:961-964`.
- **`pricing_loader` not wired to endpoint** — NO. `router.py:139` injects `Depends(maybe_get_pricing_loader)`; `_wire_pricing_loader()` is called at startup (`main.py:165`); `llm_pricing.yml` loads OK; `set_pricing_loader → maybe_get_pricing_loader` round-trips non-None in-process.

Since usage IS available (>0) and the loader set/get mechanism works in-process, the only remaining way for the gate to be False is **`cost_ledger is None` at the running endpoint** → `pricing_loader` (i.e. `maybe_get_pricing_loader()`) returns `None` at runtime despite the startup wiring.

**Leading hypothesis (pending 1 runtime check)**: **double module import** under uvicorn `--app-dir src`. If `platform_layer.billing.pricing` is imported under two distinct module identities (e.g. `platform_layer.billing.pricing` at startup vs a different path prefix at request time), the module-level `_loader` global set by startup is invisible to the request handler. Confirm by inspecting the running process's `sys.modules` for duplicate `*.pricing` entries (do in the billing-bundle sprint).

### Two RELATED findings surfaced (independent bugs)

1. **Pricing config stale vs actual deployment** — `config/llm_pricing.yml` lists `azure_openai: {gpt-4o-mini, gpt-5.4}` but the live deployment is **`gpt-5.2`** (`AZURE_OPENAI_DEPLOYMENT_NAME`; `response.model=gpt-5.2-2025-12-11`). `get_llm_pricing('azure_openai','gpt-5.2') → None`. So even once the loader issue is fixed, gpt-5.2 calls would be recorded at **zero cost** (silent under-billing). `gpt-5.4` (not 5.2) and `gpt-4o` (not used) suggest the yaml drifted from the actual deployment.

2. **Adapter `max_tokens` incompatible with gpt-5.x** — `adapter.py:210-211` sends `max_tokens`; gpt-5.2 rejects it with `400 Unsupported parameter: 'max_tokens' is not supported with this model. Use 'max_completion_tokens' instead.` The chat path works ONLY because the loop passes `request.max_tokens=None` (adapter skips the kwarg). Any path that sets a token cap (the e2e workflow's `MAX_TOKENS_PER_CALL`, or future compaction/verification sub-calls) will 400 on gpt-5.x deployments. Latent adapter compatibility bug.

## Solution (recommended — NOT yet applied)

Fold into the billing-correctness bundle (B-7/B-8/C-15):
1. **Loader-None runtime bug** — confirm double-import via `sys.modules`; if so, normalize the import path (single canonical `platform_layer.billing.pricing` identity) or move the loader to app-state instead of a module global. (Root fix for Δ=0.)
2. **Pricing config** — add `azure_openai: gpt-5.2` (and the actual deployed model id) to `llm_pricing.yml`; consider an audit-cycle check that every configured deployment has a pricing row. Consider making `record_llm_call` LOG a warning (not silent) when pricing is None.
3. **Adapter** — branch `max_tokens` → `max_completion_tokens` for gpt-5.x / reasoning models in `adapter.py` (both `chat()` and `stream()` paths).
4. **e2e gate** — once 1-3 land, `e2e-real-llm-smoke.yml`'s `cost_ledger Δ≥2` will pass; until then the assertion is known-red on gpt-5.x.

## Verification

- Reproduced: fresh current-code backend, dev-login → `POST /api/v1/chat/ {mode:real_llm}` → `loop_end` + `audit_log` Δ=1 but `cost_ledger` Δ=0 (counts read from container `ipa_v2_postgres` db `ipa_v2`).
- Usage probe (throwaway, deleted): non-streaming Azure call returns `prompt_tokens=12 completion_tokens=9 total_tokens=21`.
- In-process: `set_pricing_loader → maybe_get_pricing_loader()` non-None; `get_llm_pricing('azure_openai','gpt-5.2')=None`, `gpt-5.4`=present.
- **Pending**: runtime `sys.modules` inspection to confirm double-import (the proximate cause of `cost_ledger is None`).

## Impact

- **Billing**: every `real_llm` chat on the gpt-5.2 deployment is currently un-billed (0 cost rows). Direct revenue-leakage risk for SaaS Stage 1. Also blocks the e2e gate's cost assertion.
- **Scope**: backend only; no frontend impact. Connects to the billing-correctness work bundle (C-15 cost_ledger + B-7 RedisBudgetStore + B-8 verification cost).
- **Backend state note**: during this verification the long-running (16-day-stale) dev backend was restarted to current code (`--reload`, healthy) — a side improvement, not part of the fix.
