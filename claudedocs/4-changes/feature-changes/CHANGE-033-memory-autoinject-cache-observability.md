# CHANGE-033: Memory auto-inject (A-1 Tier2) + prompt-cache hit-rate observability (A-2 Tier2)

**Date**: 2026-06-01
**Sprint**: 57.65
**Scope**: Cat 5 (Prompt Construction — memory render) + Cat 3 (Memory Tier2) + Cat 4/12 (prompt-cache observability); api/factory + prompt_builder + loop metrics
**Status**: ✅ Shipped (feature branch `feature/sprint-57-65-memory-autoinject-cache-observability`; PR pending)

---

## Problem

57.64 (Tier-1) wired on-demand memory tools + injected the PromptBuilder onto the chat path, but the two Tier-2 capabilities remained:

1. **A-1 Tier2 (memory auto-inject)** — the chat path's PromptBuilder was fed an **empty** `MemoryRetrieval(layers={})`, so no memory ever appeared in the prompt. Additionally, there was no `≤2000`-token cap on the memory block, no `verify_before_use` lead-then-verify rule injection, and `build()` was called with `user_id=None` (user-layer memory never scoped).
2. **A-2 Tier2 (prompt-cache observability)** — the Azure prompt-cache pipe was already complete (`prompt_cache_key` applied by the adapter; `TokenUsage.cached_input_tokens` populated from `prompt_tokens_details.cached_tokens`), but the loop's `LoopMetricsAccumulator` **dropped** the cached-token signal (it flowed only to billing), so there was no cache-hit metric.

## Root Cause / Day-0 drift corrections

The two source analyses (`cat3-...` / `cat5-...`) were baselined pre-57.64; a Day-0 reality audit corrected three premises:

- **D1 (A-2)**: the analyses' "caching needs a loop.py LLM-call-site rewrite" was **stale** — `loop.py` already forwards `artifact.cache_breakpoints` to `chat()`, and the Azure adapter already applies `prompt_cache_key`. A-2 was therefore **observability-only**; no call-site change, and `PromptCacheManager.apply_breakpoints` (dead in prod) must NOT be wired.
- **D2 (A-2)**: `cached_input_tokens` was already populated by the adapter but dropped at `loop.py:961-969`.
- **D3 (A-1) — corrected mid-sprint**: the audit claimed `_build_system_section` ignores memory → "never rendered". This was a **misdiagnosis**: the render machinery already existed via `templates._memory_as_messages` consumed by the default `LostInMiddleStrategy` (Sprint 52.2; 8 tests assert it). The real chat-path gap was the **empty retrieval input** + missing cap/verify/enrichment/user_id — not a missing render. (Audit trail preserved in `sprint-57-65/progress.md` Day 1.)

## Solution

**A-1 Tier2** (Cat 5 + Cat 3) — api/factory + `prompt_builder/builder.py`:
- `make_chat_prompt_builder(chat_client, memory_retrieval=None)` uses the real retrieval when given (empty default preserves 57.64 standalone); `build_real_llm_handler` threads the SAME `MemoryRetrieval` already built for the executor's memory tools (one shared retrieval) + `user_id`.
- `loop.py:904`: `user_id=None` → `user_id=ctx.user_id` (scopes the user-layer memory).
- `DefaultPromptBuilder`: `max_memory_tokens=2000` cap (`_apply_memory_budget` drops lowest-confidence then oldest hints via the neutral `token_counter`); `verify_before_use` lead-then-verify block appended to the system role when any hint is flagged; fixed `system→tenant→role→user→session` render order. Cap + verify live in `build()`/templates (NOT a `_build_system_section` rewrite) to avoid a duplicate memory block and keep the 8 strategy tests green.
- `templates.py`: enriched hint line (`summary` + `confidence` + `last_verified_at`); `full_content_pointer` deliberately NOT inlined (it's a DB/vector ref).

**A-2 Tier2** (Cat 4/12) — loop metrics + events, observability-only:
- `LoopMetricsAccumulator.cumulative_cached_input_tokens` + a DRY `cache_hit_rate` property (cached/input, div-0 guarded → 0.0).
- `loop.py`: accumulate `cached_input_tokens` both inline (`:964`) and via `on_event` (`LLMResponded` branch) to avoid mock/real divergence (AP-10); emit `cached_input_tokens` + `cache_hit_rate` on BOTH `LoopCompleted` sites; populate `LLMResponded.cached_input_tokens`.
- `_contracts/events.py`: new fields on `LLMResponded` + `LoopCompleted` (safe defaults). Registered in `17-cross-category-interfaces.md` §4.1.

## Verification

- New tests: `test_chat_tier2_wiring.py` (8 integration: memory render into assembled prompt / verify_before_use rule / cross-tenant no-leak / negative no-block / cache-hit `cache_hit_rate==approx(0.6)` / 2-turn accumulation / zero-div-0 guard / combined render+cache one-run); `test_builder_tier2.py` (11 unit: render + cap drop-order + verify); `test_metrics_accumulator.py` (+2 unit).
- Cross-tenant isolation is a true strong assertion: tenant-B's assembled prompt contains none of tenant-A's session memory (composite tenant scoping in `MemoryRetrieval.search`).
- Full sweep: **pytest 1955 passed / 4 skipped** (+21 vs 1934 baseline); `mypy src/` **0/319**; `python scripts/lint/run_all.py` **9/9 green** (incl. `check_llm_sdk_leak` 0); frontend untouched; 57.64 keystone (11) + strategy (8) tests unchanged-green.
- Staged code-implementer delegation (Stage 1 A-1 + Stage 2 A-2), each independently re-verified by the parent (re-ran tests + mypy + lints + read diffs — not trusting self-report).
- `real_llm` live e2e leg **deferred** (confirmatory) — HTTP-level assertion of the memory block / cache_hit_rate is blocked by A-5 (events→SSE) being out of scope (both are in-process loop signals); live path already exercised in C-11; Azure cost + `cost_ledger` FIX-024 known-red.

## Impact

- **Runtime**: the production `real_llm` chat path now (a) renders a per-turn, capped (≤2000-token) tenant/user/session memory summary into the system prompt with lead-then-verify rules for stale hints, and (b) reports a prompt-cache-hit-rate on `LoopCompleted` for Cat 12 consumption. This completes the Area-A "memory-aware + structured-prompt" capability begun in 57.64.
- **Scope**: backend only (api/factory + prompt_builder + loop metrics + events); no frontend, no DB migration, no Azure-adapter change, no `loop.py` LLM-call-site rewrite (only the 1-line user_id scoping + metrics accumulation).
- **Out of scope (unchanged)**: A-5 events→SSE (HTTP-level visibility of memory/cache); Anthropic `cache_control` (no prod Anthropic adapter); `PromptCacheManager.apply_breakpoints` (dead); extraction worker auto-trigger; semantic/Qdrant timescale.
- **Follow-ups noted in retrospective** (minor, non-blocking): `_measure_memory_tokens` forwards an unused `tools` param (docstring overstates a baseline subtraction); `LoopMetricsAccumulator.to_loop_completed_payload()` was not extended with the 2 new fields (latent inconsistency — the loop constructs `LoopCompleted` manually, so not a runtime bug).
