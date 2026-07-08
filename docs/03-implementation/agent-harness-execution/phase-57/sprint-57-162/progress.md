# Sprint 57.162 Progress — DAG soft-enforce advisory + cycle report + Inspector Viz

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-162-plan.md) · [Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-162-checklist.md)

Closes the 3 remaining 57.156 DAG carryovers: `AD-TaskPrimitive-DAG-Enforce-Phase58` (SOFT — user pick), `AD-TaskPrimitive-DAG-CycleReport-Phase58`, `AD-TaskPrimitive-DAG-Viz-Phase58`. Parent-direct. User directive: 完成即暫停, 不要產生其他工作 → NO push/PR, NO new carryover AD.

---

## Day 0 — 2026-07-08 — Plan-vs-Repo Verify (三-prong) + Branch

### Branch
- `feature/sprint-57-162-dag-enforce-cyclereport-viz` from HEAD `1819180d` (= `main` `827917de` + unmerged REFACTOR-010 docs; sprint CODE == main). NOT pushed.

### Drift findings (三-prong)

| ID | Prong | Finding | Implication |
|----|-------|---------|-------------|
| D-render-cycle-label | 2 | `todo.py:207-216` — a cyclic pending node with known-unmet deps hits the `(blocked by: <titles>)` branch (confirmed by read) | the new `(blocked by cycle: …)` branch genuinely REPLACES a misleading label (not a no-op) ✓ |
| D-sse-serde | 2 | `sse.py:261` serializes `TodosUpdated` via `todos_to_jsonb(list(event.todos))` → `_todo_to_dict` already emits `depends_on` (`todo.py:101`) | Viz needs **ZERO** wire/sse/codegen change — `depends_on` already on the wire (57.156 confirmed) ✓ |
| D-existing-tests | 2 | `test_todo_dag.py` (14) / `test_todo_tools.py` (7) use CLEAN plans (no out-of-order / cycle) + substring `"3 todos" in result`; `test_render_no_deps_is_byte_identical_to_57140` byte-exact | additive advisory + cycle branch are additive-SAFE: clean-plan path stays byte-identical, no-dep render unchanged ✓ |
| D-existing-tests-fe | 2 | `InspectorTodos.test.tsx` (7) uses `getByText(<full title>)` + `getByText("pending"/"completed"/"in_progress")` (global) | Viz nodes MUST use numeric step labels + `aria-label` full-title (attribute, not getByText-matched), NO status-word text → ZERO existing-test churn ✓ |
| D-ready-todos-consistency | 2 | `ready_todos:149-169` uses KNOWN-deps-only (unknown ignored) | `detect_cycles` MUST use the same known-deps-only adjacency for consistency ✓ |
| Prong 3 schema | 3 | N/A — `session_todos.todos` JSONB blob carries `depends_on` schema-free; no migration/ORM column | — |

### Baselines (re-verified Day-0)
- backend targeted: `test_todo_dag.py` 14 + `test_todo_tools.py` 7 = **21 passed** (green baseline)
- FE: `InspectorTodos.test.tsx` **7 passed**
- mypy `src/agent_harness/_contracts/todo.py` + `tools/todo_tools.py`: **clean**
- CHANGE-129 **free** (highest = CHANGE-128 / 57.161); wire 26 (event_wire_schema.py:242 `todos_updated` generic — UNTOUCHED)
- Full pytest/Vitest/mockup/run_all counts → verified at Day-2 full gate (CLAUDE.md 57.161: pytest 3206 · Vitest 927 · mockup 51 · run_all 11/11 · mypy src 400)

### Go/no-go
- **0 drift, scope-shift 0% → PROCEED.** All plan assumptions confirmed against real code. Viz FE-only confirmed (D-sse-serde). Additive-safe confirmed (D-existing-tests).

---

## Day 1 — 2026-07-08 — Backend: cycle helper + warnings + render + soft advisory

- `_contracts/todo.py`: `detect_cycles` (DFS grey/black, known-deps-only, self-safe) + `plan_warnings` (out-of-order + cycle lines, `[]` when clean) + `render_active_plan` cycle branch (cyclic pending → `(blocked by cycle: …)`; no-dep byte-identical; instruction extended). MHist trimmed to fit E501 (first draft 106 chars → shortened).
- `tools/todo_tools.py`: handler appends `plan_warnings` advisory after `store.replace` — **write always succeeds** (soft); clean plan → summary only.
- Tests: `test_todo_dag.py` +14 (detect 7 / warnings 5 / render 2) → 28; `test_todo_tools.py` +3 → 10. One test-only fix: `test_render_non_cycle_block_unchanged` initially asserted `"blocked by cycle" not in out` — FAILED because the has_deps INSTRUCTION now mentions the marker; corrected to check no todo LINE carries the annotation.
- Partial gate: **38 passed** · mypy targets clean · black/isort applied · flake8 rc=0.

## Day 2 — 2026-07-08 — FE Inspector DAG Viz + full gate

- `InspectorTodos.tsx`: `detectCyclesTs` (mirrors backend) + `TodoDagGraph` (longest-path levels w/ cycle guard; fixed-size circular nodes coloured by status/blocked/cycle via `var(--success/--info/--warning/--danger/--border-strong)`; numeric labels + `aria-label` full title to avoid `getByText` collision; SVG edges `var(--border)`, cycle edge dashed `var(--danger)`; testids graph/node/edge/cycle-node). Rendered only when `hasDeps`; flat list retained.
- Tests: `InspectorTodos.test.tsx` +3 (graph+edges / no-graph-for-flat / cycle-marker) → 10.
- **Full gate GREEN**: mypy `src` **400/0** · run_all **11/11** · backend pytest **3223 passed / 6 skipped** (+17 = 3206 baseline) · Vitest **930 passed** (149 files, +3) · `npm run lint` rc=0 + `npm run build` rc=0 · mockup **byte-identical, hex/oklch 51 = baseline** (no new literal) · black/isort/flake8 clean · LLM-SDK-leak clean.

## Day 3 — 2026-07-08 — Drive-through (real UI + real backend + real Azure) — **STRONG PASS**

### Clean restart (Risk Class E)
- :8000 held by an **orphan `multiprocessing.spawn` worker PID 68500** (parent 39440 DEAD) from 7/7 18:25 → stale pre-57.162 code (textbook Risk Class E). Killed 68500 (python, not node — Vite :3007 PID 31616 confirmed untouched); :8000 freed; started a fresh **no-`--reload`** uvicorn (`api.main:app --app-dir src`, `load_dotenv()` walks up to root `.env` → Azure creds) — startup log `api.main: startup complete` 19:28:04, sole live process.
- Recovered the AD-Playwright-MCP-Recovery blocker: killed the stuck MCP chrome tree (profile `mcp-chrome-903abde`) to release the lock, then Playwright navigated.

### Drive-through (real chat-v2 :3007 + real backend + real Azure gpt-5.2, session `344890a3…`)
- Prompt induced `write_todos` with a deliberate 4-item DAG: `b` in_progress before prereq `a`; `c↔d` cycle.
- **Advisory (US-1 + US-2) — observed in the REAL tool observation** (evaluate + screenshot): `Recorded plan: 4 todos (0 completed, 1 in_progress, 3 pending).` + `⚠️ Plan advisory (not blocking):` + `- 'Write migration' is marked in_progress but prerequisite 'Set up database' is not completed.` + `- Dependency cycle detected among: Deploy service, Run smoke tests — these steps can never become ready; fix their depends_on.` → **write SUCCEEDED (not rejected) = soft enforce confirmed live**; agent `stop: end_turn`, Verification 0.99.
- **Viz (US-3) — DAG graph rendered live in the Inspector Todos tab** (DOM evaluate + screenshot): `todo-dag-graph` 238×94px; 4 nodes a/b/c/d labelled 1-4; aria-labels reflect status (`3. Deploy service (cycle)` / `4. Run smoke tests (cycle)`); edges `a→b` solid + `d→c`/`c→d` dashed cycle; cycle-node markers c/d; cyclic node border computed `2px dashed oklch(0.65 0.21 25)` (= `var(--danger)` resolves to a real mockup colour); flat list retained below.
- **Observed vs intended**: exactly as designed — advisory appears without blocking the write; cyclic nodes visually distinct (dashed red); no console error from the Viz. Screenshot: `artifacts/sprint-57-162-drivethrough-dag-viz-advisory.png`.
- Note (honest scope): the durable `render_active_plan` cycle annotation (cross-send system-prompt injection, not directly UI-visible) is covered by unit test `test_render_cycle_annotates_distinctly`; it shares `detect_cycles` with the drive-through-proven immediate advisory.

---
