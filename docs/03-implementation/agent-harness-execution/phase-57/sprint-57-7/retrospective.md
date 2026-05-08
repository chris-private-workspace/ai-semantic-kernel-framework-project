# Sprint 57.7 Retrospective — IAM Foundation + Frontend Foundation 1/N spike

**Sprint**: 57.7 — **Phase 57+ SaaS Frontend 4/N (cost-dashboard now AppShell-compliant)**
**Period**: 2026-05-09 ~ 2026-05-10 (Day 0-3 production code; Day 4 closeout)
**Branch**: `feature/sprint-57-7-iam-frontend-foundation` (7 commits ahead of main `d485b42d`)
**PR**: pending Day 4.5 (open + CI green + solo-dev squash merge)
**Sprint type**: HYBRID 0.60 1st application (per AD-Sprint-Plan-9 NEW class)

---

## Q1. What went well

### Q1.1 Day 0 三-prong 探勘 found 2 critical scope-saving D-findings

- **D8 (Day 0 schema verify)**: `users.external_id` column already exists pre-Sprint 57.7 → **saved Alembic 0017 migration scope** (~1-2 hr). Path verify (Prong 1) caught this before Day 1 code start.
- **D19 (Day 3 探勘 of chat router)**: AD-Reality-3a "blocked by missing user_id JWT extraction infra" assumption was **wrong** — `TenantContextMiddleware.dispatch` already populated `request.state.user_id` since Sprint 49.3 (3 sprint cycles ago). Single-line `Depends(get_current_user_id)` fix → **saved ~3-5 hr** of feared "infra design + maybe Alembic" scope.

**Combined ROI**: ~30-45 min Day 0/Day 3 探勘 cost prevented ~5-7 hr of mid-sprint rework. Validates AD-Plan-1+2+3+4 promotion to permanent §Step 2.5 rule.

### Q1.2 Vendor matrix process produced honest, specific decision

- 4-vendor evaluation (WorkOS / Clerk / Auth0 / Supabase) with 17-row capability comparison + cost projection 3 years out + 3 specific rejection rationale (NOT "best practice" hand-wave per AP-2)
- Intermediate artifact `iam-vendor-matrix.md` (160 lines) folded into `20-iam-deep-dive.md` §1 design note
- WorkOS chosen for B2B SCIM + APAC presence + cost-predictable + clear off-ramp — full reasoning auditable

### Q1.3 Foundation install (US-B1) Day 2 enabled fast Tier 3 follow-through

- Tailwind 4 + shadcn/ui + TanStack Query + RHF + Zod + Sonner + react-error-boundary + lucide-react + 12 deps installed + tailwind.config.ts + postcss.config.cjs + components.json + index.css with shadcn CSS variables + lib/utils.ts cn() helper — all Day 2 PM
- Tier 3 Day 3 PM (~2 hr actual vs ~5 hr est) — 60% under because foundation already in place

### Q1.4 7 USs delivered in 4-day session window vs 5-day plan

- All 7 USs (A1+A2+A3+B1+B2+B3+R1) closed by Day 3 PM; Day 4 = pure ceremony (design note + retro + PR + memory)
- Achieved via 3 disciplined Tier waves (Tier 1 unblocks Tier 2; Tier 3 independent frontend) — per V2 紀律 surgical change scope
- ALL 6 commits pushed clean (no force-push, no destructive rebase)

### Q1.5 Test discipline preserved (0 deletion, 0 skip)

- Vitest 35 → 41 (+6 ⏫ +20% over plan target +5)
- Pytest 1602 → 1622 (+20)
- Playwright 23 → 23 (regression sentinel green throughout)
- Existing chat router 65 unit tests required dep override + autouse env fixture additions — preserved via documented test pattern (per `.claude/rules/testing.md` §Module-level Singleton Reset extension)

---

## Q2. What didn't go well + Calibration ratio

### Q2.1 Calibration ratio under-estimated (sustained pattern)

- **Plan**: bottom-up est ~26-33 hr / committed ~18 hr (HYBRID 0.60 weighted blend: IAM × 0.60 + Frontend × 0.65 + Reality × 0.50 + closeout × 0.80)
- **Actual** (Day 0-3): ~13.5 hr / committed 18 hr → **ratio ~0.75**
- **Day 4 projection**: + ~3 hr (design note ~1.5 + retro ~0.5 + memory ~0.25 + doc syncs ~0.5 + PR ~0.25) → **final ~16.5 hr / 18 hr = ratio ~0.92** ✅ likely **in band [0.85, 1.20]**

**Pattern**: 4-sprint moving window (57.3=0.57, 57.4=0.42, 57.5=1.04, 57.6=0.54) shows mixed-pattern-reuse classification consistently under-estimates. Sprint 57.7 NEW HYBRID class projected ~0.92 fits but lands at lower edge — indicates **HYBRID 0.60 may be marginally too high** for the realistic execution speed.

**AD-Sprint-Plan-9 update proposal** (Day 4 retro Q2 evidence):
- 1-data-point baseline: HYBRID 0.60 → projected ~0.92 (in band)
- **KEEP 0.60 baseline this sprint** per `When to adjust` rule (3-sprint window required)
- Re-evaluate after 2-3 more HYBRID-class sprints

### Q2.2 Existing chat router unit tests required mid-sprint refactoring

- Adding `Depends(get_current_user_id)` to `chat()` broke 7 existing chat router tests (401 instead of 200) because their `app` fixture only overrode `get_current_tenant`
- Required mid-Tier-2 fix: NEW `DEFAULT_USER_ID` const + `dependency_overrides[get_current_user_id]` in app fixture + autouse env fixture disabling 3 observers (audit + sessions + tool_calls)
- Fix took ~15 min but interrupted flow; could have been pre-empted by Day 0 探勘 reading existing test fixture pattern before adding new Depends

**Lesson**: Day 0 探勘 should grep existing test fixtures for any new `Depends()` candidate ABCs before locking US scope. Add to AD-Plan-3 future iteration.

### Q2.3 typecheck pre-existing failure surfaced during build verify

- `npm run typecheck` fails with TS6310 on `tsconfig.node.json` emit/noEmit conflict
- Verified pre-existing via stash test (failure exists without Sprint 57.7 changes)
- `npm run build` (which runs `tsc -b && vite build`) succeeds → build pipeline unaffected
- D24 logged as Phase 58+ AD candidate (tsconfig fix; 1-line change estimated)

---

## Q3. What we learned

### Q3.1 Hosted vendor route validation (WorkOS path proven)

- `workos.AsyncWorkOSClient.user_management.{get_authorization_url, authenticate_with_code, get_logout_url}` API surface confirmed in Day 3 Tier 1 via `inspect.signature` REPL exploration
- Modern `user_management` API supersedes legacy `sso` for new hosted login integrations (no per-org connection_id pre-config required)
- `provider="authkit"` routes to WorkOS AuthKit hosted UX — cleanest spike path

### Q3.2 Frontend foundation install drove unexpected ROI

- Tailwind 4 + shadcn boilerplate often perceived as "heavy install" — actual time: ~30 min Day 2 PM
- Day 3 Tier 3 leveraged install: AppShell + ThemeProvider + ErrorBoundary written in ~30 min combined; cost-dashboard migrate ~20 min
- Net effect: 1 hr foundation install enables ~3-5 hr ongoing migration savings per page (estimate validates Phase 58.2+ Frontend Pages 11 batch ROI)

### Q3.3 「探勘 first, code second」discipline pays compound returns

- D8 (Day 0) + D19 (Day 3) + D24 (typecheck pre-existing) — each saved 1-5 hr of feared scope
- Pattern: assumption from prior sprint progress notes can become incorrect over time as code evolves; verify before committing to plan revision
- Fold-in: AD-Plan-1+2+3+4 promotion to permanent §Step 2.5 rule already done Sprint 57.1; this sprint validates 5+ months of compound usefulness

### Q3.4 Vendor SDK exploration via REPL inspect saves planning hours

- Direct `python -c "import inspect; print(inspect.signature(...))"` to discover sync vs async + parameter shapes took ~5 min; reading workos docs would have taken ~30 min
- Pattern reusable for any Python vendor SDK eval — add to general toolkit

---

## Q4. Audit Debt deferred

### Q4.1 Sprint 57.7 NEW deferred items (10 carry-forward)

| AD ID | Description | Estimated next sprint scope |
|-------|-------------|------------------------------|
| AD-Reality-3c | guardrail_audit observer in chat router | ~2-3 hr Phase 58+ |
| AD-Reality-3d | verification_audit observer in chat router | ~2-3 hr Phase 58+ |
| AD-IAM-SAML | Real SAML 2.0 connection setup | ~3-5 hr Phase 58+ when first $50K+ ACV deal |
| AD-IAM-MFA | TOTP enrollment + challenge flow | ~3-5 hr Phase 58+ |
| AD-IAM-RefreshToken | Refresh token rotation | ~2-3 hr Phase 58+ |
| AD-IAM-SCIM | Directory sync auto-provisioning | ~5-8 hr Phase 58+ |
| AD-Frontend-AuthUX | Login/callback page polish + sign-up + forgot pw | ~5-8 hr Phase 58.2+ Frontend Pages 11 |
| AD-Frontend-Sentry | Browser error tracking SDK in AppErrorBoundary | ~2-3 hr Phase 58.2+ Tier 1 |
| AD-RBAC-FullDBOnly | 100+ test fixture retrofit + remove opt-in env flag | ~5-8 hr Phase 58+ |
| AD-Frontend-Tsconfig | Fix TS6310 on `tsconfig.node.json` emit conflict (D24) | ~30 min Phase 58+ |
| AD-Cost-Dashboard-UseQuery | Migrate `useCostStore` to TanStack Query (D23) | ~2-3 hr Phase 58.2+ |
| AD-Cost-Dashboard-ChildrenTailwind | MonthPicker + CostBreakdownTable inline style → Tailwind (D25) | ~2-3 hr Phase 58.2+ batch |
| AD-Plan-3-Test-Fixture-Grep | AD-Plan-3 Day 0 探勘 to also grep existing test fixtures for new Depends candidates (Q2.2) | meta-rule iteration; ~1 hr fold-in to sprint-workflow.md §Step 2.5 |

### Q4.2 Sprint 57.7 closes (4 ADs)

| AD ID | Closure mechanism |
|-------|------------------|
| AD-Reality-3a | sessions row INSERT via SessionRepository + chat router pre-stream observer (US-R1) |
| AD-Reality-3b | tool_calls row INSERT via ToolCallRepository + chat router ToolCallExecuted observer (US-R1) |
| AD-Plan-5 | constraint-level schema verify (D8 Day 0 — `users.external_id` exists confirmation) |
| Tier 0 #5 (gap-analysis) | DB-backed RBAC RBACManager + hybrid path opt-in (US-A3) |

---

## Q5. Next steps + Phase 57.8+ direction proposal

### Q5.1 Per gap-analysis §6 adjusted roadmap candidates (NOT pre-committing per rolling planning 紀律)

- **(a) Phase 57.8 SOC 2 Readiness + SBOM Supply Chain spike** (~12-15 hr; Block C + D; EU CRA 2026 Sep deadline)
- **(b) Phase 57.8 Status Page + APAC Compliance spike** (~10-12 hr; Block E + F; target market Taiwan/HK mandatory)
- **(c) Phase 58.0+ Tier 1 IaC + DR drill** (~15-20 hr; production launch readiness)
- **(d) Pivot to existing Phase 57.x feature ship** (chat-v2 / governance / verification real ship now that auth working)
- **(e) Pivot to Frontend Pages 11** (User Profile / MFA Settings / Billing / Onboarding wizard / etc — Phase 58.2+ batch)

### Q5.2 Recommendation if pressed (NOT a commitment)

(a) SOC 2 + SBOM has hard deadline (EU CRA 2026 Sep); (b) Status Page can defer 1-2 sprints. (c) Tier 1 production launch needs real Azure provisioning Day 0 探勘 first. (d) feature ship requires user direction on which surface (chat-v2 / governance / verification all 3 are real backend + placeholder frontend).

**Direction question for user**: see Day 4.6 interaction.

---

## Q6. Solo-dev policy validation

- Branch protection `enforce_admins=true` + `review_count=0` (since Sprint 53.2 permanent solo-dev policy) — held throughout Sprint 57.7
- 5 active CI checks (backend-ci + frontend-ci + V2-Lint + Frontend E2E chromium + paths-filter workaround) expected to pass on PR open
- No admin-bypass attempts; no destructive rebases; clean linear commit history (6 forward commits)

---

## Q7. 8-Point Quality Gate self-grade — Design Note `20-iam-deep-dive.md`

| # | Gate | Pass | Evidence |
|---|------|------|----------|
| 1 | Section header 對應 spike user story | ✅ | §2.1 "OIDC Hosted Login Flow (US-A2)" + §2.4 "DB-Backed RBAC (US-A3)" + §2.5 "Sessions + ToolCalls Observer (US-R1)" |
| 2 | 每個技術 claim 有 file:line | ✅ | All §2.x include `oidc.py:L132` / `auth.py:L142` / `rbac.py` / `chat/router.py:~L210` references with grep-able class.method names |
| 3 | Decision rationale 含比較矩陣 | ✅ | §1 4-vendor matrix (17 rows) + 3 specific rejection rationale + chosen-reason 1.1 |
| 4 | Verification command (reproducible) | ✅ | Each §2.x has `pytest ... -v` reproducible command; §2.1=7 tests; §2.2=12 tests; §2.4=7 tests; §2.5=71 tests |
| 5 | Test fixture reference | ✅ | Each §2.x ends with explicit fixture description (AsyncMock + MagicMock + monkeypatch.setenv patterns) |
| 6 | Open invariant 明確分界 | ✅ | §4 lists 12 explicit deferred items with NOT-verified label; NO smuggling deferred into §2 |
| 7 | Rollback / fallback 路徑 | ✅ | §5 lists 4 distinct rollback paths (vendor swap / OIDC revert / providers revert / env flag disable) with effort estimates |
| 8 | Cross-reference 17.md single-source | ✅ | §3 explicitly states "None added" + verifies via grep `agent_harness/_contracts/` 0 new files |

**Verified ratio estimate**: ≥ 95% (only §4 deferred items NOT verified by definition; all §2 invariants have file:line + pytest reproduce + test fixture)

**Reviewer pass**: pending user Day 4.5 interaction (per checklist 4.1 last bullet)

---

## Sprint 57.7 Closure Summary

✅ **All 7 USs delivered** (US-A1 + A2 backend + frontend + A3 + B1 + B2 + B3 + R1)
✅ **AD-Reality-3a + 3b + Tier 0 #5 + AD-Plan-5 closed** (4 ADs)
✅ **Phase 57+ SaaS Frontend counter advances 3/N → 4/N** (cost-dashboard now AppShell-compliant)
✅ **V2 22/22 + Phase 56-58 SaaS Stage 1 3/3 unchanged** (Sprint 57.7 advances Phase 57+ Frontend SaaS, NOT main V2 progress)
✅ **Calibration `iam-frontend-spike` HYBRID 0.60 1st application ratio ~0.92 projected** (in band)
⏳ **PR + squash merge** pending Day 4.5
⏳ **Phase 57.8+ direction** pending user decision

**Total cumulative D-findings**: 25 (D1-D25 across Day 0-3 — 9 RED resolved + 12 YELLOW informational + 4 GREEN well-aligned)
