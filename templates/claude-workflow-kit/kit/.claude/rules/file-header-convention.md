# File Header & Modification Convention

**Purpose**: Standard metadata header on new files + a 1-line-per-entry Modification History, so anyone (human or AI) can grasp a file's purpose fast and trace why it changed.
**Category**: Development Process / Standards
**Status**: Active

---

## Why

| Pain | Fix |
|------|-----|
| AI/dev opens a file and can't tell its purpose → wasted exploration | Header pins purpose + scope in one read |
| "Structure exists but no real content" (Potemkin) | Description + Key Components force a real statement of intent |
| `git blame` can't answer "why was it designed this way" | Section headers carry the Why + Alternative considered |
| Changes accumulate with no history | Modification History records behavioral/structural changes |

---

## New File Header Template

Adapt the comment syntax to {{PRIMARY_LANGUAGE}} (`"""..."""` for Python, `/** ... */` for TS/JS, `// ...` for Go, etc.):

```
File: <relative path>
Purpose: <one sentence>
Scope: <Sprint XX.Y / module>

Description:
    <2-5 lines: what it does, why it exists, what it interacts with>

Key Components:
    - ClassA: <purpose>
    - function_b(): <purpose>

Created: YYYY-MM-DD (Sprint XX.Y)
Last Modified: YYYY-MM-DD

Modification History (newest-first):
    - YYYY-MM-DD: Initial creation (Sprint XX.Y) — <reason>
```

---

## Section Header Convention

For each important class / large function / logic block, add a short comment stating **WHY** (not WHAT):

```
# === ClassName: one-line role ===
# Why: <the problem this solves / the decision behind it>
# Alternative considered:
#   - <option> — rejected because <reason>
```

---

## Modification History Rules

### Format — 1 line max per entry

```
Modification History (newest-first):
    - YYYY-MM-DD: <verb> <what> (Sprint XX.Y) — <one-line reason>
```

- Each entry must fit one line (respect your linter's max-line-length including indent).
- Prefer verbs over noun phrases (`extract` > `extraction of`; `add` > `addition of`).
- Don't quote long paths; use a short scope keyword instead.
- If the reason doesn't fit one line → move detail to the commit message body or the `claudedocs/4-changes/FIX-XXX` record.

### Verbs

| Verb | Use |
|------|-----|
| Add | new feature / method |
| Fix | bug fix |
| Refactor | restructure, behavior unchanged |
| Update | enhance existing behavior |
| Remove | delete feature / dead code |
| Align | conform to a spec / contract |

### When to record

| Change type | Record? | Example |
|-------------|---------|---------|
| **Trivial** | ❌ No | typo / format / variable rename |
| **Behavioral** | ✅ Yes | bug fix / new feature / logic refactor |
| **Structural** | ✅ Yes | file split / interface change |

---

## Prohibited

1. **Inline history comments** — `x = compute()  # changed from old() on 2026-05-01`. Use Modification History; `git blame` already has the detail.
2. **Dead-code comments** — delete commented-out old code; git has the history.
3. **Vague commit messages** — `update` / `fix` / `changes`. Use `type(scope): specific what + why`.
4. **Skipping `claudedocs/4-changes/`** for behavioral changes.
5. **Multi-line / bulleted Modification History entries** — one line each; rich detail goes in the commit body or the 4-changes record.

---

## Exceptions

- Auto-generated files (migrations, proto, openapi): may omit the hand-written header.
- Third-party vendored files: leave as-is.
- Empty `__init__.py` / index files: may omit.
- Test files: a simplified header is fine (File / Purpose / Created / Modified).
