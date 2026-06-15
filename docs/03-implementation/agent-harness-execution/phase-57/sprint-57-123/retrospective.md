# Sprint 57.123 Retrospective — Tenant-display real-data wiring

**Slice**: `AD-FE-Tenant-Display-Fixture-Phase58` (C-class 主流量 Potemkin). **Closed** 2026-06-15.
**Branch**: `feature/sprint-57-123-tenant-display-real-data` (from `main` `937dd5ca`).

## Q1 — What shipped

The app chrome (sidebar tenant pill + topbar tenant pill + UserMenu tenant section) now renders the REAL logged-in tenant from `authStore.tenant` instead of a hardcoded fixture. `/auth/me` `AuthMeTenant` gained `plan` + `region` (real `Tenant` columns) at all 3 build sites; the FE `AuthTenant` interface threads them automatically; the 3 chrome components swap their fixtures for real data; the UserMenu's 3-tenant fixture switcher collapses to the single real current tenant (each user is JWT-scoped to one tenant). Closes the next C-class Potemkin after the HITL载重 gap (57.122). Full-stack but small; NO migration / wire (24) / codegen; visual/CSS byte-identical (mockup-fidelity 51). CHANGE-090; NO design note (feature-continuation).

## Q2 — Estimate accuracy + calibration

- **Plan**: bottom-up ~6.0 hr → class-calibrated commit ~4.5 hr (mult **0.75**, NEW class `frontend-fixture-to-real-data-wiring`). Agent-delegated: **no** (parent-direct, `agent_factor` 1.0).
- **Actual**: ~6.0 hr (Day 0 探勘 incl. plan/checklist + 三-prong with the 3-construction-sites + dev-login-new-tenant catches ~1.0 · Day 1 backend 3-sites + test ~0.75 · Day 2 components + i18n ~1.0 · Day 3 FE tests 4 files ~1.0 + drive-through ~1.25 incl. the Risk Class E orphan-worker debugging detour · Day 4 CHANGE-090 + closeout ~1.0).
- **Ratio actual/committed ≈ 1.33** (OVER band); ratio actual/bottom-up ≈ 1.0 (the bottom-up was right; the **0.75 multiplier was a touch low**).
- **Calibration action**: `frontend-fixture-to-real-data-wiring` **0.75 → re-point 0.90** (1st data point > 1.20 → per the matrix rule "re-point toward 0.90"). Consistent with the Sprint 57.120/57.122 ceremony-not-code-accelerated insight: a parent-direct sprint with FULL ceremony (plan/checklist/Day-0 三-prong/multi-leg drive-through/CHANGE/retro) lands ~0.85-1.0 even when the code is bounded + mechanical. The Risk Class E orphan-worker detour also added unplanned wall-clock.

## Q3 — What went well

- **Day-0 三-prong caught two real correctness traps before any code**: (1) `AuthMeTenant` is built at **3** sites, not the 1 the plan named — a required-field addition to only `me()` would have 500'd `dev_login` + `issue_session` (password-login + MFA). (2) The `dev_login` new-tenant branch constructs a `Tenant` with no Python-side plan/region (server_default only) → an async lazy-load risk; fixed with explicit construction values. Both were invisible to a path-only verify.
- **The FE thread was genuinely 1 interface** — Day-0 confirmed `bootstrap` spreads the whole `me.tenant` + `fetchAuthMe` is a hand-written cast (no codegen), so +2 fields on `AuthTenant` auto-threaded. No store/service edit.
- **The drive-through delta is unambiguous**: two real logins (acme-prod → globex-eu) showed the chrome FOLLOWS the session (different tenant → different sidebar/topbar/UserMenu), with the old `tenant_01h9a2 · Pro` + globex-eu/initech-jp fixtures gone — live AP-4 closure, not gate-only.
- **mockup-fidelity stayed byte-identical** (51): swapping only the component-logic data layer (not CSS classes) kept the verbatim-mockup contract intact — the two-layer split worked exactly as the CLAUDE.md rule intends.

## Q4 — What to improve

- **Risk Class E cost ~real time**: the first dev-login probe returned a tenant WITHOUT plan/region despite `dev.py restart` reporting a new PID — an orphan spawn-worker (parent dead) held :8000 with old code via SO_REUSEADDR. The `Win32_Process` PID/PPID/StartTime sweep is the reliable fix, but I should have run the sweep + a post-restart probe BEFORE assuming the restart worked (the Risk Class E reinforcement from 57.97 predicts exactly this). **Lesson**: for any `.py`-touching sprint, probe the changed endpoint immediately after restart and verify the live serving process, not the reported PID.
- **Calibration**: the new-class 0.75 was a touch optimistic for a ceremony-heavy parent-direct sprint; the 57.120/57.122 insight should have started it ~0.85-0.90. Re-pointed.

## Q5 — Anti-pattern self-check

- **AP-4 (Potemkin)**: ✅ this slice CLOSES an AP-4 (3 chrome fixtures → real data); the 2-tenant drive-through proves the chrome follows the real session live. The `check_ap4_frontend_placeholder.py` lint is green.
- **AP-2 (side-track)**: ✅ the change is on the main chrome path (every page). **AP-3 (scattering)**: ✅ the real data has one source (`authStore.tenant` ← `/auth/me`); the 3 components all consume it. **AP-6 (hybrid bridge debt)**: ✅ rejected building a real multi-tenant switcher (no backend; YAGNI) — collapsed to the single real tenant instead.
- **AP-1 / AP-8 / AP-11**: N/A. **0 violations**.

## Q6 — Design note

**N/A** — NO design note. Per `.claude/rules/sprint-workflow.md` §5.5 this is a feature-continuation / Potemkin-fix data wiring (the authStore-consumption pattern already powered the user/roles display in the same components); no new decision semantics. CHANGE-090 only.

## Q7 — Carryover

- `AD-FE-Tenant-Display-Fixture-Phase58` ✅ **SHIPPED**.
- The dev-login picker labels ("acme-prod (Pro · ap-east-1)") in `pages/auth/dev/index.tsx` are a dev-only-tool fixture (NOT 主流量 chrome) — left as-is; a future tidy-up if desired (low priority, dev-only).
- The sidebar tenant-switcher **chevron** + the "Switch tenant" tooltip imply a switcher that doesn't exist (single JWT-scoped tenant); left per mockup-fidelity — revisit if/when a real multi-tenant membership model lands.
- `FIXTURE_UNREAD_COUNT=3` (`AppShellV2.tsx:79`) — a separate (non-tenant) chrome notification fixture; a different C-class AD.
- Remaining C-class 主流量 Potemkin / the operator-portal drive-through audit backlog (see `next-phase-candidates.md`).
