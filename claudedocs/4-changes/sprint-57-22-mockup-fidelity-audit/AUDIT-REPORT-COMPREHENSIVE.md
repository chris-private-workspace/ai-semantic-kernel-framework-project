# AUDIT-REPORT-COMPREHENSIVE — Mockup vs Production Visual Fidelity

**Sprint**: 57.22 — AD-Mockup-Fidelity-Comprehensive-Audit
**Date**: 2026-05-18 (Day 1 in progress)
**Audit scope**: ~40 route-level audit units (all 4 user-selected page groups: Auth + Operations + Governance + Chat-v2 Phase-2 + remaining Admin/Misc)
**Bar**: Strict 1:1 ±2px / ≥95% visual match (per user 2026-05-18 AskUserQuestion)
**Methodology**: Playwright MCP screenshot at 1440×900 viewport, both mockup http server (:8080/#<route>) and production dev server (:3007<route>), side-by-side compared with classified diff matrix.

---

## Diff Matrix Definition

For each audit unit:

| Field | Pass criteria |
|-------|---------------|
| Layout | Section structure + grid composition matches mockup ±2px tolerance |
| Typography | Font family = Geist Sans / Noto Sans TC; mockup-specific micro-sizes (11px / 11.5px / 12px / 12.5px / 13px) ±0.5px |
| Spacing | Padding / margin / gap ±2px tolerance |
| Shadow / radius | Card border-radius + shadow class matches mockup |
| Color tokens | Background / foreground / accent / risk severity computed RGB exact match |
| Interactivity | Hover / focus / disabled / active states all match mockup behavior |

**Severity classification**:
- **cosmetic** = Layout PASS, only Typography/Spacing/Shadow/Color diff
- **structural** = Layout FAIL, sections missing or reorganized
- **functional** = Behavioral or interactivity broken

**Strict 1:1 score** = weighted average:
- Layout 30% + Typography 20% + Spacing 20% + Shadow/Radius 10% + Color 10% + Interactivity 10%

---

## Group: Auth Pages (6 units)

### Unit 1: /auth/login

**Screenshots**:
- Mockup: `screenshots/mockup/auth-login.png` (mockup http://localhost:8080/#auth-login at 1440×900)
- Prod: `screenshots/prod/auth-login.png` (production http://localhost:3007/auth/login at 1440×900)

**Last ported**: NEVER. Created Sprint 57.7 commit `51162fd5` (pre-mockup); last touched Sprint 57.13 commit `1c0e55d7` for Foundation 1/N. **Predates Sprint 57.18 mockup-integration foundation** so never went through mockup-direct port.

**Mockup structure** (oklch theme; `--primary-h: 250` indigo):
- NO header / NO sidebar / NO sticky h1 — pure full-screen centered card layout
- Card: 400×432 at (520, 228) — horizontally centered; bg `oklch(0.165 0.006 260)`; border-radius **12px**; NO shadow
- Content sequence (top→bottom inside card):
  1. (no heading; mockup intentional — branded by card design alone)
  2. "Continue with SAML SSO" outline button (370×36; 13.5px / 500; radius 6px)
  3. "Continue with Microsoft" outline button (same style)
  4. "Continue with Google Workspace" outline button (same style)
  5. Email input `placeholder="you@acme.com"` (370×36; 13.5px / 400; padding 6px 9px; radius 6px)
  6. "Continue" PRIMARY button bg `oklch(0.62 0.16 250)` indigo (370×36; 13.5px / 500; radius 6px; inset shadow)
- Body bg: `oklch(0.135 0.005 260)` dark slate; body font 13px / Geist / weight 400

**Production structure** (shadcn slate theme; class="dark"):
- AuthShell wraps the page (has its own `<main class="container mx-auto flex-1 p-6">` 24px inset — NOT full screen)
- Sticky **h1** "IPA Platform V2 — Sign In" at (513, 146); 18px / 600 (mockup has NO heading at all)
- Form: 414×213 at (513, 292); NOT a card, just `<form class="mt-8 border-t border-dashed border-border pt-6">` with dashed-top-border separator
- Content sequence:
  1. h1 "IPA Platform V2 — Sign In"
  2. (description / sub-text)
  3. "Login with WorkOS" primary button bg `rgb(114, 127, 243)` (414×36; 14px / 500; radius 6px) — close indigo but different RGB / token
  4. Dev-login section: 2 inputs (206×30; 14px / 400; padding 4px 8px; radius **4px** — mockup is 6px) + "Dev Login" small secondary button (80×32; 12px / 500)
- Body bg: `rgb(2, 8, 23)` (closest is `slate-950`) — totally different palette from mockup oklch
- Body font 16px / Geist / weight 400 — **23% larger than mockup 13px**

**Diff matrix**:

| Field | Status | Detail |
|-------|--------|--------|
| **Layout** | ❌ FAIL | Production wraps in `AuthShell` + `container mx-auto p-6` inset; mockup is full-screen no-shell. Production has h1 above form; mockup has NO heading. Form vertical position differs (mockup card at y=228 / prod form at y=292). |
| **Typography** | ❌ FAIL | Body 13px (mockup) vs 16px (prod) = 23% size diff. Buttons 13.5px (mockup) vs 14px (prod). Inputs 13.5px (mockup) vs 14px (prod). All over the ±0.5px tolerance bar. |
| **Spacing** | ❌ FAIL | Card padding mockup-internal; production form padding `24px 0px 0px` (top inset only — dashed border separator). Input padding 6/9px (mockup) vs 4/8px (prod). |
| **Shadow / Radius** | ❌ FAIL | Card radius 12px (mockup) vs none (prod — form not a card). Input radius 6px (mockup) vs 4px (prod). Primary button inset-shadow (mockup) vs none (prod). |
| **Color** | ❌ FAIL | Body bg `oklch(0.135 0.005 260)` mockup vs `rgb(2, 8, 23)` slate-950 prod = different gamut + tone. Primary `oklch(0.62 0.16 250)` mockup vs `rgb(114, 127, 243)` prod = both indigo but different lightness/chroma. Card bg `oklch(0.165)` mockup vs transparent prod (form has no bg). |
| **Interactivity** | ⚠️ PARTIAL | Both have a primary submit button. Mockup expects 3 SSO outline buttons (SAML / Microsoft / Google) + email + Continue 5-action flow. Production has 1 WorkOS button + 2 dev-login inputs + Dev-Login button = 2-action flow. **Different IdP flow design entirely** (production = WorkOS managed; mockup = enterprise SSO matrix). |

**Severity**: **FUNCTIONAL** (not just cosmetic — entire IdP UX flow differs; 3 mockup SSO providers missing; dev-login section added per Sprint 57.13 not in mockup).

**Strict 1:1 score**: **15%** (Layout 0% / Typography 0% / Spacing 0% / Shadow 0% / Color 20% same dark palette family / Interactivity 30% same primary submit pattern)
- Weighted: 0×0.3 + 0×0.2 + 0×0.2 + 0×0.1 + 20×0.1 + 30×0.1 = 2 + 3 = **5%** structural / ~15% generous

**Estimated rebuild cost**: **6-8 hr**
- Remove AuthShell wrapper around `/auth/*` routes (or refactor AuthShell to match mockup full-screen no-shell pattern)
- Rewrite login page with mockup card layout (12px radius card 400×432 centered)
- Add 3 SSO outline buttons (SAML / Microsoft / Google) — defer wiring to AD-WorkOS-Extra-IdP-Phase2 (backend integration deferred); UI placeholder with disabled state + tooltip "Enterprise SSO via WorkOS roadmap"
- Move dev-login section to separate `/auth/dev-login` route (mockup has `#auth-dev` as separate route)
- Switch typography to mockup micro-sizes (13px body / 13.5px buttons-inputs)
- Switch color palette to mockup oklch tokens OR document why production uses shadcn slate (decision point)
- Remove h1 heading (mockup intentional no-heading design)

**Action items** (Sprint 57.23+ execution):
1. **Decision**: oklch palette vs shadcn slate — adopt mockup oklch tokens project-wide (deferred AD-Brand-Primary-Color-Decision finally resolve) OR keep shadcn slate + document deviation
2. **AuthShell refactor**: full-screen no-container for `/auth/*` routes; remove `<main p-6>` wrap for auth pages specifically (or use `fullBleed` prop pattern like Sprint 57.21 D-DAY4-7 chat-v2)
3. **Login page rewrite**: 1:1 from mockup `page-extras.jsx:27-58` (`const AuthLogin = () => (...)`)
4. **Dev-login extraction**: move to `/auth/dev-login` page (mockup `#auth-dev` route)
5. **3 SSO providers**: render as disabled placeholders in Phase 57.23+ with NEW AD `AD-WorkOS-Multi-IdP-Phase58` carryover (backend wire SAML / Entra / Google)

**Carryover ADs** (NEW from Unit 1):
- 🔴 **AD-Auth-Page-Full-Rebuild-Round-2** (Phase 57.23+ TOP priority)
- 🆕 **AD-AuthShell-Mockup-Refactor** (full-screen no-container pattern for `/auth/*`)
- 🆕 **AD-WorkOS-Multi-IdP-Phase58** (3 SSO outline buttons backend wire)
- AD-Brand-Primary-Color-Decision (Sprint 57.18 carryover) ← decision point reached via Unit 1


### Unit 2: /auth/callback

**Screenshots**: `mockup/auth-callback.png` + `prod/auth-callback.png`

**Last ported**: NEVER. Created Sprint 57.7 commit `51162fd5` (pre-mockup OIDC callback handler).

**Mockup**: 400×249 centered card at (520, 356); oklch dark theme + 12px radius. Body text content shows multi-step status flow:
```
Completing sign-in…
callback=acme.workos.com
Verifying SAML assertion
Resolving tenant + RLS context
Loading feature flags + memory scopes
```
NO buttons, NO h1 — pure progress display UI (gives user confidence during multi-step backend processing).

**Production**: **Immediate redirect** to `/auth/login?redirect_to=/overview` when no `?code=` or `?error=` query params present. NO callback loading UI exists at all. Tested URL `/auth/callback` (no params) → redirected before any UI render.

**Diff matrix**:

| Field | Status | Detail |
|-------|--------|--------|
| Layout | ❌ FAIL | Production has NO callback UI — just redirect logic; mockup has dedicated centered status card |
| Typography | N/A | No prod UI to compare |
| Spacing | N/A | No prod UI |
| Shadow / Radius | N/A | No prod UI |
| Color | ⚠️ PARTIAL | Both use dark theme but no prod card to compare bg |
| Interactivity | ❌ FAIL | Mockup shows 4-line progress sequence; production silent-redirects (no UX feedback during multi-step) |

**Severity**: **STRUCTURAL** (entirely missing UI — production assumes IdP redirect is fast enough to skip loading state; mockup designs for the case where it isn't)

**Strict 1:1 score**: **5%** (component does not exist in prod; 5% bonus for shared dark theme baseline)

**Estimated rebuild cost**: **3-4 hr**
- Create new `/auth/callback` loading state UI matching mockup 4-line progress sequence
- Wire to `useAuthStatusPolling` (or similar) hook polling backend OIDC verify endpoint
- Show progress states: "Completing sign-in…" → "Verifying SAML assertion" → "Resolving tenant + RLS context" → "Loading feature flags + memory scopes"
- On error: redirect to `/auth/login?error=<reason>`
- On success: redirect to `?redirect_to=<path>` or `/overview`

**Action items** (Sprint 57.23+):
1. Rewrite `/auth/callback` to show mockup loading card BEFORE redirect (currently it redirects immediately)
2. Decision: backend OIDC verify is currently 1-step (WorkOS) — mockup designs for 4-step expectation; either backend evolves to multi-step (per-step status SSE) OR frontend mocks the 4-line sequence with timed transitions (~500ms each)

**Carryover ADs**:
- AD-Auth-Page-Full-Rebuild-Round-2 (already opened in Unit 1) — Unit 2 reinforces priority
- 🆕 **AD-Auth-Callback-Loading-UX-Phase58** (backend OIDC multi-step status emission decision)


### Unit 3: /auth/register

**Screenshots**: `mockup/auth-register.png` + `prod/auth-register.png`

**Last ported**: NEVER. Production route **does not exist** — `http://localhost:3007/auth/register` redirects to `/` (root → `/overview` after auth check).

**Mockup**: 420×351 centered card at (510, 286); oklch dark + 12px radius. **4-step self-serve wizard** (Identity / Organization / Plan / Confirm). Step 1 visible:
- Header: "Create your workspace" + sub "Self-serve onboarding · 5 mins · no credit card"
- Stepper bar: 1 Identity / 2 Organization / 3 Plan / 4 Confirm (current = 1)
- 2 inputs: Work email (`founder@yourco.com` placeholder) + Full name (`Alex Chen` placeholder); both 390×36 / 13.5px / oklch bg / 6px radius
- Footer note: "After tenant creation, you can configure SAML / OIDC SSO"
- Continue button: 97×30 / 12.5px / primary indigo / 6px radius
- "Already have a workspace? Sign in" link

**Production**: ❌ **Route does not exist**. No `/auth/register` page implementation. Production routes config likely has it as PROP stub (need to verify in `routes.config.ts`).

**Diff matrix**:
| Field | Status | Detail |
|-------|--------|--------|
| All | ❌ FAIL | Component does not exist in production |

**Severity**: **FUNCTIONAL** (entire self-serve onboarding flow missing; blocks B2B SaaS go-to-market)
**Strict 1:1 score**: **0%**
**Estimated rebuild cost**: **8-10 hr** (4-step wizard with stepper component + per-step state + form validation + backend `POST /api/v1/tenants/register` API + email verification + JWT minting after success)

**Action items** (Sprint 57.23+):
1. NEW route `/auth/register` in `routes.config.ts` (promote from PROP if exists)
2. Rewrite from mockup `page-auth-extras.jsx:31-189` (AuthRegister component)
3. NEW backend `POST /api/v1/tenants/register` endpoint (Cat 12 tenants)
4. Email verification flow (SendGrid or similar)
5. JWT minting on success → redirect to `/overview`

**Carryover ADs**:
- 🆕 **AD-Auth-Register-Full-Build-Phase58** (multi-step wizard + backend tenant registration)
- AD-Auth-Page-Full-Rebuild-Round-2 (reinforced)

---

### Unit 4: /auth/invite

**Screenshots**: `mockup/auth-invite.png` (prod route does not exist; no screenshot)

**Mockup**: 420×566 centered card at (510, 178); rich invite acceptance UI:
- "You're invited to acme-prod" header + "Finish setting up your account to start." sub
- Invite metadata grid: Tenant (acme-prod · ap-east-1) / Invited by (dan@acme.com) / Role (operator) / Expires (in 6 days)
- Full name input + Set password input (12+ chars · used only if SSO is unavailable)
- "Accept invitation" primary button
- MFA notice: "MFA is required by tenant policy — set it up next."
- Footer: "Need to forward this invite? Ask dan@acme.com to resend."

**Production**: ❌ **Route does not exist**

**Severity**: **FUNCTIONAL** (entire invitation flow missing; blocks multi-user tenant onboarding)
**Strict 1:1 score**: **0%**
**Estimated rebuild cost**: **6-8 hr** (invite UI + backend `GET /api/v1/invites/{token}` validate + `POST /api/v1/invites/{token}/accept` + password set + MFA enrollment trigger)

**Action items**:
1. NEW route `/auth/invite/:token`
2. Rewrite from mockup `page-auth-extras.jsx:191-247` (AuthInvite component)
3. NEW backend endpoints (Cat 12 invitations)

**Carryover ADs**:
- 🆕 **AD-Auth-Invite-Full-Build-Phase58**

---

### Unit 5: /auth/mfa

**Screenshots**: `mockup/auth-mfa.png` (prod route does not exist)

**Mockup**: 420×378 centered card at (510, 272); MFA verification flow:
- "Two-factor verification" header + "Enter the 6-digit code from your authenticator app." sub
- Tab selector: Authenticator / Security Key (current = Authenticator)
- 6-digit code input grid
- Countdown: "code refreshes in 23s"
- "Verify and continue" primary button
- "Use recovery code instead" link
- Footer: "Lost your device? Contact your admin"

**Production**: ❌ **Route does not exist**

**Severity**: **FUNCTIONAL** (entire MFA enrollment + verification missing; tenant policy "MFA required" cannot be enforced)
**Strict 1:1 score**: **0%**
**Estimated rebuild cost**: **8-10 hr** (TOTP enrollment + verify UI + WebAuthn security key support + recovery codes + backend Cat 12 mfa endpoints)

**Action items**:
1. NEW route `/auth/mfa`
2. Rewrite from mockup `page-auth-extras.jsx:249-372` (AuthMFA component)
3. NEW backend MFA endpoints (TOTP + WebAuthn)
4. Decision: use WorkOS MFA features or roll own?

**Carryover ADs**:
- 🆕 **AD-Auth-MFA-Full-Build-Phase58**

---

### Unit 6: /auth/expired

**Screenshots**: `mockup/auth-expired.png` (prod route does not exist)

**Mockup**: 420×393 centered card at (510, 283); session expired UX:
- "Your session expired" header + sub explaining 24h inactivity timeout
- Session metadata: Last activity (14h 02m ago) / Session ID (sess_8a2f1c3) / Reason (jwt_expired · 24h max)
- 2 buttons: "Sign in again" primary + "Resume session" secondary
- Footer: "Your in-flight chats and pending HITL approvals are preserved." (reassurance copy)

**Production**: ❌ **Route does not exist**. Production likely redirects to `/auth/login?error=expired` instead of dedicated expiry page.

**Severity**: **FUNCTIONAL** (UX-soft — silent redirect to login loses context; mockup preserves in-flight session info)
**Strict 1:1 score**: **0%**
**Estimated rebuild cost**: **4-6 hr** (dedicated expired page + backend `GET /api/v1/sessions/{id}` for metadata display + redirect logic from interceptor)

**Action items**:
1. NEW route `/auth/expired`
2. Rewrite from mockup `page-auth-extras.jsx:374-454` (AuthExpired component)
3. Update axios/fetchWithAuth 401 interceptor to redirect to `/auth/expired?session_id=X&reason=Y` instead of `/auth/login`

**Carryover ADs**:
- 🆕 **AD-Auth-Expired-Full-Build-Phase58**

---

## Group: Operations Dashboards (5 units)

### Unit 7: /overview

**Screenshots**: `mockup/overview.png` + `prod/overview.png`

**Last ported**: Sprint 57.19 commit `f8949504` (1:1 layout port — REAL port) + Sprint 57.20 commit `d6cc70bd` (token migration only — 8 find/replace).

**Mockup shape**:
- Sidebar `232×900` at (0, 0) — brand block + 6 categorized nav + bottom user card; mockup includes more PROP/DRAFT badges than production
- Topbar `1208×48` at (232, 0) — breadcrumb "Overview /overview acme-prod · operator" + search "Search runs, sessions, audit_id…" + ⌘K + EN locale + "3" notif badge + "JL" avatar
- Main column 1208 wide. Sub-header "Cross-cut view across all 12 categories"
- **4-col KPI grid**: 267.75×4 = 1071 wide (Active loops + HITL pending + Cost MTD + SLA p95)
- **2-col widget grid 1**: 637.578 + 455.406 (Active loops widget + HITL queue)
- **2-col bottom grid**: 546.5×2 + 546.5×2 (Cost burn / Providers, Recent incidents / Errors 24h)
- 31 `.card` elements total; bg `oklch(0.165 0.006 260)`; border-radius 12px (consistent mockup pattern)
- Card structure: `.card` → `.card-head` (60h) → `.card-title` (18h) + `.card-sub` (17h) → `.card-body flush/dense`
- Body font 13px / Geist

**Production shape**:
- Sidebar `240×900` at (0, 0) (+8px vs mockup 232) — same 6 categories but FEWER PROP/DRAFT badges (production has 3 PROP under OPERATIONS vs mockup 7 PROP)
- Topbar `1200×48` at (240, 0) — preserved from Sprint 57.20 Topbar component
- Main column 1200 wide × 852h
- h1 **"Overview"** present (mockup has NONE in main body)
- Sub-header: "Unified operator dashboard across the 12 categories." (close paraphrase of mockup "Cross-cut view across all 12 categories")
- **4-col KPI grid**: 266.25×4 = 1065 (±6px vs mockup 1071) ✓ — Active sessions 14 / HITL pending 3 / Cost MTD $2,847 / SLA p95 1.84s
- **2-col widget grid 1**: 634.078 + 452.906 (±3-4px vs mockup 637.578+455.406) ✓
- **2-col bottom grid**: 543.5×2 (±3px) ✓
- HITL queue widget present (3 pending) — HIGH/MEDIUM/CRITICAL items matching mockup labels
- Cost burn widget present ($2583 MTD vs $2520 on-pace / over pace)
- Providers widget (4 providers · 24h) — claude-haiku-4-5 / gpt-4.1 / gpt-4.1-mini / embedding-3-large
- Recent incidents (3 open) — INC-2451 / 2447 / 2440 / 2438
- Errors · 24h widget
- Card count via `.card` className = **0** (shadcn `Card` component uses different class semantics; renders the same visual concept but DOM markup differs)
- Body font 16px / Geist (vs mockup 13px = **23% larger**)

**Diff matrix**:

| Field | Status | Detail |
|-------|--------|--------|
| Layout | ✅ PASS (95%) | Sidebar +8px / Topbar matches / 4-col KPI ±6px / 2-col widgets ±3-4px / Sections + order match mockup exactly |
| Typography | ❌ FAIL | Body 13px (mockup) vs 16px (prod) = 23% larger. KPI numbers / labels / card titles all using Tailwind default text-sm/base/lg instead of mockup 11.5px/12.5px/13px micro-sizes |
| Spacing | ⚠️ PARTIAL | Grid gaps mostly match (gap-4 ≈ 16px); card padding differs (mockup uses .card-head 60h fixed + .card-body flush/dense; production uses Tailwind p-4/p-6) |
| Shadow / Radius | ❌ FAIL | Mockup uses 12px radius `.card` chrome consistently; production uses shadcn `Card` default radius (probably 8px) + variable shadow |
| Color | ⚠️ PARTIAL | Background palette migrated Sprint 57.20 token tree (close to mockup) but specific oklch L/C values don't match (mockup `oklch(0.165 0.006 260)` card-bg vs production `--bg-1` Sprint 57.20 approximation) |
| Interactivity | ✅ PASS | All sections present + clickable (Review / Details / All incidents / Export / New chat buttons all present) |

**Severity**: **COSMETIC** (layout structurally correct; visual chrome / typography / radius / shadow micro-detail differs from mockup) — confirms user observation "明顯差異, 不像把mockup複製再修改"

**Strict 1:1 score**: **60%** (Layout 95% ×0.3 + Typography 30% ×0.2 + Spacing 70% ×0.2 + Shadow/Radius 30% ×0.1 + Color 70% ×0.1 + Interactivity 95% ×0.1 = 28.5 + 6 + 14 + 3 + 7 + 9.5 = **~68%**) — round to 60% to reflect user's perceptual "明顯差異" rating

**Estimated rebuild cost**: **3-4 hr**
- Switch all card chrome to mockup `.card` class equivalent: 12px radius + oklch bg + .card-head (60h fixed) + .card-body (flush/dense variants)
- Apply mockup micro-typography: 13px body / 11.5px-12.5px labels / 18px card-title / 17px card-sub
- Adjust card padding to mockup pattern (head padding + body flush vs dense variants)
- Sidebar 232 vs 240 — minor; either is acceptable
- Remove h1 "Overview" from main body (mockup uses Topbar breadcrumb for page title)
- Remove or adjust sub-header to mockup wording

**Action items** (Sprint 57.23+):
1. **Decision needed**: shadcn `Card` chrome migration to mockup `.card` pattern — implement custom `MockupCard` primitive with mockup-aligned variants OR override shadcn `Card` CSS to match mockup chrome
2. Audit micro-typography sizes — Sprint 57.18 token tree has font-size tokens? If not, add mockup-aligned font-size scale to `tailwind.config.ts`
3. Re-port main body content from mockup `page-overview.jsx` with Strict 1:1 typography + spacing + card chrome
4. Remove `<h1>Overview</h1>` from page; rely on Topbar breadcrumb (already shows "Overview /overview")

**Carryover ADs**:
- 🆕 **AD-Mockup-Card-Primitive-Phase58** (custom MockupCard with .card-head/.card-body/.card-sub variants OR shadcn `Card` CSS override pattern)
- 🆕 **AD-Mockup-Typography-Scale-Phase58** (extend `tailwind.config.ts` with mockup micro-size scale 11px/11.5px/12px/12.5px/13px/13.5px)
- AD-Mockup-Existing-Pages-Retrofit Tier 1 (Sprint 57.19 carryover; /overview specifically — REAFFIRMED)


### Unit 8: /cost-dashboard

**Screenshots**: `mockup/cost-dashboard.png` + `prod/cost-dashboard.png`

**Last ported**: Sprint 57.1 v2 commit (pre-mockup). Last touched: pre-Sprint-57.18 mockup-integration. Not in Sprint 57.20 token migration batch.

**Mockup**: "Cost Ledger" title + sub "Range 12 · Token + tool spend · admin-only provider breakdown" + path pill "/cost-dashboard" + "admin scope" + "By tenant" + "CSV" actions + 4 cards visible (KPI summaries; admin-only provider breakdown widget).

**Production**: h1 "Cost Dashboard" + sub "Cost ledger summary for your tenant." + Month picker + Card with **Failed to load data / HTTP 500 / Retry** error state — backend cost-ledger endpoint missing/failing for dev tenant.

**Diff matrix**:
| Field | Status | Detail |
|-------|--------|--------|
| Layout | ❌ FAIL | Production single-card error state vs mockup 4-card admin-scoped breakdown grid |
| Typography | ❌ FAIL | Sprint 57.1 pre-mockup; 16px body / shadcn defaults vs mockup 13px |
| Spacing | ❌ FAIL | Pre-mockup spacing |
| Shadow / Radius | ❌ FAIL | shadcn Card vs mockup `.card` 12px |
| Color | ⚠️ PARTIAL | Both dark theme |
| Interactivity | ❌ FAIL | Production shows error retry only; mockup shows 4 KPI + drill-down + CSV export |

**Severity**: **FUNCTIONAL** (backend missing + UI architecture pre-mockup)
**Strict 1:1 score**: **15%** (only sidebar+topbar shared chrome)
**Estimated rebuild cost**: **4-5 hr** (backend cost-ledger endpoint + frontend 4-card grid + admin-scope dropdown + CSV export)

**Action items**:
1. Fix backend cost-ledger endpoint 500 (Sprint 56.3 Cost Ledger work; tenant-scope missing for dev tenant)
2. Rewrite frontend from mockup `page-admin.jsx:201-322` (CostPage)
3. Add admin-scope dropdown (By tenant) + CSV export

**Carryover ADs**:
- 🆕 **AD-Cost-Dashboard-Full-Rebuild-Phase58**
- 🆕 **AD-Cost-Ledger-Backend-Dev-Tenant-500** (debug + fix HTTP 500)

---

### Unit 9: /sla-dashboard

**Screenshots**: `mockup/sla-dashboard.png` + `prod/sla-dashboard.png`

**Last ported**: Sprint 57.1 v2 (pre-mockup).

**Mockup**: SlaPage from `page-admin.jsx:32-156` — likely shows SLA p95 latency chart + thresholds + providers + month-over-month trend.

**Production**: h1 "SLA Dashboard" + sub "SLA report for your tenant. Threshold fallback to Standard 99.5% availability — Enterprise tier display deferred (Day 0 D10)." + Month picker + **Failed to load data / HTTP 500 / Retry** error state.

**Diff matrix**: same FUNCTIONAL severity pattern as Unit 8 (backend missing + pre-mockup architecture).

**Severity**: **FUNCTIONAL**
**Strict 1:1 score**: **15%**
**Estimated rebuild cost**: **4-5 hr** (backend SLA endpoint + frontend chart rewrite from mockup)

**Action items**:
1. Fix backend SLA endpoint 500 (Sprint 56.3 SLAMetricRecorder; dev tenant missing data)
2. Rewrite from mockup `page-admin.jsx:32-156` (SlaPage)

**Carryover ADs**:
- 🆕 **AD-SLA-Dashboard-Full-Rebuild-Phase58**
- 🆕 **AD-SLA-Backend-Dev-Tenant-500**

---

### Unit 10: /memory

**Screenshots**: `mockup/memory.png` + `prod/memory.png`

**Last ported**: Sprint 57.12 (pre-mockup MemoryViewer).

**Mockup**: MemoryPage from `page-governance.jsx:462-598` — 5 scope layers (system/tenant/role/user/session) × 3 time scales (permanent/quarter/day) + memory ops timeline + time travel scrubber + memory entries grid.

**Production**: h1 "Memory" + 2 tabs (Recent / By Scope) + Layer selector (system / tenant / user / **role (Phase 58+)** / **session (Phase 58+)**) + "No memory entries in this layer." empty state — partial Sprint 57.12 implementation; backend has only 3 scopes wired (role/session deferred to Phase 58+).

**Diff matrix**:
| Field | Status | Detail |
|-------|--------|--------|
| Layout | ❌ FAIL | Production simple 2-tab UI vs mockup 5-scope × 3-time-scale matrix grid + time travel scrubber + memory ops timeline |
| Typography | ❌ FAIL | Pre-mockup typography |
| Spacing | ❌ FAIL | Pre-mockup |
| Shadow / Radius | ❌ FAIL | shadcn defaults |
| Color | ⚠️ PARTIAL | Both dark |
| Interactivity | ⚠️ PARTIAL | Production has tabs + scope picker (partial); mockup has full time-travel scrubber + ops timeline + edit/delete per memory |

**Severity**: **STRUCTURAL** (key features missing: time scales / time travel / ops timeline / per-memory CRUD)
**Strict 1:1 score**: **25%**
**Estimated rebuild cost**: **8-10 hr** (5-scope × 3-time-scale matrix + time travel UI + ops timeline + backend role/session scope wire)

**Action items**:
1. Backend: wire `role` + `session` scopes (Cat 3 carryover)
2. Backend: add time travel API (Cat 3 + Cat 7 cross-cutting)
3. Backend: add memory ops audit log (Cat 3 + Cat 12)
4. Frontend rewrite from mockup `page-governance.jsx:462-598`

**Carryover ADs**:
- 🆕 **AD-Memory-Page-Full-Rebuild-Phase58** (multi-sprint)
- 🆕 **AD-Memory-Scope-Role-Session-Phase58** (backend wire)
- 🆕 **AD-Memory-Time-Travel-Phase58** (backend + UI)

---

### Unit 11: /verification

**Screenshots**: `mockup/verification.png` + `prod/verification.png` (redirects to `/verification/recent`)

**Last ported**: Sprint 57.11 (pre-mockup VerificationPanel + recent list).

**Mockup**: VerificationPage from `page-extras.jsx:829-927` — VERIFY_CLAIMS list with rules-based + LLM judge breakdown.

**Production**: Redirected `/verification` → `/verification/recent`; h1 "Verification" + recent verifications list (Sprint 57.11 Real Ship).

**Diff matrix**: 結構接近 mockup verification 概念，但 visual chrome 預期 ≠ mockup (Sprint 57.11 pre-mockup; 未 Sprint 57.20 token migrate)。

**Severity**: **COSMETIC** (structurally close; visual chrome + typography differs from mockup)
**Strict 1:1 score**: **40%**
**Estimated rebuild cost**: **3-4 hr** (token migrate + typography align + card chrome rewrite)

**Action items**:
1. Token migrate (similar to Sprint 57.20 /overview pattern but full visual rewrite this time)
2. Apply mockup micro-typography
3. Migrate to mockup `.card` chrome pattern

**Carryover ADs**:
- AD-Mockup-Existing-Pages-Retrofit Tier 1 (carryover — REAFFIRMED for /verification)

---

## Group: Chat-v2 (1 page + 6 widget gaps)

### Unit 12: /chat-v2 (page-level)

**Screenshots**: `mockup/chat-v2.png` + `prod/chat-v2.png`

**Last ported**: Sprint 57.21 PR #152 commit `678222d2` — **AD-ChatV2-Full-Mockup-Fidelity Phase-1** (Turn Block Model + 3-col shell + Inspector 4-tab + Composer scaffolding).

**Mockup**: ChatV2 from `page-chat.jsx:73-92` — 3-col shell:
- Left: SessionList (6 sessions w/ DomainDot + status + agent + turns + time)
- Center: TurnList (UserTurn / AgentTurn with 4 block types thinking/tool/memory/verification/subagent_fork / HITLTurn with rich card)
- Right: ChatInspector 4-tab (Turn / Trace / Memory / Tree)
- Bottom: Composer (textarea + 3 coming-soon buttons + Send)

**Production**: Sprint 57.21 Phase-1 ship:
- ✅ 3-col shell (240/minmax(480,1fr)/320) at `chat-shell` testid
- ✅ Left SessionList with 6 fixtures + DomainDot + status indicator
- ✅ Center TurnList dispatcher (User/Agent/HITL) with 4 Block types (thinking/tool/verification/subagent_fork)
- ✅ Right ChatInspector with 4 tabs (Turn populated; Trace/Memory/Tree = ComingSoon placeholders)
- ✅ Bottom InputBar (Composer Option C visual-only NOT wired; InputBar untouched preserves 5-state pill + send/cancel + 14 SSE)

**Diff matrix**:

| Field | Status | Detail |
|-------|--------|--------|
| Layout | ✅ PASS (95%) | 3-col shell preserved Sprint 57.21 D-DAY4-7 fullBleed grid mockup-exact widths |
| Typography | ⚠️ PARTIAL | Most Sprint 57.21 uses mockup tokens but micro-sizes (11.5px/12.5px) may not be uniform |
| Spacing | ✅ PASS (85%) | Sprint 57.21 mockup-extracted padding |
| Shadow / Radius | ✅ PASS (90%) | Sprint 57.21 mockup-extracted card chrome |
| Color | ✅ PASS (95%) | Sprint 57.21 mockup tokens consumed correctly |
| Interactivity | ⚠️ PARTIAL | Phase-1 Turn/Block/HITL wired; Memory Block missing / HITL 4-action only 2 / Composer NOT wired / Inspector 3 tabs ComingSoon / SessionList backend missing |

**Severity**: **COSMETIC for shipped Phase-1; FUNCTIONAL for Phase-2 widget gaps** (covered in Units 13-18 below)
**Strict 1:1 score**: **75%** for page-level structure (Phase-1 baseline OK); Phase-2 widget gaps separately scored Units 13-18

**Estimated rebuild cost (page-level only)**: **2-3 hr** typography polish — Phase-1 structural baseline already complete

**Action items**:
1. Page-level structure DONE Sprint 57.21 (no action needed for shell + Turn dispatch + Inspector frame)
2. Phase-2 widgets covered in Units 13-18 (Memory Block / HITL 4-action / Composer wire / 3 Inspector tabs)
3. Typography polish: verify Phase-1 components use mockup 11.5/12.5/13px micro-sizes consistently

**Carryover ADs** (Phase-2; reaffirmed from Sprint 57.21):
- 🔴 **AD-ChatV2-Full-Mockup-Fidelity Phase-2** epic
- AD-ChatV2-Memory-Block-Phase2
- AD-ChatV2-HITL-FourAction-Phase2
- AD-ChatV2-Composer-Richness+Wire-Phase2
- AD-ChatV2-Inspector-Trace+Memory+Tree-Phase2
- AD-ChatV2-SessionList-Backend

### Unit 13: Phase-2 widget — Memory Block (5th Block type)

**Audit method**: Code-level (no new screenshots — Unit 12 page-level screenshots cover chat-v2 shell; widget granularity needs source-code diff).

**Mockup source**: `reference/design-mockups/page-chat.jsx` L224-233 — `Block` dispatcher case `b.type === "memory"`:
```jsx
<div className="block memory-op">
  <Icon name="memory" size={12} style={{ color: "var(--memory)" }} />
  <span className="label">{b.op}</span>                              {/* READ or WRITE */}
  <span className="mono" style={{ fontSize: 11, color: "var(--fg-muted)" }}>scope: {b.scope}</span>
  <span className="mono subtle" style={{ marginLeft: "auto" }}>{b.entry}</span>
</div>
```
Mockup hero conversation uses memory blocks at:
- TURNS[3] L43: `{ type: "memory", op: "READ", scope: "user.jamie", entry: "preferences.rca_format = '5-whys + timeline'" }`
- TURNS[4] L52: `{ type: "memory", op: "WRITE", scope: "session.sess_4tk2p", entry: "root_cause = pgbouncer pool too small on canary" }`

**Production**: `frontend/src/features/chat_v2/components/blocks/` contains 5 files (Block.tsx dispatcher + ThinkingBlock.tsx + ToolBlock.tsx + VerificationBlock.tsx + SubagentForkBlock.tsx). **NO `MemoryBlock.tsx`**. `types.ts` L194-198 + L239 explicitly excludes Memory from Block discriminated union:
```typescript
// 4 of 5 mockup block types ship Phase-1. Memory block (mockup L224-232)
// DEFERRED to Phase-2+ — requires NEW Cat 3 SSE event (AD-ChatV2-Memory-Block-Phase2).
export type Block = ThinkingBlock | ToolBlock | VerificationBlock | SubagentForkBlock;
```

**Diff matrix**:

| Field | Status | Detail |
|-------|--------|--------|
| Layout | ❌ FAIL | Component does not exist; Block dispatcher has no `memory` case branch |
| Typography | N/A | No prod component to compare (mockup uses 11px mono for scope, 12px label) |
| Spacing | N/A | No prod (mockup 1-line horizontal flex layout) |
| Shadow / Radius | N/A | No prod (mockup uses subtle `.block.memory-op` styling) |
| Color | N/A | No prod (mockup uses `var(--memory)` token cyan/teal family) |
| Interactivity | ❌ FAIL | No backend SSE event emits memory ops; chatStore.mergeEvent has no handler |

**Severity**: **STRUCTURAL** (5th Block type definitionally absent from union; backend SSE event missing; mockup hero conversation cannot be rendered fully without this)
**Strict 1:1 score**: **0%** (component completely missing)

**Estimated rebuild cost**: **4-6 hr**
- Backend Cat 3: NEW SSE event `memory_op_emitted` with `{ op: "READ"|"WRITE"|"DELETE", scope: string, entry: string }` payload (1 hr)
- backend wiring: emit event from `_memory_layer.read()` + `.write()` instrumented points (1 hr)
- Frontend `types.ts`: add `MemoryBlock` variant + extend `Block` discriminated union (15 min)
- Frontend NEW `MemoryBlock.tsx` matching mockup `.block.memory-op` style (1 hr)
- Frontend `Block.tsx` dispatcher: add `b.type === "memory"` case (15 min)
- Frontend `chatStore.mergeEvent`: handle `memory_op_emitted` → append MemoryBlock to active agent turn (45 min)
- Tests: types exhaustive check + render test + mergeEvent unit test (1-2 hr)

**Action items** (Sprint 57.23+ execution; **shares backend with Unit 17 Inspector Memory tab** — same SSE event powers both):
1. Backend Cat 3 SSE event design (memory_op_emitted) — coordinate with Cat 3 `/api/v1/memory` REST baseline (Sprint 57.12)
2. Decision: emit per-op (high frequency, more granular) vs batched-per-turn (lower frequency, sum). Mockup shows per-op so per-op preferred
3. Frontend: `MemoryBlock.tsx` + Block dispatcher case + types union extension
4. **Coordinate with Unit 17** — same backend SSE event feeds both Memory Block (in-flow stream) and Inspector Memory tab (cumulative table)

**Carryover ADs**:
- 🔴 **AD-ChatV2-Memory-Block-Phase2** (reaffirmed from Sprint 57.21; Phase-2 epic)
- 🆕 **AD-Cat3-Memory-Op-SSE-Event-Phase58** (backend Cat 3 streaming wire; shared with Unit 17)

### Unit 14: Phase-2 widget — HITL FourAction

**Audit method**: Code-level diff of mockup vs Sprint 57.21 Phase-1 HITLTurn ship.

**Last ported**: Sprint 57.21 Day 2 §2.1 (HITLTurn.tsx initial extract; mockup L270-313 1:1 visual port BUT Phase-1 ships 2-action subset of mockup 4-action UX).

**Mockup source**: `reference/design-mockups/page-chat.jsx` L270-313 — HITLTurn renders rich card with **4 action buttons** + meta row + audit_id at L300-309:
```jsx
<div className="hitl-actions">
  <Button variant="success" size="sm" icon="check">Approve & continue</Button>
  <Button variant="outline" size="sm">Approve with edits</Button>
  <Button variant="danger" size="sm" icon="x">Reject</Button>
  <Button variant="ghost" size="sm">Escalate to L2</Button>
  <span className="row subtle" style={{ marginLeft: "auto", fontSize: 11 }}>
    <Icon name="audit" size={12} />
    <span className="mono">audit_id: a8f3.k2p1</span>            {/* REAL id from backend */}
  </span>
</div>
```
Mockup meta row L294 also shows: `<Badge>tenant.acme-prod</Badge>` for **scope** field.

**Production**: `HITLTurn.tsx` L177-204 renders only **2 buttons**:
```tsx
<button data-testid="approve-btn" ...>Approve & continue</button>
<button data-testid="reject-btn"  ...>Reject</button>
{/* "Approve with edits" + "Escalate to L2" 4-action UX deferred to
    Phase-2 AD-ChatV2-HITL-FourAction-Phase2 — backend needs APPROVED_WITH_EDITS
    variant + payload editor + escalate routing. Phase-1 ships canonical
    2-action subset (matches Sprint 53.5 baseline + e2e contract). */}
```
Production missing:
- "Approve with edits" button (outline variant) + payload inline editor flow
- "Escalate to L2" button (ghost variant) + L1→L2 routing handler
- scope badge `tenant.acme-prod` (HITLTurn.tsx meta row only has severity / tool / policy; NO scope row)
- Real `audit_id`: production L214 shows `audit_id: —` placeholder (mockup shows `a8f3.k2p1`)

**Diff matrix**:

| Field | Status | Detail |
|-------|--------|--------|
| Layout | ✅ PASS (95%) | Card chrome + bar + meta row + payload block + actions row all present and mockup-aligned. Action row narrower (4 → 2 buttons). |
| Typography | ✅ PASS (90%) | Sprint 57.21 mockup-extracted micro-sizes (11.5px / 12.5px / 13px) preserved |
| Spacing | ✅ PASS (85%) | Mockup padding extracted (px-3.5, gap-2, mb-2.5) |
| Shadow / Radius | ✅ PASS (95%) | Card 1.5px severity-tinted border + 3px left bar + 6-7px radius match mockup |
| Color | ✅ PASS (95%) | Sprint 57.21 risk severity token wire (bg-risk-high/8 + text-risk-high + bg-risk-high bar) — mockup-aligned |
| Interactivity | ❌ FAIL | **2 of 4 actions wired** (50%); Approve-with-edits + Escalate-to-L2 NOT rendered. Scope badge missing. audit_id placeholder. |

**Severity**: **FUNCTIONAL** (visual fidelity high BUT operational workflow incomplete; HITL 4-action UX is core enterprise governance gate; missing 2 critical operator actions blocks Sprint 57.23+ production usage)

**Strict 1:1 score**: **70%** weighted (Layout 95×0.3 + Typography 90×0.2 + Spacing 85×0.2 + Shadow/Radius 95×0.1 + Color 95×0.1 + Interactivity 25×0.1 = 28.5 + 18 + 17 + 9.5 + 9.5 + 2.5 = **85%**) — lowered to 70% to reflect functional severity weighting

**Estimated rebuild cost**: **3-4 hr**
- Backend Cat 9: NEW decision variant `APPROVED_WITH_EDITS` (governanceService.decide payload includes edited_payload) (1 hr)
- Backend Cat 9: NEW escalation routing (`/api/v1/approvals/{id}/escalate` → L2 queue) (1 hr)
- Backend: Cat 12 emit real `audit_id` from WORM audit log + include in `ApprovalRequestedEvent` payload (30 min)
- Frontend HITLTurn.tsx: render 2 new buttons + payload inline editor modal (Approve-with-edits) + scope badge from approval metadata + real audit_id from turn.auditId field (1.5 hr)
- Update `types.ts` HITLTurn: add `scope: string` + `auditId: string | null` fields (15 min)
- Update e2e contract: approval-card.spec.ts add 4-action selectors + scope/audit_id assertions (45 min)

**Action items** (Sprint 57.23+):
1. Backend: add `APPROVED_WITH_EDITS` decision variant + payload editor flow
2. Backend: add escalation route to L2 queue (HITL Cat 9 + Cat 12 audit emit)
3. Backend: emit real audit_id in `approval_requested` SSE payload (currently `audit_id: —` placeholder)
4. Frontend: render 4-action button row + scope badge + real audit_id
5. Add payload editor modal for "Approve with edits" (Monaco or simple textarea diff view)

**Carryover ADs**:
- 🔴 **AD-ChatV2-HITL-FourAction-Phase2** (reaffirmed; opened Sprint 57.21)
- 🆕 **AD-Governance-Approved-With-Edits-Variant-Phase58** (backend decision enum + payload diff handling)
- 🆕 **AD-Governance-Escalation-L2-Routing-Phase58** (backend L2 queue + frontend escalate handler)
- 🆕 **AD-HITL-AuditId-SSE-Emit-Phase58** (backend Cat 12 WORM audit_id surface in approval_requested SSE)

### Unit 15: Phase-2 widget — Composer richness + Wire

**Audit method**: Code-level diff of mockup Composer + Sprint 57.21 visual-scaffolding Composer + still-in-use InputBar.

**Last ported**: Sprint 57.21 Day 4 §4.2 (Composer.tsx visual scaffolding; **NOT consumed by chat-v2 page** — production send path remains older InputBar.tsx).

**Mockup source**: `reference/design-mockups/page-chat.jsx` L315-368 — Composer with rich functionality:
```jsx
const Composer = () => {
  const [attachments, setAttachments] = useCs([]);
  const fileRef = useRcs(null);
  const onPick = (e) => { /* file picker handler */ };
  const onDrop = (e) => { /* drag-drop handler */ };
  return (
    <div className="composer" onDragOver={...} onDrop={onDrop}>
      <div className="composer-inner">
        {/* Attachment grid with per-file kind icon + size + remove btn */}
        <textarea className="composer-input" placeholder="Ask the agent — drag files in, paste images..."/>
        <div className="composer-tools">
          <input ref={fileRef} type="file" multiple accept="image/*,.pdf,.txt,.md,.json,.yaml,.log,.csv" />
          <Button variant="ghost" icon="plus" onClick={() => fileRef.current?.click()}>Attach</Button>
          <Button variant="ghost" icon="branch">Tools (24)</Button>
          <Button variant="ghost" icon="memory">Memory scope</Button>
          <Badge>claude-haiku-4-5</Badge>
          <span className="provider-neutral">neutral</span>
          <Button variant="primary" iconRight="send">Send</Button>          {/* WIRED */}
        </div>
      </div>
      <div>Drop files anywhere · accepts ... · max 25MB each</div>
    </div>
  );
};
```

**Production (Composer.tsx — visual scaffolding only)**: file header explicitly states "ships visual scaffolding only; not consumed by chat-v2/index.tsx this sprint". Has:
- Disabled textarea (`disabled` attribute)
- 3 disabled buttons (Attach + Tools (24) + Memory scope) with `title="Sprint 57.22+ AD-ChatV2-Composer-Richness-Phase2"`
- Disabled Send button with `title="...production send path remains InputBar.tsx"`
- NO attachment state, NO file ref, NO drag-drop handler, NO onPick
- File header: "explicit Sprint 57.21 scope-reduction per Day 4 §4.2 plan 'lower-risk option' footer — ship the visual demonstration without regressing the production send path."

**Production (InputBar.tsx — actually used)**: Sprint 50.2 baseline preserved through Sprint 57.21:
- 5-state pill (idle / running / awaiting_approval / cancelling / error)
- send + cancel handlers
- 14 SSE event integration via useLoopEventStream hook
- **NO attachment / NO tools picker / NO memory scope** affordances
- Visual chrome pre-mockup (Sprint 50.2 design — does not match mockup `.composer` chrome)

**Diff matrix**:

| Field | Status | Detail |
|-------|--------|--------|
| Layout | ❌ FAIL | Production chat-v2 uses InputBar (pre-mockup chrome). Composer.tsx exists with mockup chrome but is NOT in render tree. |
| Typography | ⚠️ PARTIAL | Composer.tsx 13px text-fg / 10.5px footer ≈ mockup; InputBar 14-16px (pre-mockup) |
| Spacing | ⚠️ PARTIAL | Composer.tsx mockup-aligned; InputBar pre-mockup |
| Shadow / Radius | ⚠️ PARTIAL | Composer.tsx mockup chrome; InputBar pre-mockup chrome |
| Color | ✅ PASS | Both consume same token tree (Sprint 57.20 migration) |
| Interactivity | ❌ FAIL | Composer.tsx ALL disabled (0% wired); InputBar functional but lacks Attach/Tools/MemoryScope affordances |

**Severity**: **FUNCTIONAL** (rich attachment + tools picker + memory scope completely missing; Composer.tsx scaffold exists but cannot be used; actual send path is older InputBar.tsx with no Phase-2 affordances)

**Strict 1:1 score**: **30%** (Composer.tsx visual scaffolding 70% mockup-aligned × 0 interactivity weight + InputBar functional but 20% mockup-aligned ≈ 30% blended)

**Estimated rebuild cost**: **6-8 hr**
- Backend NEW endpoint `GET /api/v1/tools/registry` returning 24-tool list with categories (Cat 2) (1 hr)
- Backend NEW endpoint `GET /api/v1/memory/scopes` returning available memory scopes for current session (Cat 3) (1 hr)
- Backend NEW endpoint `POST /api/v1/attachments` multipart upload returning attachment_id (1 hr)
- Frontend Composer.tsx richness: add attachment state management + file kind detection + drag-drop wire + per-file remove (2 hr)
- Frontend Composer.tsx wire: extract send-handler from InputBar to shared hook OR proxy via composition (per file header decision pending) (1.5 hr)
- Frontend Tools (24) picker: command palette modal with category filter (1 hr)
- Frontend Memory scope picker: dropdown showing 5 scopes (system / tenant / role / user / session) with current selection (45 min)
- Migration: replace InputBar.tsx with Composer.tsx in chat-v2/index.tsx; deprecate InputBar (45 min)
- Tests: Composer interactive tests + e2e file upload + tools picker + memory scope (1-2 hr)

**Action items** (Sprint 57.23+):
1. Backend tool registry endpoint (Cat 2)
2. Backend memory scopes endpoint (Cat 3)
3. Backend multipart attachment endpoint (Cat 12 storage + Cat 9 redaction wire)
4. Frontend Composer.tsx richness (attach + tools + memory scope)
5. Frontend Composer.tsx wire (extract send-handler from InputBar)
6. Replace InputBar with Composer in chat-v2 render tree
7. Deprecate InputBar.tsx (delete or rename to `_legacy/InputBar.tsx`)

**Carryover ADs**:
- 🔴 **AD-ChatV2-Composer-Richness-Phase2** (reaffirmed; opened Sprint 57.21)
- 🔴 **AD-ChatV2-Composer-Wire-Phase2** (reaffirmed; per Composer.tsx file header L20-24 decision pending)
- 🆕 **AD-Tool-Registry-Endpoint-Phase58** (Cat 2 backend)
- 🆕 **AD-Memory-Scopes-Endpoint-Phase58** (Cat 3 backend; relates to Unit 10 /memory page rebuild)
- 🆕 **AD-Attachments-Upload-Endpoint-Phase58** (Cat 12 storage + redaction wire)

### Unit 16: Phase-2 widget — Inspector Trace tab

**Audit method**: Code-level diff of mockup InspectorTrace + Sprint 57.21 ComingSoonInspectorTab placeholder.

**Last ported**: Sprint 57.21 Day 4 §4.1 (ComingSoonInspectorTab placeholder; visual hint only).

**Mockup source**: `reference/design-mockups/page-chat.jsx` L434-466 — InspectorTrace Cat 12 OTel spans waterfall:
```jsx
const InspectorTrace = () => (
  <div style={{ padding: "12px 16px" }}>
    <div style={{ fontSize: 11.5, color: "var(--fg-subtle)", textTransform: "uppercase" }}>
      Cat 12 · OTel spans · 17 turns
    </div>
    {/* 14 timeline rows: loop.iteration_0/1/2/3 + tool spans + subagent fan-out
        + memory/verification spans + hitl.requested */}
    {[
      { name: "loop.iteration_0", d: 1.42, c: "var(--primary)", off: 0 },
      { name: "├─ tool.incidents.list", d: 0.08, c: "var(--tool)", off: 1 },
      // ... 14 rows total
    ].map((s, i) => {
      const max = 2.5;
      const w = Math.max(2, (s.d / max) * 100);
      return (
        <div className="row" style={{ gap: 8, padding: "2px 0", fontSize: 10.5, fontFamily: "var(--font-mono)" }}>
          <span style={{ width: 200, color: "var(--fg-muted)", paddingLeft: s.off * 10 }}>{s.name}</span>
          <span style={{ flex: 1, height: 8, background: "var(--bg-2)", borderRadius: 2 }}>
            <span style={{ display: "block", width: w + "%", height: "100%", background: s.c, borderRadius: 2 }} />
          </span>
          <span style={{ width: 50, textAlign: "right" }}>{s.d.toFixed(2)}s</span>
        </div>
      );
    })}
  </div>
);
```

**Production**: ChatInspector dispatcher renders ComingSoonInspectorTab when `tab === "trace"`:
```tsx
<ComingSoonInspectorTab
  name="Trace"
  mockupSection="L434-466"
  carryoverAd="AD-ChatV2-Inspector-Trace-Phase2"
  hint="Cat 12 OTel spans waterfall — backend SSE event stream..."
/>
```
Placeholder shows: name header + hint paragraph + mockup link + carryover AD link. ~6 lines visible content.

**Diff matrix**:

| Field | Status | Detail |
|-------|--------|--------|
| Layout | ❌ FAIL | Mockup 14-row gantt waterfall vs production 4-line placeholder card |
| Typography | N/A | Placeholder uses generic 11-12px; mockup uses 10.5px mono for span names + 11.5px header |
| Spacing | N/A | Placeholder px-4 py-3; mockup specific 200px name column + flex bar + 50px duration column |
| Shadow / Radius | N/A | Placeholder has bg-bg-2 border; mockup bars use 2px radius |
| Color | N/A | Mockup uses 5 distinct token colors per span type (primary/tool/thinking/info/memory/success/warning) |
| Interactivity | ❌ FAIL | Mockup is read-only display BUT live-updating from SSE; placeholder is purely static |

**Severity**: **STRUCTURAL** (entire visualization feature missing; component does not exist)
**Strict 1:1 score**: **5%** (placeholder names the section + links to carryover AD; mockup gantt 100% absent)

**Estimated rebuild cost**: **5-7 hr**
- Backend Cat 12: NEW SSE event `span_emitted` per-OTel-span streaming with `{ name, duration_ms, span_type, parent_span_id, offset }` payload (1.5 hr)
- OR alternative: REST `GET /api/v1/sessions/{id}/spans` returning full span list (simpler but loses live-update) (1 hr)
- Frontend NEW `InspectorTrace.tsx` rendering gantt: per-iteration grouping (loop.iteration_N as parent) + indent based on tree depth + bar normalized to max duration (2 hr)
- Frontend chatStore add `spans: SpanEntry[]` per turn aggregation (45 min)
- Frontend Inspector dispatcher: replace ComingSoonInspectorTab with InspectorTrace when tab === "trace" (15 min)
- Tests: span aggregation unit test + gantt render test + live SSE update test (1-2 hr)

**Action items** (Sprint 57.23+):
1. Backend Cat 12: decision on per-span SSE event vs REST batch (mockup live-update suggests SSE preferred)
2. Backend: instrument loop iteration + tool execution + memory ops + verification + subagent spawn with OTel spans (Cat 12 cross-cutting)
3. Frontend: new InspectorTrace.tsx component matching mockup gantt
4. chatStore aggregation: spans per turn + auto-clear on session change

**Carryover ADs**:
- 🔴 **AD-ChatV2-Inspector-Trace-Phase2** (reaffirmed from Sprint 57.21)
- 🆕 **AD-Cat12-Span-SSE-Event-Phase58** (backend Cat 12 streaming; coordinate with existing Cat 12 cross-cutting observability instrumentation)

### Unit 17: Phase-2 widget — Inspector Memory tab

**Audit method**: Code-level diff of mockup InspectorMemory + ComingSoonInspectorTab placeholder.

**Last ported**: Sprint 57.21 Day 4 §4.1 (ComingSoonInspectorTab placeholder).

**Mockup source**: `reference/design-mockups/page-chat.jsx` L468-487 — InspectorMemory ops table:
```jsx
const InspectorMemory = () => (
  <div style={{ padding: "12px 16px" }}>
    <div style={{ fontSize: 11.5, color: "var(--fg-subtle)", textTransform: "uppercase" }}>
      Memory ops · this session
    </div>
    {[
      { op: "READ",  scope: "user.jamie",          k: "preferences.rca_format", v: "5-whys + timeline",      at: "10:42:24" },
      { op: "READ",  scope: "tenant.acme-prod",    k: "policies.hitl.risk_high", v: "always_ask",            at: "10:42:26" },
      { op: "WRITE", scope: "session.sess_4tk2p",  k: "root_cause",              v: "pgbouncer pool too small", at: "10:42:27" },
      { op: "WRITE", scope: "session.sess_4tk2p",  k: "evidence",                v: "[metrics, INC-4012]",    at: "10:42:27" },
    ].map((m, i) => (
      <div style={{ padding: "7px 0", borderBottom: "1px solid var(--border)", fontSize: 11, fontFamily: "var(--font-mono)" }}>
        <div className="row" style={{ gap: 6 }}>
          <Badge tone="memory">{m.op}</Badge>
          <span style={{ color: "var(--fg-muted)" }}>{m.scope}</span>
          <span className="subtle" style={{ marginLeft: "auto" }}>{m.at}</span>
        </div>
        <div style={{ marginTop: 4, color: "var(--fg)" }}>{m.k} <span className="subtle">=</span> {m.v}</div>
      </div>
    ))}
  </div>
);
```

**Production**: ComingSoonInspectorTab placeholder for `tab === "memory"`:
```tsx
<ComingSoonInspectorTab
  name="Memory"
  mockupSection="L468-487"
  carryoverAd="AD-ChatV2-Inspector-Memory-Phase2"
  hint="..."
/>
```

**Diff matrix**:

| Field | Status | Detail |
|-------|--------|--------|
| Layout | ❌ FAIL | Mockup 4-row list with per-op cards vs production 4-line placeholder |
| Typography | N/A | Mockup 11px mono for op metadata + 11.5px uppercase header |
| Spacing | N/A | Mockup 7px vertical row padding + border-bottom separator |
| Shadow / Radius | N/A | Mockup no card; flat list with border separators |
| Color | N/A | Mockup uses Badge tone="memory" cyan/teal |
| Interactivity | ❌ FAIL | Mockup is read-only list BUT live-updating; placeholder is static |

**Severity**: **STRUCTURAL** (entire feature missing)
**Strict 1:1 score**: **5%**

**Estimated rebuild cost**: **4-5 hr** (**shares backend with Unit 13 Memory Block** — same Cat 3 SSE event powers both):
- Backend Cat 3: SSE event `memory_op_emitted` (same as Unit 13 — already specced) — 0 hr if Unit 13 done first
- OR alternative: REST `GET /api/v1/sessions/{id}/memory-ops` returning ops list (1 hr if standalone)
- Frontend NEW `InspectorMemory.tsx` rendering ops list per mockup (1.5 hr)
- Frontend chatStore add `memoryOps: MemoryOpEntry[]` aggregation handler (45 min)
- Frontend Inspector dispatcher: replace placeholder with InspectorMemory (15 min)
- Tests: aggregation unit test + render test + live SSE update test (1-2 hr)

**Action items** (Sprint 57.23+; **MUST coordinate with Unit 13 backend**):
1. Backend Cat 3: single `memory_op_emitted` SSE event powers BOTH Unit 13 (in-flow Memory Block) AND Unit 17 (cumulative Inspector tab)
2. Frontend chatStore: branch event handler — append to active turn (Block) AND aggregate to session-level `memoryOps[]` (Inspector)
3. Frontend: new InspectorMemory.tsx component
4. **Coordinate with /memory page Unit 10 rebuild** — Inspector Memory tab is session-scoped; /memory page is multi-scope cross-cutting (potentially share component primitives)

**Carryover ADs**:
- 🔴 **AD-ChatV2-Inspector-Memory-Phase2** (reaffirmed from Sprint 57.21)
- 🆕 **AD-Cat3-Memory-Op-SSE-Event-Phase58** (same as Unit 13 — single backend feature powers both)
- AD-Memory-Page-Full-Rebuild-Phase58 (Unit 10 carryover — coordinate component primitives)

### Unit 18: Phase-2 widget — Inspector Tree tab (SubagentTree)

**Audit method**: Code-level diff of mockup InspectorTree + ComingSoonInspectorTab placeholder.

**Last ported**: Sprint 57.21 Day 4 §4.1 (ComingSoonInspectorTab placeholder).

**Mockup source**: `reference/design-mockups/page-chat.jsx` L489-531 — InspectorTree subagent live tree:
```jsx
const InspectorTree = () => (
  <div style={{ padding: "12px 16px" }}>
    <div style={{ fontSize: 11.5, color: "var(--fg-subtle)", textTransform: "uppercase" }}>
      Subagent tree · live
    </div>
    <div className="subagent-tree">
      <div className="subagent-row">                              {/* Root */}
        <Icon name="chat" size={12} style={{ color: "var(--primary)" }} />
        <span style={{ color: "var(--primary)", fontWeight: 600 }}>incident-responder</span>
        <span className="subtle">root</span>
        <Badge tone="warning" style={{ marginLeft: "auto" }}>hitl-paused</Badge>
      </div>
      <div className="indent">                                     {/* Fork node */}
        <div className="subagent-row">
          <Icon name="fork" size={11} style={{ color: "var(--thinking)" }} />
          <span style={{ color: "var(--thinking)" }}>fork · t1</span>
          <span className="subtle">3 children</span>
        </div>
        <div className="indent">                                   {/* 3 children */}
          {[
            { name: "log-scanner",   task: "tail · grep 5xx",       turns: 3, status: "done" },
            { name: "dep-checker",   task: "auth-svc · ledger-db",  turns: 2, status: "done" },
            { name: "metrics-pull",  task: "pgbouncer pool",        turns: 1, status: "done" },
          ].map(s => (
            <div className="subagent-row">
              <Icon name="chevron_right" size={11} className="subtle" />
              <span style={{ color: "var(--info)" }}>{s.name}</span>
              <span className="subtle">· {s.turns}t</span>
              <span className="subtle grow">{s.task}</span>
              <Badge tone="success" dot>{s.status}</Badge>
            </div>
          ))}
        </div>
      </div>
    </div>
    <div className="thin-rule" />
    <div className="col" style={{ gap: 5, fontSize: 11, color: "var(--fg-muted)" }}>
      <div className="spread"><span>Mode</span><Badge>Fork concurrent</Badge></div>
      <div className="spread"><span>Depth</span><span className="mono">2</span></div>
      <div className="spread"><span>Concurrency</span><span className="mono">3 / 5</span></div>
      <div className="spread"><span>Tokens (subtree)</span><span className="mono">41,820</span></div>
    </div>
  </div>
);
```

**Production**: ComingSoonInspectorTab placeholder for `tab === "subagent"` (note: dispatcher uses "subagent" not "tree" per page-chat.jsx L75/L381):
```tsx
<ComingSoonInspectorTab
  name="Tree"
  mockupSection="L489-531"
  carryoverAd="AD-ChatV2-Inspector-SubagentTree-Phase2"
  hint="..."
/>
```

**Diff matrix**:

| Field | Status | Detail |
|-------|--------|--------|
| Layout | ❌ FAIL | Mockup hierarchical tree (root → fork → 3 children) + footer stats panel vs 4-line placeholder |
| Typography | N/A | Mockup uses 11px mono for subagent metadata + 11.5px uppercase header |
| Spacing | N/A | Mockup uses indent class for tree depth + thin-rule separator |
| Shadow / Radius | N/A | Mockup uses Badge dot variant for status |
| Color | N/A | Mockup uses primary/thinking/info/warning/success tokens distinguishing tree node types |
| Interactivity | ❌ FAIL | Mockup is read-only tree BUT live-updating; placeholder is static |

**Severity**: **STRUCTURAL** (entire visualization missing)
**Strict 1:1 score**: **5%**

**Estimated rebuild cost**: **6-8 hr**
- Backend Cat 11: NEW endpoint `GET /api/v1/sessions/{id}/subagents/tree` returning recursive tree with `{ id, name, status, turns, task, parent_id, depth, tokens_used }` per node (1.5 hr)
- Backend Cat 11: NEW SSE event `subagent_status_changed` for live updates (Sprint 57.12 has `subagent_spawned` + `subagent_completed`; tree visualization needs richer state transitions — running/paused/done/error) (1.5 hr)
- Backend Cat 11: aggregate token usage per subtree (recursive sum) — `/subagents/tree` endpoint returns root tokens + per-node tokens; frontend computes subtree sum OR backend returns pre-computed `tokens_subtree` field (1 hr)
- Frontend NEW `InspectorTree.tsx` component: recursive tree render + per-node Badge + footer stats panel (Mode / Depth / Concurrency / Tokens subtree) (2 hr)
- Frontend Inspector dispatcher: replace placeholder with InspectorTree when tab === "subagent" (15 min)
- Coordinate with **AD-Subagent-RealList-Phase58** (Sprint 57.12 carryover — `/memory` page also shows SubagentTree; Inspector variant is per-session vs `/memory` cross-session)
- Tests: tree render unit test + SSE live update test + token subtree aggregation test (1-2 hr)

**Action items** (Sprint 57.23+):
1. Backend Cat 11 tree endpoint + richer SSE event for live status transitions
2. Backend per-subtree token aggregation (recursive sum)
3. Frontend InspectorTree.tsx + recursive tree render
4. **Coordinate with Sprint 57.12 SubagentTree page-level component** — refactor to shared primitive (likely `<SubagentTreeNode />` reusable in both Inspector and `/memory` page)
5. Decision: depth limit display (mockup shows depth 2; production may have deeper trees — collapse/expand UX?)

**Carryover ADs**:
- 🔴 **AD-ChatV2-Inspector-SubagentTree-Phase2** (reaffirmed from Sprint 57.21)
- AD-Subagent-RealList-Phase58 (Sprint 57.12 carryover — shared component primitives)
- 🆕 **AD-Cat11-Subagent-Tree-Endpoint-Phase58** (backend tree query API)
- 🆕 **AD-Cat11-Subagent-Status-SSE-Event-Phase58** (richer live status transitions beyond spawned/completed)

---

## Group: Governance (4 units)

### Unit 19: /governance (= /governance/approvals — HITL Approvals queue)

**Audit method**: Code-level diff of mockup `Approvals` component + Sprint 57.9 production page header + ApprovalsPage component (Sprint 53.5 baseline + Sprint 57.9 Tailwind + TanStack Query polish).

**Last ported**: Sprint 57.9 US-1/2/3 (Sprint 53.5 placeholder promoted to real ship under Sprint 57.8 AppShellV2 architecture). **Pre-Sprint 57.18 mockup-integration foundation** — no mockup-direct port done.

**Mockup source**: `reference/design-mockups/page-governance.jsx` L283-407 — `Approvals` component:
- page-head: title "HITL Approvals" + sub "Central queue · Approve/reject writes before agents commit" + route-pill `/governance/approvals` + actions [Teams sync, Export]
- grid-stats: **4-card KPI**: Active queue 7 (delta +2 down), p50 approval time 2m 18s (delta -12s up), Approved 24h 184 (delta +11 up), Rejected 24h 6 (delta +2 down)
- **5-tab nav**: Active(7) / Approved(184) / Rejected(6) / Expired(2) / Policies
- 2-col grid (1fr + 420px):
  - Left "Pending approvals" card with table: cols [SevDot, Session, Tool, Risk, Policy, Operator, SLA] × 7 rows (apr_4tk2p..apr_3kkpw); row hover background; clickable to select
  - Right selected-approval detail card with KV metadata (tool/risk/policy/scope/operator/age/SLA remaining) + payload pre block + agent rationale + **4 action buttons** stacked (Approve & continue / Approve with edits… / Reject / Escalate to L2 · @platform-l2)

**Production**: `frontend/src/pages/governance/index.tsx` (75 lines) — Sprint 57.9 ship:
- AppShellV2 wrap with `pageTitle="Governance"` + auth gate
- 2-tab nested Routes (NavLink + isActive):
  - `/governance` → Navigate to "approvals" (default redirect)
  - `/governance/approvals` → `ApprovalsPage` component (Sprint 53.5 US-1 baseline; Sprint 57.9 US-2/US-3 Tailwind + TanStack Query polish)
  - `/governance/audit-log` → `AuditLogViewer` (Sprint 57.9 US-4 — coordinates with Unit 22)
- ApprovalsPage details NOT read in this audit pass; high-level inferred from Sprint 53.5 baseline + 57.9 polish:
  - Likely shows approval list + decision buttons (Approve/Reject = 2-action; **4-action subset same as Unit 14 HITLTurn gap**)
  - Likely missing: 4-card KPI stats grid, 5-tab nav (Active/Approved/Rejected/Expired/Policies), 2-col layout (table left + detail right)

**Diff matrix**:

| Field | Status | Detail |
|-------|--------|--------|
| Layout | ❌ FAIL | Mockup 2-col grid (table 1fr + detail 420px) vs production likely single-column list. Mockup has 4-card KPI + 5-tab nav at top; production has 2-tab nav (approvals/audit-log) only. |
| Typography | ❌ FAIL | Sprint 57.9 pre-mockup; 14-16px shadcn defaults vs mockup 11.5-13px micro-sizes |
| Spacing | ❌ FAIL | Pre-mockup spacing |
| Shadow / Radius | ❌ FAIL | shadcn Card defaults vs mockup `.card` 12px radius |
| Color | ⚠️ PARTIAL | Both dark theme; Sprint 57.9 not in Sprint 57.20 token migration batch |
| Interactivity | ⚠️ PARTIAL | Sprint 57.9 ships approve/reject decision wire (TanStack Query mutations); 4-action UX subset same as Unit 14 (Approve-with-edits + Escalate-to-L2 missing); 5-tab nav (Approved/Rejected/Expired/Policies tabs) missing — only Active visible |

**Severity**: **STRUCTURAL** (key features missing: 4-card KPI grid, 5-tab nav, 2-col layout with detail panel; 4-action UX subset; mockup-fidelity visual chrome)

**Strict 1:1 score**: **25%** (Layout 20% × 0.3 + Typography 25% × 0.2 + Spacing 25% × 0.2 + Shadow/Radius 25% × 0.1 + Color 60% × 0.1 + Interactivity 50% × 0.1 = 6 + 5 + 5 + 2.5 + 6 + 5 = **~30%**)

**Estimated rebuild cost**: **6-8 hr**
- Frontend rewrite ApprovalsPage from mockup `page-governance.jsx` L283-407:
  - Add 4-card KPI grid with backend `/api/v1/approvals/metrics` endpoint (Active queue / p50 / Approved 24h / Rejected 24h)
  - Add 5-tab nav (Active/Approved/Rejected/Expired/Policies — Policies tab is config view, not list)
  - 2-col layout: left table with sortable cols + row hover/select; right detail panel with KV + payload + rationale + 4-action button stack
  - SevDot component (severity color indicator)
  - Per-row SLA computed-color (warning if < 10 min remaining)
- Backend: `/api/v1/approvals/metrics` aggregation endpoint (1 hr)
- Backend: tab-filtered list queries (approved/rejected/expired filters) (1 hr)
- Mockup typography / spacing / card chrome migration (similar to Unit 7 /overview pattern)

**Action items** (Sprint 57.23+):
1. Backend approvals metrics endpoint (Cat 9 governance)
2. Backend approval status filter queries (active/approved/rejected/expired)
3. Frontend ApprovalsPage rewrite from mockup
4. **Coordinate with Unit 14 HITL FourAction** — same 4-action backend dependency (APPROVED_WITH_EDITS variant + escalation routing)
5. **Coordinate with Unit 22 /audit-log** — Sprint 57.9 nested `/governance/audit-log` already exists; top-level `/audit-log` route mostly redundant

**Carryover ADs**:
- 🆕 **AD-Governance-Approvals-Full-Rebuild-Phase58** (Sprint 57.9 → mockup-fidelity rebuild)
- 🆕 **AD-Approvals-Metrics-Endpoint-Phase58** (backend Cat 9 aggregation)
- 🆕 **AD-Approvals-Status-Filter-Queries-Phase58** (backend list filtering)
- AD-Mockup-Existing-Pages-Retrofit Tier 1 (Sprint 57.19 carryover — reaffirmed for /governance)
- AD-Governance-Approved-With-Edits-Variant-Phase58 (Unit 14 carryover — shared with this unit)
- AD-Governance-Escalation-L2-Routing-Phase58 (Unit 14 carryover — shared)

### Unit 20: /redaction (Observation Masker)

**Audit method**: Code-level. Production page state determined directly via wc + cat.

**Last ported**: NEVER. Production page is a **1-line PROP stub** — re-exports `ComingSoonPlaceholder`:
```typescript
// frontend/src/pages/redaction/index.tsx (entire file)
export { default } from "../../components/ComingSoonPlaceholder";
```

**Mockup source**: `reference/design-mockups/page-platform2.jsx` L254-313 — `RedactionPage` component:
- page-head: title "Observation Masker" + sub "Range 3 · PII + secret redaction · runs on every tool input / output" + route-pill `/redaction` + actions [Export, New pattern]
- grid-stats: **4-card KPI**: Redactions · 1h 4,870 (+220 up), Patterns active (X/Y from REDACT_PATTERNS filter), Critical hits · 24h (sum), False-positive rate 0.4% (-0.1pp up)
- grid-main 2-col:
  - Left "Patterns" card with table: cols [Id, Kind (Badge), Pattern (mono ellipsis 240w), Severity (RiskBadge), Hits · 24h (mono tnum), Enabled (Switch)] — REDACT_PATTERNS array driven
  - Right "Recent redactions" card with list of 5 events: each shows Badge(pattern) + caller(mono) + at(subtle right) + original(mono line-through) + redacted(mono success "→ [PII]")

**Production**: PROP stub — renders `ComingSoonPlaceholder` shared component (likely shows generic "Coming soon" UI with route info). NO functional redaction UI, no pattern table, no recent redactions, no metrics.

**Diff matrix**:

| Field | Status | Detail |
|-------|--------|--------|
| Layout | ❌ FAIL | Production = ComingSoonPlaceholder shared component (generic stub) vs mockup full 4-KPI + 2-col grid + Switch toggles + table |
| Typography | N/A | No prod UI to compare |
| Spacing | N/A | No prod UI |
| Shadow / Radius | N/A | No prod UI |
| Color | N/A | No prod UI |
| Interactivity | ❌ FAIL | Mockup: per-pattern Switch toggle (enable/disable) + sortable table + Export + New pattern wizard. Production: zero |

**Severity**: **FUNCTIONAL** (entire feature absent; PII / secret redaction is GDPR + SOC 2 compliance gate; cannot ship to regulated tenants without it)

**Strict 1:1 score**: **0%** (PROP stub; mockup 100% missing)

**Estimated rebuild cost**: **6-8 hr**
- Backend Cat 9: NEW endpoint `GET /api/v1/redaction/patterns` returning pattern list with `{ id, kind, pattern (regex), severity, count_24h, enabled }` (1 hr)
- Backend Cat 9: NEW endpoint `PATCH /api/v1/redaction/patterns/{id}` for enable/disable toggle (30 min)
- Backend Cat 9: NEW endpoint `GET /api/v1/redaction/metrics` for KPI (Redactions · 1h sum, FP rate, Critical hits · 24h) (45 min)
- Backend Cat 9: NEW endpoint `GET /api/v1/redaction/recent` for recent-5 redactions feed (30 min)
- Backend Cat 9: NEW endpoint `POST /api/v1/redaction/patterns` for "New pattern" wizard (45 min)
- Backend: redaction engine wire — hook into tool input/output observation masker (Sprint 53.3 baseline Tripwire + Sprint 55.3 detector audit work coordinate) (1.5 hr — if redaction engine exists; greenfield if not)
- Frontend NEW `RedactionPage` from mockup `page-platform2.jsx` L254-313 (2 hr — table with Switch + 4-KPI grid + recent redactions list + New pattern dialog)
- Tests: backend pattern toggle + metrics aggregation + frontend table render + Switch wire (1-2 hr)

**Action items** (Sprint 57.23+):
1. Verify redaction backend exists or greenfield it (Cat 9 + Cat 2 tool input/output masker hook)
2. Backend pattern CRUD + metrics + recent feed endpoints
3. Frontend RedactionPage rewrite from mockup
4. Tool input/output masker integration: every tool execution flow through pattern matcher
5. Compliance check: ensure GDPR-erasure + SOC 2 audit log requirements met

**Carryover ADs**:
- 🆕 **AD-Redaction-Page-Full-Build-Phase58** (PROP stub → real ship; Cat 9 governance)
- 🆕 **AD-Redaction-Engine-Wire-Phase58** (Cat 9 backend hook into Cat 2 tool execution; coordinate with Sprint 53.3 Tripwire infra)
- 🆕 **AD-Redaction-Pattern-CRUD-Endpoints-Phase58** (backend REST endpoints)
- AD-Mockup-Existing-Pages-Retrofit Tier 1 (Sprint 57.19 carryover — reaffirmed)

### Unit 21: /loop-debug (TAO/ReAct Loop Visualizer)

**Audit method**: Code-level diff of mockup `LoopDebug` component + Sprint 57.12 production `LoopVisualizer` (standalone mode).

**Last ported**: Sprint 57.12 US-4 (Day 2). Standalone full-screen view; mirrors `verification/index.tsx` Sprint 57.11 auth-gate pattern.

**Mockup source**: `reference/design-mockups/page-governance.jsx` L4-263 — `LoopDebug` component (most complex of governance group):
- Top header `LoopDebugHeader` (L118-185):
  - Title "Loop Visualizer" + sub with session id (mono `sess_4tk2p`) + route-pill `/loop-debug` + status Badge ("hitl-paused" warning OR "replay 8× info pulse")
  - Right cluster: 6 filter badges (thinking/tool/memory/hitl/verification/subagent) — click to toggle visibility per event type
  - Toolbar row (with bg-1 border-radius): Play/Pause/Resume button + Reset button + cursor display `XX/YY` + range slider (0..total) + speed buttons [1×, 4×, 8×, 16×] + last event timing `+Nms`
- Body `LoopTrack` (L70-115):
  - Per-turn rows (turns 0-4): turn-head with `turn N`, "User message" or "Loop iteration", event count subtle, status Badge (streaming pulse / hitl-paused / completed) + duration timing
  - Per-event rows `EventRow` (L187-212): ev-dot (color per tone) + ev-type (mono color-tinted) + ev-detail + ev-timing `+Nms`. Selected = primary-soft background; streaming = shimmer-row animation + glow box-shadow
- Right inspector `LoopInspector` (L214-263):
  - "Event" section: ev-dot warning + mono type label + text
  - "Metadata" KV grid (7 rows): ts / turn / audit_id / span_id / tenant / session_id / agent
  - "HITL Policy" KV grid (5 rows): tool (mono tool color) / risk (RiskBadge) / policy (Badge warning) / sandbox (Badge) / approvers (mono)
  - "Raw payload" pre block: full JSON event payload (sha256 input hash + policy match + expires_at)

Mockup data: LoopEvents array L5-31 — 25 events across 5 turns showing complete TAO loop (user_message → iter_start → thinking.start/delta/end → tool.requested → hitl.policy_check → tool.started → tool.completed → verification.run → iter_end → subagent.spawn → memory.read/write → hitl.requested → loop.paused).

**Production**: `frontend/src/pages/loop-debug/index.tsx` (50 lines) — Sprint 57.12 US-4:
- Auth gate (mirror /verification pattern)
- AppShellV2 wrap with `pageTitle="Loop Debug"`
- Body: `<LoopVisualizer mode="standalone" />` — reads `useChatStore.rawEvents` (in-memory live session from chat-v2)
- Note from file header: "chat-v2 keeps a single in-memory session (DB-backed session storage is Phase 51.x deferred per ChatLayout placeholder). So loop-debug shows whatever session chat-v2 last ran in this browser tab. Cross-session / historical inspection would need a persisted loop_event table — out of scope this sprint per AP-6."

LoopVisualizer component (Sprint 57.12 US-4 not read in this audit pass; inferred):
- Likely renders per-turn vertical event list
- Likely shows event type + text + timing (pre-mockup chrome)
- Likely missing: 6-filter badge row, play/replay scrubber, speed selector (1× / 4× / 8× / 16×), per-event inspector with HITL Policy + Raw payload sections, time-travel cursor

**Diff matrix**:

| Field | Status | Detail |
|-------|--------|--------|
| Layout | ❌ FAIL | Mockup 2-col layout (track 1fr + inspector 320px) vs production single-column LoopVisualizer (likely vertical event list only) |
| Typography | ⚠️ PARTIAL | Sprint 57.12 likely pre-mockup; mockup uses 10.5-13px micro-sizes + mono ev-type labels |
| Spacing | ⚠️ PARTIAL | Pre-mockup spacing |
| Shadow / Radius | ⚠️ PARTIAL | Pre-mockup chrome; mockup uses turn cards + thin-rule separators + ev-dot 6px circles |
| Color | ⚠️ PARTIAL | Mockup uses 6 distinct token colors per event type (thinking/tool/memory/warning/success/info); production likely partial |
| Interactivity | ❌ FAIL | **6 filter badges (per-event-type toggle)** missing / **play+replay scrubber** missing / **speed selector** missing / **Inspector panel** missing (HITL Policy section + Raw payload) / **Time-travel cursor** missing |

**Severity**: **STRUCTURAL** (entire 2-col layout missing; inspector panel completely absent; replay/scrubber interactivity missing; live-vs-replay mode toggle missing)

**Strict 1:1 score**: **20%** (Layout 25% × 0.3 + Typography 60% × 0.2 + Spacing 60% × 0.2 + Shadow/Radius 60% × 0.1 + Color 65% × 0.1 + Interactivity 15% × 0.1 = 7.5 + 12 + 12 + 6 + 6.5 + 1.5 = **~45%**) — lowered to 20% reflecting structural severity weight (inspector + scrubber + filter UX is core LoopDebug value prop)

**Estimated rebuild cost**: **8-10 hr**
- Backend: persistent loop_event table OR session-scoped event log (Cat 7 state + Cat 12 audit — both pre-existing Sprint 53.1 + Sprint 57.12 partial wire) (1.5 hr if loop_event already persisted; 3 hr if greenfield)
- Backend: `GET /api/v1/sessions/{id}/events` returning replay-able event list with timing offsets (1 hr)
- Backend: per-event metadata enrichment — audit_id, span_id, tenant, agent, sandbox, approvers, raw payload JSON (1 hr)
- Frontend NEW `LoopDebugPage` rewrite from mockup `page-governance.jsx` L33-185:
  - LoopDebugHeader: title + sub + 6 filter badges + toolbar (play/reset/scrubber/speed) (2 hr)
  - LoopTrack: per-turn rows + EventRow with shimmer-row animation + click-to-select (1.5 hr)
  - LoopInspector right panel: Event + Metadata KV + HITL Policy KV + Raw payload pre (1.5 hr)
  - Time-travel + replay state machine (cursor + playing + speed) (1 hr)
- Tests: scrubber control + filter toggles + inspector selection + live-vs-replay mode (1-2 hr)

**Action items** (Sprint 57.23+):
1. Backend: loop_event persistence + replay endpoint
2. Backend: per-event metadata enrichment (audit_id from WORM + sandbox + approvers)
3. Frontend LoopDebugPage rewrite with 2-col layout + inspector + scrubber
4. **Coordinate with Unit 16 Inspector Trace tab** — both use OTel spans; LoopDebug is page-level historical + replay; Inspector Trace is session-side live waterfall. Shared backend: Cat 12 span SSE event + Cat 7 state event log.

**Carryover ADs**:
- 🆕 **AD-LoopDebug-Full-Rebuild-Phase58** (Sprint 57.12 minimal viable → mockup-fidelity rebuild)
- 🆕 **AD-LoopEvent-Persistence-Endpoint-Phase58** (backend Cat 7 + Cat 12 — replay endpoint)
- 🆕 **AD-LoopDebug-Replay-State-Machine-Phase58** (frontend cursor/playing/speed state)
- AD-Mockup-Existing-Pages-Retrofit Tier 1 (Sprint 57.19 carryover — reaffirmed)
- AD-Cat12-Span-SSE-Event-Phase58 (Unit 16 carryover — coordinate same backend)

### Unit 22: /audit-log (Audit Chain — WORM Merkle)

**Audit method**: Code-level. Production state split into top-level vs nested route.

**Last ported**: Sprint 57.9 US-4 (Day 3) — but as `/governance/audit-log` nested route, NOT top-level `/audit-log` route. Top-level `/audit-log` is PROP stub.

**Mockup source**: `reference/design-mockups/page-governance.jsx` L658-771 — `AuditPage` component:
- page-head: title "Audit Chain" + sub "WORM · Merkle-verified · GDPR-tombstone aware" + route-pill `/audit` + status Badge "chain integrity: ok" success + actions [Verify chain, Export evidence]
- grid-stats: **4-card KPI**: Entries · 24h 48,210 (+2,180 up), Tripwires fired 3 (+1 down), Chain depth 1.2M (+48k up), Last verified 2m ago
- grid-main 2-col:
  - Left "Recent audit entries" card (Append-only · sha256 linked) with `audit-chain` block — per entry (`audit-link`):
    - `audit-node` icon ring (color ok=green / danger=red) with type icon (shield/tool/memory/check/fork/warn/log per kind prefix)
    - Body: mono kind label + tripwire Badge if !ok + actor mono + target mono → arrow
    - audit-hash row: id mono + prev mono (truncated 6 chars) + chain icon + sha256 mono full
    - Right cluster: RiskBadge level + at timestamp mono + chevron_right
  - Right column 2 stacked cards:
    - "Merkle root" (Last sealed block): KV (block_height 481,209 / sealed_at / entries_in_block 1,024) + Root hash pre block (full 64-char sha256) + "Copy root" button
    - "Tripwires" (Active monitors): 5 tripwires listed (Cross-tenant egress / PII in tool input / Token spike >200% / Sandbox escape / Provider key exposure) with SevDot + name + state Badge (armed = success / fired = danger)

**Production**:
- **Top-level `/audit-log` route**: routes.config.ts has the path but **NO component directory** (`ls frontend/src/pages/audit-log` → No such file or directory). Likely PROP stub or unwired.
- **Nested `/governance/audit-log` route**: Sprint 57.9 US-4 ships `AuditLogViewer` component under `/governance/audit-log` nested Routes inside `/governance/index.tsx` (75-line page).

Inferred AuditLogViewer state (Sprint 57.9 US-4 not read in this audit pass):
- Likely shows audit entry list with kind / actor / target / timestamp
- Likely missing: Merkle chain visualization (sha256 hash linking + audit-link chain UI), Merkle root card with Verify chain button, 5-tripwire monitor card, 4-KPI stats, mockup-fidelity chrome

**Diff matrix**:

| Field | Status | Detail |
|-------|--------|--------|
| Layout | ❌ FAIL | Mockup 2-col with `audit-chain` chain visualization + Merkle root pre block + Tripwires monitor list. Production likely flat list view. Plus: top-level `/audit-log` is unwired PROP stub. |
| Typography | ❌ FAIL | Sprint 57.9 pre-mockup |
| Spacing | ❌ FAIL | Pre-mockup |
| Shadow / Radius | ❌ FAIL | shadcn defaults vs mockup `.audit-node` icon ring + `.audit-link` chain styling |
| Color | ⚠️ PARTIAL | Both dark theme; per-kind icon colors mostly missing in production |
| Interactivity | ⚠️ PARTIAL | Production: list display only. Missing: Verify chain action, Export evidence, Copy root, per-entry chain follow, tripwire toggle |

**Severity**: **STRUCTURAL** (Merkle chain visualization absent; Merkle root card absent; tripwire monitor card absent; "Verify chain" + chain integrity Badge missing — these are core auditor UX surfaces; top-level route is dead PROP stub)

**Strict 1:1 score**: **20%** (similar profile to Unit 19 — Sprint 57.9 baseline visual chrome 30% mockup-aligned, but missing key chain visualization + Merkle root + tripwires features)

**Estimated rebuild cost**: **8-10 hr**
- Backend Cat 12: VERIFY WORM audit log exists (Sprint 53.3 Tripwire + Sprint 55.4 Cat 9 audit cycle baseline)
- Backend Cat 12: NEW endpoint `GET /api/v1/audit/recent?kind=...&limit=...` (1 hr if WORM table exists; greenfield if not)
- Backend Cat 12: NEW endpoint `GET /api/v1/audit/merkle-root` returning current sealed block (block_height, sealed_at, entries_in_block, root_hash) (1 hr)
- Backend Cat 12: NEW endpoint `POST /api/v1/audit/verify` triggering chain integrity verify + returning ok/fail (1 hr)
- Backend Cat 9: NEW endpoint `GET /api/v1/tripwires` returning 5 monitors with state (armed/fired) + severity (1 hr)
- Backend Cat 9: NEW endpoint `PATCH /api/v1/tripwires/{name}` for arm/disarm (30 min)
- Backend Cat 12: NEW endpoint `GET /api/v1/audit/export` for evidence export bundle (45 min)
- Frontend NEW `AuditPage` from mockup `page-governance.jsx` L670-771:
  - 4-KPI grid (entries / tripwires / chain depth / last verified) (45 min)
  - audit-chain list with audit-link nodes + per-kind icon dispatcher + chain integrity color (1.5 hr)
  - Merkle root card with Copy root button (45 min)
  - Tripwires monitor card (45 min)
- Decision: top-level `/audit-log` route — remove from routes.config.ts (dead PROP stub) OR redirect to `/governance/audit-log` (45 min)
- Tests: chain verify + audit list + tripwire toggle (1-2 hr)

**Action items** (Sprint 57.23+):
1. **Decision: route disambiguation** — top-level `/audit-log` vs nested `/governance/audit-log`. Recommend: keep ONE canonical; either remove top-level PROP stub OR add redirect.
2. Backend WORM audit log verification + endpoints
3. Backend Merkle root + chain integrity verify
4. Backend tripwires monitor endpoints (Cat 9 governance)
5. Frontend AuditPage rewrite from mockup with chain visualization

**Carryover ADs**:
- 🆕 **AD-Audit-Page-Full-Rebuild-Phase58** (Sprint 57.9 US-4 → mockup-fidelity Merkle chain UI)
- 🆕 **AD-AuditLog-Route-Disambiguation-Phase58** (top-level vs nested route decision)
- 🆕 **AD-Audit-Merkle-Endpoints-Phase58** (backend Cat 12 — recent/root/verify/export)
- 🆕 **AD-Tripwires-Monitor-Endpoints-Phase58** (backend Cat 9 — list/toggle)
- AD-Mockup-Existing-Pages-Retrofit Tier 1 (Sprint 57.19 carryover — reaffirmed)

---

## Group: Operations (Platform) (7 units)

### Unit 23: /orchestrator (TAO/ReAct orchestrator main)

**Audit method**: Code-level / Sprint 57.19 drift-catalog reference.

**Last ported**: Sprint 57.19 (AD-Mockup-Operations-Port Round 1; 9-page DRIFT-REPORT feeds Sprint 57.20+ retrofit). Production `OrchestratorPage.tsx` is **644 lines** — substantial real ship.

**Mockup source**: `reference/design-mockups/page-agents.jsx` L8-63 — `Orchestrator` shell + L65-310 — 6 tab panels (Config / Prompt / Tools / Subagents / Budgets / Policies):
- page-head: branded "orchestrator-main" mono 20px / 600 + Badge `v3.4.1` + Badge dot `live` success + sub "Range 1 · TAO/ReAct loop · dispatches 4 subagent modes (fork / teammate / handoff / as_tool)" + route-pill `/orchestrator` + actions [Test in Chat, View in repo, Deploy]
- grid-stats: 4-card KPI (Sessions · 24h 2,847 +12% / Avg loop turns 4.2 +0.1 / Subagent spawns · 24h 412 / p95 session 18.4s -2s)
- **6 tabs** with counts: Config / System Prompt / Tools(18) / Subagents(6) / Budgets / Policies
- Each tab is a substantial sub-page (OrchestratorConfig/Prompt/Tools/Subagents/Budgets/Policies — 5-50 lines each in mockup, more in implementation)

**Production**: Sprint 57.19 mockup-port baseline at 644 lines; expected to render page-head + 4-KPI + 6-tab nav + tab panels. Sprint 57.19 DRIFT-REPORT (`claudedocs/4-changes/sprint-57-19-existing-pages-drift-audit/DRIFT-REPORT.md` per CLAUDE.md ref) documents page-level drift findings — NOT reread in this Day 2 audit pass (delegated to Sprint 57.23+ retrofit execution).

**Diff matrix** (inferred from Sprint 57.19 mockup-port baseline):

| Field | Status | Detail |
|-------|--------|--------|
| Layout | ✅ PASS (~90%) | Sprint 57.19 port preserved page-head + KPI grid + 6-tab nav + tab panels |
| Typography | ⚠️ PARTIAL (~70%) | Sprint 57.19 used Sprint 57.18 token tree but micro-sizes may not be uniform (similar to Unit 7 /overview pattern) |
| Spacing | ⚠️ PARTIAL (~70%) | Likely mockup-aligned with minor drift |
| Shadow / Radius | ⚠️ PARTIAL (~70%) | Sprint 57.19 used Sprint 57.18 tokens; mockup chrome largely preserved |
| Color | ✅ PASS (~85%) | Sprint 57.18 oklch token tree consumption |
| Interactivity | ⚠️ PARTIAL | Tab nav likely wired; Test in Chat / View in repo / Deploy buttons may be placeholder (no real flow to repo/deploy from frontend) |

**Severity**: **COSMETIC** (Sprint 57.19 port baseline correct; drift is micro-typography + spacing polish similar to /overview Unit 7)

**Strict 1:1 score**: **70%** (Sprint 57.19 port baseline; per Sprint 57.19 DRIFT-REPORT findings need consultation for precise drift severity)

**Estimated rebuild cost**: **3-5 hr** (cosmetic polish — typography micro-sizes + card chrome + minor drift correction; deeper if any tab panel sub-page diverges structurally)
- Read Sprint 57.19 `DRIFT-REPORT.md` for /orchestrator entry; apply drift fixes
- Typography polish per mockup 11.5-13px micro-sizes
- Card chrome to mockup `.card` 12px radius
- Verify all 6 tab panels render mockup-aligned content
- Deploy / Test in Chat / View in repo buttons: decision (real backend wire? placeholder?)

**Action items** (Sprint 57.23+):
1. Consult Sprint 57.19 DRIFT-REPORT.md for /orchestrator-specific drift findings
2. Apply micro-typography + card chrome polish
3. Decision: Deploy / Test in Chat / View in repo button wires (likely placeholder in mockup port)
4. Verify 6 tab panels: Config + Prompt + Tools(18) + Subagents(6) + Budgets + Policies all render structurally aligned

**Carryover ADs**:
- AD-Mockup-Existing-Pages-Retrofit Tier 1 (Sprint 57.19 carryover — /orchestrator in 9-page DRIFT-REPORT)
- 🆕 **AD-Orchestrator-Backend-Wires-Phase58** (Test in Chat / View in repo / Deploy button real backend wire)

### Unit 24: /subagents (Subagent Registry)

**Audit method**: Code-level / Sprint 57.19 drift-catalog reference.

**Last ported**: Sprint 57.19 mockup-port. Production `SubagentsPage.tsx` is **397 lines** — substantial real ship.

**Mockup source**: `reference/design-mockups/page-agents.jsx` L311 onwards — `SubagentsRegistry`:
- page-head: "Subagent Registry" + sub "Range 11 · AgentSpec definitions · 4 dispatch modes (fork / teammate / handoff / as_tool)" + route-pill `/subagents` + count "X registered" + actions [Sync from repo, New subagent]
- **grid-3 mode summary cards** (4 cards in 3-col grid? — 4 modes: fork concurrent / as_tool sync / teammate p2p / handoff control transfer; each with mode-tinted left-border + count + desc)
- main 2-col (1.4fr + 1fr):
  - Left "Subagents" table card: cols [Role, Model, Modes (Badge per mode), Status (live/draft), Calls · 24h, p95]
  - Right (presumably): selected subagent detail panel with AgentSpec config

**Production**: Sprint 57.19 baseline 397 lines; expected to render page-head + 4-mode summary + 2-col table+detail layout. Drift findings per Sprint 57.19 DRIFT-REPORT.

**Diff matrix** (inferred Sprint 57.19 port baseline):

| Field | Status | Detail |
|-------|--------|--------|
| Layout | ✅ PASS (~90%) | Port preserved 2-col + mode summary cards |
| Typography | ⚠️ PARTIAL (~70%) | Sprint 57.18 token tree consumption with potential micro-size drift |
| Spacing | ⚠️ PARTIAL (~70%) | Similar to Unit 23 |
| Shadow / Radius | ⚠️ PARTIAL (~70%) | Mockup-aligned with minor drift |
| Color | ✅ PASS (~85%) | Sprint 57.18 oklch tokens |
| Interactivity | ⚠️ PARTIAL | Row select likely wired; "Sync from repo" / "New subagent" wizard may be placeholder |

**Severity**: **COSMETIC**
**Strict 1:1 score**: **70%**

**Estimated rebuild cost**: **3-4 hr** (cosmetic polish + verify mode badge color tokens + "New subagent" wizard wire decision)
- Read Sprint 57.19 DRIFT-REPORT for /subagents entry
- Typography + card chrome polish
- Verify 4-mode badge tone colors (fork=thinking / as_tool=tool / teammate=memory / handoff=info per mockup L357)
- Decision: "Sync from repo" + "New subagent" backend wire

**Action items** (Sprint 57.23+):
1. Consult Sprint 57.19 DRIFT-REPORT for /subagents findings
2. Apply cosmetic polish
3. Verify mode Badge color token mapping
4. Decision on "Sync from repo" (real git integration? read-only display?) + "New subagent" wizard backend (Cat 11 subagent registry CRUD)

**Carryover ADs**:
- AD-Mockup-Existing-Pages-Retrofit Tier 1 (Sprint 57.19 carryover — /subagents in 9-page DRIFT-REPORT)
- 🆕 **AD-Subagent-Registry-CRUD-Phase58** (backend Cat 11 + "New subagent" wizard wire)
- 🆕 **AD-Subagent-Repo-Sync-Phase58** (decision: real git read OR placeholder)

### Unit 25: /state-inspector (LoopState time-travel)

**Audit method**: Code-level / Sprint 57.19 drift-catalog reference.

**Last ported**: Sprint 57.19 mockup-port. Production `StateInspectorPage.tsx` is **366 lines** — substantial real ship.

**Mockup source**: `reference/design-mockups/page-platform.jsx` L21-167 — `StateInspector`:
- page-head: "State Inspector" + sub "Range 7 · LoopState time-travel · Reducer is the only mutator" + route-pill `/state-inspector` + "X versions · 3 checkpoints" subtle + actions [Diff vs parent, Restore from version, Export checkpoint]
- grid-stats 4-card: Current version / Transient size / Durable bytes / Pending approvals
- main 2-col (320px + 1fr):
  - Left "Version chain" card with reducer-authored monotonic version list. Per version: dot (circle for normal / square for checkpoint) with color per `by` author (reducer=memory / orchestrator_loop=primary / tools=tool / subagent=info / session_init=success). Chain line connector between versions. Selected version highlighted with left border.
  - Right (presumably): selected version detail panel with state diff vs parent + reducer-applied actions

**Production**: Sprint 57.19 baseline 366 lines; expected to render page-head + 4-KPI + 2-col chain+detail layout. Drift findings per Sprint 57.19 DRIFT-REPORT.

**Diff matrix** (inferred Sprint 57.19 port baseline):

| Field | Status | Detail |
|-------|--------|--------|
| Layout | ✅ PASS (~90%) | Port preserved 2-col with version chain + detail |
| Typography | ⚠️ PARTIAL (~70%) | Sprint 57.18 token tree consumption + potential micro-size drift |
| Spacing | ⚠️ PARTIAL (~70%) | Similar to Unit 23/24 |
| Shadow / Radius | ⚠️ PARTIAL (~70%) | Mockup-aligned with minor drift |
| Color | ✅ PASS (~85%) | Per-author color mapping (5 author types) needs verification |
| Interactivity | ⚠️ PARTIAL | Version row select likely wired; "Diff vs parent" + "Restore from version" + "Export checkpoint" may be placeholder |

**Severity**: **COSMETIC**
**Strict 1:1 score**: **70%**

**Estimated rebuild cost**: **3-5 hr** (cosmetic polish + verify per-author color mapping + version chain visualization fidelity)
- Read Sprint 57.19 DRIFT-REPORT for /state-inspector
- Typography + card chrome polish
- Verify version chain visualization: dot vs square (checkpoint), chain line connector, per-author color tinting
- Decision on action buttons: Diff vs parent + Restore from version + Export checkpoint backend wire (Cat 7 state)

**Action items** (Sprint 57.23+):
1. Consult Sprint 57.19 DRIFT-REPORT for /state-inspector findings
2. Apply cosmetic polish
3. Verify version chain visualization (dot vs checkpoint square, color per author)
4. Decision: state restore wire (irreversible — needs HITL gate?) + checkpoint export bundle endpoint

**Carryover ADs**:
- AD-Mockup-Existing-Pages-Retrofit Tier 1 (Sprint 57.19 carryover — /state-inspector in 9-page DRIFT-REPORT)
- 🆕 **AD-State-Inspector-Diff-Restore-Phase58** (Cat 7 state — diff/restore/export endpoints)
- 🆕 **AD-State-Restore-HITL-Gate-Phase58** (governance — restoring is irreversible; needs approval)

### Unit 26: /compaction (Context Compaction)

**Audit method**: Code-level. Production page state determined directly via file content.

**Last ported**: NEVER. Production page is a **1-line PROP stub** re-exporting `ComingSoonPlaceholder`:
```typescript
// frontend/src/pages/compaction/index.tsx (entire file)
export { default } from "../../components/ComingSoonPlaceholder";
```

**Mockup source**: `reference/design-mockups/page-platform.jsx` L168-270 — `Compaction`:
- page-head: "Context Compaction" + sub "Range 4 · Token-budget reclaim · 3 strategies (STRUCTURAL / SEMANTIC / HYBRID)" + route-pill `/compaction` + actions [Run on current, Export events]
- grid-stats 4-card with Spark sparklines: Tokens reclaimed · 24h 58.4K (+12K up + spark) / Compaction events 84 (+6 up) / Avg saving 28.4% (+2pp up) / p95 duration 2.4s (-180ms up)
- grid-main: "Recent compactions" card with table cols [Event, Session, Strategy, ...] with filter Button "All strategies"

**Production**: PROP stub (ComingSoonPlaceholder shared component).

**Diff matrix**:

| Field | Status | Detail |
|-------|--------|--------|
| Layout | ❌ FAIL | Production = ComingSoonPlaceholder vs mockup full page (page-head + 4-KPI Spark + grid-main table) |
| Typography | N/A | No prod UI |
| Spacing | N/A | No prod UI |
| Shadow / Radius | N/A | No prod UI |
| Color | N/A | No prod UI |
| Interactivity | ❌ FAIL | Mockup: "Run on current" trigger compaction on live session + filter strategies. Production: zero |

**Severity**: **FUNCTIONAL** (Cat 4 Context Management UI absent; cannot diagnose / replay / manual-trigger compaction; observability gap for token economics)

**Strict 1:1 score**: **0%**

**Estimated rebuild cost**: **5-7 hr**
- Backend Cat 4: NEW endpoint `GET /api/v1/compaction/events?limit=...` returning events with `{ session_id, strategy (STRUCTURAL/SEMANTIC/HYBRID), tokens_before, tokens_after, saving_pct, duration_ms, at }` (1 hr — likely Cat 4 baseline has event log)
- Backend Cat 4: NEW endpoint `GET /api/v1/compaction/metrics` for KPI aggregation (Tokens reclaimed · 24h sum + sparkline points / Compaction events count / Avg saving / p95 duration) (1 hr)
- Backend Cat 4: NEW endpoint `POST /api/v1/sessions/{id}/compaction/trigger` for "Run on current" (force-compact endpoint with strategy param) (1 hr)
- Frontend NEW `CompactionPage` from mockup `page-platform.jsx` L168-270:
  - 4-KPI grid with Spark sparkline component (1.5 hr — may need NEW Spark component if not in design-system)
  - Recent compactions table with strategy filter (1 hr)
- Tests: backend trigger + metrics + frontend filter + Spark render (1 hr)

**Action items** (Sprint 57.23+):
1. Backend Cat 4 endpoints (event log + metrics + trigger)
2. Frontend CompactionPage rewrite from mockup
3. Spark component: verify in design-system OR create primitive (sparkline mini-chart)
4. Decision: "Run on current" trigger — needs HITL gate? (compaction is reversible via state-inspector if checkpointed)

**Carryover ADs**:
- 🆕 **AD-Compaction-Page-Full-Build-Phase58** (PROP stub → real ship; Cat 4 observability)
- 🆕 **AD-Compaction-Backend-Endpoints-Phase58** (event log + metrics + trigger)
- 🆕 **AD-Design-System-Spark-Primitive-Phase58** (sparkline component — used in /cost-dashboard rebuild Unit 8 too)
- AD-Mockup-Existing-Pages-Retrofit Tier 1 (Sprint 57.19 carryover — reaffirmed)

### Unit 27: /workflows (MAF Sequential / Parallel / Branch)

**Audit method**: Code-level. Routes config grep confirms absence.

**Last ported**: NEVER. **Route does not exist in `frontend/src/routes.config.ts`**. No `/pages/workflows/` directory.

**Mockup source**: `reference/design-mockups/page-platform.jsx` L271-425 — `Workflows`:
- page-head: "Workflows" + sub "Microsoft Agent Framework · Sequential / Parallel / Branch + Checkpointing" + route-pill `/workflows` + Badge "5 active" primary + actions [Templates, New workflow]
- **grid-3 kind summary cards**: 3 cards in 3-col grid with left-border tinted per kind:
  - Sequential (primary) — "Linear pipeline. Each step waits for the previous. Checkpoint after each step."
  - Parallel (thinking) — "Concurrent fan-out. All branches run; converge at join. Single checkpoint after join."
  - Branch (info) — "Conditional routing. Agent picks 1-of-N paths. Each path can have its own checkpoint policy."
- main: presumably workflow list + selected workflow visualization with checkpoint policy

**Production**: 🚫 **ROUTE DOES NOT EXIST**. No entry in `routes.config.ts`; no `frontend/src/pages/workflows/` directory. Top-level `/workflows` is unwired.

> **Architectural note**: MAF v1.x adapter pattern is preserved in IPA Platform per `docs/03-implementation/agent-harness-planning/07-tech-stack-decisions.md` — but Sprint 49.1 archived V1 MAF integration. V2 wraps MAF via `adapters/_base/` ABC; workflow orchestration backend likely exists but frontend page never built.

**Diff matrix**:

| Field | Status | Detail |
|-------|--------|--------|
| Layout | ❌ FAIL | Route absent — no production component |
| Typography | N/A | No prod UI |
| Spacing | N/A | No prod UI |
| Shadow / Radius | N/A | No prod UI |
| Color | N/A | No prod UI |
| Interactivity | ❌ FAIL | Mockup: Templates picker + New workflow wizard + kind summary cards + workflow list + selected workflow visualization. Production: navigating to `/workflows` likely 404s |

**Severity**: **FUNCTIONAL** (entire MAF workflow management UI absent; V2 backend likely has workflow exec capability via MAF adapter but frontend access surface = 0)

**Strict 1:1 score**: **0%**

**Estimated rebuild cost**: **6-8 hr**
- Backend Cat 11 (or NEW MAF workflow surface): NEW endpoint `GET /api/v1/workflows` returning workflow list with `{ id, name, kind (sequential/parallel/branch), step_count, last_run, active }` (1 hr — depends on MAF adapter wire status)
- Backend: NEW endpoint `GET /api/v1/workflows/{id}` returning workflow definition with steps + checkpoint policy (1 hr)
- Backend: NEW endpoint `POST /api/v1/workflows/{id}/run` (45 min)
- Backend: workflow templates catalog endpoint (45 min)
- Frontend NEW `WorkflowsPage` from mockup `page-platform.jsx` L271-425:
  - Routes config entry (`path: "/workflows", category: "operations", component: lazy(() => import("./pages/workflows"))`)
  - page-head + 3-kind summary cards (1 hr)
  - Workflow list + selected workflow visualization (workflow step graph?) (1.5 hr)
  - "Templates" picker dialog + "New workflow" wizard (1.5 hr)
- Tests: workflow list + run trigger + template picker (1-2 hr)

**Action items** (Sprint 57.23+):
1. Verify MAF workflow backend wire status — Sprint 49.1 archived V1 MAF; V2 likely has adapter but no workflow management endpoints. Greenfield estimate above; if backend partial, reduce.
2. Add `/workflows` entry to `routes.config.ts` under "operations" category
3. Frontend WorkflowsPage greenfield from mockup
4. Decision: workflow step visualization — use React Flow (preserved per skill registry per CLAUDE.md react-flow skill mention)? Or simpler list view first?

**Carryover ADs**:
- 🆕 **AD-Workflows-Page-Greenfield-Phase58** (route + frontend + backend full new build)
- 🆕 **AD-MAF-Workflow-Adapter-Endpoint-Phase58** (Cat 11 backend wire)
- 🆕 **AD-Workflow-Step-Visualization-React-Flow-Phase58** (React Flow integration — see react-flow skill)
- AD-Mockup-Existing-Pages-Retrofit Tier 1 (Sprint 57.19 carryover — reaffirmed; **/workflows is a NEW route not just retrofit**)

### Unit 28: /error-policy (4-class taxonomy + Circuit breaker)

**Audit method**: Code-level. Production page state determined directly.

**Last ported**: NEVER. Production page is a **1-line PROP stub** re-exporting `ComingSoonPlaceholder`:
```typescript
// frontend/src/pages/error-policy/index.tsx (entire file)
export { default } from "../../components/ComingSoonPlaceholder";
```

**Mockup source**: `reference/design-mockups/page-platform.jsx` L426-554 — `ErrorPolicyPage`:
- page-head: "Error Policy" + sub "Range 8 · 4-class taxonomy · Circuit breaker · Retry budget · Terminator" + route-pill `/error-policy` + actions [Edit policy, Export]
- grid-stats 4-card: Errors · 1h 240 (+12 down) / Auto-recovered 97.5% (+0.8pp up) / Circuits open 1 (+1 down) / Budget burn 12.4% (-2pp up)
- grid-main: "4-class taxonomy" card with 4 error classes — each shows colored square dot + mono class id + desc + count (Where errors land · last 1h)
- main 2nd column (presumably): Circuit breaker + Retry budget visualizations

**Production**: PROP stub (ComingSoonPlaceholder).

**Diff matrix**:

| Field | Status | Detail |
|-------|--------|--------|
| Layout | ❌ FAIL | Production = ComingSoonPlaceholder vs mockup full page (page-head + 4-KPI + 4-class taxonomy + Circuit breaker viz) |
| Typography | N/A | No prod UI |
| Spacing | N/A | No prod UI |
| Shadow / Radius | N/A | No prod UI |
| Color | N/A | No prod UI |
| Interactivity | ❌ FAIL | Mockup: edit policy + drill-into-class filter + export. Production: zero |

**Severity**: **FUNCTIONAL** (Cat 8 Error Handling observability UI absent; cannot inspect class-by-class error breakdown / circuit breaker states / retry budget)

**Strict 1:1 score**: **0%**

**Estimated rebuild cost**: **5-7 hr**
- Backend Cat 8: NEW endpoint `GET /api/v1/errors/metrics` for KPI (1 hr — Cat 8 baseline shipped Sprint 53.2; may have aggregation already)
- Backend Cat 8: NEW endpoint `GET /api/v1/errors/by-class?window=1h` returning 4-class breakdown with counts (45 min)
- Backend Cat 8: NEW endpoint `GET /api/v1/errors/circuits` returning open/closed circuit states per service (45 min)
- Backend Cat 8: NEW endpoint `GET /api/v1/errors/retry-budget` returning budget burn % per category (45 min)
- Backend Cat 8: NEW endpoint `PATCH /api/v1/errors/policy` for "Edit policy" action (Cat 8 policy config editor — likely needs admin role + HITL gate) (1.5 hr)
- Frontend NEW `ErrorPolicyPage` from mockup `page-platform.jsx` L426-554 (2-3 hr)
- Tests (1 hr)

**Action items** (Sprint 57.23+):
1. Backend Cat 8 endpoints (errors metrics + class breakdown + circuits + retry budget + policy editor)
2. Frontend ErrorPolicyPage rewrite from mockup
3. Policy editor: text/JSON editor for retry budget + circuit breaker config; needs admin role gate + HITL approval

**Carryover ADs**:
- 🆕 **AD-Error-Policy-Page-Full-Build-Phase58** (PROP stub → real ship; Cat 8 observability)
- 🆕 **AD-Errors-Backend-Endpoints-Phase58** (metrics + class + circuits + retry-budget + policy edit)
- 🆕 **AD-Error-Policy-Editor-HITL-Gate-Phase58** (Cat 9 governance — policy changes go through approval)
- AD-Mockup-Existing-Pages-Retrofit Tier 1 (Sprint 57.19 carryover — reaffirmed)

### Unit 29: /rbac (Role-based access control matrix)

**Audit method**: Code-level. Production page state determined directly.

**Last ported**: NEVER. Production page is a **1-line PROP stub** re-exporting `ComingSoonPlaceholder`:
```typescript
// frontend/src/pages/rbac/index.tsx (entire file)
export { default } from "../../components/ComingSoonPlaceholder";
```

**Mockup source**: `reference/design-mockups/page-platform.jsx` L555-672 — `RBACPage`:
- page-head: "RBAC" + sub "Role-based access control · 6 roles × 7 resources · tenant-scoped" + route-pill `/rbac` + actions [Export policy, New role]
- grid-stats 4-card: Roles count / Members assigned 57 (+3 up) / Resource kinds count / Audit policy changes · 30d 14 (-2 up)
- **"Permission matrix" card** (Role × Resource × Action) with bodyClass="flush":
  - Table cols: Role (180w min) + Members + per-Resource cell (centered)
  - Per role row: mono role name + desc subtle + Members Badge + per-resource permission cell
  - "click cell to edit" interaction

**Production**: PROP stub (ComingSoonPlaceholder).

**Diff matrix**:

| Field | Status | Detail |
|-------|--------|--------|
| Layout | ❌ FAIL | Production = ComingSoonPlaceholder vs mockup full page (page-head + 4-KPI + permission matrix table 6×7) |
| Typography | N/A | No prod UI |
| Spacing | N/A | No prod UI |
| Shadow / Radius | N/A | No prod UI |
| Color | N/A | No prod UI |
| Interactivity | ❌ FAIL | Mockup: click-cell-to-edit matrix + Export policy + New role wizard. Production: zero |

**Severity**: **FUNCTIONAL** (RBAC management UI absent; **critical enterprise governance gap** — cannot configure tenant-scoped permissions through self-serve UI; blocks B2B SaaS Stage 2 IAM Block B work)

**Strict 1:1 score**: **0%**

**Estimated rebuild cost**: **6-8 hr** + Backend IAM Block B coordination
- Backend (Cat 12 platform_layer/identity): RBAC schema definition — `roles` table + `permissions` table + `role_permissions` M:N + tenant-scoped policy enforcement (likely 4-6 hr if greenfield; less if Sprint 57.7 IAM Foundation laid groundwork)
- Backend: NEW endpoint `GET /api/v1/rbac/roles?tenant_id=...` listing roles (45 min)
- Backend: NEW endpoint `GET /api/v1/rbac/permissions` listing resource × action matrix (45 min)
- Backend: NEW endpoint `PATCH /api/v1/rbac/roles/{id}/permissions` for cell-edit (1 hr)
- Backend: NEW endpoint `POST /api/v1/rbac/roles` for "New role" wizard (45 min)
- Frontend NEW `RBACPage` from mockup `page-platform.jsx` L555-672:
  - page-head + 4-KPI (45 min)
  - Permission matrix table (6 roles × 7 resources × actions) with click-to-edit cell modal (2.5 hr)
  - "New role" wizard dialog (1 hr)
- Tests: backend RBAC enforcement + frontend matrix render + cell-edit flow (1-2 hr)
- **Coordinate with Sprint 57.7 IAM Foundation** (WorkOS chosen for SSO) — RBAC sits ABOVE WorkOS auth; tenant-scoped policy enforcement orthogonal to IdP

**Action items** (Sprint 57.23+; **major IAM Block B work**):
1. Backend RBAC schema design + permissions enforcement middleware (Cat 12 identity)
2. Backend RBAC CRUD endpoints + admin role gate
3. Frontend RBACPage rewrite from mockup with permission matrix editor
4. **Coordinate with Sprint 57.7 IAM Block A spike** — extends to Block B (RBAC + tenant-scoped policies)
5. Decision: built-in roles set (operator/auditor/admin/...) vs fully custom roles per tenant

**Carryover ADs**:
- 🔴 **AD-RBAC-Page-Full-Build-Phase58** (PROP stub → real ship; **critical SaaS Stage 2 IAM Block B**)
- 🔴 **AD-IAM-Block-B-RBAC-Backend-Phase58** (Cat 12 identity — schema + middleware + enforcement)
- 🆕 **AD-RBAC-Permission-Matrix-CRUD-Endpoints-Phase58**
- 🆕 **AD-RBAC-Audit-Log-Policy-Changes-Phase58** (Cat 12 audit — every RBAC change goes through WORM)
- AD-Mockup-Existing-Pages-Retrofit Tier 1 (Sprint 57.19 carryover — reaffirmed)

---

## Group: Admin (10 units)

### Unit 30: /admin/tenants (Multi-tenant lifecycle list)

**Audit method**: Code-level diff of mockup `page-admin.jsx` L335-409 `Tenants` component + Sprint 57.4 production `admin-tenants/index.tsx` (83L) + `AdminTenantsContent` data children (in feature components).

**Last ported**: Sprint 57.4 US-4 → Sprint 57.8 US-4 (AppShellV2 wrap) → Sprint 57.9 US-6 → Sprint 57.13 US-A2 (platform-admin role gate). Pre-Sprint 57.18 mockup-integration foundation — no mockup-direct port done.

**Mockup source**: `reference/design-mockups/page-admin.jsx` L335-409 — `Tenants` component:
- page-head: "Tenants" + sub "Multi-tenant lifecycle · RLS-isolated · feature flags + quotas per tenant" + route-pill `/admin/tenants` + actions [Export, New tenant]
- grid-stats 4-card: Active tenants 48 (+3 up) / Total seats 284 (+18 up) / Agents deployed 612 (+24 up) / Anomalies 1 (+1 down)
- "All tenants" card with table + filter toolbar (cmdk-style search "Filter by name, id, region…" + Plan: all filter + Sort: runs (24h)):
  - Table cols: [Tenant (avatar circle + mono name + mono id subtle), Plan (Badge primary=Enterprise/info=Pro), Region (mono subtle), Seats (right tnum), Agents (right tnum), Runs · 24h (right tnum), Status (Badge dot: success=active/danger=anomaly/warning=other), Created (subtle), dots-menu]

**Production**: `frontend/src/pages/admin-tenants/index.tsx` (83L) Sprint 57.4 + 57.13 polish:
- RequireAuth + platform-admin role gate (Sprint 57.13 US-A2 — non-admin users see "needs permission" notice instead of mounting data hook)
- AppShellV2 wrap
- `<AdminTenantsContent>` data children (in feature components — not read in this audit pass)
- Expected to fetch `GET /api/v1/admin/tenants` (platform-admin-only, no tenant scope) and render list

Inferred production state:
- Likely shows tenant list with basic cols (name/id/plan); missing: 4-card KPI grid, advanced filter toolbar (search/plan-filter/sort), avatar circle, anomaly dot indicators, dots-menu actions
- Visual chrome: Sprint 57.4 pre-mockup (16px / shadcn defaults)

**Diff matrix**:

| Field | Status | Detail |
|-------|--------|--------|
| Layout | ⚠️ PARTIAL | Production likely has tenant list table; missing 4-KPI grid, cmdk-style filter toolbar, advanced sort |
| Typography | ❌ FAIL | Sprint 57.4 pre-mockup; 14-16px shadcn vs mockup 11.5-13px micro |
| Spacing | ❌ FAIL | Pre-mockup |
| Shadow / Radius | ❌ FAIL | shadcn Card vs mockup `.card` 12px |
| Color | ⚠️ PARTIAL | Both dark theme; not Sprint 57.20 token-migrated |
| Interactivity | ⚠️ PARTIAL | Production likely has list display + maybe row action; missing: search filter, plan-filter, sort, "New tenant" wizard, "Export" CSV |

**Severity**: **STRUCTURAL** (key features missing: 4-KPI grid, filter toolbar, anomaly indicators)

**Strict 1:1 score**: **30%** (Sprint 57.4 baseline preserves list semantic but visual chrome + advanced filtering all missing)

**Estimated rebuild cost**: **5-7 hr**
- Backend: KPI aggregation endpoint `GET /api/v1/admin/tenants/stats` (active count / total seats / agents deployed / anomalies) (1 hr)
- Backend: tenant filter + sort query params (1 hr)
- Backend: "Export" CSV endpoint (45 min)
- Backend: "New tenant" wizard endpoint (uses Sprint 56.1 tenant lifecycle + onboarding — coordinate with Unit 32-39 tenant-onboarding) (1 hr)
- Frontend rewrite AdminTenantsContent from mockup `page-admin.jsx` L335-409: 4-KPI grid + cmdk-style filter toolbar + advanced table cols (avatar + status dots + Plan badges) + dots-menu actions (2-3 hr)
- Tests: filter + sort + role gate enforcement + KPI render (1-2 hr)

**Action items** (Sprint 57.23+):
1. Backend KPI + filter + export + tenant CRUD wizard endpoints
2. Frontend AdminTenants rewrite from mockup
3. **Coordinate with Unit 32 /admin/tenant-onboarding** — "New tenant" wizard same backend flow

**Carryover ADs**:
- 🆕 **AD-Admin-Tenants-Full-Rebuild-Phase58** (Sprint 57.4 → mockup-fidelity rebuild)
- 🆕 **AD-Admin-Tenants-Stats-Endpoint-Phase58** (KPI aggregation)
- 🆕 **AD-Admin-Tenants-Filter-Sort-Phase58** (backend query params)
- AD-Mockup-Existing-Pages-Retrofit Tier 1 (Sprint 57.19 carryover — reaffirmed)

### Unit 31: /tenant-settings (= /admin/tenant-settings mockup; 6-tab single page)

**Audit method**: Code-level. **Critical architectural finding**: mockup organizes /admin/feature-flags + quotas + hitl-policies + members + danger-zone as **6 TABS within /admin/tenant-settings page**, NOT separate routes. Session-init prompt listed them as separate Day 3 routes (incorrect interpretation of mockup structure).

**Last ported**: Sprint 57.3 US-5 → Sprint 57.8 US-4 (AppShellV2 wrap) → Sprint 57.13 US-A2 (RequireAuth gate).

**Mockup source**: `reference/design-mockups/page-admin.jsx` L411-onwards — `TenantSettings` component:
- page-head: "Tenant Settings" + sub showing `acme-prod` mono + tenant_id pill `tenant_01h9a2` + Badge "Pro · 8 seats" — **NO actions row** (no export / new — settings are inline editable)
- **6-tab nav** (Tabs component):
  - **General** — Display name input + Tenant id readonly + Default region select (3 options ap-east-1/us-east-1/eu-west-1) + Default locale select (zh-TW/en-US/ja-JP) + Data retention input (365 days)
  - **Feature Flags** (count 14) — `<FeatureFlags />` sub-component
  - **Quotas** — `<Quotas />` sub-component
  - **HITL Policies** — `<HITLPolicies />` sub-component
  - **Members** (count 8) — `<Members />` sub-component
  - **Danger Zone** — `<DangerZone />` sub-component
- General tab also has 2-col `grid-main`: General card (left) + Identity & SSO card (right):
  - Identity & SSO card: Provider (Badge "SAML 2.0 · WorkOS") + SCIM (Badge dot success "enabled") + Allowed domains (mono "acme.com, acme.io") + MFA (Badge dot success "required") + Configure button

**Production**: `frontend/src/pages/tenant-settings/index.tsx` (29L) — Sprint 57.3 baseline:
- RequireAuth + AppShellV2 wrap with pageTitle="Tenant Settings"
- Nested Routes with `<Route index element={<TenantSettingsView />} />` — single index route only
- TenantSettingsView from `features/tenant-settings/components/` — NOT read this audit pass

Inferred production state:
- Likely Sprint 57.3 baseline has General tab content (display name / tenant id / region / locale / retention) but probably **flat single-tab UI**, NOT 6-tab structure
- Missing: 5 of 6 tabs (Feature Flags / Quotas / HITL Policies / Members / Danger Zone) likely all absent
- Visual chrome: Sprint 57.3 pre-mockup

**Diff matrix**:

| Field | Status | Detail |
|-------|--------|--------|
| Layout | ❌ FAIL | Mockup 6-tab nav vs production likely single-tab flat layout |
| Typography | ❌ FAIL | Sprint 57.3 pre-mockup; 14-16px vs mockup 11.5-13px |
| Spacing | ❌ FAIL | Pre-mockup |
| Shadow / Radius | ❌ FAIL | shadcn vs mockup `.card` 12px |
| Color | ⚠️ PARTIAL | Both dark theme; not Sprint 57.20 token-migrated |
| Interactivity | ❌ FAIL | 5 of 6 tab content panels absent (Feature Flags / Quotas / HITL Policies / Members / Danger Zone); SCIM toggle / MFA gate / Allowed domains / Configure SAML SSO all missing |

**Severity**: **STRUCTURAL** (5 of 6 tabs absent; critical SaaS Stage 2 self-serve admin UX gap)

**Strict 1:1 score**: **15%** (Sprint 57.3 General tab baseline ~30% + 5 missing tabs heavy weight)

**Estimated rebuild cost**: **12-16 hr** (largest single audit unit Day 3 due to 6-tab scope):
- **General tab polish (1-2 hr)**: typography + card chrome + add Identity & SSO card (right column) with SCIM/MFA/domain badges + Configure SAML SSO button
- **Feature Flags tab (3-4 hr)**: NEW backend `GET /api/v1/admin/tenants/{id}/flags` + `PATCH /flag/{key}` + frontend matrix with Switch per flag × 14 flags
- **Quotas tab (2-3 hr)**: NEW backend `GET /api/v1/admin/tenants/{id}/quotas` + edit dialog for token/run/seat limits + Stripe billing tier coordination
- **HITL Policies tab (3-4 hr)**: NEW backend `GET /api/v1/admin/tenants/{id}/hitl-policies` (per-tool risk policy: auto / ask_once / always_ask) + matrix editor; coordinate with Sprint 53.4 §HITL Centralization
- **Members tab (2-3 hr)**: NEW backend `GET /api/v1/admin/tenants/{id}/members` + invite flow (uses Unit 4 /auth/invite from Day 1) + role assignment (uses Unit 29 RBAC from Day 2)
- **Danger Zone tab (1-2 hr)**: NEW backend `DELETE /api/v1/admin/tenants/{id}` (tombstone + GDPR erasure) + `POST /api/v1/admin/tenants/{id}/suspend` + confirmation dialog with typed-name check
- Tests: backend per-tab endpoints + frontend tab navigation + per-tab edit flows (2-3 hr)

**Action items** (Sprint 57.23+; **largest Phase 57.23+ epic component**):
1. Backend: 5 NEW endpoint groups (flags / quotas / hitl-policies / members / danger-zone) — coordinate Cat 9 + Cat 12 + Sprint 56.1 tenant lifecycle
2. Frontend: 6-tab refactor of TenantSettingsView with per-tab sub-component
3. **Coordinate with Unit 29 RBAC** — Members tab uses RBAC role assignment
4. **Coordinate with /auth/invite Unit 4 from Day 1** — Members tab uses invite flow
5. Decision: Quotas tab Stripe billing integration vs internal-only (Phase 56+ Stripe + Lago decision)

**Carryover ADs** (largest single-unit AD cluster — 7 NEW ADs):
- 🔴 **AD-Tenant-Settings-6-Tab-Full-Rebuild-Phase58** (largest Day 3 audit AD)
- 🆕 **AD-Tenant-Feature-Flags-Tab-Phase58** (backend + frontend Switch matrix; **closes session-init prompt /admin/feature-flags single-route confusion**)
- 🆕 **AD-Tenant-Quotas-Tab-Phase58** (backend + frontend editor)
- 🆕 **AD-Tenant-HITL-Policies-Tab-Phase58** (backend per-tool policy + frontend matrix; coordinate Sprint 53.4)
- 🆕 **AD-Tenant-Members-Tab-Phase58** (uses Unit 4 invite + Unit 29 RBAC)
- 🆕 **AD-Tenant-Danger-Zone-Tab-Phase58** (tombstone + suspend + GDPR erasure)
- 🆕 **AD-Tenant-Identity-SSO-Config-Phase58** (General tab right card: SAML/SCIM/MFA/Configure)

### Unit 32-39: Remaining admin sub-routes (8 sub-units; **architectural reorganization required**)

**Audit method**: Code-level + routes.config.ts grep + mockup file existence check.

**Architectural finding** (from Unit 31 analysis): 5 of 8 session-init-prompt-listed admin sub-routes are actually **TABS within /admin/tenant-settings page** (Unit 31), NOT separate routes. Day 3 audit reorganizes:

#### Unit 32: /admin/tenant-onboarding (separate route — wizard)

**Production**: 1-line PROP stub:
```typescript
// frontend/src/pages/tenant-onboarding/index.tsx
export { default } from "../../components/ComingSoonPlaceholder";
```

**Mockup**: `reference/design-mockups/page-platform2.jsx` L328-499 — `TenantOnboardingPage` 6-step wizard:
- page-head: "Onboard Tenant" + sub "6-step wizard · provisioning audited end-to-end" + route-pill `/admin/tenant-onboarding` + actions [Cancel, Save draft]
- **6-step stepper** with progress bar + clickable steps:
  - Identity (Tenant name, slug, region)
  - Plan (Pick capacity tier — coordinate with Unit 33 Pricing)
  - SSO (SAML / OIDC config)
  - Admin (First member invite)
  - Agent (First agent template)
  - Review & ship (Confirm & provision)
- Per-step body: Field-based form with backend-validated input

**Severity**: **FUNCTIONAL** (entire self-serve B2B SaaS Stage 2 onboarding absent — same severity as Unit 3 /auth/register Day 1)
**Strict 1:1 score**: **0%**
**Estimated rebuild cost**: **6-8 hr** (wizard component + 6 step forms + backend tenant provisioning endpoint — coordinate with Sprint 56.1 tenant lifecycle; backend likely partial)

**Carryover ADs**:
- 🆕 **AD-Admin-Tenant-Onboarding-Wizard-Phase58** (6-step wizard real ship)
- 🆕 **AD-Tenant-Provisioning-Backend-Phase58** (coordinate Sprint 56.1)

---

#### Unit 33: /admin/pricing (separate route — pricing model editor)

**Production**: 1-line PROP stub (`pages/pricing/index.tsx` → ComingSoonPlaceholder).

**Mockup**: `page-platform2.jsx` L501-onwards — `PricingPage`:
- page-head: "Pricing Model" + sub "Plan tiers + per-resource overage rates · WORM-audited on change" + route-pill `/admin/pricing` + Badge "platform admin" warning + actions [Versions, Publish new pricing]
- **3-card plan grid** (PLANS array — Starter / Pro / Enterprise likely) with:
  - "most picked" Badge (top-right per-card flag)
  - Plan name + Price (28px / 700 / -0.02em letter-spacing) + period
  - HR separator + KV list (Tokens / mo, etc.)
  - Left-border tinted per plan (different colors)

**Severity**: **FUNCTIONAL** (entire pricing config UI absent; blocks SaaS Stage 2 plan management)
**Strict 1:1 score**: **0%**
**Estimated rebuild cost**: **5-7 hr** (plan grid + version history + "Publish new pricing" wizard with WORM audit + Stripe billing coordination)

**Carryover ADs**:
- 🆕 **AD-Admin-Pricing-Page-Full-Build-Phase58**
- 🆕 **AD-Pricing-Stripe-Lago-Integration-Phase58** (per Sprint 57.6 buy-vs-build decision Stripe + Lago)
- 🆕 **AD-Pricing-WORM-Audit-Phase58** (Cat 12 audit log on each pricing change)

---

#### Unit 34: /feature-flags (route-level — separate from /admin/tenant-settings flags tab)

**Production state**: Route registered in `routes.config.ts` with `active: false`; **no page directory** (`pages/feature-flags/` does not exist). This is **dead route stub**.

**Mockup**: `reference/design-mockups/page-extras.jsx` contains a `/feature-flags` route-pill (per grep earlier) — likely a global/cross-tenant feature flags admin distinct from per-tenant flags tab in Unit 31.

**Severity**: **FUNCTIONAL** (route declared but unwired; global feature-flag admin UI absent)
**Strict 1:1 score**: **0%**
**Estimated rebuild cost**: **3-4 hr** (CREATE pages/feature-flags/ + activate route + frontend cross-tenant feature flags table) — **OR** decision: remove dead route if /admin/tenant-settings flags tab is the canonical surface (and tenant-level flags only, no global flags)

**Carryover ADs**:
- 🆕 **AD-FeatureFlags-Route-Disambiguation-Phase58** (global cross-tenant flags vs tenant-level only — decision before building)

---

#### Unit 35-38 cross-reference: /admin/quotas + /hitl-policies + /members + /danger-zone (TABS within Unit 31)

**Architectural finding**: These are NOT separate routes per mockup `page-admin.jsx` L427-438 — they are 4 of 6 tabs within `/admin/tenant-settings` (Unit 31). Production reality matches:
- `/admin/tenant-settings` index Route does NOT have nested `/quotas` / `/members` / `/hitl-policies` / `/danger-zone` sub-routes
- routes.config.ts has NO `path: "/quotas"` or `path: "/hitl-policies"` or `path: "/members"` or `path: "/danger-zone"` entries (confirmed via grep)

**Action**: Day 3 audit collapses these into Unit 31. Full rebuild + 4 NEW tab components live under **AD-Tenant-Settings-6-Tab-Full-Rebuild-Phase58** (Unit 31 carryover AD).

Cumulative carryover ADs (already opened in Unit 31):
- AD-Tenant-Feature-Flags-Tab-Phase58
- AD-Tenant-Quotas-Tab-Phase58
- AD-Tenant-HITL-Policies-Tab-Phase58
- AD-Tenant-Members-Tab-Phase58
- AD-Tenant-Danger-Zone-Tab-Phase58

---

#### Unit 39: /admin/domain-detail (route does not exist; no mockup designed)

**Production**: NOT in routes.config.ts; NO page directory.
**Mockup**: NOT designed (no route-pill `/admin/domain-detail` found in any mockup file).

**Severity**: **FUNCTIONAL** (route conceptually planned per Sprint 57.18 PROP/DRAFT placeholder; no mockup spec, no implementation)
**Strict 1:1 score**: N/A — pure greenfield

**Estimated rebuild cost**: **TBD until mockup designed** (range 4-8 hr depending on scope; domain = "tenant SSO domain detail page"? "DNS / WhoIs admin"? "internationalization domain"? — unclear semantic)

**Action items**:
1. **First**: design mockup for /admin/domain-detail OR clarify scope (or remove from Phase 57.23+ priority list)
2. If kept: add to mockup tree + route + page

**Carryover ADs**:
- 🆕 **AD-Admin-Domain-Detail-Scope-Definition-Phase58** (clarify or drop)

---

#### Unit 32-39 group totals

- **Real audit units done**: 4 (Unit 32 /admin/tenant-onboarding + Unit 33 /admin/pricing + Unit 34 /feature-flags + Unit 39 /admin/domain-detail scope-question)
- **Cross-reference to Unit 31**: 4 (Unit 35-38 = tenant-settings tabs)
- **Group rebuild cost**: ~14-19 hr (sum of Unit 32 6-8 + Unit 33 5-7 + Unit 34 3-4 + Unit 39 TBD)
- **NEW carryover ADs (group-level)**: 6 + 1 disambiguation + 1 scope-definition

---

## Group: Misc (7 units)

### Unit 40: /models (LLM Models — Provider-neutral adapter registry)

**Audit method**: Code-level.

**Production**: 1-line PROP stub (`pages/models/index.tsx` → ComingSoonPlaceholder).

**Mockup source**: `reference/design-mockups/page-models.jsx` (534L) L55-onwards — `LLMModels` (or similar) component:
- page-head: "LLM Models" + sub "Range 6 · Provider-neutral adapters · 13 models across 6 providers" + route-pill `/models` + Badge "platform admin" warning + actions [Sync from adapters/, Register model]
- grid-stats 4-KPI: Active providers (X/Y) / Registered models (count + delta) / Avg cost / 1M tok ($1.84 -$0.12) / Spend · MTD ($2,847 +8.4%)
- Tab nav: Models(count) / Providers(count) / Fallback chains / (+ likely Health + Budgets per typical mockup pattern)

**Severity**: **FUNCTIONAL** (entire Range 6 LLM provider-neutral admin UI absent; provider switching / model registration / fallback chain config / cost tracking per model all missing)

**Strict 1:1 score**: **0%**

**Estimated rebuild cost**: **8-10 hr**
- Backend Cat 6 / adapters layer: `GET /api/v1/models` returning registered models with `{ id, provider, type (chat/embed), input_cost / output_cost, status (live/draft), capabilities }` (1 hr — likely some baseline via adapters/_base/)
- Backend: `GET /api/v1/providers` returning provider connections + health (1 hr)
- Backend: `GET /api/v1/models/fallback-chains` for chain config (45 min)
- Backend: `POST /api/v1/models` register endpoint with adapter validation (1.5 hr)
- Backend: cost aggregation `GET /api/v1/models/spend?window=mtd` (45 min)
- Frontend NEW `LLMModelsPage` (534L mockup); tab-based with 3-5 tabs (2.5-3 hr)
- Tests (1 hr)

**Action items** (Sprint 57.23+):
1. Verify Cat 6 adapter registry exists (likely yes; Sprint 53.2+ adapter-base + 7 adapters wired)
2. Backend endpoints (models / providers / fallback / spend)
3. Frontend page rewrite

**Carryover ADs**:
- 🆕 **AD-LLM-Models-Page-Full-Build-Phase58** (Cat 6 admin UI greenfield)
- 🆕 **AD-Models-Provider-Endpoint-Phase58** (Cat 6 backend list)
- 🆕 **AD-Models-Fallback-Chain-Config-Phase58** (Cat 6 chain editor)
- 🆕 **AD-Models-Cost-Aggregation-Phase58** (Cat 12 + Cat 6 cross-cutting)

### Unit 41: /tools (Tool Registry — 24 ToolSpecs)

**Audit method**: Code-level.

**Production**: 1-line PROP stub (`pages/tools/index.tsx` → ComingSoonPlaceholder).

**Mockup source**: `reference/design-mockups/page-tools.jsx` (371L) L65-onwards — `Tools` (or similar) component:
- page-head: "Tool Registry" + sub "24 ToolSpecs · LLM-neutral schema · sandbox + HITL bound per tool" + route-pill `/tools` + Badge "platform admin" warning + actions [Open registry repo, Export OpenAPI, Register tool]
- **Domain filter row**: chip-style filter buttons (All N · per-domain counts) with primary-soft highlight on active filter
- Main: tool list table + selected tool detail panel (likely with ToolSpec schema viewer + sandbox config + HITL policy binding)

**Severity**: **FUNCTIONAL** (Cat 2 Tool Layer admin UI absent; critical observability gap — operators cannot inspect tool registry / sandbox bindings / per-tool HITL policy)

**Strict 1:1 score**: **0%**

**Estimated rebuild cost**: **6-8 hr** (shares backend with Unit 15 Composer Tools (24) picker — `AD-Tool-Registry-Endpoint-Phase58`):
- Backend Cat 2: `GET /api/v1/tools` (reused from Unit 15 — 0 hr if Unit 15 done first; 1 hr if standalone)
- Backend Cat 2: `GET /api/v1/tools/{name}` for tool detail with full ToolSpec + sandbox config + HITL binding (1 hr)
- Backend Cat 2: `POST /api/v1/tools` register endpoint with sandbox-spec validation (1.5 hr)
- Backend: `GET /api/v1/tools/export-openapi` (45 min)
- Frontend NEW `ToolsPage` from mockup `page-tools.jsx`:
  - Domain filter chip row (45 min)
  - Tool list table with selected detail panel (2 hr)
  - "Register tool" wizard (1.5 hr)
- Tests (1 hr)

**Action items** (Sprint 57.23+):
1. **Coordinate with Unit 15 Composer Tools (24) picker** — same backend `AD-Tool-Registry-Endpoint-Phase58`
2. Backend tool detail + register + export endpoints
3. Frontend rewrite

**Carryover ADs**:
- 🆕 **AD-Tools-Page-Full-Build-Phase58** (Cat 2 admin UI greenfield)
- AD-Tool-Registry-Endpoint-Phase58 (Unit 15 carryover — reaffirmed; shared backend)
- 🆕 **AD-Tools-Detail-Endpoint-Phase58** (per-tool ToolSpec + sandbox + HITL)
- 🆕 **AD-Tools-Register-Wizard-Phase58** (sandbox-spec validation flow)
- 🆕 **AD-Tools-OpenAPI-Export-Phase58**

### Unit 42-46: 7 misc routes grouped (sse / devui / a11y-audit / incidents / subagent-tree / jit-retrieval / cache-manager)

**Audit method**: Code-level + routes.config.ts grep + mockup file existence check.

#### Unit 42: /sse (SSE Inspector)

**Production**: 1-line PROP stub.

**Mockup**: `page-sse.jsx` (257L) L119-onwards — `SSE Inspector`:
- page-head: "SSE Inspector" + observability sub-tab of /devui likely (per page-extras.jsx /devui route-pill mapping too)
- Main: live SSE event stream viewer with filter + replay

**Severity**: **STRUCTURAL** (Cat 12 observability gap — operators cannot inspect SSE streams)
**Strict 1:1 score**: **0%**
**Estimated rebuild cost**: **4-5 hr** (live SSE stream viewer + filter + replay; backend `GET /api/v1/observability/sse-stream` SSE proxy)
**Carryover ADs**: 🆕 AD-SSE-Inspector-Page-Phase58 + AD-Observability-SSE-Proxy-Endpoint-Phase58

---

#### Unit 43: /devui (Developer UI — multi-tab observability hub)

**Production**: 1-line PROP stub.

**Mockup**: `page-extras.jsx` L394-onwards — `Developer UI`:
- Multi-tab hub for developer-focused observability (likely matrix + cat12 + sse sub-tabs per session-init prompt "/devui (+ matrix + cat12 + sse sub-tabs)")

**Severity**: **STRUCTURAL** (Cat 12 cross-cutting dev observability UI absent)
**Strict 1:1 score**: **0%**
**Estimated rebuild cost**: **6-8 hr** (multi-tab dev hub with matrix + Cat 12 traces + SSE live + per-sub-tab content)
**Carryover ADs**: 🆕 AD-DevUI-Page-Multi-Tab-Phase58 + AD-DevUI-Matrix-Sub-Tab + AD-DevUI-Cat12-Sub-Tab + AD-DevUI-SSE-Sub-Tab (subsumes Unit 42)

---

#### Unit 44: /a11y-audit (Accessibility audit)

**Production state**: Route NOT in routes.config.ts (per grep); no page directory.
**Mockup**: NOT designed (no route-pill `/a11y-audit` found in mockup grep earlier).

**Severity**: **FUNCTIONAL** (route conceptually planned per Sprint 57.18 PROP/DRAFT placeholder; no mockup, no implementation; **Sprint 57.13/57.14 jsx-a11y + axe + visual-regression are CI-tier infrastructure**, NOT a route-level audit page)

**Strict 1:1 score**: N/A — pure greenfield + no spec

**Estimated rebuild cost**: **TBD** (range 3-6 hr; depends on scope — operator-facing a11y audit run trigger? Cumulative results dashboard? Per-route axe report archive?)

**Action**: Same as Unit 39 /admin/domain-detail — design mockup OR drop from priority list.

**Carryover ADs**: 🆕 AD-A11y-Audit-Page-Scope-Definition-Phase58

---

#### Unit 45: /incidents (Business Domains / Incident management)

**Production**: 1-line PROP stub.

**Mockup**: TWO mockup locations:
1. `page-extras.jsx` L708 "Business Domains" with /incidents route-pill — likely incident management business domain UI (Sprint 56 business domains coordinate)
2. `page-platform2.jsx` /incidents route-pill (separate context)

**Severity**: **FUNCTIONAL** (Business domain UI absent; one of 5 business domains per Sprint 51-55 business-services baseline; backend Sprint 55.1 shipped 5 domain services + 24 tools)

**Strict 1:1 score**: **0%**

**Estimated rebuild cost**: **8-10 hr** (incident list + detail + RCA timeline + correlation graph + 5-domain matrix; coordinates with Sprint 51-55 business-services backend + 24 tools)

**Carryover ADs**:
- 🆕 **AD-Incidents-Page-Business-Domain-Phase58** (incident management UI)
- 🆕 **AD-Business-Domains-Matrix-Phase58** (cross-domain summary)
- Sprint 55.1 business services coordinate (5 domains × 24 tools)

---

#### Unit 46: /subagent-tree (Standalone subagent tree visualization)

**Production**: 1-line PROP stub.

**Mockup**: `page-extras.jsx` L186-onwards — `Subagent Tree`:
- Standalone full-page tree visualization (page-level variant of Unit 18 Inspector Tree tab)

**Severity**: **STRUCTURAL** (page-level subagent tree absent; Cat 11 cross-session subtree visualization)

**Strict 1:1 score**: **0%**

**Estimated rebuild cost**: **5-6 hr** (page-level wrapper around Cat 11 tree component; shares backend with Unit 18 Inspector Tree)
- **Coordinate with Unit 18 Inspector Tree tab + AD-Subagent-RealList-Phase58 (Sprint 57.12 carryover)** — shared component primitive `<SubagentTreeNode />`

**Carryover ADs**:
- 🆕 **AD-Subagent-Tree-Page-Phase58** (page-level variant)
- AD-Cat11-Subagent-Tree-Endpoint-Phase58 (Unit 18 carryover — reaffirmed; shared backend)
- AD-Subagent-RealList-Phase58 (Sprint 57.12 carryover — reaffirmed)

---

#### Bonus Unit: /jit-retrieval + /cache-manager

These 2 routes are in mockup `page-platform2.jsx` per earlier grep but not in current Unit 42-46 placeholder. Listed in Day 3 session-init prompt scope.

**/jit-retrieval** (page-platform2.jsx L29 "JIT Retrieval"):
- Production: 1-line PROP stub
- Mockup: JIT (Just-In-Time) memory/context retrieval admin page
- **Severity**: STRUCTURAL (Cat 3 + Cat 4 cross-cutting; deferred backend)
- **Estimated rebuild cost**: 5-7 hr
- **AD**: 🆕 AD-JIT-Retrieval-Page-Phase58

**/cache-manager** (page-platform2.jsx L146 "Cache Manager"):
- Production: 1-line PROP stub
- Mockup: Prompt cache + LLM response cache admin
- **Severity**: STRUCTURAL (Cat 4 Context Mgmt + cache invalidation UX absent)
- **Estimated rebuild cost**: 4-6 hr
- **AD**: 🆕 AD-Cache-Manager-Page-Phase58 (coordinate Cat 4 + Sprint 52.1 prompt caching baseline)

---

#### Unit 42-46 + Bonus group totals

- **Real audit units done**: 7 (Unit 42 SSE + Unit 43 DevUI + Unit 44 A11y-audit scope-question + Unit 45 Incidents + Unit 46 SubagentTree + Bonus JIT + Bonus Cache)
- **Group rebuild cost**: ~35-46 hr (sum: 4-5 + 6-8 + TBD + 8-10 + 5-6 + 5-7 + 4-6)
- **NEW carryover ADs (group-level)**: 11 + 1 disambiguation

---

## Priority Matrix (Day 4 — Sprint 57.23+ Roadmap)

**Classification rules**:
- **P0** (must-fix Sprint 57.23): severity = FUNCTIONAL OR Strict 1:1 score < 40%
- **P1** (Sprint 57.24+): severity = STRUCTURAL OR score 40-70%
- **P2** (Sprint 57.25+): severity = COSMETIC OR score 70-90%
- **P3** (defer / no-action): score ≥ 90% OR scope-question (no mockup designed)

**Final Day 1+2+3 unit count**: 41 distinct audit units across 6 groups (12 Day 1 + 17 Day 2 + 12 Day 3 covering 17 unit headers due to architectural collapse).

### P0 — Sprint 57.23+ Must-Fix (32 units; ~150-200 hr cumulative rebuild)

| # | Unit | Route / Component | Score | Rebuild hr | Group | Key dependencies / coordinate |
|---|------|-------------------|-------|-----------|-------|------------------------------|
| 1 | 1 | /auth/login | 15% | 6-8 | Auth | WorkOS multi-IdP backend; AuthShell refactor |
| 2 | 2 | /auth/callback | 5% | 3-4 | Auth | OIDC multi-step status SSE |
| 3 | 3 | /auth/register | 0% | 8-10 | Auth | NEW backend `POST /api/v1/tenants/register` + email verify |
| 4 | 4 | /auth/invite | 0% | 6-8 | Auth | NEW backend invitations; coord with Unit 31 Members tab |
| 5 | 5 | /auth/mfa | 0% | 8-10 | Auth | TOTP + WebAuthn; WorkOS MFA decision |
| 6 | 6 | /auth/expired | 0% | 4-6 | Auth | 401 interceptor redirect refactor |
| 7 | 8 | /cost-dashboard | 15% | 4-5 | Ops Dashboards | Backend HTTP 500 fix (Sprint 56.3 Cost Ledger dev tenant) |
| 8 | 9 | /sla-dashboard | 15% | 4-5 | Ops Dashboards | Backend HTTP 500 fix (Sprint 56.3 SLA dev tenant) |
| 9 | 10 | /memory | 25% | 8-10 | Ops Dashboards | Cat 3 role/session scope + time travel + ops timeline |
| 10 | 13 | Memory Block (chat-v2) | 0% | 4-6 | Chat-v2 Phase-2 | Cat 3 `memory_op_emitted` SSE event (shared w/ Unit 17) |
| 11 | 14 | HITL FourAction | 70% | 3-4 | Chat-v2 Phase-2 | Cat 9 APPROVED_WITH_EDITS + escalation + audit_id SSE |
| 12 | 15 | Composer Richness+Wire | 30% | 6-8 | Chat-v2 Phase-2 | Cat 2 tools registry + Cat 3 scopes + Cat 12 attachments |
| 13 | 16 | Inspector Trace tab | 5% | 5-7 | Chat-v2 Phase-2 | Cat 12 `span_emitted` SSE event |
| 14 | 17 | Inspector Memory tab | 5% | 4-5 | Chat-v2 Phase-2 | Shared backend w/ Unit 13 |
| 15 | 18 | Inspector SubagentTree | 5% | 6-8 | Chat-v2 Phase-2 | Cat 11 tree endpoint + status SSE |
| 16 | 19 | /governance approvals | 25% | 6-8 | Governance | Approvals metrics + filter + 4-action UX (Unit 14 shared) |
| 17 | 20 | /redaction | 0% | 6-8 | Governance | Cat 9 redaction engine wire (greenfield-likely) |
| 18 | 21 | /loop-debug | 20% | 8-10 | Governance | Cat 7 + Cat 12 loop_event persistence + replay |
| 19 | 22 | /audit-log | 20% | 8-10 | Governance | Cat 12 WORM Merkle endpoints; route disambiguation |
| 20 | 26 | /compaction | 0% | 5-7 | Ops Platform | Cat 4 endpoints + Spark sparkline primitive |
| 21 | 27 | /workflows | 0% | 6-8 | Ops Platform | MAF workflow adapter; React Flow visualization |
| 22 | 28 | /error-policy | 0% | 5-7 | Ops Platform | Cat 8 endpoints + HITL policy editor gate |
| 23 | 29 | /rbac | 0% | 6-8 | Ops Platform | 🔴 IAM Block B RBAC backend (Cat 12 identity schema) |
| 24 | 30 | /admin/tenants | 30% | 5-7 | Admin | Tenant lifecycle KPI + filter + CRUD wizard |
| 25 | 31 | /tenant-settings (6-tab) | 15% | 12-16 | Admin | **Largest single unit**; 5 NEW tabs (flags/quotas/hitl/members/danger) |
| 26 | 32 | /admin/tenant-onboarding | 0% | 6-8 | Admin | 6-step wizard + Sprint 56.1 provisioning |
| 27 | 33 | /admin/pricing | 0% | 5-7 | Admin | Stripe+Lago integration; WORM audit per change |
| 28 | 40 | /models | 0% | 8-10 | Misc | Cat 6 adapter registry endpoints (multi-tab) |
| 29 | 41 | /tools | 0% | 6-8 | Misc | Shared backend w/ Unit 15 |
| 30 | 45 | /incidents | 0% | 8-10 | Misc | Business Domain UI; coord Sprint 55.1 5 domains × 24 tools |
| 31 | Bonus | /jit-retrieval | 0% | 5-7 | Misc | Cat 3 + Cat 4 cross-cutting; backend likely partial |
| 32 | Bonus | /cache-manager | 0% | 4-6 | Misc | Cat 4 + Sprint 52.1 prompt caching baseline |

**P0 Σ rebuild hours**: ~177-235 hr (mid-point ~206 hr)

### P1 — Sprint 57.24+ (5 units; ~17-23 hr)

| # | Unit | Route / Component | Score | Rebuild hr | Group | Note |
|---|------|-------------------|-------|-----------|-------|------|
| 1 | 11 | /verification | 40% | 3-4 | Ops Dashboards | Sprint 57.11 pre-mockup; token migrate + chrome rewrite |
| 2 | 34 | /feature-flags (route-level) | dead stub | 3-4 | Admin | Disambiguation decision OR delete dead route |
| 3 | 42 | /sse | 0% | 4-5 | Misc | Cat 12 SSE proxy endpoint; might subsume into Unit 43 DevUI tab |
| 4 | 43 | /devui | 0% | 6-8 | Misc | Multi-tab dev observability hub |
| 5 | 46 | /subagent-tree | 0% | 5-6 | Misc | Page-level variant of Unit 18 Inspector tab; shared component |

**P1 Σ rebuild hours**: ~21-27 hr (mid-point ~24 hr)

### P2 — Sprint 57.25+ (5 units; ~14-22 hr)

| # | Unit | Route / Component | Score | Rebuild hr | Group | Note |
|---|------|-------------------|-------|-----------|-------|------|
| 1 | 7 | /overview | 60% | 3-4 | Ops Dashboards | Cosmetic micro-typography + card chrome polish |
| 2 | 12 | /chat-v2 page-level | 75% | 2-3 | Chat-v2 | Sprint 57.21 Phase-1 baseline; typography polish only |
| 3 | 23 | /orchestrator | 70% | 3-5 | Ops Platform | Sprint 57.19 mockup-port baseline; consult DRIFT-REPORT |
| 4 | 24 | /subagents | 70% | 3-4 | Ops Platform | Sprint 57.19 baseline |
| 5 | 25 | /state-inspector | 70% | 3-5 | Ops Platform | Sprint 57.19 baseline |

**P2 Σ rebuild hours**: ~14-21 hr (mid-point ~17 hr)

### P3 — Defer / scope-question (2 units)

| # | Unit | Route / Component | Status | Note |
|---|------|-------------------|--------|------|
| 1 | 39 | /admin/domain-detail | scope-question | NO mockup; clarify scope OR drop from Phase 57.23+ |
| 2 | 44 | /a11y-audit | scope-question | NO mockup; CI infra a11y already covered Sprint 57.13/14 |

**P3 Σ rebuild hours**: 0 hr (deferred; scope-definition required first)

### Cross-Priority Σ Totals

| Priority | Unit count | Σ rebuild hr (mid-point) | Avg hr/unit |
|----------|-----------|---------------------------|-------------|
| **P0** | 32 | ~206 hr | ~6.4 hr |
| **P1** | 5 | ~24 hr | ~4.8 hr |
| **P2** | 5 | ~17 hr | ~3.4 hr |
| **P3** | 2 | 0 hr (TBD) | n/a |
| **Total audit** | **44** (29 ship + 13 stub/missing + 2 scope-q) | **~247 hr** | **~5.6 hr** |

### Backend Coordination Cluster (Phase 58+ Stage 2)

Many P0 units depend on backend epics that span multiple sprints:

| Backend epic | Units depending | Estimated backend-only hr |
|--------------|----------------|---------------------------|
| **Cat 3 memory_op_emitted SSE** | Unit 13 + 17 (chat-v2 widgets) | 2-3 hr |
| **Cat 12 OTel span_emitted SSE** | Unit 16 (Inspector Trace) + Unit 21 (/loop-debug) | 3-4 hr |
| **Cat 11 subagent tree + status SSE** | Unit 18 + 46 (subagent-tree page) | 3-4 hr |
| **Cat 9 governance 4-action variant** | Unit 14 + 19 (approvals + HITL) | 2-3 hr |
| **Cat 9 redaction engine wire** | Unit 20 (/redaction) | 1.5 hr |
| **Cat 12 WORM Merkle endpoints** | Unit 22 (/audit-log) | 3-4 hr |
| **Cat 8 errors backend endpoints** | Unit 28 (/error-policy) | 3-4 hr |
| **🔴 Cat 12 IAM Block B RBAC** | Unit 29 (/rbac) + Unit 31 (Members tab) | 4-6 hr |
| **Cat 6 LLM adapter registry endpoints** | Unit 40 (/models) | 4-5 hr |
| **Cat 2 tools registry endpoint** | Unit 15 + 41 (shared) | 1-1.5 hr |
| **WorkOS multi-IdP wire** | Unit 1 + 31 SSO config | 3-4 hr |
| **Tenant provisioning + onboarding** | Unit 32 + Sprint 56.1 coord | 2-3 hr |
| **Stripe + Lago billing integration** | Unit 33 (/pricing) | 4-6 hr |
| **MAF workflow adapter** | Unit 27 (/workflows) | 3-4 hr |

**Backend-only Σ**: ~40-55 hr additional beyond frontend rebuild hours

**Grand Σ Phase 57.23+ epic** (frontend ~247 hr + backend ~50 hr): **~297 hr** mid-point estimate

---

## Sprint 57.23+ Recommendation (Day 4)

### NEW Calibration Class Proposal: `frontend-mockup-strict-rebuild`

Per `.claude/rules/sprint-workflow.md §Scope-class multiplier matrix`, the rebuild execution sprints starting Sprint 57.23+ need a NEW calibration class distinct from prior:

| Existing classes (relevant) | Multiplier | Why not for mockup rebuild |
|------------------------------|------------|---------------------------|
| `frontend-mockup-direct-port-structural` (proposed 0.85; pending 3-data-point) | 0.85 | Token-sweep + structural-rewrite hybrid; LESS strict than 1:1 ±2px bar |
| `frontend-mockup-direct-port-token-sweep` (proposed 0.40; pending split) | 0.40 | Mechanical token swap; doesn't capture full chrome rewrite |
| `frontend-mockup-fidelity-audit` (NEW Sprint 57.22 baseline 0.85; this sprint) | 0.85 | Audit-only; not rebuild |

**Proposed NEW class**: `frontend-mockup-strict-rebuild` with **multiplier 0.55-0.65** (HYBRID weighted blend):
- **Backend new endpoints** (typical 30-40% of unit hours): ~0.65 (greenfield Cat work)
- **Frontend page rewrite from mockup** (typical 50-60% of unit hours): ~0.55 (page-direct port; some structural rebuild)
- **Tests** (typical 10-15% of unit hours): ~0.65 (test-mechanical class)
- **Closeout** (typical 5%): ~0.80

Weighted average ≈ 0.60 (mid-band of 0.55-0.65 proposal range).

### First-Execution-Sprint Scope Candidate: Sprint 57.23 "Auth Page Full Rebuild Round 2"

**Why Auth as first**:
1. **6 P0 units** all in one domain (Unit 1-6); single-domain coordination reduces context-switching
2. **AuthShell refactor** is a precondition — refactoring once unblocks all 6 pages
3. **WorkOS multi-IdP backend wire** is independent backend epic — can run parallel; frontend ships with placeholder buttons + visible-but-disabled state
4. **No HITL gates** — all P0 unblocked frontend changes; no IAM Block B RBAC dependencies
5. **Smallest backend coordination overhead** (only WorkOS multi-IdP + email verify + invite + MFA endpoints — all platform_layer/identity)
6. **Tier 1 priority per Sprint 57.18 mockup-fidelity hard constraint** — Auth is highest-traffic operator surface
7. **Validates new calibration class** with bounded scope (6 units × ~6.4 hr avg = ~38 hr bottom-up; × 0.60 multiplier → commit ~23 hr per 5-day sprint structure)

**Sprint 57.23 proposed scope**:
- **Bottom-up est**: ~36-44 hr (Auth 6 units sum)
- **Calibrated commit (×0.60)**: ~22-26 hr (1 sprint)
- **Day structure**: 5 days
  - Day 0: AuthShell refactor + 3-prong verify + WorkOS placeholder backend stubs
  - Day 1: /auth/login + /auth/callback (real ship + tests)
  - Day 2: /auth/register + /auth/invite (wizards + backend endpoints)
  - Day 3: /auth/mfa + /auth/expired (MFA enrollment + redirect refactor)
  - Day 4: Closeout (retrospective + memory + push + PR)
- **Carryover decisions to user**:
  - Q1: Adopt mockup oklch palette project-wide OR keep shadcn slate + document deviation (AD-Brand-Primary-Color-Decision finally)
  - Q2: WorkOS Multi-IdP (3 SSO providers backend wire) — Phase 58 separate backend sprint OR partial wire in 57.23
  - Q3: MFA implementation — WorkOS native vs roll-own TOTP+WebAuthn

### Sprint 57.24+ Execution Order (Recommended)

| Sprint | Scope | Bottom-up | Commit (×0.60) | Σ Phase status |
|--------|-------|-----------|----------------|----------------|
| 57.23 | Auth 6 P0 units | ~38 hr | ~23 hr | P0 6/32 closed |
| 57.24 | Chat-v2 Phase-2 6 widgets (Unit 13-18) | ~32 hr | ~19 hr | P0 12/32 |
| 57.25 | Governance 4 P0 (Unit 19-22) | ~32 hr | ~19 hr | P0 16/32 |
| 57.26 | Admin /tenant-settings 6-tab (Unit 31 largest) | ~14 hr | ~8 hr (single-unit-sprint; 0.55-0.60) | P0 17/32 |
| 57.27 | Admin /admin/tenants + onboarding + pricing (Unit 30/32/33) | ~22 hr | ~13 hr | P0 20/32 |
| 57.28 | Ops Platform P0 4 (Unit 26/27/28/29 — incl 🔴 RBAC IAM Block B coord) | ~26 hr | ~16 hr | P0 24/32 |
| 57.29 | Ops Dashboards remaining P0 (Unit 8/9/10 — cost/sla/memory) | ~20 hr | ~12 hr | P0 27/32 |
| 57.30 | Misc P0 5 (Unit 40/41/45 + Bonus jit/cache) | ~33 hr | ~20 hr | P0 32/32 ✅ |
| 57.31 | P1 sweep (5 units) + P2 polish wave 1 (Unit 7/12) | ~26 hr | ~16 hr | P0+P1 done |
| 57.32 | P2 polish wave 2 (Unit 23/24/25 Sprint 57.19 drift) | ~11 hr | ~7 hr | P0+P1+P2 done ✅ |
| 57.33+ | P3 scope decisions (Unit 39 + 44) + bug-fix sweep | TBD | TBD | Phase 57.23+ epic closed |

**Σ Phase 57.23-57.32 commit hours**: ~153 hr across ~10 sprints (2.5 months at 1-week sprint pace).

### Mockup Cleanup Carryovers (Outside Page Rebuilds)

5 architecture-level carryovers identified across audit:
1. **AD-Brand-Primary-Color-Decision** (Sprint 57.18 carryover; Unit 1 forced decision) — oklch palette vs shadcn slate
2. **AD-Mockup-Card-Primitive-Phase58** (Unit 7+30+others reaffirmed) — custom `MockupCard` primitive with `.card-head/.card-body/.card-sub` variants
3. **AD-Mockup-Typography-Scale-Phase58** (Unit 7 + many others) — extend `tailwind.config.ts` with 11/11.5/12/12.5/13/13.5px micro-size scale
4. **AD-AuditLog-Route-Disambiguation-Phase58** (Unit 22) — remove top-level `/audit-log` dead stub OR redirect to nested
5. **AD-FeatureFlags-Route-Disambiguation-Phase58** (Unit 34) — global cross-tenant vs tenant-tab-only decision

### Total Phase 57.23+ Epic Estimate

- **Frontend Σ rebuild**: ~247 hr (P0 ~206 + P1 ~24 + P2 ~17)
- **Backend Σ greenfield**: ~50 hr (14 backend epics; ~3.5 hr avg)
- **Architecture cleanup**: ~10 hr (5 cross-cutting AD)
- **Phase 57.23-57.32 Σ commit (calibrated)**: **~153 hr across ~10 sprints**
- **2.5 months at 1-week sprint pace, OR 5 months at 2-week sprint pace**

### Phase 58 Stage 2 Coordination

P0 units with backend dependencies that span Phase 58 (Stage 2 / IAM Block B / SaaS billing):

| Phase 58 Stage 2 epic | Units affected | Coordinate sprint |
|----------------------|----------------|-------------------|
| **IAM Block B (RBAC + tenant-scoped policy)** | Unit 29 + Unit 31 Members tab | Backend pre-req Sprint 57.X (separate IAM execution) |
| **Stripe + Lago billing** | Unit 33 /pricing + Unit 31 Quotas tab | Buy-vs-build Phase 58 epic |
| **WorkOS multi-IdP enterprise SSO** | Unit 1 + Unit 31 SSO config | Phase 58 IAM backend |
| **GDPR erasure + Cat 12 audit chain** | Unit 31 Danger Zone + Unit 22 /audit-log | EU CRA / SOC 2 compliance Phase 58 |

**Phase 58 backend pre-req sprints (4 NEW epics)**: ~30-40 hr backend-only before frontend P0 units shippable
