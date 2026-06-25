# Sprint 57.142 Progress — OTel GenAI semantic-conventions span/attr mapping (research #5)

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-142-plan.md) · [Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-142-checklist.md)

---

## Day 0 — 2026-06-25 — Plan-vs-Repo Verify (三-prong) + Branch

### Three-prong verify (against `main` HEAD `3e9d069e`)

**Prong 1 — path verify** ✅
- NEW free: `observability/_genai_semconv.py` / `scripts/benchmark_otel_conformance.py` / `tests/fixtures/observability/otel_conformance_cases.yaml` / `tests/unit/agent_harness/observability/test_genai_semconv.py` (Glob 0 results)
- EDIT present: `observability/tracer.py` / `orchestrator_loop/loop.py`
- CHANGE-109 free (highest = CHANGE-108); design note 46 free (highest = 45)

**Prong 2 — content verify (drift findings)**

| ID | Finding | Implication |
|----|---------|-------------|
| **D-genai-key-names** | Pinned CNCF subset: `gen_ai.operation.name` / `gen_ai.request.model` / `gen_ai.usage.input_tokens` / `gen_ai.usage.output_tokens` / `gen_ai.response.finish_reasons` / `gen_ai.tool.name`. Spec evolves (`system`→`provider.name`; `prompt_tokens`→`input_tokens`). | GREEN — pin snapshot date in design note 46; avoid unstable keys (cache tokens, provider rename) |
| **D-inmemory-exporter** | `from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter` + `TracerProvider` + `SimpleSpanProcessor` ALL importable on pinned 1.22.0 (probe OK) | GREEN — drive-through + CI conformance unblocked |
| **D-span-cm-finally** | `tracer.py:190-197` — `try/yield/except/finally` is INSIDE `with otel_tracer.start_as_current_span(...) as otel_span:` → `finally` runs while span still open → close-time `set_attributes` lands before span end | GREEN — close-time set_attributes design valid |
| **D-loop-attr-ref** | `loop.py:2430` `llm_attrs={...}`; `:2434` `start_span(..., attributes=llm_attrs)` passes the SAME ref; `:2470-2476` mutates `llm_attrs` post-response | GREEN — close-time re-read of caller ref sees post-response tokens (the latent-bug fix mechanism) |
| **D-existing-obs-tests** | Only `test_real_handler_injects_real_tracer` (`test_chat_category_activation_wiring.py:187`) + `test_platform_tracer_factory.py:37` instantiate real `OTelTracer` — both assert `isinstance`/`is`, NOT span attr keys. `test_observability_coverage.py` uses RecordingTracer (bespoke view). | GREEN — OTelTracer-only gen_ai mapping breaks NO existing test (dual-view contract holds) |
| **D-change-designnote-free** | CHANGE-109 + `46-*.md` free | GREEN |

**Prong 3 — schema verify**: N/A (no DB table / migration / ORM column — Cat 12 telemetry only)

**D-baselines** (Sprint 57.141 closeout, re-verify Day-2 gate): pytest 2859+5skip · wire 26 · Vitest 920 · mockup 51 · mypy 0/380 · v2 lints 21. (FE/mockup UNTOUCHED this sprint.)

### Go/no-go: **GO**
Scope NOT shifted (all assumptions verified clean; slightly REDUCED vs worst case — provider deferred as planned per scope decision (e)). All 6 D-rows GREEN.

### Branch
`feature/sprint-57-142-otel-genai-semconv` created from `main` `3e9d069e`.

### Key design (locked, AskUserQuestion 2026-06-25)
- **B2** allow 1 loop.py line (`llm_attrs["finish_reason"]=response.stop_reason.value`) → `gen_ai.response.finish_reasons` exports.
- **C1** content-capture opt-in DEFERRED → `AD-Observability-Content-Capture-OptIn-Phase58`.
- translation-at-tracer: `_genai_semconv.py` applied in `OTelTracer._span_cm` start+close; dual-view (internal bespoke / exported gen_ai); close-time set_attributes fixes the latent post-response token-loss bug.

---

## Day 1 — 2026-06-25 — Mapping module + tracer integration (US-1/US-2)

- **`_genai_semconv.py`** (NEW, pure, Cat 12): `STOP_REASON_TO_FINISH_REASON` (6 enum values → CNCF finish_reason) + `SPAN_TYPE_TO_OPERATION` (LLM_CALL→chat / TOOL_EXEC→execute_tool / LOOP→invoke_agent) + `ATTR_MAP` (model→`gen_ai.request.model`, prompt/completion_tokens→`gen_ai.usage.input/output_tokens`, tool→`gen_ai.tool.name`) + `to_genai_span()` (pure; renames + name remap + preserves enterprise attrs + passes unmapped through) + `assert_genai_conformant()` (returns violations). Pinned snapshot 2026-06-25.
- **`tracer.py` `OTelTracer._span_cm`** (EDIT): apply `to_genai_span` at START (name + base+caller attrs, caller passed RAW so usage ints survive) + CLOSE (re-read caller ref → `set_attributes`). Close-time path fixes the latent post-response token loss. NoOpTracer unchanged → dual-view.
- Header MHist updated (tracer.py behavioral change).
- **Partial gate**: black/isort clean · flake8 0 (2 MHist E501 trimmed) · **mypy src 0/381** (+1 new module) · LLM-SDK-leak clean (pure str, no native import).

## Day 2 — 2026-06-25 — loop.py 1-line + conformance harness + CI tests (US-3/US-4)

- **`loop.py`** (EDIT, 1 line, B2): `llm_attrs["finish_reason"] = response.stop_reason.value` post-response → `gen_ai.response.finish_reasons` exports. Header MHist updated. ONLY loop.py edit.
- **`benchmark_otel_conformance.py`** (NEW, scripts/): real `TracerProvider` + `InMemorySpanExporter`; `build_capturing_tracer` injects a provider tracer into OTelTracer's lazy cache (NO global set_tracer_provider → CI-safe isolation); `run_synthetic` mirrors the loop's bespoke emission incl. post-response mutation; `--real` direct-constructs the DB-less loop with the capturing tracer injected; `evaluate_spans`/`build_report`; MD+JSON; conformance gate (exit non-zero if non-conformant). Synthetic standalone run: **3/3 conformant, 100%, chat usage+finish_reasons YES, exit 0**.
- **`otel_conformance_cases.yaml`** (NEW): pinned conformance spec (required keys per op + expected-on-completed + forbidden bespoke keys).
- **`test_genai_semconv.py`** (NEW, 18 tests): pure mapping (rename/passthrough/finish_reasons/enum-coverage/no-mutate) + assert_conformant (clean/exempt/bespoke-leak/missing-required/name-prefix) + real-InMemoryExporter synthetic conformance (incl. token-bug-fix proof + actual attr values, `("stop",)` tuple coercion) + corpus-driven. **18 passed**.
- **Full gate**: mypy src 0/381 · flake8/black/isort clean · **pytest 2877 passed + 5 skip** (= 2859 baseline + 18 new; 1 pre-existing `AD-Billing-Outbox-Drain-Test-Flake` Risk Class C — **passes in isolation** re-run) · v2 lint tests pass incl. **llm_sdk_leak 3/3** · existing `test_observability_coverage.py` + `test_tracer.py` green UNMODIFIED (dual-view holds) · Vitest/mockup/build UNTOUCHED (no FE).

## Day 3 — 2026-06-25 — Drive-through (US-5) — real Azure loop + real OTel SDK

### Verdict (real Azure gpt-5.2, OTelTracer → InMemorySpanExporter, "2+2" turn)

| span name | operation | conformant | usage | finish_reasons |
|-----------|-----------|------------|-------|----------------|
| `chat gpt-5.2` | chat | ✅ | ✅ | ✅ |
| `agent_loop.turn` | — (non-GenAI exempt) | — | — | — |
| `invoke_agent` | invoke_agent | ✅ | — | — |

- GenAI spans **2/2 conformant, ratio 100%**, exit 0.
- **THE verdict (observed vs intended)**: the ACTUAL production-path `chat gpt-5.2` span carries `gen_ai.operation.name=chat` + `gen_ai.request.model=gpt-5.2` + `gen_ai.usage.input_tokens`/`output_tokens` (**latent token-loss bug FIXED on the real path** — exactly intended) + `gen_ai.response.finish_reasons` (the B2 1-line). `agent_loop.run` mapped to `invoke_agent`; `agent_loop.turn` correctly passed through bespoke (non-GenAI, exempt). No tool span (no tool call this turn). Matches intended flow exactly.
- **AP-4 check**: not a Potemkin — the spans are REAL (exported via the real OTel SDK from a real Azure loop run), the `gen_ai.*` keys are really present (asserted by the harness + JSON report), the token bug fix is really observable (`chat_has_usage_tokens=true`).
- CATCH = the harness (pure-infra, no UI); real-SDK-verified (NOT gate-only).
- Report → `artifacts/otel-conformance-verdict.{md,json}` (tracked; `benchmark_reports/` gitignored).

