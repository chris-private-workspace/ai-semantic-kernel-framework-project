# Sprint 57.156 Retrospective — DAG task primitive: dependency-aware todos

**Closed**: 2026-07-01 · branch `feature/sprint-57-156-dag-task-primitive` from `main` `e7b4ba73` · closes `AD-TaskPrimitive-DAG-Phase58`

## Q1 — What shipped?

The DAG evolution of the 57.140 linear task primitive: `Todo.depends_on` (prerequisite ids) end-to-end — tolerant serde, a `ready_todos` topological-readiness helper (direct-dependency, cycle-safe, unknown-dep-ignored), a dependency-aware `## Active Plan` render (`(ready)` / `(blocked by:…)` annotations; byte-identical when no todo has deps), the `write_todos` schema `depends_on` field, and a chat-v2 Todos panel that shows a "⤷ needs" line + a `blocked` badge and dynamically re-computes on completion. Guidance-not-enforcement. Backend delta in 2 files (`_contracts/todo.py` + `tools/todo_tools.py`) + 2 FE files; loop.py / sse.py / wire / store / migration UNTOUCHED. CHANGE-123 + design note 59.

## Q2 — Estimate accuracy (calibration)

- Scope class **NEW `task-primitive-dag-spike` 0.60** (anchored to `task-primitive-spike` 0.60 (57.140, its parent)).
- **Agent-delegated: no** (parent-direct; a tightly-coupled 2+2-file change). `agent_factor` 1.0 → 3-segment form.
- Bottom-up est ~10 hr → class-calibrated commit ~6 hr (mult 0.60). **Actual ~5.5-6 hr → ratio ~0.95-1.0 IN band → KEEP 0.60.**
- Why it landed clean (not the ceremony-heavy 0.85 re-point some spikes need): the real-code core (topological readiness logic + tolerant serde + render redesign + FE mirror + 19 tests ≥~3.5 hr) HELD the 0.60 per the 57.137 lesson — this was NOT a tiny-code sprint; AND the drive-through ran on-budget (both legs passed first try, no re-architecture / re-drive), because everything was serde-transparent reuse of proven 57.140 machinery (the Day-0 prediction that loop.py/sse.py/wire/store/migration stay UNTOUCHED held exactly).
- **1st data point** — if a 2nd `task-primitive-dag-spike` lands > 1.20 (e.g. a drive-through-dominated one), re-point toward 0.70.

## Q3 — What went well?

- **Day-0 三-prong prediction was exact**: the "serde-transparent → 2 backend files, everything else UNTOUCHED" analysis held to the letter; the drive-through confirmed `depends_on` flowed onto the wire with sse.py unchanged.
- **Guidance-not-enforcement** was the right call — the drive-through showed the agent naturally worked the ready step first without any enforcement; a cycle/typo can't deadlock.
- **The no-dep byte-identical guarantee** (via `has_deps` branch in `render_active_plan`) kept the 57.140 behavior exactly for flat plans (test `test_render_no_deps_is_byte_identical_to_57140`).
- **Drive-through both legs first try** — Leg 1 (agent authors DAG, identifies ready step) + Leg 2 (completing a step live-unblocks dependents) both passed with no re-drive.

## Q4 — What to improve?

- The one existing byte-exact test (`test_serde_round_trip`) broke on the additive `depends_on:[]` — caught by the Day-0 D-existing-tests grep + fixed same-PR. Continue grepping for byte-exact `==` assertions before adding a serde field.
- The drive-through session carried noisy cross-sprint identity memory (Dana vs Chris, from 57.148-153) — irrelevant to DAG but a reminder that a shared drive-through user accumulates state; a fresh user would isolate cleaner (didn't affect the DAG verdict).

## Q5 — Anti-pattern self-check

- AP-2 (no orphan): `ready_todos` consumed by `render_active_plan` + FE mirror; all reached from the main flow. ✅
- AP-3 (no scatter): DAG logic in the one `_contracts/todo.py` chokepoint. ✅
- AP-4 (no Potemkin): drive-through proved the panel renders + updates live, not a dead control. ✅
- AP-6 (no future-proofing): shipped only the guidance DAG; enforcement/scheduler/viz deferred as ADs. ✅
- AP-8 (PromptBuilder): the render rides the existing `render_active_plan` seam; no new bare prompt assembly. ✅
- AP-11 (naming): `depends_on` / `ready_todos` — no version suffix. ✅
- v2 lints 11/11 (incl. `check_tool_descriptions` — the new `depends_on` param has a description).

## Q6 — Gates

pytest **3139 / 6 skip** (+16) · mypy `src` **399/0** · run_all **11/11** · Vitest **925 / 148 files** (+3) · mockup **51 byte-identical** · `npm run lint && npm run build` clean · black/isort/flake8 + LLM-SDK-leak clean. Drive-through STRONG PASS both legs (real Azure gpt-5.2).

## Q7 — Carryover

- `AD-TaskPrimitive-DAG-Enforce-Phase58` — topological execution enforcement (block the agent on readiness).
- `AD-TaskPrimitive-Scheduler-Phase58` — cross-burst auto-continue scheduler (research #3; durable spine shipped 57.140, DAG now shipped).
- `AD-TaskPrimitive-DAG-CycleReport-Phase58` — surface a detected cycle to the agent (today it just renders both blocked).
- `AD-TaskPrimitive-DAG-Viz-Phase58` — inline turn-block DAG graph (vs the Inspector tab).
