# CHANGE-131: Tool-error taxonomy surfaced in chat-v2 UI (reachable via terminate-path emit)

**Date**: 2026-07-10
**Sprint**: 57.164
**Scope**: 範疇 2 (Tool Layer) + 範疇 1 (Orchestrator Loop) + chat-v2 frontend — backend + FE (NO migration / NO new wire event type)

## Problem

Sprint 57.144 added a 5-value tool-error taxonomy (`ErrorTaxonomy`) + set `ToolResult.error_taxonomy` on failures, but it had **no UI surface**: it stopped at the backend `ToolResult`, never reached the SSE wire, and 0 frontend files referenced it. A human debugging a failed tool in chat-v2 saw only the raw error + a red "error" badge, not the typed diagnosis (parameter / wrong_tool / failed_api / invocation / unknown). Closes the Tool-range carryover **③3 `AD-Tool-Error-Taxonomy-UI`** (57.144).

## Root Cause

The taxonomy stopped at `ToolResult` (`_contracts/tools.py:155`); the `ToolCallFailed` loop event (`_contracts/events.py`) had no taxonomy field; the loop's 2 emit sites dropped it; `sse.py`'s `tool_call_result` frame + the wire schema + the FE `ToolBlock` all lacked it. Additionally it was only computed under the `CHAT_TOOL_ERROR_REFLECTION` lever (default OFF), so it would have been empty in normal operation.

## Solution

Three coupled parts (user AskUserQuestion decisions 2026-07-10):

1. **Option B decouple** — `classify_tool_error` now runs on EVERY tool failure (`executor._build_failure` + the rare `loop.py:3068` path); the `CHAT_TOOL_ERROR_REFLECTION` lever gates ONLY the LLM-visible `content` reflection (the evidence-first thing 57.144/57.163 A/B-measured). `error_taxonomy` is display metadata no LLM reads → agent behavior byte-identical whether the lever is on or off; `content` stays empty when OFF.

2. **Wire the taxonomy** (additive field on the EXISTING `tool_call_result` type — wire-TYPE count stays 26): `ToolCallFailed += error_taxonomy` → loop 2 emit sites (`_run_turns` + resume) → `sse.py` BOTH branches (`ToolCallExecuted`=None / `ToolCallFailed`=value, same field set for the shared type so `test_event_wire_schema_parity` stays green) → `event_wire_schema.py` → codegen regen (`loopEvents.generated.ts` + `events.json`). FE: `ToolBlock += errorTaxonomy?` → `chatStore` `tool_call_result` capture → a conditional `.badge danger` chip on the ToolBlock head (existing mockup primitive, no new CSS; renders only when present).

3. **Reachability fix (drive-through-discovered; Option a)** — the drive-through revealed the chip was NOT reachable on the live 主流量: a Cat-8 FATAL tool failure (`loop.py:3113` dominant / `:3028` rare) `yield LoopTerminated` + `return` BEFORE the `ToolCallFailed` emit (`:3172`), so the human saw only `loop_terminated` (the 57.130 "terminated" flip), never the chip. Fix: emit `ToolCallFailed(+error_taxonomy)` before `yield LoopTerminated` at BOTH terminate sites (dominant uses `result.error_taxonomy`; rare classifies from `exc`). FE unchanged — `loop_terminated` only flips `status==="pending"` tools, so the already-`error` ToolBlock keeps its chip + real error output while the turn gets the `terminated` badge.

## Verification

- **Gate**: mypy `src` 400/0 · run_all 11/11 (incl. `check_event_schema_sync`) · black/isort/flake8 clean · backend pytest **3231 passed, 5 skipped** (+1 vs 57.163 baseline 3230) · Vitest **933** (+3) · `npm run lint && npm run build` clean (NO `--silent`) · mockup **51** (`styles-mockup.css` byte-identical).
- **Drive-through PASS** (real chat-v2 + real backend + real Azure gpt-5.2, lever OFF, session `3829811e`): `get incident INC-99999` → `mock_incident_get` → mock **404** → loop trace `tool_call_request → span → tool_call_result · ERROR → loop_terminated`; the ToolBlock renders **`tool error taxonomy: failed_api`** (httpx 404 → FAILED_API, label real) + the real 404 error output + a `terminated` turn badge. Success/pending tools show NO chip. Screenshots in `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-164/artifacts/` (`…PASS-taxonomy-chip.png` + the pre-fix `…terminated-not-chip.png`). Bonus verified live: HITL approval gate + Approve flow; memory recall.

## Impact

- Backend (Cat 2 decouple + Cat 1 terminate-path emit) + chat-v2 FE. No migration, no new wire event type (field-add on `tool_call_result`, count 26), no new CSS. Agent behavior unchanged (no LLM reads `error_taxonomy`; the loop's LLM-visible `content` is untouched).
- **Reality finding (recorded)**: on the live chat 主流量, tool failures are classified Cat-8 FATAL (httpx 4xx, generic/schema Exception) or TRANSIENT-then-exhausted → they terminate the loop. The taxonomy chip is now reachable for these BECAUSE 57.164 emits a `ToolCallFailed` before the terminate. A tool failure classified NOT-terminate (LLM_RECOVERABLE) reaches the normal `:3172` emit and also shows the chip.
- Closes ③3 (3 of ~4 Tool-range ADs done; ③2 `AD-Tool-Description-AutoFix` rolls to 57.165).
- NO design note (feature sprint, not a spike).
