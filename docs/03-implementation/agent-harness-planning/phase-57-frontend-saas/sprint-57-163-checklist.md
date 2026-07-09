# Sprint 57.163 — Checklist (Tool-error reflection rare-path drive-through + weaker-model A/B)

[Plan](./sprint-57-163-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch

### 0.1 Three-prong Day-0 verify (against `main` HEAD `f4828495`)
- [x] **Prong 1 — path verify**: EDIT targets exist — `benchmark_tool_error_reflection.py`, `test_benchmark_tool_error_reflection.py`, `_error_taxonomy.py`; `CHANGE-130` slug free in `claudedocs/4-changes/feature-changes/`
- [x] **Prong 2 — content verify** (drift → progress.md):
  - [x] **D-rare-path-line** — re-confirm `_error_taxonomy.py:36` cites `loop.py:3023-3030` while the real rare path is `loop.py:3068-3086` (grep both)
  - [x] **D-executor-self-raise** — read `executor.py` `execute()` to enumerate what raises at the EXECUTOR level (vs handler soft-failure returning `ToolResult(success=False)`); pick the drive-through trigger candidate (§8 R1)
  - [x] **D-benchmark-lazy-import** — confirm `profile.cheap` (`benchmark:303`, `adapters/azure_openai/profile.py`) is a full `ChatClient` usable as an ANSWERER (not judge-only)
- [x] **Prong 3 — schema verify**: N/A (no DB / migration / ORM in scope)
- [x] **D-baselines** — pytest 3223 · wire 26 · Vitest 930 · mockup 51 · mypy `src` 400 · run_all 11/11 (re-measure; note any drift)
- [x] **Catalog drift** — progress.md Day-0 table (D-rare-path-line / D-executor-self-raise / D-benchmark-lazy-import + baseline deltas)
- [x] **Go/no-go** — RESOLVED 2026-07-09: D-executor-self-raise 🔴 confirmed the rare path near-unreachable on the 主流量 → user 方案 A: re-scope ③1 to an integration fault-inject test + gate-only + follow-on AD (scope shift ~15-20%; class 0.60 unchanged). Plan + checklist updated. Proceed.

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-163-tool-reflection-evidence` (from `main` `f4828495` + flip `2458b46e`) — DONE 2026-07-09

---

## Day 1 — Benchmark weaker-model knob + docstring fix (US-2, US-3)

### 1.1 `--answerer-tier` knob (US-2)
- [x] **Add `--answerer-tier {action,cheap}` (default `action`) to `benchmark_tool_error_reflection.py`**
  - Sub: `main()` argparse `--answerer-tier` choices `("action","cheap")` default `"action"`; thread into `asyncio.run(_amain(..., answerer_tier=args.answerer_tier))`
  - Sub: `_amain(fixture, out_dir, answerer_tier="action")` → `answerer = profile.action if answerer_tier == "action" else profile.cheap`; pass to BOTH `run_arm` calls; `judge` stays `profile.cheap`
  - Sub: `report_to_markdown` + json out include `answerer_tier` in the header/stamp; write to a tier-suffixed filename so a `cheap` run does not clobber the `action` baseline
  - DoD: `--answerer-tier action` path is byte-identical to pre-edit (answerer binding + report unchanged for default)
  - Verify: `python -c "import ast; ast.parse(open('backend/scripts/benchmark_tool_error_reflection.py').read())"` + `--help` shows the new arg

### 1.2 Docstring cross-ref fix (US-3)
- [x] **`_error_taxonomy.py:36` `loop.py:3023-3030` → `loop.py:3068-3086` + 1 MHist line**
  - DoD: `Related:` line cites the real rare-path range; newest-first MHist note added (≤ E501)
  - Verify: `grep -n "3068-3086" backend/src/agent_harness/tools/_error_taxonomy.py`

### 1.3 Knob unit tests (US-2)
- [x] **Extend `test_benchmark_tool_error_reflection.py` — tier binds answerer; default byte-identical; report labels tier**
  - Sub: spy/fake ChatClients for `profile.action` vs `profile.cheap`; assert `--answerer-tier cheap` drives `run_arm` with the cheap client as answerer, judge unchanged
  - Sub: assert default (`action`) preserves the 57.144 binding; assert report header carries the tier
  - DoD: ≥ 3 new CI-safe cases (no Azure); existing cases stay green
  - Verify: `cd backend && pytest tests/unit/scripts/test_benchmark_tool_error_reflection.py -q`

### 1.x Partial gate
- [x] `cd backend && black scripts/benchmark_tool_error_reflection.py src/agent_harness/tools/_error_taxonomy.py tests/unit/scripts/test_benchmark_tool_error_reflection.py && isort . && flake8 scripts src tests && mypy src`

---

## Day 2 — Rare-path integration fault-inject test (US-1) + full gate

### 2.1 Rare-path fault-inject integration test (US-1)
- [x] **NEW integration test: a raising executor stub drives the `loop.py:3068` branch**
  - Sub: locate the existing loop integration-test seam (a test that constructs `AgentLoopImpl` with an injected `ToolExecutor`); place the new test there (Day-0 confirms exact path)
  - Sub: stub `ToolExecutor.execute()` to `raise RuntimeError("boom")`; drive one turn with a tool call + Cat 8 `error_policy` present (so it reaches `:3068`, not the `_error_policy is None` re-raise)
  - Sub: assert lever ON (`monkeypatch.setenv("CHAT_TOOL_ERROR_REFLECTION","1")`) → the synth `ToolResult.content == render_reflection(classify_tool_error(...))` (typed diagnosis) + `error_taxonomy` set
  - Sub: assert lever OFF → `content == "Error: RuntimeError('boom'). Please adjust your approach."` + `error_taxonomy is None` (byte-identical baseline)
  - DoD: both lever states asserted; test is CI-safe (no Azure, no real chat-v2)
  - Verify: `cd backend && pytest <new test path> -q`

### 2.2 Reality finding record (US-1)
- [x] **Record the near-dead-rare-path finding in progress.md** (executor turns every failure into a `ToolResult`; the `:3068` branch fires only on executor-infra raise — gate-only, defensive full-coverage, NOT a Potemkin) + note the follow-on AD `AD-Tool-Reflection-RarePath-Near-Dead-Evaluate`

### 2.x Full gate
- [x] mypy `src` 400 · run_all 11/11 · backend pytest 3223 + new knob tests + new integration test · Vitest 930 (unchanged) · `npm run lint && npm run build` clean (unchanged — no FE) · mockup 51 (`diff` empty — no FE) · black/isort/flake8 clean · LLM-SDK-leak clean

---

## Day 3 — Real-Azure weaker-model A/B run (US-2) — gate-only (NO user-driven UI this sprint)
_(Pure-backend evidence slice — the only real-environment step is the ③4 A/B run; US-1's rare path is honestly gate-only per Day-0. Never imply usability of the rare path.)_

### 3.1 Weaker-model A/B run (US-2, real Azure)
- [x] **Confirm a genuinely weaker `AZURE_OPENAI_CHEAP_DEPLOYMENT_NAME` is set** (else `profile.cheap IS profile.action` → the A/B degenerates to strong-vs-strong; D-benchmark-lazy-import caveat). If unset → record "weaker-model A/B not run (no cheap deployment); knob shipped + unit-tested" honestly, do NOT fake it.
- [x] **Run `--answerer-tier cheap` against real Azure**: `RUN_AZURE_INTEGRATION=1 AZURE_OPENAI_*=... python scripts/benchmark_tool_error_reflection.py --answerer-tier cheap`
  - Sub: capture `fix_rate` (plain/reflection) · `fix_delta` · `token_delta` · verdict (headroom ≥ MATERIALITY 0.05 or none)
  - Sub: (optional, if within budget) re-run `--answerer-tier action` to confirm the knob didn't regress the 57.144 baseline
  - DoD: report md+json written (tier-suffixed, does not clobber the action baseline); numbers staged for CHANGE-130
  - Verify: report file exists + prints a `verdict` line

### 3.2 US-1 gate-only reality record
- [x] Confirm progress.md carries the US-1 gate-only reality finding (from Day 2.2) — the sprint claims NO real UI drive-through; the rare path is gate-only verified (integration test) + reality-finding-documented

---

## Day 4 — CHANGE-130 + closeout

### 4.1 CHANGE-130
- [x] **`CHANGE-130-tool-error-reflection-rarepath-verify-weaker-model-ab.md`** (gap ③1+③4 + fix: knob + docstring + rare-path integration fault-inject test PASS (gate-only) + near-dead-rare-path reality finding + weaker-model A/B numbers + verdict + follow-on AD; NO design note — 57.144 note 48 follow-on)

### 4.2 Closeout
- [x] retrospective.md Q1-Q7 + calibration (`tool-reflection-drivethrough-evidence-spike` 0.60, 1st data point; if drive-through staging + A/B dominated wall-clock and code core < 2 hr → flag re-point toward 0.85 per 57.120 ceremony insight)
- [x] Final gate sweep: mypy · run_all · pytest · Vitest · mockup · build · lint · LLM-SDK-leak
- [x] Navigators: CLAUDE.md Current-Sprint + Last-Updated · MEMORY.md pointer + subfile `project_phase57_163_tool_reflection_evidence.md` · `next-phase-candidates.md` (CLOSE ③1+③4 in the Tool range; leave ③2+③3 open; LOG follow-on `AD-Tool-Reflection-RarePath-Near-Dead-Evaluate`) · sprint-workflow matrix (NEW `tool-reflection-drivethrough-evidence-spike` 0.60 row)
- [x] Anti-pattern self-check (retro Q5): AP-2 (harness reachable) / AP-4 (drive-through kills Potemkin risk) / AP-8 / AP-10 (benchmark doubles are terminal only) → violations; v2 lints 11/11
- [ ] **Commit** → ⏳ PR push + open → CI → merge: PENDING USER CONFIRMATION (push is outward-facing per Developer Preferences) → post-merge status flip after gh-verified MERGED
