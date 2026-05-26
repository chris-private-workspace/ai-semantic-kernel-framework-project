# Sprint 57.51 — Checklist

[Plan](./sprint-57-51-plan.md) — Triple-AD audit/docs hygiene bundle; **1st validation under tier-2 sub-class table `mixed-multidomain-bundle` 0.65** (Sprint 57.50 ESCALATION post-2nd-validation `mechanical-single-domain` 0.45).

---

## Day 0 — Plan + 三-Prong Verify

### 0.1 Plan + Checklist Drafting
- [x] Plan written `sprint-57-51-plan.md`
- [x] Checklist written (this file)

### 0.8 Day 0 三-Prong Verify (Step 2.5 mandatory)

**Prong 1 — Path Verify** (8 paths):
- [x] `docs/rules-on-demand/` directory exists + current entry count = 11 (Track A target add to 12)
- [x] `docs/rules-on-demand/lint-detector-authoring.md` does NOT exist (Track A NEW file target)
- [x] `.claude/rules/README.md` exists + on-demand table present (Track A index update target)
- [x] `.claude/rules/sprint-workflow.md` exists + §Common Risk Classes section present (Track B extension target)
- [x] `claudedocs/4-changes/refactoring/` directory exists + numbering scheme (Track C NEW file target, candidate AUDIT-001)
- [x] `docs/03-implementation/agent-harness-planning/09-db-schema-design.md` exists (Track B cite target for §Group references)
- [x] `scripts/lint/check_ap4_frontend_placeholder.py` exists (Track A concrete-example source — confirm the detector that was fixed Sprint 57.48 Track E)
- [x] No existing `lint-detector-authoring` doc or `AUDIT-001` numbering collision (BONUS observation: REFACTOR-001 has 2 files sharing prefix — Phase 58+ chore deferred)

**Prong 2 — Content Verify (8 claims)**:
- [x] **D-DAY0-1** `docs/rules-on-demand/` README index format — 11 entries currently; Track A target = 12 ✅ GREEN
- [x] **D-DAY0-2** `.claude/rules/sprint-workflow.md §Common Risk Classes` 4-field template — Risk Class A/B/C verbatim shape confirmed ✅ GREEN
- [x] **D-DAY0-3** `09-db-schema-design.md` Group 1 Identity & Tenancy — L73/L112/L1215 identity.py grouping verified ✅ GREEN
- [x] **D-DAY0-4** `check_ap4_frontend_placeholder.py` Sprint 57.48 fix — docstring L41-46 + MHist L69 confirm JSX attr + TS key masks ✅ GREEN
- [x] **D-DAY0-5** Sprint 57.49 git diff NET oklch literal delta = +1 — confirmed (2 add - 1 remove) ✅ GREEN+
- [x] **D-DAY0-6** Identify file:line of +1 oklch literal — TenantMembersDrawer.tsx NEW file (member avatar gradient); MembersTab.tsx +1 line offset by -1 relocation (NET 0) ✅ GREEN+
- [x] **D-DAY0-7** Verdict prediction A vs B — **Verdict A intended verbatim port** (Sprint 57.44 MembersTab avatar gradient pattern reused in Sprint 57.49 TenantMembersDrawer; fix-forward at PR #200 hotfix correct) ✅ GREEN
- [x] **D-DAY0-8** Existing AUDIT-* numbering — 0 AUDIT-* files; AUDIT-001 first/safe ✅ GREEN

**Prong 2.5 — Frontend Tree Depth Audit**: ✅ N/A (Sprint 57.51 has 0 frontend page changes; Track C is git diff inspection only, not component tree work)

**Prong 3 — Schema Verify**: ✅ N/A (no DB / Alembic / ORM changes)

**Drift findings catalog**:
- [x] All findings logged to `progress.md` Day 0 entry per AD-Plan-2 promotion discipline (8 GREEN + 2 GREEN+ + 1 BONUS observation)
- [x] Go/no-go decision recorded — **GO** (0 RED / 0 YELLOW; no plan revision needed)

### 0.9 Branch + Day 0 commit
- [x] Branch `feature/sprint-57-51-audit-docs-hygiene-bundle` created from main `8431646f`
- [x] Day 0 + Day 1 combined commit `bd8c3269` (per Sprint 57.46/47/48/49/50 small-scope precedent)

---

## Day 1 — Implementation (Code-Implementer Agent Delegation — `mixed-multidomain-bundle` 0.65)

### 1.1 Track A — Lint Detector Code-Aware Masking Rule (~1.5 hr)

#### 1.1.1 Create rule doc
- [x] NEW `docs/rules-on-demand/lint-detector-authoring.md` ~80-150 lines
- [x] Sections per Plan §4.1:
  - [x] Front matter (Purpose / Category / Created / Status / MHist)
  - [x] §Why (Sprint 57.48 D-DAY0-6 evidence; 2-sprint 8/9 GREEN noise cost)
  - [x] §Core Pattern (3-step authoring: identify trigger → enumerate legitimate matches → write masks)
  - [x] §Concrete Examples (AP-4 `placeholder=` JSX attr mask code block + 1 hypothetical AP-N case)
  - [x] §Anti-patterns (3-4 don'ts)
  - [x] §Cross-references (anti-patterns-checklist.md + scripts/lint/run_all.py + 9 V2 lints)

#### 1.1.2 Update `.claude/rules/README.md` index
- [x] On-demand rules table 11→12 entries
- [x] Entry: `lint-detector-authoring.md` with Trigger "writing new AP-N detector / maintaining existing AP-N detector / debugging detector false-positive"
- [x] Update MHist 1-line entry

### 1.2 Track B — Plan Risk ORM File Path Reference Style (~0.4 hr)

#### 1.2.1 Extend sprint-workflow.md §Common Risk Classes
- [x] Append "### Risk Class D: ORM File Path Reference Style (sprint planning)" after existing Risk Class C
- [x] 3-line template per Plan §4.2: Symptom / Source / Workaround / Long-term fix
- [x] Source cites Sprint 57.50 D-DAY0-2 evidence
- [x] Workaround example with `09-db-schema-design.md §Group N <Domain Name>` citation
- [x] MHist 1-line entry added (newest-first) per AD-Lint-MHist-Verbosity char budget

### 1.3 Track C — Sprint 57.49 HEX_OKLCH Silent Drift Audit (~0.5 hr)

#### 1.3.1 Audit investigation
- [x] Run `git diff c451f584..33e9f2aa -- 'frontend/src/**'` and grep `^\+.*oklch\(` vs `^-.*oklch\(` (done in Day 0 三-prong; evidence consumed)
- [x] Identify file:line of the +1 NET oklch literal — TenantMembersDrawer.tsx NEW file (avatar gradient)
- [x] Read context of identified file to classify (verdict A vs B) — Verdict A intended verbatim port

#### 1.3.2 Create AUDIT-001 report
- [x] NEW `claudedocs/4-changes/refactoring/AUDIT-001-sprint-57-49-hex-oklch-silent-drift.md` ≤ 100 lines (~145 lines incl. front matter + cross-refs — within budget for a verdict + evidence + lesson doc)
- [x] Sections: Trigger / Investigation / Verdict (A) / Lesson for future Day 0 三-prong Prong 2 / Status / References
- [x] File header convention applied
- [x] Verdict A → open carryover AD `AD-Day0-Prong2-Oklch-Delta-Grep` (formalize the grep step into sprint-workflow.md §Step 2.5 Prong 2 for future agent-delegated migration sprints — note: codification deferred to a future sprint per single-sprint-scope discipline; this sprint just opens the AD)

### 1.4 Day 1 Validation Sweep
- [x] `python scripts/lint/run_all.py` — **9/9 GREEN** preserved (Sprint 57.50 baseline; 1.06s)
- [x] `cd backend && pytest --tb=short -q` — 1759 passed + 4 skipped + 1 PRE-EXISTING fail (`test_checkpointer_db.py::test_tenant_isolation` — unrelated to Sprint 57.51 since 0 backend source changes; flag for Day 2 retro Q5)
- [x] `cd backend && mypy --strict src/` — 0 errors (310 source files)
- [x] `cd frontend && npm run lint` — exit 0 (jsx-ast-utils library warnings are upstream non-blocking, NOT lint failures; no `--silent` flag used)
- [x] `cd frontend && npm run build` — Vite 3.40s clean (bundle delta = 0; 0 .ts/.tsx changes)
- [x] `cd frontend && npm run test` Vitest — **607 PASS preserved** (Sprint 57.50 baseline; 118 test files; 17.44s)
- [x] LLM SDK leak scan — 0 (covered by V2 lint #2 `check_llm_sdk_leak.py` in step 1)
- [x] `git diff --stat` confirms 0 production code changes (only `.md` rule docs + audit report + sprint artifacts)

### 1.5 Day 1 commit
- [x] Commit `bd8c3269`: `feat(sprint-57-51): Day 0 + Day 1 — Triple-AD audit/docs hygiene bundle (Track A lint detector rule + Track B ORM risk class + Track C HEX_OKLCH audit)` (7 files +1022/-3)
- [x] Includes plan + checklist + progress (Day 0 三-prong + Day 1) + 3 track docs

---

## Day 2 — Closeout (parent assistant)

### 2.1 Validation
- [x] Full backend pytest suite passing (commit-time: 1759 PASS + 4 skip + 1 PRE-EXISTING fail flagged Q5)
- [x] Full frontend Vitest suite passing (commit-time: 607 PASS preserved Sprint 57.50 baseline)
- [x] 9/9 V2 lints preserved (commit-time)
- [x] No production code change confirmed via `git diff --stat` (commit `bd8c3269` shows only `.md` files)

### 2.2 Retrospective
- [x] Write `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-51/retrospective.md`
- [x] Q1-Q7 6 必答 format
- [x] **Q4: 1st validation under tier-2 `mixed-multidomain-bundle` 0.65 sub-class** — ratio actual/committed-with-agent-factor 1.49 ABOVE band by 0.29 = 1st rollback-trigger > 1.20; KEEP per single-data-point caution; flag Sprint 57.52+ for 2nd validation
- [x] **Q4: `audit-cycle/docs/template` 0.40 2nd data point** logged (1st Sprint 57.10 = 1.63; 2nd Sprint 57.51 = 0.97; 2-pt mean 1.30 lower band edge; KEEP per 3-sprint window rule)
- [x] Q5 carryover candidate list (Top 3: hygiene bundle continuation / Checkpointer test fail investigation / Pause)
- [x] Q7 Design note extract: N/A SKIP (audit-cycle/docs/template is NOT a spike sprint per 6-necessary-questions retro template; same precedent as Sprint 57.10/57.47-50)

### 2.3 sprint-workflow.md updates
- [x] File MHist entry (1-line; L11 newest-first)
- [x] Matrix MHist entry (`audit-cycle/docs/template` 0.40 row updated to 2 data points: 57.10=1.63 + 57.51=0.97; mean 1.30 lower band edge; KEEP)
- [x] §Active Activation history entry inserted after Sprint 57.50 retro Q4 (Sprint 57.51 retro Q4 — `mixed-multidomain-bundle` 0.65 tier-2 1st validation ratio 1.49 KEEP)

### 2.4 Memory + index
- [x] `memory/project_phase57_51_audit_docs_hygiene_bundle.md` subfile (~3KB quality pointer; subfile link + topic + keywords per Sprint Closeout Policy)
- [x] MEMORY.md pointer entry inserted at TOP of §Project — Recent Sprints

### 2.5 CLAUDE.md
- [x] Current Sprint row updated (Sprint 57.50 → Sprint 57.51; navigator-only per Sprint Closeout Policy)
- [x] Last Updated footer updated (Sprint 57.51 closeout note)

### 2.6 next-phase-candidates.md (REFACTOR-001 single-source for open items)
- [x] Update `Updated` header (Sprint 57.51 closeout note; demoted Sprint 57.50 to "Previous Updated")
- [x] Append Sprint 57.51 carryover section at TOP (3 ADs closed + 4 NEW carryovers + tier-2 1st validation calibration + Top 3 candidates)

### 2.7 PR + merge (post-commit; user action)
- [ ] Push branch + open PR (🚧 awaiting user action)
- [ ] Touch `.github/workflows/backend-ci.yml` header comment IF needed (docs-only PR paths-filter workaround per Sprint 53.2.5 precedent; this sprint has 0 backend/frontend code so Backend CI + V2 Lints may not auto-fire) — verify CI fires first; if not, apply workaround
- [ ] Wait CI green
- [ ] User merges
- [ ] Local cleanup

### 2.8 Final
- [ ] Day 2 commit: `chore(sprint-57-51): Day 2 retro + closeout (mixed-multidomain-bundle 0.65 tier-2 1st validation)`
- [x] All Day 0-2.6 checklist items `[x]`; Day 2.7 PR + merge 🚧 pending user action; Day 2.8 final commit pending
