# Sprint 57.51 — Audit/Docs Hygiene Bundle (Triple-AD Bundle, 3 Tracks)

**Phase**: 57+ Frontend SaaS (audit-cycle / docs / template class — non-feature hygiene wave)
**Goal**: Close 3 carryover ADs from Sprint 57.48-50 trail in single bundled sprint — Track A `AD-Lint-Detector-Code-Aware-Masking-Rule` (Sprint 57.48 D-DAY0-6 codification) + Track B `AD-Plan-Risk-ORM-File-Path-Reference-Style` #82 (Sprint 57.50 D-DAY0-2 codification) + Track C `AD-Sprint-57.49-HEX_OKLCH-Silent-Drift-Audit` (PR #200 hotfix root-cause audit + verdict).
**Branch**: `feature/sprint-57-51-audit-docs-hygiene-bundle`
**Class**: `audit-cycle / docs / template` 0.40 (4th data point — 1st was Sprint 57.10 ratio ~1.63 OVER band; 2nd-3rd N/A — single data point in matrix until now)
**Sub-class** (agent_factor): `mixed-multidomain-bundle` 0.65 (3 independent tracks A+B+C; tier-2 sub-class table **1st validation post Sprint 57.48 Option B activation** + Sprint 57.50 tier-2 ESCALATION; UNCHANGED in tier-2 split)
**Date**: 2026-05-26 (Sprint 57.50 closeout same-day continuation)
**Prior sprint reference**: Sprint 57.50 (single-track Identity fixture cleanup — `mechanical-single-domain` 0.45 2nd validation → tier-2 ESCALATED) + Sprint 57.48 (5-track wave — Option B sub-class split activated; AP-4 detector false-positive fix surfaced D-DAY0-6 lesson) + Sprint 57.50 D-DAY0-2 (Tenant ORM in `identity.py` not `tenant.py` lesson)

---

## 1. Sprint Goal

```
AS the project maintainer of `.claude/rules/` + V2 plan-time discipline + frontend
   mockup-fidelity guard
I WANT 3 carryover ADs from Sprint 57.48-50 trail closed in a single bundled
   hygiene sprint:
   (Track A) codify the "lint detector must mask legitimate code patterns to
      avoid false positives" rule, learned from Sprint 57.48 AP-4 detector
      `placeholder=` JSX attr false-positive D-DAY0-6 fix
   (Track B) add ORM file path reference style as a §Common Risk Classes entry
      in sprint-workflow.md, learned from Sprint 57.50 D-DAY0-2 lesson (Tenant
      ORM in `identity.py` per 09-db-schema-design.md Group 1, not the
      speculation-based `tenant.py`)
   (Track C) audit which Sprint 57.49 change introduced the +1 HEX_OKLCH literal
      that PR #200 hotfix had to absorb via baseline bump 47→48; produce
      AUDIT-REPORT with verdict (intended verbatim-token port like prior
      Sprint 57.30/57.35/57.37/57.38/57.40 precedent → fix-forward correct, OR
      unintended drift → fix-back needed)
SO THAT (a) future lint detector authoring follows code-aware masking
   discipline (rule codified); (b) future plan §Risks entries for ORM table
   paths avoid speculation drift (rule codified); (c) Sprint 57.49 silent
   drift root cause documented for traceability + future Sprint Day 0 三-prong
   Prong 2 content verify learns to grep oklch literal delta in agent-delegated
   migration sprints (new lesson surfaced); (d) tier-2 sub-class
   `mixed-multidomain-bundle` 0.65 agent_factor gets its 1st validation data
   point (Sprint 57.48 Option B activation never validated this sub-class
   directly; both Sprint 57.49 + 57.50 were `mechanical-single-domain` 0.45).
```

## 2. Background & Context

### 2.1 Track A — `AD-Lint-Detector-Code-Aware-Masking-Rule` (Sprint 57.48 carryover)

Sprint 57.48 Track E shipped the AP-4 lint detector false-positive fix. Root cause (per Sprint 57.48 retro Q4 D-DAY0-6):
- Original `check_ap4_frontend_placeholder.py` regex `\bplaceholder\b` matched (a) HTML5 `placeholder=` JSX attribute (legitimate React idiom) and (b) TypeScript object keys / interface fields literally named `placeholder` (legitimate domain naming).
- Fix: added `JSX_PLACEHOLDER_ATTR` mask + `TS_PLACEHOLDER_KEY` mask before the main pattern grep so legitimate code patterns are pre-stripped from the line buffer.
- 0 frontend files touched — the bug was in the detector, not the pages.

The generalizable lesson: **lint detectors authored to find code anti-patterns must mask out legitimate code patterns that happen to literally contain the trigger token, to avoid noise that hides real signal**. Codify into a rule doc so future detector authoring (e.g. AP-2 BackendGapBanner detector, future AP-5+ detectors) inherits the discipline.

**Codification target**: `docs/rules-on-demand/lint-detector-authoring.md` (NEW; on-demand rule — `.claude/rules/README.md` index 11→12 entries).

### 2.2 Track B — `AD-Plan-Risk-ORM-File-Path-Reference-Style` #82 (Sprint 57.50 carryover)

Sprint 57.50 Day 0.8 three-prong Prong 2 D-DAY0-2 finding:
- Plan §8 Risks row referenced `Tenant.meta_data` JSONB existence with risk text "Tenant ORM model possibly missing the column" + risk mitigation "Day 0.8 Prong 2 read `Tenant` ORM model".
- During Prong 2 grep, AI initially looked at `backend/src/infrastructure/db/models/tenant.py` — file did not exist. Confusion resolved by reading `09-db-schema-design.md` Group 1 (Identity & Tenancy) which clarified the `Tenant` ORM lives in `identity.py` (grouped with `User` / `Role` / `OIDCProvider` per identity domain cohesion).
- ~5 min wasted on file-path speculation.

The generalizable lesson: **plan §Risks rows referencing ORM models should cite `09-db-schema-design.md` Group N classification, not speculation-based `<table_name>.py` path**. Codify into `sprint-workflow.md §Common Risk Classes` + Plan template snippet.

**Codification target**: extend `.claude/rules/sprint-workflow.md §Common Risk Classes` with a new entry Risk Class D: ORM File Path Reference Style.

### 2.3 Track C — `AD-Sprint-57.49-HEX_OKLCH-Silent-Drift-Audit` (PR #200 hotfix carryover)

Sprint 57.50 Day 2 closeout PR #200 `feat(sprint-57-50)` push surfaced an unexpected `Mockup-fidelity` CI guard failure: the guard found 48 oklch literals but `HEX_OKLCH_BASELINE = 47`. Investigation showed:
- main `33e9f2aa` (Sprint 57.49 merge) already had count 48 — meaning Sprint 57.49's merge had silently exceeded the baseline at merge time (the GitHub Actions Mockup-fidelity check passes when count ≤ baseline; Sprint 57.49 had 48 > 47, but CI was apparently green at merge — root cause TBD: maybe paths-filter, maybe a CI race, maybe baseline was 48 elsewhere).
- Sprint 57.50 itself added 0 new oklch literals (GeneralTab.tsx Identity Card refactor uses only `var(--danger)` token references in Card border style — no raw oklch literals).
- Fix-forward chosen at hotfix `74ed8a2f`: bump baseline 47 → 48 (catch up to merged main state), rather than fix-back (revert the Sprint 57.49 +1 literal which had already shipped).

**Audit purpose**: identify which Sprint 57.49 file change introduced the +1 oklch literal; classify it as (verdict A) intended verbatim-mockup-token port consistent with prior Sprint 57.30/57.35/57.37/57.38/57.40 precedent → fix-forward catch-up was correct, OR (verdict B) unintended drift / shadcn-utility residue / something else → fix-back patch needed in a follow-up commit.

**Codification target**: `claudedocs/4-changes/refactoring/AUDIT-001-sprint-57-49-hex-oklch-silent-drift.md` (audit report with verdict).

### 2.4 Tier-2 sub-class `mixed-multidomain-bundle` 0.65 1st validation

Per Sprint 57.50 retro Q4 ESCALATION:
- Sprint 57.46 was the original `mixed-multidomain-bundle` 0.65 baseline-opener (1 data point at the activated 0.45 → ratio 1.60 ABOVE band, rolled back to 0.65).
- Sprint 57.48 Option B activation kept `mixed-multidomain-bundle` 0.65 UNCHANGED (sub-class table treated it as already-calibrated from Sprint 57.46 rollback evidence; Sprint 57.48 itself was 4-endpoint mechanical → maps to `mechanical-single-domain` 0.45 not multi-domain bundle).
- Sprint 57.49 = `mechanical-single-domain` 0.45 (1st validation under new sub-class).
- Sprint 57.50 = `mechanical-single-domain` 0.45 (2nd validation → ESCALATION to tier-2).
- **Sprint 57.51 = `mixed-multidomain-bundle` 0.65 1st validation** (3 independent tracks; not mechanical; not single-domain).

If ratio lands in [0.85, 1.20] band → validates sub-class 0.65 → KEEP.
If ratio < 0.7 → 1st rollback-trigger data point; KEEP per single-data-point caution.
If ratio > 1.20 → roll back 0.65 → 1.0 (drop the modifier for multi-domain bundles; treat as `human` cadence).

---

## 3. User Stories

### US-1: Codify Lint Detector Code-Aware Masking Rule (Track A)

```
AS a future detector author writing AP-N anti-pattern lint detectors
I WANT a rule doc that articulates the code-aware masking discipline
   (mask out legitimate code patterns like JSX attrs, TS keys, comment
   blocks BEFORE applying the main anti-pattern grep) — with the Sprint
   57.48 AP-4 `placeholder=` false-positive case as concrete example
SO THAT new detectors avoid the same false-positive class out of the box,
   reducing PR CI noise and avoiding 8/9 V2 lints regression like Sprint
   57.46-47 carried until Sprint 57.48 fixed it.
```

**Acceptance**:
- NEW file `docs/rules-on-demand/lint-detector-authoring.md` ~80-150 lines
- Sections: (a) Why (Sprint 57.48 D-DAY0-6 evidence) / (b) Core Pattern (3-step authoring: identify trigger → enumerate legitimate matches → write masks) / (c) Concrete examples (AP-4 placeholder case + hypothetical AP-N case) / (d) Anti-patterns (don't use raw `\bX\b` for tokens with common legitimate usage; don't run detector on already-stripped output) / (e) Cross-references to existing 9 V2 lints
- Update `.claude/rules/README.md` index: on-demand rules 11→12 (add lint-detector-authoring entry to §On-Demand table with Trigger: "writing new AP-N detector / maintaining existing AP-N detector / debugging detector false-positive")
- File header convention applied (Purpose / Category / Created / MHist 1-line)

### US-2: Codify ORM File Path Reference Style Risk Class (Track B)

```
AS the AI assistant drafting Plan §8 Risks rows that reference ORM models
I WANT a §Common Risk Classes Risk Class D entry in sprint-workflow.md
   that documents the discipline: cite `09-db-schema-design.md` Group N
   (e.g. "Group 1 Identity & Tenancy") not speculation-based `<table>.py`
   path
SO THAT future sprint plans avoid the Sprint 57.50 D-DAY0-2 ~5 min file-path
   speculation cost; reviewer (user / AI) can verify risk row at plan time
   without fall-back-to-grep.
```

**Acceptance**:
- Extend `.claude/rules/sprint-workflow.md §Common Risk Classes` (existing has Risk Class A/B/C) with NEW Risk Class D: ORM File Path Reference Style
- Entry follows established template: `Symptom → Workaround → Long-term fix`
- Symptom: plan §Risks ORM row uses `<table_name>.py` speculation; Workaround: cite `09-db-schema-design.md` Group N; Long-term fix: codify in Plan template
- Cross-link from Plan template stub (if Plan template doc exists) — discover during Track B execution
- 1 paragraph + 1 short example block citing Sprint 57.50 D-DAY0-2 evidence
- File header MHist 1-line entry added

### US-3: Sprint 57.49 HEX_OKLCH Silent Drift Audit (Track C)

```
AS the project maintainer of the mockup-fidelity guard and the verbatim-CSS
   discipline
I WANT a Sprint 57.49 git diff audit identifying which file(s) introduced
   the +1 oklch literal that PR #200 hotfix absorbed via baseline bump
   47→48; with verdict on whether the fix-forward was correct OR whether
   fix-back is needed
SO THAT (a) Sprint 57.49 retro trail has documented closure for the silent
   drift surfaced post-merge; (b) future agent-delegated migration sprints
   add a Day 0 三-prong Prong 2 grep step "count oklch literal delta in
   touched files vs prior baseline" — generalize the audit lesson.
```

**Acceptance**:
- NEW file `claudedocs/4-changes/refactoring/AUDIT-001-sprint-57-49-hex-oklch-silent-drift.md`
- Sections: (a) Trigger (PR #200 hotfix CI failure surface) / (b) Investigation (git diff `c451f584..33e9f2aa` filtered to `frontend/src/**` oklch lines; identify file:line of the +1) / (c) Verdict (A intended verbatim port → fix-forward correct / B unintended drift → fix-back recommended) / (d) Lesson for future sprint Day 0 三-prong Prong 2 (new grep step formalization)
- If verdict B → also produce a follow-up commit revert/patch (out-of-scope for this sprint; document only)
- ≤ 100 lines (verdict + evidence; not a deep refactor doc)
- File header convention applied

---

## 4. Technical Specification

### 4.1 Track A — `docs/rules-on-demand/lint-detector-authoring.md` structure

```markdown
# Lint Detector Authoring — Code-Aware Masking Discipline

**Purpose**: When writing AP-N anti-pattern detectors (scripts/lint/*.py), mask
out legitimate code patterns containing the trigger token BEFORE applying the
main grep, to avoid false-positive noise that obscures real signal.

**Category**: Development Process / Lint Authoring
**Created**: 2026-05-26 (Sprint 57.51)
**Status**: Active

## Why

Sprint 57.48 D-DAY0-6 root cause: `check_ap4_frontend_placeholder.py` regex
`\bplaceholder\b` matched 3 classes of legitimate code patterns:
1. HTML5 `placeholder="..."` JSX attribute (legitimate React idiom)
2. TypeScript object keys / interface fields literally named `placeholder`
3. (Future) shadcn-utility `placeholder:` class modifier

Without masks, the detector flagged ~12 false-positives across Sprint 57.46-47;
the 8/9 V2 lints carryover persisted until Sprint 57.48 Track E shipped the
fix. Cost: 2 sprints of "8/9 GREEN" noise hiding real lint signal.

## Core Pattern (3 steps)

1. **Identify trigger token** — what literal string the detector is looking for
2. **Enumerate legitimate matches** — what code patterns LEGITIMATELY contain
   this token? (JSX attrs, TS keys, comment blocks, string literals, …)
3. **Write masks** — regex substitutions that pre-strip legitimate matches
   from the line buffer BEFORE the main pattern grep

## Concrete Examples

### AP-4 `placeholder=` JSX attr mask (Sprint 57.48 Track E)

```python
JSX_PLACEHOLDER_ATTR = re.compile(r'placeholder=["\'][^"\']*["\']')
TS_PLACEHOLDER_KEY = re.compile(r'\bplaceholder\s*:')

def check_line(line):
    stripped = JSX_PLACEHOLDER_ATTR.sub('', line)
    stripped = TS_PLACEHOLDER_KEY.sub('', stripped)
    return PLACEHOLDER_BAD_PATTERN.search(stripped)
```

### Hypothetical AP-N mask example

…

## Anti-patterns

- ❌ Raw `\bX\b` for tokens with common legitimate usage
- ❌ Running detector on already-stripped output without re-masking
- ❌ Skipping mask step "for performance" — false positives waste more time

## Cross-references

- `.claude/rules/anti-patterns-checklist.md` (11-point PR self-check)
- `scripts/lint/run_all.py` (V2 lint aggregator)
- 9 existing V2 lints in `scripts/lint/check_ap*_*.py`
```

### 4.2 Track B — `.claude/rules/sprint-workflow.md §Common Risk Classes` extension

Append a new "### Risk Class D: ORM File Path Reference Style (sprint planning)" section after existing C, following the established 3-line template:

```markdown
### Risk Class D: ORM File Path Reference Style (sprint planning)

**Symptom**: Plan §8 Risks row references an ORM model with a speculation-based
path like `backend/src/infrastructure/db/models/<table_name>.py` (e.g.
`tenant.py`); Day 0.8 Prong 2 then wastes 3-5 min discovering the model lives
elsewhere (e.g. `identity.py` per domain cohesion grouping).

**Source**: Sprint 57.50 D-DAY0-2 — plan referenced `Tenant.meta_data` JSONB;
AI initially looked at `tenant.py` (did not exist); Prong 2 grep resolved to
`identity.py` per `09-db-schema-design.md` Group 1 (Identity & Tenancy domain
groups User + Role + OIDCProvider + Tenant in one file).

**Workaround**: Cite `09-db-schema-design.md §Group N <Domain Name>` in plan
§Risks rows touching ORM models, not the speculation-based `.py` path. Example:
"Risk: `Tenant.X` field doesn't exist — mitigation: Day 0.8 Prong 2 read
`Tenant` ORM in `09-db-schema-design.md §Group 1 Identity & Tenancy` (note: file
is `identity.py`, not `tenant.py`)."

**Long-term fix**: Codify in Plan template stub (when Plan template doc is
formalized as part of `.claude/rules/`).
```

### 4.3 Track C — `AUDIT-001` audit method

```bash
# Step 1: Identify file:line of +1 oklch literal in Sprint 57.49 diff
git diff c451f584..33e9f2aa -- 'frontend/src/**' \
  | grep -nE '^\+.*oklch\(' \
  | head -30

# Step 2: Identify removed oklch literals (delta is NET +1, could be +5-4 etc.)
git diff c451f584..33e9f2aa -- 'frontend/src/**' \
  | grep -nE '^-.*oklch\(' \
  | head -30

# Step 3: For each NET +1 file, read the context (mockup verbatim port? shadcn-utility
# residue? unintended drift?) — verdict A vs B
```

Likely verdict (prediction): A — intended verbatim port. Sprint 57.49 introduced 5 NEW TanStack Query hooks consumed by 5 NEW tab refactors (FeatureFlagsTab / QuotasTab / HITLPoliciesTab / MembersTab + AdminTenants TenantMembersDrawer). One of these likely added a verbatim `oklch(from var(--X) l c h / Y)` token literal matching mockup source — consistent with Sprint 57.30/57.35/57.37/57.38/57.40 precedent. Fix-forward at PR #200 hotfix was the correct call; no fix-back needed; lesson is to add an explicit oklch-delta grep step in Day 0 三-prong Prong 2 for agent-delegated migration sprints.

If verdict B (unintended): document the offending file + propose fix-back commit; out-of-scope to actually do the revert.

---

## 5. File Change List

### Documentation / Rules
- `docs/rules-on-demand/lint-detector-authoring.md` (NEW; Track A; ~80-150 lines)
- `.claude/rules/README.md` (Track A) — index update on-demand rules 11→12
- `.claude/rules/sprint-workflow.md` (Track B) — §Common Risk Classes Risk Class D added; MHist 1-line entry
- `claudedocs/4-changes/refactoring/AUDIT-001-sprint-57-49-hex-oklch-silent-drift.md` (NEW; Track C; ≤ 100 lines)

### Sprint artifacts
- `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-51-plan.md` (this file)
- `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-51-checklist.md`
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-51/progress.md` (Day 0 + Day 2 entries)
- `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-51/retrospective.md`
- `memory/project_phase57_51_audit_docs_hygiene_bundle.md`
- `memory/MEMORY.md` (pointer entry)
- `claudedocs/1-planning/next-phase-candidates.md` (Sprint 57.51 closeout note)
- `CLAUDE.md` (Current Sprint row + Last Updated footer)

### No production code changes
- 0 `.py` source file change (detector codification is into a `.md` rule doc, not the detector script — the detector itself was already fixed in Sprint 57.48 Track E; this sprint codifies the lesson)
- 0 `.ts/.tsx` source file change
- 0 backend test file change
- 0 frontend test file change
- 0 DB schema / Alembic migration

---

## 6. Workload

**Bottom-up est**: ~3.0 hr
- Track A (lint detector authoring rule doc + README index entry): ~1.5 hr
- Track B (Risk Class D entry + MHist): ~0.4 hr
- Track C (git diff audit + AUDIT-001 report): ~0.5 hr
- Day 0 三-prong (Prong 1 path + Prong 2 content; Prong 2.5/3 N/A): ~0.2 hr
- Day 2 closeout (retro + memory + CLAUDE.md + next-phase-candidates): ~0.4 hr

**Class-calibrated commit** (`audit-cycle / docs / template` 0.40):
- 3.0 × 0.40 = **~1.2 hr committed**

**Agent-adjusted commit** (`agent_factor = 0.65` tier-2 `mixed-multidomain-bundle`):
- 1.2 × 0.65 = **~0.8 hr agent-adjusted**

**4-segment form**:
> Bottom-up est ~3.0 hr → class-calibrated commit ~1.2 hr (mult 0.40) → agent-adjusted commit ~0.8 hr (agent_factor 0.65 tier-2 `mixed-multidomain-bundle` — **1st validation**)

**1st validation prediction**:
- If sub-class calibrated correctly → ratio ~0.85-1.20 (actual ~0.7-1.0 hr)
- If agent overhead exceeds savings for 3-track audit/docs (no mechanical pattern reuse) → ratio > 1.20 → roll back 0.65 → 1.0 (drop modifier; treat multi-domain audit/docs as human cadence)
- If pattern-reuse acceleration somehow applies → ratio < 0.7 → 1st rollback-trigger data point; KEEP per single-data-point caution
- Mid-prediction: actual ~0.7-1.2 hr → ratio ~0.85-1.50 → in-band or top-of-band edge

---

## 7. Acceptance Criteria

| # | Criterion | Verify |
|---|---|---|
| AC-1 | NEW `docs/rules-on-demand/lint-detector-authoring.md` ~80-150 lines | wc -l |
| AC-2 | `.claude/rules/README.md` on-demand index 11→12 entries (lint-detector-authoring listed with Trigger) | grep |
| AC-3 | `.claude/rules/sprint-workflow.md §Common Risk Classes Risk Class D` present | grep "Risk Class D" |
| AC-4 | NEW `claudedocs/4-changes/refactoring/AUDIT-001-sprint-57-49-hex-oklch-silent-drift.md` ≤ 100 lines with verdict A or B | wc -l + grep "Verdict" |
| AC-5 | Verdict supported by git diff evidence (file:line of +1 oklch) | grep "file:" in AUDIT-001 |
| AC-6 | 0 production code change (0 .py / .ts / .tsx source files touched) | git diff --stat |
| AC-7 | 9 V2 lints preserved (9/9 from Sprint 57.50) | `python scripts/lint/run_all.py` exit 0 |
| AC-8 | pytest backend baseline preserved (224 PASS from Sprint 57.50) | exit 0 + count match |
| AC-9 | Vitest baseline preserved (607 PASS from Sprint 57.50) | exit 0 + count match |
| AC-10 | ESLint + tsc + Vite build all clean | exit 0 |
| AC-11 | File headers convention applied to NEW docs (Purpose / Category / Created / MHist 1-line) | grep |
| AC-12 | Day 0 三-prong report logged | Read progress.md |
| AC-13 | retrospective.md Q1-Q7 with 1st validation `mixed-multidomain-bundle` 0.65 ratio + decision per rollback rule logged in Q4 | grep Q4 |
| AC-14 | sprint-workflow.md MHist + matrix `audit-cycle/docs/template` 4th data point + §Active Activation history `mixed-multidomain-bundle` 1st validation | grep |

---

## 8. Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| `docs/rules-on-demand/` directory layout differs from §5 Frontend Mockup-Fidelity precedent | Low | Day 0.8 Prong 1 `ls docs/rules-on-demand/` to confirm structure |
| `.claude/rules/sprint-workflow.md §Common Risk Classes` section header differs from "### Risk Class A:" template | Low | Day 0.8 Prong 2 read section in full to confirm header format + 3-line template |
| `09-db-schema-design.md` Group N classification doesn't match the "Group 1 Identity & Tenancy" assumption (per `09-db-schema-design.md` Group references for ORM grouping per Group 1 Identity & Tenancy classification convention)  | Medium | Day 0.8 Prong 2 read `docs/03-implementation/agent-harness-planning/09-db-schema-design.md` Group section to confirm |
| Sprint 57.49 git diff has 0 NET oklch literal change (silent baseline was 47 not 48 at PR #200 push time; CI race surfaced an unrelated drift) | Medium | Day 0.8 Prong 2 run `git diff c451f584..33e9f2aa` oklch grep to confirm; if 0 NET +1, audit pivots to "why did PR #200 see 48 when main was 47" — likely AUDIT-001 ROOT will shift |
| Track A rule doc length > 150 lines (over-engineering for a single detector lesson) | Low-Medium | Day 1 enforce ≤150 line target; if rule needs to be deeper, split into `lint-detector-authoring.md` (overview) + future sprint adds `lint-detector-cookbook.md` (per-detector examples) |
| AUDIT-001 verdict B (unintended drift) → demand for follow-up fix-back commit | Low | If verdict B, document in AUDIT-001 §Recommended Follow-up + open as carryover AD-Sprint-57-49-HEX_OKLCH-Fix-Back-Commit for next sprint; **do not** add the fix-back to this sprint scope (audit-cycle class discipline) |
| `mixed-multidomain-bundle` 0.65 1st validation lands > 1.20 (agent overhead exceeds 3-track savings for non-mechanical work) | Medium | Single-data-point caution rule: roll back 0.65 → 1.0 (drop modifier); 2-data-point trigger required |
| `mixed-multidomain-bundle` 0.65 1st validation lands < 0.7 (agent speedup somehow applies despite non-mechanical work) | Low-Medium | Single-data-point caution: KEEP 0.65; flag Sprint 57.52+ for 2nd validation |
| Track A → Track B → Track C sequential execution forces serial agent delegation overhead (vs single bigger agent call) | Low | Plan agent delegation as 1 call with 3 sub-tasks (mirrors Sprint 57.46 multi-track agent strategy) — backend agent unused; frontend agent unused; rules/docs agent or direct edit |
| Day 0.8 Prong 2 surfaces 4th drift finding (additional carryover AD) | Low-Medium | Catalog all drifts to progress.md Day 0 per AD-Plan-2 promotion discipline; if scope shifts > 20%, revise plan §6 Workload |

---

## 9. Carryover ADs (for Sprint 57.52+ pickup)

- `AD-AgentFactor-Tier-2-MixedBundle-Validation-Sprint-57.52` (2nd data point for `mixed-multidomain-bundle` 0.65 — only if Sprint 57.51 ratio lands < 0.7 OR > 1.20 single-data-point trigger)
- `AD-Lint-Detector-Cookbook` (Phase 58+ optional — if Track A rule doc proves the discipline is useful, future sprint adds per-detector cookbook examples)
- `AD-09-DB-Schema-Group-Index` (Phase 58+ optional — if Track B reveals the Group N classification convention deserves a top-of-doc summary table)
- `AD-Sprint-57.49-HEX_OKLCH-Fix-Back-Commit` (CONDITIONAL — only created if Track C AUDIT-001 verdict B; Sprint 57.52 pickup if so)
- `AD-Day0-Prong2-Oklch-Delta-Grep` (NEW from this sprint if Track C lesson surfaces — formalize the oklch-literal-delta grep as a Day 0 三-prong Prong 2 step for agent-delegated frontend migration sprints)
- `AD-medium-frontend-Baseline-Recalibration` (Sprint 57.49 carryover continues — 3rd data point pending; not addressed in this sprint since Sprint 57.51 is `audit-cycle/docs/template` class not medium-frontend)
- `AD-MockupCapture-Frontend-Visual-Diff-Pipeline` (Phase 58+ deferred — carryover continues)
- `AD-TenantSettings-RateLimits-Persistence` (Phase 58.x deferred — carryover continues)
- `AD-TenantSettings-Identity-Persistence-Phase58` (Phase 58.x deferred — Sprint 57.50 carryover continues)
- Potential NEW from Sprint 57.51 Day 0.8 三-prong findings

---

**Modification History**:
- 2026-05-26: Sprint 57.51 Day 0.1 — Initial draft (triple-AD audit/docs hygiene bundle; tier-2 `mixed-multidomain-bundle` 0.65 1st validation post Sprint 57.50 ESCALATION)
