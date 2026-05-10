# FIX-008: `visual-baseline` workflow's direct push to `main` is blocked by branch protection — open a PR instead

**Date**: 2026-05-10
**Sprint**: 57.14 (post-merge follow-up; follows FIX-007)
**Scope**: DevOps / CI (`.github/workflows/playwright-e2e.yml` — the `visual-baseline` job introduced by Sprint 57.14 US-B1)

## Problem
After FIX-007 (the `git add` pathspec), the second `workflow_dispatch` run of the `visual-baseline` job (run `25633239693`, on `main` `d398ec04`) correctly generated and **committed** all 6 `visual-regression.spec.ts` baselines locally (`create mode 100644 frontend/tests/e2e/visual/visual-regression.spec.ts-snapshots/*.png` ×6), but the `git push origin HEAD:main` step **failed**:

```
remote: error: GH006: Protected branch update failed for refs/heads/main.
remote: - Changes must be made through a pull request.
remote: - 5 of 5 required status checks are expected.
 ! [remote rejected] HEAD -> main (protected branch hook declined)
```

The job exited 1. The baselines were still uploaded as the `visual-baselines` artifact (the manual fallback), so nothing was lost — but the auto-update of `main` is impossible by design: `main` has `enforce_admins=true` + 5 required status checks, and a `[skip ci]` commit doesn't satisfy them (no CI runs → checks "expected but not present" → push declined). Note: this was already called out in `sprint-57-14-plan.md` §Risk matrix ("visual-baseline workflow auto-commit fails due to branch protection — fallback: artifact") — the original design accepted it could happen; FIX-008 makes the job succeed cleanly instead of failing.

## Root Cause
The "Commit baselines if changed" step ended with `git push origin HEAD:${{ github.ref_name }}` — i.e., a direct push to `main` when the workflow is dispatched on `main`. Branch protection on `main` rejects all direct pushes (the workflow's `GITHUB_TOKEN` is not exempt, and `enforce_admins=true` means even an admin token couldn't). The only way to land changes on `main` is a PR that passes the 5 required checks.

## Solution
Changed the step (`.github/workflows/playwright-e2e.yml`, `visual-baseline` job) to:
- push the baseline commit to a throwaway branch `chore/visual-baselines-${{ github.run_id }}` (not `chore/**` in the workflow's `on: push` filter, so it doesn't re-trigger this workflow), and
- `gh pr create --base ${{ github.ref_name }} --head chore/visual-baselines-${{ github.run_id }}` — a PR a human reviews/merges (the baselines PR's own CI run exercises `visual-regression.spec.ts`, which now un-skips because the `-snapshots/` dir is present → confirms the Linux baselines match the CI runner).
- Added `permissions: pull-requests: write` to the job + `env: GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}` to the step (so `gh pr create` works).
- Renamed the step "Commit baselines if changed" → "Open a PR with the updated baselines (if changed)".
- The `Upload generated baselines as artifact` step stays (manual fallback if the PR path ever breaks).

Also updated the now-slightly-stale prose: `visual-regression.spec.ts` Description block + `frontend/CONVENTION.md` §8 "Visual regression baselines" — they said the job "commits the `-snapshots/` dir back to the branch"; now it "opens a PR".

## This sprint's one-off
For the actual landing of the *first* set of baselines (this sprint), I didn't wait for the fixed workflow — I downloaded the `visual-baselines` artifact from run `25633239693` and committed the 6 PNGs into `frontend/tests/e2e/visual/visual-regression.spec.ts-snapshots/` directly on the `chore/sprint-57-14-visual-baselines` branch (the same PR that carries this FIX-008 + the workflow fix). So the baselines land in this PR; future regenerations go through the auto-PR path.

## Verification
- Once this PR's `frontend/tests/e2e/visual/visual-regression.spec.ts-snapshots/*.png` are committed, the PR's own `Frontend E2E (chromium headless)` check should show `visual-regression.spec.ts` **running** (6 visual tests pass — the spec's `existsSync("<spec>-snapshots/")` guard is now true). That confirms the artifact baselines (generated on ubuntu-latest) match the CI runner.
- Future: `gh workflow run "Playwright E2E" --ref main` → the `visual-baseline` job → opens `chore/visual-baselines-<run_id>` PR → review/merge → baselines updated.
- ⚠️ The artifact-upload fallback remains for the case where the auto-PR path ever fails.

## Impact
CI-only; no application code. The `visual-baseline` job is `workflow_dispatch`-only — push/PR CI is unaffected. The job previously exited 1 on the push failure (cosmetic — the artifact was still uploaded); now it succeeds and produces a PR.
