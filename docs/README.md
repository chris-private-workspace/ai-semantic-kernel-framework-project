# docs/ — Project Documentation Index (V2)

**Purpose**: Navigation for `docs/` in the V2 era (Phase 49+, agent harness rebuild).
**Created**: 2025-11-14 (V1 BMAD) / rewritten 2026-06-12 (V2)
**Last Modified**: 2026-06-12
**Status**: Active

> **Modification History**
> - 2026-06-12: Full V2 rewrite (REFACTOR-007 docs-reorg) — V1 BMAD-phase content superseded; V1 dirs archived to `archived/docs-v1/`
> - 2025-11-14: V1 initial (BMAD Method, historical)

---

## Authority Order

1. Root `CLAUDE.md` — project navigation
2. `03-implementation/agent-harness-planning/` — **V2 design authority** (21 planning docs + spike design notes 21+)
3. Everything else below

## Directory Map

| Directory | Role | Era |
|-----------|------|-----|
| **`03-implementation/agent-harness-planning/`** | ⭐ V2 規劃權威：21 docs（00-vision … 17-cross-category-interfaces …）+ spike design notes + per-phase sprint plan/checklist | V2 active |
| **`03-implementation/agent-harness-execution/`** | ⭐ V2 執行紀錄：phase-49~57 per-sprint progress.md / retrospective.md / artifacts/ | V2 active |
| `rules-on-demand/` | 11 條 on-demand 開發規則（trigger 表見 `.claude/rules/README.md`）| V2 active |
| `08-development-log/` | Phase 57+ 開發日誌 | V2 active |
| `09-git-worktree-working-folder/` | Worktree 工作筆記 | V2 |
| `02-architecture/` | 架構參考 | shared |
| `06-skills/` | Skill 定義 | shared |
| `00-discovery/` | 2025-11 需求發現（brainstorming / product brief）| V1 reference |
| `07-analysis/` | **V1 歷史研究資產（刻意保留）**：V9 codebase analysis / claude-code-study (30 waves) / claude-agent-study / poc-agent-team | V1 reference |
| `03-implementation/` root files | `azure-service-principal-setup.md` + `local-development-guide.md`（仍有用的 ops setup）| shared |

## Root Files

| File | Role |
|------|------|
| `LOCAL-DEV-SETUP.md` | Local dev environment setup |
| `bmm-workflow-status.yaml` | BMAD workflow status tracking（root CLAUDE.md §Important Notes 沿用）|

## Archived (V1, Phase 1-48)

V1-era content was moved to **`archived/docs-v1/`** on 2026-06-12 (REFACTOR-007):
`01-planning/`(PRD) · `phase-2/` · `admin-guide/` · `api/` · `guides/` · `user-guide/` · `06-user-guide/` · `04-review/` · `04-usage/` · `05-reference/` · `migration/` · `AGENT-FRAMEWORK-AUDIT.md` · `03-implementation/{sprint-planning, sprint-execution, archive, architecture-designs, implementation-guides, legacy, migration, feature-summary, V1 root guides}`

The full V1 codebase lives in `archived/v1-phase1-48/`; V1 CLAUDE.md in `CLAUDE.backup.md`.
