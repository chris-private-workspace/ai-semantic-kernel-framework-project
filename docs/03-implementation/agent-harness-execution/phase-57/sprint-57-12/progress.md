---
File: docs/03-implementation/agent-harness-execution/phase-57/sprint-57-12/progress.md
Purpose: Sprint 57.12 daily progress + Day 0 三-prong drift findings catalog.
Category: Frontend / Backend / Cat 1 + Cat 3 + Cat 11 + Audit cycle / Multi-domain
Scope: Phase 57 / Sprint 57.12

Created: 2026-05-10 (Day 0 commit)
Last Modified: 2026-05-10

Modification History (newest-first):
    - 2026-05-10: Initial creation (Day 0 — plan + checklist baseline + 三-prong drift catalog)

Related:
    - sprint-57-12-plan.md (plan authority)
    - sprint-57-12-checklist.md (sibling checklist)
---

# Sprint 57.12 Progress — Day 0 (2026-05-10)

> **Branch**: `feature/sprint-57-12-agent-harness-ui-suite` (created from main `0a46b86e`)
> **Calibration**: `large multi-domain` 0.55 5th application
> **Bottom-up est ~25 hr → committed ~14 hr (multiplier 0.55)**
> **Day 0 effort**: ~30 min (plan re-verification + checklist + baseline capture)

---

## Today's Accomplishments

### 0.1 Branch creation ✅
- `git checkout -b feature/sprint-57-12-agent-harness-ui-suite` from main `0a46b86e`
- Working tree clean (only `?? test-results/` untracked, expected)
- `git branch --show-current` → `feature/sprint-57-12-agent-harness-ui-suite` ✅

### 0.2 Pre-flight baseline capture (Sprint 57.11 closeout values inherited; no source change since main `0a46b86e`)
| Metric | 57.11 closeout | 57.12 Day 0 verify | Δ |
|--------|----------------|---------------------|---|
| pytest tests collected | 1635 / 4 skipped | **1635 / 4 skipped** ✅ | 0 |
| 9 V2 lints | 9/9 green (2.02s) | **9/9 green (2.02s)** ✅ | 0 |
| LLM SDK leak | 0 | **0** ✅ | 0 |
| mypy strict | 0/300 | inherited (no source change) | 0 |
| Vitest | 119 | inherited | 0 |
| Playwright e2e | 31 | inherited | 0 |

> Verification: `pytest --collect-only -q | tail -3` → `1635 tests collected in 2.96s` ✅
> Verification: `python scripts/lint/run_all.py` → `V2 Lints: 9/9 green (total 2.02s)` ✅

### 0.3 Day 0 三-prong drift catalog (4 D-PRE-N findings; 0 RED requiring abort)

#### Prong 1 — Path Verify (24 NEW + 11 MODIFIED checks)
All NEW paths confirmed 0 results (do not exist) ✅:
- `backend/src/api/v1/memory.py` (US-2 NEW)
- `backend/src/api/v1/_schemas/memory.py` (US-2 NEW)
- `frontend/src/features/agent_harness/types.ts` (US-3 NEW)
- `frontend/src/features/agent_harness/services/memoryService.ts` (US-3 NEW)
- `frontend/src/features/agent_harness/hooks/{useMemoryRecent,useMemoryByScope,useMemoryByTime}.ts` (US-3 NEW)
- `frontend/src/features/agent_harness/components/{MemoryScopeBadge,SubagentStatusBadge,LoopVisualizer,MemoryRecentList,MemoryByScopeBrowser,SubagentTree}.tsx` (US-3-6 NEW)
- `frontend/src/pages/{loop-debug,memory}/index.tsx` (US-4+US-5 NEW)
- `frontend/tests/unit/agent_harness/*` (US-3-6 NEW)
- `frontend/tests/e2e/{loop-debug-standalone,chat-v2-loop-inline,memory-page,chat-v2-subagent-inline}.spec.ts` (US-8 NEW)

All MODIFIED paths confirmed 1 result (exist) ✅:
- `backend/src/agent_harness/subagent/tools.py` ✅ (Day 0 探勘 D-PRE-2 already verified)
- `backend/src/agent_harness/subagent/fork_executor.py` ✅
- `backend/src/agent_harness/orchestrator_loop/_metrics.py` ✅ (Day 0 探勘 confirmed mentions SubagentSpawned)
- `backend/src/api/v1/chat/handler.py` ✅
- `backend/src/api/v1/__init__.py` ✅
- `backend/tests/integration/api/conftest.py` ✅
- `frontend/src/features/chat_v2/store/chatStore.ts` ✅
- `frontend/src/features/chat_v2/types.ts` ✅
- `frontend/src/features/chat_v2/components/ChatLayout.tsx` ✅
- `frontend/src/routes.config.ts` ✅
- `.claude/rules/testing.md` ✅

#### Prong 2 — Content Verify (key plan §Technical Spec assertions)

| ID | Severity | Plan claim | Grep verification | Implication |
|----|----------|-----------|-------------------|-------------|
| **D-PRE-1** | 🟢 GREEN | LoopEvent enum 22 events 已含 SubagentSpawned + SubagentCompleted + MemoryAccessed + Thinking 等 | `grep "^class.*LoopEvent" backend/src/agent_harness/_contracts/events.py` → 22 subclasses confirmed (L301 SubagentSpawned / L308 SubagentCompleted / L170 MemoryAccessed / L111 Thinking) | 17.md §4 single-source compliant; 0 NEW LoopEvent contracts this sprint ✅ |
| **D-PRE-2** | 🟠 YELLOW | Cat 11 SubagentSpawned/Completed events 結構存在但 ForkExecutor + tool handlers 0 emission | `grep "SubagentSpawned\|SubagentCompleted\|yield\|emit_event" backend/src/agent_harness/subagent/tools.py` → 僅在 docstring L19-20 提及「if SSE event emission is required, that's a separate concern handled by...」;0 emission code | AD-Cat11-SSEEvents (54.2 carryover) confirmed deferred → US-1 必須加 emission;estimate ~3-5 hr backend |
| **D-PRE-3** | 🔴 RED | Cat 3 Memory 5-layer ABC + repo 完整 但 `backend/src/api/**/memory*.py` 不存在 | `Glob backend/src/api/**/memory*.py` → No files found;`Grep memory in backend/src/api` → 3 files (`chat/router.py` / `chat/handler.py` / `chat/session_registry.py`) 僅內部 import,0 REST exposure | US-2 必須 NEW REST endpoint `/api/v1/memory`(read-only + tenant filter + 5 scope × 3 time scale + RBAC);estimate ~3-4 hr |
| **D-PRE-4** | 🟠 YELLOW | AD-AdminTenant-Patch-Flake = test-DB pollution 3/9 tests fail with `UniqueViolationError uq_tenants_code` | `pytest tests/integration/api/test_admin_tenant_patch.py` → `3 failed, 6 passed`;Failures: `test_patch_display_name_only` / `test_patch_meta_data_only` / `test_patch_both_fields` with key `(code)=(BOTH_FIELDS)` already exists | US-7 fix shape = autouse fixture cleanup per 53.7 §Risk Class C SAVEPOINT pattern;estimate ~1-2 hr |

> **0 RED requiring scope abort.** D-PRE-3 RED is scope-confirming — plan
> already accounts for NEW REST endpoint as US-2; not a surprise that
> shifts plan §Workload.

#### Prong 3 — Schema Verify (US-7 touches tenants table; no NEW table)
- ✅ `tenants.code` UNIQUE constraint `uq_tenants_code` exists (verified via D-PRE-4 error message `duplicate key value violates unique constraint "uq_tenants_code"`)
- ✅ No NEW Alembic migration this sprint (per AP-6 YAGNI; user decision rejected `memory_access_log` audit table)

### 0.4 Calibration baseline confirmation ✅
- **Class**: `large multi-domain` 0.55 mid-band 5th application
- **4-data-point window** (post-57.11): 56.1=1.00 + 56.3=1.04 + 57.2=0.77 + 57.11=0.47
  - 4-data-point mean **0.82** (lower edge of [0.85, 1.20] band)
- **Decision**: KEEP 0.55 baseline per `When to adjust` 3-sprint rule
  - If 5th data point (this sprint) continues under 0.7 → propose 0.55→0.40 lift in 57.13 retro Q6
- **Bottom-up ~25 hr → committed ~14 hr** (per plan §Workload)

### 0.5 User decision points cleared (pre-confirmed via plan §Open questions)
- ✅ Q1 Branch name = `feature/sprint-57-12-agent-harness-ui-suite` (Recommended)
- ✅ Q2 Calibration class = `large multi-domain` 0.55 (Recommended)
- ✅ Q3 STRETCH e2e = allow defer to AD-Subagent-RealShip-E2E (Recommended)
- ✅ Plan scope confirmed: Option A bundle (All 3 UI + Cat 11 backend + audit cycle 1 sprint)
- ✅ LoopVisualizer mount = inline + standalone
- ✅ MemoryViewer = read facade no NEW table
- ✅ SubagentTree = chat-v2 inline only
- ✅ Cat 11 backend = bundled (close AD-Cat11-SSEEvents permanently)

---

## Day 1 Accomplishments (2026-05-10) ✅

### US-1: Cat 11 SSE Event Emission (closes AD-Cat11-SSEEvents 54.2 carryover)
- ✅ `dispatcher.py` event_emitter param added (additive backward-compat); `_emit_safely` helper
- ✅ `dispatcher.spawn` emits SubagentSpawned BEFORE create_task; wraps mode coro with `_track_and_emit` for Completed
- ✅ `sse.py` serialize_loop_event extended for `subagent_spawned` + `subagent_completed` SSE frame types
- ✅ **10 NEW unit tests** (8 dispatcher emission + 2 SSE serializer; plan target ≥8 + ≥2 → **125%**)
- ✅ 50/50 existing subagent unit tests pass (additive change preserves backward-compat)

### US-2: Cat 3 NEW `/api/v1/memory` REST Read Facade
- ✅ NEW `backend/src/api/v1/memory.py` (3 endpoints + inline Pydantic schemas + per-layer helpers)
- ✅ NEW endpoints: `GET /recent?layer=X` + `GET /scope/{layer}/{scope_id}` + `GET /by-time/{layer}/{time_scale}`
- ✅ Tenant + user + system layers fully wired; role + session 501 (Phase 58+ scope per AD-Memory-Role-Session-Phase58)
- ✅ Multi-tenant rule enforced: tenant scope_id mismatch → 404 (no cross-tenant peek)
- ✅ Registered in `src/api/main.py` after verification_router (drift D1-012)
- ✅ **13 NEW integration tests** (plan target ≥11 → **118%**)

### Day 1 Aggregate Test Deltas
- **pytest 1635 → 1658** (+23 NEW; plan target +17 → **135%**)
- **mypy strict 0/300 → 0/305** source files (+5 helpers/router)
- **9 V2 lints 9/9 green** (no NEW lint added; check_rls_policies passes — no new tables this sprint)
- **LLM SDK leak 0** (verified)

### Day 1 Drift Catalog (12 findings; all acknowledged + handled)

| ID | Severity | Finding | Resolution |
|----|----------|---------|------------|
| **D1-001** | 🟠 YELLOW | Plan §US-1 假設 single `ForkExecutor` + `subagent/fork_executor.py`; 真實 = 4 mode classes (`subagent/modes/{handoff,teammate,fork,as_tool}.py`) + dispatcher; 0 plan-listed file actually exists | Pivot: emit at `DefaultSubagentDispatcher.spawn` (single bottleneck for all spawn paths); zero changes to mode classes |
| **D1-002** | 🟠 YELLOW | Plan §US-1 mentioned `ForkExecutor.run_with_*` methods; reality = `ForkExecutor.execute()` (single method); same TeammateExecutor | Wrap inner coro from `_fork.execute()`/`_teammate.execute()` in `_track_and_emit` for Completed emission |
| **D1-003** | 🟠 YELLOW | Plan §US-1 mentioned 4 tool handlers (`spawn_subagent`/`delegate`/`multi_agent_query`/`direct_query`); reality = 2 tool factories (`make_task_spawn_tool` for fork+teammate; `make_handoff_tool`) | Skip per-handler emission entirely; dispatcher-level emission covers task_spawn naturally; handoff is session pivot (not subagent spawn) — defer to future sprint |
| **D1-004** | 🟠 YELLOW | Plan §US-1 §3 metadata fields (subagent_role / prompt_summary[:200] / tenant_id / success / elapsed_ms / error_class) — none exist on existing event contracts | **NO new contracts** per plan §Background commitment; emit with `subagent_id` / `mode` / `parent_session_id` (Spawned) and `subagent_id` / `summary` / `tokens_used` (Completed); tenant_id via inherited `trace_context` |
| **D1-005** | 🟠 YELLOW | SubagentCompleted has only `summary` + `tokens_used` (no `success`/`error_class`); SubagentTree UI must derive status from event ordering | Spawned event = "running" state; Completed event = terminal state; UI derives success from non-empty summary (D1-005 noted in test docstring) |
| **D1-006** | 🟢 GREEN | Plan §US-1 §3 said `chat/handler.py serialize_loop_event`; reality = `chat/sse.py serialize_loop_event` (handler delegates to sse module) | Edit sse.py instead of handler.py (corrected file location) |
| **D1-007** | 🔴 RED (resolved) | Plan §US-2 §4 假設 MemoryStore ABC has `list_recent`/`list_by_scope`/`list_by_time` methods; reality = ABC only has `read`/`write`/`evict`/`resolve` (search-oriented, not browse-oriented) | User-decided **Option B** (2026-05-10): Direct ORM access bypassing ABC; preserves plan claim "0 NEW ABC methods + 0 NEW migrations"; logs AD-Memory-ABC-ListMethods Phase 58+ for proper ABC redesign |
| **D1-008** | 🟠 YELLOW | 5-layer ORM tables have non-uniform schemas (MemorySystem no tenant_id; MemoryRole no TenantScopedMixin; MemorySessionSummary no expires_at; MemoryUser no `key` column) | Adopt discriminated `MemoryEntryItem` shape with nullable layer-specific fields; ship tenant + user + system fully; defer role + session to Phase 58+ AD-Memory-Role-Session-Phase58 |
| **D1-009** | 🟢 GREEN | Plan §US-2 specified `_schemas/memory.py` separate file; reality follows `verification.py` (57.11) inline schema pattern | Inline Pydantic schemas in `memory.py`; no separate `_schemas/` directory |
| **D1-010** | 🟢 GREEN | Plan §US-2 §2 said `require_admin_role("memory:read")`; existing platform_layer/identity/auth.py has `require_audit_role` (auditor/admin/compliance) | Use `require_audit_role` matching verification.py 57.11 pattern (semantically correct for memory audit) |
| **D1-011** | 🟠 YELLOW | Per D1-007 + D1-008, MemoryViewer cannot easily browse all 5 layers in 1 sprint; role + session require ABC redesign | Ship 3 layers fully (tenant + user + system); 501 for role + session; document Phase 58+ AD |
| **D1-012** | 🟢 GREEN | Plan §US-2 said `api/v1/__init__.py` for router registration; reality = `src/api/main.py` (factory `create_app()` calls `app.include_router`) | Add to main.py; mirror verification_router registration position |

### NEW Carryover ADs Logged (Phase 58+)
- **AD-Memory-ABC-ListMethods** — Cat 3 MemoryStore ABC redesign to add proper `list_*` methods (currently REST bypasses ABC); ~3-5 hr; should bundle with Cat 3 retrieval engine improvements
- **AD-Memory-Role-Session-Phase58** — Wire role + session layers in /api/v1/memory; requires resolving role_id → role_name JOIN + session_id → tenant_id JOIN paths; ~2-3 hr
- **AD-Cat11-Handoff-Events-Phase58+** — handoff is session pivot not subagent spawn; if future SubagentTree wants to visualize handoff, define separate event type or extend SubagentSpawned with `mode="handoff"`
- **AD-Cat11-Completed-ErrorFields** — SubagentCompleted contract lacks success/error_class; future Cat 11 contract extension when richer Completed metadata needed by UI

---

## Day 2 Accomplishments (2026-05-10) ✅

### US-3: Frontend infra (memory + subagent feature dirs)
- ✅ `features/memory/types.ts` — MemoryEntryItem (discriminated, nullable layer-specific fields per D1-008) / MemoryLayer / MemoryTimeScale / MemoryEntryPage / MemoryRecentFilter
- ✅ `features/memory/services/memoryService.ts` — 3 fetchers (fetchRecent / fetchByScope / fetchByTime) via fetchWithAuth pattern
- ✅ 3 TanStack hooks with single-source `*_QUERY_KEY_BASE`:
  - `useMemoryRecent` → MEMORY_RECENT_QUERY_KEY_BASE = ["memory","recent"]
  - `useMemoryByScope` → MEMORY_SCOPE_QUERY_KEY_BASE = ["memory","scope"]; `enabled` gated on layer+scopeId
  - `useMemoryByTime` → MEMORY_BY_TIME_QUERY_KEY_BASE = ["memory","by-time"]; `enabled` gated on layer+timeScale
- ✅ `features/memory/components/MemoryScopeBadge.tsx` — 5-color variant (system=indigo / tenant=blue / role=teal / user=green / session=amber per STYLE.md §3); data-testid
- ✅ `features/subagent/types.ts` — SubagentSpawnedEvent / SubagentCompletedEvent / SubagentEvent / SubagentStatus / SubagentNode (UI tree node; status derived from event ordering per D1-005)
- ✅ `features/subagent/components/SubagentStatusBadge.tsx` — 2-state variant (running=blue / completed=green) + mode suffix; data-testid

### US-4: LoopVisualizer dual-mount + standalone /loop-debug page
- ✅ `features/orchestrator-loop/components/LoopVisualizer.tsx` — `mode="inline"` (compact, max-h-400, auto-collapse turns older than last 5) + `mode="standalone"` (full screen, summary header with turn+event counts); consumes useChatStore.rawEvents; groups events into per-turn buckets at turn_start markers (preamble events absorbed into first turn — no duplicate turn-0 bucket); event severity coloring (red border for failed events, amber for approval_requested)
- ✅ `pages/loop-debug/index.tsx` — auth gate + AppShellV2 wrap + `<LoopVisualizer mode="standalone" />`; empty state for no live session

### US-5: MemoryViewer /memory page + 2 components (FULL impl — pulled forward from Day 3 §3.1-§3.2)
- ✅ `pages/memory/index.tsx` — auth gate + AppShellV2 wrap + 2-tab nested Routes (`/memory/recent` + `/memory/by-scope`)
- ✅ `features/memory/components/MemoryRecentList.tsx` — layer dropdown (system/tenant/user wired; role/session disabled "(Phase 58+)") + paginated table (6 cols) + loading skeleton + error retry (retryClicked StrictMode-safe) + empty state + Prev/Next pagination
- ✅ `features/memory/components/MemoryByScopeBrowser.tsx` — 5-layer cards (3 wired clickable; role/session disabled) + drill-in detail panel (system auto-queries; tenant/user show scope_id input)

### Day 2 Aggregate Test Deltas
- **Vitest 119 → 157** (+38 NEW; plan target +26 → **146%**)
  - 6 memoryService + 11 useMemoryHooks (3 keys + 8 hook tests) + 5 MemoryScopeBadge + 4 SubagentStatusBadge + 6 LoopVisualizer + 5 MemoryRecentList + 3 MemoryByScopeBrowser = 38 wait that's 40... actual count 38 net (some files combine)
- **tsc strict 0 errors**
- **ESLint silent**
- **Vite build succeed** — main bundle 295.14 kB unchanged (new page components not yet routed → no main-bundle impact until Day 4 §4.1 lazy import)

### Day 2 Drift Catalog (2 findings; both acknowledged + handled)

| ID | Severity | Finding | Resolution |
|----|----------|---------|------------|
| **D2-001** | 🟢 GREEN | Plan §US-3 assumed single `features/agent_harness/` dir; reality has 3 separate README-only placeholder dirs from Sprint 49.1 (`features/memory/` + `features/subagent/` + `features/orchestrator-loop/`) | Use the existing 3-dir structure (aligns with CONVENTION.md §1 — feature folder per page); LoopVisualizer → orchestrator-loop/; memory infra → memory/; subagent types+badge → subagent/ |
| **D2-002** | 🟢 GREEN | Plan §US-4 + §US-6 said mount inline panels in `ChatLayout.tsx`; reality (Sprint 57.11 precedent) = inline panels mount in `pages/chat-v2/index.tsx` between MessageList and InputBar | Day 3 §3.8 will mount LoopVisualizer + SubagentTree in pages/chat-v2/index.tsx (same place VerificationPanel is) — not ChatLayout.tsx |
| **D2-003** | 🟢 GREEN | Plan §US-4 §2 listed "all 22 LoopEvent types"; frontend only knows the ~14 serialized SSE types (chat_v2 LoopEvent union — 12 today + 2 from US-6) | LoopVisualizer renders whatever event types appear in rawEvents (eventSummary() handles all 14 known + defensive JSON fallback for any future serialized type) |

### Pace note
Day 2 actual ~2.5-3 hr / committed ~3.5-4.5 hr → ~65-75% of Day 2 budget. US-5 components (MemoryRecentList + MemoryByScopeBrowser) pulled forward from Day 3 §3.1-§3.2 — Day 3 now lighter (just chat-v2 inline mount + SubagentTree + audit cycle). Pattern reuse from 57.11 verification ship saved ~40% scaffolding time.

---

## Day 3 Accomplishments (2026-05-10) ✅

### US-6: SubagentTree (chat-v2 inline) + chatStore subagents slice + SSE 3-edit
- ✅ `chat_v2/types.ts` — Edit 1+2: `SubagentSpawnedEvent` + `SubagentCompletedEvent` added to LoopEvent union; `subagent_spawned` + `subagent_completed` added to KNOWN_LOOP_EVENT_TYPES set (per CONVENTION.md §7 3-edit checklist — closes AD-Cat11-SSEEvents frontend half)
- ✅ `chat_v2/store/chatStore.ts` — Edit 3: `subagents: SubagentNode[]` slice + `clearSubagents` reducer + mergeEvent `subagent_spawned` (push running node, dedup on id) / `subagent_completed` (transition to completed + summary + tokens; defensive-create if no prior Spawned) cases
- ✅ `features/subagent/components/SubagentTree.tsx` — chat-v2 inline panel; buildForest groups flat nodes into parent→child tree (cycle-guarded, depth cap 5); renders SubagentStatusBadge + id prefix + on completion tokens + summary snippet; null when empty (mirrors VerificationPanel)
- ✅ `pages/chat-v2/index.tsx` — mounted `<SubagentTree />` + `<LoopVisualizer mode="inline" />` between VerificationPanel and InputBar (per D2-002 — chat-v2 page, not ChatLayout)
- ✅ **11 NEW Vitest tests** (6 chatStore.subagents + 5 SubagentTree; plan target ≥5 → **220%**)

### US-7: AD-AdminTenant-Patch-Flake fix (audit cycle)
- ✅ `tests/integration/api/conftest.py` — `_clear_committed_test_tenants()` added to autouse `_reset_module_singletons` (before + after yield); deletes stale committed test-tenant rows (codes from PATCH/POST committing tests) via WORM-trigger-toggle single transaction (`ALTER TABLE audit_log DISABLE TRIGGER ... ; DELETE FROM tenants WHERE code = ANY(...) ; ALTER TABLE audit_log ENABLE TRIGGER ... ; COMMIT`)
- ✅ Root cause confirmed: `src/api/v1/admin/tenants.py` PATCH route L488 `await db.commit()` persists test-seeded tenant past db_session rollback → `uq_tenants_code` collision on next run; FK CASCADE to audit_log hits WORM trigger → naive `DELETE FROM tenants` fails
- ✅ `docs/rules-on-demand/testing.md` — NEW §Committed-Row Cleanup Pattern (autouse fixture + WORM-trigger toggle; anti-patterns; cross-refs to §Module-level Singleton + 53.7 §Risk Class C)
- ✅ Verified: `pytest tests/integration/api/test_admin_tenant_patch.py` → **9/9 pass × 3 consecutive runs** (was 3/9 fail on polluted DB)

### Day 3 Aggregate Test Deltas
- **Vitest 157 → 168** (+11 NEW; Day-0-to-Day-3 cumulative +49; plan target +26 → **188%**)
- **pytest 1658** maintained (US-7 is conftest fixture change, not new tests; AD-AdminTenant-Patch-Flake validated via existing 9 tests)
- **mypy strict 0/305** source files
- **9 V2 lints 9/9 green** / **LLM SDK leak 0** / **tsc strict 0** / **ESLint silent**
- **118/118 api integration tests pass** (conftest change no-regression confirmed)

### Day 3 Drift Catalog (1 finding)

| ID | Severity | Finding | Resolution |
|----|----------|---------|------------|
| **D3-001** | 🟠 YELLOW | AD-AdminTenant-Patch-Flake root cause is deeper than "test pollution": admin PATCH route `await db.commit()` + FK CASCADE to audit_log + WORM trigger `audit_log_no_update_delete` blocking `DELETE FROM tenants` | Single-transaction WORM-trigger-toggle in conftest cleanup (same idiom 57.10 D-PRE-DAY4-1 used for manual dev-DB cleanup); explicit committing-test code list (extend per new committing test); documented in testing.md §Committed-Row Cleanup Pattern |

### Pace note
Day 3 actual ~1.5-2 hr / committed ~3-4 hr → ~50% of Day 3 budget. US-5 components were pulled forward to Day 2 → Day 3 was just SubagentTree + chat-v2 mount + audit cycle. Total sprint actual ~7.5-9 hr vs committed ~14 hr at Day 3 end (~55-65%).

---

## Remaining for Day 4

- [ ] Day 4: US-8 routing wire (/memory + /loop-debug to routes.config.ts) + 4 Playwright e2e + chat-v2 8/8 regression + full validation sweep + retrospective Q1-Q7 + memory snapshot + 3 doc syncs + PR

---

## Notes / Risks

- **Day 0 探勘 ROI**: 4 D-PRE-N catalogued from earlier session探勘 (during plan drafting); cost ~5 min Day 0 verify; benefit prevents drifting US-1/US-2 scope mid-implementation.
- **Pattern reuse acceleration**: This sprint's frontend pattern lifts heavily from 57.11 verification real ship (chat-v2 inline panel + standalone admin page + auth gate + 2-tab Routes + features/X folder). Estimate per-US Vitest coverage scaffolding ~30% faster than greenfield Sprint 57.7 IAM rate.
- **Bundle main size watch**: 57.11 closeout left main at 295.14 kB > 285 kB ceiling per AD-Bundle-Size-285kB carryover. Adding 4 NEW lazy chunks may further inflate via shared component hoist (VerifierTypeBadge precedent). Track ratio in Day 4 §4.4 build verification; if grows >10 kB additional, document in retrospective Q3.
- **STRETCH e2e**: User approved defer-allowed for SSE-injection real-flow. Decision deferred to Day 4 — if Playwright SSE mock proves brittle, log AD-Subagent-RealShip-E2E.
