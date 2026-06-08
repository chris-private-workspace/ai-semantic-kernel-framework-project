"""
File: scripts/lint/check_ap1_pipeline_disguise.py
Purpose: V2 Lint #5 — AP-1 (Pipeline disguised as Loop) detection.
Category: Dev tooling / V2 lint suite
Scope: Phase 50 / Sprint 50.1 (Day 3.4)

Description:
    Enforces 04-anti-patterns.md §AP-1 at lint-time:
        a) Concrete AgentLoop implementations MUST drive a `while`-loop from
           their async `run()` method (not a fixed-step `for` pipeline) —
           either lexically in run() OR via a sibling helper run() delegates to
           (the Sprint 57.89 re-enterable `_run_turns` extraction).
        b) The implementation MUST feed tool results back as a tool-role
           Message — required for the LLM to observe the action result.

    Heuristic class detection:
        - Scans `<root>/agent_harness/orchestrator_loop/*.py`
        - Skips files starting with "_abc" (ABC stubs are abstract by design)
        - Treats any `class XxxImpl` or `class XxxLoop` (excluding the bare
          `AgentLoop` ABC itself) as a candidate concrete loop implementation
        - For each candidate, requires its `async def run` method body to
          contain at least one `ast.While` node and the source file to
          contain the literal substring `Message(role="tool"`.

Usage:
    python scripts/lint/check_ap1_pipeline_disguise.py --root backend/src

Exit codes:
    0 = OK (no violations)
    1 = AP-1 violation(s) detected
    2 = Configuration error (root missing etc.)

Stdlib-only (matches the 4 V2 lint scripts shipped in Sprint 49.4 Day 4).

Created: 2026-04-30 (Sprint 50.1 Day 3.4)
Last Modified: 2026-06-08 (Sprint 57.89 Slice 1)

Modification History (newest-first):
    - 2026-06-08: Sprint 57.89 Slice 1 — delegation-aware while check (run() may drive the loop via _run_turns)
    - 2026-05-04: Sprint 53.7 Day 1 — fail loudly (exit 2) instead of silent OK
      when target_dir is missing. Sprint 53.7 Day 0 drift D1 found that the
      53.6-era invocation `--root backend/src/agent_harness` silently exited
      OK because join produced `backend/src/agent_harness/agent_harness/
      orchestrator_loop` which doesn't exist. The "OK: skipping" message
      was deceiving: it implied success when in reality the AP-1 invariant
      was never checked. This change converts the missing-target-dir branch
      into a configuration error matching the existing root-not-exist branch.
      Wrapper at scripts/lint/run_all.py now passes correct `--root backend/src`.
    - 2026-04-30: Initial creation (Sprint 50.1 Day 3.4)
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

# Marker required somewhere in the source file for tool-result feedback.
TOOL_FEEDBACK_MARKER = 'Message(role="tool"'

# ABC class name that should be skipped during candidate detection.
ABC_CLASS_NAMES = frozenset({"AgentLoop", "Loop"})


def is_candidate_concrete_loop(node: ast.ClassDef) -> bool:
    """Heuristic: a class is a concrete AgentLoop impl if its name ends
    with 'Impl' or 'Loop' AND it's not the bare ABC name."""
    if node.name in ABC_CLASS_NAMES:
        return False
    return node.name.endswith("Impl") or node.name.endswith("Loop")


def find_run_method(class_node: ast.ClassDef) -> ast.AsyncFunctionDef | None:
    for item in class_node.body:
        if isinstance(item, ast.AsyncFunctionDef) and item.name == "run":
            return item
    return None


def has_while_loop(method_node: ast.AsyncFunctionDef | ast.FunctionDef) -> bool:
    return any(isinstance(n, ast.While) for n in ast.walk(method_node))


def _class_methods(
    class_node: ast.ClassDef,
) -> dict[str, ast.AsyncFunctionDef | ast.FunctionDef]:
    """Map method-name -> def node for the class's own methods."""
    return {
        item.name: item
        for item in class_node.body
        if isinstance(item, (ast.AsyncFunctionDef, ast.FunctionDef))
    }


def _self_method_calls(method_node: ast.AsyncFunctionDef | ast.FunctionDef) -> set[str]:
    """Names of methods invoked as `self.<name>(...)` anywhere in method_node."""
    names: set[str] = set()
    for n in ast.walk(method_node):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
            val = n.func.value
            if isinstance(val, ast.Name) and val.id == "self":
                names.add(n.func.attr)
    return names


def run_drives_while_loop(
    class_node: ast.ClassDef, run_method: ast.AsyncFunctionDef
) -> bool:
    """True if run() drives a StopReason `while` loop — directly OR via a sibling
    method it delegates to.

    Sprint 57.89 (run() re-entrancy refactor): the per-turn `while True` body was
    extracted from run() into a re-enterable helper `_run_turns(...)` that run()
    drives via `async for ev in self._run_turns(...)`. The AP-1 invariant (a real
    StopReason-driven loop, not a fixed-step for-pipeline) still holds — the loop
    just lives one delegation hop away. Checking only run()'s lexical body would
    false-positive on this legitimate extraction. One level of self-delegation is
    sufficient for the current loop shape.
    """
    if has_while_loop(run_method):
        return True
    methods = _class_methods(class_node)
    return any(
        (target := methods.get(name)) is not None and has_while_loop(target)
        for name in _self_method_calls(run_method)
    )


def check_file(path: Path) -> list[str]:
    """Return AP-1 violation messages for `path`. Empty list = clean."""
    src = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        return [f"{path}: SyntaxError during AP-1 lint: {exc}"]

    violations: list[str] = []
    candidates = [
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.ClassDef) and is_candidate_concrete_loop(n)
    ]
    if not candidates:
        return []

    for cls in candidates:
        run_method = find_run_method(cls)
        if run_method is None:
            continue  # class does not override run() — not an AgentLoop impl
        if not run_drives_while_loop(cls, run_method):
            violations.append(
                f"{path}:{run_method.lineno}: AP-1 violation: "
                f"{cls.name}.run() must drive a `while` loop (StopReason-driven) "
                f"— directly or via a delegated helper like _run_turns — "
                f"not a fixed-step for-pipeline. See 04-anti-patterns.md §AP-1."
            )
        if TOOL_FEEDBACK_MARKER not in src:
            violations.append(
                f"{path}:{cls.lineno}: AP-1 violation: "
                f"{cls.name} does not feed tool results back as "
                f'Message(role="tool", tool_call_id=...). '
                f"Tool results MUST be appended to messages so the LLM can "
                f"observe and continue reasoning. See 04-anti-patterns.md §AP-1."
            )
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="AP-1 (Pipeline disguised as Loop) lint — V2 lint #5."
    )
    parser.add_argument(
        "--root", required=True, help="Source root to scan (e.g. backend/src)."
    )
    args = parser.parse_args(argv)

    root = Path(args.root)
    if not root.exists():
        print(f"ERROR: root path does not exist: {root}", file=sys.stderr)
        return 2

    target_dir = root / "agent_harness" / "orchestrator_loop"
    if not target_dir.exists():
        # Sprint 53.7 D1: was previously "return 0" silent OK which masked
        # mis-invocation (e.g. --root backend/src/agent_harness causing the
        # join to produce backend/src/agent_harness/agent_harness/orchestrator_loop).
        # Now fail loudly so CI / pre-push catches the mis-invocation.
        print(
            f"ERROR: target_dir does not exist: {target_dir}\n"
            f"       Hint: --root must point to <src> such that "
            f"<src>/agent_harness/orchestrator_loop/ exists "
            f"(typically `--root backend/src`).",
            file=sys.stderr,
        )
        return 2

    all_violations: list[str] = []
    files_scanned = 0
    for py_file in sorted(target_dir.glob("*.py")):
        if py_file.name.startswith("_abc"):
            continue  # ABC stubs by design
        files_scanned += 1
        all_violations.extend(check_file(py_file))

    if all_violations:
        for v in all_violations:
            print(v)
        print(
            f"\nAP-1 lint FAILED: {len(all_violations)} violation(s) "
            f"in {files_scanned} file(s) scanned under {target_dir}.",
            file=sys.stderr,
        )
        return 1

    print(f"OK: AP-1 check passed in {target_dir} ({files_scanned} file(s) scanned)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
