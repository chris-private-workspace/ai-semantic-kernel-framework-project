# Sprint 57.107 Plan — B3 HANDOFF finish: the dead `HandoffExecutor` stub trio retires and a spec-only `handoff` tool makes the 57.68-70 real path LLM-drivable for the first time; `harness_policy` gains handoff governance (enabled + target allowlist, boot-time enforced); `GET /sessions` exposes the handoff lineage chain and the chat-v2 SessionList goes real-data; FORK/TEAMMATE child transcripts persist (CC parentUuid/isSidechain borrow — child sessions row + message_events first consumer)

**Status**: Draft (pending user approval)
**Branch**: `feature/sprint-57-107-handoff-finish`
**Base**: `main` HEAD `b6b2c392` (post-#281 merge)
**Slice**: harness-deepening Workflow B slice B3 (proposal §2.4; per interleave decision RBAC → C3 → **B3** → UX → C2 → B4)
**Scope decisions (user, 2026-06-12)**: US-1 → 刪 stub 三件套 + 註冊 spec-only handoff 工具（真 LLM 可驅動）; US-3 → SessionList 全接真資料 + 鏈顯示（bonus 關閉 `AD-ChatV2-SessionList-Backend`）; US-4 → child 逐 turn 事件持久化到 `message_events`（該表首個 consumer）。

---

## 0. Background

B3 closes Workflow B's HANDOFF slice. The platform layer is ALREADY done (57.68 control-transfer + 57.69 context carry + 57.70 per-tenant agent-spec catalog — proposal §0.2 correction), so B3 is **finish + governance**, not a fresh build. The Day-0 head-start recon found one reshaping fact: **the chat 主流量 never registers a `handoff` ToolSpec** (`business_domain/_register_all.py:266` "HANDOFF intentionally excluded") — the loop classifier (`loop.py:2656-2682`) + router boot hook (`router.py:661`) + `HandoffService` are real and integration-tested, but only a fake loop can trigger them. A real LLM cannot hand off today.

### Design decision (delete the dead trio; spec-only trigger tool; allowlist enforced at boot; sidechain ≠ handoff lineage)

- **Stub trio deleted** (`HandoffExecutor` + `dispatcher.handoff()` + `make_handoff_tool`): 主流量 consumers = 0 (tests + re-exports only) — textbook AP-2; keeping a delegate-to-platform variant would invert category layering (Cat 11 must not import platform_layer). Tests convert per Never-Delete (57.94 precedent). `SubagentMode.HANDOFF` enum value KEPT (four-mode taxonomy survives; `spawn()` already raises for it — comment updated to point at the classifier path).
- **Spec-only `handoff` tool**: the loop classifies `tc.name == "handoff"` BEFORE tool execution and returns (`loop.py:2660-2682`) → the tool needs a ToolSpec the LLM can see, never a runnable handler. Handler = defensive raise ("intercepted by the loop") + negative test (AP-4 guard). Spec description enumerates suggested targets (allowlist or the 3 `DEFAULT_AGENTS`) — guidance only; boot-time validation is authoritative.
- **Governance via `harness_policy`** (C3 mirror, 2 new sparse fields): `handoff_enabled: bool | None` (None/True = registered — the shipped feature defaults ON; False = spec not registered, zero-cost off — `risky_action_enabled` pattern) + `handoff_target_allowlist: list[str] | None` (None = all registered personas; values = restrict; empty list at PUT → 422 "use handoff_enabled to disable"). Enforced **twice**: spec registration (tool absent when disabled) + `boot_handoff(allowed_targets=...)` (LLM naming an off-list target → `HandoffError`, fail-soft + audit — defense in depth).
- **Sidechain lineage is a NEW column pair** (`parent_session_id` + `is_sidechain`, CC parentUuid/isSidechain borrow): `handoff_parent_id` stays separate — handoff = control transfer between top-level sessions; sidechain = nested subagent child. Conflating them would corrupt both queries.
- **Transcript persistence at the API layer** (router observer on `SubagentSpawned` / `SubagentChildEvent` / `SubagentCompleted` — the existing sessions/tool_calls observer pattern): `loop.py` diff 0; agent_harness untouched for US-4; `message_events` (today writerless) gets its first real consumer.
- **Rejected**: dispatcher delegating to `HandoffService` (layering inversion); reusing `handoff_parent_id` for sidechains (semantics clash); persisting child transcripts from inside Cat 11 executors (would need infra imports in agent_harness); a new wire event for any of this (`AgentHandoff` + `SubagentSpawned/Child/Completed` all exist — event count UNCHANGED).

### Ground truth (Day-0 head-start — 3 Explore recon agents + direct greps, file:line anchors on `main` HEAD `b6b2c392`)

- **Stub trio (dead on 主流量)**: `agent_harness/subagent/modes/handoff.py:37-62` (`HandoffExecutor`, ":14-17 Phase 55+ allowlist deferred" comment) · `dispatcher.py:83/:155/:315-332` (import / instantiate / `handoff()`) · `tools.py:133-190` (`make_handoff_tool`) · re-exports `subagent/__init__.py:18/:21/:36/:38` + `modes/__init__.py:5/:8` · consumers outside these: tests only (`test_handoff.py`, `test_subagent_tools.py:96-131`, `test_dispatcher_init.py:88` comment) + `_category_factories.py:221-222` comment.
- **Real path**: classifier `output_parser/classifier.py:47` (`HANDOFF_TOOL_NAME = "handoff"`) + `:68`; loop `loop.py:2656-2682` (HANDOFF branch yields `LoopCompleted(stop_reason="handoff", handoff_target/reason/context)` then returns — tool NOT executed); router hook `router.py:651-705` (detect → `HandoffService().boot_handoff` → `AgentHandoff` SSE → `HandoffError` fail-soft); `platform_layer/handoff/service.py:93-197` (`boot_handoff`: persona resolve :131-136 → tenant 鐵律 :143-151 → child session create :153-171 w/ `handoff_parent_id` + carried_context → parent `handed_off` :173-174 → hash-chained audit :176-191); `persona_registry.py:65-81` (3 `DEFAULT_AGENTS`) + `:100-147` (per-tenant DB catalog, fail-safe fallback); `context_carry.py:70-114`.
- **No allowlist today**: persona resolution is the only target gate; tenant boundary already enforced (service.py:143-151).
- **`AgentHandoff` wire**: `_contracts/events.py:383-395` + `event_wire_schema.py:188-192` (`agent_handoff`) + `sse.py:407-418` — all shipped 57.68; FE pivot + `HandoffBanner` shipped 57.69 (`chatStore.ts` `agent_handoff` → `pivotSession` + banner).
- **Sessions**: ORM `infrastructure/db/models/sessions.py:74-135` (`handoff_parent_id` :102-106 + index :134, migration 0022); `api/v1/sessions.py` has ONLY `GET /{id}/state` (:76); `SessionRepository` has NO `list_sessions()` (only create/get/mark_handed_off :53/:113/:123); session rows ARE created on chat start (router sessions observer :313-339, best-effort SAVEPOINT).
- **FE SessionList**: fixture-only (`SessionList.tsx:131-228` renders `FIXTURE_SESSIONS` + DEMO banner; `fixtures/sessions.ts:27-82`; `types.ts:180-188` Session type has NO lineage fields) — `AD-ChatV2-SessionList-Backend`.
- **Child transcripts ephemeral**: `fork.py:137-144` + `teammate.py:144-150` (`child_session_id=uuid4()` local; events drain to in-memory `final_answer`; relay SSE-only `sse.py:350`); `messages` (:141-195) + `message_events` (:201-246, monthly partitioned, TenantScopedMixin) have **ZERO writers codebase-wide**; checkpoints = `state_snapshots` (`models/state.py:75-117`).
- **HarnessPolicy (C3)**: 9 fields `harness_policy.py:108-116`; resolver :190-222 (TTL 60s, fail-open) + invalidate :225-227; admin PUT/GET + `_validate_harness_policy` `api/v1/admin/tenants.py:1621-1785`; handler resolved-values block `handler.py:470-597`; router resolve :246 → `build_handler` :277; FE `HarnessPolicyTab.tsx` 9 fields + `LIST_FIELDS` :93-144.

### STALE / drift anchors to re-confirm in the formal Day-0 三-prong (§ checklist 0.1)

All file:line above re-verified on the branch: dispatcher `_abc.py` `handoff()` ABC signature + `SubagentMode.HANDOFF` consumers · `SubagentSpawned`/`SubagentCompleted` event field shapes (subagent_id? mode? task? — Prong-2 nested-shape read) · `message_events` partition strategy (monthly partitions — does the current month's partition exist / who creates partitions? Prong-3) · migration head number (0027 occupied? next free) · `_stream_loop_events` closure scope (is the resolved `harness_policy` reachable at the :661 hook?) · `make_default_executor` signature + where the chat handler invokes it (threading point for the spec) · sessions-observer SAVEPOINT pattern (:313-339) to mirror for US-4 · FE `chatStore` sessions state shape (:114-145) · `tools.py` ToolSpec arg-schema shape for the spec-only tool.

## 1. Sprint Goal

A real LLM can hand off for the first time (spec-only `handoff` tool → classifier → `HandoffService`), governed per-tenant (`handoff_enabled` + target allowlist, enforced at registration AND boot); the dead `HandoffExecutor` stub trio is gone (AP-2/AP-11); `GET /sessions` exposes the handoff chain and the chat-v2 SessionList renders real sessions with lineage (closing `AD-ChatV2-SessionList-Backend`); FORK/TEAMMATE child transcripts persist as sidechain sessions + `message_events` rows — proven by a drive-through (real handoff e2e + allowlist rejection + sidechain transcript queryable).

## 2. User Stories

- **US-1**: 作為 platform，我希望刪除主流量零呼叫的 `HandoffExecutor`/`dispatcher.handoff()`/`make_handoff_tool` 並在 chat 主流量註冊 spec-only `handoff` 工具（loop 攔截、handler 永不執行），以便真 LLM 能驅動 57.68-70 的完整 handoff 路徑（AP-2/AP-11 收斂）。
- **US-2**: 作為 tenant admin，我希望 `harness_policy` 增加 `handoff_enabled` + `handoff_target_allowlist`（admin PUT 驗證 + FE tab 欄位），且 allowlist 在 boot 時強制（off-list target → 拒絕 + audit），以便 handoff 治理 per-tenant。
- **US-3**: 作為 chat 使用者，我希望 `GET /api/v1/sessions`（tenant-scoped，含 `handoff_parent_id` + `agent_role`）且 SessionList 渲染真資料 + handoff 鏈標記（↳ from parent），以便看到真實會話與交接脈絡（關閉 `AD-ChatV2-SessionList-Backend`）。
- **US-4**: 作為 platform，我希望 FORK/TEAMMATE child 以 sidechain session row（`parent_session_id` + `is_sidechain`，CC 借鑑）+ 逐 turn `message_events` 持久化（api 層 observer，loop.py 不動），以便 child transcript 可查詢可審計（關閉 `AD-Subagent-Transcript-Isolation`）。
- **US-5**: 作為 reviewer，我希望 drive-through 證明：真 LLM handoff e2e（工具呼叫 → child session → FE pivot + 鏈顯示）/ allowlist 拒絕 off-list target / `handoff_enabled=false` 時工具不存在 / subagent 跑完後 sidechain transcript 落庫——全程真 UI + 真後端 + 真 LLM。

## 3. Technical Specifications

### 3.0 Architecture (loop.py diff 0; no new event; 1 migration; spec-registration + boot double-gate)

```
handler (per request): policy.handoff_enabled is not False
  → register spec-only ToolSpec(name="handoff", args={target_agent, reason})
      description lists policy.handoff_target_allowlist or DEFAULT_AGENTS keys (no hot-path DB)
      handler = defensive raise (loop classifies HANDOFF before execution — loop.py:2656)
router post-loop hook (:651-705): boot_handoff(..., allowed_targets=policy.handoff_target_allowlist)
  → off-list target → HandoffError (fail-soft + audit) — defense in depth
router observer (NEW, mirror sessions-observer SAVEPOINT): SubagentSpawned → sidechain session row
  · SubagentChildEvent → message_events INSERT · SubagentCompleted → mark completed + summary
GET /api/v1/sessions: SessionRepository.list_sessions(tenant_id) — top-level only (is_sidechain=false),
  fields incl. handoff_parent_id + meta_data.agent_role → FE SessionList real-data + ↳ chain badge
```

### 3.1 Stub retirement + spec-only trigger (US-1)

DELETE `modes/handoff.py`; EDIT `dispatcher.py` (drop import/instantiate/`handoff()`), `_abc.py` (drop `handoff()` ABC method), `__init__.py`×2 (drop re-exports), `tools.py` (replace `make_handoff_tool` with `make_handoff_spec(suggested_targets) -> tuple[ToolSpec, handler]` — handler raises `RuntimeError("handoff is loop-intercepted")`). Registration threaded through `make_default_executor(handoff_targets=...)` (mirror the `subagent_dispatcher` opt-in branch). Tests: `test_handoff.py` + `test_subagent_tools.py:96-131` CONVERT to spec-shape + defensive-raise + registration-gating tests (0 deletions). 17.md: `SubagentDispatcher` contract row updated (handoff() removed; HANDOFF = classifier + platform path).

### 3.2 Handoff governance (US-2)

`harness_policy.py`: +`handoff_enabled: bool | None` + `handoff_target_allowlist: tuple[str, ...] | None` (9→11 fields, sparse/tri-state per C3). `service.py` `boot_handoff(*, allowed_targets: Sequence[str] | None = None)`: after persona resolve, `target not in allowed_targets` (when not None) → `HandoffError("target not allowed")` — router's existing fail-soft logs + audits. Admin `_validate_harness_policy`: allowlist entries non-empty str ≤100 chars, ≤20 entries; `[]` → 422 (use handoff_enabled). FE `HarnessPolicyTab`: +1 tri-state select + 1 list field (9→11). Handler: registration gate per §3.0.

### 3.3 Sessions list + lineage (US-3)

`SessionRepository.list_sessions(tenant_id, *, limit=50)` (top-level only, `started_at DESC`). `api/v1/sessions.py`: `GET /api/v1/sessions` → `SessionListItem{id, title, status, created_at, agent_role, handoff_parent_id}` (existing `get_current_tenant` + RLS pattern; 404-style hygiene per multi-tenant rule). FE: `sessionsService.listSessions()` + chatStore `loadSessions` + `SessionList.tsx` real-data render (FIXTURE_SESSIONS + DEMO banner removed; `fixtures/sessions.ts` deleted — Vitest mocks the service) + child rows show `↳ <parent short-ref>` badge; `types.ts` Session += `handoffParentId`/`agentRole`.

### 3.4 Sidechain transcript persistence (US-4) + What is explicitly NOT done

Migration 0028 (head verified Day-0): `sessions.parent_session_id UUID NULL FK ON DELETE SET NULL` + `sessions.is_sidechain BOOL NOT NULL DEFAULT false` + partial index on `parent_session_id`. Router `_stream_loop_events` NEW best-effort observer (SAVEPOINT, mirror :313-339): `SubagentSpawned` → INSERT sidechain session (id=subagent_id, tenant/user inherited, title from task, `is_sidechain=true`, `parent_session_id=session_id`, meta_data mode/agent); `SubagentChildEvent` → INSERT `message_events` (session_id=subagent_id, event_type=inner type, event_data=serialized inner, monotonic sequence_num); `SubagentCompleted` → status=completed + summary/tokens into meta_data. `list_sessions` excludes sidechains (top-level list stays clean); sidechain rows queryable by `parent_session_id`.
**NOT done**: child checkpoint/resume (transcript ≠ durable child state); a sidechain transcript READ API + Inspector replay UI (follow-on AD); messages-table writes for the PARENT transcript (separate concern — today's durable parent transcript = state_snapshots); per-tenant teammate inject policy; detached teammate (§2.5); depth>1.

### 3.5 Validation (US-1..US-5)

Unit: spec-shape + defensive-raise + registration gating (enabled/disabled/allowlist description) · policy 2 new fields (resolver round-trip + tri-state) · `boot_handoff` allowlist accept/reject/None · `list_sessions` repo. Integration: `GET /sessions` (tenant isolation 鐵律 + lineage fields + sidechain exclusion) · admin PUT 422 poles (empty allowlist / >20 / >100 chars) + round-trip · handoff e2e with allowlist reject (extend `test_chat_handoff.py`) · subagent observer (fake loop emits Spawned/Child/Completed → session row + message_events rows + tenant isolation). FE Vitest: SessionList real-data + 鏈 badge + tab new fields. Gates: mypy strict 0 · run_all 10/10 (event count UNCHANGED) · full pytest 0 del · Vitest · mockup-fidelity 53 · `loop.py` / wire schema diff = 0.

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 1 | `backend/src/agent_harness/subagent/modes/handoff.py` | **DELETE** (user-confirmed 2026-06-12) |
| 2 | `backend/src/agent_harness/subagent/dispatcher.py` | EDIT — drop handoff wiring |
| 3 | `backend/src/agent_harness/subagent/_abc.py` | EDIT — drop `handoff()` ABC method |
| 4 | `backend/src/agent_harness/subagent/tools.py` | EDIT — `make_handoff_tool` → `make_handoff_spec` (spec-only) |
| 5 | `backend/src/agent_harness/subagent/__init__.py` + `modes/__init__.py` | EDIT — exports |
| 6 | `backend/src/business_domain/_register_all.py` | EDIT — gated spec registration |
| 7 | `backend/src/platform_layer/governance/harness_policy.py` | EDIT — +2 fields (9→11) |
| 8 | `backend/src/platform_layer/handoff/service.py` | EDIT — `allowed_targets` boot enforcement |
| 9 | `backend/src/api/v1/chat/handler.py` | EDIT — handoff spec gate + threading |
| 10 | `backend/src/api/v1/chat/router.py` | EDIT — allowlist into boot hook + US-4 observer |
| 11 | `backend/src/api/v1/admin/tenants.py` | EDIT — 2 fields + validation |
| 12 | `backend/src/api/v1/sessions.py` | EDIT — `GET /sessions` list |
| 13 | sessions repository (`infrastructure/db/repositories/…`) | EDIT — `list_sessions` + sidechain helpers |
| 14 | `backend/src/infrastructure/db/models/sessions.py` | EDIT — 2 columns |
| 15 | `backend/src/infrastructure/db/migrations/versions/0028_*.py` | NEW — sidechain columns + index |
| 16 | tests: `test_handoff.py` / `test_subagent_tools.py` | CONVERT (Never-Delete) |
| 17 | tests: harness_policy / boot allowlist / sessions-list / observer integration | NEW/EDIT |
| 18 | `frontend/src/features/chat_v2/` `SessionList.tsx` + store + service + `types.ts` | EDIT — real data + 鏈; `fixtures/sessions.ts` DELETE |
| 19 | `frontend/src/features/tenant-settings/` `HarnessPolicyTab.tsx` + service mappers | EDIT — +2 fields |
| 20 | FE Vitest (SessionList + tab) | NEW/EDIT |
| — | `loop.py` / `event_wire_schema.py` / `_contracts/events.py` | **UNTOUCHED** |

## 5. Acceptance Criteria

1. 主流量 grep `HandoffExecutor|dispatcher\.handoff|make_handoff_tool` → 0 hits in `backend/src`; the `handoff` ToolSpec is visible to the LLM when policy allows.
2. Real-LLM drive-through: "hand this off to the reviewer agent" → handoff tool call → child session row (`handoff_parent_id` set) → `AgentHandoff` SSE → FE pivot + banner; sessions list shows parent (handed_off) + child with ↳ badge.
3. Tenant allowlist `["planner"]` → handoff to "reviewer" rejected (no child, audit row, fail-soft); `handoff_enabled: false` → tool absent from the spec list.
4. `task_spawn` (FORK or TEAMMATE) run → sidechain session row + ≥1 `message_events` rows queryable under `parent_session_id`; top-level `GET /sessions` excludes sidechains; cross-tenant isolation tests green.
5. No-policy tenant → handoff ON with default targets; all gates green; 0 test deletions; event count unchanged.

## 6. Deliverables

- [ ] US-1 stub retirement + spec-only tool + test conversions + 17.md row update
- [ ] US-2 policy fields + boot enforcement + admin validation + FE tab fields
- [ ] US-3 `GET /sessions` + repo + FE SessionList real-data + 鏈顯示（關 `AD-ChatV2-SessionList-Backend`）
- [ ] US-4 migration 0028 + router observer + transcript tests（關 `AD-Subagent-Transcript-Isolation`）
- [ ] US-5 drive-through PASS (screenshots + observed-vs-intended)
- [ ] CHANGE-074 + design note 29 (spike extract: handoff completion + sidechain transcript) + closeout (retro Q1-Q7 + calibration + navigators + next-phase-candidates)

## 7. Workload Calibration

- Scope class **`mixed-multidomain-bundle` 0.65** — 4 independent tracks (Cat 11 hygiene + governance mirror + sessions API/FE + transcript persistence w/ migration); heavier than the config-tiering family shape (C1/C3) because of the migration + new observer + FE list rewire.
- **Agent-delegated: partial** — backend parent-direct (deletion + boot enforcement + observer are correctness-sensitive); FE (SessionList rewire + tab fields) agent-delegated-then-parent-re-verified (57.104/57.106 precedent: blended full-stack → no single agent_factor; 3-segment form).
- Bottom-up est ~18.5 hr (US-1 ~2.5 + US-2 ~3 + US-3 ~4 + US-4 ~4.5 + drive-through ~2 + docs/closeout ~2.5) → class-calibrated commit ~12 hr (mult 0.65). Day 4 retro Q2 verifies.

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| Real LLM may not call the `handoff` tool on cue | explicit spec description + targeted prompt; fallback: tighten description wording (not the loop) — drive-through risk noted |
| `message_events` monthly partitioning — current-month partition may not exist | Day-0 Prong-3 verifies partition creation strategy; if absent → migration 0028 also ensures partition (or observer falls back to skip + warn, fail-soft) |
| Migration head drift (0028 occupied) | Day-0 Prong-3 `ls versions/ \| tail` |
| `_stream_loop_events` closure may not see resolved policy at the :661 hook | Day-0 Prong-2 verifies scope; worst case thread one param |
| Observer hot-path cost (1 INSERT per child event) | best-effort SAVEPOINT (mirror :313-339); child events are low-volume vs tokens |
| `SubagentSpawned/Completed` field-shape assumption (subagent_id/mode/task) | Day-0 Prong-2 nested-shape read of the event dataclasses |
| Removing `_abc.py` `handoff()` breaks an unseen implementer | Day-0 Prong-2 grep all `SubagentDispatcher` subclasses |
| FE SessionList rewire regressions (fixture removal) | Vitest service-mock suite + mockup-fidelity gate + drive-through |
| Risk Class C — policy TTL cache + new singletons across test loops | existing autouse reset fixtures cover harness_policy; observer is per-request (no singleton) |
| Risk Class E — stale backend masks spec registration | clean no-reload restart + startup verification before drive-through |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- Sidechain transcript READ API + Inspector replay UI (NEW AD candidate at closeout — `AD-Sidechain-Transcript-Read-API`).
- Parent-transcript `messages` table writes (today's durable parent transcript = `state_snapshots`; separate concern).
- Child checkpoint/resume; detached/streaming teammate (§2.5 — also the inject-UI prerequisite); depth>1 child-of-child.
- Per-tenant teammate inject policy; capability_matrix overrides; `AD-HITL-Policy-ReadSide-Potemkin-Phase58` (own slice per user decision).
- Handoff lineage TREE traversal API (multi-hop chain walk) — v1 ships parent-pointer only; tree walk when a real consumer appears (YAGNI).
- `AD-FE-Tenant-Display-Fixture-Phase58` (sidebar tenant switcher) — separate UX slice.
