# Sprint 57.133 Progress — chat-v2 Inspector Turn tab token-sweep

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-133-plan.md) · [Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-133-checklist.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch — 2026-06-17

### Drift findings (against `main` HEAD `3e8ee330`)

| ID | Finding | Implication |
|----|---------|-------------|
| **D-generated-cached** | ✅ GREEN — `frontend/src/features/chat_v2/generated/loopEvents.generated.ts:43` carries `cached_input_tokens: number` on the `llm_response` interface (+`loop_end` cumulative `cache_hit_rate` :77-78) | Data already on the wire (Sprint 57.65/57.108) → **FE-only**, NO backend / wire / codegen. Confirms the plan's core scope assumption. |
| **D-store-0guard** | ✅ GREEN — `chatStore.ts:598-599` `llm_response` case has the `input_tokens > 0 ? … : t.tokensIn` 0-guard | Mirror anchor for the cached capture confirmed. |
| **D-agentturn-literals** | 3 AgentTurn factories need the new required field: `ChatInspector.test.tsx:40-69 makeAgentTurn` (non-null 7410 to keep dash counts stable), `chatStore.activeSkill.test.ts:25-39 agentTurn` (null), `TurnList.test.tsx:37-51 agentTurn` (null). Plus the `chatStore.mergeEvent.test.ts:49 llmResponse` helper needs a `cachedInputTokens?` opt. | The 57.131 required-field tsc-ripple lesson; all enumerated + fixed Day 1 (tsc clean confirms full set). |
| **D-baselines** | Vitest 911 · mockup 51 · `tsc --noEmit` 0 at base | Re-verified. Backend untouched (FE-only) → mypy/run_all/pytest not re-run (zero backend diff). |

**Go/no-go**: D-generated-cached GREEN → FE-only proceed (0% scope shift from plan).

**Branch**: `git checkout -b feature/sprint-57-133-chatv2-inspector-token-sweep` from `main` `3e8ee330`.

---

## Day 1 — Store capture + type + render rows + tests — 2026-06-17

**Accomplishments** (US-1 + US-2):
- `types.ts` — `AgentTurn += cachedInputTokens: number | null` (token cluster, after `costUsd`).
- `chatStore.ts` — `turn_start` init `cachedInputTokens: null`; `llm_response` capture `cachedInputTokens: ev.data.cached_input_tokens > 0 ? … : t.cachedInputTokens` (same 0-guard as 57.108 tokensIn/Out).
- `InspectorTurn.tsx` — derived `cacheHitLabel` (`Math.round(cached / tokensIn * 100)%`, "—" until both known) + 2 KV rows (`tokens.cached` + `cache_hit`) after `tokens.thinking`, before `cost`; docstring KV count corrected (stale 8 → 12; 57.120/57.131 had drifted it) + MHist 1-line.
- Tests: ChatInspector `makeAgentTurn += cachedInputTokens: 7410` + 2 dedicated render tests (set → "7,410"/"50%"; null → "—") + null-placeholder override; chatStore.activeSkill + TurnList factories += `cachedInputTokens: null`; chatStore.mergeEvent `llmResponse` helper += `cachedInputTokens?` + 2 capture tests (set lands / absent keeps prior) + turn_start-init null assertion.
- **+4 Vitest tests** total (2 render + 2 store).

**Verify**: `npx tsc --noEmit` EXIT 0 (no required-field ripple) · `npx vitest run tests/unit/chat_v2` 203 passed.

---

## Day 2 — Full gate — 2026-06-17

- **Vitest**: 146 files / **915 passed** (baseline 911 +4). ✅
- **lint**: `npm run lint` clean (no `--silent`; max-warnings 0; the jsx-ast-utils `TSSatisfiesExpression` notes are pre-existing parser warnings, not errors). ✅
- **build**: `npm run build` ✓ built in 3.71s. ✅
- **mockup-fidelity**: `npm run check:mockup-fidelity` PASS — styles-mockup.css byte-identical; **51** hardcoded hex/oklch (baseline 51, 0 new oklch). ✅
- **backend**: UNTOUCHED (FE-only, zero backend diff) → mypy 0/372 · run_all 10/10 · pytest 2731+5skip carry from 57.132 unchanged (not re-run — no backend file changed).
- **LLM-SDK-leak**: N/A (no backend change).

---

## Day 3 — Drive-through — 2026-06-17

**Setup**: backend :8000 PID 54504 (already running — FE-only, zero backend diff, no restart needed; the wire `cached_input_tokens` predates this sprint by 57.65/57.108) + Vite :3007 PID 31616 (HMR picked up the edits). dev-login jamie@acme.com · operator · acme-prod (no admin needed for chat). Fresh session, real_llm mode.

**Run** (real chat-v2 UI via Playwright + real Azure gpt-5.2):
- **Turn 1** "What is the capital of France? Answer in one word." → "Paris". Inspector Turn tab (Turn 1 · end_turn): `tokens.in = 2,435` · **`tokens.cached = —`** · **`cache_hit = —`** · `model = gpt-5.2`.
  - ✅ Correct: turn 1 is the first request → no prior prefix cached → Azure cached_tokens 0 → the 0-guard keeps `cachedInputTokens` null → renders "—" (an unmeasured 0 does NOT masquerade as a real "0" — by design, mirrors the tokensIn 0-guard).
- **Turn 2** (same session) "What is its approximate population? Answer in one short sentence." → "…about 2.1 million…". Inspector Turn tab (Turn 2 · end_turn): `tokens.in = 2,458` · **`tokens.cached = 2,048`** · **`cache_hit = 83%`** · `model = gpt-5.2`.
  - ✅ THE feature: turn-2 re-sends the ~2,435-token turn-1 prefix → Azure prompt-cache hit → `cached_input_tokens = 2048` on the `llm_response` wire → captured into `AgentTurn.cachedInputTokens` → `tokens.cached` renders "2,048" + derived `cache_hit` = round(2048 / 2458 × 100) = **83%** (math self-consistent).

**Observed vs intended**: EXACT match. The 2 new rows render REAL store-derived values (not fixture / not hardcoded) — they change between turns (turn 1 "—" → turn 2 "2,048" / "83%"), and the derived cache_hit equals the computed ratio. AP-4 walk: rows present, real values, "—" before a cache hit. Screenshot: `artifacts/drivethrough-57133-inspector-token-sweep-PASS.jpeg`.

**Verdict**: Drive-through PASS (real UI + real backend + real Azure, non-zero cache hit). Closes `AD-ChatV2-Inspector-Turn-Metadata-Wire` token-sweep leg.

---

## Day 4 — CHANGE-100 + closeout — 2026-06-17

- CHANGE-100 written; retrospective Q1-Q7; navigators + next-phase-candidates + calibration matrix updated; memory subfile + MEMORY.md pointer.
- Calibration: `chatv2-inspector-existing-field-surface` 0.85, 3rd data point. Bottom-up ~4.0 hr → committed ~3.4 hr (mult 0.85); actual ~3.2-3.5 hr → ratio ~0.94-1.03 IN band → KEEP 0.85 (3-pt 0.85/57.120 + ~0.88/57.131 + ~0.98/57.133 confirms class).
- Final gate sweep + commit; PR pending user confirmation.
