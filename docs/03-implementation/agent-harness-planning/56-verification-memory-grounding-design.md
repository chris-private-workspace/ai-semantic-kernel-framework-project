---
title: 56-verification-memory-grounding design note
purpose: Spike-extract design note from Sprint 57.153; documents verified runtime invariants for the memory-aware in-loop verification judge
category: V2 extension docs (post-22-sprint era)
created: 2026-07-01 (Sprint 57.153 Day 4 closeout)
sprint_source: 57.153
verified_ratio: ≥ 95% (per 8-Point Quality Gate)
status: Active
---

# 56-verification-memory-grounding Design Note (Sprint 57.153 extract)

## 0. Spike Summary

- **Sprint scope** (US-1..US-6): make the in-loop Cat 10 verification judge memory-aware so a recall
  grounded in injected memory is not false-positive-rejected as fabrication. Closes
  `AD-Verification-Judge-Memory-Inject-Blind` (logged 57.149 carryover, re-confirmed 57.152 Leg-2).
- **Verified period**: 2026-07-01.
- **Calibration**: bottom-up ~6 hr → committed ~3.6 hr (NEW class `verification-memory-grounding-spike`
  0.60) → actual ≈ on-budget (see retrospective Q2).
- **Verification**: pytest +38 (9 `build_memory_block` + 4 `{memory}` substitution + 3 gate-threading +
  13 CI-safe harness + handler-stub fixes) · real-Azure A/B (10 cases, 20 judge calls) · drive-through
  (real chat-v2 + real Azure gpt-5.2, 2 legs). NO Vitest/Playwright FE change (backend-only).

## 1. Decision Matrix (threading approach)

The judge needs the per-turn injected memory as grounding. How to get it from the loop to the judge?

| Approach | Files touched | ABC change? | Test-stub blast radius | Decision |
|----------|---------------|-------------|------------------------|----------|
| **A. `TransientState.injected_memory` field** | state.py (1 field) + gate sets it + judge reads it | NO | **0** (default-None; stubs ignore) | ✅ **CHOSEN** |
| B. `Verifier.verify(*, injected_memory=)` ABC kwarg | `_abc.py` + rules_based + llm_judge + ~13 test stubs | YES (17.md §2.1) | ~13 stubs must add the kwarg | ❌ wide blast radius for a clean signal |
| C. synthetic `[RETRIEVED MEMORY]` user-message in the trace | gate only | NO | 0 | ❌ semantically muddy (memory ≠ a conversation turn); the judge instruction frames `{trace}` as turns |

**Chosen A because**: the gate already constructs a fresh throwaway `trace_state` (it is NOT the
persisted loop state, so setting a field on it does not violate the Reducer-only-mutator rule — same as
how the gate already sets `messages`/`current_turn` on that snapshot). "What memory was injected this
turn" is a legitimate transient fact; carrying it where `messages` (the other judge input) already lives
touches 0 verifier impls and 0 test stubs. This is the direct parallel of 57.111 A3, which added `state`
threading + `build_trace_block` + `{trace}` — this sprint adds `injected_memory` + `build_memory_block` +
`{memory}`.

## 2. Verified Invariants

### 2.1 The injected memory is captured at the PromptBuilder build branch, not from `messages`

- **Implementation**: `loop.py` — `turn_injected_memory: list[Any] = []` initialized before the
  `if self._prompt_builder is not None:` branch; set from `artifact.layer_metadata.get("memory_accesses", [])`
  (the SAME source as the `MemoryAccessed` Inspector emit) inside the branch. The echo/naked-fallback path
  leaves it `[]`.
- **Behavior**: the memory injected into THIS turn's system prompt (57.148 `profile()` + 57.151
  `recent_sessions()`) is captured per-turn, refreshed each turn (so a correction `continue` re-captures).
- **Verification**: `pytest tests/unit/agent_harness/orchestrator_loop/test_loop_verification_gate.py -q`
  (`test_gate_threads_injected_memory_when_grounding_on` / `_omits_..._off` / `_no_injected_accesses_is_none`).
- **Test fixture**: `_CapturingVerifier` + `_ACCESS` literal in the test file.

### 2.2 `build_memory_block` renders a bounded PII-safe grounding block

- **Implementation**: `verification/_trace.py::build_memory_block(accesses, *, char_budget)` — renders
  `[memory:{scope}] {summary}` lines (`builder.py:397` `memory_accesses` = `{scope, time_scale, key, summary}`;
  `summary` is the MemoryHint's PII-safe capped summary, NOT raw content). Empty list / budget 0 / no
  non-empty summaries → `""`. Over budget → keep the highest-priority HEAD (top-k conf-ordered), drop the tail.
  Env: `CHAT_VERIFICATION_MEMORY_CHAR_BUDGET` (default 1500), per-entry cap 300.
- **Behavior**: a bounded, PII-safe grounding section the judge weighs alongside `{output}`+`{trace}`.
- **Verification**: `pytest tests/unit/agent_harness/verification/test_trace_block.py -k memory -q` (9 tests).

### 2.3 The judge substitutes `{memory}`; absent/None is byte-identical

- **Implementation**: `llm_judge.py::_build_prompt` — `.replace("{memory}", state.transient.injected_memory or "")`
  guarded on `state is None`. A template without `{memory}` is a byte-identical no-op (same property as `{trace}`).
  Only `output_quality.txt` + `key_condition.txt` carry the `{memory}` section + the grounding instruction
  ("consistent with retrieved memory = GROUNDED, not fabrication; still flag genuine contradictions").
- **Behavior**: the judge sees the agent's grounding; lever OFF / no memory → pre-57.153 prompt.
- **Verification**: `pytest tests/unit/agent_harness/verification/test_llm_judge.py -q`
  (`test_judge_substitutes_memory_block` / `_memory_placeholder_empty_when_none` /
  `_template_without_memory_placeholder_is_noop` / `_memory_noop_when_state_none`).

### 2.4 The flag gates the threading; default ON

- **Implementation**: `loop.py` ctor kwarg `verification_memory_grounding: bool = True` → `self._verification_memory_grounding`;
  the gate computes `build_memory_block(injected_accesses) if self._verification_memory_grounding else ""` and
  sets it on the trace_state. `core/config/__init__.py::chat_verification_memory_grounding: bool = True`
  (env `CHAT_VERIFICATION_MEMORY_GROUNDING`); `handler.py` passes it into the loop ctor (same site as
  `correction_context_strategy=`).
- **Behavior**: `=false` → `injected_memory=None` → judge prompt byte-identical to pre-57.153.
- **Verification**: the OFF-path gate test (2.1) + the handler-stub field add (`test_handler.py` SimpleNamespace).

### 2.5 A/B verdict: contradiction-catch is the deterministic measurable value (KEEP default ON)

- **Implementation**: `scripts/benchmark_memory_grounded_judge.py` runs the REAL production judge
  (`LLMJudgeVerifier` + `output_quality`, cheap tier) over a 10-case corpus (5 grounded-recall + 5
  contradiction) under two arms (memory_aware vs bare); verdict via a two-sided OR (ship if false-reject↓
  OR catch↑ materially, neither regresses).
- **Behavior** (real Azure, 20 judge calls): `grounded_recall_false_reject_rate` bare 0% → memory 0%;
  `fabrication_catch_rate` bare **0% → memory 100%** (+100pp) → **KEEP default ON**. Honest finding: a
  memory-blind `output_quality` judge is lenient enough to PASS grounded recalls in an isolated 1-turn
  corpus, so the "blind judge rejects a grounded recall" mode seen at 57.149/152 is driven by ACCUMULATED
  cross-session memory creating a CONTRADICTION — the fix's deterministic value is contradiction detection
  at zero false-reject cost.
- **Verification**: `RUN_AZURE_INTEGRATION=1 AZURE_OPENAI_*=... python scripts/benchmark_memory_grounded_judge.py`
  (real-Azure, ~20 cheap-tier calls); CI-safe: `pytest tests/unit/scripts/test_benchmark_memory_grounded_judge.py -q` (13).
- **Test fixture**: `tests/fixtures/verification/memory_grounded_judge_cases.yaml`; report
  `artifacts/ab-memory-grounded-judge-report.md`.

### 2.6 Drive-through: the grounded recall is delivered, not erased (STRONG PASS)

- **Implementation/Behavior**: real chat-v2 + real Azure gpt-5.2 (fresh backend PID 49236, memory-grounding
  default ON). Leg 1 (jamie) states "Dana Okafor / Verification Loops" → `memory_write` ×2 + verify 0.99.
  Leg 2 NEW session 0-keyword "你知道我是誰?我負責哪個範疇?" → the Loop trace shows the user-layer memory
  injected (the NEW Dana facts + the accumulated 57.148 `User name is Chris.` facts = a CONTRADICTION);
  the agent recalled both grounded facts + transparently flagged the conflict; the memory-aware in-loop
  judge **VerificationPassed score 0.98** — the grounded recall was DELIVERED, vs the pre-fix blind judge
  (57.152 Leg-2) that rejected→no-recall.
- **Verification (manual reproduce)**: dev-login jamie@acme.com on `/chat-v2` (real_llm) → state an identity
  → New session → ask a 0-keyword identity question → observe `VerificationPassed` + the grounded recall in
  the answer. Screenshots: `artifacts/sprint-57-153-leg{1,2}-*.png`.

## 3. Cross-Category Contracts

**No new cross-category contract.** This sprint extends two existing single-source types additively:

- `TransientState` (17.md §1.1, owner 範疇 7) — `injected_memory: str | None = None` (additive field;
  default-None keeps every existing construction byte-identical; no behavior change to the Reducer or
  durable state). NOT a new contract — an additive field on an existing one.
- `Verifier.verify` (17.md §2.1, owner 範疇 10) — **UNCHANGED** (the chosen design specifically avoids an
  ABC change; see §1).
- `{memory}` is a judge-template placeholder convention (sibling to `{trace}`), internal to 範疇 10, not a
  cross-category contract.

## 4. Open Invariants (deferred)

- [ ] **Per-tenant memory-grounding policy** → `AD-Verification-Memory-Grounding-PerTenant-Phase58` (C3
  config-tiering; this sprint is settings-only, mirroring the 57.111 A3 `{trace}` knobs staying module-level).
- [ ] **A chat-v2 Inspector surface / wire event for "the judge saw memory this turn"** →
  `AD-Verification-Memory-Grounding-Inspector-Phase58` (no wire-count change this sprint).
- [ ] **Semantic relevance ranking of which injected memories the judge sees** → CARRY-026 (semantic axis).
- [ ] **The accumulated cross-session identity-contradiction itself** (Dana+Chris on one user_id) is a
  memory-dedup/recency concern, NOT a judge concern → tracked under the memory-formation arc carryovers
  (`AD-Memory-User-Upsert-By-Key` was exact-normalized only; a semantic near-dup would need CARRY-026).

## 5. Rollback / Fallback

- **If this design proves wrong**: set `CHAT_VERIFICATION_MEMORY_GROUNDING=false` — one env var reverts the
  judge to the pre-57.153 memory-blind behavior (the gate threads `""` → `{memory}` empty → byte-identical
  prompt). No redeploy of code logic needed; estimated rollback effort: ~0 (env flip) to revert behavior,
  ~0.5 hr to remove the field + block if fully backing out.
- **Sentinel / fallback already in place**: yes — the default-None field + the flag + the empty-block no-op
  mean every off / no-memory / naked-fallback path is byte-identical to pre-57.153. The `Verifier.verify`
  ABC is untouched, so no verifier impl can break.

## 6. References

- Sprint plan: `phase-57-frontend-saas/sprint-57-153-plan.md`
- Sprint checklist: `phase-57-frontend-saas/sprint-57-153-checklist.md`
- Sprint progress + retrospective: `agent-harness-execution/phase-57/sprint-57-153/`
- Change record: `claudedocs/4-changes/feature-changes/CHANGE-120-verification-memory-grounding.md`
- Related contracts: `17-cross-category-interfaces.md` §1.1 (TransientState) / §2.1 (Verifier ABC, unchanged)
- Predecessor: 57.111 A3 (`{trace}` — the mechanism this parallels) · 57.98 A1 (in-loop gate) ·
  57.136 (`correction_context_strategy` — the env-lever pattern mirrored)

## Modification History

- 2026-07-01: Initial extract from Sprint 57.153 closeout (Day 4)
