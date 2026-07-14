"""
File: scripts/lint/check_rules_hygiene.py
Purpose: Always-loaded rule-file hygiene lint — size budgets on .claude/rules/*
    + CLAUDE.md, and a 400-char cap on calibration-matrix.md table rows.
Category: Cross-cutting / DevOps tooling
Scope: REFACTOR-011 (2026-07-14)

Description:
    Claude Code auto-loads CLAUDE.md + every .claude/rules/*.md into EVERY
    session's context. Twice (REFACTOR-005 2026-05-31, REFACTOR-009
    2026-07-14) the sprint-workflow.md scope-class matrix re-accumulated
    full per-sprint narration in its status cells (~2000+ chars/cell, 47%
    of the file) because the only guard was an advisory prose note — each
    sprint closeout copied the previous bloated cell as its template and
    nothing failed. This lint is the missing mechanical guard:

    Check A — matrix row cap: every table row in calibration-matrix.md
        (lines starting "| `") must be <= MATRIX_ROW_MAX chars. Full
        narration belongs in calibration-log.md §1 (+ the sprint's memory
        subfile + retrospective.md), never in the matrix cell.
    Check B — size budgets: each always-loaded file must stay under its
        byte budget (current size + ~25-40% headroom). Exceeding a budget
        means evidence/history is accumulating in a rules file — move it
        to an on-demand doc (docs/rules-on-demand/ or calibration-log).
    A budgeted file that is MISSING is also a violation: if the file was
    intentionally moved/renamed, update SIZE_BUDGETS consciously here.

Key Components:
    - Violation: NamedTuple (file, kind, detail). NamedTuple, NOT @dataclass:
      tests load this script via importlib file-path (Sprint 57.165 lesson —
      @dataclass + future-annotations breaks under importlib module loading).
    - find_violations(repo_root): pure function; unit-testable via tmp_path.
    - main(): CLI wrapper; exit 0 = clean, 1 = violations found.

Usage:
    python scripts/lint/check_rules_hygiene.py [--root <repo_root>]

Created: 2026-07-14 (REFACTOR-011)
Last Modified: 2026-07-14

Modification History (newest-first):
    - 2026-07-14: Initial creation (REFACTOR-011) — the enforcement REFACTOR-005/-009 lacked

Related:
    - claudedocs/4-changes/refactoring/REFACTOR-011-*.md — rationale + budgets
    - .claude/rules/sprint-workflow.md §Sprint Closeout (anti-triple-source policy)
    - docs/03-implementation/agent-harness-execution/calibration-matrix.md
"""

import argparse
import sys
from pathlib import Path
from typing import NamedTuple

MATRIX_FILE = "docs/03-implementation/agent-harness-execution/calibration-matrix.md"
MATRIX_ROW_MAX = 400

# Byte budgets = size at REFACTOR-011 (2026-07-14) + ~25-40% headroom.
# Raising a budget is a conscious decision: justify it in the commit that
# raises it (usually the right fix is moving content on-demand instead).
SIZE_BUDGETS: dict[str, int] = {
    "CLAUDE.md": 45_000,  # 35,920 @ 2026-07-14
    ".claude/rules/sprint-workflow.md": 60_000,  # 53,684 @ 2026-07-14
    ".claude/rules/file-header-convention.md": 24_000,  # 18,043 @ 2026-07-14
    ".claude/rules/multi-tenant-data.md": 18_000,  # 13,601 @ 2026-07-14
    ".claude/rules/anti-patterns-checklist.md": 14_000,  # 9,608  @ 2026-07-14
    ".claude/rules/README.md": 14_000,  # 9,882  @ 2026-07-14
    MATRIX_FILE: 60_000,  # 28,544 @ 2026-07-14 (on-demand, but rows accrete per sprint)
}


class Violation(NamedTuple):
    file: str
    kind: str  # "missing" | "over_budget" | "matrix_row"
    detail: str


def find_violations(repo_root: Path) -> list[Violation]:
    """Return all hygiene violations under repo_root (empty list = clean)."""
    violations: list[Violation] = []

    for rel, budget in SIZE_BUDGETS.items():
        path = repo_root / rel
        if not path.is_file():
            violations.append(
                Violation(
                    rel,
                    "missing",
                    "budgeted always-loaded file not found — if moved/renamed, "
                    "update SIZE_BUDGETS in check_rules_hygiene.py",
                )
            )
            continue
        size = path.stat().st_size
        if size > budget:
            violations.append(
                Violation(
                    rel,
                    "over_budget",
                    f"{size:,} bytes > budget {budget:,} — move evidence/history "
                    f"to an on-demand doc (docs/rules-on-demand/ or calibration-log.md)",
                )
            )

    matrix = repo_root / MATRIX_FILE
    if matrix.is_file():
        for lineno, line in enumerate(
            matrix.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if line.startswith("| `") and len(line) > MATRIX_ROW_MAX:
                violations.append(
                    Violation(
                        MATRIX_FILE,
                        "matrix_row",
                        f"L{lineno} row is {len(line)} chars > {MATRIX_ROW_MAX} — "
                        f"keep verdict + ratio/band + rollback trigger + pointer; "
                        f"full narration goes to calibration-log.md §1",
                    )
                )
    # A missing matrix file is already reported by the SIZE_BUDGETS pass.

    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Always-loaded rules hygiene: size budgets + matrix-row cap."
    )
    parser.add_argument(
        "--root",
        default=str(Path(__file__).resolve().parents[2]),
        help="Repo root (default: two levels above this script).",
    )
    cli = parser.parse_args(argv)
    repo_root = Path(cli.root)

    violations = find_violations(repo_root)
    if not violations:
        n = len(SIZE_BUDGETS)
        print(
            f"rules-hygiene: OK ({n} budgeted files + matrix rows <= {MATRIX_ROW_MAX} chars)"
        )
        return 0

    print(f"rules-hygiene: {len(violations)} violation(s):")
    for v in violations:
        print(f"  [{v.kind}] {v.file}: {v.detail}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
