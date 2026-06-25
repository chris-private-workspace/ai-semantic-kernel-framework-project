# Sprint 57.144 Plan — Cat 2 tool-description lint + structured-error reflection

**Summary**: Closes research opportunity #7 `AD-Tool-Description-Lint-Reflection` (the LAST canonical research item; #6/#3/#8/#4/#1/#2/#5 all CLOSED). Two orthogonal halves in one spike: **Half A** ships a `check_tool_descriptions.py` CI lint detector (non-empty + min-length + param-level descriptions + no placeholders) — a guardrail against tool-description rot (current descriptions are already mostly good, so the value is preventing regression, NOT the anecdotal ~40% speedup). **Half B** is evidence-first: a pure `classify_tool_error` taxonomy (invocation / parameter / wrong-tool / failed-API) wired into the Cat 2 executor to enrich the failure observation the LLM sees, gated by an env lever (default decided by an A/B harness verdict), with FULL coverage including a ~3-5 line `loop.py:3023-3030` refactor for the rare executor-itself-raises path. Drive-through = a real-Azure A/B benchmark (`benchmark_tool_error_reflection.py`); this is a pure-backend/eval spike with NO user-driven UI surface (gate-only + real-Azure harness verified, explicitly NOT a chat-v2 UI drive-through). A spike → produces a design note (8-point gate).

**Status**: Approved-to-execute (user selected #7 via 2026-06-25 directive; scope A1 both-halves-one-spike + B2 full-coverage-with-loop.py-refactor via AskUserQuestion 2026-06-25; defaults C1 env-lever-evidence-driven + D1 lint-detector-not-register-time).
**Branch**: `feature/sprint-57-144-tool-desc-lint-reflection`
**Base**: `main` HEAD `74555317` (Sprint 57.143 flip PR #340 merged)
**Slice**: closes `AD-Tool-Description-Lint-Reflection` (research #7, standalone — last canonical item).
**Scope decisions**: (a) both halves in one spike — Half A = certain delivery (lint), Half B = measure-then-default; (b) Half B FULL coverage = executor enrich (dominant path) + `loop.py:3023-3030` refactor (rare executor-raises path); (c) Half B default = env-gated, A/B verdict decides; (d) Half A = CI lint detector (AST), not register-time validation.

---

## 0. Background

### The gap (`AD-Tool-Description-Lint-Reflection`, research #7)

Two missing Cat 2 capabilities surfaced by `ai-agent-harness-consolidated-analysis-20260622.md` §2.3 / §2.4:
- **(A)** No tool-description quality check anywhere — `ToolSpec.description` is a bare `str` accepted as-is at register time (no non-empty / length / param-description gate). Research §2.3: rewriting flawed tool descriptions cut task completion ~40% (single Anthropic anecdotal point, hedged 🟡).
- **(B)** Tool failures feed back to the LLM as an ad-hoc error string with no structured diagnosis. Research §2.4: structured-error reflection (taxonomy invocation / parameter / wrong-tool / failed-API) improves retry (BFCL v3 🟢 — but partly RL-training-derived, so prompt-only gain is uncertain → measure before defaulting on).

### Why it matters (the missing capability)

Half A is a regression guardrail: as new tools land (skills, subagent, task primitive all added tools recently), nothing stops a future tool shipping a one-line stub like `echo_tool`'s "Test-only built-in" — a thin description measurably hurts tool selection. Half B turns an opaque "Error: <repr>" into an actionable diagnosis ("parameter error: missing required field 'query'") so the LLM self-corrects in fewer turns — but only if the (RL-confounded) gain holds for V2's prompt-only regime, which is exactly what the A/B harness settles.

### Root cause (recon code read, file:line; ALL re-verified §checklist 0.1)

| Layer | Reality (on `main` HEAD `74555317`) | Anchor |
|-------|-------------------------------------|--------|
| ToolSpec.description unvalidated | `description: str` bare; register validates `input_schema` schema only, never description | `_contracts/tools.py:92`, `tools/registry.py:51-74` |
| No description lint | 10 detectors under `scripts/lint/`; none touch descriptions | `scripts/lint/run_all.py:60-85` |
| Dominant failure path = pure Cat 2 | handler raises → executor catches → `ToolResult(success=False, error=str(exc), error_class="mod.Cls")` | `tools/executor.py:218-243` |
| Loop soft-failure = classify + append (no content rebuild) | `if not result.success` → `classify_by_string(result.error_class)`, then appends the executor's `result` | `loop.py:3044-3055` |
| Rare failure path = loop self-builds content (the B2 target) | executor ITSELF raises → loop builds `content=f"Error: {exc!r}. Please adjust your approach."` (no error_class) | `loop.py:3023-3030` |
| Param-error source for taxonomy | schema mismatch → `"{path}: {message}"`; `_fail` covers unknown-tool / permission / rate-limit | `tools/executor.py:342-352`, `:354+` |
| Cat 8 ErrorClass is orthogonal | TRANSIENT/LLM_RECOVERABLE/HITL/FATAL = retry decision, NOT fix-diagnosis | `error_handling/_abc.py:30-36`, `retry.py:56-82` |

→ The fix: (A) add an AST lint detector over the tool/skill/subagent spec files; (B) add a pure taxonomy classifier consumed at the executor (dominant path, zero loop.py) AND refactor the rare loop.py path to call it (B2 full coverage); gate B behind an env lever whose default the A/B harness sets.

### The design (Half A = AST detector; Half B = pure classifier + executor enrich + loop.py refactor + env lever + A/B harness)

```
# Half A — scripts/lint/check_tool_descriptions.py  (mirror check_llm_sdk_leak.py)
find_violations(root): for *.py → ast.parse → find ast.Call to `ToolSpec(...)`
  → check description kwarg: present, non-empty, >= MIN_LEN, no placeholder (TODO/FIXME/...)
  → walk input_schema dict literal → each property has a non-empty description
  → allow-list: echo_tool / note_tool (test-only) exempt
main(--root) exit 0/1 ; pytest mirror in tests/unit/scripts/lint/

# Half B — agent_harness/tools/_error_taxonomy.py  (pure)
classify_tool_error(error_class: str|None, error_msg: str, schema_error: bool) -> ErrorTaxonomy
  schema/validation → PARAMETER ; unknown tool → WRONG_TOOL
  handler exc (network/timeout error_class) → FAILED_API ; else → INVOCATION
render_reflection(taxonomy, error_msg) -> str   # "parameter error: <path>: <msg>. Fix and retry."

# executor.py — enrich the failure ToolResult.content with render_reflection(...) when lever on
# loop.py:3023-3030 — refactor: build content via render_reflection(classify_tool_error(...)) (B2)
# env lever CHAT_TOOL_ERROR_REFLECTION (default off until A/B verdict)
# benchmark_tool_error_reflection.py — real-Azure A/B: reflection on/off → next-turn fix-rate + tokens
```

WHY this design over register-time validation (Half A) + emit-at-loop (Half B): a CI lint matches the existing 10-detector pattern and exempts test tools cleanly; the taxonomy lives in one pure module so both the executor (dominant) and the loop (rare) consume one source — no scattered classification.

### Ground truth (recon head-start — code read on `main` HEAD `74555317`; ALL re-verified §checklist 0.1)

- `tools/executor.py:218-243` — the dominant handler-exception → ToolResult synthesis (content="", error=str(exc), error_class set).
- `loop.py:3044-3055` — soft-failure appends the executor's `result` (so enriching `result.content` in the executor reaches the LLM with zero loop edit).
- `loop.py:3023-3030` — the ONLY self-built content path (rare; B2 refactor target).
- `scripts/lint/check_llm_sdk_leak.py` — the detector template (find_violations / NamedTuple / main(--root) exit 0/1).
- `backend/scripts/benchmark_correction_hygiene.py` — the A/B harness template (load_cases / build_* / run_arm / build_report pure / main builds Azure profile; 5pp materiality; CI-safe MockChatClient unit test + `RUN_AZURE_INTEGRATION=1` real run).
- `scripts/lint/run_all.py:60-85` — where the new detector registers (+ note run_all may be stale; v2 lints now also under `tests/unit/scripts/lint/`).

**Baselines (Sprint 57.143 closeout; re-verify Day-0)**: pytest 2881 +5skip · mypy src 0/381 · Vitest 922 · wire 26 · run_all LINTS **10 scripts** (aggregate "v2 lints 21" counts sub-assertions/pytest-lints differently — re-verify exact aggregate at Day-2 gate). [Day-0 D-runall-wiring RESOLVED: new detector = 11th LINTS entry.]

### STALE / drift findings (Day-0; full detail → progress.md — placeholder, filled in §checklist 0.1)

- **D-tool-message-field** — confirm which `ToolResult` field the loop renders into the LLM-visible tool message on soft-failure (`content` vs `error`); design enrichment to write the field the LLM actually sees (grep loop tool-message construction).
- **D-runall-wiring** — `scripts/lint/run_all.py` may be stale; confirm whether the new detector wires into `run_all.py` AND/OR a `tests/unit/scripts/lint/` pytest; mirror the live mechanism.
- **D-toolspec-call-shape** — confirm `ToolSpec(...)` is always a direct call with a literal `description=` kwarg (not built via a helper/var) across all tool files, so the AST detector sees them; note any indirect construction.
- **D-retry-line** — re-verify `retry.py` ErrorClass/matrix line range (Explore saw 56-82; consolidated-analysis cited 71-82).
- **D-baselines** — re-verify the closeout baselines above.

## 1. Sprint Goal

Ship Half A (a passing `check_tool_descriptions.py` detector + pytest, run_all LINTS 10→11) and Half B (a pure taxonomy classifier consumed at the executor + a B2 loop.py refactor + an env lever + an A/B harness), proven by: all gates green; the detector runs clean on real spec files (test tools exempt); and a **real-Azure A/B drive-through** (`benchmark_tool_error_reflection.py`) producing a go/no-go verdict on the reflection default. This is a pure-backend/eval spike — NO chat-v2 UI surface; verification is gate + real-Azure harness (explicitly stated "gate-only + real-SDK harness", never implied as a UI drive-through). Produces CHANGE-111 + a spike design note (8-point gate).

## 2. User Stories

- **US-1** (Half A — lint): 作為平台維護者，我希望一個 CI lint 強制每個工具有非空、足夠長、含 param 描述的 description，以便未來新工具不退化成一句話 stub。
- **US-2** (Half B — taxonomy): 作為 agent loop，我希望工具失敗時拿到結構化診斷分類（parameter / wrong-tool / failed-API / invocation），以便 LLM 下一輪精準修正而非盲試。
- **US-3** (Half B — full coverage): 作為維護者，我希望 dominant（執行器）與 rare（執行器自身拋）兩條失敗路徑都走同一個 Cat 2 分類來源，以便診斷一致、無殘留路徑。
- **US-4** (Half B — evidence + lever): 作為決策者，我希望一個 real-Azure A/B harness 量 reflection on/off 的 next-turn 修復率與 token 成本，以便由證據（非假設）決定 env lever 的 default。
- **US-5** (drive-through + closeout): 作為維護者，我希望跑真 Azure A/B 得到 go/no-go verdict + CHANGE-111 + 設計筆記，關閉最後一個 canonical research item。

## 3. Technical Specifications

### 3.0 Architecture (backend + scripts/lint only; NO frontend / NO migration / NO wire event / NO codegen)

```
NEW   scripts/lint/check_tool_descriptions.py                         # Half A AST detector
NEW   backend/tests/unit/scripts/lint/test_tool_descriptions.py       # Half A pytest mirror
NEW   backend/src/agent_harness/tools/_error_taxonomy.py              # Half B pure classifier + render
NEW   backend/scripts/benchmark_tool_error_reflection.py             # Half B real-Azure A/B harness
NEW   backend/tests/fixtures/tools/tool_error_reflection_cases.yaml  # A/B corpus
NEW   backend/tests/unit/.../test_error_taxonomy.py                  # taxonomy + enrich unit tests
NEW   backend/tests/unit/scripts/test_benchmark_tool_error_reflection.py  # CI-safe harness test (MockChatClient)
EDIT  backend/src/agent_harness/tools/executor.py                    # enrich failure ToolResult.content (lever-gated)
EDIT  backend/src/agent_harness/_contracts/tools.py                  # ToolResult += error_taxonomy: str|None (optional)
EDIT  backend/src/agent_harness/orchestrator_loop/loop.py            # :3023-3030 refactor → render_reflection (B2)
EDIT  scripts/lint/run_all.py (and/or pytest wiring)                 # register check_tool_descriptions (per D-runall-wiring)
UNTOUCHED  error_handling/* (Cat 8 ErrorClass orthogonal) · registry.py (D1: lint not register-time) · frontend/*
```

### 3.1 Half A — tool-description lint (US-1) — `scripts/lint/check_tool_descriptions.py`
- Mirror `check_llm_sdk_leak.py`: `find_violations(root) -> list[Violation]`, `main(--root)` exit 0/1, NamedTuple `Violation(file, lineno, tool_name, reason)`.
- AST: `ast.parse` each `*.py`; find `ast.Call` whose func resolves to `ToolSpec`; check the `description` keyword (`ast.Constant` str → non-empty, `>= MIN_DESCRIPTION_LEN`, no placeholder token); if `input_schema` is a dict literal, walk `properties` → each must have a non-empty `description`.
- Allow-list test-only tools (`echo_tool`, `note_tool`) via a constant set (documented WHY).
- Wire into the live lint runner per D-runall-wiring (run_all.py LINTS list + `--root backend/src`).

### 3.2 Half B — error taxonomy (US-2) — `agent_harness/tools/_error_taxonomy.py`
- Pure module (no I/O, no LLM): `class ErrorTaxonomy(str, Enum)` = PARAMETER / WRONG_TOOL / FAILED_API / INVOCATION / UNKNOWN.
- `classify_tool_error(*, error_class: str|None, error_msg: str, is_schema_error: bool) -> ErrorTaxonomy`: schema/validation → PARAMETER; unknown-tool / not-registered → WRONG_TOOL; network/timeout/connection `error_class` → FAILED_API; generic handler exc → INVOCATION; nothing matches → UNKNOWN.
- `render_reflection(taxonomy, error_msg) -> str`: a short actionable observation (e.g. "parameter error: query: 'query' is a required property. Provide it and retry.").

### 3.3 Half B — executor enrich (US-2) — `tools/executor.py` + `_contracts/tools.py`
- `ToolResult += error_taxonomy: str | None = None` (optional field; ABC signature unchanged; design note records).
- In the handler-exception path (`:236-243`) and the schema/validation `_fail` path: when the env lever is on, set `error_taxonomy` + enrich `content` (the LLM-visible field per D-tool-message-field) with `render_reflection(...)`.
- Lever read once (module-level `_reflection_enabled()` reading `CHAT_TOOL_ERROR_REFLECTION`, the 57.109 `_env_*` pattern); default off until A/B verdict.

### 3.4 Half B — loop.py rare-path refactor (US-3) — `loop.py:3023-3030`
- Replace the hard-coded `content=f"Error: {exc!r}. Please adjust your approach."` with `content=render_reflection(classify_tool_error(error_class=..., error_msg=repr(exc), is_schema_error=False), repr(exc))` when the lever is on (else byte-identical to today). ~3-5 lines; import from Cat 2 `_error_taxonomy` (allowed: loop is Cat 1 consuming Cat 2 public surface — confirm category-boundaries Day-0).

### 3.5 Half B — A/B harness (US-4) — `benchmark_tool_error_reflection.py`
- Mirror `benchmark_correction_hygiene.py`: `load_cases(yaml)` + `build_messages(case, arm)` (arm = plain-error vs enriched-reflection observation) + `run_arm` (real LLM produces the next tool_call/answer) + `build_report` (pure: next-turn fix-rate + mean prompt tokens; 5pp materiality) + `main()` builds Azure profile. CI-safe unit test with MockChatClient (NO Azure); real run via `RUN_AZURE_INTEGRATION=1`.
- Corpus `tool_error_reflection_cases.yaml`: cases each = a tool call that fails (missing param / wrong tool name / simulated API error) + the expected corrected call shape for judging.

### 3.x What is explicitly NOT done
- NOT register-time description validation (D1: lint detector chosen).
- NOT a chat-v2 UI surface for the taxonomy (backend observation only; no inspector tab).
- NOT defaulting reflection ON without the A/B verdict (C1).
- NOT touching Cat 8 ErrorClass / retry matrix (orthogonal).
- NOT param-description AUTO-FIX (lint reports, doesn't rewrite).

### 3.y Validation (US-1..US-5)
Gates: mypy `src` 0/381 (+ new files) · run_all LINTS 10→11 (new detector green; aggregate re-verify) · pytest 2881+new · Vitest 922 (unchanged — no FE) · `npm run lint && npm run build` clean (NO `--silent`; FE untouched so trivially clean) · black/isort/flake8 clean · LLM-SDK-leak clean (taxonomy is pure str, no SDK). Plus §3.5 real-Azure A/B drive-through (the spike's CATCH; gate-only + real-SDK, explicitly NOT a UI drive-through).

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 1 | `scripts/lint/check_tool_descriptions.py` | NEW |
| 2 | `backend/tests/unit/scripts/lint/test_tool_descriptions.py` | NEW |
| 3 | `backend/src/agent_harness/tools/_error_taxonomy.py` | NEW |
| 4 | `backend/scripts/benchmark_tool_error_reflection.py` | NEW |
| 5 | `backend/tests/fixtures/tools/tool_error_reflection_cases.yaml` | NEW |
| 6 | `backend/tests/unit/agent_harness/tools/test_error_taxonomy.py` | NEW |
| 7 | `backend/tests/unit/scripts/test_benchmark_tool_error_reflection.py` | NEW |
| 8 | `backend/src/agent_harness/tools/executor.py` | EDIT |
| 9 | `backend/src/agent_harness/_contracts/tools.py` | EDIT |
| 10 | `backend/src/agent_harness/orchestrator_loop/loop.py` | EDIT (3023-3030 refactor) |
| 11 | `scripts/lint/run_all.py` | EDIT (register detector as 11th; per D-runall-wiring) |
| 12-13 | `agent_harness/tools/{memory_tools,todo_tools}.py` | EDIT (param descriptions — 9 of the 40; Day-1 D1-40-real-gaps, user-approved) |
| 14-18 | `business_domain/{audit_domain,correlation,incident,patrol,rootcause}/tools.py` | EDIT (param descriptions — 31 of the 40; user-approved scope expansion) |
| — | `backend/src/agent_harness/tools/registry.py` | **UNTOUCHED** (D1) |
| — | `backend/src/agent_harness/error_handling/*` | **UNTOUCHED** (Cat 8 orthogonal) |
| — | `frontend/*` | **UNTOUCHED** |

## 5. Acceptance Criteria

1. `check_tool_descriptions.py` runs clean on `backend/src` (test tools exempt) + the pytest mirror passes; run_all LINTS 10→11.
2. `classify_tool_error` + `render_reflection` are pure + unit-tested across all 5 taxonomy cases; executor enrich reaches the LLM-visible field (D-tool-message-field) when lever on, byte-identical when off.
3. `loop.py:3023-3030` rare path produces the same structured reflection as the executor dominant path when the lever is on; byte-identical to today when off.
4. The env lever `CHAT_TOOL_ERROR_REFLECTION` defaults off; the A/B harness verdict is recorded; default flipped to on ONLY if gain ≥ materiality threshold.
5. **Real-Azure A/B drive-through PASS** — `benchmark_tool_error_reflection.py` runs against real Azure, reports next-turn fix-rate + token delta per arm, produces a go/no-go verdict; recorded in progress.md (gate-only + real-SDK harness, explicitly NOT a UI drive-through).
6. `AD-Tool-Description-Lint-Reflection` CLOSED; CHANGE-111 + spike design note (8-point gate); calibration recorded; navigators + next-phase-candidates updated; rare-path / future ADs logged.

## 6. Deliverables

- [ ] US-1 `check_tool_descriptions.py` detector + pytest mirror + run_all wiring
- [ ] US-2 `_error_taxonomy.py` pure classifier + executor enrich + `ToolResult.error_taxonomy`
- [ ] US-3 `loop.py:3023-3030` B2 refactor (rare path → shared classifier)
- [ ] US-4 `benchmark_tool_error_reflection.py` A/B harness + corpus + CI-safe test + env lever
- [ ] US-5 real-Azure A/B verdict + CHANGE-111 + design note + closeout

## 7. Workload Calibration

- Scope class **`tool-reflection-and-lint-spike` 0.60** (NEW class, 1st data point; anchored to `guardrail-restrict-spike` 0.60 (57.137) + `verification-context-hygiene-spike` 0.60 (57.136) — Cat 2 structural-guardrail spike + measurement harness + env-gated lever + drive-through; UPPER edge of the 0.60 family ∵ it ALSO ships a Half A lint detector + a B2 loop.py refactor. Per the 57.137 lesson, the real-code core (detector + pure classifier + executor enrich + loop refactor + ~150-line harness + fixtures + tests) holds the 0.60 — this is NOT a tiny-code full-ceremony 0.85 re-point).
- **Agent-delegated: no** (parent-direct; needs careful loop.py + cross-category reasoning + AST detector authoring, not mechanical fan-out — consistent with 57.136-143 all parent-direct). `agent_factor` 1.0 → 3-segment form.
- Bottom-up est ~11.5 hr (Half A detector+test ~2 · taxonomy+test ~1.5 · executor enrich+ToolResult ~1.5 · loop.py B2 refactor ~1 · A/B harness+corpus+CI test ~3 · env lever ~0.5 · drive-through+docs ~2) → class-calibrated commit ~6.9 hr (mult 0.60). Day-4 retro Q2 verifies.

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| AST detector misses indirect `ToolSpec(...)` construction (var/helper) | D-toolspec-call-shape Day-0 grep; if any indirect, document + scope detector to direct-literal specs + note residual |
| Enrich writes the wrong ToolResult field (LLM doesn't see it) | D-tool-message-field Day-0 verify which field renders to the LLM; write that field |
| Real-Azure A/B content-filter / non-determinism (57.130/57.136 family) | use a soft, innocuous error corpus (no jailbreak-trippy text); harness reproduces message construction without full loop (mirrors correction-hygiene); CI-safe MockChatClient for the deterministic test |
| run_all.py stale → detector not actually run in CI (Risk Class — silent lint) | D-runall-wiring Day-0; wire into the LIVE mechanism (run_all AND/OR pytest); confirm it executes |
| loop.py cross-category import of Cat 2 `_error_taxonomy` flags lint | Day-0 confirm category-boundaries allows Cat 1 → Cat 2 public surface (loop already imports ToolResult); import the public symbol |
| Test isolation (module-level lever / singleton) | Risk Class C — read env per-call or reset in fixture; no module-level cached lever state |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- Auto-rewrite of flawed descriptions (LLM-assisted) → `AD-Tool-Description-AutoFix-Phase58`.
- Surfacing the taxonomy in a chat-v2 inspector → `AD-Tool-Error-Taxonomy-UI-Phase58`.
- Per-tenant reflection policy (if A/B says default-on but some tenants want off) → fold into config-tiering family if demanded; OUT now (anti-AP-6).
- Register-time description validation (D2 alternative) → not pursued.
