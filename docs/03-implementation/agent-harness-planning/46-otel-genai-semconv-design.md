# Design Note 46 — OTel GenAI semantic-conventions span/attr mapping (research #5)

**Purpose**: Extract the verified design of V2's bespoke→CNCF OpenTelemetry GenAI semantic-conventions span/attribute mapping from the Sprint 57.142 thin-spike implementation.
**Category / Scope**: 範疇 12 (Observability) / Phase 57 / Sprint 57.142
**Created**: 2026-06-25
**Last Modified**: 2026-06-25
**Status**: Active (spike-extracted; verified ratio ≥ 95%)

> **Modification History**
> - 2026-06-25: Initial extract from Sprint 57.142 implementation (CHANGE-109)

---

## 1. Spike Summary

Closes `AD-Observability-OTel-GenAI-Schema` (research #5). Ships a translation-at-tracer layer that
maps V2's bespoke OTel span names + attribute keys to the CNCF GenAI semantic conventions (`gen_ai.*`)
so V2 telemetry interoperates with any GenAI-aware APM. 3 NEW files (`_genai_semconv.py` mapping +
`benchmark_otel_conformance.py` harness + `test_genai_semconv.py`) + 1 corpus + 2 EDITs (`tracer.py`
+ a single `loop.py` line).

**The reframe that scoped this spike** (Day-0 evidence): the research framing was "Cat 12 uses a
self-authored wrapper, not standard schema" — but the OTel SDK is ALREADY real (`opentelemetry-api/
sdk/exporter-otlp==1.22.0` + OTLP→Jaeger + Prometheus, `requirements.txt:46-52`). The gap is ONLY the
bespoke SCHEMA. So this is a schema-conformance translation, NOT an OTel adoption.

**The latent bug found + fixed for free**: `agent_loop.llm_call` writes token attrs post-response
(`loop.py:2470-2476`) AFTER OTel snapshots the start attributes → the real exported span never carried
tokens (only the by-reference test `RecordingTracer` saw them). The close-time `set_attributes`
re-read fixes this.

**Drive-through verdict** (real Azure gpt-5.2): the production-path `chat gpt-5.2` span carries
`gen_ai.operation.name` + `gen_ai.request.model` + `gen_ai.usage.input_tokens`/`output_tokens` (bug
fixed) + `gen_ai.response.finish_reasons`; GenAI 2/2 conformant, ratio 100%.

## 2. Decision Matrix

| Decision | Chosen | Alternatives rejected | Why |
|----------|--------|-----------------------|-----|
| Mapping location | translation-at-tracer (`OTelTracer._span_cm` start+close) | emit `gen_ai.*` at source (loop.py) | the tracer is the SINGLE bespoke→OTel boundary (`tracer.py:151-197`); zero loop.py for the bulk; honors "不觸 loop.py" |
| Token / finish_reason propagation | close-time `set_attributes` re-reads the caller's mutable attrs ref | only set at span start | the start snapshot can't see the post-response dict mutation (the latent bug); close-time re-read fixes it (`tracer.py:196-198`) |
| finish_reasons | allow ONE loop.py line (`finish_reason` post-response) | strict zero loop.py (defer finish_reasons) | AskUserQuestion B2 — the research-highlighted 1:1 stop_reason mapping is high-value for 1 surgical line |
| Schema view | dual-view (internal/test bespoke, exported `gen_ai.*`) | rename everywhere (loop.py + tests) | mapping OTelTracer-only → loop.py + existing observability tests untouched |
| finish_reason vocabulary | normalize StopReason → OpenAI-style (`end_turn`→`stop`, `tool_use`→`tool_calls`) | keep neutral enum values | lets telemetry flow into any APM expecting the conventional vocabulary |
| Conformance verdict | real OTel SDK `InMemorySpanExporter` (CATCH = harness) | mock span assertions | a real-SDK export is the honest drive-through for a pure-infra schema change (#135/#137/#138 pattern) |
| Content capture | DEFERRED (C1) | design the opt-in flag now | YAGNI — V2 already captures NO content (safe-by-omission); no current consumer → AP-6 risk |
| `gen_ai.provider.name` | DEFERRED | thread provider to the span | provider isn't on the loop span; needs adapter→span plumbing > 1 line |

## 3. Cross-Category Contracts

**N/A** — no new cross-category contract / ABC introduced. The mapping is a pure transform applied
INSIDE the existing `Tracer` impl (`OTelTracer`); the `Tracer` ABC (`observability/_abc.py:32-54`,
pinned `17-cross-category-interfaces.md:150`) is unchanged — the schema is the ABC's VALUES, not its
signature. Nothing to register in `17-cross-category-interfaces.md`. (`_genai_semconv.to_genai_span`
is pure-function eval/mapping scaffolding consumed only by `OTelTracer` + the conformance harness.)

## 4. Verified Invariants (this spike)

All verified via the 18-test CI-safe suite + the real-Azure drive-through:
- **mapping correctness**: `to_genai_span` renames bespoke→`gen_ai.*`, rebuilds span names, preserves
  enterprise attrs, passes non-GenAI spans through — `test_to_genai_span_*` (`test_genai_semconv.py`).
- **full enum coverage**: every `StopReason` has a finish_reason mapping — `test_stop_reason_map_covers_all_enum`.
- **real-SDK export carries `gen_ai.*`**: synthetic spans through a real `InMemorySpanExporter` are
  100% conformant — `test_synthetic_spans_export_conformant`.
- **latent token-loss FIXED**: tokens written post-span-start reach the exported span via close-time
  set_attributes — `test_chat_span_carries_usage_tokens_post_response`.
- **dual-view holds**: existing `test_observability_coverage.py` + `test_tracer.py` green UNMODIFIED.
- **LLM-neutral**: `_genai_semconv` is pure str (no native import) — v2 `test_llm_sdk_leak` 3/3.
- **real-Azure end-to-end**: the production-path `chat` span conforms (usage + finish_reasons) —
  `artifacts/otel-conformance-verdict.{md,json}`.

**Verification command**:
```
# CI-safe (no Azure):
python -m pytest tests/unit/agent_harness/observability/test_genai_semconv.py -q   # 18 passed
python scripts/benchmark_otel_conformance.py                                       # synthetic, exit 0
# Real Azure drive-through:
RUN_AZURE_INTEGRATION=1 AZURE_OPENAI_*=... python scripts/benchmark_otel_conformance.py --real
```
**Fixture**: `backend/tests/fixtures/observability/otel_conformance_cases.yaml` (pinned conformance spec).

## 5. Open Invariants (NOT verified here — deferred)

- **`gen_ai.provider.name` / `gen_ai.system`** — provider isn't threaded to the loop span; needs
  adapter→span plumbing → `AD-Observability-Provider-Attr-Phase58`.
- **content capture (`gen_ai.input.messages` / opt-in flag)** — deferred per C1 →
  `AD-Observability-Content-Capture-OptIn-Phase58`.
- **metrics-label gen_ai mapping** — `record_metric` labels are still bespoke; this spike is spans-only.
- **CNCF semconv version drift** — pinned to the 2026-06-25 STABLE subset (operation.name /
  request.model / usage.input/output_tokens / response.finish_reasons / tool.name). Unstable keys
  (cache tokens, the `system`→`provider.name` rename) intentionally NOT adopted. A re-pin is needed if
  the spec stabilizes new keys.
- **TURN / PROMPT_BUILD / COMPACTION spans** — no CNCF operation maps; they stay bespoke by design.

## 6. Rollback

3 NEW files + 2 surgical EDITs. To revert: `git rm` the 3 NEW files; in `tracer.py` restore the
pre-57.142 `_span_cm` (drop the `to_genai_span` import + the start/close mapping); in `loop.py` drop the
1 `finish_reason` line. No migration / no wire / no config / no frontend to revert. The dual-view design
means reverting restores the bespoke exported schema with zero internal-view churn. ~30 min.

## 7. References

- `claudedocs/5-status/otel-genai-schema-thin-spike-eval-20260625.md` — the pre-implementation eval / decision matrices
- `claudedocs/5-status/ai-agent-harness-consolidated-analysis-20260622.md` §2.7 / §5 #5 / §3 Cat 12 — research #5 source (OTel GenAI 🟢)
- `backend/src/agent_harness/observability/_genai_semconv.py` — the mapping
- `backend/src/agent_harness/observability/tracer.py:151-198` — `OTelTracer._span_cm` start+close apply
- `backend/src/agent_harness/orchestrator_loop/loop.py:2477` — the 1-line finish_reason write
- `backend/requirements.txt:46-52` — real OTel SDK pin
- `backend/scripts/benchmark_pass_k.py` (Sprint 57.141) — the harness pattern mirrored
- CHANGE-109 + `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-142/{progress,retrospective}.md`

## 8-Point Quality Gate (self-review)

- [x] 1. Section header ↔ spike US (§4 invariants map to US-1..6)
- [x] 2. Every technical claim carries file:line (§2/§3/§4 anchored)
- [x] 3. Decision rationale = comparison matrix (§2, 8 rows with rejected alternatives)
- [x] 4. Verification command reproducible (§4 — both CI-safe + real-Azure)
- [x] 5. Test fixture referenced (§4 — `otel_conformance_cases.yaml` + the 18-test suite)
- [x] 6. Open invariants boundary explicit (§5 — what was NOT verified, with follow-on ADs)
- [x] 7. Rollback path (§6 — 3-file rm + 2 surgical reverts, ~30 min)
- [x] 8. 17.md cross-ref (§3 — N/A justified: no new contract, schema = Tracer ABC values)
