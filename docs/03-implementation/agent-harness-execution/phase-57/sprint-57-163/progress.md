# Sprint 57.163 Progress — Tool-error reflection rare-path drive-through + weaker-model A/B

Plan: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-163-plan.md`
Checklist: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-163-checklist.md`

---

# Day 0 — 2026-07-09 — Plan-vs-Repo three-prong verify

## Prong 1 — path verify ✅
- EDIT targets exist: `backend/scripts/benchmark_tool_error_reflection.py` ✅, `backend/tests/unit/scripts/test_benchmark_tool_error_reflection.py` ✅, `backend/src/agent_harness/tools/_error_taxonomy.py` ✅.
- `CHANGE-130` slug FREE (highest existing = `CHANGE-129-dag-enforce-cyclereport-viz.md`). ✅

## Prong 2 — content verify (drift findings)

| ID | Finding | Verdict | Implication |
|----|---------|---------|-------------|
| **D-rare-path-line** | `_error_taxonomy.py:36` cites `loop.py:3023-3030`; real rare path is `loop.py:3068-3086` (+45 line drift) | CONFIRMED | US-3 fix (as planned) — trivial docstring correction |
| **D-executor-self-raise** 🔴 | `executor.execute()` (executor.py:160-249) is designed to turn EVERY failure into a `ToolResult`, NOT to raise: handler exc → `:230 except` → `_build_failure` (dominant path); unknown/schema/no-handler → `_fail` → `_build_failure`; rate-limit → terminal `ToolResult` at `:278` (NOT a raise, despite the "OUTSIDE dispatch try/except" comment `:195`). So `loop.py:3009 except Exception` (the rare path US-1 targets) only fires on an EXECUTOR-INFRASTRUCTURE raise (the loop's own TOOL_EXEC tracer span `loop.py:2976`, or a gate backend that itself raises non-fail-open) — practically near-unreachable on the 主流量. | 🔴 **GO/NO-GO** | The rare path is **defensive full-coverage, not a hot path**. US-1's premise ("prove it works when a human uses it") does not hold — a human essentially never reaches it. A "real drive-through" would require injecting an infrastructure fault (monkeypatch tracer/gate), which is artificial and proves "the defensive branch is correct IF triggered", not usability. → re-confirm scope with user. |
| **D-benchmark-lazy-import** | `profile.cheap` (profile.py:92) IS a full `AzureOpenAIAdapter` (a `ChatClient`) → usable as an answerer ✅. BUT fallback: when `AZURE_OPENAI_CHEAP_DEPLOYMENT_NAME` is unset, `cheap IS action` (same instance, profile.py:84-85) → a `--answerer-tier cheap` A/B would DEGENERATE to strong-vs-strong. | CONFIRMED (+caveat) | US-2 knob is sound; the weaker-model A/B is only meaningful when a genuinely weaker `AZURE_OPENAI_CHEAP_DEPLOYMENT_NAME` is configured. Record this caveat in CHANGE-130 (R3 refinement). |

## Prong 3 — schema verify
- N/A (no DB / migration / ORM in scope). ✅

## Baselines
- Adopted from 57.162 closeout (pytest 3223 · wire 26 · Vitest 930 · mockup 51 · mypy `src` 400 · run_all 11/11); full re-measure deferred to pre-Day-1 (after the Go/No-Go scope is settled — no point re-running the whole suite before the scope is fixed).

## Go / No-Go — 🔴 US-1 premise challenged (re-confirm with user)

D-executor-self-raise shifts US-1's core (the drive-through method), not just a line. Per `sprint-workflow.md §Step 2.5` (findings shift scope 20-50% → revise §Acceptance + re-confirm with user). US-2 (③4) is unaffected and fully feasible. Options presented to user 2026-07-09 (AskUserQuestion) — see Day-0 decision below.

**Decision** (user AskUserQuestion 2026-07-09): **方案 A** — ③4 weaker-model A/B proceeds as planned (real Azure). ③1 is RE-SCOPED from a "real chat-v2 drive-through" to an **integration fault-inject test** (inject a raising executor → assert `loop.py:3068` produces a `render_reflection` observation + `error_taxonomy` set), **honestly labelled gate-only** (the rare path is near-unreachable on the 主流量 = defensive full-coverage, NOT a Potemkin — wiring is correct, only the trigger is near-dead), + a **follow-on AD** (`AD-Tool-Reflection-RarePath-Near-Dead-Evaluate` — is the rare path worth keeping / should it have a real trigger path?). This makes 57.163 a **pure-backend evidence slice** (no user-driven UI surface → Drive-Through constraint's pure-backend exemption applies: reports say "gate-only verified", never imply usability). Scope shift ~15-20%; calibration class `tool-reflection-drivethrough-evidence-spike` 0.60 unchanged (renamed intent: "evidence" not "drivethrough" — the drive-through was the un-doable part). Plan + checklist updated to match.

---

# Day 1-2 — 2026-07-09 — Code core (US-2 knob + US-3 docstring + US-1 integration)

## Accomplishments

- **US-3 docstring fix** (`_error_taxonomy.py:36`): `loop.py:3023-3030` → `3068-3086` + 1 MHist line. Trivial doc-only.
- **US-2 `--answerer-tier` knob** (`benchmark_tool_error_reflection.py`): new pure `select_answerer(profile, tier)` helper (action=strong default, cheap=weaker; judge always cheap) + `_amain(answerer_tier=)` + `report_to_markdown(answerer_tier=)` tier label + `main()` argparse `--answerer-tier {action,cheap}` default action + tier-suffixed cheap filename (action keeps the 57.144 filename → a cheap run doesn't clobber the action baseline). Default action = byte-identical A/B binding.
- **US-2 knob unit tests** (+4 CI-safe): `select_answerer` action/cheap binding; `report_to_markdown` carries the tier label; default tier = action. No Azure.
- **US-1 rare-path integration test** (`test_loop_error_handling.py`, +2): NEW `_RaisingExecutor(ToolExecutorImpl)` overrides `execute()` to raise (distinct from the existing `_make_failing_loop_components` real-executor + raising-handler = the dominant `_build_failure` path 57.144 already covers). `error_policy` set + no terminator → reaches `loop.py:3068`. **TDD-confirmed the wiring**: lever ON → the synth `ToolResult.content == render_reflection(...)` (`RuntimeError` → INVOCATION taxonomy → "tool invocation error") reaches the LLM tool message; lever OFF → baseline `"Error: ... Please adjust your approach"` + no taxonomy label. Proves the rare branch is correctly wired (gate-only — the branch is near-unreachable in production per Day-0 D-executor-self-raise; NOT a drive-through).

## Gate (Day 2.x)

- mypy `src` **Success, 400 files, 0 issues** (= baseline) · v2 lints **11/11 green** (incl. check_llm_sdk_leak + check_tool_descriptions) · black + isort + flake8 **clean** (1 black reflow on the new test line = 101→wrapped) · target-file pytest **25 pass** (17 benchmark unit incl. +4 knob · 8 integration incl. +2 rare-path).
- Full backend pytest: running (background) — expect baseline 3223 + 6 new = **3229**, 0 fail.

## Remaining

- Day 3: US-2 real-Azure weaker-model A/B run — **needs env** (`RUN_AZURE_INTEGRATION=1` + a genuinely weaker `AZURE_OPENAI_CHEAP_DEPLOYMENT_NAME`, else `cheap IS action` and the A/B degenerates — D-benchmark-lazy-import caveat). If env unavailable this session → honestly record "knob shipped + unit-tested; weaker-model A/B not run (no cheap deployment)" rather than fake it.
- Day 4: CHANGE-130 + closeout (AD ③1+③4 close, follow-on AD log, calibration, navigators).

---

# Day 3 — 2026-07-09 — Real-Azure weaker-model A/B (US-2) + US-1 gate-only record

## US-2 weaker-model A/B — PASS (real Azure, cheap tier, 8 cases)

Ran `python scripts/benchmark_tool_error_reflection.py --answerer-tier cheap` with the root `.env` `AZURE_OPENAI_*` exported (backend/.env doesn't exist — config lives in root/.env; `AZURE_OPENAI_CHEAP_DEPLOYMENT_NAME` set, so `cheap` is a genuinely weaker deployment, not `action`). Report → `backend/benchmark_reports/tool_error_reflection_report_cheap.md`.

| metric | plain | reflection | delta (refl−plain) |
|--------|-------|------------|--------------------|
| fix_rate | 75.00% | **87.50%** | **+12.50%** |
| mean_completion_tokens | 149.2 | 142.5 | −6.8 |

**verdict (cheap arm): FLIP lever default → ON** (+12.50% ≥ 5% materiality).

### KEY FINDING — reflection is tier-dependent

- **Strong tier (57.144, action):** fix_delta **+0.00%** → keep OFF (no headroom — the strong model recovers fine from a plain error).
- **Weak tier (this sprint, cheap):** fix_delta **+12.50%** (75.0% → 87.5%) AND −6.8 tokens → the weaker model recovers materially better from the typed diagnosis, at LOWER cost.
- This validates the 57.144 §2.4 hedge ("a strong model has no headroom; a weaker one might"). The 57.144 blanket "keep OFF" is refined to **tier-dependent**: reflection helps precisely where the model is weaker.
- **Honest caveat**: 8-case single-run → directional evidence, not a decision-grade basis for a GLOBAL default flip. The direction is clear + matches theory, but a larger corpus / multi-run (mirror 57.154's `--runs N`) is needed before flipping any default. This sprint GATHERS the evidence; the policy decision is out of scope.
- **New follow-on candidate**: `AD-Tool-Reflection-PerTier-Default` (default ON for weaker/cheap-tier answerers, OFF for strong — or a per-tenant/per-profile reflection policy on the C3 seam). Log to next-phase.

## US-1 gate-only reality record — confirmed

The rare-path integration fault-inject test (Day 2.1) is the honest verification: the `loop.py:3068` branch is correctly wired (lever ON → typed diagnosis; OFF → baseline), but near-unreachable on the 主流量 (Day-0 D-executor-self-raise). NO real UI drive-through is claimed — gate-only + reality finding, per 方案 A. Follow-on `AD-Tool-Reflection-RarePath-Near-Dead-Evaluate` logged.
