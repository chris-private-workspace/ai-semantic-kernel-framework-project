# CHANGE-108: pass^k reliability eval harness (research #2)

**Date**: 2026-06-25 (work 2026-06-24 → 25)
**Sprint**: 57.141
**Scope**: 範疇 12 (Observability / Evaluation) — eval tooling; closes `AD-Eval-PassK-Reliability-Harness` (research #2)

## Problem

The platform proved quality two ways — **drive-through** (run once, can a human use it) + 5 **A/B benchmarks** (two arms, one run each). **Neither measures repeatability.** Research's headline: `reliability ≠ capability`, and the two diverge super-linearly with task length — invisible to `pass@1` (τ-bench: GPT-4o pass@1 ~61% but **pass^8 <25%**). V2 had zero pass^k / consistency / fault-injection scaffolding (grep-confirmed), despite its trace-persistence being a research-flagged cheap place to generate such data.

## Motivation (net-new feature, not a bug)

Add V2's first reliability-science axis: run the SAME input k times and measure consistency. 4 axes (user-picked over the recommended minimal 2): pass^k vs pass@1 · behavioral consistency · fault injection (λ) · perturbation (ε), hybrid oracle (rules first, LLM judge for open-ended). Evidence-first: MEASURE the research's pass^k≠pass@1 claim on V2's OWN loop rather than assume it.

## Solution

Pure-offline `scripts/benchmark_pass_k.py` (mirrors `benchmark_judge.py`, Sprint 57.111) — **3 NEW files, ZERO src edit**:
- `benchmark_pass_k.py` — `load_cases` (schema-valid YAML) + `_FaultInjectingChatClient` (6-method `ChatClient` ABC delegate; `chat` raises `InjectedFault` at `fault_rate`, rng-injectable) + hybrid `evaluate` (rules inline normalized contains/exact | `LLMJudgeVerifier(profile.cheap, per-case-criterion raw template)`) + `run_case` (direct-constructs a DB-less `AgentLoopImpl`, drives `run()` k times, `_extract`s answer/tool-seq/tokens/stop_reason) + `build_report` (pure: pass@1 / pass^k / divergence / answer+tool-seq consistency / λ degradation / ε instability / per-category) + MD+JSON + `main()` (`--k --fault-rate --epsilon`).
- `tests/fixtures/observability/pass_k_cases.yaml` — 12 cases (5 easy + 7 multistep; 10 rules + 2 judge; 2 with ε perturbations). `tool_use` schema-supported but deferred (DB-free robustness).
- `tests/unit/scripts/test_benchmark_pass_k.py` — 17 CI-safe tests (importlib idiom + spy `ChatClient` driving a REAL `AgentLoopImpl` offline + seeded rng + synthetic CaseRuns).

Key design: λ injects at the chat client (baseline/fault arms differ ONLY by the wrapper = cleanest A/B; loop uses DEFAULT error handling → measures real-loop resilience as-is). Judge oracle embeds a per-case correctness criterion in a raw template producing the `{"passed": bool}` JSON `LLMJudgeVerifier._parse_response` reads.

## Verification

- CI-safe: **17/17 unit pass** (incl. `test_run_case_drives_loop_offline` — spy client drives the REAL loop, proving harness↔loop wiring) · mypy `src` **380/0** · flake8/black/isort clean · v2 lint tests **21 pass** (incl. llm_sdk_leak 3 → `_FaultInjectingChatClient` neutrality) · full backend pytest **2859+5skip** (1 pre-existing `AD-Billing-Outbox-Drain-Test-Flake`, passes in isolation).
- **Drive-through (real Azure gpt-5.2, 12 cases · k=3 · 90 runs · 94,373 tokens)** — `artifacts/passk-drivethrough-verdict.{md,json}`:
  - pass@1 100% / pass^k 100% (divergence 0% — corpus too easy to stress the divergence regime; valid verdict)
  - **answer-consistency 75%** — 3/12 cases phrase answers differently across runs at 100% pass^k (the "agent disagrees with itself" axis, invisible to pass@1)
  - **λ degradation 50%** — a 20% LLM-fault rate halves pass^k (no chat-level retry)
  - ε instability 0% — robust to paraphrasing

## Impact

- Backend eval tooling only. ZERO src / migration / wire (stays 26) / frontend / `loop.py` edit. No runtime behavior change — a permanent, re-runnable reliability harness.
- Surfaced 2 real reliability signals invisible to pass@1 + an honest "divergence regime needs a harder corpus" boundary → 3 follow-on candidates (`AD-Eval-PassK-Harder-Corpus` / `AD-Loop-ChatLevel-Retry` / `AD-Eval-Answer-Consistency-Surface`).
- Design note 45. research #2 CLOSED; next canonical = #5 OTel GenAI schema.
