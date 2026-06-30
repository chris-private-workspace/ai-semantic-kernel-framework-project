# CHANGE-119: Combine post-send extract + summarize into one LLM call

**Date**: 2026-06-30
**Sprint**: 57.152
**Scope**: 範疇 3 (Memory) — post-send formation; backend-only

## Problem

The chat post-send memory formation (`_maybe_auto_extract`) loads the session ledger ONCE but makes **two independent** cheap-tier LLM calls over the SAME conversation: `MemoryExtractor.extract_session_to_user` (durable user facts → `UserLayer`, 57.149) + `SessionSummarizer.summarize_and_store` (rolling conversation summary → `memory_session_summary`, 57.151). Two calls over one input = ~2× background token + ~2× latency per send (both flags default ON, runs after every real_llm send).

## Root Cause

The two formation features were built incrementally (57.149 then 57.151) and wired as separate post-send calls. Each owns its own prompt + `chat()` + parse + dispatch. Nothing combined them, so the shared ledger was read by the LLM twice.

## Solution

A new `MemoryFormationWorker` (`agent_harness/memory/formation.py`) that **composes** the two existing workers and, by default, makes ONE combined cheap-tier call returning both the facts array AND the summary object, then dispatches each half to the SAME write code:

- Extracted behavior-preserving dispatch halves: `MemoryExtractor.write_facts(items, ...)` + `SessionSummarizer.store_summary(parsed, ...)` (the single-call methods now end with these).
- `MemoryFormationWorker._form_combined`: one prompt (facts/summary sections conditioned on which collaborators are wired + the known-facts dedup block) → one `chat()` → tolerant combined-JSON parse → `write_facts` + `store_summary`.
- `_form_separate`: delegates to the two full single-call methods — the env fallback path (keeps both methods live on the chat path → no AP-2/AP-4 orphaning).
- `chat_memory_combined_formation` flag (default ON; env `CHAT_MEMORY_COMBINED_FORMATION`) gates combined-vs-separate — a one-env-var revert to the proven two-call path if the combined prompt ever degrades quality. Independent of the two feature flags (which decide WHICH sections form).
- Wiring: `ChatMemoryExtractContext.{extractor, summarizer}` → `{former}`; `build_chat_memory_extractor` builds the worker; `_maybe_auto_extract` calls `former.form()` once (`profile()` known-facts read gated on `former.wants_user_facts`).
- AP-8 allowlist += `formation.py` (background utility-LLM caller, same category as `extraction.py` / `session_summarizer.py`).

Files: `formation.py` (NEW), `extraction.py` / `session_summarizer.py` (+ dispatch halves), `memory/__init__.py` (export), `handler.py` / `router.py` (rewiring), `core/config/__init__.py` (flag), `check_promptbuilder_usage.py` (allowlist), `test_formation.py` (NEW), `test_memory_auto_extract.py` / `test_handler.py` (updated). NO migration / wire / frontend / loop.py change.

## Verification

- **Unit**: `test_formation.py::test_combined_one_call_writes_both` — a spy ChatClient asserts `chat_call_count == 1` while BOTH `write_facts` + `store_summary` are invoked. `test_combined_false_uses_separate_two_calls` — fallback delegates to the 2 full methods. Section-conditioning + no-op + prompt/parse tests. (10 tests.)
- **Gates**: mypy `src` 0/397 · run_all 11/11 (incl. llm_sdk_leak + AP-8 with formation.py allowlisted) · backend pytest 3053 passed / 6 skip (+11) · black/isort/flake8 clean.
- **Drive-through STRONG PASS** (real chat-v2 + real Azure gpt-5.2, fresh 57.152 backend): one send ("I'm Marcus … Redis→DynamoDB session store … write-through cache … TTL vs explicit invalidation") → ONE combined background call wrote BOTH a `memory_session_summary` row (summary + 3 key_decisions + 3 unresolved_issues) AND `memory_user [auto_extract]` fact rows, **at the same `15:20:30` timestamp** = one call. 57.150 dedup coexists (the agent's in-loop `memory_write` of the same identity fact was upserted by the auto_extract). Leg 2 (recall, unchanged this sprint): the new session's PromptBuilder injected both halves (trace-confirmed); the final-answer synthesis hit two pre-existing carryovers (cross-sprint dan identity conflict + `AD-Verification-Judge-Memory-Inject-Blind`) — neither a 57.152 regression. Evidence: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-152/artifacts/`.

## Impact

Backend-only. Halves the post-send background formation LLM cost (token + latency) when both formation features are on (the default), with no user-visible behavior change when the combined prompt is well-formed. Flag-gated instant revert to the proven two-call path. Closes `AD-Memory-Formation-Combine-Extract-Summarize`. Design note: `54`→`55-memory-combined-formation-design.md`.
