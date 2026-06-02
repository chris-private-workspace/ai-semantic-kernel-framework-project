# Sprint 57.67 Progress — Event Schema Codegen + CI Parity Gate (A-5b)

**Plan**: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-67-plan.md`
**Checklist**: `…/sprint-57-67-checklist.md`
**Branch**: `feature/sprint-57-67-event-schema-codegen` (from main `c42ebfd3`)

---

## Day 0 — 2026-06-02 — Plan-vs-Repo Verify (Prong 1+2+3 + tooling/CI) → **GO**

Architecture pre-locked (user AskUserQuestion 2026-06-02): **declarative wire-schema registry** (Option 1). First codebase-researcher audit (plan §0, D1-D5) pre-confirmed the architecture pivot; this Day-0 entry records the residual content/tooling/CI findings needed before Day 1 code.

### Drift / verification findings

| ID | Prong | Finding | Implication |
|----|-------|---------|-------------|
| **D-DAY0-1** | 1 path | Confirmed: `backend/src/agent_harness/_contracts/events.py` (25 frozen dataclasses) / `backend/src/api/v1/chat/sse.py` (`serialize_loop_event` `:97`, `NotImplementedError` `:361`, `_jsonable isinstance UUID` `:387`, `trace_id` inject `:116`) / `frontend/src/features/chat_v2/types.ts` / `…/services/chatService.ts` gate `:121`. `scripts/codegen/` + `events.json`/`events.ts`/`.gitattributes`-for-generated do NOT exist (D4 confirmed). | Plan §4 paths correct; greenfield codegen confirmed |
| **D-DAY0-2** | 2 content | **Full 18 wire-type field-set transcription from sse.py branch bodies** (registry ground truth — see table below). `Thinking → None` skip; 6 unwired (`MemoryAccessed`/`ErrorRetried`/`LoopTerminated`/`SpanStarted`/`SpanEnded`/`MetricRecorded`) → `NotImplementedError`. | `WIRE_SCHEMA` field NAMES + SET come from here (parity test enforces); TS TYPES come from current `types.ts` interfaces (tsc+Vitest enforce) |
| **D-DAY0-3** | 2 content | `tool_call_result`: `ToolCallExecuted` (`:182`) + `ToolCallFailed` (`:194`) emit **IDENTICAL key set** `{tool_call_id, tool_name, duration_ms, result, is_error}`. | NO optional-field divergence — single clean schema entry (resolves plan §8 "two classes → one wire-type" risk) |
| **D-DAY0-4** | 2 content | `trace_id` is **universal**, injected by `serialize_loop_event` wrapper (`:116`, value `trace_ctx.trace_id if trace_ctx else None`), NOT present in any branch's `data` dict. | Registry models the 18 branch field sets; `trace_id: string \| null` declared once as a shared base (generated interfaces extend it); parity test compares `data` keys **minus `trace_id`** |
| **D-DAY0-5** | tooling/CI | **`lint.yml` does NOT call `run_all.py`** — it runs **6 lints individually** (Lint 1-6: duplicate_dataclass / cross_category_import / sync_callback / llm_sdk_leak / ap1 / promptbuilder) + a `pytest tests/unit/scripts/lint` step. `run_all.py` has **9**. Pre-existing CI↔local divergence (3 lints local-only: sole_mutator / rls_policies / ap4_placeholder). | The parity lint must be **added as a new `lint.yml` step** to gate PRs (required check `v2-lints`) AND to `run_all.py` (10th, local). **lint.yml edit = CI/CD change → flag for user authorization at push.** Do NOT attempt to reconcile the pre-existing 6-vs-9 divergence (out of scope) |
| **D-DAY0-6** | design | Codegen must load `event_wire_schema.py` via `importlib.util.spec_from_file_location` (by file path), NOT a package import. | Lint runs in CI without installing the backend package / sys.path juggling. `event_wire_schema.py` MUST be pure stdlib (dict + `to_ts` helper, no `agent_harness`/sqlalchemy imports) |
| **D-DAY0-7** | tooling | Lint scripts run from **repo root** in both `run_all.py` (`subprocess [python, script, *args]`) and `lint.yml` (`python scripts/lint/X.py`). | Codegen + lint use repo-root-relative paths (`Path(__file__).parents[2]`) for both the backend source + the frontend generated dir |
| **D-DAY0-8** | 2 content | `_jsonable` post-FIX-025 = `isinstance(value, UUID)` (`:387`); UUID→str, datetime→isoformat. So `session_id`/`request_id`/`approval_request_id`/`subagent_id`/`parent_session_id` are `string \| null` on the wire (str(UUID) or None). | TS-type-spec for those fields = `string \| null` (match current `types.ts`) |

### D-DAY0-2 — the 18 wire-types + branch field sets (registry ground truth, `trace_id` universal-base omitted)

| # | wire-type | source event(s) | data fields (name → TS type, per types.ts) |
|---|-----------|-----------------|---------------------------------------------|
| 1 | `loop_start` | LoopStarted | `session_id: string\|null`, `request_id: string` |
| 2 | `turn_start` | TurnStarted | `turn_num: number` |
| 3 | `llm_request` | LLMRequested | `model: string`, `tokens_in: number` |
| 4 | `llm_response` | LLMResponded | `content: string`, `tool_calls: {id,name,arguments}[]`, `thinking: <match types.ts>`, `cached_input_tokens: number` |
| 5 | `tool_call_request` | ToolCallRequested | `tool_call_id: string`, `tool_name: string`, `args: Record<string,unknown>` |
| 6 | `tool_call_result` | ToolCallExecuted, ToolCallFailed | `tool_call_id: string`, `tool_name: string`, `duration_ms: number`, `result: string`, `is_error: boolean` |
| 7 | `loop_end` | LoopCompleted | `stop_reason: string`, `total_turns: number`, `cached_input_tokens: number`, `cache_hit_rate: number` |
| 8 | `approval_requested` | ApprovalRequested | `approval_request_id: string\|null`, `risk_level: string` |
| 9 | `approval_received` | ApprovalReceived | `approval_request_id: string\|null`, `decision: string` |
| 10 | `guardrail_triggered` | GuardrailTriggered | `guardrail_type: string`, `action: string`, `reason: string` |
| 11 | `tripwire_triggered` | TripwireTriggered | `violation_type: string`, `detail: string` |
| 12 | `verification_passed` | VerificationPassed | `verifier: string`, `verifier_type: string`, `score: number` |
| 13 | `verification_failed` | VerificationFailed | `verifier: string`, `verifier_type: string`, `reason: string`, `suggested_correction: <match types.ts>` |
| 14 | `subagent_spawned` | SubagentSpawned | `subagent_id: string\|null`, `mode: string`, `parent_session_id: string\|null` |
| 15 | `subagent_completed` | SubagentCompleted | `subagent_id: string\|null`, `summary: string`, `tokens_used: number` |
| 16 | `context_compacted` | ContextCompacted | `tokens_before: number`, `tokens_after: number`, `compaction_strategy: string`, `messages_compacted: number`, `duration_ms: number` |
| 17 | `prompt_built` | PromptBuilt | `messages_count: number`, `estimated_input_tokens: number`, `cache_breakpoints_count: number`, `memory_layers_used: string[]`, `position_strategy_used: string`, `duration_ms: number` |
| 18 | `state_checkpointed` | StateCheckpointed | `version: number` |

(`thinking` + `suggested_correction` nullability deferred to the exact `types.ts` interface — the working FE contract is authoritative for nullability/optional; the implementer reads `types.ts` and reproduces exactly. Field NAME/SET is sse.py-authoritative; field TYPE is types.ts-authoritative.)

### go/no-go
**GO** — architecture pre-validated; all paths confirmed; the 18 field sets are fully transcribed (ground truth above); the only CI nuance (D-DAY0-5 lint.yml individual-6) is resolved by adding a step (flagged for push authorization). Residual implementation detail = faithful TS-type reproduction from `types.ts`, handled by the Stage-1/2 implementer reading the file.

### Plan deltas folded
- §8 risk "two classes → one wire-type" **resolved** (D-DAY0-3: identical keys, no optional split needed).
- §3.4 lint.yml "no-op if it calls run_all.py" **resolved to: it does NOT** (D-DAY0-5) → add a `lint.yml` step (CI/CD change, push-gated).

---

## Day 1+2 — 2026-06-02 — Implementation (staged code-implementer delegation)

**Stage 1 (backend)** — `code-implementer` agent: `event_wire_schema.py` (`WIRE_SCHEMA` 18 entries + `BASE_FIELDS` + `LLMToolCall` + `validate_ts_type`, pure stdlib) + `scripts/codegen/generate_event_schemas.py` (importlib-by-path load + events.json + loopEvents.generated.ts + `--check`) + `test_event_wire_schema_parity.py` (30 cases). Backend green: parity 30 passed, full pytest 1994/4 skipped (+30), mypy src 320/0, SDK leak 0, codegen idempotent. Reproduced richer-than-table TS types from types.ts (`score: number|null`, `reason: string|null`, `verifier_type` literal union, `LLMToolCall`, `thinking`/`suggested_correction` nullable).

**Stage 2 (FE + lint + tests)** — `code-implementer` agent: reconciled a **Stage-1 shape error** — generated TS was FLAT `{type, trace_id, ...fields}` but working `types.ts` is NESTED `{type, data:{...}}` (store reads `ev.data.X`). Fixed codegen `render_generated_ts` to emit nested `data: { trace_id?: string|null; <fields> }` (trace_id optional — wire carries it, fixtures/HITLTurn omit it); did NOT touch registry/events.json/parity test. Swapped `types.ts` → `export * from "./generated/loopEvents.generated"` (preserved Block/Turn/Session/ToolCallEntry/ApprovalEntry/Chat* non-event content). `.gitattributes` eol=lf for generated. `check_event_schema_sync.py` (10th lint) + `run_all.py` 9→10. FE test (`eventSchema.generated.test.ts`, 4 cases). FE green: tsc 0, Vitest 697 (693+4), build 4.18s, run_all 10/10, drift-catch proven (exit 1→regen→0).

### Parent independent re-verification (57.64 discipline)
Re-ran every authoritative gate myself (not trusting agent reports — Stage-1's report said "matches exactly" while the shape was wrong): read regenerated `loopEvents.generated.ts` (confirmed nested) + `types.ts` (confirmed clean re-export + preserved content); `codegen --check` exit 0; `run_all.py` **10/10**; backend parity **30 passed**; frontend `tsc` **0**; `Vitest` **697 passed (126 files)**; `build` ✓ **3.90s**. All green.

## Day 3+4 — 2026-06-02 — CI wiring + closeout

- **CI gate** (user-authorized Option A, 2026-06-02): `.github/workflows/lint.yml` `v2-lints` job += "Lint 7 — event schema codegen parity" step (`check_event_schema_sync.py`). v2-lints is a required status check → drift un-mergeable (US-3 satisfied). (User chose A over B new-workflow / C local-only after being shown B's enforcement gap.)
- **Docs**: CHANGE-035 + this progress.md + retrospective.md (Q1-Q7) + calibration-log §3 + MEMORY subfile/pointer + CLAUDE.md lean.
- Checklist Day 0-4 all `[x]` except commit/push/PR (user-gated).
- **Calibration**: `medium-backend` 0.80 + `agent_factor mechanical-greenfield-design-decisions` 0.65 CAVEATED (5th consecutive no-clean-wall-clock); new `AD-AgentFactor-NewToolchain-Greenfield-Watch` (Stage-1 rework signals heavier greenfield than a pattern-mirror — no clean measure to confirm).
- **Key AD** (`AD-Day0-Codegen-Existing-Shape-Capture`): the Stage-1 flat-vs-nested miss traces to Day-0 D-DAY0-2 listing inner `data` field names but not flagging the FE interface's nested wrapper shape → codegen-from-existing-types Day-0 must pin the target artifact's structural shape verbatim, not just field names.

---
