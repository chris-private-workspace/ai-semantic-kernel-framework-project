# CHANGE-093: chat-v2 session history replay (arc slice 2/2 — complete the backend transcript foundation + the frontend click→replay)

**Date**: 2026-06-16
**Sprint**: 57.126
**Scope**: api/v1/chat (Cat 12 persistence) + frontend/chat_v2 (service + store + component)
**Closes**: `AD-ChatV2-Session-History-Replay-Phase58` (both halves shipped → the 2-sprint arc is COMPLETE)

## Problem

The 2026-06-06 drive-through audit flagged a soft Potemkin: clicking a historical session in the chat-v2 list (`SessionList.tsx` → `setActiveSessionId`) only HIGHLIGHTED it and did NOT load/render that session's conversation. Sprint 57.125 shipped the backend half (persist the main SSE stream to `message_events` + `GET /sessions/{id}/events`), but Day-0 三-prong of THIS sprint found the 57.125 foundation **incomplete**:

1. **User prompts are persisted NOWHERE** — `loop_start`/`turn_start`/`llm_*` events carry no user text; the initial prompt is a client-side `pushUserMessage` (never an SSE frame); `state_data` explicitly EXCLUDES messages (`checkpointer.py:217` "Excludes messages"); the `messages` table has no writer; only HITL-paused sessions stash messages in `durable.metadata` (a "SPIKE shortcut"). → a pure-frontend replay of `/events` would render agent turns with the user's questions MISSING.
2. **Multi-turn `sequence_num` collision** (latent 57.125 bug) — `main_seq` reset to 0 per request (`router.py:675`); a session with ≥2 sends got colliding `sequence_num`s → the reader's `ORDER BY sequence_num` scrambled multi-turn replay (57.125's probe only tested a single send).

## Root Cause

57.125's plan inherited an incorrect premise ("`state_data` = the LLM message list") and only tested single-send persistence. The agent-side event stream is genuinely the only persisted source, and it never carried the user prompt; and `main_seq` was per-request, not per-session.

## Solution

**User decision** (2026-06-16, two AskUserQuestions — Option C "interleave from `/state`" was found non-viable because `/state` has no messages): **Option B — complete the backend writer** so the single `/events` source replays a complete `user→agent→user→agent` conversation.

**Backend** (`backend/src/api/v1/chat/router.py`):
- `_max_main_seq(db, tenant_id, session_id)` — `SELECT COALESCE(MAX(sequence_num),0)` for the MAIN session_id (sidechain rows key by subagent_id → excluded). `db None`→0.
- `_stream_loop_events`: `main_seq = await _max_main_seq(...)` (seed from MAX → globally monotonic per session across sends) + persist the inbound `user_input` as a `user_message` `message_events` row FIRST per send (`{"type":"user_message","data":{"text":...}}` via the EXISTING `_persist_main_event`; **persist-only** — never yielded to the live stream, since the live UI shows the prompt via `pushUserMessage`). The row sits before `loop_start` so the 57.116/120 active_skill stamping reconstructs on replay.

**Frontend**:
- `services/chatService.ts`: `fetchSessionEvents(id)` (GET `/events` via `fetchWithAuth`, mirror `listSessions`) + `PersistedSessionEvent` type.
- `types.ts`: `UserMessageEvent = {type:"user_message"; data:{text:string}}` — hand-written **persist-only** (NOT in the codegen wire union / `KNOWN_LOOP_EVENT_TYPES`; wire count stays 24).
- `store/chatStore.ts`: factory `create((set, get) =>` (added `get`); `mergeEvent` param widened to `LoopEvent | UserMessageEvent` + a NEW `user_message` case (push a UserTurn); NEW `loadSessionHistory(id)` action — live guard (skip the running session) → conversation-only reset (preserve `sessions`+`mode`, set both ids, `_turnCounter=0`) → `fetchSessionEvents` → race guard (latest-clicked-wins) → `sort(sequence_num)` → replay each `{type,data}` through `mergeEvent`.
- `components/SessionList.tsx`: `SessionItem` onClick + keyboard → `void loadSessionHistory(session.id)` (was `setActiveSessionId`; the action sets `activeSessionId` so the highlight still works).

**No** migration / codegen / new wire event (count 24) / `styles-mockup.css` change (ZERO new CSS — replay reuses the existing turn/block components).

## Verification

- **Backend tests** (`test_main_transcript_persist.py`): user_message row first (seq 1, exact text) + multi-turn `test_main_seq_continues_across_sends` (2 sends → seq 1..8 monotonic, ORDER BY yields send-1 then send-2). 5 passed.
- **Frontend Vitest** (+9): `chatStore.historyReplay.test.ts` (6 — replay→user+agent turns / sort / live guard / race guard / reset preserves sessions / fetch error) + `chatService.sessionEvents.test.ts` (2) + `SessionList.test.tsx` (+1 trigger).
- **Gates**: mypy `src` 0/370 · run_all 10/10 (`check_event_schema_sync` green → wire 24 intact) · full pytest 2712+5skip (+1) · Vitest 904 (+9) · `diff styles-mockup.css` empty · mockup-fidelity 51 byte-identical · lint exit 0 · build ✅.
- **Drive-through PASS** (real UI + real backend + real Azure gpt-5.2, dev-login jamie/acme-prod): a 2-message real chat (session `d5bd3950…`) → `/events` = 34 events / 2 user_message rows / seq 1..34 monotonic → reload (fresh store) → click the session → the COMPLETE conversation replayed (both user prompts + both agent turns + verification + the full trace; AP-4 clear) → a follow-up continued the SAME session (`/events` = 51 events / 3 user_message rows / seq 1..51 monotonic). Screenshots: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-126/artifacts/sprint-57-126-replay-{complete,then-continue}.png`.

## Impact

Backend (1 src file: a helper + a 2-line writer addition + a seed) + frontend (4 src files: service / store / types / component + 3 tests). The chat-v2 session list's click is now functional (a historical conversation loads + renders + can be continued) — the soft Potemkin from the drive-through audit is closed. NO migration / wire / codegen / CSS. The replay reuses the live `mergeEvent` reducer unchanged.

## Out of scope (follow-on)

- The resume path persisting main events (a pre-existing 57.125 gap — resume continuations unpersisted).
- A delta-filter (`AD-ChatV2-Transcript-Volume-Filter`) / retention policy (`AD-ChatV2-Transcript-Retention`, Phase 58+).
- Promoting `user_message` to a live wire event (it stays persist-only).
- The live multi-turn context gap (the backend doesn't rehydrate prior conversation messages for the live loop — observed in the drive-through where turn 2 lost "it"→Paris context; a separate pre-existing issue, NOT replay-related).
