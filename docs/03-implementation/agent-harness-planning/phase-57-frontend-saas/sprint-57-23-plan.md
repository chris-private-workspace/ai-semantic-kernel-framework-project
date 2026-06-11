---
sprint: 57.23
phase: Phase 57+ Frontend SaaS 19/N (pending close)
title: AD-Auth-Page-Full-Rebuild-Round-2 — 6 P0 Auth Routes Full Mockup-Fidelity Rebuild (Frontend-Only Spike)
class: frontend-mockup-strict-rebuild 0.60 (1st application; HYBRID weighted blend)
duration_days: 5 (Day 0 三-prong + Day 1 AuthShell refactor + login + dev / Day 2 callback + register / Day 3 invite + mfa + expired / Day 4 i18n + App.tsx wire + closeout)
related:
  - Sprint 57.22 plan + AUDIT-REPORT-COMPREHENSIVE.md (Unit 1-6 Auth Tier 1 P0)
  - Sprint 57.22 retrospective Q6 (AD-Auth-Page-Full-Rebuild-Round-2 top carryover)
  - Sprint 57.21 plan (mockup-direct port pattern reference)
  - CLAUDE.md §Frontend Mockup-Fidelity Hard Constraint (2026-05-17)
  - memory/feedback_frontend_mockup_fidelity_hard_constraint.md
  - reference/design-mockups/page-extras.jsx (AuthShell + AuthLogin + AuthCallback + AuthDev L1-200)
  - reference/design-mockups/page-auth-extras.jsx (AuthRegister + AuthInvite + AuthMFA + AuthExpired L1-418)
  - .claude/rules/sprint-workflow.md §Scope-class multiplier matrix
  - 01-eleven-categories-spec.md §Cat 9 (governance/HITL — MFA backend defer)
  - 17-cross-category-interfaces.md (no new contracts this sprint; frontend-only)
---

# Sprint 57.23 — AD-Auth-Page-Full-Rebuild-Round-2

## Sprint Goal

Rebuild **6 P0 Auth routes (login / callback / register / invite / mfa / expired) + 1 supporting route (dev-login)** to **1:1 mockup fidelity** per `reference/design-mockups/page-extras.jsx` + `page-auth-extras.jsx`, refactor `AuthShell` to mockup full-screen-centered pattern, and ship Composer richness via Roll-own TOTP + WebAuthn UI per mockup design — **frontend-only**, backend MFA/registration service deferred to Phase 58+ IAM Block C.

**Two-line philosophy** (per Sprint 57.20 Option W carry-forward):

1. **Frontend leads** — All 6 P0 + 1 supporting Auth routes rebuilt 1:1 from mockup; `AuthShell` rewritten in-place (no other `/auth/*` consumers exist); no incremental patching.
2. **Backend follows** — Existing endpoints reused (`/api/v1/auth/login` WorkOS OIDC redirect / `/auth/callback` cookie handshake / `/auth/dev-login`); new endpoints (register / invite-validate / mfa-enroll / mfa-verify) stubbed HTTP 501 NotImplemented; full backend wire deferred to Phase 58+ IAM Block C (MFA TOTP + WebAuthn) + IAM Block B (tenant register + invite flow).

## Background

### Why Sprint 57.23 (this sprint)

Sprint 57.22 AUDIT-REPORT-COMPREHENSIVE.md classified Auth as **Tier 1 P0** with all 6 of 6 units P0:

| Unit | Route | Audit score | Existing? | Mockup source | Rebuild hr (mid) |
|------|-------|-------------|-----------|---------------|------------------|
| 1 | `/auth/login` | 15% (FUNCTIONAL drift) | ✅ exists (Sprint 57.7) | `page-extras.jsx:27-57` | 6-8 hr |
| 2 | `/auth/callback` | 5% (STRUCTURAL — no UI) | ✅ exists (Sprint 57.7) | `page-extras.jsx:59-107` | 3-4 hr |
| 3 | `/auth/register` | 0% (missing route) | ❌ missing | `page-auth-extras.jsx:31-188` | 8-10 hr |
| 4 | `/auth/invite` | 0% (missing route) | ❌ missing | `page-auth-extras.jsx:191-246` | 6-8 hr |
| 5 | `/auth/mfa` | 0% (missing route) | ❌ missing | `page-auth-extras.jsx:249-371` | 8-10 hr |
| 6 | `/auth/expired` | 0% (missing route) | ❌ missing | `page-auth-extras.jsx:374-416` | 4-6 hr |
| **+ supporting** | `/auth/dev` (extracted from login) | n/a | ❌ embedded in login | `page-extras.jsx:109-185` (AuthDev) | 1-2 hr |
| **+ shell** | `AuthShell.tsx` refactor | 0% structural | ✅ exists (Sprint 57.7 → 57.13 Tailwind) | `page-extras.jsx:5-25` (AuthShell mockup) | 2-3 hr |

**Σ bottom-up**: ~38-51 hr (mid ~46 hr) before calibration

### Q1 + Q2 + Q3 decisions (2026-05-18 user alignment)

| # | Decision | Sprint 57.23 implication |
|---|----------|--------------------------|
| Q1 | **Mockup oklch indigo** as brand primary | ✅ Already wired (Sprint 57.18 `--primary: 234 89% 60%` light / `234 84% 70%` dark ≈ oklch indigo HSL); Day 1 Playwright MCP pair-verify visual parity (D-PRE-2 finding) |
| Q2 | **Frontend-only rebuild** | ✅ 0 backend code changes; backend register/invite/mfa endpoints stub 501; full wire → Phase 58+ IAM Block B/C |
| Q3 | **Roll-own TOTP + WebAuthn UI per mockup** | ✅ Frontend ship full mockup UI (6-digit TOTP grid + WebAuthn spinning ring); backend totp_secrets + webauthn_credentials tables + service → Phase 58+ IAM Block C |

### What is preserved (NOT rewritten)

| Layer | Specific | Reuse mechanism |
|-------|----------|-----------------|
| Auth API client | `fetchWithAuth` + tenant_id header | Unchanged for `/auth/login` (WorkOS redirect) + `/auth/callback` (cookie bootstrap) |
| WorkOS OIDC flow | Backend redirect chain `/api/v1/auth/login` → vendor → `/auth/callback` | Frontend just kicks off via `window.location.href` (login page) + receives via `useAuthStore.bootstrap()` (callback page) |
| DevLogin POST | `POST /api/v1/auth/dev-login` (DEV builds) | Extract `DevLoginSection` from login page into NEW `/auth/dev` route; same fetchWithAuth call preserved |
| `useAuthStore` + `consumePostLoginRedirect` | Bootstrap + redirect dispatch | Unchanged |
| Existing 14 routes | All non-`/auth/*` pages | NOT touched (auth flow isolated work) |
| `tailwind.config.ts` `--primary` token | indigo HSL (Sprint 57.18) | Per D-PRE-2: no new token needed |
| Vitest baseline | 348/348 (Sprint 57.21 close) | Adapt selectors for AuthShell + login rewrite (~5-10 spec updates); preserve behavioral assertions |

### What gets rewritten (this sprint scope)

| Layer | File | Approach |
|-------|------|----------|
| AuthShell | `frontend/src/components/AuthShell.tsx` | REWRITE in-place: full-screen centered card + radial gradient backdrop + brand mark slot + footer; no sticky header / no `container mx-auto p-6`; mockup `page-extras.jsx:5-25` 1:1 |
| Login | `frontend/src/pages/auth/login/index.tsx` | REWRITE: 3 SSO outline buttons (SAML / Microsoft / Google) disabled + tooltip placeholder + email + Continue primary button; DevLoginSection extracted; mockup `page-extras.jsx:27-57` 1:1 |
| Callback | `frontend/src/pages/auth/callback/index.tsx` | REWRITE: timed 3-step progress UI (Verifying SAML assertion / Resolving tenant + RLS context / Loading feature flags + memory scopes) per mockup `page-extras.jsx:59-107`; preserve `bootstrap()` + `consumePostLoginRedirect()` logic underneath |
| Dev-login | `frontend/src/pages/auth/dev/index.tsx` (NEW) | EXTRACT from `DevLoginSection` in current login + augment with mockup-fidelity wrapper (risk-high hitl-card banner + identity dropdown + assume button); mockup `page-extras.jsx:109-185` |
| Register | `frontend/src/pages/auth/register/index.tsx` (NEW) | 4-step wizard (Identity / Organization / Plan / Confirm) with stepper bar + per-step form state; mockup `page-auth-extras.jsx:31-188` 1:1; backend `POST /api/v1/tenants/register` stub 501 |
| Invite | `frontend/src/pages/auth/invite/index.tsx` (NEW) | Token-based invite acceptance UI; `:token` route param; metadata grid (Tenant/Invited by/Role/Expires) + name + password fields + Accept primary button; mockup `page-auth-extras.jsx:191-246` 1:1; backend `GET/POST /api/v1/invites/:token` stub 501 |
| MFA | `frontend/src/pages/auth/mfa/index.tsx` (NEW) | Tab selector (Authenticator / Security Key); 6-digit TOTP grid with auto-focus advance + countdown + Verify button; WebAuthn spinning conic-gradient ring + simulate fallback; mockup `page-auth-extras.jsx:249-371` 1:1; backend `POST /api/v1/mfa/{enroll,verify}` stub 501 |
| Expired | `frontend/src/pages/auth/expired/index.tsx` (NEW) | Session expired UX card (Last activity / Session ID / Reason badge) + 2 buttons (Sign in again / Resume session); mockup `page-auth-extras.jsx:374-416` 1:1; no backend wire (pure frontend display from `?session_id=` + `?reason=` query params) |
| App.tsx | `frontend/src/App.tsx` | Add 5 NEW `<Route>` entries via `lazy()` import (register / invite / mfa / expired / dev); preserve existing login + callback wiring; total 7 `/auth/*` routes |
| i18n | `frontend/src/i18n/locales/en/auth.json` + `zh-TW/auth.json` | +~40 keys (register.* / invite.* / mfa.* / expired.* / dev.*); preserve existing keys |
| Vitest specs | existing auth/login/callback specs | Selector adapt (AuthShell rewrite cascades); preserve behavioral assertions |
| Playwright e2e | existing auth flow specs | Selector adapt; happy-path register/invite/mfa specs defer (backend stubs 501) |

### V2 紀律對齐 (per Sprint 57.21 pattern)

- **約束 1 單一範疇歸屬**: 純 frontend sprint; all changes in `frontend/src/components/AuthShell.tsx` + `frontend/src/pages/auth/**` + `frontend/src/App.tsx` + i18n
- **約束 2 主流量驗證**: `/auth/*` routes are entry points to all gated pages; runtime Playwright MCP pair-verify required at Day 1 (AuthShell + login) + Day 3 (register/invite/mfa/expired) + Day 4 closeout
- **約束 3 LLM Provider Neutrality**: 0 SDK import preserved
- **約束 4 Anti-Pattern checklist**:
  - AP-2 (no Potemkin): MFA UI ships visually but backend stub 501 — **must visibly mark as "MFA backend wire pending Phase 58+ IAM Block C" demo banner** to honor AP-2
  - AP-4 (rename-only refactor): every rewrite delivers visible mockup-fidelity gain (Playwright MCP pair-verify artifact + DRIFT verdict per page)
  - AP-3 (cross-directory scattering): all auth routes stay in `frontend/src/pages/auth/<route>/index.tsx`; AuthShell stays at `components/AuthShell.tsx`
- **約束 5 測試優先**: Vitest 348 baseline preserved; NEW specs (~20-30 cases for 4 new pages + AuthShell refactor); Playwright e2e baseline preserved (selector adapt)

## User Stories

### Group A — Day 0 setup + 三-prong + Playwright MCP reference captures

**US-A1**: As a Sprint 57.23 owner, I want plan/checklist landed + feature branch created + Day 0 三-prong (Prong 1 path + Prong 2 content + Prong 3 schema N/A) drift findings catalogued in `progress.md` + Playwright MCP screenshot pipeline ready for both mockup (port 8080) + production (port 3007) at 1440×900 + 6 mockup reference captures saved to `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-23/artifacts/auth-page-full-rebuild-round-2/screenshots/mockup/` so that Day 1+ work has visual ground truth artifacts.

### Group B — AuthShell + Login + Dev (Day 1)

**US-B1**: As an unauthenticated user, I want `AuthShell.tsx` rewritten to mockup full-screen-centered pattern (radial gradient backdrop with primary 12% alpha + brand mark slot + 420-wide column + optional footer slot) per mockup `page-extras.jsx:5-25` so that all `/auth/*` pages match mockup visual baseline at 1440×900.

**US-B2**: As a returning user signing in, I want `/auth/login` rewritten with 3 SSO outline buttons (SAML SSO / Microsoft / Google Workspace) + "or" divider + Work email input + "Continue" primary button + MFA hint + dev-login link per mockup `page-extras.jsx:27-57` so that login UX matches mockup; 3 SSO buttons render disabled with tooltip "Enterprise SSO via WorkOS roadmap" (deferred to AD-WorkOS-Multi-IdP-Phase58); "Continue" button preserves existing WorkOS OIDC flow.

**US-B3**: As a dev / non-prod operator, I want DevLoginSection extracted from login into separate `/auth/dev` route per mockup `page-extras.jsx:109-185` (AuthDev) with risk-high hitl-card banner + identity dropdown ("jamie@acme.com · operator" / etc.) + "Assume identity" button so that dev-login is visually distinct from production login flow; production builds gate the route to 404 via `import.meta.env.DEV` check.

### Group C — Callback + Register (Day 2)

**US-C1**: As a user returning from IdP redirect, I want `/auth/callback` rewritten with timed 3-step progress UI per mockup `page-extras.jsx:59-107` (Verifying SAML assertion → Resolving tenant + RLS context → Loading feature flags + memory scopes) using frontend-only `setTimeout` transitions (800/1800/2800ms simulated) so that callback UX matches mockup; existing `bootstrap()` + `consumePostLoginRedirect()` logic preserved underneath (kicks off in parallel with timed UI; whichever completes first wins navigation, with min 2800ms enforced for UX consistency).

**US-C2**: As a new tenant signing up, I want `/auth/register` (NEW route) rendering 4-step wizard per mockup `page-auth-extras.jsx:31-188` (Identity → Organization → Plan → Confirm) with stepper bar + per-step form state + Continue/Back navigation + final summary card with terms checkbox + verification hint so that self-serve onboarding UX ships; backend `POST /api/v1/tenants/register` stub 501 + "Backend wire pending Phase 58+ IAM Block B" demo banner.

### Group D — Invite + MFA + Expired (Day 3)

**US-D1**: As an invited user clicking an email link, I want `/auth/invite/:token` (NEW route with `:token` param) rendering invite acceptance UI per mockup `page-auth-extras.jsx:191-246` (avatar icon + metadata grid for Tenant/Invited by/Role/Expires + Full name input + Set password input + Accept primary button + MFA notice) so that invite flow UX ships; backend `GET /api/v1/invites/:token` validate + `POST /api/v1/invites/:token/accept` stub 501 + demo banner.

**US-D2**: As a user prompted for MFA after sign-in, I want `/auth/mfa` (NEW route) rendering tab selector (Authenticator / Security Key) + 6-digit TOTP grid with auto-focus advance + Backspace step-back + countdown ("code refreshes in 23s") + Verify button + recovery code link per mockup `page-auth-extras.jsx:249-371` AuthMFA component; WebAuthn tab shows spinning conic-gradient ring + simulate fallback button so that MFA UX ships visually per Q3 Roll-own design; backend `POST /api/v1/mfa/{enroll,verify}` stub 501 + demo banner.

**US-D3**: As a user with expired session, I want `/auth/expired` (NEW route) rendering session expired card per mockup `page-auth-extras.jsx:374-416` (warning icon + title + sub + metadata grid for Last activity / Session ID / Reason badge + 2 buttons Sign in again / Resume session + data preservation hint) so that expiry UX matches mockup; route accepts `?session_id=` + `?reason=` query params for metadata display (fixture fallback if absent).

### Group E — i18n + App.tsx wire + Vitest + closeout (Day 4)

**US-E1**: As a multilingual operator, I want `frontend/src/i18n/locales/en/auth.json` + `zh-TW/auth.json` extended with ~40 NEW keys covering `auth.register.*` (workEmail / fullName / companyName / tenantSlug / region / size / plan.* / confirm.* / verify / terms / continue / back / create) + `auth.invite.*` (title / subtitle / fullName / password / passwordHint / accept / mfaHint / foot) + `auth.mfa.*` (title / totpSub / webauthnSub / verify / recoveryCode / webauthnHint / simulate / foot / help) + `auth.expired.*` (title / subtitle / signInAgain / resume / dataHint) + `auth.dev.*` so that all NEW pages render in both EN and zh-TW.

**US-E2**: As a routing maintainer, I want `frontend/src/App.tsx` updated with 5 NEW `<Route>` entries (`/auth/register` / `/auth/invite/:token` / `/auth/mfa` / `/auth/expired` / `/auth/dev`) wired via `React.lazy()` import per existing `LoginPage` + `CallbackPage` pattern + DEV-only gate on `/auth/dev` (404 fallback in production builds) so that all 7 `/auth/*` routes accessible from URL.

**US-E3**: As a Sprint 57.23 owner, I want Vitest 348 baseline grown to 348+N (N≥15 covering NEW page rendering + form validation + stepper navigation + TOTP input grid logic + AuthShell wrap) without regression + Playwright e2e auth flow baseline preserved (selector adapt for AuthShell rewrite; happy-path register/invite/mfa e2e deferred until backend wire) + commits + retrospective.md Q1-Q7 + memory snapshot `memory/project_phase57_23_*.md` + MEMORY.md +1 line + `.claude/rules/sprint-workflow.md` calibration matrix +1 row for NEW `frontend-mockup-strict-rebuild` 0.60 class 1st app + CLAUDE.md Current Sprint row + Last Updated footer landed so that Sprint 57.23 = COMPLETE and Phase 57+ Frontend 19/N opens cleanly.

## Technical Specifications

### AuthShell.tsx rewrite — mockup full-screen-centered

```typescript
// AFTER (mockup-direct port)
import type { FC, ReactNode } from "react";

interface AuthShellProps {
  children: ReactNode;
  footer?: ReactNode;
}

export const AuthShell: FC<AuthShellProps> = ({ children, footer }) => {
  return (
    <div
      data-testid="auth-shell"
      className="min-h-screen flex items-center justify-center p-10"
      style={{
        background:
          "radial-gradient(ellipse 800px 600px at 50% -10%, hsl(var(--primary) / 0.12) 0%, transparent 60%), hsl(var(--background))",
      }}
    >
      <div className="w-[420px] flex flex-col gap-[18px]">
        {/* Brand mark + IPA Platform + V2 · loop-first metadata */}
        <div className="flex flex-row gap-2.5 mb-1 justify-center items-center">
          <div className="w-8 h-8 rounded-md bg-primary" aria-hidden />
          <div>
            <div className="text-base font-semibold">IPA Platform</div>
            <div className="text-[10.5px] font-mono uppercase tracking-[0.04em] text-fg-subtle">V2 · loop-first</div>
          </div>
        </div>
        {children}
        {footer && <div className="text-[11px] text-fg-subtle text-center mt-1">{footer}</div>}
      </div>
    </div>
  );
};
```

**Note**: One escape-hatch `style={{ background: "radial-gradient..." }}` is allowed (per STYLE.md §3 — when no Tailwind utility maps cleanly to multi-stop gradient with HSL variables). Documented in MHist.

### App.tsx route additions (7 total `/auth/*` routes)

```typescript
const LoginPage = lazy(() => import("./pages/auth/login"));        // existing
const CallbackPage = lazy(() => import("./pages/auth/callback"));  // existing
const RegisterPage = lazy(() => import("./pages/auth/register"));  // NEW
const InvitePage = lazy(() => import("./pages/auth/invite"));      // NEW
const MFAPage = lazy(() => import("./pages/auth/mfa"));            // NEW
const ExpiredPage = lazy(() => import("./pages/auth/expired"));    // NEW
const DevPage = lazy(() => import("./pages/auth/dev"));            // NEW (DEV-only — 404 in prod)

// Routes
<Route path="/auth/login" element={<LoginPage />} />
<Route path="/auth/callback" element={<CallbackPage />} />
<Route path="/auth/register" element={<RegisterPage />} />
<Route path="/auth/invite/:token" element={<InvitePage />} />
<Route path="/auth/mfa" element={<MFAPage />} />
<Route path="/auth/expired" element={<ExpiredPage />} />
{import.meta.env.DEV && <Route path="/auth/dev" element={<DevPage />} />}
```

### Token usage (per Sprint 57.18 wired tokens; D-PRE-2 finding)

| Mockup CSS var | Production Tailwind class | Verified? |
|----------------|---------------------------|-----------|
| `var(--primary)` | `bg-primary` / `text-primary` / `ring-primary/20` | ✅ wired Sprint 57.18 (HSL 234 89% 60% light / 234 84% 70% dark) |
| `var(--bg)` | `bg-background` (Sprint 57.18 root token) | ✅ wired |
| `var(--bg-1)` | `bg-bg-1` (Sprint 57.20 layout token) | ✅ wired |
| `var(--bg-2)` | `bg-bg-2` | ✅ wired |
| `var(--bg-3)` | `bg-bg-3` | ✅ wired |
| `var(--fg)` | `text-foreground` | ✅ wired |
| `var(--fg-muted)` | `text-fg-muted` | ✅ wired |
| `var(--fg-subtle)` | `text-fg-subtle` | ✅ wired |
| `var(--border)` | `border-border` | ✅ wired |
| `var(--warning)` | `bg-warning` / `text-warning` | ✅ wired (Sprint 57.18 semantic) |
| `var(--success)` | `bg-success` | ✅ wired |
| `var(--primary)/0.10–0.14` alpha | `bg-primary/10` / `bg-primary/[0.14]` arbitrary | ✅ Tailwind utility |
| `oklch(from var(--primary) l c h / 0.12)` | `bg-primary/[0.12]` Tailwind arbitrary alpha | ✅ approximation |

**No new tokens needed this sprint.**

### MFA UI implementation detail (Q3 Roll-own per mockup)

- **TOTP tab** (default): 6 single-digit `<input>` boxes with `ref` array + auto-focus advance on digit entry + Backspace step-back; `inputMode="numeric"` + `maxLength={1}`; `defaultChecked` indigo border + 10% alpha bg when filled; Verify button disabled until all 6 digits entered; countdown "code refreshes in 23s" (static text — no real TOTP rotation; backend wire defers)
- **WebAuthn tab**: conic-gradient spinning ring (CSS `animation: spin 2.5s linear infinite`) + Shield icon + "Insert your security key or use platform authenticator" hint + "Simulate success" ghost button (DEV-only fallback)
- **Recovery code link**: routes to `/auth/recovery` (NEW route deferred to Phase 58+; current sprint shows as inactive link — Tailwind `pointer-events-none` + tooltip "Recovery flow pending Phase 58+ IAM Block C")
- **Backend stub**: `POST /api/v1/mfa/enroll` + `POST /api/v1/mfa/verify` return HTTP 501 NotImplemented; frontend `Verify` button on submit calls fetch + catches 501 + shows demo banner "MFA backend wire pending Phase 58+ IAM Block C"

### Register 4-step wizard implementation detail

- **Stepper bar**: 4 circles connected by horizontal lines; current step = primary bg + white text; completed steps = primary bg + check icon; future steps = bg-3 + border + fg-subtle text
- **Per-step state**: `useState` for `step` (0-3) + step-local form state (email/name → org-slug-region-size → plan → terms)
- **Step 0 (Identity)**: Work email + Full name + SAML hint
- **Step 1 (Organization)**: Company name + Tenant slug (with `.ipa.platform` suffix) + Region dropdown (ap-east-1 / us-east-1 / eu-west-1 / ap-northeast-1) + Size dropdown
- **Step 2 (Plan)**: 3 radio cards (Trial / Pro $1,200/mo / Enterprise Custom); Pro defaultChecked
- **Step 3 (Confirm)**: Summary hitl-card severity=risk-low + terms checkbox + verification hint
- **Navigation**: Back button (steps 1-3) + Continue button (steps 0-2) / Create workspace button (step 3 → POST register stub 501)

### Backend impact

**0 backend changes this sprint** (Q2 frontend-only decision). Endpoint stub 501s relied upon (no need to write):
- `POST /api/v1/tenants/register` — register submit (501)
- `GET /api/v1/invites/:token` — invite validate (501)
- `POST /api/v1/invites/:token/accept` — invite accept (501)
- `POST /api/v1/mfa/enroll` — MFA enroll (501)
- `POST /api/v1/mfa/verify` — MFA verify (501)

Carryover ADs for backend wire:
- 🆕 **AD-Auth-Register-Backend-IAM-Block-B-Phase58** (tenants/register + email verification + JWT minting)
- 🆕 **AD-Auth-Invite-Backend-IAM-Block-B-Phase58** (invites validate/accept + cascade to user create + tenant membership)
- 🆕 **AD-Auth-MFA-Backend-IAM-Block-C-Phase58** (totp_secrets + webauthn_credentials tables + Cat 9 service + recovery codes)
- 🆕 **AD-Auth-Callback-Loading-UX-Phase58** (backend OIDC multi-step status emission — currently mocked via 3 setTimeout transitions; future real SSE per step)

## File Change List

**NEW files**:
- `frontend/src/pages/auth/register/index.tsx` (~280 lines; mockup AuthRegister 4-step wizard)
- `frontend/src/pages/auth/invite/index.tsx` (~120 lines; mockup AuthInvite)
- `frontend/src/pages/auth/mfa/index.tsx` (~200 lines; mockup AuthMFA with TOTP + WebAuthn tabs)
- `frontend/src/pages/auth/expired/index.tsx` (~90 lines; mockup AuthExpired)
- `frontend/src/pages/auth/dev/index.tsx` (~120 lines; extracted DevLoginSection + mockup AuthDev wrapper)
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-23/artifacts/auth-page-full-rebuild-round-2/screenshots/{mockup,prod}/*.png` (~12 files Playwright MCP captures)
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-23/artifacts/auth-page-full-rebuild-round-2/DRIFT-REPORT-AUTH-ROUND-2.md` (Day 4 closeout output)

**REWRITE files** (in-place behavior preserve):
- `frontend/src/components/AuthShell.tsx` (rewrite — full-screen centered + gradient + brand mark + footer slot)
- `frontend/src/pages/auth/login/index.tsx` (rewrite — 3 SSO outline + email + Continue; extract DevLoginSection)
- `frontend/src/pages/auth/callback/index.tsx` (rewrite — timed 3-step progress + parallel bootstrap)

**EDIT files**:
- `frontend/src/App.tsx` (+5 lazy imports + 5 `<Route>` entries; preserve existing 2)
- `frontend/src/i18n/locales/en/auth.json` (+~40 keys for register/invite/mfa/expired/dev)
- `frontend/src/i18n/locales/zh-TW/auth.json` (+~40 keys parallel)
- existing Vitest specs for AuthShell + login + callback (selector adapt; preserve behavioral assertions)
- existing Playwright e2e specs `tests/e2e/auth/*.spec.ts` (selector adapt)

**NEW docs**:
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-23/progress.md` (Day 0-4 entries)
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-23/retrospective.md` (Day 4 Q1-Q7)
- `memory/project_phase57_23_auth_page_full_rebuild_round_2.md` (auto-memory subfile)

**EDIT docs** (closeout):
- `CLAUDE.md` (Current Sprint row + Last Updated footer per REFACTOR-001 §Sprint Closeout policy — minimal touch)
- `memory/MEMORY.md` (+1 quality-pointer line)
- `.claude/rules/sprint-workflow.md` calibration matrix (+1 row for NEW `frontend-mockup-strict-rebuild` 0.60 class 1st app)

Sprint total: ~30 file touches (5 NEW pages + 3 rewrite + ~7 edit + ~5 doc + ~10 test/spec adapt).

## Acceptance Criteria

1. `AuthShell.tsx` renders full-screen centered card per mockup with radial gradient backdrop + brand mark + footer slot at 1440×900 — Playwright MCP pair-verify
2. `/auth/login` renders 3 SSO outline buttons (disabled + tooltip) + email + Continue primary button per mockup; existing WorkOS OIDC redirect preserved on Continue click — Playwright MCP pair-verify + behavioral test
3. `/auth/callback` renders timed 3-step progress UI per mockup (Verifying SAML / Resolving tenant / Loading flags); existing `bootstrap()` + redirect dispatch preserved with min 2800ms UI duration — Playwright MCP pair-verify + behavioral test
4. `/auth/dev` (NEW; DEV-only) renders risk-high hitl-card + identity dropdown + Assume identity button per mockup AuthDev; production build returns 404 — Playwright MCP pair-verify (DEV only)
5. `/auth/register` (NEW) renders 4-step wizard per mockup AuthRegister with stepper bar + Back/Continue navigation + Create button → POST stub 501 + demo banner — Playwright MCP pair-verify + Vitest stepper logic
6. `/auth/invite/:token` (NEW) renders invite acceptance UI per mockup AuthInvite; backend GET stub 501 + demo banner — Playwright MCP pair-verify
7. `/auth/mfa` (NEW) renders Tab selector + 6-digit TOTP grid with auto-focus advance + WebAuthn spinning ring + Verify button per mockup AuthMFA; backend POST stub 501 + demo banner — Playwright MCP pair-verify + Vitest TOTP input logic
8. `/auth/expired` (NEW) renders session expired card per mockup AuthExpired with metadata grid + 2 buttons; route accepts `?session_id=` + `?reason=` query params — Playwright MCP pair-verify
9. `frontend/src/App.tsx` wires 5 NEW lazy-imported `<Route>` entries with DEV-only gate on `/auth/dev`
10. i18n keys ~40 added EN + zh-TW symmetric; no key drift between locales (verified by symmetric-keys test if exists, else manual diff)
11. Vitest 348 baseline grown to 348+N (N≥15); 0 regression — `npm run test` in `frontend/`
12. Playwright e2e auth flow baseline preserved (selector adapt only); new page happy-path e2e deferred to backend wire — `npm run playwright` in `frontend/`
13. Build < 3s + main bundle within +40 KB of Sprint 57.22 baseline (321.92 kB) — `npm run build`
14. 0 backend changes ✅ verified by `git diff --stat main..HEAD` showing only `frontend/` + `docs/` + `claudedocs/` + `memory/` + `.claude/rules/sprint-workflow.md` paths
15. 0 LLM SDK leak in frontend (`grep -rn "import openai\|import anthropic" frontend/src/` = 0)
16. Anti-Pattern checklist 11/11 PASS (AP-2 demo banner discipline on register/invite/mfa pages)
17. AD-Auth-Page-Full-Rebuild-Round-2 Round-2 catalogued as CLOSED in retrospective Q5 (next: Round-3 governance pages — Sprint 57.25 candidate per Sprint 57.22 audit Priority Matrix)

## Workload

- Bottom-up estimate: ~38-51 hr (Unit 1-6 audit sum 35-46 + AuthShell refactor 2-3 + /auth/dev extraction 1-2 + i18n ~40 keys ~2 + Day 0 三-prong 2 + Day 4 closeout 3)
- Mid bottom-up: **~46 hr**
- Calibration multiplier: **0.60** (`frontend-mockup-strict-rebuild` NEW class 1st application; HYBRID weighted blend per Sprint 57.22 §Sprint 57.23+ Recommendation: AuthShell refactor mockup-direct 0.55 ~10% + page rebuilds mockup-direct 0.55 ~60% + i18n + tests ~0.65 ~15% + closeout 0.80 ~15% = mid ~0.60)
- Calibrated commit: **~28 hr** (5-day solo-dev sprint at ~5-6 hr/day)

**Calibration note** (1st application of NEW class):

- Per Sprint 57.22 retrospective Q6 + §Sprint 57.23+ Recommendation: `frontend-mockup-strict-rebuild` 0.55-0.65 range proposed; mid 0.60 baseline for Sprint 57.23
- 3-sprint window rule: 1-data-point insufficient for adjustment; KEEP 0.60 this sprint regardless of ratio outcome
- If ratio < 0.7 (over-conservative haircut; bottom-up too generous) → AD-Sprint-Plan-NEW propose 0.60 → 0.40-0.50 for Sprint 57.24+
- If ratio > 1.2 (haircut too aggressive; bottom-up was accurate) → propose 0.60 → 0.75-0.80
- If ratio in [0.85, 1.20] band → maintain 0.60; baseline validated

## Risks & Mitigations

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|-----------|
| R1 | AuthShell rewrite breaks existing `/auth/login` + `/auth/callback` Vitest + Playwright specs cascading via selector changes | High | Medium | Day 1 first action: AuthShell rewrite + adapt existing 2 page specs in same commit before moving to login rewrite; full Vitest run before Day 1 EOD |
| R2 | 3 disabled SSO buttons (SAML / Microsoft / Google) on login page violate AP-2 (Potemkin) if not visibly marked | Medium | Medium | US-B2 acceptance: tooltip "Enterprise SSO via WorkOS roadmap" + `aria-disabled` + visible secondary styling; document fixture state in i18n key |
| R3 | MFA UI on `/auth/mfa` ships visually but backend stub 501 creates Potemkin appearance | High | Medium | US-D2 acceptance: visible "MFA backend wire pending Phase 58+ IAM Block C" demo banner above form; styled like Sprint 57.21 SessionList "Demo data" banner |
| R4 | Register 4-step wizard form validation complexity exceeds Day 2 budget | Medium | Medium | Day 2 scope: skip exhaustive validation (only required-field check + basic email regex); detailed validation (tenant-slug uniqueness check / region availability / etc.) → Phase 58+ when backend wires |
| R5 | TOTP 6-digit input grid auto-focus advance logic flaky in edge cases (paste 6 digits / mobile keyboard / RTL languages) | Medium | Low | US-D2 acceptance: handle paste event (split 6 chars into boxes); skip RTL test (out of scope; defer to Phase 58+ a11y audit) |
| R6 | i18n ~40 NEW keys × 2 locales = ~80 strings; symmetric-keys check might surface drift | Medium | Low | Day 4 first action: write both locales in parallel (copy EN keys → translate zh-TW); run symmetric-keys check if exists (or manual diff); fix drift before commit |
| R7 | Playwright e2e auth flow baseline regression from AuthShell rewrite (currently has sticky header `<h1>`; new mockup has NO h1) | Medium | High | Day 1 EOD: run full Playwright auth suite; adapt selectors using `data-testid="auth-shell"` anchor (US-B1) instead of `<h1>` text-content; preserve behavioral assertions |
| R8 | DevLoginSection extraction breaks `import.meta.env.DEV` gating (could expose /auth/dev in production) | Low | High | US-B3 acceptance: App.tsx route definition wrapped in `import.meta.env.DEV &&` condition; production build NOT include route at all (verified via `npm run build && grep "auth/dev" dist/`) |
| R9 | Sprint 57.20 Geist font / Sprint 57.18 token cascade pushes auth pages out of mockup font baseline | Medium | Medium | Day 0 三-prong D-PRE-2 already verified primary token; Day 1 Playwright MCP pair-verify confirms Geist + token visual baseline; if drift > cosmetic → iterate Tailwind |
| R10 | NEW Vitest specs for 4 new pages introduce module-level singleton leakage (chatStore-style Risk Class C) | Low | Low | Per sprint-workflow.md Common Risk Class C: each new page Vitest uses `beforeEach` reset for `useAuthStore` if pages consume it; pure-render specs (most NEW pages) have no shared singletons |

### Common Risk Classes referenced (sprint-workflow.md)

- **Risk Class A (paths-filter)**: N/A — pure frontend, no `.github/workflows/` changes
- **Risk Class B (mypy unused-ignore)**: N/A — no Python changes
- **Risk Class C (singleton across test loops)**: R10 mitigation for `useAuthStore` consumers

## Dependencies

- Sprint 57.22 merged (✅ main HEAD `1840cb27`) + PR #155 squash merged
- Mockup `page-extras.jsx` (✅ confirmed exists at `reference/design-mockups/page-extras.jsx` 991 lines — AuthShell + AuthLogin + AuthCallback + AuthDev at L1-200)
- Mockup `page-auth-extras.jsx` (✅ confirmed exists at `reference/design-mockups/page-auth-extras.jsx` 418 lines — AuthShellX re-export + AuthRegister + AuthInvite + AuthMFA + AuthExpired)
- Sprint 57.18 + 57.20 tokens (`--primary` indigo / `--bg-1` / `--fg-subtle` / `--warning` / `--success`) available (✅ wired)
- Sprint 57.20 Geist font / dark default active (✅ wired)
- Sprint 57.21 Vitest 348 baseline (✅ post-merge)
- Dev server port 3007 runnable (✅ confirmed Sprint 57.21)
- Mockup http.server runnable at port 8080 (✅ confirmed Sprint 57.21)
- Backend `/api/v1/auth/login` + `/auth/callback` + `/auth/dev-login` endpoints unchanged (✅ existing)

## Cross-Sprint Carryovers

**Preserved from Sprint 57.22** (top priority Sprint 57.23+ scope confirmed):

- 🔴 **AD-Auth-Page-Full-Rebuild-Round-2** — TARGETED THIS SPRINT (Sprint 57.23 close = AD CLOSED for Round-2)
- 🆕 **AD-AuthShell-Mockup-Refactor** — TARGETED THIS SPRINT (US-B1)
- 🆕 **AD-WorkOS-Multi-IdP-Phase58** — DEFERRED (3 SSO outline buttons disabled placeholder this sprint)
- 🆕 **AD-Auth-Callback-Loading-UX-Phase58** — PARTIALLY ADDRESSED (frontend timed UI this sprint; backend SSE per-step → Phase 58+)
- 🆕 **AD-Brand-Primary-Color-Decision** — CLOSED via Q1 (oklch indigo confirmed; Sprint 57.18 wiring already aligns)

**Opens this sprint** (likely carryovers to Phase 58+):

- 🆕 **AD-Auth-Register-Backend-IAM-Block-B-Phase58** (tenants/register + email verification + JWT minting)
- 🆕 **AD-Auth-Invite-Backend-IAM-Block-B-Phase58** (invites validate/accept + cascade to user create + tenant membership)
- 🆕 **AD-Auth-MFA-Backend-IAM-Block-C-Phase58** (totp_secrets + webauthn_credentials tables + Cat 9 service + recovery codes)
- 🆕 **AD-Auth-Recovery-Page-Phase58** (recovery code entry page deferred; MFA tab footer link inactive this sprint)
- 🆕 **AD-WorkOS-Multi-IdP-Phase58** (SAML SSO + Microsoft + Google Workspace via WorkOS organization-level config; 3 outline buttons currently disabled placeholders)

## Out of Scope (Explicit)

- ❌ Backend `POST /api/v1/tenants/register` real implementation (stub 501)
- ❌ Backend invite token validation + acceptance real implementation (stub 501)
- ❌ Backend MFA TOTP secret + WebAuthn credential storage + service (stub 501)
- ❌ Recovery codes flow (MFA tab footer link inactive)
- ❌ WorkOS Multi-IdP (SAML/Microsoft/Google) backend organization wire — 3 outline buttons disabled
- ❌ Real OIDC multi-step backend status SSE (callback uses frontend-only setTimeout simulation)
- ❌ Sprint 57.22 audit Auth Tier 2 routes (Round-3 Auth flow polish — Sprint 57.24+ candidate per audit Priority Matrix)
- ❌ Other audit P0 routes (chat-v2 Phase-2 / governance / tenant-settings / etc.) — Sprint 57.24+ per Phase 57.23-57.32 epic roadmap
- ❌ Visual regression baseline regeneration in CI (Sprint 57.14 mechanism; can run end-of-sprint if needed but not required deliverable)
- ❌ Lighthouse hard-gate promotion (AD-Lighthouse-Visual-Hard-Gate carryover; not Sprint 57.23 scope)

## Definition of Sprint Complete

- [ ] All Acceptance Criteria 1-17 met
- [ ] Anti-Pattern checklist 11/11 PASS
- [ ] 3 doc syncs landed (CLAUDE.md / MEMORY.md / sprint-workflow.md calibration matrix +1 row for NEW class 1st app)
- [ ] PR opened against main + CI 7 checks green
- [ ] Closeout PR (chore) opened with doc syncs if not bundled into main PR
- [ ] Phase 57+ Frontend status updated 18/N → 19/N
- [ ] 5+ NEW carryover ADs catalogued in retrospective for Phase 58+ (IAM Block B + Block C + AD-WorkOS-Multi-IdP + AD-Recovery-Page + AD-Callback-Loading-UX-Backend)
