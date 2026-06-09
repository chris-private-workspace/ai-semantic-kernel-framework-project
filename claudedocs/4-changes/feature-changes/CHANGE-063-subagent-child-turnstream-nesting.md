# CHANGE-063: Subagent child turn-stream nesting (Cat 11 Scope B)

**Change Date**: 2026-06-09
**Change Type**: New Feature (feature-continuation of the Cat 11 arc — NO design note per `sprint-workflow.md §Step 5.5`)
**Sprint**: 57.96
**Scope**: Cat 11 (Subagent) × Cat 12 (Observability) — backend contract + executor + chat SSE; frontend store + Inspector Tree
**Status**: ✅ Completed (drive-through PASS)

## Change Summary

The chat-v2 Inspector "Tree" subagent node now **expands to show the child loop's per-turn TAO loop** (the child's `TurnStarted` / `LLMResponded` / tool-call events), closing the remaining half of `AD-Subagent-Child-Event-SSE-Relay`. Sprint 57.94 made FORK run a real child loop; 57.95 made the subagent visible as a single collapsed node; 57.96 expands that node.

## Change Reason

57.95 closed `AD-Subagent-Child-Event-SSE-Relay` at the **node level** only — the Tree showed a collapsed node (mode / summary / tokens) but not the child's inner loop. The carryover (Scope B) requested expanding the node to surface the child's per-turn TAO so the operator can see what the subagent actually did.

## Design (locked via AskUserQuestion 2026-06-09)

- **Relay mechanism = Wrapper event** (over a `LoopEvent` base field): NEW `SubagentChildEvent(subagent_id, inner: LoopEvent)`. Minimal blast radius — the `LoopEvent` base + ~30 existing serializers are UNCHANGED; the wrapper IS a `LoopEvent` so it rides the existing 57.95 emitter + already-generic router buffer-drain for free.
- **Depth = TAO essentials subset**: only `TurnStarted` / `LLMResponded` / `ToolCallRequested` / `ToolCallExecuted` / `ToolCallFailed` are forwarded (excludes `LLMRequested` / `PromptBuilt` / `MemoryAccessed` / `Span*` / `Metric*` / `Checkpoint` / `ContextCompacted` noise) to keep the Tree high-signal.

## Detailed Changes

### Backend
- `agent_harness/_contracts/events.py` — NEW `SubagentChildEvent(LoopEvent)` (`subagent_id: UUID | None`, `inner: LoopEvent | None`) + `_contracts/__init__.py` re-export.
- `api/v1/chat/sse.py` — NEW `serialize_loop_event` branch → wire type `subagent_child` with `{subagent_id, inner_type, inner}` (the inner is re-serialized via its OWN branch → `{type, data}`; `inner` = the inner event's `data` dict; defensive skip if the inner serializes to None).
- `api/v1/chat/event_wire_schema.py` — registry +1 (`subagent_child`; 22→23) + `scripts/codegen/generate_event_schemas.py` `WIRE_TYPE_TO_INTERFACE["subagent_child"]="SubagentChildEvent"` → regenerated `frontend/.../generated/{events.json,loopEvents.generated.ts}` (lint #10 `check_event_schema_sync` green).
- `agent_harness/subagent/modes/fork.py` — `_TAO_CHILD_EVENT_TYPES` tuple; `ForkExecutor.__init__` gains `event_emitter`; `_drive` forwards each TAO-subset child event wrapped in `SubagentChildEvent(subagent_id=…, inner=ev)`. Final-answer/token extraction preserved.
- `agent_harness/subagent/dispatcher.py` — `ForkExecutor(event_emitter=self._emit_safely)` (best-effort wrapper; reads the live `_event_emitter` at call time → no `__init__` ordering issue). **AS_TOOL shares `self._fork` → inherits forwarding free.**
- **UNCHANGED**: `loop.py` (diff = 0), `router.py` (the 57.95 relay is already generic — diff = 0), the `LoopEvent` base, the 57.95 emitter threading.

### Frontend
- `features/subagent/types.ts` — `SubagentNode.childEvents: ChildTurnEvent[]` + NEW `ChildTurnEvent` interface.
- `features/chat_v2/store/chatStore.ts` — NEW `case "subagent_child"` routes by `subagent_id` (type-guarded projection of `inner` → `ChildTurnEvent`; defensive-create on out-of-order).
- `features/chat_v2/components/inspector/InspectorTree.tsx` — `ChildTurnRow` renders each child TAO event as a nested `.subagent-row` inside the node's `.indent` (mockup vocabulary; no new CSS / no new oklch).

## Modified Files List

Backend (6 src + 3 tests): `_contracts/events.py`, `_contracts/__init__.py`, `api/v1/chat/sse.py`, `api/v1/chat/event_wire_schema.py`, `subagent/modes/fork.py`, `subagent/dispatcher.py`; `test_subagent_child_turnstream.py` (NEW), `test_event_wire_schema_parity.py`, `test_subagent_sse_emission.py`.
Frontend (3 src + 2 generated + 3 tests): `subagent/types.ts`, `chat_v2/store/chatStore.ts`, `chat_v2/components/inspector/InspectorTree.tsx`; `generated/events.json`, `generated/loopEvents.generated.ts`; `chatStore.mergeEvent.test.ts`, `ChatInspector.test.tsx`, `eventSchema.generated.test.ts`.
Tooling: `scripts/codegen/generate_event_schemas.py`. Contract: `17-cross-category-interfaces.md`.

## Test Verification

- mypy `src --strict` 0/351 · pytest 2283 (+6) / 4 skipped · run_all 10/10 (incl `check_event_schema_sync`) · black/isort/flake8 clean · `loop.py`+`router.py` diff = 0.
- Vitest 777 (+7) · build (tsc) ✓ · lint ✓ · `check:mockup-fidelity` baseline 53 unchanged.
- **Drive-through PASS** (real UI :3007 + fresh backend PID 41464 + real Azure gpt-5.2): a `task_spawn` whose child calls `echo_tool` → the Tree node expands to `turn 0 / LLM / → echo_tool() / ← echo_tool · child turn-stream visible / turn 1 / LLM · child turn-stream visible`; the Trace shows the relayed `subagent_child` wire frames; the parent answers "The child returned: `child turn-stream visible`". Screenshots: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-96/artifacts/`.

## Impact

Backend (new event type + executor forward) + frontend (store + Inspector render). No DB/migration, no adapter/SDK, no `loop.py`/`router.py` change. The new `subagent_child` wire type is a contract addition (registered in 17.md). Out of scope (carryover): recursion depth > 1 (child-of-child), full-fidelity child events, TEAMMATE/HANDOFF real loops, the inline `SubagentForkBlock` `0t` turn-count nuance.
