# CHANGE-083: Skills force-load Inspector affordance — user-turn "active skill" chip

**Date**: 2026-06-14
**Sprint**: 57.116
**Scope**: chat API (Cat 12 wire / Cat 5 skills surface) + chat-v2 frontend
**Closes**: `AD-Skills-Inspector-Affordance`

## Problem

Sprint 57.115 shipped a deterministic `/skill-name` force-load: the picked skill's instructions are injected into the turn's system prompt server-side, and the model follows them WITHOUT calling `read_skill`. The force-load works, but after send it is **invisible** — the `/token` is stripped from the message body and (by design) there is no `read_skill` tool call to surface in the timeline. The model-invoked path (57.113) has no such gap (`read_skill` rides the visible Cat-2 tool stream). `AD-Skills-Inspector-Affordance` asked for a visible affordance.

## Root Cause

Force-load is a chat-API / Cat-5 concern that never reaches the timeline: the loop only ever receives a `system_prompt` string (it has no concept of "skill"), and the router strips the `/token` from the user message before the run. Nothing on the wire told the frontend a skill was active.

## Solution

A **server-confirmed** `active_skill` field on the run's opening `loop_start` SSE event drives a small chip on the user turn:

- **Wire (additive, count stays 24)** — `api/v1/chat/sse.py` `LoopStarted` serializer defaults `data.active_skill = None`; `api/v1/chat/event_wire_schema.py` declares `loop_start.active_skill: "string | null"` (drives codegen + the `test_event_wire_schema_parity.py` guard); `scripts/codegen/generate_event_schemas.py` regenerates `loopEvents.generated.ts` (`LoopStartEvent.data.active_skill: string | null`). No new event TYPE.
- **Router augment** — `api/v1/chat/router.py` `_stream_loop_events` gains an `active_skill` param (passed `=forced_skill`, the validated 57.115 value); after `serialize_loop_event`, it injects the confirmed name onto the `loop_start` frame (`if active_skill and isinstance(event, LoopStarted): payload["data"]["active_skill"] = active_skill`). `LoopStarted` was added to the events import. **`loop.py` / `events.py` / the `LoopStarted` dataclass / `read_skill` / `_stream_resume_events` UNTOUCHED** — skill knowledge stays out of Cat 1. The resume mirror passes nothing → `null`.
- **Frontend** — `chat_v2/types.ts` `UserTurn += activeSkill?`; `chat_v2/store/chatStore.ts` `mergeEvent` `loop_start` case stamps the LAST user turn's `activeSkill` from `ev.data.active_skill`, **only when truthy** (a `null` never overwrites — resume-safe); `chat_v2/components/turns/UserTurn.tsx` renders a `.route-pill` "⚡ {skill}" chip in the `.turn-head` (reuses the 57.101 `injected`-tag pattern; no new colour literal). The FE chips from the SERVER value, NOT the sent `force_load_skill` (an invalid name the FE sent must not produce a chip).

Build-time: the generated `active_skill` is a REQUIRED field → a demo fixture literal (`orchestrator-loop/_fixtures/demoLoopEvents.ts`) needed `active_skill: null` and the `loop_start` store map needed proper union narrowing (caught by `tsc -b`, not the Vitest transform).

## Verification

- **Unit/integration**: `test_loop_start_active_skill.py` (×4 — serializer default null / wire-schema key / count 24 unchanged); `test_chat_e2e.py` (+3 SSE — `force_load_skill=code-review` → `loop_start.active_skill=="code-review"`, none → null, unknown → null); the `event_wire_schema_parity` guard stays green. FE Vitest `chatStore.activeSkill.test.ts` (×4 — stamp / null no-stamp / resume-safe / last-user-turn) + `UserTurn.skillChip.test.tsx` (×2 — present/absent).
- **Gates**: mypy 0/370 · run_all 10/10 (count 24, codegen regen) · pytest 2623+5skip (+7) · FE lint 0 · build ✓ · Vitest 869 (+6) · mockup-fidelity 51.
- **Drive-through (real chat-v2 :3007 + fresh repo-root backend + real Azure gpt-5.2, tenant acme-skills)** — ALL 3 cases PASS:
  - **A**: `/release-notes <task>` → user turn shows `⚡ release-notes` chip + output follows `## Summary/## Highlights/## Upgrade steps` + `read_skill` 0× (deterministic) + verification 0.99.
  - **B**: `/nonexistent …` → NO chip (router dropped → `active_skill:null`; not a client echo) + agent "OK".
  - **C**: plain message → NO chip + agent "4".
  - 3 user turns, only Leg A chipped (correct triggering-turn binding). Screenshots in `docs/.../sprint-57-116/artifacts/`.

## Impact

chat API wire (additive field on `loop_start`, count 24) + chat-v2 frontend (store stamp + 1 chip). No migration, no new event type, no design note (feature continuation of the Skills epic + the 57.108 additive-wire-field pattern). `loop.py` / `events.py` / `read_skill` / the resume mirror untouched. Closes the Skills epic's first UX affordance; an Inspector-panel metadata row, a per-`read_skill` chip, and a dedicated skill event stay deferred.
