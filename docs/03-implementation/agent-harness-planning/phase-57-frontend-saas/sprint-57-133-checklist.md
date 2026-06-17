# Sprint 57.133 — Checklist (chat-v2 Inspector Turn tab token-sweep: cached + cache-hit rows)

[Plan](./sprint-57-133-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch

### 0.1 Three-prong Day-0 verify (against `main` HEAD `3e8ee330`)
- [x] **Prong 1 — path verify**: `types.ts` + `store/chatStore.ts` + `components/inspector/InspectorTurn.tsx` present; chat_v2 unit test dir present; `CHANGE-100` free
- [x] **Prong 2 — content verify** (drift → progress.md):
  - [x] **D-generated-cached** — `generated/loopEvents.generated.ts:43` `llm_response` carries `cached_input_tokens: number` ✅ (no codegen needed; FE-only confirmed)
  - [x] **D-store-0guard** — `chatStore.ts:598-599` has the `input_tokens > 0 ? … : t.tokensIn` 0-guard ✅
  - [x] **D-agentturn-literals** — 3 factories enumerated: ChatInspector `makeAgentTurn` (non-null 7410) / activeSkill `agentTurn` (null) / TurnList `agentTurn` (null) + mergeEvent `llmResponse` helper ✅
- [x] **Prong 3 — schema verify**: N/A (no DB / migration / ORM — FE-only)
- [x] **D-baselines** — Vitest 911 · mockup 51 · tsc 0; backend untouched (FE-only)
- [x] **Catalog drift** — progress.md Day-0 table (all GREEN, 0% scope shift)
- [x] **Go/no-go** — D-generated-cached GREEN → FE-only proceed

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-133-chatv2-inspector-token-sweep` (from `main` `3e8ee330`)

---

## Day 1 — Store capture + type field + render rows (US-1 + US-2)

### 1.1 Type field
- [x] **`types.ts` AgentTurn += `cachedInputTokens: number | null`** (token cluster, after `costUsd`; comment mirrors 57.131 `model`)
  - DoD: required `number | null`; comment states capture-at-`llm_response` + null-until-first + closes token-sweep leg ✅
  - Verify: `npx tsc --noEmit` EXIT 0

### 1.2 Store init + capture
- [x] **`chatStore.ts` `turn_start` init `cachedInputTokens: null`** ✅
- [x] **`chatStore.ts` `llm_response` capture** 0-guard `cached_input_tokens > 0 ? … : t.cachedInputTokens` ✅
  - DoD: real value lands; 0/absent keeps prior; no other case touched ✅

### 1.3 Render rows
- [x] **`InspectorTurn.tsx` +`tokens.cached` row + derived `cache_hit` row** after `tokens.thinking`, before `cost` ✅
  - DoD: reuse `KV` + `mono`; 0 new CSS/HEX/oklch; docstring 8→12 KV rows + MHist 1-line ✅
  - Verify: mockup-fidelity `diff` empty (styles-mockup.css untouched)

### 1.4 Factory ripple fix (57.131 lesson)
- [x] **3 AgentTurn factories + mergeEvent helper fixed** (ChatInspector non-null / activeSkill + TurnList null / llmResponse `cachedInputTokens?`)
  - DoD: `npx tsc --noEmit` EXIT 0 ✅

### 1.5 Tests
- [x] **store test** — cached_input_tokens > 0 → set; absent frame keeps prior ✅
- [x] **render test** — `tokens.cached` value + `cache_hit` % (7410/14820 → 50%); "—" when null ✅
  - Verify: `npx vitest run tests/unit/chat_v2` 203 passed

### 1.x Partial gate
- [x] `npm run lint && npm run build` clean (NO `--silent`) ✅

---

## Day 2 — Full gate

### 2.1 (rolled into Day 1 for an FE-only ~10-line sprint; Day 2 = full gate sweep)
- [x] (no separate Day-2 code task)

### 2.x Full gate
- [x] Vitest 146 files / **915 passed** (911 +4) · `npm run lint && npm run build` clean · mockup-fidelity PASS (51 baseline, byte-identical) · backend UNTOUCHED (FE-only, zero diff) ✅

---

## Day 3 — Drive-through (US-3) — real UI + real backend + real LLM

### 3.1 Clean restart (Risk Class E — FE-only variant)
- [x] backend :8000 PID 54504 already running (no backend diff → no restart); Vite :3007 HMR served edits; dev-login jamie@acme.com/acme-prod ✅

### 3.2 Drive-through (MANDATORY — NOT gate-only)
- [x] real chat-v2 UI + real Azure: turn 1 then turn 2 same session ✅
- [x] **THE feature**: turn 2 Inspector Turn tab `tokens.cached = 2,048` + `cache_hit = 83%` (real Azure prefix cache hit; derived 2048/2458 = 83% self-consistent); turn 1 = "—" (no cache hit, 0-guard honest) ✅
- [x] per-control AP-4 walk: rows render real store-derived values (turn-varying, not fixture/hardcoded) ✅
- [x] Screenshot (`artifacts/drivethrough-57133-inspector-token-sweep-PASS.jpeg`) + observed-vs-intended → progress.md Day 3 ✅

---

## Day 4 — CHANGE-100 + closeout

### 4.1 CHANGE-100
- [x] **`CHANGE-100-chatv2-inspector-token-sweep.md`** (gap + FE-only fix + drive-through PASS + AD CLOSED). NO design note ✅

### 4.2 Closeout
- [x] retrospective.md Q1-Q7 + calibration (`chatv2-inspector-existing-field-surface` 0.85, 3rd data point, ratio ~0.94-1.03 IN band → KEEP) ✅
- [x] Final gate sweep: Vitest 915 · lint · build · mockup 51 · (backend untouched) ✅
- [x] Navigators: CLAUDE.md Current-Sprint + Last-Updated · MEMORY.md pointer + subfile · next-phase-candidates (CLOSE `AD-ChatV2-Inspector-Turn-Metadata-Wire` all legs) · sprint-workflow matrix (3rd data point) ✅
- [x] Anti-pattern self-check (retro Q5): AP-2/3/4/6/8/11 → 0 violations ✅
- [ ] **Commit** → ⏳ PR push + open → CI → merge: PENDING USER CONFIRMATION (push is outward-facing per Developer Preferences) → post-merge status flip after gh-verified MERGED
