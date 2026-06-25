"""
File: scripts/lint/check_tool_descriptions.py
Purpose: Forbid low-quality tool descriptions — every ToolSpec(...) must have a
         non-empty, sufficiently-long, placeholder-free description AND each of its
         input_schema properties must carry a description.
Category: V2 Lint / CI / Quality
Scope: Phase 57 / Sprint 57.144 (research #7 AD-Tool-Description-Lint-Reflection, Half A)

Usage:
    python -m scripts.lint.check_tool_descriptions [--root backend/src]

What it forbids (per ToolSpec(...) call literal):
    - missing / empty `description=` kwarg
    - `description` shorter than MIN_DESCRIPTION_LEN characters (stripped)
    - `description` containing a placeholder token (TODO / FIXME / XXX / TBD)
    - any `input_schema` property without a non-empty `description`

What it allows / skips (NO false-positive):
    - dynamically-built descriptions / schemas (f-string / variable / call) are NOT
      statically checkable → SKIPPED (counted as residual-uncheckable, never failed).
      Adjacent string-literal concatenation — e.g. ("a" "b" "c") — is folded to a
      single ast.Constant at parse time, so the common multi-line description style
      IS checked.
    - No tool allow-list is needed: the test-only built-ins (echo_tool / note_tool)
      already clear the bar (full sentence + every param described). If a future
      test tool legitimately cannot, prefer giving it a real description over adding
      an exception here.

Why:
    Research #7 (ai-agent-harness-consolidated-analysis §2.3): rewriting flawed tool
    descriptions measurably improves tool selection. V2's current descriptions are
    already good; this lint is a GUARDRAIL against regression as new tools land
    (skills / subagent / task primitive all added tools recently) — it stops a future
    tool shipping a one-line stub that silently degrades selection.

Per .claude/rules/lint-detector-authoring.md (code-aware: AST, skip non-literal).
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path
from typing import NamedTuple

# A useful description is at least a short sentence. The shortest real built-in
# ("Echoes the 'text' argument back verbatim. Test-only built-in." ~60 chars)
# clears this comfortably; a bare one-word stub does not.
MIN_DESCRIPTION_LEN = 20

# Placeholder tokens that signal an unfinished description. UPPERCASE-only on
# purpose (code-aware masking, lint-detector-authoring.md): placeholder markers
# are conventionally uppercase (TODO / FIXME), whereas the English words "todo" /
# "todos" appear legitimately in real descriptions (e.g. write_todos). An
# IGNORECASE match here false-positived on write_todos' "(3 or more todos)".
PLACEHOLDER_RE = re.compile(r"\b(TODO|FIXME|XXX|TBD)\b")


class Violation(NamedTuple):
    file: Path
    lineno: int
    tool: str
    reason: str


def _const_str(node: ast.expr | None) -> str | None:
    """Return the str value iff `node` is a string constant, else None.

    Adjacent string literals (implicit concatenation) are already folded into a
    single ast.Constant by the parser, so multi-line `("a" "b")` descriptions
    are returned as one string. f-strings (ast.JoinedStr), names, and BinOps
    return None → caller skips (not statically checkable).
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _kwarg(call: ast.Call, name: str) -> ast.expr | None:
    for kw in call.keywords:
        if kw.arg == name:
            return kw.value
    return None


def _check_description(
    value: ast.expr, tool: str, file: Path, lineno: int
) -> list[Violation]:
    text = _const_str(value)
    if text is None:
        return []  # dynamic description — not statically checkable; skip
    out: list[Violation] = []
    stripped = text.strip()
    if not stripped:
        out.append(Violation(file, lineno, tool, "description is empty"))
    elif len(stripped) < MIN_DESCRIPTION_LEN:
        out.append(
            Violation(
                file,
                lineno,
                tool,
                f"description too short ({len(stripped)} < {MIN_DESCRIPTION_LEN} chars)",
            )
        )
    if PLACEHOLDER_RE.search(text):
        out.append(
            Violation(
                file,
                lineno,
                tool,
                "description has a placeholder token (TODO/FIXME/XXX/TBD)",
            )
        )
    return out


def _dict_get(node: ast.Dict, key: str) -> ast.expr | None:
    for k, v in zip(node.keys, node.values):
        if _const_str(k) == key:
            return v
    return None


def _check_params(
    schema: ast.expr, tool: str, file: Path, lineno: int
) -> list[Violation]:
    if not isinstance(schema, ast.Dict):
        return []  # dynamic schema — skip
    props = _dict_get(schema, "properties")
    if not isinstance(props, ast.Dict):
        return []
    out: list[Violation] = []
    for pkey, pval in zip(props.keys, props.values):
        pname = _const_str(pkey)
        if pname is None or not isinstance(pval, ast.Dict):
            continue  # dynamic property name / value — skip
        desc = _dict_get(pval, "description")
        desc_text = _const_str(desc) if desc is not None else None
        if desc_text is None or not desc_text.strip():
            out.append(
                Violation(
                    file, lineno, tool, f"param '{pname}' has no (or empty) description"
                )
            )
    return out


def _toolspec_calls(tree: ast.Module) -> list[ast.Call]:
    out: list[ast.Call] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        is_toolspec = (isinstance(func, ast.Name) and func.id == "ToolSpec") or (
            isinstance(func, ast.Attribute) and func.attr == "ToolSpec"
        )
        if is_toolspec:
            out.append(node)
    return out


def find_violations(root: Path) -> list[Violation]:
    violations: list[Violation] = []
    for py_file in root.rglob("*.py"):
        if "__pycache__" in py_file.parts:
            continue
        try:
            text = py_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        for call in _toolspec_calls(tree):
            tool = _const_str(_kwarg(call, "name")) or "<unknown>"
            desc_node = _kwarg(call, "description")
            if desc_node is None:
                violations.append(
                    Violation(py_file, call.lineno, tool, "missing description kwarg")
                )
            else:
                violations.extend(
                    _check_description(desc_node, tool, py_file, call.lineno)
                )
            schema_node = _kwarg(call, "input_schema")
            if schema_node is not None:
                violations.extend(
                    _check_params(schema_node, tool, py_file, call.lineno)
                )
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="backend/src")
    args = parser.parse_args(argv)

    root = Path(args.root)
    if not root.exists():
        print(f"ERROR: --root not found: {root}", file=sys.stderr)
        return 2

    violations = find_violations(root)
    if not violations:
        print(f"OK: all ToolSpec descriptions well-formed under {root}")
        return 0

    print(
        f"FAIL: {len(violations)} tool-description issue(s):",
        file=sys.stderr,
    )
    for v in violations:
        print(f"  {v.file}:{v.lineno}  [{v.tool}]  {v.reason}", file=sys.stderr)
    print(
        "\nFIX: Give every tool a clear (>= "
        f"{MIN_DESCRIPTION_LEN}-char) description + a description on every "
        "input_schema property. Per research #7 (tool-description quality).",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
