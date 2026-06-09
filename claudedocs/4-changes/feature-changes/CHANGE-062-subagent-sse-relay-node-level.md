# CHANGE-062: Cat 11 Subagent SSE Relay (node-level) — Inspector Tree no longer headless

**Change Date**: 2026-06-09
**Change Type**: Feature Improvement (wiring an existing-but-unwired Cat 11 → Cat 12 emitter)
**Status**: ✅ Completed (drive-through PASS; push + PR pending user authorization)
**Sprint**: 57.95
**Scope**: Cat 11 (Subagent Orchestration) × Cat 12 (Observability) — backend-only chat composition wiring

## Change Summary

Sprint 57.94 made FORK run a real child agent loop, but the child ran **headless**: the chat-v2 Inspector "Tree" tab showed "no subagents spawned this session" even when a subagent ran (the 2026-06-06 drive-through audit flagged this as `AD-Subagent-Child-Event-SSE-Relay`). This change closes that gap at the **node level** (Scope A): the chat subagent dispatcher now carries an `event_emitter`, so `SubagentSpawned` / `SubagentCompleted` reach the SSE stream and the Tree renders the subagent node (mode / summary / tokens, running→completed).

## Change Reason

Drive-Through Acceptance: 57.94's drive-through confirmed the child loops + uses a tool, but the user could not SEE the subagent in the UI. The headless subagent is an honest-but-incomplete experience.

## Root Cause (of the headless gap)

The SSE relay chain already existed end-to-end — `DefaultSubagentDispatcher` has had an `event_emitter` slot + `_emit_safely` emission since Sprint 57.12; `serialize_loop_event` maps both subagent events (`sse.py:306-326`); the frontend `chatStore` + `InspectorTree` already consume them. The ONLY unwired link: `make_chat_subagent_dispatcher` (`_category_factories.py:224`) returned the dispatcher WITHOUT an `event_emitter`, so `_emit_safely` no-op'd on the chat path. `SubagentSpawned` already carries `parent_session_id` → **no `LoopEvent` contract change, no new event type, no frontend change** for node-level relay.

## Detailed Changes

The engineering challenge is timing, not contracts: subagent events are emitted while the parent loop is awaiting the `task_spawn` tool (the loop generator is blocked, cannot `yield`). So:

- **`_category_factories.py`**: `make_chat_subagent_dispatcher` gains `event_emitter` (kw-only), threaded into `DefaultSubagentDispatcher`.
- **`handler.py`**: `build_real_llm_handler` + the `build_handler` dispatch gain `subagent_event_emitter`, threaded down; the echo handler (no subagent dispatcher) ignores it.
- **`router.py`**: the chat handler fn creates a `subagent_event_buffer: list[LoopEvent]` + an async `_relay_subagent_event` closure that appends to it, passes the emitter into `build_handler` + the buffer into `_stream_loop_events`. NEW `_drain_subagent_frames(buffer) -> list[bytes]` helper serializes buffered events (mirroring the loop-event `NotImplementedError`/`None` skip); `_stream_loop_events` drains it before each loop event + after the loop. Single asyncio task (the append + the drain both run in `_stream_loop_events`'s task) → no queue, no lock.

**`loop.py` UNCHANGED**; `dispatcher.py` / `events.py` / `sse.py` / frontend UNCHANGED.

## Modified Files List

- `backend/src/api/v1/chat/_category_factories.py` (+8)
- `backend/src/api/v1/chat/handler.py` (+15)
- `backend/src/api/v1/chat/router.py` (+62/-3)
- `backend/tests/unit/api/v1/chat/test_subagent_sse_relay.py` (NEW — 6 tests)

## Verification

- **Gate**: mypy `src --strict` 0/351 · pytest **2277** (baseline 2271 → +6, 0 deletions) · run_all 10/10 (AP-1 — the drain is not flagged as a pipeline; `check_event_schema_sync` green; `check_cross_category_import` green) · black/isort/flake8 clean · `loop.py` diff = 0.
- **Tests**: factory threads emitter / `_drain_subagent_frames` serializes + empties / `_stream_loop_events` relays a buffered spawn into `subagent_spawned`+`subagent_completed` frames / empty-buffer no-regression. Sprint 57.12 emission + 57.94 child-loop tests UNCHANGED + green.
- **Drive-through PASS** (real UI :3007 + fresh backend PID 50200 + real Azure gpt-5.2): a `task_spawn` chat request → BEFORE: Tree "no subagents spawned this session"; AFTER: Tree node `fork` · completed · 3,692 tokens · "subagent node is visible" + the Trace shows `subagent_spawned`/`subagent_completed` frames (the relayed dispatcher events). Evidence: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-95/artifacts/`.

## Impact

Backend-only (3 chat-composition files); no DB/migration, no contract change, no frontend change, `loop.py` untouched. Closes `AD-Subagent-Child-Event-SSE-Relay` at the **node level**; Scope B (relaying the child's inner turn-by-turn LoopEvents for an expandable Tree) remains open (needs a `LoopEvent` base `parent_session_id`/`depth` field + `ForkExecutor` forwarding + frontend nested render).
