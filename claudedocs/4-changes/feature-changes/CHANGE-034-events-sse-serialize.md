# CHANGE-034: Serialize already-yielded diagnostic events to client SSE (A-5a+)

**Change Date**: 2026-06-02
**Change Type**: New Feature (observability — SSE event surfacing)
**Sprint**: 57.66
**Scope**: Cat 12 (Observability) / api/v1/chat SSE serializer + chat_v2 frontend wire-contract
**Status**: ✅ Completed (real_llm live e2e leg 🚧 deferred — Azure secrets; blocker removed)

## Change Summary

Four agent-loop diagnostic `LoopEvent`s were already yielded on the production chat path but **silently dropped at the SSE serializer** (no isinstance branch → `NotImplementedError` → `router.py` `except: continue`). This change adds their serializer branches so they reach the client, and carries the Sprint 57.65 prompt-cache fields onto the existing `llm_response`/`loop_end` frames. **Zero `loop.py` change** — the events already flowed; only their SSE projection + the FE wire-type gate were missing.

This is the **A-5a+ slice** of the larger "A-5 events→SSE" item (which the Day-0 audit found is 3 sub-pieces: A-5a serialize / A-5b codegen / A-5c Inspector UI). It directly **removes the architectural blocker** the deferred 57.63/64/65 `real_llm` e2e legs cited ("PromptBuilt / cache signal is in-process, not client SSE").

## Change Reason

- Capabilities shipped in prior sprints (Cat 5 PromptBuilt, Cat 4 ContextCompacted, Cat 7 StateCheckpointed, Cat 9 TripwireTriggered, and the 57.65 prompt-cache-hit signal) were invisible to the client — they died as in-process loop events. Operators couldn't observe prompt construction, context compaction, state checkpointing, guardrail tripwires, or cache effectiveness on the live stream.
- The 57.65 `cached_input_tokens`/`cache_hit_rate` fields were added to the events but the serializer never carried them (fresh regression — the signal died at the SSE boundary).

## Detailed Changes

### Backend (`backend/src/api/v1/chat/sse.py`)
- 4 net-new `serialize_loop_event` branches (mirror the `GuardrailTriggered` 53.6 pattern), snake_case wire-types:
  - `PromptBuilt` → `prompt_built` `{messages_count, estimated_input_tokens, cache_breakpoints_count, memory_layers_used: list, position_strategy_used, duration_ms}` (scope-key list, no memory content)
  - `ContextCompacted` → `context_compacted` `{tokens_before, tokens_after, compaction_strategy, messages_compacted, duration_ms}`
  - `StateCheckpointed` → `state_checkpointed` `{version}` (no snapshot body)
  - `TripwireTriggered` → `tripwire_triggered` `{violation_type, detail}`
- `cached_input_tokens` added to `llm_response`; `cached_input_tokens`+`cache_hit_rate` added to `loop_end` (additive).
- **FIX-025** (bundled — surfaced by the router e2e): `_jsonable` `hasattr(value,"hex")` heuristic also matched `float` → floats stringified on the wire; fixed to `isinstance(value, UUID)`. See `claudedocs/4-changes/bug-fixes/FIX-025-*.md`.

### Frontend (`frontend/src/features/chat_v2/`)
- `types.ts`: 4 new event types + `LoopEvent` union + `KNOWN_LOOP_EVENT_TYPES` (14→18); cache fields (`number`) on `LLMResponseEvent`/`LoopEndEvent`.
- `store/chatStore.ts`: `mergeEvent` exhaustive `switch (never)` required 4 explicit passthrough cases (`rawEvents`-only, mirror `guardrail_triggered`; no Inspector UI — A-5c deferred). `chatService.ts` unchanged (gate reads the KNOWN set).
- `orchestrator-loop/_fixtures/demoLoopEvents.ts`: cache-field ripple on `llm_response`/`loop_end` literals.

### Docs
- `docs/03-implementation/agent-harness-planning/02-architecture-design.md §SSE`: Sprint 57.66 real-serializer registration note (4 real wire-types + 2 cache fields; preserves the drifted catalog per the doc's Naming Drift Note precedent). 17.md §4.1 emit-ownership unchanged (events already registered).

## Modified Files List

| File | Change |
|------|--------|
| `backend/src/api/v1/chat/sse.py` | 4 serializer branches + cache fields + FIX-025 `_jsonable` |
| `backend/tests/unit/api/v1/chat/test_sse.py` | +7 unit +2 augmented +1 FIX-025 regression |
| `backend/tests/integration/api/test_chat_e2e.py` | `TestDiagnosticEventsE2E` router-level AP-4 e2e |
| `frontend/src/features/chat_v2/types.ts` | 4 event types + union + KNOWN set + cache fields |
| `frontend/src/features/chat_v2/store/chatStore.ts` | 4 passthrough `mergeEvent` cases |
| `frontend/src/features/orchestrator-loop/_fixtures/demoLoopEvents.ts` | cache-field fixture ripple |
| `frontend/tests/unit/chat_v2/chatService.parseSSEFrame.test.ts` | NEW — 7 FE recognition/parse tests |
| `docs/03-implementation/agent-harness-planning/02-architecture-design.md` | §SSE registration note |
| `claudedocs/4-changes/bug-fixes/FIX-025-*.md` | FIX-025 record |

## Test Checklist

- [x] Backend serializer per-event + cache fields + None/default-safe (`test_sse.py`)
- [x] Router-level AP-4 e2e — 4 events reach client through real pipeline + cache fields (`TestDiagnosticEventsE2E`)
- [x] Multi-tenant: `prompt_built` payload = scope-key list only, no content leak
- [x] FIX-025 regression: float wire fields serialize as JSON numbers
- [x] FE: 4 wire-types recognized (not dropped) + cache fields parse as numbers + unknown-type still dropped
- [x] pytest **1964 passed / 4 skipped** (+9); mypy src **0/319**; 9/9 V2 lints; Vitest **693** (+7); tsc 0; FE build ✓
- [ ] 🚧 real_llm live e2e (Azure secrets; blocker removed — now writable)
