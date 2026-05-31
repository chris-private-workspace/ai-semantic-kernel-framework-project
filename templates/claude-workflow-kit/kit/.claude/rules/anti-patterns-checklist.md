# Anti-Patterns Checklist (PR must pass)

**Purpose**: A code-review self-check list. Every PR must answer ✅ / ❌ / N/A for each item before merge.
**Category**: Framework / Development Process
**Status**: Active

> This file ships with **universal** anti-patterns. Add your project's own lessons under `§Project-Specific` as you learn them — start empty, append one line each time you hit a new trap.

---

## How to use

Before opening a PR, fill ✅ (pass) / ❌ (fail) / N/A for each item. Any ❌ must be fixed before merge. Reviewers treat this as a mandatory gate.

---

## Universal Anti-Patterns

### AP-U1: Orphan / Side-Track Code
**Symptom**: code exists but nothing on the main flow calls it; modules tagged "PoC"/"experimental" that never get retired; multiple parallel versions.
**Self-check**: Can the new code be traced from a real entry point (API route / main / exported surface)? Is there no `_v1` / `_v2` / `_old` duplicate?
**Fix**: main-flow code must be reachable; PoCs go in an `experimental/` area with a deadline; delete unused code (git keeps history).

### AP-U2: Partial Features / TODO Stubs
**Symptom**: function exists but throws "not implemented"; core logic left as `// TODO`; mock/placeholder data shipped as real.
**Self-check**: If this feature were toggled on, would it actually work end-to-end? Coverage ≥ 80%?
**Fix**: start it = finish it. No TODO for core behavior; no fake data.

### AP-U3: Cross-Directory Scattering
**Symptom**: one concern's code spread across 3+ directories that don't know about each other; duplicate dataclasses/types.
**Self-check**: Is this feature's code concentrated in one place? Any duplicate type definitions?
**Fix**: keep each concern in one module; shared logic in a clearly-named shared location.

### AP-U4: Naming-Behavior Mismatch (Potemkin)
**Symptom**: a `validator` that only saves; a `verifier` that doesn't verify; empty stub with a complete-looking interface.
**Self-check**: Does the name match what it actually does? Is there a negative test (what breaks if you turn it off)?
**Fix**: name = behavior; add an end-to-end + negative test.

### AP-U5: Mock vs Real Divergence
**Symptom**: dev uses a mock, prod uses the real thing, and the two drift; bugs reproduce only in prod.
**Self-check**: Do mock and real share the same interface/ABC? Does CI exercise the real path?
**Fix**: mock and real implement the same interface; CI runs the real path; mock doesn't simplify away edge cases.

### AP-U6: Version-Suffix Residue
**Symptom**: `_v1` / `_v2` / `_old` / `_new` / `_legacy` in file / class / function names; rename left half-done.
**Self-check**: Any version suffixes in this PR? Does naming reflect actual behavior? Did you grep the whole codebase for stragglers?
**Fix**: no version suffixes; complete renames with a full-codebase grep; no leftover aliases unless there's a documented deprecation plan.

---

## Project-Specific (TODO — grow this)

> Append your own as you learn them. One entry each:
>
> ### AP-P1: <name>
> **Symptom**: …
> **Self-check**: …
> **Fix**: …

*(none yet)*

---

## PR Template Insert

```markdown
## Anti-Pattern Checklist
- [ ] AP-U1: No orphan / side-track code (traceable from entry point)
- [ ] AP-U2: No partial features / TODO stubs (works end-to-end + tests)
- [ ] AP-U3: No cross-directory scattering (one concern, one place)
- [ ] AP-U4: Name matches behavior (+ negative test)
- [ ] AP-U5: Mock and real share the same interface
- [ ] AP-U6: No version suffixes; naming consistent
<!-- add AP-P* project-specific rows here -->
```
