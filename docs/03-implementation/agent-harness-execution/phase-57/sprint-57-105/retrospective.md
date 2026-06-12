# Sprint 57.105 Retrospective — RBAC DB→JWT wiring

**Date**: 2026-06-12
**Branch**: `feature/sprint-57-105-rbac-jwt-wiring` (base `main` `ed52d435`)
**Commits**: `7e6d4fc7` (Day 0-2 impl) + `3213a6b9` (Day 3 drive-through docs) + closeout

## Q1 — What shipped?

DB role grants are now JWT-effective at login. NEW `RBACManager.get_user_role_codes(*, user_id,
tenant_id, session)` (tenant-scoped `Role JOIN UserRole`, sorted+deduped); the OIDC callback
(`roles=["user"]` literal retired) + password-login (`_PASSWORD_LOGIN_ROLES` deleted) both issue
`sorted({"user", *db_codes})` into the JWT claim AND the login response body; dev-login untouched
(dev-only, prod 404). Drive-through PASS with **zero dev-login**: register 201 → set_password
(D11) → password-login 200 → sidebar "DT Founder / admin" (ISSUE-6 closed) → Model Policy PUT
200 (first admin write ever driven without dev-login) → role-less JWT 403. Closes
`AD-RBAC-DB-To-JWT-Wiring-Phase58`. CHANGE-072 + note 23 §5 RESOLVED.

## Q2 — Estimate accuracy (calibration)

- Plan §7: bottom-up ~10.5 hr → class-calibrated commit ~6.8 hr (`iam-backend-spike` 0.65,
  **2nd validation data point**); **Agent-delegated: no** (parent-direct, `agent_factor = 1.0`).
- Actual ≈ 6.5 hr (Day 0 ~1.0 / Day 1 ~1.5 / Day 2 ~2.0 incl. Docker-down recovery / Day 3 ~1.5
  / Day 4 ~0.5) → **ratio ≈ 0.95 IN band** (0.7-1.2).
- 3-sprint window: 57.87 ≈1.0 + 57.105 ≈0.95 → 2 consecutive IN band → **KEEP 0.65**; matrix row
  added to sprint-workflow.md (the class had been proposed in plans but never landed in the matrix).
- D5 (CONVERT list empty) + D11 (no register password) both shifted scope DOWN/UP in offsetting
  ways: tests became extend-only (−), but the drive-through gained the out-of-band set_password
  leg (+). Net wash — the 0.65 haircut absorbed both.

## Q3 — What went well?

- **Option A design held end-to-end**: single truth source = the JWT; gate code zero-diff; FE
  zero-diff (`authStore` self-healed via the login payload — D10 verified, D2 made it immediate).
- **Day-0 three-prong ROI again**: D5 emptied the conversion list (0 conversions / 0 deletions);
  D1 grep-proved exactly 3 issue sites (no hidden 4th); D11 caught the no-password-at-register
  drift at Day 2 instead of mid-drive-through.
- Drive-through proved BOTH poles (admin 200 / role-less 403) on the REAL gate with the REAL C1
  admin surface — not a probe.

## Q4 — What to improve / lessons?

- **D11 class**: plan §0 asserted "register stores the password" from the 57.86/57.87 memory
  blend — a Prong-2 grep on the register request schema would have caught it at Day 0 (it was
  caught at Day 2 writing the chain test). Lesson folds into the existing
  claimed-but-missing-storage-path drift class (grep the REQUEST body schema too, not just storage).
- **D12 class**: checklist committed to a 17.md row that note 23 §4 precedent forbids
  (identity ∉ the 11+1 registry). Plan-drafting should cross-check "docs to update" against the
  target doc's own scope rules. Resolved by precedent, annotated, no harm.
- Pre-existing FE carryover surfaced by the drive-through: sidebar tenant-switcher/header render
  fixture "acme-prod" regardless of the real tenant → logged as
  `AD-FE-Tenant-Display-Fixture-Phase58` in next-phase-candidates.

## Q5 — Carryover / next

- `AD-Register-OIDC-User-Linkage-Phase58` — still open (why the drive-through spine is
  password-login).
- `AD-FE-Tenant-Display-Fixture-Phase58` (NEW) — sidebar/header tenant label is fixture.
- dev-login `_DEV_LOGIN_ROLES` hardcode — dev-only debt, documented in CHANGE-072.
- Claim staleness until re-login — documented invariant (re-login refreshes; no token refresh).
- **Next slice per interleave decision: C3** (harness-deepening Workflow C).

## Q6 — Discipline self-check

1. Server-Side First ✅ · 2. LLM Neutrality ✅ (identity layer; no LLM surface) · 3. CC 不照搬 ✅
· 4. 17.md single-source ✅ (N/A by precedent — D12) · 5. 範疇歸屬 ✅ (platform_layer/identity ×
api/v1) · 6. anti-patterns ✅ (retired 2 hardcodes; 0 Potemkin; negative pole tested) · 7. workflow
✅ (plan → checklist → Day 0 → code → drive-through → closeout) · 8. file header ✅ (MHist 1-line)
· 9. multi-tenant ✅ (tenant-scoped query + cross-tenant isolation test). Rolling: no future plans
pre-written ✅; no unchecked items deleted ✅.

## Q7 — Design Note Extract

N/A — gap-fix continuation, NOT a spike (per §Step 5.5 "When NOT to apply"). The verified
invariant lands as an EDIT to existing note 23 §5 (RESOLVED entry) + CHANGE-072; no new note.
