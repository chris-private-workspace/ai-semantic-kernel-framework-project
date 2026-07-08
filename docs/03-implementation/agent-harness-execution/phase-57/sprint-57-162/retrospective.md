# Sprint 57.162 Retrospective — DAG soft-enforce advisory + cycle report + Inspector Viz

**Closed**: 2026-07-08 · Branch `feature/sprint-57-162-dag-enforce-cyclereport-viz` (local, NOT pushed per user 完成即暫停) · CHANGE-129 · closes `AD-TaskPrimitive-DAG-Enforce-Phase58` (soft) + `AD-TaskPrimitive-DAG-CycleReport-Phase58` + `AD-TaskPrimitive-DAG-Viz-Phase58`.

## Q1 — What went well

- **Day-0 三-prong caught the two real design constraints before code**: (a) D-sse-serde proved the wire already carries `depends_on` (Viz = FE-only, zero backend); (b) D-existing-tests-fe surfaced the `getByText` collision risk → numeric node labels + `aria-label` full title → **zero existing-test churn** (all 7 prior InspectorTodos tests + 14 prior DAG tests stayed green).
- **The enforcement-semantics question was the right thing to ask.** "DAG-Enforce" literally conflicts with the codebase's deliberate guidance-not-enforcement principle; asking (AskUserQuestion → SOFT) avoided building a hard-reject that would have contradicted 57.140/156/157.
- **Additive-safe design held**: clean-plan handler path + no-dep render stayed byte-identical → no regression across 3223 backend + 930 FE tests.
- **Drive-through STRONG PASS first try** (no re-drive): the deliberate-DAG prompt deterministically triggered BOTH advisory types + the cyclic Viz; the screenshot visually confirmed the dashed-red cycle nodes + the advisory in the real observation.

## Q2 — Estimate accuracy / calibration

- Class **`task-primitive-dag-spike` 0.60** — 2nd data point (57.156 = 1st, ~0.95-1.0).
- Bottom-up ~7.3 hr → committed ~4.4 hr (mult 0.60, 3-segment, `agent_factor` 1.0 parent-direct).
- **Actual ≈ committed → ratio ~1.0-1.1 (IN band, upper edge) → KEEP 0.60.** The code core landed on-budget (backend clean bar 1 test-assertion fix; FE clean). The upper-edge push came from the **drive-through staging** — the Risk-E orphan spawn-worker kill (68500, dead parent 39440) + the AD-Playwright-MCP-Recovery stuck-chrome-lock recovery + the fresh no-`--reload` backend restart + Azure/env verification — exactly the variance driver the 57.156 note predicted ("if a 2nd lands > 1.20 drive-through-dominated → re-point 0.70"). It did NOT exceed 1.20 (the drive-through itself was first-try, no re-drive), so 0.60 holds; if a 3rd DAG-family spike with a mandatory drive-through lands > 1.20, re-point 0.70.

## Q3 — What to improve / lessons

- **MHist E501 recurred** (first-draft 106 chars) — the exact anti-pattern `file-header-convention.md` warns about; caught by flake8, trimmed. The char-budget templates exist; apply them on first draft next time.
- **A test asserted the negative of an instruction-string change**: `test_render_non_cycle_block_unchanged` initially checked `"blocked by cycle" not in out`, but the has_deps INSTRUCTION now mentions the `(blocked by cycle: ...)` marker → false failure. Lesson: when a render adds explanatory instruction text, negative substring assertions must scope to the TODO LINES, not the whole output.
- **Risk Class E reconfirmed**: `dev.py status` reported the backend "not running" while an orphan spawn-worker (dead-parent) was actively serving :8000 with stale code — the port-owner PID (39440) was dead; the live worker (68500) was a `multiprocessing.spawn` child. The `Win32_Process` PID/PPID/StartTime sweep is the reliable check (as the rule already documents).

## Q4 — Anti-pattern self-check (Q5 gate)

- AP-2 (no orphan / side-track): ✅ every new function reachable from the main flow (`plan_warnings`←handler; `detect_cycles`←`plan_warnings`+`render_active_plan`; `TodoDagGraph`←`InspectorTodos`).
- AP-3 (no cross-dir scatter): ✅ backend logic in `_contracts/todo.py` + `tools/todo_tools.py`; FE in the one Inspector component.
- AP-4 (no Potemkin): ✅ the Viz + advisory are drive-through-proven real (screenshot + DOM evaluate + real observation), not fixtures.
- AP-6 (no speculative abstraction): ✅ SOFT advisory only; NO per-tenant policy / interactive editing built (and NOT logged as new ADs per user directive).
- AP-8 (PromptBuilder single-source): N/A (no new LLM call site; `render_active_plan` is the existing injection).
- AP-11 (no version suffix / naming drift): ✅.
- v2 lints **11/11**.

## Q5 — Drive-through (record)

STRONG PASS — see progress.md Day 3 + CHANGE-129 §Verification + `artifacts/sprint-57-162-drivethrough-dag-viz-advisory.png`. Real chat-v2 + real backend (57.162) + real Azure gpt-5.2; advisory (out-of-order + cycle) in the real observation with the write succeeding (soft); DAG Viz (nodes + dashed cycle edges + cycle markers) rendered live in the Inspector Todos tab.

## Q6 — Carryover

**NONE** — per the user directive (只完成這工作就可以暫停, 不要產生其他工作), no new carryover ADs were logged. The tempting-but-out-of-scope items (hard enforcement, per-tenant advisory policy, interactive graph editing, cross-send cycle-annotation UI surface) were deliberately NOT started and NOT recorded as ADs. The DAG arc (57.140 linear → 57.156 DAG → 57.157 scheduler → 57.162 enforce/cycle/viz) is complete for now.

## Q7 — Metrics

- Files: 3 source (todo.py, todo_tools.py, InspectorTodos.tsx) + 3 test edits. NO migration / wire / codegen / loop.py / sse.py / store.
- pytest 3223/6skip (+17) · Vitest 930 (+3) · mypy `src` 400/0 · run_all 11/11 · mockup 51 byte-identical · build rc=0.
- Calibration: `task-primitive-dag-spike` 0.60 2nd data point, ratio ~1.0-1.1 IN band → KEEP.
