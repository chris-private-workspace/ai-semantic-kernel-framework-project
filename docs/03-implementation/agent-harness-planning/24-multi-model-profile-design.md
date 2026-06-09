---
title: 24-multi-model-profile design note
purpose: Spike-extract design note from Sprint 57.97; documents verified runtime invariants for the multi-model ModelProfile seam (verification routed to a cheap tier)
category: V2 extension docs (post-22-sprint era)
created: 2026-06-10 (Sprint 57.97 Day 4 closeout)
sprint_source: 57.97
verified_ratio: ≥ 95% (per 8-Point Quality Gate)
status: Active
---

# 24-multi-model-profile Design Note (Sprint 57.97 extract)

> **8-Point Quality Gate self-check** (per `sprint-workflow.md §Step 5.5` + `claudedocs/templates/spike-design-note-template.md`):
> [x] 1. Section headers map to US-1..US-5 · [x] 2. every claim has file:line · [x] 3. Decision Matrix (4-row) · [x] 4. reproducible verify commands · [x] 5. test fixture refs · [x] 6. Open Invariants fenced from Verified · [x] 7. Rollback path · [x] 8. 17.md cross-ref (`ModelProfile` registered §2.1)

## 0. Spike Summary

- **Sprint scope**: US-1 thin `ModelProfile{action, cheap}` value object · US-2 cheap config + fallback · US-3 verification (llm_judge) routed to cheap · US-4 cost attribution + neutrality + loop-unchanged · US-5 drive-through (verification ran cheap, visible cost delta).
- **Verified period**: 2026-06-09 (Day 0-3) ~ 2026-06-10 (Day 4 closeout).
- **Calibration**: bottom-up ~14 hr → class-calibrated commit ~7.5 hr (NEW class `multi-model-profile-spike` 0.55; agent-delegated **no** → `agent_factor 1.0`). Ratio recorded in retrospective Q2.
- **Verification**: pytest **+8** new (2283 → 2291; 0 deletions) + mypy 0/353 + run_all 10/10 + **drive-through PASS** (real Azure, cost_ledger-proven ~62% cheaper verification).

## 1. Decision Matrix (how to select a model per phase)

| Approach | Mechanism | Verdict | Reason |
|----------|-----------|---------|--------|
| **Per-call `model=` param on `ChatClient.chat()`** | pass the model at each call site | ❌ Rejected | The `ChatClient` ABC fixes the model at construction — `chat()`/`stream()` have NO `model=`/`deployment=` param (`adapters/_base/chat_client.py:69-93`); adding one breaks the locked single-source contract (17.md §2.1) for all adapters. |
| **`ModelProfileChatClient` ABC wrapper** (a `ChatClient` that internally dispatches by phase) | wrap N clients behind the ABC | ❌ Rejected | The ABC has no phase concept; a dispatching wrapper would need a phase param threaded through `chat()` → same contract break as above, plus a heavier abstraction (AP-6 hybrid-bridge debt for one consumer). |
| **Thin `ModelProfile{action, cheap}` value object** | build N clients upfront, callers read the field for their phase | ✅ **CHOSEN** | Zero ABC change; provider-neutral (holds only the ABC, no SDK); single-source seam — future tiers add a field, not a new injection site; `loop.py` diff = 0 (`adapters/_base/model_profile.py:46-58`). |
| **Direct injection (no value object)** | pass a bare `cheap_client` to the verifier factory only | ❌ Rejected | Works for one consumer but leaves no single-source seam — the next phase (compaction/memory/thinking) would re-derive the cheap client at a 2nd site → scatter (AP-3). The value object centralizes the pairing for ~0 extra cost. |

**Per-call vs per-construction was the crux**: the recon confirmed model selection is per-CLIENT-construction (the deployment is immutable instance state — `AzureOpenAIAdapter.__init__(config)` `azure_openai/adapter.py:121`, used at `:197`), so the only correct seam is "build 2+ clients, select by phase".

## 2. Verified Invariants

### 2.1 US-1 — `ModelProfile` is a frozen, provider-neutral value object
- **Implementation**: `backend/src/adapters/_base/model_profile.py:46-58` — `@dataclass(frozen=True) class ModelProfile` with `action: ChatClient` + `cheap: ChatClient`; imports ONLY `from adapters._base.chat_client import ChatClient` (no SDK). Re-exported at `adapters/_base/__init__.py`.
- **Behavior**: pairs two pre-built clients by role; immutable (reassignment raises `FrozenInstanceError`); no construction / no dispatch method.
- **Verification**: `pytest backend/tests/unit/adapters/_base/test_model_profile.py` (3 tests: pairs action/cheap; frozen; same-instance fallback shape). Neutrality: `python backend/scripts/lint/check_llm_sdk_leak.py` → 0 (within `run_all`).
- **Test fixture**: in-test `cast(ChatClient, object())` placeholders (no real client needed — the value object only holds refs).

### 2.2 US-2 — cheap config + byte-identical fallback
- **Implementation**: `backend/src/adapters/azure_openai/profile.py:54-82` — `build_azure_model_profile(strong_client)`. Reads `AZURE_OPENAI_CHEAP_DEPLOYMENT_NAME` (`:63`). Unset → `ModelProfile(action=strong, cheap=strong)` (same instance, `:66`). Set → a 2nd `AzureOpenAIAdapter(AzureOpenAIConfig(deployment_name=cheap, model_name=...))` reusing the shared endpoint/key/api_version loaded by BaseSettings from env (`:75-81`).
- **Behavior**: explicit kwargs override env in pydantic-settings, so the strong `AZURE_OPENAI_DEPLOYMENT_NAME` is overridden by the cheap deployment for the cheap instance only; the connection (endpoint/key) is shared.
- **Verification**: `pytest backend/tests/unit/adapters/azure_openai/test_profile.py` (3 tests: unset→`cheap is action` identity; set→distinct `AzureOpenAIAdapter` with cheap `deployment_name`/`model_name`; `model_name` defaults to the deployment when `AZURE_OPENAI_CHEAP_MODEL_NAME` unset).
- **Test fixture**: `monkeypatch.setenv("AZURE_OPENAI_ENDPOINT"/"AZURE_OPENAI_API_KEY"/"AZURE_OPENAI_CHEAP_DEPLOYMENT_NAME", ...)` placeholders; `.env.example` documents the production vars.

### 2.3 US-3 — verification runs on the cheap tier; loop + compaction stay strong
- **Implementation**: `backend/src/api/v1/chat/handler.py` (`build_real_llm_handler`) — `profile = build_azure_model_profile(chat_client)`; verifier ← `profile.cheap` via `make_chat_verifier_registry(profile.cheap, ...)` (~`:479`); the loop (`AgentLoopImpl(chat_client=...)`), compactor (`make_chat_compactor(...)`), prompt builder and subagents keep `chat_client` (== `profile.action`). `LLMJudgeVerifier.__init__(chat_client=)` already accepts a `ChatClient` (`verification/llm_judge.py:74`) → no signature change.
- **Behavior**: the per-request verification (default-ON since 57.83) calls the cheap deployment; the user-facing main turn (`loop.py:1954`) is untouched. **`loop.py` diff = 0.**
- **Verification**: `pytest backend/tests/unit/api/v1/chat/test_handler.py -k "cheap or verifier"` (the verifier's `_chat` deployment == cheap + the loop's `_chat_client` deployment == strong; cheap unset → verifier shares the loop's action client).
- **Test fixture**: `monkeypatch.setenv` for the AZURE vars + a `SimpleNamespace` patch of `api.v1.chat.handler.get_settings` to force verification enabled.

### 2.4 US-4 — cost attributed to the cheap model; no SDK leak; loop diff = 0
- **Implementation**: cost is NOT priced via the adapter — `platform_layer/billing/cost_ledger.py` `record_llm_call(provider, model, tokens, sub_type_suffix)` prices via `config/llm_pricing.yml` (`PricingLoader.get_llm_pricing(provider, model)`, model-keyed, Azure version-suffix stripped). `LLMJudgeVerifier` already captures `response.model` (Sprint 57.82, `verification/llm_judge.py:97-103`) → routing the verifier to the cheap client makes the cheap MODEL NAME flow to the cost-ledger automatically. The cheap + strong models are priced in `config/llm_pricing.yml:15-30`.
- **Behavior**: the verification call records a distinct sub_type `azure_openai_<cheap-model>_verification_*` (vs the main turn's `azure_openai_<strong-model>_*`); the model-attribution difference is visible regardless of pricing, and the $ delta is visible because both models are priced.
- **Verification**: `python backend/scripts/lint/run_all.py` → 10/10 (`check_llm_sdk_leak` 0); `git diff main -- backend/src/agent_harness/orchestrator_loop/loop.py` → empty.

### 2.5 US-5 — drive-through (real Azure, visible cost delta)
- **Behavior**: a chat-v2 request with `AZURE_OPENAI_CHEAP_DEPLOYMENT_NAME=gpt-5.4-mini` → verification recorded at gpt-5.4-mini (~$0.000301) while the main turn ran at gpt-5.2 → **~62% cheaper verification**, answer quality unchanged.
- **Verification**: `pytest -m real_llm` not used here; the drive-through was manual (real UI + real backend + real Azure). Reproduce: set `AZURE_OPENAI_CHEAP_DEPLOYMENT_NAME=gpt-5.4-mini` in `.env`, clean-restart the backend (verify the LIVE serving process per §5 Risk Class E), send a chat, then read the newest `cost_ledger` rows — the verification sub_type carries `gpt-5.4-mini`. Cost ~$0.0003/request (gpt-5.4-mini, 234+28 tokens) — negligible.
- **Test fixture / evidence**: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-97/artifacts/sprint-57-97-2-drivethrough-pass-cheap-verification.png` + the cost_ledger rows in `progress.md` Day 3.

## 3. Cross-Category Contracts

- **Contract: `ModelProfile`** (value object, NOT an ABC)
  - **Owner**: this design note (`24-multi-model-profile-design.md`); home category = adapters/_base (the home of `ChatClient`).
  - **Registered at**: `17-cross-category-interfaces.md` §2.1 (a `ModelProfile` row noting it WRAPS pre-built `ChatClient`s by role and does NOT modify the `ChatClient` ABC).
  - **Signature**: `@dataclass(frozen=True) class ModelProfile: action: ChatClient; cheap: ChatClient`.
  - **Builder** (provider-specific, NOT a contract): `build_azure_model_profile(strong_client: ChatClient) -> ModelProfile` in `adapters/azure_openai/profile.py`.

## 4. Open Invariants (deferred — NOT verified this sprint)

- [ ] **Compaction / memory-extraction / thinking cheap-tier** — the seam is built; only verification is wired. Adding `profile.compaction` etc. is a follow-on (add a field defaulting to `action` + the consuming factory reads it). Compaction is the highest token-volume target but needs a long conversation to drive-through.
- [ ] **Threading `ModelProfile` into the loop** — this sprint keeps it handler-local (constructed + consumed in `handler.py`). In-loop per-phase selection is a separate slice.
- [ ] **Per-tenant model policy (Config 分層)** — a tenant choosing its own model/budget is the SEPARATE "Config 分層" parity gap (cc-parity §7.3), not this sprint.
- [ ] **Cheap-judge accuracy** — a cheaper judge MAY be less reliable. NOT formally benchmarked; the drive-through observed the judge still functioned (score ≈0.98). The action turn is NEVER cheap (user-facing quality preserved). If the cheap judge visibly mis-verifies, keep the judge on the strong tier (the seam supports per-phase choice).
- [ ] **Non-Azure cheap tiers** — the seam is provider-neutral but only the Azure builder is wired. An Anthropic/OpenAI cheap tier is a follow-on builder.
- [ ] **LLM-call Trace span `model` attribute** — deferred: the cost-ledger sub_type (`azure_openai_<model>_verification_*`) already carries the model attribution, so no span change was needed for the drive-through. Add a span attr only if a future Trace-view feature needs per-call model on the span itself.

## 5. Rollback / Fallback

- **Soft rollback (no code change)**: unset `AZURE_OPENAI_CHEAP_DEPLOYMENT_NAME` in `.env` → `build_azure_model_profile` returns `cheap is action` → byte-identical to 57.96 (verification back on the strong tier). The fallback is the safety net — already in place + tested (`test_profile.py` unset→identity).
- **Hard rollback (revert the feature)**: revert the `handler.py` verifier arg (`profile.cheap` → `chat_client`) + delete `adapters/_base/model_profile.py` + `adapters/azure_openai/profile.py` + the `__init__.py` re-export + the 3 test files + the `llm_pricing.yml` cheap-model rows. Est. ~30 min. No DB/migration/event-schema to unwind.
- **Sentinel already in place**: the unset-fallback (`cheap is action`) means a misconfigured / unavailable cheap deployment degrades to the strong tier, not to an error.

## 6. References
- Sprint plan: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-97-plan.md`
- Sprint retrospective: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-97/retrospective.md`
- Change record: `claudedocs/4-changes/feature-changes/CHANGE-064-multi-model-profile-verification.md`
- Source: `claudedocs/5-status/agent-harness-cc-parity-20260607.md` §4 (C-class) + §6 (priority 1) + 圖 D 波次 1 R1
- Related contracts: `17-cross-category-interfaces.md` §2.1 (`ChatClient` ABC — WRAPPED; `ModelProfile` registered)
- Related rules: `.claude/rules/sprint-workflow.md` §Common Risk Classes Risk Class E (orphaned spawn-worker, reinforced this sprint) · `docs/rules-on-demand/llm-provider-neutrality.md`

## Modification History
- 2026-06-10: Initial extract from Sprint 57.97 closeout (Day 4) — multi-model `ModelProfile` seam; verification routed to cheap tier
