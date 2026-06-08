# Sprint 57.89 Plan — run() Re-entrancy Refactor Slice 1: pure extraction (closes AD-Resume-Continuation-Fidelity Slice 1/2)

**Purpose**: The 地基 A keystone debt-paydown, Slice 1 of 2. Sprint 57.88 shipped durable pause-resume but `resume()` continues via `_resume_continuation` (`loop.py:1992-2140`) — a SECOND, reduced copy of `run()`'s per-turn body that omits Cat 4 compaction / Cat 7 checkpoints / Cat 8 retry / Cat 9 output+per-tool guardrail / Cat 12 spans (analysis note `claudedocs/1-planning/run-loop-reentrancy-refactor-analysis-20260608.md §3`). The root cause is structural: run()'s per-turn body is a deeply-nested inline block inside the outer `while True` (`loop.py:1035`), never extracted into a callable unit, so `resume()` had nothing to share. **This sprint = Slice 1: extract run()'s per-turn body into a single re-enterable `_run_turns(state, ctx)` unit that `run()` drives — with ZERO observable behavior change.** It does NOT touch `resume()` / `_resume_continuation` (Slice 2) and does NOT delete the copy yet. The gate is **the full backend suite passing unchanged** (a pure refactor proves itself by not moving any test). Slice 2 (rewire `resume()` onto `_run_turns` + delete `_resume_continuation` + multi-pause + drive-through) is a separate sprint. **This is a REFACTOR** (Cat 1 core, 主流量) → high-care, zero-behavior-change discipline; no design note (REFACTOR record `REFACTOR-006`, not a spike).
**Category / Scope**: Cat 1 (Orchestrator Loop — `run()` body extraction) + integration points it must preserve (Cat 4 compaction / Cat 5 PromptBuilder / Cat 7 checkpoint / Cat 8 retry / Cat 9 guardrail+HITL / Cat 12 spans); Phase 57.89
**Created**: 2026-06-08
**Status**: Draft (scope below; code execution gated on Day-0 GO)
**Source**: Post-Sprint-57.88 strategy fork (user选「還拱心石的債 — run() 可重入重構」, 2026-06-08) → analysis note `run-loop-reentrancy-refactor-analysis-20260608.md` (ground-truth read of loop.py).

> **Modification History**
> - 2026-06-08: Initial creation — Slice 1 pure-extraction; folds the analysis note's §5 target design + §7 slicing + §6 risks

---

## 0. Background

The 5-point harness-deepening review chose 地基 A ("Loop 可暫停/可分裂") as the first thrust. Sprint 57.88 shipped the durable pause-resume vertical (thin spike) but with an explicit, fenced honest boundary: `resume()`'s continuation is a reduced copy of the loop. The post-57.88 strategy discussion (grounded in the CC-parity analysis — CC is a turn-based while-loop, NOT a phase machine, so this is self-research the right way) identified `AD-Resume-Continuation-Fidelity` as the highest-leverage next step: it is a prerequisite for BOTH generalized pause points AND the subagent child-loop (Cat 11), which would otherwise inherit the reduced-copy debt.

### Analysis already done (Day-0 head-start — analysis note 2026-06-08)

The analysis note read the real `loop.py` and established:
- **run() per-turn anatomy** (note §2): outer `while True` @1035 with pre-LLM terminators → Cat 4 compaction → Cat 5 PromptBuilder → LLM → parse → Cat 7 post-LLM checkpoint → Cat 9 output guardrail → stop_reason → dispatch (incl. HANDOFF) → tool loop (Cat 9 per-tool `_cat9_hitl_branch` + Cat 8 retry) → Cat 7 post-tool checkpoint.
- **The divergence** (note §3): `_resume_continuation` includes Cat 5 (AP-8) + token accounting + parse/dispatch + tool emit, but omits 7 machineries (Cat 9 per-tool pause = the killer → one-approval-per-run; Cat 8 retry; Cat 4 compaction; Cat 7 checkpoints; Cat 9 output; Cat 12 spans; HANDOFF + cancellation).
- **The fix** (note §5): extract `_run_turns(state, ctx)` driven off the existing `LoopState`; both `run()` (this sprint) and `resume()` (Slice 2) call it.

Day-0 Prong-2 (content verify) is therefore largely pre-done by the analysis note; Day-0 re-confirms the exact line ranges + that nothing drifted since the note.

---

## 1. Sprint Goal

Extract `run()`'s per-turn body — the entire content of the outer `while True` (`loop.py:1035-1811`): pre-LLM terminators, Cat 4 compaction, Cat 5 PromptBuilder, LLM call, parse + `LLMResponded`/`Thinking`, Cat 7 post-LLM checkpoint, Cat 9 output guardrail, stop_reason terminator, OutputType dispatch (END_TURN / HANDOFF / TOOL_USE), the tool loop (Cat 9 per-tool `_cat9_hitl_branch` + Cat 8 retry `_handle_tool_error`), and Cat 7 post-tool checkpoint — into a single **re-enterable** `_run_turns(state, ctx) -> AsyncIterator[LoopEvent]` async generator that operates on the existing `LoopState` carrier. `run()` keeps its pre-loop input guardrail/tripwire (`loop.py:1023`) then delegates the turn loop to `_run_turns`. **Observable behavior is byte-identical** — every emitted `LoopEvent` (incl. `LoopCompleted`'s 57.2/57.65/57.82 accumulator fields), every Cat 12 LOOP→TURN span nesting, and every termination path is preserved. **The gate is the full backend pytest suite passing UNCHANGED (2229), mypy 0, run_all 10/10, and the span-tree test green** — a pure extraction moves zero tests. `resume()` / `_resume_continuation` are NOT touched this sprint (Slice 2). No drive-through (no user-facing change). Defer: rewiring `resume()`, deleting `_resume_continuation`, multi-pause, generalized pause points.

---

## 2. User Stories

- **US-1 (extract the re-enterable unit)** — As the loop maintainer, I want `run()`'s per-turn body extracted into `_run_turns(state, ctx)` operating on `LoopState`, so a single source of truth drives both `run()` (now) and `resume()` (Slice 2), eliminating the reduced-copy debt. → `loop.py` new private method `_run_turns`; `run()` delegates after the pre-loop input guardrail.
- **US-2 (state as carrier, no field loss)** — As the loop, I want the loose per-run locals (`turn_count` / `tokens_used` / `messages` / the Cat 12 token + 57.65 cache + 57.82 verification accumulators) threaded through `LoopState` (or a small run-scoped context) so the extraction drops NO `LoopCompleted` field and NO accumulated metric. → state-carrier wiring; `check_event_schema_sync` + existing token/cache tests are the guard.
- **US-3 (preserve Cat 12 span tree + all events)** — As observability, I want the LOOP→TURN→{LLM_CALL/TOOL_EXEC/PROMPT_BUILD/COMPACTION} span nesting (Sprint 57.71) and every `LoopEvent` to emit identically after extraction, so tracing + SSE consumers see no change. → span-context threading; `test_reconstructs_loop_turn_operation_tree_with_correct_nesting` green.
- **US-4 (zero-behavior-change gate)** — As a reviewer, I want proof the extraction changed nothing: full backend pytest unchanged (2229 passed / 4 skipped), mypy 0, run_all 10/10, no event/schema drift, no new test needed (existing behavior tests ARE the proof). → full regression sweep + REFACTOR-006 record.

---

## 3. Technical Specifications

### 3.0 Architecture (the extraction)

```
BEFORE                                  AFTER (Slice 1)
run():                                  run():
  input guardrail/tripwire (1023)         input guardrail/tripwire (1023)   [unchanged]
  while True:                             async for ev in self._run_turns(state, ctx):
    <800-line per-turn body>                  yield ev
                                        _run_turns(state, ctx):           [NEW — the moved body]
                                          while True:
                                            <the SAME 800-line body, reading/writing state>
_resume_continuation():  [UNTOUCHED]    _resume_continuation():  [UNTOUCHED — Slice 2 deletes it]
resume():                [UNTOUCHED]    resume():                [UNTOUCHED — Slice 2 rewires it]
```

The move is mechanical: cut the outer-`while True` body, paste into `_run_turns`, replace loose locals with `state.transient.*` reads/writes (current_turn / token_usage_so_far / messages) + a run-scoped accumulator object for the Cat 12/57.65/57.82 metric fields. `run()` builds the initial `LoopState` (it already constructs equivalent locals) and delegates.

### 3.1 `_run_turns` signature + carrier (US-1/US-2)
- `async def _run_turns(self, *, state: LoopState, ctx: TraceContext) -> AsyncIterator[LoopEvent]`.
- Reads/writes `state.transient.messages` / `.current_turn` / `.token_usage_so_far`; the metric accumulators (token totals, `cached_input_tokens`, verification_* — currently loose locals updated through the body and stamped onto `LoopCompleted`) move to a small run-scoped dataclass held for the method's lifetime (NOT durable — they're per-run, like today).
- Day-0 Prong-2 reads the EXACT current locals + their update sites before moving (the analysis note §2 maps them; re-confirm no drift).

### 3.2 Preserve every termination + dispatch path (US-3)
- All `LoopCompleted(stop_reason=...)` exits (MAX_TURNS / TOKEN_BUDGET / CANCELLED / END_TURN / HANDOFF / GUARDRAIL_BLOCKED / TRIPWIRE / AWAITING_APPROVAL / ERROR) move verbatim — same fields, same order.
- The Cat 9 per-tool `_cat9_hitl_branch` call (incl. the 57.88 deferred-pause branch) moves intact — `run()`'s pause behavior is unchanged (this is why Slice 1 can be zero-behavior-change even though it carries the pause branch).
- HANDOFF dispatch (1485-1501) + Cat 8 inner retry `while True` (1590) + `_handle_tool_error` move intact.

### 3.3 Span + event identity (US-3)
- Cat 12 `category_span` open/close points move with the body; the LOOP span stays opened by `run()` (or moves to a wrapper that both entry points will share in Slice 2 — but for Slice 1, keep the LOOP span where it is so behavior is identical). Verify the span-tree test.
- No `LoopEvent` type/field changes → `check_event_schema_sync` + `serialize_loop_event` parity untouched.

### 3.4 What is explicitly NOT done (Slice 2+)
- `resume()` still calls `_resume_continuation` (untouched). `_resume_continuation` is NOT deleted. No multi-pause. No `resume()` rewire onto `_run_turns`. No generalized pause. (These are Slice 2 / Slice 3 per analysis note §7.)

### 3.5 Lint / neutrality / doc single-source
- `check_llm_sdk_leak` 0 (no SDK touched). `check_promptbuilder_usage` (AP-8) green (PromptBuilder call moves intact). No new contract → 17.md unchanged. REFACTOR-006 records the extraction.

### 3.6 Validation (US-4)
- **Full backend pytest UNCHANGED**: 2229 passed / 4 skipped (the exact pre-sprint baseline). This is the primary gate — a pure extraction must not move a single test.
- mypy `src/ --strict` 0; `run_all` 10/10; `test_reconstructs_loop_turn_operation_tree_with_correct_nesting` green; the 8 pause-resume unit + 5 integration green (proving `run()`'s pause path is intact).
- **No new tests** added (testing a private-method extraction's internals = testing implementation; the existing behavior suite is the proof). If a behavior-preservation seam genuinely needs a characterization test, add it — but the default is zero new tests.
- **No drive-through** (no user-facing change; Slice 1 gate is the unchanged suite). Slice 2 carries the drive-through.

---

## 4. File Change List

| File | Change |
|------|--------|
| `backend/src/agent_harness/orchestrator_loop/loop.py` | **EDIT** — extract the outer-`while True` body of `run()` (≈1035-1811) into NEW `_run_turns(state, ctx)`; `run()` delegates after the pre-loop input guardrail; thread loose locals onto `LoopState` + a run-scoped accumulator (US-1/US-2/US-3). `resume()` / `_resume_continuation` UNTOUCHED. |
| `claudedocs/4-changes/refactoring/REFACTOR-006-run-loop-reentrancy-slice-1.md` | **NEW** — refactoring record (problem / extraction / verification / impact) |
| `claudedocs/1-planning/run-loop-reentrancy-refactor-analysis-20260608.md` | **(already written)** — the grounding analysis; committed with this sprint's branch |
| `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-89-plan.md` + `-checklist.md` | **NEW** — this plan + checklist |
| `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-89/progress.md` + `retrospective.md` | **NEW** — Day 0-N progress + retro |

No new DB table / no migration / no frontend / no Azure-adapter change / no new tests by default / no 17.md change.

---

## 5. Acceptance Criteria

- `run()`'s per-turn body lives in `_run_turns(state, ctx)`; `run()` delegates to it after the pre-loop input guardrail; the loose per-run locals are threaded through `LoopState` + a run-scoped accumulator.
- **Observable behavior byte-identical**: full backend `pytest` passes UNCHANGED (2229 passed / 4 skipped — the exact pre-sprint baseline; zero tests moved/added/skipped); the 8 pause-resume unit + 5 integration green; `test_reconstructs_loop_turn_operation_tree_with_correct_nesting` green.
- No `LoopCompleted` field dropped (57.2 token totals / 57.65 cache fields / 57.82 verification fields all still stamped); `check_event_schema_sync` green.
- `resume()` / `_resume_continuation` unchanged (Slice 2 untouched).
- `mypy --strict src/` 0; 10/10 V2 lints (LLM SDK leak 0; AP-1 while-loop; AP-8 PromptBuilder). REFACTOR-006 written. No frontend touched.

---

## 6. Deliverables

- [ ] `_run_turns(state, ctx)` extraction; `run()` delegates (US-1)
- [ ] loose locals → `LoopState` + run-scoped accumulator, no `LoopCompleted` field loss (US-2)
- [ ] Cat 12 span tree + all `LoopEvent`s + all termination paths preserved (US-3)
- [ ] full backend pytest UNCHANGED (2229) + mypy 0 + run_all 10/10 + span-tree test green (US-4)
- [ ] REFACTOR-006 + progress.md + retrospective.md
- [ ] commit (Day 0-N) — push + PR user-authorized

---

## 7. Workload Calibration

Scope class: **`backend-core-loop-refactor` (0.55, NEW — pending validation)** — a high-care pure-extraction of the 主流量 Cat 1 `run()` body (deeply-nested ~800-line block) with a zero-behavior-change requirement; the cost is dominated by careful read (largely pre-done in the analysis note) + the mechanical move + full-suite regression debugging, not new code. Distinct from `frontend-refactor-mechanical` (UI, 0.80 at 3rd+) because the blast radius (主流量 loop + 9 categories' integration points) demands surgical care. **Agent-delegated: no** (parent-direct) — a deeply-nested 主流量 extraction with a byte-identical-behavior gate is too high-blast-radius to delegate cleanly; `agent_factor = 1.0`. Caveat: 1 unvalidated data point — record caveated, do NOT generalize.

> Bottom-up est ~10 hr → class-calibrated commit ~5.5 hr (mult 0.55).

If Day-1 shows the extraction can't be done zero-behavior-change in one mechanical move (e.g. the accumulator threading forces a behavior-visible change), STOP and re-scope (split the accumulator move into its own slice) rather than smuggle a behavior change into the extraction commit.

---

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| **Smuggling a behavior change into the extraction** | The gate IS "full pytest unchanged" (2229). Commit the extraction ALONE; if a test moves, the extraction wasn't pure — fix the extraction, don't update the test (analysis note §6 risk 5). |
| **Dropping a `LoopCompleted` accumulator field** (57.2/57.65/57.82) | Day-0 Prong-2 enumerate every loose local + its stamp site; `check_event_schema_sync` + existing token/cache/verification tests guard; explicit US-2 deliverable. |
| **pre-approved pending tool re-escalation** (the Slice-2 subtlety) | OUT OF SCOPE this sprint — `_run_turns` carries the Cat 9 branch but `resume()` doesn't call `_run_turns` yet, so no re-escalation path exists in Slice 1. Locked for the Slice-2 plan. |
| **Cat 12 span tree breakage** (Sprint 57.71) | Keep the LOOP span where `run()` opens it (don't move it to a shared wrapper until Slice 2); verify `test_reconstructs_loop_turn_operation_tree_with_correct_nesting`. |
| **Test isolation on the full re-run** (Risk Class C) | The most-tested file changes → run the full suite (not a subset); module-level singleton reset fixtures already in place (sprint-workflow §Common Risk Classes C). |
| **mypy on the moved body** (closures, types) | `_run_turns` typed explicitly (`state: LoopState`, `ctx: TraceContext`, return `AsyncIterator[LoopEvent]`); run cross-platform `# type: ignore[..., unused-ignore]` pattern if a stub diverges (Risk Class B). |
| **Scope creep into Slice 2** | Hard stop: no `resume()` edit, no `_resume_continuation` delete this sprint. Checklist enforces. |
| **LLM-neutrality** | No adapter/SDK touched; `check_llm_sdk_leak` gates. |

---

## 9. Out of Scope (this sprint; → Slice 2 / Slice 3)

- **Slice 2**: rewire `resume()` to execute the pre-approved pending tool then drive `_run_turns`; **DELETE `_resume_continuation`**; multi-pause-per-run (2nd ESCALATE in continuation pauses again) + drive-through. (analysis note §7)
- **Slice 3**: generalized pause points (input ESCALATE / mid-loop) enabled by the shared unit.
- **Subagent child-loop (Cat 11)** — consumes this refactor; distinct larger sprint.
- **Checkpoint-bloat / per-tenant capability policy / reject-path reaper** — separate 57.88 carryover ADs.
- **地基 B explicit phase machine** — separate design decision (B1 native thinking vs B2 explicit phases).
