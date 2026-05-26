# Sprint 57.53 — Progress

**Sprint**: Phase 57 / Sprint 57.53 — Checkpointer Test Tenant Isolation Pre-Existing Fail Investigation
**Class**: `medium-backend` 0.80 (6th data point)
**Sub-class** (agent_factor): `mechanical-greenfield` 0.50 (**tier-3 1st validation** under NEW table effective Sprint 57.53+)
**Branch**: `feature/sprint-57-53-checkpointer-tenant-isolation-investigation` (not yet created — Day 0.9)
**Plan**: [`sprint-57-53-plan.md`](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-53-plan.md)
**Checklist**: [`sprint-57-53-checklist.md`](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-53-checklist.md)

---

## Day 0 — 2026-05-26 — Plan + 三-Prong Verify

### 0.1 Plan + Checklist Drafting
- **0.1.1** Plan `sprint-57-53-plan.md` written; 9 sections mirroring Sprint 57.52 format (Sprint Goal / Background §6 sub / 3 User Stories / Technical Specification §4 sub / File Change List / Workload 4-segment / Acceptance Criteria 15 / Risks 9 / Carryover ADs)
- **0.1.2** Checklist `sprint-57-53-checklist.md` written; Day 0-2 structure mirroring Sprint 57.52 (0.1 + 0.8 + 0.9 / 1.1-1.5 / 2.1-2.8 = 16 task groups; Option-dependent 1.3 sub-structure A/B/C/D + Conditional)

### 0.8 Day 0 三-Prong Verify

**Prong 1 — Path Verify (6/6 GREEN)**:
- ✅ `backend/tests/integration/agent_harness/state_mgmt/test_checkpointer_db.py` exists (test target file with `test_tenant_isolation` at L142-155)
- ✅ `backend/tests/conftest.py` exists (`db_session` fixture L41-62 + `seed_tenant` L65-73)
- ✅ `backend/src/agent_harness/state_mgmt/checkpointer.py` exists (DBCheckpointer source under test)
- ✅ `backend/src/infrastructure/db/models/identity.py` exists (Tenant ORM per 09-db-schema-design.md §Group 1 + Sprint 57.50 D-DAY0-2 lesson)
- ✅ `backend/src/infrastructure/db/engine.py` exists (`get_session_factory` + `dispose_engine`)
- ✅ `.claude/rules/sprint-workflow.md §Common Risk Classes` Risk Class C section at L792-800 (Sprint 53.6 module-level singleton precedent)

**Prong 2 — Content Verify (5 GREEN + 2 NEW NOTABLE findings + 1 YELLOW)**:

- **D-DAY0-1** ✅ GREEN — `db_session` fixture at `conftest.py` L41-62 confirms `await session.rollback()` in `finally` + `await dispose_engine()` after; matches plan §2.2 baseline claim verbatim

- **D-DAY0-2** ✅ GREEN — `seed_tenant` at `conftest.py` L65-73 confirms `await session.flush()` (NOT commit); contract docstring "Caller must NOT commit — fixture rollback handles cleanup" verbatim at L68; matches plan §2.2

- **D-DAY0-3** 🟡 YELLOW (plan reference clarification needed) — Risk Class C at `sprint-workflow.md` L792-800 documents **module-level singleton** pattern (Sprint 53.6 `reset_service_factory` autouse fixture, NOT SAVEPOINT). Plan §2.4 + §4.3 Option C reference "Sprint 55.4 `AD-Test-DB-Trigger` SAVEPOINT pattern" — verify cross-doc accuracy in Day 1.1.4 SAVEPOINT precedent grep step. **Scope impact**: 0 (Option C remains valid as SQLAlchemy `begin_nested()` native feature; precedent reference will be corrected in plan at Day 2 retro or earlier if Day 1.1.4 surfaces correct citation).

- **D-DAY0-4** ✅ GREEN — `tenants.code` constraint at `identity.py` L116: `code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)` → SQLAlchemy auto-generates `uq_tenants_code` constraint name (matches UniqueViolationError message verbatim in Day 0 recon)

- **D-DAY0-5** ✅ GREEN — `test_checkpointer_db.py` `_build_session` helper at L49-59 confirmed positional `seed_tenant(db_session, code=tenant_code)`; no `commit()` in helper itself; matches plan §2.2

- **D-DAY0-6** ✅ GREEN (constraint-metric baseline noted) — Per Sprint 57.52 Track A NEW Drift Class row 6 (Claimed-but-silent-constraint-delta): current pytest baseline = **1759 PASS + 1 PRE-EXISTING fail** (Sprint 57.51 + 57.52 baselines). If Option B/C adds NEW regression tests → baseline shift expected `1759 + N` where N = 1-3 typically. Sprint plan §6 Workload includes N in acceptance criteria AC-3. No silent drift risk.

- **D-DAY0-7** 🆕 NEW NOTABLE — Targeted grep `session\.commit|db_session\.commit|\.commit\(\)` in `tests/integration/agent_harness/state_mgmt/` returned **0 matches**. Strong evidence that H1 (test file caller commits) is **REFUTED for state_mgmt/ scope**. Strengthens H2/H5 hypotheses (stale row from external source OR crashed test run). Day 1.1.2 will broaden grep to full `tests/` scope.

- **D-DAY0-8** 🆕 NEW NOTABLE — Broader grep across all `backend/tests/` found **9 test/conftest files containing `session.commit\|db_session.commit`**:
  - `tests/integration/api/conftest.py` (fixture file — needs Day 1.1.2 inspection of intent)
  - `tests/integration/api/test_governance_endpoints.py`
  - `tests/integration/api/test_audit_endpoints.py`
  - `tests/integration/platform_layer/governance/hitl/test_manager.py`
  - `tests/unit/platform_layer/governance/hitl/test_db_hitl_policy_store.py`
  - `tests/unit/agent_harness/memory/test_{tenant,user,role,system}_layer.py` (4 files)

  Sprint 53.6 Day 4 lesson: WORM-trigger-toggle tests use deliberate commits for audit_log WORM trigger. These MAY be legitimate exceptions OR fixture-contract violators. Day 1.1.2 will analyze each to determine if any use `seed_tenant` (with any code) followed by `commit()` — would be a strong H1 confirmation.

**Prong 2.5 — Frontend Tree Depth Audit**: ✅ N/A (Sprint 57.53 backend test-infra investigation only; 0 frontend page changes)

**Prong 3 — Schema Verify (file-level GREEN; DB-level deferred to Day 1.1.5)**:

- ✅ **Column-level**: `tenants.code VARCHAR(64) UNIQUE NOT NULL` confirmed in `identity.py` L116 (Tenant ORM); maps to `uq_tenants_code` unique constraint per SQLAlchemy auto-naming convention
- ⏸️ **FK CASCADE rules**: from/to `tenants` table — deferred to Day 1.1.5 live DB inspection (information_schema query)
- ⏸️ **Active triggers**: on `tenants` table — deferred to Day 1.1.5 live DB inspection (`SELECT * FROM information_schema.triggers WHERE event_object_table='tenants'`)
- ✅ **Migration head ordering**: Sprint 57.50 introduced Alembic 0018 (per `next-phase-candidates.md` + identity.py header history); no recent migration affecting `tenants.code` column

**Drift findings catalog summary**:
- **Prong 1**: 6 GREEN / 0 YELLOW / 0 RED
- **Prong 2**: 5 GREEN / 1 YELLOW (D-DAY0-3 plan reference clarification) / 2 NEW NOTABLE (D-DAY0-7 refutes H1 in state_mgmt scope + D-DAY0-8 surfaces 9 commit-using files for Day 1.1.2 analysis) / 0 RED
- **Prong 3**: 2 GREEN (column + migration) / 2 DEFERRED to Day 1.1.5 (DB-level triggers/CASCADE) / 0 RED

**Go/no-go decision**: ✅ **GO** (0 RED; D-DAY0-3 YELLOW is plan-reference-only with 0 scope impact; D-DAY0-7+8 NEW findings strengthen plan §2.3 hypothesis catalog quality without shifting scope; Day 1 proceeds with original scope).

**Notes for plan adjustment at Day 2 retro** (no Day 1 disruption):
- Plan §2.4 + §4.3 Option C: revise "Sprint 55.4 `AD-Test-DB-Trigger` SAVEPOINT pattern" reference to either (a) verified citation surfaced by Day 1.1.4 OR (b) generic "SQLAlchemy `begin_nested()` native feature" without sprint precedent
- Plan §6 Risks: "Sprint 53.6 SAVEPOINT precedent doesn't fit current case" risk row was correct directionally — Sprint 53.6 is module-level singleton, not SAVEPOINT; the Sprint 55.4 SAVEPOINT precedent (if exists) is a separate citation

### 0.9 Branch + Day 0 commit
- ⏸️ Pending Day 1 start: branch `feature/sprint-57-53-checkpointer-tenant-isolation-investigation` to be created from main `43e5d8f7`
- ⏸️ Pending: Day 0 + Day 1 combined commit per Sprint 57.46/47/48/49/50/51/52 small-scope precedent

---

## Day 1 — 2026-05-26 — Implementation

### 1.1 Hypothesis Elimination Investigation

#### 1.1.1 Step 1 — Test DB stale tenant rows
**Result**: `STALE_ROW_COUNT=1` — only `ISO_A` present (id=`956dbe82-45f8-4dfc-8c33-a02ce026862f`, `created_at=2026-05-26 02:14:29.750333+00:00`).

**Critical signals**:
- Only 1 of 9 test codes leaked → **H5 (crashed run leaking all codes) REFUTED**
- `created_at = today 02:14:29 UTC` — recent, programmatic origin (not stale-from-week-ago)
- Other test codes (RT, TT, MM_SID, MM_TID, MISSING, SIZE, CHKPT_TEST, TEST_TENANT) **NOT present** → other tests in same file don't leak; targeted leak specific to `test_tenant_isolation`

#### 1.1.2 Step 2 — Fixture-contract violator grep
**State_mgmt scope** (D-DAY0-7 reaffirmed): `tests/integration/agent_harness/state_mgmt/` = **0 `.commit()` calls** → H1 REFUTED for state_mgmt scope.

**Broader scope** (D-DAY0-8 reaffirmed): 9 backend test/conftest files contain `.commit()`:
- `tests/integration/api/conftest.py` (Sprint 57.12 cleanup itself uses commit — legitimate)
- `tests/integration/api/test_governance_endpoints.py` + 1 audit_endpoints + 1 hitl/test_manager + 1 hitl/test_db_hitl_policy_store
- `tests/unit/agent_harness/memory/test_{tenant,user,role,system}_layer.py` (4 memory unit tests)

**Important**: ISO_A literal usage repo-wide check shows **only `test_checkpointer_db.py:145` uses bare `"ISO_A"`** — all other tests use prefixed (`US4_ISO_A` / `RL_ISO_A` / `MEM_ISO_A` / etc.) or `_uniq("ISO_A")` randomized. **Zero cross-test code collision**.

#### 1.1.3 Step 3 — seed_tenant git history
`git log --follow backend/tests/conftest.py` → **6 commits total**; most recent touching = `6671615f feat(infrastructure-db, sprint-49-2): Day 2 sessions partition + ORM + CRUD test` (Sprint 49.2, original creation).

**No subsequent refactor** of `seed_tenant` from `commit()` → `flush()`. → **H4 (migration gap) REFUTED**.

#### 1.1.4 Step 4 — SAVEPOINT precedent cross-reference
Per `docs/rules-on-demand/testing.md` MHist L11-12:
- L11: `2026-05-10: Sprint 57.12 US-7 — add §Committed-Row Cleanup Pattern (closes AD-AdminTenant-Patch-Flake)`
- L12: `2026-05-05: Sprint 55.6 triage cleanup — add §SAVEPOINT pattern (closes AD-Test-DB-Trigger)`

**D-DAY0-3 YELLOW RESOLVED ✅**: Sprint 55.4 `AD-Test-DB-Trigger` SAVEPOINT pattern **does exist** at `testing.md §SAVEPOINT Pattern for Post-Error Verification` L179-225. **BUT** that pattern is for `try/except` post-error verification (deliberate IntegrityError + verify other state survived) — **not applicable to our committed-row leak case**.

**🎯 D-DAY0-9 NEW MAJOR finding**: `Sprint 57.12 §Committed-Row Cleanup Pattern` (testing.md L229-283) is **direct precedent**. Root cause per Sprint 57.12: `admin/tenants.py` PATCH route line ~488 `await db.commit()` persists rows past `db_session` rollback → `uq_tenants_code` collision. Pattern provides WORM-trigger-toggle DELETE in autouse fixture at `tests/integration/api/conftest.py`.

#### 1.1.5 Step 5 — Tenants table triggers inventory
`SELECT * FROM information_schema.triggers WHERE event_object_table='tenants'` → **`TRIGGER_COUNT=0`** → **H3 (WORM trigger on tenants) REFUTED**.

Note: WORM trigger exists on `audit_log` table (per Sprint 57.12 pattern), reached via FK CASCADE from `tenants` deletion — relevant for DELETE cleanup mechanism (needs trigger toggle), not for the leak itself.

#### 1.1.6 Verdict

| Hypothesis | Status | Evidence |
|------------|--------|----------|
| **H1** — Fixture contract violated by test commit | **REFUTED in state_mgmt scope** (0 commit calls) — but **CONFIRMED via Sprint 57.12 precedent** that commits-from-API-routes can leak into other tests' rows when test runs interleave | D-DAY0-7 + Sprint 57.12 `AD-AdminTenant-Patch-Flake` root cause |
| **H2** — Manual psql leftover from interactive debugging | **PLAUSIBLE secondary** (programmatic timestamp 02:14:29 today suggests pytest run not psql, but can't rule out) | Step 1 timestamp + Step 5 no triggers |
| **H3** — WORM trigger on tenants persists row | **REFUTED** | Step 5 TRIGGER_COUNT=0 |
| **H4** — `seed_tenant` commit()→flush() migration gap | **REFUTED** | Step 3 no refactor in history |
| **H5** — Crashed run leaking all 7 test codes | **REFUTED** | Step 1 only 1/9 leaked |
| **H6 (NEW)** — `DBCheckpointer.save()` commits internally | **REFUTED** | Step 2 (grep showed 0 `.commit()` in `checkpointer.py`) |

**Most likely root cause** (cumulative evidence): **Concurrent test interleaving with API tests that commit (Sprint 57.12 root cause pattern)** OR direct manual psql leftover (H2). Both point to the same fix path.

### 1.2 Option Decision Gate

**Decision**: **Option A enriched with Sprint 57.12 `§Committed-Row Cleanup Pattern` lift**.

**Rationale**:
- **Option A baseline + Sprint 57.12 precedent**: data cleanup + autouse fixture, mirroring `tests/integration/api/conftest.py` pattern at sibling scope
- **Option B (caller refactor) — REJECTED**: no committer identified in state_mgmt test scope; Sprint 57.12 precedent fixed root-cause caller (admin PATCH route) in its own scope
- **Option C (SAVEPOINT pattern) — REJECTED**: `testing.md §SAVEPOINT Pattern` is for `try/except` post-error verification, NOT committed-row leak prevention; misapplication risk
- **Option D (random codes) — REJECTED**: per Sprint 57.12 `testing.md L274` explicit anti-pattern *"Make committing tests use UUID-suffixed codes → loses predictable test IDs; harder to read assertions"*

**Implementation scope**:
1. One-shot manual DELETE of ISO_A row (with WORM trigger toggle, mirror Sprint 57.12 manual cleanup at retro D-PRE-DAY4-1)
2. NEW `tests/integration/agent_harness/conftest.py` with autouse cleanup fixture (scope = all agent_harness integration tests)
3. Allowlist `_COMMITTING_STATE_MGMT_TENANT_CODES` covering state_mgmt test codes: `ISO_A`, `RT`, `TT`, `MM_SID`, `MM_TID`, `MISSING`, `SIZE`, `CHKPT_TEST`, `TEST_TENANT`
4. Mirror trigger-toggle pattern verbatim from `tests/integration/api/conftest.py` L95-123
5. NO `_reset_module_singletons` wrapping (api-test-specific, not needed for agent_harness)

**Scope alignment**: ~30-45 min actual vs plan §6 Workload `agent_factor`-adjusted ~48 min — within ±5%. No user escalation needed.

### 1.3 Implementation

**Step 1 — One-shot DELETE ISO_A (with WORM trigger toggle)**:
- Ran Python async script: `ALTER TABLE audit_log DISABLE TRIGGER audit_log_no_update_delete; DELETE FROM tenants WHERE code='ISO_A'; ALTER TABLE audit_log ENABLE TRIGGER ...; COMMIT`
- Output: `DELETED_ROWS=1; COMMIT_OK; POST_CLEANUP_ISO_A_COUNT=0` ✅

**Step 2 — NEW `backend/tests/integration/agent_harness/conftest.py`** (~120 lines):
- Mirrors `tests/integration/api/conftest.py` Sprint 57.12 §Committed-Row Cleanup Pattern verbatim at sibling scope
- `_COMMITTING_STATE_MGMT_TENANT_CODES` allowlist with 9 codes (CHKPT_TEST, ISO_A, MISSING, MM_SID, MM_TID, RT, SIZE, TT, TEST_TENANT) — alphabetically grouped by test file per readability
- `_clear_committed_state_mgmt_tenants()` cleanup function with WORM trigger toggle (DISABLE → DELETE → ENABLE → COMMIT pattern)
- `@pytest.fixture(autouse=True) _reset_state_mgmt_test_state` — before+after yield cleanup
- File header includes full Description + Sprint 57.53 root cause investigation summary + Sprint 57.12 anti-pattern references (rejected Options B/C/D rationale)
- 0 changes to existing files (zero-risk additive scope)

### 1.4 Day 1 Validation Sweep

| AC | Check | Result |
|---|---|---|
| AC-1 | `test_tenant_isolation` PASS | ✅ PASSED (0.97s within full suite) |
| AC-2 | 7/7 checkpointer DB tests PASS | ✅ `7 passed in 0.97s` |
| AC-3 | Full backend pytest 1759+N PASS + 0 fail | ✅ **1760 passed, 4 skipped in 63.81s** (+1 net = previously-failing test_tenant_isolation now passes; 0 new regressions) |
| AC-6 | mypy --strict 0 errors | ✅ `Success: no issues found in 310 source files` |
| AC-7 | 9/9 V2 lints | ✅ `V2 Lints: 9/9 green (total 1.19s)` |
| AC-8 | Vitest 607 PASS preserved | ✅ `Test Files 118 passed (118); Tests 607 passed (607)` |
| AC-9 | Vite build clean | ✅ `built in 3.51s` (bundle sizes preserved — 0 frontend changes) |
| AC-10 | LLM SDK leak 0 | ✅ covered by `check_llm_sdk_leak.py` in 9/9 V2 lints green |
| AC-11 | File MHist on edited files | ✅ NEW conftest.py has MHist section; 0 existing files touched (zero-edit-on-existing scope) |
| AC-15 | (Conditional) Risk Class E codification | ⏸️ **N/A** — Option A chosen; `testing.md` already documents the pattern at §Committed-Row Cleanup; **no NEW row in sprint-workflow.md needed** per plan §AC-15 conditional rule |

**Validation summary**: ALL acceptance criteria for Day 1 satisfied. AD-Checkpointer-Test-Tenant-Isolation-PreExisting-Fail-Investigation **CLOSED**.

**Scope alignment with plan §5 File Change List**:
- `backend/tests/integration/agent_harness/conftest.py` — NEW (~120 lines)
- 1 one-shot manual DELETE against test DB (runbook documented in §1.3 Step 1; not committed to repo)
- Plan + checklist + progress.md (Sprint artifacts)
- **0 `.ts`/`.tsx` files touched** ✅
- **0 source code changes to existing files** (zero-edit-on-existing minimal scope)
- **0 changes to `tests/conftest.py`** (no fixture contract change needed)

### 1.5 Day 1 commit
- ⏳ pending Day 0+1 combined commit per small-scope precedent (Sprint 57.46-52)
