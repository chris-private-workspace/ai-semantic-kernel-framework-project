# Sprint 57.159 — Checklist (compaction live drive-through + Inspector timeline marker)

[Plan](./sprint-57-159-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch

### 0.1 Three-prong Day-0 verify (against `main` HEAD `8eb3d261`)
- [x] **Prong 1 — path verify**: EDIT targets exist (`chatStore.ts:839` / `types.ts:215` / `TurnList.tsx:76` / `common.json:24`); `turns/CompactionMarker.tsx` FREE (Glob 0); `CHANGE-126` free (highest 125); NO design note; backend (`loop.py:2288`/`sse.py:397`/`event_wire_schema.py`) already carries `context_compacted` → ZERO backend edit ✅
- [x] **Prong 2 — content verify** (all 5 confirmed vs real code → progress.md Day-0 table):
  - [x] **D-context-compacted-rawevents** — `chatStore.ts:839-846` `case "context_compacted": … rawEvents` only (grouped w/ prompt_built/state_checkpointed/tripwire; "DEFERRED A-5c") ✅
  - [x] **D-turn-union-shape** ⚠️ DRIFT — `Turn = UserTurn\|AgentTurn\|HITLTurn` in **`types.ts:215`** (NOT chatStore.ts) → add `CompactionMarkerTurn` there; +1 file to §Change List (<5% shift) ✅
  - [x] **D-marker-mockup-class** — `.thin-rule` (`:1166`) + `.badge`/`.badge.warning` (`:507,525`) reusable; compaction==warning matches `InspectorTrace.tsx:70` → NO new CSS ✅
  - [x] **D-compaction-trigger-live** — `CHAT_COMPACTION_TOKEN_BUDGET` env (`_category_factories.py:123-131,183`) + ≥3-turn gate; pin exact low value at Day-3 setup ✅
  - [x] **D-vitest-render-path** — `chatStore.mergeEvent.test.ts` (mergeEvent) + `components/*.test.tsx` (render) ✅
- [x] **Prong 3 — schema verify**: **N/A** (ZERO DB/wire/codegen — event already in `event_wire_schema.py` + generated; wire 26) ✅
- [x] **D-baselines** — Vitest 925 · mockup 51 · mypy `src` 400 · run_all 11/11 · wire 26 (backend unaffected, FE-only) ✅
- [x] **Catalog drift** — progress.md Day-0 table written (5 D-* + 1 DRIFT + implication) ✅
- [x] **Go/no-go** — 1 minor drift (types.ts location) → **PROCEED** ✅

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-159-compaction-drivethrough-inspector` (from `main` `8eb3d261`) ✅

---

## Day 1 — Store: CompactionMarkerTurn + context_compacted case (US-1)

### 1.1 Turn union + marker type
- [x] **`types.ts` (EDIT — drift: type here, not chatStore.ts)** — added `CompactionMarkerTurn { role:"compaction"; … }` + extended the `Turn` union (`:215`) ✅
  - DoD: tsc clean (build passed) ✅

### 1.2 context_compacted → push marker
- [x] **`chatStore.ts` (EDIT)** — split `case "context_compacted"` out; pushes a `CompactionMarkerTurn` into `s.turns` (mirror `message_injected` :558-577); rawEvents retained ✅
  - DoD: reducer returns `{...s, rawEvents, turns:[...s.turns, marker]}`; fields mapped from `ev.data.tokens_before/after/compaction_strategy/messages_compacted` ✅

### 1.x Partial gate
- [x] tsc / eslint clean on the store + types edit ✅

---

## Day 2 — Render marker + Vitest (US-1)

### 2.1 CompactionMarker component
- [x] **`turns/CompactionMarker.tsx` (NEW)** — slim centered marker `⚡ Context compacted · {before} → {after} tokens ({strategy} · {n} msgs)`; reuses `.badge.warning` (D-marker-mockup-class); NO new CSS/oklch/HEX ✅
  - DoD: renders locale-labelled (toLocaleString on token numbers) ✅

### 2.2 TurnList dispatch (i18n DROPPED — surrounding turn components use English literals, match-surrounding-code)
- [x] **`TurnList.tsx` (EDIT)** — `+import CompactionMarker` + `if (turn.role === "compaction") return <CompactionMarker key={turn.id} turn={turn} />;` ✅
- [x] **i18n common.json — DROPPED (scope reduction)** — `UserTurn`/`AgentTurn` use English literals not i18n → the marker matches; no `common.json` edit ✅

### 2.3 Vitest
- [x] **chat-v2 Vitest (NEW/EDIT)** — `mergeEvent.test.ts` (+1: context_compacted → marker in `turns` + rawEvents retained) + `components/CompactionMarker.test.tsx` (NEW: renders reduction/strategy/msgs) ✅
  - DoD: Vitest 927 (925 **+2**) passing ✅

### 2.x Full gate
- [x] Vitest **927** (+2) · mockup **51** (`diff` empty) · `npm run lint` (NO `--silent`, LINT_EXIT=0) + `npm run build` clean · mypy `src` 400 (no backend) · run_all 11/11 (unaffected) ✅

---

## Day 3 — Live compaction drive-through (US-2, MANDATORY) — L2→L3

### 3.1 Env + clean restart (Risk Class E)
- [x] `CHAT_COMPACTION_TOKEN_BUDGET=3000`; fresh single-process uvicorn (NO `--reload` → clean, no orphan); docker deps up; real Azure gpt-5.2 ✅
- [x] Confirmed real Azure (not echo/mock) — Verification 0.99 answers + real tool exec ✅

### 3.2 Drive-through legs (MANDATORY — NOT gate-only)
- [x] **Leg 1 (marker renders)** — 8 markers rendered live (`4,086→4,086` … `35,144→35,144`) as the agent ran a long tool-using send; `.badge.warning` in timeline (artifact leg1). **Real reduction** captured Drive 2 (`keep_recent=1`): `4,604 → 1,770 tokens (hybrid · 8 msgs)` −62% (artifact leg3) ✅
- [x] **Leg 2 (context retention)** — post-compaction recall PASSED both drives: Aurora/Oracle→Postgres/NUMBER(38,4) (0.99) + Beacon/October/Lodestar (0.99) ✅
- [x] Observed-vs-intended + honesty → progress.md Day 3. Context NOT lost (0.99) → no same-sprint contingency fix. 🔴 L2→L3 finding: compaction triggers but 0-reduces on single-user-turn chat path → carryover `AD-Compaction-NoOp-On-Single-User-Turn-Chat-Path` ✅

---

## Day 4 — CHANGE-126 + closeout

### 4.1 CHANGE-126
- [x] **`CHANGE-126-compaction-drivethrough-inspector.md`** (gap: Cat 4 L2 + rawEvents-only surface + drive-through verdict + no-op finding) ✅

### 4.2 Closeout
- [x] retrospective.md Q1-Q7 + calibration (`chatv2-compaction-drivethrough-surface` 0.85, 1st pt ~1.06 IN band); no design note (existing-field-surface + drive-through, not a spike) ✅
- [x] Final gate sweep: Vitest 927 (+2) · mockup 51 byte-identical · lint LINT_EXIT=0 · build clean · mypy `src` 400 · run_all 11/11 ✅
- [x] Navigators: CLAUDE.md Current-Sprint + Last-Updated · MEMORY.md pointer + subfile · next-phase-candidates (Cat 4 L2→L3 + 2 NEW carryover ADs) · sprint-workflow matrix (`chatv2-compaction-drivethrough-surface` 0.85 row) ✅
- [x] Anti-pattern self-check (retro Q5): AP-2/3/4 (marker is real render — the sprint DE-Potemkins compaction) → 0 violations; v2 lints 11/11 ✅
- [ ] **Commit** → ⏳ PR push + open → CI → merge: PENDING USER CONFIRMATION (push is outward-facing) → post-merge status flip after gh-verified MERGED
