# CHANGE-074: B3 HANDOFF finish — stub retirement + LLM-drivable handoff + governance + lineage list + sidechain transcripts

**Date**: 2026-06-12
**Sprint**: 57.107 (harness-deepening Workflow B slice B3)
**Scope**: Cat 11 (Subagent) × platform_layer (handoff/governance) × api (chat/sessions/admin) × infrastructure (migration 0028) × frontend (chat-v2 + tenant-settings)

## Problem

Four B3 gaps (proposal §2.4): (1) the `HandoffExecutor` UUID stub trio was dead on 主流量
(AP-2/AP-11) AND — Day-0 finding — the chat path never registered a `handoff` ToolSpec,
so a **real LLM could never trigger** the 57.68-70 handoff machinery; (2) no per-tenant
handoff governance (any persona always boots); (3) no sessions list API — the chat-v2
SessionList was fixture (`AD-ChatV2-SessionList-Backend`) and the `handoff_parent_id`
lineage was invisible; (4) FORK/TEAMMATE child transcripts were ephemeral
(`AD-Subagent-Transcript-Isolation`) — `messages`/`message_events` had ZERO writers,
and (Day-0 D4) their month partitions ended at `2026_06` → both tables un-writable
from 2026-07-01.

## Solution

- **US-1**: stub trio DELETED (`modes/handoff.py` + `dispatcher.handoff()` + ABC method
  + `make_handoff_tool`); NEW spec-only `make_handoff_spec(suggested_targets)` registered
  on the real_llm executor (handler raises if invoked — the loop classifier intercepts
  pre-execution). 17.md rows updated.
- **US-2**: `HarnessPolicy` 9→11 (`handoff_enabled` tri-state + `handoff_target_allowlist`);
  double-gate: spec registration (tool absent when Off) + `boot_handoff(allowed_targets=)`
  off-list reject BEFORE any write (router fail-soft); admin PUT 422 poles + FE tab 9→11.
- **US-3**: `SessionRepository.list_sessions` + `GET /api/v1/sessions` (lineage fields;
  sidechains excluded) + chat-v2 SessionList real-data + `↳ {agentRole}` chain badge
  (FIXTURE_SESSIONS deleted). Closes `AD-ChatV2-SessionList-Backend`.
- **US-4**: migration `0028_sidechain_sessions` (`parent_session_id` + `is_sidechain` —
  CC parentUuid/isSidechain borrow — + partial index + **DEFAULT partitions** for
  messages/message_events, the D4 time-bomb fix); router `_persist_subagent_transcript`
  observer (Spawned → sidechain session; ChildEvent → `message_events` FIRST writer,
  monotonic seq; Completed → summary/tokens). Closes `AD-Subagent-Transcript-Isolation`.

## Verification

Gates: mypy `src` 0/359 · flake8 0 · run_all 10/10 (event count UNCHANGED) · full pytest
**2460+4skip (+21, 0 del)** · FE lint 0 / build / Vitest 828 / mockup-fidelity
(baseline ratcheted 53→51). **Drive-through ALL 4 legs PASS** (real UI + fresh no-reload
backend + real Azure gpt-5.2, zero dev-login): first-ever real-LLM handoff (tool call →
`stop=handoff` → child boot → `agent_handoff` SSE → banner + ↳ badge) · allowlist
spec-layer steering observed live (LLM chose the only allowed target) · `handoff_enabled=
Off` → tool absent → `end_turn` (LLM fell back to task_spawn) · sidechain transcript
DB-probed (session `709ded76…` + 6 `message_events` rows). Screenshots:
`sprint-57-107/artifacts/dt57107-*.png`.

## Impact

Backend (Cat 11 + platform + api + 1 migration) + frontend (chat-v2 + tenant-settings).
`loop.py` / wire schema / event count UNTOUCHED. No-policy tenants: handoff defaults ON
with the 3 default personas (was: impossible) — the only intentional behavior change.
