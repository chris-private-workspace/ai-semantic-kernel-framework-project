# Sprint 57.107 Progress — B3 HANDOFF finish

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-107-plan.md) · [Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-107-checklist.md)

---

## Day 0 — 2026-06-12 — Plan/Checklist + three-prong verify

**Done**: branch `feature/sprint-57-107-handoff-finish` (from `main` `b6b2c392`) · plan + checklist drafted (mirror 57.106 structure) · user scope decisions captured (stub delete + spec-only tool / SessionList full real-data / message_events first consumer) · three-prong verify complete.

### Drift findings

- **D1** (Prong 3): migration head = `0027_user_password_hash` → **0028 free** ✓ (plan assumption holds).
- **D2** (Prong 2): `_abc.py:58-67` `handoff()` abstractmethod confirmed; **sole implementer = `DefaultSubagentDispatcher`** (`dispatcher.py:97`) + 1 `isinstance` assertion (`test_dispatcher_init.py:44`) → ABC-method removal is safe, no unseen implementers.
- **D3** (Prong 2): `SubagentMode.HANDOFF` consumers = enum def (`_contracts/subagent.py:56`) + `dispatcher.py:195` spawn-raise → KEEP enum, re-point the raise comment at the classifier path.
- **D4** 🔴 (Prong 3, load-bearing): `messages` + `message_events` partitions exist **only `2026_04/05/06`** (created inline in `0002_sessions_partitioned.py:175+`); NO partition-creation helper anywhere → both tables become **un-writable 2026-07-01**. Plan §8 anticipated this branch → **migration 0028 also adds `DEFAULT` partitions for BOTH tables** (2 statements; prevents a dated production failure; messages currently writerless but same bomb).
- **D5** (Prong 2, nested-shape read): `SubagentSpawned{subagent_id, mode, parent_session_id}` (`events.py:352-355`) — **NO task/title field** → sidechain session title = `f"Subagent · {mode}"` (plan §3.4 said "title from task"; adjusted, no event change).
- **D6** (Prong 2): `SubagentCompleted{subagent_id, summary, tokens_used}` + `SubagentChildEvent{subagent_id, inner}` confirmed (:359-379); observer serializes `inner` via the existing sse branch.
- **D7** (Prong 2): sessions-observer pattern confirmed (`router.py:313-339`): env-gate `SESSIONS_CHAT_OBSERVER` (tests set false) + `begin_nested` + early commit + best-effort except → US-4 observer mirrors with its **own flag `SUBAGENT_TRANSCRIPT_OBSERVER`** (default true; conftest false; dedicated suite enables).
- **D8** (Prong 2): `_stream_loop_events` is **module-level** (`router.py:420-435`), NOT a closure → `harness_policy` NOT in scope at the `:661` hook. Plan §8 worst-case branch confirmed: thread one param `handoff_allowed_targets: Sequence[str] | None = None`.
- **D9** (Prong 2): `SessionRepository.create_session` already takes `title`/`handoff_parent_id`/`meta_data` → extend with `parent_session_id`/`is_sidechain` kwargs.
- **D10** (Prong 2): `make_default_executor` call sites in handler = `:224` echo / `:342` child / `:373` teammate / `:419` MAIN real_llm → thread `handoff_targets` **only at `:419`** (echo/child/teammate get None — children cannot handoff by design, depth-bound).
- **D11** (Prong 2): handler (api layer) may import `platform_layer.handoff.persona_registry.DEFAULT_AGENTS` for the default spec-target list (api → platform import direction OK; router already imports `HandoffService`).

**Go/no-go**: GO — D4 adds 2 migration statements; D5/D8/D10 are parameter/wording-level; no acceptance-criteria change.

### Remaining for Day 1
US-1 stub retirement + spec-only tool + US-2 governance fields + boot enforcement + unit tests/conversions.

---

## Day 1 — 2026-06-12 — US-1 stub retirement + spec-only tool + US-2 governance (backend)

**Done**:
- **US-1**: DELETED `modes/handoff.py` (`HandoffExecutor` stub; user-confirmed); `dispatcher.py` dropped import/instantiate/`handoff()` + spawn-raise re-pointed; `_abc.py` dropped `handoff()` abstractmethod; `__init__.py`×2 re-exports updated; `tools.py` `make_handoff_tool` → spec-only `make_handoff_spec(suggested_targets)` (defensive-raise handler — loop classifier intercepts pre-execution); `_register_all.py` opt-in `handoff_targets` registration; `handler.py` policy-gated threading at the MAIN real_llm executor only (`policy` hoisted above the build; echo/child/teammate get None — D10); 17.md `SubagentDispatcher` + `handoff` tool rows updated.
- **US-2**: `harness_policy.py` 9→11 fields (`handoff_enabled` tri-state + `handoff_target_allowlist`); `service.py` `boot_handoff(allowed_targets=)` off-list reject BEFORE any write; `router.py` `handoff_allowed_targets` param threaded into module-level `_stream_loop_events` (D8) → boot hook.
- **Tests**: `test_handoff.py` CONVERTED (4: defensive-raise / description-targets / empty-hint / spawn-HANDOFF-raise); `test_subagent_tools.py` handoff block CONVERTED (3) + 2 NEW gating tests; `test_harness_policy.py` +2; `test_service.py` +3 allowlist. 0 deletions.
- **Gates**: mypy `src` **0/358** (was 359 — 1 file deleted) · flake8 0 · run_all **10/10** (event count UNCHANGED) · full unit **1734 passed**.

**Note**: run_all must run from repo root (from `backend/` it reports 9/10 false-FAIL — CWD-sensitive `--root` defaults).

### Remaining for Day 2
US-3 sessions list API + US-4 migration 0028 (sidechain columns + DEFAULT partitions per D4) + router observer + admin validation fields + integration tests.

---

## Day 2 — 2026-06-12 — US-3 sessions list + US-4 sidechain transcript (backend)

**Done**:
- **US-3**: `SessionRepository.list_sessions` (top-level, newest-first, limit 50) + `create_session` sidechain kwargs; `GET /api/v1/sessions` (`SessionListItem` with `agent_role` + `handoff_parent_id` lineage); `test_sessions_list.py` 4 tests.
- **US-4**: migration `0028_sidechain_sessions` (2 columns + partial index + **DEFAULT partitions both tables — D4 fix**; applied clean); `models/sessions.py` + repo; router `_persist_subagent_transcript` observer (SAVEPOINT best-effort, BOTH drain sites — in-loop + defensive flush; per-sidechain monotonic seq; `SUBAGENT_TRANSCRIPT_OBSERVER` env-gate, conftest false per D7); `message_events` gets its FIRST writer. `test_subagent_transcript_observer.py` 3 tests.
- **US-2 rest**: admin `tenants.py` +2 fields + 422 poles (empty-allowlist / >20 / blank-or->100-char) + caps `_MAX_HANDOFF_TARGETS=20`/`_MAX_HANDOFF_TARGET_LEN=100`; +4 pole tests; `test_chat_handoff.py` +2 allowlist e2e (off-list fail-soft: no child + parent stays active + no `agent_handoff` frame; allowlisted boots).
- **Gates**: mypy 0/359 · flake8 0 · run_all 10/10 · **full pytest 2460+4skip (+21 vs 57.106, 0 del)** · alembic head = 0028.

### Remaining for Day 3
FE (SessionList real-data + 鏈 badge + HarnessPolicyTab 2 fields + Vitest) → full FE gates → drive-through (US-5) → CHANGE-074 + note 29.

---

## Day 3 — 2026-06-12 — FE (agent-delegated, parent re-verified) + drive-through PASS

**3.1 FE** (code-implementer agent; parent re-ran ALL 4 gates per Before-Commit item 7):
SessionList fixture→real (`listSessions` service + `loadSessions` store action + ↳ `.route-pill` chain badge; FIXTURE_SESSIONS + DEMO banner deleted; ChatHeader rewired); HarnessPolicyTab 9→11 fields. Gates: lint 0 · build ✓ · Vitest 828/828 (137 files) · mockup-fidelity ✓ (**HEX_OKLCH_BASELINE ratcheted 53→51** — banner removal −2). Agent deviations accepted: `domain` field dropped (no backend source — anti-Potemkin), ChatHeader rewire (fixture-deletion forced), orphan i18n keys removed. Closes `AD-ChatV2-SessionList-Backend`.

**3.3 Drive-through (US-5) — ALL 4 LEGS PASS** (real UI :3007 + fresh no-reload backend PID 9680 on 57.107 + real Azure gpt-5.2; founder `founder@dt57105.test` password-login, zero dev-login; Risk Class E clean restart — killed stale 57.106-era PID 37844, fresh process sole :8000 owner; founder password re-set via the 57.105 D11 out-of-band `set_password` pattern — not recorded in docs by design):

| Leg | Intended | Observed |
|-----|----------|----------|
| **A — handoff e2e** | LLM calls `handoff` → child boots → SSE → FE pivot | ✅ **FIRST EVER real-LLM handoff**: gpt-5.2 called the spec-only tool (llm_response "1 tool call") → `loop_end stop=handoff` → `agent_handoff` frame (target=reviewer, child `eab49331…`) → HandoffBanner「已交棒給 reviewer」+ reason rendered. `dt57107-A-handoff-banner.png` |
| **B1 — allowlist** | off-list target rejected | ✅ STRONGER than intended: the allowlist's FIRST defense layer (spec description listing only `planner`) steered the real LLM to hand off to planner — it never attempted the off-list reviewer (reason: "transferring to available agent identity"). Boot-time rejection (2nd layer) proven by `test_chat_handoff_offlist_target_fails_soft_no_child`. `dt57107-B1-…png` |
| **B2 — enabled=Off** | tool absent, no handoff | ✅ same ask → `Turn 2 · end_turn` completed normally, NO handoff/banner/child; the LLM (lacking the tool) delegated via `task_spawn` instead — Subagents (1) panel. `dt57107-B2-…png` |
| **C — sidechain transcript** | task_spawn → rows queryable | ✅ sidechain session `709ded76…` (title "Subagent · teammate", completed, parent set, summary + tokens 3993 folded into meta_data) + **message_events FIRST EVER rows: 6 (seq 1-6, subagent_child)** |
| **D — SessionList real** | real list + 鏈 | ✅ 8 real sessions newest-first; "Handoff → reviewer/planner" children with `↳ reviewer`/`↳ planner` badges + agent_role; parents no longer "running" (handed_off mapped). `dt57107-D-sessionlist-chain.png` |

Cleanup: tenant policy cleared back to System default via the tab (cache invalidation re-proven). Screenshots in `artifacts/` (4).

### Remaining for Day 4
CHANGE-074 + design note 29 + checklist final + retro Q1-Q7 + calibration + navigators + carryover.
