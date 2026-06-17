# CHANGE-100: chat-v2 Inspector Turn tab token-sweep (cached + cache-hit rows)

**Date**: 2026-06-17
**Sprint**: 57.133
**Scope**: Frontend (chat_v2) — closes the token-sweep leg of `AD-ChatV2-Inspector-Turn-Metadata-Wire`

## Problem

The chat-v2 Inspector Turn tab showed `tokens.in` / `tokens.out` / `tokens.thinking` per turn, but not the per-turn prompt-cache economics: `cached_input_tokens` (how many prompt tokens were a cache hit) and the `cache_hit` rate. Prompt-cache hits are the biggest per-turn cost/latency lever, and the operator-facing Inspector is where a turn's economics are read — yet the data was invisible.

## Root Cause

The data was already on the SSE wire — Azure adapter extracts `prompt_tokens_details.cached_tokens` (Sprint 57.65 A-2), `LLMResponded` carries `cached_input_tokens` (Sprint 57.108), and `event_wire_schema.py` serializes it on `llm_response` (already in `generated/loopEvents.generated.ts:43`). But the chat-v2 store's `llm_response` reducer captured only `input_tokens`/`output_tokens`, the `AgentTurn` type had no `cachedInputTokens` field, and `InspectorTurn` had no row. A pure missing-FE-read, not a missing capability.

## Solution

FE-only (3 src + 4 test files; NO backend / wire / codegen / migration):
- `types.ts` — `AgentTurn += cachedInputTokens: number | null` (token cluster, sibling of `tokensIn`).
- `store/chatStore.ts` — `turn_start` inits `cachedInputTokens: null`; `llm_response` captures `cachedInputTokens: ev.data.cached_input_tokens > 0 ? … : t.cachedInputTokens` (same 0-guard as the 57.108 `tokensIn`/`tokensOut` — an old-frame / unmeasured 0 must not clobber a real prior value).
- `components/inspector/InspectorTurn.tsx` — derived `cacheHitLabel` (`Math.round(cachedInputTokens / tokensIn × 100)%`, "—" until both known — derived, no new store state; the wire's `loop_end.cache_hit_rate` is cumulative, we want per-turn) + 2 KV rows (`tokens.cached`, `cache_hit`) after `tokens.thinking`; reuses the `KV` helper + `.mono` → 0 new mockup CSS / HEX / oklch (mockup 51 byte-identical). Docstring KV count corrected (stale 8 → 12; the 57.120/57.131 rows had drifted it).
- Tests — ChatInspector `makeAgentTurn += cachedInputTokens: 7410` + 2 render tests (set → "7,410"/"50%"; null → "—"); chatStore.mergeEvent `llmResponse` helper += `cachedInputTokens?` + 2 capture tests (set lands / absent keeps prior) + turn_start-init null assertion; activeSkill + TurnList factories += `cachedInputTokens: null` (the 57.131 required-field tsc-ripple lesson, all 3 factories enumerated Day-0).

Carve-out (§9): "actual `input_tokens` vs the `tokens_in` estimate" dual-display — the actual already overwrites the estimate at `llm_response` and IS the surfaced truth.

## Verification

- **Gates**: Vitest 146 files / **915 passed** (baseline 911 +4) · `npm run lint && npm run build` clean (no `--silent`) · `check:mockup-fidelity` PASS (styles-mockup.css byte-identical; 51 hex/oklch baseline, 0 new oklch) · `tsc --noEmit` 0 (no required-field ripple). Backend UNTOUCHED (FE-only, zero backend diff).
- **Drive-through PASS** (real chat-v2 UI via Playwright + real Azure gpt-5.2, jamie@acme.com/acme-prod, fresh session): Turn 1 "capital of France?" → "Paris", Inspector Turn tab `tokens.in 2,435` / `tokens.cached —` / `cache_hit —` (first request, no prior prefix cached → 0-guard keeps null → honest "—"). Turn 2 "its population?" → "…2.1 million…", Inspector Turn tab `tokens.in 2,458` / **`tokens.cached 2,048`** / **`cache_hit 83%`** (re-sent ~2,435-token prefix → Azure prompt-cache hit; derived 2048/2458 = 83% self-consistent). Values change turn-to-turn (not fixture/hardcoded). Screenshot: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-133/artifacts/drivethrough-57133-inspector-token-sweep-PASS.jpeg`.

## Impact

Frontend-only. `AD-ChatV2-Inspector-Turn-Metadata-Wire` fully CLOSED (all 3 legs: active_skill 57.120 + model 57.131 + token-sweep 57.133). No design note (continuation of the existing wire AD; no new contract). Bucket-C remaining: transcript retention (57.125).
