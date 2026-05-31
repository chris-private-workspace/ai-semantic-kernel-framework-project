# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> Bootstrapped from `claude-workflow-kit` on {{DATE}}. Customize sections marked **TODO** before relying on it.

---

## Project Overview

**{{PROJECT_NAME}}** — {{PROJECT_DESC}}

- **Primary language**: {{PRIMARY_LANGUAGE}}
- **Default branch**: {{DEFAULT_BRANCH}}

### Mission (TODO)

> One paragraph: what does this project deliver, for whom, and what makes it worth building?

### Core Constraints (TODO)

> The non-negotiable design rules for THIS project. Replace these examples with your own.
> Examples of the *kind* of constraint to write (not literal — adapt to your domain):
> 1. <e.g. all business tables carry tenant_id>
> 2. <e.g. no direct vendor SDK imports in the core layer>
> 3. <e.g. every feature must be reachable from the main API flow>

---

## Development Commands

```bash
# Format
{{FORMAT_CMD}}

# Lint
{{LINT_CMD}}

# Type check
{{TYPECHECK_CMD}}

# Test
{{TEST_CMD}}

# Project-specific architecture lints (one-stop wrapper)
python scripts/lint/run_all.py
```

---

## Code Standards — Rule Loading (Hybrid)

Rules are split into two tiers to control session context usage:

**🔴 Always-loaded (`.claude/rules/`)** — auto-loaded every session:

| Rule | Scope |
|------|-------|
| `sprint-workflow.md` | 5-step sprint flow + Day-0 verify + workload calibration |
| `file-header-convention.md` | File header + Modification History |
| `anti-patterns-checklist.md` | PR self-check list |

**📋 On-demand (`docs/rules-on-demand/`)** — Read manually when the trigger applies. Add project-specific rules here (DB conventions, API style, etc.).

See [`.claude/rules/README.md`](.claude/rules/README.md) for the full loading strategy.

---

## CRITICAL: Sprint Execution Workflow

Every sprint MUST follow this order (see `.claude/rules/sprint-workflow.md` for detail):

```
Plan → Checklist → Day-0 Verify → Code → Update Checklist → Progress Doc
```

- **Plan / checklist** live in `docs/sprints/sprint-XX-Y-plan.md` + `-checklist.md`
- **Progress** lives in `docs/sprints/sprint-XX-Y/progress.md`
- **Change records** (bug/feature/refactor) live in `claudedocs/4-changes/`

---

## Developer Preferences (TODO — adapt)

### Communication
- **Language**: <your preferred chat language>
- **Documentation**: code + design docs in English
- **Confirmation on Destructive Only**: ask before `git push` / `git reset --hard` / `--force` / deleting production code / changing CI/CD / sending external messages. NOT destructive: Write/Edit/Read within aligned scope, Glob, Grep, read-only Bash.

### Code Style
- **Comments**: English, explain WHY not WHAT
- **Git Commit**: commit only when a logical unit is complete
- **Testing**: new features must ship with unit tests

---

**Last Updated**: {{DATE}} (workflow kit bootstrap)
**Workflow Kit**: based on `claude-workflow-kit` — see `.claude/rules/` for the methodology
