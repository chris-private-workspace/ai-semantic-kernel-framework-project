# Sprint 57.160 Plan — tool-anchored observation masking (env-gated) + reduction/retention A/B

**Summary**: Fix the `AD-Compaction-NoOp-On-Single-User-Turn-Chat-Path` effectiveness gap that the 57.159 drive-through surfaced — compaction triggers every over-budget turn but reduces 0 messages on the chat main flow because the `DefaultObservationMasker` anchors its keep-window on **user-message count** and a single `send` produces exactly one user turn (even across a 20-turn tool run). This sprint adds an env-gated **tool-result-recency** anchor mode to the masker (default OFF → byte-identical current behaviour) so that, within a single user turn, old tool-result blobs are tombstoned while the most-recent N survive. The rollout is **evidence-first (env lever OFF + A/B harness)**, mirroring the 57.139/57.144 discipline (AskUserQuestion pick: "B: env-gated + A/B harness"). A NEW `benchmark_tool_anchored_masking.py` measures reduction% + mechanical retention over a single-user-turn tool-heavy corpus; the flip-to-default decision is data-gated in a design note. Drive-through is **MANDATORY** — export the lever, run a long single-send tool chat, and confirm the 57.159 timeline marker renders a REAL reduction on the DEFAULT chat path (previously a no-op) while context is retained. Also makes concrete progress on `AD-Compaction-ToolAnchored-Preclear-Phase58` (57.139 deferred — same root fix). CHANGE-127 + design note (spike).

**Status**: Approved-to-execute (user AskUserQuestion 2026-07-07 — direction "compaction 續攻 / AD-Compaction-NoOp-On-Single-User-Turn-Chat-Path"; rollout "B: env-gated + A/B harness").
**Branch**: `feature/sprint-57-160-compaction-tool-anchored-masking`
**Base**: `main` HEAD `29da11e8` (chore flip Sprint 57.159 PR-pending → MERGED, #375)
**Slice**: closes `AD-Compaction-NoOp-On-Single-User-Turn-Chat-Path` (57.159 carryover) via lever + evidence; advances `AD-Compaction-ToolAnchored-Preclear-Phase58` (57.139 deferred, same root fix). Standalone spike in the engine-debt compaction range.
**Scope decisions**: (a) tool-anchored masking = an instance-config mode on `DefaultObservationMasker` (`tool_anchor_keep: int | None`), NOT a new masker class — reuses every existing injection site; (b) env-gated default OFF (`CHAT_COMPACTION_TOOL_ANCHORED_MASKING`) → existing 6 masker tests + byte-identical current path unchanged; (c) A/B core is deterministic/LLM-free (masking is deterministic) — reduction% + mechanical retention CI-safe; an optional real-LLM behavioural-retention arm is `RUN_AZURE_INTEGRATION`-gated (mirror 57.139); (d) NO wire/codegen/frontend — the 57.159 `context_compacted` marker already renders, so the lever ON makes it show a REAL reduction on the default path.

---

## 0. Background

### The gap (`AD-Compaction-NoOp-On-Single-User-Turn-Chat-Path`, 57.159 carryover)

The 57.159 compaction drive-through proved compaction **triggers every over-budget turn** (`token_usage > budget×0.75`) but **reduces 0 messages** on the chat main flow. Root cause: the masker's keep-window is anchored on **user-message count**, and the chat path runs exactly **one user message per `send`** — even a 20-turn tool run shares ONE user turn. So the reduction only fires across a cross-user-turn boundary (rehydrated multi-turn / mid-run injection), never within the single long tool run where the growth actually happens.

Observed: context grew **4k → 35k tokens** across one 20-turn send with **8 no-op compactions** (each a `context_compacted` marker showing `N → N`, 0 reduction).

### Why it matters (the missing capability)

The engine's compaction machinery is real (harness-proven in 57.139) and the marker is now visible (57.159), but on the DEFAULT chat path the token budget is never actually enforced within a long single-user-turn tool run → context grows unbounded → higher cost + eventual context-window pressure on genuinely long tool runs. This is an **effectiveness gap** (the machinery is correct but structurally unreachable on the main flow), not a correctness bug (retention was 0.99 in 57.159 — the agent still answered).

### Root cause (recon code read, file:line; ALL re-verified §checklist 0.1)

| Layer | Reality (on `main` HEAD `29da11e8`) | Anchor |
|-------|-------------------------------------|--------|
| Masker keep-window anchor | `user_indices = [i for i,m … if m.role=="user"]; if len(user_indices) <= keep_recent: return list(messages)` — user-turn count gate; single-send = 1 user turn ≤ 5 → returns unmasked | `observation_masker.py:62-64` |
| Structural compaction runs the masker | `self.masker.mask_old_results(rest_filtered, keep_recent=self.keep_recent_turns)` — inherits the user-anchor no-op | `structural.py:170-172` |
| PreClear (57.139) runs the SAME masker | reuses `DefaultObservationMasker`; `tombstoned == 0 → passthrough` on single-send | `preclear.py:139-158`, docstring `:24-29` explicitly defers the fix to `AD-Compaction-ToolAnchored-Preclear-Phase58` |
| `keep_recent` cannot help | it's a user-turn count; `keep_recent=0` hits the `user_indices[-0]==[0]` silent-full-keep bug (factory guards min 1) | `_category_factories.py:133-147` |
| Marker already renders (57.159) | `context_compacted` → `CompactionMarkerTurn`; shows `tokensBefore → tokensAfter` | `chatStore.ts` (57.159), `CompactionMarker.tsx` |

→ The fix must make the masker able to anchor on **tool-result recency** (keep last N `role=="tool"` results, tombstone older) so it reduces WITHIN a single user turn — independent of user-turn count.

### The design (backend-only Cat 4: 1 masker mode + 1 factory env branch + 1 A/B harness + tests; ZERO wire/codegen/frontend)

```
observation_masker.py
  DefaultObservationMasker.__init__(*, tool_anchor_keep: int | None = None)   # NEW instance config
  mask_old_results(messages, *, keep_recent=5):
    if self.tool_anchor_keep is not None:            # NEW branch (env-gated via factory)
        tool_idx = [i for i,m in enumerate(messages) if m.role == "tool"]
        if len(tool_idx) <= self.tool_anchor_keep: return list(messages)   # honest passthrough
        cutoff = tool_idx[-self.tool_anchor_keep]    # keep last N tool results intact
        tombstone every role=="tool" message with index < cutoff           # older blobs → tombstone
    else:                                            # EXISTING user-anchored path (byte-identical)
        <unchanged>

_category_factories.py
  _compaction_tool_anchored_keep() -> int | None     # reads CHAT_COMPACTION_TOOL_ANCHORED_MASKING
  make_chat_compactor: when set, inject DefaultObservationMasker(tool_anchor_keep=N)
    into StructuralCompactor(masker=…) AND PreClearCompactor(masker=…)      # both become effective
  default (unset/invalid) → no masker arg → byte-identical pre-57.160

scripts/benchmark_tool_anchored_masking.py           # NEW — mirror benchmark_layered_compaction.py
  single-user-turn multi-tool corpus → OFF vs ON reduction% + mechanical retention (deterministic)
  optional RUN_AZURE_INTEGRATION behavioural-retention arm (real cheap-tier answer survives)
```

WHY instance-config over a call param: the masker call site lives inside StructuralCompactor / PreClearCompactor (`self.masker.mask_old_results(...)`); those compactors don't forward a new call kwarg. Making tool-anchoring a MASKER instance property lets the factory construct the configured masker once and inject it into both compactors — zero compactor signature change, zero new call-site threading.

### Ground truth (recon head-start — code read on `main` HEAD `29da11e8`; ALL re-verified §checklist 0.1)

- `observation_masker.py:47-78` — `DefaultObservationMasker` has NO `__init__` today (stateless); adding a keyword-only ctor is additive.
- `observation_masker.py:62-64` — the user-anchor gate (the no-op source).
- `structural.py:124` — `self.masker = masker or DefaultObservationMasker()` (masker is already injectable).
- `preclear.py:97` — `self.masker = masker or DefaultObservationMasker()` (already injectable).
- `_category_factories.py:186-217` — `make_chat_compactor` constructs Structural + PreClear WITHOUT passing a masker today → they default to `DefaultObservationMasker()`.
- `_category_factories.py:150-165` — `_compaction_preclear_ratio()` is the pattern to mirror for the new env reader.
- `benchmark_layered_compaction.py` (57.139) — the harness scaffold to mirror (`load_cases`/`build_transcript`/`measure_case`/`build_report`/`main`; CI-safe core + Azure-gated arm); its docstring `:31-35` already names this exact fix.
- `test_observation_masker.py` — 6 existing tests construct `DefaultObservationMasker()` (no arg) → `tool_anchor_keep=None` → unchanged.

**Baselines (57.159 closeout)**: pytest 3180 · wire 26 · Vitest 927 · mockup 51 · mypy `src` 400 · run_all 11/11. Re-verify Day-0.

### STALE / drift findings (Day-0; full detail → progress.md — placeholder, filled in §checklist 0.1)

- **D-masker-ctor-absent** — confirm `DefaultObservationMasker` truly has no `__init__` (recon says stateless) so the additive ctor doesn't collide.
- **D-abc-signature** — confirm `ObservationMasker` ABC only declares `mask_old_results`; the impl `__init__` is impl-detail (no ABC change).
- **D-factory-masker-inject** — confirm StructuralCompactor + PreClearCompactor both accept `masker=` kwarg (recon: yes) so the factory can inject.
- **D-tool-msg-shape** — confirm tool results are `role=="tool"` with `name` + `tool_call_id` (recon: `chat.py:76-93`; masker already uses `msg.name`).
- **D-harness-import-shadow** — the 57.139 harness note flags `tests.unit.scripts` importlib-shadow + Windows cp950 print; mirror the same guards.

## 1. Sprint Goal

Add an env-gated tool-result-recency masking mode (`CHAT_COMPACTION_TOOL_ANCHORED_MASKING`, default OFF → byte-identical) that makes structural + preclear compaction actually reduce tokens within a single-user-turn tool run, PROVEN by (a) a new deterministic A/B harness reporting OFF-vs-ON reduction% + mechanical retention over a single-user-turn tool corpus, (b) the full gate set, and (c) a **MANDATORY drive-through** — lever ON, a long single-send tool chat renders the 57.159 timeline marker with a REAL reduction on the DEFAULT path (previously a no-op) while context is retained (agent still answers). Produces CHANGE-127 + a spike design note carrying the data-gated flip-to-default verdict.

## 2. User Stories

- **US-1** (masking mode): 作為 platform engineer，我希望 masker 能以 tool-result recency 為錨點遮罩舊 tool 結果，以便在單一 user turn 的長 tool run 內真正縮減 context。
- **US-2** (env lever): 作為 ops，我希望以 `CHAT_COMPACTION_TOOL_ANCHORED_MASKING` env 控制此模式且預設 OFF，以便在有證據前現況零行為變更。
- **US-3** (A/B evidence): 作為 decision owner，我希望一支確定性 A/B harness 量測 OFF-vs-ON 的 reduction% 與 mechanical retention，以便用數據決定是否 flip default。
- **US-4** (drive-through, MANDATORY): 作為 user，我希望開啟 lever 後在真 chat-v2 的長 tool send 內看到 57.159 marker 顯示 REAL 縮減且對話上下文仍保留，以便確認引擎在主流量真的壓縮而非 no-op。
- **US-5** (closeout): 交付 CHANGE-127 + design note（8-point gate）+ calibration + navigators + AD 收尾。

## 3. Technical Specifications

### 3.0 Architecture (backend-only Cat 4; NO wire/codegen/frontend/migration)

```
EDIT  backend/src/agent_harness/context_mgmt/observation_masker.py     # + __init__(tool_anchor_keep) + tool-anchored branch
EDIT  backend/src/api/v1/chat/_category_factories.py                   # + _compaction_tool_anchored_keep() + inject masker
NEW   backend/scripts/benchmark_tool_anchored_masking.py               # A/B reduction + retention harness (mirror 57.139)
NEW   backend/tests/fixtures/context_mgmt/tool_anchored_masking_cases.yaml   # single-user-turn tool corpus
NEW   backend/tests/unit/scripts/test_benchmark_tool_anchored_masking.py     # CI-safe harness tests
EDIT  backend/tests/unit/agent_harness/context_mgmt/test_observation_masker.py   # + tool-anchored mode tests (6 existing unchanged)
EDIT  backend/tests/.../test_*category_factories*.py (if present)      # + env-reader test
UNTOUCHED  loop.py · sse.py · event_wire_schema.py · generated/* · frontend/* · migrations   # marker already renders (57.159)
```

### 3.1 Tool-anchored masking mode (US-1) — `observation_masker.py`

- Add keyword-only `__init__(self, *, tool_anchor_keep: int | None = None)`; store on `self`.
- In `mask_old_results`, branch at the top: if `self.tool_anchor_keep is not None`, take the tool-anchored path; else the existing user-anchored path (byte-identical).
- Tool-anchored path: `tool_idx = [i for i,m in enumerate(messages) if m.role == "tool"]`; if `len(tool_idx) <= self.tool_anchor_keep` → honest `return list(messages)` (nothing old enough); else `cutoff = tool_idx[-self.tool_anchor_keep]`; tombstone every `role=="tool"` message at index `< cutoff` using the SAME tombstone string format (`[REDACTED: tool {name} result; bytes={n}]`); never touch system/user/assistant (`tool_calls` provenance preserved — the caller already strips system/HITL before calling).
- Reuse the existing tombstone builder (extract a small `_tombstone(msg)` helper if it de-dupes the two branches cleanly; else inline identically).

### 3.2 Env lever + factory injection (US-2) — `_category_factories.py`

- Add `_compaction_tool_anchored_keep() -> int | None` mirroring `_compaction_preclear_ratio()`: read `CHAT_COMPACTION_TOOL_ANCHORED_MASKING`; parse int; return `N` iff `N >= 1` else `None` (unset/invalid/0 → OFF).
- In `make_chat_compactor`: compute `tool_anchor = _compaction_tool_anchored_keep()`; if not None, build `masker = DefaultObservationMasker(tool_anchor_keep=tool_anchor)` and pass `masker=masker` into `StructuralCompactor(...)` AND (inside the preclear branch) `PreClearCompactor(...)`. When None → construct as today (no masker arg) → byte-identical.
- Docstring the knob (WHY: single-user-turn no-op fix; default OFF evidence-first; interacts with `CHAT_COMPACTION_PRECLEAR_RATIO`).

### 3.3 A/B reduction + retention harness (US-3) — `scripts/benchmark_tool_anchored_masking.py` + corpus

- Mirror `benchmark_layered_compaction.py`: `load_cases` / `build_transcript` / `measure_case` / `build_report` / `report_to_markdown` / `main`; importable reusable core; CI-safe (real `TiktokenCounter`, NO Azure for the core).
- Corpus models the REAL chat path: **single user turn** followed by K assistant→tool round-trips (`n_tool_calls` within one user turn), varying `tool_result_chars` / `tool_anchor_keep`.
- Per case measure: `off_reduction = (L0 - mask_OFF)/L0` (expected ~0, confirming the no-op), `on_reduction = (L0 - mask_ON)/L0` (the fix's yield), and **mechanical retention** = the last `tool_anchor_keep` tool results survive byte-intact AND every `assistant.tool_calls` provenance survives AND system preserved (a boolean per case).
- Verdict fields: `mean_on_reduction`, `mean_off_reduction`, `retention_ok_rate`, `recommend_default_on` = (`mean_on_reduction ≥ materiality` AND `mean_off_reduction ≈ 0` AND `retention_ok_rate == 1.0`). Materiality floor documented (e.g. ≥ 0.10).
- Optional `RUN_AZURE_INTEGRATION` behavioural arm (mirror 57.139 L3-gate): after ON-masking, a real cheap-tier answer to a probe still references the retained recent tool result → behavioural retention proxy (design-note only, gate-optional).
- Mirror the 57.139 guards: `sys.stdout.reconfigure(utf-8)` for cp950; `tests.unit.scripts` importlib shadow handling.

### 3.4 What is explicitly NOT done

- **NOT flipping the default ON** — evidence-first; the flip decision is the design-note verdict (data-gated), a separate follow-on if recommended.
- **NOT** changing `keep_recent` semantics / the user-anchored path (multi-turn behaviour byte-identical).
- **NOT** a new wire event / codegen / frontend change — the 57.159 marker already surfaces the reduction; this sprint makes the reduction non-zero on the default path when the lever is ON.
- **NOT** flipping `CHAT_COMPACTION_PRECLEAR_RATIO` default (that is `AD-Compaction-Preclear-PerTenant-Phase58` / a separate lever) — but the tool-anchored masker MAKES preclear effective when both are enabled.
- **NOT** per-tenant tool-anchor policy — global env lever only (per-tenant → carryover AD).

### 3.5 Validation (US-1..US-5)

Gates: mypy `src` 400 · run_all 11/11 · pytest 3180 + new · Vitest 927 (unchanged — no FE) · mockup 51 (`diff` empty — no CSS) · `npm run lint && npm run build` (NO `--silent`) · black/isort/flake8 clean · LLM-SDK-leak clean (harness Azure arm is lazy-imported via ChatClient ABC / `build_azure_model_profile`, no direct SDK). Plus the §3.6 drive-through (MANDATORY — user-facing chat-v2 marker).

### 3.6 Drive-through (US-4, MANDATORY — real UI + real backend + real LLM)

1. Clean restart (Risk Class E): kill stale uvicorn reloader + orphan spawn-workers on :8000; start a single no-`--reload` backend with `CHAT_COMPACTION_TOOL_ANCHORED_MASKING=<N>` (+ a low `CHAT_COMPACTION_TOKEN_BUDGET` to trigger within one send); confirm sole port owner + startup log.
2. Open real chat-v2 (`/chat-v2`, real_llm mode) + Azure gpt-5.2; send a long single tool-using prompt that drives many tool round-trips within ONE user turn.
3. Confirm the 57.159 `CompactionMarker` renders a REAL reduction (`tokensBefore > tokensAfter`, e.g. `12,480 → 6,210 (structural · N msgs)`) on the DEFAULT path — contrast with the 57.159 no-op `N → N`.
4. Confirm context retention: a follow-up question about an early fact still answers correctly (the recent-N tool results + provenance survived; older blobs tombstoned).
5. Screenshot + observed-vs-intended → progress.md Day 3; note this is the same finding 57.159 caught, now DRIVEN to a real reduction via the lever.

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 1 | `backend/src/agent_harness/context_mgmt/observation_masker.py` | EDIT (+ `__init__` + tool-anchored branch) |
| 2 | `backend/src/api/v1/chat/_category_factories.py` | EDIT (+ env reader + masker injection) |
| 3 | `backend/scripts/benchmark_tool_anchored_masking.py` | NEW (A/B harness) |
| 4 | `backend/tests/fixtures/context_mgmt/tool_anchored_masking_cases.yaml` | NEW (corpus) |
| 5 | `backend/tests/unit/scripts/test_benchmark_tool_anchored_masking.py` | NEW (CI-safe harness tests) |
| 6 | `backend/tests/unit/agent_harness/context_mgmt/test_observation_masker.py` | EDIT (+ tool-anchored mode tests; 6 existing unchanged) |
| 7 | `backend/tests/**/test_*category_factories*` | EDIT (+ env-reader test — if a factory test module exists; else fold into an integration test) |
| — | `loop.py` · `sse.py` · `event_wire_schema.py` · `generated/*` · `frontend/*` · `alembic/versions/*` | **UNTOUCHED** |

## 5. Acceptance Criteria

1. `DefaultObservationMasker(tool_anchor_keep=N)` tombstones tool results older than the last N `role=="tool"` messages within a single user turn; `tool_anchor_keep=None` is byte-identical to today (existing 6 masker tests pass unchanged).
2. `CHAT_COMPACTION_TOOL_ANCHORED_MASKING` unset/invalid/0 → factory returns the byte-identical pre-57.160 compactor (structural + optional preclear with default masker); `>=1` → both compactors get the tool-anchored masker.
3. `benchmark_tool_anchored_masking.py` runs CI-safe (no Azure) and reports `mean_off_reduction ≈ 0`, `mean_on_reduction` materially > 0, `retention_ok_rate == 1.0`, and a `recommend_default_on` verdict over the single-user-turn corpus; CI-safe unit tests cover the core.
4. All gates green (pytest 3180+new · mypy 400 · run_all 11/11 · lint/build · black/isort/flake8 · LLM-SDK-leak) with FE untouched (Vitest 927 / mockup 51 unchanged).
5. **Drive-through PASS (MANDATORY, real UI + backend + LLM)** — lever ON, a long single-send tool chat renders the 57.159 marker with a REAL `tokensBefore > tokensAfter` on the DEFAULT path + context retained; screenshot + observed-vs-intended in progress.md. (NOT gate-only.)
6. `AD-Compaction-NoOp-On-Single-User-Turn-Chat-Path` CLOSED (via lever + evidence + drive-through); `AD-Compaction-ToolAnchored-Preclear-Phase58` advanced/annotated; CHANGE-127 + design note (8-point gate); calibration recorded; navigators + next-phase-candidates updated.

## 6. Deliverables

- [ ] US-1 tool-anchored masking mode on `DefaultObservationMasker`
- [ ] US-2 `CHAT_COMPACTION_TOOL_ANCHORED_MASKING` env lever + factory injection (default OFF)
- [ ] US-3 `benchmark_tool_anchored_masking.py` + corpus + CI-safe tests + verdict
- [ ] US-4 drive-through PASS (real reduction on default path + retention) + screenshots
- [ ] US-5 CHANGE-127 + design note + calibration + navigators + AD closeout

## 7. Workload Calibration

- Scope class **NEW `compaction-tool-anchored-masking-spike` 0.60** (anchored to `layered-compaction-spike` 0.60 (57.139) — same Cat 4 evidence-first shape: a bounded env-gated masking-mode change + a deterministic A/B measurement harness + a real-code core ≥~3.5 hr; also kin to `verification-context-hygiene-spike` 0.60 (57.136) / `guardrail-restrict-spike` 0.60 (57.137). Set 0.60 NOT a tiny-code 0.85 re-point because the real-code core — masker branch + factory injection + a ~250-line harness + corpus + ~20 tests — holds the 0.60 per the 57.137 lesson; NOT a ~10-line surface change wrapped in full ceremony. The MANDATORY drive-through adds ceremony but the harness+masker code is genuine implementation).
- **Agent-delegated: no** (parent-direct — a subtle Cat-4 correctness-adjacent masker change + a drive-through the parent must drive; agent_factor 1.0 → 3-segment form).
- Bottom-up est ~5.5 hr (masker mode + tests ~1.5 hr · factory env + test ~0.75 hr · harness + corpus + CI tests ~2 hr · drive-through ~1 hr · closeout + design note ~0.75 hr — wait, sums ~6 hr; use ~5.5-6 hr) → class-calibrated commit ~3.5 hr (×0.60). Day-4 retro Q2 verifies; if ratio out of [0.7, 1.2] band → re-point (2nd data point of the new class → validation).

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| Over-tombstoning the working set (agent loses a recent tool result it needs mid-run) | `tool_anchor_keep` keeps the last N intact + provenance (`tool_calls`) always preserved; drive-through §3.6 step 4 validates behavioural retention; harness `retention_ok_rate` asserts mechanical retention |
| Env lever ON silently changes multi-turn behaviour | tool-anchored path is a DISTINCT branch keyed on the instance flag; when OFF the user-anchored path is byte-identical (existing 6 tests + factory-default guard) |
| Harness import shadow / cp950 print (Risk carryover from 57.139) | mirror the 57.139 guards (`tests.unit.scripts` importlib shadow, `sys.stdout.reconfigure(utf-8)`) |
| Stale `--reload` backend masks the env-gated wiring (Risk Class E) | clean single-process no-`--reload` restart with the env set BEFORE start; confirm sole port owner + startup log; verify the LIVE worker via `Win32_Process` PID/PPID/StartTime if SO_REUSEADDR orphans recur |
| Backend currently running with non-default `keep_recent=1` (57.159 leftover) | restart to defaults first, then set only the 57.160 lever for the drive-through |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- Flipping `CHAT_COMPACTION_TOOL_ANCHORED_MASKING` default ON — data-gated follow-on if the design-note verdict recommends (new AD if recommended).
- Per-tenant tool-anchor policy (mirror the per-tenant model/config pattern) — new carryover AD.
- Tool-anchored **PreClear default-on** (`AD-Compaction-Preclear-PerTenant-Phase58`) — separate lever; this sprint only makes preclear *effective* when enabled.
- Correlating the marker to its Trace-tab COMPACTION span (`AD-Compaction-Marker-Inspector-Trace-Correlate`, 57.159) — frontend, separate slice.
