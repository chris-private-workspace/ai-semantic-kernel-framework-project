# Sprint 57.164 Progress — Tool-error taxonomy surfaced in chat-v2 UI

Plan: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-164-plan.md`
Checklist: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-164-checklist.md`

---

# Day 0 — 2026-07-10 — Plan-vs-Repo three-prong verify + Branch

## Prong 1 — path verify ✅

All EDIT targets exist: `executor.py`, `loop.py`, `_contracts/events.py`, `sse.py`, `event_wire_schema.py`, `_error_taxonomy.py`, `types.ts`, `chatStore.ts`, `ToolBlock.tsx` + the 7 test files. REGEN targets exist: `loopEvents.generated.ts`, `events.json`. `CHANGE-131` slug FREE (highest existing = `CHANGE-130`).

## Prong 2 — content verify (drift findings)

| ID | Finding | Verdict | Implication |
|----|---------|---------|-------------|
| **D-parity-two-events-one-type** | `test_event_wire_schema_parity.py` is DATA-DRIVEN: `test_serializer_field_set_matches_registry` (per event) + `test_tool_call_executed_and_failed_share_wire_type` (:187 asserts `set(executed["data"]) == set(failed["data"])`). | ✅ GREEN | Add `error_taxonomy` to the registry + BOTH sse branches (success=None / fail=value) → parity test AUTO-PASSES. **Plan item 15 → UNTOUCHED** (no edit). |
| **D-wire-count-tests** | `test_wire_schema_has_26_entries` asserts `len==26`; `eventSchema.generated.test.ts` asserts `KNOWN_LOOP_EVENT_TYPES.size===26` — both count TYPES, not fields. A FIELD add keeps count 26. | ✅ GREEN | Count asserts stay green. **Plan item 17 (`eventSchema.generated.test.ts`) → UNTOUCHED** (no field snapshot). |
| **D-off-test-flips** | `test_executor.py` has exactly 2 OFF-asserts: `:345` (`test_reflection_off_handler_exception_byte_identical`) + `:404` (`test_reflection_off_unknown_tool_byte_identical`), both `error_taxonomy is None` + `content == ""` + docstring `:327-330`. `test_loop_error_handling.py` grep = **0** `error_taxonomy` matches (57.163 asserts the loop tool-MESSAGE `content`, not the field). | CONFIRMED (+scope shift) | Option B decouple leaves `content` byte-identical (only taxonomy decoupled) → **integration test UNAFFECTED**. `test_executor.py` 2 OFF-asserts flip to `== "invocation"` / `== "wrong_tool"` (content assert kept) + rename "byte_identical"→"content_byte_identical" + docstring. **Plan item 13 → ADD a `ToolCallFailed.error_taxonomy` assertion** (new US-2 coverage, NOT a flip). |
| **D-drivethrough-trigger** 🔑 | `make_default_executor` (`business_domain/_register_all.py:219`) registers echo + 18 business + python_sandbox/web_search/memory/knowledge/skills/todos/subagent. `test_executor.py` confirms 3 `_build_failure`→`ToolCallFailed`(3173)→chip paths: handler-raise→INVOCATION, unknown→WRONG_TOOL, schema-invalid→PARAMETER. The dominant path (executor catches handler exc → success=False) goes STRAIGHT to 3173 (terminate/retry logic lives only in the rare `except Exception`). web_search → Cat-8 FATAL terminate (57.130) so EXCLUDED. | CONFIRMED (Day-3 empirical) | Day-3 trigger candidates ranked: (a) prompt agent to call a business tool on a nonexistent entity → mock 404 → handler failure; (b) forced schema PARAMETER (prompt agent to pass a wrong-typed required arg); (c) a handler-raise tool. Pick first reliable Day-3; record the trigger + taxonomy. |

## Prong 3 — schema verify

N/A — no DB / migration / ORM in scope. ✅

## Baselines (re-measured on `main` HEAD `2614303c`)

- pytest **3235 collected** (= 3230 pass + 5 skip) ✅
- mypy `src` **400 files / 0 issues** ✅
- run_all **11/11 green** (incl. `check_event_schema_sync` — the wire↔codegen sync lint; must stay green after regen) ✅
- wire **26** types ✅
- Vitest 930 / mockup 51 — defer re-confirm to Day 2 (FE untouched until then).

## Go / No-Go — ✅ GO (scope net ~−5%, REDUCTION)

Two planned test-file edits dropped (parity + eventSchema.generated → UNTOUCHED, data-driven/count-based). One refined (integration test = ADD, not flip). No scope expansion; the one open risk (drive-through trigger) is de-risked to 3 ranked Day-3 candidates. Proceed to Day 1.

## 0.2 Branch ✅

`git checkout -b feature/sprint-57-164-tool-taxonomy-ui` from `main` `2614303c`.

---

# Day 1-2 — 2026-07-10 — Backend decouple + wire + FE surface + tests (US-1/2/3)

## US-1 backend decouple (Option B)
- `executor.py:_build_failure` — `classify_tool_error` now runs unconditionally; `content = render_reflection(...) if lever else ""`. `error_taxonomy` always set on failure; LLM-visible `content` byte-identical when OFF. Docstring updated.
- `loop.py:3068` rare path — mirror: `_tax`/`_err_taxonomy` always; only `_err_content` lever-gated.
- `_error_taxonomy.py` — "Consumers" docstring reframed (classification always; lever gates only LLM content) + MHist.

## US-2 wire the taxonomy (additive field on the existing `tool_call_result`; count 26)
- `events.py` `ToolCallFailed += error_taxonomy: str | None = None`.
- `loop.py` 2 emit sites (`_run_turns` + resume) → `error_taxonomy=result.error_taxonomy`.
- `sse.py` BOTH branches (`ToolCallExecuted`=None / `ToolCallFailed`=value) — same field set for parity + MHist.
- `event_wire_schema.py` `tool_call_result += "error_taxonomy": "string | null"` (count 26) + MHist.
- Codegen regen → `loopEvents.generated.ts` `ToolCallResultEvent.data.error_taxonomy: string | null` + `events.json` (git diff confirmed).

## US-3 FE surface
- `types.ts` `ToolBlock += errorTaxonomy?: string | null`.
- `chatStore.ts` `tool_call_result` case → `errorTaxonomy: ev.data.error_taxonomy`.
- `ToolBlock.tsx` — conditional `.badge danger` chip (`data-testid="tool-error-taxonomy"`) in the head row, renders only when present; `styles-mockup.css` UNTOUCHED (byte-identical), no new oklch/hex + MHist.

## Tests
- Backend: `test_executor.py` 2 OFF-asserts flipped (`== "invocation"` / `== "wrong_tool"`, `content == ""` kept) + renamed `..._content_byte_identical` + docstring; `test_sse.py` +2 assertions (fail `failed_api` / success `None`); `test_loop_error_handling.py` +1 test (`ToolCallFailed.error_taxonomy == "invocation"` lever OFF, US-2 wire coverage).
- FE: `chatStore.mergeEvent.test.ts` helper +`error_taxonomy` + 1 capture test + success-null assert; `blocks.test.tsx` +2 (chip present / absent).
- tsc required-field drift (57.116-class): `demoLoopEvents.ts` (2) + `LoopVisualizer.test.tsx` + `chatStore.pauseResume.test.ts` += `error_taxonomy: null`.

## Day 2.x Full gate — ALL GREEN ✅
- mypy `src` **400/0** · run_all **11/11** (incl. `check_event_schema_sync` — codegen↔wire in sync) · black/isort/flake8 clean (2 first-draft MHist E501 fixed) · LLM-SDK-leak clean
- backend pytest **3231 passed, 5 skipped** (+1) · Vitest **933** (+3) · `npm run lint && npm run build` clean (NO `--silent`; jsx-ast-utils TSSatisfies notices pre-existing) · mockup **51** (`styles-mockup.css` byte-identical)

## Notes
- D-parity-two-events-one-type confirmed GREEN: parity test is data-driven → auto-passed once both sse branches + registry carry `error_taxonomy` (item 15 untouched).
- Agent behavior byte-identical: no LLM reads `error_taxonomy` (loop renders `content`); the decouple only adds display metadata to the wire.

## Remaining
- Day 3: drive-through (real chat-v2 + real Azure) — see below.
- Day 4: CHANGE-131 + closeout.

---

# Day 3 — 2026-07-10 — Drive-through (real chat-v2 + Azure gpt-5.2) → 🔴 REACHABILITY FINDING

## Environment
- Docker up (postgres/redis/rabbitmq/qdrant/**mock_services**/jaeger); backend fresh single worker (PID 43828, no orphan — Risk-E clean); frontend :3007; dev-login jamie@acme.com · acme-prod. Lever OFF (Option B — taxonomy should show without it).

## Attempts (real Azure gpt-5.2, session 995960a0 / e50cdab9 / 9659e7ce)
1. **close incident INC-99999** — agent (correctly cautious) called `request_approval` first (HITL gate, MEDIUM/always_ask); after Approve, the `request_approval` DEPRECATED-placeholder returned `pending` so the agent re-explained instead of calling `mock_incident_close`. No failing tool reached. (Bonus: HITL gate + approval flow verified live.)
2. **get incident INC-99999** (read, no HITL) — agent called `mock_incident_get(INC-99999)` → mock **404** (`GET /mock/incident/INC-99999`, curl-confirmed 404) → **`loop_terminated {reason: fatal_exception, detail: "Client error '404 Not Found'"}`** → ToolBlock shows the 57.130 "terminated: fatal_exception" flip, **NOT** the taxonomy chip.
3. **forced schema error** (`mock_incident_get` with `{}`) — agent complied → **`loop_terminated {reason: fatal_exception, detail: "schema mismatch: 'incident_id' is a required property"}`** → again terminated, no chip.

## 🔴 Finding — the chip is NOT reachable on the live chat 主流量 (analogous to 57.163's near-dead branch, but user-facing)

Root cause (code-confirmed `loop.py:3101-3122`): when the executor returns a failed `ToolResult` (the 404 WAS caught → `success=False`, `error_taxonomy="failed_api"` IS set), the loop passes a synthetic exception to `_handle_tool_error` → `classify_by_string(result.error_class)`. For a FATAL class (httpx 4xx observed) → `terminate=True` → **`yield LoopTerminated` + `return` at `:3113-3122`, BEFORE the `ToolCallFailed` emit at `:3172`**. So the taxonomy is computed but the loop terminates before surfacing it. The chip renders ONLY for a NOT-terminate (LLM_RECOVERABLE) failure that reaches `:3172` — and the natural live failure modes (httpx 4xx→FATAL, generic/schema Exception→FATAL, ConnectionError→TRANSIENT→retry-exhausted→terminate) all terminate.

**Honest status**: ③3 wiring is CORRECT (all gates green; unit+integration+FE prove the taxonomy flows to a `ToolCallFailed`→`tool_call_result`→chip). But on the live 主流量 a human hits `loop_terminated` (57.130 flip), not the chip — so this is **gate-verified, NOT drive-through-verified as reachable**. The Drive-Through discipline caught exactly the kind of "wired but a human can't reach it" gap it exists for.

## Decision (user AskUserQuestion 2026-07-10): **(a) Extend ③3 — emit ToolCallFailed before terminate**

### Fix (loop.py, 2 terminate sites)
- **Dominant path (`loop.py:3113`, executor-returned failure — the 404)**: before `yield LoopTerminated`, emit `ToolCallFailed(tool_call_id, tool_name, error=result.error, error_taxonomy=result.error_taxonomy)`.
- **Rare path (`loop.py:3028`, executor-raised — schema/infra)**: mirror — emit `ToolCallFailed(..., error_taxonomy=classify_tool_error(from exc).value)` (the synthetic ToolResult isn't built on this FATAL branch).
- **FE UNCHANGED**: `loop_terminated` only flips `status==="pending"` tools (chatStore.ts:749); the ToolCallFailed already set `status="error"` + `errorTaxonomy`, so `loop_terminated` doesn't touch it → the chip + the real 404 error output PERSIST, and the turn head gets the `terminated` badge. Both visible.
- **Test**: `test_fatal_exception_terminates_loop` += assert a `ToolCallFailed(error_taxonomy="invocation")` is emitted BEFORE the `LoopTerminated` (event-index order).

### 🟢 Drive-through PASS (real chat-v2 + real Azure gpt-5.2, lever OFF, session 3829811e)
Clean backend restart (fresh sole worker PID 52148, 8:19:30 — Risk-E) → re-login → `get incident INC-99999`:
- Loop trace: `tool_call_request mock_incident_get` → span (156ms) → **`tool_call_result … · ERROR`** (my new emit) → `loop_terminated{fatal_exception, 404}`. The `tool_call_result` (ERROR) now precedes `loop_terminated`.
- **ToolBlock renders the chip**: `mock_incident_get` · status **error** · **`tool error taxonomy: failed_api`** (the chip, `title="tool error taxonomy"`) · output = the real `Client error '404 Not Found' …` (NOT "terminated") · turn head `terminated · fatal_exception` badge.
- Label REAL: httpx 404 → FAILED_API → `failed_api`. Lever OFF proves Option B (taxonomy without the reflection lever). Screenshot: `artifacts/sprint-57-164-drivethrough-PASS-taxonomy-chip.png` (+ the pre-fix `…terminated-not-chip.png`).
- **Per-control AP-4 walk**: chip is real (matches classified taxonomy), renders (not a dead label), only on failure (success/pending tools show no chip — Day-2 Vitest confirms), agent behavior unchanged (no LLM read).

### Bonus verified live
- HITL approval gate + Approve flow (close-incident attempt, MEDIUM/always_ask); memory recall (BOREALIS-9 / session summaries injected).

## Day 3 remaining
- Full backend pytest re-run after the loop.py change (background) — expect 3231, 0 fail (loop-core change, no new test count; +1 assertion in an existing test).
