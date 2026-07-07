# Sprint 57.160 Retrospective — tool-anchored observation masking + reduction/retention A/B

**Closed**: 2026-07-07 · Branch `feature/sprint-57-160-compaction-tool-anchored-masking` from `main` `29da11e8` · Cat 4 (Context Mgmt) · engine-debt compaction range.

## Q1 — What shipped?

An env-gated **tool-result-recency** anchor mode on `DefaultObservationMasker` (`CHAT_COMPACTION_TOOL_ANCHORED_MASKING`, default OFF → byte-identical) that makes structural + preclear compaction actually reduce WITHIN a single-user-turn tool run — the fix for `AD-Compaction-NoOp-On-Single-User-Turn-Chat-Path` (57.159). Rolled out evidence-first (env lever + deterministic A/B harness — AskUserQuestion pick "B"). Backend-only, ZERO wire/codegen/frontend/migration (the 57.159 marker already renders). CHANGE-127 + design note 62.

## Q2 — Calibration

- **Class**: NEW `compaction-tool-anchored-masking-spike` **0.60** (1st data point). Anchored to `layered-compaction-spike` 0.60 (57.139) / `verification-context-hygiene-spike` 0.60 (57.136) — same Cat-4 evidence-first shape (bounded masker-mode change + env lever + deterministic A/B harness + real-code core).
- **Agent-delegated: no** (parent-direct; agent_factor 1.0 → 3-segment).
- Bottom-up ~5.5-6 hr → committed ~3.5 hr (×0.60) → **actual ~5 hr → ratio ~0.83-0.9 vs committed / ~1.0 vs the 3-sprint band** — IN band. The wall-clock driver was NOT the code (masker mode + factory + harness + 28 tests were on-budget ~3.5 hr) but the **Day-3 drive-through discovery loop**: 3 backend restarts + 2 dead-end legs (keep=3 then keep=1 both showed `N→N` before the Structural-blindness root cause was found) + the pivot to knowledge_search + preclear. KEEP 0.60 (1st data point); if a 2nd `compaction-tool-anchored-masking-spike` lands > 1.2 (drive-through-discovery-dominated) re-point toward 0.75.

## Q3 — What went well?

- **Day-0 三-prong 0-drift**: all 5 D-items GREEN (masker had no ctor / ABC declares only `mask_old_results` / both compactors take `masker=` / tool-msg shape / harness guards) → the additive design landed exactly as planned; scope shift ~0%.
- **Instance-config over call-kwarg**: making the tool-anchor a masker property let the factory inject one masker into both compactors with zero compactor-signature / call-site threading change.
- **A/B harness verdict was decisive + deterministic**: off 0.00% / on 60.83% / retention 100% / recommend True — no LLM run-to-run noise (unlike 57.154), so a single run sufficed.
- **Drive-through found a real, non-obvious runtime truth** (Q4).

## Q4 — What was hard / surprising?

- **The Structural message-count-ratio blindness** (the KEY finding). Legs 1-2 showed `N→N · 0 msgs` even at `keep=1` — the tool-anchored masking WAS tombstoning real context, but `StructuralCompactor.tokens_after = tokens_before × len(kept)/original` (`structural.py:192-193`) is blind to in-place tombstoning (masking preserves list length). Only `PreClearCompactor`'s real `TiktokenCounter` re-count surfaces it. This is exactly the limitation 57.139's `preclear.py:19-22` documented — the drive-through connected the two. The fix works; surfacing it in the marker needs preclear too. → carryover `AD-Compaction-Structural-RealTokenCount`.
- **Getting ≥2 tool results + ≥2 compaction events in one send was the real obstacle** — gpt-5.2 finished python-heavy prompts in ~2 turns. The pivot to **knowledge_search × 6 topics** (each topic REQUIRES a separate call — the model can't batch) reliably produced 6 tool round-trips.

## Q5 — Anti-pattern self-check

- AP-2 (side-track): ✅ N/A — the masker mode is on the main compaction path; the harness is importable + CI-tested.
- AP-4 (Potemkin): ✅ the marker renders REAL wire data (drive-through proved the reduction is real, not a dead control); the harness measures real token counts.
- AP-6 (future-proofing): ✅ env lever has a concrete drive-through use case + A/B evidence; no speculative abstraction.
- AP-7 (context rot): ✅ this IS the context-rot mitigation being made effective on the single-user-turn path.
- AP-8/11: ✅ N/A (no PromptBuilder change / no version suffix).
- v2 lints: **11/11**.

## Q6 — Design Note Extract (spike sprint)

**File**: `docs/03-implementation/agent-harness-planning/62-tool-anchored-masking-design.md`
**Verified ratio (estimated)**: ≥ 95% (every claim carries a file:line + a pytest/harness/drive-through verification).
**8-Point Quality Gate**:
- [x] 1. Section headers map to US-1..US-5 + the KEY finding
- [x] 2. file:line on every claim (`observation_masker.py`, `_category_factories.py`, `structural.py:192-193`, `preclear.py`)
- [x] 3. Decision matrix (rollout A vs B)
- [x] 4. Verification command (pytest + harness invocation)
- [x] 5. Test fixture reference (`tool_anchored_masking_cases.yaml` + inline builders)
- [x] 6. Open-invariant boundary (§4 deferred list vs §2 verified)
- [x] 7. Rollback path (env-OFF sentinel + 2-file revert ~0.5 hr)
- [x] 8. 17.md cross-ref (no new contract → no 17.md edit; explicitly stated)

**Reviewer pass**: self-review.

## Q7 — Carryover

- **NEW `AD-Compaction-Structural-RealTokenCount`** — upgrade `StructuralCompactor.tokens_after` to a real `TiktokenCounter` re-count so tool-anchored masking surfaces WITHOUT also enabling preclear.
- `AD-Compaction-ToolAnchored-Preclear-Phase58` (57.139) — mechanism half CLOSED (tool-anchored masking makes preclear effective on single-user-turn); the default-on-preclear decision remains open.
- Flip `CHAT_COMPACTION_TOOL_ANCHORED_MASKING` default ON — data-gated follow-on (A/B recommends; wants a real-traffic retention observation first).
- Per-tenant tool-anchor policy · behavioural-retention-under-real-traffic study.
- Still open (compaction range): `AD-Compaction-Marker-Inspector-Trace-Correlate` (57.159, FE) · `AD-Compaction-Preclear-PerTenant-Phase58`.
