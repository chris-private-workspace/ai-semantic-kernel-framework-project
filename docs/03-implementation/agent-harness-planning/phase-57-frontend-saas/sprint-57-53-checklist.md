# Sprint 57.53 — Checklist

[Plan](./sprint-57-53-plan.md) — Checkpointer test tenant isolation pre-existing fail investigation (Sprint 57.51 + 57.52 carryover closure); **1st validation under NEW tier-3 sub-class `mechanical-greenfield` 0.50** (effective Sprint 57.53+ per Sprint 57.52 retro Q4 SPLIT ACTIVATION); **`medium-backend` 0.80 6th data point** (5-pt mean 0.52 confound resolved by sub-class layer; KEEP baseline).

---

## Day 0 — Plan + 三-Prong Verify

### 0.1 Plan + Checklist Drafting
- [x] Plan written `sprint-57-53-plan.md`
- [x] Checklist written (this file)

### 0.8 Day 0 三-Prong Verify (Step 2.5 mandatory)

**Prong 1 — Path Verify** (~6 paths):
- [ ] `backend/tests/integration/agent_harness/state_mgmt/test_checkpointer_db.py` exists (test target file with `test_tenant_isolation` at L142-155)
- [ ] `backend/tests/conftest.py` exists (`db_session` fixture L41-62 + `seed_tenant` L65-73)
- [ ] `backend/src/agent_harness/state_mgmt/checkpointer.py` exists (DBCheckpointer source under test)
- [ ] `.claude/rules/sprint-workflow.md §Common Risk Classes` Risk Class C section exists (Sprint 53.6 module-level singleton precedent for SAVEPOINT pattern)
- [ ] `backend/src/infrastructure/db/models/identity.py` (per 09-db-schema-design.md §Group 1 + Sprint 57.50 D-DAY0-2 lesson) — Tenant ORM with `tenants.code` UNIQUE constraint
- [ ] `infrastructure/db/engine.py` — `get_session_factory` + `dispose_engine` (per-test rollback fixture machinery)

**Prong 2 — Content Verify** (~6 claims; per `sprint-workflow.md §Step 2.5 Prong 2` Drift Class table):
- [ ] **D-DAY0-1** `db_session` fixture in `conftest.py` L41-62 confirms `await session.rollback()` in finally + `await dispose_engine()` after; matches plan §2.2 baseline claim
- [ ] **D-DAY0-2** `seed_tenant` in `conftest.py` L65-73 confirms `await session.flush()` (NOT commit); contract docstring "Caller must NOT commit" verbatim; matches plan §2.2
- [ ] **D-DAY0-3** Sprint 53.6 SAVEPOINT precedent referenced in `sprint-workflow.md §Common Risk Classes Risk Class C` — confirm Sprint 53.6 cited + reset_service_factory autouse pattern documented (basis for Option C template in plan §4.3)
- [ ] **D-DAY0-4** `tenants` table schema — `code VARCHAR(64) UNIQUE NOT NULL` constraint confirmed in `identity.py` Tenant ORM (matches UniqueViolationError message `uq_tenants_code`)
- [ ] **D-DAY0-5** `test_checkpointer_db.py` `_build_session` helper at L49-59 uses positional `seed_tenant(db_session, code=tenant_code)` — confirm signature alignment with `seed_tenant` (no commit() in helper itself)
- [ ] **D-DAY0-6** **Constraint-metric delta grep** (per Sprint 57.52 Track A NEW Drift Class row 6): if any Day 1 fix path adds NEW pytest tests, baseline 1759 PASS will shift; record planned baseline shift in plan §6 Workload + Day 1.4 verify

**Prong 2.5 — Frontend Tree Depth Audit**: ✅ N/A (Sprint 57.53 backend test-infra investigation only; 0 frontend page changes)

**Prong 3 — Schema Verify** (per `sprint-workflow.md §Step 2.5 Prong 3`; AD-Plan-4 promoted Sprint 57.1):
- [ ] `tenants` table column `code VARCHAR(64) UNIQUE NOT NULL` in Alembic migrations history (no recent schema change to this column)
- [ ] `tenants` table FK CASCADE rules to `audit_log` / `users` / `sessions` (check if cascading triggers persist rows beyond rollback)
- [ ] Active triggers on `tenants` table: `SELECT * FROM information_schema.triggers WHERE event_object_table='tenants'` — confirm no WORM-style trigger that commits beyond rollback

**Drift findings catalog**:
- [ ] All findings logged to `progress.md` Day 0 entry per AD-Plan-2 promotion discipline (target: 5-6 GREEN + 0-2 YELLOW + 0 RED)
- [ ] Go/no-go decision recorded — GO if 0 RED; revise plan §Technical Spec if YELLOW shifts scope > 20%

### 0.9 Branch + Day 0 commit
- [ ] Branch `feature/sprint-57-53-checkpointer-tenant-isolation-investigation` created from main `43e5d8f7`
- [ ] Day 0 + Day 1 combined commit (per Sprint 57.46/47/48/49/50/51/52 small-scope precedent; OR split if Day 1 fix path is non-trivial)

---

## Day 1 — Implementation (Code-Implementer Agent Delegation — `mechanical-greenfield` 0.50 tier-3 1st validation)

### 1.1 Task 1.1 — Hypothesis Elimination Investigation

#### 1.1.1 Step 1 — Query test DB stale tenant rows
- [ ] Run Python async script (per plan §4.1 Step 1) querying `SELECT code, display_name, id, created_at FROM tenants WHERE code IN ('ISO_A','RT','TT','MM_SID','MM_TID','MISSING','SIZE','CHKPT_TEST','TEST_TENANT')`
- [ ] Record result in `progress.md` Day 1.1.1: codes present + count + `created_at` timestamps + same-hour clustering analysis

#### 1.1.2 Step 2 — Grep fixture-contract violators
- [ ] `cd backend && grep -rn "session\.commit\|db_session\.commit\|\.commit()" tests/ --include="*.py" | grep -v "rollback" | head -50`
- [ ] Catalog offending callers in `progress.md` Day 1.1.2 (file:line + commit context)

#### 1.1.3 Step 3 — Review `seed_tenant` git history
- [ ] `cd backend && git log --follow --oneline -- tests/conftest.py | head -20`
- [ ] Identify any commit() → flush() refactor + record sprint origin (H4 hypothesis evidence)

#### 1.1.4 Step 4 — Cross-reference SAVEPOINT precedent
- [ ] `grep -n "savepoint\|SAVEPOINT\|begin_nested" backend/tests/conftest.py backend/tests/**/conftest.py 2>/dev/null`
- [ ] Confirm whether Sprint 53.6 SAVEPOINT pattern already in use elsewhere in test infra

#### 1.1.5 Step 5 — Check triggers + WORM cascade
- [ ] Run Python async script (per plan §4.1 Step 5) `SELECT * FROM information_schema.triggers WHERE event_object_table='tenants'`
- [ ] Record trigger inventory in `progress.md` Day 1.1.5 (rule out H3 WORM hypothesis)

#### 1.1.6 Verdict
- [ ] Write hypothesis verdict in `progress.md` Day 1.1.6: H1/H2/H3/H4/H5 = confirmed / refuted / inconclusive
- [ ] Highlight which 1-2 hypotheses have strongest evidence

### 1.2 Task 1.2 — Option Decision Gate

- [ ] Review §4.2 decision criteria table mapping evidence → Option
- [ ] Choose Option A / B / C / D (or hybrid) — write decision + rationale in `progress.md` Day 1.2
- [ ] Confirm scope alignment with plan §6 Workload bottom-up est; if chosen Option drives > 20% scope expansion → escalate to user before Day 1.3

### 1.3 Task 1.3 — Fix Implementation (Option-dependent)

**Option A — Data-only cleanup + autouse fixture**:
- [ ] Manual one-shot `DELETE FROM tenants WHERE code IN ('ISO_A','RT','TT','MM_SID','MM_TID','MISSING','SIZE','CHKPT_TEST','TEST_TENANT')` against test DB (document runbook step in `progress.md` Day 1.3)
- [ ] Add `_cleanup_stale_test_tenants` autouse session-scope fixture to `backend/tests/conftest.py` (per plan §4.3 Option A template)
- [ ] File MHist 1-line entry on `conftest.py` (≤100 char budget per AD-Lint-MHist-Verbosity)

**Option B — Caller refactor + regression test**:
- [ ] Locate offending committer test/fixture (from Day 1.1.2 catalog)
- [ ] Refactor `await session.commit()` → `await session.flush()` (or remove entirely if not needed)
- [ ] Create NEW `backend/tests/test_fixture_contract.py` with `test_seed_tenant_does_not_persist_across_sessions` regression test
- [ ] File MHist 1-line entry on edited files

**Option C — SAVEPOINT pattern**:
- [ ] Wrap `db_session` fixture body in `async with session.begin_nested():` SAVEPOINT (per plan §4.3 Option C template)
- [ ] Verify pattern alignment with Sprint 53.6 `reset_service_factory` precedent (no double-rollback issue)
- [ ] File MHist 1-line entry on `conftest.py`

**Option D — Per-test code randomization**:
- [ ] Change `seed_tenant` default to `code=f"TEST_{uuid.uuid4().hex[:8]}"` (per plan §4.3 Option D template)
- [ ] Update existing test callers in `test_checkpointer_db.py` if explicit code assertions exist
- [ ] File MHist 1-line entry on `conftest.py` + edited test files

**Conditional — Risk Class codification** (Option B/C/D triggers):
- [ ] Append NEW row to `.claude/rules/sprint-workflow.md §Common Risk Classes` (Risk Class E "DB Row Leak Across Pytest Sessions") OR extend Risk Class C variant note
- [ ] File MHist 1-line entry on `sprint-workflow.md`

### 1.4 Day 1 Validation Sweep
- [ ] `cd backend && pytest tests/integration/agent_harness/state_mgmt/test_checkpointer_db.py -v` — **7/7 PASS** (target: full DBCheckpointer test class green)
- [ ] `cd backend && pytest --tb=short -q` — **1759+N PASS + 0 fail** (N depends on Option B/C regression tests; record actual baseline in progress.md)
- [ ] `cd backend && mypy --strict src/` — **0 errors / 310 files preserved**
- [ ] `python scripts/lint/run_all.py` — **9/9 GREEN** preserved (Sprint 57.52 baseline; total ~1.00s)
- [ ] `cd frontend && npm run lint` — **exit 0** (no `--silent` flag per Sprint 57.40 AD-Pre-Push-Lint-Silent-Suppression closure)
- [ ] `cd frontend && npm run build` — **Vite built; bundle sizes preserved** (0 frontend changes expected)
- [ ] `cd frontend && npm run test` — **Vitest 607 PASS / 118 test files preserved** (Sprint 57.52 baseline)
- [ ] LLM SDK leak scan — **0** (covered by V2 lint #5 `check_llm_sdk_leak.py` in `run_all.py` GREEN sweep)
- [ ] `git diff --stat HEAD` confirms: scope matches plan §5 File Change List (Option-dependent); **0 `.ts/.tsx` files touched**

### 1.5 Day 1 commit
- [ ] Commit: `feat(sprint-57-53): Day 0 + Day 1 — Checkpointer test tenant isolation fix (Option {A/B/C/D})` (Day 0 + Day 1 combined per small-scope precedent)
- [ ] Includes plan + checklist + progress (Day 0 三-prong + Day 1 投查 + Fix) + chosen Option's source changes

---

## Day 2 — Closeout (parent assistant)

### 2.1 Validation
- [ ] Full backend pytest suite passing (commit-time: 1759+N PASS + 0 fail) — **AD-Checkpointer-Test-Tenant-Isolation-PreExisting-Fail-Investigation CLOSED**
- [ ] Full frontend Vitest suite passing (commit-time: 607 PASS preserved Sprint 57.52 baseline)
- [ ] 9/9 V2 lints preserved (commit-time)
- [ ] All edited files have MHist 1-line entry (`git diff --stat` matches plan §5 File Change List Option-dependent expansion)

### 2.2 Retrospective
- [ ] Write `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-53/retrospective.md`
- [ ] Q1-Q7 6 必答 format (per Sprint 57.52 + earlier precedent)
- [ ] **Q3 (lessons)**: fixture contract finding + Option choice rationale + (conditional) propose Risk Class E codification OR Risk Class C variant note
- [ ] **Q4 (calibration)**:
  - `medium-backend` 0.80 6th data point (ratio + 6-pt mean + matrix decision per `When to adjust` rule)
  - tier-3 `mechanical-greenfield` 0.50 **1st validation** (ratio + single-data-point caution rule decision: KEEP / flag Sprint 57.54+ for 2nd validation)
- [ ] Q5 carryover candidate list (next sprint candidates per rolling planning §6)
- [ ] Q7 Design note extract: N/A SKIP (investigation/fix sprint NOT spike; same precedent as Sprint 57.10/57.47-52)

### 2.3 sprint-workflow.md updates
- [ ] File MHist entry (1-line; newest-first; ≤100 char budget)
- [ ] Matrix `medium-backend` 0.80 row updated to 6 data points (55.5=1.14 + 55.6=0.92 + 57.47=0.16 + 57.48=0.11 + 57.50=0.27 + 57.53=?; 6-pt mean + decision)
- [ ] §Active Activation history entry inserted after Sprint 57.52 retro Q4 (Sprint 57.53 retro Q4 — `mechanical-greenfield` 0.50 tier-3 1st validation outcome)
- [ ] §Active sub-class table tracking entry updated if applicable (no structural change expected for 1st validation per single-data-point caution)
- [ ] §Active History trail line extended with Sprint 57.53 1st validation entry
- [ ] (Conditional) §Common Risk Classes Risk Class E NEW row OR Risk Class C variant note IF Option B/C/D triggered codification

### 2.4 Memory + index
- [ ] `memory/project_phase57_53_checkpointer_tenant_isolation_fix.md` subfile created (full retro highlights + calibration + 3 ADs status + Option chosen + carryover ADs)
- [ ] MEMORY.md pointer entry inserted at TOP of §Project — Recent Sprints (~250-300 char quality pointer per Sprint Closeout Policy)

### 2.5 CLAUDE.md
- [ ] Current Sprint row updated (Sprint 57.52 → Sprint 57.53; navigator-only per Sprint Closeout Policy)
- [ ] Last Updated footer updated (Sprint 57.53 closeout note; AD-Checkpointer CLOSED + 1st validation outcome)

### 2.6 next-phase-candidates.md (REFACTOR-001 single-source for open items)
- [ ] Update `Updated` header (Sprint 57.53 closeout note; demoted Sprint 57.52 to "Previous Updated")
- [ ] Append Sprint 57.53 carryover section at TOP (AD-Checkpointer CLOSED + 1st validation outcome + carryover ADs from Sprint 57.53 retro Q5)
- [ ] Mark `AD-Checkpointer-Test-Tenant-Isolation-PreExisting-Fail-Investigation` as CLOSED in candidates list
- [ ] Mark `AD-AgentFactor-Tier-3-Validation-Sprint-57.53` as CLOSED with outcome ratio

### 2.7 PR + merge (post-commit; user action)
- [ ] Push branch + open PR (awaiting user authorization)
- [ ] Touch `.github/workflows/backend-ci.yml` header IF CI doesn't fire (paths-filter workaround; Sprint 57.51 + 57.52 PR #201/#202 precedent: backend test changes naturally fire CI)
- [ ] 🚧 Wait CI green (4 required checks: Backend E2E + Frontend E2E + Lint+Type+Test PG16 + v2-lints)
- [ ] 🚧 User merges (via GitHub UI when CI green)
- [ ] 🚧 Local cleanup (main fast-forward + delete feature branch post-merge)

### 2.8 Final
- [ ] Day 2 commit: `chore(sprint-57-53): Day 2 retro + closeout (medium-backend 0.80 6th data point + mechanical-greenfield 0.50 tier-3 1st validation outcome)`
- [ ] All Day 0-2.6 checklist items `[x]`; Day 2.7 PR + merge 🚧 pending user authorization; Day 2.8 final commit pending
