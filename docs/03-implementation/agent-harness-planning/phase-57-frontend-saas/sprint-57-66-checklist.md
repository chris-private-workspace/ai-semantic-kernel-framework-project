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
- [ ] `PromptBuilt` → `prompt_built` `{messages_count, estimated_tokens, cache_breakpoints_count, memory_layers_used (scope-key list), duration_ms}` + trace_id
  - DoD: `serialize_loop_event(PromptBuilt(...))` returns `prompt_built` frame; no raw memory content in payload
- [ ] `ContextCompacted` → `context_compacted` (exact fields per Day-0 Prong 2) + trace_id
- [ ] `StateCheckpointed` → `state_checkpointed` `{version}` (NO snapshot body) + trace_id
- [ ] `TripwireTriggered` → `tripwire_triggered` `{violation_type, detail}` + trace_id
  - DoD: all four previously hit `NotImplementedError` (`sse.py:298`) → now return a frame; mirror `GuardrailTriggered` branch shape

### 1.2 D3 cache-field carry (US-2) — `sse.py`
- [ ] `llm_response` payload (`:142-156`) += `cached_input_tokens` (None/0-safe)
- [ ] `loop_end` payload (`:197-204`) += `cached_input_tokens` + `cache_hit_rate` (None/0-safe)
  - DoD: existing `llm_response`/`loop_end` consumers unaffected (additive); fields present when `cached_input_tokens>0`

### 1.3 Backend tests (US-4)
- [ ] NEW `test_chat_sse_diagnostic_events.py` (or extend existing SSE test): per-event serializer wire-type + payload; cache fields present + None-safe
- [ ] Integration: driven guardrail violation → `tripwire_triggered` frame in SSE stream alongside `loop_end` (AP-4 prove-reaches-client)
- [ ] Multi-tenant: `prompt_built.memory_layers_used` = scope-key list only, no cross-tenant/raw content (鐵律)
  - DoD: backend suite green; mypy src 0; `check_llm_sdk_leak` 0

---

## Day 2 — Frontend wire-contract (US-3) + doc

### 2.1 FE wire-type recognition (US-3) — `types.ts`
- [ ] Add `prompt_built`/`context_compacted`/`state_checkpointed`/`tripwire_triggered` to `KNOWN_LOOP_EVENT_TYPES` (`:177-192`) + TS payload types
- [ ] Add `cached_input_tokens`/`cache_hit_rate` to `llm_response`/`loop_end` TS types
  - DoD: tsc 0; the 4 types pass the gate (`chatService.ts:121-124`)

### 2.2 FE minimal consumer (US-3) — `chatService.ts`
- [ ] 4 new types land in `rawEvents` (not dropped); NO Inspector UI (A-5c OOS); optional lightweight `tripwire_triggered` surfacing only if cheap in the existing switch
  - DoD: Vitest — 4 wire-types recognized + parsed into typed events + appended to rawEvents; cache fields parsed on llm_response/loop_end

### 2.3 Doc single-source
- [ ] `02-architecture-design.md §SSE` wire-type catalog += 4 new types + 2 cache fields (single-source); 17.md §4.1 unchanged (D4 — emit-ownership already has the 4 events)

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
