# Sprint 57.133 Plan — chat-v2 Inspector Turn tab token-sweep (cached + cache-hit rows)

**Summary**: FE-only. Surface per-turn `cached_input_tokens` + a derived `cache_hit` rate in the chat-v2 Inspector Turn tab, closing the **last open leg** of `AD-ChatV2-Inspector-Turn-Metadata-Wire` (the token-sweep leg; the `active_skill` leg shipped 57.120, the `model` leg shipped 57.131). The data is ALREADY on the SSE wire (`llm_response.cached_input_tokens` since Sprint 57.65/57.108) → no backend / wire / codegen / migration; the FE just doesn't read it yet. Drive-through is MANDATORY (Inspector is a user-facing surface). NO design note (continuation of the existing wire AD; no new contract).

**Status**: Approved-to-execute (user 2026-06-17: "現在開始執行 Inspector token-sweep leg、transcript retention(57.125)" — Inspector token-sweep is the first-listed item; transcript retention follows as a separate slice per rolling discipline).
**Branch**: `feature/sprint-57-133-chatv2-inspector-token-sweep`
**Base**: `main` HEAD `3e8ee330` (Sprint 57.132 flip PR #311 merged)
**Slice**: closes the token-sweep leg of `AD-ChatV2-Inspector-Turn-Metadata-Wire` (bucket-C; the wire AD's final leg → AD fully CLOSED after this).
**Scope decisions**: (a) add `cachedInputTokens: number | null` to `AgentTurn` (required, mirroring the `tokensIn` token-cluster siblings) + capture it in the `llm_response` reducer with the same 0-guard as 57.108. (b) `cache_hit` is DERIVED in render (`cachedInputTokens / tokensIn`) — no new field / no new store state. (c) the "actual `input_tokens` vs the `tokens_in` estimate" dual-display is a YAGNI carve-out (the actual already overwrites the estimate at `llm_response`; the actual IS the truth) → §9.

---

## 0. Background

### The gap (`AD-ChatV2-Inspector-Turn-Metadata-Wire` — token-sweep leg)

The Inspector Turn tab shows `tokens.in` / `tokens.out` / `tokens.thinking` per turn, but NOT:
- `cached_input_tokens` — how many of the prompt tokens were a prompt-cache hit this turn.
- `cache_hit` rate — `cached_input_tokens / input_tokens` (the fraction of the prompt served from cache).

Both numbers are already produced by the backend (Azure adapter extracts `prompt_tokens_details.cached_tokens`; Sprint 57.65 A-2) and already serialized to the wire on `llm_response` (Sprint 57.108), but the chat-v2 store never reads `cached_input_tokens` and the `AgentTurn` type has no field for it.

### Why it matters (the missing capability)

Prompt-cache hits are the single biggest per-turn cost / latency lever, and the operator-facing Inspector is where a turn's economics are read. Without the cached / cache-hit rows, an operator can't tell whether a long multi-turn session is actually benefiting from caching — the data is on the wire but invisible.

### Root cause (recon code read, file:line; ALL re-verified §checklist 0.1)

| Layer | Reality (on `main` HEAD `3e8ee330`) | Anchor |
|-------|--------------------------------------|--------|
| backend usage | Azure adapter populates `TokenUsage.cached_input_tokens` from `prompt_tokens_details.cached_tokens` | `adapters/azure_openai/adapter.py:445-457` |
| loop event | `LLMResponded` carries `input_tokens` / `output_tokens` / `cached_input_tokens` | `agent_harness/_contracts/events.py:96-124` |
| wire | `llm_response` serializes `cached_input_tokens` / `input_tokens` / `output_tokens` | `api/v1/chat/event_wire_schema.py:103-110` + `api/v1/chat/sse.py:169-191` |
| store capture | `llm_response` case captures `input_tokens` / `output_tokens` (0-guard overwrite) but NOT `cached_input_tokens` | `store/chatStore.ts:592-600` |
| type | `AgentTurn` has `tokensIn/Out/Thinking`, `model`, … but NO `cachedInputTokens` | `types.ts:159-189` |
| render | `InspectorTurn` shows `tokens.in/out/thinking` but no cached / cache_hit row | `components/inspector/InspectorTurn.tsx:173-179` |

→ The fix reads an already-on-wire field into a new `AgentTurn` field and renders 2 KV rows. Pure frontend, mirroring the 57.131 `model`-row and 57.120 `active_skill`-row pattern exactly.

### The design (FE-only: 1 type field + 1 store init + 1 store capture + 2 KV rows + tests)

```
types.ts            AgentTurn += cachedInputTokens: number | null   (token-cluster sibling of tokensIn)
chatStore.ts        turn_start: init cachedInputTokens: null
                    llm_response: cachedInputTokens = ev.data.cached_input_tokens > 0
                                    ? ev.data.cached_input_tokens : t.cachedInputTokens   (0-guard, mirrors 57.108 tokensIn/out)
InspectorTurn.tsx   after tokens.thinking, before cost:
                      <KV k="tokens.cached" v={cachedInputTokens?.toLocaleString() ?? "—"} mono />
                      <KV k="cache_hit"     v={derive(cachedInputTokens, tokensIn) }      mono />
                    derive = (cached!=null && tokensIn>0) ? `${(cached/tokensIn*100).toFixed(0)}%` : "—"
```

WHY a derived `cache_hit` over a new store field: the rate is a pure function of two values already on the turn (`cachedInputTokens`, `tokensIn`); persisting it would duplicate state that can drift. The wire's `loop_end.cache_hit_rate` is *cumulative*; we want *per-turn*, so derive locally.

### Ground truth (recon head-start — code read on `main` HEAD `3e8ee330`; ALL re-verified §checklist 0.1)

- `store/chatStore.ts:598-599` — the `input_tokens > 0 ? … : t.tokensIn` 0-guard to mirror for cached (an unmeasured 0 must not clobber a real prior count).
- `store/chatStore.ts:512-520` — `turn_start` `AgentTurn` literal (add `cachedInputTokens: null`).
- `components/inspector/InspectorTurn.tsx:173-179` — the `tokens.in/out/thinking` KV cluster (insert the 2 new rows after `tokens.thinking`, before `cost`, to keep all token rows contiguous); `KV` helper + `mono` already exist (`:64-71`).
- `types.ts:177` — the `model` field (Sprint 57.131) — add `cachedInputTokens` in the token cluster (`:168-171`).
- 57.131 Day-0 lesson: a NEW required `AgentTurn` field triggers a tsc ripple in `AgentTurn` literals / factories in tests → Day-0 Prong-2 grep enumerates them.

**Baselines (57.132 closeout)**: pytest 2731 (+5 skip) · wire 25 · Vitest 911 · mockup 51 · mypy 0/372 · run_all 10/10. Backend gates UNTOUCHED this sprint (FE-only). Re-verify Day-0.

### STALE / drift findings (Day-0; full detail → progress.md — placeholder, filled in §checklist 0.1)

- **D-generated-cached** — grep `frontend/src/features/chat_v2/generated/loopEvents.generated.ts` that the `llm_response` interface carries `cached_input_tokens: number` (proves no codegen needed) → if absent, scope shifts to wire/codegen (unexpected).
- **D-agentturn-literals** — grep every `AgentTurn` literal / `makeAgentTurn`-style factory (src + tests) → the required-field tsc ripple set (mirror 57.131 +2 factories).
- **D-baselines** — confirm Vitest 911 · mockup 51 · the FE build is green at base.

## 1. Sprint Goal

Surface per-turn prompt-cache economics in the chat-v2 Inspector Turn tab by reading the already-on-wire `cached_input_tokens` into a new `AgentTurn` field and rendering a `tokens.cached` row + a derived `cache_hit` row — closing the final leg of `AD-ChatV2-Inspector-Turn-Metadata-Wire`. Proven by Vitest (store capture + render rows) + `npm run lint && npm run build` clean + mockup 51 byte-identical + a MANDATORY drive-through (real chat-v2 UI + real Azure across ≥2 turns showing real cached / cache_hit values). CHANGE-100; NO design note.

## 2. User Stories

- **US-1** (store): 作為 chat-v2 前端，我希望在 `llm_response` 時把 `cached_input_tokens` 捕捉到 `AgentTurn.cachedInputTokens`，以便每個 turn 的 cache 命中數可被 Inspector 讀取。
- **US-2** (render): 作為操作者，我希望 Inspector Turn tab 顯示 `tokens.cached` 與衍生的 `cache_hit`，以便評估此 turn 的 prompt-cache 經濟性。
- **US-3** (drive-through MANDATORY): 作為驗收者，我希望開真 UI + 真 Azure 跑 ≥2 turn，親眼確認 cached / cache_hit 列渲染真實值（非 fixture / 非寫死），以便確定功能可用而非 Potemkin。
- **US-4** (closeout): CHANGE-100 + retrospective + navigators + AD CLOSED。

## 3. Technical Specifications

### 3.0 Architecture (FE-only; NO backend / wire / codegen / migration / new CSS)

```
EDIT  frontend/src/features/chat_v2/types.ts                          AgentTurn += cachedInputTokens: number | null
EDIT  frontend/src/features/chat_v2/store/chatStore.ts                turn_start init + llm_response capture (0-guard)
EDIT  frontend/src/features/chat_v2/components/inspector/InspectorTurn.tsx   +2 KV rows (tokens.cached + derived cache_hit)
EDIT  frontend/tests/unit/features/chat_v2/...                        store capture test + InspectorTurn render test + factory ripple fix
UNTOUCHED  backend/** · generated/loopEvents.generated.ts · styles-mockup.css · event_wire_schema.py
```

### 3.1 Store (US-1) — `store/chatStore.ts`

- `turn_start` `AgentTurn` literal (`:512-520`): add `cachedInputTokens: null` in the token cluster (after `costUsd: null`, near `model: null`).
- `llm_response` reducer (`:595-600`): add `cachedInputTokens: ev.data.cached_input_tokens > 0 ? ev.data.cached_input_tokens : t.cachedInputTokens` — same 0-guard as `tokensIn`/`tokensOut` (an old frame / unmeasured 0 must not clobber a real prior value). `cached_input_tokens` is already typed on the generated `llm_response` interface (D-generated-cached confirms).

### 3.2 Type (US-1) — `types.ts`

- `AgentTurn` (`:168-171`): add `cachedInputTokens: number | null` in the token cluster with a comment mirroring the 57.131 `model` comment (captured at `llm_response` from `cached_input_tokens`; null until the turn's first `llm_response`; closes the token-sweep leg).

### 3.3 Render (US-2) — `components/inspector/InspectorTurn.tsx`

- After `tokens.thinking` (`:176-179`), before `cost` (`:180`), add:
  - `<KV k="tokens.cached" v={lastAgent.cachedInputTokens != null ? lastAgent.cachedInputTokens.toLocaleString() : "—"} mono />`
  - `<KV k="cache_hit" v={cacheHitLabel} mono />` where `cacheHitLabel` is derived above the JSX: `const cacheHitLabel = lastAgent.cachedInputTokens != null && lastAgent.tokensIn != null && lastAgent.tokensIn > 0 ? \`${Math.round((lastAgent.cachedInputTokens / lastAgent.tokensIn) * 100)}%\` : "—";`
- Reuses the existing `KV` helper + `mono` → 0 new mockup CSS / HEX / oklch (mockup 51 byte-identical). Update the file-header MHist (1-line) + the docstring "8 KV rows" count.

### 3.x What is explicitly NOT done

- No "actual `input_tokens` vs estimate" dual display — the actual overwrites the estimate at `llm_response` and IS the surfaced truth; carrying a stale estimate alongside adds state for marginal value (carve-out → §9).
- No cumulative `loop_end.cache_hit_rate` session row — this leg is per-turn; a session-level cache summary is a separate (YAGNI) idea.
- No `cost` in-stream change (the existing `AD-ChatV2-Inspector-Cost-InStream` carve-out stands; cost stays honest "—" post-loop by design).

### 3.y Validation (US-1..US-4)

Gates: Vitest 911 + new · `npm run lint && npm run build` clean (NO `--silent`) · mockup 51 (`diff` empty). Backend UNTOUCHED → mypy 0/372 · run_all 10/10 · pytest 2731+5skip unchanged (re-verified as a sanity sweep, not modified). Plus the §3 drive-through (MANDATORY).

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 1 | `frontend/src/features/chat_v2/types.ts` | EDIT (AgentTurn += cachedInputTokens) |
| 2 | `frontend/src/features/chat_v2/store/chatStore.ts` | EDIT (turn_start init + llm_response capture) |
| 3 | `frontend/src/features/chat_v2/components/inspector/InspectorTurn.tsx` | EDIT (+2 KV rows + derive + docstring/MHist) |
| 4 | `frontend/tests/unit/features/chat_v2/**` | EDIT (store capture + render rows + factory ripple) |
| 5 | `claudedocs/4-changes/feature-changes/CHANGE-100-*.md` | NEW |
| — | `frontend/src/features/chat_v2/generated/loopEvents.generated.ts` | **UNTOUCHED** (cached_input_tokens already generated) |
| — | `backend/**` · `event_wire_schema.py` · `styles-mockup.css` | **UNTOUCHED** |

## 5. Acceptance Criteria

1. `AgentTurn.cachedInputTokens` captured from `llm_response.cached_input_tokens` with the 0-guard; unit test proves a real value lands + a 0/absent frame doesn't clobber a prior value.
2. Inspector Turn tab renders `tokens.cached` (count or "—") + `cache_hit` (rounded % or "—"); unit test asserts both rows + the derived %.
3. mockup 51 byte-identical (`diff` empty); `npm run lint && npm run build` clean; backend gates unchanged.
4. **Drive-through PASS (MANDATORY, real UI + backend + LLM)** — real chat-v2 UI + real Azure, ≥2 turns; Inspector Turn tab shows real `tokens.cached` + `cache_hit` (target a non-zero cache hit on turn 2; if Azure caching does not fire, a truthful "0 / 0%" render is acceptable and labeled honestly — NOT Potemkin); screenshot + observed-vs-intended in progress.md.
5. `AD-ChatV2-Inspector-Turn-Metadata-Wire` CLOSED (all 3 legs done); CHANGE-100; calibration recorded; navigators + next-phase-candidates updated.

## 6. Deliverables

- [ ] US-1 store capture (turn_start init + llm_response 0-guard) + type field
- [ ] US-2 InspectorTurn `tokens.cached` + derived `cache_hit` rows
- [ ] US-3 drive-through PASS (real UI + Azure, ≥2 turns)
- [ ] US-4 CHANGE-100 + closeout + AD CLOSED

## 7. Workload Calibration

- Scope class **`chatv2-inspector-existing-field-surface` 0.85** (3rd data point; 57.120 = 0.85 re-point, 57.131 = 0.85 2nd-pt ratio ~0.82-0.93 IN band → KEEP 0.85). Same shape: surface an already-store-reachable / already-on-wire field in a new Inspector render location + a thin store capture; tiny code, full ceremony — ceremony-not-code-accelerated.
- **Agent-delegated: no** (parent-direct; ~10-line FE change, not worth a code-implementer agent). `agent_factor` 1.0 → 3-segment form (class-calibrated commit IS the final commit).
- Bottom-up est ~4.0 hr (type+store ~0.5, render+derive ~0.5, tests ~1.0, drive-through ~1.5, closeout ~0.5) → class-calibrated commit ~3.4 hr (mult 0.85). Day-4 retro Q2 verifies.

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| Required `AgentTurn` field → tsc ripple in test factories (57.131 lesson) | Day-0 Prong-2 `D-agentturn-literals` grep enumerates all literals/factories; fix in the same Day-1 commit |
| Azure prompt caching may not fire on a short session → cached=0 (drive-through non-determinism, cf. 57.122/129/130) | Drive-through uses ≥2 turns with the harness's large system prompt (input_tokens routinely >1024 → turn-2 prefix cache likely); a truthful "0 / 0%" render is an acceptable (labeled-honest) drive-through of the render path — the AD is "surface the field", and 0 is a real value, not a fixture |
| Stale `--reload` backend masks nothing (FE-only) but Vite may serve stale bundle | Risk Class E variant: FE-only → no backend restart needed; hard-reload the browser / confirm Vite picked up the edit before drive-through |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- "actual `input_tokens` vs the `tokens_in` estimate" dual display — carve-out (actual is the surfaced truth; the estimate is transient). If ever wanted, a separate tiny leg.
- A session-level cumulative cache summary (`loop_end.cache_hit_rate`) — separate YAGNI idea.
- **transcript retention (57.125)** — the OTHER user-named bucket-C item; a backend retention/cleanup infra slice → runs as its own sprint AFTER this one (rolling discipline).
