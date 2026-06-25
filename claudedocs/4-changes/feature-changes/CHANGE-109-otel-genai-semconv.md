# CHANGE-109: OTel GenAI semantic-conventions span/attr mapping (research #5)

**Date**: 2026-06-25
**Sprint**: 57.142
**Scope**: 範疇 12 (Observability) — telemetry schema; closes `AD-Observability-OTel-GenAI-Schema`

## Problem

V2's Cat 12 already emits REAL OTel spans (the OTel SDK + OTLP/Prometheus exporters are
version-pinned at `requirements.txt:46-52`), but the span NAMES (`agent_loop.llm_call`) and
attribute KEYS (`span_type` / `model` / `prompt_tokens`) are BESPOKE — not the CNCF OpenTelemetry
GenAI semantic conventions (`gen_ai.*`). Downstream GenAI-aware APM stacks cannot parse V2 traces.
(The research framing "self-authored wrapper" was half wrong — only the SCHEMA is bespoke, not the
SDK; see design note 46 §1.)

Separately, an evidence-first read found a **latent bug**: the `agent_loop.llm_call` span's token
attrs are written post-response (`loop.py:2470-2476`) AFTER OTel snapshots the start attributes, so
the REAL exported span never carried token usage (only the by-reference test `RecordingTracer` saw
them → tests green, production Jaeger trace missing tokens).

## Root Cause

All loop spans flow through ONE bespoke→OTel boundary: `OTelTracer._span_cm` (`tracer.py:151-197`).
The bespoke keys were passed straight to the real SDK with no CNCF translation. The token-loss was a
snapshot-timing bug: `start_as_current_span(attributes=...)` fixes attrs at span start; the caller's
later dict mutation never propagated.

## Solution

Translation-at-tracer (scope decision: AskUserQuestion 2026-06-25 — **B2** allow 1 loop.py line for
finish_reasons; **C1** defer content capture):

- **NEW `observability/_genai_semconv.py`** — pure mapping: `STOP_REASON_TO_FINISH_REASON` (6 enum
  values → CNCF finish_reason) + `SPAN_TYPE_TO_OPERATION` (LLM_CALL→chat / TOOL_EXEC→execute_tool /
  LOOP→invoke_agent) + `ATTR_MAP` + `to_genai_span()` (renames to `gen_ai.*`, rebuilds the span name
  `chat {model}` / `execute_tool {name}` / `invoke_agent`, preserves enterprise attrs, passes
  non-GenAI spans through bespoke) + `assert_genai_conformant()`.
- **EDIT `observability/tracer.py`** — `OTelTracer._span_cm` applies `to_genai_span` at span START
  (name + attrs) and at CLOSE (re-reads the caller's mutable attrs ref → `set_attributes`). The
  close-time path makes `gen_ai.usage.*` + `gen_ai.response.finish_reasons` actually export — fixing
  the latent token loss as a free side-effect. Mapping is OTelTracer-only → the INTERNAL/test view
  stays bespoke (dual-view contract; existing tests untouched).
- **EDIT `orchestrator_loop/loop.py`** — ONE line: `llm_attrs["finish_reason"] = response.stop_reason.value`
  post-response (B2) so finish_reasons reaches the close-time translate.
- **NEW `scripts/benchmark_otel_conformance.py`** — real OTel SDK (`TracerProvider` +
  `InMemorySpanExporter`) conformance harness; synthetic (CI-safe) default + `--real` (Azure loop).
- **NEW `tests/fixtures/observability/otel_conformance_cases.yaml`** — pinned conformance spec.
- **NEW `tests/unit/agent_harness/observability/test_genai_semconv.py`** — 18 tests.

Deferred (out of scope): `gen_ai.provider.name` (`AD-Observability-Provider-Attr-Phase58`), content
capture opt-in flag (`AD-Observability-Content-Capture-OptIn-Phase58`), metrics-label mapping.

## Verification

- **Gates**: mypy `src` 0/381 · pytest 2877 passed + 5 skip (= 2859 + 18 new; 1 pre-existing
  `AD-Billing-Outbox-Drain-Test-Flake` Risk Class C passes in isolation) · flake8/black/isort clean ·
  v2 lint tests pass incl. llm_sdk_leak 3/3 (mapping is pure str, neutrality preserved) · existing
  `test_observability_coverage.py` + `test_tracer.py` green UNMODIFIED.
- **Drive-through PASS (real Azure gpt-5.2)**: `python scripts/benchmark_otel_conformance.py --real` —
  the ACTUAL production-path `chat gpt-5.2` span carries `gen_ai.operation.name=chat` +
  `gen_ai.request.model=gpt-5.2` + `gen_ai.usage.input_tokens`/`output_tokens` (latent bug FIXED on
  the real path) + `gen_ai.response.finish_reasons`; `invoke_agent` conformant; `agent_loop.turn`
  exempt. GenAI 2/2 conformant, ratio 100%, exit 0. Artifacts:
  `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-142/artifacts/otel-conformance-verdict.{md,json}`.
- CI-safe: `python -m pytest tests/unit/agent_harness/observability/test_genai_semconv.py` → 18 passed.

## Impact

Backend-only, Cat 12 telemetry schema. NO migration / NO wire event / NO frontend / NO 17.md contract
change (Tracer ABC shape unchanged — schema is the ABC's values). Dual-view: exported spans now
conform to CNCF GenAI conventions; internal/test view + loop.py emission stay bespoke.
