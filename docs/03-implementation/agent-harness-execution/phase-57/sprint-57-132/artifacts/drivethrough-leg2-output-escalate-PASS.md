# Sprint 57.132 Leg-2 — output-escalate resume-replay drive-through (PASS)

**Date**: 2026-06-17 (follow-up to Sprint 57.132; closes carryover `AD-ChatV2-Resume-Replay-Drive-Through`)
**What**: The Leg-2 path 57.132 shipped but could only verify by unit test (the real-LLM `confidential` trigger was non-deterministic + content-filter-prone). This drive-through DRIVES it on the real chat-v2 UI + real backend + real Azure LLM + real DB, using a DETERMINISTIC benign escalate phrase.

## The corrected premise (the headline)

The 57.132 carryover stated *"No admin endpoint exists today for `escalate_output_phrases` (HarnessPolicy)"* and assumed Leg-2 would need a NEW controllable escalate-phrase admin surface OR a verification-fail fixture.

**That premise was wrong** — the surface already exists (`check existing before building`, same trap as the 57.134 Day-1 pivot):

- `PUT /api/v1/admin/tenants/{id}/harness-policy` already accepts `escalate_output_phrases: list[str] | None` — `backend/src/api/v1/admin/tenants.py:1671` (request), `:1809` (sparse store), `:1845` (cache invalidate).
- `handler.py:588-592` resolves the per-tenant override → `handler.py:639-642` wires it into `OutputKeywordEscalationGuardrail` (priority 5, when `hitl_manager is not None`).
- `OutputKeywordEscalationGuardrail.check` does a case-insensitive substring match (`escalation_keyword_detector.py:66-80`).

So Leg-2 was driveable with ZERO new code — set the escalate phrase to a benign, content-filter-safe word the LLM reliably emits (`paris`) instead of `confidential`.

## Deterministic trigger recipe (no code)

1. `PUT /admin/tenants/{acme-prod}/harness-policy` `{ "escalate_output_phrases": ["paris"] }` → 200, GET confirms (cache invalidated → next turn resolves it).
2. Ask *"What is the capital of France? Reply with just the city name."* → answer contains `Paris` → output guardrail `ESCALATE`.
3. Approve → `_replay_approved_output` delivers the held answer + persists it to the `messages` ledger (the Leg-2 fix).
4. Restore: `PUT {}` → clears the override (back to baseline all-null).

## Evidence (real UI via Playwright + dan@acme.com/acme-prod + real Azure gpt-5.2 + real PostgreSQL)

Session `e0ec3410-1f67-47e2-956f-5778e7c860f7`.

- **Pause held the answer (not delivered)**: HITL approval card — severity HIGH, **tool: —** (an OUTPUT-guardrail pause, not a tool pause), policy `always_ask`, **Rationale: `output matched escalation phrase: 'paris'`**, approval_id `b2809ca0-07ae-455e-b02f-c23e2631c249`. Loop: `llm_call → approval_requested risk=HIGH → state_checkpointed → loop_end stop=awaiting_approval turns=0`.
- **Approve & continue (UI) → replay**: turn `stop: end_turn`, answer **`Paris`** rendered; card shows **`Decision: APPROVED`**.
- **Leg-2 fix proven — held answer persisted AT RESUME**: `messages` Cat-3 ledger after approve = **2 rows**: `seq=1 user "What is the capital of France?…"` / **`seq=2 assistant "Paris"`**. Because the loop paused BEFORE delivery, `_run_turns`' end_turn persist never ran — the only path that writes `seq=2` is `_replay_approved_output` at resume. Pre-fix this row would be MISSING.
- **End-to-end rehydration**: follow-up *"How many letters are in the city you just named? Reply with just the number."* (POST sends only `{message, session_id}`, no history) → **`5`** + Verification passed (0.99). `5` is un-deducible without the rehydrated `seq=2 "Paris"`; the answer `5` does not contain `paris` so no second escalate. Final ledger = **4 rows**: `seq=1 user / seq=2 assistant "Paris" / seq=3 user / seq=4 assistant "5"`.

Verification command: `cd backend && PYTHONPATH=src python ../docs/.../sprint-57-132/artifacts/verify_ledger.py e0ec3410-1f67-47e2-956f-5778e7c860f7`.

Screenshot: `drivethrough-leg2-output-escalate-PASS.jpeg` (transcript: user prompt → resolved APPROVED output-escalate card → `Paris` → follow-up `5`).

## Verdict

Leg-2 (`_replay_approved_output` delivers + persists the held answer at resume) is now **drive-through verified** (was honestly labeled gate-only in 57.132). `AD-ChatV2-Resume-Replay-Drive-Through` CLOSED. No code change — the deterministic trigger used the existing per-tenant `escalate_output_phrases` admin surface.
