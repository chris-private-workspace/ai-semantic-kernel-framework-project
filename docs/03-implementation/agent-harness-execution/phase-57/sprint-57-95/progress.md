# Sprint 57.95 Progress — Cat 11 Subagent SSE Relay (node-level)

**Branch**: `feature/sprint-57-95-subagent-sse-relay` (from `main` `8c6a2250`)
**Plan / Checklist**: `sprint-57-95-{plan,checklist}.md`
**Record**: CHANGE-062 (feature-continuation — NO design note)

---

## Day 0 — Plan-vs-Repo Verify (2026-06-09)

### Prong 1 — path verify (3 read-only passes + 1 Explore agent map)
All anchors confirmed (see checklist 0.1 Prong 1). The headline: the relay chain exists end-to-end and is unused for ONE reason — `make_chat_subagent_dispatcher` (`_category_factories.py:224`) returns the dispatcher WITHOUT `event_emitter`, so `DefaultSubagentDispatcher._emit_safely` (`dispatcher.py:138-139`) returns immediately on the chat path.

### Prong 2 — content verify
- The `event_emitter` slot on `DefaultSubagentDispatcher.__init__` (`dispatcher.py:109`) + the `spawn`/`_track_and_emit` emission (`:189-196` / `:224-249`) have existed since Sprint 57.12 — only the chat composition never filled the slot.
- `SubagentSpawned` (`events.py:348-353`) already carries `parent_session_id`; `serialize_loop_event` already maps both subagent events (`sse.py:306-326`); `chatStore.ts:638-743` + `InspectorTree.tsx` already consume them. → **no `LoopEvent` contract change, no frontend change** for node-level relay.

### Prong 2.5 — drift findings
- **D1**: subagent events are emitted while the parent loop awaits the `task_spawn` tool (loop generator blocked) → cannot be `yield`ed by the loop → a router-owned buffer drained by `_stream_loop_events` is the bridge.
- **D2**: `build_handler` (`router.py:222`) is the echo/real_llm dispatch → the emitter threads through it → `build_real_llm_handler`; the echo handler builds no subagent dispatcher → ignores the arg.
- **D3**: the buffer must live in the router handler fn scope (the dispatcher is built in `build_handler` BEFORE the stream; the SSE sink is in `_stream_loop_events`).
- **D4 (scope-reduction drift vs the 57.94 carryover)**: the Sprint 57.94 design note §5 + `next-phase-candidates.md` carryover stated node visibility "needs a `LoopEvent` `parent_session_id`/`depth` field". **Day-0 corrects this**: NODE-level relay needs ONLY the emitter wired — `SubagentSpawned` (a `LoopEvent` *subclass*) already carries `parent_session_id`; the base-class field is a Scope-B (child inner turn-stream) concern. **Scope is SMALLER than the carryover implied; 0 contract change.** Not a blocker → GO.

### Prong 3 — schema verify
N/A (no DB/migration/ORM; no `LoopEvent` contract; no new event type).

### Baseline + harness
- Baseline = `8c6a2250` (57.94 merged; CI-green 2271 / mypy 0/351 / run_all 10/10).
- Harness located: `_StubLoop` + `_consume` drain in `test_chat_sla_recording.py:36-61` (drives `_stream_loop_events` with deps=None) → mirrored for the buffer-drain test.
- **Go/no-go = GO** (0% scope change; D4 is a reduction).

---

## Day 1 — code (2026-06-09)

3 files edited (`loop.py` UNCHANGED; `dispatcher.py`/`events.py`/`sse.py`/frontend UNCHANGED):

- **`_category_factories.py`** (+8): `make_chat_subagent_dispatcher` gains `event_emitter` (kw-only), threads to `DefaultSubagentDispatcher`; `SubagentEventEmitter` TYPE_CHECKING import; MHist.
- **`handler.py`** (+15): `build_real_llm_handler` + `build_handler` gain `subagent_event_emitter`; threaded to `make_chat_subagent_dispatcher(event_emitter=…)`; echo path ignores; MHist.
- **`router.py`** (+62/-3): NEW `_drain_subagent_frames(buffer) -> list[bytes]` helper (serialize + frame, mirroring the loop-event NotImplementedError/None skip); `_stream_loop_events` gains `subagent_event_buffer` param + drains it at the TOP of each `async for` iteration + once after the loop (defensive); the chat handler fn builds `subagent_event_buffer` + the `_relay_subagent_event` closure, passes the emitter into `build_handler` + the buffer into `_stream_loop_events`; `LoopEvent` added to the runtime import; MHist.

**Design**: buffer-drain (single asyncio task — the emitter append + the drain both run in `_stream_loop_events`'s task), NOT an `asyncio.Queue` + background-task merge → no lock, no concurrency hazard. Ordering: subagent frames precede the next loop event after the tool-await (e.g. `tool_call_request`, `subagent_spawned`, `subagent_completed`, `tool_call_result`).

- mypy `src --strict`: **0/351** ✅

---

## Day 2 — tests (2026-06-09)

NEW `backend/tests/unit/api/v1/chat/test_subagent_sse_relay.py` (6 tests):
- `make_chat_subagent_dispatcher` threads `event_emitter` (+ default-None).
- `_drain_subagent_frames`: empty/None → `[]`; Spawned+Completed → 2 frames + buffer emptied.
- `_stream_loop_events` relays a buffered spawn (`_SpawningStubLoop`) → SSE bytes contain `subagent_spawned`+`subagent_completed`+summary, before `loop_end`, buffer drained.
- no-regression: `_PlainStubLoop` + empty buffer → no `subagent_*` frames.

Existing green (UNCHANGED): 57.12 `test_subagent_sse_emission.py` (8) + 57.94 `test_subagent_child_loop.py`/`test_fork`/`test_as_tool`. `loop.py` diff = 0 confirmed.

---

## Day 3.1 — full gate (2026-06-09)

- **pytest**: **2277 passed, 4 skipped** (baseline 2271 → **+6** = the new tests; 0 deletions, 0 regressions). The 2 warnings are pre-existing FakeRedis GC artifacts.
- **mypy `src --strict`**: 0/351.
- **run_all**: **10/10** (AP-1 — the `for _frame in _drain_subagent_frames(...)` drain is NOT flagged as a pipeline; `check_event_schema_sync` green — no event schema drift; `check_cross_category_import` green; `check_llm_sdk_leak` 0).
- **format chain**: `black`/`isort`/`flake8 src tests` clean.
- **diff scope**: 3 chat files only (`_category_factories` +8 / `handler` +15 / `router` +62/-3); `loop.py` empty.

---

## Day 3.2 — drive-through (2026-06-09) — **PASS**

Real UI (`:3007`) + real backend (fresh PID 50200) + real Azure gpt-5.2. dev-login jamie@acme.com / acme-prod / real_llm mode.

### Risk Class E — clean restart
The stale 57.94 backend (reloader 14580 → spawn-worker 38308, pre-57.95 code) owned `:8000`. Killed BOTH python procs (never node), verified `:8000` FREE, `dev.py start backend` → fresh **PID 50200** owns `:8000` (`/health` responds 401 = server up + tenant middleware active). The wiring is startup-built; a stale process would still drop the events → the drive MUST run on the fresh PID.

### Observed vs intended

| | Intended | Observed |
|---|---|---|
| **BEFORE** (Tree tab, no spawn) | "no subagents" empty state | ✅ "**no subagents spawned this session**" (`tree-1-before-empty.png`) |
| Prompt | agent calls `task_spawn` → child uses `echo_tool` | ✅ `task_spawn(mode=fork)` → child echoed; loop 2 turns, gpt-5.2 |
| **Inspector → Tree** (AFTER) | subagent node shown (mode / summary / tokens / completed) | ✅ **"Subagent tree · live"** → node `1ff0167a…` · root · **completed** · **Mode fork** · Depth 0 · **Tokens 3,692** · summary **"subagent node is visible"** (`tree-3-populated.png`) |
| **Inspector → Trace** (SSE proof) | `subagent_spawned` + `subagent_completed` frames | ✅ `subagent_spawned  mode=fork parent=95b9f45f-…` + `subagent_completed  subagent node is visible · 3692 tokens` |
| Child result (task_spawn output) | real summary + tokens | ✅ `{success:true, summary:"subagent node is visible", tokens_used:3692}` |

**Why this proves the relay (not the tool result)**: the `subagent_spawned` / `subagent_completed` frames in the Trace are the **dispatcher's** lifecycle events — emitted only via the `event_emitter` this sprint wired. Before 57.95 they were dropped by `_emit_safely` (no-op), so the Tree showed "no subagents" + the Trace had no subagent frames. Their presence + the populated Tree node = the node-level relay works end-to-end.

**Minor observation (pre-existing, out of scope)**: the INLINE `SubagentForkBlock` in the conversation turn shows `0t` while the Tree node + the `subagent_completed` frame correctly show 3,692 tokens. The inline fork-block token field is a separate frontend dual-emit display detail (not the Tree node this sprint targets); the relay + the Tree are correct. Logged for a future frontend touch, not a 57.95 regression (the inline block is unchanged by this backend-only sprint).

Artifacts: `artifacts/sprint-57-95-tree-{1-before-empty,3-populated}.png` + `artifacts/sprint-57-95-after-snapshot.yml`.

## Day 3.3 — CHANGE-062 + 17.md (2026-06-09)
- CHANGE-062 written.
- 17.md: a 1-line Cat 11 note (the chat composition now wires the pre-existing `SubagentEventEmitter` for the SSE relay; ABC + type unchanged).

## Day 4 — closeout (in progress)
