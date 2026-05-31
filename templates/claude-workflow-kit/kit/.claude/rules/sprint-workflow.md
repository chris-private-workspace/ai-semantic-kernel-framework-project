# Sprint Workflow Rules

**Purpose**: Enforce sprint execution discipline so scope is explicit, traceable, and reviewable.
**Category**: Development Process
**Status**: Active

---

## Overview

This document enforces a **mandatory 5-step sprint flow**. Skipping plan + checklist leads to scattered implementation, unclear PR scope, and blind retrospectives.

**Golden Rule**:
```
Sprint Plan → Sprint Checklist → Day-0 Verify → Code → Update Checklist → Progress Doc
```

---

## Step 1: Create Plan File

**Before writing any code**, create `docs/sprints/sprint-XX-Y-plan.md`.

**Required sections** (mirror the most recent completed sprint's plan for format consistency):
- **Sprint Goal**: one sentence — what does this sprint deliver?
- **User Stories**: 3-5 in "As a / I want / So that" format
- **Technical Specifications**: design decisions + rationale
- **File Change List**: explicit list of files to create/modify (with counts)
- **Acceptance Criteria**: measurable, testable definition of done
- **Deliverables**: `- [ ]` checkbox list mapping to stories
- **Workload**: estimate (see calibration below)
- **Dependencies & Risks**: what could block + mitigation

> **Format consistency**: read the *most recent completed* sprint plan first and mirror its section count / naming / detail level. Express scope differences through **content** (more stories / files), not **structure** (don't add/rename sections).

### Workload Calibration

State the estimate in this form:

> Bottom-up est ~X hr → calibrated commit ~Y hr (multiplier Z)

- **X** = sum of raw per-task estimates
- **Z** = calibration multiplier, default **0.6** (start here; bottom-up estimates tend to over-shoot)
- **Y** = X × Z = what you actually commit to

**Adjusting Z** (3-sprint moving evidence; ignore single outliers):
- 3+ consecutive sprints with `actual/committed > 1.2` → raise Z (under-estimating)
- 3+ consecutive sprints with `actual/committed < 0.7` → lower Z (buffer too generous)

The Day-N / sprint-end retrospective recomputes `actual/committed` to verify Z.

---

## Step 2: Create Checklist File

Immediately after plan approval, create `docs/sprints/sprint-XX-Y-checklist.md`.

```markdown
# Sprint XX.Y — Checklist

[link to plan]

## Day N — Task Group

### N.M Task Description
- [ ] **Specific deliverable**
  - DoD: measurable definition of done
  - Verify: `<command>`
```

**Rules**:
- Use `- [ ]` format; one logical unit per checkbox
- Each task has a DoD + a verify command
- Map each task to a plan acceptance criterion
- **Do NOT put time estimates in the checklist** — per-day actuals go in `progress.md`; sprint-aggregate calibration lives in the plan §Workload only

**Sacred rule**: only change `[ ]` → `[x]`. **Never delete** unchecked items (that hides scope cuts). If scope is cut, leave `[ ]` and note the reason in `progress.md`.

---

## Step 2.5: Day-0 Plan-vs-Repo Verify

**Mandatory** between drafting and Day-1 code. Plans drafted from memory drift from the real repo (renamed classes, moved files, changed signatures, schema deltas). Catch drift in ~30 min at Day 0 instead of paying hours of mid-sprint rework.

Run a **grep/glob pass** over every claim in the plan:

1. **Path verify** — every file path in §File Change List: confirm new files don't exist yet; edited files do exist.
2. **Content verify** — every factual claim about existing code ("X is unused", "Y class extends Z", "consumer imports A"): grep the symbol/pattern to confirm. Path existing ≠ body matching the claim.
3. **Schema verify** (when DB schema in scope) — every new table/column/migration: grep the actual model/migration to confirm name + type + nullable; confirm the next migration number isn't taken.

**Catalog findings** in `progress.md` under a "Drift findings" header (`D1`, `D2`, …) and cross-reference plan §Risks. **Do NOT silently rewrite the plan** — add findings to §Risks to preserve the audit trail of planned-vs-actual.

**Go/no-go**:
- scope shift ≤ 20% → continue, note risk
- 20-50% → revise plan §Acceptance + §Workload, re-confirm
- > 50% → abort + redraft from reality baseline

---

## Step 3: Implement Code

Only after plan + checklist + Day-0 verify exist.

1. Create feature branch: `git checkout -b feature/sprint-XX-Y-<scope>`
2. Code against checklist deliverables, one at a time
3. Commit per logical unit

**Prohibited**: starting code before plan/checklist; committing without a checklist entry; scope creep without updating plan + checklist.

---

## Step 4: Update Checklist During Implementation

- As you complete: `[ ]` → `[x]` (change, never delete)
- If blocked: add `🚧 blocked: <reason>` below the task; continue elsewhere or escalate
- Commit checklist updates daily

---

## Step 5: Progress & Retrospective

**Daily** — update `docs/sprints/sprint-XX-Y/progress.md`:
```markdown
# Sprint XX.Y Progress — YYYY-MM-DD
## Today's Accomplishments
- Task X.Y — actual Z min (est ~W min, delta ±N%)
## Remaining for Next Day
## Notes (learnings / decisions / risks)
```

**Sprint end** — create `retrospective.md`: did well / improve next / action items + estimate accuracy (`actual/committed` ratio to verify the multiplier).

---

## Change Record Conventions

When fixing bugs or changing features, create a record in `claudedocs/4-changes/`:

| Type | Directory | Naming |
|------|-----------|--------|
| Bug Fix | `4-changes/bug-fixes/` | `FIX-XXX-description.md` |
| Feature Change | `4-changes/feature-changes/` | `CHANGE-XXX-description.md` |
| Refactoring | `4-changes/refactoring/` | `REFACTOR-XXX-description.md` |

Templates live in `claudedocs/templates/`.

---

## Before Commit Checklist

1. **Corresponds to a checklist task** (message matches task ID)
2. **Format + lint + type + test pass**:
   - `{{FORMAT_CMD}}`
   - `{{LINT_CMD}}` (do NOT use `--silent` — it can swallow lint errors)
   - `{{TYPECHECK_CMD}}`
   - `{{TEST_CMD}}`
   - `python scripts/lint/run_all.py` (project-specific architecture lints)
3. **Anti-patterns checklist** passes (`anti-patterns-checklist.md`)
4. **File headers updated** (`file-header-convention.md`)

---

## Prohibited Actions

- ❌ Force push to {{DEFAULT_BRANCH}}
- ❌ Commit without a corresponding checklist entry
- ❌ Delete unchecked `[ ]` items from the checklist
- ❌ Skip `progress.md` updates (update daily)
- ❌ Skip FIX/CHANGE/REFACTOR records for bug/feature changes
- ❌ Code before plan + checklist exist
- ❌ Commit secrets, large binaries, generated files
- ❌ Scope creep without updating the plan

---

## Common Violation Patterns

| Pattern | Why bad | Fix |
|---------|---------|-----|
| Skip plan | Unknown scope → rework | Always plan → checklist → code |
| Delete `[ ]` items | Hides scope cuts; retro can't diagnose | Only mark `[x]` or note `[blocked]` |
| Update checklist after sprint | Data quality → estimates useless | Update daily, during work |
| Skip progress.md | Details lost; weak retro | 10-min daily entry |
| Vague DoD | Infinite rework | DoD: testable + measurable |
| Format inconsistency | Hard to navigate | Mirror prior sprint's structure |
