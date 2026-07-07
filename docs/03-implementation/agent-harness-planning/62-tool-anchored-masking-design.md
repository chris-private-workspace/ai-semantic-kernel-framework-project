---
title: 62-tool-anchored-masking design note
purpose: Spike-extract design note from Sprint 57.160; documents verified runtime invariants for tool-result-recency observation masking (Cat 4)
category: V2 extension docs (post-22-sprint era)
created: 2026-07-07 (Sprint 57.160 Day 4 closeout)
sprint_source: 57.160
verified_ratio: ≥ 95% (per 8-Point Quality Gate)
status: Active
---

# 62-tool-anchored-masking Design Note (Sprint 57.160 extract)

## 0. Spike Summary

- **Sprint scope** (US-1..US-5): add an env-gated tool-result-recency anchor mode to `DefaultObservationMasker` so compaction reduces WITHIN a single-user-turn tool run (the chat main flow's shape); roll out evidence-first (lever default OFF + A/B harness); drive-through the real reduction on chat-v2.
- **AD closed**: `AD-Compaction-NoOp-On-Single-User-Turn-Chat-Path` (57.159 carryover). Advances `AD-Compaction-ToolAnchored-Preclear-Phase58` (57.139 deferred — same root fix).
- **Verified period**: 2026-07-07.
- **Calibration**: bottom-up ~5.5-6 hr → committed ~3.5 hr (class `compaction-tool-anchored-masking-spike` 0.60, parent-direct agent_factor 1.0) → actual ~5 hr → ratio ~1.0 IN band (the Leg-1/2 drive-through discovery loop was the wall-clock driver, not the code).
- **Verification**: pytest +28 (5 masker + 10 factory + 13 harness) · A/B harness verdict `recommend_default_on: True` · drive-through PASS (real reductions −42%/−51%).

## 1. Decision Matrix (rollout posture — user AskUserQuestion pick)

| Option | Default behaviour | Evidence path | Cost | Decision |
|--------|-------------------|---------------|------|----------|
| A: default-on correctness fix | chat path reduces by default; changes masker default + existing tests | drive-through only | lower ceremony, higher blast radius | **rejected** — behaviour change without a measured retention floor |
| **B: env-gated + A/B harness** ✅ | default OFF (byte-identical); opt-in `CHAT_COMPACTION_TOOL_ANCHORED_MASKING` | deterministic A/B harness + drive-through | matches 57.136-144 evidence-first discipline | **CHOSEN** (user pick) — measure reduction% + retention, flip decided by data |

Why B: the reduction is mechanically certain (tombstoning old tool blobs always reduces tokens), but the DEFAULT-change blast radius (over-tombstoning a working-set tool result mid-run) warranted a measured retention floor before any flip. B keeps the existing 6 masker tests + all deployments byte-identical while producing the evidence.

## 2. Verified Invariants

### 2.1 Tool-anchored masking reduces within a single user turn (US-1)
- **Implementation**: `backend/src/agent_harness/context_mgmt/observation_masker.py:_mask_tool_anchored` — `tool_idx = [i for i,m … if m.role=="tool"]`; `len(tool_idx) <= keep` → passthrough; else `cutoff = tool_idx[-keep]`; tombstone every `role=="tool"` at index `< cutoff` via `_tombstone` (shared with the user-anchored path).
- **Behavior**: keeps the last N tool results intact, tombstones older tool bodies, independent of user-turn count; `tool_anchor_keep=None` → the original user-anchored path (byte-identical).
- **Verification**: `pytest tests/unit/agent_harness/context_mgmt/test_observation_masker.py -q` (11 passed: 6 original UNCHANGED + 5 new incl. `test_tool_anchored_single_turn_reduces` + `test_default_none_is_user_anchored_noop_on_single_turn`).
- **Test fixture**: inline `_build_single_user_turn(num_tools)` (1 user + N×(assistant tool_call, tool result)).

### 2.2 Env lever injects the masker into both compactors; default OFF is byte-identical (US-2)
- **Implementation**: `backend/src/api/v1/chat/_category_factories.py:_compaction_tool_anchored_keep()` (reads `CHAT_COMPACTION_TOOL_ANCHORED_MASKING`; `>=1`→N else None) + `make_chat_compactor` injects `DefaultObservationMasker(tool_anchor_keep=N)` into `StructuralCompactor(masker=)` AND `PreClearCompactor(masker=)`; None → `masker=None` → the compactors default to a user-anchored `DefaultObservationMasker()`.
- **Behavior**: unset/invalid/0/negative → OFF (byte-identical pre-57.160); `>=1` → both stages tool-anchor.
- **Verification**: `pytest tests/unit/api/test_category_factories.py -q` (incl. `test_factory_default_masker_is_user_anchored` + `test_factory_injects_tool_anchored_masker_into_structural` + `_into_preclear`).

### 2.3 A/B: off no-op vs on material reduction, 100% mechanical retention (US-3)
- **Implementation**: `backend/scripts/benchmark_tool_anchored_masking.py` — `measure_case` runs OFF (`DefaultObservationMasker()`) vs ON (`tool_anchor_keep=N`) over single-user-turn corpora with a real `TiktokenCounter`; `_mechanical_retention_ok` asserts the last N tool results survive byte-intact + all `tool_calls` provenance + non-tool content untouched.
- **Verdict** (8 cases): mean off_reduction **0.00%**, mean on_reduction **60.83%**, retention_ok_rate **100%**, `recommend_default_on` **True**.
- **Verification**: `python backend/scripts/benchmark_tool_anchored_masking.py` (writes `benchmark_reports/tool_anchored_masking_report.md`) + `pytest tests/unit/scripts/test_benchmark_tool_anchored_masking.py -q` (13 CI-safe).
- **Test fixture**: `backend/tests/fixtures/context_mgmt/tool_anchored_masking_cases.yaml` (8 cases incl. `keep-covers-all` boundary + `long-single-send` 20-round).
- **Report artifact**: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-160/artifacts/tool_anchored_masking_report.{md,json}`.

### 2.4 Drive-through: real reduction rendered LIVE on the default single-user-turn path (US-4)
- **Behavior**: real chat-v2 + Azure gpt-5.2 + 6× knowledge_search in ONE user turn (`CHAT_COMPACTION_TOOL_ANCHORED_MASKING=1` + `CHAT_COMPACTION_PRECLEAR_RATIO=0.5` + budget 2500) → the 57.159 `CompactionMarker` renders `13,615 → 7,933 (−42%)` and `16,199 → 7,984 (−51%)`; context bounded ~8-9k vs 57.159's unbounded 4k→35k; `BOREALIS-9` + all 6 topics retained through compaction.
- **Verification**: manual drive-through (Playwright-driven); screenshot `artifacts/sprint-57-160-leg3-compaction-real-reduction.png` + full observed-vs-intended in `sprint-57-160/progress.md` Day 3.

### 2.5 KEY runtime finding — Structural's tokens_after is blind to in-place tombstoning
- **Implementation anchor**: `backend/src/agent_harness/context_mgmt/compactor/structural.py:192-193` — `token_usage_so_far = int(tokens_before * len(kept_messages) / max(original_count, 1))` + `messages_compacted = original_count - len(kept_messages)`.
- **Behavior**: masking tombstones tool BODIES in place (list length preserved) → `len(kept)==original` → the Hybrid→Structural path reports `tokens_after==tokens_before` and `messages_compacted=0` EVEN WHEN real tokens dropped. Only `PreClearCompactor` (`preclear.py:178-181`, real `TiktokenCounter` re-count) surfaces the reduction. So the tool-anchored masking is what makes `PreClearCompactor` EFFECTIVE on the single-user-turn path — the mechanism half of `AD-Compaction-ToolAnchored-Preclear-Phase58`.
- **Verification**: drive-through Legs 1-2 (tool-anchored alone → marker `N→N`) vs Leg 3 (tool-anchored + preclear → real reduction). Code-confirmed at `structural.py:192-193` vs `preclear.py:178-181`.

## 3. Cross-Category Contracts

No new contract / ABC. `ObservationMasker` ABC (`context_mgmt/_abc.py:57-80`) is unchanged — the tool-anchor mode is an instance-config property of the concrete `DefaultObservationMasker` (impl detail), not an ABC signature change. `17-cross-category-interfaces.md §2.1` (Compactor / ObservationMasker rows) needs no edit.

## 4. Open Invariants (deferred)

- [ ] **Flip `CHAT_COMPACTION_TOOL_ANCHORED_MASKING` default ON** — data-gated; the A/B recommends it, but a real-traffic retention observation should precede the default flip (new AD if pursued).
- [ ] **`AD-Compaction-Structural-RealTokenCount`** (NEW) — upgrade `StructuralCompactor.tokens_after` to a real `TiktokenCounter` re-count (like `PreClearCompactor`) so tool-anchored masking surfaces in the marker WITHOUT also enabling preclear.
- [ ] **Per-tenant tool-anchor policy** — mirror the per-tenant model/config pattern (global env lever only today).
- [ ] **Tool-anchored PreClear default-on** (`AD-Compaction-Preclear-PerTenant-Phase58`) — separate lever.
- [ ] **Behavioural retention under real traffic** — this spike's retention is mechanical (deterministic) + one drive-through; a real-traffic study is deferred.

## 5. Rollback / Fallback

- **Sentinel already in place**: the env lever defaults OFF → any deployment is byte-identical to pre-57.160 with zero action. Disabling = unset `CHAT_COMPACTION_TOOL_ANCHORED_MASKING`.
- **If the mode proves wrong**: revert `observation_masker.py` (`__init__` + `_mask_tool_anchored`) + the `_category_factories.py` injection (2 EDIT files); estimated ~0.5 hr. The harness + tests are additive (no revert needed).
- **Blast radius**: OFF by default, so a revert affects only deployments that opted in.

## 6. References

- Sprint plan: `phase-57-frontend-saas/sprint-57-160-plan.md`
- Sprint retrospective: `agent-harness-execution/phase-57/sprint-57-160/retrospective.md`
- CHANGE record: `claudedocs/4-changes/feature-changes/CHANGE-127-tool-anchored-observation-masking.md`
- Related: `preclear.py:19-35` (57.139 documented the exact limitation this fixes) · `62`↔`AD-Compaction-ToolAnchored-Preclear-Phase58` · `.claude/rules/sprint-workflow.md §Scope-class matrix` (`compaction-tool-anchored-masking-spike` 0.60)
- 04-anti-patterns.md AP-7 (Context Rot Ignored — the root motivation for the masker)

## Modification History

- 2026-07-07: Initial extract from Sprint 57.160 closeout (Day 4)
