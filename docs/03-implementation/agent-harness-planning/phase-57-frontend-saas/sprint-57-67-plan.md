# Sprint 57.67 Plan — Event Schema Codegen + CI Parity Gate (A-5b)

**Purpose**: Replace the **hand-maintained triple surface** that defines the chat SSE event contract — (1) the `sse.py` serializer branches, (2) the FE `KNOWN_LOOP_EVENT_TYPES` gate, (3) the FE per-event TS interfaces — with **one declarative Python single-source registry** (`event_wire_schema.py`) that **generates** the FE artifacts (`events.json` + `loopEvents.generated.ts`), plus a **CI parity gate** that makes drift mechanically un-mergeable. This automates the exact double-gate that 57.66 maintained by hand (add a `sse.py` branch → must remember to add the FE wire-string + interface, or the event is silently dropped client-side).
**Category / Scope**: Cat 12 (Observability — SSE wire contract, cross-cutting) + build-tooling (codegen + lint) + light FE refactor (replace hand-written event types with generated re-export); Phase 57.67
**Created**: 2026-06-02
**Status**: Draft (user-approved architecture: Option 1 "宣告式 wire-schema registry"; code execution gated on Day-0 GO)
**Source**: Area-A integration capstone (A-5b component) + **Day-0 reality audit (codebase-researcher, 2026-06-02)** which corrected the capstone's "frozen dataclass → events.json → events.ts" framing (D5 — dataclass fields ≠ wire shape; see §0) + user AskUserQuestion decision 2026-06-02 (Option 1 declarative registry over name-only / serializer-AST-introspection)

> **Modification History**
> - 2026-06-02: Initial creation — A-5b codegen; folds Day-0 audit drift (D1-D5) into §0; architecture = declarative wire-schema registry per user decision

---

## 0. Background

57.66 (A-5a+) closed the last hand-maintained drift by adding 4 serializer branches + 4 FE wire-strings + 4 TS interfaces **by hand**, and §8 explicitly named the residual risk: "FE double-gate: serializer branch without FE wire-string → still dropped client-side … the double-gate the A-5b codegen would prevent; here done by hand". A-5b is that codegen.

A **Day-0 reality audit on current main (`c42ebfd3`)** corrected the capstone's stale framing (folded here, not silently rewritten, per `sprint-workflow.md §Step 2.5`):

### ⚠️ Day-0 drift corrections (from the 2026-06-02 codebase-researcher audit)

- **D1 — source path drift**: the single-source event definitions live at **`backend/src/agent_harness/_contracts/events.py`** (NOT `orchestrator_loop/_contracts/events.py`); `orchestrator_loop/events.py` is a re-export shim. FE types live at **`frontend/src/features/chat_v2/types.ts`** (NOT `orchestrator-loop/types.ts`). All §3-§4 paths use the corrected locations.
- **D2 — 25 concrete `LoopEvent` subclasses, all `@dataclass(frozen=True)`** (`events.py:51`), NOT Pydantic. Header docstring says "22" (stale). Base `LoopEvent` carries `event_id: UUID` / `timestamp: datetime` / `trace_context: TraceContext | None` — none of which go on the wire (the serializer drops them and injects a flat `trace_id` string instead).
- **D3 — 18 distinct wire-types today**, produced by 17 isinstance branches (`Thinking → None` is a deliberate skip; `ToolCallExecuted` + `ToolCallFailed` both → `tool_call_result`). 6 event classes are **unwired** (`MemoryAccessed`, `ErrorRetried`, `LoopTerminated`, `SpanStarted`, `SpanEnded`, `MetricRecorded` → `NotImplementedError` at `sse.py:361`). The FE `KNOWN_LOOP_EVENT_TYPES` Set (`types.ts:227-246`) has exactly **18 members** — matching the 18 wire-types. **The registry models the 18 wire-types, not the 25 dataclasses** (D5).
- **D4 — no codegen exists** (confirmed: no `scripts/codegen/`, no `events.json`/`events.ts`/`event-schema-sync.yml`; no `datamodel-code-generator`/`pydantic2ts`/`quicktype` in either dep tree). `scripts/lint/run_all.py` has a **9-lint `LINTS` list** (`:59-81`); a 10th slots in as one `(filename, args)` tuple. V2 lints run in CI via `.github/workflows/lint.yml` job `v2-lints` (`:26`) — **no GitHub secrets** needed for a new parity lint.
- **D5 — THE architecture pivot (why the capstone framing was wrong)**: the wire shape is the serializer's **hand-built `data` dict**, which **systematically diverges from the dataclass fields** — it renames (`arguments`→`args`, `result_content`→`result`), drops every base field (`event_id`/`timestamp`/`trace_context`), adds `trace_id`/`is_error`, and the dataclasses carry non-TS-mappable types (`trace_context: TraceContext`, `tool_calls: tuple[Any,...]`, `dict[str,Any]`). **A naive dataclass→TS walk generates the wrong contract.** Therefore the **single source of truth is a NEW declarative wire-schema registry authored from the serializer's real output** — NOT the dataclass, NOT a fragile AST-scrape of `sse.py`. (User decision 2026-06-02: Option 1 over name-only / AST-introspection.)

**Net**: author one declarative `WIRE_SCHEMA` (18 entries, each = wire-type → field→TS-type map) transcribed from `sse.py`'s real branch output; generate `events.json` + `loopEvents.generated.ts` (per-event interface + `LoopEvent` union + `KNOWN_LOOP_EVENT_TYPES`); refactor `types.ts` to re-export the generated symbols (deleting the hand-written copies); lock it with two parity gates — a pytest test (serializer output ⊆/== registry) + a `--check` codegen lint (committed generated artifacts == freshly regenerated). **Zero behavior change** (the 18 wire-types + their consumers are byte-faithfully reproduced — proven by tsc + Vitest 693 + pytest all staying green). **No `loop.py`, no `events.py`, no new event subclass, no DB, no serializer rewrite** (serializer keeps its hand-written branches; only a parity test is added).

---

## 1. Sprint Goal

Establish a single declarative Python wire-schema registry (`backend/src/api/v1/chat/event_wire_schema.py`) as the sole authoring point for the chat SSE event contract, generate the FE `events.json` + `loopEvents.generated.ts` from it (per-event interfaces + union + `KNOWN_LOOP_EVENT_TYPES`), refactor `types.ts` to consume the generated file, and enforce non-drift with (a) a pytest parity test asserting every `serialize_loop_event` branch's wire-type + payload-key set matches the registry, and (b) a `check_event_schema_sync` lint (10th V2 lint, wired into `run_all.py` + CI `lint.yml`) that regenerates and fails on any diff against the committed artifacts. **Zero behavior change** — all existing tests green, tsc 0, Vitest 693, pytest unchanged-or-higher. **No GitHub secrets** (parity lint is local + CI-runnable).

---

## 2. User Stories

- **US-1 (single-source registry)** — As a harness maintainer, I want one declarative `WIRE_SCHEMA` (wire-type → ordered field→TS-type map) as the single source of truth for all 18 SSE event wire-types + payload shapes, so the contract has one authoring point instead of three hand-maintained surfaces. → new `event_wire_schema.py` transcribed faithfully from `sse.py`'s real branch output (D5).
- **US-2 (codegen → events.json + events.ts)** — As a frontend consumer, I want the FE per-event interfaces, the `LoopEvent` union, and `KNOWN_LOOP_EVENT_TYPES` generated from the registry (via `events.json`), so adding/changing an event never requires hand-editing FE types — the 57.66 double-gate pain disappears. → new `scripts/codegen/generate_event_schemas.py` (run + `--check` modes); generated `events.json` + `loopEvents.generated.ts`; `types.ts` re-exports the generated symbols (hand-written copies deleted).
- **US-3 (parity gates make drift un-mergeable)** — As a reviewer, I want CI to fail when (a) a `sse.py` serializer branch emits a wire-type or payload-key set that diverges from the registry, or (b) the committed generated FE artifacts are stale vs the registry, so contract drift is mechanically impossible to merge. → pytest `test_event_wire_schema_parity.py` (serializer output == registry) + `check_event_schema_sync.py` lint (codegen `--check`: regenerate, diff must be empty), wired into `run_all.py` (9→10) + `lint.yml` `v2-lints`.
- **US-4 (retrofit existing 18 + zero-behavior-change validation)** — As a maintainer, I want all 18 current wire-types migrated onto the generated source with every existing test green, so this is a pure automation refactor (no contract change), proven by tsc 0 + Vitest 693 + pytest all green and the generated `types.ts` re-export producing byte-identical downstream behavior.

---

## 3. Technical Specifications

### 3.0 Architecture (locked — Option 1 declarative registry; D5 pivot)

```
backend/src/api/v1/chat/event_wire_schema.py   ← SINGLE SOURCE (hand-authored from sse.py reality)
        │  WIRE_SCHEMA: dict[wire_type, FieldSpec]  (18 entries)
        ▼
scripts/codegen/generate_event_schemas.py  (run | --check)
        │  imports WIRE_SCHEMA (runtime, not AST), maps the TS-type mini-language
        ├──▶ frontend/src/features/chat_v2/generated/events.json            (canonical contract snapshot)
        └──▶ frontend/src/features/chat_v2/generated/loopEvents.generated.ts (interfaces + union + KNOWN set)
                     │
                     ▼
        frontend/src/features/chat_v2/types.ts   re-exports generated symbols (hand-written copies removed)

Parity gates (US-3):
  • pytest test_event_wire_schema_parity.py : serialize_loop_event(instance) for each wired event
        → assert wire-type ∈ WIRE_SCHEMA AND data-keys (minus universal trace_id) == WIRE_SCHEMA[type].keys
  • scripts/lint/check_event_schema_sync.py : run codegen --check (regenerate to temp, diff vs committed) → exit≠0 on drift
        → registry == FE KNOWN set is implied (KNOWN set IS generated), so "committed == regenerated" closes the loop
```

The serializer (`sse.py`) is **NOT rewritten** to consume the registry (keeps 57.66 code stable, minimises risk); it is only **locked by the parity test**. The registry is authored once from the serializer's real output and then becomes authoritative.

### 3.1 Single-source registry (US-1) — `backend/src/api/v1/chat/event_wire_schema.py` (NEW)

- `WIRE_SCHEMA: dict[str, dict[str, str]]` — 18 entries keyed by snake_case wire-type; each value is an **ordered** field→TS-type-spec map (insertion order = generated interface field order, for deterministic diffs).
- **TS-type mini-language** (string values; small, closed vocabulary covering all wire payloads, which are JSON primitives/arrays/objects after `_jsonable`): `"string"`, `"number"` (covers `int`+`float`), `"boolean"`, `"string[]"`, `"number[]"`, `"Record<string, unknown>"` (for `dict[str,Any]` payloads), plus optional suffix `"?"` (e.g. `"number?"` → `field?: number`) and nullable union `"| null"` where the serializer can emit `None`. A `_TS_TYPES` frozenset + a tiny `to_ts(spec)->str` helper validates the vocabulary (unknown spec → codegen raises, caught by the parity lint).
- `trace_id: "string"` is **universal** (every frame carries it — `sse.py:108-109`); declare it once as a shared base so it is not repeated 18×. Generated interfaces extend a base `{ type: string; trace_id: string | null }`-style shape (Day-1 confirms the exact base — `trace_id` is `str | None`).
- The 18 entries + their exact field sets are transcribed Day-1 from the real `sse.py` branch `data` dicts (Prong 2 reads each branch body, NOT the dataclass — D5) and cross-checked against the current `types.ts` interfaces for the TS types.

### 3.2 Codegen script (US-2) — `scripts/codegen/generate_event_schemas.py` (NEW)

- Imports `WIRE_SCHEMA` (runtime import of the Python module — robust; not an AST scrape of `sse.py`).
- **`events.json`**: canonical language-neutral snapshot — `{ "wire_types": [...18 sorted...], "events": { "<wire_type>": { "<field>": "<ts-spec>", ... }, ... } }`. Deterministic key ordering (sorted wire-types; declared field order within each).
- **`loopEvents.generated.ts`**: a clearly-marked `// AUTO-GENERATED by scripts/codegen/generate_event_schemas.py — DO NOT EDIT` header, then: one `export interface <Pascal>Event { type: "<wire_type>"; trace_id: string | null; <fields> }` per wire-type (PascalCase derived from wire-type: `prompt_built`→`PromptBuiltEvent`, matching the current hand-written names — Day-1 confirms the 18 interface names match exactly), the `export type LoopEvent = A | B | …` union, and `export const KNOWN_LOOP_EVENT_TYPES = new Set<string>([...])`.
- **Determinism**: writes `\n` line endings explicitly + trailing newline; `--check` normalises line endings before diffing (Windows-dev/Linux-CI CRLF risk — see §8). Add the two generated files to `.gitattributes` as `text eol=lf` to keep `diff` stable.
- **Modes**: `python scripts/codegen/generate_event_schemas.py` (writes the 2 files); `--check` (regenerate in-memory, compare to committed, print a unified diff + exit 1 on mismatch).

### 3.3 FE integration (US-2) — `frontend/src/features/chat_v2/types.ts` (EDIT) + generated dir (NEW)

- New `frontend/src/features/chat_v2/generated/` holding `events.json` + `loopEvents.generated.ts` (both committed, both codegen-owned).
- `types.ts`: **delete** the hand-written 18 event interfaces (`:45-205`), the `LoopEvent` union (`:207-225`), and the `KNOWN_LOOP_EVENT_TYPES` Set (`:227-246`); **add** `export * from "./generated/loopEvents.generated";` (or explicit named re-exports if `types.ts` has other content that would collide — Day-1 reads the full file). Any non-event content in `types.ts` stays.
- Downstream (`chatService.ts:121` gate, `chatStore.ts` `mergeEvent` switch, components) import from `types.ts` unchanged → re-export keeps them working. **Faithful transcription is mandatory**: generated interface names + field names + types must reproduce the current ones exactly so `mergeEvent`'s exhaustive `switch (never)` and tsc stay green.

### 3.4 Parity gates (US-3)

- **pytest `backend/tests/.../test_event_wire_schema_parity.py` (NEW)**: build one representative instance of each of the 17 wired event classes (frozen dataclasses; known fields), call `serialize_loop_event`, and assert: (a) the emitted `event:` wire-type ∈ `WIRE_SCHEMA`; (b) the emitted `data` dict key set, minus the universal `trace_id`, **equals** `WIRE_SCHEMA[wire_type]` key set. Covers both drift directions (serializer adds a field but not the registry; registry has a field the serializer never emits). For the two classes sharing `tool_call_result`, assert each class's keys ⊆ the schema and the schema = the union (Day-1 confirms whether the two emit identical keys; if not, the differing fields are declared optional `?`). Also assert the 6 unwired classes still raise `NotImplementedError` (lock the current boundary). Plus: a generated-vs-source consistency unit (`KNOWN_LOOP_EVENT_TYPES` count == `len(WIRE_SCHEMA)` == 18).
- **lint `scripts/lint/check_event_schema_sync.py` (NEW)**: invokes the codegen in `--check` mode (regenerate, diff vs committed `events.json` + `loopEvents.generated.ts`); exit 0 = in sync, exit 1 = stale (prints which file + diff). Follows the existing lint script shape (argparse, `--root` if needed, exit codes).
- **`scripts/lint/run_all.py` (EDIT)**: add `("check_event_schema_sync.py", [])` to the `LINTS` list (`:59-81`) → 9 → **10**; the wrapper's `<failed>/10` summary updates automatically.
- **`.github/workflows/lint.yml` (EDIT)**: add the new script to the `v2-lints` job (`:26`) alongside the existing 9 (or, if the job already calls `run_all.py`, no edit — Day-1 confirms whether `lint.yml` calls scripts individually or via the wrapper; align to whatever it does today). **No secrets**.

### 3.5 Validation + lint / neutrality / doc single-source

- **Neutrality**: `event_wire_schema.py` + codegen + lint are pure data/string work — provider-free; `agent_harness/**` untouched → `check_llm_sdk_leak` stays 0. The registry lives in the api layer (presentation/wire concern), not `agent_harness` (correct category boundary — the wire mapping was always an api decision, which is why `sse.py` owned it).
- **Doc single-source**: `02-architecture-design.md §SSE` is the wire-type catalog (referenced by `sse.py`); add a note that the catalog is now **generated from `event_wire_schema.py`** (point readers to the registry as the source). 17.md §4.1 emit-ownership is unchanged (no new event). The `events.json` snapshot doubles as a language-neutral contract doc.
- **Validation**: see §5.

---

## 4. File Change List

| File | Change |
|------|--------|
| `backend/src/api/v1/chat/event_wire_schema.py` | **NEW** — `WIRE_SCHEMA` (18 entries) + TS-type mini-language vocab + `to_ts()` helper (single source of truth, US-1) |
| `scripts/codegen/generate_event_schemas.py` | **NEW** — codegen: imports registry → emits `events.json` + `loopEvents.generated.ts`; `--check` mode (US-2) |
| `frontend/src/features/chat_v2/generated/events.json` | **NEW (generated, committed)** — canonical wire-type contract snapshot |
| `frontend/src/features/chat_v2/generated/loopEvents.generated.ts` | **NEW (generated, committed)** — 18 interfaces + `LoopEvent` union + `KNOWN_LOOP_EVENT_TYPES` |
| `frontend/src/features/chat_v2/types.ts` | **EDIT** — delete hand-written interfaces/union/KNOWN set (`:45-246`); re-export from generated (US-2); keep any non-event content |
| `.gitattributes` | **EDIT/NEW** — `*.generated.ts` + `events.json` `text eol=lf` (stable cross-platform diff) |
| `backend/tests/.../test_event_wire_schema_parity.py` | **NEW** — serializer↔registry parity (17 wired events) + unwired-still-raises + count==18 (US-3) |
| `scripts/lint/check_event_schema_sync.py` | **NEW** — codegen `--check` parity lint (10th V2 lint, US-3) |
| `scripts/lint/run_all.py` | **EDIT** — add 10th lint to `LINTS` (`:59-81`) |
| `.github/workflows/lint.yml` | **EDIT** — add lint to `v2-lints` job (`:26`) (or no-op if it calls `run_all.py`) |
| `frontend/src/features/chat_v2/__tests__/*.test.ts` | **EDIT/NEW** — assert generated KNOWN set == 18 + the 4 newest types still recognized (mostly covered by existing 693 staying green) |
| `docs/03-implementation/agent-harness-planning/02-architecture-design.md` (§SSE) | **EDIT** — note the wire-type catalog is now generated from `event_wire_schema.py` (single source) |
| `claudedocs/4-changes/feature-changes/CHANGE-035-event-schema-codegen.md` | **NEW** — change record |

**No `loop.py`**, **no `events.py`** (dataclasses untouched — registry is the wire layer, D5), **no new `LoopEvent` subclass**, **no DB / migration**, **no Azure-adapter change**, **no serializer rewrite** (only a parity test is added against `sse.py`).

---

## 5. Acceptance Criteria

- `event_wire_schema.py` declares all 18 current wire-types with field sets that **exactly match** `sse.py`'s real branch output (locked by the parity test).
- `python scripts/codegen/generate_event_schemas.py` regenerates `events.json` + `loopEvents.generated.ts` deterministically; running it twice produces no diff; `--check` exits 0 on the committed artifacts.
- `types.ts` re-exports the generated symbols; the hand-written interfaces/union/KNOWN set are removed; tsc EXIT 0; **Vitest 693 green** (zero behavior change — downstream `mergeEvent`/`chatService` gate/components unaffected).
- pytest parity test: each of the 17 wired event classes serializes to a wire-type ∈ registry with `data` keys (minus `trace_id`) == the registry field set; the 6 unwired classes still raise `NotImplementedError`; `len(KNOWN_LOOP_EVENT_TYPES) == len(WIRE_SCHEMA) == 18`.
- `check_event_schema_sync.py` is the **10th** lint in `run_all.py` (`10/10` green) and runs in CI `lint.yml` `v2-lints`; a deliberately-staled generated file makes it exit 1 (drift caught).
- All existing tests green; `mypy --strict src/` clean (0/N); **10/10 V2 lints (LLM SDK leak 0)**; pytest count ≥ prior (+ the new parity test cases); no `loop.py`/`events.py`/new-event/DB/Azure changes.

---

## 6. Deliverables

- [ ] `event_wire_schema.py`: `WIRE_SCHEMA` (18 entries) + TS-type vocab + `to_ts()` (US-1)
- [ ] `scripts/codegen/generate_event_schemas.py`: run + `--check` (US-2)
- [ ] generated `events.json` + `loopEvents.generated.ts` committed (US-2)
- [ ] `types.ts` re-export refactor (hand-written copies deleted) (US-2)
- [ ] `.gitattributes` LF for generated artifacts (cross-platform diff stability)
- [ ] pytest `test_event_wire_schema_parity.py` (serializer↔registry + unwired-raises + count) (US-3)
- [ ] `check_event_schema_sync.py` lint + `run_all.py` 9→10 + `lint.yml` `v2-lints` (US-3)
- [ ] FE Vitest: generated KNOWN set == 18 + recognition (US-4)
- [ ] `02-architecture-design.md §SSE` single-source note
- [ ] CHANGE-035 record + progress.md + retrospective.md

---

## 7. Workload Calibration

Scope class: **`medium-backend` (0.80)** — the bulk is backend tooling (registry + codegen + parity lint + parity test); the FE change is a mechanical re-export refactor (no mockup/page work). **Agent-delegated: yes** (57.64/57.65/57.66 proven staged-delegation pattern). `agent_factor` **`mechanical-greenfield-design-decisions` 0.65** — there are genuine greenfield design decisions (registry schema format, TS-type mini-language vocabulary, codegen output shape, FE re-export strategy) beyond a single mechanical port, consistent with the recent sub-class.

> Bottom-up est ~10 hr → class-calibrated commit ~8 hr (mult 0.80) → agent-adjusted commit ~5.2 hr (agent_factor 0.65).

Calibration caveat carried from 57.63/64/65/66: agent-delegated sprints have not produced a clean wall-clock measurement (`AD-Calibration-AgentDelegated-WallClock-Measure`, now 5 consecutive if this lands the same way); record this point as caveated, do NOT adjust the 0.65 baseline on it alone. **Watch**: this sprint has heavier genuine greenfield (a new codegen toolchain) than 57.66's pattern-mirror — if the ratio runs > 1.20 it is a candidate signal that "new-toolchain greenfield" deserves a distinct sub-class from "design-decisions on an existing pattern" (note in retro Q2, do not pre-split).

---

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| **D5 — dataclass fields ≠ wire shape** (the whole reason for Option 1) | registry authored from `sse.py`'s real branch output (Prong 2 reads each branch body, NOT the dataclass); parity test locks serializer↔registry equality forever |
| **18-payload transcription error** (wrong field name/type in registry) | parity test asserts exact key-set equality per wire-type → any transcription error fails the test immediately; tsc catches FE type mismatches |
| **Faithful-reproduction risk** (generated `types.ts` re-export changes downstream behavior) | generated interface names + field names + types reproduce the current hand-written ones exactly; gate = tsc 0 + Vitest 693 green + `mergeEvent` exhaustive `switch (never)` compiles (any divergence is a compile error) |
| **Cross-platform diff instability** (Windows-dev CRLF vs Linux-CI LF → false `--check` failures) | codegen writes explicit `\n` + trailing newline; `--check` normalises line endings before diffing; `.gitattributes` pins generated files to `eol=lf` |
| **Type-spec is key-parity-only** (parity test checks field NAMES, not that a value's runtime type matches the declared TS type) | accept as a known limitation (FE tsc + Vitest cover the type side); note carryover `AD-EventSchema-RuntimeTypeParity` (a future test could assert int-value→"number" etc.); do NOT over-build now (YAGNI) |
| **Two classes → one wire-type** (`ToolCallExecuted`/`ToolCallFailed`→`tool_call_result`) | Day-1 Prong 2 confirms whether both emit identical keys; if not, the differing fields are declared optional `?` in the registry and the parity test asserts each class's keys ⊆ schema |
| **`lint.yml` invocation style** (calls scripts individually vs via `run_all.py`) | Day-0 Prong 1 reads `lint.yml`; if it calls `run_all.py` the new lint is auto-included (no `.yml` edit); if individual, add the one line — mirror existing exactly |
| **Generated-file staleness false-confidence** | the `--check` lint in `run_all.py` + CI is the gate; a deliberately-staled-file test proves it fails (US-3 acceptance) |
| **Scope creep into A-5c / never-yielded events** | this sprint models ONLY the 18 existing wire-types; the 6 unwired events stay unwired (locked by the parity test); Inspector UI = A-5c (OOS §9) |
| **Module-level singleton test isolation** (Risk Class C) | autouse reset fixtures per `.claude/rules/testing.md` if the parity test touches the chat app singletons (it shouldn't — it calls `serialize_loop_event` directly) |

---

## 9. Out of Scope

- **A-5c diagnostic Inspector UI** — rich rendering of `prompt_built`/`context_compacted`/etc. (the 4 events currently land in `rawEvents` only); later FE sprint, downstream.
- **Wiring the 6 currently-unwired events** (`MemoryAccessed`/`ErrorRetried`/`LoopTerminated`/`Span*`/`MetricRecorded`) — requires `loop.py` emission decisions (A-1/A-4/Cat 8); this sprint locks them as unwired, it does not add them.
- **Rewriting `sse.py` to consume the registry** (the serializer keeps its hand-written branches; only a parity test is added — minimises risk to just-shipped 57.66 code; a future refactor could make the serializer build from the registry, carryover `AD-EventSchema-SerializerConsumesRegistry`).
- **Runtime-type parity** (asserting a value's runtime type matches the declared TS-spec) — key-parity only this sprint (`AD-EventSchema-RuntimeTypeParity`).
- **Generating the backend dataclasses or the serializer from the registry** — the registry is the *wire* layer only; `events.py` dataclasses + `sse.py` branches stay hand-written (D5).
- **`loop.py` / `events.py` changes / new event subclass / DB / Azure-adapter** — none needed.
- **OpenAPI / SSE `id:` line / resume** — separate concerns (cat-events §3).
