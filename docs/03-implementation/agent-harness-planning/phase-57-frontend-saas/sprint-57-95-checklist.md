# Sprint 57.95 — Checklist (Cat 11 Subagent SSE Relay — node-level; child no longer headless in the Tree)

**Plan**: [`sprint-57-95-plan.md`](./sprint-57-95-plan.md)
**Created**: 2026-06-09
**Status**: Day 0-4 done — drive-through PASS; closeout committed; **push + PR pending user authorization**

> Rule: only `[ ]` → `[x]`; never delete unchecked items; defer with `🚧 + reason`.
> CHANGE (feature-continuation — wire an existing-but-unwired Cat 11 → Cat 12 emitter) → CHANGE-062. **NO design note** (not a spike — `sprint-workflow.md §Step 5.5`). Gate = full backend pytest green (NET delta documented) + **drive-through PASS** (the Inspector Tree shows the subagent node, where it said "no subagents" — the 2026-06-06 audit gap). Locked scope: **Scope A node-level** (relay `SubagentSpawned`/`SubagentCompleted`); Scope B (child inner turn-stream nesting) + TEAMMATE/HANDOFF deferred.

---

## Day 0 — Plan-vs-Repo Verify + Branch

### 0.1 Three-prong Day-0 verify
- [x] **Prong 1 (path)**: confirmed (3 read-only探查 passes + 1 Explore agent map) — `make_chat_subagent_dispatcher` `_category_factories.py:197-227` (returns `DefaultSubagentDispatcher(chat_client, child_loop_factory)` — NO event_emitter) / `DefaultSubagentDispatcher.__init__` `dispatcher.py:104-134` (ALREADY has `event_emitter` param `:109`, stored `:134`) + `_emit_safely` `:136-143` + `SubagentEventEmitter` type `:90` / `spawn` emits SubagentSpawned `:189-196` + `_track_and_emit` emits SubagentCompleted `:224-249` / `SubagentSpawned` `events.py:348-353` (has `parent_session_id`) + `SubagentCompleted` `:355-359` / `serialize_loop_event` maps both `sse.py:306-326` / `build_real_llm_handler` `handler.py:242` + dispatcher build `:332-334` / `build_handler` dispatch + router call `router.py:222-239` / `StreamingResponse(_stream_loop_events(...))` `:314-329` / `_stream_loop_events` `:341-402` (`async for` `:384`, serialize `:393`, `format_sse_message` `:402`, NotImplementedError/None skip `:394-401`) / frontend `chatStore.ts:638-743` + `InspectorTree.tsx:176/178-197/73-95`. (progress.md Day-0 Prong 1)
- [x] **Prong 2 (content)**: confirmed — (a) the relay chain exists end-to-end; the ONLY unwired link is `make_chat_subagent_dispatcher` not passing `event_emitter`; (b) **NO `LoopEvent` contract change** for node-level — `SubagentSpawned` already carries `parent_session_id`, both events already serialized, frontend already consumes; (c) the emitter slot has existed since Sprint 57.12 (`dispatcher.py:131-134`), deliberately left unwired on chat; (d) the carryover's "needs `LoopEvent` parent_session_id/depth" is true ONLY for Scope B (child inner turn-stream), NOT node-level. (progress.md Day-0 Prong 2)
- [x] **Prong 2.5 (event / drift)**: confirmed — **D1**: subagent events fire during the parent's `task_spawn` tool-await → loop generator blocked → a router-owned buffer drained by `_stream_loop_events` is the bridge (not a direct loop yield). **D2**: `build_handler` (`router.py:222`) is the echo/real_llm dispatch → emitter threads through it → `build_real_llm_handler` (echo ignores). **D3**: the buffer must live in the router handler fn scope (shared between the emitter at build-time and the drain at stream-time). **D4 (drift vs 57.94 design note)**: 57.94 §5 + carryover said node visibility "needs a `LoopEvent` parent_session_id/depth field" — Day-0 corrects this: NODE-level needs ONLY the emitter wired (SubagentSpawned subclass already carries the field); the contract field is a Scope-B concern → recorded in progress.md (scope is SMALLER than the carryover implied; no contract change). (progress.md Day-0 Prong 2.5)
- [x] **Prong 3 (schema)**: N/A — no DB/migration/ORM change; no `LoopEvent` contract change (SubagentSpawned already has the fields); no new event type.
- [x] **Baseline capture**: baseline = `main` HEAD `8c6a2250` (57.94 merged; CI-green pytest 2271 / mypy 0/351 / run_all 10/10) — full local run after edits = 2277 (= 2271 + 6 new); NET delta +6, 0 deletions
- [x] **`_stream_loop_events` test harness locate**: found `_StubLoop` + `_consume` drain harness in `tests/integration/api/test_chat_sla_recording.py:36-61` (drives `_stream_loop_events(stub, tenant, session, registry, ...)` with deps=None) → mirrored for the buffer-drain test
- [x] Catalogue any Day-1 drift in progress.md; **go/no-go = GO** (feasibility CONFIRMED — one unwired link + a buffer-drain bridge; 0% contract change; D4 correction is a scope REDUCTION not a blocker)

### 0.2 Branch
- [x] Branch `feature/sprint-57-95-subagent-sse-relay` from `main` (`8c6a2250`)
- [x] plan + checklist + progress committed (Day-0 commit)

---

## Day 1 — `event_emitter` threading + buffer-drain bridge (US-1/US-2)

### 1.1 `event_emitter` threading (US-1)
- [x] **`_category_factories.py`** — `make_chat_subagent_dispatcher` gains `event_emitter: SubagentEventEmitter | None = None` (kw-only after `child_loop_factory`); passes to `DefaultSubagentDispatcher(chat_client=…, child_loop_factory=…, event_emitter=event_emitter)`; import `SubagentEventEmitter` (TYPE_CHECKING from `subagent.dispatcher`); file-header MHist
- [x] **`handler.py` `build_real_llm_handler`** — gains `subagent_event_emitter: "SubagentEventEmitter | None" = None`; threads into `make_chat_subagent_dispatcher(..., event_emitter=subagent_event_emitter)` (`:332-334`); MHist
- [x] **`handler.py` `build_handler`** — gains `subagent_event_emitter` passthrough to `build_real_llm_handler`; echo branch ignores (no subagent dispatcher)
- [x] **mypy clean** on the 2 files (full `src --strict` 0/351)

### 1.2 Router buffer + emitter closure (US-2)
- [x] **`router.py` chat handler fn** — create `subagent_event_buffer: list[LoopEvent] = []` before `build_handler`; define `async def _relay_subagent_event(ev: LoopEvent) -> None: subagent_event_buffer.append(ev)`
- [x] **Pass emitter** — `build_handler(..., subagent_event_emitter=_relay_subagent_event)`
- [x] **Pass buffer** — `_stream_loop_events(..., subagent_event_buffer=subagent_event_buffer)`; MHist 1-line + `LoopEvent` added to runtime import

### 1.3 `_stream_loop_events` buffer drain (US-2/US-4)
- [x] **`_drain_subagent_frames(buffer) -> list[bytes]` helper** — while non-empty: `pop(0)` → `serialize_loop_event` (mirror NotImplementedError skip + None skip `:394-401`) → `format_sse_message`; returns frames
- [x] **Add param** — `_stream_loop_events(..., subagent_event_buffer: "list[LoopEvent] | None" = None)`
- [x] **Drain per loop event** — at the TOP of the `async for` body (before serializing the current event): `for _frame in _drain_subagent_frames(subagent_event_buffer): yield _frame`
- [x] **Drain at end** — after the `async for` completes (before the `except`/finalize): drain once more (defensive)
- [x] **Guard** — empty/None buffer → `[]` → zero behavior change on the non-spawn path
- [x] **mypy clean** on `router.py`

---

## Day 2 — Tests (US-1..US-4)

### 2.1 Factory threading test (US-1)
- [x] **`make_chat_subagent_dispatcher(chat_client, event_emitter=sentinel)`** → the returned dispatcher's `_event_emitter is sentinel` (NEW `test_subagent_sse_relay.py`; + a default-None test)

### 2.2 Buffer-drain SSE-frame tests (US-2/US-4)
- [x] **buffer-drain emits frames** — drive `_stream_loop_events` with `_SpawningStubLoop` (appends Spawned+Completed to the buffer, yields LoopCompleted); assert the SSE bytes contain `subagent_spawned` + `subagent_completed` + the child summary, before `loop_end`, buffer drained empty
- [x] **no-regression (empty buffer)** — `_PlainStubLoop` + empty buffer → no `subagent_*` frames
- [x] **`_drain_subagent_frames` pure helper** — empty/None → `[]`; Spawned+Completed → 2 frames + buffer emptied
- [x] **harness** — mirrored `_StubLoop`/`_consume` from `test_chat_sla_recording.py`

### 2.3 Existing tests green (US-4)
- [x] **Sprint 57.12 dispatcher emission tests** (`test_subagent_sse_emission.py`, 8 tests) UNCHANGED + green
- [x] **Sprint 57.94 child-loop tests** (`test_subagent_child_loop.py` + `test_fork`/`test_as_tool`) UNCHANGED + green
- [x] **`loop.py` diff = 0** — `git diff main..HEAD -- backend/src/agent_harness/orchestrator_loop/loop.py` empty (confirmed)

---

## Day 3 — Full regression + drive-through (US-5) + CHANGE-062

### 3.1 Full gate sweep
- [x] **Full backend pytest green (NET delta documented)** — baseline 2271 → **2277 (+6)**, 4 skipped; NO test deleted
- [x] **mypy 0 + run_all 10/10 + format chain** — mypy `src --strict` 0/351; run_all **10/10** (LLM SDK leak 0; AP-1 — drain NOT flagged as pipeline; check_event_schema_sync green — no event schema drift; check_cross_category_import green); `black`/`isort` clean; `flake8 src tests` clean (CI-equivalent scope)

### 3.2 Drive-through (US-5 — the Tree shows the subagent node) — **PASS pending**
- [x] **Clean backend restart (Risk Class E)** — killed stale 57.94 reloader 14580 + spawn-worker 38308 (python, not node); verified :8000 FREE; `dev.py start backend` → fresh **PID 50200** owns :8000 (`/health` 401 = server up + tenant middleware); frontend node :3007 untouched; Azure gpt-5.2 live
- [x] **Drove a `task_spawn` subagent through real UI + real backend + real Azure** — jamie@acme.com/acme-prod/real_llm. BEFORE: Tree "no subagents spawned this session". `task_spawn(mode=fork)` → child `echo_tool` → AFTER: Tree node `1ff0167a…` · root · **completed** · Mode **fork** · Depth 0 · **Tokens 3,692** · "subagent node is visible". Observed-vs-intended table in progress.md Day 3.2
  - Evidence: `artifacts/sprint-57-95-tree-{1-before-empty,3-populated}.png` + `-after-snapshot.yml`
- [x] **Backend confirm** — Inspector Trace shows the relayed `subagent_spawned` (mode=fork parent=95b9f45f…) + `subagent_completed` (subagent node is visible · 3692 tokens) frames (dispatcher events, not the tool result → proof of the relay)

### 3.3 CHANGE-062 (NO design note — feature-continuation)
- [x] `claudedocs/4-changes/feature-changes/CHANGE-062-subagent-sse-relay-node-level.md` written
- [x] **`17-cross-category-interfaces.md`** — Cat 11 §: NEW `SubagentEventEmitter` composition row (chat path now wires it; ABC + type unchanged, pre-existing since 57.12)

---

## Day 4 — Closeout

### 4.1 Closeout
- [x] Full validation (parent re-verified): pytest **2277** (+6) / mypy 0/351 / run_all 10/10 / 57.12 + 57.94 tests unchanged / `loop.py` diff = 0 / **drive-through PASS** (screenshots + before/after observed-vs-intended)
- [x] progress.md (Day 0-3.2) + retrospective.md (Q1-Q7) — NO design-note 8-pt gate (feature-continuation, not a spike)
- [x] Calibration: `subagent-sse-relay-wiring` 0.55 (1st data point) + `agent_factor` 1.0 (parent-direct); recorded `calibration-log.md §3` + `sprint-workflow.md §Scope-class matrix` row; carryover (Scope B child turn-stream / span nesting / TEAMMATE/HANDOFF / failure policies) → next-phase-candidates.md
- [x] MEMORY.md pointer + `project_phase57_95_subagent_sse_relay.md` subfile + CLAUDE.md lean (Current Sprint row + Last Updated) + CHANGE-062 + 17.md row
- [ ] commit (Day 0-N) + push + PR — Day 0-2 commit `a06352b7` + closeout commit done; **push + PR pending user authorization**
