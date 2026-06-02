# Sprint 57.66 Plan — Serialize Already-Yielded Diagnostic Events to Client SSE (A-5a+)

**Purpose**: Make four agent-loop diagnostic `LoopEvent`s that are **already yielded on the production chat path but silently skipped at the SSE serializer** become client-observable — `PromptBuilt` (Cat 5), `ContextCompacted` (Cat 4), `StateCheckpointed` (Cat 7), `TripwireTriggered` (Cat 9) — plus fold the 57.65 prompt-cache signal (`cached_input_tokens` / `cache_hit_rate`) into the existing `llm_response` / `loop_end` SSE payloads (a fresh regression: 57.65 added the fields to the events but the serializer never carried them). **Zero `loop.py` changes** — the events already reach `serialize_loop_event`; the gap is the missing isinstance branches + the FE wire-type gate. This directly **unblocks the deferred `real_llm` e2e legs from Sprints 57.63/57.64/57.65** (the stated A-5 motivation: prior-sprint capabilities become externally observable instead of dying in-process).
**Category / Scope**: Cat 12 (Observability — SSE serialization, cross-cutting) touching Cat 5/4/7/9 event surfaces + light frontend wire-type contract; Phase 57.66
**Created**: 2026-06-01
**Status**: Draft (user-approved scope: Option A "A-5a+ serialize already-yielded"; code execution gated on Day-0 GO)
**Source**: `claudedocs/5-status/cat-events-to-sse-analysis-20260531.md` (A-5 sub-analysis) + `area-a-integration-sequencing-capstone-20260531.md` (A-5a/b/c split) + **Day-0 reality audit (codebase-researcher, 2026-06-01)** which corrected the capstone's pre-57.64/57.65 baseline (D1-D5 below) + user AskUserQuestion decision 2026-06-01 (Option A over A-5b codegen / A-5b+A-5a bundle)

> **Modification History**
> - 2026-06-01: Initial creation — A-5a+ slice; folds Day-0 audit drift (D1 A-5-is-3-sub-pieces, D2 PromptBuilt-now-yielded-post-57.64, D3 57.65-cache-fields-die-at-SSE, D5 dataclass-not-Pydantic) into §0 + §8

---

## 0. Background

The user selected "A-5 (events→SSE)" as the most valuable next sprint. A **Day-0 reality audit on current main (`b57c0cdf`)** found "A-5" is **not one sprint** — the source docs (`cat-events-to-sse-analysis` §7 + capstone §3) explicitly split it into **A-5a** (serialize `TripwireTriggered`), **A-5b** (schema codegen + CI parity gate), **A-5c** (diagnostic SSE + Inspector UI, downstream of A-1/A-2/A-4). User chose (AskUserQuestion 2026-06-01) the **A-5a+ slice**: serialize the already-yielded diagnostic events + close the 57.65 cache-field regression, deferring A-5b (codegen) and A-5c (Inspector UI).

The audit corrected the capstone's stale baseline (folded here, not silently rewritten, per `sprint-workflow.md §Step 2.5`):

### ⚠️ Day-0 drift corrections (from post-57.64/57.65 reality audit)

- **D1 — "A-5" is 3 sub-pieces, not one sprint**: capstone bundles A-5b+A-5a as 候選 Sprint C and defers A-5c. This sprint is a deliberately tighter slice than either source framing: serialize the **already-yielded** events (the cheap, high-value core) + the 57.65 cache fields; **A-5b codegen + A-5c Inspector UI are OUT** (§9).
- **D2 — `PromptBuilt` is ALREADY yielded on the chat path (capstone "only yielded once A-2 lands" is STALE)**: 57.64 wired the keystone PromptBuilder; `loop.py:883` now guards `if self._prompt_builder is not None:` and yields `PromptBuilt` at `loop.py:919` with `memory_layers_used` etc. It reaches `serialize_loop_event` and hits `NotImplementedError` (`sse.py:298`), caught + skipped at `router.py:354-359`. So `PromptBuilt` moves from "not-yielded" into the **cheap-serializer bucket** — adding one isinstance branch makes it client-visible.
- **D3 — 57.65 cache signal DIES at the SSE boundary (fresh in-scope regression)**: 57.65 added `cached_input_tokens` to `LLMResponded` (`events.py:114`) and `cached_input_tokens`/`cache_hit_rate` to `LoopCompleted` (`events.py:149-150`), but the serializers were NOT updated — `llm_response` payload (`sse.py:142-156`) and `loop_end` payload (`sse.py:197-204`) omit both. The cache-observability signal never reaches the client. **Cheapest possible win: add the fields to the two existing payloads (no new event).**
- **D4 — exactly 26 concrete `LoopEvent` subclasses** in single-source `_contracts/events.py` (`orchestrator_loop/events.py` is a re-export shim). The doc's "~22-26" hedge resolves to 26. The 4 target events all already exist + are emitted; this sprint adds **no new event subclass** → 17.md §4.1 emit-ownership table needs no new row (the wire-type mapping is the only doc delta — see §3.5).
- **D5 — A-5b's codegen toolchain is genuinely absent + would need a dataclass exporter**: `export_event_schemas.py` / `events.json` / `events.ts` / `event-schema-sync.yml` do not exist (confirmed), and `events.py` uses **frozen dataclasses, not Pydantic** (`events.py:51`) so 16.md's "Pydantic→JSON Schema" assumption is wrong. This is exactly why A-5b is deferred (§9) — it's a distinct toolchain sprint, not part of this slice.

**Net**: the mechanism is proven (the `GuardrailTriggered` 53.6 pattern: add an isinstance branch in `sse.py` + add the wire-type string to FE `KNOWN_LOOP_EVENT_TYPES` + a consumer). No `loop.py` change. No new event subclass. Scope is a tight backend serializer + light-FE wire-contract slice.

---

## 1. Sprint Goal

Make the four already-yielded-but-skipped diagnostic events (`PromptBuilt` / `ContextCompacted` / `StateCheckpointed` / `TripwireTriggered`) reach the client over the chat SSE stream via new `sse.py` serializer branches + FE wire-type registration + minimal `rawEvents`-level consumers, and carry the 57.65 prompt-cache fields (`cached_input_tokens` / `cache_hit_rate`) on the existing `llm_response` / `loop_end` frames. Prove it with backend tests (a driven tripwire produces a `tripwire_triggered` frame; the diagnostic events serialize with scope-safe payloads; cache fields present) + FE tests (the new wire-types are recognized, not dropped) + a `real_llm` e2e asserting `prompt_built` + cache fields appear in-stream — which **closes the deferred 57.63/64/65 real_llm legs**. **No `loop.py` change** (events already yielded — D2); payloads are scope-checked (no raw memory keys/content — multi-tenant 鐵律).

---

## 2. User Stories

- **US-1 (A-5a serialize diagnostic events)** — As an operator watching a chat run, I want to see when the agent built its prompt, compacted context, checkpointed state, or tripped a guardrail, so the loop's internal reasoning steps are visible instead of invisible. → add `sse.py` isinstance branches for `PromptBuilt` → `prompt_built`, `ContextCompacted` → `context_compacted`, `StateCheckpointed` → `state_checkpointed`, `TripwireTriggered` → `tripwire_triggered`, each with a scope-safe JSON payload (counts / version / violation_type — NO raw memory content).
- **US-2 (D3 cache-field carry)** — As a platform owner, I want the 57.65 prompt-cache signal (`cached_input_tokens` + `cache_hit_rate`) to actually reach the client on the `llm_response` / `loop_end` frames, so the cache-effectiveness metric is observable end-to-end (today it dies at the serializer). → extend the existing `llm_response` + `loop_end` payloads with the two fields (no new event).
- **US-3 (FE wire-type contract)** — As a frontend consumer, I want the four new wire-types recognized (not dropped by the `KNOWN_LOOP_EVENT_TYPES` gate) and landed in `rawEvents`, so the events are available for later Inspector UI (A-5c) without a rich UI now. → add the four strings + TS types; add the cache fields to the `llm_response`/`loop_end` TS types; minimal `rawEvents`-level handling.
- **US-4 (Validation + real_llm unblock)** — As a reviewer, I want backend + FE tests proving the events serialize + are recognized, and a `real_llm` e2e proving `prompt_built` + cache fields appear in the client stream, so the deferred 57.63/64/65 legs are closed at runtime.

---

## 3. Technical Specifications

### 3.0 Shared change surface
- **`backend/src/api/v1/chat/sse.py`** — the serializer `serialize_loop_event` (16 isinstance branches today; frame builder `:304-307` `event: <type>\ndata: <json>\n\n`; `trace_id` injected `:108-109`; `NotImplementedError` fallthrough `:298`). All four new branches follow the existing branch shape; the cache-field carry edits the existing `llm_response` (`:142-156`) + `loop_end` (`:197-204`) payload dicts.
- **Wire-type naming**: snake_case to match the existing 14 (`llm_response`, `loop_end`, `tool_call`, `verification_passed`, …) → `prompt_built` / `context_compacted` / `state_checkpointed` / `tripwire_triggered`.
- **No `loop.py`**: the four events are already yielded (D2; `loop.py:919/863/1013+1324/456+527+747`). No new event subclass (D4).
- **LLM-neutral**: serialization is provider-free; `agent_harness/**` untouched → `check_llm_sdk_leak` stays 0.

### 3.1 A-5a serialize the four diagnostic events (US-1) — `sse.py` (net-new branches)
Each branch maps the frozen-dataclass event → a scope-safe payload (Day-0 Prong 2 reads the real `events.py` field set; payload includes ONLY the listed fields):
- `PromptBuilt` (`events.py:206`) → `prompt_built`: `{messages_count, estimated_tokens, cache_breakpoints_count, memory_layers_used, duration_ms}` — `memory_layers_used` is the **scope-key list** (e.g. `["session","tenant"]`), NOT raw memory content (multi-tenant note).
- `ContextCompacted` (`events.py:194`) → `context_compacted`: `{<fields per events.py — tokens_before/after / strategy / etc.>}` (confirm exact fields Day-0 Prong 2).
- `StateCheckpointed` (`events.py:233`) → `state_checkpointed`: `{version}` (+ any non-sensitive metadata; NO snapshot body).
- `TripwireTriggered` (`events.py:273`) → `tripwire_triggered`: `{violation_type, detail}` (scope-safe; `detail` already a human string).
- All carry the injected `trace_id` like every other frame (`:108-109`).

### 3.2 D3 cache-field carry (US-2) — `sse.py` (edit existing payloads)
- `llm_response` payload (`:142-156`) += `cached_input_tokens` (from `LLMResponded.cached_input_tokens`, `events.py:114`; default 0 / None-safe).
- `loop_end` payload (`:197-204`) += `cached_input_tokens` + `cache_hit_rate` (from `LoopCompleted`, `events.py:149-150`; None-safe).
- No new wire-type; existing `llm_response`/`loop_end` consumers keep working (additive fields).

### 3.3 FE wire-type contract + minimal consumer (US-3)
- **`frontend/src/.../types.ts`** (`:177-192` `KNOWN_LOOP_EVENT_TYPES` Set + the event union types) — add `prompt_built` / `context_compacted` / `state_checkpointed` / `tripwire_triggered` to the Set; add TS payload types; add `cached_input_tokens`/`cache_hit_rate` to the `llm_response`/`loop_end` types.
- **`frontend/src/.../chatService.ts`** (`:121-124` KNOWN gate) — the four types now pass the gate → land in `rawEvents`. **Minimal consumer only**: ensure they're not dropped + are appended to `rawEvents`; **NO rich Inspector UI** (deferred to A-5c). Optional: a lightweight `tripwire_triggered` surfacing (alert/toast) if it fits the existing event-handling switch cheaply — confirm Day-1 (A-5a's "decent UX" note); otherwise rawEvents-only for all four.

### 3.4 Validation (US-4)
- **Backend** (new `backend/tests/integration/api/test_chat_sse_diagnostic_events.py` or extend an existing SSE serializer test): unit-level — `serialize_loop_event` returns the right wire-type + payload for each of the four events (was `NotImplementedError`); cache fields present in `llm_response`/`loop_end` payloads with `cached_input_tokens>0` mock and None-safe when absent. Integration — a run that **drives a tripwire** (guardrail violation) asserts a `tripwire_triggered` frame appears in the SSE stream alongside `loop_end` (AP-4: prove it reaches the client, not just that the branch exists). Multi-tenant: assert no raw memory content / cross-tenant keys in `prompt_built.memory_layers_used` (scope-key list only).
- **FE** (Vitest): the four new wire-types pass `KNOWN_LOOP_EVENT_TYPES` (not dropped) + parse into typed events + land in `rawEvents`; `llm_response`/`loop_end` parse the new cache fields.
- **`real_llm` e2e**: a 2-turn Azure chat run → assert `prompt_built` frame in-stream + `cached_input_tokens>0` on turn-2 `llm_response`/`loop_end` (cache warm). **This closes the deferred 57.63/64/65 legs** (PromptBuilt/cache now HTTP-observable). Gated on C-11 Azure secrets; assert via the SSE stream now that A-5a makes it client-visible (the A-5 OOS caveat that blocked 57.63/64/65 is precisely what this sprint removes for these events).

### 3.5 Lint / neutrality / doc single-source
- `check_llm_sdk_leak` stays 0 (serializer is provider-free). No new naked-assembly. `check_promptbuilder_usage` unaffected.
- **Doc single-source**: 17.md §4.1 is **emit-ownership** — the 4 events already exist there, **no new row** (D4). The **LoopEvent→client-SSE wire-type mapping** lives in `02-architecture-design.md §SSE` (referenced by `sse.py:58`) — register the 4 new wire-types + the 2 added cache fields there. Day-0 Prong 1 confirms the exact doc section/location.

---

## 4. File Change List

| File | Change |
|------|--------|
| `backend/src/api/v1/chat/sse.py` | **net-new**: 4 isinstance branches (`PromptBuilt`/`ContextCompacted`/`StateCheckpointed`/`TripwireTriggered` → snake_case wire-types, scope-safe payloads); **edit**: add `cached_input_tokens` to `llm_response` payload + `cached_input_tokens`/`cache_hit_rate` to `loop_end` payload (D3) |
| `frontend/src/.../types.ts` | add 4 wire-type strings to `KNOWN_LOOP_EVENT_TYPES` + TS payload types; add cache fields to `llm_response`/`loop_end` types (exact path Day-0 Prong 1) |
| `frontend/src/.../chatService.ts` | minimal `rawEvents`-level handling for the 4 new types (no Inspector UI); optional lightweight `tripwire_triggered` surfacing if cheap |
| `backend/tests/integration/api/test_chat_sse_diagnostic_events.py` (or extend existing SSE test) | **NEW/extend** — serializer per-event + cache fields + driven-tripwire integration + multi-tenant scope-safe payload |
| `frontend/src/.../*.test.ts(x)` | **NEW/extend** Vitest — 4 wire-types recognized + parsed + cache fields parsed |
| `docs/03-implementation/agent-harness-planning/02-architecture-design.md` (§SSE wire-type catalog) | register 4 new wire-types + 2 added cache fields (single-source; exact section Day-0) |
| `backend/tests/integration/api/test_chat_e2e_real_llm.py` | extend (or add `real_llm`-marked case) — `prompt_built` + cache fields in-stream on 2-turn Azure run (closes 57.63/64/65 legs) |
| `claudedocs/4-changes/feature-changes/CHANGE-0XX-events-sse-serialize.md` | change record |

**No DB migration**, **no `loop.py` change** (events already yielded — D2), **no new `LoopEvent` subclass** (D4), **no Azure-adapter change**, **no A-5b codegen / A-5c Inspector UI** (§9).

---

## 5. Acceptance Criteria

- `serialize_loop_event` returns the correct wire-type + scope-safe payload for all four diagnostic events (previously `NotImplementedError` → router silent-skip); no raw memory content / snapshot body in any payload.
- `llm_response` carries `cached_input_tokens`; `loop_end` carries `cached_input_tokens` + `cache_hit_rate` (None/0-safe) — the 57.65 signal now reaches the client (D3 closed).
- FE recognizes the four new wire-types (pass `KNOWN_LOOP_EVENT_TYPES`, not dropped), parses them + the new cache fields into typed events, and lands them in `rawEvents`.
- Backend integration test: a driven guardrail violation produces a `tripwire_triggered` frame in the SSE stream (AP-4 prove-reaches-client); multi-tenant payload-scope test passes.
- `real_llm` e2e: a 2-turn Azure run shows a `prompt_built` frame + `cached_input_tokens>0` on turn-2 — the deferred 57.63/64/65 real_llm legs are closed (gated on C-11 secrets).
- All existing tests green; `mypy --strict` clean; 9/9 V2 lints (**LLM SDK leak 0**); existing 14 wire-types + their consumers unaffected (additive); no `loop.py` / Azure-adapter / new-event-subclass changes.

---

## 6. Deliverables

- [ ] `sse.py`: 4 net-new serializer branches (`prompt_built`/`context_compacted`/`state_checkpointed`/`tripwire_triggered`), scope-safe payloads (US-1)
- [ ] `sse.py`: cache fields into `llm_response` + `loop_end` payloads (US-2, D3)
- [ ] FE `types.ts`: 4 wire-type strings + payload types + cache fields (US-3)
- [ ] FE `chatService.ts`: minimal `rawEvents` consumers (US-3)
- [ ] backend test: per-event serializer + cache fields + driven-tripwire integration + multi-tenant scope-safe (US-4)
- [ ] FE Vitest: 4 wire-types recognized + parsed + cache fields (US-4)
- [ ] `real_llm` e2e: `prompt_built` + cache fields in-stream (closes 57.63/64/65 legs) (US-4)
- [ ] `02-architecture-design.md §SSE` wire-type catalog updated (single-source)
- [ ] CHANGE record + progress.md + retrospective.md

---

## 7. Workload Calibration

Scope class: **`medium-backend` (0.80)** — backend serializer is the bulk; FE is wire-strings + minimal `rawEvents` consumer (NO mockup/page work → not a frontend-class sprint). **Agent-delegated: yes** (57.64/57.65 proven staged-delegation pattern; well-scoped serializer mirror of the `GuardrailTriggered` 53.6 precedent) → `agent_factor` **`mechanical-greenfield-design-decisions` 0.65** (4 distinct event-payload shape decisions + cache-field placement + FE consumer = genuine design beyond a single mechanical port; consistent with 57.64/57.65 sub-class).

> Bottom-up est ~8 hr → class-calibrated commit ~6.4 hr (mult 0.80) → agent-adjusted commit ~4.2 hr (agent_factor 0.65).

Calibration caveat carried from 57.63/64/65: agent-delegated sprints have not produced a clean wall-clock measurement (`AD-Calibration-AgentDelegated-WallClock-Measure`); record this point as caveated, do NOT adjust the 0.65 baseline on it alone.

---

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| **D1 — A-5 is 3 sub-pieces; scoping creep** | this sprint is the A-5a+ slice ONLY (serialize already-yielded + cache fields); A-5b codegen + A-5c Inspector UI explicitly OOS (§9) |
| **D2 — capstone says PromptBuilt not-yielded (STALE)** | confirmed yielded `loop.py:919` post-57.64; no `loop.py` change — just the serializer branch |
| **D3 — 57.65 cache fields die at serializer (fresh regression)** | add to existing `llm_response`/`loop_end` payloads (additive; no new event); test asserts fields present |
| **Multi-tenant leakage via diagnostic payloads** | `PromptBuilt.memory_layers_used` = scope-key list only (e.g. `["session"]`), NOT raw content; `StateCheckpointed` = `version` only, NO snapshot body; cross-tenant/scope-safe payload test (multi-tenant 鐵律) |
| **FE double-gate**: serializer branch without FE wire-string → still dropped client-side | add both the serializer branch AND the `KNOWN_LOOP_EVENT_TYPES` string in the same sprint (the double-gate the A-5b codegen would prevent; here done by hand + covered by FE test) |
| **Exact `ContextCompacted` / `StateCheckpointed` field set** | Day-0 Prong 2 reads `events.py:194/233` bodies before writing payloads (read body not name — `AD-Day0-Prong2-Nested-Shape-Read`) |
| **Wire-type doc location** (17.md §4.1 vs 02.md §SSE) | Day-0 Prong 1 confirms: 17.md §4.1 = emit-ownership (no new row, D4); wire-type mapping → `02-architecture-design.md §SSE` |
| **Driving a tripwire deterministically in test** | use an existing guardrail-violation fixture / a deterministic input that trips a configured tripwire; if none exists, monkeypatch the guardrail to yield `TripwireTriggered` (assert the SSE frame, not the guardrail logic) |
| **real_llm cache warm-up** (turn-1 cold) | 2-turn run; assert `cached_input_tokens>0` on turn-2; gated on C-11 Azure secrets; cost note (FIX-024 cost_ledger red — billing bundle, independent) |
| **Module-level singleton test isolation** (Risk Class C) | autouse reset fixtures per `.claude/rules/testing.md` (existing chat test conftest pattern) |
| **LLM-neutrality** | serializer is provider-free; `agent_harness/**` untouched; `check_llm_sdk_leak` gates |

---

## 9. Out of Scope

- **A-5b schema codegen + CI parity gate** (`export_event_schemas.py` → `events.json` → `events.ts` + `event-schema-sync.yml`) — separate infra sprint (候選 Sprint C component); note D5 (dataclass-not-Pydantic exporter needed). The hand-maintained `KNOWN_LOOP_EVENT_TYPES` + FE test is the interim drift guard.
- **A-5c diagnostic Inspector UI** (rich rendering of `prompt_built`/`context_compacted`/`state_checkpointed` in the chat Inspector) — later FE sprint, downstream; this sprint only lands the events in `rawEvents`.
- **Never-yielded events** (`MemoryAccessed` / `Span*` / `Metric*` / `ErrorRetried` / `LoopTerminated`) — require `loop.py` upstream emission (A-1/A-4/Cat 8), not part of A-5's surface.
- **SSE `id:` line / `last_event_id` resume** — the stream has no event-id today (cat-events §3); resume is a separate concern.
- **`loop.py` changes / new `LoopEvent` subclass** — events already yielded (D2); none added (D4).
- **FIX-024 billing** (cost_ledger / pricing drift / max_tokens gpt-5.x) — billing bundle B-7/B-8/C-15, independent.
