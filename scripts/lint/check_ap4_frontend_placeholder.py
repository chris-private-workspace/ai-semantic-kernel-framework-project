"""
File: scripts/lint/check_ap4_frontend_placeholder.py
Purpose: V2 Lint #9 — AP-4 (Potemkin Features) detection for frontend pages.
Category: Dev tooling / V2 lint suite
Scope: Sprint 57.6 US-5 (R5 / closes AD-Reality-5)

Description:
    Enforces 04-anti-patterns.md §AP-4 at lint-time on the frontend code base:
    pages MUST NOT regress into stub-only "Coming in Phase X" / "skeleton" /
    "placeholder" / "Not implemented" copy after a real ship has happened.

    Sprint 57.5 V2 reality check found 3 placeholder pages still live (chat-v2 /
    governance / verification — D-23+24+25). Sprint 57.6 US-5 wires this lint
    so future regressions are caught at PR time. Existing 3 known placeholder
    pages remain expected findings until Phase 57.7-57.9 ship per AD-Reality-4
    (16-frontend-design.md §V2 Ship Timeline);lint output therefore expected
    non-zero this sprint until those pages ship。

Forbidden text patterns (case-insensitive):
    - 'Coming in Phase'           — V1 / V2 placeholder hint
    - 'skeleton'                  — Sprint 50.2 chat-v2 phrasing
    - 'placeholder'               — generic stub phrasing (UI-visible only;
      JSX `placeholder="..."` HTML5 attribute and TS object keys are masked
      out per Sprint 57.48 Track E false-positive correction)
    - 'TODO' / 'FIXME'            — incomplete-impl markers
    - 'land in subsequent sprints' — common 17.md drift phrasing
    - 'will be added later'       — common drift phrasing
    - 'Not implemented'            — runtime-error stub copy
    - 'WIP'                        — work-in-progress flag

All comment forms are SKIPPED (developer notes are allowed):
    - JSX block comments `{/* ... */}`
    - JS/TS line comments `// ...`
    - JS/TS block comments `/* ... */` (incl. JSDoc `/** ... */` file headers)
This is critical because file headers / MHist entries naturally mention
"placeholder" / "Sprint 49.1 placeholder" / etc. as historical notes — those
are NOT the AP-4 violation target;the target is RENDERED UI body text。

JSX attribute / TS object key masking (Sprint 57.48 Track E — closes
AD-Frontend-AP4-Pre-Existing-Lint):
    - `placeholder="..."`/`placeholder={...}` JSX/HTML5 attribute → masked
    - `placeholder: "..."` TS object key → masked
    The HTML5 `placeholder` attribute on `<input>` is a legitimate web
    standard, not an AP-4 violation. Same for fixture object keys like
    `{ placeholder: "..." }`. The AP-4 lint targets RENDERED UI body text
    (e.g. `<p>This is a placeholder for Phase 58+</p>`), not attribute
    or property names.

Excluded directories (ship-pending — will be removed once page ships):
    - frontend/src/pages/chat-v2 — Phase 57.7 candidate ship per 16.md
    - frontend/src/pages/governance — Phase 57.8 candidate ship
    - frontend/src/pages/verification — Phase 57.9 candidate ship

Usage:
    python scripts/lint/check_ap4_frontend_placeholder.py
    python scripts/lint/check_ap4_frontend_placeholder.py --root frontend/src/pages
    python scripts/lint/check_ap4_frontend_placeholder.py --verbose

Exit codes:
    0 = clean (no findings)
    1 = AP-4 findings detected (placeholder text in frontend pages)
    2 = configuration error (root path missing)

Stdlib-only (matches the 8 V2 lint scripts shipped in Sprint 49.4-56.1).

Created: 2026-05-08 (Sprint 57.6 Day 3)

Modification History:
    - 2026-05-26: Sprint 57.48 Track E — mask JSX `placeholder=` attr + TS `placeholder:` key (closes AD-Frontend-AP4-Pre-Existing-Lint)
    - 2026-05-08: Sprint 57.6 US-5 — initial creation (closes AD-Reality-5)

Related:
    - .claude/rules/anti-patterns-checklist.md §AP-4 Potemkin Features
    - 16-frontend-design.md §V2 Ship Timeline — page ship tracking
    - 57.5 reality check D-23+24+25 — chat-v2 / governance / verification placeholder
    - scripts/lint/run_all.py — orchestrator wraps this as 9th lint
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Forbidden patterns (case-insensitive). Each tuple = (pattern, human-label).
FORBIDDEN_PATTERNS: list[tuple[str, str]] = [
    (r"Coming in Phase", "Coming-in-Phase placeholder"),
    (r"\bskeleton\b", "skeleton placeholder"),
    (r"\bplaceholder\b", "explicit placeholder marker"),
    (r"\bTODO\b", "TODO marker"),
    (r"\bFIXME\b", "FIXME marker"),
    (r"land in subsequent sprints", "drift phrasing"),
    (r"will be added later", "drift phrasing"),
    (r"\bNot implemented\b", "runtime-error stub copy"),
    (r"\bWIP\b", "WIP flag"),
]

COMPILED = [(re.compile(p, re.IGNORECASE), label) for p, label in FORBIDDEN_PATTERNS]

# Comment regexes — masked to whitespace before pattern scan so file
# headers / MHist / inline notes don't trigger findings。
JSX_BLOCK_COMMENT = re.compile(r"\{/\*.*?\*/\}", re.DOTALL)
JS_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
JS_LINE_COMMENT = re.compile(r"//[^\n]*")

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

# File extensions to scan in frontend pages tree。
SCAN_EXTENSIONS = frozenset({".tsx", ".ts", ".jsx", ".js"})

# Ship-pending directories excluded from AP-4 lint per 16-frontend-design.md
# §V2 Ship Timeline。Remove once each page ships in Phase 57.7-57.9。
EXCLUDE_DIRS_DEFAULT = ("chat-v2", "governance", "verification")


def mask_comments(src: str) -> str:
    """Mask all comment forms (JSX block / JS block / JS line) + JSX
    `placeholder=` attribute + TS `placeholder:` key to whitespace.

    Order matters:
        1. JSX `{/* ... */}` first so the inner `/* ... */` isn't double-counted
        2. JS block / line comments
        3. JSX `placeholder=` attribute + TS `placeholder:` key — masked AFTER
           comments so we don't accidentally unmask inside a stripped comment

    The `placeholder` attribute mask is critical: HTML5 `<input placeholder="...">`
    and `<textarea placeholder="...">` are valid web-standard usage and must
    NOT trigger the AP-4 `\\bplaceholder\\b` rule (Sprint 57.48 Track E
    closes AD-Frontend-AP4-Pre-Existing-Lint).
    """
    masked = JSX_BLOCK_COMMENT.sub(
        lambda m: " " * (m.end() - m.start()), src
    )
    masked = JS_BLOCK_COMMENT.sub(
        lambda m: " " * (m.end() - m.start()), masked
    )
    masked = JS_LINE_COMMENT.sub(
        lambda m: " " * (m.end() - m.start()), masked
    )
    masked = JSX_PLACEHOLDER_ATTR.sub(
        lambda m: " " * (m.end() - m.start()), masked
    )
    masked = TS_PLACEHOLDER_KEY.sub(
        lambda m: " " * (m.end() - m.start()), masked
    )
    return masked


def check_file(path: Path) -> list[str]:
    """Return AP-4 finding messages for `path`. Empty list = clean."""
    try:
        src = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return [f"{path}: read error during AP-4 lint: {exc}"]

    masked = mask_comments(src)
    findings: list[str] = []
    for pat, label in COMPILED:
        for match in pat.finditer(masked):
            line_no = masked[: match.start()].count("\n") + 1
            snippet = src.splitlines()[line_no - 1].strip()[:80]
            findings.append(
                f"{path}:{line_no}: AP-4 finding ({label}): {snippet}"
            )
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="AP-4 (Potemkin Features) frontend page placeholder lint — V2 lint #9."
    )
    parser.add_argument(
        "--root",
        default="frontend/src/pages",
        help="Frontend pages root to scan (default: frontend/src/pages).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print clean files explicitly (default: only findings + summary).",
    )
    parser.add_argument(
        "--exclude",
        default=",".join(EXCLUDE_DIRS_DEFAULT),
        help=(
            "Comma-separated directory NAMES (not paths) to exclude. "
            "Default: chat-v2,governance,verification (3 ship-pending pages "
            "per 16-frontend-design.md §V2 Ship Timeline; remove from list as each ships)."
        ),
    )
    args = parser.parse_args(argv)
    exclude_dirs = frozenset(
        d.strip() for d in args.exclude.split(",") if d.strip()
    )

    root = Path(args.root)
    if not root.exists():
        print(
            f"ERROR: root path does not exist: {root}\n"
            f"       Hint: --root must point to the frontend pages tree "
            f"(typically `frontend/src/pages`).",
            file=sys.stderr,
        )
        return 2

    all_findings: list[str] = []
    files_scanned = 0
    for ext in SCAN_EXTENSIONS:
        for path in sorted(root.rglob(f"*{ext}")):
            # Skip node_modules / dist / build artifacts defensively.
            if any(part in {"node_modules", "dist", "build"} for part in path.parts):
                continue
            # Skip ship-pending dirs (chat-v2 / governance / verification).
            if any(part in exclude_dirs for part in path.parts):
                continue
            files_scanned += 1
            findings = check_file(path)
            all_findings.extend(findings)
            if args.verbose and not findings:
                print(f"[clean] {path}")

    if all_findings:
        for f in all_findings:
            print(f)
        print(
            f"\nAP-4 lint FAILED: {len(all_findings)} finding(s) "
            f"in {files_scanned} file(s) scanned under {root}.",
            file=sys.stderr,
        )
        return 1

    print(
        f"OK: AP-4 check passed in {root} ({files_scanned} file(s) scanned)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
