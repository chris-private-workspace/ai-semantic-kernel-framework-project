# Sprint 57.96 Progress — Cat 11 Subagent child turn-stream nesting (Scope B)

**Plan**: [`../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-96-plan.md`](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-96-plan.md)
**Checklist**: [`../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-96-checklist.md`](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-96-checklist.md)

---

## Day 0 — 2026-06-09 — Plan-vs-Repo Verify + Branch

### Today's Accomplishments
- Selected via AskUserQuestion (2026-06-09): Theme B → **Scope B child turn-stream**; relay mechanism = **Wrapper event** `SubagentChildEvent(subagent_id, inner)`; depth = **TAO essentials subset**.
- Ran 1 Explore agent map (read-only) of the Scope B-relevant backend contract / executor / SSE relay + frontend Tree → grounded the plan in repo reality (anchors below).
- Drafted plan (9 sections 0-9, mirroring 57.95) + checklist (Day 0-4) + this progress.
- Branch `feature/sprint-57-96-subagent-child-turnstream` from `main` `aebeab4c` (57.95 merged, #268).

### Day-0 Three-Prong Verify

**Prong 1 (path)** — anchors confirmed:
- `LoopEvent` base `_contracts/events.py:56` (event_id/timestamp/trace_context only) · `SubagentSpawned` `:349` (subagent_id/mode/parent_session_id) · `SubagentCompleted` `:356` · TAO types `TurnStarted` `:73`, `LLMResponded` `:92`, `ToolCallRequested` `:183`, `ToolCallExecuted` `:193`, `ToolCallFailed` `:201`, `LoopCompleted` `:127`.
- `ForkExecutor._drive` drain loop `subagent/modes/fork.py:102-114` (acts on LLMResponded + LoopCompleted only; discards the rest; no emitter).
- `SubagentEventEmitter` `dispatcher.py:90` · `_event_emitter` param `:109` stored `:134` · emit SubagentSpawned `:189-196` · SubagentCompleted `:234/:242`.
- Router relay `_relay_subagent_event` `router.py:237-238` + `_drain_subagent_frames` `:363-385` (GENERIC over any LoopEvent) · `serialize_loop_event` subagent branches `sse.py:306-326` + LLMResponded `:153-171` + NotImplementedError fallthrough `:429`.
- Frontend `features/subagent/types.ts:62-73` (SubagentNode flat — no childEvents) · `chat_v2/store/chatStore.ts:136` slice / `:638-692` spawned / `:695-743` completed · `chat_v2/components/inspector/InspectorTree.tsx:73-95` buildTree / `:132-173` NodeRow (recursive, MAX_DEPTH=5 `:59`) · `chat_v2/components/blocks/SubagentForkBlock.tsx:54-93` inline (separate; `{a.turns}t` `:88` = integer turn count, NOT tokens).

**Prong 2 (content)** — premise check (Explore "Scope B premise check"):
- Premise 1 (LoopEvent base field) → **CONFIRMED-NEEDED** — child TAO events carry no session/subagent identifier. Resolved by the **wrapper** (locked), NOT a base field.
- Premise 2 (ForkExecutor forwarding) → **CONFIRMED-NEEDED** — `_drive` discards all but LLMResponded/LoopCompleted; ForkExecutor has no emitter.
- Premise 3 (frontend nested render) → **PARTIALLY-EXISTS** — InspectorTree recursive scaffold exists; `SubagentNode` has no `childEvents` + no store routing.
- Premise 4 (chatStore subagent_id routing) → **CONFIRMED-NEEDED** — no case routes child loop events by subagent_id.
- Bonus correction: the router relay is ALREADY generic → **router.py needs ZERO change**; `sse.py` already serializes the inner TAO types → only ONE new wrapper serializer branch.

**Prong 2.5 (event / drift)**:
- **D1**: `SubagentChildEvent` IS a `LoopEvent` → rides the SAME 57.95 emitter + already-generic router buffer-drain for FREE (only a new SSE serializer branch).
- **D2**: child events MUST be tagged with the spawn `subagent_id` (NOT the local `child_session_id` uuid4 `fork.py:105`) so the frontend routes to the node the spawn created. **Key routing-correctness item.**
- **D3**: a NEW event type touches `check_event_schema_sync` (the one gating lint — Day-1 locate its source) + 17.md (mandatory contract registration). Unlike 57.95 (pure composition wiring, conditional 17.md), this is a contract addition.
- **D4 (drift vs 57.95 carryover)**: carryover said Scope B "needs a LoopEvent base parent_session_id/depth field" — the locked decision is a WRAPPER (base untouched); and router.py is UNCHANGED (carryover implied relay work — it's already generic). Scope is wrapper+executor+frontend, NOT a base-contract change.

**Prong 3 (schema)**: N/A — no DB/migration/ORM. (Event-contract addition handled via `check_event_schema_sync`, not DB schema.)

### Go/No-Go
**GO** — feasibility CONFIRMED: the wrapper rides the existing 57.95 relay; `router.py`/`loop.py`/`LoopEvent` base UNCHANGED; the 4 layers (wrapper+serializer / executor forward / store route / render) are scoped. Two Day-1 locates remain (the `check_event_schema_sync` source; the `ForkExecutor` emitter threading path + AS_TOOL sharing) — both are reads, not blockers; if either ripples wider than expected (ABC cascade / codegen), STOP and re-scope per plan §7.

### Remaining for Day 1
- Locate `check_event_schema_sync` source + the `ForkExecutor` emitter threading path (ABC vs spawn-call; AS_TOOL sharing).
- Capture exact pytest + Vitest baselines at branch creation.
- US-1 wrapper event + serializer + schema-sync; US-2 ForkExecutor TAO forward + dispatcher threading.

### Notes
- Baseline = `main` HEAD `aebeab4c` (57.95 #268): pytest 2277 / mypy 0/351 / run_all 10/10 (exact Vitest baseline to capture Day-1).
- Calibration class: NEW `subagent-child-turnstream-nesting` 0.55 mid-band (1st data point); agent_factor 1.0 (parent-direct).

---

## Day 1-2 — 2026-06-09 — Wrapper + ForkExecutor forward + frontend (US-1/2/3)

### Day-1 locates (resolved)
- **`check_event_schema_sync` source**: a codegen chain — `event_wire_schema.py` (registry) → `scripts/codegen/generate_event_schemas.py` → `frontend/.../generated/{events.json,loopEvents.generated.ts}`; lint #10 runs codegen `--check`. A new wire type → registry entry + run codegen + commit generated artifacts + parity test (backend `test_event_wire_schema_parity.py` 22→23 + frontend `eventSchema.generated.test.ts` 22→23).
- **ForkExecutor emitter path**: `ForkExecutor.__init__` gains `event_emitter`; the dispatcher passes `self._emit_safely` (best-effort + reads live `_event_emitter` at call time → no `__init__` ordering issue). `execute(subagent_id: UUID, …)` ALREADY carries `subagent_id` → tag uses it directly. **AS_TOOL shares `self._fork`** (`AsToolWrapper(fork_executor=self._fork)`) → inherits forwarding free.
- **Day-1 naming refinement (drift)**: wire type named **`subagent_child`** (NOT `subagent_child_event`) to avoid the `SubagentChildEventEvent` interface in `WIRE_TYPE_TO_INTERFACE` (codegen appends nothing; the map value is the full name). Interface = `SubagentChildEvent` (clean; matches the Python class name cross-layer).

### Implemented
- Backend: `SubagentChildEvent(subagent_id, inner)` in `_contracts/events.py` (+ `__init__` re-export) · `sse.py` serializer → `subagent_child` (recursive inner re-serialize → `{inner_type, inner}`) · `event_wire_schema.py` +1 (22→23) · codegen regen + lint #10 green · `fork.py` `_TAO_CHILD_EVENT_TYPES` + `_drive` forwards wrapped/tagged · `dispatcher.py` passes `_emit_safely`. **`loop.py`/`router.py`/`LoopEvent` base UNCHANGED.**
- Frontend: `SubagentNode.childEvents` + `ChildTurnEvent` (`subagent/types.ts`) · `chatStore` `case "subagent_child"` routes by `subagent_id` (type-guarded projection) · `InspectorTree` `ChildTurnRow` nested rows (mockup `.subagent-row`/`.indent` vocabulary, no new CSS).
- Tests: NEW `test_subagent_child_turnstream.py` (5: TAO-subset forward + tag + filter / no-emitter no-forward / serialize round-trip / Thinking+None skip) · parity 22→23 + instance · 57.12 emission test fixed (locate Completed by type — child TAO now interleaves) · frontend mergeEvent +2 routing tests · ChatInspector +2 render tests · eventSchema 22→23 +recognize test · ChatInspector fixture `childEvents:[]`.

### Gate (parent-verified)
- mypy `src --strict` **0/351** · pytest **2283 (+6)** / 4 skipped · run_all **10/10** (incl `check_event_schema_sync`) · black/isort/flake8 `src tests` clean · `loop.py`+`router.py` diff = **0**.
- Vitest **777 (+7)** · `npm run build` (tsc) ✓ · `npm run lint` ✓ · `check:mockup-fidelity` baseline **53 unchanged** (0 new oklch/hex).
- Commit `d087a451` (Day 1-2 code+tests+regenerated artifacts).

---

## Day 3 — 2026-06-09 — Drive-through (US-5) — **PASS**

### Risk Class E clean restart
- :8000 held by stale 57.95 reloader **50200** + spawn-worker **20360**; `--reload` respawned a worker (70560) when the worker was killed first → killed the **reloader first** then the orphan worker → :8000 FREE → `dev.py start backend` → fresh **PID 41464** owns :8000 (`/health` 401 = up + tenant middleware). Frontend node :3007 (PID 6200) untouched (constraint: never stop node).

### Drive-through (real UI :3007 + fresh backend PID 41464 + real Azure gpt-5.2; jamie@acme.com / acme-prod / real_llm)
Prompt: *"Use task_spawn to delegate a sub-task to a child subagent. Instruct that child to call echo_tool with the exact text 'child turn-stream visible', then tell me what the child returned."*

| Layer | Observed | Intended | Verdict |
|-------|----------|----------|---------|
| **Tree (BEFORE)** | "no subagents spawned this session" | empty pre-spawn | ✅ |
| **Tree (AFTER)** | each FORK node EXPANDS → `turn 0` · `LLM` · `→ echo_tool()` · `← echo_tool · child turn-stream visible` · `turn 1` · `LLM · child turn-stream visible` | node shows the child's per-turn TAO loop | ✅ **Scope B met** |
| **Trace frames** | relayed `subagent_child {subagent_id, inner_type, inner}` frames for turn_start/llm_response/tool_call_request/tool_call_result, interleaved between `subagent_spawned`/`subagent_completed` | the wrapper rides the relay; impossible pre-57.96 (child events discarded) | ✅ corroboration |
| **Parent answer** | turn 7 `stop: end_turn` → "The child returned: `child turn-stream visible`" | final answer renders in the conversation | ✅ |
| **Summary row** | Mode fork · Depth 1 · Tokens (subtree) 11,068 | unchanged subagent-nesting depth (child rows ≠ subagents) | ✅ |

- Real LLM task_spawned **3 forks** (LLM retried after the verification judge scored the fragment off-topic — irrelevant to Scope B; all 3 nodes render their child TAO correctly).
- Out-of-scope nuance confirmed unchanged: the inline `SubagentForkBlock` still shows `0t` (turn count, NOT the Tree; deferred 🟢 per plan §9).
- Evidence: `artifacts/sprint-57-96-tree-{1-before-empty,2-expanded-child-tao,3-fullpage-answer-and-tree}.png`.

### Verdict
Shipped + **drive-through PASS**. The Tree node expands to the child's per-turn TAO; the relayed `subagent_child` wire frames in the Trace are unambiguous proof (the exact serializer shape, impossible pre-57.96). `loop.py`/`router.py`/`LoopEvent`-base untouched; wrapper-event minimal blast radius.
