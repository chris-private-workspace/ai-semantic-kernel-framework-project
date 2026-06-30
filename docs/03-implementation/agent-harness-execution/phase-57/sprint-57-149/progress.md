# Sprint 57.149 Progress — memory Option-B deterministic post-send fact extraction

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-149-plan.md) · [Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-149-checklist.md)

---

## Day 0 — 2026-06-28 — Plan-vs-Repo Verify (三-prong) + Branch

### Three-prong verify (against `main` HEAD `694e0062`)

**Prong 1 — path verify** ✅ all edit targets exist; NEW docs free:
- `_category_factories.py` / `extraction.py` / `user_layer.py` / `handler.py` / `router.py` / `core/config/__init__.py` — present
- `test_extraction.py` / `test_extraction_worker.py` — present
- `sprint-57-149-*` / `CHANGE-116` / `53-memory-auto-extract-design.md` — free (Glob 0 results)

**Prong 2 — content verify** — Drift findings:

| ID | Finding | Implication |
|----|---------|-------------|
| **D-msgstore-load** | `DBMessageStore.load() -> list[Message]` (`message_store.py:124`), NO params → returns the FULL session ledger. `MessageStore` ABC `state_mgmt/_abc.py:66`. | Extractor input = whole ledger; rely on prompt-level dedup (read `profile()` first). Whole-ledger is fine for MVP (compaction bounds length); a recent-K cap is NOT needed Day-1 (revisit only if prompts grow). |
| **D-write-source** | `MemoryUser.source: Mapped[str \| None]` column ALREADY exists (`infrastructure/db/models/memory.py:230`). | `UserLayer.write(source=...)` writes a real column — **NO migration, NO metadata fallback**. Prong 3 = clean N/A. |
| **D-extractor-msg-type** | `DBMessageStore.load()` yields `agent_harness._contracts.Message`; `MemoryExtractor.extract_session_to_user(messages: list[Message])` consumes the SAME type. | No adapter / conversion needed between the ledger and the extractor. |
| **D-cheap-tier** | `build_real_llm_handler` builds `profile = build_azure_model_profile(model_policy)` (`handler.py:352`); `profile.cheap` = cheap tier (same as verifier 57.97 / compaction 57.109); `memory_layers["user"]` = real `UserLayer` (`:360`). | Both extractor deps are in `build_real_llm_handler` scope. Use cheap tier (the `handler.py:347` comment says "memory extraction run on profile.action" but no extraction exists yet — I wire it to **cheap**, consistent with the other background LLM calls; update that comment). |
| **D-handler-return** | `build_handler`/`build_real_llm_handler` return `AgentLoopImpl` (`:301`/`:810`). Callers: router `:316`, `resume/service.py:125`, **~10 unit tests** assert `loop = build_*_handler()`. | Returning a `(loop, extractor)` tuple would break all ~12 callers (anti-surgical). **RESOLVED**: add a self-contained `build_chat_memory_extractor(model_policy, db) -> MemoryExtractor \| None` in `handler.py` (late-imports `build_azure_model_profile` like `build_real_llm_handler`, builds `profile.cheap` + `UserLayer` via `make_chat_memory_deps`); the router's real_llm path calls it separately. 0 caller breakage. Re-building the profile object (no API call) is a negligible cost vs threading through `build_handler`. Plan §3.1/§3.2 said factory in `_category_factories.py` taking `(chat_client, user_layer)`; the self-contained handler-resident form is the thinner real shape — recorded here (NOT silently editing plan §Technical Spec; this Day-0 finding refines §3.1/§3.2 + §4 file #1 destination). |

**Prong 3 — schema verify** ✅ N/A — no new table / migration. `MemoryUser.source` column pre-exists (D-write-source) → `write(source=)` is additive write only, NO DDL.

**D-baselines** (re-verify full Day 4): pytest 2999 · wire 26 · Vitest 922 · mockup 51 · mypy 0/392 · run_all 11/11.

**Go/no-go**: scope-shift ~0% (D-handler-return refines the factory's location/signature but the change-set + behavior are unchanged). **GO.**

### Branch
✅ `git checkout -b feature/sprint-57-149-memory-auto-extract` (from `main` `694e0062`).

---

## Day 1-2 — 2026-06-28 — Wiring core + dedup + env gate + source tag + tests

### Code (7 src files, backend-only, NO migration / wire / frontend / loop.py)
- `agent_harness/memory/layers/user_layer.py` — `write()` additive `source: str | None` → real `memory_user.source` column (D-write-source: column pre-existed → no migration).
- `agent_harness/memory/extraction.py` — `extract_session_to_user(known_facts=...)` → `_build_known_block` prompt-level dedup ("only NEW facts"; empty = 51.2 byte-identical) + `source="auto_extract"` on every write.
- `core/config/__init__.py` — `chat_memory_auto_extract: bool = True` (`CHAT_MEMORY_AUTO_EXTRACT`).
- `api/v1/chat/handler.py` — `ChatMemoryExtractContext` dataclass (extractor+retrieval+message_store) + `build_chat_memory_extractor(model_policy, db, session_id, tenant_id)` (cheap tier; SOFT-None on missing env/db/session/tenant; self-contained per D-handler-return → 0 caller breakage).
- `api/v1/chat/router.py` — `_maybe_auto_extract` module helper (gate + profile() dedup + best-effort swallow) + a post-`natural_completion` call in `_stream_loop_events` + ctx build (gated real_llm + flag) + thread through.

### Tests (+14)
- `test_extraction.py` +5 (source tag / `_build_known_block` empty+listed / known_facts reach prompt / no-dedup-block-without-known).
- `test_extraction_worker.py` +1 (known_facts integration) + source assert + stub `source` param.
- `test_handler.py` +3 (factory none-without-env SOFT / none-without-db-session-tenant / cheap-tier context).
- `test_memory_auto_extract.py` **NEW** +5 (ctx-None noop / no-user noop / empty-ledger noop / runs-with-ledger+known-facts / swallows-extractor-failure).
- `test_tenant_isolation.py` stub +`source` param (no new test; isolation test still green).

### Design refinements during code (NOT silent plan edits — logged here)
- **D-handler-return resolved**: `build_chat_memory_extractor` is self-contained (rebuilds the cheap profile object, NO API call) instead of a `build_handler` tuple → 0 of the ~12 callers touched.
- **Helper extraction**: the inline hook → `_maybe_auto_extract` so gate + best-effort body are unit-testable WITHOUT driving the SSE generator.
- **2 test stubs needed the additive `source` param** (`_RecordingLayer`, `_TenantStubLayer`) — MemoryExtractor now passes `source=`; the memory suite caught this before full pytest.

### Gate (Day 2.4 full)
- mypy `src` **0/392** ✓ (no new src file → count unchanged).
- v2 lints **25 passed** (incl. `llm_sdk_leak` — extraction stays on the ChatClient ABC, provider-neutral).
- pytest **3013 passed / 6 skipped** (2999 → +14, NO regression; 137s).
- black/isort/flake8 clean (7 src + 5 test files).
- FE untouched (Vitest 922 / mockup 51).

---

## Day 3 — 2026-06-28 — Drive-through (real chat-v2 + real Azure gpt-5.2) — ALL 3 LEGS PASS

### Clean restart (Risk Class E)
Killed stale main backend (reloader 46684 + worker 30056), port 8000 free + 0 python orphans (node frontend + claude-code untouched), fresh no-reload uvicorn on branch code (`CHAT_MEMORY_AUTO_EXTRACT` default ON). Health 200, startup log clean. Frontend vite on **3007** (3005 taken).

### Leg 1 — Formation (dan@acme.com, user_id `cf2b40a1…`, baseline 3 rows all `source=none`)
Sent a NEW durable fact ("我接手了一個叫 Project Aurora 的資料庫遷移專案…Oracle…PostgreSQL…第三季上線" + a question). trace `5b04311d…`. After the loop completed (2× gpt-5.2 action + 2× **gpt-5.4-mini cheap** = verification judge + **extractor**), DB → **`[auto_extract]` conf=0.99 'Chris is currently handling Project Aurora, a database migration from Oracle to PostgreSQL'** @ 13:10:26. (The agent ALSO nudge-wrote a `source=none` Aurora row @ 13:10:10 — 57.148 Option-A fired too — but the `auto_extract` row proves the extractor ran deterministically + independently.)

### Leg 2 — Recall (NEW session, same dan, 0-keyword-overlap question "你還記得關於我…工作嗎？")
trace `567722ab…` (memory reads trace `9ff1b25f…`). Agent answer: **"你叫 Chris…你最近在忙的重點是 Project Aurora：把舊的 Oracle 資料庫…遷移到 PostgreSQL，目標是第三季（Q3）上線。"** Inspector Memory tab shows `profile()` read the **extractor row** `memory_user:5d487f86 = "Chris is currently handling Project Aurora…"` → end-to-end: extractor wrote → always-on `profile()` inject pulled it → agent recalled. (Notable: the in-loop verification judge REJECTed "invents details" because the judge sees only the trace, NOT the injected memory — a 57.98×57.148 interaction, NOT this sprint's bug; the agent still recalled correctly.)

### Leg 3 — Isolation (priya@acme.com, user_id `dc921d38…`, different user)
Same identity/project question → **"我不知道你是誰、也不知道你手上正在忙什麼專案…你還沒有提供任何…資訊。"** verification judge Score 0.99 (honest answer). 0 leak of dan's Aurora memory — per-user `WHERE user_id` scoping holds.

### Day-3 design evolution: synchronous-in-generator → Starlette `BackgroundTask`
The synchronous-in-`_stream_loop_events` version (Day 1-2) PASSED all 3 legs, but the drive-through surfaced two things:
1. **The post-loop extraction await blocked the SSE connection-close** (~1-2s, as the plan predicted) AND coincided with `async generator ignored GeneratorExit` + OTel `Failed to detach context` ERROR logs on every chat.
2. **Investigated the noise → it is PRE-EXISTING, NOT the extraction**: the traceback points to `agent_harness/observability/tracer.py:200 _span_cm` (the OTel span context-manager) + an anonymous `<async_generator_athrow>` — the 57.71/57.142 OTel-on-SSE-close known issue. Confirmed by re-running on the BackgroundTask version: the 2 GeneratorExit + 2 OTel-detach lines remain (so the extraction was never their cause; my initial hypothesis was wrong).
3. **Still moved to `BackgroundTask`** — the plan's "synchronous over background" rationale feared a fire-and-forget `asyncio.create_task` orphan (57.97/57.143 trap). But Starlette `BackgroundTask` is NOT an orphan — it runs after the response body in Starlette's own managed lifecycle. So it's the strictly-better choice: extraction no longer blocks the connection close, and the streaming generator is free of a post-loop blocking await. The extractor/retrieval/message_store all open their OWN sessions, so the request `db` teardown doesn't affect it.

**Re-drive (priya, BackgroundTask version)**: sent a durable fact ("我是公司的法遵主管…準備 SOC 2 Type II 稽核"). DB (baseline 0) → **`[auto_extract]` conf=0.78** SOC 2 row @ 13:26:38 (the BackgroundTask ran AFTER the response, 26s after the nudge row) + an agent nudge row @ 13:26:12. Confirms the BackgroundTask extractor writes correctly + per-user isolation (priya `dc921d38` ≠ dan `cf2b40a1`).

### Day-3 finding (NOT a blocker; logged for closeout)
- The in-loop verification judge (57.98) reports a **false-positive REJECT on memory-injected facts** — it judges against the conversation trace only and cannot see the `profile()`-injected memory, so a correct identity recall reads as "invents details". The agent still recalled correctly (the memory is genuinely in the prompt). Carryover: `AD-Verification-Judge-Memory-Inject-Blind`.

### Screenshots → artifacts/
`sprint-57-149-{s1-formation, s1b-memory-tab, s2-recall, s3-isolation-priya}.png` + `s2-recall-snapshot.md` / `s3-isolation-snapshot.md` moved to `sprint-57-149/artifacts/`.

### Post-BackgroundTask gate (Day 3 re-verify)
- mypy `src` **0/392** · v2 lints **25** · full pytest **3013 passed / 6 skipped** (BackgroundTask change; audit_log_observer's 2 subset-isolation failures are a PRE-EXISTING `integration/api/conftest.py:84 setdefault(MAIN_TRANSCRIPT_OBSERVER, false)` leak, GREEN in full run + with env set — NOT this change). black/isort/flake8 clean.

---
