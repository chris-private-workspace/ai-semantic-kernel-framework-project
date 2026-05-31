# claudedocs — AI Assistant Execution Docs

Dynamic execution record shared by the AI assistant and developer, separate from `docs/`.

```
claudedocs/
├── 1-planning/          # overall planning
├── 4-changes/           # change records
│   ├── bug-fixes/       # FIX-XXX-*.md
│   ├── feature-changes/ # CHANGE-XXX-*.md
│   └── refactoring/     # REFACTOR-XXX-*.md
└── templates/           # record templates (copy these)
```

## Change record conventions

When fixing a bug or changing a feature, create a record using the matching template in `templates/`:

| Type | Directory | Naming |
|------|-----------|--------|
| Bug Fix | `4-changes/bug-fixes/` | `FIX-XXX-description.md` |
| Feature Change | `4-changes/feature-changes/` | `CHANGE-XXX-description.md` |
| Refactoring | `4-changes/refactoring/` | `REFACTOR-XXX-description.md` |

See `.claude/rules/sprint-workflow.md` §Change Record Conventions.
