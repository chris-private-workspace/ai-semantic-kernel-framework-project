# Sprint 57.89 — Checklist (run() Re-entrancy Refactor Slice 1: pure extraction — zero behavior change)

**Plan**: [`sprint-57-89-plan.md`](./sprint-57-89-plan.md)
**Created**: 2026-06-08
**Status**: Draft (code gated on Day-0 GO)

> Rule: only `[ ]` → `[x]`; never delete unchecked items; defer with `🚧 + reason`.
> REFACTOR (not spike) → REFACTOR-006 record, no design note. Gate = **full backend pytest UNCHANGED (2229)** — a pure extraction moves zero tests. NO `resume()` / `_resume_continuation` edit (Slice 2). NO drive-through (no user-facing change).

---

## Day 0 — Plan-vs-Repo Verify + Branch

### 0.1 Three-prong Day-0 verify
- [x] **Prong 1 (path)**: confirmed — run()'s `while True` @1035 wrapped in `async with start_span(LOOP) as root_ctx:` (1002) + `try` (1009) / `finally: SpanEnded(LOOP)` (1832); while-body ends `turn_count += 1` (1830); per-turn TURN span async with+try/finally inside; `resume()` 1841 / `_resume_continuation` 1992 NOT touched. (progress.md Day-0 Prong 1)
- [x] **Prong 2 (content — accumulator enumeration, the critical one)**: enumerated — per-run mutables `messages` (969) / `turn_count` (974) / `tokens_used` (975) / `metrics_acc = LoopMetricsAccumulator()` (980) + span carriers root_ctx (1007) + _root_ctx_t0; verbatim move preserves every update + LoopCompleted stamp by construction; `verification_*` (57.82) stamped by OUTER wrapper not run() → out of scope. (progress.md Day-0 Prong 2)
- [x] **Prong 3 (schema)**: N/A — no DB / migration / ORM change this sprint (progress.md Day-0)
- [x] **Baseline capture**: pre-sprint baseline = main `e2948810` (same HEAD as 57.88 closeout): pytest 2229 passed / 4 skipped, mypy 0/346, run_all 10/10; will re-confirm exact numbers Day-1 before editing
- [x] Catalogue D-DAY0-1..3 drift findings in progress.md; **go/no-go = GO** (raw-locals signature adopted per D-DAY0-1; verbatim-move locks zero-behavior-change)

### 0.2 Branch
- [x] Branch `feature/sprint-57-89-run-loop-reentrancy` from `main` (`e2948810`)
- [x] plan + checklist + analysis note committed (Day-0 commit)

---

## Day 1 — Extract `_run_turns` (US-1)

### 1.1 Create the re-enterable unit
- [x] **NEW `async def _run_turns(self, *, state: LoopState, ctx: TraceContext) -> AsyncIterator[LoopEvent]`**
  - Cut the outer-`while True` body of `run()` (≈1035-1811) verbatim into `_run_turns`
  - DoD: `_run_turns` contains the full per-turn body; `run()`'s `while True` is replaced by `async for ev in self._run_turns(...): yield ev`
  - Verify: `grep -n "_run_turns" backend/src/agent_harness/orchestrator_loop/loop.py`
- [x] **`run()` builds initial `LoopState` + delegates after the pre-loop input guardrail**
  - input guardrail/tripwire (1023) stays in `run()`; the LOOP span stays opened by `run()` (do NOT move to a shared wrapper — Slice 2)
  - DoD: `run()` body after the input guardrail = build state + `async for ev in self._run_turns(state, ctx): yield ev`
- [x] **mypy clean on the moved body**
  - DoD: `_run_turns` fully typed; no new mypy errors
  - Verify: `cd backend && python -m mypy src/agent_harness/orchestrator_loop/loop.py 2>&1 | tail -1`

---

## Day 2 — State carrier + accumulator preservation (US-2/US-3)

### 2.1 Thread loose locals onto the carrier
- [x] **`turn_count` / `tokens_used` / `messages` read/written via `state.transient`** (current_turn / token_usage_so_far / messages)
  - DoD: no loose `turn_count`/`tokens_used`/`messages` locals survive in `_run_turns` except as `state.transient.*` proxies where needed
- [x] **Metric accumulators (57.2 token totals + 57.65 cache + 57.82 verification) → a run-scoped accumulator object** held for `_run_turns`'s lifetime (per-run, NOT durable)
  - DoD: every accumulator from Day-0 Prong-2's list has its init/update/stamp preserved; the run-scoped object passed/held correctly
  - Verify: `cd backend && python -m pytest tests/ -q -k "token or cache or verification or loop_completed" 2>&1 | tail -3`

### 2.2 Preserve span tree + event identity
- [x] **Cat 12 LOOP→TURN span nesting preserved** (Sprint 57.71)
  - DoD: `category_span` open/close points move with the body; LOOP span unchanged
  - Verify: `cd backend && python -m pytest tests/ -q -k "tree_with_correct_nesting" 2>&1 | tail -3`
- [x] **All `LoopEvent`s + termination paths emit identically** (no field/order change)
  - DoD: MAX_TURNS / TOKEN_BUDGET / CANCELLED / END_TURN / HANDOFF / GUARDRAIL_BLOCKED / TRIPWIRE / AWAITING_APPROVAL / ERROR all move verbatim
  - Verify: `cd backend && python scripts/lint/run_all.py 2>&1 | tail -3` (incl. check_event_schema_sync)

---

## Day 3 — Full regression sweep + REFACTOR-006

### 3.1 The zero-behavior-change gate (US-4)
- [x] **Full backend pytest UNCHANGED**
  - DoD: 2229 passed / 4 skipped — the EXACT Day-0 baseline; zero tests moved/added/skipped
  - Verify: `cd backend && python -m pytest -q 2>&1 | tail -3`
- [x] **The 57.88 pause path still intact** (proves `run()`'s deferred-pause branch moved correctly)
  - DoD: 8 pause-resume unit + 5 integration green
  - Verify: `cd backend && python -m pytest tests/unit/agent_harness/orchestrator_loop/test_loop_pause_resume.py tests/integration/api/test_chat_pause_resume_e2e.py -q 2>&1 | tail -3`
- [x] **mypy 0 + run_all 10/10 + format chain**
  - Verify: `cd backend && python -m mypy src/ && python scripts/lint/run_all.py && python -m black --check src/ tests/ && python -m isort --check-only src/ tests/ && python -m flake8 src/ tests/`
- [x] **`resume()` / `_resume_continuation` byte-unchanged** (scope guard — no Slice-2 creep)
  - DoD: `git diff` shows zero change to `resume()` / `_resume_continuation` bodies
  - Verify: `git diff main -- backend/src/agent_harness/orchestrator_loop/loop.py | grep -A2 -E "def resume|def _resume_continuation"`

### 3.2 REFACTOR-006
- [x] `claudedocs/4-changes/refactoring/REFACTOR-006-run-loop-reentrancy-slice-1.md` (problem / extraction / verification / impact)

---

## Day 4 — Closeout

### 4.1 Closeout
- [x] Full validation (parent re-verified): pytest **2231** (2229 UNCHANGED + 2 detector, documented) / mypy 0/346 / run_all 10/10 / span-tree green / pause-resume green / **no resume() diff**
- [x] progress.md (Day 0-4) + retrospective.md (Q1-Q7)
- [x] Calibration: `backend-core-loop-refactor` 0.55 (NEW, 1 pt, caveated) + `agent_factor` 1.0 (parent-direct); recorded `calibration-log.md §3`; carryover (Slice 2: rewire resume + delete `_resume_continuation` + multi-pause + drive-through) → next-phase-candidates.md
- [x] MEMORY.md pointer + `project_phase57_89_run_loop_reentrancy.md` subfile + CLAUDE.md lean
- [ ] commit (Day 0-N) + push + PR — user-authorized
  - Code commits done (8965a8c7 Day-0 + 75243368 extraction). Closeout-docs commit done; push + PR **pending user authorization**.
