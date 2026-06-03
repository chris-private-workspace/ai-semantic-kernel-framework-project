# Sprint 57.75 Plan — Inspector Trace + Memory tabs full-chain (emit SpanStarted/Ended + MemoryAccessed → wire/codegen → InspectorTrace + InspectorMemory) (closes AD-ChatV2-Inspector-Trace-Phase2 + AD-ChatV2-Inspector-Memory-Phase2)

**Phase**: 57 (Frontend + SaaS Stage 1 ongoing)
**Scope class**: `mixed-multidomain-bundle` (backend event-emit chain + frontend 2-tab consumer)
**Branch**: `feature/sprint-57-75-inspector-trace-memory` (from `main` `aaf0364c`)
**Status**: Day 0 (plan)

---

## 0. Background

chat-v2 Inspector has 4 tabs (Turn / Trace / Memory / Tree). Sprint 57.72 (A-5c) wired **Tree** to real data (`InspectorTree` consuming `subagent_spawned/completed`); Turn was wired earlier (`InspectorTurn`). **Trace + Memory remain `ComingSoonInspectorTab`** (`ChatInspector.tsx:98-113`) — the last 2 unfilled Inspector tabs. This sprint fills both via the A-5 full-chain pattern (emit SSE event → serialize → wire-schema + codegen → frontend consumer), the same chain A-5a (57.66) + A-5b (57.67) + A-5c-Tree (57.72) established.

This is the "process all carryover except A-4 Tier 2" program item #1+#2.

### Day-0 ground-truth (5 researcher passes + parent direct grep/read, main `aaf0364c`)

The original `AD-ChatV2-Inspector-*-Phase2` carryovers assumed both tabs were blocked. Day-0 verification **refuted the Memory blocker** and **confirmed the Trace emit mechanism is zero-blast-radius**:

- **D-DAY0-1 (refutes stale analysis — Memory NOT a Potemkin)**: `cat3-memory-loop-injection-analysis-20260531.md` claimed production chat path passes no PromptBuilder (memory auto-inject = cut wire). **This is stale.** `handler.py:258` `make_chat_prompt_builder(chat_client, memory_retrieval=memory_retrieval)` + `handler.py:292` `prompt_builder=prompt_builder` inject it into `AgentLoopImpl`; MHist confirms **Sprint 57.64 Day 1 "inject Cat 5 prompt_builder (keystone)" + 57.65 "share executor's MemoryRetrieval into prompt builder (A-1)"**. Router `build_handler(req.mode,...)` (router.py:217) → `mode=="real_llm"` → `build_real_llm_handler` (the production real-LLM path) which injects. So `loop.py:928` `if self._prompt_builder is not None` true-branch runs → `build()` runs `_inject_memory_layers` → memory IS touched at runtime. `MemoryAccessed` will carry real data on the real_llm path.
- **D-DAY0-2 (event types exist, fields insufficient)**: `SpanStarted`/`SpanEnded` (events.py:378-389) + `MemoryAccessed` (events.py:200-203) **already exist** but are never emitted + never serialized. `SpanStarted` lacks `parent_span_id`+`span_type` (waterfall indent + color); `MemoryAccessed` lacks `summary`(mockup `v`)+`time_scale`(雙軸). → extend fields, not create types.
- **D-DAY0-3 (Trace emit mechanism = ZERO blast radius — Option C)**: loop.py's 6 span points already use `self._tracer.start_span(...) as <ctx>` directly (NOT `category_span`): LOOP `as root_ctx` (797), COMPACTION (877), TURN `as turn_ctx` (912), PROMPT_BUILD (960), LLM_CALL (1021), TOOL_EXEC (1289). Nesting is explicit via `trace_context=` kwarg (ctx→root_ctx→turn_ctx→leaf). Both `OTelTracer` and `NoOpTracer` `.start_span` yield a populated `TraceContext` (real `span_id`+`parent_span_id`, observability.py:60-65). → emit `SpanStarted`/`SpanEnded` at the existing `as <ctx>` sites reading `.span_id`/`.parent_span_id`. Only `loop.py` + `events.py` change; `helpers.category_span`, `tracer.py`, `_abc.py`, verification/business callers untouched.
- **D-DAY0-4 (Trace主流量有效)**: `get_tracer` (platform_layer/observability/tracer.py:54-65) defaults to `OTelTracer` singleton, no env-gating; router.py:145 `Depends(get_tracer)` → :233 injected. Production POST /chat runs OTelTracer. SSE span events are loop-yielded (independent of OTel export) but share the same TraceContext ids → consistent.
- **D-DAY0-5 (echo_demo honest empty)**: `mode=="echo_demo"` → `build_echo_demo_handler` does NOT inject prompt_builder → memory not touched → Memory tab shows honest empty state for demo sessions (correct conditional behavior, not a Potemkin). Trace tab still works on echo_demo (spans always open).
- **D-DAY0-6 (codegen single-source)**: `event_wire_schema.py` `WIRE_SCHEMA` (18 entries) is the codegen source; `scripts/codegen/generate_event_schemas.py` emits `frontend/src/features/chat_v2/generated/{events.json,loopEvents.generated.ts}`; parity test `test_event_wire_schema_parity.py` + lint `check_event_schema_sync.py` (run_all 10/10) gate drift. Adding 3 wire entries (18→21) auto-propagates TS types.
- **D-DAY0-7 (frontend consumer template)**: `InspectorTree.tsx` (57.72) is the consumer template — `useChatStore((s)=>s.subagents)` derived slice → `buildTree()` flat→forest → recursive render. `chatStore.ts` `mergeEvent` (:245) exhaustive switch + `rawEvents` (:247) + derived slices. Trace/Memory each need: a `mergeEvent` case + a derived slice (`spans`/`memoryOps`) + a new component + ChatInspector swap.
- **Mockup spec**: `reference/design-mockups/page-chat.jsx` Trace `InspectorTrace` (L434-466) = span waterfall (`{name,d,c,off}` rows, indent tree-glyphs `├─/└─`, colored duration bar, right `{d}s`); Memory `InspectorMemory` (L468-487) = ops list (`{op,scope,k,v,at}` rows, `<Badge tone="memory">` READ/WRITE + scope + right `.subtle` timestamp + `{k} = {v}` line).

---

## 1. Sprint Goal

Fill the last 2 chat-v2 Inspector tabs (Trace + Memory) with **real runtime data** by emitting `SpanStarted`/`SpanEnded` (all 6 span granularities) + `MemoryAccessed` (per-hint) as SSE LoopEvents, wiring them through the codegen chain, and building `InspectorTrace` (span waterfall) + `InspectorMemory` (memory ops list) per mockup `page-chat.jsx` L434-487 — no fabrication, honest empty state on echo_demo.

---

## 2. User Stories

- **US-1** (Trace UI): As a platform operator, I want the Trace tab to show the loop's span waterfall (LOOP→TURN→{LLM_CALL, TOOL_EXEC, PROMPT_BUILD, COMPACTION} with indent + duration bars), so I can see the execution structure + timing of a single chat turn-set.
- **US-2** (Memory UI): As a platform operator, I want the Memory tab to show this session's memory accesses (scope / time_scale / op / key / summary), so I can see which memories the agent retrieved.
- **US-3** (Trace emit): As the platform, the loop emits `SpanStarted`/`SpanEnded` at all 6 span sites with `span_id`+`parent_span_id`+`span_type`+`duration_ms` (Option C — at existing `as <ctx>` sites; zero blast radius).
- **US-4** (Memory emit): As the platform, the loop emits `MemoryAccessed` per retrieved hint after `build()` (real_llm path), carrying `layer`(scope)/`operation`/`key`/`summary`/`time_scale`.
- **US-5** (wire+codegen): Event wire schema gains 3 entries (18→21) + regenerated TS types; parity test + lint stay green.
- **US-6** (backend tests): Emit order + nesting (parent_span_id linkage) + serialize parity + per-hint memory emit are unit-tested.
- **US-7** (mockup-fidelity DoD): Trace waterfall (L434-466) + Memory ops list (L468-487) match mockup verbatim CSS; `check:mockup-fidelity` byte-identical; no shadcn residue.

---

## 3. Technical Specifications

### 3.0 Architecture

Full-chain vertical slice mirroring A-5 (57.66/67/72). Two independent backend producers (Trace span lifecycle + Memory access) feed two independent frontend consumers via the shared wire/codegen registry. The Trace producer is loop-only (Option C); the Memory producer needs a small `build()` metadata enrichment to surface per-hint detail. **No DB migration. No new dependency.** LLM-neutral (pure loop/event code; no provider import).

### 3.1 Event field extension (US-3/US-4) — `_contracts/events.py`

- `SpanStarted` (378-382): add `parent_span_id: str = ""` + `span_type: str = ""` (keep `span_name`/`span_id`). Frozen dataclass, defaults preserve existing constructors.
- `SpanEnded` (384-389): add `span_type: str = ""` (keep `span_name`/`span_id`/`duration_ms`).
- `MemoryAccessed` (200-203): add `summary: str = ""` + `time_scale: str = ""` (keep `layer`/`operation`/`key`).
- All additive with defaults → no existing test breaks.

### 3.2 Trace emit (US-3) — `orchestrator_loop/loop.py`

- At each of the 6 existing `async with self._tracer.start_span(...) as <ctx>:` sites (797/877/912/960/1021/1289):
  - On enter: record `_t0 = time.monotonic()`; `yield SpanStarted(span_name=<name>, span_id=ctx.span_id, parent_span_id=ctx.parent_span_id or "", span_type=<TYPE>, trace_context=ctx)`.
  - On exit (block end / all termination paths): `yield SpanEnded(span_name=<name>, span_id=ctx.span_id, span_type=<TYPE>, duration_ms=(time.monotonic()-_t0)*1000.0, trace_context=ctx)`.
- `span_type` values: `LOOP` / `TURN` / `LLM_CALL` / `TOOL_EXEC` / `PROMPT_BUILD` / `COMPACTION` (read from the existing `attributes["span_type"]`).
- **Multi-exit guard**: TURN/LLM_CALL spans may `break`/`continue`/raise. Use `try: ... finally: yield SpanEnded(...)` where a span has multiple exit paths so SpanEnded always fires (async-generator `finally` with yield is valid here — the generator is consumed to completion by the SSE driver). Document the chosen pattern per span in the implementation.
- duration is loop-measured (`time.monotonic()`), independent of OTel's internal span timing — the SSE waterfall is a diagnostic view, not the OTel trace.

### 3.3 Memory emit (US-4) — `loop.py` + `prompt_builder/builder.py`

- `builder.py`: `build()` currently surfaces `layer_metadata["memory_layers_used"]` (:294). Enrich to also return per-hint access detail — a list of `{scope, time_scale, key, summary}` from the `MemoryHint`s returned by `MemoryRetrieval.search()` (hints carry `layer`/`time_scale`/`summary`, `_contracts/memory.py:51-79`). Keep the existing field; add a new `layer_metadata["memory_accesses"]` list. PII: emit `summary` (already a capped ≤2000-token summary, not raw content); apply `PIIRedactor` if free-text risk.
- `loop.py:~966` (after `artifact = await self._prompt_builder.build(...)`, inside the `prompt_builder is not None` branch, next to where `PromptBuilt` is yielded): for each entry in `artifact.layer_metadata["memory_accesses"]`, `yield MemoryAccessed(layer=scope, operation="read", key=key, summary=summary, time_scale=time_scale, trace_context=turn_ctx)`.
- echo_demo path (no prompt_builder) emits nothing → honest empty Memory tab (D-DAY0-5).

### 3.4 Serialize + wire + codegen (US-5) — `api/v1/chat/sse.py` + `event_wire_schema.py`

- `sse.py` `_serialize_inner` (:122): add 3 `isinstance` branches (SpanStarted/SpanEnded/MemoryAccessed) returning the wire dict (flat→nested envelope per 57.67 lesson: `{type, data:{...}}` — verify the envelope shape against the existing branches, NOT assumed flat).
- `event_wire_schema.py` `WIRE_SCHEMA`: add 3 entries (18→21) with field lists matching the extended dataclasses.
- Re-run `python scripts/codegen/generate_event_schemas.py` → regenerates `frontend/src/features/chat_v2/generated/{events.json,loopEvents.generated.ts}` + `KNOWN_LOOP_EVENT_TYPES`.
- Parity test `test_event_wire_schema_parity.py` + lint `check_event_schema_sync.py` must stay green (run_all 10/10).

### 3.5 Frontend consumers (US-1/US-2/US-7) — `chat_v2/`

- `store/chatStore.ts`: add 2 derived slices to `ChatStoreState` + `_initial()` (`spans: SpanNode[]`, `memoryOps: MemoryOp[]`); add 3 `mergeEvent` switch cases (span_started → push/open span; span_ended → close span set duration; memory_accessed → push memoryOp). Mirror the `subagents` slice pattern.
- `components/inspector/InspectorTrace.tsx` (NEW): consume `useChatStore((s)=>s.spans)`; build waterfall by `parent_span_id` (indent depth + tree-glyphs); per-row colored duration bar by `span_type` (map to mockup color tokens var(--primary/--tool/--info/--memory/--success/--warning)); right-aligned `{d}s`; empty-state. Mockup L434-466 verbatim CSS classes.
- `components/inspector/InspectorMemory.tsx` (NEW): consume `useChatStore((s)=>s.memoryOps)`; ops list rows = `<Badge tone="memory">{op}</Badge>` + scope + right `.subtle` timestamp + `{key} = {summary}` line; empty-state. Mockup L468-487 verbatim.
- `components/inspector/ChatInspector.tsx`: swap the 2 `ComingSoonInspectorTab` (`:98-113`) → `<InspectorTrace/>` / `<InspectorMemory/>` (Turn/Tree untouched).

### 3.6 Mockup-fidelity DoD (US-7) — `frontend-mockup-fidelity.md`

- `diff reference/design-mockups/styles.css frontend/src/styles-mockup.css` → empty (no CSS change expected; both tabs reuse existing classes).
- `check:mockup-fidelity` byte-identical + `HEX_OKLCH_BASELINE` unchanged (no new oklch/hex literals — consume var(--*) tokens only).
- No shadcn residue grep in new components; inline `style=` only with STYLE.md §3 escape comment if unavoidable.

### 3.7 Lint / validation

- Backend: `mypy src/` 0 errors; `pytest` (new emit + serialize tests + regression); `scripts/lint/run_all.py` 10/10 (incl. `check_event_schema_sync` + `check_llm_sdk_leak`).
- Frontend: `npm run lint` (NO `--silent`) exit 0; `npm run build` tsc 0; `check:mockup-fidelity` byte-identical; Vitest (new + regression).

---

## 4. File Change List

**Backend** (~6 files):
- `backend/src/agent_harness/_contracts/events.py` — extend SpanStarted/SpanEnded/MemoryAccessed fields (Cat 12 + Cat 3).
- `backend/src/agent_harness/orchestrator_loop/loop.py` — emit SpanStarted/Ended (6 sites) + MemoryAccessed (post-build) (Cat 1).
- `backend/src/agent_harness/prompt_builder/builder.py` — enrich `layer_metadata["memory_accesses"]` (Cat 5).
- `backend/src/api/v1/chat/sse.py` — +3 serialize branches (Cat 12 / API).
- `backend/src/api/v1/chat/event_wire_schema.py` — +3 WIRE_SCHEMA entries (18→21) (build-tooling).
- `frontend/src/features/chat_v2/generated/{events.json,loopEvents.generated.ts}` — codegen output (DO NOT hand-edit).

**Backend tests** (~2 files):
- `backend/tests/unit/agent_harness/orchestrator_loop/test_*` (NEW or extend) — span emit order + nesting + memory emit.
- `backend/tests/unit/api/v1/chat/test_event_wire_schema_parity.py` — parity for 3 new types.

**Frontend** (~5 files):
- `frontend/src/features/chat_v2/store/chatStore.ts` — +2 slices, +3 mergeEvent cases.
- `frontend/src/features/chat_v2/components/inspector/InspectorTrace.tsx` (NEW).
- `frontend/src/features/chat_v2/components/inspector/InspectorMemory.tsx` (NEW).
- `frontend/src/features/chat_v2/components/inspector/ChatInspector.tsx` — swap 2 tabs.
- `frontend/src/features/chat_v2/components/inspector/ComingSoonInspectorTab.tsx` — **DELETED** (Day-3 decision, not in original plan): orphaned by the 2-tab swap (no remaining consumer; only a Sprint 57.30 one-shot verify-script comment mentions the name). AP-2 + Karpathy §3 (change-produced orphan). User-gated at PR review (deleting production code per CLAUDE.md).

**Frontend tests** (~3 files):
- `frontend/tests/unit/chat_v2/{InspectorTrace,InspectorMemory}.test.tsx` (NEW).
- `frontend/tests/unit/chat_v2/chatStore.test.ts` (extend — new slices).
- `frontend/tests/e2e/*chat*inspector*.spec.ts` (NEW or extend — Trace/Memory tab render).

**No DB migration. No CSS change. No new dependency.**

---

## 5. Acceptance Criteria

- AC-1: Real_llm chat session → Trace tab renders a span waterfall with ≥1 LOOP root + ≥1 TURN + nested LLM_CALL/TOOL_EXEC/PROMPT_BUILD, correctly indented by parent_span_id, each with a duration bar.
- AC-2: Real_llm chat session that touches memory → Memory tab lists ≥1 memory access with scope + time_scale + op + key + summary; echo_demo session → honest empty state (no fabrication).
- AC-3: Backend emits SpanStarted/SpanEnded (6 span types) + MemoryAccessed; serialize branches produce valid wire dicts; parity test + `check_event_schema_sync` green (18→21).
- AC-4: `check:mockup-fidelity` byte-identical + baseline unchanged; new components use verbatim mockup CSS classes (no shadcn residue, no new oklch/hex literal).
- AC-5: Backend mypy 0; pytest green (new + regression); run_all 10/10. Frontend lint 0 (no `--silent`); build tsc 0; Vitest green.
- AC-6: AP-4 (no Potemkin) — emitted events carry real loop/memory data; AP-2 (no orphan) — Trace/Memory tabs consume the events they declare. LLM-neutrality green.

---

## 6. Deliverables

- [ ] Extended event dataclasses (SpanStarted/SpanEnded/MemoryAccessed)
- [ ] loop.py span lifecycle emit (6 sites, Option C)
- [ ] loop.py + builder.py memory access emit (per-hint)
- [ ] sse.py 3 serialize branches + WIRE_SCHEMA 18→21 + codegen regen
- [ ] backend tests (emit order/nesting/serialize parity/memory emit)
- [ ] chatStore 2 slices + 3 mergeEvent cases
- [ ] InspectorTrace.tsx (waterfall)
- [ ] InspectorMemory.tsx (ops list)
- [ ] ChatInspector 2-tab swap
- [ ] frontend tests (2 component + store + e2e)
- [ ] mockup-fidelity DoD pass
- [ ] CHANGE-043 + progress.md + retrospective.md + closeout

---

## 7. Workload Calibration

Bottom-up est: backend Trace ~4 hr + backend Memory ~3 hr + frontend 2-tab ~4 hr + e2e/mockup/closeout ~2 hr = **~13 hr**.
→ class-calibrated commit (`mixed-multidomain-bundle` ×0.65) ~**8.5 hr**
→ agent-adjusted commit (agent_factor `mixed-multidomain-bundle-mechanical` ×0.45) ~**3.8 hr**.

**Agent-delegated: yes** — Track A backend (events + loop emit + serialize + wire + codegen + tests), Track B frontend (store slices + 2 components + ChatInspector + tests), sequential (backend response contract → frontend), each via code-implementer + parent re-verify (Before-Commit item 7). Note: 12+ consecutive agent-delegated sprints with no clean wall-clock → ratio will be CAVEATED per `AD-Calibration-AgentDelegated-WallClock-Measure`. `mixed-multidomain-bundle-mechanical` 0.45 has a design component (field extension + waterfall tree-build) that is not pure pattern-reuse; if actual >> 0.45 band, note for sub-class refinement.

---

## 8. Dependencies & Risks

- **R1 (Risk Class C — test isolation)**: emit tests use the loop's async-generator drive; module-level singletons (tracer / service_factory) across event loops → use the autouse reset fixtures (`.claude/rules/testing.md §Module-level Singleton Reset Pattern`). New DB-touching path? No — emit reads in-memory artifact, no new DB call.
- **R2 (codegen flat-vs-nested envelope — 57.67 lesson)**: the wire dict envelope is nested `{type, data:{...}}`, NOT flat. Verify the 3 new serialize branches against an existing branch's shape BEFORE drafting the TS consumer; the parity test enforces it.
- **R3 (async-generator `finally` + yield for SpanEnded)**: multi-exit spans (TURN break/continue, exception paths) must still emit SpanEnded. `try/finally: yield` in an async generator is valid but requires the consumer drives to completion (the SSE driver does). Risk: an early `return` inside the generator skips `finally`-after-yield only if the generator is GC'd un-driven — not the case here. Test a tool-error turn + a max-turns exit to confirm SpanEnded fires.
- **R4 (Memory emit depends on prompt_builder injection)**: confirmed live on real_llm path (D-DAY0-1); echo_demo emits nothing by design (D-DAY0-5). NOT a Potemkin — but the Memory tab MUST show an honest empty state on echo_demo, not a fabricated row.
- **R5 (SSE traffic volume)**: 6 span types × 2 (start/end) × N turns → more SSE frames. Acceptable for a diagnostic stream; no throttle this sprint (note if a future perf concern).
- **R6 (multi-tenant / PII)**: SSE stream is session/tenant-scoped (`Depends(get_current_tenant)`, router.py:138). Span payload carries only name/id/duration/type (no content). Memory emits `summary` (capped, not raw) — apply PIIRedactor if free-text risk. No cross-tenant leak at transport.

---

## 9. Out of Scope (this sprint; carryover)

- **A-4 Tier 2** (Jaeger export / Area-C DevOps) — explicitly excluded per user program ("process all carryover except A-4 Tier 2").
- **SpanStarted/Ended over subagent boundaries** (cross-process parent_span_id) — single-loop only this sprint.
- **Memory write/evict ops emit** — read-on-build only this sprint (write/evict happen inside tools, already under TOOL_EXEC span); a future sprint may emit write/evict if the Memory tab needs them.
- **A-6 FE `/subagents` real list** (`AD-Subagent-RealList-Phase58`) — separate program item.
- **memory ops-history backend** (`AD-Memory-OpsHistory-Backend`) — the Memory tab here is live-session SSE, NOT persisted ops-history; the persisted view is a separate backend line.
