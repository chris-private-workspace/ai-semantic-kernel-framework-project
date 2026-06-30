# Sprint 57.149 Retrospective — memory Option-B deterministic post-send fact extraction

**Sprint goal**: make the platform form durable user memory deterministically after every send — independent of whether the agent chose to call `memory_write` — by wiring the long-existing-but-unwired `MemoryExtractor` onto the chat path, proven by a 3-leg real-LLM drive-through. Close `AD-Memory-Formation-Auto-Extract`.

**Outcome**: ✅ achieved. Drive-through PASS (real chat-v2 + real Azure gpt-5.2): the extractor runs deterministically (cheap tier) after each send, writes `source="auto_extract"` user rows, those rows are recalled cross-session via the 57.148 always-on `profile()` inject, and a different user sees nothing. A Day-3 design evolution moved the extraction to a Starlette `BackgroundTask` (off the SSE generator).

---

## Q1 — What went well

- **The building block was already there**: `MemoryExtractor` existed since 51.2 (with tests) — this slice was wiring + a dedup param + a provenance tag, not new infra. The Day-0 三-prong confirmed every dependency (cheap tier in handler scope, `DBMessageStore.load()` returns the ledger, `MemoryUser.source` column pre-existed → no migration).
- **D-handler-return resolved cleanly**: returning a `(loop, ctx)` tuple would have broken ~12 callers; a self-contained `build_chat_memory_extractor` (rebuilds the cheap profile object, no API call) touched 0 of them — the surgical choice.
- **The drive-through was decisive AND caught a real architecture improvement**: the synchronous version PASSED all 3 legs, but driving it surfaced that the post-loop await blocks the SSE connection-close → moved to a Starlette BackgroundTask (NOT a fire-and-forget orphan — the plan's stated fear doesn't apply to Starlette's managed lifecycle). The re-drive confirmed the BackgroundTask extractor still writes correctly.
- **Investigated the noise instead of assuming**: the `async generator ignored GeneratorExit` + OTel `Failed to detach context` ERRORs looked like my extraction's fault; the traceback (`tracer.py:200 _span_cm`) + the fact they persisted on the BackgroundTask version proved them PRE-EXISTING (57.71/57.142 OTel-on-SSE-close). Avoided "fixing" something I didn't break.

## Q2 — Estimate accuracy (calibration)

- **Class**: NEW `memory-formation-extract-spike` **0.60 → re-pointed 0.85** (1st data point). **Agent-delegated: no** (parent-direct; `agent_factor` 1.0).
- **Plan**: bottom-up ~7-9 hr → class-calibrated commit ~4.5-5.5 hr (mult 0.60).
- **Actual**: ~7 hr (Day 0-3). Day 0-2 (6 src edits + 14 tests + gate) ran on-budget (~4 hr — every piece had a precedent). **Day 3 ran heavy** (~3 hr): the 3-leg drive-through + the BackgroundTask re-architecture (NOT in the plan — a Day-3 evolution) + the noise investigation + a full clean-restart re-drive.
- **Ratio ≈ 1.3-1.4** (OVER band). Per the 57.148 retro's note ("if a 2nd `memory-formation-*-spike` lands > 1.20, re-point toward 0.85") → **re-point 0.60 → 0.85**. The variance driver is the **drive-through discovery loop** (BackgroundTask re-arch + noise investigation + re-drive), the same ceremony-not-code-accelerated pattern as the 57.120/122/123/126/129/132 0.85 re-points — except here it's a genuine architecture change found by the drive-through, not just fixed-cost ceremony. The real-code core (~4 hr) held its share; the over-run is all in Day 3. If a 2nd `memory-formation-extract-spike` lands < 0.7 at 0.85, lower again.

## Q3 — What to improve

- **Don't pre-commit to "synchronous over background" in the plan when the real choice is Starlette BackgroundTask vs `asyncio.create_task`**: the plan conflated the two and chose synchronous to avoid an orphan. The drive-through corrected it. Lesson: a "background work after a streaming response" need should default to evaluating Starlette `BackgroundTask` (managed lifecycle, no orphan) FIRST.
- **The drive-through couldn't cleanly show "agent didn't write but extractor did"**: the 57.148 nudge (default ON) made the agent ALSO `memory_write` the same fact, so both rows appeared. The `source="auto_extract"` tag still proved the extractor ran independently, but a cleaner demo would temporarily disable the nudge. (Acceptable — the extractor's deterministic behavior is the invariant, proven by the tagged row; "agent didn't write" is its value scenario, not its mechanism.)

## Q4 — Lessons / ADs

- **Lesson (reusable)**: when a noise log appears right after a change, check the traceback's file:line + try the change-removed path before assuming causation. Here the OTel/GeneratorExit noise was pre-existing; the BackgroundTask move (made for a different, real reason) left it unchanged — confirming non-causation.
- **Lesson (Starlette)**: `BackgroundTask` ≠ fire-and-forget. It runs in the response's managed lifecycle after the body, so it's the right home for post-response work that shouldn't block the connection-close — without the orphan risk that `asyncio.create_task` carries.
- Carryover ADs: `AD-Memory-User-Upsert-By-Key` · `AD-Memory-Formation-Session-Recall` (缺口 2) · **`AD-Verification-Judge-Memory-Inject-Blind`** (NEW — the in-loop judge false-positive-REJECTs memory-injected recalls because it sees only the trace) · CARRY-026 / CARRY-027.

## Q5 — Anti-pattern self-check

- **AP-2** (side-track): ✅ reachable from chat main flow — drive-through ran the extractor on the real path.
- **AP-4** (Potemkin): ✅ NOT — the `[auto_extract]` DB rows + the cross-session recall + the priya isolation are the falsifications a fake would fail.
- **AP-6** (speculative abstraction): ✅ no new abstraction — reuses `MemoryExtractor`/`UserLayer`/`profile()`/`DBMessageStore`; the auto-extract toggle is settings-only (no per-tenant override built speculatively).
- **AP-8** (centralized PromptBuilder): ✅ N/A — the extraction prompt is the extractor's own; the dedup facts come from the centralized `profile()`.
- **AP-11** (naming): ✅ `build_chat_memory_extractor` / `ChatMemoryExtractContext` / `_maybe_auto_extract` / `source="auto_extract"` match behavior.
- **v2 lints**: 25 green (incl. `llm_sdk_leak` — extraction stays on the ChatClient ABC).

## Q6 — Carryover

`AD-Memory-User-Upsert-By-Key` · `AD-Memory-Formation-Session-Recall` (缺口 2) · `AD-Verification-Judge-Memory-Inject-Blind` (NEW) · CARRY-026 (semantic axis) · CARRY-027 (async queue) · per-tenant auto-extract override. Recorded in `next-phase-candidates.md`.

## Q7 — Drive-through evidence

- Leg 1 (formation): dan@acme.com (`cf2b40a1…`, baseline 3 `source=none`) → `[auto_extract]` conf 0.99 'Chris is currently handling Project Aurora, a database migration from Oracle to PostgreSQL' (trace `5b04311d…`).
- Leg 2 (recall, trace `567722ab…` / reads `9ff1b25f…`): NEW session → "你叫 Chris…Project Aurora…Oracle…PostgreSQL…Q3"; Inspector `profile()` read of the extractor row `memory_user:5d487f86`.
- Leg 3 (isolation): priya@acme.com (`dc921d38…`) → "我不知道你是誰" (judge 0.99; 0 leak).
- Re-drive (BackgroundTask, priya, baseline 0): `[auto_extract]` conf 0.78 SOC 2 row written after the response.
- Screenshots `sprint-57-149/artifacts/sprint-57-149-{s1-formation,s1b-memory-tab,s2-recall,s3-isolation-priya}.png` + `s2-recall-snapshot.md` / `s3-isolation-snapshot.md`. Full narrative: progress.md Day 3.

---

## Design Note Extract (spike sprint — §5.5)

**File**: `docs/03-implementation/agent-harness-planning/53-memory-auto-extract-design.md`
**Verified ratio (estimated)**: ~95% (every §3 invariant has file:line + a pytest verification or the real-Azure drive-through; §5 deferred items explicitly marked NOT verified)
**8-Point Quality Gate**:
- [x] 1. Section headers map to spike US (US-1..US-5 in §1)
- [x] 2. Each technical claim has file:line (§3 invariants 1-9)
- [x] 3. Decision rationale has comparison matrices (§2: trigger timing / where-it-runs / dedup)
- [x] 4. Verification commands reproducible (§3: pytest per invariant + the drive-through reproduce)
- [x] 5. Test fixture reference (§3: the 14 new/edited tests by name + the real 3-leg drive-through)
- [x] 6. Open invariants explicitly bounded (§5 verified-vs-deferred table + boundary statement)
- [x] 7. Rollback path (§6: env-off / user_id=None byte-identical + full revert < 1 hr, no migration/sentinel)
- [x] 8. 17.md cross-ref (§4: no new contract — reuses MemoryExtractor / UserLayer / profile() / DBMessageStore / BackgroundTask)

**Reviewer pass**: self-review (solo-dev).
