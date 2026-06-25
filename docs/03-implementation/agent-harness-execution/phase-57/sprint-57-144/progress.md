# Sprint 57.144 Progress — Cat 2 tool-description lint + structured-error reflection

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-144-plan.md) · [Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-144-checklist.md)

Closes research #7 `AD-Tool-Description-Lint-Reflection` (last canonical item). Base `main` HEAD `74555317`. Branch `feature/sprint-57-144-tool-desc-lint-reflection`.

---

## Day 0 — 2026-06-25 — Plan-vs-Repo Verify (三-prong) + Branch

### Prong 1 — path verify ✅
- NEW files all free: `scripts/lint/check_tool_descriptions.py` / `agent_harness/tools/_error_taxonomy.py` / `backend/scripts/benchmark_tool_error_reflection.py` (ls → not found, as expected).
- EDIT files all present: `tools/executor.py` / `_contracts/tools.py` / `orchestrator_loop/loop.py` / `scripts/lint/run_all.py`.
- `CHANGE-111` free (highest = CHANGE-110). Design note `48-` free (highest = 47).

### Prong 2 — content verify (drift findings below)
### Prong 3 — schema verify
- N/A — NO DB table / migration / ORM column / RLS this sprint (pure Cat 2 + scripts/lint).

### Drift findings (Day-0)

| ID | Finding (file:line) | Implication | §Risks / §Spec cross-ref |
|----|---------------------|-------------|--------------------------|
| **D-tool-message-field** 🟡 NOTABLE | LLM-visible tool message = `result.content` ONLY — `tool_content = self._tool_result_to_text(result.content)` (`loop.py:3092`); `_tool_result_to_text` (`loop.py:3745-3764`) NEVER reads `error`. The dominant soft-failure path (handler raises → executor `content="", error=str(exc)`, `executor.py:236-243`) therefore feeds the LLM an **EMPTY** observation; `error` only rides the SSE `ToolCallFailed` event (`loop.py:3115-3120`). | Half B enrich MUST write `content`. Doing so ALSO fixes a latent gap (LLM currently sees nothing useful on handler-raised tool failures). The A/B "reflection-off" arm baseline = today's empty/`repr` content. **NO scope shift** (the fix IS the enrichment) — strengthens Half B value. | §3.3 (write `content`), §3.5 (A/B baseline), Acceptance #2 + #5 |
| **D-runall-wiring** ✅ RESOLVED | `scripts/lint/check_*.py` = **10** scripts; `run_all.py` LINTS list = 10 entries (`run_all.py:62-84`) = the LIVE mechanism. Only 5/10 have a `tests/unit/scripts/lint/` pytest mirror. The aggregate "v2 lints 21" (57.142/57.143 baseline) counts differently (sub-assertions / pytest lint tests), NOT 10. | New detector = **11th LINTS entry** in `run_all.py`. **Correct plan/checklist "v2 lints 15→16" → "run_all LINTS 10→11"**; re-verify the aggregate number at Day-2 gate. Adding a pytest mirror = good practice (matches the 5 well-tested detectors), kept in checklist 1.1. | §3.1, §3.y, checklist 1.1 |
| **D-toolspec-call-shape** ✅ RESOLVED | 14 `ToolSpec(` sites: 8 module-level `XXX_SPEC: ToolSpec = ToolSpec(...)` (tools/ + skills/) + 6 function-nested (`subagent/tools.py:82,180,231` + `subagent/modes/as_tool.py:75` + ...). `task_spawn` (`subagent/tools.py:84-88`) uses parenthesized adjacent-string concat = single `ast.Constant`. `ast.Call` walk finds nested calls at any depth. | Detector: check `description` when `ast.Constant` str; SKIP (no false-positive) when dynamic (`ast.JoinedStr` f-string / `ast.Name` / `ast.BinOp`) + count as residual-uncheckable. Verify `as_tool.py:75` + `subagent/tools.py:180,231` description shape Day-1 (may interpolate an agent name → dynamic → skip). **NO scope shift**. | §3.1, §8 Risk row 1 |
| **D-retry-line** ⏳ Day-1 | Explore saw `retry.py:56-82`; consolidated-analysis cited `71-82`. Minor; not load-bearing (Cat 8 untouched). | Re-confirm when reading Cat 8 for the taxonomy-orthogonality design note. NO scope impact. | §0 root-cause table |
| **D-loop-import-boundary** ⏳ Day-1 | `loop.py` already imports `ToolResult` from Cat 2 `_contracts`; Half B adds an import of `tools._error_taxonomy` public symbols (Cat 1 → Cat 2 public surface). | Confirm `check_cross_category_import` allows it when wiring the B2 refactor (Day 2). Likely fine (loop consumes Cat 2 public). NO scope impact. | §3.4, §8 Risk row 5 |

### Baselines (57.143 closeout; re-verify at Day-2 full gate)
- pytest 2881 +5skip · mypy src 0/381 · Vitest 922 (FE untouched this sprint) · wire 26 · run_all LINTS **10 scripts** (aggregate "v2 lints 21" — re-verify exact aggregate at gate).

### Go/no-go → **PROCEED to Day 1**
- All Prong-1 GREEN; Prong-2 = 1 NOTABLE (D-tool-message-field — strengthens Half B, no scope shift) + 2 RESOLVED + 2 minor deferred to Day-1; Prong-3 N/A.
- Scope shift ~0% (only correction: lint-count wording 15→16 → LINTS 10→11). Plan/checklist updated accordingly.

### Day 0 done
- [x] Branch `feature/sprint-57-144-tool-desc-lint-reflection` from `main` `74555317`.
- [x] Three-prong verify + drift catalogued.

---

## Day 1 — 2026-06-25 — Half A lint detector + 40 param fixes + Half B taxonomy

### Half A — `check_tool_descriptions.py` (US-1) ✅
- Wrote the AST detector (mirror `check_llm_sdk_leak`): finds `ToolSpec(...)` calls (any nesting via `ast.walk`), checks `description` (non-empty + `>= MIN_DESCRIPTION_LEN=20` + no UPPERCASE placeholder token) + every `input_schema` property has a non-empty `description`; skips dynamic (f-string / var) descriptions+schemas (no false-positive).
- Wired as the **11th** lint in `run_all.py` LINTS (+ MHist) → **run_all 11/11 green**.
- 10 pytest mirror cases in `tests/unit/scripts/lint/test_tool_descriptions.py` (pass / empty / short / placeholder / lowercase-"todos" regression / missing-param / missing-kwarg / dynamic-skip ×2 / adjacent-concat) — all pass.

### Day-1 discoveries (reshaped Half A)

| ID | Finding | Resolution |
|----|---------|-----------|
| **D1-placeholder-FP** 🐛 | Initial `\b(TODO\|FIXME\|XXX\|TBD)\b` IGNORECASE false-positived on `write_todos` (the English word "todos"/"todo"). | Fixed: UPPERCASE-only match (placeholders are conventionally uppercase; the word "todos" is lowercase). Regression test added. Code-aware-masking lesson (`lint-detector-authoring.md`). |
| **D1-drop-allowlist** ✂️ YAGNI | Plan §3.1 assumed an echo/note allow-list. Reality: echo_tool/note_tool descriptions (~60 chars) + their `text` param descriptions all PASS the bar → no allow-list needed. | Dropped the allow-list (Karpathy §2 — don't build the unneeded). Detector has none. |
| **D1-40-real-gaps** 🟡 SCOPE (user-approved) | The survey claimed memory/etc. params had descriptions — WRONG. The detector found **40 real missing param descriptions**: 9 core harness (`memory_search` ×4, `memory_write` ×4, `write_todos` ×1) + 31 `business_domain` mock tools (audit/correlation/incident/patrol/rootcause). tool-LEVEL descriptions all pass; param-LEVEL widely absent. | **User-approved (AskUserQuestion 2026-06-25): full fix + param-level enforcement.** Added all 40 param descriptions across 7 files (purely additive — every existing key/type/enum/default preserved; verified via `git diff`). Lint now 0 violations. File List 11→18. Synergy with Half B (better param descriptions → fewer `parameter`-class errors). |

- The 40-param fill was delegated to ONE code-implementer agent (bounded mechanical chunk, ~15% of Day-1 — overall sprint stays parent-direct `agent_factor` 1.0). **Parent re-verified independently** (Before-Commit item 7): `check_tool_descriptions --root backend/src` → OK exit 0; `git diff` purely additive (spot-checked memory_tools + incident — `scope` (pre-existing desc) untouched, no key deletions); `black --check` 7 files clean.

### Half B — `_error_taxonomy.py` (US-2 part) ✅
- Pure module (no I/O/LLM/runtime imports): `ErrorTaxonomy` enum (PARAMETER / WRONG_TOOL / FAILED_API / INVOCATION / UNKNOWN) + `classify_tool_error(*, error_class, error_msg, is_schema_error, is_unknown_tool)` (flags-first precedence → exception-class markers → message heuristics → generic) + `render_reflection(taxonomy, error_msg)` (label + raw + actionable guidance).
- 19 pytest cases (each branch + message heuristics + precedence + render + empty-fallback + `.value` stability) — all pass; mypy clean.
- Orthogonal to Cat 8 ErrorClass (retry decision) — documented in module docstring.

### Day 1 gate (partial)
- Half A: run_all 11/11 · 10 lint tests · black/mypy clean. Half B: 19 tests · mypy clean.

### Day 1 done
- [x] Half A detector + 40 param fixes + run_all wiring + pytest mirror.
- [x] Half B taxonomy pure module + tests.

---

## Day 2 — 2026-06-25 — executor enrich + loop B2 refactor + env lever

### Code (US-2 + US-3) ✅
- **`_contracts/tools.py`**: `ToolResult += error_taxonomy: str | None = None` (optional; stores the enum `.value` so the contract takes NO dependency on `tools/_error_taxonomy`).
- **`tools/executor.py`**: NEW `_build_failure(call, *, error, error_class, is_schema_error, is_unknown_tool)` — the single failure-result builder used by BOTH the handler-exception path (236-243) and `_fail` (schema_invalid → parameter; unknown → wrong-tool). Lever ON → enriched `content` (render_reflection) + `error_taxonomy`; OFF → `content=""` + error/error_class only = **byte-identical** to pre-57.144. (D-tool-message-field confirmed the loop renders `content`, not `error` → enriching `content` reaches the LLM AND fixes the prior empty-observation gap.)
- **`tools/_error_taxonomy.py`**: added `tool_error_reflection_enabled()` (reads `CHAT_TOOL_ERROR_REFLECTION` per-call, no cache — Risk Class C; default OFF). Decided in-module env read (sandbox `DOCKER_SANDBOX_IMAGE` precedent) over factory-inject to keep the spike lean; documented WHY (the A/B harness is the deliverable, the live lever is flippable scaffolding).
- **`tools/__init__.py`**: re-export `ErrorTaxonomy / classify_tool_error / render_reflection / tool_error_reflection_enabled` (so loop imports via the PUBLIC package path — D-loop-import-boundary RESOLVED: `from agent_harness.tools import ...` is allowed by `check_cross_category_import`; a private `_error_taxonomy` import would have been a VIOLATION).
- **`loop.py:3023-3036` (B2 full coverage, US-3)**: the rare executor-itself-raises path now routes its synthesized `content` through the SAME `render_reflection(classify_tool_error(...))` when the lever is on; byte-identical (`"Error: …"`) when off.

### Tests ✅
- `test_executor.py` +5: handler-exc OFF byte-identical (content="", error_class set, taxonomy None) / ON enriched (invocation) / unknown-tool ON (wrong_tool) / schema-invalid ON (parameter) / unknown-tool OFF byte-identical.
- `test_loop_error_handling.py` +2 (end-to-end, drive-through ethos): a `_RecordingFakeChatClient` captures the messages the LLM receives → ON: the tool-role message content carries "tool execution failed (external/API error)" (ConnectionError → FAILED_API); OFF: content empty, no taxonomy text leaks. **Proves the LLM actually sees the reflection through the real loop.**

### Day 2 gate ✅
- mypy `src` **382** (was 381 — +`_error_taxonomy.py`) · flake8/black/isort clean · run_all **11/11** · targeted pytest **278 passed +1 skip** (tools + orchestrator_loop ×2 + scripts/lint + business_domain — no regression from the 40 param edits / ToolResult field / executor refactor).

### Day 2 done
- [x] ToolResult field + executor `_build_failure` enrich + env lever + loop B2 refactor.
- [x] Unit + integration tests (on/off, byte-identical-off proven).

---

## Day 3 — 2026-06-25 — A/B harness + real-Azure drive-through (US-4)

### Code ✅
- **`scripts/benchmark_tool_error_reflection.py`** (mirror `benchmark_correction_hygiene.py`): `load_cases` + `observation_for(case, arm)` (plain raw error vs the PRODUCTION `render_reflection(classify_tool_error(...))`) + `build_messages` (provider-neutral 3-message construction, observation = sole variable) + `judge_recovery` (real cheap-tier PASS/FAIL judge) + `run_arm` + `build_report` (pure; fix_rate + completion-tokens; 5pp materiality) + `main()` (Azure profile). mypy errors are scripts-only (import-untyped — same as the other benchmark_*.py; CI gate is `mypy src/`, scripts excluded).
- **`tests/fixtures/tools/tool_error_reflection_cases.yaml`**: 8 innocuous cases across all taxonomy-driving shapes (missing-param / wrong-type / unknown-tool / connection / timeout / generic-NameError / missing-title business tool / SSL).
- **`tests/unit/scripts/test_benchmark_tool_error_reflection.py`**: 13 CI-safe tests (fake ChatClients; load / observation plain-vs-typed / build / judge PASS-FAIL / run_arm all-pass+all-fail / report material+immaterial) — all pass.

### Real-Azure A/B drive-through ✅ (the spike CATCH — gate + real-SDK, NOT a UI drive-through)
Ran `benchmark_tool_error_reflection.py` against real Azure (action tier = answerer, cheap tier = judge), 8 cases × 2 arms × 2 calls = 32 real calls. Report: `artifacts/tool_error_reflection_report.{md,json}`.

| metric | plain | reflection | delta (refl−plain) |
|--------|-------|------------|--------------------|
| fix_rate | 87.50% (7/8) | 87.50% (7/8) | **+0.00%** |
| mean_completion_tokens | 198.9 | 166.9 | **−32.0** |

**Verdict: KEEP `CHAT_TOOL_ERROR_REFLECTION` default OFF** (fix_delta 0.0 < 5% materiality). Honest reading:
- V2's strong action-tier model already recovers from plain errors at 87.5% → little headroom for prompt-only structured guidance to lift the fix rate on this small corpus. **Consistent with the eval's RL-confound hedge**: research §2.4's BFCL gains (16→20%, 6.8→26.4%) were on small RL-TRAINED models; a strong prompt-only model shows no material lift — exactly why we measured before defaulting on.
- Secondary signal: reflection produced **more token-efficient** recoveries (−32 completion tokens) — directional but not a default-flip trigger (token savings alone don't justify a behavior change, mirroring 57.136's rule).
- Same evidence-first outcome shape as 57.136 (#6 keep-default) + 57.138 (#8 opt-in): ship the lever as opt-in, default OFF, verdict recorded.
- Caveat for the design note: the gain may appear on WEAKER models / HARDER corpora (the regime where §2.4's gains were measured) — the lever lets a deployment opt in.

### Day 3 done
- [x] A/B harness + corpus + 13 CI-safe tests.
- [x] Real-Azure A/B verdict (KEEP OFF) + artifact saved.

---

## Day 4 — 2026-06-25 — CHANGE-111 + design note + closeout

### Final gate sweep ✅
- mypy `src` **382** (no issues) · flake8 `src tests` **CLEAN** · run_all **11/11** · pytest **2930 passed +5 skip** (baseline 2881 +49 new) · black/isort clean · check_tool_descriptions 0 violations · LLM-SDK-leak clean · Vitest **922 unchanged** (NO frontend changes this sprint).
- Late catch (Before-Commit item 7): the delegated 40-param agent's descriptions were black-clean + lint-clean but 3 exceeded flake8 E501 (100) — black does NOT break long string-literal lines. Parent re-verify (full flake8 src+tests) caught + fixed them. Lesson → retro Q4 + carried to the Before-Commit discipline.

### Docs ✅
- **CHANGE-111** `claudedocs/4-changes/feature-changes/CHANGE-111-tool-desc-lint-error-reflection.md`.
- **Design note 48** `docs/03-implementation/agent-harness-planning/48-tool-error-reflection-design.md` (8-point gate self-passed — retro Q7).
- **retrospective.md** Q1-Q7 + calibration.
- **Navigators**: CLAUDE.md Current-Sprint + Last-Updated · MEMORY.md pointer + subfile · next-phase-candidates (close `AD-Tool-Description-Lint-Reflection`) · sprint-workflow matrix (`tool-reflection-and-lint-spike` 0.60 row).

### Day 4 done
- [x] CHANGE-111 + design note 48 + retrospective.
- [x] Final gate sweep (all green).
- [x] Navigators updated.
- [ ] Commit → PR (PENDING USER CONFIRMATION — push is outward-facing) → CI → merge → status flip.
