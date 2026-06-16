# CHANGE-094: chat-v2 live multi-turn context (rehydrate prior conversation into the live loop)

**Date**: 2026-06-16
**Sprint**: 57.127
**Scope**: 範疇 7 (State Mgmt) + 範疇 1 (Orchestrator Loop) — cross-category (new persistence seam + loop lifecycle)
**AD closed**: `AD-ChatV2-Live-MultiTurn-Context` (the real product bug the 57.126 drive-through surfaced)

## Problem

In chat-v2, a follow-up message in an EXISTING session started the agent loop WITHOUT the prior conversation. The 57.126 drive-through (real Azure gpt-5.2) logged: turn 1 "capital of France?" → "Paris" ✅; turn 2 "its population?" → the agent answered *"missing what 'it' refers to"* ❌. The same `session_id` was reused (57.126 continuation works), but the agent had **no memory of turn 1** — multi-turn chat was effectively single-turn for context.

## Root Cause (grep-confirmed on `main` `c1d3d1be`)

| Layer | Reality | Anchor |
|-------|---------|--------|
| Loop builds messages from scratch | `messages = []` → append system (if any) → append the new `user_input`. No prior load. | `loop.py` `run()` |
| Router never loads prior | `_stream_loop_events` calls `loop.run(session_id, user_input, trace_context)`; no prior-message query | `router.py` |
| `state_data` excludes messages | `_serialize_state_for_db` "Excludes messages"; `_deserialize` `messages=[]  # caller rehydrates` | `checkpointer.py:217/258` |
| `messages` table had no writer | the table existed (Cat-3 ORM) but nothing wrote to it | `models/sessions.py:163-217` |
| HITL-only rehydration | only the deferred-pause branch stashed `metadata["resume_messages"]`; normal completed sessions never persisted messages | `loop.py` `messages_from_metadata` |

The 57.125/126 `message_events` table persists serialized SSE frames for the **frontend replay UI** — it is NOT fed to the live loop. So there was no path to carry a completed turn's conversation into the next send.

## Solution (Approach A — user-picked via AskUserQuestion 2026-06-16)

Give the existing `messages` table a real writer + rehydrate on follow-up, via a NEW provider-neutral `MessageStore` ABC injected into the main-chat loop (the loop self-loads + persists; `loop.run()`'s ABC signature is UNCHANGED → no caller ripple).

- **`agent_harness/_contracts/message_serde.py`** (NEW): relocated `_message_to_dict` / `_message_from_dict` / `_content_block_to_dict` from `loop.py` to a `_contracts` leaf so `state_mgmt` imports them without importing the heavy `loop.py` (circular-import safety). `loop.py` imports them; `messages_from_metadata` stays in `loop.py`.
- **`agent_harness/state_mgmt/_abc.py`** (EDIT): `MessageStore` ABC — `load()` + `append(messages, *, turn_num)`, bound to `(session_id, tenant_id)` at construction (sibling to `Checkpointer`). Provider-neutral.
- **`agent_harness/state_mgmt/message_store.py`** (NEW): `DBMessageStore(db, session_id, tenant_id)` — `load()` = `SELECT ... WHERE session & tenant ORDER BY sequence_num → _message_from_dict`; `append()` = `sequence_num` from `MAX(...)+1`, best-effort `begin_nested()` SAVEPOINT, `db is None`-safe. Tenant-scoped (鐵律). ORM `Message` aliased `MessageRow`.
- **`agent_harness/state_mgmt/__init__.py`** (EDIT): export `MessageStore` + `DBMessageStore`.
- **`agent_harness/orchestrator_loop/loop.py`** (EDIT): ctor `+message_store`; `run()` self-loads prior + seeds (system reconstructed fresh, NEVER persisted; prior NOT re-persisted) + persists the user prompt at send start; the 2 end_turn sites (stop_reason terminator + `output_type==FINAL`) persist the final answer. Covers `run()` + `resume()`.
- **`api/v1/chat/_category_factories.py`** (EDIT): `make_chat_message_store(db, session_id, tenant_id) -> MessageStore | None` (None-guard, mirrors `make_chat_state_deps`).
- **`api/v1/chat/handler.py`** (EDIT): `build_handler` injects `DBMessageStore` onto the MAIN chat loop only; subagent child loops get none → `prior=[]`, unaffected.

### Dual-ledger note (not accidental duplication)

Two tables now persist overlapping-but-distinct data: `message_events` (57.125/126 — serialized SSE frames, for the frontend replay UI) and `messages` (this change — Cat-3 `Message` objects, for live-loop rehydration). Different shapes, different consumers; both endorsed by the `loop.py` SPIKE NOTE. A future canonical-ledger consolidation is a deferred AD.

### Deviations from the plan (documented)

1. **Persistence simplified** — the plan envisioned a compaction-immune `new_this_run` side-list recording every message-append site (incl. tool results). The FINAL branch yields end_turn WITHOUT appending the answer to `messages`, so instrumenting `messages.append` would miss the answer. De-risked to: persist **user prompt (send start) + final answer (2 end_turn sites)** directly — no side-list, no tool-site instrumentation, no dangling-tool_call risk. **Intra-turn tool round-trips deferred → `AD-ChatV2-Ledger-Tool-RoundTrips`.** Fully covers the reported text-multi-turn bug. NOT lossy reconstruction (verbatim Cat-3 Messages).
2. **No migration** — Day-0 confirmed `messages_default` + `message_events_default` partitions exist (`0028`) → no 2026-07 cliff → the conditional forward-partition migration was DROPPED.
3. **Test substitution** — the plan's `test_chat_multiturn_context.py` (chat-POST harness) → realized as `test_message_store.py` (real-PG integration, 5 cases) + `test_loop_multiturn_rehydration.py` (loop unit, 3 cases incl. prior-reaches-LLM-request). The 2-send rehydration is proven by the loop unit (same `run()` self-load) + the drive-through.

## Verification

- **Gates**: mypy `src` **0/372** · run_all **10/10** (wire **24**, LLM-SDK-leak clean) · full pytest **2720 passed / 5 skipped** (+8) · Vitest **904** / mockup **51** UNCHANGED (pure backend). `black`/`isort`/`flake8` clean.
- **Tests**: `tests/integration/agent_harness/state_mgmt/test_message_store.py` (5) + `tests/unit/agent_harness/orchestrator_loop/test_loop_multiturn_rehydration.py` (3).
- **Drive-through PASS** (MANDATORY — real chat-v2 UI + clean-restart backend + real Azure gpt-5.2, session `9e89775d`):
  - turn 1 "What is the capital of France?" → "Paris." (`prompt_built messages_count=4`)
  - turn 2 (same session) "What is its population?" → **"Paris has about 2.1 million residents in the city proper…"** (`prompt_built messages_count=6` = 4 base **+2** rehydrated prior) — resolved "its"→Paris, the exact 57.126 failure now fixed.
  - DB ledger (`artifacts/verify_ledger.py`): 4 rows, `sequence_num` 1→4 monotonic (user/assistant × 2 sends), verbatim content.
  - Evidence: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-127/artifacts/sprint-57-127-drivethrough-turn{1,2}.png` + `backend-drivethrough.log`.

## Impact

Backend-only. The main chat-v2 loop now carries prior conversation into each follow-up send (text multi-turn context works). Subagent child loops, the resume path, and pre-57.127 sessions are unaffected (graceful degrade to `prior=[]`). Intra-turn tool round-trips within a single turn are not yet persisted (`AD-ChatV2-Ledger-Tool-RoundTrips`).
