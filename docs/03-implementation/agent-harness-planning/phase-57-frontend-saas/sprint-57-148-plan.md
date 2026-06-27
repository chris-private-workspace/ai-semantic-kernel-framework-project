# Sprint 57.148 Plan — memory-formation Slice 1: user-identity write + always-on inject

**Summary**: Close 缺口 1 (identity auto-formation) of the memory-formation arc — the gap a live drive-through surfaced (new session → "你知道我是誰嗎?" → "我不知道你是誰"). Two coupled backend pieces, both required for a non-Potemkin fix: (a) a **formation nudge** in the chat system prompt so the agent proactively calls the already-wired `memory_write(scope=user)` when the user states durable identity/preference facts; (b) an **always-on user-profile injection** in the PromptBuilder that surfaces user-scope long_term facts UNCONDITIONALLY (NOT subject to the existing ILIKE query-gating that silently hides identity for a "who am I" question). Drive-through is MANDATORY (2 sessions, same dev-login user). This is a spike → a design note is required.

**Status**: Approved-to-execute (user picked 缺口 1 / identity thin slice, 2026-06-27 — "起 memory-formation 的 plan… 從缺口 1 身分擷取這片最小切入")
**Branch**: `feature/sprint-57-148-memory-formation-identity`
**Base**: `main` HEAD `3d5a1360` (chore: flip Sprint 57.147 PR-pending → MERGED, #349)
**Slice**: opens the new `AD-Memory-Formation-Identity` arc — Slice 1 of N (identity write+inject); cross-session message recall (缺口 2) + memory semantic axis (缺口 3 / CARRY-026) are later slices
**Scope decisions**: (a) **Option A formation = LLM nudge + reuse existing `memory_write`** (NOT a deterministic post-turn extraction step — heavier, Option B, deferred); (b) **surfacing = always-on user-profile pull** (wildcard user-scope long_term, NOT query-gated) because the live injection is ILIKE-keyword-gated and would hide identity; (c) **user-scope only** (tenant/role/session always-on = out); (d) **backend-only** — no migration (memory_user + UserLayer exist), no wire event, no frontend (the chat UI already renders the answer); (e) parent-direct.

---

## 0. Background

### The gap (`AD-Memory-Formation-Identity`)

A live drive-through on the real chat page exposed the platform's headline memory promise as non-functional in practice:

- User (new session): "你知道我是誰嗎? 也記得之前我有問過什麼問題嗎?"
- Agent: "我不知道你是誰 … 也沒有取到任何可用的『之前你問過什麼』的記錄或摘要。"

The 5-layer memory machinery is genuinely WIRED (auto-inject + real `memory_write`/`memory_search` handlers), but the **formation half is empty-spinning** and the **surfacing half is query-gated** — so nothing ever accumulates, and even if it did, an identity question wouldn't retrieve it.

### Why it matters (the missing capability)

This is the Claude-Code-equivalent of "the platform remembers who you are." CC achieves it with two halves — **formation** (you/`#` write a memory file) + **injection** (force-injected every session). This project built a strong **injection** half but the **formation** half never fires and the injection is keyword-gated, so the user experience is "it forgets me every time." Per the reality-audit north star, this is exactly an "引擎接好 ≠ 行為落地" gap (vision pillar: memory-equipped agents).

### Root cause (recon code read, file:line; ALL re-verified §checklist 0.1)

| Layer | Reality (on `main` HEAD `3d5a1360`) | Anchor |
|-------|-------------------------------------|--------|
| Auto-inject IS wired (not Potemkin) | real 5-scope `MemoryRetrieval` → PromptBuilder + executor | `api/v1/chat/handler.py:359,507,570` |
| **Surfacing is ILIKE query-gated** | injects ONLY hints whose `content`/`category` ILIKE-match the user's last message; empty query → `{}` | `prompt_builder/builder.py:581-594` + `memory/layers/user_layer.py:88-95` |
| **Formation never fires** | base system prompt has NO memory-formation instruction; `memory_write` is purely LLM-discretionary | `prompt_builder/templates.py:38` + (no nudge anywhere) |
| `memory_write` can persist user facts | `scope=user`, `time_scale=long_term` → `UserLayer.write` INSERT into `memory_user` (+ ops log) | `tools/memory_tools.py:172-218` + `user_layer.py:106-162` |
| user_id is stable across sessions | dev-login get-or-create by `(tenant, external_id=dev:<email>)`; JWT `sub=user.id` | `api/v1/auth.py:446-467` |

→ The fix must (1) make the agent WRITE durable user facts, and (2) SURFACE user-scope long_term facts unconditionally (bypassing ILIKE query-gating) so an identity question recalls them.

### The design (backend-only: 1 nudge string + 1 always-on profile pull + merge + tests)

```
# Formation (US-1) — chat system-prompt assembly (handler.py, where skills catalog is appended)
#   append MEMORY_FORMATION_NUDGE (only when memory tools wired):
#   "When the user shares durable facts about themselves (name, role, team, project,
#    preferences), call memory_write(scope='user', time_scale='long_term') to remember them."

# Surfacing (US-2) — DefaultPromptBuilder always-on user profile (NOT query-gated)
#   MemoryRetrieval.profile(tenant_id, user_id, top_k)        # NEW: wildcard user-scope long_term
#     -> UserLayer.read(query="", tenant_id, user_id, time_scales=("long_term",), max_hints=top_k)
#        (ILIKE '%%' matches all; ordered by confidence) — bypasses the empty-query guard
#   build(): merge profile hints into the 'user' layer block UNCONDITIONALLY,
#            dedup by hint_id vs the existing query-gated hints, respect the ≤2000-tok Tier2 cap

# Drive-through (US-3) — 2 sessions, SAME dev-login email (=> same user_id)
#   S1: "我是 Chris, 我在做知識連接器" -> agent calls memory_write(scope=user)
#   close -> S2 (new session_id, same user_id): "你知道我是誰嗎?"
#     -> always-on profile injects the fact -> agent: "你是 Chris, 在做知識連接器"
```

Why always-on injection over a "nudge the agent to call `memory_search` at session start": the search path is ALSO ILIKE query-gated and depends on the agent choosing a good query — unreliable. CC injects identity deterministically every session; the always-on profile pull is the faithful, falsifiable equivalent.

### Ground truth (recon head-start — code read on `main` HEAD `3d5a1360`; ALL re-verified §checklist 0.1)

- `prompt_builder/builder.py:581` — `if not query.strip(): return {}` (empty-query short-circuit; the always-on pull must NOT go through this).
- `memory/layers/user_layer.py:88-100` — `read()` ILIKE on content/category, order by confidence desc, `max_hints` cap; `query=""` → `ILIKE '%%'` matches all user rows.
- `tools/memory_tools.py:172-218` — `MEMORY_WRITE_SPEC` scope ∈ {session,user,tenant,role}; user-scope + long_term is exactly identity persistence.
- `api/v1/chat/handler.py:519-544` — system-prompt assembly seam (skills catalog + force-load appended here at handler construction) → the nudge rides the same seam.
- `api/v1/chat/_category_factories.py:264-307` — `make_chat_memory_deps` builds the real UserLayer (PostgreSQL); the `profile()` pull reuses this same retrieval.

**Baselines (57.147 closeout)**: pytest 2988 · wire 26 · Vitest 922 · mockup 51 · mypy 0/392 · run_all 11/11. Re-verify Day-0.

### STALE / drift findings (Day-0; full detail → progress.md — placeholder, filled in §checklist 0.1)

- **D-empty-query-guard** — confirm `MemoryRetrieval.search` (not just the builder) also guards empty query → decides whether `profile()` calls `UserLayer.read` directly or a new retrieval method.
- **D-write-upsert** — confirm `UserLayer.write` INSERTs (no upsert-by-key) → repeated identity writes make dup rows; acceptable for MVP (profile caps top-k by confidence), note as limitation.
- **D-nudge-seam** — confirm the `handler.py` system-prompt string is the seam reaching the real_llm loop (not overwritten downstream).
- **D-tier2-cap** — confirm the ≤2000-tok memory cap location so the always-on profile respects it.

## 1. Sprint Goal

Make the platform actually remember a user's stated identity across sessions: the agent proactively persists durable user facts (`memory_write` scope=user) and the PromptBuilder injects user-scope long_term facts unconditionally, PROVEN by a 2-session real-LLM drive-through (tell identity in S1 → recall in a fresh S2). Closes `AD-Memory-Formation-Identity` Slice 1; produces CHANGE-115 + spike design note `52-memory-formation-identity-design.md`.

## 2. User Stories

- **US-1** (formation): 作為使用者，我希望當我告訴 agent 我的身分／偏好時它會主動記住，以便我下次不必重講。
- **US-2** (surfacing): 作為使用者，我希望 agent 在新對話也能說出我是誰，以便延續脈絡 —— 且不受我問句的關鍵字是否命中影響。
- **US-3** (drive-through, MANDATORY): 作為驗證者，我要一個 2-session 真實 drive-through（同一 dev-login 用戶）證明跨 session 身分回憶，而非 gate-only。
- **US-4** (closeout): CHANGE-115 + design note 52（8-point gate）+ calibration + navigators。

## 3. Technical Specifications

### 3.0 Architecture (backend-only; NO migration / NO wire event / NO frontend)

```
EDIT  business_domain/.../system prompt seam (handler.py)   — append MEMORY_FORMATION_NUDGE when memory tools wired
EDIT  agent_harness/memory/retrieval.py                     — NEW profile(tenant_id, user_id, top_k) wildcard user-scope pull
EDIT  agent_harness/prompt_builder/builder.py               — always-on user-profile merge into 'user' block (dedup + Tier2 cap)
EDIT  agent_harness/tools/memory_tools.py (maybe)           — only if the nudge text belongs near the spec (TBD Day-1; likely NOT)
EDIT  tests: test_prompt_builder_memory.py / test_memory_retrieval.py / test_chat_handler_*  — profile pull + always-on inject + nudge presence + multi-tenant
UNTOUCHED  infrastructure/db (memory_user exists) · loop.py · executor.py · wire schema (26) · frontend
```

### 3.1 Formation nudge (US-1) — system-prompt seam

- Append a concise memory-formation instruction to the chat system prompt at the `handler.py` assembly seam (rides the skills-catalog seam ~519-544), gated on memory tools being wired (so echo/tests unaffected).
- Instruction: when the user states durable self-facts (name/role/team/project/preferences) → call `memory_write(scope='user', time_scale='long_term')`. Mirrors how the skills catalog block nudges `read_skill`.

### 3.2 Always-on user-profile injection (US-2) — `retrieval.py` + `builder.py`

- NEW `MemoryRetrieval.profile(tenant_id, user_id, top_k)` → `UserLayer.read(query="", time_scales=("long_term",))` (wildcard, confidence-ordered, capped). Bypasses the empty-query guard by NOT routing through `search()` (or a dedicated guard-free branch — settle Day-1 per D-empty-query-guard).
- `DefaultPromptBuilder.build()`: after the existing query-gated `_inject_memory_layers`, pull `profile()` and merge into the `user` layer block UNCONDITIONALLY; dedup by `hint_id`; keep within the ≤2000-tok Tier2 cap (profile facts take priority — they are the always-relevant context).
- Render under an "About this user" sub-heading so the model treats it as standing context, not a query result.

### 3.x What is explicitly NOT done

- Deterministic post-turn fact-extraction (Option B) — heavier; deferred.
- Upsert-by-key in `UserLayer.write` (dedup dup identity rows) — deferred; MVP tolerates dups (profile caps top-k).
- tenant/role/session always-on injection — out (identity = user-scope).
- Cross-session message/conversation recall (缺口 2) + memory semantic/Qdrant axis (缺口 3 / CARRY-026) — separate slices.
- Frontend — none (agent answer already renders).

### 3.y Validation (US-1..US-4)

Gates: mypy `src` 0 · run_all 11/11 · pytest ≥2988 (+ new) · Vitest 922 (untouched) · mockup 51 (untouched) · `npm run lint && npm run build` (FE untouched; run if any FE file moves) · black/isort/flake8 clean · LLM-SDK-leak clean. Plus the §3.1/3.2 2-session drive-through (MANDATORY).

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 1 | `api/v1/chat/handler.py` (or the precise system-prompt seam) | EDIT — append formation nudge |
| 2 | `agent_harness/memory/retrieval.py` | EDIT — NEW `profile()` |
| 3 | `agent_harness/prompt_builder/builder.py` | EDIT — always-on user-profile merge |
| 4 | `agent_harness/memory/layers/user_layer.py` | EDIT (maybe) — only if a guard-free wildcard read needs a hook |
| 5 | tests (prompt builder / retrieval / handler) | EDIT/NEW — profile + inject + nudge + multi-tenant |
| 6 | `claudedocs/4-changes/feature-changes/CHANGE-115-*.md` | NEW |
| 7 | `docs/.../planning/52-memory-formation-identity-design.md` | NEW (spike design note) |
| — | `infrastructure/db/**` · `loop.py` · `executor.py` · wire schema · `frontend/**` | **UNTOUCHED** |

## 5. Acceptance Criteria

1. The chat system prompt contains a memory-formation nudge ONLY when memory tools are wired (unit-asserted).
2. `MemoryRetrieval.profile()` returns user-scope long_term facts regardless of query, tenant+user scoped (multi-tenant test: tenant A profile never returns tenant B rows).
3. `DefaultPromptBuilder.build()` injects profile facts unconditionally (even when the user message keyword-mismatches), deduped, within the Tier2 cap (unit-asserted).
4. **Drive-through PASS (MANDATORY, real UI + backend + LLM)** — S1 tell identity → agent persists (`memory_write` user row in DB); fresh S2 (same user_id) "你知道我是誰嗎?" → agent recalls name+context; screenshot + observed-vs-intended in progress.md. (NOT gate-only.)
5. `AD-Memory-Formation-Identity` Slice 1 CLOSED; CHANGE-115 + design note 52 (8-point gate); calibration recorded; navigators + next-phase-candidates updated.

## 6. Deliverables

- [ ] US-1 formation nudge in chat system prompt
- [ ] US-2 `profile()` + always-on injection + dedup + cap
- [ ] US-3 2-session drive-through PASS (real LLM)
- [ ] US-4 CHANGE-115 + design note 52 + closeout

## 7. Workload Calibration

- Scope class **NEW `memory-formation-identity-spike` 0.60** (1st data point). Anchored between `verification-in-loop-spike` 0.60 (a Cat-core new-domain spike with a real-code core) and `harness-loadbearing-gap-fix` 0.85 (57.122 — make an existing mechanism load-bearing + full-ceremony drive-through). Set 0.60 NOT 0.85 because the real-code core (new `profile()` + builder merge + nudge + multi-tenant tests, ~3-4 hr) holds the spike multiplier per the 57.137 lesson — this is NOT a tiny-code-wrapped-in-ceremony sprint. **Variance driver = the 2-session drive-through setup** (2 dev-login sessions + clean restart + DB verify); if it lands > 1.20, re-point toward 0.85 (the 57.120/122/126/129/132 ceremony-not-code-accelerated pattern).
- **Agent-delegated: no** (parent-direct; touches the load-bearing prompt path + needs careful design judgment on always-on injection + a careful 2-session drive-through). `agent_factor` 1.0 → 3-segment form.
- Bottom-up est ~7-9 hr (nudge ~0.5 · profile() ~1 · builder merge ~1.5-2 · tests ~1.5-2 · drive-through ~1.5-2 · docs ~1.5) → class-calibrated commit ~4.5-5 hr (mult 0.60). Day-4 retro Q2 verifies.

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| **Always-on injection floods prompt / dups query-gated hints** | dedup by `hint_id`; cap to top-k by confidence within the ≤2000-tok Tier2 budget; user-scope only |
| **Empty-query guard blocks the wildcard pull** (D-empty-query-guard) | `profile()` calls `UserLayer.read(query="")` directly (ILIKE `%%`), NOT via `search()`'s guard — settle exact path Day-1 |
| **Agent doesn't obey the nudge (real-LLM non-determinism)** | nudge is explicit + scoped; drive-through uses a clear "我是 X, 在做 Y" statement; if the agent still skips, treat as a finding (tune nudge), not a silent pass |
| **Dup identity rows from repeated writes** (D-write-upsert) | acceptable for MVP (profile top-k by confidence); upsert-by-key deferred + noted in design note §Open Invariants |
| **Stale `--reload` masks the nudge/profile wiring** (Risk Class E) | clean restart + verify sole live worker (Win32_Process PID/PPID/StartTime) + startup log before the drive-through |
| **DB-touching handler test isolation** (Risk Class C) | ensure the suite's `get_db_session` override / autouse session fixture covers the memory-read path |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- Cross-session conversation/message recall + session-summary into Layer 5 (缺口 2) — `AD-Memory-Formation-Session-Recall`.
- Memory semantic/Qdrant axis (缺口 3) — CARRY-026 (the 57.147 per-tenant pattern is reusable).
- Deterministic post-turn fact extraction (Option B) — `AD-Memory-Formation-Auto-Extract`.
- Upsert-by-key in `UserLayer.write` — `AD-Memory-User-Upsert-By-Key`.
- tenant/role/session always-on injection — future memory-surfacing slice.
