# Sprint 57.91 Retrospective — Generalized Pause Primitive + Input-ESCALATE Pause Point (地基 A Slice 3 leg 1)

**Sprint**: 57.91 / **Branch**: `feature/sprint-57-91-generalized-pause-input-escalate` / **Closed**: 2026-06-08
**Plan**: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-91-plan.md`
**Type**: CHANGE (Cat 1 + Cat 9 feature add) → CHANGE-058.

---

## Q1 — Goal & outcome

Goal: extract a generalized pause primitive (the durable-pause tail decoupled from a tool call) and build the FIRST new pause point on it — input-guardrail ESCALATE. **Hit in full.** `_emit_deferred_pause(...)` shipped; the tool deferred branch routes through it byte-identically; `_cat9_input_check` ESCALATE → `_cat9_input_hitl_pause` → input-kind pause (no tool_call); `resume()` branches on `pending_approval["kind"]` (input-kind drives `_run_turns` with no tool exec); a real `KeywordEscalationGuardrail` wired into the chat handler. Proven by 4 unit tests + a real-UI drive-through (`approval required: …` → pause `awaiting_approval` no LLM call → approve → "Paris"). pytest 2243 (+11) / mypy 0/347 / run_all 10/10. Scope locked via AskUserQuestion (primitive + input-ESCALATE; between-turns / mid-thinking deferred to legs 2/3).

## Q2 — Estimate accuracy (calibration)

- Scope class: **`backend-core-loop-refactor` 0.55 (3rd data point, CAVEATED — FEATURE-ADD shape, different again from Slice 1 pure-extraction + Slice 2 behavior-change-rewire)**. This sprint ADDED a pause point + a generalized primitive + a new guardrail + handler wiring — a feature, not a refactor.
- `agent_factor`: **1.0 (parent-direct)** — 主流量 loop surgery (input check + resume restructure) + a behavior-visible feature + a drive-through is too high-blast-radius to delegate. Does NOT extend the `AD-Calibration-AgentDelegated-WallClock-Measure` streak (parent-direct, same as 57.88/89/90).
- Committed: bottom-up ~10 hr → ~5.5 hr (mult 0.55).
- **Ratio**: actual well under the ~5.5 hr commit again — the 57.89/90 keystone made adding a new pause point cheap (`_run_turns` + the deferred machinery already existed; the work was a small primitive extract + an input branch mirroring the tool branch + a kind-branch in resume). The dominant non-code cost was the drive-through, inflated by the Risk Class E stale-process detour (~15 min). Likely ratio < 0.7 a THIRD time in this class.
- **3 consecutive < 0.7 in `backend-core-loop-refactor`** (57.89 extract / 57.90 rewire / 57.91 feature-add) — but all 3 have DIFFERENT shapes (pure-extraction / behavior-rewire / feature-add) and all 3 benefited from the prior slice's groundwork. Per the matrix lower-trigger rule (3+ consecutive < 0.7 → consider lowering), but the shape heterogeneity argues against a single multiplier change. Recommendation: KEEP 0.55, flag for a possible `loop-pause-point-feature` class split if a 4th same-shape (feature-add-on-existing-loop) data point also lands < 0.7. Record CAVEATED in `calibration-log.md §3`.

## Q3 — What went well

- **The 57.89/90 keystone paid off again** — adding a brand-new pause point was cheap because `_run_turns` + the deferred-checkpoint/resume machinery already existed. The input branch just mirrors the tool branch; the only genuinely new design was the `kind` discriminator + the no-pending-tool resume path. The "primitive + first pause point" decomposition kept the slice thin.
- **The frontend needed ZERO change** — the Day-0 prediction held: the HITL card / Approve / resume are driven by events (`ApprovalRequested` + `awaiting_approval`), not a tool struct. An input pause renders the same card with `tool: —`. The drive-through confirmed it (I did NOT trust the Explore agent's claim — I drove it).
- **The generalized primitive avoided over-abstraction** — I factored ONLY the shared tail (`_emit_deferred_pause`); each kind builds its own `ApprovalRequest` (payloads genuinely differ). A parameterized request-builder generator would have been worse (Karpathy §2/§3).
- **Tool-path tests passed UNCHANGED** — the `"kind":"tool"` key is additive + `resume()` defaults missing kind to `"tool"`, so the 57.88-90 tool pause-resume tests didn't need a single edit (Never-Delete honored trivially).

## Q4 — What to improve / lessons

- **Risk Class E bit again — and the drive-through caught it.** The first drive-through attempt showed the input going straight to the LLM (no pause). The gate-green code was correct; a STALE pre-57.91 uvicorn listener (PID 19056) still owned `:8000` via SO_REUSEADDR and served my requests against old `handler.py` (no input guardrail). `dev.py restart` had reported success but only killed the listener it knew about (54916), not the older 19056. **Lesson re-applied**: before a drive-through, don't trust `dev.py restart`'s "started successfully" — verify the `:8000` OWNER is your fresh PID (`Get-NetTCPConnection -LocalPort 8000`), and kill ALL stale uvicorn python procs (listener + spawn-workers) until the port is FREE, then start ONE. I isolated the cause with a no-LLM repro (the guardrail returns ESCALATE in-process) BEFORE blaming the code — which is what kept me from "fixing" correct code.
- **Diagnose process-state vs code-bug with a cheap isolated repro.** A 5-line `check_input("approval required: …")` script proved the guardrail logic was fine, pointing squarely at wiring/process-state. That saved a wild goose chase through the loop.
- **The drive-through is the only thing that proves it.** Every gate was green (2243 / mypy 0 / run_all 10/10) AND the first UI attempt still showed no pause — because the gates test the code, not the running process. Only driving the real UI surfaced the stale-process reality.

## Q5 — Action items / carryover (→ `next-phase-candidates.md`)

- **Slice 3 leg 2 — between-turns pause** (a policy gate inside `_run_turns`: budget/turn-count/periodic check-in → pause). The `_emit_deferred_pause` primitive shipped here is its foundation; needs a trigger-policy design.
- **Slice 3 leg 3 — mid-thinking pause** (interrupt an in-flight streaming LLM call). Hardest; separate.
- **Output-guardrail ESCALATE pause** — the primitive supports it; a possible smaller future leg.
- **Subagent child-loop (Cat 11)** — consumes the lifecycle skeleton; distinct larger sprint.
- Remaining 57.88 carryover ADs unchanged: `AD-Resume-Checkpoint-Bloat` (the input pause adds another `resume_messages` writer), `AD-Resume-Tenant-Capability-Policy` (now also per-tenant input-escalation phrases), `AD-Resume-Reject-Path` (an input-kind reject leaves a dangling checkpoint the same way).

## Q6 — Discipline self-check

- ☑ Plan → Checklist → Day-0 verify (3-prong + 4 drift) → Code → Update checklist → Progress → Retro (5-step honored)
- ☑ Scope locked via AskUserQuestion before plan (new sprint direction + multiple valid scopings → ask, per CLAUDE.md "Ask Before Acting on STRATEGY")
- ☑ No future sprint plan pre-written (rolling); legs 2/3 only listed as carryover
- ☑ No unchecked `[ ]` deleted; tool-path tests UNCHANGED (no test deleted)
- ☑ LLM neutrality (`check_llm_sdk_leak` 0; no adapter/SDK touched); no multi-tenant surface change; no new contract (17.md note only)
- ☑ File headers + MHist updated (loop.py + handler.py + 2 new/edited test files + new guardrail); MHist 1-line E501-safe
- ☑ **Drive-through DONE (user-facing change)** — real UI + real backend + real Azure; 2 screenshots + observed-vs-intended table; NOT claimed gate-only (and the Risk Class E detour is recorded honestly)
- ☑ Format chain (black/isort/flake8) + run_all 10/10 from the start
- ☑ CHANGE-058 written; `19-pause-resume-design.md §5` updated; 17.md 1-line note

## Q7 — Numbers

pytest **2243 passed / 4 skipped** (baseline 2232 → +11: 4 input pause-resume unit + 7 `KeywordEscalationGuardrail` unit) · mypy `src --strict` **0** (347 files, +1 guardrail) · run_all **10/10** · black+isort+flake8 clean · loop.py: +`_emit_deferred_pause` + `_cat9_input_hitl_pause` + input-ESCALATE branch + resume kind-branch; new `escalation_keyword_detector.py` (~95 lines) + handler wiring. Drive-through PASS (real gpt-5.2: pause → approve → "Paris"; no frontend change). Commits: `faee9a27` Day-0 → `ecb64b57` code+tests → closeout.
