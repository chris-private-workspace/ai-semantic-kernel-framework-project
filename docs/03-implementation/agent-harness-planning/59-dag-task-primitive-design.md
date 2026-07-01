# 59 — DAG task primitive: dependency-aware todos (design note)

**Purpose**: Extract the verified design of the Sprint 57.156 DAG task primitive — `Todo.depends_on` + topological readiness + dependency-aware `## Active Plan` render + chat-v2 panel, evolving the Sprint 57.140 linear primitive.
**Category / Scope**: 範疇 3 (task primitive) + 範疇 2 (tool) + frontend / Phase 57 / Sprint 57.156
**Created**: 2026-07-01
**Status**: Active
**Slice**: closes `AD-TaskPrimitive-DAG-Phase58` (the DAG evolution of the 57.140 linear primitive; scheduler = separate `AD-TaskPrimitive-Scheduler-Phase58`)

> **Modification History**
> - 2026-07-01: Initial creation (Sprint 57.156) — dependency-DAG task primitive (KEEP; drive-through STRONG PASS)

---

## 1. Spike Summary (US: dependency-aware todos)

The Sprint 57.140 task primitive modeled a plan as a flat `[{id,title,status}]` list (`_contracts/todo.py`); real multi-step work has prerequisites the flat list can't express, so the agent had no structured signal for what it could work on NOW vs what was blocked (deferred at 57.140 as `AD-TaskPrimitive-DAG-Phase58`). This spike adds `Todo.depends_on` end-to-end (contract → serde → tool schema → dependency-aware `## Active Plan` render → chat-v2 Todos panel), riding the existing 57.140 machinery so no migration / wire schema / codegen / loop.py / sse.py / store change is needed.

**Verdict (drive-through, real Azure gpt-5.2)**: KEEP — the agent authors a DAG, the wire carries it, the agent reasons about readiness, and the panel renders + dynamically re-computes ready/blocked; shipped additive + always-on (no flag; a no-dep plan is byte-identical to 57.140).

## 2. Decision Matrix

### 2.1 Guidance vs enforcement

| Option | Behavior | Verdict |
|--------|----------|---------|
| **Guidance (CHOSEN)** | the loop RENDERS `(ready)` / `(blocked by:…)` in `## Active Plan`; nothing gates the agent's `write_todos` on readiness | ✅ aligns with the agent-autonomy + guardrail-ESCALATE-not-block philosophy + the 57.140 nudge-not-force pattern; the agent stays controllable + can re-plan (fix a cycle) |
| Enforcement | the loop refuses to let the agent advance a blocked todo | ❌ over-constrains an autonomous agent; a wrong dependency (or cycle) would deadlock the plan with no escape → `AD-TaskPrimitive-DAG-Enforce-Phase58` if ever wanted |

### 2.2 Readiness — direct-dependency vs transitive resolution

| Option | Complexity | Verdict |
|--------|-----------|---------|
| **Direct-dependency (CHOSEN)** | a pending todo is ready iff every KNOWN dep is `completed` — one pass, O(n·d) | ✅ transitive blocking falls out for free (a mid-chain dep is neither ready nor completed until its own parent is done); cycle-safe by construction (no recursion) |
| Transitive topological sort | resolve the full reachability closure | ❌ needs cycle detection + recursion for a result the direct check already yields correctly; unnecessary machinery for a guidance nudge |

### 2.3 Unknown dependency id policy

| Option | On a dep referencing a non-existent id | Verdict |
|--------|----------------------------------------|---------|
| **Ignore (CHOSEN)** | treat as satisfied — `ready_todos` skips deps not in the plan | ✅ a typo, or a dep whose todo was dropped by tolerant serde, must NOT permanently deadlock the plan; the annotation only lists deps that exist |
| Treat as blocking | a todo with an unknown dep stays forever blocked | ❌ a single typo silently freezes a step with no recovery signal to the agent |

## 3. Verified Invariants (each with file:line + verification command)

- **A no-dependency plan renders byte-identical to 57.140** — `render_active_plan` branches on `has_deps = any(t.depends_on for t in todos)` (`_contracts/todo.py`); when false it emits the original instruction + flat `- [status] title` lines.
  - Verify: `test_render_no_deps_is_byte_identical_to_57140` — `backend/tests/unit/agent_harness/state_mgmt/test_todo_dag.py`.
- **`depends_on` round-trips tolerantly** — `_todo_to_dict` emits `depends_on: list`; `_normalize_depends_on` drops self-ref / empties / non-list + order-preserving dedup (`_contracts/todo.py`).
  - Verify: `test_depends_on_round_trips` + `test_depends_on_tolerant_non_list` + `test_depends_on_drops_self_ref_empties_and_dedups`.
- **`ready_todos` is direct-dependency, cycle-safe, unknown-dep-ignored** — single pass over `todo.depends_on`, dep must be in `known` and in `completed` (`_contracts/todo.py`).
  - Verify: `test_ready_chain_unblocks_progressively` + `test_ready_diamond_needs_both_parents` + `test_ready_ignores_unknown_dep` + `test_ready_cycle_leaves_both_blocked` + `test_ready_empty_list` + `test_ready_excludes_non_pending`.
- **The wire carries `depends_on` with sse.py + the wire schema UNCHANGED** — `serialize_loop_event` uses `todos_to_jsonb(list(event.todos))` (`sse.py:261`); `todos_updated = {todos:"Record<string,unknown>[]"}` is generic (`event_wire_schema.py:242-244`, count 26).
  - Verify: **drive-through** — the `todos_updated` event carried `depends_on` per todo (trace `743c72d4…`); the FE panel rendered blocked badges + "⤷ needs" lines.
- **The FE mirrors the backend ready rule** — `InspectorTodos.tsx` computes `blocked = pending && deps.some(d => titleById.has(d) && !completedIds.has(d))`.
  - Verify: `InspectorTodos.test.tsx` (blocked badge + deps line; deps-completed → no badge; badge className `badge`) + **drive-through Leg 2** (completing step 1 unblocked steps 2+3 live).
- **Full-suite green** — `cd backend && python -m pytest -q` → **3139 passed / 6 skipped**; `mypy src` → 399/0; `python scripts/lint/run_all.py` → 11/11; frontend Vitest 925 / 148 files; mockup 51 byte-identical.

## 4. Cross-Category Contracts

**No new contract.** `Todo` (範疇 3 task-primitive contract) gains a defaulted field — the `MemoryLayer` / `TodoStore` ABC signatures are unchanged, `TodosUpdated` (範疇 12 event) carries the richer `Todo` transparently. No new ABC / event / DB column / wire type (count 26). Not in `17-cross-category-interfaces.md` (the task primitive is a 57.140-local contract, not a cross-category single-source interface).

## 5. Open Invariants (verified vs deferred)

**Verified in this spike**: `Todo.depends_on` end-to-end (contract → serde → tool schema → dependency-aware render → panel); direct-dependency readiness (cycle-safe, unknown-dep-ignored); byte-identical no-dep render; the agent authors + reasons about a DAG on the real chat flow; the panel renders + dynamically re-computes ready/blocked (real Azure).

**Deferred (NOT verified here)**:
- **Topological EXECUTION enforcement** (block the agent on readiness) — `AD-TaskPrimitive-DAG-Enforce-Phase58`.
- **Cross-burst auto-continue scheduler** (auto-advance ready steps across sends) — `AD-TaskPrimitive-Scheduler-Phase58` (research #3; its durable spine shipped 57.140).
- **Cycle validation / auto-repair surfaced to the agent** (today a cycle just renders both blocked) — `AD-TaskPrimitive-DAG-CycleReport-Phase58`.
- **Inline turn-block DAG visualization** (a graph in the chat stream, not just the Inspector tab) — `AD-TaskPrimitive-DAG-Viz-Phase58`.

## 6. Rollback / Fallback

Additive + always-on (no flag). To revert: drop `Todo.depends_on` (+ the serde/`ready_todos`/render branch) + the tool schema field + the 2 FE edits → the primitive reverts to the 57.140 flat list; stored blobs with a `depends_on` key deserialize harmlessly (tolerant serde ignores it once the field is gone). No data migration (JSONB, field-additive). Est: revert 4 files.

## 7. References

- `backend/src/agent_harness/_contracts/todo.py` — `Todo.depends_on` + `_normalize_depends_on` + `ready_todos` + `render_active_plan`
- `backend/src/agent_harness/tools/todo_tools.py` — `write_todos` schema `depends_on`
- `frontend/src/features/chat_v2/store/chatStore.ts` — `TodoItem.depends_on` + `todos_updated` map
- `frontend/src/features/chat_v2/components/inspector/InspectorTodos.tsx` — blocked badge + "⤷ needs" line
- `backend/tests/unit/agent_harness/state_mgmt/test_todo_dag.py` + `.../tools/test_todo_tools.py` + `frontend/tests/.../InspectorTodos.test.tsx` — tests
- `docs/.../sprint-57-156/progress.md` Day 3 + `artifacts/` — drive-through evidence (2 screenshots + trace)
- `44-task-primitive-write-todos-design.md` — the 57.140 linear primitive this evolves
- CHANGE-123

## 8. Modification History

- 2026-07-01: Initial creation (Sprint 57.156) — dependency-DAG task primitive (closes `AD-TaskPrimitive-DAG-Phase58`; KEEP, drive-through STRONG PASS)
