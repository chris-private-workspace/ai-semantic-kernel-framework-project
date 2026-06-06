# Sprint 57.87 Retrospective — C-12 IAM Block B: self-service tenant registration backend

**Closed**: 2026-06-06 (PR pending) · Branch `feature/sprint-57-87-register-backend` (from `main` `ab2adcc7`)
**Closes**: `AD-Auth-Register-Backend-IAM-Block-B-Phase58` (3rd C-12 spike)

---

## Q1 — What shipped?
A self-service tenant registration vertical slice: `RegistrationService.register` (tenant ACTIVE + first real admin Role + founding User + UserRole + audit), a public EXEMPT `POST /api/v1/tenants/register` (201 / 409 / 422), and the un-stubbed `/auth/register` wizard (201→`/auth/callback`, 409→slug-taken; AP-2 banner removed). No migration / no mockup-CSS change. The codebase's **first real `Role(...)` creation**.

## Q2 — Estimate vs actual (calibration)
- **Agent-delegated: no** (parent-direct — security-sensitive public pre-auth tenant-creation + admin-role grant). `agent_factor` 1.0 → 3-segment form.
- Scope class **`iam-backend-spike` 0.65** — ADOPTED this sprint per the 57.86 carryover `AD-Sprint-Plan-IAM-Backend-Spike-Class` (register = "the next IAM backend spike"). **1st validation data point.**
- Bottom-up ~8.5 hr → committed ~5.5 hr (×0.65). Actual core work ≈ committed (~5.5 hr; smaller than 57.86 — no migration, no mockup extension, frontend mostly existed). **+ environmental overhead**: a concurrent-session branch collision (see Q4) cost ~30-45 min of mis-diagnosis (a phantom mypy "registration missing" that was actually the wrong branch). Excluding the anomaly ratio ≈ **1.0**; including it ≈ **1.1-1.2**.
- **Verdict**: KEEP `iam-backend-spike` 0.65 (single data point; the over-run was environmental, not a class-estimation miss). Flag the 2nd `iam-backend-spike` sprint (MFA/recovery) for confirmation per the 3-sprint window rule.

## Q3 — What went well
- Day-0 three-prong (Explore + parent re-verify) caught the 2 real design forks BEFORE coding (tenant-state + admin-role-seed) → AskUserQuestion locked them → zero rework on scope.
- The `invites.accept` pattern was a clean mirror (User+UserRole+audit + `_set_tenant`) → the service was small + correct first-draft.
- The Day-2 cut-line discipline held (service + 6 tests green before any HTTP/UI wiring).
- 8 drift findings cataloged Day-0 (D1-D8) all proved accurate; D5/D9 (RLS-untestable-under-superuser) was pre-known from 57.85 → isolation asserted app-layer from the start (no failed-test surprise on the service test; the integration test was app-layer too).

## Q4 — What to improve / anomalies
- **🔴 Concurrent-session branch collision** — mid-Day-3, the working tree was switched to `chore/drive-through-acceptance-principle` by another Claude session sharing the same repo directory. My uncommitted Day-3 edits landed on that wrong branch; `registration.py` (committed on 57.87) was absent → a phantom mypy `import-untyped` error that I first mis-chased as an editable-install staleness issue (~30-45 min) before `git status` revealed the wrong branch. **Recovery** (no data loss): `git stash -u` → restore chore worktree clean → checkout 57.87 → `git stash pop` (the 2 shared files were byte-identical across branches → zero conflict). **Lesson**: when a first-party import shows mypy "installed missing py.typed" + the source-file count doesn't increment, check `git branch` FIRST (a wrong-branch/missing-file is far more likely than an editable-install quirk). User chose to continue with frequent defensive commits. Two-sessions-one-worktree is the root environmental hazard (recommend separate git worktrees/clones per session).
- After the collision, frequent per-Day commits (Day-3 backend, Day-3 frontend separately) limited the blast radius — good defensive habit under a shared worktree.

## Q5 — Decisions (rolling)
D1 tenant ACTIVE-now (skip stub workflow) · D2 seed real admin Role+UserRole (JWT-effectiveness deferred) · D3 service in identity/ · D4 no password (OIDC-first, mockup has none) · D5 plan→meta_data (enum only ENTERPRISE) · D6 no migration. All in design note `23-iam-registration-spike.md` §2.

## Q6 — Gates
mypy `src/` **0/344** · flake8 0 · `run_all.py` **10/10** (check_rls_policies green — no new table) · pytest **2214 passed** / 4 skipped (+12: 6 service + 6 integration) · frontend lint(no `--silent`)+build · Vitest **763 passed** · check:mockup-fidelity ✓ (oklch baseline **53 UNCHANGED**; styles-mockup.css byte-identical).

## Q7 — Carryovers → next-phase-candidates.md
NEW: `AD-RBAC-DB-To-JWT-Wiring-Phase58` (seeded admin role not yet authz-effective) · `AD-Register-OIDC-User-Linkage-Phase58` (register-user vs OIDC-user dup) · `AD-Tenant-Plan-Tiers-Phase58` (TenantPlan only ENTERPRISE). Carry: MFA / recovery / lockout / invite-email / admin-invites-list / seed_default_roles full promotion. Process: the wrong-branch-vs-editable-install diagnostic lesson (fold into `sprint-workflow.md` only if it recurs — single occurrence; root cause is the shared-worktree setup, not a workflow gap).

---

## Design Note Extract (spike sprint — §Step 5.5)

**File**: `docs/03-implementation/agent-harness-planning/23-iam-registration-spike.md`
**Verified ratio (estimated)**: ~95% (every §3 invariant has file:line + a named test)
**8-Point Quality Gate**:
- [x] 1. Section header → spike user story (§1 maps US-1..US-4)
- [x] 2. file:line per claim (§3 table)
- [x] 3. Decision matrix (§2 — 6 decisions, options + rejection rationale)
- [x] 4. Verification command (§3 — pytest + vitest commands)
- [x] 5. Test fixture reference (§3 — `conftest.py` db_session + `_build_app`)
- [x] 6. Open-invariant boundary (§5 — verified vs deferred clearly split)
- [x] 7. Rollback path (§6 — additive revert, no DB rollback, <30 min)
- [x] 8. 17.md cross-ref (§4 — N/A justified, same call as 57.84/85/86)

**Reviewer pass**: self-review (parent).
