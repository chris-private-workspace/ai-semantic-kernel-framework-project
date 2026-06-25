# Sprint 57.142 — Checklist (OTel GenAI semantic-conventions span/attr mapping, research #5)

[Plan](./sprint-57-142-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch

### 0.1 Three-prong Day-0 verify (against `main` HEAD `3e9d069e`)
- [x] **Prong 1 — path verify**: NEW targets free (`observability/_genai_semconv.py` / `scripts/benchmark_otel_conformance.py` / `tests/fixtures/observability/otel_conformance_cases.yaml` / `tests/unit/agent_harness/observability/test_genai_semconv.py`); EDIT files present (`tracer.py` / `loop.py`); `CHANGE-109` + design note `46` free
- [x] **Prong 2 — content verify** (drift → progress.md):
  - [x] **D-genai-key-names** — confirm pinned CNCF subset spelling (`gen_ai.operation.name` / `gen_ai.request.model` / `gen_ai.usage.input_tokens` / `gen_ai.usage.output_tokens` / `gen_ai.response.finish_reasons` / `gen_ai.tool.name`); pin snapshot date in design note
  - [x] **D-inmemory-exporter** — `python -c "from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter"` importable on pinned 1.22.0
  - [x] **D-span-cm-finally** — re-read `tracer.py:190-197`: `set_attributes` in `finally` lands before `with` exits (span still open)
  - [x] **D-loop-attr-ref** — confirm `loop.py:2434` passes the SAME `llm_attrs` ref (not a copy) into `start_span`
  - [x] **D-existing-obs-tests** — grep `test_observability_coverage.py` + `test_tracer.py` use RecordingTracer/NoOpTracer (NOT OTelTracer) → bespoke view unaffected
  - [x] **D-change-designnote-free** — `CHANGE-109` + `46-*.md` numbers free
- [x] **Prong 3 — schema verify**: N/A (no DB table / migration / ORM column — Cat 12 telemetry only)
- [x] **D-baselines** — pytest 2859+5skip · wire 26 · Vitest 920 · mockup 51 · mypy 0/380 · v2 lints 21 (FE/mockup UNTOUCHED this sprint; full re-verify Day-2 gate)
- [x] **Catalog drift** — progress.md Day-0 table (all D-rows)
- [x] **Go/no-go** — proceed if scope shift ≤ 20%

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-142-otel-genai-semconv` (from `main` `3e9d069e`)

---

## Day 1 — Mapping module + tracer integration (US-1/US-2)

### 1.1 `_genai_semconv.py` pure mapping module
- [x] **`STOP_REASON_TO_FINISH_REASON` + `SPAN_TYPE_TO_OPERATION` + `ATTR_MAP` + `to_genai_span()` + `assert_genai_conformant()`**
  - DoD: `to_genai_span` remaps GenAI span names (`chat {model}` / `execute_tool {tool}` / `invoke_agent`), adds `gen_ai.operation.name`, renames mapped attrs, preserves enterprise attrs (category/tenant/user/session/span_type) + passes unmapped through; pure (no I/O); finish_reason → 1-element `gen_ai.response.finish_reasons` via the stop-reason map
  - Verify: `test_to_genai_span_*` + `test_stop_reason_map_covers_all_enum` green
- [x] **File header (Cat 12) + WHY section comment (translation-at-tracer rationale + dual-view)**
  - DoD: header per `.claude/rules/file-header-convention.md`; Related → 17.md §Contract 12 + design note 46

### 1.2 `OTelTracer._span_cm` start+close apply
- [x] **Apply `to_genai_span` at span START (name + attrs) + CLOSE (re-read caller ref → `set_attributes`)**
  - DoD: START remaps name + static attrs; CLOSE (in existing `finally`, span open) re-reads the ORIGINAL `attributes` ref → translate → `otel_span.set_attributes(...)` (brings out post-response usage + finish_reason); NoOpTracer unchanged; mapping is OTelTracer-only (dual-view)
  - Verify: synthetic-span-through-real-InMemoryExporter test asserts gen_ai.* on exported span

### 1.x partial gate
- [x] black/isort/flake8 clean + mypy `src` 0/380 + LLM-SDK-leak clean (mapping is pure str, no native import)

---

## Day 2 — loop.py 1-line + conformance harness + CI tests (US-3/US-4)

### 2.1 loop.py finish_reason (1 line, B2)
- [x] **`loop.py:2476+` add `llm_attrs["finish_reason"] = response.stop_reason.value`** (ONLY loop.py edit)
  - DoD: post-response, before span close; MHist + Related updated; no other loop.py change
  - Verify: conformance test sees `gen_ai.response.finish_reasons` on the chat span

### 2.2 Conformance harness `benchmark_otel_conformance.py`
- [x] **Real `TracerProvider` + `InMemorySpanExporter` harness; synthetic default (CI-safe) + `--real` Azure-gated loop drive; MD+JSON report**
  - DoD: drives OTelTracer through representative spans, reads exported spans, runs `assert_genai_conformant` per span, conformance ratio; `--real` direct-constructs DB-less loop (mirrors `benchmark_pass_k.py`); report → `benchmark_reports/` (gitignored)
  - Verify: `python scripts/benchmark_otel_conformance.py` (synthetic) exits 0 with conformance report

### 2.3 Corpus + CI tests
- [x] **`otel_conformance_cases.yaml` (required gen_ai.* keys per span kind) + `test_genai_semconv.py` (mapping fns + synthetic real-InMemoryExporter conformance + importlib harness smoke, NO Azure)**
  - DoD: covers chat/tool/loop span kinds; token-bug-fix asserted (usage tokens ON exported span); finish_reasons asserted; importlib idiom mirrors `test_benchmark_pass_k.py`
  - Verify: `pytest tests/unit/agent_harness/observability/test_genai_semconv.py` all green without Azure

### 2.x Full gate
- [x] mypy `src` 0/380 · v2 lints 21/21 (incl. llm_sdk_leak) · backend pytest 2859 + new green (note pre-existing `AD-Billing-Outbox-Drain-Test-Flake` Risk Class C — passes in isolation) · black/isort/flake8 clean · LLM-SDK-leak clean · Vitest/mockup/build UNTOUCHED (no FE)
- [x] Existing `test_observability_coverage.py` + `test_tracer.py` green UNMODIFIED (dual-view contract)

---

## Day 3 — Drive-through (US-5) — real OTel SDK + real Azure loop (pure-infra; CATCH = harness, NOT gate-only)
_(Pure-infra telemetry schema → the real-OTel-SDK conformance run over the REAL loop IS the drive-through, #135/#137/#138 "CATCH = the harness" pattern. No UI; explicitly "real-SDK-verified".)_

### 3.1 Clean env (Risk Class E)
- [x] Standalone harness invocation (no long-running server; direct-construct DB-less loop per 57.141 D-loop-run-noDB); `.env` Azure creds (`set -a && source ../.env && set +a`); `build_azure_model_profile` → real gpt-5.2 client

### 3.2 Drive-through (real OTel SDK + real Azure)
- [x] Run `benchmark_otel_conformance.py --real` (real Azure gpt-5.2, OTelTracer→InMemorySpanExporter) — the ACTUAL production-path `chat` span exported
- [x] **THE verdict**: exported `chat` span carries `gen_ai.operation.name=chat` + `gen_ai.request.model` + `gen_ai.usage.input_tokens`/`output_tokens` (latent bug FIXED) + `gen_ai.response.finish_reasons`; `execute_tool` span carries `gen_ai.tool.name` (if a tool fires); conformance ratio reported
- [x] Report MD+JSON → `artifacts/otel-conformance-verdict.{md,json}` (tracked; `benchmark_reports/` gitignored); verdict table + reading + AP-4 check → progress.md Day 3

---

## Day 4 — CHANGE-109 + design note 46 + closeout

### 4.1 CHANGE-109 + design note
- [x] **`CHANGE-109-otel-genai-semconv.md`** (gap + reframe + translation-at-tracer + token-bug fix + drive-through verdict + AD closed)
- [x] **Spike design note `46-otel-genai-semconv-design.md`** (8/8-point gate; §3 cross-category N/A — reuses Tracer ABC, no new contract; pin CNCF semconv snapshot date; document dual-view contract)

### 4.2 Closeout
- [x] retrospective.md Q1-Q7 + calibration (`otel-genai-semconv-spike` 0.60, 1st data point → KEEP / re-point if out of band)
- [x] Final gate sweep: mypy src 0/380 · pytest 2859+new · v2 lints 21 · black/isort/flake8 clean · LLM-SDK-leak clean · Vitest/mockup/build UNTOUCHED
- [x] Navigators: CLAUDE.md Current-Sprint + Last-Updated · MEMORY.md pointer + subfile · next-phase-candidates (CLOSE research #5; log deferred `AD-Observability-Provider-Attr-Phase58` + `AD-Observability-Content-Capture-OptIn-Phase58`; next #7) · sprint-workflow matrix (`otel-genai-semconv-spike` row)
- [x] Anti-pattern self-check (retro Q5): AP-2/3/4/6/8/11 no violations; v2 lints 21/21
- [ ] **Commit** (local DONE) → ⏳ PR push + open → CI → merge: PENDING USER CONFIRMATION (push is outward-facing) → post-merge status flip after gh-verified MERGED
