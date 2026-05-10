# FIX-007: `visual-baseline` workflow `git add` pathspec didn't match the generated snapshots

**Date**: 2026-05-10
**Sprint**: 57.14 (post-merge follow-up)
**Scope**: DevOps / CI (`.github/workflows/playwright-e2e.yml` — the `visual-baseline` job introduced by Sprint 57.14 US-B1)

## Problem
The first `workflow_dispatch` run of the `visual-baseline` job (run `25632807137`, on `main` `ae217743`) generated all 6 `visual-regression.spec.ts` baselines correctly ("A snapshot doesn't exist … writing actual" ×6, all tests ✓) but **did not commit them** — the "Commit baselines if changed" step logged `fatal: pathspec 'tests/e2e/visual/**/*-snapshots/' did not match any files` then `no baseline changes`, so `origin/main` stayed at `ae217743` with no `-snapshots/` dir. The baselines were still uploaded as the `visual-baselines` artifact, so nothing was lost — but the auto-commit (the whole point of the job) was a no-op.

## Root Cause
The `git add` line was `git add tests/e2e/visual/**/*-snapshots/ || true`. The `**` recursive glob doesn't work here:
- Bash `globstar` is off in the runner's non-interactive shell, so `**` is treated as a single `*` segment and the pattern doesn't expand to anything on disk → bash passes the literal string `tests/e2e/visual/**/*-snapshots/` to `git add`.
- `git add` then interprets `**` as a literal path component (git pathspecs only treat `**` specially with the `:(glob)` magic prefix) → `fatal: pathspec … did not match` → the `|| true` swallows it → nothing staged → `git diff --cached --quiet` is true → "no baseline changes" → no commit.

Playwright actually writes baselines to `frontend/tests/e2e/visual/visual-regression.spec.ts-snapshots/*.png` — a dir directly under `tests/e2e/visual/`, not nested.

## Solution
Changed the `git add` line (in `.github/workflows/playwright-e2e.yml`, `visual-baseline` job, "Commit baselines if changed" step, `working-directory: frontend`) from:

```bash
git add tests/e2e/visual/**/*-snapshots/ || true
```
to:
```bash
git add tests/e2e/visual/
```

`git add tests/e2e/visual/` stages everything new/changed under that dir (= the `<spec>-snapshots/` dir + its PNGs). Nothing else under `tests/e2e/visual/` changes during the run, so this is exact in practice. (Dropped the `|| true` too — `git add <dir>` of an existing dir never errors; if there's nothing to add it's a clean no-op, and the subsequent `git diff --cached --quiet` handles the "no changes" case.)

Added a code comment explaining the bash-globstar / git-pathspec gotcha so it doesn't regress.

## Verification
- After this fix merges to `main`, re-trigger: `gh workflow run "Playwright E2E" --ref main` → the `visual-baseline` job should now `git commit` + `git push` the `frontend/tests/e2e/visual/visual-regression.spec.ts-snapshots/*.png` to `main` (commit message `chore(e2e): regenerate visual-regression baselines [skip ci]`). Confirm via `git ls-tree -r origin/main --name-only | grep snapshots` → 6 PNGs.
- Once committed, `visual-regression.spec.ts`'s skip guard (`existsSync("<spec>-snapshots/")`) auto-un-skips → the spec runs as part of the regular `e2e` job on every push/PR.
- ⚠️ If the bot push is blocked by branch protection (`enforce_admins=true` + required checks vs the `[skip ci]` commit not triggering CI) → the baselines are still on the `visual-baselines` artifact; download + commit manually. (This fallback was already noted in `sprint-57-14-plan.md` §Risk matrix.)

## Impact
CI-only; no application code. The `visual-baseline` job is `workflow_dispatch`-only so this never affected push/PR CI. Until the re-trigger, `visual-regression.spec.ts` stays auto-skipped (no baselines committed) — push/PR e2e is unaffected (40 pass / 7 skip).
