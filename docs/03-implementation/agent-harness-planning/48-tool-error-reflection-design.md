---
title: 48-tool-error-reflection design note
purpose: Spike-extract design note from Sprint 57.144; documents verified runtime invariants for Cat 2 tool-description lint + structured-error reflection (research #7)
category: V2 extension docs (post-22-sprint era)
created: 2026-06-25 (Sprint 57.144 Day 4 closeout)
sprint_source: 57.144
verified_ratio: ≥ 95% (per 8-Point Quality Gate)
status: Active
---

# 48-tool-error-reflection Design Note (Sprint 57.144 extract)

Closes research #7 `AD-Tool-Description-Lint-Reflection` (the LAST canonical research item; #6/#3/#8/#4/#1/#2/#5 all CLOSED). Two orthogonal halves: **A** a tool-description lint (guardrail), **B** structured-error reflection (evidence-first, default OFF after an A/B verdict).

## 0. Spike Summary

- **Sprint scope** (US): US-1 lint detector / US-2 taxonomy + executor enrich / US-3 loop B2 full coverage / US-4 A/B evidence + lever / US-5 verdict + closeout.
- **Verified period**: 2026-06-25.
- **Calibration**: bottom-up ~11.5 hr → committed ~6.9 hr (class `tool-reflection-and-lint-spike` 0.60, parent-direct `agent_factor` 1.0). Actual ≈ in band (retro Q2).
- **Verification**: pytest +49 (10 lint + 19 taxonomy + 5 executor + 2 loop-integration + 13 A/B harness) → 2930 +5skip; mypy src 382; run_all 11/11; real-Azure A/B (32 calls).

## 1. Decision Matrix

| Decision | Options | Chosen | Why / rejected |
|----------|---------|--------|----------------|
| Half A location | (D1) CI lint detector / (D2) register-time validation | **D1** | Matches the existing 10-detector pattern; exempts nothing at runtime; register stays syntax-only. D2 rejected: would make every test-tool registration heavier + mixes "lint=quality / register=syntax"分工. |
| Half B coverage | (B1) pure Cat 2, rare path deferred / (B2) full incl. loop.py refactor | **B2** (user pick) | Both the dominant (executor) AND the rare (executor-itself-raises, `loop.py:3023`) failure paths route through ONE taxonomy → no residual path. |
| Half B default | (C1) env lever, verdict-driven / (C2) default-on | **C1** | Evidence-first: the A/B verdict decides. C2 rejected: §2.4's BFCL gains carry an RL-training confound — assuming they hold for V2's prompt-only model was untested. |
| Lever read site | factory-inject / in-module env read | **in-module** (`_error_taxonomy.tool_error_reflection_enabled`) | Spike-lean (the A/B harness, not the live lever, is the deliverable); precedent = `sandbox.py` `DOCKER_SANDBOX_IMAGE`. Per-call read (Risk Class C). |
| 40 missing param descs | fix all / defer business_domain / tool-level only | **fix all** (user pick) | A lint that ships with 40 exempted violations is a Potemkin (AP-4); param descriptions also reduce `parameter`-class errors (Half B synergy). |

## 2. Verified Invariants

### 2.1 US-1 — tool-description lint catches real gaps + no false-positive
- **Implementation**: `scripts/lint/check_tool_descriptions.py` (AST `find_violations(root)`); wired 11th in `scripts/lint/run_all.py:85`.
- **Behavior**: flags missing/empty/`<20`-char/placeholder descriptions + any `input_schema` property without a description; skips dynamic (f-string/var) descriptions+schemas; UPPERCASE-only placeholder match (the lowercase word "todos" must pass).
- **Verification**: `python -m scripts.lint.check_tool_descriptions --root backend/src` → OK exit 0; `pytest tests/unit/scripts/lint/test_tool_descriptions.py` (10, incl. the lowercase-"todos" regression).
- **Test fixture**: inline tmp_path `ToolSpec(...)` literals in the test.

### 2.2 US-1 — 40 real param-description gaps filled
- **Implementation**: param `"description"` keys added to `tools/{memory_tools,todo_tools}.py` (9) + `business_domain/{audit_domain,correlation,incident,patrol,rootcause}/tools.py` (31), purely additive.
- **Verification**: `check_tool_descriptions --root backend/src` was 40 violations → 0; `git diff` purely additive (no key/type/enum/default change).

### 2.3 US-2 — taxonomy is pure + orthogonal to Cat 8
- **Implementation**: `tools/_error_taxonomy.py` — `classify_tool_error(*, error_class, error_msg, is_schema_error, is_unknown_tool)` (flags-first → exception-class markers → message heuristics → generic) + `render_reflection()`.
- **Behavior**: PARAMETER / WRONG_TOOL / FAILED_API / INVOCATION / UNKNOWN — answers "how to FIX", distinct from Cat 8 `ErrorClass` (`error_handling/_abc.py:30-36`) which answers "retry?".
- **Verification**: `pytest tests/unit/agent_harness/tools/test_error_taxonomy.py` (19).

### 2.4 US-2 — executor enrich reaches the LLM (lever ON), byte-identical (OFF)
- **Implementation**: `tools/executor.py:_build_failure` (one builder for the handler-exception path + `_fail`); writes `content` (the loop renders `content` via `loop.py:3092` `_tool_result_to_text`, never `error`) + `error_taxonomy` when `tool_error_reflection_enabled()`.
- **Behavior**: OFF → `content=""` + error/error_class only (pre-57.144 byte-identical); ON → typed reflection in `content` (also FIXES the prior empty-observation gap).
- **Verification**: `pytest tests/unit/agent_harness/tools/test_executor.py -k reflection` (5) + the end-to-end `test_loop_error_handling.py::test_structured_reflection_reaches_llm_when_lever_on` (a `_RecordingFakeChatClient` asserts the tool-role message the LLM receives carries "tool execution failed (external/API error)" on a ConnectionError ON; empty OFF).

### 2.5 US-3 — loop rare path (B2) shares the taxonomy
- **Implementation**: `loop.py:3023-3036` — the executor-itself-raises synthesis uses `render_reflection(classify_tool_error(...))` when the lever is on; byte-identical `"Error: …"` when off.
- **Verification**: covered by the OFF byte-identical existing error-path integration tests + the taxonomy unit tests (the synthesis reuses the same pure functions); import via the PUBLIC `agent_harness.tools` path (cross-category lint clean).

### 2.6 US-4 — A/B harness verdict (real Azure)
- **Implementation**: `scripts/benchmark_tool_error_reflection.py` (plain vs reflection observation; real cheap-tier judge); corpus `tests/fixtures/tools/tool_error_reflection_cases.yaml` (8 cases).
- **Verification (reproduce)**: `RUN_AZURE_INTEGRATION=1 AZURE_OPENAI_*=... python scripts/benchmark_tool_error_reflection.py` (real-LLM, ~32 calls; cost ≈ small). CI-safe: `pytest tests/unit/scripts/test_benchmark_tool_error_reflection.py` (13, fake clients).
- **Result**: fix_rate 87.5% plain == 87.5% reflection (Δ +0.00% < 5% materiality) → **verdict KEEP lever OFF**; reflection −32 completion tokens (secondary). Artifact: `agent-harness-execution/phase-57/sprint-57-144/artifacts/tool_error_reflection_report.{md,json}`.

## 3. Cross-Category Contracts

No NEW boundary contract. `ToolResult` (Cat 7 shared contract, `_contracts/tools.py`) gains an OPTIONAL `error_taxonomy: str | None` field (stores the enum `.value` — the contract takes NO dependency on `tools/_error_taxonomy`). The `ToolExecutor` / `ToolResult` ABCs (17.md §2.1) keep their signatures → no `17-cross-category-interfaces.md` change. `loop.py` (Cat 1) consumes the taxonomy via the PUBLIC `agent_harness.tools` package surface (re-exported in `tools/__init__.py`) — allowed by `check_cross_category_import`.

## 4. Open Invariants (deferred to Phase 58)

- [ ] `AD-Tool-Error-Reflection-Loop-RarePath-DriveThrough`: the rare executor-itself-raises path's ON behavior is verified by composition (taxonomy unit tests + the identical render call), NOT by a dedicated loop integration test (triggering it needs a non-ToolExecutorImpl raising executor + error_policy wiring not in the test helper). The DOMINANT path IS end-to-end tested (§2.4).
- [ ] `AD-Tool-Description-AutoFix-Phase58`: LLM-assisted rewrite of flawed descriptions (lint reports, doesn't fix).
- [ ] `AD-Tool-Error-Taxonomy-UI-Phase58`: surface `error_taxonomy` in a chat-v2 inspector.
- [ ] Reflection gain on WEAKER models / HARDER corpora: the A/B used V2's strong action tier + an 8-case corpus (87.5% plain baseline → little headroom). The §2.4 regime (weaker RL-trained models) may show a material lift; the opt-in lever lets such a deployment enable it. A larger / harder corpus is a future eval.

## 5. Rollback / Fallback

- **Half A**: revert `scripts/lint/check_tool_descriptions.py` + its `run_all.py` entry (the 40 param descriptions are harmless to keep). ~10 min.
- **Half B**: the `CHAT_TOOL_ERROR_REFLECTION` lever IS the fallback — default OFF = pre-57.144 behavior. To fully revert, drop `_build_failure`'s enrich branch + the `loop.py:3023` branch + the `ToolResult.error_taxonomy` field. ~30 min. Sentinel already in place (lever default OFF).
- Estimated total rollback: ~1 hr.

## 6. References

- Eval: `claudedocs/5-status/tool-description-lint-reflection-thin-spike-eval-20260625.md`
- Sprint plan: `phase-57-frontend-saas/sprint-57-144-plan.md` · checklist `sprint-57-144-checklist.md`
- Retrospective: `agent-harness-execution/phase-57/sprint-57-144/retrospective.md`
- CHANGE-111: `claudedocs/4-changes/feature-changes/CHANGE-111-tool-desc-lint-error-reflection.md`
- Research: `claudedocs/5-status/ai-agent-harness-consolidated-analysis-20260622.md` §2.3 / §2.4 / §5 #7
- Mirrored harness: `scripts/benchmark_correction_hygiene.py` (57.136)
- Rules: `.claude/rules/lint-detector-authoring.md` (code-aware masking)

## Modification History
- 2026-06-25: Initial extract from Sprint 57.144 closeout (Day 4)
