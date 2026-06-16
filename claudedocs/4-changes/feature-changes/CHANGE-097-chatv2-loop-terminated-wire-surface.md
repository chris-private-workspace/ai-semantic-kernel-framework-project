# CHANGE-097: chat-v2 LoopTerminated wire surface

**Date**: 2026-06-16
**Sprint**: 57.130
**Scope**: 範疇 12 (Observability / SSE surfacing) + Frontend (chat-v2) — surfaces an existing 範疇 8 (Error Handling) event; NO new 17.md contract
**Closes**: `AD-LoopTerminated-Wire-Surface` (57.110 carryover)

## Problem
A FATAL-terminated chat-v2 run (`fail_fast` / rate-limit / circuit-open / max-retries / budget / fatal-exception via the Cat-8 `ErrorTerminator`) ends by `yield`ing a `LoopTerminated` event, but `serialize_loop_event` had no branch for it → it fell through to `NotImplementedError` → the router silently dropped it (`logger.debug("sse: skip ...")`). The SSE stream then just ENDED with no terminal frame:
- a tool that was mid-flight (a `tool_call_request` already streamed) never got a `tool_call_result` → the chat-v2 `ToolBlock` stayed **`status:"pending"` forever** (a perpetual spinner — the stuck pending tool chip);
- the run silently stopped with **no reason** shown to the user (the termination reason was server-side-only).

An AP-4 Potemkin-class broken-UX on the 主流量 (any fatal error reaches it), invisible to every gate (the backend "works", the API "responds" with a clean stream end).

## Root Cause
`LoopTerminated` (defined `agent_harness/_contracts/events.py:297`, emitted `loop.py:2939` hard / `:3008` soft) was never added to the chat SSE wire: no `serialize_loop_event` branch (`sse.py`), no `WIRE_SCHEMA` entry (`event_wire_schema.py`), so the codegen never produced a FE type and `mergeEvent` had no case. The router's `except NotImplementedError: continue` (`router.py:747-751`) dropped it.

## Solution
Cross-stack surfacing of the EXISTING event (no backend logic change; no new contract):
- **`sse.py`**: added a `LoopTerminated` branch to `serialize_loop_event` → `{type:"loop_terminated", data:{reason, detail, last_state_version}}`, mirroring the sibling `tripwire_triggered` fatal-terminate event (`trace_id` auto-injected by the wrapper).
- **`event_wire_schema.py`**: appended the `loop_terminated` entry (`reason`/`detail:"string | null"`/`last_state_version:"number | null"`) → **24→25 wire types**.
- **codegen** (`scripts/codegen/generate_event_schemas.py`): added `"loop_terminated": "LoopTerminatedEvent"` to `WIRE_TYPE_TO_INTERFACE`, then ran it → regenerated `loopEvents.generated.ts` (`LoopTerminatedEvent` + the `LoopEvent` union + `KNOWN_LOOP_EVENT_TYPES`) + `events.json`.
- **`chatStore.ts`** `mergeEvent`: new `case "loop_terminated"` — flips any dangling pending `ToolBlock` in the active turn to `status:"error"` (output `terminated: {reason}` — the stuck-chip fix), records `turn.terminated = {reason, detail}` + `waiting:false`, and sets chat `status:"completed"` (the proven `loop_end` unfreeze path — no new status enum) so the composer re-enables.
- **`types.ts`**: `AgentTurn += terminated?: {reason; detail?}`.
- **`AgentTurn.tsx`**: head renders `<span className="badge danger">terminated · {reason}</span>` when `turn.terminated` — reuses the EXISTING `.badge.danger` class (`styles-mockup.css:526`, `var(--danger)` + already-counted oklch tints) → **0 new CSS / 0 new oklch literal** (`HEX_OKLCH_BASELINE` 51 unchanged; `styles-mockup.css` byte-identical).
- parity test (`test_event_wire_schema_parity.py`): `LoopTerminated` moved UNWIRED→WIRED, count `==24`→`==25`. Two other hardcoded `24` count assertions also bumped: `eventSchema.generated.test.ts` (`.size).toBe(25)` + a recognition test) and `test_loop_start_active_skill.py` (renamed `test_active_skill_is_field_not_wire_type`, `==25`).

NOT done (deferred): a richer mockup-authored `TerminatedBlock` component; the resume-path terminate surfacing; a new loop/turn `status` enum value.

## Verification
- Gates: mypy `src` **0/372** · run_all **10/10** (wire **25** — `check_event_schema_sync` green) · backend pytest **2727 passed / 5 skipped** · Vitest **908** (+4: 3 `mergeEvent` cases + 1 recognition) · `npm run build` clean · lint clean · `check:mockup-fidelity` **51** byte-identical · black/isort/flake8 clean.
- **Drive-through PASS** (real chat-v2 UI + real backend + real Azure gpt-5.2, jamie@acme.com/acme-prod): a `web_search` call with `BING_SEARCH_API_KEY` unset → `WebSearchConfigError` → unregistered → FATAL → `LoopTerminated(fatal_exception)` mid-tool → the UI flipped the pending `web_search` chip to **error** (output `terminated: fatal_exception`), rendered the **`terminated · fatal_exception`** danger badge, dropped the running live-dot, and re-enabled the composer. Screenshot `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-130/artifacts/` (via `.playwright-mcp/drivethrough-57130-loop-terminated-PASS.jpeg`). The render is end-to-end proof (serializer → codegen → mergeEvent all exercised live).

## Impact
Cross-stack (backend SSE serializer + wire registry + codegen; frontend store + 1 turn field + 1 render + tests). NO migration / new backend primitive / new CSS class. A fatal terminate now surfaces a reason + clears the stuck chip + unfreezes the composer instead of hanging silently.
