# CHANGE-075: chat-v2 HITL card real tool/reason + Inspector turn metadata wire

**Date**: 2026-06-12
**Sprint**: 57.108
**Scope**: Cat 1 (yield sites) × api/v1/chat (wire) × Frontend chat_v2 (store)

## Problem

Two honest-but-unwired chat-v2 surfaces (ISSUE-5 + the 57.106 drive-through finding):
the HITL approval card rendered `tool: —` for every `approval_requested` (a reviewer
could not see WHICH tool wanted approval or WHY), and the Inspector turn pane's
trace_id / span_id / tokens.out / duration always fell back to "—" (initialized null,
never populated). Neither was a Potemkin (FIX-030 analysis) — but both blocked the
reviewer/observability workflow.

## Root Cause

- `ApprovalRequested` never carried tool/reason to the wire — the data existed
  (ApprovalRequest DB payload stores both) but the LoopEvent had no fields.
- FE chatStore hardcoded `tool: "—"` / `rationale: "—"` / `traceId: null` instead of
  reading frame data; `LLMResponded` token actuals were never serialized; no
  `turn_end` event exists so `durationMs` had no producer.

## Solution

Additive wire fields only — event count stays 24, no new event type, no DB change:

- `ApprovalRequested` += `tool_name: str | None` + `reason: str` (events.py); all 5
  loop.py escalate yields pass `reason=` (in-scope local); the tool site (:1048) also
  passes `tool_name=tc.name`. Wire + sse serializer extended; codegen regenerated.
- `llm_response` wire += `input_tokens`/`output_tokens` (LLMResponded already carried
  them; completes the 57.65 `cached_input_tokens` pattern).
- chatStore (4 captures, ZERO component edits — HITLTurn/InspectorTurn are
  store-driven): approval tool/rationale; turn_start `trace_id` + TURN-span link
  (**D9**: SpanStarted(TURN) precedes TurnStarted, so linking happens at turn_start
  from the newest running TURN span — linking in span_started would attach to the
  previous turn); llm_response token actuals (overwrite-when->0 — D1: one LLM call
  per TAO turn; 0/absent keeps the honest "—"); span_ended TURN fills `durationMs`.
- NOT wired by design: `cost` (post-loop in cost_ledger; the cost dashboard is its
  surface) + `tokens.thinking` (no server-side counter). They keep the honest "—".

## Verification

Backend: 5 escalate-site assertions extended + sse defaults/tool-context/token tests
(`test_loop_pause_resume.py` / `test_sse.py`); full pytest 2462+4skip (+2, 0 del);
mypy 0/359; run_all 10/10 (count 24 unchanged). FE: mergeEvent Vitest 46→54 (+8);
Vitest 836 (+8, 0 del); build ✓; mockup-fidelity 51==51. Drive-through: see
sprint-57-108 progress.md (real UI + real backend + real Azure; tool-escalate card
reality + Inspector reality).

## Impact

Cross-stack additive (backend wire + FE store). Old frames degrade honestly ("—").
`loop.py` diff = 5 yield kwargs + header. `demoLoopEvents.ts` fixture gained the new
required literals (type-contract ripple, 57.66 precedent). Closes
`AD-ChatV2-HITL-Card-Tool-Name` + `AD-ChatV2-Inspector-Turn-Metadata-Wire`.
