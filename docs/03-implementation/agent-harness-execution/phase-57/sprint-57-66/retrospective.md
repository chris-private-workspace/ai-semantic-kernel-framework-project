# Sprint 57.66 Retrospective — Serialize Already-Yielded Diagnostic Events to Client SSE (A-5a+)

**Date**: 2026-06-02
**Sprint**: 57.66
**Scope**: A-5a+ — surface 4 already-yielded diagnostic `LoopEvent`s (`PromptBuilt`/`ContextCompacted`/`StateCheckpointed`/`TripwireTriggered`) on the client chat SSE stream + carry the 57.65 prompt-cache fields on `llm_response`/`loop_end`; backend serializer + light FE wire-contract; **no loop.py change**
**Status**: Closed (with one deferred item: real_llm live e2e — confirmatory; blocker REMOVED this sprint, only gated on Azure secrets now)

> Modification History
> - 2026-06-02: Initial creation (Sprint 57.66 closeout)

---

## Q1: What was delivered?

- **A-5a serialize (backend)**: `sse.py` 4 net-new isinstance branches mirroring the `GuardrailTriggered` 53.6 pattern — `PromptBuilt`→`prompt_built`, `ContextCompacted`→`context_compacted`, `StateCheckpointed`→`state_checkpointed`, `TripwireTriggered`→`tripwire_triggered`. Scope-safe payloads (`memory_layers_used` = scope-key list, `state_checkpointed` = `version` only). No `loop.py` change (events already yielded post-57.64).
- **D3 cache-field carry (backend)**: `cached_input_tokens` on `llm_response`; `cached_input_tokens`+`cache_hit_rate` on `loop_end` (additive). Closes the fresh 57.65 regression where the cache signal died at the serializer boundary.
- **FE wire-contract**: `chat_v2/types.ts` 4 new event types + union + `KNOWN_LOOP_EVENT_TYPES` (14→18) + cache fields (all `number`); `chatStore.ts` `mergeEvent` 4 passthrough cases (rawEvents-only, mirror `guardrail_triggered`, no Inspector UI — A-5c deferred); `demoLoopEvents.ts` fixture cache-field ripple. `chatService.ts` unchanged (gate auto-passes via the KNOWN set).
- **FIX-025**: root-cause fix to `sse.py:_jsonable` — the `hasattr(value,"hex")` UUID heuristic also matched `float` (`float.hex` exists), stringifying `cache_hit_rate`/`duration_ms` on the wire (`"0.5"`). Fixed to `isinstance(value, UUID)`. Discovered by the router e2e (the only test that round-trips a float through `format_sse_message`).
- **Doc**: `02-architecture-design.md §SSE` real-serializer registration note (single-source); 17.md §4.1 unchanged (events already registered — D4).
- **Tests**: `test_sse.py` +7 unit +2 augmented + 1 FIX-025 regression; `test_chat_e2e.py` `TestDiagnosticEventsE2E` router-level AP-4 e2e; `chatService.parseSSEFrame.test.ts` +7 FE.

**Core thesis validated**: the 4 events were a cheap-serializer bucket (already yielded, just unmapped) — a tight backend+FE wire slice with zero loop.py change makes the prior-sprint capabilities (Cat 4/5/7/9 + 57.65 cache) client-observable, which removes the architectural blocker the 57.63/64/65 real_llm legs were deferred on.

## Q2: Estimate accuracy (calibration)

- Scope class: **medium-backend (0.80)** (backend serializer is the bulk; FE is wire-strings + minimal passthrough, no page/mockup work).
- **Agent-delegated: YES** — Stage 1 (backend serializer + tests + router e2e) + Stage 2 (FE wire-contract) via 2 sequential `code-implementer` agents, each independently re-verified by the parent (read all diffs; re-ran backend full suite + FE tsc + the new tests). FIX-025 + the 02.md drift note + closeout were parent-direct. → **`agent_factor` `mechanical-greenfield-design-decisions` 0.65** (the 4 serializer payload shapes + the FIX-025 root-cause + the exhaustive-switch + 02.md-drift decisions carry design weight beyond a single mechanical port; consistent with 57.64/57.65 sub-class — a `-port-style` 0.45 read is defensible since the branches mirror GuardrailTriggered, noted as the alternative).
- Plan §Workload: bottom-up ~8 hr → class-calibrated ~6.4 hr (0.80) → agent-adjusted ~4.2 hr (×0.65).
- **Actual**: NOT cleanly wall-clock-measurable — 3 background agents (Stage 1 + the router-test follow-up + Stage 2) + parent re-verification + parent FIX-025 investigation + parent docs dominate and don't map to "focused human implementation hours". **Low-confidence; do NOT adjust 0.65.** This is the **4th consecutive agent-delegated sprint (57.63/64/65/66) without a clean wall-clock** — reinforces `AD-Calibration-AgentDelegated-WallClock-Measure` (Q6).

## Q3: What went well?

- **Day-0 audit (researcher) correctly reframed the scope before any code**: it found "A-5" is 3 sub-pieces (A-5a/b/c), that PromptBuilt is now yielded post-57.64 (D2), and that the 57.65 cache fields die at the SSE boundary (D3). The user picked the tightest high-value slice (A-5a+) at an AskUserQuestion gate — avoided building A-5b codegen or A-5c Inspector UI prematurely.
- **Staged delegation + parent re-verification surfaced + fixed a real production bug**: the router e2e (added as an AP-4 follow-up) was the FIRST test to round-trip a float through `format_sse_message`, exposing FIX-025 (`cache_hit_rate` wired as `"0.5"`). Because I asked for the full-pipeline e2e (not just the isolated serializer unit test), the latent bug surfaced inside this sprint instead of as a frontend type-mismatch later.
- **Right call to fix FIX-025 in-sprint, not defer**: the agent flagged it as "out of Stage 2 scope (production sse.py)", but `cache_hit_rate` is a NEW wire field THIS sprint ships — a stringified float would make the Stage-2 FE TS type (`number`) a lie. Fixing the root cause (`_jsonable`) was the correct call (also incidentally corrected the pre-existing `duration_ms` stringification — same code path, not scope creep).
- **The exhaustive `switch (never)` in `chatStore.mergeEvent` worked as designed**: adding 4 union members forced explicit handling (tsc caught it), so the events can't be silently forgotten on the FE — the type system enforced the wire-contract completeness.
- **Honest doc handling**: `02-architecture-design.md §SSE` was already drifted (lists aspirational `tripwire_fired`/`compaction_triggered`). I added a 57.66 registration note for the REAL wire-types rather than rewriting the historical catalog — consistent with the doc's own Naming Drift Note precedent.

## Q4: What to improve?

- **The plan referenced a `test_chat_e2e_real_llm.py` + `real_llm` marker that don't exist**. The 57.63/64/65 plans propagated this same phantom reference. A Day-0 prong should have grepped for the marker/file before the plan committed to "extend `test_chat_e2e_real_llm.py`". Minor (the real_llm leg was always going to defer on secrets), but the plan's File Change List cited a non-existent file. Lesson: Day-0 Prong 1 should verify cited test-infra files exist, not just product files.
- **Sub-class ambiguity (port-style 0.45 vs design-decisions 0.65)**: this sprint sits between the two — mostly a mechanical mirror of GuardrailTriggered, but with genuine design (FIX-025, payload shapes, drift handling). The caveated low-confidence calibration makes the choice low-stakes, but the agent-delegated wall-clock problem (Q6) means we keep recording sub-class points we can't cleanly validate.
- **FIX-025 is a pre-existing bug that escaped since Sprint 50.2** because no test asserted the wire-level numeric type. A broader "serializer round-trip type" test pass (asserting all numeric payload fields wire as numbers) would have caught it earlier — but that's a separate hardening task, not in this slice.

## Q5: Anti-pattern audit (11 checks)

- AP-1 (Pipeline-as-Loop): N/A — no loop change; the serializer is a pure function.
- AP-2 (side-track): ✅ — all new branches reachable from `router.py:_stream_loop_events`; the router e2e proves the path.
- AP-3 (cross-dir scatter): ✅ — serializer in `api/v1/chat/sse.py`, FE contract in `chat_v2/types.ts` — each in its cohesive home.
- AP-4 (Potemkin): ✅ — `TestDiagnosticEventsE2E` proves the events reach the client through the REAL router pipeline (not just the isolated serializer); the multi-tenant test asserts no content leak. **Deliberately did NOT create a never-running real_llm test** (that would BE an AP-4 violation) — deferred it honestly.
- AP-5 (PoC accumulation): N/A.
- AP-6 (hybrid bridge debt): ✅ — no speculative abstraction; serializer branches mirror the existing pattern; FE passthrough mirrors guardrail_triggered.
- AP-7 (context rot): N/A.
- AP-8 (no central PromptBuilder): N/A — Cat 5 not touched (PromptBuilt event already emitted by 57.64).
- AP-9 (no verification): N/A.
- AP-10 (mock vs real divergence): ✅ — the router e2e drives the REAL `_stream_loop_events`→`serialize`→`format` pipeline with a mocked loop generator; the serializer + format functions under test are the production ones.
- AP-11 (version suffix): ✅ — no `_v1`/`_v2` names.

## Q6: Carryover ADs

- **AD-Calibration-AgentDelegated-WallClock-Measure** (continues — now 4 consecutive: 57.63/64/65/66): agent-delegated sprints produce only caveated low-confidence calibration points; the "focused human hours" denominator doesn't fit staged-delegation-plus-review. Propose a measure capturing agent wall-clock + parent review/verify/investigate overhead.
- **AD-A-5b-Schema-Codegen** (NEW — the deferred A-5b): build the dataclass→`events.json`→`events.ts` exporter + `event-schema-sync.yml` CI parity gate. D5: `events.py` is frozen dataclasses (NOT Pydantic), so the exporter must be dataclass-based. High-leverage (prevents the hand-maintained `KNOWN_LOOP_EVENT_TYPES`/serializer double-gate drift this sprint did by hand) + no upstream dep. (capstone 候選 Sprint C component.)
- **AD-A-5c-Diagnostic-Inspector-UI** (NEW — the deferred A-5c): rich Inspector rendering of `prompt_built`/`context_compacted`/`state_checkpointed` (the events now land in `rawEvents` only). Downstream FE sprint.
- **AD-SSE-Serializer-Numeric-RoundTrip-Hardening** (NEW — from FIX-025): a focused test pass asserting ALL numeric SSE payload fields wire as JSON numbers (FIX-025 fixed `_jsonable` but a regression net beyond `cache_hit_rate` would harden against future float-field additions).
- **AD-Day0-Prong1-TestInfra-File-Verify** (NEW — from Q4): Day-0 Prong 1 should verify cited test-infra files (e.g. `test_chat_e2e_real_llm.py`, pytest markers) exist, not just product files — the phantom `real_llm` file/marker propagated across 3 sprint plans.
- **AD-RealLLM-E2E-Live-Confirmation** (continues, blocker now REMOVED): a live-Azure 2-turn run asserting `prompt_built` + `cached_input_tokens>0` in the HTTP SSE stream is now writable (A-5a made it client-visible) — only gated on Azure secrets; supersedes the 57.63/64/65 "blocked by A-5 OOS" framing.
- **02.md §SSE catalog drift** (continues, informational): the catalog still lists aspirational `tripwire_fired`/`compaction_triggered`/`guardrail_check`/`hitl_required`/`verification_start` that don't match the real serializer; a future doc-hygiene pass could reconcile it (out of this slice — I added a registration note, not a rewrite).

## Q7: Calibration matrix update

- Record 1 data point: scope class `medium-backend` (0.80), `agent_factor = mechanical-greenfield-design-decisions 0.65` (agent-delegated: yes), **CAVEATED low-confidence** (no clean wall-clock — 2 staged agents + a follow-up agent + parent FIX-025/docs/re-verify dominate). **Do NOT adjust the 0.65 sub-class baseline** on this point; it does NOT count toward `AD-AgentFactor-DesignDecisions-Below-Band-Watch` (which needs a clean measurement). Prior clean validations (57.56=1.02 / 57.57=1.15 IN / 57.61=0.74 / 57.62=0.77 BELOW) stand unchanged.
- **Meta-observation (4th consecutive caveat)**: 57.63 (1.0) / 57.64 (0.65) / 57.65 (0.65) / 57.66 (0.65) all caveated — the staged-delegation-plus-review mode is structurally unmeasurable in "focused human hours". Logged as `AD-Calibration-AgentDelegated-WallClock-Measure`. Record in `calibration-log.md §3`.

## Closeout checklist

- [x] Plan + checklist exist (1st branch commit `14fa1168`)
- [x] Day 0 三-prong (audit + re-verify; D6 field-name drift catalogued; GO) `cf062802`
- [x] Stage 1 (backend serializer + unit + router e2e) `fda80b09` delegated + parent re-verified; FIX-025 in same commit
- [x] Stage 2 (FE wire-contract + 02.md) `41576b89` delegated + parent re-verified (re-ran tsc + 7 tests)
- [x] Tests: backend +9 (full **1964 passed / 4 skipped**); FE +7 (Vitest **693**)
- [x] mypy src **0/319** / 9-9 V2 lints green (SDK leak 0) / tsc 0 / FE lint clean / FE build ✓
- [x] progress.md (Day 0-4) + retrospective.md (this file)
- [x] CHANGE-034
- [x] Area-A capstone update (A-5a+ shipped; D2/D3 runtime-confirmed; A-5b/A-5c remain)
- [ ] commit (Day 3+4) + push + PR — user-authorized
- [ ] 🚧 real_llm live e2e — deferred (Azure secrets; blocker REMOVED this sprint)

---

(Filled per the Q1-Q7 + closeout structure mirrored from sprint-57-65/retrospective.md.)
