---
File: docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-10-checklist.md
Purpose: Sprint 57.10 (PIVOTED) day-by-day checklist — Frontend Convention Codification (CONVENTION.md + STYLE.md docs only).
Category: Frontend / Documentation / Process
Scope: Phase 57 / Sprint 57.10

Created: 2026-05-09 (drafted post-pivot)
Last Modified: 2026-05-09

Modification History (newest-first):
    - 2026-05-09: PIVOT from Verification Real Ship per user 2026-05-09 reality check
    - 2026-05-09 (superseded): Initial creation as Verification Real Ship (preserved in commit 6e11a9d9)

Related: sprint-57-10-plan.md (PIVOTED) / Day 0 commit 6e11a9d9 (verification ship original)
---

# Sprint 57.10 (PIVOTED) — Checklist (Frontend Convention Codification)

[See sprint-57-10-plan.md for full goal / USs / acceptance / risks / workload]

---

## Day 0.5 — Sprint Pivot + Carryover Catalog + Commit

### 0.5.1 Pivot orientation

- [ ] Read user 2026-05-09 reality-check session feedback (Q1 13 pages不夠 + Q2 convention not codified)
- [ ] Confirm pivot strategy A (keep 6e11a9d9 + replace plan/checklist with convention scope)
- [ ] Confirm 2-doc scope (CONVENTION.md + STYLE.md; NOT 3-doc + ARCHITECTURE.md per user)

### 0.5.2 Carryover catalog (3 NEW ADs to log Day 4)

- [ ] **AD-Verification-RealShip-Deferred** — full plan/checklist preserved in git commit 6e11a9d9; Phase 57.11+ candidate; backend Cat 10 ready since 54.1+55.5
- [ ] **AD-Frontend-SSE-Silent-Drop-Fix** — D-PRE-13 discovery from 6e11a9d9 progress.md; chat-v2 chatService.parseSSEFrame filters unknown verification_passed/failed events 3+ sprints (54.1 → 57.9); fix is types.ts LoopEvent union extension + KNOWN_LOOP_EVENT_TYPES set + chatStore.mergeEvent 2 case branches; ~1 hr fix; Phase 57.11+ candidate (could bundle with verification real ship)
- [ ] **AD-Convention-Drift-Audit-Cycle** — Phase 58.x periodic re-audit (every 4-6 sprints, scan latest ships for new emergent patterns NOT in CONVENTION.md/STYLE.md); analogous to Phase 55 audit cycle pattern

### 0.5.3 Re-prong (lighter than Day 0; pure-docs sprint)

- [ ] **Prong 1 Path** — Glob `frontend/CONVENTION.md` 0 results ✓ + `frontend/STYLE.md` 0 results ✓ (NEW files confirmed)
- [ ] **Prong 2 Content** — Read `.claude/rules/frontend-react.md` head 30 lines + tail 30 lines to confirm structure for cross-ref add (NOT replace)
- [ ] **Prong 3 Schema** — N/A (pure-docs sprint; no DB)

### 0.5.4 Calibration baseline

- [ ] Confirm `audit-cycle / docs / template` 0.40 baseline (2nd app after 55.2=1.10 ✅)
- [ ] Bottom-up est ~10 hr × 0.40 = ~4 hr commit; matches user 3-5 hr budget
- [ ] Document in progress.md Day 0.5 entry

### 0.5.5 Replace plan + checklist + amend progress.md

- [ ] Plan + checklist files already overwritten with convention scope (this draft + plan)
- [ ] progress.md APPEND Day 0.5 Pivot entry (do NOT replace original Day 0 entry; preserve verification ship audit trail)
- [ ] Stage: `git add docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-10-{plan,checklist}.md docs/03-implementation/agent-harness-execution/phase-57/sprint-57-10/progress.md`
- [ ] Commit: `git commit -m "chore(sprint-57-10, pivot): Frontend Convention Codification (replaces verification ship scope; preserves Day 0 commit 6e11a9d9 + 13 D-PRE)"`

---

## Day 1 — CONVENTION.md Draft (9 sections)

### 1.1 Source material gather

- [ ] Read Sprint 57.7 plan + key code touched (auth + cost-dashboard AppShell wrap)
- [ ] Read Sprint 57.8 plan + key code touched (AppShellV2 + Sidebar + UserMenu + routes.config + chat-v2 ship)
- [ ] Read Sprint 57.9 plan + key code touched (governance + 4-page TanStack migration + AuditLogViewer)
- [ ] Identify 9 emergent patterns to codify (one per CONVENTION.md section)

### 1.2 CONVENTION.md draft (9 sections)

- [ ] §1 Page Architecture Pattern — auth gate via Navigate + AppShellV2 wrap pageTitle + nested Routes for tabs (per 57.8+57.9)
- [ ] §2 features/&lt;X&gt;/ Folder Convention — types / services / hooks / components / store sub-folders + 11 範疇 mapping reference
- [ ] §3 Routing Convention — routes.config.ts single-source registry + active flag + lazy import (per 57.8 D9)
- [ ] §4 State Management Convention — Zustand UI-only post-migration (filter / form draft / modal); server state in TanStack Query (per 57.9 US-6 4-page batch)
- [ ] §5 Server State Convention (TanStack Query) — `*_QUERY_KEY_BASE = ["X", "Y"] as const` single-source export + keepPreviousData + enabled gate + refetchInterval + useMutation onSuccess invalidateQueries
- [ ] §6 API Service Convention — fetchWithAuth from authService.ts (NOT separate file) + URLSearchParams omit-undefined + throw Error with detail message
- [ ] §7 SSE Event Convention — chatStore.mergeEvent reducer single-point + KNOWN_LOOP_EVENT_TYPES set + parseSSEFrame filter; D-PRE-13 lesson (adding event = 3 edits: types.ts + KNOWN set + chatStore case)
- [ ] §8 Test Convention — Vitest unit + Playwright e2e + seedAuthJwt fixture + retryClicked flag pattern (D-PRE-15) + objectContaining for fetchWithAuth tests
- [ ] §9 File Header MHist Convention — 1-line max ≤ E501; cross-ref `.claude/rules/file-header-convention.md`

### 1.3 Day 1 self-review

- [ ] Each section has 3-5 sub-points + 1-2 code samples
- [ ] Each section cross-references source sprint
- [ ] Total ~400-500 lines (within scope)
- [ ] No content duplicates 16-frontend-design.md (which is design philosophy, not operational rules)
- [ ] Commit Day 1: `git add frontend/CONVENTION.md && git commit -m "docs(sprint-57-10, US-1): NEW frontend/CONVENTION.md (9 sections codifying 57.7+57.8+57.9 emergent patterns)"`

---

## Day 2 — STYLE.md Draft + frontend-react.md Cross-Ref

### 2.1 STYLE.md draft (8 sections)

- [ ] §1 Tailwind Utility-First — no inline styles + no custom CSS files except shadcn vars + use shadcn primitives where available
- [ ] §2 Color Tokens — token name / hex / Tailwind class table (primary / success / warning / danger / thinking / tool / memory per 16.md L249-262); preferred `text-success` not `text-[#10B981]`
- [ ] §3 Risk Badge Palette — LOW (#2e7d32 / text-green-700) / MEDIUM (#ed6c02) / HIGH (#d84315) / CRITICAL (#b71c1c) canonical table (per 53.5 governance ship)
- [ ] §4 Typography — Inter sans + JetBrains Mono code; 5 size tokens (per 16.md L264-276)
- [ ] §5 Spacing Convention — `p-4` / `p-6` page padding / `gap-2` flex / `gap-4` grid / `mb-4` section spacing
- [ ] §6 Loading Skeleton Pattern — 5-row table skeleton (per 57.9 ApprovalList) + 3-card skeleton; canonical Tailwind classes
- [ ] §7 Empty State Pattern — center message + Reset/Retry button (per 57.9 governance + admin-tenants); canonical layout
- [ ] §8 Error Retry UX Pattern — error message + Retry button + retryClicked flag for StrictMode mock (D-PRE-15 codified)

### 2.2 frontend-react.md cross-ref update

- [ ] Add NEW section "## Detailed Conventions" near end of `.claude/rules/frontend-react.md`
- [ ] Cross-reference: "For comprehensive frontend convention rules, see `frontend/CONVENTION.md`"
- [ ] Cross-reference: "For style + visual rules, see `frontend/STYLE.md`"
- [ ] Existing 85 lines of basic rules retained (do NOT delete)
- [ ] Verify ESLint silent + tsc strict 0 errors (no code changed but defensive)

### 2.3 Day 2 commit

- [ ] Commit: `git add frontend/STYLE.md .claude/rules/frontend-react.md && git commit -m "docs(sprint-57-10, US-2+US-3 partial): NEW frontend/STYLE.md (8 sections) + frontend-react.md cross-ref to NEW docs"`

---

## Day 3 — Self-review + Cross-ref Polish + Early Validation

### 3.1 Self-review both docs

- [ ] CONVENTION.md ≥ 400 lines + 9 sections + cross-refs valid
- [ ] STYLE.md ≥ 300 lines + 8 sections + color/risk tables complete
- [ ] D-PRE-13 SSE silent drop lesson explicitly codified in CONVENTION.md §7
- [ ] D-PRE-15 StrictMode mock pattern explicitly codified in CONVENTION.md §8 + STYLE.md §8
- [ ] D9 Sprint 57.8 page-level h1 lesson codified in CONVENTION.md §1

### 3.2 Cross-ref polish

- [ ] CONVENTION.md cross-refs to STYLE.md where overlap (e.g. §1 "see STYLE.md §3 risk palette for Tailwind class equivalents")
- [ ] STYLE.md cross-refs to CONVENTION.md where overlap
- [ ] Both docs have proper frontmatter (File / Purpose / Category / Created / MHist / Related)

### 3.3 Early validation sweep (defensive — no code changed but sentinel)

- [ ] pytest baseline maintained: `cd backend && python -m pytest --co -q | tail -3` → expect 1622
- [ ] Vitest baseline maintained: `cd frontend && npm run test -- --run 2>&1 | tail -3` → expect 93
- [ ] Playwright baseline: `cd frontend && npx playwright test --list 2>&1 | tail -3` → expect 27 specs
- [ ] V2 lints: `python scripts/lint/run_all.py` → 9/9 green
- [ ] tsc strict: `cd frontend && npx tsc --noEmit` → 0 errors

---

## Day 4 — Retro + Memory + 4 Doc Syncs + PR

### 4.1 Full validation sweep (BLOCKER for Day 4 commit)

- [ ] Backend: pytest 1622 / mypy strict 0 / black + isort + flake8 silent
- [ ] Frontend: Vitest 93 / tsc 0 / ESLint silent / Vite build clean
- [ ] V2 lints 9/9
- [ ] LLM SDK leak 0
- [ ] Playwright 27 pass

### 4.2 Retrospective.md (Q1-Q7 mandatory format per Sprint 57.7+57.8+57.9)

- [ ] Create `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-10/retrospective.md` Q1-Q7:
  - Q1 What went well? (pivot speed / convention codify ROI)
  - Q2 Calibration ratio = actual / committed; log `audit-cycle / docs / template` 0.40 2-data-point mean update
  - Q3 What didn't go well? (over-document risk / cross-ref staleness)
  - Q4 What carryover ADs? (3 NEW: Verification-RealShip-Deferred / Frontend-SSE-Silent-Drop-Fix / Convention-Drift-Audit-Cycle)
  - Q4.1 Update 16.md cross-ref to NEW docs
  - Q5 Phase 57.11+ direction — list 5 candidates per rolling planning 紀律 (verification-realship MOST LIKELY first since deferred this sprint)
  - Q6 V2 紀律 9 項 self-check
  - Q7 Spike sprint design note? (N/A SKIP — pure docs sprint NOT spike)

### 4.3 Memory snapshot

- [ ] Create `C:\Users\Chris\.claude\projects\C--Users-Chris-Downloads-ai-semantic-kernel-framework-project\memory\project_phase57_10_convention_codify.md`
  - Frontmatter: name / description / type=project
  - Body: pivot context + 2 docs created + 3 carryover ADs + calibration validation
- [ ] Update `MEMORY.md` index +1 line entry under ~150 chars

### 4.4 Doc syncs (3/4; CLAUDE.md deferred to post-merge closeout PR per 57.7+57.8+57.9 pattern)

- [ ] Update `.claude/rules/sprint-workflow.md` §Calibration matrix:
  - Add 1 row: `audit-cycle / docs / template` 0.40 2nd data point 57.10=X.XX
  - Update mean (55.2=1.10 + 57.10=X.XX → 2-data mean Y.YY)
- [ ] Update `claudedocs/6-ai-assistant/prompts/SITUATION-V2-SESSION-START.md`:
  - §9 milestones table: NEW row Sprint 57.10 entry (PIVOTED)
  - §11 (or wherever Open Items live): NEW carryover ADs
- [ ] Update `docs/03-implementation/agent-harness-planning/16-frontend-design.md`:
  - Add cross-reference at top (or near §Design System): "**Operational rules** for frontend dev → `frontend/CONVENTION.md` + `frontend/STYLE.md` (Sprint 57.10 codified)"
  - Note: 16.md remains design philosophy + page roadmap; new docs are operational rules
- [ ] CLAUDE.md sync DEFERRED to post-merge closeout PR per Sprint 57.7+57.8+57.9 pattern

### 4.5 PR open + closeout sync

- [ ] Commit Day 4: `git add . && git commit -m "feat(sprint-57-10, US-3 + closeout): cross-refs + frontend-react.md update + 3 doc syncs + retrospective + memory"`
- [ ] Push branch: `git push -u origin feature/sprint-57-10-verification-real-ship` (NOTE: branch name is verification-real-ship from pre-pivot; can rename or accept; mention in PR title)
- [ ] Open PR via `gh pr create` with title "Sprint 57.10 (PIVOTED) — Frontend Convention Codification (CONVENTION.md + STYLE.md NEW; verification real ship deferred to AD-Verification-RealShip-Deferred)" + body summary explaining pivot
- [ ] After PR merge to main, capture main HEAD SHA
- [ ] Open closeout PR with CLAUDE.md sync (per Sprint 57.7+57.8+57.9 pattern)
- [ ] Merge closeout PR → main
- [ ] Update memory snapshot with merged main HEAD SHA

### 4.6 Day 4 closeout user decision points

- [ ] Confirm with user: Phase 57.11+ scope direction per Q5 retrospective (5 candidates including verification-realship + agent-harness-UI-suite + Tier 1 IaC + Status Page + SOC 2)
- [ ] Confirm with user: 3 NEW carryover ADs need immediate attention vs Phase 57.x deferred

---

## 重要備註

### Rolling planning 紀律自檢

- ☐ 沒預寫 Phase 57.11+ plan/checklist
- ☐ 沒跳過 plan/checklist 直接 code (this sprint = pure docs)
- ☐ 沒刪除未勾選的 [ ] 項目
- ☐ 沒在 retrospective.md Q5 寫具體 Phase 57.11 task (只列 5 candidates 等 user 選定)

### V2 紀律 9 項自檢

1. N/A Server-Side First (pure docs)
2. N/A LLM Provider Neutrality (no code)
3. N/A CC Reference 不照搬
4. N/A 17.md Single-source (no NEW contracts)
5. N/A 11+1 範疇 (frontend convention only)
6. ✅ 04 anti-patterns — AP-2 no orphan (deferred work logged as AD) + AP-4 no Potemkin (real codification not stub) + AP-6 YAGNI (2 docs not 3)
7. ✅ Sprint workflow — pivot replaced plan + checklist; Day 0.5 commit preserves audit trail; checklist execution per Day 1-4
8. ✅ File header convention — both NEW docs follow MHist 1-line max
9. N/A Multi-tenant rule (no data layer change)

### Sprint 57.10 pivot lesson 強制執行(此 sprint 必行)

- **Preserve Day 0 commit 6e11a9d9** — verification ship plan + 13 D-PRE findings remain in git history; AD-Verification-RealShip-Deferred references commit SHA for re-pickup
- **D-PRE-13 standalone fix promoted to dedicated AD** — AD-Frontend-SSE-Silent-Drop-Fix is ~1 hr Phase 57.11+ candidate; could bundle with verification ship re-pickup OR ship standalone first

### Open Items / Carry-forward(填入 retrospective Q4)

- 🚧 **AD-Verification-RealShip-Deferred** — full plan/checklist preserved in commit 6e11a9d9; Phase 57.11+ candidate
- 🚧 **AD-Frontend-SSE-Silent-Drop-Fix** — D-PRE-13 ~1 hr; Phase 57.11+ candidate
- 🚧 **AD-Convention-Drift-Audit-Cycle** — Phase 58.x periodic
- 🚧 (其他 Day 4 retrospective Q4 catalogued ADs)

---

**End of Sprint 57.10 (PIVOTED) Checklist**
