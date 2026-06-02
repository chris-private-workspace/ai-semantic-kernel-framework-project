"""
File: scripts/lint/run_all.py
Purpose: One-stop wrapper that invokes all V2 architecture lint scripts with
    the correct CLI arguments + emits a per-script timing summary + final
    aggregated pass/fail count. Replaces the separate manual invocations
    that historically caused silent-skip false-greens when the `--root` arg
    mismatched a script's expectation (see Sprint 53.7 Day 0 drift D1).
Category: Cross-cutting / DevOps tooling
Scope: Sprint 53.7 US-1 (closes AD-Lint-1) / Sprint 55.3 (adds 7th lint via AD-Cat7-1)

Modification History:
    - 2026-06-02: Sprint 57.67 — add 10th lint check_event_schema_sync (A-5b codegen parity)
    - 2026-05-08: Sprint 57.6 Day 3 — add 9th lint check_ap4_frontend_placeholder (closes AD-Reality-5)
    - 2026-05-06: Sprint 56.1 Day 4 — add 8th lint check_rls_policies (closes US-5)
    - 2026-05-04: Sprint 55.3 — add 7th lint check_sole_mutator (closes AD-Cat7-1)
    - 2026-05-04: Sprint 53.7 — initial 6-lint wrapper (closes AD-Lint-1)

Description:
    Each V2 lint enforces a different architectural invariant (AP-1 / cross-
    category import / duplicate dataclass / LLM SDK leak / sync callback /
    AP-8 PromptBuilder usage / Cat 7 sole-mutator). The scripts have
    inconsistent `--root` semantics:
        - check_ap1_pipeline_disguise.py:  required `--root backend/src`
          (internally joins `<root>/agent_harness/orchestrator_loop`)
        - check_promptbuilder_usage.py:    default `backend/src/agent_harness`
        - 4 others (cross_category_import / duplicate_dataclass /
          llm_sdk_leak / sync_callback): walk default backend/src/* tree
          (no `--root` flag exposed)

    Pre-53.7 invocations passed `--root backend/src/agent_harness` to BOTH
    check_ap1 AND check_promptbuilder uniformly, which made check_ap1
    silently exit OK (`target_dir = backend/src/agent_harness/agent_harness/
    orchestrator_loop` doesn't exist → "no orchestrator_loop dir; skipping").
    This wrapper hardcodes the correct args per-script.

Usage:
    python scripts/lint/run_all.py            # exit 0 if all lints green
    python scripts/lint/run_all.py --verbose  # also print per-lint stdout

Exit codes:
    0 = all lints green
    N = N lints failed; per-script status printed to stdout

Created: 2026-05-04 (Sprint 53.7 Day 1)

Related:
    - .claude/rules/sprint-workflow.md §Before Commit Checklist (Lint + Format)
    - feedback_v2_lints_must_run_locally.md (53.4 Sprint pre-push lesson)
    - Sprint 53.6 retrospective Q4 (AD-Lint-1 origin)
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

LINTS: list[tuple[str, list[str]]] = [
    # (script_filename, extra_args_after_script_path)
    ("check_ap1_pipeline_disguise.py", ["--root", "backend/src"]),
    # check_promptbuilder default root is now correct after Sprint 53.7 D1 fix
    # (was parents[1] -> scripts/; fixed to parents[2] -> repo root); pass
    # explicit --root anyway for defense-in-depth so this wrapper is robust
    # against future re-introductions of the same kind of path bug.
    ("check_promptbuilder_usage.py", ["--root", "backend/src/agent_harness"]),
    ("check_cross_category_import.py", []),
    ("check_duplicate_dataclass.py", []),
    ("check_llm_sdk_leak.py", []),
    ("check_sync_callback.py", []),
    # Sprint 55.3 (AD-Cat7-1): Cat 7 sole-mutator enforcement.
    ("check_sole_mutator.py", ["--root", "backend/src"]),
    # Sprint 56.1 Day 4 (US-5): RLS coverage on TenantScopedMixin tables.
    ("check_rls_policies.py", ["--root", "backend/src"]),
    # Sprint 57.6 Day 3 (US-5; AD-Reality-5): AP-4 Potemkin frontend page
    # placeholder text — prevents future ship-regression after a real ship.
    # Existing 3 known placeholder pages (chat-v2 / governance / verification)
    # are EXPECTED non-zero findings until Phase 57.7-57.9 ship per
    # 16-frontend-design.md §V2 Ship Timeline (closes AD-Reality-4-partial).
    ("check_ap4_frontend_placeholder.py", ["--root", "frontend/src/pages"]),
    # Sprint 57.67 (A-5b): SSE event-schema codegen parity — fails if the
    # committed FE generated artifacts drift from the wire-schema registry.
    ("check_event_schema_sync.py", []),
]


def run_one(
    script_path: Path, args: list[str], verbose: bool
) -> tuple[int, float, str]:
    """Run a single lint script. Return (exit_code, elapsed_seconds, stdout)."""
    cmd = [sys.executable, str(script_path), *args]
    t0 = time.time()
    cp = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.time() - t0
    if verbose and cp.stdout:
        print(cp.stdout, end="")
    if cp.returncode != 0 and cp.stderr:
        # Always surface stderr on failure (regardless of --verbose).
        print(cp.stderr, end="", file=sys.stderr)
    return cp.returncode, elapsed, cp.stdout


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run all V2 architecture lint scripts with correct args."
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Also print per-lint stdout (default: only summary line per script).",
    )
    cli = parser.parse_args(argv)

    base = Path(__file__).parent
    if not base.exists():
        print(f"ERROR: scripts/lint dir not found at {base}", file=sys.stderr)
        return 99

    n_lints = len(LINTS)
    print(f"Running {n_lints} V2 architecture lint scripts:")
    print("=" * 60)

    failures = 0
    total_elapsed = 0.0
    for script_name, extra_args in LINTS:
        script_path = base / script_name
        if not script_path.exists():
            print(f"  [MISSING] {script_name:38s}  (skipping)")
            failures += 1
            continue
        rc, elapsed, _ = run_one(script_path, extra_args, cli.verbose)
        total_elapsed += elapsed
        status = "OK  " if rc == 0 else "FAIL"
        print(f"  [{status}] {script_name:38s} {elapsed:5.2f}s")
        if rc != 0:
            failures += 1

    print("=" * 60)
    if failures == 0:
        print(f"V2 Lints: {n_lints}/{n_lints} green  (total {total_elapsed:.2f}s)")
        return 0
    print(
        f"V2 Lints: {n_lints - failures}/{n_lints} green -- {failures} FAILED "
        f"(total {total_elapsed:.2f}s)"
    )
    return failures


if __name__ == "__main__":
    sys.exit(main())
