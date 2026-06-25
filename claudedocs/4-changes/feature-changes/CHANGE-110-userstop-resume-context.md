# CHANGE-110: user Stop→continue durable interrupt-resume

**Date**: 2026-06-25
**Sprint**: 57.143
**Scope**: Cat 7 (State Mgmt) + Cat 1 / api (chat) + chat-v2 frontend — cross-cutting durability
**AD**: closes `AD-UserStop-Resume-Context`

## Problem

In chat-v2, a user who sent a message, let the agent run, **hit Stop mid-run**, then typed "continue" got amnesia — the agent replied "Continue from what, exactly?". It remembered earlier *completed* turns but had ZERO record of the interrupted run (not its answer, not even the user's prompt for that run). One of the most visible "feels broken vs Claude Code" behaviors.

## Root Cause

The interrupted run persisted **nothing** to the `messages` Cat-3 ledger:
- `DBMessageStore.append` wrote via `self._db.begin_nested()` (SAVEPOINT) on the **request** `AsyncSession`, whose outer commit is deferred to stream-end (`message_store.py:122`).
- The frontend Stop is a client-side abort only (`useLoopEventStream.ts:149-152`) — it closes the SSE; the server sees `asyncio.CancelledError` (`router.py:1127`).
- `get_db_session` `rollback()`s on ANY exception incl. that `CancelledError` (`session.py:54-56`), and the stream `finally` does NOT commit → the turn-0 user-prompt SAVEPOINT (and any completed tool batches since the early `db.commit()` at `router.py:384`) are rolled back. The loop is ALSO torn down by the cancel — so both "loop cancelled" and "commit never happened" are true.
- `registry.cancel()` sets a `cancel_event` that **no code polls** (`session_registry.py:127`), so `/cancel` was status-flip-only for actual termination.

## Solution

Scope **B (full CC parity)** — add CC's "persist immediately + record the interrupt" discipline onto the ledger-replay V2 already has (`DBMessageStore.load()` at run start = CC's `buildConversationChain`).

**US-1 — durable own-session ledger** (`message_store.py` + `_category_factories.py`): `DBMessageStore` holds a session FACTORY (not a request session); `load()`/`append()` each open their OWN short-lived tenant-scoped session + `set_config('app.tenant_id', …, true)` (FORCE-RLS `messages`; mirrors `transcripts/retention.py`), and `append()` COMMITS immediately. The loop's turn-0 prompt + tool batches + final answer become durable for free — `loop.py` UNTOUCHED. `make_chat_message_store` passes `get_session_factory()` (`del db`, memory-layer precedent).

**US-2 — interrupt marker** (`router.py` + `chatService.ts` + `useLoopEventStream.ts`): `cancel_session` persists `Message(role="assistant", content="[Request interrupted by user]")` via a self-contained `DBMessageStore` (best-effort — never fails the 204). Frontend `cancel()` now does `abort()` + `setStatus("cancelled")` + `void cancelSession(sid).catch(()=>{})` (`POST /sessions/{id}/cancel`; fire-and-forget — a cancel-API failure must not change the UI cancelled state). Synthetic tool_results DROPPED (57.129 atomic-batch ⇒ no dangling tool_use; YAGNI).

## Verification

- Backend: `tests/integration/agent_harness/state_mgmt/test_message_store.py` (6 — incl. `test_append_survives_request_session_rollback`, the durability proof) + `tests/integration/api/v1/chat/test_cancel_marker.py` (2 — marker persisted + cross-tenant 404 no marker). Frontend: `tests/unit/chat_v2/chatService.cancelSession.test.ts` (2).
- Gates: mypy `src` 0/381 · v2 lint tests 15 (llm_sdk_leak 3/3) · flake8/black/isort clean · chat unit + state_mgmt + chat integration 177 pass · frontend lint + build clean.
- **Drive-through PASS (real UI + backend + real Azure gpt-5.2, session `35789e63-…`)**: send → Stop mid-run → continue. DB `messages` ledger showed seq 5 = the interrupted essay prompt (DURABLE — survived the Stop), seq 6 = `[Request interrupted by user]` marker; on "continue" (seq 7) the agent rehydrated 19 messages and continued the ORIGINAL task (`write_todos` naming "computing history (abacus to AI)" + "1500-word essay") — NOT "continue from what?". Evidence: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-143/artifacts/`.

## Impact

Backend (Cat 7 own-session refactor + Cat 1/api cancel handler) + 1 FE wire (chat-v2 Stop). NO migration / new table / new wire event / codegen / mockup change. `loop.py` + `session_registry.py` UNTOUCHED.

## Out of Scope (→ Phase 58)

- `AD-Loop-CancelEvent-Poll-Phase58` — make the loop poll `cancel_event` for a graceful in-process stop + in-flight LLM cancel (today the abort tears it down; the marker covers coherence).
- partial assistant-answer streaming capture; `message_events` (replay ledger) disconnect durability.
