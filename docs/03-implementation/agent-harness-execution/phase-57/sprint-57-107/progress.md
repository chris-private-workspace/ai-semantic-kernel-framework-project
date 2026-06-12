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
