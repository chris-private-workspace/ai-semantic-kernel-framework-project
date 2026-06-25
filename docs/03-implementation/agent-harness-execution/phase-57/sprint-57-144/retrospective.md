# Sprint 57.144 Retrospective — Cat 2 tool-description lint + structured-error reflection

Closes research #7 `AD-Tool-Description-Lint-Reflection` (the LAST canonical research item). Base `main` `74555317`. Branch `feature/sprint-57-144-tool-desc-lint-reflection`.

## Q1 — Goal & outcome
**Goal**: ship Half A (tool-description lint, guardrail) + Half B (structured-error reflection, evidence-first env lever) with a real-Azure A/B verdict. **Achieved**: ✅ Half A lint (11th in run_all) + 40 real param-description fixes + Half B taxonomy/executor-enrich/loop-B2/lever + A/B harness; real-Azure A/B verdict = **KEEP lever OFF** (no material fix-rate lift on V2's strong model). Last canonical research item CLOSED.

## Q2 — Calibration
- Class **`tool-reflection-and-lint-spike` 0.60** (NEW, 1st data point); parent-direct `agent_factor` 1.0 → 3-segment.
- Bottom-up ~11.5 hr → committed ~6.9 hr (mult 0.60).
- Actual ≈ **~7-7.5 hr** (the +40-param scope expansion + the 3 flake8-E501 + black re-formats added ~1 hr over a clean spike; offset by the agent-delegated param fill ~0.5 hr saved). Ratio actual/committed ≈ **~1.05-1.1 IN band (upper edge)**.
- Verdict: KEEP 0.60 single-data-point. The real-code core (AST detector + pure taxonomy + executor refactor + loop B2 + ~250-line harness + corpus + 49 tests) held the 0.60 (57.137 lesson — a >3 hr real-implementation core holds the spike multiplier, NOT a tiny-code 0.85 re-point). The upper-edge came from the user-approved 40-param expansion, not ceremony. If a 2nd `tool-reflection-and-lint-spike` lands > 1.20, re-point toward 0.75.

## Q3 — What went well
- **Evidence-first paid off**: the A/B gave an honest KEEP-OFF verdict (87.5% == 87.5%) consistent with the eval's pre-stated RL-confound hedge — we did NOT default-on an unproven gain. Same disciplined shape as 57.136/138.
- **The lint found REAL gaps**: 40 missing param descriptions (the survey had hallucinated they existed) — the guardrail justified itself on day 1.
- **D-tool-message-field discovery**: surfaced a latent gap (handler-raised failures fed the LLM an EMPTY observation) → Half B's enrich both adds the reflection AND fixes the empty observation; gave the A/B a clean baseline.
- **Clean Day-0 三-prong**: Prong-1 all GREEN; D-loop-import-boundary caught the private-cross-category trap BEFORE coding (re-export via `tools/__init__.py`).
- **End-to-end Half B proof**: the `_RecordingFakeChatClient` integration test proves the LLM actually SEES the reflection through the real loop (drive-through ethos at the unit level).

## Q4 — What drifted / lessons
- **D1-placeholder-FP** (detector bug): IGNORECASE `\bTODO\b` false-positived on the word "todos" → fixed UPPERCASE-only + regression test. Code-aware-masking lesson (`lint-detector-authoring.md`).
- **D1-40-real-gaps** (scope, user-approved): the lint's param-level check surfaced 40 real gaps → scope expanded 11→18 files (re-confirmed with user per the 20-50% scope-shift rule).
- **Agent-flake8-miss** (NEW lesson, Before-Commit item 7 reinforcement): the delegated 40-param agent verified via `check_tool_descriptions` + `black --check` but NOT flake8 — 3 of its descriptions exceeded E501 (100). The parent re-verify (full flake8 src+tests) caught them. **Lesson: when delegating, the parent's independent gate MUST include flake8 E501, not just black + the feature-specific lint** — black does not break long string-literal lines, so a black-clean file can still fail E501.
- **D1-drop-allowlist** (YAGNI): the planned echo/note allow-list was unnecessary (both pass the bar) → dropped.

## Q5 — Anti-pattern self-check
- **AP-2** (side-track): ✅ both halves on the main flow (lint in run_all CI; taxonomy in the executor→loop→LLM path) — no orphan.
- **AP-3** (scattering): ✅ taxonomy in ONE pure module; one `_build_failure` builder (not duplicated across the 2 executor failure sites).
- **AP-4** (Potemkin): ✅ the lint passes on a CLEAN codebase (40 gaps fixed, not exempted); the A/B harness ran real Azure (not a stub).
- **AP-6** (future-proofing): ✅ `error_taxonomy` field has a live consumer (the executor/loop enrich); the lever has a current use (the A/B). No speculative abstraction.
- **AP-8** (PromptBuilder): N/A (no LLM prompt assembly changed).
- **AP-11** (version suffix): ✅ none.
- v2 lints: 11/11 (incl. the new check_tool_descriptions + llm_sdk_leak clean — the taxonomy is pure str, no SDK).

## Q6 — Carryover (Phase 58)
- `AD-Tool-Error-Reflection-Loop-RarePath-DriveThrough` (the rare path's ON behavior is composition-verified, not loop-integration-tested).
- `AD-Tool-Description-AutoFix-Phase58` (LLM-assisted description rewrite).
- `AD-Tool-Error-Taxonomy-UI-Phase58` (surface taxonomy in chat-v2 inspector).
- Reflection gain on weaker models / harder corpora (a future eval; the opt-in lever already lets a deployment enable it).
- Pre-existing: `AD-Billing-Outbox-Drain-Test-Flake` (Risk Class C — did NOT surface this sprint, full suite 2930 green).
- **#7 was the LAST canonical research item** → the Phase-58 carryover pool (DAG / scheduler / provider-attr / content-capture / metrics-labels / `AD-Loop-CancelEvent-Poll` / the above) is now the candidate set.

## Q7 — Design note 8-point gate (self-check)
File: `docs/03-implementation/agent-harness-planning/48-tool-error-reflection-design.md` · verified ratio ≥ 95%.
- [x] 1. Section headers map to US (US-1..US-4).
- [x] 2. Every claim has file:line.
- [x] 3. Decision matrix (5 decisions + chosen + rejected reasons).
- [x] 4. Verification commands (pytest + the real-Azure reproduce).
- [x] 5. Test fixtures referenced (corpus yaml + inline tmp_path).
- [x] 6. Open invariants demarcated (§4 deferred to Phase 58).
- [x] 7. Rollback path (§5, ~1 hr, lever-OFF sentinel in place).
- [x] 8. 17.md cross-ref (§3 — no new contract; ToolResult optional field, ABCs unchanged).
- **Self-review pass**: yes.
