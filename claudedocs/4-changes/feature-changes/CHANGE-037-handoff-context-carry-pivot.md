# CHANGE-037: HANDOFF Agent-Side Context Carry + FE Session-Pivot (A-3b slice 2)

**Date**: 2026-06-02
**Sprint**: 57.69
**Scope**: Cat 11 (HANDOFF) + Cat 1 (loop snapshot) + platform handoff service + Cat 5 (persona prompt seed) + Frontend (chat_v2 session-pivot)

## What Changed

Slice 2 of the user-chosen full HANDOFF model (Option B). Slice 1 (57.68) booted a linked child session under the target persona but with NO prior conversation, and the FE only logged `agent_handoff` in `rawEvents`. This change adds:

1. **Agent-side context carry** — the target agent now runs with the parent's prior conversation in its prompt:
   - `loop.py` snapshots the in-memory conversation (`handoff_context=list(messages)`) onto `LoopCompleted` (in-process field; NOT on the `loop_end` client wire — `sse.py` maps only 4 fields).
   - `platform_layer/handoff/context_carry.py` (NEW): `cap_and_serialize` (last-20 message-count cap, drop-oldest, LLM-neutral — no `ChatClient`) + `render_carried_context_block`.
   - `HandoffService.boot_handoff(+parent_context)` stores the capped verbatim copy in the child's `meta_data["carried_context"]` (no migration — `meta_data` JSONB; 57.68 backward-compat when empty).
   - `router.py` passes `event.handoff_context`; `handler.py resolve_session_persona` appends the carried block to the resolved persona prompt (nested fail-open).
2. **FE session-pivot** — the `agent_handoff` SSE event pivots the active chat session to `new_session_id` (reset conversation, set `sessionId` + `activeSessionId`) and shows a transition banner (`HandoffBanner.tsx`, AP-2 — no mockup source).

## Why

`18-handoff-design.md §5` listed FE session-pivot + full message-context carry as the deferred half of Option B. A >50% Day-0 reality drift (conversation messages are never persisted — the `messages` table is dormant; history lives only in the in-memory loop state; the FE rebuilds the transcript from the live SSE stream) reshaped the user's "full message-context carry" into **C-1 agent-side carry** (1 sprint): carry the in-memory snapshot, not a DB copy. User-visible transcript continuity (showing old messages in the pivoted UI) needs a message-persistence subsystem (2+ sprints) and stays deferred.

## Verification

- Backend: full `pytest tests/unit tests/integration` → **2015 passed / 4 skipped / 0 failed**; `mypy src/` 0/325; `run_all.py` 10/10 (`check_llm_sdk_leak` 0; no codegen drift — `WIRE_SCHEMA` 19). New: `test_context_carry.py` (10) + `test_service.py` (+2) + `test_chat_handoff_unit.py` (+3) + integration `test_chat_handoff.py` (+1: carried_context populated/capped/tenant-scoped + `loop_end` has no `handoff_context` + persona embeds the block).
- Frontend: `check:mockup-fidelity` ✓ (50=50; `HEX_OKLCH_BASELINE` bumped 48→50 for the banner's verbatim `var(--info)` tints) + `lint` exit 0 + Vitest **709 passed** (+11: chatStore +8, HandoffBanner +3) + `build` ✓.

## Impact

- Backend: additive (no migration, no new wire-type, no codegen). `boot_handoff` signature gains an optional `parent_context`; `LoopCompleted` gains an in-process `handoff_context`; `resolve_session_persona` augments the prompt. All LLM-neutral.
- Frontend: `chat_v2` `agent_handoff` now pivots (was a passthrough); new `HandoffBanner` component.
- Deferred (design note §5/§8.4): user-visible transcript continuity, summarize-carry, target auto-first-turn, multi-hop chains, real agent catalog, dedicated columns.

## Related

- `docs/03-implementation/agent-harness-planning/18-handoff-design.md §8` — slice-2 design note (8-point gate)
- `sprint-57-69-plan.md` / `-checklist.md` / `agent-harness-execution/phase-57/sprint-57-69/{progress,retrospective}.md`
- Predecessor: CHANGE-036 (57.68 slice 1)
