# Sprint 57.142 Plan — OTel GenAI semantic-conventions span/attr mapping (research #5)

**Summary**: Standardize Cat 12's exported telemetry to the CNCF OpenTelemetry GenAI semantic conventions, closing `AD-Observability-OTel-GenAI-Schema` (research #5). Evidence-first reframe: the OTel SDK is ALREADY real (`opentelemetry-*==1.22.0` + OTLP/Prometheus exporters), so the gap is ONLY the bespoke span/attribute SCHEMA (`span_type`/`model`/`prompt_tokens`) vs `gen_ai.*`. The fix is a translation-at-tracer layer (`_genai_semconv.py` applied in `OTelTracer._span_cm` at span start + close), which ALSO fixes a discovered latent bug where post-response token attrs never reach exported spans. Key scope decisions (AskUserQuestion 2026-06-25): **B2** allow ONE loop.py line so `gen_ai.response.finish_reasons` exports (the research-highlighted 1:1 stop_reason mapping); **C1** defer content-capture opt-in flag to a follow-on AD. Drive-through = a real OTel-SDK `InMemorySpanExporter` conformance run over the REAL loop (CATCH = the harness, #135/#137/#138 pattern — pure-infra, no UI). Spike sprint → design note 46 required.

**Status**: Approved-to-execute (user selected research #5 via post-compact direction 2026-06-25; scope decisions B2 + C1 confirmed via AskUserQuestion 2026-06-25)
**Branch**: `feature/sprint-57-142-otel-genai-semconv`
**Base**: `main` HEAD `3e9d069e` (Sprint 57.141 PR #336 flip merged)
**Slice**: closes `AD-Observability-OTel-GenAI-Schema` (research #5; canonical order #6→#3→#8→#4→#1→#2→**#5**→#7; standalone, independent of loop.py per proposal §4.4)
**Scope decisions**: (a) translation-at-tracer — NEW `_genai_semconv.py` pure mapping applied in `OTelTracer._span_cm` start+close, loop.py bulk untouched, internal/test view stays bespoke + exported view = `gen_ai.*` (dual-view contract); (b) close-time `set_attributes` re-reads the caller's mutable attrs dict → fixes the latent post-response token-propagation bug as a free side-effect; (c) ONE loop.py line adds `finish_reason` post-response so `gen_ai.response.finish_reasons` exports (B2); (d) content-capture opt-in DEFERRED → `AD-Observability-Content-Capture-OptIn-Phase58` (C1); (e) pin a STABLE CNCF semconv subset (operation.name + request.model + usage.input/output_tokens + finish_reasons + tool.name), `gen_ai.provider.name` deferred (not threaded to span without more plumbing).

---

## 0. Background

### The gap (`AD-Observability-OTel-GenAI-Schema`, research #5)

- V2's Cat 12 emits real OTel spans, but the span NAMES (`agent_loop.llm_call`) and attribute KEYS (`span_type`, `model`, `prompt_tokens`, `completion_tokens`) are **bespoke** — not the CNCF `gen_ai.*` semantic conventions.
- Downstream OTel/APM stacks that understand the GenAI conventions (operation/model/usage/finish_reason dashboards) cannot parse V2 traces → no interop, a bespoke schema lock-in.

### Why it matters (the missing capability)

- The CNCF GenAI conventions are provider-neutral by construction (reinforces 約束 3) and CNCF-backed (avoids a self-authored schema). Standardizing makes V2 telemetry flow into ANY GenAI-aware observability stack (Jaeger GenAI views, Grafana, Datadog LLM Obs) without bespoke mapping.
- The research highlights `gen_ai.response.finish_reasons` (`tool_calls` vs `stop`) maps 1:1 to the while-true loop `stop_reason` — a high-value, currently-missing signal.

### Root cause (recon code read, file:line; ALL re-verified §checklist 0.1)

| Layer | Reality (on `main` HEAD `3e9d069e`) | Anchor |
|-------|-------------------------------------|--------|
| OTel SDK | REAL, version-pinned (api/sdk/exporter-otlp==1.22.0 + Prometheus) | `requirements.txt:46-52` |
| Single translation boundary | all loop spans → real OTel via ONE method | `tracer.py:151-197` (`OTelTracer._span_cm`); start_as_current_span `:178` |
| Bespoke attrs (start) | `category`/`trace_id_neutral`/`tenant`/`user`/`session` added by tracer + caller attrs str-copied | `tracer.py:162-173` |
| Bespoke span name + attrs (llm) | `agent_loop.llm_call` + `span_type`/`model` | `loop.py:2430-2438` |
| **Latent bug**: post-response token attrs lost | `llm_attrs` mutated AFTER span snapshot → never on exported span (only by-ref RecordingTracer sees it) | `loop.py:2470-2476` vs `tracer.py:173,178` |
| stop_reason NOT in span | only in `LLMResponded`/`LoopCompleted` event | `_contracts/chat.py:41-49`; loop has no span handle post-response |
| ABC = single-source | `Tracer` pins `start_span`/`record_metric` shape, not attr VALUES | `17-cross-category-interfaces.md:150` |

→ The fix maps bespoke→`gen_ai.*` at the single tracer boundary (start: name + static attrs; close: re-read caller attrs → usage tokens + finish_reason). The close-time set_attributes simultaneously fixes the latent token-loss bug. ONE loop.py line writes `finish_reason` post-response so it reaches the close-time translate.

### The design (translation-at-tracer: 1 NEW pure mapping module + tracer start/close apply + 1 loop.py line + conformance harness)

```
# _genai_semconv.py (NEW, pure, no I/O)
STOP_REASON_TO_FINISH_REASON = {           # provider-neutral StopReason → CNCF-canonical finish_reason
    "end_turn": "stop", "tool_use": "tool_calls", "max_tokens": "length",
    "stop_sequence": "stop", "safety_refusal": "content_filter", "provider_error": "error",
}
SPAN_TYPE_TO_OPERATION = {"LLM_CALL": "chat", "LOOP": "invoke_agent", "TOOL_EXEC": "execute_tool"}
ATTR_MAP = {"model": "gen_ai.request.model", "prompt_tokens": "gen_ai.usage.input_tokens",
            "completion_tokens": "gen_ai.usage.output_tokens", "tool": "gen_ai.tool.name", ...}

def to_genai_span(name, attributes) -> tuple[new_name, translated_attrs]:
    # remap GenAI-relevant span names (chat {model} / execute_tool {name} / invoke_agent);
    # rename known attrs to gen_ai.*; finish_reason -> gen_ai.response.finish_reasons=[mapped];
    # preserve enterprise attrs (category/tenant/user/session/span_type) verbatim; pass unmapped through

def assert_genai_conformant(span) -> list[str]:   # returns violations ([] = conformant)

# tracer.py OTelTracer._span_cm — apply at START (name+attrs) and at CLOSE (re-read caller ref → set_attributes)
# loop.py:2476+ — ONE line: llm_attrs["finish_reason"] = response.stop_reason.value
```

The mapping runs ONLY inside `OTelTracer` → the internal view (loop.py emits, NoOp/RecordingTracer in tests see) stays bespoke (existing tests unchanged); the EXPORTED view (real OTel span) is `gen_ai.*`. This dual-view contract keeps the change surgical and existing observability tests green.

### Ground truth (recon head-start — code read on `main` HEAD `3e9d069e`; ALL re-verified §checklist 0.1)

- `tracer.py:151-197` — `_span_cm` is the sole bespoke→OTel boundary; `finally` block (`:196-197`) runs while `otel_span` still open → close-time `set_attributes` lands before span end.
- `tracer.py:173` — caller `attributes` is str-copied into a NEW `attrs` dict (so the start snapshot can't see post-response mutation); the close-time path must re-read the ORIGINAL `attributes` reference.
- `loop.py:2430,2470-2476` — `llm_attrs` is the mutable dict passed to `start_span`; post-response token writes land on it before span close.
- `_contracts/chat.py:41-49` — `StopReason` enum 6 values → the `STOP_REASON_TO_FINISH_REASON` map.
- DB-less loop drivable (Sprint 57.141 D-loop-run-noDB): `AgentLoopImpl.__init__` deps `|None=None` → drive-through can direct-construct the loop with OTelTracer + InMemorySpanExporter.

**Baselines (Sprint 57.141 closeout)**: pytest 2859 (+5 skip) · wire 26 · Vitest 920 · mockup 51 · mypy 0/380 · v2 lints 21. Re-verify Day-0.

### STALE / drift findings (Day-0; full detail → progress.md — placeholder, filled in §checklist 0.1)

- **D-genai-key-names** — confirm CNCF GenAI semconv key spelling for the pinned subset (`gen_ai.operation.name` / `gen_ai.request.model` / `gen_ai.usage.input_tokens` / `gen_ai.usage.output_tokens` / `gen_ai.response.finish_reasons` / `gen_ai.tool.name`); spec evolves (`system`→`provider.name`, `prompt_tokens`→`input_tokens`) → pin a snapshot date in design note.
- **D-inmemory-exporter** — verify `opentelemetry.sdk.trace.export.in_memory_span_exporter.InMemorySpanExporter` importable from the pinned 1.22.0 SDK (drive-through + CI conformance depend on it).
- **D-span-cm-finally** — re-read `tracer.py:190-197`: confirm `otel_span.set_attributes(...)` in the `finally` lands before the `with` exits (span still open).
- **D-loop-attr-ref** — confirm `loop.py` passes the SAME `llm_attrs` ref (not a copy) into `start_span` so close-time re-read sees the post-response mutation.
- **D-existing-obs-tests** — grep `test_observability_coverage.py` / `test_tracer.py`: they use RecordingTracer/NoOpTracer (NOT OTelTracer) → assert bespoke keys → unaffected by an OTelTracer-only transform (confirm before claiming "tests unchanged").
- **D-change-designnote-free** — confirm CHANGE-109 + design note 46 numbers free.

## 1. Sprint Goal

Ship a translation-at-tracer layer that makes V2's EXPORTED OTel spans conform to a pinned CNCF GenAI semantic-conventions subset (operation.name + request.model + usage.input/output_tokens + finish_reasons + tool.name), with ZERO loop.py edits except ONE line writing `finish_reason`, and a real OTel-SDK `InMemorySpanExporter` conformance harness proving it. Proven by: gates (mypy/pytest/v2-lints/black/isort/flake8) + a CI conformance test (synthetic spans through the REAL InMemoryExporter, no Azure) + a real-loop drive-through (real Azure gpt-5.2, OTelTracer→InMemoryExporter, assert the actual `chat` span carries `gen_ai.*` incl. usage tokens [bug fixed] + finish_reasons). Produces CHANGE-109 + design note 46 (8-point gate).

## 2. User Stories

- **US-1** (mapping): 作為平台維運者，我希望 V2 匯出的 LLM/tool/agent span 用 CNCF `gen_ai.*` 命名，以便接任何 GenAI-aware APM 不需 bespoke 轉接。
- **US-2** (tracer integration): 作為 Cat 12 owner，我希望映射只發生在 `OTelTracer` 邊界（內部視圖不變），以便既有 observability 測試與 loop.py 不受影響。
- **US-3** (token-bug + finish_reasons): 作為維運者，我希望 exported span 真的帶 token usage（修掉 latent bug）與 `gen_ai.response.finish_reasons`，以便看得到每次 LLM call 的成本與終止原因。
- **US-4** (conformance harness + CI): 作為維運者，我希望一個用真 OTel SDK 的 conformance harness + CI test 斷言 `gen_ai.*` 合規，以便 schema 退化會被自動抓到。
- **US-5** (drive-through, MANDATORY-equivalent): 作為維運者，我希望在真 Azure loop 上跑一次、檢查實際 production-path span 帶 `gen_ai.*`（CATCH = harness；pure-infra 無 UI），以便證明非 Potemkin。
- **US-6** (closeout): 作為 scrum master，我希望 CHANGE-109 + design note 46 + 校準 + navigators，以便 AD CLOSED 可追溯。

## 3. Technical Specifications

### 3.0 Architecture (Cat 12 only; NO migration / NO wire event / NO frontend / NO 17.md contract change)

```
NEW   backend/src/agent_harness/observability/_genai_semconv.py        # pure mapping: STOP_REASON_TO_FINISH_REASON + SPAN_TYPE_TO_OPERATION + ATTR_MAP + to_genai_span() + assert_genai_conformant()
EDIT  backend/src/agent_harness/observability/tracer.py                # OTelTracer._span_cm: apply to_genai_span at START (name+attrs) + CLOSE (re-read caller ref → set_attributes); fixes token bug
EDIT  backend/src/agent_harness/orchestrator_loop/loop.py              # ONE line: llm_attrs["finish_reason"] = response.stop_reason.value (after :2476)
NEW   backend/scripts/benchmark_otel_conformance.py                    # real OTel SDK (TracerProvider+InMemorySpanExporter) conformance harness; --real drives the loop (Azure-gated), synthetic default (CI-safe); MD+JSON report
NEW   backend/tests/fixtures/observability/otel_conformance_cases.yaml # required gen_ai.* key checklist per span kind
NEW   backend/tests/unit/agent_harness/observability/test_genai_semconv.py  # pure mapping tests + synthetic-span-through-real-InMemoryExporter conformance + importlib harness smoke (NO Azure)
UNTOUCHED backend/src/agent_harness/observability/_abc.py              # ABC shape unchanged (schema = values, not signature)
UNTOUCHED backend/tests/integration/orchestrator_loop/test_observability_coverage.py  # RecordingTracer view stays bespoke
```

### 3.1 Mapping module (US-1) — `_genai_semconv.py`

- `STOP_REASON_TO_FINISH_REASON`: 6-entry dict (END_TURN→stop / TOOL_USE→tool_calls / MAX_TOKENS→length / STOP_SEQUENCE→stop / SAFETY_REFUSAL→content_filter / PROVIDER_ERROR→error). Provider-neutral enum value (`StopReason.value`) → CNCF-canonical string.
- `SPAN_TYPE_TO_OPERATION`: `LLM_CALL`→`chat`, `LOOP`→`invoke_agent`, `TOOL_EXEC`→`execute_tool`. Other span_types (TURN/PROMPT_BUILD/COMPACTION) have NO GenAI operation → pass through unchanged (NOT GenAI-spec spans).
- `ATTR_MAP`: `model`→`gen_ai.request.model`, `prompt_tokens`→`gen_ai.usage.input_tokens`, `completion_tokens`→`gen_ai.usage.output_tokens`, `tool`→`gen_ai.tool.name`. `finish_reason`→`gen_ai.response.finish_reasons` (value wrapped as a 1-element list via the stop-reason map). `total_tokens`/`cached_input_tokens` preserved bespoke (no stable CNCF key — design note hedge).
- `to_genai_span(name, attributes) -> tuple[str, dict]`: pure; remaps the span name for GenAI ops (`chat {model}` / `execute_tool {tool}` / `invoke_agent`), adds `gen_ai.operation.name`, renames mapped attrs, preserves enterprise attrs (`category`/`trace_id_neutral`/`tenant_id`/`user_id`/`session_id`/`span_type`) verbatim, passes unmapped keys through.
- `assert_genai_conformant(span_name, attrs) -> list[str]`: returns conformance violations (empty = conformant) for the pinned subset.

### 3.2 Tracer integration (US-2/US-3) — `tracer.py` `OTelTracer._span_cm`

- START: compute `mapped_name, mapped_attrs = to_genai_span(name, {**enterprise, **(attributes or {})})`; `start_as_current_span(mapped_name, attributes=mapped_attrs)`.
- CLOSE (in the existing `finally`, span still open): if `attributes` is not None, recompute `_, close_attrs = to_genai_span(name, {**enterprise, **attributes})` (re-reads the now-mutated caller ref) and `otel_span.set_attributes(close_attrs)` — brings out post-response `gen_ai.usage.*` (fixes latent bug) + `gen_ai.response.finish_reasons`.
- NoOpTracer unchanged (no real span). The mapping is OTelTracer-only.

### 3.3 loop.py 1-line (US-3) — `loop.py`

- After `loop.py:2476` (token attrs): `llm_attrs["finish_reason"] = response.stop_reason.value`. ONLY edit to loop.py. (Per B2 decision.)

### 3.4 Conformance harness + CI (US-4/US-5) — `benchmark_otel_conformance.py` + `test_genai_semconv.py`

- Harness: build a real `TracerProvider` + `InMemorySpanExporter`, set it global, run an `OTelTracer` through representative spans (synthetic default; `--real` direct-constructs the DB-less loop with a real Azure ChatClient, RUN_AZURE_INTEGRATION-gated, mirrors `benchmark_pass_k.py`), read exported spans, run `assert_genai_conformant` per span, emit conformance ratio + MD/JSON report (`benchmark_reports/`, gitignored → artifact copied to sprint `artifacts/`).
- CI test: pure mapping fn cases + a synthetic-span-through-real-InMemoryExporter conformance assertion (in-process, NO Azure → fully CI-safe) + importlib harness smoke (mirrors `test_benchmark_pass_k.py`).

### 3.x What is explicitly NOT done

- `gen_ai.provider.name` / `gen_ai.system` — provider not threaded to loop span; needs adapter→span plumbing > 1 line → deferred (`AD-Observability-Provider-Attr-Phase58`).
- content capture (`gen_ai.input.messages` / opt-in flag) — C1 deferred → `AD-Observability-Content-Capture-OptIn-Phase58`.
- TURN/PROMPT_BUILD/COMPACTION span GenAI mapping — no CNCF operation maps; stay bespoke.
- Renaming the INTERNAL/test view to gen_ai.* — dual-view by design; existing tests stay bespoke.

### 3.y Validation (US-1..US-6)

Gates: mypy `src` 0/380 · v2 lints 21/21 (incl. llm_sdk_leak — mapping is pure str, no native import) · pytest 2859 + new · black/isort/flake8 clean · LLM-SDK-leak clean · Vitest/mockup/build UNTOUCHED (no FE). Plus the §3.4 real-OTel-SDK conformance drive-through (CATCH = harness; pure-infra, no UI/LLM strictly required but real-loop run done for production-path proof).

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 1 | `backend/src/agent_harness/observability/_genai_semconv.py` | NEW |
| 2 | `backend/src/agent_harness/observability/tracer.py` | EDIT |
| 3 | `backend/src/agent_harness/orchestrator_loop/loop.py` | EDIT (1 line) |
| 4 | `backend/scripts/benchmark_otel_conformance.py` | NEW |
| 5 | `backend/tests/fixtures/observability/otel_conformance_cases.yaml` | NEW |
| 6 | `backend/tests/unit/agent_harness/observability/test_genai_semconv.py` | NEW |
| 7 | `claudedocs/4-changes/feature-changes/CHANGE-109-otel-genai-semconv.md` | NEW |
| 8 | `docs/03-implementation/agent-harness-planning/46-otel-genai-semconv-design.md` | NEW |
| — | `backend/src/agent_harness/observability/_abc.py` | **UNTOUCHED** (ABC shape unchanged) |
| — | `backend/tests/integration/orchestrator_loop/test_observability_coverage.py` | **UNTOUCHED** (RecordingTracer = bespoke view) |
| — | `docs/.../17-cross-category-interfaces.md` | **UNTOUCHED** (no contract change) |

## 5. Acceptance Criteria

1. `to_genai_span` renames the pinned subset correctly + preserves enterprise attrs + passes unmapped through (unit-tested).
2. `OTelTracer` exported spans (via real InMemorySpanExporter) carry `gen_ai.operation.name` + `gen_ai.request.model` (chat span) + `gen_ai.tool.name` (tool span); span names = `chat {model}` / `execute_tool {name}` / `invoke_agent`.
3. Exported `chat` span carries `gen_ai.usage.input_tokens` + `gen_ai.usage.output_tokens` (latent token bug FIXED) + `gen_ai.response.finish_reasons` (1-element, mapped from stop_reason).
4. Existing `test_observability_coverage.py` + `test_tracer.py` stay green UNMODIFIED (dual-view contract holds).
5. **Drive-through PASS (real OTel SDK + real Azure loop)** — run `benchmark_otel_conformance.py --real` (or the direct-construct loop) on real Azure gpt-5.2; the ACTUAL production-path `chat` span carries `gen_ai.*` incl. usage tokens + finish_reasons; conformance ratio reported; MD+JSON → `artifacts/`. (CATCH = harness; pure-infra, explicitly "real-SDK-verified", no UI.)
6. `AD-Observability-OTel-GenAI-Schema` CLOSED; CHANGE-109; design note 46 (8/8 gate); calibration recorded; navigators + next-phase-candidates updated (deferred follow-ons logged).

## 6. Deliverables

- [ ] US-1 `_genai_semconv.py` pure mapping module
- [ ] US-2 `OTelTracer._span_cm` start+close apply (dual-view, OTelTracer-only)
- [ ] US-3 latent token bug fixed (close-time set_attributes) + 1-line loop.py finish_reason
- [ ] US-4 `benchmark_otel_conformance.py` + `otel_conformance_cases.yaml` + CI tests
- [ ] US-5 real-OTel-SDK + real-Azure drive-through verdict → artifacts
- [ ] US-6 CHANGE-109 + design note 46 + closeout

## 7. Workload Calibration

- Scope class **NEW `otel-genai-semconv-spike` 0.60** (1st data point; Cat 12 schema-mapping + conformance-harness spike. Kin: `verification-trace-and-benchmark-spike` 0.60 / `guardrail-restrict-spike` 0.60 / `layered-compaction-spike` 0.60 / `passk-reliability-spike` 0.60 — all real-code-core measurement/structural spikes. Per the 57.137 lesson: a >~3 hr real implementation core (mapping module + tracer integration + harness + tests) holds the spike multiplier, NOT a tiny-code 0.85 ceremony re-point. The 1-line loop.py + the latent-bug fix add real-code substance.)
- **Agent-delegated: no** (parent-direct, like the recent #136-141 spikes). `agent_factor` 1.0 → 3-segment form.
- Bottom-up est ~10 hr (US-1 ~2 / US-2 ~1.5 / US-3 ~2 / US-4 ~1.5 / US-5 ~1 / US-6 ~2) → class-calibrated commit ~6 hr (mult 0.60). Day-4 retro Q2 verifies.

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| CNCF GenAI semconv spec drift (key renames) | pin a STABLE subset + snapshot date in design note (D-genai-key-names); avoid unstable keys (cache tokens, provider rename) |
| Close-time `set_attributes` fires after span end (no effect) | D-span-cm-finally re-verify the `finally` runs while span open; CI conformance test asserts tokens ARE on the exported span |
| loop.py passes a COPY not the ref → close-time re-read stale | D-loop-attr-ref re-verify same-ref pass; the token-bug-fix test catches it |
| OTelTracer-only mapping breaks an existing test that DOES use OTelTracer | D-existing-obs-tests grep confirms tests use NoOp/RecordingTracer; run full pytest Day-2 |
| `InMemorySpanExporter` import path differs in 1.22.0 | D-inmemory-exporter Day-0 import probe |
| Risk Class E (stale `--reload` masks the loop wiring) | drive-through direct-constructs the loop standalone (no server), like `benchmark_pass_k.py` — no stale-process risk |
| dual-view confusion (internal bespoke / exported gen_ai) | design note §contract explicitly documents the two views |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- `gen_ai.provider.name` / `gen_ai.system` — `AD-Observability-Provider-Attr-Phase58`.
- content capture opt-in flag — `AD-Observability-Content-Capture-OptIn-Phase58` (C1).
- Renaming internal/test view to gen_ai.* (collapse dual-view) — only if a future need arises.
- metrics-label gen_ai mapping (`record_metric` labels) — could extend later; this sprint = spans only (note in design note).
- #7 `AD-Tool-Description-Lint-Reflection` — next canonical item after #5.
