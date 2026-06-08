# Sprint 57.90 Retrospective — run() Re-entrancy Refactor Slice 2 (rewire resume + delete copy + multi-pause)

**Sprint**: 57.90 / **Branch**: `feature/sprint-57-90-resume-reentrancy-slice-2` / **Closed**: 2026-06-08
**Plan**: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-90-plan.md`
**Type**: CHANGE (Cat 1 behavior change) → CHANGE-057. **Closes `AD-Resume-Continuation-Fidelity` (Slice 1+2).**

---

## Q1 — Goal & outcome

Goal: point `resume()` at the shared `_run_turns` (extracted in 57.89), DELETE `_resume_continuation`, and get multi-pause-per-run + a drive-through. **Hit in full.** resume() drives `_run_turns` inside a LOOP span (after the pre-approved pending tool exec, no re-escalation); `_resume_continuation` deleted; multi-pause proven by `test_resume_continuation_can_pause_again` AND a real-UI/real-backend/real-Azure drive-through (echo `alpha`→pause→approve→echo `beta`→**2nd pause**→approve→end_turn). pytest 2232 (+1) / mypy 0/346 / run_all 10/10. `AD-Resume-Continuation-Fidelity` closed.

## Q2 — Estimate accuracy (calibration)

- Scope class: **`backend-core-loop-refactor` 0.55 (2nd data point, CAVEATED — different shape from Slice 1)**. Slice 1 was a pure extraction (zero-behavior-change gate); Slice 2 is a behavior-change slice (small rewire + a 148-line delete + a new multi-pause test + a real drive-through). The dominant cost was the drive-through (auth + chat-v2 + real-LLM two-echo + screenshot), not new code — the rewire itself was ~40 lines.
- `agent_factor`: **1.0 (parent-direct)** — 主流量 loop surgery + a behavior change + a drive-through is too high-blast-radius to delegate; done parent-direct. Does NOT extend the `AD-Calibration-AgentDelegated-WallClock-Measure` streak.
- Committed: bottom-up ~10 hr → ~5.5 hr (mult 0.55).
- **Ratio**: actual well under the ~5.5 hr commit — the rewire was tiny (the 57.89 extraction did the hard structural work), the existing tests absorbed the behavior change (contains-style), and the drive-through passed first try (no frontend fix needed). Likely ratio < 0.7 again. But: 2nd data point in this class + the two slices have very different shapes (pure-extraction vs behavior-change-with-drive-through) → record CAVEATED, KEEP 0.55, no generalization.
- Record to `calibration-log.md §3`.

## Q3 — What went well

- **The 57.89 extraction made Slice 2 almost trivial** — because `_run_turns` already existed (verbatim run() body), the rewire was "swap one call for a LOOP-span `_run_turns` drive" (~40 lines). All the structural risk was paid down in Slice 1. The two-slice split was the right call.
- **Multi-pause fell out for free, exactly as the analysis predicted** — `_run_turns` carries `_cat9_tool_check → _cat9_hitl_branch` (the deferred-pause checkpoint), so once resume drove `_run_turns`, a 2nd ESCALATE checkpointed + paused with NO extra code. The Day-0 analysis (the resume path shares `build_real_llm_handler`, so it's fully wired) held end-to-end.
- **The drive-through passed first try AND needed no frontend fix** — the chat-v2 UI surfaced the 2nd HITL approval (new approval_id + its own Approve) without any change; `useLoopEventStream`/`HITLTurn` already re-trigger on a repeated pause. The real gpt-5.2 obligingly called echo twice across the pause boundary.
- **The existing 8 pause-resume tests absorbed the behavior change** — contains-style assertions meant the additive spans/checkpoints didn't break them; I added ONE lock-in LOOP-span assertion + the new multi-pause test rather than force-rewriting passing tests (Karpathy §3).

## Q4 — What to improve / lessons

- **POSIX-Bash heredoc, not PowerShell `@'...'@`** — the Day-0 commit subject leaked a literal `@` because I used the PowerShell here-string on the POSIX Bash tool (the exact trap I'd been warned about). Caught immediately, amended. Lesson re-applied for the rest of the sprint: Bash tool = `-F - <<'EOF'`.
- **The drive-through Azure config wasn't in `backend/.env`** — `backend/.env` doesn't exist; the real Azure gpt-5.2 config is the repo-root `.env` (loaded by dev.py). A minute of confusion before checking the root. Worth remembering for future drive-throughs.
- **Risk Class E applied proactively** — restarted the backend cleanly before the drive-through so it ran the committed code (not a stale pre-change process), avoiding the "looks broken but it's process-state" trap.
- **Drive-through is the only thing that proves "the car drives"** — the unit test proved multi-pause mechanically, but the drive-through proved the WHOLE chain (real LLM → 2nd tool call → 2nd pause checkpoint persisted → 2nd `/resume` loads it → end_turn renders). The terse final answer (`beta`) is the LLM's wording choice, not a defect — recorded honestly.

## Q5 — Action items / carryover (→ `next-phase-candidates.md`)

- **Slice 3** (generalized pause points: input ESCALATE / mid-thinking / between-turns) — now enabled by the shared `_run_turns` + checkpoint-everywhere.
- **Subagent child-loop (Cat 11)** — consumes this refactor (no longer inherits the reduced-copy debt); distinct larger sprint.
- Remaining 57.88 carryover ADs unchanged: `AD-Resume-Checkpoint-Bloat` (resume_messages → messages table + TTL), `AD-Resume-Tenant-Capability-Policy`, `AD-Resume-Reject-Path`.
- (Deferred this sprint, noted in plan §9) Cat 8 retry on the resumed pre-approved pending-tool exec — minor; the tool is already approved and a failure surfaces to the continuation LLM.

## Q6 — Discipline self-check

- ☑ Plan → Checklist → Day-0 verify → Code → Update checklist → Progress → Retro (5-step honored)
- ☑ No future sprint plan pre-written (rolling); Slice 3 only listed as carryover
- ☑ No unchecked `[ ]` deleted; the deleted `_resume_continuation` is CODE (dead copy), not a checklist item
- ☑ LLM neutrality (no adapter/SDK touched; `check_llm_sdk_leak` 0); no multi-tenant surface change
- ☑ File headers + MHist updated (loop.py + test file); MHist 1-line E501-safe (~99 chars)
- ☑ **Drive-through DONE (user-facing change)** — real UI + real backend + real Azure; screenshot + observed-vs-intended table; NOT claimed gate-only
- ☑ Format chain run (black/isort/flake8) from the start (57.88 lesson)
- ☑ CHANGE-057 written; `19-pause-resume-design.md §5` closed; 17.md unchanged (resume() ABC sig unchanged)

## Q7 — Numbers

pytest **2232 passed / 4 skipped** (57.89 baseline 2231 → +1 multi-pause test) · mypy `src/ --strict` **0/346** · run_all **10/10** · black+isort+flake8 clean · loop.py net −164 lines (148-line copy deleted, ~40-line rewire added; test file +~70). Drive-through PASS (2 real pauses + end_turn, real gpt-5.2). 3 commits: `17103640` Day-0 → `bba611f2` rewire+delete+tests → closeout.
