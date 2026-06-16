# Sprint 57.126 — Checklist (chat-v2 session history replay, arc slice 2 of 2: **complete the backend transcript foundation + the frontend click→replay**. Day-0 三-prong caught the 57.125 foundation is incomplete — user prompts are persisted NOWHERE (state_data EXCLUDES messages; messages table no writer; only HITL-pause stashes them in metadata) + a latent multi-turn `main_seq` collision (resets to 0 per request). **User picked Option B**: the writer ALSO persists the user prompt (`user_message` row, persist-only) + seeds `main_seq` from `MAX(sequence_num)` (ordering fix) → the single `/events` source replays a complete user→agent→user→agent conversation. Frontend: click → fetch `/events` → sort → replay through the EXISTING `mergeEvent` + a NEW `user_message` case → render historical turns → continue. **ZERO new CSS** (mockup 51); `user_message` persist-only → NO wire (24)/codegen/migration. **Full-stack user-facing → drive-through MANDATORY**. CHANGE-093; NO design note (contract = design note 37 §4, amended with the user_message row))

[Plan](./sprint-57-126-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong + Prong 2.5) + Branch  ✅ DONE (catalogued in progress.md)

### 0.1 Three-prong Day-0 verify (against `main` HEAD `c8a338c8`)
- [x] **Prong 1 — path verify** ✅ all backend (`router.py:568/629/675`, `_persist_main_event`) + frontend (`chatService.ts:112`, `chatStore.ts:360/318/295`, `SessionList.tsx:58-115`, `useLoopEventStream.ts:79`) anchors exist; `fetchSessionEvents`/`loadSessionHistory`/`user_message` NOT defined; `CHANGE-093` free
- [x] **Prong 2 — content verify** (drift → progress.md):
  - [x] **D-user-message-not-persisted** ⚠️ THE finding — `loop_start/turn_start/llm_*` data carry NO user prompt; `state_data` EXCLUDES messages (`checkpointer.py:217` docstring); `messages` table no writer; only HITL-pause metadata (spike) → pure-FE replay loses user prompts → **Option B** (backend completes the writer)
  - [x] **D-multiturn-seq-collision** ⚠️ — `main_seq=0` per request (`router.py:675`) → ≥2-send sessions collide on `sequence_num` → seed from `MAX(sequence_num)`
  - [x] **D-state-excludes-messages** — Option C (interleave from `/state`) DEAD (no message list in state_data)
  - [x] **D-mergeEvent-input-shape** ✅ — `mergeEvent({type,data})`; reads only type/data (`parseSSEFrame` builds same)
  - [x] **D-no-get-in-factory** ✅ — `create((set)=>` → add `get` (idiomatic; `useLoopEventStream` already uses `useChatStore.getState()`)
  - [x] **D-continuation-route** ✅ — `send()` passes `session_id: sessionId` (`useLoopEventStream.ts:79`) → continuation free
  - [x] **D-fe-test-path** ✅ — `frontend/tests/unit/chat_v2/...` (NOT `.../features/...`); `SessionList.test.tsx` exists
  - [x] **D-resume-unpersisted** — resume path doesn't persist main events (pre-existing 57.125 gap) → OUT of scope
- [x] **Prong 2.5 — child-component-tree** ✅ — no re-point (only a click handler + store action change); turn components untouched → no shadcn/inline-style drift dragged in
- [x] **Prong 3 — schema** ✅ N/A (no migration — `message_events` + partitions exist; `user_message` is just an `event_type` string value, no DDL)
- [x] **D-baselines** ✅ Vitest 892 · mockup 51 · pytest 2711+5skip · wire 24 · mypy 0/370 · run_all 10/10 (from 57.125 merge)
- [x] **Catalog drift** ✅ progress.md Day-0 table written
- [x] **Go/no-go** ✅ scope shifted FE-only → full-stack (Option B) — user re-confirmed via 2 AskUserQuestions; plan + checklist revised

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-126-chatv2-session-history-replay-frontend` (from `main` `c8a338c8`) ✅

---

## Day 1 — Backend: complete the transcript foundation (US-1/2)

### 1.1 `_max_main_seq` helper + `main_seq` seed (US-2) ✅
- [x] **`router.py`** (EDIT): `_max_main_seq(db, tenant_id, session_id) -> int` (`select(func.coalesce(func.max(sequence_num),0)).where(session_id & tenant_id)`; `db is None`→0); `_stream_loop_events` `main_seq = await _max_main_seq(...) if main_transcript_on else 0` (replaced `=0`); +`from sqlalchemy import func, select` ✅
  - DoD: a 2nd send on the same session continues seq from MAX (no collision) ✅ (test_main_seq_continues_across_sends)

### 1.2 Persist `user_message` first (US-1) ✅
- [x] **`router.py`** (EDIT): before the `async for`, `if main_transcript_on and user_input: main_seq += 1; await _persist_main_event({"type":"user_message","data":{"text":user_input}}, ...)` (reuse 57.125 helper; persist-only — NO yield); MHist + Last Modified ✅
  - DoD: the send's FIRST `message_events` row is `user_message` with `data.text==user_input` ✅

### 1.3 Backend tests (US-7 part 1) ✅
- [x] **`test_main_transcript_persist.py`** (EDIT): updated 2 existing assertions (user_message row first, seq 1..4) + NEW `test_main_seq_continues_across_sends` (2-send → seq 1..8 monotonic, ORDER BY yields send-1 then send-2) ✅
  - Verify: `pytest tests/integration/api/test_main_transcript_persist.py -q` → **5 passed** ✅

### 1.4 Backend gate (partial) ✅
- [x] black 2 files unchanged · isort clean · flake8 clean · mypy `src` **0/370** · 5 writer tests passed ✅

---

## Day 2 — Frontend: service + replay action + user_message case (US-3/4) + click (US-5)

### 2.1 `fetchSessionEvents` service (US-3) ✅
- [x] **`chatService.ts`** (EDIT): `fetchSessionEvents(sessionId)` via `fetchWithAuth` (mirror `listSessions`); `PersistedSessionEvent` + `SessionEventsResponse` types; throw on non-2xx; return `.events`; MHist ✅

### 2.2 Store: `+get`, `loadSessionHistory`, `user_message` case (US-4) ✅
- [x] **`chatStore.ts`** (EDIT): factory `create((set, get) =>` + updated the `applyPivot` 57.69 comment (pure helper stays) ✅
- [x] **`loadSessionHistory(sessionId)`** + `ChatStoreState` signature: live guard · conversation-only reset (preserve `sessions`+`mode`, set both ids, `_turnCounter=0`) · race guard · `sort(sequence_num)` · `for ev: merge({type,data})` · catch→`errorMessage` ✅
- [x] **`user_message` mergeEvent case**: push `{role:"user", id, at, text:ev.data.text}` (replay-only); `mergeEvent` param widened to `LoopEvent | UserMessageEvent`; `rawEvents` narrowing cast (no consumer ripple) ✅
- [x] **`types.ts`** (EDIT): `UserMessageEvent = {type:"user_message"; data:{text:string}}` (hand-written, persist-only, NOT codegen; wire 24) ✅

### 2.3 `SessionItem` click rewire (US-5) ✅
- [x] **`SessionList.tsx`** (EDIT): onClick + keyboard → `void loadSessionHistory(session.id)` (subscribe action; highlight still works via action setting `activeSessionId`); NO CSS; MHist ✅

### 2.4 Frontend tests (US-7 part 2) ✅
- [x] **`chatStore.historyReplay.test.ts`** (NEW, 6 tests): replay→`[UserTurn,AgentTurn]` / out-of-order→sorted / live guard / race guard / reset preserves `sessions` / fetch error → errorMessage ✅
- [x] **`chatService.sessionEvents.test.ts`** (NEW, 2 tests): 200→events / non-2xx→throw ✅
- [x] **`SessionList.test.tsx`** (EDIT): +click→`loadSessionHistory(id)` spy; mock fetchSessionEvents for the existing click test ✅

### 2.5 Frontend gate (full) ✅
- [x] `npm run lint` exit 0 (no `--silent`) · `npm run build` ✅ (tsc) · Vitest **904 passed** (+9 net-new, 0 fail) · `diff styles-mockup.css` empty · mockup **51** · mypy `src` **0/370** · run_all **10/10** (24) · full pytest **2712+5skip** (+1) · codegen/migration UNTOUCHED ✅

---

## Day 3 — Drive-through (US-8) — real UI + real backend + real LLM (MANDATORY, multi-turn)

### 3.1 Clean restart (Risk Class E — `router.py` changed) ✅
- [x] :8000 had NO listener (clean — no orphan) → fresh no-`--reload` uvicorn `api.main:app` sole owner + "startup complete" + pricing loader wired; `MAIN_TRANSCRIPT_OBSERVER` default on; Vite :3007 NOT stopped ✅
  - DoD: `GET /sessions/{id}/events` shows `user_message` rows (seq 1 + 17) for `d5bd3950…` BEFORE the UI click ✅

### 3.2 Drive-through (MANDATORY — NOT gate-only) ✅
- [x] **multi-turn** real-LLM chat (Azure gpt-5.2, dev-login jamie/acme-prod): 2 messages → session `d5bd3950…`; `/events` = 34 events, 2 user_message rows, seq 1..34 monotonic (no collision) ✅
- [x] reload `/chat-v2` (fresh store, empty pane) → **click prior session** → COMPLETE replay: user-1+agent-1(Paris, v0.99)+user-2+agent-2(v0.98), correct order; row `[active]`; Loop "2 turns" w/ both user_message events; Inspector Turn populated; no crash/empty ✅ (`artifacts/sprint-57-126-replay-complete.png`)
- [x] **continue**: "Name one landmark in Paris" → Eiffel Tower streamed; `/events` = 51 events, 3 user_message rows, seq 1..51 monotonic → continued SAME `session_id` ✅ (`artifacts/sprint-57-126-replay-then-continue.png`)
- [x] per-control AP-4 walk + screenshots + observed-vs-intended → progress.md Day 3; **PASS** (real UI + real backend + real LLM) ✅

---

## Day 4 — CHANGE-093 + closeout

### 4.1 CHANGE-093 ✅
- [x] **`CHANGE-093-chatv2-session-history-replay.md`** (backend foundation completion + frontend replay + continuation + drive-through + arc-complete). NO design note (feature continuation; contract = design note 37 §4 amended with user_message) ✅

### 4.2 Closeout
- [x] retrospective.md Q1-Q7 + calibration (`chatv2-history-replay-fullstack` 0.60→0.85 re-pointed, ratio ~1.43; parent-direct) + progress.md final ✅
- [x] Final gate sweep: mypy `src` **0/370** · run_all **10/10** (24) · pytest **2712+5skip** (+1) · Vitest **904** (+9) · mockup **51** byte-identical · lint exit 0 · build ✅
- [x] Navigators: CLAUDE.md Current-Sprint + Last-Updated (minimal-touch) · MEMORY.md pointer + subfile `project_phase57_126_*` · next-phase-candidates (**CLOSED `AD-ChatV2-Session-History-Replay-Phase58`** — both halves shipped; 2-sprint arc COMPLETE; +2 new carryover ADs) · sprint-workflow matrix `chatv2-history-replay-fullstack` 0.85 row ✅
- [x] **Anti-pattern self-check** (retro Q5): AP-1 (reducer reused) / AP-3 (replay in store) / AP-4 (real complete replay — drive-through proven LIVE) / AP-6 (user_message persist-only, no speculative wire event / skeleton) / AP-11 (setActiveSessionId still used) → 0 violations; v2 lints 10/10 ✅
- [ ] PR (push + open) — **awaiting user confirm before `git push`** (destructive-confirm rule); CI → merge on green (gh-verified MERGED before main sync)
