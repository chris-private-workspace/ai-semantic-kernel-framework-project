"""
File: scripts/lint/check_event_schema_sync.py
Purpose: V2 Lint #10 — SSE event-schema codegen parity (committed FE artifacts == registry).
Category: Dev tooling / V2 lint suite
Scope: Sprint 57.67 (A-5b — event schema codegen parity gate, US-3)

Description:
    Guards against drift between the single declarative wire-schema registry
    (backend/src/api/v1/chat/event_wire_schema.py) and the committed frontend
    artifacts it generates (frontend/src/features/chat_v2/generated/events.json
    + loopEvents.generated.ts). It does this by invoking the codegen in
    `--check` mode (regenerate in-memory, diff vs the committed files,
    line-ending-normalized) and propagating its exit code + stdout.

    If a maintainer edits the registry (adds/changes a wire-type or payload
    field) but forgets to re-run the codegen + commit the regenerated
    artifacts, this lint fails — making contract drift mechanically
    un-mergeable. The companion pytest test
    (backend/tests/.../test_event_wire_schema_parity.py) locks the other
    direction (serializer output == registry); together they close the
    57.66 "double-gate by hand" pain.

    Stdlib-only (matches the other 9 V2 lint scripts). Provider-free.

Usage:
    python scripts/lint/check_event_schema_sync.py
    python scripts/lint/check_event_schema_sync.py --verbose

Exit codes:
    0 = generated FE artifacts are in sync with the registry
    1 = drift (registry changed but generated artifacts not regenerated/committed)
    2 = configuration error (codegen script not found)

Created: 2026-06-02 (Sprint 57.67 A-5b)

Modification History (newest-first):
    - 2026-06-02: Sprint 57.67 A-5b — initial creation (codegen --check parity lint)

Related:
    - scripts/codegen/generate_event_schemas.py (the codegen this wraps in --check)
    - backend/src/api/v1/chat/event_wire_schema.py (single-source registry)
    - backend/tests/unit/api/v1/chat/test_event_wire_schema_parity.py (sibling gate)
    - scripts/lint/run_all.py — orchestrator wraps this as the 10th lint
    - .claude/rules/anti-patterns-checklist.md §AP-8 (single-source contract)
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# scripts/lint/check_event_schema_sync.py → parents[2] = repo root.
REPO_ROOT = Path(__file__).resolve().parents[2]
CODEGEN_SCRIPT = REPO_ROOT / "scripts" / "codegen" / "generate_event_schemas.py"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "SSE event-schema codegen parity lint — V2 lint #10. Fails if the "
            "committed frontend generated artifacts are stale vs the registry."
        )
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print the codegen --check stdout even when in sync (default: only on drift).",
    )
    args = parser.parse_args(argv)

    if not CODEGEN_SCRIPT.exists():
        print(
            f"ERROR: codegen script not found at {CODEGEN_SCRIPT}\n"
            "       Hint: expected scripts/codegen/generate_event_schemas.py "
            "(Sprint 57.67 A-5b).",
            file=sys.stderr,
        )
        return 2

    # Delegate the regenerate-and-diff to the codegen's own --check mode so the
    # diff logic + line-ending normalization live in ONE place (the codegen),
    # not duplicated here. We just propagate its exit code + surface its output.
    cp = subprocess.run(
        [sys.executable, str(CODEGEN_SCRIPT), "--check"],
        capture_output=True,
        text=True,
    )

    if cp.returncode == 0:
        if args.verbose and cp.stdout:
            print(cp.stdout, end="")
        print("OK: event schema codegen in sync (FE artifacts == registry).")
        return 0

    # Drift (or codegen error): surface the codegen's diff + clear remediation.
    if cp.stdout:
        print(cp.stdout, end="")
    if cp.stderr:
        print(cp.stderr, end="", file=sys.stderr)
    print(
        "\nEvent schema lint FAILED: frontend generated artifacts are stale "
        "vs backend/src/api/v1/chat/event_wire_schema.py.\n"
        "Fix: run `python scripts/codegen/generate_event_schemas.py` and commit "
        "the regenerated events.json + loopEvents.generated.ts.",
        file=sys.stderr,
    )
    # Map any codegen non-zero (drift exit 1, or unexpected) to lint failure 1.
    return 1


if __name__ == "__main__":
    sys.exit(main())
