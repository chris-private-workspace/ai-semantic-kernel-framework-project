# Sprint 57.126 Plan — chat-v2 session history replay (arc slice 2 of 2: complete the backend transcript foundation + the frontend click→replay). **The user-facing payoff** of the 2-sprint arc opened by 57.125. Day-0 三-prong (this sprint) caught that the 57.125 foundation is **incomplete**: the persisted `message_events` stream contains only the *agent-side* SSE events — the user's prompts are NOT persisted anywhere (the initial prompt is a client-side `pushUserMessage`, never an SSE event; `state_data` explicitly EXCLUDES messages — `checkpointer.py:217` "Excludes messages"; the `messages` table has no writer; only HITL-paused sessions stash messages in `durable.metadata` as a "SPIKE shortcut"). So a pure-frontend replay of `/events` would render agent turns with the user's questions MISSING. Day-0 ALSO caught a latent 57.125 multi-turn ordering bug: `main_seq` resets to 0 per request (`router.py:675`) → a session with ≥2 sends gets colliding `sequence_num`s → the reader's `ORDER BY sequence_num` scrambles multi-turn replay (57.125's probe only tested a single send). **User decision (2026-06-16, two AskUserQuestions)**: complete the backend (Option B) — the writer ALSO persists the user prompt as the first `message_events` row of each send (persist-only, NOT streamed live; the router already has `user_input` in scope) + seed `main_seq` from the session's current `MAX(sequence_num)` (multi-turn ordering fix) — so the single `/events` source replays a complete `user→agent→user→agent` conversation. The frontend then: a session click fetches `/events`, sorts by `sequence_num`, and replays each `{type, data}` through the EXISTING exported 18-case `mergeEvent` reducer (`chatStore.ts:360`, `(ev)=>void`, callable standalone) + a NEW `user_message` case (pushes a UserTurn) onto a conversation-only reset — reconstructing pixel-identical historical turns (the `user_message` row sits before `loop_start` so the 57.116/120 active_skill stamping reconstructs too) — then makes the loaded session active so a follow-up continues it. **ZERO new CSS** (`styles-mockup.css` byte-identical, mockup 51); `user_message` is persist-only → NO new wire event (count 24) / codegen / migration. Full-stack (backend writer completion + frontend replay) → a real UI + real backend + real LLM **drive-through is MANDATORY**. CHANGE-093; NO design note (feature continuation; the replay contract is design note 37 §4, amended here with the user_message row).

**Status**: Approved-to-execute (user 2026-06-16: "現在執行 1. AD-ChatV2-Session-History-Replay-Phase58 前端半 → Sprint 57.126" → Day-0 三-prong found Option C non-viable → AskUserQuestion #1 picked the hybrid, AskUserQuestion #2 (after deeper verify proved no persisted user-prompt source exists) picked **Option B: complete the backend writer**).
**Branch**: `feature/sprint-57-126-chatv2-session-history-replay-frontend`
**Base**: `main` HEAD `c8a338c8` (post-#300 — Sprint 57.125 backend SSE transcript persistence + replay endpoint).
**Slice**: arc slice 2 of 2 under `AD-ChatV2-Session-History-Replay-Phase58`. 57.125 shipped the agent-side persistence + the read endpoint; this slice completes the foundation (the user-prompt row + the multi-turn ordering fix) AND ships the frontend replay UI. Closes the AD.
**Scope decisions**: (a) **Backend (complete the foundation)**: the `_stream_loop_events` writer persists the inbound `user_input` as a synthetic `message_events` row (`event_type="user_message"`, `data={"text": user_input}`) at the START of each send (persist-only — the live UI already shows it via `pushUserMessage`, so it is NOT added to the live SSE stream / wire schema) + seeds `main_seq` from the session's `MAX(sequence_num)` so `sequence_num` is globally monotonic per session across sends (multi-turn ordering fix). (b) **Frontend**: replay reuses the EXISTING `mergeEvent` reducer + a NEW `user_message` case (pushes a UserTurn); a conversation-only reset (model on `applyPivot`); a `fetchSessionEvents` service; the click rewire; route continuation; latest-clicked + skip-if-live guards. (c) `user_message` is a hand-written persist-only `LoopEvent` union member — NOT in the live wire schema / `KNOWN_LOOP_EVENT_TYPES` (count 24 unchanged, NO codegen). (d) **ZERO new CSS** (reuse `.session-item[data-active]` + the turn components; `styles-mockup.css` untouched, byte-identical 51). (e) NO migration (`message_events` exists). (f) Full-stack user-facing → a real drive-through is MANDATORY (not gate-only).

---

## 0. Background

### What 57.125 shipped — and what Day-0 found it MISSING

Sprint 57.125 (merged `c8a338c8`, PR #300) shipped:
- **`_persist_main_event`** (`router.py:568`): each main-session SSE event (the serialized `payload`) → a `message_events` row, keyed by the MAIN `session_id`, `sequence_num=main_seq`, env-gated `MAIN_TRANSCRIPT_OBSERVER` (default on), best-effort SAVEPOINT.
- **`GET /api/v1/sessions/{id}/events`** (`sessions.py` `list_session_events`): the ordered stream, `{events: [{type, data, sequence_num, timestamp_ms}, ...]}`, cross-tenant/unknown → 200 `[]`.

Day-0 三-prong (this sprint) verified the persistence reality and found **two gaps** the 57.125 plan missed (it inherited an incorrect premise that `state_data` holds the message list):

**Gap 1 — user prompts are not persisted anywhere** (the linchpin finding):
| Source | Reality (grep-verified) |
|--------|--------------------------|
| `message_events` (57.125) | agent-side SSE events only — `loop_start.data`=`{session_id, request_id, active_skill}`, `turn_start`=`{turn_num}`, `llm_request`=`{model, tokens_in}`, `llm_response`=the agent output. **No user prompt event** (the initial prompt is a client-side `pushUserMessage`, NOT an SSE frame). |
| `state_snapshots.state_data` | `_serialize_state_for_db` (`checkpointer.py:217`) docstring: **"Excludes messages + pending_tool_calls"**; `_deserialize` (`:258`) `messages=[]  # caller rehydrates from messages history`. The user prompts are NOT here. |
| `state_data["durable"]["metadata"]` | messages ARE serialized here, but ONLY by the HITL deferred-pause branch (`loop.py:242/330/3594` "SPIKE shortcut") — NOT for normal completed sessions. |
| `messages` table | no main-flow writer (every `Message(...)` in `backend/src` is the Cat-3 in-memory dataclass, NOT a `db.add` row). |
| `conversation_summary` | a summary, not the verbatim prompt. |

→ A pure-frontend replay of `/events` reconstructs agent turns with the user's questions MISSING. **User picked Option B**: complete the writer so the user prompt is persisted (the single `/events` source then replays a complete conversation).

**Gap 2 — multi-turn `sequence_num` collision** (latent 57.125 bug): `main_seq = 0` per request (`router.py:675`), incremented per event. A session with ≥2 sends (each a separate `_stream_loop_events` call) gets two row-ranges both starting at `sequence_num=1` → the reader's `ORDER BY sequence_num` interleaves them WRONGLY. 57.125's live probe only tested a single send (16 events). This sprint's drive-through (replay a multi-turn session + continue) requires the fix: seed `main_seq` from the session's `MAX(sequence_num)` so it is globally monotonic per session.

### The Option-B elegance (why the foundation completion is small + clean)

`_stream_loop_events` (`router.py:629`) receives both `session_id` (`:632`) and `user_input` (`:635`) at function entry. `_persist_main_event` (`:568`) takes a `{"type", "data"}` payload dict. So:
- **User prompt persist**: before the `async for` loop, persist `{"type": "user_message", "data": {"text": user_input}}` via the EXISTING `_persist_main_event` (no new helper). It gets `sequence_num` 1 of this send → sits before `loop_start` → on replay the `user_message` case pushes the UserTurn, then the replayed `loop_start` finds it as the last user turn and stamps `active_skill` (57.116/120) — reconstructing the chip too.
- **Ordering fix**: `main_seq = await _max_main_seq(db, session_id, tenant_id)` (a `SELECT COALESCE(MAX(sequence_num),0)` for the MAIN session_id — sidechain rows key by `subagent_id` so they're naturally excluded) instead of `0`. Each send continues the count; multi-turn `ORDER BY sequence_num` is correct.
- **Frontend**: the persisted `{type, data}` is byte-identical to the live frame; `mergeEvent` is exported + standalone-callable + reads only `ev.type`/`ev.data` → replay = `reset-conversation` then `for (ev of sortedEvents) mergeEvent({type, data})`; a NEW `user_message` case pushes the UserTurn. No reducer rewrite, no new visual surface, no new CSS.

### Ground truth (Day-0 head-start — direct reads on `main` HEAD `c8a338c8`; ALL re-verified in §checklist 0.1)

**Backend (writer completion):**
- `router.py:629-740` — `_stream_loop_events`; `session_id` + `user_input` params at entry; `main_seq = 0` (`:675`, → seed from DB); `main_transcript_on` (`:676`); the `async for event in loop.run(...)` (`:684`); `main_seq += 1` + `_persist_main_event(...)` (`:728-736`).
- `router.py:568-601` — `_persist_main_event(payload, *, db, tenant_id, session_id, sequence_num)` (reuse for the user_message row).
- `router.py:1175` — `loop.resume(...)` in the resume path (`_stream_resume_events`) — does NOT persist main events (a pre-existing 57.125 gap; resume continuations unpersisted — OUT of scope, noted §9).
- `infrastructure/db/models/sessions.py:223-267` — `MessageEvent` ORM (`event_type`, `event_data` JSONB, `sequence_num`, `timestamp_ms`).
- `backend/tests/integration/api/test_main_transcript_persist.py` — the 57.125 writer tests (extend for the user_message row + multi-turn ordering).

**Frontend (replay UI):**
- `frontend/src/features/chat_v2/services/chatService.ts:112-120` — `listSessions` (mirror for `fetchSessionEvents`); `:50` `fetchWithAuth`; `:130-158` `streamChat` (`:79` `...(sessionId ? {session_id: sessionId} : {})` → continuation keys off store `sessionId` ✅); `:261-281` `parseSSEFrame` builds `{type, data}` (the reducer-input shape ✅).
- `frontend/src/features/chat_v2/store/chatStore.ts:360` — `mergeEvent(ev) => set((s) => switch(ev.type){...})` (exported, standalone-callable; reads `ev.type`/`ev.data` only ✅); `:318` `create((set) => ...)` (NO `get` today → ADD `get` for the async replay action); `:295-316` `applyPivot` (the conversation-only-reset template: clears turns/status/approvals/verifications/subagents/spans/memoryOps, preserves `sessions`, sets `sessionId`+`activeSessionId`); `:208` `let _turnCounter` (reset on replay); `:352-358` `pushUserMessage` (the UserTurn shape the `user_message` case mirrors).
- `frontend/src/features/chat_v2/components/SessionList.tsx:58-115` — `SessionItem`; `:70` `onClick={() => setActiveSessionId(session.id)}` + `:71-76` keyboard (the rewire point → `loadSessionHistory`); `:69` `data-testid={\`session-item-${id}\`}` (drive-through/test handle).
- `frontend/src/features/chat_v2/hooks/useLoopEventStream.ts:65-99` — `send()` passes `session_id: sessionId` from the store (`:57,79`) → continuation automatic once `loadSessionHistory` sets `sessionId` ✅.
- `frontend/src/features/chat_v2/types.ts` — `LoopEvent` union + `Turn` types (ADD a hand-written `UserMessageEvent = {type:"user_message"; data:{text:string}}` union member — persist-only, NOT codegen).
- Tests live at `frontend/tests/unit/chat_v2/...` (D-fe-test-path: NOT `.../features/chat_v2/...`); `frontend/tests/unit/chat_v2/components/SessionList.test.tsx` + `chatStore.*.test.ts` + `chatService.*.test.ts` exist.

**Mockup-fidelity:** `reference/design-mockups/styles.css` ⟷ `frontend/src/styles-mockup.css` byte-identical; `.session-item[data-active]` styles the highlight; replay reuses the turn/block components → **ZERO new CSS**.

**Baselines (57.125 closeout)**: full pytest **2711+5skip** · wire **24** · Vitest **892** · mockup **51** · mypy `src` **0/370** · run_all **10/10**. Re-verify Day-0.

### STALE / drift findings already catalogued (Day-0; full detail → progress.md)

- **D-user-message-not-persisted** (⚠️ THE finding) → Option B (backend writer completion).
- **D-multiturn-seq-collision** (latent 57.125 bug) → seed `main_seq` from DB MAX.
- **D-state-excludes-messages**: `state_data` has no message list (57.125 plan premise was wrong) → Option C dead.
- **D-mergeEvent-input-shape** ✅: `mergeEvent({type, data})`; reducer reads only `type`/`data`.
- **D-no-get-in-factory** ✅: `create((set) =>` → add `get` for the async replay action (idiomatic; `useLoopEventStream` already uses `useChatStore.getState()`).
- **D-continuation-route** ✅: `send()` keys off store `sessionId` → continuation free once set.
- **D-fe-test-path** ✅: `frontend/tests/unit/chat_v2/...` (NOT `.../features/...`).
- **D-resume-unpersisted** (noted, OUT of scope): the resume path doesn't persist main events (pre-existing 57.125 gap).

## 1. Sprint Goal

Complete the chat-v2 history-replay arc: the backend writer ALSO persists the user's prompt (a `user_message` `message_events` row at the start of each send, persist-only) and seeds `main_seq` from the session's `MAX(sequence_num)` (multi-turn ordering fix) so the single `GET /api/v1/sessions/{id}/events` source replays a complete `user→agent→user→agent` conversation; the frontend `loadSessionHistory` action (triggered by a session click) fetches it, sorts by `sequence_num`, and replays each `{type, data}` through the EXISTING `mergeEvent` reducer + a NEW `user_message` case — reconstructing pixel-identical historical turns (incl. the active_skill chip) in the unchanged turn/block components — then makes the loaded session active so a follow-up continues it. Guarded by latest-clicked-wins + skip-if-live. ZERO new CSS (mockup 51 unchanged); `user_message` persist-only → NO wire (24) / codegen / migration. Closes `AD-ChatV2-Session-History-Replay-Phase58`. Proven by backend integration tests (user_message row first + multi-turn monotonic ordering) + Vitest (replay incl. user turns; guards) **and a MANDATORY real UI + real backend + real LLM drive-through** (a multi-turn real chat → click it → complete replay renders → continue). CHANGE-093; NO design note.

## 2. User Stories

- **US-1** (backend — user prompt persist): 作為 chat 主流量 `_stream_loop_events`，我希望每個 send 開頭把 `user_input` 以 `{"type":"user_message","data":{"text":...}}` 經既有 `_persist_main_event` 持久化成 `message_events` 的第一筆（persist-only，不加入 live SSE 流），以便 `/events` 重播能重建使用者的提問。
- **US-2** (backend — multi-turn ordering): 作為重播來源，我希望 `main_seq` 從該 session 的 `MAX(sequence_num)` seed（非每 request 從 0），以便多輪 session 的 `sequence_num` 全域單調、`ORDER BY sequence_num` 重播順序正確。
- **US-3** (frontend — service): 作為 chat-v2 前端，我希望 `fetchSessionEvents(id)` GET `/api/v1/sessions/{id}/events` 回傳 `{type,data,sequence_num,timestamp_ms}[]`（鏡像 `listSessions`）。
- **US-4** (frontend — replay action + user_message case): 作為 chat-v2 store，我希望 `loadSessionHistory(id)` 做 conversation-only reset（保留 `sessions`、設 `activeSessionId`+`sessionId`、歸零 `_turnCounter`）→ 依 `sequence_num` 排序 → 對每事件呼叫 `mergeEvent({type,data})`，其中 NEW `user_message` case push 一個 UserTurn（loop_start 之前 → activeSkill 正確重建）。
- **US-5** (frontend — click + guards): 作為使用者，我希望點歷史 session 會載入並渲染其完整對話（`SessionItem` onClick → `loadSessionHistory`），有 race guard（latest-clicked-wins）+ live guard（當前 running session 不重載）。
- **US-6** (frontend — continuation): 作為使用者，我希望載入歷史 session 後送出的下一則訊息延續該 session（`send` 以 store `sessionId` 為準 — Day-0 已確認）。
- **US-7** (tests): backend（user_message row first / multi-turn monotonic seq / env-off no rows）+ frontend Vitest（service / replay incl. user turns / sort / race / live guard / click）。
- **US-8** (drive-through — MANDATORY): 真 UI + 真後端（`MAIN_TRANSCRIPT_OBSERVER` on）+ 真 Azure：一個**多輪**真 chat → 點該 session → 完整對話（user+agent turns、thinking/answer/tools/verification、skill chip）pixel-identical 重播 → 送 follow-up 延續同 session；逐控件 AP-4 walk + 截圖 + 實際-vs-預期 → progress.md。
- **US-9** (closeout): CHANGE-093 + 收尾（retro + calibration + navigators + **CLOSE the AD**）。

## 3. Technical Specifications

### 3.0 Architecture (backend writer completion + frontend replay; NO migration / wire / codegen / CSS)

```
# Backend (complete the 57.125 transcript foundation)
backend/src/api/v1/chat/router.py   (EDIT): _stream_loop_events — seed main_seq from MAX(sequence_num) + persist user_message first (reuse _persist_main_event); + _max_main_seq helper
backend/tests/integration/api/test_main_transcript_persist.py (EDIT): user_message row first + multi-turn monotonic seq
# Frontend (replay UI)
frontend/src/features/chat_v2/services/chatService.ts  (EDIT): fetchSessionEvents + PersistedSessionEvent
frontend/src/features/chat_v2/store/chatStore.ts       (EDIT): +get in factory; loadSessionHistory action (reset+sort+replay+guards); user_message mergeEvent case
frontend/src/features/chat_v2/types.ts                 (EDIT): UserMessageEvent union member (persist-only) + store action type
frontend/src/features/chat_v2/components/SessionList.tsx (EDIT): SessionItem onClick/keyboard → loadSessionHistory
frontend/tests/unit/chat_v2/chatStore.historyReplay.test.ts    (NEW): replay incl. user turns + guards
frontend/tests/unit/chat_v2/chatService.sessionEvents.test.ts  (NEW): fetchSessionEvents
frontend/tests/unit/chat_v2/components/SessionList.test.tsx     (EDIT): click → loadSessionHistory
# docs
claudedocs/4-changes/feature-changes/CHANGE-093-chatv2-session-history-replay.md (NEW)
migrations / events.py / sse.py / codegen / styles-mockup.css: UNTOUCHED (wire 24, mockup 51)
```

### 3.1 Backend — user-prompt persist + ordering fix (US-1/2) — `router.py`

- **`_max_main_seq(db, session_id, tenant_id) -> int`** (NEW helper): `SELECT COALESCE(MAX(sequence_num), 0) FROM message_events WHERE session_id=:sid AND tenant_id=:tid`. Returns 0 for a fresh session. (Sidechain rows key by `subagent_id` ≠ the main `session_id` → excluded naturally.) `db is None` → 0.
- **`_stream_loop_events`**: replace `main_seq = 0` (`:675`) with `main_seq = await _max_main_seq(db, session_id, tenant_id) if main_transcript_on else 0`. Then, BEFORE the `async for`, if `main_transcript_on and user_input`: `main_seq += 1; await _persist_main_event({"type": "user_message", "data": {"text": user_input}}, db=db, tenant_id=tenant_id, session_id=session_id, sequence_num=main_seq)`. The loop events then continue incrementing `main_seq`.
- **Persist-only**: the `user_message` row is NEVER yielded to the live stream (no `format_sse_message` / `yield` for it) — the live UI shows the prompt via `pushUserMessage`. Only the persisted transcript carries it (for replay).
- Multi-tenant: `tenant_id` on the row (RLS). Best-effort SAVEPOINT inherited from `_persist_main_event`.

### 3.2 Frontend — service (US-3) — `chatService.ts`

- `fetchSessionEvents(sessionId): Promise<PersistedSessionEvent[]>` mirroring `listSessions`: `fetchWithAuth(\`/api/v1/sessions/${sessionId}/events\`, {method:"GET"})`; throw on non-2xx; return `(await res.json()).events`.
- `PersistedSessionEvent = { type: string; data: Record<string, unknown>; sequence_num: number; timestamp_ms: number }`.

### 3.3 Frontend — replay action + user_message case + guards (US-4/5/6) — `chatStore.ts` + `types.ts`

- Add `get` to the factory: `create<ChatStoreState>((set, get) => ({...}))` (idiomatic; update the 57.69 `applyPivot` comment to note `get` is now available but the helper stays pure for the shared `agent_handoff` `s`-only case).
- **`loadSessionHistory(sessionId): Promise<void>`** + signature in `ChatStoreState`:
  - live guard: `if (get().sessionId === sessionId && get().status === "running") return;`
  - conversation-only reset (model on `applyPivot`, but `handoffBanner: null`, `rawEvents: []`, `currentModel: null`): clear turns/spans/approvals/verifications/subagents/memoryOps/rawEvents/status/stopReason/errorMessage/currentModel/handoffBanner; PRESERVE `sessions`; set `activeSessionId=sessionId`+`sessionId=sessionId`; `_turnCounter = 0`.
  - race guard: after `const events = await fetchSessionEvents(sessionId)`, `if (get().activeSessionId !== sessionId) return;`
  - replay: `events.sort((a,b)=>a.sequence_num-b.sequence_num); for (const ev of events) get().mergeEvent({type: ev.type, data: ev.data} as LoopEvent);`
  - error: `catch → set({ errorMessage })`, leave pane empty.
- **`user_message` mergeEvent case** (NEW, `chatStore.ts`): `case "user_message": return { ...s, rawEvents, turns: [...s.turns, { role: "user", id: nextTurnId(), at: nowIso(), text: String(ev.data.text ?? "") }] };` — replay-only (never streamed live; the case is a no-op in the live path because the event is never emitted).
- **`types.ts`**: add `export type UserMessageEvent = { type: "user_message"; data: { text: string } };` to the `LoopEvent` union (hand-written, persist-only — NOT in the codegen wire schema / `KNOWN_LOOP_EVENT_TYPES`; wire count 24 unchanged).

### 3.4 Frontend — click rewire (US-5) — `SessionList.tsx`

- `SessionItem` onClick (`:70`) + keyboard (`:71-76`): `setActiveSessionId(session.id)` → `loadSessionHistory(session.id)` (subscribe the action; the action sets `activeSessionId` itself so the highlight keeps working). NO CSS change.

### 3.5 Frontend — continuation (US-6)

- `loadSessionHistory` sets `sessionId`; `send()` (`useLoopEventStream.ts:79`) already passes `session_id: sessionId` → a follow-up continues the loaded session (same mechanism as live multi-turn). Verified Day-0; confirmed live in the drive-through.

### 3.6 Tests (US-7)

- **Backend** (`test_main_transcript_persist.py`, EDIT): a send with a user_input → the FIRST `message_events` row is `event_type="user_message"` with `data.text == user_input`, `sequence_num=1`, then the loop events follow with monotonic seq; a SECOND send on the same session → its rows continue from `MAX+1` (no collision; `ORDER BY sequence_num` yields send-1 then send-2); env-off → no rows.
- **Frontend store** (`chatStore.historyReplay.test.ts`, NEW): given `[user_message, loop_start, turn_start, llm_response, loop_end]`, `loadSessionHistory` (mock `fetchSessionEvents`) → `turns == [UserTurn(text), AgentTurn(answer)]`; out-of-order input → identical after sort; live guard (running same session → no reload); race guard (stale resolution dropped); reset preserves `sessions`.
- **Frontend service** (`chatService.sessionEvents.test.ts`, NEW): `fetchSessionEvents` 200 → events / non-2xx → throw.
- **Frontend component** (`SessionList.test.tsx`, EDIT): click row → `loadSessionHistory(id)` (spy).

### 3.7 Drive-through (US-8) — real UI + real backend + real LLM (MANDATORY)

1. Clean restart (Risk Class E — backend `router.py` changed; `MAIN_TRANSCRIPT_OBSERVER` on; `Win32_Process` PID/PPID/StartTime sweep; fresh sole :8000 owner + startup log). Vite :3007 (node) NOT stopped (HMR picks up FE edits).
2. A **multi-turn** real-LLM chat in chat-v2 (Azure gpt-5.2): send ≥2 messages (a tool call / a `/skill` if easy) → note the session.
3. Start fresh / "New session" → **click the prior session** → assert the COMPLETE conversation replays: BOTH the user prompts AND the agent turns (thinking/answer/verification/tool/skill-chip), in correct multi-turn order; highlight moves; no crash / no empty pane.
4. **Continue**: send a follow-up in the loaded session → it continues the same `session_id` (a new turn streams; not a brand-new session).
5. Per-control AP-4 walk (clickable / effect / real label / renders); screenshots + observed-vs-intended → progress.md. Report "drive-through PASS" only if 2-4 actually pass on real LLM.

### 3.8 What is explicitly NOT done

The resume path persisting main events (a pre-existing 57.125 gap — resume continuations unpersisted; noted, separate AD); a delta-filter for volume (`AD-ChatV2-Transcript-Volume-Filter`); a retention/TTL policy (`AD-ChatV2-Transcript-Retention`); promoting `user_message` to a live wire event (it stays persist-only — count 24); a "viewing history" banner / loading skeleton (the mockup has none); any migration / codegen / `styles-mockup.css` change; reconstructing turns from `state_snapshots` (the dead Option A/C).

### 3.9 Validation (US-1..US-9)

Gates: mypy `src` **0/370 + the router edit** (re-assert 0 errors) · run_all **10/10** (wire **24** unchanged) · full pytest **2711+5skip + backend delta** (user_message + multi-turn tests) · Vitest **892 + frontend delta** · mockup-fidelity **51 UNCHANGED** (`diff styles-mockup.css` empty) · `npm run lint` clean (no `--silent`) · `npm run build` ✅ · codegen/migration **UNTOUCHED**. Plus: backend integration tests (user_message + ordering) + Vitest (replay + guards) + the §3.7 drive-through.

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 1 | `backend/src/api/v1/chat/router.py` | EDIT — `_max_main_seq` helper; `_stream_loop_events` seed `main_seq` from MAX + persist `user_message` first (reuse `_persist_main_event`) |
| 2 | `backend/tests/integration/api/test_main_transcript_persist.py` | EDIT — user_message row first + multi-turn monotonic seq + env-off |
| 3 | `frontend/src/features/chat_v2/services/chatService.ts` | EDIT — `fetchSessionEvents` + `PersistedSessionEvent` |
| 4 | `frontend/src/features/chat_v2/store/chatStore.ts` | EDIT — `+get` in factory; `loadSessionHistory` (reset+sort+replay+guards); `user_message` mergeEvent case; signature in `ChatStoreState` |
| 5 | `frontend/src/features/chat_v2/types.ts` | EDIT — `UserMessageEvent` union member (persist-only) |
| 6 | `frontend/src/features/chat_v2/components/SessionList.tsx` | EDIT — `SessionItem` onClick/keyboard → `loadSessionHistory` |
| 7 | `frontend/tests/unit/chat_v2/chatStore.historyReplay.test.ts` | NEW — replay incl. user turns + sort + race/live guards + reset preserves sessions |
| 8 | `frontend/tests/unit/chat_v2/chatService.sessionEvents.test.ts` | NEW — `fetchSessionEvents` |
| 9 | `frontend/tests/unit/chat_v2/components/SessionList.test.tsx` | EDIT — click → `loadSessionHistory` |
| 10 | `claudedocs/4-changes/feature-changes/CHANGE-093-chatv2-session-history-replay.md` | NEW — change record (backend completion + frontend replay + drive-through + arc-complete) |
| — | migrations / `events.py` / `sse.py` / codegen / `styles-mockup.css` | **UNTOUCHED / NONE** |

## 5. Acceptance Criteria

1. **Backend user prompt**: each send persists a `user_message` `message_events` row (`data.text == user_input`) as that send's first transcript row (lowest `sequence_num` of the send); persist-only (NOT in the live SSE stream).
2. **Backend ordering**: `main_seq` seeds from the session's `MAX(sequence_num)`; a 2-send session → globally monotonic `sequence_num` → `GET /events` returns send-1's events then send-2's, in order.
3. **Frontend replay**: `loadSessionHistory(id)` clears the conversation slices (preserving `sessions`), sorts by `sequence_num`, replays through `mergeEvent` (incl. the NEW `user_message` → UserTurn case) → the COMPLETE historical conversation (user + agent turns, incl. the active_skill chip) renders in the existing components; `activeSessionId`+`sessionId` set.
4. **Guards**: clicking the running live session → no reload; a stale fetch after a newer click → dropped.
5. **Continuation**: after loading a historical session, a follow-up continues the same `session_id`.
6. **Zero CSS / mockup**: `diff styles-mockup.css` empty; mockup 51 UNCHANGED; replay reuses the live components (no new surface).
7. **No wire/codegen/migration**: `user_message` is a persist-only hand-written type (count 24); Alembic head unchanged.
8. Gates: mypy 0 errors · run_all 10/10 (24) · pytest 2711+5 + backend delta · Vitest 892 + frontend delta · mockup 51 · lint clean · build ✅.
9. **Drive-through PASS (MANDATORY, real UI + backend + LLM)**: a multi-turn real chat → click it → complete replay (user + agent turns, correct order) → continue same session; per-control AP-4 walk clean; screenshots + observed-vs-intended in progress.md. (NOT gate-only.)
10. `AD-ChatV2-Session-History-Replay-Phase58` CLOSED (both halves); CHANGE-093; NO design note; calibration recorded; navigators + next-phase-candidates updated.

## 6. Deliverables

- [ ] US-1 backend `user_message` persist (reuse `_persist_main_event`) (`router.py`)
- [ ] US-2 backend `main_seq` seed from `MAX(sequence_num)` (`_max_main_seq`) (`router.py`)
- [ ] US-3 `fetchSessionEvents` + `PersistedSessionEvent` (`chatService.ts`)
- [ ] US-4 `loadSessionHistory` (reset+sort+replay+guards) + `user_message` mergeEvent case + `+get` (`chatStore.ts`, `types.ts`)
- [ ] US-5 `SessionItem` click/keyboard → `loadSessionHistory` (`SessionList.tsx`)
- [ ] US-6 continuation (loaded session active; send keys off `sessionId`)
- [ ] US-7 backend tests (user_message row + multi-turn ordering) + Vitest (service / replay incl. user turns / guards / click)
- [ ] US-8 drive-through (multi-turn real chat → click → complete replay → continue; screenshots; MANDATORY)
- [ ] US-9 CHANGE-093 + closeout (retro + calibration + navigators + CLOSE the AD)

## 7. Workload Calibration

- Scope class **`chatv2-history-replay-fullstack` 0.60** (NEW — a full-stack feature: a small backend writer completion (reuse `_persist_main_event` for the user_message row + a `MAX(sequence_num)` seed; mirrors the proven 57.125 observer) + a multi-turn ordering fix + a frontend replay feature (a service fetch + a store replay action with a new reducer case + click rewire + guards; ZERO new CSS, NO wire/codegen). Closest classes: the backend half ≈ `chatv2-transcript-persistence-spike` 0.60 (57.125); the frontend half ≈ `frontend-feature-with-event-wire-addition` 0.55 (but no wire add). Combined full-stack → 0.60. **Ceremony-floor note** (57.120/122/123): a full-ceremony parent-direct sprint WITH a mandatory drive-through does NOT drop below ~0.55 even for bounded code.
- **Agent-delegated: no** (parent-direct; the user_message placement + the `MAX(seq)` ordering fix + the replay shape mapping + the reset-vs-`reset()` + race/live guards are precise and best hand-authored + self-verified). `agent_factor` 1.0 → 3-segment form.
- Bottom-up est ~10.5 hr (Day-0 三-prong + the linchpin grep chain ~1.5 (DONE) · backend user_message + seed + helper ~1.0 · backend tests ~1.0 · service ~0.5 · store action + user_message case + get ~1.75 · click ~0.5 · Vitest ~1.75 · drive-through + clean restart ~1.5 · CHANGE-093 + closeout ~1.0) → class-calibrated commit ~6.3 hr (mult 0.60). Day-4 retro Q2 verifies (`chatv2-history-replay-fullstack` 1st data point; flag if the backend ordering fix or the drive-through over-runs).

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| **Multi-turn `sequence_num` collision** (latent 57.125 bug) | seed `main_seq` from `MAX(sequence_num)` for the MAIN session_id; a backend test drives 2 sends and asserts globally monotonic seq + correct `ORDER BY` |
| **`user_message` accidentally streamed live** (double-render: pushUserMessage + a streamed user_message) | persist-only — NO `yield`/`format_sse_message` for it; it never enters the live SSE stream / `KNOWN_LOOP_EVENT_TYPES`; the live UI keeps using `pushUserMessage`; the replay case is a no-op live (the event is never emitted) |
| **`user_message` ordering vs loop_start** | persisted as the send's FIRST row (lowest seq) → on replay the UserTurn is pushed before `loop_start`, so `loop_start`'s active_skill stamping finds it (chip reconstructs) |
| **D-mergeEvent-input-shape** | `mergeEvent({type, data})` (verified reads only type/data); replay drops seq/timestamp; a store test asserts a fixed array → expected turns |
| **No `get` in the store factory** | add `get` to `create((set, get) =>` (idiomatic; `useLoopEventStream` already uses `useChatStore.getState()`); `applyPivot` stays a pure helper |
| **Replaying onto a live/dirty store** | conversation-only reset BEFORE replay (preserve `sessions`); live guard skips a running session; `_turnCounter=0` for fresh ids |
| **Race: two fast clicks** | latest-clicked-wins — after the await, `if get().activeSessionId !== id return` |
| **Out-of-order events** | the persisted stream is `sequence_num`-ordered; replay sorts defensively; a store test feeds a shuffled array |
| **Mockup-fidelity drift** | ZERO new CSS (reuse `.session-item[data-active]` + turn components); `diff` empty; Prong 2.5 confirms no child re-point dragged in |
| **Risk Class E** — stale `--reload` backend serves pre-edit `router.py` during the drive-through | clean restart (`Win32_Process` PID/PPID/StartTime sweep; orphan spawn-workers on :8000); confirm fresh sole owner + startup log + `GET /events` shows a user_message row before trusting the UI |
| **Resume continuations unpersisted** (pre-existing) | OUT of scope (noted §9); a session that ended via resume replays up to the pause (acceptable; a follow-on AD) |
| **Test/Vitest counts move** | document the exact deltas in the retro; the gate asserts the finals |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- **The resume path persisting main events** — a pre-existing 57.125 gap (resume continuations unpersisted); a separate follow-on AD.
- **Promoting `user_message` to a live wire event** (with codegen) — it stays persist-only (count 24); only needed if the live UI ever wants an event-driven user turn.
- **A delta-filter / retention policy** — `AD-ChatV2-Transcript-Volume-Filter` (🟢) / `AD-ChatV2-Transcript-Retention` (🟢, Phase 58+).
- **A "viewing history" banner / loading skeleton** — the mockup has none (instant); add only if the drive-through shows lag (YAGNI).
- **Replaying a handed-off parent session's pivot** — `agent_handoff` in a replayed stream would `applyPivot` (clear turns); rare edge (the parent stream typically ends at handoff); a follow-on if it surfaces.
- **Any migration / codegen / `styles-mockup.css` change** (count 24, mockup 51 unchanged); **reconstructing turns from `state_snapshots`** (the dead Option A/C).
