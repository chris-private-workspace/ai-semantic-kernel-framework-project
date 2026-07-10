# CHANGE-132: LLM-assisted `--fix` for the tool-description lint

**Date**: 2026-07-10
**Sprint**: 57.165
**Scope**: 範疇 2 (Tool Layer) — CI / dev tooling (`scripts/lint/`)
**Closes**: ③2 `AD-Tool-Description-AutoFix` (57.144 carryover) → Tool range **4/4**

## Problem

The Sprint 57.144 lint `scripts/lint/check_tool_descriptions.py` REPORTS flawed tool/param descriptions (missing / empty / `<20`-char / placeholder tool descriptions; params with no description) but does not draft replacements. When a new tool lands with a stub description the lint blocks the PR and leaves the author to hand-author each fix from a blank page.

## Motivation

Research #7 (`ai-agent-harness-consolidated-analysis §2.3`): tool-description quality measurably affects tool selection. An opt-in `--fix` that drafts a first-cut description (which the author reviews for accuracy) removes the blank-page toil while keeping the human as the accuracy gate.

## Solution

Add an opt-in `--fix` mode, folded INTO `check_tool_descriptions.py` (NOT a sibling module — a sibling's `from scripts.lint... import` fails under the existing importlib file-path test load; one module also keeps the violation predicates single-sourced). Apply-mode = **Option B** (user AskUserQuestion pick): `--fix` dry-run report by default, `--fix --write` to apply, `git diff` = 2nd review gate.

- **`collect_fix_targets(root) -> (list[FixTarget], unfixable_dynamic)`** — reuses the checker's own predicates so a `FixTarget` exists for exactly the statically-fixable subset the lint flags. 3 kinds: `replace_desc` (bad string literal, tool-level or empty param), `insert_tool_desc` (absent `description=`), `insert_param_desc` (absent param `"description"`). A present-but-dynamic param description is lint-flagged but not autofixable → counted, not targeted. `FixTarget` carries `ast.get_source_segment` as LLM context.
- **`draft_description(client, target)`** — async, provider-neutral (the `ChatClient` ABC; only `_build_cheap_client()` lazily imports `adapters.azure_openai.profile.build_azure_model_profile().cheap`). Self-validates each draft against the lint's own predicate (`_lint_ok`); retries once with a terser hint; else emits `NEEDS_MANUAL` — never a lint-failing draft.
- **`apply_fixes(text, targets_and_drafts) -> (new_text, applied)`** (`--write`) — position-based AST splice: re-parses the file, computes a `(start, end, replacement)` op per target, applies them back-to-front (highest offset first) so earlier edits never shift later spans. Idempotent (a fixed file yields 0 targets). `_quote` emits a double-quoted single-line literal; the implicit-concat parens nuance is handled (the Constant span covers the inner literals; the outer `()` remain valid).
- **`main()`** gains `--fix` / `--write` (`--write requires --fix`); the no-`--fix` report path is byte-identical + imports nothing new, so run_all / CI is unchanged. `--fix` is NEVER wired into run_all (it needs real Azure creds).

## Verification

- **Unit** (`backend/tests/unit/scripts/lint/test_tool_description_autofix.py`, 24 tests, fake ChatClient — NO Azure): collect (all 3 kinds + dynamic skip/count), drafter (clean / quote-strip / retry / needs-manual), report (dry-run), splice (replace / insert-tool multiline+singleline / insert-param / multi-edit), idempotency, and `run_fix` orchestration (write across files / dry-run-does-not-write / no-targets-short-circuits-without-client). Each splice test asserts the result `compile()`s + re-collects to 0.
- **Existing checker tests** (10) unbroken; `run_all` **11/11** green (no-`--fix` path byte-identical); lint self-run `OK` byte-identical.
- **Real-Azure smoke** (Day 3, cheap tier): a throwaway 5-gap fixture → `--fix` drafted 5/5 → `--fix --write` applied → **re-lint `OK`** (all drafts passed the lint + valid Python). Honest findings: drafts use Unicode smart quotes + insert the param key first — valid + lint-passing, surfaced by the ⚠ banner + git-diff gate for the human to adjust.
- black/isort/flake8 clean (project 100 std); mypy `src` 400/0 UNAFFECTED (all changes outside `src/`).

## Impact

- Backend/CI-tooling only. **NO** agent_harness runtime change / migration / wire / frontend / drive-through. Zero chance of a live regression (the runtime never imports the `--fix` path).
- The reporting lint remains the CI gate; `--fix` is an opt-in local assist.
- Design note: `docs/03-implementation/agent-harness-planning/64-tool-description-autofix-design.md`.
- Carryover (polish, → next-phase-candidates): ASCII-normalize drafts; param-key insert ordering; `AD-Tool-Taxonomy-HumanLabel` + the other 57.164 follow-ons remain open.
