# CHANGE-126: Compaction live drive-through + Inspector timeline marker (Cat 4 L2→L3)

**Date**: 2026-07-07
**Sprint**: 57.159
**Scope**: 範疇 4 (Context Mgmt / Compaction) + Frontend chat_v2 (observability surface)

## Problem

The reality-audit (§3) assessed Cat 4 context compaction as **L2** — "真壓縮過 9824→2679 但只在 harness 級證實,plain Q&A 無機會觸發". Compaction had never been driven on a live chat-v2 conversation. Worse, the `context_compacted` event — fully wired loop→sse→wire→store — was left **rawEvents-only** in the chat-v2 store (`chatStore.ts:839-846`, "Rich Inspector render DEFERRED to A-5c"), so when compaction fired the token reduction rendered NOWHERE in the UI (only a bare `COMPACTION` span duration bar in the Trace tab). Compacting an invisible thing is weak 落地.

## Root Cause

Two gaps: (1) an observability gap — the store recognized `context_compacted` but never rendered it; (2) a verification gap — compaction was gate/harness-verified, never live-driven. The event's data (`tokens_before/after`, `compaction_strategy`, `messages_compacted`) was already on the wire (`sse.py:397`, `event_wire_schema.py`, `loopEvents.generated.ts`) since 57.66; only the render was missing.

## Solution

FE-only surface (ZERO backend/wire/codegen — the event is already wired):
- `types.ts` — `+CompactionMarkerTurn { role:"compaction"; tokensBefore; tokensAfter; strategy; messagesCompacted }` in the `Turn` union (Day-0 drift D-turn-union-shape: the type lives here, not chatStore.ts).
- `chatStore.ts` — split `case "context_compacted"` out of the rawEvents-only bucket → push a `CompactionMarkerTurn` into `turns` (mirrors the `message_injected` pseudo-turn); rawEvents retained. Fires before `turn_started` → marker precedes the turn it enabled.
- `turns/CompactionMarker.tsx` (NEW) — a slim centered timeline marker "⚡ Context compacted · 9,824 → 2,679 tokens (hybrid · 12 msgs)" using the mockup `.badge.warning` chip (compaction == warning, matching `InspectorTrace.tsx:70`); NO new CSS/HEX/oklch.
- `TurnList.tsx` — `role==="compaction"` dispatch branch.
- i18n common.json DROPPED (the surrounding turn components use English literals not i18n — match-surrounding-code).
- Tests: `chatStore.mergeEvent.test.ts` (+1) + `components/CompactionMarker.test.tsx` (NEW).

Location: `frontend/src/features/chat_v2/`. PR: (pending). No design note (existing-field-surface + drive-through, not a new-domain spike; mirrors 57.120/131/133).

## Verification

- **Gates**: Vitest 927 (925 **+2**) · lint `LINT_EXIT=0` · build (tsc+vite) clean · mockup-fidelity 51 byte-identical · mypy `src` 400 / run_all 11/11 (backend UNTOUCHED).
- **Drive-through (MANDATORY, real chat-v2 + backend + Azure gpt-5.2)** — Cat 4 L2→L3:
  - US-1: the CompactionMarker rendered LIVE — 8 markers on a long tool-using send (`4,086→4,086` … `35,144→35,144`) + a **real reduction** `4,604 → 1,770 tokens (hybrid · 8 msgs)` (−62%, `keep_recent=1` drive). Previously invisible.
  - US-2: after multiple compactions the agent recalled early context correctly — "Aurora / Oracle→PostgreSQL / NUMBER(38,4) top risk" (0.99) + "Beacon / October / Lodestar" (0.99). Compaction preserved meaning.
  - Artifacts: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-159/artifacts/sprint-57-159-leg{1,2,3}-*.png`.

## Impact

Frontend-only (chat_v2 observability); ZERO backend/wire/codegen/migration. Raises Cat 4 L2→L3 (compaction now driveable + visible). 

**L2→L3 finding (carryover, NOT a same-sprint fix)**: compaction TRIGGERS every over-budget turn but REDUCES 0 messages on the chat path unless `len(user_indices) > keep_recent_turns` (`structural.py:126`); a single-user-message send (even a 20-turn tool run) never reduces → context grows unbounded (4k→35k). Context is NOT lost (retention 0.99) → an effectiveness gap, not a correctness bug. Registered: `AD-Compaction-NoOp-On-Single-User-Turn-Chat-Path` (reduce within a long single-user-turn run — loop-turn-based masking / auto-tune keep_recent / default-on ACON preclear) + `AD-Compaction-Marker-Inspector-Trace-Correlate`.
