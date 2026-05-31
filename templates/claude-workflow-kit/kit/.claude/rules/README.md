# `.claude/rules/` + `docs/rules-on-demand/` Index

**Purpose**: Development rules overview + on-demand loading guide for **{{PROJECT_NAME}}**.
**Status**: Active

---

## Loading Strategy (Hybrid)

To control session context usage, rules are split into two tiers:

| Location | Behavior | Use |
|----------|----------|-----|
| **`.claude/rules/*.md`** (3 always-loaded + this README) | ✅ Claude Code auto-loads every session | High-frequency critical rules |
| **`docs/rules-on-demand/*.md`** | ⏸️ Not loaded by default; AI must `Read` when triggered | Situational rules |

**Why not put everything in `.claude/`?** Claude Code recursively scans the whole `.claude/` tree into project memory. On-demand rules placed under `.claude/` would still be auto-loaded, defeating the purpose. Keeping them under `docs/rules-on-demand/` keeps them out of the auto-scan until explicitly Read.

**Why Hybrid?** Loading every rule costs context at session start; loading nothing risks the AI missing the sprint workflow / file-header / anti-pattern discipline. Hybrid keeps the 3 highest-ROI rules always-loaded and the rest on-demand.

---

## 🔴 Always-Loaded (3 critical, always in context)

| File | Purpose |
|------|---------|
| [`sprint-workflow.md`](./sprint-workflow.md) | Plan → Checklist → Day-0 Verify → Code → Update → Progress + workload calibration |
| [`file-header-convention.md`](./file-header-convention.md) | File header + Modification History (1-line max) |
| [`anti-patterns-checklist.md`](./anti-patterns-checklist.md) | PR self-check list (universal + project-specific) |

---

## 📋 On-Demand (Read when triggered)

> **AI rule**: when you hit a trigger below, **Read the rule file BEFORE starting to code.**
> Add your project's situational rules here. Suggested starters:

| File (create under `docs/rules-on-demand/`) | Trigger (when to Read) |
|------|------------------------|
| `git-workflow.md` | Writing commit messages / opening a branch |
| `testing.md` | Writing tests / planning test coverage |
| `code-quality.md` | Fixing lint / type-check errors |
| `<your-domain>.md` | Domain-specific conventions (DB schema, API style, auth, …) |

---

## Task-to-Rule Quick Map

| Situation | Always | Read on-demand |
|-----------|--------|----------------|
| Start a sprint | `sprint-workflow.md` | — |
| Create a new file | `file-header-convention.md` | `<domain>.md` |
| Code review / PR self-check | `anti-patterns-checklist.md` | `git-workflow.md` |

---

## Maintenance

- Rule changes = workflow changes → tag PR title `chore(rules)`.
- New rules go through the standard `sprint-workflow.md` flow.
- Retire old rules via an `archive` change, not deletion (preserve git history).
- **Promote/demote**: if an on-demand rule is Read in 3 consecutive sprints, promote it to always-loaded (and vice versa).

---

**Maintained per** `claude-workflow-kit`. The methodology layer is portable; the content is yours to grow.
