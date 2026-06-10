# Sprint 57.99 Retrospective — Verification-ESCALATE human-in-the-loop (A2)

**Sprint**: 57.99 (A2 — harness-deepening Workflow A, slice 2)
**Dates**: 2026-06-10 (Day 0-4, single session)
**Branch**: `feature/sprint-57-99-verification-escalate` (from `main` `be89d3ec` = A1 PR #272)
**Scope class**: `loop-pause-point-feature` (NEW, 0.50) · agent_factor 1.0 (parent-direct)

---

## Q1 — What was the goal, and was it met?

Goal: conditionally swap the A1 `verification_failed` terminal (Sprint 57.98) for a human ESCALATE
pause, behind a global toggle (default OFF = A1 byte-identical). On max-attempts: APPROVE delivers
the held failed answer (human overrides the judge); REJECT-with-note re-injects the note as a
correction and runs exactly ONE human-coached turn, then binds to the A1 terminal.

**Met.** All 6 US shipped + gate-green + the escalate→APPROVE path drive-through-verified through the
real UI/backend/Azure. REJECT-with-note is backend-complete + unit-proven; its UI-driving is a
documented chat-v2 frontend follow-up (a drive-through finding, user-confirmed Option A).

## Q2 — Estimate accuracy (calibration)

- Plan §Workload: **Bottom-up ~15 hr → class-calibrated commit ~7.5 hr (mult 0.50)**. Agent-delegated: **no** (parent-direct → `agent_factor = 1.0`; 3-segment form).
- Actual (AI-paced estimate, not human-hours): **~7 hr** → ratio `actual / committed ≈ 0.93` — **IN band**.
- The REJECT-with-note frontend gap SHRANK the drive-through (only the APPROVE half UI-driven; the REJECT half unit-proven) — a small reduction; the D-DAY3-1 stub fix + the D-DAY3-2 drive-through iteration added a little back. Net ≈ committed.
- `loop-pause-point-feature` 0.50 is the **1st data point** (the 57.92/93 retrospectives proposed this class ~0.40; A2 set 0.50 because it carries more than a pure pause leg — the bounded REJECT continuation + the held-answer snapshot + the durable flag). KEEP 0.50 pending 2-3 sprint validation.

## Q3 — What went well

- **Re-enterable `_run_turns` (57.89/90 payoff) + the A1 in-loop gate (57.98) made A2 small**: the escalate pause was a mirror of `_cat9_output_hitl_pause`; the resume APPROVE reused 57.93's `_replay_approved_output` verbatim; the conditional terminal was a guard + a method call, not loop surgery. 285 backend src lines across 3 files; NO new event / wire / DB / DTO / frontend.
- **The durable flag rode `metadata`** (the 57.98 `verification_attempts` precedent) — no migration, no `DurableState` field.
- **Day-0 three-prong verify** kept the plan anchored (swap point, resume branches, config cluster all confirmed pre-code).
- **The drive-through earned its keep twice**: it caught (a) the D-DAY3-2 confound (a tool-equipped agent ACTS on a forced fail) and (b) the REJECT-with-note frontend gap — neither visible to any gate.

## Q4 — What to improve / lessons

- **D-DAY3-1 (the recurring escape)**: a Day-1 `handler.py` settings read broke 2 Sprint-57.97 tests whose `SimpleNamespace` settings stub didn't carry the new attribute. The Day-1 scoped regression run (loop+verification+smoke) missed `test_handler.py`. **Lesson: when adding a `settings.X` read in a shared builder, grep for `SimpleNamespace`/`get_settings` stubs in the test tree at Day-0/Day-1, OR run the handler test file in the Day-1 regression set.** The Day-3 full sweep is the backstop that caught it (its value, reaffirmed).
- **D-DAY3-2 (real-agent behaviour)**: a forced-fail correction that mentions "approval" leads a tool-equipped agent to CALL an approval tool (a tool-call turn ≠ a FINAL answer → the verify gate never reaches failed_max → a DIFFERENT pause fires). Driving a verification-escalate needs the candidate to remain a final answer — a neutral "no tools, just re-answer" correction. **Lesson: forced-fail drive-through fixtures must steer the agent away from tool calls.**
- **The chat-v2 HITL UI is tool-kind-shaped**: `HITLTurn` reject = terminate + no note input. New pause kinds whose reject semantics differ (A2 reject = coach-one-turn) need explicit frontend wiring. Surfaced as a follow-up rather than silently scope-crept.

## Q5 — Anti-pattern audit (04 / 11 points)

- AP-1 (pipeline-as-loop): ✅ the escalate is a conditional `return` inside the while-driven `_run_turns`; the reject continuation drives the SAME `_run_turns`. `check_ap1` green.
- AP-4 (Potemkin): ✅ the escalate pause + resume branches are exercised by 5 unit tests + the APPROVE drive-through; the toggle default-OFF is byte-identical (tested).
- AP-9 (no verification loop): ✅ A2 is literally a verification-loop human off-ramp.
- AP-11 (version suffix / naming): ✅ no `_v2` etc.; `kind="verification"` matches behaviour.
- All others N/A or ✅ (no new event = `check_event_schema_sync` green; LLM SDK leak 0; single category boundary — Cat 1×10×9×7).

## Q6 — Gate evidence

- mypy `src` **0/353**; `run_all.py` **10/10** (AP-1, event-schema-sync green = no new event, SDK-leak 0); black/isort/flake8 FULL scope clean.
- Full backend pytest **2299 passed + 4 skipped = 2303** (Day-0 baseline 2298 + 5: 2 Day-1 escalate + 3 Day-2 resume; zero deletion).
- events.py / DB models / frontend src diff vs main = **0** (3 backend src files only: loop.py + handler.py + config).
- **Drive-through PASS** (APPROVE half): real UI + real backend + real Azure gpt-5.2 + a real LLM judge (env forced-fail). Screenshots in `artifacts/`.

## Q7 — Carryover (→ next-phase-candidates.md)

1. **chat-v2 verification-reject UI follow-up** (frontend): `HITLTurn` resume-on-reject for `kind="verification"` + a coaching-note input → `decide(reason)`. Makes the REJECT-with-note half UI-drivable.
2. **A3 — trace-aware critique** verifier (sees recent turns/tool errors, not just the final string) + a cheap-judge accuracy benchmark.
3. **Per-tenant verification mode/policy** (Config 分層 = workflow C / C3) — a tenant choosing its own escalate policy.
4. **deliver-with-flag terminal** (option b — deliver but flag failed; not chosen for A1/A2).
5. **Multi-round human coaching** (>1 turn — A2 bounds to exactly one).
6. **Cheap-judge accuracy** (does the cheap-tier judge over/under-correct vs the strong tier — A3 territory).

---

## Design Note Extract (spike sprint only)

**N/A** — A2 is a **feature-continuation** (the 4th pause leg, extending the 57.91-93 + 57.98 primitives). Per `.claude/rules/sprint-workflow.md §Step 5.5`, feature-continuation sprints do NOT extract a design note. Record = CHANGE-066 + `25-verification-in-loop-design.md` §4 (A2 invariant deferred → SHIPPED) + `17-cross-category-interfaces.md` (the `LoopCompleted` 5th `awaiting_approval` origin).
