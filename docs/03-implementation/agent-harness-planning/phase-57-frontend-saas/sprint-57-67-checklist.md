# Sprint 57.67 — Checklist (Event Schema Codegen + CI Parity Gate — A-5b)

**Plan**: [`sprint-57-67-plan.md`](./sprint-57-67-plan.md)
**Created**: 2026-06-02
**Status**: Draft (code gated on Day-0 GO)

> Rule: only `[ ]` → `[x]`; never delete unchecked items; defer with `🚧 + reason`.
> Architecture locked (user 2026-06-02): **declarative wire-schema registry** (Option 1) — single Python source → codegen → events.json + events.ts; parity = pytest (serializer↔registry) + `--check` lint (generated==committed). Day-0 audit (codebase-researcher 2026-06-02) pre-confirmed D1-D5 (plan §0); re-confirm residual unknowns (exact 18 field sets + lint.yml invocation style + types.ts non-event content) at sprint start before Day 1 code.

---

## Day 0 — Plan-vs-Repo Verify + Branch

### 0.1 Three-prong Day-0 verify (per `.claude/rules/sprint-workflow.md §Step 2.5`)
- [ ] **Prong 1 (path)**: confirm `backend/src/agent_harness/_contracts/events.py` (25 frozen dataclasses) / `backend/src/api/v1/chat/sse.py` (`serialize_loop_event`, `NotImplementedError` `:361`, `_jsonable` `isinstance UUID` `:387`, `trace_id` inject `:108-109`) / `frontend/src/features/chat_v2/types.ts` (interfaces `:45-205`, union `:207-225`, KNOWN set `:227-246`) / `frontend/src/features/chat_v2/services/chatService.ts` gate `:121` / `scripts/lint/run_all.py` `LINTS` `:59-81` (9 lints) / `.github/workflows/lint.yml` `v2-lints` `:26`; confirm `scripts/codegen/` + `events.json`/`events.ts`/`.gitattributes`-for-generated do NOT exist (D4)
- [ ] **Prong 2 (content)**: read EACH of the 17 wired `sse.py` branch `data` dicts → record the exact wire-type + payload key set + value source (NOT the dataclass fields — D5: `arguments`→`args`, `result_content`→`result`, base fields dropped, `trace_id`/`is_error` added); cross-read `types.ts` interfaces for the TS types; confirm the 2 classes → `tool_call_result` emit identical-or-divergent keys (→ optional `?` if divergent); confirm `trace_id` is `str | None` (universal base field); read full `types.ts` for any NON-event content that must survive the re-export refactor
- [ ] **Prong 3 (schema)**: N/A — no DB/migration/ORM change; 0 Alembic delta
- [ ] **Tooling verify**: read `run_all.py` `LINTS` shape (`(filename, args)` tuple, exit-code aggregation) + one existing lint script (e.g. `check_ap4_frontend_placeholder.py`) for the argparse/`--root`/exit pattern to mirror; read `lint.yml` `v2-lints` job — does it call scripts individually or `run_all.py`? (decides whether `.yml` needs an edit — plan §3.4)
- [ ] **Doc-location verify**: `02-architecture-design.md §SSE` = wire-type catalog (sse.py header ref); 17.md §4.1 emit-ownership needs NO change (no new event)
- [ ] Catalogue all findings (D-DAY0-N) in progress.md Day 0 table; **go/no-go** (expect GO — architecture pre-validated; residual = exact 18 field sets transcription)

### 0.2 Branch + decisions
- [ ] Branch `feature/sprint-57-67-event-schema-codegen` created from current main `c42ebfd3`; plan+checklist committed (1st commit)
- [ ] Scope decisions resolved: source = `backend/src/api/v1/chat/event_wire_schema.py`; generated dir = `frontend/src/features/chat_v2/generated/` (events.json + loopEvents.generated.ts); 18 wire-types modelled (NOT 25 dataclasses, NOT 6 unwired); serializer NOT rewritten (parity test only); **Agent-delegated: yes** (staged: Stage-1 backend registry+codegen+parity-test, Stage-2 FE generation+re-export+CI lint); no GitHub secrets

---

## Day 1 — Backend: registry + codegen + parity test (US-1 + US-3 backend half)

### 1.1 Single-source registry (US-1) — `event_wire_schema.py` (NEW)
- [ ] `WIRE_SCHEMA: dict[str, dict[str, str]]` — 18 ordered entries transcribed from Prong-2 branch output (field order = generated interface order)
- [ ] TS-type mini-language: `_TS_TYPES` vocab (`string`/`number`/`boolean`/`string[]`/`number[]`/`Record<string, unknown>` + `?` optional + `| null` nullable) + `to_ts(spec) -> str` helper (unknown spec → raise)
- [ ] `trace_id` declared once as universal base (not repeated 18×); file header per convention
  - DoD: `from ... import WIRE_SCHEMA` works; `len(WIRE_SCHEMA) == 18`; every value's specs ∈ vocab

### 1.2 Codegen script (US-2) — `scripts/codegen/generate_event_schemas.py` (NEW)
- [ ] Imports `WIRE_SCHEMA`; emits `events.json` (sorted wire-types + declared field order) + `loopEvents.generated.ts` (AUTO-GENERATED header + 18 `*Event` interfaces with PascalCase names matching current `types.ts` + `LoopEvent` union + `KNOWN_LOOP_EVENT_TYPES` Set)
- [ ] Explicit `\n` line endings + trailing newline; idempotent (run twice → no diff)
- [ ] `--check` mode: regenerate in-memory, normalise line endings, diff vs committed, print unified diff + exit 1 on mismatch
  - DoD: run writes the 2 files; second run = no git diff; `--check` exit 0 after write

### 1.3 Backend parity test (US-3) — `test_event_wire_schema_parity.py` (NEW)
- [ ] Instantiate one representative of each of the 17 wired event classes → `serialize_loop_event` → assert wire-type ∈ `WIRE_SCHEMA` AND `data` keys (minus universal `trace_id`) == `WIRE_SCHEMA[type]` keys (both drift directions)
- [ ] `tool_call_result`: assert each of the 2 classes' keys ⊆ schema; schema == union (optional `?` for divergent fields)
- [ ] Assert the 6 unwired classes still raise `NotImplementedError` (lock the boundary); assert `len(KNOWN-equivalent) == len(WIRE_SCHEMA) == 18`
  - DoD: pytest green; deliberately mutating one `WIRE_SCHEMA` field name makes the test fail (drift caught)

### 1.4 Backend sweep
- [ ] `black . && isort . && flake8 . && mypy src/` clean on new files; full `pytest` green (+ new parity cases); `check_llm_sdk_leak` 0
  - DoD: pytest ≥ prior 1964 (+ parity cases) / mypy 0/N / new files lint-clean

---

## Day 2 — FE generation + re-export + CI lint (US-2 + US-3 FE/CI half + US-4)

### 2.1 Generated artifacts committed (US-2)
- [ ] Run codegen → commit `frontend/src/features/chat_v2/generated/events.json` + `loopEvents.generated.ts`
- [ ] `.gitattributes`: `*.generated.ts` + `generated/events.json` `text eol=lf`
  - DoD: generated TS interface names + fields byte-match the current hand-written ones (pre-refactor `git diff` of the types is empty in spirit)

### 2.2 `types.ts` re-export refactor (US-2)
- [ ] Delete hand-written 18 interfaces (`:45-205`) + union (`:207-225`) + KNOWN set (`:227-246`); add re-export from `./generated/loopEvents.generated`; preserve any non-event content (Prong-2 finding)
  - DoD: tsc EXIT 0; `chatService.ts` gate + `chatStore.ts` `mergeEvent` exhaustive `switch (never)` compile unchanged

### 2.3 Parity lint + wiring (US-3)
- [ ] `scripts/lint/check_event_schema_sync.py` (NEW) — invoke codegen `--check`; mirror existing lint argparse/exit shape
- [ ] `scripts/lint/run_all.py` — add `("check_event_schema_sync.py", [])` → `LINTS` 9→10
- [ ] `.github/workflows/lint.yml` `v2-lints` — add the lint (or no-op if it calls `run_all.py` — Day-0 finding)
  - DoD: `python scripts/lint/run_all.py` = `10/10`; staling a generated file → lint exit 1

### 2.4 FE tests (US-4)
- [ ] Vitest: assert generated `KNOWN_LOOP_EVENT_TYPES` size == 18 + the 4 newest types (`prompt_built`/`context_compacted`/`state_checkpointed`/`tripwire_triggered`) recognized; existing suite unaffected
  - DoD: `npm run lint` (NO `--silent`) clean + `npm run build` ✓ + **Vitest 693** (zero behavior change)

---

## Day 3 — Cross-cutting + doc + full sweep

- [ ] `02-architecture-design.md §SSE`: note the wire-type catalog is generated from `event_wire_schema.py` (single source); 17.md §4.1 unchanged
- [ ] Full sweep: backend `pytest` green / `mypy src/` 0/N / `run_all.py` **10/10** (SDK leak 0) / frontend `npm run lint` clean + `npm run build` ✓ + Vitest 693
- [ ] Drift self-check: run codegen → `git diff` empty; `--check` exit 0; `run_all.py` 10/10

---

## Day 4 — Closeout

- [ ] Full validation sweep: pytest / mypy src 0/N / run_all.py 10/10 / Vitest 693 / tsc 0 / build ✓
- [ ] `claudedocs/4-changes/feature-changes/CHANGE-035-event-schema-codegen.md`
- [ ] progress.md (Day 0-4) + retrospective.md (Q1-Q7)
- [ ] Calibration: `medium-backend` 0.80 + `agent_factor mechanical-greenfield-design-decisions` 0.65 (CAVEATED — 5th consecutive no-clean-wall-clock per `AD-Calibration-AgentDelegated-WallClock-Measure`; watch new-toolchain-greenfield ratio per plan §7); record `calibration-log.md §3`
- [ ] Area-A capstone: A-5b shipped (drift now mechanically un-mergeable); A-5c (Inspector UI) remains; note carryover ADs (`AD-EventSchema-RuntimeTypeParity`, `AD-EventSchema-SerializerConsumesRegistry`)
- [ ] MEMORY.md pointer + `project_phase57_67_*.md` subfile + CLAUDE.md lean Current Sprint/Last Updated
- [ ] commit (Day 3+4) + push + PR — user-authorized
