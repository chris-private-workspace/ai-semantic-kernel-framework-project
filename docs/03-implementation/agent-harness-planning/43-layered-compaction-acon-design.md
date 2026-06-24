---
title: 43-layered-compaction-acon design note
purpose: Spike-extract design note from Sprint 57.139; documents verified runtime invariants for the ACON tool-result preclear layer + per-layer compaction yield
category: V2 extension docs (post-22-sprint era)
created: 2026-06-24 (Sprint 57.139 Day 4 closeout)
sprint_source: 57.139
verified_ratio: ≥ 95% (per 8-Point Quality Gate)
status: Active
---

# 43-layered-compaction-acon Design Note (Sprint 57.139 extract)

## 0. Spike Summary

- **Sprint scope** (closes `AD-Context-Layered-Compaction-ACON`, research #4; Cat 4): US-1 standalone LLM-free tool-result preclear layer · US-2 per-layer yield measurement harness · US-3 selectable env opt-in (default OFF, byte-identical) · US-4 drive-through · US-5 closeout.
- **Verified period**: 2026-06-24.
- **Calibration**: bottom-up ~12 hr → committed ~7.2 hr (NEW class `layered-compaction-spike` 0.60) → actual ~7 hr → ratio ~0.97 IN band (parent-direct, agent_factor 1.0).
- **Verification**: pytest +28 (8 preclear + 7 chained + 13 harness) · real-Azure A/B (6 cases) · chat-v2 drive-through (3+1 real-LLM turns).
- **The "different axis from C2 (57.109)"**: C2 made the semantic SUMMARIZER cheap (cheaper model, same single trigger). #4 makes the FREE tool-clear layer run EARLIER so the expensive semantic call is DEFERRED/avoided. Orthogonal — both shipped, both default-tuned by evidence.

## 1. Decision Matrix

| Decision | Option chosen | Alternatives rejected (reason) |
|----------|---------------|-------------------------------|
| Preclear masking logic | **Reuse `DefaultObservationMasker.mask_old_results`** | New tool-anchored masker (NEW logic, scope creep — deferred to Phase 58); fold into structural (muddies single responsibility, AP-3) |
| Compose into the loop | **`ChainedCompactor` (preclear→hybrid)** | Add preclear param INTO `HybridCompactor` (muddies its responsibility); edit `loop.py` to call 2 compactors (the loop's single call site stays clean) |
| `tokens_after` for preclear | **Real token-reduction ratio `int(tokens_before × masked/original)` via injected `TokenCounter`** | Structural's message-count ratio (`structural.py:192-193` — blind to in-place tombstoning → would report ~0 reduction); raw `counter.count(masked)` (scale-mismatch with the loop's `tokens_before` → false token spike, would misfire the chained hybrid) |
| `strategy_used` for preclear | **Reuse `CompactionStrategy.STRUCTURAL`** | New `PRECLEAR` enum value (ripples to `event_wire_schema.py` + codegen — D-compaction-strategy-wire) |
| Default state | **OFF (`CHAT_COMPACTION_PRECLEAR_RATIO` unset → bare `HybridCompactor`)** | Default ON (the win is composition-dependent + user-anchored NO-OP single-send → not a safe default flip; evidence-first like #136/#138) |
| Per-tenant config | **Out (env-only this spike)** | Per-tenant preclear (AP-6 speculative; → Phase 58 if demanded) |

## 2. Verified Invariants

### 2.1 PreClearCompactor masks tool results at a lower trigger, LLM-free
- **Implementation**: `backend/src/agent_harness/context_mgmt/compactor/preclear.py:80-200` — `should_compact` at `token_usage_so_far > preclear_ratio × token_budget` (default 0.50); `compact_if_needed` separates system+HITL, runs `masker.mask_old_results`, honest passthrough when 0 tombstoned.
- **Behavior**: reclaims context by tombstoning old `role="tool"` bodies WITHOUT any LLM call; `strategy_used=STRUCTURAL`.
- **Verification**: `pytest tests/unit/agent_harness/context_mgmt/test_compactor_preclear.py` (8 passed).
- **Test fixture**: in-test `_LenCounter` + `_tool_transcript` builder.

### 2.2 tokens_after reflects the REAL masking reduction (loop-scale)
- **Implementation**: `preclear.py:178-189` — `reduction_ratio = tokens_masked / tokens_original; tokens_after = int(tokens_before × reduction_ratio)`.
- **Behavior**: keeps `tokens_after` in the loop's token scale (so `loop.py:2234 tokens_used = result.tokens_after` and the chained hybrid's `should_compact` compare apples-to-apples) while honestly reflecting the tombstone reduction — fixing structural's message-count-ratio blindness for the masking-only case.
- **Verification**: `pytest ...test_compactor_preclear.py::test_tokens_after_reflects_real_reduction_ratio`.

### 2.3 ChainedCompactor threads state so the cheap layer defers semantic
- **Implementation**: `backend/src/agent_harness/context_mgmt/compactor/chained.py:71-123` — runs children in sequence, `current_state = result.compacted_state`, merges `messages_compacted`, carries C2 usage; `loop.py` UNTOUCHED (single `compact_if_needed` call site `loop.py:2221`).
- **Behavior**: the 2nd child (hybrid) sees the preclear-reduced `token_usage_so_far` via `should_compact` → may skip its semantic stage.
- **Verification**: `pytest tests/unit/agent_harness/context_mgmt/test_compactor_chained.py::test_threads_state_to_next_child` (7 passed total).

### 2.4 Default path is byte-identical (factory returns bare hybrid when OFF)
- **Implementation**: `backend/src/api/v1/chat/_category_factories.py:_compaction_preclear_ratio()` + `make_chat_compactor` branch — ratio>0 → `ChainedCompactor([PreClearCompactor(TiktokenCounter(gpt-4o)), hybrid])`; unset/0/invalid → bare `HybridCompactor`.
- **Verification**: `pytest tests/unit/api/test_category_factories.py` (22 passed, unchanged) + drive-through ARM B.

### 2.5 Per-layer yield (the research #4 measurement)
- **Implementation**: `backend/scripts/benchmark_layered_compaction.py` — L0/L1/L2 (LLM-free) + L3 (`RUN_AZURE_INTEGRATION`).
- **Behavior (real Azure, 6 cases)**: mean tool_clear_reduction **33.72% → IN ACON band [26-54%]**; mean semantic_reduction 40.65% (tool-clear captures ~83% of total yield for free); semantic_deferred_rate 66.67%; preclear_recommended True. Per-case spread 0% (single-turn NO-OP) → 64% (very tool-heavy) → 11% (prose-heavy) — composition-dependent.
- **Verification**: `RUN_AZURE_INTEGRATION=1 AZURE_OPENAI_*=... python scripts/benchmark_layered_compaction.py` → `sprint-57-139/artifacts/layered_compaction_report.{md,json}`. CI-safe core: `pytest tests/unit/scripts/test_benchmark_layered_compaction.py` (13 passed).
- **Test fixture**: `backend/tests/fixtures/context_mgmt/layered_compaction_cases.yaml` (6 specs).

### 2.6 Drive-through (chat-v2, real Azure gpt-5.2)
- **Behavior**: ARM A (preclear ON, `ChainedCompactor` active) → 3 turns (TCP/TLS/QUIC) no-regression; ARM B (default OFF, bare hybrid) → "Tokyo" byte-identical. Honest 兩者結合: CATCH = the harness; UI = no-regression + chain wiring (masking NOT UI-triggerable on plain tool-less chat).
- **Verification**: screenshots `sprint-57-139/artifacts/dt-57139-preclear-on-no-regression.jpeg` + `dt-57139-default-off-unchanged.jpeg`; progress.md Day 3.

## 3. Cross-Category Contracts

**No new contract.** `PreClearCompactor` + `ChainedCompactor` are new concrete impls of the EXISTING `Compactor` ABC (`compactor/_abc.py`); `CompactionResult` + `CompactionStrategy` (`_contracts/compaction.py`) are UNCHANGED (preclear reuses `STRUCTURAL`). No new ABC method, no new wire event → nothing to register in `17-cross-category-interfaces.md` (§2.1 Compactor row already covers the ABC). N/A justified.

## 4. Open Invariants (deferred)

- [ ] **Tool-anchored preclear** (`AD-Compaction-ToolAnchored-Preclear-Phase58`): the masker is USER-anchored (`observation_masker.py:62-66`) so it NO-OPs single-send chat (1 user turn); a clear keyed on `tool_use_id` (CC microcompact style) would cover single-send. NOT verified this spike.
- [ ] **Per-tenant preclear ratio** (`AD-Compaction-Preclear-PerTenant-Phase58`, C3 seam): env-only this spike.
- [ ] **Larger / real-traffic corpus**: the 33.72%-in-band mean is from a 6-case synthetic corpus chosen to span the spectrum; real tool-result size distributions may shift the mean. NOT a real-traffic claim.
- [ ] **Default flip to ON**: only if a larger corpus proves a strong, low-risk, composition-independent win.

## 5. Rollback / Fallback

- **If preclear proves wrong**: the default is already OFF (`CHAT_COMPACTION_PRECLEAR_RATIO` unset → bare `HybridCompactor`) — a deployment simply does not set the env. To fully revert: delete `compactor/preclear.py` + `compactor/chained.py` + the `make_chat_compactor` branch (3 files) + tests + harness. Est ~1 hr. `loop.py` / `observation_masker.py` / the other compactors were never touched → zero blast radius on the default path.
- **Sentinel already in place**: yes — the factory's `ratio>0` guard means an unset/invalid env is the bare-hybrid path; the chain only exists when explicitly enabled.

## 6. References

- Sprint plan: `phase-57-frontend-saas/sprint-57-139-plan.md`
- Sprint retrospective: `agent-harness-execution/phase-57/sprint-57-139/retrospective.md`
- CHANGE: `claudedocs/4-changes/feature-changes/CHANGE-106-layered-compaction-acon.md`
- Related: `17-cross-category-interfaces.md` §2.1 (Compactor row, unchanged) · `04-anti-patterns.md` AP-7 (Context Rot) · CC ladder analysis `claudedocs/5-status/cc-long-running-loop-source-analysis-20260619.md` §3 (5-layer ladder reference)
- Predecessor spikes: `40-verification-correction-hygiene-design.md` (57.136) · `41-sandbox-detect-to-restrict-design.md` (57.137) · `42-verification-key-condition-design.md` (57.138) — same evidence-first harness+lever shape

## Modification History
- 2026-06-24: Initial extract from Sprint 57.139 closeout (Day 4)
