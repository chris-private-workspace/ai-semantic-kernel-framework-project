# AUDIT-001: Sprint 57.49 HEX_OKLCH Baseline Silent Drift Audit

**Purpose**: Audit which Sprint 57.49 file change introduced the +1 oklch literal that PR #200 hotfix `74ed8a2f` absorbed via baseline bump 47→48; classify as intended verbatim port (verdict A) or unintended drift (verdict B); recommend lesson for future agent-delegated frontend migration sprints.

**Category**: Audit / Refactoring
**Created**: 2026-05-26 (Sprint 57.51)
**Last Modified**: 2026-05-26
**Status**: Closed (verdict A — fix-forward at PR #200 confirmed correct)
**Sprint**: 57.51 Track C
**Closes**: `AD-Sprint-57.49-HEX_OKLCH-Silent-Drift-Audit`

> **Modification History**
> - 2026-05-26: Sprint 57.51 Track C — Initial creation + verdict A close-out + new carryover `AD-Day0-Prong2-Oklch-Delta-Grep` opened

---

## §Trigger

Sprint 57.50 Day 2 closeout PR #200 (`feat(sprint-57-50): TenantSettings Identity Fixture Cleanup`) push surfaced an unexpected GitHub Actions `Mockup-fidelity` CI guard failure: the workflow found 48 oklch literals across `frontend/src/**` but the in-repo constant `HEX_OKLCH_BASELINE = 47`. Investigation revealed:

- **main `33e9f2aa`** (Sprint 57.49 merge commit) ALREADY had count 48 — meaning Sprint 57.49's merge silently exceeded the prior baseline at merge time.
- **Sprint 57.50 itself contributed 0 new oklch literals** (GeneralTab.tsx Identity Card refactor used only `var(--danger)` token references in Card border styles — no raw oklch literals).
- **Fix-forward** chosen at hotfix `74ed8a2f`: bump `HEX_OKLCH_BASELINE` 47 → 48 (catch up to merged main state), rather than fix-back (revert the Sprint 57.49 +1 literal which had already shipped to main and was visually load-bearing).

This audit identifies the source file:line of the +1 oklch literal, classifies it, and validates the fix-forward decision.

---

## §Investigation method

Three-step `git diff` filter pipeline:

```bash
# Step 1 — Count added oklch lines in Sprint 57.49 diff
git diff c451f584..33e9f2aa -- 'frontend/src/**' \
  | grep -cE '^\+[^+].*oklch\('
# Result: 2 added lines containing oklch literals

# Step 2 — Count removed oklch lines
git diff c451f584..33e9f2aa -- 'frontend/src/**' \
  | grep -cE '^-[^-].*oklch\('
# Result: 1 removed line containing an oklch literal
# NET delta: +2 - 1 = +1 line (matches the baseline bump 47→48)

# Step 3 — Locate file:line of added oklch lines
git diff c451f584..33e9f2aa -- 'frontend/src/**' \
  | grep -nE '^\+\+\+|^\+[^+].*oklch\('
# Identifies the +line file boundaries and their surrounding `+++ b/...` headers
```

Result interpretation: 2 lines added + 1 line removed = NET +1 line; the baseline bump 47→48 in PR #200 exactly absorbs this net delta.

---

## §Evidence — file:line identification

### Source of the NET +1 oklch literal

**File**: `frontend/src/features/admin-tenants/components/TenantMembersDrawer.tsx` (NEW file in Sprint 57.49)
**Sprint context**: Sprint 57.49 Track B introduced `TenantMembersDrawer` as the admin-tenants Members row-click drawer slide-over component
**Line content** (canonical gradient pattern):
```tsx
background: `linear-gradient(135deg, oklch(0.65 0.15 ${c % 360}), oklch(0.5 0.16 ${(c + 60) % 360}))`
```

This single line contributes **2 oklch literal occurrences** (one for each gradient stop). The avatar circle's hue is computed dynamically from a number `c` (member identifier hash) so each member gets a deterministic but distinct gradient.

### Offsetting -1 oklch in MembersTab.tsx

**File**: `frontend/src/features/tenant-settings/components/tabs/MembersTab.tsx`
**Sprint context**: Sprint 57.49 Track A refactored MembersTab from fixture data to TanStack Query hook; during the refactor, an identical avatar-gradient line was relocated within the file body
**Net contribution**: `+line` and `-line` of the same gradient pattern offset → **NET 0 contribution** from MembersTab to the oklch literal count

### Net source of the +1 baseline drift

Therefore: **NET +1 contribution comes from `TenantMembersDrawer.tsx` (NEW file)**, NOT from MembersTab.tsx (which net-zeroed via relocation).

---

## §Verdict A — intended verbatim port

**Classification**: Verdict A — intended verbatim port, mockup-discipline compliant.

**Supporting evidence**:

1. **Original pattern established Sprint 57.44**: The avatar gradient `linear-gradient(135deg, oklch(0.65 0.15 ${c % 360}), oklch(0.5 0.16 ${(c + 60) % 360}))` was introduced in Sprint 57.44 MembersTab rebuild. Citation from `.claude/rules/sprint-workflow.md` Scope-class multiplier matrix MHist:

   > "HEX_OKLCH 46 → 47 (+1 MembersTab avatar gradient verbatim port per plan §3.6 within-range; ended 4-sprint +0 streak)"

   Sprint 57.44 plan §3.6 explicitly authorized the within-range +1 bump for the MembersTab avatar gradient as verbatim-CSS-protocol compliant.

2. **Sprint 57.49 cross-component consistency reuse**: Sprint 57.49 Track B introduced `TenantMembersDrawer` (NEW component for /admin-tenants Members row-click drawer slide-over) which **reuses the SAME gradient pattern by design** — cross-component visual consistency between (a) /admin-tenants Members drawer avatars (Track B) and (b) /tenant-settings Members tab avatars (Track A baseline). Both surfaces show the same member avatar shape; rendering them with a different gradient would be a UX regression.

3. **Mockup-discipline conformance**: The mockup pages `reference/design-mockups/page-admin-tenants.jsx` and `reference/design-mockups/page-tenant-settings.jsx` both show member avatar circles with the identical gradient idiom. The Sprint 57.49 implementation preserves this idiom byte-for-byte across both components.

4. **Visual consistency invariant**: Reverting the Sprint 57.49 TenantMembersDrawer gradient (fix-back path) would break the cross-component visual consistency invariant — drawer avatars would diverge from MembersTab avatars. This is unacceptable; fix-forward at PR #200 was the correct call.

**Verdict**: ✅ **A — intended verbatim port**. Mockup-discipline compliant. No fix-back commit needed.

---

## §Why the drift was "silent" (root cause)

Despite the addition being mockup-discipline compliant, the baseline drift was unflagged through merge. Root cause has three contributing factors:

1. **Sprint 57.49 plan §6 acceptance criteria omission**: The plan checklist did NOT include an explicit "+1 HEX_OKLCH bump if drawer reuses MembersTab avatar gradient" note. The agent-delegated Day 1 implementation produced the correct mockup-aligned code but did not surface the baseline bump need in the commit message or pre-push lint local-run.

2. **CI race / paths-filter sequence**: Sprint 57.49 CI presumably ran on a feature-branch HEAD with prior baseline 47 BEFORE the +1 line had its final form (e.g. earlier draft commits may not have included the drawer file); main HEAD post-merge had count 48 — but CI never re-ran against main HEAD post-merge to catch the now-failing baseline. (Paths-filter / required-status-checks discipline see Risk Class A in `sprint-workflow.md`.)

3. **No Day 0 三-prong oklch-delta grep**: The Day 0 plan-verify discipline (`sprint-workflow.md §Step 2.5`) does not currently include an oklch-literal-delta grep step for agent-delegated frontend migration sprints. Such a step would have caught the +1 at plan-verify time, allowing Sprint 57.49 plan §6 to add the baseline bump acceptance criterion before code started.

---

## §Fix-forward verdict

**Decision at PR #200 hotfix `74ed8a2f`**: Bump `HEX_OKLCH_BASELINE` 47 → 48.

**Verdict**: ✅ **Correct decision**. Reverting Sprint 57.49 TenantMembersDrawer gradient (fix-back path) would break cross-component visual consistency between drawer avatars and MembersTab avatars (both surfaces show the same member entities; gradient divergence would be a UX regression). No fix-back commit recommended.

---

## §Lesson for future Day 0 三-prong

**NEW Day 0.8 Prong 2 step proposed for agent-delegated frontend migration sprints**:

```bash
# For sprints touching frontend/src/**, compute oklch literal delta upfront:
git diff $(git merge-base main HEAD)..HEAD -- 'frontend/src/**' \
  | grep -cE '^\+[^+].*oklch\('
# Compare against:
git diff $(git merge-base main HEAD)..HEAD -- 'frontend/src/**' \
  | grep -cE '^-[^-].*oklch\('
# NET delta > 0 → flag baseline bump need in plan §6 acceptance criteria
#               + Day 1 commit message
```

**Formalization path**: NEW carryover `AD-Day0-Prong2-Oklch-Delta-Grep` for Sprint 57.52+ pickup to codify the grep step into `sprint-workflow.md §Step 2.5 Prong 2` content-verify discipline.

---

## §Status

**CLOSED** — `AD-Sprint-57.49-HEX_OKLCH-Silent-Drift-Audit` resolved by this audit. Fix-forward at PR #200 hotfix `74ed8a2f` confirmed correct. NEW carryover opened: `AD-Day0-Prong2-Oklch-Delta-Grep` (next-sprint pickup).

## §References

- Sprint 57.49 plan / retrospective: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-49/`
- Sprint 57.50 closeout PR #200 hotfix `74ed8a2f`
- Sprint 57.44 MembersTab original gradient introduction context: `.claude/rules/sprint-workflow.md` §Scope-class multiplier matrix `frontend-mockup-strict-rebuild` 10th data point MHist
- `frontend/scripts/check-mockup-fidelity.mjs` (CI guard implementing `HEX_OKLCH_BASELINE` constant; verify in-repo source path during Sprint 57.52+ codification)
- `.claude/rules/sprint-workflow.md §Step 2.5 Prong 2` (target location for future oklch-delta-grep codification)
