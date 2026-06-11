# CHANGE-067: chat-v2 verification-reject UI (the A2 follow-up)

**Date**: 2026-06-10
**Sprint**: 57.100
**Scope**: Frontend (chat-v2 HITL) × Cat 12 (event wire) × Cat 9 (HITL) — backend touch is a thin additive wire field

## Problem

Sprint 57.99 (A2) shipped the verification-ESCALATE backend: on max-attempts the loop pauses for a human; APPROVE delivers the held answer; **REJECT-with-note re-injects the reviewer note and runs exactly one human-coached turn** (`loop.py` `resume()` `kind="verification"`). The 57.99 drive-through proved the APPROVE half through the real UI, but found the REJECT half is **not UI-drivable**: the chat-v2 HITL card (`HITLTurn.tsx`) was built for the tool-approval shape — APPROVE resumes (since 57.88), but REJECT is hardcoded to *terminate* (no resume, no note input), and the card cannot tell a verification pause from a tool pause because the `approval_requested` SSE wire carries only `approval_request_id` + `risk_level` — **no `kind`**.

## Root Cause

The pause `kind` ("tool"/"input"/"between_turns"/"output"/"verification") already exists in the persisted `ApprovalRequest` (built by each pause method's `pending_approval["kind"]`), but the `ApprovalRequested` event + its SSE serializer never surfaced it. Without `kind` on the wire, the frontend has no honest signal to distinguish a verification pause — and event-ordering inference (treat the pause as verification if preceded by a `verification_failed`) is a fragile Potemkin heuristic (AP-4) that breaks the moment a tool pause follows a verification turn.

## Solution

**Surface the pause `kind` on the `approval_requested` wire (additive — a field on an existing event type, NOT a new type → no event-count bump), then branch the chat-v2 reject behavior on it.**

Backend (thin, additive):
- `agent_harness/_contracts/events.py` — `ApprovalRequested` +`kind: str = ""`.
- `agent_harness/orchestrator_loop/loop.py` — the 5 `yield ApprovalRequested(...)` sites pass their real `kind=` (`:814` input / `:1030` tool / `:1433` between_turns / `:1596` output / `:1812` verification — each == its `pending_approval["kind"]`).
- `api/v1/chat/sse.py` — the `approval_requested` serializer +`"kind": event.kind`.
- `api/v1/chat/event_wire_schema.py` — the `"approval_requested"` entry +`"kind": "string"`.
- `scripts/codegen/generate_event_schemas.py` regen → `frontend/.../generated/loopEvents.generated.ts` `ApprovalRequestedEvent.data` gains `kind: string` (+ `events.json`). 22 wire types unchanged.

Frontend:
- `chat_v2/types.ts` — `HITLTurn` +`kind: string`.
- `chat_v2/store/chatStore.ts` — the `approval_requested` case sets `kind: ev.data.kind ?? ""`.
- `chat_v2/components/turns/HITLTurn.tsx` — `isVerification = turn.kind === "verification"`; `submitDecision(decision, note?)` passes `note` to `decide` + `shouldResume = approved || (rejected && isVerification)` (guarded on `awaiting_approval`); for verification, the Reject button reveals an optional coaching-note textarea (`reject-note` / "Reject & coach" `reject-confirm-btn`) → `decide(id, "rejected", note)` + `resume()`; every other kind rejects immediately (terminate — byte-identical); the meta row reads `kind: verification` instead of `tool: —`. The textarea uses confirmed mockup tokens (`--radius-sm`/`--border`/`--bg-1`/`--fg`) — no mockup source for this element, so design-system vocab only, no new HEX/oklch.

The reviewer note + the held answer + the verifier reason needed NO new wire: the note rides the existing `ApprovalDecision.reason` (decide already accepts it, 57.99); the held answer + verifier reason are already rendered by the existing chat-v2 `VerificationBlock` (chatStore `verification_failed` case) above the card.

## Verification

- Backend: mypy `src` 0/353 · run_all 10/10 (`check_event_schema_sync` green — field added, count unchanged) · black/isort/flake8 FULL `src tests` clean · `test_sse.py` 31 passed (+`test_approval_requested_carries_kind`, +`kind==""` default assert) · `test_event_wire_schema_parity.py` 32 passed (regen) · full suite green (see progress.md NET delta).
- Frontend: build (tsc -b) exit 0 (D-DAY2-1: a stale demo fixture `demoLoopEvents.ts` was caught at COMPILE time — the required field surfaced the only stale construction site) · lint clean · `check:mockup-fidelity` HEX_OKLCH baseline 53 unchanged · Vitest 782 passed (+5: 3 HITLTurn verification cases + 2 chatStore kind cases).
- **Drive-through** (the REJECT half — the 57.99 drive-through did only APPROVE): see progress.md Day-3 + screenshots in `sprint-57-100/artifacts/`.

## Impact

Frontend chat-v2 + a thin additive backend wire field. `resume()` / `ApprovalDecision` DTO / `governanceService` / DB / migration / `ApprovalCard.tsx` (legacy fallback) / `ModelProfile` diff = 0. The wire field is REQUIRED on the generated type (so any stale construction site fails at compile time — intended type-safety); existing tool/input/between_turns/output reject behavior is byte-identical (verification-gated). Feature-continuation → NO new design note; record = this CHANGE-067 + 17.md (`approval_requested` wire +kind) + 25.md §4 (the A2 reviewer UI → SHIPPED).
