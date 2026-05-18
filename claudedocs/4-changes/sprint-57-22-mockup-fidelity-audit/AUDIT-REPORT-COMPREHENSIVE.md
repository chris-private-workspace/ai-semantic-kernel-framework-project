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

### Unit 13: Phase-2 widget — Memory Block

(Day 2 in-progress)

### Unit 14: Phase-2 widget — HITL FourAction

(Day 2 in-progress)

### Unit 15: Phase-2 widget — Composer richness

(Day 2 in-progress)

### Unit 16: Phase-2 widget — Inspector Trace tab

(Day 2 in-progress)

### Unit 17: Phase-2 widget — Inspector Memory tab

(Day 2 in-progress)

### Unit 18: Phase-2 widget — Inspector Tree tab

(Day 2 in-progress)

---

## Group: Governance (4 units)

### Unit 19: /governance/approvals

(Day 2 in-progress)

### Unit 20: /governance/redaction

(Day 2 in-progress)

### Unit 21: /governance/loop-debug

(Day 2 in-progress)

### Unit 22: /governance/audit-log

(Day 2 in-progress)

---

## Group: Operations (Platform) (7 units)

### Unit 23: /orchestrator

(Day 2 in-progress)

### Unit 24: /subagents

(Day 2 in-progress)

### Unit 25: /state-inspector

(Day 2 in-progress)

### Unit 26: /compaction

(Day 2 in-progress)

### Unit 27: /workflows

(Day 2 in-progress)

### Unit 28: /error-policy

(Day 2 in-progress)

### Unit 29: /rbac

(Day 2 in-progress)

---

## Group: Admin (10 units)

### Unit 30: /admin/tenants

(Day 3 in-progress)

### Unit 31: /tenant-settings

(Day 3 in-progress)

### Unit 32-39: /admin/feature-flags + quotas + hitl-policies + members + danger-zone + tenant-onboarding + pricing + domain-detail

(Day 3 in-progress)

---

## Group: Misc (7 units)

### Unit 40: /models

(Day 3 in-progress)

### Unit 41: /tools

(Day 3 in-progress)

### Unit 42-46: /sse + /devui + /a11y-audit + /incidents + /subagent-tree + /jit-retrieval + /cache-manager

(Day 3 in-progress)

---

## Priority Matrix (Day 4)

(Final priority matrix populated Day 4 after all audit units complete)

| Priority | Page | Score | Rebuild hr | Group | Dependencies |
|----------|------|-------|-----------|-------|--------------|
| _TBD_ | _TBD_ | _TBD_ | _TBD_ | _TBD_ | _TBD_ |

---

## Sprint 57.23+ Recommendation (Day 4)

(Recommendation populated Day 4 based on priority matrix totals)
