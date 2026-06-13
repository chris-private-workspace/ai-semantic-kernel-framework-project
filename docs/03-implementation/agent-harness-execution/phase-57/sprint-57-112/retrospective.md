# Sprint 57.112 Retrospective — IAM Block C MFA (TOTP-only vertical)

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-112-plan.md) · [Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-112-checklist.md) · [Design note 30](../../../agent-harness-planning/30-iam-mfa-spike.md) · CHANGE-079

---

## Q1 — What was the goal? Did we hit it?

Close the TOTP leg of `AD-Auth-MFA-Backend-IAM-Block-C-Phase58`: a real app-level TOTP second factor on the local-password login path. **Hit.** `TOTPService` (enroll/confirm/verify) + 3 endpoints + the password-login challenge gate + thin FE, all drive-through-proven (real UI + real backend + real Postgres, ALL 3 legs PASS). WebAuthn + recovery deferred per the scope decision.

## Q2 — Estimate accuracy / calibration

- Class **`iam-backend-spike` 0.65** (3rd data point — 57.87 registration ≈1.0, 57.105 RBAC-JWT ≈0.95).
- Bottom-up ~14 hr → committed ~9 hr (×0.65) → **actual ~11.5 hr** → **ratio ≈1.28** (slightly over the 1.20 band).
- **Why over**: this sprint carried a NOTABLE FE component (2 pages + i18n en/zh-TW + 3 Vitest conversions + the D13 drive-through bug + re-drive) that 57.87/57.105 (more purely backend) did not. The over-run is the FE + the drive-through-detour, not a backend mis-estimate.
- **Action**: KEEP 0.65 — a single over-point does not trigger adjustment (3-consecutive rule); the 3-point mean ≈1.08 is IN band. If the next `iam-backend-spike` also runs >1.20, propose an `iam-backend-with-fe` sub-class ~0.75. agent-delegated: no (parent-direct — auth security-sensitive).

## Q3 — What went well

- **The `CredentialsService` mirror was a clean template** — `TOTPService` came together fast (Day 1 ahead of estimate); the established IAM pattern (typed errors / `_set_tenant` / singleton) paid off.
- **Shared `issue_session` extraction** de-duped the full-session block cleanly (password-login non-MFA + `/mfa/verify`); 87 auth/identity regression tests stayed green → behavior-preserving.
- **Day-0 三-prong caught the load-bearing facts upfront** (D1 EXEMPT exact-match → no in-endpoint-guard pivot; D2 no-encryption-utility → confirmed plaintext decision) — zero mid-sprint design pivots.
- **The full enroll→confirm→login→verify e2e integration test** + the real drive-through gave high confidence the vertical actually works end-to-end.

## Q4 — What to improve / lessons

- **D13 — the drive-through caught a real bug Vitest could not** (the headline lesson): the MFA `/mfa/verify` `fetchWithAuth` lacked `{redirectOn401:false}`, so a wrong-code 401 bounced to the SSO login page instead of the inline error. The Vitest mocks `global.fetch` directly + jsdom no-ops `window.location` → the unit test passed while the real behavior was broken. **Only the real drive-through surfaced it.** Textbook Drive-Through-Acceptance value: gate-green ≠ usable. Generalizable: any page calling `fetchWithAuth` for a NON-session-expiry 401 (a validation 401) MUST pass `{redirectOn401:false}` — grep candidate for a future FE lint.
- **D12 — dep-file drift**: `pyproject.toml` is `dependencies=[]`; runtime deps live in `requirements.txt`. Caught Day 1 (plan FCL said pyproject). Minor.
- **run_all.py is CWD-sensitive** (the 57.107 `AD-RunAll-CWD-Guard` recurrence): from `backend/` it 404s; must run from repo root. 3rd occurrence — the repo-root guard is overdue.
- **Test DB needs `alembic upgrade head`** before the new-column tests pass (conftest documents this) — applied once, then green.

## Q5 — Carryover ADs (→ next-phase-candidates.md)

- **`AD-MFA-Secret-At-Rest-Encryption`** (🟡) — `totp_secret` is base32 plaintext; encrypt at rest once an encryption utility is wired.
- **WebAuthn** (🟡) — real ceremony + `py_webauthn` + credential table + FE rework; a separate C-12 spike.
- **`AD-Auth-MFA-Recovery-Page`** (🟡) — recovery codes + `/auth/mfa/recovery` (needs an email adapter).
- **OIDC-callback MFA gate** (🟢) — SSO MFA is IdP-enforced; the 302 gate is a separate slice.
- **`AD-MFA-Enroll-Setup-UI`** (🟢) — no enroll mockup; enroll is API-driven today.
- **`AD-Auth-PasswordLogin-Lockout`** (🟢, shared) — extend the brute-force throttle to `/mfa/verify`.
- **`AD-FE-FetchWithAuth-Validation-401-Lint`** (🟢 NEW from D13) — a lint/grep guard that any `fetchWithAuth` whose 401 is a validation error (not session expiry) passes `{redirectOn401:false}`.

## Q6 — Spike design-note 8-point quality gate self-check (§5.5)

**File**: `docs/03-implementation/agent-harness-planning/30-iam-mfa-spike.md` · **Verified ratio (est)**: ~95%

- [x] 1. Section headers map to US-1/US-2/US-3
- [x] 2. Every technical claim has a file:line / migration / command anchor (§3 table)
- [x] 3. Decision rationale is a comparison matrix (§2 — challenge-token, secret storage, gate scope)
- [x] 4. Verification commands reproducible (`pytest …test_mfa_service.py` / `…test_mfa_endpoints.py` / alembic roundtrip)
- [x] 5. Test fixture references (real Postgres `db_session` + httpx ASGITransport; pyotp codes)
- [x] 6. Open invariants explicitly fenced off (§5 — deferred, NOT verified)
- [x] 7. Rollback path (§6 — revert 3 commits + `alembic downgrade -1`, tested; per-user `mfa_enabled` kill)
- [x] 8. 17.md cross-ref (§4 — no new contract; identity is platform infra, consistent with 21/22/23)

**Reviewer pass**: self-review.

## Q7 — Anti-pattern audit (11-point)

- AP-1 (pipeline-as-loop): N/A (no loop). AP-2 (side-track): ✅ all code reachable from `/api/v1/mfa/*` + the login gate. AP-3 (scattering): ✅ MFA in `identity/mfa.py` + `api/v1/mfa.py`. **AP-4 (Potemkin)**: ✅ the vertical is REAL + drive-through-proven (enroll→confirm→verify all work; the demo banner is GONE; WebAuthn returns an honest 400, not a fake success; the recovery link is honestly disabled). AP-6 (speculative abstraction): ✅ TOTP-only, no WebAuthn scaffolding. AP-8 (PromptBuilder): N/A. AP-9 (verification): N/A. AP-11 (version suffix): ✅ none. **Total violations: 0.**
