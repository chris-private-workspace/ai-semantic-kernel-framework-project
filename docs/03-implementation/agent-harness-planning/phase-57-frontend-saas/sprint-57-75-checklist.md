# Sprint 57.75 — Checklist (Inspector Trace + Memory tabs full-chain: emit SpanStarted/Ended + MemoryAccessed → wire/codegen → InspectorTrace + InspectorMemory)

**Plan**: `sprint-57-75-plan.md`
**Branch**: `feature/sprint-57-75-inspector-trace-memory` (from `main` `aaf0364c`)
**Closes**: `AD-ChatV2-Inspector-Trace-Phase2` + `AD-ChatV2-Inspector-Memory-Phase2`

---

## Day 0 — Plan-vs-Repo Verify + Branch + Decisions

### 0.1 Day-0 verify (5 researcher passes + parent grep/read, main `aaf0364c`)
- [x] **Prong 1 (path)** — all target files exist: `_contracts/events.py`, `orchestrator_loop/loop.py`, `prompt_builder/builder.py`, `api/v1/chat/{sse,event_wire_schema,handler,router}.py`, `frontend/src/features/chat_v2/{store/chatStore,components/inspector/{ChatInspector,InspectorTree}}`, `generated/{events.json,loopEvents.generated.ts}`, mockup `page-chat.jsx`.
- [x] **Prong 2 (content)** — D-DAY0-1..7 catalogued in plan §0 (A-1 cut-wire REFUTED via handler.py:258+292; event types exist field-short; Option C zero-blast emit; OTelTracer default; echo_demo honest-empty; codegen single-source; InspectorTree template).
- [x] **Prong 3 (schema)** — N/A (no DB table / migration / ORM change; emit reads in-memory artifact).
- [x] **Prong 2.5 (child-tree)** — N/A backend-heavy; frontend new components are leaf (no existing child tree to audit); ChatInspector swap only.
- [x] **go/no-go = GO** — Memory blocker refuted, Trace mechanism confirmed zero-blast; no >20% scope drift.

### 0.2 Branch + decisions
- [x] **Branch created** `feature/sprint-57-75-inspector-trace-memory`
  - Command: `git branch --show-current` → matches
- [x] **Decisions locked** (user AskUserQuestion): scope = Trace + Memory both (Memory un-blocked by D-DAY0-1); span granularity = all 6 span types emit; agent-delegated yes (Track A backend → Track B frontend + parent re-verify).
- [x] **Day-0 commit** plan + checklist + progress.md Day 0
  - Command: `git add docs/ && git commit`

---

## Day 1 — Backend Trace emit + wire/codegen (US-3 part + US-5 + US-6 part)

### 1.1 Event field extension + Trace emit (US-3)
- [x] **Extend SpanStarted/SpanEnded** in `_contracts/events.py`
  - SpanStarted +`parent_span_id: str = ""` +`span_type: str = ""`; SpanEnded +`span_type: str = ""`
  - DoD: frozen dataclass, defaults preserve existing ctors; mypy clean
- [x] **Emit SpanStarted/Ended at 6 loop sites** (`loop.py` 797/877/912/960/1021/1289)
  - Option C: at existing `as <ctx>`; `_t0=time.monotonic()` + yield SpanStarted on enter; yield SpanEnded (duration_ms) on exit
  - span_type: LOOP/COMPACTION/TURN/PROMPT_BUILD/LLM_CALL/TOOL_EXEC (from `attributes["span_type"]`)
  - multi-exit spans: `try/finally: yield SpanEnded` so it always fires
  - DoD: `helpers.category_span`/`tracer.py`/`_abc.py`/verification/business untouched (zero blast)

### 1.2 Serialize + wire + codegen (US-5)
- [x] **Add 2 serialize branches** (SpanStarted/SpanEnded) in `sse.py` `_serialize_inner`
  - Verify nested `{type, data:{...}}` envelope against an existing branch (57.67 flat-vs-nested lesson)
- [x] **Add 2 WIRE_SCHEMA entries** (`event_wire_schema.py`, 18→20) + regenerate codegen
  - Command: `python scripts/codegen/generate_event_schemas.py`
  - DoD: `frontend/.../generated/{events.json,loopEvents.generated.ts}` regenerated; KNOWN_LOOP_EVENT_TYPES updated

### 1.3 Backend Trace tests (US-6 part)
- [x] **Span emit order + nesting test**
  - ≥1 LOOP root; TURN.parent_span_id == LOOP.span_id; LLM_CALL/TOOL_EXEC.parent == TURN
  - tool-error turn + max-turns exit → SpanEnded still fires (R3)
  - Command: `pytest backend/tests/unit/agent_harness/orchestrator_loop/ -k span`
- [x] **Parent re-verify (Before-Commit item 7)** — read loop emit + serialize; re-run mypy + pytest (subset) + `run_all.py`

---

## Day 2 — Backend Memory emit (US-4 + US-5 + US-6 part)

### 2.1 Memory access metadata + emit (US-4)
- [x] **Extend MemoryAccessed** in `_contracts/events.py`
  - +`summary: str = ""` +`time_scale: str = ""` (keep layer/operation/key)
- [x] **Enrich build() metadata** in `prompt_builder/builder.py`
  - add `layer_metadata["memory_accesses"]` = list of `{scope, time_scale, key, summary}` from MemoryHints (`_contracts/memory.py:51-79`)
  - PII: summary is capped ≤2000-tok summary not raw; PIIRedactor if free-text risk
- [x] **Emit MemoryAccessed per-hint** in `loop.py:~966` (post-build, inside `prompt_builder is not None` branch, next to PromptBuilt)
  - `yield MemoryAccessed(layer=scope, operation="read", key=key, summary=summary, time_scale=time_scale, trace_context=turn_ctx)`
  - echo_demo path: no emit (honest empty, D-DAY0-5)

### 2.2 Serialize + wire (US-5)
- [x] **Add 1 serialize branch** (MemoryAccessed) in `sse.py` + **1 WIRE_SCHEMA entry** (20→21) + regen codegen
  - Command: `python scripts/codegen/generate_event_schemas.py`

### 2.3 Backend Memory tests + parity (US-6)
- [x] **MemoryAccessed emit test** (real_llm path emits ≥1; echo_demo emits 0)
- [x] **Parity test** `test_event_wire_schema_parity.py` for 3 new types (18→21)
  - Command: `pytest backend/tests/unit/api/v1/chat/test_event_wire_schema_parity.py`
- [x] **Parent re-verify** — mypy 0; pytest green; `run_all.py` 10/10 (incl. check_event_schema_sync + check_llm_sdk_leak)

---

## Day 3 — Frontend 2 tabs (US-1/US-2/US-7 part)

### 3.1 Store slices + mergeEvent (US-1/US-2 plumbing)
- [x] **chatStore.ts** — 2 derived slices `spans: SpanNode[]` + `memoryOps: MemoryOp[]` in ChatStoreState + `_initial()`
- [x] **3 mergeEvent cases** — span_started (open) / span_ended (close+duration) / memory_accessed (push op); mirror `subagents` slice
  - DoD: exhaustive switch stays complete; rawEvents still pushed

### 3.2 InspectorTrace (US-1)
- [x] **InspectorTrace.tsx** (NEW) — consume `s.spans`; waterfall by parent_span_id (indent + tree-glyph); colored duration bar by span_type (var(--*) tokens); right `{d}s`; empty-state
  - Mockup L434-466 verbatim CSS classes; no shadcn residue; no new oklch/hex literal

### 3.3 InspectorMemory (US-2)
- [x] **InspectorMemory.tsx** (NEW) — consume `s.memoryOps`; ops list (`<Badge tone="memory">{op}</Badge>` + scope + `.subtle` timestamp + `{key} = {summary}`); empty-state
  - Mockup L468-487 verbatim CSS classes

### 3.4 ChatInspector swap + Vitest (US-1/US-2)
- [x] **ChatInspector.tsx** — swap 2 `ComingSoonInspectorTab` (:98-113) → `<InspectorTrace/>` / `<InspectorMemory/>` (Turn/Tree untouched)
- [x] **Vitest** — `{InspectorTrace,InspectorMemory}.test.tsx` (NEW: waterfall nesting / ops render / empty-state) + chatStore.test (new slices)
  - Command: `npm run test -- chat_v2`

---

## Day 4 — e2e + Mockup-fidelity sweep + Closeout

### 4.1 e2e + mockup-fidelity (US-7)
- [x] **e2e** — `*chat*inspector*.spec.ts` (NEW or extend): SSE mock with span/memory events → Trace waterfall + Memory ops render; echo_demo → Memory empty
- [x] **Mockup-fidelity DoD**
  - Command: `diff reference/design-mockups/styles.css frontend/src/styles-mockup.css` → empty
  - Command: `npm run check:mockup-fidelity` → byte-identical + HEX_OKLCH_BASELINE unchanged
  - shadcn-residue grep = 0 in new components
- [x] **Full sweep (parent re-verify, Before-Commit item 7)**
  - Backend: `mypy src/` 0 + `pytest` + `python scripts/lint/run_all.py` 10/10
  - Frontend: `npm run lint` (NO `--silent`) 0 + `npm run build` tsc 0 + Vitest green
  - Read all agent-changed code (real data / no fabrication / English copy / mockup-native)

### 4.2 Closeout docs
- [x] **CHANGE-043** in `claudedocs/4-changes/feature-changes/`
- [x] **progress.md** Day 0-4 + **retrospective.md** Q1-Q7
- [x] **Checklist** all `[x]` (no deletion of unchecked)
- [x] **Calibration** record (mixed-multidomain-bundle 0.65 + agent_factor 0.45; CAVEAT 12+ consecutive)
- [x] **AD closure**: `AD-ChatV2-Inspector-Trace-Phase2` + `-Memory-Phase2` → CLOSED; new carryovers (subagent-boundary spans / memory write-evict emit) → next-phase-candidates.md
- [x] **MEMORY subfile + pointer** + **CLAUDE.md lean** (Current Sprint + Last Updated only)
- [x] **No design note** (feature-continuation: extends A-5 chain 57.66/67/72 + existing event types)

### 4.3 Ship
- [x] **Commit mapping** Day-0 / Track A backend / Track B frontend / closeout
- [ ] **Push + PR** (user-gated — explicit authorization required)
