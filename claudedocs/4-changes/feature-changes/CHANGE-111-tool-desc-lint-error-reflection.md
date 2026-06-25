# CHANGE-111: Cat 2 tool-description lint + structured-error reflection

**Date**: 2026-06-25
**Sprint**: 57.144
**Scope**: 範疇 2 (Tool Layer) + scripts/lint + 範疇 1 (loop rare-path)

## Problem

Research opportunity #7 `AD-Tool-Description-Lint-Reflection` (the LAST canonical research item; consolidated-analysis §2.3 / §2.4) flagged two Cat 2 gaps:
- **(A)** No tool-description quality check — `ToolSpec.description` is a bare `str` accepted as-is at register time; nothing stops a new tool shipping a one-line stub that degrades tool selection.
- **(B)** Tool failures feed the LLM an opaque/empty observation — the dominant handler-exception path returned `content=""` (the loop renders `content`, not `error`, so the LLM saw NOTHING useful on a handler-raised tool failure), with no structured diagnosis to guide recovery.

## Root Cause

- (A): `tools/registry.py:51-74` validates `input_schema` JSON-Schema syntax only — never the description text; no lint covered descriptions (`scripts/lint/run_all.py` had 10 detectors, none for descriptions).
- (B): `tools/executor.py:236-243` (handler exception) set `content=""`; `loop.py:3092` renders `result.content` via `_tool_result_to_text` (never `error`) → the LLM-visible tool message was empty on the dominant failure path. The Cat 8 `ErrorClass` taxonomy (`error_handling/_abc.py:30-36`) only answers "retry?", not "how to fix".

## Solution

**Half A — tool-description lint** (`scripts/lint/check_tool_descriptions.py`, NEW; 11th lint in `run_all.py`): an AST detector — every `ToolSpec(...)` needs a non-empty, `>= 20`-char, placeholder-free (UPPERCASE TODO/FIXME/XXX/TBD) description + a description on every `input_schema` property; skips dynamically-built descriptions/schemas (no false-positive). It surfaced **40 real missing param descriptions** (9 core harness + 31 business_domain mock tools) — all filled this sprint (user-approved scope expansion).

**Half B — structured-error reflection** (`tools/_error_taxonomy.py`, NEW): a pure `classify_tool_error()` (PARAMETER / WRONG_TOOL / FAILED_API / INVOCATION / UNKNOWN) + `render_reflection()`, consumed at `tools/executor.py:_build_failure` (dominant path) AND `loop.py:3023-3036` (rare executor-raises path, B2 full coverage), gated by the `CHAT_TOOL_ERROR_REFLECTION` env lever (default OFF). Orthogonal to Cat 8 ErrorClass. `ToolResult += error_taxonomy: str | None`.

## Verification

- **Half A**: `python -m scripts.lint.check_tool_descriptions --root backend/src` → OK exit 0; `run_all.py` → 11/11; `pytest tests/unit/scripts/lint/test_tool_descriptions.py` (10).
- **Half B**: `pytest tests/unit/agent_harness/tools/test_error_taxonomy.py` (19) + `test_executor.py` (+5 on/off) + `tests/integration/agent_harness/orchestrator_loop/test_loop_error_handling.py` (+2 end-to-end: the LLM sees the reflection content when ON, empty when OFF).
- **A/B drive-through (real Azure)**: `python scripts/benchmark_tool_error_reflection.py` (8 cases × 2 arms). Verdict **KEEP lever OFF** — fix_rate 87.5% plain == 87.5% reflection (+0.00%, below 5% materiality); reflection −32 completion tokens (secondary, not a flip trigger). Honest: V2's strong action-tier model already recovers from plain errors; consistent with the eval's RL-confound hedge (§2.4's BFCL gains were on weaker RL-trained models). Lever shipped as opt-in. Artifact: `agent-harness-execution/phase-57/sprint-57-144/artifacts/tool_error_reflection_report.{md,json}`.
- Gates: mypy `src` 382 · flake8 src+tests clean · run_all 11/11 · pytest 2930 +5skip · black/isort clean · LLM-SDK-leak clean.

## Impact

Backend + scripts/lint only. NO migration / NO wire event (stays 26) / NO codegen / NO frontend / NO 17.md contract change (ToolResult gains an optional field; reuses the Cat 7 ToolResult contract). Lever default OFF → byte-identical runtime behavior unless `CHAT_TOOL_ERROR_REFLECTION` is set. Closes `AD-Tool-Description-Lint-Reflection` (research #7 — last canonical item).
