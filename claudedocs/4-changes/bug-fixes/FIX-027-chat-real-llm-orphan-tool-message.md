# FIX-027: chat real_llm orphan-tool-message 400 + tool-turn non-convergence

**Date**: 2026-06-04
**Sprint**: 57.80
**Scope**: 範疇 5 (Prompt Construction) — `DefaultPromptBuilder` (backend-only)
**Closes**: `AD-Chat-RealLLM-Orphan-Tool-Message`

## Problem
`POST /api/v1/chat/` in `mode=real_llm` returned a 400 from Azure on any tool-calling turn: **`messages[3] role 'tool' must follow tool_calls`** (orphan tool message). A fresh tenant + clean session reproduced it (`messages_count:4`), so it was a per-turn prompt-assembly defect, not session-history pollution. Surfaced by the Sprint 57.79 Day-3 real-LLM run (which bypassed it via the direct cost_ledger record path). echo_demo mode was unaffected.

## Root Cause
The real_llm path injects `DefaultPromptBuilder` (keystone Sprint 57.64), so the loop sends `artifact.messages` (`loop.py:1052`) rather than its own correctly-ordered `messages`. The builder's default `LostInMiddleStrategy.arrange()` (`lost_in_middle.py:64-76`) splits the conversation into `recent_assistants` (appended at the tail) vs `mid_history` (everything else, incl. `role='tool'` results, appended before). For a tool turn `[system, user, assistant(tool_calls), tool]` it produced `[new_system, echo, old_system, tool, assistant(tool_calls), user]` — the `tool` (idx 3) precedes its `assistant` (idx 4), violating the provider hard-constraint that a `role='tool'` message must immediately follow the assistant bearing the matching `tool_calls`. `messages[3]=tool` exactly matched the 400.

Invisible until real Azure because the loop+builder integration tests only ran single-turn-no-tool scripts AND `MockChatClient` does not validate adjacency (AP-10 mock-vs-real divergence + AP-4 no negative coverage of the tool-turn assembly).

**Secondary (surfaced once the 400 no longer short-circuited the loop)**: every strategy re-anchors the current user message at the tail (`lost_in_middle.py:79-80`). On a tool turn the assembled prompt therefore ended with the user message (after the tool result) → the model treated the re-anchored request as fresh and re-called the tool every turn → the echo demo looped to `max_turns` (`stop_reason=max_turns total_turns=8`) instead of converging.

## Solution
Two builder-level changes in `backend/src/agent_harness/prompt_builder/builder.py` (single enforcement point — AP-8; LLM-neutral; no strategy / loop / adapter change):

1. **Tool-call adjacency invariant** — new `_enforce_tool_adjacency(messages)` static method, called in `build()` immediately after `strategy.arrange()`. Maps each `ToolCall.id` → emitting assistant, then rebuilds the list so every `role='tool'` message directly follows its owning assistant, preserving all other order. Orphan tools (no resolved owner — does not occur on the loop path) are left in place (no silent drop). No-op when no tool turn exists.

2. **Pending-tool-turn user re-anchor suppression** (targeted Approach C; in-sprint extension per the Day-3 finding + user decision) — `build()` detects a pending tool turn (`state.transient.messages[-1].role == "tool"`) and passes the full conversation in chronological order + `user_message=None` (no tail re-anchor, no top echo), so the prompt ends with the tool result and the model produces its final answer. Fresh / non-tool turns keep the lost-in-middle echo + tail re-anchor unchanged.

## Verification
- Unit: `tests/unit/agent_harness/prompt_builder/test_builder_tool_adjacency.py` — 5 `_enforce_tool_adjacency` cases + build()-through-LostInMiddle adjacency + 2 pending-vs-fresh re-anchor cases.
- Integration: `tests/integration/agent_harness/prompt_builder/test_loop_with_prompt_builder.py` — 2-turn tool script asserts `chat_client.last_request.messages` adjacency (AP-10 closure). Regression-guard verified: temporarily disabling the invariant → build() test FAILED `assistant@4, tool@3` (the real Azure `messages[3]` 400 shape) → restored → green.
- Real Azure (fresh tenant, gpt-5.2): `POST /chat real_llm` → HTTP 200, no `must follow tool_calls`, SSE `loop_end stop_reason=end_turn` (was `max_turns`), final `content="hello"`, last `prompt_built messages_count=5` ending with the tool result; cost_ledger rows written.
- Gates: `mypy src/` 0 (331) + `pytest` 2130 passed / 4 skipped (+9) + `python scripts/lint/run_all.py` 10/10.

## Impact
Backend-only (Cat 5). Fixes real_llm chat on all tool-calling turns (the core agent path); echo_demo + non-tool real_llm turns unchanged. No frontend / migration / schema / contract change.
