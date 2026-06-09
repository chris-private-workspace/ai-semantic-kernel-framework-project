# Sprint 57.96 Plan — Cat 11 Subagent child turn-stream nesting (Scope B; the Tree node expands to show the child's per-turn TAO loop)

**Purpose**: Sprint 57.94 made FORK run a REAL child agent loop; Sprint 57.95 made that subagent visible in the chat-v2 Inspector "Tree" tab as a **single collapsed node** (mode / summary / tokens, running→completed) by wiring the dispatcher's `event_emitter` at the node level. The remaining half of `AD-Subagent-Child-Event-SSE-Relay` is **Scope B**: expand that node so it shows the child's per-turn TAO loop (the child's own `LLMResponded` / tool-call events) nested underneath. The Day-0 Explore map corrected the carryover's premises with file:line anchors: (1) the `LoopEvent` base (`_contracts/events.py:56`) has only `event_id`/`timestamp`/`trace_context` — child events carry NO identifier linking them to their child session → **a tag is genuinely needed**; (2) `ForkExecutor._drive()` (`fork.py:102-114`) already receives every child event while draining but **discards all except `LLMResponded` (final answer) + `LoopCompleted` (tokens)** → forwarding is genuinely needed; (3) the chat router relay (`_relay_subagent_event` + `_drain_subagent_frames`, `router.py:237-385`) is **already generic over any `LoopEvent`** and `sse.py` already serializes the standard child event types → **router.py needs ZERO change**, only a serializer for the new wrapper; (4) `InspectorTree.tsx` `buildTree`/`NodeRow` (`:73-95`/`:132-173`) is **already recursive** (renders nested children, MAX_DEPTH=5) → the render scaffold exists, but `SubagentNode` (`features/subagent/types.ts:62-73`) has no per-turn field and the store has no case routing child events by `subagent_id`. Two design decisions locked 2026-06-09 (AskUserQuestion): the relay mechanism = a **Wrapper event** `SubagentChildEvent(subagent_id, inner: LoopEvent)` (minimal blast radius — does NOT touch the `LoopEvent` base that ~30 subclasses inherit, does NOT touch the existing per-type serializers); the depth = a **TAO essentials subset** (`TurnStarted` + `LLMResponded` + `ToolCallRequested` + `ToolCallExecuted`/`Failed` only — keeps the Tree high-signal, excludes `LLMRequested`/`PromptBuilt`/`MemoryAccessed`/`Span*`/`Metric*`/`Checkpoint` noise). The wrapper IS a `LoopEvent`, so the SAME 57.95 emitter + the SAME already-generic router buffer-drain relay it for free — the new backend work is the wrapper type + one SSE serializer + `ForkExecutor` forwarding the TAO subset (tagged with the dispatcher's `subagent_id`); the new frontend work is a `childEvents` field on `SubagentNode` + a `subagent_child_event` store case routing by `subagent_id` + a per-turn render row under the node. This is a **feature-continuation** of the validated Cat 11 arc (57.94 child loop → 57.95 node visible → 57.96 node expands), NOT a new-domain spike → record = **CHANGE-063** (no design-note extract), BUT the new `SubagentChildEvent` event type is a contract addition → **17.md registration is mandatory** (not conditional like 57.95) + `check_event_schema_sync` must stay green (backend event ↔ frontend wire type sync). **Drive-through** (real UI + real backend + real Azure): a chat-v2 request that makes the agent `task_spawn` a sub-task that itself calls a tool → the Inspector Tree subagent node, when expanded, shows the child's per-turn TAO events (the child's `LLMResponded` + the tool call), where 57.95 showed only the collapsed node.

**Category / Scope**: Cat 11 (Subagent — forward the child loop's TAO events tagged by `subagent_id`) × Cat 12 (Observability — the wrapper is the SSE relay of the child's inner lifecycle). Backend: a new `SubagentChildEvent` wrapper event (`_contracts/events.py`); one SSE serializer (`sse.py`); `ForkExecutor` forwards the TAO subset (`fork.py`); the dispatcher threads its `_event_emitter` + `subagent_id` into the executor (`dispatcher.py`). Frontend: `SubagentNode.childEvents` (`features/subagent/types.ts`); a `subagent_child_event` store case (`chatStore.ts`); a per-turn render row under the node (`InspectorTree.tsx`). **`loop.py` UNCHANGED**; **`router.py` UNCHANGED** (relay already generic); **`LoopEvent` base UNCHANGED** (wrapper, not a base field). Phase 57.96

**Created**: 2026-06-09
**Status**: Draft (scope below; code execution gated on Day-0 GO — Day-0 Explore map already run, findings in §0)
**Source**: `next-phase-candidates.md` Sprint 57.95 Carryover ("**Scope B — child INNER turn-stream nesting** 🟡 — the remaining half of `AD-Subagent-Child-Event-SSE-Relay` — to EXPAND [the node] to show the child's per-turn TAO loop, relay the child's INNER `LoopEvent`s. Needs a `LoopEvent` base `parent_session_id`/`depth` field (or a wrapper event) + `ForkExecutor` forwarding every child event + frontend nested render + `chatStore` routing by `subagent_id`") + AskUserQuestion 2026-06-09 (Theme B → Scope B child turn-stream; relay mechanism = **Wrapper event**; depth = **TAO essentials subset**).

> **Modification History**
> - 2026-06-09: Initial creation — child turn-stream nesting via SubagentChildEvent wrapper (TAO subset); ForkExecutor forwards tagged child events; frontend childEvents + subagent_child_event store case + per-turn render; loop.py/router.py/LoopEvent-base UNCHANGED

---

## 0. Background

Sprint 57.94 (地基 A payoff Slice 1) made Cat 11 FORK run a REAL child `AgentLoopImpl`; Sprint 57.95 (node-level relay) made that subagent visible in the Inspector "Tree" as a single collapsed node by wiring the dispatcher's `event_emitter` + a router-owned buffer-drain bridge. The 57.95 retro + the carryover recorded the remaining open: the node is collapsed; the child's per-turn TAO loop (its `LLMResponded`/tool calls) is not surfaced. This sprint closes that — Scope B of `AD-Subagent-Child-Event-SSE-Relay`.

### Ground truth (Day-0 head-start — this plan's Day-0 verify, 1 Explore agent map + anchors)

Re-confirmed with file:line anchors (Explore "Scope B premise check"):

- **The wrapper-tag is genuinely needed (premise 1 CONFIRMED-NEEDED).** `LoopEvent` base (`_contracts/events.py:56`) carries only `event_id`/`timestamp`/`trace_context`. `parent_session_id` exists ONLY on `SubagentSpawned` (`:349`) + `AgentHandoff`; `depth` exists nowhere. The child's TAO events (`LLMResponded` `:92`, `ToolCallRequested` `:183`, `ToolCallExecuted` `:193`, `ToolCallFailed` `:201`, `TurnStarted` `:73`) carry NO `session_id`/`subagent_id` → indistinguishable from parent-loop events by content. The locked decision is a **wrapper event** `SubagentChildEvent(subagent_id, inner)` (NOT a base field — minimal blast radius; the base + ~30 subclasses + every existing serializer stay untouched).
- **`ForkExecutor` forwarding is genuinely needed (premise 2 CONFIRMED-NEEDED).** `fork.py:102-114` `_drive()` does `async for ev in child.run(...)` and acts ONLY on `LLMResponded` (final answer) + `LoopCompleted` (tokens); every other child event is silently discarded. `ForkExecutor` holds no emitter. The work: thread the dispatcher's `_event_emitter` + the spawn `subagent_id` into the executor; in the drain loop, for each child event in the TAO subset, `await emitter(SubagentChildEvent(subagent_id=…, inner=ev))`.
- **The router relay needs ZERO change (premise — router already generic).** `_relay_subagent_event` (`router.py:237-238`) appends ANY `LoopEvent` to `subagent_event_buffer`; `_drain_subagent_frames` (`:363-385`) serializes ANY event via `serialize_loop_event` (skips `NotImplementedError`/`None`). Since `SubagentChildEvent` IS a `LoopEvent`, the 57.95 emitter + buffer + drain relay it for free — IF `sse.py` can serialize it. So the only backend SSE work is ONE new serializer branch for `SubagentChildEvent`.
- **`sse.py` already serializes the inner TAO types.** `LLMResponded` (`:153-171`), tool events, etc. already have serializer branches; the fallthrough raises `NotImplementedError` (`:429`). The new `SubagentChildEvent` branch produces `{type: "subagent_child_event", data: {subagent_id, inner: serialize_loop_event(inner)}}` — recursively reusing the existing inner serializers (the TAO subset is all serializable; the ForkExecutor filter guarantees it).
- **The frontend render scaffold exists; the data model + routing do not (premises 3 PARTIALLY-EXISTS + 4 CONFIRMED-NEEDED).** `InspectorTree.tsx` `buildTree`/`NodeRow` (`:73-95`/`:132-173`, MAX_DEPTH=5, recurse `:164-170`) already renders nested subagent children. BUT `SubagentNode` (`features/subagent/types.ts:62-73`) has no `childEvents`/`turns` field; `chatStore.ts` (`:136` slice, `:638-692` spawned, `:695-743` completed) has NO case routing child loop events by `subagent_id`. The work: add `childEvents` to `SubagentNode`; a `case "subagent_child_event"` that finds the node by `subagent_id` and appends a parsed per-turn entry; a render row under `NodeRow` showing the child's turns (turn N: LLMResponded text / tool call).
- **The inline `0t` is NOT in scope and is NOT a token bug.** `SubagentForkBlock.tsx:88` shows `{a.turns}t` — an integer TURN count (`SubagentEntry.turns`), a separate inline chat-bubble component distinct from `InspectorTree`. The 57.95 carryover mislabeled it "0t token-display"; it is unrelated to Scope B (the Tree). Out of scope (stays a 🟢 frontend nuance).
- **This is a feature-continuation with a contract addition.** The Cat 11 arc is validated (57.94 + 57.95); this extends it. NO design-note extract (`sprint-workflow.md §Step 5.5`) — `progress.md` + `retrospective.md` + CHANGE-063. BUT a NEW event type is a contract change → **17.md registration mandatory** + `check_event_schema_sync` green (Day-1 locate what the lint reads).

---

## 1. Sprint Goal

Expand the chat-v2 Inspector "Tree" subagent node so it shows the child's per-turn TAO loop: (1) a NEW `SubagentChildEvent(subagent_id, inner: LoopEvent)` wrapper event in `_contracts/events.py` + a `subagent_child_event` SSE serializer in `sse.py` (recursively serializing the inner via existing per-type branches); (2) `ForkExecutor._drive` threads the dispatcher's `_event_emitter` + the spawn `subagent_id` and, during the drain, forwards the TAO subset (`TurnStarted`/`LLMResponded`/`ToolCallRequested`/`ToolCallExecuted`/`Failed`) wrapped in `SubagentChildEvent`; the dispatcher passes `self._event_emitter` + `subagent_id` into the executor; (3) frontend `SubagentNode` gains a `childEvents` array, `chatStore` gains a `case "subagent_child_event"` routing by `subagent_id`, and `InspectorTree.NodeRow` renders the per-turn child events under the node. **`loop.py` UNCHANGED; `router.py` UNCHANGED (relay already generic); `LoopEvent` base UNCHANGED (wrapper, not a base field); the 57.95 spawn/completed node relay UNCHANGED.** Converted/new tests assert the wrapper serialize round-trip + the ForkExecutor TAO-subset forwarding (tagged + filtered) + the store routing + no-regression on the non-spawn path; existing 57.12 emission + 57.94 child-loop + 57.95 relay tests stay green; `check_event_schema_sync` green. **Drive-through**: a chat-v2 `task_spawn` whose child calls a tool → the Tree node, expanded, shows the child's per-turn TAO (LLMResponded + the tool call) where 57.95 showed only the collapsed node. Out of scope: recursion depth > 1 (child-of-child); `LLMRequested`/`PromptBuilt`/`MemoryAccessed`/`Span*`/`Metric*`/`Checkpoint` events; the inline `SubagentForkBlock` `{a.turns}t` count; TEAMMATE/HANDOFF real loops; child checkpoint/transcript/governance.

---

## 2. User Stories

- **US-1 (the wrapper event + serializer)** — As the contract/observability maintainer, I want a `SubagentChildEvent(subagent_id, inner: LoopEvent)` wrapper + one SSE serializer, so a child's inner event can be relayed tagged by subagent WITHOUT touching the `LoopEvent` base or the ~30 existing serializers. → NEW `SubagentChildEvent` in `_contracts/events.py`; `serialize_loop_event(SubagentChildEvent)` → `{type: "subagent_child_event", data: {subagent_id, inner: serialize_loop_event(inner)}}`; `check_event_schema_sync` updated both sides.
- **US-2 (ForkExecutor forwards the TAO subset)** — As Cat 11, I want the FORK child's per-turn TAO events forwarded (tagged with the spawn `subagent_id`) instead of discarded, so the child's loop reaches the SSE stream. → `ForkExecutor._drive` gains the dispatcher's `_event_emitter` + `subagent_id`; in the drain, for each `ev` whose type ∈ {`TurnStarted`,`LLMResponded`,`ToolCallRequested`,`ToolCallExecuted`,`ToolCallFailed`}, `await emitter(SubagentChildEvent(subagent_id=…, inner=ev))`; the dispatcher threads `self._event_emitter` + `subagent_id` into the executor. The existing `LLMResponded`→final-answer + `LoopCompleted`→tokens handling is preserved.
- **US-3 (the Tree node expands — frontend)** — As the user, I want the Inspector "Tree" subagent node to expand and show the child's per-turn TAO loop. → `SubagentNode.childEvents: ChildTurnEvent[]`; `chatStore` `case "subagent_child_event"` finds the node by `subagent_id` and appends a parsed entry; `InspectorTree.NodeRow` renders the per-turn child rows under the node (turn / LLMResponded snippet / tool call). The 57.95 collapsed-node render is preserved (this adds the expansion).
- **US-4 (no contract-base / router / loop change; no regression)** — As the loop/contract maintainer, I want the `LoopEvent` BASE, `router.py`, `loop.py`, and the 57.95 spawn/completed relay all UNCHANGED. → the wrapper is a subclass (base untouched); the router buffer-drain is already generic (zero change); `loop.py` diff = 0; a chat run whose subagent emits no TAO subset (or never spawns) yields a byte-identical SSE stream vs 57.95; 57.12 + 57.94 + 57.95 tests green; `check_event_schema_sync` green.
- **US-5 (drive-through acceptance — the node expands to child turns)** — As the user, I want to actually SEE the child's per-turn TAO under the node end-to-end. → drive-through: a chat-v2 request that makes the agent `task_spawn` a sub-task whose child calls a tool (real UI + real backend + real Azure) → expand the subagent node in the Tree → confirm the child's per-turn TAO events render (the child's LLMResponded + the tool call) → screenshot + observed-vs-intended diff (before: 57.95 collapsed node; after: node expands to child turns) in progress.md.

---

## 3. Technical Specifications

### 3.0 Architecture (the wrapper rides the existing 57.95 relay; only the executor + frontend grow)

```
57.95 (collapsed node)                              57.96 (node expands to child TAO)
  dispatcher.spawn() → emit SubagentSpawned           dispatcher.spawn() → emit SubagentSpawned   (UNCHANGED)
     → _relay → buffer → _stream drains → SSE             + pass self._event_emitter + subagent_id INTO executor
  ForkExecutor._drive:                                ForkExecutor._drive (gains emitter + subagent_id):
    async for ev in child.run(...):                     async for ev in child.run(...):
      if LLMResponded: final_answer = ev.content          if type(ev) in TAO_SUBSET:
      elif LoopCompleted: tokens = ev.total_tokens           await emitter(SubagentChildEvent(subagent_id, inner=ev))
      # everything else DISCARDED                          if LLMResponded: final_answer = ev.content   (preserved)
                                                           elif LoopCompleted: tokens = ev.total_tokens  (preserved)
  dispatcher.emit SubagentCompleted                   dispatcher.emit SubagentCompleted             (UNCHANGED)

  router relay (generic, UNCHANGED): _relay_subagent_event appends ANY LoopEvent → _drain_subagent_frames
     → serialize_loop_event → SSE frame   ← SubagentChildEvent rides this for FREE (it IS a LoopEvent)

  sse.py: + NEW branch serialize_loop_event(SubagentChildEvent)
            → {type:"subagent_child_event", data:{subagent_id, inner: serialize_loop_event(inner)}}

  frontend:
    SubagentNode + childEvents: ChildTurnEvent[]
    chatStore + case "subagent_child_event": byId[subagent_id].childEvents.push(parse(inner))
    InspectorTree.NodeRow + per-turn child rows under the node (turn / LLMResponded / tool call)

  Inspector Tree: FORK node ▸ expand ▸  turn 1: LLMResponded "…" → echo_tool(…)  → turn 2: LLMResponded "done"
```

The wrapper rides the SAME single-asyncio-task buffer-drain the 57.95 spawn/completed events ride (the emitter append + the drain both run in `_stream_loop_events`'s task). No new queue, no lock, no router change.

### 3.1 The `SubagentChildEvent` wrapper + serializer (US-1)
- `_contracts/events.py` — NEW `@dataclass` `SubagentChildEvent(LoopEvent)` with `subagent_id: str` + `inner: LoopEvent`. Placed near `SubagentSpawned`/`SubagentCompleted` (`:349-359`). It inherits the base `event_id`/`timestamp`/`trace_context`. (Day-1 confirm the dataclass `kw_only`/default conventions used by the neighbours.)
- `sse.py` — NEW branch in `serialize_loop_event`: `isinstance(ev, SubagentChildEvent)` → `inner = serialize_loop_event(ev.inner)`; if `inner` is `None`/raises `NotImplementedError`, propagate-skip (the ForkExecutor TAO filter guarantees serializable inners, so this is defensive); else `{"type": "subagent_child_event", "data": {"subagent_id": ev.subagent_id, "inner": inner}}`. Place the branch with the other subagent branches (`:306-326`).
- `check_event_schema_sync` — Day-1 locate what it reads (a shared event-type ↔ wire-type registry / generated map). Add `SubagentChildEvent` ↔ `subagent_child_event` both sides so the lint stays green (this is the mandatory contract-sync step for a new event type).

### 3.2 `ForkExecutor` forwards the TAO subset (US-2)
- `subagent/modes/fork.py` — `ForkExecutor` (the `_drive` coroutine `:102-114`) gains access to an `event_emitter: SubagentEventEmitter | None` + the `subagent_id: str` (Day-1 confirm whether via `__init__` or the `spawn`/`run` call — the Explore noted `__init__` accepts no emitter today). Define module-level `_TAO_CHILD_EVENT_TYPES = (TurnStarted, LLMResponded, ToolCallRequested, ToolCallExecuted, ToolCallFailed)`. In the drain loop, BEFORE the existing `LLMResponded`/`LoopCompleted` handling: `if emitter is not None and isinstance(ev, _TAO_CHILD_EVENT_TYPES): await emitter(SubagentChildEvent(subagent_id=subagent_id, inner=ev))`. The existing final-answer/token extraction is preserved unchanged.
- `subagent/dispatcher.py` — when constructing/invoking `ForkExecutor` (Day-1 confirm the exact call site), pass `event_emitter=self._event_emitter` + the `subagent_id` it just used for `SubagentSpawned` (`:189-196`) so the child events route to the SAME node the frontend created on spawn. The emitter is `self._event_emitter` (already stored `:134`), so when the chat path wired it (57.95) the child events flow; when no emitter (other paths), `_drive` simply doesn't forward (guard `emitter is not None`).
- **AS_TOOL**: 57.94 noted AS_TOOL "inherits the real loop FREE" via the same `ForkExecutor`. Day-1 confirm AS_TOOL shares this executor path → it inherits the child-event forwarding too (in scope, same code). TEAMMATE/HANDOFF (single-shot) do NOT (out of scope).

### 3.3 Frontend: `childEvents` + store case + per-turn render (US-3)
- `features/subagent/types.ts` — `SubagentNode` (`:62-73`) gains `childEvents: ChildTurnEvent[]` (NEW interface: `{ kind: string; turn?: number; text?: string; toolName?: string; toolCallId?: string }` — a minimal projection of the TAO subset; Day-1 finalize fields from the wire `inner.data`). Initialize `childEvents: []` on spawn-create.
- `chat_v2/store/chatStore.ts` — NEW `case "subagent_child_event"`: read `data.subagent_id` + `data.inner` (`{type, data}`); find the `SubagentNode` by `subagentId === data.subagent_id` (defensive-create if absent, mirroring the spawned/completed handlers `:638-743`); push a parsed `ChildTurnEvent` (map `inner.type` → kind: `turn_started`/`llm_responded`/`tool_call_request`/`tool_call_result`/`tool_call_failed`, extract turn/text/toolName from `inner.data`) onto `node.childEvents`.
- `chat_v2/components/inspector/InspectorTree.tsx` — `NodeRow` (`:132-173`) renders, under the node's existing label/status row, the `childEvents` as a per-turn list (e.g. `turn N · LLMResponded "…snippet…"` / `→ echo_tool(…)`). Reuse the existing `.indent` nesting style; the recursive subagent-of-subagent render (`:164-170`) is untouched (depth > 1 stays out of scope). Empty `childEvents` → render nothing extra (the 57.95 collapsed-node look is preserved when no TAO subset arrived).

### 3.4 What is explicitly NOT done (Scope reductions / separate slices)
- **Recursion depth > 1 (child-of-child turn-stream)** — a FORK whose child itself spawns: the inner subagent's TAO would need a second level of `subagent_id` routing. Out of scope; node-level recursion render exists but child-event nesting is depth-1 only this sprint.
- **Full-fidelity child events** — `LLMRequested`/`PromptBuilt`/`MemoryAccessed`/`SpanStarted`/`SpanEnded`/`MetricRecorded`/`StateCheckpointed`/`ContextCompacted` are NOT forwarded (TAO subset only — locked decision; keeps the Tree high-signal).
- **`LoopEvent` base `parent_session_id`/`depth` field** — NOT added (wrapper event chosen — minimal blast radius).
- **The inline `SubagentForkBlock` `{a.turns}t`** — a separate inline chat-bubble component; not the Tree; stays a 🟢 nuance.
- **TEAMMATE/HANDOFF real loops, child checkpoint/transcript/governance, failure policies** — unrelated, deferred per 57.94/57.95 carryover.

### 3.5 Lint / neutrality / schema-sync / 17.md
- `check_llm_sdk_leak` 0 (no adapter/SDK touched). `check_ap1_pipeline_disguise` green (the forward is a plain `isinstance`-gated emit inside the existing drain `async for`; no new loop driving). AP-4 green (this REMOVES Potemkin — the collapsed node now expands to real child telemetry). `category-boundaries`: the wrapper + serializer are Cat 11/contracts + the chat SSE layer; `ForkExecutor` is Cat 11; no new cross-category ABC. **`check_event_schema_sync` is the gating lint** — a new event type MUST be registered both sides (Day-1 locate; this is the one lint that a new wire type touches). **17.md (MANDATORY)**: register `SubagentChildEvent` ↔ `subagent_child_event` in the Cat 11/Cat 12 event registry section (a new event type is a contract addition — unlike 57.95's pure composition wiring). **No design note** (feature-continuation, not a spike — `sprint-workflow.md §Step 5.5`); CHANGE-063 records it.

### 3.6 Validation (US-1..US-5)
- **mypy `src/ --strict` 0**; `run_all` 10/10 (incl. `check_event_schema_sync` green); `black`/`isort`/`flake8 src/ tests/` clean (CI-equivalent scope, the 57.92 lesson; never `&&`-chain the format checks — the 57.95 CI lesson — run each independently).
- **pytest (backend)**:
  - **NEW** wrapper serialize test: `serialize_loop_event(SubagentChildEvent(subagent_id="x", inner=LLMResponded(...)))` → `{"type": "subagent_child_event", "data": {"subagent_id": "x", "inner": {"type": "llm_responded", "data": {...}}}}`; an inner non-TAO/non-serializable → skipped/propagated (defensive).
  - **NEW** ForkExecutor forwarding test: drive a FORK with a fake child loop yielding `TurnStarted`+`LLMResponded`+`ToolCallRequested`+`ToolCallExecuted`+`LoopCompleted` + a capturing emitter; assert the emitter received `SubagentChildEvent`s ONLY for the TAO subset (not `LoopCompleted`), each tagged with the spawn `subagent_id`, and the final-answer/token extraction still works.
  - **NEW** no-regression: a FORK with no emitter (other paths) → no forwarding, behaviour byte-identical to 57.94; a chat stream whose subagent emits no TAO subset → SSE byte-identical to 57.95 (the buffer-drain only adds `subagent_child_event` frames when forwarded).
  - **Existing** 57.12 emission + 57.94 child-loop + 57.95 relay tests UNCHANGED + green; `loop.py` diff = 0; `router.py` diff = 0.
  - Full backend suite green (NET delta documented — expect +N new tests, 0 deletions).
- **Vitest (frontend)**:
  - **NEW** `chatStore` `subagent_child_event` routing test: dispatch a `subagent_spawned` then a `subagent_child_event` (same `subagent_id`) → the node's `childEvents` has the parsed entry; an out-of-order `subagent_child_event` (no prior spawn) → defensive-creates the node.
  - **NEW** `InspectorTree` render test: a `SubagentNode` with `childEvents` → the per-turn rows render under the node; empty `childEvents` → only the collapsed node (57.95 look preserved).
- **Drive-through** (US-5): real UI + real backend + real Azure — a chat-v2 request that makes the agent `task_spawn` a sub-task whose child calls a tool → expand the Tree subagent node → confirm the child's per-turn TAO renders (LLMResponded + the tool call) where 57.95 showed only the collapsed node; screenshot + observed-vs-intended diff in progress.md. (Per CLAUDE.md §Drive-Through Acceptance — "the Tree node actually expands to child turns a human can see" is the leg-specific assertion; backend frames alone are gate/probe, not drive-through.)

---

## 4. File Change List

| File | Change |
|------|--------|
| `backend/src/agent_harness/_contracts/events.py` | **EDIT** — NEW `SubagentChildEvent(LoopEvent)` dataclass (`subagent_id: str`, `inner: LoopEvent`), placed near `SubagentSpawned`/`SubagentCompleted`. MHist 1-line. |
| `backend/src/api/v1/chat/sse.py` | **EDIT** — NEW `serialize_loop_event` branch for `SubagentChildEvent` → `subagent_child_event` (recursively serialize `inner`). MHist 1-line. |
| `backend/src/agent_harness/subagent/modes/fork.py` | **EDIT** — `_drive` forwards the TAO subset wrapped in `SubagentChildEvent` (tagged with `subagent_id`); `_TAO_CHILD_EVENT_TYPES` tuple; emitter + subagent_id param. MHist 1-line. |
| `backend/src/agent_harness/subagent/dispatcher.py` | **EDIT** — thread `self._event_emitter` + the spawn `subagent_id` into the `ForkExecutor` drive. MHist 1-line. |
| `backend/src/agent_harness/subagent/_abc.py` or executor base (Day-1 confirm) | **EDIT (conditional)** — if the executor ABC `spawn`/`run` signature needs the emitter + subagent_id param. |
| `<event schema sync source>` (Day-1 locate via `check_event_schema_sync`) | **EDIT** — register `SubagentChildEvent` ↔ `subagent_child_event` so the sync lint stays green. |
| `frontend/src/features/subagent/types.ts` | **EDIT** — `SubagentNode.childEvents: ChildTurnEvent[]` + NEW `ChildTurnEvent` interface. |
| `frontend/src/features/chat_v2/store/chatStore.ts` | **EDIT** — NEW `case "subagent_child_event"` routes by `subagent_id` → appends parsed entry to `node.childEvents`. |
| `frontend/src/features/chat_v2/components/inspector/InspectorTree.tsx` | **EDIT** — `NodeRow` renders the per-turn `childEvents` under the node (reuse `.indent`). |
| `backend/tests/.../chat/test_subagent_child_turnstream*.py` (NEW) | **NEW** — wrapper serialize round-trip + ForkExecutor TAO-subset forwarding (tagged + filtered) + no-regression. |
| `frontend/src/features/chat_v2/store/__tests__/...` + `inspector/__tests__/...` (Day-1 locate / NEW) | **NEW** — store `subagent_child_event` routing + `InspectorTree` per-turn render. |
| `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-96-plan.md` + `-checklist.md` | **NEW** — this plan + checklist |
| `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-96/progress.md` + `retrospective.md` | **NEW** — Day 0-N progress + retro |
| `claudedocs/4-changes/feature-changes/CHANGE-063-subagent-child-turnstream-nesting.md` | **NEW** — the change record (wrapper event; ForkExecutor TAO forward; frontend childEvents + render). |
| `docs/03-implementation/agent-harness-planning/17-cross-category-interfaces.md` | **EDIT (MANDATORY)** — register `SubagentChildEvent` ↔ `subagent_child_event` in the Cat 11/Cat 12 event registry (new event type = contract addition). |

**NOT in this list (unchanged)**: `loop.py` (diff = 0) · `router.py` (the 57.95 relay is already generic — diff = 0) · `LoopEvent` base (wrapper, not a base field) · the 57.95 spawn/completed serializers (`sse.py:306-326` kept; the new branch is additive) · the 57.95 emitter threading (`_category_factories.py`/`handler.py` reused as-is — the child events flow through the SAME emitter) · no DB/migration · no adapter/SDK.

---

## 5. Acceptance Criteria

- A NEW `SubagentChildEvent(subagent_id, inner: LoopEvent)` wrapper exists with one SSE serializer producing `subagent_child_event` (recursively serializing the inner); the `LoopEvent` base + the ~30 existing serializers are untouched (US-1).
- `ForkExecutor._drive` forwards the TAO subset (`TurnStarted`/`LLMResponded`/`ToolCallRequested`/`ToolCallExecuted`/`Failed`) wrapped + tagged with the spawn `subagent_id`; the dispatcher threads `self._event_emitter` + `subagent_id`; the final-answer/token extraction is preserved; non-TAO events + `LoopCompleted` are NOT forwarded (US-2).
- The Inspector "Tree" subagent node expands to show the child's per-turn TAO (`SubagentNode.childEvents` + `chatStore` `subagent_child_event` routing by `subagent_id` + `InspectorTree.NodeRow` per-turn render); the 57.95 collapsed-node render is preserved when no TAO subset arrives (US-3).
- NO `LoopEvent` base change; `router.py` diff = 0; `loop.py` diff = 0; the 57.95 relay UNCHANGED; a non-spawn / no-TAO run → byte-identical SSE vs 57.95; 57.12 + 57.94 + 57.95 tests green; `check_event_schema_sync` green (US-4).
- `mypy --strict src/` 0; `run_all` 10/10 (LLM SDK leak 0; AP-1; AP-4 — removes a Potemkin; `check_event_schema_sync`); `black`/`isort`/`flake8 src/ tests/` clean (run independently, not `&&`-chained); full backend pytest + Vitest green (NET deltas documented); CHANGE-063 written; **17.md event registered** (mandatory).
- **Drive-through PASS**: real UI + real backend + real Azure — a chat-v2 `task_spawn` whose child calls a tool → the Tree node expands to show the child's per-turn TAO (LLMResponded + the tool call); screenshot + observed-vs-intended diff (before: 57.95 collapsed node; after: expanded child turns). (No "gate-only" claimed as drive-through.)

---

## 6. Deliverables

- [ ] `SubagentChildEvent(subagent_id, inner)` wrapper in `_contracts/events.py` + `subagent_child_event` SSE serializer in `sse.py` (US-1)
- [ ] `check_event_schema_sync` source registers `SubagentChildEvent` ↔ `subagent_child_event` both sides (US-1/US-4)
- [ ] `ForkExecutor._drive` forwards the TAO subset wrapped + tagged with `subagent_id`; dispatcher threads `_event_emitter` + `subagent_id`; final-answer/token extraction preserved (US-2)
- [ ] Frontend: `SubagentNode.childEvents` + `chatStore` `subagent_child_event` routing + `InspectorTree.NodeRow` per-turn render (US-3)
- [ ] Tests (backend): wrapper serialize round-trip / ForkExecutor TAO-subset forwarding (tagged + filtered) / no-regression (no emitter + no-TAO byte-identical) / 57.12+57.94+57.95 green / `loop.py`+`router.py` diff = 0 (US-1..US-4)
- [ ] Tests (frontend): `chatStore` `subagent_child_event` routing / `InspectorTree` per-turn render + empty-preserves-collapsed (US-3/US-4)
- [ ] mypy 0 + run_all 10/10 (incl. `check_event_schema_sync`) + format chain `flake8 src/ tests/` (run independently) (validation)
- [ ] **drive-through PASS** (real UI + real backend + real Azure; the Tree node expands to child TAO; screenshot + before/after diff) (US-5)
- [ ] CHANGE-063 + progress.md + retrospective.md + **17.md event registration** (NO design note — feature-continuation)
- [ ] commit (Day 0-N) — push + PR user-authorized

---

## 7. Workload Calibration

Scope class: **`subagent-child-turnstream-nesting` (NEW, 0.55 mid-band) — 1st data point, pending 2-3 sprint validation**. A multi-layer feature extension (NEW contract event type + executor forwarding + frontend data model + store routing + nested render), distinct from `subagent-sse-relay-wiring` (57.95, pure backend composition wiring, no contract/frontend) and from `subagent-child-loop-spike` (57.94, child-loop construction). The work splits: wrapper event + SSE serializer + schema-sync (~1.5 hr) / ForkExecutor TAO-subset forward + dispatcher threading (~1.5 hr) / frontend childEvents + store case + NodeRow render (~3 hr) / tests backend + frontend (~3 hr) / drive-through (spawn a tool-using subagent + expand the node + screenshot) (~1.5 hr) / docs (CHANGE-063 + progress + retro + 17.md; NO design note) (~1.5 hr). Dominant costs = frontend render + tests. **Agent-delegated: no** (parent-direct) — the contract event type, the ForkExecutor `subagent_id` tagging correctness, and the drive-through (a UI nested-Tree assertion) are parent verification work; the frontend render could be agent-delegated once this pattern lands. `agent_factor = 1.0`; does NOT extend the AgentDelegated-WallClock streak.

> Bottom-up est ~12 hr → class-calibrated commit ~6.5 hr (mult 0.55). **Agent-delegated: no.**

If Day-1 shows the wiring ripples wider than the spec'd files (e.g. `ForkExecutor` can't receive the emitter without an ABC signature change cascading to TEAMMATE/HANDOFF; `check_event_schema_sync` requires a codegen step that touches many files; the `subagent_id` available at spawn differs from the child-event routing key the frontend expects; the per-turn render needs a `SubagentNode` shape change that breaks the 57.95 node tests), STOP and re-scope rather than rush.

---

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| **`subagent_id` mismatch (child events route to the wrong node)** | The frontend `SubagentNode` is keyed by the `subagent_id` from `SubagentSpawned` (`dispatcher.py:189-196`). The ForkExecutor MUST tag child events with the SAME `subagent_id` (NOT the local `child_session_id` uuid4 `fork.py:105`). Day-1 confirm the dispatcher passes its spawn `subagent_id` (not the child session id) into `_drive`. A routing test (spawn then child_event, assert the node got it) guards it. |
| **`check_event_schema_sync` codegen / dual-source** | A new event type is the one change that touches this lint. Day-1 locate what it reads (a hand-maintained map vs a generated file). If hand-maintained → add both sides; if generated → run the codegen + commit. The lint must be green before any drive-through. |
| **`ForkExecutor` emitter threading (ABC ripple)** | The Explore noted `ForkExecutor.__init__` accepts no emitter; the dispatcher invokes it. Prefer passing emitter + subagent_id via the `spawn`/`run` call (not `__init__`) to avoid an ABC signature change that ripples to TEAMMATE/HANDOFF executors. Day-1 read the executor ABC + the dispatcher call site; if the ABC must change, keep the new params optional (default None) so TEAMMATE/HANDOFF are unaffected. |
| **AS_TOOL shares the executor → inherits forwarding** | 57.94 said AS_TOOL inherits the FORK child loop. Day-1 confirm it shares `ForkExecutor` → it inherits the child-event forwarding (in scope, same code, no extra work). If it does NOT share, AS_TOOL child-turn-stream is a separate slice (note in §9). |
| **Frontend `SubagentNode` shape change breaks 57.95 node tests** | `childEvents` is additive (default `[]`); the 57.95 spawned/completed tests assert `subagentId`/`status`/`summary`/`tokensUsed` — unaffected. Initialize `childEvents: []` on spawn-create so existing assertions + the collapsed render are byte-identical when no TAO arrives. |
| **AP-1 flags the forward as a pipeline** | The forward is an `isinstance`-gated `await emitter(...)` inside the EXISTING drain `async for` (no new loop driving, no `for step in steps`); mirror the 57.95 precedent (the drain is a serialize-and-yield, not a pipeline). |
| **Out-of-order / dropped child_event in the store** | The store routes by `subagent_id`; if a `subagent_child_event` arrives before its `subagent_spawned` (unlikely — spawn emits first), defensive-create the node (mirror the 57.95 completed-handler defensive create `:695-743`). A routing test covers the out-of-order case. |
| **Tree noise / render perf** | TAO subset only (locked) keeps the per-turn list short; depth > 1 out of scope. The render is a flat per-turn list under the node (not a deep recursion), so MAX_DEPTH=5 is unaffected. |
| **Risk Class E (stale `--reload` backend)** | Clean restart before the drive-through (kill stale uvicorn reloader+worker procs; verify :8000 OWNER is the fresh PID) — the forwarding is startup-built; a stale process runs the 57.95-only dispatcher and the node would (wrongly) stay collapsed. Bit 57.91-95 (5 consecutive). |
| **Risk Class C (test isolation)** | The buffer is per-request (57.95, router fn scope); no module singleton. The ForkExecutor emitter is passed per-spawn. Run the full suite; existing chat conftest reset fixtures cover the dispatcher. |
| **Over-engineering (Scope creep)** | TAO subset + depth-1 only; NO base field, NO full-fidelity events, NO TEAMMATE/HANDOFF, NO inline `{a.turns}t` (Karpathy §2/§3). |
| **Smuggling unrelated change** | The diff is exactly: contract (`events.py`) + serializer (`sse.py`) + executor (`fork.py`/`dispatcher.py`) + schema-sync source + 3 frontend files + tests + docs. `loop.py`/`router.py`/`LoopEvent`-base/57.95-emitter-threading diff = 0. |
| **LLM-neutrality** | No adapter/SDK touched; `check_llm_sdk_leak` gates. |
| **`&&`-chained format checks mask failures (57.95 CI lesson)** | Run `black --check` / `isort --check` / `flake8` / `mypy` INDEPENDENTLY (not `&&`-chained) before push — an early failure must not short-circuit the later checks (the 57.95 PR #268 CI miss). |

---

## 9. Out of Scope (this sprint; → separate slices / ADs)

- **Recursion depth > 1 (child-of-child turn-stream)** — a subagent whose child itself spawns needs a second level of `subagent_id` routing + nested-of-nested render. Stays `AD-Subagent-Child-Event-SSE-Relay` residual.
- **Full-fidelity child events** (`LLMRequested`/`PromptBuilt`/`MemoryAccessed`/`Span*`/`Metric*`/`Checkpoint`/`ContextCompacted`) — TAO subset only (locked decision).
- **`LoopEvent` base `parent_session_id`/`depth` field** — wrapper chosen (locked decision).
- **Inline `SubagentForkBlock` `{a.turns}t`** — separate inline component, not the Tree; 🟢 nuance.
- **`AD-Subagent-Child-Span-Nesting`** (task_spawn passes `trace_context=None` → child span not explicitly parented) — separate 🟢; orthogonal to SSE relay.
- **TEAMMATE / HANDOFF real loops · `HandoffService`** — separate slices (single-shot today; AS_TOOL inherits FORK forwarding only if it shares the executor).
- **Recursion depth > 1 · parentUuid transcript chain · child checkpoint · child-internal governance · failure policies** — deferred per 57.94/57.95 carryover.
