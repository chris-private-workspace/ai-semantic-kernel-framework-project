# CHANGE-035: Event Schema Codegen + CI Parity Gate (A-5b)

**Date**: 2026-06-02
**Sprint**: 57.67
**Scope**: Cat 12 (Observability — SSE wire contract) + build-tooling (codegen + lint) + frontend chat_v2 + CI (lint.yml)

## Problem
The chat SSE event contract was defined across **three hand-maintained surfaces** that could silently drift: (1) the `sse.py` serializer branches, (2) the frontend `KNOWN_LOOP_EVENT_TYPES` gate, (3) the frontend per-event TS interfaces. Sprint 57.66 §8 explicitly named the residual risk — adding a serializer branch but forgetting the matching FE wire-string drops the event client-side with no error.

## Root Cause
No single source of truth. The capstone's proposed "frozen dataclass → events.ts" was non-viable (Day-0 D5): the wire shape is the serializer's hand-built `data` dict, which diverges from the dataclass fields (`arguments`→`args`, `result_content`→`result`, base fields dropped, `trace_id`/`is_error` added, non-TS-mappable types).

## Solution
Declarative single-source registry (user-chosen architecture, 2026-06-02):
- **`backend/src/api/v1/chat/event_wire_schema.py`** (NEW) — `WIRE_SCHEMA` (18 ordered wire-type → field→TS-type entries) + `BASE_FIELDS` (universal `trace_id`) + `LLMToolCall` element + `validate_ts_type`. Pure stdlib (loadable by file path). Authored from `sse.py`'s real branch output; TS types from `types.ts`.
- **`scripts/codegen/generate_event_schemas.py`** (NEW) — imports the registry via `importlib` (file path, no package install), emits `frontend/src/features/chat_v2/generated/events.json` + `loopEvents.generated.ts` (18 `*Event` interfaces in the nested `{ type, data: { trace_id?, ...fields } }` shape matching the working FE contract + `LoopEvent` union + `KNOWN_LOOP_EVENT_TYPES`). `--check` mode regenerates + diffs (LF-normalized).
- **`frontend/src/features/chat_v2/types.ts`** (EDIT) — deleted the 18 hand-written interfaces/union/KNOWN set/`LLMToolCall`; `export * from "./generated/loopEvents.generated"`. All non-event content (Block/Turn/Session/ToolCallEntry/ApprovalEntry/Chat* types) preserved.
- **`.gitattributes`** (NEW) — `generated/*.ts` + `events.json` `eol=lf` (cross-platform diff stability).
- **Parity gates**: `backend/tests/unit/api/v1/chat/test_event_wire_schema_parity.py` (NEW, serializer↔registry: every wired event's wire-type ∈ registry + `data` keys minus `trace_id` == registry; 6 unwired still raise; count==18) + `scripts/lint/check_event_schema_sync.py` (NEW, 10th V2 lint, codegen `--check`) wired into `scripts/lint/run_all.py` (9→10) + `.github/workflows/lint.yml` `v2-lints` job (Lint 7 — a required status check, so drift is un-mergeable).

## Verification
- Backend: parity test **30 passed**; full `pytest` **1994 passed / 4 skipped** (+30 vs main 1964); `mypy src/` **320 files, 0 errors**; `check_llm_sdk_leak` 0.
- Codegen: `--check` exit 0; idempotent (run twice → no diff).
- Frontend: `tsc --noEmit` **0 errors**; `npm run lint` clean; `npm run build` ✓ (3.90s); **Vitest 697 passed** (693 baseline + 4 new generated-KNOWN-set cases).
- Lints: `run_all.py` **10/10 green**.
- Drift-catch proof: editing a generated TS field → `check_event_schema_sync.py` exit 1 (unified diff) → regenerate → exit 0.

## Impact
Backend `api/v1/chat` (new registry + parity test; **`sse.py` NOT rewritten** — only locked by the test) + `scripts/codegen/` (new) + `scripts/lint/` (new lint + wrapper) + frontend `chat_v2` (re-export refactor + generated dir + test) + CI `lint.yml` (1 step). **No `loop.py` / `events.py` / new event subclass / DB / Azure changes.** Zero behavior change (the 18 wire-types + downstream consumers reproduced faithfully — proven by tsc + Vitest + pytest all green).
