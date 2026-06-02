# Sprint 57.67 Retrospective — Event Schema Codegen + CI Parity Gate (A-5b)

**Closed**: 2026-06-02
**Plan**: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-67-plan.md`

---

## Q1 — What shipped?

A declarative single-source wire-schema registry (`event_wire_schema.py`, 18 wire-types) that **generates** the frontend event contract (`events.json` + `loopEvents.generated.ts` — 18 interfaces + `LoopEvent` union + `KNOWN_LOOP_EVENT_TYPES`), consumed via a `types.ts` re-export (hand-written copies deleted). Drift is locked by two gates: a pytest serializer↔registry parity test (30 cases) + a `check_event_schema_sync.py` lint (10th V2 lint) wired into `run_all.py` AND the CI `lint.yml` `v2-lints` required check. Automates the triple hand-maintained surface 57.66 §8 flagged. Zero behavior change (tsc 0 / Vitest 697 / pytest 1994 / build ✓).

## Q2 — Estimate accuracy + calibration

- Scope class **`medium-backend` (0.80)** + **`agent_factor mechanical-greenfield-design-decisions` 0.65**. Agent-delegated: **yes** (2 staged `code-implementer` agents + parent independent re-verification).
- Plan committed ~5.2 hr (10 bottom-up × 0.80 × 0.65). **No clean wall-clock** — work spanned 2 delegated agent runs + parent verify across a session; **5th consecutive agent-delegated sprint with no clean measurement** (57.63/64/65/66/67) → reinforces `AD-Calibration-AgentDelegated-WallClock-Measure`.
- **KEEP 0.65**, no baseline change (caveated single point, per the rollback rule's "no clean measure → do not adjust").
- **Watch (plan §7 prediction held qualitatively)**: this was heavier genuine greenfield (a NEW codegen toolchain + TS-type mini-language + flat-vs-nested reconciliation) than 57.66's pattern-mirror, AND Stage-1 shipped a wrong shape that Stage-2 had to fix (intra-sprint rework). That rework is a signal "new-toolchain greenfield" carries more design risk than "design-decisions on an existing pattern". Logged as a watch (`AD-AgentFactor-NewToolchain-Greenfield-Watch`); do NOT pre-split — needs a clean-measured data point.

## Q3 — What went well?

- **The staged-delegation + reconciliation discipline caught a real bug.** Stage-1's generated TS used a FLAT `{ type, trace_id, ...fields }` shape; the working `types.ts` is NESTED `{ type, data: {...} }` (the store reads `ev.data.X`). Re-exporting flat would have broken tsc everywhere. Stage-2's mandatory "read current types.ts, diff, reconcile to green" step found it and fixed the codegen emission — without touching the registry/events.json/parity test.
- **Day-0's full 18-field transcription** (D-DAY0-2) gave the implementer exact field NAMES/SET ground truth → zero field-level drift; the parity test locks it.
- **Parent independent re-verification** (57.64 discipline) re-ran every authoritative gate (codegen --check, run_all 10/10, frontend tsc + Vitest 697 + build, backend parity) rather than trusting agent reports — important given Stage-1's report said "matches exactly" while the shape was wrong.
- Architecture decision surfaced to user (AskUserQuestion) BEFORE coding, because Day-0 contradicted the capstone's "dataclass→ts" framing — avoided building the wrong thing.

## Q4 — What to improve? (ADs)

- **NEW `AD-Day0-Codegen-Existing-Shape-Capture`** (root cause of the Stage-1 miss): when codegen targets an EXISTING typed surface, Day-0 Prong-2 must capture the existing artifact's STRUCTURAL SHAPE (nested vs flat, wrapper keys), not just the field name set. My D-DAY0-2 table listed the inner `data` fields correctly but did not flag that the FE interfaces nest under `data:` — so the Stage-1 spec implicitly described a flat interface. A codegen-from-existing-types sprint should read 1-2 of the existing target interfaces verbatim and pin their exact shape in the Day-0 findings + the implementer spec. Cheap (~2 min); would have prevented the Stage-1→Stage-2 rework.
- **Carryover ADs** (out of scope, logged): `AD-EventSchema-RuntimeTypeParity` (parity test is key-name only; a future test could assert a value's runtime type matches the declared TS-spec), `AD-EventSchema-SerializerConsumesRegistry` (a future refactor could make `sse.py` build from the registry instead of being locked-by-test), `AD-LintYml-RunAll-Divergence` (lint.yml runs 6 lints individually + now mine = 7; run_all.py runs 10 — pre-existing 3-lint local-only gap, not this sprint's to fix but worth a future reconciliation).

## Q5 — Risks realized?

- **Cross-platform line endings** (plan §8): real (git warned LF→CRLF on the planning docs). Mitigated by codegen writing explicit `\n` + `--check` normalizing + `.gitattributes eol=lf` on generated files. CI (Linux) `--check` is clean.
- **Faithful-reproduction risk** (plan §8): materialized as the flat-vs-nested shape error — caught by the tsc-0 + Vitest-697 gate exactly as designed (Stage-2 reconciliation).
- **Two classes → one wire-type**: did NOT materialize (D-DAY0-3: `ToolCallExecuted`/`ToolCallFailed` emit identical keys → single clean schema entry).

## Q6 — Carryover

- Area-A capstone: **A-5b shipped** (drift now mechanically un-mergeable via the required CI check). Remaining: **A-5c** (diagnostic Inspector UI — the 4 diagnostic events still land in `rawEvents` only), A-3b (Cat 11 HANDOFF), A-4 (loop tracer), A-6 (frontend). `AD-RealLLM-E2E-Live-Confirmation` (blocker removed 57.66, gated on Azure secrets).
- ADs above (`AD-Day0-Codegen-Existing-Shape-Capture` candidate for sprint-workflow §Step 2.5 Prong-2 fold-in after 1-2 more codegen-from-existing-types data points; `AD-EventSchema-RuntimeTypeParity`; `AD-EventSchema-SerializerConsumesRegistry`; `AD-LintYml-RunAll-Divergence`; `AD-AgentFactor-NewToolchain-Greenfield-Watch`).

## Q7 — N/A (feature ship)

No design-note extract required — this is a feature/tooling sprint, not a spike (per sprint-workflow §Step 5.5: spike-extract applies to new-domain spikes, not continuation/tooling).
