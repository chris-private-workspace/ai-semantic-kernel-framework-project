# CHANGE-115: memory-formation Slice 1 — user-identity write + always-on inject

**Date**: 2026-06-27
**Sprint**: 57.148
**Scope**: Cat 3 (Memory) + Cat 5 (Prompt Construction) + Cat 2 (system-prompt nudge); backend-only

## Problem

A live drive-through on the real chat page exposed the platform's headline memory promise as non-functional: a user asking "你知道我是誰嗎? 也記得之前我有問過什麼問題嗎?" got "我不知道你是誰 … 也沒有取到任何可用的記錄". The 5-layer memory machinery is wired (auto-inject + real `memory_search`/`memory_write` handlers) but the platform never actually remembered who the user is across sessions.

## Root Cause

Two coupled gaps (both confirmed by Day-0 recon):

1. **Formation never fires** — the chat system prompt had no instruction to persist user facts; `memory_write` was purely LLM-discretionary, so in normal chat nothing was ever written to `memory_user`.
2. **Surfacing is ILIKE query-gated** — `DefaultPromptBuilder._inject_memory_layers` (`builder.py:581`) passes the user's last message as the search query, and `UserLayer.read` (`user_layer.py:88-95`) matches `content ILIKE %query%`. An identity question ("你知道我是誰") shares no keyword with a stored "User name is Chris", so even a populated fact is never retrieved.

(This is exactly the "引擎接好 ≠ 行為落地" gap from the reality-audit: injection was built; formation + keyword-independent surfacing were not.)

## Solution

Backend-only, two coupled pieces (mirrors how Claude Code remembers you = formation + always-on injection):

- **Formation nudge** (`tools/memory_tools.py` `MEMORY_FORMATION_NUDGE` + `api/v1/chat/handler.py`): appended to the chat system prompt on the SAME proven seam as the skills catalog (the loop prepends `self._system_prompt` as the system message, `loop.py:1970`), gated on `memory_retrieval is not None`. Instructs the agent to `memory_write(scope='user', time_scale='long_term')` when the user states durable self-facts.
- **Always-on user-profile injection** (`memory/retrieval.py` new `profile()` + `prompt_builder/builder.py`): `MemoryRetrieval.profile(tenant_id, user_id, top_k)` pulls user-scope long_term facts with a wildcard query (NOT query-gated; bypasses the builder's empty-query guard). `build()` merges these into the `user` memory block UNCONDITIONALLY (deduped by `hint_id`, within the existing ≤2000-tok Tier2 cap, graceful-degrade on failure). New ctor param `profile_top_k=5`.

NO migration / wire event / frontend change (`memory_user` + `UserLayer` already existed; chat UI already renders the answer).

## Verification

- **Gate**: mypy `src` 0/392 · run_all 11/11 · +11 unit/integration tests (profile 4 / always-on inject 4 / per-tenant isolation 1 / handler nudge 2) · black/isort/flake8 clean · full pytest <see retrospective>.
- **Drive-through (real UI + real backend + real Azure gpt-5.2)** — jamie@acme.com (baseline 0 rows):
  - Leg 1: stated identity (no "remember me") → agent proactively `memory_write` ×2 → DB `'User name is Chris.'` + `'Chris is responsible for developing the Knowledge Connector feature…'`.
  - Leg 2: NEW session (same user_id), "你知道我是誰嗎?" (0 keyword overlap) → "你是 Chris。我也記得你目前負責…開發 Knowledge Connector" (Inspector showed 2 user-layer reads).
  - Leg 3: priya@acme.com (different user_id) → "我不知道你是誰…" — per-user isolation holds.

## Impact

Backend-only. The chat main flow now (a) proactively persists durable user identity/preference facts and (b) surfaces them every future turn regardless of the message keywords. Closes `AD-Memory-Formation-Identity` Slice 1. Deferred (separate slices): Option-B deterministic extraction (`MemoryExtractor` already exists, unwired), upsert-by-key in `UserLayer.write`, cross-session conversation recall, memory semantic/Qdrant axis (CARRY-026). Design note: `52-memory-formation-identity-design.md`.
