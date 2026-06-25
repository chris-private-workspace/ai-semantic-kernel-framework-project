# Sprint 57.142 Retrospective — OTel GenAI semantic-conventions span/attr mapping (research #5)

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-142-plan.md) · [Progress](./progress.md)

---

## Q1. What was delivered?

Closed `AD-Observability-OTel-GenAI-Schema` (research #5). A translation-at-tracer layer maps V2's
bespoke OTel span names + attribute keys to the CNCF GenAI semantic conventions (`gen_ai.*`):
- **NEW `_genai_semconv.py`** — pure mapping (stop-reason → finish_reason, span_type → operation, attr
  renames, `to_genai_span()`, `assert_genai_conformant()`).
- **EDIT `tracer.py`** — `OTelTracer._span_cm` applies the mapping at span start + close; the close-time
  `set_attributes` re-read fixes a discovered latent post-response token-loss bug as a free side-effect.
- **EDIT `loop.py`** — 1 line writes `finish_reason` (B2) → `gen_ai.response.finish_reasons`.
- **NEW `benchmark_otel_conformance.py`** — real-OTel-SDK `InMemorySpanExporter` conformance harness
  (synthetic CI-safe + `--real` Azure loop).
- **NEW `otel_conformance_cases.yaml`** + **NEW `test_genai_semconv.py`** (18 tests).
- CHANGE-109 + design note 46 (8/8 gate).

## Q2. Estimate accuracy / calibration

- Scope class **NEW `otel-genai-semconv-spike` 0.60** (1st data point). Parent-direct (`agent_factor` 1.0) → 3-segment form.
- Bottom-up est ~10 hr → class-calibrated commit ~6 hr (mult 0.60).
- **Actual ≈ commit (ratio ~0.95-1.0, IN band)** → KEEP 0.60. Clean execution: all 6 Day-0 D-rows
  GREEN (no scope shift), tests passed first try (18/18), synthetic + real drive-through both passed
  first try. The real-code core (mapping module + tracer integration + harness + 18 tests) held the
  0.60 spike multiplier — consistent with the 57.137 lesson (a >~3 hr real implementation core holds
  the spike multiplier; NOT a tiny-code 0.85 ceremony re-point). Kin: `verification-trace-and-benchmark-spike`
  0.60 / `guardrail-restrict-spike` 0.60 / `layered-compaction-spike` 0.60 / `passk-reliability-spike` 0.60.

## Q3. What went well?

- **Evidence-first reframe paid off**: Day-0 found the OTel SDK was already real (not "self-authored
  wrapper") → scope collapsed from "adopt OTel" to "translate the schema" → much smaller, surgical spike.
- **The latent bug discovery**: reading `loop.py:2470-2476` vs `tracer.py:173,178` surfaced that real
  exported spans never carried tokens — fixed for free by the close-time re-read. A pure-infra spike that
  ALSO fixed a real production-trace gap.
- **Dual-view design** kept loop.py (1 line) + all existing observability tests untouched.
- **Real-SDK drive-through** (InMemorySpanExporter) gave honest pure-infra verification — the actual
  production-path `chat gpt-5.2` span conforms, not a mock.

## Q4. What was harder / surprising?

- The OTel attribute coercion: a `list` attribute (`gen_ai.response.finish_reasons=["stop"]`) is stored
  as a `tuple` by the SDK → the test asserts `("stop",)`. Caught immediately by the real-SDK test.
- 2 MHist lines exceeded E501 on first draft (tracer.py + loop.py) → trimmed (the recurring MHist
  char-budget lesson; `file-header-convention.md`).

## Q5. Anti-pattern self-check (AP-2/3/4/6/8/11)

- **AP-2** (no orphan): the mapping is reachable from `OTelTracer._span_cm` (the production tracer); the
  harness is run by CI tests + the drive-through. No orphan. ✅
- **AP-3** (no scatter): all mapping in ONE `_genai_semconv.py`, applied at ONE tracer boundary. ✅
- **AP-4** (no Potemkin): the conformance is asserted on REAL exported spans (real OTel SDK), the token
  fix is observable (`chat_has_usage_tokens=true`). Not a shell. ✅
- **AP-6** (no speculative abstraction): the mapping has a current real consumer (external GenAI APM
  interop). Content-capture flag (no current consumer) was DEFERRED to avoid AP-6. ✅
- **AP-8** (PromptBuilder): N/A (no prompt assembly). ✅
- **AP-11** (no version suffix): no `_v2`/`_new`. ✅
- v2 lint tests pass incl. llm_sdk_leak 3/3 (mapping is pure str — neutrality preserved). ✅

## Q6. Carryover / follow-ons

- `AD-Observability-Provider-Attr-Phase58` — thread `gen_ai.provider.name` to the span (adapter→span plumbing).
- `AD-Observability-Content-Capture-OptIn-Phase58` — opt-in `gen_ai.input/output.messages` flag (C1 deferral).
- `AD-Observability-Metrics-GenAI-Labels-Phase58` — extend the gen_ai mapping to `record_metric` labels (spans-only this sprint).
- Optional: re-pin the CNCF semconv subset when more keys stabilize (cache tokens, provider rename).

## Q7. Next

- Research #5 CLOSED. Per canonical order (#6→#3→#8→#4→#1→#2→#5→**#7**), next un-done = **#7
  `AD-Tool-Description-Lint-Reflection`** (Cat 2 — tool-description lint + structured-error reflection).
- Rolling discipline: do NOT pre-write; the next sprint opens with an evidence-first eval when the user
  selects the direction.

## Design Note Extract (spike sprint)

**File**: `docs/03-implementation/agent-harness-planning/46-otel-genai-semconv-design.md`
**Verified ratio (estimated)**: ≥ 95%
**8-Point Quality Gate**: [x] 1 header [x] 2 file:line [x] 3 decision matrix [x] 4 verify command
[x] 5 test fixture [x] 6 open-invariant boundary [x] 7 rollback [x] 8 17.md cross-ref (N/A justified)
**Reviewer pass**: self-review (parent-direct)
