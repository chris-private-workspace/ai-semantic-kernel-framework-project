# Sprint 57.67 — Checklist (Event Schema Codegen + CI Parity Gate — A-5b)

**Plan**: [`sprint-57-67-plan.md`](./sprint-57-67-plan.md)
**Created**: 2026-06-02
**Status**: Complete (commit/push/PR user-gated)

> Rule: only `[ ]` → `[x]`; never delete unchecked items; defer with `🚧 + reason`.
> Architecture locked (user 2026-06-02): **declarative wire-schema registry** (Option 1) — single Python source → codegen → events.json + events.ts; parity = pytest (serializer↔registry) + `--check` lint (generated==committed).

---

## Day 0 — Plan-vs-Repo Verify + Branch

### 0.1 Three-prong Day-0 verify (per `.claude/rules/sprint-workflow.md §Step 2.5`)
- [x] **Prong 1 (path)**: confirmed `_contracts/events.py` (25 frozen dataclasses) / `sse.py` (`serialize_loop_event` `:97`, `NotImplementedError` `:361`, `_jsonable isinstance UUID` `:387`, `trace_id` inject `:116`) / `chat_v2/types.ts` (interfaces `:45-205`, union `:207-225`, KNOWN `:227-246`) / `chatService.ts` gate `:121` / `run_all.py` LINTS `:59-81` (9 lints) / `lint.yml` v2-lints `:26`; `scripts/codegen/` + `events.json`/`events.ts`/generated `.gitattributes` do NOT exist (D4)
- [x] **Prong 2 (content)**: full 18 wire-type field-set transcription from sse.py branch bodies (D-DAY0-2 table in progress.md); `tool_call_result` 2 classes emit IDENTICAL keys (D-DAY0-3, no optional split); `trace_id` universal-base injected by wrapper (D-DAY0-4); TS types read from types.ts (richer than table: score/reason nullable, verifier_type union, LLMToolCall, thinking/suggested_correction nullable)
- [x] **Prong 3 (schema)**: N/A — no DB/migration/ORM change
- [x] **Tooling/CI verify**: `run_all.py` `(filename, args)` tuple shape + exit aggregation; **`lint.yml` runs 6 lints INDIVIDUALLY (not run_all.py) + unit-test step (D-DAY0-5)** → parity lint needs a `lint.yml` step (CI/CD, user-auth); codegen loads registry via `importlib.spec_from_file_location` (D-DAY0-6); repo-root-relative paths (D-DAY0-7)
- [x] Catalogued D-DAY0-1..8 in progress.md Day 0 table; **go/no-go = GO** (all prongs GREEN; 18 field sets fully transcribed)

### 0.2 Branch + decisions
- [x] Branch `feature/sprint-57-67-event-schema-codegen` from `c42ebfd3`; plan+checklist committed (`e9effd89`); Day-0 progress committed (`7275df72`)
- [x] Scope decisions resolved: source `event_wire_schema.py`; generated dir `chat_v2/generated/`; 18 wire-types modelled (NOT 25 dataclasses / 6 unwired); serializer NOT rewritten (parity test only); **Agent-delegated: yes** (staged Stage-1 backend / Stage-2 FE+CI); CI gate = user-auth at push

---

## Day 1 — Backend: registry + codegen + parity test (US-1 + US-3 backend half)

### 1.1 Single-source registry (US-1) — `event_wire_schema.py` (NEW)
- [x] `WIRE_SCHEMA` — 18 ordered entries transcribed from Prong-2 (field order = interface order)
- [x] TS-type mini-language: `_RECOGNIZED_TS_TYPES` + `_PASSTHROUGH_TS_TYPES` (LLMToolCall[] + verifier_type union) + `validate_ts_type()`
- [x] `BASE_FIELDS = {"trace_id": "string | null"}` (universal, not repeated 18×); file header per convention; pure stdlib

### 1.2 Codegen script (US-2) — `scripts/codegen/generate_event_schemas.py` (NEW)
- [x] Imports registry via `importlib`; emits `events.json` + `loopEvents.generated.ts` (AUTO-GENERATED header; 18 `*Event` interfaces matching types.ts names + `LLMToolCall` + `LoopEvent` union + `KNOWN_LOOP_EVENT_TYPES`)
- [x] Explicit `\n` + trailing newline; idempotent
- [x] `--check` mode: regenerate, LF-normalize, diff, exit 1 on mismatch

### 1.3 Backend parity test (US-3) — `test_event_wire_schema_parity.py` (NEW)
- [x] 17 wired event classes → `serialize_loop_event` → wire-type ∈ `WIRE_SCHEMA` AND `data` keys minus `trace_id` == registry keys
- [x] `tool_call_result` both classes identical keys; 6 unwired raise `NotImplementedError`; `Thinking`→None; count==18

### 1.4 Backend sweep
- [x] black/isort/flake8 clean on new files; `mypy src/` **320/0**; full `pytest` **1994 passed / 4 skipped** (+30); `check_llm_sdk_leak` 0

---

## Day 2 — FE generation + re-export + CI lint (US-2 + US-3 FE/CI half + US-4)

### 2.1 Generated artifacts committed (US-2)
- [x] codegen produced `chat_v2/generated/events.json` + `loopEvents.generated.ts` (nested `{type, data:{trace_id?, ...}}` shape — Stage-2 reconciliation fix)
- [x] `.gitattributes`: generated `*.ts` + `events.json` `eol=lf`

### 2.2 `types.ts` re-export refactor (US-2)
- [x] Deleted hand-written interfaces/union/KNOWN/LLMToolCall; `export * from "./generated/loopEvents.generated"`; preserved Block/Turn/Session/ToolCallEntry/ApprovalEntry/Chat* content; tsc EXIT 0

### 2.3 Parity lint + wiring (US-3)
- [x] `scripts/lint/check_event_schema_sync.py` (NEW) — codegen `--check`; mirrors existing lint shape
- [x] `run_all.py` — `LINTS` 9→10 (`10/10` green)
- [x] `.github/workflows/lint.yml` `v2-lints` — "Lint 7" step (**user-authorized Option A**, 2026-06-02 — required check → drift un-mergeable)

### 2.4 FE tests (US-4)
- [x] Vitest `eventSchema.generated.test.ts`: KNOWN set size == 18 + newest types recognized; `npm run lint` (no `--silent`) clean + `npm run build` ✓ + **Vitest 697** (693+4)

---

## Day 3 — Cross-cutting + doc + full sweep

- [x] `02-architecture-design.md §SSE`: registry-as-single-source note; 17.md §4.1 unchanged (no new event)
- [x] Full sweep: pytest 1994 / `mypy src/` 320/0 / `run_all.py` **10/10** (SDK leak 0) / `npm run lint` clean + `npm run build` ✓ / Vitest 697
- [x] Drift self-check: codegen → `git diff` empty; `--check` exit 0; drift-catch proven (edit generated field → lint exit 1 → regen → 0)

---

## Day 4 — Closeout

- [x] Full validation sweep: pytest 1994 / mypy src 320/0 / run_all 10/10 / Vitest 697 / tsc 0 / build ✓ (parent independently re-verified)
- [x] `claudedocs/4-changes/feature-changes/CHANGE-035-event-schema-codegen.md`
- [x] progress.md (Day 0-4) + retrospective.md (Q1-Q7)
- [x] Calibration: `medium-backend` 0.80 + `agent_factor mechanical-greenfield-design-decisions` 0.65 (CAVEATED — 5th consecutive no-clean-wall-clock; NEW `AD-AgentFactor-NewToolchain-Greenfield-Watch`); recorded `calibration-log.md §3`
- [x] Area-A capstone: A-5b shipped (drift mechanically un-mergeable); A-5c (Inspector UI) remains; carryover ADs noted (`AD-Day0-Codegen-Existing-Shape-Capture`, `AD-EventSchema-RuntimeTypeParity`, `AD-EventSchema-SerializerConsumesRegistry`, `AD-LintYml-RunAll-Divergence`)
- [x] MEMORY.md pointer + `project_phase57_67_event_schema_codegen.md` subfile + CLAUDE.md lean Current Sprint/Last Updated
- [ ] commit (Day 1-4) + push + PR — user-authorized
