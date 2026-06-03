# CHANGE-043: chat-v2 Inspector Trace + Memory tabs — full-chain SSE emit → consumer

**Change Date**: 2026-06-03
**Change Type**: New Feature (backend SSE emit chain + frontend 2-tab consumer)
**Sprint**: 57.75
**Scope**: Cat 12 (Observability span lifecycle) + Cat 3 (Memory access) emit + Cat 1 (loop) + api/v1/chat (serialize/wire/codegen) + Frontend chat_v2 Inspector
**Status**: ✅ Completed (push/PR user-gated)

## Change Summary
Closes the carryovers `AD-ChatV2-Inspector-Trace-Phase2` + `AD-ChatV2-Inspector-Memory-Phase2` (Area-A program items #1+#2). Fills the last 2 unfilled chat-v2 Inspector tabs by emitting `SpanStarted`/`SpanEnded` (6 span types) + `MemoryAccessed` (per-hint) as SSE LoopEvents, wiring them through the A-5 codegen chain (57.66/67/72), and building `InspectorTrace` (span waterfall) + `InspectorMemory` (memory ops list) per mockup `page-chat.jsx` L434-487.

## Change Reason
Sprint 57.72 (A-5c) wired the Tree tab but left Trace + Memory as `ComingSoonInspectorTab`. The two carryover ADs assumed both tabs were blocked. Day-0 verification **refuted the Memory blocker**: the stale `cat3-memory-loop-injection-analysis-20260531.md` claimed production passes no PromptBuilder, but `handler.py:258+292` inject it (Sprint 57.64-65 A-1 fix) → memory IS touched on the real_llm path. The Trace emit mechanism is zero-blast-radius (loop.py already captures `TraceContext` via `as <ctx>`).

## Detailed Changes
**Backend** (emit chain):
- `_contracts/events.py` — `SpanStarted` +`parent_span_id`+`span_type`; `SpanEnded` +`span_type`; `MemoryAccessed` +`summary`+`time_scale` (all additive, frozen-dataclass defaults preserve existing ctors).
- `orchestrator_loop/loop.py` — emit `SpanStarted`/`SpanEnded` at all 6 span sites (Option C: at existing `as <ctx>`; `try/finally: yield SpanEnded` so every exit closes the span). LOOP `SpanStarted` ordered after `LoopStarted`; LOOP `SpanEnded` trails `LoopCompleted` (span wraps whole loop).
- `prompt_builder/builder.py` — `build()` returns `layer_metadata["memory_accesses"]` (per-hint `{scope, time_scale, key=full_content_pointer, summary}`) from the already-retrieved `memory_layers` (no extra `MemoryRetrieval.search()`).
- `loop.py` — emit one `MemoryAccessed(operation="read")` per hint after `PromptBuilt` (real_llm path; echo_demo has no prompt_builder → 0 events → honest-empty Memory tab).
- `api/v1/chat/sse.py` — +3 `_serialize_inner` branches (nested `{type, data:{...}}` envelope).
- `api/v1/chat/event_wire_schema.py` — `WIRE_SCHEMA` 19→22.
- `scripts/codegen/generate_event_schemas.py` — +3 interface mappings; regenerated `frontend/.../generated/{events.json, loopEvents.generated.ts}`.

**Frontend** (consumer):
- `chat_v2/store/chatStore.ts` — +`SpanNode`/`MemoryOp` types + `spans`/`memoryOps` slices (state + `_initial()` + `applyPivot` reset) + 3 `mergeEvent` cases (span_started open / span_ended close+duration / memory_accessed push; span dedup + orphan span_ended guard; `at=Date.now()` honest client time).
- `chat_v2/components/inspector/InspectorTrace.tsx` (NEW) — span waterfall: `orderSpans()` parent-before-child by `parentSpanId` (cycle-guard + MAX_DEPTH=8) + tree-glyph + indent; `SPAN_COLOR` map (var(--*) tokens); duration bar (width=ms/max); running span = subtle bar + em-dash (no fabricated duration).
- `chat_v2/components/inspector/InspectorMemory.tsx` (NEW) — ops list: verbatim `<span className="badge memory">` + scope·timeScale (雙軸) + client-time ts + `{key} = {summary}`; honest empty-state.
- `chat_v2/components/inspector/ChatInspector.tsx` — swap 2 `ComingSoonInspectorTab` → `<InspectorTrace/>`/`<InspectorMemory/>` (all 4 tabs now real).
- **Removed** `chat_v2/components/inspector/ComingSoonInspectorTab.tsx` — orphan after swap (no remaining consumer; only a Sprint 57.30 one-shot verify-script comment mentions the name). AP-2 cleanup + Karpathy §3 (change-produced orphan). NOT in plan §4 originally — recorded as Day-3 decision.

## Modified Files List
- Backend: `_contracts/events.py`, `orchestrator_loop/loop.py`, `prompt_builder/builder.py`, `api/v1/chat/{sse,event_wire_schema}.py`, `scripts/codegen/generate_event_schemas.py`, `frontend/.../generated/{events.json,loopEvents.generated.ts}`
- Backend tests: `test_observability_coverage.py` (+3 span emit), `test_loop_with_prompt_builder.py` (+2 memory emit), `test_event_wire_schema_parity.py` (19→22), 5 existing sequence tests (filter diagnostic events via `_public()`)
- Frontend: `chat_v2/store/chatStore.ts`, `components/inspector/{InspectorTrace,InspectorMemory}.tsx` (NEW), `ChatInspector.tsx`, `-ComingSoonInspectorTab.tsx` (deleted)
- Frontend tests: `{InspectorTrace,InspectorMemory}.test.tsx` (NEW), `chatStore.mergeEvent.test.ts` (+13), `ChatInspector.test.tsx` (2 ComingSoon→empty), `eventSchema.generated.test.ts` (19→22), `e2e/chat/chat-v2-inspector-trace-memory.spec.ts` (NEW)

## Verification (parent-run, Before-Commit item 7)
- Backend: `mypy src/` 0/329; `pytest` 2089 passed, 4 skipped, 0 failed; `scripts/lint/run_all.py` 10/10 (incl. check_event_schema_sync + check_llm_sdk_leak + check_ap4_frontend_placeholder); black 607 / isort / flake8 clean.
- Frontend: `npm run lint` exit 0 (no `--silent`); `npm run build` tsc 0; `check:mockup-fidelity` byte-identical + baseline 50 unchanged; Vitest 738 passed (131 files, +30 net).
- e2e: `chat-v2-inspector-trace-memory.spec.ts` written (SSE mock → Trace waterfall + Memory ops; echo_demo → empty); not run locally (frontend dev server :3007 is the live Claude Code node process — not touched); CI Frontend-E2E gate covers it.
- Parent read all agent-changed code: emit additive + envelope consistent; 5 existing tests filter-only (none weakened/deleted); 2 new components verbatim mockup CSS + English copy + honest running/empty (AP-4); 2 new tests rigorous (nesting/running/empty/雙軸/verbatim-class).

## Impact
Backend + frontend; chat-v2 Inspector only. No DB migration, no CSS change, no new dependency. Removed 1 orphan component. Memory tab is live-session SSE (NOT persisted ops-history — that remains `AD-Memory-OpsHistory-Backend`). echo_demo sessions show honest-empty Memory (conditional, not Potemkin). New carryovers: subagent-boundary spans (cross-process parent_span_id) + memory write/evict emit.
