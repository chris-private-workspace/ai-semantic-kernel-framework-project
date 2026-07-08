# Sprint 57.162 Plan — DAG task primitive: soft-enforce warnings + cycle report + Inspector Viz

**Summary**: Closes the 3 remaining 57.156 DAG carryovers as one coherent slice on the guidance-not-enforcement foundation. (1) **DAG-Enforce (soft)** — `write_todos` appends a non-blocking ⚠️ advisory to its observation when the agent marks a todo `in_progress`/`completed` while a known prerequisite is still incomplete (the write still succeeds — a NUDGE, per the user's AskUserQuestion pick). (2) **CycleReport** — a shared `detect_cycles` helper surfaces dependency cycles to the agent both immediately (the same tool advisory) and durably (`render_active_plan` annotates a cyclic pending node `(blocked by cycle: …)` instead of the misleading `(blocked by: …)`). (3) **Viz** — the Inspector Todos tab gains an inline topological-layer DAG view (node-link, reuses mockup `.badge`/`var(--*)` only; `styles-mockup.css` UNTOUCHED). Rides the 57.140/156 machinery serde-transparently: **NO migration/wire(26)/codegen/sse.py/loop.py-signature/store change**. Backend delta = 2 files (`_contracts/todo.py` + `tools/todo_tools.py`), FE = 1 file. **Drive-through MANDATORY** (Viz + advisory are user-facing). No design note (not a research-eval spike — a bounded feature slice on an existing primitive).

**Status**: Approved-to-execute (user selected the 3 DAG carryovers 2026-07-08 "只完成這工作就可以暫停"; DAG-Enforce semantics = **軟驗證/警告** via AskUserQuestion pick, preserving guidance-not-enforcement)
**Branch**: `feature/sprint-57-162-dag-enforce-cyclereport-viz`
**Base**: current HEAD `1819180d` (= `main` `827917de` + unmerged REFACTOR-010 docs; the sprint CODE is byte-identical to `main` — REFACTOR-010 only touched docs; branched off HEAD to keep the REFACTOR-010 next-phase-candidates append-contract in the working tree for closeout). NOT pushed / no PR this sprint (user: 完成即暫停).
**Slice**: closes `AD-TaskPrimitive-DAG-Enforce-Phase58` + `AD-TaskPrimitive-DAG-CycleReport-Phase58` + `AD-TaskPrimitive-DAG-Viz-Phase58` (the 3 remaining 57.156 carryovers; the DAG arc's final slice)
**Scope decisions**: (a) Enforce = SOFT (advisory appended to observation, write always succeeds) — user pick, keeps guidance-not-enforcement; (b) cycle detection is a shared `detect_cycles` helper consumed by BOTH the handler advisory (immediate) and `render_active_plan` (durable cross-send); (c) Viz is FE-only (the wire already carries `depends_on` since 57.156) — a leveled node-link view reusing mockup classes, `styles-mockup.css` byte-identical; (d) NO new carryover ADs / NO scope expansion (user: 不要產生其他工作).

---

## 0. Background

### The gap (the 3 remaining 57.156 DAG carryovers)

57.156 shipped the DAG data model (`Todo.depends_on` + `ready_todos` + dependency-aware render + FE `⤷ needs`/`blocked` badge) but deliberately left three follow-ons open:

- **DAG-Enforce** — nothing tells the agent when it works out of dependency order (marks a dependent `in_progress`/`completed` before its prerequisite is done). No signal at all today.
- **CycleReport** — `ready_todos` is "cycle-safe by construction" (a cycle just leaves its nodes permanently not-ready) but the cycle is NEVER surfaced: those todos silently stay blocked forever and a pending cyclic node even renders the misleading `(blocked by: <titles>)` as if it were a normal, resolvable block.
- **Viz** — the Inspector Todos tab is a flat list with a textual `⤷ needs` line; the DAG structure (parallelizable layers, downstream chains) isn't visible.

### Why it matters (the missing capability)

The DAG primitive's value is that the agent works ready steps first and a human can see the plan structure. Without an out-of-order signal the agent can silently violate its own declared order; without cycle surfacing a typo'd `depends_on` deadlocks part of the plan invisibly; without a graph view the operator can't see the dependency shape at a glance.

### Root cause (recon code read, file:line; ALL re-verified §checklist 0.1)

| Layer | Reality (on HEAD `1819180d`; code == `main`) | Anchor |
|-------|----------------------------------------------|--------|
| tool handler returns only a plain summary | `return f"Recorded plan: {summarize_todos(todos)}."` — no advisory | `tools/todo_tools.py:142` |
| cycle nodes silently not-ready, no report | `ready_todos` single-pass leaves cycle nodes out of `ready`, never flags them | `_contracts/todo.py:149-169` |
| render mislabels a cyclic pending node | unmet-known-dep pending node → `(blocked by: …)` regardless of whether the block is a cycle | `_contracts/todo.py:207-216` |
| FE has `depends_on` but only a flat list | `TodoItem.depends_on?` narrowed from the wire; rendered as `⤷ needs` text | `InspectorTodos.tsx:150-165`, `chatStore.ts:591` |
| wire already carries `depends_on` | `todos_updated` is generic `Record<string,unknown>[]`; sse serializes via `todos_to_jsonb` | `chatStore.ts:581-594` (57.156 drive-through confirmed) |

→ The fix: (a) a shared `detect_cycles` + `plan_warnings` in the contract; (b) append `plan_warnings` output to the handler result (soft); (c) render distinguishes cycle-blocked from normal-blocked; (d) an FE leveled node-link Viz — all reusing existing machinery, zero wire/migration.

### The design (backend: 2 files + 1 contract helper set; FE: 1 file leveled Viz)

```
_contracts/todo.py  (EDIT)
  + detect_cycles(todos) -> set[str]        # DFS grey/black over KNOWN deps only; ignores unknown ids
  + plan_warnings(todos) -> list[str]       # out-of-order (non-pending w/ unmet known prereq) + cycle lines
  ~ render_active_plan(...)                 # cyclic pending node → "(blocked by cycle: <titles>)"; else unchanged
tools/todo_tools.py (EDIT)
  ~ handler: result += "\n\n⚠️ Plan advisory (not blocking):\n- …"  if plan_warnings(todos)   # SOFT
InspectorTodos.tsx  (EDIT)
  + <TodoDagGraph todos> : compute topological levels (longest-path over known deps) + a cycle set (mirror
    detect_cycles) → SVG node-link (nodes = .badge-toned chips by status/blocked/cycle; edges = <line> in
    var(--border)); falls back to the existing flat list below the graph. NO new CSS, NO oklch literal.
```

Why soft over hard enforce: the entire 57.140/156/157 primitive is deliberately guidance-not-enforcement (`todo.py` docstring: "a NUDGE, nothing enforces the order"; `ready_todos` ignores unknown deps so a typo never deadlocks). A hard reject of an out-of-order `write_todos` would contradict that core design and the tolerant-serde philosophy. The user picked SOFT.

### Ground truth (recon head-start — code read on HEAD `1819180d`; ALL re-verified §checklist 0.1)

- `_contracts/todo.py:149-169` — `ready_todos` (the readiness rule the FE + render mirror; the cycle helper must be consistent: KNOWN-deps-only).
- `_contracts/todo.py:187-217` — `render_active_plan` (`has_deps` gate → byte-identical to 57.140 when no dep; the cycle annotation must preserve that).
- `tools/todo_tools.py:126-144` — the handler (has the parsed `todos`; the advisory append point).
- `loop.py:2000-2003` — `render_active_plan` injected at run-start (the durable cycle surface reaches the agent here).
- `loop.py:3167-3171` — `TodosUpdated` emit (name-coupled to `write_todos`; UNTOUCHED — Viz needs no new event).
- `chatStore.ts:581-594` + `InspectorTodos.tsx:150-165` — FE already narrows `depends_on`; Viz consumes the existing slice.

**Baselines (57.161 closeout)**: pytest 3206 · wire 26 · Vitest 927 · mockup 51 (byte-identical) · mypy `src` 400 · run_all 11/11. Re-verify Day-0.

### STALE / drift findings (Day-0; full detail → progress.md — filled in §checklist 0.1)

- **D-baselines** — the 57.161 closeout numbers above are from CLAUDE.md; re-run to confirm current counts before adding tests.
- **D-render-cycle-label** — confirm a cyclic pending node currently falls into the `(blocked by: …)` branch (`todo.py:209-215`) so the new cycle branch genuinely replaces a misleading label (not a no-op).
- **D-sse-serde** — confirm the `TodosUpdated` serializer path already carries `depends_on` (57.156 said `todos_to_jsonb`); Viz relies on it → Prong-2 grep the serializer, expect NO change needed.
- **D-existing-tests** — `test_todo_dag.py` / `test_todo_tools.py` / `InspectorTodos.test.tsx` byte-exact assumptions that the additive advisory / Viz could break (57.156 hit `test_serde_round_trip`); grep before editing.

## 1. Sprint Goal

Close the 3 remaining 57.156 DAG carryovers as one guidance-preserving slice: the agent receives a non-blocking advisory when it works out of order or writes a cycle; a cyclic plan is surfaced (immediately + durably) instead of silently deadlocking; and the operator sees an inline DAG graph in the Inspector Todos tab. Proven by all gates green + a MANDATORY real chat-v2 + real backend + real Azure drive-through in which the agent writes a multi-step DAG (including a deliberate out-of-order and/or cycle scenario) and the advisory + Viz render live. CHANGE-129. No design note (bounded feature slice, not a research-eval spike).

## 2. User Stories

- **US-1** (soft enforce): 作為 agent loop，我希望在把某 todo 標成 in_progress/completed 但其 prerequisite 未完成時收到一則非阻擋的 ⚠️ 提醒，以便我能自我修正順序而不被強制中斷。
- **US-2** (cycle report): 作為 agent 與 operator，我希望依賴環被明確指出（tool observation 即時 + Active Plan 持久），以便一個 typo 造成的死結不會無聲地卡住計畫。
- **US-3** (viz): 作為 operator，我希望在 Inspector Todos tab 看到內嵌的 DAG 圖（拓撲分層 + 節點狀態），以便一眼看懂計畫的依賴結構與可平行步驟。
- **US-4** (drive-through, MANDATORY): 作為維護者，我希望在真 UI + 真後端 + 真 Azure 上實跑一個含 out-of-order / cycle 的多步 DAG，確認 advisory 進入 agent observation 且 Viz 正確渲染。
- **US-5** (closeout): CHANGE-129 + retrospective + navigators + close the 3 ADs; **NO new carryover AD**.

## 3. Technical Specifications

### 3.0 Architecture (backend 2 files + FE 1 file; NO migration / NO wire / NO codegen / NO sse.py / NO loop.py-signature / NO store)

```
EDIT  backend/src/agent_harness/_contracts/todo.py   — detect_cycles + plan_warnings + render cycle branch
EDIT  backend/src/agent_harness/tools/todo_tools.py  — append plan_warnings to handler result (soft)
EDIT  frontend/src/features/chat_v2/components/inspector/InspectorTodos.tsx — inline TodoDagGraph (leveled SVG)
NEW   backend/.../tests/unit/agent_harness/contracts/test_todo_dag.py  — extend (cycle + warnings + render)
NEW   frontend/tests/unit/features/chat_v2/.../InspectorTodos.test.tsx — extend (Viz + cycle chip)
UNTOUCHED  loop.py · sse.py · event_wire_schema.py · todo_store.py · migrations · chatStore.ts (depends_on already narrowed)
```

### 3.1 detect_cycles + plan_warnings (US-1, US-2) — `_contracts/todo.py`

- `detect_cycles(todos) -> set[str]`: iterative/recursive DFS with grey (on-stack) / black (done) coloring over the adjacency `id → depends_on ∩ known_ids` (unknown deps ignored, consistent with `ready_todos`). Any back-edge marks every node currently on the DFS stack up to the target as cyclic. Returns the set of cyclic ids. Empty for an acyclic plan.
- `plan_warnings(todos) -> list[str]`: ordered advisory lines, empty when clean:
  - out-of-order: for each todo whose status ∈ {in_progress, completed}, each KNOWN prereq not completed → `"'<title>' is marked <status> but prerequisite '<prereq title>' is not completed."`
  - cycle: if `detect_cycles` non-empty → one line `"Dependency cycle detected among: <titles> — these steps can never become ready; fix their depends_on."`
- `render_active_plan`: inside the pending-annotation branch, if the todo is in `detect_cycles(todos)` → `" (blocked by cycle: <cycle-member titles>)"`; else the existing `(ready)` / `(blocked by: …)`. `has_deps=False` path stays byte-identical to 57.140.

### 3.2 handler soft advisory (US-1, US-2) — `tools/todo_tools.py`

- After `await store.replace(todos)`: `result = f"Recorded plan: {summarize_todos(todos)}."`; `warnings = plan_warnings(todos)`; if warnings → `result += "\n\n⚠️ Plan advisory (not blocking):\n" + "\n".join(f"- {w}" for w in warnings)`. Return `result`. Write ALWAYS succeeds (soft). No schema/HITL/risk change.

### 3.3 Inspector DAG Viz (US-3) — `InspectorTodos.tsx`

- New self-contained `TodoDagGraph({ todos })` rendered above the existing flat list (list retained as the honest textual fallback / a11y).
- Compute topological levels via longest-path over known deps (cyclic nodes → a dedicated "cycle" lane); mirror `detect_cycles` locally (small TS DFS).
- Render an SVG: nodes = chips positioned by (level → x band, index → y) carrying a status/blocked/cycle `.badge` tone; edges = `<line>`/`<path>` from a node to each known prereq in `var(--border)`. testids: `todo-dag-graph`, `todo-dag-node-<id>`, `todo-dag-edge-<from>-<to>`, `todo-dag-cycle-node-<id>`.
- Reuse ONLY existing mockup classes + `var(--*)` tokens (no hex/oklch literal) → `styles-mockup.css` byte-identical; `check:mockup-fidelity` diff empty; `HEX_OKLCH_BASELINE` unchanged.

### 3.x What is explicitly NOT done

- HARD topological enforcement (reject out-of-order `write_todos`) — user picked SOFT; would contradict guidance-not-enforcement.
- Per-tenant advisory/verbosity policy (a C3 seam) — out of scope, NOT logged as a new AD (user: 不要產生其他工作).
- Draggable / interactive graph editing — read-only Viz only.
- Any new wire event / codegen / migration — the wire already carries `depends_on`.

### 3.y Validation (US-1..US-5)

Gates: mypy `src` 400 · run_all 11/11 (incl. `check_tool_descriptions` — no new tool param) · pytest 3206 + new · Vitest 927 + new · mockup 51 (`diff` empty) · `npm run lint && npm run build` (NO `--silent`) · black/isort/flake8 clean · LLM-SDK-leak clean. Plus the §3.3/US-4 drive-through (MANDATORY — user-facing Viz + advisory).

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 1 | `backend/src/agent_harness/_contracts/todo.py` | EDIT (detect_cycles + plan_warnings + render cycle branch) |
| 2 | `backend/src/agent_harness/tools/todo_tools.py` | EDIT (soft advisory append) |
| 3 | `frontend/src/features/chat_v2/components/inspector/InspectorTodos.tsx` | EDIT (TodoDagGraph Viz) |
| 4 | `backend/.../tests/unit/agent_harness/contracts/test_todo_dag.py` | EDIT/NEW (cycle + warnings + render tests) |
| 5 | `backend/.../tests/unit/.../test_todo_tools.py` | EDIT (advisory-append test) |
| 6 | `frontend/tests/unit/features/chat_v2/.../InspectorTodos.test.tsx` | EDIT (Viz + cycle chip tests) |
| — | `loop.py` · `sse.py` · `event_wire_schema.py` · `todo_store.py` · `chatStore.ts` · migrations | **UNTOUCHED** |

## 5. Acceptance Criteria

1. `plan_warnings` returns an out-of-order line for a non-pending todo with an unmet known prereq, a cycle line for a cyclic plan, and `[]` for a clean plan (unit-tested).
2. `detect_cycles` returns exactly the cyclic ids (self-safe already dropped by normalize; 2-node + 3-node + acyclic cases tested); ignores unknown deps.
3. `render_active_plan`: a cyclic pending node renders `(blocked by cycle: …)`; no-dep plans stay byte-identical to 57.140 (regression asserted).
4. The `write_todos` handler appends the ⚠️ advisory when warnings exist and the write still succeeds (returns the recorded-plan summary + advisory); clean plan → summary only (byte-identical to 57.156).
5. Inspector Todos tab renders the DAG graph (nodes + edges + cycle chips) above the flat list; `styles-mockup.css` diff empty; no oklch literal added.
6. **Drive-through PASS (MANDATORY, real UI + backend + LLM)** — agent writes a multi-step DAG incl. an out-of-order and/or cycle scenario; the advisory appears in the agent's tool observation AND the Viz renders the graph live; screenshot + observed-vs-intended in progress.md. (NOT gate-only.)
7. The 3 ADs CLOSED; CHANGE-129; calibration recorded (`task-primitive-dag-spike` 0.60, 2nd data point); navigators + next-phase-candidates updated. **NO new carryover AD.**

## 6. Deliverables

- [ ] US-1 soft out-of-order advisory in the handler observation
- [ ] US-2 `detect_cycles` + cycle advisory (immediate) + render cycle annotation (durable)
- [ ] US-3 Inspector TodoDagGraph leveled node-link Viz
- [ ] US-4 drive-through PASS (real chat-v2 + backend + Azure)
- [ ] US-5 CHANGE-129 + closeout; 3 ADs closed; NO new carryover

## 7. Workload Calibration

- Scope class **`task-primitive-dag-spike` 0.60** (2nd data point; 57.156 = 1st, ratio ~0.95-1.0 IN band → KEEP). Same shape as 57.156 (contract helper + handler + render + FE render + tests + drive-through), reuses ALL 57.140/156 machinery; the delta over 57.156 is a cycle helper + soft-advisory + a real SVG Viz (heavier FE than 57.156's textual line), offset by zero new data model / wire.
- **Agent-delegated: no** (parent-direct; `agent_factor` 1.0 → 3-segment form). The core is a small contract helper + a handler line + a bounded FE component I implement directly.
- Bottom-up est ~7.3 hr (cycle+warnings+render ~1.5 · handler ~0.3 · Viz ~2 · tests ~1.5 · drive-through ~1 · docs ~1) → class-calibrated commit ~4.4 hr (mult 0.60). Day-4 retro Q2 verifies; if ratio > 1.20 (drive-through-dominated) re-point 0.70 per the 57.156 note.

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| Risk Class E (stale `--reload` / orphan spawn-worker masks the advisory at drive-through) | Clean restart + verify sole live PID + startup log before driving; FE change → rebuild Vite (Day-0 §Common Risk Classes E) |
| SVG leveled layout fiddly / not robust | Leveled layout (longest-path) is the must-have; SVG edges the enhancement — if edges prove brittle, fall back to leveled node chips + retained textual `⤷ needs` (still a legitimate DAG viz) and note honestly; the flat list stays as the fallback |
| additive advisory breaks a byte-exact existing test (57.156 hit `test_serde_round_trip`) | Prong-2 grep the 3 test files Day-0; clean-plan path kept byte-identical so only new-scenario tests change |
| render cycle branch accidentally shifts the no-dep byte-identical guarantee | keep the cycle branch strictly inside the existing `has_deps and pending and depends_on` block; assert the 57.140 no-dep regression |
| mockup-fidelity drift from the SVG | reuse `.badge`/`var(--*)` only, no hex/oklch; `diff styles-mockup.css` must be empty; `check:mockup-fidelity` green |

## 9. Out of Scope (this sprint; → NOT logged as new ADs per user "不要產生其他工作")

- Hard topological enforcement — deliberately rejected (user picked soft).
- Per-tenant advisory policy, interactive graph editing, semantic dep suggestions — intentionally not started and NOT recorded as carryover ADs.
- PR / push — user requested pause; commit local only.
