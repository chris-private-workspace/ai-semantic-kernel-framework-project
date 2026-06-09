# Sprint 57.95 Plan — Cat 11 Subagent SSE Relay (node-level; child no longer headless in the Tree)

**Purpose**: Sprint 57.94 made FORK run a REAL child agent loop, but its Day-0 + drive-through both confirmed the child runs **headless** in the UI: the chat-v2 Inspector "Tree" tab shows "no subagents spawned this session" even when a subagent ran (the 2026-06-06 drive-through audit recorded this as `AD-Subagent-Child-Event-SSE-Relay`). This sprint closes that gap at the **node level** (Scope A, user-selected 2026-06-09): wire the `event_emitter` side-channel so the dispatcher's `SubagentSpawned` / `SubagentCompleted` events reach the SSE stream and the Tree shows the subagent node (mode / summary / tokens / running→completed). The decisive Day-0 finding (read-only探查): the ENTIRE relay chain already exists end-to-end and is unused for ONE reason — `make_chat_subagent_dispatcher` (`_category_factories.py:224`) does not pass an `event_emitter` to `DefaultSubagentDispatcher`, so `_emit_safely` no-ops on the chat path. `SubagentSpawned` already carries `parent_session_id` (`events.py:353`); `sse.py:306-326` already serializes both events to `subagent_spawned` / `subagent_completed`; `chatStore.ts:638-743` already handles both cases; `InspectorTree.tsx` already renders any non-empty `subagents` slice. So **NO `LoopEvent` contract change, NO new event type, NO frontend change** is needed for node-level relay — the carryover's premise ("needs a `LoopEvent` `parent_session_id`/`depth` field") is true ONLY for the larger child-turn-stream nesting (Scope B, deferred). The real engineering is the **timing bridge**: subagent events are emitted while the parent loop is `await`ing the `task_spawn` tool (its generator is blocked, cannot `yield`), so a router-owned **buffer** collects them and `_stream_loop_events` drains it (serialize → SSE frame) before each loop event + after the loop ends — a single-asyncio-task, no-concurrency design (lower-risk than an `asyncio.Queue` + background-task merge). This is a **feature-continuation** sprint (wiring an existing-but-unwired Cat 11 → Cat 12 emitter), NOT a new-domain spike → record = **CHANGE-062** (no design-note extract). **Drive-through** (real UI + real backend + real Azure): a chat-v2 request that makes the agent `task_spawn` a sub-task → the Inspector Tree now shows the subagent node populated (mode FORK + real summary + tokens), where before it said "no subagents" — the exact gap the 2026-06-06 audit flagged.

**Category / Scope**: Cat 11 (Subagent — relay `SubagentSpawned`/`SubagentCompleted` on the chat path) × Cat 12 (Observability — the emitter is the SSE relay of subagent lifecycle events). Backend-only wiring: `make_chat_subagent_dispatcher` threads `event_emitter`; `build_real_llm_handler` + `build_handler` thread `subagent_event_emitter`; the router builds the buffer + emitter closure; `_stream_loop_events` drains the buffer into SSE frames. **`loop.py` UNCHANGED**; **no `LoopEvent`/contract change**; **no frontend change** (the consumer is already wired). Phase 57.95

**Created**: 2026-06-09
**Status**: Draft (scope below; code execution gated on Day-0 GO — Day-0 head-start already run, findings in §0)
**Source**: `next-phase-candidates.md` Sprint 57.94 Carryover ("`AD-Subagent-Child-Event-SSE-Relay` 🟡 — surfaced by the drive-through; the chat `DefaultSubagentDispatcher` is built WITHOUT an `event_emitter` … the Inspector Tree tab shows 'no subagents' even though one ran; the child is HEADLESS") + the 2026-06-06 drive-through audit (`drive-through-20260606/audit.md`) + AskUserQuestion 2026-06-09 (direction = **Child 上 UI (SSE-relay)**; scope = **Scope A — node-level relay**, child turn-stream nesting deferred).

> **Modification History**
> - 2026-06-09: Initial creation — wire the chat subagent event_emitter (node-level SSE relay); router-owned buffer drained by _stream_loop_events; no LoopEvent contract / no frontend change; Scope B (child turn-stream nesting) deferred

---

## 0. Background

Sprint 57.94 (地基 A payoff Slice 1) made Cat 11 FORK run a REAL child `AgentLoopImpl` (multi-turn, tool-capable) instead of a single-shot `chat()`. Its design note `20-subagent-child-loop-design.md §5` recorded a deferred invariant: the child runs **headless** — "the chat dispatcher has no `event_emitter` → Inspector Tree shows 'no subagents'". The 2026-06-06 drive-through audit independently flagged the same gap (`AD-Subagent-Child-Event-SSE-Relay`). This sprint closes it at the node level.

### Ground truth (Day-0 head-start — this plan's Day-0 verify, 3 read-only探查 passes + 1 Explore agent map)

Re-confirmed with file:line anchors:

- **The relay chain already exists end-to-end; ONE link is unwired.** `DefaultSubagentDispatcher.__init__` ALREADY accepts `event_emitter: SubagentEventEmitter | None = None` (`dispatcher.py:109`, stored `:134`) and emits via `_emit_safely` (`:136-143`) on every `spawn()` (SubagentSpawned, `:189-196`) + `_track_and_emit()` (SubagentCompleted, `:224-249`). The slot has existed since Sprint 57.12 (US-1) but the chat path never filled it. The ONLY gap: `make_chat_subagent_dispatcher` (`_category_factories.py:197-227`) returns `DefaultSubagentDispatcher(chat_client=…, child_loop_factory=…)` **without** `event_emitter` → `_emit_safely` returns immediately (`:138-139`) → no subagent events on the chat SSE.
- **No `LoopEvent` contract change for node-level relay.** `SubagentSpawned` (`events.py:348-353`) already carries `subagent_id`, `mode`, `parent_session_id`; `SubagentCompleted` (`:355-359`) already carries `subagent_id`, `summary`, `tokens_used`. `serialize_loop_event` already maps both to wire types `subagent_spawned` / `subagent_completed` (`sse.py:306-326`). The `LoopEvent` BASE lacking `parent_session_id`/`depth` (`events.py:56`) only blocks relaying the child's INNER events (LLMResponded/ToolCall) tagged by subagent — that is Scope B (deferred), not this sprint.
- **The frontend consumer is already wired.** `chatStore.ts:638-693` handles `case "subagent_spawned"` (creates a `SubagentNode`, status `running`); `:695-743` handles `case "subagent_completed"` (status `completed`, summary, tokensUsed). `InspectorTree.tsx:176` reads `s.subagents`; `:178-197` renders the empty state "no subagents spawned this session" only when the slice is empty; `buildTree()` (`:73-95`) renders any node. **No frontend change needed** — populate the slice and the Tree renders.
- **The timing bridge is the real work (D1).** Subagent events are emitted while the parent loop is `await`ing the `task_spawn` tool inside `_run_turns` — the parent loop generator is blocked, cannot `yield` them. `_stream_loop_events` (`router.py:341-402`) drives `async for event in run_with_verification(agent_loop=loop, …)` (`:384`), serializing each event (`:393`) and yielding an SSE frame (`:402`). To interleave subagent events, a **router-owned buffer** (`list[LoopEvent]`) is filled by the emitter closure and drained by `_stream_loop_events` (serialize → frame) before each loop event + after the loop ends. Single asyncio task (the emitter append + the drain both run in `_stream_loop_events`'s task) → no concurrency hazard; lower-risk than an `asyncio.Queue` + background-task merge (Explore "Option A", simplified).
- **The buffer must live in the router function scope (D3).** The dispatcher is built inside `build_handler` (`router.py:222`, called BEFORE the stream) but the SSE sink is in `_stream_loop_events` (the `StreamingResponse` generator, `router.py:314`). The shared buffer is created in the router handler function (which wraps both): the emitter closure (passed DOWN into `build_handler` → `build_real_llm_handler` → `make_chat_subagent_dispatcher`) appends to it; `_stream_loop_events` (passed the same buffer) drains it.
- **`build_handler` is the dispatch layer (D2).** The router calls `build_handler(req.mode, req.message, …, tracer=tracer)` (`router.py:222-239`), which routes echo vs real_llm. The emitter threads through `build_handler` → `build_real_llm_handler` (`handler.py:242`); the echo handler (`handler.py:…-239`, no subagent dispatcher) ignores it.
- **This is a feature-continuation, not a spike.** The Cat 11 → Cat 12 SSE relay machinery exists; this wires an unwired link. Per `sprint-workflow.md §Step 5.5`, NO design-note extract — `progress.md` + `retrospective.md` + CHANGE-062 only.

---

## 1. Sprint Goal

Make a FORK/AS_TOOL subagent visible in the chat-v2 Inspector "Tree" tab at the node level: (1) `make_chat_subagent_dispatcher` gains an `event_emitter` param threaded into `DefaultSubagentDispatcher`; (2) `build_real_llm_handler` + the `build_handler` dispatch gain a `subagent_event_emitter` param threaded down; (3) the chat router handler creates a `subagent_event_buffer: list[LoopEvent]` + an async emitter closure that appends to it, passes the emitter into `build_handler`, and passes the buffer into `_stream_loop_events`; (4) `_stream_loop_events` drains the buffer (serialize → SSE frame, mirroring the existing loop-event serialize/skip handling) before each loop event + after the loop ends. **`loop.py` UNCHANGED; no `LoopEvent` contract change (SubagentSpawned already carries parent_session_id); no frontend change (chatStore + InspectorTree already consume the events).** Converted/new unit tests assert the wiring (factory threads the emitter) + the buffer-drain (a buffered SubagentSpawned → a `subagent_spawned` SSE frame) + no-regression on the non-spawn path; existing Sprint 57.12 dispatcher emission tests stay green. **Drive-through**: a chat-v2 `task_spawn` → the Inspector Tree shows the subagent node populated (was "no subagents"). Out of scope: Scope B (relaying the child's INNER turn-by-turn LoopEvents — needs a `LoopEvent` `parent_session_id`/`depth` field + ForkExecutor forwarding + frontend nested render); a `depth` field; TEAMMATE/HANDOFF real loops; child checkpoint/transcript.

---

## 2. User Stories

- **US-1 (wire the chat subagent emitter)** — As the platform, I want the chat subagent dispatcher to carry an `event_emitter` so `SubagentSpawned`/`SubagentCompleted` are no longer silently dropped, so subagent lifecycle reaches the SSE stream. → `make_chat_subagent_dispatcher(event_emitter=…)` → `DefaultSubagentDispatcher(event_emitter=…)`; `build_real_llm_handler` + `build_handler` thread `subagent_event_emitter` down.
- **US-2 (timing bridge — buffer drain)** — As the SSE stream, I want subagent events emitted during the parent's `task_spawn` tool-await to be interleaved into the stream, since the loop generator is blocked at that moment. → a router-owned `subagent_event_buffer` filled by the emitter closure; `_stream_loop_events` drains it (serialize → frame) before each loop event + after the loop ends; single asyncio task (no concurrency).
- **US-3 (Tree shows the node — no frontend change)** — As the user, I want the Inspector "Tree" tab to show the subagent node (mode / summary / tokens, running→completed) instead of "no subagents". → the frontend already consumes `subagent_spawned`/`subagent_completed` (`chatStore.ts`) and renders any non-empty `subagents` slice (`InspectorTree.tsx`); wiring the backend emitter populates it — zero frontend change.
- **US-4 (no contract change / no regression)** — As the loop/contract maintainer, I want NO `LoopEvent` contract change and NO behavior change on the non-spawn path. → `SubagentSpawned` already carries `parent_session_id`; no new event type; the buffer is drained only when non-empty; a chat run that never spawns yields a byte-identical SSE stream; Sprint 57.12 dispatcher emission tests stay green; `loop.py` diff = 0.
- **US-5 (drive-through acceptance — Tree populated)** — As the user, I want to actually SEE the subagent in the Tree end-to-end. → drive-through: a chat-v2 request that makes the agent `task_spawn` a sub-task (real UI + real backend + real Azure) → the Inspector Tree shows the subagent node populated (mode + real summary + tokens) → screenshot + observed-vs-intended diff (before: "no subagents"; after: node shown) in progress.md.

---

## 3. Technical Specifications

### 3.0 Architecture (the one unwired link + the timing bridge)

```
TODAY (headless)                                  AFTER (node-level relay)
  dispatcher = DefaultSubagentDispatcher(           router handler:
    chat_client, child_loop_factory)                  subagent_event_buffer: list[LoopEvent] = []
  # event_emitter = None → _emit_safely no-ops        async def _relay(ev): subagent_event_buffer.append(ev)
                                                       loop, vreg = build_handler(mode, …,
  parent loop awaits task_spawn:                          subagent_event_emitter=_relay)   # threads to dispatcher
    dispatcher.spawn() → _emit_safely(Spawned)         StreamingResponse(_stream_loop_events(loop, …,
       → emitter is None → dropped                         subagent_event_buffer=subagent_event_buffer))
    child runs → _emit_safely(Completed) → dropped
                                                     parent loop awaits task_spawn:
  Inspector Tree: "no subagents"                       dispatcher.spawn() → _emit_safely(Spawned)
                                                          → _relay() → buffer.append(Spawned)
                                                       child runs → _emit_safely(Completed) → buffer.append(Completed)

                                                     _stream_loop_events drain (per loop event + at end):
                                                       for frame in _drain_subagent_frames(buffer): yield frame
                                                       # serialize_loop_event → format_sse_message (same as loop events)

                                                     Inspector Tree: FORK node — running→completed — summary — N tokens
```

The buffer-append (emitter) and the buffer-drain (`_stream_loop_events`) both run in the SAME asyncio task (the stream generator's task) — the emitter fires synchronously during the loop's tool-await, which is inside the generator's `__anext__` driven by `_stream_loop_events`. No queue, no background task, no lock.

### 3.1 `event_emitter` threading (US-1)
- `_category_factories.py` `make_chat_subagent_dispatcher` — add `event_emitter: SubagentEventEmitter | None = None` (keyword-only, after `child_loop_factory`); pass to `DefaultSubagentDispatcher(chat_client=…, child_loop_factory=…, event_emitter=event_emitter)`. Import `SubagentEventEmitter` + `LoopEvent` from the Cat 11 / contracts module (Day-1 confirm the import path — `SubagentEventEmitter` is defined in `subagent/dispatcher.py:90`; the type may need re-export or a direct import).
- `handler.py` `build_real_llm_handler` — add `subagent_event_emitter: "SubagentEventEmitter | None" = None`; pass into `make_chat_subagent_dispatcher(chat_client, child_loop_factory=_make_child_loop, event_emitter=subagent_event_emitter)` (`:332-334`). Only the `session_id is not None` branch builds the dispatcher (the emitter is harmlessly ignored when no dispatcher is built).
- `handler.py` `build_handler` (the mode dispatch) — add `subagent_event_emitter` passthrough to `build_real_llm_handler`; the echo branch ignores it (no subagent dispatcher). Day-1 confirm `build_handler`'s exact signature + that echo simply drops the kwarg.

### 3.2 Router buffer + emitter closure (US-2/US-3)
- In the chat router handler function (the one at `router.py:222` building the handler + `:314` returning the StreamingResponse): create `subagent_event_buffer: list[LoopEvent] = []` BEFORE `build_handler`; define `async def _relay_subagent_event(ev: LoopEvent) -> None: subagent_event_buffer.append(ev)`; pass `subagent_event_emitter=_relay_subagent_event` into `build_handler(...)`; pass `subagent_event_buffer=subagent_event_buffer` into `_stream_loop_events(...)`.
- The emitter signature matches `SubagentEventEmitter = Callable[[LoopEvent], Awaitable[None]]` (`dispatcher.py:90`); the append is sync inside an async function (no await) → atomic w.r.t. the event loop.

### 3.3 `_stream_loop_events` buffer drain (US-2/US-4)
- Add param `subagent_event_buffer: list[LoopEvent] | None = None` to `_stream_loop_events`.
- Add a module-level helper `_drain_subagent_frames(buffer: list[LoopEvent] | None) -> list[bytes]`: while the buffer is non-empty, `pop(0)` → `serialize_loop_event(ev)` (mirror the existing `NotImplementedError` skip + `payload is None` skip at `:394-401`) → `format_sse_message(payload["type"], payload["data"])`; return the frames. (A standalone helper because an async generator cannot delegate `yield`s to a nested function.)
- In `_stream_loop_events`, inside the `async for event in run_with_verification(...)` body, at the TOP (before serializing the current loop event): `for frame in _drain_subagent_frames(subagent_event_buffer): yield frame`. After the `async for` completes (before the finalize/registry cleanup): drain once more (events appended during the final await / StopAsyncIteration).
- Ordering: subagent events appear right before the next loop event after the tool-await (e.g. `tool_call_request`, `subagent_spawned`, `subagent_completed`, `tool_call_result`) — semantically correct (the subagent ran as part of the tool). Tree rendering is order-insensitive (the store maps by `subagent_id`).
- Guard: when `subagent_event_buffer` is None/empty, the helper returns `[]` → zero behavior change on the non-spawn path (US-4).

### 3.4 What is explicitly NOT done (Scope B / separate slices)
- **Child INNER turn-stream nesting** (the Tree expanding to show the child's per-turn TAO loop) — needs a `LoopEvent` base `parent_session_id`/`depth` (or a wrapper event) + `ForkExecutor` forwarding every child event + frontend nested render + `chatStore` routing by `subagent_id`. Scope B → stays `AD-Subagent-Child-Event-SSE-Relay` (the node-level part closes; the turn-stream part is the remaining open).
- **`depth` field on events** — not needed for node-level (a single FORK node has parent_session_id = the chat session; the Tree's local `depth` in `InspectorTree.tsx:73-95` is computed).
- **TEAMMATE/HANDOFF real loops, child checkpoint/transcript, failure policies** — unrelated, deferred per 57.94 carryover.

### 3.5 Lint / neutrality / doc single-source
- `check_llm_sdk_leak` 0 (no adapter/SDK touched). `check_ap1_pipeline_disguise` green (no loop driving added — the drain is a plain serialize-and-yield of buffered events). AP-4 green (this REMOVES a Potemkin — the headless subagent now surfaces; the opposite of a structural-slot-without-content). `category-boundaries`: the wiring stays in the chat composition layer (`api/v1/chat/`) + Cat 11 factory; the `SubagentEventEmitter`/`LoopEvent` types are Cat 11/contracts (no new cross-category ABC). **17.md**: confirm whether the Cat 11 section needs a note that the chat path now wires the `SubagentEventEmitter` SSE relay — likely NO contract change (the type + the dispatcher param pre-exist since 57.12; this is composition wiring). CHANGE-062 records it. **No design note** (feature-continuation, not a spike — `sprint-workflow.md §Step 5.5`).

### 3.6 Validation (US-1..US-5)
- **mypy `src/ --strict` 0**; `run_all` 10/10; `black`/`isort`/`flake8 src/ tests/` clean (CI-equivalent scope, the 57.92 lesson).
- **pytest**:
  - **NEW/extended** `_category_factories` test: `make_chat_subagent_dispatcher(chat_client, event_emitter=sentinel)` → the returned dispatcher's `_event_emitter is sentinel` (threading).
  - **NEW** `_stream_loop_events` buffer-drain test: drive `_stream_loop_events` with a fake loop generator that yields a couple of loop events + a pre-filled `subagent_event_buffer` containing a `SubagentSpawned` + `SubagentCompleted`; assert the SSE byte output contains a `subagent_spawned` frame + a `subagent_completed` frame interleaved with the loop frames (mirror any existing `_stream_loop_events` / SSE router test harness; Day-1 locate it).
  - **NEW** no-regression test: an empty buffer → the SSE output is byte-identical to today (no subagent frames).
  - **Existing** Sprint 57.12 dispatcher emission tests (`test_subagent_sse_emission.py` or similar) + 57.94 child-loop tests UNCHANGED + green (the emission mechanism is unchanged; only the chat wiring is added).
  - Full backend suite green (NET delta documented — expect +N new wiring tests, 0 deletions).
- **Drive-through** (US-5): real UI + real backend + real Azure — a chat-v2 request that makes the agent `task_spawn` a sub-task → open the Inspector "Tree" tab → confirm the subagent node is shown (mode FORK + a real summary + tokens, running→completed) where before it said "no subagents"; screenshot + observed-vs-intended diff in progress.md. (Per CLAUDE.md §Drive-Through Acceptance — "the Tree actually shows the node a human can see" is the leg-specific assertion; backend-trace alone is gate/probe, not drive-through.)

---

## 4. File Change List

| File | Change |
|------|--------|
| `backend/src/api/v1/chat/_category_factories.py` | **EDIT** — `make_chat_subagent_dispatcher` gains `event_emitter: SubagentEventEmitter \| None = None`; passes it to `DefaultSubagentDispatcher`. Import `SubagentEventEmitter` (+ `LoopEvent` if needed for the annotation). MHist 1-line. |
| `backend/src/api/v1/chat/handler.py` | **EDIT** — `build_real_llm_handler` gains `subagent_event_emitter`; threads into `make_chat_subagent_dispatcher(...)`. `build_handler` dispatch gains the passthrough (echo ignores). MHist 1-line. |
| `backend/src/api/v1/chat/router.py` | **EDIT** — the chat handler fn builds `subagent_event_buffer` + the `_relay_subagent_event` emitter closure, passes the emitter into `build_handler` + the buffer into `_stream_loop_events`; add `_drain_subagent_frames` helper + drain it in `_stream_loop_events` (per loop event + at end) + the new `subagent_event_buffer` param. MHist 1-line. |
| `backend/tests/.../chat/test_category_factories*.py` (Day-1 locate / NEW) | **EDIT/NEW** — `make_chat_subagent_dispatcher` threads `event_emitter` (dispatcher `_event_emitter is sentinel`). |
| `backend/tests/.../chat/test_stream_loop_events*.py` or the SSE router test (Day-1 locate / NEW) | **NEW** — buffer-drain: a pre-filled buffer → `subagent_spawned`/`subagent_completed` SSE frames interleaved; empty buffer → byte-identical (no-regression). |
| `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-95-plan.md` + `-checklist.md` | **NEW** — this plan + checklist |
| `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-95/progress.md` + `retrospective.md` | **NEW** — Day 0-N progress + retro |
| `claudedocs/4-changes/feature-changes/CHANGE-062-subagent-sse-relay-node-level.md` | **NEW** — the change record (wire the chat subagent emitter; buffer-drain bridge; Tree shows the node). |
| `docs/03-implementation/agent-harness-planning/17-cross-category-interfaces.md` | **EDIT (conditional)** — Cat 11 §: note the chat path now wires the `SubagentEventEmitter` SSE relay (composition; ABC + type unchanged). Day-3 decide if a note is warranted. |

**NOT in this list (unchanged)**: `loop.py` · `dispatcher.py` (the emitter slot + emission already exist since 57.12) · `events.py` (no contract change — SubagentSpawned already carries parent_session_id) · `sse.py` (already serializes both events) · any `frontend/` file (chatStore + InspectorTree already consume) · no DB/migration · no adapter/SDK · no `/resume`/ResumeService · no design note (feature-continuation).

---

## 5. Acceptance Criteria

- The chat subagent dispatcher carries a real `event_emitter` (threaded `router → build_handler → build_real_llm_handler → make_chat_subagent_dispatcher → DefaultSubagentDispatcher`); `SubagentSpawned`/`SubagentCompleted` are no longer dropped on the chat path (US-1).
- Subagent events emitted during the parent's `task_spawn` tool-await are interleaved into the SSE stream via the router-owned buffer drained by `_stream_loop_events` (per loop event + at end); single asyncio task, no concurrency (US-2).
- The Inspector "Tree" tab shows the subagent node (mode/summary/tokens, running→completed) — NO frontend change (the consumer is already wired) (US-3).
- NO `LoopEvent` contract change (SubagentSpawned already carries parent_session_id); `loop.py` diff = 0; an empty buffer → byte-identical non-spawn SSE stream; Sprint 57.12 emission tests + 57.94 child-loop tests green (US-4).
- `mypy --strict src/` 0; `run_all` 10/10 (LLM SDK leak 0; AP-1; AP-4 — removes a Potemkin); `black`/`isort`/`flake8 src/ tests/` clean; full backend pytest green (NET delta documented); CHANGE-062 written; 17.md note if warranted.
- **Drive-through PASS**: real UI + real backend + real Azure — a chat-v2 `task_spawn` → the Inspector Tree shows the subagent node populated (was "no subagents"); screenshot + observed-vs-intended diff. (No "gate-only" claimed as drive-through.)

---

## 6. Deliverables

- [ ] `make_chat_subagent_dispatcher` threads `event_emitter` → `DefaultSubagentDispatcher` (US-1)
- [ ] `build_real_llm_handler` + `build_handler` thread `subagent_event_emitter` (echo ignores) (US-1)
- [ ] Router builds `subagent_event_buffer` + `_relay_subagent_event` closure; passes emitter into `build_handler` + buffer into `_stream_loop_events` (US-2)
- [ ] `_drain_subagent_frames` helper + drain in `_stream_loop_events` (per loop event + at end) + new buffer param (US-2/US-4)
- [ ] Tests: factory threads emitter / buffer-drain emits `subagent_spawned`+`subagent_completed` frames / empty buffer byte-identical (no-regression) / 57.12 + 57.94 tests green (US-1..US-4)
- [ ] mypy 0 + run_all 10/10 + format chain `flake8 src/ tests/` (validation)
- [ ] **drive-through PASS** (real UI + real backend + real Azure; Tree shows the subagent node; screenshot + before/after diff) (US-5)
- [ ] CHANGE-062 + progress.md + retrospective.md (+ 17.md note if warranted; NO design note — feature-continuation)
- [ ] commit (Day 0-N) — push + PR user-authorized

---

## 7. Workload Calibration

Scope class: **`subagent-sse-relay-wiring` (NEW, 0.55 mid-band) — 1st data point, pending 2-3 sprint validation**. Pure backend composition wiring (thread an existing-but-unwired emitter + a buffer-drain bridge), NOT the `subagent-child-loop-spike` build shape (57.94, which constructed a child loop) and NOT a `loop.py` refactor. The work splits: emitter threading across 3 files (`_category_factories` + `handler` `build_real_llm_handler` + `build_handler` dispatch) (~1 hr) / router buffer + emitter closure + passthrough (~0.75 hr) / `_drain_subagent_frames` + the `_stream_loop_events` drain integration (~1.25 hr; the merge timing is the only subtle part) / tests (factory threading + buffer-drain SSE-frame + no-regression) (~2 hr) / drive-through (spawn a subagent + screenshot the Tree populated) (~1.5 hr) / docs (CHANGE-062 + progress + retro; NO design note) (~1 hr). Dominant costs = tests + drive-through. **Agent-delegated: no** (parent-direct) — small sprint; the async-ordering correctness of the buffer-drain + the drive-through (a UI Tree-populated screenshot, the exact 2026-06-06 audit gap) are parent verification work. Future Cat 11 wiring follow-ons MAY be agent-delegated once this pattern lands. `agent_factor = 1.0`; does NOT extend the AgentDelegated-WallClock streak.

> Bottom-up est ~7.5 hr → class-calibrated commit ~4 hr (mult 0.55). **Agent-delegated: no.**

If Day-1 shows the wiring ripples wider than the 3 backend files + tests (e.g. the emitter param cannot thread cleanly through `build_handler`; `_stream_loop_events` has no clean test harness so the buffer-drain needs a fixture rebuild; the buffer-drain ordering breaks an existing SSE-stream test; the emitter type import creates a Cat boundary issue), STOP and re-scope rather than rush.

---

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| **`SubagentEventEmitter` import / Cat boundary** | The type is defined in `subagent/dispatcher.py:90`; `_category_factories.py` already imports from `agent_harness.subagent`. Day-1 confirm a clean import (or re-export from the Cat 11 `__init__`); `LoopEvent` for the buffer annotation is in `_contracts/events.py` (already imported in `router.py` for the existing serialize path). |
| **`build_handler` passthrough (echo branch)** | Day-1 read `build_handler`'s exact signature; add `subagent_event_emitter` kwarg passed to `build_real_llm_handler`; the echo branch (no subagent dispatcher) simply does not forward it — confirm it accepts+drops the kwarg or branch on mode. |
| **Buffer-drain ordering breaks an existing SSE test** | The drain only adds frames when the buffer is non-empty; non-spawn runs are byte-identical (a no-regression test guards it). If an existing `_stream_loop_events` test asserts an exact frame sequence, it never spawns → unaffected. |
| **`_stream_loop_events` test harness** | Day-1 locate the existing SSE/router test (it drives `_stream_loop_events` or the endpoint with a fake/mock loop). If none drives `_stream_loop_events` directly, build a minimal fake async loop generator fixture + a pre-filled buffer — assert the serialized frames. |
| **Subagent events emitted from a child asyncio task** | `dispatcher.spawn` creates the subagent `asyncio.Task`; emission (`_emit_safely`) runs from whichever task calls it, but the append (`buffer.append`) is atomic (no await between) and the drain runs in `_stream_loop_events`'s task when it regains control — deterministic regardless of which task appended. No lock needed. |
| **AP-1 flags the drain as a pipeline** | The drain is a plain serialize-and-yield of pre-collected events (no loop driving, no `for step in steps` orchestration); if the detector mis-flags, it is a serialize loop like the existing loop-event yield — mirror the existing handling. |
| **Double-emit / dual-block in chatStore** | `chatStore.ts:638-693` also appends a `SubagentForkBlock` to the active turn (dual-emit) — that is existing frontend behavior, unchanged; node-level relay simply makes both fire. No frontend change. |
| **Risk Class E (stale `--reload` backend)** | Clean restart before the drive-through (kill stale uvicorn reloader+worker procs; verify :8000 OWNER is the fresh PID) — the emitter wiring is startup-built; a stale process runs the unwired dispatcher and the Tree would (wrongly) still say "no subagents". Bit 57.91/92/93/94. |
| **Risk Class C (test isolation)** | The buffer is per-request (created in the router fn); no module singleton. Run the full suite; existing chat conftest reset fixtures cover the dispatcher. |
| **Over-engineering (Scope creep into Scope B)** | Node-level only: relay `SubagentSpawned`/`SubagentCompleted`, NOT the child's inner events. No `LoopEvent` field, no ForkExecutor change, no frontend change (Karpathy §2/§3). |
| **Smuggling unrelated change** | The diff is exactly the 3 backend chat files (emitter threading + buffer-drain) + tests + docs. `loop.py`/`dispatcher.py`/`events.py`/`sse.py`/frontend diff = 0. |
| **LLM-neutrality** | No adapter/SDK touched; `check_llm_sdk_leak` gates. |

---

## 9. Out of Scope (this sprint; → separate slices / ADs)

- **Scope B — child INNER turn-stream nesting** (the Tree expanding to show the child's per-turn TAO loop) — needs a `LoopEvent` base `parent_session_id`/`depth` (or wrapper event) + `ForkExecutor` forwarding every child event + frontend nested render + `chatStore` routing by `subagent_id`. Stays `AD-Subagent-Child-Event-SSE-Relay` (node-level closes; turn-stream remains).
- **`depth` field on events** — not needed for node-level.
- **`AD-Subagent-Child-Span-Nesting`** (task_spawn passes `trace_context=None` → child span not explicitly parented) — separate 🟢; orthogonal to SSE relay.
- **TEAMMATE / HANDOFF real loops · `HandoffService`** — separate slices.
- **Recursion depth > 1 · parentUuid transcript chain · child checkpoint · child-internal governance · failure policies** — deferred per 57.94 carryover.
