# Sprint 57.94 Retrospective — Cat 11 FORK Real Child Agent Loop (地基 A payoff)

**Sprint**: 57.94 (Cat 11 FORK child loop, Slice 1)
**Closed**: 2026-06-09
**Branch**: `feature/sprint-57-94-subagent-fork-child-loop`
**Record**: CHANGE-061 + design note `20-subagent-child-loop-design.md`

---

## Q1 — What did we deliver?

The **first real child agent loop** in Cat 11: FORK now drives a real multi-turn, tool-capable child `AgentLoopImpl` (reusing the parent `run()`/`_run_turns`) instead of the single-shot `chat()` that had stood in for it since Sprint 54.2. This cashes in the 地基 A investment (57.88-93).

- `ChildLoopFactory` type (Cat 11 `_contracts`, TYPE_CHECKING `AgentLoop`) + `ForkExecutor` real child-loop drive + `LoopEvent`→`SubagentResult` drain + dispatcher threading + the factory closure (recursion-safe subset via `make_default_executor(subagent_dispatcher=None)`) in `build_real_llm_handler`.
- **`loop.py` UNCHANGED** — the child reuses the re-enterable `run()`/`_run_turns` (the 57.89 payoff). AS_TOOL inherits the real loop for free; TEAMMATE/HANDOFF unchanged.
- No single-shot fallback (US-5 → no AP-10): existing FORK/AS_TOOL tests converted (Never-Delete) + NEW `test_subagent_child_loop.py` (multi-turn+tool / recursion-safe subset / tenant / child LOOP span).
- mypy 0/351 · pytest **2271** (+5) · run_all 10/10 · black/isort/flake8 clean.
- **Drive-through PASS** (real chat-v2 UI + backend + Azure gpt-5.2): `task_spawn` → child uses `echo_tool` → `{success: true, summary: "child loop is real", tokens_used: 3684}` + 2389ms TOOL_EXEC span.

## Q2 — Calibration

Scope class: **`subagent-child-loop-spike` (NEW, 0.60 mid-band) — 1st data point, pending 2-3 sprint validation**. NOT the `backend-core-loop-refactor` pause-point shape (that touched `loop.py`; this did NOT — the changes are confined to `subagent/` + the `handler.py` factory closure). Agent-delegated: **no** (parent-direct — first real child loop + new-domain design + drive-through with trace assertion). `agent_factor = 1.0` (does NOT extend the AgentDelegated-WallClock streak).

> Bottom-up est ~12.5 hr → class-calibrated commit ~7.5 hr (mult 0.60) → **actual ≈ 7 hr (AI-cadence est) → actual/committed ≈ 0.93 (IN band)**.

- The dominant cost was the Day-0 research (2 read-only passes mapping the hollow stub + the factory-wiring feasibility) + the test conversion (the integration `_redirect_subagent_chat` rewire surfaced as a 2-test failure in the full run, caught + fixed cleanly) + the drive-through. The core code (ForkExecutor drive/drain + factory closure) was small once Day-0 confirmed `loop.py` needs no change.
- 1st data point for the class → KEEP 0.60 pending validation (the directional signal: the spike landed roughly on the calibrated commit, no major over/under-run; AI-cadence wall-clock is imperfectly measured, `AD-Calibration-AgentDelegated-WallClock-Measure`).

## Q3 — What went well?

- **Day-0 research nailed the keystone insight**: `loop.py` needs ZERO change because the child reuses the re-enterable `run()` (the 57.89 payoff). This collapsed the perceived blast-radius — the spike became "wire a factory in `subagent/` + `handler.py`", not "surgery on the loop".
- **The recursion guard fell out for free**: `make_default_executor(subagent_dispatcher=None)` already builds the FORK-safe subset (no `task_spawn`/`handoff`) — no `max_subagent_depth` threading needed (a child that can't spawn is depth-bounded at 1).
- **The drive-through proof was unambiguous**: delegating a task that REQUIRES a tool made the result self-proving — `summary="child loop is real"` (the echoed phrase) + 3684 tokens are impossible under the old single-shot (which `empty_response`s on a tool-call response). No need to read backend logs.
- **Full-run caught the integration regression**: the subagent-dir + keystone-file targeted runs passed, but the FULL run surfaced 2 `test_chat_keystone_wiring.py` FORK tests still using the removed `_fork._chat` redirect → fixed by swapping to `_child_loop_factory`. Running the full suite (not just the touched dir) is what caught it.

## Q4 — What to improve?

- **The `_redirect_subagent_chat` regression was foreseeable** — removing `ForkExecutor._chat` should have prompted a grep for `._fork._chat` / `_chat =` across tests at Day-1, not waited for the full-run failure. A Day-1 "grep for the attr I just removed" check would have caught it before the full run (~3.5 min). Cheap lesson: when removing a public-ish attr, grep its usages immediately.
- The child runs **headless** (no SSE relay) → the Inspector Tree tab shows "no subagents" even though one ran. This is honest (deferred D2) but a future slice should wire the chat dispatcher's `event_emitter` + a `LoopEvent` parent marker so the UI shows the subagent.

## Q5 — Action items / carryover

- Carryover (deferred, → `next-phase-candidates.md`): TEAMMATE/HANDOFF real loops / `HandoffService` / **`AD-Subagent-Child-Event-SSE-Relay`** (the chat dispatcher has no `event_emitter` → Tree tab empty; child headless) / **`AD-Subagent-Child-Span-Nesting`** (task_spawn passes `trace_context=None` → child span not explicitly parented) / recursion depth > 1 / `AD-Subagent-Transcript-Isolation` (parentUuid chain) / `AD-Subagent-Child-Governance` (Cat 9/10 in the child) / failure policies.
- Calibration: record `subagent-child-loop-spike` 0.60 (1st data point) in `calibration-log.md §3` + propose in `sprint-workflow.md §Scope-class matrix`.

## Q6 — Anti-pattern / discipline self-check

- AP-1 (no pipeline-as-loop — the child is a real `while True` `_run_turns`; run_all confirms the detector doesn't flag the `async for ev in child.run()` drive) ✅ · AP-4 (not Potemkin — real child loop proven by the drive-through; the old single-shot WAS the Potemkin this closes) ✅ · AP-8 (PromptBuilder untouched) ✅ · AP-10 (no Mock-vs-Real divergence — no single-shot fallback; the mock-LLM tests exercise the SAME real-loop path) ✅ · LLM neutrality (SDK leak 0; child uses the same ChatClient ABC) ✅ · Multi-tenant (tenant_id threaded into the child) ✅ · Sprint workflow (plan → checklist → Day-0 verify → code → test → drive-through → docs) ✅ · File-header MHist 1-line E501-safe ✅ · Spike design note extracted (8-pt gate, §8 self-check all ✅) ✅ · Drive-Through Acceptance (real UI + backend + Azure, not gate-only) ✅.

## Design Note Extract (spike sprint)

**File**: `docs/03-implementation/agent-harness-planning/20-subagent-child-loop-design.md`
**Verified ratio (estimated)**: ≥95%
**8-Point Quality Gate**: 1. Section header ✅ · 2. file:line ✅ · 3. Decision matrix (factory vs override vs fallback) ✅ · 4. Verification command (git diff + pytest) ✅ · 5. Test fixture (`_child_loop_helpers.py` + `test_subagent_child_loop.py`) ✅ · 6. Open invariant boundary ✅ · 7. Rollback path ✅ · 8. 17.md cross-ref ✅.
**Reviewer pass**: self-review.

## Q7 — Verdict

Shipped + drive-through PASS. The first real child loop in Cat 11 — a subagent is now a multi-turn, tool-using agent, not a 1-shot. The `loop.py`-untouched property (the child reuses the 57.89 re-enterable loop) made it a low-blast-radius spike. Honest deferred boundary (headless child / no SSE relay / span nesting best-effort) documented. Push + PR pending user authorization.
