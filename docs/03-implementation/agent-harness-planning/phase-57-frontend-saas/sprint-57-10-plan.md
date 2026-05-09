---
File: docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-10-plan.md
Purpose: Sprint 57.10 plan — Frontend Convention Codification (CONVENTION.md + STYLE.md docs only; stop convention drift before next feature ship).
Category: Frontend / Documentation / Process
Scope: Phase 57 / Sprint 57.10

Description:
    PIVOT from original Verification Real Ship scope (preserved in git history
    of Day 0 commit `6e11a9d9`) per 2026-05-09 user reality-check session.
    Frontend has 7 ship pages + 14 features/* folders but ZERO codified
    convention docs — page architecture / state mgmt / TanStack pattern /
    SSE event handling / test pattern all live as "documented-by-precedent"
    (each new sprint must read most-recent shipped sprint plan to absorb).

    Risk: as pages multiply (10+ planned per 16.md), convention drift
    accelerates. D-PRE-13 caught Sprint 57.10 Day 0 (chat-v2 silently
    dropping verification SSE 3+ sprints) is exactly this drift symptom.

    Sprint 57.10 codifies emergent patterns from Sprint 57.7+57.8+57.9 ships
    into 2 docs: `frontend/CONVENTION.md` (architecture / state / SSE / test)
    + `frontend/STYLE.md` (Tailwind / color tokens / typography / UX).

    Verification real ship work deferred to AD-Verification-RealShip-Deferred
    (full plan/checklist preserved in commit 6e11a9d9 — re-pickup after
    convention codification done). D-PRE-13 SSE silent drop bug logged as
    standalone AD-Frontend-SSE-Silent-Drop-Fix (~1 hr fix; Phase 57.11+
    candidate).

Created: 2026-05-09 (drafted post-pivot)
Last Modified: 2026-05-09
Status: Draft (pending user approval pre-Day-0.5 commit)

Modification History (newest-first):
    - 2026-05-09: PIVOT from Verification Real Ship per user 2026-05-09 reality
      check — frontend convention drift identified; replace plan+checklist
      while preserving Day 0 commit 6e11a9d9 audit trail
    - 2026-05-09 (superseded): Initial creation as Verification Real Ship
      (preserved in git history of commit 6e11a9d9)

Related:
    - 16-frontend-design.md §Page 規劃 + §Features 目錄 + §Design System
    - sprint-57-9-plan.md (structural template per sprint-workflow.md §Step 1)
    - .claude/rules/frontend-react.md (current ~85-line rules; will reference NEW docs)
    - Day 0 commit 6e11a9d9 (Verification Real Ship plan + 13 D-PRE — preserved)
---

# Sprint 57.10 (PIVOTED) — Frontend Convention Codification

## Sprint Goal

Codify emergent frontend patterns from Sprint 57.7+57.8+57.9 ships into
**2 NEW docs** — `frontend/CONVENTION.md` (page architecture / features
folder / TanStack Query / Zustand UI-only / fetchWithAuth / SSE event /
test patterns) + `frontend/STYLE.md` (Tailwind utility-first / color tokens
/ risk badge palette / typography / spacing / loading-empty-error UX) —
stopping the documented-by-precedent drift that contributed to D-PRE-13
(chat-v2 silently dropping verification SSE events 3+ sprints) and similar
D-PRE-15 (StrictMode mock pattern brittleness).

---

## Background

### Why this pivot now

User 2026-05-09 reality-check session identified two structural gaps:

1. **Frontend page coverage drift** — 13 planned pages (per 16.md) shrunk to
   7 actual ship + 1 placeholder = 8/13. Of the 4 NOT-in-original-plan ships
   (cost / sla / tenant-settings / SaaS admin), all replaced agent-harness
   UI components (LoopVisualizer / MemoryViewer / SubagentTree / DevUI suite)
   that 16.md L159-220 planned. Original "11 範疇 transparent UI" vision
   < 30% realized.

2. **Frontend convention not documented** — `frontend/STYLE.md` and
   `frontend/CONVENTION.md` do NOT exist. Only `.claude/rules/frontend-react.md`
   (~85 lines) covers basic React rules. Page architecture / Zustand-TanStack
   split / SSE chatStore.mergeEvent reducer / `*_QUERY_KEY_BASE` single-source
   / `fetchWithAuth` / StrictMode mock pattern are all emergent precedent
   from 57.7-57.9 ships, never codified.

### What changed since Sprint 57.9

| Asset | 57.9 ship state | 57.10 needs |
|-------|-----------------|------------|
| `frontend/CONVENTION.md` | ❌ does NOT exist | NEW: ~400-500 lines codifying 9 convention areas |
| `frontend/STYLE.md` | ❌ does NOT exist | NEW: ~300-400 lines codifying 8 style areas |
| `.claude/rules/frontend-react.md` | 85 lines basic rules | UPDATE: add cross-ref to 2 NEW docs (do NOT duplicate content) |
| Sprint 57.10 verification ship plan | ✅ committed at 6e11a9d9 | DEFERRED to AD-Verification-RealShip-Deferred (preserved in git history) |
| D-PRE-13 SSE silent drop discovery | catalogued in 6e11a9d9 progress.md | NEW carryover AD-Frontend-SSE-Silent-Drop-Fix (~1 hr Phase 57.11+ candidate) |

### Why `audit-cycle / docs / template` 0.40 calibration

Per sprint-workflow.md §Calibration matrix:
- 55.2 evidence: ratio 1.10 ✅ in [0.85, 1.20] band
- 2nd application this sprint validates baseline
- Pure-docs sprints have no integration / e2e overhead → low multiplier appropriate

---

## User Stories

### US-1 (greenfield) — frontend/CONVENTION.md NEW

**As a** frontend developer joining the project (or returning AI session)
**I want** a single canonical doc explaining HOW pages are structured + HOW
state flows + HOW SSE events route + HOW tests are written
**So that** I don't have to grep 6-8 sprint commits to absorb the emergent
convention; convention drift halts at Sprint 57.10

**Acceptance**:
- File `frontend/CONVENTION.md` created with 9 sections:
  1. **Page Architecture Pattern** — auth gate via Navigate to /auth/login + setPostLoginRedirect / AppShellV2 wrap with pageTitle / nested Routes (per 57.8+57.9 ship)
  2. **features/&lt;X&gt;/ Folder Convention** — types / services / hooks / components / store sub-folders; 11 範疇 mapping (some folders are stubs; 16.md L159-220 reference)
  3. **Routing Convention** — `routes.config.ts` single-source registry + active flag + lazy import via `component: () => import("./pages/X")` (per 57.8 D9 architectural fix)
  4. **State Management Convention** — Zustand stores reduced to UI-only (filter / form draft / modal state); server state goes to TanStack Query (per 57.9 US-6 4-page batch migration)
  5. **Server State Convention (TanStack Query)** — `*_QUERY_KEY_BASE = ["X", "Y"] as const` single-source export pattern + `keepPreviousData` for paginated queries + `enabled: !!sessionId` gate pattern + `refetchInterval` for polling + `useMutation` with `onSuccess: invalidateQueries` (per 57.9 US-3+US-6)
  6. **API Service Convention** — `fetchWithAuth` from `features/auth/services/authService.ts` (NOT separate file) + URLSearchParams omit-undefined helper + throw Error with detail message on non-2xx (per 57.7 IAM ship)
  7. **SSE Event Convention** — chatStore.mergeEvent reducer single-point switch on ev.type + KNOWN_LOOP_EVENT_TYPES set + chatService.parseSSEFrame filters unknown events (so adding NEW event variant requires 3 edits: types.ts union + KNOWN set + chatStore case branch). D-PRE-13 lesson codified here.
  8. **Test Convention** — Vitest unit tests in `tests/unit/<feature>/` mirror src structure / Playwright e2e in `tests/e2e/<feature>-real-ship.spec.ts` / seedAuthJwt fixture in beforeEach for auth-gated pages (per 57.9 D-PRE-16 lesson) / retryClicked flag pattern for StrictMode mock retry (per 57.9 D-PRE-15) / `expect.objectContaining({ credentials: "include" })` for fetchWithAuth wrapped service tests
  9. **File Header MHist Convention** — 1-line max ≤ E501 budget per `.claude/rules/file-header-convention.md` Sprint 55.3+ rule; cross-reference for completeness
- Each section has 3-5 sub-points + 1-2 code samples + cross-reference to source sprint
- Total ~400-500 lines

### US-2 (greenfield) — frontend/STYLE.md NEW

**As a** frontend developer building UI
**I want** a single canonical doc explaining color tokens / typography /
spacing / standard UX patterns (loading skeleton / empty state / error retry)
**So that** new components don't introduce drift (e.g. 57.9 used arbitrary
`text-[#2e7d32]` instead of color token → AD-StyleDrift potential)

**Acceptance**:
- File `frontend/STYLE.md` created with 8 sections:
  1. **Tailwind Utility-First** — no inline styles per .claude/rules/frontend-react.md / no custom CSS files except shadcn vars / use shadcn primitives where available
  2. **Color Tokens** — token names + hex values + Tailwind class equivalents (primary / success / warning / danger / thinking / tool / memory per 16.md L249-262); preferred: `text-success` not `text-[#10B981]`
  3. **Risk Badge Palette** — LOW (#2e7d32 / text-green-700) / MEDIUM (#ed6c02 / text-orange-600) / HIGH (#d84315 / text-orange-800) / CRITICAL (#b71c1c / text-red-800) per 53.5 governance ship; canonical class names
  4. **Typography** — Inter sans + JetBrains Mono code; 5 size tokens (text-xs / text-sm / text-base / text-lg / text-xl) per 16.md L264-276
  5. **Spacing Convention** — `p-4` / `p-6` page padding / `gap-2` flex / `gap-4` grid / `mb-4` section spacing baseline
  6. **Loading Skeleton Pattern** — 5-row table skeleton (per 57.9 ApprovalList) / 3-card skeleton; canonical Tailwind classes
  7. **Empty State Pattern** — 中央 message + Reset / Retry button (per 57.9 governance + admin-tenants); canonical layout
  8. **Error Retry UX Pattern** — error message + Retry button + retryClicked flag for StrictMode mock idempotency (per 57.9 D-PRE-15 codified)
- Each section has 2-3 sub-points + code/markup samples
- Total ~300-400 lines

### US-3 (mechanical) — Cross-references + frontend-react.md update + closeout

**As a** project consistency reviewer
**I want** `.claude/rules/frontend-react.md` to point at NEW docs (not
duplicate content) and Sprint 57.10 closeout includes 4 doc syncs
**So that** future AI session reading rules finds the codified convention
through single-source references

**Acceptance**:
- `.claude/rules/frontend-react.md` adds NEW section "Detailed Conventions" with cross-reference: `See frontend/CONVENTION.md` + `See frontend/STYLE.md`
- Existing 85 lines of basic rules retained (do NOT delete; coexist with new section)
- 4 doc syncs Day 4 closeout (per Sprint 57.7+57.8+57.9 pattern):
  - sprint-workflow.md §Calibration matrix +1 row `audit-cycle / docs / template` 0.40 2nd data point
  - SITUATION-V2 §9 + §11 NEW entry
  - 16-frontend-design.md gets cross-reference link to NEW frontend/CONVENTION.md + frontend/STYLE.md (16.md remains "design philosophy"; new docs are "operational rules")
  - CLAUDE.md sync deferred to post-merge closeout PR (per 57.7+57.8+57.9 pattern)
- 3 NEW carryover ADs logged Q4 retrospective:
  - AD-Verification-RealShip-Deferred (full plan in commit 6e11a9d9; re-pickup after convention codify)
  - AD-Frontend-SSE-Silent-Drop-Fix (D-PRE-13 ~1 hr fix; Phase 57.11+ candidate)
  - AD-Convention-Drift-Audit-Cycle (Phase 58.x periodic re-audit conventions vs latest sprints)

---

## Technical Specifications

### CONVENTION.md sample structure

```markdown
# Frontend Convention

> Operational rules for frontend development. For design philosophy / page
> roadmap, see `docs/03-implementation/agent-harness-planning/16-frontend-design.md`.

## 1. Page Architecture Pattern

Every authenticated page wraps in this 3-layer composition (per Sprint 57.8+57.9):

```tsx
import { Navigate } from "react-router-dom";
import { AppShellV2 } from "@/components/AppShellV2";
import { isAuthenticated, setPostLoginRedirect } from "@/features/auth/services/authService";

export default function MyPage(): JSX.Element {
  if (!isAuthenticated()) {
    setPostLoginRedirect("/my-page");
    return <Navigate to="/auth/login" replace />;
  }
  return (
    <AppShellV2 pageTitle="My Page">
      {/* page content */}
    </AppShellV2>
  );
}
```

**Sub-routes**: For pages with tabs (governance / verification), use nested
Routes inside the AppShellV2 (per Sprint 57.9 governance pattern):

```tsx
<AppShellV2 pageTitle="Verification">
  <nav className="mb-4 flex gap-2 border-b border-border"> ... </nav>
  <Routes>
    <Route index element={<Navigate to="recent" replace />} />
    <Route path="recent" element={<RecentTab />} />
    <Route path="timeline" element={<TimelineTab />} />
  </Routes>
</AppShellV2>
```

**Lesson**: Page-level h1 ownership lives in AppShellV2 pageTitle. Inner
components MUST NOT render h1 to avoid cascade conflict (per Sprint 57.8 D9
architectural fix on SLAOverview + TenantSettingsView).

## 2. features/<X>/ Folder Convention

[similar detail level for each section]

[... 7 more sections ...]
```

### STYLE.md sample structure

```markdown
# Frontend Style Guide

> Visual + UX rules. For convention rules (architecture / state / test), see
> `frontend/CONVENTION.md`.

## 1. Tailwind Utility-First

[detailed rules]

## 2. Color Tokens

| Token | Hex | Tailwind class | Usage |
|-------|-----|----------------|-------|
| primary | #3B82F6 | text-primary / bg-primary | Main actions |
| success | #10B981 | text-success / bg-success | Verified / approved |
[... full table ...]

[... 7 more sections ...]
```

---

## File Change List

### Frontend NEW (2 files)

- `frontend/CONVENTION.md` (~400-500 lines)
- `frontend/STYLE.md` (~300-400 lines)

### Project MODIFY (1 file)

- `.claude/rules/frontend-react.md` (add NEW "Detailed Conventions" cross-reference section; existing 85 lines retained)

### Docs UPDATE (4 files; Day 4 closeout)

- `.claude/rules/sprint-workflow.md` (+1 row to Calibration matrix `audit-cycle` 2nd data point)
- `claudedocs/6-ai-assistant/prompts/SITUATION-V2-SESSION-START.md` (§9 + §11 NEW entry)
- `docs/03-implementation/agent-harness-planning/16-frontend-design.md` (cross-reference NEW operational docs)
- `CLAUDE.md` (post-merge closeout PR per 57.7+57.8+57.9 pattern)

---

## Acceptance Criteria

### US-1 (CONVENTION.md)

- ✅ File created with 9 sections + code samples + cross-references to source sprints
- ✅ Total ≥ 400 lines (codify scope is broad; under-document risks future drift)
- ✅ Each section has 3-5 sub-points + 1-2 examples
- ✅ D-PRE-13 SSE silent drop lesson explicitly codified in §7
- ✅ D-PRE-15 StrictMode mock pattern explicitly codified in §8
- ✅ Sprint 57.8 D9 page-level h1 lesson codified in §1

### US-2 (STYLE.md)

- ✅ File created with 8 sections + code/markup samples
- ✅ Total ≥ 300 lines
- ✅ Color token table includes hex + Tailwind class equivalents (NOT just hex)
- ✅ Risk badge palette explicit table (canonical 53.5 ship values)

### US-3 (Cross-refs + closeout)

- ✅ `.claude/rules/frontend-react.md` adds cross-reference section without deleting existing content
- ✅ 4 doc syncs Day 4 closeout
- ✅ 3 NEW carryover ADs logged in retrospective.md Q4

### Sprint-wide

- ✅ pytest baseline maintained: 1622 passed (NO backend changes; sentinel)
- ✅ Vitest baseline maintained: 93 passed (NO frontend code changes; sentinel)
- ✅ Playwright baseline maintained: 27 specs passing
- ✅ V2 lints 9/9 green
- ✅ tsc strict 0 errors
- ✅ Vite build clean (no main chunk change expected)
- ✅ LLM SDK leak 0
- ✅ NEW docs pass markdown linting (if any) + line length within 100 chars where possible

---

## Deliverables (checklist mapping)

- [ ] US-1 — CONVENTION.md NEW (sprint-57-10-checklist.md §1.1-1.3)
- [ ] US-2 — STYLE.md NEW (§2.1-2.2)
- [ ] US-3 — Cross-refs + frontend-react.md update + closeout (§3.1 + §4.1-4.7)
- [ ] Day 0.5 — Pivot orientation + carryover catalog + commit (§0.5)
- [ ] Day 4 — Retro + memory + 4 doc syncs + PR (§4.1-4.7)

---

## Dependencies & Risks

### Dependencies

1. **Sprint 57.7+57.8+57.9 ships** — codified patterns originate from these 3 sprints; must read their plan/checklist/code as source material
2. **16-frontend-design.md** — design philosophy reference (do NOT duplicate; cross-reference)
3. **.claude/rules/frontend-react.md** — basic rules baseline (extend, don't replace)

### Risks

| # | Risk | Likelihood | Mitigation |
|---|------|------------|------------|
| A | CONVENTION.md becomes 800+ line monster (over-document) | MEDIUM | Hard cap at 9 sections; if section grows past 80 lines, split sub-doc OR push detail to inline code samples |
| B | STYLE.md duplicates Tailwind official docs | LOW | Focus on PROJECT-SPECIFIC rules (color tokens / risk palette / standard patterns) NOT Tailwind syntax |
| C | Cross-references go stale fast (sprint references rot) | MEDIUM | Use generic phrasing "per Sprint 57.X ship pattern" + content snippet; avoid dependency on commit SHA |
| D | Convention codified is wrong (premature) | MEDIUM | Each codified pattern MUST point to ≥ 2 sprint examples (57.7 + 57.9 / 57.8 + 57.9) NOT single-data-point |
| E | scope creep (user wants ARCHITECTURE.md added) | LOW | User pre-confirmed 2 docs; reject 3rd doc; defer to AD-Frontend-Architecture-Codification if needed |
| F | Sprint 57.10 ratio > 1.20 (under-estimated docs work) | MEDIUM | Day 4 retro Q2; if > 1.20 → AD-Sprint-Plan-12 propose lift `audit-cycle` 0.40 → 0.50 |
| G | Verification real ship deferred indefinitely | LOW | AD-Verification-RealShip-Deferred preserves full plan in git 6e11a9d9; re-pickup Phase 57.11+ first candidate |

### Sprint 57.7 + 57.8 + 57.9 lesson carry-forward

- **Plan/checklist format consistency** — Sprint 57.10 plan mirrors Sprint 57.9 9-section structure (with shorter content per pure-docs sprint)
- **Day 0 三-prong** — Day 0.5 quick re-prong (Path verify CONVENTION.md/STYLE.md don't exist; Content verify frontend-react.md current content; Schema N/A — no DB)
- **MHist 1-line max** — both NEW docs follow file-header-convention.md Sprint 55.3+ rule
- **Day 4 closeout 4 doc syncs** — sprint-workflow.md / SITUATION-V2 / 16.md / CLAUDE.md (deferred PR)

---

## Workload (calibrated)

### Bottom-up estimate

| Day | Task | Bottom-up |
|-----|------|-----------|
| 0.5 | Pivot orientation + carryover catalog + commit (replace plan/checklist) | 1 hr |
| 1 | CONVENTION.md draft (9 sections) | 4 hr |
| 2 | STYLE.md draft (8 sections) + frontend-react.md cross-ref | 2.5 hr |
| 3 | Self-review + cross-ref polish + early validation sweep | 1 hr |
| 4 | Retro Q1-Q7 + memory + 4 doc syncs + PR + closeout | 1.5 hr |
| **Total** | | **~10 hr** |

### Calibration: `audit-cycle / docs / template` 0.40 (2nd data point)

- Bottom-up ~10 hr × 0.40 = **~4 hr commit** (matches user's 3-5 hr budget)
- 55.2 1st app ratio 1.10 ✅ in [0.85, 1.20] band
- KEEP 0.40 baseline; Day 4 retro Q2 logs 2nd data point
- If 2-data-point mean stays in band → KEEP 0.40 for Phase 58.x audit cycles

---

## Open questions for user (pending plan approval)

✅ All 4 pivot questions PRE-CONFIRMED in chat session 2026-05-09:

| Q | User answer |
|---|-------------|
| Pivot Strategy | (A) Keep Day 0 commit + pivot 說明 |
| Doc count | (2 docs) CONVENTION.md + STYLE.md |
| Calibration class | `audit-cycle / docs / template` 0.40 |
| Phase 57.11+ hint | Don't pre-commit (rolling planning 紀律) |

**No outstanding questions.** Ready for plan + checklist review + Day 0.5 commit.

---

**End of Sprint 57.10 (PIVOTED) Plan**
