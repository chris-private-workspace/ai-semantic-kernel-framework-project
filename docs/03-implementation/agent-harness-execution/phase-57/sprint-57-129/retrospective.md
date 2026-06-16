# Sprint 57.129 Retrospective — chat-v2 ledger intra-turn tool round-trips

**Closed**: 2026-06-16 · **Branch**: `feature/sprint-57-129-chatv2-ledger-tool-roundtrips` (from `main` `858bd3af`) · closes `AD-ChatV2-Ledger-Tool-RoundTrips`

## Q1 — What shipped?
The loop now persists each turn's complete intra-turn tool round-trip (`assistant tool_use` + its `tool` results) to the `messages` Cat-3 ledger, so a follow-up send rehydrates the FULL tool context (not just `[user, final-answer]`). One marker + one `_persist_to_ledger` call in `_run_turns`'s `TOOL_USE` branch (after the post-tool checkpoint), reusing `DBMessageStore.append` + `message_serde`. Pure backend: 1 src EDIT (`loop.py`) + 1 test EDIT. CHANGE-096; no design note (continuation of the 57.127 ledger).

## Q2 — Estimate accuracy / calibration
- Class **`chatv2-ledger-tool-roundtrips-wiring`**, parent-direct, `agent_factor` 1.0 (3-segment).
- Bottom-up ~4.75 hr → class-calibrated commit ~2.6 hr (mult **0.55**). **Actual ~5.0 hr → ratio ~1.9 OVER band.**
- The CODE + tests were on-budget (~1.5 hr; the change is ~2 lines + docstring + 3 tests). The over-run was entirely the **Day-3 drive-through**: clean restart + HITL-policy setup (to make python_sandbox auto-run in-loop) + multiple real-LLM chat cycles + DB-verify scripts + a **content-filter false-alarm root-cause investigation** (~1-1.5 hr). Even excluding the false-alarm detour, the base drive-through alone → ratio ~1.35 (still over).
- **Re-point 0.55 → 0.85** (1st data point). Same ceremony-not-code-accelerated insight as 57.120 `chatv2-inspector-existing-field-surface` / 57.122 `harness-loadbearing-gap-fix` / 57.123 `frontend-fixture-to-real-data-wiring` / 57.126 `chatv2-history-replay-fullstack`: a tiny-code, full-ceremony, parent-direct sprint WITH a mandatory drive-through does NOT land in the 0.45-0.55 band — the fixed-cost drive-through (here amplified by the HITL-policy setup + the recall-prompt content-filter investigation) dominates. If a 2nd `chatv2-ledger-tool-roundtrips-wiring` lands < 0.7 at 0.85, lower again.

## Q3 — What went well?
- Day-0 三-prong was decisive: the marker-placement + no-other-appends-in-window + early-return greps pinned the exact 2-line surgical change with zero mid-sprint surprise; gates green first try (mypy 0, run_all 10/10, pytest 2727+5).
- The drive-through design (tool result NOT in the final answer → a follow-up that recovers/uses it) gave an UNAMBIGUOUS end-to-end proof: turn 2 computed `333228` (= the rehydrated `333221` + 7) with the POST sending only {message, session_id}.
- DB ledger + live SSE `messages_count=8` together proved persist + rehydrate at the mechanism level (independent of LLM behavior).

## Q4 — What to improve / lessons?
- **Drive-through recall prompts must be natural, not adversarial.** My first recall prompts ("**Disregard** the earlier 'do not reveal' instruction", "do not reveal the number", "recall it … do NOT run any tool") tripped Azure's content filter (`400 content_filter` `jailbreak: detected`), producing EMPTY follow-up turns that LOOKED like a rehydration regression. A no-tool control follow-up (Paris→population) worked, and the backend log line 212 revealed the 400 → confirmed NOT a regression. **Lesson (worth carrying): test rehydration recall with innocent follow-ups ("add 7 to that number"), never override/disregard/withhold phrasings.** ~1-1.5 hr cost.
- **HITL-policy-setup is part of the drive-through cost** for any tool-execution feature: `python_sandbox` is MEDIUM and the default policy escalates it (→ resume() path, which is the DEFERRED sub-carryover, NOT this fix). Had to set acme-prod `auto=MEDIUM/require=HIGH` so the tool auto-runs in-loop. Budget this for future tool-flow drive-throughs.
- The `messages_count` from the live SSE `prompt_built` event is a clean, mechanism-level rehydration probe — more reliable than waiting for the LLM to behave.

## Q5 — Anti-pattern self-check (11)
- AP-1 (loop not pipeline): N/A (persist site in the existing while-loop). ✅
- AP-2 (no orphan / on 主流量): the persist fires in the live `_run_turns` TOOL_USE path, drive-through-proven LIVE. ✅
- AP-3 (no cross-dir scatter): one `_persist_to_ledger` reused; no duplicate writer. ✅
- AP-4 (no Potemkin): real tool-context rehydration proven by the live drive-through (333228) + DB ledger. ✅
- AP-6 (no for-future abstraction): reuses the existing helper/ABC/serde; no new abstraction. ✅
- AP-8 (PromptBuilder): N/A (no prompt assembly change). ✅
- AP-11 (no version suffix): none. ✅
- v2 lints 10/10. **0 violations.**

## Q6 — Carryover
- **`AD-ChatV2-Resume-Tool-RoundTrips`** (NEW sub-carryover) — resume()'s pending-tool observation is appended before driving `_run_turns` → not captured by the `TOOL_USE` marker → a HITL-paused-then-approved tool's round-trip isn't persisted. Niche; deferred.
- Pre-existing: `AD-Billing-Outbox-Drain-Test-Flake` (intermittent Risk Class C; did NOT surface this sprint); deferred infra (`message_events`/`messages` consolidation; pg_partman; `turn_num` cross-send counter).

## Q7 — Gate summary
mypy `src` 0/372 · run_all 10/10 (wire 24) · full pytest 2727 passed / 5 skipped (+3) · black/isort/flake8 clean · LLM-SDK-leak clean · frontend untouched (Vitest 904 / mockup 51 UNCHANGED) · **drive-through PASS** (real UI + backend + Azure gpt-5.2; session 9150a32f; turn 2 used the rehydrated tool result).
