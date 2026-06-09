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
