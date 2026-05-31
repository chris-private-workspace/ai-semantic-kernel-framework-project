#!/usr/bin/env python3
"""
File: scripts/lint/run_all.py
Purpose: One-stop wrapper that runs every architecture-lint detector and reports
         an aggregate pass/fail so CI and pre-commit have a single entry point.
Scope: Workflow kit foundation

Description:
    Discovers sibling `check_*.py` detector scripts, runs each as a subprocess,
    and aggregates results. Exit 0 = all green; non-zero = "<failed>/<total>"
    with a per-script line summary. Add detectors by dropping a new `check_*.py`
    next to this file (see `_example_detector.py` for the pattern).

Created: {{DATE}}
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

LINT_DIR = Path(__file__).resolve().parent


def discover_detectors() -> list[Path]:
    """Every check_*.py sibling is a detector. Order is stable (sorted)."""
    return sorted(p for p in LINT_DIR.glob("check_*.py") if p.is_file())


def run_detector(script: Path) -> tuple[bool, str]:
    """Run one detector; return (passed, last_output_line)."""
    proc = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
    )
    output = (proc.stdout + proc.stderr).strip()
    last_line = output.splitlines()[-1] if output else "(no output)"
    return proc.returncode == 0, last_line


def main() -> int:
    detectors = discover_detectors()
    if not detectors:
        print("No detectors found (add check_*.py next to run_all.py). OK.")
        return 0

    failed = 0
    for script in detectors:
        passed, summary = run_detector(script)
        mark = "OK " if passed else "FAIL"
        print(f"  [{mark}] {script.name}: {summary}")
        if not passed:
            failed += 1

    total = len(detectors)
    if failed:
        print(f"\n{failed}/{total} architecture lints FAILED.")
        return 1
    print(f"\nAll {total} architecture lints passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
