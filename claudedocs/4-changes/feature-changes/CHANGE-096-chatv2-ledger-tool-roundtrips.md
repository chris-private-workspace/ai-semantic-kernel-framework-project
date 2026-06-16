# CHANGE-096: chat-v2 ledger intra-turn tool round-trips

**Date**: 2026-06-16
**Sprint**: 57.129
**Scope**: 範疇 1 (Orchestrator Loop) — persist site addition; 範疇 7 (State Mgmt) ledger consumer
**AD**: closes `AD-ChatV2-Ledger-Tool-RoundTrips` (57.127 carryover)

## Problem

Sprint 57.127 built the `messages` Cat-3 ledger (`MessageStore` ABC + `DBMessageStore` + loop self-load on `run()`), but to de-risk dangling-tool_call rows it persisted ONLY two points per run: the **user prompt** at send start (`loop.py:1941`, turn 0) and the **final answer** at end_turn (`loop.py:2689/2721`). The **intra-turn tool round-trips** — the `assistant` message carrying `tool_calls` (`loop.py:2777`) + the `tool` result messages (`:2826`/`:3051`) — were appended to the in-memory buffer DURING a turn but NEVER written to the ledger. So a follow-up send rehydrated `[user, final-answer]` with the tool interactions stripped: a user could not reference a prior tool result (e.g. "add 7 to that number", "re-run that search").

## Root Cause

`_persist_to_ledger` was called only at the user-prompt and final-answer sites; the `TOOL_USE` branch of `_run_turns` had no persist call. The final answer is the only cross-send unit 57.127 persisted (and it is NOT in the buffer when the loop ends, hence its explicit persist).

## Solution

**Option A — incremental per-turn-batch persist** (user-picked over Option B end-of-run full-slice; AskUserQuestion 2026-06-16). In `_run_turns`'s `TOOL_USE` branch (`backend/src/agent_harness/orchestrator_loop/loop.py`):

1. `_tool_batch_start = len(messages)` immediately before the `assistant tool_use` append (`:2777`).
2. After the post-tool checkpoint `yield post_tool_event` (`:3072`), before the TURN-span `finally`: `await self._persist_to_ledger(messages[_tool_batch_start:], turn_num=turn_count)`.

The slice is exactly `[assistant tool_use, *tool results]` (the only `messages.append` sites in that window are the assistant tool_use + the cat9-blocked result + the normal result — verified Day-0). It is persisted as ONE atomic `DBMessageStore.append` (a `begin_nested()` SAVEPOINT) and is REACHED ONLY when the round-trip is complete and well-formed — every early-return path (cat9/cat8 terminate `:2819`/`:2926`/`:2995`, cancellation `:2900`) returns BEFORE the persist, so a partial/failed turn never leaves a dangling `assistant tool_use` (a `tool_use` without its `tool_result`) in the ledger. The final answer is still persisted separately at end_turn (57.127, untouched); the verification in-loop self-correction messages (a different branch that `continue`s earlier) are intentionally excluded. `_persist_to_ledger`'s docstring was updated to reflect the new pass-site (Karpathy §3 stale-docstring). Reuses `_persist_to_ledger` + `DBMessageStore.append` + `message_serde` (which already round-trips `tool_calls` / `tool_call_id` / `name`) — NO new helper / ABC / table / event type / wire / codegen / frontend / migration.

## Verification

- **Unit** (`tests/unit/agent_harness/orchestrator_loop/test_loop_multiturn_rehydration.py`, +3 tests, 6/6 pass): `test_run_persists_tool_round_trip` (roles `[user, assistant, tool, assistant]`; assistant carries `tool_calls`; tool result has `tool_call_id` + the result text not in the final answer); `test_tool_round_trip_persisted_atomically` (exactly one `append_calls` entry = `[assistant, tool]` → dangling-free); `test_prior_tool_round_trip_rehydrated` (a seeded prior round-trip rehydrates into LLM `request[0]`).
- **Gates**: mypy `src` 0/372 · run_all 10/10 (wire 24, no codegen) · full pytest 2727 passed / 5 skipped (2724 baseline + 3) · black/isort/flake8 clean · LLM-SDK-leak clean · frontend untouched (Vitest 904 / mockup 51 UNCHANGED).
- **Drive-through PASS** (real chat-v2 UI + real Azure gpt-5.2, dan@acme.com/acme-prod, session `9150a32f`; clean-restart backend PID 40596; acme-prod HITL set `auto=MEDIUM/require=HIGH` so python_sandbox auto-runs in-loop): turn 1 "run `random.randint(100000,999999)`, reply EVEN/ODD" → `stdout=333221`, answer "ODD" (number not in the answer); turn 2 (innocent) "add 7 to that number" → **"333228"** (= 333221+7, where 333221 is ONLY in the rehydrated tool result; turn-2 POST = {message,session_id} only). DB `messages` ledger = 6 rows incl. seq=2 assistant tool_calls=python_sandbox + seq=3 tool `{"stdout":"333221..."}`. (A first-session false-alarm — empty follow-up answers — was root-caused to Azure content-filter `jailbreak` 400 on adversarial recall prompts, NOT this change; a no-tool follow-up worked + innocent prompts work.)

## Impact

Backend-only: 1 src EDIT (`loop.py` +marker +persist +docstring), 1 test EDIT. No frontend / wire / codegen / migration. `message_store.py` / `message_serde.py` / the end_turn final-answer persist untouched. A user-facing capability (follow-ups now carry the prior turn's full tool interaction) on the chat-v2 main flow.

## Carryover

- `AD-ChatV2-Resume-Tool-RoundTrips` (NEW, sub-carryover) — resume()'s pending-tool observation is appended BEFORE driving `_run_turns`, so it is NOT captured by the `TOOL_USE`-branch marker; a HITL-paused-then-approved tool's round-trip is not persisted. Niche HITL path; deferred (distinct from the SHIPPED `AD-ChatV2-Resume-Transcript-Persistence` `message_events` work).
