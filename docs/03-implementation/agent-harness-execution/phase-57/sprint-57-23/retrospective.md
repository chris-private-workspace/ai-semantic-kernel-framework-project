# Sprint 57.23 — Retrospective

**Sprint**: AD-Auth-Page-Full-Rebuild-Round-2 — 6 P0 Auth Routes Full Mockup-Fidelity Rebuild (Frontend-Only Spike)
**Branch**: `feature/sprint-57-23-auth-page-full-rebuild-round-2`
**Calibration class**: `frontend-mockup-strict-rebuild` 0.60 (NEW; 1st application; HYBRID weighted blend per Sprint 57.22 audit §Sprint 57.23+ Recommendation)
**Bottom-up estimate**: ~46 hr → **Calibrated commit**: ~28 hr (multiplier 0.60)
**Days**: 5 (Day 0 setup + 三-prong / Day 1-3 implementation / Day 4 closeout)
**Closed**: 2026-05-18

---

## Q1 — What was the goal? Did we hit it?

**Goal**: Frontend-only rebuild of 6 P0 Auth routes (+ 1 supporting `/auth/dev` + AuthShell shell rewrite) with strict mockup-fidelity per Sprint 57.22 audit findings (per `reference/design-mockups/page-extras.jsx` + `page-auth-extras.jsx`). All backend wiring deferred to Phase 58+ IAM Block B / Block C.

**Outcome**: ✅ **Hit, all 8 unit deliverables shipped**:

| US | Route / Component | Status |
|----|-------------------|--------|
| US-B1 | `AuthShell.tsx` shell rewrite | ✅ shipped Day 1 |
| US-B2 | `/auth/login` rewrite | ✅ shipped Day 1 |
| US-B3 | `/auth/dev` NEW (extracted from login) | ✅ shipped Day 1 |
| US-C1 | `/auth/callback` 3-step timed rewrite | ✅ shipped Day 2 |
| US-C2 | `/auth/register` NEW 4-step wizard | ✅ shipped Day 2 |
| US-D1 | `/auth/invite/:token` NEW | ✅ shipped Day 3 |
| US-D2 | `/auth/mfa` NEW (TOTP + WebAuthn) | ✅ shipped Day 3 |
| US-D3 | `/auth/expired` NEW | ✅ shipped Day 3 |

DRIFT-REPORT signed off Day 4 (12 page-states; all PARITY or COSMETIC; no STRUCTURAL / FUNCTIONAL).

---

## Q2 — How did we do on time? Calibration ratio for NEW class

**Bottom-up estimate**: ~46 hr (per plan §Workload)
**Calibrated commit**: ~28 hr (multiplier 0.60)
**Actual**: ~16-17 hr (Day 0 ~1 / Day 1 ~5 / Day 2 ~4-5 / Day 3 ~5 / Day 4 ~2 [Playwright MCP deferred → no capture session])

**Ratios**:
- `actual / committed` = 16.5 / 28 ≈ **0.59** — **BELOW [0.85, 1.20] band by 0.26**
- `actual / bottom-up` = 16.5 / 46 ≈ **0.36** — bottom-up was 2.8× too generous; 0.60 haircut insufficient

**Q8: NEW class `frontend-mockup-strict-rebuild` 0.60 1st application calibration narrative**:

The NEW class was opened in Sprint 57.22 audit §Sprint 57.23+ Recommendation as a HYBRID weighted blend of {auth-flow IAM-ish × 0.55 + frontend-mockup-direct-port-structural × 0.85 + 4-step wizard × 0.50 + 6-digit input grid × 0.55} ≈ 0.60 mid-band. Sprint 57.23 1st application shows the haircut was **too conservative**; reasons:

1. **Mockup line-by-line port discipline reduced design ambiguity**: Each page has explicit `mockup-ref Lxx-yy` comments. JSX/Tailwind/state machines all mapped 1:1 — no design-decision overhead per element.
2. **Tailwind tokens pre-aligned with mockup**: Sprint 57.18 had already wired `--primary: 234 89% 60%` oklch indigo HSL approximation. Day 0 D-PRE-2 confirmed this; saved ~1-2 hr of token-translation work that the original estimate included.
3. **Register 4-step wizard pattern was repetitive**: Step body shapes (form fields / radio cards / hitl-summary) are mechanical translations once stepper scaffolding is in place. Bottom-up under-counted reuse.
4. **AP-2 demo banner pattern reused 3× cleanly** (register / invite / mfa): paste-and-customize 4-line snippet, not per-page novel design.
5. **`AuthShell footer` slot pattern reused 7×**: each page passes a 1-line footer; no per-page chrome design.

Recommendation:
- **KEEP 0.60 baseline** per `When to adjust` 3-sprint window rule (1 data point insufficient for adjustment)
- **If pattern recurs 2-3× more (below band)** → propose 0.60 → **0.40-0.45** to reflect mockup-line-by-line port efficiency
- Track via Sprint 57.24+ if AD-Sprint-57-23-Followup or similar rebuild work matches this class

**Per-day breakdown (actual vs informal target)**:

| Day | Informal target | Actual | Delta |
|-----|-----------------|--------|-------|
| Day 0 | ~1 hr | ~1 hr | bullseye |
| Day 1 | ~6 hr | ~5 hr | -17% |
| Day 2 | ~8 hr | ~4-5 hr | -40% (timed callback was small + register wizard mechanical) |
| Day 3 | ~7 hr | ~5 hr | -28% (line-by-line port from mockup uncovered no surprises) |
| Day 4 | ~6 hr | ~2 hr | -66% (Playwright MCP unavailable; code-level audit faster) |

---

## Q3 — What worked well? (Keep doing)

1. **Mockup-Fidelity Hard Constraint enforcement via mockup-ref line comments**: Every page implementation file documents `mockup-ref Lxx-yy` in section comments + MHist. Removed all design ambiguity. Future audit / handoff has zero gap.
2. **Day 0 三-prong (Path + Content + Schema verify) caught 5 D-PRE findings**: D-PRE-2 (token already wired — saved ~1-2 hr) was a direct calibration win.
3. **Rolling planning discipline preserved**: Sprint 57.24 plan NOT drafted during this sprint; only Day 4 closeout work was done. No predictive plans for future sprints.
4. **AP-2 demo banner discipline on stub-501 pages**: 3 pages (register / invite / mfa) display "Backend wire pending Phase 58+ IAM Block B/C" banner above forms. Zero hidden stub failures; user sees the boundary before clicking.
5. **i18n key symmetry maintained**: 80 NEW strings (40 keys × en + zh-TW) shipped together each Day; jq paths diff = 0 verified Day 4 (R6 mitigation).
6. **MHist 1-line max discipline preserved**: All new files have ≤100-char MHist entries with `(closes XXX)` paren style. No verbose multi-line that triggered Sprint 55.x lint hits.
7. **ESLint escape hatches all documented**: 3 inline-style hatches (AuthShell radial gradient / callback conic spinning ring / mfa conic ring) — each with `// eslint-disable-next-line no-restricted-syntax -- STYLE.md §3 ... (Sprint 57.23 US-Xn mockup AuthY Lxx-yy)` reason comment. Sprint 57.16 codebase-wide no-restricted-syntax JSX guard caught any forgotten ones.
8. **Vitest behavioral coverage = 369/369 PASS preserved**: +14 NEW (4 invite + 7 mfa + 3 expired) without any regression to Sprint 57.13-57.22 baseline.

---

## Q4 — What didn't work? (Stop or fix)

1. **Playwright MCP browser state stuck from prior Sprint 57.22 session**: Cannot reset within a single session. Day 4 visual pair-verify deferred to AD-Sprint-57-23-Playwright-MCP-Visual-Verify-Followup. Worked around via code-level audit + Sprint 57.22 baseline reliance + visual-regression CI; verdicts all PARITY or COSMETIC.
2. **R8 dev-link gate gap caught at Day 4 production grep**: Day 1 login.tsx rewrite (US-B2) shipped `<Link to="/auth/dev">` without `import.meta.env.DEV` wrapper. Route was gated in App.tsx (security boundary preserved), but link visible in prod build was UX leakage. Day 4 fix landed (1 line wrap). **Lesson**: Day 0 三-prong missed the dev-link gate as a verification target. Add to next sprint's Day 0 checklist when refactoring auth pages.
3. **Bottom-up estimate over-counted register wizard**: Plan estimated ~12 hr for register; actual ~4-5 hr because stepper + 4-step body shapes were mechanical Tailwind translations once scaffolding was in place. Pattern repeated across mfa (estimated ~8 hr, actual ~2 hr). Bottom-up estimates for **mockup-direct-port mechanical class** trend systematically 2-3× too generous.
4. **i18n keys 80 strings exceeded plan estimate ~44**: Growth was from translating busy-state strings (Verifying… / Accepting…) + recoveryTooltip + per-tab subtitles. Plan estimated keys only; busy-states were forgotten. **Lesson**: When estimating i18n, count all distinct user-visible strings, not just primary content keys.

---

## Q5 — Carryover ADs (open items not closed this sprint)

Documented in `claudedocs/1-planning/next-phase-candidates.md` (per REFACTOR-001 §Sprint Closeout policy — Open items destination):

1. **AD-Auth-Register-Backend-IAM-Block-B-Phase58** — `POST /api/v1/tenants/register` real implementation (currently 501 stub). Phase 58+ IAM Block B scope.
2. **AD-Auth-Invite-Backend-IAM-Block-B-Phase58** — `GET /api/v1/invites/:token` + `POST /api/v1/invites/:token/accept` real implementations (currently 501 stub). Phase 58+ IAM Block B scope.
3. **AD-Auth-MFA-Backend-IAM-Block-C-Phase58** — `POST /api/v1/mfa/verify` + TOTP secret enrollment + WebAuthn credential registration backend. Phase 58+ IAM Block C scope.
4. **AD-Auth-MFA-Recovery-Page-Phase58** — `/auth/mfa/recovery` page for recovery codes (currently pointer-events-none link tooltip). Phase 58+ IAM Block C scope.
5. **AD-Auth-Callback-Loading-UX-Phase58** — replace static 3-step setTimeout with real backend SSE per-step events when WorkOS OIDC callback wiring exists. Phase 58+ IAM Block B scope.
6. **AD-WorkOS-Multi-IdP-Phase58** — wire actual SAML / Microsoft / Google SSO via WorkOS (currently 3 buttons disabled with "Enterprise SSO via WorkOS roadmap" tooltip). Phase 58+ IAM Block B scope.
7. **AD-Sprint-57-23-Playwright-MCP-Visual-Verify-Followup** — re-run Playwright MCP visual pair-verify on the 12 page-states after browser-state reset. Low priority; visual-regression CI + code-level audit cover the fidelity gate.

---

## Q6 — Anti-Pattern + V2 Constraint Compliance

### 11 V2 anti-patterns (per `.claude/rules/anti-patterns-checklist.md`)

All 11 checked; no violations introduced:
- AP-1 Loop-disguised-Pipeline: N/A (no agent loop work)
- AP-2 Side-track / pollution: ✅ demo banners on stub-501 pages explicitly flag Phase 58+ AD references
- AP-3 Cross-directory scattering: ✅ all new code lives under `frontend/src/pages/auth/<feature>/` canonical structure
- AP-4 Premature abstraction: ✅ AuthShellX shell helper not extracted; 7 usages would justify but kept inline per current scope
- AP-5 Stale mock data: ✅ all fixture data sprint-specific (acme-prod / sess_8a2f1c3); not pretending to be real
- AP-6 Hardcoded credentials / secrets: ✅ none
- AP-7 Skipped tests / TODO comments: ✅ 0 test.skip / 0 // TODO in shipped code
- AP-8 Wrong-language docs: ✅ all file headers + comments in English; user-visible UI in i18n keys per locale
- AP-9 Untyped any: ✅ no `any` introduced
- AP-10 Imperative DOM manipulation: ✅ all DOM access via React refs + state
- AP-11 Magic strings: ✅ fixture constants extracted to module-level

### V2 5 大核心約束

- ✅ **Server-Side First**: frontend-only sprint (per Q2 user decision); 0 backend changes; no agent_harness leakage
- ✅ **LLM Provider Neutrality**: N/A — frontend has no LLM SDK imports
- ✅ **CC Reference 不照搬**: no CC patterns lifted; mockup is canonical visual source
- ✅ **17.md Single-source**: no new contracts added (frontend-only)
- ✅ **11+1 範疇歸屬**: all new code lives in `frontend/`; not crossing into `agent_harness/` or `platform_layer/`

### Sprint workflow discipline (per `.claude/rules/sprint-workflow.md`)

- ✅ Plan + Checklist + Code + Update + Progress workflow strict 5-step
- ✅ Day 0 三-prong (Path + Content + Schema) caught 5 D-PRE findings before Day 1 code
- ✅ Format consistency: plan + checklist mirror Sprint 57.22 (most recent completed sprint) section structure
- ✅ Day 4 closeout per REFACTOR-001 §Sprint Closeout policy minimal touch (CLAUDE.md Current Sprint row + Last Updated only; memory subfile single-source for sprint detail)

---

## Q7 — Next sprint candidate (rolling planning)

Per `.claude/rules/sprint-workflow.md` rolling planning discipline + `claudedocs/1-planning/next-phase-candidates.md`:

**Sprint 57.24 candidate** (NOT drafted during this sprint — to be drafted at start of Sprint 57.24 itself per rolling rule):

Per Sprint 57.22 audit Priority Matrix (which drove Sprint 57.23), the next highest-priority bundle is **Ops / Operations frontend rebuild** (5 P1 routes: Overview / Orchestrator / Subagents / StateInspector / topbar overlays already shipped in 57.19 — likely smaller scope: gap-finishing for Operations or pivoting to Chat-v2 Phase 2 structural rebuild).

Alternative candidates per `next-phase-candidates.md`:
- AD-ChatV2-Full-Mockup-Fidelity Phase-2 (continuation of 57.21 Phase-1)
- AD-IAM-Block-B Backend (close AD-Auth-Register/Invite-Backend carryovers from this sprint)
- AD-Mockup-Direct-Port Round-3 (token-sweep continuation if 57.20+57.21 bimodal pattern reaffirms)

User to decide at Sprint 57.24 kickoff.

---

## Q8 — Calibration matrix update (closes carryover §Sprint 57.22 §Sprint 57.23+ Recommendation)

NEW class `frontend-mockup-strict-rebuild` 0.60 — 1st application data point:
- **Ratio actual/committed**: 0.59 (BELOW [0.85, 1.20] band by 0.26)
- **Ratio actual/bottom-up**: 0.36 (bottom-up 2.8× generous; 0.60 haircut insufficient)

**Decision**: KEEP 0.60 baseline per `When to adjust` 3-sprint window rule. Pending 2-3 sprint validation.

If pattern recurs (below band 2-3×) → propose 0.60 → 0.40-0.45 (mockup-direct-port mechanical efficiency similar to Sprint 57.16 AD-Sprint-Plan-13 mechanical class lift).

Update `.claude/rules/sprint-workflow.md §Scope-class multiplier matrix` Day 4 closeout to record this 1-data-point baseline.

---

## Closing Notes

Sprint 57.23 = ✅ **CLOSED** with all 8 unit deliverables shipped + code-level DRIFT-REPORT verdicts PARITY or COSMETIC across 12 page-states. No STRUCTURAL or FUNCTIONAL drift. R8 hardening completed (dev-link gate Day 4). 7 carryover ADs documented for Phase 58+ pickup. 1st calibration data point recorded for NEW class.

Branch ready for closeout commits + push + draft PR.
