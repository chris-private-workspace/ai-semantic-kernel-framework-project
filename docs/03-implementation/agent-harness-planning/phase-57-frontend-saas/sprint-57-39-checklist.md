# Sprint 57.39 — Checklist

[Plan](sprint-57-39-plan.md)

**4-domain batched** (mirror 57.38 5-phase Day-numbering): Day 0 / Day 1 / Day 2 / Day 2.5 / Day 3

---

## Day 0 — Plan + Checklist + 三-prong + before baseline

### 0.1 Plan + Checklist drafted (Sprint 57.38 template mirror)
- [x] **Read Sprint 57.38 plan + checklist § structure outline** (per sprint-workflow §Step 1 format-consistency rule)
- [x] **Draft `sprint-57-39-plan.md`** mirroring 57.38 §0-9 (10 sections) with 4-domain scope (governance + verification + redaction + error-policy)
- [x] **Draft `sprint-57-39-checklist.md`** mirroring 57.38 Day 0/1/2/2.5/3 structure adapted for 4 ship domains (Day 1 = re-point pair / Day 2 = PROP→real pair)

### 0.2 Step 2.5 Prong 1 — Path verify (4 domains scope) ✅ COMPLETED Day 0
- [x] **Domain A `/governance` production source path verify** — `frontend/src/pages/governance/index.tsx` exists (75 lines, real content, Tailwind utility classes)
- [x] **Domain B `/verification` production source path verify** — `frontend/src/pages/verification/index.tsx` exists (77 lines, real content, Sprint 57.33 defensive guards)
- [x] **Domain C `/redaction` production source path verify** — `frontend/src/pages/redaction/index.tsx` exists (1-line ComingSoonPlaceholder re-export)
- [x] **Domain D `/error-policy` production source path verify** — `frontend/src/pages/error-policy/index.tsx` exists (1-line ComingSoonPlaceholder re-export)
- [x] **All 4 mockup sources confirmed**:
  - `page-governance.jsx` (773 lines) — `const Approvals = () =>` @ L283 (data `const APPROVALS = [` @ L273) — minor drift from initial plan estimate L283 → actual symbol start, both lines part of mockup source
  - `page-extras.jsx` (991 lines) — `const VerificationPage = () =>` @ L829
  - `page-platform2.jsx` (722 lines) — `const RedactionPage = () =>` @ L254
  - `page-platform.jsx` (672 lines) — `const ErrorPolicyPage = () =>` @ L426

### 0.3 Step 2.5 Prong 2 — Content verify ✅ COMPLETED Day 0
- [x] **Domain A `/governance` content shape verify** — current uses Tailwind utility classes (`bg-card`, `text-card-foreground`, etc.); imports from `features/governance/` (ApprovalList + ApprovalCard + service hooks); NO mockup verbatim classes yet
- [x] **Domain B `/verification` content shape verify** — current uses Tailwind utility classes; Sprint 57.33 defensive `(query.data.entries ?? []).length` pattern present; NO mockup verbatim classes yet
- [x] **Domain C `/redaction` content shape verify** — single 1-line file re-exporting ComingSoonPlaceholder; `features/redaction/` directory does NOT yet exist (clean slate for mockup port)
- [x] **Domain D `/error-policy` content shape verify** — same as Domain C (1-line stub; `features/error-policy/` does NOT yet exist)
- [ ] **routes.config.ts `/redaction` + `/error-policy` rows confirm `proposed: true`** before Day 2 PROP→real promotion — confirm at Day 2 start

### 0.4 Step 2.5 Prong 3 — Schema verify
- [ ] **N/A — no DB schema / migration / ORM changes in Sprint 57.39** (all 4 domains are frontend-only; Cat 9 audit unchanged from 57.38)

### 0.5 Catalog drift findings in progress.md
- [ ] **Create `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-39/progress.md`**
  - Day 0 entry with "Drift findings" header
  - Format: `D{N}` ID + Finding + Implication; cross-ref plan §Risks if scope-shift
  - Decide go/no-go: ≤20% shift → continue; 20-50% → revise plan §Acceptance + §Workload; >50% → abort & redraft
  - DoD: progress.md exists with Day 0 entry summarizing 4-domain scope confirmation

### 0.6 Capture before baseline (route-sweep)
- [ ] **Re-point `frontend/scripts/route-sweep.mjs` OUT_DIR** to `sprint-57-39-governance-multipage-phase2` (1-line edit + MHist entry; mirror Sprint 57.38 D-DAY0 pattern)
- [ ] **Start dev server** `npm run dev` (port 3007) in background
- [ ] **Run sweep before**: `node frontend/scripts/route-sweep.mjs before` → 22 PNGs in `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-39/artifacts/governance-multipage-phase2/screenshots/before/`
- [ ] **Verify**: 22 files in before/ + no failed routes

### 0.7 Pre-Day-1 baseline checks
- [ ] **Vitest baseline confirm 464/464** (`cd frontend && npm test -- --reporter=dot`)
- [ ] **mockup-fidelity guard exit 0** (`node frontend/scripts/check-mockup-fidelity.mjs`)
- [ ] **TypeScript compile baseline** — `npm run typecheck` (skip if pre-existing tsconfig TS6310 same as FIX-010/011 hotfix)
- [ ] **Lint baseline** — `npm run lint` (clean except 3 pre-existing jsx-ast-utils warnings)

---

## Day 1 — Re-point pair (Domain A `/governance` + Domain B `/verification`; agent-delegated)

### 1.1 Agent delegation prep (Domain A + B)
- [ ] **Read `frontend/src/pages/governance/index.tsx` (75 lines) + mockup `page-governance.jsx:273-410` `Approvals` block** (gather context for code-implementer agent prompt)
- [ ] **Read `frontend/src/pages/verification/index.tsx` (77 lines) + mockup `page-extras.jsx:829-991` `VerificationPage` block**
- [ ] **Prepare agent task brief** (single agent invocation handles both):
  - Scope = verbatim CSS swap on 2 single-file pages
  - Preserve Sprint 57.33 `(entries ?? []).length` defensive guard in /verification
  - Mirror Sprint 57.34 `/orchestrator` precedent (config/tabbed-forms shape) + Sprint 57.38 `/subagents` precedent (single-file 402-line swap)
  - Use mockup verbatim inline-style literals per `AD-Inline-Style-Rule-vs-Verbatim-Method`
  - DO NOT touch backend wiring (`useApprovals` + `useApprovalDecision` mutation hooks unchanged; `useVerificationEntries` unchanged)

### 1.2 Domain A + B production code edit (agent-delegated)
- [ ] **Delegate to `code-implementer` agent** (1st invocation):
  - Input: 4 file contents (2 production + 2 mockup) + Sprint 57.38 `SubagentsPage` precedent as shape reference
  - Output: 2 commits OR 1 combined commit covering both production page swaps
  - DoD: TS 0 errors / lint clean / Vitest still passes
- [ ] **Mark 6th consecutive code-implementer delegation** in progress.md Day 1 entry

### 1.3 Vitest spec adapt (decide at agent finish)
- [ ] **Run Vitest** — `npm test -- --reporter=dot`
- [ ] **If all 464 pass** → D-DAY1-1 positive surprise (Sprint 57.37 D-DAY3-1 convention candidate validated again — text/role/data-testid selectors class-swap-resilient)
- [ ] **If any fail** → adapt spec (prefer adding text/role assertions over class-name assertions where possible)
- [ ] DoD: Vitest ≥464/464

### 1.4 Day 1 drift catalog + commit
- [ ] **progress.md Day 1 entry** — actual hr vs ~3.6 est; drift findings if any (D-DAY1-X format)
- [ ] **Commit**: `feat(frontend, sprint-57-39): Domain A /governance + Domain B /verification verbatim CSS re-point`

---

## Day 2 — PROP→real pair (Domain C `/redaction` + Domain D `/error-policy`; agent-delegated)

### 2.1 Agent delegation prep (Domain C + D)
- [ ] **Read mockup `page-platform2.jsx:254-end-of-RedactionPage` block** (line range TBD on first read; estimate ~150-200 lines)
- [ ] **Read mockup `page-platform.jsx:426-end-of-ErrorPolicyPage` block** (estimate ~245 lines)
- [ ] **Decide per-domain component structure**:
  - If mockup is single page-level component (no inner components) → port as single `index.tsx` rewrite
  - If mockup uses inner components → create `frontend/src/features/{redaction,error-policy}/components/` directory
- [ ] **Prepare agent task brief** (single agent invocation handles both):
  - Scope = replace 1-line ComingSoonPlaceholder re-export with full mockup port
  - Use verbatim CSS classes per Sprint 57.28 foundation (NO Tailwind utility invention)
  - Backend data = fixture; AP-2 BackendGapBanner expected per CLAUDE.md §Frontend Mockup-Fidelity Hard Constraint
  - Drop `proposed: true` from routes.config.ts for both routes

### 2.2 Domain C + D production code edit (agent-delegated)
- [ ] **Delegate to `code-implementer` agent** (2nd invocation Day 2):
  - Input: mockup sources + Sprint 57.21 chat-v2 Phase-1 precedent (similar PROP-to-real shape)
  - Output: 2 commits OR 1 combined commit covering both PROP→real ports + routes.config.ts flag drops
  - DoD: TS 0 errors / lint clean / Vitest still passes (or +0-4 NEW specs added)
- [ ] **Verify routes.config.ts**:
  - `grep -A3 'path: "/redaction"' frontend/src/routes.config.ts` → no `proposed:` line
  - `grep -A3 'path: "/error-policy"' frontend/src/routes.config.ts` → no `proposed:` line

### 2.3 Vitest spec stability check + new specs
- [ ] **Run Vitest** — `npm test -- --reporter=dot`
- [ ] **Decide on +1-2 NEW spec per new page**:
  - `frontend/tests/unit/pages/redaction/RedactionPage.test.tsx` — render verify; mockup-class smoke test
  - `frontend/tests/unit/pages/error-policy/ErrorPolicyPage.test.tsx` — render verify; mockup-class smoke test
  - DoD: Vitest ≥464/464 (or ≥468/468 if +4 specs added)

### 2.4 Day 2 drift catalog + commit
- [ ] **progress.md Day 2 entry** — actual hr vs ~3.9 est; drift findings if any (D-DAY2-X format)
- [ ] **Commit**: `feat(frontend, sprint-57-39): Domain C /redaction + Domain D /error-policy PROP→real mockup port`
- [ ] **Run mockup-fidelity guard** — `node frontend/scripts/check-mockup-fidelity.mjs` exit 0; `HEX_OKLCH_BASELINE` bump within +5-13 envelope (current 51 → target ≤64)

---

## Day 2.5 — Capture after baseline + 22-route sweep diff review + fidelity verdict (4 routes)

### 2.5.1 Capture after baseline (route-sweep)
- [ ] **Run sweep after**: `node frontend/scripts/route-sweep.mjs after` → 22 PNGs in `screenshots/after/`
- [ ] **Verify**: 22 files in after/ + 0 failed routes

### 2.5.2 Before/after diff review
- [ ] **Compare each route**: before/X.png vs after/X.png
- [ ] **Classify**: IDENTICAL (byte-equal) / CHANGED (visual diff) / FAIL (any route crashed)
- [ ] **Expected CHANGED set**: `/governance` + `/verification` + `/redaction` + `/error-policy` (4 Domain A-D intentional)
- [ ] **0 UNINTENDED regressions**: any CHANGED outside expected set = drift to investigate before close

### 2.5.3 Fidelity verdict (4 domains)
- [ ] **`/governance` verdict**: PARITY / NEAR-PARITY / MINOR-DRIFT / MAJOR-DRIFT
- [ ] **`/verification` verdict**: same
- [ ] **`/redaction` verdict**: same
- [ ] **`/error-policy` verdict**: same
- [ ] DoD: 4 verdicts recorded in retrospective.md §per-Domain

### 2.5.4 Day 2.5 drift + commit
- [ ] **progress.md Day 2.5 entry** — sweep summary IDENTICAL count / CHANGED count (expected 18 IDENTICAL + 4 CHANGED)
- [ ] **Commit**: `chore(sprint-57-39): Day 2.5 22-route sweep + 4-domain fidelity verdicts`

---

## Day 3 — Closeout (retro + matrix update + memory + push + PR)

### 3.1 Retrospective
- [ ] **Create `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-39/retrospective.md`** with Q1-Q7 sections
- [ ] **Q2 per-domain calibration ratios** — `actual_total_hr / committed_total_hr` for each of A/B/C/D; sprint-aggregate ratio; verdict vs ~0.67 expected blend
- [ ] **Q2 `-with-extras` 1st deliberate-test data point** — narrative on whether the 4 ratios validate 0.65 baseline against 4-route mixed shape (re-point + PROP→real); compare with 57.35/36/37B retroactive data
- [ ] **Q5 carryover candidates** — any new sub-classification ADs if Domain C/D PROP→real diverges from re-point; backend-pair needs for /redaction or /error-policy

### 3.2 Calibration matrix update (`sprint-workflow.md §Scope-class multiplier matrix`)
- [ ] **`-with-extras` row update** — append Sprint 57.39 as 1st deliberate-test data point (4 ratios + sprint-aggregate); update class status (`KEEP 0.65` if in band; `propose lift` if 2+ above band)
- [ ] **If C/D PROP→real ratios diverge significantly from A/B re-point ratios** → log new AD `AD-Sprint-Plan-frontend-verbatim-css-repoint-with-extras-prop-to-real-sub-class` for future split consideration

### 3.3 Memory subfile + MEMORY.md pointer
- [ ] **Create `memory/project_phase57_39_governance_multipage_phase2.md`** with sprint detail
- [ ] **Add MEMORY.md entry** — quality pointer (~250-300 char with topic + keywords + subfile link per §Sprint Closeout Update Policy)
- [ ] DoD: index entry rendered

### 3.4 next-phase-candidates.md
- [ ] **Add Sprint 57.39 carryover section** at top
- [ ] **Remove `/governance multi-page Phase-2`** entry from 🟡 remaining list (4 routes shipped)
- [ ] **Update Phase-2 epic progress**: 11/17 → **15/17 shipped** / **2 🟡 remaining** (Phase 58+ STRUCTURAL: /memory + /tenant-settings; /audit-log DRAFT still requires backend pair; /admin-tenants + /compaction still candidate but moved to separate listing)
- [ ] **Add any new carryover** (e.g., if Domain C/D required backend wire deferral → log carryover; if Vitest budget exceeded → log)

### 3.5 CLAUDE.md minimal touch (per §Sprint Closeout Update Policy)
- [ ] **Update `Current Sprint` row** with 57.40 placeholder (or candidate description)
- [ ] **Update `Last Updated` footer** — 1-line: `**Last Updated**: 2026-05-XX (Sprint 57.39 — 4-domain batched: governance multi-page Phase-2: /governance + /verification re-point + /redaction + /error-policy PROP→real); see memory/ for sprint history`
- [ ] **NO retro detail packed into table cells** (per REFACTOR-001 lesson)

### 3.6 Commit closeout + push + PR
- [ ] **Final commit**: `chore(sprint-57-39): closeout — retro + matrix + memory + CLAUDE.md`
- [ ] **Push**: `git push -u origin feature/sprint-57-39-governance-multipage-phase2`
- [ ] **Open PR**: `gh pr create --base main --title "feat(frontend, sprint-57-39): Governance Category Multi-Page Phase-2 — 4-domain batched (governance + verification re-point + redaction + error-policy PROP→real)"` with full body (mirror 57.38 PR template)
- [ ] **Wait for CI green** → squash-merge ready → user confirmation before merge

---

## Sprint 57.39 Closeout Self-Check (per `.claude/rules/sprint-workflow.md` §Sprint Closeout)

- [ ] **CLAUDE.md changes**: Only Current Sprint row + Last Updated footer (no per-sprint history table additions)?
- [ ] **MEMORY.md new entry**: ~250-300 char quality pointer (topic + keywords + subfile link)?
- [ ] **Sprint detail preserved**: memory subfile + retrospective.md with full content?
- [ ] **Carryover / open items**: documented in `next-phase-candidates.md` (NOT in CLAUDE.md / MEMORY.md prose)?
- [ ] **Calibration ratios**: tracked in `sprint-workflow.md §Scope-class multiplier matrix` (4 domains + sprint-aggregate)?
- [ ] **D-DAY1-1 surprise note**: if Vitest spec needed NO update on re-point pair → record as Sprint 57.37 D-DAY3-1 convention candidate further validation
- [ ] **Phase-2 epic progress note**: post-sprint 15/17 routes Phase-2 shipped (next non-Phase-58+ candidate = /audit-log backend-pair OR /admin-tenants `-simple` 3rd validation)
