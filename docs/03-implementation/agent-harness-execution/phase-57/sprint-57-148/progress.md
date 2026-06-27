# Sprint 57.148 Progress — memory-formation Slice 1 (user-identity write + always-on inject)

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-148-plan.md) · [Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-148-checklist.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch — 2026-06-27

Branch `feature/sprint-57-148-memory-formation-identity` from `main` `3d5a1360`.

### Prong 1 — path verify ✅
All edit targets exist: `api/v1/chat/handler.py`, `agent_harness/memory/retrieval.py`, `agent_harness/prompt_builder/builder.py`, `agent_harness/memory/layers/user_layer.py`, `agent_harness/tools/memory_tools.py`, the 4 test files. `CHANGE-115` + `52-memory-formation-identity-design.md` free.

### Prong 2 — content verify (drift findings)

| D-ID | Finding | Implication |
|------|---------|-------------|
| **D-empty-query-guard** | `MemoryRetrieval.search` has NO empty-query guard (only `tenant_id is None` → `[]`, `retrieval.py:67`); the empty-query short-circuit lives in the BUILDER (`builder.py:581`). | `profile()` dispatches to the user layer with `query=""` directly → bypasses the builder guard cleanly. No new guard-free branch needed. |
| **D-write-upsert** | `UserLayer.write` always INSERTs (new uuid4, `category="general"`, `user_layer.py:135`); no upsert-by-key. | Repeated identity writes make dup rows. MVP tolerates it (profile caps top-k by confidence). Noted as a deferred refinement (`AD-Memory-User-Upsert-By-Key`). |
| **D-nudge-seam** | The handler's `system_prompt` reaches the LLM via the LOOP prepending it as the system message (`handler.py:750` → `loop.py:410` `self._system_prompt` → `loop.py:1970`), NOT via the PromptBuilder's `_system_role_text`. The skills catalog already rides this exact seam (drive-through-proven). | The nudge goes in `handler.py` next to the skills catalog (`:524-544`), gated on `memory_retrieval is not None`. Guaranteed to reach the LLM identically. |
| **D-tier2-cap** | `_apply_memory_budget(memory_layers, tools=...)` at `builder.py:257`, AFTER `_inject_memory_layers` (`:246-252`); caps to `self._max_memory_tokens` (default 2000). | The always-on profile merge inserts BETWEEN 252 and 257 → the existing budget cap automatically bounds the merged set. |

### Prong 2.5 — N/A (no frontend page work this sprint).
### Prong 3 — schema verify: N/A — `memory_user` + `UserLayer` exist; NO migration (identity facts use the existing `content` column).

### Bonus recon finding
`agent_harness.memory.extraction.MemoryExtractor.extract_session_to_user` ALREADY exists (LLM-extracts session messages → user memory). This is the Option-B (deterministic post-turn extraction) building block — present but NOT wired to the chat path (confirms the "formation half empty-spinning" diagnosis). This sprint uses Option A (nudge); MemoryExtractor is the foundation for a future Option-B slice. Noted for the design note.

### Baselines (57.147 closeout) — to re-verify Day 4
pytest 2988 · wire 26 · Vitest 922 · mockup 51 · mypy 0/392 · run_all 11/11.

### Go/no-go ✅
Scope-shift **0%** — Risk A (ILIKE query-gating) CONFIRMED real (`builder.py:581` + `user_layer.py:88-95`) → the always-on-inject design holds exactly as planned. Risk B (user_id stability) GREEN — dev-login get-or-create by `(tenant, external_id=dev:<email>)` (`auth.py:446-459`), JWT `sub=user.id` → same email → same user_id. **Proceed.**

---

## Day 1 — Surfacing core: always-on user-profile (US-2) — 2026-06-27

- **1.1** `MemoryRetrieval.profile(tenant_id, user_id, top_k)` (`retrieval.py`) — wildcard user-scope long_term pull; `[]` without tenant/user or user layer; bypasses the builder's empty-query guard. 4 unit tests.
- **1.2** `DefaultPromptBuilder.build()` always-on merge (`builder.py`) — pull `profile()` (gated on `user_id is not None`), prepend into the `user` layer block, dedup by `hint_id`, within the Tier2 cap; graceful-degrade on profile() failure. New ctor param `profile_top_k=5`. 4 unit tests.
- **1.3** multi-tenant isolation — profile() with `query=""` still enforces the tenant filter (tenant B sees 0 of tenant A's rows). 1 integration test.

## Day 2 — Formation nudge (US-1) + full gate — 2026-06-27

- **2.1** `MEMORY_FORMATION_NUDGE` constant (`memory_tools.py`) + appended to the chat system prompt in `handler.py` gated on `memory_retrieval is not None` (real path always wired; echo path byte-identical). 2 handler tests (nudge present on real_llm path / absent on echo path).
- **2.2** Gate ✅: 42 affected tests pass (+11 new) · mypy `src` 0/392 · run_all **11/11** (incl. check_promptbuilder_usage / check_tool_descriptions / check_llm_sdk_leak) · black/isort/flake8 clean on all 8 touched files.

**Code change summary** (backend-only; NO migration / wire / frontend):
- EDIT `agent_harness/memory/retrieval.py` — `profile()` + header MHist
- EDIT `agent_harness/prompt_builder/builder.py` — ctor `profile_top_k` + always-on merge + header MHist
- EDIT `agent_harness/tools/memory_tools.py` — `MEMORY_FORMATION_NUDGE` + header MHist
- EDIT `api/v1/chat/handler.py` — import + append nudge gated on memory tools
- EDIT 4 test files (+11 tests)

---

## Day 3 — Drive-through (US-3) — ✅ PASS (real UI + real backend + real Azure gpt-5.2) — 2026-06-27/28

### 3.1 Clean restart (Risk Class E)
Killed stale backend python PID 54568 (pre-edit code), confirmed `:8000` free + ALL python gone (no orphans) + node frontend PID 31616 (port 3007) untouched. Fresh `dev.py restart backend` → reloader PID 46684 + worker PID 30056 (both fresh) serving my branch code; `/api/v1/health` 200. 57.147 test env (`KNOWLEDGE_VECTOR_ENABLED` / temp corpus) was shell-set, NOT in `.env` → fresh process is clean default. Real Azure (3 keys) wired.

### 3.2 Drive-through (3 legs, all PASS — NOT gate-only)

User: **jamie@acme.com** / acme-prod — `user_id=04dc4ee0-b672-4e44-a997-61c905ef2cb9`, `tenant=09eb1b62-…`. **Baseline: 0 `memory_user` rows.**

**Leg 1 — formation (S1)**: typed "你好，我是 Chris，我在這個平台負責知識連接器（knowledge connector）功能的開發。" (NO "please remember me"). The real gpt-5.2 agent PROACTIVELY called `memory_write(scope=user, time_scale=long_term)` **twice** (the nudge worked). DB after (was 0 → 2):
- `[16:07:10] conf=0.90 perm :: 'User name is Chris.'`
- `[16:07:12] conf=0.85 perm :: 'Chris is responsible for developing the Knowledge Connector feature on this platform.'`
Session showed `gpt-5.2 · 2 turns`. Screenshot `sprint-57-148-s1-formation.png`.

**Leg 2 — cross-session recall (S2, the headline fix)**: clicked **New session** (new `session_id`, SAME `user_id`), asked "你知道我是誰嗎？也記得我在負責什麼工作嗎？" — **ZERO keyword overlap** with the stored "User name is Chris". Agent replied: **「你是 Chris。我也記得你目前負責在這個平台上開發 Knowledge Connector 功能。」** Inspector Memory showed 2 user-layer **read** ops (trace `ddc56264484a496981f4d005a1a430e9`) surfacing both facts — proving the always-on `profile()` inject bypasses the ILIKE query-gating that caused the original "我不知道你是誰". Screenshot `sprint-57-148-s2-recall.png`.

**Leg 3 — per-user isolation**: re-logged-in as **priya@acme.com** (different `user_id`, same tenant), asked the same question. `mentionsChris=false`; agent: **「我不知道你是誰…目前我的記憶裡沒有任何關於你的身份或職務的資訊。」** Chris's facts never leak to a different user on the real path. Screenshot `sprint-57-148-s3-isolation-priya.png`.

**Verdict**: the exact failure the user reported (new session → "我不知道你是誰") is FIXED end-to-end on real UI + real backend + real Azure gpt-5.2; formation (proactive write) + surfacing (always-on inject, keyword-independent) + per-user isolation all proven. NOT gate-only.

(Screenshots in the Playwright output dir → to be copied to `artifacts/` Day 4. `memory_user` rows for jamie left as evidence; harmless dev data.)

## Day 4 — CHANGE-115 + design note 52 + closeout — PENDING (full pytest re-verify · CHANGE-115 · design note 52 8-point gate · retrospective · navigators · commit pending user confirmation)
