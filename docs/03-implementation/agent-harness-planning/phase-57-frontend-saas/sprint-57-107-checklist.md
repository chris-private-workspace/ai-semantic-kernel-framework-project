# Sprint 57.107 — Checklist (B3 HANDOFF finish: stub retirement + spec-only `handoff` tool + per-tenant handoff governance + `GET /sessions` lineage + chat-v2 SessionList real-data + sidechain transcript persistence → real-LLM handoff drive-through)

[Plan](./sprint-57-107-plan.md)

---

## Day 0 — Plan-vs-Repo Verify + Branch ✅

### 0.1 Three-prong Day-0 verify (against `main` HEAD `b6b2c392`) — DONE, catalogued in progress.md D1-D11
- [x] **Prong 1 — path verify**: DELETE target `modes/handoff.py` Glob-1; NEW files Glob-0 (migration 0028 / `make_handoff_spec` does not pre-exist / FE service additions); EDIT files Glob-1 (dispatcher / _abc / tools / _register_all / harness_policy / service / handler / router / tenants / sessions.py / models/sessions.py / repo / SessionList / HarnessPolicyTab); test suites pinned (convert targets `test_handoff.py` + `test_subagent_tools.py:96-131`; integration naming precedent for sessions-list + observer suites)
- [x] **Prong 2 — content verify**: ALL plan §0 STALE anchors — `_abc.py` `handoff()` ABC signature + ALL `SubagentDispatcher` implementers (grep subclass); `SubagentMode.HANDOFF` consumers; **`SubagentSpawned`/`SubagentChildEvent`/`SubagentCompleted` dataclass BODY read** (subagent_id/mode/task fields — nested-shape rule); `_stream_loop_events` closure scope (resolved `harness_policy` reachable at the :661 hook?); `make_default_executor` signature + chat-handler invocation point; sessions-observer SAVEPOINT pattern :313-339; classifier :47/:68 + loop :2656-2682 unchanged; `boot_handoff` signature :93-197; FE `chatStore` sessions state shape + `SessionList.tsx` fixture wiring
- [x] **Prong 2.5 — FE tree audit** (HarnessPolicyTab LIST_FIELDS shape ✓; SessionList depth-2 re-checked at Day 3 code time): `SessionList.tsx` child-component imports (depth-2 grep: shadcn residue / inline-style escapes / fullBleed) + `HarnessPolicyTab` LIST_FIELDS shape for +2 fields
- [x] **Prong 3 — schema verify** (D1 head 0028 free; D4 🔴 partitions only to 2026_06 → 0028 adds DEFAULT partitions): migration head (`ls versions/ | sort -V | tail -3` — 0028 free?); `sessions` table current columns (no `parent_session_id`/`is_sidechain` collision); **`message_events` partition strategy** (monthly partitions — who creates them / does the current month exist? INSERT path viability); RLS posture on sessions/message_events (TenantScopedMixin)
- [x] **Catalog drift** findings in progress.md Day 0 (D1-D11 + implications; plan §8 cross-ref)
- [x] **Go/no-go**: GO — scope shift 微小 (D4 +2 migration statements; D5/D8/D10 parameter-level)

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-107-handoff-finish` (from `main` `b6b2c392`)

---

## Day 1 — Backend core: stub retirement + spec-only tool + governance fields (US-1 / US-2) ✅

### 1.1 Stub retirement (US-1)
- [x] **DELETE `modes/handoff.py`**; EDIT `dispatcher.py` (drop import :83 / instantiate :155 / `handoff()` :315-332), `_abc.py` (drop `handoff()` ABC), `subagent/__init__.py` + `modes/__init__.py` (drop re-exports); `SubagentMode.HANDOFF` enum KEPT, `spawn()` raise comment re-pointed at the classifier path
  - DoD: grep `HandoffExecutor|dispatcher\.handoff|make_handoff_tool` → 0 hits in `backend/src` ✓; mypy strict 0/358 ✓; `check_cross_category_import` green ✓
- [x] **17.md**: `SubagentDispatcher` contract row updated (handoff() removed; HANDOFF = classifier + platform path) + §3.1 `handoff` tool row (spec-only + policy gate)

### 1.2 Spec-only `handoff` tool (US-1)
- [x] **`tools.py`**: `make_handoff_tool` → `make_handoff_spec(suggested_targets: Sequence[str]) -> tuple[ToolSpec, handler]`; description enumerates targets + when-to-use; args `{target_agent: str (required), reason: str}`; handler raises `RuntimeError("handoff is loop-intercepted")` (AP-4 negative guard)
- [x] **`_register_all.py`**: `make_default_executor(handoff_targets: Sequence[str] | None = None)` opt-in branch (mirror `subagent_dispatcher`); registers the spec when not None
- [x] **`handler.py`**: thread `handoff_targets = policy.handoff_target_allowlist or DEFAULT_AGENTS keys` when `policy.handoff_enabled is not False`; else None (tool absent); `policy` resolution hoisted above the executor build
  - DoD: NO-policy tenant → tool REGISTERED with 3 default targets ✓; `handoff_enabled=false` → absent ✓; no hot-path DB added ✓

### 1.3 Governance fields + boot enforcement (US-2)
- [x] **`harness_policy.py`**: +`handoff_enabled: bool | None` + `handoff_target_allowlist: tuple[str, ...] | None` (9→11 sparse fields; tri-state semantics preserved; `from_dict` wrong-type → not-set)
- [x] **`service.py`**: `boot_handoff(*, allowed_targets: Sequence[str] | None = None)` — post-persona-resolve reject off-list target → `HandoffError("not allowed by tenant policy")` (router fail-soft + audit path unchanged)
- [x] **`router.py`**: thread `handoff_allowed_targets` param into module-level `_stream_loop_events` (D8) + pass into the boot hook
- [x] **Unit tests**: spec-shape + defensive-raise + registration gating ×2 · policy 2-field round-trip/tri-state ×2 · `boot_handoff` allowlist accept/reject/None ×3 · CONVERTED `test_handoff.py` (4 tests) + `test_subagent_tools.py` handoff block (3 tests) + `test_dispatcher_init.py` raise-match (0 deletions — Never-Delete)
  - DoD: full unit suite **1734 passed** ✓; flake8 0 ✓; run_all 10/10 (event count UNCHANGED) ✓

---

## Day 2 — Sessions list + sidechain transcript (US-3 backend / US-4) ✅

### 2.1 Sessions list API (US-3 backend)
- [x] **Repo**: `SessionRepository.list_sessions(tenant_id, *, limit=50)` — top-level only (`is_sidechain=false`), `started_at DESC`; `create_session` +`parent_session_id`/`is_sidechain` kwargs
- [x] **`api/v1/sessions.py`**: `GET /api/v1/sessions` → `SessionListItem{id, title, status, agent_role, handoff_parent_id, started_at_ms, total_turns}`; `get_current_tenant` + RLS pattern per existing endpoint
- [x] **Integration tests**: `test_sessions_list.py` (4: newest-first+lineage / sidechain-excluded / isolation 鐵律 / empty-200)
  - DoD: suite green ✓; mypy 0/359 ✓

### 2.2 Sidechain migration + observer (US-4)
- [x] **Migration 0028** `0028_sidechain_sessions`: 2 columns + partial index + **DEFAULT partitions for messages + message_events (D4 time-bomb fix — tables were un-writable from 2026-07-01)**; `models/sessions.py` 2 columns + MHist; `alembic upgrade head` clean ✓
- [x] **Router observer** `_persist_subagent_transcript` (best-effort SAVEPOINT, both drain sites): `SubagentSpawned` → sidechain session (title `Subagent · {mode}` per D5 — event has no task field); `SubagentChildEvent` → `message_events` INSERT (serializer payload, monotonic per-sidechain seq); `SubagentCompleted` → completed + summary/tokens meta_data; env-gate `SUBAGENT_TRANSCRIPT_OBSERVER` (conftest false — D7)
- [x] **Admin validation (US-2 rest)**: `tenants.py` 2 fields + 422 poles (empty allowlist / >20 / >100 chars) + audit + invalidate (existing op name)
- [x] **Integration tests**: `test_subagent_transcript_observer.py` (3: full transcript round-trip / env-gated-off / cross-tenant isolation) + `test_chat_handoff.py` +2 (off-list fail-soft no-child + allowlisted boots) + admin +4 poles
  - DoD: alembic clean ✓; **full pytest 2460+4skip (+21, 0 del)** ✓; run_all 10/10 ✓; flake8 0 ✓

---

## Day 3 — FE (US-3 FE / US-2 tab) + full gates + drive-through (US-5) + CHANGE-074 + note 29

### 3.1 FE SessionList real-data + 鏈 (US-3) ✅
- [x] **`chatService.listSessions()`** + chatStore `loadSessions` + `SessionList.tsx` real render (FIXTURE_SESSIONS + DEMO banner removed; `fixtures/sessions.ts` deleted; Vitest mocks the store/service); `types.ts` Session += `handoffParentId`/`agentRole` (− `domain`, no backend source); child rows `↳ {agentRole}` `.route-pill` badge; ChatHeader rewired (fixture-deletion forced)
- [x] **`HarnessPolicyTab.tsx`**: +1 tri-state select (`handoffEnabled`) + 1 list field (`handoffTargetAllowlist`) + service mappers (9→11)
- [x] **FE Vitest**: SessionList real-data/empty/鏈-badge + tab 2 new fields (828/828, 137 files)
  - DoD: lint 0 (non-silent) ✓ · build ✓ · Vitest green ✓ · mockup-fidelity ✓ — **baseline RATCHETED 53→51** (banner removal −2; agent-delegated, parent re-verified all 4 gates)

### 3.2 Full gate sweep ✅
- [x] mypy strict 0/359 · run_all 10/10 (event count UNCHANGED) · full pytest 2460+4skip (0 del) · FE 4 gates · `loop.py`/wire-schema diff = 0

### 3.3 Drive-through (US-5 — real UI + real backend + real Azure; clean no-reload restart per Risk Class E) ✅ ALL LEGS PASS
- [x] **Handoff e2e**: **FIRST EVER real-LLM handoff** — gpt-5.2 called the spec-only tool → `loop_end stop=handoff` → `agent_handoff` (child `eab49331…`) → HandoffBanner「已交棒給 reviewer」→ sessions list parent (not running) + child ↳ badge
- [x] **Allowlist negative**: policy `["planner"]` → the spec-description FIRST layer steered the real LLM to planner (never attempted off-list reviewer); boot-time rejection proven by integration test; `handoff_enabled=false` → tool absent → same ask `end_turn` normally (LLM fell back to task_spawn)
- [x] **Sidechain**: teammate spawn → sidechain session `709ded76…` (completed + summary + 3993 tokens) + **message_events first-ever 6 rows (seq 1-6)** — DB-probed
- [x] Screenshots (4, `artifacts/dt57107-*.png`) + observed-vs-intended in progress.md
  - DoD: ALL legs PASS ✓; policy cleared back to defaults (cache invalidation re-proven)

### 3.4 CHANGE-074 + docs ✅
- [x] `claudedocs/4-changes/feature-changes/CHANGE-074-handoff-finish-sidechain-transcripts.md` + design note `29-handoff-completion-sidechain-transcript-design.md` (spike extract, 8-point gate) + 17.md cross-refs (Day 1)

---

## Day 4 — Closeout

### 4.1 Closeout
- [ ] retrospective.md Q1-Q7 + calibration (`mixed-multidomain-bundle` 0.65 data point + agent-delegated tag) + progress.md final
- [ ] Navigators: CLAUDE.md Current-Sprint row + Last-Updated; MEMORY.md quality pointer + memory subfile; next-phase-candidates 57.107 carryover block (close `AD-ChatV2-SessionList-Backend` + `AD-Subagent-Transcript-Isolation`; NEW `AD-Sidechain-Transcript-Read-API` etc.); sprint-workflow matrix row
- [ ] PR (push + open on user authorization)
