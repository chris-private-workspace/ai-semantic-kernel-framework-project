# ClaudeDocs — AI Assistant Execution Docs Index (V2)

**Purpose**: Directory index + placement rules for `claudedocs/` (dynamic execution records: planning candidates, change records, status analyses). Design-authority docs live in `docs/03-implementation/agent-harness-planning/`, NOT here.
**Created**: 2025-11 (V1) / rewritten 2026-06-12 (V2)
**Last Modified**: 2026-06-12
**Status**: Active

> **Modification History**
> - 2026-06-12: Full V2 rewrite (REFACTOR-007 docs-reorg) — V1 content (MAF / Phase 1-44 / intent-routing era) superseded; V1 copy preserved in git history and `archived/claudedocs-v1/`
> - 2026-03-31: V1 version 3.2.0 (historical)

---

## Authority Order

1. Root `CLAUDE.md` — project navigation (V2 Phase 49+)
2. `docs/03-implementation/agent-harness-planning/` — 21 planning docs + spike design notes (design authority)
3. This file — claudedocs placement rules only

## Directory Structure (actual, post 2026-06-12 reorg)

```
claudedocs/
├── 1-planning/          # Active planning: next-phase-candidates.md (pending single-source),
│                        #   harness-deepening-proposal, enterprise-saas-gap-analysis, scope analyses
├── 2-sprints/           # (templates only — sprint plans/checklists live in
│                        #   docs/03-implementation/agent-harness-planning/phase-XX/)
├── 3-progress/          # Daily/weekly progress (sprint progress.md lives in
│                        #   docs/03-implementation/agent-harness-execution/)
├── 4-changes/           # ONLY: bug-fixes/ (FIX-XXX) · feature-changes/ (CHANGE-XXX)
│                        #   · refactoring/ (REFACTOR-XXX) · templates/
├── 5-status/            # Status/analysis snapshots — see 5-status/README.md (total index)
├── 6-ai-assistant/      # SITUATION-1..7 prompts (active) + analysis + archives
├── 7-archive/           # Historical archive (phase-1-mvp, session-logs)
├── templates/           # spike-design-note-template.md (referenced by sprint-workflow.md §5.5)
├── CLAUDE.md            # This file
└── README.md            # Human-facing quick tour
```

## Placement Rules（鐵律）

| Content | Goes to | NOT to |
|---------|---------|--------|
| Bug fix record | `4-changes/bug-fixes/FIX-XXX-desc.md` | — |
| Feature change record | `4-changes/feature-changes/CHANGE-XXX-desc.md` | — |
| Refactoring record | `4-changes/refactoring/REFACTOR-XXX-desc.md` | — |
| **Sprint artifacts**（截圖 / DRIFT / REPOINT / AUDIT 報告）| `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-XX/artifacts/` | ❌ NOT `4-changes/`（57.19-45 歷史誤放已於 2026-06-12 遷出）|
| Status / analysis snapshot | `5-status/<topic>-<content>-YYYYMMDD.md` + add 1 line to `5-status/README.md` | — |
| Completed audit batch | `5-status/<batch>-<date>/` subdir | flat in 5-status root |
| Sprint plan / checklist | `docs/03-implementation/agent-harness-planning/phase-XX/` | ❌ NOT claudedocs |
| Sprint progress / retrospective | `docs/03-implementation/agent-harness-execution/phase-XX/sprint-XX-Y/` | ❌ NOT claudedocs |
| Pending / next-sprint candidates | `1-planning/next-phase-candidates.md`（single-source）| ❌ NOT CLAUDE.md / MEMORY.md |
| V1-era (pre-2026-04-28) docs | `archived/claudedocs-v1/` | ❌ never left in active dirs |

## Key Active Files

| File | Role |
|------|------|
| `1-planning/next-phase-candidates.md` | Pending items / carryover ADs single-source |
| `1-planning/harness-deepening-proposal-20260610.md` | Harness deepening roadmap (3 workflows / 10 slices) |
| `1-planning/enterprise-saas-gap-analysis-20260508.md` | SaaS gap analysis (root CLAUDE.md 必讀 #5) |
| `5-status/README.md` | 5-status total index (7 topic groups) |
| `5-status/README-integration-gap-abc.md` | A+B+C 15-item integration-gap index |
| `6-ai-assistant/prompts/SITUATION-1..7` | Session situation prompts (see root CLAUDE.md §AI Assistant Situation Prompts) |
| `templates/spike-design-note-template.md` | Spike design-note template (sprint-workflow.md §Step 5.5) |

## Change Record Conventions

Numbering is monotonic per type (FIX-001.. / CHANGE-001.. / REFACTOR-001..); check the highest existing number before creating. 1-page format per `.claude/rules/sprint-workflow.md` §Change Record Conventions.

## V1 History

V1 (Phase 1-48, MAF / AG-UI / intent-routing era, pre-2026-04-28) claudedocs content was archived to `archived/claudedocs-v1/` on 2026-06-12 (REFACTOR-007). The V1 version of this index is in git history.
