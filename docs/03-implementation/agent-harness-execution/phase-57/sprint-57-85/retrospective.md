# Sprint 57.85 Retrospective — C-12 IAM Block B: invites vertical spike

**Sprint**: 57.85
**Closed**: 2026-06-06
**Branch**: `feature/sprint-57-85-iam-invites`
**Closes**: `AD-Auth-Invite-Backend-IAM-Block-B-Phase58` (invites leg of C-12 Block B). First spike of C-12.

---

## Q1. Goal achieved?

✅ Yes. The invites vertical slice is live end-to-end:
- NEW `invites` table (migration `0026`, RLS two-policy + guest-lookup sentinel escape) + `InvitesService` (create / get_metadata / accept / revoke) + 3 endpoints (admin create + guest GET/accept, exempt) + frontend invite page wired to the real backend (fixture + AP-2 banner removed).
- DB-backed opaque token (user choice over JWT): revocable / single-use / expiring; raw token returned once, only sha256 stored.
- `password` accepted-not-stored (split to 57.86 per the new-info AskUserQuestion round).
- Gates: mypy 0/339 · full pytest **2179 passed** · run_all 10/10 · Vitest **757** · check:mockup-fidelity ✓ (oklch baseline 50 unchanged).

## Q2. Estimate accuracy

- Plan: bottom-up ~9 hr → class-calibrated commit ~7.2 hr (`medium-backend` 0.80, `agent_factor` 1.0 parent-direct).
- Actual: ~8.5-9.5 hr (Day-0 analysis+Explore+plan/checklist ~1.5; Day-1 schema ~1; Day-2+3 service+endpoints+tests ~3.5 incl. 3 lint/mypy fix cycles + 2 test-failure fixes; frontend ~1.5; closeout ~1.5).
- Ratio actual/committed ~1.2-1.3 — **above the band**. This is the **greenfield-domain caveat** materializing exactly as the plan flagged: `medium-backend`'s recent pattern-reuse mean ran ~0.5 (over-estimating), but a *greenfield IAM* spike (no prior invites pattern, new middleware exempt path, new RLS table) ran ~2x that. The estimate held for the pure mechanical parts; the over-run was the design-discovery tail (token mechanism, guest-context RLS, password-deferral pivot, the two integration-test corrections).
- **Calibration action**: one greenfield-domain `medium-backend` data point at ratio ~1.25. NOT enough to create an `iam-backend-spike` class (diversification discipline needs 2+ points). If 57.86 (credentials, also IAM greenfield) lands > 1.0 again → propose `iam-backend-spike` ~0.55-0.65.

## Q3. What went well

- **Day-0 三-prong + Explore caught the real shape early**: the reusable Block-A infra (JWT/tenant/RBAC/audit/ORM), the frontend contract, the per-tenant email uniqueness (D2), the guest-context RLS wrinkle (D3), and the password-no-store reality (D4) were all surfaced before code — so the plan was built on reality, and the 2 AskUserQuestion rounds locked scope before plan v1 (zero plan-rewrite cycle).
- **Reusing the billing_outbox (57.84) sentinel-escape RLS pattern** I had just built made the guest-context-RLS design a known quantity (set sentinel for the token lookup → switch to the invite's tenant for writes), rather than a fresh problem.
- **The password new-info round was worth it**: surfacing that the login page is OIDC-only + mockup forbids a password field + no UI consumer this sprint changed the user's initial "add password" answer to "split" — avoiding a ~2x backend-ahead slice with no consumer (Professional Honesty paid off).
- **Lenient singleton (`maybe_get() or Service()`)** deliberately sidestepped the 57.84 Day-3 singleton-leak regression class — no lifespan wiring, no conftest reset, nothing to leak.

## Q4. Lessons

- **A superuser test DB role makes DB-level RLS untestable (D5).** The `ipa_v2` connection bypasses RLS even under FORCE, so a cross-tenant read is not blocked in tests. The first isolation test (asserting RLS blocks a cross-tenant read) failed at 201/visible. The codebase convention (hitl/quotas tests) already handles this: assert isolation at the **application layer** (row attributed to the right tenant; the other tenant has no row). RLS policies are still present (check_rls_policies green) + enforce in production. **Don't write RLS-block assertions against the superuser test role.**
- **mypy strict types `AsyncSession.execute(update())` as `Result` (no `.rowcount`).** Use `.returning(<pk>).scalar_one_or_none()` for rowcount-style guards (single-use consume, revoke) — cleaner than a `cast` and mypy-clean.
- **The existing frontend test for a re-pointed page must be rewritten in-place** (Sprint 57.78 D-DAY1-1 lesson applied successfully here): `invite.test.tsx` already existed (testing the fixture/banner behavior); I rewrote it for the wired behavior rather than adding a dup.
- **Redundant "defense" is worse than no defense**: the own-tenant guard read as security but was a no-op (both gated roles are cross-tenant by design). Dropped it (Karpathy §2/§3 — no fake flexibility).

## Q5. Improvements next sprint

- For 57.86 (credentials), expect the same greenfield-IAM over-run; budget at `medium-backend` 0.80 but plan for ratio ~1.2 (or propose `iam-backend-spike` if this is the 2nd confirming point).
- Consider a Day-0 check item: "does the target table's RLS need to be tested for blocking? If the test role is superuser, plan an application-layer isolation assertion instead" — would have saved the one isolation-test rewrite (~10 min). Single data point; fold into `sprint-workflow.md` only if it recurs.

## Q6. Carryover (→ next-phase-candidates.md)

- **`AD-Auth-Credentials-PasswordLogin-Phase58`** (NEW, 57.86) — local-password credentials table + bcrypt + a tenant-scoped password-login endpoint. The accept's `password` is accepted-not-stored until then.
- **`AD-Auth-Register-Backend-IAM-Block-B-Phase58`** — self-service tenant registration (POST /tenants/register).
- **`AD-Auth-MFA-Backend-IAM-Block-C-Phase58`** — MFA TOTP + WebAuthn (accept navigates to `/auth/mfa`, still stub 501).
- **Invite email delivery** — no email facility; create returns the raw token in-response. Phase-58 follow-up.
- **Admin invites-list / resend UI** — `revoke` service method exists; the management surface is a follow-up.

## Q7. Risks

- **Low-Medium** (new security domain + a tenant-context middleware change). Mitigations: the exempt prefix matches only the guest paths (admin create stays role-gated — `test_create_requires_admin` + `test_exempt_path_contract` gate it); the token is high-entropy + sha256-stored + lookup-by-equality only; single-use is rowcount-guarded; all 18 backend + 5 frontend tests green; not merged until gates green.
- **Residual**: DB-level RLS isolation is asserted at the application layer in tests (superuser test role) — the policies enforce in production under a non-superuser app role; the sentinel escape is correct-by-construction (production-verified in billing_outbox 57.84).

---

## Design Note Extract (spike sprint)

**File**: `docs/03-implementation/agent-harness-planning/21-iam-invites-spike.md`
**Verified ratio (estimated)**: ~97% (every technical claim carries a file:line or a test name; the only non-verified content is the §5 deferred boundary, explicitly marked).

**8-Point Quality Gate**:
- [x] 1. Section header → spike user story (§1 US-1..US-5)
- [x] 2. file:line per technical claim (§3 table — invites.py / 0026 / auth.py / tenant_context.py lines)
- [x] 3. Decision matrix (§2.1 token DB-opaque vs JWT 6-column matrix + §2.2/§2.3)
- [x] 4. Verification command (§3 `pytest tests/.../test_invites*.py`)
- [x] 5. Test fixture reference (§3 conftest seed_* + `_build_app` X-Test headers)
- [x] 6. Open invariant boundary (§5 verified lifecycle/isolation vs deferred credentials/register/MFA/email + the RLS-superuser note)
- [x] 7. Rollback path (§6 revert files + `alembic downgrade -1` + sentinel risk note)
- [x] 8. 17.md cross-ref (§4 — assessed N/A with rationale, same as 57.84)

**Reviewer pass**: self-review (parent).
