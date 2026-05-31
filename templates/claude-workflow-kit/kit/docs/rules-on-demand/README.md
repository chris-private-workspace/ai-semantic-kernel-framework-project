# On-Demand Rules

Place situational rules here. They are **not** auto-loaded into the session — the AI must `Read` a file when its trigger applies (see `.claude/rules/README.md`).

## Why here and not under `.claude/`

Claude Code recursively scans the whole `.claude/` tree into project memory every session. Rules placed under `.claude/` are always loaded, which defeats the "on-demand" intent. Keeping them under `docs/rules-on-demand/` keeps them out of the auto-scan until explicitly Read.

## Suggested starters (create as you need them)

| File | Trigger |
|------|---------|
| `git-workflow.md` | commit message format / branch naming |
| `testing.md` | writing tests / coverage planning |
| `code-quality.md` | fixing lint / type-check errors |
| `<your-domain>.md` | DB schema, API style, auth, observability, … |

Each rule file should state its **Trigger** at the top so the AI knows when to load it.
