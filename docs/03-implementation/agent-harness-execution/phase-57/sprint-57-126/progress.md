# Sprint 57.126 Progress — chat-v2 session history replay (arc slice 2/2: complete backend transcript foundation + frontend click→replay)

**Branch**: `feature/sprint-57-126-chatv2-session-history-replay-frontend` · **Base**: `main` `c8a338c8` (post-#300, 57.125)

---

## Day 0 — 2026-06-16 — Plan-vs-Repo 三-prong verify (the high-value day)

### Sequence
Plan + checklist drafted (frontend-only first) → 3 Explore sweeps (SessionList/service + chatStore/mergeEvent + mockup-fidelity) → branch created → formal Prong-2 content greps → **two findings flipped the sprint from frontend-only to full-stack** → 2 AskUserQuestions → plan + checklist rewritten for Option B.

### Drift findings (D-table)

| ID | Finding | Implication |
|----|---------|-------------|
| **D-user-message-not-persisted** ⚠️ | `loop_start.data`=`{session_id,request_id,active_skill}` / `turn_start`=`{turn_num}` / `llm_request`=`{model,tokens_in}` / `llm_response`=agent output — **no event carries the user prompt**. The initial prompt is a client-side `pushUserMessage` (`useLoopEventStream.ts:68`), never an SSE frame. `state_data` EXCLUDES messages (`checkpointer.py:217` docstring "Excludes messages"; `_deserialize:258` `messages=[] # caller rehydrates`). `messages` table has no writer (all `Message(...)` in `backend/src` are the Cat-3 dataclass, not `db.add` rows). Only the HITL deferred-pause branch stashes messages in `durable.metadata` (`loop.py:3594` "SPIKE shortcut") — not normal sessions. | A pure-FE replay of `/events` reconstructs agent turns with the user's questions MISSING. The 57.125 plan's premise ("state_data = LLM message list") was WRONG. → **Option B**: the writer must persist the user prompt. Scope flips FE-only → full-stack. |
| **D-multiturn-seq-collision** ⚠️ | `main_seq = 0` per request (`router.py:675`), incremented per event. Each send is a separate `_stream_loop_events` call → a session with ≥2 sends gets two row-ranges both starting at `sequence_num=1` → the reader's `ORDER BY sequence_num` interleaves them WRONGLY. 57.125's probe only tested a single send (16 events). | Latent 57.125 bug. This sprint's drive-through (multi-turn + continue) requires the fix: seed `main_seq` from `MAX(sequence_num)` for the MAIN session_id. |
| **D-state-excludes-messages** | `_serialize_state_for_db` (`checkpointer.py:217-240`) serializes only `durable`/`transient_summary`/`version_meta` — no message list. `platform_layer/resume/service.py:192` `messages_from_metadata(durable.metadata)` rehydrates, but metadata-messages are written only on HITL-deferred-pause. | Option C (interleave user prompts from `/state`) is DEAD — `/state` has no messages for normal sessions. |
| **D-mergeEvent-input-shape** ✅ | `mergeEvent(ev: LoopEvent) => set((s)=>switch(ev.type){...})` (`chatStore.ts:360`); reads only `ev.type` (switch) + `ev.data.*`. Live path: `parseSSEFrame` (`chatService.ts:261-281`) builds `{type, data}` → `consumeSSEStream` → `onEvent` → `mergeEvent`. | Replay = `mergeEvent({type: it.type, data: it.data})` (drop `sequence_num`/`timestamp_ms`). Exported + standalone-callable → loop-replay works. |
| **D-no-get-in-factory** ✅ | `create<ChatStoreState>((set) => ...)` (`chatStore.ts:318`) — only `set`, no `get` (57.69 comment `:284`). `useLoopEventStream` already reads live state via `useChatStore.getState()` (`:95/106/138`). | The async `loadSessionHistory` (live/race guards + calling `mergeEvent`) needs `get` → add `get` to the factory (idiomatic; update the `applyPivot` comment, keep the helper pure for the shared `agent_handoff` `s`-only case). |
| **D-partial-reset-template** ✅ | `applyPivot` (`:295-316`) clears turns/status/totalTurns/stopReason/errorMessage/approvals/verifications/subagents/spans/memoryOps + sets `sessionId`+`activeSessionId`, preserves `sessions`+`rawEvents`+`mode`. But it's handoff-specific (sets a banner, keeps rawEvents). | `loadSessionHistory`'s reset models on it but `handoffBanner:null`, `rawEvents:[]`, `currentModel:null`, `_turnCounter=0`. Don't reuse `reset()` (it nukes `sessions`/`activeSessionId`). |
| **D-continuation-route** ✅ | `send()` (`useLoopEventStream.ts:65-99`) `...(sessionId ? {session_id: sessionId} : {})` (`:79`), `sessionId` from `useChatStore((s)=>s.sessionId)` (`:57`). | Continuation is automatic once `loadSessionHistory` sets `sessionId` (same mechanism as live multi-turn). US-6 ≈ free. |
| **D-fe-test-path** ✅ | chat_v2 tests at `frontend/tests/unit/chat_v2/...` (NOT `.../features/chat_v2/...` — the first glob guess returned 0). `SessionList.test.tsx` + `chatStore.*.test.ts` + `chatService.parseSSEFrame.test.ts` exist there. | New tests: `frontend/tests/unit/chat_v2/chatStore.historyReplay.test.ts` + `chatService.sessionEvents.test.ts`; EDIT `components/SessionList.test.tsx`. Plan §4 paths corrected. |
| **D-resume-unpersisted** | the resume path (`router.py:1175` `loop.resume`, `_stream_resume_events`) does NOT call `_persist_main_event`. | Pre-existing 57.125 gap (resume continuations unpersisted). OUT of scope (§9); a session that ended via resume replays up to the pause. Follow-on AD. |

### user_message ordering insight (why Option B is clean)
`_persist_main_event(payload, ...)` takes a `{"type","data"}` dict → persist `{"type":"user_message","data":{"text":user_input}}` via the EXISTING helper (no new helper). Persisted as the send's FIRST row (lowest seq) → on replay the UserTurn is pushed BEFORE `loop_start` → `loop_start`'s active_skill stamping (`chatStore.ts:374-377`) finds it → the skill chip reconstructs too. `_stream_loop_events` has both `session_id` (`:632`) and `user_input` (`:635`) at entry → both the seed query and the user_message persist are trivial.

### Decisions
- **AskUserQuestion #1** (user prompts missing from `/events`): user picked the hybrid (`/events` + `/state` interleave).
- Deeper verify (D-state-excludes-messages) proved the hybrid non-viable (no message source). **AskUserQuestion #2**: user picked **Option B** — complete the backend writer (persist the user prompt; the cleanest single-source path).
- Scope: FE-only → **full-stack** (small backend writer completion + the multi-turn ordering fix + the FE replay). Plan + checklist rewritten. NEW class `chatv2-history-replay-fullstack` 0.60.

### Go/no-go
GO — direction re-confirmed by the user (Option B). Backend change is small (reuse `_persist_main_event` + a `MAX(seq)` seed). No migration (count 24, mockup 51 unchanged).

---

## Day 1 — 2026-06-16 — Backend: complete the transcript foundation

- **`_max_main_seq` helper** (`router.py`): `select(func.coalesce(func.max(MessageEvent.sequence_num), 0)).where(session_id & tenant_id)`; `db None`→0. +`from sqlalchemy import func, select`.
- **`_stream_loop_events`**: `main_seq = await _max_main_seq(...) if main_transcript_on else 0` (multi-turn seed); then `if main_transcript_on and user_input: main_seq += 1; _persist_main_event({"type":"user_message","data":{"text":user_input}}, ...)` (persist-only, before the `async for`, reuses the 57.125 helper). MHist + Last Modified.
- **Tests** (`test_main_transcript_persist.py`): updated 2 existing assertions (user_message row first → seq 1..4; main/sidechain seq {1,2,3,4}) + NEW `test_main_seq_continues_across_sends` (2 sends same session → seq 1..8 monotonic, ORDER BY yields send-1 then send-2).
- **Gate**: black 2 files unchanged · isort/flake8 clean · mypy `src` **0/370** · writer tests **5 passed** (1.37s).
- Insight realized: `user_message` row at seq 1 (before loop_start) → on replay the UserTurn is pushed first → loop_start's active_skill stamping finds it (chip reconstructs). `_persist_main_event` reused as-is (takes a `{type,data}` dict).

## Day 2 — 2026-06-16 — Frontend: service + replay action + user_message case + click + tests

- **`chatService.ts`**: `fetchSessionEvents(id)` (mirror `listSessions` `fetchWithAuth`) + `PersistedSessionEvent` / `SessionEventsResponse` types. MHist.
- **`types.ts`**: `UserMessageEvent = {type:"user_message"; data:{text:string}}` — hand-written persist-only (NOT in the codegen wire union / KNOWN_LOOP_EVENT_TYPES; wire count 24).
- **`chatStore.ts`**: factory `create((set, get) =>` (added `get`; updated the 57.69 `applyPivot` comment). `mergeEvent` param widened to `LoopEvent | UserMessageEvent` (contravariant → live `onEvent` still type-checks); `rawEvents` line `ev as LoopEvent` narrowing cast (rawEvents stays `LoopEvent[]` — no `LoopVisualizer` ripple). NEW `user_message` case (push UserTurn). NEW `loadSessionHistory` action: live guard → conversation-only reset (preserve `sessions`+`mode`, set both ids, `_turnCounter=0`) → `fetchSessionEvents` → race guard → `sort(sequence_num)` → `merge({type,data})` loop → catch sets `errorMessage`.
- **`SessionList.tsx`**: `SessionItem` onClick + keyboard → `void loadSessionHistory(session.id)` (was `setActiveSessionId`). Highlight still works (the action sets `activeSessionId`). NO CSS. MHist.
- **Tests**: `chatStore.historyReplay.test.ts` (6) + `chatService.sessionEvents.test.ts` (2) + `SessionList.test.tsx` (+1 trigger test; mocked `fetchSessionEvents` for the existing click test). One fix: `mockFetch.mockReset()` in beforeEach (the vi.mock factory fn accumulates call history across tests; `restoreAllMocks` doesn't reset it → the live-guard "not called" assertion saw prior tests' calls).
- **Gate**: `npm run lint` exit **0** · `npm run build` ✅ (tsc — the widened union + casts type-check) · Vitest **904 passed** (+9; 0 fail) · `diff styles-mockup.css` empty · mockup **51** byte-identical · mypy `src` **0/370** · run_all **10/10** (`check_event_schema_sync` green → wire 24 intact) · full backend pytest **2712 passed / 5 skipped** (+1) · NO codegen/migration.

## Day 3 — 2026-06-16 — Drive-through (real UI + real backend + real Azure gpt-5.2) — PASS

**Clean restart** (Risk Class E): :8000 had NO listener (clean — no orphan); started a fresh no-`--reload` uvicorn `api.main:app` (sole owner, "startup complete", pricing loader wired, `MAIN_TRANSCRIPT_OBSERVER` default on). Vite :3007 (node 31616) NOT stopped. (A stray `python -m http.server 8090` from Sprint 57.121 left running — not mine, not interfering — left alone per Karpathy §3.)

**Flow** (Playwright MCP, dev-login jamie@acme.com / acme-prod, real Azure gpt-5.2):
1. **Multi-turn real chat** (2 sends): "What is the capital of France?" → *"The capital of France is Paris."* (verification 0.99) + "And roughly what is its population?" → *"I'm missing what 'it' refers to…"* (verification 0.98). Session `d5bd3950-8c17-4c56-82c4-62019b342c03`. (The 2nd answer being context-less is a PRE-EXISTING live-multi-turn issue — the backend doesn't persist conversation messages for the live loop; NOT a 57.126 concern, and the replay faithfully reproduces what the user saw.)
2. **Backend probe** (`GET /events` via the page's auth): **34 events, 200**; **2 `user_message` rows** (seq 1 + 17, exact prompt texts); **sequence_num monotonic 1..34** — NO multi-turn collision (the `main_seq` MAX-seed fix works; send-1 = 1-16, send-2 = 17-34, NOT both from 1). Both sends keyed by the SAME session_id → continuation routed.
3. **Replay** (the user-facing payoff): reloaded `/chat-v2` (fresh store — conversation pane empty, "Type a message…" hint) → the session list reloaded with `d5bd3950` (下午2:09) → **clicked it** → the COMPLETE conversation replayed: user-1 "capital of France" + agent-1 "Paris" (verification 0.99) + user-2 "population" + agent-2 "missing it" (verification 0.98); the row went `[active]`; the Loop visualizer showed "Loop (2 turns)" with BOTH `user_message` events in the stream; the Inspector Turn tab populated (trace_id 773569…, tokens.in 2,433, block sequence). **The user prompts reappeared** — the user_message persistence + replay reducer worked end-to-end. AP-4 clear (real data, real render, no dead control / fixture / mislabel). Screenshot `artifacts/sprint-57-126-replay-complete.png`.
4. **Continuation**: sent "Name one famous landmark in Paris." in the loaded session → *"…Eiffel Tower…"* streamed. `GET /events` → **51 events**, **3 `user_message` rows** (the follow-up is the 3rd), **seq monotonic 1..51** — the follow-up CONTINUED the SAME session `d5bd3950` (not a new one), and `main_seq` stayed monotonic across the replay→continue boundary. Screenshot `artifacts/sprint-57-126-replay-then-continue.png`.

**Verdict**: drive-through PASS (NOT gate-only). US-1/2/5/6/8 verified live; US-3/4/7 verified by Vitest + the replay render.

## Day 4 — 2026-06-16 — CHANGE-093 + closeout

- **CHANGE-093** written (backend completion + frontend replay + continuation + drive-through + arc-complete). NO design note (feature continuation; contract = design note 37 §4 amended with user_message).
- **retrospective.md** Q1-Q7 + calibration (`chatv2-history-replay-fullstack` 0.60→**0.85 re-pointed**, ratio ~1.43 over; ceremony-not-code-accelerated).
- **Navigators**: CLAUDE.md Current-Sprint + Last-Updated (minimal-touch) · MEMORY.md pointer + subfile · next-phase-candidates (CLOSED `AD-ChatV2-Session-History-Replay-Phase58` + 2 new carryovers: `AD-ChatV2-Resume-Transcript-Persistence` 🟢, `AD-ChatV2-Live-MultiTurn-Context` 🟡) · sprint-workflow.md calibration matrix row.
- **Final gate**: mypy `src` 0/370 · run_all 10/10 · pytest 2712+5skip · Vitest 904 · mockup 51 · lint exit 0 · build ✅. Drive-through PASS (Day 3).
- **Anti-pattern self-check**: AP-1/3/4/6/11 → 0 violations; v2 lints 10/10.
- PR: awaiting user `git push` confirm.
