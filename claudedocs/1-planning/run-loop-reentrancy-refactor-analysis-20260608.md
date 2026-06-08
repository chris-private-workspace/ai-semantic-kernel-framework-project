# Analysis — run() Re-entrancy Refactor (closes AD-Resume-Continuation-Fidelity)

**Purpose**: Ground-truth scoping analysis for the 地基 A keystone debt: refactor `AgentLoopImpl.run()`'s per-turn body into a single **re-enterable** unit that BOTH `run()` and `resume()` drive, so `resume()` is no longer a reduced second copy of the loop. Output of the post-Sprint-57.88 strategy fork (user选「還拱心石的債」, 2026-06-08).
**Category / Scope**: Cat 1 (Orchestrator Loop) core; touches Cat 4/7/8/9/12 integration points.
**Status**: Analysis / design note — **NOT a sprint plan**. No User Stories / File Change List / Day structure. A sprint plan + checklist will be drafted (rolling) when the user kicks off Slice 1.
**Source**: Sprint 57.88 `19-pause-resume-design.md §5` (AD-Resume-Continuation-Fidelity) + real `loop.py` read (2026-06-08).

> **Modification History**
> - 2026-06-08: Initial analysis — grounded in loop.py read; divergence table + target design + slicing strategy.

---

## 1. What this addresses (and what it is NOT)

`AD-Resume-Continuation-Fidelity` (the top 57.88 carryover): `resume()` continues a paused conversation via `_resume_continuation` (`loop.py:1992-2140`) — a SECOND, reduced copy of `run()`'s loop body. It is a real `while True` through PromptBuilder honoring max_turns/token_budget (passes AP-1/AP-8), BUT it omits run()'s Cat 4/7/8/9/12 machinery (§3 below). Consequences: (a) a resumed conversation **cannot pause again** (no checkpoint in the continuation → one-approval-per-run); (b) it's a duplication that drifts from run(); (c) the **subagent child-loop (Cat 11) would inherit this debt** — a child loop that can't pause/resume properly is not production-grade.

This refactor is the prerequisite for: generalized pause points + subagent child-loop resumability. It is NOT: a new feature, a 地基 B phase machine, or a behavior change to the happy path (run()'s observable behavior must be byte-identical after Slice 1).

---

## 2. Ground truth — run()'s per-turn anatomy (`loop.py`)

`run()` (960+) structure:
- `1023` Cat 9 **input** guardrail + tripwire (once, pre-loop)
- `1035` **outer `while True`** (the turn loop)
  - `1036-1055` pre-LLM terminators: max_turns / token_budget / **cancellation**
  - `1062-1141` Cat 4 **compaction** (`compactor.compact_if_needed`)
  - `1141` per-turn marker + `TurnStarted` (inside Cat 12 `category_span`)
  - `1164-1283` Cat 5 **PromptBuilder.build** (memory layers + cache breakpoints)
  - `1283-1390` LLM call (+ cancellation mid-call)
  - `1390-1412` parse + `LLMResponded` + `Thinking`
  - `1412-1428` Cat 7 **post-LLM checkpoint** (`_emit_state_checkpoint`)
  - `1428-1442` Cat 9 **output guardrail**
  - `1442-1460` stop_reason terminator → END_TURN
  - `1460-1525` dispatch on OutputType (END_TURN / **HANDOFF** 1485-1501 / TOOL_USE)
  - `1525-1807` `for tc in parsed.tool_calls:`
    - `1533` Cat 9 **per-tool check** → `_cat9_hitl_branch` (the ESCALATE/HITL/**deferred-pause** branch)
    - `1590-1807` inner `while True` Cat 8 **retry** + `_handle_tool_error` (1654/1730)
  - `1807-1811` Cat 7 **post-tool checkpoint**

`resume()` (1841-1990): load pending_approval → `get_decision` → APPROVED: exec the pending tool (inline, NOT via the Cat 9/8 path) → append observation → `_resume_continuation`; REJECTED → block; undecided → fail-closed ERROR.

---

## 3. The divergence — what `_resume_continuation` OMITS vs run()

| # | Machinery | run() | `_resume_continuation` | Risk of the omission |
|---|-----------|-------|------------------------|----------------------|
| 1 | Cat 9 **per-tool guardrail / deferred-pause** (`_cat9_hitl_branch`) | ✅ 1533 | ❌ raw `tool_executor.execute` (2122) | **A 2nd ESCALATE in the continuation is NOT caught → cannot pause again (one-approval-per-run).** The core limitation. |
| 2 | Cat 8 **retry / error policy / circuit breaker** (`_handle_tool_error`) | ✅ 1590-1807 | ❌ emits `ToolCallFailed`, continues (2132) | Resumed tool failures aren't retried; error budget/circuit breaker not applied. |
| 3 | Cat 4 **compaction** (`compact_if_needed`) | ✅ 1062-1141 | ❌ none | A long resumed conversation can exceed context with no compaction. |
| 4 | Cat 7 **checkpoints** (post-LLM + post-tool) | ✅ 1412/1811 | ❌ none | No durable state during continuation → nothing to resume from if it pauses/crashes. |
| 5 | Cat 9 **output guardrail** (`check_output`) | ✅ 1428 | ❌ none | Resumed final answer isn't output-guardrail-checked. |
| 6 | Cat 12 **per-turn spans** (`category_span`) | ✅ 1141 | ❌ none | Continuation turns are unobserved in tracing. |
| 7 | **HANDOFF** dispatch | ✅ 1485-1501 | ❌ treats as plain END_TURN (2094) | A handoff requested in the continuation is silently ended. |
| — | cancellation mid-loop | ✅ 1049 | ❌ (only max_turns/token_budget) | Resumed loop can't be cancelled mid-turn. |

`_resume_continuation` DOES correctly include: Cat 5 PromptBuilder (AP-8, 2035-2063), token accounting (2071), parse + `LLMResponded`/`Thinking` (2073-2081), stop_reason/dispatch (2083-2101), tool-call emit + append (2110-2139). So it is NOT a Potemkin — it's an honest, fenced reduced copy. The debt is the duplication + the 7 omissions.

---

## 4. Root cause

run()'s per-turn body is a **deeply-nested inline block** inside the outer `while True` (1035), closing over `turn_count` / `tokens_used` / `messages` / accumulators / span context. It was never extracted into a callable unit, so `resume()` — which must re-enter mid-conversation and run the same per-turn logic — had no shared unit to call and got a hand-written reduced copy instead. The fix is **structural extraction**, not feature work.

---

## 5. Target design — one re-enterable turn loop

Extract run()'s per-turn body into a single async-generator unit driven off `LoopState` (the existing transient+durable carrier), called by BOTH entry points:

```
_run_turns(state: LoopState, ctx) -> AsyncIterator[LoopEvent]:
    # exactly run()'s current outer-while body (Cat 4 → 5 → LLM → parse →
    # Cat 7 post-LLM → Cat 9 output → stop_reason → dispatch incl. HANDOFF →
    # tool loop with Cat 9 per-tool (_cat9_hitl_branch) + Cat 8 retry →
    # Cat 7 post-tool), reading/writing turn_count+tokens+messages on `state`.

run(...):                      # unchanged observable behavior
    ... input guardrail/tripwire (1023) ...
    async for ev in self._run_turns(state, ctx): yield ev

resume(...):                   # no more _resume_continuation
    state = <load checkpoint + rehydrate messages>            # already done (service.py)
    # exec the approved pending tool THROUGH the shared tool path, pre-approved
    # (the HITL decision is already APPROVED → must NOT re-trigger _cat9_hitl_branch
    #  for THIS tool_call) → append observation to state.messages
    async for ev in self._run_turns(state, ctx): yield ev
```

**Why this shape**: `LoopState` already exists and `resume()` already reconstructs it (`service.py:187-193` checkpointer.load + `messages_from_metadata`). Threading state via `LoopState` (not loose locals) is the natural carrier and avoids a giant param list. Once `_run_turns` contains the Cat 9 deferred-pause branch, **a 2nd ESCALATE in the continuation checkpoints + pauses again for free → multi-pause-per-run falls out** (closes the §3-#1 + #4 limitation simultaneously).

---

## 6. Key design decisions / risks to resolve in the plan

1. **Pre-approved pending tool must not re-escalate** (the subtle one). On resume, the pending tool is already HITL-APPROVED; re-running it through `_cat9_hitl_branch` would re-trigger ESCALATE. Options: (a) pass an "approval already granted for tool_call_id=X" sentinel into the first turn's tool path; (b) execute the pending tool once outside `_run_turns` (current resume() does this) then enter `_run_turns` for the rest. **(b) is the smaller change** and keeps `_run_turns` ignorant of resume — preferred unless multi-pause requires the pending tool itself to be the pause point. Lock this in the plan.
2. **State as carrier vs loose locals** — run() currently uses loose `turn_count`/`tokens_used`/`messages` + metric accumulators (Cat 12 token attrs, cache fields from 57.65). The extraction must move these onto `LoopState` (or a small per-run context object) without dropping the 57.2/57.65/57.82 accumulator fields on `LoopCompleted`. Risk: silently losing a `LoopCompleted` field → caught by existing tests + `check_event_schema_sync`.
3. **Span nesting** (Cat 12, 57.71) — run()'s LOOP→TURN span tree must survive extraction (the TURN span opens inside the body). Verify the tracer tree test (`test_reconstructs_loop_turn_operation_tree_with_correct_nesting`) stays green.
4. **Test isolation** (Risk Class C) — the refactor touches the most-tested file; expect to re-run the full backend suite (2229) + the 8 pause-resume unit + 5 integration.
5. **Blast radius** — `run()` is the 主流量. Slice 1 MUST be pure extraction with zero behavior change (full pytest unchanged is the gate). Do NOT mix behavior changes into the extraction commit.

---

## 7. Slicing strategy (thin-first, drive-through per slice)

| Slice | What | Gate | Size |
|-------|------|------|------|
| **Slice 1 — pure extraction** | Move run()'s outer-while body into `_run_turns(state, ctx)`; run() calls it. **Zero behavior change.** `_resume_continuation` untouched (still in use). | Full backend pytest 2229 **unchanged** + mypy 0 + run_all 10/10 + span-tree test green. No drive-through needed (no user-facing change). | ~1 sprint (mechanical but high-care) |
| **Slice 2 — rewire resume + delete the copy** | `resume()` execs the pre-approved pending tool then drives `_run_turns`; **DELETE `_resume_continuation`**. Resumed continuation now has Cat 4/7/8/9/12. | 57.88 pause-resume tests green + NEW test: a 2nd ESCALATE in the continuation pauses again (multi-pause) + **drive-through** (echo twice → pause → approve → 2nd pause → approve → answer). | ~1 sprint |
| **Slice 3 — generalized pause (optional next)** | With the shared unit + checkpoint-everywhere, enable input-ESCALATE pause + mid-loop pause points (closes part of the 57.88 generalization carryover). | Per-pause-point drive-through. | ~1-2 sprint (defer until Slice 1+2 land) |

Slice 1+2 = the AD-Resume-Continuation-Fidelity close (~2-3 sprint total). Slice 3 + subagent child-loop build are downstream and out of this analysis's scope.

---

## 8. Out of scope

- 地基 B explicit phase machine / multi-cognition-per-loop (separate design decision — see `cc-source-blueprint-pause-resume-phases-20260608.md`).
- Subagent child-loop build (Cat 11) — consumes this refactor; distinct larger sprint.
- Checkpoint-bloat (`resume_messages` → messages table) — separate AD (`AD-Resume-Checkpoint-Bloat`).
- Per-tenant capability policy / reject-path reaper — separate ADs.

---

## 9. References

- `19-pause-resume-design.md §5` — AD-Resume-Continuation-Fidelity (the debt this closes)
- `loop.py` — run() 960-1811 / resume() 1841-1990 / `_resume_continuation` 1992-2140 / `_emit_state_checkpoint` 2141
- `platform_layer/resume/service.py:187-197` — state reconstruction (already feeds the shared unit)
- `claudedocs/5-status/agent-harness-cc-parity-20260607.md` — CC-parity gap (loop core ✅; this refactor hardens it)
- `claudedocs/1-planning/next-phase-candidates.md §Sprint 57.88 Carryover` — carryover ADs
- `.claude/rules/sprint-workflow.md §Common Risk Classes` C (test isolation) — applies to the full-suite re-run
