# REFACTOR-007: docs/ + claudedocs/ V1-legacy archive & artifact relocation reorg

**Date**: 2026-06-12
**Sprint**: post-57.104 chore (branch `chore/docs-reorg-v1-archive`)
**Scope**: cross-cutting (documentation tree only; zero code change)

## Problem

Documentation tree had accumulated 4 sources of confusion (user-reported):
1. `claudedocs/4-changes/` held 31 `sprint-57-19..45` artifact folders (~1,013 files: Playwright screenshots + DRIFT/REPOINT/AUDIT reports) — a May mockup-fidelity-era misplacement; convention since 57.95 is per-sprint `agent-harness-execution/.../artifacts/`.
2. `claudedocs/5-status/` mixed 7 topic groups (53 flat files) with no index — filenames alone didn't reveal topic/situation; 21 of them were a *completed* 2026-04/05 V2-AUDIT batch.
3. V1-era (Phase 1-48, pre-2026-04-28) leftovers scattered across both trees: 9 non-standard claudedocs top-level dirs + root files, 11 docs/ root dirs, `03-implementation/{sprint-planning(432), sprint-execution(279), …}` parallel to the V2 authority dirs.
4. `claudedocs sample/` (another project's claudedocs, 228 files) sat at repo root; `claudedocs/nul` junk file (Windows redirection accident).

## Solution (4 phases, 4 commits, all `git mv` — history preserved, nothing deleted except `nul`)

| Phase | Commit | What |
|-------|--------|------|
| 1 | `6961b331` | claudedocs V1 → `archived/claudedocs-v1/`: 8 top-level dirs (prompts/session-logs/session-summaries/sprint-reports/testing/code-review/uat/8-conversation-log) + 5 root files + 1-planning epics & 2× 20260423 archaeology + 3-progress/daily 2× V1 dailies + 5-status 5 V1 items; deleted `claudedocs/nul` (user-authorized). 168 files. |
| 2 | `a74f4a18` | docs V1 → `archived/docs-v1/`: 11 root dirs + AGENT-FRAMEWORK-AUDIT.md + 03-implementation 8 V1 dirs + 5 V1 root files (kept azure-service-principal-setup.md + local-development-guide.md). Link fixes in active referencers (root README, SITUATION prompts, generate-summary, scripts/uat READMEs, 02-architecture, 07-analysis mentions). `.bmad/` generic example text deliberately reverted (false-positive replace). 916 files. |
| 3 | `369b9b22` | 31 sprint artifact folders → `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-NN/artifacts/<desc>/`; path refs fixed across 74 md files; `4-changes/` back to canonical 4 subdirs. 1,078 files. |
| 4 | (this commit) | `claudedocs sample/` → `archived/claudedocs-sample/`; V2-AUDIT 22 files → `5-status/v2-audit-2026-04/` (+9 referencing files fixed); NEW `5-status/README.md` total index (7 topic groups, 1 line/file); V2 rewrites of `claudedocs/CLAUDE.md` (was 2026-03-31 V1 content), `claudedocs/README.md`, `docs/README.md` (was 2025-11-14 BMAD Phase-0); this record. |

## Decisions (user-approved 2026-06-12)

- A: V1 legacy → repo-root `archived/` (single V1 entry alongside `archived/v1-phase1-48/`)
- B: sprint artifacts → execution `artifacts/` (align with 57.95+ convention)
- C: 5-status = index + completed-batch subdir only (active files NOT moved — ~40 referencing files unbroken)
- D: `claudedocs sample/` archive + `nul` delete

## Deliberately NOT touched

- `docs/07-analysis/` (386 files) — V1 research assets, root CLAUDE.md explicitly preserves
- `claudedocs/templates/` — active (sprint-workflow.md §Step 5.5 references it)
- `claudedocs/6-ai-assistant/` SITUATION prompts — active workflow (links fixed only)
- `CLAUDE.backup.md` / `archived/**` internals — historical snapshots keep stale links verbatim
- 5 closed-sprint plan/checklist files keep historical wildcard artifact-path mentions verbatim (audit trail; `git grep "4-changes/sprint-57-"` hits are intentional)
- Untracked local files: 3× 5-status analyses (cc-parity / cc-source-blueprint / flow-visualization — user's never-commit decision), 4× sprint artifacts dirs (57.95/96/103/104), `CUsersChrisDownloadsdeep_research.py` (flagged to user, not touched)
- `scripts/uat/` V1 test scripts — out of scope (doc links updated to archived paths only)

## Verification

- After each phase: `git grep` sweep for stale references to moved paths (active area = excluding `archived/`, `CLAUDE.backup*`) → 0 unintended leftovers
- `git diff --cached` audit each phase: deep_research.py / never-commit 5-status files / `.bmad` false replaces caught and excluded/reverted before commit
- All moves register as 100% renames in git (history preserved)
- Final tree: `docs/03-implementation/` = agent-harness-planning + agent-harness-execution + 2 ops guides only; `claudedocs/` = 7-layer canonical + templates only; `4-changes/` = 4 canonical subdirs only

## Impact

Docs-only; zero backend/frontend/CI change. ~2,400 files relocated via rename. Future placement rules codified in `claudedocs/CLAUDE.md` §Placement Rules + `5-status/README.md` §使用規則.
