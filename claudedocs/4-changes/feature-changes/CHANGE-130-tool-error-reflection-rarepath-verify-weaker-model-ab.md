# CHANGE-130: Tool-error reflection rare-path verify + weaker-model A/B (tier-dependent finding)

**Date**: 2026-07-09
**Sprint**: 57.163
**Scope**: 範疇 2 (Tool Layer) — evidence slice; backend + scripts only (NO migration / wire / codegen / frontend / loop.py-logic change)

## Problem

Two Sprint 57.144 (research #7 Half B, structured-error reflection) carryovers were left un-verified:
- **③1 `AD-Tool-Error-Reflection-Loop-RarePath-DriveThrough`**: reflection has two consumers — the dominant `executor._build_failure` (handler-exception / schema / unknown-tool) AND the rare `loop.py:3068` path where the **executor itself raises**. Only the dominant path was exercised end-to-end; the rare path was unit-covered but never driven.
- **③4 reflection weaker-model re-check**: the 57.144 A/B measured `fix_delta +0.00%` on the STRONG (action-tier) model → lever kept OFF. §2.4 hedged that a weaker model might have headroom, but the harness hardcoded the answerer so it was never tested.

## Root Cause

- ③1: never followed up after 57.144 shipped (the rare path is defensive full-coverage).
- ③4: `benchmark_tool_error_reflection.py::_amain` hardcoded `answerer=profile.action`; no CLI knob to swap in the weaker tier.
- **Day-0 discovery (D-executor-self-raise)**: `executor.execute()` is designed to turn EVERY failure into a `ToolResult` (handler exc → `:230` catch → `_build_failure`; unknown/schema → `_fail`; rate-limit → terminal `ToolResult`), so it does NOT self-raise on the 主流量. The `loop.py:3068` rare branch is therefore near-unreachable in production (fires only on an executor-INFRASTRUCTURE raise — the loop's own TOOL_EXEC tracer span, or a gate backend raising non-fail-open). A real chat-v2 drive-through cannot honestly stage a near-dead branch.

## Solution

Re-scoped ③1 (user AskUserQuestion 方案 A, 2026-07-09) from a real chat-v2 drive-through to an **integration fault-inject test** + honest gate-only labelling + a follow-on AD:

- **③1** — `tests/integration/.../test_loop_error_handling.py`: NEW `_RaisingExecutor(ToolExecutorImpl)` overrides `execute()` to raise (distinct from a handler soft-failure the real executor catches). With `error_policy` set + no terminator it reaches `loop.py:3068`. Asserts: lever ON → the synth `ToolResult.content == render_reflection(classify_tool_error(...))` (`RuntimeError` → INVOCATION taxonomy → "tool invocation error") reaches the LLM tool message + `error_taxonomy` set; lever OFF → baseline `"Error: … Please adjust your approach"` + `error_taxonomy is None`.
- **③4** — `scripts/benchmark_tool_error_reflection.py`: new pure `select_answerer(profile, tier)` helper + `_amain(answerer_tier=)` + `report_to_markdown(answerer_tier=)` tier label + `main()` argparse `--answerer-tier {action,cheap}` (default `action`, judge always `profile.cheap`). Default `action` = byte-identical A/B binding; `cheap` report is tier-suffixed so it doesn't clobber the action baseline. +4 CI-safe unit tests.
- **③1-fix** — `_error_taxonomy.py:36` stale cross-ref `loop.py:3023-3030` → `3068-3086` + 1 MHist line.

## Verification

- **Gate**: mypy `src` 400/0 · v2 lints 11/11 · black/isort/flake8 clean · backend pytest **3230 passed, 5 skipped, 0 fail** (+6 new: 4 knob unit + 2 rare-path integration).
- **③1 integration fault-inject PASS** (gate-only, NOT a drive-through — the rare path is near-unreachable in production; this asserts the wiring, not usability).
- **③4 weaker-model A/B** (real Azure, cheap deployment, 8 cases): plain **75.0%** → reflection **87.5%** fix_rate (**+12.5%**), tokens 149.2 → 142.5 (**−6.8**), verdict **FLIP → ON** for the cheap arm.

## Impact

- Backend/scripts only; no runtime behavior change (lever default stays OFF — this is an evidence slice). The rare-path reflection code is byte-unchanged (verified, not rewritten).
- **KEY finding — reflection is tier-dependent**: strong tier +0.00% (57.144, keep OFF) vs weak tier +12.5% at −6.8 tokens (this sprint). Reflection helps precisely where the model is weaker — the 57.144 blanket "keep OFF" is refined to tier-dependent. Direction is clear + matches the §2.4 hedge; an 8-case single run is directional, not decision-grade (a larger corpus / multi-run is needed before any GLOBAL default flip).
- **Follow-on ADs** (→ `next-phase-candidates.md`): `AD-Tool-Reflection-RarePath-Near-Dead-Evaluate` (is the near-dead rare branch worth keeping / should the executor expose a real self-raise → reflected-observation path?) + `AD-Tool-Reflection-PerTier-Default` (default ON for weaker/cheap-tier answerers, or a per-tenant/per-profile reflection policy on the C3 seam).
- Closes ③1 + ③4 of the Tool range (2 of ~4 open; ③2 autofix + ③3 taxonomy-UI remain).
- NO design note (57.144 design note 48 follow-on).
