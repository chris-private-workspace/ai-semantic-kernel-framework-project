# Sprint 57.92 Retrospective — Between-Turns Guardrail ESCALATE Pause Point (地基 A Slice 3 leg 2)

**Sprint**: 57.92 / **Branch**: `feature/sprint-57-92-between-turns-pause` / **Closed**: 2026-06-08
**Plan**: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-92-plan.md`
**Type**: CHANGE (Cat 1 + Cat 9 feature add) → CHANGE-059.

---

## Q1 — Goal & outcome

Goal: build the SECOND generalized pause point on the leg-1 `_emit_deferred_pause` primitive — between-turns guardrail ESCALATE (a pause BETWEEN completed turns, before the next LLM call). **Hit in full.** A new `GuardrailType.BETWEEN_TURNS` + `check_between_turns`; a gate at the `_run_turns` loop top (`turn_count > 0 and not skip_between_turns_once`) runs `_cat9_between_turns_check` on the just-completed turn's output → ESCALATE pauses durably (between_turns-kind, no tool_call) via `_cat9_between_turns_hitl_pause` + `_emit_deferred_pause`; `resume()` drives the shared `_run_turns` with `skip_between_turns_once=True` so the boundary doesn't re-escalate; a real `BetweenTurnsKeywordGuardrail` + a non-escalate `note_tool` make it reachable on 主流量. Proven by 4 unit tests + a real-UI drive-through (`note the word checkpoint` → turn 0 `note_tool` → pause `awaiting_approval` `tool: —` → approve → `end_turn` "checkpoint"). pytest 2254 (+11) / mypy 0/350 / run_all 10/10. Scope locked via AskUserQuestion (trigger = between-turns guardrail ESCALATE; scope = leg 2 only; mid-thinking deferred to leg 3).

## Q2 — Estimate accuracy (calibration)

- Scope class: **`backend-core-loop-refactor` 0.55 (4th data point, CAVEATED — FEATURE-ADD shape, 2nd consecutive after 57.91 leg 1)**. This sprint added a pause point + a new GuardrailType + a new engine method + a new guardrail + a non-escalate demo tool + handler wiring — a feature, not a refactor.
- `agent_factor`: **1.0 (parent-direct)** — 主流量 loop surgery (a new loop-top gate + a resume kind-branch) on the most-tested file + a behavior-visible feature + a drive-through is too high-blast-radius to delegate. Does NOT extend the `AD-Calibration-AgentDelegated-WallClock-Measure` streak (parent-direct, same as 57.88/89/90/91).
- Committed: bottom-up ~9.75 hr → ~5.4 hr (mult 0.55).
- **Ratio**: actual well under the ~5.4 hr commit AGAIN — the leg-1 primitive + resume machinery made adding the between-turns point cheap: `_cat9_between_turns_check` / `_cat9_between_turns_hitl_pause` are near-verbatim mirrors of the leg-1 input methods, `_emit_deferred_pause` was reused unchanged, the resume branch mirrors the input branch + one flag. The genuinely new design was the loop-top seam choice (avoiding the mid-output-check re-generation trap) + the `skip_between_turns_once` flag + the non-escalate `note_tool` (to make the boundary reachable, since echo_tool tool-escalates). Drive-through ran first-try clean (the Risk Class E stale-process was caught + fixed BEFORE driving, not during). Likely ratio < 0.7 a FOURTH time in this class.
- **4 consecutive < 0.7 in `backend-core-loop-refactor`** (57.89 extract / 57.90 rewire / 57.91 feature-add / 57.92 feature-add) — but the 4 split into 3 shapes: pure-extraction (89) / behavior-rewire (90) / feature-add (91, 92). The last TWO are the SAME shape (feature-add-on-existing-pause-primitive) AND both landed < 0.7. **Recommendation: propose a `loop-pause-point-feature` class split (~0.40) in the next pause-point sprint's plan** — the leg-1 keystone makes each subsequent pause point a thin mirror, so 0.55 over-estimates this specific sub-shape. Record CAVEATED in `calibration-log.md §3`; the split is a proposal (2 same-shape data points; the matrix lower-trigger is met but a 3rd same-shape point would confirm the baseline).

## Q3 — What went well

- **The leg-1 keystone paid off (again).** `_emit_deferred_pause` was reused byte-for-byte; the between-turns check + hitl-pause methods are near-verbatim mirrors of the input ones; the resume branch mirrors the input branch. The "primitive + first pause point" decomposition (57.91) made leg 2 a thin mirror — most of the sprint was the genuinely-new parts (the loop-top seam + skip flag + note_tool).
- **The loop-top seam choice avoided a correctness trap.** The obvious seam (the existing per-response `_cat9_output_check`, which already had a dormant ESCALATE branch) would have paused mid-turn, and resume would re-call the LLM → re-generate the output the approver approved → fidelity break + re-escalation loop. Putting the gate at the loop TOP (before the next turn's LLM call, after the prior turn fully completed) means resume continues by making a call that never ran — clean, no re-generation. Caught this during Day-0 design analysis, not in code.
- **A new GuardrailType, not a reused OUTPUT type.** Reusing OUTPUT would have double-fired with the existing per-response output check. A distinct `BETWEEN_TURNS` chain is type-safe + zero double-fire; Day-0 Prong 2.5 confirmed no exhaustiveness consumer breaks on a 4th enum value.
- **The drive-through needed a real insight, not a hack.** `echo_tool` (the only deterministic demo tool) tool-escalates → a tool resume execs the pending tool OUTSIDE the loop → the re-entered turn 0 is the final answer → `turn_count` never reaches 1 → the between-turns gate is unreachable. Adding a non-escalate `note_tool` (so turn 0 runs end-to-end INSIDE the loop) was the correct fix, not a test-only shortcut. The drive-through confirmed it on the real LLM.
- **ZERO frontend change.** As predicted (and as leg 1 established), the HITL card renders generically from `ApprovalRequested` + `awaiting_approval` — a between-turns pause shows `tool: —` and the same Approve/Reject. I drove it (did not trust the prediction).
- **Tool-path + input-path tests passed UNCHANGED** — the `skip_between_turns_once` flag defaults False and the input/tool branches are byte-identical, so the 57.88-91 cases didn't need an edit.

## Q4 — What to improve / lessons

- **Risk Class E caught proactively this time.** `:8000` was owned by PID 50548 — the SAME stale 57.91 drive-through process (PRE-57.92 code). Unlike 57.91 (where the stale process surfaced DURING the drive-through as "no pause"), this time I checked the `:8000` owner BEFORE driving, recognized it as pre-57.92, and killed the full uvicorn tree (worker 16992 + reloader 50548) + verified no LISTEN owner before starting the fresh PID 53688. The lesson from 57.91 ("verify the `:8000` OWNER is your fresh PID; kill ALL stale uvicorn") was applied pre-emptively → the drive-through ran first-try.
- **Frontend port drift.** The frontend was on `:3007` (not the documented `:3005`) — `dev.py` found `:3005`/`:3007` and restarted an existing dev server on `:3007`. Minor; resolved by reading the dev.py output URL. Worth noting `dev.py start frontend` restarts an existing one (kills the old node) — acceptable here (the killed node was the old frontend, not Claude Code's node).
- **Calibration shape signal is now strong.** Two consecutive feature-add-on-pause-primitive sprints both landed < 0.7 at 0.55. The `loop-pause-point-feature` split should be proposed in the next pause-point plan (leg 3 / output-guardrail / subagent child-loop if it reuses the primitive).
- **Local flake8 must match the CI scope (`src/ tests/`), not just changed src files.** PR #265's first CI run failed on a single `E501` (a test-file docstring `Scope:` line at 101 chars) — because the local pre-commit lint ran `flake8 src/<changed files>` only, while CI runs `flake8 src/ tests/`. The src-file E501s were caught locally (and fixed) but the test-file one slipped. **Lesson: run the CI-equivalent `flake8 src/ tests/` (or `flake8 .`) before pushing, not a path-scoped subset** — the same way the `npm run lint` no-`--silent` rule exists for the frontend. Fixed in a follow-up commit; `flake8 src/ tests/` EXIT 0.

## Q5 — Action items / carryover (→ `next-phase-candidates.md`)

- **Slice 3 leg 3 — mid-thinking pause** (interrupt an in-flight streaming LLM call). Hardest; separate sprint. The primitive supports the durable tail; the new work is interrupting + checkpointing a streaming call.
- **Output-guardrail ESCALATE pause** — the per-response `_cat9_output_check` ESCALATE (currently "continue") → pause. Distinct from the between-turns gate (per-response vs loop-top); a smaller possible future leg; would need the re-generation-fidelity question answered (the per-response seam has the same mid-turn problem the between-turns gate sidestepped).
- **Subagent child-loop (Cat 11)** — consumes the lifecycle skeleton; a distinct larger sprint.
- **`loop-pause-point-feature` calibration class** — propose ~0.40 in the next pause-point plan (2 same-shape < 0.7 data points; 3rd confirms).
- Remaining 57.88 carryover ADs unchanged: `AD-Resume-Checkpoint-Bloat` (the between-turns pause adds another `resume_messages` writer), `AD-Resume-Tenant-Capability-Policy` (now also per-tenant between-turns phrases), `AD-Resume-Reject-Path` (a between-turns reject leaves a dangling checkpoint the same way).

## Q6 — Discipline self-check

- ☑ Plan → Checklist → Day-0 verify (3-prong + Prong 2.5 + 4 drift) → Code → Update checklist → Progress → Retro (5-step honored)
- ☑ Scope locked via AskUserQuestion before plan (new sprint direction + multiple valid trigger designs → asked, per CLAUDE.md "Ask Before Acting on STRATEGY")
- ☑ No future sprint plan pre-written (rolling); leg 3 + subagent only listed as carryover
- ☑ No unchecked `[ ]` deleted; input/tool-path tests UNCHANGED (no test deleted)
- ☑ LLM neutrality (`check_llm_sdk_leak` 0; no adapter/SDK touched); no multi-tenant surface change; one additive contract value (`GuardrailType.BETWEEN_TURNS`, 17.md noted)
- ☑ File headers + MHist updated (loop.py + engine.py + _abc.py + handler.py + note_tool.py + new guardrail + 2 test files); MHist 1-line E501-safe (the 2 first-draft E501s were on docstring Purpose/Related lines, fixed before commit)
- ☑ **Drive-through DONE (user-facing change)** — real chat-v2 UI + real backend + real Azure gpt-5.2; 2 screenshots + observed-vs-intended table; NOT claimed gate-only; Risk Class E detour recorded honestly
- ☑ Format chain (black/isort/flake8) + run_all 10/10
- ☑ CHANGE-059 written; `19-pause-resume-design.md §5` updated; 17.md `LoopCompleted` 3rd-origin note

## Q7 — Numbers

pytest **2254 passed / 4 skipped** (baseline 2243 → +11: 4 between-turns loop pause/resume/skip/block unit + 7 `BetweenTurnsKeywordGuardrail` unit) · mypy `src --strict` **0** (350 files, +2: new guardrail + note_tool) · run_all **10/10** · black+isort+flake8 clean · loop.py: +`_latest_output_text` + `_cat9_between_turns_check` + `_cat9_between_turns_hitl_pause` + loop-top gate + `_run_turns` skip flag + `resume()` between_turns branch; new `between_turns/keyword_detector.py` + `note_tool.py` + `_abc.py`/`engine.py`/`handler.py`/`_register_all.py` wiring. Drive-through PASS (real gpt-5.2: turn-0 note_tool → between-turns pause `tool: —` → approve → "checkpoint"; no frontend change). Commits: `d12e68ed` Day-0 → `fb23ed5e` code+tests → closeout.
