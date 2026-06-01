# Sprint 57.66 — Checklist (Serialize Already-Yielded Diagnostic Events to Client SSE — A-5a+)

**Plan**: [`sprint-57-66-plan.md`](./sprint-57-66-plan.md)
**Created**: 2026-06-01
**Status**: Draft (code gated on Day-0 GO)

> Rule: only `[ ]` → `[x]`; never delete unchecked items; defer with `🚧 + reason`.
> Day-0 prongs below were largely PRE-VERIFIED by the post-57.64/57.65 reality audit (D1-D5 in plan §0); re-confirm the residual unknowns (exact field sets + doc location) at sprint start before Day 1 code.

---

## Day 0 — Plan-vs-Repo Verify + Branch

### 0.1 Three-prong Day-0 verify (per `.claude/rules/sprint-workflow.md §Step 2.5`)
- [x] **Prong 1 (path)**: confirmed `sse.py` (serializer + `NotImplementedError` `:298` + `llm_response` `:140-156` + `loop_end` `:197-204` + frame `:304-307` + trace_id inject `:108-109` + import block `:69-87`) / `_contracts/events.py` single-source / FE `chat_v2/types.ts` KNOWN set `:177-192` + union `:161-175` / `chat_v2/services/chatService.ts` gate `:121-124`
- [x] **Prong 2 (content)**: read exact field sets — `ContextCompacted`{tokens_before/after,compaction_strategy,messages_compacted,duration_ms} / `PromptBuilt`{messages_count,estimated_input_tokens,cache_breakpoints_count,memory_layers_used(tuple),position_strategy_used,duration_ms} / `StateCheckpointed`{version} / `TripwireTriggered`{violation_type,detail}; cache fields `LLMResponded.cached_input_tokens` `:114` + `LoopCompleted` `:149-150`; **D6 minor drift** (plan §3.1 said `estimated_tokens`→real `estimated_input_tokens`+`position_strategy_used`); `memory_layers_used`=scope-key list (scope-safe); `GuardrailTriggered` `sse.py:237` = mirror + FE precedent (in KNOWN set + typed, no rich UI)
- [x] **Prong 3 (schema)**: N/A — no DB/migration/ORM change; 0 Alembic delta confirmed
- [x] **Doc-location verify**: `02-architecture-design.md §SSE` = wire-type catalog (sse.py header + raise both ref it); 17.md §4.1 emit-ownership needs NO new row (D4)
- [x] Catalogued D6 + D1-D5 in progress.md Day 0 table; **go/no-go = GO** (all prongs GREEN, D6 <5% scope)

### 0.2 Branch + decisions
- [x] Branch `feature/sprint-57-66-events-sse-serialize` created from `b57c0cdf`; plan+checklist committed (1st commit)
- [x] Scope decisions resolved: 4 wire-types = `prompt_built`/`context_compacted`/`state_checkpointed`/`tripwire_triggered` (snake_case mirror); cache fields additive on existing `llm_response`/`loop_end`; payloads scope-safe (memory_layers_used = scope-key list, StateCheckpointed = version only, NO raw content/snapshot); FE = mirror `GuardrailTriggered` treatment (KNOWN set + typed, NO Inspector UI — A-5c OOS); **Agent-delegated: yes** (57.64 staged pattern); real_llm leg = closes 57.63/64/65 (gated C-11 secrets)

---

## Day 1 — Backend serializer (US-1 + US-2)

### 1.1 Four diagnostic-event serializer branches (US-1) — `sse.py`
- [x] `PromptBuilt` → `prompt_built` `{messages_count, estimated_input_tokens, cache_breakpoints_count, memory_layers_used (list scope-keys), position_strategy_used, duration_ms}` + trace_id (D6: real fields)
- [x] `ContextCompacted` → `context_compacted` `{tokens_before, tokens_after, compaction_strategy, messages_compacted, duration_ms}` + trace_id
- [x] `StateCheckpointed` → `state_checkpointed` `{version}` (NO snapshot body) + trace_id
- [x] `TripwireTriggered` → `tripwire_triggered` `{violation_type, detail}` + trace_id
  - DoD ✅: all four previously hit `NotImplementedError` (`sse.py:298`) → now return a frame; mirror `GuardrailTriggered` branch shape (commit pending Day-1 bundle)

### 1.2 D3 cache-field carry (US-2) — `sse.py`
- [x] `llm_response` payload (`:140-156`) += `cached_input_tokens` (default-0-safe)
- [x] `loop_end` payload (`:197-204`) += `cached_input_tokens` + `cache_hit_rate` (default 0/0.0-safe)
  - DoD ✅: existing payloads' keys unchanged (additive); fields present when set + default when unset

### 1.3 Backend tests (US-4)
- [x] Extended existing `tests/unit/api/v1/chat/test_sse.py` (the "or extend existing" path): 7 new + 2 augmented — per-event serializer wire-type + payload; cache fields >0 + default; round-trip wire-frame; re-pointed `test_unsupported_event_raises` to `ErrorRetried` (still-unwired)
- [x] Integration: `test_chat_e2e.py::TestDiagnosticEventsE2E` — router-level `run_with_verification` mock → 4 diagnostic frames in SSE stream + cache fields on `llm_response`/`loop_end` (AP-4 prove-reaches-client through full pipeline)
- [x] Multi-tenant: `test_prompt_built` + e2e assert exact key set / scope-key list only, no raw content leak — 鐵律
- [x] **FIX-025** (discovered via the router e2e): `_jsonable` `hasattr(value,"hex")` heuristic stringified floats (`float.hex` exists) → `cache_hit_rate`/`duration_ms` wired as JSON strings; fixed to `isinstance(value, UUID)` + regression test `test_float_wire_fields_serialize_as_json_numbers`
  - DoD ✅: pytest **1964 passed / 4 skipped** (+9) / mypy src **0/319** / **9/9 V2 lints** (SDK leak 0) / black+isort+flake8 clean on 3 files

---

## Day 2 — Frontend wire-contract (US-3) + doc

### 2.1 FE wire-type recognition (US-3) — `types.ts`
- [x] Added `PromptBuiltEvent`/`ContextCompactedEvent`/`StateCheckpointedEvent`/`TripwireTriggeredEvent` types + union members + 4 strings to `KNOWN_LOOP_EVENT_TYPES`; docstring count 14→18 + MHist
- [x] Added `cached_input_tokens` to `LLMResponseEvent.data` + `cached_input_tokens`/`cache_hit_rate` to `LoopEndEvent.data` (all `number` — FIX-025 numeric wire)
  - DoD ✅: tsc EXIT 0 (re-run by parent); the 4 types pass the gate

### 2.2 FE minimal consumer (US-3)
- [x] `chatService.ts` needed NO change (gate uses `KNOWN_LOOP_EVENT_TYPES` → auto-passes once strings added). Consumer = `chatStore.ts` `mergeEvent` **exhaustive switch** (`const _exhaustive: never`) → added 4 passthrough cases `return { ...s, rawEvents }` mirroring `guardrail_triggered` (rawEvents-only, NO turn mutation, NO Inspector UI — A-5c OOS). tsc-ripple fix: `orchestrator-loop/_fixtures/demoLoopEvents.ts` cache fields on llm_response/loop_end literals.
  - DoD ✅: Vitest 686→693 (+7) — 4 wire-types recognized (not dropped) + cache fields parsed (`cache_hit_rate === 0.5`, `typeof number`) + unknown-type still dropped

### 2.3 Doc single-source
- [x] `02-architecture-design.md §SSE` += Sprint 57.66 real-serializer registration note (4 real wire-types + 2 cache fields; flags catalog's aspirational `tripwire_fired`/`compaction_triggered` vs real names; preserves drifted catalog per Naming Drift Note precedent); 17.md §4.1 unchanged (D4 — emit-ownership already has the 4 events)

---

## Day 3 — Cross-cutting + real_llm e2e + lint

- [ ] real_llm e2e (extend `test_chat_e2e_real_llm.py` or add `real_llm`-marked case): 2-turn Azure run → `prompt_built` frame in-stream + `cached_input_tokens>0` on turn-2 `llm_response`/`loop_end` → **closes deferred 57.63/64/65 legs** (gated C-11 secrets; assert via SSE stream now that A-5a makes it client-visible)
  - Verify (when run): `pytest -m real_llm tests/integration/api/test_chat_e2e_real_llm.py -q`
- [ ] Full sweep: backend `pytest` (+N new) / `mypy src/` 0 / `python scripts/lint/run_all.py` 9/9 (SDK leak 0) / frontend `npm run lint && npm run build` (NO `--silent`) + Vitest (+N new)

---

## Day 4 — Closeout

- [ ] Full validation sweep: pytest (+N) / mypy src 0 / run_all.py 9/9 / Vitest (+N) / tsc 0
- [ ] `claudedocs/4-changes/feature-changes/CHANGE-0XX-events-sse-serialize.md`
- [ ] progress.md (Day 0-4) + retrospective.md (Q1-Q7)
- [ ] Calibration: `medium-backend` 0.80 + `agent_factor mechanical-greenfield-design-decisions` 0.65 (caveated per `AD-Calibration-AgentDelegated-WallClock-Measure`); record `calibration-log.md §3`
- [ ] Area-A capstone: A-5a+ shipped; D2/D3 corrections runtime-confirmed; A-5b/A-5c remain
- [ ] MEMORY.md pointer + `project_phase57_66_*.md` subfile + CLAUDE.md lean Current Sprint/Last Updated
- [ ] commit (Day 1-4) + push + PR — user-authorized
- [ ] 🚧 (carry if real_llm leg can't run locally — Azure secrets; mock tests are the primary gate)
