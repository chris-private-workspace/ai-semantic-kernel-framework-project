#!/usr/bin/env python3
"""AP-8 lint: enforce PromptBuilder.build() before ChatClient.chat()/.stream().

Sprint 52.2 Day 4.1 — AST-based check. For every Python file under
`backend/src/agent_harness/`, walks each function/method body and verifies
that any `<obj>.chat(...)` or `<obj>.stream(...)` call is paired with at
least one `<obj>.build(...)` call in the SAME function scope. Files matching
ALLOWLIST_PATTERNS are skipped (tests, mocks, utility-LLM callers).

Sprint 57.64 — added a POSITIVE check (check_chat_handler_wiring) that asserts
the production chat handler `build_real_llm_handler` constructs
`AgentLoopImpl(..., prompt_builder=...)`. The negative scan above is rooted at
agent_harness/ and never sees the api-layer handler, so it was false-green
(AP-2): it passed even while the loop always took its naked fallback path. The
positive check closes that gap and regresses if the kwarg is removed.

Why:
    Anti-pattern AP-8 (no centralized PromptBuilder) caused V1 to leak prompt
    assembly across 6+ call-sites — each LLM caller hand-rolled `messages`
    lists, bypassing memory injection / cache breakpoints / prompt cache key
    derivation. V2 cures this by routing every main-loop LLM call through
    DefaultPromptBuilder.build(). This script keeps that invariant.

Usage:
    python scripts/check_promptbuilder_usage.py            # exit 1 on violation
    python scripts/check_promptbuilder_usage.py --dry-run  # print only, exit 0
    python scripts/check_promptbuilder_usage.py --root <path>

CI integration: see .github/workflows/lint.yml (added 52.2 closeout).
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

# --- Allowlist ----------------------------------------------------------------
# Paths matching ANY substring here are excluded from the check.
ALLOWLIST_PATTERNS: tuple[str, ...] = (
    # Tests + test infrastructure: these legitimately exercise chat() directly
    # to drive mocks; PromptBuilder coverage lives in dedicated test files.
    "tests/",
    "_testing/",
    "_mock/",
    "contract_test_",
    # Self-exempt
    "scripts/check_promptbuilder_usage.py",
    # Utility-LLM exceptions: NOT the main agent loop. These call ChatClient
    # internally for narrow purposes (compaction summarization / memory
    # extraction). They build their own task-specific prompt and are by design
    # not subject to centralized PromptBuilder routing.
    "agent_harness/context_mgmt/compactor/",
    "agent_harness/memory/extraction.py",
    # Sprint 57.151: Cat 3 SessionSummarizer is a background memory-formation
    # caller (same category as extraction.py) — it runs a narrow cheap-tier
    # summarization of a finished conversation into memory_session_summary for
    # cross-session recall. It builds its own task-specific summary prompt and is
    # by design NOT the main agent loop (no memory layers / tools / cache
    # breakpoints), so it is not routed through the centralized PromptBuilder.
    "agent_harness/memory/session_summarizer.py",
    # Sprint 57.152: Cat 3 MemoryFormationWorker composes the extractor +
    # summarizer into ONE combined background cheap-tier call (same utility-LLM
    # category as extraction.py / session_summarizer.py above). It builds its own
    # task-specific combined formation prompt and is by design NOT the main agent
    # loop, so it is not routed through the centralized PromptBuilder.
    "agent_harness/memory/formation.py",
    # Sprint 53.2: Cat 8 CircuitBreakerWrapper is a transparent ChatClient
    # decorator at adapter layer — it delegates `chat()` / `stream()` to the
    # inner adapter without constructing prompts. Caller (the AgentLoop) has
    # already routed through PromptBuilder before invoking the wrapped client.
    "adapters/_base/circuit_breaker_wrapper.py",
    # Sprint 54.1: Cat 10 LLMJudgeVerifier is a verification subagent that runs
    # an INDEPENDENT judge LLM call on candidate output (not the main agent
    # loop). It builds its own narrow judge prompt from a static template
    # (verification/templates/) and is by design not routed through
    # PromptBuilder (which constructs main-loop prompts with memory layers /
    # tools / cache breakpoints — none of which apply to a verifier).
    "agent_harness/verification/llm_judge.py",
    # Sprint 54.2: Cat 11 ForkExecutor is a subagent runner that executes a
    # bounded delegated task via a single ChatClient call (not the main agent
    # loop). It builds a narrow task-as-user-message prompt under the parent
    # AgentLoop's bounded SubagentBudget and is by design not routed through
    # PromptBuilder — the parent loop already passed through PromptBuilder
    # before deciding to spawn a subagent. Memory / tools / cache breakpoints
    # from the parent context are deliberately NOT inherited (Day 2 D12 design;
    # see modes/fork.py module docstring).
    "agent_harness/subagent/modes/fork.py",
    # Sprint 54.2: Cat 11 TeammateExecutor — same justification as ForkExecutor
    # above (utility-LLM caller, not main loop). Difference is mailbox-side-
    # effect delivery to parent on completion (Day 3 D15 design).
    "agent_harness/subagent/modes/teammate.py",
)


def _is_allowlisted(path: Path) -> bool:
    s = path.as_posix()
    return any(pat in s for pat in ALLOWLIST_PATTERNS)


# --- AST-based check ----------------------------------------------------------


def _function_scopes(tree: ast.AST) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    """Yield every function / async function in `tree` (incl. nested)."""
    out: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.append(node)
    return out


def _find_method_calls(
    func: ast.FunctionDef | ast.AsyncFunctionDef, attrs: tuple[str, ...]
) -> list[tuple[int, str]]:
    """Return (lineno, attr_name) for every `<obj>.{attr}(...)` Call inside func."""
    out: list[tuple[int, str]] = []
    for node in ast.walk(func):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        if isinstance(f, ast.Attribute) and f.attr in attrs:
            out.append((node.lineno, f.attr))
    return out


def find_violations(tree: ast.AST, file_path: Path) -> list[str]:
    """Return human-readable violation messages for this AST."""
    msgs: list[str] = []
    for func in _function_scopes(tree):
        chats = _find_method_calls(func, ("chat", "stream"))
        builds = _find_method_calls(func, ("build",))
        if chats and not builds:
            for lineno, attr in chats:
                msgs.append(
                    f"{file_path.as_posix()}:{lineno}: "
                    f"<obj>.{attr}() in function `{func.name}` "
                    f"without paired PromptBuilder.build() — AP-8 violation"
                )
    return msgs


def _scan(root: Path) -> list[str]:
    violations: list[str] = []
    for py in sorted(root.rglob("*.py")):
        if _is_allowlisted(py):
            continue
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            violations.append(f"{py.as_posix()}: SyntaxError {exc}")
            continue
        violations.extend(find_violations(tree, py))
    return violations


# --- Positive check: production chat handler must inject the PromptBuilder -----
# Why (Sprint 57.64, closes AP-2 false-green): the negative-only `_scan` above
# is rooted at `backend/src/agent_harness/`, so it NEVER scans the api-layer
# chat handler. Before 57.64 the handler omitted `prompt_builder=` from its
# AgentLoopImpl(...) call, so the loop always took its naked fallback path — yet
# this lint stayed green (it simply never looked there). This positive check
# asserts the keystone wiring exists at the real call-site: it PASSES once the
# handler passes `prompt_builder=`, and REGRESSES (fails) if that kwarg is ever
# removed. The check is path-targeted (not a scan-root extension) to avoid
# flagging unrelated utility-LLM callers across the whole api tree.

# Resolve <repo>/backend/src/api/v1/chat/handler.py from this file's location.
_CHAT_HANDLER_REL = Path("backend/src/api/v1/chat/handler.py")
_CHAT_HANDLER_FN = "build_real_llm_handler"
_LOOP_CTOR = "AgentLoopImpl"
_REQUIRED_KWARG = "prompt_builder"


def _chat_handler_path() -> Path:
    here = Path(__file__).resolve()
    return here.parents[2] / _CHAT_HANDLER_REL


def _call_passes_kwarg(node: ast.Call, ctor_name: str, kwarg: str) -> bool:
    """True if `node` is a `<ctor_name>(...)` call passing keyword `kwarg=`."""
    f = node.func
    name = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else None)
    if name != ctor_name:
        return False
    return any(kw.arg == kwarg for kw in node.keywords)


def check_chat_handler_wiring(handler_path: Path | None = None) -> list[str]:
    """Return violation messages if the chat handler omits the prompt_builder kwarg.

    Positive (true-green) check: `build_real_llm_handler` MUST construct
    `AgentLoopImpl(..., prompt_builder=...)`. Returns [] when wired correctly.
    """
    path = handler_path if handler_path is not None else _chat_handler_path()
    if not path.exists():
        return [f"{path.as_posix()}: chat handler not found — cannot verify Cat 5 wiring"]

    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        return [f"{path.as_posix()}: SyntaxError {exc}"]

    target_fn: ast.FunctionDef | ast.AsyncFunctionDef | None = None
    for fn in _function_scopes(tree):
        if fn.name == _CHAT_HANDLER_FN:
            target_fn = fn
            break

    if target_fn is None:
        return [
            f"{path.as_posix()}: function `{_CHAT_HANDLER_FN}` not found — "
            f"cannot verify Cat 5 PromptBuilder wiring"
        ]

    wired = any(
        isinstance(node, ast.Call) and _call_passes_kwarg(node, _LOOP_CTOR, _REQUIRED_KWARG)
        for node in ast.walk(target_fn)
    )
    if wired:
        return []
    return [
        f"{path.as_posix()}: `{_CHAT_HANDLER_FN}` builds `{_LOOP_CTOR}(...)` "
        f"without `{_REQUIRED_KWARG}=` — Cat 5 keystone un-wired (loop falls back "
        f"to naked prompt assembly; AP-8 / AP-2 regression)"
    ]


# --- CLI ----------------------------------------------------------------------


def _default_root() -> Path:
    """Resolve `<repo_root>/backend/src/agent_harness` from this file's location.

    Sprint 53.7 Day 1 fix: was `here.parents[1]` (= `<repo>/scripts/`) which
    produced `<repo>/scripts/backend/src/agent_harness` — that path doesn't
    exist, so default invocation always exited with "root not found". Fixed
    to `here.parents[2]` (= repo root). The bug went unnoticed because pre-
    Sprint-53.7 callers always passed explicit `--root backend/src/agent_harness`
    relative to cwd (project root). The new run_all.py wrapper exposed it.
    """
    here = Path(__file__).resolve()
    return here.parents[2] / "backend" / "src" / "agent_harness"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "AP-8 lint: every <obj>.chat()/.stream() in agent_harness/ must be "
            "paired with <obj>.build() in the same function scope (or in the "
            "allowlist of utility-LLM callers / tests / mocks)."
        ),
    )
    parser.add_argument(
        "--root",
        default=str(_default_root()),
        help="Directory to scan recursively (default: backend/src/agent_harness)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print violations without exiting non-zero",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"AP-8 lint: root not found: {root}", file=sys.stderr)
        return 2

    violations = _scan(root)
    # Positive check (Sprint 57.64): the production chat handler must inject the
    # PromptBuilder into the loop. Runs regardless of --root so the AP-2
    # false-green can never re-open by re-scoping the scan.
    violations.extend(check_chat_handler_wiring())

    if not violations:
        print(
            f"AP-8 lint: 0 violations under {root.as_posix()}; "
            f"chat handler injects {_REQUIRED_KWARG}=."
        )
        return 0

    for msg in violations:
        print(msg)

    if args.dry_run:
        print(
            f"\n[dry-run] {len(violations)} violation(s) — not failing.",
            file=sys.stderr,
        )
        return 0

    print(
        f"\nAP-8 lint failed: {len(violations)} violation(s). "
        f"Either route the call through PromptBuilder.build() or add the "
        f"file to ALLOWLIST_PATTERNS with rationale.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
