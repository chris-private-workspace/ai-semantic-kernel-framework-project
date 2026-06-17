# Sprint 57.133 Retrospective — chat-v2 Inspector Turn tab token-sweep

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-133-plan.md) · [Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-133-checklist.md) · [Progress](./progress.md) · CHANGE-100

## Q1 — What shipped?
Closed the token-sweep leg (the last leg) of `AD-ChatV2-Inspector-Turn-Metadata-Wire`: the chat-v2 Inspector Turn tab now shows per-turn `tokens.cached` (actual prompt-cache-hit tokens) + a derived `cache_hit` rate. FE-only (3 src + 4 test edits): an `AgentTurn.cachedInputTokens` field + an `llm_response` 0-guard capture (the data was already on the wire since 57.65/57.108) + 2 KV rows reusing the `KV` helper. +4 Vitest tests. Drive-through PASS with a real non-zero Azure cache hit (turn 2: cached 2,048 / cache_hit 83%).

## Q2 — Estimate accuracy / calibration
- Scope class **`chatv2-inspector-existing-field-surface` 0.85** — **3rd data point** (57.120 0.85 re-point + 57.131 ~0.88 IN band).
- Bottom-up ~4.0 hr → committed ~3.4 hr (mult 0.85), parent-direct (agent_factor 1.0).
- Actual ~3.2-3.5 hr → ratio **~0.94-1.03 IN band**. KEEP 0.85. The 3-point trend (0.85 / ~0.88 / ~0.98) confirms the class: a tiny-code (~10-line) + full-ceremony parent-direct sprint that surfaces an already-on-wire/store-reachable field lands ~0.85-1.0 (ceremony-not-code-accelerated), NOT the 0.45-0.55 pure-repoint band.
- This sprint was the smoothest of the 3 (clean Day-0 三-prong, no mid-sprint surprise, a non-zero cache hit on the first drive-through attempt).

## Q3 — What went well?
- Day-0 three-prong fully de-risked: D-generated-cached proved the data was already on the wire (→ FE-only, no codegen) BEFORE any code; D-agentturn-literals enumerated all 3 factory ripples + the store helper upfront → `tsc --noEmit` clean first try.
- The 0-guard mirror (from 57.108) gave a correct turn-1 behavior for free: turn 1 = "—" (no cache hit; an unmeasured 0 doesn't masquerade), which is MORE honest than "0".
- The drive-through produced a strong, real proof: a genuine Azure prompt-cache hit (2,048 cached on the re-sent 2,435-token prefix) with the derived 83% self-consistent — values that change turn-to-turn, not fixture/hardcoded.
- Fixed a stale docstring while editing (KV count 8 → 12; 57.120/57.131 had drifted it) — Karpathy §3 keep-true.

## Q4 — What was hard / what to improve?
- Nothing hard. The only judgment call was the dash-count stability in `ChatInspector.test.tsx`: setting `cachedInputTokens: 7410` (non-null) in the default `makeAgentTurn` keeps the existing `toHaveLength(1)`/`(2)` dash tests valid (cached renders a value, not a dash) — chosen deliberately over null-by-default (which would have shifted every dash count).
- `curl` is blocked by the context-mode hook for the port health-check; used PowerShell `Get-NetTCPConnection` instead (noted for future drive-throughs).

## Q5 — Anti-pattern self-check
- AP-2 (no orphan): both KV rows reachable from the live Inspector; drive-through proves they render real wire values. ✅
- AP-3 (no scatter): all edits in chat_v2 (types + store + 1 component) + the 4 existing chat_v2 test files. ✅
- AP-4 (no Potemkin): drive-through proved real, turn-varying values (turn 1 "—" → turn 2 "2,048"/"83%") from the wire, not fixture/hardcoded. ✅
- AP-6 (no premature abstraction): reused `KV` + the 57.108 0-guard pattern; cache_hit derived, no new store state. ✅
- AP-8 (PromptBuilder): N/A. AP-11 (no version suffix): none. ✅
- v2 lints: N/A backend (FE-only); frontend lint + mockup-fidelity clean.

## Q6 — Drive-through honesty (約束)
Full drive-through PASS — real chat-v2 UI (Playwright) + real backend + real Azure gpt-5.2, a genuine non-zero cache hit. NOT gate-only. Evidence: screenshot + observed-vs-intended in progress.md Day 3.

## Q7 — Carryover
- `AD-ChatV2-Inspector-Turn-Metadata-Wire` fully CLOSED (3/3 legs). No new carryover from the feature.
- Bucket-C remaining (the OTHER user-named item): **transcript retention (57.125)** — runs as its own sprint next (rolling discipline).
- Open (unchanged): `AD-ChatV2-Resume-Replay-Drive-Through` (57.132 Leg-2 fixture); `AD-Billing-Outbox-Drain-Test-Flake` (Risk Class C, did NOT surface — FE-only).

## Design Note Extract
N/A — not a spike sprint (continuation of the existing wire AD; no new contract). NO design note.
