# Sprint 57.65 Plan — Memory Auto-Inject + Prompt-Cache Observability (A-1 Tier2 + A-2 Tier2)

**Purpose**: Land the two Tier-2 Area-A capabilities that 57.64 (Tier-1) unblocked. **A-1 Tier2**: make the production chat path actually *render* a per-turn L1-L4 memory summary (≤2000 tokens) into the system prompt + inject `verify_before_use` lead-then-verify rules — today the PromptBuilder *fetches* hints but never renders them, and is fed an empty `MemoryRetrieval`. **A-2 Tier2**: surface prompt-cache effectiveness — the Azure caching pipe (`prompt_cache_key` + `cached_input_tokens`) is already complete end-to-end, but the loop drops the cached-token signal; accumulate it + emit a Cat 12 cache-hit-rate metric. Day-0 audit overturned the analyses' "動 loop.py at the LLM-call site" premise (stale): the call-site already forwards breakpoints, so the only loop.py change is a small metrics accumulation.
**Category / Scope**: Cat 5 (Prompt Construction — memory render) + Cat 3 (Memory Tier2) + Cat 4/12 (prompt-cache observability); Phase 57.65
**Created**: 2026-06-01
**Status**: Draft (pending user scope approval; code execution gated)
**Source**: `claudedocs/5-status/area-a-integration-sequencing-capstone-20260531.md` (候選 Sprint B) + `cat3-memory-loop-injection-analysis-20260531.md` (A-1) + `cat5-promptbuilder-loop-injection-analysis-20260531.md` (A-2) + **Day-0 post-57.64 reality audit (codebase-researcher, 2026-06-01)** which corrected the analyses' pre-57.64 baseline (D1-D6 below)

> **Modification History**
> - 2026-06-01: Initial creation — 候選 Sprint B; folds Day-0 audit drift (D1 caching-already-wired, D2 cached_input_tokens-already-populated, D3 memory-hints-fetched-but-not-rendered) into §0 + §8

---

## 0. Background

This sprint is the named follow-up to Sprint 57.64 (§9: "A-1 Tier2 (memory auto-inject) + A-2 Tier2 (prompt caching) — these touch `loop.py`; next sprint (候選 Sprint B)"). 57.64 shipped Tier-1 (on-demand memory tools + PromptBuilder injected + subagent tools) at the api/factory layer. This sprint is the Tier-2 layer.

The two source analyses were baselined at `526be549` (pre-57.64). A **Day-0 reality audit on current main** found their core premises are now **stale** — the corrections below shape the real scope (folded here, not silently rewritten, per `sprint-workflow.md §Step 2.5`):

### ⚠️ Day-0 drift corrections (from post-57.64 reality audit)

- **D1 — A-2 caching call-site is ALREADY wired (analysis "discarded / requires loop.py change" is FALSE)**: `loop.py:910-912` collects `artifact.cache_breakpoints`; `loop.py:939-943` forwards them to `self._chat_client.chat(request, cache_breakpoints=…)`. The ChatClient ABC accepts them (`adapters/_base/chat_client.py:69-75`). The **Azure adapter consumes them as automatic caching** — `_compute_prompt_cache_key(cache_breakpoints)` → `extra_body={"prompt_cache_key": …}` (`adapters/azure_openai/adapter.py:216-218`) — NOT Anthropic-style `cache_control` (that exists only in `adapters/_mock/anthropic_adapter.py`, test-only). So there is **no LLM-call-site rewrite** in this sprint. `PromptCacheManager.apply_breakpoints` (`context_mgmt/cache_manager.py`) is **dead in production** (zero non-test call sites) and must NOT be wired (Azure path doesn't use it).
- **D2 — cached-token signal ALREADY populated, but DROPPED by the loop**: `TokenUsage.cached_input_tokens` exists (`_contracts/chat.py:104`); the Azure adapter populates it from `prompt_tokens_details.cached_tokens` (`adapter.py:437-443`). But the loop's `metrics_acc` reads only `prompt_tokens`/`completion_tokens` (`loop.py:961-964`) — `cached_input_tokens` flows only to billing (`cost_ledger.py:114`), never to a cache-hit metric. **A-2 Tier2 = observability only.**
- **D3 — A-1 memory is fetched but NOT rendered (hidden Potemkin gap)**: `DefaultPromptBuilder.build()` calls `_inject_memory_layers()` (`builder.py:224`) → real `self._memory_retrieval.search(tenant_id, user_id, session_id, trace_context)` (`builder.py:350-359`), storing hints in `PromptSections.memory_layers`. But `_build_system_section()` (`builder.py:283`) **ignores that dict** — hints are never turned into prompt text. Plus: `make_chat_prompt_builder` feeds an **empty** `MemoryRetrieval(layers={})` (`_category_factories.py:131`); there is **NO** `max_memory_tokens` cap anywhere (0 grep hits); `verify_before_use` is only a `MemoryHint` field (`_contracts/memory.py:76`), never injected into the system prompt (0 hits in `prompt_builder/**`); `build()` is called with `user_id=None` (`loop.py:904`) so the user-scope layer is never scoped. **A-1 Tier2 is net-new builder render/cap/verify code + a factory thread — not a one-liner.**
- **D4 — no `PromptInputs` / `memory_provider` / `MemoryLayerProvider`**: the analyses describe a build-time `memory_provider` Protocol; it does not exist. Memory comes from the **ctor dep** `memory_retrieval: MemoryRetrieval` (`builder.py:168/176`); `build()` takes `state`/`tenant_id`/`user_id`/`session_id`/`trace_context` (`_abc.py:50-60`). Wiring = pass the real `MemoryRetrieval` into the ctor (NOT a new Protocol).
- **D5 — `CacheBreakpoint` fields**: real fields are `position`/`section_id`/`content_hash`/`cache_control` (`_contracts/chat.py:147-160`), not the analysis's `{index, kind}`.
- **D6 — `PromptBuilt` already emitted**: `loop.py:915` emits it with `cache_breakpoints_count` etc.; it already reads `layer_metadata["memory_layers_used"]` (`loop.py:918`). Once memory renders, this becomes non-empty automatically.

**Net**: "動 loop.py" is now accurate ONLY for the small A-2 metrics accumulation (~`loop.py:961-969` + `LoopCompleted` emission). The real A-1 work is in `prompt_builder/builder.py` (render + cap + verify) + a `_category_factories.py` / `handler.py` thread. Scope shift is < 20% of the original bundle intent (both Tier2s still in) → continue.

---

## 1. Sprint Goal

Make the production `real_llm` chat path (1) auto-inject a per-turn L1-L4 memory summary (≤2000 tokens) + `verify_before_use` lead-then-verify rules into the system prompt — by threading the real `MemoryRetrieval` into the PromptBuilder and building the missing render/cap/verify steps — and (2) emit a Cat 12 prompt-cache-hit-rate metric by accumulating the already-populated `cached_input_tokens` the loop currently drops. Prove both on the chat SSE flow with integration tests + a `real_llm` e2e showing a non-empty memory block and a cache-hit metric. **No LLM-call-site rewrite** (Day-0 D1: already wired); the only loop.py change is metrics accumulation. LLM-neutrality preserved: memory render is provider-free; the cache signal comes through the `ChatClient`/`TokenUsage` ABC.

---

## 2. User Stories

- **US-1 (A-1 Tier2 — memory auto-inject + verify_before_use)** — As an operator, I want the agent to *see* relevant tenant/user/session memory in its system prompt every turn (capped ≤2000 tokens) and be told to verify stale hints before acting, so it reasons with continuity without me re-explaining context. → thread the real `MemoryRetrieval` (from `make_chat_memory_deps`) into `make_chat_prompt_builder`; build the render step (`MemoryHint` dict → system-prompt text block) + the ≤2000-token cap + the `verify_before_use` rule injection in `DefaultPromptBuilder`; scope by real `user_id`.
- **US-2 (A-2 Tier2 — prompt-cache observability)** — As a platform owner, I want a steady-state prompt-cache-hit-rate metric, so I can verify the Azure `prompt_cache_key` caching is actually saving input tokens (target >50%). → accumulate `cached_input_tokens` in the loop's `metrics_acc`; emit a Cat 12 cache-hit-rate signal on `LoopCompleted`.
- **US-3 (Validation)** — As a reviewer, I want integration tests proving the chat SSE path renders a non-empty, capped memory block with verify rules (+ `PromptBuilt.memory_layers_used` non-empty) and emits the cache-hit metric, plus a `real_llm` e2e, so "Tier2 live" is true at runtime, not just in isolated builder unit tests.

---

## 3. Technical Specifications

### 3.0 Shared change surface (prerequisite for US-1/2)
- **`make_chat_prompt_builder`** (`api/v1/chat/_category_factories.py:104`) — extend to accept the real `MemoryRetrieval` (today hard-codes `MemoryRetrieval(layers={})` at `:131`). Signature mirror: `make_chat_prompt_builder(chat_client, memory_retrieval=None)`; default empty preserves 57.64 standalone behavior.
- **`build_real_llm_handler`** (`api/v1/chat/handler.py`) — build the memory deps once (it already calls `make_chat_memory_deps` for the executor since 57.64), and pass the SAME `MemoryRetrieval` into `make_chat_prompt_builder` so tools + prompt share one retrieval. Thread the real `user_id` so `build()` scopes the user layer (today `loop.py:904` passes `user_id=None`).
- **LLM-neutral**: `MemoryRetrieval`/layers never touch `ChatClient`; the cache signal is read from the neutral `TokenUsage.cached_input_tokens`. `agent_harness/**` stays SDK-import-clean.

### 3.1 A-1 Tier2 memory render + cap + verify (US-1) — `prompt_builder/builder.py` (net-new)
- **Render**: `_build_system_section()` (`:283`) must consume `PromptSections.memory_layers` (the `dict[str, list[MemoryHint]]` already populated by `_inject_memory_layers` at `:224`/`:350-359`) into a deterministic system-prompt text block (scope-grouped; each hint shows summary + confidence + `last_verified_at`).
- **Cap**: enforce a `max_memory_tokens` budget (default 2000) using the injected `token_counter` (`ChatClient.count_tokens` neutral path) — truncate lowest-confidence / oldest hints first until under budget. Add `max_memory_tokens` to the builder config/ctor (D4: no `PromptInputs`).
- **verify_before_use**: when any rendered hint has `verify_before_use=True`, inject a lead-then-verify instruction block into the system prompt (per `10.md §原則3` / `01.md §範疇3`). Static rule text + the list of to-verify hints.
- **Scope**: `build()` already receives `trace_context`; read `user_id` from it (or thread real `user_id`) so `MemoryRetrieval.search(user_id=…)` scopes the user layer. Confirm tenant scoping holds (multi-tenant 鐵律).

### 3.2 A-2 Tier2 prompt-cache observability (US-2) — `loop.py` + Cat 12
- **Accumulate**: in `metrics_acc` aggregation (`loop.py:961-969`) add `cached_input_tokens` (today dropped) alongside prompt/completion.
- **Emit**: on `LoopCompleted` (`loop.py:1026-1046`) compute cache-hit-rate = `cached_input_tokens / prompt_tokens` (guard div-0) and emit it via the existing Cat 12 metrics/Tracer path (mirror how loop token metrics are emitted). If `LoopCompleted` needs a field, extend the event contract (`_contracts/events.py`) + register in 17.md.
- **No caching change**: the Azure `prompt_cache_key` path stays as-is (D1). Confirm `InMemoryCacheManager` (chat path, `_category_factories.py:132`) emits non-empty `cache_breakpoints` (so the key is stable); if it is a no-op stub, that is the only caching-side fix.

### 3.3 Validation (US-3)
- Integration tests (extend `test_chat_keystone_wiring.py` or a new `test_chat_tier2_wiring.py`): with real layers wired, a chat run renders a non-empty memory block in the assembled system prompt (assert text present + ≤2000 tokens), `verify_before_use` rule present when a flagged hint exists, `PromptBuilt.memory_layers_used` non-empty; a 2-turn run emits a cache-hit-rate metric (mock usage with `cached_input_tokens>0`). Negative guards: empty retrieval → no memory block, no crash; no cached tokens → metric = 0, no crash. Cross-tenant: tenant-B prompt shows none of tenant-A's hints.
- `real_llm` e2e: a 2-turn Azure run → 2nd turn shows `cached_input_tokens>0` (Azure auto-cache warm) and a non-empty memory block when memory exists. Gated on C-11 secrets; HTTP-level `PromptBuilt`-in-stream still blocked by A-5 (events→SSE OOS) → assert via loop event stream / metric, like 57.64.

### 3.4 Lint / neutrality
- `check_llm_sdk_leak` stays 0 (memory render + metric are provider-free). `check_promptbuilder_usage` stays true-green (57.64). No new naked-assembly.

---

## 4. File Change List

| File | Change |
|------|--------|
| `backend/src/api/v1/chat/_category_factories.py` | `make_chat_prompt_builder(chat_client, memory_retrieval=None)` — accept + use the real retrieval (was hard-coded empty `:131`) |
| `backend/src/api/v1/chat/handler.py` | pass the SAME `MemoryRetrieval` (already built for the executor) into `make_chat_prompt_builder`; thread real `user_id` into the build path |
| `backend/src/agent_harness/prompt_builder/builder.py` | **net-new**: render `memory_layers` hints → system-prompt text block in `_build_system_section`; enforce `max_memory_tokens≤2000` cap (via `token_counter`); inject `verify_before_use` lead-then-verify rules |
| `backend/src/agent_harness/prompt_builder/_abc.py` | add `max_memory_tokens` (default 2000) to the builder config/ctor if not present (D4 — no `PromptInputs`) |
| `backend/src/agent_harness/orchestrator_loop/loop.py` | accumulate `cached_input_tokens` in `metrics_acc` (~`:961-969`); emit cache-hit-rate on `LoopCompleted` (~`:1026-1046`); thread real `user_id` into `build()` if not via trace_context (~`:904`) |
| `backend/src/agent_harness/_contracts/events.py` | extend `LoopCompleted` with a cache-hit field IF needed (Day-1 confirm; else reuse existing metrics path) |
| `backend/src/agent_harness/observability/*` | Cat 12 cache-hit-rate metric hook (mirror existing loop token metrics) |
| `backend/tests/integration/api/test_chat_tier2_wiring.py` (or extend `test_chat_keystone_wiring.py`) | **NEW/extend** — memory render + cap + verify on chat SSE path + cache-hit metric + multi-tenant + negative guards |
| `docs/03-implementation/agent-harness-planning/17-cross-category-interfaces.md` | register the cache-hit metric / any new `LoopCompleted` field (single-source) |
| `claudedocs/4-changes/feature-changes/CHANGE-0XX-memory-autoinject-cache-observability.md` | change record |

**No DB migration**, **no Azure-adapter change** (caching already wired — D1), **no `PromptCacheManager.apply_breakpoints` wiring** (dead in prod — D1). Confirm Day-0 Prong-2/3.

---

## 5. Acceptance Criteria

- The chat path's PromptBuilder is fed the real `MemoryRetrieval`; a chat run renders a non-empty, scope-grouped memory block into the system prompt, capped ≤2000 tokens, with `verify_before_use` rules present when a flagged hint exists; `PromptBuilt.memory_layers_used` is non-empty.
- The loop accumulates `cached_input_tokens` and emits a Cat 12 cache-hit-rate metric on `LoopCompleted` (rate = cached/prompt, div-0 guarded).
- Integration tests prove: memory render + ≤2000 cap + verify rules + non-empty `memory_layers_used` (US-1); cache-hit metric emitted with mock `cached_input_tokens>0`, and =0 / no-crash when absent (US-2); cross-tenant isolation (tenant-B prompt shows none of tenant-A's hints); negative guards (empty retrieval → no block, no crash).
- `real_llm` e2e: a 2-turn Azure run shows `cached_input_tokens>0` on turn 2 + a non-empty memory block when memory exists (gated on C-11; assert via loop event stream / metric per A-5 OOS).
- All existing tests green; `mypy --strict` clean; 9/9 V2 lints (**LLM SDK leak 0**); frontend untouched; HANDOFF stub tests unchanged; no Azure-adapter / `apply_breakpoints` changes.

---

## 6. Deliverables

- [ ] `make_chat_prompt_builder` accepts + uses the real `MemoryRetrieval`; `handler.py` threads it + `user_id`
- [ ] `builder.py` net-new: memory-hint render into system prompt (US-1)
- [ ] `builder.py` net-new: `max_memory_tokens≤2000` cap (US-1)
- [ ] `builder.py` net-new: `verify_before_use` lead-then-verify injection (US-1)
- [ ] `loop.py`: accumulate `cached_input_tokens` + emit Cat 12 cache-hit-rate on `LoopCompleted` (US-2)
- [ ] 17.md updated for any new metric / event field
- [ ] integration test (render + cap + verify + cache metric + multi-tenant + negative) + real_llm e2e
- [ ] CHANGE record + progress.md + retrospective.md

---

## 7. Workload Calibration

Scope class: `medium-backend` (0.80). **Agent-delegated: TBD-Day-1-decision** (resolve at Day 1 start; likely `yes` → `mechanical-greenfield-design-decisions` 0.65, given net-new builder render/cap/verify design + the cache-metric design). The builder render + verify-rule injection is genuine design work (not mechanical port); the loop metrics accumulation is mechanical.

> Bottom-up est ~12 hr → class-calibrated commit ~9.5 hr (mult 0.80) → agent-adjusted commit TBD (apply `agent_factor` sub-class per `.claude/rules/sprint-workflow.md §Active Agent Delegation Factor Modifier` if Day-1 = `yes`).

---

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| **D1 drift**: analyses say "動 loop.py at LLM-call site for caching" — STALE (already forwarded; Azure `prompt_cache_key` already applied) | This sprint does NOT touch the call-site; A-2 = observability only (metrics accumulation). Do NOT wire `PromptCacheManager.apply_breakpoints` (dead in prod) |
| **D3 hidden Potemkin**: memory hints are fetched but `_build_system_section` ignores them | US-1 is net-new render code, not a one-liner; integration test asserts the block is actually IN the assembled prompt text (AP-4: prove it renders, not just fetches) |
| **`max_memory_tokens` cap nonexistent** | build the cap with the neutral `token_counter`; test asserts ≤2000; truncation order = lowest-confidence/oldest first |
| **`verify_before_use` injection nonexistent** | build static rule block + per-hint list; test asserts presence when a flagged hint exists, absence otherwise |
| **user_id scoping**: `build()` called with `user_id=None` (`loop.py:904`) | read `user_id` from `trace_context` in the builder OR thread real user_id; confirm user-layer scoping in a test |
| **Multi-tenant leakage via memory render** | cross-tenant test: tenant-B prompt shows none of tenant-A's hints (composite tenant scoping in `MemoryRetrieval.search`) — multi-tenant 鐵律 |
| **`InMemoryCacheManager` may emit no breakpoints** (chat path) → unstable `prompt_cache_key` | Day-0 Prong-2: confirm it produces non-empty `cache_breakpoints` with stable `section_id`; if no-op, that's the only caching-side fix |
| **`LoopCompleted` may need a new field** for cache-hit | Day-0 confirm; prefer reusing the existing Cat 12 metrics/Tracer path over a contract change; if changed, register in 17.md |
| **real_llm cache warm-up**: turn-1 has no cache; need ≥2 turns to see `cached_input_tokens>0` | e2e uses a 2-turn run; gated on C-11 secrets; assert via loop event/metric (A-5 OOS for HTTP-level) |
| **Module-level singleton test isolation** (Risk Class C) | autouse reset fixtures per `.claude/rules/testing.md` (the 57.64 keystone tests already use `_reset_settings_cache`) |
| **LLM-neutrality** (SDK into agent_harness) | memory render + metric are provider-free; cache signal via neutral `TokenUsage`; `check_llm_sdk_leak` gates |

---

## 9. Out of Scope

- **Anthropic `cache_control` breakpoints** — only the mock adapter has it; no production Anthropic adapter. Azure `prompt_cache_key` automatic caching is the prod path.
- **`PromptCacheManager.apply_breakpoints` activation** — dead in prod (D1); not needed for the Azure path.
- **A-5 events→SSE** (PromptBuilt / MemoryAccessed / cache-hit metric → frontend) — HTTP-level visibility is a separate sprint; this sprint asserts via the loop event stream / metric.
- **Extraction worker auto-trigger** (session-end L5→L4) — Celery deferred; independent.
- **semantic / Qdrant timescale** — Sprint 51.2 stub; Tier2 renders `short_term` + `long_term` layers first.
- **A-3b Cat 11 HANDOFF** — separate spike.
- **FIX-024 billing** (cost_ledger / pricing drift / max_tokens gpt-5.x) — billing bundle B-7/B-8/C-15.
