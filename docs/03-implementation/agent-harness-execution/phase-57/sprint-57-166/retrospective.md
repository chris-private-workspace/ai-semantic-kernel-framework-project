# Sprint 57.166 Retrospective — cross-burst turn/token aggregate in the final `loop_end`

**Date**: 2026-07-22 · **Branch**: `feature/sprint-57-166-burst-stats-aggregate` · **Base**: `main` `3395b4a1`

---

## Q1 — What shipped

Closes the task-primitive-range carryover **`AD-Scheduler-Burst-Stats-Aggregate-Phase58`** (57.157). The scheduler runs the loop across N bursts, each emitting its own `LoopCompleted`; the intermediate ones are swallowed, so the surviving terminal `loop_end` reported only the **last** burst — a 7-turn / 3-burst run told the human "2 turns" and wrote the same understatement into the `conversation_completed` audit row.

Fix (4 surgical edits inside `_stream_loop_events`, `api/v1/chat/router.py`): 4 accumulators before the `async for` → `+=` on every `LoopCompleted` (swallowed + final) → patch `total_turns` on the **final** frame only → audit `operation_data` 4 counters read the aggregates. **Billing deliberately untouched** (still per-burst `event.*`). No migration / no wire change / no frontend change / no `agent_harness/` change. New test file `test_scheduler_burst_stats.py` (4 tests). CHANGE-135.

## Q2 — Estimate accuracy / calibration

- Plan: bottom-up ~4.25 hr → class-calibrated commit **~2.6 hr** (class `scheduler-cross-burst-spike` **0.60**, `Agent-delegated: no` → `agent_factor` 1.0, 3-segment form).
- Actual ≈ **5.0–5.5 hr** → ratio ≈ **1.9–2.1** — well outside the band.
- **Where it went**: code + tests + gate landed roughly on estimate (~2.5 hr for a ~2.5 hr slice). The whole overrun is **Day 3 drive-through**: budgeted 1.5 hr for one leg, actually took **6 legs across 2 sessions** (~2.5–3 hr). Two independent determinism blockers, neither foreseeable from the plan: (a) real `gpt-5.2` refuses to self-loop on a tool-only prompt (*"I can't keep calling write_todos turn after turn on my own"*) so the `max_turns` ceiling is never reached by persuasion alone; (b) once the ceiling *was* forced, burst 2 froze at the `python_sandbox` HITL approval gate with 0 completed turns, making the sum indistinguishable from last-burst-only.
- **Action (per the class note "if a 2nd scheduler-\* lands > 1.20 → 0.70")**: re-point `scheduler-cross-burst-spike` **0.60 → 0.70**. Note the 57.157 (1st pt, ~1.15–1.3) and 57.166 over-edges have the **same shape** — both were drive-through environment/determinism detective work, not code mis-estimation. The class's real signal is: *scheduler slices need a deterministic-run lever budgeted up front*, not more code hours.

## Q3 — What went well / key lesson

- **Day-0 Prong 2 paid for the whole design.** `D-billing-per-burst-ungated` (the enqueue is a standalone `if`, NOT gated on `_swallow`) is precisely what ruled out the obvious implementation — mutating the event to hold the aggregate — which would have silently **double-billed** burst 1 inside burst 2's row. A ~5-minute grep prevented a revenue-correctness bug that no unit test would have been written for. T4 then locked it in.
- **Two read-sites, one aggregate, zero event mutation** kept the change additive: single burst → `agg == event.*` → byte-identical, proven by T3 + the 27 untouched chat-integration tests.
- **Key lesson — "the drive-through needs a determinism lever, and the lever needs an exit plan."** Both blockers were solved by *temporary* levers (`max_turns` 8→2 in code; `HITL_ENABLED=false` in env), user-approved before use, and both reverted immediately after with proof (`git diff` empty; backend restarted with no flags). Sprints whose acceptance depends on a *rare* runtime path should budget the lever in the plan, not improvise it on Day 3.

## Q4 — What to improve next

- **Plan the lever at Day 0.** When acceptance needs a rare path (ceiling hit / N-th burst / a specific stop_reason), name the lever + its revert proof in plan §Risks up front. Would have collapsed 6 legs into ~2.
- **Record inconclusive legs as inconclusive.** Leg 1 was tempting to read as a pass (2 = 2+0, and last-burst-only would have shown 0) — but "consistent with the fix" is not "distinguishes the fix". It is written up as **inconclusive**; only Leg 3 (7 vs a per-burst ceiling of 2) is arithmetically decisive. New AD below.
- The `total_turns` semantics across a HITL-`awaiting_approval` burst (contributes 0) is worth a look — see carryover.

## Q5 — Anti-pattern self-check

| AP | Verdict |
|----|---------|
| AP-1 Pipeline-as-loop | N/A — no loop control-flow change |
| AP-2 Side-track | ✅ on the 主流量 `_stream_loop_events` path; reachable from `POST /chat/{id}/messages` |
| AP-3 Cross-directory scatter | ✅ 1 production file |
| AP-4 Potemkin | ✅ drive-through PASS on real UI + real LLM (badge 7 == audit 7); 2 non-decisive legs labelled inconclusive, not "verified" |
| AP-6 Speculative abstraction | ✅ 4 plain locals; no new class/ABC/flag |
| AP-8 PromptBuilder bypass | N/A — no LLM call added |
| AP-11 Version suffix | ✅ none |

v2 lints **12/12**.

## Q6 — Carryover

- **NEW `AD-Scheduler-Burst-CacheRate-Aggregate`** — `cached_input_tokens` (summable) and `cache_hit_rate` (a *rate* — needs weighted re-derivation, not a sum) on the `loop_end` payload are still last-burst-only.
- **NEW `AD-Scheduler-AwaitingApproval-Burst-Turn-Count`** — a burst that stops at a HITL gate reports `total_turns=0`, so the aggregate silently omits the partial turn. Confirm whether that is the intended semantics.
- **NEW `AD-DriveThrough-Determinism-Lever-Plan-At-Day0`** — codify "name the rare-path lever + revert proof in plan §Risks" (Q4).
- Unchanged from 57.157: `AD-Scheduler-{BurstWire,PerTenant,TokenBudget}-Phase58`.

## Q7 — Gate summary

mypy `src` **400/0** · `run_all` **12/12** · black / isort / flake8 clean · LLM-SDK-leak clean · scheduler + router + new = **48 passed** · chat integration **27 passed** · new tests **4 passed**. Pre-existing (`main`) `test_audit_log_observer` ×2 failures unchanged — out of scope per Day-0 `D-audit-observer-pre-existing-fails`.
