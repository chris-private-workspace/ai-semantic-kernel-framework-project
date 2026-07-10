"""
File: scripts/lint/check_tool_descriptions.py
Purpose: Forbid low-quality tool descriptions — every ToolSpec(...) must have a
         non-empty, sufficiently-long, placeholder-free description AND each of its
         input_schema properties must carry a description.
Category: V2 Lint / CI / Quality
Scope: Phase 57 / Sprint 57.144 (research #7 AD-Tool-Description-Lint-Reflection, Half A)

Usage:
    python -m scripts.lint.check_tool_descriptions [--root backend/src]
    python -m scripts.lint.check_tool_descriptions --fix [--root ...]           # dry-run: draft
    python -m scripts.lint.check_tool_descriptions --fix --write [--root ...]   # apply drafts

The default (no `--fix`) is the report-only CI lint wired in run_all.py — it imports
nothing beyond the stdlib. `--fix` is an opt-in local assist (Sprint 57.165, closes
③2 AD-Tool-Description-AutoFix): for each flagged tool/param it drafts a description via
the neutral cheap-tier ChatClient (adapters.azure_openai.profile — lazily imported ONLY
under `--fix`, needs real Azure creds), self-validates each draft against this lint's own
predicate (retry once, else emit `<needs-manual>` — never a lint-failing draft), and prints
a dry-run report. `--write` additionally applies the drafts to source via position-based
AST splicing (review `git diff` after). `--fix` is NEVER wired into run_all / CI.

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
import asyncio
import re
import sys
from pathlib import Path
from typing import Any, NamedTuple

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


def _check_description(value: ast.expr, tool: str, file: Path, lineno: int) -> list[Violation]:
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


def _check_params(schema: ast.expr, tool: str, file: Path, lineno: int) -> list[Violation]:
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
                Violation(file, lineno, tool, f"param '{pname}' has no (or empty) description")
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
                violations.extend(_check_description(desc_node, tool, py_file, call.lineno))
            schema_node = _kwarg(call, "input_schema")
            if schema_node is not None:
                violations.extend(_check_params(schema_node, tool, py_file, call.lineno))
    return violations


# ===========================================================================
# --fix / --write  (Sprint 57.165, ③2 AD-Tool-Description-AutoFix)
# ---------------------------------------------------------------------------
# Opt-in local assist. Everything below is reached ONLY when `--fix` is passed;
# the CI report path (find_violations + main's default branch) imports nothing
# here. The neutral cheap-tier ChatClient (adapters.*) is imported LAZILY inside
# _build_cheap_client() so a plain CI run never pulls the backend adapter.
# Folded into this module (not a sibling _autofix.py) so the existing importlib
# file-path test load reaches these helpers and the violation predicates stay
# single-sourced (Sprint 57.165 Day-1 D-fold-into-checker).
# ===========================================================================

NEEDS_MANUAL = "<needs-manual>"


class FixTarget(NamedTuple):
    """One fixable tool-description gap + the LLM context to draft it.

    kind:
        replace_desc      — a bad string-literal description (tool-level when
                            param is None, or an empty param literal) → replace
                            the ast.Constant span.
        insert_tool_desc  — an absent `description=` kwarg → splice a kwarg.
        insert_param_desc — an absent param `"description"` key → splice a key.
    A param whose description is present-but-DYNAMIC (a variable) is flagged by
    the lint but is NOT statically autofixable (a splice would duplicate the
    key) → skipped + counted as unfixable, never emitted as a target.
    """

    file: Path
    kind: str
    tool: str
    param: str | None  # None = tool-level; else the parameter name
    lineno: int  # the ToolSpec call line (report + apply re-match key)
    source_segment: str  # the whole ToolSpec(...) literal — LLM context


def collect_fix_targets(root: Path) -> tuple[list[FixTarget], int]:
    """Walk `root` and return (fixable targets, count of unfixable-dynamic params).

    Reuses the SAME predicates as find_violations (MIN_DESCRIPTION_LEN /
    PLACEHOLDER_RE / _const_str / _dict_get / _kwarg / _toolspec_calls) so a
    target exists for exactly the statically-fixable subset of what the lint
    flags. Dynamic (f-string / variable) tool descriptions are lint-skipped
    (no violation → no target); dynamic param descriptions are lint-flagged but
    not autofixable → counted, not targeted.
    """
    targets: list[FixTarget] = []
    unfixable_dynamic = 0
    for py_file in sorted(root.rglob("*.py")):
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
            seg = ast.get_source_segment(text, call) or ""

            desc_node = _kwarg(call, "description")
            if desc_node is None:
                targets.append(FixTarget(py_file, "insert_tool_desc", tool, None, call.lineno, seg))
            else:
                desc_text = _const_str(desc_node)
                if desc_text is not None:  # a literal we can replace (skip dynamic)
                    stripped = desc_text.strip()
                    bad = (
                        not stripped
                        or len(stripped) < MIN_DESCRIPTION_LEN
                        or bool(PLACEHOLDER_RE.search(desc_text))
                    )
                    if bad:
                        targets.append(
                            FixTarget(py_file, "replace_desc", tool, None, call.lineno, seg)
                        )

            schema_node = _kwarg(call, "input_schema")
            if isinstance(schema_node, ast.Dict):
                props = _dict_get(schema_node, "properties")
                if isinstance(props, ast.Dict):
                    for pkey, pval in zip(props.keys, props.values):
                        pname = _const_str(pkey)
                        if pname is None or not isinstance(pval, ast.Dict):
                            continue
                        desc = _dict_get(pval, "description")
                        if desc is None:
                            targets.append(
                                FixTarget(
                                    py_file, "insert_param_desc", tool, pname, call.lineno, seg
                                )
                            )
                        else:
                            dtext = _const_str(desc)
                            if dtext is None:
                                unfixable_dynamic += 1  # dynamic param desc — can't splice
                            elif not dtext.strip():
                                targets.append(
                                    FixTarget(
                                        py_file, "replace_desc", tool, pname, call.lineno, seg
                                    )
                                )
    return targets, unfixable_dynamic


# --- neutral drafting (lazy backend import) --------------------------------


def _ensure_backend_on_path() -> None:
    """Put backend/src on sys.path so the Azure adapter + ChatClient import.

    Called ONLY under `--fix`. In the pytest context (rootdir = backend/) the
    path is already present → this is a harmless no-op.
    """
    src = Path(__file__).resolve().parents[2] / "backend" / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


def _content_text(content: Any) -> str:
    """Extract plain text from a ChatResponse.content (str or list[ContentBlock])."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join((getattr(b, "text", "") or "") for b in content)
    return str(content)


_DRAFT_SYSTEM = (
    "You write documentation for tools that an LLM agent may call. Given a tool "
    "definition, write ONE concise imperative sentence describing what the tool "
    "(or the named parameter) does and when to use it. Requirements: at least "
    f"{MIN_DESCRIPTION_LEN} characters, at most ~200, a single line, no markdown, "
    "no placeholder words (TODO / FIXME / XXX / TBD). Reply with ONLY the sentence."
)

_RETRY_HINT = (
    "\n\n(Your previous reply was empty, too short, or contained a placeholder. "
    f"Reply with ONE clear sentence of at least {MIN_DESCRIPTION_LEN} characters.)"
)


def _draft_prompt(t: FixTarget) -> str:
    subject = f"the parameter '{t.param}' of tool '{t.tool}'" if t.param else f"the tool '{t.tool}'"
    return f"Tool definition:\n{t.source_segment}\n\nWrite a description for {subject}."


def _lint_ok(text: str) -> bool:
    """The draft must clear this lint's own predicate (never emit a failing draft)."""
    stripped = text.strip()
    return (
        bool(stripped) and len(stripped) >= MIN_DESCRIPTION_LEN and not PLACEHOLDER_RE.search(text)
    )


def _clean_draft(raw: str) -> str:
    """Strip wrapping quotes + collapse to a single line."""
    text = " ".join(raw.split())
    if len(text) >= 2 and text[0] in "\"'" and text[-1] == text[0]:
        text = text[1:-1].strip()
    return text


async def draft_description(client: Any, target: FixTarget, *, max_tokens: int = 80) -> str:
    """Draft a description via the neutral ChatClient, self-validated.

    Retries once with a terser hint; if the model still cannot produce a
    lint-passing sentence, returns NEEDS_MANUAL (never a lint-failing string).
    """
    from agent_harness._contracts.chat import ChatRequest, Message

    for attempt in range(2):
        prompt = _draft_prompt(target) + ("" if attempt == 0 else _RETRY_HINT)
        resp = await client.chat(
            ChatRequest(
                messages=[
                    Message(role="system", content=_DRAFT_SYSTEM),
                    Message(role="user", content=prompt),
                ],
                temperature=0.0,
                max_tokens=max_tokens,
            )
        )
        draft = _clean_draft(_content_text(resp.content))
        if _lint_ok(draft):
            return draft
    return NEEDS_MANUAL


async def _draft_all(client: Any, targets: list[FixTarget]) -> list[tuple[FixTarget, str]]:
    out: list[tuple[FixTarget, str]] = []
    for t in targets:
        out.append((t, await draft_description(client, t)))
    return out


def _build_cheap_client() -> Any:
    """Build the neutral cheap-tier ChatClient (lazy; needs Azure env)."""
    _ensure_backend_on_path()
    from adapters.azure_openai.profile import build_azure_model_profile

    return build_azure_model_profile().cheap


# --- dry-run report --------------------------------------------------------


def render_report(drafts: list[tuple[FixTarget, str]], unfixable_dynamic: int = 0) -> str:
    """Group the drafts by file for a dry-run report (source is NOT modified)."""
    lines = [
        "[tool-description --fix] LLM-drafted suggestions — review each for ACCURACY,",
        "then apply with --write (source is UNCHANGED in this dry-run).",
        "",
    ]
    by_file: dict[Path, list[tuple[FixTarget, str]]] = {}
    for t, draft in drafts:
        by_file.setdefault(t.file, []).append((t, draft))
    for file in sorted(by_file, key=str):
        lines.append(f"{file}:")
        for t, draft in by_file[file]:
            where = f"[{t.tool}]" + (f" param '{t.param}'" if t.param else "")
            lines.append(f"  L{t.lineno} {t.kind} {where}")
            lines.append(f"      -> {draft}")
        lines.append("")
    n = len(drafts)
    needs = sum(1 for _, d in drafts if d == NEEDS_MANUAL)
    summary = f"{n} suggestion(s)"
    if needs:
        summary += f" ({needs} could not be drafted → {NEEDS_MANUAL})"
    if unfixable_dynamic:
        summary += f"; {unfixable_dynamic} dynamic description(s) skipped (not autofixable)"
    summary += ". Source UNCHANGED. Re-run with --write to apply, then review `git diff`."
    lines.append(summary)
    return "\n".join(lines)


# --- apply (--write): position-based AST splice ----------------------------


def _line_starts(text: str) -> list[int]:
    """Char offset of the start of each 1-based line (index 0 = line 1)."""
    starts = [0]
    for i, ch in enumerate(text):
        if ch == "\n":
            starts.append(i + 1)
    return starts


def _offset(line_starts: list[int], lineno: int, col: int) -> int:
    """Absolute char offset for a 1-based line + 0-based column."""
    return line_starts[lineno - 1] + col


def _quote(text: str) -> str:
    """A double-quoted single-line Python string literal for `text`."""
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _param_dict(call: ast.Call, param: str) -> ast.Dict | None:
    """The ast.Dict value of `input_schema.properties[param]`, or None."""
    schema = _kwarg(call, "input_schema")
    if not isinstance(schema, ast.Dict):
        return None
    props = _dict_get(schema, "properties")
    if not isinstance(props, ast.Dict):
        return None
    for pkey, pval in zip(props.keys, props.values):
        if _const_str(pkey) == param and isinstance(pval, ast.Dict):
            return pval
    return None


def _splice_op(
    text: str,
    line_starts: list[int],
    call: ast.Call,
    target: FixTarget,
    draft: str,
) -> tuple[int, int, str] | None:
    """Compute a (start, end, replacement) edit for one target, or None if unresolved.

    replace_desc      → overwrite the description ast.Constant span.
    insert_tool_desc  → splice a `description=<quoted>,` kwarg after `name=`.
    insert_param_desc → splice a `"description": <quoted>,` key just after the param `{`.
    """
    q = _quote(draft)

    if target.kind == "replace_desc":
        if target.param is None:
            node = _kwarg(call, "description")
        else:
            pval = _param_dict(call, target.param)
            node = _dict_get(pval, "description") if isinstance(pval, ast.Dict) else None
        if (
            not isinstance(node, ast.Constant)
            or node.end_lineno is None
            or node.end_col_offset is None
        ):
            return None
        start = _offset(line_starts, node.lineno, node.col_offset)
        end = _offset(line_starts, node.end_lineno, node.end_col_offset)
        return (start, end, q)

    if target.kind == "insert_tool_desc":
        if not call.keywords:
            return None
        name_kw = next((k for k in call.keywords if k.arg == "name"), call.keywords[0])
        v = name_kw.value
        if v.end_lineno is None or v.end_col_offset is None:
            return None
        v_end = _offset(line_starts, v.end_lineno, v.end_col_offset)
        comma = text.find(",", v_end)
        if comma == -1:
            return None
        pos = comma + 1
        if call.lineno != call.end_lineno:
            indent = " " * name_kw.col_offset
            insert = f"\n{indent}description={q},"
        else:
            insert = f" description={q},"
        return (pos, pos, insert)

    if target.kind == "insert_param_desc" and target.param is not None:
        pval = _param_dict(call, target.param)
        if pval is None:
            return None
        pos = _offset(line_starts, pval.lineno, pval.col_offset) + 1  # just after `{`
        return (pos, pos, f'"description": {q}, ')

    return None


def apply_fixes(text: str, targets_and_drafts: list[tuple[FixTarget, str]]) -> tuple[str, int]:
    """Apply the drafts for ONE file's targets via position-based splicing.

    Re-parses `text` (so all offsets come from one consistent parse), computes an
    edit per target, and applies them back-to-front (highest offset first) so an
    earlier splice never shifts a later target's span. NEEDS_MANUAL drafts and
    unresolved targets are skipped. Returns (new_text, applied_count). Idempotent:
    once a file has no remaining gaps, collect_fix_targets yields nothing → no ops.
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return text, 0
    line_starts = _line_starts(text)
    calls_by_line: dict[int, ast.Call] = {c.lineno: c for c in _toolspec_calls(tree)}
    ops: list[tuple[int, int, str]] = []
    for target, draft in targets_and_drafts:
        if draft == NEEDS_MANUAL:
            continue
        call = calls_by_line.get(target.lineno)
        if call is None:
            continue
        op = _splice_op(text, line_starts, call, target, draft)
        if op is not None:
            ops.append(op)
    for start, end, replacement in sorted(ops, key=lambda o: o[0], reverse=True):
        text = text[:start] + replacement + text[end:]
    return text, len(ops)


def run_fix(root: Path, *, write: bool = False) -> int:
    """`--fix`: collect gaps, draft descriptions, then report (dry-run) or apply (--write)."""
    targets, unfixable_dynamic = collect_fix_targets(root)
    if not targets:
        msg = f"OK: no fixable tool-description issues under {root}"
        if unfixable_dynamic:
            msg += f" ({unfixable_dynamic} dynamic description(s) are not autofixable)"
        print(msg)
        return 0
    client = _build_cheap_client()
    drafts = asyncio.run(_draft_all(client, targets))

    if not write:
        print(render_report(drafts, unfixable_dynamic))
        return 0

    by_file: dict[Path, list[tuple[FixTarget, str]]] = {}
    for target, draft in drafts:
        by_file.setdefault(target.file, []).append((target, draft))
    applied = 0
    for file in sorted(by_file, key=str):
        text = file.read_text(encoding="utf-8")
        new_text, n = apply_fixes(text, by_file[file])
        applied += n
        if new_text != text:
            file.write_text(new_text, encoding="utf-8")
    manual = sum(1 for _, draft in drafts if draft == NEEDS_MANUAL)
    print(f"Applied {applied} description(s) across {len(by_file)} file(s).")
    if applied:
        print("⚠ LLM-DRAFTED — review `git diff` for ACCURACY before commit.")
    if manual:
        print(f"{manual} could not be drafted → left as {NEEDS_MANUAL} for manual authoring.")
    if unfixable_dynamic:
        print(f"{unfixable_dynamic} dynamic description(s) skipped (not autofixable).")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="backend/src")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="draft descriptions for flagged tools/params via the cheap-tier LLM "
        "(dry-run report; source unchanged; needs Azure creds)",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="with --fix: apply the drafts to source via AST splicing "
        "(review `git diff` for accuracy before commit)",
    )
    args = parser.parse_args(argv)

    if args.write and not args.fix:
        parser.error("--write requires --fix")

    root = Path(args.root)
    if not root.exists():
        print(f"ERROR: --root not found: {root}", file=sys.stderr)
        return 2

    if args.fix:
        # The report carries non-ASCII typography (->); a Windows cp950 console
        # cannot encode it. Force the stdout text layer to UTF-8 (mirror the
        # benchmark scripts) so the print never crashes.
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
        except Exception:  # noqa: BLE001 — best-effort; odd/redirected streams keep their codec
            pass
        return run_fix(root, write=args.write)

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
