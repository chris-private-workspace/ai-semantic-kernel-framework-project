# Sprint 57.163 Plan — Tool-error reflection rare-path drive-through + weaker-model A/B

**Summary**: Closes 2 Tool-range (Cat 2) evidence carryovers from Sprint 57.144: **③1 `AD-Tool-Error-Reflection-Loop-RarePath-DriveThrough`** — the reflection on the RARE executor-itself-raises path (`loop.py:3068`) was code-covered but NEVER drive-through verified (the dominant `executor._build_failure` path was); and **③4 reflection weaker-model re-check** — the 57.144 A/B measured `fix_delta +0.00%` on the STRONG model (→ lever kept OFF) but the harness has no model knob to test whether a WEAKER model has headroom. Scope decision: this is an evidence/verification slice, NOT a behavior change — the rare-path reflection code stays byte-identical (we verify it, don't rewrite it), and the lever default stays OFF (this sprint only GATHERS the weaker-model evidence; any default flip is a separate decision). **Day-0 re-scope (user 方案 A, 2026-07-09)**: Day-0 found the rare path is near-unreachable on the 主流量 (executor turns every failure into a `ToolResult`, so it does not self-raise) → ③1 is verified by an **integration fault-inject test** (not a real chat-v2 drive-through, which cannot be staged honestly for a near-dead branch), labelled **gate-only** + a reality finding + a follow-on AD. ③4's weaker-model A/B still runs against **real Azure**. This is a **pure-backend evidence slice** (no user-driven UI → Drive-Through constraint's pure-backend exemption; reports say "gate-only", never imply usability). NO new design note (57.144 design note 48 follow-on; A/B numbers recorded in the CHANGE).

**Status**: Approved-to-execute (user AskUserQuestion pick 2026-07-09: "③1+③4 reflection 驗證 slice"; engine-debt program Tool range, kickoff after 57.162)
**Branch**: `feature/sprint-57-163-tool-reflection-evidence`
**Base**: `main` HEAD `f4828495` (57.162 DAG soft-enforce, PR #381) + the 57.162 flip-doc commit `2458b46e` (docs-only)
**Slice**: closes ③1 + ③4 (Tool range 2 of ~4 open ADs); standalone evidence slice (not an arc)
**Scope decisions**: (a) rare-path reflection code UNCHANGED — we verify it, don't rewrite; (b) **Day-0 re-scope**: ③1 verified by an integration fault-inject test (inject a raising executor → assert `loop.py:3068` produces the reflection observation + `error_taxonomy`), labelled gate-only + reality finding + follow-on AD — NOT a real chat-v2 drive-through (the rare path is near-unreachable on the 主流量); (c) `--answerer-tier` reuses `profile.cheap` as the weaker answerer (no new Azure deployment); (d) lever default stays OFF — evidence-only sprint.

---

## 0. Background

### The gap (③1 + ③4, Sprint 57.144 carryovers)

Sprint 57.144 shipped structured-error reflection (research #7 Half B): on a tool failure, feed the LLM a TYPED diagnosis (`parameter` / `wrong_tool` / `failed_api` / `invocation` / `unknown`) + actionable guidance instead of an opaque `Error: <repr>`. Two things were left un-verified at closeout:

- **③1**: the reflection has TWO consumers — the dominant `executor._build_failure` (handler-exception / schema / unknown-tool) AND the rare `loop.py` path where the **executor itself raises**. Only the dominant path was drive-through-exercised; the rare path is code-covered by unit tests but was never driven through a real chat-v2 + real LLM.
- **③4**: the A/B harness measured the reflection's recovery lift on the STRONG action-tier model = `fix_delta +0.00%` (both arms 87.5%) → lever kept OFF. §2.4 hedged that a strong model has no headroom; a weaker model might. The harness hardcodes the answerer model so this was never tested.

### Why it matters (the missing capability)

Per the Drive-Through Acceptance hard constraint, "gate-green + unit-tested" ≠ "verified working on the 主流量". A reflection path that only fires when the executor itself raises is exactly the kind of rare branch that rots silently — ③1 closes that by proving it live. ③4 turns a one-model verdict into a model-tier-aware one: if a weaker model DOES recover better with reflection, the lever's default (or a per-tier / per-tenant policy) is worth revisiting on evidence rather than assumption.

### Root cause (recon code read, file:line; ALL re-verified §checklist 0.1)

| Layer | Reality (on `main` HEAD `f4828495`) | Anchor |
|-------|-------------------------------------|--------|
| Taxonomy module (pure) | `classify_tool_error` + `render_reflection` + `ErrorTaxonomy` 5-enum + `tool_error_reflection_enabled()` (per-call env read, default OFF) | `_error_taxonomy.py:65-72,104,168,53` |
| Env lever | `CHAT_TOOL_ERROR_REFLECTION`, default OFF, truthy set | `_error_taxonomy.py:49-50` |
| Dominant consumer | `executor._build_failure` — content=typed diagnosis when ON, `""` when OFF (byte-identical) | `executor.py:385-423` |
| **Rare consumer (③1 target)** | loop.py `except Exception as exc:` (executor SELF raised) → Cat8 `_handle_tool_error` → not-terminate → retry consultation → not-retry → synth `ToolResult` with `render_reflection` when ON | `loop.py:3009,3068-3088` |
| Trigger boundary | try wraps `self._tool_executor.execute()` (`loop.py:2991`); handler exceptions are caught INSIDE the executor → dominant path. Only an executor-level raise reaches `:3009`. | `loop.py:2954,2990-2993,3009` |
| `ToolResult` field | `error_taxonomy: str \| None = None` (set only when lever ON) | `_contracts/tools.py:155` |
| **Benchmark (③4 target)** | `_amain` hardcodes `build_azure_model_profile()`; `answerer=profile.action`, `judge=profile.cheap`; `run_arm(arm, cases, answerer, judge)` already parameterized | `benchmark_tool_error_reflection.py:293-303,219-247` |
| Benchmark corpus knob | `--fixture` already exists (harder corpus = free); `--out` exists; NO `--answerer-tier` / model knob | `benchmark_tool_error_reflection.py:334-348` |
| Stale docstring (③1 fix) | `Related:` cites `loop.py:3023-3030` — real rare path is `3068-3086` (+45 line drift) | `_error_taxonomy.py:36` |

→ The fix is: (1) DRIVE the rare path live (no code change to the path itself); (2) add a `--answerer-tier` knob to the benchmark + run one weaker-model A/B; (3) correct the stale docstring cross-ref.

### The design (evidence slice: 1 benchmark knob + 1 docstring fix + 1 staged drive-through; NO rare-path logic change)

```
# ③4 — benchmark_tool_error_reflection.py
main():   + parser.add_argument("--answerer-tier", choices=("action","cheap"), default="action")
_amain(fixture, out_dir, answerer_tier="action"):
    answerer = profile.action if answerer_tier == "action" else profile.cheap
    # judge stays profile.cheap (the production judge tier)
    report_to_markdown(... include the answerer_tier in the stamp/header ...)
# default "action" => byte-identical to 57.144 run.

# ③1 — drive-through ONLY (no loop.py edit). Day-1 stages an executor-self-raise:
#   register/point a real tool whose execute() raises at the executor level (NOT a
#   handler soft-failure), lever CHAT_TOOL_ERROR_REFLECTION=1, observe in real chat-v2:
#   executor raises -> loop.py:3068 synth ToolResult(content=render_reflection(...),
#   error_taxonomy=...) -> LLM sees typed diagnosis -> agent corrects next turn.

# ③1-fix — _error_taxonomy.py:36 docstring "loop.py:3023-3030" -> "loop.py:3068-3086"
```

Why drive-through over "the unit tests already cover the rare path": unit tests prove `classify/render` are wired at `:3068`; they do NOT prove an executor CAN raise on the 主流量, that the synth `ToolResult` reaches the LLM as an observation, and that the LLM acts on it — the exact Potemkin gap the Drive-Through constraint exists to catch.

### Ground truth (recon head-start — code read on `main` HEAD `f4828495`; ALL re-verified §checklist 0.1)

- `loop.py:2990-2993` — the ONLY thing inside the inner try is `self._tool_executor.execute(...)`; its raise (not a returned `ToolResult(success=False)`) is what reaches `:3009`.
- `loop.py:3024` — if `self._error_policy is None` the except RE-RAISES (53.1 opt-out); chat 主流量 wires Cat 8 so `_error_policy` is present → reaches the reflection branch.
- `benchmark_tool_error_reflection.py:302-303` — `run_arm` is called twice (plain/reflection), both with `answerer=profile.action`; changing only the `answerer` binding is sufficient for the weaker-model arm.
- `benchmark_tool_error_reflection.py:33` — CI-safe unit tests at `tests/unit/scripts/test_benchmark_tool_error_reflection.py` (fake ChatClients, no Azure) — the knob test extends these.

**Baselines (57.162 closeout)**: pytest 3223 · wire 26 · Vitest 930 · mockup 51 · mypy `src` 400 · run_all 11/11. Re-verify Day-0.

### STALE / drift findings (Day-0; full detail → progress.md — placeholder, filled in §checklist 0.1)

- **D-rare-path-line** — `_error_taxonomy.py:36` cites `loop.py:3023-3030`; real rare path `3068-3086` (already confirmed in recon; §checklist 0.1 re-confirms + this sprint fixes it).
- **D-executor-self-raise** — confirm WHAT real tool/condition makes `executor.execute()` raise at the executor level (vs handler soft-failure). Day-1 finalizes the drive-through trigger; shifts §8 R1.
- **D-benchmark-lazy-import** — `_amain` lazy-imports `build_azure_model_profile` (`:296`); confirm `profile.cheap` is a valid `ChatClient` usable as an answerer (not judge-only).

## 1. Sprint Goal

Verify the rare-path (executor-self-raise) tool-error reflection is correctly wired via an integration fault-inject test (inject a raising executor → the `loop.py:3068` branch produces a `render_reflection` typed-diagnosis observation + `error_taxonomy`), and equip the A/B harness with a `--answerer-tier` knob + run one weaker-model A/B to settle whether reflection has headroom below the strong tier. PROVEN by: full gate sweep + the fault-inject integration test (honestly gate-only — the rare path is near-unreachable on the 主流量) + a recorded weaker-model A/B verdict. Produces **CHANGE-130** (gap + the near-dead-rare-path reality finding + weaker-model A/B numbers) + a follow-on AD; NO new design note (57.144 note 48 follow-on).

## 2. User Stories

- **US-1** (③1 rare-path integration verify + reality finding): 作為平台維運者，我希望 rare-path（executor 自身 raise）的 tool-error reflection 以 integration fault-inject test 驗證其接線正確（inject 一個 raising executor → `loop.py:3068` 產生 `render_reflection` observation + `error_taxonomy`），並誠實記錄「該分支在主流量近乎不可觸發（executor 把一切轉 ToolResult）＝防禦性完整覆蓋而非熱路徑」，以便確認 wiring 正確且不假裝一個不可驅動的分支能被人使用。
- **US-2** (③4 weaker-model A/B): 作為引擎決策者，我希望 benchmark 能對弱模型（cheap tier）跑 reflection A/B，以便判斷 57.144「強模型 +0.00%」在弱模型上是否有 headroom（決定 lever default / per-tier 政策是否值得重議）。
- **US-3** (docstring 順修 + closeout): 順修 `_error_taxonomy.py:36` stale cross-ref (3023→3068) + CHANGE-130 + closeout（drive-through + A/B 結果記錄 + AD close + calibration + navigators）。

## 3. Technical Specifications

### 3.0 Architecture (backend + scripts only — NO migration / wire / codegen / frontend / loop.py-logic change)

```
EDIT   backend/scripts/benchmark_tool_error_reflection.py   — + --answerer-tier knob (③4)
EDIT   backend/src/agent_harness/tools/_error_taxonomy.py   — docstring cross-ref fix (③1-fix)
EDIT   backend/tests/unit/scripts/test_benchmark_tool_error_reflection.py — knob unit tests (③4)
NEW    backend/tests/integration/... a fault-inject integration test — a raising
         executor stub fed to the loop → assert the `loop.py:3068` rare branch
         produces content=render_reflection(...) + error_taxonomy set (lever ON) and
         a plain `Error: …` + error_taxonomy=None (lever OFF). Test-only, not shipped.
UNTOUCHED  loop.py:3068-3088 rare-path LOGIC (verify it, don't rewrite)
UNTOUCHED  executor.py / _contracts/tools.py / event_wire_schema.py / frontend / migrations
```

### 3.1 Weaker-model A/B knob (US-2) — `benchmark_tool_error_reflection.py`

- `main()`: add `parser.add_argument("--answerer-tier", choices=("action","cheap"), default="action")`; thread into `_amain`.
- `_amain(fixture, out_dir, answerer_tier="action")`: bind `answerer = profile.action if answerer_tier == "action" else profile.cheap`; pass to BOTH `run_arm` calls. `judge` stays `profile.cheap` (production judge tier, unchanged — the judge grades recovery, must stay constant across the A/B).
- `report_to_markdown` / json out: include `answerer_tier` in the header + json so the two runs (action baseline vs cheap) are self-labelling; write to a tier-suffixed filename OR the same `--out` (Day-1: avoid clobbering the action baseline — suffix by tier).
- Default `--answerer-tier action` ⇒ byte-identical to the 57.144 run (regression safety).
- Run once against real Azure with `--answerer-tier cheap` (`RUN_AZURE_INTEGRATION=1`) → record `fix_delta` + verdict in CHANGE-130.

### 3.2 Rare-path integration verify (US-1) — no code edit to the path; honestly gate-only

Day-0 D-executor-self-raise established the rare path (`loop.py:3009` → `:3068`) is near-unreachable on the 主流量: `executor.execute()` turns every failure into a `ToolResult` (handler exc → `:230` → `_build_failure`; unknown/schema/no-handler → `_fail`; rate-limit → terminal `ToolResult` `:278`) rather than raising. It only fires on an executor-INFRASTRUCTURE raise (the loop's own TOOL_EXEC tracer span `loop.py:2976`, or a gate backend raising non-fail-open). A real chat-v2 drive-through cannot honestly stage a near-dead branch, so:

- **Integration fault-inject test**: feed the loop a stub `ToolExecutor` whose `execute()` RAISES (a plain `RuntimeError`), drive one turn, and assert the `loop.py:3068` branch: lever ON → the synth `ToolResult.content == render_reflection(classify_tool_error(...))` (typed diagnosis, not `Error: <repr>`) + `error_taxonomy` set; lever OFF → `content == "Error: <repr>. Please adjust your approach."` + `error_taxonomy is None` (byte-identical baseline). This proves the wiring at `:3068` with both lever states.
- **Honest labelling**: the sprint records this as **gate-only verified** + a reality finding ("rare path near-unreachable on the 主流量 = defensive full-coverage, wiring correct, trigger near-dead") — NOT a drive-through, NOT a Potemkin (the code is correctly wired; only its trigger is near-dead).
- **Follow-on AD** `AD-Tool-Reflection-RarePath-Near-Dead-Evaluate` — is the rare-path branch worth keeping, or should the executor expose a real self-raise path (e.g. surface infra faults as reflected observations)? Logged to `next-phase-candidates.md`, not decided here.

### 3.3 Docstring cross-ref fix (US-3) — `_error_taxonomy.py:36`

- `loop.py:3023-3030 (rare path)` → `loop.py:3068-3086 (rare path)`. Trivial; MHist entry (Behavioral? No — doc-only; a 1-line MHist note is optional per file-header convention "Trivial" tier, but since it rides a real sprint, add one newest-first line).

### 3.x What is explicitly NOT done

- **Lever default flip** — this sprint GATHERS the weaker-model evidence; flipping `CHAT_TOOL_ERROR_REFLECTION` default (or a per-tier / per-tenant policy) is a SEPARATE decision on the recorded numbers.
- **③2 `AD-Tool-Description-AutoFix`** (AST write-back) + **③3 `AD-Tool-Error-Taxonomy-UI`** (wire→codegen→FE surface) — separate Tool-range slices.
- **Rare-path logic rewrite** — the `:3068` branch is byte-unchanged; if the drive-through surfaces a real bug there, that becomes a FIX with its own record.
- **New Azure deployment** — the weaker arm reuses the existing `profile.cheap`.

### 3.y Validation (US-1..US-3)

Gates: mypy `src` 400 · run_all 11/11 · pytest 3223 + new knob tests · Vitest 930 (unchanged — no FE) · mockup 51 (`diff` empty — no FE) · `npm run lint && npm run build` (NO `--silent`; unchanged — no FE) · black/isort/flake8 clean · LLM-SDK-leak clean (benchmark stays on the ChatClient ABC; concrete Azure profile only in `main`/`_amain` lazy import). Plus the §3.2 rare-path drive-through (MANDATORY) + the §3.1 weaker-model A/B run.

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 1 | `backend/scripts/benchmark_tool_error_reflection.py` | EDIT (`--answerer-tier` knob + report labelling) |
| 2 | `backend/tests/unit/scripts/test_benchmark_tool_error_reflection.py` | EDIT (knob unit tests: tier binds answerer; default byte-identical; report label) |
| 3 | `backend/src/agent_harness/tools/_error_taxonomy.py` | EDIT (docstring cross-ref fix + 1 MHist line) |
| 4 | `backend/tests/integration/tools/test_rarepath_reflection.py` (or nearest existing loop integration test dir) | NEW (fault-inject: raising executor stub → assert `loop.py:3068` reflection branch, lever ON/OFF) |
| — | `backend/src/agent_harness/orchestrator_loop/loop.py` | **UNTOUCHED** (rare-path logic driven, not rewritten) |
| — | `backend/src/agent_harness/tools/executor.py` · `_contracts/tools.py` | **UNTOUCHED** |
| — | `event_wire_schema.py` · codegen · `frontend/**` · migrations | **UNTOUCHED** |

## 5. Acceptance Criteria

1. `benchmark_tool_error_reflection.py --answerer-tier {action,cheap}` binds the answerer accordingly; `--answerer-tier action` (default) is byte-identical to the 57.144 behavior (regression-tested); judge stays `profile.cheap`.
2. One weaker-model (`cheap`) A/B run completes against real Azure; its `fix_rate` / `fix_delta` / `token_delta` + verdict recorded in CHANGE-130 (headroom or none).
3. `_error_taxonomy.py:36` cross-ref corrected to `loop.py:3068-3086`.
4. **Rare-path integration fault-inject test PASS** — a raising executor stub drives the `loop.py:3068` branch: lever ON → `content == render_reflection(...)` + `error_taxonomy` set; lever OFF → plain `Error: <repr>` + `error_taxonomy is None`. Honestly recorded as **gate-only** (rare path near-unreachable on the 主流量; no real UI drive-through is claimed) + the reality finding in progress.md + CHANGE-130.
5. ③1 + ③4 CLOSED; **CHANGE-130**; calibration recorded (`tool-reflection-drivethrough-evidence-spike` 0.60, 1st data point); navigators (CLAUDE.md / MEMORY.md) + `next-phase-candidates.md` updated (Tool range: 2 of ~4 closed).

## 6. Deliverables

- [ ] US-1 rare-path reflection integration fault-inject test PASS (lever ON/OFF) + reality finding recorded (gate-only) + follow-on AD logged
- [ ] US-2 `--answerer-tier` knob + unit tests + one recorded weaker-model A/B run
- [ ] US-3 docstring cross-ref fix + CHANGE-130 + closeout (AD close + calibration + navigators)

## 7. Workload Calibration

- Scope class **NEW `tool-reflection-drivethrough-evidence-spike` 0.60** (anchored to 57.144 `tool-reflection-and-lint-spike` 0.60 + the `verification-*-spike` / `guardrail-restrict-spike` 0.60 evidence-first family — same shape: a bounded backend/harness change + a real-Azure A/B + a MANDATORY drive-through; the real-code core here — the knob + tests + drive-through staging — is smaller than 57.144's full spike, so watch for the 57.120 ceremony-not-code-accelerated pattern: if the drive-through staging + one A/B run dominate wall-clock and the code core lands < 2 hr, Day-4 re-points toward 0.85).
- **Agent-delegated: no** (parent-direct — the drive-through staging judgement + reading the A/B verdict need the parent in the loop; not a mechanical delegation). `agent_factor` 1.0 → 3-segment form.
- Bottom-up est ~5 hr (US-1 integration fault-inject test + reality finding ~1.5 hr · US-2 knob + tests + real-Azure A/B ~2 hr · US-3 docstring + CHANGE + closeout ~1.5 hr) → class-calibrated commit ~3 hr (mult 0.60). Day-0 re-scope dropped ~1 hr of UI drive-through staging (integration test replaces it). Day-4 retro Q2 verifies + confirms/repoints the new class.

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| **R1 — RESOLVED at Day-0**: executor-self-raise is near-unreachable on the 主流量 (executor turns every failure into a `ToolResult`) → a real drive-through cannot honestly stage the branch | Day-0 re-scope (user 方案 A): verify via an integration fault-inject test (raising executor stub → assert `loop.py:3068`, lever ON/OFF) + label gate-only + reality finding + follow-on AD. No UI staging needed; risk retired. |
| **R2 — Risk Class E: stale `--reload` backend masks the lever** (`CHAT_TOOL_ERROR_REFLECTION` is read per-call from env, but a stale/orphan worker started before the env was set won't have it) | Clean restart: kill stale uvicorn reloader + orphan spawn-workers (Win32_Process PID/PPID/StartTime sweep), confirm the fresh sole worker, set the env BEFORE start, verify with a one-off probe. |
| **R3 — weaker-model A/B needs real Azure** (`RUN_AZURE_INTEGRATION=1` + Azure key; `profile.cheap` must be answerer-capable) | Confirm Day-0 D-benchmark-lazy-import (`profile.cheap` is a full ChatClient). The run is on-demand, not CI; deterministic-ish at temp=0 (per 57.144). If `profile.cheap` == judge tier only in config, Day-1 falls back to a distinct weaker deployment via env. |
| **R4 — cross-platform mypy `unused-ignore`** (Risk Class B) | Dual ignore code `# type: ignore[X, unused-ignore]` if the knob threading needs one; unlikely (pure arg add). |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- **`AD-Tool-Reflection-RarePath-Near-Dead-Evaluate`** (produced by this sprint's Day-0 finding) — whether the near-unreachable rare-path branch is worth keeping, or the executor should expose a real self-raise → reflected-observation path. Logged to `next-phase-candidates.md` at closeout; the DECISION is out of this sprint.
- ③2 `AD-Tool-Description-AutoFix-Phase58` (AST write-back) — separate Tool-range tooling slice.
- ③3 `AD-Tool-Error-Taxonomy-UI-Phase58` (wire→codegen→FE surface) — Day-0 noted it can bundle with ⑥2+⑥5 verification wire-surface; separate slice.
- Flipping the `CHAT_TOOL_ERROR_REFLECTION` default / a per-tier / per-tenant reflection policy — a decision on THIS sprint's recorded weaker-model numbers, not this sprint.
- Harder-corpus re-run — the `--fixture` knob already supports it (free); out of this sprint's evidence scope unless the weaker-model run is inconclusive.
