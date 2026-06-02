# FIX-026: HANDOFF persona DB-call surfaced a test-isolation connection leak

**Date**: 2026-06-02
**Sprint**: 57.68 (A-3b)
**Scope**: Tests / api-chat (test isolation — Risk Class C)

## Problem
After Sprint 57.68 Stage-2, the full `pytest tests/unit tests/integration` run failed **deterministically** on `tests/unit/business_domain/incident/test_service.py::test_create_returns_incident` with `RuntimeError: Event loop is closed` (+ `coroutine 'Connection._cancel' was never awaited`). The incident test passes in isolation + as a whole module; Sprint 57.67 (main) ran the full suite green (1994 passed / 0 failed). The incident module was NOT touched this sprint.

## Root Cause
The Stage-2 source change added `system_prompt = await resolve_session_persona(db, session_id, current_tenant)` to the `chat()` endpoint (`handler.py`/`router.py`). `resolve_session_persona` issues a real `SessionRepository.get_session` SELECT. The pre-existing unit test `tests/unit/api/v1/chat/test_router.py` drives the real `POST /chat` via `TestClient` and overrides `get_current_tenant`/`get_current_user_id` but **not** `get_db_session` — so the new SELECT forced an actual asyncpg socket on the TestClient's per-test event loop (previously the lazily-pooled connection was acquired but never queried, so no socket opened). That connection returned to the singleton engine pool; the TestClient loop closed; `dispose_engine()` never ran (the test has no `db_session` fixture); a later `db_session` test (incident, first in collection order after the api group) pinged the pooled dead connection → "Event loop is closed". The added Stage-2 tests shifted collection order so the GC-timed failure now lands on the incident test. This is the documented **Risk Class C** (module-level singleton/engine across test event loops).

## Solution
Two proper fixes (no skip/xfail):
1. **Root cause** — `test_router.py` `app` fixture now overrides `get_db_session` → an async `_no_db()` yielding `None`. The endpoint's full path handles `db=None` (`resolve_session_persona` returns `DEMO_SYSTEM_PROMPT` via its `if db is None` guard; the handoff hook is gated on `db is not None`; LoopCompleted observers are env-disabled in conftest). No real connection is ever opened on the unit path → the leak is eliminated at its source, independent of ordering/GC.
2. **Hygiene** — the 3 router-hook tests that drive the real `_stream_loop_events` were relocated from `test_chat_handoff_unit.py` to the integration file `test_chat_handoff.py`, each now `db_session`-dependent (so `dispose_engine()` teardown runs). The unit file keeps only the 6 `resolve_session_persona` tests (mocked repo + `object()`/`None` db — never open a connection).

## Verification
`cd backend && python -m pytest tests/unit tests/integration -q -p no:cacheprovider` → **1999 passed / 4 skipped / 0 failed** (incident passes in the full run). `tests/unit` alone → 1424 passed / 0 failed. `mypy src/` 0; `run_all.py` 10/10; flake8 clean on both modified test files.

## Impact
Tests only (`test_router.py` fixture + relocation of 3 tests to integration). No source/behavior change beyond CHANGE-036. Confirms a general lesson: adding a DB call to an endpoint can surface latent test-isolation leaks in TestClient-based tests that don't override `get_db_session` (logged for sprint-workflow §Common Risk Classes — Risk Class C reinforcement).
