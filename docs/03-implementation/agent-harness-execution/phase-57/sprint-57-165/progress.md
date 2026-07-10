# Sprint 57.165 Progress — LLM-assisted `--fix` for the tool-description lint

Plan: `../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-165-plan.md`
Checklist: `../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-165-checklist.md`

---

## Day 0 — Plan-vs-Repo Verify (三-prong PRE-verify) — 2026-07-10

> **Sequencing note**: This Day-0 三-prong was run as a PRE-verify against current repo reality while Sprint 57.164 is still PR-pending (`107148e7`, not merged). The sprint has NOT branched or started code. The FINAL Day-0 baseline re-confirm + branch creation (§0.2) happen when 57.165 actually starts — i.e. AFTER 57.164 merges + user go-ahead. The content-verify findings below are stable facts about repo structure that 57.164's merge does not change (only the pytest baseline shifts trivially by ~+1).

### Prong 1 — path verify ✅

- EDIT `scripts/lint/check_tool_descriptions.py` — present (57.144 Half A).
- NEW `scripts/lint/_autofix.py` — free (Glob 0 results).
- NEW `tests/unit/scripts/lint/test_tool_description_autofix.py` — free (Glob 0 results).
- `CHANGE-132` slug — free (highest existing = CHANGE-131 tool-error-taxonomy-ui).
- Design note number — **64 free** (60 scheduler / 61 recall-precision / 62 tool-anchored-masking / 63 structural-realcount exist).
- `backend/src/adapters/azure_openai/profile.py` — present (the neutral client build target).

### Prong 2 — content verify ✅ (4/4 GREEN + 2 impl-note refinements)

| D-item | Verdict | Finding / implication |
|--------|---------|-----------------------|
| **D-sys-path-fix** | ✅ GREEN | `adapters.azure_openai.profile` lives at `backend/src/adapters/azure_openai/profile.py`. A top-level `scripts/lint/_autofix.py` resolves it via a lazy `sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend" / "src"))` under `--fix` ONLY. The CI report path never imports it. Fallback (a `backend/scripts/` sibling drafter) NOT needed. No §Risks shift. |
| **D-node-span-avail** | ✅ GREEN | `requires-python = ">=3.11"` → every `ast` node carries `end_lineno`/`end_col_offset`. Spot-checked `memory_tools.py:123,173`: ToolSpec literals are single-call `X: ToolSpec = ToolSpec(name=..., description=(<implicit-concat>), input_schema={<dict>})`. **Nuance for Day-2**: a multi-line `description=("a" "b" "c")` folds to ONE `ast.Constant` whose span covers the inner string literals, NOT the surrounding parens → a replace-splice overwrites the literals and leaves the outer `( )` → still valid Python (`description=(<new single-line>)`). Param values are `ast.Dict` → the missing-`"description"` insert splices a new key. |
| **D-profile-cheap** | ✅ GREEN | `build_azure_model_profile(policy=None) -> ModelProfile` (`profile.py:57`); `.cheap` is a `ChatClient` (`AzureOpenAIAdapter`, or the action instance when no cheap deployment is configured → byte-identical). **Refinement for §3.1**: `ChatClient.chat` is **async** (the benchmarks `await` it), so `draft_description` is `async` and `--fix` runs it via `asyncio.run(...)` (mirror `benchmark_tool_error_reflection.py::_amain`). Impl note only — no scope/acceptance change. |
| **D-runall-untouched** | ✅ GREEN | `scripts/lint/run_all.py:89` entry = `("check_tool_descriptions.py", ["--root", "backend/src"])` (no `--fix`) → the CI gate is byte-identical; `--fix`/`--write` are opt-in and never hit run_all. |

### Prong 3 — schema verify ✅

- N/A — this sprint introduces NO DB table / migration / ORM model / schema field. Confirmed.

### Baselines (reference — re-confirm at actual branch creation post-57.164-merge)

- pytest **3231** (+5 skip) · run_all **11/11** (incl. `check_tool_descriptions`) · mypy `src` **400/0**. wire 26 / Vitest 933 / mockup 51 — this sprint touches NONE of them.
- Expect pytest ~3231-3232 at branch time (57.164 added +1).

### Go / no-go

- **PROCEED** — scope shift ~0%. The 2 refinements (async drafter; implicit-concat parens nuance) are folded into the implementation design; §Acceptance / §Workload / §File Change List unchanged.
- **Gated on**: (1) Sprint 57.164 merging first, (2) user go-ahead to branch + start Day 1. Until then, §0.2 branch + Day 1+ are NOT started.

### Catalog drift findings

- D-sys-path-fix / D-node-span-avail / D-profile-cheap / D-runall-untouched — all GREEN (table above). No drift shifted a §Risks row; 2 impl-note refinements recorded (async `.chat`, implicit-concat span parens).

---

## Day 1 — `--fix` dry-run report + neutral self-validating drafter (US-1) — 2026-07-10

### Branch
- `feature/sprint-57-165-tool-desc-autofix` created from `main` `980b3357` (57.164 merged as PR #385). 57.165 planning files present (untracked, carried over).

### Day-1 drift findings (design refinements — recorded, NOT silent)

| D-item | Finding | Decision |
|--------|---------|----------|
| **D-fold-into-checker** | The plan §3.0 put the `--fix` logic in a NEW sibling `scripts/lint/_autofix.py`. Reading the existing test (`backend/tests/unit/scripts/lint/test_tool_descriptions.py`) shows the checker is loaded via `importlib.util.spec_from_file_location` (by FILE PATH) from under `backend/`, because from `backend/`'s pytest rootdir the top-level `scripts.lint` package is NOT importable. A sibling `_autofix.py` doing `from scripts.lint.check_tool_descriptions import <predicates>` would fail in that importlib context. | **Fold `--fix`/`--write` INTO `check_tool_descriptions.py`** (one module). The test loads the one module by path (as the existing test does) → the drafter/splicer/report are directly testable with a fake client. Backend adapter import stays lazy (only inside `_build_cheap_client()` / `_ensure_backend_on_path()`), so the CI report path (`python … check_tool_descriptions.py --root backend/src`, no `--fix`) imports nothing new + is byte-identical. This is SIMPLER (Karpathy §2) + truly single-sources the violation predicates (no cross-module duplicate). File Change List updated: drop `_autofix.py` NEW; item 1 EDIT grows. |
| **D-test-path** | Plan File Change List said `tests/unit/scripts/lint/test_tool_description_autofix.py` (top-level). Real test dir is `backend/tests/unit/scripts/lint/`. | New test → `backend/tests/unit/scripts/lint/test_tool_description_autofix.py`. |
| **D-3-fix-kinds** | The 3 fixable violation shapes map to 3 kinds: `replace_desc` (a bad string-literal description — tool-level OR param-level empty literal → replace the `ast.Constant` span), `insert_tool_desc` (absent `description=` kwarg → splice a kwarg), `insert_param_desc` (absent param `"description"` key → splice a key). A param whose description is present-but-DYNAMIC (a variable) is flagged by the lint but is NOT statically autofixable (inserting would duplicate the key) → skipped + counted as unfixable in the report. Tool-level dynamic descriptions are already lint-SKIPPED (no violation). | 3 kinds; dynamic-param-desc → skip + report "N unfixable (dynamic)". |
| **D-rich-context** | Instead of reconstructing the LLM context from the AST, pass `ast.get_source_segment(text, call)` (the whole ToolSpec literal) as context — richer + simpler. | Drafter prompt carries the ToolSpec source segment + the specific target (tool / param name). |

### Day-1 tasks — DONE

- **1.1 surface AST node** — `collect_fix_targets(root) -> (list[FixTarget], unfixable_dynamic)` added (reuses the checker's own predicates `MIN_DESCRIPTION_LEN`/`PLACEHOLDER_RE`/`_const_str`/`_dict_get`/`_kwarg`/`_toolspec_calls` → true single-source; carries `ast.get_source_segment` as LLM context). The report path (`find_violations` + no-`--fix` `main`) is byte-identical.
- **1.2 neutral self-validating drafter** — `draft_description(client, target)` async; lazy `from agent_harness._contracts.chat import ChatRequest, Message`; `_clean_draft` (strip quotes + collapse to one line); `_lint_ok` self-validation against the lint's own predicate; retry once with `_RETRY_HINT`; else `NEEDS_MANUAL`. `_build_cheap_client` lazy `build_azure_model_profile().cheap` (Azure only under `--fix`).
- **1.3 `--fix` dry-run report** — `render_report` groups by file, prints drafts + "Source UNCHANGED", counts `<needs-manual>` + dynamic-skipped; `run_fix(root)` collects → (short-circuits if 0, no Azure) → drafts → prints. `main()` gains `--fix` (only; `--write` is Day 2) + cp950 stdout reconfigure.
- **`FixTarget` = `NamedTuple`** (NOT `@dataclass`) — a Day-1 bug: `@dataclass` + `from __future__ import annotations` needs the module in `sys.modules` to resolve annotations, but the importlib file-path test load doesn't register it → `AttributeError` in `dataclasses.py`. NamedTuple (like the existing `Violation`) has no such dependency. Root-caused via the existing checker tests ALSO failing (shared `_load_module`).

### Day-1 gate ✅

- pytest `tests/unit/scripts/lint/` = **38 passed** (13 NEW autofix + 10 existing checker unbroken + 15 other lint). Full-suite count deferred to Day-2/final (baseline 3231 + 13 → ~3244).
- `scripts/` is NOT in the CI lint scope (CI lints `backend/src` + `backend/tests`; mypy `src/ --strict` only). The checker file is formatted to the project 100 standard for consistency; the NEW test (`backend/tests/…`) IS CI-linted → black/isort/flake8 clean.
- lint self-run (no `--fix`): `OK: all ToolSpec descriptions well-formed` (byte-identical). `--fix` wiring smoke on backend/src (0 violations) short-circuits `OK: no fixable…` WITHOUT touching Azure.
- mypy `src` 400/0 UNAFFECTED (all Day-1 changes are outside `src/`).

---

## Day 2 — `--fix --write` position-based splice + idempotency (US-2) — 2026-07-10

### Day-2 tasks — DONE

- **2.1 splicer (3 kinds)** — `apply_fixes(text, targets_and_drafts) -> (new_text, applied_count)`: re-parses the file (one consistent parse), computes a `(start, end, replacement)` op per target via `_splice_op`, applies them **back-to-front** (highest offset first) so an earlier edit never shifts a later span. `_line_starts`/`_offset` convert (lineno, col) → char offset; `_quote` emits a double-quoted single-line literal; `_param_dict` re-finds a param's value dict.
  - `replace_desc` → overwrite the description `ast.Constant` span (tool-level OR empty-param literal). The implicit-concat parens nuance (D-node-span-avail) is handled: the Constant span covers the inner literals → the outer `()` remain valid.
  - `insert_tool_desc` → splice `description=<q>,` after the `name=` value's comma; multi-line indents to `name_kw.col_offset`, single-line inserts inline.
  - `insert_param_desc` → splice `"description": <q>, ` just after the param dict's `{`.
- **2.2 idempotency** — after a `--write`, `collect_fix_targets` finds 0 remaining gaps → a re-run is a no-op (`apply_fixes(text, []) → (text, 0)`). Proven by `test_apply_idempotent`.
- **`--write` wiring** — `main()` gains `--write` (+ `parser.error("--write requires --fix")`); `run_fix(root, *, write)` groups drafts by file, applies, writes, and prints an `⚠ LLM-DRAFTED — review git diff` banner + `<needs-manual>` / dynamic-skipped counts.
- **run_fix orchestration tested WITHOUT Azure** (non-Potemkin) — 3 tests monkeypatch `_build_cheap_client` + `_draft_all`: `test_run_fix_write_applies_across_files` (2 files → both cleared + drafted), `test_run_fix_dry_run_does_not_write` (source untouched + "Source UNCHANGED"), `test_run_fix_no_targets_short_circuits_without_client` (0 targets → never builds the Azure client). The real drafter is Day-3 smoke.

### Day-2 gate ✅

- pytest `test_tool_description_autofix.py` = **24** (13 Day-1 + 8 splice + 3 run_fix) + `test_tool_descriptions.py` **10** unbroken = **34 passed**; whole `tests/unit/scripts/lint/` = 46 passed.
- **run_all 11/11 green** — `check_tool_descriptions.py` (11th lint) still passes with the no-`--fix` path byte-identical; other 10 unaffected.
- black/isort/flake8 clean (100 std; 1 E501 on the run_fix docstring fixed) · lint self-run `OK: all ToolSpec descriptions well-formed` byte-identical · mypy `src` 400/0 UNAFFECTED.
- Each `apply_fixes` test asserts the result `compile()`s (valid Python) + re-collects to 0 targets (fix actually landed).

---

## Day 3 — real-Azure smoke (US-3) — NOT a drive-through — 2026-07-10

> Pure dev/CI tooling, no user-driven UI surface → the Drive-Through Hard Constraint does not apply. This is a real-LLM SMOKE + honest accuracy note (NOT a runtime A/B, NOT a UI drive-through). Fixture lives in the session scratchpad (throwaway, NOT committed).

### Setup + reproduce

- Throwaway fixture `scratchpad/smoke_tools/tools.py` — 2 ToolSpecs with 5 deliberately-stripped gaps covering all 3 fix kinds: `get_incident_details` (missing tool desc + 2 params missing desc) + `close_support_ticket` (`"close it"` too-short desc + 1 param missing desc). Plain lint confirmed exactly 5 violations.
- Reproduce (real cheap-tier, root `.env` auto-loaded by `AzureOpenAIConfig(env_file=".env")` + `AZURE_OPENAI_CHEAP_DEPLOYMENT_NAME` sourced → the `.cheap` tier really is cheap, not the action fallback):
  ```
  set -a; source .env; set +a
  python -m scripts.lint.check_tool_descriptions --fix --root scratchpad/smoke_tools           # dry-run
  python -m scripts.lint.check_tool_descriptions --fix --write --root scratchpad/smoke_tools    # apply
  python -m scripts.lint.check_tool_descriptions --root scratchpad/smoke_tools                  # re-lint → OK
  ```

### Result — 🟢 PASS

- **Dry-run `--fix`**: 5/5 drafts produced by the REAL cheap-tier Azure model, e.g. `insert_tool_desc [get_incident_details] -> "Retrieve detailed information for a specific incident by ID, and set include_timeline to true when you also need its event history."`; `replace_desc [close_support_ticket] -> "Close a support ticket by ticket_id and include a resolution_note when the issue is resolved."`. Source UNCHANGED (dry-run confirmed — file byte-identical after `--fix`).
- **`--fix --write`**: `Applied 5 description(s) across 1 file(s).` + the `⚠ LLM-DRAFTED — review git diff` banner. All 3 splice kinds landed on the real file: `description=` inserted after `name=` (multi-line indent correct); `"description":` inserted into both param dicts; `"close it"` replaced.
- **Re-lint after write → `OK: all ToolSpec descriptions well-formed`** — proves every drafted description cleared the lint's own predicate (self-validation held end-to-end) AND the splices produced valid Python (the lint `ast.parse`s each file).
- **Accuracy (eyeball)**: all 5 descriptions are correct + relevant given the tool name + schema context (e.g. `include_timeline` → "Set this to true to include the incident's event timeline…").

### Honest findings (NOT blockers; the Option-B review gate is exactly for these)

1. **Unicode smart quotes** — the model emitted `incident’s` (U+2019), so the written literal carries a non-ASCII apostrophe. Valid Python (UTF-8 file) + passes the lint, but a reviewer may prefer ASCII. The `⚠ LLM-DRAFTED — review git diff` banner + Option-B `--write` review gate surface exactly this. A future ASCII-normalization of drafts is a possible polish (→ carryover, not this sprint).
2. **Param key ordering** — the splice inserts `"description"` as the FIRST key (`{"description": …, "type": "string"}`); the codebase convention is usually `type` first. Valid + lint-passing; cosmetic. The developer reorders during the git-diff review if desired (or a future polish anchors the insert after the last key).

These confirm the drafter is a genuine first-cut assist with a human accuracy gate (NOT a Potemkin): the tool drafts + self-validates + applies, and the two review gates (dry-run report → `--write` → `git diff`) keep the human in the loop for accuracy/style.
