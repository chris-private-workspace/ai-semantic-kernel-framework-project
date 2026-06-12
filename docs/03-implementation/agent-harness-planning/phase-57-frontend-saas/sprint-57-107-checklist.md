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

## Day 2 — Sessions list + sidechain transcript (US-3 backend / US-4)

### 2.1 Sessions list API (US-3 backend)
- [ ] **Repo**: `SessionRepository.list_sessions(tenant_id, *, limit=50)` — top-level only (`is_sidechain=false` post-2.2 migration), `started_at DESC`
- [ ] **`api/v1/sessions.py`**: `GET /api/v1/sessions` → `SessionListItem{id, title, status, created_at, agent_role, handoff_parent_id}`; `get_current_tenant` + RLS pattern per existing endpoint
- [ ] **Integration tests**: list round-trip + lineage fields + sidechain exclusion + tenant isolation 鐵律 (foreign tenant sees nothing)
  - DoD: suite green; OpenAPI renders; mypy 0

### 2.2 Sidechain migration + observer (US-4)
- [ ] **Migration 0028** (number per Prong-3): `sessions.parent_session_id UUID NULL FK sessions(id) ON DELETE SET NULL` + `sessions.is_sidechain BOOL NOT NULL DEFAULT false` + partial index; `models/sessions.py` 2 columns + MHist
- [ ] **Router observer** (mirror :313-339 best-effort SAVEPOINT): `SubagentSpawned` → INSERT sidechain session (id=subagent_id, tenant/user inherited, title from task, meta_data mode/agent); `SubagentChildEvent` → INSERT `message_events` (event_type=inner type, serialized inner, monotonic sequence_num); `SubagentCompleted` → status=completed + summary/tokens meta_data
- [ ] **Admin validation (US-2 rest)**: `tenants.py` 2 fields + 422 poles (empty allowlist → 422 / >20 entries / >100 chars / non-str) + audit + invalidate (existing op name)
- [ ] **Integration tests**: fake loop emits Spawned/Child×N/Completed → sidechain session row + N `message_events` rows + isolation; allowlist-reject e2e (extend `test_chat_handoff.py`); admin PUT poles
  - DoD: alembic upgrade head clean; full pytest 0 del; run_all 10/10; RLS lint green

---

## Day 3 — FE (US-3 FE / US-2 tab) + full gates + drive-through (US-5) + CHANGE-074 + note 29

### 3.1 FE SessionList real-data + 鏈 (US-3)
- [ ] **`sessionsService.listSessions()`** + chatStore `loadSessions` + `SessionList.tsx` real render (FIXTURE_SESSIONS + DEMO banner removed; `fixtures/sessions.ts` deleted; Vitest mocks the service); `types.ts` Session += `handoffParentId`/`agentRole`; child rows `↳ <parent short-ref>` badge
- [ ] **`HarnessPolicyTab.tsx`**: +1 tri-state select (`handoffEnabled`) + 1 list field (`handoffTargetAllowlist`) + service mappers
- [ ] **FE Vitest**: SessionList real-data/empty/鏈-badge + tab 2 new fields
  - DoD: lint 0 (non-silent) · build 0 · Vitest green · mockup-fidelity 53

### 3.2 Full gate sweep
- [ ] mypy strict 0 · run_all 10/10 (event count UNCHANGED) · full pytest 0 del · FE 4 gates · `loop.py`/wire-schema diff = 0

### 3.3 Drive-through (US-5 — real UI + real backend + real Azure; clean no-reload restart per Risk Class E)
- [ ] **Handoff e2e**: "hand this off to the reviewer agent" → handoff tool call → child session (`handoff_parent_id` set) → `AgentHandoff` SSE → FE pivot + banner → sessions list shows parent (handed_off) + child ↳ badge
- [ ] **Allowlist negative**: tenant policy `["planner"]` → handoff to "reviewer" rejected (no child + audit row); `handoff_enabled=false` → tool absent (LLM cannot call it)
- [ ] **Sidechain**: `task_spawn` run → sidechain session + `message_events` rows queryable (psql/API probe)
- [ ] Screenshots + observed-vs-intended into progress.md
  - DoD: ALL legs PASS or findings catalogued + fixed-to-usable

### 3.4 CHANGE-074 + docs
- [ ] `claudedocs/4-changes/feature-changes/CHANGE-074-*.md` + design note 29 (spike extract, 8-point gate) + 17.md cross-refs

---

## Day 4 — Closeout

### 4.1 Closeout
- [ ] retrospective.md Q1-Q7 + calibration (`mixed-multidomain-bundle` 0.65 data point + agent-delegated tag) + progress.md final
- [ ] Navigators: CLAUDE.md Current-Sprint row + Last-Updated; MEMORY.md quality pointer + memory subfile; next-phase-candidates 57.107 carryover block (close `AD-ChatV2-SessionList-Backend` + `AD-Subagent-Transcript-Isolation`; NEW `AD-Sidechain-Transcript-Read-API` etc.); sprint-workflow matrix row
- [ ] PR (push + open on user authorization)
