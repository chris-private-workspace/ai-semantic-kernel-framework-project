# CHANGE-127: env-gated tool-anchored observation masking + reduction/retention A/B

**Date**: 2026-07-07
**Sprint**: 57.160
**Scope**: 範疇 4 (Context Management) — backend-only; no wire/codegen/frontend/migration

## Problem

The 57.159 compaction drive-through surfaced `AD-Compaction-NoOp-On-Single-User-Turn-Chat-Path`: compaction **triggers** every over-budget turn but **reduces 0 messages** on the chat main flow. Root cause — `DefaultObservationMasker` anchors its keep-window on **user-message count** (`observation_masker.py:62-64`: `if len(user_indices) <= keep_recent: return list(messages)`), and the chat path runs exactly **one user message per send** (even a 20-turn tool run shares ONE user turn). So the masker no-ops within the long single-user-turn tool run where context actually grows (observed 4k→35k, 8 no-op compactions). `keep_recent` cannot help (it is a user-turn count; `0` hits the `user_indices[-0]==[0]` full-keep bug the factory already guards).

## Root Cause

The masking UNIT (user turns) is mismatched to the growth UNIT (tool results within a single user turn). 57.139's `preclear.py:24-29` already documented this exact limitation and deferred the fix to `AD-Compaction-ToolAnchored-Preclear-Phase58` (tool-anchored clearing).

## Solution

Add an **opt-in tool-result-recency anchor mode** to the masker, rolled out evidence-first (env lever default OFF + A/B harness — AskUserQuestion pick "B", mirrors 57.139/144 discipline).

- `observation_masker.py` — `DefaultObservationMasker.__init__(*, tool_anchor_keep: int | None = None)`; `mask_old_results` branches: `None` → the original user-anchored path (byte-identical); `>=1` → `_mask_tool_anchored` keeps the last N `role=="tool"` results intact and tombstones older tool bodies WITHIN a single user turn (extracted shared `_tombstone` helper; defensive `keep<1` passthrough).
- `_category_factories.py` — `_compaction_tool_anchored_keep()` reads `CHAT_COMPACTION_TOOL_ANCHORED_MASKING` (`>=1` → N, else None; mirrors `_compaction_preclear_ratio`); `make_chat_compactor` injects `DefaultObservationMasker(tool_anchor_keep=N)` into BOTH `StructuralCompactor` and `PreClearCompactor` when set. Unset → `masker=None` → user-anchored default (byte-identical pre-57.160).
- `scripts/benchmark_tool_anchored_masking.py` + corpus + 13 CI-safe tests — deterministic OFF-vs-ON reduction% + mechanical-retention A/B (no Azure; masking is a pure transform).

## Verification

- A/B harness (real TiktokenCounter, 8 single-user-turn cases): **mean off_reduction 0.00%** (confirms the no-op) · **mean on_reduction 60.83%** · **retention_ok_rate 100%** · **recommend_default_on True**. Report: `artifacts/tool_anchored_masking_report.md`.
- Gates: pytest 3202 passed + 6 skipped (baseline 3180 +28) · mypy `src` 400 · run_all 11/11 · black/isort/flake8 clean · LLM-SDK-leak clean · FE untouched (Vitest 927 / mockup 51).
- **Drive-through PASS** (real chat-v2 + Azure gpt-5.2 + 6× knowledge_search in ONE user turn; `CHAT_COMPACTION_TOOL_ANCHORED_MASKING=1` + `CHAT_COMPACTION_PRECLEAR_RATIO=0.5` + budget 2500): the 57.159 marker renders REAL reductions `13,615→7,933 (−42%)` and `16,199→7,984 (−51%)`; context bounded ~8-9k vs 57.159's unbounded 4k→35k; BOREALIS-9 + 6 topics retained through compaction. Screenshot: `artifacts/sprint-57-160-leg3-compaction-real-reduction.png`.

**Drive-through KEY FINDING**: `StructuralCompactor.tokens_after` is a message-count ratio (`structural.py:192-193`) blind to in-place tombstoning, so the Hybrid→Structural path reports the reduction as `N→N · 0 msgs` even though real context shrank; only `PreClearCompactor` (real `TiktokenCounter` re-count) surfaces it. The tool-anchored masking is what makes preclear EFFECTIVE on the single-user-turn path — closing the mechanism half of `AD-Compaction-ToolAnchored-Preclear-Phase58`.

## Impact

Backend-only, 範疇 4. Default OFF → zero behaviour change on any existing deployment. When enabled, makes structural + preclear compaction actually reduce within a long single-user-turn tool run (bounds context growth). Closes `AD-Compaction-NoOp-On-Single-User-Turn-Chat-Path`; advances `AD-Compaction-ToolAnchored-Preclear-Phase58`. Flip-to-default is data-gated (design note 62). New carryover `AD-Compaction-Structural-RealTokenCount`.
