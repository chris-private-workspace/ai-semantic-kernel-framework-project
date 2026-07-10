---
title: 64-tool-description-autofix design note
purpose: Spike-extract design note from Sprint 57.165; documents the verified design of the LLM-assisted `--fix` for the tool-description lint (③2 AD-Tool-Description-AutoFix)
category: V2 extension docs (post-22-sprint era)
created: 2026-07-10 (Sprint 57.165 Day 4 closeout)
sprint_source: 57.165
verified_ratio: ≥ 95% (per 8-Point Quality Gate)
status: Active
---

# 64-tool-description-autofix Design Note (Sprint 57.165 extract)

Closes ③2 `AD-Tool-Description-AutoFix` (the 57.144 carryover; ①/③1/③4 done 57.163, ③3 done 57.164 → Tool range **4/4**). Adds an opt-in `--fix` (LLM-assisted draft) + `--fix --write` (apply) to the Sprint 57.144 tool-description lint. Backend/CI-tooling only; no agent_harness runtime change.

## 0. Spike Summary

- **Sprint scope** (US): US-1 `--fix` dry-run report + neutral self-validating drafter / US-2 `--fix --write` position-based splicer + idempotency / US-3 real-Azure smoke evidence / US-4 CHANGE-132 + this note + closeout.
- **Verified period**: 2026-07-10.
- **Calibration**: NEW class `tool-autofix-spike` 0.60, parent-direct `agent_factor` 1.0. See retrospective Q2.
- **Verification**: 24 new unit tests (fake ChatClient, NO Azure) → `backend/tests/unit/scripts/lint/test_tool_description_autofix.py`; existing 10 checker tests unbroken; `run_all` 11/11; real-Azure cheap-tier smoke (5-gap fixture → 5/5 drafted + applied + re-lint OK).

## 1. Decision Matrix

| Decision | Options | Chosen | Why / rejected |
|----------|---------|--------|----------------|
| Apply mode | (A) report-only / (B) default-report + `--write` / (C) auto-apply + git-diff | **B** (user AskUserQuestion) | Two conscious gates (read report → decide `--write` → review `git diff`) for LLM-drafted "plausibly-wrong" text. A rejected: too weak for a "fix" tool. C rejected: one gate is easy to rubber-stamp a wrong-but-lint-passing description (the very failure research #7 warns of). |
| Code location | (1) sibling `scripts/lint/_autofix.py` / (2) fold into `check_tool_descriptions.py` | **2** (Day-1 D-fold-into-checker) | A sibling's `from scripts.lint.check_tool_descriptions import <predicates>` fails under the existing test's importlib file-path load (from `backend/`, `scripts.lint` is not an importable package). One module keeps the predicates single-sourced + directly testable; the backend adapter import stays lazy → the CI report path is byte-identical. |
| Source rewrite | (a) libcst / (b) position-based `ast` splice | **b** | No new dependency (`libcst` absent). Python 3.11 → every `ast` node carries `end_lineno`/`end_col_offset` → a splice target span is well-defined. |
| Draft trust | (i) trust the LLM draft / (ii) self-validate vs the lint | **ii** | `draft_description` re-checks each draft against the lint's own predicate (`_lint_ok`); retry once; else `NEEDS_MANUAL`. `--fix` never emits a draft that still fails the lint. |
| `FixTarget` type | (α) `@dataclass` / (β) `NamedTuple` | **β** (Day-1 bug) | `@dataclass` + `from __future__ import annotations` needs the module in `sys.modules` to resolve annotations; the importlib file-path test load doesn't register it → `AttributeError` in `dataclasses.py`. `NamedTuple` (like the existing `Violation`) has no such dependency. |

## 2. Verified Invariants

### 2.1 US-1 — collect maps exactly to the statically-fixable lint subset
- **Implementation**: `scripts/lint/check_tool_descriptions.py::collect_fix_targets` — reuses `MIN_DESCRIPTION_LEN` / `PLACEHOLDER_RE` / `_const_str` / `_dict_get` / `_kwarg` / `_toolspec_calls` (the SAME predicates as `find_violations`). 3 kinds: `replace_desc` / `insert_tool_desc` / `insert_param_desc`; a present-but-dynamic param description → `unfixable_dynamic` count, not a target; a dynamic tool description is lint-skipped (no target).
- **Verification**: `pytest tests/unit/scripts/lint/test_tool_description_autofix.py -k collect` (8 tests).

### 2.2 US-1 — the drafter is provider-neutral + self-validating
- **Implementation**: `check_tool_descriptions.py::draft_description` (async) takes a `ChatClient`; only `check_tool_descriptions.py::_build_cheap_client` lazily imports `adapters.azure_openai.profile.build_azure_model_profile().cheap`. `_lint_ok` re-checks the draft against the lint predicate; `_clean_draft` strips wrapping quotes + collapses to one line; retry once with `_RETRY_HINT`; else `NEEDS_MANUAL`.
- **Behavior**: LLM-SDK-leak clean (no `import openai/anthropic`; the adapter import is lazy + inside `--fix`). The CI report path imports nothing new.
- **Verification**: `pytest ... -k "draft or needs_manual"` (4 tests, fake ChatClient); `check_llm_sdk_leak` in `run_all` (11/11).

### 2.3 US-2 — position-based splice is correct + idempotent
- **Implementation**: `check_tool_descriptions.py::apply_fixes` re-parses the file, computes one `(start, end, replacement)` op per target via `_splice_op`, applies them back-to-front (highest offset first). `_line_starts`/`_offset` map (lineno, col) → char offset; `_quote` emits a double-quoted single-line literal; `_param_dict` re-finds a param value dict. `insert_tool_desc` splices after the `name=` value's comma (multi-line indents to `name_kw.col_offset`, single-line inline); `insert_param_desc` splices just after the param dict `{`; `replace_desc` overwrites the description `ast.Constant` span.
- **Behavior**: idempotent — a fixed file yields 0 targets → `apply_fixes(text, []) → (text, 0)`. `NEEDS_MANUAL` + unresolved targets are skipped.
- **Verification**: `pytest ... -k "apply or idempotent"` (9 tests) — each asserts the result `compile()`s (valid Python) + re-collects to 0 targets.

### 2.4 US-2 — `run_fix` orchestration works without Azure (non-Potemkin)
- **Implementation**: `check_tool_descriptions.py::run_fix(root, *, write)` — collect → (short-circuit if 0, no client) → draft → report (dry-run) OR group-by-file + apply + write + `⚠ LLM-DRAFTED` banner. `main()` adds `--fix`/`--write` (`--write requires --fix`); no-`--fix` path byte-identical.
- **Verification**: `pytest ... -k run_fix` (3 tests) monkeypatch `_build_cheap_client` + `_draft_all` → write-across-files / dry-run-does-not-write / no-targets-short-circuits-without-client.

### 2.5 US-3 — real-Azure smoke (cheap tier)
- **Reproduce**: root `.env` auto-loaded by `AzureOpenAIConfig(env_file=".env")` (`backend/src/adapters/azure_openai/config.py:37-43`) + `AZURE_OPENAI_CHEAP_DEPLOYMENT_NAME` sourced; `python -m scripts.lint.check_tool_descriptions --fix [--write] --root <fixture>`.
- **Result**: a 5-gap fixture (all 3 kinds) → 5/5 drafts from the real cheap-tier model → `--fix --write` applied → **re-lint `OK`** (drafts passed the lint + valid Python). Full command + output + the 2 honest cosmetic findings (Unicode smart quotes, param-key ordering) in `agent-harness-execution/phase-57/sprint-57-165/progress.md` §Day 3.
- **Test fixture**: throwaway `scratchpad/smoke_tools/tools.py` (session-isolated, NOT committed); the CI-safe equivalent is the fake-client unit suite (§2.1-2.4).

## 3. Cross-Category Contracts

No NEW boundary contract; no `17-cross-category-interfaces.md` change. `--fix` is a `scripts/lint/` dev/CI tool that consumes the existing neutral `ChatClient` ABC (`adapters/_base/chat_client.py`) + `build_azure_model_profile` (`adapters/azure_openai/profile.py`) via a LAZY import, outside `agent_harness/`. It touches no runtime category surface.

## 4. Open Invariants (deferred)

- [ ] **ASCII-normalize drafts** — the cheap model emitted Unicode smart quotes (`’`); valid Python + lint-passing but a reviewer may prefer ASCII. The ⚠ banner + Option-B git-diff gate surface it; an auto-normalization is a possible polish.
- [ ] **Param-key insert ordering** — `insert_param_desc` splices `"description"` as the FIRST key (`{"description": …, "type": …}`); the codebase convention is `type` first. Valid + lint-passing; a future splice could anchor after the last key.
- [ ] **`--fix` is Azure-only** — the drafter needs real creds → not CI-gated; the reporting lint stays the CI gate. A local pre-commit hook wiring is out of scope (non-deterministic).
- [ ] **No runtime A/B** — the value is toil-reduction with a human accuracy gate; there is no cheap runtime metric to A/B whether autofixed descriptions improve live tool selection (→ `AD-Tool-Autofix-Selection-Impact-Phase58` if ever pursued).

## 5. Rollback / Fallback

- Revert `scripts/lint/check_tool_descriptions.py` to its 57.144 state (drop the `--fix`/`--write` block + the 3 imports `asyncio` / `Any` / the machinery) + delete `backend/tests/unit/scripts/lint/test_tool_description_autofix.py`. ~15 min.
- The report-only lint + run_all wiring are UNCHANGED, so a revert cannot affect CI. Sentinel: `--fix` is opt-in (never invoked by run_all).

## 6. References

- Sprint plan: `phase-57-frontend-saas/sprint-57-165-plan.md` · checklist `sprint-57-165-checklist.md`
- Progress: `agent-harness-execution/phase-57/sprint-57-165/progress.md` (Day 0-3) · retrospective `.../retrospective.md`
- CHANGE-132: `claudedocs/4-changes/feature-changes/CHANGE-132-tool-description-autofix.md`
- Predecessor: `48-tool-error-reflection-design.md` (57.144 — the lint this extends; Half A) + `scripts/lint/check_tool_descriptions.py`
- Neutral client build mirrored from `backend/scripts/benchmark_tool_error_reflection.py:306-318`
- Research: `claudedocs/5-status/ai-agent-harness-consolidated-analysis-20260622.md` §2.3 / §5 #7

## Modification History
- 2026-07-10: Initial extract from Sprint 57.165 closeout (Day 4)
