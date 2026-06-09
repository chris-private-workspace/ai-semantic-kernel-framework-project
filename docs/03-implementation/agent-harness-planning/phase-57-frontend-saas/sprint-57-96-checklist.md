# Sprint 57.96 — Checklist (Cat 11 Subagent child turn-stream nesting — Scope B; the Tree node expands to the child's per-turn TAO loop)

**Plan**: [`sprint-57-96-plan.md`](./sprint-57-96-plan.md)
**Created**: 2026-06-09
**Status**: Day 0-4 done — drive-through PASS; closeout committed; **push + PR pending user authorization**

> Rule: only `[ ]` → `[x]`; never delete unchecked items; defer with `🚧 + reason`.
> CHANGE (feature-continuation — extend the validated Cat 11 arc: 57.94 child loop → 57.95 node visible → 57.96 node expands) → CHANGE-063. **NO design note** (not a spike — `sprint-workflow.md §Step 5.5`), BUT a NEW event type = contract addition → **17.md registration MANDATORY** + `check_event_schema_sync` green. Gate = full backend pytest + Vitest green (NET deltas documented) + **drive-through PASS** (the Tree subagent node expands to the child's per-turn TAO). Locked scope (AskUserQuestion 2026-06-09): relay mechanism = **Wrapper event** `SubagentChildEvent(subagent_id, inner)`; depth = **TAO essentials subset** (`TurnStarted`/`LLMResponded`/`ToolCallRequested`/`ToolCallExecuted`/`Failed`). Out: recursion depth > 1, full-fidelity events, base field, TEAMMATE/HANDOFF, inline `{a.turns}t`.

---

## Day 0 — Plan-vs-Repo Verify + Branch

### 0.1 Three-prong Day-0 verify
- [x] **Prong 1 (path)**: confirmed (1 Explore agent map) — `LoopEvent` base `_contracts/events.py:56` (event_id/timestamp/trace_context only) / `SubagentSpawned` `:349` (subagent_id/mode/parent_session_id) + `SubagentCompleted` `:356` / TAO types `TurnStarted` `:73`, `LLMResponded` `:92`, `ToolCallRequested` `:183`, `ToolCallExecuted` `:193`, `ToolCallFailed` `:201`, `LoopCompleted` `:127` / `ForkExecutor._drive` drain loop `fork.py:102-114` / `SubagentEventEmitter` type `dispatcher.py:90` + `_event_emitter` `:109/:134` + emit spawn `:189-196` / completed `:234/:242` / router relay `_relay_subagent_event` `router.py:237-238` + `_drain_subagent_frames` `:363-385` (GENERIC) / `serialize_loop_event` subagent branches `sse.py:306-326` + LLMResponded `:153-171` + NotImplementedError fallthrough `:429` / frontend `features/subagent/types.ts:62-73` (SubagentNode flat) + `chat_v2/store/chatStore.ts:136/:638-692/:695-743` + `chat_v2/components/inspector/InspectorTree.tsx:73-95/:132-173` (recursive) + `chat_v2/components/blocks/SubagentForkBlock.tsx:54-93` (inline, separate). (progress.md Day-0 Prong 1)
- [x] **Prong 2 (content)**: confirmed — (a) premise 1 CONFIRMED-NEEDED: child TAO events carry NO session/subagent identifier → a tag is needed (wrapper chosen); (b) premise 2 CONFIRMED-NEEDED: `_drive` discards all child events except LLMResponded/LoopCompleted, ForkExecutor has no emitter; (c) router relay ALREADY generic over any LoopEvent → router.py ZERO change; (d) premise 3 PARTIALLY-EXISTS: InspectorTree recursive scaffold exists, but SubagentNode has no childEvents + no store routing; (e) the inline `0t` is `a.turns` integer count (separate component), NOT a token bug → out of scope. (progress.md Day-0 Prong 2)
- [x] **Prong 2.5 (event / drift)**: confirmed — **D1**: the wrapper `SubagentChildEvent` IS a `LoopEvent` → rides the SAME 57.95 emitter + already-generic router buffer-drain for FREE (only a new SSE serializer branch needed). **D2**: child events must be tagged with the spawn `subagent_id` (NOT `child_session_id` uuid4 `fork.py:105`) so the frontend routes to the node the spawn created. **D3**: a NEW event type touches `check_event_schema_sync` (the one gating lint) + 17.md (mandatory contract registration). **D4 (drift vs 57.95 carryover)**: carryover said Scope B "needs a LoopEvent base parent_session_id/depth field" — locked decision is a WRAPPER (base untouched); router.py UNCHANGED (carryover implied relay work — already generic). (progress.md Day-0 Prong 2.5)
- [x] **Prong 3 (schema)**: N/A — no DB/migration/ORM change. (Event-contract addition handled via `check_event_schema_sync` in Prong 2.5/Day-1, not DB schema.)
- [x] **Baseline capture**: baseline = `main` HEAD (57.95 merged `aebeab4c`; CI-green pytest 2277 / mypy 0/351 / run_all 10/10 / Vitest baseline) — capture exact pytest + Vitest numbers at branch creation; record NET delta after edits
- [x] **`check_event_schema_sync` source locate**: Day-1 find what the lint reads (hand-maintained event↔wire map vs generated file) so the new type registers green
- [x] **`ForkExecutor` emitter threading path locate**: Day-1 read the executor ABC + the dispatcher call site → decide emitter+subagent_id via `spawn`/`run` call (optional params, default None) vs `__init__`; confirm AS_TOOL shares the path
- [x] Catalogue Day-0/Day-1 drift in progress.md; **go/no-go = GO** (feasibility CONFIRMED — wrapper rides existing relay; router/loop/base UNCHANGED; the 4 layers are scoped)

### 0.2 Branch
- [x] Branch `feature/sprint-57-96-subagent-child-turnstream` from `main` (`aebeab4c`)
- [x] plan + checklist + progress committed (Day-0 commit)

---

## Day 1 — Wrapper event + ForkExecutor forwarding (US-1/US-2)

### 1.1 The `SubagentChildEvent` wrapper + serializer (US-1)
- [x] **`_contracts/events.py`** — NEW `SubagentChildEvent(LoopEvent)` dataclass (`subagent_id: str`, `inner: LoopEvent`), near `SubagentSpawned`/`SubagentCompleted`; match the neighbours' `kw_only`/default convention; file-header MHist
  - DoD: `mypy src/ --strict` 0; the dataclass instantiates with an inner `LLMResponded`
- [x] **`sse.py`** — NEW `serialize_loop_event` branch: `SubagentChildEvent` → `{type:"subagent_child_event", data:{subagent_id, inner: serialize_loop_event(inner)}}`; defensive skip if inner serialize raises/None; MHist
  - DoD: a unit serialize test round-trips the wrapper + inner LLMResponded
- [x] **`check_event_schema_sync` source** — register `SubagentChildEvent` ↔ `subagent_child_event` both sides (Day-0 locate)
  - DoD: `python scripts/lint/run_all.py` → `check_event_schema_sync` green

### 1.2 ForkExecutor forwards the TAO subset (US-2)
- [x] **`subagent/modes/fork.py`** — `_TAO_CHILD_EVENT_TYPES = (TurnStarted, LLMResponded, ToolCallRequested, ToolCallExecuted, ToolCallFailed)`; in `_drive` drain loop, `if emitter is not None and isinstance(ev, _TAO_CHILD_EVENT_TYPES): await emitter(SubagentChildEvent(subagent_id=subagent_id, inner=ev))`; preserve final-answer/token extraction; emitter + subagent_id param
  - DoD: a fake child loop yielding TAO + LoopCompleted → emitter receives SubagentChildEvent ONLY for the TAO subset, tagged with subagent_id
- [x] **`subagent/dispatcher.py`** — thread `self._event_emitter` + the spawn `subagent_id` (the one used for SubagentSpawned `:189-196`) into the `ForkExecutor` drive; MHist
  - DoD: the child events carry the SAME subagent_id as SubagentSpawned (routing test)
- [x] **executor ABC (conditional)** — if `spawn`/`run` signature needs the params, keep them optional (default None) so TEAMMATE/HANDOFF unaffected; confirm AS_TOOL inherits forwarding (shares ForkExecutor) or note separate slice in plan §9
- [x] **mypy clean** on the backend files (full `src --strict` 0)

---

## Day 2 — Frontend childEvents + store routing + render (US-3) + tests (US-1..US-4)

### 2.1 Frontend data model + store + render (US-3)
- [x] **`features/subagent/types.ts`** — `SubagentNode.childEvents: ChildTurnEvent[]` + NEW `ChildTurnEvent` interface (`kind`, `turn?`, `text?`, `toolName?`, `toolCallId?`); init `childEvents: []` on spawn-create
- [x] **`chat_v2/store/chatStore.ts`** — NEW `case "subagent_child_event"`: route by `data.subagent_id` → find node (defensive-create) → push parsed `ChildTurnEvent` (map `inner.type` → kind, extract turn/text/toolName from `inner.data`)
- [x] **`chat_v2/components/inspector/InspectorTree.tsx`** — `NodeRow` renders the per-turn `childEvents` under the node (reuse `.indent`); empty `childEvents` → only the collapsed node (57.95 look preserved); depth>1 recursion untouched
  - DoD: `npm run build` + `tsc` clean

### 2.2 Backend tests (US-1/US-2/US-4)
- [x] **wrapper serialize round-trip** — `serialize_loop_event(SubagentChildEvent("x", LLMResponded(...)))` → expected nested dict; non-serializable inner → skipped (defensive)
- [x] **ForkExecutor forwarding** — fake child loop (TurnStarted+LLMResponded+ToolCallRequested+ToolCallExecuted+LoopCompleted) + capturing emitter → SubagentChildEvent ONLY for the TAO subset (not LoopCompleted), each tagged subagent_id; final-answer/token still extracted (NEW `test_subagent_child_turnstream.py`)
- [x] **no-regression** — FORK with no emitter → no forwarding (byte-identical to 57.94); no-TAO stream → SSE byte-identical to 57.95
- [x] **`loop.py` + `router.py` diff = 0** — `git diff main..HEAD -- backend/src/agent_harness/orchestrator_loop/loop.py backend/src/api/v1/chat/router.py` empty

### 2.3 Frontend tests (US-3/US-4)
- [x] **`chatStore` routing** — `subagent_spawned` then `subagent_child_event` (same id) → node.childEvents has the entry; out-of-order child_event → defensive-create
- [x] **`InspectorTree` render** — node with childEvents → per-turn rows render; empty childEvents → only collapsed node (57.95 preserved)
- [x] **existing 57.95 store/Tree tests green** — spawned/completed node tests UNCHANGED (childEvents additive)

---

## Day 3 — Full regression + drive-through (US-5) + CHANGE-063

### 3.1 Full gate sweep
- [x] **Full backend pytest green (NET delta documented)** — baseline 2277 → expected +N; NO test deleted; 57.12 + 57.94 + 57.95 tests UNCHANGED + green
- [x] **Full Vitest green (NET delta documented)** — baseline → expected +N; existing chatStore/InspectorTree tests UNCHANGED
- [x] **mypy 0 + run_all 10/10 + format chain** — mypy `src --strict` 0; run_all **10/10** (LLM SDK leak 0; AP-1 — forward NOT flagged as pipeline; **`check_event_schema_sync` green** — new type registered; check_cross_category_import green); `black`/`isort`/`flake8 src tests` clean — **run each INDEPENDENTLY, not `&&`-chained** (57.95 CI lesson)

### 3.2 Drive-through (US-5 — the Tree node expands to the child's TAO)
- [x] **Clean backend restart (Risk Class E)** — kill stale 57.95 reloader+spawn-worker (python, not node); verify :8000 FREE → `dev.py start backend` → fresh PID owns :8000; frontend node untouched; Azure live
- [x] **Drove a tool-using `task_spawn` subagent through real UI + real backend + real Azure** — a prompt that makes the agent `task_spawn` a sub-task whose child must call a tool (e.g. echo_tool); BEFORE: Tree node collapsed (57.95); AFTER: expand node → child's per-turn TAO rows (LLMResponded + the tool call). Observed-vs-intended table in progress.md Day 3.2
  - Evidence: `artifacts/sprint-57-96-tree-{1-collapsed,2-expanded-child-tao}.png` + snapshot
- [x] **Backend confirm** — Inspector Trace shows the relayed `subagent_child_event` frames (child's TurnStarted/LLMResponded/ToolCall, tagged subagent_id) — proof of the forward

### 3.3 CHANGE-063 + 17.md (NO design note — feature-continuation)
- [x] `claudedocs/4-changes/feature-changes/CHANGE-063-subagent-child-turnstream-nesting.md` written
- [x] **`17-cross-category-interfaces.md`** — register `SubagentChildEvent` ↔ `subagent_child_event` in the Cat 11/Cat 12 event registry (MANDATORY — new event type)

---

## Day 4 — Closeout

### 4.1 Closeout
- [x] Full validation (parent re-verified): pytest +N / Vitest +N / mypy 0/351 / run_all 10/10 (incl. check_event_schema_sync) / 57.12 + 57.94 + 57.95 tests unchanged / `loop.py` + `router.py` diff = 0 / **drive-through PASS** (screenshots + before/after observed-vs-intended)
- [x] progress.md (Day 0-3.2) + retrospective.md (Q1-Q7) — NO design-note 8-pt gate (feature-continuation, not a spike)
- [x] Calibration: `subagent-child-turnstream-nesting` 0.55 (1st data point) + `agent_factor` 1.0 (parent-direct); recorded `calibration-log.md §3` + `sprint-workflow.md §Scope-class matrix` row; carryover (recursion depth>1 / full-fidelity events / TEAMMATE-HANDOFF / inline {a.turns}t / span nesting / failure policies) → next-phase-candidates.md
- [x] MEMORY.md pointer + `project_phase57_96_subagent_child_turnstream.md` subfile + CLAUDE.md lean (Current Sprint row + Last Updated) + CHANGE-063 + 17.md event registration
- [ ] commit (Day 0-N) + push + PR — **push + PR pending user authorization**
