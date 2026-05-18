# Sprint 57.23 — Checklist

**Plan**: `sprint-57-23-plan.md`
**Calibration**: `frontend-mockup-strict-rebuild` 0.60 (NEW class 1st application; HYBRID weighted blend per Sprint 57.22 §Sprint 57.23+ Recommendation) — bottom-up ~46 hr → calibrated commit ~28 hr (3-sprint window rule: KEEP 0.60 regardless of ratio outcome; if recurs 2-3× → propose 0.60 → 0.40-0.50 or 0.75-0.80 per evidence)
**Day count**: 5 (Day 0 三-prong + Day 1 AuthShell + login + dev / Day 2 callback + register / Day 3 invite + mfa + expired / Day 4 i18n + App.tsx wire + closeout)
**Branch**: `feature/sprint-57-23-auth-page-full-rebuild-round-2`

---

## Day 0 — Setup + 三-prong + Playwright MCP reference captures

### 0.1 Plan + checklist landed
- [x] Plan drafted at `sprint-57-23-plan.md` (Frontend-only rebuild; Q1+Q2+Q3 decisions encoded)
- [x] Checklist drafted at `sprint-57-23-checklist.md` (this file)
- [x] User Q1+Q2+Q3 alignment (2026-05-18 — Mockup oklch indigo / Frontend-only rebuild / Roll-own TOTP + WebAuthn UI per mockup)

### 0.2 Branch + initial doc files
- [x] Verify main HEAD: `1840cb27` (PR #155 squash merge for Sprint 57.22)
- [x] Switch from `main` (working tree should be clean after Sprint 57.22 closeout)
- [x] Create feature branch `feature/sprint-57-23-auth-page-full-rebuild-round-2` from main `1840cb27`
- [x] Create `progress.md` at `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-23/progress.md` (Day 0 entry + 5 D-PRE findings + Playwright captures table)
- [x] Create `claudedocs/4-changes/sprint-57-23-auth-page-full-rebuild-round-2/{screenshots/{mockup,prod,post-rebuild}/, DRIFT-REPORT-AUTH-ROUND-2.md}` skeleton

### 0.3 Day 0 三-prong scope verify (per sprint-workflow.md §Step 2.5)
- [x] **Prong 1 (Path verify)** — confirm each plan §File Change List entry:
  - `frontend/src/components/AuthShell.tsx` exists ✅ (current state: sticky header + container p-6 inset — D-PRE-1 mismatch)
  - `frontend/src/pages/auth/login/index.tsx` exists ✅ (174L; D-PRE-4 DevLoginSection embedded)
  - `frontend/src/pages/auth/callback/index.tsx` exists ✅ (96L; D-PRE-5 no multi-step UI)
  - `frontend/src/pages/auth/register/` directory MISSING ❌ (Unit 3 confirmed)
  - `frontend/src/pages/auth/invite/` directory MISSING ❌ (Unit 4 confirmed)
  - `frontend/src/pages/auth/mfa/` directory MISSING ❌ (Unit 5 confirmed)
  - `frontend/src/pages/auth/expired/` directory MISSING ❌ (Unit 6 confirmed)
  - `frontend/src/pages/auth/dev/` directory MISSING ❌ (extracted from login)
  - `reference/design-mockups/page-extras.jsx` exists ✅ (991L — AuthShell/AuthLogin/AuthCallback/AuthDev at L1-200)
  - `reference/design-mockups/page-auth-extras.jsx` exists ✅ (418L — AuthShellX/AuthRegister/AuthInvite/AuthMFA/AuthExpired)
  - `frontend/src/i18n/locales/{en,zh-TW}/auth.json` exists ✅ (current state: smaller key set for login+callback only)
- [x] **Prong 2 (Content verify)** — grep each plan §Technical Spec assertion:
  - `AuthShell.tsx` line 38-52 confirms sticky `<header>` + `container mx-auto flex-1 p-6` + footer (D-PRE-1)
  - `tailwind.config.ts` line 26-28 confirms `primary: hsl(var(--primary))` token wired (D-PRE-2)
  - `index.css` line 38 confirms `--primary: 234 89% 60%` light + line 92 `--primary: 234 84% 70%` dark (D-PRE-2)
  - `App.tsx` line 11-15 + L88-89 confirms `Auth routes (/auth/*) NOT in registry` + 2 routes wired directly (D-PRE-3)
  - `login/index.tsx` L67-133 confirms `DevLoginSection` embedded with `import.meta.env.DEV` gate (D-PRE-4)
  - `callback/index.tsx` L52-69 confirms `bootstrap()` + navigate; no timed progress UI (D-PRE-5)
  - `useAuthStore` + `consumePostLoginRedirect` consumed at `frontend/src/features/auth/services/authService.ts` + `store/authStore.ts`
- [x] **Prong 3 (Schema verify)**: N/A this sprint (pure frontend, 0 DB schema work per Q2 frontend-only decision)
- [x] Catalog Day 0 drift findings as `D-PRE-1` through `D-PRE-5` in `progress.md`:
  - D-PRE-1: AuthShell structure mismatch (rewrite scope confirmed)
  - D-PRE-2: `--primary` token already indigo HSL (scope reduction; no new token needed — save ~1-2 hr)
  - D-PRE-3: routes.config.ts excludes `/auth/*` (use App.tsx direct wire)
  - D-PRE-4: DevLoginSection embedded in login (extract to /auth/dev)
  - D-PRE-5: callback lacks multi-step UI (add timed setTimeout simulation)
- [x] Go/no-go decision: scope shift verdict = **~5% reduction** (D-PRE-2 saves 1-2 hr) → **GO Day 1**

### 0.4 Playwright MCP reference captures (US-A1)
- [ ] Verify mockup http.server still running at port 8080 (Sprint 57.18 setup)
- [ ] Verify dev server running at port 3007 (DO NOT kill — per CLAUDE rule)
- [ ] Playwright MCP capture mockup pages at 1440×900 → `screenshots/mockup/`:
  - `auth-login.png` (mockup `#auth-login`)
  - `auth-callback.png` (mockup `#auth-callback`)
  - `auth-register.png` (mockup `#auth-register`)
  - `auth-invite.png` (mockup `#auth-invite`)
  - `auth-mfa.png` (mockup `#auth-mfa`)
  - `auth-expired.png` (mockup `#auth-expired`)
  - `auth-dev.png` (mockup `#auth-dev`)
- [ ] Playwright MCP capture pre-rebuild production at 1440×900 → `screenshots/prod/`:
  - `auth-login-pre.png` (prod `/auth/login`)
  - `auth-callback-pre.png` (prod `/auth/callback`)
  - `auth-register-pre.png` (prod `/auth/register` → expected 404 or redirect)
- [ ] Commit Day 0 artifacts: `chore(sprint-57-23, Day 0): plan + checklist + Day 0 三-prong + Playwright MCP reference captures`

---

## Day 1 — AuthShell refactor + Login rewrite + Dev extraction (US-B1 + US-B2 + US-B3)

**Workflow**: mockup-direct rewrite per `.claude/rules/sprint-workflow.md` Frontend Mockup-Fidelity Hard Constraint. Source baseline: `reference/design-mockups/page-extras.jsx` L1-200.

### 1.1 US-B1 AuthShell.tsx full-screen-centered rewrite
- [x] **REWRITE** `frontend/src/components/AuthShell.tsx`:
  - Remove sticky `<header>` + `container mx-auto p-6` + `<footer>` (current shell)
  - Add radial gradient backdrop via inline `style={{ background: "radial-gradient(...)" }}` (one escape-hatch per STYLE.md §3 — no Tailwind utility for multi-stop HSL gradient)
  - Centered 420-wide column + brand mark slot (32×32 `bg-primary` aria-hidden) + IPA Platform 16px / V2 · loop-first 10.5px subtitle + children + optional footer slot per mockup `page-extras.jsx:5-25`
  - Preserve `data-testid="auth-shell"` anchor for Playwright e2e selector stability (R7 mitigation)
  - File-header Modification History: `2026-05-18: Sprint 57.23 — rewrite to mockup full-screen centered per AD-AuthShell-Mockup-Refactor (closes Sprint 57.22 AD)`
- [x] **ADAPT existing Vitest specs** (`AuthShell.test.tsx`):
  - Selector adapt: `<h1>IPA Platform V2 — Sign In</h1>` removed; replaced by 16px "IPA Platform" + 10.5px metadata
  - Renamed prop `headerActions` → `footer` (mockup pattern); test adapted
  - Preserve behavioral assertions (children render slot / footer render slot / wrap pattern)
- [x] `npx tsc --noEmit` 0 errors
- [x] `npx vitest run AuthShell` PASS (2 cases adapted: brand text + footer slot)
- [ ] Verify: Playwright MCP capture post-rewrite `/auth/login` at 1440×900 — DEFERRED to Day 4 batch capture (matches Sprint 57.21 pattern)

### 1.2 US-B2 /auth/login mockup-direct rewrite
- [x] **REWRITE** `frontend/src/pages/auth/login/index.tsx`:
  - Remove embedded `DevLoginSection` (extracted to §1.3)
  - Per mockup `page-extras.jsx:27-57`: Card containing "Sign in" 18px + sub "Continue with SSO or your work email." 12.5px + 3 SSO outline buttons (SAML / Microsoft / Google Workspace) **disabled** with tooltip "Enterprise SSO via WorkOS roadmap" (`aria-disabled` + secondary styling) + "or" divider + Work email input 13.5px + Continue primary button bg-primary + MFA hint footer + dev-login link
  - Preserve existing `handleLogin` (window.location WorkOS redirect)
  - Preserve `errorMessage` `?error=` param surface + ErrorAlert component
  - Remove `<h1>` heading (mockup has NO h1; H1-rule via mockup-fidelity overrides a11y page-has-heading-one for `/auth/login`)
  - File-header MHist: `2026-05-18: Sprint 57.23 US-B2 — mockup-direct rewrite (3 SSO disabled + email + Continue; extract DevLoginSection)`
- [x] **ADAPT existing Vitest specs** for login (`login.test.tsx`):
  - 5 obsolete tests removed/adapted: "Login with WorkOS" + h1 + no-inline-style + 3 dev-login tests moved to new dev.test.tsx
  - 4 NEW cases: Sign in heading + 3 SSO disabled + Continue primary + no-h1
- [x] **ADAPT i18n keys** `auth.json` EN + zh-TW:
  - REMOVED: `signInTitle` / `signInSubtitle` / `loginWithWorkOS` / `devSection.*` (4 + 6 keys)
  - ADDED: `login.*` (14 keys) + `dev.*` (12 keys; +tenantLabel/roleLabel/continueAs Day 1.3)
- [ ] Verify: Playwright MCP capture post-rewrite `/auth/login` at 1440×900 → DEFERRED to Day 4 batch

### 1.3 US-B3 /auth/dev extraction
- [x] **NEW FILE** `frontend/src/pages/auth/dev/index.tsx` (~180L; mockup AuthDev L109-152 1:1 port):
  - Wrap in `<AuthShell footer={...}>` with mockup footer copy + monospace `DEV_LOGIN=true` highlight
  - risk-high warning card with destructive token border + ShieldAlert icon + warning title + body (mockup hitl-card semantic preserved via destructive token mapping)
  - Card with 3 fields: Assume identity (select 4 fixtures) + Tenant (select 3 fixtures) + Role (4 badges, active=identity.role; aria-pressed)
  - "Continue as {{email}}" primary button → POST /api/v1/auth/dev-login (tenant_code + email) → bootstrap → navigate(consumePostLoginRedirect())
  - File-header MHist
- [x] **ADD ROUTE** in `App.tsx`:
  - `const DevLoginPage = lazy(() => import("./pages/auth/dev"));`
  - `{import.meta.env.DEV && <Route path="/auth/dev" element={<DevLoginPage />} />}` — production gates to 404
- [x] **i18n keys** `auth.json` EN + zh-TW: 12 dev.* keys (title / warningTitle / warningBody / identityLabel / tenantLabel / roleLabel / continueAs / footer / submitting / errorDisabled / errorFailed / errorRequest)
- [x] **NEW Vitest spec** `frontend/tests/unit/pages/auth/dev.test.tsx` (3 cases: mockup shape render / POST dev-login + bootstrap / 404 errorDisabled)
- [ ] Verify: `npm run build && grep -r "auth/dev" frontend/dist/` = 0 results in production build (R8 mitigation) — DEFERRED to Day 4 (current `npx vite build` was dev-mode preview; final prod gate verify at Day 4)
- [ ] Verify: Playwright MCP capture dev mode `/auth/dev` at 1440×900 → DEFERRED to Day 4 batch

### 1.4 Day 1 closeout
- [x] `npx tsc --noEmit` 0 errors
- [x] `npx vitest run` Vitest 350/350 PASS (Sprint 57.22 baseline 348 → 350; net +2 = dev.test.tsx NEW 3 cases / login.test.tsx -1 obsolete DevLogin)
- [x] `npm run lint` silent (--max-warnings 0; 1 escape-hatch eslint-disable-next-line on AuthShell gradient)
- [x] `npx vite build` succeeds 3.46s; main bundle 323.24 kB (+1.32 KB vs 321.92 kB Sprint 57.22 baseline; within +5 KB target ✅)
- [ ] Progress.md Day 1 entry + 3 DRIFT verdicts (AuthShell / login / dev) — DRIFT verdicts deferred to Day 4 Playwright MCP batch capture
- [ ] Day 1 commit: `feat(frontend, sprint-57-23, Day 1): AuthShell + /auth/login + /auth/dev rewrite per mockup`

---

## Day 2 — Callback + Register rewrite (US-C1 + US-C2)

### 2.1 US-C1 /auth/callback timed 3-step progress rewrite
- [x] **REWRITE** `frontend/src/pages/auth/callback/index.tsx`:
  - Per mockup `page-extras.jsx:59-107`: Card with conic-gradient spinning ring + "Completing sign-in…" + `callback=acme.workos.com` mono subtitle + 3-step progress list ("Verifying SAML assertion" / "Resolving tenant + RLS context" / "Loading feature flags + memory scopes") with timed `setTimeout` transitions (800/1800/2800ms)
  - Preserve existing `bootstrap()` + `consumePostLoginRedirect()` logic (runs in parallel with timed UI)
  - Min navigation duration enforce 2800ms for UX consistency (don't redirect before final step renders)
  - Error case: `?error=` param → EmptyState w/ "Back to login" (preserve Sprint 57.13 behavior)
  - File-header MHist: `2026-05-18: Sprint 57.23 — rewrite to mockup AuthCallback (timed 3-step progress + parallel bootstrap; min 2800ms UX duration)`
- [x] **ADAPT existing Vitest specs** for callback:
  - Selector adapt: 3-step progress list assertions added (Verifying SAML / Resolving tenant / Loading flags)
  - Dropped no-inline-style assertion (conic-gradient + animation legitimate STYLE.md §3 escape hatches)
  - Preserve bootstrap → navigate behavioral assertion via existing ?error short-circuit test
- [x] **i18n keys** `auth.json` EN + zh-TW: `callback.*` (5 keys — callbackUrlPrefix / callbackUrlHost / steps.verifySaml / steps.resolveTenant / steps.loadFlags)
- [ ] Verify: Playwright MCP capture `/auth/callback` at 1440×900 — DEFERRED to Day 4 batch

### 2.2 US-C2 /auth/register 4-step wizard
- [x] **NEW FILE** `frontend/src/pages/auth/register/index.tsx` (~370L):
  - Wrap in `<AuthShell footer={<>Already have a workspace? <a href="/auth/login">Sign in</a></>}>`
  - Per mockup `page-auth-extras.jsx:31-188`: Card with stepper bar (4 circles + connectors) + 4 step bodies + Back/Continue navigation
  - State: `useState<0|1|2|3>(step)` + step-local form state (email/name → org/slug/region/size → plan radios → terms checkbox)
  - **Step 0 (Identity)**: Work email input + Full name input + SAML hint w/ shield icon
  - **Step 1 (Organization)**: Company name + Tenant slug (with `.ipa.platform` suffix) + Region dropdown (4 options: ap-east-1 default / us-east-1 / eu-west-1 / ap-northeast-1) + Size dropdown (4 options: 1-50 / 51-500 / 500-2000 default / 2000+)
  - **Step 2 (Plan)**: 3 radio cards (Trial 14 days / Pro $1,200/mo defaultChecked / Enterprise Custom)
  - **Step 3 (Confirm)**: Summary hitl-card severity=risk-low + terms checkbox + verification email hint warning icon
  - Navigation: Back button (steps 1-3) + Continue button (steps 0-2) / Create workspace primary button (step 3 → call `POST /api/v1/tenants/register` → expect 501 → show demo banner)
  - "Backend wire pending Phase 58+ IAM Block B" demo banner above stepper (AP-2 compliance)
  - File-header MHist
- [x] **ADD ROUTE** in `App.tsx`: `const RegisterPage = lazy(() => import("./pages/auth/register"));` + `<Route path="/auth/register" element={<RegisterPage />} />`
- [x] **i18n keys** `auth.json` EN + zh-TW: 25 register.* keys (title / subtitle / step1-4 / workEmail / fullName / ssoHint / companyName / tenantSlug / tenantSlugHelp / region / size / almostDone / terms / verifyHint / create / alreadyHave / signIn / back / continue / demoBanner / submitting / errorStubbed / errorRequired)
- [x] **NEW Vitest spec** `frontend/tests/unit/pages/auth/register.test.tsx`: **5 cases** (initial render step 0 + demo banner / Continue advances 0→1 / Back retreats 1→0 / advances to step 3 Create button / 501 stub error surface)
- [ ] Verify: Playwright MCP capture `/auth/register` at 1440×900 — DEFERRED to Day 4 batch

### 2.3 Day 2 closeout
- [x] `npx tsc --noEmit` 0 errors
- [x] `npx vitest run` 355/355 PASS (Day 1 baseline 350 → 355; +5 register.test.tsx NEW; 0 regression)
- [x] `npm run lint` silent (--max-warnings 0; needed `aria-label` on plan radio labels for jsx-a11y/label-has-associated-control after stepper added)
- [x] `npx vite build` 3.48s; main bundle 325.48 kB (+2.24 KB vs Day 1 / +3.56 KB vs Sprint 57.22 baseline; within +15 KB Day 2 target ✅)
- [x] Progress.md Day 2 entry — DRIFT verdicts deferred to Day 4 Playwright MCP batch
- [ ] Day 2 commit: `feat(frontend, sprint-57-23, Day 2): /auth/callback timed-progress + /auth/register 4-step wizard per mockup`

---

## Day 3 — Invite + MFA + Expired (US-D1 + US-D2 + US-D3)

### 3.1 US-D1 /auth/invite/:token NEW
- [ ] **NEW FILE** `frontend/src/pages/auth/invite/index.tsx` (~120L):
  - Wrap in `<AuthShell footer={t("auth.invite.foot")}>`
  - Per mockup `page-auth-extras.jsx:191-246`: Card with avatar icon (56×56 primary alpha bg + User lucide) + title "You're invited to acme-prod" + subtitle + metadata grid 4 rows (Tenant / Invited by / Role / Expires; fixture values + Badge primary for Role) + Full name input + Set password input with hint "12+ chars · used only if SSO is unavailable" + Accept primary button + MFA notice shield-icon row
  - `useParams<{ token: string }>()` to read URL `:token` param
  - On mount: call `GET /api/v1/invites/:token` → expect 501 → fallback to fixture metadata (acme-prod / dan@acme.com / operator / 6 days)
  - On Accept: call `POST /api/v1/invites/:token/accept` → expect 501 → demo banner → navigate `/auth/mfa` (mockup flow continuation L235)
  - "Backend wire pending Phase 58+ IAM Block B" demo banner
  - File-header MHist
- [ ] **ADD ROUTE** in `App.tsx`: `const InvitePage = lazy(() => import("./pages/auth/invite"));` + `<Route path="/auth/invite/:token" element={<InvitePage />} />`
- [ ] **i18n keys** `auth.json`: `invite.title` / `invite.subtitle` / `invite.fullName` / `invite.password` / `invite.passwordHint` / `invite.accept` / `invite.mfaHint` / `invite.foot` (~8 keys × 2 locales)
- [ ] **NEW Vitest spec** `frontend/tests/unit/pages/auth/invite.test.tsx`: 3-4 cases (initial render with fixture metadata / Accept button calls POST / demo banner visible / navigate to /auth/mfa on success)
- [ ] Verify: Playwright MCP capture `/auth/invite/test-token` at 1440×900 → DRIFT verdict

### 3.2 US-D2 /auth/mfa NEW — Roll-own TOTP + WebAuthn UI (Q3)
- [ ] **NEW FILE** `frontend/src/pages/auth/mfa/index.tsx` (~200L):
  - Wrap in `<AuthShell footer={<>{t("auth.mfa.foot")} <a href="#">{t("auth.mfa.help")}</a></>}>`
  - Per mockup `page-auth-extras.jsx:249-371`: Card with warning-icon (Keys lucide) + title "Two-factor verification" + dynamic subtitle (TOTP/WebAuthn) + Tab selector (Authenticator default / Security Key)
  - **TOTP tab**: 6-digit input grid (6 `<input>` boxes 44×52 / 22px mono / `inputMode="numeric"` / `maxLength={1}`) with `useRef` array + auto-focus advance + Backspace step-back; filled boxes get `bg-primary/10` border-primary; countdown text "code refreshes in 23s" (static — no real rotation); Verify button disabled until `code.every(v => v !== "")`
  - **WebAuthn tab**: 88×88 conic-gradient spinning ring (CSS `animation: spin 2.5s linear infinite`) + Shield icon + hint "Insert your security key or use platform authenticator" + "Simulate success" ghost button (DEV-only fallback)
  - **Paste handler**: paste event splits 6 chars into all boxes (R5 mitigation)
  - **Recovery code link**: `pointer-events-none text-fg-subtle` + tooltip "Recovery flow pending Phase 58+ IAM Block C"
  - On Verify submit: call `POST /api/v1/mfa/verify` → expect 501 → demo banner → navigate `/auth/callback`
  - "MFA backend wire pending Phase 58+ IAM Block C" demo banner above tabs
  - File-header MHist
- [ ] **ADD ROUTE** in `App.tsx`: `const MFAPage = lazy(() => import("./pages/auth/mfa"));` + `<Route path="/auth/mfa" element={<MFAPage />} />`
- [ ] **i18n keys** `auth.json`: `mfa.title` / `mfa.totpSub` / `mfa.webauthnSub` / `mfa.verify` / `mfa.recoveryCode` / `mfa.webauthnHint` / `mfa.simulate` / `mfa.foot` / `mfa.help` (~9 keys × 2 locales)
- [ ] **NEW Vitest spec** `frontend/tests/unit/pages/auth/mfa.test.tsx`: 5-7 cases (TOTP digit entry advances focus / Backspace retreats focus / paste 6 digits fills all / Verify disabled until 6 digits / Verify enabled at 6 digits / Tab switch TOTP↔WebAuthn / WebAuthn simulate button)
- [ ] Verify: Playwright MCP capture `/auth/mfa` at 1440×900 (TOTP tab + WebAuthn tab) → 2 screenshots + DRIFT verdicts

### 3.3 US-D3 /auth/expired NEW
- [ ] **NEW FILE** `frontend/src/pages/auth/expired/index.tsx` (~90L):
  - Wrap in `<AuthShell>` (no footer per mockup)
  - Per mockup `page-auth-extras.jsx:374-416`: Card with warning-icon (Clock lucide) + title "Your session expired" + subtitle 320px max-width + metadata grid 3 rows (Last activity / Session ID / Reason Badge w/ tone=warning) + 2 buttons row (Sign in again outline + Resume session primary) + data preservation hint
  - `useSearchParams()` read `?session_id=` + `?reason=` query params; fallback to fixture values (14h 02m ago / sess_8a2f1c3 / jwt_expired · 24h max) when absent
  - On "Sign in again" click: `navigate("/auth/login")`
  - On "Resume session" click: `navigate("/auth/callback?next=" + originalPath)` (preserves stashed redirect)
  - File-header MHist
- [ ] **ADD ROUTE** in `App.tsx`: `const ExpiredPage = lazy(() => import("./pages/auth/expired"));` + `<Route path="/auth/expired" element={<ExpiredPage />} />`
- [ ] **i18n keys** `auth.json`: `expired.title` / `expired.subtitle` / `expired.signInAgain` / `expired.resume` / `expired.dataHint` (~5 keys × 2 locales)
- [ ] **NEW Vitest spec** `frontend/tests/unit/pages/auth/expired.test.tsx`: 3 cases (initial render with fixture metadata / Sign in again click → navigate / Resume click → navigate with next param)
- [ ] Verify: Playwright MCP capture `/auth/expired?session_id=test&reason=jwt_expired` at 1440×900 → DRIFT verdict

### 3.4 Day 3 closeout
- [ ] `npx tsc --noEmit` 0 errors
- [ ] `npx vitest run` 348+N PASS (Day 3 deltas; expect ~11-14 NEW cases for invite + mfa + expired)
- [ ] `npm run lint` silent
- [ ] `npx vite build` succeeds; main bundle within +30 KB of 321.92 kB baseline
- [ ] Progress.md Day 3 entry + 4 DRIFT verdicts (invite + 2 mfa tabs + expired) recorded
- [ ] Day 3 commit: `feat(frontend, sprint-57-23, Day 3): /auth/invite + /auth/mfa + /auth/expired per mockup`

---

## Day 4 — i18n + App.tsx wire verification + Playwright + closeout (US-E1 + US-E2 + US-E3)

### 4.1 US-E1 i18n symmetric verify
- [ ] Final review of `frontend/src/i18n/locales/en/auth.json` + `frontend/src/i18n/locales/zh-TW/auth.json`:
  - Run `diff <(jq -r 'paths(scalars) | join(".")' en/auth.json | sort) <(jq -r 'paths(scalars) | join(".")' zh-TW/auth.json | sort)` → expect 0 output (R6 mitigation)
  - Total NEW keys ≈ 40 across register/invite/mfa/expired/dev (per Days 1-3 additions)
  - zh-TW translations human-readable (not machine-translated placeholder strings)
- [ ] If symmetric-keys lint exists at `frontend/tests/unit/i18n/` → run it; fix any drift

### 4.2 US-E2 App.tsx wire verification + final route audit
- [ ] Visual confirm `App.tsx` has 7 `/auth/*` routes total:
  - `/auth/login` (existing) + `/auth/callback` (existing) + `/auth/register` (Day 2 NEW) + `/auth/invite/:token` (Day 3 NEW) + `/auth/mfa` (Day 3 NEW) + `/auth/expired` (Day 3 NEW) + `/auth/dev` (Day 1 NEW; DEV-only gated)
- [ ] Verify DEV gate: `npm run build && grep -r "auth/dev" frontend/dist/` = 0 (R8 mitigation)
- [ ] Verify lazy imports: each route uses `React.lazy()` per existing pattern
- [ ] Manual URL test in dev mode at port 3007 — visit each route + verify renders (not 404)

### 4.3 US-E3 Vitest + Playwright e2e baselines
- [ ] Full Vitest run: `npx vitest run` → expect 348+N (N ≥ 15) ALL PASS; 0 regression
- [ ] Full Playwright e2e: `npx playwright test tests/e2e/auth/` → expect baseline preserved (selector adapt complete; happy-path register/invite/mfa specs deferred — backend stubs 501 — verify they're marked `test.skip` or guarded by `test.fixme` with AD reference)
- [ ] If Playwright auth flow fails post-AuthShell rewrite → adapt selectors using `data-testid="auth-shell"` anchor; preserve behavioral assertions

### 4.4 Day 4 Playwright MCP final pair-verify
- [ ] Re-capture all 6 production pages + dev page post-rebuild at 1440×900 → `screenshots/post-rebuild/`:
  - `auth-login-post.png` / `auth-callback-post.png` / `auth-register-post-step{0,1,2,3}.png` / `auth-invite-post.png` / `auth-mfa-post-totp.png` / `auth-mfa-post-webauthn.png` / `auth-expired-post.png` / `auth-dev-post.png`
- [ ] Side-by-side compare mockup vs post-rebuild → DRIFT-REPORT-AUTH-ROUND-2.md final entry per page (PARITY / COSMETIC / STRUCTURAL drift verdict)
- [ ] If any STRUCTURAL drift → fix-then-commit in Day 4 (per Mockup-Fidelity Hard Constraint structural drift CANNOT defer)

### 4.5 Day 4 doc syncs (closeout — per REFACTOR-001 §Sprint Closeout policy minimal touch)
- [ ] `retrospective.md` Q1-Q7 + Q8 if applicable (NEW class 1st app calibration narrative)
- [ ] `memory/project_phase57_23_auth_page_full_rebuild_round_2.md` (auto-memory subfile per REFACTOR-001 policy; ~250-300 char quality pointer compatible content)
- [ ] `memory/MEMORY.md` +1 quality-pointer line (subfile path + topic + keywords; ≤300 char)
- [ ] `.claude/rules/sprint-workflow.md` calibration matrix +1 row for NEW `frontend-mockup-strict-rebuild` 0.60 class 1st app baseline (Day 4 actual ratio observation)
- [ ] `CLAUDE.md` minimal-touch update:
  - Current Sprint row: `Sprint 57.23 closed YYYY-MM-DD (PR pending) — Auth Page Full Rebuild Round 2; see memory/project_phase57_23_*.md for detail. Next: Sprint 57.24 candidate per Sprint 57.22 audit Priority Matrix`
  - Last Updated footer: `**Last Updated**: YYYY-MM-DD (Sprint 57.23 — Auth Page Full Rebuild Round 2); see memory/ for sprint history`
  - NO additional `Latest Sprint` / `Prev Sprint` rows packed with retro detail (per REFACTOR-001 forbidden item)

### 4.6 Day 4 final commits + PR open
- [ ] Day 4 commit: `feat(frontend, sprint-57-23, Day 4): i18n + App.tsx wire + Vitest 348+N + retrospective + memory + DRIFT-REPORT`
- [ ] Day 4 closeout commit (CLAUDE.md + MEMORY.md + sprint-workflow.md): `chore(closeout-57-23): CLAUDE.md + MEMORY.md + calibration matrix sync`
- [ ] `git push -u origin feature/sprint-57-23-auth-page-full-rebuild-round-2`
- [ ] `gh pr create --title "feat(frontend, sprint-57-23): AD-Auth-Page-Full-Rebuild-Round-2 — 6 P0 Auth Routes Full Mockup-Fidelity Rebuild (Frontend-Only Spike)" --body "..."`
- [ ] CI green: pytest baseline preserved + frontend-ci 5 checks (lint / build / Vitest / Playwright if enabled / a11y if enabled)
- [ ] Verify PR CI 7 checks green (frontend tracks + V2 lints + sprint workflow checks)

### 4.7 Sprint complete verification
- [ ] All Acceptance Criteria 1-17 from plan met
- [ ] Anti-Pattern checklist 11/11 PASS (especially AP-2 demo banner discipline on register/invite/mfa)
- [ ] 3 doc syncs landed (CLAUDE.md / MEMORY.md / sprint-workflow.md calibration matrix)
- [ ] Phase 57+ Frontend status updated 18/N → 19/N
- [ ] 5+ NEW carryover ADs catalogued in retrospective Q6 for Phase 58+ (IAM Block B + Block C + WorkOS Multi-IdP + Recovery Page + Callback Loading UX Backend)
- [ ] AD-Auth-Page-Full-Rebuild-Round-2 CLOSED in retrospective Q5 (Sprint 57.24+ candidate = chat-v2 Phase-2 per Sprint 57.22 audit Priority Matrix)

---

## Estimated Workload Reference

- **Bottom-up est** ~46 hr → **calibrated commit** ~28 hr (`frontend-mockup-strict-rebuild` 0.60 × bottom-up)
- **Per-day informal target** (non-binding):
  - Day 0: ~3 hr (plan + checklist + 三-prong + reference captures)
  - Day 1: ~7 hr (AuthShell + login + dev)
  - Day 2: ~8 hr (callback + register 4-step wizard)
  - Day 3: ~7 hr (invite + mfa + expired)
  - Day 4: ~3 hr (i18n verify + App.tsx audit + Vitest + Playwright + closeout docs)
- Per-task actuals tracked in `progress.md` Day entries (not in this checklist per AD-Lint-2)
