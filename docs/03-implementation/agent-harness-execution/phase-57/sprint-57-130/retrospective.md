# Sprint 57.130 Retrospective — chat-v2 LoopTerminated wire surface

**Closed** 2026-06-16. Branch `feature/sprint-57-130-chatv2-loop-terminated-wire-surface` (from `main` `b9334946`, post-#306). Closes `AD-LoopTerminated-Wire-Surface` (57.110 carryover). CHANGE-097; NO design note (cross-stack wire-surfacing, not a spike).

## Q1 — What shipped
A FATAL-terminated chat-v2 run now surfaces its `LoopTerminated` Cat-8 event instead of silently ending. Backend: `serialize_loop_event` branch + `WIRE_SCHEMA` entry (24→25) + codegen regen + parity test. Frontend: `mergeEvent` `loop_terminated` case (flip dangling pending `ToolBlock`→error = the stuck-chip fix; record `turn.terminated`; set status terminal = composer unfreeze) + `AgentTurn` danger badge (reuses `.badge.danger`, 0 new CSS) + tests. Pure cross-stack surfacing of an existing event — no new backend primitive / contract / migration / CSS class.

## Q2 — Estimate accuracy (calibration)
- Class **`chatv2-fatal-terminate-wire-surface` 0.55** (NEW, 1st data point) · **parent-direct** (`agent_factor` 1.0, 3-segment form).
- Bottom-up ~6.0 hr → class-calibrated commit ~3.3 hr (mult 0.55). Actual ~4.25 hr → **ratio ~1.29 (slightly OVER band-top 1.2)**.
- Over-run drivers (NOT the code — the cross-stack code itself was on-budget): (1) the **drive-through trigger hunt** — `python_sandbox` always returns `success=True` so it can't trigger a terminate; had to trace the Cat-8 FATAL-classification path + find which built-in tool actually RAISES (`web_search` on unset `BING_SEARCH_API_KEY`); (2) **two Day-0-missed drifts** that surfaced mid-implementation (the codegen interface map + the 3-location count-test bump) added rework.
- **Verdict**: KEEP 0.55 (single-data-point caution; the rollback rule needs 2 consec >1.20). If a 2nd `*-wire-surface` sprint also lands >1.20, re-point toward 0.65 — the variance is the drive-through-staging cost, which the bottom-up under-prices for "surface an existing event" sprints.

## Q3 — What went well
- The recon-first approach (2 Explore passes → file:line plan) made the cross-stack edit surgical; backend Day 1 was first-try green.
- The minimal render decision (reuse `.badge.danger` + flip ToolBlock to error, NO new `TerminatedBlock`/CSS) kept `styles-mockup.css` byte-identical + `HEX_OKLCH_BASELINE` 51 unchanged — zero mockup-fidelity risk.
- The TS `never`-default exhaustiveness guard FORCED the `mergeEvent` case to compile (caught at build, not runtime) — a good safety net for adding a wire type.
- The drive-through trigger, once found, was clean: no code/config change, just an unset env var + a `web_search` prompt → deterministic `fatal_exception` mid-tool = the exact dangling-chip scenario.

## Q4 — What to improve (Day-0 lessons → fold into sprint-workflow)
- **D-codegen-interface-map** (NEW): the event codegen has an EXPLICIT `WIRE_TYPE_TO_INTERFACE` dict — adding a wire TYPE needs that map updated too, not just `WIRE_SCHEMA`. The first codegen run hard-failed. **Lesson**: Day-0 Prong-2 for a NEW wire type must grep the codegen's interface-name map.
- **D-three-count-test-locations** (NEW): the hardcoded wire count `24` was asserted in THREE files (parity test + FE `eventSchema.generated.test.ts` + `test_loop_start_active_skill.py`), not one. Two surfaced only at the full-suite run. **Lesson**: Day-0 Prong-2 for a wire-count change must grep `== 24` / `.size).toBe(24)` / `count.*24` across ALL test files (backend + frontend) upfront.
- Both are wire-count-change-specific; together they're a candidate "adding a wire event type" Day-0 checklist addendum.
- The drive-through trigger hunt reinforces `AD-DriveThrough-Deterministic-Tool-Trigger` (57.122) — a forced-tool-call harness would make terminate/guardrail drive-throughs trivial instead of requiring a real-tool-failure hunt.

## Q5 — Anti-pattern self-check
AP-1 N/A (no loop logic) · AP-2 ✅ (no orphan — `loop_terminated` reachable from the real loop emission → serializer → FE) · AP-3 ✅ (changes scoped to api/v1/chat + chat_v2) · AP-4 ✅ (this REMOVES an AP-4 Potemkin — the silent stuck chip; drive-through PASS proves it renders) · AP-6 ✅ (no speculative abstraction) · AP-8 N/A · AP-11 ✅ (no version suffix). v2 lints 10/10.

## Q6 — Gates
mypy `src` **0/372** · run_all **10/10** (wire **25**, `check_event_schema_sync` green, LLM-SDK-leak clean) · backend pytest **2727 passed / 5 skipped** · Vitest **908** (+4) · `npm run build` clean · lint clean · `check:mockup-fidelity` **51** byte-identical · black/isort/flake8 clean. **Drive-through PASS** (real Azure, web_search→fatal_exception→terminated badge + error chip + unfrozen composer).

## Q7 — Carryover
- **NONE new from the feature.** Deferred follow-on: a richer mockup-authored `TerminatedBlock` (the minimal danger badge is the real fix); the resume-path terminate surfacing.
- Pre-existing: `AD-Billing-Outbox-Drain-Test-Flake` (Risk Class C; did NOT surface this run); `AD-DriveThrough-Deterministic-Tool-Trigger` (reinforced).
- Bucket-C remaining (other 57.130-sibling carryovers, separate slices): `AD-ChatV2-Resume-Tool-RoundTrips`, `AD-ChatV2-HITL-Card-Tool-Name`, Inspector turn metadata, transcript retention.
