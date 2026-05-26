# Sprint 57.53 — Checkpointer Test Tenant Isolation Pre-Existing Fail Investigation

**Phase**: 57+ Frontend SaaS (medium-backend class — non-frontend test-infra hygiene investigation)
**Goal**: Investigate + classify + fix the pre-existing pytest failure `tests/integration/agent_harness/state_mgmt/test_checkpointer_db.py::test_tenant_isolation` carried as `AD-Checkpointer-Test-Tenant-Isolation-PreExisting-Fail-Investigation` since Sprint 57.51 + Sprint 57.52 (Sprint 57.51 + 57.52 carried it as 0-backend-source-change hygiene sprints; Sprint 57.53 is the user-confirmed scope for full investigation).
**Branch**: `feature/sprint-57-53-checkpointer-tenant-isolation-investigation`
**Class**: `medium-backend` 0.80 (5-data-point baseline: 55.5=1.14 + 55.6=0.92 + 57.47=0.16 + 57.48=0.11 + 57.50=0.27; 5-pt mean 0.52; KEEP per Sprint 57.50 retro `confound-resolved-by-sub-class-split` discipline — class baseline calibrates human-pace, agent residual captured at sub-class layer)
**Sub-class** (agent_factor): `mechanical-greenfield` 0.50 (**tier-3 1st validation** under NEW table effective Sprint 57.53+ per Sprint 57.52 retro Q4 tier-3 SPLIT ACTIVATION; closes carryover `AD-AgentFactor-Tier-3-Validation-Sprint-57.53`)
**Date**: 2026-05-26 (Sprint 57.52 closeout same-day continuation)
**Prior sprint reference**: Sprint 57.51 closeout Day 1 validation sweep first surfaced + flagged the pre-existing fail (Sprint 57.51 `progress.md` Day 1.4) + Sprint 57.52 Day 1 validation sweep re-confirmed unchanged status (commit `bfa010f1` baseline); both sprints carried it forward as out-of-scope NEW carryover AD.

---

## 1. Sprint Goal

```
AS the project maintainer of V2 pytest baseline integrity + test data
   isolation discipline (per `.claude/rules/multi-tenant-data.md` 鐵律
   + `.claude/rules/sprint-workflow.md §Common Risk Classes Risk Class C`)
I WANT the pre-existing `test_checkpointer_db::test_tenant_isolation`
   failure on main investigated, root-cause-classified, and fixed such that
   the full backend pytest suite returns to ALL-GREEN (1759 PASS + 0 fail)
SO THAT (a) Sprint 57.54+ sprints have a clean pytest baseline to detect
   regressions against (currently 1759 PASS + 1 PRE-EXISTING fail masks
   any new test regression in the same test file); (b) the carryover AD
   that has been deferred across Sprint 57.51 + 57.52 closure is closed
   permanently; (c) the test-infra fixture contract violation (or other
   root cause) is documented in retrospective.md Q3 as a generalizable
   lesson for future test design; (d) `medium-backend` 0.80 class gets
   its 6th data point (5-pt mean 0.52 below band currently — confound
   resolved by sub-class split per Sprint 57.50 retro Q4 discipline);
   (e) NEW tier-3 sub-class `mechanical-greenfield` 0.50 gets its 1st
   validation data point — completes carryover AD-AgentFactor-Tier-3-
   Validation-Sprint-57.53.
```

## 2. Background & Context

### 2.1 Failing test snapshot

**Test**: `backend/tests/integration/agent_harness/state_mgmt/test_checkpointer_db.py::test_tenant_isolation` (L142-155)

**Test design intent**: Verify `DBCheckpointer.load()` is tenant-isolated — `tenant_b`'s checkpointer cannot read `tenant_a`'s saved state snapshot even when probing with `session_a.id`. Asserts `StateNotFoundError` is raised when `cp_b.load(version=1)` targets `session_a`'s row.

**Actual fail mode** (captured Sprint 57.53 Day 0 recon):
```
sqlalchemy.exc.IntegrityError: <class 'asyncpg.exceptions.UniqueViolationError'>:
duplicate key value violates unique constraint "uq_tenants_code"
DETAIL: Key (code)=(ISO_A) already exists.
[SQL: INSERT INTO tenants (code, display_name) VALUES ('ISO_A', 'Tenant ISO_A')]
```

The IntegrityError fires at `_build_session(db_session, tenant_code="ISO_A")` L145, never reaches the assertion under test. The `uq_tenants_code` UNIQUE constraint on `tenants.code` rejects the INSERT because a prior `ISO_A` row already exists in the test DB.

### 2.2 Fixture contract baseline (`backend/tests/conftest.py`)

```python
async def db_session() -> AsyncIterator[AsyncSession]:
    """Per-test AsyncSession with rollback + engine disposal at end."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
        finally:
            await session.rollback()
    await dispose_engine()

async def seed_tenant(session, *, code: str = "TEST_TENANT", ...) -> Tenant:
    """Create + flush a Tenant. Caller must NOT commit — fixture rollback handles cleanup."""
    t = Tenant(code=code, display_name=display_name or f"Tenant {code}")
    session.add(t)
    await session.flush()
    await session.refresh(t)
    return t
```

**Fixture contract**: `db_session` rolls back at teardown. `seed_tenant` flushes (not commits) so rollback clears the row. **If contract is respected, ISO_A row should NEVER persist across tests, let alone across pytest sessions.**

### 2.3 Hypotheses for ISO_A persistence

| Hypothesis | Plausibility | Evidence to gather | Fix path |
|------------|--------------|--------------------|----------|
| **H1**: Fixture contract violated — some test / fixture calls `session.commit()` for an `ISO_A` tenant | Medium-High | `grep -rn "commit.*ISO_A\|ISO_A.*commit"` + `grep -rn "session.commit\|db_session.commit"` in `tests/` | Refactor offending test to use `flush()` not `commit()` |
| **H2**: Manual `psql` insert leftover from interactive debugging | Medium | `SELECT * FROM tenants WHERE code = 'ISO_A'` → check `created_at` (predates current pytest run?) | DELETE stale rows + document baseline cleanup runbook |
| **H3**: Sprint 53.6 WORM trigger pattern variant — tenant row survives db_session rollback via a DB trigger commit | Low | `SELECT * FROM information_schema.triggers WHERE event_object_table='tenants'` + check `audit_log` trigger cascade | Add SAVEPOINT pattern + autouse cleanup fixture (per Sprint 53.6 `reset_service_factory` precedent) |
| **H4**: Test infrastructure changed between Sprint 53.1 (test creation) + Sprint 57.51 (first surfaced) — earlier `seed_tenant` may have used `commit()` then was refactored to `flush()` without migration | Medium | `git log --follow tests/conftest.py | grep -i 'seed_tenant\|commit'` + git blame on conftest.py L65-73 | Document migration gap + close via fixture audit |
| **H5**: Stale row from a previous broken test run that crashed before rollback could execute | Low-Medium | `SELECT * FROM tenants WHERE code IN ('ISO_A','RT','TT','MM_SID','MM_TID','MISSING','SIZE')` — if all 7 test codes are present, H5 confirmed | DELETE stale rows + add startup cleanup hook OR randomize codes |

**Day 1 task 1.1 (Investigation)** will execute the evidence-gathering steps for H1-H5 and produce a verdict.

### 2.4 Pattern alignment with existing rules

**`.claude/rules/sprint-workflow.md §Common Risk Classes Risk Class C`** documents the Module-level Singleton variant (Sprint 53.6 lesson). The current case is a sibling pattern — **DB row leak**, not module singleton — but the structural lesson is identical: **fixtures with implicit cleanup contracts can silently leak state across test sessions if any caller violates the contract**.

Sprint 57.53 Day 2 retro Q3 will propose either (a) extending §Common Risk Classes with NEW row "Risk Class E: Test DB Row Leak Across Pytest Sessions" OR (b) treating this as Risk Class C variant case 2 (Sprint 53.6 = singleton across event loops; Sprint 57.53 = DB row across pytest sessions). Decision deferred to Day 2 evidence-based.

### 2.5 Sprint 57.51-57.52 carryover chain

- Sprint 57.51 closeout (`progress.md` Day 1.4): "pytest 1759 PASS + 4 skip + 1 PRE-EXISTING fail flagged `test_checkpointer_db::test_tenant_isolation` 0 backend source changes → NEW carryover AD"
- Sprint 57.52 closeout (`progress.md` Day 1 + retrospective.md Q5): "pytest 1759 PASS + 4 skip + **1 PRE-EXISTING fail** (`test_checkpointer_db::test_tenant_isolation` unchanged; Sprint 57.53 user-confirmed scope; **not investigated per instructions**)"
- Sprint 57.53 = first sprint where investigation is in-scope

### 2.6 Tier-3 sub-class `mechanical-greenfield` 0.50 1st validation

Per Sprint 57.52 retro Q4 + `sprint-workflow.md §Active Activation history` Sprint 57.52 entry:
- Tier-3 SPLIT ACTIVATED 2026-05-27: `mixed-multidomain-bundle-mechanical` 0.65 (unchanged) + `mixed-multidomain-bundle-non-mechanical` 1.0 NEW
- Existing tier-2 sub-classes UNCHANGED: `mechanical-pattern-reuse-heavy` 0.30 / `mechanical-greenfield` 0.50 / `partial` 0.75 / `human` 1.0
- Sprint 57.53 work shape = single-domain backend test-infra investigation + targeted fix = matches `mechanical-greenfield` 0.50 (single NEW component-pair or single-track fix; <4 mechanical repetitions of same template)

**1st validation prediction**:
- If fix is Option A (DELETE stale row + add cleanup hook) → ~30-45 min actual → ratio ~0.6-0.9 IN/BELOW band; 1st validation data point
- If fix is Option B (refactor offending caller) → ~45-60 min actual → ratio ~0.9-1.2 IN band; cleanest validation
- If investigation reveals deeper structural issue (Sprint 53.6 variant requiring SAVEPOINT pattern across multiple test suites) → ~90 min actual → ratio ~1.8 ABOVE band → flag for tier-3 refinement

---

## 3. User Stories

### US-1: Investigate Root Cause via Hypothesis Elimination

```
AS the AI assistant inheriting the AD-Checkpointer-Test-Tenant-Isolation-
   PreExisting-Fail-Investigation carryover from Sprint 57.51 + 57.52
I WANT to systematically eliminate hypotheses H1-H5 (per §2.3) by querying
   the test DB state, grep'ing the test infrastructure for fixture-contract
   violators, and reading git history of `tests/conftest.py`
SO THAT the root cause is identified with evidence + a fix path
   (Option A/B/C/D) is chosen at Day 1 task 1.2 decision gate.
```

**Acceptance**:
- DB query result captured in `progress.md` Day 1.1: `SELECT * FROM tenants WHERE code IN ('ISO_A','RT','TT','MM_SID','MM_TID','MISSING','SIZE')` — count of stale rows per code + their `created_at` timestamps
- `tests/` directory grep'd for `session.commit\|db_session.commit\|.commit()` patterns + offending callers (if any) catalogued
- `git log --follow tests/conftest.py` reviewed for `seed_tenant` evolution + commit() → flush() migration history (if any)
- Verdict written: H1/H2/H3/H4/H5 = confirmed / refuted / inconclusive
- Fix path decided: Option A (data-only cleanup) / Option B (caller refactor) / Option C (SAVEPOINT pattern) / Option D (per-test code randomization)

### US-2: Implement Chosen Fix Path

```
AS the project maintainer of pytest baseline integrity
I WANT the chosen fix from US-1 implemented + verified end-to-end
SO THAT the next full `pytest --tb=short -q` returns 1759+N PASS + 0 fail
   (where N depends on whether US-1 surfaces additional tests that should
   be added to prevent regression — e.g. a fixture-contract enforcement
   test).
```

**Acceptance** (one of Option A-D applied):
- **Option A — Data-only cleanup**: Manual `DELETE FROM tenants WHERE code IN ('ISO_A','RT','TT','MM_SID','MM_TID','MISSING','SIZE')` against test DB + add `conftest.py` autouse `_cleanup_test_tenants` fixture that DELETEs known test tenant codes at session start
- **Option B — Caller refactor**: Identify offending test/fixture using `session.commit()` against contract; refactor to `flush()` only; add regression test guarding the contract
- **Option C — SAVEPOINT pattern**: Wrap `db_session` fixture body in nested transaction (`async with session.begin_nested():`) so even contract violations get rolled back at outer scope (precedent: Sprint 55.4 `AD-Test-DB-Trigger` SAVEPOINT pattern)
- **Option D — Per-test code randomization**: Change `seed_tenant` default to `code=f"TEST_{uuid4().hex[:8]}"` so collisions are impossible; update existing test callers to pass explicit codes only when uniqueness matters for the assertion

### US-3: Document Lesson in Retrospective Q3 + Codify into Sprint Workflow Rule

```
AS the V2 sprint workflow maintainer
I WANT the root cause + fix decision + generalizable lesson documented
   in Sprint 57.53 retrospective Q3 + (conditionally) appended to
   `sprint-workflow.md §Common Risk Classes` as either a new Risk Class E
   (DB Row Leak Across Pytest Sessions) OR an extension to Risk Class C
   (variant case 2 — distinct from Sprint 53.6 module singleton)
SO THAT future test design avoids the same trap + Day 0 三-prong Prong 2
   content verify gains a new pattern grep target ("commit() against
   fixture contract") when reviewing test-infra changes.
```

**Acceptance**:
- `retrospective.md` Q3 (lessons section) includes specific fixture-contract finding + Option choice rationale
- If Option B/C/D chosen → `sprint-workflow.md §Common Risk Classes` extended with NEW row OR Risk Class C variant note
- If Option A only → §Common Risk Classes left untouched (treating Sprint 57.53 as one-time data cleanup; document only in retro for traceability)
- MHist 1-line entry on any edited file (≤100 char budget per AD-Lint-MHist-Verbosity)

---

## 4. Technical Specification

### 4.1 Day 1 Task 1.1 — Hypothesis Elimination Steps

**Step 1**: Connect to test PostgreSQL + query stale tenant rows:
```bash
cd backend && python -c "
import asyncio
from infrastructure.db.engine import get_session_factory
from sqlalchemy import text

async def main():
    factory = get_session_factory()
    async with factory() as session:
        result = await session.execute(text(\"\"\"
            SELECT code, display_name, id, created_at FROM tenants
            WHERE code IN ('ISO_A','RT','TT','MM_SID','MM_TID','MISSING','SIZE','CHKPT_TEST','TEST_TENANT')
            ORDER BY created_at;
        \"\"\"))
        for row in result: print(row)

asyncio.run(main())
"
```

**Step 2**: Grep test infrastructure for fixture-contract violators:
```bash
cd backend && grep -rn "session\.commit\|db_session\.commit\|\.commit()" tests/ --include="*.py" | grep -v "session.rollback\|db_session.rollback" | head -50
```

**Step 3**: Review `seed_tenant` evolution history:
```bash
cd backend && git log --follow --oneline -- tests/conftest.py | head -20
```

**Step 4**: Cross-reference Sprint 53.6 SAVEPOINT precedent + Sprint 55.4 AD-Test-DB-Trigger pattern:
```bash
grep -n "savepoint\|SAVEPOINT\|begin_nested" backend/tests/conftest.py backend/tests/**/conftest.py 2>/dev/null
```

**Step 5**: Check audit_log / FK CASCADE / WORM trigger involvement:
```bash
cd backend && python -c "
import asyncio
from infrastructure.db.engine import get_session_factory
from sqlalchemy import text

async def main():
    factory = get_session_factory()
    async with factory() as session:
        result = await session.execute(text(\"\"\"
            SELECT event_object_table, trigger_name, event_manipulation, action_timing
            FROM information_schema.triggers
            WHERE event_object_table = 'tenants';
        \"\"\"))
        for row in result: print(row)

asyncio.run(main())
"
```

### 4.2 Day 1 Task 1.2 — Option Decision Gate

Based on evidence from §4.1, choose Option A/B/C/D (or hybrid). Decision criteria:

| Evidence pattern | Recommended Option | Rationale |
|------------------|--------------------|-----------|
| All 7 test codes present in DB with consistent `created_at` (same hour) | Option A | One-time data leak from a single crashed run; cleanup + prevention via autouse fixture |
| Only `ISO_A` present (or sparse codes) | Option A + investigate why only ISO_A | Targeted leak; investigate caller |
| `grep .commit()` finds explicit committer in test_checkpointer_db.py or related | Option B | Fixture contract violator located; refactor caller |
| WORM trigger or audit_log FK CASCADE drives row persistence | Option C (Sprint 53.6 SAVEPOINT precedent) | DB-level pattern requires SAVEPOINT fix |
| All test codes have varying `created_at` across multiple days | Option D | Persistent contract leakage; randomize defaults |
| H1-H5 all inconclusive | Option A only + Day 2 retro Q3 propose deeper investigation as Phase 58.x carryover | Don't over-engineer without evidence |

### 4.3 Day 1 Task 1.3 — Fix Implementation Templates

**Option A template**:
```python
# backend/tests/conftest.py — ADD autouse session-scope fixture
@pytest.fixture(scope="session", autouse=True)
async def _cleanup_stale_test_tenants():
    """Delete known test tenant codes left from prior crashed runs."""
    factory = get_session_factory()
    async with factory() as session:
        await session.execute(text("""
            DELETE FROM tenants WHERE code IN (
                'ISO_A','RT','TT','MM_SID','MM_TID','MISSING','SIZE','CHKPT_TEST','TEST_TENANT'
            )
        """))
        await session.commit()  # intentional: cleanup must persist
    yield
```

**Option B template** (caller refactor):
- Locate offending test → change `await session.commit()` → `await session.flush()`
- Add `tests/test_fixture_contract.py::test_seed_tenant_does_not_persist_across_sessions` regression test

**Option C template** (SAVEPOINT pattern):
```python
async def db_session() -> AsyncIterator[AsyncSession]:
    factory = get_session_factory()
    async with factory() as session:
        async with session.begin_nested():  # SAVEPOINT
            try:
                yield session
            finally:
                pass  # outer rollback drops the SAVEPOINT
        await session.rollback()
    await dispose_engine()
```

**Option D template**:
```python
# backend/tests/conftest.py — change default
import uuid
async def seed_tenant(session, *, code: str | None = None, ...) -> Tenant:
    code = code or f"TEST_{uuid.uuid4().hex[:8]}"
    ...
```
+ Update `test_checkpointer_db.py` callers if they assert on specific code values.

### 4.4 Day 1 Task 1.4 — Verification

- `cd backend && pytest tests/integration/agent_harness/state_mgmt/test_checkpointer_db.py -v` → 7/7 PASS
- `cd backend && pytest --tb=short -q` → **1759+N PASS + 0 fail** (N = number of regression tests added in Option B/C)
- `cd backend && mypy --strict src/` → 0 errors
- `python scripts/lint/run_all.py` → 9/9 GREEN
- `cd frontend && npm run test` → 607 PASS preserved
- `cd frontend && npm run build` → exit 0
- LLM SDK leak scan → 0

---

## 5. File Change List

### Backend test infra (likely scope; Option-dependent)
- `backend/tests/conftest.py` — Option A adds `_cleanup_stale_test_tenants` autouse fixture; Option C wraps `db_session` in `begin_nested()`; Option D changes `seed_tenant` default
- `backend/tests/integration/agent_harness/state_mgmt/test_checkpointer_db.py` — Option B may refactor offending caller; Option D may update callers if explicit code assertions exist
- `backend/tests/test_fixture_contract.py` — NEW file IF Option B (regression test guarding fixture contract)

### Test DB data cleanup (Option A always)
- 1 one-shot manual `DELETE FROM tenants WHERE code IN (...)` against test DB (not committed to repo — runbook step documented in `progress.md` Day 1.3)

### Sprint workflow rule (conditional; Option B/C/D triggers; not always)
- `.claude/rules/sprint-workflow.md §Common Risk Classes` — add Risk Class E OR extend Risk Class C variant note
- MHist 1-line entry on edited rule file

### Sprint artifacts
- `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-53-plan.md` (this file)
- `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-53-checklist.md`
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-53/progress.md`
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-53/retrospective.md`
- `memory/project_phase57_53_checkpointer_tenant_isolation_fix.md`
- `memory/MEMORY.md` (pointer entry)
- `claudedocs/1-planning/next-phase-candidates.md` (Sprint 57.53 closeout note)
- `CLAUDE.md` (Current Sprint row + Last Updated footer)

### Frontend
- 0 `.ts/.tsx` changes (backend test-infra investigation only)

---

## 6. Workload

**Bottom-up est**: ~2.0 hr
- Day 0 三-prong (Prong 1 path verify on conftest.py + test file + Risk Class C section; Prong 2 content verify on `seed_tenant` + `db_session` contract claims + Sprint 53.6 SAVEPOINT precedent; Prong 3 Schema verify on `tenants` table + WORM trigger): ~0.3 hr
- Day 1 Task 1.1 Investigation (5 evidence-gathering steps + verdict): ~0.5 hr
- Day 1 Task 1.2 Option decision gate (read evidence + pick Option A-D): ~0.1 hr
- Day 1 Task 1.3 Fix implementation (Option A baseline; B/C/D may add ~30 min each): ~0.6 hr
- Day 1 Task 1.4 Verification sweep (pytest + mypy + lints + frontend): ~0.2 hr
- Day 2 closeout (retro + memory + CLAUDE.md + sprint-workflow.md conditional update): ~0.3 hr

**Class-calibrated commit** (`medium-backend` 0.80):
- 2.0 × 0.80 = **~1.6 hr committed (~96 min)**

**Agent-adjusted commit** (`agent_factor = 0.50` tier-3 `mechanical-greenfield` — **1st validation**):
- 1.6 × 0.50 = **~0.8 hr agent-adjusted (~48 min)**

**4-segment form**:
> Bottom-up est ~2.0 hr → class-calibrated commit ~1.6 hr (mult 0.80) → agent-adjusted commit ~0.8 hr (agent_factor 0.50 tier-3 `mechanical-greenfield` — **1st validation under NEW tier-3 table** effective Sprint 57.53+)

**1st validation prediction (tier-3 `mechanical-greenfield` 0.50)**:
- If Option A simple (data cleanup + 1 autouse fixture) → actual ~30-45 min → ratio actual/committed-with-agent-factor ~0.6-0.9 likely BELOW band lower edge by 0-0.25 (single-data-point caution rule applies)
- If Option B/C requires non-trivial refactor → actual ~60-75 min → ratio ~1.25-1.6 ABOVE band by 0.05-0.4 (1st rollback-trigger > 1.20 candidate)
- If Option D requires updating many callers → actual ~90 min → ratio ~1.9 ABOVE band by 0.7 (rollback-trigger MET)

Per Sprint 57.52 retro Q4 rollback rule single-data-point caution: 1 data point < 0.7 OR > 1.20 → KEEP 0.50; need 2 consecutive to tighten/lift. Sprint 57.53 1st data point alone does NOT trigger structural change — flag for Sprint 57.54+ 2nd validation tracking.

---

## 7. Acceptance Criteria

| # | Criterion | Verify |
|---|---|---|
| AC-1 | `test_checkpointer_db::test_tenant_isolation` passes | `pytest tests/integration/agent_harness/state_mgmt/test_checkpointer_db.py::test_tenant_isolation -v` exit 0 |
| AC-2 | All 7 checkpointer DB tests pass | `pytest tests/integration/agent_harness/state_mgmt/test_checkpointer_db.py -v` 7/7 PASS |
| AC-3 | Full backend pytest baseline ALL-GREEN | `pytest --tb=short -q` 1759+N PASS + 0 fail |
| AC-4 | Root cause classification recorded in progress.md Day 1.1 | grep `Verdict:` + hypothesis H1-H5 status |
| AC-5 | Option A/B/C/D decision rationale recorded in progress.md Day 1.2 | grep `Decision:` + Option chosen |
| AC-6 | mypy --strict 0 errors | `mypy --strict src/` |
| AC-7 | 9 V2 lints preserved | `python scripts/lint/run_all.py` exit 0 |
| AC-8 | Vitest 607 preserved | `npm run test` 607 PASS |
| AC-9 | Vite build clean | `npm run build` exit 0 |
| AC-10 | LLM SDK leak 0 | covered by `run_all.py` |
| AC-11 | File MHist updated on edited files (≤100 char budget) | grep MHist lines |
| AC-12 | Day 0 三-prong report logged with drift findings | Read progress.md Day 0 |
| AC-13 | retrospective.md Q1-Q7 with **1st validation `mechanical-greenfield` 0.50 ratio** in Q4 + Q3 lesson on fixture contract | grep Q3 + Q4 |
| AC-14 | sprint-workflow.md MHist + matrix `medium-backend` 0.80 6th data point + §Active Activation history `mechanical-greenfield` 1st validation entry | grep |
| AC-15 | (Conditional) sprint-workflow.md §Common Risk Classes Risk Class E NEW row OR Risk Class C variant note added IF Option B/C/D | grep `Risk Class E` OR variant marker |

---

## 8. Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Investigation Steps 1-5 produce inconclusive evidence (H1-H5 all unconfirmed) | Medium | Fall back to Option A (data-only cleanup) + flag Phase 58.x deeper structural investigation as carryover AD; do NOT over-engineer Option C/D without evidence (per Karpathy §1 — Think Before Coding) |
| Test DB connection requires specific env vars not in current shell | Low | Day 0.8 Prong 1 verify `.env` + `DB_HOST=localhost`/`5432` set; if missing, fix env first |
| Sprint 53.6 SAVEPOINT precedent doesn't fit current case (DB row leak ≠ event loop singleton) | High | Plan §2.4 explicitly distinguishes; Option C is conditional, not default; don't apply pattern without confirmed root cause match |
| Test DB has rows from production migrations that should NOT be deleted | Low | Step 1 query result must show `code IN ('ISO_A','RT','TT',...)` — confined to test-only codes; DELETE WHERE clause is scoped, not blanket |
| Option B requires touching unrelated tests (broader refactor than scope) | Medium | If Option B turns out to touch > 3 files, downgrade to Option A + carryover AD for Option B as Phase 58.x cleanup |
| **`mechanical-greenfield` 0.50 1st validation lands > 1.20** | Medium | Rollback rule single-data-point caution: KEEP 0.50 + flag Sprint 57.54+ for 2nd validation; if 2 consecutive > 1.20 → propose 0.50 → 0.65 lift in Sprint 57.54 retro Q4 |
| **`mechanical-greenfield` 0.50 1st validation lands < 0.7** | Medium | Rollback rule single-data-point caution: KEEP 0.50 + flag Sprint 57.54+ for 2nd validation; if 2 consecutive < 0.7 → propose tier-4 refinement (extreme-mechanical sub-class) |
| `medium-backend` 0.80 6th data point continues confound pattern (still < 0.7 at agent layer) | Medium | Per Sprint 57.50 retro Q4 discipline: KEEP 0.80 class baseline; confound is resolved by sub-class layer; 6th data point feeds matrix for tracking only |
| Day 0.8 Prong 2 reveals `seed_tenant` was refactored commit() → flush() in a recent sprint without test DB cleanup (H4) | Medium | Document in progress.md Day 0 as Drift Class table NEW row candidate "Refactor-cleanup-gap" (future codification candidate for `sprint-workflow.md §Step 2.5 Prong 2`) — Karpathy §3 cleanup mindset to test data leftovers |
| Fix changes break other tests not currently failing | Low-Medium | AC-3 enforces full pytest sweep; if regression, revert + escalate |

---

## 9. Carryover ADs (for Sprint 57.54+ pickup)

- **`AD-AgentFactor-Tier-3-Validation-Sprint-57.54`** (NEW IF this sprint's 1st validation lands outside band; Sprint 57.54+ must be agent-delegated + classified as `mechanical-greenfield` to deliver 2nd validation data point)
- **`AD-Risk-Class-E-Codification`** (CONDITIONAL — only if Option B/C/D fix path triggers new Risk Class E entry in §Common Risk Classes)
- **`AD-Fixture-Contract-Enforcement-Test`** (CONDITIONAL — only if Option B chosen and regression test added; ensures future test design is guarded)
- `AD-medium-frontend-Baseline-Recalibration` (Sprint 57.49 carryover continues; 3rd data point pending at next medium-frontend sprint)
- `AD-TenantSettings-{HITLPolicies,FeatureFlags,Quotas,RateLimits}-Persistence` Phase 58.x (Sprint 57.48 carryover)
- `AD-TenantSettings-Identity-Persistence-Phase58` (Sprint 57.50 carryover)
- `AD-MockupCapture-Frontend-Visual-Diff-Pipeline` (Phase 58+ deferred)
- Potential NEW from Sprint 57.53 Day 0.8 三-prong findings

---

**Modification History**:
- 2026-05-26: Sprint 57.53 Day 0.1 — Initial draft (checkpointer test tenant isolation pre-existing fail investigation; closes Sprint 57.51 + 57.52 carryover; `medium-backend` 0.80 6th data point + tier-3 `mechanical-greenfield` 0.50 1st validation under NEW sub-class table effective Sprint 57.53+)
