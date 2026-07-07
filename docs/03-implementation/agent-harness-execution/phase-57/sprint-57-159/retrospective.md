# Sprint 57.159 Retrospective — compaction live drive-through + Inspector timeline marker

**Closed**: 2026-07-07
**Branch**: `feature/sprint-57-159-compaction-drivethrough-inspector` (from `main` `8eb3d261`)
**Raises**: Cat 4 Context compaction **L2 → L3** (reality-audit §3 gap); fills the deferred 57.66 "A-5c" for `context_compacted`

## Q1 — What shipped?

An FE-only observability surface + a mandatory live drive-through that took Cat 4 compaction from harness-verified (L2) to live-drive-through-verified (L3). The `context_compacted` event was fully wired (loop→sse→wire→store) but rendered NOWHERE (rawEvents-only, 57.66 A-5c deferral) → compaction's token reduction was invisible.

- `types.ts` `+CompactionMarkerTurn` in the `Turn` union; `chatStore.ts` `context_compacted` → push a marker into `turns`; `turns/CompactionMarker.tsx` (NEW, `.badge.warning` chip); `TurnList.tsx` dispatch; +2 Vitest.
- Drive-through PASS (real chat-v2 + Azure gpt-5.2): marker renders live (no-op `4,086→4,086` + real `4,604→1,770 · 8 msgs`); context retained after compaction (0.99 ×2).
- **L2→L3 finding**: compaction triggers but 0-reduces on the single-user-turn chat path (context grows 4k→35k); NOT a correctness bug (retention 0.99) → carryover AD.

## Q2 — Calibration (estimate accuracy)

- Class **NEW `chatv2-compaction-drivethrough-surface` 0.85**; **agent-delegated: no** (parent-direct, `agent_factor` 1.0, 3-segment). Anchored to `chatv2-inspector-existing-field-surface` 0.85 (57.120/131/133): surface an already-store-captured wire field in a NEW render location — tiny FE code + full ceremony + parent-direct + MANDATORY drive-through, ceremony-dominated not code-accelerated.
- Bottom-up ~5.5 hr → class-calibrated commit **~4.7 hr** (×0.85).
- Actual ~5 hr (FE ~1.5-2 hr: types+store+component+dispatch+2 tests; drive-through ~2 hr: dual-service setup + 2 drives + a backend restart to expose the reduction cutoff + finding analysis + 3 screenshots; closeout ~1 hr) → **ratio ~1.06 IN band**. The 0.85 held: the marker is a real-but-bounded FE change; the cost was ceremony + the long-conversation drive-through (heavier than a single-send surface) + the keep_recent restart, all offset by the FE-only ZERO-backend surface.
- **Verdict**: KEEP 0.85 as the 1st data point. Per plan §7: if a 2nd lands > 1.20 (long-conversation drive-through staging is the variance driver) re-point toward 1.0.

## Q3 — What went well?

- **The drive-through found a real behavior gap** (compaction 0-reduces on the chat path), exactly the L2→L3 payoff — same shape as the memory drive-throughs' bug finds. The marker made 8 previously-silent no-op compactions VISIBLE.
- **The event was already fully wired** (Day-0 confirmed) → ZERO backend/wire/codegen; a clean FE-only surface.
- **Reused proven patterns cleanly**: `message_injected` pseudo-turn (store), `.badge.warning` (compaction==warning matches the Trace span color), the 57.120/131/133 existing-field-surface class.
- **Honest scope reduction**: dropped the planned i18n (surrounding components use English literals) — match-surrounding-code, one fewer file.

## Q4 — What to improve?

- I initially set `CHAT_COMPACTION_TOKEN_BUDGET=3000` + `keep_recent=2` and saw 8 no-op compactions — I had to reason through the `user_indices > keep_recent` cutoff + restart with `keep_recent=1` to force a real reduction. **Lesson**: for a compaction drive-through, set `keep_recent` BELOW the expected user-turn count up front (the reduction is keyed on USER turns, and the chat path has ~1 user turn per send).
- The no-op finding is significant enough that a follow-on sprint (`AD-Compaction-NoOp-On-Single-User-Turn-Chat-Path`) should decide whether default deployments need loop-turn-based reduction or default-on ACON preclear — the current default compaction is effectively inert for long single-user-turn agentic runs.

## Q5 — Anti-pattern self-check

- **AP-2** (side-track): ✅ the marker is on the main chat-v2 render path (TurnList dispatch), driven live.
- **AP-4** (Potemkin): ✅ the OPPOSITE — this sprint EXISTS to de-Potemkin compaction (surface + drive-through). The marker renders real wire data (proven live); it is not a dead control or fixture.
- **AP-3** (scattering): ✅ the marker component sits beside its siblings in `turns/`; type in `types.ts` union; store case in `chatStore.ts`.
- **AP-6/8/10/11**: N/A / ✅ (no new abstraction; no LLM call in the FE; no version suffix).
- v2 lints: `run_all.py` → 11/11.

## Q6 — Carryover ADs (registered in next-phase-candidates.md)

- `AD-Compaction-NoOp-On-Single-User-Turn-Chat-Path` (NEW — compaction 0-reduces on the single-user-turn chat path; reduce within a long tool run via loop-turn masking / auto-tune keep_recent / default-on ACON preclear).
- `AD-Compaction-Marker-Inspector-Trace-Correlate` (NEW — link the timeline marker to its Trace-tab COMPACTION span for cross-view drill-down).
- Existing compaction follow-ons still open: `AD-Compaction-ToolAnchored-Preclear-Phase58`, `AD-Compaction-Preclear-PerTenant-Phase58`.

## Q7 — Verification summary

- Vitest 927 (+2) · lint LINT_EXIT=0 · build (tsc+vite) clean · mockup-fidelity 51 byte-identical · mypy `src` 400 / run_all 11/11 (backend UNTOUCHED).
- Drive-through PASS (real chat-v2 + Azure gpt-5.2): marker renders live (no-op + real `4,604→1,770 · 8 msgs`); context retained after compaction (0.99 ×2). Cat 4 L2→L3. Artifacts: `artifacts/sprint-57-159-leg{1,2,3}-*.png`.
