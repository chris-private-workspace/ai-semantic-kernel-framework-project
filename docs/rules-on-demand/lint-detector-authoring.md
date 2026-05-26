# Lint Detector Authoring — Code-Aware Masking Discipline

**Purpose**: When authoring AP-N anti-pattern detectors under `scripts/lint/`, mask legitimate code patterns containing the trigger token BEFORE applying the main grep, to avoid false-positive noise that obscures real signal.

**Category**: Development Process / Lint Authoring
**Created**: 2026-05-26 (Sprint 57.51)
**Last Modified**: 2026-05-26
**Status**: Active

> **Modification History**
> - 2026-05-26: Sprint 57.51 — Initial creation (closes AD-Lint-Detector-Code-Aware-Masking-Rule from Sprint 57.48 D-DAY0-6)

---

## Why

Sprint 57.48 D-DAY0-6 (root-cause investigation of 8/9 V2 lints carryover):

`scripts/lint/check_ap4_frontend_placeholder.py` was authored Sprint 57.6 with a `\bplaceholder\b` regex intended to catch UI body copy like `<p>This is a placeholder for Phase 58+</p>`. Once the codebase grew, the same regex began matching three classes of LEGITIMATE code that happen to contain the literal `placeholder`:

1. **HTML5 `placeholder="..."` JSX attribute** — a web-standard input hint, NOT an AP-4 violation
2. **TypeScript object keys / interface fields literally named `placeholder`** — e.g. fixture data `{ placeholder: "Enter email" }`
3. (Hypothetically) **shadcn-utility `placeholder:` Tailwind modifier** — future variant if utility classes are introduced

Result: ~12 false-positive findings accumulated across Sprint 57.46-47, leaving 8/9 V2 lints status for 2 sprints. The real signal (genuine AP-4 placeholder UI copy) was buried under attribute / key noise. Sprint 57.48 Track E fixed the detector — NOT the pages — by adding two regex masks (`JSX_PLACEHOLDER_ATTR` + `TS_PLACEHOLDER_KEY`) that pre-strip the legitimate matches from the line buffer.

The generalizable lesson: **lint detectors authored to find anti-patterns must mask out legitimate code patterns that happen to literally contain the trigger token, to avoid noise that hides real signal.** This rule codifies the discipline so future AP-N detector authoring inherits the pattern out of the box.

**Cost of skipping this rule**: 2 sprints (~5-7 days wall clock) carrying 8/9 V2 lints status, masking other real signals; ~12 false-positive findings to triage.

---

## Core Pattern (3 steps)

When writing a new AP-N detector or maintaining an existing one, follow these three steps in order:

### Step 1 — Identify trigger token

What literal string (or regex) is the detector looking for? Document the trigger in the detector's docstring `Forbidden text patterns` section. Example from AP-4:

```
'placeholder' — generic stub phrasing (UI-visible only)
```

### Step 2 — Enumerate legitimate matches

Before writing the regex, ask: **what code patterns LEGITIMATELY contain this token without being the anti-pattern?** Common classes to consider:

- **JSX/HTML attributes** (`placeholder="..."`, `aria-label="..."`, `title="..."`)
- **TS object keys / interface fields** (`{ placeholder: ..., title: ... }`)
- **String literals inside test fixtures** (`expect(x).toBe("placeholder text")`)
- **Comment blocks** (file headers / MHist / JSDoc / `// TODO` archaeology notes)
- **Identifier names** (`function getPlaceholderText()`, `const PLACEHOLDER_BAD_PATTERN = ...`)
- **CSS class modifiers** (Tailwind `placeholder:text-gray-400`)

Each class is a candidate mask. Enumerate them up front; under-enumeration costs sprints of carryover false-positives.

### Step 3 — Write masks

For each legitimate-match class, write a regex substitution that pre-strips the match from the line buffer BEFORE the main pattern grep. Use named constants (NOT inline regex) for maintainability. Apply masks in dependency order — strip larger structures (block comments) before smaller ones (line comments) before key/attr patterns.

Detector flow becomes:

```
src → mask_comments(src) → mask_jsx_attrs(masked) → mask_ts_keys(masked) → main_pattern.findall(masked)
```

---

## Concrete Examples

### Example 1: AP-4 `placeholder=` JSX attr mask (Sprint 57.48 Track E — closes AD-Frontend-AP4-Pre-Existing-Lint)

Verbatim from `scripts/lint/check_ap4_frontend_placeholder.py` lines 107-156:

```python
# JSX attribute / TS object key masks (Sprint 57.48 Track E — closes
# AD-Frontend-AP4-Pre-Existing-Lint). The HTML5 `placeholder` attribute and
# TS object keys named `placeholder` are NOT AP-4 violations; they're
# legitimate API/standard names. Mask them before the pattern scan so the
# `\bplaceholder\b` rule only catches UI body text.
JSX_PLACEHOLDER_ATTR = re.compile(
    r"placeholder\s*=\s*(?:\"[^\"]*\"|'[^']*'|\{[^}]*\})",
    re.IGNORECASE,
)
TS_PLACEHOLDER_KEY = re.compile(r"\bplaceholder\s*:", re.IGNORECASE)


def mask_comments(src: str) -> str:
    """Mask all comment forms + JSX `placeholder=` attribute +
    TS `placeholder:` key to whitespace.

    Order matters:
        1. JSX `{/* ... */}` first so inner `/* ... */` isn't double-counted
        2. JS block / line comments
        3. JSX `placeholder=` attribute + TS `placeholder:` key — masked AFTER
           comments so we don't accidentally unmask inside a stripped comment
    """
    masked = JSX_BLOCK_COMMENT.sub(lambda m: " " * (m.end() - m.start()), src)
    masked = JS_BLOCK_COMMENT.sub(lambda m: " " * (m.end() - m.start()), masked)
    masked = JS_LINE_COMMENT.sub(lambda m: " " * (m.end() - m.start()), masked)
    masked = JSX_PLACEHOLDER_ATTR.sub(lambda m: " " * (m.end() - m.start()), masked)
    masked = TS_PLACEHOLDER_KEY.sub(lambda m: " " * (m.end() - m.start()), masked)
    return masked
```

Key properties:

- **Named constants** (`JSX_PLACEHOLDER_ATTR` / `TS_PLACEHOLDER_KEY`) instead of inline regex — discoverable, testable, maintainable
- **Whitespace-substitution** (not delete) — preserves line numbers in findings reports
- **Order matters** — comments first (so the inner content of comments doesn't trigger downstream attr/key matches), then structural masks
- **Case-insensitive** — matches AP-4's `re.IGNORECASE` main grep policy

### Example 2: Hypothetical AP-5 "TODO comment in production code" detector

Suppose a future AP-5 detector aims to catch `TODO` markers in production source files. Trigger token = `TODO`. Legitimate-match enumeration:

- **Test files** (`*.test.ts`, `*_test.py`) — TODOs in tests are conventional triage markers
- **Markdown code fences in source comments** (e.g. JSDoc embedded examples)
- **Git-blame archaeology comments** (`// historical: TODO from 2024-01-01 — already resolved`)
- **Identifier names** (`function processTODOQueue()`)

Masks to write:

```python
TEST_FILE_PATH = re.compile(r"\.(test|spec)\.(ts|tsx|js|jsx|py)$")  # path-level skip
MARKDOWN_CODE_FENCE = re.compile(r"```[\s\S]*?```")                  # block-level mask
ARCHAEOLOGY_COMMENT = re.compile(r"//\s*historical:.*", re.IGNORECASE)
TODO_IN_IDENTIFIER = re.compile(r"\b[a-zA-Z_]*TODO[a-zA-Z_]*\b")
```

Same 3-step discipline applies; just substitute the domain-specific legitimate matches.

---

## Anti-patterns

- ❌ **Raw `\bX\b` for tokens with common legitimate usage** — e.g. `\bplaceholder\b` matches HTML5 attr unmodified. Always enumerate legitimate matches first.
- ❌ **Running detector on output already pre-stripped by another tool without re-masking** — mask order matters; if input is partially stripped, downstream masks may match unintended content. Always compose masks in a single ordered pipeline within the detector.
- ❌ **Skipping the mask step "for performance"** — false positives waste more developer time (triage cost + carryover sprints) than the regex `sub` call adds to detector runtime. Mask cost is negligible (~ms); FP triage cost is hours.
- ❌ **Hardcoding masks inline without a named constant** — Sprint 57.48 fix used `JSX_PLACEHOLDER_ATTR` + `TS_PLACEHOLDER_KEY` constants for maintainability. Inline regex literals scattered through `check_line()` are unsearchable, untestable, and impossible to extend.

---

## Cross-references

- [`.claude/rules/anti-patterns-checklist.md`](../../.claude/rules/anti-patterns-checklist.md) — 11-point PR self-check (AP-2 / AP-4 / AP-5 row authorship)
- [`scripts/lint/run_all.py`](../../scripts/lint/run_all.py) — V2 lint aggregator wrapping all 9 V2 lints
- `scripts/lint/check_ap1_pipeline_disguise.py` — AP-1 detector (existing; pattern-based without trigger-token masks; lower FP surface area)
- `scripts/lint/check_ap4_frontend_placeholder.py` — AP-4 detector (the case study for this rule)
- [`docs/03-implementation/agent-harness-planning/04-anti-patterns.md`](../03-implementation/agent-harness-planning/04-anti-patterns.md) — V2 11 anti-patterns full spec

---

**When to Read this rule**: writing a NEW AP-N detector / maintaining an existing AP-N detector / debugging a detector false-positive / extending an existing detector to a new file class. If you are authoring a `scripts/lint/check_ap*_*.py` file, this rule is mandatory reading.
