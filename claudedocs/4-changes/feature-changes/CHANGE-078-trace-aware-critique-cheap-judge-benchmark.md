# CHANGE-078: A3 — trace-aware critique verifier + permanent cheap-judge accuracy benchmark

**Date**: 2026-06-13
**Sprint**: 57.111 (A3 — the LAST harness-deepening slice; closes the 10-slice set)
**Scope**: 範疇 10 (Verification Loops) + 範疇 1 (Orchestrator Loop, gate threading) + eval tooling

## Problem

Two gaps from the harness-deepening proposal §1.4 (A3):
1. **Verifier is blind to the loop trace** — A1 (57.98) defined `Verifier.verify(*, output, state: LoopState, ...)` but the in-loop gate passed `state=cast(LoopState, None)`, so the LLM judge only ever saw the final answer string. It could not critique trace-aware (catch a final answer that contradicts a mid-trace tool error).
2. **Cheap-judge accuracy never measured** — 57.97 routed the judge to the cheap tier; design note 24:78 left it an Open Invariant ("a cheaper judge MAY be less reliable; NOT formally benchmarked"), with no number and a qualitative decision rule.

## Root Cause

1. A1 laid the `state` plumbing but every call site (the gate + 3 Cat 9 fallback judge paths) passed `cast(LoopState, None)` — the trace was never threaded. `_run_turns` has no `LoopState` object in scope (only the loop-local `messages`), so the gate had to build one.
2. Greenfield — the repo had no eval/benchmark harness for the judge.

## Solution

**US-1 trace-aware critique** (`loop.py` diff = 25 ins / 3 del, threading only — NO logic rewrite):
- `verification/_trace.py` (NEW): `build_trace_block(messages, *, max_messages, char_budget)` — a bounded (last-N msgs / per-msg cap / total char budget, env-overridable) provider-neutral formatter of recent turns + tool errors.
- `loop.py` `_cat10_verify_gate`: gains a `messages` param + builds a minimal `trace_state` (mirroring the Cat 4 `compact_state` idiom) + forwards `state=trace_state` to `verifier.verify` (the candidate answer is appended AFTER the gate → the trace excludes it, no double-count).
- `verification/llm_judge.py`: `_build_prompt(output, state)` substitutes a `{trace}` block from `state.transient.messages`; `state=None` → empty (back-compat). + an optional `temperature` ctor param (the benchmark uses 0.0; default 1.0 byte-identical).
- `verification/templates/output_quality.txt`: a `{trace}` section + a 4th "contradicts the trace" failure bullet; "MAY BE EMPTY" wording preserves the no-state path.
- **ABC widen**: `Verifier.verify` `state: LoopState → LoopState | None = None` — removes the 4-site `cast(LoopState, None)` type-lie (the 3 Cat 9 fallback judge sites — `tools.py` / `cat9_mutator.py` / `cat9_fallback.py` — now pass `state=None`).

**US-2 permanent cheap-judge benchmark**:
- `scripts/benchmark_judge.py` (NEW): the reusable logic (`load_cases` / `run_judge(with_trace)` / `build_report`) + `CHEAP_ACCURACY_FLOOR=0.70` (floor judged on unambiguous categories) + a `main()` CLI.
- `tests/fixtures/verification/judge_benchmark.yaml` (NEW): 28 hand-labeled cases (clear_pass ×8 / clear_fail ×8 / trace_dependent ×7 / borderline ×5).
- `tests/benchmark/test_judge_accuracy.py` (NEW): `@pytest.mark.benchmark` + `RUN_AZURE_INTEGRATION` skipif real-LLM wrapper.
- `tests/unit/scripts/test_benchmark_judge.py` (NEW): 9 CI-safe logic tests. Both test files load the script via `importlib` (the `tests.unit.scripts` shadow, `verify_audit_chain` idiom).
- `pyproject.toml`: `benchmark` marker. `.gitignore`: `/backend/benchmark_reports/`.

## Verification

- **Gates**: mypy `src` 0/360 · black/isort/flake8 0 · run_all 10/10 (wire count 24, no codegen diff) · full pytest **2526 passed + 5 skipped** (+24, +1 benchmark skip, 0 del) · Vitest 837 holds (no FE) · mockup-fidelity 51 holds · `loop.py` diff threading-only.
- **Drive-through Leg A** (real UI :3007 + fresh A3 backend PID 38328 + real Azure gpt-5.2, dev-login `jamie@acme.com · acme-prod`): "what is the capital of France?" → "The capital of France is Paris." + **Verification (1) ✅** — the in-loop trace-aware gate ran live (built the `trace_state`, the judge verified + passed a good answer). Confirms the A3 path is active end-to-end (no Potemkin); screenshot `artifacts/dt57111-legA-chat-verification-pass.png`.
- **Drive-through Leg B** (real Azure benchmark, `python scripts/benchmark_judge.py`, exit 0): cheap accuracy **92.86%** (stable across 2 runs) · strong 78.57–92.86% (Azure non-determinism on clear_pass even at temp 0) · cheap-vs-strong agreement 71–86% · **trace_delta +42.86% (stable)** — the cheap judge WITH trace nails trace_dependent 100%; WITHOUT trace it misses ~43% → the quantitative proof US-1 works on real Azure · floor 70% → **PASS**. Report `artifacts/legB-benchmark-report.md`.
- **Design note 24 verdict** (settled): the cheap tier is accurate (92.86%, stable, 100% trace_dependent) and actually aligns BETTER with the lenient judge contract than the strong tier (which over-flags clear_pass) → **keep the cheap tier** (57.97's choice confirmed).

## Impact

Backend + eval tooling only — NO frontend, NO DB/migration, NO wire/codegen change (`VerificationFailed.reason` carries the richer critique). `loop.py` data-threading only (no control-flow change). The 3 Cat 9 fallback judge paths rely on the back-compat empty-trace (`state=None`) path. The benchmark is on-demand (CI skips it via `RUN_AZURE_INTEGRATION`). Closes the harness-deepening 10-slice set (only optional follow-ons remain).

## Honest scope note (drive-through)

Leg A drove a PASS case (a good answer the trace-aware judge correctly passed; the trace was the prior user turn). A live trace-dependent FAIL was NOT engineered (gpt-5.2 won't claim success after a tool error without a config change) — the trace-aware FAIL behavior is proven QUANTITATIVELY by Leg B (trace_delta on 7 trace_dependent cases). Leg A proves the path runs live + renders; Leg B proves the trace-aware judging behavior.
