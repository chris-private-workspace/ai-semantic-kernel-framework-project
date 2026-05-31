#!/usr/bin/env python3
"""
File: scripts/lint/_example_detector.py
Purpose: Reference template for writing a project-specific architecture lint.
Scope: Workflow kit foundation

Description:
    This is NOT auto-run (leading underscore -> not matched by check_*.py glob).
    Copy it to `check_<your_rule>.py` and adapt. It demonstrates the detector
    contract that run_all.py expects:
      - exit 0 on pass, non-zero on violations
      - print a final summary line (run_all.py shows the last line)

    The example below enforces AP-U6 (no version-suffix residue) by scanning
    tracked filenames for `_v1` / `_v2` / `_old` / `_new` / `_legacy`. It is a
    text-level check; for deeper rules, parse the AST (Python: `ast` module;
    TS: a tsc-based or regex pass) instead of matching filenames.

Created: {{DATE}}
"""
from __future__ import annotations

import re
import subprocess
import sys

# Directories to scan (adjust to your repo layout)
SCAN_GLOBS = ["src", "backend/src", "frontend/src", "lib"]

BANNED = re.compile(r"_(v\d+|old|new|legacy)\b", re.IGNORECASE)


def tracked_files() -> list[str]:
    """Use git so we only check committed/staged files, not build artifacts."""
    out = subprocess.run(
        ["git", "ls-files", *SCAN_GLOBS],
        capture_output=True,
        text=True,
    )
    return [line for line in out.stdout.splitlines() if line]


def main() -> int:
    violations = [f for f in tracked_files() if BANNED.search(f)]
    if violations:
        print("Version-suffix residue found (AP-U6):")
        for v in violations:
            print(f"  - {v}")
        print(f"FAIL: {len(violations)} file(s) with banned version suffix.")
        return 1
    print("OK: no version-suffix residue.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
