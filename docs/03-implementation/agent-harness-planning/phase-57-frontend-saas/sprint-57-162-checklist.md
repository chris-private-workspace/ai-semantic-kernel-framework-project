# Sprint 57.162 — Checklist (DAG soft-enforce advisory + cycle report + Inspector Viz)

[Plan](./sprint-57-162-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch

### 0.1 Three-prong Day-0 verify (against HEAD `1819180d`; code == `main` `827917de`)
- [x] **Prong 1 — path verify**: 3 source + 3 test files present; `CHANGE-129` free (highest = 128)
- [x] **Prong 2 — content verify** (drift → progress.md):
  - [x] **D-render-cycle-label** — confirmed cyclic pending node hits `(blocked by: …)` → new branch replaces a misleading label
  - [x] **D-sse-serde** — `sse.py:261` `todos_to_jsonb` already emits `depends_on` → Viz NO wire/sse change
  - [x] **D-existing-tests** — clean-plan paths + `"3 todos"` substring → additive-safe; FE `getByText` collision avoided via numeric-label Viz
  - [x] **D-ready-todos-consistency** — `ready_todos:152-172` known-deps-only; `detect_cycles` mirrors it
- [x] **Prong 3 — schema verify**: N/A (JSONB blob, no migration/ORM column)
- [x] **D-baselines** — todo tests 21 green · InspectorTodos 7 green · mypy targets clean · CHANGE-129 free (full counts at Day-2 gate)
- [x] **Catalog drift** — progress.md Day-0 table
- [x] **Go/no-go** — 0 drift → PROCEED

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-162-dag-enforce-cyclereport-viz` (from HEAD `1819180d`; done pre-plan)

---

## Day 1 — Backend: cycle helper + warnings + render + soft advisory (US-1, US-2)

### 1.1 `detect_cycles` + `plan_warnings` (`_contracts/todo.py`)
- [x] **`detect_cycles(todos) -> set[str]`** — DFS grey/black over known-deps-only adjacency; 7 tests (2/3-node/partial/acyclic/unknown/self/empty)
- [x] **`plan_warnings(todos) -> list[str]`** — out-of-order + cycle line; `[]` when clean (5 tests)

### 1.2 `render_active_plan` cycle branch (`_contracts/todo.py`)
- [x] **cyclic pending node → `(blocked by cycle: <titles>)`**; no-dep byte-identical (57.140 regression asserted); non-cycle block unchanged

### 1.3 Soft advisory in handler (`tools/todo_tools.py`)
- [x] **append `plan_warnings` to result; write always succeeds** — clean → summary only (byte-identical); out-of-order + cycle → ⚠️ advisory (3 tests)

### 1.x Partial gate
- [x] `test_todo_dag.py` 26 + `test_todo_tools.py` 12 = **38 passed** · mypy targets clean · black/isort applied · flake8 rc=0

---

## Day 2 — FE Inspector DAG Viz + full gate (US-3)

### 2.1 `TodoDagGraph` leveled node-link Viz (`InspectorTodos.tsx`)
- [x] **inline SVG DAG above the flat list** — longest-path levels (cycle-guarded) + status/blocked/cycle circular nodes + edges; `var(--*)` only; testids graph/node/edge/cycle-node; flat list retained
- [x] **mockup-fidelity**: `check:mockup-fidelity` PASS — styles-mockup.css byte-identical; hex/oklch **51 = baseline** (no new literal)

### 2.2 FE + backend unit tests
- [x] **Vitest** `InspectorTodos.test.tsx` +3 (graph+edges / no-graph-for-flat / cycle-marker) → 10 passed
- [x] **backend** `test_todo_dag.py` 28 + `test_todo_tools.py` 10 green

### 2.x Full gate
- [x] mypy `src` **400/0** · run_all **11/11** · backend pytest **3223/6skip** (+17) · Vitest **930** (+3) · `npm run lint`+`build` rc=0 · mockup **51 byte-identical** · black/isort/flake8 clean · LLM-SDK-leak clean

---

## Day 3 — Drive-through (US-4) — real UI + real backend + real Azure

### 3.1 Clean restart (Risk Class E)
- [x] killed orphan spawn-worker PID 68500 (parent 39440 DEAD, 7/7 stale code) — python not node (Vite :3007 untouched); fresh no-`--reload` uvicorn, sole live PID, startup log 19:28:04; recovered stuck MCP chrome profile lock

### 3.2 Drive-through (MANDATORY — NOT gate-only) — **STRONG PASS**
- [x] real chat-v2 :3007 + real backend (57.162 code) + real Azure gpt-5.2 (session `344890a3…`, `stop: end_turn`, Verification 0.99); agent `write_todos` the 4-item DAG
- [x] **out-of-order + cycle**: `⚠️ Plan advisory (not blocking):` in the REAL observation — out-of-order (Write migration) + cycle (Deploy service, Run smoke tests); **write SUCCEEDED = soft enforce confirmed**
- [x] **Viz (real UI)**: `todo-dag-graph` 238×94px live; 4 nodes 1-4; edges a→b + c↔d dashed cycle; cycle-node markers c/d; `var(--danger)` → `oklch(0.65 0.21 25)`; flat list retained
- [x] Screenshot `artifacts/sprint-57-162-drivethrough-dag-viz-advisory.png` + observed-vs-intended → progress.md Day 3

---

## Day 4 — CHANGE-129 + closeout

### 4.1 CHANGE-129
- [x] **`CHANGE-129-dag-enforce-cyclereport-viz.md`** (gap + soft-advisory/cycle/viz fix + drive-through PASS + 3 ADs closed). No design note (bounded feature slice).

### 4.2 Closeout
- [x] retrospective.md Q1-Q7 + calibration (`task-primitive-dag-spike` 0.60, 2nd data point ~1.0-1.1 IN band → KEEP)
- [x] Final gate sweep: pytest 3223/6skip · Vitest 930 · mypy src 400/0 · run_all 11/11 · mockup 51 · build+lint rc=0 · LLM-SDK-leak clean
- [x] Navigators: CLAUDE.md Current-Sprint + Last-Updated (lean) · MEMORY.md pointer + subfile · next-phase-candidates (CLOSED 3 ADs, §Shipped Pointer Index row) · sprint-workflow matrix (2nd data point)
- [x] Anti-pattern self-check (retro Q4): AP-2/3/4/6/8/11 clean; v2 lints 11/11; **NO new carryover AD** (user: 不要產生其他工作)
- [x] **Commit (local only)** — staged ONLY sprint files (not the pre-existing D/M/untracked noise). ⏳ PR push + open: **NOT done** (user 完成即暫停; push outward-facing → pending explicit user go)
