# Next Phase 候選 (Phase 57.22+)

**Purpose**: Open items / pending decisions / carryover ADs accumulated from prior sprint retrospectives. Single-source for "what could be next sprint". CLAUDE.md / MEMORY.md no longer carry this list per §Sprint Closeout policy ([`.claude/rules/sprint-workflow.md`](../../.claude/rules/sprint-workflow.md)).

**Selection Rule**: User explicitly selects → draft plan kicks off Sprint XX.Y; otherwise items wait here indefinitely until selected or archived.

**Updated**: 2026-05-18 (Sprint 57.21 closeout — extracted from CLAUDE.md V2 Refactor Status table per REFACTOR-001 Step 3)

---

## 🔴 Top Candidates (User-Aligned Priority)

### 1. AD-ChatV2-Full-Mockup-Fidelity Phase-2

Multi-sprint epic continuation. Sprint 57.21 Phase-1 already shipped:
- Turn Block Model
- SessionList fixture
- Inspector 4-tab frame
- Composer visual scaffolding

**Phase-2 carryover ADs** (from Sprint 57.21 retro):
- AD-ChatV2-Memory-Block-Phase2
- AD-ChatV2-HITL-FourAction-Phase2
- AD-ChatV2-Composer-Richness-Phase2
- AD-ChatV2-Composer-Wire-Phase2
- AD-ChatV2-Inspector-{Trace, Memory, SubagentTree}-Phase2
- AD-ChatV2-SessionList-Backend
- AD-Cat12-SSE-Trace-Id-Phase2

**Mode**: Pick subset for Phase-2 first sprint depending on backend dependency ordering. Likely structural-rewrite mode → `frontend-mockup-direct-port` ratio ~1.0-1.2 predicted.

### 2. 🆕 AD-Mockup-Direct-Port-Round-2

NEW Sprint 57.20 Day 4 DRIFT-REPORT-ROUND-2 (16 R2 findings).

**Scope** — Token migration sweep for **8 remaining ship pages**:
- cost-dashboard / memory / verification / governance + 4 governance sub-routes / sla-dashboard / admin-tenants / tenant-settings

Plus:
- 3 overlay backend wiring
- R2-A 5 cosmetic Card visual polish

**Class**: Same `frontend-mockup-direct-port` 0.55 class likely.

### 3. AD-Mockup-Existing-Pages-Retrofit Tier 1

Sprint 57.19 US-F1 DRIFT-REPORT; partially closed Sprint 57.20 via `/overview` + `/chat-v2` token migration; **folds INTO Round-2 above**.

**Scope**: 9-page retrofit Tier 1 ~10.5 hr bottom-up = ~5.8 hr calibrated commit at NEW class `mockup-fidelity-retrofit` 0.55 1st app (HYBRID: cosmetic mechanical 0.45 + structural design 0.65 + closeout 0.80).

**5 priority pages**:
- cost-dashboard (3 hr)
- chat-v2 (3 hr)
- memory (2 hr)
- verification (2 hr)
- governance (1.5 hr)

**Tier 2**: ~5.5 hr → Sprint 57.21+
**Tier 3**: ~1 hr + Round 3 epic

---

## 🟡 Mockup-Page-Port Continuation

### 4. AD-Mockup-Page-X-Port Round 3 — Auth 4

Sprint 57.19 carryover. Pages:
- register / invite / mfa / expired

**Pairing**: IAM Block B (WorkOS SCIM/SAML/org-level RBAC) per 用戶 2026-05-16 Q3 alignment「前後端同 sprint」.

### 5. AD-Mockup-Page-X-Port Round 4 — Governance 3

Sprint 57.19 carryover. Pages:
- redaction / error-policy / audit-log (DRAFT → active promote)

**Pairing**: Cat 9 endpoint extensions.

---

## 🟢 Backend Wire Bundle

### 6. AD-Backend-Wire Bundle

Sprint 57.19 4 NEW ADs:
- Subagent-RealList-Phase58
- Loop-Session-Enrich-Phase58
- Overview-Backend-Wire
- Orchestrator-Backend-Wire

**Scope**: Backend persistence + aggregation for Operations 4 pages (current fixture/stub). Can pair with retrofit work.

### 7. 🆕 AD-CommandPalette-Backend-Wire

NEW Sprint 57.19 US-D1. Tenants + sessions groups currently fixture; wire Cat 1 sessions list + Cat 12 tenants index.

### 8. 🆕 AD-NotificationsPanel-Backend-Feed

NEW Sprint 57.19 US-D2. 6 mockup items local state; Cat 12 SSE/poll feed spec TBD.

### 9. 🆕 AD-UserMenu-Tenant-Switch

NEW Sprint 57.19 US-D3. Wire tenant switching paired with Round 2 WorkOS SCIM.

---

## 🛠️ Tooling / Infrastructure / Style

### 10. AD-Tailwind-v4-Config-Migration

Sprint 57.17 carryover. Full v4 idiomatic `@theme inline {}` block 取代 `@config "../tailwind.config.ts"` + 刪 legacy v3 config file. ~6-8 hr standalone sprint, same class `frontend-css-engine-hotfix`.

### 11. AD-Post-Hotfix-Token-Audit

NEW Sprint 57.17 contrast-ratio portion. **Folds INTO** AD-Mockup-Existing-Pages-Retrofit Tier 1 work (same shadcn slate base sub-AA pairs).

### 12. 🆕 AD-Brand-Primary-Color-Decision

Sprint 57.18 D-PRE-1. Partially actioned by Sprint 57.19 US-A1 mockup indigo; finalization decision pending.

### 13. 🆕 AD-Theme-Variant-Mechanism

Sprint 57.18 D-PRE-2.

### 14. 🆕 AD-Density-Variant-Mechanism

Sprint 57.18 D-PRE-3.

### 15. AD-CI-7-GHA-PR-Permission

Sprint 57.17 carryover. `playwright-e2e.yml:163-188` auto-PR-create blocked by repo setting.

### 16. AD-Lighthouse-Visual-Hard-Gate

Baselines reliable post-57.17; required CI check.

### 17. AD-Bundle-Size code-split

### 18. AD-i18n-Feature-Namespaces

### 19. AD-A11y-Structural-Nits

Sprint 57.16 carryover. `/chat-v2` 的 `heading-order` + duplicate `<main>` landmarks moderate/minor；`/auth/callback?error` `page-has-heading-one`.

---

## 🏢 Enterprise / SaaS Stage 2

### 20. IAM Block B Spike

~12-18 hr — WorkOS SCIM/SAML/org-level. Pairs with #4 Auth 4.

### 21. Tier 1 IaC + DR Drill

~15-20 hr.

### 22. SOC 2 + SBOM

~12-15 hr.

---

## 🟣 Sprint 57.23 Auth Page Rebuild Carryovers (NEW 2026-05-18)

7 ADs from Sprint 57.23 AD-Auth-Page-Full-Rebuild-Round-2 closeout. Frontend rebuild shipped 8/8 USs with stub-501 demo banners; backend wiring deferred to Phase 58+ IAM Block B/C per Q2 frontend-only decision.

### 23. AD-Auth-Register-Backend-IAM-Block-B-Phase58
`POST /api/v1/tenants/register` real implementation. Currently 501 stub. Frontend `/auth/register` 4-step wizard fully shipped + i18n + Vitest 5 cases. Phase 58+ IAM Block B scope.

### 24. AD-Auth-Invite-Backend-IAM-Block-B-Phase58
`GET /api/v1/invites/:token` (metadata) + `POST /api/v1/invites/:token/accept`. Currently 501 stubs; frontend falls back to fixture metadata silently for GET, surfaces explicit error for POST. Frontend `/auth/invite/:token` shipped + Vitest 4 cases. Phase 58+ IAM Block B scope.

### 25. AD-Auth-MFA-Backend-IAM-Block-C-Phase58
`POST /api/v1/mfa/verify` + TOTP secret enrollment + WebAuthn credential registration backend. Currently 501 stub. Frontend `/auth/mfa` Roll-own UI shipped (TOTP 6-digit grid + WebAuthn conic ring + Simulate button) + Vitest 7 cases. Phase 58+ IAM Block C scope.

### 26. AD-Auth-MFA-Recovery-Page-Phase58
`/auth/mfa/recovery` page wire — currently displayed as `<span pointer-events-none>` with tooltip "Recovery flow pending Phase 58+ IAM Block C". Backend recovery-code generation + verification. Phase 58+ IAM Block C scope.

### 27. AD-Auth-Callback-Loading-UX-Phase58
Replace static 3-step `setTimeout` (800/1800/2800ms) with real backend SSE per-step events when WorkOS OIDC callback wiring exists. Frontend already has 3-step UI + parallel-bootstrap + min-2800ms-enforce mechanism. Phase 58+ IAM Block B scope.

### 28. AD-WorkOS-Multi-IdP-Phase58
Wire actual SAML / Microsoft / Google SSO via WorkOS. Currently 3 buttons disabled with "Enterprise SSO via WorkOS roadmap" tooltip per mockup. Backend WorkOS Multi-IdP integration. Phase 58+ IAM Block B scope. (Existed pre-57.23 as design intent; now actively blocks Sprint 57.23 login button enablement.)

### 29. AD-Sprint-57-23-Playwright-MCP-Visual-Verify-Followup
Re-run Playwright MCP visual pair-verify on Sprint 57.23 12 page-states. Day 4 closeout encountered stuck browser state from prior Sprint 57.22 session (`Error: Browser is already in use ... use --isolated`). Closure via code-level audit + Sprint 57.22 baseline + visual-regression CI mechanism. Re-run in future session with fresh browser instance. **Low priority** — line-by-line port discipline + DRIFT-REPORT verdicts (all PARITY or COSMETIC; 0 STRUCTURAL/FUNCTIONAL) already cover fidelity gate.

### 30. AD-I18n-Symmetric-Keys-Lint-Phase58
Implement automated symmetric-keys lint at `frontend/tests/unit/i18n/` that runs `jq paths(scalars)` diff between en/<namespace>.json and zh-TW/<namespace>.json on every PR. Sprint 57.23 verified manually for `auth.json`; this AD generalizes for `chat-v2.json` / `governance.json` / `tenant-settings.json` etc. ~2-3 hr.

---

## Maintenance Notes

- New carryover ADs from each sprint retrospective should be **appended here**, NOT to CLAUDE.md table cells (per §Sprint Closeout policy).
- When a candidate becomes the selected next sprint, leave the entry marked `→ Sprint XX.Y` until that sprint closes; then move to "Closed" section or delete.
- Cross-references: see `memory/MEMORY.md` index + per-sprint memory subfile + retrospective.md for sprint-by-sprint detail.

---

## Modification History

- 2026-05-18: Sprint 57.23 Day 4 closeout — +8 ADs (#23-#30) Auth Page Rebuild Round 2 carryovers (Phase 58+ IAM Block B/C + Playwright MCP followup + i18n lint)
- 2026-05-18: Initial creation (REFACTOR-001 Step 3; extracted from CLAUDE.md V2 Refactor Status table 20-bullet `Next Phase 候選` row per §Sprint Closeout policy)
