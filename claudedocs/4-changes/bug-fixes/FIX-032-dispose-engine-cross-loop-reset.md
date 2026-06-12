# FIX-032: dispose_engine cross-loop reset — test-infra event-loop isolation

**Date**: 2026-06-12
**Sprint**: 57.106 (post-merge CI fix on the C3 PR #281 branch)
**Scope**: infrastructure/db (test-infra) — cross-cutting

## Problem

PR #281's required check "Lint + Type Check + Test (with PostgreSQL 16)" FAILED on
`tests/unit/business_domain/incident/test_service.py::test_create_returns_incident`:

```
RuntimeError: Task <...test_create_returns_incident()...> got Future <...>
attached to a different loop
... RuntimeError: Event loop is closed
```

The test passes in isolation (1/1) and in its own file (12/12); `git diff main...HEAD`
touches **zero** incident files. It is a latent Risk Class C (module-level engine
singleton across pytest-asyncio per-test event loops) flake that Sprint 57.106's new
unit test files (`tests/unit/platform_layer/governance/test_harness_policy.py` +
`tests/unit/agent_harness/guardrails/test_risky_action_detector.py`) **unmasked by
shifting pytest's collection order** — a different test now runs immediately before
the incident suite under CI's ordering.

## Root Cause

`infrastructure/db/engine.py` caches a module-level `AsyncEngine` + `async_sessionmaker`.
The `db_session` fixture (`tests/conftest.py`, function-scoped) disposes the engine at
**teardown** so the next per-test loop gets a fresh engine. Two gaps let a stale engine
survive into the next test:

1. **`dispose_engine()` reset was not exception-safe**: `await _engine.dispose()` on a
   stale engine whose pooled asyncpg connection belongs to an already-closed loop makes
   asyncpg's graceful close call `create_task` on that dead loop → `RuntimeError('Event
   loop is closed')`. The exception propagated **before** `_engine`/`_session_factory`
   were nulled, so the stale engine stayed cached and the NEXT test reused it cross-loop.
2. **Teardown-only disposal**: a test that touches the engine WITHOUT the `db_session`
   fixture (no teardown dispose) also leaks it into the next test.

## Solution

Two-part, in the test-infra owners:

1. **`engine.py` `dispose_engine()`** — wrap `await _engine.dispose()` in `try/except` so
   the singleton reset to `None` ALWAYS runs, even if graceful close raises on a dead loop
   (the connection's loop is gone — there's nothing left to clean). Forces a fresh engine
   on the next loop regardless.
2. **`tests/conftest.py` `db_session`** — `await dispose_engine()` at fixture **setup**
   too (not only teardown), so every test starts on a fresh engine bound to its own loop
   regardless of what ran before (covers the non-`db_session` engine-user case). Safe now
   that #1 makes dispose always reset.

## Verification

- Full backend suite: **2439 passed + 4 skipped, 0 failures** (107s) — incident test now
  passes reliably (+1 vs the pre-fix 2438+flake). Unit suite alone: 1726 passed.
- mypy `src` 0/359 · flake8 clean · run_all 10/10.
- Re-push re-triggers PR #281 CI (the previously-red required check).

## Impact

Test-infra only (`engine.py` dispose hardening is also a strictly-more-robust app-shutdown
path — a failed graceful close no longer leaves a dangling singleton). No product behavior
change. The fix is general (not incident-specific): any test-ordering permutation that
previously leaked the engine cross-loop is now self-healing.
