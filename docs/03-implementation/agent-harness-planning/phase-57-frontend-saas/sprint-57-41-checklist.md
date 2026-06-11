# Sprint 57.41 — Checklist

[Plan](sprint-57-41-plan.md)

**Single-domain `frontend-mockup-strict-rebuild`** (mirror 57.40 5-phase Day-numbering): Day 0 / Day 1 / Day 2 / Day 2.5 / Day 3

---

## Day 0 — Plan + Checklist + 3-prong + before baseline

### 0.1 Plan + Checklist drafted (Sprint 57.40 template mirror)
- [x] **Read Sprint 57.40 plan + checklist § structure outline** (per sprint-workflow §Step 1 format-consistency rule)
- [x] **Draft `sprint-57-41-plan.md`** mirroring 57.40 §0-9 (9 sections) with single-domain scope
- [x] **Draft `sprint-57-41-checklist.md`** mirroring 57.40 Day 0/1/2/2.5/3 structure adapted for verification rebuild

### 0.2 Step 2.5 Prong 1 — Path verify (single domain scope)
- [x] **Production page mount path verify** — `frontend/src/pages/verification/index.tsx` exists (81 lines; preserved outer 2-tab shell with `recent` + `timeline` routes)
- [x] **Production component tree path verify** — `frontend/src/features/verification/components/{VerificationList,VerificationPanel,VerifierTypeBadge,CorrectionTraceView}.tsx` all exist
- [ ] **Production hooks path verify** — `Glob frontend/src/features/verification/hooks/*.ts` confirm `useVerificationRecent` exists; identify any other hooks (`useCorrectionTrace` for timeline tab — out of scope)
- [ ] **Production service path verify** — `Glob frontend/src/features/verification/services/*.ts` confirm `verificationService` exists; note signature for `listRecent` filter shape
- [x] **Mockup source path verify** — `reference/design-mockups/page-extras.jsx` exists; `const VERIFY_CLAIMS = [` @ L818-827 (~8 claim rows); `const VerificationPage = () =>` @ L829-926 (~98 lines including VERIFY_CLAIMS const)
- [ ] **mockup-ui primitive presence check** — `grep -nE "^export (function|const) (Stat|Card|Badge|Icon|BackendGapBanner)" frontend/src/components/mockup-ui.tsx` → log which primitives are present (Sprint 57.40 post-promotion all should exist; confirm `Icon` size prop usage)
- [ ] **Vitest spec presence check** — `Glob frontend/tests/unit/verification/*.test.tsx` → identify existing specs (VerificationList likely) to migrate/delete
- [ ] **e2e spec presence check** — `Glob frontend/tests/e2e/verification/*.spec.ts` → identify what needs adaptation

### 0.3 Step 2.5 Prong 2 — Content verify
- [x] **Production verification/index.tsx content shape verify** — outer 2-tab Tabs (`recent` / `timeline`) + RequireAuth + AppShellV2; PRESERVED unchanged per §1.4 Option A decision
- [x] **Production VerificationList.tsx content verify** — 299 lines; filter form (3 fields Session ID / Verifier Type / Passed) + paginated 6-col table + Prev/Next footer + Sprint 57.33 defensive `?? []` guards at L186/200/215/257; ORPHAN DELETE per Karpathy §3
- [ ] **`VerificationLogEntry` / `VerificationLogFilter` / `VerifierType` types verify** — `grep -B 2 -A 20 "VerificationLogEntry\|VerificationLogFilter" frontend/src/features/verification/types.ts` → confirm shape fields needed for `VERIFY_CLAIMS` mapping (per plan §3.7); document gaps as candidates for `AD-Verification-Backend-Claim-Evidence-Extension`
- [ ] **Backend `/verifications/recent` response schema verify** — `Glob backend/src/api/v1/verification/router.py` + grep response model → confirm field shape matches mockup's claim/evidence/kind needs; document gaps
- [ ] **`useVerificationRecent` query shape verify** — `Read frontend/src/features/verification/hooks/useVerificationRecent.ts` → confirm returns `{items, total, has_more}` envelope (per `query.data.items ?? []` defensive pattern in VerificationList:200/215)

### 0.4 Step 2.5 Prong 2.5 — Child component tree depth audit (AP-Phase2-A/B/C anti-patterns) — AD-Plan-5
- [ ] **Enumerate child component tree** — `grep -nE "import.*from.*@/features/verification" frontend/src/pages/verification/index.tsx` (depth-1: VerificationList + CorrectionTraceView)
- [ ] **AP-Phase2-C grep on each child in scope** — `grep -E "bg-card|text-foreground|border-border|bg-muted|text-muted-foreground" frontend/src/features/verification/components/{VerificationList,VerificationPanel,VerifierTypeBadge}.tsx` → should be 0 (post FIX-015); confirm. CorrectionTraceView excluded (out of scope `timeline` tab)
- [ ] **STYLE.md §3 inline `style=` escape comment grep** — `grep -E "style=\\{\\{" frontend/src/features/verification/components/*.tsx` → verify each match has adjacent `eslint-disable-next-line no-restricted-syntax` comment (Sprint 57.40 FIX-015 lesson)
- [ ] **AP-Phase2-A outer wrapper artifact grep** — `grep -nE "<div style=\\{\\{[^}]*padding" frontend/src/features/verification/components/*.tsx` → should be 0
- [ ] **Layout-class fullBleed grep** — `grep -nE "fullBleed" frontend/src/pages/verification/index.tsx` → verification is NOT fullBleed page (fits normal page padding), confirm

### 0.5 Step 2.5 Prong 3 — Schema verify
- [x] **N/A — no DB schema / migration / ORM changes in Sprint 57.41** (frontend-only sprint; backend `/verifications/recent` endpoint unchanged)

### 0.6 Catalog drift findings in progress.md
- [ ] **Create `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-41/progress.md`**
  - Day 0 entry with "Drift findings" header
  - Any Prong 1 / 2 / 2.5 grep results that don't match Plan §3 spec → log as D-DAY0-X
  - Anticipated D-DAY0-1: backend `VerificationLogEntry` likely lacks structured `claim` / `evidence` / `kind` fields → confirm + carryover AD
  - Decide go/no-go: ≤20% shift → continue; 20-50% → revise plan §Acceptance + §Workload; >50% → abort & redraft
  - DoD: progress.md exists with Day 0 entry summarizing single-domain scope confirmation

### 0.7 Capture before baseline (route-sweep)
- [ ] **Re-point `frontend/scripts/route-sweep.mjs` OUT_DIR** to `sprint-57-41-verification-full-rebuild` (1-line edit + MHist entry; mirror Sprint 57.40 D-DAY0 pattern)
- [ ] **Dev server check on port 3007** — if not running, start `cd frontend && npm run dev -- --port 3007` (do not stop any node.js process per session guidance)
- [ ] **Run sweep before**: `node frontend/scripts/route-sweep.mjs before` → 24 PNGs in `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-41/artifacts/verification-full-rebuild/screenshots/before/`
- [ ] **Verify**: 24 files in before/ + no new failed routes (8 PUBLIC + 16 AppShellV2 per FIX-018 auto-derive)

### 0.8 Pre-Day-1 baseline checks
- [ ] **Vitest baseline confirm 493/493** (`cd frontend && npm test -- --reporter=dot`)
- [ ] **mockup-fidelity guard exit 0** (`node frontend/scripts/check-mockup-fidelity.mjs`) → baseline 46
- [ ] **Lint baseline** — `npm run lint` (non-silent per `.claude/rules/sprint-workflow.md §Before Commit Checklist` — no `--silent` swallow)

### 0.9 Day 0 user review checkpoint
- [ ] **Present plan + checklist summary to user** — `Sprint 57.41 Day 0 ready. Plan = ~340 lines. Checklist = ~210 lines. Single-domain frontend-mockup-strict-rebuild 0.60 (7th data point). Scope = 6 NEW components + VerificationList orphan delete + route swap on pages/verification/index.tsx + route-sweep mock + drift audit report update.`
- [ ] **Wait for user green-light before Day 1 code starts** — per CLAUDE.md §Sprint Execution Workflow Step 1+2

---

## Day 1 — 6 NEW components + VerificationList orphan delete (agent-delegated 8th consecutive)

### 1.1 Agent delegation prep
- [ ] **Read mockup `page-extras.jsx:817-926`** (VERIFY_CLAIMS + VerificationPage)
- [ ] **Read existing mockup-ui primitives** — confirm Stat / Card / Badge / Icon / BackendGapBanner exports
- [ ] **Read existing `useVerificationRecent` hook** — confirm query shape + filter prop signature (Day 1 mapping reference)
- [ ] **Prepare agent task brief**:
  - Scope = 6 NEW components (per plan §3.2) + orphan delete VerificationList.tsx + swap `pages/verification/index.tsx` recent route mount
  - Preserve `useVerificationRecent` / `verificationService` wiring (NO touch)
  - Preserve `VerifierTypeBadge` export (reused in new `VerificationRunsTable`)
  - Preserve outer 2-tab shell in `pages/verification/index.tsx` (NO touch — only the `recent` Route element swaps)
  - Preserve `/verification/timeline` route + CorrectionTraceView (NO touch)
  - Use mockup verbatim CSS classes per Sprint 57.28 foundation; inline `style=` literals per `AD-Inline-Style-Rule-vs-Verbatim-Method` (file-level `eslint-disable no-restricted-syntax` with rationale)
  - 4 KPI: Pass rate derived from `useVerificationRecent.data.items` (compute `passed.length / total * 100`); other 3 fixture + AP-2 BackendGapBanner
  - Sidebar Failure kinds + Flaky checks: AP-2 fixture (mockup data verbatim)
  - Field mapping per plan §3.7 with best-effort fallbacks where backend lacks structured fields

### 1.2 Primitive lifts (if Day 0 0.2 grep showed missing)
- [ ] **Confirm all primitives present** — Stat / Card / Badge / Icon / BackendGapBanner should all be in mockup-ui.tsx post Sprint 57.40 promotion; if Icon size prop missing, lift from page-extras.jsx Icon usage

### 1.3 6 NEW component creation (agent-delegated 1st invocation — 8th consecutive)
- [ ] **Delegate to `code-implementer` agent** (1st invocation):
  - Input: 6 component specs from plan §3.2 + mockup source line ranges + Sprint 57.40 ApprovalsPageHeader/ApprovalsStatsStrip precedents for rename
  - Output: 6 NEW files (VerificationPageHeader / VerificationStatsStrip / VerificationRunsTable / FailureKindsCard / FlakyChecksCard / VerificationView)
  - DoD: TS 0 errors / lint clean / each component renders standalone if isolated

### 1.4 VerificationList orphan delete + route swap
- [ ] **Delete `frontend/src/features/verification/components/VerificationList.tsx`** (per Karpathy §3; backend `?session_id=&verifier_type=&passed=` filter capability preserved at hook level — UI deferred to Phase 58+ via carryover AD)
- [ ] **Delete `frontend/tests/unit/verification/VerificationList.test.tsx`** if exists (with parent)
- [ ] **Edit `frontend/src/pages/verification/index.tsx`** — swap `<VerificationList />` → `<VerificationView />` import + Route element (1-line ish change); update MHist
- [ ] **Mark 8th consecutive code-implementer delegation** in progress.md Day 1 entry

### 1.5 Vitest spec verify (decide at agent finish)
- [ ] **Run Vitest** — `npm test -- --reporter=dot`
- [ ] **If 493 - VerificationList.test count = N** (e.g. 493 - 4 = 489) → confirm baseline before NEW specs
- [ ] **If any unrelated fail** → adapt spec (prefer text/role/testid assertions over class-name per Sprint 57.37 D-DAY3-1 class-swap-resilient convention)
- [ ] DoD: Vitest passes (count adjusted for VerificationList.test deletion)

### 1.6 Day 1 drift catalog + commit
- [ ] **progress.md Day 1 entry** — actual hr vs ~4.5 est; drift findings if any (D-DAY1-X format)
- [ ] **Commit**: `feat(frontend, sprint-57-41): /verification recent view full rebuild — 6 NEW components + VerificationList orphan delete + recent route mount swap`

---

## Day 2 — Vitest specs + route-sweep mock + mockup-fidelity threshold + drift audit report update

### 2.1 Vitest spec migration
- [ ] **Delete `VerificationList.test.tsx`** (with VerificationList.tsx orphan delete in 1.4) — confirm gone
- [ ] **Audit `frontend/tests/e2e/verification/*.spec.ts`** — adapt or delete per scope (filter-form-flow tests obsolete; replace with mockup-shape view assertions if time permits — best-effort Day 2)

### 2.2 NEW Vitest specs (+5-8 NEW specs target)
- [ ] **NEW `VerificationPageHeader.test.tsx`** — 1-2 tests: title + sub + route-pill + All kinds + Export buttons render
- [ ] **NEW `VerificationStatsStrip.test.tsx`** — 2 tests: 4 KPI labels render / Pass rate computed from items / AP-2 BackendGapBanner declares 3 fixture KPI status
- [ ] **NEW `VerificationRunsTable.test.tsx`** — 2-3 tests: 6-col header / status circle green/red dispatch / score color tier (>0.85 success / >0.6 warning / else danger) / mapping `VerificationLogEntry`→mockup `VERIFY_CLAIMS` shape
- [ ] **NEW `FailureKindsCard.test.tsx`** — 1 test: 5-row Card title + AP-2 banner + bar-track + palette
- [ ] **NEW `FlakyChecksCard.test.tsx`** — 1 test: 3-row Card title + AP-2 banner + rate badge
- [ ] DoD: Vitest 489 (post-VerificationList delete) + 5-8 NEW = ~494-497/497

### 2.3 D-DAY0-1 candidate: route-sweep mock fix
- [ ] **Edit `frontend/scripts/route-sweep.mjs`** — if Day 0 confirmed `/verifications/recent` needs envelope mock (per plan §3.5 + AD-RouteSweep-Envelope-Mock-Convention), add URL-dispatch branch returning `{items: [], total: 0, has_more: false}`
- [ ] **MHist entry** added with reference to Sprint 57.40 governance precedent (2nd application of envelope mock pattern)
- [ ] **Smoke test**: `node scripts/route-sweep.mjs before --list-only` → 24 routes intact, derive logic unchanged

### 2.4 mockup-fidelity threshold update
- [ ] **Run guard** — live count vs baseline 46
- [ ] **Update `HEX_OKLCH_BASELINE`** 46 → expected 48-50 (per plan §3.6 +2-4 budget: status circle bg ×2 + minor color literals); within ≤50 envelope
- [ ] **MHist entry** added with mockup-token-vocabulary precedent reference

### 2.5 Drift audit report update
- [ ] **Edit `claudedocs/5-status/drift-audit-2026-05-25/audit-report.md`** — `/verification` verdict 🔴 CATASTROPHIC → ✅ PARITY (post-rebuild)
- [ ] **Update verdict summary table** — 17 PARITY → 18 (+1 NEAR-PARITY); 4 CATASTROPHIC → 3 (memory / admin-tenants / tenant-settings remain)
- [ ] **Update Recommendations section** — strike Sprint 57.40-closed #1 (sweep-mock fix) + #2 (verification rebuild via Sprint 57.41); promote remaining to 1–4; add note `AD-RouteSweep-Envelope-Mock-Convention` reaches 2nd application

### 2.6 Day 2 drift catalog + commit
- [ ] **progress.md Day 2 entry** — full Day 2 narrative with calibration data + commit SHA back-fill
- [ ] **Commit**: `chore(frontend, sprint-57-41): Day 2 — +5-8 NEW Vitest specs + route-sweep envelope mock + mockup-fidelity baseline 46->48-50 + drift audit report verification PARITY update`

---

## Day 2.5 — Capture after baseline + 22-route sweep diff review + fidelity verdict

### 2.5.1 Capture after baseline (route-sweep)
- [ ] **Run sweep after**: `node frontend/scripts/route-sweep.mjs after` → 24 PNGs in `screenshots/after/`
- [ ] **Verify**: 24 files in after/ + 0 failed routes (8 PUBLIC + 16 AppShellV2)

### 2.5.2 Before/after diff review
- [ ] **Compare each route**: before/X.png vs after/X.png via python sha256
- [ ] **Classify**: IDENTICAL / CHANGED / FAIL
- [ ] **Expected CHANGED set**: `/verification` + `/verification/recent` (rebuild)
- [ ] **Confirm 0 UNINTENDED regressions** in other 20 routes (sub-300 byte noise acceptable per Sprint 57.40 envelope)

### 2.5.3 Fidelity verdict (/verification only)
- [ ] **`/verification` verdict**: aim ✅ **PARITY** — structural check (page-head / 4 KPI / 2-col grid / 6-col runs table / Failure kinds sidebar / Flaky checks sidebar / outer 2-tab preserved)
- [ ] DoD: verdict recorded in progress.md Day 2.5 §2.5.3; retrospective.md §Q1 will fold-in Day 3 closeout

### 2.5.4 Side-by-side mockup compare (re-use mockup-sweep.mjs)
- [ ] **Mockup re-shoot** — `node frontend/scripts/mockup-sweep.mjs` regenerate `claudedocs/5-status/drift-audit-2026-05-25/screenshots/mockup/verification.png` (or reuse existing if static)
- [ ] **Visual compare**: production `after/verification.png` vs mockup → verdict
- [ ] **Evidence saved**: 3-way pair (BEFORE day0 / AFTER day1 / MOCKUP reference) in `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-41/artifacts/verification-full-rebuild/before-after/`

### 2.5.5 Day 2.5 drift + commit
- [ ] **progress.md Day 2.5 entry** — full sweep summary + verdict + evidence stage
- [ ] **Commit**: `chore(sprint-57-41): Day 2.5 — after-baseline 24 PNGs + N IDENTICAL/M CHANGED diff + /verification PARITY verdict + 3-way evidence pair`

---

## Day 3 — Closeout (retro + matrix update + memory + push + PR)

### 3.1 Retrospective
- [ ] **Create retrospective.md** with Q1-Q6 sections — mirroring Sprint 57.40 format (commits / Q1-Q5 narrative depth + Q6 verbatim-CSS / Q7 N/A SKIP)
- [ ] **Q2 single-domain calibration ratio** — actual / committed ≈ TBD; classify vs [0.85, 1.20] band
- [ ] **Q2 7th data point narrative** — 7-pt window 0.59/1.19/0.88/0.95/1.18/0.36/TBD; compute mean; `When to adjust` per 3-sprint window rule
- [ ] **Q4 audit debt** — All kinds dropdown AP-2 stub / 3 fixture KPI / sidebar fixture cards / filter form retirement; documented as carryover ADs
- [ ] **Q5 carryover candidates** — AD-Verification-Filter-Form-Phase58-Migrate / AD-Verification-Backend-Claim-Evidence-Extension / AD-Verification-All-Kinds-Filter-Dropdown / AD-Verification-Failure-Kinds-Aggregation-Endpoint / AD-Verification-Flaky-Checks-Aggregation-Endpoint / AD-Sprint-Plan-Agent-Delegation-Factor-Modifier (4th data point if ratio < 0.7)
- [ ] **Q6 verbatim-CSS protocol compliance** — Layer 2 diff 0 / Layer 4 collision 0 / HEX_OKLCH_BASELINE bump within ≤50 envelope / guard PASS

### 3.2 Calibration matrix update (`sprint-workflow.md §Scope-class multiplier matrix`)
- [ ] **`frontend-mockup-strict-rebuild` row update** — append Sprint 57.41 as 7th data point (ratio TBD + 7-pt mean); status decision per `When to adjust` rule
- [ ] **MHist entry** — Sprint 57.41 Day 3 entry added with 7th data point notation; if ratio < 0.7, document as 4th cross-class data point for `AD-Sprint-Plan-Agent-Delegation-Factor-Modifier` activation evaluation
- [ ] **Agent-delegation factor modifier proposal status check** — if 4-data-point cross-class evidence threshold met (per plan §1.5), document in Q4 + Q5 + propose Sprint 57.42 retro structural decision

### 3.3 Memory subfile + MEMORY.md pointer
- [ ] **Create `memory/project_phase57_41_verification_full_rebuild.md`** with sprint detail (goal/shipped/calibration/Phase-2 progress/carryover ADs/anomalies/commits/related)
- [ ] **Add MEMORY.md entry** — quality pointer with topic + keywords + subfile link per §Sprint Closeout Update Policy (~250-300 char ceiling)

### 3.4 next-phase-candidates.md
- [ ] **Add Sprint 57.41 carryover section** at top with shipped summary + calibration + Phase-2 epic progress
- [ ] **Update Phase-2 epic progress** — 4 → 3 🔴 CATASTROPHIC remaining (memory / admin-tenants / tenant-settings) + 1 NEAR-PARITY (chat-v2 rename) + 18 PARITY (or higher depending on /verification + /verification/recent count separately)
- [ ] **Add 5-7 NEW carryover ADs** (#60+) ordered by ROI per audit Recommendations remaining

### 3.5 CLAUDE.md minimal touch (per §Sprint Closeout Update Policy)
- [ ] **Update `Current Sprint` row** with Sprint 57.41 1-line + redirect to memory subfile + next-phase-candidates.md
- [ ] **Update `Last Updated` footer** — 1-line per §Sprint Closeout Policy navigator format
- [ ] **NO retro detail packed into table cells** (REFACTOR-001 discipline observed)

### 3.6 Commit closeout + push + PR
- [ ] **Final commit**: `chore(sprint-57-41): Day 3 closeout — retro + matrix + memory + CLAUDE.md`
- [ ] **Push**: `git push -u origin feature/sprint-57-41-verification-full-rebuild` (per CLAUDE.md "Confirmation on Destructive Only" — push needs explicit user authorization)
- [ ] **Open PR**: `gh pr create --base main --title "feat(frontend, sprint-57-41): /verification recent view full mockup-fidelity rebuild (closes drift audit 2026-05-25 #2 priority CATASTROPHIC)"`
- [ ] **Wait for CI green** → squash-merge ready → user confirmation before merge

---

## Sprint 57.41 Closeout Self-Check (per `.claude/rules/sprint-workflow.md` §Sprint Closeout)

- [ ] **CLAUDE.md changes**: Only Current Sprint row + Last Updated footer (no per-sprint history table additions)?
- [ ] **MEMORY.md new entry**: ~250-300 char quality pointer (topic + keywords + subfile link)?
- [ ] **Sprint detail preserved**: memory subfile + retrospective.md with full content?
- [ ] **Carryover / open items**: documented in `next-phase-candidates.md` (NOT in CLAUDE.md / MEMORY.md prose)?
- [ ] **Calibration ratio**: tracked in `sprint-workflow.md §Scope-class multiplier matrix` (7th data point + 7-pt mean)?
- [ ] **Agent-delegation factor modifier**: 4th cross-class data point status logged in Q4 + Q5 if applicable?
- [ ] **Phase-2 epic progress note**: post-sprint 4 → 3 🔴 CATASTROPHIC remaining (next high-ROI candidates = `/memory` matrix rebuild ~10-15 hr OR `/admin-tenants` tenants table rebuild ~12-15 hr OR `/tenant-settings` 6-tab rebuild ~15-20 hr OR `/chat-v2` tab rename ~30 min quick win)
- [ ] **Drift audit report updated**: `/verification` verdict ✅ PARITY in `claudedocs/5-status/drift-audit-2026-05-25/audit-report.md`?
